# 业务接入与 OpenAMSM 集成设计说明书

> 文档类型：业务集成设计说明书  
> 文档版本：0.2.2  
> 状态：目标集成设计已重建；外部 Owner 能力已实现，Next Plugin/Host 端到端尚未验收  
> 功能归属：F06 — 业务接入与集成；EC04、EC05、EC07  
> 关联 IR：IR-004、IR-005、IR-006  
> 关联 SR：SR-009、SR-010、SR-011、SR-017、SR-018、SR-019  
> 修订日期：2026-11-25

## 1. 目标与范围

本功能验证通用 Agent 可通过 Skill-first Event 接入、统一 Plugin、Tool Interface Package 和 Owner 能力接入 OpenAMSM，而不在 Agent Core 中增加 OpenAMSM 专用业务分支。

本设计定义 Next 侧集成边界：
- EC04 OpenAMSM Plugin 负责 SBI ingress、Event normalization、multipart/Content-ID、二进制 staging 和 response Delivery。
- F02 Resolver 绑定 Skill，Plugin 不选择 Skill。
- F05 Host ArtifactStore 管理原始 N1/N2 字节。
- F04 Runtime 执行已绑定 Skill 的 Action，并解释 Owner Receipt/Outcome。
- EC03 ca-client-tools 提供 Tool Interface Package、Provider 和 Codec Tool。
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

Event Schema 只描述协议归一化后的输入和 Artifact slots。它不携带 Skill ID、Goal、Procedure 或 Capability Grant。每个新业务 Event 必须绑定一个 Skill；没有候选、输入冲突或 when 失败时显式停止，不得走 unbound Generic Agent fallback。

Continuation 不重新选择 Skill，必须恢复原 Run、原 Skill、原 generation 和原 response obligation。

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
| Skill requestSchema / when | CA-SL v1alpha5 | F02 Resolver |
| Tool Callable / IO Schema / Effect / Capability | ca-client-tools Interface Package | F04 / Plugin Manager |
| Owner 状态、Receipt、Commit Proof、Reconcile | env-openamsm MAS Owner v1alpha4 | Runtime 结果解释 |
| 原始二进制 Artifact refs | Next Host ArtifactStore | F05 |

SBI requestSchema 是业务 Skill 输入契约，不应复制完整 3GPP multipart schema 或把原始 N1/N2 变成模型可见字符串。

## 5. CreateSMContext

Create 的新 Event 来自 Nsmf CreateSMContext。Event Plugin 提取 HTTP/JSON 请求字段和 N1/N2 multipart slots，形成 nsmf.create-sm-context Event。F02 根据 requestType、Event type 和可选 contract.when 选择建立 PDU Session 的 Skill。当前 ca-skills 的 Owner-linked v1alpha5 MAS 作者源位于 examples/skills/establish-pdu-session-mas；不要与 skills/establish-pdu-session-mas 下的早期独立示例混淆。

Skill 按 CA-SL Procedure 调用 Owner Callable，完成订阅校验、SM Context、UECM、Policy、UP Anchor、地址、Charging、UP Session 等步骤。当前 Owner-linked 作者源为 examples/skills/establish-pdu-session-mas。每一步输入输出来自 Owner Tool Interface Package；Agent 不在 Core 中硬编码 5GC 流程。

成功响应由 Host 汇总 Runtime/Owner 结果并交给 Delivery Plugin。只有 Owner 有效 Receipt/Commit Proof 证明的 mutation 才能作为提交成功。

## 6. Modify

UE Modify 是 UpdateSMContext 中携带 5GSM PDU Session Modification Request（0xC9）的场景，不是任何 N1/N2 completion callback。

目标流程：

~~~text
UpdateSMContext + N1 0xC9
  -> EC04 minimal discriminator
  -> Skill Resolver selects Modify Skill
  -> F05 artifactRef carries original N1 bytes
  -> optional Codec Tool parse
  -> SSM.PARSE_N1_MODIFY (READ) / typed parse result
  -> UPN.MODIFY_QOS_DELTA or published Modify Callable
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

目标流程：

~~~text
UpdateSMContext + N1 0xD1
  -> EC04 discriminator
  -> Skill Resolver selects UE Release Skill
  -> SSM.PARSE_N1_RELEASE (READ)
  -> SSM.BUILD_RELEASE_COMMAND
  -> N1 Release Command 0xD3 + N2 PDU_RES_REL_CMD
  -> Event/Delivery Plugin sends response
  -> Wait on N1 Release Complete 0xD4
  -> Wait on N2 PDU_RES_REL_RSP
  -> validate same releaseGeneration + releaseTxn + original Run
  -> PA.DELETE_SM_POLICY
  -> UPN.DELETE_UP_SESSION (PFCP 54/55)
  -> SE.EMIT_RELEASE_EVENT
  -> SC.RELEASE_SM_CONTEXT(finalize=1)
  -> Owner Receipt / final result
~~~

N1 与 N2 确认是两个独立输入，必须绑定同一个 Owner generation、releaseTxn、原始 Invocation 和 Run。重复、迟到、乱序、旧 generation 或错误 Session 的消息都不得触发清理。只有两者都确认后才可执行最终清理。

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

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 根据 OpenAMSM Owner、Plugin Draft、Mock AMF 与当前跨仓状态重建 Create/Modify/UE Release 集成设计 | Issue #12；SR-017～019 |
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §2、§4、§10 | 更新 ca-skills Owner-linked Skill 源路径、PR #83～#86 状态及 ca-client-tools v1.2.0 / CA-SL Release Record 状态 | 避免旧示例、旧 Provider 版本和规范头部候选文字造成误读 | Issue #12；SR-017～019、SR-023 |
| 2026-11-25 | 0.2.2 | GPT-6.2（ChatGPT） | §10 | 更新 ca-client-tools PR #39 与 env-5gc-sim PR #86 的 Codec 状态；明确 Mock AMF C1 不代表 Agent Tool/Provider 或 Next 集成 | 防止把独立测试对端迁移误计为 OpenAMSM Agent 集成进展 | Issue #12；SR-009～SR-011、SR-017～SR-019 |
