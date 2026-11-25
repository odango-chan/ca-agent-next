# ca-agent-demo 复用审计

> 文档类型：代码复用与实现证据审计  
> 状态：实现参考快照；实施前需重新核对  
> 审计日期：2026-11-25  
> 主审基线：ca-agent-demo main 57e277ff9094dad93543df46910a12a1dbbaf560  
> 补充输入：PR #246（68a6f9e7723a0c2da1aebf5047c23ae96c5d237f，OPEN）、PR #249（dfbcc33467a1ea3b6fa45d661ac2e77bfd71423a，OPEN）

## 1. 审计结论

ca-agent-demo 是 Next Python Agent Core 的主要代码和测试证据来源，但不是可以整体复制的模板。应逐文件审计依赖和业务耦合，选择性复用 Python 模块；不得把 OpenAMSM/5GC 集成层、Mock Compiler 或 Mock Runtime 当作 Next 的最终实现。

本文区分三类信息：**证据**表示已检查的仓库、文件或 PR 记录；**判断**表示基于证据的架构结论；**建议**表示 Next 的实施方向。本文没有重新执行 ca-agent-demo 全量测试套件。

## 2. 仓库基线

- 主分支基线：57e277ff9094dad93543df46910a12a1dbbaf560。
- README 将项目定位为 Generic Agent Host 参考实现；Python Distribution 为 ca-agent-host，导入包为 ca_agent_host，README 标注架构版本 0.4.0。
- 主目录包含 src/ca_agent_host/、tools/、skills/、examples/ 和 pytest 测试。
- 当前 README 将通用 Agent Host 架构作为主实现依据，将 5GC 定位为业务集成示例，而不是 Host 身份。
- 复用方向是从 Python 实现中挑选模块迁入 Next；不从 ca-agent 的 Go 源码开始。

## 3. 机制盘点与 Next 处理方式

| 机制 | Demo 中的实现证据 | Next 处理建议 |
|---|---|---|
| Agent / Model 边界 | agent/intent/、agent/model_adapter.py、model_request.py 及对应 ingress 测试 | 复用并简化 Python Model Adapter；Model Loop 留在 Host/Agent |
| Formal 搜索与计划绑定 | agent/formal/search、grounding、operators、ranking、resolver、strategy | 复用检索、grounding 和排序原语；选择语义改为 when 显式候选 + SKILL.md 无条件语义候选 |
| Root Eligibility / Routing | agent/host/root_eligibility.py、routing.py、root_routing_profile.py | 只复用候选、排除和消歧结构；删除部署侧 Event→Root 路由模型 |
| LLM 歧义选择 | SkillRoutingChooser、agent/semantic/chooser.py | 只允许在精确候选集合内消歧，并校验返回的 Skill ID |
| Context / Observation | agent/context/、runtime/observation/ | 复用来源与只读观察的类型设计，按 Next 简化 |
| 发布 Artifact 加载 | runtime/admission.py、compiler_artifact.py、compiler_skill.py、skill_assets.py | 只复用基本格式、文件、引用和本地依赖检查；不迁移 Skill Admission、信任或审批机制 |
| Tool / Provider | PR #246 的通用 Provider Loader、Interface Package Loader、Runtime-only bindings | 复用已验证的通用调用实现；Next 统一收敛到唯一 Plugin Manager 的 tools Extension |
| Run / Artifact Store | Demo 中的最小 Run、Artifact 管理实现 | 评估后选择性复用，不引入生产级分布式存储 |
| Owner Receipt / Evidence | Outcome、Receipt、Commit Proof 相关实现与测试 | 保留权威 Owner 结果语义；UNKNOWN 不得被提升为 COMMITTED |
| 5GC 专用集成 | integrations/fivegc/、NsmfRunExecutor 等 | 不整体复制，不进入 Agent Core |

## 4. 与 Next 目标架构的差异

### 4.1 Event 路由不是 Skill Resolver

Demo 的 root_routing_profile.py 使用部署侧 StructuredEventRoute，结合 Contract Version、Message Type、Request Type 选择 Root。它不是目标中的 Skill 包自声明适用性机制。

Next 对新 Event 先评估可选 assurance/contract.yaml.when；显式匹配集合优先。没有显式匹配时，只对未声明 when 的 Skill 使用 SKILL.md 语义选择。不得新增 Domain Contract Package、业务路由表或 Event→Skill 映射表。

### 4.2 Plugin 与 Tool 管理需要统一

既有 PR #246 的 Provider Manager / ToolComposition 不能与 PR #249 提出的 Plugin Manager 并列成为两个永久管理器。Next 只有一个 Plugin Manager；Tool 是 Plugin 导出的 Operation，Tool Plugin 只是导出 tools Extension 的 Plugin。

### 4.3 Catalog 与 Compiler 边界不同

Next 的 SkillCatalog 由 Python Core/Host 拥有。Agent 只消费已发布 Skill 包，不调用 Compiler，也不建立 Skill Admission。Demo 中的 MockCompiler、MockRuntime 不构成真实 Compiler 或 Next Runtime 的验收证据。

## 5. 选择性复用清单

| 源码范围 | 建议 | 处理原则 |
|---|---|---|
| agent/intent/、Model Adapter 与 Request 类型 | 复制并适配 | 移除 Demo 业务装配 |
| agent/formal/{search,grounding,operators,ranking} | 复制并适配 | 保留通用推理原语，调整 Skill 候选约束 |
| agent/host/root_eligibility.py、routing.py | 改造复用 | 只保留候选和排除模型，替换 Event→Root 选择 |
| agent/context/、runtime/observation/ | 复制并适配 | 保留来源和 Observation 模型，简化上下文装配 |
| published Artifact 读取与结构检查 | 选择性复用 | 去掉 Admission / Trust / Approval |
| 通用 Tool 契约校验与 Outcome/Evidence | 选择性复用 | 以 Interface Package 和 Owner Receipt 为准 |
| integrations/fivegc/、NsmfRunExecutor | 不复制 | 业务集成不得进入通用 Core |
| MockCompiler、MockRuntime | 不作为最终实现 | 仅可作测试替身，不能冒充真实依赖 |

## 6. PR 与测试证据

| 记录 | 截至审计日状态 | 能证明 | 不能证明 |
|---|---|---|---|
| Issue #241 | OPEN | Tool 子系统切换任务 | 真实隔离 Scheme C 已通过 |
| PR #246 | OPEN，head 68a6f9e | 通用 Provider Loader、Interface Package Loader、Runtime-only bindings、单一 ToolComposition；合成 Owner G5 证据 | 真实 OpenAMSM Scheme C E2E、合并或生产资格 |
| Issue #235 | OPEN | 延后 Plugin ingress/delivery 范围 | Plugin Runtime 已实现 |
| PR #249 | OPEN，head dfbcc334，文档设计 | Event Contract、Plugin IPC/Manifest 的设计提案 | Plugin Runtime 或 T2/T3 已通过 |

PR #246 记录的 G5 为合成有状态 Owner，22 项测试通过；真实隔离 OpenAMSM Scheme C G6 仍为 NOT_RUN/BLOCKED。不得将合成 G5 表述为真实 OpenAMSM E2E。

## 7. 使用限制

本审计是代码和状态快照，不是全量测试报告。实施前必须重新读取 ca-agent-demo 的当前分支、PR 和源文件；任何复用都应在 Next 内独立运行测试。复用结论不授权直接修改 ca-agent-demo 或其他兄弟仓。
