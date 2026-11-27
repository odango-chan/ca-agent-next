# SR-032：SKILL 作者规范、Node 拆分与注释原则

> 文档类型：软件需求（SR）  
> SR 版本：0.1.12  
> 状态：**DRAFT（中央作者规范已形成设计候选，待独立设计评审；实施 NOT_READY）**  
> 创建日期：2026-11-27  
> 修订日期：2026-11-27  
> 上游需求：IR-008（关联 IR-003）  
> 功能：EC01 / F01 / F02 / F03 / F04 / F05 / F08 / F09（作者规范由 EC01 维护；Host、Importer、Runtime、Compiler、Studio 消费）  
> 设计依据：[EC01 CA-SL 与 Skill 作者体系架构](../架构设计/外部能力域/EC01-CA-SL与Skill作者体系架构设计.md) v0.2.0；[CA-SL 1.6.0 完整语言规范](../规范/CA-SL%201.6.0完整语言规范.md) v0.2.2；[SKILL 作者规范](../规范/SKILL作者规范.md) v0.1.9  
> 目标仓：odango-chan/ca-agent-next（仅中央设计和规范）  
> 上游来源仓：odango-chan/ca-skills，固定 main 780497a2918ad3e7bdff554ab64b0ba627e867e0  
> 关联 Issue：[ca-agent-next #49](https://github.com/odango-chan/ca-agent-next/issues/49)、父级迁移 Issue #12、CA-SL 设计 Issue #40  
> 固定设计基线：4873608f5ca854a6bb47cf1a83cb9214da4ae202
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：不冻结 Compiler Build / Artifact wire DTO、Plugin IPC 或生产级 Script sandbox；不授权 ca-skills、Compiler、Studio、Runtime 或其他兄弟仓实施；不声称 CA-SL 1.6.0 Release、Host Script Execution 产品实现、产品验收或 E2E PASS。

## 1. 目标

把 ca-skills 已整理的 Skill 作者经验迁移并收敛为 Next 的唯一中央作者规范，使作者、评审者和 Skill Studio AI Authoring 对以下事项有统一、可执行的判断依据：

- 什么行为应成为 Skill，什么应保留为公开 Capability，什么属于 Agent routing；
- Procedure Node 何时拆分、何时合并，以及一个 Node 的 Operation / Observation 边界；
- Precondition、Operation、Observation、Postcondition 四阶段的职责；
- YAML 注释应解释什么、不能承担什么；
- SKILL.md、Package 根目录共享 schemas/、scripts/、references/、assets/ 与可选 Assurance 的组织和所有权；
- LLM 通过 Host Resource Read 读取共享资源、通过同一 Host Script Runner 调用全部登记 transform / predicate Script 的边界；
- Capability-only、显式 arguments、when、Evidence 和 UNKNOWN 的作者约束；Skill 层不定义 Wait / await / polling。

本 SR 是中央文档迁移与规范设计，不是 ca-skills、Compiler、Studio 或 Runtime 的代码实施授权。

## 2. 来源基线与迁移范围

ca-skills 固定源提交：780497a2918ad3e7bdff554ab64b0ba627e867e0。

迁移来源包括：

- docs/authoring.zh-CN.md 与 docs/authoring.md；
- docs/authoring-model.md；
- docs/project-layout.md 与 docs/schema-ownership.md；
- .agents/skills/create-connectionagent-skill/SKILL.md；
- .agents/skills/create-connectionagent-skill/references/skill-granularity.md 与 authoring-syntax.md；
- Create / Modify / Release MAS Skill 的实际 Procedure 样本。

原中文作者指南和作者模型已在 Next 历史区归档。本轮再补齐英文指南、Skill Granularity、Authoring Syntax、Package Layout、Schema Ownership 和 Create Skill 工作流的只读原文。每份源文记录固定 commit 和 blob SHA。

特别区分：

1. 旧 Skill Granularity 说明的是 Skill package 与 Capability / routing policy 的边界，不是 Procedure Node 拆分规则。
2. 已核对的旧作者文档没有独立、完整的 YAML 注释规范；注释原则属于本次 Next 新增设计，不伪称为旧文档原文。
3. 旧 v1alpha5 语法、目录和 Callable 身份仅作为历史证据，不进入新版规范示例。

## 3. 设计范围

### 3.1 作者规范

新增《SKILL 作者规范》，并明确其与 CA-SL 1.6.0 语言规范的权威边界：语言规范定义原有 Procedure / Node / routes / arguments / PredicateSet 结构、Package 根目录共享资源、Script Registry、Script 输入输出 / Evidence / 错误语义和 Host Script Execution；作者规范定义资源组织、粒度、表达、注释和质量要求。不得为作者新增 Wait / await / polling 语法。

### 3.2 Skill 与 Capability 粒度

保留可复用产品 / 领域 Skill 的原则；原始 Provider 操作、环境适配和无独立业务语义的 READ / MUTATION 保留为 Capability；routing 由 Agent 负责；禁止一 Tool Call 一个 Skill。

### 3.3 Node 粒度

一个业务 Node 表达一个主要业务动作，最多一个 Operation（公开 Capability 或纯本地 Script），可带一个直接相关的 READ Observation 和本动作的前后置 Predicate。

必须拆分：两个不同 Operation Capability、独立业务提交边界、具有独立生命周期 / 权威来源 / Correlation 且需要独立消费的证据确认边界，或需要执行独立业务动作的恢复路径。异步完成不构成作者 Node；等待、轮询和恢复由 Operation / Host Runtime 负责。

应保持合并：同一 Capability 内部的 Provider / HTTP / SBI / NAS / N2 / PFCP 子步骤；同一阶段的多个 Predicate；仅需通过 routes 跳转的 Outcome 分支；同一动作的直接 Observation / Postcondition 确认；简单参数映射。

允许最终 Postcondition-only Node、独立 Observation-only Node 和有明确边界的纯 Script Node；禁止 start-only、reconcile-only、HTTP-only、Provider handler-only、单 Predicate Node。

### 3.4 注释

注释解释 why、业务上下文、非显然映射和固定来源；不得替代类型、Schema、参数、Predicate、Evidence、Effect、Outcome、routes、重试或权限契约。注释不得含密钥、用户数据或临时运行时 ID。复杂背景放 references，不逐行解释 YAML。

### 3.5 共享资源与 Script Execution

schemas/、scripts/、references/、assets/ 位于 Skill Package 根目录，不依赖 assurance/ 是否存在。Schema 使用 YAML 1.2 表示 JSON Schema 数据模型；Script 由 scripts/manifest.yaml 登记稳定 Script ID、精确包内入口、purpose、输入/输出 Schema。LLM 通过 Host Resource Read 按需读取当前 Package snapshot 的共享文本资源，并通过 Host-owned host.skill-script.execute system Capability 调用当前 Skill Registry 中登记的全部 transform / predicate Script；LLM、Procedure 与 Predicate 共用同一 Script Runner，不设置逐脚本标记或额外 Host 开关。Predicate Script 的直接 LLM 调用不产生 Evidence 或 Assurance Outcome。模型不得提交代码、路径、模块、函数、Evidence 或命令。Assurance Procedure / Predicate 与 LLM 使用同一脚本字节、Registry 和 Schema；脚本不得产生外部副作用。

### 3.6 AI Authoring

F09 的 AI Authoring 必须使用同一作者规范和完整正向示例生成、检查 Change Set；通过 F05 host.skill-resource.read 读取共享 Schema / Script 作为上下文，但当前 Procedure-only Change Set 只修改 assurance/procedure.yaml，并可引用已有 Script ID，不得修改 schemas/、scripts/ 或 scripts/manifest.yaml。不得生成 Wait / await / polling，不得通过注释补足机器语义，不得暴露 Callable / backendOperationId，不得机械拆分 Node。Apply 后仍须通过同一 1.6.0 Compiler gate；本 SR 不宣称现有 Studio 已实现。

## 4. 非目标

- 不冻结 Compiler Build / Artifact wire DTO、Plugin IPC、Script Runner 的具体进程实现或生产级沙箱 / Admission；这些由对应 Owner 的后续设计与实施 SR 冻结。
- 不支持 v1alpha5 / v1alpha6 兼容、双轨、自动迁移或旧包 fallback。
- 不修改 ca-skills、ca-skill-compiler、ca-skill-studio-demo 或其他兄弟仓。
- 不实现注释 Linter、Node 自动拆分器或新的 AI Authoring Runtime。
- 不把生产级 Admission、Trust、签名、额外 package digest 或完整 DFX 纳入 Demo。
- 不将文档设计评审等同产品发布、代码实现或 E2E PASS。

## 5. 依赖与边界

| 类型 | 依赖 | 影响 |
|---|---|---|
| 设计依赖 | CA-SL 1.6.0 v0.2.0 / SR-029；SKILL 作者规范 v0.1.8 | 原有 Node / routes / arguments / PredicateSet 语法、Capability 绑定、四阶段、共享资源根目录、Script Registry、Script I/O / Evidence / 错误契约、Host Resource Read / Script Execution 和 when 语义必须一致；Skill 层无 Wait / await / polling；本 SR 不冻结 Compiler wire API |
| 历史来源 | SR-023 / ca-skills v1alpha5 | 只用于来源核对和历史归档 |
| 消费者设计 | F01 / F02 / F03 / F04 / F05 / F08 / F09；SR-004 / SR-007 / SR-016 | Host Model Loop、Importer、Plugin Manager、Runtime Action Boundary、Host Resource Read、完整 Script Registry、Compiler / Bundle 和 AI Authoring 必须消费同一共享资源与 Script Execution 契约；现有产品实现状态不自动变化 |
| 外部发布依赖 | ca-skills 1.6.0 正式 Schema / Golden / Release | 正式发布前，本规范与语言稿均保持设计候选，不声称产品可执行 |
| 实施边界 | ca-agent-next | 本 SR 的目标仓仅为中央文档；如未来需要改动 ca-skills 或 Studio，另建目标仓实施 SR |

## 6. 验收条件

| AC | 验收要求 | 证据 |
|---|---|---|
| AC-032-01 | 作者指南、作者模型、Skill Granularity、Authoring Syntax、Package Layout、Schema Ownership、创建工作流和实际 Skill 样本均有固定源路径、commit / blob SHA 和迁移裁决 | 作者规范 §12、历史归档文件、恢复清单 |
| AC-032-02 | Skill package 粒度与 Node 粒度分开定义；Skill / Capability / Agent routing 边界明确 | 作者规范 §2、§6 |
| AC-032-03 | Node 拆分与合并规则严格符合 1.6.0 原有四阶段顺序、每种阶段最多一个、Operation / Observation Capability 边界和静态 DAG；Outcome-only 路由不得触发机械拆分；异步等待不成为作者 Node；Create / Modify / Release 样本只用于结构性裁决 | 作者规范 §5～§6.6；CA-SL 1.6.0 §6；固定源 Procedure 样本 |
| AC-032-04 | 注释规则区分解释性内容与机器执行契约，给出明确正反例；注释示例不伪装成可构建 Procedure；不把旧资料未定义的规则伪称为迁移原文 | 作者规范 §7.5、§12 |
| AC-032-05 | Package 文件职责、Schema 所有权、Capability-only、显式 arguments、when、Evidence / UNKNOWN 与 1.6.0 设计一致；明确 Skill 层不定义 Wait / await / polling，异步由 Operation / Host Runtime 负责 | 作者规范 §3～§5、§8～§10；CA-SL 1.6.0 §2、§5、§6、§10～§11 |
| AC-032-06 | F09 明确 AI Authoring 必须遵守同一作者规范，并保留用户确认和 Compiler gate | F09 §9.3 |
| AC-032-07 | IR、功能树、SR 索引、实施状态、文档目录、迁移审计和修订记录完整互链；不误报 1.6.0 Release / 实施 / E2E 状态 | 本 SR、各治理索引、PR 静态检查 |
| AC-032-08 | Procedure.inputs 只绑定精确 context SourcePath；Capability / Script arguments 使用具名映射，Predicate arguments 与参数签名有序对应；Node 输出只引用 NodeId.operation.output / NodeId.observation.output；不定义 wait.output；作者规范不得发明正式语言 Schema 未冻结的参数结构 | 作者规范 §4.2；CA-SL 1.6.0 §6.1～§6.3 |
| AC-032-09 | 无 assurance/ 的 Skill 仅 LLM-guided，仍可携带并使用共享资源；存在 assurance/ 时所有必需文件与静态语义必须完整有效，不得静默降级；Skill 层无 Wait / await / polling 语法 | 作者规范 §3、§5；CA-SL 1.6.0 §2、§10 |
| AC-032-10 | schemas/、scripts/、references/、assets/ 位于 Skill Package 根目录，不受 assurance/ 可选性影响；Schema / Script 路径相对 Package 根目录；Schema YAML 源与 JSON Schema G.4 语义明确；同一资源不在 assurance/ 复制 | CA-SL 1.6.0 §2、§5、§8；作者规范 §3～§4；Package 格式规范 §2～§4 |
| AC-032-11 | Script Registry 精确登记 Script ID / file / entrypoint / purpose / I/O Schema；LLM 可调用全部已登记 transform / predicate Script，Procedure / Predicate 通过同一 Script Runner 调用；补齐 arguments → JSON input、Predicate Evidence projection / evidenceUsed、异常 / timeout / output invalid 诊断；无逐脚本 LLM 标记或额外 Host 开关；禁止模型提交代码/路径/命令和脚本外部副作用 | CA-SL 1.6.0 §8；F03 / F04 / F05 / F08；作者规范 §3～§4 |
| AC-032-12 | F01/F02/F03/F04/F05/F08/F09 与总体架构、SR-004/SR-007/SR-016 对无 Assurance 共享资源、Host Resource Read、完整 Script Registry、Compiler 资源闭包和 AI Change Set 边界无冲突；所有实现状态仍 NOT_RUN / NOT_IMPLEMENTED | 对应设计说明书版本、跨文档一致性审计和 PR 静态检查 |
| AC-032-13 | CA-SL 1.6.0 保留原有 Node / routes / arguments / PredicateSet YAML 形状并明确规范文法；Procedure / Node / Stage / Predicate / Script Registry 字段、基数、映射/序列区别、SourcePath 和终态完整；不得新增 Wait 语法。正式机器 Schema / Golden 的发布责任与 NOT_RELEASED 状态明确 | CA-SL 1.6.0 §6.1～§6.3、§8；原 v1alpha4/v1alpha5 只读源规范对照；ca-skills 正式 Schema / Golden release gate |
| AC-032-14 | Host Resource Read 有精确请求 / 响应、当前 Run Package snapshot 绑定、路径根 / 路径穿越拒绝、文本媒体类型、单文件大小上限、拒绝诊断；F01/F02/F03/F04/F05/F08/F09/SR-004/SR-007/SR-016 均引用同一接口 | F05 §2.1；F01 / F03 / F04；SR-004 AC-004-01/02；SR-007 AC-007-08 |
| AC-032-15 | `when` 是有 Assurance Skill 的 SKILL.md Front Matter 可选 CA-Agent 扩展；无 Assurance Skill 不声明 when；`when` 不属于 Contract YAML，input 成员由 Contract.requestSchema 类型化，Compiler 发布 CheckedExpr/DescriptorSet，Importer 核对作者声明与 Artifact 一致 | SKILL 作者规范 §3～§4；CA-SL 1.6.0 §2、§4～§5、§9；F02 §6～§7；F08 §2～§3；SR-004 AC-004-01～03；SR-013 AC-013-02 |

## 7. 当前状态与门禁

- 中央作者规范和历史来源归档：本 PR 提交候选。
- 独立设计评审：待执行；不得标记 APPROVE_FOR_READY。
- CA-SL 1.6.0 正式作者 Schema / Golden / Release：NOT_RELEASED。
- Compiler / Bundle / Studio / Runtime 产品验收：NOT_RUN。
- ca-skills 或其他外仓实施：未授权、未执行。
- DeepSeek Harness Goal：本 SR 未达到实施 READY，不得派发代码实施提示词。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 SKILL 作者规范迁移范围、Node / 注释规则和独立 AC | 将已有 ca-skills 作者经验纳入 Next 单一设计权威，避免旧语法直接复用或注释替代机器契约 | IR-008；Issue #49；SR-023/029 |
| 2026-11-27 | 0.1.1 | GPT-6.2（ChatGPT） | §3.3～3.4、§6 | 补充 SourcePath 与 Procedure.inputs 的准确边界，并增加 AC-032-08；同步作者规范修订版 | 防止作者规范擅自扩展 CA-SL 1.6.0 未冻结的参数结构 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.2 | GPT-6.2（ChatGPT） | §3、§6 | 增加 Assurance 有效性、LLM-guided 边界、Node-entry Wait 约束及 AC-032-09 | 让作者规范覆盖完整包生命周期与 Wait 作者边界，避免静默降级和伪造 Wait Node | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.3 | GPT-6.2（ChatGPT） | §3.3、§6 | 将参数结构明确交由 CA-SL 1.6.0 正式 Schema / Golden 冻结，避免作者规范引入未定义语法 | 保持语言规范与作者风格规范职责分离 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.4 | GPT-6.2（ChatGPT） | 文档头、§3.3、§6 | 修正 SR 局部非目标；细化独立证据与分支拆分条件，补齐真实样本对照和注释正反例验收 | 防止 SR 自身非目标误指向归档文件，并让验收条件对应可核验内容 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.5 | GPT-6.2（ChatGPT） | 文档头、设计依据 | 将 EC01 架构设计基线更新至 v0.1.5 | 确保 SR 评审引用与 PR Head 中的架构文档一致 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.6 | GPT-6.2（ChatGPT） | §1、§3～§6 | 将 Package 根目录共享资源、YAML Schema 源、Script Registry 与 Host Script Execution 纳入作者规范范围，更新 F01～F09 依赖和 AC-032-10～12 | 修复 schemas/scripts 归入可选 Assurance 导致 LLM-only Skill 无法共享资源的架构问题 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.7 | GPT-6.2（ChatGPT） | 文档头、设计消费者 | 扩展 SR-032 功能归属至 F01/F03/F04/F05/F08，覆盖 Model Context、Host 内建 Tools Extension、Runtime Action Boundary、资源快照和 Bundle | 确保 Host Script Execution 的跨模块消费方纳入同一设计门禁 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.8 | GPT-6.2（ChatGPT） | §5～§6 | 更新 CA-SL / 作者规范依赖版本；将 Host Script Execution 双门禁纳入 AC-032-11 | 使 SR 验收与 CA-SL、Host 配置及作者规范的最终边界一致 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.9 | GPT-6.2（ChatGPT） | §5～§6 | 删除 `llmInvocable` 与 `scriptExecution.llmEnabled` 双门禁，更新 AC-032-11 为同一 Script Runner | 明确 Demo 中 LLM 默认可执行当前 Skill scripts/ 登记脚本，与确定性执行使用相同脚本能力 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.10 | GPT-6.2（ChatGPT） | §6、设计依赖 | 将 SR-032 设计依赖版本更新至 CA-SL 1.6.0 v0.1.9 / SKILL 作者规范 v0.1.7 | 确保 SR 验收引用的机器语义与作者规则均为移除双门禁后的最新基线 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.11 | GPT-6.2（ChatGPT） | §1、§3～§6 | 移除 Skill 层 Wait / await / polling 语法；补齐 CA-SL 原有 YAML 机器结构、Script I/O / Evidence / 错误契约、Host Resource Read；新增 AC-032-13/14 并纳入 SR-004/007/016 | 回应独立评审的真实阻断项，同时恢复既定语言边界，不重构原有四阶段语法 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.12 | GPT-6.2（ChatGPT） | §3～§6、AC-032-15、设计依据 | 增加 `when` 的 Front Matter 位置、Assurance-only 适用范围、Request Schema 类型来源与 Compiler/Importer 一致性门禁 | 落实用户确认的入口方案，防止无 Assurance Skill 声明未经编译的 when | Issue #49；IR-008；F02/F08/F09；SR-004/013 |
