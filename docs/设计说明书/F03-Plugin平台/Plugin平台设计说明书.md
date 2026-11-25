# Plugin 平台设计说明书

> 文档类型：机制设计说明书  
> 状态：目标设计，待实现和验收  
> 文档版本：0.2.2  
> 功能归属：F03 — Plugin 平台  
> 关联 SR：SR-003、SR-010    
> 全局评审范围：继承根目录 Agent.md 的 review_scope    
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  
> 修订日期：2026-11-25  
> 适用范围：Python Plugin Manager、独立进程 Plugin、Package、IPC 与 Extension 分发  
> 对应规范：[插件包与进程通信协议规范](../../规范/插件包与进程通信协议规范.md)

关联需求项见 [IR-002](../../IR/IR%20总登记册.md#ir-002)、[IR-005](../../IR/IR%20总登记册.md#ir-005)。

## 1. 背景与目标

将 Event ingress、Tool 调用和 Event delivery 统一为一种 Plugin 机制。Plugin 是独立包/进程和生命周期管理单元；Extension 是 Plugin 对 Host 暴露的能力接口。目标是避免为 Tool、Provider、Event、Delivery、Codec 分别建立 Manager、Registry、IPC 和授权路径。

## 2. 设计原则

1. 全系统只有一个 Plugin Manager。
2. 一个 Plugin 进程可以导出一种或多种 Extension。
3. Tool 是 Plugin 导出的可调用 Operation，不是独立进程。
4. 一个 Plugin 可以导出多个 Capability，一个 Capability 可以包含多个 Operation。
5. Plugin Manager 负责生命周期、握手、IPC 和 Extension 分发，不负责 Skill 选择、Action 授权或 Owner 结果判断。
6. Tool Interface Package 是 Tool 契约权威源；Plugin Manifest 不复制 Tool 定义。
7. ToolCatalog 只是可发现能力的只读视图，不管理生命周期，也不构成第二个 Registry。

## 3. 组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Plugin Manager | 加载包、校验 Manifest、启动/停止进程、握手、IPC、关联、Extension 分发 | Skill 选择、授权、Owner Commit 判断 |
| Plugin Process | 实现声明的 Extension，访问自己拥有的资源 | 选择 Skill、扩大 Capability |
| Event Extension | 解析外部协议并发布规范化 Event | 业务 Skill 映射、Owner Tool 调用 |
| Tool Extension | 执行 Interface Package 定义的 Operation | 自行授权、声明业务提交 |
| Delivery Extension | 按 Host 指令向外部协议响应方交付 | 选择 Run、改变 Owner outcome |
| Tool Interface Package | Callable ID、Schema、Effect、Capability 和 Owner 结果契约 | 进程生命周期 |

## 4. 包与进程模型

原生 Plugin 使用 YAML Manifest，包内包含 plugin.yaml、可执行文件和本包拥有的 Schema/资源。Manifest 的 apiVersion 固定为 connectionagent.io/plugin-package/v1alpha1；进程 IPC 使用 connectionagent.io/plugin-ipc/v1alpha1。Manifest 声明进程入口和 Extensions，不声明 Skill ID、业务 Goal、业务授权或 Tool 的完整 Schema。

~~~text
plugins/<plugin-id>/
├── plugin.yaml
├── bin/<plugin-executable>
├── schemas/
└── resources/
~~~

完整字段和示例以规范为准，不能在实现时另造别名或 fallback 版本。

## 5. 加载与生命周期

启动顺序：

1. 读取 plugin.yaml，使用安全 YAML 1.2 解析器，拒绝重复 YAML key。
2. 校验 API 版本、Plugin 身份、Extension 结构和必填字段。
3. 解析相对包根目录的可执行文件、Schema 和资源路径；拒绝绝对路径、路径穿越和逃逸包根的符号链接。
4. 校验 Event Schema，并按引用加载 Tool Interface Package。
5. 启动独立进程，发送 host.initialize。
6. 接收 plugin.ready，核对 Plugin ID、版本、IPC 版本和实际 Extension 列表。
7. 只有握手匹配的 Extension 才进入可用状态；失败时该 Plugin 不可用并提供可诊断错误。

Demo 使用显式安装路径和操作员提供的进程参数。修改 Plugin 后重启 Host 即可，不要求 Marketplace、自动下载、通用安装器、文件监视器或热更新。

## 6. IPC 与消息分发

Native Plugin 使用 UTF-8 NDJSON over stdin/stdout。stdout 仅承载协议帧，诊断信息写入 stderr。每帧有 apiVersion、messageId、可选 correlationId、type 和 payload。

| 方向 | 消息 | 用途 |
|---|---|---|
| Host → Plugin | host.initialize | 传入身份、版本、配置和 Artifact staging 目录 |
| Plugin → Host | plugin.ready | 握手确认 |
| Plugin → Host | ingress.event | 发布规范化 Event |
| Host → Plugin | ingress.ack | 接收、重复关联、冲突或拒绝 |
| Host → Plugin | tools.invoke | 调用已授权 Operation |
| Plugin → Host | tools.result | 返回结果或错误 |
| Host → Plugin | delivery.dispatch | 履行 Host 已记录的响应义务 |
| Plugin → Host | delivery.result | 返回 delivered / failed / unknown |
| Host → Plugin | host.cancel | 请求取消 |
| Plugin → Host | plugin.cancelled | 报告取消结果 |
| Host → Plugin | host.shutdown | 请求进程退出 |
| Plugin → Host | plugin.stopped | 进程停止确认 |

messageId、correlationId、eventId、invocationId、deliveryId、responseObligationId 和 Run ID 是不同身份，不得互相替代。详细消息字段、错误对象和状态机见规范。

## 7. ca-client-tools 的迁移适配

ca-client-tools 当前 Provider v2 进程协议可以由统一 Plugin Manager 内部的 tools Extension Driver 适配。该适配只是一段迁移桥接，不得演变为永久 Provider Manager、第二套 Tool Registry 或第二条授权路径。

Plugin Manager 只转发 Runtime 已检查的调用。Tool Plugin 返回的传输成功不等于 Owner 业务 COMMITTED；Owner Receipt、Commit Proof 和 outcome mapping 由其 Interface Package 与 Runtime 解释。

Codec Operation 如正式发布，也通过同一个 tools Extension 暴露，不建立独立 Codec Plugin/Manager。Codec 具体可调用范围由 Interface Package 和已验收消息子集决定。

## 8. 错误处理

- Manifest、Schema、版本或路径无效：Plugin 加载失败。
- 握手身份或 Extension 不匹配：Plugin 不可用。
- IPC 关联不一致、未知消息类型或畸形 Payload：受影响操作失败关闭。
- Tool 不匹配 Interface Package：调用失败。
- Owner outcome UNKNOWN：保持 UNKNOWN，不得由 Plugin Manager 推断为 COMMITTED。
- Plugin 传输成功：只代表 IPC 层成功，不代表业务 mutation 已提交。

Demo 不增加签名、Trust Registry、包完整性哈希或生产级密钥体系。

## 9. 验收要求

- 一个 Plugin 进程可以同时暴露 Event、Delivery 和多个 Tool Operation。
- Plugin Manager 是唯一生命周期和 IPC 入口。
- Tool 调用必须经过 Runtime 的 Callable Scope 检查和统一 Manager。
- 不存在独立 Provider Manager、Tool Registry 或 Codec Manager。
- 错误版本、未知消息、错误关联、重复 YAML key、路径穿越均有自动化测试。
- Echo 示例证明组合 Plugin 的启动、握手、Event、Tool 和 Delivery 完整链路。

## 10. 当前实现状态

Plugin Package/IPC v1alpha1 是 PR #1 中的目标契约，不等于已完成实现。Provider v2 适配是迁移策略；何时切换 Native IPC 需由真实集成验收决定。




## 11. 功能归属与外部能力

本说明书属于 F03。SR-003 定义唯一 Plugin Manager 与 Extension IPC；SR-010 定义 OpenAMSM Tool Plugin 与按需 Codec 集成。Tool Interface Package、Provider 和 Codec 的内部契约以 EC03 ca-client-tools 为准；OpenAMSM Event/Delivery Plugin 的内部实现以 EC04 ca-openamsm-plugin 为准。Next 只维护 Manager 生命周期、Extension 分发和消费端边界。

### Tool Interface 与 Provider

Tool Interface 绑定 callable ID、参数、结果和 Effect，Provider v2 在工具进程分发。Next 适配通过唯一 Plugin Manager 的 tools Extension；已有 Codec 的接口和发布证据先按 SR-015 固定版本。 详见[分仓证据](../../参考与审计/跨仓设计资产迁移与一致性审计.md)。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 历史修订者/模型未记录 | 原始设计全文 | 既有功能机制设计基线；逐章历史记录未建立 | 原文档未记录历史作者，本轮不臆造 | PR #1 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 第 1～10 章 | 归入对应 Feature 并补充外部能力边界 | 按 F03 归档，明确统一 Plugin Manager 与外部 Tool Interface 权威边界 | F03；SR-003/010；EC03/EC04；PR #1 |
| 2026-11-25 | 0.2.1 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.2 | Codex / GPT-6 | Tool Interface 与 Provider | 合并有效边界与分仓证据入口 | 跨仓设计移交 | IR-006 |
