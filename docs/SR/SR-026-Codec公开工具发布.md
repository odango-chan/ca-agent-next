# SR-026：Codec公开工具发布

> 文档类型：软件需求（SR）  
> SR 版本：0.2.0\
> 状态：整项 DRAFT；本轮中央生产端设计已补齐，`DESIGN_REVIEW_REQUESTED`；产品 AC 仍 NOT_RUN。实施 Issue 未创建，须待 SR-026 READY。  
> 下一步：独立评审本轮中央契约；达到 READY 后再在 ca-client-tools 创建实施 Issue。PR #39 仅是 Codec 库 / Worker 的 Phase B 候选，不是公开 Provider Tool 发布。  
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

目标仓：`odango-chan/ca-client-tools`；消费方为 Next / SR-010。中央依据为 F03.05 §8.2.1、§12.3.1、SR-026 与 SR-029。Provider v1.2.0 的 11 个历史 READ 和 PR #39 的 Codec 库 / Worker 仅作实现来源；本 SR 的目标是按 1.6.0 Provider Interface Package 2.0.0 发布 3 Capability / 3 Callable，其中 Codec 是第三个本地 READ。

## 2. 在源仓交付

1. 以 `protocol/codec/nas.go` 的 DecodeNAS 与同目录测试为输入，固定一个已支持的消息类型、原始输入和预期 JSON。声明新的公开 Callable ID、Capability membership、READ、精确输入输出 Schema、输入 artifact slot 和媒体类型。READY 前由 Provider 所有者在本节登记精确 ID、Schema、handler 与版本，不由消费端命名。
2. 在 `internal/provider/` 接入进程内本地 handler，通过 Host artifact channel 取原字节；结果不经过远端 SBI，拒绝错误 slot、非法消息与超限。以现有 v2 schema 实测能否合法表示本地结果；若必须改变冻结 envelope，先给出版本化契约、Driver 选择和兼容测试，再启动该部分。
3. 同步 Provider 发布包生成器、公开 Interface、bindings 和私有 backend catalog；真实进程只在声明的 ID 上响应。将构建所得包交给 Next，禁止直接从分支代码导入 Go 库作为 Tool。包的新增版本使用纯数字 SemVer。
## 2.2 中央固定的生产端接口契约（设计目标，尚未发布）

本 SR 的目标不是等待 Provider Owner 自行发明公开接口，而是按 F03.05 中央设计实现以下契约：

| 项目 | 唯一目标值 |
|---|---|
| Capability ID | `protocol.nas.5gsm.release-request.decode` |
| Callable ID | `ca-client-tools.codec.nas.5gsm.release-request.decode` |
| Interface Package ID | `urn:wtlab:ca-client-tools:openamsm-sbi-interface` |
| Package / Provider 目标 SemVer | `2.0.0` |
| Runtime Bindings Sidecar | `ca.tool-provider-runtime-bindings/v2` |
| Provider Protocol | `ca-client-tools.provider/v2` |
| Artifact Channel | `ca-host.artifact-store/v1` |
| 首批消息 | NAS 5GSM PDU Session Release Request `0xD1` / `PDUSessRelReq` |

公开 Provider Interface 1.6.0 目标闭包为 3/3：`openamsm.smf.mas.context.read` ↔ `ca-client-tools.openamsm.smf.mas.context.read`；`openamsm.nf.metrics.read` ↔ `ca-client-tools.openamsm.nf.metrics.read`；`protocol.nas.5gsm.release-request.decode` ↔ `ca-client-tools.codec.nas.5gsm.release-request.decode`。前两项分别使用闭合 `contextKind`、`resourceKind` selector；第三项使用唯一 Codec Callable。Capability 与 Callable 一对一，backendOperationId 只留在 Provider 私有映射。

**输入：**公开 Input Schema 是空闭合对象；原始 N1 字节通过 Host-owned `PRIVATE_MATERIAL` 注入，不暴露给 Skill / LLM。Runtime Bindings v2 私有参数为 `n1_sm`，Artifact slot=`n1Message`，direction=`INPUT`，mediaType=`application/vnd.3gpp.5gnas`。Provider catalog descriptor 声明 `artifactSlots.inputs` pointer `/n1_sm`。Host 注入当前 Invocation 的 `artifactRef`；缺少 Artifact Channel、slot/mediaType 不符或引用不属于当前 Invocation 时派发前拒绝。

**输出：**发布闭合 Output Schema，字段为 3GPP 语义名：`protocol=NAS`、`messageType=PDU_SESSION_RELEASE_REQUEST`、`messageTypeCode=209`、header（EPD=46、PSI、PTI）、qualification（complete/qualified/rawPreserved/structuralParse/projectionValid/reencodeEligible/reencodeVerified/consumedBits/totalBits/ieToDo）、status 和 diagnostics。首批只允许当前 Golden 已覆盖的 Release Request 投影；底层返回 ePCO 等未资格化字段时必须 `NOT_QUALIFIED`，不得作为可用业务数据。原始字节不返回、不 Base64 化，保留在 Host Artifact Store。

**状态与错误：**Codec 状态枚举为 `SUCCESS`、`PARTIAL`、`UNSUPPORTED_MESSAGE`、`UNSUPPORTED_IE`、`DUPLICATE_IE`、`INVALID`、`NOT_QUALIFIED`。只有 `SUCCESS && complete && qualified && rawPreserved && projectionValid && reencodeVerified` 才是可消费 Observation。Release Complete `2e 05 07 d4` 对本 Capability 返回 `UNSUPPORTED_MESSAGE` / `MESSAGE_TYPE_OUT_OF_SCOPE`；截断 `2e 05 01` 返回 `INVALID`。

**执行：**Provider 进程内直接调用 Go `protocol/codec` Facade，不启动 Python Worker 子进程、不发远程 SBI、不修改 Owner 状态。旧 `protocol/nas5gsm` helper（ca-client-tools#18）仍是独立 Host/Mock AMF 协议辅助库，不等同于本 SR 的公开 Provider Capability；PR #39 的 `protocol/codec` 仅是本地库候选。

以上为中央设计目标，尚未发布。Provider Owner 不得自行改名或扩大消息范围；实现中如发现不可行，必须先回到 Next 更新 F03.05 / SR-026。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-026-01 | 在选定候选根运行 `go test ./protocol/codec/...`，记录受测 SHA、支持子集、具体 fixture 和测试数；截断/不支持的消息失败 |
| AC-026-02 | 按 F03.05 中央契约实现 Provider Interface Package 2.0.0 与 Runtime Bindings v2；运行 `go test ./internal/provider ./internal/runtimebindings ./internal/interfacepkg`，再用正式包的 `provider serve` 完成 initialize/catalog/invoke；断言 3/3 Capability↔Callable、私有 Artifact slot、闭合输出 Schema、零远端 SBI 请求、原字节不变，缺通道时绑定 unavailable |
| AC-026-03 | 用同一正式 Provider 包和同一 NAS fixture 执行 SR-010；未声明 `protocol.nas.5gsm.release-request.decode` 时验证零调用，声明并授权后验证一次 READ Observation；越权在派发前拒绝，任何非 SUCCESS/未资格化结果不得提升为 PASS |

## 4. 状态与非目标

目标仓为 `odango-chan/ca-client-tools`；实施 Issue=`NOT_CREATED`，仅 SR-026 与 SR-029 均 READY 后创建。测试仍 NOT_RUN。首批不含 Encode、全量 NGAP、ext=1 或其他未经资格化消息。SR-015 的设计移交和 SR-010 已发布 Provider 部分可单独验收。无替代 SR。

**中央设计裁决（D14 CLOSED，Issue #113）：**Package ID、Capability ID、Callable ID、Input/Output Schema、Artifact slot/mediaType、首批消息范围和 Provider 执行路径已在 Next / F03.05 / SR-026 固定。生产仓只负责实现和发布，不得把这些设计空白留给 Harness 或临时决定。`ca-client-tools#18` 只覆盖历史 `protocol/nas5gsm` helper；PR #39 是 `protocol/codec` Phase B 候选库，不是公开 Provider Package。

### 首批 NAS 向量

固定 PR #39 `protocol/codec/codec_test.go::TestDecodeNASOpenAMSMVectors` 中的 `release-request`，原始四个 octet 为 `2e 05 01 d1`，Decoder 的消息类型应为 `PDUSessRelReq`，PSI=5、PTI=1。加入截断到三个 octet、同头但最后 octet 为 0xd4（Release Complete 固定向量 `2e 05 07 d4`）的反例，后者是有效 Release Complete、超出首批指定的消息类型。以 `go test ./protocol/codec -run TestDecodeNASOpenAMSMVectors -count=1 -v` 单独核对原始库向量，再由公开 Provider 调用重跑。本节只定义第一批公开子集。

### 4.1 目标仓与实施 Issue 绑定

| 项目 | 绑定值 |
|---|---|
| 中央 SR | SR-026（F03.05 §8.2.1 / §12.3.1） |
| 目标仓 | `odango-chan/ca-client-tools` |
| 实施 Issue | `NOT_CREATED`；仅 SR-026 与 Provider 3/3 设计依赖 SR-029 均 READY 后创建 |
| 相关历史工作 | PR #39（Phase B Codec 库 / Worker，OPEN）；ca-client-tools#18（旧 `protocol/nas5gsm` Host/Mock AMF 辅助库） |
| 新 Issue 必须引用 | 本 SR、F03.05 固定设计 SHA、Capability/Callable、Package 2.0.0、Runtime Bindings v2、AC-026-01～03 |

目标 Issue 创建前不授权 Provider 代码实施或发布。实现完成后，PR / Commit / 测试日志 / Release 资产必须回填本 SR；任何契约变化先回到 Next 修订。
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
| 2026-11-27 | 0.2.0 | GPT-6.2（ChatGPT） | §2.2、§3、§4.1、文档头 | 固定 Codec Capability/Callable、Provider Package 3/3、Runtime Bindings v2、Host Artifact slot、NAS 首批范围与资格结果；明确目标仓 Issue 仅在 READY 后创建 | 将外部输入阻塞改为中央先定义、生产仓按契约实施，避免 Provider Owner 在发布时自行发明接口 | Issue #113；F03.05；SR-029 |
