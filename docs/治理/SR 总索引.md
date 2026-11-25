# SR 总索引

> 文档类型：软件需求索引  
> 文档版本：0.3.5\
> 状态：待评审；全部 SR 当前为 DRAFT，不允许直接实施  
> 修订日期：2026-11-25  
> 权威规则：[SR 管理规范](../规范/SR%20管理规范.md)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  

跨仓任务从 Next 发起。先在本仓登记覆盖目标仓和修改范围的 SR，达到 READY 后再切换到目标仓实施，目标仓结果回填本仓 SR。既有外部 Issue 可作为关联入口。详见《SR 管理规范》§8.1。

## 1. 使用规则

- 每项 SR 的完整范围和验收条件以对应 SR 文件为准。
- 本索引只汇总 ID、标题、设计依据、状态、依赖和实施入口。
- 状态变化先更新 SR 文件，再更新本索引和[实施状态总览](实施状态总览.md)。
- ca-agent-next PR #1 是文档/设计基线 PR，不是任何 SR 的实现 PR。
- PR #1 已合并；原 SR 和新增跨仓 SR 仍为 DRAFT。

## 2. SR 清单

| SR | 上游 IR | 需求 | 状态 |
|---|---|---|---|
| [SR-001](../SR/SR-001-评审上下文自动生成.md) | [IR-001](../IR/IR%20总登记册.md#ir-001) | 评审上下文自动生成 | DRAFT |
| [SR-002](../SR/SR-002-Python%20核心与宿主基础骨架.md) | [IR-002](../IR/IR%20总登记册.md#ir-002) | Python 核心与宿主基础骨架 | DRAFT |
| [SR-003](../SR/SR-003-统一插件管理器与扩展通信.md) | [IR-002](../IR/IR%20总登记册.md#ir-002) | 统一插件管理器与扩展通信 | DRAFT |
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
| [SR-015](../SR/SR-015-工具契约设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 工具契约设计移交 | DRAFT |
| [SR-016](../SR/SR-016-工作台设计移交与条件编辑.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 工作台设计移交与条件编辑 | DRAFT |
| [SR-017](../SR/SR-017-业务插件设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 业务插件设计移交 | DRAFT |
| [SR-018](../SR/SR-018-业务所有者设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 业务所有者设计移交 | DRAFT |
| [SR-019](../SR/SR-019-仿真对端设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 仿真对端设计移交 | DRAFT |
| [SR-020](../SR/SR-020-参考宿主设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 参考宿主设计移交 | DRAFT |
| [SR-021](../SR/SR-021-原生宿主设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 原生宿主设计移交 | DRAFT |
| [SR-022](../SR/SR-022-执行内核设计移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 执行内核设计移交 | DRAFT |
| [SR-023](../SR/SR-023-技能作者源与语言规范移交.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | 技能作者源与语言规范移交 | DRAFT |
| [SR-024](../SR/SR-024-Host%20Context%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | Host Context Interface Package Publisher | DRAFT |
| [SR-025](../SR/SR-025-MAS%20Owner%20Interface%20Package%20Publisher.md) | [IR-006](../IR/IR%20总登记册.md#ir-006) | MAS Owner Development Interface Package Publisher | DRAFT |

设计版本与章节、依赖、验收 ID、实施证据以各 SR 为准。逐项阻塞见[就绪审计](../参考与审计/跨仓设计资产迁移与一致性审计.md#8-设计就绪审计)。

## 3. 设计恢复与实施顺序

### 3.1 中央设计恢复批次（当前均为 DRAFT，不可实施）

| 顺序 | SR | 主要功能 | 目标仓 / 参考仓 | 依赖和产出 |
|---|---|---|---|---|
| 1 | SR-023 | CA-SL v1alpha5、作者源与发布基线恢复 | ca-skills | 先固定语言、Skill 作者源与版本边界；Compiler #61 仍是外部 OPEN 依赖 |
| 2 | SR-015 | Tool Interface / Provider / Codec 设计恢复 | ca-client-tools → Next F03.05 | 明确公开 Callable、Owner Contract、Provider v2 和单一 Plugin Manager 消费 |
| 3 | SR-025 | MAS Owner Development Interface Package Publisher | ca-client-tools → Next F03.05 / F09 | 将 Owner v1alpha4 source 包装为 Compiler v2.1.0 Development Interface Package；package.version 固定为 `1.0.0` |
| 4 | SR-024 | Host Context Interface Package Publisher | ca-agent-demo → Next F09 | 发布 Host Context Development fixture 的正式 Interface Package；不占用 SR-020 的参考宿主审计 ID |
| 5 | SR-018 | OpenAMSM Owner 权威状态恢复 | env-openamsm | 固定 Callable、Receipt、Commit Proof、Reconcile 和 Modify/Release 边界 |
| 6 | SR-019 | Mock AMF / 5GC 仿真对端恢复 | env-5gc-sim | 固定协议对端、World、进程和真实测试边界 |
| 7 | SR-017 | OpenAMSM Event/Delivery Plugin 恢复 | ca-openamsm-plugin | 依赖 F03/F05、EC05 Owner Contract；当前 PR #1 Draft |
| 8 | SR-020 | Python Generic Host 参考实现审计 | ca-agent-demo | 为 F01/F03/F04/F05 提供可复用代码证据；不复制业务专用架构 |
| 9 | SR-022 | ca-runtime 执行内核设计审计 | ca-runtime | 与 F04 对照，区分采用、简化和排除的机制 |
| 10 | SR-016 | Skill Studio / AI Authoring 设计恢复 | ca-skill-studio-demo | 与 CA-SL、F08/F09 对齐；PR #258 已合并，部署状态独立验证 |
| 11 | SR-021 | Go Native Host 晋级目标审计 | ca-agent | 最后对照，不能改变 Next 当前 Python Host 决策 |

以上顺序是文档依赖和设计评审顺序，不是实施授权。每份 SR 必须完成设计章节、目标仓/固定 SHA、代码/测试差异、验收命令和非目标边界；评审通过后才可进入 READY。

### 3.2 Next 实施阶段

- 治理自动化：SR-001，与产品阶段独立；交付门禁、实际 Issue 和当前设计提交评审通过后方可启动。
- Phase A：SR-002。
- Phase B：SR-003。
- Phase C：SR-004。
- Phase D：SR-005、SR-006。
- Phase E：SR-007。
- Phase F：SR-008。
- Phase G：SR-009、SR-010。
- Phase H：SR-011。
- Compiler 外部发布依赖：SR-012、SR-013；SR-013 的 [PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN，不代表 Compiler 产品发布或完整 SR VERIFIED。

阶段顺序是建议依赖顺序；每个 SR 只有达到 READY 且依赖满足后才能进入实施。Goal 模式可将同一依赖批次中的多个 READY SR 合并执行，但不得跨越未满足的依赖或把 DRAFT SR 当成可执行任务。

## 4. 当前基线说明

- 设计来源：ca-agent-next PR #1 的架构、设计、规范和 Acceptance 文档。
- PR #1：已合并；只代表设计文档变更。
- Next Runtime：README 声明尚无已验收 Runtime 实现。
- 24 项 SR 当前均为 DRAFT；[PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN，不改变 SR-013 总体 DRAFT 状态。SR-009 仅覆盖 Event/Delivery Plugin 与本地 staging；SR-010 还覆盖 Next Host ArtifactStore、ca-host.artifact-store/v1 channel server、Provider v2 Driver 和 Codec 消费。
- Issue #12 追踪本轮中央设计资产恢复；PR #11/#13/#15/#16/#18 均在独立分支 OPEN/DRAFT，恢复分支已同步可复用的最新文档内容但尚未创建 PR；PR 状态不等于 SR 实施状态。
- 本分支 docs/restore-original-designs-20261125 尚未创建 PR；现行入口的相对路径和锚点已复核；各 SR 的正式资产、环境与交付门禁分开判断。
- ca-agent-demo、ca-client-tools、ca-skill-compiler、ca-skills 和 ca-openamsm-plugin 的现有代码/PR 只能作为外部复用或依赖证据，不能自动算作 Next SR 已实施。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | 收编既有 SR-001，并建立 Phase A～H 的 10 项初始 SR | 统一需求编号和设计实施追踪 | SR-001～SR-011 |
| 2026-11-25 | 0.2.1 | 补齐文档版本与评审范围声明 | 落实正式文档版本和评审范围继承规则 | SR-001～SR-011 |
| 2026-11-25 | 0.2.2 | 统一 SR-002～SR-011 文件名和标题为中文 | 落实文档命名规范，保留 SR ID 不变 | SR-002～SR-011 |
| 2026-11-25 | 0.2.3 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.4 | 明确跨仓 SR 登记及证据回填 | 统一跨仓入口 | 见关联 SR |
| 2026-11-25 | 0.2.5 | 更新 EC02 归档与追踪 | 对齐中央设计及 Compiler #61 | SR-012 |
| 2026-11-25 | 0.2.6 | Codex 登记 Compiler 实施 SR | 对齐跨仓实施门槛 | SR-013 |
| 2026-11-25 | 0.2.6 | Codex / GPT-6 · §1–4 · 登记分仓 SR 与真实基线状态 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.2.8 | 将 SR-015～SR-024 按功能依赖排序，区分文档恢复批次与 Next 实施阶段；记录 PR #13 与 Issue #12 的真实边界，并注明 AC-013-01 隔离 PoC PASS | 避免 DRAFT 被误判为可执行，区分 PoC 与产品发布 | Issue #12；SR-013、SR-015～SR-023 |
| 2026-11-25 | 0.2.9 | GPT-6.2（ChatGPT） | §1～4 | 明确 SR-009 的 Plugin staging 边界与 SR-010 的 Next Host ArtifactStore/Channel 实施范围 | 使 F05 的 Host/Plugin 责任有唯一 SR 归属 | Issue #12；SR-009、SR-010 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §2～4 | 新增 SR-024 Host Context Interface Package Publisher；调整跨仓设计恢复顺序；将 AC-013-01 标记为报告 PASS、证据未归档、独立复核未运行 | 修复 SR-020 编号冲突，避免把 PoC 报告误作产品验收 | Issue #12/#14；IR-006；SR-013、SR-020、SR-024 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §2～4 | 明确 AC-013-01 报告性 PASS 与证据未归档状态，更新多 PR 内容协调规则 | 保持 DRAFT/READY/IMPLEMENTED 状态严格分离 | Issue #12/#14；PR #11/#13/#15/#16/#18 |
| 2026-11-25 | 0.3.2 | 同步当前权威设计或审计证据 | 核对 Issue #12 与固定提交 | 见就绪审计 |

| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | §2～4 | 新增 ca-client-tools MAS Owner Development Interface Package Publisher SR-025，并将其置于 SR-015 设计之后、SR-024 Host Publisher 之前 | 按目标仓分离 Owner 与 Host Publisher，避免把中央设计 SR 当作外部代码实施 SR | Issue #12；SR-015、SR-016、SR-024、SR-025 |
| 2026-11-25 | 0.3.4 | Codex / GPT-6 · 同步 Publisher 身份、版本和验收边界 | 对齐当前架构与实施门禁 | Issue #12 |
| 2026-11-25 | 0.3.5 | Codex / GPT-6 · §3～4 区分文档检查、实现和独立审批条件 | 对齐当前架构与实施门禁 | Issue #12 |
