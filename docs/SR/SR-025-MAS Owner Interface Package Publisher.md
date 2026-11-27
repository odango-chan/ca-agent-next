# SR-025：MAS Owner Development Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.1.11
> 状态：READY
> 创建日期：2026-11-25
> 所属阶段：外部 Publisher 实施移交
> 上游需求：[IR-006](../IR/IR%20总登记册.md#ir-006)
> 功能：F03.05 / EC03（消费方关联 F09.07）
> 设计依据：[F03.05 Tool Interface / Provider 设计](../../docs/设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) v0.3.9；[F09 §4.5](../../docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md#45-两个-contract-root-的正式-publisher-输出) v0.3.13；[SR-015](SR-015-工具契约设计移交.md)；[Compiler v2.1.0 Development BuildRequest](https://github.com/odango-chan/ca-skill-compiler/blob/v2.1.0/internal/compiler/development_request.go)
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：Provider v2 重构、Runtime Binding 重构、Owner Contract 语义修改、生产级 Trust/Admission/签名或额外包完整性体系

## 1. 目标仓与基线

- 目标仓：`odango-chan/ca-client-tools`，目标分支 `main`，审计基线 `7bcb2614aa3615d8358df31eecefd0909e894e40`。
- Owner source：`contracts/owner/openamsm-mas/v1alpha4`；source tag `v1.2.0` 对应 Revision `fc44c3a745c68443fcfb12054c7eadf0ed7cc3f7`；source buildIdentity `sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0`。
- 当前 main 与 v1.2.0 tag 的 Owner source 目录 59 个文件（manifest + 58 artifacts）逐个 blob 相同；`manifest.json` Git blob 固定为 `dff8136f7dc48b83bbc09d08ed0340f2c9a6ae72`，`buildIdentity` 固定为 `sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0`。当前 main HEAD 晚于 source Revision，但 59 个 blob 无差异；Publisher 不得错误要求整个 checkout HEAD 等于 source Revision，而应固定校验 manifest blob/buildIdentity 与 58 个 artifact digest。
- 当前 `manifest.json` 的 `operations` 有 25 个已发布 contracts，`notPublished` 另列 7 个旧 Callable；这与 Provider 内部 Catalog 的 8 个 legacy typed callables 是两套不同清单。

## 2. 目标与实施范围

将 Owner v1alpha4 source snapshot 包装为 Compiler v2.1.0 Development profile 可消费的正式 `connectionagent.io/interface-package/v1alpha1` ZIP，供 Contract root `mas: urn:openamsm:mas:tool-contracts` 使用。该包是 Development Interface Package，不替代冻结 v1alpha5 Runtime Owner Contract Package，也不改变现有 Provider v2 Interface Package。

- 固定 Package ID：`urn:openamsm:mas:tool-contracts`。
- 固定 Publisher：`openamsm.smf.mas`。
- 固定 Language Target：`connectionagent.io/v1alpha5`。
- Compiler v2.1.0 要求 `package.json.version` 与 Development snapshot key version 均为 exact SemVer。源 Owner version `v1alpha4` 不能直接作为 package version。本包首版为 `1.0.0`，manifest 与 Development snapshot key 逐字一致。
- `package.json` 严格符合 Compiler v2.1.0 `contracts/development/v1alpha1/interface-package.schema.json`，不得增加 sourceRevision、buildIdentity、sourceStatus、Owner Trust 或其他扩展字段。源 Revision/buildIdentity 固定在本 SR 和 Publisher 测试中，不要求 Studio lock 重复保存。
- 新增独立 Owner Publisher，建议路径：
  - `internal/ownerinterfacepkg`
  - `cmd/ca-client-tools-owner-interface-release`
  - 子命令 `generate` / `verify`
- 实现与验收命令：
  ```bash
  go run ./cmd/ca-client-tools-owner-interface-release generate \
    --source contracts/owner/openamsm-mas/v1alpha4 \
    --package-version 1.0.0 \
    --out dist/ca-client-tools_mas-owner_interface_1.0.0.zip

  go run ./cmd/ca-client-tools-owner-interface-release verify \
    --package dist/ca-client-tools_mas-owner_interface_1.0.0.zip
  ```
- 不修改现有 `cmd/ca-client-tools-release` / `internal/interfacepkg` 的 Provider `provider-bindings/v2` 语义；不从 `contracts/mas-owner-candidate`、Provider Runtime Bindings 或 Provider 内部 Catalog 推导 Owner Contract。

## 3. Interface Package 内容与导出闭包

### 3.1 Source validation

- Publisher 先按 Owner source `manifest.json` 验证全部 58 个 artifact digest，再读取 ToolCatalog、CapabilityContracts、Evidence Guarantees 和 Schema。
- ToolCatalog source API 为 `connectionagent.io/toolcatalog/v1alpha4`，Compiler v2.1.0 ToolCatalog parser 可直接读取原始 `tool-catalog.yaml`。
- 25 个公开 contract ID 必须精确等于 `manifest.operations[].callable` 与 ToolCatalog `spec.contracts[].id` 的集合；7 个 `notPublished` ID 不得进入 exports。
- 7 个 notPublished ID：
  - `SC.UPDATE_SM_CONTEXT`
  - `UPN.MODIFY_UP_SESSION_INTENT`
  - `SSM.SIGNAL_UE_AN_MODIFY`
  - `SSM.SIGNAL_UE_AN_RELEASE`
  - `PA.DELETE_SM_POLICY`
  - `SC.RELEASE_SM_CONTEXT`
  - `SE.EMIT_RELEASE_EVENT`
- Provider 内部 8 个 legacy typed callables 与上述 7 项不是同一集合；`UPN.MODIFY_QOS_FLOWS` 是 Provider 内部 legacy binding，不是 Owner ToolCatalog public export，也必须排除。

### 3.2 Exports

| Export kind | 数量 | 来源 / 生成方式 |
|---|---:|---|
| CallableCatalog | 25 | 原始 `tool-catalog.yaml`，每个公开 `spec.contracts[].id` 精确一个 export |
| CapabilityCatalog | 24 IDs / 25 members | 从原始 `capability-contracts.yaml` 生成 `capability-catalog.yaml` |
| EvidenceDescriptor | 25 | 原始 `evidence-guarantees.yaml` 顶层 fact-ID mapping |
| Schema | 53 | 25 个公开 contract 的完整 input/output/receipt/commit-proof/reconcile $ref 闭包 |
| **合计** | **127** | 不包含 notPublished / Provider private bindings |

`package.json.exports[]` 按每个身份逐项生成，不是每种 kind 只生成一个聚合记录：CallableCatalog 的 `id` 精确等于对应 `spec.contracts[].id`，CapabilityCatalog 的 `id` 等于 `capabilities[].id`，EvidenceDescriptor 的 `id` 等于顶层 fact ID，Schema 的 `id` 等于原始 JSON Schema `$id`；每项 `path` 指向其所在的原始或生成文件。相同 kind 下不得有重复 `id`，导出集合与来源集合必须双向相等。

- 原始 Owner `capability-contracts.yaml` 是 `connectionagent.io/capability-contracts/v1alpha4`，结构 `spec.capabilities[].callables[]`，不能直接作为 Compiler Development CapabilityCatalog。生成的 `capability-catalog.yaml` 只允许根字段 `capabilities`，每项为 `{id, members:[{callableId}]}`；不得携带 owner/effect/scopePolicyRef，不是 Grant、Trust 或 Scope Policy。
- 当前 24 个 Capability ID 的 25 个 members 精确覆盖 25 个公开 contract ID；Publisher 测试必须断言集合相等。该 24/25 是当前 CA-SL v1alpha5 + Owner v1alpha4 source 的冻结投影。Next [Issue #40](https://github.com/odango-chan/ca-agent-next/issues/40) 讨论的是下一代 Capability-first 作者模型方向；后续设计目标统一为 **CA-SL 1.6.0（NOT_RELEASED）**，准确的机器标识 `languageTarget` 仍待 ca-skills / Compiler 正式冻结，不得提前猜测或写成已发布契约。本 SR 的当前发布输入仍固定为 CA-SL v1alpha5 + Owner v1alpha4，不得改变本 SR 的包身份。当前 source 中的 `mas.reconcile.exact_original` / `MAS.RECONCILE` 按既有源数据保留；它仍是专用 Runtime Reconcile target，不得把包内静态 CapabilityCatalog membership 解释为普通 Procedure operation 权限。Development Artifact 固定 `NOT_ADMITTED`，不授予运行资格。
- 当前 25 个 Evidence Descriptor 的 `authority` 均为 `openamsm.smf.mas`，Producer ID 集合精确覆盖 25 个公开 contract ID，且不包含 7 个 notPublished ID。Publisher 还必须逐项验证 Producer `provides.path` 与 ToolCatalog guarantee path 精确匹配。
- 源目录有 54 个 Schema 文件；公开 $ref 闭包为 53 项，`deployment-binding.schema.json` 不在公开闭包，必须排除。
- Source manifest 有 58 个 artifact 条目。正式 ZIP 的 56 个 payload 文件由 55 个原始文件（ToolCatalog、Evidence Guarantees、53 个 Schema）和 1 个生成的 `capability-catalog.yaml` 组成；加根 `package.json` 后 57 个文件。当前 55 个原始 payload 合计 80,479 bytes，低于 Compiler v2.1.0 16 MiB aggregate request limit。
- 正式包不包含 `manifest.json`、`capability-contracts.yaml`、`deployment-binding.yaml`、`deployment-binding.schema.json`、部署私有数据或 Provider Runtime Bindings。
- `package.json.files[]` 必须精确列出全部 56 个 payload 文件（不含 package.json），并按包内原始字节计算 Compiler schema 要求的 SHA-256。除此之外不增加包级 checksum manifest、签名、Trust Registry 或额外完整性机制。

## 4. Build / Verify / Release

- 单元测试：`go test ./... -count=1`。
- Publisher 正例：固定 source Revision 下两次 `generate` 产生逐字节相同 ZIP；`verify` 对包内文件集合、manifest identity、exports、digest 和 Schema $ref 闭包全部通过。
- Publisher 负例：source manifest artifact digest 损坏、遗漏/多余文件、错误 Package ID/publisher/languageTarget、非 SemVer package version、重复 export、误导出 7 个 notPublished ID、导出 `UPN.MODIFY_QOS_FLOWS`、Capability member 非公开 callable、Evidence Producer/path 不匹配、Schema 缺失或 tampered ZIP 均 fail-closed。
- Compiler 集成：复用 ca-client-tools `release.yml` 当前固定的 Compiler v2.1.0 binary（SHA-256 `11da056ae5fff416de1fcfacd0a3535a4392a2b2d7349d928f41e1928398b568`）。新增固定 fixture `examples/mas-owner-interface-skill/skills/mas-owner-receipt-smoke/`，包含 `SKILL.md`、`assurance/contract.yaml`、`assurance/procedure.yaml` 和 `schemas/receipt-query-request.schema.yaml`。Contract 只声明 `dependencies.mas=urn:openamsm:mas:tool-contracts` 与 `capabilities: [mas.receipt.query]`；Procedure 只调用 `mas::MAS.RECEIPT_QUERY`，将 `context.request.originalInvocationId`、`deploymentId`、`ownerInstanceId` 映射到同名 arguments，并覆盖 `SUCCEEDED` / `FAILED` 两个 Owner outcomes。BuildRequest 的 `files[]` 使用 `skills/mas-owner-receipt-smoke/...` 相对路径，`targets` 只含该 Skill；lock root alias `mas` 指向 package key `urn:openamsm:mas:tool-contracts@1.0.0`，snapshot 由生成 ZIP 的全部 package files 构成。该 fixture 不依赖 Host Context root，能独立证明 Owner package。负例只将 Procedure tool 改为 `mas::SC.UPDATE_SM_CONTEXT`，Build 必须失败并包含 `EXPORT_ID_MISSING`。
  执行：
  ```bash
  skillc build-development --request request.json --out out --json > result.json
  skillc verify-development --request request.json --result result.json --json
  ```
  正例状态必须为 `VALIDATED / LINKED / BUILT / NOT_ADMITTED`；引用 `SC.UPDATE_SM_CONTEXT` 的负例必须报 export missing。不得声称真实 MAS E2E 或 Production Qualification。
- 发布资产：`ca-client-tools_mas-owner_interface_1.0.0.zip`。若实施时 latest release 仍为 v1.2.0，下一次 ca-client-tools code release 为 v1.2.1；package version 与 source version、code release tag 是三个独立标识。
- 现有 `release.yml` 已将 `dist/*.zip` 纳入 Release assets，`ca-client-tools_*.zip` 纳入 `SHA256SUMS`，并在发布后下载 `ca-client-tools_*` 复验。Publisher 必须在现有 release workflow 的资产/checksum 阶段之前生成并 verify ZIP，再由现有 glob 纳入 `SHA256SUMS` 和上传；发布后显式断言 `ca-client-tools_mas-owner_interface_1.0.0.zip` 存在且 checksum 验证通过。若最新 Release 仍为 v1.2.0，目标代码 Release 为 v1.2.1；Publisher ZIP 自身版本仍为 1.0.0。不得建立第二套 Release 或 Registry。
- 不改写 Owner source Revision/buildIdentity，不把它们复制进 Studio lock；Studio 只锁定正式 Interface Package snapshot 的 packageId/version/publisher 和精确文件快照。

## 5. 验收

- AC-025-01：Publisher 固定读取 Owner source Revision `fc44c3a745c68443fcfb12054c7eadf0ed7cc3f7` 的内容快照；验证 `manifest.json` blob `dff8136f7dc48b83bbc09d08ed0340f2c9a6ae72`、buildIdentity `sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0`、58 个 artifact 路径集合及各自 SHA-256。当前 main `7bcb261` 的同目录 59 个 blob 与 source Revision 完全一致，故不要求 checkout HEAD 等于 source Revision。任一文件缺失、多余、身份或 digest 不符均 fail-closed。
- AC-025-02：正式 package.json 通过 Compiler v2.1.0 Interface Package schema；Package ID、publisher、languageTarget、dependencies 与本 SR 一致。package.json.version 与 snapshot key 均严格等于字符串 `1.0.0`。源版本或带后缀的其他值在 Publisher 身份测试中拒绝。
- AC-025-03：CallableCatalog 精确导出 25 个 Owner ToolCatalog published contract ID；7 个 notPublished ID 和 Provider 内部 8 个 legacy typed callable 均不可导出。Receipt Query / Reconcile 的角色必须与 F03.05 设计一致。
- AC-025-04：CapabilityCatalog 精确为 24 IDs / 25 members，且成员集合等于 25 个公开 contract ID；EvidenceDescriptor 精确 25 项，authority 与 publisher 一致，Producer ID / provides.path 与公开 contract guarantee 精确匹配；Schema exports 精确覆盖 53 项公开 $ref 闭包。
- AC-025-05：正式 ZIP 根目录含 package.json 和 56 个 payload 文件；package.json.files[] 精确列出全部 payload 文件及其 schema-required SHA-256。公开源文件保持原始字节，capability-catalog.yaml 是唯一生成投影；不得额外加入 manifest、sidecar、包级 checksum manifest、签名或 Trust Registry。
- AC-025-06：go test ./... -count=1 PASS；generate / verify 对固定 source Revision 产生逐字节确定 ZIP。覆盖损坏 manifest、错误身份、非 SemVer、重复/缺失/多余 export、notPublished/private callable 泄漏、Capability 成员错误、Evidence Producer/path 错误、Schema 闭包缺失和 ZIP 篡改等负例。
- AC-025-07：使用 ca-client-tools release.yml 固定的 Compiler v2.1.0 binary 执行 BuildDevelopment + VerifyDevelopment；正例 fixture 为 `examples/mas-owner-interface-skill/skills/mas-owner-receipt-smoke/`，Contract 显式声明单一 `mas` root 与 `mas.receipt.query`，Procedure 调用 `mas::MAS.RECEIPT_QUERY`。执行 `skillc build-development --request request.json --out out --json > result.json`（out 必须为空或不存在），再执行 `skillc verify-development --request request.json --result result.json --json`；两条命令均返回 0，状态精确为 `VALIDATED / LINKED / BUILT / NOT_ADMITTED`。负例将 tool 改为 `mas::SC.UPDATE_SM_CONTEXT`，Build 非 0 且诊断包含 `EXPORT_ID_MISSING`。不得声明真实 MAS E2E 或 Production Qualification。
- AC-025-08：新 Owner ZIP `ca-client-tools_mas-owner_interface_1.0.0.zip` 纳入 ca-client-tools 下一次 patch Release（本轮核验 latest 为 v1.2.0，目标 v1.2.1）；沿用现有 dist/*.zip、SHA256SUMS 和发布后下载复验，并新增显式资产存在断言。实际发布按目标仓授权取证。

## 6. 依赖与启动条件

- 依赖本 SR 设计依据所列 F03.05、F09 §4.5、Compiler v2.1.0 Development Interface Package schema/Linker。AC-025-07 用显式 mas root 的最小 Development BuildRequest 独立验收；两包在真实 MAS Example 的组合消费由 SR-016 验收。
- ca-client-tools 当前 main 与 v1.2.0 tag 的 Owner source 59/59 blobs 相同；若实施时 source Revision 已变化，必须重新核对 source manifest、buildIdentity、exports 和 schema closure，不得静默更新基线。
- 包版本已确定为 `1.0.0`。仅将 Owner source version `v1alpha4` 用于定位源材料。
- 本 SR 已完成独立技术设计评审（2026-11-26，结论 `APPROVE_FOR_READY`）：源快照、Package 身份、127 项导出映射、Compiler schema/Linker、正负 Build/Verify fixture、Release workflow 接入点及 Demo 非目标均已固定；未发现要求实现者猜测的 P0/P1 设计缺口。SR 状态转为 READY，允许创建 ca-client-tools 实施 Issue。不得在实施 Issue 之外扩大到 Provider v2、Runtime 或生产 Trust/Admission。DeepSeek Harness Goal 仍须等待目标 Issue 创建和文档门禁检查后单独生成。

## 7. 实施关联

- 目标仓：`odango-chan/ca-client-tools`。
- 现有 ca-client-tools v1.2.0 Provider Interface Package 已发布；它不是本 SR 的 MAS Owner Package。
- ca-client-tools #39 Codec Phase B 与本 SR 相互独立，不作为 Publisher 的硬前置。
- 本 SR 实施 Issue：[ca-client-tools #43](https://github.com/odango-chan/ca-client-tools/issues/43) OPEN；实施 PR / Commit：无；实施：NOT_STARTED；验收：NOT_RUN；替代关系：无。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | §1～6 | 新增 ca-client-tools MAS Owner Development Interface Package Publisher 独立实施 SR；固定 Owner source、25/24/25/53 exports、127 exports、56 payload files、Compiler Build/Verify gate 和 Release 集成；记录 SemVer 映射待用户确认。 | IR-006 · F03.05 · F09 · SR-015 · SR-016 · SR-024 · Issue #12 |

| 2026-11-25 | 0.1.1 | GPT-6.2（ChatGPT） | §2～7 | 补齐 AC-025-01～08，明确 package.version SemVer 决策门槛、导出闭包、负向测试和既有 Release 流程 | 让 ca-client-tools Publisher 达到可评审、可执行的 SR 粒度；不在决策确认前生成实施提示词 | Issue #12；F03.05；F09；SR-015、SR-016、SR-024 |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | 正文 | §2、4～6 固定 MAS 包身份，解除 Publisher 对下游 Studio 的循环前置 | Issue #12 SR-025 |
| 2026-11-25 | 0.1.3 | Codex / GPT-6 | 正文 | §6 明确发布者独立验收输入；同步所引权威设计版本；清理重复基线指针 | Issue #12 SR-025 |
| 2026-11-25 | 0.1.4 | Codex / GPT-6 | 正文 | AC-025-07 固定 v2.1.0 真实 CLI 和复验输入；同步本轮受影响的现行设计依据 | Issue #12 SR-025 |
| 2026-11-26 | 0.1.5 | Codex / GPT-6 | 见本行变更 | 同步设计依据到本次复审的修订版本 | Issue #12 |
| 2026-11-26 | 0.1.6 | GPT-6.2（ChatGPT） | §1～§7 | 独立评审并固定 Owner source manifest blob/buildIdentity 与 59 文件内容基线；明确 127 项 export ID 生成规则、v1alpha5 与未来 v1alpha6 边界、单根 MAS Receipt Query Build/Verify 正负 fixture、release.yml checksum/asset gate；状态提升 READY | 消除源 Revision 与目标 checkout HEAD 的歧义，补齐 Harness 所需的 export identity、最小正例和发布步骤；避免未来 Capability-first 设计静默改变当前 v1alpha5 Publisher 输出 | Issue #12、Next #40；IR-006；F03.05 v0.3.9；F09 v0.3.8；SR-015、SR-016、SR-024；Compiler v2.1.0 |
| 2026-11-26 | 0.1.7 | GPT-6.2（ChatGPT） | §7 | 创建并关联 ca-client-tools 实施 Issue #43；明确 SR-025 已 READY、目标仓实施尚未开始 | 完成 SR READY → 目标仓 Issue 的治理交接，不提前声称代码或发布已实施 | IR-006；SR-025；ca-client-tools #43 |
| 2026-11-27 | 0.1.8 | GPT-6.2（ChatGPT） | §1、§7 | 将 SR-025 v0.1.7 READY 设计基线及 ca-client-tools #43 OPEN 状态纳入恢复分支；重新核对目标仓 main `7bcb261` 与 Issue #43，未发现 Publisher 已实施证据 | 恢复此前未进入恢复分支的有效设计修订，同时明确本轮仅做文档整合，不宣称实施或发布完成 | Issue #53；Issue #12；IR-006；ca-client-tools #43；F03.05 v0.3.9；F09 v0.3.9 |
| 2026-11-27 | 0.1.9 | GPT-6.2（ChatGPT） | §1、§3、§7 | 将 F09 设计依据更新至 v0.3.11；将未来 Capability-first 方向统一表述为 CA-SL 1.6.0 NOT_RELEASED、准确 languageTarget 待正式冻结；保留当前 v1alpha5 + Owner v1alpha4 Publisher 输入 | 消除未冻结的 v1alpha6 机器版本猜测，避免未来设计污染当前 READY Publisher 契约 | Issue #53；Issue #40；PR #45；SR-029；F09 v0.3.11；ca-client-tools #43 |
| 2026-11-27 | 0.1.10 | GPT-6.2（ChatGPT） | 文档头 | 将 F09 §4.5 权威设计引用更新至 v0.3.12 | 保证 Publisher 输入契约引用当时的 F09 版本，不改变 SR-025 READY 与当前 v1alpha5 + Owner v1alpha4 发布输入 | Issue #53；F09 v0.3.12；SR-025；ca-client-tools #43 |
| 2026-11-27 | 0.1.11 | GPT-6.2（ChatGPT） | 文档头 | 将 F09 §4.5 权威设计引用更新至 v0.3.13 | 保持 Publisher 与 F09 最新正式设计版本一致；SR-025 READY、当前 v1alpha5 + Owner v1alpha4 输入和 package version 1.0.0 均不变 | Issue #53；F09 v0.3.13；SR-025；ca-client-tools #43 |
