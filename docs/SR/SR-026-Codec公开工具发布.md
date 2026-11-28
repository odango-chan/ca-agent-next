# SR-026：Codec公开工具发布

> 文档类型：软件需求（SR）  
> SR 版本：0.2.0
> 状态：整项 DRAFT；BLOCKED_EXTERNAL_INPUT。AC-026-01～03 维持既有候选库/Provider 门槛；新增 AC-026-04～06（原生协议源、公开 Codec READ 1:1、T2 Result 校验）全部 BLOCKED_EXTERNAL_INPUT / NOT_RUN。
> 下一步：Provider Owner 需交付 Codec 公开 Capability、唯一 Callable、输入输出 Schema、slot/mediaType、handler 和包版本。v1.2.0 与候选 PR #39 分别记录。  
> 阶段依据：[独立评审 #87](https://github.com/odango-chan/ca-agent-next/issues/87#issuecomment-7209366603)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。
> 创建日期：2026-11-26  
> 修订日期：2026-11-27\
> 上游需求：IR-006  
> 设计依据：F03.05 v0.4.4 §8.2、§11 与 EC03 外部生产端复验。\
> 关联 Issue：ca-agent-next#12（设计）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §4；本批仅验收指定 NAS Decode。

## 0. 本轮设计评审入口（2026-11-26）

本 SR 已提交 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计审查；**主状态 `DRAFT` 与设计 `REVIEW_REQUESTED` 独立，实施 READY/产品 PASS 均未获得**。新语言架构见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 和 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮审查重点：**核查 Codec 的独立 READ 能力、公开 Capability ID/唯一 Callable Binding、私有 backend 选择、严格 Schema 与真实字节向量。
- **未发布/未证据项：**现有 Provider 2 Capability / 11 历史 Callables 不是 1.6.0 公共模型；新绑定与 Codec 公开契约须由 ca-client-tools Owner 冻结，AC 未运行。
- **统一目标：**CA-SL **1.6.0 ONLY**；Skill-facing 只有 Capability ID，公开 Capability↔Callable 严格双向一对一；旧语言、Compiler DTO、Artifact、Bundle、别名、fallback 与迁移兼容均禁止。旧源 Schema/fixture/发布身份只用于只读历史审计；新机器契约由发布者冻结，不得自行猜测。
- **评审退出：**逐项核查范围/非目标、外部契约、失败语义和 AC；外部新合同未发布为 `BLOCKED`、产品未运行为 `NOT_RUN`。在独立评审通过前不得向 Harness 交付实施提示词。

## 1. 目标与前置

目标仓 ca-client-tools，功能 F03.05 / EC03，消费方 ca-agent-next SR-010。中央依据为 F03.05 §8.2、§11 及 [Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md#ec03-外部生产端与复验)。现状为 Provider v1.2.0 有 11 个 READ，Codec 候选 PR #39 有本地库和 Worker。先固定可复验的 Phase B revision，仅选已通过正反向 fixture 的一类 NAS Decode 做第一批。现有 11 个公开导出和 Owner 契约不包含此操作。

## 2. 在源仓交付

1. 以 `protocol/codec/nas.go` 的 DecodeNAS 与同目录测试为输入，固定一个已支持的消息类型、原始输入和预期 JSON。声明新的公开 Callable ID、Capability membership、READ、精确输入输出 Schema、输入 artifact slot 和媒体类型。READY 前由 Provider 所有者在本节登记精确 ID、Schema、handler 与版本，不由消费端命名。
2. 在 `internal/provider/` 接入进程内本地 handler，通过 Host artifact channel 取原字节；结果不经过远端 SBI，拒绝错误 slot、非法消息与超限。以现有 v2 schema 实测能否合法表示本地结果；若必须改变冻结 envelope，先给出版本化契约、Driver 选择和兼容测试，再启动该部分。
3. 同步 Provider 发布包生成器、公开 Interface、bindings 和私有 backend catalog；真实进程只在声明的 ID 上响应。将构建所得包交给 Next，禁止直接从分支代码导入 Go 库作为 Tool。包的新增版本使用纯数字 SemVer。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-026-01 | 在选定候选根运行 `go test ./protocol/codec/...`，记录受测 SHA、支持子集、具体 fixture 和测试数；截断/不支持的消息失败 |
| AC-026-02 | 在生产端运行 `go test ./internal/provider ./internal/runtimebindings ./internal/interfacepkg`，再用发行包的 `provider serve` 完成 initialize/catalog/invoke；断言精确投影、零远端 SBI 请求、原字节不变，缺通道时该绑定 unavailable |
| AC-026-03 | 用同一发行包和同一 fixture 执行 SR-010。先无 decode 声明验证零调用，再在有授权的 Skill 上验证一次调用；越权在派发前拒绝 |
| AC-026-04 | 固定 OpenAMSM source commit、NAS/NGAP 原生协议源版本、消息 Profile、原始 bytes 与字段来源；不得把 SBI binary part 当解码 Result 或伪造官方 YAML | BLOCKED_EXTERNAL_INPUT |
| AC-026-05 | Provider Owner 发布正式 Codec READ Capability↔唯一 Callable、封闭 selector、Artifact slot、Output Schema、版本、handler 与 Golden；多 Profile 必须证明单一封闭 Schema 可表达，否则另提设计 | BLOCKED_EXTERNAL_INPUT |
| AC-026-06 | MAS 1.6.0 Skill 仅在 T2 调用 Codec READ 并校验 Result；T1 不读 NAS-only 字段；0xD4≠0xD1；截断/越权/错 Profile/Schema 不符 fail-closed，Owner mutation=0 | NOT_RUN / BLOCKED_EXTERNAL_INPUT |

## 4. 状态与非目标

源仓实施 Issue、PR、commit、正式包未登记，测试 NOT_RUN。前述公开 ID/Schema、版本与本地结果 profile 未冻结，维持 DRAFT。第一批不含 Encode、全量 NGAP、ext=1 或其他未经资格化消息。SR-015 的设计移交和 SR-010 已发布 Provider 部分可单独验收。无替代 SR。

**外部契约决定（D14，OPEN）**。已核对 ca-client-tools main `7bcb2614aa3615d8358df31eecefd0909e894e40` 与 [PR #39](https://github.com/odango-chan/ca-client-tools/pull/39) 的候选库 `eb1169fe1d0e2e691d101908aad08ee8801da754`。生产者需提供同一固定源中的 Package ID/纯数字版本、公开 Capability 与唯一 Callable、入出参 Schema 及 slot/mediaType、handler 路径/符号与本地结果 profile，并记录正式发布或签认的 PR/commit。AC-026-01 仅复核库向量。此记录为空时 02/03、AC-010-06b 的全量 3/3 及 07/08 均不得使用候选别名或推测 Schema。

### 首批 NAS 向量

固定 PR #39 `protocol/codec/codec_test.go::TestDecodeNASOpenAMSMVectors` 中的 `release-request`，原始四个 octet 为 `2e 05 01 d1`，Decoder 的消息类型应为 `PDUSessRelReq`，PSI=5、PTI=1。加入截断到三个 octet、同头但最后 octet 为 0xd4 的反例，后者是有效 Release Complete、超出首批指定的消息类型。以 `go test ./protocol/codec -run TestDecodeNASOpenAMSMVectors -count=1 -v` 单独核对原始库向量，再由公开 Provider 调用重跑。本节只定义第一批公开子集。

### 4.1 公开 Codec Package 生产者交接表（尚未交付）

| 生产者 | 必须固定且可复核的内容 | 缺失时受阻的门槛 |
|---|---|---|
| ca-client-tools / Provider Owner | 正式源 SHA、Package ID / SemVer、1.6.0 languageTarget、公开 Capability ID 与唯一 Callable ID、READ kind/Effect、真实 handler 路径和符号 | AC-026-02/03 及 Consumer SR-010 正向运行 |
| ca-client-tools / Provider Owner | 输入/输出 Schema、Artifact slot/方向/mediaType、Release Request 专属 JSON 结果 profile、错误码及截断/错误类型负例 | 正式 Codec Tool 的准确参数与结果验收 |
| ca-client-tools / Provider Owner | 同一发行包 initialize/catalog/invoke 证据、零远端 SBI 请求、与原 Provider 查询 2/2 合成 3/3 的一对一对账 | 不得将 PR #39 库向量或私有 backend 名称冒充公开 Tool |

这些字段由生产者在其签认 Issue/PR 和正式发布记录中提交。本 SR 现有 `2e 05 01 d1` 向量、`0xd4` 非目标负例可先供静态评议；任何字段尚缺时，禁止由 Harness 推断别名、Schema、版本或“兼容”路径，SR-026 整体仍 BLOCKED_EXTERNAL_INPUT。

## 5. 3GPP SBI OpenAPI 与 NAS / NGAP Codec Result 的边界（IR-009）

**TS 29.502 SBI OpenAPI 不是 NAS / NGAP Decoder Result Schema。** SR-031 原样代发布 OpenAMSM 实际使用的 OAS 3.0 YAML；`format: binary`、MIME type 与 Content-ID 只定义 N1/N2 multipart transport，不定义 NAS IE / NGAP ASN.1 解码字段。SR-026 Provider 必须独立发布真实 READ Capability / 唯一 Callable / Input Schema / Output Schema / message Profile。

当前已核对的 OpenAMSM 源证据（`env-openamsm@dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`）：

| 协议 | 原生标准源 | 生成 / 实现证据 | 当前边界 |
|---|---|---|---|
| NAS 5GSM | TS 24.501 R19.6.2：`lib/nas/5gs/support/r19.6.2/24501-j62-ch8-ch9.docx`，blob `82dcc4c97436ec85c3da14bb35f022385c9484b6` | OpenAMSM NAS README 说明生成 `message.h` / `ies.h` / `decoder.c` / `encoder.c` | 只证明 OpenAMSM 源版本和生成流程，不证明 Provider 已发布 |
| NGAP | TS 38.413 R19.2.0：`lib/asn1c/support/ngap-r19.2.0/38413-j20.asn`，blob `3fa6da460a85bb2054316afec3da37d2b7043fe0` | `lib/asn1c/ngap/meson.build` / 生成 C 注释引用该 ASN.1 模块 | 不代表 Codec 已覆盖全部 NGAP PDU / IE |

第二阶段追加验收：

- **AC-026-04** 固定 OpenAMSM source commit、NAS / NGAP 原生协议源版本、消息 Profile、原始 bytes 和逐字段来源。不得把 SBI `binary` part 当作解码结果类型，不得凭空生成 NAS / NGAP 官方 YAML。
- **AC-026-05** Provider Owner 发布正式 Codec READ Capability ↔ 唯一 Callable、关闭 Input selector、Artifact slot、Output Schema、版本、handler 和 Golden。Create 所需 PSI / PTI / PDU Session Type / SSC mode、Modify 字段及 N2 输出均须有真实 fixture。一个 Capability 若覆盖多个 Profile，必须证明一个封闭 Output Schema + 固定 enum selector 能表达每个 Profile 的字段约束并保持 1:1；否则先提出新设计，不能暗中扩张 Callable 或采用开放 tagged union。
- **AC-026-06** 新 MAS 1.6.0 Skill 在 T2 调用 Codec READ 并逐字段校验 Provider Result；T1 不读取 NAS-only 字段；0xD4 不是 0xD1；截断、越权、错误 Profile、Output Schema 不符均 fail-closed，Owner mutation=0。缺正式 Provider / Bundle 时 NOT_RUN。
- **现有证据隔离**：ca-client-tools PR #39 的 Go 内部库 / 解码向量不等于公开 Provider Capability / Callable / Output Schema；不得将 PR #39 库测试宣称为 Provider Release 或全量 NAS/NGAP 资格。

原 AC-026-01～03 与首批 0xD1 范围保持不变。新增 AC-026-04～06 均 BLOCKED_EXTERNAL_INPUT；SR-031 原版 OAS Source Bundle 的 byte-for-byte PASS 不能代替 SR-026 Codec 产品验收。消费者为 SR-010 / SR-027 / SR-011；详见 [EC01.3GPP 设计](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | Codex / GPT-6 | 见本行变更 | 首次登记两端交付、独立复验与就绪条件 | 未单独记录（历史原因未提供） | Issue #12 |
| 2026-11-26 | 0.1.1 | Codex / GPT-6 | 见本行变更 | 固定实际 Codec 向量及验收结果；补齐正式文档的评审范围与非目标；绑定中央设计章节；列明依赖设计版本 | 未单独记录（历史原因未提供） | Issue #12 |
| 2026-11-26 | 0.1.2 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 提交设计待评审、明确新旧契约/验收隔离并保留 DRAFT 主状态 | 未单独记录（历史原因未提供） | Issue #12；PR #45；SR-029 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 设计依据与新版本路径 | 刷新 1.6.0 正式目标设计引用：v0.4.0→v0.4.1 | 未单独记录（历史原因未提供） | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.1.4 | Codex / GPT-6 | §2、§4 | 标出 Provider Owner 缺件及候选库可复核边界 | 未单独记录（历史原因未提供） | Issue #12，PR #46 |
| 2026-11-27 | 0.1.5 | Codex / GPT-6 | 评审状态 | 登记第二轮限定范围及外部依赖 | 未单独记录（历史原因未提供） | Issue #12，PR #46 |
| 2026-11-27 | 0.1.6 | GPT-6（ChatGPT） | §4.1、修订表 | 固定 Codec 公开契约缺件及唯一生产者，保留现有库向量独立可审查范围，整理历史六列修订记录 | 将外部输入阻塞与静态候选审查隔离，杜绝猜测公开机器 ID | Issue #12；PR #46；SR-026 |
| 2026-11-27 | 0.1.7 | GPT-6（ChatGPT） | 修订记录 | 将历史记录统一为七列并保留原始文字及原始关联，修正非规范行的分隔符 | 确保修订表可由文档校验器完整解析；不影响设计语义及 READY 主状态 | Issue #12；PR #46；SR-026 |
| 2026-11-27 | 0.1.8 | Codex / GPT-6 | 文档头 | 登记BLOCKED_EXTERNAL_INPUT及 AC 范围 | 按单项独立评审推进 | Issue #12、#87；PR #46 |
