# EC01 — CA-SL 与 Skill 作者体系架构设计

> 文档类型：外部能力域架构设计（Next 中央权威设计）  
> 文档版本：0.1.8\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first 唯一新目标；作者规范/Compiler/Bundle 未发布）
> 功能归属：EC01；关联 F02、F06、F08、F09  
> 关联需求：IR-003、IR-006；SR-004～SR-006、SR-011、SR-023  
> 修订日期：2026-11-28
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：Agent 运行时实现、生产准入与信任体系，详见 §9。
> 来源：ca-skills main 780497a；CA-SL v1alpha5 发布规范 18d818436；PR #88/#89

## 1. 架构定位

EC01 负责 Skill 作者源格式、CA-SL 语言语义、Skill Package 内容组织和业务 Skill 源。它定义“作者如何表达能力”，不负责 Agent Runtime、Plugin 生命周期、Tool Provider 进程、Owner 权威状态或 Compiler 的执行实现。

依赖关系：

~~~text
Skill package (CA-SL 1.6.0 Assurance design target)
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

Compiler **唯一从 `skills/<skill-id>/assurance/contract.yaml` 读取可选顶层 `when`**，依据正式 Request Schema 与 Publisher 已冻结 Event metadata 校验并编译；`SKILL.md` Front Matter 和无 Assurance Skill 都不得声明 `when`。`when` 只用于 Event/Input 的 T1 Skill 选择，不替代执行期 `predicates.yaml`。

~~~yaml
when: 'event.type == "nsmf.create-sm-context" && has(input.request.requestType) && input.request.requestType == "INITIAL_REQUEST"'
~~~

此例仅说明作者源位置和候选表达式形式。`input` 是规范化 Event payload，原版 OpenAPI `SmContextCreateData` 位于 `input.request`；其 `requestType` 为可选字符串，读取前必须以 `has(input.request.requestType)` 守卫，并与字符串 `"INITIAL_REQUEST"` 比较。当前固定 OpenAMSM OAS3 `RequestType` 的两个 `anyOf` 分支均为 string；不得使用整数比较。`event.type` 只有在 Event Publisher 正式冻结 metadata Schema/Descriptor 后才可引用；`has()` 与 `&&` 左到右短路语义也必须由 ca-skills Publisher 纳入并冻结于 CA-SL 1.6.0 CEL Profile；冻结前不得视为已发布契约。

SBI JSON 直接采用 OpenAMSM 对应版本的 3GPP/OpenAMSM 正式 OpenAPI YAML，保留原件及其引用。NAS/NGAP 二进制经 Codec 解码，解码字段遵循 Codec 发布的结果 Schema。`format: binary` 只描述传输形式。选择期只读取当时已存在的输入，Request Schema 解析与 when 的静态类型检查遵循正式 CA-SL / Compiler 契约。

约束：

- when 只在新业务 Event 的 Skill 选择阶段评估。
- 表达式使用 Publisher 已冻结的 Event metadata 与该 Skill requestSchema 所定义的输入类型；静态检查必须在发布阶段完成。当前 `event.type` 仅为候选字段，Event envelope、metadata 字段集/类型和规范化规则须由 Publisher 冻结。
- `when` 只能引用 T1 已有的 Event metadata 与已按 Request Schema 验证的 `input`；不得引用 T2 Codec Result、运行期 Evidence、Owner 状态或未声明字段。`event.type` 仍须经 Publisher 正式冻结为规范化 metadata，不能凭候选示例假定机器字段已发布。
- optional input 字段先用 `has(input.field)` 守卫，nullable 字段先判存在再与 `null` 比较；`has()` 和 `&&` 左到右短路语义属于 Publisher/Compiler 资格化门槛。`requestType` 的枚举和值按 OpenAMSM 对应正式 OpenAPI 原件校验，当前示例非已发布合同。
- 无 when 的 Skill 仍可通过 Skill 元数据和语义选择进入候选；when 返回 false 的 Skill 不得被选择。
- CEL 解析/类型/求值错误必须 fail closed，不得把错误或 UNKNOWN 变成 true。
- Continuation 关联到原 Run/Skill，不重新进行新 Event 的 Skill 选择。
- 不得把 when 写进 SKILL.md、predicates.yaml 或另建 constraint.yaml/activation.yaml、第二套选择包。

## 5. Compiler 与发布边界

ca-skill-compiler 是唯一 CA-SL 编译器。EC01 不复制 Parser、Schema Resolver、Linker、Procedure Graph Validator 或 Artifact Assembler。

作者源发布链路的目标是：

1. 以确定的作者源和 Schema 闭包作为输入。
2. CI 调用已发布的 Compiler 版本完成 Check、Build、Verify。
3. 只有全部成功才组装并发布 Skill Bundle。
4. 发布记录固定作者源、Compiler Release、Artifact 契约和 Bundle 版本。
5. Next Host 只导入发布 Bundle，不运行 Compiler。

历史 v1alpha5 的 `when` 已在 ca-skills #88/#89 留下冻结发布记录，但 Compiler #61 仅属于该历史范围。**1.6.0-only Compiler 由 [#62](https://github.com/odango-chan/ca-skill-compiler/issues/62) 单独跟踪**：v2.1.0 尚无 1.6.0 Contract.when AST/可消费的 CheckedExpr/DescriptorSet，须由正式 Publisher/Compiler 冻结和互操作验证；旧 v1alpha5 Artifact 和 Development v1alpha1 不得转换、兼容消费或混用。历史规范已发布并不等于新版 Bundle/Runtime 已完成。

## 6. 版本、缓存与运行时消费

- Skill Bundle 的发布版本和 CA-SL languageTarget 是两个独立维度。
- Host 导入时检查 Bundle 支持版本、必需文件、路径、引用、Schema/类型材料和依赖身份；不调用 Compiler。
- SR-004 返回经校验的 candidate；SR-005 据此构建并原子激活不可变 SkillCatalog generation，解析后的 metadata、when 程序和选择所需类型环境驻留内存。
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
| 1.6.0 Compiler when CheckedExpr / DescriptorSet | ca-skill-compiler #62 跟踪新 1.6.0-only 产物；历史 #61 仅只读审计，当前 v2.1.0 尚不具备新 AST/Runtime Artifact | NOT_IMPLEMENTED / NOT_RELEASED |
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

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 从 CA-SL v1alpha5、作者模型和 Compiler #61 还原作者体系架构，分离规范发布与 Compiler/Host 实现状态 | 历史记录未单列原因 | Issue #12；SR-023 |
| 2026-11-27 | 0.1.1 | Codex | §1～6 | 校正新旧版本、选择条件示例、Schema 来源与导入职责 | 历史记录未单列原因 | Issue #40、#43；PR #44 |
| 2026-11-27 | 0.1.2 | Codex | 文档头 | 补录全局评审范围及 §9 局部非目标，满足治理规范 §11.7 | 历史记录未单列原因 | Issue #43；PR #44 |
| 2026-11-27 | 0.1.3 | GPT-6.2（ChatGPT） | §2～3、§10、修订记录 | 整合 #45 的 1.6.0-only 设计增量并保留恢复分支当前状态，避免回滚 #44 与后续修订。 | 历史记录未单列原因 | Issue #12/#40/#43；PR #44/#45 |
| 2026-11-27 | 0.1.4 | GPT-6.2（ChatGPT） | §4、修订记录 | 为可选 requestType 增加 has() 守卫；将 Event metadata、has() 与短路规则明确为 Publisher 冻结前候选，避免可选字段误排除且不提前冻结 1.6.0 Event/CEL 契约 | 历史记录未单列原因 | Issue #40/#49；SR-013/029；PR #45/#52 |
| 2026-11-27 | 0.1.5 | GPT-6.2（ChatGPT） | EC01 §5/§8 | 区分 v1alpha5 Issue #61 历史范围与 1.6.0-only Issue #62 的 Compiler when / Runtime Artifact 追踪。 | 避免把历史 Compiler Issue 当作 1.6.0 目标实现。 | Issue #40/#62；PR #45 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 1.6.0 新目标与历史边界 | 将 EC01 完整规范入口切换至 CA-SL 1.6.0，固定 languageTarget 候选并明确 v1alpha5 只读 | 历史记录未单列原因 | Issue #12/#40；PR #46 |
| 2026-11-28 | PR46-0.1.4（历史分支标记） | GPT-6（ChatGPT） | §4、§5、§8、修订记录 | 合并前 #46 分支限定修订：when 唯一 contract.yaml、optional requestType CEL Guard、T1/T2 分离和 Compiler #62 | 历史分支原采用 0.1.4 版本号，区别于恢复分支已发布的同号修订 | Issue #40；#47；PR #45；#46 |
| 2026-11-28 | 0.1.6 | GPT-6（ChatGPT） | §4、§5、§8、修订记录 | 合并恢复分支 0.1.5 的 Event/Request Schema、G.4 Guard 规则与 #46 的 1.6.0-only/T1-T2/Compiler #62 修订 | 保存双方有效设计与分支历史，保持新 Compiler/Product NOT_RELEASED | Issue #12；#40；PR #45；#46 |
| 2026-11-28 | 0.1.7 | GPT-6（ChatGPT） | §4、修订记录 | 修正 when 的规范化输入嵌套路径和 RequestType 字符串类型；统一修订表列结构 | 避免可选字段读取路径错误、数字比较及修订记录关联列错位 | Issue #12；#40；PR #46；Review #6095143611 |
| 2026-11-28 | 0.1.8 | GLM-5.3（DeepSeek Harness） | 修订记录 | 合并被空行拆断的孤儿修订表段为单一连续表格，不改变任何历史行内容 | 修复 R8-09 同类 Markdown 渲染断裂，保证修订数据完整可见 | Issue #12；PR #46；Review #6095143611 |
