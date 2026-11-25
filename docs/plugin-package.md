# Plugin Package v1alpha1

**Status:** proposed Next Demo contract. Package schema, IPC protocol and Plugin release version have independent identities.

A native Plugin is an installed, platform-specific directory. Its root contains a UTF-8 JSON manifest named `plugin.json`, a runnable entry point and referenced local contract snapshots. A release may be transported as an archive. The Host receives the installed directory from explicit deployment configuration.

```json
{
  "apiVersion": "connectionagent.io/plugin-package/v1alpha1",
  "id": "urn:example:plugin:echo",
  "version": "0.1.0",
  "process": {
    "executable": "bin/echo",
    "args": [],
    "protocol": "connectionagent.io/plugin-ipc/v1alpha1"
  },
  "extensions": {
    "event.ingress": { "eventPackage": "contracts/event-package.json" },
    "event.delivery": { "eventPackage": "contracts/event-package.json" },
    "tools": { "interfacePackage": "interface" }
  }
}
```

- Require the shown top-level fields, process fields and at least one supported extension. Extension names are unique. Reject duplicate JSON keys, unknown fields and unsupported versions. Use a stable URI for `id` and SemVer for `version`. Activate at most one release per Plugin ID in a deployment.
- Executable and contract references are relative paths within the installed root. Reject absolute paths, traversal and links escaping the root. Launch the platform executable directly with the declared argument list. Use NDJSON on stdio and logs on stderr. Deployment supplies operator configuration, endpoints and secret references separately.
- Deployment pins Plugin ID and version and the exact imported Event and Interface snapshots. Verify imports before startup. Event snapshot identity is SHA-256 of the UTF-8 compact JSON array of `[relativePath, lowercaseSha256Hex]` pairs sorted by path in UTF-8 byte order. Include the declaration and its transitive local Schema files, with slash-separated paths relative to the declaration's directory and literal UTF-8 for non-ASCII characters. Use the Compiler Interface Package's canonical snapshot digest for `tools`.
- The Event declaration identifies supported Event types, business-contract references and normalized request/response Schemas. Ingress and delivery share the declaration when both are present. The Tool Interface Package owns callable IDs, Schemas, Effects, Capabilities and Owner outcomes. The Plugin manifest references that package and the handshake advertises callable IDs, which must resolve exactly against the verified Interface Package.
- Preflight validates the manifest, local entry point and pinned imports. Handshake must confirm the ID, release version, protocol and extension set before registration. A rejected preflight or handshake leaves no active registration. Runtime authorizes each Tool invocation. The originating Event Plugin retains its protocol delivery handle.

The released `ca-client-tools.provider/v2` package contains an executable, `provider.yaml` and an Interface Package. A deployment-selected driver validates those native artifacts behind the same Plugin Manager. Verify the binding from released Interface exports to Provider operations before enabling the adapter in OpenAMSM integration.

## Event contract entry

For the Demo, the Event package entry is a JSON object with an `events` map keyed by normalized Event type. Each entry requires a `businessContract` object containing `id`, `version` and `digest` for the exact business contract, and a local `requestSchema` path. It also requires a local `responseSchema` path when the Event supports paired response delivery. Schema paths are relative to the entry file and remain within its directory. Example Event entry:

```json
{
  "events": {
    "echo.request": {
      "businessContract": {
        "id": "urn:example:echo:request",
        "version": "0.1.0",
        "digest": "sha256:2a8ed904f7da9e23ffe2cd84657f4c9e18e21af89569b926f64b01a7fd7c8d27"
      },
      "requestSchema": "echo.request.schema.json",
      "responseSchema": "echo.response.schema.json"
    }
  }
}
```

The example digest illustrates the field form. Resolve the reference from provisioned snapshots by exact identity before registration. Validate ingress and delivery payloads against the declared schemas. The deployment must provision the corresponding business contract and Skill independently of the Plugin executable. This entry describes fresh Event payloads and their immediate delivery contract. Reuse the existing typed Ingress/Correlation contract for richer paired-response and Wait semantics when integrating them.
