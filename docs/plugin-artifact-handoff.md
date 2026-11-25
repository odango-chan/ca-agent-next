# Plugin Artifact Handoff v1alpha1

**Status:** target Host/Plugin contract for binary Event and Delivery payloads. This is a Demo-level local-process handoff, not a new Artifact service.

## 1. Ownership

- Plugin owns external protocol parsing, multipart/Content-ID association and raw byte extraction/encoding.
- Host owns staging directories, ArtifactStore custody, opaque Artifact references, Run association, access authorization and cleanup.
- Runtime decides which Action may read or produce an Artifact.
- Tool Provider receives only Artifact references authorized for that invocation.
- Plugin does not own an Artifact database, durable namespace or Run lifecycle.

This handoff is between the Event/Delivery Plugin and Host. It is distinct from the existing Host-to-Provider binary channel used by ca-client-tools.

## 2. Local staging contract

When a Plugin declares binary Event or Delivery slots, host.initialize supplies two Host-created directories:

~~~json
{
  "artifactStaging": {
    "inboundDirectory": "/host-managed/plugin/openamsm/inbound",
    "outboundDirectory": "/host-managed/plugin/openamsm/outbound"
  }
}
~~~

The paths are process-local configuration, not portable package values. The Plugin writes inbound files only under inboundDirectory. The Host writes outbound files only under outboundDirectory. The Plugin never chooses the root directory.

Every IPC artifact descriptor uses a relative stagingPath, never an absolute path:

~~~json
{
  "slot": "n1.request",
  "mediaType": "application/vnd.3gpp.5gnas",
  "contentId": "n1SmMsg",
  "stagingPath": "event-123/n1.bin",
  "byteLength": 48
}
~~~

Required descriptor fields: slot, mediaType, stagingPath and byteLength. contentId is required when the source protocol provides a multipart Content-ID; otherwise it is omitted. Paths must remain under the supplied direction-specific root. Reject absolute paths, traversal, symlink escape, missing files and declared/actual byte-length mismatch.

No checksum or extra SHA-256 digest is introduced. The Host reads the actual file bytes before accepting the Event.

## 3. Inbound flow

1. Host creates and owns the inbound/outbound staging directories and passes them in host.initialize.
2. Plugin parses the external SBI body and writes each declared binary part to inboundDirectory using a relative path.
3. Plugin sends ingress.event with normalized JSON payload and artifact descriptors. It does not send raw bytes or Base64.
4. Host validates the Event Schema, slot declaration, media type, path containment and actual byte length.
5. Host imports the bytes into its existing ArtifactStore, associates opaque artifactRefs with the Event and Run, and only then returns ingress.ack.
6. ingress.ack returns the Host-issued artifactRefs corresponding to the accepted slots. The Plugin does not create or choose artifactRef values.

If import or validation fails, Host rejects the Event and does not start business execution.

## 4. Outbound flow

1. Runtime produces or receives an Artifact through an authorized Action/Tool result.
2. Host verifies that the response obligation permits the declared output slot and writes the exact bytes to outboundDirectory.
3. Host sends delivery.dispatch with responseObligationId and descriptors containing slot, mediaType, contentId when applicable, relative stagingPath, byteLength and opaque artifactRef.
4. Plugin reads only the declared outbound file, builds the required SBI multipart/Content-ID representation and returns delivery.result.
5. Host records delivery disposition and cleans the staged file. An ambiguous delivery is UNKNOWN and does not change the Owner outcome.

The Plugin cannot request arbitrary ArtifactStore reads. It receives only files staged for that delivery.

## 5. OpenAMSM slot conventions

Media types:

- NAS / 5GSM: application/vnd.3gpp.5gnas
- NGAP / N2: application/vnd.3gpp.ngap

Initial slot vocabulary:

| Slot | Direction | Meaning |
|---|---|---|
| n1.request | Inbound | Original N1 NAS message from the SBI request |
| n2.request | Inbound | Original N2 SM information when present in the SBI request |
| n1.confirmation | Inbound | N1 continuation/confirmation, including PDU Session Release Complete (0xD4), when delivered as a later ingress |
| n2.confirmation | Inbound | N2 continuation/confirmation, including PDU Session Resource Release Response, when delivered as a later ingress |
| n1.response | Outbound | Owner/Host-produced N1 NAS response for the recorded obligation |
| n2.response | Outbound | Owner/Host-produced N2 NGAP response for the recorded obligation |

Event-specific declarations decide which slots are required or optional. A Plugin must never fabricate an absent N1/N2 part.

### 5.1 Optional Codec Tool use

This handoff preserves and transports bytes; it does not require every N1/N2 artifact to be fully decoded. Before Skill selection, the Event Plugin may extract only the minimum protocol discriminator required to normalize an ambiguous shared SBI operation (for example, the NAS message type for UpdateSMContext). This is a narrow protocol-to-Event classification step, not a full decode or business decision; it must reuse the shared codec implementation and preserve the original artifact.

- If the selected Skill does not need inner protocol fields, it may pass the original `artifactRef` directly to the appropriate business Tool. No Codec invocation is required.
- If the Skill needs NAS/NGAP fields, it invokes the corresponding Codec Tool exported by the `ca-client-tools` Tool Plugin through the normal Runtime Action Boundary.
- The Host binds the Run-owned artifact to the specific Tool invocation and transfers it through the existing Host-to-Provider artifact channel. The Codec Tool returns a structured JSON projection; it does not replace or mutate the original artifact.
- An Encode Tool may return an output artifact reference. Host stages that artifact for the exact response obligation and the Event Plugin performs SBI multipart/Content-ID encoding.
- Codec Tool operations must be declared in the canonical Tool Interface Package and limited to the message subset actually implemented and tested. The current pure `protocol/nas5gsm` library is not automatically callable by a Skill.

Expected Skill inputs:

| Skill | Initial input |
|---|---|
| Establish | n1.request; n2.request only when the actual SBI operation carries it |
| Modify | n1.request containing the original PDU Session Modification Request (0xC9) |
| UE-requested Release | n1.request containing the original PDU Session Release Request (0xD1) |
| Release continuation | n1.confirmation and/or n2.confirmation, correlated by Host to the exact original Run and generation |

The native manifest declares these slots under event.ingress.events[].artifacts.input and event.delivery.responses[].artifacts.output, with slot, mediaType and required. The initial normalized Event types are nsmf.create-sm-context, nsmf.update-sm-context and nsmf.update-sm-context.continuation. Modify and UE-requested Release are distinguished from validated fields on UpdateSMContext; continuation Events resume the original Run and bypass fresh Skill selection. The actual SBI operation IDs, multipart part names, NAS discriminator field, optionality and response mapping must be checked against the current OpenAMSM OpenAPI and existing ca-agent-demo Host behavior before T3 implementation. In particular, UE-requested PDU Session Release is not interchangeable with AMF/network-initiated ReleaseSMContext.

## 6. Run and retry semantics

- Host assigns Run ID and responseObligationId after validating the Event.
- Plugin supplies externalRequestId only from a stable protocol request identity or an explicitly tested canonical request identity.
- An HTTP/2 stream ID is only a transient response channel and must never be used as the logical Event/Run identity.
- A same-request retry may attach a new response obligation to the existing Run; it must not repeat the Owner mutation.
- A reused externalRequestId with different normalized content or different actual Artifact bytes is a conflict.
- Release continuation artifacts must resolve to the same original Run, SUPI, PSI and session generation. A stale confirmation must not wake a newer Run.
- If an operation has no proven stable retry identity or continuation correlation, its real E2E gate remains NOT_RUN; do not claim safe replay.

No Event content digest, package digest or Artifact checksum is required by this handoff.

## 7. Cleanup and Demo limits

- Host cleans inbound staging files after successful import.
- Host cleans outbound staging files after delivery result or process shutdown.
- On process restart, Host may remove stale files under its own staging root; no Plugin database or recovery protocol is added.
- Keep path containment and file-length validation. Do not add a general sandbox, remote Artifact service, distributed storage, content-addressed store or production-grade DFX.
