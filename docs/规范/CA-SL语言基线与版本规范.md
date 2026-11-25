# CA-SL 语言基线与版本规范

> 文档类型：规范  
> 文档版本：0.1.2  
> 状态：待评审  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、签名、完整性体系和 Trust Registry  

关联 [IR-006](../IR/IR%20总登记册.md#ir-006)、IR-003。

## 1. 发布与候选

现行发布版本为 `connectionagent.io/v1alpha5`。完整规范固定到 [docs/skill-language-spec.v1alpha5.zh-CN.md](https://github.com/odango-chan/ca-skills/blob/0abfd0e1ab99f481a4ae01f3f47efc54783dd5e5/docs/skill-language-spec.v1alpha5.zh-CN.md)，发行记录见 [docs/releases/ca-sl-v1alpha5.md](https://github.com/odango-chan/ca-skills/blob/b06f72baae3eb3d578c489f950a325e2d63d556f/docs/releases/ca-sl-v1alpha5.md)。IngressCatalog 与诊断注册沿用各自冻结版本。v1alpha4 仅作历史继承记录。

[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 同标识刷新仍待评审。候选 §11.3、§12.8、附录 M 对应 SA-001～SA-012。移交时保留完整发布规范、引用、原提交和修订历史。正式切换前由 SR-023 核验源文件完整性、章节引用、Schema、示例、规范锁及发布入口。本稿仅建立中央版本登记与变更边界。

## 2. Next 技能作者与执行边界

[技能与确定性保障格式规范](技能与确定性保障格式规范.md) 定义 Next 作者源及消费包边界。SKILL.md 必需；可选 Assurance 包含 contract、procedure 和 predicates。Contract 顶层可选 `when` 为候选作者语义。存在 Assurance 时校验失败须拒绝。节点 Precondition、Operation、Observation、Postcondition 与执行期 Predicate 的冻结语义仍沿用语言发布基线。

候选 §12.8 中的作者源导入与构建适用于作者工具；Next 运行时产品只导入正式发布包。中央语言刷新须明确这两个产品边界并验证对应入口。

## 3. 候选规范评审与 DSH 恢复输入

对照 [ca-skills #88 的固定候选](https://github.com/odango-chan/ca-skills/blob/2eedf4231075b6c589212d7d25576c7abbe6a5d9/docs/skill-language-spec.v1alpha5.zh-CN.md#m4-skill-import-与编译边界) 评审以下改动。此节记录待规范负责人确认的语义及验收预期。

| 候选条款 | 拟澄清的行为 | 验收输入与可观察结果 |
|---|---|---|
| M.4、SA-002／003 | 作者工具校验完整 Assurance，调用外部 Compiler 构建和验证，再交由发布流程。Next 运行时接受 SKILL.md-only 或正式发布的 Assurance Bundle。 | 有效作者源生成可验证产物；缺失或无效 Assurance 失败。向 Next 导入作者源包应失败，不能降级成 SKILL.md-only。 |
| M.4、SA-009 | Next Importer 对正式发布 Bundle 做受支持版本、结构、文件、引用和类型检查。Compiler 的构建与验证在发布流程完成。 | 有效 Bundle 导入成功且两个模式可选。损坏、路径无效或类型数据不可解码的 Bundle 导入失败。两组都验证 Host 无 Compiler 调用。 |
| M.4、SA-011 | AI 编辑走与用户编辑相同的作者校验、编译和发布路径。已运行的 Catalog generation 直到显式导入成功后才切换。 | 只编辑未发布的 Assurance 源，当前 Run 和生效目录不变；导入新发布 Bundle 后，新事件使用新 generation。 |
| M.2／M.3、SA-008 | 建议在新事件上，将声明了 requestSchema 但 payload 不匹配的 Assurance Skill 排除在两个候选集合之外。保留 Schema 不匹配诊断，区分 CEL 求值错误。 | A 无 when 且 requestSchema 要求整数 requestType，B 为 SKILL.md-only。输入 requestType 为字符串且无显式匹配，候选只含 B。把输入改为整数后，A、B 均进入语义候选。规范负责人需确认此预期。 |

**DSH 恢复证据**包括正式语言规范 SHA 与发布记录、对上表各项的规范决议或采用的替代语义，以及 READY 的 SR-013。规范确认后，将对应正反例纳入 AC-013-01 的跨语言 fixture 或 SR-004～006 的 Host fixture，按职责分别取证。规范发布和 READY 仍为外部评审门槛。

### 3.1 候选复核结果

[#88 当前候选](https://github.com/odango-chan/ca-skills/blob/697246a967067cdeddb01c2f43b11a3e56afa480/docs/skill-language-spec.v1alpha5.zh-CN.md#m3-compiler-与-host-的职责) 的 M.4／SA-002、009、011 已将作者编译与 Agent Bundle 导入分开，明确消费路径无需独立 Admission。M.3.5／SA-012 已确认请求 Schema 不匹配时排除 Skill，记录输入校验诊断，并跳过 CEL。§3 保留此前评审输入。候选源码已对齐，验收未运行。DSH 预检须确认正式发布 SHA 保留上述条款，并重新核对 SR-013 是否 READY。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F02 · IR-003 / IR-006 · SR-023 |
| 2026-11-25 | 0.1.1 | Codex / GPT-6 | §3 | 固定候选冲突、拟澄清语义与正反例，明确 DSH 恢复输入 | F02 · SR-013 · SR-023 |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | §1、§3.1 | 固定已澄清候选与正式发布门槛 | SR-013、SR-023 |
