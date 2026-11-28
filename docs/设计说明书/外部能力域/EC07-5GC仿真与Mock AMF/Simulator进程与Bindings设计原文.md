> 迁移来源：env-5gc-sim/docs/design/process-and-bindings.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：Simulator 单 World 进程、配置、就绪、Owner API、调度与关闭设计  
> 迁移追踪：ca-agent-next Issue #12。env-5gc-sim 同时包含 5GC reference simulator 与 Mock AMF test peer；两者在 Next 设计中分开描述。

---

# env-5gc-sim Process and Bindings Design

Status: Accepted  
Version: v0.2  
Date: 2026-09-18  
Scope: first N4/PFCP reference-simulation slice

## 1. 目的

本文定义 `env-5gc-sim` 从 S2 owner-local core 进入真实进程与跨仓集成时的**进程、配置、健康/就绪、C2/C6 transport 与 consumer-side binding 设计**。

它回答：

```text
env-5gc-sim 进程怎么启动
一个进程承载多少 world
配置从哪里进入
何时算 alive，何时才算 ready
C2/C6 如何跨进程访问
reset 如何进入 owner-local WorldStore
Scheduler/Fabric binding 如何接入而不复制 owner machine contract
endpoint 如何注册/接收 delivery
HTTP/client disconnect 如何与 backend operation lifecycle 分离
graceful shutdown 怎么做
CA Lab / Sandbox / Runtime 分别看到什么
```

本文不重新定义：

```text
C1 Environment/scheduler machine contract       -> ca-sandbox
C3/C4 simulated acquisition/Network Observation -> env-fabric
C5 intervention lease                            -> ca-benchmark-engine + env-fabric
C7 ProviderBinding/Outcome/Reconcile             -> ca-runtime
C8 evidence closure                              -> evaluation owners
```

这些 owner contract 未 READY 时，本文只冻结 consumer-side seam 和 fail-closed 行为，不允许本仓补第二套 wire DTO。

## 2. 首片进程模型

首个 process profile 固定：

```text
one env-5gc-sim process
  = one live materialized world
  = one WorldStore
  = one worldRef
  = one current worldGeneration
  = one scheduler binding
  = one set of SMF/UPF simulated endpoints
```

同一进程允许 Environment reset：

```text
same worldRef
new worldGeneration
revision -> 0
seed reapplied
bindings revalidated/reregistered
```

首片**不实现 multi-world server**。

这样做的原因：

1. Environment/Instance isolation 与 CA Lab ownership 一一对应；
2. reset/generation fence 不需要额外 world router；
3. endpoint registration 不需要复用多个 world/generation namespace；
4. 单个进程崩溃不影响其他 Environment；
5. 后续若真需要 multi-world，可以版本化新的 process profile，而不改变 C2/C6 domain contract。

`env-5gc-sim` 仍然不是 Environment manager。Environment create/reuse/delete 由 Sandbox/Lab 负责。

## 3. Owner 分工

```text
CA Lab
  = process/resource materialization
  = PID/process identity/log ownership
  = start/stop/delete/reconcile of process resource

Sandbox
  = Environment identity/generation
  = deterministic scheduler semantic owner
  = Environment reset orchestration

env-5gc-sim
  = one world
  = C2 fact authority
  = C6 backend operation authority
  = simulated NF endpoint behavior
  = owner-local reset primitive

Service Fabric
  = simulated endpoint registration/delivery boundary
  = Network Observation
  = network-fault enforcement

Runtime
  = ProviderBinding/read/ObservationSource
  = Runtime Outcome/Reconcile
```

保持：

```text
process alive != Environment READY
HTTP reachable != Runtime Provider admitted
world current != Runtime binding current
endpoint registered != Fabric proves message delivered
```

## 4. Binary 与 composition

`cmd/env-5gc-sim/main.go` is executable composition only: strict v3 YAML config, schema profile, one WorldStore, FactReader, deterministic process scheduler, endpoint registry, independent PFCP UDP transport, OperationService, owner HTTP server, readiness and managed shutdown. Domain transitions remain in owner-local packages.

## 5. CLI surface

```bash
env-5gc-sim serve --config <file>
env-5gc-sim check-config --config <file>
env-5gc-sim contract-info
```

`serve` is the foreground long-running process. Background process ownership belongs to CA Lab. There is no production standalone or synchronous in-process PFCP profile.

## 6. Process configuration

The operator supplies only `--config FILE`; strict block-style YAML parsing and semantic validation complete before listeners or UDP sockets open. The canonical input is `FiveGCSimProcessConfig.v3`, with `process`, `world`, and `n4` sections. JSON-shaped input, multiple documents, duplicate keys, unknown fields, YAML aliases/anchors, non-string mapping keys, and scalar types outside JSON are rejected. The resulting value is decoded against the sole `ProcessConfig` structure with unknown fields disabled; its digest is SHA-256 over canonical JSON for that decoded profile. The checked-in JSON Schema remains the field/wire-shape authority. `process.providerListen` and `process.controlListen` are distinct explicit HTTP listener addresses. `n4.smf.local`, `n4.smf.peer`, and `n4.upf.local` are explicit IPv4 socket addresses; response timeout is positive and bounded. `world` contains the world identity and an explicitly validated seed profile. The process scheduler ref is derived as `simulator-local:<worldGeneration>`.

`n4.smf.peer` is the semantic UPF endpoint. Fabric is not configured as a protocol peer; where required, it transparently mediates the topology/network path. Process config does not copy C1/C3 owner DTOs or create a second authority for Network Observation.

Seed profile parameters remain explicitly validated. `registered-active-pdu-sessions-v1` preserves current-main per-session activity seeds and exact C2 semantics. No config reload occurs while serving.

## 7. Config validation

`check-config` strictly decodes the v3 YAML profile, validates the canonical schema and lock, world identity, seed parameters, explicit IPv4 socket addresses, and positive response timeout. It does not start a server, open UDP sockets, mutate WorldStore, contact Runtime, or configure Fabric. Socket bind/readiness is checked by `serve`.

## 8. Listen 与端口

首片默认 loopback。

非 loopback listen 必须显式配置并由 deployment policy允许。

如果配置端口已占用：

```text
startup fails
reason = LISTEN_IN_USE
no fallback port
no kill of unrelated process
```

进程不自己扫描“可用端口”。

若 Lab 分配动态端口，应由 Lab materialization 机制给出最终 listen address。

## 9. Process identity

每次启动生成：

```text
processInstanceRef
```

它只表示本次 OS process incarnation。

identity 至少包含：

```text
service = env-5gc-sim
processInstanceRef
pid?                         # local diagnostic only
processStartedAt?            # diagnostic only
configDigest
worldRef
worldGeneration
supported C2/C6 contract identities
```

`pid/processStartedAt` 不参与 5GC domain identity、fact digest、scheduler ordering 或 replay equality。

## 10. Transport choice

首片 owner API：

```text
HTTP
JSON body
canonical C2/C6/process schemas as payload authority
route/status/body binding = schemas/v1alpha1/{provider,control}.openapi.yaml
```

OpenAPI 3.1 只绑定 route/status/body；各 JSON Schema 仍是 payload machine authority。

HTTP/1.1 或 HTTP/2 都可承载；HTTP版本不是 semantic contract。

首片不恢复 Provider MCP。

原因：

1. C2/C6 已有 canonical JSON Schema；
2. Runtime ProviderContract transport-neutral；
3. Sandbox/Fabric 各有自己的 owner surface；
4. HTTP方便 Lab/Runtime adapter做身份、超时、typed evidence测试。

## 11. Owner HTTP API

### 11.1 Provider / Control listener split

Provider exposes only business C2/C6 routes and its checked-in OpenAPI/docs:

```text
GET  /v1/world
POST /v1/facts/read
POST /v1/operations
GET  /openapi.yaml
GET  /docs/
```

Control exposes lifecycle and trusted internal routes with separate OpenAPI/docs:

```text
GET  /management/v1/identity
GET  /management/v1/healthz
GET  /management/v1/readyz
POST /management/v1/drain
GET  /management/v1/operations/{operationId}
POST /internal/v1/world/reset
GET  /openapi.yaml
GET  /docs/
```

Root `/identity`, `/healthz`, `/readyz` aliases are absent. `/internal/fabric/delivery` is removed; N4 crosses the PFCP/UDP protocol boundary directly and Fabric transparently mediates the network path.

Managed Node identity/health/readiness semantics remain owned by `ca-lab`'s Managed Node contract. Health reports process liveness; readiness reports normal work admission and returns 503 while draining. Process-specific world fence and phase stay in the owner process contract.

### 11.3 WorldHandle

```http
GET /v1/world
```

成功 body：

```text
FiveGCSimWorld.v1
```

它是 C2 owner record，不是 Environment status。

### 11.4 Fact read

```http
POST /v1/facts/read
Content-Type: application/json
```

request：

```text
FiveGCSimFactReadRequest.v1
```

accepted result：

```text
FiveGCSimFactReadResult.v1
```

acceptance failure：

```text
FiveGCSimFactReadAcceptanceError.v1
```

### 11.5 Operation

```http
POST /v1/operations
Content-Type: application/json
```

request：

```text
FiveGCSimOperationRequest.v1
```

accepted backend result：

```text
FiveGCSimOperationResult.v1
```

acceptance failure：

```text
FiveGCSimOperationAcceptanceError.v1
```

### 11.6 Host-only reset

```http
POST /internal/v1/world/reset
```

这是 deployment/control surface，不是 Runtime Capability，不进入 Agent Toolset。

request/response machine contract：

```text
FiveGCSimWorldResetRequest.v1
FiveGCSimWorldResetResult.v1
```

它只调用本仓 WorldStore.Reset 和 binding refresh。

在 C1 machine contract未 READY前，不复制 Sandbox owner DTO。owner-local reset input只包含本仓实际需要的：

```text
expected current worldRef/generation
new worldGeneration
new schedulerBindingRef
seed profile + parameters
```

未来 Sandbox adapter负责把 C1 authoritative material映射进这些 inputs。

### 11.7 禁止 generic admin

首片不提供：

```text
GET /debug/world/all
POST /fault
POST /inject
POST /reconcile
POST /retry
POST /ensure
POST /runtime-outcome
```

## 12. HTTP status mapping

Transport status 与 C2/C6 semantic result分开。

### 12.1 Accepted semantic

HTTP 200：

```text
FiveGCSimWorld
FactReadResult:
  FOUND
  KNOWN_ABSENT
  KNOWN_NEGATIVE
  UNAVAILABLE
  INVALID_QUERY

OperationResult:
  COMPLETED
  REJECTED
  WAIT_EXPIRED
  INVALID_PRESTATE
```

例如：

```text
C6 INVALID_PRESTATE
  = valid accepted backend result
  = HTTP 200
```

### 12.2 Acceptance errors

固定：

```text
400
  MALFORMED_REQUEST
  UNSUPPORTED_CONTRACT_VERSION
  UNSUPPORTED_FACT_SEMANTIC
  UNSUPPORTED_OPERATION
  INVALID_PARAMETER

404
  WORLD_NOT_FOUND

409
  WORLD_GENERATION_MISMATCH
  EXPECTED_REVISION_MISMATCH
```

Body始终是 canonical acceptance-error schema。

### 12.3 Process-local errors

至少：

```text
SERVICE_NOT_READY
SERVICE_DRAINING
RESET_BUSY
BINDING_UNAVAILABLE
CONFIGURATION_INVALID
```

`FiveGCSimProcessError.v1` 是 canonical process/control error body，当前 codes 包括 `MALFORMED_REQUEST / CONFIGURATION_INVALID / LISTEN_IN_USE / SERVICE_NOT_READY / SERVICE_DRAINING / BINDING_UNAVAILABLE / RESET_BUSY / WORLD_REF_MISMATCH / WORLD_GENERATION_MISMATCH / INTERNAL_ERROR`。

process错误不能伪装成 SourceFact `UNAVAILABLE` 或 C6 `WAIT_EXPIRED`。

## 13. Readiness state machine

Process states remain `BOOTING`, `BINDING`, `READY`, `DRAINING`, `STOPPED`, and `FAILED`.

### 13.1 READY conditions

READY requires the strict v2 process config and schema profile, a materialized WorldStore, installed C2/C6 services, the generation-fenced process-local logical scheduler, and both independently bound PFCP UDP sockets. No reset or drain may be active.

A local socket bind proves only local endpoint availability. It does not prove remote peer reachability, transparent Fabric mediation, or Network Observation. C1/C3 are not process startup dependencies. A failed socket bind leaves the process in BINDING/NOT_READY; production has no in-process PFCP fallback.

## 14. Health response

Health is a process projection, not a 5GC fact. Contract v2 reports local `scheduler` and `n4` readiness with process/world identity. `n4=READY` means both local UDP sockets are bound; it does not prove remote peer reachability, Fabric mediation, or message delivery. Non-READY responses contain a safe reason code and do not expose credentials or full world state.

## 15. Process scheduler and PFCP UDP transport

### 15.1 Deterministic logical scheduler

Production `ProcessScheduler` wraps `scheduler.Local` and fences scheduled work to `simulator-local:<worldGeneration>`. Logical time advances only through deterministic scheduler operations. Reset re-pins the wrapper after WorldStore generation changes. Wall-clock response deadlines apply only to network PFCP response waiting; they do not replace logical scheduling.

### 15.2 PFCP sockets and wire boundary

`binding.PFCPUdp` owns distinct SMF and UPF UDP sockets. `n4.smf.peer` is the semantic UPF destination. The supported wire messages are Session Establishment Request/Response and Session Deletion Request/Response (types 50/51/54/55). The codec validates PFCP framing and supported message types.

Simulator-only values (SUPI, session/resource refs, Runtime invocation refs, backend refs, and world fence) stay in a local transaction table. The wire contains only PFCP-native header and IEs. Responses match on sequence number, response type, header SEID, and exact configured UPF peer address; arrival order is never a correlation key. The UPF accepts only a request matching a locally reserved transaction's sequence, Node ID, CP F-SEID, message type, and required session IEs, allowing transparent Fabric forwarding without a private wire field. A bounded response wait yields `WAIT_EXPIRED`; there is no automatic retry or success bypass. Late, duplicate, malformed, unsupported, and wrong-peer response datagrams cannot complete another operation.

C6 keeps protocol-native transaction identity separate from caller correlation and local backend refs. Retained `protocolTransactions` entries describe only wire message kind, direction, sequence and socket endpoints.

When the UPF generates an accepted establishment response, the process transport retains its generated UP F-SEID under the exact owner `pfcpResourceRef` before sending the datagram. If Fabric drops that response, a later explicitly admitted exact-cleanup operation can still emit a standards-shaped Session Deletion Request for that resource. The mapping stays owner-local and is not exposed as an SMF observation or public fact.

### 15.3 Service Fabric boundary

The simulator targets the configured UPF peer directly. If topology requires Service Fabric mediation, Fabric transparently owns that network path and the resulting Network Observation. The simulator does not address a Fabric callback as its PFCP peer and does not infer Fabric delivery from local UDP send/receive. Fabric P3 qualification remains tracked by `env-fabric#11`.

## 17. Runtime C2 binding expectation

## 17. Runtime C2 binding expectation

目标：

```text
Runtime read-only Capability / ObservationSource
-> C7 admitted binding
-> env-5gc-sim HTTP adapter
-> POST /v1/facts/read
```

Runtime adapter必须保留：

```text
worldRef
worldGeneration
evaluatedWorldRevision
sourceAuthority
factRef
schemaRef/schemaDigest
contentDigest when present
```

Agent-facing `ca-mcp` 不直接发现本 HTTP API。

## 18. Runtime C6 binding expectation

目标：

```text
Runtime Capability
-> ProviderBinding
-> env-5gc-sim Provider adapter
-> POST /v1/operations
-> C6 OperationResult
-> ProviderKnowledge
-> Runtime Outcome/Reconcile
```

保持：

```text
HTTP success != C6 COMPLETED
C6 WAIT_EXPIRED != HTTP timeout
C6 WAIT_EXPIRED != Runtime OUTCOME_UNKNOWN by itself
HTTP client disconnect != backend NOT_COMMITTED
```

## 19. HTTP lifecycle vs backend operation

### 19.1 C2 read

read只读，可以随 request context取消。

### 19.2 Mutation before dispatch

如果 caller取消发生在：

```text
acceptance / pre-state
before backend protocol dispatch barrier
```

可以停止且不产生 backend dispatch。

### 19.3 Mutation after dispatch

一旦 operation越过 authoritative backend dispatch barrier：

```text
client disconnect
HTTP response write failure
Runtime transport timeout
```

都不能自动：

```text
rollback domain state
cancel already delivered PFCP request
mark NOT_DISPATCHED
retry
```

backend procedure继续按 scheduler/endpoint规则推进。

这与 Runtime R1 的 transport-lifecycle原则一致。

## 20. Response write failure

如果 C6 OperationResult已经形成，但 HTTP写回失败：

```text
historical OperationResult remains immutable
world remains as actually committed
transport failure does not alter C6 result
```

Runtime/C7如何恢复 transport ambiguity由 Runtime owner决定。

首片不提前增加 `GET /operations/{ref}` 之类 recovery query；如果未来 C7确有需要，再版本化设计。

## 21. Reset orchestration

Reset is host control. It closes admission to concurrent reset, requires current world/generation and no active accepted operation, advances WorldStore generation, reapplies seed data, and rotates the process scheduler fence. Configured socket addresses remain the process configuration for the new generation; old-generation callbacks/commits fail closed. Reset does not create Fabric delivery evidence or complete pending work to satisfy a safe point.

A reset that cannot re-establish required local process endpoints remains NOT_READY with an explicit reason; it never returns partial READY.

## 22. Graceful shutdown

触发：

```text
SIGTERM / SIGINT
Lab-owned process stop
```

流程：

```text
phase -> DRAINING
ready=false
stop admitting new C2/C6 work except identity/health
stop admitting reset
unregister Fabric endpoints when possible
cancel not-yet-dispatched local work
allow already-dispatched work only to bounded safe shutdown point
close HTTP listener
release process-local resources
exit
```

shutdown timeout是 process-control wall clock，可以使用真实时间；它不能改写 domain/C6 knowledge。

强制结束时不得伪造 COMPLETED/FAILED。

## 23. Persistence

首片：

```text
world state = in-memory
operation journal = in-memory
```

不宣称 crash-recoverable continuation。

进程意外退出：

```text
current world process lost
Environment must not remain READY
```

恢复必须由 Environment owner建立新的有效 process/generation策略。

同一 `worldRef` 不能让新进程冒充旧 generation仍存活。

C8 evidence retention与 live process persistence分开。

## 24. Logging

日志是诊断，不是事实 authority。

建议每条关键日志带：

```text
processInstanceRef
worldRef
worldGeneration
backendOperationRef when known
protocolTransactionRef when known
```

日志不能替代：

```text
C2 SourceFact
C4 Network Observation
Runtime Outcome
Benchmark Verdict
```

不得输出 credential/secret。

## 25. Process transport failure behavior

A process scheduler failure blocks deterministic scheduled work. PFCP socket bind failure prevents READY. A response timeout returns `WAIT_EXPIRED` while preserving backend journal state and operation result immutability. Late or mismatched responses are quarantined and cannot satisfy another transaction. No retry, local success fallback, or Fabric delivery inference is allowed. C2 fact reads remain simulator-owned, subject to HTTP/process admission behavior.

## 26. Endpoint reference behavior

Endpoint-local fixture可以在启动/reset配置：

```text
ACCEPT
REJECT(reasonCode)
RESPONSE_AFTER(logical endpoint delay)
RESOURCE_UNAVAILABLE(reasonCode)
```

禁止：

```text
DROP_RESPONSE
SUPPRESS_RESPONSE
REORDER_NETWORK
NETWORK_DELAY
UNKNOWN_DISPOSITION
```

## 27. No Provider-side identity MCP in this repository

env-5gc-sim **不暴露 Agent-facing MCP**，也不恢复 Sandbox legacy
Provider MCP，且**不拥有**用户可见身份解析 MCP。

2026-09-28 曾为 first-slice 增加独立 Provider-side identity MCP
（`/provider/mcp/identity` + `/internal/mcp/identity-control`），但该
ownership 假设已被 Issue #4 修正：alias 解析 authority 唯一属于
`tool-common`（canonical `subject.identity.lookup@v1`）。本仓的
重复实现（`internal/identity`、`internal/identitymcp`、对应设计文档）
已于 2026-09-29 删除，Git 历史保留记录。

sim 侧身份锚点 authority：

```text
docs/design/simulated-ue-identity-anchors.md
```

必须保持：

```text
alias resolution != simulator domain read
mappingRevision authority = tool-common only
sim world generation authority = env-5gc-sim only
```

Agent 仍只经过：

```text
Agent -> ca-mcp -> RuntimeHost -> admitted Capability -> ProviderBinding
  -> tool-common (identity) -> env-5gc-sim (SUPI-anchored domain)
```

## 28. Trust surfaces

首片默认受控本地/test Environment，即使暂不做 TLS/OAuth，也要保持 logical separation：

```text
Runtime-facing owner API
  /v1/world
  /v1/facts/read
  /v1/operations

Control listener
  /management/v1/identity
  /management/v1/healthz
  /management/v1/readyz
  /internal/v1/world/reset

Provider and Control use separate listeners, each with its own OpenAPI and docs.
There is no simulator HTTP delivery callback; N4 uses PFCP/UDP.
```

Host-only control不进入普通 Runtime Provider surface。

## 29. Implementation packages

进入本阶段后新增：

```text
cmd/env-5gc-sim/
  main.go

internal/app/
  app.go
  lifecycle.go
  readiness.go

internal/config/
  config.go
  load.go
  validate.go
  digest.go

internal/httpapi/
  server.go
  identity.go
  health.go
  world.go
  fact.go
  operation.go
  reset.go
  errors.go

internal/binding/
  scheduler_adapter.go
  fabric_adapter.go
  status.go
```

依赖方向：

```text
cmd -> app

app
  -> config
  -> world/fact/operation/endpoints
  -> binding
  -> httpapi

httpapi
  -> contract + owner-local services

binding
  -> internal scheduler/Fabric ports
  -> owner adapters only

world/fact/operation/smf/upf
  must not depend on httpapi/app/config
```

## 30. Required process tests

```text
TestProcess_InvalidConfigFailsBeforeListen
TestProcess_PortInUseDoesNotFallback
TestProcess_IdentityMatchesCurrentWorldFence
TestProcess_HealthIs503BeforeBindingsReady
TestProcess_HealthIs200OnlyAfterRequiredBindings
TestProcess_C2HTTPRoundTripUsesCanonicalSchema
TestProcess_C6HTTPRoundTripUsesCanonicalSchema
TestProcess_InvalidPrestateIsHTTP200C6Result
TestProcess_AcceptanceErrorUsesTypedBodyAndStatus
TestProcess_ClientDisconnectAfterDispatchDoesNotCancelBackend
TestProcess_ResetBusyRejectsActiveOperation
TestProcess_ResetChangesGenerationAndReregistersBindings
TestProcess_OldDeliveryAfterResetCannotMutateWorld
TestProcess_FabricLossDropsReadinessWithoutFallback
TestProcess_GracefulDrainRejectsNewOperations
```

这些可以使用 adapter test doubles做本仓 component test，但不能据此标 S3/S4/S5 CROSS_REPO PASS。

## 31. S3/S4/S5 preparation

### S3

当前已实现：

```text
C3 production HTTP adapter
endpoint registration + callback translation
binding readiness state
Environment/generation/scheduler fence check
same-attempt ACK replay
```

C4 Network Observation consumer/runtime integration仍 OPEN；C3 live cross-process evidence仍需 S3 真实 composition。

### S4

现在可实现：

```text
host-only reset primitive
one-process-one-world lifecycle
ready=false during reset
old-generation fail-closed
```

真实 C1 production consumer 已接入；Sandbox owner + simulator + Service Fabric 的 live composition 仍需 S4/S3 acceptance evidence。

### S5

现在可实现：

```text
stable HTTP C2/C6 owner API
typed status/error behavior
```

Runtime C7 ProviderBinding/adapter仍由 Runtime owner闭合。

## 32. CA Lab expectation

Lab adapter把 simulator当普通 managed process：

```text
Ensure
  -> write resolved process config
  -> spawn env-5gc-sim serve --config ...
  -> verify /management/v1/identity on Control listener
  -> poll /management/v1/readyz on Control listener
  -> publish approved Provider and Control endpoint relations

Observe
  -> verify process identity
  -> read /management/v1/healthz
  -> do not infer READY from PID/port

Stop/Delete
  -> controlled signal + ownership check
  -> never kill unrelated process
```

具体 ProviderDescriptor/Instance contract仍属于 CA Lab。

## 33. Runtime expectation

Runtime adapter拿到 admitted/frozen endpoint后：

```text
C7 binding
-> owner HTTP request
-> typed C2/C6 decode
-> preserve source/provenance
-> map ProviderKnowledge
```

Runtime不得：

```text
scan localhost
parse Lab human CLI output
spawn simulator
choose arbitrary Environment
fallback to legacy Sandbox simulator
```

## 34. Evidence

后续 process/S3/S4/S5验收至少保留：

```text
process config digest
processInstanceRef
identity response
health response
worldRef/generation
scheduler binding ref/status
Fabric registration refs when owner contract exists
C2/C6 request/response canonical material
reset before/after identity
shutdown/cleanup result
```

日志不能替代 owner-native typed records。

## 35. Common failures

### 端口开了就标 READY

错误。查：

```text
healthz
scheduler binding
Fabric registration
generation match
```

### production fallback到 TestScheduler

错误。TestScheduler只属于 S2 component composition。

### Fabric不可用就切 LocalFabric

错误。会把 S3故障伪装成 READY。

### client timeout后 cancel backend

错误。先判断是否已越过 dispatch barrier。

### reset直接替换 map

错误。必须经过 WorldStore.Reset + generation fence + binding refresh。

### Runtime调用 internal reset

错误。reset是 host control，不是 Runtime business Provider API。

## 36. Definition of Done — canonical process

The owner-local process gate requires strict `FiveGCSimProcessConfig.v3`, schema/OpenAPI/fixture validation, one process and one world, isolated Provider/Control listeners, Managed Node identity/health/readiness and Drain, C2/C6/reset surfaces, separate PFCP/UDP sockets, protocol-native wire correlation, no production in-process PFCP path, focused transport tests, `go test ./...`, `go vet ./...`, `go test -race ./internal/...`, and a retained real-process PFCP establishment/deletion smoke.

These owner-local gates do not establish Fabric P3, cross-repository Environment composition, or Network Observation. Those require fresh Fabric/Sandbox/Lab/Runtime evidence.

## 37. Current status source

The current implementation, acceptance, and evidence status is maintained in
[`docs/WORK.md`](../WORK.md) and [`docs/TRACEABILITY.md`](../TRACEABILITY.md).
Historical S0-S7 execution records remain in migration/evidence documents and
are not a live readiness signal.

## 38. Canonical process profile

`serve` is the only production process profile. It consumes `FiveGCSimProcessConfig.v3`, creates one world and a deterministic process-local scheduler, binds independent SMF/UPF PFCP UDP sockets and Provider/Control HTTP listeners. `check-config` performs strict config and schema checks without opening sockets or mutating state.

The old standalone profile and synchronous in-process transport are removed from production. Component tests may inject deterministic transports, but those tests do not qualify the process network path.

The canonical config fields are `process`, `world`, and `n4`. The scheduler binding ref is derived from world generation. SMF peer is always the semantic UPF; Fabric may mediate the network path by topology. Process identity and health use v2. Reset rotates world generation and scheduler binding while retaining the configured endpoint identity. Local readiness does not imply Fabric or remote-peer acceptance.

`serve` exposes business C2/C6 on Provider and lifecycle/reset on Control; root aliases and the Fabric delivery callback are absent. Process readiness is an owner-local liveness projection and never a 5GC domain fact.
