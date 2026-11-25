# CA-SL 语言基线与版本规范

> 文档类型：语言版本与运行时消费规范  
> 文档版本：0.2.0  
> 状态：CA-SL v1alpha5 FROZEN / RELEASED；Compiler when 运行时 Artifact 尚未完成  
> 修订日期：2026-11-25  
> 关联 IR：IR-003、IR-006；SR-023、SR-013  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：旧版兼容、Agent 内置 Compiler、Skill Admission、签名、Trust Registry 和额外 SHA-256

## 1. 当前正式语言基线

当前唯一语言目标为 connectionagent.io/v1alpha5，不引入旧版兼容映射或新的 v1alpha6。

完整规范正文已迁入 Next：[CA-SL v1alpha5 完整语言规范](CA-SL%20v1alpha5完整语言规范.md)。迁移来源是 ca-skills 发布规范提交 18d8184367982ccbc835756136c4a53f9096c3a0；ca-skills PR #88（规范刷新）和 PR #89（发布记录固定）均已合并。

权威来源：
- [ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88) — 2026-11-25 09:08 UTC MERGED。
- [ca-skills PR #89](https://github.com/odango-chan/ca-skills/pull/89) — 2026-11-25 09:10 UTC MERGED。
- [固定发布规范提交](https://github.com/odango-chan/ca-skills/blob/18d8184367982ccbc835756136c4a53f9096c3a0/docs/skill-language-spec.v1alpha5.zh-CN.md)。
- [发布记录](https://github.com/odango-chan/ca-skills/blob/main/docs/releases/ca-sl-v1alpha5.md)。

源仓当前 main 的规范文件头部仍有 Proposed Refresh / Normative Candidate 表述，而 Release Record 已记录正式发布。为避免误用，本仓以 Release Record 指向的不可变提交作为规范发布身份；源仓头部状态不一致列为待清理项，不改变已合并 PR 和 Release Record 的事实。

## 2. Next 作者与运行时消费边界

- SKILL.md 必需。
- Assurance 可选；不存在 Assurance 的 Skill 可用于 LLM-guided，不要求 Compiler。
- Assurance 存在时必须整体有效；导入失败不得降级成 SKILL.md-only。
- 有效发布 Assurance Artifact 可用于 Deterministic 和 LLM-guided。
- Contract 位于 assurance/contract.yaml；when 是可选顶层字段。
- predicates.yaml 只描述执行期 Predicate；when 只负责新 Event 的 Skill 选择。
- Node 阶段、Wait、Observation、Operation、Postcondition 及 Procedure Graph 语义以完整 CA-SL v1alpha5 规范为准。
- Next Agent 只导入正式发布 Bundle，不读取作者源进行运行时编译，不内置或调用 Compiler。

## 3. when 的发布与运行时依赖

when 的作者语义已进入 CA-SL v1alpha5 正式发布。它使用 Event 与 Skill requestSchema 类型环境，必须在发布阶段完成 CEL 解析、静态类型检查和 G.4 限制检查。

但语言规范发布不等于 Compiler 发布物已完成：
- ca-skill-compiler Issue #61 当前 OPEN。
- Compiler v2.1.0 当前 ContractAST 尚无 when 节点。
- 冻结 Artifact v1alpha5 不得原地添加 when 字段/文件。
- Development Artifact v1alpha1 保持 NOT_ADMITTED，不可作为 Next 可运行 Skill Bundle。
- 新版发布 Artifact、CheckedExpr、DescriptorSet 和 Python cel-expr-python 互操作必须由 Issue #61 的后续实现和 Release 证明。

Next 不得通过重新解析 CEL 原文、DynType 或自制 evaluator 绕过该依赖。Compiler 产物未发布前，带 when 的 Assurance Bundle 不得声称跨语言运行时互操作 PASS。

## 4. 规范变更规则

CA-SL 语义变化必须：
1. 在 ca-skills 对应设计和规范中提出。
2. 明确 languageTarget、Schema/fixture、示例和迁移影响。
3. 通过规范评审和正式发布记录。
4. 更新 Next 完整规范副本、F02/F08/F09 设计、SR-023/SR-013 和文档索引。
5. 对旧冻结 Artifact 采取新版本契约，不原地改变字节或语义。

## 5. 非目标

不引入旧版兼容、Agent 内置 Compiler、运行期编译、独立 Skill Admission、审批、签名、Trust Registry、额外 SHA-256 或第二套选择条件语言。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.3 | 原记录 | 全文 | 建立 CA-SL v1alpha5 发布登记 | IR-006 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | §1–5 | 核对 #88/#89 合并状态，迁入完整规范正文，明确源仓状态差异与 Compiler #61 未完成边界 | Issue #12；SR-023；SR-013 |
