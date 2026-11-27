# 业务接入与 OpenAMSM 集成设计说明书

> 文档类型：业务集成设计说明书  
> 文档版本：0.3.6\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first；实施及发布 NOT_RUN）
> 功能归属：F06 — 业务接入与集成；EC04、EC05、EC07  
> 关联 IR：IR-004、IR-005、IR-006  
> 关联 SR：SR-009、SR-010、SR-011、SR-017、SR-018、SR-019、SR-026、SR-030\
> 修订日期：2026-11-27
> 全局评审范围：继承根目录 Agent.md 的 review_scope。  
> 本文局部非目标：生产级资格、完整 NAS/NGAP 和 Core 业务分支。

## 1. 目标与范围

本功能验证通用 Agent 可通过 Skill-first Event 接入、统一 Plugin、Tool Interface Package 和 Owner 能力接入 OpenAMSM，而不在 Agent Core 中增加 OpenAMSM 专用业务分支。

本设计定义 Next 侧集成边界：
- EC04 OpenAMSM Plugin 负责 SBI ingress、Event normalization、multipart/Content-ID、二进制 staging 和 response Delivery。
- F02 Resolver 绑定 Skill，Plugin 不选择 Skill。
- F05 Host ArtifactStore 管理原始 N1/N2 字节。
- F04 Runtime 执行已绑定 Skill 的 Action，并解释 Owner Receipt/Outcome。
- EC03 ca-client-tools 提供 Tool Interface Package 和 Provider；Codec Tool 待公开发布。
- EC05 env-openamsm MAS Owner 负责权威业务状态和 mutation。
- EC07 env-5gc-sim 提供 Mock AMF SBI test peer；它不是 Owner，也不代表真实 5GC 状态。

## 2. Skill-first Event 接入

新 Event 流程：

~~~text
OpenAMSM SBI request
  -> EC04 Event Plugin parses / normalizes
  -> Host validates declared Event Schema
  -> Host creates Event + responseObligation
  -> F02 Resolver evaluates Skill candidates / contract.when
  -> Host binds Skill + Catalog generation
  -> F04 creates/resumes Run
  -> Runtime Action Boundary
  -> EC03 Tool Plugin / EC05 Owner
  -> Host prepares response
  -> EC04 Delivery Plugin
~~~

Event Schema 只描述协议归一化后的输入和 Artifact slots。它不携带 Skill ID、Goal、Procedure 或 Capability Grant。每个新业务 Event 必须绑定一个 Skill；逐个候选检查 requestSchema 与可选 when，单个候选不匹配时继续评估其余候选；最终零个匹配时澄清或拒绝；**多个 when=true** 时仅由 F02 在精确候选集内调用 LLM 消歧并校验 Skill ID；不得走 unbound Generic Agent fallback。

Continuation 不重新选择 Skill，必须恢复原 Run、原 Skill、原 generation；区分被恢复 Run 的原响应义务与本次 HTTP 请求自己的响应义务，分别按 correlation 完成。

## 3. OpenAMSM SBI Event / Delivery Plugin

EC04 的目标职责：
- 处理 SBI HTTP/2 ingress 和响应 Delivery。
- 解析 JSON 与 multipart/related。
- 根据 Content-ID 关联 N1/N2 原始字节。
- 对已声明的 SBI operation 生成规范化 Event。
- 仅提取 Skill selection 所需的最小 discriminator。
- 把原始二进制交给 F05 Host staging/ArtifactStore。
- 按 Host 的 delivery.dispatch 发送响应和输出 Artifact。

Plugin 不负责：
- Skill 选择、Run 生命周期或执行模式。
- Owner Tool 调用、Owner 状态机或 Receipt 判定。
- 完整 NAS/NGAP 业务解码。
- PFCP/QoS 计算或会话状态管理。
- Runtime Wait/Resume 或 Reconcile。

对于共享 UpdateSMContext，Plugin 只提取最小 5GSM discriminator：0xC9 表示 UE PDU Session Modification Request；0xD1 表示 UE-requested PDU Session Release Request。它不解析完整 NAS、不做业务状态判断；Host Resolver 根据规范化 Event 选择对应 Skill。畸形、未知或不支持消息必须 fail closed。

## 4. 协议与契约权威

| 内容 | 权威来源 | Next 使用方式 |
|---|---|---|
| Nsmf SBI Operation、HTTP 路径和 JSON Schema | 3GPP TS 29.502 / OpenAMSM OpenAPI 基线 | EC04 解析 |
| multipart/related、Content-ID、N1/N2 slot | 3GPP OpenAPI 与 OpenAMSM 实际行为 | EC04 + F05 |
| NAS 5GSM 消息与字段 | 3GPP NAS 标准、已资格化 Codec | Skill 按需调用 Codec Tool |
| NGAP N2 PDU Session Resource 消息 | 3GPP NGAP 标准、已资格化 Codec | Skill 按需调用 Codec Tool |
| Skill requestSchema / when | CA-SL **1.6.0** 正式作者规范/Runtime Artifact（未发布） | F02 Resolver，v1alpha5 仅历史追溯 |
| Tool Callable / IO Schema / Effect / Capability | Provider 自有 Callable 取自 Provider Interface Package，MAS Callable 取自 Owner Contract | F04 / Plugin Manager |
| Owner 状态、Receipt、Commit Proof、Reconcile | env-openamsm MAS Owner v1alpha4 | Runtime 结果解释 |
| 原始二进制 Artifact refs | Next Host ArtifactStore | F05 |


### 4.1 Normalized Event type、payload 与 continuation contract（规范性）

本节冻结 Next 集成侧的 Event 语义映射。F06 是 operation、discriminator、payload 字段和 fixtures 的中央权威；Event Plugin 仍负责在其 plugin.yaml / schemas 中发布实际 Event declarations 与 schema 文件，且必须逐项符合本节。不得由 Plugin、Harness 或 Runtime 各自再造一套事件名。上游 3GPP OpenAPI 文件只读引用，禁止修改原 YAML、删字段、补字段或手写替代 3GPP schema。

**固定来源**：env-openamsm commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`，`upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`（TS 29.502 V19.5.0）。使用其中 `PostSmContexts` / `SmContextCreateData` 与 `UpdateSmContext` / `SmContextUpdateData` 的原始 JSON 语义；插件包 schema 通过固定来源生成/引用，不修改源 YAML。Update 的 `smContextRef` 来自 URL path parameter，不从 body 猜测。

| Event type | OpenAPI operation / path | payload 必需字段 | classification | binary Artifact slots |
|---|---|---|---|---|
| `nsmf.create-sm-context` | `PostSmContexts` / `POST /sm-contexts` | `operationId="PostSmContexts"`；`request` 为原样 `SmContextCreateData` JSON object | 无 NAS operation discriminator；保留原始 `requestType` 等 OpenAPI 字段，不补默认值 | `n1SmMsg.contentId → n1.request`；`n2SmInfo.contentId → n2.request` |
| `nsmf.update-sm-context` | `UpdateSmContext` / `POST /sm-contexts/{smContextRef}/modify` | `operationId="UpdateSmContext"`；`smContextRef`；`request` 为原样 `SmContextUpdateData` JSON object | `discriminator.n1MessageType` 只允许 `0xC9`（UE Modify）或 `0xD1`（UE-requested Release） | `n1SmMsg.contentId → n1.request`；若请求实际含 N2 part，则 `n2SmInfo.contentId → n2.request` |
| `nsmf.update-sm-context.continuation` | 同一 `UpdateSmContext` / modify path | `operationId="UpdateSmContext"`；`smContextRef`；`request` 为原样 `SmContextUpdateData` JSON object | 至少包含 `discriminator.n1MessageType="0xD4"`，或 `discriminator.n2SmInfoType` 为 `PDU_RES_SETUP_RSP`、`PDU_RES_MOD_RSP`、`PDU_RES_REL_RSP`；两路可在同一请求中同时出现 | `n1SmMsg.contentId → n1.confirmation`；`n2SmInfo.contentId → n2.confirmation` |

每个 `ingress.event` 的 IPC payload 固定包含：`eventId`、`ingressId`、`eventType`、可选 `externalRequestId`、`responseChannelId`、`source{protocol,peerId}`、上述规范化 `payload` 与 `artifacts[]`。规范化 `payload` 固定为 `{operationId, smContextRef?, request, discriminator?}`；其中 `request` 保留 OpenAPI JSON 字段名和值，不把原始 N1/N2 bytes 嵌入 JSON。每个 Artifact descriptor 固定包含 `stagingPath`（相对路径）、`slot`、`mediaType`、`contentId`（若 multipart 提供）和 `byteLength`。N2 `n2SmInfoType` 直接使用 OpenAPI enum 字符串；N1 `n1MessageType` 只读取原始 NAS 首字节并以 `0xC9`/`0xD1`/`0xD4` 字符串表达，不执行完整 NAS/NGAP 解码。

分类规则：
1. N1 为 `0xC9` 或 `0xD1` 且无 continuation-only discriminator 时，Event type 为 `nsmf.update-sm-context`。
2. N1 为 `0xD4`，或 N2 类型为上述三种 response 时，Event type 为 `nsmf.update-sm-context.continuation`；两路同时出现且都属于 continuation 时保留两路 Artifact/discriminator。
3. 同一请求同时出现新操作 discriminator（0xC9/0xD1）与 continuation discriminator，或 discriminator 缺失、未知、与 Content-ID/part 不匹配时，拒绝整个 ingress，不发布 Event。
4. 当前 Demo 不消费 `n2SmInfoExt1`；若其出现而没有显式受支持 slot，必须 fail-closed，不得静默丢弃或误并入 `n2SmInfo`。

`responseChannelId` 是 Plugin 为每个 HTTP/2 stream 生成的本地短期 handle，只用于把 Host 的 `delivery.dispatch` 送回该次 HTTP response；Plugin 只保留对应的内存 waiter。Host 为每个 ingress 创建 `responseObligationId`，并在 delivery.dispatch 中提供；Plugin 不生成、不持有、不回传 responseObligationId。Plugin 不接收、不存储、不发送 Run ID、generation、releaseTxn 或 continuation state。

`externalRequestId` 不是上述 3GPP OpenAPI 字段。仅在受信 Demo peer 明确配置并发送私有 `X-CA-Request-Id` 时填入；真实对端未提供稳定身份时为空，不得用 `smContextRef`、Content-ID 或 responseChannelId 冒充跨重试幂等键。Host 负责 deduplication 和 Run association。Continuation 由 Host-owned pending index 依据受信 peer、operationId、smContextRef 和 discriminator 查找；无匹配或多重匹配时拒绝，不创建新 Run。Owner/Runtime 再验证原 Run 的 generation、releaseTxn、SUPI/PSI 与本路 originalInvocationId/Proof。当前 HTTP callback 的 response obligation 与原 Run 的执行身份分开管理。

SBI requestSchema 是业务 Skill 输入契约，不应复制完整 3GPP multipart schema 或把原始 N1/N2 变成模型可见字符串。

**新 1.6.0 MAS Skill 只引用 Capability ID。** Compiler 用 Owner 24/24 与 Provider 查询子集 2/2（含 Codec 的全量为 3/3）的正式公开映射检查 Grant、唯一 Callable、kind/Effect/Schema，并输出 Artifact capabilityBindings；Runtime 依 Binding 和部署固定的 Owner/Provider identity 验证内部 Callable Scope 后才分发。历史 v1alpha5 Artifact 不含 Capability 的审计事实**不构成新分发规则**。

`MAS.RECONCILE` 保留 Owner ToolCatalog 作为 Coordinator internal-only target：Coordinator 按 original Invocation/Scope/Correlation 与原 Mutation Reconcile binding 回查，普通 Skill/LLM 直调则在 IPC 前拒绝。`MAS.RECEIPT_QUERY` 仍是受 Capability/Scope 控制的普通 READ。

## 5. CreateSMContext

Create 的新 Event 来自 Nsmf CreateSMContext。Event Plugin 提取 HTTP/JSON 请求字段和 N1/N2 multipart slots，形成 nsmf.create-sm-context Event。F02 根据 requestType、Event type 和可选 contract.when 选择建立 PDU Session 的 Skill。当前 ca-skills 的 Owner-linked v1alpha5 MAS 作者源位于 examples/skills/establish-pdu-session-mas；不要与 skills/establish-pdu-session-mas 下的早期独立示例混淆。

Skill 按 CA-SL **1.6.0 Procedure Capability Binding** 经内部 Owner Callable 完成订阅校验、SM Context、UECM、Policy、UP Anchor、地址、Charging、UP Session 等步骤。当前 Owner-linked 作者源为 examples/skills/establish-pdu-session-mas。每一步输入输出来自 Owner Tool Interface Package；Agent 不在 Core 中硬编码 5GC 流程。

成功响应由 Host 汇总 Runtime/Owner 结果并交给 Delivery Plugin。只有 Owner 有效 Receipt/Commit Proof 证明的 mutation 才能作为提交成功。

## 6. Modify

UE Modify 是 UpdateSMContext 中携带 5GSM PDU Session Modification Request（0xC9）的场景，不是任何 N1/N2 completion callback。

以下流程中的 mas:: 名称仅表示 Compiler 完成 Binding 后的内部 Owner Callable。1.6.0 作者在 Procedure 中只写 §13 的 Capability ID。

~~~text
UpdateSMContext + N1 0xC9
  -> EC04 minimal discriminator
  -> Skill Resolver selects Modify Skill
  -> F05 artifactRef carries original N1 bytes
  -> optional Codec Tool parse
  -> mas::SSM.PARSE_N1_MODIFY (READ)
  -> mas::UPN.MODIFY_QOS_DELTA
  -> PFCP Update QER 52/53
  -> SSM / Relay delivers N1 0xCB + N2 PDU_RES_MOD_REQ
  -> Owner waits for correlated completion
  -> Owner Receipt / final result
  -> UpdateSMContext response Delivery
~~~

约束：
- 原始 N1 字节始终保留在 Host ArtifactStore。
- Codec Tool 是普通 Tool，通过 Runtime Action Boundary 调用；不得另建 Codec Manager。
- Agent 不自行解码 NAS、不计算 QER、不发 PFCP。
- PFCP 已应用但 N1/N2 Transfer 未确认时不得报告成功；Owner 可能返回 UNKNOWN/失败语义。
- N1/N2 completion response 不得重新启动 Modify mutation。
- QFI、5QI、GFBR/MBR 等字段由 Owner/Codec 契约定义，不由模型自由生成。

## 7. UE-requested Release

UE-requested PDU Session Release 是 UpdateSMContext 携带 NAS 5GSM 0xD1 的场景，不能与 AMF/network-initiated ReleaseSMContext 混为一谈。

以下流程中的 mas:: 名称仅表示 Compiler 完成 Binding 后的内部 Owner Callable。1.6.0 作者在 Procedure 中只写 §13 的 Capability ID。

~~~text
UpdateSMContext + N1 0xD1
  -> EC04 discriminator
  -> Skill Resolver selects UE Release Skill
  -> mas::SSM.PARSE_N1_RELEASE (READ)
  -> mas::SSM.BUILD_RELEASE_COMMAND
  -> N1 Release Command 0xD3 + N2 PDU_RES_REL_CMD
  -> SMF sends Namf N1N2MessageTransfer to AMF
  -> mas::SSM.RELEASE_CONFIRM_N1 (0xD4)
  -> mas::SSM.RELEASE_CONFIRM_N2 (PDU_RES_REL_RSP)
  -> validate same releaseGeneration + releaseTxn + original Run
  -> mas::PA.DELETE_SM_POLICY_C
  -> mas::UPN.DELETE_UP_SESSION (PFCP 54/55)
  -> mas::SE.EMIT_RELEASE_EVENT_C
  -> mas::SC.RELEASE_SM_CONTEXT_C
  -> Owner Receipt / final result
~~~

当前发布的 `SSM.RELEASE_CONFIRM_N1` 与 `SSM.RELEASE_CONFIRM_N2` 均为 MUTATION，须按各自原始 Invocation 验证 Owner 结果。收到回调、读到字节或验证关联本身不能证明确认动作已提交。CA-SL Wait 的触发只允许声明的 READ，不得将这两个确认操作填入 READ trigger。

作者侧两路确认分别写 `mas.ssm.n1.release.confirm.n1` 和 `mas.ssm.n1.release.confirm.n2`。N1 与 N2 确认是两个独立输入，必须绑定同一个 Owner generation、releaseTxn 和 Run。N1、N2 各自以其 confirm mutation 的 originalInvocationId 验证本路 Receipt/Proof，UNKNOWN 时按本路原调用 Reconcile；互换两路收据必须拒绝且清理次数为零。重复、迟到、乱序、旧 generation 或错误 Session 的消息都不得触发清理。只有两者都确认后才可执行最终清理。

## 8. Owner Receipt 与 UNKNOWN

MUTATION 调用的提交结果由 EC05 Owner 决定。Runtime 使用 originalInvocationId 查询 Receipt；UNKNOWN 不能提升为 COMMITTED，也不能直接重发 mutation。PFCP deletion UNKNOWN 只能按 Owner 精确绑定的 Reconcile 设计处理。Delivery 成功不等于业务 mutation 成功；HTTP 2xx 不等于 Owner COMMITTED。

## 9. Mock AMF 与真实 E2E

EC07 Mock AMF SBI Test Peer 负责发送协议准确的 Create/Update/UE-requested Release 输入、模拟 AMF 对端交互、提供 N1/N2 回调和可重复测试场景。它是测试对端，不拥有 OpenAMSM SMF 的业务状态，也不代替真实 AMF/UPF。

必须分开记录：
- Mock AMF 组件/进程 PASS；
- Mock AMF 对真实 OpenAMSM 的协议交互 PASS；
- ca-agent-demo Python Host/Runtime E2E PASS；
- Next Python Host/Plugin/Runtime E2E PASS；
- Production Qualification（本 Demo 不声明）。

前面几项的 PASS 不自动传递到后面的层级。

当前 ca-skills main 已包含 Owner-linked 作者源：`examples/skills/establish-pdu-session-mas`、`examples/skills/modify-pdu-session-mas`、`examples/skills/release-pdu-session-mas`；PR #83～#86 均已合并。它们是当前正式 Skill 源，不应与 `skills/` 下的早期独立示例混淆。2026-11-23 Development E2E 证据早于当前 Skill revision；必须对当前精确 revision 重跑，不能自动沿用旧 PASS。

## 10. 当前实现审计

| 对象 | 当前证据 | 状态 |
|---|---|---|
| env-openamsm MAS Owner v1alpha4 | main dc83ccbf；23 业务 Callable + 2 证据 READ；Receipt/Proof/Reconcile | IMPLEMENTED |
| Scheme C Modify / UE-requested Release | Owner 设计和补丁记录；真实 PFCP 52/53、54/55 与 N1/N2 流程证据 | IMPLEMENTED（Owner/隔离演示范围） |
| env-5gc-sim Mock AMF | main 6ba1dc4；完整设计、实现记录和 E2E 场景 | IMPLEMENTED（测试对端范围；按证据限定） |
| ca-client-tools Provider v1.2.0 | main 7bcb261；Provider package/typed callables | IMPLEMENTED；Next adapter 未验收 |
| ca-client-tools Codec Phase B | PR #39 OPEN（非 Draft）；Phase B FINAL_PASS / PHASE_C_READY，尚未合并 | NOT_MERGED |
| env-5gc-sim Mock AMF Codec C1 | PR #86 OPEN；仅将 Mock AMF 测试对端迁移到统一 Codec Facade，不触及 ToolCatalog、Provider、Host 或 Next Runtime | NOT_MERGED |
| ca-openamsm-plugin | main eb83c8f 仅 README；PR #1 OPEN/Draft | NOT_IMPLEMENTED |
| ca-agent-demo Provider runtime cutover | PR #246 OPEN；#248/#249 OPEN；#251 OPEN/Draft（Contract.when 设计提案，未进入 main） | NOT_MERGED |
| Next OpenAMSM Skill-first E2E | 依赖 F02/F03/F04/F05/EC04/EC05 | NOT_RUN |

## 11. 验收门槛

- Event Plugin 只做协议解析、最小分类和响应 Delivery；不选择 Skill。
- Create、Modify、UE-requested Release 分别有规范 Event fixture、Skill 选择和完整 Owner callable 路径。
- 0xC9 与 0xD1 的正负向分类测试覆盖 malformed/unknown/unsupported。
- N1/N2 原始 bytes 不进入 NDJSON 或 LLM Context；Artifact refs 按 Run/Invocation 授权。
- Modify PFCP 52/53 与 N1/N2 response correlation 通过。
- UE Release N1 0xD4 + N2 PDU_RES_REL_RSP 的双确认、generation、releaseTxn 和 Run 绑定通过。
- Owner Receipt/Commit Proof/UNKNOWN/Reconcile 全部按 exact-original 规则验证。
- duplicate Event、duplicate invocation、late/old N1/N2、delivery failure 不产生第二次 mutation。
- Mock AMF 与真实 OpenAMSM E2E、ca-agent-demo E2E、Next E2E 分层报告。
- 不声明 Production Qualification。

## 12. 原始设计资产

- [OpenAMSM Plugin Draft 架构](../../架构设计/外部能力域/EC04-OpenAMSM%20Go%20Event%20Plugin架构提案原文.md)
- [MAS Owner Receipt / Proof](../外部能力域/EC05-OpenAMSM%20Owner/MAS%20Owner契约与Receipt设计原文.md)
- [Scheme C Modify / Release Owner](../外部能力域/EC05-OpenAMSM%20Owner/Scheme%20C%20Modify与Release%20Owner设计原文.md)
- [PFCP UNKNOWN Reconcile](../外部能力域/EC05-OpenAMSM%20Owner/PFCP%20UNKNOWN%20Reconcile与重启恢复设计原文.md)
- [Mock AMF SBI Test Peer 完整设计](../外部能力域/EC07-5GC仿真与Mock%20AMF/Mock%20AMF%20SBI%20Test%20Peer完整设计原文.md)
- [env-5gc-sim 架构原文](../../架构设计/外部能力域/EC07-5GC模拟器架构原文.md)
- [EC03 Typed MAS Callables](../外部能力域/EC03-Tool%20Provider/MAS%20Scheme%20C%20Typed%20Callables设计原文.md)

### EC04 两端实现与逐例复核

OpenAPI 源位于 env-openamsm `dc83ccbf` 的 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`。以下路径相对 `/nsmf-pdusession/v1`。在 ca-openamsm-plugin 实现 HTTP/2 与 Event/Delivery，ca-agent-next 实现通用 IPC、ArtifactStore、Resolver、Continuation。对端 fixture 来源为 env-5gc-sim `6ba1dc4` 的 `internal/mockamf/ue_modify.go` 和 `ue_release.go`。

| HTTP POST / operationId | 输入与身份 | 可观察结果 |
|---|---|---|
| `/sm-contexts` / `PostSmContexts` | Create，解析引用的 multipart part | 新 Event。成功时 201 和 Host 公共资源 Location |
| `/sm-contexts/{smContextRef}/modify` / `UpdateSmContext` | N1 0xC9 或 0xD1 | 分别为新 Modify 或新 UE Release；核对 Owner 结果后验证成功响应 204 |
| 同一 modify 路径 | N2 PDU_RES_SETUP_RSP、PDU_RES_MOD_RSP、PDU_RES_REL_RSP，或 N1 Release Complete 0xD4 | 进入对应既有事务。Release 的 N1/N2 可分次到达；回调自身的 HTTP 响应按本次请求关联 |
| `/sm-contexts/{smContextRef}/release` / `ReleaseSmContext` | AMF/network-initiated Release | 与 UE 0xD1 分开，未支持的入口显式拒绝 |

JSON 的 `n1SmMsg.contentId`、`n2SmInfo.contentId`、`n2SmInfoExt1.contentId` 必须分别关联 N1、N2、N2 Ext1 命名 part 的 `Content-ID`；同时分别校验 `n2SmInfoType` 与 `n2SmInfoTypeExt1`。引用目标缺失、重复 Content-ID、错槽、媒体类型或类型冲突时不得产生 mutation。未被 JSON 引用的 part 不得交给 Codec；额外 part 的拒绝 / 忽略由 ingress profile 明确规定。Namf 下行传输与 Nsmf 入站响应分别验收。

历史 ca-skills `780497a2` 的三个 MAS 作者源曾把 `pti`、`requestedPduSessionType`、`requestedSscMode` 放进 Create 输入；这些字段不能据此成为新 CA-SL 1.6.0 的 T1 Request 必填。新作者源必须拆分：T1 只声明真实 SBI `jsonData` / 已规范化 Event 中可获得的字段；NAS-only 字段在 T2 由已选 Skill 的正式 Codec READ Result 提供，再通过显式 SourcePath / arguments 使用。Modify / Release 也须逐字段确认 SBI / NAS / NGAP 来源。Release 的 trigger 是作者层枚举，不是 NAS 字节 0xD1。每个 fixture 保存原始 SBI、multipart parts、JSON / N1 / N2 原字节、T1 可用字段、T2 预期 Result、候选集合和 Run。缺少字段来源或 Codec READ 时停止该子场景并保持 BLOCKED；禁止 Host 补默认值或偷偷完整解码。

重试验收需要一次逻辑请求的稳定 externalRequestId。资源 URI、principal 或 MIME Content-ID 单独均不足以标识一次操作。在 Plugin 与 peer 的隔离 fixture 验证同次同内容重试、同 ID 内容冲突和两次内容相同的合法请求。隔离 Demo 的可控 peer 与 EC04 使用私有测试头 `X-CA-Request-Id`：peer 在新逻辑操作时生成唯一值并在其重试中复用，EC04 以已配置 peer 身份和该值构成 externalRequestId；新 HTTP 尝试各获独立 responseChannelId。比较相同 ID 的 operation、资源、规范化元数据及各 slot 原字节，内容冲突时拒绝；合法重复附着同一执行。该头仅属于 Demo 部署配置，不属于 3GPP。真实对端未提供等价稳定标识时，跨重连去重保持 BLOCKED。

### Create 入参的已知断点

`ca-agent-demo@57e277ff/src/ca_agent_host/integrations/fivegc/nsmf_http.py::_create_request` 的历史实现会从 N1 解出 PDU Session Type 与 SSC mode，并交叉检查 N1 与 SBI JSON 的 PSI；这证明这些值的协议来源在 NAS，而不是 SBI JSON。当前历史 MAS Create 在 Skill 选择前要求这些字段，形成 T1/T2 循环依赖。CA-SL 1.6.0 新作者源必须将这些 NAS-only 值移到 T2 Codec READ 后的 Procedure 输入；T1 仅使用原版 TS 29.502 `jsonData` 中真实存在且经 OpenAPI 3.0 校验的字段。实施前逐字段固定 SBI / NAS 来源、operation、Schema Component / Codec Output、读取阶段和消费者；SBI/N1 冲突必须在 Owner mutation 前失败。没有正式 Codec READ 时保留 BLOCKED。

## 13. OpenAMSM Capability-first Skill 映射（1.6.0 目标）

本节是 CA-SL 1.6.0 新 MAS Skill 重写草案；历史 v1alpha5 只作事实审计，不可在新版 Compiler/Agent 运行，也不提供迁移工具。

### 13.1 Create

~~~yaml
record-session-establishment-event:
  operation:
    capability: mas.se.establishment-event.record
    arguments:
      ue_identity: context.supi
      psi: context.request.pduSessionId
      event: "ESTABLISHED"
      sessionKeys: create-sm-context.operation.output.session_keys
~~~

该 Capability 唯一映射 Owner Callable SE.EMIT_EVENTS，保留 ESTABLISHED 输入 Schema 和 se.establishment-event-recorded Evidence Guarantee。

### 13.2 Modify

~~~yaml
apply-qos-delta:
  operation:
    capability: mas.upn.up.qos.delta
    arguments:
      ue_identity: context.supi
      psi: context.request.pduSessionId
      qos_flows_delta: "1"
      qfi: parse-n1.operation.output.qfi
      five_qi: parse-n1.operation.output.five_qi
      gfbr_ul: parse-n1.operation.output.gfbr_ul
      gfbr_dl: parse-n1.operation.output.gfbr_dl
      mfbr_ul: parse-n1.operation.output.mfbr_ul
      mfbr_dl: parse-n1.operation.output.mfbr_dl
~~~

Modify 的 Goal、Owner Receipt、QoS Delta 和 N1/N2 语义不变；仅把 Skill-facing Callable 引用改为 Capability。

### 13.3 UE-requested Release

~~~yaml
emit-release-event:
  operation:
    capability: mas.se.release-event-marker.write
    arguments:
      ue_identity: context.supi
      psi: context.request.pduSessionId
      ev: "RELEASED"
~~~

该 Capability 唯一映射 Owner Callable SE.EMIT_RELEASE_EVENT_C，保留 RELEASED 输入 Schema 和 se.release-event-marker-written Evidence Guarantee。它与 Create 的建立事件 Capability 分离，不把本地释放标记描述为外部 Delivery。

### 13.4 Provider Observation

Provider 的 SMF Context Read 和 NF Metrics Read 分别使用一个 READ Observation Capability，并通过封闭 selector 选择查询资源：

- openamsm.smf.mas.context.read：contextKind 为 sc / pa / upn / ssm / iam / ups / ca / saa。
- openamsm.nf.metrics.read：resourceKind 为 amf.ue-info / amf.gnb-info / smf.pdu-info。

selector 是公开 Callable Input Schema 的字段；11 个旧 backendOperationId 保留在 Provider 内部，不进入 Skill 源。

### 13.5 Codec Capability 与 Host Context Schema Package

- Codec 不作为模型可见的自由 Callable；SR-026 发布一个 Skill-facing Codec Capability ↔ 一个公开 Callable，首批仅支持冻结的 NAS Decode 消息子集。Codec 输入使用已授权的 Artifact ref / slot，不把原始 N1/N2 bytes 转成模型可见字符串；Provider 私有 handler 和 backendOperationId 不进入 Skill 源。
- Provider 新目标由两个通用 READ Capability / Callable 加一个 Codec Capability / Callable 构成，合计 3/3；若 Publisher 采用多个 Package，跨 Package 合计仍为 3/3，且每个 Package 快照内独立校验。
- MAS Skill 的 requestSchema 根必须为 Skill 自有 Schema。仅 Contract.contexts 可引用 Host Context Schema-only Package 的显式导出。SR-030 负责其 1.6.0 Publisher；该 Package 只导出 Schema，0 Capability / 0 Callable，不得虚构 Tool。SR-024 VERIFIED 仅代表历史 Development Publisher，不满足新版消费门槛。
- Codec / Host Context 的正式发布物尚未存在；相关产品 AC 保持 NOT_RUN / BLOCKED。

### 13.6 业务流程不变

Create → Modify → Release 的顺序、Owner authoritative state、Receipt / Commit Proof、UNKNOWN / Reconcile、N1/N2 generation 和 Evidence Goal 均保持现有定义。此次只改变 Capability / Callable 契约表达，不重写 5GC 业务流程，也不声明新 E2E 已通过。

**1.6.0-only 待评审硬门槛：** MAS Skill 必须按 1.6.0 重新编写与发布；旧 E2E PASS 不证明新版本；此处只是目标设计，产品和 E2E 均 NOT_RUN。


### 13.7 真实联测与模块证据分层

1.6.0 Create/Modify/Release Skill 必须由 ca-skills 作者重新编写、使用唯一新 Compiler Check/Build/Verify 并正式发布 Bundle；历史 v1alpha5 E2E/Owner v1alpha4 只是业务输出参考，不能证明新 Runtime Binding 或新系统资格。SR-009 单独验 Plugin ingress/delivery/staging，SR-010 单独验 Host Artifact Channel、Provider/Codec，SR-011 才在正式新发布物和隔离环境齐备后执行同 UE/PSI 的真实 E2E；OM/EX 不能倒灌模块设计 READY 门槛。

## 14. OpenAMSM 原版 OpenAPI 3.0 直接消费与 Create 解码阶段修正（IR-009）

**原版来源与直接引用**：ca-skills / SR-031 只原样代发布 OpenAMSM 实际使用的 OpenAPI 3.0 YAML 与可达引用闭包，所有 bytes / 相对 `$ref` 不变。Plugin 按 OAS 3.0 operation / requestBody / multipart 验证；Compiler 在 Skill 显式 pin Source Bundle 后可直接解析原版 `components/schemas`。外部 Schema Object 按 OAS 3.0 dialect 处理，不生成 G.4 Adapter；Skill-owned `requestSchema` 根及本地节点仍遵循 G.4。Host Context 只经 `Contract.contexts` 引用。

1. **T0**：Event Plugin 按 TS 29.502 的选定 `PostSmContexts.requestBody` 验证 SBI JSON、`multipart/related`、`jsonData`、N1/N2/N2 Ext1 binary parts、Content-Type 与 Content-ID；只 lazy resolve 该选定 surface 的 refs，不全文件 eager resolve 其他 operation。当前 `SmContextCreateData` 的可达闭包为 TS 29.502 / 29.571 / 29.510 NFManagement / 29.518 Namf 四份原版 YAML。依据 CommonData `RefToBinaryData.contentId`，`n1SmMsg.contentId` ↔ N1 part、`n2SmInfo.contentId` ↔ N2 part、`n2SmInfoExt1.contentId` ↔ N2 Ext1 part；必须精确匹配对应 slot，引用目标缺失、重复 Content-ID、错槽或错媒体类型在 Artifact 发布前拒绝。未被 JSON 引用的 part 不得交给 Codec；额外 part 的拒绝 / 忽略由 ingress profile 明确规定。通过验证后保存原始 N1/N2/N2 Ext1 bytes。T0 只做最小 0xC9 / 0xD1 / 0xD4 分类，不完整解码。
2. **T1**：Skill Request / `when` 只读取到场 SBI JSON / 已规范化 Event 字段；不调用 Codec。Create 的 PDU Session Type / SSC mode / NAS PTI 等只有从 N1 解码才能获得，不能在 T1 强制要求。
3. **T2**：选定 Procedure 调正式 Codec READ 后，才能通过 Provider Output Schema 使用 NAS / NGAP Result。SBI 与 N1 的 PSI / 类型冲突在 Owner mutation 前拒绝，不补默认值。
4. **Modify / Release / Continuation**：0xC9 是最小分类，不代表完整 Modify Decoder；0xD1 首批候选不证明 Create / Modify / N2 已支持；0xD4 / N2 completion 只续跑原 Run，检查 generation / PSI / PTI / N2 message type。
5. **类型职责**：SBI 原版 OAS Source Bundle（SR-031）、Compiler OAS3 Resolver（SR-013）、Provider NAS/NGAP Output Schema（SR-026）、Skill-owned Request（CA-SL 1.6.0）与 Host Context（SR-030）是不同工件 / Owner。Codec JSON 不代表 Owner Receipt / Commit Proof；Source Bundle 不产生 Tool Scope。
6. **门槛**：SR-031 Source Bundle、SR-010 ingress / Artifact Channel、SR-013 Compiler Resolver、SR-026 Provider Profile、SR-027 Bundle 各自独立验收。没有正式 OAS3 Resolver / Provider / 1.6.0 Bundle 时对应产品 AC NOT_RUN / BLOCKED；不引入旧版兼容。

[权威设计](../EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。


## 修订记录



| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 根据 OpenAMSM Owner、Plugin Draft、Mock AMF 与当前跨仓状态重建 Create/Modify/UE Release 集成设计 | 历史记录未单独分列原因 | Issue #12；SR-017～019 |
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §2、§4、§10 | 更新 ca-skills Owner-linked Skill 源路径、PR #83～#86 状态及 ca-client-tools v1.2.0 / CA-SL Release Record 状态 | 避免旧示例、旧 Provider 版本和规范头部候选文字造成误读 | Issue #12；SR-017～019、SR-023 |
| 2026-11-25 | 0.2.2 | GPT-6.2（ChatGPT） | §10 | 更新 ca-client-tools PR #39 与 env-5gc-sim PR #86 的 Codec 状态；明确 Mock AMF C1 不代表 Agent Tool/Provider 或 Next 集成 | 防止把独立测试对端迁移误计为 OpenAMSM Agent 集成进展 | Issue #12；SR-009～SR-011、SR-017～SR-019 |
| 2026-11-26 | 0.2.3 | Codex / GPT-6 | 见本行变更 | §2、4、6、7 校正候选判定、HTTP 响应义务和真实 Owner Callable；§12 增补 EC04 固定协议来源、请求投影与独立复验 | 历史记录未单独分列原因 | Issue #12 |
| 2026-11-26 | 0.2.4 | Codex / GPT-6 | 见本行变更 | 补足 Create 的真实 NAS 字段来源及跨仓设计缺口；补齐正式文档的评审范围与非目标；明确可控 peer/Plugin 的重试身份；§7 依据 Owner catalog 区分确认 mutation 和 Wait READ | 历史记录未单独分列原因 | Issue #12 |
| 2026-11-26 | 0.2.5 | GPT-6.2（ChatGPT） | §4、§8 | 同步冻结 v1alpha5 Capability Build-time / Runtime 边界及 MAS.RECONCILE internal-only 保证 | 让 OpenAMSM 业务集成流程引用 F03.05 的唯一 Tool/Provider Runtime 设计 | IR-006 · SR-015 · Issue #12 |
| 2026-11-26 | 0.2.6 | GPT-6（ChatGPT） | 新增 Capability-first 1.6.0 章节与状态 | 移植旧分支设计并按无兼容最新基线校正 | 仅设计待评审，不将历史 E2E 视为新版本通过 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.7 | GPT-6（ChatGPT） | 规范性设计与验收门槛 | 纠正多 true 候选决策和 MAS 旧 Callable-only Runtime，区分模块/系统证据 | 修复新旧语言/能力运行时冲突 | Issue #12/#40；SR-013/025/029；PR #46 |
| 2026-11-26 | 0.2.8 | GPT-6（ChatGPT） | 1.6.0 Capability / Codec 目标 | 补齐 Provider Codec 1:1 Capability 与 Host Context Schema-only Package 的业务集成边界 | 修正历史 Callable-only 描述和 Provider 能力基数遗漏 | Issue #12/#40；SR-025/026/030 |
| 2026-11-27 | 0.3.0 | Codex / GPT-6 | §5～7、§13.5 | 明确作者 Capability、两路收据、Schema 与 Provider 基数 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.1 | GPT-6（ChatGPT）；ChatGPT / GPT-6 | §4.1、§5～7、修订记录；3GPP Schema 与阶段输入补充 | 冻结三个 OpenAMSM normalized Event type、operationId、payload.request、NAS/N2 discriminator、Content-ID/slot 与 Host-owned continuation/response obligation 边界；固定 3GPP OpenAPI 源 SHA；明确公共 Schema-only 导出、选择期 Request 与执行期 Codec Result 的 Link / 业务字段来源 | 处理独立模型 Review #6082541121 的 SR-009 P1，消除 Event type/schema/Run 所有权歧义，避免插件实现猜测；关闭 Create 选择前依赖 NAS 解码的循环、固定跨包类型门禁 | Issue #12；PR #46；SR-009；Review #6082541121；IR-009；Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.3.2 | ChatGPT / GPT-6 | 本轮 IR-009 设计修正 | 固定 OpenAMSM 版本 + 原版 YAML 逐字节代发布；显式区分可选 Adapter 与 Provider Codec 输出 | 落实原版 YAML 不得改动、消除误把原版当 G.4 的风险 | Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.3.3 | ChatGPT / GPT-6.2 | §2、§14 | 以原版 OAS3 operation / multipart 和直接组件引用替代 Adapter；修正历史 Create NAS-only 字段不能在 T1 必填 | 关闭 Create 选择前解码循环并对齐原始标准 | IR-009；Issue #47；SR-010/013/026/031 |
| 2026-11-27 | 0.3.4 | ChatGPT / GPT-6.2 | §14 | 补齐 PostSmContexts 四文件选定闭包、lazy refs 和 RefToBinaryData Content-ID 到 N1/N2/N2 Ext1 part 的精确关联 | 防止 SBI ingress 错配二进制消息或因无关 operation refs 误失败 | IR-009；Issue #47；SR-010/031；EC01 |
| 2026-11-27 | 0.3.5 | ChatGPT / GPT-6.2 | §2、§14 | 补齐 N2 Ext1 type 对账；未引用 part 不交 Codec，额外 part 策略归 ingress profile | 避免未引用数据被误解码或对原版 Schema 施加隐含限制 | IR-009；Issue #47；SR-010/031；EC01 |
| 2026-11-27 | 0.3.6 | GPT-6.2（ChatGPT） | §4.1、§14、修订记录 | 合并 PR #46 的 Normalized Event / continuation contract 与 IR-009 原版 OAS3 / multipart / Codec 分阶段消费设计 | 保留原始 3GPP JSON 与 binary transport 边界，避免 Event Plugin 与 Codec 责任重叠 | Issue #47/#12；PR #46/#48；IR-009；SR-009/010/013/031 |