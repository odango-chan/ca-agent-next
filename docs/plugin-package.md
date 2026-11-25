# Plugin Package v1alpha1

**Status:** normative target contract for ca-agent-next and all native Plugins. The document is part of the open architecture PR; it is not an implementation claim.

## 1. One Plugin mechanism

A Plugin is one independently running package/process managed by the single Python Plugin Manager. One process may expose any combination of:

- event.ingress — Plugin publishes normalized external Events to Host;
- event.delivery — Host sends a structured response to the originating Plugin;
- tools — Host invokes callable Tool operations exported by the Plugin.

A Tool is an operation, not a process, manager or Runtime. There is no separate Provider Manager, Tool registry, Event Registry or Delivery manager.

The Plugin Manager owns process lifecycle, handshake, IPC framing, correlation and extension dispatch. It does not select Skills, authorize Actions or decide Owner outcomes.

## 2. Package layout and manifest

A native Plugin package contains one YAML manifest, its executable and the local assets it owns.

~~~text
plugins/openamsm/
├── plugin.yaml
├── bin/
│   └── ca-openamsm-plugin
└── schemas/
    ├── create-sm-context.request.schema.yaml
    ├── update-sm-context.request.schema.yaml
    └── response.schema.yaml
~~~

The manifest is YAML-first. Tool definitions are not copied into it.

~~~yaml
apiVersion: connectionagent.io/plugin-package/v1alpha1
kind: Plugin
metadata:
  id: urn:connectionagent:plugin:openamsm
  version: 0.1.0

process:
  executable: bin/ca-openamsm-plugin
  args: [serve]
  protocol: connectionagent.io/plugin-ipc/v1alpha1

extensions:
  event.ingress:
    events:
      - type: nsmf.create-sm-context
        description: Normalized Nsmf CreateSMContext request.
        requestSchema: schemas/create-sm-context.request.schema.yaml
        artifacts:
          - slot: n1.request
            mediaType: application/vnd.3gpp.5gnas
            required: true
          - slot: n2.request
            mediaType: application/vnd.3gpp.ngap
            required: false
        artifacts:
          input:
            - slot: n1.request
              mediaType: application/vnd.3gpp.5gnas
              required: true
            - slot: n2.request
              mediaType: application/vnd.3gpp.ngap
              required: false

      - type: nsmf.update-sm-context
        description: Normalized Nsmf UpdateSMContext request carrying Modify or UE-requested Release.
        requestSchema: schemas/update-sm-context.request.schema.yaml
        artifacts:
          input:
            - slot: n1.request
              mediaType: application/vnd.3gpp.5gnas
              required: true

      - type: nsmf.update-sm-context.continuation
        description: Normalized continuation input for an existing UpdateSMContext Run.
        requestSchema: schemas/update-sm-context.continuation.schema.yaml
        artifacts:
          input:
            - slot: n1.confirmation
              mediaType: application/vnd.3gpp.5gnas
              required: false
            - slot: n2.confirmation
              mediaType: application/vnd.3gpp.ngap
              required: false

  event.delivery:
    responses:
      - eventType: nsmf.create-sm-context
        responseSchema: schemas/response.schema.yaml
        artifacts:
          output:
            - slot: n1.response
              mediaType: application/vnd.3gpp.5gnas
              required: false
            - slot: n2.response
              mediaType: application/vnd.3gpp.ngap
              required: false
        artifacts:
          output:
            - slot: n1.response
              mediaType: application/vnd.3gpp.5gnas
              required: false
            - slot: n2.response
              mediaType: application/vnd.3gpp.ngap
              required: false
      - eventType: nsmf.update-sm-context
        responseSchema: schemas/response.schema.yaml
        artifacts:
          output:
            - slot: n1.response
              mediaType: application/vnd.3gpp.5gnas
              required: false
            - slot: n2.response
              mediaType: application/vnd.3gpp.ngap
              required: false
      - eventType: nsmf.update-sm-context.continuation
        responseSchema: schemas/response.schema.yaml
~~~

Manifest rules:

- apiVersion and process.protocol are exact versions. No aliases, fallback versions or legacy compatibility.
- metadata.id identifies the Plugin; metadata.version identifies the installed Plugin release.
- process.executable is relative to the installed package root. process.args is passed as an argument vector without shell interpretation.
- extensions contains one or more of event.ingress, event.delivery and tools. A Plugin may expose all three in one process.
- Event schemas describe the normalized Event payload. They do not contain Skill IDs, business Goals, execution modes or authorization grants.
- An Event declaration may include `artifacts` slot declarations (slot, mediaType and required) when the SBI operation carries binary parts. Slot names and requiredness must follow the operation's 3GPP OpenAPI definition and [Plugin Artifact Handoff](plugin-artifact-handoff.md); they are not a second protocol Schema.
- An Event may declare artifacts.input slots; a delivery response may declare artifacts.output slots. Each slot has an exact slot name, mediaType and required flag. The Event Schema and OpenAMSM operation mapping determine conditional requirements; undeclared slots are rejected.
- event.delivery pairs a response schema with the originating event type. Host records the response obligation; Plugin does not choose which Run or response to deliver.
- tools.interfacePackage points to the canonical Tool Interface Package. Callable IDs, input/output Schemas, Effects, Capability membership and Owner outcome semantics remain owned by that package.
- Unknown fields, duplicate YAML keys, missing fields, unsupported versions, invalid Schema references and paths escaping the package root fail Plugin loading with an actionable diagnostic.

The manifest is not a second business Contract, ToolCatalog, Skill descriptor or authorization document.

## 3. Package loading and lifecycle

At Host startup, the one Plugin Manager:

1. Loads plugin.yaml with a safe YAML 1.2 parser.
2. Validates the manifest shape, exact API version, Plugin identity and extension declarations.
3. Resolves executable and local Schema paths relative to the package root. Reject absolute paths, traversal and symlinks escaping the root.
4. Validates declared Event Schemas and loads a Tool Interface Package using that package's own canonical contract.
5. Starts the executable directly, performs the common IPC handshake and compares the Plugin's reported identity, protocol and extensions with the manifest.
6. Makes only the verified extensions available. A failed package or handshake leaves that Plugin unavailable.

The Demo uses explicit installed package paths and operator-provided process arguments. A deployment change and Host restart are sufficient to add or change a Plugin. No Marketplace, installer, automatic download, hot reload, package signature or Trust Registry is required.

This is basic correctness validation, not a package-integrity framework. Do not add extra Plugin/Event SHA-256 snapshots or package signatures. Existing Compiler/Interface Package identity rules remain with their owners.

## 4. Normalized Event envelope

The Event Plugin owns external protocol parsing and normalization. Host receives only a declared Event type and its normalized payload.

~~~json
{
  "eventId": "event-123",
  "ingressId": "openamsm.nsmf",
  "eventType": "nsmf.create-sm-context",
  "externalRequestId": "protocol-stable-request-id",
  "responseChannelId": "plugin-local-channel-456",
  "source": {
    "protocol": "3gpp-sbi",
    "peerId": "authenticated-peer"
  },
  "payload": {
    "requestType": 1
  },
  "artifacts": []
}
~~~

Fields:

- eventId: unique logical Event instance ID; distinct from an IPC messageId and an HTTP/2 stream ID.
- ingressId: exact declared ingress extension ID.
- eventType: exact declared normalized Event type.
- externalRequestId: stable protocol request/retry identity when the external operation defines one. It must not be an HTTP/2 stream ID. If an operation has no reliable retry identity, its retry/replay behavior remains an explicit integration blocker; do not invent a false guarantee.
- responseChannelId: opaque Plugin-local handle for the current external response channel. It is not a Host Run ID and is not a durable business identity.
- source: protocol and authenticated peer context established by the Plugin.
- payload: normalized JSON input validated against the declared Event request Schema.
- artifacts: optional inbound binary descriptors defined by the Host Artifact Handoff contract.

The Host assigns Run IDs and responseObligationIds. The Plugin never supplies a Skill ID, selects a Skill, names a Run or chooses execution mode.

For the same stable externalRequestId, an identical retry attaches a new response obligation to the original Run. Reuse with different normalized content is a conflict. The Host must compare the actual normalized values and referenced bytes as needed; no semantic-content digest is introduced. If identity or equality cannot be established, fail closed rather than repeat a mutation.

The Event payload is the input offered to Skill selection. An Assurance Skill's requestSchema, when present, must also accept the normalized input. No generic business projection layer is added.

## 5. Common IPC v1alpha1

Native Plugin processes use UTF-8 NDJSON over stdin/stdout:

- Host writes frames to Plugin stdin.
- Plugin writes frames to stdout.
- stdout is protocol-only; diagnostics go to stderr.
- One long-lived process connection serves initialization, Event ingress, Tools, Delivery, cancellation and shutdown.
- The Plugin must not import Python Host modules or create a second Host API.

Every frame has one envelope:

~~~json
{
  "apiVersion": "connectionagent.io/plugin-ipc/v1alpha1",
  "messageId": "frame-123",
  "correlationId": "frame-100",
  "type": "ingress.ack",
  "payload": {}
}
~~~

Envelope semantics:

- apiVersion: exact IPC version.
- messageId: unique ID for this frame.
- correlationId: required for a reply or a message continuing an existing request; it equals the messageId of the request being answered. It may be omitted for an unsolicited ingress.event.
- type: exact message type from the inventory below.
- payload: type-specific object.

messageId, correlationId, eventId, invocationId, deliveryId, responseObligationId and Run ID are distinct identities. Do not substitute one for another.

### 5.1 Message inventory and required payloads

| Direction | Type | Required payload fields | Meaning |
|---|---|---|---|
| Host → Plugin | host.initialize | pluginId, expectedVersion, ipcVersion, config | Start configuration and negotiated IPC version. When binary transfer is enabled, includes Host-created artifactStaging.inboundDirectory and artifactStaging.outboundDirectory. |
| Plugin → Host | plugin.ready | pluginId, pluginVersion, ipcVersion, extensions | Confirms identity, protocol and exact extension IDs/types implemented by this process. |
| Plugin → Host | ingress.event | eventId, ingressId, eventType, externalRequestId, responseChannelId, source, payload, artifacts | Publish one normalized external Event. correlationId is omitted unless the Event is itself a continuation of a correlated IPC operation. |
| Host → Plugin | ingress.ack | eventId, disposition, runId?, responseObligationId?, artifactRefs?, error? | Accepted, duplicate attached, conflict or rejected disposition. |
| Host → Plugin | tools.invoke | invocationId, callableId, arguments, invocationContext, artifactRefs, deadlineMs? | Invoke one authorized Tool operation. Runtime has already checked the selected Skill, Capability, Effect and input Schema. |
| Plugin → Host | tools.result | invocationId, result? or error | Return the Tool result matching the owning Interface Package, or a transport/operation error. |
| Host → Plugin | delivery.dispatch | deliveryId, runId, responseObligationId, eventType, statusCode, headers, body, artifacts | Deliver the Host-validated response for the recorded obligation. |
| Plugin → Host | delivery.result | deliveryId, disposition, statusCode?, error? | Report delivered, failed or unknown. |
| Host → Plugin | host.cancel | targetMessageId or targetOperationId, reason | Request cancellation where the operation supports it. |
| Plugin → Host | plugin.cancelled | targetOperationId, disposition | Report cancelled, too_late or unsupported. |
| Host → Plugin | host.shutdown | gracePeriodMs | Stop accepting new work and shut down. |
| Plugin → Host | plugin.stopped | inFlightCount | Confirm process stop and report remaining in-flight work. |

Type-specific requirements:

- host.initialize must provide the Plugin's exact package identity and the one supported IPC version. Plugin must not choose a different version.
- plugin.ready must report only extensions declared in plugin.yaml. A mismatch fails the handshake.
- ingress.ack disposition is one of accepted, duplicate_attached, conflict or rejected. accepted and duplicate_attached include Host-assigned runId and responseObligationId. Rejected/conflict includes error.
- tools.invoke uses the exact callableId and argument shape from the canonical Tool Interface Package. invocationContext carries only the Host invocation fields declared by that Tool binding's existing hostInvocation contract; it does not create a second context schema. Runtime authorizes before dispatch. Tool Plugin does not grant Capability or choose a Skill.
- tools.result returns the Interface Package-defined result. Owner Receipt, Commit Proof and outcome semantics are interpreted by Runtime from the owning contract; Plugin transport success is not business COMMITTED.
- delivery.dispatch is addressed by responseObligationId created by Host. It includes the exact status, headers, structured body and only the authorized outbound artifact descriptors.
- delivery.result disposition is delivered, failed or unknown. An ambiguous delivery remains unknown; it never changes the Owner business outcome.
- Cancellation is best-effort. A too_late or unsupported response must not be interpreted as rollback of an external mutation.
- A malformed frame, invalid JSON, unsupported message type, mismatched correlation or invalid payload produces a clear protocol error and fails the affected operation closed.

### 5.2 Error shape

An operation error uses one common object:

~~~json
{
  "code": "PLUGIN_OPERATION_FAILED",
  "message": "The external operation failed.",
  "retryable": false,
  "details": {}
}
~~~

code and message are required. retryable is required and is a transport/retry hint only; it does not assert that a business mutation did not commit. details is optional diagnostic context and must not contain secrets or raw binary payloads.

### 5.3 Lifecycle

~~~text
CONFIGURED → STARTING → READY
                     ↘ NOT_READY
READY → STOPPING → STOPPED
~~~

One Plugin process may handle concurrent requests, but it must serialize writes to stdout and correlate each reply to its request. A Plugin failure makes only its own extensions unavailable. No automatic hot reload or production supervisor is required.

## 6. Tool Plugin and ca-client-tools

`ca-client-tools` is the OpenAMSM Tool implementation and canonical owner of its Tool Interface Package and Provider runtime bindings. It is loaded as the Plugin exposing the `tools` extension; an individual Tool remains a callable operation in that extension, not a separate Plugin process. `ca-openamsm-plugin` is the Event ingress/delivery Plugin and must not duplicate Owner operations.

The current `ca-client-tools` executable speaks its existing provider/v2 process protocol, not this native Plugin IPC. During migration, one Tool-extension adapter inside the single Plugin Manager translates the common Runtime Action invocation to provider/v2 and translates the result back. This is a transport adapter owned by Plugin Manager, not a second Provider Manager, Tool registry, Runtime or authorization path.

Protocol Codec operations may be added to the same Tool Plugin through its canonical Interface Package. They use the existing Go codec packages/Worker/Facade and are invoked exactly like other Tools. A Skill calls Decode only when it needs structured protocol fields; otherwise it can pass the original artifactRef to a business Tool. Do not create a separate Codec Plugin/Manager or duplicate codec code in Host/Event Plugin.

The current `protocol/nas5gsm` package is a pure Go codec library for a narrow 5GSM Establishment Request slice. It is not yet an Agent-callable Tool, and it does not establish full NAS/NGAP coverage. Do not expose it to Skills until the callable operation and Schema are published in the Interface Package and the exact message subset is accepted.

Do not fork the Go Provider, reimplement its Tool catalog in Python or copy its private Owner bindings into the OpenAMSM Event Plugin.

## 7. Host Artifact Handoff

Binary N1/N2 data uses the Host-owned staging and ArtifactStore contract in [Plugin Artifact Handoff](plugin-artifact-handoff.md). It is not embedded in NDJSON, Base64-encoded, or stored in a Plugin-owned database.

The Plugin receives Host-created inbound/outbound staging directories only when its declared extensions require binary transfer. The Host validates and imports inbound files, issues opaque artifactRefs, authorizes access per Run/Action, stages authorized outbound files and cleans temporary files.

## 8. OpenAMSM integration boundary

- The OpenAMSM Event Plugin owns SBI listener/wire handling, JSON/multipart and Content-ID parsing, normalized Event publication and response encoding. It preserves original N1/N2 bytes and does not eagerly deep-decode them for business reasoning.
- Host owns Event validation, Skill selection, Run identity, retry/replay, response obligations, resource/alias mapping, ArtifactStore, authorization and delivery records.
- ca-client-tools owns Tool implementation, private backend binding, Owner-facing calls and any Codec Tool operations it actually publishes.
- OpenAMSM Owner/SMF remains authoritative for SM Context identity, existence and business mutation outcomes.
- The Plugin never selects a Skill. Every fresh request binds a Skill first; optional assurance/contract.yaml.when is evaluated by the Host Resolver.
- A selected Skill may invoke a Codec Tool through the normal Runtime Action Boundary when it needs NAS/NGAP fields. Decode is optional; the original artifact remains the source for any later forwarding.
- Establish, Modify and UE-requested Release are separate Skill cases. Modify and Release may arrive through the same Nsmf service operation and must be distinguished only by fields validated in the normalized Event Schema. Do not infer the Skill from an HTTP path alone.
- Exact mapping of Create/Update/Release and release continuation messages to OpenAMSM OpenAPI operations, Event fields and stable externalRequestId is a pre-implementation acceptance gate.

## 9. Demo constraints

Do not add:

- a second Plugin IPC or compatibility alias;
- a separate Provider Manager, Tool registry, Event Registry or business Contract Package;
- extra SHA-256 Plugin/Event/Artifact hashing, package signatures or Trust Registry;
- a Plugin-owned Artifact database or Base64 binary transport;
- legacy compatibility, Marketplace, automatic downloads, hot reload or production-grade DFX.

Keep basic manifest/Schema/version/reference validation, path containment, clear errors, explicit process configuration, minimal correlation and useful logs. Existing Compiler/Interface Package identity rules remain owned by their canonical contracts.
