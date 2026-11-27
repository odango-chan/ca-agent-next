# SR-027：技能Bundle构建与发布

> 文档类型：软件需求（SR）  
> SR 版本：0.1.12\
> 状态：**DRAFT（设计待评审）**；CA-SL 1.6.0-only、完全不兼容旧版；**代码实施/发布 NOT_READY**，模块验收 NOT_RUN
> 创建日期：2026-11-26  
> 上游需求：IR-006  
> 设计依据：F08 v0.3.18 §4、§6；CA-SL 1.6.0 目标（Issue #40 / SR-029）。\
> 关联 Issue：ca-agent-next#12（设计）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §4；本批限外部构建与发布。

## 1. 目标与前置

目标仓 ca-skills，功能 F08 / EC01，中央依据为 [F08 发布设计 §4](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md#4-ca-skills-ci-编译与-bundle-组装)。基线 `780497a2918ad3e7bdff554ab64b0ba627e867e0`。SR-023 的历史 v1alpha5 作者规范保留追溯；**新 Bundle 面向 CA-SL 1.6.0**，SR-029 + ca-skills 发布 Capability-first 作者规范，SR-013 / Compiler #61 联合交付 when + 唯一 Capability Binding 的新版 Compiler Release，SR-004 与 SR-008 消费发布物。固定作者 SHA、Compiler 发布 tag 与可执行文件、适用的 Runtime Artifact API。某一 Skill 需要下一版 Artifact 时单列等待。

## 2. 在源仓交付

历史 `scripts/compile_mas_v1alpha5.py`、`tests/test_compile_mas_v1alpha5.py` 及原有 CI **仅作为留档审计线索，不作为 1.6.0 新实现或验收入口**。新 Bundle 构建与测试必须基于 ca-skills 正式发布的 **1.6.0 作者语法**、SR-029 的 Capability→Callable Binding 和 Compiler 新版契约，从头定义单版本流程；不保留调用旧编译脚本的兼容分支。为本批指定的 Echo 作者源、MAS 作者源分别建立构建输入清单。Echo 在该基线缺失，准备 SR-008 所用的指导包和带 Assurance 的 Echo，登记路径、Capability、请求/响应样例及预期。MAS 业务样例选 `examples/skills/{establish,modify,release}-pdu-session-mas`，逐个给出依赖和 Verify 日志。**这些当前路径对应历史 v1alpha5 作者源，只作为业务语义与迁写参考；实际进入 1.6.0 Build 的必须是作者按 SR-029 人工重新编写、固定 revision 并经 1.6.0 Compiler Check/Build/Verify 的新源，禁止直接编译当前历史文件。**

CI 对同一批次一次解析并固定 Compiler 发行版，逐包构建与验证成功后组装发布目录。指导包只含作者入口及声明的资源；确定性包随附已验证的 Runtime Artifact。输出记录作者 revision、Compiler 实际版本、API、资产路径、各包结果。发布前在临时目录验证，失败不上传部分批次；由授权的发布步骤消费同一份候选。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-027-01 | ca-skills 仓根使用新建的 **1.6.0 专用测试入口**（命令、文件名与测试数在新实现 Issue 固定），检验新版 Compiler Check/Build/Verify、Bundle 成功与错误拒绝；可继续运行文档检查，但 **v1alpha5 测试不得作为本 AC 的 PASS 证据**；记录命令、受测 SHA、发现数和日志 |
| AC-027-02 | CI 在干净 checkout 生成候选。逐项查 SKILL.md、所声明的资源及可选 Assurance 对应产物；损坏 Artifact 使当批发布数为零。Development Artifact 不进入 Runtime Bundle |
| AC-027-03 | 使用同一候选在 Next 执行 SR-004 导入与 SR-008 Echo；原始作者 checkout 和 Compiler 从 Host 运行环境移除后依然可运行。分别记录构建、发布及消费状态 |

## 4. 状态与非目标

中央设计 Issue #12；ca-skills 实施 Issue、实施 PR、构建证据和正式发行资产尚未登记。READY 前固定首批作者源、Bundle 的具体文件清单、可用 Compiler 版本与匹配 Verify 命令；候选构建和正式发布分别登记。状态 DRAFT，测试 NOT_RUN。Next 不编译，Compiler 不负责组装 Bundle。无替代 SR。

## 5. 当前外部输入与发布证据核对（2026-11-26）

| 输入 | 当前可核对事实 | 对本 SR 的结论 |
|---|---|---|
| CA-SL v1alpha5 | ca-skills PR #88 MERGED；normative SHA `18d8184367982ccbc835756136c4a53f9096c3a0`；PR #89 将该 SHA 固定在 release record | 语言规范依赖已满足；不是 Skill Bundle |
| Compiler v2.1.0 | [正式 Release](https://github.com/odango-chan/ca-skill-compiler/releases/tag/v2.1.0)；冻结 Artifact v1alpha5 和 Development Artifact v1alpha1；旧 Artifact 字节/语义不变 | 不能满足 F08 新 Runtime Artifact API 的 Request Schema/when 输出 |
| Compiler when Artifact | [Compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) OPEN；SR-013 AC-013-02～04 未完成，AC-013-05 BLOCKED | 新 Runtime Artifact API 尚未发布；本 SR 不得选择或猜测候选 API/Manifest 字段 |
| ca-skills 作者源 | main `780497a2918ad3e7bdff554ab64b0ba627e867e0` 含 v1alpha5 MAS 作者源；`scripts/compile_mas_v1alpha5.py` 只对单 Skill 做 Check/Inspect/可选 Build | 现有脚本不是 Bundle assembler，也不证明正式 Bundle 已发布 |
| ca-skills Release | 当前 Release 列表只有历史 v0.1.0；未发现与 **CA-SL 1.6.0** Runtime Artifact API 匹配的 Published Skill Bundle | 无可供 SR-004 使用的正式 Assurance 正例 |
| ca-skills 仓库布局 | 当前 main 未发现 `published-skills/` / 新 Runtime Artifact Bundle 发布目录 | Bundle layout / Skill 与 Artifact 关联契约仍须由本 SR 和 F08 明确的生产端 SR 冻结 |

**阶段结论：** 本 SR 仍为 DRAFT。下一发布链只面向 **CA-SL 1.6.0**；先等 ca-skills / SR-029 规范及精确机器标识、Compiler #61 / SR-013 对 1.6.0 语言及 Capability Binding 冻结新 Runtime API，再组装 Bundle；不得猜测 Manifest，不得把本地旧 v1alpha5 编译目录或临时拼装包当作 AC-027-02/03 正例。SR-004 的 SKILL.md-only 路径可独立验证，但不提升 SR-027 或 Assurance Bundle 的状态。

## 6. 修订记录


| 日期 | 版本 | 修订者/模型 | 章节 | 内容 | 关联 |
|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | Codex / GPT-6 | 见本行变更 | 首次登记两端交付、独立复验与就绪条件 | Issue #12 |
| 2026-11-26 | 0.1.1 | Codex / GPT-6 | 见本行变更 | 补齐正式文档的评审范围与非目标；列明依赖设计版本；同步设计依据到本次复审的修订版本 | Issue #12 |
| 2026-11-26 | 0.1.2 | GPT-6.2（ChatGPT） | 文档头、§4～6、修订记录 | 记录 CA-SL v1alpha5 固定源、Compiler v2.1.0 冻结 Artifact、Issue #61 未完成及 ca-skills 当前无正式 Bundle；防止将规范/Compiler Release/本地 Build 误报为 Published Skill Bundle，并为 SR-004 明确外部依赖 | Issue #43；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.1.3 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 将 F08 设计依据更新至 v0.3.8，保持 SR-027 与发布端权威设计版本一致 | Issue #43；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.1.4 | GPT-6.2（ChatGPT） | 文档头、§1、§5、修订记录 | 将后续 Skill Bundle 生产目标更新为 CA-SL 1.6.0，增加 SR-029 Capability Binding 与 Compiler #61 联合 Release 门槛；避免继续发布 v1alpha6 候选或旧 v1alpha5 作者源作为最新运行包 | Issue #40/#43；SR-029；SR-013；SR-027 |
| 2026-11-26 | 0.1.5 | GPT-6.2（ChatGPT） | §2～3、修订记录 | 将旧 v1alpha5 构建脚本与测试从新版验收入口移除，仅保留历史审计；1.6.0 Bundle 必须原生编译/验证；严格无兼容、无旧构建管线的 1.6.0 单版本发布 | Issue #40/#43；SR-029；SR-027 |
| 2026-11-27 | 0.1.6 | Codex | 设计依据 | 关联 F08 整合版本，正式 Bundle 仍待交付 | Issue #40、#43；PR #44 |

| 2026-11-27 | 0.1.7 | GPT-6.2（ChatGPT） | §2、设计依据、修订记录 | 明确历史 v1alpha5 MAS 路径仅作迁写参考；1.6.0 Build 必须使用人工重写并通过新版 Compiler 验证的作者源；同步 F08 最新版本 | Issue #40/#43；SR-029；PR #44/#45 |
| 2026-11-27 | 0.1.8 | GPT-6.2（ChatGPT） | 文档头、设计依据、§2、修订记录 | 同步 1.6.0-only Compiler/Authoring 设计修订后的当前版本引用，保留 28 SR / 8 IR 状态与未发布门槛。 | Issue #12/#40/#43；SR-004/013/027/029；PR #45 |
| 2026-11-27 | 0.1.9 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 Compiler 1.6.0-only 新契约的 M.3 / Request Schema Owner Gate 与跨文档当前版本引用；旧 v1alpha5 仅保留历史冻结语义。 | Issue #40；SR-004/013/027/029；EC02；F08；PR #45 |
| 2026-11-27 | 0.1.10 | GPT-6.2（ChatGPT） | 设计依据、修订记录 | 与 EC02 v0.2.12、F08 v0.3.16 和 1.6.0-only 候选设计保持一致；未授予产品实施 READY | Issue #40/#43；PR #45；SR-013/SR-029 |
| 2026-11-27 | 0.1.11 | GPT-6.2（ChatGPT） | 文档头设计依据、修订记录 | 将当前 Bundle 设计依据更新至 F08 v0.3.17 | Issue #40；PR #45；SR-004/013/027；SR-031/PR #48 |
| 2026-11-27 | 0.1.12 | GPT-6.2（ChatGPT） | 文档头设计依据、修订记录 | 将 Bundle 设计依据更新至 F08 v0.3.18 | Issue #40；PR #45；SR-027 |
