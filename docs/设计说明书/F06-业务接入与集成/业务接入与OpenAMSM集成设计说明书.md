# 业务接入与 OpenAMSM 集成设计说明书

> 文档类型：功能设计说明书  
> 文档版本：0.1.3
> 功能归属：F06 — 业务接入与集成  
> 关联 SR：SR-009、SR-010、SR-011  
> 状态：目标集成设计；真实隔离 E2E 尚未完成  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope

关联需求项见 [IR-005](../../IR/IR%20总登记册.md#ir-005)。

## 1. 目标与范围

本功能验证通用 Agent 可以通过独立 Plugin、Skill、Tool Interface Package 和 Owner 能力接入 OpenAMSM，而不在 Agent Core 中增加 OpenAMSM 专用业务分支。

OpenAMSM 是 Echo 之后的第二个业务集成。本文定义 Next 侧集成边界，不复制 ca-openamsm-plugin、ca-client-tools 或 env-openamsm 的内部设计。二进制 Artifact 交接细节由 [Context 与 Artifact 管理设计说明书](../F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) 维护；Plugin 生命周期和 IPC 由 F03 维护；Runtime 和 Owner 结果解释由 F04 维护。

## 2. Skill-first 业务接入

外部 Event 到达 Host 后，先形成规范化 Event，再由 F02 Resolver 绑定 Skill，之后才选择执行模式并进入 Runtime。Event Schema 不包含 Skill ID、Goal 或业务 Contract Package；不新增 Event→Skill 或 Event→Mode 映射表。

业务选择信息只允许来自明确的协议 discriminator 和 Skill Contract.when。没有匹配候选时停止或澄清，不进入无 Skill 绑定的通用执行路径。

## 3. OpenAMSM SBI Event / Delivery Plugin

EC04 ca-openamsm-plugin 负责：

- SBI HTTP/2 ingress 和响应 Delivery。
- JSON 与 multipart/related 解析。
- Content-ID 与 N1/N2 原始字节关联。
- 规范化 Event 发布。
- 将原始二进制交给 F05 定义的 Host staging / ArtifactStore。

该 Plugin 不负责 Skill 选择、Owner Tool、RunStore、Wait/Resume、Runtime、完整 NAS/NGAP 业务解码或业务状态机。

共享 UpdateSMContext 只允许提取已资格化的最小 NAS discriminator，用于区分 Modify 与 UE-requested Release。畸形、歧义或不支持的消息必须显式失败；不得把业务选择逻辑藏进 Plugin。

## 4. 协议与契约归属

| 内容 | 权威来源 | Next 使用方式 |
|---|---|---|
| Nsmf/Namf SBI Operation、HTTP 路径和 JSON Schema | 3GPP OpenAPI / OpenAMSM 版本基线 | Event Plugin 按协议解析 |
| NAS / NGAP 消息和字段 | 对应 3GPP 标准及已资格化 Codec | Skill 按需调用 Codec Tool |
| Skill 选择输入 | Skill Contract.requestSchema 与 when | 只描述 Skill 所需业务输入 |
| Provider 公开 Callable / IO Schema / Effect / Capability | ca-client-tools Tool Interface Package（当前公开 11 个 READ Tools） | Compiler / Runtime 消费；不表示 Skill 获得授权 |
| OpenAMSM 业务 Callable / Owner Outcomes / Receipt / Commit Proof / Reconcile | env-openamsm Owner Contract Package v1alpha4 | Provider / Runtime 消费；Owner 是业务状态权威 |
| Provider 私有 backendOperationId / HostInvocation / privateArguments | ca-client-tools Provider Runtime Bindings v1 | 唯一 Plugin Manager 内部 ProviderV2 Driver 消费；不暴露给 Skill |
| Plugin Manifest / IPC | ca-agent-next Plugin 规范 | Event Plugin 对齐本仓契约 |

Provider 进程、Tool Interface、Owner Contract 与 Provider Runtime Bindings 的 Next 消费边界见 [F03.05 Tool Interface 与 Provider 集成设计说明书](../F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)。本说明书只负责 OpenAMSM 业务接入、Event/Delivery 与 Create/Modify/Release 的业务组合，不定义通用 Provider Manager。\n\n不把完整 3GPP OpenAPI 或 NAS/NGAP Schema 复制进 SKILL.md 的 requestSchema；不在 Next 重定义 Owner 契约。

## 5. Create、Modify 与 UE-requested Release

### 5.1 Create

规范化 Create Event 先绑定 Establish Skill。Skill 通过已发布 Tool Interface Package 调用 Owner 创建操作。Runtime 依据 Owner Receipt / Commit Proof 判定提交结果；HTTP 201 本身不是 Commit Proof。后续 N1/N2 消息和响应通过 F05 Artifact Handoff。

### 5.2 Modify

Modify Event 绑定 Modify Skill。业务变化通过 Tool Interface Package 暴露的 typed Callable 表达；Runtime 不维护 MAS 私有字段投影。Owner 对 QoS / Session 修改的提交结果和状态由 Owner Receipt、Commit Proof 与最终状态投影证明。

### 5.3 UE-requested Release

UE-requested Release Event 绑定 Release Skill。N1 Release Complete（0xD4）及适用 N2 Release Response 通过原 Run 的 Wait / Continuation 恢复；不得把旧消息、旧 generation 或其他 UE/PSI 的消息串入新 Run。

Create、Modify、Release 的详细业务 Procedure 由 ca-skills 作者源和发布 Artifact 维护；Owner 行为由 env-openamsm 与 ca-client-tools 维护。Next 不复制这些业务流程。

## 6. Core 零业务耦合

第二业务接入的验收目标是只增加：

- 业务 Event / Delivery Plugin。
- 业务 Skill 和已发布 Artifact。
- Tool Interface Package 与 Tool Plugin。
- 部署配置、协议 Schema 和验收 Fixture。

不得修改 F01 Agent Core、F02 Resolver、F03 Plugin Manager 或 F04 Runtime 的业务专用分支。确有通用机制缺口时，先定义通用 SR，再设计不包含 OpenAMSM 词汇的机制扩展。

## 7. 外部依赖

| 外部能力 | 权威仓库 | Next 关联 |
|---|---|---|
| Skill 作者规范和业务 Skill | ca-skills（EC01） | SR-011 |
| Compiler 发布物和 when | ca-skill-compiler（EC02） | SR-004、SR-005 |
| Tool Interface / Provider / Codec | ca-client-tools（EC03） | SR-003、SR-007、SR-010、SR-011 |
| SBI Event / Delivery Plugin | ca-openamsm-plugin（EC04） | SR-009、SR-011 |
| Owner 状态与 Receipt | env-openamsm（EC05） | SR-007、SR-010、SR-011 |

外部仓内部设计以其权威文档为准。外部状态快照统一由功能树和跨仓审计维护，本文不重复维护会过期的 PR 状态。

## 8. 验收与追踪

- SR-009：OM-01～OM-03、OM-05～OM-08、OM-14、OM-15。
- SR-010：OM-04、OM-10、OM-13。
- SR-011：EX-20、OM-09、OM-11、OM-12。

真实隔离 E2E 必须使用一个 UE/PSI，经真实 OpenAMSM Owner 完成 Create → Modify → UE-requested Release，保留 N1/N2 原始 Artifact、Run/Wait 关联、Owner Receipt/Commit Proof 和零重复 mutation 证据。Synthetic Owner、fixture 或离线测试不能替代真实隔离 E2E。

## 9. 文档修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 F06 业务接入与 OpenAMSM 集成设计 | 将 SBI、Tool、Owner 和业务 E2E 统一到一个集成边界，不在 Core 中复制业务逻辑 | F06；SR-009～011；EC01～EC05；PR #1 |
| 2026-11-25 | 0.1.1 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | OpenAMSM Owner 与仿真对端 | 合并有效边界与分仓证据入口 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.1.3 | GPT-6.2（ChatGPT） | §4 | 区分公开 Provider Interface、Owner Contract Package 和 Provider Runtime Bindings，并链接 F03.05 集成设计 | 对齐 EC03 v1.2.0 与 Owner v1alpha4 的实际发布边界 | IR-006 · SR-015 · Issue #12 |
