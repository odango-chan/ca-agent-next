> 迁移来源：ca-agent/docs/design/agent-task-machine-contracts.md  
> 固定源提交：447d0cce7e42c7c1184b11fb2563792eead68d51  
> 原始状态：TARGET01 Go Host 当前设计/契约；仅作为后续晋级目标参考。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# ca-agent ProductTask v2 Go Implementation Profile

**Status: Accepted**  
**Version: v1.2**  
**Date: 2026-09-23**  
**Owner: ca-agent**  
**Shared contract owner: connectionagent**  
**Applies to: AG-M1 through AG-M4**

本文只定义 ca-agent 作为被选中的 Go Agent Host 时，如何实现 shared ProductTask v2。

Shared semantic / machine authority：

~~~text
connectionagent/docs/design/product-task-v2.md
connectionagent/contracts/schemas/product-task-v2.schema.yaml
connectionagent/contracts/schemas/task-relation-v1.schema.yaml
connectionagent/contracts/schemas/external-input-request-v1.schema.yaml
connectionagent/contracts/schemas/task-resource-claim-v1.schema.yaml
connectionagent/contracts/schemas/agent-continuity-v1.schema.yaml
~~~

本文不得改写上述 lifecycle、attention、CANCEL、relation、input、resource、continuity 语义。ca-dsh / ca-nanobot 是并列实现，不依赖本仓 Go API。

---

## 1. Current baseline

当前代码是 ProductTask v1：

~~~text
contractVersion = connectionagent.product-task/v1

LifecycleState:
  ACCEPTED
  RUNNING
  COMPLETED
  FAILED
  ATTENTION
  UNKNOWN

Actions:
  EXECUTE
  REPEAT

AttentionState:
  one string
~~~

当前 durable store：

~~~text
ProductTaskStore
  mutex
  one JSON ledger file
  tasks[]
  idempotency maps
  operation receipt maps

persist:
  marshal whole ledger
  -> write .tmp
  -> atomic rename
~~~

这一基础非常适合 v2 first slice：继续保持一个 owner-local atomic ledger，不引入数据库或四套独立持久化系统。

---

## 2. Target Go public surface

新增 v2 Go types，命名与 shared contract一一对应：

~~~text
ProductTaskV2
TaskAttention
TaskActionDescriptorV2
TaskRelation
ExternalInputRequest
TaskResourceClaim
AgentContinuityRecord
~~~

ProductTaskV2：

~~~text
ContractVersion = connectionagent.product-task/v2

LifecycleState:
  ACCEPTED
  RUNNING
  COMPLETED
  FAILED
  CANCELLED
  UNKNOWN

Attention []TaskAttention

Action:
  EXECUTE
  REPEAT
  CANCEL
~~~

当前 ProductTask v1 type在 compatibility gate关闭前保留，但不再作为新语义 authority。

Host-specific：

~~~text
ProposalSnapshots
raw model/planning material
Skill load transport material
other Go review material
~~~

继续保留在 Go owner-native trajectory/material 中；不要为了 ProductTask v2 schema 把它们硬塞进 shared core。

### 2.1 Canonical v2 ingress 是 deployment-neutral

~~~text
caller -> POST /api/v2/tasks
  { operationRef, intent, sourceTaskRef?, skillEligibilityDecisionRef? }

Platform / preparation plane
  resolves Context / Environment
  -> materializes Host effective config
       effective model / Tool Base envelope / Skill config / MCP endpoint
       effective capability set / effective profile / implementation identity
  -> starts ca-agent
~~~

- canonical ProductTask aggregate 不携带 `contextRef`/`environmentRef`/
  `environmentSelection`/`requestedAgentProfileRef`/`controlMode`；这些只在
  v1 COMPATIBILITY 的 `LegacyProductTaskFields` carrier 中保留，且不会进入
  canonical `/api/v2/tasks` executor（connectionagent#44）。
- canonical model input 只有 `{intent, tools, observation}`；deployment/
  Benchmark identity 不得进入 model request。
- Tool session 只依赖 `taskRef`/`AgentInstanceRef` + Host effective Tool
  surface/config + MCP endpoint。
- Skill eligibility 保留计算/policy/candidate validation，但消费 deployment
  materialize 的 effective capability set，而不是跨 owner `environmentRef`
  或 Environment owner lookup。
- AgentInstance reuse compatibility 由 `profileRef`/`implementationRef`/
  `effectiveConfigDigest`/Base Envelope digest/MCP client generation 决定，
  不再使用 `environmentRef`。

### 2.2 Authenticated material detail causal refs

`ca-agent.product-task.material-detail/v2` is the authenticated read-only
projection of the Host's private model/Tool material. It retains the exact
causal edges written by the canonical executor:

```text
ModelInteraction.responseRef
  -> selectedToolCallRequestRefs[]
  -> ToolCall.requestId
  -> toolResultSourceRequestRefs[] on the consuming ModelInteraction
  -> ModelInteraction.requestRef
  -> ProductTaskExecutionMaterial.finalResponseRef
```

The arrays contain opaque owner refs, never tool names or locally derived
IDs. The first edge is recorded only after the selected model decision invokes
the Host Tool session and receives its `requestId`; the second is recorded
only when the captured next ModelInteraction request contains that Tool
result. `finalResponseRef` names the ModelInteraction response that produced
the owner `final` field. Missing refs remain absent. Consumers must not
reconstruct these relationships from material array order, timestamps, names,
or payload equality. The v1 detail projection remains decodable as historical
material without these correlation guarantees.

---

## 3. Go ledger v2

目标仍是一份 owner ledger：

~~~text
productTaskLedgerV2 {
  contractVersion

  tasks[]
  relations[]
  externalInputRequests[]
  resourceClaims[]
  continuities[]

  submitIdempotency
  operationReceipts
  enqueueSequences
}
~~~

建议 ledger identity：

~~~text
connectionagent.ca-agent-product-task-ledger/v2
~~~

所有 Task-domain mutation继续：

~~~text
lock one mutex
 -> load/validate
 -> apply all related typed changes in memory
 -> marshal complete v2 ledger
 -> write temp
 -> atomic rename
 -> ack
~~~

因此 crash-consistency 不需要新增通用数据库 transaction framework。

禁止拆成：

~~~text
tasks.json
relations.json
inputs.json
claims.json
~~~

然后分别 best-effort 写入。

未来若 ledger 规模需要数据库，再以行为等价替换 persistence；不是 AG-M1 first slice。

---

## 4. v1 -> v2 migration

loader 必须识别 legacy v1 ledger。

迁移规则严格服从 shared ProductTask v2 §13。

### 4.1 direct states

~~~text
ACCEPTED  -> ACCEPTED
RUNNING   -> RUNNING
COMPLETED -> COMPLETED
FAILED    -> FAILED
UNKNOWN   -> UNKNOWN
~~~

### 4.2 legacy ATTENTION

如果 durable owner material 能机械证明 ATTENTION 前 lifecycle：

~~~text
restore proven lifecycle
+ emit corresponding v2 TaskAttention
~~~

不能证明时：

~~~text
LifecycleState = UNKNOWN
Attention += {
  Kind: RECOVERY_REQUIRED
  Code: LEGACY_ATTENTION_STATE
}
~~~

AttentionState 原字符串可作为 summary/provenance保留。

禁止：

~~~text
legacy ATTENTION -> ACCEPTED by default
legacy ATTENTION -> RUNNING by default
~~~

### 4.3 persistence cutover

首次成功 migration 必须通过 v2 ledger atomic replace持久化。

若需要保留 rollback artifact，只保存 legacy bytes/digest 作为 migration evidence/backup，不继续成为 writable authority。

---

## 5. v1 compatibility view

在 replacement-before-delete gate完成前，现有 /api/v1 可以作为 v2 owner state 的 compatibility projection。

固定：

~~~text
v2 attention empty
  -> render corresponding v1 lifecycle when representable

v2 attention non-empty
  -> legacy read may render lifecycleState=ATTENTION
     AttentionState=governed compatibility summary

v2 CANCELLED
  -> legacy read renders UNKNOWN
     AttentionState=TASK_CANCELLED_V2_COMPAT
     no EXECUTE action
~~~

这是 legacy view，不得写回成为 authority。

v1 mutation endpoint只允许机械翻译仍有无损 v2语义的旧 action。新 CANCEL 只通过 v2 surface 暴露。

v1 compatibility删除必须等所有已知 consumer迁移完成。

---

## 6. v2 HTTP surface

由于 ProductTask wire semantics有 breaking change，v2使用独立 API version。

目标：

~~~text
POST /api/v2/tasks
GET  /api/v2/tasks/{taskRef}
POST /api/v2/tasks/{taskRef}/actions

POST /api/v2/tasks/{parentTaskRef}/children
GET  /api/v2/tasks/{taskRef}/relations

POST /api/v2/tasks/{taskRef}/external-input-requests
GET  /api/v2/tasks/{taskRef}/external-input-requests
POST /api/v2/external-input-requests/{requestRef}/answer
POST /api/v2/external-input-requests/{requestRef}/cancel

POST /api/v2/tasks/{taskRef}/resource-claims
GET  /api/v2/tasks/{taskRef}/resource-claims
POST /api/v2/resource-claims/{claimRef}/release
POST /api/v2/resource-claims/{claimRef}/cancel

POST /api/v2/tasks/{taskRef}/continuities
GET  /api/v2/tasks/{taskRef}/continuities
~~~

read responses必须能机械投影到 canonical connectionagent schemas。

---

## 7. Common mutation / error contract

Go HTTP API继续使用：

~~~text
operationRef
expectedRevision
canonical request digest
~~~

行为：

~~~text
same operationRef + same digest
  -> same result

same operationRef + different digest
  -> OPERATION_CONFLICT

stale expectedRevision
  -> REVISION_CONFLICT
~~~

Go API error code：

~~~text
INVALID_ARGUMENT
NOT_FOUND
REVISION_CONFLICT
OPERATION_CONFLICT
PRECONDITION_FAILED
ALREADY_TERMINAL
RESOURCE_CONFLICT
INCOMPATIBLE_AGENT_INSTANCE
INTERNAL_ERROR
~~~

HTTP：

~~~text
400 INVALID_ARGUMENT
404 NOT_FOUND
409 REVISION_CONFLICT
409 OPERATION_CONFLICT
409 ALREADY_TERMINAL
409 RESOURCE_CONFLICT
409 INCOMPATIBLE_AGENT_INSTANCE
412 PRECONDITION_FAILED
500 INTERNAL_ERROR
~~~

409/412应返回当前 ref/revision when available。

---

## 8. AG-M1 — ProductTask v2 core + TaskRelation

AG-M1 先完成 v2 core，不直接跳到 child orchestration。

### 8.1 core cutover

实现：

~~~text
ProductTaskV2 type
TaskAttention[]
CANCELLED lifecycle
CANCEL action
v1 -> v2 migration
v2 ledger
/api/v2 task create/read/actions
v1 compatibility projection
~~~

CANCEL：

~~~text
non-terminal Task -> CANCELLED
stop fresh Agent/model work
no fresh Runtime mutation

!= Runtime cancel success
!= rollback
!= AgentInstance stop
~~~

### 8.2 TaskRelation

Go ledger中保存 shared immutable TaskRelation：

~~~text
relationRef
parentTaskRef
childTaskRef
spawnRef
ordinal
createdAt
~~~

没有：

~~~text
relation revision
ACTIVE/CANCELLED state
updatedAt
~~~

唯一性：

~~~text
(parentTaskRef, spawnRef)
childTaskRef has at most one parent
~~~

child spawn：

~~~text
1. validate parent v2 expectedRevision
2. parent non-terminal
3. validate spawnRef idempotency
4. create child ProductTaskV2
5. create immutable TaskRelation
6. parent revision +1 because owner relation view changed
7. atomic ledger persist
~~~

### 8.3 no implicit orchestration

first slice明确不做：

~~~text
parent CANCEL -> child CANCEL cascade
child FAILED -> parent FAILED
all children COMPLETED -> parent COMPLETED
~~~

parent CANCEL只取消 parent自身。

---

## 9. AG-M2 — ExternalInputRequest

ExternalInputRequest 存入同一 Go ledger typed collection；不是独立 database/store authority。

OPEN：

~~~text
create request revision=1
ensure at most one OPEN request per task
add TaskAttention {
  Kind: EXTERNAL_INPUT
  SubjectRef: requestRef
  Code: reasonCode
}
ProductTask revision +1
atomic ledger persist
~~~

ProductTask lifecycle不变。

ANSWER：

~~~text
OPEN -> ANSWERED
request revision +1
remove matching EXTERNAL_INPUT attention
ProductTask revision +1
do not change lifecycle
do not execute Runtime
atomic ledger persist
~~~

request CANCEL：

~~~text
OPEN -> CANCELLED
remove matching attention
ProductTask lifecycle unchanged
~~~

Task CANCEL：

~~~text
ProductTask -> CANCELLED
all OPEN ExternalInputRequest for Task -> CANCELLED
atomic same ledger persist
~~~

---

## 10. AG-M3 — TaskResourceClaim

ResourceClaim 仍在同一 v2 ledger，但需要按 conflictKey全局索引/扫描。

first slice：

~~~text
EXCLUSIVE
WAIT | FAIL
one active WAITING/HELD claim per Task
~~~

enqueueSequence：

~~~text
monotonic per Host owner
assigned under same ledger mutex
never timestamp
~~~

acquire：

~~~text
no HELD conflict
  -> HELD

HELD conflict + WAIT
  -> WAITING
  -> add RESOURCE_WAIT attention
  -> ProductTask revision +1

HELD conflict + FAIL
  -> RESOURCE_CONFLICT
  -> no claim object
~~~

Task lifecycle不变。

release/cancel holder：

~~~text
mark old claim terminal
promote lowest enqueueSequence waiter
remove promoted Task RESOURCE_WAIT attention
promoted Task revision +1
atomic ledger persist
~~~

Task CANCEL：

~~~text
WAITING claim -> CANCELLED
HELD claim -> RELEASED/CANCELLED scheduling ownership
promote next waiter if any
do not imply Provider cleanup
~~~

---

## 11. AG-M4 — AgentContinuity

Go ledger保存 immutable AgentContinuityRecord，字段必须能投影 shared AgentContinuity v1 schema。

first slice：

~~~text
same ca-agent implementation
same materialized effective config
same ProductTask
old AgentInstance -> compatible replacement AgentInstance
~~~

不支持切换到 ca-dsh / ca-nanobot。

continuity commit：

~~~text
1. load Task / old instance / new instance
2. validate expected Task revision
3. validate same Go Host implementation
4. validate effective config/Profile/Base Envelope/MCP generation compatibility
5. snapshot existing request/run/input/skill/binding refs
6. append immutable continuity record
7. update resolvedAgentInstanceRef
8. ProductTask revision +1
9. atomic ledger persist
~~~

no replay：

~~~text
known terminal Runtime mutation
  -> preserve refs, never dispatch

Host RESULT_UNKNOWN
  -> same original requestId recovery

known non-terminal Run
  -> owner query/reconcile existing identity

OPEN ExternalInput
  -> same requestRef

ANSWERED
  -> no duplicate prompt
~~~

---

## 12. ActionDescriptor v2

每次 ProductTask revision变化后重新 materialize ActionDescriptors。

baseline：

~~~text
ACCEPTED:
  EXECUTE if Host executor available
  REPEAT
  CANCEL

RUNNING:
  CANCEL
  REPEAT only if product policy explicitly allows new Task recreation

UNKNOWN:
  CANCEL
  REPEAT
  EXECUTE false until recovery

COMPLETED / FAILED / CANCELLED:
  REPEAT
  EXECUTE false
  CANCEL false
~~~

ActionDescriptor只描述 owner允许动作；Console不从 lifecycle自行推按钮。

---

## 13. Schema conformance

ca-agent不复制 connectionagent canonical schema作为新的 authority。

本仓需要 canonical JSON fixtures，workspace/contract gate用 pinned connectionagent schema验证：

~~~text
ProductTaskV2
TaskRelation
ExternalInputRequest
TaskResourceClaim
AgentContinuityRecord
~~~

Go focused tests还必须验证：

~~~text
encode -> canonical field names
decode canonical fixture
invalid lifecycle/attention/state rejected
v1 migration deterministic
unknown JSON / incompatible version fail closed where applicable
~~~

---

## 14. Focused tests

AG-M1：

~~~text
producttask_v2_test.go
producttask_v1_migration_test.go
task_relation_test.go
producttask API v2 contract tests
legacy v1 projection tests
restart/reload tests
~~~

AG-M2：

~~~text
external_input_test.go
multi-attention coexistence
answer does not change lifecycle
Task CANCEL closes OPEN request
stale/duplicate/conflict tests
~~~

AG-M3：

~~~text
task_resource_claim_test.go
FIFO promotion
WAIT attention only
Task CANCEL claim cleanup
Runtime denial still effective
~~~

AG-M4：

~~~text
continuity_test.go
same-host compatibility
cross-host replacement reject
terminal no replay
RESULT_UNKNOWN same requestId
ExternalInput restore
~~~

---

## 15. Forbidden shortcuts

禁止：

~~~text
keep ATTENTION as v2 lifecycle
ExternalInput answer -> ACCEPTED
Resource waiter promotion -> ACCEPTED
TaskRelation ACTIVE/CANCELLED state
implicit parent cancel cascade
one Task hold multiple active resource keys
timestamp waiter ordering
cross ca-agent/ca-dsh/ca-nanobot continuity
four independent JSON files without atomic commit
ProductTask v1 projection becoming writable authority
copy connectionagent schemas and edit them locally
~~~

---

## 16. Implementation order

固定：

~~~text
AG-M0
  Runtime exit gate
  pin shared ProductTask v2 contract ref

AG-M1
  v2 core / migration / ledger / API
  immutable TaskRelation

AG-M2
  ExternalInputRequest + orthogonal attention

AG-M3
  ResourceClaim + orthogonal attention

AG-M4
  same-Go-Host continuity

AG-M5
  ca-agent AHB/HCP + offline evidence

AG-M6
  compatibility/repository cleanup

AG-M7
  final fresh gates
~~~


---

## 17. Concurrent Trial / Goal isolation

当前 AgentInstance 可以在相同：

```text
Profile
Resolved Config
Implementation
Environment
```

下复用。

这只证明 Host process/base binding 可复用，不证明多个 active Goal 可以共享同一个可变 Goal execution state。

当前 scoped MCP Host 的关键 mutable state 包括：

```text
goalRegistry
modelVisible
current Goal toolset
```

并通过 `ReplaceGoalRegistry` 更新。

因此当前能力上限：

```text
same AgentInstance
+ serialized Goals
= supported

same AgentInstance
+ concurrent active Goals/Benchmark Trials
= NOT_VERIFIED / NOT_READY
```

在宣称 concurrent reuse 前必须实现以下之一：

1. per-Task/Goal mutable registry keyed by immutable Task/Goal identity；
2. independent Agent client generation/child execution context per active Trial；
3. exclusive AgentInstance lease per active Trial。

固定不变量：

- Goal-A Toolset/Skill/model context 不得被 Goal-B registry replacement 改写；
- model-visible Tool surface 必须能机械归属一个 Task/Goal；
- Proposal/ModelInput/ModelOutput snapshot 必须绑定 Task/Goal/Trial；
- cancellation/continuity 不能释放另一个 active Trial 的 Goal state。

Benchmark shared-Environment parallelism 不能因为 Environment subject 已隔离，就自动认为 Agent Host 也已隔离。
