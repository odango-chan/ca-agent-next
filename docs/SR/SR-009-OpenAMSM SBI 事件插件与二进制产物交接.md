# SR-009：OpenAMSM SBI 事件插件与二进制产物交接

> 文档类型：软件需求（SR）  
> SR 版本：0.2.15
> 状态：整项 DRAFT；Issue #116 固定旧快照对 AC-009-01/02/03/05/06 的原批准子集与 AC-009-04 Event mapping/Schema/test-double 给出限定 `APPROVE_FOR_READY`（0 P0/0 P1/11 P2）；当前 v0.2.15 新增 Ext1/可选 N2、Host 三元义务和 IPC ack 规则尚需独立复评，相关产品测试 NOT_RUN，不自动扩大原批准。生产 T0 classifier 直接依赖 ca-client-tools#44，`BLOCKED_EXTERNAL_INPUT`；Next Host/系统 OM/E2E 及 Production 均 NOT_RUN。
> 下一步：独立复核本版中央契约及 PR #117 的 4 P1，再决定阶段 READY；ca-openamsm-plugin Issue #2 / PR #3 是外部模块候选实现（尚未合并），其 CI 不能取代 Next 或新子项的验收；生产 classifier 等 ca-client-tools#44。
> 创建日期：2026-11-25  
> 修订日期：2026-11-28\
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.13 §1～13、16；[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.3.9 §2～5、§4.1、§13.7、§14；[插件包与进程通信协议规范](../规范/插件包与进程通信协议规范.md) v0.2.8 §5～6
> Acceptance：OM-01～OM-03、OM-05～OM-08、OM-14、OM-15（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查 ingress/delivery 插件职责、multipart/Content-ID 字节保真、Host-owned staging/ArtifactStore 与失败重放。
- **已知依赖与未验证项：**Owner/Provider/Go Host 外部证据不等于 Next Python Host/Plugin 实现；正式 1.6.0 Skill 选择留给 Core；系统 OM 未执行。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

## 1. 目标

实现独立 Go OpenAMSM Event/Delivery Plugin，通过统一 Plugin Package/IPC 接入 SBI JSON 与 multipart 二进制，并由 Host 管理 ArtifactStore。

## 2. 实施范围

- SBI HTTP/2 ingress、JSON/multipart/related 解析和 Content-ID 关联。
- Plugin 仅通过 Host 提供的 inbound/outbound staging directory 写入/读取原始 N1/N2 文件描述符；不拥有 ArtifactStore，不生成 artifactRef。Host 导入/导出由 Next SR-010 承载。
- 将规范化 Event 发布给 Host，并执行 SBI Delivery 编码。
- 对共享 UpdateSMContext 通过 ca-client-tools 正式发布的窄 T0 5GSM classifier API 取得最小 NAS discriminator，区分新 Modify、UE-requested Release 与既有事务的 N1/N2 completion；Plugin 不实现/复制 parser、不调用完整 DecodeNAS；API 未发布前仅可用 test double 验证 Event mapping，生产分类保持 BLOCKED。Host Resolver/Continuation 负责选择或恢复 Skill，Plugin 不识别原 Run。
- 仅保留协议/部署提供的 externalRequestId（缺失时为空）、Plugin 本地 responseChannelId、可信 source.peerId、Content-ID/slot 和当前 HTTP/2 stream 的内存 waiter。Plugin 不保存、不接收、不发送 Run ID 或 continuation state；responseObligationId 随 delivery.dispatch 到达时仅瞬时接收，不解释、不持久化、不转发、不回传。Host 创建该 ID，并依据 Host-owned pending continuation index 关联原 Run/generation。当前 HTTP callback 的 responseChannelId 与原 Run 的执行身份严格分离。

## 3. 非目标

- 不在 Plugin 中选择 Skill、执行业务逻辑或调用 Owner。
- 不完整解码 NAS/NGAP，不复制 Codec 实现。
- 不使用 Base64、Plugin 自有 Artifact 数据库或额外摘要机制；不实现 ca-host.artifact-store/v1 channel server，也不接收/生成 Host artifactRef。

## 4. 依赖与分阶段门槛（遵循 SR 管理规范 §6.1）

| 依赖类型 | 权威输入 | 适用门槛 |
|---|---|---|
| 设计 | F03 Plugin/IPC、F05 Artifact、F06 和 SR-017 源候选设计 | Plugin 只做 Event/Delivery/Staging；Skill 选择归 Core |
| 实施 | Plugin Package/IPC v1alpha1 已冻结规范、Plugin 自身独立 Go 进程 | 可用测试 Host 单独实施/验收 Plugin，无需 Next Skill/Owner；生产 UpdateSMContext 分类需消费 ca-client-tools#44 正式发布的 T0 classifier API |
| 模块验收 | SBI 原始 Create/Update/multipart/NAS 字节样本与测试 Host | Event mapping 可用 test double 验证；生产 0xC9/0xD1/0xD4 classifier 仅在 ca-client-tools#44 API 发布后验收，不得复制 parser 或用完整 DecodeNAS 替代 |
| 系统 OM | OM-01～03/05～08/14/15 与完整 Next Host + Mock AMF | 只能在组合环境验收；不代替 Plugin 单模块 AC |

**设计评审与实施 READY 独立判定**：本 SR 的功能职责、已知目标契约、失败路径和下面每项模块 AC 足够完整即可请求设计评审；不得要求“全部前置 SR VERIFIED”作为统一前置。实际实施按本次 Scope 逐阶段检查所消费的已发布能力；缺失时仅相应 AC 标记 BLOCKED/NOT_RUN，系统 EX/OM 不倒灌模块门禁。Owner/Provider/Compiler 的未知机器标识、Schema 和 API 只能由对应 Owner 正式发布，Harness 不得推测。新 Skill/Artifact/Runtime 接口只接受 CA-SL 1.6.0 / Capability-first，不提供旧版兼容。

## 5. 独立模块验收条件（正例、反例与证据）

| 模块 AC | 固定输入/操作 | 预期、诊断与隔离 |
|---|---|---|
| AC-009-01 | Plugin 启动、stdin/stdout IPC `host.initialize` → `plugin.ready`；Host 比对 Manifest 的 extensions 与 ready.payload.extensions（无独立 discovery 帧）；注入错版本、缺/多 extension、超帧 | 协议/Extension 集合全部匹配才注册，非法消息 fail-closed；`ingress.ack` 的安全 payload 单独在 AC-009-05 验证 |
| AC-009-02 | Create/Update 原样 OAS3 JSON 与 multipart；N1/N2 原始字节及可选 `n2.request`、`n2Ext1.request` 的 Content-ID/slot/mediaType/byteLength 正负例 | Event `eventId`/`ingressId` 与 JSON 引用/part 一致，bytes 逐位保留，`ingress.event.payload` 不携带 IPC `correlationId`；**新增 Ext1 子路径为设计范围，独立复评/实测前仍 NOT_RUN，不能追溯算进 Issue #116 固定批准** |
| AC-009-03 | Staging 仅可提交相对路径、声明 slot；绝对路径、路径穿越、artifactRef 反例 | 非法描述拒绝；Plugin 不直接创建 Host artifactRef/ArtifactStore |
| AC-009-04 | 按 F06 v0.3.7 §4.1/§13.7/§14 固定三个 normalized eventType、operationId、payload.request Schema、N1/N2 discriminator 与 Content-ID/slot；Event mapping 单测可注入 classifier test double，覆盖 N1 `0xC9`/`0xD1`/`0xD4`、N2 三种 response、分别/双路到达、冲突与错配；生产 classifier 必须使用 ca-client-tools#44 发布的窄 T0 API | Schema/映射/负例逻辑可独立实现；生产分类器绑定在 API package/signature/version 固定并发布前 BLOCKED_EXTERNAL_INPUT；不得在 Plugin 复制 parser、调用完整 DecodeNAS 或宣称生产 classifier PASS |
| AC-009-05 | `delivery.dispatch` 带 Host-owned opaque `responseObligationId`、Plugin-local `responseChannelId` 和 `deliveryId`；Plugin 只验 obligation 非空、不持久化，使用 live channel 回写，并在 `delivery.result` 精确回显 `deliveryId`。负例：空/缺 obligation、错误/关闭 channel、错误 eventType、错/重复 deliveryId、IPC 回复帧顶层 correlationId 不匹配、跨 stream 串单；`ingress.ack` payload 注入 runId/skillId/artifactRef/responseObligationId/deliveryId 或嵌套 error.details 必须拒绝 | **Host** 才有 obligation/channel/delivery 三元权威映射及有效性/过期/授权/去重责任；Plugin 无法判断一个非空但实际错误的 opaque obligation ID，故该类 Host 三元校验归 SR-010/011 且 NOT_RUN，**不得算 Plugin 模块 PASS**。Plugin 只证明 channel 路由、deliveryId 关联、ack 白名单、不泄漏、不生成或持久化 Run/obligation |
| AC-009-06 | 并发 HTTP/2 streams、不同 `eventId` / `responseChannelId` / `deliveryId` 和原始 fixture 交错回放；IPC 回复帧顶层 `correlationId` 只绑定其请求 `messageId` | 原始 bytes、Content-ID、slot、Event/channel/delivery 不串线；`ingress.event.payload` 不携带 `correlationId`，Plugin 不做 externalRequestId 去重或 Run 关联；不宣称 Next Host/OM E2E |

AC-009-01/02/03/05/06 仅依赖测试 Host、协议 fixture 和计数 peer。AC-009-04 的 Event mapping/Schema 子集可用 test double 独立实现；生产 classifier adapter 直接依赖 ca-client-tools#44。真实 Owner/Provider、Echo E2E 与隔离 NF 只影响系统组合验收。

### 5.1 AC-009-04 参数化分类用例与职责边界

本节是 AC-009-04 的**模块测试子例**，不是新增系统 OM 或 Run/Owner 实现范围。规范化事件字段以 F06 v0.3.7 §4.1 为唯一集成语义合同，插件包的 plugin.yaml / schemas 必须逐项实现该合同；3GPP OpenAPI 原始 YAML 不得修改、手写投影或补字段。operationId、payload.request、discriminator、Content-ID/slot 和三个 eventType 均按 F06 固定值验收，不允许 Harness 猜测。

| 输入（各含规范化 JSON/Content-ID 与原始字节 fixture） | 固定 eventType / discriminator | Plugin 应证明的分类与禁止事项 |
|---|---|---|
| `POST /sm-contexts` / Create（`SmContextCreateData` 原样 JSON，无 NAS operation discriminator） | `nsmf.create-sm-context`；payload.operationId=`PostSmContexts`，payload.request 为原样 `SmContextCreateData` JSON object，无 discriminator | 新 Create ingress；不选择 Skill、不创建/关联 Run；N1/N2 原始 part 仅按 Content-ID/slot 交 Host staging，保留原始 `requestType` 等 OpenAPI 字段、不补默认值 |
| `POST /sm-contexts/{smContextRef}/modify` + N1 5GSM `0xC9` | `nsmf.update-sm-context`；payload.operationId=`UpdateSmContext`，payload.discriminator.n1MessageType=`0xC9` | 新 UE Modify ingress；不选择 Modify Skill、不创建/关联 Run |
| 相同路径 + N1 5GSM `0xD1` | `nsmf.update-sm-context`；payload.operationId=`UpdateSmContext`，payload.discriminator.n1MessageType=`0xD1` | 新 UE-requested Release ingress（非 network-initiated ReleaseSMContext）；不调用 Release Owner |
| 相同路径 + N1 Release Complete `0xD4` | `nsmf.update-sm-context.continuation`；payload.discriminator.n1MessageType=`0xD4` | 既有 Release 的 N1 confirmation ingress；不把 `0xD4` 当作新的 Release 请求 |
| 相同路径 + N2 `PDU_RES_SETUP_RSP` | `nsmf.update-sm-context.continuation`；payload.discriminator.n2SmInfoType=`PDU_RES_SETUP_RSP` | 既有 Create 事务的 N2 completion ingress；不重新触发 Create |
| 相同路径 + N2 `PDU_RES_MOD_RSP` | `nsmf.update-sm-context.continuation`；payload.discriminator.n2SmInfoType=`PDU_RES_MOD_RSP` | 既有 Modify 事务的 N2 completion ingress；不重新触发 Modify |
| 相同路径 + N2 `PDU_RES_REL_RSP` | `nsmf.update-sm-context.continuation`；payload.discriminator.n2SmInfoType=`PDU_RES_REL_RSP` | 既有 Release 事务的 N2 completion ingress；不重新触发 Release |
| N1/N2 回调分别到达、交错到达；同 peer 多事务并发 | `nsmf.update-sm-context.continuation`；payload 保留 `smContextRef`、原始 UpdateSmContext JSON 和各自 discriminator；每次 ingress 有独立 responseChannelId | 保留可信 peer、externalRequestId（仅在协议/受信部署提供时）、Content-ID/slot 和原字节；Host 通过 Host-owned pending index 查找原 Run，Owner 再校验 generation/transaction；Plugin 不持有 Run/responseObligation |
| Create/Update 的可选 `n2SmInfo` / `n2SmInfoExt1` JSON 引用和 multipart part 组合 | `n2.request` / `n2Ext1.request` 仅在 JSON 实际引用时分别 staging；Create 无 NAS operation discriminator 合法 | 新增 Ext1/可选 N2 子项为设计覆盖，**NOT_RUN / 待独立复评**；不追溯计入 #116 的限定批准 |
| continuation 携带 `n2SmInfoExt1` | F06 v0.3.9 未冻结 continuation Ext1 slot，当前 profile 显式拒绝 | 子项 NOT_RUN；不能静默丢弃、猜测 `n2Ext1.confirmation` 或修改原版 YAML |
| 缺失或重复 Content-ID、part 错配、`n2SmInfoType` 与 N2 part 不符、截断/未知 5GSM、互相冲突的消息种类 | 拒绝错误输入，不发布新的可执行业务事件 | 不通过默补字段或业务解码修复输入 |

测试 Host 仅验证 Plugin 的三个规范化 eventType、payload schema、discriminator 投影、staging 和 IPC。N1 分类映射单测使用注入的 test double；生产实现必须在 ca-client-tools#44 发布精确 API 后绑定，不得自建 parser。Plugin 只为当前 HTTP/2 stream 保留内存 waiter；Host 创建本次 ingress 的 responseObligationId，并用 Host-owned pending continuation index 按可信 peer、operationId、smContextRef 和分类定位候选原 Run；若无匹配或多重匹配则拒绝，不新建 Run。Owner/Runtime 再验证原 Run 的 generation、releaseTxn、SUPI/PSI 与本路 originalInvocationId/Proof。**原 Run/generation/releaseTxn 的匹配、回调独立响应义务以及零重复 mutation** 属 F02/F04/F05、SR-010/011 的组合验收，不由 SR-009 单模块声称 PASS。Plugin 不接收或发送 Run ID；`responseObligationId` 作为 Host-owned 字段随 `delivery.dispatch` 到达时仅瞬时接收，不解释、不持久化、不转发、不回传，Delivery 写回仍由 Plugin-local `responseChannelId` 完成。

### 5.2 实现落点、运行和取证

- 目标实现：`cmd/openamsm-plugin（ca-openamsm-plugin）`；测试入口：`go test ./... -count=1 && go build ./cmd/openamsm-plugin`。若实现前目标仓文件/命令尚未存在，由具体实施 PR 在模块范围内创建并登记，**不得以不存在的脚本退出 0 或 0 discovered tests 作为 PASS**。
- 使用本 SR 明示的最小正负例与计数型测试 Provider/Mock；真实 Publisher、新 Compiler、Owner 收据、隔离环境等数据只从固定 SHA 的正式发布物读取。模拟输入能验证本地行为，但**不能替代**要求正式外部源的 AC。
- 每项 AC 单独记录受测代码 SHA、设计 Head、外部 Package/Schema/API 版本、命令、环境、测试数量、预期/实测、失败诊断与证据路径。未执行始终 NOT_RUN；输入缺失标记 BLOCKED；系统 EX/OM 必须用独立组合证据交付。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-openamsm-plugin |
| GitHub Issue | [ca-openamsm-plugin #2](https://github.com/odango-chan/ca-openamsm-plugin/issues/2) 已存在；只承接独立 Plugin 模块，不代表 Next/系统 E2E PASS |
| 实施 PR | [ca-openamsm-plugin #3](https://github.com/odango-chan/ca-openamsm-plugin/pull/3) OPEN、非 Draft、未合并；Head `161ffe6344baa325f004899718392dfa49cce97e` |
| Commit | 外部模块候选 `161ffe6344baa325f004899718392dfa49cce97e`，不在 Next 源码树 |
| 实施状态 | 外部模块候选已经提交，未合并；本版中央增量仍需复评；Next 集成 NOT_RUN |
| 验收证据 | 外部 Plugin module CI #46123933375 SUCCESS（受测 `161ffe6`）；不等于新增 Ext1、Host 三元义务、生产 classifier、Next Host 或系统验收 PASS；逐 AC 仍须独立定界 |

ca-openamsm-plugin PR #1 仍是设计候选（Head `5bb987aec6a643d453e7d2f111c04c4f02dbcd2f`）；PR #3 堆叠于该设计分支，是模块实现候选而非 Next 产品。其设计 pin 及系统 OAP gates 分组仍要由各自源仓收敛，不得直接以 #117 的较旧设计覆盖 #115。

### 6.1 Issue #116 固定批准与本版增量边界

[Issue #116](https://github.com/odango-chan/ca-agent-next/issues/116) 于旧固定 Next Head `ba5354c575394295cfa7a790922e02422b0c96f4` 给出限定 APPROVE_FOR_READY（0 P0 / 0 P1 / 11 P2），只覆盖 AC-009-01/02/03/05/06 已有子集及 AC-009-04 Event mapping/Schema/test-double。**不涵盖新增 Ext1 产品验收、Host 三元义务有效性、生产 T0 classifier**。PR #117 的独立复评对固定 Head `64ee3c7ccc005720c9752d91e803657e4e8bd06b` 给出 NEEDS_REVISION（4 P1 / 9 P2）；不吸收其 READY/Ext1 PASS/Plugin 不可实现的 Host 三元验证宣告。

#116 的 P2-01（Ext1）已在中央设计补全、产品子项 NOT_RUN；P2-02～06/09/10 的 ack/身份/握手、Create 分类、范围、T0 边界已在本版正文收敛；P2-07/08（外部 Plugin 文档 pin、模块与系统 OAP gate 分组）继续在目标仓追踪；P2-11 的索引版本/状态按 #115 当前快照维护。是否真正关闭各项，必须在本版独立复评后确认。

## 7. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：原模块设计已由独立 Review #73 在旧快照限定批准；本轮 F06 0.3.7 / SR-009 0.2.13 / Plugin PR #1 的增量修改待新的独立复评；生产 T0 classifier 依赖 ca-client-tools#44。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续发生语义变化时创建新的 SR 并引用本 SR，不覆盖历史要求。

### EC04 源仓验收入口

以 [F06 两端实施矩阵](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md#ec04-两端实现与逐例复核) 的 operationId、固定 OpenAPI、peer 输入与 MAS 作者契约制作 fixtures。先在 ca-openamsm-plugin 以独立测试 Host 核对双向 IPC、HTTP 与 staging，再在 ca-agent-next 接真实子进程。分别记录外部仓和中央仓的 SHA、命令、测试数、输入投影及结果。授权跨仓后按上述归属修改，不能只改 Host 使 fixture 通过。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史记录未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-009 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-009 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-009 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05/F06/Plugin IPC 设计版本，并将 Go Event/Delivery Plugin 的实施目标仓更正为 ca-openamsm-plugin | 设计仓与实际代码仓分离；防止将插件实现错误归入 Next Host | Issue #12 |
| 2026-11-25 | 0.1.4 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05 至 v0.4.0，并将 Event/Delivery Plugin 的 staging 职责与 Next Host ArtifactStore / Tool Channel 明确分离 | 防止把 Host 实现责任错误计入 ca-openamsm-plugin；Host 侧由 SR-010 追踪 | Issue #12；SR-009、SR-010 |
| 2026-11-25 | 0.1.5 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05/F06/Plugin IPC 设计依据至当前版本；同步冻结的 Host Artifact Store v1 与 Codec Consumer 分层状态 | 避免 SR-009 继续指向过期设计版本，确保 Plugin staging 和 Host→Tool Channel 的实施边界一致 | Issue #12；F05 v0.4.1；F06 v0.2.2；Plugin IPC v0.2.2 |
| 2026-11-25 | 0.1.6 | Codex / GPT-6 | §4～5 | Codex / GPT-6 · §4～5 清除自依赖，区分协议组件和组合验收 | 对齐当前架构与实施门禁 | Issue #12 SR-009 |
| 2026-11-26 | 0.1.7 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐外部实现输入及两端验收 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.8 | 未记录（历史资料未提供） | 历史记录未细分 | 同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.9 | Codex / GPT-6 | §4～5 | Codex / GPT-6，§4～5。分别登记设计输入、实施接入和验收依赖。 | 使 Harness 能按当前阶段判定启动与验收条件 | Issue #12、#21 |
| 2026-11-26 | 0.2.0 | GPT-6.2（ChatGPT） | 文档头部 | 将 Plugin IPC 设计依据更新至 v0.2.4 | 与当前 12 帧协议和 SR-003 使用同一冻结规范版本 | Issue #26 |
| 2026-11-26 | 0.2.1 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.2.2 | GPT-6（ChatGPT） | §4～§5 | 按治理 §6.1 拆分设计/实施/模块/系统依赖；补齐 AC-009-xx 正反验收 | 解除全局 VERIFIED 门槛与缺模块 AC 问题，避免 Harness 猜测/EX 倒灌 | Issue #12/#40；PR #46；SR 管理规范 §6.1 |
| 2026-11-26 | 0.2.3 | GPT-6（ChatGPT） | 文档头、设计依据 | 同步本次 1.6.0 实质整改后的权威 Feature/Compiler 文档版本 | 保证 SR 新旧规范引用与固定审核 Head 一致 | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.2.4 | Codex / GPT-6 | 设计依据、§5 | 标明测试 Host 可覆盖的模块范围 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.5 | Codex / GPT-6 | 评审状态 | 登记第二轮限定范围及外部依赖 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.6 | GPT-6（ChatGPT） | §2、§5～5.2、设计依据、修订记录 | 扩展 AC-009-04 到 0xD4 与三种 N2 completion；模块验证和 Host Continuation/Owner 验证分离；按版本整理修订记录 | 关闭合法回调被误拒/误发新 mutation 的设计缺口，保持既定 AC 数量与实施非目标 | Issue #12；PR #46；SR-009；F06 §EC04 |
| 2026-11-27 | 0.2.7 | GPT-6（ChatGPT） | §2、§5～5.2、设计依据、修订记录 | 移除 Plugin 对 Run/responseObligation/continuation state 的持有要求；引用 F06 冻结的三个 Event type、payload.request、discriminator、Content-ID/slot 与 Host-owned continuation 关联规则 | 处理独立模型 Review #6082541121 的 P1 R3-SR009-01/02，避免 IPC 违反 Host-only Run 边界和实现者猜测 Event 契约 | Issue #12；PR #46；F06 v0.3.3；Review #6082541121 |
| 2026-11-27 | 0.2.8 | Codex / GPT-6 | 文档头 | 登记模块设计已认可，待目标仓实施交接及 AC 范围 | 按单项独立评审推进 | Issue #12、#73；PR #46 |
| 2026-11-28 | 0.2.9 | GPT-6（ChatGPT） | §2、AC-009-04/05、§5.1、修订记录 | 修正 N1 5GSM EPD/Message Type 字节偏移与截断验收；对齐 Host-owned responseObligationId 的瞬时接收与不回传边界 | 防止合法 NAS 分类失败或因把“非所有权”误写为“不能接收”而拒绝合法 Delivery | Issue #12；PR #46；F06 v0.3.3；Review #6095143611 |
| 2026-11-28 | 0.2.10 | GPT-6（ChatGPT） | §5.1、修订记录 | 清除 §5.1 对 responseObligationId“不得接收”的残留表述，与 dispatch Host-owned 瞬时接收规则统一 | 防止同一 SR 内一处允许接收、一处禁止接收，导致合法 Delivery 被实现拒绝 | Issue #12；PR #46；F06 v0.3.3；Review #6095143611 |
| 2026-11-28 | 0.2.11 | GPT-6.2（ChatGPT） | §2、设计依据、修订记录 | 对齐 IPC v0.2.7，明确 responseObligationId 仅随 delivery.dispatch 瞬时接收，responseChannelId 负责本地 HTTP/2 stream 写回 | 将 SR-009 模块边界与公共 IPC 契约保持一致，避免将非所有权误解为不可接收 | Issue #12；PR #46；IPC v0.2.7；Review #6095143611 |
| 2026-11-28 | 0.2.12 | GLM-5.3（DeepSeek Harness） | §5.1、修订记录 | 为 AC-009-04 §5.1 参数化用例表补 `nsmf.create-sm-context` Create 正例行 | 关闭首轮 R1-SR009-02 的 Create 用例缺口，使三个 eventType 均有正例 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-28 | 0.2.13 | GPT-6.2（ChatGPT） | 文档头、§2、§4～6、修订记录 | 刷新 F05/F06/IPC 权威版本；将 AC-009-05 收窄到 responseChannel/delivery 映射，externalRequestId 去重明确归 Host；将 AC-009-04 生产 classifier 绑定列为 ca-client-tools#44 直接外部依赖，并允许 test double 仅验证 Event mapping；等待当前快照独立增量复评后再创建实施 Issue | 消除 Plugin/Host 重试身份边界和 NAS classifier 所有权歧义，避免 Harness 猜测 API 或复制 parser | Issue #12；Review #73；F05 v0.4.10；F06 v0.3.7；IPC v0.2.7；ca-client-tools#44；PR #115 |
| 2026-11-28 | 0.2.15 | GPT-6（ChatGPT） | 文档头、§5～6、修订记录 | 只选择性吸收 #117 的明确设计修订，不采用其越权 READY/Ext1 PASS/Plugin 可验证 Host 三元身份的宣告；固定 #116 原批准范围、Host 三元所有权与外部 Plugin #3 候选证据 | 消除 #116 P2-01～06/09/10 及 #117 三类 P1 的中央语义冲突；P2-07/08 外部待复核，最终需独立全量复评 | Issue #50/#116；PR #115/#117；ca-openamsm-plugin#3 |
