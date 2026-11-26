# SR 总索引

> 文档类型：软件需求索引  
> 文档版本：0.3.33
> 状态：27 项 SR：SR-001/SR-002/SR-003/SR-024 VERIFIED；SR-015 IMPLEMENTED；22 项 DRAFT；SR-003 模块 AC 全部 PASS，系统 EX NOT_RUN
> 修订日期：2026-11-26  
> 权威规则：[SR 管理规范](../规范/SR%20管理规范.md)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  

跨仓任务从 Next 发起。先在本仓登记覆盖目标仓和修改范围的 SR，达到 READY 后再切换到目标仓实施，目标仓结果回填本仓 SR。既有外部 Issue 可作为关联入口。详见《SR 管理规范》§8.1。

## 1. 使用规则

- 每项 SR 的完整范围和验收条件以对应 SR 文件为准。
- 本索引只汇总 ID、标题、设计依据、状态、依赖和实施入口。
- 状态变化先更新 SR 文件，再更新本索引和[实施状态总览](实施状态总览.md)。
- ca-agent-next PR #1 是文档/设计基线 PR，不是任何 SR 的实现 PR。
- PR #1、#32、#34 已合并；SR-001/SR-002/SR-003/SR-024 VERIFIED，SR-015 IMPLEMENTED，其余 22 项 DRAFT。

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
| [SR-024](../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Host Context Interface Package Publisher | VERIFIED |
| [SR-025](../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | MAS Owner Development Interface Package Publisher | DRAFT |
| [SR-026](../SR/SR-026-Codec公开工具发布.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Codec 公开工具发布 | DRAFT |
| [SR-027](../SR/SR-027-技能Bundle构建与发布.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 技能 Bundle 构建与发布 | DRAFT |
| [SR-028](../SR/SR-028-Python工程工具链与uv环境管理.md) | [IR-007](../IR/IR%20总登记册.md#ir-007) | Python 工程工具链与 uv 环境管理 | DRAFT |

设计版本与章节、依赖、验收 ID、实施证据以各 SR 为准。逐项阻塞见[就绪审计](../参考与审计/跨仓设计资产迁移与一致性审计.md#8-设计就绪审计)。

## 3. 设计恢复与实施顺序

### 3.1 中央设计恢复批次（按各 SR 状态与依赖门禁执行）

| 顺序 | SR | 主要功能 | 目标仓 / 参考仓 | 依赖和产出 |
|---|---|---|---|---|
| 1 | SR-023 | CA-SL v1alpha5、作者源与发布基线恢复 | ca-skills | 先固定语言、Skill 作者源与版本边界；Compiler #61 仍是外部 OPEN 依赖 |
| 2 | SR-015 | Tool Interface / Provider / Codec 设计恢复 | ca-client-tools → Next F03.05 | IMPLEMENTED；F03.05 v0.3.9、SR-015 v0.3.8；PR #37 MERGED，产品代码未实现 |
| 3 | SR-025 | MAS Owner Development Interface Package Publisher | ca-client-tools → Next F03.05 / F09 | 将 Owner v1alpha4 source 包装为 Compiler v2.1.0 Development Interface Package；package.version 固定为 `1.0.0` |
| 4 | SR-024 | Host Context Interface Package Publisher | ca-agent-demo → Next F09 | VERIFIED；[Issue #252](https://github.com/odango-chan/ca-agent-demo/issues/252) 已关闭；[PR #253](https://github.com/odango-chan/ca-agent-demo/pull/253) 已合并，merge `25168db031e996bfa4de440c4156ae94f4e19bce`；AC-024-01～07 均 PASS。Review COMMENTED、4 个 PR checks SKIPPED 如实保留；不占用 SR-020 的参考宿主审计 ID |
| 5 | SR-018 | OpenAMSM Owner 权威状态恢复 | env-openamsm | 固定 Callable、Receipt、Commit Proof、Reconcile 和 Modify/Release 边界 |
| 6 | SR-019 | Mock AMF / 5GC 仿真对端恢复 | env-5gc-sim | 固定协议对端、World、进程和真实测试边界 |
| 7 | SR-017 | OpenAMSM Event/Delivery Plugin 恢复 | ca-openamsm-plugin | 依赖 F03/F05、EC05 Owner Contract；当前 PR #1 Draft |
| 8 | SR-020 | Python Generic Host 参考实现审计 | ca-agent-demo | 为 F01/F03/F04/F05 提供可复用代码证据；不复制业务专用架构 |
| 9 | SR-022 | ca-runtime 执行内核设计审计 | ca-runtime | 与 F04 对照，区分采用、简化和排除的机制 |
| 10 | SR-016 | Skill Studio / AI Authoring 设计恢复 | ca-skill-studio-demo | 与 CA-SL、F08/F09 对齐；PR #258 已合并，部署状态独立验证 |
| 11 | SR-021 | Go Native Host 晋级目标审计 | ca-agent | 最后对照，不能改变 Next 当前 Python Host 决策 |

以上顺序是文档依赖和设计评审顺序，不是实施授权。每份 SR 必须完成设计章节、目标仓/固定 SHA、代码/测试差异、验收命令和非目标边界；评审通过后才可进入 READY。

### 3.2 Next 实施阶段

- 治理自动化：SR-001 VERIFIED；[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) MERGED（`7a0fac41e573021207ab8201bbc718718c451e50`）；AC-REV-01～10 PASS、80 tests OK、Run [45793590532](https://github.com/odango-chan/ca-agent-next/actions/runs/45793590532) success；SR-028 仍为 DRAFT。
- Phase A：SR-002（VERIFIED；PR #23 已集成；AC-002-01～08 PASS；EX-01 仍 NOT_RUN）。
- Phase B：**SR-003 VERIFIED（模块）**；[实施 PR #34](https://github.com/odango-chan/ca-agent-next/pull/34) 与 [治理回填 PR #41](https://github.com/odango-chan/ca-agent-next/pull/41) 均 MERGED。最终实施 Head `e8bcb1b` 与 Merge `32c7c1be` tree 一致；治理回填 Head `f3f59b54` 与 Merge `a899409` tree 一致。[CI #45815167442](https://github.com/odango-chan/ca-agent-next/actions/runs/45815167442)、[CI #45817800342](https://github.com/odango-chan/ca-agent-next/actions/runs/45817800342) 均 SUCCESS：Linux Python 3.12 + Windows Python 3.14 每平台 Plugin 87 / Host 52 / Review Context 80 tests PASS，Go Echo build、compileall 与证据采集 PASS；AC-003-01～04 均 PASS。系统 EX-02/03/04/18 仍 NOT_RUN；Provider v2 wire DTO 属 SR-010，不影响 SR-003 模块结论。
- Phase C：SR-004 DRAFT / NOT READY；[设计 Issue #43](https://github.com/odango-chan/ca-agent-next/issues/43) OPEN，SR-004 v0.2.1 已定义 AC-004-01～06。SKILL.md-only 子路径可独立设计；Assurance 路径等待 Compiler #61 / SR-013 新 Runtime Artifact API 与 ca-skills SR-027 正式 Bundle 契约/正例。冻结 Artifact v1alpha5 与 Development v1alpha1 均不作为当前正例；未达到 READY，不创建实施 Issue、不提供 Harness 提示词。
- Phase D：SR-005、SR-006。
- Phase E：SR-007。
- Phase F：SR-008。
- Phase G：SR-009、SR-010。
- Phase H：SR-011。
- Compiler 外部发布依赖：SR-012、SR-013；SR-013 的 [PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN，不代表 Compiler 产品发布或完整 SR VERIFIED。

阶段顺序仅约束实际实施依赖，不限制独立设计评审。每个 SR 达到 READY 后，只有当前实施阶段的直接实施依赖满足才可启动；未满足的依赖只阻塞其消费者，不得阻塞独立 SR/AC。Goal 模式可将同一依赖批次中的多个 READY SR 合并执行，但不得跨越未满足的实施依赖或把 DRAFT SR 当成可执行任务。

## 4. 当前基线说明
- SR-002 设计 PR [#20](https://github.com/odango-chan/ca-agent-next/pull/20) 已 MERGED（`281ccb957b9222e72175e210d1afed177aa8a14f`）；实施 PR [#23](https://github.com/odango-chan/ca-agent-next/pull/23) 已 MERGED（`49964464e19d13d219ea0b3513d2223fe81d2435`）；设计 Issue #19 与治理 Issue #21 已关闭。SR-002 为 VERIFIED，AC-002-01～08 PASS；EX-01、CPython 3.11/3.12/3.13 矩阵及 DeepSeek Harness 仍 NOT_RUN。实施 Issue [#22](https://github.com/odango-chan/ca-agent-next/issues/22) 由本次证据回填 PR #25 合并关闭。

- 设计来源：ca-agent-next PR #1 的架构、设计、规范和 Acceptance 文档。
- PR #1：已合并；只代表设计文档变更。
- Next Runtime：README 声明尚无已验收 Runtime 实现。
- 当前 27 项 SR 中 4 VERIFIED（SR-001/002/003/024）、1 IMPLEMENTED（SR-015）、22 DRAFT；SR-013 归档 PoC 不改变 DRAFT；SR-009 只覆盖 Event/Delivery Plugin/staging，SR-010 覆盖 Host ArtifactStore、Channel、Provider v2 Driver/Codec。
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
| 2026-11-25 | 0.2.6 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex 登记 Compiler 实施 SR | 对齐跨仓实施门槛 | SR-013 |
| 2026-11-25 | 0.2.6 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex / GPT-6 · §1–4 · 登记分仓 SR 与真实基线状态 | 跨仓设计移交 | IR-006 |
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
