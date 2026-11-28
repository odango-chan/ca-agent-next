> 迁移来源：ca-runtime/docs/design/executable-procedure.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# ExecutableProcedure 确定性执行合同

**Status: Accepted**<br>
**Version: v1.1**<br>
**Date: 2026-10-01**

## 1. 定位

`ExecutableProcedure` 是 Runtime-owned、已经解析并冻结的执行材料。它承接 Agent/确定性 caller 已经选定的 capability/procedure，并在 Runtime trust boundary 内执行。

```text
Agent / deterministic Procedure source
        ↓ selected intent / artifact / entrypoint
RuntimeHost.v1
        ↓ resolve admitted immutable material
ExecutableProcedure
        ↓
Authorization / Assurance
        ↓
ProviderBinding / Dispatch
        ↓
Outcome / Evidence / Reconcile
```

它不是 authoring `ProcedureSpec`，也不是 LLM planning loop。

## 2. Agent 与 Runtime 的分工

Agent Host owns：

```text
Goal understanding
context / Skill selection
open-ended planning
model request/response
capability/procedure choice
```

Runtime owns：

```text
admission of selected immutable material
deterministic procedure progression
preconditions / postconditions / invariants
Authorization / Assurance
exact side-effect dispatch
Outcome / UNKNOWN
Reconcile / Recovery
Run/Event facts
```

Runtime canonical path 不在每个 Action 内重新调用 LLM 让模型决定“下一步做什么”。仓内仍存在的 model-driven engine/qualification code属于 compatibility cleanup，不定义本合同。

## 3. Procedure 来源

上游可以有多种 Procedure 来源：

```text
Agent/LLM planned procedure
predefined deterministic procedure
fallback-selected certified deterministic procedure
```

进入 Runtime 前必须收敛为同一类 frozen executable material。Runtime 不因来源不同而复制三套执行器。

## 4. 节点与 progression

Runtime 可以支持确定性的：

```text
Action
Verify
bounded Decision
Terminal
```

其中 bounded `Decision` 只能基于已经冻结的 deterministic Predicate / trusted fact 做有限分支；若仍需要开放式 LLM reasoning，应回到 Agent Host，而不是在 Runtime private state 内调用模型。

Runtime 自己推进 program counter；Host 不提交或修改 private PC。

### 4.1 Bounded `for` 与 composed loop body

`ExecutableLoop` 是 Runtime-native 的 bounded structured control-flow。冻结材料有两种 body 形态：

```text
legacy single-Action shorthand
  body = 一个 direct Action，且没有 body transition
  enclosing loop 的 on 拥有唯一 outcome edge；既有语义保持不变

composed loop body
  body = 冻结的多节点确定性 sub-graph
  每次 iteration 都从 body[0] 进入，只沿 body 内部 transition 推进
  每个 body Terminal 的 Result 是一个 iteration outcome
  enclosing loop 的 on 必须 route 每一个 body terminal result
```

composed body 是 Skill 侧 composition 把 dependent Skill 在一个 loop site inline 后形成的冻结形态；Runtime 不为它引入第二套 runner，而是复用同一 ActionKernel、同一 trusted Predicate boundary、同一 Recovery 与同一 Run/Event 事实。

`for` 的 bound 仍由 `maxItems` 与 `Procedure.MaxActions` 机械决定。Runtime 只把 body 中实际 dispatch 的 Action/Script 计入 action budget：per-iteration worst-case cost 取 body DAG 上单次 iteration 的最长 Action/Script 路径，而不是 body 节点数。`planning.budgetPartition` 的 parent/child 划分不由 Runtime 重新推导；parent actions 与 child actions 使用同一个 flat per-run budget，caller 只能收紧。Runtime 消费的 frozen material 只携带 `parentActions + childActions` 的单一 `maxActions`，不携带 partition 本身；`spec.planning.budgetPartition` 是 Toolchain 侧 compile-time planning/accounting 声明（其 owner 为 `odango-chan/ca-skill-toolchain#102`），Runtime 既不重新推导也不另行报告子分区。

iteration 语义：

```text
body terminal SUCCEEDED        -> 下一个 collection item
body terminal 其他结果          -> 立即结束 loop，由 loop 的 on route
UNKNOWN / UNRESOLVED iteration -> 绝不盲目 continue
```

body 内 `verify` / `decision` 走同一 trusted Predicate boundary，因此 composed per-iteration postcondition verify 逐 iteration 求值。Action 仍走同一 ActionKernel，`OUTCOME_UNKNOWN` 仍走 frozen Recovery；mid-iteration 的 checkpoint/resume 由 Runtime-private continuation 承担，恢复后不重复 dispatch 已完成 Action。

composed body 的 `decision` 只支持 evaluator-driven 形态：PredicateEvaluator 直接返回 `PASS`/`FAIL`/`UNKNOWN`，Runtime 按 body 内冻结的 `on` 机械转移。若 evaluator 为某个 body decision 返回 `DecisionRequiredError`（需要外部 bounded choice），composed iteration 内**没有** body-scoped decision continuation 可以暂停/恢复；这是已冻结的合同限制，Runtime 必须 fail closed 返回 `ErrUnsupportedProcedure`，不得猜测分支、不得部分 dispatch、也不得把该 choice 提升为 top-level Run decision pause。需要外部选择的 decision 必须放在 composed body 之外。（`ca-runtime#119`）

composed body 的 `script` 节点同样没有 body-scoped 执行路径：top-level Script 由 caller-owned ScriptExecutor 执行，而 composed-iteration executor 只求值 Verify/Decision，admission 因此以 `ErrUnsupportedProcedure` 拒绝 body 内的 `script` 节点，而不是让它落到 deterministic evaluator 的 unsupported-node default 上 latent 失败。script 必须放在 bounded body 之外。（`ca-runtime#119`）

admission 必须 fail closed：nested loop、未知/重复 body node、body `script`、越出 body 的 dangling transition、unrouted body terminal、不可达 body node、无法到达 terminal 或无界 body cycle 一律拒绝；body node id 还必须与 top-level node 以及其它 loop body 的 node id 互不冲突。

## 5. Action

一个可执行 Action 至少冻结：

```text
capability / tool identity
effect
input source / authoritative arguments
allowed transitions
recovery policy when applicable
required binding constraints
```

进入 Provider 前必须经过统一安全路径：

```text
resolve/admit
-> Authorization
-> Assurance
-> pre-dispatch binding barrier
-> authoritative dispatch fact
-> Provider Invoke
```

Host/Agent 不能覆盖 Runtime-selected ProviderBinding，也不能跳过任何 gate。

## 6. Input binding

输入可以来自：

```text
RuntimeHost request input
frozen prior Action output binding
immutable Artifact/Variant material
```

动态绑定必须 deterministic、可验证、可审计。任何 schema mismatch、missing required material 或 ambiguous mapping 都必须在 side effect 前 fail closed。

不允许用 payload similarity、时间邻近或 LLM 猜测建立 Action 间数据依赖。

## 7. Verify / Predicate

Verify 与 bounded Decision 使用 Runtime trusted Predicate boundary：

```text
trusted Observation / normalized Evidence
  -> Predicate evaluator
  -> PASS / FAIL / UNKNOWN
  -> frozen transition
```

模型可见 business query 不等于 trusted Evidence。Benchmark Oracle 也不进入 Runtime Predicate chain。

## 8. Outcome

Provider transport/remote response只是 knowledge input。Runtime 根据 effect、dispatch facts、Provider knowledge 与证据形成 authoritative outcome。

对于 mutation：

```text
COMMITTED
NOT_COMMITTED
FAILED / DENIED where contract allows
OUTCOME_UNKNOWN
```

具体 vocabulary 以 Runtime machine contract 为准。

## 9. OUTCOME_UNKNOWN / Recovery

副作用 dispatch 后若 commit knowledge 不确定：

```text
Provider uncertainty
  -> Runtime OUTCOME_UNKNOWN
  -> Reconciler
  -> COMMITTED / NOT_COMMITTED / UNRESOLVED
  -> frozen recovery transition
```

必须满足：

```text
COMMITTED       -> never replay original mutation
NOT_COMMITTED   -> retry only when frozen policy explicitly permits
UNRESOLVED      -> safe stop / pending write semantics
```

`OUTCOME_UNKNOWN` 永远不授权盲目重试。

## 10. Cancellation

Transport/caller context 不是 Procedure business lifecycle authority。mutation 进入 authoritative lifecycle 后，caller disconnect不能隐式中断 Outcome/Reconcile/persistence。

显式取消只能使用 Runtime-owned control action，并受 current state/revision/fence 约束。

## 11. Immutable execution material

Production Runtime 不重新读取 mutable Skill authoring workspace。目标链：

```text
Skill Source
  -> Toolchain build/validate/freeze
  -> Artifact / Variant / Runtime Bundle
  -> Production admission
  -> Runtime resolver
  -> ExecutableProcedure
```

Runtime 只消费 exact frozen identity，并验证必要 digest/profile/contract。

## 12. Ownership boundary

ExecutableProcedure 只描述确定性的 Runtime execution material。Model/LLM loop、开放式规划与 qualification-specific orchestration 不属于 Runtime Procedure authority，也不提供兼容入口。

## 13. 不变量

```text
ExecutableProcedure is deterministic Runtime material.
Open-ended LLM reasoning belongs to Agent Host.
Runtime owns private procedure progression.
Every side effect crosses the same Authorization/Assurance/Binding barrier.
Provider does not own final Runtime Outcome.
OUTCOME_UNKNOWN never authorizes blind retry.
Transport disconnect does not cancel business execution.
```