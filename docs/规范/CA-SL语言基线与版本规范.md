# CA-SL 语言基线与版本规范

> 文档类型：规范  
> 文档版本：0.1.0  
> 状态：待评审  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、签名、完整性体系和 Trust Registry  

关联 [IR-006](../IR/IR%20总登记册.md#ir-006)、IR-003。

## 1. 发布与候选

现行发布版本为 `connectionagent.io/v1alpha5`。完整规范固定到 [docs/skill-language-spec.v1alpha5.zh-CN.md](https://github.com/odango-chan/ca-skills/blob/0abfd0e1ab99f481a4ae01f3f47efc54783dd5e5/docs/skill-language-spec.v1alpha5.zh-CN.md)，发行记录见 [docs/releases/ca-sl-v1alpha5.md](https://github.com/odango-chan/ca-skills/blob/b06f72baae3eb3d578c489f950a325e2d63d556f/docs/releases/ca-sl-v1alpha5.md)。IngressCatalog 与诊断注册沿用各自冻结版本。v1alpha4 仅作历史继承记录。

[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 同标识刷新仍待评审。候选 §11.3、§12.8、附录 M 对应 SA-001～SA-011。移交时保留完整发布规范、引用、原提交和修订历史。正式切换前由 SR-013 核验源文件完整性、章节引用、Schema、示例、规范锁及发布入口。本稿仅建立中央版本登记与变更边界。

## 2. Next 技能作者与执行边界

[技能与确定性保障格式规范](技能与确定性保障格式规范.md) 定义 Next 作者源及消费包边界。SKILL.md 必需；可选 Assurance 包含 contract、procedure 和 predicates。Contract 顶层可选 `when` 为候选作者语义。存在 Assurance 时校验失败须拒绝。节点 Precondition、Operation、Observation、Postcondition 与执行期 Predicate 的冻结语义仍沿用语言发布基线。

候选 §12.8 中的作者源导入与构建适用于作者工具；Next 运行时产品只导入正式发布包。中央语言刷新须明确这两个产品边界并验证对应入口。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F02 · IR-003 / IR-006 · SR-013 |
