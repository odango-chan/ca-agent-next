# Runtime 执行设计说明书

> 文档类型：机制设计说明书  
> 状态：目标设计，待实现和验收  
> 文档版本：0.3.4
> 功能归属：F04 — Runtime 执行  
> 关联 SR：SR-007    
> 全局评审范围：继承根目录 Agent.md 的 review_scope    
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  
> 修订日期：2026-11-25  
> 适用范围：Python Runtime、Run、Callable Scope 检查、Outcome/Evidence、Wait/Resume/Reconcile

关联需求项见 [IR-003](../../IR/IR%20总登记册.md#ir-003)、[IR-004](../../IR/IR%20总登记册.md#ir-004)。

## 1. 设计目标

Runtime 是唯一执行路径的控制点，负责将已绑定 Skill 的执行意图转化为经过基本契约检查、范围检查和结果记录的 Action。Deterministic Procedure Engine 与 LLM Model Loop 是两种不同的 Action 提议来源，但不得形成两条执行或 Tool 分发路径。

本 Demo 不建设独立 Skill Admission 或生产级授权体系。Runtime 仍必须检查 Action 是否属于当前 Skill 已发布 Artifact 声明的 Callable Scope，并确保两种执行模式使用相同的调用边界。

## 2. 组件边界

| 组件 | 职责 |
|---|---|
| Host / Agent Model Loop | 推理、Context 组装、Skill 选择协调、提出 LLM Action |
| Procedure Engine | 推进已发布 Artifact 中的确定性 Procedure，提出下一步 Action |
| Runtime | Run 状态、Callable Scope 检查、Action Boundary、Outcome/Evidence、Wait/Resume/Reconcile |
| Plugin Manager | 将 Runtime 放行的 Tool 调用分发到对应 Plugin |
| Tool Plugin | 执行 Operation，返回契约定义的结果 |
| Owner | 权威业务状态和最终提交结果 |

Host 不直接调用 Tool Plugin。LLM 不得绕过 Runtime，也不得自行扩大 Skill 声明的 Callable Scope、制造 Evidence 或声明 Owner mutation 已提交。

## 3. 统一 Action Boundary

Deterministic 与 LLM-guided 都形成同一种概念上的 Runtime Action Request，并经过相同的校验和分发路径。Callable ID、输入/输出 Schema 和 Effect 来自 Skill Artifact `dependencyClosure` 声明的契约来源：Provider Interface Package 或业务 Owner Contract Package；Capability membership 来自对应 Owner/Interface 契约定义。OpenAMSM MAS 的 `mas::CALLABLE` 来自 Owner Contract Package，而不是 ca-client-tools 的 11-READ Interface Package。**冻结 v1alpha5 Artifact 不包含 Skill 声明的 Capability ID 或 `capabilityRequirements[]`**；Compiler 在 Build 时已用 `trustedBuildContext.capabilityContracts` 校验作者源 Capability 声明，Runtime 不得从 Artifact 推断 Capability ID。运行期 Skill Callable Scope 只由 Artifact 精确 operation/observation exports 建立。Owner Outcomes、Receipt、Commit Proof 和 Reconcile 只来自 Owner Contract Package。Provider Runtime Bindings 只提供私有 backendOperationId、HostInvocation/privateArguments 来源和 observation 定位，不是公开 Tool 契约或授权来源。不得在 Agent Core 内维护重复 Tool 定义。

冻结 CA-SL v1alpha5 Artifact 的 `dependencyClosure` 只携带 dependency alias、stablePackageId 与 exports，不携带 Owner package version / snapshotDigest，也不携带 Capability ID。Next 目标部署设计使用 provider.yaml 的 `interfacePackagePath` / `interfaceSnapshotDigest` 校验 Provider Interface snapshot，并使用 Provider Runtime Bindings sidecar 中的 Owner stableId、version、publicationDigest、manifestDigest 校验部署安装的 Owner publication；这属于部署级依赖固定，不是逐 Skill 字节级 pin。**这不是 ca-agent-demo main 已实现的 package loader**：main 有 ProviderV2Process 和 Scope/契约校验，但没有 provider.yaml / sidecar package loader；PR #246 仍 OPEN、未合并。Runtime 必须验证 Artifact 所需 exports / Schema 存在且与 sidecar Owner identity 一致。

Runtime 在分发前至少核对：

1. 当前 Run 是否绑定有效 Skill 和对应 Catalog generation。
2. Action 是否属于当前 Skill 发布 Artifact 的精确 operation/observation export Scope；冻结 v1alpha5 不提供 Capability ID 字段，不能将 Capability ID 作为运行时 Scope 来源。
3. Callable ID 是否存在且属于部署固定的 Provider Interface Package 或 Owner Contract Package；参数是否符合对应 Schema。Provider Interface bytes 应匹配 provider.yaml 的 `interfaceSnapshotDigest`；Owner snapshot 的 stable ID / required exports 应与 Artifact dependencyClosure 一致，Owner version / publicationDigest / manifestDigest 应与 Provider sidecar 一致。
4. Effect 是否与该 Operation 的声明一致；sidecar Mutation `commitProof.reconcile.bindingId` 引用的 internal-only Reconcile binding 不得通过普通 Skill/LLM Action dispatch。
5. Artifact Reference 是否由 Host 管理并关联到当前 Invocation。
6. Action 是否满足当前 Run 的状态和 continuation 约束。

通过后由 Plugin Manager 分发；拒绝时产生明确诊断，不调用 Plugin。此检查是 Demo 的调用范围正确性，不是生产级 Skill Admission 或 Owner Trust。

## 4. 两种执行模式

### 4.1 Deterministic

前提是 Skill 发布包包含有效 Assurance Artifact，且该 Artifact 已由外部 Compiler 构建并发布。Procedure Engine 只消费已发布 Procedure，不调用 Compiler，不重新做 Procedure Graph 验证。它推进 Procedure 并通过统一 Action Boundary 执行其中的 Action。Procedure 的 precondition、operation、observation、postcondition 语义以 CA-SL v1alpha5 和 Compiler 发布契约为准。

### 4.2 LLM-guided

没有 Assurance Artifact 的 Skill 只能使用 LLM-guided。有有效 Assurance Artifact 的 Skill 也可以使用 LLM-guided，但仍然受该 Skill 的 Callable Scope、Context 和 Runtime Action Boundary 约束。LLM 提出的 Action 不编译成临时 Procedure，不为每个 Action 调用 Compiler。

两种模式共享同一个 Runtime Action Boundary、Plugin Manager、Outcome 和 Evidence 解释路径。

## 5. Run、Context 与来源

Host 为每次新业务执行创建 Run，维护 Event 来源、选定 Skill、Catalog generation、Context 引用、响应义务和交付状态。Continuation 必须依据精确关联恢复原 Run，不得被当成新业务 Event 重新选择 Skill。

Context 中区分：

- Event：外部 Push 输入。
- Tool READ：带来源的 Pull Observation。
- Owner Receipt / Commit Proof：业务执行 Evidence。
- 模型生成文本：推理产物，不是 Observation，也不是 Owner 事实。

Tool 返回成功或 HTTP 2xx 不能自动等价于业务 COMMITTED。具体提交语义由 Owner 发布的 Receipt/Commit Proof 契约决定。

## 6. Wait、Resume 与 Reconcile

Runtime 负责将异步等待与原 Run 关联。恢复消息必须匹配原始 Run、业务身份和等待代际；不能用 HTTP/2 stream ID 替代 Run ID。重复或过期消息不能唤醒新的 Run，也不能重复执行 mutation。

Owner 返回 UNKNOWN 时必须保留 UNKNOWN，并按 Owner 契约执行后续查询或 Reconcile；任何映射都不得把 UNKNOWN 提升为 COMMITTED。传输成功、响应已发送或 Delivery 成功都不能替代 Owner 提交证明。

当前 OpenAMSM Owner v1alpha4 将 `MAS.RECONCILE` 发布为普通 READ operation；冻结 Compiler 不保证直接 Skill 引用一定在 Build 时失败。Next Runtime 必须从 sidecar Mutation `commitProof.reconcile.bindingId` 关系建立 internal-only binding 集合，普通 Skill/LLM Action 调用这些 binding 必须在 Provider IPC 前拒绝；只有 Reconcile Coordinator 可以通过内部专用入口、携带原始 `originalInvocationId` 和 Host scope 调用。缺失/重复/非 READ 目标导致 package load fail-closed。

具体状态机和 Owner Receipt 结构由 Owner Contract Package 定义；Provider Runtime Bindings 只声明 Provider 如何定位并返回该 Receipt，不得重定义其字段和状态。Runtime 不自行发明业务状态枚举。

## 7. 失败语义

Skill/Artifact 无效、Callable Scope 不匹配、Schema 不匹配、Plugin 不可用、IPC 失败、continuation 关联失败均必须产生明确诊断。失败不得伪造 Owner 结果、猜测目标 Run 或自动执行未经声明的替代 Action。

## 8. 验收要求

- Deterministic 和 LLM-guided 两种模式都经过同一 Action Boundary。
- LLM 无法直接访问 Plugin，也无法扩大 Skill 声明的 Callable Scope。
- READ Observation 与 Owner Mutation Evidence 有明确来源。
- UNKNOWN 不得变成 COMMITTED。
- 重复或过期 continuation 不得导致重复 mutation。
- Runtime 的每个拒绝路径都有可断言的错误和自动化测试。
- 冻结 v1alpha5 Artifact 的 Skill Scope 只包含其 operation/observation exports，不读取或推断 Capability ID。
- Skill/LLM 直接调用 sidecar 引用的 internal-only Reconcile binding 时，Runtime 在 Provider IPC 前拒绝；Reconcile Coordinator 内部调用使用原始 Invocation 身份成功。
- Reconcile binding 缺失、重复或非 READ 时 Provider package load fail-closed。

以上是 Demo 功能正确性要求，不是生产级安全或可靠性资格声明。




## 9. 功能归属与需求追踪

本说明书属于 F04，主要需求为 SR-007。Run/Continuation 的协议身份由 F05/F06 的集成设计补充；Owner Receipt/Commit Proof 的权威字段由 EC05 Owner Contract Package 定义，Provider Runtime Bindings（EC03）只提供私有调用映射和 Receipt 定位。Runtime 只消费并解释，不复制 Owner 私有状态映射。Tool Provider 与 Plugin Manager 的消费边界见 [F03.05 Tool Interface 与 Provider 集成设计](../F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)。

### 既有执行内核边界

现行 ca-runtime 的 RuntimeHost.v1、ProviderBinding、请求重放、Outcome 与执行期 Predicate 具有独立实现基线。Next 沿用结果和证据语义，业务 Skill 选择在宿主完成。SR-022 负责核对出入参、实现和证据。 详见[分仓证据](../../参考与审计/跨仓设计资产迁移与一致性审计.md)。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 历史修订者/模型未记录 | 原始设计全文 | 既有功能机制设计基线；逐章历史记录未建立 | 原文档未记录历史作者，本轮不臆造 | PR #1 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 第 1～8 章 | 归入对应 Feature 并补充外部能力边界 | 按 F04 归档，固定两种执行模式共用的 Action Boundary、Run 和 Owner Outcome 语义 | F04；SR-007；EC03/EC05；PR #1 |
| 2026-11-25 | 0.2.1 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.2 | Codex / GPT-6 | 既有执行内核边界 | 合并有效边界与分仓证据入口 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | 第 3、6、9 章 | 区分公开 Interface Package、Owner Contract Package 与 Provider Runtime Bindings 的权威边界 | 对齐 ca-client-tools v1.2.0 与 Owner v1alpha4 的实际发布结构 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | 第 3 章 | 明确 Provider Interface 与 Owner Contract 是两个 Callable/Schema 来源，MAS `mas::` 引用只从 Owner snapshot 解析 | 修正 Runtime 把 Owner Callable 误认为 Provider Interface Package 导出的歧义 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | 第 3 章 | 明确冻结 v1alpha5 Artifact 不携带 dependency snapshotDigest，Owner version pin 由 Provider sidecar / 部署配置提供 | 防止 Runtime 宣称逐 Skill 字节级依赖锁 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | 第 3 章 | 补充 provider.yaml interfaceSnapshotDigest 对 Provider Interface snapshot 的部署级校验 | 与 Owner sidecar 的部署 pin 一起闭合 Provider / Owner 两类依赖 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.4 | GPT-6.2（ChatGPT） | §3、§6、§8 | 明确冻结 v1alpha5 Capability ID 不进入运行时 Artifact，Runtime Scope 使用精确 Callable exports；补充 Reconcile internal-only sidecar 派发边界及验收 | 对齐 Compiler v2.1.0 frozen artifact schema 与 Owner v1alpha4 实际发布契约 | IR-006 · SR-015 · Issue #12 |
