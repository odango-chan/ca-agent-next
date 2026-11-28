> 迁移来源：ca-agent-demo/docs/design/createdsession-fabric-ingress-interface.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：SBI ingress、fabric、response correlation 设计  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；证据的当前有效性需按具体 main/PR/测试 SHA 单独核验。

---

> **HISTORICAL / SUPERSEDED (2026-11-11):** non-normative history/evidence. Current authority: docs/design/generic-agent-host-architecture.md and docs/work/generic-agent-host-final-convergence-20261110.md.

# CreatedSession Fabric HELD Ingress 接口（D3-A1 flat Agent message v0.1）

Status: **D3-A1 consumer / wire contract snapshot**；该快照时真实 Fabric joined 未执行。后续 P8-D4 有历史核心网 live PASS，但 HELD action disposition 仍有 UNRESOLVED responsibility；当前状态见 [W0 audit](w0-system-audit.md)。
（D3-A1 当时：`FABRIC + DEMO JOINED = NOT_RUN`；后续 P8-D4 证据不代表当前 main 重跑或 disposition 全闭合。）
Tracking：ca-agent-demo#78 / #139、env-fabric#60
适用代码：`src/ca_agent_demo/integrations/env_fabric/createdsession_ingress.py`

本文只记录**已核对存在**的 Fabric 接口，以及本仓 consumer 对它的精确映射。
它不定义 Fabric 契约、不新增 endpoint、不把候选分支写成已合并能力。

## 0. 结论摘要

| 层 | 状态 | 依据 |
| --- | --- | --- |
| Consumer 实现（flat v0.1） | **已实现** | `createdsession_ingress.py`；`ResidentFabricCreatedSessionSource` 组合真实客户端 |
| L1 Mechanism | **PASS** | `tests/unit/test_createdsession_fabric_contract_conformance.py`、`tests/unit/test_createdsession_live_ingress.py` |
| L2 Fake Integration | **PASS** | `tests/fixtures/createdsession_fabric_contract_server.py` 复刻 producer 语义 |
| 真实 Fabric joined | **NOT_RUN** | 本轮未启动两进程 joined 验收 |
| 真实 5GC E2E | **NOT_RUN** | 无 WSL2 / Open5GS / UERANSIM 证据 |

L2 PASS 不能读成真实 Fabric PASS：本地假服务只复刻协议，不产生真实 HELD Action、不接触 SCP/SMF。

## 1. Producer 证据（只读核对）

| 对象 | 值 |
| --- | --- |
| 仓库 | `odango-chan/env-fabric`（只读） |
| 分支 | `codex/createdsession-d3-a1-governed-ingress` |
| 本轮验收 head | `ee4eb44d464aa3c82f12dc22351ad08344a1149d` |
| 已核对文件 | `internal/inline/sbi/governed/http_transport.go`、`internal/inline/sbi/governed/processor.go`、`internal/agentmessage/message.go`、`internal/heldaction/core.go`、`contracts/proposed/createdsession-agent-ingress/v0.1/`、`docs/design/network-intent-control.md` |

该分支仍是**候选实现**，不在 `env-fabric/main`；本文描述的是它当前的已验收代码，不是已发布能力。

## 2. 端点与传输

`env-fabric sbi-governed` 起两个监听：SBI（h2c，接收 AMF 的 CreateSMContext）与
**control（loopback，HTTP/1.1）**。Demo 只使用 control 监听。

| 方法 | 路径 | 鉴权 | 语义 |
| --- | --- | --- | --- |
| `GET` | `/v1/network-intents/next` | `Authorization: Bearer <control token>` | 有界长轮询；body 为 flat Agent message v0.1，身份与 revision 在响应头 |
| `POST` | `/v1/network-actions/reject` | `Authorization: Bearer <control token>` | 固定 REJECTED disposition（向原 SBI waiter 回 503，不转发 SCP） |
| `POST` | `/v1/network-actions/forward` | `Authorization: Bearer <control token>` | 受控 FORWARD：把保留的原始请求向强制 SCP 重放一次，并把真实 SCP/SMF 响应保留给原 waiter |
| ~~`GET`~~ | ~~`/v1/network-source-records/{ref}/n1-sm`~~ | — | **已删除**，同未知路由一样返回 `404` |
| `POST` | `/v1/network-actions/execute` | — | 不存在（未安装），Demo 也不调用 |

Control 监听的约束（producer 侧强制）：

- 必须绑定 loopback；Demo 侧配置同样要求 numeric loopback HTTP；
- 明文 HTTP/1.1，无 TLS；
- 两个路由都要求同一个私有 bearer token；缺 token 或 token 错误均为 `401`；
- `POST` 主体按单个 JSON 值严格解码（未知字段、成员别名、重复成员、缺失成员、`null`、尾部 JSON → `400`）。

## 3. 发现、领取、重复投递与并发

```text
AMF --CreateSMContext(h2c)--> Fabric SBI 监听
    Fabric Project -> Prepare -> Emit -> Publish 出唯一 HELD action（内存，单进程）
Demo --GET /next(token)--> flat Agent message + X-Env-Fabric-Action-Ref/Revision
Demo --POST /reject(token)--> 固定 503 回到原 AMF waiter
```

| 问题 | producer 行为 | Demo 的处理 |
| --- | --- | --- |
| Action 如何被发现 | control `GET /next` 暴露内存中**单个** active HELD action | `next_intent()`；空 body = 有界轮询到期，继续轮询 |
| 身份在哪 | `actionRef` / `revision` 只在 HTTP 头 | 从响应头精确读取，各必须恰好一个值；缺失/重复/非法即 fail closed |
| Action identity | `actionRef = "sbi-action:" + sourceRecordRef` | 由 `actionRef` **推导** `sourceRef`，并用精确正则校验；不猜、不补 |
| 源记录 | 无 source 读取端点 | Demo 不再读 raw N1；找不到 source 读取路径是契约事实，不是缺陷 |
| 重复投递 | HELD 期间 `GET /next` 重复返回同一 body + 同一身份 | 先持久 claim；重投按 journal `RETRY_SAFE / DUPLICATE_REJECTED / BLOCKED_UNRESOLVED` 分类 |
| 并发领取 | producer 用 `nextMu` 串行化；action 存储为进程内存 | Demo 单实例进程锁（`flock`），第二个 Host 不 READY、不轮询 |
| Action 寿命 | `deadline = 源 ingress 时刻 + --timeout`，**不出现在 wire 上** | Demo 不再读取 deadline；用自己的 `maxOperationSeconds` 约束本仓执行，并记录“无 deadline”事实 |
| 取消 / 过期 | 原 SBI caller 取消 → `ABANDONED`；到 deadline → `EXPIRED`；两者都不会再交付 | Demo 只看到终态：poll 不再返回该 action；reject 得到 `409`/`410` |

## 4. Flat Agent message v0.1

body 只有 11 个成员，**没有** `contractVersion`、`intentRef`、`episodeRef`、`actionRef`、
`source`、`subjectRef`、`operation`、`request`、`sourceRefs`、`revision`、`deadline`、
`sNssai` 或任何 envelope：

```text
sourceName timestampUs messageType seqNo supi pduSessionId pti requestType [sst] [sd] [dnn]
```

| 字段 | 约束 | Demo 用途 |
| --- | --- | --- |
| `sourceName` | 必须 `SRF` | profile 门禁 |
| `timestampUs` | 正整数微秒 | 事件时间证据（整数微秒换算，不经浮点） |
| `messageType` | 必须 `193`（PDU Session Establishment Request） | profile 门禁；195 是 Reject，不是本 ingress 事件 |
| `seqNo` | 正整数 | 参与消息摘要与证据 |
| `supi` | 非空、无首尾空白 | 选择 operator `sourceProfiles[supi]` |
| `pduSessionId` | `1..15` | Runtime 请求上下文 |
| `pti` | `0..255` | Runtime 请求上下文 |
| `requestType` | `1,2,3,4,6` | Runtime 请求上下文 |
| `sst` | 可选；`0..255`；显式 `0` 与缺席不同 | Runtime S-NSSAI |
| `sd` | 可选；`0..0xFFFFFF`；必须伴随 `sst` | Runtime S-NSSAI |
| `dnn` | 可选；非空白 | Runtime DNN |

严格性：成员集合必须恰好是“8 个必填 + 允许的可选子集”，出现其它成员即拒绝；
整数成员不接受 `bool`/字符串；`sd` 无 `sst` 拒绝；`supi`/`dnn` 带空白拒绝。

### 4.1 DNN / S-NSSAI 是 wire 可选字段

producer 对 `dnn`/`sst`/`sd` 使用 `omitempty`：CreateSMContext 可以依赖订阅默认值，
因此真实消息**可以没有**它们。Demo 无权威臆造默认值：

- `next_intent()` 接受可选缺席的 wire 形状（出现时仍严格校验）；
- 在 materialization 阶段若缺少 `dnn` 或 S-NSSAI，抛 `FabricIngressError`；
- 该失败走唯一 disposition owner，对精确 action 投递 reject，AMF waiter 得到 503；
- 不臆造默认 DNN、不按订阅猜测 S-NSSAI。

### 4.2 Lifecycle 身份不在 wire 上（P8-B2）

flat 消息成员集合里没有 `lifecycleRef`，Fabric 的 `--demo-lifecycle-ref` 也不出现在
本 endpoint 的 body 或头里。生命周期身份只能有两个来源之一：

1. **v0.4（当前）**：Resident 部署的 `lifecycleBinding.lifecycleRef`（operator 声明），
   经 journal、invocation facts 传到 UDM/PCF hold 选择器；
2. **v0.3（兼容）**：`lifecycle:createdsession:<sourceRef>` 派生值，provenance 记为
   `DERIVED_FROM_INGRESS`。

Hold scope 的比较是**相等检查**，不做推断：

| Fabric hold scope | 本地 binding | 结果 |
| --- | --- | --- |
| `environmentRef` 相同、`lifecycleRef` 相同 | 同 | 唯一候选 |
| `environmentRef` 相同、`lifecycleRef` 不同 | 同 environment | `UDM_HOLD_LIFECYCLE_MISMATCH` / `PCF_HOLD_LIFECYCLE_MISMATCH` |
| `environmentRef` 不同 | — | `UDM_HOLD_ENVIRONMENT_MISMATCH` / `PCF_HOLD_ENVIRONMENT_MISMATCH` |
| 无任何同 operation kind 的 hold | — | `UDM_HOLD_NOT_FOUND` / `PCF_HOLD_NOT_FOUND` |

P8-B1 的 `UDM_HOLD_LIFECYCLE_IDENTITY_MISMATCH` 现场就是第一列比较失败：Fabric 用
operator lifecycle，Resident 用派生值。修复只在 Demo 侧（v0.4 声明 + 单 ingress 绑定），
没有改变 Fabric 的 Hold/Claim/Deliver/Forward 语义，也没有把 Lifecycle 塞进 flat 消息。

## 4.3 业务 Intent 与 5gc-intent policy（2026-11-10 更新）

当前 flat v0.1 message 的 exact member set 没有业务 intent 或自然语言字段。Consumer 的 intent_ref 是本地从 actionRef 派生的 correlation identity，不代表业务 intent。

**生产入口始终是本节描述的 Fabric SBI / CreatedSession ingress。** 未来自然语言输入是同一 SBI contract 的可选 intent 字段，不新增 /chat、/intent endpoint，不增加 envelope，不建立第二条生产 ingress。

当前行为：
1. Host 先验证 flat v0.1 schema、source、action、lifecycle 与 event identity。
2. 未识别 / 不支持的结构化 event 在进入 5gc-intent policy 前 NO_MATCH。
3. 当前已识别的 PDU Session Establishment event 因 intent 成员缺席，进入 5gc-intent absent policy，确定性选择 eligible 的 establish-pdu-session。
4. 当前 v0.1 只验收 intent absent 的生产分支；不得把 intent_ref 当业务 intent，也不得伪称当前 wire 已支持自然语言。

未来同一 SBI contract 扩展可选 intent 后：
- intent absent：仍按已识别 event 的确定性 route；
- intent present 且有效非空：event schema / scope 先限制 Root candidates，再由 IntentGoalModelAdapter 产生 ProducedGoal、SkillRoutingModelAdapter 从 exact eligible candidates 中选择；
- intent present-null / empty / whitespace / invalid type / uninterpretable / unknown / ambiguous：fail closed，不回退 absent default；
- intent 与结构化 event scope 冲突：拒绝，不能让自然语言覆盖协议语义。

W2b 在 producer / consumer contract 正式升级前，只用同一 Host API 与下一版 contract fixture 验收；CLI 只是该 Host API 的调试 Adapter，不是生产入口或独立 composition root。详细执行顺序见 [五个工作包](../work/runtime-mechanism-convergence-task-package.md)。
## 5. 控制头

| 头 | 含义 | Demo 校验 |
| --- | --- | --- |
| `X-Env-Fabric-Action-Ref` | `sbi-action:sbi-source:<32 hex>` | 恰好一个值，精确匹配 producer 形态，否则 fail closed |
| `X-Env-Fabric-Action-Revision` | 必须回填为 `expectedRevision` | 恰好一个值，十进制正整数 |

HELD 重投返回相同 body、相同 action identity、相同 revision。响应带 `Cache-Control: no-store`。

## 6. Reject（唯一的可交付 disposition）

```json
{
  "apiVersion": "service-fabric.env-fabric/v1alpha1",
  "kind": "SBIHeldActionRejectRequest",
  "contractVersion": "service-fabric.createdsession-sbi-held-action-disposition/v0.1",
  "actionRef": "sbi-action:sbi-source:<32 hex>",
  "expectedRevision": 1
}
```

`forward` 的请求/响应与 reject 共用 `service-fabric.createdsession-sbi-held-action-disposition/v0.1`，
请求 kind 为 `SBIHeldActionForwardRequest`（同样只有 `actionRef` + `expectedRevision`），
成功响应 kind 为 `SBIHeldActionForwardResult`，且 `actionState=FORWARDED`、
`forwardedToSCP=true`、`sourceResponseStatus` 为真实下游状态。producer 在
HTTP 200 返回前已经完成一次出站发送并保留真实响应，因此该调用可能是同步长请求。

成功响应必须是 `SBIHeldActionRejectResult`，且 `actionRef`、`sourceRecordRef`、
`actionState=REJECTED`、`sourceResponseStatus=503`、`forwardedToSCP=false` 全部与本地
action 精确一致，否则不算确认。

| producer 结果 | 含义 | Demo 行为 |
| --- | --- | --- |
| `200` + 精确结果 | Fabric 本地接受 reject，已向原 waiter 发 503，未转发 SCP | `confirm_held_action_reject` → `REJECTED/CONFIRMED` |
| `400` | 请求字段不符 | 传输失败 → `UNRESOLVED`，`OUTCOME_UNKNOWN` |
| `401` | token 缺失/错误 | 同上 |
| `404` | action 不存在 | 同上 |
| `409` | **不是确认**：revision 过期、action 已终态、waiter 已不在等待 | 同上 |
| `410` | action 已过期 | 同上 |
| 超时 / 连接中断 / 非 JSON | 外部效果未知 | 同上，`UNRESOLVED`，`OUTCOME_UNKNOWN` |

责任窗口（D2 已实现，本阶段沿用，不另置疑点）：

1. claim（消息身份 digest）在任何其它工作之前持久化；
2. 收到消息后立即绑定该消息的精确内容 digest；
3. 任何执行前失败都只经 `CreatedSessionHeldDispositionOwner`；
4. `POST` 之前先持久化 `ATTEMPTED`，只有精确结果才 `CONFIRMED`；
5. `ATTEMPTED` / `OUTCOME_UNKNOWN` 的重投一律 `BLOCKED_UNRESOLVED`，不重发、不新造 `dispositionRef`；
6. 已确认的 reject 依据 journal 回答，绝不再 POST。

`200` **只**表示 Fabric 接受了 reject 请求：action 完成一次本地 `REJECTED` 转换、固定
`503` 已在该进程的 waiter 通道上发出。它**不**表示 AMF 已经收到 503、原 SBI caller
已经观察到它，或 5GC 会话达到任何远端状态；`SBI 503` 也不等于 PDU Session 创建成功或失败。

## 7. Consumer 映射（本仓）

| Fabric 事实 | Demo 位置 |
| --- | --- |
| 端点、头、字段、状态码、token 文件 | `src/ca_agent_demo/integrations/env_fabric/createdsession_ingress.py` |
| HELD claim / 消息 digest 绑定 / 重投分类 / 执行前失败交接 / Lifecycle 身份 | `src/ca_agent_demo/demo/createdsession_resident_ingress.py` |
| Lifecycle → ingress 单一绑定（journal） | `createdsession_reference_journal.py::bind_lifecycle_ingress` |
| 唯一 reject 投递者与 attempt 状态机 | `src/ca_agent_demo/demo/createdsession_held_disposition.py` |
| 持久责任记录（`held_actions`） | `src/ca_agent_demo/runtime/createdsession_reference_journal.py` |
| 组合、READY 门禁、顺序 Invocation | `src/ca_agent_demo/demo/createdsession_resident_host.py` |
| 部署字段（`fabric.*`、`lifecycleBinding.*`） | `src/ca_agent_demo/demo/createdsession_resident_config.py` |
| 进入既有 Skill Runtime 前的材料化 | `createdsession_resident_ingress.py::_materialize` |
| admitted operation-context selection（PDU Session Type / SSC Mode） | `src/ca_agent_demo/demo/createdsession_source_profile.py` |

Token 文件规则与 producer 一致：普通文件、权限不含 `0o077`、trim 后 32..4096 字节。

## 8. Provider 输入边界（本阶段的能力缺口）

Flat 消息只提供 `pduSessionId`/`pti`/`requestType`/`supi`/`dnn`/`sst`/`sd`/`messageType`/
`seqNo`/`timestampUs`。producer 同时删除了 raw N1 source 读取，因此本仓**不再解码 NAS**：

- 已删除 `integrations/ca_provider_5gc/createdsession_n1_decode.py` 及其依赖；
- `requestedPduSessionType` / `requestedSscMode` 由**可信 operator 部署资料**显式声明
  （`sourceProfiles[*].requestedPduSessionType` / `requestedSscMode`），属于 admitted
  operation-context selection；无默认值，缺失即配置错误；
- UE IPv4、QoS/AMBR/ARP、UPF N3/TEID 等事实仍不在本 ingress 可得范围内，相关
  Provider 能力继续 `NOT_RUN`/fail-closed，不由本仓臆造。

## 9. 部署前提

- **同主机**：control 监听只能 loopback，Resident Host 与 Fabric 必须同机（SBI 监听另在 h2c 端口）。
- `fabric.origin` 必须等于 `fabric.allowedOrigin`；明文 HTTP 仅用于该 loopback control 端点。
- `fabric.controlTokenFile` 指向 producer `--control-token-file` 使用的同一私有 token。
- `fabric.timeoutSeconds` 是 Demo 的**读超时**（轮询有界等待），与 producer 的 action 寿命 `--timeout` 是两个独立量。
- 本阶段不新增 TLS/mTLS、CA/PKI；Demo → Provider 五类 adapter 已统一为固定白名单 `http://` 的明文 HTTP（Provider 侧按 Runtime caller CIDR 准入），与本机 loopback Fabric control 端点互不混用。

## 10. D3-A1 阶段不实现项（历史快照，非当前 main 缺口结论）

| 项 | 状态 |
| --- | --- |
| `POST /v1/network-actions/execute`（Fabric 向 SCP 转发原请求） | Demo 不调用；执行权威在 Agent |
| 成功 disposition（2xx/非 503 回填给原 SMF waiter） | D3-A1 当时的能力缺口；P8-D4 已有 FORWARDED/201 历史证据，但本地 held-actions UNRESOLVED 责任映射仍需收敛 |
| Fabric → 原 SMF waiter 的成功响应交付与 SMF 消费 | D3-A1 当时尚未验证；P8-D4 曾验证原 waiter 收到真实响应并被 SMF 消费（历史特定 SHA / 环境） |
| raw N1 读取 / NAS 解码 | producer 已删除该端点；本仓不恢复、不替代 |
| Fabric action 过期后的自动恢复 / 重放 | 不做；`UNRESOLVED` 保留并停止 Host |
| HA / 多实例 / 自动恢复 | 不做 |

`UNRESOLVED` 表示责任仍在 Demo 侧留档，不等于成功或失败；Host 以 `BLOCKED` 停止而不是猜测。
