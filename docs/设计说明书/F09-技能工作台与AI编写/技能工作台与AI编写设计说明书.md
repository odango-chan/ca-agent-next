# 技能工作台与AI编写设计说明书

> 文档类型：设计说明书  
> 文档版本：0.3.26\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first；实施及发布 NOT_RUN）
> 修订日期：2026-11-27\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、额外 package-level digest、签名和 Trust Registry；历史 Compiler v2.1.0 的 `files[].sha256` 要求仅归旧版审计，不转为新版 Schema 要求

关联 IR-006、IR-008、SR-015、SR-016、SR-020（参考宿主架构审计）、SR-024（旧 Development Host Publisher，仅历史）、SR-025（MAS Owner 1.6.0 Publisher）、SR-030（Host Context 1.6.0 Schema-only Publisher）、SR-032（中央 SKILL 作者规范）；新 1.6.0 Compiler 接口以 [EC02 Compiler 设计说明书](../EC02-Compiler/Compiler设计说明书.md) v0.2.13 和 [SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md) v0.2.21 为准；历史 EC02 Development Build 设计只保留源审计，不作为当前 Compiler DTO/Worker/Bundle 发布入口。基线为 [docs/architecture/studio-boundaries.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/architecture/studio-boundaries.md)、[docs/design/ai-procedure-authoring.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/design/ai-procedure-authoring.md)。

## 1. 编辑与语言服务

Theia 的 Package Explorer 以作者源码为工作区入口。可视化视图、导航与诊断来自同一源码和语言核心，未保存缓冲区及包代际变化要驱动刷新；Browser Worker 失效后要给出可见状态。编辑器维护诊断、语义 token、补全和导航，规范锁固定到已发布版本。Package View 的 Dependencies 与 Build Artifacts 使用各自数据源，源码修改保留文本与未改动区域。

## 2. AI 编写

上下文与变更集由编辑宿主管理。模型和独立 Gateway 返回候选提案；宿主校验语义操作，将其转换为可预览的源码补丁。应用前对同一候选执行 Compiler gate，用户保存后才持久化。编辑器及 Gateway 不负责 Skill 选择、Runtime 执行或 Tool 调用。

## 3. when 编写与验收

正式语言刷新后，Contract 字段提示与诊断对齐中央规范。`when` 是 `assurance/contract.yaml` 中的可选顶层字段，不是 SKILL.md Front Matter 字段；其 Schema 类型、CEL 静态检查与错误定位必须对齐 **CA-SL 1.6.0 的唯一正式作者 Schema + 新 Compiler 契约**；历史 v1alpha5 仅用于只读测试差异审计。没有 `when` 的 Contract 保持原有行为。文本与 AI 编辑均保持可预览，不能把选择条件写入 Predicate。覆盖 Browser Worker、源码往返、已有包、有效与无效表达式、Compiler gate 与应用后再打开。

## 4. 历史 Interface Package / Development Build 设计审计（非 1.6.0 规范）

**本 §4.1～§4.5 只记载 Compiler v2.1.0、Studio #267/#270、旧 1.0.0 ZIP 和历史 Lock 的真实行为与来源。它们不是 CA-SL 1.6.0 的 Package Schema、BuildRequest、Lock、发布物或实施验收目标。新规范性流程唯一见 §5～§6 与 §9，凡字段/版本/测试冲突以这些新条款为准；不实现任何历史格式兼容入口。**

### 4.1 职责边界

Skill Studio 的依赖导入负责**获取、验证和固定原始包快照**，不实现 Compiler Linker，也不把 ToolCatalog / Schema Bundle 自动转换成 Compiler Interface Package。

- Add Dependency 支持本地 ZIP，以及用户明确指定的 GitHub owner/repository/tag/asset。禁止默认 latest/main、模糊资产匹配或离线静默回退。
- ZIP Importer 校验 ZIP 结构、CRC、文件数/展开大小限制、路径、重复/大小写冲突、符号链接/特殊文件、根 `package.json`、文件清单和原始字节 SHA-256。不得重写 `package.json`、规范化/改写载荷或推断 Owner 授权。
- 导入后保存**原始文件字节**和来源信息为不可变项目快照。Package Explorer 只读展示 Manifest exports 与来源；点击导出只打开已锁定快照，不进行网络请求。
- 浏览器直连 GitHub Release 若受 CORS/网络限制必须 fail-closed；本地 ZIP 仍是可用导入路径。不得声称 CORS 已通过，除非实际 Pages-origin Chromium 验收通过。

### 4.2 两种 Lock 不得混淆

- Studio 项目锁 `skillc.lock/v0.1` 是持久化的项目导入/来源/快照记录，保存 alias、dependency kind、来源 ref/revision、包身份和精确文件字节/摘要。它是 Studio Resolver 的权威输入，重新加载时重新校验快照字节。
- Compiler `connectionagent.io/interface-dependency-lock/v1alpha1` 是 Development BuildRequest 的**派生输入**。Build adapter 根据每个 Skill 的 `assurance/contract.yaml.dependencies`（alias → stable Package ID）和锁定 Interface Package 的 manifest dependencies，构造 roots、packages 与传递闭包。
- 不把 Compiler Lock 另存为第二个持久化项目锁，不替换 `skillc.lock/v0.1`。两个 Lock 的字段、摘要 framing 和职责不同。
- Compiler request 的 Interface Package snapshots 必须直接来自已验证 Studio 快照的原始字节。Studio lock 摘要与 Compiler `CA-SKILL-DEPENDENCY-SNAPSHOT\\0v1\\0` 摘要是不同 framing；Build adapter 先复核 Studio 锁摘要，再从同一原始字节计算 Compiler 摘要。

### 4.3 BuildRequest 的依赖选择

- 只选择当前 Skill Contract 明确声明的根 alias，以及这些根 package manifest 声明的传递依赖闭包。
- 项目中未被当前 Skill 引用的额外依赖（例如仅供 IntelliSense 的 `ca-client`）不得自动进入 roots，也不得因为它们是 `tool-catalog` / `schema-bundle` 就阻断另一个 Skill 的独立构建。
- 若 Contract 声明的根 alias 在 Studio lock 中不存在，报精确的 Missing Root；若该 alias 对应的锁定条目不是正式 `connectionagent.io/interface-package/v1alpha1`，报明确的 Unsupported Dependency Kind。不得把不同 kind 转换为伪造的 Interface Package。
- 所有入选根及传递依赖必须通过 packageId/version、manifest edge、原始快照摘要、路径和文件清单校验。缺包、歧义 alias、冲突版本、依赖环、锁边与 manifest 不一致、损坏字节均 fail-closed。
- Compiler 是静态链接与类型/语义验证权威。Studio 的 Package Explorer / LSP 可以投影已验证导出，但不得替代 Compiler 进行完整 Callable、Capability、Evidence、Schema Link 判断。

### 4.4 当前 OpenAMSM Example 的真实边界

当前三个 MAS Example Contract 的根依赖为：

| Contract alias | Stable Package ID | 当前 Studio lock kind | 状态 |
|---|---|---|---|
| `mas` | `urn:openamsm:mas:tool-contracts` | `tool-catalog`（ca-client-tools v1.2.0 Owner contract source） | 尚非正式 Interface Package |
| `ca-context` | `urn:connectionagent:ca:host-context` | `schema-bundle`（Host Development fixture） | 尚非正式 Interface Package |

项目另预加载 `ca-client`，其 Package ID 为 `urn:wtlab:ca-client-tools:openamsm-sbi-interface`，来自已发布 `ca-client-tools_interface_1.1.0.zip`。它导出十一项 public READ Tools / 两个 Capabilities，用于只读 SBI Query IntelliSense；它**不是** `mas` Owner contract，也不是 `ca-context`，当前 Contract 未声明它为根。Studio/Compiler 不得推断替换。

历史 v2.1.0 Development Build 使用的 Owner / Host Package 仅用于 SR-024 / SR-025 来源审计，不是 1.6.0 新入口。新 1.6.0 MAS Owner Package 由 [SR-025](../../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) 负责；Host Context Schema-only Package 由 [SR-030](../../SR/SR-030-Host%20Context%201.6.0%20Schema-only%20Interface%20Package%20Publisher.md) 负责。Studio 只导入正式新发布物，不代替 Publisher 组包。

### 4.5 两个 Contract root 的正式 Publisher 输出

历史 Compiler v2.1.0 Development Build 使用 connectionagent.io/interface-package/v1alpha1，仅作为 §4.5 的只读审计来源。新 1.6.0 Publisher 由 SR-025 / SR-030 分别负责；Studio 的 Import / Lock / Compiler 集成由 SR-016 负责。

两个包的 `package.json` 必须严格符合 Compiler v2.1.0 的 [interface-package.schema.json](https://github.com/odango-chan/ca-skill-compiler/blob/v2.1.0/contracts/development/v1alpha1/interface-package.schema.json)：字段为 `apiVersion`、`packageId`、`version`、`languageTarget`、`publisher`、`dependencies`、`exports`、`files`，`additionalProperties=false`。不得添加 `sourceStatus`、sourceRevision 或 Owner Trust 等非契约字段。Compiler 要求 `package.json.version` 与 Development snapshot key version 完全相等。

**版本兼容阻塞（两个 Publisher 共用）**

Compiler v2.1.0 的 `validDevelopmentVersion` 接受 `major.minor.patch` 和合法的 prerelease，显式拒绝 `+build` 元数据。本项目这两个 Publisher 的首版仅发布 `1.0.0`。解析器通过的其他版本仍须通过 Publisher 身份断言；这里检查的是两个不同的条件。BuildRequest parser 会拒绝 `v1alpha4` 和 `v1`，诊断为 `DEVELOPMENT_SNAPSHOT_INVALID`，即使 Interface Package JSON Schema 的 `version` 属性本身只声明为字符串。当前 MAS Skill 的 `Contract.dependencies` 只声明 Package ID，不固定 package version，因此可以保持 Package ID 和源契约版本不变，为 Development Interface Package envelope 单独选择 SemVer。

两种包各自从首版 `1.0.0` 开始；锁与请求按完整 Package ID 和版本识别：

| Contract root | 原始源版本 | Compiler Interface Package version（确定值） |
|---|---|---|
| `urn:openamsm:mas:tool-contracts` | Owner source `v1alpha4` | `1.0.0` |
| `urn:connectionagent:ca:host-context` | Subject Schema ID `v1` | `1.0.0` |

两个不同的 Package ID 可以使用相同的包版本。重开工程后 lock、snapshot key、package.json 三者应能按各自的身份相等匹配；原始 Owner version 与 Schema ID 单独核对。

**MAS Owner Interface Package**

- 固定 Package ID：`urn:openamsm:mas:tool-contracts`；Publisher：`openamsm.smf.mas`；Language Target：`connectionagent.io/v1alpha5`。源版本仍为 Owner v1alpha4；Development Interface Package version 为 `1.0.0`，由 SR-025 实现。
- Owner source manifest 的 `operations` 包含 **25 个已发布 contracts**（23 个业务 Callable + Receipt Query / Reconcile 两个 evidence operations）；`notPublished` 另列 7 个旧 Callable，不能把它们计入 25 个 published contracts。Provider 内部另有 8 个 legacy typed callable，其中 `UPN.MODIFY_QOS_FLOWS` 不属于 Owner ToolCatalog；两组排除清单不得混淆。
- `CallableCatalog` exports 精确 25 项，来源为 Owner v1alpha4 原始 `tool-catalog.yaml`；Receipt Query 是受 Capability/Scope 约束的 READ Callable，Reconcile 是专用 Reconcile target，不得作为普通 `operation.tool` 调用。
- Owner `capability-contracts.yaml` 是 `connectionagent.io/capability-contracts/v1alpha4`，结构为 `spec.capabilities[].callables[]`，不能直接作为 Compiler Development CapabilityCatalog。Publisher 生成唯一确定性投影 `capability-catalog.yaml`：24 个 Capability ID、25 个公开成员，结构为 `capabilities: [{id, members: [{callableId}]}]`；不包含 owner/effect/scopePolicyRef，不构成 Grant 或 Trust。
- `EvidenceDescriptor` exports 精确 25 项；当前 25 个 Producer ID 与 25 个已发布 ToolCatalog contract ID 精确匹配，authority 为 `openamsm.smf.mas`，不与 7 个 `notPublished` ID 重叠。Publisher 还须校验 Producer `provides.path` 与 ToolCatalog guarantee path 精确匹配。
- `Schema` exports 为 53 项，覆盖全部公开 contracts 的 input/output/receipt/commit-proof/reconcile `$ref` 闭包；源目录 54 个 Schema 中，未进入公开闭包的 `deployment-binding.schema.json` 排除。
- Owner source manifest 有 58 个 artifact 条目，Publisher 先验证全部源 artifact digest。正式包的 56 个 payload 文件由 55 个原始文件（ToolCatalog、Evidence Guarantees、53 个 Schema）和 1 个生成的 `capability-catalog.yaml` 组成；加根 `package.json` 后 57 个文件。总计 **127 个 exports**（25 Callable + 24 Capability + 25 Evidence + 53 Schema）；当前原始 payload 为 80,479 bytes，远低于 Compiler v2.1.0 的 16 MiB aggregate request limit。
- 正式包不包含 `capability-contracts.yaml`、`deployment-binding.yaml`、`deployment-binding.schema.json`、Owner source `manifest.json`、部署私有配置或 Provider Runtime Bindings。公开 ToolCatalog、EvidenceDescriptor、Schema 文件保持原始字节；CapabilityCatalog 投影是唯一生成文件。Compiler `files[]` 精确列出 56 个 payload 文件（不含 `package.json`），每个文件的 SHA-256 是 Interface Package schema 要求；不增加第二套包级完整性、签名或 Trust Registry。
- `ca-client-tools_interface_1.2.0.zip` 是 Provider v2 的 11-READ Interface Package；`openamsm-mas-compiler-contract-v0.3.0.zip` 是 `wtlab` 的 `compilerLinkable=false` candidate。两者均不是 MAS Owner Development Interface Package。

**Host Context Interface Package**

- **历史 SR-024** 固定 Package ID / Publisher / Schema $id 和 v1alpha5 Development Package 1.0.0；只读保留，不进入新版 Studio。
- **新 SR-030** 沿用稳定 Package ID / Publisher / Schema $id，languageTarget 目标 CA-SL 1.6.0（候选 connectionagent.io/v1.6.0），新 Package SemVer 不复用 1.0.0；只导出 Schema，Capability / Callable exports 均为空。
- ZIP 仅含根 `package.json` 与原始 `subject.schema.json`；只导出一个 `Schema`，ID 精确为 `urn:connectionagent:ca:context:subject:v1`；`dependencies=[]`；`files[]` 只列出原始 Schema 文件的 SHA-256。不得重写或重新序列化 Schema。
- Source Revision `57e277ff9094dad93543df46910a12a1dbbaf560` 与 Git blob `4faee66642b8bc5eb2e45c131be4688b982037d8` 固定在 SR-024 / Publisher 验收中；Studio lock 不重复保存 source Revision/Git blob。该包是 Development fixture，不是生产 Host Trust 或 Admission。

**Studio Lock 与共同边界**

- `sourceStatus=DEVELOPMENT_FIXTURE` 只由 Studio 写入 `skillc.lock/v0.1` 的 `source.sourceStatus`；不得写入任何正式 `package.json`。这项持久化由 SR-016 / Studio #269 验收。SR-024 已固定 Host source Revision/Git blob，不要求项目锁重复保存。
- #267 ZIP Import 和 #270 MAS Example preload 已 MERGED，不得再列为尚未实现的前置。#269 仍负责 Development BuildRequest、Package Audit、AI Authoring Compiler Gate 和 no-root 诊断。
- 两个 Publisher 都只发布静态 Interface Package；`publisher` 是声明身份，不是 Owner Trust。Compiler v2.1.0 Development BuildRequest 不接受 `trustedBuildContext`、Owner attestation、Deployment Grant、live Evidence 或 Provider binding；成功结果仍为 `VALIDATED / LINKED / BUILT / NOT_ADMITTED`，不代表 Host Admission 或 Runtime Execution。
## 5. CA-SL 1.6.0 Package Audit / AI Authoring 单一路径

### 5.1 新版输入、组件与生命周期

1. Studio 打开 1.6.0 Skill 工作区，绑定当前**原始源码 Buffer**和其不可变 revision。导入依赖只接受新 Compiler/Publisher 冻结的 1.6.0 Interface Package ZIP；严格验证新版正式 Package Schema、语言标识、公开 Capability 唯一映射、精确导出闭包与当前项目依赖快照。旧 v1alpha5、Development v1alpha1/v2.1.0 ZIP 和旧项目配置一律拒绝，不做转换。
2. Studio 维护自己的持久 Project Lock：Package ID、SemVer、Publisher、languageTarget、来源类型 / 上传元数据及已安装源快照引用。Package Manifest 只包含 1.6.0 Package Schema 规定的 Package identity / exports / files；sourceStatus、sourceRevision、Git blob 和 Studio upload provenance 不属于 Package Manifest。Project Lock 的字段和 reload 语义由 SR-016 冻结，不偷用旧 skillc.lock/v0.1 wire 格式。Compiler 的 BuildRequest/派生依赖闭包由同一候选源码和**同一项目锁 revision**生成，不建立第二个持久项目锁；Compiler 负责权威静态链接，Studio 不复制 Linker。
3. Package Explorer 展示 Package→Capability；每个 Capability 仅对应一个公开 Callable。Callable、backendOperationId 不成为作者选择节点；Editor/LSP/AI 只生成 `contract.capabilities`、`operation.capability`、`observation.capability`。包内多成员、重复 Callable、Schema 不符、旧 Alias::Callable 都标记为不可用于新版编译。
4. Package Audit 与 AI Authoring 都走**同一新 1.6.0 Compiler adapter/Worker/WASM/Build/Verify**。输入为准确源码字节 + lock revision + Owner 的新 BuildRequest；禁止调用历史 `build-development`、`verify-development`、v2.1.0 Worker 或构建 fallback。Compiler 未冻结字段/API 之前，本调用保持 `BLOCKED`，不凭旧 Schema 猜测。
5. Preview/Review 允许查看未经编译的候选 Change Set，但标记「尚未检查，不能 Apply」。只有**与当前候选字节和当前项目锁 revision 精确匹配**的 Build + Verify 成功，才可提供「应用候选」；Apply 必须由用户确认、保留未保存 Buffer、支持 Undo 恢复逐字原文；Save 仍由用户决定。候选、依赖快照或语言版本变化使旧结果立刻失效。
6. Browser、Native、WASM 用同一构建输入与可追踪诊断，任一结果不能混用来自另一 HEAD、Lock revision 或旧语言的 PASS。Worker 不访问 Provider credentials、不执行 Runtime Tool、不赋予 Owner/Host 资格。

### 5.2 UI 状态投影（非新 Compiler 机器字段）

| 关注项 | 显示原则 |
|---|---|
| Source | `NOT_CHECKED`、`VALIDATED`、`FAILED` 是 Studio 概念状态；Compiler 返回值必须按**正式新 Schema**映射，不虚构 wire 字段 |
| Package/Capability Link | 精确唯一映射成功才显示 LINKED；任何多成员/重复 Callable/失配源都显示明确错误 |
| Artifact | 仅当前候选 Build+Verify 成功才标记 BUILT；未构建/过期标记 NOT_RUN/STALE |
| Execution | Build ≠ Host/Runtime 授权；Demo 没有独立 Skill Admission，不能凭编译成功伪造 Owner Commit 或运行资格 |
| Historical | 旧 Development 的 `VALIDATED / LINKED / BUILT / NOT_ADMITTED` 仅供 §4 历史审计，**不是 1.6.0 新 BuildResult 机器值** |

失败应给出由哪个输入、哪一 SourcePath、哪一 Capability/Schema 导致拒绝；诊断不能因为编辑器无法加载 Compiler 就假装 PASS。公开 LSP/Preview 不触发旧版编译器。

## 6. 新 1.6.0 无 Assurance 与零外部依赖

- **无 Assurance Skill Package**：可包含 schemas/、scripts/、references/ 和 assets/；不调用 Compiler，不生成 Assurance Artifact，不拥有业务 Capability Scope，仅支持 LLM-guided；在双栏源编辑器中仍可预览指导文本、元数据与共享资源。
- **存在 Assurance、没有外部 Capability / Schema 引用**：新 1.6.0 Compiler 必须允许零 Capability roots 与空 Package dependency closure；BuildRequest 仍包含 Skill/语言/Schema/源身份，Compiler 生成不含外部 Tool Effect 的确定性 Artifact。
- **存在 Assurance、仅引用 Schema-only Package**：例如 Contract.contexts 引用 SR-030 Host Context Schema。此时 Capability roots 与 Callable bindings 仍为空，但 Package dependency closure 必须包含该显式依赖的 Schema export 和完整 $ref 闭包；不得把 Schema-only Package 当作 Capability root，也不得虚构 Tool / Callable。
- **存在 Assurance 且使用 Capability 但未声明依赖**：Compiler 静态 Link 必须拒绝 `CAPABILITY_UNRESOLVED` / `CAPABILITY_NOT_GRANTED`；绝不能把它当成合法零根。旧 v2.1.0 只能接受非空 roots 的限制**不是 1.6.0 新设计**。
- 联验顺序固定为 Compiler Owner 冻结正式 Package/Build Schema → SR-030 生成真实 Schema-only 候选 → 同一版 Compiler 执行 AC-013-06 → AC-013-05 发布 Release。SR-027 用该 Release 构建 Bundle；SR-016 在 Release 后按各 AC 取实际需要的输入完成六宿主联验。正式契约缺失时 Studio 显示 COMPILER_CONTRACT_PENDING，不调用旧 API 或产生 Artifact。现有六宿主 workflow 只证明入口存在。

## 7. 历史实现状态与新版本待验证项

截至 2026-11-25：

| 项目 | 状态 | 证据 / 未完成 |
|---|---|---|
| ZIP Import / immutable snapshot / Package Explorer | MERGED | [Studio #267](https://github.com/odango-chan/ca-skill-studio-demo/pull/267)，main merge `11b1246` |
| Default Example dependency preload | MERGED | [Studio #270](https://github.com/odango-chan/ca-skill-studio-demo/pull/270)，main merge `d3b1d36` |
| Compiler v2.1.0 request builder | OPEN / DRAFT / STALE | [Studio #272](https://github.com/odango-chan/ca-skill-studio-demo/pull/272)，测试 HEAD `8abffc7`，当前落后 main 67 commits |
| Compiler v2.1.0 Node/Browser Worker | OPEN / DRAFT / STALE | [Studio #276](https://github.com/odango-chan/ca-skill-studio-demo/pull/276)，测试 HEAD `7d6adeb`，落后 #272 base 9 commits |
| Package Audit Development Build cutover | NOT_IMPLEMENTED | [Studio #269](https://github.com/odango-chan/ca-skill-studio-demo/issues/269) |
| AI Authoring exact-candidate Development Build gate | NOT_IMPLEMENTED | [Studio #269](https://github.com/odango-chan/ca-skill-studio-demo/issues/269) |
| MAS / Host Context 1.6.0 Package publication | BLOCKED | MAS Owner Capability-first Package 归 SR-025；Host Context Schema-only Package 归 SR-030；新 Package Schema / SemVer / languageTarget 尚未正式发布；旧 SR-024 的 1.0.0 不得作为新输入 |
| Host fixture provenance in Studio lock | NOT_IMPLEMENTED | #267 已持久化 ZIP source metadata（upload/contentDigest/packageId/version/publisher），但尚未写入 `source.sourceStatus`；由 SR-016 / Studio #269 补齐 |
| Real released ca-client-tools v1.1.0 as Compiler root | NOT_RUN | 需显式 `ca-client` synthetic Contract 正例 |
| No-root UI state | NOT_IMPLEMENTED | 不调用 Compiler、无 Artifact、无 `NOT_ADMITTED` |

#272 / #276 曾在各自历史 HEAD 通过 PR Verify、Native Windows、IDE Host、Theia Browser-Only、Theia Browser Host 和 Pages Chromium 等检查，但当前分支分别落后 main / base；历史 PASS 不满足当前合并门禁。必须在刷新分支后重跑完整 exact-head 验收。

必要验收至少包括：原始发布 ZIP 导入/锁定字节一致性；Contract root closure 只包含可达 Interface Packages；无关项目依赖不进入 BuildRequest；声明为非 Interface Package 的 root fail-closed；缺失/损坏/摘要错/传递依赖环拒绝；无 Assurance 不调用 Compiler；Assurance 无外部 Capability / Schema 依赖时允许空闭包 Build；Assurance 仅引用 Schema-only Package 时保留非空 Schema closure 但零 Capability roots / Callable bindings；Node/WASM/Chromium 结果一致；AI 候选 stale invalidation、Apply/Undo 和磁盘未保存语义。所有结果只证明相应静态/编辑器层，不代表 Owner/Host Admission、Runtime、Production 或真实 5GC Qualification。

## 8. 历史决策

EC06 历史决策已统一归档于中央仓：[ADR-0001 Source-first Visual](../../决策记录/EC06-ADR-0001-Source-first-Visual.md)、[ADR-0002 IDE Host Spike](../../决策记录/EC06-ADR-0002-IDE%20Host%20Spike.md)、[ADR-0003 Theia 原生工作台与 Markdown](../../决策记录/EC06-ADR-0003-Theia原生工作台与Markdown.md)、[ADR-0004 Package 优先工作区](../../决策记录/EC06-ADR-0004-Package优先工作区.md)、[ADR-0005 固定源码与预览工作台](../../决策记录/EC06-ADR-0005-固定源码与预览工作台.md)。Classic 为历史迁移证据。原始设计材料包括 [Studio boundaries](../../架构设计/外部能力域/EC06-Skill%20Studio所有权与源码边界原文.md)、[Authoring Workbench](../外部能力域/EC06-Skill%20Studio/Authoring%20Workbench设计原文.md)、[Plugin-managed Configuration v0.1](../外部能力域/EC06-Skill%20Studio/Plugin-managed%20Configuration%20%26%20Tool%20Integration%20v0.1原文.md) 和 [C4 Package Overview](../外部能力域/EC06-Skill%20Studio/C4%20Package%20Overview原文.md)；当前目标设计仍以本文为准。

## 9. Capability-first Package Explorer 与 LSP

### 9.1 唯一能力入口

Skill Studio 的 Package Explorer 以 Capability 作为唯一 Skill-facing 业务能力导航入口。Package 依赖仍按 Package 分组；Package 内的业务能力区只显示 Capability，不再并列展示 Tools / Operations / Callable 树。共享资源区单独显示 Package 根目录的 schemas/、scripts/manifest.yaml、scripts/、references/ 和 assets/；这些资源不是 Capability，不出现在 Capability exports 列表。Capability 详情可显示描述、kind、Effect、Input/Output Schema、Evidence 和来源 Package；Callable ID 只允许出现在内部 Binding 详情或编译诊断，不作为可选择的作者节点。

### 9.2 语言服务

1.6.0 LSP / Completion 对 Contract.capabilities、operation.capability、observation.capability 提供 Capability ID 补全、悬停、定义跳转和静态诊断。补全来源是已导入并固定的 Package Capability exports，不是运行时 Provider catalog。对根目录 schemas/*.schema.yaml 提供 YAML 语法高亮、JSON Schema Profile 字段补全、引用跳转和本地诊断；对 scripts/manifest.yaml 提供 Script ID / entrypoint / Schema 引用补全与校验，并允许跳转到 scripts/ 源码。上述资源路径都相对 Skill Package 根目录。对 `assurance/procedure.yaml` 的 `operation.script`、`assurance/predicates.yaml` 的 `evaluator` 提供 Script ID 补全、悬停、定义跳转和 Registry 引用诊断；脚本路径和入口函数名不作为作者可选值。Compiler 仍是 Capability membership、唯一性、Schema、Evidence、Scope、Script Registry 与 Procedure Link 的最终权威；LSP 不得把本地投影诊断显示为 Compiler Build PASS。

### 9.3 AI Authoring

AI Authoring 的 Change Set 必须遵守中央 [SKILL 作者规范](../../规范/SKILL作者规范.md)的全部适用规则：Skill / Capability 粒度、共享 Package 资源与 Schema 所有权、SourcePath / 显式 arguments、when / Wait、Evidence / UNKNOWN、静态 DAG、四阶段顺序、Node 拆分 / 合并和注释非执行语义。AI Authoring 可以读取当前 Package snapshot 的 schemas/、scripts/manifest.yaml 与 scripts/ 源码作为上下文；读取不等于执行。当前 Procedure Authoring Change Set 只修改 `assurance/procedure.yaml`：允许新增 / 删除 / 修改 `start`、Node、四阶段、已发布 Capability / Predicate / Script ID 的引用、显式 arguments、阶段 routes、Node-entry Wait 和解释性注释；引用只能来自已导入并 pin 的 Package exports / PredicateSet / Script Registry，不得自行创造 Capability / Predicate / Schema / Script 身份。该 Change Set 不修改 `assurance/contract.yaml`、`schemas/`、`assurance/predicates.yaml`、`scripts/`、`scripts/manifest.yaml`、Package Manifest 或外部 Package exports；Contract.when 的字段编辑仍走 §3 的独立编辑与校验路径，不混入 Procedure Change Set。若重命名 / 删除的 Node 被 `contract.precondition` 引用，或其他 Procedure 修改必须同步修改 Contract 字段，当前 Change Set 必须返回 OUT_OF_SCOPE；不得只改 `procedure.yaml` 留下悬空的跨文件引用。超出范围的提案必须明确返回 OUT_OF_SCOPE，不得静默扩大变更集。不得生成 Callable ID、backendOperationId 或动态 Provider 选择，不得通过注释补足缺失的 Schema、Predicate、Evidence 或 routes。AI Authoring 不执行脚本；需要运行脚本时只能在正常 Agent Runtime 中由 Host 配置 `scriptExecution.llmEnabled=true`，且 Registry 将该 transform Script 标记为 `llmInvocable=true` 时，才可提供 host.skill-script.execute；不能在 Studio Worker / AI Authoring 中创建第二套 Python 执行器。Apply 前仍须用户确认，随后对同一候选源码和项目锁使用同一 1.6.0 Compiler Build / Verify 路径重新检查；本设计不表示当前 Studio 已实现作者规范感知或 Compiler gate。

### 9.4 版本与导入

- 历史 v1alpha5 Package / Skill 快照只读归档，不进入新版 Studio，也不提供迁移。
- 1.6.0 Package 必须声明唯一 languageTarget，并使用满足一对一约束的 Capability exports。
- Studio 只支持 1.6.0 项目，不提供历史项目兼容读取或版本 fallback。
- 当前 Studio #267/#269 的既有实施状态不因本设计自动升级；Capability Explorer、LSP 和新 Package 消费仍是未实施目标。

**1.6.0-only 待评审硬门槛：** 新 Studio 仅接受 1.6.0 项目，旧项目不兼容、不自动迁移；此处只是目标设计，产品和 E2E 均 NOT_RUN。


### 9.5 1.6.0 独立验收矩阵

| 验收方向 | 固定输入 | 必需输出 |
|---|---|---|
| 1.6.0 新 ZIP Import | Publisher 正式包、唯一 Capability↔Callable 和声明 Schema | 原字节快照、Package→Capability Explorer 和可重新打开的新版锁 |
| 旧包/旧项目拒绝 | v1alpha5、v2.1.0 Development、旧 `skillc.lock` | 明确版本诊断、无转换、无 fallback、锁未被污染 |
| 唯一 Binding | 正确 one-to-one 与多成员/重复 Callable 反例 | 补全和定义跳转只返回公开 Capability；错误不得显示 Compiler PASS |
| 共同 Compiler 路径 | 同源码/lock 的 Package Audit 与 AI Candidate | 完全相同的新 BuildRequest/Verify；不同 revision 不可复用结果 |
| stale/Apply/Undo | Candidate 或 lock 变化、Apply 后立即 Undo | 旧结果失效；显式确认；精确还原原始 Buffer，Save 不被触发 |
| Assurance / Capability / Schema closure | 无 Assurance；有 Assurance 且无外部 Capability / Schema 依赖；有 Assurance 且仅引用 SR-030 Schema-only Package；缺依赖但引用外部 Capability | 分别为不调用 Compiler、空 Package closure 合法 Build、非空 Schema closure 且零 Capability roots / Callable bindings 的合法 Build、fail-closed 拒绝 |
| 多宿主一致性 | 同正式 1.6.0 Snapshot 的 Node/Native/WASM/Chromium | 诊断/结果相同，记录 SHA、测试数、命令、真实截图/日志 |

**评审与实施门槛**：上述每项测试的正式 Package Schema、Compiler DTO/CLI/Worker、语言标识由对应发布者冻结后才允许产品 PASS。Studio 旧 Example 替换、旧 1.6.0 不兼容及历史导入结果仅用于审计，不能混入新 AC。SR-016 是该矩阵的实施与验收追踪入口；系统 E2E 不能代替 Studio 模块 AC。

## 10. 原版 3GPP OpenAPI 只读展示与直接 Schema Component 引用（IR-009）

- 工作台可展示 SR-031 原样代发布的 OpenAMSM OpenAPI 3.0 Source Bundle，作为只读标准来源视图；保留原始 bytes、文件名 / 路径 / 相对 `$ref`，不提供自动格式化、重写、修补或保存原件修改。任何 AI Change Set 试图修改原版 YAML 必须拒绝。
- Schema Explorer / LSP 可沿已 pin Source Bundle 的精确 `components/schemas` 外部引用显示定义、来源文件、JSON Pointer、OpenAMSM commit 和标准版本；Compiler 才是跨 dialect Schema Link / Build / Verify 权威。不得把原版 OAS3 Schema Object 重写为 G.4 Adapter；本地 Skill-owned Request 根仍遵循 G.4。
- Studio / Project Lock 必须记录正式 Source Bundle dependency identity 与完整可达文件快照；不解析动态 latest、不从任意 URL 下载，也不让无 3GPP 依赖的项目被强制导入该 Bundle。
- Procedure 可引用 ca-client-tools 正式 Codec READ Capability 与 Output Schema，但不能展示私有 Handler / Callable；当 T1 `when` 企图读取 T2 才解码的 NAS 字段，Compiler 应给稳定的 SourcePath / 可用性诊断，不能偷偷触发解码。
- NAS / NGAP Output Schema 是 Provider 独立发布物，不从 SBI `format: binary` 推导。没有正式 Compiler OAS3 Resolver / Provider Golden 时，不生成假 Schema、不宣称产品 PASS；现行产品验收 NOT_RUN。

[统一权威设计](../EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)与 [SR-031](../../SR/SR-031-3GPP公共Schema-only-Publisher.md)。唯一语言 1.6.0，不创建第二管理器。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F09 · IR-006 · SR-016 |
| 2026-11-25 | 0.2.0 | GPT-6 | §4–7 | 明确 Studio 项目锁与 Compiler Lock 的边界、当前 MAS roots 的 package-kind 不匹配、no-root 行为、统一 Development Build gate 和当前 PR 新鲜度门禁。 | Studio #261、#267、#269、#270、#272、#276；EC02 Development Build |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §3–7 | 明确 when 位于 `assurance/contract.yaml`；补齐 MAS Owner / Host Context Interface Package 的 Publisher 字段、导出闭包、精确来源与 Development provenance 边界，并关联 SR-015 / SR-020。 | IR-006 · SR-015 · SR-016 · SR-020 · Studio #269 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §4.4～7 | 将 Host Context Interface Package Publisher 从 SR-020 拆分到新 SR-024；SR-020 保留参考宿主架构审计职责；明确仅使用 Compiler v2.1.0 schema 要求的 files[].sha256；避免一个 SR ID 承载两项不同工作，并区分既有 Interface Package 文件摘要与 CA-SL Skill Artifact 的非目标完整性体系 | IR-006；SR-015、SR-016、SR-020、SR-024；Studio #261/#269/#272/#276 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4.4～7 | 修复 SR-024 Publisher 文档链接并同步 F02/F08/SR-016/SR-024 版本；明确 SR-020 只承担参考宿主审计；解决 SR-020/SR-024 责任冲突，确保 Publisher 入口唯一 | IR-006；SR-015、SR-016、SR-020、SR-024 |
| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | §4.5、§5.2、§7 | 对照 Studio #267 合入代码，明确 `source.sourceStatus` 尚未写入 lock，并将其归入 SR-016/#269；区分项目来源元数据与 Compiler BuildResult.sourceStatus；避免把设计要求误报为当前持久化能力，防止两个 sourceStatus 语义混淆 | Issue #12；SR-016、SR-024；Studio #267/#269 |
| 2026-11-25 | 0.3.4 | GPT-6.2（ChatGPT） | §8 | 将 EC06 ADR-0001/0002 与 Plugin-managed/C4 原文纳入中央仓，并将 F09 历史决策和原始设计引用切换为 Next 内部链接；关闭原始设计缺失与跨仓引用断链；不改变历史决策内容 | Issue #12；EC06-ADR-0001～0005；SR-016、SR-024 |
| 2026-11-27 | 0.3.16 | Codex / GPT-6 | §5～6、设计依据 | 固定 Schema、候选、Compiler 联验与正式发布的先后关系 | Issue #12，PR #46 |

| 2026-11-25 | 0.3.5 | GPT-6.2（ChatGPT） | §4.5、§6～7 | 将 MAS Owner Publisher 独立归入 SR-025、Host Publisher 归入 SR-024；按 Compiler v2.1.0 修正 MAS exports 为 25/24/25/53；发现 v1alpha4/v1 非 SemVer，提出 package/source version 分离决策门槛；防止发布无法被 Development Build 接受的版本，同时保持 Owner/Host 源身份与 Studio lock 边界 | IR-006 · SR-015 · SR-016 · SR-024 · SR-025 · Studio #269 |
| 2026-11-25 | 0.3.6 | Codex / GPT-6 | 正文 | 同步两个 Publisher 的 1.0.0 身份与消费边界 | Issue #12 |
| 2026-11-25 | 0.3.7 | Codex / GPT-6 | 正文 | §4.5 依据 v2.1.0 源函数实测修正 +build 与项目包身份限制 | Issue #12 |
| 2026-11-26 | 0.3.8 | GPT-6（ChatGPT） | 新增 1.6.0 目标设计 | 仅支持新版本，无兼容或迁移 | Issue #40；SR-029 |
| 2026-11-26 | 0.3.9 | GPT-6（ChatGPT） | 版本隔离与修订记录 | 隔离历史 Development Compiler 流程，1.6.0-only Studio 仅用新 Worker/Build DTO | Issue #40；SR-029 |
| 2026-11-26 | 0.3.10 | GPT-6（ChatGPT） | 修订表/记录 | 合并历史修订行的内容与原因列，仅保留原文字义，不改历史断言 | Issue #40；SR-029 |
| 2026-11-26 | 0.3.11 | GPT-6（ChatGPT） | 目标合同、实施 AC 和旧版留档 | §3～§9 重建 1.6.0-only Studio Package/Compiler/AI/zero-root 工作流和独立验收，旧 Development 只读留档 | Issue #12/#40；SR-016/025/029；PR #46 |
| 2026-11-26 | 0.3.12 | GPT-6（ChatGPT） | 文档头与 1.6.0 当前设计依据 | 修复 PR #46 Review Context 文档头检查及旧 Development Build 设计依据，更新新 Compiler/SR-013 正式入口 | Issue #12/#40；PR #46；CI #45837224652 |

| 2026-11-26 | 0.3.13 | GPT-6（ChatGPT） | 1.6.0 Host Context Publisher / 依赖边界 | 纠正 SR-024 仅为旧 Development Publisher，新增 SR-030 Schema-only 1.6.0 Host Context 发布链，并将来源 provenance 放回 Project Lock | Issue #12/#40；IR-006/008；SR-030 |
| 2026-11-26 | 0.3.14 | GPT-6（ChatGPT） | §4.4～§6、§9.5、修订记录 | 明确零 Capability roots 不等于零 Package dependency closure；增加 Schema-only Host Context Package 的 Compiler gate、Studio 测试和 AC-016-04 映射 | 消除 F09 原“零根不调用 Compiler”与“无外部依赖 Assurance 可 Build”之间的矛盾，确保 Schema-only 依赖可被正确消费 | Issue #12/#40；SR-013 AC-013-06；SR-016 AC-016-04；SR-030；PR #46 |
| 2026-11-26 | 0.3.15 | GPT-6（ChatGPT） | §5～§9、修订记录 | 同步 EC02 v0.2.12 与 SR-013 v0.2.18，保持 Schema-only Package / zero Capability roots 依赖契约一致 | 使 Studio Package Audit / AI Authoring 消费与 Compiler AC-013-06 使用同一 Schema-only 语义 | Issue #12/#40；EC02、SR-013、SR-016、SR-030；PR #46 |
| 2026-11-27 | 0.3.17 | ChatGPT / GPT-6 | 3GPP Schema/Codec 分阶段消费 | 对齐 SR-031 公共类型、T1 Request 与 T2 Codec Result，新增分期拒绝/验收范围 | 修复标准输入来源与实现门禁的跨仓断点 | IR-009；Issue #47；SR-031/026 |
| 2026-11-27 | 0.3.18 | ChatGPT / GPT-6 | 3GPP 原版发布裁决 | 版本随 OpenAMSM、原版 YAML 完全不改；将只读 Source Bundle 与可选 Adapter / Codec Output 分离 | 防止标准原件被类型适配误改 | Issue #47；SR-031/026 |
| 2026-11-27 | 0.3.19 | ChatGPT / GPT-6.2 | §10 | 将 Studio 从 Adapter Schema Explorer 改为原版 OAS3 只读展示 / 精确组件导航；Project Lock 固定 Source Bundle | 遵循原版标准直接引用且不允许编辑 | IR-009；Issue #47；SR-031/013/026 |
| 2026-11-27 | 0.3.20 | GPT-6.2（ChatGPT） | §9.3、修订记录 | AI Authoring 明确消费统一 SKILL 作者规范，加入 Node 粒度与注释非执行语义约束 | 防止 AI 生成的 Procedure 违背中央作者规则或用注释代替机器契约 | IR-008；Issue #49；SR-032 |
| 2026-11-27 | 0.3.21 | GPT-6.2（ChatGPT） | 文档头、§9.3 | 将 SR-032 纳入 F09 追踪；明确 Procedure Change Set 的允许字段、引用来源、非目标及 OUT_OF_SCOPE 行为，并区分 when 独立编辑路径 | 防止 AI Authoring 以“正式作者字段”为由擅自修改 Contract / Schema / Package 或发明外部身份 | IR-008；Issue #49；SR-032 |
| 2026-11-27 | 0.3.22 | GPT-6.2（ChatGPT） | §9.3 | 明确当 Procedure 修改需要同步 contract.precondition 时，Procedure-only Change Set 必须 OUT_OF_SCOPE | 防止 Node ID 变更导致跨文件引用悬空或部分应用 | Issue #49；SR-032 |
| 2026-11-27 | 0.3.23 | GPT-6.2（ChatGPT） | §9.2～9.3 | 增加共享 Schema / Script 的 LSP 与 AI 上下文读取规则；Script 运行只由正常 Runtime Host capability 提供，Studio 不建第二执行器 | 统一 Schema / Script 的作者体验、资源身份和运行边界 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.24 | GPT-6.2（ChatGPT） | §9.1、§9.3 | Package Explorer 将共享资源与 Capability 导航分区；修正 Procedure-only Change Set 的 assurance/predicates.yaml 路径 | 保持 Capability-only 导航和共享资源可见性，同时避免 Studio 错写作者路径 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.25 | GPT-6.2（ChatGPT） | §9.2～§9.3、修订记录 | 增加 Script ID 的 Procedure / Predicate LSP 补全与跳转；明确 Studio 不执行脚本，Host 暴露仍受双门禁控制；清理重复修订行 | 保持作者体验、Host Script Execution 和文档版本历史一致 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.26 | GPT-6.2（ChatGPT） | §6 | 将 SKILL.md-only 子路径更正为可携带共享资源的无 Assurance Skill Package | 使 Studio 的资源视图与 Agent 的无 Assurance 导入语义一致 | Issue #49；IR-008；SR-032 |
