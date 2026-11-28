> 迁移来源：env-5gc-sim/docs/design/owner-local-core.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：Simulator Owner-local Core 与状态变更边界  
> 迁移追踪：ca-agent-next Issue #12。env-5gc-sim 同时包含 5GC reference simulator 与 Mock AMF test peer；两者在 Next 设计中分开描述。

---

# S2 Owner-Local Core Design

Status: Accepted  
Version: v0.2  
Date: 2026-09-23  
Scope: N4/PFCP first slice only

## 1. 目的

本文是 `env-5gc-sim` **S2 Owner-local Core** 的可执行施工图。

它回答：

```text
第一行 production code 写在哪里
World 如何存储 / snapshot / commit / reset
worldRevision 到底由谁推进
C2 FactReader 怎样从同一 revision 产出 SourceFact
C6 OperationService 怎样区分 acceptance / prestate / dispatch / wait
SMF/UPF endpoint 怎样通过 PFCP semantic exchange 推进 domain state
S2 本地怎样测试 Scheduler/Fabric seam 而不发明 C1/C3 machine contract
S2-01..S2-17 分别落在哪个 package / test / evidence
```

本文不重新定义 C2/C6 wire contract：

```text
C2 semantic authority  -> docs/design/observations.md
C6 semantic authority  -> docs/design/capabilities.md
machine shape authority -> schemas/v1alpha1/**
S2 acceptance authority -> docs/migration/phase-acceptance.md
evidence rules          -> docs/migration/acceptance-evidence.md
```

本文不重复定义 process/network transport。正式进程、配置、readiness、C2/C6 HTTP 与 external binding seam 已由 `process-and-bindings.md` 冻结；S2 本身仍必须能够在**无真实 C1/C3/C4/C5/C7/C8**的情况下，以 production owner-local packages + deterministic local test seams 完成 COMPONENT acceptance。

## 2. S2 Definition of Ready

S2 开工前必须满足：

```text
S0-01 PASS
S0-02 PASS
S0-03 PASS
S0-04 PASS
S0-05 PASS

go.mod exists
central Go layout profile includes env-5gc-sim
schema.lock is current
C2/C6 fixture manifest is complete for S0 scope
contractcodec/canonical/digest gate is green
```

S1 可以并行，不阻塞 S2 owner-local code；但迁移时不得用尚未完成的 S1 inventory 为理由把 legacy shortcut复制进新实现。

## 3. S2 明确边界

### 3.1 S2 实现

```text
schema-backed internal C2/C6 Go types
one World Store per materialized owner-local world
WorldHandle / fence / revision
immutable WorldSnapshot
atomic domain commit
reset / generation invalidation
deterministic initial seed
C2 FactReader / SourceFact producer
C6 OperationService
backendOperationRef allocation
operation-local journal
SMF first-slice controller
UPF first-slice endpoint
PFCP semantic request/response types
endpoint registry
consumer-side SchedulerPort seam
consumer-side FabricPort seam
deterministic local scheduler test double
immediate local protocol-delivery test double
endpoint behavior fixture
component acceptance tests
```

### 3.2 S2 不实现

```text
env-5gc-sim HTTP/gRPC/MCP server
production process lifecycle/readiness
Sandbox Environment binding API
C1 scheduler wire contract
C3 SimulatedProtocolEnvelope
C4 FabricEvent / Network Observation
C5 Intervention / boundary fault lease
C7 Runtime Provider/read adapter
C8 evidence closure service
dynamic registration procedure
N11/N2/N3
QoS expansion
real Open5GS adapter
protocol drop/delay/reorder fault
Runtime OUTCOME_UNKNOWN
Runtime reconcile policy
```

S2 可以制造 `WAIT_EXPIRED` backend knowledge，但不能自己生成 Runtime `OUTCOME_UNKNOWN`。

## 4. S2 目标目录

S0 已存在：

```text
internal/contractcodec/
internal/contracttest/
```

S2 新增：

```text
internal/
├── contract/
│   ├── c2.go
│   ├── c6.go
│   ├── refs.go
│   └── roundtrip_test.go
├── world/
│   ├── types.go
│   ├── state.go
│   ├── snapshot.go
│   ├── store.go
│   ├── reset.go
│   ├── invariants.go
│   └── store_s2_test.go
├── pfcp/
│   ├── message.go
│   ├── transaction.go
│   └── semantic.go
├── scheduler/
│   └── port.go
├── endpoint/
│   ├── handler.go
│   ├── registry.go
│   ├── fabric_port.go
│   └── endpoint_s2_test.go
├── smf/
│   ├── controller.go
│   ├── create.go
│   ├── release.go
│   └── response.go
├── upf/
│   ├── endpoint.go
│   ├── establish.go
│   ├── delete.go
│   └── behavior.go
├── fact/
│   ├── reader.go
│   ├── source_fact.go
│   ├── ref.go
│   └── reader_s2_test.go
├── operation/
│   ├── service.go
│   ├── acceptance.go
│   ├── prestate.go
│   ├── refs.go
│   ├── journal.go
│   ├── wait.go
│   └── service_s2_test.go
├── fixture/
│   ├── seed.go
│   └── endpoint_behavior.go
└── testkit/
    ├── composition.go
    ├── scheduler.go
    ├── fabric.go
    ├── refs.go
    └── evidence.go
```

### 4.1 S2 暂不创建 `cmd/env-5gc-sim`

S2 是 owner-local production core，不是 process integration 阶段。

S2 不创建或测试正式进程 surface；这些内容统一按 `process-and-bindings.md` 在 S2 PASS 后的 Process Preparation 实现。S2 可以全部通过 Go package/component tests 完成。

### 4.2 `internal/amf` 暂不要求

首片 registration 只使用 deterministic registered-UE seed；不实现动态 registration FSM。

`internal/amf/` 等 dynamic registration 进入对应 feature scope 时再创建，避免空 package 和假实现。

## 5. 依赖方向

必须保持单向：

```text
contractcodec
    ↑
contract

world        pfcp        scheduler
  ↑           ↑             ↑
  ├──── fact  │             │
  │           │             │
  ├──── smf ──┼── endpoint ─┤
  │           │             │
  └──── upf ──┘             │
          ↑                  │
          └──── operation ───┘

testkit may depend on all internal owner-local packages
production packages must not depend on testkit
```

更精确：

```text
world
  -> stdlib only

pfcp
  -> stdlib only

scheduler
  -> stdlib only; defines consumer-side internal seam

endpoint
  -> pfcp
  -> scheduler only where endpoint-local scheduling is required

smf
  -> world + pfcp + endpoint + scheduler

upf
  -> world + pfcp + endpoint + scheduler

fact
  -> world + contract + contractcodec

operation
  -> world + contract + smf/upf + scheduler

fixture
  -> typed owner-local packages only

testkit
  -> all of the above for deterministic composition
```

禁止：

```text
world -> fact
world -> operation
world -> Runtime
world -> Fabric owner DTO
smf/upf -> operation
production package -> testkit
```

## 6. Schema-backed `internal/contract`

S2 需要唯一一套 private Go wire model。

规则：

```text
schemas/v1alpha1/** = authority
internal/contract/** = private Go representation of that authority
```

不得再出现第二套 hand-written transport DTO。

最低类型：

```go
type World struct { ... }                    // FiveGCSimWorld.v1
type FactReadRequest struct { ... }
type FactReadResult struct { ... }
type FactReadAcceptanceError struct { ... }
type SourceFact struct { ... }

type OperationRequest struct { ... }
type OperationResult struct { ... }
type OperationAcceptanceError struct { ... }
```

要求：

1. JSON field/enum/wire representation 与 schema 一致；
2. `worldRevision` wire 仍是 decimal string；
3. business value 使用 typed structs/enums，不使用 `map[string]any`；
4. round-trip canonical fixtures；
5. unknown field/version/enum fail-closed 仍由 S0 contract gate保证；
6. package 是 `internal`，不是跨仓 Go API。

如果后续采用生成代码，生成结果放在该 package，不新建 `generated/` architecture layer。

## 7. World 模型

### 7.1 一个 Store = 一个 materialized world

S2 不建立全局 WorldManager。

```text
world.Store
  = exactly one materialized env-5gc-sim world
```

Environment -> process -> world registry 属 process/binding 层。

一个 Store 至少包含：

```text
worldRef
worldGeneration
worldRevision
schedulerBindingRef
domainState
closed/reset fence state
```

### 7.2 First-slice domain state

```go
type State struct {
    Registrations map[string]RegistrationState
    Sessions      map[SessionKey]PDUSessionState
    PFCPResources map[string]PFCPResourceState
}
```

逻辑字段：

```text
RegistrationState
  supi
  registrationManagementState = REGISTERED | DEREGISTERED

PDUSessionState
  supi
  pduSessionId
  smLifecycle = CREATING | ESTABLISHED | MODIFYING | RELEASING | FAILED_OR_RECOVERY
  dnn
  sNssai
  upConnectionState? if modeled

PFCPResourceState
  pfcpResourceRef
  supi
  pduSessionId
  lifecycle = ESTABLISHING | ESTABLISHED | MODIFYING | DELETING
```

Absence 不保存成 mutable entity state：

```text
no map entry
  -> authoritative absence when query scope is valid
```

### 7.3 允许 partial state

世界不变量**不得**错误规定：

```text
PFCP resource exists -> PDU session must be ESTABLISHED
PDU session exists -> PFCP resource must exist
```

因为可靠性场景需要表达：

```text
PFCP committed
SMF still CREATING / FAILED_OR_RECOVERY

PFCP already absent
SMF still RELEASING
```

真正禁止的是 identity corruption，例如：

```text
same pfcpResourceRef attached to two different session subjects
same SessionKey with conflicting supi/session id
duplicate identical resourceRef entries
invalid typed lifecycle value
```

多个**不同** `pfcpResourceRef` 指向同一个 session 是允许的异常状态，C2 必须把 `resourceCount > 1` 原样暴露。

## 8. WorldHandle

内部：

```go
type Handle struct {
    WorldRef            string
    WorldGeneration     string
    WorldRevision       uint64
    SchedulerBindingRef string
}
```

wire encode：

```text
WorldRevision uint64
  -> decimal string
```

规则：

```text
worldRef
  = one logical materialized world identity

worldGeneration
  = reset fence
  = opaque equality token
  != numeric ordering counter

worldRevision
  = monotonic only inside one generation
```

生产 default：

```text
new world revision = 0
reset world revision = 0
```

Seed 是 baseline materialization，不被计作运行期 domain mutation。

## 9. WorldSnapshot

### 9.1 Snapshot 是 immutable deep copy

```go
type Snapshot struct {
    Handle Handle
    State  immutableState
}
```

要求：

- 获取 snapshot 时一次锁定 world revision；
- state 与 handle 来自同一个临界区；
- 返回后不能通过 map/slice/pointer alias 改 Store；
- FactReader 在一个 snapshot 上完成一次 read；
- operation pre-state 使用一个明确 snapshot/revision。

禁止返回内部 map 指针。

### 9.2 Historical behavior in S2

S2 不实现历史 revision store。

```text
CURRENT
  -> current snapshot

AT_REVISION == current revision
  -> current snapshot

AT_REVISION != current revision
  -> UNAVAILABLE
```

older revision 可以返回：

```text
reasonCode = REVISION_NOT_RETAINED
```

future/non-current revision 可以返回：

```text
reasonCode = REVISION_NOT_AVAILABLE
```

不得回退到 CURRENT。

C8 retention 以后再增加历史 materialization；不能在 S2 偷做第二套历史数据库。

## 10. Atomic Commit

### 10.1 唯一 domain mutation 入口

`world.Store` 是 `worldRevision` 唯一 authority。

所有运行期 domain mutation 必须走：

```go
Commit(fence, optionalExpectedRevision, mutation)
```

逻辑签名：

```go
type Fence struct {
    WorldRef        string
    WorldGeneration string
}

type CommitResult struct {
    BeforeRevision uint64
    AfterRevision  uint64
    Changed        bool
}

func (s *Store) Commit(
    ctx context.Context,
    fence Fence,
    expectedRevision *uint64,
    mutate func(*Draft) error,
) (CommitResult, error)
```

这是逻辑 contract；具体 Go 命名可微调，但语义不可变。

### 10.2 Commit algorithm

一次 Commit：

```text
lock
-> validate store open
-> validate worldRef
-> validate generation
-> validate expected revision when supplied
-> deep-clone current typed State into Draft
-> apply mutation only to Draft
-> validate domain invariants
-> semantic compare Draft vs current
-> if unchanged:
     publish nothing
     revision unchanged
-> if changed:
     revision = revision + 1 exactly once
     atomically publish Draft
-> unlock
```

Mutation error：

```text
discard Draft
revision unchanged
no partial state
```

### 10.3 不使用手工 dirty bit

首片 correctness 优先。

是否 changed 由 typed semantic equality 决定，不依赖调用者记得：

```text
tx.MarkDirty()
```

避免“改了状态但忘记 bump revision”的隐蔽错误。

未来性能优化若替换 deep-clone/equality，必须保留相同测试行为。

### 10.4 Atomic vs partial commit

```text
one Commit call
  -> at most one revision increment

two intentionally visible partial effects
  -> two Commit calls
  -> two revisions
```

不能在一个 Commit 内人为多次 bump revision。

## 11. Reset / Generation Invalidation

### 11.1 Reset 语义

S2 owner-local Reset：

```text
exclusive lock
-> capture old generation
-> replace generation with caller-supplied new opaque generation
-> replace schedulerBindingRef
-> deep-copy new seed baseline
-> revision = 0
-> publish atomically
```

首片 reset 保持同一个 `worldRef`，只更新 `worldGeneration`。

新 Environment/materialization 可以创建新的 worldRef；“新 Environment”与“同 Environment reset”不要混为一个动作。

### 11.2 Pending operation safety

WorldStore 的**硬安全责任**只有：

> reset 后，任何持旧 generation fence 的 commit 必须失败。

因此即使旧 goroutine/endpoint callback 没来得及 cancel：

```text
old callback
-> Commit(oldGeneration)
-> WORLD_GENERATION_MISMATCH / stale internal error
-> no domain mutation
```

OperationService/Scheduler 可以主动 cancel old-generation work，但那是资源清理优化，不是数据正确性的唯一防线。

### 11.3 Result/material stale rule

旧 generation 的：

```text
FactReadRequest
OperationRequest
SourceFact
backend callback
scheduled work
```

不得被静默 rebound 到新 generation。

## 12. Deterministic Seed

### 12.1 SeedSpec

`internal/fixture/seed.go` 提供 typed seed：

```go
type SeedSpec struct {
    Registrations []RegistrationSeed
    Sessions      []SessionSeed
    PFCPResources []PFCPResourceSeed
}
```

首个默认 seed：

```text
one REGISTERED UE
no target PDU session
no target PFCP resource
```

S2 不通过 AMF procedure“跑出”这个 seed。

### 12.2 Seed requirements

```text
deep copy input
stable sort set-like collections
reject duplicate identity
validate typed domain invariants
do not consume wall clock/randomness
same explicit world identity + generation + scheduler ref + seed
  -> same semantic initial state
```

修改原 SeedSpec 或测试返回对象不能反向修改 Store。

### 12.3 Ref generation

生产代码不得依赖 random UUID 才能保证正确性。

S2 注入：

```text
RefFactory
```

用于：

```text
backendOperationRef
pfcpResourceRef
protocolTransactionRef
factRef
```

默认实现可以生成 opaque unique ref；测试实现必须 deterministic。

Ref 的字符串格式不是 public semantic contract。

## 13. C2 FactReader

### 13.1 入口

逻辑 API：

```go
type AccessContext struct {
    AccessClass AccessClass // ORDINARY | EVALUATOR_ONLY
}

func (r *Reader) Read(
    ctx context.Context,
    access AccessContext,
    req contract.FactReadRequest,
) (contract.FactReadResult, *contract.FactReadAcceptanceError)
```

`AccessContext` 来自 trusted serving/binding layer，不来自 FactReadRequest payload。

因此 caller 不能通过请求字段自升权。

### 13.2 Read algorithm

```text
validate contract/profile already decoded by contract layer
-> validate worldRef/generation
-> obtain one Snapshot
-> resolve CURRENT / AT_REVISION
-> validate factSemantic + subject semantic
-> read typed state from that Snapshot only
-> derive resolution
-> if authoritative:
     build SourceFact
     attach schemaRef/schemaDigest
     assign stable factRef
     compute contentDigest
-> build FactReadResult
-> run S0 C2 invariant checker in tests / optional debug assertion
-> return
```

Read 不允许调用 `Store.Commit`。

### 13.3 Fact mappings

#### UE_REGISTRATION

```text
registration exists
  -> FOUND
  -> RegistrationFact.v1

known UE registration record says DEREGISTERED
  -> KNOWN_NEGATIVE
  -> typed registration value

no known UE record
  -> KNOWN_ABSENT
```

首个 default seed为 REGISTERED。

#### UE_REGISTRATION_CONTEXT

```text
registration exists
  -> FOUND
  -> RegistrationContextFact.v1
  -> {contextState, consistency}

no known UE record
  -> KNOWN_ABSENT
```

`contextState` / `consistency` 是从 RM state + registration context presence 派生的只读视图，不是第二份 mutable truth。

#### PDU_SESSION

```text
SessionKey exists
  -> FOUND
  -> PduSessionFact.v1
  -> smLifecycle + DNN/S-NSSAI/UP summary
  -> derived established / qosSatisfied / resolved5qi
  -> installed qosFlows（按 QFI 升序）

no SessionKey
  -> KNOWN_ABSENT
```

`sessions` entry 可携带 `required5qi` 与 installed `qosFlows`；`PDU_SESSION_CREATE` 可带 optional `fiveQi`，成功 establishment 后安装 deterministic default QoS flow（QFI 1）。

#### USER_PLANE_CONNECTIVITY

```text
SessionKey exists
  -> FOUND
  -> UserPlaneConnectivityFact.v1
  -> {available}
  -> available = ESTABLISHED && upConnectionState == ACTIVATED

no SessionKey
  -> KNOWN_ABSENT
```

Connectivity 是与 PDU_SESSION 独立的事实：`session exists != user-plane available`。

#### PFCP_RESOURCE

按 `supi + pduSessionId` 查询：

```text
0 resource
  -> KNOWN_ABSENT

1+ resource
  -> FOUND
  -> resourceCount = exact count
  -> resources sorted by pfcpResourceRef
```

多个不同 resourceRef 不自动去重。

### 13.4 FactRef

`factRef` 必须对“同一 concrete read material”稳定。

推荐 identity input：

```text
worldRef
worldGeneration
worldRevision
recordType
canonical subjectRef
resolution
accessClass
canonical correlationRefs
```

对该 tuple 做 deterministic digest/ref generation。

不要用：

```text
time.Now
global random
pointer address
map iteration order
```

`factRef` 不从 `contentDigest` 反推，避免循环：

```text
contentDigest includes factRef
```

### 13.5 schemaRef/schemaDigest

SourceFact：

```text
schemaRef
  = canonical FiveGCSimSourceFact root schema identity

schemaDigest
  = S0 schema.lock 对应 profile digest
```

不能在 S2 hard-code 一个看起来像 SHA 的常量。

### 13.6 materialRef

S2 不实现 C8 immutable material store。

因此：

```text
factRef       required
contentDigest recommended/produced
materialRef   absent in S2 unless a real owner-native retention implementation exists
```

不能把临时内存地址/文件路径冒充 materialRef。

## 14. Ordinary / Evaluator-only

首片使用同一 FactReader implementation，但 serving authority决定 AccessClass。

允许：

```text
ordinary binding
  -> AccessClass=ORDINARY

trusted evaluator binding
  -> AccessClass=EVALUATOR_ONLY
```

S2-09 必须证明：

1. FactReadRequest 无字段可以请求 elevation；
2. ordinary reader 永远不能因 payload/correlationRef 变成 EVALUATOR_ONLY；
3. evaluator reader 产生的 SourceFact 仍是 `sourceAuthority=env-5gc-sim`，不是第二 authority。

首片 evaluator-only 可以返回与 ordinary 相同 typed business value；S2 的目标先锁住**访问边界与 provenance**，不需要为了测试凭空增加 hidden business field。

## 15. C6 OperationService

### 15.1 入口

逻辑 API：

```go
func (s *Service) Execute(
    ctx context.Context,
    req contract.OperationRequest,
) (contract.OperationResult, *contract.OperationAcceptanceError)
```

### 15.2 五层必须分开

```text
1 contract acceptance
2 world fence/revision acceptance
3 semantic pre-state
4 backend dispatch / endpoint progress
5 response knowledge by deterministic wait deadline
```

不能把五层合成一个 `Outcome string`。

### 15.3 Acceptance

在分配 `backendOperationRef` 前检查：

```text
world exists/open
worldRef matches
worldGeneration matches
expectedWorldRevision matches when supplied
schedulerBindingRef in responseWaitBudget matches bound scheduler seam
request semantic/parameters already satisfy schema
```

失败：

```text
FiveGCSimOperationAcceptanceError
no backendOperationRef
no endpoint dispatch
no domain mutation
```

### 15.4 Backend operation allocation

Acceptance PASS 后：

```text
allocate new backendOperationRef
capture startWorldRevision
record callerCorrelationRefs exactly/canonically
```

同一个 Runtime request/correlation ref 重复出现：

```text
does NOT imply simulator dedupe
```

每次 accepted backend invocation 默认获得新的 `backendOperationRef`。

幂等只由具体 operation semantic 定义。

## 16. Semantic Pre-state

Pre-state failure属于 accepted backend operation：

```text
resultCode = INVALID_PRESTATE
backendEffectDispatch = NOT_DISPATCHED
startWorldRevision == endWorldRevision
```

### 16.1 PDU_SESSION_CREATE

首片必须：

```text
UE registration == REGISTERED
target PDU session absent
target session has zero PFCP resource
```

任一不满足：

```text
INVALID_PRESTATE
no endpoint dispatch
```

这显式覆盖 duplicate-resource reliability case。

### 16.2 PDU_SESSION_RELEASE

首片允许：

```text
target session exists
and lifecycle is ESTABLISHED
```

其他 lifecycle 先 fail closed 为 INVALID_PRESTATE；不要在 S2 发明复杂 ensure/recovery behavior。

### 16.3 PFCP_RESOURCE_CLEANUP

subject 必须包含 exact `pfcpResourceRef`。

若 exact ref absent：

```text
COMPLETED
NOT_DISPATCHED
ALREADY_ABSENT
revision unchanged
```

若存在：

```text
dispatch exact deletion path
never delete every resource for the session
```

## 17. Operation Journal

S2 增加 private internal journal，目的：

- debug component behavior；
- S2-17 证明“返回的 C6 knowledge”和“后来 backend/domain progress”可以分开；
- 不把 journal 变成 Runtime Outcome 或 public Observation。

最低记录：

```text
backendOperationRef
worldRef/generation
operationSemantic
subjectRef
startWorldRevision
callerCorrelationRefs
protocolTransactionRefs
internal lifecycle
returnedResult? immutable copy
latest backend progress
```

internal lifecycle 示例：

```text
ACCEPTED
PRESTATE_REJECTED
DISPATCHED
WAIT_EXPIRED_RETURNED
TERMINAL_RESPONSE_OBSERVED
COMPLETED
INVALIDATED_BY_RESET
```

这些 enum **不是 public C6 schema**。

关键：

```text
once C6 OperationResult returned
  -> never mutate/rewrite that returned record

later backend/domain progress
  -> visible through World/C2 and internal journal
  -> not by editing historical WAIT_EXPIRED into COMPLETED
```

## 18. First-slice create flow

### 18.1 Commit points

正常 create 固定三个 domain commit point：

```text
CP-CREATE-1
  SMF session ABSENT -> CREATING
  revision +1

PFCP request delivered to UPF

CP-CREATE-2
  UPF creates PFCP resource ESTABLISHED
  revision +1

PFCP success response delivered to SMF

CP-CREATE-3
  SMF session CREATING -> ESTABLISHED
  revision +1
```

因此正常 create：

```text
startRevision = R
endRevision   = R + 3
resultCode    = COMPLETED
dispatch      = DISPATCHED
```

这里的 “+3” 是首片 reference implementation 的 owner-local行为，不是 C6 wire contract 的永久跨版本承诺。若未来 state-machine design改变 commit point，需要先更新本文与 S2 cases。

### 18.2 为什么这样拆

它允许自然表达：

```text
session CREATING
PFCP already ESTABLISHED
SMF has not received terminal response
```

这正是后续 response-loss / reconcile 需要看到的 partial state。

## 19. Endpoint rejection flow

首片 reject fixture：

```text
CP-CREATE-1
  session -> CREATING

request delivered to UPF

UPF endpoint rejects before PFCP resource commit
  -> no PFCP resource

reject response delivered to SMF

CP-REJECT-1
  session CREATING -> FAILED_OR_RECOVERY
```

C6：

```text
REJECTED
DISPATCHED
protocolTransactionRefs present
no successful PFCP resource
```

所以 `REJECTED` 不等于“世界完全没变”。

Acceptance case 只要求没有成功 resource side effect；S2 额外通过 typed state证明失败 context 没被伪装成成功。

## 20. Release flow

正常 release：

```text
CP-RELEASE-1
  session ESTABLISHED -> RELEASING

PFCP deletion request delivered

CP-RELEASE-2
  exact related PFCP resource removed

PFCP deletion response delivered

CP-RELEASE-3
  session removed
```

若首片发现多个 PFCP resources：

```text
PDU_SESSION_RELEASE
  -> fail closed / INVALID_PRESTATE
```

不要由 release“顺手全删”，因为 duplicate resource 是需要暴露并由 recovery 明确处理的异常。

## 21. Exact PFCP cleanup

### existing resource

```text
CP-CLEANUP-1
  resource ESTABLISHED -> DELETING

exact deletion request delivered

CP-CLEANUP-2
  exact resource removed

response delivered
-> no extra session mutation
```

C6：

```text
COMPLETED + DISPATCHED
```

### already absent

```text
no commit
no protocol dispatch
COMPLETED + NOT_DISPATCHED + ALREADY_ABSENT
startRevision == endRevision
```

## 22. PFCP semantic package

`internal/pfcp` 只定义 owner-local semantic message，不定义 C3 envelope。

最低 message：

```text
SessionEstablishmentRequest
SessionEstablishmentResponse
SessionDeletionRequest
SessionDeletionResponse
```

字段仅保留 endpoint behavior 需要的 semantic data：

```text
transactionRef
supi
pduSessionId
pfcpResourceRef where applicable
accepted/reason for response
```

保持：

```text
pfcp.Message
!= SimulatedProtocolEnvelope
!= FabricEvent
!= packet/PCAP bytes
```

## 23. Endpoint Registry

`internal/endpoint` 定义 private local endpoint seam。

逻辑：

```go
type Handler interface {
    Handle(context.Context, pfcp.Message) error
}

type Registry interface {
    Register(endpointRef string, handler Handler) error
    Resolve(endpointRef string) (Handler, bool)
}
```

EndpointRef 在 S2 是 owner-local opaque ref。

S3 才由 Fabric owner contract 决定如何注册/寻址跨组件 simulated endpoint。

## 24. FabricPort — consumer-side seam only

S2 可以定义：

```go
type FabricPort interface {
    Send(context.Context, MessageCandidate) error
}
```

但这里：

```text
FabricPort
  = private consumer-side interface
  != C3 machine contract
  != Network Observation API
```

`MessageCandidate` 也是 private typed semantic carrier。

### 24.1 S2 LocalFabric

`internal/testkit/fabric.go` 提供：

```text
ImmediateLocalFabric
```

唯一行为：

```text
receive candidate
-> resolve destination endpoint
-> deliver immediately in caller-defined deterministic order
```

它明确**不支持**：

```text
drop
delay
reorder
mutate
fault receipt
FabricEvent
Network Observation
capture
```

因此 S2 evidence 绝不能把 LocalFabric 输出称为 Fabric evidence。

Production owner traffic uses the independent SMF/UPF PFCP UDP sockets in
`internal/binding/pfcp_udp.go`. The current testkit's synchronous transport is
component-only; it is not a production fallback and cannot qualify Fabric
delivery or Network Observation.

## 25. SchedulerPort — consumer-side seam only

C1 machine contract 当前 BLOCKED，所以 S2 不冻结 C1 wire type。

private seam 只表达 owner-local需要的能力：

```text
validate/resolve scheduler binding
resolve opaque logicalDuration according to bound profile
wait until terminal signal or logical deadline
schedule endpoint-local deterministic work
associate work with world generation fence
```

OperationService **不得自己 parse `logicalDuration`**。

例如：

```text
"5s"
```

的含义由 injected SchedulerPort 决定，不由 `time.ParseDuration` 变成系统 authority。

### 25.1 S2 TestScheduler

TestScheduler 使用显式 test profile：

```text
"s0" / "5s" / custom fixture token
  -> deterministic logical ticks
```

映射由 test composition提供。

TestScheduler：

- 不读 wall clock；
- 不调用 `time.Sleep`；
- stable FIFO tie-break；
- 可推进到 next scheduled event；
- 可让 endpoint-local response generation晚于 operation wait budget；
- reset 后旧 generation callback即使执行，也会被 WorldStore fence拒绝。

S3/S4 再替换为 C1 owner adapter。

### 25.2 Process-local deterministic scheduler

The canonical `serve` process uses `binding.ProcessScheduler` around
`internal/scheduler.Local`. Its identity is derived from world generation and
reset rebinds only through the explicit World reset path. It has no wall-clock
authority and does not replace Sandbox's scheduler for Environment scheduling.

## 26. WAIT_EXPIRED 的 S2 本地模型

S2 不用 network drop 制造 WAIT_EXPIRED。

合法 component test：

```text
request delivered immediately
UPF accepts
CP-CREATE-2 resource commit occurs
UPF endpoint-local fixture delays terminal response generation
OperationService logical wait budget expires
-> C6 WAIT_EXPIRED
later endpoint-local scheduled response is generated
LocalFabric immediately delivers
SMF applies CP-CREATE-3
```

所以：

```text
returned OperationResult.endWorldRevision
  = revision visible at wait deadline

later World.currentRevision
  may be greater

returned WAIT_EXPIRED record
  remains immutable
```

这是 S2-17。

它**不是** S6 response-loss。

S6 必须由真实 Service Fabric DROP 证明。

## 27. Endpoint behavior fixture

`internal/fixture/endpoint_behavior.go` / `internal/upf/behavior.go` 只允许 endpoint-local behavior：

```text
ACCEPT
REJECT(reasonCode)
RESPONSE_AFTER(logical local delay)
RESOURCE_UNAVAILABLE(reasonCode)
```

不允许：

```text
DROP_RESPONSE
SUPPRESS_RESPONSE
REORDER
NETWORK_DELAY
COMMIT_AND_SUPPRESS
UNKNOWN_DISPOSITION
```

“endpoint 花很久才生成 response”与“Fabric 已拿到 response 但在网络边界 delay/drop”必须分开。

## 28. C6 terminal result rules

### COMPLETED

```text
terminal modeled response observed before wait deadline
operation semantic satisfied
endWorldRevision = revision at result emission
```

### REJECTED

```text
backend request dispatched
endpoint explicitly rejects
terminal reject response observed
```

### WAIT_EXPIRED

```text
backend dispatch occurred
no terminal response knowledge before logical deadline
result contains no generic commit truth
```

### INVALID_PRESTATE

```text
request accepted at contract/world level
semantic pre-state prevents dispatch
no protocol transaction
no world mutation from this invocation
```

## 29. Concurrency

### 29.1 Store synchronization

Store 必须支持并发 read，但 domain publish原子：

```text
Snapshot
  -> RLock / equivalent

Commit / Reset
  -> exclusive lock
```

实现不要求锁名，但行为必须能通过 `go test -race`。

### 29.2 Subject reservation by state

S2 不引入分布式锁或隐式 global request dedupe。

Create 的第一次 commit：

```text
ABSENT -> CREATING
```

本身就是 subject reservation。

第二个 concurrent create看到：

```text
session already exists
-> INVALID_PRESTATE
-> NOT_DISPATCHED
```

Release：

```text
ESTABLISHED -> RELEASING
```

同理阻止第二个 release。

### 29.3 TOCTOU

Pre-state判断与第一个 reservation commit必须在同一个 Store commit临界区内重新验证。

禁止：

```text
Snapshot says absent
unlock
send PFCP
another operation commits
first operation still dispatches using stale pre-state
```

正确：

```text
Commit:
  re-check current state
  transition to CREATING/RELEASING/DELETING
  publish
then dispatch
```

## 30. Reset 与异步 callback

每个 backend procedure / PFCP message / endpoint-local scheduled callback携带：

```text
worldRef
worldGeneration
backendOperationRef / transactionRef as relevant
```

callback commit时必须再过 Store fence。

因此：

```text
reset
-> old delayed response arrives
-> SMF attempts commit with old generation
-> rejected
-> new world unchanged
```

不能只靠“scheduler应该已经 cancel了”保证安全。

## 31. Wall-clock 禁令

下列 production owner-local package 不允许让 wall clock决定业务结果：

```text
world
fact
operation
smf
upf
pfcp
endpoint
scheduler consumer seam
```

禁止 authoritative path 使用：

```go
time.Now()
time.Sleep()
time.After()
time.NewTimer()
```

日志时间戳如果未来需要，必须与 domain/scheduler ordering分离；S2 不需要。

建议加 architecture test/grep 作为 repository Gate。

## 32. Legacy migration rule for S2

旧 `ca-sandbox/simulator` 可以作为 characterization source，不作为代码模板。

### KEEP semantics

```text
per-world/run state isolation
deep-copy seeded state
concurrency protection
validate/precondition before mutation
returned object cannot mutate stored state
deterministic fixture behavior
```

### CHANGE

```text
generic map[string]interface{}
  -> typed domain/contract structs

one Run god object
  -> world/fact/operation/smf/upf/pfcp packages

generic Outcome
  -> C6 resultCode + backendEffectDispatch + Runtime-owned Outcome later
```

### MOVE OUT

```text
fault receipt / network response suppression
  -> Service Fabric / intervention owners

Environment lifecycle
  -> Sandbox/Lab

Runtime reconcile policy
  -> ca-runtime
```

### DROP

```text
pendingMutation.UnknownDisposition
StateMutation
ResponseSuppressed
time.Now / timer based authoritative fault behavior
simulator-owned OUTCOME_UNKNOWN
```

## 33. S2 Component Composition

`internal/testkit/composition.go` 提供唯一标准 S2 component assembly：

```text
SeedSpec
  -> world.Store

world.Store
  -> fact.Reader

TestScheduler
  -> scheduler.Port

endpoint.Registry
  <- smf.Controller
  <- upf.Endpoint

ImmediateLocalFabric
  -> endpoint.Registry

smf.Controller
  -> world.Store
  -> pfcp
  -> FabricPort
  -> SchedulerPort

upf.Endpoint
  -> world.Store
  -> pfcp
  -> FabricPort
  -> SchedulerPort
  -> EndpointBehavior

operation.Service
  -> world.Store
  -> smf.Controller / exact cleanup path
  -> SchedulerPort
  -> RefFactory
  -> operation.Journal
```

所有 S2-10～17 使用这套 composition，禁止每个 test 自己拼一套语义不同的 fake。

## 34. S2 Test Naming

Required acceptance test名称稳定使用：

```text
TestS2_01_ResetFencesOldGeneration
TestS2_02_AtomicCommitAdvancesRevisionOnce
TestS2_03_PartialEffectsUseSeparateCommits
TestS2_04_SeedIsDeterministicAndIsolated

TestS2_05_RegistrationFoundSourceFact
TestS2_06_PduSessionKnownAbsent
TestS2_07_HistoricalRevisionUnavailable
TestS2_08_PfcpResourceMultiplicityPreserved
TestS2_09_OrdinaryReadCannotElevateAccess

TestS2_10_CreateCompletesThroughLocalPfcpPath
TestS2_11_CreateConflictingResourceInvalidPrestate
TestS2_12_ExactCleanupAndAlreadyAbsentNoop
TestS2_13_StaleGenerationAndRevisionFailBeforeDispatch
TestS2_14_CallerCorrelationDoesNotDeduplicateBackendOperation

TestS2_15_DeliveredPfcpEstablishmentCommitsResource
TestS2_16_EndpointRejectHasNoSuccessfulPfcpResource
TestS2_17_WaitExpiryDoesNotStopBackendProgress
```

辅助 tests 可以自由增加，但这些名字作为 acceptance mapping 保持稳定。

## 35. S2 Case → Package → Test → Evidence

|Case|主要 package|Required test|必须保存的关键 evidence|
|---|---|---|---|
|S2-01|`world`|`TestS2_01_ResetFencesOldGeneration`|before/after Handle；old-generation Commit error；new state unchanged|
|S2-02|`world`|`TestS2_02_AtomicCommitAdvancesRevisionOnce`|multi-field before/after snapshot；revision +1|
|S2-03|`world`|`TestS2_03_PartialEffectsUseSeparateCommits`|two commit results；two revisions；intermediate snapshot|
|S2-04|`world/fixture`|`TestS2_04_SeedIsDeterministicAndIsolated`|two canonical state snapshots/digests；mutation-isolation assertion|
|S2-05|`fact`|`TestS2_05_RegistrationFoundSourceFact`|FactReadResult + SourceFact + unchanged revision|
|S2-06|`fact`|`TestS2_06_PduSessionKnownAbsent`|KNOWN_ABSENT SourceFact；no fake value|
|S2-07|`fact`|`TestS2_07_HistoricalRevisionUnavailable`|AT_REVISION request/result；no fallback to current|
|S2-08|`fact`|`TestS2_08_PfcpResourceMultiplicityPreserved`|count=1 and >1 results；stable ordered distinct refs|
|S2-09|`fact`|`TestS2_09_OrdinaryReadCannotElevateAccess`|ordinary/evaluator pair；negative elevation proof|
|S2-10|`operation/smf/upf`|`TestS2_10_CreateCompletesThroughLocalPfcpPath`|OperationResult；3 commit revisions；tx ref；final session/resource facts|
|S2-11|`operation/world`|`TestS2_11_CreateConflictingResourceInvalidPrestate`|INVALID_PRESTATE；dispatch count=0；resource count unchanged|
|S2-12|`operation/upf`|`TestS2_12_ExactCleanupAndAlreadyAbsentNoop`|first exact deletion tx；second ALREADY_ABSENT；revision unchanged on second|
|S2-13|`operation/world`|`TestS2_13_StaleGenerationAndRevisionFailBeforeDispatch`|acceptance errors；dispatch count=0；before/after world equality|
|S2-14|`operation`|`TestS2_14_CallerCorrelationDoesNotDeduplicateBackendOperation`|same caller refs；two distinct backendOperationRef|
|S2-15|`endpoint/upf`|`TestS2_15_DeliveredPfcpEstablishmentCommitsResource`|request tx；UPF commit result；PFCP SourceFact|
|S2-16|`endpoint/upf/smf`|`TestS2_16_EndpointRejectHasNoSuccessfulPfcpResource`|REJECTED；no PFCP resource；session FAILED_OR_RECOVERY|
|S2-17|`operation/scheduler/smf/upf`|`TestS2_17_WaitExpiryDoesNotStopBackendProgress`|immutable WAIT_EXPIRED；later world revision/facts；journal progression|

## 36. Required Commands

S2 开发循环：

```bash
go test ./internal/world
go test ./internal/fact
go test ./internal/operation
go test ./internal/endpoint ./internal/smf ./internal/upf ./internal/pfcp
```

S2 acceptance focused：

```bash
go test ./internal/world -run '^TestS2_0[1-4]_'
go test ./internal/fact -run '^TestS2_0[5-9]_'
go test ./internal/operation -run '^TestS2_1[0-4]_'
go test ./internal/... -run '^TestS2_1[5-7]_'
```

Repository Gate：

```bash
go test ./...
go vet ./...
```

Concurrency Gate：

```bash
go test -race ./internal/...
```

若当前 host 不支持 race detector：

```text
local run may record ENVIRONMENT_BLOCKED for race gate
but S2 VERIFIED requires a supported CI/host race PASS
```

仍需执行 central layout：

```bash
python3 ../connectionagent/scripts/validate_go_layout.py --require-all
```

实际 workspace 路径按开发环境调整；不要把相对路径脚本化成产品 contract。

## 37. Acceptance Evidence

当设置：

```text
CA_ACCEPTANCE_DIR=<run dir>
```

S2 tests 应通过 `internal/testkit/evidence.go` 记录最小原始证据。

默认普通 `go test` 不要求污染工作树。

建议：

```text
artifacts/acceptance/<run-id>/S2-xx/
  manifest.json
  requests/
  responses/
  domain/
  logs/
  negative/
  cleanup/
```

COMPONENT case 不伪造：

```text
FabricEvent
BoundaryFaultReceipt
Runtime Outcome
Benchmark Verdict
```

这些 owner evidence 在 S3+ 才出现。

## 38. Common Failure / Diagnosis

### revision 多加一次

查：

```text
是否一次 logical commit 被拆成多个 Store.Commit
是否 read/materialization 错误调用 Commit
是否 no-op 仍 bump revision
```

### stale generation 仍能修改新 world

查：

```text
endpoint callback是否保存原 fence
Commit 是否每次重新校验 generation
是否只依赖 scheduler cancel
```

### duplicate PFCP resource 被“修好”成一个

查：

```text
是否以 session key 做 map value 单例覆盖
是否 FactReader 对 resources 去重/first()
是否 cleanup/release 隐式全删
```

### WAIT_EXPIRED 后世界停止推进

查：

```text
OperationService是否 cancel backend work when wait ends
endpoint response generation是否错误绑定 caller context cancellation
journal是否把 wait deadline当 backend cancellation
```

默认语义：

```text
caller/wait knowledge deadline
!= backend cancellation
```

除非未来明确增加 owner cancellation contract。

### WAIT_EXPIRED 被改写成 COMPLETED

查：

```text
是否复用一个 mutable OperationResult pointer
是否 journal 后续完成反写历史 result
```

历史 C6 result必须 immutable。

### endpoint reject 后出现 PFCP resource

查：

```text
UPF commit point是否发生在 rejection decision之前
fixture是否错误用“commit then reject”
```

### test 需要 sleep 才稳定

这本身就是失败信号。

查：

```text
是否绕开 TestScheduler
是否 goroutine ordering没有 logical scheduler/fence
是否用 wall clock 等待异步 callback
```

## 39. S2 Supporting Invariants

除了 S2-01～17，repository tests还必须锁住：

```text
seed deep-copy
snapshot deep-copy
returned SourceFact/result mutation cannot alter Store
read never changes revision
factRef stable for identical concrete material
schemaDigest always sourced from schema.lock
contentDigest matches S0 algorithm
no map iteration affects order
no wall-clock authoritative behavior
production packages do not import testkit
contract structs do not use map[string]any for typed C2/C6 values
```

## 40. S2 Exit Criteria

S2 可在 WORK 标 `VERIFIED` 当且仅当：

```text
S0 remains PASS

internal/contract implemented and fixture round-trip PASS
world Store/Snapshot/Commit/Reset implemented
deterministic seed implemented
FactReader/SourceFact producer implemented
OperationService implemented
operation journal implemented
SMF/UPF/PFCP owner-local endpoint path implemented
TestScheduler implemented
ImmediateLocalFabric implemented
endpoint fixture implemented

S2-01 PASS
S2-02 PASS
S2-03 PASS
S2-04 PASS
S2-05 PASS
S2-06 PASS
S2-07 PASS
S2-08 PASS
S2-09 PASS
S2-10 PASS
S2-11 PASS
S2-12 PASS
S2-13 PASS
S2-14 PASS
S2-15 PASS
S2-16 PASS
S2-17 PASS

go test ./... PASS
go vet ./... PASS
go test -race ./internal/... PASS on supported host
central Go layout PASS
acceptance evidence complete
WORK updated
```

## 41. S2 完成后仍然不代表

即使 S2 VERIFIED：

```text
C1 scheduler integration      NOT VERIFIED
C3 Fabric acquisition         NOT VERIFIED
C4 Network Observation        NOT VERIFIED
C5 boundary fault             NOT VERIFIED
C7 Runtime integration        NOT VERIFIED
C8 evidence closure           NOT VERIFIED
S3+                           still governed by machine-contract ledger
```

尤其：

```text
ImmediateLocalFabric
!= Service Fabric SIMULATED

TestScheduler
!= Sandbox/C1 deterministic scheduler

WAIT_EXPIRED component test
!= response-loss SYSTEM_E2E
```

## 42. S2 明确禁止

```text
复制 legacy Run god object
使用 generic InvocationResult.Outcome
保留 pendingMutation / UnknownDisposition
simulator自己 suppress/drop response
LocalFabric 支持 protocol fault
用 wall clock决定 endpoint/result
把 TestScheduler 升级成 C1 schema
把 private FabricPort DTO 升级成 C3 schema
FactReader 直接读可变 Store map
read 推进 revision
reset 靠 cancel 而不做 generation fence
duplicate resource自动去重
PDU_SESSION_RELEASE 顺手清掉全部 duplicate resources
OperationService按 caller requestId dedupe
WAIT_EXPIRED携带 committed/notCommitted/retrySafe
异步完成后重写历史 OperationResult
为了 S2 提前发明进程 transport/readiness
```

S2 的成功标准是：

> **在没有真实 Sandbox/Fabric/Runtime 的情况下，env-5gc-sim 自己拥有的 domain state、fact/read、operation 与 endpoint commit 语义已经确定、可并发验证、可 reset、可复现，并且后续跨仓 adapter 只能“接上去”，不能重新解释 owner-local semantics。**


## 42. Shared-Environment subject concurrency note

`worldRevision` is one monotonic revision for the entire materialized world/generation.

It is intentionally **not** a per-UE or per-PDU-Session revision.

Consequences for concurrent Trials:

```text
subject reservation/state
  = scoped by typed subject identity

worldRevision
  = global world snapshot/commit order
```

A caller may use `expectedWorldRevision` only when it truly needs whole-world optimistic concurrency.

Do not make `expectedWorldRevision` a default requirement for ordinary operations on independent subjects:

```text
Trial A / UE-A reads world revision 10
Trial B / UE-B commits -> revision 11
Trial A subject is still valid
```

If Trial A blindly requires revision 10, it gets a false conflict caused by unrelated UE-B activity.

Current Runtime adapter behavior is compatible with this rule: it forwards `expectedWorldRevision` only when explicitly present in invocation arguments.

If future scenarios need subject-local compare-and-swap semantics, add an owner-native subject/session revision contract; do not reinterpret `worldRevision`.
