# 技能工作台与 AI 编写设计说明书

> 文档类型：外部能力集成与工作台设计说明书  
> 文档版本：0.2.0  
> 状态：目标设计已重建；Studio 当前实现与下一版本架构存在差异，需按 §11 逐项验收  
> 功能归属：F09 — 技能工作台与 AI 编写；EC06  
> 关联 IR：IR-006  
> 关联 SR：SR-016、SR-023  
> 修订日期：2026-11-25  
> 适用范围：Theia Browser-Only 工作台、CA-SL v1alpha5 编辑、Package View、LSP、Source-first Visual Editor、AI Authoring

## 1. 定位与所有权

Skill Studio 是 Skill 作者工具和源码编辑器，不是 Agent Runtime、Skill Selector、Compiler、Tool Provider 或 5GC Owner。源文件是唯一业务真源；图、节点、边、布局、Inspector、诊断和 AI 候选都是从当前源码投影出来的视图或变更提案。

~~~text
Skill Source Files
  -> YAML 1.2 CST / source spans
  -> Semantic Projection / Package Context
  -> Graph / Outline / Inspector / Problems / Data Flow
  -> bounded Source Patch proposal
  -> reparse + semantic validation
  -> Diff / explicit confirmation
  -> native WorkspaceEdit / Undo / Save
~~~

责任分工：

- ca-skills：CA-SL 规范、Skill 作者源和业务 Skill。
- ca-skill-compiler：唯一 Compiler、静态检查、链接、Build/Verify 和运行时 Artifact。
- ca-agent-next：Skill Bundle 导入、SkillCatalog、Resolver 和 Runtime。
- ca-skill-studio-demo：编辑器、语言服务、可视化投影、源码 Patch、AI Authoring UI。
- ai-gateway：模型协议、Provider credential 和请求转发。
- Studio 不执行 Skill、不调用业务 Tool、不写 Owner 状态、不代替 Runtime 证据。

## 2. 宿主与工作台架构

当前交付以 Theia Browser-Only / 静态 Pages 为主要入口，复用 Theia 原生 Explorer、Editor、Outline、Problems 和 Markdown Preview。工作台通过 VS Code Web Extension 适配器接入 Theia；共享的语言核心、源码投影和 Patch Engine 不依赖具体宿主。

默认编辑体验保持双栏：左侧源码，右侧预览；禁止增加常驻第三栏。Package Explorer 默认可见，依赖信息只读。Outline、Problems 使用宿主原生视图。Markdown 预览使用固定版本的原生 VS Code Markdown extension，不再维护 Classic 自研 Markdown Preview 作为默认入口。

宿主适配层只负责 TreeDataProvider、TextDocument、Workspace FS、DiagnosticCollection、WorkspaceEdit 和 Webview 生命周期，不重新定义 CA-SL 语义。

## 3. Package 工作区与源码权威

一个 Package 是编辑、诊断、导出和 Compiler 检查的边界。Package Context 必须绑定完整文件清单和 generation。未保存的 TextDocument Buffer 优先于磁盘内容；文档变更、Package import/update 和依赖快照变化都使相关 generation 失效。

Source 文件可以被用户编辑；依赖/生成产物不能被当作普通作者源。当前源仓的 Plugin-managed Studio v0.1 设计将 Package Dependencies 交给 Plugin Dependency Service，不再要求固定的 lib/ 和 output/ 目录。现有 main 代码和测试仍包含早期 skills/lib/output 布局，因此二者是“当前实现”与“下一版本目标”的差异，不能把早期目录直接写成新契约。迁移前应保持用户文件不被覆盖，结构变化需要单独验收。

Package View 至少展示：
- 当前 Package 与 Skill Source；
- Plugin-managed Dependencies 的来源、版本和只读快照；
- 真实 Compiler BuildResult 存在时才显示 Build Artifacts；
- 缺少依赖、文件、Schema 或 Compiler Result 时显示明确 unavailable，不生成虚假状态。

## 4. Source Editor 与 Visual Editor

YAML 源文本是唯一权威数据。Procedure Preview 从解析器和源码 span 构建 Node/Route 投影；ELK 负责布局，React Flow 负责展示和交互。Node、Edge、坐标、折叠状态、Inspector selection 不得写成第二份业务定义。

任何可视化编辑必须：

1. 绑定当前文档 URI、版本、Package generation 和精确 YAML source span。
2. 检查语法与结构处于支持范围；未知/歧义结构降级为 Source-only。
3. 构造有界 Patch，不重写无关节点、注释、顺序或原始字段。
4. 重新解析候选源码并做结构/语义对比。
5. 显示精确 Diff，由用户显式确认。
6. 通过宿主原生 WorkspaceEdit 写入当前 Buffer，保留 Undo/Redo。
7. 源版本变化、span 失效或候选不再等价时拒绝 Apply。

不允许通过重新序列化整份 YAML 破坏用户格式或注释。

## 5. LSP 与语言服务

LSP Server/Browser Worker 是只读语言服务，使用同一共享分析器。跨文件导航必须绑定完整 Package generation 和精确 UTF-16 source range。

支持范围以实际实现为准，当前源设计包括：
- Definition：Procedure/Predictate Script 路径定位脚本 metadata；Python input/output Schema metadata 定位 Schema 标题。
- References：返回精确引用点并遵守 includeDeclaration。
- Hover：显示源码可证明的 Script、Tool、Schema 和 Python 顶层声明信息。
- Document Symbols：Python 顶层 class/function。
- Completion：仅在已支持的 Script path 和 Schema metadata 上给出 Package-local 候选。
- Diagnostics：编辑期跨文件问题、缺失文件和已知结构错误。

负向边界：
- 不做完整 Python 类型检查，不替代 Pyright/Pylance。
- 不把 LSP 诊断当 Compiler PASS。
- Package 不完整、重复名称、source range 歧义、generation 过期时不猜测导航目标。
- 不因模型或文件名推断 Tool eligibility、Runtime 能力或 Owner 状态。

## 6. AI Authoring Workbench

AI Authoring 是源码修改助手，不是自动执行 Agent。模型只生成结构化 Change Set；宿主拥有上下文、Source revision、语义 Patch、Diff、验证、Apply 和保存。

流程：

~~~text
用户任务
  -> Context disclosure / user consent
  -> Package snapshot（包含未保存 Buffer）
  -> AI Gateway / OpenAI-compatible model
  -> structured Change Set
  -> Host schema + semantic operation validation
  -> source Patch Engine
  -> candidate Procedure
  -> Compiler Check gate
  -> current vs candidate preview / YAML diff
  -> user accepts atomic groups
  -> native WorkspaceEdit
  -> user Save
~~~

关键决策：
- 第一阶段只修改现有 CA-SL v1alpha5 Procedure，不支持旧版本兼容。
- 不允许模型直接写文件；模型输出必须符合 Change Set schema 和 operation allowlist。
- Change Set 由 Studio Host 管理，具有 base revision、目标 Package、目标文件和原子组。
- Apply 前必须重新验证 Source revision，冲突时拒绝过期提案。
- 用户可逐原子组接受/拒绝；不能应用的组明确说明原因。
- Apply 只写入当前 TextDocument Buffer，保存仍由用户完成。
- Compiler gate 必须使用真实 Compiler 结果；缺少 Compiler 能力时禁用 Apply，不用本地轻量检查冒充 Compiler PASS。
- 不自动触发 Runtime、Tool 或真实 5GC 副作用。

## 7. AI Gateway 与部署边界

Gateway 是独立 Go 服务，提供 OpenAI-compatible 请求/响应协议和统一 Provider credential。浏览器 Studio 不持有模型 Provider Key；Gateway credential 由部署者配置。可部署在 loopback 或可信内网；不依赖 Cloudflare，也不要求每个用户管理自己的模型 Key。

Studio 保存 Gateway URL、模型选择和部署配置；Provider/model availability 由 Gateway 报告。网络不可达、认证失败、Provider 返回错误、超时和模型响应 Schema 错误都必须显示可诊断错误，不生成伪候选。

## 8. React Flow 当前/候选对比

当前与候选 Procedure 双图对比只读，不产生新的业务图模型。两张图共享 CA-SL v1alpha5 source analyzer、ELK layout 和 React Flow projection。Node/Stage/Route 的新增、修改、删除和重定向使用精确 Source identity 标记。点击图元素只定位对应 Change Set 原子组和源码行，不直接接受变更。

默认显示所有路径，避免折叠隐藏失败/恢复路径的变化；“仅显示正常路径”是显式视图选项。图投影失败时回退到语义 Outline 和 YAML Diff，不影响 Compiler fail-closed 规则。

## 9. Package 生命周期与恢复

- 导入 Package 时创建完整 inventory 和 generation。
- 当前打开的未保存文档优先作为分析输入。
- 删除、移动、重命名或依赖变化后重新计算 Package Context。
- Browser Worker 崩溃或协议失败时显示失败状态，禁止使用陈旧诊断/导航结果。
- stale LSP result、stale graph selection 和 stale AI proposal 必须由 generation/document version 检查拒绝。
- ZIP 导出保持文件路径和内容；下载 ZIP 不等于本地磁盘原位保存或 GitHub 提交。

## 10. 验收

- Browser-Only 和 Theia Host 使用同一 Source analyzer、Patch Engine 和 Change Set schema。
- 双栏 Source/Preview、Package View、Outline、Problems、Markdown 原生 Preview 行为一致。
- YAML round-trip 保持注释、键顺序和未修改区域字节身份。
- 可视化 Patch 精确 span、Diff、确认、Undo/Redo 和 stale rejection 全部有正负向测试。
- LSP 对 CRLF、Unicode、multiline YAML 的 UTF-16 offsets 正确；不完整 Package 不猜测跨文件目标。
- AI Context 只包含用户授权文件；请求前展示披露；Gateway key 不进入浏览器或日志。
- Change Set schema、operation allowlist、atomic groups、stale revision、Compiler gate、Apply 和 Undo 均有测试。
- React Flow 双图与当前 main 的 Change Set 对照测试通过；失败时 Source/Outline fallback。
- Runtime/5GC 执行不在本仓验收范围。

## 11. 当前实现审计与待决差异

| 能力 | 当前证据 | 状态 |
|---|---|---|
| Theia Browser-Only / 原生 Explorer、Outline、Problems | Studio main 架构和迁移文档 | IMPLEMENTED |
| Source-first Visual Editor、ELK / React Flow、精确 Patch / Diff | Studio 多份设计与实现记录 | IMPLEMENTED（支持范围受限） |
| LSP Browser Worker、导航、诊断 | LSP L2 设计及主线测试 | IMPLEMENTED（仅声明范围） |
| Package Explorer / Dependencies | 当前 main 使用早期 skills/lib/output 工作区，Plugin-managed v0.1 是后续目标 | PARTIAL / TARGET DESIGN |
| AI Gateway | 独立 Gateway main 有可运行 Go 服务；Studio 连接和模型调用有真实 Smoke 证据 | IMPLEMENTED / DEMO |
| AI Workbench Change Set / Compiler gate | 原始设计与多个已合并实现切片 | PARTIAL；以当前 main 测试逐项核对 |
| React Flow current/candidate 双图 | PR #258 已 MERGED，head 428d818f441dcec819825752596a1bec22161823 | IMPLEMENTED |
| Pages 部署 | 本轮未独立核对最新部署 SHA | UNVERIFIED |
| 完整 CA-SL v1alpha5 编译一致性 | 依赖 Compiler #61 新版 when Artifact | BLOCKED / NOT_RUN |
| Runtime / OpenAMSM E2E | 非 Studio 所有权 | NOT_APPLICABLE |

## 12. 原始设计资产

- [Studio ownership / source authority 原文](../../架构设计/外部能力域/EC06-Skill%20Studio所有权与源码边界原文.md)
- [Theia workbench 架构与迁移原文](../../架构设计/外部能力域/EC06-Theia工作台架构与迁移原文.md)
- [AI Procedure Authoring Workbench 原文](../外部能力域/EC06-Skill%20Studio/AI%20Procedure%20Authoring%20Workbench设计原文.md)
- [Authoring Workbench 原文](../外部能力域/EC06-Skill%20Studio/Authoring%20Workbench设计原文.md)
- [LSP 语言导航设计原文](../外部能力域/EC06-Skill%20Studio/LSP语言导航与补全设计原文.md)
- [Theia / Package-first ADR](../../决策记录/EC06-ADR-0004-Package优先工作区.md)
- [React Flow 双图 PR #258](https://github.com/odango-chan/ca-skill-studio-demo/pull/258)

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 按最新 Studio 架构、AI Authoring、LSP 和 PR #258 恢复完整目标设计，并分离当前实现与 Plugin-managed v0.1 目标 | Issue #12；SR-016 |
