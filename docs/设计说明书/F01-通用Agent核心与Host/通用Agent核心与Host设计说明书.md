# 通用 Agent Core 与 Host 设计说明书

> 文档类型：功能设计说明书  
> 文档版本：0.1.1  
> 功能归属：F01 — 通用 Agent Core 与 Host  
> 关联 SR：SR-002  
> 状态：目标设计基线，待评审、实现和验收  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope

关联需求项见 [IR-002](../../IR/IR%20总登记册.md#ir-002)。

## 1. 目标与范围

本设计定义通用 Agent Core、Python Host 和 Agent Model Loop 的边界及最小生命周期。Agent Core 不包含 OpenAMSM、5GC 或其他业务专用路由、业务枚举、协议 Schema、Owner 操作和业务状态机。

Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 固定使用 Python。独立 Plugin 可以使用 Go；Plugin 的语言选择不改变 Host 语言。

## 2. 组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Host | 进程入口、配置、Event 接收协调、Run 生命周期、Model Loop 宿主 | 业务协议深度解码、业务状态机 |
| Agent Core | 通用任务协调、Context 组装、Skill 选择流程编排、执行模式协调 | OpenAMSM 专用分支、Owner 状态机 |
| Agent Model Loop | 与 Model Client 交互、产生受约束的推理/Action 提议 | 直接调用 Plugin、声明业务提交 |
| Skill Resolver | 按 F02 规则产生候选并绑定 Skill | 维护 Event→Skill 业务路由表 |
| Runtime | 接收 Action Request 并执行统一边界检查 | 承担模型推理或 Plugin 生命周期 |
| Plugin Manager | 按 F03 机制管理 Plugin 并分发 Extension | 选择 Skill、决定 Owner Outcome |

## 3. 主处理流程

~~~text
外部 Event
  → Host 接收规范化 Event
  → 创建或恢复 Run
  → Agent Core 组装基础 Context
  → Skill Resolver 绑定 Skill（F02）
  → 根据 Skill 发布资产派生执行模式（F02）
  → Model Loop / Procedure Engine 提出 Action
  → Runtime 统一执行（F04）
  → Host 整理结果并交给 Delivery Extension（F03/F05）
~~~

Continuation 不创建新的业务任务，不重新选择 Skill；Host/Runtime 必须按原 Run 和 Catalog generation 恢复。

## 4. Model Loop 与 Action 提议

Model Loop 只与 Model Client 交互，基于当前 Run、已绑定 Skill、Context 和允许的 Tool 描述生成下一步建议。模型输出不是可直接执行的调用。所有 Action 必须转换为统一 Runtime Action Request，经过 F04 的 Callable Scope、参数和 Run 状态检查后才能由 Plugin Manager 分发。

Model Client 接口应允许确定性 Fake Model Client 用于自动化测试，不将特定模型供应商硬编码到 Core。模型服务、模型选择和 Gateway 属于部署/基础设施配置，不改变 Agent Core 的业务中立性。

## 5. Context 与 Run 边界

Host 创建 Run 并关联规范化 Event、Skill、Catalog generation、当前执行状态和响应义务。Context 的具体数据来源、Observation/Evidence 和 Artifact Reference 由 F05 定义；本设计只规定 Host 如何协调其生命周期。

新 Event、重复 Event、Continuation 和 Delivery 回执必须区分。重复 Event 不得造成重复 mutation；Continuation 必须恢复精确原 Run。Skill 无候选、输入不足、模型输出无效、Runtime 拒绝 Action 或 Plugin 调用失败时，返回明确诊断，不得静默切换到未绑定 Skill 的通用执行路径。

## 6. 业务中立与扩展

新增业务只允许通过以下资产扩展：

- 外部业务 Event/Delivery Plugin。
- 一个或多个 Skill 及其已发布运行时 Artifact。
- Tool Interface Package 和对应 Tool Plugin。
- 部署配置、协议 Schema 和按需 Codec 能力。

新增业务不得要求修改 Agent Core、Skill Resolver、Runtime 或 Plugin Manager 中的业务专用条件分支。Echo 是第一个业务中立性验证；OpenAMSM 是第二个验证。

## 7. Demo 边界

本阶段不建设生产级调度集群、HA/DR、SLA、多地域或复杂多租户平台。基本生命周期、错误处理、重复消息保护、模块边界和可复核诊断属于 Demo 正确性要求。

## 8. 验收与追踪

SR-002 的验收要求为 EX-01：Host 能启动并执行最小 Model Loop；核心模块边界清晰；Host、Agent Core 和 Model Loop 均为 Python；不包含 OpenAMSM 业务分支或复制的业务执行器。完整测试命令、Commit 和证据在 SR-002 与实施状态记录中维护。

## 9. 文档修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 F01 的 Core、Host、Model Loop 和业务中立设计 | 为 SR-002 提供长期功能设计基线 | F01；SR-002；PR #1 |
| 2026-11-25 | 0.1.1 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
