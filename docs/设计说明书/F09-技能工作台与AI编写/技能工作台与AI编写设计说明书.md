# 技能工作台与AI编写设计说明书

> 文档类型：设计说明书  
> 文档版本：0.3.8  
> 状态：Capability-first Package Explorer / LSP / AI Authoring 目标设计已补充；Studio 消费端尚未实现/验收  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、额外 package-level digest、签名和 Trust Registry；仅保留 Compiler v2.1.0 Interface Package schema 明确要求的 `files[].sha256`  

关联 IR-006、SR-015、SR-016、SR-020（参考宿主架构审计）、SR-024（Host Context Publisher）、SR-025（MAS Owner Publisher）；Compiler 接口以 [EC02 Development Build 设计](../EC02-Compiler/Development%20Build设计.md) 为准。基线为 [docs/architecture/studio-boundaries.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/architecture/studio-boundaries.md)、[docs/design/ai-procedure-authoring.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/design/ai-procedure-authoring.md)。

## 1. 编辑与语言服务

Theia 的 Package Explorer 以作者源码为工作区入口。可视化视图、导航与诊断来自同一源码和语言核心，未保存缓冲区及包代际变化要驱动刷新；Browser Worker 失效后要给出可见状态。编辑器维护诊断、语义 token、补全和导航，规范锁固定到已发布版本。Package View 的 Dependencies 与 Build Artifacts 使用各自数据源，源码修改保留文本与未改动区域。

## 2. AI 编写

上下文与变更集由编辑宿主管理。模型和独立 Gateway 返回候选提案；宿主校验语义操作，将其转换为可预览的源码补丁。应用前对同一候选执行 Compiler gate，用户保存后才持久化。编辑器及 Gateway 不负责 Skill 选择、Runtime 执行或 Tool 调用。

## 3. when 编写与验收

正式语言刷新后，Contract 字段提示与诊断对齐中央规范。`when` 是 `assurance/contract.yaml` 中的可选顶层字段，不是 SKILL.md Front Matter 字段；其 Schema 类型、CEL 静态检查与错误定位必须对齐 CA-SL v1alpha5 作者规范。没有 `when` 的 Contract 保持原有行为。文本与 AI 编辑均保持可预览，不能把选择条件写入 Predicate。覆盖 Browser Worker、源码往返、已有包、有效与无效表达式、Compiler gate 与应用后再打开。

## 4. Interface Package 导入与项目快照

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

要让当前 MAS Example 使用 Compiler v2.1.0 Development Build，Owner 与 Host 必须分别发布正式 `connectionagent.io/interface-package/v1alpha1` 包。MAS Owner Publisher 由 [SR-025](../../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) 负责；Host Context Publisher 由 [SR-024](../../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md) 负责；Studio 只导入发布物，不代替 Publisher 组包。

### 4.5 两个 Contract root 的正式 Publisher 输出

Compiler v2.1.0 Development Build 使用 `connectionagent.io/interface-package/v1alpha1`。Studio 只导入正式 Publisher 输出，不在本地包装、改写或伪造 Owner/Host Package。MAS Owner 与 Host Context 是两个独立发布任务：MAS Publisher 由 [SR-025](../../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) 负责；Host Publisher 由 [SR-024](../../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md) 负责；Studio 的 Import / Lock / Compiler 集成由 SR-016 负责。

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

- 固定 Package ID：`urn:connectionagent:ca:host-context`；Publisher：`urn:connectionagent:owner:ca-context`；Language Target：`connectionagent.io/v1alpha5`。Subject Schema 的 `$id` 版本仍为 `v1`；Compiler Interface Package version 为 `1.0.0`，由 SR-024 实现。
- ZIP 仅含根 `package.json` 与原始 `subject.schema.json`；只导出一个 `Schema`，ID 精确为 `urn:connectionagent:ca:context:subject:v1`；`dependencies=[]`；`files[]` 只列出原始 Schema 文件的 SHA-256。不得重写或重新序列化 Schema。
- Source Revision `57e277ff9094dad93543df46910a12a1dbbaf560` 与 Git blob `4faee66642b8bc5eb2e45c131be4688b982037d8` 固定在 SR-024 / Publisher 验收中；Studio lock 不重复保存 source Revision/Git blob。该包是 Development fixture，不是生产 Host Trust 或 Admission。

**Studio Lock 与共同边界**

- `sourceStatus=DEVELOPMENT_FIXTURE` 只由 Studio 写入 `skillc.lock/v0.1` 的 `source.sourceStatus`；不得写入任何正式 `package.json`。这项持久化由 SR-016 / Studio #269 验收。SR-024 已固定 Host source Revision/Git blob，不要求项目锁重复保存。
- #267 ZIP Import 和 #270 MAS Example preload 已 MERGED，不得再列为尚未实现的前置。#269 仍负责 Development BuildRequest、Package Audit、AI Authoring Compiler Gate 和 no-root 诊断。
- 两个 Publisher 都只发布静态 Interface Package；`publisher` 是声明身份，不是 Owner Trust。Compiler v2.1.0 Development BuildRequest 不接受 `trustedBuildContext`、Owner attestation、Deployment Grant、live Evidence 或 Provider binding；成功结果仍为 `VALIDATED / LINKED / BUILT / NOT_ADMITTED`，不代表 Host Admission 或 Runtime Execution。
## 5. Compiler Development Build 与状态投影

### 5.1 单一 Build 路径

Package Audit 和 AI Authoring 必须共用同一个 Development Build request builder、Compiler v2.1.0 Worker/WASM 与 VerifyDevelopment。不得各自实现 Linker、依赖闭包、摘要或结果解释，也不得在 Development Build 失败时静默回退到冻结 v1alpha5 Build/Verify v2.0.2。

- Package Audit 对当前保存源码和当前 lock generation 进行 Build + VerifyDevelopment。
- AI Authoring 对**同一候选源码字节**和同一 lock generation 进行 Build + VerifyDevelopment；候选变更或 lock generation 改变立即使旧 Build/Verify 结果失效。
- 仅在候选的 Build + VerifyDevelopment 成功后，才允许显示可应用的候选；Apply 仍需用户明确确认。Apply 使用原生编辑器 Buffer，Undo 必须恢复精确原文；Save 由用户决定。
- Worker 只执行 Compiler Core，不下载依赖、不访问项目文件系统、不读取 Provider credentials、不授予 Owner Trust、不执行 Runtime Tool。

### 5.2 结果状态

Compiler Development Build 成功结果固定为：

| 字段 | 成功值 | 含义 |
|---|---|---|
| `sourceStatus` | `VALIDATED` | 当前源码通过 Compiler 静态检查 |
| `interfaceLinkStatus` | `LINKED` | Contract roots 和完整 Interface Package 闭包链接成功 |
| `artifactStatus` | `BUILT` | Development Artifact 已生成 |
| `executionStatus` | `NOT_ADMITTED` | 不授予 Host/Runtime 执行资格 |

失败时，失败阶段为 `FAILED`，后续未执行阶段为 `NOT_RUN`，不得返回部分 Artifact。Host Admission Requirements 和 Runtime Execution Requirements 是不同集合，不能把 Requirement 缺失、Build 成功或 `NOT_ADMITTED` 误报为真实 Owner 授权或 Runtime 结果。

Package Explorer、LSP、Problems 与 AI Workbench 必须区分源码诊断、接口链接诊断、Artifact 状态、Host Admission Requirement 和 Runtime Execution Requirement。Compiler 未运行、未链接或没有 Artifact 时不得显示 Build PASS。注意：BuildResult 顶层 `sourceStatus=VALIDATED` 与 Studio 项目锁中的 `source.sourceStatus=DEVELOPMENT_FIXTURE` 属于不同对象、不同语义，不得互相覆盖或由一方推导另一方。

## 6. 无 Assurance、零根依赖与 no-root 状态

- 只有 `SKILL.md`、没有 `assurance/` 的 Skill 按 CA-SL v1alpha5 走 LLM-guided only 路径：不调用 Compiler，不构造 Development BuildRequest，不生成 Deterministic Artifact。
- 存在 Assurance 但 `contract.dependencies` 没有根依赖的 Skill，不能直接调用当前 Compiler v2.1.0 Development Build：冻结的 BuildRequest / Interface Dependency Lock 契约要求非空 `snapshots`、`roots` 和 `packages`。
- Studio 必须显示显式 `NO_INTERFACE_ROOTS` / `BUILD_NOT_RUN` 状态和可理解的诊断，不合成假 Package、不构造空 roots 请求、不回退冻结 v2.0.2 Build、不生成 Artifact，也不伪造 `NOT_ADMITTED`（该值只来自成功 Development BuildResult）。
- 本地编辑器语法提示可以继续工作，但不得将本地提示冒充 Compiler `VALIDATED`。Compiler 未运行时，其 `sourceStatus` 是 `NOT_RUN`，或根本不存在 BuildResult。
- 如果产品需要“零外部依赖的 Assurance Skill 也生成确定性 Artifact”，必须另立 Compiler 契约变更并发布新契约版本；不得改变 v2.1.0 冻结 Schema 或在 Studio 中私自扩展。

## 7. 当前实施状态与验收门槛

截至 2026-11-25：

| 项目 | 状态 | 证据 / 未完成 |
|---|---|---|
| ZIP Import / immutable snapshot / Package Explorer | MERGED | [Studio #267](https://github.com/odango-chan/ca-skill-studio-demo/pull/267)，main merge `11b1246` |
| Default Example dependency preload | MERGED | [Studio #270](https://github.com/odango-chan/ca-skill-studio-demo/pull/270)，main merge `d3b1d36` |
| Compiler v2.1.0 request builder | OPEN / DRAFT / STALE | [Studio #272](https://github.com/odango-chan/ca-skill-studio-demo/pull/272)，测试 HEAD `8abffc7`，当前落后 main 67 commits |
| Compiler v2.1.0 Node/Browser Worker | OPEN / DRAFT / STALE | [Studio #276](https://github.com/odango-chan/ca-skill-studio-demo/pull/276)，测试 HEAD `7d6adeb`，落后 #272 base 9 commits |
| Package Audit Development Build cutover | NOT_IMPLEMENTED | [Studio #269](https://github.com/odango-chan/ca-skill-studio-demo/issues/269) |
| AI Authoring exact-candidate Development Build gate | NOT_IMPLEMENTED | [Studio #269](https://github.com/odango-chan/ca-skill-studio-demo/issues/269) |
| MAS / Host Context formal Interface Package publication | BLOCKED | 当前锁定 kind 分别为 `tool-catalog` / `schema-bundle`；MAS Owner Publisher 归 SR-025，Host Context Publisher 归 SR-024；两个 Package ID 各自使用首版 `1.0.0`，发布物尚未产生 |
| Host fixture provenance in Studio lock | NOT_IMPLEMENTED | #267 已持久化 ZIP source metadata（upload/contentDigest/packageId/version/publisher），但尚未写入 `source.sourceStatus`；由 SR-016 / Studio #269 补齐 |
| Real released ca-client-tools v1.1.0 as Compiler root | NOT_RUN | 需显式 `ca-client` synthetic Contract 正例 |
| No-root UI state | NOT_IMPLEMENTED | 不调用 Compiler、无 Artifact、无 `NOT_ADMITTED` |

#272 / #276 曾在各自历史 HEAD 通过 PR Verify、Native Windows、IDE Host、Theia Browser-Only、Theia Browser Host 和 Pages Chromium 等检查，但当前分支分别落后 main / base；历史 PASS 不满足当前合并门禁。必须在刷新分支后重跑完整 exact-head 验收。

必要验收至少包括：原始发布 ZIP 导入/锁定字节一致性；Contract root closure 只包含可达 Interface Packages；无关项目依赖不进入 BuildRequest；声明为非 Interface Package 的 root fail-closed；缺失/损坏/摘要错/传递依赖环拒绝；零根不调用 Compiler；Node/WASM/Chromium 结果一致；AI 候选 stale invalidation、Apply/Undo 和磁盘未保存语义。所有结果只证明相应静态/编辑器层，不代表 Owner/Host Admission、Runtime、Production 或真实 5GC Qualification。

## 8. 历史决策

EC06 历史决策已统一归档于中央仓：[ADR-0001 Source-first Visual](../../决策记录/EC06-ADR-0001-Source-first-Visual.md)、[ADR-0002 IDE Host Spike](../../决策记录/EC06-ADR-0002-IDE%20Host%20Spike.md)、[ADR-0003 Theia 原生工作台与 Markdown](../../决策记录/EC06-ADR-0003-Theia原生工作台与Markdown.md)、[ADR-0004 Package 优先工作区](../../决策记录/EC06-ADR-0004-Package优先工作区.md)、[ADR-0005 固定源码与预览工作台](../../决策记录/EC06-ADR-0005-固定源码与预览工作台.md)。Classic 为历史迁移证据。原始设计材料包括 [Studio boundaries](../../架构设计/外部能力域/EC06-Skill%20Studio所有权与源码边界原文.md)、[Authoring Workbench](../外部能力域/EC06-Skill%20Studio/Authoring%20Workbench设计原文.md)、[Plugin-managed Configuration v0.1](../外部能力域/EC06-Skill%20Studio/Plugin-managed%20Configuration%20%26%20Tool%20Integration%20v0.1原文.md) 和 [C4 Package Overview](../外部能力域/EC06-Skill%20Studio/C4%20Package%20Overview原文.md)；当前目标设计仍以本文为准。

## 9. Capability-first Package Explorer 与 LSP

### 9.1 唯一能力入口

Skill Studio 的 Package Explorer 以 Capability 作为唯一 Skill-facing 能力导航入口。Package 依赖仍按 Package 分组；Package 内显示 Capability，不再并列展示 Tools / Operations / Callable 树。Capability 详情可显示描述、kind、Effect、Input/Output Schema、Evidence 和来源 Package；Callable ID 只允许出现在内部 Binding 详情或编译诊断，不作为可选择的作者节点。

### 9.2 语言服务

v1alpha6 LSP / Completion 对 Contract.capabilities、operation.capability、observation.capability 提供 Capability ID 补全、悬停、定义跳转和静态诊断。补全来源是已导入并固定的 Package Capability exports，不是运行时 Provider catalog。Compiler 仍是 Capability membership、唯一性、Schema、Evidence、Scope 的最终 Link 权威；LSP 不得把本地投影诊断显示为 Compiler Build PASS。

### 9.3 AI Authoring

AI Authoring 的 Change Set 只能新增或修改 Capability ID、Procedure arguments 和其他 CA-SL 作者字段；不得生成 Callable ID、backendOperationId 或动态 Provider 选择。Apply 后使用同一语言服务和 Compiler BuildRequest / Verify 路径重新检查。

### 9.4 版本与导入

- 当前已发布 v1alpha5 Package / Skill 快照保持原样，不做自动迁移。
- v1alpha6 Package 必须声明唯一 languageTarget，并使用满足一对一约束的 Capability exports。
- v1alpha5 / v1alpha6 不得在同一项目中通过兼容别名混合解析；不支持的 languageTarget 明确报错。
- 当前 Studio #267/#269 的既有实施状态不因本设计自动升级；Capability Explorer、LSP 和新 Package 消费仍是未实施目标。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F09 · IR-006 · SR-016 |
| 2026-11-25 | 0.2.0 | GPT-6 | §4–7 | 明确 Studio 项目锁与 Compiler Lock 的边界、当前 MAS roots 的 package-kind 不匹配、no-root 行为、统一 Development Build gate 和当前 PR 新鲜度门禁。 | Studio #261、#267、#269、#270、#272、#276；EC02 Development Build |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §3–7 | 明确 when 位于 `assurance/contract.yaml`；补齐 MAS Owner / Host Context Interface Package 的 Publisher 字段、导出闭包、精确来源与 Development provenance 边界，并关联 SR-015 / SR-020。 | IR-006 · SR-015 · SR-016 · SR-020 · Studio #269 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §4.4～7 | 将 Host Context Interface Package Publisher 从 SR-020 拆分到新 SR-024；SR-020 保留参考宿主架构审计职责；明确仅使用 Compiler v2.1.0 schema 要求的 files[].sha256 | 避免一个 SR ID 承载两项不同工作，并区分既有 Interface Package 文件摘要与 CA-SL Skill Artifact 的非目标完整性体系 | IR-006；SR-015、SR-016、SR-020、SR-024；Studio #261/#269/#272/#276 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4.4～7 | 修复 SR-024 Publisher 文档链接并同步 F02/F08/SR-016/SR-024 版本；明确 SR-020 只承担参考宿主审计 | 解决 SR-020/SR-024 责任冲突，确保 Publisher 入口唯一 | IR-006；SR-015、SR-016、SR-020、SR-024 |
| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | §4.5、§5.2、§7 | 对照 Studio #267 合入代码，明确 `source.sourceStatus` 尚未写入 lock，并将其归入 SR-016/#269；区分项目来源元数据与 Compiler BuildResult.sourceStatus | 避免把设计要求误报为当前持久化能力，防止两个 sourceStatus 语义混淆 | Issue #12；SR-016、SR-024；Studio #267/#269 |
| 2026-11-25 | 0.3.4 | GPT-6.2（ChatGPT） | §8 | 将 EC06 ADR-0001/0002 与 Plugin-managed/C4 原文纳入中央仓，并将 F09 历史决策和原始设计引用切换为 Next 内部链接 | 关闭原始设计缺失与跨仓引用断链；不改变历史决策内容 | Issue #12；EC06-ADR-0001～0005；SR-016、SR-024 |

| 2026-11-25 | 0.3.5 | GPT-6.2（ChatGPT） | §4.5、§6～7 | 将 MAS Owner Publisher 独立归入 SR-025、Host Publisher 归入 SR-024；按 Compiler v2.1.0 修正 MAS exports 为 25/24/25/53；发现 v1alpha4/v1 非 SemVer，提出 package/source version 分离决策门槛 | 防止发布无法被 Development Build 接受的版本，同时保持 Owner/Host 源身份与 Studio lock 边界 | IR-006 · SR-015 · SR-016 · SR-024 · SR-025 · Studio #269 |
| 2026-11-25 | 0.3.6 | Codex / GPT-6 | 正文 | 同步两个 Publisher 的 1.0.0 身份与消费边界 | Issue #12 |
| 2026-11-25 | 0.3.7 | Codex / GPT-6 | 正文 | §4.5 依据 v2.1.0 源函数实测修正 +build 与项目包身份限制 | Issue #12 |
| 2026-11-26 | 0.3.8 | GPT-6.2（ChatGPT） | §9 | 定义 Capability-only Explorer、LSP 补全与 AI Authoring 约束 | 避免 Studio 把 Callable / Tool 作为 Skill 作者可选择入口 | IR-008；SR-029；Issue #40 |
