# SR-008：Echo 垂直端到端示例

> 文档类型：软件需求（SR）  
> SR 版本：0.1.1  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase F  
> 设计依据：演示验收基线 §1～§6；实施路线与阶段门槛 §6  
> Acceptance：EX-17  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

以业务中立 Echo 验证 Python Core、唯一 Plugin Manager、两种 Skill 形态、Resolver、Runtime 和 Delivery 的完整链路。

## 2. 实施范围

- 一个 Go Plugin 同时暴露 Event、Delivery 和 Tool。
- 一个 SKILL.md-only Skill 走 LLM-guided。
- 一个含有效发布 Assurance Artifact 的 Skill 验证 Deterministic 和 LLM-guided。
- 覆盖导入、选择、Action Scope、Outcome/Evidence 和响应交付。

## 3. 非目标

- 不引入 OpenAMSM 业务代码。
- 不以单元测试代替垂直 E2E。

## 4. 依赖与前置条件

SR-002～SR-007。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. Echo Event → Skill → Run → Tool → Outcome/Evidence → Delivery 完整运行。
2. 两种 Skill 形态和两种执行模式按设计工作。
3. Demo Acceptance 中 Echo 适用项全部有真实运行证据。
4. 不依赖 OpenAMSM 专用逻辑。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-agent-next |
| GitHub Issue | 未创建 |
| 实施 PR | 未创建 |
| Commit | 无 |
| 实施状态 | NOT_STARTED |
| 验收证据 | NOT_RUN |

ca-agent-next PR #1 是设计基线 PR，不是本 SR 的实现 PR，不得在此标记实施完成。

## 7. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：初始分解；等待设计基线评审。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续发生语义变化时创建新的 SR 并引用本 SR，不覆盖历史要求。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-008 |

| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |