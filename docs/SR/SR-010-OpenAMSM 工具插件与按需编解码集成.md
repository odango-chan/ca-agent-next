# SR-010：OpenAMSM 工具插件与按需编解码集成

> 文档类型：软件需求（SR）  
> SR 版本：0.3.0\
> 状态：整项 DRAFT；阶段 READY（本仓 Host Channel 设计）；AC-010-03 BLOCKED_EXTERNAL_INPUT（外部 ca-host.artifact-store/v1 仍含 SHA-256 约束，须先修订为无 hash 的 Demo channel）；其他 Host Channel AC 按各自阶段独立验收。  
> 下一步：仅实现 Next Python Host ArtifactStore/Channel 与 no-decode 路径。06a 等真实 Importer/Catalog/Runtime 三层入口，09 等固定共享 fixtures 和联测；06b/07/08 等正式包。  
> 阶段依据：[独立评审 #74](https://github.com/odango-chan/ca-agent-next/issues/74#issuecomment-7210244694)，评审 Head `ee73ad48f9cf4132561f7a72065086ef00bb3606`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。  
> 工作项：[阶段工作项 #94](https://github.com/odango-chan/ca-agent-next/issues/94)。
> 创建日期：2026-11-25  
> 修订日期：2026-11-27\
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Plugin平台设计说明书](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md) v0.3.7 §8；[Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) v0.4.4 §6.2/§6.5/§8.1；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.5 §5～6；[公共契约与所有权规范](../规范/公共契约与所有权规范.md) v0.2.7 §2、5、6、8、10\
> Acceptance：OM-04、OM-10、OM-13（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查唯一 Plugin Manager 的 Provider 工具路径、Host Artifact Channel、Codec READ、Owner 效果/Proof 与 Scope fail-closed。
- **已知依赖与未验证项：**旧 Provider 11 READ Callables 仅作历史审计；新版公开 Capability↔Callable 一对一需上游重发，不能宣称代码已实现。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

## 1. 目标

通过唯一 Plugin Manager 接入 ca-client-tools，并在 Next Python Host 实现 Host-owned ArtifactStore 与冻结的 ca-host.artifact-store/v1 channel，使 Skill 能通过普通 Tool Action 按需调用 Provider/Codec Operation。

## 2. 实施范围

- 将 ca-client-tools provider/v2 适配在统一 Plugin Manager 的 tools Extension 内，不增加第二个 Provider Manager。
- 在 Next Host 实现 Host-owned ArtifactStore 和 `ca-host.artifact-store/v1` loopback HTTP/1.1 channel；Host 在 Provider `initialize` 中传入闭合 `artifactChannel`，由 Provider 使用 GET 输入 / POST 输出交接原始 bytes。
- Artifact reference 使用 Host 生成的随机 opaque token，并绑定 invocation、direction、slot；不包含路径、URL、mediaType、size 或 digest。
- Provider `artifactSlots` 必须来自可信 Backend Catalog；原始 bytes 不进入 NDJSON、不使用 Base64、不暴露任意本地路径。
- 按 Demo channel 完成原始 bytes 流交接、长度/数量配额、超时/取消、过期清理和输出原子发布；不计算或校验 SHA-256、checksum 或 digest。
- 缺少 `artifactChannel` 时 artifact-bearing binding 必须 `NOT_CONFIGURED`，并在远端 SBI I/O 前拒绝。
- Codec Decode/Encode/最小分类操作必须先发布在权威 Tool Interface Package；Skill 需要结构化协议字段时才调用 Codec Tool。
- Codec 输出 JSON 投影或新 Artifact Reference；原始 Artifact 不被替换。

## 3. 非目标

- 不把当前纯 Go codec library 误报为已发布 Agent-callable Tool。
- 不创建独立 Codec Plugin/Manager，不在 Host/Event Plugin 复制编解码实现。
- 不宣称未验收的全量 NGAP 支持。
- 不实现 content-addressed artifact identity、去重、SHA-256 / checksum / digest 校验、签名、Trust Registry 或生产级 package integrity；只做 opaque ref、Invocation/slot 绑定、长度/数量配额与原子发布。
- 不允许 Provider 自行选择文件路径、远端 URL 或凭据。

## 4. 依赖与分阶段门槛（遵循 SR 管理规范 §6.1）

| 依赖类型 | 权威输入 | 适用门槛 |
|---|---|---|
| 设计 | F03.05/ F05 正式 ca-host.artifact-store/v1、SR-029 1.6.0 Capability Binding | Host Artifact Channel 与 Provider Tool/Codec 不能混成双 Provider Manager |
| 实施 | SR-003 单 Plugin Manager、SR-007 Action Boundary、SR-009 Plugin staging；Provider v1.2.0 旧 API 只作 Host channel 历史互操作参考 | Host ArtifactStore / Channel 可独立实现，外部新 1.6.0 Capability 导出不阻塞本 Host 子阶段 |
**Demo 完整性边界**：现有 `odango-chan/ca-agent` `ca-host.artifact-store/v1`（commit `2c0b07f2eaff3bc1020bfc6775ef9bf09e3052ae`）仍规定逐 Artifact SHA-256，不能原样复用。该外部契约必须先修订为无 hash 的 Demo channel；在此之前 AC-010-03 保持 BLOCKED_EXTERNAL_INPUT，不得由 Harness 自行兼容或绕过。
| 模块验收 | Host channel v1 已冻结 conformance fixtures；SR-026 新 Codec Capability 发布包 | AC-010-01～05 用测试 Host/Provider；09 使用真实 Go Provider 与 Python Host，无需真实 NF；06a 本地拒绝，06b/07/08 依赖正式 1.6.0 资产 |
| 系统 OM | OM-04/10/13 与真实 NF/Owner | 不作为 Host Channel 模块 READY 前置 |

**设计评审与实施 READY 独立判定**：本 SR 的功能职责、已知目标契约、失败路径和下面每项模块 AC 足够完整即可请求设计评审；不得要求“全部前置 SR VERIFIED”作为统一前置。实际实施按本次 Scope 逐阶段检查所消费的已发布能力；缺失时仅相应 AC 标记 BLOCKED/NOT_RUN，系统 EX/OM 不倒灌模块门禁。Owner/Provider/Compiler 的未知机器标识、Schema 和 API 只能由对应 Owner 正式发布，Harness 不得推测。新 Skill/Artifact/Runtime 接口只接受 CA-SL 1.6.0 / Capability-first，不提供旧版兼容。

## 5. 独立模块验收条件（正例、反例与证据）

| 模块 AC | 固定输入/操作 | 预期、诊断与隔离 |
|---|---|---|
| AC-010-01 | 通过唯一 Plugin Manager 初始化 Provider Tools Extension；配置缺失/非法 | 无第二 Manager；缺 channel 可初始化但 Artifact Binding NOT_CONFIGURED；非法配置 PROVIDER_CONFIGURATION_INVALID，远端 I/O=0 |
| AC-010-02 | Host 生成 opaque artifactRef 与同一/跨 Invocation、direction、slot 的读取 | 合法引用通过，跨边界/过期/路径泄漏拒绝，token 不编码文件/URL |
| AC-010-03 | Provider GET 输入/POST 输出正确二进制与 mediaType、Content-Length、长度/数量配额 | 输出原子发布，字节流与交接长度一致；slot/schema/size 不符不形成可读产物；不计算或校验摘要 |
| AC-010-04 | 取消、超时、Provider 退出、部分写入、配额超限 | 所有 staged outputs 清理；未完成 Artifact 不可读取；无重复 Owner mutation |
| AC-010-05 | Codec 未发布、Host 不需要 Decode、Codec 必需但不存在 | no-decode 路径不触发 Codec；必需 Codec 未发布只阻塞对应 AC，不冒充已发布能力 |
| AC-010-06 | 06a 本地旧包拒绝：先通过真实 Importer 测旧 Artifact 拒绝；再以测试专用 fixture **绕过 Importer**，直接构造含旧 Artifact 的 Catalog entry/Resolver input；再直接构造旧 Run/旧 Callable-only Binding 注入 Runtime Action Boundary。06b 在正式 1.6.0 Package 与 Bundle 上按已 Link 的 Capability 分发 | 06a 每一层单独记录输入和计数：Importer candidate=0；直注 Catalog/Resolver 不得产生可选 candidate；Runtime 不得建立 Scope/dispatch；每层 Provider IPC=0。Resolver 与 Runtime 子例不得复用“Importer 已拒绝”的同一结果冒充独立测试。非法 selector 在后端 I/O 前拒绝；06b 核对唯一公开映射、合法路由及 Scope；缺正式输入时 06b BLOCKED，单独 06a 不能使整项 PASS |
| AC-010-07 | SR-026 正式发布的 DecodeNAS Capability 与单消息 0xD1、截断/错误类型 | 正常 Decode 输出结构化 JSON 且原 bytes 保留；负例 fail-closed；未发布时 BLOCKED |
| AC-010-08 | 1.6.0 Bundle 对已导出 Codec READ Capability 做真实 Runtime Tool Action | 必须经统一 Action Boundary + Provider channel；所需 new Package/Runtime Artifact 缺失时 NOT_RUN |
| AC-010-09 | 同一 conformance fixtures 的 Host Python / Provider Go 联合测试 | 准确记录受测 SHA、请求/响应、GET/POST 字节、Slot、配额与错误映射；另测只有 Provider ok=true、HTTP 2xx、IPC 成功或模型成功文本，及 Receipt 的 Scope/Invocation 不符：按 SR-007 AC-007-05/06 均不得记 COMMITTED，无重复 mutation；仅算 Host 子模块，不算 OM E2E |
| AC-010-10 | 固定 TS 29.502 `PostSmContexts.requestBody` multipart fixture；验证 `n1SmMsg.contentId`→N1、`n2SmInfo.contentId`→N2、`n2SmInfoExt1.contentId`→N2 Ext1 | 正例覆盖三组引用与命名 part / Content-ID / media type 一一对应；负例覆盖引用目标缺失、重复 Content-ID、错 slot、Content-Type 不符、malformed multipart；未引用或未知 part 不得交给 Codec，其拒绝 / 忽略由 ingress profile 明确规定；选定闭包外 refs 不触发 eager resolve。失败不得把错误 bytes 交给 Codec 或触发 Owner mutation；缺正式 Source Bundle / Consumer 时 BLOCKED / NOT_RUN |

### 5.1 实现落点、运行和取证

- 目标实现：`src/ca_agent_next/plugins/ 与 Host ArtifactStore`；测试入口：`python -m unittest discover -s tests -p test_artifact_channel.py -v`。若实现前目标仓文件/命令尚未存在，由具体实施 PR 在模块范围内创建并登记，**不得以不存在的脚本退出 0 或 0 discovered tests 作为 PASS**。
- 使用本 SR 明示的最小正负例与计数型测试 Provider/Mock；真实 Publisher、新 Compiler、Owner 收据、隔离环境等数据只从固定 SHA 的正式发布物读取。模拟输入能验证本地行为，但**不能替代**要求正式外部源的 AC。
- 每项 AC 单独记录受测代码 SHA、设计 Head、外部 Package/Schema/API 版本、命令、环境、测试数量、预期/实测、失败诊断与证据路径。未执行始终 NOT_RUN；输入缺失标记 BLOCKED；系统 EX/OM 必须用独立组合证据交付。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-agent-next |
| GitHub Issue | [阶段工作项 #94](https://github.com/odango-chan/ca-agent-next/issues/94)（限定范围） |
| 实施 PR | 未创建 |
| Commit | 无 |
| 实施状态 | NOT_STARTED |
| 验收证据 | NOT_RUN |

ca-agent-next PR #1 是设计基线 PR，不是本 SR 的实现 PR，不得在此标记实施完成。

## 7. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：初始分解；等待设计基线评审。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续发生语义变化时创建新的 SR 并引用本 SR，不覆盖历史要求。

## 8. OpenAMSM 原版 OpenAPI 3.0 Ingress 与 Codec READ 消费（IR-009）

- SR-031 发布 OpenAMSM 实际支持的原版 OpenAPI 3.0 Source Bundle；逐字节保留 YAML、路径和相对 `$ref`。它是标准源快照，不是 Interface Package，不导出 Capability / Callable，也不需要 Adapter。
- **T0 Ingress**：Plugin 按 pin 后的 TS 29.502 OAS 3.0 operation 解析 method/path/operationId，并将当前选定 surface 固定为 `requestBody`；`PostSmContexts` 的 `multipart/related` `jsonData` 引用 `SmContextCreateData`。只 lazy resolve 该选定 surface 的可达 refs，不全文件 eager resolve 其他 operation；当前闭包为 TS 29.502 / 29.571 / 29.510 NFManagement / 29.518 Namf Communication 四份原版 YAML。N1 / N2 / N2 Ext1 binary bytes 通过 slot / Content-ID / media type 验证后原样写入 Host ArtifactStore。
- Plugin 只负责协议入口验证、最小业务 discriminator 和原始 Artifact staging；不完整解码 NAS / NGAP，不在 Host 中维护第二套 SBI Schema。OpenAPI 3.0 Schema Object 按原生语义解释，禁止改写 YAML。
- **Content-ID 关联**：依据 CommonData `RefToBinaryData.contentId`，`jsonData.n1SmMsg.contentId` 必须匹配 `binaryDataN1SmMessage` 的 `Content-ID`；`jsonData.n2SmInfo.contentId` 匹配 `binaryDataN2SmInformation`；`jsonData.n2SmInfoExt1.contentId` 匹配 `binaryDataN2SmInformationExt1`。每个出现的引用必须且只能命中对应 slot；parts 的 Content-ID 必须唯一；引用目标缺失、重复 ID、错槽或错 media type 均拒绝。未被 JSON 引用的 part 不得交给 Codec；额外 / 未引用 part 的拒绝或忽略由选定 ingress profile 明确规定。Content-ID 值按标准 MIME 解析结果精确比较，不做自定义字符串变换。任何失败发生在 Artifact 发布与 Owner mutation 之前。
- **T1** 只按已收到的 SBI / 归一化 Event 字段选择 Skill；`when` 不调用 Codec。Skill-owned Request 根仍为 G.4，可经显式 pin 的 Source Bundle dependency 直接引用精确 OAS 3.0 `components/schemas`；Compiler 负责 dialect-aware Resolver（SR-013），Plugin 不做 Schema 投影。
- **T2** 由已选 Skill Procedure 调用 ca-client-tools SR-026 正式 Codec READ；Provider Output Schema 必须匹配 OpenAMSM NAS / NGAP 支持版本和已资格化 Profile。原始 N1/N2 bytes 保留，Codec Result 不是 Owner Receipt / Commit Proof。
- T4 的 0xD4 / N2 completion 只恢复原 Run，不创建新候选；核对 generation、PSI / PTI 和 N2 message type。
- 原 AC-010-01～05/09 Host Channel 可独立验收；AC-010-07 的 0xD1 仅证明首批候选库向量，不代表公开 Provider。AC-010-10 验证 OAS 3.0 选定 requestBody / multipart / 三组 Content-ID 到 N1/N2/N2 Ext1 slot 的映射和负例；未引用或未知 part 不得交给 Codec，其拒绝 / 忽略策略由 ingress profile 明确规定。同时验证原始 byte staging、精确 Source Bundle pin、T1/T2 SourcePath、SBI/N1 冲突、越权 artifactRef 与错误 generation。缺正式 Source Bundle / Compiler Resolver / Provider 时对应子项 BLOCKED / NOT_RUN。
- 无 Codec 依赖的 Skill 不得被强制解码；不能发明 Provider Machine ID / Output Schema、动态 latest 或旧版迁移。权威说明见 [EC01.3GPP 设计](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史条目未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-010 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史条目未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-010 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史条目未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-010 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史条目未细分 | 补齐 F03.05 Provider v2 消费设计，并更新 F05 / 公共契约引用 | Tool Interface / Owner Contract / Provider Runtime Bindings 已有独立中央设计 | Issue #12 |
| 2026-11-25 | 0.1.4 | 未记录（历史资料未提供） | 历史条目未细分 | 将 ca-host.artifact-store/v1 Host 端实现、Provider artifactChannel bootstrap/GET/POST、原子输出发布和共享 fixtures 纳入 Next 工具集成验收；同步 F03.05/F05/公共契约版本 | 当前 Provider v1.2.0 已有 channel consumer 与冻结契约，Next Host 仍需实现并独立验收；不能把 ca-agent Go Host PASS 计入 Next | Issue #12；SR-010、SR-015 |
| 2026-11-25 | 0.1.5 | 未记录（历史资料未提供） | 历史条目未细分 | 更新 F05 设计依据至 v0.4.1；明确 Mock AMF Codec C1 PR #86 不构成 Agent Tool/Provider Consumer，也不解除 Next Host Channel 的 NOT_IMPLEMENTED 门槛 | 对齐 Host ArtifactStore 与 Codec 的最新跨仓状态，避免把测试对端迁移误判为 Next 实施 | Issue #12；F05 v0.4.1；F06 v0.2.2 |
| 2026-11-25 | 0.1.6 | 未记录（历史资料未提供） | 历史条目未细分 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-010 |
| 2026-11-26 | 0.1.7 | 未记录（历史资料未提供） | 历史条目未细分 | §5 对齐真实 Provider v2，分别验收消费与外部发布 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.8 | 未记录（历史资料未提供） | 历史条目未细分 | 同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.9 | 未记录（历史资料未提供） | 历史条目未细分 | F03.05 v0.3.9 已包含 SR-015 设计移交，但本 SR Provider v2 wire contract 仍待设计门禁 | Issue #28；SR-003；SR-010 | Issue #28；SR-003；SR-010（其余历史关联未记录）；undefined |
| 2026-11-26 | 0.1.10 | 未记录（历史资料未提供） | 历史条目未细分 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.1.11 | 未记录（历史资料未提供） | 历史条目未细分 | 按治理 §6.1 拆分设计/实施/模块/系统依赖；补齐 AC-010-xx 正反验收 | 解除全局 VERIFIED 门槛与缺模块 AC 问题，避免 Harness 猜测/EX 倒灌 | Issue #12/#40；PR #46；SR 管理规范 §6.1 |
| 2026-11-26 | 0.1.12 | 未记录（历史资料未提供） | 历史条目未细分 | 同步本次 1.6.0 实质整改后的权威 Feature/Compiler 文档版本 | 保证 SR 新旧规范引用与固定审核 Head 一致 | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.2.0 | 未记录（历史资料未提供） | 历史条目未细分 | Codex / GPT-6，§4～5、AC-010-06/09，拆分测试环境并核对 Owner Proof | 落实首轮独立评审，区分设计依据与实测证据 | SR-010，Issue #12，PR #46 |
| 2026-11-27 | 0.2.1 | 未记录（历史资料未提供） | 历史条目未细分 | Codex / GPT-6，设计依据、AC-010-06，加入三层旧包拒绝及公共契约 §10 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.2 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | Host Artifact Channel AC-010-01～05/09 与 Codec 公开能力 AC-010-06b/07/08 分阶段，旧包三层零 IPC 负例可独立验；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-010 |
| 2026-11-27 | 0.2.3 | GPT-6（ChatGPT） | 修订记录 | 将历史记录统一为七列并保留原始文字及原始关联，修正非规范行的分隔符 | 确保修订表可由文档校验器完整解析；不影响设计语义及 READY 主状态 | Issue #12；PR #46；SR-010 |
| 2026-11-27 | 0.2.4 | GPT-6（ChatGPT）；ChatGPT / GPT-6 | 文档头、AC-010-06、历史修订账本、修订记录；3GPP Schema/Codec 分阶段消费 | 补齐 F03.05/F05/公共契约固定版本与章节；要求直接注入旧 Catalog/Run/Binding 分层验证；将历史 undefined 关联改为可审计说明；对齐 SR-031 公共类型、T1 Request 与 T2 Codec Result，新增分期拒绝/验收范围 | 处理独立模型 Review #6082541121 的 R3-SR010-01/02/03，避免占位符和同一 Importer 错误冒充多层 fail-closed；修复标准输入来源与实现门禁的跨仓断点 | Issue #12；PR #46；Review #6082541121；IR-009；Issue #47；SR-031/026 |
| 2026-11-27 | 0.2.5 | Codex / GPT-6；ChatGPT / GPT-6 | 文档头；IR-009 OpenAMSM YAML 原件发布边界 | 登记阶段 READY（本仓 Host Channel）及 AC 范围与工作项 #94；版本随 OpenAMSM、原版不改动；Adapter 与 Provider Result 独立发版，保留阶段 AC | 按单项独立评审推进；避免把标准 YAML 代发布等同解码产品资格 | Issue #12、#74；PR #46；Issue #47；SR-031/026/010/027 |
| 2026-11-27 | 0.2.6 | ChatGPT / GPT-6.2 | §8 | 以原生 OAS3 operation / multipart 消费替代 Adapter 前置；补充 Compiler 精确组件引用、T0/T1/T2/T4 和 AC-010-10 | 使 Plugin、Compiler、Codec 各自承担正确协议层责任 | IR-009；Issue #47；SR-031/013/026/027 |
| 2026-11-27 | 0.2.7 | ChatGPT / GPT-6.2 | §8、AC-010-10 | 固定 requestBody 选定面与 lazy refs；补齐 RefToBinaryData.contentId 到 N1/N2/N2 Ext1 part 的精确映射和负例 | 防止只检查 Header 存在却把错误二进制交给 Codec | IR-009；Issue #47；SR-031/026；EC01/F06 |
| 2026-11-27 | 0.2.8 | ChatGPT / GPT-6.2 | §5、§8、AC-010-10 | 补入正式 AC-010-10 表格行；未引用 part 不交 Codec，额外 part 策略显式归 ingress profile | 避免 AC 仅在摘要出现，并避免超出 OpenAPI schema 的隐含拒绝 | IR-009；Issue #47；SR-031/026；EC01/F06 |
| 2026-11-27 | 0.2.9 | ChatGPT / GPT-6.2 | §2～5、AC-010-03 | 移除 Demo 的逐 Artifact SHA-256 校验；明确 ca-agent 现有 artifact-store v1 不兼容，修订前阻塞实施 | 遵守 Demo 不做 hash 校验的范围，避免复用不兼容的外部契约 | IR-009；Issue #47；SR-031；F03.05 |
| 2026-11-27 | 0.3.0 | GPT-6.2（ChatGPT） | PR #46 / PR #48 集成刷新 | 合并最新 PR #46 的 Host Channel 分阶段状态与 PR #48 的原版 OAS3 / multipart / Codec 消费设计；保留 AC-010-06 分层旧包拒绝及 AC-010-10 Content-ID 映射 | 解决堆叠分支基线漂移并保持无 hash Demo 边界、Host Channel 外部契约阻塞状态一致 | Issue #47/#12；PR #46/#48；IR-009；SR-010/013/026/027 |