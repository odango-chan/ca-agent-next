# 业务接入与 OpenAMSM 集成设计说明书

> 文档类型：业务集成设计说明书  
> 文档版本：0.3.3\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first；实施及发布 NOT_RUN）
> 功能归属：F06 — 业务接入与集成；EC04、EC05、EC07  
> 关联 IR：IR-004、IR-005、IR-006  
> 关联 SR：SR-009、SR-010、SR-011、SR-017、SR-018、SR-019、SR-026、SR-030\
> 修订日期：2026-11-28
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
| Skill requestSchema / when / Event metadata | CA-SL **1.6.0** Publisher 正式冻结的 Schema/metadata 与 Compiler #62 CheckedExpr（尚未发布） | F02 T1 Resolver/Compiler 静态检查；旧 v1alpha5 只读审计 |
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

每个 `ingress.event` 的 IPC payload 固定包含：`eventId`、`ingressId`、`eventType`、可选 `externalRequestId`、`responseChannelId`、`source{protocol,peerId}`、上述规范化 `payload` 与 `artifacts[]`。规范化 `payload` 固定为 `{operationId, smContextRef?, request, discriminator?}`；其中 `request` 保留 OpenAPI JSON 字段名和值，不把原始 N1/N2 bytes 嵌入 JSON。每个 Artifact descriptor 固定包含 `stagingPath`（相对路径）、`slot`、`mediaType`、`contentId`（若 multipart 提供）和 `byteLength`。N2 `n2SmInfoType` 直接使用 OpenAPI enum 字符串；N1 最小 5GSM 头分类先要求至少 4 字节且第 0 字节 EPD=`0x2e`，从偏移 3（第 4 字节）读取 Message Type，并以 `0xC9`/`0xD1`/`0xD4` 字符串表达；第 1/2 字节分别是 PDU Session Identity/PTI，不得将首字节当作消息类型。该步骤仅作 T1 最小路由分类，不执行完整 NAS/NGAP 解码；短于 4 字节或 EPD 不匹配必须 fail-closed。

分类规则：
1. N1 为 `0xC9` 或 `0xD1` 且无 continuation-only discriminator 时，Event type 为 `nsmf.update-sm-context`。
2. N1 为 `0xD4`，或 N2 类型为上述三种 response 时，Event type 为 `nsmf.update-sm-context.continuation`；两路同时出现且都属于 continuation 时保留两路 Artifact/discriminator。
3. 同一请求同时出现新操作 discriminator（0xC9/0xD1）与 continuation discriminator，或 discriminator 缺失、未知、与 Content-ID/part 不匹配时，拒绝整个 ingress，不发布 Event。
4. 当前 Demo 不消费 `n2SmInfoExt1`；若其出现而没有显式受支持 slot，必须 fail-closed，不得静默丢弃或误并入 `n2SmInfo`。

`responseChannelId` 是 Plugin 为每个 HTTP/2 stream 生成的本地短期 handle，只用于把 Host 的 `delivery.dispatch` 送回该次 HTTP response；Plugin 只保留对应的内存 waiter。Host 为每个 ingress 创建 `responseObligationId`，并在 `delivery.dispatch` 中提供。Plugin 会在该帧中瞬时收到此 Host-owned opaque token，但不得生成、解释为 Run 身份、跨请求保存/持久化、转发或在 `delivery.result` 中回传；Plugin 只使用本地 `responseChannelId` 将当前 dispatch 写回对应 HTTP/2 stream，不得混同两种 ID。Plugin 不接收、不存储、不发送 Run ID、generation、releaseTxn 或 continuation state。

`externalRequestId` 不是上述 3GPP OpenAPI 字段。仅在受信 Demo peer 明确配置并发送私有 `X-CA-Request-Id` 时填入；真实对端未提供稳定身份时为空，不得用 `smContextRef`、Content-ID 或 responseChannelId 冒充跨重试幂等键。Host 负责 deduplication 和 Run association。Continuation 由 Host-owned pending index 依据受信 peer、operationId、smContextRef 和 discriminator 查找；无匹配或多重匹配时拒绝，不创建新 Run。Owner/Runtime 再验证原 Run 的 generation、releaseTxn、SUPI/PSI 与本路 originalInvocationId/Proof。当前 HTTP callback 的 response obligation 与原 Run 的执行身份分开管理。

SBI requestSchema 是 Skill 选择期正式 Request Schema 根；采用 OpenAMSM 支持版本的原始 OAS3 JSON 组件及其保留字节的 `$ref`，不复制整个 multipart 结构、不把 N1/N2 字节转为模型可见字符串。T0 只提取及 staging 原始 Artifact；T1 仅用 Publisher 冻结的 Event metadata 与请求输入及最小 discriminator；T2 绑定 Skill/Run 后由资格化 Codec READ 解码并验证正式 Result Schema；T3 Owner mutation/Receipt/Proof/Reconcile；T4 continuation 仅恢复原 Run。T2 Codec Result 不得进入 T1。

**1.6.0 MAS Skill 作者仅引用 Capability ID。** Compiler 只对 Publisher 正式冻结的 Owner/Provider 一对一公开映射检查 Grant、唯一 Callable、kind/Effect/Schema 并生成 Binding；Provider 两个查询 2/2，加正式 Codec 目标 3/3；Owner 两项旧 Parser 必须分别签认：双移除为候选 22/22；一项移除、一项重构为只消费已验证 Codec Result 的纯业务 READ 为候选 23/23；两项均重构为纯业务 READ 为候选 24/24；任一项未签认则最终成员数未冻结、Publisher 不得 Release。其他导出变化必须重新计数。Runtime 只消费已检查 Binding 与部署身份，不从 v1alpha5 历史 Artifact 或私有 backend Catalog 构造映射。

`MAS.RECONCILE` 保留 Owner ToolCatalog 作为 Coordinator internal-only target：Coordinator 按 original Invocation/Scope/Correlation 与原 Mutation Reconcile binding 回查，普通 Skill/LLM 直调则在 IPC 前拒绝。`MAS.RECEIPT_QUERY` 仍是受 Capability/Scope 控制的普通 READ。

## 5. CreateSMContext

Create 的新 Event 来自 Nsmf CreateSMContext。Event Plugin 提取 HTTP/JSON 请求字段和 N1/N2 multipart slots，形成 nsmf.create-sm-context Event。F02 根据 requestType、Event type 和可选 contract.when 选择建立 PDU Session 的 Skill。当前 ca-skills 的 Owner-linked v1alpha5 MAS 作者源位于 examples/skills/establish-pdu-session-mas；不要与 skills/establish-pdu-session-mas 下的早期独立示例混淆。

Skill 按 CA-SL **1.6.0 Procedure Capability Binding** 经内部 Owner Callable 完成订阅校验、SM Context、UECM、Policy、UP Anchor、地址、Charging、UP Session 等步骤。当前 Owner-linked 作者源为 examples/skills/establish-pdu-session-mas。每一步输入输出来自 Owner Tool Interface Package；Agent 不在 Core 中硬编码 5GC 流程。

成功响应由 Host 汇总 Runtime/Owner 结果并交给 Delivery Plugin。只有 Owner 有效 Receipt/Commit Proof 证明的 mutation 才能作为提交成功。

## 6. Modify

UE Modify 是 UpdateSMContext 中携带 5GSM PDU Session Modification Request（0xC9）的场景，不是任何 N1/N2 completion callback。

目标流程：

~~~text
UpdateSMContext + N1 0xC9
  -> EC04 minimal discriminator
  -> Skill Resolver selects Modify Skill
  -> F05 artifactRef carries original N1 bytes
  -> T2: required qualified Provider Codec READ Capability (0xC9 profile; ID/Schema not yet published)
  -> validate decoded NAS Result Schema; typed QoS delta
  -> Owner business-only validation (if published; no raw NAS decode)
  -> Owner UPN.MODIFY_QOS_DELTA Capability (mutation; unique Compiler Binding)
  -> PFCP Update QER 52/53
  -> SSM / Relay delivers N1 0xCB + N2 PDU_RES_MOD_REQ
  -> Owner waits for correlated completion
  -> Owner Receipt / final result
  -> UpdateSMContext response Delivery
~~~

约束：
- 原始 N1 字节始终保留在 Host ArtifactStore。
- Codec 是现有 Tools Extension 中**正式发布的 Provider READ Capability**，必须解码 0xC9 并经 Result Schema 校验；不是可选步骤，不得另建 Codec Manager。当前 0xC9 profile 未资格化，故新版 Modify 依赖路径 BLOCKED，禁止回退历史 Owner Parser。
- Agent 不自行解码 NAS、不计算 QER、不发 PFCP。
- PFCP 已应用但 N1/N2 Transfer 未确认时不得报告成功；Owner 可能返回 UNKNOWN/失败语义。
- N1/N2 completion response 不得重新启动 Modify mutation。
- QFI、5QI、GFBR/MBR 等字段由 Owner/Codec 契约定义，不由模型自由生成。

## 7. UE-requested Release

UE-requested PDU Session Release 是 UpdateSMContext 携带 NAS 5GSM 0xD1 的场景，不能与 AMF/network-initiated ReleaseSMContext 混为一谈。

目标流程：

~~~text
UpdateSMContext + N1 0xD1
  -> EC04 discriminator
  -> Skill Resolver selects UE Release Skill
  -> T2: required qualified Provider Codec READ Capability (0xD1 profile; formal ID/Schema pending)
  -> validate NAS Release Request Result Schema
  -> Owner business-only validation (if published; no second NAS decode)
  -> Owner SSM.BUILD_RELEASE_COMMAND Capability (Compiler-internal Callable Binding)
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

当前发布的 `SSM.RELEASE_CONFIRM_N1` 与 `SSM.RELEASE_CONFIRM_N2` 均为 MUTATION，须按各自原始 Invocation 验证 Owner 结果。当前 Owner v1alpha4 的 `SSM.PARSE_N1_RELEASE` 属历史 Skill-facing READ；在 Owner 签认其真实 handler/Schema 与纯业务重构前，1.6.0 不允许拿它替代 Codec。收到回调、读到字节或验证关联本身不能证明确认动作已提交。CA-SL Wait 的触发只允许声明的 READ，不得将这两个确认操作填入 READ trigger。

N1 与 N2 确认是两个独立输入，必须绑定同一个 Owner generation、releaseTxn、原始 Invocation 和 Run。重复、迟到、乱序、旧 generation 或错误 Session 的消息都不得触发清理。只有两者都确认后才可执行最终清理。

### 7.1 历史 Owner N1 Parser 审计与冻结门槛

固定源：`env-openamsm@dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 的 `contracts/mas/v1alpha4/capability-contracts.yaml`、`tool-catalog.yaml` 明确列出 `mas.ssm.n1.modify.parse / SSM.PARSE_N1_MODIFY` 与 `mas.ssm.n1.release.parse / SSM.PARSE_N1_RELEASE`，均为 READ。进一步核对 `patches/openamsm/0007-ssm-n1-modify-parse.patch`：`ssm_parse_n1_modify` 实际调用 `ogs_nas_5gsm_decode` 并投影 QoS 字段，因此 Modify Parser 确实实施协议解码，不能以“业务 READ”名义保留原调用。Release 的完整 handler 与数据流需要 Owner 独立审计，此处不能凭 ID 断言它也执行同一 decoder。

1. **唯一解码权威**：新 1.6.0 Skill 执行期 NAS/NGAP 协议 Decode 归已资格化 Codec Provider；Owner 保留业务语义、session 校验、mutation、Receipt/Proof/Reconcile。Owner 不得对收到的原始 NAS 再解码。
2. **待 Owner 签认的互斥方案**：若两个旧 Parser 仅为协议解析，移出新版 Skill-facing Owner Package；若仍提供独立业务校验，则重构为只接受已验证 Codec Result 的纯业务 READ，并由 Owner 冻结新的接口与 Schema。不要擅自删除旧发布文件，也不要将历史 ID/Schema 默认为新版重构身份；详情见 SR-029 §3.1。
3. **产品状态**：Provider Codec 目标 3/3 是设计结构，Release Request 0xD1、Modify 0xC9、NGAP 各自需要正式 Capability、Result Schema、handler、版本与 Golden。未满足的路径一律 BLOCKED / NOT_RUN，不以历史 Owner Parser 或 Plugin 最小路由分类降级。
4. **跨仓实施映射**：Next #40/#113 统一治理；未来 ca-client-tools Issue 负责 Codec Publisher/Release，env-openamsm Issue 负责 Parser 审计、业务 READ 合同选择与发布，二者仅在对应中央 SR READY 后建立。

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

JSON 的 `n1SmMsg.contentId`、`n2SmInfo.contentId` 必须各自唯一关联对应 part，N2 同时校验 `n2SmInfoType`。缺失、重复、类型冲突或不完整时不得产生 mutation。Namf 下行传输与 Nsmf 入站响应分别验收。

ca-skills `780497a2` 的三个 MAS `examples/skills/*-pdu-session-mas/assurance/contract.yaml` 均未声明 when。Create 输入含 pduSessionId、pti、requestType、dnn、sNssai、servingPlmn、requestedPduSessionType、requestedSscMode；Modify 为 pduSessionId、entryKind；Release 再含 trigger。按源 Schema 的必填、枚举与关闭对象校验，不能向输入追加 NAS 类型。Release 的 trigger 使用作者枚举，不能直接填入 NAS 字节 0xD1。每个 fixture 保存原始请求、parts、预期投影、候选集合和预期 Run。若 ingress 无法仅凭可用字段构造完整合法输入，登记 EC04/作者契约缺口并停止该场景，禁止 Host 补造默认值或偷偷做完整解码。

重试验收需要一次逻辑请求的稳定 externalRequestId。资源 URI、principal 或 MIME Content-ID 单独均不足以标识一次操作。在 Plugin 与 peer 的隔离 fixture 验证同次同内容重试、同 ID 内容冲突和两次内容相同的合法请求。隔离 Demo 的可控 peer 与 EC04 使用私有测试头 `X-CA-Request-Id`：peer 在新逻辑操作时生成唯一值并在其重试中复用，EC04 以已配置 peer 身份和该值构成 externalRequestId；新 HTTP 尝试各获独立 responseChannelId。比较相同 ID 的 operation、资源、规范化元数据及各 slot 原字节，内容冲突时拒绝；合法重复附着同一执行。该头仅属于 Demo 部署配置，不属于 3GPP。真实对端未提供等价稳定标识时，跨重连去重保持 BLOCKED。

### Create 入参的已知断点

`ca-agent-demo@57e277ff/src/ca_agent_host/integrations/fivegc/nsmf_http.py::_create_request` 对 `INITIAL_REQUEST` 投影为 1，从 N1 解出 PDU Session Type 与 SSC mode，并拒绝客户端在 SBI JSON 中注入同名字段。它还交叉检查 N1 与 JSON 的 PSI。当前 MAS Create 又在选择前要求这些字段。仅移植最小 discriminator 不能满足该契约。应在 ca-skills 的作者契约和 Procedure 中区分选择输入与绑定后的业务读取，由已声明的 Owner/Codec READ 根据原始 Artifact 获取后者。实施前把每个字段的来源、读取操作、Schema 和消费者写入同一 fixture，以固定作者 revision 验证；若没有已发布的所需 READ，保留该依赖的 BLOCKED。稳定重试与共享 /modify 路径的分类可用独立 fixture 先验收。

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

**数据流约束（不是可直接编译的 CA-SL 片段）：**

| 阶段 | 输入 | 产出与消费者 |
|---|---|---|
| T1 Resolve | 规范化 Event + 当前 SBI JSON + 0xC9 最小分类 | 选择 Modify Skill；不需要解码得到的 QFI/5QI/GBR |
| T2 Codec READ Node | Host 授权的原始 N1 `artifactRef` + Publisher 冻结的 0xC9 profile/slot | ca-client-tools Codec Capability→唯一 Callable；按正式 Result Schema 返回 QFI、5QI、GFBR/MBR 等**在发布 Schema 中真实存在的字段** |
| T2 Owner business-only READ（如需要） | **经过 Schema 校验的 Codec Result** 与 session identity | Owner 校验/业务决策，禁止重新解码 N1；具体 Callable/Schema 由 env-openamsm 后续冻结 |
| T2 Owner Mutation | 经验证的业务参数/会话身份 | 现有 QoS Delta 的 Capability-only 调用；Effect/Receipt/Proof 仍由 Owner 合同决定 |
| T3/T4 | Owner Receipt / correlated N1/N2 completion | commit 判定/原 Run 续跑；不触发第二次 mutation |

`codec-n1` 之类的本地节点名、`codecResult.qfi` 等字段路径此处**不预先发明为正式 CA-SL 机器接口**；作者在实际 0xC9 Codec Result Schema、Callable.kind、Owner 业务参数 Schema 冻结后，再按正式语法将 Codec Node 输出绑定到后继 Node `arguments`。不得继续引用旧的 `parse-n1.operation.output` 作为 Owner 原始 NAS 解码结果。当前 0xC9 Profile、Codec 1.6.0 Release、Owner 冻结裁决均 NOT_RELEASED / BLOCKED。Modify 的 Goal、Receipt、QoS 和 N1/N2 业务语义不变。

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

- Create、Modify、UE-requested Release 必须分别具有 T1 规范化 Event/Skill 选择 fixture、T2 Codec→Owner 结构化路径及正式发布的 Schema/Codec profile 证据。0xC9/0xD1 的 T1 最小分类应覆盖 malformed/unknown/unsupported 正负样例，证明该分类**不构成完整协议解码**；T2 单独校验 Codec Profile/Result Schema，并拒绝不合格数据。缺正式 Codec/Owner 合同时维持 BLOCKED/NOT_RUN。
- 本设计中的 typed Result 字段、Node 名、Codec 公开 Callable 以正式 Publisher/Compiler 契约为准，不能把示例标识误当成已发行机器接口。


1.6.0 Create/Modify/Release Skill 必须由 ca-skills 作者重新编写、使用唯一新 Compiler Check/Build/Verify 并正式发布 Bundle；历史 v1alpha5 E2E/Owner v1alpha4 只是业务输出参考，不能证明新 Runtime Binding 或新系统资格。SR-009 单独验 Plugin ingress/delivery/staging，SR-010 单独验 Host Artifact Channel、Provider/Codec，SR-011 才在正式新发布物和隔离环境齐备后执行同 UE/PSI 的真实 E2E；OM/EX 不能倒灌模块设计 READY 门槛。

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
| 2026-11-27 | 0.3.1 | GPT-6（ChatGPT） | §4.1、§5～7、修订记录 | 冻结三个 OpenAMSM normalized Event type、operationId、payload.request、NAS/N2 discriminator、Content-ID/slot 与 Host-owned continuation/response obligation 边界；固定 3GPP OpenAPI 源 SHA | 处理独立模型 Review #6082541121 的 SR-009 P1，消除 Event type/schema/Run 所有权歧义，避免插件实现猜测 | Issue #12；PR #46；SR-009；Review #6082541121 |
| 2026-11-28 | 0.3.2 | GPT-6（ChatGPT） | §4、§6～8、修订记录 | 保存 #46 原版 OpenAPI Event/Continuation 结构与 #45 Owner Parser 固定源审计；将旧 optional Codec + MAS.PARSE_N1 回退流程替换为 T2 必需的已资格化 Provider Codec READ，Owner 只做业务语义，确保发布合同仍 BLOCKED | 阻断旧 NAS Parser 冒充 Codec 或提前宣布 24/24 冻结 | Issue #12；#40；#113；PR #45；#46 |
| 2026-11-28 | 0.3.2-integration-2 | GPT-6（ChatGPT） | §13.2、§13.7 | 修复整合稿遗留的旧 `parse-n1.operation.output` 编译示例，恢复正式数据流约束和 0xC9/0xD1 双阶段验收条件 | 原始 NAS 只由资格化 Codec 解码；避免示例与 Owner Parser 不得 fallback 的新架构冲突 | Issue #12；#40；#113；PR #45；#46 |
| 2026-11-28 | 0.3.3 | GPT-6（ChatGPT） | §4.1、修订记录 | 修正 5GSM EPD 与 Message Type 字节偏移；明确 responseObligationId 在 dispatch 中的瞬时接收边界；补齐 Owner Parser 混合签认基数 | 防止将 NAS EPD 当作消息类型、误拒合法 Delivery，或将未签认的固定 Owner 数量当作发布条件 | Issue #12；PR #46；Review #6095143611 |
