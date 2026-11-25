# Plugin Package v1alpha1

**Status:** proposed Next Demo contract. This document defines the YAML package manifest and the minimal common Plugin process boundary. It does not define a Marketplace, package trust platform or business contract registry.

## 1. Package layout

A Plugin is one independently running process/package. Its installed directory contains a YAML manifest, its executable, and only the local Event Schemas or other assets it owns.

~~~text
plugins/echo/
├── plugin.yaml
├── bin/
│   └── echo
├── schemas/
│   ├── echo-request.schema.yaml
│   └── echo-response.schema.yaml
└── interface/
    └── <Compiler-owned Tool Interface Package files>
~~~

The Tool Interface Package keeps its own canonical format. Do not rewrite it to match the Plugin manifest or copy its Tool definitions into plugin.yaml.

## 2. YAML manifest

~~~yaml
# plugin.yaml
apiVersion: connectionagent.io/plugin-package/v1alpha1
kind: Plugin
metadata:
  id: urn:example:plugin:echo
  version: 0.1.0

process:
  executable: bin/echo
  args: [serve]
  protocol: connectionagent.io/plugin-ipc/v1alpha1

extensions:
  event.ingress:
    events:
      - type: echo.request
        description: Receive an Echo request.
        requestSchema: schemas/echo-request.schema.yaml

  event.delivery:
    responses:
      - eventType: echo.request
        responseSchema: schemas/echo-response.schema.yaml

  tools:
    interfacePackage: interface/
~~~

Rules:

- metadata.id is a stable Plugin identity; metadata.version is the installed Plugin release version.
- process.executable is relative to the installed package root. process.args is passed as an argument vector, without shell interpretation.
- process.protocol selects the common Plugin IPC version.
- extensions declares one or more of event.ingress, event.delivery and tools. A Plugin may expose any combination in the same process.
- Each Event type has a normalized request Schema. A paired response declaration identifies the response Schema for that Event type.
- The tools extension references the existing Tool Interface Package. Callable IDs, input/output Schemas, Effects, Capability membership and Owner outcome semantics remain owned by that Interface Package.
- The manifest must not contain a Skill ID, business Goal, business Contract Package reference, execution mode or authorization grant.
- A Tool Plugin may export many Tool operations. Do not create one process per Tool.

## 3. Basic package validation

At startup the Plugin Manager:

1. Loads plugin.yaml with a YAML 1.2 safe parser.
2. Rejects invalid YAML, duplicate keys, unknown manifest fields, missing required fields, unsupported API versions and an empty extension set.
3. Validates the Plugin ID/version shape and the basic manifest Schema.
4. Resolves executable, Event Schema and Interface Package paths relative to the installed root. Reject absolute paths, path traversal and symlinks that escape the root.
5. Validates the referenced Event Schemas and loads the Tool Interface Package using its owning contract.
6. Starts the executable directly, performs the handshake and registers only the extensions confirmed by both manifest and Plugin.
7. Leaves the Plugin unavailable if preflight or handshake fails.

This is ordinary correctness validation. The Demo does not calculate an additional SHA-256 snapshot for the Plugin or Event package, require package signatures, run a Trust Registry, or implement a package-integrity framework. The Compiler/Interface Package may retain its own canonical identity rules where its owning contract requires them; the Host must not add a parallel hashing system.

Deployment configuration selects the installed package directory, executable configuration, endpoints and secret references. Adding or changing a Plugin requires an explicit deployment change and Host restart. No Marketplace, installer, automatic download or hot reload is required.

## 4. Normalized Event contract

The Event Plugin owns protocol decoding and normalization. The Host receives only the declared normalized Event type and payload.

Example Event declaration:

~~~yaml
# Part of plugin.yaml
extensions:
  event.ingress:
    events:
      - type: nsmf.create-sm-context
        description: A normalized Create SM Context request.
        requestSchema: schemas/create-sm-context.schema.yaml
~~~

Example ingress payload:

~~~json
{
  "eventId": "event-123",
  "ingressId": "openamsm.nsmf",
  "eventType": "nsmf.create-sm-context",
  "source": "authenticated-peer",
  "payload": {
    "requestType": 1
  }
}
~~~

The Event envelope contains:

- eventId: stable logical identity for this external event, distinct from the IPC frame ID;
- ingressId: the exact declared ingress extension;
- eventType: an exact event type declared in plugin.yaml;
- source: the authenticated or otherwise Plugin-established source identity;
- payload: normalized input validated against the Event request Schema.

The Event Plugin does not select a Skill and does not include a Skill ID or business-contract package reference. The normalized payload is the input offered to Skill selection. A selected Assurance requestSchema must accept that input; the Host does not guess or invent a business-specific projection.

For paired responses, the Host records an opaque response handle with the accepted Event and sends the structured response to the same originating Plugin process. Protocol-specific encoding remains inside that Plugin.

## 5. Common Plugin IPC

The initial Demo uses one long-lived child process per configured Plugin and UTF-8 NDJSON over stdin/stdout.

- Host writes protocol frames to Plugin stdin.
- Plugin writes protocol frames to stdout.
- stdout is protocol-only; diagnostics go to stderr.
- The Plugin does not import Python Host modules or expose a second Host control API.
- One connection carries initialization, Event ingress, Tool invocation, Delivery, cancellation and shutdown messages.

Every frame has this common envelope:

~~~json
{
  "apiVersion": "connectionagent.io/plugin-ipc/v1alpha1",
  "messageId": "frame-123",
  "correlationId": "request-456",
  "type": "message.type",
  "payload": {}
}
~~~

messageId identifies one transport frame. correlationId links a request and its reply or a long-running operation. Neither replaces the logical Event ID, Run ID or Owner invocation identity.

### 5.1 Message inventory

| Direction | Type | Purpose |
|---|---|---|
| Host → Plugin | host.initialize | Supply Plugin identity, supported IPC version and deployment configuration |
| Plugin → Host | plugin.ready | Confirm Plugin identity, release version, IPC version and available extensions |
| Plugin → Host | ingress.event | Submit a normalized Event |
| Host → Plugin | ingress.ack | Return accepted, duplicate, conflict or rejected disposition and Run reference when accepted |
| Host → Plugin | tools.invoke | Invoke an exported Tool operation |
| Plugin → Host | tools.result | Return Tool output or a structured error/result |
| Host → Plugin | delivery.dispatch | Deliver a validated structured response to the originating Plugin |
| Plugin → Host | delivery.result | Report delivered, failed or unknown |
| Host → Plugin | host.cancel | Request cancellation of a correlated operation where supported |
| Plugin → Host | plugin.cancelled | Confirm cancellation disposition |
| Host → Plugin | host.shutdown | Stop accepting new work and shut down |
| Plugin → Host | plugin.stopped | Confirm process shutdown |

The exact required fields for each payload are defined by the IPC message Schema in the implementation. Do not create a second IPC protocol for Tools or Event Delivery.

### 5.2 Lifecycle

~~~text
CONFIGURED → STARTING → READY
                     ↘ NOT_READY
READY → STOPPING → STOPPED
~~~

A failed Plugin makes its own bindings unavailable. The Demo does not require automatic hot reload or a general restart supervisor.

## 6. Runtime and Tool ownership

- The Runtime validates each proposed Action, selected Skill scope, Capability, Effect, Schema and budget before dispatch.
- The Plugin Manager routes the authorized invocation to the Tool extension of the selected Plugin.
- The Tool Plugin performs the external call and returns the result or Owner receipt it actually received.
- The Runtime remains the sole authority for normalizing outcomes and recording Evidence.
- A Tool Plugin cannot grant itself Capability, choose a Skill, or turn HTTP success/model text into COMMITTED.
- The Interface Package remains the single authority for Tool contracts. Plugin registration/availability is not invocation authorization.

The released ca-client-tools.provider/v2 process may initially be consumed by a Tool-extension adapter inside this Plugin Manager. This adapter is temporary protocol reuse, not a second permanent Provider Manager or Runtime.
