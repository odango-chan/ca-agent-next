> 迁移来源：env-5gc-sim/docs/design/mock-amf-sbi-peer.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：Mock AMF 的进程、协议、状态、测试场景、验收序列与实现历史  
> 迁移追踪：ca-agent-next Issue #12。env-5gc-sim 同时包含 5GC reference simulator 与 Mock AMF test peer；两者在 Next 设计中分开描述。

---

# Mock AMF SBI Test Peer — Design

Status: Accepted (implementation tracked by #66)
Version: v0.7
Date: 2026-11-21
Owner: `env-5gc-sim`
Tracking: [#66](https://github.com/odango-chan/env-5gc-sim/issues/66)

Implementation status: D0–D2 are implemented and owner-local PASS for the
claimed scope (§16). **D3 is PASS** on Linux/WSL2 (§17) and was reproduced
natively on macOS/arm64 (§20). D4 (CA Agent parity) remains **BLOCKED**
(§15.5). No `FULL_INTERFACE_PARITY_PASS` is claimed by this document.

## 1. Purpose and status

This document defines a reusable AMF-side **SBI test peer** for 5GC PDU Session lifecycle integration tests. Its first consumers are the existing OpenAMSM NW-Agent (baseline) and the CA Agent Host (replacement candidate), both driving the **same real OpenAMSM SMF/MAS**. The peer lives in `env-5gc-sim` to share deterministic network-simulation engineering, fixtures, and maintenance ownership; it must not become a second SMF, orchestration engine, Runtime, or E2E Harness.

This is the **accepted design and implementation reference** for the independently runnable Mock AMF SBI test peer, **not a separately published OpenAPI**. The D0–D3 implementation and native macOS/arm64 evidence are recorded in §§16–20; UE-requested Release passes **only on the six-patch `env-openamsm#12` build**, while network-requested Release is blocked by `env-openamsm#10` on the real SMF. **`MOCK_AMF_V1_LIFECYCLE_ACCEPTED` and full-interface parity are not claimed**; D4 remains externally blocked (see §15.5). The existing `env-5gc-sim` deterministic reference world, C2/C6, PFCP/UDP process and its previously verified N4 slice are unchanged.

### 1.1 Verified starting point

The imported OpenAMSM snapshot contains:

- `tools/nw-agent/server.py`: HTTP/2 h2c Plan/Replan, Nsmf facade, Namf relay and IAM query proxy;
- `tools/nw-agent/orch_engine.py`: in-memory association, cursor, ledger, stepwise MAS Catalog Invoke, early Create 201/Location and asynchronous continuation after SIGNAL;
- `tools/nw-agent/openapi/Nnwagent_Relay.md`: the Namf relay forwards `N1N2MessageTransfer` to the **real AMF**, not to a mock;
- `tools/nw-agent/openapi/Nsmf_MasOrchestration.yaml`: SMF-side `/invoke` and `/sm-context-update-sync`, which are **not** Mock AMF APIs;
- `tools/test-console`: run/trace UI and agent mode control, not a canonical AMF simulator.

The OpenAMSM local acceptance on 2026-11-17 proved live UE registration, a PDU Session, AMF/SMF list reads and eight MAS Context Query calls. **It did not certify the new Mock AMF or full NW-Agent `agent_step` / CA Agent parity E2E.**

Source: `odango-chan/env-openamsm`, `upstream/openamsm/tools/nw-agent/` and `docs/acceptance-20261117.md`.

## 2. Goals and non-goals

### 2.1 First-slice goals (P0)

1. Implement an independent HTTP/2 AMF **peer** that can act as the AMF counterpart of a real SMF via standard 3GPP SBI messages, without requiring a real gNB/UE for the selected scenarios.
2. Drive Nsmf_PDUSession Create, Update and Release; receive Namf_Communication N1N2MessageTransfer and react according to a deterministic scenario.
3. Preserve the real SMF/MAS as the authority for SM Context and MAS domain state. Validate terminal state with independently read real SMF/MAS observations.
4. Correlate multiple UE and PDU Sessions exactly; support bounded out-of-order, duplicate, delayed and failed callback behavior without accidental cross-session delivery.
5. Allow the same scenario semantics and frozen reference vectors to run against (a) NW-Agent scheme C and (b) CA Agent Host as separate targets, producing comparable request/response and state evidence. Runtime-generated NAS and per-session N2 Transfer must match the scenario inputs.
6. Keep the peer independently runnable and deployable; its executable and scenario assets must not depend on NW-Agent, Agent Host, or OpenAMSM private in-process code.

### 2.2 Explicit non-goals

- Implementing AMF NAS security, full 5G MM registration, NGAP/SCTP, RAN/user-plane traffic or a complete 3GPP AMF.
- Replacing the real SMF, MAS, UDM/PCF/UPF or simulating their authoritative results.
- Creating another CA-SL Procedure engine, MAS execution engine, Agent-facing MCP, Runtime Outcome, Predicate evaluator, or Benchmark verdict source.
- Replacing `env-fabric` for protocol-boundary loss, delay or network Observation.
- Changing `env-5gc-sim` existing `serve` profile, WorldStore, C2/C6 JSON API, machine contracts or verified PFCP lifecycle in the design phase.
- Silently adapting private HTTP/1.1 payloads into 3GPP SBI or claiming protocol parity when target Host does not accept standard SBI.

## 3. Process topology and ownership

### 3.1 Real OpenAMSM E2E topology

```text
Scenario Runner / Test Console / external E2E Harness
       |
       +---- selects scenario, target, fixtures and assertions
       |
       v
Mock AMF (independent SBI peer; this repository)
       |  Nsmf_PDUSession over HTTP/2
       v
+------------------------------+     +------------------------------+
| target A: NW-Agent Scheme C  | OR  | target B: CA Agent Host      |
| Nsmf facade -> MAS invoke    |     | SBI ingress -> Skill Runtime |
+------------------------------+     +------------------------------+
                     \                 /
                      \               /
                       v             v
                     REAL OpenAMSM SMF / MAS
                            |
                  Namf_Communication N1N2
                            |
                            v
                       Mock AMF
                            |
                   scenario-triggered Nsmf Update
                            |
                            v
                     REAL OpenAMSM SMF

Assertion reader -> real OpenAMSM MAS Query / authorized NF read
Evidence collector -> wire events + peer event ledger + real SMF facts
```

The two targets are **alternatives**, not simultaneously authoritative proxies for one session. NW-Agent may internally relay Namf back to Mock AMF, but its own Nsmf facade and MAS operations are target-specific. An Agent Host target is eligible only once it provides compatible SBI ingress and outbound Namf connectivity. Inbound transport format must not be faked to bypass that gate.

### 3.1.1 Location routing and the actual OpenAMSM AMF override

**Critical implementation discovery.** The Create response `Location` contains the SM Context resource URI. Subsequent Update/Release ordinarily use that resource URI; it need not name the same host as the initial Nsmf Create target. The NW-Agent `Nnwagent_NsmfFacade.yaml` deliberately returns a **real SMF Location**. OpenAMSM's actual modified AMF implementation (`upstream/openamsm/src/amf/sbi-path.c`) nevertheless rewrites **all** Nsmf Create/Update/Release requests to NW-Agent in `agent_step` mode, replacing the URI apiRoot while retaining the path and SM Context reference. Direct business Update/Release to SMF can be **rejected** by `src/smf/nsmf-handler.c` in that mode.

The Mock AMF must support **explicit test-side routing profiles**, not silently assume one of them:

| Routing profile | Create and later operations | Use |
| --- | --- | --- |
| `location_follow` | Create to configured Nsmf apiRoot; later operations to the exact Create `Location` resource URI | General standard-style AMF behavior, may bypass Agent |
| `openamsm_agent_step_override` | Create and all later Nsmf operations to Agent apiRoot; preserve the SM Context resource path/ref on Update/Release | Actual OpenAMSM Scheme C AMF behavior, required for NW-Agent parity |
| `agent_owned_location` | Host returns an Agent-owned resource URI that subsequent operations follow | CA Agent option only after its full SBI lifecycle is verified |

Always retain and assert both `logicalSmContextUri` (the actual Create `Location`) and `effectiveRequestUri` (the destination actually called). The routing profile belongs to the **scenario runner**, never to a proprietary field in a 3GPP request body. A generic, unmodified Location-follow AMF test that reaches the SMF and receives a `403 AGENT_STEP_NSMF_REJECTED` is an explicit routing-compatibility result, **not** an unexplained Mock AMF malfunction.

### 3.2 Authority matrix

| Subject | Authority / responsibility | Explicit prohibition |
| --- | --- | --- |
| `env-5gc-sim` existing reference process | Simulated world, `worldRevision`, C2/C6 source facts, simulated NF behavior | No change to existing world or contracts for this test peer |
| New Mock AMF peer | AMF-side **test** UE/access association, SBI endpoint behavior, deterministic scenario event ledger | Must not answer as authoritative real SMF/UPF/MAS |
| Real OpenAMSM SMF / MAS | SM Context, PDU Session and MAS business state | Peer must not mutate private SMF State or invent success |
| NW-Agent / CA Agent Host | Their own execution and orchestration behavior | Peer must not choose or execute their MAS Operations |
| Test runner / Harness | Scenario deployment, orchestration, case result and assertions | Peer must not publish E2E PASS or Benchmark verdict |
| `env-fabric` | Actual network/protocol boundary mediation and Network Observation, when used | Peer must not fabricate Fabric events or loss receipts |
| `ca-runtime` / Evidence owners | Runtime Outcome, Predicate, admitted Observation/Evidence | Peer trace alone cannot certify business success |
| `tool-common` | Human alias / subjectRef mapping where relevant | Peer must not mint a parallel alias directory |

**State split:** the Mock AMF peer keeps only its own test-side AMF UE/session association and event queue. A real SMF's Session Context is always remote. In the existing deterministic `env-5gc-sim serve` process, all authoritative *simulated* domain facts remain in the one WorldStore; the new test peer is a **separate executable with no WorldStore/C2/C6 authority**. This is an independent test-peer role, not a new multi-world server profile.

## 4. Deployment and package boundary

Proposed implementation layout (not yet present):

```text
cmd/mock-amf/                  # independent process composition
internal/mockamf/
  sbi/                         # h2 server, h2 client, transport errors
  protocol/                    # contract-backed Nsmf / Namf adapters
  correlation/                 # SUPI / PSI / smContextRef transaction map
  scenario/                    # deterministic event scripts and clocks
  ledger/                      # peer events; no Runtime/Evidence authority
  fixtures/                    # protocol reference vectors/oracles, never universal payloads
  n2transfer/                  # test-only ASN.1 N2 request validation / response encoding
tests/mock-amf/                # component / process / live E2E checks
docs/design/mock-amf-sbi-peer.md
```

Executable name `mock-amf` is provisional; it must not reuse `env-5gc-sim serve` startup or management listeners. No public Go `pkg/` or SDK **in this repository** is required. The peer's separate HTTP/2 server/client needs a real external process boundary. `ca-client-tools/internal/sbi` and `internal/sbi/payload` are **not importable across repositories**, so the peer may use standard Go HTTP/2 and MIME primitives locally, validating against the same pinned SBI contract; it must not copy the production Provider's private Catalog or Artifact Store protocol. Cross-repo reuse of the small NAS codec requires an intentionally exported, tested protocol-only API from `ca-client-tools`.

Configuration responsibilities:

- Peer: bind address, local test identity, allowed peer origins, AMF callback apiRoot, Nsmf target apiRoot, scenario fixture, request limits and run epoch.
- Runner/Lab: start/stop the process, allocate ports, supply credentials, configure target and reset isolation.
- Target/NF: own its real service configuration and secrets; never write them into fixtures.
- Transport: local **h2c prior-knowledge** for the OpenAMSM test profile; optional TLS/HTTP2 only after a separately verified interoperability profile. HTTP/1.1 fallback is not implicit.

Keep management/ready endpoints in the test peer separate from SBI paths. A local operator interface for scenario loading and event inspection is allowed only as a test-control surface; do not expose it as an Agent Tool.

## 5. SBI interfaces and contract sources

The 3GPP/OpenAMSM **wire contract is authoritative**. This design lists logical operations and observed path families, not a competing OpenAPI. Exact body, enum, headers, ProblemDetails, response codes and binary content types must be resolved from the target OpenAMSM-compatible TS 29.502 / 29.518 OpenAPI and real fixture captures **before implementation**.

| Direction | Service and operation | Observed / expected path family | First slice |
| --- | --- | --- | --- |
| Mock AMF -> target | Nsmf_PDUSession CreateSMContext | `POST /nsmf-pdusession/v1/sm-contexts` | Required |
| Mock AMF -> target | Nsmf_PDUSession UpdateSMContext | `POST /nsmf-pdusession/v1/sm-contexts/{smContextRef}/modify` | Required |
| Mock AMF -> target | Nsmf_PDUSession ReleaseSMContext | `POST /nsmf-pdusession/v1/sm-contexts/{smContextRef}/release` | Required |
| target/SMF -> Mock AMF | Namf_Communication N1N2MessageTransfer | `/namf-comm/v1/ue-contexts/{ueContextId}/n1-n2-messages` | Required |
| Mock AMF -> SMF callback | N1N2 transfer failure notification | Callback URI from actual request/config; no hard-coded invented route | Required for failure scenario |
| Mock AMF -> target | Retrieve/other SM Context operations | Target OpenAPI dependent | Deferred |
| Other | UE registration, N1 NAS and NGAP emulation | Full AMF/RAN protocol stack | Out of scope |

Nsmf request/response must preserve 3GPP content shape. Where N1/N2 is binary, retain the original bytes and `multipart/related` `Content-Id` references. Do **not** replace binary SBI bodies with a proprietary JSON Base64 envelope. Preserve original wire request ID and HTTP status and do not normalize an error into success.

The Namf service's actual configured apiRoot is supplied explicitly. NW-Agent's existing `namf-comm` relay may be pointed at it; this peer **does not require** source-code modifications to the real OpenAMSM AMF or SMF.

### 5.1 Protocol generation ownership: NAS in Client Tools, N2 Transfer in Mock AMF

A **golden binary is a regression vector, not the universal test request**. Tests freeze semantic inputs, the supported protocol revision, codec revision, expected normalized semantics and reference vectors; they generate the actual bytes from the current scenario/transaction.

| Content | Production path | Mock AMF test path | Owner |
| --- | --- | --- | --- |
| N1 5GSM NAS | Host retains the **exact original N1 bytes** from the inbound SBI multipart, uses a typed decoder when needed, and passes original bytes to the authoritative OpenAMSM handling boundary | Generate the N1 5GSM request from constrained scenario data (PSI, PTI, PDU Session Type, SSC Mode, supported optional IEs such as ePCO), encode afresh and verify decode round-trip | Reusable 5GSM codec in `ca-client-tools`; Host owns original-byte artifact lifecycle |
| N2 NGAP SM Transfer | Host/Client Tools validate SBI multipart references and forward N2 bytes **opaqely**; real OpenAMSM AMF/SMF parses and handles the network-side semantics | For successful establishment, build the narrow **PDU Session Resource Setup Response Transfer** with current RAN address, GTP-TEID and applicable QoS Flow IDs; encode APER with a verified fixture/template builder | `env-5gc-sim` Mock AMF test peer, not production `ca-client-tools` |
| SBI HTTP/2 JSON + binary/multipart | Current `ca-client-tools` trusted outbound transport/Payload Engine and Host artifact channel | Independent h2c server/client and standard multipart assembly from the same pinned 3GPP wire shape; cannot import `ca-client-tools/internal/*` | Production Provider owns its own implementation; Mock AMF owns test peer transport, not a second wire contract |

**N1 scope:** The first-slice codec is for **5GSM session management**, not a complete 5GMM NAS registration/security stack. `supi`, `dnn` and `sNssai` in the Nsmf Create JSON are not automatically re-encoded as mandatory fields of the 5GSM PDU Session Establishment Request. Follow the exact TS 24.501 IE conditions and the pinned OpenAMSM 5GSM handler. Invalid or unsupported optional IEs must fail closed. For reproducibility a test may fix input parameters, PTI and any deterministic seed, without hardcoding a universal N1 byte array.

**Existing dependency:** [ca-client-tools#18](https://github.com/odango-chan/ca-client-tools/issues/18) already tracks scoped N1 5GSM **decode**, preservation of the original N1 artifact and private Owner ingestion. Deterministic **encode** for simulator-created requests is a proposed extension to that protocol scope, not a claim that a codec or callable has shipped. Mock AMF cannot import `ca-client-tools/internal/*`; the implementation decision is to use a narrowly exported protocol-only **Go package** from `ca-client-tools`, proposed import path `github.com/odango-chan/ca-client-tools/protocol/nas5gsm`. It must be independently importable and must not depend on Provider, Catalog, Runtime, Host, network endpoints, credentials, or Artifact Store. The repository currently has no such public package; its creation and compatibility tests are `ca-client-tools#18` work. If API publication is blocked, stop the dynamic-NAS E2E gate rather than copy a second decoder. Encoding is **not** automatically an Agent-callable Tool or a Production mutation capability.

**N2 scope:** Do **not** introduce a complete NGAP codec or NGAP/SCTP stack into `ca-client-tools` for this use case. The production Host needs Content-ID/media/length/digest validation, **not** deep N2 parsing to perform the AMF–SMF SBI handoff. For the positive simulator test, a single frozen APER binary is valid only when every relevant RAN address, TEID, QFI and transfer IE is identical. The test peer needs a **narrow reader** for the incoming `PDUSessionResourceSetupRequestTransfer` (at least enough to validate supported QoS Flow IDs) plus a **narrow encoder** for `PDUSessionResourceSetupResponseTransfer`; neither requires a full NGAP message stack. Multi-UE, multi-session or changed transport addresses require binding those values into an ASN.1 structure and re-encoding; never patch arbitrary APER byte offsets or claim dynamic coverage from one hardcoded sample.

OpenAMSM includes reference builders at `upstream/openamsm/tests/common/ngap-build.c::testngap_build_pdu_session_resource_setup_response_trasfer` and the consuming parser at `src/smf/ngap-handler.c::ngap_handle_pdu_session_resource_setup_response_transfer`. Use the pinned source/fixtures as differential acceptance oracles. It is acceptable to implement only this **N2 Transfer** IE and not any complete outer NGAP message; the SBI payload has an N2 SM Transfer, not an NGAP/SCTP network connection.

**Future decision:** Add production NGAP decode to `ca-client-tools` only if a concrete Host routing/admission decision needs an N2 IE, and only with an explicit 3GPP contract, owned API and tests. No such production requirement is established for the P0 Mock AMF scenario.

### 5.2 Contract-accurate Create and valid N2 response

The real OpenAMSM `src/amf/nsmf-build.c::amf_nsmf_pdusession_build_create_sm_context` populates `supi`, `pduSessionId`, `dnn`, `sNssai`, `servingNfId`, `guami`, `servingNetwork`, `anType`, `ratType`, NR `ueLocation`, `smContextStatusUri` and `n1SmMsg` with the original binary N1 `5gnas-sm` multipart reference, subject to conditions. **These are fields seen in the actual builder, not a claim that all are unconditionally mandatory under every 3GPP version.** A minimal JSON that passes a lenient facade is not enough; a real OpenAMSM SMF must accept the same validated multipart fixture.

OpenAMSM's `src/smf/mas/ssm/ssm_ran.c` keeps `SIGNAL_UE_AN` pending until it sees an actual **RAN F-TEID**. Namf N1N2MessageTransfer HTTP 200/201 by itself does **not** prove setup completion. P0 must supply valid binary **NGAP PDU Session Resource Setup Response Transfer** via multipart UpdateSMContext with `n2SmInfoType=PDU_RES_SETUP_RSP`, matching `n2SmInfo` Content-Id, an explicit RAN transport address and nonzero GTP-TEID. Use a narrow NGAP N2 Transfer ASN.1 APER encoder/template builder, with frozen golden binaries only as compatibility oracles (or for a strictly identical single-session fixture). Evidence must show the real SMF consumed it and advanced its SSM/MAS step; traffic/UP reachability remains `NOT_RUN` without an actual user-plane probe.

**Two distinct Locations:** Nsmf Create `Location` is the SM Context resource URI. A Namf N1N2 transfer's own response may yield a separate N1N2 resource URI used as `n1n2MsgDataUri` for failure-notification correlation. These are never interchangeable. A Namf 202/paging condition is not the same success path as a CM-CONNECTED 200/201 response.

**Two distinct callbacks:** the AMF includes `smContextStatusUri` in Create and must expose the corresponding **SM Context status notification** receiver if the SMF issues one. A failed N1N2 transfer is notified **outbound from Mock AMF** to the NF consumer's `n1n2FailureTxfNotifURI`, if provided in the original Namf request and applicable to the scenario. Preserve their individual callback shapes, conditions and status codes. OpenAMSM SSM may ACK a FailureNotification while keeping the frame pending; successful callback delivery does not prove a session release.

## 6. Session correlation and local state

### 6.1 Identities

The peer uses **per-run, per-session** correlation. Minimum key:

```text
runEpoch
  + SUPI (target wire representation)
  + pduSessionId
  + smContextRef (after Create Location is bound)
  + original request / callback correlation reference where available
```

- Before Create returns Location, maintain a provisional correlation for `(runEpoch, SUPI, pduSessionId, createRequestId)`. Do not use the "latest UE" or "last session" heuristic.
- Bind `smContextRef` from the actual Create response Location/contract, never fabricate a successful SMF ref.
- For repeated SUPI+PSI procedures, retain transaction-instance identity so a prior run's callback cannot satisfy the next run.
- Multiple PDU Sessions per UE and concurrent UEs are permitted. A missing/ambiguous key is a recorded rejected event, not an implicit first match.
- The real OpenAMSM SBI commonly carries `imsi-...` SUPI whereas the existing `env-5gc-sim` C2 owner state uses unprefixed SUPI anchors. No shared heuristic conversion: scenario fixture must declare the target wire identity explicitly; any future bridge is a separately tested boundary mapping and never a rewrite of owner contract.

### 6.2 Local state model

The peer models local protocol progress only:

```text
PRESEEDED_ACCESS
  -> CREATE_SENT
  -> SM_CONTEXT_BOUND
  -> N1N2_RECEIVED
  -> UPDATE_SENT
  -> UPDATE_ACKNOWLEDGED
  -> RELEASE_SENT -> RELEASE_ACKNOWLEDGED
       \-> ERROR / ABORTED
```

`PRESEEDED_ACCESS` means a trusted fixture says the UE is registered and in the required CM/access condition. It is **not** an additional Skill business precondition checked after a Create request has already arrived from AMF. Registration and NAS security are not simulated in P0.

A Namf request may arrive before the Create response is processed, because the current NW-Agent can return 201/Location and continue SIGNAL asynchronously. The peer must support a **bounded** unmatched-callback buffer, attach it only on exact correlation, and reject on expiry or ambiguity. It must not block an HTTP/2 stream indefinitely waiting for the downstream update.

### 6.3 Event isolation and reset

Each scenario run has an opaque `runEpoch`, but **this is local metadata and does not appear on ordinary SBI messages**. Reset must clear associations, rotate/drain the externally reachable listener or callback apiRoot/port as appropriate, and reject any callback without an exact unambiguous on-wire transaction match. Two indistinguishable old/new wire requests cannot be separated by an internal epoch check alone: reject/quarantine instead of silently consuming the wrong one. Keep bounded tombstones and do not recycle an old `smContextRef` into a new run while prior traffic can still arrive.

- One HTTP/2 connection may carry concurrent streams. The connection or stream ID alone is not the 5GC session key.
- Event/association queues have finite capacity and deterministic ordering.
- Duplicates remain visible as separate received events. Deduplication is allowed only on a contract-backed semantic request identity; never on timestamp proximity or similar body content.
- Cancel/timeout **and successful consumption** both establish completed-event fencing; a replay from an earlier wait/callback cannot satisfy the next scenario step.
- No autonomous silent retries after an ambiguous update or loss of response. Reconcile from real SMF state or let the runner decide a safe action.

## 7. Scenario and timing model

The first slice uses explicit scenario actions and deterministic triggers. Application-level behavior options include accepting N1N2, deliberately rejecting it, returning an error, withholding a response, invoking the standard failure callback and generating a subsequent UpdateSMContext with contract-correct N2 information.

Network packet loss/delay/reorder is **not** implemented by pretending the peer owns Fabric. Where byte-accurate transport faults are required, run through the owner Network Fault/Fabric path and retain its receipts. A peer-side "defer application response" is labelled **application behavior**, not a Fabric drop.

The runner controls scenario advancement through explicit events, virtual/declarative ticks or an injected deterministic clock; wall-clock sleeps cannot be used as the authority for test order. HTTP transport timeouts remain bounded implementation mechanics, distinct from domain event deadlines.

### 7.1 Illustrative scenario fixture (not a frozen schema)

```yaml
scenario: pdu-establish-success
transport: h2c
target: nsmf-pdusession
routing: openamsm_agent_step_override  # alternative: location_follow
ue:
  supi: "imsi-999700000000001"  # explicit OpenAMSM wire form
  pduSessionId: 1
  dnn: internet
  sNssai:
    sst: 1
    sd: "000001"
nas5gsm:
  message: PduSessionEstablishmentRequest
  pti: 1
  pduSessionType: IPV4
  sscMode: 1
  epco: []                     # optional IEs for this test
ngapN2:
  setupResponseTransfer:
    ranAddress: 10.10.0.8     # illustrative only; runner binds a reachable test N3 address
    ranTeid: 1001
    qosFlowIds: [1]            # bind to the actual N2 setup request
access:
  registration: preseeded
  cm: connected
steps:
  - send: CreateSMContext
  - expect: N1N2MessageTransfer
  - respond: accept
  - send: UpdateSMContext  # N2 binary PDU_RES_SETUP_RSP + run-bound RAN F-TEID
  - assert: real-smf-session-established
```

This YAML is explanatory, **not** a released public scenario machine contract. An implementation must define and version its own test-control schema. `nas5gsm` inputs are encoded into N1 by a pinned 5GSM codec; `ngapN2` values are encoded into a narrow N2 Transfer by the Mock AMF test peer. The actual protocol body/IE constraints must be checked against the pinned OpenAMSM and 3GPP contracts. An OpenAMSM reference binary remains a regression vector, not the only permissible runtime bytes. `assert` is evaluated by the owning runner using real SMF/MAS reads, not by trusting the Mock AMF's local state.

## 8. Required end-to-end interactions

### 8.1 Establish success

1. Runner provisions real OpenAMSM SMF/MAS/UPF and required NFs, plus Mock AMF on a run-isolated callback endpoint, then selects exactly one target and an explicit Nsmf routing profile.
2. Trusted setup supplies a registered/CM-CONNECTED AMF-side UE fixture plus the real backend subscription. Mock AMF **dynamically encodes N1 5GSM** from the scenario, checks the decoded semantics, and sends OpenAMSM-validated multipart CreateSMContext containing the generated bytes; not a static global NAS sample or empty JSON envelope.
3. Record the Create status and **full Location**; bind the SM Context reference and resolve the effective Update/Release destination according to the selected routing profile.
4. Target/real SMF sends standard Namf N1N2MessageTransfer to the configured Mock AMF apiRoot.
5. Peer validates N1/N2 multipart and correlation, sends a valid Namf response, builds a **session-bound NGAP N2 Setup Response Transfer** using the scenario's RAN address/TEID and negotiated flow(s), then sends multipart UpdateSMContext with `n2SmInfoType=PDU_RES_SETUP_RSP` and matching Content-ID to the selected effective destination.
6. Verify that real SMF parses the N2 information, binds the RAN F-TEID and resumes the waiting SSM/MAS operation. Namf 2xx alone is not proof.
7. Independent real SMF QueryContext and NF/N4 reads confirm the terminal session state. `AVAILABLE` alone is not establishment proof; without an actual data-plane probe, UE traffic reachability is **NOT_RUN**.

Expected evidence includes Create/Location, effective Update destination, Namf request/response, byte-exact N2 response and parsed RAN F-TEID, Update response, MAS operation trace, real session read, and exact request/callback correlation references.

### 8.2 Release and modify

**Routing gate:** Release and business Modify must use the scenario's selected effective destination. With ordinary `location_follow`, an SMF `Location` may bypass NW-Agent; in `agent_step` mode the real SMF deliberately rejects some direct business Update/Release. With `openamsm_agent_step_override`, the correct parity path is to rewrite apiRoot to NW-Agent, as the actual OpenAMSM AMF does. Record either outcome explicitly and do not count a direct-to-SMF completion Update as successful Agent business orchestration.

Release must call the actual Nsmf Release operation and independently verify authoritative SMF cleanup (including the expected lifecycle and absence/retention semantics). Modify must be driven by a specific contract-correct update condition; a generic empty Update is insufficient to certify a modify path. Neither path may be marked PASS solely because the Mock AMF replied with HTTP 2xx.

**Modify-response capability (2026-11-21, D5).** The peer accepts an SMF-initiated
`PDU_RES_MOD_REQ` N1N2 transfer on an already `UPDATE_ACKNOWLEDGED` session and
replaces the consumed establishment transfer with a new modify transaction. The
scenario steps are `await-n2-modify` (consume the exact `PDU_RES_MOD_REQ`) and
`update-modify-response` (send multipart `UpdateSMContext` with
`n2SmInfoType=PDU_RES_MOD_RSP` and a valid `PDUSessionResourceModifyResponseTransfer`
carrying the scenario RAN address and `N3Teid+1`). The modify request decoder
projects the UL/DL NGU-UP TNL modify list; the response codec is covered by
`internal/mockamf/n2transfer/modify_test.go` and the Namf parser by
`internal/mockamf/modify_test.go`. This is a test-peer capability only. It does
not make the pinned OpenAMSM SMF emit a modify request; with an SMF that never
emits `PDU_RES_MOD_REQ`, the `await-n2-modify` step fails closed by timeout and
must not be reported as a modify PASS.

### 8.3 Negative and concurrency scenarios

| Case ID | Scenario | Required assertion |
| --- | --- | --- |
| AMF-01 | Establish success | Valid N1/N2 binary and RAN F-TEID; exact Create/Namf/Update sequence; real SMF terminal state |
| AMF-02 | Release success | Correct Release and independent cleanup state |
| AMF-03 | N1N2 reject / FailureNotify | Correct callback semantics; target/SMF failure handling; no false success |
| AMF-04 | Application-level delayed reply | Bounded wait/cancel and eventual event handling, no invented network fault receipt |
| AMF-05 | Duplicate N1N2 or Update | Duplicate recorded; no cross-step consumption or silent extra side effect |
| AMF-06 | Two UEs / two sessions | No SUPI/PSI/SM Context mix-up under concurrent HTTP/2 streams |
| AMF-07 | Same UE sequential transactions | Old callback cannot satisfy a new transaction; indistinguishable wire traffic rejected |
| AMF-08 | Reset during outstanding callback | Rotated external callback endpoint and exact wire fence isolate old traffic; new run unchanged |
| AMF-09 | Invalid identity/ref/multipart | Fail closed with protocol-correct error, no dispatch to unrelated session |
| AMF-10 | NW-Agent vs CA Agent parity | Same fixture and real SMF; semantic comparison plus explicit differing effects |
| AMF-11 | Transport response lost after side effect | Outcome ambiguity retained; no blind retry; real SMF reconciliation |
| AMF-12 | Modify with specific update | Correct Update contract and real modified state |

**P0:** AMF-01, 02 (lab routing override), 03, 05, 06, 07, 08, 09, 13, 14, 15, with semantic-input NAS encode/decode round-trip and narrow NGAP N2 request validation + response encode plus real SMF decode verification. AMF-10 is blocked until CA Agent Host has verified HTTP/2 SBI ingress.
**P1:** AMF-04, 11, 12 and expanded failure variants; AMF-10 end-to-end parity after CA Agent readiness.

These are **proposed case IDs** local to this design, not additions to the old S0–S7 canonical matrix and not evidence that any case has run.

### 8.4 Additional mandatory review scenarios

| Case ID | Scenario | Required assertion |
| --- | --- | --- |
| AMF-13 | Nsmf `Location` follow versus OpenAMSM Scheme C override | Both logical resource URI and effective network destination recorded; mismatched profile fails explicitly |
| AMF-14 | SM Context status callback | Real callback to the AMF-provided `smContextStatusUri` is received and correlated; no fabricated notification |
| AMF-15 | N1 optional-IE plan-selection parity | Compare Nsmf façade with/without ePCO against the separate NW-Agent Plan route; record observed plan selection and do not mark unsupported N1 semantic parity PASS |

AMF-13, AMF-14, AMF-15 (explicitly allowed to expose a known NW-Agent limitation), and binary N2 setup-response encode/decode are **P0** acceptance gates, along with the existing P0 cases. All case IDs remain **proposed / NOT_RUN**.

## 9. Test harness, evidence and comparison

Each run must retain:

- Exact source identity (repo/commit/tag), **routing profile**, scenario and N2 binary fixture digests, configured target, OpenAMSM build identity, runtime start/end, peer run epoch and actual callback endpoint identity.
- HTTP/2 method, path, status, stream-local transport identity, **Create Location / logicalSmContextUri / effectiveRequestUri**, relevant content-type/Content-Id, N2 binary/RAN F-TEID, sanitized fixture digest and trace timestamps/order.
- Exact `SUPI`, `pduSessionId`, `smContextRef`, request/callback correlation, per-event disposition and peer-ledger sequence.
- The target's MAS invocation/evidence trace where available, plus real SMF/MAS state queries with their authoritative status/keys.
- Explicit account of application-script behavior versus Fabric-owner network fault receipts if a Fabric lane was used.
- An independent assertion report showing PASS/FAIL/BLOCKED for each criterion and missing evidence, not a success bit emitted by Mock AMF.

The runner compares **semantic** results rather than demanding byte-identical internal workflows. **A working Mock AMF and a successful NW-Agent smoke do not prove full preservation of original N1 semantics.** The actual NW-Agent Nsmf façade (`server.py::_handle_nsmf_facade`) parses multipart N1 and uses `enrich_create_msg_from_n1` for PDU Session Type, but currently selects `ESTABLISH_POLICY_FIRST` if that plan exists (falling back to `ESTABLISH`), **without using the ePCO policy-first scan for this façade path**. Its separate Plan/intent matching path (`match_plan`) does inspect the ePCO hint when `honor_n1` is enabled. These paths must not be conflated. OpenAMSM MAS `/invoke` maps JSON scalar inputs into its input map; additional IEs and original bytes are not generally transferred across that Owner boundary. Record N1 semantic coverage and original-binary propagation explicitly, and mark full-interface parity **BLOCKED** until an authoritative Owner/Host handoff is implemented and verified. NW-Agent currently uses `oes-dsl/1.3` with a step cursor; CA Agent uses CA-SL Procedure/Runtime. **Run baseline and candidate separately against the same pinned OpenAMSM build, with full cleanup and reseed between runs**, not as simultaneous controllers of one session. Report routing-profile and outbound effects separately; external SBI and authoritative SMF outcomes must be independently observed.

Comparison must distinguish: transport accepted; Nsmf request accepted; MAS Operation committed; terminal SMF state observed; Runtime Outcome/Evidence (if applicable); and actual user-plane connectivity. These are not interchangeable.

## 10. Boundaries, security and failure policy

- Bind on loopback by default. External bind requires explicit operator configuration and authenticated transport or isolated lab network.
- No production subscriber data or credentials in fixtures or logs. Redact headers/tokens, sensitive body sections and any subscriber identifiers in published evidence.
- No privileged introspection of SMF private State, no writing to real SMF memory, no bypassing OpenAMSM's query/invoke access control.
- Reject unexpected origin, unknown operation/path, oversized multipart, inconsistent Content-Id, unsupported method, ambiguous correlation and unallowlisted callback destination; permit only explicit lab NF callback hosts to prevent callback-driven SSRF.
- Network disconnect/timeout never implies backend `NOT_COMMITTED` and never authorizes automatic retry.
- Bounded queues and clean process shutdown are mandatory. Any outstanding run is reported incomplete on abrupt restart; no imaginary durable recovery.
- Do not introduce new test-only source patches into real OpenAMSM for this peer. Existing documented `agent_step` configuration and its AMF-side URI rewrite are permitted in the isolated lab, but must be recorded in run evidence.

## 11. Implementation sequence and gates

| Stage | Deliverable | Gate |
| --- | --- | --- |
| D0 | Freeze design/inputs and pin OpenAMSM source, TS 24.501/29.502/29.518/38.413 relevant contracts and reference vectors, Nsmf routing and callbacks | A written exact release/commit + source/fixture digest; no codec invention from memory |
| D1 | Independent h2c peer, scenario runner seam, correlation, reset/listener fencing | Real h2c client/server test, known/unknown operations, duplicate/late/cross-UE, bounded multipart; no codec dependency for skeleton |
| D2 | Import Client Tools protocol-only 5GSM codec; dynamically build Create N1, N2 request validation / response Transfer; Nsmf/Namf callbacks | `ca-client-tools#18` exported API gate + isolated round-trips, NGAP reference/differential checks, AMF-01/02/03/05/06/07/08/09/13/14 plus AMF-15 documented baseline behavior component/process PASS |
| D3 | Live OpenAMSM against NW-Agent Scheme C | `openamsm_agent_step_override`, exact target source and N2 F-TEID, real SMF/MAS readback; label smoke versus full N1 semantic parity separately |
| D4 | Live OpenAMSM against CA Agent Host | `ca-agent-demo#220` true h2c Nsmf ingress/Location + `ca-client-tools#18` original-N1/Owner binding, typed operations and Runtime readiness; same fixtures, AMF-10; missing items = BLOCKED |
| D5 | Extended scenarios, optional Fabric-mediated fault, recovery diagnostics | AMF-04/11/12 and explicit owner Network Observation where applicable |

Do not merge D1/D2 into the old `serve` process or change canonical C2/C6 schemas to satisfy D3/D4. D1 is independently executable now; D2 dynamic-NAS acceptance depends on the cross-repo exported codec; D3 live smoke needs a working OpenAMSM lab; D4 full parity also needs the Host SBI/Owner original-N1 path and cannot be self-certified inside this repository. Implement new peer-only machine contracts after D0 approval; publish/version the scenario control schema only when a concrete consumer requires it.

### 11.1 Review questions before D1

**P0 additions from formal review:** Pin OpenAMSM `src/amf/sbi-path.c` `agent_step` URI rewrite and both routing profiles; pin `src/amf/nsmf-build.c` full Create multipart and `smContextStatusUri`; validate dynamically generated NAS against pinned OpenAMSM reference vectors, and a narrow NGAP N2 PDU Session Resource Setup Response Transfer builder against the actual OpenAMSM parser; distinguish Namf N1N2 transfer Location from Nsmf Create Location. These are required before claiming a real Establish PASS. Confirm CA Agent Host's HTTP/2 SBI ingress and its Location/Modify/Release semantics independently; unverified readiness is `BLOCKED`.

1. Which pinned TS 29.502 / TS 29.518 OpenAPI version and OpenAMSM build/fixture set is used for the first run? (Must verify the target; no protocol version chosen by prose alone.)
2. What exact callback URI and N1/N2 success/failure payload combinations does the OpenAMSM build emit? Verify by recording the existing real AMF interchange; do not infer only from a façade spec.
3. Does CA Agent Host expose the 3GPP SBI Nsmf endpoint in HTTP/2 now? If not, mark D4 `BLOCKED` until it does. An HTTP/1-to-2 compatibility proxy does not meet parity.
4. Who owns the actual runner and Lab composition for D3/D4? Mock AMF must remain runnable without either target.
5. Does `env-fabric` support the desired SBI test topology? If not, keep first-slice application-level failure cases distinct and defer transport fault qualification.

## 12. Decision record (Proposed)

**Choose:** One repository, separate SBI test-peer process; dynamically encode scenario-driven NAS 5GSM using the scoped Client Tools codec, retain fixed vectors as regression oracles, and build only the N2 Transfer needed for testing inside Mock AMF. The production Host/Client Tools route N2 opaquely. Keep contract-backed 3GPP Nsmf/Namf messages, explicit routing profiles, run isolation and authoritative real SMF readback.

**Reject:**

- Adding Mock AMF inside OpenAMSM's NW-Agent (consumer coupling).
- Having Mock AMF directly mutate real SMF state or fabricate QueryContext results (false E2E).
- Adding an alternative WorldStore or C2/C6 source-fact API for the real-peer mode (duplicate authority).
- Treating a Namf forwarding relay as a functional Mock AMF (no UE/access response behavior).
- Implementing fault receipts inside the peer or claiming network drop from an application timeout.
- Falling back to HTTP/1.1 or test-only custom JSON in lieu of real SBI.
- Treating Namf HTTP 2xx as proof of the RAN F-TEID or successful SMF session establishment.
- Treating a local `runEpoch` as a wire-visible epoch, or silently rewiring Nsmf `Location` without an explicit test profile.

## 13. Executable handoff and second-pass review

### 13.1 Readiness verdict (2026-11-19)

**DESIGN_READY / PHASED_IMPLEMENTATION_READY; FULL_E2E_BLOCKED.** This is a source-backed plan, not a code completion or live acceptance claim.

| Work item | Owning repo/locator | Known fact | Gate |
| --- | --- | --- | --- |
| D1 process and scenario core | `env-5gc-sim` #66 and this design | Proposed, no executable yet | Can implement and test now, separately from existing `serve` |
| N1 deterministic 5GSM codec | `ca-client-tools` #18 | No existing production NAS codec; current Provider/Host N1 path preserves artifact bytes but does not expose a codec | Implement limited Decode+Encode, publish small cross-repo Go API and prove independent import |
| N2 request inspection / response Transfer | `env-5gc-sim` #66 | OpenAMSM has test builder and SMF decoder; only a narrow N2 Transfer is needed | Validate QFI against incoming N2; bind RAN N3 IP/TEID from runner and encode APER |
| Real NW-Agent Scheme C smoke | `env-openamsm`, pinned source; `tools/nw-agent` | N1 multipart accepted and selected attributes parsed; MAS `/invoke` currently scalar input map | Can test operation flow, but must not label full N1 parity PASS |
| Host native Nsmf ingress | `ca-agent-demo` #220 | Current implementation uses Fabric input and lacks native Nsmf Create server as of issue baseline | Native h2c Create + post-201 continuation + Location routing acceptance |
| Owner original-N1 semantic closure | `ca-client-tools` #18 plus OpenAMSM owner/Host integration | Exact N1 artifact/Owner binding unimplemented; MAS `/invoke` maps scalar JSON inputs | Real Owner consumes original N1 **or** explicit, source-proven full semantic equivalence for the supported scope |
| CA Agent full MAS E2E | `ca-agent-demo` #215 and #216; `ca-client-tools` #18 | Runtime/Temporal, typed Provider/Owner Receipt and formal Build gates tracked separately | No full E2E PASS until all relevant owner gates and real evidence exist |

The reference OpenAMSM source inspected for this design is `odango-chan/env-openamsm@594dec78b95bff4fdc34deac8a3a9681fb41228f`, particularly `upstream/openamsm/tools/nw-agent/server.py`, `orch_engine.py`, `src/smf/mas/common/mas-orchestration-sbi.c`, `src/amf/sbi-path.c`, `tests/common/ngap-build.c`, and `src/smf/ngap-handler.c`. Pin actual protocol OpenAPI release and 5GSM/NGAP fixtures in a D0 manifest before coding. This source commit is a reference observation, **not** a declaration that the OpenAMSM runtime target has been deployed or accepted at that exact commit.

### 13.2 Concrete codec contract for ca-client-tools #18

The **proposed** public, protocol-only Go surface is `github.com/odango-chan/ca-client-tools/protocol/nas5gsm`. It is small enough to support a real cross-repo consumer without exporting `internal/*`.

```go
// Proposed API shape, not existing code or a finalized wire contract.
type EstablishmentRequest struct {
    PduSessionID   uint8
    PTI            uint8
    PduSessionType uint8
    SSCMode        uint8
    EPCO           []byte // validated supported optional IE, not arbitrary raw NAS
}
func EncodeEstablishmentRequest(EstablishmentRequest) ([]byte, error)
func DecodeEstablishmentRequest([]byte) (EstablishmentRequest, error)
```

The actual public semantic type/enums and optional IE bounds must follow pinned TS 24.501/OpenAMSM. Do not silently discard or normalize unsupported IEs. A mock-generated request may call Encode, but production ingress must keep the **original** N1 byte artifact; Decode does not authorize Re-Encode before forwarding to Owner.

Codec tests: two distinct PSIs/PTIs and PDU Session Types, supported SSC modes, with/without ePCO; multiple well-formed supported IE variants; malformed/truncated headers and length overflows; exact semantic Encode→Decode round-trip; differential vectors against the pinned OpenAMSM decoder. Prove an independent `env-5gc-sim` Go import works. The package must have **no** network, Host Artifact Store, Provider Catalog or Runtime dependencies. An importable Go helper is not an Agent-callable Tool.

### 13.3 N2 Transfer builder contract for the Mock AMF

The peer is not a generic NGAP RAN. It handles the **N2 SM Transfer payloads** exposed over Namf/Nsmf:

- Validate the supported incoming `PDUSessionResourceSetupRequestTransfer` with a strict, bounded decoder/inspection path. At minimum check the corresponding session and supported QFI set; reject unsupported transfer variants rather than inventing RAN outcomes.
- Given explicit runner-provided N3 transport-layer address and run-scoped nonzero GTP-TEID, encode an ASN.1 APER `PDUSessionResourceSetupResponseTransfer` with `dLQosFlowPerTNLInformation`, `gTPTunnel` and `associatedQosFlowList` consistent with the incoming request and selected scenario.
- Reject duplicate or conflicting N3 TEIDs for simultaneous sessions unless the scenario explicitly tests that failure. Make test values deterministic from the run seed but session-distinct.
- Feed encoded bytes as a named MIME part in Nsmf Update with `n2SmInfoType=PDU_RES_SETUP_RSP` and a matching `n2SmInfo.contentId`.
- Differential validation: compare decoded fields with OpenAMSM `tests/common/ngap-build.c::testngap_build_pdu_session_resource_setup_response_trasfer` and prove the OpenAMSM SMF `src/smf/ngap-handler.c::ngap_handle_pdu_session_resource_setup_response_transfer` accepts the payload. **Byte equality is not required** when encoding is semantically equivalent; fixed binary examples are regression oracles only.
- Do **not** publish N2 decoding/encoding in Client Tools, or implement outer NGAP/SCTP/NAS security, to satisfy this Mock AMF project.

### 13.4 Minimum executable first scenario

```yaml
# Illustrative. Freeze a versioned test-control schema before runtime use.
scenario: establish-two-ue
mode: openamsm_agent_step_override
target: http://127.0.0.1:8091  # selected NW-Agent / Agent Host
ue:
  - supi: "imsi-999700000000001"
    pduSessionId: 1
    nas: {pti: 1, pduSessionType: IPV4, sscMode: 1}
    ran: {n3Address: "10.10.0.8", n3Teid: 1001}
  - supi: "imsi-999700000000002"
    pduSessionId: 2
    nas: {pti: 2, pduSessionType: IPV4, sscMode: 1}
    ran: {n3Address: "10.10.0.8", n3Teid: 1002}
steps: [create, expect-namf, send-n2-setup-response, query-real-smf]
```

This demonstrates **semantic-input fixtures**. PDU Session Type and SSC Mode are NAS inputs, while SUPI, DNN/S-NSSAI, UE location, callback URI and NF identity live in the appropriate Nsmf Create JSON/context. The example omits those environment-bound fields intentionally; the D0 fixture manifest must supply them and the validated NAS content before an executable test can run. `10.10.0.8` is illustrative, **not** evidence of an actual assigned or reachable RAN N3 address.

### 13.5 Tasks in dependency order; safe stopping rules

1. **D0 — Contract inventory:** Record exact source SHA, supported OpenAPI/TS revision, binary fixtures, N1 required IE matrix, supported N2 request/response transfer, callback endpoints and effective Location routing. Add focused case names and a machine-readable scenario schema only in the owning mock-test scope. Do not make additional OpenAMSM source patches by assumption.
2. **D1 — Mock server skeleton:** Implement a separate h2c client/server, bounded multipart, exact per-session correlation, configurable routes, epoch/listener isolation, deterministic scenario actions, readiness and events. Test locally against a deliberately minimal protocol fixture. Do **not** call this E2E or fabricate an Owner response.
3. **D2a — ca-client-tools codec:** Implement and accept the narrow 5GSM Decode/Encode API and source-validated tests. Coordinate original-N1 Host Artifact Store and Owner binding separately; do not mix them into a public Go codec.
4. **D2b — Mock N2 builder:** Implement only supported N2 Transfer subset and dynamic NAS-backed Create, run per-case component/process tests and compare with OpenAMSM reference parser. If client codec remains unavailable, stop the dynamic-NAS gate and report `DEPENDENCY_BLOCKED`; do not embed a duplicate NAS decoder in the mock.
5. **D3 — NW-Agent real smoke:** Point an isolated real OpenAMSM NW-Agent/SMF to this mock callback endpoint, send Create with N1, respond with N2 Setup Response Transfer, then verify actual MAS and SMF states. The live NF proves **SBI_PROCEDURE_SMOKE** only if accepted; independently record which N1 semantics were actually consumed by the scalar-only Owner path.
6. **D4 — CA Agent parity:** Wait for native Host Nsmf ingress, 201/Location continuation, original-N1 Owner closure, typed Provider/Runtime dependencies. Run the exact same semantic scenario in a fresh isolated real backend, compare SBI and SMF states, and require actual evidence to claim `FULL_INTERFACE_PARITY_PASS`. A successful Mock AMF component test or NW-Agent smoke **cannot** substitute for this.

If dependency readiness is unknown: implement only the locally owned code and tests; open/update the correct owner Issue, mark `BLOCKED` with exact locator, and never invent a private wire DTO or move a production boundary into the simulator.

### 13.6 Evidence, quality gates and Definition of Done

`env-5gc-sim` owner-local: `go test ./...`, `go vet ./...`, targeted `go test -race ./internal/mockamf/...`, build `./cmd/mock-amf`, h2c and multipart negative cases, schema and doc link gates, `git diff --check`. Record actual results; do not claim PASS without execution. Existing `serve` PFCP/World tests must remain green.

`ca-client-tools` codec: isolated Go tests with NAS vectors and malformed cases, exact independent cross-repo import, `go test ./...`, `go vet ./...`, Windows/Linux native builds per its project rules. Existing production mutation gate and read-only binding rules remain unchanged.

Live evidence: full executable versions, source SHAs, scenario semantic-input manifest, generated N1/N2 digests, request/response Status and Locations, stream/Content-ID correlation, exact SMF context read and MAS step log, real RAN F-TEID, isolation and cleanup receipts. Publish no raw production subscriber identifiers or credentials.

A **design-only PR** may merge after review, but its status remains `Proposed / NOT_IMPLEMENTED / NOT_RUN`. An implementation PR cannot close #66 or claim full E2E until actual evidence for its explicitly claimed scope is committed. `SBI_PROCEDURE_SMOKE_PASS` and `FULL_INTERFACE_PARITY_PASS` are intentionally different.

## 14. References

- [OpenAMSM AMF Scheme C Nsmf route rewriting](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/src/amf/sbi-path.c)
- [OpenAMSM AMF Create/Update/Release and callback builder](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/src/amf/nsmf-build.c)
- [OpenAMSM MAS SSM N1/N2 RAN F-TEID handling](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/src/smf/mas/ssm/ssm_ran.c)
- [OpenAMSM direct Nsmf business Update/Release guard](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/src/smf/nsmf-handler.c)

- [env-5gc-sim architecture](../architecture/env-5gc-sim-architecture.md)
- [One Process One World](../decisions/ADR-0004-one-process-one-world.md)
- [HTTP/JSON owner API](../decisions/ADR-0005-http-json-owner-api.md)
- [Open5GS semantic alignment](open5gs-alignment.md)
- [Process and bindings](process-and-bindings.md)
- [Network Observation / Fabric boundary](network-observation-and-service-fabric.md)
- [OpenAMSM NW-Agent README](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/tools/nw-agent/README.md)
- [NW-Agent orchestration engine](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/tools/nw-agent/orch_engine.py)
- [Namf relay note](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/tools/nw-agent/openapi/Nnwagent_Relay.md)
- [Nsmf façade proposal implemented in NW-Agent](https://github.com/odango-chan/env-openamsm/blob/main/upstream/openamsm/tools/nw-agent/openapi/Nnwagent_NsmfFacade.yaml)
- [Real OpenAMSM acceptance evidence](https://github.com/odango-chan/env-openamsm/blob/main/docs/acceptance-20261117.md)

## 15. Implementation record (2026-11-19)

This section records actual implementation status against the v0.4 design. It
does not change the design contract above. Status authority remains
[`docs/WORK.md`](../WORK.md); evidence locators are in the acceptance artifact.

### 15.1 D0 baseline

- OpenAMSM environment source: `env-openamsm@594dec78b95bff4fdc34deac8a3a9681fb41228f`
  (snapshot commit `c27e1761ae09957a474cc2b0208d227cde64aabf`, Open5GS 2.8.0).
- NGAP reference: `lib/asn1c/support/ngap-r19.2.0/38413-j20.asn` and the
  generated APER codec under `lib/asn1c/ngap`.
- NAS reference: `lib/nas/5gs/{message.h,types.h,ies.c,encoder.c,decoder.c}`.
- N2 golden vectors were generated with the pinned OpenAMSM `asn1c` APER
  codec, not hand-authored byte offsets.
- Real lab used: WSL2 mirrored networking, real OpenAMSM NFs, NW-Agent
  `tools/nw-agent`, Mock AMF on Windows.

### 15.2 D1/D2 implemented scope

- `cmd/mock-amf` and `internal/mockamf`: independent process, h2c server/client,
  multipart/related builder/parser, per-`(SUPI, PSI)` correlation, bounded early
  callback buffer, duplicate recording, reset tombstones, event ledger, health
  and reset control endpoints.
- Explicit routing profiles: `location_follow` and
  `openamsm_agent_step_override`; both `logicalSmContextUri` and
  `effectiveRequestUri` are recorded.
- Scenario runner: `create`, `await-n1n2`, `update-setup-response`, `release`,
  `notify-failure`, `expect-no-n1n2`, the test-control barrier
  `await-control` (blocks until `POST /mock-amf/v1/continue`, so an external
  runner can read independent backend state at a deterministic point; §18.1),
  and `parallel` step groups for true concurrent sub-steps (§22).
- NAS: `github.com/odango-chan/ca-client-tools/protocol/nas5gsm` at merged
  `ca-client-tools@0001c61e9bf752acc4b59147a387e708f61dbe14`; scenario input is
  encoded dynamically and decoded back before use.
- N2: `internal/mockamf/n2transfer` encodes
  `PDUSessionResourceSetupResponseTransfer` and decodes the mandatory root IEs
  of `PDUSessionResourceSetupRequestTransfer`. Golden bytes match the pinned
  OpenAMSM APER encoder exactly for IPv4/IPv6, distinct TEIDs and one/two QFIs.

### 15.3 First-slice restrictions

- The incoming N2 setup request decoder accepts exactly one QoS Flow Setup
  Request item; multi-QFI setup requests fail closed as `UNSUPPORTED`. The
  response encoder supports 1..63 associated QoS flows.
- The N2 decoder reads the UPF N3 address/TEID, PDU session type and QFI; it does
  not decode the full QoS parameter tree. The mandatory
  `QosFlowLevelQosParameters` tree must be present for the single item but is not
  interpreted.
- Runner `runEpoch` is local metadata and is never placed on the 3GPP wire.
  Cross-run endpoint rotation is the runner's responsibility; the in-process
  reset fences locally known sessions and tombstones.
- A released `(SUPI, PSI)` key is retired. Its late callbacks are rejected
  (`404 STALE_SM_CONTEXT`) and a new `Create` for the same key is refused as
  ambiguous until an explicit reset. `POST /mock-amf/v1/reset` with
  `{"reuseKeys":true}` clears that fence and is only safe after the caller has
  rotated or drained the externally reachable listener, because two
  indistinguishable wire requests from different epochs cannot be told apart by
  local metadata. AMF-07 is qualified on that explicit contract (§16.2).
- The `n1n2MsgDataUri` returned in a 202 response is a holding/correlation URI:
  the pinned OpenAPI defines no retrieval operation for it, so the peer does not
  serve a GET for it. Its contract role is that the later
  `N1N2MsgTxfrFailureNotification.n1n2MsgDataUri` equals it, which is how the
  real SMF finds the paging session.
- No full 5GMM/NAS security, NGAP/SCTP, outer NGAP PDU, UPF/user-plane probe or
  second SMF/Runtime exists.

### 15.4 D3 result — BLOCKED; live Namf ingress is not yet attributed

There are two distinct real-lab observations and they must not be conflated:

1. The first D3 attempt recorded in
   `artifacts/acceptance/20261119-mock-amf-d1-d3/run-manifest.json`
   returned Create `201`, then the real SMF failed with
   `Unexpected PFCP type [55] in initial` before emitting Namf. This is the
   pre-PFCP-fix run and remains historical evidence.
2. The later 19:15 run after the OpenAMSM PFCP response fix logged
   `N1N2 xact without amf_nf_id`, followed by MAS compensation and PFCP
   deletion. The Mock AMF scenario result still contains only
   `nsmf.create.bound`; it has no `namf.n1n2.*` event. The exact HTTP response
   status and ProblemDetails body from the relay-to-peer hop were not retained.

**Source correction:** the statement that Mock AMF has no N1N2 route is not
supported by the current source. At implementation commit `9881a4e` (merged
as `83c06e8`), `Peer.Handler()` registers
`POST /namf-comm/v1/ue-contexts/{ueContextId}/n1-n2-messages`, the command
serves `peer.Handler()`, and `TestScenarioEstablishSuccess` exercises a
multipart Namf request through that route. Therefore, do not add a duplicate
route based only on a non-2xx response. The unresolved possibilities are a
wrong relay target/listener, a path mismatch, or request rejection before the
existing acceptance event.

The diagnostics change on the current D3 follow-up branch adds:
- `namf.n1n2.request_received`: matched route, content type, body size and
  SHA-256 (never raw NAS/N2 bytes);
- `namf.n1n2.rejected`: exact HTTP status, cause and validation detail;
- `sbi.unmatched_request`: redacted path for an unmatched route/404.

These are source-level diagnostics, not live E2E evidence. The next real run
must rebuild the peer from the diagnostic commit and retain the resolved
`OPENAMSM_AMF_BASE`, Mock AMF events, NW-Agent response status/body and SMF
window. Interpret the result explicitly:

- no request event: request did not reach this Mock AMF process/listener;
- unmatched event: relay path/method does not match the registered SBI route;
- request + rejected event: inspect the recorded ProblemDetails cause and
  contract/multipart/N2 validation;
- accepted event: proceed to prove Nsmf UpdateSMContext response and real
  SMF/MAS state advancement.

D3 was **BLOCKED** at that point; **SBI_PROCEDURE_SMOKE_PASS was not claimed**.
A Namf 2xx alone is not proof of a successful PDU Session establishment or RAN
F-TEID consumption. This historical result was superseded on 2026-11-20 by the
real establishment recorded in §17.

### 15.5 D4 result — BLOCKED

`ca-agent-demo#220` (native Nsmf ingress), `#215`/`#216` (same-Run continuation
and Runtime/Temporal gates) remain open, and `ca-client-tools#18` still lacks
the private original-N1 Owner binding. D4 is **BLOCKED**; no CA Agent parity or
`FULL_INTERFACE_PARITY_PASS` is claimed.

## 16. Conformance and reliability record (2026-11-20)

This section records the second implementation round against the pinned wire
contract. It supersedes nothing in §5–§9; it makes the implemented subset and
its acceptance evidence explicit. Status authority remains
[`docs/WORK.md`](../WORK.md).

### 16.1 Pinned contract source

The peer models exactly these pinned 3GPP artifacts from
`env-openamsm@594dec78b95bff4fdc34deac8a3a9681fb41228f`:

| Contract | Pinned locator | Used for |
| --- | --- | --- |
| TS 29.518 Namf_Communication | `upstream/openamsm/lib/sbi/support/r16-20230226-openapitools-6.4.0/modified/TS29518_Namf_Communication.yaml` | `N1N2MessageTransferReqData`, `N1N2MessageTransferRspData`, `N1N2MsgTxfrFailureNotification`, `N1N2MessageTransferError`, `N1N2MessageTransferCause`, `N2InfoContainer`/`N2SmInformation`/`N2InfoContent`, `N1MessageClass`, `NgapIeType` |
| TS 29.502 Nsmf_PDUSession | same release, `TS29502_Nsmf_PDUSession.yaml` | `SmContextStatusNotification`, `StatusInfo`, `ResourceStatus` |
| TS 29.571 Common Data | same release, `TS29571_CommonData.yaml` | `ProblemDetails`, `RefToBinaryData`, `PduSessionId`, `Uri` |
| TS 24.501 5GSM header | `upstream/openamsm/lib/nas/5gs/message.h` plus OpenAMSM SBI constants in `lib/sbi/message.h` | N1 structural check (`application/vnd.3gpp.5gnas`, EPD `0x2e`, PSI), Content-IDs `5gnas-sm`/`ngap-sm` |
| TS 38.413 NGAP SM Transfer | `lib/asn1c/support/ngap-r19.2.0/38413-j20.asn`, generated APER under `lib/asn1c/ngap` | narrow request decode and response encode |

The peer's own Go types are named after these schemas; there is no second wire
DTO authority in the repository (the peer is a test-only process, not a
published OpenAPI).

### 16.2 AMF acceptance matrix

Method types: **COMPONENT** = in-process h2c client/server against a fake SMF
that mirrors the real Open5GS handler rules; **PROCESS** = the real
`mock-amf.exe` binary spawned as a child process, driven over h2c; **LIVE** =
real OpenAMSM NF. Nothing in this table is LIVE.

| Case | Test method | Actual result | Key evidence | Status |
| --- | --- | --- | --- | --- |
| AMF-01 Establish success | PROCESS + COMPONENT: Create multipart (N1 5GSM + N2 `PDU_RES_SETUP_REQ`), Namf 200 `N1_N2_TRANSFER_INITIATED`, Update with N2 `PDU_RES_SETUP_RSP` | Create 201, Namf 200, Update 200, SMF-side N2 decode yields RAN `10.10.0.8`/TEID 1001/QFI 1, Release 204 | `cmd/mock-amf/process_test.go::TestProcessRunEstablishScenarioOverH2C`; `internal/mockamf/peer_test.go::TestScenarioEstablishSuccess` | COMPONENT+PROCESS PASS |
| AMF-02 Release success | COMPONENT + PROCESS + LIVE: Release on the bound SM Context | COMPONENT/PROCESS: Release 204 recorded on the peer and seen by the fake SMF. LIVE 2026-11-20 (§18): SCP-routed `POST …/sm-contexts/1/release` with a conformant body, `200`, the real SMF executed the RELEASE plan and deleted the PFCP session (54/55) and the UPF session, but the real SMF retained the SM Context (`pdu_state=active` for 60 s, `pfcp_sessions_active=1`) | `TestScenarioEstablishSuccess` (release step); `release_test.go`; `scp_test.go`; `cmd/mock-amf/process_test.go::TestProcessRunReleaseLifecycleWithControlBarrier`; `artifacts/acceptance/20261120-mock-amf-release-lifecycle/` | COMPONENT+PROCESS PASS; LIVE SBI PASS; **real-SMF cleanup state FAIL — owner `env-openamsm#10`** |
| AMF-03 N1N2 reject / failure notify | COMPONENT + PROCESS: `reject_sync` (200 `N1_MSG_NOT_TRANSFERRED`) and `reject_async` (202 + Location, then standard failure notification) | Sync: 200 with `N1_MSG_NOT_TRANSFERRED`, no Update. Async: 202 `ATTEMPTING_TO_REACH_UE` + Location; notification body is exactly `{cause,n1n2MsgDataUri}` and the fake SMF correlates the session by that URI (204) | `failure_test.go::TestSyncRejectionReturnsN1NotTransferred`, `::TestAsyncRejectionSendsStandardFailureNotification`; `cmd/mock-amf/process_test.go::TestProcessRunFailureNotificationScenario` | COMPONENT+PROCESS PASS |
| AMF-04 Application-level delayed reply | No delay action is implemented | — | — | NOT_RUN |
| AMF-05 Duplicate N1N2 | COMPONENT: second transfer for a consumed session | 409 `N1N2MessageTransferError` (`cause=SESSION_CONFLICT`); first transfer kept; duplicate counted | `negative_test.go::TestDuplicateN1N2IsConflictWithoutSecondConsumption` | COMPONENT+PROCESS PASS |
| AMF-06 Two UEs / concurrent sessions | PROCESS + COMPONENT: two UEs, two PSIs, both transfers delivered while both contexts are bound; optional `parallel` step group (§22) overlaps the Creates | Each session consumes only its own transfer (UPF TEID 2001 in both, distinct transactions and RAN TEIDs), no cross-delivery, both released; parallel sub-step results stay ordered by declaration | `peer_test.go::TestTwoUEParallelEstablishment`, `session_test.go::TestTwoSessionsDoNotCrossDeliver`, `parallel_test.go::TestParallelSubStepsActuallyOverlap` | COMPONENT+PROCESS PASS |
| AMF-07 Same UE sequential transactions | COMPONENT: release then late callback, retired key, explicit reuse reset | Released key rejects late callback with 404 `STALE_SM_CONTEXT`; a new Create for the retired key is refused as ambiguous; `reset {reuseKeys:true}` (listener-drained contract) admits the next transaction | `session_test.go::TestReleaseRetiresKeyWithoutGuessing`; `peer_test.go::TestResetRejectsStaleCallback` | COMPONENT+PROCESS PASS (wire ambiguity rejected, never guessed) |
| AMF-08 Reset + old callback isolation | COMPONENT: reset without/with key reuse; late status notification | Old-generation N1N2 and Status notifications get 404 `STALE_SM_CONTEXT`; generation advances; reuse reset admits a new key epoch | `peer_test.go::TestResetRejectsStaleCallback`; `status_test.go::TestSMContextStatusAfterResetIsStale`; `session_test.go::TestResetRotatesGenerationAndFencesSessions` | COMPONENT+PROCESS PASS (listener rotation remains runner-owned) |
| AMF-09 Invalid identity / reference / multipart | COMPONENT: 24 negative request cases plus oversized body and non-JSON multipart root | Fail closed with the recorded status/cause pairs (`400`/`413`/`415`); no session mutation | `namf_test.go::TestNamfRequestValidation`, `::TestNamfBodyLimit`, `::TestNamfMultipartRootMustBeJSONFirst`; `negative_test.go::TestNamfRejectsPartWithoutContentID` | COMPONENT+PROCESS PASS |
| AMF-10 NW-Agent vs CA Agent parity | Requires CA Agent Host SBI ingress | — | — | BLOCKED (`ca-agent-demo#220/#215/#216`) |
| AMF-11 Transport response lost after side effect | No loss-injection profile in the peer | — | — | NOT_RUN |
| AMF-12 Modify with specific update condition | Only the setup-response Update is implemented | — | — | NOT_RUN |
| AMF-13 Nsmf Location vs Scheme C override | COMPONENT: both routing profiles; explicit 403 failure | `location_follow` keeps the Create `Location`; `openamsm_agent_step_override` rewrites apiRoot and keeps the SM Context path; a documented 403 surfaces as an explicit failure | `peer_test.go::TestRoutingOverrideRetargetsHostKeepsPath`, `::TestDocumentedRoutingMismatchIsExplicit`; routing audit asserted in `TestScenarioEstablishSuccess` | COMPONENT+PROCESS PASS |
| AMF-14 SM Context status callback | COMPONENT: SMF posts a real `SmContextStatusNotification` to the peer-provided `smContextStatusUri` | `RELEASED` correlates to the exact transaction and retires the session; `UNCHANGED` keeps it usable; unknown/wrong-PSI/stale/duplicate/bad-body cases fail closed or are recorded | `status_test.go` suite | COMPONENT+PROCESS PASS |
| AMF-15 N1 optional IE / plan selection | COMPONENT: N1 generated with and without ePCO; both decode back through the pinned 5GSM codec | ePCO option `{protocol 1, value 01}` appears in the Create N1 and decodes identically; absence yields no ePCO IE. NW-Agent Plan-selection observation is not part of this peer | `peer_test.go::TestN1OptionalEPCOIsEncodedIntoCreate` | COMPONENT PASS for N1 optional-IE generation; NW-Agent plan-selection parity NOT_RUN |

Interpretation rules:

- COMPONENT+PROCESS PASS means the peer's own protocol behavior and the second
  process boundary are proven. It never means a real SMF consumed the exchange.
- AMF-01/02/03/13/14 stay `PASS` at component/process level until D3 supplies the
  real-SMF lane; they must then be re-run and re-recorded, not relabelled.
- AMF-07 is now qualified because the peer rejects indistinguishable wire
  traffic instead of guessing; the earlier `NOT_RUN` reflected a restriction
  that no longer exists in that form.

### 16.3 Ingress diagnostics and redaction

Every Namf transfer produces ordered ledger events:

- `namf.n1n2.request_received`: method, matched route pattern, HTTP protocol,
  content type, body size and SHA-256;
- `namf.n1n2.parsed`: PDU session ID, part count, part Content-IDs/media
  types/sizes/digests, decoded UPF address/TEID/QFIs, `notActedOn` fields;
- `namf.n1n2.accepted` or `namf.n1n2.rejected`: exact status, cause and
  transaction identity.

Requests that match no route are recorded as `sbi.unmatched_request`; a known path
with a wrong method is recorded as `sbi.method_not_allowed` with the `Allow`
header. Paths are templated per segment against a closed set of literal route
segments, so an unmatched or malformed path cannot leak a subscriber identity or
an opaque resource reference (`/namf-comm/v1/ue-contexts/{id}/{id}`).

The protocol response is written and flushed *before* scenario waiters are
released, so a later step (for example `notify-failure`) cannot act on a transfer
that the requester has not yet been told about.

Operator logs (`--log-level`) are a redacted projection: full SUPI is replaced by
a truncated SHA-256 (`supi=sha256:…`), the raw `Content-Type` header is replaced
by its parsed media type (or `<invalid>`), and only an allowlist of scalar detail
keys is printed. Raw NAS/N2 octets, request bodies and callback URLs with query
strings are never logged. The event ledger itself (test-control endpoint, loop
back only) keeps the exact values required as evidence.

Regression: `TestRedactedLoggingNeverPrintsFullSUPIOrBody` injects a synthetic
SUPI, an opaque session reference and a malformed `Content-Type` that embeds a
SUPI, then asserts none of them, no raw N2 bytes and no body digest appear in the
process log; `TestSanitizeContentTypeAndPath` pins the sanitizers.

### 16.4 Quality gates for this round

All commands were executed locally on Windows with `GOWORK=off` and a
workspace-local `GOCACHE`; logs are in
`artifacts/acceptance/20261120-mock-amf-conformance/`.

| Gate | Result |
| --- | --- |
| `go test ./...` | PASS (all packages) |
| `go test -race ./...` | PASS (all packages, including the native process tests) |
| `go test -race ./internal/...` | PASS |
| `go vet ./...` | PASS |
| `gofmt -l` over LF-normalized sources | PASS (no output) |
| Native build `./cmd/mock-amf`, `./cmd/env-5gc-sim` | PASS |
| Native Windows process checks (`serve` health over h2c, `run` scenario, failure-notification scenario) | PASS (`cmd/mock-amf/process_test.go`) |
| h2c integration + two-UE concurrency + duplicate/delayed callbacks | PASS (`internal/mockamf`) |
| N2 response golden vectors from the pinned asn1c APER codec (independent encoder oracle) | PASS (6 vectors: IPv4/IPv6, 1–3 QoS flows, TEID `0x01020304`/`0x12345678`/`0x10203040`, QFI 63). Generator and vectors: `artifacts/acceptance/20261120-mock-amf-conformance/{oracle-driver.c,asn1c-oracle-vectors.txt}` |
| `scripts/contract_gate.py`, `scripts/package_boundary.py`, `scripts/embedded_contract_assets.py` | PASS |
| `git diff --check` | PASS |
| GitHub Actions `Owner Verify` / `windows-process-smoke` | **NOT_RUN / ENVIRONMENT_BLOCKED**: jobs fail in ~2s with `The job was not started because recent account payments have failed…` (`env-5gc-sim#73`). No CI PASS is claimed. |

### 16.5 Operator entry points

- `configs/examples/mock-amf-local.yaml` — single-UE establishment, Scheme C
  routing; documents the TS 29.500 indirect (SCP) form of `nsmfApiRoot` +
  `sbiTargetApiRoot` next to the default direct form.
- `configs/examples/mock-amf-scenario-establish-two-ue.yaml` — two UEs / two
  sessions.
- `configs/examples/mock-amf-scenario-reject-async.yaml` — 202 asynchronous
  rejection and the standard failure notification.

`mock-amf run --config … --scenario … --json` executes one scenario and exits
with the scenario status; `mock-amf serve --config …` keeps the SBI listener and
test-control endpoints available for an external runner.

## 17. D3 record — real OpenAMSM establishment (2026-11-20)

Status: **PASS** (`D3_REAL_OPENAMSM_ESTABLISHMENT_PASS`,
`SBI_PROCEDURE_SMOKE_PASS` for this procedure). Evidence:
`artifacts/acceptance/20261120-d3-real-openamsm-establishment/` (manifest,
narrative, peer ledger, PFCP capture, SMF/UPF windows, MAS trace, independent
state reads, and the five earlier failing attempts).

### 17.1 What was proven

One Mock AMF process completed, for one UE (`imsi-999700000000001`) and one PDU
session (PSI 6), against the real `env-openamsm@594dec78` stack:

| Step | Result |
| --- | --- |
| CreateSMContext via SCP → NW-Agent Scheme C facade → real SMF | `201` + real SMF `Location` (`nc…/sm-contexts/1`); the 927-byte request body and its digest are retained in the ledger |
| real SMF Namf `N1N2MessageTransfer` via the Agent relay | `200 {cause:N1_N2_TRANSFER_INITIATED}`, 3 multipart parts, PSI 6, QFI 1, UPF N3 `10.30.20.7:36083` |
| Mock AMF `PDUSessionResourceSetupResponseTransfer` (RAN `10.10.0.8`/TEID `1001`/QFI 1) | 13 bytes, `sha256:b3016cf1…`, retained in the ledger |
| UpdateSMContext (`PDU_RES_SETUP_RSP`) via SCP → Agent → real SMF | `204` |
| real SMF `ngap_handle_pdu_session_resource_setup_response_transfer` | handler entered, `ogs_asn_decode` succeeded, no error branch, `mas_ssm_on_ran_fteid` trace `ON_RAN_FTEID result=0` |
| SSM → UP session → PFCP Session Modification | `Update FAR` FORW, destination Access, Outer Header Creation GTP-U/UDP/IPv4 `10.10.0.8` TEID `1001`; response `53` |
| no unexpected PFCP DELETE | no `54`/`55` in the capture |
| independent SMF state | `/pdu-info`: PSI 6, QFI 1/5QI 9, `n3.gnb 1001@[10.10.0.8]:2152`, `pdu_state=active` |

### 17.2 Topology and SCP

The Create and Update are sent to the SCP (`10.30.20.200:7777`) and reach the
Agent through TS 29.500 indirect communication: the peer sends
`User-Agent: AMF-mock-amf` and `3gpp-Sbi-Target-ApiRoot: http://127.0.0.1:18091`,
which `src/scp/sbi-path.c` requires and honours. The Namf return hop is the
environment's own `namf_peer=agent_relay` direct SMF→Agent delivery, because the
Agent is not an NRF-registered NF; that is the same path the real AMF uses in
Scheme C. Two new configuration fields carry this
(`userAgent`, `sbiTargetApiRoot`); an empty `sbiTargetApiRoot` keeps direct
communication and sends no target header, and a target-less SCP call still fails
closed.

### 17.3 Interop defects the run exposed (all fixed in this repository)

1. A real SMF multipart root part carries **no** Content-ID (Open5GS
   `build_multipart()` emits only a Content-Type there).
2. `PDUSessionAggregateMaximumBitRate` (id 130) and the other members of
   `PDUSessionResourceSetupRequestTransferIEs` are **known** IEs, not unknown
   ones; only a genuinely unknown reject IE may fail the transfer.
3. `Content-ID` must be written **bare** (`ngap-sm`), because Open5GS stores the
   header verbatim and compares it to the JSON `contentId`.
4. A buffered early `N1N2MessageTransfer` must become `CONSUMED` when the SM
   Context binds; otherwise a fast SMF makes the Setup Response unreachable.

### 17.4 External observations (not patched here)

- `[OES] plan library (oes-dsl/1.3) failed to load` / `plan file missing:
  tools/nw-agent/plans/...` at SMF start (`src/smf/oes/plan_provider.c:770`,
  `runtime.c:76`), logged since 2026-11-17; the library reloads on demand and the
  plan executed.
- `[6] OES.Start adapt failed` (`src/smf/gsm-sm.c:1462`) after the PFCP
  modification completed: the 5GSM FSM's local `OES.Start` fallback cannot
  resolve a plan in `agent_step`, where the NW-Agent owns it. It does not change
  the N2 decode, the F-TEID commit, the PFCP modification or the `204`.
- `CREATE_CHARGING` reports `E_NOT_IMPL`/`stub` (documented simplification).

### 17.5 Not claimed

No real gNB/UE access, NAS security, NGAP/SCTP or user-plane ping; no N1 accept
assessment; no Modify/Release beyond the establishment Update; no D4 parity and
no `FULL_INTERFACE_PARITY_PASS`; no CI PASS (`#73`).

## 18. Release-lifecycle record — real OpenAMSM Create/Update/Release (2026-11-20)

Status: **`MOCK_AMF_RELEASE_SBI_PASS__REAL_SMF_RELEASE_STATE_BLOCKED`**.
Evidence: `artifacts/acceptance/20261120-mock-amf-release-lifecycle/` (manifest,
summary, narrative, SBI/PFCP traces, 60-sample SMF state, UPF state, gate logs,
the operator script, and the four diagnostic attempts).

### 18.1 What was added to the peer

Release hardening (`runner.go`, `session.go`, `config.go`, `peer.go`):

- a released `(SUPI, PSI)` is terminal; a second `release` step fails closed with
  `ErrConflict` and never sends a duplicate Release to the SMF;
- the `nsmf.release` ledger event now pins the exact request URI, content type,
  request bytes/digest, and the SMF response bytes/digest, so evidence is the
  bytes on the wire, not a reconstruction;
- a non-2xx answer records `nsmf.release.rejected` and leaves the session
  established (a deliberate retry is possible); a transport failure or timeout
  records `nsmf.release.failed` and never marks the session released.

`await-control` (new test-control step, not a 3GPP concept): blocks until the
runner posts `/mock-amf/v1/continue`, records `scenario.await_control` and
`scenario.continued`, and rejects a stray continue with `409`. It exists so the
acceptance can prove "independent state read happened before the Release"
without a wall-clock sleep.

The Release request body stays `{}` with `Content-Type: application/json`,
reviewed against the pinned TS 29.502 `ReleaseSmContext` contract
(`requestBody.required: false`; `SmContextReleaseData` has no required member)
and the real OpenAMSM handling of this mode. No release cause is invented; the
Agent release path does not interpret the body.

### 18.2 The single real run

`rel-20261120-01`, SUPI `imsi-999700000000001`, PSI 6, through the mandatory SCP
→ NW-Agent Scheme C → real `env-openamsm@594dec78`. Steps:
`create → await-n1n2 → update-setup-response → await-control → release`, one
process, one scenario, peer exit 0.

| Item | Result |
| --- | --- |
| CreateSMContext | `201` + real SMF Location `…/sm-contexts/1`; 928-byte body pinned |
| Namf return hop | `200 N1_N2_TRANSFER_INITIATED`, 3 parts, QFI 1, UPF N3 `42798` |
| UpdateSMContext | `204`; 13-byte N2 setup response pinned; SMF committed `10.10.0.8`/`1001` |
| PFCP Session Modification | frames 10/11 (52/53) |
| independent read at the barrier | `/pdu-info` `pdu_state=active`, `n3.gnb 1001@[10.10.0.8]:2152`, `qos_flows [{qfi:1,5qi:9}]` |
| ReleaseSMContext | `POST …/sm-contexts/1/release` via SCP, `application/json`, `{}`, `200 {"smContextRef":"1"}` |
| PFCP Session Deletion | frames 12/13 (54 SEID `0x37b`, 55 SEID `0x6f0`) matching the establishment F-SEIDs |
| UPF cleanup | `[Removed] Number of UPF-sessions is now 0`; `fivegs_upffunction_upf_sessionnbr 0` |
| PCF / UDM cleanup | `DELETE_SM_POLICY {"terminated":"1"}`, UECM deregistration, SC `lifecycle=RELEASING` |
| **SMF SM Context** | **not released**: `/pdu-info` `pdu_state=active` in all 60 post-release samples; `pfcp_sessions_active 1`; no `[Removed] Number of SMF-Sessions` |

Acceptance mapping:

| Case | Status |
| --- | --- |
| `MOCK_AMF_CREATE_PASS` | PASS |
| `MOCK_AMF_UPDATE_PASS` | PASS |
| `MOCK_AMF_RELEASE_SBI_PASS` | PASS |
| `REAL_PFCP_DELETION_PASS` | PASS |
| `REAL_UPF_CLEANUP_PASS` | PASS |
| `REAL_OPENAMSM_RELEASE_PASS` | **FAIL** — the SMF executed the plan but kept the SM Context |
| `CREATE_UPDATE_RELEASE_LIFECYCLE_PASS` | **FAIL** — blocked by the item above |
| `MOCK_AMF_V1_LIFECYCLE_ACCEPTED` | **NOT_CLAIMED** |

### 18.3 Blocker and its owner

The failure is an OpenAMSM Scheme-C (`agent_step`) release-state defect, not a
Mock AMF protocol defect and not an environment/transport fault:

- `src/smf/gsm-sm.c:1545-1565`: the PFCP deletion response in
  `smf_gsm_state_operational` takes the `SMF_CATALOG_OP_DELETE_UP_SESSION` branch
  and completes the MAS invoke **without**
  `OGS_FSM_TRAN(s, smf_gsm_state_session_will_release)`.
- `src/smf/mas/sc/session_context.c:562-641`: `commit_release_advance` sets
  `SMF_SC_STATE_RELEASING` and ends in `mas_session_context_ack_amf_release`,
  which only answers the release stream / sets `release_http_done`; nothing calls
  `smf_oes_finish_release()` or `SMF_SESS_CLEAR`.
- The vanilla `smf_nsmf_handle_release_sm_context` flow is unavailable in this
  mode (deliberate `403 AGENT_STEP_NSMF_REJECTED`).

Tracked as `odango-chan/env-openamsm#10` (with `#8` for the undeclared release
plan `trigger` input and `#9` for the pre-existing OES startup noise). No
OpenAMSM source/config/runtime state was patched and no resource was removed by
hand to make a check pass.

**Attribution control (peer is not the cause).** Three checks separate the peer
from the defect:

1. The Agent executed the whole RELEASE plan (`r1..r6 status OK`) and returned
   `200 {"smContextRef":"1"}`; a malformed/mis-addressed request would fail at
   the SBI/plan layer, which did not happen.
2. The Agent's `/release` branch ignores the request body and hardcodes
   `entry.start_inputs = {"trigger": "6"}` (`tools/nw-agent/server.py`), so the
   SMF-side MAS op sequence cannot depend on the `{}` body or any other JSON.
3. A control run (`attempts/attempt-8-hold-after-release/`) keeps the Mock AMF
   alive for 25 s after the Release. The SMF sends **no** callback
   (`expect-no-n1n2` PASS, no `namf.*` event, no request to `127.0.0.1:18092`),
   yet `/pdu-info` still reports `active` ~85 s after the Release.

The source explains why no AMF action can reach the clear path in this mode:
`smf_uecm_oes_release_handoff()` (`src/smf/smf-sm.c:44-70`) sees the agent
`RELEASE_SM_CONTEXT` frame, answers the MAS waiter via `smf_mas_on_southbound()`
and returns `true`; the callers then `break` before `smf_sess_clear_if_may()`.
The other clear hook, `smf_oes_finish_release()`
(`src/smf/oes/runtime.c:1120`, invoked at `runtime.c:1348` when a local OES
workflow completes), needs an OES release instance that `agent_step`
deliberately does not create (the SMF's own comment at `smf-sm.c:44-56`).

### 18.4 Environment observation (recorded, not patched)

A Create issued within ~2 s of stack start fails with `No UPFs are PFCP associated
that are suited to RR`, because the UPF completes the PFCP association ~2.5 s
after its listeners appear. `run-lifecycle.sh` therefore waits for the real
`PFCP associated [10.30.20.4]` line before starting the scenario, and the PFCP
association exchange is inside the capture.

### 18.5 Not claimed

`MOCK_AMF_V1_LIFECYCLE_ACCEPTED` is deferred until `env-openamsm#10` is fixed
and a fresh run proves the SMF-side release state. No D4 parity, no
`FULL_INTERFACE_PARITY_PASS`, no CI PASS (`#73`); all gates in this round are
local (`LOCAL_ACCEPTANCE_PASS`).

## 19. UE-requested release record — real OpenAMSM (2026-11-20)

Status: **`UE_REQUESTED_RELEASE_LIFECYCLE_PASS`**.
Evidence: `artifacts/acceptance/20261120-mock-amf-ue-release/` (manifest,
summary, SBI/PFCP/SMF/UPF traces, narrative, the operator script, and the
OpenAMSM patch set under `openamsm-patches/`).

### 19.1 Procedure and why it differs from §18

§18 is the **network-requested** release: the AMF decides, invokes
`Nsmf_PDUSession_ReleaseSMContext` (`POST …/release`) and OpenAMSM uses delete
trigger 6. This section is the **UE-requested** release (TS 23.502 §4.3.4.2):

1. UE → AMF → SMF: `UpdateSMContext` with the 5GSM PDU Session Release Request
   (N1 type 0xd1).
2. SMF → AMF: the Update answer carries the 5GSM Release Command (0xd3) and the
   NGAP PDU Session Resource Release Command (`PDU_RES_REL_CMD`).
3. AMF/RAN → SMF: `UpdateSMContext` with the N2 Release Response
   (`PDU_RES_REL_RSP`, empty `PDUSessionResourceReleaseResponseTransfer`).
4. UE → AMF → SMF: `UpdateSMContext` with the 5GSM Release Complete (0xd4).
   Steps 3 and 4 are independent and may arrive in either order.
5. The SMF runs the local release plan with trigger 2 (`UE_REQUESTED`), deletes
   the PFCP session, deregisters UECM, deletes the PCF policy and removes the SM
   context.

The peer models only this narrow control-plane exchange; it is not a UE or a
RAN, and the N2 payloads are the minimum the procedure needs.

### 19.2 Peer additions

- Scenario actions `ue-release-request`, `ue-release-complete`,
  `ue-release-n2-response`; the request validates the SMF answer (N1 Release
  Command PSI/PTI and the N2 `PDU_RES_REL_CMD` part) and fails closed on a
  mismatch, a duplicate completion, or a network Release layered on an in-flight
  UE release.
- States `RELEASE_COMMAND_RECEIVED`, `N1_RELEASE_COMPLETE_SENT`,
  `N2_RELEASE_SENT`; the session projection records `releaseMode=ue_requested`,
  the command/complete/N2 statuses and digests.
- `n2transfer.EncodeReleaseResponseTransfer` (APER `0x00` for the empty
  transfer).
- `ca-client-tools@d4a88b0` adds the 5GSM Release Request/Complete encoders and
  the Release Command header decoder, with the message types pinned to
  `lib/nas/5gs/message.h` (209/211/212).

### 19.3 Real result

One run `ue-rel-20261120-01` (SUPI `imsi-999700000000001`, PSI 6) through the
SCP → patched NW-Agent facade → real `env-openamsm@594dec78`:

| Item | Result |
| --- | --- |
| UE Release Request | `UpdateSMContext` 200 with N1 `2e0601d3…` + N2 `PDU_RES_REL_CMD` |
| N2 Release Response | `204` |
| N1 Release Complete | `204` |
| SMF plan | `plan_source=local wf-certified-pdu-rel-v4` r1..r6 |
| PFCP deletion | 54/55 with SEIDs `0xbe2`/`0xe40` matching the establishment |
| UPF | `[Removed] Number of UPF-sessions is now 0`, metric 0 |
| SM context | removed: `/pdu-info` empty, `[Removed] Number of SMF-Sessions is now 0`, `pfcp_sessions_active 0` |

Acceptance: `MOCK_AMF_UE_RELEASE_PASS`, `REAL_OPENAMSM_UE_RELEASE_PASS`,
`REAL_PFCP_DELETION_PASS`, `REAL_UPF_CLEANUP_PASS`,
`UE_REQUESTED_RELEASE_LIFECYCLE_PASS` all PASS **on the patched build**. This is
not a claim about `env-openamsm` main: the six patches are still OPEN in
`env-openamsm#12`, and the unpatched baseline remains BLOCKED for this
procedure. The outbound SM Context status
notification is `NOT_RUN` in this mode (no AMF NF client; see 19.4).

### 19.4 OpenAMSM support delivered as patches

The Scheme C environment did not support the UE-release ingress; the run exposed
four gaps and the fixes are delivered as six patch files (source not committed):

- `0003` agent_step guard allows N1 0xd1/0xd4 and N2 `PDU_RES_REL_RSP`;
- `0004` the release plan declares `start_inputs.trigger`, seeded from the
  intent's delete trigger;
- `0005` the NW-Agent facade forwards the UE-release Updates to the SMF;
- `0006` no AMF client: the SM Context status notification is skipped instead of
  `ogs_assert(client)` aborting the SMF;
- `0007` the OES executor honours `async_ok` so the plan completes;
- `0008` the OES instance is released before `SMF_SESS_CLEAR`, otherwise
  `smf_sess_clear()` skips with `reason=oes_owns_release`.

`openamsm-patches/README.md` documents applying them, pointing the SMF at the
staged plan library and running the Agent from a patched copy.

### 19.5 Not claimed

No outbound status notification in Scheme C; no real gNB/UE, NAS security,
NGAP/SCTP or user-plane probe; no CI PASS (`#73`). The network-requested
`ReleaseSMContext` SMF-state limitation (§18, `env-openamsm#10`) is unchanged —
this section proves the other procedure, not that one.

## 20. macOS/arm64 native record (2026-11-21)

Status: **`MOCK_AMF_MACOS_NATIVE_PASS`** for the peer and the
Create/Update/SBI-Release lanes. The real lifecycle verdicts remain
owner-split: network-requested release is **BLOCKED** by `env-openamsm#10`,
and UE-requested release is **BLOCKED** by `env-openamsm#12` in the unpatched
baseline; the UE procedure passed only on a build carrying the six patches.

Evidence: `artifacts/acceptance/20261121-macos-native-e2e/` (environment,
gate logs, the three lane directories, the UE harness, and the retained failed
attempt).

### 20.1 Host and binary

One Go implementation, same `mock-amf` executable semantics as Linux/WSL2:
native Mach-O arm64 build, `go1.26.2 darwin/arm64`, macOS 27.2.1, no Docker,
Linux VM or Rosetta. Binary
`sha256:2549993a63e162da84c403ac6dd154f5d063b90d5ce2fee160a7e4858a33b4e0`.
The real core is `env-openamsm` PR #14 HEAD `778a1e8` (native macOS baseline,
still OPEN), reached through the mandatory SCP with TS 29.500 indirect
communication.

### 20.2 Gates and lanes

| Gate / lane | Result |
| --- | --- |
| `go build`, `go test`, `go test -race` (`./...` and `./internal/...`), `go vet`, `gofmt`, contract/package/embedded gates, `git diff --check` | PASS |
| Focused `internal/mockamf` + `n2transfer` + `cmd/mock-amf` suite | PASS (192 entries, 86 top-level PASS, 0 FAIL) |
| D3 establishment (`macos-pr76-d3-baseline-03`) | PASS — Create `201`, Namf `200`, Update `204`, PFCP `50/51` + `52/53`, `/pdu-info` active, no `54/55`; repeat run also PASS |
| Network-requested release (`macos-pr76-network-baseline-03`) | SBI PASS, PFCP `54/55`, UPF 0, **SM Context retained** → `BLOCKED` / `env-openamsm#10` |
| UE-requested release (`macos-pr76-ue-release-03`, patched build only) | PASS — N1 Release Request → Release Command + N2 REL_CMD → N2 REL_RSP + N1 Complete → PFCP `50/51`, `52/53`, `54/55` → UPF 0, `[Removed] Number of SMF-Sessions is now 0`, `/pdu-info` absent |

The network-requested run uses the unpatched PR #14 build
(`open5gs-smfd sha256:600d3c71…`). The UE run uses a locally patched build
(`open5gs-smfd sha256:5be40ea2…`); patch digests and the apply/rebuild steps are
in `environment.txt` and `harness/README.md`. The unpatched tree does **not**
support the UE procedure, and this section does not claim that it does.

### 20.3 Result tokens

| Token | Status |
| --- | --- |
| `MOCK_AMF_COMPONENT_PASS` / `MOCK_AMF_PROCESS_PASS` | PASS |
| `MOCK_AMF_CREATE_PASS` / `MOCK_AMF_UPDATE_PASS` | PASS |
| `MOCK_AMF_RELEASE_SBI_PASS` / `MOCK_AMF_UE_RELEASE_PASS` | PASS |
| `MOCK_AMF_MACOS_NATIVE_PASS` | PASS |
| `REAL_PFCP_DELETION_PASS` / `REAL_UPF_CLEANUP_PASS` | PASS |
| `REAL_OPENAMSM_RELEASE_PASS` | FAIL (`env-openamsm#10`) |
| `REAL_OPENAMSM_UE_RELEASE_PASS` | PASS_PATCHED_BUILD_ONLY |
| `NETWORK_REQUESTED_RELEASE_LIFECYCLE_PASS` | BLOCKED (`env-openamsm#10`) |
| `UE_REQUESTED_RELEASE_LIFECYCLE_PASS` | BLOCKED (`env-openamsm#12` unmerged) |
| `CREATE_UPDATE_RELEASE_LIFECYCLE_PASS` | FAIL (same `#10`) |
| `MOCK_AMF_V1_LIFECYCLE_ACCEPTED` | NOT_CLAIMED |

### 20.4 Not claimed

No Linux/WSL2 re-run in this round (`NOT_RUN`; no Linux host). No CI PASS
(`#73`). No D4 parity. The macOS result does not upgrade the OpenAMSM#10 or
#12 blockers, and no Mock AMF success criterion was relaxed to make the real
SMF look clean.

## 21. UE-requested modify record — peer capability (2026-11-22)

This section records the **test-peer** half of the UE-requested PDU Session
Modification acceptance (`env-5gc-sim#78`, `env-openamsm#16`). It does not claim
a real Modify E2E; the Scheme A/C network-effect gates are separate runs.

### 21.1 Procedure

TS 23.502 §4.3.3.2 over Nsmf `UpdateSMContext`:

1. UE → AMF → SMF: 5GSM PDU Session Modification Request (`0xc9`) in the N1
   part, with one Requested QoS flow descriptions IE (`0x79`).
2. SMF → AMF: Update answer with the 5GSM Modification Command (`0xcb`,
   Authorized QoS flow descriptions) and the NGAP `PDU_RES_MOD_REQ` transfer.
3. UE → AMF → SMF: 5GSM Modification Complete (`0xcc`).
4. RAN → AMF → SMF: `PDU_RES_MOD_RSP` carrying the accepted QFI list.

Steps 3 and 4 are independent Updates and may arrive in either order.

### 21.2 Peer additions

- Scenario input `ues[].modify` with `qfi`, optional `fiveQI` and the
  GFBR/MFBR UL/DL values in Kbps. Values the TS 24.501 bitrate grammar cannot
  represent exactly are rejected before any I/O.
- Scenario actions `ue-modify-request`, `ue-modify-complete`,
  `ue-modify-n2-response`.
- `ue-modify-request` requires an `UPDATE_ACKNOWLEDGED` (or previously
  `MODIFY_COMPLETED`) session, sends the real `0xc9`, and accepts only a `200`
  answer whose N1 part decodes as a `0xcb` Command for the same PSI/PTI and QFI
  with the exact authorized bitrates, and whose N2 part decodes as a
  `PDU_RES_MOD_REQ` containing that QFI. Any mismatch fails closed.
- `ue-modify-complete` / `ue-modify-n2-response` require the observed command;
  they never fabricate the UE/RAN side of the transaction. States
  `MODIFY_COMMAND_RECEIVED`, `N1_MODIFY_COMPLETE_SENT`, `N2_MODIFY_SENT`,
  `MODIFY_COMPLETED` make duplicate or out-of-order completion fail closed while
  allowing either order.
- `n2transfer.EncodeQoSModifyRequestTransfer` emits the QoS-only modify request
  shape the pinned SMF builds, and is covered by a decode round-trip.
- Scheme C delivers the N1 Modification Command through the Namf relay. The
  peer retains the N1 bytes from the accepted transfer, decodes the `0xcb`
  command, requires its authorized QFI to match the N2 `PDU_RES_MOD_REQ` QFI
  set, records the command (`namf.ue_modify.command`) and exposes the new
  `await-modify-command` step; a command-less facade response records
  `MODIFY_REQUEST_SENT` and a Complete is only accepted after the real command.
- A native (Scheme A) SMF returns the N1/N2 establishment parts in the
  CreateSMContext response body without a Namf transfer. The peer now consumes
  that body (`nsmf.create.n1n2`): it decodes the N2 `PDU_RES_SETUP_REQ`,
  requires the scenario QFI set, and attaches the transfer to the session so
  `await-n1n2` / `update-setup-response` work unchanged. A body without N1/N2
  keeps the existing Namf path; a mismatch fails closed.
- `ca-client-tools@a3733f1` (PR #26) provides the scoped `0xc9`/`0xcb`/`0xcc`
  codecs, including the OpenAMSM-decoder golden vectors.

### 21.3 Not claimed

The isolated Scheme A run is executed and recorded in
`artifacts/acceptance/20261122-scheme-a-ue-modify-release/`: real N1 `0xc9` /
`0xd1`, mandatory SCP, real SMF `0xcb`/`0xd3` commands, N2 modify/release
transfers, PFCP 50/51 + 52/53 (QER MBR/GBR 500/1000 and GBR 200/400) +
54/55, UPF session 0 and SMF context removal. The test peer itself still does
not assert PFCP/QER state (that proof comes from the independent packet
capture); Scheme C parity remains open.

## 22. Concurrent scenario groups — peer capability (2026-11-22)

The scenario runner executes top-level `steps` sequentially. The `parallel`
action is the only way scenario actions overlap in time, so a release test can
prove concurrent UE/session isolation instead of emulating it with sequential
steps. This is test-control input only: it is not a 3GPP wire contract and does
not change any SBI request/response shape or acceptance semantics.

### 22.1 YAML syntax

```yaml
steps:
  - action: parallel
    timeout: 5s            # group deadline (default: requestTimeout)
    steps:
      - action: create
        ue: 0
        timeout: 3s        # sub-step deadline (default: requestTimeout)
      - action: create
        ue: 1
        timeout: 3s
  - action: await-n1n2
    ue: 0
  - action: await-n1n2
    ue: 1
```

`steps` is a `Step` list and is valid only on `action: parallel`. Sub-steps use
the normal supported actions (`create`, `await-n1n2`, release/modify actions,
`await-control`, ...); a sub-step's `ue` must be in range. An empty `steps` list
and a nested `parallel` are validation errors. The parent `parallel` step's
`ue` is ignored.

### 22.2 Execution, deadlines and results

- All sub-steps are started before any is awaited and joined with a
  `sync.WaitGroup`; the group never returns while a sub-step goroutine runs.
- The group gets its own `context.WithTimeout` from the parent runner context.
  Each sub-step derives its own timeout from that group context, so the parent
  deadline always caps the group.
- A failing sub-step makes the group FAIL. The implementation chooses
  **fail-fast cancellation**: the first failure cancels the group's derived
  context so in-flight siblings stop, and the group still waits for all of them.
  Parent cancellation propagates to every sub-step. This is the documented
  trade-off: a sibling can end as FAIL with `context canceled` even though its
  own action was valid.
- `StepResult.SubSteps` records every sub-step with its declared index, action
  and UE. The slice is ordered by declaration, not completion; it is omitted
  (`omitempty`) for normal steps, so existing `RunResult` JSON stays backward
  compatible. The group is PASS only when every sub-step is PASS.

### 22.3 Concurrency safety

`Peer.mu` already serializes the session map, pending creates, tombstones, event
ledger/sequence, waiters and control barrier; outbound request state is the
`http.Client`/HTTP/2 transport, which is safe for concurrent use. Concurrent
sub-steps therefore reuse the same synchronization as concurrent HTTP/2 streams.
Sub-step results are written to per-index slots, requiring no shared lock.
`go test -race ./internal/mockamf/...` covers the group path.

### 22.4 Focused tests

`internal/mockamf/parallel_test.go` covers: two parallel `create` sub-steps for
two UEs that both bind; a fake-SMF arrival barrier that can only release after
both Creates overlap (so a sequential runner would fail); empty/nested/out-of-
range/unsupported validation; YAML decoding; and a failing sub-step that makes
the group FAIL while its blocked sibling is cancelled and joined. Tests use
context deadlines, not sleeps, as authority.
