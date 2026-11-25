# SR-011：真实 OpenAMSM 创建修改释放端到端验证

> 文档类型：软件需求（SR）  
> SR 版本：0.1.3  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase H  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.2.1 §5～10；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.3.0 §2～12；[演示验收基线](../验收与实施/演示验收基线.md) v0.2.3 §2～10  
> Acceptance：EX-20、OM-09、OM-11、OM-12（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

在 Echo 通过后，以 OpenAMSM 作为第二个业务证明，完成真实隔离环境下 Create → Modify → UE-requested Release。

## 2. 实施范围

- 通过 Next Host、OpenAMSM Event Plugin、Skill 和 ca-client-tools Tool Plugin 串联 Create/Modify/Release。
- 使用一个 UE/PSI，保留 N1/N2 原始 Artifact 和 Run/continuation 关联。
- 验证 Owner Receipt/Commit Proof、UNKNOWN、Reconcile 和零重复 mutation。
- 证明新增业务只需 Plugin、Skill、Tool Interface Package 和部署配置，不修改 Core。

## 3. 非目标

- Synthetic Owner 或 fixture 通过不等于真实隔离 E2E。
- 不声明 Production Qualification。

## 4. 依赖与前置条件

SR-008、SR-009、SR-010；外部依赖为真实 OpenAMSM、ca-client-tools 和所需 Skill 发布物。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. 一个真实隔离 OpenAMSM Owner/SMF 和一个 UE/PSI 完成 Create → Modify → Release。
2. N1/N2 原始字节、ArtifactRef、Run/generation 和 continuation 关联可追溯。
3. Owner Receipt/Commit Proof/Reconcile 语义正确，UNKNOWN 不提升为 COMMITTED。
4. 无重复 mutation，最终状态与响应交付一致。
5. Agent Core、Resolver、Runtime、Plugin Manager 无 OpenAMSM 业务分支。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-agent-next |
| GitHub Issue | 未创建 |
| 实施 PR | 未创建 |
| Commit | 无 |
| 实施状态 | NOT_STARTED |
| 验收证据 | NOT_RUN |

ca-agent-next PR #1 是设计基线 PR，不是本 SR 的实现 PR，不得在此标记实施完成。

## 7. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：初始分解；等待设计基线评审。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续发生语义变化时创建新的 SR 并引用本 SR，不覆盖历史要求。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-011 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-011 |
| 2026-11-25 | 0.1.2 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-011 |
| 2026-11-25 | 0.1.3 | 更新 F05/F06 与 Acceptance 基线版本引用 | 对齐最新 OpenAMSM 业务设计和 Artifact 边界 | Issue #12 |
