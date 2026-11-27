# SR 总索引

> 文档类型：软件需求索引  
> 文档版本：0.3.61
> 状态：31 项 SR：4 VERIFIED、1 IMPLEMENTED、26 DRAFT；PR #46 原 24 项批次的 23 项独立评审已归档；SR-031（IR-009）与 SR-032（IR-008）为独立增量设计候选，AC-031/032 产品验收 NOT_RUN；READY 不因本次文档集成自动变化。
> 修订日期：2026-11-27\
> 权威规则：[SR 管理规范](../规范/SR%20管理规范.md)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  

跨仓任务从 Next 发起。先在本仓登记覆盖目标仓和修改范围的 SR，达到 READY 后再切换到目标仓实施，目标仓结果回填本仓 SR。既有外部 Issue 可作为关联入口。详见《SR 管理规范》§8.1。

## 1. 使用规则

- 每项 SR 的完整范围和验收条件以对应 SR 文件为准。
- 本索引只汇总 ID、标题、设计依据、状态、依赖和实施入口。
- 状态变化先更新 SR 文件，再更新本索引和[实施状态总览](实施状态总览.md)。
- 正式独立评审必须在 GitHub PR Review/Issue comment 留存完整 SHA 和逐 SR/AC 结果；独立性由评审模型/上下文判定，同一 GitHub 账号不构成否定理由。模型结论与平台 Review event 分开记录，详见[SR 管理规范 §8.3](../规范/SR%20管理规范.md#83-正式评审结果必须持久化到-github)。
- ca-agent-next PR #1 是文档/设计基线 PR，不是任何 SR 的实现 PR。
- PR #1、#32、#34 已合并；SR-001/SR-002/SR-003/SR-024 VERIFIED，SR-015 IMPLEMENTED，其余 26 项 DRAFT（原 24 项属于 PR #46 批次；SR-031、SR-032 为独立增量候选；均非实施 READY）。

## 2. SR 清单

| SR | 上游 IR | 需求 | 状态 |
|---|---|---|---|
| [SR-001](../SR/SR-001-评审上下文自动生成.md) | [IR-001](../IR/IR%20总登记册.md#ir-001) | 评审上下文自动生成 | VERIFIED |
| [SR-002](../SR/SR-002-Python%20核心与宿主基础骨架.md) | [IR-002](../IR/IR%20总登记册.md#ir-002) | Python 核心与宿主基础骨架 | VERIFIED |
| [SR-003](../SR/SR-003-统一插件管理器与扩展通信.md) | [IR-002](../IR/IR%20总登记册.md#ir-002) | 统一插件管理器与扩展通信 | **VERIFIED（模块）** |
| [SR-004](../SR/SR-004-已发布技能包导入.md) | [IR-003](../IR/IR%20总登记册.md#ir-003) | 已发布技能包导入 | DRAFT |
| [SR-005](../SR/SR-005-技能目录与条件程序消费.md) | [IR-003](../IR/IR%20总登记册.md#ir-003) | 技能目录与已检查 when 程序消费 | DRAFT |
| [SR-006](../SR/SR-006-技能解析器与续跑选择.md) | [IR-003](../IR/IR%20总登记册.md#ir-003) | 技能解析器与 continuation 选择 | DRAFT |
| [SR-007](../SR/SR-007-统一运行时动作边界与双执行模式.md) | [IR-004](../IR/IR%20总登记册.md#ir-004) | 统一运行时动作边界与双执行模式 | DRAFT |
| [SR-008](../SR/SR-008-Echo%20垂直端到端示例.md) | [IR-004](../IR/IR%20总登记册.md#ir-004) | Echo 垂直端到端示例 | DRAFT |
| [SR-009](../SR/SR-009-OpenAMSM%20SBI%20事件插件与二进制产物交接.md) | [IR-005](../IR/IR%20总登记册.md#ir-005) | OpenAMSM SBI 事件插件与二进制产物交接 | DRAFT |
| [SR-010](../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md) | [IR-005](../IR/IR%20总登记册.md#ir-005) | OpenAMSM 工具插件与按需编解码集成 | DRAFT |
| [SR-011](../SR/SR-011-真实%20OpenAMSM%20创建修改释放端到端验证.md) | [IR-005](../IR/IR%20总登记册.md#ir-005) | 真实 OpenAMSM 创建修改释放端到端验证 | DRAFT |
| [SR-012](../SR/SR-012-Compiler设计归档与跨仓收敛.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Compiler 设计归档与跨仓收敛 | DRAFT |
| [SR-013](../SR/SR-013-Compiler已检查when与发布产物.md) | [IR-003](../IR/IR%20总登记册.md#ir-003) | Compiler 已检查 when 与发布产物 | DRAFT |
| [SR-015](../SR/SR-015-工具契约设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 工具契约设计移交 | IMPLEMENTED |
| [SR-016](../SR/SR-016-工作台设计移交与条件编辑.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 工作台设计移交与条件编辑 | DRAFT |
| [SR-017](../SR/SR-017-业务插件设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 业务插件设计移交 | DRAFT |
| [SR-018](../SR/SR-018-业务所有者设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 业务所有者设计移交 | DRAFT |
| [SR-019](../SR/SR-019-仿真对端设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 仿真对端设计移交 | DRAFT |
| [SR-020](../SR/SR-020-参考宿主设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 参考宿主设计移交 | DRAFT |
| [SR-021](../SR/SR-021-原生宿主设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 原生宿主设计移交 | DRAFT |
| [SR-022](../SR/SR-022-执行内核设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 执行内核设计移交 | DRAFT |
| [SR-023](../SR/SR-023-技能作者源与语言规范移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 技能作者源与语言规范移交 | DRAFT |
| [SR-024](../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Host Context Interface Package Publisher（历史 v1alpha5） | VERIFIED（历史范围） |
| [SR-025](../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | MAS Owner 1.6.0 Capability-first Interface Package Publisher | DRAFT |
| [SR-026](../SR/SR-026-Codec公开工具发布.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Codec 公开工具发布 | DRAFT |
| [SR-027](../SR/SR-027-技能Bundle构建与发布.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 技能 Bundle 构建与发布 | DRAFT |
| [SR-028](../SR/SR-028-Python工程工具链与uv环境管理.md) | [IR-007](../IR/IR%20总登记册.md#ir-007) | Python 工程工具链与 uv 环境管理 | DRAFT |
| [SR-029](../SR/SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) | [IR-008](../IR/IR%20总登记册.md#ir-008)（关联 IR-003） | CA-SL 1.6.0 Capability-first 作者模型与 Callable 双向一对一；完全无旧版兼容 | **DRAFT（设计待评审，非实施 READY）** |
| [SR-030](../SR/SR-030-Host%20Context%201.6.0%20Schema-only%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Host Context 1.6.0 Schema-only Interface Package Publisher | DRAFT |
| [SR-031](../SR/SR-031-3GPP公共Schema-only-Publisher.md) | [IR-009](../IR/IR%20总登记册.md#ir-009) | OpenAMSM 3GPP OpenAPI 原版 Source Bundle 原样代发布（ca-skills） | **DRAFT（增量设计待评审、Publisher / Consumer 产品 NOT_RUN）** |
| [SR-032](../SR/SR-032-SKILL作者规范与Node设计原则.md) | [IR-008](../IR/IR%20总登记册.md#ir-008) | SKILL 作者规范、原有 CA-SL 四阶段 / DAG 结构、共享 Package 资源、Host Resource Read、全 Registry Script Runner、Script I/O / Evidence / 错误契约、Node 粒度与注释原则（无 Skill Wait） | **DRAFT（Issue #49 增量设计待独立评审；仅中央文档，非实施 READY）** |

设计版本与章节、依赖、验收 ID、实施证据以各 SR 为准。逐项阻塞见[就绪审计](../参考与审计/跨仓设计资产迁移与一致性审计.md#8-设计就绪审计)。

### 2.1 第三轮独立模型评审记录（2026-11-27）

**正式评审证据：**[GitHub Review #6082541121](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6082541121)，事件为 `COMMENTED`，提交时间 2026-11-27T02:02:40Z；评审模型为 DeepSeek Harness Goal / `opencode-go/deepseek-v4.1-flash` / reasoning effort `low`。用户确认作者模型与评审模型不同，因此这是**独立模型评审**；同一 GitHub 登录不否定模型层独立性。GitHub event 仍是 COMMENTED，不得写成平台 APPROVED。

- **固定评审基线：**Head `3d5f17b7f921788d5d38378edb2a14165ea0e03e`；Base `3c7c48383c52504a4861900bc1f8b731442f16c2`；29 条 inline comments 均绑定该 Head。
- **历史第二轮证据限制：**仓内曾登记第二轮评审基线 `1bf748db86c553dfcbf140477928fd68d811e67e`，但其原始 GitHub Review URL/ID 在当前可访问 Review API 与 PR Conversation 中不可恢复；该结论仅为仓内登记，原始证据不可访问，不作为正式独立审批证据。
- **第三轮结论：**19 项限定范围 `APPROVE_FOR_READY`、3 项 `CHANGES_REQUESTED`（SR-007/009/011）、2 项 `BLOCKED_EXTERNAL_INPUT`（SR-026/027）；0 P0 / 4 P1 / 25 P2。限定认可不是整项 SR READY，也不代表产品 AC/EX/OM PASS。
- **评审边界：**本 Review 只覆盖固定 Head `3d5f17b7...`，不外推至其后提交。当前分支的修订必须以最终 Head 重新独立评审。

| SR | 第三轮独立模型评审结论 | 限定范围 / 未解决边界 | 实施主状态 |
|---|---|---|---|
| SR-004 | APPROVE_FOR_READY（限定） | 仅 SKILL.md-only、Importer candidate、AC-004-01/02/05/06A；AC-004-03/04/06B 依赖正式 1.6.0 输入，整项不 READY | DRAFT |
| SR-005 | APPROVE_FOR_READY（限定） | Catalog 原子激活/热路径；AC-005-06 需区分 Importer 与 Catalog 证据归属 | DRAFT |
| SR-006 | APPROVE_FOR_READY（限定） | 直接文本、when 三态、幂等冲突与原代际 Continuation | DRAFT |
| SR-007 | CHANGES_REQUESTED | P1：AC-007-05 缺 Owner Proof 完整身份字段与同 ID Proof 负例 | DRAFT |
| SR-008 | APPROVE_FOR_READY（限定） | 三场景静态设计；真实 Echo 运行仍阻塞 | DRAFT |
| SR-009 | CHANGES_REQUESTED | P1：Plugin Run 所有权矛盾；completion Event type / payload Schema / fixtures 未冻结 | DRAFT |
| SR-010 | APPROVE_FOR_READY（限定） | Host ArtifactStore/Channel 与 06A；06B/07/08 依赖正式 Codec 等资产 | DRAFT |
| SR-011 | CHANGES_REQUESTED | P1：AC-011-04 缺 N1/N2 乱序、交错、多事务与旧代际断言 | DRAFT |
| SR-012 | APPROVE_FOR_READY（限定） | 固定源 docs/design=12、docs=218；源仓正文替换仍等默认分支链接 | DRAFT |
| SR-013 | APPROVE_FOR_READY（限定） | Compiler/Schema-only 设计与历史 PoC 归档；新产品 AC 未运行 | DRAFT |
| SR-016 | APPROVE_FOR_READY（限定） | Studio 同源与六宿主设计；正式发布和六宿主实测未完成 | DRAFT |
| SR-017 | APPROVE_FOR_READY（限定） | 业务 Plugin 静态移交；需补 SR-009 completion 对照 | DRAFT |
| SR-018 | APPROVE_FOR_READY（限定） | 仅历史 Owner AC-018-01/02/04；不代表新版包或 Next PASS | DRAFT |
| SR-019 | APPROVE_FOR_READY（限定） | Mock peer 静态移交；运行和真实 NF/E2E 未执行 | DRAFT |
| SR-020 | APPROVE_FOR_READY（限定） | Python Host 参考审计；AC-020-04 需补 SR-030 新 Publisher 边界 | DRAFT |
| SR-021 | APPROVE_FOR_READY（限定） | Go Host 只读参考；不替换 Next Python Host | DRAFT |
| SR-022 | APPROVE_FOR_READY（限定） | Runtime 语义对照；不倒灌 Next 产品验收 | DRAFT |
| SR-023 | APPROVE_FOR_READY（限定） | 历史作者规范移交；设计依据需补版本/章节 | DRAFT |
| SR-025 | APPROVE_FOR_READY（限定） | 中央 MAS Owner Publisher 设计；正式发布仍阻塞 | DRAFT |
| SR-026 | BLOCKED_EXTERNAL_INPUT | Codec 公开 ID、Schema、slot/mediaType、handler、Package/SemVer、正式 SHA 与进程证据缺失 | DRAFT |
| SR-027 | BLOCKED_EXTERNAL_INPUT | 五根同批 1.6.0 作者提交、Echo Interface、新 Compiler Release/argv、Bundle 资产及授权缺失 | DRAFT |
| SR-028 | APPROVE_FOR_READY（第七轮 Review #6084094037；固定 Head `93f1389e`） | 0 P0 / 0 P1 / 2 P2（非阻断，P2-1/2 已按 Issue #96 comment #7212463039 关闭）；READY 回填 PR #97 OPEN / 未合并；实施 PR #99 OPEN / 未合并；AC-028-01/02/03/06/07/08/09/10 独立核验 PASS，AC-028-04/05 脚本级证据已补充、更新独立复核待完成 | DRAFT |
| SR-029 | APPROVE_FOR_READY（限定） | 中央 1.6.0 Capability-first 设计；生产者机器契约未发布 | DRAFT |
| SR-030 | APPROVE_FOR_READY（限定） | Schema-only 设计与 AC-030-01 固定源审计；新版 Publisher 未发布 | DRAFT |


### 2.1.1 SR-028 专项独立复评（2026-11-27）

**前一轮正式评审证据：**[PR #46 Review #6082874849](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6082874849)，固定 Head `37d22e9862d22bdc07edb48ffd84b976663a48f4` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`，结论 CHANGES_REQUESTED（0 P0 / 7 P1 / 2 P2）。该 Review 只覆盖 SR-028，并取代 SR-028 在 Review #6082541121 中的旧 Head 限定认可；不改变其他 SR 结论。

**第四轮正式评审：**[PR #46 Review #6083225844](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6083225844)，平台事件 `COMMENTED`；固定 Head `42a7fe2ce7826b7cda74110e843f39401571299c` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`。独立评审模型为 `codearts/deepseek-v4.1-flash` / `reasoning_effort=low`，结论 CHANGES_REQUESTED（0 P0 / 4 P1 / 3 P2）。上一轮 4 P1 / 3 P2 已在第五轮复评中全部 CLOSED。

**最新第五轮正式评审：**[PR #46 Review #6083641266](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6083641266)，平台事件 `COMMENTED`；固定 Head `ee73ad48f9cf4132561f7a72065086ef00bb3606` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`。模型结论 CHANGES_REQUESTED，0 P0 / 1 P1 / 3 P2；唯一 P1 R028-17 阻断 READY。

**历史第六轮正式评审：**[PR #46 Review #6083872622](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6083872622)，平台事件 `COMMENTED`；固定 Head `2d20a128a1574103d709d82f6c426580ecb47f48` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`。独立模型 `codearts/deepseek-v4.1-flash` / `reasoning_effort=low`，结论 CHANGES_REQUESTED（0 P0 / 1 P1 / 2 P2）。评审原任务 Head `07346aae` 曾漂移，经用户授权改以 `2d20a12` 固定快照；评审报告说明 G02/SR-028 在各中间快照逐字节一致。随后分支在本轮整改起点前推进至 `072248ff`，增量为其他 SR 与治理文档，不改 G02/SR-028。

**最新第七轮正式评审：**[PR #46 Review #6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6084094037)，固定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`，结论 `APPROVE_FOR_READY`（0 P0 / 0 P1 / 2 P2）；P2-1/P2-2 不阻断 READY，后续实施证据必须包含负例 PR base / 文件清单和 `run-context.txt` 中真实 `base_sha`、注入 `generator_base_sha`、`failure_injection=invalid-base`。关闭检查点见 [Issue #96 comment #7212463039](https://github.com/odango-chan/ca-agent-next/issues/96#issuecomment-7212463039)。

**实施状态（截至 2026-11-27）：**READY 回填 PR #97（Head `66a82f0`）OPEN / 未合并；实施 PR #99（Head `83d23e8`）OPEN / 未合并。PR #99 独立实施复核 #6085168356 已确认 AC-028-01/02/03/06/07/08/09/10；当时 AC-028-04/05 仍因缺少脚本级执行闭环。Issue #96 comments [#7213406863](https://github.com/odango-chan/ca-agent-next/issues/96#issuecomment-7213406863) 与 [#7213473388](https://github.com/odango-chan/ca-agent-next/issues/96#issuecomment-7213473388) 随后补齐 stdout/stderr、整体及子步骤退出码、cleanup、worktree list、`EVIDENCE_DIR` 与最终工作区状态；这两项更新证据尚待独立复评。故实施 PR 仍 OPEN，SR-028 不得标记 VERIFIED。

- **R028-21（P1）：**AC-028-08 受控负例同时要求测试通过和 head `Agent.md` 的 `review_scope` 无效，但测试模块导入时直接从仓库根 `Agent.md` 派生 fixture；破坏该配置会先令 gate 失败，生成器步骤被跳过，无法产生生成器诊断证据。
- **R028-22（P2）：**AC-028-08 证据列缺少负例 PR 不合并、恢复后重新执行成功路径的明确证据。
- **R028-23（P2）：**G02 §3.8 与 §4.3 gate 自动断言字段遗漏 `discovery_exception`。
- R028-17～23 均已 CLOSED；前四轮 4 P1 / 3 P2 无回归。第七轮设计结论 APPROVE_FOR_READY；产品证据按 PR #99 及 Issue #96 逐 AC 记录，AC-028-04/05 更新证据的独立复核待完成。
- 当前设计追踪 Issue #12 已完成第七轮评审；原 G02 设计 Issue #35 已 CLOSED。方案 B 负例采用有效 `Agent.md` + gate PASS + 临时 Workflow PR 注入全零 base SHA；实施证据已归档至 Issue #96。
- **R028-17（P1）：**G02 §3.8 将 gate JSON/log 与生成器证据放在 `if: always()` 上传，与 AC-028-08 正式 Artifact 恰含三份文件、现有 `if: success()` 和失败时不上传完成态 Artifact 的契约冲突；必须拆分诊断 Artifact 与正式三文件 Artifact，分别明确名称、文件集合和上传条件。
- **R028-18（P2）：**`loader_errors` 字段语义/来源/计数未定义。
- **R028-19（P2）：**SR-028 AC-028-07 的 `pull_request.paths` 枚举不完整，需与 G02 完整清单一致。
- **R028-20（P2）：**SR §5.1 要求逐范围 `exit_code`，G02 仅定义整体 `exit_code`，需统一逐范围和整体定义。
- 第五轮固定基线核验通过；G02 §4.1/§4.2 Bash 故障注入显示前轮 fail-fast/cleanup 规则 CLOSED，A-return 全部 `--no-sync`；该仿真不是 uv 0.13.10 产品运行证据。当前产品证据由 PR #99 / Issue #96 管理，AC-028-04/05 更新后的脚本级证据待独立复评。
- 第七轮设计复评已 APPROVE_FOR_READY；READY 回填 PR #97 与实施 PR #99 均 OPEN / 未合并。当前分支仍保留基线 DRAFT 状态；PR #99 已有 AC-028-01～10 产品证据，AC-028-04/05 更新后的脚本级证据等待独立复评；未合并前不标记 VERIFIED。

### 2.2 第三轮发现的修订追踪与当前门槛

- **P1（4 条）**：SR-007、SR-009、SR-011 的阻断问题已在本分支修订；各自新增 AC/契约断言仍须对最终 Head 独立复评。
- **P2（25 条）**：覆盖 SR-004/005/006/007/008/010/013/017/020/030、SR 总索引证据说明，以及 SR-005/013/017/018/019/020/021/022/023/025 十份修订账本；修订完成不等于原 Review 自动重新批准。
- **外部阻塞**：SR-026/027 仍缺生产者正式输入；不允许以文档补写替代外部发布。
- **实施门槛**：PR #46 原 24 项批次的整项主状态在本分支仍按 DRAFT 记录；SR-028 已有第七轮 APPROVE_FOR_READY，但 READY 回填 PR #97 与实施 PR #99 均 OPEN / 未合并，故本基线 READY=0。PR #99 产品证据已提交，AC-028-04/05 更新后的独立复核待完成；不得将 OPEN PR 视为已合并实施。其他 SR 的产品门槛仍按各自 AC/依赖独立记录。
- **SR-028 专项门槛**：第七轮 Review #6084094037 对固定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` 给出 `APPROVE_FOR_READY`（0 P0 / 0 P1 / 2 P2）；READY 回填 PR #97 OPEN / 未合并，实施 PR #99 OPEN / 未合并；AC-028-04/05 补充的脚本级执行闭环证据待独立复评，未合并前不标记 VERIFIED。


### 2.3 23 项逐 SR 独立评审与复评入口


### 2.4 其余 21 项的下一阶段

工作依据为 PR #46 `8c4cb284627ef34d25e18051814897d274dcd346`。21 份 SR 的正文 blob 与各自独立评审快照一致。公共术语的一对一修订符合原批准范围；SR-007 的收据矩阵相关运行项留在后续阶段。完整 SR 主状态与单项 AC 的阶段 READY 分列。下表登记 4 项本仓代码子阶段、11 项中央只读子阶段和 6 项交接或等待项。各产品 AC 仍须提供运行证据。

执行入口为[Skill 链路 #93](https://github.com/odango-chan/ca-agent-next/issues/93)、[Host Channel #94](https://github.com/odango-chan/ca-agent-next/issues/94)、[只读取证 #95](https://github.com/odango-chan/ca-agent-next/issues/95)。完整目标、逐项测试命令和即时推送要求均在各自 Issue 正文。

| SR | 阶段 | AC 范围 | 实施依赖、交付与排除 | 独立评审 |
|---|---|---|---|---|
| [SR-004](../SR/SR-004-已发布技能包导入.md) | 阶段 READY（本仓 Skill 链路） | AC-004-01/02/05/06A | SKILL.md-only 导入与旧作者源/旧包拒绝。03/04/06B 等 Compiler 与正式 Bundle。 | [#68](https://github.com/odango-chan/ca-agent-next/issues/68#issuecomment-7209411777) |
| [SR-005](../SR/SR-005-技能目录与条件程序消费.md) | 阶段 READY（本仓 Skill 链路） | AC-005-01/03/04/06 | 不可变 Catalog、原子激活和 generation。集成读取 A 批 SR-004 的 candidate；02/05 等正式 CheckedExpr/DescriptorSet。 | [#69](https://github.com/odango-chan/ca-agent-next/issues/69#issuecomment-7209428208) |
| [SR-006](../SR/SR-006-技能解析器与续跑选择.md) | 阶段 READY（本仓 Skill 链路） | AC-006-01～04/06/07 | 以本地 fixture 检查选择与精确续跑，接入 A 批 SR-005 generation。05 的正式 typed-input 互操作另验。 | [#70](https://github.com/odango-chan/ca-agent-next/issues/70#issuecomment-7209449444) |
| [SR-008](../SR/SR-008-Echo%20垂直端到端示例.md) | 限定设计已认可，等待直接依赖 | AC-008-01/04（SKILL.md-only） | 已获限定设计认可。接入 A 批真实 Importer、Catalog、Resolver 后验证 Fake Model、文本 Delivery、重放与越权拒绝；02/03/05 等 Echo Interface、Bundle 和组合环境。 | [#72](https://github.com/odango-chan/ca-agent-next/issues/72#issuecomment-7210341882) |
| [SR-009](../SR/SR-009-OpenAMSM%20SBI%20事件插件与二进制产物交接.md) | 模块设计已认可，待目标仓实施交接 | AC-009-01～06（测试 Host/peer） | 独立 Go Plugin 模块已获设计认可。目标仓 ca-openamsm-plugin 的实施分支和 Issue 需登记；联调验证由 SR-011 跟踪。Create 断言须覆盖 eventType；responseObligationId 由 Host 分配。 | [#73](https://github.com/odango-chan/ca-agent-next/issues/73#issuecomment-7210217168) |
| [SR-010](../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md) | 阶段 READY（本仓 Host Channel） | AC-010-01～05（Next Host Channel） | 仅实现 Next Python Host ArtifactStore/Channel 与 no-decode 路径。06a 等真实 Importer/Catalog/Runtime 三层入口，09 等固定共享 fixtures 和联测；06b/07/08 等正式包。 | [#74](https://github.com/odango-chan/ca-agent-next/issues/74#issuecomment-7210244694) |
| [SR-011](../SR/SR-011-真实%20OpenAMSM%20创建修改释放端到端验证.md) | 限定设计已认可，等待直接依赖 | AC-011-06 静态架构断言 | 已获限定设计认可。组合实现具备后检查 Core 零业务分支；01～05 等同批 Bundle、Compiler Verify、Provider/Owner Package 和隔离对端。 | [#75](https://github.com/odango-chan/ca-agent-next/issues/75#issuecomment-7210271472) |
| [SR-012](../SR/SR-012-Compiler设计归档与跨仓收敛.md) | 阶段 READY（中央只读核验） | AC-012-01 的 Next→源仓静态部分、03 | 固定 Compiler 源树清单 218/12 与历史边界；02 源仓链接替换等默认分支与源仓授权。 | [#76](https://github.com/odango-chan/ca-agent-next/issues/76#issuecomment-7210373026) |
| [SR-013](../SR/SR-013-Compiler已检查when与发布产物.md) | 阶段 READY（中央只读核验） | AC-013-01 归档完整性 | 核对 PR #18 归档、58 项校验清单及原始报告。复跑单列；02/04 NOT_RUN，03/05/06 等 Compiler Owner 与正式契约。 | [#77](https://github.com/odango-chan/ca-agent-next/issues/77#issuecomment-7209276846) |
| [SR-016](../SR/SR-016-工作台设计移交与条件编辑.md) | 阶段 READY（中央只读核验） | MIG-016-01、AC-016-09 设计对照 | 核对 Studio 迁移来源和状态模型；02～08/10 依赖正式包与 Compiler；六宿主实测另行登记。 | [#78](https://github.com/odango-chan/ca-agent-next/issues/78#issuecomment-7210318006) |
| [SR-017](../SR/SR-017-业务插件设计移交.md) | 阶段 READY（中央只读核验） | AC-017-01～04 静态移交 | 核对固定源、F06 Event、Host/Plugin 权责和证据类型。实现归 SR-009。 | [#79](https://github.com/odango-chan/ca-agent-next/issues/79#issuecomment-7210393284) |
| [SR-018](../SR/SR-018-业务所有者设计移交.md) | 阶段 READY（中央只读核验） | AC-018-01、02（除 Release 子项）、04 | 核对 Receipt/Proof/QoS/Reconcile 固定源；Release 子项需补原始证据，03 等 Owner 24/24 正式包。 | [#80](https://github.com/odango-chan/ca-agent-next/issues/80#issuecomment-7210419119) |
| [SR-019](../SR/SR-019-仿真对端设计移交.md) | 阶段 READY（中央只读核验） | AC-019-01/02/04 静态移交 | 核对 Mock peer 源文件、场景与 fixture；03 运行测试另记。 | [#81](https://github.com/odango-chan/ca-agent-next/issues/81#issuecomment-7210443123) |
| [SR-020](../SR/SR-020-参考宿主设计移交.md) | 阶段 READY（中央只读核验） | AC-020-01/02/04 静态审计 | 核对 Python 参考 Host 采用/排除表及历史/现行 Publisher 边界；03 的运行证据另记。 | [#82](https://github.com/odango-chan/ca-agent-next/issues/82#issuecomment-7210465672) |
| [SR-021](../SR/SR-021-原生宿主设计移交.md) | 阶段 READY（中央只读核验） | AC-021-01/02/04 静态审计 | 核对 Go Host 来源、边界与晋级条件；03 的 ArtifactStore 实测另记。 | [#83](https://github.com/odango-chan/ca-agent-next/issues/83#issuecomment-7210492778) |
| [SR-022](../SR/SR-022-执行内核设计移交.md) | 阶段 READY（中央只读核验） | AC-022-01/02/04 静态对照 | 核对参考 Runtime 的语义、采用/排除及权威划分；03 的执行测试另记。 | [#84](https://github.com/odango-chan/ca-agent-next/issues/84#issuecomment-7210514058) |
| [SR-023](../SR/SR-023-技能作者源与语言规范移交.md) | 阶段 READY（中央只读核验） | AC-023-01～03 静态移交 | 以固定源核对历史作者规范、Release 与迁移目录；04 等新版 Compiler/Bundle/Importer。 | [#85](https://github.com/odango-chan/ca-agent-next/issues/85#issuecomment-7210543020) |
| [SR-025](../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) | 限定设计已认可，等待直接依赖 | 中央 Owner Publisher 设计已认可 | AC-025-01～08 的执行等待新 Owner 24/24 源、正式 Package Schema/CLI 与 Compiler 验证入口；发布另需授权。 | [#86](https://github.com/odango-chan/ca-agent-next/issues/86#issuecomment-7209318291) |
| [SR-026](../SR/SR-026-Codec公开工具发布.md) | BLOCKED_EXTERNAL_INPUT | BLOCKED_EXTERNAL_INPUT | Provider Owner 需交付 Codec 公开 Capability、唯一 Callable、输入输出 Schema、slot/mediaType、handler 和包版本。v1.2.0 与候选 PR #39 分别记录。 | [#87](https://github.com/odango-chan/ca-agent-next/issues/87#issuecomment-7209366603) |
| [SR-027](../SR/SR-027-技能Bundle构建与发布.md) | BLOCKED_EXTERNAL_INPUT | BLOCKED_EXTERNAL_INPUT | ca-skills 需交付同提交五根作者源、Echo Interface、匹配 Compiler Release/argv/Verify 和 Bundle 发布授权。 | [#89](https://github.com/odango-chan/ca-agent-next/issues/89#issuecomment-7209388846) |
| [SR-030](../SR/SR-030-Host%20Context%201.6.0%20Schema-only%20Interface%20Package%20Publisher.md) | 阶段 READY（中央只读核验） | AC-030-01 固定源，06/07 设计约束 | 核对 Subject Schema 原始字节与来源、Provenance 归属和 Demo 排除项。02～05、Publisher 实现与发布等待正式 Schema/languageTarget。 | [#91](https://github.com/odango-chan/ca-agent-next/issues/91#issuecomment-7209340753) |

**IR-009 增量设计（不追溯改变 PR #46 历史评议）：**新增 [SR-031](../SR/SR-031-3GPP公共Schema-only-Publisher.md) 与 [3GPP OpenAPI 原版引用设计](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。其独立设计评审和代码实施门槛均另行判定；AC-013-07、AC-010-10、AC-026-04～06、AC-027-05 为新设计验收要求，尚未获得原 12 项限定评审的背书。当前总数 31：4 VERIFIED / 1 IMPLEMENTED / 26 DRAFT，READY=0。当前 `PostSmContexts` 选定闭包为四份原版 YAML / 102 个 Schema Component；未选定 operation refs 不全局 eager resolve，Content-ID 必须精确关联 N1/N2/N2 Ext1 part。
**IR-008 作者规范增量设计（Issue #49）：**新增 [SR-032](../SR/SR-032-SKILL作者规范与Node设计原则.md) 与 [SKILL 作者规范](../规范/SKILL作者规范.md)，迁移 ca-skills 作者材料并新增 Node 拆分、注释原则；只覆盖中央规范，不修改 ca-skills；CA-SL 1.6.0 仅做 Capability-first / 共享资源 / Script 契约等必要修订，保留原有四阶段 / DAG / arguments / PredicateSet 结构，不定义 Skill Wait / await / polling。它是独立设计评审候选，不属于 PR #46 原 24 项或 Issue #47 / IR-009 批次。当前总数 31：4 VERIFIED / 1 IMPLEMENTED / 26 DRAFT，READY=0。

## 3. 设计恢复与实施顺序

### 3.1 中央设计恢复批次（按各 SR 状态与依赖门禁执行）

| 顺序 | SR | 主要功能 | 目标仓 / 参考仓 | 依赖和产出 |
|---|---|---|---|---|
| 1 | SR-023 | CA-SL v1alpha5、作者源与发布基线恢复 | ca-skills | 先固定语言、Skill 作者源与版本边界；Compiler #61 仍是外部 OPEN 依赖 |
| 2 | SR-015 | Tool Interface / Provider / Codec 设计恢复 | ca-client-tools → Next F03.05 | IMPLEMENTED；SR-015 合并时 F03.05 v0.3.9（现行 v0.4.4）；SR-015 v0.3.8；PR #37 MERGED，产品代码未实现 |
| 3 | SR-025 | MAS Owner 1.6.0 Capability-first Interface Package Publisher | ca-client-tools → Next F03.05 / F09 | 新 Owner 24/24 Capability↔Callable 发布；历史 24/25、Development v1alpha1 和 1.0.0 仅审计；具体新机器 Schema/版本待 Owner/Compiler 冻结 |
| 4a | SR-031 | OpenAMSM 3GPP OpenAPI 原版 Source Bundle | ca-skills → Next EC01/F06 | DRAFT / REVIEW_REQUESTED；独立于 SR-030 Host Context；Source Lock / Publisher identity / byte Golden 未发布，AC-031-01～07 NOT_RUN |
| 4 | SR-030 | Host Context 1.6.0 Schema-only Interface Package Publisher | ca-agent-demo → Next F09 | DRAFT；固定原始 Schema 来源；0 Capability / 0 Callable；新 Package Schema、languageTarget 和 SemVer 待冻结，AC-030-01～07 NOT_RUN；SR-024 VERIFIED 仅作为旧 v1alpha5 Development Publisher 历史证据 |
| 5 | SR-018 | OpenAMSM Owner 权威状态恢复 | env-openamsm | 固定 Callable、Receipt、Commit Proof、Reconcile 和 Modify/Release 边界 |
| 6 | SR-019 | Mock AMF / 5GC 仿真对端恢复 | env-5gc-sim | 固定协议对端、World、进程和真实测试边界 |
| 7 | SR-017 | OpenAMSM Event/Delivery Plugin 恢复 | ca-openamsm-plugin | 依赖 F03/F05、EC05 Owner Contract；当前 PR #1 Draft |
| 8 | SR-020 | Python Generic Host 参考实现审计 | ca-agent-demo | 为 F01/F03/F04/F05 提供可复用代码证据；不复制业务专用架构 |
| 9 | SR-022 | ca-runtime 执行内核设计审计 | ca-runtime | 与 F04 对照，区分采用、简化和排除的机制 |
| 10 | SR-016 | Skill Studio / AI Authoring 设计恢复 | ca-skill-studio-demo | 与 CA-SL、F08/F09 对齐；PR #258 已合并，部署状态独立验证 |
| 11 | SR-021 | Go Native Host 晋级目标审计 | ca-agent | 最后对照，不能改变 Next 当前 Python Host 决策 |

以上顺序是文档依赖和设计评审顺序，不是实施授权。每份 SR 必须完成设计章节、目标仓/固定 SHA、代码/测试差异、验收命令和非目标边界；评审通过后才可进入 READY。

### 3.2 Next 实施阶段

- 治理自动化：SR-001 VERIFIED；[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) MERGED（`7a0fac41e573021207ab8201bbc718718c451e50`）；AC-REV-01～10 PASS、80 tests OK、Run [45793590532](https://github.com/odango-chan/ca-agent-next/actions/runs/45793590532) success。SR-028 第七轮 Review #6084094037 已 APPROVE_FOR_READY；READY 回填 PR #97 与实施 PR #99 均 OPEN / 未合并，实施证据见 Issue #96；AC-028-04/05 补证后的独立复核待完成，不标记 VERIFIED。
- Phase A：SR-002（VERIFIED；PR #23 已集成；AC-002-01～08 PASS；EX-01 仍 NOT_RUN）。
- Phase B：**SR-003 VERIFIED（模块）**；[实施 PR #34](https://github.com/odango-chan/ca-agent-next/pull/34) 与 [治理回填 PR #41](https://github.com/odango-chan/ca-agent-next/pull/41) 均 MERGED。最终实施 Head `e8bcb1b` 与 Merge `32c7c1be` tree 一致；治理回填 Head `f3f59b54` 与 Merge `a899409` tree 一致。[CI #45815167442](https://github.com/odango-chan/ca-agent-next/actions/runs/45815167442)、[CI #45817800342](https://github.com/odango-chan/ca-agent-next/actions/runs/45817800342) 均 SUCCESS：Linux Python 3.12 + Windows Python 3.14 每平台 Plugin 87 / Host 52 / Review Context 80 tests PASS，Go Echo build、compileall 与证据采集 PASS；AC-003-01～04 均 PASS。系统 EX-02/03/04/18 仍 NOT_RUN；Provider v2 wire DTO 属 SR-010，不影响 SR-003 模块结论。
- Phase C：SR-004 DRAFT / NOT READY；[设计 Issue #43](https://github.com/odango-chan/ca-agent-next/issues/43) OPEN，SR-004 v0.2.12 已定义 AC-004-01～06。无 Assurance Package 子路径（可携带共享资源）可独立设计；新 Assurance 路径面向 **CA-SL 1.6.0**（Issue #40 / SR-029；NOT_RELEASED），还需 Compiler #61 / SR-013 唯一 Capability Binding Artifact 与 ca-skills SR-027 正式 Bundle 契约/正例。冻结 Artifact v1alpha5 与 Development v1alpha1 均不作为当前正例；未达到 READY，不创建实施 Issue、不提供 Harness 提示词。
- Phase D：SR-005、SR-006。
- Phase E：SR-007。
- Phase F：SR-008。
- Phase G：SR-009 独立 Plugin 模块可按自身 READY/Issue/授权先行，不等待 Echo；SR-010 逐子阶段核对实施依赖；两者的系统 OM 组合仍待 Echo 与 Host/Owner 对端。
- Phase H：SR-011。
- Capability-first 新版本设计：[SR-029](../SR/SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [Issue #40](https://github.com/odango-chan/ca-agent-next/issues/40)：**CA-SL 1.6.0-only / 完全无旧版兼容 / 设计待独立评审**。F02/F03.05/F04/F06/F08/F09/EC02 已加入待评审章节；Compiler/Publisher/Runtime/Studio/Bundle 新契约尚未发布，不启动代码实施。
- Compiler 外部发布依赖：SR-012、SR-013；SR-013 的 [PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN，不代表 Compiler 产品发布或完整 SR VERIFIED。

阶段顺序仅约束实际实施依赖，不限制独立设计评审。每个 SR 达到 READY 后，只有当前实施阶段的直接实施依赖满足才可启动；未满足的依赖只阻塞其消费者，不得阻塞独立 SR/AC。Goal 模式可将同一依赖批次中的多个 READY SR 合并执行，但不得跨越未满足的实施依赖或把 DRAFT SR 当成可执行任务。

### 3.3 实质修订与设计复评追踪

本轮 #46 以 1.6.0-only 的规范性内容实际替换旧 Compiler/Studio/Publisher 实施要求：EC02、SR-013 统一新 Parser/BuildRequest/Binding；F09/SR-016、SR-025 重写新版本验收；F02/F03/F03.05/F04/F06/F08 修正新旧规范冲突；SR-005～011 分开四类依赖、定义模块 AC；SR-012 和 SR-017～023 明确设计移交的独立静态 AC。设计评审与实际发布、实施和系统 E2E 分离，**当前 24 项实施 SR 仍为 DRAFT**；新 1.6.0 机器 Schema、正式 Owner/Compiler/Bundle 发布物尚未交付，产品验收 NOT_RUN。

**IR-009 / SR-031 范围裁决（2026-11-27）**：[EC01.3GPP](../设计说明书/EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md) 只代发布 OpenAMSM 实际支持的原版 OpenAPI 3.0 YAML，逐字节不改；当前 `PostSmContexts.requestBody → jsonData → SmContextCreateData` 的可达闭包为四份原版 YAML / 102 个 Schema Component，只 lazy resolve 选定根；相对 `$ref` 按 RFC 3986 / JSON Pointer 按 RFC 6901 解析，允许规范化后仍在 Source Root 内的 `../`。Plugin 原生消费 operation / multipart，并将 `n1SmMsg` / `n2SmInfo` / `n2SmInfoExt1.contentId` 精确匹配 N1 / N2 / N2 Ext1 part；Compiler 对 pin 后的 `components/schemas` 直接引用并保留 OAS3 dialect，不强制 Adapter。NAS/NGAP Codec Output Schema 由 ca-client-tools Provider 独立发布。此裁决不改变 PR #46 原 24 项评审结论或已拆分模块 AC；SR-031 Source Lock / byte compare 可独立评议，Compiler / Plugin / Codec / Bundle 未发布仍 BLOCKED。

## 4. 当前基线说明
- SR-002 设计 PR [#20](https://github.com/odango-chan/ca-agent-next/pull/20) 已 MERGED（`281ccb957b9222e72175e210d1afed177aa8a14f`）；实施 PR [#23](https://github.com/odango-chan/ca-agent-next/pull/23) 已 MERGED（`49964464e19d13d219ea0b3513d2223fe81d2435`）；设计 Issue #19 与治理 Issue #21 已关闭。SR-002 为 VERIFIED，AC-002-01～08 PASS；EX-01、CPython 3.11/3.12/3.13 矩阵及 DeepSeek Harness 仍 NOT_RUN。实施 Issue [#22](https://github.com/odango-chan/ca-agent-next/issues/22) 由本次证据回填 PR #25 合并关闭。

- 设计来源：ca-agent-next PR #1 的架构、设计、规范和 Acceptance 文档。
- PR #1：已合并；只代表设计文档变更。
- Next Runtime：README 声明尚无已验收 Runtime 实现。
- 当前 31 项 SR 中 4 VERIFIED（SR-001/002/003/024）、1 IMPLEMENTED（SR-015）、26 DRAFT（含 SR-031 / SR-032 两项独立增量设计待评审）；SR-024 VERIFIED 仅覆盖旧 v1alpha5 Development Publisher；SR-013 归档 PoC 不改变 DRAFT；SR-009 只覆盖 Event/Delivery Plugin/staging，SR-010 覆盖 Host ArtifactStore、Channel、Provider v2 Driver/Codec。
- Issue #12 追踪本轮中央设计资产恢复；PR #11/#13/#15/#16/#18 均在独立分支 OPEN/DRAFT，恢复分支已同步可复用的最新文档内容但尚未创建 PR；PR 状态不等于 SR 实施状态。
- 恢复分支 docs/restore-original-designs-20261125 尚未创建指向 main 的总 PR；SR-002 设计 PR #20 与实施 PR #23 均已合并到恢复分支，SR-002 为 VERIFIED、AC-002-01～08 PASS；EX-01 仍 NOT_RUN。该恢复分支尚未合并 main。
- ca-agent-demo、ca-client-tools、ca-skill-compiler、ca-skills 和 ca-openamsm-plugin 的现有代码/PR 只能作为外部复用或依赖证据，不能自动算作 Next SR 已实施。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 收编既有 SR-001，并建立 Phase A～H 的 10 项初始 SR | 统一需求编号和设计实施追踪 | SR-001～SR-011 |
| 2026-11-25 | 0.2.1 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 补齐文档版本与评审范围声明 | 落实正式文档版本和评审范围继承规则 | SR-001～SR-011 |
| 2026-11-25 | 0.2.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 统一 SR-002～SR-011 文件名和标题为中文 | 落实文档命名规范，保留 SR ID 不变 | SR-002～SR-011 |
| 2026-11-25 | 0.2.3 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.4 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 明确跨仓 SR 登记及证据回填 | 统一跨仓入口 | 见关联 SR |
| 2026-11-25 | 0.2.5 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 更新 EC02 归档与追踪 | 对齐中央设计及 Compiler #61 | SR-012 |
| 2026-11-25 | 0.2.6 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex 登记 Compiler 实施 SR；Codex / GPT-6 · §1–4 · 登记分仓 SR 与真实基线状态 | 对齐跨仓实施门槛；跨仓设计移交 | SR-013；IR-006 |
| 2026-11-25 | 0.2.8 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 将 SR-015～SR-024 按功能依赖排序，区分文档恢复批次与 Next 实施阶段；记录 PR #13 与 Issue #12 的真实边界，并注明 AC-013-01 隔离 PoC PASS | 避免 DRAFT 被误判为可执行，区分 PoC 与产品发布 | Issue #12；SR-013、SR-015～SR-023 |
| 2026-11-25 | 0.2.9 | GPT-6.2（ChatGPT） | §1～4 | 明确 SR-009 的 Plugin staging 边界与 SR-010 的 Next Host ArtifactStore/Channel 实施范围 | 使 F05 的 Host/Plugin 责任有唯一 SR 归属 | Issue #12；SR-009、SR-010 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §2～4 | 新增 SR-024 Host Context Interface Package Publisher；调整跨仓设计恢复顺序；将 AC-013-01 标记为报告 PASS、证据未归档、独立复核未运行 | 修复 SR-020 编号冲突，避免把 PoC 报告误作产品验收 | Issue #12/#14；IR-006；SR-013、SR-020、SR-024 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §2～4 | 明确 AC-013-01 报告性 PASS 与证据未归档状态，更新多 PR 内容协调规则 | 保持 DRAFT/READY/IMPLEMENTED 状态严格分离 | Issue #12/#14；PR #11/#13/#15/#16/#18 |
| 2026-11-25 | 0.3.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 同步当前权威设计或审计证据 | 核对 Issue #12 与固定提交 | 见就绪审计 |
| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | §2～4 | 新增 ca-client-tools MAS Owner Development Interface Package Publisher SR-025，并将其置于 SR-015 设计之后、SR-024 Host Publisher 之前 | 按目标仓分离 Owner 与 Host Publisher，避免把中央设计 SR 当作外部代码实施 SR | Issue #12；SR-015、SR-016、SR-024、SR-025 |
| 2026-11-25 | 0.3.4 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex / GPT-6 · 同步 Publisher 身份、版本和验收边界 | 对齐当前架构与实施门禁 | Issue #12 |
| 2026-11-25 | 0.3.5 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex / GPT-6 · §3～4 区分文档检查、实现和独立审批条件 | 对齐当前架构与实施门禁 | Issue #12 |
| 2026-11-26 | 0.3.6 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 更新新增两项跨仓生产端 SR 的当前统计；登记新 SR 和 IR 归属 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.3.7 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 登记 SR-002 设计修订 Issue #19 和模块/系统验收分层；保持 26 项 SR 全部 DRAFT | 让 SR 索引反映设计评审与实施门禁的真实区别 | Issue #19；SR-002～SR-007 |
| 2026-11-26 | 0.3.8 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 回填 Draft PR #20 与恢复分支目标；未改变 SR 状态和验收执行状态 | 保持索引与 GitHub 评审入口一致 | Issue #19；PR #20 |
| 2026-11-26 | 0.3.9 | GPT-6.2（ChatGPT） | §2～§4 | 同步 SR-002 v0.2.4、SR-003 v0.2.3 与 F01 v0.3.4 的追踪入口 | 使 SR 清单、依赖和设计评审状态与权威文档一致 | IR-002；SR-002；SR-003；Issue #19；PR #20 |
| 2026-11-26 | 0.3.10 | GPT-6.2（ChatGPT） | §2～§4 | 同步 SR-002 v0.2.5、SR-003 v0.2.4 与 F01 v0.3.5 的追踪入口。 | 使 SR 清单、依赖和设计评审状态与权威文档一致。 | IR-002；SR-002；SR-003；Issue #19；PR #20 |
| 2026-11-26 | 0.3.11 | GPT-6.2（ChatGPT） | §2、§4 | 同步 SR-002 PR #20 Ready for review 状态，SR 仍为 DRAFT、AC/EX 仍 NOT_RUN。 | 保持 SR 索引与实际 PR 状态一致，避免误判实施门禁。 | SR-002；Issue #19；PR #20 |
| 2026-11-26 | 0.3.12 | GPT-6.2（ChatGPT） | §2～§4 | 同步 SR-002 v0.2.6、SR-003 v0.2.4、F01 v0.3.5 与 Acceptance v0.3.7 | 使 SR 清单、依赖和验收状态与权威文档一致 | IR-002；SR-002；SR-003；Issue #19；PR #20 |
| 2026-11-26 | 0.3.13 | GPT-6.2（ChatGPT） | §1～§4 | 同步 SR-002 READY、SR-003 实施依赖语义及 SR 管理规范阶段门禁；保持 AC/EX NOT_RUN。 | 让索引只反映真实直接依赖，不把系统 EX 或后续实现阻塞提前传递。 | Issue #19；Issue #21；PR #20；SR-002；SR-003 |
| 2026-11-26 | 0.3.14 | GPT-6.2（ChatGPT） | §1～§4 | 修正 SR-002/SR-003 对 F01 的当前版本引用为 v0.3.6，并清理索引中“全部 SR 仍 DRAFT”的过期概括。 | 保持权威设计版本与当前 SR 状态一致。 | Issue #19；Issue #21；F01 v0.3.6；SR-002；SR-003；PR #20 |
| 2026-11-26 | 0.3.15 | GPT-6.2（ChatGPT） | §3～§4 | 登记 SR-002 独立实施 Issue #22，并保持 SR-003 DRAFT、实施依赖 SR-002 VERIFIED 的边界。 | 完成 READY→实施 Issue 的追踪闭环，不把设计 Issue 当作代码任务。 | Issue #19；Issue #21；Issue #22；PR #20 |
| 2026-11-26 | 0.3.16 | GPT-6.2（ChatGPT） | §1～§4 | 将 SR-002 更新为 VERIFIED，回填 PR #20/#23 的合并状态和 AC-002-01～08 PASS；保持 SR-003 DRAFT 与 EX-01 NOT_RUN。 | 使 SR 索引反映模块实现和验收的真实状态，不把系统级 EX 或其他 SR 的未完成状态传播为 SR-002 阻塞。 | Issue #22；PR #20；PR #23；SR-002 v0.2.10 |
| 2026-11-26 | 0.3.17 | GPT-6.2（ChatGPT） | §1～§4 | 将 SR-001/SR-003/SR-024 更新为 READY，并登记 Issue #27/#28/#252；同步 SR-002 VERIFIED 后的 SR-003 启动门槛 | 使索引反映最新设计审查、实施追踪和并行 SR-002 证据，不将系统 EX-01 混入模块门禁 | Issue #26～#28；ca-agent-demo #252；PR #25；PR #29 |
| 2026-11-26 | 0.3.18 | GPT-6.2（ChatGPT） | §1～§3、§5 | 将 SR-003 实施状态从等待 PR #29 改为按最终恢复分支集成 SHA 启动；保留 SR-002 VERIFIED 与 1 VERIFIED / 3 READY / 22 DRAFT 统计。 | 消除已满足门禁的过期等待表述，并使实施入口绑定最终设计基线。 | Issue #26～#28；PR #29；SR-002、SR-003 |
| 2026-11-26 | 0.3.19 | GPT-6.2（ChatGPT） | §1～§3 | 登记 SR-028 DRAFT，更新为 27 项 SR，并明确 SR-028 只有设计 Issue #35、尚无实施授权 | 建立 Python 工程工具链需求到 IR-007/G02/SR-028 的追踪，不把设计工作误作代码实施 | Issue #35；IR-007；G02；SR-028 |
| 2026-11-26 | 0.3.20 | GPT-6.2（ChatGPT） | §1～§3 | 修正 SR 总索引正文中的 26 项/22 DRAFT 过期统计，并同步 G02/SR-028 v0.1.1 命令前置 | 保证状态头部、统计正文和 SR 清单一致 | Issue #35；IR-007；G02；SR-028 |
| 2026-11-26 | 0.3.21 | GPT-6.2（ChatGPT） | §1～§3 | 回填 SR-001 最终 AC-REV-01～10 PASS、78 项专项测试和 Run 45791388839；明确 PR #32 未合并 | 区分验收完成与集成完成，避免 AC 状态和 PR 状态混淆 | Issue #27；PR #32；Run 45791388839 |
| 2026-11-26 | 0.3.22 | GPT-6.2（ChatGPT） | §1～§3 | 更新 SR-001 最新 HEAD 9d061c0、80 项专项测试和 Run 45793336377 | 回填最终代码块/注释/重复声明反例的验收结果，保持 PR 未合并门禁 | Issue #27；PR #32；Run 45793336377 |
| 2026-11-26 | 0.3.23 | GPT-6.2（ChatGPT） | §1～§3 | 回填 SR-001 VERIFIED，合计 2 VERIFIED/2 READY/23 DRAFT | 与必需 AC 和合并状态一致 | Issue #27；PR #32；PR #36 |
| 2026-11-26 | 0.3.24 | GPT-6.2（ChatGPT） | §3、修订记录 | 消除正文中残留的 1 VERIFIED / 3 READY 旧统计，统一为 2 VERIFIED / 2 READY / 23 DRAFT | 保持头部、列表和统计段落完全一致 | Issue #27；PR #32；PR #36 |
| 2026-11-26 | 0.3.25 | GPT-6.2（ChatGPT） | §1～§3、修订记录 | 在最新 27 项 SR 基线上登记 SR-015 READY，统计更新为 2 VERIFIED / 3 READY / 22 DRAFT；保留 SR-001 VERIFIED、SR-028 DRAFT 和 PR #36 的原有证据 | 解决 PR #37 与并行治理提交的分支冲突，不覆盖已集成的 SR-001/G02 变更 | Issue #12；SR-015；PR #37 |
| 2026-11-26 | 0.3.26 | GPT-6.2（ChatGPT） | §1～§4、修订记录 | 回填 PR #37 MERGED，将 SR-015 标为 IMPLEMENTED；27 项状态为 2 VERIFIED / 2 READY / 1 IMPLEMENTED / 22 DRAFT | 按 SR 状态机区分文档迁移完成与验收 VERIFIED，保留 SR-001、SR-028 并行结果 | Issue #12；SR-015；PR #37 |
| 2026-11-26 | 0.3.27 | GPT-6.2（ChatGPT） | §1～§4 | 回填 ca-agent-demo PR #253 合并、Issue #252 关闭及 AC-024-01～07 PASS；SR-024 转 VERIFIED；同步 SR-003 的设计 READY / 实施 IN_PROGRESS 与本地模块 AC 证据 | 消除 SR-024 已完成仍显示 READY 的过期状态，并区分 SR-003 设计门禁、实施进度与未运行的 CI/系统 EX | Issue #12；ca-agent-demo #252/#253；SR-024 v0.1.12；SR-003；PR #34 |
| 2026-11-26 | 0.3.28 | GPT-6（ChatGPT） | 文档头、§3.2、修订记录 | 保留 SR-024 VERIFIED 与 SR-003 设计 READY / 实施 IN_PROGRESS；回填 PR #34 Merge 候选 Base SHA | 与最新恢复分支一致，不能将历史 AC 结果升级为候选 Head PASS | Issue #28；PR #34 |
| 2026-11-26 | 0.3.29 | GPT-6（ChatGPT） | 文档头、§3、修订记录 | 以新 Head 的 CI success 替换等待验证状态 | 不将模块测试等同系统验收 | Issue #28；PR #34；[CI #45814208662](https://github.com/odango-chan/ca-agent-next/actions/runs/45814208662) |
| 2026-11-26 | 0.3.30 | GPT-6（ChatGPT） | §1～4 | SR-003 IMPLEMENTED，主状态统计更新为 3/2/22 | 满足实现合并后的 SR 状态回填 | Issue #28；PR #34；Merge `32c7c1be` |
| 2026-11-26 | 0.3.31 | GPT-6（ChatGPT） | 文档头、§1～4、修订记录 | SR-003 模块 VERIFIED，27 项统计 4 VERIFIED / 1 IMPLEMENTED / 22 DRAFT；附双平台 CI、merge tree 证据 | 与权威 SR-003/Acceptance 最新状态一致，EX 保持 NOT_RUN | Issue #28；PR #34/#41；CI #45815167442/#45817800342 |
| 2026-11-26 | 0.3.32 | GPT-6.2（ChatGPT） | §3.2、修订记录 | 记录 SR-004 v0.2.0 当前 DRAFT/NOT READY、模块 AC 和 SR-013/SR-027 的实际设计依赖 | 避免将外部发布依赖尚未完成的 Assurance 路径误判为可实施 | Issue #43；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.3.33 | GPT-6.2（ChatGPT） | §3.2、修订记录 | 将 SR-004 引用更新至 v0.2.1，确认新 Runtime Artifact 字段映射仍由 Compiler #61 冻结 | 防止 SR 索引引用过期 SR 版本 | Issue #43；SR-004；SR-013 |
| 2026-11-26 | 0.3.34 | GPT-6.2（ChatGPT） | §3.2、修订记录 | 将 SR-004 引用更新至 v0.2.3，并纳入 Agent Skills Front Matter 契约 | 保持 SR 索引与最新导入设计一致 | Issue #43；SR-004 |
| 2026-11-26 | 0.3.35 | GPT-6.2（ChatGPT） | Phase C、修订记录 | SR-004 指向 v0.2.4，新增 1.6.0/SR-029 Capability Binding 正式发布直接依赖 | 不提前把 Compiler v1alpha5 when 当成 1.6.0 完成；SR 仍 DRAFT | Issue #40/#43；SR-004；SR-029；SR-013 |
| 2026-11-26 | 0.3.36 | GPT-6.2（ChatGPT） | Phase C、修订记录 | SR-004 v0.2.5 明确只接受 CA-SL 1.6.0 新 Artifact，拒绝旧包、兼容、fallback 与迁移 | 保持 1.6.0 单版本验收门禁；SR-004 仍 DRAFT | Issue #40/#43；SR-004；SR-029 |
| 2026-11-26 | 0.3.37 | GPT-6（ChatGPT） | SR 清单、§3.2、§4、修订记录 | 新增 SR-029 设计待评审，28 项 SR 统计更新为 4 VERIFIED / 1 IMPLEMENTED / 23 DRAFT，约束 1.6.0-only 无兼容 | 将设计待评审与实施 READY 分开并追溯 IR-008 / Issue #40 | Issue #40；SR-029；IR-008 |
| 2026-11-26 | 0.3.38 | GPT-6（ChatGPT） | 文档互引与修订记录 | 刷新当前生效版本引用：当前 SR-004 文档版本已刷新为设计待评审，实施仍 DRAFT | 防止待审文档引用旧版本 | Issue #40；SR-029 |
| 2026-11-26 | 0.3.39 | GPT-6（ChatGPT） | Phase C、修订记录 | 将 SR-004 最新待评审版本对齐 v0.2.7；维持 28 项 SR（4 VERIFIED / 1 IMPLEMENTED / 23 DRAFT） | 不把审核状态误认为下游实施 READY | Issue #40/#43；PR #45 |
| 2026-11-26 | 0.3.40 | GPT-6（ChatGPT） | 文档头、设计评审、修订记录 | 为全部 23 项 DRAFT SR 建立独立设计待评审矩阵；实施状态统计仍为 4/1/23 | 明确评审请求与实施 READY 独立，不假设 1.6.0 外部产物已发布 | Issue #12/#40/#43；SR-004～SR-029 |
| 2026-11-26 | 0.3.41 | GPT-6（ChatGPT） | 现行 1.6.0 权威设计与审核追踪 | 与 #46 实质设计整改一致，更新当前版本、Owner 1.6.0 Publisher 和模块 AC 边界 | 消除旧 Development 1.0.0 误导与设计/实施状态混淆 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.3.42 | GPT-6（ChatGPT） | SR 清单、设计待评审矩阵、Publisher 顺序与修订记录 | 将新增 SR-030 纳入唯一 1.6.0 Host Context Schema-only Publisher；把 SR-024 明确标为历史 v1alpha5 Publisher；统计更新为 29 项 SR / 4 VERIFIED / 1 IMPLEMENTED / 24 DRAFT | 避免把旧 Development Publisher 的 VERIFIED 误认为新版 Schema-only Package 已发布 | Issue #12/#40；SR-024、SR-030；PR #46 |
| 2026-11-26 | 0.3.43 | GPT-6（ChatGPT） | §2.1、SR-013/SR-016/SR-030 评审焦点、修订记录 | 将 Schema-only Package / zero Capability roots 的新 AC-013-06 纳入 SR-013 评审焦点，并明确 SR-016 消费与 SR-030 Publisher 的联合验收关系 | 让 24 项 DRAFT 的评审矩阵与 F08/EC02/SR-013/F09/SR-016 的最新闭环一致 | Issue #12/#40；SR-013、SR-016、SR-030；PR #46 |
| 2026-11-26 | 0.3.44 | Codex / GPT-6 | 当前设计入口与修订记录 | 对齐本轮 Importer、Compiler 或 Publisher 的阶段门槛与引用版本 | 供评审者按同一提交核对生产和消费证据 | Issue #12/#40/#43，PR #46 |
| 2026-11-27 | 0.3.45 | Codex / GPT-6 | 24 项设计评审表 | 逐 SR 回填固定提交的独立结论与复评范围 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.46 | Codex / GPT-6 | §2.1、3.1 | 逐项登记第二轮独立评审范围与修订门槛 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.47 | GPT-6（ChatGPT） | §2.1、§3.2、修订记录 | 记录 SR-009 AC-009-04 completion 增量复评与模块/系统实施顺序 | 不把第二轮认可范围擅自扩展或把 Echo E2E 误作插件模块启动条件 | Issue #12；PR #46；SR-009 |
| 2026-11-27 | 0.3.48 | GPT-6（ChatGPT） | §2.1～2.2、修订记录 | 十项第二轮需修订的设计登记第三轮自评候选，十二项限定认可保留，SR-026/027 精确列缺件；主状态 24 DRAFT 不变 | 为外部独立评审形成逐项可复核入口，禁止把作者自评误作实施 READY | Issue #12；PR #46；SR-004～030 |
| 2026-11-27 | 0.3.49 | GPT-6（ChatGPT） | §2.1～2.2、修订记录 | 调整第三轮自评段落与原有规范性来源警示的阅读顺序，改用稳定文件路径 | 避免拆断规范性段落或误导评审者访问未经核实的自动生成锚点 | Issue #12；PR #46 |
| 2026-11-27 | 0.3.50 | ChatGPT / GPT-6；GPT-6（ChatGPT） | §2～4、修订记录；文档头、§1、修订记录 | 新增 IR-009/SR-031，登记原 24 项评审批次之外的 3GPP 公共 Schema 发布与 T1/T2 Codec 消费分期，统计为 30 项；同步 SR 管理规范 v0.8.0 的 GitHub 正式评审留存要求；明确 PR #46 第三轮独立评审尚未留存、READY=0 | 保留历史评审结论边界，不把新增类型契约冒充 READY；防止仅凭作者自评或聊天结论推进 SR 状态 | Issue #47；SR-031；SR-026/010/013/027；Issue #12；PR #46 |
| 2026-11-27 | 0.3.51 | ChatGPT / GPT-6；GPT-6（ChatGPT） | IR-009 标准代发布原则；文档头、§1、修订记录 | 只随 OpenAMSM 采用版本发布原件，YAML 不做任何修改，独立 Adapter 与 Codec Output 分界；同步独立评审模型身份规则：允许同一 GitHub 账号由不同模型承担独立评审，区分模型结论与 GitHub Review event | 落实最新版本/原版无变更裁决并修正导航；与 SR 管理规范 v0.8.1 一致，避免账号身份误判评审独立性 | Issue #47；SR-031；Issue #12；PR #46 |
| 2026-11-27 | 0.3.52 | ChatGPT / GPT-6.2；GPT-6（ChatGPT） | IR-009 / SR-031；文档头、§2.1～2.2、修订记录 | 将 SR-031 从 Schema-only / Adapter Publisher 修正为原版 OAS3 Source Bundle Publisher；同步 Compiler direct refs 与 Plugin native OAS3 consumer；回填独立模型 Review #6082541121 的固定 Head/Base、19/3/2 结论和 29 条 inline 留痕；明确第二轮原始 Review 证据不可访问；将自评矩阵替换为真实独立评审结果 | 统一原始标准直接消费路径；处理 R3-GOV-01，避免将仓内登记或作者自评冒充正式独立审批，并确保新 Head 不继承旧 Review 结论 | Issue #47；SR-031/010/013/026/027；Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.3.53 | GPT-6.2（ChatGPT）；ChatGPT / GPT-6.2 | 文档头、§2.1、§2.2、§3.2、修订记录；SR-031 / IR-009；SR 清单、IR-008 增量设计、修订记录 | 记录 SR-028 专项独立 Review #6082874849 的固定 Head/Base 与 CHANGES_REQUESTED 结论，覆盖旧 Head 限定认可；同步 Issue #12 整改状态；固定 PostSmContexts requestBody 四文件 / 102 Component 选定闭包、lazy refs、Content-ID slot mapping 与 Source Root 相对引用边界；同步实施阻塞；新增 SR-032 与 SKILL 作者规范，更新至 31 项 SR / 26 项 DRAFT | 防止 SR-028 继续沿用已被新专项复评推翻的旧 Head 结论，保持 READY=0；让 SR 索引、独立评审范围与权威设计一致；将作者规则从历史资料提升为 Next 唯一中央规范入口，且不改变 PR #46 / Issue #47 历史评议 | Issue #12；PR #46；Review #6082874849；SR-028 v0.2.6；Issue #47；SR-031/010/013/026/027；EC01/EC02；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.54 | GPT-6.2（ChatGPT） | 文档头、§2.1.1、§2.2、§3.2、修订记录；§3、修订记录 | 回填 SR-028 第四轮独立 Review #6083225844 的固定 Head/Base、0 P0/4 P1/3 P2、AC 设计结论与产品 NOT_RUN；记录第四轮整改已推送并等待新 Head 复评；清除 §3 中残留的 30 项 / 25 DRAFT 旧统计，统一当前 SR 状态 | 不沿用已被第四轮复评覆盖的旧 7 P1/2 P2 结论，不提前提升 READY；避免摘要与清单、实施状态总览不一致 | Issue #12；PR #46；Review #6083225844；G02 v0.2.5；SR-028 v0.2.7；Issue #49；SR-032 |
| 2026-11-27 | 0.3.55 | GPT-6.2（ChatGPT） | 文档头、§2.1.1、§2.2、§3.2、修订记录；SR-032 清单 | 回填 SR-028 第五轮独立 Review #6083641266 的固定 Head/Base、0 P0/1 P1/3 P2 与 R028-17～20；记录第五轮整改已推送的 G02 v0.2.6 / SR-028 v0.2.8 版本与第六轮复评门槛，READY=0、产品 AC NOT_RUN 不变；更新 SR-032 对共享 Package 资源、Script Registry 和 Host Script Execution 的描述 | 防止 SR 索引沿用第四轮问题统计或将本轮文档整改误认为产品实施/READY；使索引与最新 SR-032 / CA-SL 1.6.0 设计一致 | Issue #12；PR #46；Review #6083641266；G02 v0.2.6；SR-028 v0.2.8；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.56 | Codex / GPT-6；GPT-6.2（ChatGPT） | §2.3；Phase C | 归档 23 项评审和两项整改的复评范围；将 SKILL.md-only 子路径更正为可携带共享资源的无 Assurance Package 子路径 | 区分原评审结论、设计修订与实施状态；保持 SR-004 实施阶段导航与 Package 根目录结构一致 | Issue #12、#71、#90；PR #46；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.57 | Codex / GPT-6；GPT-6.2（ChatGPT） | 分阶段门槛与追踪；SR-032 清单 | 登记 21 项下一阶段与直接依赖；更新 SR-032 的脚本执行原则为 LLM / Procedure / Predicate 共用同一 Script Runner | 依独立评审启动限定范围；使治理索引反映移除逐脚本与 Host LLM 双门禁后的最新设计 | Issue #12；PR #46；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.58 | GPT-6.2（ChatGPT） | 文档头、§2.1.1、§2.2、SR-028 状态行、修订记录；SR-004、SR-007、SR-016、SR-032 清单 | 回填第六轮 Review #6083872622 固定 Head/Base 与 0 P0/1 P1/2 P2；登记 R028-21～23 及方案 B 整改；同步 G02 v0.2.7、SR-028 v0.2.9 与第七轮复评门槛；将 SR-004 子路径改为无 Assurance Package；同步 SR-007 Host Resource Read / Script Runner、SR-016 作者规范 Change Set、SR-032 无 Wait / 原有语法 / Script 契约验收 | 保留前五轮历史结论并明确当前唯一阻断项；不将文档整改误报为 READY 或产品验收；让 SR 索引与 Issue #49 修订后的实施边界一致 | Issue #12；PR #46；Review #6083872622；G02 v0.2.7；SR-028 v0.2.9；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.59 | GPT-6.2（ChatGPT） | PR #46 / PR #48 集成刷新 | 合并 PR #46 的 23 项独立评审追踪与 SR-031 / IR-009 新增条目、状态及实施阻塞；保持 30 项 SR、4 VERIFIED、1 IMPLEMENTED、25 DRAFT | 避免 3GPP 增量覆盖既有 SR 评审状态，统一总索引与跨仓设计审计 | Issue #47/#12；PR #46/#48；SR-031；IR-009 |
| 2026-11-27 | 0.3.60 | GPT-6.2（ChatGPT） | SR-031/032、PR #46 评审追踪、修订记录 | 合并 PR #46 23 项独立设计评审追踪与 SR-031 / SR-032 两项独立增量设计；统一为 31 项 SR、4 VERIFIED、1 IMPLEMENTED、26 DRAFT | 防止 PR #48 的 IR-009 与 PR #52 的 IR-008 相互覆盖，保留各自产品 NOT_RUN / BLOCKED 边界 | Issue #47/#49/#12；PR #46/#48/#52；IR-008/009；SR-031/032 |
| 2026-11-27 | 0.3.61 | GPT-6.2（ChatGPT） | §2.1.1、§2.2、§3.2、修订记录 | 回填 SR-028 第七轮 Review #6084094037 APPROVE_FOR_READY、P2-1/2 关闭、PR #97 READY 回填与 PR #99 实施进度；补入 AC-028-04/05 脚本级证据补充及独立复核待完成状态，修正实施门槛与 SR-028 最新状态入口 | 避免继续引用第六轮 CHANGES_REQUESTED / 全部 NOT_RUN 作为最新结论，也不将 OPEN PR 或未复核证据误报为 VERIFIED | Issue #96；PR #46/#97/#99；Review #6084094037/#6085168356；Issue comments #7212463039/#7213406863/#7213473388 |