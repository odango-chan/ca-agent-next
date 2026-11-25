# ca-agent-demo 复用审计

> 文档类型：既有实现审计与复用建议  
> 状态：审计快照；不是 Next 实现证明  
> 审计日期：2026-11-25  
> 主审计来源：ca-agent-demo main 57e277ff9094dad93543df46910a12a1dbbaf560  
> 补充输入：PR #246（OPEN）和 PR #249（OPEN）

## 1. 仓库状态与定位

- ca-agent-demo 是 Generic Agent Host 的 Python 参考实现，包含 Agent、Host、Runtime、Resident、Context、Tool 契约和 5GC 集成。
- 主线 README 将 5GC 定位为业务/集成示例，而不是 Host 身份。
- 主线已有 Python 模块、examples、tools 和 pytest 测试。
- PR #246 在开放分支增加通用 Provider loader / ToolComposition，但不是 main 已合并代码。
- PR #249 是 Plugin/Event 契约设计输入，不代表 Plugin Runtime 已实现。
- 结论：ca-agent-demo 是 Next 的主要 Python 代码和测试证据来源，但必须按文件和依赖逐项复用，不能整仓复制。

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

## 3. 与 Next 目标的主要差异

### 3.1 Event→Root 路由不是目标

Demo 当前有结构化 Event/Root Routing。Next 使用可选 Assurance Contract.when 做显式 Skill 选择；没有 when 的 Skill 通过 SKILL.md 语义候选。不得把现有路由表改名后带入 Next。

### 3.2 Agent-first / Skill-optional 不是目标

PR #249 的早期设计含 Agent 默认路径。Next 要求每个新业务 Event 先绑定 Skill；无候选时澄清或拒绝，不允许无 Skill 绑定的 Generic Agent fallback。

### 3.3 SkillCatalog 是 Next 新机制

Demo 的现有目录/缓存实现不能直接视为目标 SkillCatalog。Next 必须明确进程内不可变快照、when 程序驻留、每个 Event 独立求值、原子 generation 更新和 Invocation generation pinning。

### 3.4 Mock 名称不代表正式能力

MockCompiler 不是真正的 CA-SL Compiler；MockRuntime 也不证明 Next Runtime 已实现。Compiler 是独立 Go 工具链。Next 只消费其发布 Artifact，不在运行时执行编译或 Admission。

## 4. PR / Issue 证据与状态

截至审计时点：

- ca-agent-demo PR #246：OPEN；通用 Provider loader 位于开放分支，不能当作 main 已合并实现。
- ca-agent-demo PR #249：OPEN；主要是 Plugin/Event 文档设计输入。
- PR #246 记录 G5 synthetic Owner 22 项测试通过；真实隔离 Scheme C G6 仍为 NOT_RUN/BLOCKED，G7 为 PARTIAL。
- PR #246 的 Synthetic G5 不等于真实 OpenAMSM E2E，不得据此声明真实 Owner 通过。

本审计不是对 Demo 全量测试套件的重新执行。测试状态只引用对应 PR/测试文件的现有证据。

## 5. 建议复用清单

**优先复用/改造：**
- Python Agent/Model Adapter。
- Formal Search、Grounding、Ranking 等通用推理原语。
- Context Loader 和 Observation Provenance 类型。
- Tool Contract Validation 和 Outcome/Evidence 语义。
- 最小 Run/Invocation 和 Host ArtifactStore 机制。
- PR #246 的通用进程/Interface Package loader 思路。

**需要重构：**
- Skill 选择从结构化 Event→Root 映射改为 when + SKILL.md 候选。
- Tool dispatch 从 Provider 专属路径改为统一 Plugin Manager 的 tools Extension。
- Runtime 和 Host 的职责边界。
- Context 中 Event、Observation、Evidence 和模型文本来源区分。

**禁止整块复制：**
- integrations/fivegc/。
- NsmfRunExecutor、Owner claims、业务补偿和 5GC 专用路由。
- MockCompiler 作为真实 Compiler。
- MockRuntime 作为 Next 最终 Runtime。
- 独立 Provider Manager 或第二 Tool Registry。

## 6. 结论

ca-agent-demo 为 Next 提供了可观的 Python 代码和测试资产，但 Next 的目标边界更简单：Python Core + 一个 Plugin Manager + 一个 Runtime Action Boundary + Core-owned SkillCatalog + 外部发布的 Skill Artifact。复用必须以测试和依赖审查为前提，不能把 Demo 既有 5GC 业务组合结构带入通用 Core。
