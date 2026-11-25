# CA Agent Next

CA Agent Next 是下一代通用 Agent 的独立实现仓。目标是用尽可能少、可验证的机制证明：通用 Agent 可以通过 Skill 和 Plugin 扩展不同业务，而不需要为每个业务修改 Agent Core。

**语言决策：Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 固定使用 Python。** 独立 Plugin 可以使用 Go；Go Plugin 不意味着 Go Host。

> 当前状态：PR #1 是架构、功能设计和规范基线，仍待评审；本仓尚无已验收的 Agent Runtime 实现。设计完成、代码实现和验收通过必须分别表述。

## 从这里开始

1. [功能树与需求追踪基线](docs/治理/功能树与需求追踪基线.md) — 先识别 Feature / IR / SR，再按功能加载资料。
2. [CA Agent Next 架构设计](docs/架构设计/CA%20Agent%20Next%20架构设计.md) — 唯一总体架构。
3. [文档总目录与索引](docs/治理/文档总目录与索引.md) — 正式文档入口。
4. [SR 管理规范](docs/规范/SR%20管理规范.md) — SR、Issue、PR、Commit 和验收追踪规则。
5. [文档编写与治理规范](docs/规范/文档编写与治理规范.md) — 功能设计与修订记录要求。
6. [演示验收基线](docs/验收与实施/演示验收基线.md) — Echo 与 OpenAMSM 的 EX/OM 验收门槛。
7. [仓库协作指引](Agent.md) — 自动化协作入口和不可违反的约束。

[IR 总登记册](docs/IR/IR%20总登记册.md)记录需求项、Issue 协作入口和 SR 分解。

## 文档体系

25 份正式文档，另有 1 份 IR 登记册（5 项 IR）和 11 份 SR 记录。正式文档包括 1 份总体架构、6 份设计说明书、7 份规范、5 份治理、4 份验收与实施、2 份参考审计。

架构设计与设计说明书在 docs 下同级。设计说明书按 F01～F06 功能域归档；SR 记录需求范围和验收条件，不替代功能设计。F07 示例与验收由统一验收基线承载。

## 跨仓任务入口

项目群任务统一从本仓发起。先查[各仓功能子树](docs/治理/功能树与需求追踪基线.md#51-按仓功能子树)，在本仓登记或选用明确覆盖目标仓改动的 SR，达到 READY 后再实施，随后回填目标仓 PR、Commit 与验收证据。

## 仓库职责与外部能力

| 功能/能力 | 权威仓库 | Next 的责任 |
|---|---|---|
| Agent Core / Host / Runtime | ca-agent-next | Python 新实现 |
| Skill 作者规范与业务 Skill（EC01） | ca-skills | 消费 SKILL.md 与发布输入 |
| CA-SL Compiler / Artifact 发布（EC02） | ca-skill-compiler | 只消费已发布 Runtime Artifact |
| Tool Interface / Provider / Codec（EC03） | ca-client-tools | 通过唯一 Plugin Manager 的 tools Extension 调用 |
| OpenAMSM SBI Event / Delivery Plugin（EC04） | ca-openamsm-plugin | 消费统一 Plugin Package/IPC 和 Artifact Handoff |
| OpenAMSM Owner（EC05） | env-openamsm 等 Owner 仓 | 消费权威 Receipt / Commit Proof |
| 参考实现（REF01） | ca-agent-demo | 逐文件选择性复用代码和测试 |
| 后续晋级目标（TARGET01） | ca-agent | Next 验收后评估晋级 |

Compiler 机制设计集中在 [EC02](docs/设计说明书/EC02-Compiler/Compiler设计说明书.md)，实现和机器契约由 ca-skill-compiler 维护。其余外部能力的内部设计由各权威仓维护，Next 管理消费边界与集成 SR。

## 架构要点

- 全系统只有一个 Plugin Manager。Plugin 可导出 event.ingress、event.delivery、tools 中一种或多种 Extension。
- Tool 是 Plugin 导出的 Callable Operation，不是独立进程或 Manager。
- 每个 Skill 必须有 SKILL.md；Assurance 可选。无 Assurance 仅 LLM-guided；有效发布 Artifact 支持 Deterministic 和 LLM-guided；无效 Artifact 导入失败。
- when 是可选 Assurance Contract 中的 CEL 选择表达式；predicates.yaml 只用于执行期业务判断。
- Agent 只消费已发布 Skill Artifact，不调用 Compiler，不实现 Skill Admission。
- Deterministic 与 LLM-guided 经过同一个 Runtime Action Boundary。
- SBI 可携带 JSON 和 multipart 二进制。Event Plugin 处理外部协议；Host 管理 ArtifactStore；Codec 按需作为现有 Tool Plugin 的 Operation 调用。

## 实施顺序

先完成 Python Core、唯一 Plugin Manager、已发布 Skill 导入、SkillCatalog / Resolver 和 Runtime Action Boundary；通过 Echo 垂直 E2E 后，再接入 OpenAMSM Plugin、Tool Package 和 Create → Modify → Release。未取得真实证据的阶段标记 NOT_STARTED / NOT_RUN。

## Demo 范围

本仓证明机制正确性和可扩展性，不做生产级资格认证。可靠性与安全 DFX 暂不展开生产方案；不增加 HA/DR/SLA、包签名、Trust Registry、生产密钥管理或复杂多租户治理。基本输入校验、明确错误、fail-closed、Owner 结果语义、最小可观测性和自动化验收仍必须具备。
