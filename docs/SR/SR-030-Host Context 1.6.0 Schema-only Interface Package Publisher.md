# SR-030：Host Context 1.6.0 Schema-only Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.1.11
> 状态：整项 DRAFT；阶段 READY（中央只读核验）。AC-030-01 固定源，06/07 设计约束。  
> 下一步：核对 Subject Schema 原始字节与来源、Provenance 归属和 Demo 排除项。02～05、Publisher 实现与发布等待正式 Schema/languageTarget。  
> 阶段依据：[独立评审 #91](https://github.com/odango-chan/ca-agent-next/issues/91#issuecomment-7209340753)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。  
> 工作项：[阶段工作项 #95](https://github.com/odango-chan/ca-agent-next/issues/95)。[本轮固定源静态核验报告](../issue-95-fixed-source-handoff/SR-030.md)；历史首批证据见 [Issue #95 评论](https://github.com/odango-chan/ca-agent-next/issues/95#issuecomment-7210746570)。
> 创建日期：2026-11-26
> 修订日期：2026-11-27
> 上游需求：[IR-006](../IR/IR%20总登记册.md#ir-006)；关联需求：[IR-008](../IR/IR%20总登记册.md#ir-008)、[IR-003](../IR/IR%20总登记册.md#ir-003)
> 功能：F09.06 — Host Context Interface Package Publisher
> 目标仓：odango-chan/ca-agent-demo
> 中央设计：F09、F08、EC02 Compiler、CA-SL 1.6.0 完整语言规范、SR-013、SR-016、SR-029
> 设计依据：[F09 技能工作台与 AI 编写](../设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md) v0.3.16 §5～9；[F08 技能编译与发布](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md) v0.3.16；[EC02 Compiler](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.13 §10～11；[CA-SL 1.6.0 完整语言规范](../规范/CA-SL%201.6.0完整语言规范.md) v0.2.10 §5.2、§14～16；[SR-013](SR-013-Compiler已检查when与发布产物.md) v0.2.23 §5～6
> 设计 Issue：[ca-agent-next #40](https://github.com/odango-chan/ca-agent-next/issues/40)
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：Host Trust / Admission、运行期 Context 实例、Capability / Callable、生产级资格、签名、额外摘要、Trust Registry、Agent 内置 Compiler
> 版本边界：SR-024 VERIFIED 仅覆盖旧 Compiler v2.1.0 Development v1alpha1 / CA-SL v1alpha5 Package；本 SR 是新 1.6.0 Publisher，不继承旧格式或旧验收结果

## 1. 目标与责任

**第三轮独立模型评审记录**：[GitHub Review #6082541121](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6082541121)，固定 Head `3d5f17b7f921788d5d38378edb2a14165ea0e03e` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`；`APPROVE_FOR_READY` 仅限 Schema-only 设计及 AC-030-01 固定源审计，不代表新版 Publisher 已实现或发布。

将 ca-agent-demo 中 Host-owned 的静态 Subject Context Schema，按 CA-SL 1.6.0 / Compiler 新 Interface Package 契约重新发布为 **Schema-only Package**，供 Skill Contract.contexts 的 Host Context Schema 依赖闭包使用；Contract.requestSchema 始终指向 Skill 自有 Request Schema，不引用本 Host Context Package。

本 SR 只发布 Schema，不发布 Capability、Callable、Tool、Observation、Context 实例、Runtime identity 或 Admission Grant。新 Package 必须允许 0 Capability exports / 0 Callable exports；不得为了迁就旧 v1alpha1 Package 结构虚构 Tool / Callable。

SR-024 的源码和实现仍是历史审计来源。它已 VERIFIED 的 AC 只证明旧 Development Publisher 的输入、ZIP 和 v1alpha5 package.json；不证明 1.6.0 Package Schema、languageTarget、Compiler Link 或 Studio 消费。

## 2. 固定源码与语义身份

来源固定为 SR-024 已验证的 Host Context 原始 Schema：

| 项目 | 固定值 |
|---|---|
| Repository | odango-chan/ca-agent-demo |
| Source Revision | 57e277ff9094dad93543df46910a12a1dbbaf560 |
| Source path | tests/fixtures/compiler/mas-v1alpha5-scheme-c/trusted/snapshots/ca-context/subject.schema.json |
| Git blob | 4faee66642b8bc5eb2e45c131be4688b982037d8 |
| Schema $id | urn:connectionagent:ca:context:subject:v1 |
| Package ID | urn:connectionagent:ca:host-context |
| Publisher | urn:connectionagent:owner:ca-context |

Publisher 必须从固定 Revision 读取原始 Schema 字节并核对 Git blob；不得从 Studio 工作区、编译后 Artifact、当前浮动 main 或其他导出副本重新生成。Subject Schema 的 $id 版本 v1 是 Schema 内容身份，不是 CA-SL 语言版本；内容未改变时保持不变。

## 3. CA-SL 1.6.0 Package 合同

1. 唯一目标语言为 CA-SL 1.6.0；languageTarget 建议值为 connectionagent.io/v1.6.0，由 ca-skills / Compiler 在正式 Schema / Golden 中共同确认。不得使用 connectionagent.io/v1alpha5。
2. Package ID 与 Publisher 沿用上述稳定逻辑身份；新 Package API 必须采用 Compiler 1.6.0 正式 Schema，不得使用旧 connectionagent.io/interface-package/v1alpha1 或 Development v1alpha1 DTO。
3. Package version 必须使用一个新的 SemVer 版本；旧 1.0.0 是历史 Development Package 版本，不得复用为新发布版本。建议候选 2.0.0，最终由 Publisher 在实施 Issue / 正式 Package Schema 中冻结。
4. Package 只包含根 Manifest 与原始 subject.schema.json；仅发布一个 Schema export，ID 精确等于源 $id，路径指向原始文件；dependencies 为空。
5. Capability exports 必须为空；Callable exports 必须为空；ToolCatalog / Evidence / Runtime Bindings 不属于本 Package。
6. 新 Package Schema 必须明确允许 Schema-only Package；若 Compiler 1.6.0 Package Schema 不允许空 Capability / Callable exports，则该 Schema 与 CA-SL 1.6.0 Context Schema 设计冲突，必须先修订中央契约，Publisher 不得制造合成 Callable 绕过。
7. Package 的 Manifest 只含 1.6.0 Package Schema 明确规定的字段。sourceRevision、Git blob、sourceStatus、Studio upload metadata 不得添加为自定义 Package 字段。
8. 不额外增加 package-level digest、签名、Trust Registry 或 Admission。若新 Package Schema 自身要求必要的逐文件字段，严格按该 Schema 实现；不得从旧 v1alpha1 Schema 推断新字段。
9. 新 Compiler 必须能把此 Package 作为 Contract.contexts 的纯 Schema 依赖加入 closure，并在没有任何 Capability roots 时正确处理；此项由 SR-013 AC-013-06 与本 SR AC-030-03 联合验收。

## 4. Studio Project Lock 的来源边界

- Package Manifest 记录 Package identity、Publisher、SemVer、languageTarget、Schema exports 和文件列表；不记录源码仓 Revision、Git blob、Studio 上传状态或 sourceStatus。
- Studio Project Lock / Import Provenance 记录恢复项目所需的导入来源和已安装快照，包括 source type、upload metadata（若为 ZIP 上传）、Package ID / version / publisher、必要的来源状态及已安装源快照引用。
- 固定 Git Revision / blob 作为 Publisher 输入和 CI 证据保存在本 SR / 实施记录；Studio Lock 不要求重复保存 Git blob。若未来 Lock 需要更精确来源字段，由 SR-016 明确字段与 reload 行为，不得扩展 Package Manifest。
- sourceStatus=DEVELOPMENT_FIXTURE 若用于区分本 Demo Host Context 来源，只能位于 Studio Project Lock，不得写入 1.6.0 Package。
- SR-016 AC-016-07 / AC-016-10 负责 Studio 导入、Lock 持久化、reload 和 Package Explorer 消费；SR-030 不把消费端 PASS 冒充 Publisher PASS。

## 5. 独立模块验收

| AC | 验收内容 | 预期 |
|---|---|---|
| AC-030-01 | 固定源 Revision、路径、Git blob 与原始字节 | 精确匹配 SR-024 已验证来源；源文件缺失、blob 变化或从非固定 Revision 读取均拒绝 |
| AC-030-02 | 新 Package identity 与 1.6.0 Language Target | Package ID / Publisher 稳定；languageTarget 使用正式批准值；新 SemVer 与旧 1.0.0 区分；Manifest 通过 Compiler 1.6.0 正式 Schema |
| AC-030-03 | Schema-only Package | 恰好一个 Schema export；0 Capability / 0 Callable；无 ToolCatalog、Evidence 或 Runtime Binding；可作为 Contract.contexts 的 Context Schema closure root；不得替代 Skill 自有 requestSchema |
| AC-030-04 | 原始字节与确定性发布 | subject.schema.json 原始字节不变；ZIP entries 按规范化相对路径排序；DOS 时间戳固定为 1980-01-01 00:00:00，不使用构建时钟；压缩方法/级别固定，清除 ZIP comment/extra fields 并归一外部属性；Manifest 按正式 Package 契约确定性序列化；同一固定输入在两个全新输出目录构建的 ZIP 必须逐字节相同；不得增加自定义来源字段 |
| AC-030-05 | 负例与旧版拒绝 | 旧 v1alpha5 / Development v1alpha1 Package、旧 1.0.0 manifest、错误 languageTarget、额外 Callable、重复 Schema、未知文件、Schema ID 不匹配均 fail-closed；不转换、不 fallback |
| AC-030-06 | Provenance 分层 | sourceRevision / Git blob 仅在 Publisher 证据；sourceStatus / upload metadata 仅在 Studio Lock；Package Manifest 不接收这些字段 |
| AC-030-07 | 非目标机制约束 | 不增加包级 hash、签名、Trust Registry、Admission 或运行期 Context；只实现新 Package Schema 要求的必要字段 |

### AC-030-04 确定性发布的可验收细则

1. Publisher 必须从固定 Revision/path 读取原始 Schema 字节；ZIP 内该文件解压后的字节与源文件逐字节相同。
2. ZIP entry 使用稳定的规范化相对路径排序；不允许绝对路径、父目录穿越、重复 entry、隐藏临时文件或依赖文件系统枚举顺序。
3. ZIP 元数据固定：DOS 时间戳统一为 1980-01-01 00:00:00；压缩方法/级别固定；ZIP comment 与 extra fields 清空；外部文件属性按统一规则归一，不携带构建机差异。
4. Manifest 必须通过 Compiler Owner 正式发布的 1.6.0 Package Schema；序列化字节必须确定，但具体字段与序列化规则只能来自正式契约，未发布时保持 BLOCKED，不由 Publisher 自行扩字段。
5. 在两个独立空输出目录使用相同固定源和正式工具链各构建一次；比较完整 ZIP 字节（`cmp`）并计算 SHA-256，必须完全一致；同时比较解包后的 entry 集合和每个文件的字节。
6. 不增加 package-level hash、签名、Trust Registry 或 Admission；若正式 Package Schema 要求必要字段，严格按该 Schema 实现。

### 5.1 验收证据

每个 AC 记录源 Revision、Publisher 实施 SHA、命令、测试数、预期 / 实测、输出 ZIP 路径、Manifest / Schema 校验结果和日志位置。未实际运行的命令必须记 NOT_RUN；不得以 SR-024 的历史测试数或 Review COMMENTED 作为本 SR 证据。

## 6. 依赖与阶段门槛

**设计依赖：**
- CA-SL 1.6.0 完整语言规范 v0.1.2 §5.2、§14～16；F08 v0.3.33；EC02 v0.2.22 §10～11；SR-013 v0.2.42 §8（AC-013-06）明确 Schema-only Package / Context Schema closure 与零 Capability roots 的处理。
- SR-029 / CA-SL 1.6.0 规范明确 Contract.contexts 引用 Host Context Schema，requestSchema 则是 Skill 自有请求 Schema。
- F09 v0.3.41 §5～9 / SR-016 明确 Package Manifest 与 Project Lock provenance 的边界。

**实施依赖：**
- 固定 Compiler Owner 正式公布的 1.6.0 Package Schema、BuildRequest / DependencyInspection 与 Schema-only Link 规则的版本、SHA、Golden 和来源。机器契约可独立于 Compiler 二进制发行；契约尚未公布时，不得生成候选。
- 按正式契约从固定源生成真实 Publisher 候选，记录生产者 SHA、命令、样本与输出。先验 AC-030-03 的包结构，再将同一份候选交给 AC-013-06 检查 Context Schema closure 和零 Capability roots。候选生成不等待 AC-013-05；Compiler Release、Publisher 正式发布和 Studio 导入分别记录。
- ca-skills 1.6.0 languageTarget / Schema / Golden 发布；
- ca-agent-demo 新实施 Issue 在本设计独立评审通过后创建，并固定设计 SHA。

在上述机器契约未发布前，SR-030 可进行设计评审，但实现状态 BLOCKED / NOT_STARTED，所有产品 AC NOT_RUN。不得向 DeepSeek Harness 提供猜测 Package 字段的实施提示词。

## 7. 本轮固定源静态核验（Issue #95）

[完整报告](../issue-95-fixed-source-handoff/SR-030.md)独立通过 contents API 和 Git blob API 读取 `57e277ff9094dad93543df46910a12a1dbbaf560` 的 `subject.schema.json`。两次均为 274 字节，`SequenceEqual=True`，SHA-256 均为 `1147f48e2a45405c07d32b8a09f79f151c292cd3711b1fd97c2fd1a3e5485675`，`$id=urn:connectionagent:ca:context:subject:v1`，blob 为 `4faee66642b8bc5eb2e45c131be4688b982037d8`。

- AC-030-01：PASS（固定源与原始字节）。
- AC-030-02/03/05：BLOCKED，等待正式机器契约和实际候选；AC-030-04：NOT_RUN，未生成 ZIP。
- AC-030-06/07：PASS（设计约束静态对照）；Publisher 证据与 Studio Lock provenance 分层，未引入额外包级 hash、签名、Trust Registry、Admission 或运行期 Context。

整项 DRAFT；未生成 Publisher、未调用 Compiler Link、未执行 Studio reload 或产品验收。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | GPT-6（ChatGPT） | 全文 | 新增 Host Context CA-SL 1.6.0 Schema-only Package Publisher 设计，区分 SR-024 历史 VERIFIED 与新版发布门槛，定义 0/0 Capability/Callable、源码 pin、Lock provenance 和独立 AC | 发现 F09 / SR-016 仍把旧 Development Publisher 当作新版依赖，且 Compiler Schema-only Package 能力未定义 | Issue #12/#40；IR-006/008；SR-013/016/024/029 |
| 2026-11-26 | 0.1.1 | GPT-6（ChatGPT） | §1、§3、AC-030-03、依赖与修订记录 | 明确 Host Context Schema-only Package 只能由 Contract.contexts 引用；requestSchema 始终是 Skill 自有 Schema 根 | 避免将 Host Context Package 错误当成 Skill Request Schema，保持 CA-SL 1.6.0 §4 的作者语义一致 | Issue #12/#40；CA-SL 1.6.0；SR-013 AC-013-06；SR-029；PR #46 |
| 2026-11-26 | 0.1.2 | Codex / GPT-6 | §6，修订记录 | 区分机器 Schema 发布、真实 Publisher 候选、Compiler 联验和二进制发行 | 消除相互等待 | Issue #12/#40，PR #46，SR-013/030 |
| 2026-11-27 | 0.1.3 | Codex / GPT-6 | 评审入口 | 回填独立评审批准评议的具体范围 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.1.4 | Codex / GPT-6 | 评审状态 | 登记第二轮限定范围及外部依赖 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.1.5 | GPT-6（ChatGPT） | 文档头、§1、§6、修订记录 | 补齐 F09/F08/EC02/CA-SL 1.6.0/SR-013 的固定版本与章节；修复修订账本排序 | 处理独立模型 Review #6082541121 的 R3-SR030-01 与 R3-LEDGER-01，避免 Schema-only Publisher 的核心设计依据不可定位 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.1.6 | GPT-6（ChatGPT） | 文档头、§1、§6、修订记录 | 将第二轮不可访问的评审登记替换为正式 Review #6082541121 的限定结论；标记 SR-030 P2 依据修订位于后续 Head | 避免将固定旧 Head 的设计认可外推到新 Head 或 Publisher 实施 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.1.7 | Codex / GPT-6 | 文档头 | 登记阶段 READY（中央只读核验）及 AC 范围与工作项 #95 | 按单项独立评审推进 | Issue #12、#91；PR #46 |
| 2026-11-27 | 0.1.8 | kimi-k3.1-pro | §7、文档头 | 独立复验 Subject Schema 274 字节/blob/SHA-256/$id，核对 Provenance 与 Demo 排除；01/06/07 静态 PASS，02～05 原状态不变 | 证明固定输入而不冒充 Publisher 或 Compiler 产品验收 | Issue #95；SR-030 |
| 2026-11-27 | 0.1.9 | GPT-6.2（ChatGPT） | §5、§6、修订记录 | 统一 SR-013 版本引用；细化 AC-030-04 ZIP 元数据归一、entry 顺序、双构建逐字节比较与正式 Schema 验证 | 处理既有评审 P2；不推测未发布的 Package Schema 字段 | Issue #95；#106；Review #91 |
| 2026-11-27 | 0.1.10 | GPT-6.2（ChatGPT） | §6、修订记录 | 将 SR-013 互引从错误的 §5～6 更正为实际定义 Schema-only / 零 Capability roots 的 §8（AC-013-06） | 确保跨 SR 规则引用可定位且与实际章节一致 | Issue #106；Review #91 |
| 2026-11-28 | 0.1.11 | GPT-6.2（ChatGPT） | 文档头、§1、§6、修订记录 | 将活动依赖入口同步到 F09 v0.3.41、F08 v0.3.33、EC02 v0.2.22、CA-SL 1.6.0 v0.2.10 与 SR-013 v0.2.42 §8 | 避免 Host Context Publisher 继续引用旧版本或错误章节，保持 AC-013-06 / AC-030-03 联合验收入口一致 | Issue #95/#106；PR #107/#115 |
