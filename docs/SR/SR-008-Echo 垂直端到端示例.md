# SR-008：Echo 垂直端到端示例

> 文档类型：软件需求（SR）  
> SR 版本：0.1.6\
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase F  
> 上游需求：[IR-004](../IR/IR%20总登记册.md#ir-004)  
> 设计依据：[演示验收基线](../验收与实施/演示验收基线.md) v0.2.7 §1～6；[实施路线与阶段门槛](../验收与实施/实施路线与阶段门槛.md) v0.2.3 §6\
> Acceptance：EX-17（见[演示验收基线](../验收与实施/演示验收基线.md)）  
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

### 实施位置与复验入口

以下路径为本 SR 的目标交付物。在 ca-agent-next 仓根运行，测试通过公开入口调用受测组件。目标位置为 `examples/echo/`、测试 Host 的公开进程入口。在独立临时目录运行同一 Go Plugin、一个已发布 Assurance Echo 包和 Fake Model。对相同输入分别指定两种允许模式，校验 Run、调用与交付的 correlation；再以纯指导包验证无 Compiler 调用和无声明 Tool 的拒绝。测试结束关闭进程并清理本次临时目录。发布方为 ca-skills。READY 前登记 Echo 的作者源 commit、外部 Compiler tag/SHA、发布资产路径、Artifact API 与 Verify 日志。固定 ca-skills 审计树 `780497a2918ad3e7bdff554ab64b0ba627e867e0` 没有名称含 Echo 的作者包；若已有异名合适资产，由发布方提供该组证据。若需要增加作者包，在 ca-skills 的独立实施 SR 中跟踪，Next 不自行生成或伪造运行包。

验收命令为 `python -m unittest discover -s tests -p test_echo.py -v`。必须发现并执行本节正反例；发现 0 个测试或跳过必需用例时，退出码 0 也不能计入 PASS。逐个 Acceptance ID 回填受测 SHA、命令、预期与实测值及日志位置。

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

### Echo 的外部交付

首批可执行 Echo 的作者源、固定 Compiler 和 Bundle 候选由 [SR-027](SR-027-技能Bundle构建与发布.md) 交付。测试 Host 与 Plugin 的协议 fixture 可以先验收。正式组合用例必须使用同一资产。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-008 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.2 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-008 |
| 2026-11-25 | 0.1.3 | 校正当前设计依据版本 | 核对 Issue #12 与固定提交 | SR-008 |
| 2026-11-25 | 0.1.4 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-25 | 0.1.5 | Codex / GPT-6 · §5 明确 Echo 输入的发布方、缺件和恢复条件 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-26 | 0.1.6 | 对齐外部 Echo 生产端 | 对齐跨仓实现与独立复验 | Issue #12 |
