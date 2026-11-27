# 3GPP 公共 Schema 发布与 Skill 分阶段消费设计说明书

> 文档类型：功能设计说明书（EC01.3GPP；关联 EC03/F02/F06/F08/F09）
> 文档版本：0.2.0
> 修订日期：2026-11-27
> 状态：DRAFT / REVIEW_REQUESTED；原版 YAML 代发布、适配契约和 Codec 产品均尚未验收
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：生产级资格、全量 NAS/NGAP、修改上游 YAML、重定义 3GPP 标准
> 上游：[IR-009](../../IR/IR%20总登记册.md#ir-009)、[Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)
> SR：[SR-031](../../SR/SR-031-3GPP公共Schema-only-Publisher.md)（标准 YAML 代发布）、[SR-026](../../SR/SR-026-Codec公开工具发布.md)（Provider Codec）、[SR-010](../../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md)（消费）

## 1. 不可变原则（用户 2026-11-27 最新裁决）

1. **唯一版本依据是当前选定 OpenAMSM 基线实际支持、实际使用的 3GPP OpenAPI YAML**，不是 ca-skills、NEXT、Codec Owner 自行选一个“最新 3GPP Release”。以固定 OpenAMSM 仓提交、内嵌标准目录、OpenAPI 文件与传递依赖文件作为唯一版本闭包。目录名如 `r19-20260402-openapitools-7.20.0` 是来源线索；**不能仅凭目录名断言正式 3GPP 标准发行号**，必须以具体 YAML 头/规范标记及 OpenAMSM 构建/代码引用证据确认。
2. **ca-skills 仅代为发布原始 3GPP YAML，不能改动 YAML 中任何内容**。包括字段、大小写、类型、OpenAPI / JSON Schema 约束、`$ref`、注释、顺序、缩进、空白、换行、编码、目录内相对引用内容。禁止重序列化 YAML、重新生成“等价 YAML”、格式化、删除不支持字段、修补标准或把派生 YAML 覆盖原文件。源文件到发行物逐文件 **byte-for-byte 相同**；相对路径/层级保持原样。只允许在**原文件之外**增加代发布清单/来源证明与测试证据。
3. **原版 YAML 与 CA-SL 运行时可消费 Schema 是两种不同工件**。3GPP 原始 OpenAPI 可能使用 CA-SL 1.6.0 G.4 不支持的 `#/components`、`oneOf`、`format` 等。**不能**将未转换的原版 YAML 声称为可经 Compiler 直接 `$ref` 的合法 G.4 类型，也不能为了让 Compiler 通过而修改原版 YAML。若业务需要编译期机器类型，另行发布**独立、显式标记为 Adapter / Projection 的 JSON Schema 契约**（非 3GPP 原版、不覆盖原件），其 Owner、版本、Golden、字段映射和引用机制必须另经评审冻结。无正式适配契约时，相关 Compiler/Bundle AC 坚持 BLOCKED。
4. **3GPP 公共发布不等于 NAS/NGAP 全量解码能力**。OpenAMSM 现存 `TS29502_Nsmf_PDUSession.yaml` 属于 SBI OpenAPI；TS 24.501（NAS）与 TS 38.413（NGAP）原文及其 Codec Result 不能因为发布 SBI YAML 就假定有对应的 YAML 或已资格化的 Decoder。NAS/NGAP 按 OpenAMSM 同一支持基线的真实实现与协议证据逐类型核对，由 Provider 发布自身 Output Schema；若无上游 YAML，**不得凭空生成“3GPP 官方 NAS/NGAP YAML”**。
5. 所有业务仍是 CA-SL **1.6.0 ONLY**、Skill-facing Capability、Capability↔Callable 双向一对一、唯一 Plugin Manager、Host-owned ArtifactStore、Owner 权威 Receipt/Commit Proof；不提供旧版兼容或迁移。

冲突处理优先级：本章**覆盖本仓先前“把 OpenAPI 转换后作为 3GPP 原版 Schema 导出”的说法**。原样代发布不可被业务消费适配要求推翻；若两者暂不能衔接，只标明依赖 BLOCKED，而不放宽原样要求。

## 2. OpenAMSM 基线锁与发行范围

| 源范围 | Source-of-truth | 可代发布的内容 | 明确不推断 |
|---|---|---|---|
| Nsmf_PDUSession SBI | OpenAMSM 自身使用的 TS 29.502 OpenAPI + 直接/间接引用的 YAML；历史 Demo 基线 `env-openamsm@dc83ccbf` 下 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml` | 该 OpenAMSM 基线的**原版 TS29502 YAML 文件及全部实际依赖的其他 YAML**；保留文件名/相对路径/原文 | 不随意补一套 R18/R19 或把另一仓更“新”的版本拼入 |
| NAS 5GSM | OpenAMSM 实际支持版本及 `ca-client-tools` 已检验的 NAS 解码实现/fixture；首批 PR #39 0xD1 fixture 是历史候选 | 仅 OpenAMSM 原来**确实提供**的标准 YAML 才可原样代发布；无该 YAML 就不造文件 | 不用 TS29.502 SBI YAML 代表完整 TS24.501 NAS 结构 |
| N2 NGAP | OpenAMSM 采用的消息结构 / 版本与受测 Codec/Mock peer | 同上，只代发布确实存在的 YAML | 不声明全量 TS38.413 ASN.1 已转成 OpenAPI Schema |

**源锁发布前必填**：OpenAMSM 实际受测 commit、原始源根、3GPP YAML 完整相对路径列表、每个文件 Git blob identity / byte digest、跨文件相对 `$ref` 闭包、源 YAML 的版本/规范标签、引用它的 OpenAMSM 真实构建/运行证据，以及原版与发行物的一对一文件映射。当前 `dc83ccbf` 是已记录的历史来源候选，不能假设就是新的 OpenAMSM 最新支持基线；新版本只能在 OpenAMSM 自身升级后，经新 Source Lock 和新发行版本发布，历史已发布文件不改写。

## 3. 两层交付物与严格分权

| 层级 / 产物 | 发布者与格式 | 可以做 | 不允许做 |
|---|---|---|---|
| **A：3GPP 原版 YAML Source Bundle（强制）** | ca-skills / SR-031 只读代发布 | 按源相对路径复制原始 OpenAMSM 支持的 YAML；单独附 source-lock/asset manifest、来源与版本/文件对账结果；让 Studio/作者检索原协议 | 修改或重写任一 YAML 字节；声称 YAML 自然符合 CA-SL G.4；凭空发布 NAS/NGAP 的 YAML |
| **B：CA-SL 1.6.0 类型适配/Schema-only Interface Package（仅业务确实需要时，独立受审）** | ca-skills 的**分离** Adapter 文件/包；Owner 和 1.6.0 Package Schema/Golden 由正式发布方冻结 | 从 A 的精确 Source Lock 生成或手工定义**不同路径、不同名称、显式标 Adapter** 的闭合 G.4 JSON Schema 类型；单独保留 field-to-source 映射和原始标准 revision；0 Capability/0 Callable | 冒充“原始 3GPP YAML”、回写 A、悄悄丢弃未知/多态约束、在正式 Package Schema 未批准时对外声称可直接 Link |
| **C：Codec READ Tool Interface + Output Schema** | ca-client-tools / SR-026 | 绑定已授权 raw artifactRef/slot、正式 READ Capability↔唯一 Callable；每个 NAS/NGAP 消息 profile 有经过检验的结构化 Result Schema/字段来源，使用 B 的公共类型仅在发布过且版本匹配时 | 重新定义 A 的 3GPP 原版、混用不匹配 Release、把 Codec Result 当 Owner Proof |
| **D：Skill-owned Request Schema + Host Context** | ca-skills Skill 作者、Host Context SR-030 | Skill-owned root 描述 T1 真实 Event 输入；适配包 B 已可 Link 时可引用其精确公共类型 $id；Host Context 独立只经 `Contract.contexts` 绑定 | 用 A 的未经适配的 OpenAPI 直接喂有限 G.4 Compiler；把 Codec 解码后字段放到 T1 强制要求 |

**关键语义**：A 是 **Source Bundle**，原版 YAML 即使随同发布也不构成可执行 Schema-only Interface Package；只有 B 真正满足 1.6.0 Package Schema / 非空 Schema exports / G.4 / Compiler Golden 时才能称为合法 Schema-only Package。若 B 尚未获准发布，A 可以独立完成“代发布”模块验收，但涉及 Compiler/Skill 的 B/C/D 产品验收保持 BLOCKED。这不是双语言兼容，而是区分原件与独立机器适配工件。

## 4. 原版 YAML 代发布的机器可核验规则

- 对锁定的 OpenAMSM 基线列出完整 YAML closure，逐文件按原相对路径复制为**不变的字节流**，包括 CRLF/LF、BOM、注释、YAML key 顺序、alias 与文本表述；禁止 YAML Parser load/dump、OpenAPI generator 再导出和 format。
- 确认发行包里对应路径的 byte length 与源一致，并用逐文件 `cmp` 或二进制相等比较 + Git blob ID / 文件 digest 做证据（不新增生产 Host Artifact 身份/Trust Registry）。任何差异立即发布失败；不能通过转换成同一 JSON 值证明“等价”。
- Manifest 可在独立文件中记录 OpenAMSM repo SHA、源码根、原始路径、文件身份、3GPP 版本判据和版权/授权来源；**不在 YAML 头追加版权或版本文本**。
- OpenAMSM 支持的版本更新时构建**新的**正式发布快照，旧 Package 不覆盖；禁止不同 OpenAMSM commit 的 YAML 混拼为单一源快照。业务 Package/Compiler 依赖只能 pin 某一确定性 Snapshot，绝不解析动态 latest。
- 保留原版 YAML 的所有相对依赖引用；发行包树布局导致引用失效时必须改变外围打包层级，**绝不能重写 YAML `$ref`**。

## 5. Event / SKILL / Codec 分阶段边界

| 阶段 | 输入 / 责任 | 结果和失败语义 |
|---|---|---|
| T0 Event Plugin | OpenAMSM 受支持的 Nsmf SBI、JSON 与 multipart/Content-ID；Stage 原始 N1/N2；仅最小 0xC9 / 0xD1 / 0xD4 判别 | Event Schema 已验证，raw artifactRef Host-owned；出错 fail-closed，无 Owner mutation |
| T1 Skill 选择 | 仅已存在的 Event 类型、SBI 字段/路径、最小 discriminator 与 Skill-owned `requestSchema`、`when` | 不允许调用 Codec；只有完整 T1 字段才能作为 Request 必填；无候选拒绝 |
| T2 已选 Skill 的 Procedure | 已发布的 Codec READ Capability、授权的 artifactRef/slot、正式 Provider Result Schema | 解码 NAS/NGAP 的受验子集，原 bytes 保留；字段先通过 Output Schema 再作为显式 SourcePath；失败不进入 Owner mutation |
| T3 Owner/Observation | T2 的有效 Result + Host Context / Owner READ | Owner 权威状态和 Receipt/Proof 是唯一 Commit 判据；模型文本或 Codec 结果不是 Proof |
| T4 Continuation | 原 Run 代际/身份、合法 N1/N2 完成消息 | 续跑原 Run，不重新选择或求值 when；不接受跨 Run 或迟到串包 |

| 业务入口 | T1 已验证字段 | 仅 T2 才能得出的字段 | 强制检验 |
|---|---|---|---|
| Create `PostSmContexts` | 实际 SBI JSON 已携带的 DNN / S-NSSAI / PLMN / pduSessionId 等（是否存在由固定 OpenAMSM fixture 逐字段确定）+ N1 slot | N1 内 PSI/PTI、PDU Session Type、SSC mode | 不能在 T1 必填 NAS-only 的 requestedPduSessionType / requestedSscMode；T2 比较 N1 与 SBI 的 PSI/类型冲突，不能伪造默认值 |
| Modify `UpdateSmContext` / 0xC9 | SBI 元数据、资源/原请求 identity、最小分类与 N1 ref | 修改内容及 QoS；由正式 Codec/Owner READ 输出 | 未资格化的 Modify profile 不能用 0xD1 的首批成绩代替 |
| UE Release / 0xD1 | ABI/SBI resource + 0xD1 discriminator、N1 ref | 首批 Release Request PSI/PTI | `2e 05 01 d1` 是历史已测候选字节，不是当前正式 Tool 发布 |
| N1 0xD4、N2 Setup/Modify/Release Response | 只供原 Run continuation correlation，不选新 Skill | 相应完成证据 | 必须核对原 Run generation、PSI/PTI、N2 类型；无重复 mutation |

NAS/NGAP 的精确数据类型由 Provider 正式 Output Schema 发布，并需对照当前 OpenAMSM 版本证据；**不能**因 A 层 YAML 存在，就推断这些类型已进入公共 Adapter B。T1 的 requestSchema 根仍属于 Skill 本身，`when` 无 Tool 权限。

## 6. Compiler / Studio / Bundle 边界

- CA-SL 1.6.0 G.4 允许的 JSON Schema 有限 Profile 不变。未经批准的原版 3GPP YAML（A）不得进入 Compiler 的 G.4 `$ref` 闭包；B 作为**独立生成/维护的类型适配包**，必须有获批准的单独 Package identity、schemaId、发布 Golden 与 Source Lock，并明确 Adapter 类型不等于官方标准原版。
- 只有 B 的 schemaId 被正式发布并经 Skill dependency Alias 明确声明，Skill-owned Request root 才能引用 B 的字段类型；Host Context SR-030 只通过 `Contract.contexts` 引用。Compiler Link 必须验证精确闭包、来源、版本一致性与阶段可用性，Schema-only 0/0 不产生 Capability Grant。
- Codec Result Schema 属于 Provider Package 的 Output Schema，固定消息 profile 与本次 OpenAMSM 支持基线；若引用 B，则固定版本/来源及字段可表示性，不通过原版 OpenAPI 的多态结构自动猜类型。
- Studio 原样展示原版 YAML 以方便查标准；B 的类型才可用于 Schema Explorer/SourcePath/Compiler 辅助，不得修改 A 或把 A 标成 Tool。Bundle 对 A 的出处可记录，但业务运行强依赖的是实际使用的 B/Provider/Host Context/Owner 的正式版本快照。
- 新 1.6.0 Compiler / Publisher 机器 API 未冻结时，任何 wire field、Package ID / SemVer / schemaId / Backend handler 不得由 Harness 推断；相应产品 AC=BLOCKED/NOT_RUN。

## 7. Golden / AC 与阶段独立性

| ID | 要求 | 当前证据 |
|---|---|---|
| DS-3GPP-01 | 以 OpenAMSM 受测 commit 固定 TS29.502 源 YAML + transitive refs；原/发行逐文件字节和路径完全一致；修改一个空格/注释/换行也必须失败 | 需要正式 Source Lock，NOT_RUN |
| DS-3GPP-02 | 仅发布 A 原版时，不伪称它是 G.4 Schema-only；若业务需要 B，验证 Adapter 明确为另包/另文件，与 A 不同文件路径/身份；无 B 时 Compiler Link BLOCKED | 未发布 |
| DS-3GPP-03 | B 仅采用 CA-SL 已准的 G.4 Profile；源带 `#/components`、`oneOf` 或 `format` 时不得修改 A；Adapter 转换必须保留来源/明确丢失与失败门槛 | Adapter Owner/Golden 待定 |
| DS-3GPP-04 | Create Request 选择不含 NAS-only 需解码字段；T2 正确解码后显式使用；SBI 与 N1 冲突拒绝，Owner mutation=0 | 业务作者+Codec 未发布 |
| DS-3GPP-05 | 0xD1 Release Request 正例、截断/0xD4 非该 profile；0xC9 Modify、Create 与 N2 分别资格化，不混称全量 | Provider 未发布 |
| DS-3GPP-06 | Schema-only B 0/0、Codec READ 1/1、总 Provider 3/3；重复 schemaId/跨 OpenAMSM 版本/缺 Bundle/错误 T1/T2 SourcePath 拒绝 | Compiler/Studio/Bundle NOT_RUN |
| DS-3GPP-07 | 无 Codec 的 Skill / no-decode 路径不被公共原版发布阻塞；必须 Codec 但缺正式 Provider 则仅该子阶段 BLOCKED | NOT_RUN |

SR-009 Event Plugin 和 SR-010 Host Artifact Channel 可按直接依赖独立评审/实现；原版 YAML 代发布 A 亦可独立验收。B 类型适配、C Provider Codec、业务 Skill Bundle 与 E2E 必须逐级独立冻结和签认，不让产品依赖反向阻塞原件代发布，也不得提前提供代码实施 Goal。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 建立 3GPP 公共 Schema、T0～T4 与 Source/Codec/Compiler 分层候选 | 修正 Create 选择前解码循环 | IR-009；Issue #47 |
| 2026-11-27 | 0.2.0 | ChatGPT / GPT-6 | 全文 | 按最新裁决将 OpenAMSM 支持的版本作为唯一来源，冻结 YAML byte-for-byte 原样代发布；分离 A 原版与 B 可选 G.4 Adapter/Schema-only，NAS/NGAP 不伪造 YAML | 禁止任何 3GPP YAML 变更，避免为 Compiler 适配而改标准 | Issue #47；SR-031/026/013 |
