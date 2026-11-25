# 技能工作台与AI编写设计说明书

> 文档类型：设计说明书  
> 文档版本：0.3.2  
> 状态：待评审  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、额外 package-level digest、签名和 Trust Registry；仅保留 Compiler v2.1.0 Interface Package schema 明确要求的 `files[].sha256`  

关联 IR-006、SR-015、SR-016、SR-020（参考宿主架构审计）、SR-024（Host Context Publisher）；Compiler 接口以 [EC02 Development Build 设计](../EC02-Compiler/Development%20Build设计.md) 为准。基线为 [docs/architecture/studio-boundaries.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/architecture/studio-boundaries.md)、[docs/design/ai-procedure-authoring.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/design/ai-procedure-authoring.md)。

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

要让当前 MAS Example 使用 Compiler v2.1.0 Development Build，Owner 与 Host 必须分别发布正式 `connectionagent.io/interface-package/v1alpha1` 包。发布任务分别归入 [SR-015](../../SR/SR-015-工具契约设计移交.md)（MAS Owner）和 [SR-024](../../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md)（Host Context）；Studio 只导入发布物，不代替 Publisher 组包。

### 4.5 两个 Contract root 的正式 Publisher 输出

两个包的 `package.json` 必须严格符合 Compiler v2.1.0 的 [interface-package.schema.json](https://github.com/odango-chan/ca-skill-compiler/blob/v2.1.0/contracts/development/v1alpha1/interface-package.schema.json)：`apiVersion`、`packageId`、`version`、`languageTarget`、`publisher`、`dependencies`、`exports`、`files` 为完整字段集合；Schema `additionalProperties: false`，不得添加 `sourceStatus` 等自定义字段。`files[]` 的 SHA-256 必须针对实际包内的精确文件字节计算；这是已发布 Interface Package schema 的逐文件字段，不是 CA-SL Skill Artifact 的额外包级完整性体系。不得增加 manifest-level digest、签名或 Trust Registry。新生成的 `package.json` 是正式 Interface Package envelope；它不能冒充或覆盖 Owner 原有的 `manifest.json`。

**MAS Owner 包**

- 固定身份：`packageId=urn:openamsm:mas:tool-contracts`、`version=v1alpha4`、`publisher=openamsm.smf.mas`、`languageTarget=connectionagent.io/v1alpha5`。
- 权威来源：`odango-chan/ca-client-tools` tag `v1.2.0`，目录 `contracts/owner/openamsm-mas/v1alpha4`，解析 Revision `fc44c3a745c68443fcfb12054c7eadf0ed7cc3f7`，Owner source `buildIdentity=sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0`。
- `CallableCatalog` exports 从 `tool-catalog.yaml` 的正式 `spec.contracts[].id` 逐项生成；`CapabilityCatalog` exports 从 `capability-contracts.yaml` 的 capability ID 生成；`EvidenceDescriptor` exports 从 `evidence-guarantees.yaml` 的 fact ID 生成；`Schema` exports 覆盖这些公开接口及其 `$ref` 闭包中的精确 Schema `$id`。Export ID 必须取自源契约，不得由 Studio 猜测。
- 保留上述公开契约文件及 Schema 文件的原始字节；先按 Owner source `manifest.json` 校验来源工件，再由 Publisher 生成正式 `package.json`。`manifest.json` 的 `connectionagent.io/toolcatalog/v1alpha4` 是 Owner source manifest，不是 Interface Package manifest。
- `deployment-binding.yaml` 及其部署私有数据、Runtime-only Provider bindings 不得进入公开 exports 或包文件闭包；仅导出 Skill/Compiler 静态链接实际需要的公开接口。不得把 `ca-client-tools#37` 的 private Runtime-only bindings 包装成 public Callable。

**Host Context Development fixture 包**

- 固定身份：`packageId=urn:connectionagent:ca:host-context`、`version=v1`、`publisher=urn:connectionagent:owner:ca-context`、`languageTarget=connectionagent.io/v1alpha5`。
- 权威来源：`odango-chan/ca-agent-demo` Revision `57e277ff9094dad93543df46910a12a1dbbaf560`，目录 `tests/fixtures/compiler/mas-v1alpha5-scheme-c/trusted/snapshots/ca-context`，文件 `subject.schema.json`，Git blob `4faee66642b8bc5eb2e45c131be4688b982037d8`。
- 发布一个 `Schema` export，ID 精确等于 Schema `$id` `urn:connectionagent:ca:context:subject:v1`，路径为包内原始 `subject.schema.json`；不得重写或重新序列化 Schema 字节。
- `sourceStatus=DEVELOPMENT_FIXTURE` 保留在 Studio `skillc.lock/v0.1` 的 `source` provenance 中；不得写入 `package.json`。Compiler BuildRequest 的 `profile=DEVELOPMENT` 表示构建档位，二者都不授予 Host Admission。

**共同边界**

- 两个 Publisher 都只生成正式静态 Interface Package；`publisher` 是声明身份，不是 Host 已验证的 Owner Trust。
- `dependencies` 只列出实际 Interface Package 依赖；无依赖时使用空数组。不得通过 Studio 重写包字节、改 Package ID、猜测 Export ID 或合成 Owner/Host 授权。
- Compiler v2.1.0 Development BuildRequest 不接受 `trustedBuildContext`、Owner attestation、Deployment Grant 或 Provider binding。成功结果仍是 `VALIDATED / LINKED / BUILT / NOT_ADMITTED`；Host Admission 与 Runtime Execution 继续独立处理。

`ca-client-tools_interface_1.1.0.zip` 仍应作为独立的真实发布包正例：使用一个 Contract 明确声明 `ca-client` alias 与精确 Package ID 的 synthetic Skill 验证 Compiler v2.1.0。该测试证明真实 ZIP 与 Compiler 契约互操作，不代表 MAS Create/Modify/Release Example 已链接或 Qualified。

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

Package Explorer、LSP、Problems 与 AI Workbench 必须区分源码诊断、接口链接诊断、Artifact 状态、Host Admission Requirement 和 Runtime Execution Requirement。Compiler 未运行、未链接或没有 Artifact 时不得显示 Build PASS。

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
| MAS / Host Context formal Interface Package publication | BLOCKED | 当前锁定 kind 分别为 `tool-catalog` / `schema-bundle`；Publisher 设计与验收归入 SR-015 / SR-024，尚未发布 |
| Real released ca-client-tools v1.1.0 as Compiler root | NOT_RUN | 需显式 `ca-client` synthetic Contract 正例 |
| No-root UI state | NOT_IMPLEMENTED | 不调用 Compiler、无 Artifact、无 `NOT_ADMITTED` |

#272 / #276 曾在各自历史 HEAD 通过 PR Verify、Native Windows、IDE Host、Theia Browser-Only、Theia Browser Host 和 Pages Chromium 等检查，但当前分支分别落后 main / base；历史 PASS 不满足当前合并门禁。必须在刷新分支后重跑完整 exact-head 验收。

必要验收至少包括：原始发布 ZIP 导入/锁定字节一致性；Contract root closure 只包含可达 Interface Packages；无关项目依赖不进入 BuildRequest；声明为非 Interface Package 的 root fail-closed；缺失/损坏/摘要错/传递依赖环拒绝；零根不调用 Compiler；Node/WASM/Chromium 结果一致；AI 候选 stale invalidation、Apply/Undo 和磁盘未保存语义。所有结果只证明相应静态/编辑器层，不代表 Owner/Host Admission、Runtime、Production 或真实 5GC Qualification。

## 8. 历史决策

保留 [docs/decisions/0001-source-first-visual.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0001-source-first-visual.md) 与 [docs/decisions/0002-ide-host-spike.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0002-ide-host-spike.md)；Classic 为历史迁移证据。Package-first 见 [docs/decisions/0004-package-first-workspace.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0004-package-first-workspace.md)。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F09 · IR-006 · SR-016 |
| 2026-11-25 | 0.2.0 | GPT-6 | §4–7 | 明确 Studio 项目锁与 Compiler Lock 的边界、当前 MAS roots 的 package-kind 不匹配、no-root 行为、统一 Development Build gate 和当前 PR 新鲜度门禁。 | Studio #261、#267、#269、#270、#272、#276；EC02 Development Build |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §3–7 | 明确 when 位于 `assurance/contract.yaml`；补齐 MAS Owner / Host Context Interface Package 的 Publisher 字段、导出闭包、精确来源与 Development provenance 边界，并关联 SR-015 / SR-020。 | IR-006 · SR-015 · SR-016 · SR-020 · Studio #269 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §4.4～7 | 将 Host Context Interface Package Publisher 从 SR-020 拆分到新 SR-024；SR-020 保留参考宿主架构审计职责；明确仅使用 Compiler v2.1.0 schema 要求的 files[].sha256 | 避免一个 SR ID 承载两项不同工作，并区分既有 Interface Package 文件摘要与 CA-SL Skill Artifact 的非目标完整性体系 | IR-006；SR-015、SR-016、SR-020、SR-024；Studio #261/#269/#272/#276 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4.4～7 | 修复 SR-024 Publisher 文档链接并同步 F02/F08/SR-016/SR-024 版本；明确 SR-020 只承担参考宿主审计 | 解决 SR-020/SR-024 责任冲突，确保 Publisher 入口唯一 | IR-006；SR-015、SR-016、SR-020、SR-024 |
