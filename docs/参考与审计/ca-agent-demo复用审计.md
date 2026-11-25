# ca-agent-demo 复用审计

> 文档类型：既有实现审计与复用建议  
> 状态：审计快照；不是 Next 实现证明  
> 文档版本：0.1.0    
> 全局评审范围：继承根目录 Agent.md 的 review_scope    
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  
> 审计日期：2026-11-25  
> 主审基线：ca-agent-demo main 57e277ff9094dad93543df46910a12a1dbbaf560  
> 补充输入：PR #246 head 68a6f9e7723a0c2da1aebf5047c23ae96c5d237f（OPEN）、PR #249 head dfbcc33467a1ea3b6fa45d661ac2e77bfd71423a（OPEN）

## 1. 仓库状态与定位

- ca-agent-demo 是 Generic Agent Host 的 Python 参考实现，包含 Agent、Host、Runtime、Resident、Context、Tool 契约和 5GC 集成。
- 主线 README 将 5GC 定位为业务/集成示例，而不是 Host 身份；主线包含 src/ca_agent_host/、tools/、skills/、examples/ 和 pytest 测试。
- Python Distribution 为 ca-agent-host，导入包为 ca_agent_host，README 标注架构版本 0.4.0。
- PR #246 在开放分支增加通用 Provider loader / ToolComposition，但不是 main 已合并代码。
- PR #249 是 Plugin/Event 契约设计输入，不代表 Plugin Runtime 已实现。
- 结论：ca-agent-demo 是 Next 的主要 Python 代码和测试证据来源，但必须按文件和依赖逐项复用，不能整仓复制。

本文区分三类信息：证据表示已检查的仓库、文件或 PR 记录；判断表示基于证据的架构结论；建议表示 Next 的实施方向。本文没有重新执行 ca-agent-demo 全量测试套件。

## 2. 机制盘点与 Next 处理建议

| 机制 | Demo 现有位置/证据 | Next 建议 |
|---|---|---|
| Intent / Agent Model Boundary | agent/intent、agent/model_adapter.py、model_request.py、tests/unit/test_intent_ingress.py | 复用并简化；模型循环留在 Python Host |
| Formal Search / Grounding | agent/formal/search、grounding、operators、ranking、resolver、strategy | 复用候选与排序能力；改为 when 显式候选 + SKILL.md 无 when 候选 |
| Root/Skill Eligibility | agent/host/root_eligibility.py、routing.py、root_routing_profile.py | 复用通用排除/候选概念；移除部署级 Event→Root 业务路由 |
| LLM 歧义选择 | agent/host/routing.py、agent/semantic/chooser.py | 仅允许在精确候选集合内消歧，并验证返回的 Skill ID |
| Context / Observation | agent/context、runtime/observation | 复用来源/投影思路，简化 Provenance |
| Artifact 检查 | runtime/admission.py、compiler_artifact.py、compiler_skill.py、skill_assets.py | 只借鉴包结构与依赖检查；Next 不建立 Skill Admission，也不调用 Compiler Inspect/Verify |
| Compiler | skill_toolchain/compiler.py 中有 MockCompiler；真正 Compiler 在独立 Go 仓库 | MockCompiler 不能作为正式 Compiler；Next 运行时不调用 Compiler |
| Procedure Linker | runtime/linker.py、frozen.py、casl_adapter.py | 只评估必要的消费/执行适配，不复制 CA-SL 语言语义 |
| Runtime | runtime/engine.py（MockRuntime）、outcomes.py、evidence_wait.py、durable.py | 复用语义边界和测试；在 Next 建立简化的统一 Runtime |
| Tool Action Boundary | runtime/tool_contract.py、ToolContractRegistry、ToolBoundOperationBackend；tests/unit/test_unified_resident_action.py | 强复用候选；分发目标改为 Plugin tools Extension |
| Host/Resident Lifecycle | resident/host.py、service.py、invocation.py、delivery.py、ingress.py | 复用基础生命周期；避免复制 5GC 组合逻辑和过度恢复机制 |
| Run / Artifact Store | resident/run_store.py、artifact_store.py | 只复用 Demo 所需最小 Run 关联和 Host Artifact 托管 |
| Provider 集成 | integrations/ca_client_tools/provider_v2.py、mas_typed.py | 不携带 MAS 专用表和 Python Owner Adapter |
| 通用 Tool Plugin Loader | PR #246 的 providers/manifest、interface、process、runtime、backend、service、runtime_bindings 和 ToolComposition | 作为实现证据，吸收到唯一 Plugin Manager，不保留 Provider Manager |
| Event ingress/Delivery | PR #249 文档 | 只作为契约输入；必须服从 Skill-first 和统一 Plugin 机制 |
| 5GC SBI/Nsmf | integrations/fivegc、NsmfRunExecutor、Namf Relay | 不整体复制；按协议 Plugin、Host、Runtime、Owner 职责拆分 |

## 3. 与 Next 目标架构的主要差异

### 3.1 Event→Root 路由不是目标

Demo 当前有结构化 Event/Root Routing。Next 使用可选 Assurance Contract.when 做显式 Skill 选择；没有 when 的 Skill 通过 SKILL.md 语义候选。不得把现有路由表改名后带入 Next。

### 3.2 Agent-first / Skill-optional 不是目标

PR #249 的早期设计含 Agent 默认路径。Next 要求每个新业务 Event 先绑定 Skill；无候选时澄清或拒绝，不允许无 Skill 绑定的 Generic Agent fallback。

### 3.3 SkillCatalog 是 Next 新机制

Demo 的现有目录/缓存实现不能直接视为目标 SkillCatalog。Next 必须明确进程内不可变快照、when 程序驻留、每个 Event 独立求值、原子 generation 更新和 Invocation generation pinning。

### 3.4 Mock 名称不代表正式能力

MockCompiler 不是真正的 CA-SL Compiler；MockRuntime 也不证明 Next Runtime 已实现。Compiler 是独立 Go 工具链。Next 只消费其发布 Artifact，不在运行时执行编译或 Admission。

## 4. 选择性复用清单

| 源码范围 | 建议 | 处理原则 |
|---|---|---|
| agent/intent/、Model Adapter 与 Request 类型 | 复制并适配 | 移除 Demo 业务装配 |
| agent/formal/{search,grounding,operators,ranking} | 复制并适配 | 保留通用推理原语，调整 Skill 候选约束 |
| agent/host/root_eligibility.py、routing.py | 改造复用 | 只保留候选和排除模型，替换 Event→Root 选择 |
| agent/context/、runtime/observation/ | 复制并适配 | 保留来源和 Observation 模型，简化上下文装配 |
| published Artifact 读取与结构检查 | 选择性复用 | 去掉 Admission / Trust / Approval |
| 通用 Tool 契约校验与 Outcome/Evidence | 选择性复用 | 以 Interface Package 和 Owner Receipt 为准 |
| integrations/fivegc/、NsmfRunExecutor、Owner claims、业务补偿 | 不复制 | 业务集成不得进入通用 Core |
| MockCompiler、MockRuntime | 不作为最终实现 | 仅可作测试替身，不能冒充真实依赖 |

**优先复用/改造：** Python Agent/Model Adapter、Formal Search/Grounding/Ranking、Context Loader、Observation Provenance、Tool Contract Validation、Outcome/Evidence 语义、最小 Run/Invocation、Host ArtifactStore，以及 PR #246 的通用进程和 Interface Package Loader 思路。

**需要重构：** Skill 选择从结构化 Event→Root 映射改为 when + SKILL.md 候选；Tool dispatch 从 Provider 专属路径改为统一 Plugin Manager 的 tools Extension；重新划分 Runtime 与 Host；区分 Context 中 Event、Observation、Evidence 和模型文本的来源。

**禁止整块复制：** integrations/fivegc/、NsmfRunExecutor、5GC 专用路由和补偿、MockCompiler 作为真实 Compiler、MockRuntime 作为 Next 最终 Runtime、独立 Provider Manager 或第二 Tool Registry。

## 5. PR / Issue 证据与状态

| 记录 | 截至审计日状态 | 能证明 | 不能证明 |
|---|---|---|---|
| Issue #241 | OPEN | Tool 子系统切换任务 | 真实隔离 Scheme C 已通过 |
| PR #246 | OPEN，head 68a6f9e | 通用 Provider Loader、Interface Package Loader、Runtime-only bindings、单一 ToolComposition；合成 Owner G5 证据 | 真实 OpenAMSM Scheme C E2E、合并或生产资格 |
| Issue #235 | OPEN | 延后 Plugin ingress/delivery 范围 | Plugin Runtime 已实现 |
| PR #249 | OPEN，head dfbcc334，文档设计 | Event Contract、Plugin IPC/Manifest 的设计提案 | Plugin Runtime 或 T2/T3 已通过 |

PR #246 记录的 G5 为合成有状态 Owner，22 项测试通过；真实隔离 OpenAMSM Scheme C G6 仍为 NOT_RUN/BLOCKED，G7 为 PARTIAL。不得将 Synthetic G5 表述为真实 OpenAMSM E2E。

## 6. 使用限制与结论

本审计是代码和状态快照，不是全量测试报告。实施前必须重新读取 ca-agent-demo 的当前分支、PR 和源文件；任何复用都应在 Next 内独立运行测试。复用结论不授权直接修改 ca-agent-demo 或其他兄弟仓。

ca-agent-demo 为 Next 提供了可观的 Python 代码和测试资产，但 Next 的目标边界更简单：Python Core + 一个 Plugin Manager + 一个 Runtime Action Boundary + Core-owned SkillCatalog + 外部发布的 Skill Artifact。复用必须以测试和依赖审查为前提，不能把 Demo 既有 5GC 业务组合结构带入通用 Core。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 登记现有文档基线并纳入 SR 追踪 | 建立文档版本和需求追踪基线 | SR-002～SR-008 |
