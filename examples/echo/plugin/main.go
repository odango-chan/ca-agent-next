// Command echo-plugin is the reusable Echo fixture for the Native Plugin IPC
// v1alpha1 contract.
//
// The default behaviour (no command-line flags) reproduces the pinned 12-frame
// record in docs/规范/插件包与进程通信协议规范.md §5.1 exactly, including the
// original message identifiers m2/m3/m6/m8/m10/m12.
//
// SR-003 extends the peer with three Callables that share one Plugin process:
//
//	echo.read      -> result {"text": <argument text>}
//	echo.describe  -> result describing the Callables exported by this process
//	echo.wait      -> stays pending until host.cancel targets its invocationId
//
// The flags below are test-only support for the SR-003 negative cases. They are
// not part of the Plugin Package/IPC contract and the default invocation never
// exercises them.
//
//	--fault=<mode>
//	--extensions=<comma list>
//	--ingress=<json payload>   (repeatable)
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

const (
	apiVersion       = "connectionagent.io/plugin-ipc/v1alpha1"
	pluginID         = "example.echo"
	pluginVersion    = "1.0.0"
	ipcVersion       = "connectionagent.io/plugin-ipc/v1alpha1"
	callableRead     = "echo.read"
	callableDescribe = "echo.describe"
	callableWait     = "echo.wait"
	eventID          = "evt1"
	eventType        = "echo.request"
	externalRequest  = "client-1"
	responseChannel  = "ch1"
	invocationID     = "inv1"
	deliveryID       = "del1"
	obligationID     = "obl1"
	cancelTarget     = "inv1"
)

type frame struct {
	APIVersion    string         `json:"apiVersion"`
	MessageID     string         `json:"messageId"`
	CorrelationID string         `json:"correlationId,omitempty"`
	Type          string         `json:"type"`
	Payload       map[string]any `json:"payload"`
}

// stringList collects repeatable string flags.
type stringList []string

func (s *stringList) String() string { return strings.Join(*s, ",") }

func (s *stringList) Set(value string) error {
	*s = append(*s, value)
	return nil
}

// waitOperation is an echo.wait invocation that has not produced a terminal
// frame yet. It is completed by a matching host.cancel.
type waitOperation struct {
	messageID string
	text      string
	emitLate  bool
}

type plugin struct {
	hostIDs     map[string]struct{}
	outgoingIDs map[string]struct{}
	initialized bool
	seq         int
	fault       string
	extensions  []string
	ingress     stringList
	pending     map[string]*waitOperation
	buffered    []frame
}

func main() {
	var rest []string
	for _, argument := range os.Args[1:] {
		switch argument {
		case "serve":
			// The documented manifest argv is [serve].
		case "--version", "version":
			fmt.Printf("echo-plugin %s (%s)\n", pluginVersion, ipcVersion)
			return
		default:
			rest = append(rest, argument)
		}
	}

	flags := flag.NewFlagSet("echo-plugin", flag.ContinueOnError)
	flags.SetOutput(os.Stderr)
	faultMode := flags.String("fault", "", "test-only fault mode")
	extensionList := flags.String("extensions", "", "test-only plugin.ready extension override")
	var ingressJSON stringList
	flags.Var(&ingressJSON, "ingress", "test-only ingress.event payload JSON (repeatable)")
	if err := flags.Parse(rest); err != nil {
		fmt.Fprintf(os.Stderr, "echo-plugin: %v (usage: echo-plugin serve)\n", err)
		os.Exit(2)
	}
	if flags.NArg() != 0 {
		fmt.Fprintf(os.Stderr, "echo-plugin: unsupported argument %q (usage: echo-plugin serve)\n", flags.Arg(0))
		os.Exit(2)
	}

	extensions := []string{"event.ingress", "event.delivery", "tools"}
	if *extensionList != "" {
		extensions = strings.Split(*extensionList, ",")
	}

	p := &plugin{
		hostIDs:     map[string]struct{}{},
		outgoingIDs: map[string]struct{}{},
		fault:       *faultMode,
		extensions:  extensions,
		ingress:     ingressJSON,
		pending:     map[string]*waitOperation{},
	}
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 64*1024), 8<<20)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		in, err := p.parseRequest(line)
		if err != nil {
			p.violation("FRAME_INVALID", "stdin", err.Error())
		}
		if _, duplicate := p.hostIDs[in.MessageID]; duplicate {
			p.violation("DUPLICATE_MESSAGE_ID", in.Type, in.MessageID)
		}
		p.hostIDs[in.MessageID] = struct{}{}
		if stop := p.handle(in); stop {
			return
		}
	}
	logf("EOF_WITHOUT_SHUTDOWN")
}

func (p *plugin) parseRequest(line []byte) (frame, error) {
	decoder := json.NewDecoder(bytes.NewReader(line))
	decoder.DisallowUnknownFields()
	var f frame
	if err := decoder.Decode(&f); err != nil {
		return frame{}, fmt.Errorf("decode: %w", err)
	}
	if f.APIVersion != apiVersion {
		return frame{}, fmt.Errorf("apiVersion=%q", f.APIVersion)
	}
	if f.MessageID == "" || f.Type == "" || f.Payload == nil {
		return frame{}, fmt.Errorf("missing messageId/type/payload")
	}
	return f, nil
}

func (p *plugin) handle(in frame) (stop bool) {
	switch in.Type {
	case "host.initialize":
		p.handleInitialize(in)
	case "ingress.ack":
		p.handleAck(in)
	case "tools.invoke":
		p.handleInvoke(in)
	case "delivery.dispatch":
		p.handleDelivery(in)
	case "host.cancel":
		p.handleCancel(in)
	case "host.shutdown":
		return p.handleShutdown(in)
	default:
		p.violation("UNKNOWN_MESSAGE_TYPE", in.Type, in.MessageID)
	}
	return false
}

func (p *plugin) handleInitialize(in frame) {
	if p.initialized {
		p.violation("DUPLICATE_INITIALIZE", in.Type, in.MessageID)
	}
	p.initialized = true
	if in.CorrelationID != "" {
		p.violation("UNEXPECTED_CORRELATION", in.Type, in.CorrelationID)
	}
	if in.Payload["pluginId"] != pluginID || in.Payload["expectedVersion"] != pluginVersion || in.Payload["ipcVersion"] != ipcVersion {
		p.violation("INITIALIZE_IDENTITY_MISMATCH", in.Type, "")
	}
	if _, ok := in.Payload["config"].(map[string]any); !ok {
		p.violation("INITIALIZE_CONFIG_INVALID", in.Type, "")
	}
	if p.fault == "no-ready" {
		logf("FAULT no-ready")
		os.Exit(1)
	}
	if p.fault == "stall-before-ready" {
		// A live peer that withholds ready until the Host closes stdin.
		// Unlike no-ready, this exercises a real startup deadline.
		logf("FAULT stall-before-ready")
		var ignored [1]byte
		_, _ = os.Stdin.Read(ignored[:])
		return
	}

	extensions := make([]any, 0, len(p.extensions))
	for _, extension := range p.extensions {
		extensions = append(extensions, extension)
	}
	p.sendFixed("m2", in.MessageID, "plugin.ready", map[string]any{
		"pluginId":      pluginID,
		"pluginVersion": pluginVersion,
		"ipcVersion":    ipcVersion,
		"extensions":    extensions,
	})
	if p.fault == "crash-after-ready" {
		logf("FAULT crash-after-ready")
		os.Exit(1)
	}

	if !p.hasExtension("event.ingress") {
		return
	}
	if len(p.ingress) > 0 {
		for _, raw := range p.ingress {
			var payload map[string]any
			decoder := json.NewDecoder(strings.NewReader(raw))
			decoder.UseNumber()
			if err := decoder.Decode(&payload); err != nil {
				p.violation("INGRESS_OVERRIDE_INVALID", "test flag", err.Error())
			}
			p.send(p.nextID("x"), "", "ingress.event", payload)
		}
		return
	}
	p.sendFixed("m3", "", "ingress.event", map[string]any{
		"eventId":           eventID,
		"ingressId":         pluginID,
		"eventType":         eventType,
		"externalRequestId": externalRequest,
		"responseChannelId": responseChannel,
		"source": map[string]any{
			"protocol": "echo",
			"peerId":   "test-peer",
		},
		"payload":   map[string]any{"text": "hello"},
		"artifacts": []any{},
	})
	logf("INGRESS_EVENT_SENT eventId=%s", eventID)
}

// handleAck is the receiver-side check for the injected runId negative case.
// The design says ingress.ack may contain only eventId, disposition and an
// optional error; any Run/Skill/artifactRef identity is a protocol violation.
func (p *plugin) handleAck(in frame) {
	allowed := map[string]bool{"eventId": true, "disposition": true, "error": true}
	for key := range in.Payload {
		if !allowed[key] {
			p.violation("UNEXPECTED_PAYLOAD_FIELD", "ingress.ack", key)
		}
	}
	if in.CorrelationID == "" || in.Payload["eventId"] == nil {
		p.violation("ACK_CORRELATION_MISMATCH", "ingress.ack", "")
	}
	disposition, _ := in.Payload["disposition"].(string)
	switch disposition {
	case "accepted", "duplicate_attached", "conflict", "rejected":
	default:
		p.violation("ACK_DISPOSITION_INVALID", "ingress.ack", disposition)
	}
	logf("ACK disposition=%s eventId=%v", disposition, in.Payload["eventId"])
}

func (p *plugin) handleInvoke(in frame) {
	invocation, _ := in.Payload["invocationId"].(string)
	callable, _ := in.Payload["callableId"].(string)
	if invocation == "" || callable == "" {
		p.violation("INVOKE_IDENTITY_MISMATCH", "tools.invoke", "")
	}
	arguments, ok := in.Payload["arguments"].(map[string]any)
	if !ok {
		p.violation("INVOKE_ARGUMENTS_INVALID", "tools.invoke", "")
	}
	text, _ := arguments["text"].(string)

	if p.fault == "out-of-order" {
		p.buffered = append(p.buffered, in)
		if len(p.buffered) == 2 {
			first, second := p.buffered[0], p.buffered[1]
			p.buffered = nil
			p.replyRead(second)
			p.replyRead(first)
		}
		return
	}

	switch p.fault {
	case "cancel-too-late-late-result", "cancel-unsupported-late-result":
		// The operation is already complete on the plugin side. The host has not
		// seen the terminal frame yet: host.cancel is answered first (too_late or
		// unsupported), then the original tools.result is emitted. A correct host
		// keeps the pending tool operation and still accepts this result.
		p.pending[invocation] = &waitOperation{
			messageID: in.MessageID,
			text:      text,
			emitLate:  false,
		}
		logf("COMPLETED_PENDING_BEFORE_CANCEL invocationId=%s", invocation)
		return
	}

	switch callable {
	case callableRead:
		p.replyRead(in)
	case callableDescribe:
		result := map[string]any{
			"callableId": callableDescribe,
			"operations": []any{callableRead, callableDescribe, callableWait},
			"text":       text,
		}
		p.emitResult(in, invocation, result, "")
	case callableWait:
		emitLate, _ := arguments["emitLateResult"].(bool)
		p.pending[invocation] = &waitOperation{
			messageID: in.MessageID,
			text:      text,
			emitLate:  emitLate,
		}
		logf("WAIT_PENDING invocationId=%s", invocation)
	default:
		p.send(p.nextID("r"), in.MessageID, "tools.result", map[string]any{
			"invocationId": invocation,
			"error": map[string]any{
				"code":      "UNKNOWN_CALLABLE",
				"message":   "callable is not exported by this plugin",
				"retryable": false,
			},
		})
	}
}

func (p *plugin) replyRead(in frame) {
	invocation, _ := in.Payload["invocationId"].(string)
	arguments, _ := in.Payload["arguments"].(map[string]any)
	text, _ := arguments["text"].(string)
	if p.fault == "wrong-invocation-id" {
		p.writeWithID(p.nextID("r"), in.MessageID, "tools.result", map[string]any{
			"invocationId": "inv-bogus",
			"result":       map[string]any{"text": text},
		})
		return
	}
	if p.fault == "unknown-correlation-id" {
		p.writeWithID(p.nextID("r"), "unknown-correlation-id", "tools.result", map[string]any{
			"invocationId": invocation,
			"result":       map[string]any{"text": text},
		})
		return
	}
	golden := ""
	if invocation == invocationID && !p.used("m6") {
		golden = "m6"
	}
	p.emitResult(in, invocation, map[string]any{"text": text}, golden)
}

func (p *plugin) emitResult(in frame, invocation string, result map[string]any, goldenID string) {
	messageID := goldenID
	if messageID == "" {
		messageID = p.nextID("r")
	}
	payload := map[string]any{
		"invocationId": invocation,
		"result":       result,
	}
	if p.fault == "duplicate-result" {
		p.writeWithID(messageID, in.MessageID, "tools.result", payload)
		p.writeWithID(messageID, in.MessageID, "tools.result", payload)
		return
	}
	if p.fault == "duplicate-terminal" {
		p.sendWithID(messageID, in.MessageID, "tools.result", payload)
		p.send(p.nextID("r"), in.MessageID, "tools.result", payload)
		return
	}
	p.sendWithID(messageID, in.MessageID, "tools.result", payload)
}

func (p *plugin) handleDelivery(in frame) {
	if p.fault == "wrong-delivery-id" {
		p.writeWithID(p.nextID("d"), in.MessageID, "delivery.result", map[string]any{
			"deliveryId":  "del-bogus",
			"disposition": "delivered",
			"statusCode":  200,
		})
		return
	}
	delivery, _ := in.Payload["deliveryId"].(string)
	if delivery == "" {
		p.violation("DELIVERY_IDENTITY_MISMATCH", "delivery.dispatch", "")
	}
	status, ok := in.Payload["statusCode"].(float64)
	if !ok {
		p.violation("DELIVERY_STATUS_INVALID", "delivery.dispatch", "")
	}
	golden := ""
	if delivery == deliveryID && in.Payload["responseObligationId"] == obligationID &&
		in.Payload["responseChannelId"] == responseChannel && in.Payload["eventType"] == eventType && !p.used("m8") {
		golden = "m8"
	}
	messageID := golden
	if messageID == "" {
		messageID = p.nextID("d")
	}
	p.sendWithID(messageID, in.MessageID, "delivery.result", map[string]any{
		"deliveryId":  delivery,
		"disposition": "delivered",
		"statusCode":  status,
	})
}

func (p *plugin) handleCancel(in frame) {
	target, _ := in.Payload["targetOperationId"].(string)
	if target == "" {
		p.violation("CANCEL_TARGET_MISMATCH", "host.cancel", "")
	}
	if p.fault == "cancel-no-reply" {
		logf("FAULT cancel-no-reply targetOperationId=%s", target)
		return
	}
	if operation, ok := p.pending[target]; ok {
		if p.fault == "cancel-too-late-late-result" || p.fault == "cancel-unsupported-late-result" {
			disposition := "too_late"
			if p.fault == "cancel-unsupported-late-result" {
				disposition = "unsupported"
			}
			delete(p.pending, target)
			p.send(p.nextID("c"), in.MessageID, "plugin.cancelled", map[string]any{
				"targetOperationId": target,
				"disposition":       disposition,
			})
			logf("CANCELLED_SENT targetOperationId=%s disposition=%s", target, disposition)
			p.send(p.nextID("r"), operation.messageID, "tools.result", map[string]any{
				"invocationId": target,
				"result":       map[string]any{"text": operation.text},
			})
			logf("ORIGINAL_RESULT_SENT invocationId=%s", target)
			return
		}
		delete(p.pending, target)
		p.send(p.nextID("c"), in.MessageID, "plugin.cancelled", map[string]any{
			"targetOperationId": target,
			"disposition":       "cancelled",
		})
		logf("CANCELLED_SENT targetOperationId=%s disposition=cancelled", target)
		if operation.emitLate {
			p.send(p.nextID("r"), operation.messageID, "tools.result", map[string]any{
				"invocationId": target,
				"result":       map[string]any{"text": operation.text + " (late)"},
			})
			logf("LATE_RESULT_SENT invocationId=%s", target)
		}
		return
	}
	messageID := ""
	if target == cancelTarget && !p.used("m10") {
		messageID = "m10"
	} else {
		messageID = p.nextID("c")
	}
	p.sendWithID(messageID, in.MessageID, "plugin.cancelled", map[string]any{
		"targetOperationId": target,
		"disposition":       "too_late",
	})
	logf("CANCELLED_SENT targetOperationId=%s disposition=too_late", target)
}

func (p *plugin) handleShutdown(in frame) (stop bool) {
	messageID := "m12"
	if p.used("m12") {
		messageID = p.nextID("s")
	}
	if p.fault == "shutdown-no-reply" {
		logf("FAULT shutdown-no-reply")
		return false
	}
	// inFlightCount 必须是真实挂起数；默认轨迹没有挂起操作，仍逐帧保持
	// golden 的 inFlightCount=0。
	inFlight := len(p.pending)
	switch p.fault {
	case "shutdown-wrong-correlation":
		p.writeWithID(p.nextID("s"), "not-the-shutdown-message-id", "plugin.stopped", map[string]any{
			"inFlightCount": inFlight,
		})
		logf("FAULT shutdown-wrong-correlation")
		return true
	case "shutdown-bad-inflight":
		p.writeWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": true,
		})
		logf("FAULT shutdown-bad-inflight")
		return true
	case "shutdown-negative-inflight":
		p.writeWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": -1,
		})
		logf("FAULT shutdown-negative-inflight")
		return true
	case "shutdown-duplicate":
		p.sendWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": inFlight,
		})
		p.send(p.nextID("s"), in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": inFlight,
		})
		logf("FAULT shutdown-duplicate")
		return true
	case "shutdown-zero-inflight":
		// 自报 0 但实际仍有挂起操作：用于验证 Host 不以 Plugin 自报计数
		// 判定本地待决操作的终态。
		p.sendWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": 0,
		})
		logf("FAULT shutdown-zero-inflight actual=%d", inFlight)
		return true
	case "shutdown-excess-inflight":
		// 自报比实际更多：用于验证 Host 只记录诊断，不据此提升或伪造终态。
		p.sendWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{
			"inFlightCount": inFlight + 1,
		})
		logf("FAULT shutdown-excess-inflight actual=%d", inFlight)
		return true
	}
	p.sendWithID(messageID, in.MessageID, "plugin.stopped", map[string]any{"inFlightCount": inFlight})
	logf("STOPPED_SENT inFlightCount=%d", inFlight)
	return true
}

func (p *plugin) hasExtension(name string) bool {
	for _, extension := range p.extensions {
		if extension == name {
			return true
		}
	}
	return false
}

func (p *plugin) used(messageID string) bool {
	_, ok := p.outgoingIDs[messageID]
	return ok
}

func (p *plugin) nextID(prefix string) string {
	p.seq++
	return fmt.Sprintf("%s%d", prefix, p.seq)
}

// send allocates the next dynamic messageId for messageType.
func (p *plugin) send(messageID, correlationID, messageType string, payload map[string]any) {
	p.sendWithID(messageID, correlationID, messageType, payload)
}

// sendFixed emits a pinned golden messageId exactly once.
func (p *plugin) sendFixed(messageID, correlationID, messageType string, payload map[string]any) {
	if p.used(messageID) {
		p.violation("DUPLICATE_LOCAL_MESSAGE_ID", messageType, messageID)
	}
	p.sendWithID(messageID, correlationID, messageType, payload)
}

func (p *plugin) sendWithID(messageID, correlationID, messageType string, payload map[string]any) {
	if _, duplicate := p.outgoingIDs[messageID]; duplicate {
		p.violation("DUPLICATE_LOCAL_MESSAGE_ID", messageType, messageID)
	}
	p.outgoingIDs[messageID] = struct{}{}
	p.writeWithID(messageID, correlationID, messageType, payload)
}

// writeWithID writes a frame without enforcing local messageId uniqueness. It
// exists only so the test-only duplicate-result fault can emit a duplicate.
func (p *plugin) writeWithID(messageID, correlationID, messageType string, payload map[string]any) {
	out := map[string]any{
		"apiVersion": apiVersion,
		"messageId":  messageID,
		"type":       messageType,
		"payload":    payload,
	}
	if correlationID != "" {
		out["correlationId"] = correlationID
	}
	p.write(out)
}

func (p *plugin) write(out map[string]any) {
	encoded, err := json.Marshal(out)
	if err != nil {
		p.violation("ENCODE_FAILED", "", err.Error())
	}
	encoded = append(encoded, '\n')
	if _, err := os.Stdout.Write(encoded); err != nil {
		p.violation("STDOUT_WRITE_FAILED", "", err.Error())
	}
}

func (p *plugin) violation(code, where, detail string) {
	logf("PROTOCOL_VIOLATION code=%s frame=%s field_or_id=%s", code, where, detail)
	os.Exit(2)
}

func logf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "echo-plugin: "+format+"\n", args...)
}
