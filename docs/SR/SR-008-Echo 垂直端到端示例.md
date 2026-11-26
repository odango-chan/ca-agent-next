# SR-008：Echo 垂直端到端示例

> 文档类型：软件需求（SR）  
> SR 版本：0.1.10\
> 状态：DRAFT（SR 实施主状态）；**设计待评审 / REVIEW_REQUESTED**，未获得实施 READY，产品验收 NOT_RUN  
> 创建日期：2026-11-25  
> 修订日期：2026-11-26  
> 所属阶段：Phase F  
> 上游需求：[IR-004](../IR/IR%20总登记册.md#ir-004)  
> 设计依据：[演示验收基线](../验收与实施/演示验收基线.md) v0.3.21 §1～6；[实施路线与阶段门槛](../验收与实施/实施路线与阶段门槛.md) v0.2.11 §6\
> Acceptance：EX-17（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查一个 Go Plugin 组合 Event/Tool/Delivery、指导型与 Assurance Skill 的同链路、正反向和失败案例。
- **已知依赖与未验证项：**Echo 的新 Assurance Bundle 需要 1.6.0 重编译发布；旧版 Example/编译脚本不算新系统验收，EX-17 NOT_RUN。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

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

设计按 F07 与 F02/F04 对照两种模式的输入和预期。组合执行消费 SR-002～007 对应模块证据与 SR-027 的 Echo Bundle。Go Plugin 对测可用固定源码，只有正式组合运行可记 EX-17。 设计可按 SR 管理规范 §6.1 单独评审。

## 5. 验收条件

1. Echo Event → Skill → Run → Tool → Outcome/Evidence → Delivery 完整运行。
2. 两种 Skill 形态和两种执行模式按设计工作。
3. Demo Acceptance 中 Echo 适用项全部有真实运行证据。
4. 不依赖 OpenAMSM 专用逻辑。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

### 实施位置与复验入口

以下路径为本 SR 的目标交付物。在 ca-agent-next 仓根运行，测试通过公开入口调用受测组件。目标位置为 `examples/echo/`、测试 Host 的公开进程入口。在独立临时目录运行同一 Go Plugin、一个已发布 Assurance Echo 包和 Fake Model。对相同输入分别指定两种允许模式，校验 Run、调用与交付的 correlation；再以纯指导包验证无 Compiler 调用和无声明 Tool 的拒绝。测试结束关闭进程并清理本次临时目录。发布方为 ca-skills。执行正式 Echo 组合验收前登记 Echo 的作者源 commit、外部 Compiler tag/SHA、发布资产路径、Artifact API 与 Verify 日志。固定 ca-skills 审计树 `780497a2918ad3e7bdff554ab64b0ba627e867e0` 没有名称含 Echo 的作者包；若已有异名合适资产，由发布方提供该组证据。若需要增加作者包，在 ca-skills 的独立实施 SR 中跟踪，Next 不自行生成或伪造运行包。

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

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史记录未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-008 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-008 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史记录未细分 | 校正当前设计依据版本 | 核对 Issue #12 与固定提交 | SR-008 |
| 2026-11-25 | 0.1.4 | Codex / GPT-6 | §5 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-25 | 0.1.5 | Codex / GPT-6 | §5 | Codex / GPT-6 · §5 明确 Echo 输入的发布方、缺件和恢复条件 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-26 | 0.1.6 | 未记录（历史资料未提供） | 历史记录未细分 | 对齐外部 Echo 生产端 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.7 | Codex / GPT-6 | §4～5 | Codex / GPT-6，§4～5。分别登记设计输入、实施接入和验收依赖。 | 使 Harness 能按当前阶段判定启动与验收条件 | Issue #12、#21 |
| 2026-11-26 | 0.1.8 | GPT-6.2（ChatGPT） | §1 | 将 Acceptance 设计依据更新至 v0.3.8 | 避免 Echo 设计继续引用过期验收版本 | Issue #26 |
| 2026-11-26 | 0.1.9 | GPT-6.2（ChatGPT） | 文档头部 | 将 Acceptance 设计依据更新至 v0.3.9 | 与 SR-002 集成后当前演示验收基线保持一致 | PR #25；Issue #26 |
| 2026-11-26 | 0.1.10 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
