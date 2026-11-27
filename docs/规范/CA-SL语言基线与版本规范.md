# CA-SL 语言基线与版本规范

> 文档类型：语言版本与运行时消费规范  
> 文档版本：0.2.6\
> 状态：**设计待评审**（唯一新目标 CA-SL 1.6.0；全链路不兼容任何旧作者语法、Build DTO、Artifact、Bundle；1.6.0 产品未发布）
> 修订日期：2026-11-26  
> 关联 IR：IR-003、IR-006；SR-023、SR-013  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：旧版兼容、Agent 内置 Compiler、Skill Admission、签名、Trust Registry 和额外 SHA-256

## 1. 当前正式语言基线

**版本决策（Issue #40，2026-11-26）：新增作者与产品实现统一面向 CA-SL 1.6.0，不再创建 v1alpha6 版本。** 已发布的历史语言规范仍为 `connectionagent.io/v1alpha5`（冻结不可变），但它不再是新产品链的目标。1.6.0 的精确 `languageTarget` 机器标识必须由 ca-skills 正式规范与 Compiler 跨仓互操作契约共同冻结；在正式发布前不得自造标识、把历史 Artifact 重命名或宣称已发布。无旧版兼容解析与自动迁移。

完整规范正文已迁入 Next：[CA-SL v1alpha5 完整语言规范](CA-SL%20v1alpha5完整语言规范.md)。迁移来源是 ca-skills 发布规范提交 18d8184367982ccbc835756136c4a53f9096c3a0；ca-skills PR #88（规范刷新）和 PR #89（发布记录固定）均已合并。

权威来源：
- [ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88) — 2026-11-25 09:08 UTC MERGED。
- [ca-skills PR #89](https://github.com/odango-chan/ca-skills/pull/89) — 2026-11-25 09:10 UTC MERGED。
- [固定发布规范提交](https://github.com/odango-chan/ca-skills/blob/18d8184367982ccbc835756136c4a53f9096c3a0/docs/skill-language-spec.v1alpha5.zh-CN.md)。
- [发布记录](https://github.com/odango-chan/ca-skills/blob/main/docs/releases/ca-sl-v1alpha5.md)。

源仓当前 main 的规范文件头部仍有 Proposed Refresh / Normative Candidate 表述，而 Release Record 已记录正式发布。为避免误用，本仓以 Release Record 指向的不可变提交作为规范发布身份；源仓头部状态不一致列为待清理项，不改变已合并 PR 和 Release Record 的事实。

### 新发布物的数字版本

**历史 Compiler v2.1.0 的**两个 Development Interface Package 的 `package.json.version` 与各自 snapshot key 均为 `1.0.0`；它不是新 1.6.0 Package 的版本规范。新设计的 Runtime Artifact 与 BuildResult 候选版本段为 `2`，按 SR-013 的 Owner 契约确认及发布流程冻结。复核已有发行物时按固定 revision 读取原始路径、`apiVersion`、`languageTarget`、Schema `$id` 和字节；新版机器标识由 ca-skills / Compiler 全新冻结；**不迁移旧版机器标识**，不实现旧标识别名或兼容输入。

## 2. Next 作者与运行时消费边界

- SKILL.md 必需。
- Assurance 可选；不存在 Assurance 的 Skill 可用于 LLM-guided，不要求 Compiler。
- Assurance 存在时必须整体有效；导入失败不得降级成 SKILL.md-only。
- 有效发布 Assurance Artifact 可用于 Deterministic 和 LLM-guided。
- Contract 位于 assurance/contract.yaml；when 是可选顶层字段。
- predicates.yaml 只描述执行期 Predicate；when 只负责新 Event 的 Skill 选择。
- **1.6.0** 的 Node 阶段、Wait、Observation、Operation、Postcondition 与 Procedure Graph 语义由 ca-skills 下一正式作者规范冻结；历史 v1alpha5 仅用于审计。Operation/Observation 只表示阶段，不新增 Skill-facing Operation ID。
- Next Agent 只导入正式发布 Bundle，不读取作者源进行运行时编译，不内置或调用 Compiler。

## 3. when 的发布与运行时依赖

**历史事实：**when 已进入 v1alpha5 Release，但不是新产品入口。**1.6.0 唯一目标**中 when 位于 Contract 顶层；Compiler 按 ca-skills 正式发布的新 CEL 剖面、当前 Skill Request Schema 和规范化 Event 静态校验、生成 CheckedExpr/DescriptorSet。安全 Guard/nullable/短路规则可借用旧 G.4 算法，准确新条款号/机器标识由 Owner 冻结，不猜测旧格式等价。

但语言规范发布不等于 Compiler 发布物已完成：
- ca-skill-compiler Issue #61 当前 OPEN。
- Compiler v2.1.0 当前 ContractAST 尚无 when 节点。
- 冻结 Artifact v1alpha5 不得原地添加 when 字段/文件。
- Development Artifact v1alpha1 保持 NOT_ADMITTED，不可作为 Next 可运行 Skill Bundle。
- 新版发布 Artifact、CheckedExpr、DescriptorSet 和 Python cel-expr-python 互操作必须由 Issue #61 的后续实现和 Release 证明。

Next 不得通过重新解析 CEL 原文、DynType 或自制 evaluator 绕过该依赖。Compiler 产物未发布前，带 when 的 Assurance Bundle 不得声称跨语言运行时互操作 PASS。

## 4. 规范变更规则

CA-SL 语义变化必须：
1. 在 Next 的 EC01 中登记 IR/SR、语义变化与受影响的消费者，由 ca-skills 维护作者源、发布记录与可核对的规范版本。
2. 明确 languageTarget、Schema/fixture、示例、与旧版的破坏性边界及拒绝旧输入的行为。
3. 通过规范评审和正式发布记录。
4. 更新 Next 完整规范副本、F02/F08/F09 设计、SR-023/SR-013 和文档索引。
5. 对旧冻结 Artifact 采取新版本契约，不原地改变字节或语义。

## 5. 非目标

不引入旧版兼容、Agent 内置 Compiler、运行期编译、独立 Skill Admission、审批、签名、Trust Registry、额外 SHA-256 或第二套选择条件语言。

## 6. 下一正式语言目标：CA-SL 1.6.0（未发布）

本节依据 [Issue #40](https://github.com/odango-chan/ca-agent-next/issues/40) 的最新版本决策；独立 SR-029 负责 Capability-first 作者语义及跨模块闭环。**“1.6.0”是下一个正式发布目标，不是“v1alpha6”的别名，也不是已经发布的 Runtime 契约。**

- Skill-facing Contract / Procedure 仅使用 Capability ID，不再用 `tool: alias::CALLABLE_ID`；Skill-facing Capability 与公开 Callable **一对一**。Callable ID 保留在内部 Package/Compiler/Provider/Runtime 绑定和诊断中。
- Operation / Observation 仍为 Node 阶段而非外部 Operation ID，按 Callable kind、Effect、Schema 校验；Compiler 必须链接出唯一 Capability→Callable Binding。Provider 内部可用封闭枚举路由多个 backend handler，但不能扩大 Skill Scope。
- 1.6.0 的作者示例、Schema、Compiler API、Runtime Artifact、Provider/Owner 发布身份、ca-skills Bundle、Studio 浏览及真实回归须按 SR-029、SR-013、SR-027 和相关模块分别冻结/验收；**Compiler #61 针对历史 v1alpha5 的 when 设计不自动等同 1.6.0 产品发布**。
- 当前未发布 1.6.0；只可规划新实现，不得把旧 `v1alpha5` Builder、Development v1alpha1 Artifact 或候选机器标识当作 1.6.0 正式产物。
- **全链路单版本约束：** 新 ca-skills 作者源、新 Compiler Check/Build/Verify 与 BuildRequest/BuildResult、新 Runtime Artifact、新 Agent Importer/Runtime、Skill Studio 只支持 **CA-SL 1.6.0**。不解析/编译/导入/执行历史 v1alpha5 或任何 v1alpha6 候选；不建立双语法、版本协商、兼容映射、fallback、自动转换或 Agent 内编译。旧 Skill 必须由作者按 1.6.0 重新编写、由新 Compiler 重新构建和发布，**不提供迁移工具**。旧包和旧 `languageTarget` 在新运行时均明确拒绝；历史 v1alpha5 规范、Release Record 与 Artifact 字节只读留档，仅供审计溯源。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.3 | 原记录 | 全文 | 建立 CA-SL v1alpha5 发布登记 | IR-006 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | §1–5 | 核对 #88/#89 合并状态，迁入完整规范正文，明确源仓状态差异与 Compiler #61 未完成边界 | Issue #12；SR-023；SR-013 |
| 2026-11-25 | 0.2.1 | Codex / GPT-6 | 正文 | §4 对齐中央设计与语言发布责任 | Issue #12 |
| 2026-11-26 | 0.2.2 | Codex / GPT-6 | 见本行变更 | 区分数字版本的新发布物和固定来源的实际机器标识 | Issue #12 |
| 2026-11-26 | 0.2.3 | GPT-6.2（ChatGPT） | 文档头、§1、§6、修订记录 | 根据 Issue #40 明确下一正式目标改为 CA-SL 1.6.0（不使用 v1alpha6），定义 Capability-first 与历史冻结发布边界；避免反复 alpha 命名、静默重解释 v1alpha5 或提前宣称 1.6.0 已发布 | Issue #40；SR-029；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.2.4 | GPT-6.2（ChatGPT） | §1、§4、§6、修订记录 | 将无兼容要求冻结为 1.6.0 全链路单版本强制规则：不接受旧语法、旧 Build DTO、旧 Bundle、旧 Artifact、迁移或 fallback；历史记录仅审计留档，不让旧产物成为新版合法输入 | Issue #40/#43；SR-029；SR-004 |
| 2026-11-26 | 0.2.5 | GPT-6（ChatGPT） | 文档头、修订记录 | 统一 1.6.0-only 设计待评审状态，不提升产品发布状态 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.6 | GPT-6（ChatGPT） | 规范性设计与验收门槛 | 修正旧 G.4/Development 1.0.0 规范权威，唯一新目标为 1.6.0 | Issue #12/#40；SR-013/025/029；PR #46 |
