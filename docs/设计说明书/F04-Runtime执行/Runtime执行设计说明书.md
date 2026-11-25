# Runtime 执行设计说明书

> 文档类型：机制设计说明书  
> 文档版本：0.3.1  
> 状态：Next 目标设计；现有 Python/Go Runtime 仅作为参考实现，Next 自身执行链尚待实施验收  
> 功能归属：F04 — Runtime 执行  
> 关联 SR：SR-007、SR-022  
> 修订日期：2026-11-25  
> 适用范围：统一 Action Boundary、Deterministic / LLM-guided、Run / Wait / Resume / Replay、Outcome / Evidence / Reconcile

关联需求见 IR-003、IR-004、IR-006。既有 ca-runtime 与 ca-agent-demo 设计原文见 §12。Tool Interface / Provider 契约消费见 [F03.05](../F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)。

## 1. 设计目标

Runtime 是所有 Skill 操作的唯一执行控制点。Deterministic Procedure Engine 与 LLM Model Loop 可以提出不同 Action，但必须通过相同 Runtime Action Boundary、相同 Plugin Manager 和相同 Owner 结果解释路径。任何模型输出、Procedure 节点或 Plugin 都不能直接绕过 Runtime 执行 Tool。

Runtime 只执行已绑定 Skill 的操作，不承担模型推理、Plugin 生命周期、Skill 作者源编译或业务 Owner 状态所有权。

## 2. 组件边界

| 组件 | 职责 | 禁止职责 |
|---|---|---|
| Host / Agent Core | Event、Run 生命周期协调，Context 组装，Model Loop 宿主 | 直接调用 Tool Plugin |
| Skill Resolver | 新 Event 的 Skill 绑定；Continuation 恢复原 Skill | 执行业务操作 |
| Procedure Engine | 解释已发布 Assurance Artifact，推进确定性 Node | 直接调用 Provider |
| Agent Model Loop | 根据当前 Skill/Context 提出下一步 Action | 扩大 Callable Scope、伪造 Evidence |
| Runtime | Action 校验、Run 状态、Wait/Resume、结果记录和 Reconcile | 模型推理、Plugin 进程管理 |
| Plugin Manager | 分发已放行的 Event/Tool/Delivery Extension | Skill 选择、Owner outcome |
| Tool Plugin | 执行 Interface Package 定义的 Callable | 重新授权或改变 Callable 契约 |
| Owner | 权威业务状态与 mutation 结果 | 由 Agent/Runtime 代替判断 |

## 3. Run 与 Skill Binding

Host 为每个新业务 Event 创建或关联 Run。Run 至少固定：

- runId；
- 原始 Event 身份及 externalRequestId；
- 已绑定 Skill identity 和发布 Artifact identity；
- SkillCatalog generation；
- 执行模式；
- 当前 Procedure/Model interaction 位置；
- responseObligation；
- 已发生的 Invocation、结果和 Artifact refs；
- 当前 lifecycle 状态及终态 outcome。

新 Event 选择 Skill 后，Run 的 Skill identity 和 Catalog generation 不再随 Catalog 更新而漂移。Continuation 必须精确关联原 Run，并恢复原 Skill、原发布 Artifact 和原 response obligation。不能把 Continuation 当作新的 Skill selection event。

生命周期与业务 outcome 分开表达：

~~~text
CREATED -> RUNNING -> WAITING -> RUNNING -> TERMINAL
~~~

TERMINAL 之后的业务结果仍可能是 COMMITTED、NOT_COMMITTED、UNKNOWN 或明确的非 mutation 失败。Run 已结束不等于 Owner mutation 已提交。

Runtime 对公开 Callable、Capability、Effect、Schema、Owner Contract 和 Provider 私有映射的消费关系，遵循 [F03.05 Tool Interface 与 Provider 集成设计](../F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)；Runtime 不解析 Provider 私有 Backend Binding Catalog，也不把 backendOperationId 暴露给 Skill 或模型。

## 4. 统一 Runtime Action Boundary

Deterministic Procedure Engine 和 LLM Model Loop 都生成统一概念的 Action Request：

~~~json
{
  "runId": "run-...",
  "skillRef": "skill-...",
  "catalogGeneration": 12,
  "callableId": "UPN.MODIFY_UP_SESSION",
  "arguments": {},
  "artifactRefs": [],
  "invocationId": "inv-..."
}
~~~

实际序列化 Schema 由 Runtime 公共契约定义；上述仅说明字段职责，不作为独立新协议。

分发前至少检查：

1. Run 存在且处于允许执行的状态。
2. Action 的 Skill identity 与 Run 绑定一致。
3. Callable ID 存在于当前发布 Skill Artifact 声明的 Callable Scope。
4. Callable Interface Package 存在，输入参数满足发布 Schema。
5. Effect、Capability 和 Owner result contract 与 Callable 定义一致。
6. Artifact refs 由 Host 管理，且当前 Invocation/Run 被授权访问。
7. 当前 Action 与 Procedure Node、Wait continuation 和 response obligation 一致。
8. 稳定 invocationId 不会造成同一 mutation 被重复执行。

任何检查失败都在调用 Plugin 前拒绝并记录诊断。Runtime 不得通过自动扩权、猜测 Callable、从模型输出生成 Capability 或 fallback 到另一个 Provider 来修复错误。

## 5. Deterministic 执行

只有存在有效发布 Assurance Artifact 的 Skill 才能使用 Deterministic 模式。Procedure Engine 读取发布 Artifact，不读取作者源、不运行 Compiler、不在运行时重新解析 CA-SL YAML。

每个 Node 按冻结 CA-SL v1alpha5 语义推进：

1. Precondition：验证当前可用 Context/Evidence。
2. Operation：提出一个通过 Runtime Action Boundary 的 Callable Action。
3. Observation：执行只读 Observation Tool，获取事实，不产生 mutation。
4. Postcondition：使用新鲜、来源明确的 Evidence 判断结果。

Procedure 的 Node、Route、Input binding、Wait 和 Predicate 语义以 CA-SL v1alpha5 完整规范为准。Runtime 不应重新定义一套 Procedure DSL。

确定性执行是控制流确定，不意味着所有外部系统结果都可预测。Owner/网络超时可能产生 UNKNOWN。

## 6. LLM-guided 执行

LLM-guided 适用于 SKILL.md-only Skill 和带有效 Assurance 的 Skill。模型根据当前 Skill、Context 和允许的 Callable 描述提出下一步 Action。模型输出不是执行结果，也不是授权。

- SKILL.md-only 没有 Deterministic Procedure，模型负责选择下一步，但 Action 仍经过统一 Runtime Boundary。
- 有 Assurance 的 Skill 可由模型引导，但不得超出发布 Artifact 的 Callable Scope。
- 模型可以请求缺少的 Context 或调用已声明 READ Tool；不能直接构造 Owner Receipt、Commit Proof 或 Evidence。
- 模型失败、输出格式错误、无效 Callable 或不完整参数时停止并给出诊断。

两种模式不形成两套 Tool registry、Provider dispatch 或 Owner outcome 解释。

## 7. Wait、Resume 与 Continuation

Wait 是 CA-SL Procedure 中目标 Node 声明的 READ 触发，不引入作者级 await/poll 循环，也不让 Skill 反复轮询外部服务。

目标流程：

~~~text
Procedure reaches Wait target Node
  -> Runtime records expected READ trigger / correlation
  -> Run becomes WAITING
  -> Host receives matching normalized Event / READ result
  -> Runtime validates original Run + expected target + correlation
  -> same Run resumes at the declared continuation
~~~

Wait 的目标 Node、触发 Callable、输入/输出和相关身份必须来自已发布 Artifact。Runtime 不得用时间接近、相同 SUPI/PSI 或模型推断来匹配 Continuation。

重复或迟到事件：
- 精确相同事件只可作为已知重复处理，不重复执行 mutation。
- Run 已终结、目标不匹配、generation 不一致或 correlation 冲突时拒绝。
- 无法证明是原 Run continuation 时不得新建 unbound Run 继续旧流程。

## 8. Outcome、Evidence 与 Reconcile

Runtime 负责记录 Action/Run 观察到的结果；Owner 负责权威业务状态和 mutation 提交事实。Runtime 不得将 HTTP 200、Plugin process success、delivery success 或本地缓存直接提升为 COMMITTED。

| Owner 结果 | Runtime 解释 |
|---|---|
| COMMITTED + 有效 Receipt/Commit Proof | 原始 mutation 已提交 |
| NOT_COMMITTED + Owner 证明未发生副作用 | 明确未提交 |
| UNKNOWN | 副作用可能发生但无法证明；保持 UNKNOWN |
| READ result | 只表示读操作返回事实，不构成 mutation commit |

对 UNKNOWN：
1. 固定 originalInvocationId、deploymentId、ownerInstanceId、Callable、Run、业务主体和 generation。
2. 禁止直接重发 mutation。
3. 只允许调用 Owner 明确发布的 exact-original Receipt Query / Reconcile。
4. Reconcile 必须匹配原始事务身份；不能换绑新 Run、新 generation 或其他 Session。
5. Reconcile 无法证明时保持 UNKNOWN，不把超时变成失败或成功。

Evidence 必须记录 producer、subject、scope、freshness、correlation 和来源。Runtime 不能伪造 Owner Evidence，也不能把调用者知识写回 Owner 业务状态。

## 9. Replay、幂等与失败

Replay 不是重新执行所有动作。Host/Runtime 应按 Run 与 Invocation identity 恢复已记录的状态，识别已经完成的调用，并在外部 Owner 有 Receipt 支持时精确查询原始结果。

| 失败 | 处理 |
|---|---|
| Skill / Artifact 未绑定 | 不执行 |
| Callable 不在当前 Skill Scope | 拒绝，不调用 Plugin |
| Schema / Artifact ref 无效 | 拒绝，不调用 Plugin |
| Plugin unavailable | 明确失败；不自动换用另一份契约 |
| READ timeout | 记录未知读取结果，按业务流程等待或失败 |
| MUTATION timeout | 默认 UNKNOWN，先查 Owner Receipt，不直接重放 |
| Continuation mismatch | 拒绝恢复 |
| Owner Reconcile unresolved | 保持 UNKNOWN |
| Delivery failed/unknown | 记录响应交付状态，不改变 Owner outcome |

## 10. Demo 范围与非目标

本 Demo 需要基本 Run 关联、调用范围检查、重复 mutation 保护、Wait continuation 和 Owner Receipt/UNKNOWN/Reconcile 正确性。暂不建设生产级 Skill Admission、复杂多租户授权、分布式调度、HA/DR、SLA、跨地域事务、通用 Saga 平台或大规模 Replay 集群。存储实现可采用最小 Host-owned 机制，但不得破坏精确身份与重放约束。

## 11. 验收

- Deterministic 与 LLM-guided 对同一 Callable 都经过同一个 Runtime Action Boundary。
- 模型不能绕过 Runtime 直接调用 Plugin。
- Skill Scope、Schema、Effect、Artifact ref 和 Run 状态检查有正负向测试。
- Wait 由明确 READ 触发，恢复原 Run；不引入作者级 await/poll。
- Duplicate Event、Duplicate Invocation、late response 和 stale generation 不产生第二次 mutation。
- Owner COMMITTED/NOT_COMMITTED/UNKNOWN 映射正确；UNKNOWN 不提升、不重放。
- Reconcile 精确绑定 originalInvocationId、deploymentId、ownerInstanceId、generation 和原 Run。
- Tool Plugin/Owner 故障和 Delivery unknown 不改变 Owner 业务结果。
- 真实 Owner E2E 与 Next Runtime 自身测试分别记录；外部仓 PASS 不得作为 Next Runtime PASS。

## 12. 原始设计资产与实现参考

- [ca-runtime Runtime 架构原文](../../架构设计/参考实现/REF02-CA%20Runtime架构.md)
- [ca-runtime Runtime Host 原文](../参考实现/REF02-Runtime%20Host设计原文.md)
- [Executable Procedure 原文](../参考实现/REF02-Executable%20Procedure设计原文.md)
- [Provider Boundary 原文](../参考实现/REF02-Provider边界设计原文.md)
- [Predicate Runtime 原文](../参考实现/REF02-Predicate%20Runtime设计原文.md)
- [Observation Source 原文](../参考实现/REF02-Observation%20Source契约原文.md)
- [ca-agent-demo Generic Host 架构原文](../../架构设计/参考实现/REF01-Python%20Generic%20Agent%20Host规范架构.md)
- [ca-agent-demo Skill/Tool/Runtime 边界原文](../参考实现/REF01-Skill%20Tool%20Runtime边界原文.md)
- [EC05 Owner Receipt / Reconcile 架构](../../架构设计/外部能力域/EC05-OpenAMSM%20Owner与权威状态架构设计.md)

## 13. 当前实现状态

| 对象 | 状态 | 说明 |
|---|---|---|
| ca-runtime Go Runtime | IMPLEMENTED（独立参考仓） | 不等于 Next Runtime |
| ca-agent-demo Python Host/Runtime | IMPLEMENTED（参考仓 main） | 现有 Root/Admission 路径与 Next Demo 边界有差异 |
| Next Python Runtime | NOT_IMPLEMENTED / NOT_VERIFIED | 本轮恢复设计，不宣称实现 |
| Owner Receipt / Reconcile | IMPLEMENTED（env-openamsm） | 外部 Owner 证据，不替代 Next Runtime 集成验收 |
| Next Create/Modify/Release E2E | NOT_RUN | 需 F03/F05/F06 集成后执行 |

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | 全文 | 从 CA-SL v1alpha5、ca-runtime 与 ca-agent-demo 原始设计重建 Next Runtime 目标，并区分外部参考实现与 Next 实现 | Issue #12；SR-007、SR-022 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §1、§4 | 关联 F03.05 的公开 Tool/Owner/Provider 契约边界，避免 Runtime 消费 Provider 私有映射 | Issue #12；SR-015 |
