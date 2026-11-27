# SR-027：技能Bundle构建与发布

> 文档类型：软件需求（SR）  
> SR 版本：0.3.0\
> 状态：整项 DRAFT；中央生产端设计已补齐，`DESIGN_REVIEW_REQUESTED`；产品 AC 仍 NOT_RUN。ca-skills 实施 Issue 未创建，须待 SR-027 READY。  
> 下一步：独立评审中央作者输入、Compiler pin、Bundle 目录与原子 ZIP 契约；达到 READY 后再创建 ca-skills 实施 Issue。  
> 阶段依据：[独立评审 #89](https://github.com/odango-chan/ca-agent-next/issues/89#issuecomment-7209388846)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。
> 创建日期：2026-11-26  
> 修订日期：2026-11-27\
> 上游需求：IR-006  
> 设计依据：F08 v0.3.16 §4、§6；CA-SL 1.6.0 目标（Issue #40 / SR-029）。\
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

目标仓：`odango-chan/ca-skills`；中央依据为 F08 §3～§6.1、CA-SL 1.6.0 规范、SR-013、SR-008、SR-029、SR-025、SR-030。ca-skills 负责五个作者根和 Bundle 组装；Compiler 由 SR-013 / `ca-skill-compiler` 负责；Echo Interface Package 由 Next / SR-008 负责。`ca-skill-compiler#61` 是 v1alpha5 历史任务，不是 1.6.0 Compiler 实施入口。

## 2. 在源仓交付

历史 `scripts/compile_mas_v1alpha5.py`、`tests/test_compile_mas_v1alpha5.py` 及原有 CI **仅作为留档审计线索，不作为 1.6.0 新实现或验收入口**。新 Bundle 构建与测试必须基于 ca-skills 正式发布的 **1.6.0 作者语法**、SR-029 的 Capability→Callable Binding 和 Compiler 新版契约，从头定义单版本流程；不保留调用旧编译脚本的兼容分支。为本批指定的 Echo 作者源、MAS 作者源分别建立构建输入清单。Echo 在该基线缺失，准备 SR-008 所用的指导包和带 Assurance 的 Echo，登记路径、Capability、请求/响应样例及预期。MAS 输入选 `examples/skills/{establish,modify,release}-pdu-session-mas`，逐个给出依赖和 Verify 日志。

CI 对同一批次一次解析并固定 Compiler 发行版，逐包构建与验证成功后组装发布目录。指导包只含作者入口及声明的资源；确定性包随附已验证的 Runtime Artifact。输出记录作者 revision、Compiler 实际版本、API、资产路径、各包结果。发布前在临时目录验证，失败不上传部分批次；由授权的发布步骤消费同一份候选。

### 2.1 首批构建矩阵

作者根相对 ca-skills 的 `examples/skills/`。三项 MAS 原始输入固定为 `780497a2918ad3e7bdff554ab64b0ba627e867e0`，Echo 两个目录为本 SR 的新增目标。正式批次只取一个含五份 1.6.0 作者输入的 **同一提交**。CI 从 checkout 的 `git rev-parse HEAD` 记录实际作者 revision，逐根核对，无权用此历史 SHA 代替新作者 SHA。

| 作者目录 / 输出 ID | 输入和验收 |
|---|---|
| `echo-guide` | 仅 SKILL.md，无 Capability、外部依赖及 Artifact。同一 echo.request 文本 hello 经 Delivery 回传。 |
| `echo-assured` | 使用 Capability `example.echo.message.read`；依赖 Next / SR-008 导出的 Interface Package `urn:example:echo:interface@1.0.0`。Callable `echo.read` 只存在于 Interface Package，不进入 Skill 作者源；输入/输出均为含 `text` 的闭合对象。 |
| `establish-pdu-session-mas` | Owner + Host Context Schema-only。沿固定源的 13 项 grants，将事件项替换为 `mas.se.establishment-event.record`；Grant 与实际 Procedure、Owner 输出逐项核对。 |
| `modify-pdu-session-mas` | Owner + Host Context Schema-only，`mas.ssm.n1.modify.parse`、`mas.upn.up.qos.delta`；QoS 来源保持可追溯。 |
| `release-pdu-session-mas` | Owner + Host Context Schema-only。沿固定源的 8 项 grants，把事件项替换为 `mas.se.release-event-marker.write`，两路 confirm 保持独立。 |

每个根输出至 `published-skills/<skill-id>/`，根名等于 SKILL.md 的 name。原样包含一份 SKILL.md、按相对路径列明的资源；四个 Assurance 根另含同一次 Build/Verify 给出的完整 Runtime Artifact 文件集合，保留 Compiler 的相对布局，拒绝路径碰撞、遗漏、额外 Artifact 或作者 assurance/ 源混入。记录每包源路径、同批 revision、依赖版本、Capability 清单、实际输出相对路径和 Verify 日志。候选只上传一次；五包中任一失败则发布数为零。

**目标仓测试入口（待实现）**为 `python -m unittest discover -s tests -p test_bundle_160.py -v`。最少 10 个必需用例：五包各一项成功、旧 languageTarget、缺依赖、歧义 Binding、缺 Artifact 文件、Verify 失败时全批零上传。必需失败/跳过均为零，记录实际发现数。正式 Compiler 可执行、Check/Build/Verify 的完整 argv 与 tag、Echo Interface 导出和新作者 SHA 由相应生产者登记；缺任一项则停止 AC-027-01/02，不能把本文候选名称、历史 CLI 或 mock 输出作为发布证据。
## 2.2 中央固定的作者源与 Bundle 构建契约

**语言与编译器版本：**唯一 languageTarget=`connectionagent.io/v1.6.0`；Compiler 目标 Release=`3.0.0`；BuildRequest=`connectionagent.io/compiler-build-request/2`；DependencyInspection=`connectionagent.io/compiler-dependency-inspection/2`；BuildResult=`connectionagent.io/compiler-build-result/2`；Runtime Artifact=`connectionagent.io/compiler-artifact/2`。这些是 Next 中央设计值，尚未发布。`release/bundle-inputs.yaml` 必须固定上述版本、Compiler commit SHA / Release asset，以及 Echo / Owner / Host Context Package 的准确 ID / SemVer；禁止运行时解析浮动 `latest`。

**作者源与构建矩阵：**五个 Skill 根来自同一个 ca-skills commit。`echo-guide` 是 SKILL.md-only，不调用 Compiler；其余四个 Assurance 根分别使用同一 Compiler 3.0.0 执行 Check、DependencyInspection、Build、Verify。`when` 只允许写在 `assurance/contract.yaml` 顶层，不得写入 SKILL.md Front Matter。`assurance/` 源文件不得进入发布包。

**归属边界：**ca-skills 只负责作者源、CI 调度、Bundle 组装和发布；Compiler 负责单个 Assurance Skill 的 Runtime Artifact，不组装 Bundle；Next 负责 Runtime 导入与选择，不调用 Compiler。Echo Interface Package 由 Next / SR-008 产生；MAS Owner Capability 和 Host Context Schema-only Package 分别由 SR-025 / SR-030 产生。SR-026 的协议级 Codec Capability 不替代 MAS Owner 的 `mas.ssm.n1.modify.parse` / `mas.ssm.n1.release.parse`。

**单个 Skill 发布目录：**

~~~text
published-skills/<skill-id>/
  SKILL.md
  resources/...
  runtime-artifact/                 # 仅 Assurance Skill
    manifest.json
    skills/<skill-id>/compiled/...
~~~

SKILL.md-only 根不含 `runtime-artifact/`。Assurance 根必须包含单 Skill 的完整 Compiler Artifact 根，保留 `manifest.json` 与所有相对路径；不得缺 `.pb`、Schema 闭包或 Binding 文件，不得混入作者源或 Compiler 二进制。

**唯一发布资产：**生成 `skill-bundle-1.6.0.zip`，顶层只含 `published-skills/` 和五个 Skill 根。外层不另造 Bundle Manifest；Compiler Artifact Manifest 仍由 Compiler 拥有。`bundle-build-report.json` 作为 CI 证据附件，记录源 commit、Compiler 版本/commit/API、依赖 Package ID/版本、五个根、四个 Artifact、文件列表和 Verify 结果，不作为 Agent 导入输入。

ZIP 复用仓库既有确定性归档规则：路径排序、统一 `/`、固定时间戳、拒绝 symlink 和非普通文件。同一固定输入重复构建必须逐字节一致。五根源检查全部通过、四个 Artifact 全部 Verify、依赖闭包唯一、目录无缺失/额外/碰撞后才允许进入单一发布步骤；任一失败，本批发布资产为零。发布授权是最终 Release 门槛，不是设计或本地 Build 的前置。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-027-01 | ca-skills 仓根使用新建的 **1.6.0 专用测试入口**（§2.1 固定命令、文件与必需用例），检验新版 Compiler Check/Build/Verify、Bundle 成功与错误拒绝；可继续运行文档检查，但 **v1alpha5 测试不得作为本 AC 的 PASS 证据**；记录命令、受测 SHA、发现数和日志 |
| AC-027-02 | CI 在干净 checkout、单一源 commit 和 `release/bundle-inputs.yaml` 固定 Compiler 输入下生成五根候选；echo-guide 不编译，四个 Assurance 根逐个 Verify；组装 `skill-bundle-1.6.0.zip` 并核对完整文件清单/确定性。任一根或 Artifact 损坏使当批发布数为零；Development Artifact 不进入 Bundle |
| AC-027-03 | 发布后从正式资产入口取得同一 `skill-bundle-1.6.0.zip`，解压后逐个将五个 Skill 根交给 Next / SR-004；执行 SR-008 Echo 与 MAS 对应消费验收。Host 运行环境移除作者 checkout 和 Compiler 后仍可运行；分别记录构建、发布及消费状态 |

## 4. 状态与非目标

中央设计 Issue #113；目标仓 `odango-chan/ca-skills`。实施 Issue=`NOT_CREATED`，仅 SR-027 独立评审达到 READY 后创建；新 Issue 必须引用本 SR、F08 设计 SHA、CA-SL 1.6.0 / Compiler API 版本、五根作者源矩阵和 AC-027-01/02。当前只完成设计，不实施、不发布。AC-027-01/02/03 产品测试仍 NOT_RUN；发布授权只在正式 Release 步骤使用。SR-013 / SR-008 / SR-029 / SR-025 / SR-030 是上游设计依赖；SR-004 是消费验收，不反向阻塞构建设计。

## 5. 当前产品输入状态与跨仓绑定（2026-11-27）

| 输入 | 中央设计目标 | 当前产品事实 | 对本 SR 的影响 |
|---|---|---|---|
| CA-SL 1.6.0 | `connectionagent.io/v1.6.0`，规范在 Next | ca-skills PR #88 / #89 只覆盖 v1alpha5 同标识刷新；1.6.0 Schema / Golden / 五根作者源尚未发布 | 产品 AC NOT_RUN；不阻塞中央设计评审 |
| Compiler | Release `3.0.0`；Artifact `/2`；BuildRequest / DependencyInspection / BuildResult `/2` | 当前正式 Release 仍 v2.1.0；Compiler #61 是 v1alpha5 目标；1.6.0 新 Runtime Artifact 未实现 | 由 SR-013 / ca-skill-compiler 实施；#61 不得复用 |
| Echo Interface | `urn:example:echo:interface@1.0.0`；Capability `example.echo.message.read` ↔ Callable `echo.read` | Echo Plugin 示例位于 Next；正式 Interface Package 尚未导出 | 由 SR-008 / ca-agent-next 实施，不是 ca-skills 外部 Owner |
| 五个 Skill 作者根 | 同一 ca-skills commit；1 SKILL.md-only + 4 Assurance | 当前固定 ca-skills SHA `780497a` 只有三份 MAS 根，无两个 Echo 根 | 作者源实施 Issue 在 SR-027 READY 后创建 |
| Bundle | `skill-bundle-1.6.0.zip`；五根全量原子发布 | 当前无 1.6.0 Bundle、无正式发布资产 | AC-027-02/03 NOT_RUN；不是设计阻塞 |

**当前阶段结论：** SR-027 的生产端设计现已在 Next 明确；仍需独立评审，不能直接实施。产品输入缺失属于后续实施/验收状态，不再作为要求 ca-skills 或 Compiler Owner 先发布、再由消费端猜测设计的理由。

### 5.1 目标仓与实施 Issue 绑定

| 工作 | 中央 SR | 目标仓 | 实施 Issue |
|---|---|---|---|
| 五个作者根、CA-SL 1.6.0 作者 Schema / Golden、Bundle Builder 与发布 | SR-027 / SR-029 | `odango-chan/ca-skills` | `NOT_CREATED`，SR-027 / SR-029 READY 后创建 |
| Compiler 1.6.0 Runtime Artifact / Build / Verify | SR-013 | `odango-chan/ca-skill-compiler` | `NOT_CREATED`，SR-013 READY 后创建；#61 是 v1alpha5 历史 Issue |
| Echo Interface Package | SR-008 | `odango-chan/ca-agent-next` | `NOT_CREATED`，SR-008 READY 后创建 |

ca-skills 实施 Issue 只覆盖作者源和 Bundle 组装，不实现 Compiler、Echo Plugin Interface 或 Owner/Provider Package。生产仓不得复制本 SR/F08 作为第二套权威设计；Issue 创建后引用中央设计固定 SHA.
## 6. 修订记录

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
| 2026-11-27 | 0.3.0 | GPT-6.2（ChatGPT） | §2.2、§3、§4、§5、文档头 | 固定 CA-SL / Compiler 机器契约、五根作者源与编译矩阵、Echo Interface 归属、Bundle 目录/ZIP/原子发布及目标仓 Issue 门槛 | 将 SR-027 从外部发布物阻塞改为可独立评审的生产端设计 | Issue #113；F08；SR-008/013/029/025/030 |
