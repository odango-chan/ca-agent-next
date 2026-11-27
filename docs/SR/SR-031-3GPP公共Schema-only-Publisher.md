# SR-031：3GPP 公共 Schema-only Interface Package Publisher

> 文档类型：软件需求（SR）  
> 版本：0.1.0  
> 日期：2026-11-27  
> 状态：**DRAFT / REVIEW_REQUESTED（中央设计可独立评审，实施非 READY）**  
> 上游：[IR-009](../IR/IR%20总登记册.md#ir-009)；[设计 Issue #47](https://github.com/odango-chan/ca-agent-next/issues/47)  
> 目标实施仓：**odango-chan/ca-skills（EC01）**；设计/治理仓：ca-agent-next  
> 核心设计：[3GPP 公共 Schema 发布与 Skill 分阶段消费](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)  
> 全局评审范围：继承根 Agent.md review_scope；Demo/Development；无代码/产品验收主张

## 0. 目标、范围与发布责任

为 CA-SL **1.6.0 ONLY** 生产可被 Skill-owned `requestSchema`、Provider Codec Result Schema、Compiler/Bundle 和 Studio **精确引用**的 3GPP 公共 Schema-only Interface Package；0 Capability、0 Callable，不引入运行时 Tool、独立 Registry、第二 Provider 或自动版本迁移。Package 的公开 Schema 类型受限于当前语言 JSON Schema Profile，标准来源真实可追溯而非复制整份 OpenAPI/NAS/NGAP。

本 SR 的 **ca-skills** 实现必须另建实施 Issue、固定受审的中央设计 SHA、正式 CA-SL 1.6.0 Package Schema/Golden 后才可启动 Harness。设计 Issue #47 / 本次中央文档 PR **不是**实施授权。

## 1. Source / Output 决定表

| 输入 | 固定来源与方法 | 公共发布产出 |
|---|---|---|
| SBI / CommonData | TS 29.502 `TS29502_Nsmf_PDUSession.yaml` 与明确引用的 29.571 类型；Demo 初始取 `env-openamsm@dc83ccbf` `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`；逐文件记录源 SHA/blob/3GPP 版本 | 经审查的 SBI 规范化输入字段类型、事件选择用标量/闭合对象、Content-ID/slot profile；不是原始 multipart Schema 的复制品 |
| NAS 5GSM | TS 24.501 + `ca-client-tools` PR #39 的已复核 bytes（正式产物必须重新 pin 受测 Source） | 指定消息结果的类型定义；首批 0xD1 Release Request PSI/PTI；Create Establishment、Modify 0xC9 后续受资格化子集 |
| N2 NGAP | TS 38.413 及匹配的 29.502 N2 information-type 定义 | **仅在** codec/fixture/ASN.1 字段与来源明确、正负向资格化之后导出相应子集；初期无 NGAP 全量承诺 |
| 类型投影与构建 | CA-SL 1.6.0 JSON Schema Profile；Package Schema 由 ca-skills + Compiler Owner 冻结 | 每个导出具备独立稳定 $id、闭合 JSON Schema、明示完整 ref closure、sourceMap、fixture/expected output、Package ID、数字 SemVer、languageTarget、不可变 snapshot identity |

不得把缺失的 Machine ID、SemVer、schemaId、真实 Publisher 路径/argv 或 3GPP 字段编造成正式规范。Source Lock 无法确定或上游特征不能无损或明示有损投影时标记该类型 `BLOCKED`，其他已确认类型可独立设计/验收。

## 2. 开发者必须遵守的契约

1. `requestSchema` 根由 Skill 作者在其 `assurance/schemas/` 中维护，根闭合；通过显式 3GPP Common Schema-only dependency + **完整导出 $id** 的 $ref 重用共享类型；禁止使用 fragment、模糊 alias、未固定标准版本、运行期网络解析。
2. 公共包为 Schema-only：**0 Capability / 0 Callable**。普通 Provider / Owner 功能包仍须满足 Skill-facing Capability↔Callable 严格双向 1:1。Codec Tool 的 READ Capability 和其结果 Schema 由 **ca-client-tools / SR-026** 负责，本 SR 不重发布 Go Codec。
3. Provider Codec Result 引用同一精确 3GPP Schema snapshot；必须由 Producer 逐字段固定类型/nullable/enum、来源标准、消息 profile、有效负例。代码私有 struct 与公开 Schema 不可互相替代。
4. Compiler Check/Build/Verify 在闭包中区分 Schema-only dependency roots 和 Capability Binding；每个 `$ref` 解析到可信唯一 schemaId/snapshot；Request Schema 与 Codec Output Schema 的类型检查不能在运行时猜测或绕过。
5. 3GPP OpenAPI 不可直接按未受支持的 `#/components`、`$defs`、`oneOf`、`format` 等元素注入新 1.6.0 JSON Schema Profile；任何转换必须可追溯且拒绝丢失约束/类型。
6. 技能选择 `when` 不调用 Codec；T1 只允许来自已验证 Event 的字段，NAS-only 的 `requestedPduSessionType`、`requestedSscMode` 由选中 Skill 在 T2 的 Codec READ 获取，再交给 Procedure 参数和 Owner 校验。0xD4 仅用于原 Run continuation。
7. 只支持 CA-SL 1.6.0；无 v1alpha5 兼容包、旧 Compiler DTO/Artifact/Bundle 或自动迁移。

## 3. 交付物与独立产品 AC

| AC | 可复验输入 / 预期 | 所属产品阶段 |
|---|---|---|
| AC-031-01 | 冻结 TS 29.502 / 29.571 / TS 24.501 / 38.413 实际用到的标准 release、source SHA/blob、依赖文件闭包；建立字段级 sourceMap；缺文件、版本漂移和规范断点失败 | Source Lock |
| AC-031-02 | 发布 1.6.0 Schema-only Package：0 Capability / 0 Callable、非空显式 Schema exports、闭合 $id 和 Package SemVer；重复构建资产/快照一致 | Publisher |
| AC-031-03 | 源中有 `#/components` / `oneOf` / `format` / recursion 时必须拒绝原样导出；仅合法 G.4 投影通过；未支持 Type 单独标 BLOCKED | Projection |
| AC-031-04 | Skill-owned request root 引用已声明公共 $id 并经新 Compiler Link，固定 closure；缺依赖、同名不同版本、缺 export、漂移、片段引用失败；0/0 不生成 Capability Binding | Compiler consumer |
| AC-031-05 | Provider READ 的 0xD1 固定 byte 向量 `2e 05 01 d1` 匹配公共结果字段型；截断、不同 0xD4 消息 profile、非法 PSI/PTI 或未知字段拒绝；**外部 Provider 未发布时 BLOCKED** | Provider consumer |
| AC-031-06 | Create 选择不要求 NAS 解码后字段，选中后 Codec READ 才提供 PDU Session Type / SSC mode；Modify 0xC9 与 N2 profile 仅按正式资格化范围消费 | Skill author / E2E |
| AC-031-07 | Studio Schema-only 只显示 Schema 类型，绝不当作 Tools/Operations/Capabilities；Bundle 完整锁定 schemaId/snapshot，拒旧版 / 动态 latest | Studio / Bundle |

实际命令、受测 SHA、测试数量、Golden 固定位置及发行包下载/读取入口必须由 **ca-skills Publisher Owner / Compiler Owner** 在新实施 Issue/签认 Release 填入后，才能判定对应 AC 具备实施启动条件。不可用 `echo PASS`、历史 v1alpha5 测试或模拟发行包替代。

## 4. 依赖、分阶段 READY 与非目标

- **设计阶段**：本 SR 的 Publisher 输入/输出、来源、失败路径和 AC 已足以提交独立技术评审；独立批准尚无，主状态 DRAFT。
- **实施阶段**：需要独立 ca-skills 实施 Issue 和目标仓授权、正式 CA-SL 1.6.0 Package Schema + Schema-only Publisher API/Schema Golden；缺失标 `BLOCKED_EXTERNAL_INPUT`。已冻结标准文件的 Source Lock 与转换可作为独立子阶段评议，不把其通过当作全包 READY。
- **消费阶段**：SR-013/027 必须支持外部 Schema-only dependency 和 Request/Output Schema closure；SR-026 必须按独立 Provider Owner 正式导出 Codec READ；SR-010、SR-011、SR-016 不得以本 SR 静态设计替代产品运行。
- **非目标**：不实现 3GPP 全量标准编译器、NAS/NGAP 全量 decode、生产 Trust/Signing、共享在线 Schema Registry、兼容层、独立 Codec Manager 或由模型自由生成 3GPP fields。

## 5. 交接记录（待 Provider / Publisher Owner 填报）

| Owner | 尚缺正式输出 | 阻塞的 AC |
|---|---|---|
| ca-skills | 1.6.0 languageTarget、Machine Package Schema / Golden、Package ID / SemVer、Schema exports $id、Publisher 确切 argv、Source Lock fixture | 031-02～04/07 |
| ca-skill-compiler | 1.6.0 Build/Verify API、Schema-only 依赖/跨 Package $ref/Output Schema Link 的正式行为与拒绝诊断 | 031-04/07 |
| ca-client-tools | 0xD1 Codec READ Capability / 唯一 Callable、Input/Output Schema、与公共 Schema snapshot 的匹配、正式包 / handler / fixture | 031-05/06 |
| ca-skills MAS 作者 | Create/Modify/Release 重写后的 Skill-owned requestSchema + Procedure Codec READ source mapping、1.6.0 Bundle | 031-06/07 |

所有缺失保持 `NOT_RELEASED / NOT_RUN / BLOCKED`，严禁下游 Harness 自行命名或假定已冻结。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | ChatGPT / GPT-6 | 全文 | 新增跨仓 3GPP Schema-only Publisher SR，明确 CA-SL 1.6.0 Producer/Consumer、测试、发布门槛 | 消除发布物责任缺口及选择前解码循环 | IR-009；Issue #47；SR-010/013/026/027 |
