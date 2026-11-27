# EC01 — CA-SL 与 Skill 作者体系架构设计

> 文档类型：外部能力域架构设计（Next 中央权威设计）  
> 文档版本：0.1.3\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first 唯一新目标；作者规范/Compiler/Bundle 未发布）  
> 功能归属：EC01；关联 F02、F06、F08、F09  
> 关联需求：IR-003、IR-006；SR-004～SR-006、SR-011、SR-023  
> 修订日期：2026-11-26
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文第 §9 节为准；Demo 不引入生产级准入、签名或兼容层  
> 来源：ca-skills main 780497a；CA-SL v1alpha5 发布规范 18d818436；PR #88/#89

## 1. 架构定位

EC01 负责 Skill 作者源格式、CA-SL 语言语义、Skill Package 内容组织和业务 Skill 源。它定义“作者如何表达能力”，不负责 Agent Runtime、Plugin 生命周期、Tool Provider 进程、Owner 权威状态或 Compiler 的执行实现。

依赖关系：

~~~text
CA-SL 1.6.0 complete author specification draft (not released; v1alpha5 archival only)
  ├─ SKILL.md metadata / package identity
  ├─ optional Assurance author source
  │    ├─ contract.yaml
  │    ├─ procedure.yaml
  │    └─ predicates.yaml
  ├─ schemas / scripts / references
  └─ business Skill source
       ↓
ca-skill-compiler (EC02, external build-time owner)
       ↓
published Skill Bundle
       ↓
Next Host importer / SkillCatalog / Resolver (F02)
       ↓
Runtime (F04)
~~~

EC01 与 EC02、F02、F09 的职责必须分离：EC01 定义作者语义；EC02 编译和发布可消费产物；F02 导入、缓存、选择和绑定 Skill；F09 提供源码编辑体验。

## 2. Skill Package 与作者输入

SKILL.md 是每个 Skill 的基础身份和描述入口，至少提供稳定名称及描述。Assurance 是可选作者内容；新作者的唯一语法目标是 **CA-SL 1.6.0**（Capability ID 仅作者可见、Capability↔Callable 双向一对一），尚未正式发布。历史冻结 CA-SL v1alpha5 仅用于审计，不是新作者或 Compiler 的合法输入。

~~~text
<skill>/
  SKILL.md
  assurance/                 # optional
    contract.yaml
    procedure.yaml
    predicates.yaml
  schemas/
  scripts/
  references/
~~~

边界规则：

1. 没有 Assurance 的 SKILL.md-only Package 是合法 Skill，可供 LLM-guided 模式使用。
2. 存在 Assurance 时，Contract、Procedure、PredicateSet 和其引用必须整体有效；任何验证失败均拒绝导入，不得降级成 SKILL.md-only。
3. Assurance 有效时，Skill 可供 Deterministic 与 LLM-guided 两种模式使用。
4. 不允许 Agent 自行编译作者源；Agent 只导入发布好的 Skill Bundle。
5. **唯一新语言目标 CA-SL 1.6.0**；languageTarget 建议值为 connectionagent.io/v1.6.0，须由 ca-skills / Compiler 在正式 Schema / Golden 中共同确认；完全不支持 v1alpha5 旧语法、旧 Build DTO/Artifact/Bundle、双轨、转换、迁移或 fallback。

## 3. Contract、Procedure、Predicate 的语义分层

| 构件 | 作用 | 不得承担 |
|---|---|---|
| SKILL.md | Skill 身份、描述、作者可读元数据 | 运行时授权、Owner 事实 |
| Contract | 请求输入契约、Skill 选择条件、可声明的执行约束 | 业务执行步骤 |
| Procedure | 有序 Node、路由、输入绑定和操作/观察/后置条件 | Skill 选择 |
| PredicateSet | 执行期事实判断与 Assurance | Skill 选择条件 |
| Schema | 输入输出字段、类型及约束 | 业务执行逻辑 |
| Script / Tool binding | 受契约约束的具体操作实现或外部调用 | 取代 Owner 权威结果 |

Node 仍包含 Precondition、Operation、Observation、Postcondition 阶段；新 1.6.0 的 Operation / Observation 仅引用 Capability ID，Observation 要求 `kind=observation` 且 `Effect=READ`；具体 1.6.0 Schema 由 ca-skills 正式发布并通过 SR-029 审核。历史 v1alpha5 的节点语义只读留档，不被新版解释器兼容。

## 4. when 与执行期 Predicate 分离

可选的 Skill 选择条件位于 assurance/contract.yaml 的顶层 when。它只回答“当前 Event/Input 是否适用这个 Skill”，不替代 predicates.yaml，也不执行任何业务操作。

~~~yaml
when: 'event.type == "nsmf.create-sm-context" && input.requestType == 1'
~~~

约束：

- when 只在新业务 Event 的 Skill 选择阶段评估。
- 表达式使用 Event 与该 Skill requestSchema 所定义的输入类型；静态检查必须在发布阶段完成。
- when 不得引用运行期 Evidence、Owner 状态或未声明字段。
- 无 when 的 Skill 仍可通过 Skill 元数据和语义选择进入候选；when 返回 false 的 Skill 不得被选择。
- CEL 解析/类型/求值错误必须 fail closed，不得把错误或 UNKNOWN 变成 true。
- Continuation 关联到原 Run/Skill，不重新进行新 Event 的 Skill 选择。
- 不得把 when 写进 predicates.yaml，不得新增 constraint.yaml 或另一套选择包。

## 5. Compiler 与发布边界

ca-skill-compiler 是唯一 CA-SL 编译器。EC01 不复制 Parser、Schema Resolver、Linker、Procedure Graph Validator 或 Artifact Assembler。

作者源发布链路的目标是：

1. 以确定的作者源和 Schema 闭包作为输入。
2. CI 调用已发布的 Compiler 版本完成 Check、Build、Verify。
3. 只有全部成功才组装并发布 Skill Bundle。
4. 发布记录固定作者源、Compiler Release、Artifact 契约和 Bundle 版本。
5. Next Host 只导入发布 Bundle，不运行 Compiler。

CA-SL v1alpha5 的 when 已进入已合并的 ca-skills #88/#89 发布刷新；但 Compiler Issue #61 仍 OPEN，目标是生成可供 Python Runtime 加载的 CheckedExpr 与 DescriptorSet 新版发布 Artifact。旧冻结 Artifact v1alpha5 和 Development Artifact v1alpha1 不得原地修改或混用。故“作者规范已发布”不等于“Compiler when 发布物已完成”，也不等于“Next 运行时互操作已通过”。

## 6. 版本、缓存与运行时消费

- Skill Bundle 的发布版本和 CA-SL languageTarget 是两个独立维度。
- Host 导入时检查 Bundle 支持版本、必需文件、路径、引用、Schema/类型材料和依赖身份；不调用 Compiler。
- 成功导入形成不可变 SkillCatalog generation，解析后的 metadata、when 程序和选择所需类型环境驻留内存。
- 每个新 Event 在当前 Catalog generation 上进行候选过滤和 when 求值，不重复读取磁盘作者源或重新解析 CEL。
- Skill 导入、更新、卸载才改变 Catalog generation；在途 Run 固定原 Skill 身份与 generation。
- 不建设额外分布式缓存、包管理器、自动更新服务或生产准入系统。

## 7. 版本权威与来源材料

- 完整新规范设计：[CA-SL 1.6.0 完整语言规范](../../规范/CA-SL%201.6.0完整语言规范.md)；历史来源：[CA-SL v1alpha5 完整语言规范](../../规范/CA-SL%20v1alpha5完整语言规范.md)，仅只读审计。
- 作者模型原文：[CA-SL 作者模型](../../设计说明书/外部能力域/EC01-CA-SL/CA-SL作者模型原文.md)。
- 作者指南原文：[CA-SL 作者指南](../../设计说明书/外部能力域/EC01-CA-SL/CA-SL作者指南原文.md)。
- Ingress Operation 契约：[原始设计](../../设计说明书/外部能力域/EC01-CA-SL/Ingress%20Operation契约设计原文.md)。
- Schema 闭包：[原始设计](../../设计说明书/外部能力域/EC01-CA-SL/Schema闭包摘要设计原文.md)。

## 8. 实现状态审计（与目标设计分开）

| 能力 | 当前证据 | 状态 |
|---|---|---|
| CA-SL v1alpha5 规范刷新 | ca-skills #88、#89 已合并；发布记录固定规范提交 18d818436 | IMPLEMENTED / RELEASED |
| 作者模型与指南 | ca-skills main 有 authoring-model.md、authoring.zh-CN.md | IMPLEMENTED |
| when 作者语义 | 已进入 CA-SL v1alpha5 正式发布记录；main 文档头部仍有 Proposed Refresh 字样，与 Release Record 状态冲突 | RELEASED；源仓文档状态不一致，需后续清理 |
| Compiler when CheckedExpr / DescriptorSet | ca-skill-compiler Issue #61 OPEN；Compiler v2.1.0 当前没有 Contract.when AST / 运行时选择程序 | NOT_IMPLEMENTED |
| Next Bundle Importer / Catalog generation / when evaluator | 当前设计待完整实施验收 | NOT_VERIFIED |
| Skill-first OpenAMSM 新 Event 选择 | 需 F02/F06 与 EC04 集成验收 | NOT_RUN |

## 9. 非目标

不引入旧版兼容、Agent 内置 Compiler、独立 Skill Admission、审批流程、签名、Trust Registry、额外 SHA-256、包完整性平台、业务状态选择器、第二套 Predicate 语言或 Runtime 业务逻辑。

## 10. CA-SL 1.6.0 唯一新作者目标（设计待评审）

- **作者输入**：SKILL.md Front Matter 遵守 Agent Skills Specification，CA-SL 1.6.0 作者规范仅定义可选 assurance/。Contract grants 只列 Capability ID；Procedure operation.capability/observation.capability 引用 Capability，Skill 不再表达 Owner/Provider Callable ID，也不引入额外 Operation ID。
- **基数**：每个 Skill-facing Capability ↔ 唯一公开 Callable；编译时强制双向一对一，kind/Effect/Input/Output Schema/依赖闭包静态匹配；Provider 内部可用封闭 selector 将一个公开 Callable 路由到多个私有 backendOperationId。Reconcile 是 Runtime internal-only，Receipt Query 仍为普通受控 READ。
- **发布链**：ca-skills 发布 1.6.0 完整规范、Schema、作者示例、languageTarget（建议 connectionagent.io/v1.6.0）；Compiler 仅为 1.6.0 创建新的 BuildRequest/BuildResult、Capability Binding、CheckedExpr/Request Schema Runtime Artifact，SR-027 重新 Build/Verify/Bundle；Agent 只导入该版本的正式 Bundle，Studio 只编辑 1.6.0。
- **彻底无兼容**：历史 v1alpha5 规范 / Golden / Release Record 只读留档，不被新 Compiler/Agent/Studio 加载；没有双语法、旧包解析、映射、版本协商、自动迁移或 fallback，旧 Skill 必须手工重写并重新发布。
- **阶段**：本 EC01 架构增量处于**待评审**，SR-029 / SR-013 / SR-027 必须分别完成规范审查和外部发行。1.6.0 代码、Golden、Bundle 与 E2E 均 NOT_RUN；不因旧 v1alpha5 发布历史提前宣布 PASS。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 从 CA-SL v1alpha5、作者模型和 Compiler #61 还原作者体系架构，分离规范发布与 Compiler/Host 实现状态 | Issue #12；SR-023 |
| 2026-11-26 | 0.1.1 | GPT-6（ChatGPT） | §2～3、§10、修订记录 | 将 EC01 新作者体系统一到 1.6.0-only Capability-first、一对一绑定和无兼容；旧 v1alpha5 仅审计 | Issue #40；IR-008；SR-029；SR-027 |
| 2026-11-26 | 0.1.2 | GPT-6（ChatGPT） | 文档头与修订记录 | 补齐 EC01 规范 review_scope 与非目标头部声明 | Issue #40；PR #45 |

| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 1.6.0 新目标与历史边界 | 将 EC01 完整规范入口切换至 CA-SL 1.6.0，固定 languageTarget 候选并明确 v1alpha5 只读 | Issue #12/#40；PR #46 |
