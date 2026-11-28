# Context 与 Artifact 管理设计说明书

> 文档类型：机制设计说明书  
> 文档版本：0.4.14\
> 状态：ca-host.artifact-store/v1 保留为历史冻结契约（要求 SHA-256，Provider v1.2.0 已消费）；新 1.6.0 Demo 目标为 ca-host.artifact-store/v2（无 hash，Next 中央设计已固定；独立复评和实现尚未完成）；Next Python Host / ArtifactStore / v2 Channel NOT_IMPLEMENTED。
> 功能归属：F05 — Context 与 Artifact 管理  
> 关联 SR：SR-009；交叉 SR：SR-007、SR-010、SR-011、SR-015、SR-017、SR-030、SR-032\
> 关联 IR：IR-004、IR-005、IR-006、IR-008  
> 修订日期：2026-11-28  
> 适用范围：Event Context、Run Context、Observation/Evidence 投影、Host-owned ArtifactStore、SBI multipart、Plugin Handoff、Codec 输入输出

> 全局评审范围：继承根目录 Agent.md 的 review_scope。
> 本文局部非目标：详见 §13。

## 1. 目标与基本边界

F05 定义 Host 如何组装当前执行所需 Context，以及如何保留、引用、授权和交付原始二进制 Artifact。它不是第二个 Runtime、Plugin Manager、Context Service、Artifact Service 或业务事实数据库。

必须区分：

- **Context**：某个 Run/Action 可使用的结构化输入、事实、只读观察、Skill 指导和关联身份的受控视图。
- **Artifact**：由 Host 管理的原始字节或文件材料，通过 opaque artifactRef 引用。
- **Observation**：通过 READ 能力从权威来源取得的事实数据。
- **Evidence**：按 Owner/Tool Interface 契约定义、可被 Runtime 用来解释结果的证明材料；不是任意 Context 字段。
- **Run / Invocation / Response Obligation**：分别表示业务执行、单次工具调用和对外响应义务，不得用 Artifact ID 或 HTTP stream ID 代替。

所有权：

| 内容 | 唯一所有者 |
|---|---|
| 外部 SBI 解析、multipart、Content-ID、N1/N2 原始字节提取/编码 | Event/Delivery Plugin |
| Context 组装、模型可见投影、ArtifactStore、opaque artifactRef、staging 目录 | Host |
| 当前 Action 可读写的 Context/Artifact 范围 | Runtime |
| Tool 的公开输入输出与引用语义 | 当前 Callable 的 Provider Interface 或 Owner Contract；进程内交接按 backend binding 的 artifactSlots |
| Observation 的来源事实与 Evidence 的权威语义 | 对应 READ Tool / Owner Contract |
| 业务事实和 mutation 最终状态 | Owner |

## 2. Context 组装模型

Host 按 Run 和当前 Action 组装 Context，不建设全局可变 Context Registry。概念上由以下部分组成：

| 部分 | 来源 | 用途 |
|---|---|---|
| Event Input | 已通过 Event Schema 校验的 normalized Event | 当前业务请求和协议身份 |
| Skill Context | 已绑定 Skill 的 SKILL.md；schemas/、scripts/manifest.yaml、scripts/、references/、assets/ 按需读取 | 模型指导、Schema 理解、Script 源码读取和当前 Skill 范围 |
| Run Context | Host 的 Run 记录、Skill identity、Artifact identity、当前执行位置和 response obligation | 续跑、关联和失败恢复 |
| Read Facts / Observations | 当前 Run 允许的 READ Tool / Owner Observation | 当前业务事实 |
| Evidence References | Owner/Tool Contract 声明的 Receipt、Commit Proof 或其他 typed Evidence | Runtime 结果解释 |
| Artifact References | Host 签发并绑定到 Event/Run/Invocation 的 opaque refs | 向允许的 Tool 传递原始材料 |

组装规则：

1. 新 Event 通过 Schema 校验后，Host 先创建 Event identity 和 response obligation，再由 F02 选择 Skill。
2. Run 固定 Skill identity、发布 Artifact identity、Catalog generation 和原始 Event；Catalog 更新不得改变在途 Run。
3. 每次 Action 只获得其所需的 Context 和已授权 Artifact refs；不得把整个 Host store 暴露给模型或 Plugin。
4. Continuation 恢复原 Run、原 Skill、原代际及该 Run 已有响应义务。新到达的 HTTP 回调若需要回包，单独记录其 responseChannelId 与响应义务；两者分别结清，不重新选择 Skill。
5. Context 只读投影可以按需重建；不要求引入独立 Context DB 或全局快照服务。
6. 原始二进制只通过 Artifact ref / 独立交接通道使用，不转换成模型可见文本。
7. Skill Package 的 schemas/、scripts/、references/ 和 assets/ 是独立的只读 Package Resource，不进入 ArtifactStore；Host 按当前 Run 固定的 Package snapshot 提供精确相对路径读取，不暴露宿主文件系统路径。
8. LLM 通过 F05 §2.1 的 host.skill-resource.read 按需读取当前 Package snapshot 的 schemas/、scripts/manifest.yaml、scripts/ 源码与 references；读取 Script 不等于执行。所有已登记 Script（transform / predicate）均可通过 F04 定义的 host.skill-script.execute 调用；LLM 与 Assurance 共用同一 Script Runner，不设置逐脚本标记或额外 Host 开关。Predicate Script 的 LLM 调用不产生 Evidence 或 Assurance 阶段 Outcome。

### 2.1 Host Skill Resource Read

Host 提供只读 system Capability `host.skill-resource.read`，通过统一 Runtime Action Boundary / Host Tools Extension 供当前 Run 的 LLM 按需读取当前 Skill Package snapshot 中的文本资源。它不是业务 Capability，不进入 `contract.capabilities`，不改变业务 Capability Scope。

**请求：**

~~~yaml
path: schemas/qos-request.schema.yaml
~~~

请求只有一个字段 `path`，必须是当前 Skill Package 根目录相对路径。Host 从当前 Run 绑定 Skill ID 和不可变 Package snapshot；模型不得提交 `skillId`、Package generation、宿主绝对路径、URL 或其他 Skill 身份。

允许读取的根路径为 `SKILL.md`、当前包存在时的 `assurance/`、`schemas/`、`scripts/`、`references/` 和 `assets/`。路径必须使用正斜杠、规范化相对路径；拒绝绝对路径、空路径段、`.` / `..`、反斜杠、符号链接逃逸、Package 清单之外的文件和跨 Skill 访问。

仅支持 UTF-8 文本资源。单次读取上限为 1 MiB；超限完整拒绝，不截断、不返回部分内容。二进制资源不通过此文本 Action 返回；如需交付原始 bytes，必须使用已有 Host Artifact / Handoff 契约。

**响应：**

~~~yaml
path: schemas/qos-request.schema.yaml
mediaType: application/yaml
content: "<原始 UTF-8 文本内容>"
byteLength: 512
~~~

响应字段为精确相对路径、Host 推导的媒体类型、原始文本内容和 UTF-8 字节数。Host 不格式化、不改写或重序列化资源。

**拒绝诊断：**

| Code | 含义 | 处理 |
|---|---|---|
| RESOURCE_PATH_INVALID | 路径不合法、越界或逃逸 Package | 拒绝读取 |
| RESOURCE_NOT_FOUND | 当前 snapshot 中不存在该文件 | 拒绝读取 |
| RESOURCE_TOO_LARGE | 文件超过 1 MiB | 完整拒绝，不截断 |
| RESOURCE_MEDIA_TYPE_UNSUPPORTED | 文件不是受支持 UTF-8 文本 | 拒绝文本读取 |
| RESOURCE_SNAPSHOT_UNAVAILABLE | 当前 Run 的 Package snapshot 不可用或不匹配 | 拒绝读取，不回退到其他版本 |

Resource Read 不暴露宿主文件系统路径，不读取其他 Skill / 其他 Run 的资源，不产生写入或业务副作用。每次读取消耗一个 Host-owned per-Run Runtime Action Budget 单位；该预算与 `Contract.limits.maxActions` 分离，后者只统计业务 Capability Actions。Host Script Execution 使用同一 Runtime Action Budget，详见 F04 §10.3。

## 3. Fact、Observation 与 Evidence

Context Fact 是带来源的结构化事实，不因进入 Context 就自动成为权威证明。其概念信息至少包括：

- fact key / semantic identity；
- value（包括明确的 UNKNOWN）；
- authority / producer；
- source reference；
- freshness 或 observed revision；
- grounded subject / scope；
- visibility（MODEL_VISIBLE 或 HOST_ONLY）。

这些字段说明事实从何而来、适用对象和可见范围；它们本身不授予 mutation 权限或提交权威。

### 3.1 Observation

- Observation 必须由唯一映射的 READ Capability / Callable 取得；Skill 只引用 Capability。
- READ 返回必须符合该 Callable 所属 Provider Interface 或 Owner Contract 的输出 Schema，并关联原 Run/Invocation。
- Observation 的来源、对象范围和新鲜度必须保留；缺失、来源不匹配或 Schema 无效时不得构造成功事实。
- UNKNOWN 必须保持 UNKNOWN，不得因模型推断、缓存默认值或“没有查到”而转成 PASS/true。
- Observation 不得触发 Owner mutation。

### 3.2 Evidence

- Evidence 的类型、生产者、来源和消费位置由 Owner Contract / Tool Interface Package 定义。
- Runtime 只能按契约验证 Evidence；模型文本、普通 Observation 或 Artifact 存在性不能替代 Commit Proof。
- COMMITTED 必须有与原始 Invocation 精确绑定的 Owner Receipt / Commit Proof。
- NOT_COMMITTED 必须有 Owner 对未发生副作用的证明。
- UNKNOWN 保持 UNKNOWN，必要时对同一 originalInvocationId 执行 exact-original Reconcile；不得重新发起原 mutation。

## 4. Context 可见性与模型投影

Host 是模型上下文的唯一组装者。模型只接收当前任务所需且被明确允许的内容：

- 当前 Skill 的 SKILL.md；
- 当前 Skill Package snapshot 中按需读取的 schemas/、scripts/manifest.yaml、scripts/、references/ 与 assets/；
- 明确声明且由用户/Host 策略允许的 reference；
- Event Schema 允许的业务输入字段；
- 明确标记 MODEL_VISIBLE 的只读事实；
- 当前 Run 的最小执行摘要；
- 当前 Skill 已授权的 Capability 描述和参数 Schema；不得把 Callable ID 或 backendOperationId 投影给模型。

以下内容默认 HOST_ONLY：

- 原始 N1/N2 bytes；
- ArtifactStore 内部路径和 stagingPath；
- Provider 私有 backendOperationId、服务 URL、凭据、privateArguments；
- Owner 私有数据、未授权 Observation 和完整 Receipt/Commit Proof 原文；
- 不属于当前 Run/Invocation 的其他 Artifact。

如需向模型展示某个 Artifact 的存在，只能提供经授权的安全元数据（例如 slot / mediaType / byteLength），不能暴露文件路径或原始 bytes。模型不能自行构造 artifactRef、Evidence 或 Owner Outcome。

Skill 的 schemas/、scripts/、references/ 和 assets/ 默认按需读取，不在 Skill 激活时预加载全部文件；所有读取必须相对当前 Run 固定的 Package snapshot，并限制在其文件清单内。Script 源码可见不代表可执行；执行只接受 Registry 中的 Script ID，不接受模型提供的文件路径或 Python 代码。读取失败、资源缺失或 Package snapshot 不匹配时返回明确诊断，不回退到未声明路径。

## 5. ArtifactStore 与引用模型

Host 拥有唯一 ArtifactStore。其逻辑职责：

- 接收并保留入站原始 bytes；
- 为每份材料分配 Host-owned opaque artifactRef；
- 记录 slot、mediaType、byteLength 和 Event/Run/Invocation/Response Obligation 关联；
- 在 Runtime 授权后向对应 Tool 提供材料；
- 接收 Tool 生成的新 Artifact 并绑定当前 Invocation；
- 为当前 response obligation 暂存出站文件；
- 在相关 Run/Delivery 生命周期结束后清理暂存材料。

约束：

1. artifactRef 是不透明引用，不编码文件路径、外部 URI、Content-ID 或内容摘要。
2. Host 不把 artifactRef 作为业务事实；它只表示 Host 能定位并授权访问的材料。
3. Artifact 元数据与原始 bytes 分离。任何调用者不得通过猜测 ref 或路径读取其他 Run 的文件。
4. artifactRef 不采用内容寻址或摘要身份；不引入去重、独立数据库或远程 Artifact Service。新 1.6.0 Demo Host→Tool channel v2 不计算、不传输、不校验 SHA-256、checksum 或 digest；只校验 opaque reference、Invocation/direction/slot、mediaType、byteLength 与配额。v1 的逐 Artifact SHA-256 是历史外部契约要求，不属于新目标，不得复用或兼容。
5. 本地文件存储可以作为 Host 内部实现；对 Plugin/Tool 暴露的仍是受控引用，不暴露宿主文件系统路径。
6. ArtifactStore 不是 Evidence Store；原始协议字节不能自动被解释为业务已提交。

建议的逻辑关联字段（不是新增独立 wire schema）：

| 字段 | 含义 |
|---|---|
| artifactRef | Host 生成的 opaque reference |
| slot | 由 Event / Tool Interface 声明的材料槽位 |
| mediaType | 原始媒体类型 |
| byteLength | 实际字节长度 |
| eventId | 来源 Event |
| runId | 当前业务 Run |
| invocationId | 可选，产生或消费该材料的 Tool Invocation |
| responseObligationId | 可选，允许该材料用于哪个外部响应 |

## 6. 两种二进制交接边界

必须区分两条路径，不能合并成新的通用二进制服务。

### 6.1 Event / Delivery Plugin ↔ Host

使用 Host 创建的本地 inbound/outbound staging directory。Plugin 通过相对 stagingPath 交付文件描述符，Host 校验并导入 ArtifactStore。该路径由 Plugin Package/IPC v1alpha1 及本设计定义。

### 6.2 Host / Runtime ↔ Tool Plugin

Tool 只接收当前 Invocation 已授权的 artifactRef 和声明的 slot，不接收任意本地路径。二进制通过独立 Host Artifact Store Channel 交接，不进入 NDJSON、不使用 Base64。

**历史协议基线（v1，已冻结但不用于新 1.6.0）：** ca-host.artifact-store/v1 是 Provider v1.2.0 使用的旧 Host→Tool 二进制交接契约，完整原文见 [TARGET01 Go Host Artifact Store 契约原文](../目标参考/TARGET01-Go%20Host%20Artifact%20Store契约原文.md)。该契约冻结版本为 ca-agent commit 2c0b07f2eaff3bc1020bfc6775ef9bf09e3052ae；当前 Go Host 实现基线为 447d0cce7e42c7c1184b11fb2563792eead68d51。其 SHA-256 传输校验与 Demo 限制冲突，故仅作历史审计证据；不得作为 Next 1.6.0 Host Channel 或 Provider 2.0.0 的实现基线。

**引用与绑定：** Provider 只接受闭合 JSON 对象 `{"artifactRef":"art_<43 base64url characters>"}`。该 token 由 Host 使用 CSPRNG 生成（32 random bytes），并绑定当前 `invocationId`、`direction`（input/output）和声明的 `slot`；对象不得附带 path、URL、mediaType、size、digest 或其他字段。Provider 不解析、不生成、不持久化该 token，也不得把它当作授权凭据；Runtime 仍须先完成 Skill/Capability/Invocation 授权。

**Channel bootstrap：** Host 为每个 Provider 进程创建 loopback HTTP/1.1 listener（仅 `127.0.0.1`、ephemeral port），在 Provider `initialize` 中传入可选的闭合 `artifactChannel` 对象：`baseUrl`、`processToken`、`requestTimeoutMs`、`maxArtifactBytes`、`maxAggregateBytes`、`maxAttachments`。不得把 channel URL/token 放入进程 argv、环境变量或日志。`baseUrl` 只能是 `http://127.0.0.1:<port>`。

**传输方向：** Input 由 Provider 对 `{baseUrl}/v1/artifacts/{artifactRef}` 发起 GET，并携带 Bearer process token、`X-CA-Invocation`、`X-CA-Slot`；Host 返回声明的 media type、精确 Content-Length、`X-CA-Artifact-Sha256` 和原始 bytes。Output 由 Provider 对 `{baseUrl}/v1/artifacts` 发起 POST，携带相同的 invocation/slot 绑定、media type、Content-Length 和可选 `X-CA-Artifact-Sha256`；Host 自行计算并验证摘要，返回 staged reference。

**发布与清理：** Provider 输出引用在 invoke result 通过 Host 的 slot/reference/result validation 之前只能处于 staging；只有整个结果有效时，Host 才一次性发布全部必需输出。任何超时、取消、Provider 退出、无效结果、重复 slot 或传输错误都必须丢弃本次 Invocation 的 staged outputs；不得部分发布。引用/字节按契约执行 per-artifact 1 MiB、per-invocation 4 MiB、最多 8 attachments、channel request timeout 3 s、发布后 10 min expiry（Host 可采用更严格的部署上限）。

**摘要语义：** SHA-256 是 v1 wire contract 对精确字节的传输完整性校验：Host 在接收时计算、在 GET 时返回，Provider 验证收到的 bytes；它不进入 artifactRef，不用于公开内容寻址或去重。Next 只实现这一既有协议要求，不增加额外 package hash、签名、Trust Registry 或第二套完整性机制。

**v1 历史未配置行为：** 缺少 artifactChannel 时 Provider catalog 将 artifact-bearing binding 标记 NOT_CONFIGURED；该行为继续适用于历史 v1 Provider。新 1.6.0 v2 的配置与拒绝行为按下方 v2 契约执行。

**1.6.0 Demo 目标协议（v2，无摘要；中央设计，尚未实现）：** 新 Provider 2.0.0 / Runtime Bindings v2 只消费 ca-host.artifact-store/v2。v1 保持冻结历史，不提供 v1↔v2 Adapter、双轨、fallback，也不得通过忽略 SHA-256 header 伪装兼容。

- **Bootstrap：** Host 为每个 Provider 进程创建 loopback HTTP/1.1 listener（仅 127.0.0.1、ephemeral port），在 initialize 中提供闭合 artifactChannel：apiVersion=ca-host.artifact-store/v2、baseUrl、本进程短期 processToken、requestTimeoutMs、maxArtifactBytes、maxAggregateBytes、maxAttachments。无 TLS/OAuth；processToken 仅为本机进程通道令牌，不引入 OAuth 流程。URL/token 不进入 argv、环境变量或日志。
- **Input：** Provider 对 /v2/artifacts/{artifactRef} 发起 GET，携带 process token、X-CA-Invocation、X-CA-Slot；Host 返回 Content-Type、精确 Content-Length 与原始 bytes。不得返回 X-CA-Artifact-Sha256 或其他摘要字段。
- **Output：** Provider 对 /v2/artifacts 发起 POST，携带 Invocation、slot、mediaType、Content-Length 和原始 bytes；Host 校验当前 Invocation / direction / slot 绑定、媒体类型、实际长度与配额，返回随机 opaque staged reference。不得发送、计算或校验 SHA-256、checksum 或 digest。
- **原子性：** Provider 输出只在整个 invoke result、所有 slot/reference 与 Schema 校验通过后一次性发布；超时、取消、进程退出、无效结果、重复 slot 或传输错误均丢弃本次 staged outputs，不得部分发布。保留既定大小/数量配额、超时、取消、过期清理。
- **拒绝：** 缺 channel、错误 apiVersion、未知/越权 reference、Invocation/direction/slot 不匹配、Content-Length 与实际字节数不符、媒体类型不符或超配额，均在远端 SBI I/O 前或材料交付前 fail-closed。v1 Provider / fixtures 不构成 v2 互操作证据；v2 由 SR-010 与 SR-026 分别验收 Host 和 Provider 两端。

## 7. 本地 staging 协议

当 Plugin Manifest 声明二进制 Event / Delivery slot 时，Host 在 host.initialize 中提供由 Host 创建的目录：

~~~json
{
  "artifactStaging": {
    "inboundDirectory": "/host-managed/plugin/openamsm/inbound",
    "outboundDirectory": "/host-managed/plugin/openamsm/outbound"
  }
}
~~~

路径是当前进程配置，不是可移植包内值。Plugin 只能在 inboundDirectory 写入；Host 只能在 outboundDirectory 写入；Plugin 不得选择目录根。

每个 Artifact 描述符使用相对 stagingPath：

~~~json
{
  "slot": "n1.request",
  "mediaType": "application/vnd.3gpp.5gnas",
  "contentId": "n1SmMsg",
  "stagingPath": "event-123/n1.bin",
  "byteLength": 48
}
~~~

必需字段：slot、mediaType、stagingPath、byteLength。源协议提供 multipart Content-ID 时必须附带 contentId，否则省略。路径必须留在对应 staging 根目录内。绝对路径、路径穿越、符号链接逃逸、文件缺失、空文件（若该 slot 不允许空值）以及声明长度与真实长度不一致均必须拒绝。

Host 必须读取真实文件长度；Plugin→Host 本地 staging 边界不计算额外摘要或 SHA-256。后续 Host→Tool 独立 channel 按 ca-host.artifact-store/v2 校验引用绑定、媒体类型、长度和配额，不计算或校验摘要。具体最大文件尺寸由 Host 部署配置约束，不在此重复建立第二份全局数值常量。

## 8. 入站流程

1. Host 创建并拥有 inbound/outbound staging 目录，通过 host.initialize 交给 Plugin。
2. Plugin 解析 SBI Body，将每个二进制 part 按相对路径写入 inboundDirectory。
3. Plugin 发送 ingress.event，包含规范化 JSON payload 和 Artifact 描述符；不得发送原始 bytes 或 Base64。
4. Host 校验 Event Schema、Manifest slot、media type、路径边界和真实 byteLength。
5. Host 将 bytes 导入 ArtifactStore，生成 opaque artifactRef，并绑定 Event identity。
6. Host 完成导入后才返回 `ingress.ack`；payload 仅 `eventId` / `disposition` / 可选安全 `error`，不得夹带 `runId`、`skillId`、`artifactRef`、`responseObligationId`、`deliveryId`、`responseChannelId`（含嵌套 details）；IPC 帧顶层请求应答 `correlationId` 仍可匹配原 messageId，但不是 Event payload 身份。Host artifactRef 留在 Host 内部，Plugin 不创建或选择 artifactRef。
7. 任一必需 part 缺失或校验失败时拒绝 Event，不创建业务 Run。
8. Event 校验成功后，Host 创建/关联 Run，并按 Runtime 授权把所需 refs 交给对应 Tool；不得自动把全部入站 refs 交给模型。

## 9. 出站流程

1. Runtime 通过已授权 Action / Tool 获得输出 Artifact。
2. Host 验证当前 responseObligation 是否允许该 slot，并将精确 bytes 写入 outboundDirectory。
3. Host 发送 `delivery.dispatch` 前，先根据 Host 权威 Response 表原子核对 `deliveryId`（本次发放）、`responseObligationId`（本次 HTTP 响应义务）、`responseChannelId`（本次 live HTTP/2 waiter）与原 Event/Run/代际授权一致；有效后发送这三个身份、eventType、slot、mediaType、Content-ID（如适用）、相对 stagingPath 和 byteLength。Host artifactRef 保持 Host 内部，不交给 Delivery Plugin。Plugin 只验证自己能看到的 channel/eventType、deliveryId 回显和 opaque obligation **非空/不泄漏**，不得以本地缓存推测 Host 三元授权。
4. Plugin 只读取本次交付声明的文件，按外部协议构造 SBI multipart / Content-ID 响应。
5. Plugin 返回 delivery.result；Host 记录 delivered / failed / unknown 并清理出站 staging 文件。
6. Delivery UNKNOWN 不改变 Owner 业务 outcome，也不得触发 mutation 重放。

Plugin 不得请求任意 ArtifactStore 读取；只能访问本次 Delivery 已暂存的文件。

## 10. OpenAMSM slot 与 Codec

Media Type：

- NAS / 5GSM：application/vnd.3gpp.5gnas
- NGAP / N2：application/vnd.3gpp.ngap

初始 slot 词汇：

| Slot | 方向 | 含义 |
|---|---|---|
| n1.request | 入站 | SBI 请求中的原始 N1 NAS 消息 |
| n2.request | 入站 | SBI Create/Update 请求中实际存在且被 JSON 引用的原始 N2 SM 信息 |
| n2Ext1.request | 入站 | SBI Create/Update 的 JSON `n2SmInfoExt1.contentId` 所引用的原始 N2 Ext1 字节，与 `n2.request` 独立 |
| n1.confirmation | 入站 | 后续 ingress 中的 N1 continuation / confirmation，例如 PDU Session Release Complete（0xD4） |
| n2.confirmation | 入站 | 后续 ingress 中的 N2 continuation / confirmation，例如 PDU Session Resource Release Response |
| n1.response | 出站 | Owner / Host 为当前响应义务生成的 N1 NAS 响应 |
| n2.response | 出站 | Owner / Host 为当前响应义务生成的 N2 NGAP 响应 |

具体 Event 决定 slot 必需或可选。Create/Update 的 `n2.request` / `n2Ext1.request` 均按正式 OAS3 request JSON 的引用选用；Ext1 严格按 F06 §4.1 的 Content-ID、media type 和 N2 类型校验，不能合并到 `n2.request` 或静默丢弃。Continuation 尚未冻结 `n2Ext1.confirmation`：收到 Ext1 时当前 profile 必须显式 fail-closed，运行子项记 NOT_RUN，不得猜测 slot。Create 的 N1 是否必需须由 OAS3 或正式发布的 Demo ingress profile 明确，不能仅凭 Plugin manifest 擅自将可选升格为必需。

Codec 规则：

- 不需要协议字段的 Skill 可以直接使用授权 artifactRef，不调用 Codec。
- 需要字段时，通过统一 Runtime Action Boundary 调用 ca-client-tools 导出的普通 Codec Callable。
- Codec 只有在 Tool Interface Package 正式发布 Callable、输入输出 Schema 和支持消息范围后，才能经 Tools Extension 使用。
- Decode 返回结构化投影或新 Artifact，不修改原始 Artifact。
- Encode 产生的新 bytes 绑定当前 Invocation / response obligation，由 Host 暂存，再交给 Event/Delivery Plugin 编码。
- ca-client-tools PR #39 当前 OPEN；Phase B facade/worker 不等于 Phase C consumer integration。未发布 Callable 的纯 Go Codec library 不是 Agent 可调用 Tool。
- 不宣称完整 NGAP 支持；只声明实际发布、测试和资格化的消息子集。

共享 `UpdateSmContext` 在 Skill 选择前只使用 T0 最小 5GSM discriminator：`0xC9` Modify、`0xD1` UE-requested Release、`0xD4` Release Complete continuation；它不是完整业务解码。生产 T0 分类由 ca-client-tools#44 正式发布的窄 classifier API 提供（F06 §4.1/§14），Plugin 仅调用并映射 Event，不得自建 NAS parser 或以完整 DecodeNAS 代替。API 未发布前生产绑定 BLOCKED_EXTERNAL_INPUT；test double 仅证明 Event mapping，不证明生产分类器或系统 E2E。原始 bytes 必须保留。

## 11. Run、重试与 Artifact 生命周期

Host 必须维护以下关联：

- Event：eventId、ingressId、eventType、externalRequestId（若协议提供）；
- Run：runId、原始 Event、Skill identity、Artifact identity、Catalog generation；
- Invocation：invocationId、Tool Callable、授权的 artifactRefs；
- Response：Host 权威的 `responseObligationId`、当前 live `responseChannelId`、本次 `deliveryId` 三元映射，附本次 Event/Run/请求 generation 授权及终态；Plugin 不维护第二套可查询的三元表。
- Artifact：artifactRef、slot、mediaType、byteLength 和上述关联身份。

规则：

- HTTP/2 stream ID 仅是瞬时传输身份，不是 Event/Run 身份。
- 相同稳定 externalRequestId 的重试只有在身份与原始内容（含真实 bytes）精确相等时才可关联原 Run；相同 ID 不同内容必须拒绝。
- 不使用内容摘要替代字节相等证明。
- Continuation 必须关联同一 Run、SUPI、PSI、Session generation 和原 response obligation；旧消息不得唤醒新 Run。
- Artifact 在导入后归 Host 所有；Runtime 授权其被哪个 Invocation 读取/生成；Delivery 只读取本次 response obligation 的输出。
- **Host 必须在 dispatch 前执行权威三元绑定负例**：采用一个格式正确、非空但属于另一 Event/Run/代际或另一 live channel 的 `responseObligationId`，与当前合法 `deliveryId`/`responseChannelId` 混合；交换两条并发 HTTP/2 waiter 的 obligation；使用已结清/过期 obligation 或重复 `deliveryId`。全部必须在 Host 侧 fail-closed，不发送成功 dispatch、不完成错误 waiter、不得把旧 Run/旧 generation 标成 delivered，也不得改变 Owner mutation outcome。只有完整匹配并未结清的三元身份允许派发。测试归 SR-011 AC-011-05；当前 Next Host 联测 **NOT_RUN**，绝不能用 ca-openamsm-plugin 的非空/不泄漏校验充当 Host 权威绑定 PASS。
- 成功导入后 Host 清理入站 staging 文件；Delivery result 或 Plugin 关闭后清理出站 staging 文件。
- Host 可在关闭/重启时清理自己 staging 根下的残留文件；不增加 Plugin 数据库或恢复协议。
- Artifact 生命周期至少覆盖正在执行的 Run/Invocation 和未完成 response obligation；终态清理后，引用不可继续解析。

## 12. 失败处理

| 失败 | 行为 |
|---|---|
| Event Schema / slot 无效 | 拒绝 Event，不创建 Run |
| stagingPath 越界、符号链接逃逸、文件缺失或 byteLength 不匹配 | 拒绝导入并清理本次临时文件 |
| Artifact ref 不属于当前 Run / Invocation | Runtime 拒绝 Action |
| Next Host 未配置 artifactChannel | artifact-bearing binding 标记 NOT_CONFIGURED，远端 I/O 前失败；不尝试备用 URL、文件路径或 Provider |
| Tool 返回未知 Artifact ref | Runtime 拒绝结果，不生成成功 Observation |
| 原始 bytes 不支持当前 Codec | 返回明确 unsupported，不改变原 Artifact |
| Owner/Provider mutation 结果 UNKNOWN | 保持 UNKNOWN，按 F04 exact-original Reconcile |
| Delivery failed / unknown | 记录响应义务状态，不改变 Owner outcome、不重放 mutation |
| Host 重启后找不到未终结 Run 所需 Artifact | 该 Run 标记不可恢复并给出诊断；不猜测或重新构造原始 bytes |

## 13. Demo 范围与非目标

Demo 必须具备：本地 Host-owned ArtifactStore、精确 slot、相对路径校验、byteLength 校验、Run/Invocation/response obligation 关联、按需 Codec 和明确失败行为。

不要求生产级 HA/DR、远程对象存储、分布式 Artifact Service、内容寻址、去重、额外 package hash/签名、Artifact Marketplace、通用沙箱或跨地域生命周期管理。Host→Tool 新 1.6.0 channel v2 不实现任何 hash / digest 校验；v1 仅保留历史实现记录，不作为新目标。允许 Host 内部使用本地文件持久化；不要求所有 Artifact 只存内存。

不把 ca-agent-demo 的 PlanningContext / ContextRequirement / ContextOffer 全套规划机制复制进 Next。Next 仅采用必要的事实来源、只读 Observation、显式可见性和 Run 绑定；不建设独立 Planning Runtime。

## 14. 当前实现审计

| 对象 | 当前状态 | 已核对证据与边界 |
|---|---|---|
| Next Context Assembly | NOT_IMPLEMENTED | Next 当前仍是设计仓；无已验收 Python Host |
| Next Host ArtifactStore / Plugin staging | NOT_IMPLEMENTED | F05 为目标设计，未有 Next 代码和 E2E |
| ca-agent-demo Context Fact / Resolver / Projection | IMPLEMENTED（参考仓 main） | main 57e277ff；agent/context/base.py、loader.py、observation_resolver.py、projection.py、requirements.py；测试 test_context_loader.py、test_context_observation_resolver.py |
| ca-agent-demo Skill Context Loader | IMPLEMENTED（参考仓 main） | agent/host/skill_context.py；测试 test_skill_context.py；精确 Skill identity 与按需 reference |
| ca-agent-demo Host ArtifactStore | IMPLEMENTED（参考仓 main） | resident/artifact_store.py；测试 test_host_artifact_store.py。其 `artifact:sha256` 内容寻址不移植；ca-host.artifact-store/v1 的 SHA-256 传输校验仅作历史记录；Next 1.6.0 v2 使用随机 opaque token、slot / direction / byteLength 校验，不采用内容寻址或摘要 |
| ca-runtime Skill Context Identity | 参考设计 | REF02 Skill Context 原文；是 Go RuntimeHost 参考，不是 Next Python 契约 |
| ca-agent Go Host Artifact Store | IMPLEMENTED / VERIFIED（外部参考） | main 447d0cc；ca-host.artifact-store/v1；P1 acceptance 43/43（read-only 11/11）；real-NF multipart NOT_VERIFIED；仅证明 Go Host 参考实现 |
| ca-host.artifact-store/v1 契约 | FROZEN / ACCEPTED | TARGET01 原文；contract pin 2c0b07f；Provider v1.2.0 固定 fixtures；artifactRef 为随机 opaque token，SHA-256 仅用于逐 Artifact 传输校验 |
| ca-client-tools Provider Artifact Channel | IMPLEMENTED（历史 Provider v1.2.0） | main 7bcb261；`contracts/host-artifact-store/v1/`、`internal/artifactchannel/`、`internal/providerapp/artifacts.go`；证明冻结 Host Artifact Channel 的传输实现，不证明 1.6.0 Interface Package / Capability exports |
| Next Host→Tool Artifact Channel v2 | NOT_IMPLEMENTED | Next Python Host 尚无 server/adapter；SR-010 实施；通过 v2 no-hash fixtures 前保持 NOT_CONFIGURED |
| ca-client-tools Codec Phase B | OPEN / NOT_MERGED | PR #39 OPEN（非 Draft）；Phase B 已达 FINAL_PASS / PHASE_C_READY，但未合并 |
| env-5gc-sim Mock AMF Codec C1 | OPEN / NOT_MERGED | PR #86 OPEN；只将 Mock AMF 测试对端迁移到 `ca-client-tools/protocol/codec`，不提供 Agent Tool/Provider Callable，也不实现 Next Host/Runtime 集成 |
| Next Agent Tool / Provider Codec Consumer | NOT_STARTED（1.6.0 目标设计见 SR-026） | PR #39 尚未合并；PR #86 不属于 Agent Tool/Provider 集成；新目标为一个 Skill-facing Codec Capability ↔ 一个公开 Callable，内部只处理已声明 NAS 消息子集 |
| Next Artifact / OpenAMSM E2E | NOT_RUN | 不得以外部仓的测试 PASS 代替 |

### 14.1 复用原则

可选择性复用：事实来源与 freshness、只读 Observation、模型可见性显式 allowlist、Skill reference 精确路径、Artifact ref 由 Host 管理的概念。

不直接复用：artifact:sha256 内容寻址、ca-agent-demo 的完整 PlanningContext / ContextOffer / Candidate Strategy 模型、5GC 专用 Context alias 和 MAS 业务参数。复用必须由后续 SR 明确具体代码路径和必要性。

### 14.2 1.6.0 Capability / Package 目标边界

| 接口域 | 新 1.6.0 目标 | 旧发布物的定位 |
|---|---|---|
| Owner MAS | 24 Skill-facing Capability ↔ 24 公开 Callable；ToolCatalog 保留 25 contracts，MAS.RECONCILE internal-only | Owner v1alpha4 的 24/25 membership 仅作来源审计 |
| Provider READ | 两个通用 READ Capability 各映射一个公开 Callable，分别用封闭 contextKind / resourceKind 选择内部后端 | Provider v1.2.0 的 2 Capability / 11 READ Callable 仅作来源审计 |
| Provider Codec | 新增一个 Codec Capability ↔ 一个公开 Callable；首批只覆盖 SR-026 冻结的 NAS Decode 子集 | 旧 Provider Interface 未导出该 Capability；PR #86 Mock AMF Codec 不构成 Provider 发布 |
| Host Context | 由 SR-030 发布 Schema-only Package，0 Capability / 0 Callable；只供 Contract.contexts 的 Host Context Schema 闭包；requestSchema 始终指向 Skill 自有请求 Schema | SR-024 VERIFIED 仅证明旧 Development Package Publisher，不证明 1.6.0 Package |
| Host Artifact Channel | 新 1.6.0 目标为 ca-host.artifact-store/v2（no-hash）；v1 仅作历史契约 | 不复用 SHA-256 v1，不做双轨兼容 |

模型只接收 Capability 描述；Runtime 从 1.6.0 Artifact capabilityBindings 解析内部 Callable。Provider v1.2.0 的 11 个公开 READ ID 不得成为新 Skill-facing 输入。Studio Project Lock 保存导入来源、Package identity/version 与安装快照；这些 provenance 不得塞入 Package Manifest，也不得新增包级 hash / signature。

## 15. 原始设计资产与实现参考

- [ca-agent-demo Generic Host 架构原文](../../架构设计/参考实现/REF01-Python%20Generic%20Agent%20Host规范架构.md)
- [ca-agent-demo Skill/Tool/Runtime 边界原文](../参考实现/REF01-Skill%20Tool%20Runtime边界原文.md)
- [ca-agent-demo 当前实现基线原文](../../参考与审计/实现证据/REF01-ca-agent-demo当前实现基线原文.md)
- [ca-runtime Skill Context 原文](../参考实现/REF02-Skill%20Context设计原文.md)
- [ca-agent Host Artifact Store 契约原文](../目标参考/TARGET01-Go%20Host%20Artifact%20Store契约原文.md)
- [ca-agent Go Host P1 Artifact Store 验收证据](https://github.com/odango-chan/ca-agent/blob/447d0cce7e42c7c1184b11fb2563792eead68d51/docs/evidence/host-artifact-store-p1-20261118.md)
- [ca-client-tools Host integration](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/host-integration.md)
- [env-5gc-sim Mock AMF Codec C1 PR #86](https://github.com/odango-chan/env-5gc-sim/pull/86)（OPEN；仅测试对端消费迁移，不是 Agent Tool/Provider 集成）
- [F03 Plugin 平台设计](../F03-Plugin平台/Plugin平台设计说明书.md)
- [F03.05 Tool Interface / Provider 集成设计](../F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)
- [F04 Runtime 执行设计](../F04-Runtime执行/Runtime执行设计说明书.md)
- [F06 OpenAMSM 集成设计](../F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md)
- [Plugin Package / IPC 规范](../../规范/插件包与进程通信协议规范.md)
- [公共契约与所有权规范](../../规范/公共契约与所有权规范.md)

## 16. 验收门槛

- Event payload 与 Artifact slot 均由明确 Schema/Manifest 声明；未知字段和不支持版本 fail closed。
- Event / Run / Invocation / responseObligation / Artifact identity 不混用。
- Event Plugin 与 Host staging 只传相对路径描述符；绝不将原始 bytes/Base64 放入 NDJSON。
- Host 校验 staging 根目录、路径穿越、符号链接、真实 byteLength 和 slot requiredness。
- Artifact ref 为 Host-owned opaque token；不包含路径、外部 URI 或内容摘要。Host→Tool v2 只校验引用绑定、slot、mediaType、byteLength 和配额；不计算、传输或校验 SHA-256 / checksum / digest。
- Runtime 对 Artifact refs 执行 Run/Invocation 级授权；Tool 不能任意读取 Host 文件。
- Model projection 不包含原始 bytes、stagingPath、Provider 私有参数或未授权事实。
- Observation 必须来自 READ 能力；Evidence 必须符合 Owner Contract；UNKNOWN 不得提升。
- Next Host 尚未实现 ca-host.artifact-store/v2 channel 前，所有 artifact-bearing Provider binding 必须 NOT_CONFIGURED，并在远端 I/O 前拒绝；实现后必须通过 v2 no-hash fixtures，覆盖引用/slot/direction、字节长度、配额、过期、取消、清理和输出原子发布。
- Codec 只按正式发布的 1:1 Capability / Callable 和已验证消息子集调用；原始 Artifact 不被修改。
- Duplicate Event、Continuation、Delivery retry 和 Host restart 不产生伪成功或重复 mutation。
- 所有测试分别记录 Next / ca-agent-demo / ca-runtime 的仓库、SHA、命令和范围；外部参考仓 PASS 不算 Next PASS。

## 17. 功能归属与需求追踪

本说明书属于 F05。SR-009 仅承载 ca-openamsm-plugin 的 Event/Delivery 与本地 staging；SR-010 承载 Next Host ArtifactStore、ca-host.artifact-store/v2 no-hash channel server、Provider v2 Driver 和 Codec 消费；SR-015 记录历史 Tool Interface / Provider 设计移交；SR-026 发布 Codec Capability / Callable；SR-030 发布 Host Context Schema-only Package；真实 OpenAMSM E2E 由 SR-011 承载。F06 负责业务事件、Create/Modify/Release 映射；F03/F03.05 负责 Plugin 与 Provider IPC/Channel；F04 负责 Action 授权和 Owner outcome。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 归入 F05，明确 Context、ArtifactStore、Codec 与外部契约关系 | F05；SR-009；EC03/EC04；PR #1 |
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §1–12 | 补充 Event/Delivery staging、OpenAMSM slot、Run/Artifact 关联与失败处理 | IR-005；SR-009 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | 全文 | 从未实现视角重建 Context/Artifact 目标；核对 ca-agent-demo Context/ArtifactStore 代码与测试；明确不移植 content-addressed SHA256，并冻结 Host→Tool Channel 未发布边界 | Issue #12；SR-009、SR-010、SR-015 |
| 2026-11-25 | 0.4.0 | GPT-6.2（ChatGPT） | §5、§6.2、§7、§12～17 | 将 Host Artifact Store v1 从“未发布”纠正为已冻结契约；区分 Provider/Go Host 外部实现与 Next Python Host 未实现；明确随机 artifactRef 与逐字节 SHA-256 传输校验的不同语义，并把 SR-009/SR-010 的 Host/Plugin 责任拆清 | ca-agent contract pin 2c0b07f、ca-agent main 447d0cc P1 证据、ca-client-tools v1.2.0 源码/fixtures；避免沿用 ca-agent-demo 旧注释和内容寻址实现误判协议状态 | Issue #12；SR-009、SR-010、SR-015 |
| 2026-11-25 | 0.4.1 | GPT-6.2（ChatGPT） | §14～15 | 补入 env-5gc-sim PR #86 的 Mock AMF Codec C1 状态，并明确它不等于 Agent Tool/Provider Codec Consumer；保持 Next Host ArtifactStore/Channel NOT_IMPLEMENTED | 防止把测试对端的 Codec API 迁移误报为 Next Tool/Provider 或 Host 二进制链路完成 | Issue #12；SR-009、SR-010、SR-011 |
| 2026-11-26 | 0.4.2 | Codex / GPT-6 | 见本行变更 | §2～4 明确跨请求的响应义务及声明 Schema 的归属 | Issue #12 |
| 2026-11-28 | 0.4.11 | GPT-6.2（ChatGPT） | §5、§6.2、§7、§12～17、修订记录 | 将 v1 SHA-256 channel 限定为历史契约，定义 1.6.0 no-hash v2 目标并同步 SR-010/F03.05/SR-026 | Issue #113；IR-006；SR-010/026；F03.05；PR #115 |

| 2026-11-26 | 0.4.3 | GPT-6（ChatGPT） | 当前目标契约 | 新增 1.6.0 Capability / Codec / Host Context Schema-only Package 目标，修正模型可见 Callable 和旧 Provider v1.2.0 的证据定位 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.4.4 | GPT-6（ChatGPT） | 文档头、F05/Host Context 责任映射 | 统一正式评审范围/局部非目标声明，并将 1.6.0 Host Context Schema-only Publisher 纳入 SR-030 交叉追踪 | 修复 review context CI 头部门禁；区分 Host Context Schema 发布与其他 Context/Artifact 职责 | Issue #12；SR-030；PR #46 |
| 2026-11-26 | 0.4.5 | GPT-6（ChatGPT） | Host Context Package 消费边界、修订记录 | 明确 SR-030 Schema-only Package 只由 Contract.contexts 引用，不替代 Skill 自有 requestSchema | 与 CA-SL 1.6.0 §4 的 Request / Context Schema 分工一致，避免 Schema root 语义混淆 | Issue #12/#40；CA-SL 1.6.0；SR-030；PR #46 |
| 2026-11-27 | 0.4.6 | GPT-6.2（ChatGPT） | §2、§4 | 将 Skill schemas/scripts 纳入 Host 只读 Package Resource Access；区分资源读取与 Host Script Execution Capability | 让 LLM 与 Assurance 共用同一资源快照，不把 Package 资源混入 ArtifactStore 或任意文件访问 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.4.7 | GPT-6.2（ChatGPT） | §2、§4 | 将 Host Script Execution 的 LLM 暴露条件对齐为 `scriptExecution.llmEnabled` 与 Registry `llmInvocable` 双门禁 | 使 Package Resource Access 与脚本执行授权保持独立、明确 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.4.8 | GPT-6.2（ChatGPT） | §2、§4 | 移除 LLM 专属 Script 执行门禁，LLM 与 Assurance 共用 Script Registry / Runner | 使 Context 资源读取、脚本执行和 Package snapshot 的边界保持统一 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.4.9 | GPT-6.2（ChatGPT） | §2、§4 | 定义 Host Resource Read system Action 的请求、响应、Package snapshot 绑定、路径 / 大小限制和拒绝诊断；明确 LLM 可调用全部登记 Script | 补齐 LLM 读取 Schema / Script 的实际接口，消除只写“按需读取”却无请求输出契约的问题 | Issue #49；IR-008；SR-032 |

| 2026-11-27 | 0.4.10 | GPT-6.2（ChatGPT） | §2.1、修订记录 | 明确 Resource Read 使用 Host per-Run Runtime Action Budget，而非 Contract.limits.maxActions 业务动作预算 | 与 F04 Script Execution 预算规则统一，防止系统内建动作绕过 Host 资源上限 | Issue #49；IR-008；SR-007/032；PR #52 |
| 2026-11-28 | 0.4.13 | GPT-6（ChatGPT） | 文档头、§8、§10、修订记录 | 选择性吸收 #117 F05 v0.4.12 的 Ext1/T0 语义，新增独立 n2Ext1.request、Create/Update 可选 N2/Ext1、continuation Ext1 fail-closed 与 Create N1 必需性约束；同步 ingress.ack 严格身份白名单 | 关闭 #116 P2-01/02/10 的中央设计缺口，不把 #117 未通过复评的运行断言当作已验收 | Issue #50/#116；PR #115/#117 |
| 2026-11-28 | 0.4.14 | GPT-6（ChatGPT） | 文档头、§9、§11、修订记录 | 明确 Host 在 dispatch 前核验 deliveryId/responseObligationId/responseChannelId 三元权威映射；补充非空但错误 obligation、跨 Run/代际/Channel、重复/过期负例与 Plugin 非空校验的区别 | 将 SR-009 P2-05 的身份合法性明确分配给 Host；SR-011 AC-011-05 的系统负例 NOT_RUN，不冒称模块 PASS | Issue #50/#74/#75/#116；PR #115 |
