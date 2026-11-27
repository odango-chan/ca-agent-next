# SR-032：SKILL 作者规范、Node 拆分与注释原则

> 文档类型：软件需求（SR）  
> SR 版本：0.1.2  
> 状态：**DRAFT（中央作者规范已形成设计候选，待独立设计评审；实施 NOT_READY）**  
> 创建日期：2026-11-27  
> 修订日期：2026-11-27  
> 上游需求：IR-008（关联 IR-003）  
> 功能：EC01 / F02 / F09（作者规范由 EC01 维护，F09 AI Authoring 消费）  
> 设计依据：[EC01 CA-SL 与 Skill 作者体系架构](../架构设计/外部能力域/EC01-CA-SL与Skill作者体系架构设计.md) v0.1.4；[CA-SL 1.6.0 完整语言规范](../规范/CA-SL%201.6.0完整语言规范.md) v0.1.5；[SKILL 作者规范](../规范/SKILL作者规范.md) v0.1.2  
> 目标仓：odango-chan/ca-agent-next（仅中央设计和规范）  
> 上游来源仓：odango-chan/ca-skills，固定 main 780497a2918ad3e7bdff554ab64b0ba627e867e0  
> 关联 Issue：[ca-agent-next #49](https://github.com/odango-chan/ca-agent-next/issues/49)、父级迁移 Issue #12、CA-SL 设计 Issue #40  
> 固定设计基线：4873608f5ca854a6bb47cf1a83cb9214da4ae202

## 1. 目标

把 ca-skills 已整理的 Skill 作者经验迁移并收敛为 Next 的唯一中央作者规范，使作者、评审者和 Skill Studio AI Authoring 对以下事项有统一、可执行的判断依据：

- 什么行为应成为 Skill，什么应保留为公开 Capability，什么属于 Agent routing；
- Procedure Node 何时拆分、何时合并，以及一个 Node 的 Operation / Observation 边界；
- Precondition、Operation、Observation、Postcondition 四阶段的职责；
- YAML 注释应解释什么、不能承担什么；
- SKILL.md、Contract、Procedure、PredicateSet、Schema、Script 和 references 的组织与所有权；
- Capability-only、显式 arguments、when、Wait、Evidence 和 UNKNOWN 的作者约束。

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

新增《SKILL 作者规范》，并明确其与 CA-SL 1.6.0 语言规范的权威边界：语言规范定义语法和机器字段；作者规范定义粒度、表达、注释和质量要求。

### 3.2 Skill 与 Capability 粒度

保留可复用产品 / 领域 Skill 的原则；原始 Provider 操作、环境适配和无独立业务语义的 READ / MUTATION 保留为 Capability；routing 由 Agent 负责；禁止一 Tool Call 一个 Skill。

### 3.3 Node 粒度

一个业务 Node 表达一个主要业务动作，最多一个 Operation（公开 Capability 或纯本地 Script），可带一个直接相关的 READ Observation 和本动作的前后置 Predicate。

必须拆分：两个不同 Operation Capability、独立业务提交边界、独立证据确认边界、真实业务分支或恢复路径。

应保持合并：同一 Capability 内部的 Provider / HTTP / SBI / NAS / N2 / PFCP 子步骤；同一阶段的多个 Predicate；可用 routes 表达的 Outcome 分支；简单参数映射。

允许最终 Postcondition-only Node、独立 Observation-only Node 和有明确边界的纯 Script Node；禁止 start-only、wait-only、reconcile-only、HTTP-only、Provider handler-only、单 Predicate Node。

### 3.4 注释

注释解释 why、业务上下文、非显然映射和固定来源；不得替代类型、Schema、参数、Predicate、Evidence、Effect、Outcome、routes、重试或权限契约。注释不得含密钥、用户数据或临时运行时 ID。复杂背景放 references，不逐行解释 YAML。

### 3.5 AI Authoring

F09 的 AI Authoring 必须使用同一作者规范生成和检查 Change Set；不得通过注释补足机器语义，不得暴露 Callable / backendOperationId，不得机械拆分 Node。Apply 后仍须通过同一 1.6.0 Compiler gate；本 SR 不宣称现有 Studio 已实现。

## 4. 非目标

- 不修改 CA-SL 1.6.0 语言语法、Schema、Outcome 或 Compiler API。
- 不支持 v1alpha5 / v1alpha6 兼容、双轨、自动迁移或旧包 fallback。
- 不修改 ca-skills、ca-skill-compiler、ca-skill-studio-demo 或其他兄弟仓。
- 不实现注释 Linter、Node 自动拆分器或新的 AI Authoring Runtime。
- 不把生产级 Admission、Trust、签名、额外 package digest 或完整 DFX 纳入 Demo。
- 不将文档设计评审等同产品发布、代码实现或 E2E PASS。

## 5. 依赖与边界

| 类型 | 依赖 | 影响 |
|---|---|---|
| 设计依赖 | SR-029 / CA-SL 1.6.0 | Node 字段、Capability 绑定、四阶段和 when 语义必须一致；不反向修改语言规范 |
| 历史来源 | SR-023 / ca-skills v1alpha5 | 只用于来源核对和历史归档 |
| 消费者设计 | F09 / SR-016 | AI Authoring 应读取本规范；现有产品实现状态不自动变化 |
| 外部发布依赖 | ca-skills 1.6.0 正式 Schema / Golden / Release | 正式发布前，本规范与语言稿均保持设计候选，不声称产品可执行 |
| 实施边界 | ca-agent-next | 本 SR 的目标仓仅为中央文档；如未来需要改动 ca-skills 或 Studio，另建目标仓实施 SR |

## 6. 验收条件

| AC | 验收要求 | 证据 |
|---|---|---|
| AC-032-01 | 作者指南、作者模型、Skill Granularity、Authoring Syntax、Package Layout、Schema Ownership、创建工作流和实际 Skill 样本均有固定源路径、commit / blob SHA 和迁移裁决 | 作者规范 §12、历史归档文件、恢复清单 |
| AC-032-02 | Skill package 粒度与 Node 粒度分开定义；Skill / Capability / Agent routing 边界明确 | 作者规范 §2、§6 |
| AC-032-03 | Node 拆分与合并规则严格符合 1.6.0 四阶段顺序、每种阶段最多一个、Operation / Observation Capability 边界和静态 DAG | 作者规范 §5～§6；CA-SL 1.6.0 对照 |
| AC-032-04 | 注释规则区分解释性内容与机器执行契约，给出正反例，且不把旧资料未定义的规则伪称为迁移原文 | 作者规范 §7、§12 |
| AC-032-05 | Package 文件职责、Schema 所有权、Capability-only、显式 arguments、when、Wait、Evidence / UNKNOWN 与 1.6.0 设计一致 | 作者规范 §3～§5、§8～§9 |
| AC-032-06 | F09 明确 AI Authoring 必须遵守同一作者规范，并保留用户确认和 Compiler gate | F09 §9.3 |
| AC-032-07 | IR、功能树、SR 索引、实施状态、文档目录、迁移审计和修订记录完整互链；不误报 1.6.0 Release / 实施 / E2E 状态 | 本 SR、各治理索引、PR 静态检查 |
| AC-032-08 | Procedure.inputs 只绑定精确 context SourcePath；调用 arguments 只使用受支持 SourcePath / 标量字面量；Node / Wait 输出引用精确到 NodeId.Stage.output / NodeId.wait.output；作者规范不得发明正式语言 Schema 未冻结的参数结构 | 作者规范 §4.2；CA-SL 1.6.0 §5.3 |
| AC-032-09 | 无 assurance/ 的 Skill 仅 LLM-guided；存在 assurance/ 时所有必需文件与静态语义必须完整有效，不得静默降级；Wait 仅作为 Node-entry Host Runtime READ 控制，不创建 Wait-only Node 或作者级 polling | 作者规范 §3、§5；CA-SL 1.6.0 §2、§10 |

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
