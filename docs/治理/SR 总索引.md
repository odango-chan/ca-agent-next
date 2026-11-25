# SR 总索引

> 文档类型：软件需求索引  
> 文档版本：0.2.1  
> 状态：待评审；全部 SR 当前为 DRAFT，不允许直接实施  
> 修订日期：2026-11-25  
> 权威规则：[SR 管理规范](../规范/SR%20管理规范.md)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  

## 1. 使用规则

- 每项 SR 的完整范围和验收条件以对应 SR 文件为准。
- 本索引只汇总 ID、标题、设计依据、状态、依赖和实施入口。
- 状态变化先更新 SR 文件，再更新本索引和[实施状态总览](实施状态总览.md)。
- ca-agent-next PR #1 是文档/设计基线 PR，不是任何 SR 的实现 PR。
- PR #1 尚未合并，正式设计基线尚待评审，因此本批 SR 全部为 DRAFT。

## 2. SR 清单

| SR ID | 需求 | 设计依据 | Acceptance | 依赖 | 状态 | Issue / 实施 PR |
|---|---|---|---|---|---|---|
| [SR-001](../SR/SR-001-评审上下文自动生成.md) | 评审上下文自动生成 | 文档编写与治理规范 §11；Agent.md review_scope | AC-REV-01～AC-REV-10 | 无 | DRAFT | 未创建 |
| [SR-002](../SR/SR-002-Python%20核心与%20Host%20基础骨架.md) | Python 核心与 Host 基础骨架 | CA Agent Next 架构设计 §3～§5；实施路线与阶段门槛 §1 | EX-01 | 无；ca-agent-demo 仅作为只读复用证据。 | DRAFT | 未创建 |
| [SR-003](../SR/SR-003-统一%20Plugin%20Manager%20与%20Extension%20IPC.md) | 统一 Plugin Manager 与 Extension IPC | 插件管理与通信设计说明书 §3～§10；插件包与进程通信协议规范 §1～§12 | EX-02、EX-03、EX-18 | SR-002。 | DRAFT | 未创建 |
| [SR-004](../SR/SR-004-已发布%20Skill%20包导入.md) | 已发布 Skill 包导入 | 技能导入与选择设计说明书 §2～§4；技能与确定性保障格式规范 §1～§5 | EX-05～EX-08 | SR-002；外部依赖为 ca-skills 作者格式与 ca-skill-compiler 发布契约。 | DRAFT | 未创建 |
| [SR-005](../SR/SR-005-SkillCatalog%20与已检查%20when%20程序消费.md) | SkillCatalog 与已检查 when 程序消费 | 技能导入与选择设计说明书 §5、§7；发布产物与 CEL 运行时互操作设计说明书 §5～§8 | EX-21～EX-23、EX-25～EX-29 | SR-004；外部依赖为 ca-skill-compiler 发布 CheckedExpr/DescriptorSet 格式及 Python CEL Runtime。 | DRAFT | 未创建 |
| [SR-006](../SR/SR-006-Skill%20Resolver%20与%20continuation%20选择.md) | Skill Resolver 与 continuation 选择 | 技能导入与选择设计说明书 §6；CA Agent Next 架构设计 §7 | EX-09、EX-10、EX-19、EX-24 | SR-005。 | DRAFT | 未创建 |
| [SR-007](../SR/SR-007-统一%20Runtime%20Action%20Boundary%20与双执行模式.md) | 统一 Runtime Action Boundary 与双执行模式 | 运行时与动作边界设计说明书 §2～§8；公共契约与所有权规范 §5～§8 | EX-13～EX-16 | SR-003、SR-004、SR-006。 | DRAFT | 未创建 |
| [SR-008](../SR/SR-008-Echo%20首个垂直%20E2E%20示例.md) | Echo 首个垂直 E2E 示例 | 演示验收基线 §1～§6；实施路线与阶段门槛 §6 | EX-17 | SR-002～SR-007。 | DRAFT | 未创建 |
| [SR-009](../SR/SR-009-OpenAMSM%20SBI%20Event%20Plugin%20与%20Artifact%20Handoff.md) | OpenAMSM SBI Event Plugin 与 Artifact Handoff | 事件接入与二进制产物交接设计说明书 §1～§6、§8～§10；插件包与进程通信协议规范 | OM-01～OM-03、OM-05～OM-08、OM-14、OM-15 | SR-008、SR-003；外部依赖为 ca-openamsm-plugin 设计/实现契约。 | DRAFT | 未创建 |
| [SR-010](../SR/SR-010-OpenAMSM%20Tool%20Plugin%20与按需%20Codec%20集成.md) | OpenAMSM Tool Plugin 与按需 Codec 集成 | 插件管理与通信设计说明书 §7；事件接入与二进制产物交接设计说明书 §7；公共契约与所有权规范 §5、§6 | OM-04、OM-10、OM-13 | SR-003、SR-007、SR-009；外部依赖为 ca-client-tools Codec API 发布与准确消息子集资格。 | DRAFT | 未创建 |
| [SR-011](../SR/SR-011-真实%20OpenAMSM%20Create%20Modify%20Release%20E2E.md) | 真实 OpenAMSM Create Modify Release E2E | CA Agent Next 架构设计 §10～§13；事件接入与二进制产物交接设计说明书 §8～§11；演示验收基线 §7 | EX-20、OM-09、OM-11、OM-12 | SR-008、SR-009、SR-010；外部依赖为真实 OpenAMSM、ca-client-tools 和所需 Skill 发布物。 | DRAFT | 未创建 |

## 3. 实施顺序

- 治理自动化：SR-001，可独立实施；依赖设计基线评审通过。
- Phase A：SR-002。
- Phase B：SR-003。
- Phase C：SR-004。
- Phase D：SR-005、SR-006。
- Phase E：SR-007。
- Phase F：SR-008。
- Phase G：SR-009、SR-010。
- Phase H：SR-011。

阶段顺序是建议依赖顺序；每个 SR 只有达到 READY 且依赖满足后才能进入实施。

## 4. 当前基线说明

- 设计来源：ca-agent-next PR #1 的架构、设计、规范和 Acceptance 文档，当前文档版本基线 0.1.0。
- PR #1：OPEN，非 Draft，仍待评审；只代表设计文档变更。
- Next Runtime：README 声明尚无已验收 Runtime 实现。
- 所有 SR：DRAFT；Issue、实现 PR、Commit 和测试证据均未建立。
- ca-agent-demo、ca-client-tools、ca-skill-compiler、ca-skills 和 ca-openamsm-plugin 的现有代码/PR 只能作为外部复用或依赖证据，不能自动算作 Next SR 已实施。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | 收编既有 SR-001，并建立 Phase A～H 的 10 项初始 SR | 统一需求编号和设计实施追踪 | SR-001～SR-011 |

| 2026-11-25 | 0.2.1 | 补齐文档版本与评审范围声明 | 落实正式文档版本和评审范围继承规则 | SR-001～SR-011 |