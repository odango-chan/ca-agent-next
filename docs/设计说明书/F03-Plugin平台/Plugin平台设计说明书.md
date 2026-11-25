# Plugin 平台设计说明书

> 文档类型：机制设计说明书  
> 文档版本：0.3.0  
> 状态：Next 目标设计；Plugin Package/IPC 规范已进入主线文档，运行时代码尚未完成  
> 功能归属：F03 — Plugin 平台  
> 关联 SR：SR-003、SR-010、SR-015、SR-017  
> 修订日期：2026-11-25  
> 适用范围：唯一 Python Plugin Manager、Native Plugin、Event/Delivery/Tools Extension 与 ca-client-tools 适配

关联需求见 IR-002、IR-005、IR-006。外部原始架构及设计资产见本文件 §13。

## 1. 目标与边界

Plugin 是 Host 管理的独立包/进程及生命周期单元。它是 Agent Core 对外部协议和可调用能力的统一扩展机制。Event ingress、response delivery、Tool invocation 都通过同一个 Plugin Manager、同一进程模型和同一 IPC 协议完成。

核心目标是：新增业务时，通过新增 Plugin、Skill、Tool Interface Package 和部署配置扩展，不在 Agent Core、Runtime 或 Plugin Manager 中增加业务专用分支。

### 1.1 范围

- 一个 Python Plugin Manager。
- Native Plugin Manifest、包结构和进程生命周期。
- stdio NDJSON IPC v1alpha1。
- event.ingress、event.delivery、tools 三种 Extension。
- Correlation、Error、Cancellation、Shutdown。
- Tool Interface Package 引用与 ca-client-tools Provider v2 适配。
- Plugin 与 Host Artifact Handoff 的边界。

### 1.2 非目标

不建立独立 Provider Manager、Tool Registry、Event Registry、Delivery Manager、Codec Manager 或第二套 IPC；不在 Plugin 中选择 Skill、创建 Run、决定执行模式、授权 Action 或判定 Owner 提交；不引入 Marketplace、自动下载、签名、Trust Registry、生产级自动恢复平台或跨进程数据库。

## 2. 总体组件与所有权

~~~text
Python Host
  ├─ Agent Core / Skill Resolver
  ├─ Runtime Action Boundary
  ├─ Plugin Manager                 [唯一]
  │    ├─ Package / Manifest Loader
  │    ├─ Process Supervisor
  │    ├─ IPC Framer / Correlator
  │    └─ Extension Dispatcher
  └─ Host ArtifactStore
       ↑                       ↓
       │                       │ stdio NDJSON
       │             Native Plugin Process
       │               ├─ event.ingress
       │               ├─ event.delivery
       │               └─ tools
       │
       └─ opaque artifactRef / staging handoff
~~~

| 组件 | 负责 | 不负责 |
|---|---|---|
| Plugin Manager | Manifest 校验、进程启动/停止、握手、IPC、Correlation、Extension 分发 | Skill 选择、Action 授权、Owner outcome |
| Native Plugin | 实现声明的 Extension，持有外部协议连接和本地协议上下文 | 创建 Run、选择 Skill、扩大 Callable Scope |
| Event Extension | 解析外部协议、规范化 Event、提取声明的二进制 slot | 业务路由和 Skill 选择 |
| Delivery Extension | 按 Host 指令交付响应 | 选择响应义务或改变 Owner outcome |
| Tool Extension | 执行 Interface Package 定义的 Callable | 自行授权、重写 Tool Schema、伪造提交证明 |
| Runtime | 对 Action 做统一边界检查，解释 Tool/Owner 结果 | 管理 Plugin 进程 |
| Host ArtifactStore | 原始字节托管、opaque refs、Run/Invocation 关联和授权 | 协议深度解码 |

Tool 是 Plugin 导出的 Operation，不是独立进程或管理器。一个 Plugin 可以同时导出一种或多种 Extension。

## 3. Package 与 Manifest

标准包布局：

~~~text
plugins/<plugin-id>/
  plugin.yaml
  bin/<plugin-executable>
  schemas/
  resources/
~~~

Manifest 固定使用 connectionagent.io/plugin-package/v1alpha1；进程 IPC 固定使用 connectionagent.io/plugin-ipc/v1alpha1。Manifest 只声明身份、版本、进程入口和 Extension。Callable ID、输入输出 Schema、Effect、Capability、Artifact 参数和 Owner outcome 必须来自 Tool Interface Package，禁止在 Manifest 中复制。

Manifest 校验至少包含：

1. YAML 1.2 严格解析，拒绝重复 key、未知字段和不支持版本。
2. pluginId、版本、可执行文件和 Extension 声明完整。
3. executable、Schema、resources 路径解析后必须位于包根目录内；拒绝绝对路径、路径穿越和符号链接逃逸。
4. Event Schema、Artifact slot、mediaType 和 requiredness 与 Host/3GPP 契约一致。
5. tools.interfacePackage 精确引用已发布 Tool Interface Package。
6. Manifest 声明的 Extension 必须与进程握手返回内容一致。

Package 校验失败时 Plugin 不得启动为 READY，不得部分注册 Extension。

## 4. 生命周期与启动顺序

生命周期状态：

~~~text
CONFIGURED -> STARTING -> READY
                       -> NOT_READY
READY -> STOPPING -> STOPPED
~~~

启动顺序：

1. Host 读取部署配置中的 Plugin 安装路径。
2. Plugin Manager 读取并校验 Manifest 和包内资源。
3. 解析 Tool Interface Package 引用和 Event Schema。
4. 启动可执行文件；不经 Shell 拼接参数。
5. 发送 host.initialize，包含 Plugin 身份、期望版本、IPC 版本、部署配置和必要的 Host staging 目录。
6. 接收 plugin.ready，验证 pluginId、pluginVersion、ipcVersion 和实际 Extensions。
7. 只有全部一致时才把 Plugin 置为 READY，并注册其 Extensions。

Plugin 进程退出、握手超时、非法帧或版本不匹配时，Plugin 置为 NOT_READY；相关操作明确失败。Demo 阶段不要求自动重启、热升级或跨主机调度。配置变更通过显式部署配置和 Host 重启生效。

## 5. IPC 与消息关联

Native Plugin 使用 UTF-8 NDJSON over stdin/stdout。Host 写 stdin，Plugin 写 stdout；stdout 只能承载协议帧，诊断输出到 stderr。单进程连接承载 initialize、Event、Tool、Delivery、cancel 和 shutdown。

每帧包含 apiVersion、messageId、可选 correlationId、type 和 payload。以下 ID 不得混用：messageId、correlationId、eventId、externalRequestId、responseChannelId、runId、invocationId、deliveryId、responseObligationId、catalogGeneration。

核心消息：

| 方向 | 消息 | 作用 |
|---|---|---|
| Host → Plugin | host.initialize | 初始化进程与 Host-owned staging |
| Plugin → Host | plugin.ready | 握手完成 |
| Plugin → Host | ingress.event | 发布规范化 Event |
| Host → Plugin | ingress.ack | 接收、重复关联、冲突或拒绝 |
| Host → Plugin | tools.invoke | Runtime 已放行的 Callable 调用 |
| Plugin → Host | tools.result | 返回 Interface Package 定义的结果或错误 |
| Host → Plugin | delivery.dispatch | 按 responseObligationId 交付响应 |
| Plugin → Host | delivery.result | 报告 delivered / failed / unknown |
| Host → Plugin | host.cancel | 请求取消 |
| Plugin → Host | plugin.cancelled | cancelled / too_late / unsupported |
| Host → Plugin | host.shutdown | 请求优雅退出 |
| Plugin → Host | plugin.stopped | 停止确认 |

所有回复必须按 correlationId 关联原请求。未知消息、错误版本、缺失关联、重复 response 或非法 payload 必须 fail closed。一个进程可以并发处理多个 operation，但必须串行写 stdout，且每个响应准确匹配 invocationId/deliveryId。

## 6. Event Ingress Extension

Event Plugin 负责外部协议 framing、认证上下文、JSON/multipart 解析、Content-ID 关联、声明 slot 的原始字节提取和规范化 Event。Host 对 Event Schema 做最终校验，并由 Host 创建 Run 与 responseObligation。

规范化 Event 至少包含 eventId、ingressId、eventType、externalRequestId、responseChannelId、source、payload 和 artifacts。

- eventId 是逻辑 Event 实例身份，不是 IPC messageId 或 HTTP/2 stream ID。
- externalRequestId 使用外部协议定义的稳定重试身份；不得以瞬时 stream ID 代替。
- responseChannelId 是 Plugin 的本地响应句柄，不是 Run ID。
- payload 仅包含规范化 JSON，不包含 Skill ID、Goal、执行模式或 Capability Grant。
- artifacts 只包含 Manifest 已声明的 slot 描述符。

Plugin 不选择 Skill。每个新业务 Event 必须先由 F02 Resolver 绑定 Skill，再进入 Runtime。无候选、输入冲突或未知 discriminator 时停止并产生诊断；不允许 unbound Generic Agent fallback。

相同 externalRequestId 的相同请求重试可关联原 Run 并建立新的 responseObligation；同 ID 不同 payload 或原始 Artifact 字节冲突必须拒绝。不能证明相同请求时不重放 mutation。

## 7. Event Delivery Extension

Host 在 Event 被接收时创建 responseObligation，记录原始 Run、Event、外部请求身份和 Plugin responseChannel。Runtime 完成后，Host 根据原 Run 的结果构造结构化响应，并发送 delivery.dispatch。

Delivery Plugin 只负责将 Host 提供的响应编码为外部协议响应、附加允许的 N1/N2 Artifact，并向原 responseChannel 交付。它不得重新选择 Run、Skill 或 Owner Outcome。

delivery.result 只表示交付事实：
- delivered：外部响应通道确认发送；
- failed：明确未完成交付；
- unknown：交付是否发生无法证明。

Delivery unknown 不得改变 Owner Receipt，也不得导致业务 mutation 重放。

## 8. Tools Extension 与 ca-client-tools

Tool Plugin 通过 tools Extension 导出 Callable。运行时调用链固定为：

~~~text
LLM / Procedure Engine
  -> Runtime Action Request
  -> Runtime checks Skill Callable Scope + schema + Run state
  -> Plugin Manager
  -> tools.invoke
  -> Tool Plugin
  -> tools.result
  -> Runtime interprets typed result / Owner Receipt
~~~

ca-client-tools 是 Tool Interface Package、Provider、SBI client 和 Codec 能力的外部所有者。其当前 Provider v2 进程由 Next Plugin Manager 的 tools Extension Driver 适配；不复制 Owner Tool 实现，不建立第二个 Provider Manager。Provider v2 与 Next Plugin IPC 是不同协议，适配器只做字段/帧映射，不得改变 Callable、Effect、Schema 或 Owner Receipt 语义。

Codec 如果正式发布，也作为同一个 tools Extension 中的普通 Callable，不新增 Codec Manager。ca-client-tools PR #39 当前仍 OPEN；Phase B worker/facade 不等于 Agent 消费集成完成，Phase C consumer integration 需单独验收。

## 9. Artifact Handoff 与二进制边界

原始 N1/N2 不进入 NDJSON，不使用 Base64，不直接放入 LLM Context。

- Event Plugin 从协议中提取原始字节，写入 Host 提供的 inbound staging directory。
- Plugin 仅提交相对 stagingPath、slot、mediaType、contentId 和实际 byteLength 描述符。
- Host 校验 staging path、slot、大小和本次 Event 关联后导入 Host-owned ArtifactStore，发放 opaque artifactRef。
- Runtime 决定当前 Action 是否可以读取或生成该 Artifact。
- Tool Plugin 仅接收当前 invocation 已授权的 artifactRef；具体字节通过 Host 的 invocation-scoped artifact stream 交接。
- Delivery 输出由 Host 写入 outbound staging，Plugin 按 delivery.dispatch 读取并编码。
- Plugin 不拥有 ArtifactStore、业务 Run 关联或持久化 Artifact 数据库。

不增加额外 SHA-256、独立 Artifact Service 或生产级内容完整性机制。

## 10. 错误、取消与重试

统一错误对象包含 code、message、retryable 和可选 details。retryable 只是传输重试提示，不证明 mutation 未提交。

| 场景 | 行为 |
|---|---|
| Manifest / Schema 无效 | Plugin 不启动 |
| 握手不匹配 | Plugin NOT_READY，不注册 Extension |
| IPC 帧损坏 / correlation 错误 | 当前 operation 失败关闭，记录诊断 |
| Plugin 进程异常退出 | 未完成调用返回明确失败或 UNKNOWN；不伪造成功 |
| Tool 超时 | Runtime 根据 Effect/Owner Receipt 判定；不能仅凭超时断言 NOT_COMMITTED |
| Delivery 超时 | delivery unknown，保留 responseObligation 状态 |
| Cancel too_late | 仅表示取消未能阻止 operation，不表示业务回滚 |
| 同一外部请求重复 | 精确身份匹配时关联原 Run；冲突则拒绝 |

Host 负责 Run/Invocation 的重试策略；Plugin 不得自行重新发起业务 mutation。

## 11. Demo 部署与运维

Plugin 由本地显式安装路径和部署配置加载。Host 启动时校验并启动进程；Plugin 独立日志输出到 stderr。Demo 只要求明确的启动失败、运行错误、关闭和可诊断状态。不建设 Marketplace、在线安装、自动升级、生产级隔离容器、HA 或多租户调度。

## 12. 当前实现审计

| 对象 | 当前状态 | 证据与限制 |
|---|---|---|
| Next Plugin Package/IPC 规范 | 文档已合入 Next main | Next PR #1 已合并；规范不等于运行时代码 |
| Next Python Plugin Manager | NOT_IMPLEMENTED | 本轮仅恢复设计与规范 |
| ca-client-tools Provider v2 | IMPLEMENTED / RELEASED | main 7bcb261；Provider v1.1.0；尚需 Next adapter |
| ca-client-tools Codec Phase B | OPEN | PR #39 head eb1169f；未合并 |
| ca-agent-demo Provider v1.1.0 runtime cutover | OPEN | PR #246 head 68a6f9e；不是 main 证据 |
| ca-openamsm-plugin | NOT_IMPLEMENTED | main eb83c8f 只有 README；PR #1 为 OPEN/Draft 设计提案 |
| Next Plugin / Echo / OpenAMSM E2E | NOT_RUN | 需在 Next Host 代码落地后执行 |

## 13. 原始设计与来源

- [ca-agent-demo Generic Host 架构原文](../../架构设计/参考实现/REF01-Python%20Generic%20Agent%20Host规范架构.md)
- [ca-agent-demo v0.5 Plugin 下一版本架构原文](../../架构设计/参考实现/REF01-Plugin下一版本目标架构.md)
- [ca-client-tools Tool/Provider 架构原文](../../架构设计/外部能力域/EC03-Tool与Provider架构原文.md)
- [EC03 Provider Protocol v2 原文](../外部能力域/EC03-Tool%20Provider/Provider%20Protocol%20v2契约原文.md)
- [EC03 Runtime Bindings 原文](../外部能力域/EC03-Tool%20Provider/Runtime%20Bindings设计原文.md)
- [EC04 OpenAMSM Plugin Draft 架构原文](../../架构设计/外部能力域/EC04-OpenAMSM%20Go%20Event%20Plugin架构提案原文.md)
- [Plugin Package/IPC 规范](../../规范/插件包与进程通信协议规范.md)
- [公共契约与所有权规范](../../规范/公共契约与所有权规范.md)

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.2.2 | GPT-6.2（ChatGPT） | 全文 | 按 Next 唯一 Plugin Manager、Provider v2 适配和 ca-openamsm-plugin 候选设计恢复完整边界 | Issue #12；SR-015～017 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | 全文 | 补齐 Manifest、生命周期、IPC、Event/Delivery/Tools、Artifact、错误与当前实现审计 | Issue #12 |
