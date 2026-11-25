# Plugin 包与 IPC 协议规范

> 文档类型：公共格式与进程通信规范  
> 状态：目标契约，待 PR #1 评审；不是实现完成声明  
> 修订日期：2026-11-25  
> 适用范围：ca-agent-next Plugin Manager 与所有 Native Plugin  
> 契约版本：connectionagent.io/plugin-package/v1alpha1；connectionagent.io/plugin-ipc/v1alpha1

## 1. 统一 Plugin 机制

Plugin 是由唯一 Python Plugin Manager 管理的独立包/进程单元。一个进程可以导出一种或多种 Extension：

| Extension | 方向 | 含义 |
|---|---|---|
| event.ingress | Plugin → Host | 发布规范化外部 Event |
| event.delivery | Host → Plugin | 向原协议响应通道交付结构化响应 |
| tools | Host → Plugin | 导出可调用 Tool Operation |

Tool 是 Operation，不是独立进程、Package、Manager 或 Runtime。Tool Plugin 是导出 tools Extension 的 Plugin。不存在独立 Provider Manager、Tool Registry、Event Registry、Delivery Manager 或 Codec Manager。

Plugin Manager 管理进程生命周期、握手、IPC framing、correlation 和 Extension 分发；不选择 Skill、不授权 Action、不判断 Owner 是否提交。

## 2. 包结构

~~~text
plugins/<plugin-id>/
├── plugin.yaml
├── bin/
│   └── <plugin-executable>
├── schemas/
└── resources/
~~~

Manifest 使用 YAML。Tool 定义不复制进 Manifest；Callable ID、IO Schema、Effect、Capability 和 Owner outcome 由权威 Tool Interface Package 定义。

## 3. Manifest 规范示例

~~~yaml
apiVersion: connectionagent.io/plugin-package/v1alpha1
kind: Plugin
metadata:
  id: urn:connectionagent:plugin:openamsm
  version: 0.1.0

process:
  executable: bin/ca-openamsm-plugin
  args: [serve]
  protocol: connectionagent.io/plugin-ipc/v1alpha1

extensions:
  event.ingress:
    events:
      - type: nsmf.create-sm-context
        description: Normalized Nsmf CreateSMContext request.
        requestSchema: schemas/create-sm-context.request.schema.yaml
        artifacts:
          input:
            - slot: n1.request
              mediaType: application/vnd.3gpp.5gnas
              required: true
            - slot: n2.request
              mediaType: application/vnd.3gpp.ngap
              required: false
      - type: nsmf.update-sm-context
        description: Normalized Nsmf UpdateSMContext request.
        requestSchema: schemas/update-sm-context.request.schema.yaml
        artifacts:
          input:
            - slot: n1.request
              mediaType: application/vnd.3gpp.5gnas
              required: true

  event.delivery:
    responses:
      - eventType: nsmf.create-sm-context
        responseSchema: schemas/response.schema.yaml
        artifacts:
          output:
            - slot: n1.response
              mediaType: application/vnd.3gpp.5gnas
              required: false
            - slot: n2.response
              mediaType: application/vnd.3gpp.ngap
              required: false

  tools:
    interfacePackage: <canonical-interface-package-reference>
~~~

上述 tools.interfacePackage 的引用值必须使用已发布 Tool Interface Package 的权威身份/引用；不得在 Plugin Manifest 里复制 Callable 定义。引用解析细节必须与 Interface Package 发布契约和部署配置一致，不得自行增加另一套 Tool Registry。

## 4. Manifest 字段规则

- apiVersion 固定为 connectionagent.io/plugin-package/v1alpha1。
- kind 固定为 Plugin。
- metadata.id 是稳定 Plugin 身份；metadata.version 是安装的 Plugin 版本。
- process.executable 相对安装包根目录；process.args 按参数数组传递，不经 Shell 字符串解释。
- process.protocol 固定为 connectionagent.io/plugin-ipc/v1alpha1。
- extensions 至少声明 event.ingress、event.delivery、tools 中的一种；允许同一进程同时声明多种。
- Event Schema 描述规范化 Event payload，不包含 Skill ID、业务 Goal、执行模式或授权 Grant。
- Event 的 artifacts.input 声明入站 slot；Delivery 的 artifacts.output 声明出站 slot。每项包含 slot、mediaType、required。
- Event slot 名称和 requiredness 必须与对应 3GPP OpenAPI 和 Host Artifact Handoff 设计一致；未声明 slot 必须拒绝。
- event.delivery 按 eventType 关联响应 Schema；Host 创建 responseObligation，Plugin 不选择 Run 或响应义务。
- tools.interfacePackage 引用权威 Tool Interface Package；Plugin Manifest 不重复其 Schema/Callable/Evidence 语义。
- 未知字段、重复 YAML key、缺失字段、不支持的版本、无效 Schema 引用和逃逸包根的路径均导致加载失败。

Manifest 不是业务 Contract、ToolCatalog、Skill Descriptor 或授权文件。

## 5. Plugin 加载与握手

唯一 Plugin Manager 在 Host 启动时：

1. 使用安全 YAML 1.2 解析器读取 plugin.yaml，拒绝重复 key。
2. 校验结构、精确 API 版本、Plugin 身份和 Extension 声明。
3. 将 executable、Schema 和资源路径解析到安装包根目录内；拒绝绝对路径、路径穿越和符号链接逃逸。
4. 校验 Event Schema，并按引用解析 Tool Interface Package。
5. 直接启动进程并发送 host.initialize。
6. 接收 plugin.ready，核对 Plugin ID、版本、IPC 版本和 Extension 列表。
7. 仅注册与 Manifest 匹配的 Extension。失败时 Plugin 不可用，并输出可诊断错误。

Demo 使用显式安装路径和操作员提供的进程参数。新增/修改 Plugin 通过部署配置和 Host 重启生效。不要求 Marketplace、安装器、自动下载、热更新、签名或 Trust Registry。

## 6. 规范化 Event 信封

Event Plugin 负责外部协议解析与规范化。Host 只接收已声明 Event type 和 JSON payload。

~~~json
{
  "eventId": "event-123",
  "ingressId": "openamsm.nsmf",
  "eventType": "nsmf.create-sm-context",
  "externalRequestId": "protocol-stable-request-id",
  "responseChannelId": "plugin-local-channel-456",
  "source": {
    "protocol": "3gpp-sbi",
    "peerId": "authenticated-peer"
  },
  "payload": {
    "requestType": 1
  },
  "artifacts": []
}
~~~

字段语义：

- eventId：逻辑 Event 实例 ID，不等于 IPC messageId 或 HTTP/2 stream ID。
- ingressId：Manifest 中精确声明的 ingress Extension ID。
- eventType：精确声明的规范化 Event 类型。
- externalRequestId：外部协议定义的稳定请求/重试身份；不得用 HTTP/2 stream ID 伪造。
- responseChannelId：Plugin 本地响应通道句柄，不是 Host Run ID 或持久业务身份。
- source：由 Plugin 建立的协议和对端上下文。
- payload：按 Event request Schema 校验的规范化 JSON。
- artifacts：可选二进制描述符，遵循 Host Artifact Handoff。

Host 分配 Run ID 和 responseObligationId。Plugin 不得提供 Skill ID、选择 Skill、指定 Run 或选择执行模式。

同一个稳定 externalRequestId 的相同请求重试可以附加新的 responseObligation 到原 Run；同 ID 不同规范化内容或真实 Artifact 字节冲突时必须失败。无法证明身份或相等性时 fail-closed，不重复执行 mutation。

## 7. IPC v1alpha1 信封

Native Plugin 使用 UTF-8 NDJSON over stdin/stdout：

- Host 写入 Plugin stdin。
- Plugin 写入 stdout。
- stdout 只承载协议帧；诊断写入 stderr。
- 一个长生命周期进程连接承载初始化、Event、Tool、Delivery、取消和关闭。
- Plugin 不导入 Python Host 模块，不创建第二套 Host API。

每帧格式：

~~~json
{
  "apiVersion": "connectionagent.io/plugin-ipc/v1alpha1",
  "messageId": "frame-123",
  "correlationId": "frame-100",
  "type": "ingress.ack",
  "payload": {}
}
~~~

- apiVersion：精确 IPC 版本。
- messageId：当前帧唯一 ID。
- correlationId：回复或延续现有请求时必须提供，值为被回复请求的 messageId；独立 ingress.event 可省略。
- type：下表中的精确消息类型。
- payload：消息类型对应对象。

messageId、correlationId、eventId、invocationId、deliveryId、responseObligationId 和 Run ID 必须保持不同。

## 8. 消息清单

| 方向 | type | 必需 payload 字段 | 含义 |
|---|---|---|---|
| Host → Plugin | host.initialize | pluginId, expectedVersion, ipcVersion, config | 启动配置和协商版本；启用二进制时包含 Host 创建的 artifactStaging.inboundDirectory / outboundDirectory |
| Plugin → Host | plugin.ready | pluginId, pluginVersion, ipcVersion, extensions | 确认身份、协议和该进程实际实现的 Extension |
| Plugin → Host | ingress.event | eventId, ingressId, eventType, externalRequestId, responseChannelId, source, payload, artifacts | 发布一个规范化 Event |
| Host → Plugin | ingress.ack | eventId, disposition, runId?, responseObligationId?, artifactRefs?, error? | 接收、重复关联、冲突或拒绝 |
| Host → Plugin | tools.invoke | invocationId, callableId, arguments, invocationContext, artifactRefs, deadlineMs? | 调用一个已经过 Runtime Callable Scope 检查的 Tool |
| Plugin → Host | tools.result | invocationId, result? 或 error | 返回 Interface Package 定义的结果或错误 |
| Host → Plugin | delivery.dispatch | deliveryId, runId, responseObligationId, eventType, statusCode, headers, body, artifacts | 交付 Host 已记录的响应 |
| Plugin → Host | delivery.result | deliveryId, disposition, statusCode?, error? | 报告 delivered、failed 或 unknown |
| Host → Plugin | host.cancel | targetMessageId 或 targetOperationId, reason | 请求取消 |
| Plugin → Host | plugin.cancelled | targetOperationId, disposition | 报告 cancelled、too_late 或 unsupported |
| Host → Plugin | host.shutdown | gracePeriodMs | 请求进程停止 |
| Plugin → Host | plugin.stopped | inFlightCount | 确认停止并报告剩余在途工作 |

类型约束：

- host.initialize 传入精确 Plugin 身份和唯一支持的 IPC 版本；Plugin 不得自行选择其他版本。
- plugin.ready 只能报告 Manifest 已声明的 Extension；不一致则握手失败。
- ingress.ack disposition 为 accepted、duplicate_attached、conflict 或 rejected。accepted / duplicate_attached 包含 Host 分配的 runId 和 responseObligationId；conflict / rejected 包含 error。
- tools.invoke 使用 Interface Package 中精确 callableId 和参数结构。invocationContext 只包含对应 Tool binding 已声明的 Host invocation 字段。
- tools.result 的结构由 Interface Package 定义。Owner Receipt / Commit Proof / outcome 由 Runtime 按 Owner 契约解释，Plugin 传输成功不等于业务 COMMITTED。
- delivery.dispatch 由 Host responseObligationId 定位，只携带该义务允许的响应和 Artifact。
- delivery.result disposition 为 delivered、failed 或 unknown；不确定交付必须保持 unknown，不改变 Owner 业务 outcome。
- 取消是尽力而为；too_late / unsupported 不代表外部 mutation 已回滚。
- 畸形帧、非法 JSON、未知消息、关联不匹配或 Payload 无效时，受影响操作失败关闭。

## 9. 统一错误对象

~~~json
{
  "code": "PLUGIN_OPERATION_FAILED",
  "message": "The external operation failed.",
  "retryable": false,
  "details": {}
}
~~~

code 和 message 必需；retryable 是传输/重试提示，不证明业务 mutation 未提交；details 可选，不得包含秘密或原始二进制。

## 10. Plugin 生命周期

~~~text
CONFIGURED → STARTING → READY
                     ↘ NOT_READY
READY → STOPPING → STOPPED
~~~

一个 Plugin 进程可并发处理请求，但必须串行写 stdout，并按 correlation 关联回复。Plugin 失败只影响其自身 Extension。Demo 不要求自动热更新或生产级 Supervisor。

## 11. Provider v2 过渡适配

ca-client-tools 当前使用 provider/v2 进程协议。过渡期可在唯一 Plugin Manager 内实现 tools Extension Driver，把 Runtime 调用转换为 provider/v2，再将结果映射回来。

该 Driver 是迁移适配，不是独立 Provider Manager，不得形成第二套 Tool Registry、Runtime 或授权路径。Codec Operation 若发布，也通过同一个 tools Extension 提供。

## 12. Demo 禁止项

不增加第二套 IPC、兼容别名、Provider Manager、Tool Registry、Event Registry、业务 Contract Package、Plugin 自有 Artifact 数据库、Base64 二进制传输、额外 SHA-256、签名、Trust Registry、旧版兼容、Marketplace、自动下载、热更新或生产级 DFX。

保留基本 Manifest/Schema/版本/引用校验、路径边界、明确错误、显式进程配置、最小关联和可运行 Acceptance。
