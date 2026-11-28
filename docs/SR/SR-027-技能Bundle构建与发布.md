# SR-027：技能Bundle构建与发布

> 文档类型：软件需求（SR）  
> SR 版本：0.3.0\
> 状态：整项 DRAFT；中央作者源与 Bundle 构建机器契约已固定，DESIGN_REVIEW_REQUESTED；产品 AC 仍 NOT_RUN，ca-skills 1.6.0 作者 Schema/Golden、Compiler 3.0.0 Release 与五根作者源尚未发布。
> 下一步：独立评审本轮五根作者源、Compiler pin、release/bundle-inputs.yaml、Bundle 目录与原子 ZIP 契约；达到 SR-027 READY 后再创建 ca-skills 实施 Issue。
> 阶段依据：[独立评审 #89](https://github.com/odango-chan/ca-agent-next/issues/89#issuecomment-7209388846)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。
> 创建日期：2026-11-26  
> 修订日期：2026-11-27\
> 上游需求：IR-006  
> 设计依据：F08 v0.3.19 §4、§6；CA-SL 1.6.0 目标（Issue #40 / SR-029）。\
> 关联 Issue：ca-agent-next#12（设计）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §4；本批限外部构建与发布。

## 0. 本轮设计评审入口（2026-11-26）

本 SR 已提交 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计审查；**主状态 `DRAFT` 与设计 `REVIEW_REQUESTED` 独立，实施 READY/产品 PASS 均未获得**。新语言架构见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 和 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮审查重点：**核查 ca-skills CI 基于正式 1.6.0 作者源、新 Compiler Build/Verify、Echo/MAS Bundle 原生发布与失败原子性。
- **未发布/未证据项：**旧 compile_mas_v1alpha5.py、测试/Golden 仅留档；1.6.0 语言、Binding、Compiler 发行与新 Bundle 未发布，AC-027 NOT_RUN。
- **统一目标：**CA-SL **1.6.0 ONLY**；Skill-facing 只有 Capability ID，公开 Capability↔Callable 严格双向一对一；旧语言、Compiler DTO、Artifact、Bundle、别名、fallback 与迁移兼容均禁止。旧源 Schema/fixture/发布身份只用于只读历史审计；新机器契约由发布者冻结，不得自行猜测。
- **评审退出：**逐项核查范围/非目标、外部契约、失败语义和 AC；外部新合同未发布为 `BLOCKED`、产品未运行为 `NOT_RUN`。在独立评审通过前不得向 Harness 交付实施提示词。

## 1. 目标与前置

目标仓 ca-skills，功能 F08 / EC01，中央依据为 [F08 发布设计 §4](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md#4-ca-skills-ci-编译与-bundle-组装)。基线 `780497a2918ad3e7bdff554ab64b0ba627e867e0`。SR-023 的历史 v1alpha5 作者规范保留追溯；**新 Bundle 面向 CA-SL 1.6.0**，SR-029 + ca-skills 发布 Capability-first 作者规范，SR-013 / Compiler #62 联合交付 when + 唯一 Capability Binding 的新版 Compiler Release（旧 #61 仅为 v1alpha5 历史范围），SR-004 与 SR-008 消费发布物。固定作者 SHA、Compiler 发布 tag 与可执行文件、适用的 Runtime Artifact API。某一 Skill 需要下一版 Artifact 时单列等待。

## 2. 在源仓交付

历史 `scripts/compile_mas_v1alpha5.py`、`tests/test_compile_mas_v1alpha5.py` 及原有 CI **仅作为留档审计线索，不作为 1.6.0 新实现或验收入口**。新 Bundle 构建与测试必须基于 ca-skills 正式发布的 **1.6.0 作者语法**、SR-029 的 Capability→Callable Binding 和 Compiler 新版契约，从头定义单版本流程；不保留调用旧编译脚本的兼容分支。为本批指定的 Echo 作者源、MAS 作者源分别建立构建输入清单。Echo 在该基线缺失，准备 SR-008 所用的指导包和带 Assurance 的 Echo，登记路径、Capability、请求/响应样例及预期。MAS 业务样例选 `examples/skills/{establish,modify,release}-pdu-session-mas`，逐个给出依赖和 Verify 日志。**这些当前路径对应历史 v1alpha5 作者源，只作为业务语义与迁写参考；实际进入 1.6.0 Build 的必须是作者按 SR-029 人工重新编写、固定 revision 并经 1.6.0 Compiler Check/Build/Verify 的新源，禁止直接编译当前历史文件。**

CI 对同一批次一次解析并固定 Compiler 发行版，逐包构建与验证成功后组装发布目录。指导包只含作者入口及声明的资源；确定性包随附已验证的 Runtime Artifact。输出记录作者 revision、Compiler 实际版本、API、资产路径、各包结果。发布前在临时目录验证，失败不上传部分批次；由授权的发布步骤消费同一份候选。

### 2.1 首批构建矩阵

作者根相对 ca-skills 的 `examples/skills/`。三项 MAS 原始输入固定为 `780497a2918ad3e7bdff554ab64b0ba627e867e0`，Echo 两个目录为本 SR 的新增目标。正式批次只取一个含五份 1.6.0 作者输入的 **同一提交**。CI 从 checkout 的 `git rev-parse HEAD` 记录实际作者 revision，逐根核对，无权用此历史 SHA 代替新作者 SHA。

| 作者目录 / 输出 ID | 输入和验收 |
|---|---|
| `echo-guide` | 仅 SKILL.md，无 Capability、外部依赖及 Artifact。同一 echo.request 文本 hello 经 Delivery 回传。 |
| `echo-assured` | 示例设计要求一个 Echo READ 及唯一公开绑定，输入/输出均为含 text 的闭合对象。SR-003 的 Plugin 使用 `urn:example:echo:interface`、实际 Callable 为 `echo.read`；发布包须显式导出示例 Capability（建议 `echo.read`，同名也必须有正式 Binding），不得从 Callable 名反推。 |
| `establish-pdu-session-mas` | Owner + Host Context Schema-only。沿固定源的 13 项 grants，将事件项替换为 `mas.se.establishment-event.record`；Grant 与实际 Procedure、Owner 输出逐项核对。 |
| `modify-pdu-session-mas` | Owner + Host Context Schema-only，`mas.ssm.n1.modify.parse`、`mas.upn.up.qos.delta`；QoS 来源保持可追溯。 |
| `release-pdu-session-mas` | Owner + Host Context Schema-only。沿固定源的 8 项 grants，把事件项替换为 `mas.se.release-event-marker.write`，两路 confirm 保持独立。 |

每个根输出至 `published-skills/<skill-id>/`，根名等于 SKILL.md 的 name。原样包含一份 SKILL.md、按相对路径列明的资源；四个 Assurance 根另含同一次 Build/Verify 给出的完整 Runtime Artifact 文件集合，保留 Compiler 的相对布局，拒绝路径碰撞、遗漏、额外 Artifact 或作者 assurance/ 源混入。记录每包源路径、同批 revision、依赖版本、Capability 清单、实际输出相对路径和 Verify 日志。候选只上传一次；五包中任一失败则发布数为零。

**目标仓测试入口（待实现）**为 `python -m unittest discover -s tests -p test_bundle_160.py -v`。最少 10 个必需用例：五包各一项成功、旧 languageTarget、缺依赖、歧义 Binding、缺 Artifact 文件、Verify 失败时全批零上传。必需失败/跳过均为零，记录实际发现数。正式 Compiler 可执行、Check/Build/Verify 的完整 argv 与 tag、Echo Interface 导出和新作者 SHA 由相应生产者登记；缺任一项则停止 AC-027-01/02，不能把本文候选名称、历史 CLI 或 mock 输出作为发布证据。

## 2.2 中央固定的作者源与 Bundle 构建契约

**语言与编译器版本：**唯一 languageTarget=connectionagent.io/v1.6.0；Compiler 目标 Release=3.0.0；BuildRequest=connectionagent.io/compiler-build-request/2；DependencyInspection=connectionagent.io/compiler-dependency-inspection/2；BuildResult=connectionagent.io/compiler-build-result/2；Runtime Artifact=connectionagent.io/compiler-artifact/2。这些是 Next 中央设计值，尚未发布。release/bundle-inputs.yaml 必须固定上述版本、Compiler commit SHA / Release asset，以及 Echo / Owner / Host Context Package 的准确 ID / SemVer；禁止运行时解析浮动 latest。

**作者源与构建矩阵：**五个 Skill 根来自同一个 ca-skills commit。echo-guide 是 SKILL.md-only，不调用 Compiler；其余四个 Assurance 根分别使用同一 Compiler 3.0.0 执行 Check、DependencyInspection、Build、Verify。when 只允许写在 assurance/contract.yaml 顶层，不得写入 SKILL.md Front Matter。assurance/ 源文件不得进入发布包。

**归属边界：**ca-skills 只负责作者源、CI 调度、Bundle 组装和发布；Compiler 负责单个 Assurance Skill 的 Runtime Artifact，不组装 Bundle；Next 负责 Runtime 导入与选择，不调用 Compiler。Echo Interface Package 由 Next / SR-008 产生；MAS Owner Capability 和 Host Context Schema-only Package 分别由 SR-025 / SR-030 产生。SR-026 的协议级 Codec Capability 不替代 MAS Owner 的 mas.ssm.n1.modify.parse / mas.ssm.n1.release.parse。

**单个 Skill 发布目录：**

~~~text
published-skills/<skill-id>/
  SKILL.md
  resources/...
  runtime-artifact/                 # 仅 Assurance Skill
    manifest.json
    skills/<skill-id>/compiled/...
~~~

SKILL.md-only 根不含 runtime-artifact/。Assurance 根必须包含单 Skill 的完整 Compiler Artifact 根，保留 manifest.json 与所有相对路径；不得缺 .pb、Schema 闭包或 Binding 文件，不得混入作者源或 Compiler 二进制。

**唯一发布资产：**生成 skill-bundle-1.6.0.zip，顶层只含 published-skills/ 和五个 Skill 根。外层不另造 Bundle Manifest；Compiler Artifact Manifest 仍由 Compiler 拥有。bundle-build-report.json 作为 CI 证据附件，记录源 commit、Compiler 版本/commit/API、依赖 Package ID/版本、五个根、四个 Artifact、文件列表和 Verify 结果，不作为 Agent 导入输入。

ZIP 复用仓库既有确定性归档规则：路径排序、统一 /、固定时间戳、拒绝 symlink 和非普通文件。同一固定输入重复构建必须逐字节一致。五根源检查全部通过、四个 Artifact 全部 Verify、依赖闭包唯一、目录无缺失/额外/碰撞后才允许进入单一发布步骤；任一失败，本批发布资产为零。发布授权是最终 Release 门槛，不是设计或本地 Build 的前置。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-027-01 | ca-skills 仓根使用新建的 **1.6.0 专用测试入口**（§2.1 固定命令、文件与必需用例），检验新版 Compiler Check/Build/Verify、Bundle 成功与错误拒绝；可继续运行文档检查，但 **v1alpha5 测试不得作为本 AC 的 PASS 证据**；记录命令、受测 SHA、发现数和日志 |
| AC-027-02 | CI 在干净 checkout 生成候选。逐项查 SKILL.md、所声明的资源及可选 Assurance 对应产物；损坏 Artifact 使当批发布数为零。Development Artifact 不进入 Runtime Bundle |
| AC-027-03 | 发布后从正式资产入口取得 AC-027-02 的同一批内容，在 Next 执行 SR-004 导入与 SR-008 Echo；原始作者 checkout 和 Compiler 从 Host 运行环境移除后依然可运行。分别记录构建、发布及消费状态 |
| AC-027-05 | Source Bundle 原件 byte-compare、OAS3 引用闭包、Compiler Build/Verify snapshot、Request/Codec Result 阶段可用性及版本隔离均具备正反证据；Source Bundle-only PASS 不升级 Codec/MAS Bundle/系统 E2E | NOT_RUN / BLOCKED |

## 4. 状态与非目标

中央设计 Issue #12；ca-skills 实施 Issue、实施 PR、构建证据和正式发行资产尚未登记。READY 前固定首批作者源、Bundle 的具体文件清单、可用 Compiler 版本与匹配 Verify 命令；候选构建和正式发布分别登记。AC-027-01/02 通过、资产与 Verify 日志可追溯且取得发布授权后，由发布步骤上传同一批次。AC-027-03 是发布后的消费联验，不作为上传前置；消费端尚未就绪时只暂停该 AC，整项 SR 仍待验证。状态 DRAFT，测试 NOT_RUN。Next 不编译，Compiler 不负责组装 Bundle。无替代 SR。

## 5. 当前外部输入与发布证据核对（2026-11-26）

| 输入 | 当前可核对事实 | 对本 SR 的结论 |
|---|---|---|
| CA-SL v1alpha5 | ca-skills PR #88 MERGED；normative SHA `18d8184367982ccbc835756136c4a53f9096c3a0`；PR #89 将该 SHA 固定在 release record | 仅覆盖历史语言；新版作者 Schema 和机器标识仍待 ca-skills 正式发布 |
| Compiler v2.1.0 | [正式 Release](https://github.com/odango-chan/ca-skill-compiler/releases/tag/v2.1.0)；冻结 Artifact v1alpha5 和 Development Artifact v1alpha1；旧 Artifact 字节/语义不变 | 不能满足 F08 新 Runtime Artifact API 的 Request Schema/when 输出 |
| Compiler when Artifact | [Compiler Issue #62](https://github.com/odango-chan/ca-skill-compiler/issues/62) OPEN（CA-SL 1.6.0-only）；Next 已固定 Compiler 3.0.0 与 BuildRequest / DependencyInspection / BuildResult / Artifact /2；旧 [Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) 仅为 v1alpha5 历史范围 | 目标 API/Manifest 已由中央设计固定，但正式 Schema、Golden、Release 与产品验收仍 NOT_RUN；不得将设计值误报为已发布 |
| ca-skills 作者源 | main `780497a2918ad3e7bdff554ab64b0ba627e867e0` 含 v1alpha5 MAS 作者源；`scripts/compile_mas_v1alpha5.py` 只对单 Skill 做 Check/Inspect/可选 Build | 现有脚本不是 Bundle assembler，也不证明正式 Bundle 已发布 |
| ca-skills Release | 当前 Release 列表只有历史 v0.1.0；未发现与 **CA-SL 1.6.0** Runtime Artifact API 匹配的 Published Skill Bundle | 无可供 SR-004 使用的正式 Assurance 正例 |
| ca-skills 仓库布局 | 当前 main 未发现 `published-skills/` / 新 Runtime Artifact Bundle 发布目录 | §2.1 固定候选根与关联规则；实际 Compiler Manifest 文件及生成结果随同版发行证据登记 |

**阶段结论：** 本 SR 仍为 DRAFT / DESIGN_REVIEW_REQUESTED。Next 已固定 CA-SL 1.6.0 languageTarget、Compiler 3.0.0、BuildRequest / DependencyInspection / BuildResult / Artifact /2 与五根 Bundle 输入锁定规则；ca-skills 的正式 1.6.0 Schema/Golden、Compiler Release、五根新作者源和 Bundle 发布资产尚未存在，产品 AC 保持 NOT_RUN。不得将设计目标误报为产品发布，也不得把旧 v1alpha5 作者源/编译目录作为 AC-027-01/02 正例。SR-004 的 SKILL.md-only 路径可独立验证，不提升 SR-027 或 Assurance Bundle 状态。

### 5.1 五包发布的生产者交接表（尚未交付）

| 生产者 | 唯一正式输入 | 可解除的阶段门槛 |
|---|---|---|
| ca-skills 语言与 Skill 作者 | 1.6.0 作者 Schema / Golden / languageTarget；包含 echo-guide、echo-assured 与三份 MAS 新作者源的**同一固定提交** | AC-027-01 真实作者正例 |
| Echo Interface Package Owner | 正式 Echo READ Capability/唯一 Callable/Schema、Package ID/SemVer/导出与源 SHA | echo-assured 的唯一 Binding 正例 |
| Compiler / SR-013 Owner | 正式 1.6.0 Compiler tag、可执行文件、完整 Check/Build/Verify argv、Runtime Artifact Schema/Manifest、Package Schema 与 Golden | AC-027-01/02 真实 Build/Verify、缺件和失败原子性 |
| ca-skills 发布者 | 五包来源清单、各包准确 Artifact 相对文件列表、发布资产及授权、下载 URL 与 Verify 证据 | 先 AC-027-01/02 后授权上传；AC-027-03 是发布后的消费者联验 |

缺任何正式输入，禁止把候选目录、旧 v1alpha5 脚本、mock Compiler 或历史 1.0.0 包算作新版本发布。设计矩阵可以独立审查，但 SR-027 完整 READY 仍受外部生产者交付阻塞；不得传递性阻塞 SR-004 的独立 SKILL.md-only 子范围。

## 6. OpenAMSM OpenAPI Source Bundle 与 MAS 1.6.0 Bundle 的严格分层（IR-009）

ca-skills / SR-031 原样发布 OpenAMSM 实际支持版本的 OpenAPI 3.0 Source Bundle；原始 YAML bytes、相对路径和 `$ref` 不变。Source Bundle 是不可变标准来源快照，不是 Schema-only Interface Package，不导出 Capability / Callable，也不需要 Adapter。

- 新 CA-SL 1.6.0 Skill 的 Request 根始终自有、遵循 G.4，并且只描述 T1 已可用的 SBI / 归一化字段。若字段类型需要复用原版 3GPP 类型，Skill 显式声明并 pin Source Bundle dependency，Compiler 直接解析精确 `components/schemas`；外部目标使用 OAS 3.0 dialect，不做投影。
- Bundle / Compiler Lock 必须固定 OpenAMSM source commit、Source Bundle identity、每个文件的原始相对路径 / Git blob ID / byte length、选定 operation surface、完整可达 `$ref` 闭包和标准版本取证；Publisher 直接 byte-compare 原件，不新增 per-file SHA-256 / digest 或 package hash。Build / Verify 不得动态下载 latest 或跨 commit 混源。
- 当前 `PostSmContexts.requestBody` → `jsonData` → `SmContextCreateData` 的选定闭包是四份原版 YAML / 102 个 Schema Component；不要求复制 472 份 standard YAML，也不要求解析根文件中未选定 operation 的 refs。
- Provider Codec Output Schema 与 OpenAPI Source Bundle 是不同依赖。NAS / NGAP 结果由 ca-client-tools SR-026 发布，必须固定 OpenAMSM 协议源版本和已资格化 Profile；0xD1 首批不能证明 Create / Modify / N2 支持。
- Host Context SR-030 的 0/0 Schema-only Package 仍只经 `Contract.contexts` 使用；不得把 Source Bundle 当 Host Context 或 Capability Package。
- 无 3GPP 依赖的 Echo 不强制下载 Source Bundle / Codec。Publisher CI 验证真实 Link / Build / Verify 与完整快照；缺正式 OAS3 Resolver / Source Lock / Provider Output Schema 时相应子项 BLOCKED / NOT_RUN。
- 新增 **AC-027-05**：Source Bundle 原件 byte-compare、OAS3 引用闭包、Compiler Build / Verify snapshot、Request / Codec Result 阶段可用性及版本隔离均有正反向证据；Source Bundle-only PASS 不能升级为 Codec / MAS Bundle / 系统 E2E PASS。原 AC-027-01～04 不因新增跨包类型要求扩大范围。

[权威公共设计](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。

## 7. 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | Codex / GPT-6 | 见本行变更 | 首次登记两端交付、独立复验与就绪条件 | 未单独记录（历史原因未提供） | Issue #12 |
| 2026-11-26 | 0.1.1 | Codex / GPT-6 | 见本行变更 | 补齐正式文档的评审范围与非目标；列明依赖设计版本；同步设计依据到本次复审的修订版本 | 未单独记录（历史原因未提供） | Issue #12 |
| 2026-11-26 | 0.1.2 | GPT-6.2（ChatGPT） | 文档头、§4～6、修订记录 | 记录 CA-SL v1alpha5 固定源、Compiler v2.1.0 冻结 Artifact、Issue #61 未完成及 ca-skills 当前无正式 Bundle；防止将规范/Compiler Release/本地 Build 误报为 Published Skill Bundle，并为 SR-004 明确外部依赖 | 未单独记录（历史原因未提供） | Issue #43；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.1.3 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 将 F08 设计依据更新至 v0.3.8，保持 SR-027 与发布端权威设计版本一致 | 未单独记录（历史原因未提供） | Issue #43；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.1.4 | GPT-6.2（ChatGPT） | 文档头、§1、§5、修订记录 | 将后续 Skill Bundle 生产目标更新为 CA-SL 1.6.0，增加 SR-029 Capability Binding 与 Compiler #61 联合 Release 门槛；避免继续发布 v1alpha6 候选或旧 v1alpha5 作者源作为最新运行包 | 未单独记录（历史原因未提供） | Issue #40/#43；SR-029；SR-013；SR-027 |
| 2026-11-26 | 0.1.5 | GPT-6.2（ChatGPT） | §2～3、修订记录 | 将旧 v1alpha5 构建脚本与测试从新版验收入口移除，仅保留历史审计；1.6.0 Bundle 必须原生编译/验证；严格无兼容、无旧构建管线的 1.6.0 单版本发布 | 未单独记录（历史原因未提供） | Issue #40/#43；SR-029；SR-027 |
| 2026-11-26 | 0.1.6 | GPT-6（ChatGPT） | 文档头、设计依据/修订记录 | 对齐最新 1.6.0-only 待评审设计与发布门槛 | 未单独记录（历史原因未提供） | Issue #40/#43；SR-029 |
| 2026-11-26 | 0.1.7 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 提交设计待评审、明确新旧契约/验收隔离并保留 DRAFT 主状态 | 未单独记录（历史原因未提供） | Issue #12；PR #45；SR-029 |
| 2026-11-26 | 0.1.8 | GPT-6（ChatGPT） | 设计依据与新版本路径 | 刷新 1.6.0 正式目标设计引用：v0.3.12→v0.3.13 | 未单独记录（历史原因未提供） | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.1.9 | Codex / GPT-6 | §3～5 | 将构建、授权发布、正式资产消费按顺序取证，消除发布与消费互等并纠正历史语言依赖状态 | 未单独记录（历史原因未提供） | Issue #12/#43，PR #46，SR-004/008/013/027 |
| 2026-11-27 | 0.2.0 | Codex / GPT-6 | §2～5、AC-027-01/02 | 登记同批五个作者根、测试与发行输入缺口 | 未单独记录（历史原因未提供） | Issue #12，PR #46 |
| 2026-11-27 | 0.2.1 | Codex / GPT-6 | 评审状态 | 登记第二轮限定范围及外部依赖 | 未单独记录（历史原因未提供） | Issue #12，PR #46 |
| 2026-11-27 | 0.2.2 | GPT-6（ChatGPT） | §5.1、修订表 | 明确五根作者提交、Echo Interface、Compiler Release/argv 与发行授权的生产者边界，整理历史六列修订记录 | 允许审查固定设计而不臆造缺失发布物或将下游联验误作上传门槛 | Issue #12；PR #46；SR-027 |
| 2026-11-27 | 0.2.3 | GPT-6（ChatGPT） | 修订记录 | 将历史记录统一为七列并保留原始文字及原始关联，修正非规范行的分隔符 | 确保修订表可由文档校验器完整解析；不影响设计语义及 READY 主状态 | Issue #12；PR #46；SR-027 |
| 2026-11-27 | 0.2.4 | Codex / GPT-6 | 文档头 | 登记BLOCKED_EXTERNAL_INPUT及 AC 范围 | 按单项独立评审推进 | Issue #12、#89；PR #46 |
| 2026-11-28 | 0.2.5 | GPT-6（ChatGPT） | 分支整合、设计依据与修订记录 | 合并恢复分支已批准的 F08 v0.3.19 引用与 #46 新版 Bundle 设计；保留 CA-SL 1.6.0-only、未发布 Compiler/Publisher 门槛 | 避免把历史 Bundle 误作新版成品，保持 SR-027 独立 Publisher/验收责任 | Issue #12；#40；#113；PR #45；#46 |
| 2026-11-28 | 0.2.5-integration-fix | GPT-6（ChatGPT） | 文档头与修订记录 | 修正整合期间版本/验收时点一致性，不改变产品状态 | 保持历史证据与新 1.6.0 设计边界 | Issue #12；PR #45；#46 |
| 2026-11-28 | 0.3.0 | GPT-6.2（ChatGPT） | §0、§2.2、§3～6、修订记录 | 固定 CA-SL 1.6.0 languageTarget、Compiler 3.0.0 / API /2、五根作者源、Bundle 输入锁与原子 ZIP 契约 | 把生产端设计从等待外部命名推进为中央可评审的唯一目标，同时保留产品未发布状态 | Issue #113；F08；EC02；SR-013/027/029/030；PR #115 |
