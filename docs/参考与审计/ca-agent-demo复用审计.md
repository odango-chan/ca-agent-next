# ca-agent-demo 复用审计

> 文档类型：既有实现审计与复用建议  
> 文档版本：0.2.1  
> 状态：基于 main 57e277ff 和已合并 PR #219 的静态源码/证据审计；本轮未重新执行外部仓全量测试  
> 审计日期：2026-11-25  
> 主审基线：[ca-agent-demo main 57e277ff](https://github.com/odango-chan/ca-agent-demo/tree/57e277ff9094dad93543df46910a12a1dbbaf560)  
> 补充 PR：[#219 MERGED](https://github.com/odango-chan/ca-agent-demo/pull/219)、[#246 OPEN](https://github.com/odango-chan/ca-agent-demo/pull/246)、[#248 OPEN/Draft](https://github.com/odango-chan/ca-agent-demo/pull/248)、[#249 OPEN](https://github.com/odango-chan/ca-agent-demo/pull/249)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：不要求把 ca-agent-demo 整仓迁入 Next；不把参考仓 Development PASS 当作 Next PASS 或 Production Qualification

## 1. 仓库状态与定位

ca-agent-demo 是 Python Generic Agent Host 的参考实现，包含 Agent、Host、Runtime、Resident、Context、ArtifactStore、Tool Contract、Provider Adapter 和 OpenAMSM/5GC Development 集成。它是 Next 的主要 Python 代码和测试证据来源，但不是 Next 目标架构的权威文档；目标设计以本仓 F01～F06、F03.05 和规范为准。

主线固定 SHA 为 57e277ff9094dad93543df46910a12a1dbbaf560。PR #219 已合并，提供真实 SCP、Provider、N2/PFCP session correlation 的 Development 集成证据；其报告明确没有 durable Owner mutation Receipt / exact-original Reconcile 的完整证明，不声明 Production Qualification。

当前未合并 PR：
- #246：通用 Provider v1.1.0 Runtime cutover，OPEN。
- #248：Plugin ingress/delivery 契约与 T2 Acceptance，OPEN / Draft。
- #249：Agent-first Event Contract 和 OpenAMSM T3 边界，OPEN。

上述 OPEN PR 不计入 main 实现。本文核对源码路径和历史 PR 证据，没有重新运行 ca-agent-demo 全量测试。

## 2. 机制盘点与 Next 处理建议

| 机制 | main 代码 / 测试证据 | Next 建议 |
|---|---|---|
| Agent / Model Boundary | agent/intent、agent/model_adapter.py、model_request.py | 复用 Python Model Adapter 和结构化 Action Proposal；模型不直接调用 Plugin |
| Formal Search / Grounding / Ranking | agent/formal/search、grounding、operators、ranking、resolver、strategy | 复用通用候选和排序原语；候选集合必须由 Next Skill Resolver 精确约束 |
| Root / Skill Eligibility | agent/host/root_eligibility.py、routing.py、root_routing_profile.py | 只借鉴排除/候选结构；Next 不复制 Event→Root 业务路由 |
| Context / Observation | agent/context/base.py、loader.py、observation_resolver.py、projection.py、requirements.py | 选择性复用来源、scope、freshness、只读 Observation 和显式模型投影；不复制完整 Planning Context 工作流 |
| Skill Context | agent/host/skill_context.py；tests/unit/test_skill_context.py | 复用精确 Skill identity、按需读取声明 reference 的思路；Next 不预加载所有 references |
| ArtifactStore | resident/artifact_store.py；tests/unit/test_host_artifact_store.py | 复用 Host-owned 生命周期概念；不复制 `artifact:sha256` 内容寻址身份；Host→Tool 必须遵循独立的 ca-host.artifact-store/v1 随机 ref / 传输摘要契约 |
| Tool Contract / Outcome | runtime/tool_contract.py、ToolContractRegistry、ToolBoundOperationBackend；tests/unit/test_unified_resident_action.py | 复用契约校验与统一 Action Boundary 思路；Callable 权威改为 F03.05 Tool Interface Package |
| Runtime / Wait / Evidence | runtime/engine.py、outcomes.py、evidence_wait.py、durable.py | 只复用必要的状态语义和测试；Next 不复制复杂 Admission 或生产级恢复层 |
| Provider Adapter | integrations/ca_client_tools/provider_v2.py、mas_typed.py | 作为 Provider v2 参考；必须经过唯一 Plugin Manager 的 ProviderV2 Driver |
| 5GC SBI / Nsmf | integrations/fivegc、NsmfRunExecutor、Namf Relay | 不整块复制；按 Event Plugin、Host、Runtime、Tool Plugin、Owner 拆分 |
| 通用 Provider Loader | PR #246 中的 manifest/interface/process/runtime/backend/service/runtime_bindings/ToolComposition | 仅作为 OPEN PR 候选设计，不计入 main；合并后再逐文件复核 |
| Event ingress / Delivery | PR #248/#249 文档 | 只作为候选契约输入；必须服从 Next Plugin Package/IPC 和 Skill-first 边界 |

### 2.1 Context / Artifact 的选择性复用

当前 main 已有以下可定位资产：

- Context Fact / Resolver / Projection：agent/context/base.py、loader.py、observation_resolver.py、projection.py、requirements.py。
- Skill Context：agent/host/skill_context.py。
- Host ArtifactStore：resident/artifact_store.py。
- 对应测试：test_context_loader.py、test_context_observation_resolver.py、test_skill_context.py、test_host_artifact_store.py。

Next 可复用事实来源、只读 Observation、显式模型可见性、精确 Skill identity 和 Host-owned Artifact ref 的概念；不直接复用其完整 PlanningContext / ContextRequirement / ContextOffer / Candidate Strategy 工作流。Next Demo 不新增独立 Planning Runtime 或 Context Service。

ca-agent-demo ArtifactStore 使用 `artifact:sha256` 内容寻址，属于该 Python 参考实现的内部模型，Next 不直接复制。它与 `ca-host.artifact-store/v1` 不同：v1 使用 Host CSPRNG 生成的随机 `art_...` opaque reference，并要求 Host/Provider 对精确传输字节执行 SHA-256 校验；摘要不进入 reference，不用于内容寻址或去重。Next 只实现已冻结 v1 wire contract 要求的传输校验，不增加额外 package hash、签名或 Trust Registry。

**过期注释说明：** ca-agent-demo main `57e277ff` 的 `resident/artifact_store.py` 注释中仍称 `ca-host.artifact-store/v1` “尚未发布”；该状态文字已过期。当前 ca-agent main `447d0cc` 已有 Host 实现和 P1 证据，ca-client-tools v1.2.0 已有 Provider consumer 与 fixtures。本轮只修正 Next 中央审计，不修改 ca-agent-demo 源仓。

## 3. 与 Next 目标架构的主要差异

### 3.1 Event→Root 路由不是目标

Demo 有结构化 Event/Root Routing。Next 使用可选 Assurance Contract.when 做显式 Skill 选择；没有 when 的 Skill 通过 SKILL.md 语义候选。不得把现有路由表改名后带入 Next。

### 3.2 Skill-first 是 Next 的硬边界

新 Event 必须先绑定 Skill。Continuation 恢复原 Run，不重新选择。无候选时澄清或拒绝，不允许无 Skill 绑定地回退到 Generic Agent。PR #249 中早期 Agent-first / Skill-optional 方案不能直接作为 Next 目标。

### 3.3 SkillCatalog 是 Next 的独立设计

Demo 现有目录/缓存实现不能直接视为目标 SkillCatalog。Next 明确进程内不可变快照、已发布 Artifact、when 程序驻留、每个 Event 独立求值、原子 generation 更新和 Invocation generation pinning。具体以 F02 为准。

### 3.4 Compiler / Runtime Mock 不是正式实现

MockCompiler 不能作为真实 CA-SL Compiler；MockRuntime 不能证明 Next Runtime 已实现。Compiler 是独立 Go 工具链，Next 只消费发布 Artifact，不在运行时调用 Compiler 或做 Skill Admission。

### 3.5 Provider v2 不等于第二个 Manager

ca-agent-demo 中 Provider Adapter 和开放 PR #246 的通用 Provider Loader 仅作为实现参考。Next 仍只有一个 Plugin Manager；Tool 是 Plugin 的 Operation，不引入 Provider Manager、Tool Registry 或 Codec Manager。

## 4. 选择性复用清单

| 源码范围 | 建议 | 处理原则 |
|---|---|---|
| agent/intent、Model Adapter 与 Request 类型 | COPY + ADAPT | 移除 Demo 业务装配 |
| agent/formal/search、grounding、operators、ranking | COPY + ADAPT | 保留通用推理原语，严格限制 Skill 候选 |
| agent/host/root_eligibility.py、routing.py | ADAPT | 只保留候选和排除模型，替换 Event→Root 选择 |
| agent/context、runtime/observation | COPY + ADAPT | 保留来源/只读 Observation，简化 Context 装配 |
| agent/host/skill_context.py | COPY + ADAPT | 精确 Skill identity 和按需 reference |
| resident/artifact_store.py | REVIEW + REIMPLEMENT | 保留 Host-owned Artifact 生命周期；排除内容寻址/SHA-256 |
| Tool Contract Validation / Outcome/Evidence | COPY + ADAPT | 以 Tool Interface Package 和 Owner Contract 为准 |
| integrations/ca_client_tools/provider_v2.py | REVIEW | 适配到唯一 Plugin Manager；不得引入第二 Manager |
| integrations/fivegc、NsmfRunExecutor、Owner claims、业务补偿 | DO NOT COPY | 业务集成不得进入通用 Core |
| MockCompiler / MockRuntime | TEST DOUBLE ONLY | 不能冒充真实 Compiler / Next Runtime |
| PR #246 / #248 / #249 | NOT_MAIN | 未合并前仅为候选，不计入当前实现 |

**优先复用/改造：** Python Model Adapter、Formal Search/Grounding/Ranking、Context Fact/Observation、Skill Context Loader、Tool Contract Validation、Outcome/Evidence 语义和最小 Run/Invocation。

**禁止整块复制：** integrations/fivegc、NsmfRunExecutor、5GC 专用路由/补偿、ArtifactStore 内容寻址实现、完整 PlanningContext / ContextOffer 体系、MockCompiler/MockRuntime 作为正式依赖、第二 Provider Manager。

## 5. PR / Issue 证据与状态

| 记录 | 截至审计日状态 | 能证明 | 不能证明 |
|---|---|---|---|
| PR #219 | MERGED；main 57e277ff | Development H1/H2/H3 真实 SCP、Provider、N2/PFCP 相关证据；PR 报告列出 2120 offline tests | durable Owner mutation Receipt / exact-original Reconcile 完整证明；Production Qualification |
| PR #246 | OPEN，head 68a6f9e | 通用 Provider Loader、Interface Package Loader、Runtime-only bindings、单一 ToolComposition 的候选实现 | main 已切换；Next Plugin Manager 已实现 |
| PR #248 | OPEN / Draft，head 7c18318 | Plugin ingress/delivery 最小契约和 T2 Acceptance 候选 | Plugin Runtime、T2/T3 或 Next E2E 已通过 |
| PR #249 | OPEN，head dfbcc334 | Agent-first Event Contract 和 OpenAMSM T3 边界候选设计 | Next 已接受 Skill-optional / Agent-first 模式 |
| Issue #241 | OPEN | Tool 子系统切换任务 | 真实隔离 Scheme C 已由 Next 验收 |

PR #219 的限制必须保留：真实 Development Provider/N2/PFCP correlation 不是 durable Owner Receipt/Commit Proof。Owner 侧 v1alpha4 和 Scheme C 证据属于 env-openamsm，不自动补齐 ca-agent-demo 或 Next Runtime 的 Owner commit boundary。

## 6. 使用限制与结论

ca-agent-demo 为 Next 提供了可观的 Python 代码和测试资产，但 Next 目标更简单：Python Core + 一个 Plugin Manager + 一个 Runtime Action Boundary + Core-owned SkillCatalog + 外部发布 Skill Artifact。

复用必须以当前 main SHA、精确文件、依赖和测试为依据。外部仓 PASS 不能计入 Next PASS；OPEN PR 不得计入 main。任何代码迁移必须由 READY SR 授权并在 Next 重新测试。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 历史修订记录未提供 | 全文 | 原始 ca-agent-demo 复用审计 | 作为 Next 参考实现输入 | SR-002～SR-008 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 更新 PR #219 合并证据、#246/#248/#249 OPEN 状态；加入 Context/Artifact 源码审计和 SHA-256 不复用决策 | 避免把历史 G5/PR 提案误报为当前 main 或 Next PASS | Issue #12；SR-020 |
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §2、§4～6 | 区分 ca-agent-demo 内容寻址 ArtifactStore 与 ca-host.artifact-store/v1 随机引用/传输摘要；记录源仓旧注释已过期 | 防止把参考实现内部模型误当成当前 Provider/Host wire contract | Issue #12；SR-010 |
