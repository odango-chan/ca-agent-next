> 迁移来源：ca-runtime/docs/design/runtime-execution-profile.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# Runtime Execution Profile: GOVERNED 与 DIRECT

Status: Accepted<br>
Version: v1.1<br>
Date: 2026-09-30<br>
Issue: ca-runtime#103 · ca-runtime#105 (deployment-owned active profile)

## 1. 目的

本文冻结 Runtime 的 **execution governance profile** 机器契约，把 Runtime execution surface 正式拆成两条
**Runtime-owned、Benchmark-neutral** 的机械路径：

```text
GOVERNED
DIRECT
```

Benchmark 组合语义因此可以表达成：

```text
LLM_RUNTIME
  = Agent + LLM + CA Tools + GOVERNED Runtime/Harness

LLM_ONLY
  = Agent + LLM + CA Tools + DIRECT Runtime execution
  = 不经过 Harness governance

RUNTIME_ONLY
  = no LLM + GOVERNED Runtime/Harness
```

Benchmark enum 仍然只有：

```text
LLM_RUNTIME
LLM_ONLY
RUNTIME_ONLY
```

禁止新增 `PURE_LLM` / `LLM_DIRECT` / `DIRECT_LLM` 等 Benchmark Mode。

## 2. Benchmark-neutrality

Runtime **不得**接收或分支：

```text
benchmarkMode
LLM_ONLY
LLM_RUNTIME
RUNTIME_ONLY
Case
Trial
Oracle
Verdict
```

Benchmark/Deployment owner 只把 **已经解析并冻结** 的 execution binding 交给 Runtime：

```text
resolvedExecutionProfile = GOVERNED | DIRECT
```

Runtime 不知道为什么选择 DIRECT，也不接收 Benchmark 词汇。Benchmark 在 Runtime 之外记录它冻结了哪个
profile。

## 3. 机器契约

contract version：

```text
connectionagent.runtime-execution-profile/v1
```

请求侧没有任何 execution-governance machine type。ordinary `ExecuteRequest` /
`ProcedureExecutionRequest` 只携带 request identity 与 executable identity：

```yaml
requestId: <idempotency identity>
artifactDigest: sha256:<...>
entrypoint: <entrypoint>
input: <business input>
correlation: {host, callId, ...}
```

governance selection 完全属于 deployment configuration（见 §8.1）。

properties：

```text
Benchmark-neutral
versioned
serializable
digestable
freezeable
auditable
```

deployment 侧 admission（`runtimehost.ExecutionProfileAdmission(s)`）：

```yaml
admittedProfiles: [GOVERNED] | [GOVERNED, DIRECT]
bindings:
  - bindingRef: <ref>
    bindingDigest: sha256:<...>
    profile: GOVERNED | DIRECT
    profileRef: <runtime-profile-ref>?
    sourceAuthority: <owner>?
    toolsetRef: <ref>?
    toolsetDigest: sha256:<...>?
    capabilities: [<admitted capability>...]?   # optional Tool-surface upper bound
```

约束：

```text
caller 不提交任何 execution-governance 选择
DIRECT 只有在 deployment admits DIRECT、activeProfile 为 DIRECT 且存在 admitted DIRECT binding 时才可达
无 activeProfile -> GOVERNED default
从未就绪的 deployment configuration 不进入执行（install/readiness fail closed）
```

`capabilities` 是 **Host-facing（entrypoint 级）admitted Tool surface** 的上界：Runtime 用它在 Provider side effect 之前对 `capability`/`entrypoint` 做 fail-closed 校验。artifact 内部 callable（MCP dispatch key）由 `ResolveDirect` 机械翻译（ca-runtime#104），不是 request/admission 的 Host-facing identity。

## 4. Tool visibility 与 execution governance 正交

Tool visibility 与 execution governance 是 **两个独立轴**：

```text
Tool visibility axis
  = resolved Tool surface
  = 现有 Runtime Toolset / Capability resolution owner（resolved-ca-toolset.md）

Execution governance axis
  = GOVERNED | DIRECT
```

禁止：

```text
DIRECT  = 全量 Tools
GOVERNED = narrowed Tools
LLM_ONLY = no Tools
```

允许并被 first-slice acceptance 证明：

```text
same Tool surface + GOVERNED
same Tool surface + DIRECT
```

admission 的 `toolsetRef`/`toolsetDigest` 描述 effective Tool surface；`capabilities` 是 deployment-owned
上界，缺失时以 deployment admitted catalog 为准。caller 不能确认或扩大 Tool surface。

## 5. GOVERNED 语义（不得变化）

production GOVERNED 路径保持：

```text
RuntimeHost
  -> admission
  -> resolved Toolset / Skill / Procedure
  -> preconditions
  -> predicates / invariants
  -> execution
  -> Outcome
  -> reconcile
  -> retry fence
  -> assurance
  -> ProviderBinding
  -> Provider
```

本轮不得改变：

```text
Outcome semantics
OUTCOME_UNKNOWN
Reconcile
Procedure
Assurance
Retry fence
Authorization
ProviderBinding
RuntimeHost v1 behavior
```

`GOVERNED` 是 absent binding 的 compatibility default；现有 caller 行为必须与之前完全一致。

## 6. DIRECT 语义

DIRECT 只保留“正确调用 Tool/Capability 所需的机械执行能力”。

保留：

```text
stable Tool / Capability identity
input contract validation required for transport correctness
ProviderBinding resolution
Provider selection
Provider transport
request correlation
result correlation
typed/raw Provider result projection
deterministic transport/error normalization
execution profile provenance
```

明确不执行：

```text
Skill / Procedure orchestration
Goal-scoped Harness admission
preconditions / postconditions
Predicate / invariant gate
Assurance
Runtime recovery policy
OUTCOME_UNKNOWN reconciliation policy
controlled retry / retry fence
compensation
Harness mutation orchestration
```

DIRECT **不是** “disable a few checks in Procedure”，而是一条独立、机械的 execution path：

```text
resolver.ResolveDirect
  -> Tool identity + input schema（transport correctness）
  -> prepareDispatch（复用 Runtime-owned ProviderBinding）
  -> invokeProvider（复用 Runtime-owned Provider transport）
  -> deterministic status/projection
```

Tool identity 绑定规则（ca-runtime#104）：MCP dispatch binding 以 artifact **bound
callable** 为 key，而不是 artifact entrypoint name。`ResolveDirect` 必须把
entrypoint/artifact DIRECT request 机械翻译成 admitted bound callable：

```text
single-callable artifact  -> tool name = the admitted bound callable
multiple callables        -> fail closed unless an explicit callable is admitted
```

这修复了 artifact-deployment HTTP DIRECT path 的 `MCP_STATIC_DISPATCH_BINDING_MISSING`。

### 6.1 DIRECT 的 durable Run evidence（ca-runtime#106）

DIRECT 仍是纯机械路径，但每次 execution 都提交权威 `RunRecord` + `RunEvent`
stream（`run.started` → `run.ended`），字段与 GOVERNED Run 相同：

```text
RunID / Host / HostRequestID / HostCallID / ArtifactDigest / Entrypoint / VariantDigest
```

因此 `GET /api/host/v1/runs/{runId}` 与 run list 能读回 DIRECT Run，association
plane 不需要 DUT echo。

- stream 只包含 `run.started` / `run.ended`；不写 Procedure/Authorization/
  Assurance/Dispatch/Reconcile fact，也不进入 reconcile/retry policy；
- `run.ended` terminal controlState 只使用 `SUCCEEDED | FAILED`：
  `RESULT_UNKNOWN` 是 capability operation outcome，不是 Run control state
  （见 `run_record.go`），因此 DIRECT 的 `RESULT_UNKNOWN` 记 terminal `FAILED`
  并在 `run.ended` payload 保留 exact `directStatus` / `operationOutcome`；
- RunStore commit 定义成功：无法提交 Run record 的 DIRECT execution 直接
  fail closed，绝不返回不可读的 `runId`；
- 同一 deterministic `runId` + identity replay 是 idempotent，不重开/重关
  已终结的 stream。

## 7. ProviderBinding 单一 authority

ProviderBinding / Provider catalog / Capability→Provider mapping / Provider selection / Provider transport
configuration 只有一份 authority：Runtime。两条路径汇合到同一个 owner：

```text
Runtime execution substrate
        |
        +-- GOVERNED
        |      |
        |      +-- Harness governance
        |              |
        |              +-- ProviderBinding
        |
        +-- DIRECT
               |
               +-- ProviderBinding
```

禁止：

```text
tool-mcp-gw -> direct Provider
DIRECT 复制 Provider catalog / mapping / selection / transport config
```

两条路径都消费 resolver 产出的同一 `runtimeengine.Dependencies`（`DispatchPreparer` + `Provider`）。

## 8. RuntimeHost exposure

RuntimeHost 的普通 request **不承载任何 execution-governance 选择**：`ExecuteRequest` /
`ProcedureExecutionRequest` 只有 request identity 与 executable identity。caller 既不能提交裸 profile
字符串，也不能提交 owner-resolved binding。effective execution profile 完全由 Runtime 从自己的
deployment configuration 解析。

### 8.1 Deployment-owned active profile (ca-runtime#105)

active execution profile 属于 Runtime deployment configuration：

```yaml
# RuntimeArtifactDeployment.spec.executionProfiles
executionProfiles:
  admittedProfiles: [GOVERNED, DIRECT]
  activeProfile: DIRECT          # deployment-owned; empty => GOVERNED compatibility default
  bindings:
    - bindingRef: ...
      bindingDigest: sha256:...
      profile: DIRECT
      ...
```

规则：

```text
ordinary Execute
  -> Runtime resolves the deployment activeProfile
  -> empty/GOVERNED -> GOVERNED default
  -> DIRECT requires DIRECT in admittedProfiles + an admitted DIRECT binding
  -> otherwise fail closed (PROFILE_NOT_ADMITTED)

activeProfile DIRECT without admitted DIRECT profile or an admitted DIRECT binding
  -> rejects at deployment installation time, not per Tool call

restart-based activation:
  write config -> restart Runtime -> wait READY -> ordinary Execute
  hot reload is optional and must fence on active executions == 0

missing / invalid deployment profile
  -> fail closed at deployment install / startup / readiness, never per Tool call
```

effective profile 仍由 `applyExecutionProfileProvenance` 正向记录到结果上（§10）。

Runtime 实例通过 `GET /api/v1/identity` 暴露 **owner output**：`deploymentRef` / `environmentRef` / `executionProfile`（当前 effective active profile）。这使 owner preparation 能够 read-back 并签发 truthful `PreparationReceipt`（`owner=RUNTIME`、`effectiveExecutionProfile`、`readiness`），而不是让 Engine 猜「应该配置好了」。

此外，每个 `ExecuteResult` 正向记录 effective deployment provenance（owner output，非 caller input）：`runtimeDeploymentRef` + `runtimeDeploymentDigest`（immutable manifest digest），与 `executionProfile` / `executionProfileDigest` / `providerBindingRef`+digest / `runId` / `requestId` 一起供 Evaluator 建立 external association。

## 9. Security / admission fence（fail closed）

Direct execution 只有在 Runtime 自己的 deployment configuration 已经 admitted 时才可达：

```text
Runtime deployment admits DIRECT profile
+
deployment activeProfile == DIRECT
+
an admitted DIRECT binding exists in the frozen deployment admission
```

configuration 错误在 **deployment install / startup / readiness** 阶段 fail closed，不推迟到普通 Tool Call：

```text
PROFILE_NOT_ADMITTED   (403)  active DIRECT profile 缺失/未 admitted，或没有 admitted DIRECT binding
                              未就绪的 deployment 不会开始服务普通 Execute
```

执行期剩余 fence（仍在 Provider dispatch 之前失败，且不产生任何运行事实）：

```text
TOOL_NOT_ADMITTED      (403)  capability 不在 admitted Tool surface
EXECUTION_NOT_READY    (503)  composition 无 direct seam（fail closed）
```

## 10. Provenance

每次 execution 都携带正向 profile evidence（GOVERNED 不从“没有 DIRECT fact”反推）：

```text
executionProfile
executionProfileVersion
executionProfileRef
executionProfileDigest
executionSourceAuthority
executionPath = GOVERNED_PROCEDURE | DIRECT_PROVIDER
effectiveToolsetRef / effectiveToolsetDigest
invocations[].providerBindingRef / providerBindingDigest
```

`executionProfileDigest = sha256(profile | profileRef | sourceAuthority)`（canonical，可由 auditor 重算）。
provenance 冻结进 ExecuteResult，并由 durable `RequestStore` record 保留。

## 11. Error / result 语义

DIRECT 不复用 governed `Outcome` / `Terminal` / `Reconcile`。

DIRECT result status：

```text
SUCCEEDED               dispatch 发生且 provider 报告成功/commit
FAILED_BEFORE_DISPATCH  binding/input 失败，Provider 从未被调用
PROVIDER_ERROR          dispatch 后 provider 机械失败
RESULT_UNKNOWN          dispatch 可能发生但结果 transport/commit 不确定
```

Host 执行完成字段映射：

```text
SUCCEEDED              -> hostState = SUCCEEDED
FAILED_BEFORE_DISPATCH -> hostState = FAILED
PROVIDER_ERROR         -> hostState = FAILED
RESULT_UNKNOWN         -> hostState = RESULT_UNKNOWN
```

DIRECT result 单独放在 `directResult`，并保留 typed/raw provider payload 在 `invocations[].result`。

## 12. Uncertainty ownership

DIRECT side-effecting call 出现：

```text
dispatch happened
result unknown
```

形成 `RESULT_UNKNOWN`（`hostState = RESULT_UNKNOWN`），但：

```text
DIRECT MUST NOT automatically reconcile
DIRECT MUST NOT automatically retry
DIRECT MUST NOT compensate
```

DIRECT 可以报告 ambiguity，但不能自动治理它。Runtime `OUTCOME_UNKNOWN` / `Reconcile` ownership 不被
DIRECT 破坏：DIRECT 不产生 `SAFE_STOPPED` / `pendingAction`，也不形成 reconciliation 事实。

## 13. Run / Event 边界

DIRECT 是机械 Tool 调用，不是 governed Run：

```text
no ProcedureDigest
no governed HostState（SAFE_STOPPED / NEEDS_DECISION）
no RunEvent governed lifecycle
provenance 在 ExecuteResult + durable RequestStore record 中保留
```

GOVERNED 仍创建 authoritative RunRecord / RunEvent。

## 14. tool-mcp-gw 边界

`tool-mcp-gw` ownership 不变：

```text
Agent Host -> standard MCP -> tool-mcp-gw -> Runtime execution port
```

不得：

```text
tool-mcp-gw  ├─ Runtime backend
        └─ Provider backend
pureLlm=true / llmOnly=true / benchmarkMode=... / skipHarness=true
```

`tool-mcp-gw` 只机械承载 Runtime owner 已解析/允许的 execution binding。

## 15. Migration / sequencing

```text
1. Runtime 冻结本 machine contract（本文）
2. GOVERNED regression 保持不变
3. DIRECT implemented（same ProviderBinding mechanics）
4. Engine #35 负责 ResolvedCUTIngress + effective Tool surface + execution profile provenance 的 freeze/resolution
5. Benchmark 保持 LLM_RUNTIME | LLM_ONLY | RUNTIME_ONLY
```

历史 `#30` `LLM_ONLY -> RuntimeBackedTools=ABSENT` 仍是有效的 no-tools ablation / ingress baseline evidence，
**不得**被重新解释为 LLM_ONLY DIRECT PASS。新的 DIRECT evidence 必须来自新的 acceptance artifact。

## 16. Acceptance

见 `docs/WORK.md` / `docs/TRACEABILITY.md` 与
`artifacts/acceptance/20260930-runtime-direct-profile/`。

required focused cases：

```text
GOVERNED existing behavior unchanged
DIRECT read-only success
same semantic Tool through GOVERNED and DIRECT
same ProviderBinding used by both
Tool surface independent from execution profile
DIRECT skips Procedure
DIRECT skips Predicate/invariants
DIRECT skips Assurance
DIRECT skips reconcile
DIRECT skips controlled retry
DIRECT skips compensation
```

negatives（全部 fail before side effects）：

```text
DIRECT not admitted by deployment (install-time)
activeProfile DIRECT without an admitted DIRECT binding (install-time)
ProviderBinding unavailable
Tool not in admitted Tool surface
```

## 17. 不变量

```text
Runtime execution governance is GOVERNED | DIRECT and Benchmark-neutral.
DIRECT is never the default; the deployment activeProfile (empty) preserves GOVERNED.
Tool visibility and execution governance are independent axes.
Runtime owns the single ProviderBinding / Provider transport authority.
DIRECT reuses the governed ProviderBinding mechanics; it never duplicates them.
DIRECT never executes Procedure/Predicate/Assurance/Reconcile/retry/compensation.
DIRECT reports uncertainty but never governs it.
DIRECT is not a governed Run.
The ordinary RuntimeHost request carries no execution-governance selection.
Deployment profile errors fail closed at install/startup/readiness, not per Tool call.
Execution profile provenance is positive, durable evidence of the path that ran.
tool-mcp-gw remains the Agent-facing Runtime execution adapter, never a Provider proxy.
```

## 18. Historical / superseded: request-level execution binding

**Status: REMOVED / SUPERSEDED (ca-runtime#105; historical ca-runtime#103 shape).**

An earlier revision of this contract let a caller submit an owner-resolved request-level
`executionBinding` (`runtimehost.ExecutionBinding`) on `ExecuteRequest` /
`ProcedureExecutionRequest`. That surface has been **hard-removed**: the Go DTO fields, the
`runtime-host.schema.yaml` request/binding definitions and result `executionBindingRef` /
`executionBindingDigest` fields, the request-side normalization/fingerprint contribution, and the
`EXECUTION_BINDING_REQUIRED` / `EXECUTION_PROFILE_UNKNOWN` / `PROFILE_BINDING_MISMATCH` errors.

Runtime now selects the effective profile only from its own deployment configuration
(`RuntimeArtifactDeployment.spec.executionProfiles.activeProfile`, §8.1). Historical #103/#104
evidence under `artifacts/acceptance/` is retained unchanged as audit material and must not be
read as current canonical behavior. This section is history, not a compatibility contract.
