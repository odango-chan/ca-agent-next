# 3GPP 公共 OpenAPI 原版引用与 Skill 分阶段消费设计说明书

> 文档类型：功能设计说明书（EC01.3GPP；关联 EC03/F02/F06/F08/F09）
> 文档版本：0.3.3
> 修订日期：2026-11-27
> 状态：DRAFT / REVIEW_REQUESTED；原版 Source Bundle、OAS3 Consumer、Compiler 外部引用与 Codec 产品均未完成产品验收
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文非目标：生产级资格、全量 NAS/NGAP、修改上游 YAML、重定义 3GPP 标准、旧 CA-SL 兼容
> 上游：[IR-009](../../IR/IR%20总登记册.md#ir-009)、[Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)
> SR：[SR-031](../../SR/SR-031-3GPP公共Schema-only-Publisher.md)、[SR-010](../../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md)、[SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)、[SR-026](../../SR/SR-026-Codec公开工具发布.md)

## 1. 不可变原则与本轮裁决

1. 唯一来源是 OpenAMSM 实际支持 / 构建使用的协议源快照；版本由文件规范标记和 OpenAMSM 构建 / 代码证据确认，不能自行选择 latest 或混合 commit。
2. 原版 OpenAPI YAML 原样代发布：字段、类型、注释、key 顺序、空白、换行、编码、`$ref`、路径全部不改。Publisher 只在原件树外增加 Source Lock / manifest / 测试证据。
3. 采用原生 OpenAPI 3.0 消费，不强制 Adapter / Projection。OAS 3.0 Schema Object 与 CA-SL 1.6.0 G.4 是不同 dialect；G.4 限制不能成为修改原件或另造影子标准的理由。
4. Skill-owned `requestSchema` 根和本地 Schema 节点仍遵循 G.4；在显式声明并 pin OpenAMSM Source Bundle 后，可以直接引用原版 OAS 3.0 `components/schemas`。外部目标按 OAS3 Schema Object 语义解析，不能转换成 G.4 或静默丢弃关键字。wire 表示由 ca-skills / Compiler Owner 在正式 1.6.0 Schema / Golden 冻结。
5. NAS / NGAP 不等于 SBI OpenAPI。TS 29.502 binary part 只定义原始 N1/N2 transport、MIME / Content-ID，不定义 NAS IE / NGAP ASN.1 解码字段。Result Schema 必须由 Codec Provider 按 OpenAMSM 协议源和已资格化消息 Profile 发布。
6. 全系统仍为 CA-SL 1.6.0 ONLY、Capability↔Callable 双向一对一、唯一 Plugin Manager、Host-owned ArtifactStore、Owner 权威 Receipt / Commit Proof；不提供旧版兼容。

本裁决取代“必须先发布 G.4 Adapter 才能引用原版 OpenAPI 类型”的旧假设。只有未来出现可复现的 OAS3 消费阻断，才另开 Issue 提出最小方案；当前不把 Adapter 作为产品路径或前置条件。

## 2. 已核实的 OpenAMSM 源快照

截至 2026-11-27，`env-openamsm/main` = `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`。这是已观察快照，正式发行仍需 OpenAMSM Owner 签认。

| 用途 | 原始路径 | 3GPP 标准版本 | OpenAPI / 源版本与 blob |
|---|---|---|---|
| SBI Nsmf | `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml` | TS 29.502 V19.5.0 | OpenAPI 3.0.0；`info.version: 1.4.0`；`3572be0315a782691ce8b5546b7bc1d5b22fcd64` |
| Common Data | `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29571_CommonData.yaml` | TS 29.571 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.6.1`；`e09e9bb4aef0cf24aee008da06b1ef0023475efb` |
| NRF NFManagement | `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29510_Nnrf_NFManagement.yaml` | TS 29.510 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.4.1`；`59d115ee6c7f4854aa123ad0c4ff7112fa879d73` |
| AMF Communication | `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29518_Namf_Communication.yaml` | TS 29.518 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.4.1`；`b695453dad07d1dd7b0d9a5ee28a80a71fee805d` |
| NAS 5GSM | `upstream/openamsm/lib/nas/5gs/support/r19.6.2/24501-j62-ch8-ch9.docx` | TS 24.501 R19.6.2 | `82dcc4c97436ec85c3da14bb35f022385c9484b6` |
| NGAP ASN.1 | `upstream/openamsm/lib/asn1c/support/ngap-r19.2.0/38413-j20.asn` | TS 38.413 R19.2.0 | `3fa6da460a85bb2054316afec3da37d2b7043fe0` |

OpenAPI `info.version` 是 API 文档版本，不是 3GPP TS 版本。TS 29.571 externalDocs 标记 V19.6.0，`info.version` 为 1.6.1。当前 Plugin ingress 选定面固定为 `PostSmContexts.requestBody` → `multipart/related` → `jsonData` → `#/components/schemas/SmContextCreateData`。在 source commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 上静态递归遍历得到 4 份原版 YAML、102 个可达 Schema Component；未发现选定闭包内未解析目标或循环。该计数是固定快照的来源审计结果，仍需 Publisher / Compiler Golden 验证，不代表产品验收。闭包文件为 TS 29.502、TS 29.571、TS 29.510 NFManagement、TS 29.518 Namf Communication；不默认复制全部 472 份。TS 29.502 根文件含其他 operation 的外部引用，消费端必须先定位选定 surface，再 lazy resolve 其可达引用；不得全文件 eager resolve。若以后消费 response / callback，须将其作为额外选定根加入 Lock。NAS README 说明 NAS C files 从 TS 24.501 Word 源生成；NGAP C files 由 ASN.1 源生成。二者不是 OpenAPI YAML。

## 3. 工件与所有权

| 工件 | Owner | 责任 |
|---|---|---|
| OpenAPI Source Bundle | ca-skills / SR-031 | 原版 OAS3 YAML + 可达 refs，byte-for-byte 不变；无 Capability / Callable |
| SBI Ingress Consumer | Plugin / SR-010 | 原生解析 method/path/operationId、requestBody、multipart、JSON / binary parts、media type、Content-ID；只做 ingress 验证和原始 bytes staging |
| Compiler OAS3 Resolver | Compiler / SR-013 | 对 Skill-owned G.4 Request 根中的精确外部 `components/schemas` 引用做 dialect-aware Link / Validate / Lock |
| Codec READ + Output Schema | ca-client-tools / SR-026 | 按授权 artifact slot 解码已资格化 NAS/NGAP Profile，发布 Provider Output Schema |
| Skill Request / Host Context | ca-skills / SR-029、SR-030 | Request 根归 Skill；Host Context 只经 `Contract.contexts`；Codec Result 只在 Procedure 执行期可用 |

Source Bundle 不是 Interface Package，不授予 Tool Scope。SR-030 Host Context Schema-only Package 与 Source Bundle 不同，仍只经 `Contract.contexts`。

## 4. 原生 OpenAPI 3.0 引用规则

TS 29.502 `PostSmContexts` 的选定 ingress surface 为 operation 的 `requestBody`：`multipart/related` 中 `jsonData` 指向 `#/components/schemas/SmContextCreateData`。该组件不只引用 TS 29.571 CommonData，还引用 TS 29.510 NFManagement 的 `ServiceName` / `WAgfInfo` / `TngfInfo` / `TwifInfo`，以及 TS 29.518 Namf Communication 的 `NgRanTargetId` / `SbiBindingLevel`；因此该入口完整可达闭包为 §2 所列四份原版 YAML。binary slots 为 `binaryDataN1SmMessage`（`application/vnd.3gpp.5gnas`）、`binaryDataN2SmInformation` 与 `binaryDataN2SmInformationExt1`（`application/vnd.3gpp.ngap`）；encoding 声明 JSON `application/json` 与 binary part 的 `Content-Id`。

Plugin 按 OAS3 原件解析选定 operation / requestBody / content / multipart encoding / part Schema / media type / Content-ID，不能把 binary part 当作已解码字段。原始 TS 29.502 YAML 中其他 operation 的 refs 不属于当前选定闭包；Plugin / Compiler 必须 selection-scoped lazy resolve，不得因未选定 refs 不在 Bundle 中而失败。相对 `$ref` 以引用文件为基准；`../` 只有在规范化后仍位于锁定 Source Root 内才允许，逃出 Source Root 必须拒绝。

3GPP CommonData 的 `RefToBinaryData.contentId` 表示被引用 binary body part 的 `Content-ID` header 值。对 `PostSmContexts` 必须精确关联：`jsonData.n1SmMsg.contentId` ↔ `binaryDataN1SmMessage`；`jsonData.n2SmInfo.contentId` ↔ `binaryDataN2SmInformation`；`jsonData.n2SmInfoExt1.contentId` ↔ `binaryDataN2SmInformationExt1`。每个已声明引用必须且只能命中对应 slot；Content-ID 在 parts 间唯一；引用目标缺失、重复 ID、错槽或媒体类型不符均 fail-closed。未被 JSON 引用的 part 不得交给 Codec；额外或未引用 part 的拒绝 / 忽略由选定 ingress profile 明确规定，不能由 Schema 隐含推断。Header 名按 MIME 规则识别，Content-ID 值按标准 MIME 解析结果精确比较，不做自定义大小写转换或字符串裁剪。

Skill-owned `requestSchema` 根仍是本地 G.4 闭合对象。它可以在显式 pin Source Bundle dependency 后直接引用原版 OAS3 `components/schemas`，并保留 `nullable`、`oneOf`、`anyOf`、`allOf`、`pattern`、`additionalProperties`、`format` 等 OAS3 语义；不做 Adapter / Projection。只允许 pin 后的 Schema Component，不允许任意 URL、dynamic latest、Path Item / Operation / RequestBody / Response 或 Bundle 外文件。Compiler / Host 不支持可达语义时必须 fail-closed，不得静默忽略或产生部分 Artifact。

CEL 类型推导对 `anyOf` / `oneOf` 只无条件暴露在每个可满足分支中均声明、均列入 `required` 且类型一致的字段；其他字段仅在 CEL 类型系统显式支持 optional 时按 optional 暴露，否则不得无条件访问。`allOf` 按交集合并约束并合并 required 集合；nullable 的 Null 与 Missing 区分。dependency alias、relative path、JSON Pointer、Source Bundle identity 和 Lock wire 字段必须由 ca-skills / Compiler Owner 在正式 1.6.0 Schema / Golden 冻结；本设计不预造机器字段名。

## 5. T0～T4 分阶段边界

| 阶段 | 输入 / 责任 | 约束 |
|---|---|---|
| T0 Plugin | OAS3 operation / multipart / Content-ID；验证 JSON / binary parts，保存原始 N1/N2；最小 0xC9 / 0xD1 / 0xD4 分类 | 不完整解码；错误 fail-closed，无 Owner mutation |
| T1 Skill 选择 | 到场 SBI JSON / 归一化 Event、Skill-owned Request、when | 不调用 Codec；NAS-only 字段不能成为必填 |
| T2 Procedure | 已发布 Codec READ、授权 artifactRef/slot、Provider Output Schema | 只解码资格化 Profile；Output Schema 验证后 SourcePath 才可用；原 bytes 保留 |
| T3 Owner / Observation | 有效 T2 Result + Host Context / Owner READ | Owner Receipt / Proof 是 Commit 判据，Codec JSON 不是 Proof |
| T4 Continuation | 原 Run generation / identity 与合法 N1/N2 completion | 续跑原 Run，不重新选择 Skill 或重算 when |

| 入口 | T1 可用 | T2 才可用 |
|---|---|---|
| Create `PostSmContexts` | 实际 jsonData 字段（以 fixture 确认）+ N1 slot 引用 | N1 PSI / PTI / PDU Session Type / SSC mode |
| Modify / 0xC9 | SBI metadata、resource / original request identity、最小分类 | 修改内容 / QoS，取决于已资格化 Codec / Owner READ |
| UE Release / 0xD1 | SBI resource、0xD1 discriminator、N1 ref | Release Request PSI / PTI |
| 0xD4 / N2 completion | 原 Run correlation | 相应完成证据 |

T1 不得要求 NAS-only PDU Session Type / SSC mode；T2 必须校验 SBI / N1 冲突，禁止默认值补造。0xD4 / N2 completion 只续跑原 Run，不产生新候选。

## 6. NAS / NGAP Codec Output

Codec Result 由 SR-026 Provider 发布，不由 SBI Source Bundle 代替。NAS 依据 TS 24.501 R19.6.2 Word 源及 OpenAMSM 生成代码；NGAP 依据 TS 38.413 R19.2.0 ASN.1 及 asn1c 生成代码。Provider Output Schema 必须与真实 Decoder 逐字段一致，固定 message Profile、版本、slot、字段映射、unknown / extension 行为和 Golden。

ca-client-tools PR #39 的 Go 内部解码向量 / 方法不等于公开 Provider Capability / Callable / Output Schema；0xD1 首批资格不能外推到 0xC1 Establishment、0xC9 Modify 或 N2。若单个 Codec Capability 通过 enum selector 覆盖多 Profile，必须证明单一封闭 Output Schema 能表达所有字段约束并保持 Capability↔Callable 1:1；否则另提设计，不能暗中增加 Callable 或开放 tagged union。Codec Result 不是 Owner Receipt / Commit Proof。

## 7. Golden 与阶段门槛

| ID | 验收要求 | 当前状态 |
|---|---|---|
| DS-3GPP-01 | 固定 OpenAMSM commit / 四文件 Schema 闭包 / 标准版本 / Git blob / 选定 requestBody surface；跨 commit 混源失败 | Source Lock 未签认，NOT_RUN |
| DS-3GPP-02 | Source Bundle 逐文件 byte-for-byte；单字节 / 空格 / 注释 / CRLF 改动失败；不增加 per-file digest / package hash | Publisher 未发布，NOT_RUN |
| DS-3GPP-03 | PostSmContexts 的 n1SmMsg / n2SmInfo / n2SmInfoExt1 contentId 分别匹配对应 MIME Content-ID；引用目标缺失、重复 Content-ID、错槽、媒体类型不符时失败；未被 JSON 引用的 part 不得交给 Codec，额外 part 的拒绝 / 忽略由选定 ingress profile 决定 | Plugin / Compiler 未验收，NOT_RUN |
| DS-3GPP-04 | Skill G.4 根直接引用 pin 后 OAS3 Schema Component；保留 anyOf / oneOf / allOf / nullable / pattern / additionalProperties / format；未选定 refs 不 eager resolve | Compiler Schema / Golden 未冻结，BLOCKED |
| DS-3GPP-05 | Create T1 不要求 NAS-only 字段；T2 Codec Result 显式 SourcePath；SBI/N1 冲突在 mutation 前失败 | 作者源 / Provider Create Profile 未发布，BLOCKED |
| DS-3GPP-06 | 0xD1 / 0xC1 / 0xC9 / N2 独立资格化；截断 / 错 Profile / 0xD4 误作新候选失败 | Provider 未发布，BLOCKED |
| DS-3GPP-07 | 0xD4 / N2 completion 只续跑原 Run；原 bytes 保留；Codec Result 不作 Commit Proof | 联合实测 NOT_RUN |

SR-031、SR-010、SR-013、SR-026、SR-027 各自独立验收；任何一层 PASS 不自动升级下一层或系统 E2E。无 Codec 的 Skill 不因 Source Bundle / Codec 缺失被阻塞。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 建立 3GPP 公共 Schema、T0～T4 与 Source/Codec/Compiler 分层候选 | 修正 Create 选择前解码循环 | IR-009；Issue #47 |
| 2026-11-27 | 0.2.0 | ChatGPT / GPT-6 | 全文 | 冻结 OpenAMSM 实际支持版本与原版 YAML byte-for-byte 代发布 | 禁止任何 3GPP YAML 变更 | Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.3.0 | ChatGPT / GPT-6.2 | 全文 | 撤销强制 Adapter，确立 OAS3 原生消费与精确组件引用；补齐源版本 / blob、Compiler Resolver 和 Codec Output 边界 | 不应因 G.4 限制复制或投影 3GPP 标准 | Issue #47；SR-031/010/013/026/027 |
| 2026-11-27 | 0.3.1 | ChatGPT / GPT-6.2 | §2、§4、§7 | 补齐 PostSmContexts 四文件 / 102 Component 的选定闭包、lazy ref 解析、OAS3 实际关键字与 RefToBinaryData Content-ID 对应关系 | 防止漏锁传递依赖、全文件 eager resolve 和 multipart 二进制错配 | Issue #47；SR-031/010/013；CA-SL 1.6.0 |
| 2026-11-27 | 0.3.2 | ChatGPT / GPT-6.2 | §4、DS-3GPP-03～04 | 收紧 union 类型推导到 required 字段；明确未引用 multipart part 的消费隔离与 ingress profile 策略 | 不把可选字段误判为必有，也不超出原版 OpenAPI Schema 施加隐含拒绝 | Issue #47；SR-010/013；CA-SL 1.6.0 |
| 2026-11-27 | 0.3.3 | ChatGPT / GPT-6.2 | DS-3GPP-03 | 将未引用 part 的处理收敛为 Codec 隔离，额外 part 策略交由 ingress profile | 避免把 OpenAPI Schema 未声明的额外 part 一概判为非法 | Issue #47；SR-010/031；F06 |