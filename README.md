# CA Agent Next

CA Agent Next 是下一代通用 Agent 的独立实现仓。目标是以最小、可验证的机制证明：通用 Agent 可以通过可插拔 Plugin、Skill 和 Tool 扩展业务，而不需要为新增业务修改 Agent Core。

**语言决策：Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 固定使用 Python。** 独立运行的 Plugin 可以使用 Go 等适合的语言；Go Plugin 不代表 Go Host。

> 当前状态：PR #1 是目标架构与契约文档基线，仍待评审；本仓尚无已验收的 Agent Runtime 实现。设计完成、代码实现和验收通过必须分别表述。

## 从这里开始

1. [CA Agent Next 架构设计](docs/架构设计/CA%20Agent%20Next%20架构设计.md)
2. [文档总目录与索引](docs/治理/文档总目录与索引.md)
3. [现有文档盘点与收敛计划](docs/治理/现有文档盘点与收敛计划.md)
4. [文档编写与治理规范](docs/规范/文档编写与治理规范.md)
5. [SR-001：评审上下文自动生成](docs/验收与实施/SR-001%20评审上下文自动生成.md)
6. [文件结构规范](docs/规范/文件结构规范.md)
7. [演示验收基线](docs/验收与实施/演示验收基线.md)
8. [仓库协作指引](Agent.md)

## 文档体系

正式文档共 20 份：1 份总体架构、5 份设计说明书、6 份规范、2 份治理、4 份验收与实施（含 SR-001）、2 份参考审计。README.md 和 Agent.md 是仓库入口，不计入正式文档数量。

架构设计与设计说明书在 docs 下同级。架构只定义全局边界和主流程；设计说明书描述机制；规范定义文件结构、字段和公共契约；治理目录维护索引与迁移台账；验收与实施记录门槛和实施任务；参考与审计保留代码复用和跨仓状态证据。

## 仓库职责

| 仓库 | 权威职责 |
|---|---|
| ca-agent-next | Agent 架构、Plugin/Runtime 公共机制、Skill 导入与选择机制 |
| ca-agent-demo | 既有 Python 实现、测试和复用证据 |
| ca-skill-compiler | CA-SL 语言语义、编译、链接、Artifact 构建与发布 |
| ca-skills | Skill 作者源、业务 Assurance 和 CA-SL 规范发布 |
| ca-client-tools | Tool 实现、Tool Interface Package 和 Owner 交互契约 |
| ca-openamsm-plugin | OpenAMSM SBI Event ingress / Delivery Plugin |
| ca-agent | 当前稳定实现及未来晋级目标 |

Next 不复制 CA-SL 语言规范、业务 Skill 或 Tool 实现。其他仓库只维护本仓实现、集成、操作和验收材料，并引用 Next 的架构和公共机制规范。

## 架构要点

- 全系统只有一个 Plugin Manager。Plugin 可导出 event.ingress、event.delivery、tools 中的一种或多种 Extension。
- Tool 是 Plugin 导出的可调用 Operation，不是独立进程、Manager 或 Registry。Tool Plugin 是导出 tools Extension 的 Plugin。
- 每个 Skill 必须有 SKILL.md；assurance/ 可选。没有 Assurance 只能 LLM-guided；存在有效发布 Artifact 时可 Deterministic 或 LLM-guided；无效 Artifact 导入失败，不得静默降级。
- when 是 assurance/contract.yaml 的可选 CEL 选择表达式；predicates.yaml 只用于执行期业务判断。
- Agent 只消费已发布 Skill Artifact，不调用 Compiler，也不实现独立 Skill Admission。
- 所有 Deterministic 和 LLM-guided Action 都经过同一个 Runtime Action Boundary。
- SBI 可携带 JSON 和 multipart 二进制。Event Plugin 处理外部协议；Host 管理 ArtifactStore；Codec 按需作为现有 Tool Plugin 的 Operation 调用。

## 实施顺序

先完成 Python Core、唯一 Plugin Manager、已发布 Skill 导入、SkillCatalog/Resolver 和 Runtime Action Boundary；通过 Echo 垂直 E2E 后，再接入 OpenAMSM Plugin、Tool Package 和 Create → Modify → Release。没有真实证据的阶段标记 NOT_STARTED / NOT_RUN。

## Demo 范围

本仓证明机制正确性和可扩展性，不做生产级资格认证。可靠性与安全 DFX 暂不展开生产方案；不增加 HA/DR/SLA、包签名、Trust Registry、生产密钥管理或复杂多租户治理。基本输入校验、明确错误、fail-closed、Owner 结果语义、最小可观测性和自动化验收仍必须具备。
