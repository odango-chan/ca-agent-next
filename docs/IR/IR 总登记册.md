# IR 总登记册

> 文档类型：需求项（IR）权威记录  
> 文档版本：0.1.22  
> 修订日期：2026-11-26  
> 状态：7 项 IR；IR-007 登记 Python 工程工具链统一需求，SR-028 为 DRAFT。  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级需求管理平台

IR 编号稳定。GitHub Issue 用于讨论、分派和跟踪，一个 IR 可关联零个或多个 Issue，也可分解为多个 SR。实现和验收证据从 SR 回查。

## IR-001

**可复现的评审上下文**

评审者需要从实际 PR HEAD 获得一致的范围与任务证据。

- 协作 Issue：[Issue #35](https://github.com/odango-chan/ca-agent-next/issues/35)（G01 §11.8 状态刷新；SR-001 代码修复仍由 Issue #27 跟踪）。
- 实施分解：[SR-001](../SR/SR-001-评审上下文自动生成.md)。
- 架构、设计和规范：[文档编写与治理规范](../规范/文档编写与治理规范.md)、[Agent](../../Agent.md)。
- 完成依据：已满足。SR-001 v0.3.10 VERIFIED；[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) MERGED（`7a0fac41e573021207ab8201bbc718718c451e50`），AC-REV-01～10 PASS；最终代码 HEAD `9d061c0c06d5d2ebba4be3cde9143ec6db413a3e` 的 Workflow [45793590532](https://github.com/odango-chan/ca-agent-next/actions/runs/45793590532) success、80 项测试通过、三文件 Artifact 已核对。权威状态回填随 PR #36 集成，Issue #27 在回填合并后关闭。

## IR-002
- 设计修订追踪：[Next Issue #19](https://github.com/odango-chan/ca-agent-next/issues/19)（CLOSED）；[设计 PR #20](https://github.com/odango-chan/ca-agent-next/pull/20)（MERGED，commit `281ccb957b9222e72175e210d1afed177aa8a14f`）；阶段门禁治理：[Issue #21](https://github.com/odango-chan/ca-agent-next/issues/21)（CLOSED）；父级中央设计恢复见 [Next Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)。

**通用宿主与可插拔扩展**

业务通过 Plugin 扩展，宿主保持 Python 和业务中立。

- 实施协作 Issue：[SR-002 实施 Issue #22](https://github.com/odango-chan/ca-agent-next/issues/22)（实施 PR #23 已 MERGED；证据回填 PR #25 负责关闭该 Issue）；[PR #23](https://github.com/odango-chan/ca-agent-next/pull/23) merge commit `49964464e19d13d219ea0b3513d2223fe81d2435`。SR-002 已 VERIFIED，AC-002-01～08 PASS；Issue #19 仅用于设计修订，Issue #21 仅用于治理修订。
- 实施分解：[SR-002](../SR/SR-002-Python%20核心与宿主基础骨架.md)、[SR-003](../SR/SR-003-统一插件管理器与扩展通信.md)。
- 架构、设计和规范：[CA Agent Next 架构设计](../架构设计/CA%20Agent%20Next%20架构设计.md)、[通用Agent核心与Host设计说明书](../设计说明书/F01-通用Agent核心与Host/通用Agent核心与Host设计说明书.md)、[Plugin平台设计说明书](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md)、[插件包与进程通信协议规范](../规范/插件包与进程通信协议规范.md)。
- 完成依据：SR-002 已 VERIFIED，AC-002-01～08 PASS；SR-003 设计 READY，实施 IN_PROGRESS（PR #34 OPEN），AC-003-01～04 在受测 SHA `504ec1b0a35fc761eba621149a94c83d1012626f` 本地 PASS，但尚未合入恢复分支；GitHub CI 与 EX-02/03/04/18 仍 NOT_RUN。因此 IR-002 尚未整体完成。

## IR-003

**已发布技能消费与选择**

使用发布产物导入、选择及续跑，保留跨语言语义与代际一致性。

- 协作 Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)（EC02 外部实现）；[Next #14](https://github.com/odango-chan/ca-agent-next/issues/14) 跟踪中央设计文档刷新；[PR #16](https://github.com/odango-chan/ca-agent-next/pull/16) 为对应 Draft 文档评审，不代表实施。
- 实施分解：[SR-004](../SR/SR-004-已发布技能包导入.md)、[SR-005](../SR/SR-005-技能目录与条件程序消费.md)、[SR-006](../SR/SR-006-技能解析器与续跑选择.md)。
- 架构、设计和规范：[Skill管理与选择设计说明书](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md)、[技能与确定性保障格式规范](../规范/技能与确定性保障格式规范.md)、[Runtime执行设计说明书](../设计说明书/F04-Runtime执行/Runtime执行设计说明书.md)。
- 完成依据：对应 SR 的必需验收全部 VERIFIED；当前均为 DRAFT，证据未执行。

## IR-004

**统一执行与首个垂直验收**

两种执行模式共享约束，通过 Echo 验证从事件到交付。

- 协作 Issue：未登记。
- 实施分解：[SR-007](../SR/SR-007-统一运行时动作边界与双执行模式.md)、[SR-008](../SR/SR-008-Echo%20垂直端到端示例.md)。
- 架构、设计和规范：[Runtime执行设计说明书](../设计说明书/F04-Runtime执行/Runtime执行设计说明书.md)、[公共契约与所有权规范](../规范/公共契约与所有权规范.md)、[演示验收基线](../验收与实施/演示验收基线.md)、[实施路线与阶段门槛](../验收与实施/实施路线与阶段门槛.md)。
- 完成依据：对应 SR 的必需验收全部 VERIFIED；当前均为 DRAFT，证据未执行。

## IR-005

**真实 OpenAMSM 业务接入**

隔离环境完成创建、修改、释放，二进制交接与 Owner 证据可追溯。

- 协作 Issue：未登记。
- 实施分解：[SR-009](../SR/SR-009-OpenAMSM%20SBI%20事件插件与二进制产物交接.md)、[SR-010](../SR/SR-010-OpenAMSM%20工具插件与按需编解码集成.md)、[SR-011](../SR/SR-011-真实%20OpenAMSM%20创建修改释放端到端验证.md)。
- 架构、设计和规范：[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md)、[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md)、[插件包与进程通信协议规范](../规范/插件包与进程通信协议规范.md)、[Plugin平台设计说明书](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md)、[公共契约与所有权规范](../规范/公共契约与所有权规范.md)、[演示验收基线](../验收与实施/演示验收基线.md)。
- 完成依据：对应 SR 的必需验收全部 VERIFIED；当前均为 DRAFT，证据未执行。

## IR-006

**Compiler 设计归档与跨仓收敛**

集中维护 Compiler 机制与冻结决策，使 Harness 能依据已验证的依赖和验收门槛交接。

- 协作 Issue：[Next #2](https://github.com/odango-chan/ca-agent-next/issues/2)、[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)（独立实现依赖）。
- 实施分解：[SR-012](../SR/SR-012-Compiler设计归档与跨仓收敛.md)。设计：[EC02 Compiler 设计](../设计说明书/EC02-Compiler/Compiler设计说明书.md)。
- 完成依据：AC-012-01～03。跨仓清理待 READY。

Compiler 实施沿用 [SR-013](../SR/SR-013-Compiler已检查when与发布产物.md)，其发布证据供 SR-004/005 消费。

**项目群设计移交扩展**

以 Next 作为唯一设计中心。分仓移交现行与历史基线并补齐 Contract.when 链路，Next 消费验收沿用 IR-003。

- 协作入口：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88)、[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。
- 实施分解：[SR-023](../SR/SR-023-技能作者源与语言规范移交.md)、[SR-015](../SR/SR-015-工具契约设计移交.md)、[SR-016](../SR/SR-016-工作台设计移交与条件编辑.md)、[SR-017](../SR/SR-017-业务插件设计移交.md)、[SR-018](../SR/SR-018-业务所有者设计移交.md)、[SR-019](../SR/SR-019-仿真对端设计移交.md)、[SR-020](../SR/SR-020-参考宿主设计移交.md)、[SR-021](../SR/SR-021-原生宿主设计移交.md)、[SR-022](../SR/SR-022-执行内核设计移交.md)、[SR-024](../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md)、[SR-025](../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md)、[SR-026](../SR/SR-026-Codec公开工具发布.md)、[SR-027](../SR/SR-027-技能Bundle构建与发布.md)。
- 设计与验收：[跨仓设计资产迁移与一致性审计](../参考与审计/跨仓设计资产迁移与一致性审计.md)，逐仓检查文档迁移和行为符合性。
- SR-024 完成依据：[ca-agent-demo PR #253](https://github.com/odango-chan/ca-agent-demo/pull/253) 已 MERGED，Issue #252 已关闭；AC-024-01～07 均有真实 PASS 证据，SR-024 VERIFIED。GitHub Review COMMENTED、4 个 PR checks SKIPPED 不计作 APPROVED/CI PASS；Studio #269 消费端仍归 SR-016。


## IR-007

**Python 工程工具链与可复现开发环境**

Next 的 Python 项目需要统一依赖声明、版本锁定、解释器选择、虚拟环境隔离和 CI 执行入口，避免各 Workflow 临时安装未声明依赖，也避免多个 Git worktree 共享 editable 安装造成环境污染。

- 协作 Issue：[Next #35](https://github.com/odango-chan/ca-agent-next/issues/35)（中央设计与治理刷新；不是代码实施 Issue）。
- 实施分解：[SR-028](../SR/SR-028-Python工程工具链与uv环境管理.md)（DRAFT；实施 Issue 尚未创建）。
- 架构与设计：[G02 Python 工程工具链与环境管理设计说明书](../设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md) v0.1.2。
- 实施范围：首批仅覆盖 `ca-agent-next` 根 Python 项目；其他仓库采用 uv 或迁移依赖管理须各自登记目标仓、基线、Issue 和 SR。
- 完成依据：SR-028 的全部必需验收在目标仓真实执行并 VERIFIED；设计评审或锁文件生成本身不代表实施完成。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 登记五项 IR 及其实施分解 | 建立双向需求追踪 | SR-001～SR-011 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 更新 EC02 归档与追踪 | 对齐中央设计及 Compiler #61 | SR-012 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex 登记 Compiler 实施 SR | 对齐跨仓实施门槛 | SR-013 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | Codex / GPT-6 · IR-006 · 登记十项分仓 SR | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.1.3 | GPT-6.2（ChatGPT） | IR-003 | 明确 Compiler #61 为外部实现 Issue、Next #14 为文档刷新 Issue；不改变 SR-004/005/006 的消费端职责 | 区分外部实现和中央设计治理 | Issue #14、SR-013、Compiler #61 |
| 2026-11-25 | 0.1.4 | GPT-6.2（ChatGPT） | IR-003 | 登记 PR #16 为中央设计 Draft PR，明确不计入产品实施 | 使需求、设计 PR 和实施 Issue 状态一致 | Issue #14、PR #16、Compiler #61 |
| 2026-11-25 | 0.1.5 | GPT-6.2（ChatGPT） | IR-006 | 登记 Host Context Interface Package Publisher 独立需求 SR-024，并保留 SR-020 的参考宿主审计职责 | 修复 SR ID 冲突，保持 IR→SR 一对多追踪 | IR-006；SR-020、SR-024 |
| 2026-11-26 | 0.1.6 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 修复 IR-006 缺 SR-025 并登记 SR-026/027 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.7 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | IR-002 登记 SR-002 设计修订 Issue #19，并明确其不代表实施授权 | 补齐需求到设计修订的协作追踪 | Issue #19；SR-002 |
| 2026-11-26 | 0.1.8 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 回填 SR-002 设计 PR #20 的 Draft 状态和恢复分支目标 | 保持需求、Issue、PR 追踪闭合 | Issue #19；PR #20 |
| 2026-11-26 | 0.1.9 | GPT-6.2（ChatGPT） | IR-002 | 明确 Issue #19/#20 仅跟踪 SR-002 设计修订，并与实施 Issue 分离 | 避免将设计评审追踪误读为代码实施授权，保持 IR→SR→Issue→PR 关系清晰 | IR-002；SR-002；Issue #19；PR #20 |
| 2026-11-26 | 0.1.10 | GPT-6.2（ChatGPT） | IR-002 | 明确 Issue #19/#20 仅跟踪 SR-002 设计修订，并与实施 Issue 分离。 | 避免将设计评审追踪误读为代码实施授权，保持 IR→SR→Issue→PR 关系清晰。 | IR-002；SR-002；Issue #19；PR #20 |
| 2026-11-26 | 0.1.11 | GPT-6.2（ChatGPT） | IR-002 | 将 SR-002 设计 PR #20 状态同步为 Ready for review，并继续明确 Issue #19 非实施 Issue。 | 使需求登记与 GitHub 评审状态一致，不产生提前实施授权。 | IR-002；Issue #19；PR #20 |
| 2026-11-26 | 0.1.12 | GPT-6.2（ChatGPT） | IR-002 | 同步 SR-002 v0.2.6、Acceptance v0.3.7 与 PR #20 Ready for review 状态 | 使需求登记、设计修订追踪和验收版本一致，同时保持实施 Issue 未创建 | IR-002；SR-002；Issue #19；PR #20 |
| 2026-11-26 | 0.1.13 | GPT-6.2（ChatGPT） | IR-002 | 同步 SR-002 独立设计评审 APPROVE_FOR_READY 与 READY 状态，并登记治理 Issue #21；模块 AC 和系统 EX 继续 NOT_RUN。 | 区分设计、治理和后续代码实施追踪，避免把设计 Issue 当作实施授权。 | IR-002；SR-002；SR-003；Issue #19；Issue #21；PR #20 |
| 2026-11-26 | 0.1.14 | GPT-6.2（ChatGPT） | IR-002 | 登记 SR-002 READY 后创建的独立实施 Issue #22，并明确 Issue #19/#21 分别承担设计和治理追踪。 | 完成需求到实施任务的追踪链，防止误用设计 Issue。 | IR-002；SR-002；Issue #19；Issue #21；Issue #22；PR #20 |
| 2026-11-26 | 0.1.15 | GPT-6.2（ChatGPT） | IR-002 | 同步 SR-002 实施 PR #23 合并、AC-002-01～08 PASS、SR-002 VERIFIED，以及设计/治理 Issue #19/#21 的关闭状态；保留 SR-003 DRAFT 与 EX-01 NOT_RUN。 | 使 IR-002 的完成状态反映已完成模块和剩余模块，不把单个 SR VERIFIED 或模块 AC PASS 误报为 IR 整体完成。 | Issue #22；PR #20；PR #23；SR-002 v0.2.10；SR-003 v0.2.7 |
| 2026-11-26 | 0.1.16 | GPT-6.2（ChatGPT） | IR-001、IR-007 | 刷新 SR-001 当前 PR/验收边界，并登记 Python 工程工具链与 uv 环境管理需求 | 修正 G01 §11.8 过期状态，建立 Python 工具链需求到 G02/SR-028 的追踪 | Issue #35；PR #32；SR-001；SR-028 |
| 2026-11-26 | 0.1.17 | GPT-6.2（ChatGPT） | IR-007 | 将 G02 设计引用更新至 v0.1.1，明确 SR-028 命令只在 PR #32 集成后可用 | 保持 IR、G02 和 SR-028 使用同一最新设计版本与阶段依赖 | Issue #35；G02 v0.1.1；SR-028 v0.1.1 |
| 2026-11-26 | 0.1.18 | GPT-6.2（ChatGPT） | IR-001 | 回填 SR-001 最终 78 项测试、AC-REV-01～10 PASS 与真实 Workflow/Artifact 证据；保留 PR OPEN 的集成门禁 | 两个独立复核 BLOCKER 已修复，但未合并前不把需求标记完成 | Issue #27；PR #32；Run 45791388839；SR-001 v0.3.8 |
| 2026-11-26 | 0.1.19 | GPT-6.2（ChatGPT） | IR-001 | 回填 SR-001 最终 80 项测试、代码块/注释/重复声明反例与 Run 45793336377；保留 PR OPEN 的集成门禁 | 将最新代码 HEAD、测试与 Artifact 证据同步至需求登记册，不把验收 PASS 误报为已集成 | Issue #27；PR #32；Run 45793336377；SR-001 v0.3.9 |
| 2026-11-26 | 0.1.20 | GPT-6.2（ChatGPT） | IR-007 | 将 G02/SR-028 引用升级到 v0.1.2，记录精确 Python 文件内容、setup-uv 配置和可复现边界 | 使需求登记册指向最新可执行设计基线 | Issue #35；G02 v0.1.2；SR-028 v0.1.2 |
| 2026-11-26 | 0.1.21 | GPT-6.2（ChatGPT） | IR-001 | 根据 PR #32 合并、80 项测试及 AC 证据更新 SR-001 完成依据 | 此前 PR OPEN 的历史状态已过期 | Issue #27；PR #32；PR #36 |
| 2026-11-26 | 0.1.22 | GPT-6.2（ChatGPT） | IR-002、IR-006 | 回填 SR-003 设计 READY / 实施 IN_PROGRESS 及 PR #34 本地模块 AC 证据；回填 SR-024 PR #253 合并、Issue #252 关闭和 VERIFIED 状态 | 修正需求登记册中 SR-003 DRAFT、SR-024 未记录实施结果的过期状态；不把未合并 PR 或 SKIPPED checks 误报为已集成/CI PASS | Issue #12、#28；SR-003；SR-024；PR #34；ca-agent-demo #252/#253 |
