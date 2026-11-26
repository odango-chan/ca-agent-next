// Command echo-plugin is the reusable Echo fixture for the Native Plugin IPC
// v1alpha1 contract.  It is a clean protocol implementation: it has no
// test-only fault modes.  The A-batch negative cases are injected by the
// Python test Host (see tests/).
//
// Expected values are copied from the pinned design record
// docs/规范/插件包与进程通信协议规范.md §5.1 at
// ca-agent-next 5b097e28e7197603cf3f00e103a0315c4bce0d79.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"os"
)

const (
	apiVersion      = "connectionagent.io/plugin-ipc/v1alpha1"
	pluginID        = "example.echo"
	pluginVersion   = "1.0.0"
	ipcVersion      = "connectionagent.io/plugin-ipc/v1alpha1"
	callableID      = "echo.read"
	eventID         = "evt1"
	eventType       = "echo.request"
	externalRequest = "client-1"
	responseChannel = "ch1"
	invocationID    = "inv1"
	deliveryID      = "del1"
	obligationID    = "obl1"
	cancelTarget    = "inv1"
)

type frame struct {
	APIVersion    string         `json:"apiVersion"`
	MessageID     string         `json:"messageId"`
	CorrelationID string         `json:"correlationId,omitempty"`
	Type          string         `json:"type"`
	Payload       map[string]any `json:"payload"`
}

type plugin struct {
	hostIDs     map[string]struct{}
	outgoingIDs map[string]struct{}
}

func main() {
	for _, argument := range os.Args[1:] {
		switch argument {
		case "serve":
			// The documented manifest argv is [serve].
		case "--version", "version":
			fmt.Printf("echo-plugin %s (%s)\n", pluginVersion, ipcVersion)
			return
		default:
			fmt.Fprintf(os.Stderr, "echo-plugin: unsupported argument %q (usage: echo-plugin serve)\n", argument)
			os.Exit(2)
		}
	}
	p := &plugin{
		hostIDs:     map[string]struct{}{},
		outgoingIDs: map[string]struct{}{},
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
		p.handleShutdown(in)
		return true
	default:
		p.violation("UNKNOWN_MESSAGE_TYPE", in.Type, in.MessageID)
	}
	return false
}

func (p *plugin) handleInitialize(in frame) {
	if in.CorrelationID != "" {
		p.violation("UNEXPECTED_CORRELATION", in.Type, in.CorrelationID)
	}
	if in.Payload["pluginId"] != pluginID || in.Payload["expectedVersion"] != pluginVersion || in.Payload["ipcVersion"] != ipcVersion {
		p.violation("INITIALIZE_IDENTITY_MISMATCH", in.Type, "")
	}
	if _, ok := in.Payload["config"].(map[string]any); !ok {
		p.violation("INITIALIZE_CONFIG_INVALID", in.Type, "")
	}
	p.emit("m2", in.MessageID, "plugin.ready", map[string]any{
		"pluginId":      pluginID,
		"pluginVersion": pluginVersion,
		"ipcVersion":    ipcVersion,
		"extensions":    []any{"event.ingress", "event.delivery", "tools"},
	})
	p.emit("m3", "", "ingress.event", map[string]any{
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
	if in.CorrelationID != "m3" || in.Payload["eventId"] != eventID {
		p.violation("ACK_CORRELATION_MISMATCH", "ingress.ack", "")
	}
	disposition, _ := in.Payload["disposition"].(string)
	switch disposition {
	case "accepted", "duplicate_attached", "conflict", "rejected":
	default:
		p.violation("ACK_DISPOSITION_INVALID", "ingress.ack", disposition)
	}
	if disposition != "accepted" {
		p.violation("ACK_UNEXPECTED_DISPOSITION", "ingress.ack", disposition)
	}
	logf("ACK_ACCEPTED eventId=%s", eventID)
}

func (p *plugin) handleInvoke(in frame) {
	if in.Payload["invocationId"] != invocationID || in.Payload["callableId"] != callableID {
		p.violation("INVOKE_IDENTITY_MISMATCH", "tools.invoke", "")
	}
	arguments, ok := in.Payload["arguments"].(map[string]any)
	if !ok || arguments["text"] != "hello" {
		p.violation("INVOKE_ARGUMENTS_INVALID", "tools.invoke", "")
	}
	p.emit("m6", in.MessageID, "tools.result", map[string]any{
		"invocationId": invocationID,
		"result":       map[string]any{"text": "hello"},
	})
	logf("RESULT_SENT invocationId=%s", invocationID)
}

func (p *plugin) handleDelivery(in frame) {
	if in.Payload["deliveryId"] != deliveryID || in.Payload["responseObligationId"] != obligationID ||
		in.Payload["responseChannelId"] != responseChannel || in.Payload["eventType"] != eventType {
		p.violation("DELIVERY_IDENTITY_MISMATCH", "delivery.dispatch", "")
	}
	if status, ok := in.Payload["statusCode"].(float64); !ok || status != 200 {
		p.violation("DELIVERY_STATUS_INVALID", "delivery.dispatch", "")
	}
	p.emit("m8", in.MessageID, "delivery.result", map[string]any{
		"deliveryId":  deliveryID,
		"disposition": "delivered",
		"statusCode":  200,
	})
	logf("DELIVERY_RESULT_SENT deliveryId=%s", deliveryID)
}

func (p *plugin) handleCancel(in frame) {
	if in.Payload["targetOperationId"] != cancelTarget {
		p.violation("CANCEL_TARGET_MISMATCH", "host.cancel", "")
	}
	p.emit("m10", in.MessageID, "plugin.cancelled", map[string]any{
		"targetOperationId": cancelTarget,
		"disposition":       "too_late",
	})
	logf("CANCELLED_SENT targetOperationId=%s disposition=too_late", cancelTarget)
}

func (p *plugin) handleShutdown(in frame) {
	p.emit("m12", in.MessageID, "plugin.stopped", map[string]any{"inFlightCount": 0})
	logf("STOPPED_SENT inFlightCount=0")
}

func (p *plugin) emit(messageID, correlationID, messageType string, payload map[string]any) {
	if _, duplicate := p.outgoingIDs[messageID]; duplicate {
		p.violation("DUPLICATE_LOCAL_MESSAGE_ID", messageType, messageID)
	}
	p.outgoingIDs[messageID] = struct{}{}
	out := map[string]any{
		"apiVersion": apiVersion,
		"messageId":  messageID,
		"type":       messageType,
		"payload":    payload,
	}
	if correlationID != "" {
		out["correlationId"] = correlationID
	}
	encoded, err := json.Marshal(out)
	if err != nil {
		p.violation("ENCODE_FAILED", messageType, err.Error())
	}
	encoded = append(encoded, '\n')
	if _, err := os.Stdout.Write(encoded); err != nil {
		p.violation("STDOUT_WRITE_FAILED", messageType, err.Error())
	}
}

func (p *plugin) violation(code, where, detail string) {
	logf("PROTOCOL_VIOLATION code=%s frame=%s field_or_id=%s", code, where, detail)
	os.Exit(2)
}

func logf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "echo-plugin: "+format+"\n", args...)
}
