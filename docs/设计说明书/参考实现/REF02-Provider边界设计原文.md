> 迁移来源：ca-runtime/docs/design/provider-boundary.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# Provider / Outcome / Reconcile 边界

Status: Accepted<br>
Version: v1.2<br>
Date: 2026-09-29

## 1. 定位

Provider 是 Runtime 执行真实能力的受治理边界。Provider 可以封装 Service Fabric、MCP、native NF、HTTP/gRPC 或 process-local implementation，但 transport family 不改变 Runtime safety semantics。

```text
Runtime Procedure
  -> Authorization / Assurance
  -> ProviderBinding
  -> authoritative dispatch
  -> Provider
  -> Provider knowledge/evidence
  -> Runtime Outcome
  -> Reconcile when required
```

## 2. Ownership

Runtime owns：

```text
Capability admission
ProviderBinding identity
pre-dispatch barrier
invocation identity / idempotency material
Run dispatch facts
Outcome / OUTCOME_UNKNOWN
retry fence
Reconcile / Recovery
```

Provider owns：

```text
concrete transport / SDK usage
remote operation invocation
remote result decoding
provider-specific knowledge normalization
provider-specific credential/endpoint handling where applicable
```

Provider does **not** own Runtime authorization、final Outcome、blind retry policy 或 Run state。

## 3. ProviderContract 必须 transport-neutral

Runtime core 面向稳定 Provider contract，而不是协议特化接口。概念 seam：

```go
type Provider interface {
    Invoke(context.Context, Invocation) (ProviderKnowledge, error)
}
```

字段以当前 machine contract 为准；关键原则是不为了 MCP/HTTP/Service Fabric 修改 Runtime 核心 Outcome/Run 语义。

## 4. ProviderBinding

Provider discovery/reachability 不等于 admission。

目标链：

```text
frozen expected capability/tool contract
  + deployment/provider discovery
  + conformance
  -> admitted ProviderBinding
  -> frozen dispatch identity
```

Runtime Action 只能使用 admitted exact binding。Provider 新增 operation、修改 schema 或换 endpoint不能自动扩大 Agent/Artifact 权限。

DIRECT execution profile 不复制 ProviderBinding authority：两条 execution path（GOVERNED/DIRECT）都通过
Runtime-owned `DispatchPreparer` + `Provider` 解析/使用同一个 admitted ProviderBinding。见
[`runtime-execution-profile.md`](runtime-execution-profile.md)。

## 5. Agent-facing capability 与 Provider operation

```text
Runtime capability identity
!= Provider tool/operation identity
```

Agent 通过 `tool-mcp-gw` 看到的是 Runtime admitted capability，不是 Provider `tools/list` 原样转发。

```text
Agent Host -> tool-mcp-gw -> Runtime capability
Runtime -> ProviderBinding -> Provider operation
```

## 6. Provider MCP 与 tool-mcp-gw

Provider 使用 MCP 时：

```text
Runtime
  -> Provider MCP adapter
  -> provider MCP server
```

Agent-facing MCP：

```text
Agent Host
  -> tool-mcp-gw
  -> RuntimeHost.v1
```

两者不同 owner、不同权限、不同 identity。Provider MCP discovery 不能成为 Agent authorization。

## 7. Mutation retry

副作用 mutation 越过 authoritative dispatch barrier 后，Provider transport ambiguity 必须保守处理：

```text
timeout / response loss / connection reset
  -> no blind redispatch
  -> return uncertainty/knowledge to Runtime
  -> Runtime derives OUTCOME_UNKNOWN when applicable
```

Provider 内部不得因为“HTTP/MCP 调用失败”就推断 remote NOT_COMMITTED。

Read-only retry可以有独立有限策略，但不能被复用为 mutation retry policy。

## 8. Simulation 中三类 timeout

Reference simulation 必须区分：

~~~text
simulated protocol response deadline
  = Environment deterministic scheduler domain

Runtime provider/execution deadline
  = Runtime execution control

Host / MCP caller timeout
  = caller wait/transport lifecycle
~~~

只有 Runtime 根据 authoritative dispatch、Provider knowledge 与 Evidence 才能形成 OUTCOME_UNKNOWN。

~~~text
Host timeout
!= Runtime OUTCOME_UNKNOWN

simulated protocol WAIT_EXPIRED
!= Runtime OUTCOME_UNKNOWN by itself

response lost after side-effect dispatch
-> Runtime may derive OUTCOME_UNKNOWN
~~~

首个 N4/PFCP simulation slice 以 connectionagent/docs/simulation-n4-pfcp-vertical-slice.md 为冻结语义。

### 8.1 C7 first-slice ProviderKnowledge mapping

首个 N4/PFCP reference simulation 的 simulator backend knowledge 至少区分：

~~~text
COMPLETED
REJECTED
WAIT_EXPIRED
INVALID_PRESTATE
~~~

Runtime mapping 规则：

~~~text
COMPLETED
  -> continue normal postcondition / Outcome derivation

REJECTED
  -> explicit provider/business failure knowledge
  -> Runtime still applies its own policy/outcome semantics

INVALID_PRESTATE
  -> no backend side-effect dispatch for this operation
  -> Runtime classifies according to admission/procedure semantics

WAIT_EXPIRED
  + authoritative side-effect dispatch crossed
  + commit disposition not established
  -> candidate for Runtime OUTCOME_UNKNOWN
  -> no blind redispatch
  -> reconcile
~~~

Runtime 不允许 adapter 把 WAIT_EXPIRED 直接硬编码成 OUTCOME_UNKNOWN；authoritative dispatch fact 与 effect classification 仍必须参与。

### 8.2 Recovery identity

首个 reference recovery branch 保持：

~~~text
same requestId
  = same external logical mutation/idempotency identity

same runId
  = same authoritative Runtime execution

new invocationRef
  = new internal provider/recovery invocation

new PFCP transactionRef
  = new protocol transaction for cleanup/retry
~~~

因此：

~~~text
controlled retry inside reconcile
!= second external request
!= RequestStore replay
~~~

Runtime 必须在 Run/RunEvent 中保留 old UNKNOWN invocation 与 recovery invocation 的显式 lineage。

## 9. Outcome

原则：

```text
Provider reports knowledge.
Runtime derives authoritative Outcome.
```

Runtime Outcome 需要结合：

```text
effect
authoritative dispatch fact
Provider knowledge
trusted evidence where required
reconcile result when uncertain
```

Transport success不等于业务 COMMITTED；Provider result也不能绕过 postcondition/Evidence gate。

## 10. Reconcile

`Reconciler` 是 Runtime trusted UNKNOWN resolution boundary，不是普通 Agent Tool，也不是 Provider 自动重试器。

```text
OUTCOME_UNKNOWN
  -> Reconcile
  -> establish externally verifiable state
  -> choose admitted continue / compensate / controlled retry / safe stop
```

恢复策略由 frozen Runtime procedure/policy消费。

## 11. Evidence

Provider output 与 trusted Evidence 是不同角色：

```text
Provider result
  = operation knowledge/output

Trusted Observation/Evidence
  = postcondition / Predicate / Assurance input
```

具体 adapter可以帮助归一化 observation，但不能直接制造 `PASS`/`FAIL` 来夺走 Runtime Predicate ownership。

## 12. Endpoint / credentials

Endpoint、credential material 与 transport wiring 属于 deployment/provider adapter，不进入：

```text
LLM Tool arguments
Runtime Artifact identity
Agent-facing capability schema
Run public facts as raw secret
```

Runtime/Provider只保存需要审计的 opaque refs / safe provenance。

## 13. Concrete adapters

当前仓已有或保留的实现说明位于：

```text
design/integrations/offline-provider-adapter.md
design/integrations/provider-mcp-discovery-and-binding.md
design/integrations/service-fabric/
```

这些实现不能反向覆盖本页的 Runtime core boundary。

## 14. Pending mutation uncertainty 与 action budget exhaustion

Status: **Frozen**（ca-runtime#96；Runtime authoritative semantics）

### 14.1 两个正交事实

```text
mutation outcome uncertainty
  = 一次已越过 authoritative dispatch 的 mutation 的远端结果
    尚未被 Runtime 权威确定

action budget exhaustion
  = authored governed-action 预算已用尽
```

两者可以同时成立，但互不覆盖。budget exhaustion 只能作为**并存的 execution fact**，不能：

```text
erase   previous OUTCOME_UNKNOWN invocation
erase   reconcile result
erase   owning action identity
rewrite pending / uncertainty state
authorize blind redispatch
```

Runtime evidence 必须保留足够 owner-native facts，使普通 budget stop 与 uncertainty/recovery stop 在机器上可区分。

### 14.2 决策表

| Case | 语义 | Outcome | Terminal | pendingAction | reasonCode | budget.exhausted | Provider redispatch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | ordinary budget exhaustion；无 pending mutation | `FAILED` | `FAILED` | 空 | `BUDGET_EXCEEDED` | `true` | 无 |
| B | mutation `OUTCOME_UNKNOWN` 无法权威 resolve（无 recovery map，或 reconcile `UNRESOLVED`） | `SAFE_STOPPED` | frozen recovery terminal（`UNRESOLVED` 映射的 terminal），否则空 | UNKNOWN mutation Action node | 空（uncertainty 是直接原因） | 若预算同时耗尽则 `true`（并存事实） | 无 |
| C | `OUTCOME_UNKNOWN` -> reconcile `NOT_COMMITTED`（retry admitted）-> 下一个 Action 需要 dispatch，但预算已耗尽 | `SAFE_STOPPED` | 空 | 被 admit 但未 dispatch 的 retry Action node | `BUDGET_EXHAUSTED_PENDING_RETRY` | `true` | 无（第二次 dispatch = 0） |

`pendingAction` 只有一个含义：**Runtime 停止前没有完成的那个 Action node**（其 dispatch 或 owner resolution 仍待进行）。Case B/C 的“为什么仍未完成”由 `reasonCode` 与 retained reconciliation 区分，而不是让 `pendingAction` 承担两种含义。

### 14.3 Case A — ordinary budget exhaustion

没有任何 outstanding mutation uncertainty / admitted recovery 时，`ActionCount >= effective maxActions` 保持既有兼容语义：

```text
Outcome        = FAILED
DomainTerminal = FAILED
ReasonCode     = BUDGET_EXCEEDED
PendingAction  = empty
Budget.Exhausted = true
```

不得因为 #96 顺手重定义该情形；G08 即此语义。

### 14.4 Case B — mutation OUTCOME_UNKNOWN 无法 resolve

```text
mutation -> OUTCOME_UNKNOWN
  -> recovery map 缺失，或 reconcile = UNRESOLVED
  -> SAFE_STOPPED
```

- remote mutation outcome 仍然 UNKNOWN；
- `pendingAction` = 该 mutation node；
- `reasonCode` 保持空：uncertainty 是直接原因，budget（若同时耗尽）只是并存事实；
- 若 recovery `UNRESOLVED` 映射到 frozen terminal，则该 terminal 作为 `Terminal` 保留；
- 不得回退为 `FAILED / BUDGET_EXCEEDED`；
- 不得 redispatch。

### 14.5 Case C — NOT_COMMITTED retry admitted 但预算耗尽

```text
mutation A -> OUTCOME_UNKNOWN
  -> reconcile = NOT_COMMITTED, retry = true
  -> frozen recovery transition 指向 retry Action
  -> no authored action budget remains
  -> SAFE_STOPPED
```

必须同时冻结：

```text
original mutation outcome history
  = 保留的 OUTCOME_UNKNOWN invocation（含其 Reconciliation）

reconcile result
  = NOT_COMMITTED（authoritative；远端第一次 mutation 未提交）

retry admission
  = admitted（NOT_COMMITTED + retry=true + frozen recovery transition to an Action）

budget exhaustion
  = actionsUsed == maxActions, exhausted = true

final Runtime outcome
  = SAFE_STOPPED

pending / action state
  = pendingAction = 被 admit 但未 dispatch 的 retry Action node

reasonCode
  = BUDGET_EXHAUSTED_PENDING_RETRY
```

区分两个概念：

```text
historical mutation uncertainty
  = 历史事实：第一次 invocation 曾是 OUTCOME_UNKNOWN（必须保留）

current authoritative reconciliation result
  = 当前事实：reconcile 已权威证明 NOT_COMMITTED
```

以及：

```text
goal / action still pending
  = 是（admitted retry 未执行）

remote side-effect outcome still unresolved
  = 否（已是 NOT_COMMITTED）
```

因此：

- 不得在 reconcile 权威 `NOT_COMMITTED` 后仍宣称 remote commit unknown；
- 也不得因为已 `NOT_COMMITTED` 就丢掉历史 `OUTCOME_UNKNOWN` invocation / reconciliation；
- 预算耗尽必须阻止第二次 dispatch，但不得把该情形折叠成普通 `FAILED / BUDGET_EXCEEDED`。

Case B 与 Case C 的机器区分由 retained invocation 的 `reconciliation.resolution`（`UNRESOLVED`/absent vs `NOT_COMMITTED` + `retry=true`）与 `reasonCode`（空 vs `BUDGET_EXHAUSTED_PENDING_RETRY`）共同承担。

## 15. Action budget 计数语义

`effective maxActions` 由冻结材料机械决定：

```text
effective maxActions
  = min(PreparedRun.executionLimits.maxActions, Procedure.MaxActions)
```

caller / replay 只能收紧，不能提高 Procedure intrinsic bound。

消耗 `maxActions` 的动作（每次 dispatch +1）：

```text
ordinary Action dispatch
loop body Action dispatch
composed loop body Action dispatch（每次 iteration 内每个实际 dispatch 的 body Action 各 +1）
Script Action execution
controlled mutation retry 触发的新的 Action dispatch
```

不消耗 `maxActions` 的行为：

```text
Reconcile（Runtime trusted resolution 本身不 dispatch mutation）
Predicate / Verify
Observe
deterministic transition
Decision pause / resume
Terminal
```

原则：

```text
任何新的 externally observable side-effect dispatch 不得绕过 Action budget。
```

controlled retry 是**新的** Action dispatch，因此消耗预算；`maxActions = N` 意味着最多 N 次 governed Action dispatch（含 retry）。不得因为 Reconcile 属 recovery 就偷偷扩大 `PreparedRun.executionLimits.maxActions` 的 authority。

## 16. 不变量

```text
Provider transport is not Runtime authority.
Provider discovery is not Agent authorization.
ProviderBinding is admitted and frozen before side-effect dispatch.
Provider reports knowledge; Runtime owns Outcome/Reconcile.
Mutation transport uncertainty never authorizes blind retry.
Provider MCP != Agent-facing tool-mcp-gw.
UNKNOWN must never be erased merely because action budget is exhausted.
Action budget exhaustion never authorizes blind redispatch.
Controlled retry requires NOT_COMMITTED + retry=true + remaining authored budget.
ordinary budget exhaustion != budget exhaustion with pending/admitted recovery context.
```

## 17. Cancel boundary / parallel mutation conflict

取消边界（`PRE_DISPATCH_CANCEL` / `POST_DISPATCH_ABANDONMENT` /
`transport_disconnect` / `business_cancel`）与竞争 mutation 的
conflictKey/holder/admission/revalidation 已冻结在
[`cancel-boundary-and-mutation-conflict.md`](cancel-boundary-and-mutation-conflict.md)。

关键不变量：

```text
transport disconnect != business cancellation
caller disconnect 不得 revoke 业务 operation
PRE_DISPATCH_CANCEL 才可证明 NOT_COMMITTED（且没有 action.dispatched）
POST_DISPATCH_ABANDONMENT 必须 OUTCOME_UNKNOWN + 既有 Reconcile 规则
conflictKey 与 request identity 解耦；competing mutation 确定性 fail closed
```