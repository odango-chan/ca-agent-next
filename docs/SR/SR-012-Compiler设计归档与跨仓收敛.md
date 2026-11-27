# SR-012 Compiler 设计归档与跨仓收敛

> 文档版本：0.1.8\
> 状态：DRAFT（实施主状态）；第二轮独立评审 CHANGES_REQUESTED（历史结论）；第三轮自评 **DESIGN_READY_FOR_INDEPENDENT_REVIEW**（仅设计评审候选，非独立批准或实施 READY）；产品 AC NOT_RUN/BLOCKED。
> 上游 IR：IR-006  
> 创建日期：2026-11-25  
> 修订日期：2026-11-27\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、5GC/MAS 认证及发布。

## 0. 本轮设计评审入口（2026-11-26）

本 SR 纳入 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计评审批次。**SR 实施主状态依旧为 `DRAFT`；设计 `REVIEW_REQUESTED` 不等于独立 APPROVED、实施 READY 或产品 PASS。** 单版本决定见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**Compiler 活动设计与中央 EC02 文档的权威映射、历史冻结发布只读归档、源仓重复正文迁移后的路径。
- **阻塞/未验证：**Compiler #61 的 1.6.0 Artifact/API 与 Next main 尚未就绪；不能先替换源仓权威文档链接。
- **通用架构约束：**新 CA-SL 作者源、Compiler API/Build DTO、Runtime Artifact、Bundle、Studio 与 Agent Importer/Runtime **只支持 1.6.0**；Skill 只选择 Capability ID，公开 Capability↔Callable 双向一对一。历史版本材料只读留档；不做别名、兼容、双轨、迁移或 fallback。机器字段/ID 必须等待发布者冻结，不猜测。
- **评审输出：**逐项核对范围、非目标、外部 Owner、错误/状态语义、Acceptance 与证据路径。设计无独立结论写 `PENDING_REVIEW`；未发布依赖写 `BLOCKED`；未运行测试写 `NOT_RUN`。当前不得派发 DeepSeek Harness 实施任务。

目标是让 Next EC02 成为现行 Compiler 机制设计入口。设计依据为 [EC02 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.13 §1–4。

本 SR 的唯一实施仓为 `odango-chan/ca-skill-compiler`。Next 上的 EC02、IR/SR 和审计属于中央设计输入与结果回填。以 Compiler `255ab85fa5abb4b0bf36656bf64250cafebf45cb` 的 README.md、README.zh-CN.md 为导航入口，对 `git ls-tree -r --name-only HEAD docs` 中的活动设计逐项比对 EC02。仅在可定位到已评审的中央章节时将重复正文改为链接；无法对应的条目列为差异并保留原文。用 `git diff --name-status` 检查变更仅落在已登记的文档，逐个验证新增的中央链接在 Next 默认分支可达。保留机器契约、实现、测试、示例、运行说明和发布证据。其他协作仓仅在发现重复 EC02 设计后，通过覆盖目标仓的 SR 处理。CA-SL 作者规范的**中央设计权威在 Next**，ca-skills 负责正式作者 Schema/Release 和作者源实现，不在 Compiler 目标仓复制一份新规范。Compiler #61 的实现及版本发布单独追踪。

**AC-012-02 文件处置清单**。中央接收位置分别见 [EC02 Compiler](../设计说明书/EC02-Compiler/Compiler设计说明书.md)、[工具链](../设计说明书/EC02-Compiler/工具链设计.md)、[Development Build](../设计说明书/EC02-Compiler/Development%20Build设计.md) 与 [Evidence 职责](../设计说明书/EC02-Compiler/Evidence职责设计.md)。以本节固定 Compiler SHA 为源。在目标仓中根 `README.md`、`README.zh-CN.md` 与 `docs/README.md`、`docs/README.zh-CN.md` 只更新设计导航。下表路径相对 `docs/design/`。指定为“链接”的部分只有在 Next 默认分支对应章节可达且保存固定历史来源后才可替换。

| 文件 | 处置 |
|---|---|
| `README.md` | 导航 → EC02 Compiler 设计说明书 §1 |
| `README.zh-CN.md` | 导航 → EC02 Compiler 设计说明书 §1 |
| `archify-redraw-brief-scp-only-20261119.zh-CN.md` | 保留历史制图 brief |
| `ca-toolchain-architecture-vnext.zh-CN.md` | 链接 → EC02 工具链设计 |
| `compiler-artifact-v1alpha5.md` | 保留冻结 v1alpha5 Artifact 正文 |
| `compiler-core-v1alpha5.md` | 保留冻结 v1alpha5 Core 正文 |
| `compiler-development-build-harness.zh-CN.md` | 链接 → EC02 Development Build 设计，保留冻结命令与历史运行段 |
| `compiler-development-build-implementation-report.zh-CN.md` | 保留历史实施报告 |
| `compiler-development-build-pilot.zh-CN.md` | 链接 → EC02 Development Build 设计，保留历史版本边界 |
| `compiler-evidence-assurance-responsibility-audit.zh-CN.md` | 链接 → EC02 Evidence 职责设计，保留历史证据 |
| `compiler-evolution-roadmap-vnext.zh-CN.md` | 链接 → EC02 Compiler 设计说明书的演进边界，保留历史路线记录 |
| `fixtures/registration-development-request.json` | 保留机器输入 fixture |

从 Compiler 仓根执行 `git ls-tree -r --name-only 255ab85fa5abb4b0bf36656bf64250cafebf45cb -- docs/design`，输出必须逐行匹配上表 12 个文件。再执行 `git ls-tree -r --name-only 255ab85fa5abb4b0bf36656bf64250cafebf45cb -- docs`，预期共 218 个文件，其余 206 个（含两份 docs 导航）按上述导航例外或原样保留。活动分支相对此清单新增的活动设计须先映射。执行 `git diff --name-status 255ab85fa5abb4b0bf36656bf64250cafebf45cb HEAD -- docs/design` 核对源漂移，实施 diff 另用 `git diff --name-status <实施基线SHA> HEAD`。逐个新增的 Next 默认分支链接运行 `curl --fail --location --silent --output /dev/null "$URL"` 并检查目标页章节；未映射、越界修改、断链或错误锚点均停止。**本 SR 可在 PR #46 固定候选 Head 独立评审；在 #44→#45→#46 集成到目标默认分支且相关中央链接真实可达前，不得替换 Compiler 源仓的活动设计正文。**

依赖分类：**设计依赖**为 Next EC02（目前 1.6.0 候选可评审）；**实施依赖**为中央文档进入 main 且源仓活动文档链接已可达；**模块 AC** 由静态迁移证据独立取证；**系统 Compiler 1.6.0 Release** 由 SR-013 独立负责，不作为本设计评审的先决。跨仓改动仍须独立实施 Issue、固定设计 SHA 和授权。

| 验收 ID | 验收内容 | 证据状态 |
|---|---|---|
| AC-012-01 | EC02 设计、IR/SR、源 SHA、Issue、范围和修订可双向导航 | DESIGN |
| AC-012-02 | Compiler 默认分支的设计入口指向 Next；清理重复活动设计且保留冻结历史及机器契约，文档门禁通过 | NOT_RUN |
| AC-012-03 | 审查每项冻结决策及候选 when 的状态，提供可复核的 Harness 门槛和证据路径 | DESIGN |

Issue [Next #2](https://github.com/odango-chan/ca-agent-next/issues/2)；依赖工作 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。实施 PR、Commit、受测 SHA 与测试证据待回填。替代关系：无。

### 设计移交与模块验收的独立映射（2026-11-26）

**性质**：源文档与 Next 的静态迁移/治理验收；真实 Compiler 1.6.0 发行归 SR-013，不在本 SR 复用旧 Release。 不新增不必要的生产 DFX/Qualification，也不因外部 Release 尚未发布而整体阻断设计审查。

| 模块 AC | 样本/动作 | 预期与证据边界 |
|---|---|---|
| AC-012-01 | 固定 Compiler 源 SHA、Next EC02 入口、IR/SR/Issue 双向链接 | 引用全部可达；旧 Runtime API/Golden 不被覆写 |
| AC-012-02 | 源仓活动 docs 与 Next EC02 对照；重复项/无法映射项分别归类 | 仅已批准重复正文变链接；无法映射保留原文；Git diff 文件范围明确 |
| AC-012-03 | 记录每项 v1alpha5/Development v1alpha1 为历史、1.6.0 新目标与 Compiler #61 的产品 Release 状态 | 核对 EC02《工具链设计》§3.2.1 与主设计 §11，旧版仅进入历史清单；现行 Loader、Resolver、Runtime 遇旧 Artifact 均拒绝且 IPC=0。源仓入口收敛另按 AC-012-02 取证 |

**执行及证据**：设计 AC 以固定中央设计 HEAD、源仓 SHA、准确文件/符号/静态 diff 与逐项对照表取证；若此轮未实际读/跑某源代码或测试，则记录 `NOT_RUN` 而不是 PASS。跨仓源仓代码修改必须有独立实施 Issue/PR、授权并在相应产品 SR 留痕。已有的 SRxxx-A/B/... 原验收保留作细项追踪，不能据此把模块产品或 Next E2E 状态提升为 VERIFIED。

## 修订记录


| 日期 | 版本 | 修订者 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 设计基线 | 集中维护及验证交接 | IR-006、SR-012、#2 |
| 2026-11-25 | 0.1.1 | Codex / GPT-6 | 正文 | 明确唯一实施仓与文档移交流程 | 消除执行歧义并同步中央设计 | Issue #12 SR-012 |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | 正文 | 同步所引权威设计版本 | 消除执行歧义并同步中央设计 | Issue #12 SR-012 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记统一 1.6.0 专项设计评审、阻塞与证据边界；不改变产品实施主状态 | 设计集中评审、避免历史来源冒充新发布 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.1.4 | GPT-6（ChatGPT） | 设计移交与模块验收 | 新增独立 AC / 来源 SHA / 与实现产品、系统 E2E 证据隔离 | 使设计移交在无需臆造产品发布的情况下可逐项审查 | Issue #12；SR-029；PR #46 |
| 2026-11-26 | 0.1.5 | GPT-6（ChatGPT） | 最新权威设计依据 | 同步最新版 1.6.0 Feature/EC02，Studio 不再引用历史 §4.5 | 避免 Harness 误把旧 Development Publisher 当成新目标 | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.1.6 | Codex / GPT-6 | AC-012-02 | 固定逐文件清单、版本与文档差异检查 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.1.7 | Codex / GPT-6 | AC-012-03 | 将权威入口的版本一致性列为归档核查项 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.1.8 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | Compiler 固定源 docs/design 12 条、docs 218 文件已独立从 Git tree 对账；仅在 Next 中央链接进目标默认分支后替换源仓活动设计；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-012 |
