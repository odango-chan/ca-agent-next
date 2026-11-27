# SR-031：3GPP 公共 Schema-only Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.2.0
> 创建日期：2026-11-27
> 修订日期：2026-11-27
> 状态：DRAFT / REVIEW_REQUESTED；仅原版 YAML 代发布设计可先独立评审，CA-SL 类型适配与全产品实施仍 BLOCKED_EXTERNAL_INPUT
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：修改原版 YAML、擅定 3GPP 发行版、全量 NAS/NGAP 解码、兼容旧 CA-SL
> 上游：[IR-009](../IR/IR%20总登记册.md#ir-009)、[Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)
> 实施仓：ca-skills（EC01）；NEXT 为中央设计/追踪中心
> 权威设计：[3GPP 公共 Schema 与 SKILL 分阶段消费](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)

## 0. 唯一裁决与两个独立交付阶段

**本 SR 第一阶段只做 3GPP 原始 YAML 代发布，不是新规范作者，不负责调整/格式化/转换 YAML。** 公开版本必须等于冻结的 OpenAMSM 真实支持的 3GPP OpenAPI YAML 版本。原文件逐字节保持不变，源路径/层级及相对 `$ref` 仍有效。禁止替换成更“新”的 3GPP 标准版本，禁止将 OpenAMSM 不支持版本的 YAML 拼进去。

- **Phase A（原版代发布）**：`ca-skills` 复制 OpenAMSM 已使用的 YAML 及其依赖闭包，以只读 Source Bundle 方式发布；每份文件 bytes、编码、换行、注释、空白、内容、目录结构完全相同。可在原件之外附来源锁和清单。Source Bundle **不自动是**符合 CA-SL 1.6.0 G.4 的 Schema-only Interface Package。
- **Phase B（可选、单独设计评审和发布）**：若 1.6.0 Skill/Compiler 确实需要静态公共类型，另创建**不同文件/目录/Package identity** 的、显式标识 `CA-SL Adapter` 的 Schema-only Interface Package：0 Capability / 0 Callable、非空 G.4 Schema exports、固定 A Source Lock 和字段来源。Adapter 不覆盖 A 的 YAML，不能宣称 Adapter 等价于 3GPP 原版，也不能为了适配而改 A。机器 Package Schema、schemaId、命令、Golden 尚未发布；此阶段 BLOCKED_EXTERNAL_INPUT。

**保持 SR 编号/文件名**以兼容中央现有引用，但 Scope 以本节最新决定为准：不再把未经转换的原版 OpenAPI YAML 误报为可供 Compiler 直接 `$ref` 的 Schema-only 导出。

## 1. 唯一版本来源与 Source Lock

Demo 初始来源线索：`env-openamsm@dc83ccbf` 的 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`。正式实施时必须由 OpenAMSM 仓 Owner 确认**实际受测/构建使用的 commit 与标准目录**；不能仅凭 `r19-` 目录名断定正式 3GPP Release、不能默认该历史 SHA 是当前最新支持版本。

Scope 仅包含该 OpenAMSM 真实使用的标准 YAML 与为其相对引用所必需的 YAML 依赖闭包，包括关联的 CommonData 等文件；所有文件必须来自**同一受验证的 OpenAMSM 源快照**。NAS TS 24.501、NGAP TS 38.413 原文不是因为 SBI TS29.502 YAML 存在就自动有对应原版 YAML；仅当 OpenAMSM **确实分发**相应 YAML，才可列入 Phase A。不得人工创造“标准 NAS YAML”。

Source Lock 每个文件的独立记录必须包括：源仓和固定 commit、原路径、发行路径（保持相对结构）、原始 Git blob identity/byte length/byte digest、3GPP 标准标识与版本元数据取证位置、直接及传递的相对引用列表、OpenAMSM 代码/构建引用证据；一个不可变 Release 只能对应一个 OpenAMSM support baseline。源升级必须发新 Bundle，旧版内容不得覆盖。

## 2. Phase A 实施硬规则

1. 使用二进制复制，不 load/dump、format、normalize、re-encode、newline conversion、修改 YAML header、重排 key、替换 `$ref`、生成“内容等价”的 YAML。
2. 逐文件保留原名称和相对目录树；若发布格式需要目录包装，包装层在树外实现，内部 YAML path/ref 不改。
3. 所有原件和发布物逐文件比较 byte length 与 `cmp` 结果；可以用 Git blob ID/校验摘要佐证，**不额外创建 Host Artifact 身份体系**。内容只差一个空格、注释、CRLF、BOM 或结尾换行均失败；不能只比较解析后的 JSON/YAML 结构。
4. 来源清单、许可证/来源告知、Package 元数据在**单独**文件；不得写入任何原始 YAML。若上游要求遵守许可证/署名，应原样保留原件并将外围声明分开。
5. 发布前确认 OpenAMSM 真实支持范围的版本/完整依赖闭包；缺明确证据不得用随机上游 3GPP YAML 代替，也不得选择邻近 release “凑齐”。
6. Source Bundle 原版 YAML 只读展示；没有 Phase B 时 Compiler 不 Link 它作为 G.4 Type Package，不允许 Skill 在 requestSchema 写一个指向原版 OpenAPI 的直接 $ref 然后声称有效。

## 3. Phase B Adapter（独立可选，不重写 Phase A）

- 仅当正式 ca-skills / Compiler Owner 确认新 1.6.0 Interface Package Schema / schemaId / Golden / Build DTO 后，才能实施。Adapter 应当是新的、公开标识为非标准原件的 JSON Schema Profile 与映射清单；**Adapter 不是 3GPP 官方 YAML**。
- G.4 受限 JSON Schema 不支持 `#/components`、`oneOf`、`format` 等，不能因此删除/改写原版 YAML；只有明示来源、明示模型限制、完整 guard/负例并通过审查的独立适配类型才能进 Compiler。
- Adapter Package 必须 0 Capability / 0 Callable，至少 1 个正式 Schema export，固定 Source Lock；只能在 Skill-owned requestSchema 中通过声明的精确依赖与完整 $id 作为**字段类型**引用，Root 仍是 Skill 自有。Host Context SR-030 只经 `Contract.contexts` 引用，不混合。
- Codec 的 NAS/NGAP Result Schema 由 `ca-client-tools` SR-026 发布。Provider 如消费 Adapter 的共享类型，须与同一 OpenAMSM 支持基线严格匹配；不能假定 TS29.502 SBI YAML 自身包含 NAS 5GSM 结构。
- Phase A 的 READY/VERIFIED 不能转换成 Phase B、Compiler、Codec 或全系统 PASS。单一 Language Target 1.6.0，不保留 v1alpha5 迁移/兼容层。

## 4. AC 逐阶段验收

| AC | 固定可复验对象、正反向断言 | 门禁 |
|---|---|---|
| AC-031-01 | 固定真实 OpenAMSM commit、所采用的 TS29.502 等 YAML 文件与 transitive ref 闭包、实际受支持版本/构建引用证据；拒绝跨 commit 混用、臆测 3GPP Release 和遗漏的相对依赖 | Phase A Source Lock；尚待正式 Owner 证据 |
| AC-031-02 | 正式发行 Source Bundle：对每一原文件 `cmp` bytes、length、ref 目录结构完全一致；正例和变动单个空白/CRLF/注释/字段反例均可复验 | Phase A 发布；NOT_RUN |
| AC-031-03 | YAML 不经 Parser 重新序列化，不做 schema “标准化”，外围 source-lock/manifest 与 YAML 原件分离；反例任何修改一律发布失败 | Phase A immutability；NOT_RUN |
| AC-031-04 | 如启动 Phase B，单独发布 G.4 合法的 Adapter Schema-only Package，0/0、非空 Schema exports，明确其非标准原版 identity 与 Source Lock；直接以 A 作 Compiler $ref 的负例失败 | Phase B；BLOCKED |
| AC-031-05 | Provider 正式 0xD1 Codec READ 的 Output Schema/fixture 对齐采用的 OpenAMSM 版本，原始 YAML 未动；截断或 0xD4 非该 profile；不以原版 SBI YAML 充当 NAS 解码 Schema | 依赖 SR-026；BLOCKED |
| AC-031-06 | Create T1 不必填仅存在于 N1 的 PDU Session Type/SSC mode，T2 读取正式 Codec Result；Modify 0xC9/Release 0xD1 与 T4 0xD4/N2 continuation 不混同 | 作者/Runtime；BLOCKED |
| AC-031-07 | Studio 只读展示 A 原件；B 仅在正式发布后可作为独立 Schema-only 依赖被 Compiler Link；缺版本快照/旧版/跨 OpenAMSM 源混用失败 | Compiler/Studio/Bundle；BLOCKED |

**测试命令与产物身份**：在独立 ca-skills 实施 Issue 中固定真实 checkout SHA、源路径、source YAML 数量、目标 ZIP/目录、逐文件 `cmp` 执行命令与结果、负例、发现数、正式发行入口；不接受空测试、虚假成功。此处仅给出必须验证的行为，不伪造尚不存在的 Publisher CLI/Golden。

## 5. 关联 SR、当前状态、实施门槛

- [SR-026](SR-026-Codec公开工具发布.md) 仍由 ca-client-tools 独立实现 Codec READ，首批 0xD1。Create/Modify 需要其后续受资格化消息 Profile，不受本 SR Phase A 成功替代。
- [SR-010](SR-010-OpenAMSM%20工具插件与按需编解码集成.md) Host Artifact Channel 可独立模块验收；只有选定 Skill 的 T2 才调用 Codec，Event Plugin 不完整解码，原 bytes 留存。
- [SR-013](SR-013-Compiler已检查when与发布产物.md) 的 AC-013-07 仅在 B 取得正式 Adapter 产物后 Link；A 原版 YAML 不得进入受限 G.4 路径。
- [SR-027](SR-027-技能Bundle构建与发布.md) 对 B 与 Provider 的正式依赖闭包 pin；A 可作为只读标准参考资源独立发布。

**设计评审现在可审查 Phase A 原样代发布原则和明确的失败矩阵**；完整 SR 实施主状态 **DRAFT**。任何真实实施都要求独立 ca-skills Issue、固定本设计 SHA、OpenAMSM 源 SHA、目标仓授权和正式 Publisher 决策；Phase B/C 依赖机器 Package/schemaId/Golden/Provider Release，均 BLOCKED_EXTERNAL_INPUT。没有 READY、VERIFIED 或系统 E2E 声明。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 创建公共 3GPP Schema Producer 与 Compiler/Codec 消费 AC | 修正入口/解码阶段循环依赖 | Issue #47 |
| 2026-11-27 | 0.2.0 | ChatGPT / GPT-6 | 全文 | 将 OpenAMSM 实际支持版本作为唯一 Source Lock，原版 YAML byte-for-byte 代发布，适配 Schema-only 另包/另文件；修订 AC-031-01～07 阶段门槛并补足 CI 标准文档头 | 落实“不修改 YAML，仅代为发布”的最新裁决，防止假冒标准原件 | Issue #47；IR-009；SR-026/010/013/027 |
