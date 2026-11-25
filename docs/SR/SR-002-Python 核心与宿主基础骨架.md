# SR-002：Python 核心与宿主基础骨架

> 文档类型：软件需求（SR）  
> SR 版本：0.1.0  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase A  
> 设计依据：CA Agent Next 架构设计 §3～§5；实施路线与阶段门槛 §1  
> Acceptance：EX-01  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

建立 Python Agent Core、Host 和 Model Loop 的最小可运行骨架，明确模块边界，为后续 Plugin、Skill 和 Runtime 提供稳定宿主。

## 2. 实施范围

- 建立 Python 包结构、Host 入口和 Agent Model Loop。
- 定义基础 Context、Event、Run 类型及模块边界。
- 为后续 Plugin Manager、Skill Importer、Resolver 和 Runtime 提供稳定的模块调用边界。

## 3. 非目标

- 不迁移整个 ca-agent-demo。
- 不引入 OpenAMSM 专用业务逻辑。
- 不把 Agent Core 改为 Go。

## 4. 依赖与前置条件

无；ca-agent-demo 仅作为只读复用证据。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. Host 可启动并执行最小 Model Loop。
2. 核心模块边界清晰，公开入口有自动化测试。
3. Agent Core、Host、Model Loop 均为 Python。
4. 不包含 OpenAMSM 业务分支或复制的业务执行器。

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
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-002 |
