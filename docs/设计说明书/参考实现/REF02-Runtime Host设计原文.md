> 迁移来源：ca-runtime/docs/design/runtime-host.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# RuntimeHost.v1 机器边界

Status: Accepted  
Version: v1.7  
Date: 2026-09-30

## 1. 定位

`RuntimeHost.v1` 是 `ca-runtime` 对外的稳定机器门面。外部 Host、`tool-mcp-gw`、Console/control adapter 只通过该边界请求 Runtime 能力、执行、查询和显式控制，不依赖 Runtime 内部 package。

```text
Agent Host
  -> tool-mcp-gw
  -> RuntimeHost.v1
  -> ca-runtime

Composition / Lifecycle / Control Adapter
  -> RuntimeHost.v1 query/resolve/control
  -> ca-runtime
```

Agent-facing MCP protocol 不属于 RuntimeHost；它由 `tool-mcp-gw` 适配到 RuntimeHost。

## 2. RuntimeHost 不是什么

它不是：

```text
MCP protocol
Provider API
Sandbox API
Benchmark API
Agent planning API
second execution engine
```

它只是 Runtime/Harness authority 的 public facade。

## 3. 当前与目标核心 surface

当前 Host surface 至少包含以下能力族：

```text
Capability catalog
  GET /api/host/v1/capabilities

Execution
  POST /api/host/v1/executions

Prepared/control material
  POST /api/host/v1/prepared-runs

Skill context compatibility surfaces
  GET  /api/host/v1/skills
  POST /api/host/v1/skills:load
  POST /api/host/v1/references:read

Run inspection/control
  GET  /api/host/v1/runs
  GET  /api/host/v1/runs/{runID}
  GET  /api/host/v1/runs/{runID}/events
  GET  /api/host/v1/runs/{runID}/evidence/material
  POST /api/host/v1/runs/{runID}/actions

Request recovery/control
  GET  /api/host/v1/requests/resolve
  POST /api/host/v1/requests/cancel

Deployment observation
  GET /api/host/v1/provider-bindings

Tool eligibility
  POST /api/host/v1/toolsets/resolve
```

`GET /api/host/v1/provider-bindings` may expose `admittedTargets` under the
versioned `connectionagent.provider-mcp-target/v1` sub-contract. Runtime builds
each target from admitted Provider MCP discovery and includes the governed
binding digest, concrete wire `toolName`, and tool/governed/discovery digests.
It includes the immutable Runtime deployment digest and active execution
profile ref and digest. Consumers must reject absent or mismatched provenance
and resolve a single target before installing an effect-owner control. The
projection excludes MCP endpoints, credentials, and provider inputs.
`admittedTools` remains the capability identity list; it is not a substitute
for wire `toolName`.

An artifact deployment may declare a semantic operation to callable relation
using `operationBindings` on an artifact with no variants, or on each variant
when variants are present:

```json
{
  "operationRef": "operation.file-transfer.prepare@1",
  "callableRefs": ["ca_capability_0123456789abcdef"],
  "subjectRefInputPointers": {
    "ca_capability_0123456789abcdef": ["/receiverImsis", "/senderImsi"]
  }
}
```

The operation ref is owner supplied and opaque to Runtime. Runtime validates
that each callable is in the frozen artifact/variant admission, resolves it
through the same deployment `DispatchPreparer` used at execution, and joins its
exact ToolRef and binding/discovery digests to one admitted Provider MCP target.
The target projection records `artifactRef`, artifact/variant digests, and the
explicit `{operationRef, callableRef}` relations. Optional
`subjectRefInputPointers` explicitly marks callable JSON Pointer paths whose
validated string or string-array values are business subject identities. The
projection is deployment-owned, is included in the deployment digest, and is
exposed with each operation/callable target relation; Runtime does not infer
paths from names or payload shape. At the pre-dispatch binding barrier Runtime
resolves the declared pointers against the actual callable input, rejects
missing, empty, duplicate, or non-string values before Provider dispatch, and
freezes canonical `{authority: connectionagent, type: subject, ref}` values in
dispatch metadata. The Provider MCP transport emits those values as
`connectionagent/subjectRefs`. When no projection is declared, existing
Provider MCP metadata is unchanged. Execute requests do not accept caller- or
Benchmark-supplied subject refs.

A missing callable mapping, unadmitted callable, invalid subject pointer, or
zero or multiple matching Provider targets rejects deployment admission.
Engine may resolve the frozen semantic operation against the active artifact
and variant, but a subject-scoped lease must use the same concrete execution
identity values produced by the declared projection; stable logical subject
labels are not interchangeable with IMSIs or other business identifiers.
This projection does not itself prove a Fabric lease match; that requires
cross-repository owner acceptance.

当前 Host machine contract 已实现并验证两项 scoped/exact identity 升级：

```text
TOOL-01 scoped v2
  contractVersion = connectionagent.resolved-ca-toolset/v2
  resolutionScope = AGENT_INSTANCE_BASE | GOAL_EXECUTION
  status = IMPLEMENTED / VERIFIED

Skill Context exact identity
  same /skills:load and /references:read paths
  request/response consume exact RuntimeSkillIdentity directly
  status = IMPLEMENTED / VERIFIED
```

`toolsets/resolve` 的 scoped 语义见 [`resolved-ca-toolset.md`](resolved-ca-toolset.md)。

`skills:load` / `references:read` 的 exact RuntimeSkillIdentity 语义见 [`skill-context.md`](skill-context.md)。

旧 single-scope TOOL-01 v1 已删除；name-only Skill load 仅保留 compatibility，不再定义 Agent-facing target。当前实现状态以 `docs/WORK.md` 与 public machine contract 为准。

## 3.1 Skill Qualification 消费 RuntimeHost

Skill Qualification 不获得第二套 Runtime execution API，也不要求 `runtimeengine` / `runtimeapp` 成为跨仓 library contract。

目标链：

```text
Skill Toolchain
  -> compile / freeze Artifact or Variant
  -> prepare qualification Environment through its owner control plane
  -> select owner-configured Qualification Runtime deployment
  -> POST RuntimeHost.v1 /prepared-runs
  -> ordinary Runtime Authorization / Assurance / ProviderBinding / Outcome / Reconcile
  -> Run / RunEvent / RunEvidenceMaterial
  -> Toolchain assembles QualificationReport
```

关键点：

- Runtime 不因为 caller 是 SQ2 就进入一套弱化或平行的 safety semantics；
- Qualification 使用正常 Runtime deterministic execution authority，环境/Provider 可以是 qualification-specific deployment composition；
- `PreparedRun` 适合 deterministic caller 在不创建 ProductTask 的前提下冻结 Environment 与 execution identity；它不是 TOOL-01 resolver，也不是 Benchmark API；
- Toolchain 的 expected result、case verdict、QualificationReport 不进入 Runtime authoritative Outcome；
- Runtime 只返回 owner facts；Toolchain 根据 frozen case/qualification contract解释这些 facts；
- 不新增 `/qualifications`、不把 `runtimeengine.Qualification` 暴露成跨仓 wire contract；
- 历史 Toolchain 对 `runtimeengine/runtimeapp/runtimebundle/adapter` 的直接 import 属 migration compatibility，不能反向要求这些 package 永久 public。

若某个 SQ1/Agent planning qualification 需要开放式模型循环，该模型循环仍属于 Toolchain/Agent-side qualification harness；只有最终 deterministic execution material 进入 Runtime。

## 3.2 PreparedRun execution limits

`PreparedRun` 是 deterministic caller 的 execution preparation surface。除 Environment selection 外，它允许 caller 提交已经由自己 authority 冻结的**收紧型执行限制**。

Accepted target：

```json
{
  "contractVersion": "connectionagent.prepared-run/v1",
  "...": "...",
  "executionLimits": {
    "maxActions": 1
  }
}
```

语义以 [ADR-0002](../decisions/ADR-0002-prepared-run-execution-limits.md) 为准：

```text
executionLimits absent
  -> effective maxActions = frozen Procedure.MaxActions

executionLimits.maxActions present
  -> require 0 <= requested <= frozen Procedure.MaxActions
  -> effective maxActions = requested
```

规则：

- 只能收紧，不能扩大 admitted Procedure authority；
- 超过 `Procedure.MaxActions` 时 fail closed，不做 clamp；
- `0` 是合法显式值，因此实现必须保留 field presence；
- `executionLimits` 属 request content，参与 request fingerprint；
- same `(host, requestId)` + different limit -> `RUNTIME_HOST_REQUEST_CONFLICT`；
- Runtime owner evidence中的 `executionSummary.budget.maxActions` 必须反映 effective limit；
- caller不能凭自己的 frozen request声称 budget已生效；
- Benchmark/Qualification只允许从 frozen task/case机械映射；
- Browser、model text、MCP Tool input不能提升或覆盖该限制。

边界：

```text
PreparedRun
  -> may narrow execution budget

ordinary /executions
  -> no caller-controlled action budget
```

这样不会把 deterministic evaluation/qualification control扩散到普通 Agent-facing Execute。

当前代码状态（2026-09-22）：

```text
runtimeengine ActionBudget semantics = IMPLEMENTED
PreparedRun.executionLimits wire     = IMPLEMENTED / CONTRACT PASS
M2 consumer cutover                  = remains gated by the other M0/M1-M2 cases
```

因此文档 Accepted 仍不得被误读为 live cross-repository cutover 已完成；RC-M0-05 的 owner contract 已通过，后续 M1-M7 仍需各自的 consumer/live evidence。

Budget stop 的终端语义与 [provider-boundary.md §14](provider-boundary.md) 对齐（ca-runtime#96）：

```text
ordinary budget exhaustion（无 pending / admitted recovery）
  -> HostState = FAILED, run.ended.executionSummary.reasonCode = BUDGET_EXCEEDED

mutation OUTCOME_UNKNOWN 无法权威 resolve
  -> HostState = SAFE_STOPPED, pendingAction 保留, reasonCode 空
  -> budget 若同时耗尽只是并存事实

reconcile NOT_COMMITTED(retry=true) 的 controlled retry 因预算耗尽未 dispatch
  -> HostState = SAFE_STOPPED, reasonCode = BUDGET_EXHAUSTED_PENDING_RETRY
  -> 预算耗尽不授权第二次 dispatch，也不抹去 OUTCOME_UNKNOWN / reconciliation 事实
```

`SAFE_STOPPED` / `OUTCOME_UNKNOWN` 属 Runtime governed result：Host adapter 必须原样映射，不得改写为 generic protocol failure，也不得自行推导 reconcile 或 retry。

## 4. Capability catalog、Base Envelope 与 Goal-scoped Toolset

`GET /capabilities` 返回 Runtime **已经 admission 的 Agent-capable Capability catalog**。它回答“系统有哪些已准入 Capability”，不是某个 AgentInstance/Goal 当前应该看到的最终 Toolset。

公开 metadata 必须足够让 adapter 机械完成必要映射，包括：

```text
stable capability identity
human description
input schema
runtime-owned effect classification
frozen artifact/entrypoint identity where required
```

`tool-mcp-gw` 不允许通过 Tool 名猜 read-only/mutation，也不维护第二份业务 Tool YAML。

TOOL-01 v2 分两层 resolution：

```text
Runtime Capability Catalog
        ↓
AGENT_INSTANCE_BASE
        ↓
AgentInstance Base CA Capability Envelope

Goal + selected/bound Skill / Artifact
+ Base Envelope
+ Context / Profile / Environment / security policy
        ↓
GOAL_EXECUTION
        ↓
Goal-scoped Runtime Resolved Execution Toolset
```

保持：

```text
Host request-visible CA Tools
  ⊆ Goal-scoped Runtime Resolved Execution Toolset
  ⊆ AgentInstance Base CA Capability Envelope
  ⊆ Runtime Capability Catalog

Host request-visible CA Tools
  ⊆ tool-mcp-gw Server Tool Catalog
```

Base Envelope 不依赖未来 Goal 的动态 selected Skill。Goal-scoped Toolset 只有在 Skill/Artifact 已经 Harness-bound 后才能解析。

`SkillContract.allowedResources.capabilities` 是 Goal Toolset 的结构化上限输入之一，不等于模型最终可见 Tool 列表。

禁止：

```text
GET /capabilities -> treat as model-visible Tool list
Goal text -> permission expansion
LLM Skill selection -> permission expansion
PreparedRun side effect -> Toolset resolution
Host/tool-mcp-gw local eligibility authority
previous Goal Toolset fallback
```

详细 request/response、digest 和 fail-closed 规则见 [`resolved-ca-toolset.md`](resolved-ca-toolset.md)。

## 4.1 vNext：GOAL_PLANNING read-scope resolution

当前 VERIFIED scoped machine contract 只有：

~~~text
AGENT_INSTANCE_BASE
GOAL_EXECUTION
~~~

Planning V2 需要在两者之间增加一个新的 Runtime/Harness-owned scope：

~~~text
GOAL_PLANNING
~~~

原因：

~~~text
selected RuntimeSkillIdentity 已确定
planning 需要 governed current facts
execution Artifact / Variant 尚未 bind
因此 GOAL_EXECUTION 尚不存在
~~~

目标输入：

~~~text
selected RuntimeSkillIdentity
Goal / ProductTask planning identity/material
AgentInstance Base Envelope
Environment / policy / implementation compatibility
Skill semantic resource upper bound
~~~

目标输出：

~~~text
Goal-scoped Runtime Resolved Planning Read Set
  only read-only / inspect Capability refs
  no mutation capability
  stable ref/revision/digest
  resolution provenance
~~~

该 set 必须满足：

~~~text
GOAL_PLANNING
  ⊆ AGENT_INSTANCE_BASE
  ⊆ Runtime Capability Catalog
~~~

Host 只能把它与 tool-mcp-gw Server Tool Catalog / Host support / local narrowing 机械求交后交给 deterministic Context Loader。它**不是**模型默认可见的 Tool registry。

Context Loader 的实际 read 仍走 ordinary Runtime governed Capability execution/read path，因此：

~~~text
GOAL_PLANNING resolution
  != second execution engine
  != ProviderBinding bypass
  != direct fact-owner access
~~~

Runtime 继续拥有 read Capability admission、Provider/ObservationSource binding 与 governed ToolResult projection。

Semantic Chooser 的 ContextOffer / NEED_CONTEXT 完全属于 Host planning orchestration；Runtime 不解析这些对象。Runtime 只负责：
1. 解析 GOAL_PLANNING eligibility；
2. 执行被 Host 选择的已准入 read-only Capability；
3. 返回 governed owner result。

当前 machine schema/API 尚未实现 GOAL_PLANNING；在 Runtime owner contract / tests 完成前保持 implementation OPEN，不得由 Host 自造本地 scope schema 冒充 Runtime authority。

## 5. Tool visibility、Skill context 与 execution authorization

三个概念必须分开：

```text
Skill model context
  = 模型关于 selected frozen Skill 的指导材料

request-visible execution Tools
  = 当前 Goal 模型可以考虑调用的 CA Tool schemas

per-call execution authorization
  = 某次实际 Tool Call 是否允许继续执行
```

Skill routing/load：

```text
owner-native SkillEligibilityDecision
  -> model selects canonical SkillCatalogEntry
  -> Host normalizes to exact RuntimeSkillIdentity
  -> POST /skills:load v2
  -> RuntimeHost owner-native load result
  -> selected Runtime Bundle SKILL.md injected into later model input
```

随后 execution preparation：

```text
selected RuntimeSkillIdentity
+ planning / optional Variant decision
  -> Harness binds exact execution Artifact / Variant
  -> TOOL-01 GOAL_EXECUTION
  -> Goal-scoped Toolset
```

Goal-scoped Tool visibility：

```text
Host request-visible CA Tools
  = Goal-scoped Runtime Resolved Execution Toolset
    ∩ tool-mcp-gw Server Tool Catalog
    ∩ Host-supported subset
    ∩ optional Host-local least-privilege narrowing
```

执行时仍再次通过 Runtime admission / Authorization / Assurance / binding / dispatch。

因此：

```text
RuntimeHost Skill load result != model actually saw it
skill/injected proof != Tool permission
visible Tool != automatically executable Tool
tool-mcp-gw tools/list != request-visible execution Tool catalog
```

execution binding 必须证明 bound Artifact/Variant 与 selected RuntimeSkillIdentity 的 Release/Runtime Bundle lineage 兼容。

## 6. Execute request

Host 只能提交 Runtime public contract 允许的执行材料，例如：

```text
requestId
artifactDigest / admitted capability identity
entrypoint
variantDigest? where applicable
input
Host-owned correlation (host / callId / turnId / rootCallId / parentTaskRef / proposal provenance / skill-load provenance)
```

Host 不提交：

```text
Context selection (contextRef)
Environment selection (environmentRef / environmentSelection / contextDefaultEnvironmentRef)
Benchmark identity (evaluationTaskRef)
generic subjectRef as universal correlation
execution governance selection (profile / controlMode); the Runtime deployment activeProfile owns it
ExecutableProcedure internals
ProviderBinding
Authorizer/Assurer override
Predicate result
Outcome
Reconcile policy
Runtime-private program counter
```

Runtime 自己完成 resolve、admission、Authorization/Assurance、binding 和 execution。Environment/execution-profile 由 Runtime deployment configuration 拥有（见 §6.2 与 [`runtime-execution-profile.md`](runtime-execution-profile.md) §8.1）。

即使 Host 曾经看到过某个 Tool，也不能用该事实绕过当前 Runtime eligibility 或 per-call execution Gate。

### 6.1 Governed Tool result projection

Agent-facing read-only Capability 必须把**实际读取结果**返回给 Host，而不能只返回“执行成功”摘要。RuntimeHost v1 通过：

```text
ExecuteResult.invocations[].result
```

承载 Runtime 已接收并允许作为 Tool result 的 governed payload。该字段来自当前 invocation 的 `ProviderKnowledge.Content`，保持 JSON 机器结构；例如 reference simulation 的 C2 read 可以返回 owner-native `FiveGCSimFactReadResult` / ordinary `FiveGCSimSourceFact`，随后由 `tool-mcp-gw` 原样作为 Runtime ExecuteResult 的一部分映射到 MCP `StructuredContent`。

这不等于开放 Provider 内部状态。Host projection 继续禁止暴露：

```text
Provider evidence collection
transport failure diagnostics
ProviderBinding / credentials / endpoint internals
Runtime private program counter
Reconcile private state
evaluator-only Source Fact
```

是否允许某份 owner payload进入 `result` 仍由具体 admitted Provider adapter负责；例如 `fivegcsim` adapter 在产生普通 read result 前会拒绝 `EVALUATOR_ONLY` SourceFact。

因此：

```text
Tool succeeded
!= Agent learned the requested state

Agent-readable state
= successful Runtime invocation
  + governed invocation.result payload
```

### 6.2 execution profile / execution binding

RuntimeHost 支持两个 Runtime-owned、Benchmark-neutral 的 execution governance profile：

```text
GOVERNED  (default)
DIRECT
```

canonical activation 是 **deployment-owned**（[`runtime-execution-profile.md`](runtime-execution-profile.md) §8.1）：

```text
RuntimeArtifactDeployment.spec.executionProfiles.activeProfile = GOVERNED | DIRECT
```

ordinary Execute/PreparedRun 不携带 governance selection：request 只有 request identity 与 executable identity。Runtime 从自己的 deployment configuration 解析 effective profile，绝不从裸 profile 字符串或 caller-supplied binding 打开 DIRECT。request-level execution binding 已 REMOVED（见 [`runtime-execution-profile.md`](runtime-execution-profile.md) §18 historical）。

Host 边界保持：

```text
Runtime owns execution-profile admission resolution and the active profile.
tool-mcp-gw/RuntimeHost 只机械承载 compatibility binding（canonical 不再生产）。
absent binding -> deployment activeProfile（默认 GOVERNED）。
```

## 7. Identity

### requestId

```text
logical request identity = (host, requestId)
```

`requestId` 是 Runtime durable execution idempotency identity。它不是 callId、JSON-RPC id、MCP session id、MCP task id 或 HTTP connection id。

### runId

`runId` 是 Runtime authoritative execution identity。原始 Execute response 与后续 Run current state 是不同问题。

### baseEnvelopeDigest

```text
baseEnvelopeDigest
  = AgentInstance long-lived CA capability compatibility identity component
```

它随会改变 AgentInstance capability upper bound 的 Profile/System/Environment/security/admission facts 变化。

### goal-scoped toolsetDigest

```text
toolsetDigest
  = one Goal execution Toolset identity
  != AgentInstance reuse identity
```

不同 Goal/selected Skill 可以有不同 toolsetDigest，同时复用同一个兼容 AgentInstance。

### RuntimeSkillIdentity

复用 ca-skill-toolchain machine contract：

```text
skillName
version
releaseId
runtimeBundleDigest
profile identity
```

它是 Skill context load 的 immutable identity。Host 从 frozen SkillCatalogEntry 归一化得到它，模型不手工提供 releaseId/digest。

### LoadedSkillSnapshot / contentHash

复用 ca-skill-toolchain machine contract，证明 Loader 取得了哪一个 RuntimeSkillIdentity 的 frozen model context；`skill/injected` 或 ModelInput refs 再证明内容真正进入模型输入。

### execution binding identity

后续 Harness-bound Artifact/Variant 是另一层 identity。它必须与 selected RuntimeSkillIdentity lineage-compatible，但不是 Skill context load 的前置条件。

### operationRef

只在 Prepared Run 或显式 control contract 需要时使用高层 operationRef；普通 capability Execute 不因为外部使用 MCP 就新增强制 operationRef。

## 8. RequestStore / replay

Runtime owns durable request lifecycle：

```text
ABSENT -> CLAIMED -> COMPLETED
ABSENT -> SEALED_BEFORE_START
```

同一 `(host, requestId)`：

```text
same normalized request
  -> wait / reconstruct / replay original response
  -> no second Provider dispatch

different request
  -> conflict / fail closed
```

Replay 回答“原 Execute 的逻辑结果是什么”；Run query 回答“当前 authoritative Run 状态是什么”。二者不能混用。

Toolset resolver 不进入 RequestStore mutation lifecycle。

## 9. request resolve

`requests/resolve` 用原始 request identity 恢复 transport uncertainty。

典型知识状态：

```text
unknown / absent knowledge
claimed / in-flight
completed / terminal result available
sealed-before-start
```

具体 wire vocabulary 以 owner contract 为准；外部 adapter 不通过 timestamp、payload similarity 或新 requestId 猜测原调用。

## 10. Transport lifecycle

Runtime 必须坚持：

```text
caller wait lifecycle
!= Runtime business execution lifecycle
```

尤其 mutation 已 claim 并可能越过 dispatch barrier 后，HTTP/MCP client disconnect 不得自动停止：

```text
Provider result handling
Outcome / OUTCOME_UNKNOWN
Reconcile
Run/Event persistence
RequestStore completion
```

业务 cancellation 只能通过显式 Runtime control contract。

## 11. Host RESULT_UNKNOWN

`tool-mcp-gw`/Host 没拿到确定 Runtime response时，可以形成 Host-side `RESULT_UNKNOWN`。

```text
Host RESULT_UNKNOWN
!= Runtime OUTCOME_UNKNOWN
```

RuntimeHost transport failure不能推出 Provider 未提交、Runtime FAILED 或 safe retry。

## 12. tool-mcp-gw / Host 映射

`tool-mcp-gw` 的机械映射：

```text
MCP Server Tool Catalog <- RuntimeHost admitted Capability catalog
MCP tools/call          -> RuntimeHost Execute
transport uncertainty   -> original requestId + resolve/recovery
```

AgentInstance/client preparation：

```text
TOOL-01 AGENT_INSTANCE_BASE
  -> Base Envelope
  -> materialize/reuse AgentInstance
  -> tool-mcp-gw initialize/tools-list
  -> cache Server Tool Catalog
```

每个动态 Goal：

```text
SkillCatalogSnapshot
  -> SKILL_ROUTING model choice
  -> exact RuntimeSkillIdentity
  -> RuntimeHost Skill Context v2 load
  -> LoadedSkillSnapshot
  -> selected Skill context injected
  -> planning / optional Variant choice
  -> Harness binds execution Artifact / Variant
  -> TOOL-01 GOAL_EXECUTION
  -> Goal-scoped Toolset

Host
  -> intersect Goal-scoped Toolset with cached Server Catalog
  -> execution ModelInput contains selected Skill context + exact Tool schemas
```

`tool-mcp-gw` 不参与 Skill Catalog/Context loading，也不拥有 Skill selection/binding authority。RuntimeHost context surface 不因此成为 Skill eligibility owner。

## 13. Error boundary

必须区分：

```text
invalid RuntimeHost request
Toolset resolution scope/input invalid
Base Envelope mismatch
Goal execution binding invalid

Skill selection invalid / ambiguous       # Host selection normalization
Skill release/catalog mismatch             # RuntimeSkillIdentity fence
Skill context identity mismatch            # RuntimeHost context materialization
Skill context unavailable
Skill execution-lineage binding failed     # later Harness binding
Skill reference identity mismatch
Skill reference not found

Tool/capability not eligible in current Goal-scoped Toolset
request identity conflict
operation sealed before start
Runtime composition unavailable/internal failure
Runtime governed result
transport result unavailable to caller
```

Toolset/context identity 无法机械证明时都必须 fail closed：

```text
no full catalog fallback
no latest Skill-by-name fallback
no previous Goal Toolset fallback
no current Skill source reconstruction
```

`DENIED`、`SAFE_STOPPED`、`NEEDS_DECISION`、Runtime `OUTCOME_UNKNOWN` 等 governed result 不应被 adapter 改写成 generic protocol crash。

## 14. 不变量

```text
RuntimeHost is the public Runtime machine boundary.
tool-mcp-gw maps MCP to RuntimeHost; Runtime does not own MCP protocol.
Skill SQ2 consumes ordinary RuntimeHost PreparedRun/execution facts; Runtime does not expose a second Qualification execution engine.

Runtime/Harness owns authoritative ConnectionAgent capability eligibility.
GET /capabilities is a catalog, not model-visible authority.
TOOL-01 v2 currently separates AGENT_INSTANCE_BASE from GOAL_EXECUTION.
vNext adds GOAL_PLANNING between selected Skill load and execution binding; current implementation remains OPEN until owner machine contract lands.
GOAL_PLANNING is read-only and cannot grant mutation authority.
baseEnvelopeDigest participates in AgentInstance compatibility.
goal-scoped planning-read digest and execution toolsetDigest are Goal-scoped identities, not AgentInstance reuse identity.

Consume owner-canonical SkillCatalogEntry directly for routing candidates.
Consume Toolchain RuntimeSkillIdentity directly for Skill load identity.
RuntimeHost returns an owner-native load result; no loaded-context projection is required.
Skill selection is not Skill context loading.
Name-only Skill lookup is compatibility behavior, not the target Host contract.
Skill context load may occur before execution Artifact/Variant binding.
Later execution binding must be lineage-compatible with selected RuntimeSkillIdentity.
On-demand reference reads must remain fenced to the same RuntimeSkillIdentity.

Host-visible execution CA Tools = Goal-scoped Toolset ∩ tool-mcp-gw Server Catalog ∩ Host/local narrowing.
Host may narrow but never widen Runtime/Harness eligibility.
Tool visibility does not imply per-call authorization.

External callers never submit ProviderBinding or authoritative Outcome.
requestId owns logical request replay identity.
replay != current Run query.
transport disconnect != business cancellation.
Host RESULT_UNKNOWN != Runtime OUTCOME_UNKNOWN.

Execution governance profile is Runtime-owned, versioned and Benchmark-neutral: GOVERNED | DIRECT.
An empty deployment activeProfile preserves GOVERNED behavior exactly.
DIRECT is never opened by a caller-supplied profile string.
Tool visibility and execution governance are independent axes.
DIRECT reuses the Runtime ProviderBinding/transport authority and never duplicates it.
DIRECT never executes Procedure/Predicate/Assurance/Reconcile/retry/compensation.
```
