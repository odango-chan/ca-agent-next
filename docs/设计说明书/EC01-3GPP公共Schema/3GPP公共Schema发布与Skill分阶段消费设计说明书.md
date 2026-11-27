# 3GPP 公共 Schema 发布与 Skill 分阶段消费设计说明书

> 文档类型：功能设计说明书（EC01.3GPP；涉及 EC03/F02/F06/F08/F09）  
> 文档版本：0.1.0  
> 修订日期：2026-11-27  
> 状态：DRAFT / REVIEW_REQUESTED；仅中央设计候选，外部 Publisher、Compiler、Provider、Bundle 产品均未据本文验收  
> 上游需求：[IR-009](../../IR/IR%20总登记册.md#ir-009) · [Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)  
> 实施分解：[SR-031](../../SR/SR-031-3GPP公共Schema-only-Publisher.md)、[SR-026](../../SR/SR-026-Codec公开工具发布.md)、[SR-010](../../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md)  
> 全局评审范围：继承仓根 Agent.md 的 review_scope；本文 Demo / Development，不含 Production Qualification

## 1. 问题、目标与结论

F06 Create 既要求 Skill 在选择前取得 N1 NAS 中的 requestedPduSessionType / requestedSscMode，又规定只有选定 Skill 的 Procedure 可调用 Codec。这是阶段依赖环，不得以在 Host 或 Event Plugin 中偷偷完整解码、合成默认字段或允许 when 调 Tool 来绕过。

**决策：分离两类标准化输入**：① *选择输入*（Plugin 已验证/归一化的 Nsmf SBI 元数据 + 最小安全 discriminator + Host Artifact 引用）用于 Skill-owned `requestSchema` 和 `when`；② *执行输入*（被选中 Skill 经普通 Codec READ Capability 解出的 3GPP 结构化字段）用于 Procedure 的显式参数、Observation / Owner Action。所有共享 3GPP 类型由 **独立公共 Schema-only Interface Package** 发布；不把完整 3GPP JSON/OpenAPI/multipart/ASN.1 搬进 `requestSchema`。

本决策不改变 CA-SL **1.6.0 ONLY**、Skill-facing Capability、Capability↔Callable 双向一对一、唯一 Plugin Manager / Runtime Action Boundary、Host-owned ArtifactStore、Owner 权威状态与 Receipt/Commit Proof；历史 v1alpha5 只读，不提供兼容映射。

## 2. 来源、标准与固定基线

| 协议域 | 上游权威 | 本设计消费范围 | 出处/版本证据与缺口 |
|---|---|---|---|
| SBI Nsmf_PDUSession | 3GPP TS 29.502；OpenAPI `TS29502_Nsmf_PDUSession.yaml`，关联 29.571 CommonData | SBI JSON、operationId、Content-ID、N1/N2 attachment 类型和业务可见标准字段 | Demo 固定现存 OpenAMSM 源 `env-openamsm@dc83ccbf` 的 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`；正式 Producer 必须固定完整 SHA、blob identity、依赖 OpenAPI 文件闭包、对应 3GPP 版本 |
| N1 NAS 5GSM | 3GPP TS 24.501 | 首批 0xD1 Release Request；扩充 Create Establishment Request、0xC9 Modification Request 的逐条消息投影 | 可复验历史候选 `ca-client-tools` PR #39 `eb1169fe` 的 `protocol/codec/nas.go` 与 `codec_test.go`；精确支持集合与各 fixture 应由 Provider Owner 签认；不得由此推断全量支持 |
| N2 NGAP | 3GPP TS 38.413；对应 N2 SM information type / transfer 还需匹配 3GPP TS 38.413 及其适用的 29.502/38.413 transfer 定义 | PDU Resource Setup / Modify / Release response 的**受验证子集**和 Run completion correlation | 未冻结的字段与 ASN.1/PER 不准臆测；第一批没有 NGAP 公共 Decode 验收 |
| Agent / CA-SL 语义 | [CA-SL 1.6.0](../../规范/CA-SL%201.6.0完整语言规范.md)、F02、F03.05、F05、F06、F08 | 严格 Schema 闭包、Capability Binding、Tool Action、Event 先行验证 | 完整语言机器 ID / Compiler 1.6.0 API / Schema-only Package 仍待正式 Publisher 冻结 |

**标准源与产品包不能混为一谈**：3GPP 原始 OpenAPI 常含 `#/components`、`oneOf` 等当前 CA-SL 1.6.0 G.4 不支持的 JSON Schema 结构；NAS/NGAP 更不是 JSON Schema。Producer 发布的是从**固定标准源**导出的、声明每个字段来源和无损/有损投影规则的有限型公共契约，不能声称重发了 3GPP 官方原版 Schema。

## 3. 发布物与所有权

| 产物 | 生产者/目标仓 | 必需导出及消费 | 明确不拥有 |
|---|---|---|---|
| **3GPP Common Schema-only Interface Package** | **ca-skills（EC01 / SR-031）**；Next 中央定义与审计 | 源标准锁清单、Package ID / 数字 SemVer / 1.6.0 languageTarget、显式 Schema exports（闭合 JSON Schema $id、完整 ref closure、typed profiles、fixture+sourceMap）、0 Capability、0 Callable；供 Skill 作者/Compiler/Studio、Provider Interface 引用 | 可执行 Codec、网络、Owner、Host Context、消息原始字节 |
| Plugin Event Schema | EC04 ca-openamsm-plugin 发布输入；Next Host 校验 | 规范化 SBI operation、业务元数据、仅已证实的最小 NAS discriminator；Host 另行授权原始 Artifact 引用 | Skill 选择、完整 NAS/NGAP 解码 |
| Skill-owned `Contract.requestSchema` | ca-skills 业务 Skill 作者 + Compiler | 根必须在本 Skill `assurance/schemas/`；仅选择前可验证字段；必要时用精确依赖 alias / $id 引用 3GPP Common 类型；验证后供 F02 `when` | 完整 3GPP multipart、解码后才可获得的请求字段、Host Context |
| Codec Tool Interface Package | ca-client-tools（EC03 / SR-026） | Capability↔Callable 1:1 的 READ；输入 artifactRef/slot/mediaType/message profile，输出 Schema 固定为与 3GPP Common Schema 同源、同版本、类型可校验的 JSON 投影或新 Artifact；自带依赖快照 | 公共 3GPP 类型原始定义、Owner State、Commit Proof、独立 Codec Manager |
| Host Context Schema-only Package | ca-agent-demo / SR-030 | 仅供 `Contract.contexts` 引用的独立 Host-owned Schema exports；0 Capability / 0 Callable | 3GPP Common Schema、Codec |
| Runtime Artifact / Bundle | ca-skill-compiler / ca-skills SR-013、SR-027 | Skill-owned Request 根、3GPP Common Schema 闭包、Codec 的有效 Input/Output Schema、Capability Binding 和依赖 identity，固定到不可变构建快照 | 源标准自动抓取、运行期构建或回退 |

**公共 Schema 的具体机器 ID、Package 版本与导出文件名本设计不发明**；由 SR-031 在签认的 ca-skills 正式 Publisher 产物中一次冻结。Provider Owner 在 SR-026 使用同一发布快照标注输出与 profile，不能把私有 Go struct 或自由 JSON 当作公共 Schema。Publisher 不能强迫含 0 Capability 的包虚构 Tool。

## 4. 分阶段数据流与最小契约

| 阶段 | 消费输入 | 明确输出 | 失败与副作用 |
|---|---|---|---|
| T0：EC04 ingress | Nsmf HTTP path / operationId、SBI JSON、multipart Content-ID、原始 N1/N2 | 已验证 Event identity、已证实分类与规范化字段、Host staged raw bytes | malformed JSON/part/Content-ID/mismatch 拒绝；**无 Owner Mutation** |
| T1：F02 选择 | Event Schema + Skill-owned `requestSchema` + 可选 `when` | 唯一候选 Skill（或精确候选集）、原 Run 的 continuation | 不调用 Codec；`requestSchema` 不包含须由 Codec 解出的字段；fail-closed，无候选不 dispatch |
| T2：Procedure READ | 已选择 Skill 的 Capability Grant、绑定 artifactRef/slot | Codec READ 输出的 typed 3GPP JSON / ref，验证 output Schema，原始字节不变 | Capability 缺失、跨 Run/slot、非法消息、输出 Schema 不匹配均失败；READ 不生成 Owner mutation/Proof |
| T3：Procedure business | 已验证 Codec fields + 已发布 Owner/Host Context + 显式 arguments | Owner READ/MUTATION、Receipt/Commit Proof / Observation | 不凭模型文本、Codec 输出或 HTTP 2xx 宣告 COMMITTED |
| T4：Continuation | 原 Run identity、Wait correlation、合法 N1/N2 completion | 恢复原 Run，不重新选择或求值 when | 迟到、重复、错误代际不得新建业务 Run/产生重复 mutation |

**No-decode 路径是有效路径**：不需要 N1/N2 结构字段的 Skill 不声明 Codec Capability，也不得为其强制引入 Codec 或其结果。只有特定 Procedure 引用 Codec 时才要求其正式发布与 Scope。

## 5. Create / Modify / Release 字段来源与阶段

| 场景 | T0/T1 可用于 Skill 选择（必须由实际 ingress fixture 证明） | T2 后方可供 Procedure 使用 | 约束与失败判据 |
|---|---|---|---|
| Create `PostSmContexts` | operation / Event type、经 OpenAPI 校验的 SBI JSON 字段（例如 DNN、S-NSSAI、serving PLMN，**仅实际请求已携带时**）、N1 slot 存在性 | N1 解出的 PSI/PTI、PDU Session Type、SSC mode、对应已资格化 NAS 信息 | **不得要求** T1 的 `requestedPduSessionType` / `requestedSscMode` 为 NAS 解码值；T2 再验证 N1 与 SBI JSON PSI / QoS / session type 一致性；字段不在上游不得合成 |
| Modify `UpdateSmContext` + NAS 0xC9 | 已验证 path/context identity、SBI 元数据、最小 0xC9 discriminator / event.type、N1 ref | 修改请求 NAS 内容；若 QoS GBR/MBR 必须由已发布 Owner/Codec READ 或可信输入显式提供，不由模型猜测 | 非法/未知 NAS 不可默认为 Modify；没有已资格化输出时该业务子路径 BLOCKED |
| UE Release `UpdateSmContext` + NAS 0xD1 | 最小 discriminator、已有资源 identity、N1 ref、SBI 元数据 | `PDUSessRelReq` PSI/PTI 等指定 Release Request 输出 | 第一批 SR-026 仅验证固定 0xD1 消息；不自动宣称 0xC9/Establishment 可用 |
| `UpdateSmContext` + 0xD4 / N2 Setup/Modify/Release response | 仅用于旧 Run 的 correlation / Wait；不是新业务 Skill 选择输入 | 按 Wait 所声明的原事务读取受验证 completion evidence | 禁止当作新 Release 请求；generation/PTI/PSI 与原 Run、N2 message type 不匹配必须拒绝 |
| `ReleaseSmContext` HTTP | HTTP operation identity 与 SBI JSON 元数据 | 按独立支持范围执行，而非假定 0xD1 路径 | 与 UE-initiated 0xD1 区分；尚未支持的路径显式拒绝 |

F06 历史 Create Contract 在 T1 就要求 `pti`、`requestedPduSessionType`、`requestedSscMode` 等字段，须按本表重写**新的 CA-SL 1.6.0** 作者源。字段转移不等于删除业务校验；必须在 T2/T3 完成，并在 F02 的早期 Schema 与 Procedure 输入 Schema 分别取证。所有 `when` 只读取 T1；不能引用 `codec.result` 或 Tool/Context/Observation。

## 6. Schema 生成与链接约束（不能留给 Harness 猜）

1. **Source Lock**：每个类型记录标准规范号/版本、源库 commit/blob、上游对象路径与字段级 `sourceMap`；同时标注该投影是否是标准原名、归一化命名或有损映射。多版本不能隐式合并。
2. **G.4 受限 Profile**：仅使用 [CA-SL 1.6.0 §12](../../规范/CA-SL%201.6.0完整语言规范.md#12-request-schema--cel-的-json-schema-profile) 已批准的 JSON Schema Draft 2020-12 有限子集；不输出 `$defs`、`#/components`、`oneOf`、`format`、`pattern`、tuple 或动态引用。所有递归/多态源类型必须显式分拆为**不同已声明类型或固定枚举的关闭对象**，缺可表达性则拒绝发布该类型，不可静默丢字段。
3. **Root / Closure**：`requestSchema` 根仍由 Skill 自有，根 `additionalProperties=false`；精确 `$ref` 可以引用声明的独立 3GPP Schema-only 依赖导出 $id，Compiler 固定完整传递闭包和依赖快照。Host Context 仍只通过 `Contract.contexts` 引用，不因本设计引入全局类型捷径。
4. **输出匹配**：Codec 的公共 Result Schema 是 Provider Package 的正式 Output Schema，字段类型与公共 3GPP Schema 的固定 $id / source revision 一致；运行期只按已发布 Output Schema 验证，绝不临时推断字段。未知扩展、错消息类型、缺字段、错误 enum/nullability 不得被解释成成功。
5. **发布原子性**：ca-skills Publisher 与 ca-client-tools Provider 分别发布；Compiler/Bundle 引用固定 Package 版本、export identity 和 snapshot digest，禁止运行期解析 `latest`、自动下载或混合 Schema 版本。Schema-only 不计入 Capability/Callable 基数，Provider 仍保持原设计查询 2/2 + Codec 1/1 = 3/3。
6. **Studio**：Schema-only 依赖出现在依赖/Schema 视图，提供类型补全与 SourcePath 诊断；不能被渲染为 Tool/Operation/Capability，不能给 Skill Grant 或影响 Callable Scope。
7. **发布机器字段缺失**：若 1.6.0 Package Schema / Compiler Build DTO 尚未正式冻结，`packageId`、`schemaId`、`languageTarget` 具体值保留 `BLOCKED_EXTERNAL_INPUT`，上述结构是契约要求，不是已发布的 JSON/Manifest 示例。

## 7. 模块验收与 Golden

| ID | 测试输入 / 固定断言 | 退出条件 |
|---|---|---|
| DS-3GPP-01 | 同一指定 29.502 OpenAPI 与 29.571 闭包重建公共 SBI 类型；两次构建输出等价，附字段 sourceMap 与版本 | 无未知 G.4 关键字，所有外部 $ref 精确、闭合、来源可审计 |
| DS-3GPP-02 | Skill-owned 选择 Schema 引用公共类型；故意给 T1 注入 NAS-only `requestedSscMode` | 正例可 Link；缺请求字段的错误输入被拒，T1 **不**隐式 Decode / default |
| DS-3GPP-03 | 0xD1 `2e 05 01 d1` → `PDUSessRelReq` PSI=5/PTI=1；截断三 octets 与 0xD4 作 Release Request 负例 | 经真实发布 Provider Codec READ 一次调用、JSON Schema 验证、原字节不变；0xD4 不作该消息合法结果 |
| DS-3GPP-04 | Create NAS 字段在 T1 缺席、T2 经已发布 Codec 才出现；SBI 与 N1 PSI 冲突 | T1 不因晚到字段失配；T2 校验并拒绝冲突，无 Owner mutation |
| DS-3GPP-05 | Modify 0xC9、0xD4 Completion、N2 三类；错误 generation/PTI/PSI | 0xC9 选 Modify；0xD4/N2 只续跑；不完整/错误证据不创建新 Run/重复 mutation |
| DS-3GPP-06 | 重复 Schema ID、不同版本混链、Schema-only 0/0、Provider 3/3、非法解码输出 | 必须拒绝漂移/歧义；合法零 Capability roots 仍被 Link，Codec READ 不授予 Owner MUTATION |
| DS-3GPP-07 | 无需 Codec 的 Skill，或缺 Codec 发布的必需子流程 | 前者 zero Codec IPC 可执行，后者仅对应子流程 BLOCKED；系统 E2E 不得冒充 PASS |

所有 Product AC 必须记录目标仓 SHA、设计 SHA、测试环境、fixture bytes、命令、发现数、期望/实测与发布资产 identity。现在全部 `NOT_RUN`；依赖尚未发布的标 `BLOCKED`。新作者源和 Bundle 必须从 CA-SL 1.6.0 重新生成，不兼容旧文件。

## 8. 执行与评审门禁 / 非目标

实施按 [SR-031](../../SR/SR-031-3GPP公共Schema-only-Publisher.md)（共享 Schema）→ [SR-026](../../SR/SR-026-Codec公开工具发布.md)（公开 Codec Tool / 扩展消息）→ SR-010（Runtime/Host 消费）→ SR-027（Skill Bundle）→ SR-011（组合 E2E）分阶段走**独立实施 Issue**。SR-009 的 Event Plugin 与 SR-010 的 Host Artifact Channel 可按直接依赖单独推进，不等待本设计的全部 Release。

在 Publisher 冻结 Package/Schema ID、版本、字段、Golden 和完整 Compiler 接口前，**不得**发跨仓产品实施 Goal 要求 DeepSeek Harness 猜测。可以开展独立中央设计评审，不把标准文本分析或 PR #39 库测试当成已发布 Codec。

不新增第二 Manager、Host/Plugin 内完整 Codec、NAS/NGAP 全覆盖承诺、通用 Schema Registry 服务、生产级签名/Trust Registry/HA/TLS/OAuth；不重写已完成的 Create→Modify→Release Demo 业务目标，仅修正新 1.6.0 的类型与来源闭环。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 新增 3GPP 公共 Schema Producer、T0～T4 阶段、字段来源矩阵、跨仓身份/闭包/验收与未发布门禁 | 关闭 F06 Create 选 Skill 前需 NAS 解码的依赖环，避免工具与 Schema 职责混淆 | IR-009；Issue #47；SR-031/026/010 |
