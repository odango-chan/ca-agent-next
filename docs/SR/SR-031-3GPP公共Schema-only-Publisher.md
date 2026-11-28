# SR-031：OpenAMSM 3GPP OpenAPI 原版 Source Bundle 发布

> 文档类型：软件需求（SR）
> SR 版本：0.3.3
> 创建日期：2026-11-27
> 修订日期：2026-11-27
> 状态：DRAFT / REVIEW_REQUESTED；Publisher / Compiler / Plugin / Codec 产品均 NOT_RUN 或 BLOCKED_EXTERNAL_INPUT
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：修改原版 YAML、改写 3GPP 标准、伪造 NAS/NGAP YAML、实现消费端、全量协议资格、旧版兼容
> 上游：[IR-009](../IR/IR%20总登记册.md#ir-009)、[Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)
> 实施仓：ca-skills（Publisher）；消费端归 SR-010 / SR-013
> 权威设计：[EC01.3GPP](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)

## 0. 唯一裁决与范围

**SR-031 只负责原版 OpenAMSM 3GPP OpenAPI Source Bundle 的确定性代发布。它不是 Schema-only Interface Package Publisher，也不是 Adapter / Projection 生成器。** 原始 YAML 按 OpenAMSM 实际支持的来源快照逐字节发布。当前主路径是原生 OpenAPI 3.0 消费；不得因 G.4 限制修改原件或预设必须生成 Adapter。

- Publisher：从固定 OpenAMSM commit 复制选定 OpenAPI 根文件及其可达外部 `$ref` 闭包，保持原路径，附 Source Lock / byte-compare 证据。
- Plugin / SR-010：原生解析 SBI operation、requestBody、multipart、JSON / binary parts、media type、Content-ID；不完整解码 NAS/NGAP。
- Compiler / SR-013：Skill-owned G.4 Request 根可引用 pin 后 Source Bundle 中精确 OAS 3.0 `components/schemas`；外部目标按 OAS 3.0 Schema Object dialect 解析。
- Provider / SR-026：独立发布 NAS/NGAP Decoder Result Schema 与 READ Capability；SBI `format: binary` 不是解码结果契约。

Source Bundle 不是 Interface Package，不导出 Capability / Callable，不产生 Capability Scope。SR-030 Host Context Schema-only Package 仍只经 `Contract.contexts` 使用。当前不设计 Adapter；若未来有可复现的 OAS 3.0 语义阻断，另开 Issue 并以证据评审最小方案。

## 1. 已核实的 OpenAMSM 来源样本

截至 2026-11-27，`env-openamsm/main` = `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`。这是已观察快照，不替代 OpenAMSM Owner 对正式构建基线的签认。

| 文件 | 3GPP 标准版本 | OpenAPI / 源版本 | Git blob |
|---|---|---|---|
| `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml` | TS 29.502 V19.5.0 | OpenAPI 3.0.0；`info.version: 1.4.0` | `3572be0315a782691ce8b5546b7bc1d5b22fcd64` |
| `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29571_CommonData.yaml` | TS 29.571 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.6.1` | `e09e9bb4aef0cf24aee008da06b1ef0023475efb` |
| `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29510_Nnrf_NFManagement.yaml` | TS 29.510 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.4.1` | `59d115ee6c7f4854aa123ad0c4ff7112fa879d73` |
| `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29518_Namf_Communication.yaml` | TS 29.518 V19.6.0 | OpenAPI 3.0.0；`info.version: 1.4.1` | `b695453dad07d1dd7b0d9a5ee28a80a71fee805d` |

不得把 OpenAPI `info.version` 误认为 3GPP TS 版本。当前 ingress 的选定面固定为 `PostSmContexts.requestBody` → `multipart/related` → `jsonData` → `#/components/schemas/SmContextCreateData`。在 source commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 上，递归 Schema 引用静态遍历得到 4 份原版 YAML、102 个可达 Schema Component，无未解析目标或循环；文件为 TS 29.502、TS 29.571、TS 29.510 NFManagement、TS 29.518 Namf Communication。该结果只适用于此选定根，不是整个 operation 的 response / callback 闭包，也不是全部 472 份 YAML。若后续消费 response / callback，必须作为额外选定根显式登记。

NAS / NGAP 是 Codec 源证据，不是本 SR 的 OpenAPI 发布对象：NAS TS 24.501 R19.6.2 DOCX `upstream/openamsm/lib/nas/5gs/support/r19.6.2/24501-j62-ch8-ch9.docx`，blob `82dcc4c97436ec85c3da14bb35f022385c9484b6`；NGAP TS 38.413 R19.2.0 ASN.1 `upstream/openamsm/lib/asn1c/support/ngap-r19.2.0/38413-j20.asn`，blob `3fa6da460a85bb2054316afec3da37d2b7043fe0`。不得伪造 NAS / NGAP 官方 YAML。

## 2. Source Lock 与复制规则

Source Lock 必须固定 OpenAMSM repo / commit、源码根（当前为 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/`）、标准版本证据、OpenAPI `openapi` / `info.version`、所选 HTTP method / path / operationId、选定消费 surface（当前 ingress 为 `requestBody` / `jsonData`）、每个文件的原始相对路径 / Git blob ID / byte length、Schema Component JSON Pointer 与该选定根的本地及跨文件 `$ref` 闭包。只使用 Git 原生 commit / blob 作为来源定位，不增加 per-file SHA-256 / digest、package hash、签名或 Trust Registry；Publisher 通过直接 byte-for-byte 比较验证原件。一个 Release 只对应一个 OpenAMSM snapshot，不得跨 commit 混源。

- 二进制复制；禁止 YAML load/dump、格式化、重序列化、key 重排、编码 / 换行转换、注释修改或生成“等价 YAML”。
- 原文件名、目录、相对 `$ref` 保持原样；外围 manifest / Source Lock 放在原件树外。
- 对固定 commit 对应的源文件与发行文件直接 byte-for-byte 比较；单字节、空格、注释、BOM、CRLF/LF 变化都失败。Git blob ID 只作上游来源定位，不作为新增哈希校验机制。
- 不能以解析后的 JSON/YAML 相等证明原件不变；不能重写 `$ref` 使引用看似可用。
- OpenAMSM 升级时发布新 snapshot，不覆盖旧版本，不使用动态 latest。
- 每个选定根必须明确到消费 surface，而不是只写 operation 名。当前 Plugin ingress 选定根是 `PostSmContexts.requestBody`，其 multipart `jsonData` schema 指向 `SmContextCreateData`；Compiler 选定根是精确 `components/schemas` pointer。
- Publisher 保留完整原始根 YAML 文件，但依赖闭包只收集选定根可达的 refs。消费端必须先解析根文档，再 lazy resolve 选定根；不得全文件 eager resolve。未选定 operation 的外部 refs 可以不在本 Bundle；选定闭包内缺文件 / 错 pointer / 循环 / 规范化后逃出 Source Root 必须失败。`../` 在规范化后仍位于 Source Root 内时允许。

## 3. 原生 OAS 3.0 消费契约

TS 29.502 `PostSmContexts` 的 ingress surface 使用 `multipart/related`：`jsonData` 引用 `#/components/schemas/SmContextCreateData`。该 Schema Component 除 TS 29.571 CommonData 外，还引用 TS 29.510 NFManagement（`ServiceName` / `WAgfInfo` / `TngfInfo` / `TwifInfo`）和 TS 29.518 Namf Communication（`NgRanTargetId` / `SbiBindingLevel`）；所以当前 requestBody / jsonData 闭包必须锁定四份原版 YAML。其余 binary parts 为 `binaryDataN1SmMessage`（`application/vnd.3gpp.5gnas`）、`binaryDataN2SmInformation` / `binaryDataN2SmInformationExt1`（`application/vnd.3gpp.ngap`）；encoding 声明 JSON `application/json` 和 binary parts 的 `Content-Id`。

CommonData `RefToBinaryData.contentId` 是被引用 binary body part 的 `Content-ID` header 值。Plugin 必须精确校验 `jsonData.n1SmMsg.contentId` ↔ `binaryDataN1SmMessage`、`jsonData.n2SmInfo.contentId` ↔ `binaryDataN2SmInformation`、`jsonData.n2SmInfoExt1.contentId` ↔ `binaryDataN2SmInformationExt1`。每个出现的引用必须唯一命中对应 slot；Content-ID 不得在 parts 间重复；引用目标缺失、错槽或媒体类型不符均拒绝。未被 JSON 引用的 part 不得交给 Codec；额外或未引用 part 的拒绝 / 忽略由选定 ingress profile 明确规定，不从 Schema 隐含推断。

Plugin 必须按原版 OAS 3.0 解释选定 operation / requestBody / content / multipart encoding / part Schema / media type / Content-ID，不得手写第二套 SBI Schema，也不得把 binary slot 当作已解码 NAS/NGAP 字段。只解析选定 surface 的可达 refs，不全局 eager resolve 根文件中其他 operation 的 refs。

Skill-owned `requestSchema` 根仍是本地 G.4。显式声明并 pin Source Bundle 后，本地字段可直接引用原版 OAS 3.0 `#/components/schemas/...`，外部目标按 OAS 3.0 Schema Object 语义处理，保留 `nullable` / 组合 Schema / `format` 等，不做 Adapter / Projection。只允许精确 Schema Component；禁止任意 URL、动态 latest、Path Item / Operation / RequestBody / Response 或 Bundle 外文件。实际 dependency alias / path / pointer wire 表示由 ca-skills / Compiler Owner 在正式 1.6.0 Schema / Golden 冻结，本 SR 不伪造 DTO。

若 Compiler / Runtime 不支持可达闭包中的 OAS 3.0 语义，必须 fail-closed 并阻止 Build / Verify；不得静默丢关键字或生成部分 Artifact。此能力归 SR-013 / EC02，不归 Publisher。

## 4. AC 逐项验收

| AC | 正反向断言 | 当前门槛 |
|---|---|---|
| AC-031-01 | 固定 OpenAMSM commit、TS 29.502 / 29.571 / 29.510 / 29.518 标准版本、四文件 Git blob、选定 requestBody surface 与完整可达 refs；跨 commit / 缺 ref 失败 | Owner source lock 未签认，NOT_RUN |
| AC-031-02 | 每个源文件与发行文件 byte-for-byte 相同；单字节 / 空格 / 注释 / CRLF 反例失败；不新增 per-file digest / package hash | Publisher CI，NOT_RUN |
| AC-031-03 | 仅对选定 surface 递归闭包；选定 refs 缺文件、错 pointer、循环、规范化后逃出 Source Root 失败；`../` 目标仍在 Source Root 内时允许；未选定 operation 的 refs 不触发 eager resolve | Source Lock validator，NOT_RUN |
| AC-031-04 | 不经 load/dump / format / generator / normalization；manifest 在 YAML 树外 | Publisher immutability，NOT_RUN |
| AC-031-05 | 向 SR-010 / SR-013 提供原始 OAS3 文档、operation + surface 身份、四文件引用闭包和 Content-ID slot mapping fixtures；不声称 Publisher 已完成消费端解析 | Consumer handoff，NOT_RUN |
| AC-031-06 | NAS / NGAP 不因 SBI binary parts 自动生成 Schema；DOCX / ASN.1 仅为 Codec 源证据 | Source inventory，NOT_RUN |
| AC-031-07 | source snapshot 升级发布新不可变 Bundle；旧版不覆盖；混源 / latest / byte mismatch 失败 | Release identity，NOT_RUN |

Publisher CLI、Source Bundle identity 和正式 Golden 尚未由 ca-skills Owner 发布，不得由 Harness 猜测。实施 Issue 必须绑定本设计 SHA、OpenAMSM source SHA、授权目标仓、byte-compare 命令和远端发行证据。

## 5. 责任与状态

- SR-010 / Plugin：原生 OAS3 SBI ingress、multipart / Content-ID 校验、原始 N1/N2 staging；不完整解码。
- SR-013 / Compiler：Skill-owned G.4 根对 pin 后 OAS3 Schema Component 的跨 dialect 引用、类型检查、运行期快照与 fail-closed。
- SR-026 / Provider：NAS/NGAP Codec READ、唯一 Callable、Decoder Result Schema 和消息 Profile。
- SR-027 / Bundle：固定实际使用的 Source Bundle、Compiler / Provider / Owner / Host snapshots；无关 Echo 不强制下载。
- F09 / Studio：原版 YAML 只读展示和来源导航，不允许 AI Change Set 修改原件。

SR-031 主状态保持 DRAFT；本设计可独立评审，但 Publisher、Compiler Resolver、Plugin ingress、Provider Codec、1.6.0 Bundle 产品 AC 均 NOT_RUN / BLOCKED。原版代发布成功不等于 Compiler / Codec / 系统 E2E PASS。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 建立 3GPP 公共 Schema、T0～T4 与 Source/Codec/Compiler 分层候选 | 修正 Create 选择前解码循环 | IR-009；Issue #47 |
| 2026-11-27 | 0.2.0 | ChatGPT / GPT-6 | 全文 | 冻结 OpenAMSM 实际支持版本与原版 YAML byte-for-byte 代发布 | 禁止任何 3GPP YAML 变更 | Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.3.0 | ChatGPT / GPT-6.2 | 全文 | 撤销强制 Adapter 假设；改为原生 OAS3 消费和精确组件引用；补齐源文件 / blob / 标准版本、Source Lock、NAS/NGAP 原生源 | G.4 与 OAS3 是不同 dialect，不应复制一套标准 | Issue #47；SR-010/013/026/027 |
| 2026-11-27 | 0.3.1 | ChatGPT / GPT-6.2 | §1～4、AC-031-01～05 | 补齐 PostSmContexts requestBody 四文件 / 102 Component 闭包、选定面 lazy refs、Git blob + byte-compare Lock、RefToBinaryData Content-ID 对应 | 修复漏锁跨文件依赖、全文件 eager resolve 和 multipart part 错配风险 | Issue #47；SR-010/013/027；EC01/EC02 |
| 2026-11-27 | 0.3.2 | ChatGPT / GPT-6.2 | §2～4 | 统一 Git blob 仅作来源定位、byte-for-byte 为唯一原件比较；未引用 multipart part 不交 Codec，拒绝策略归 ingress profile | 避免额外哈希机制和超出原版 Schema 的隐含拒绝 | Issue #47；SR-010/013；EC01/EC02 |