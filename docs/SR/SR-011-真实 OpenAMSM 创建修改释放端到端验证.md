# SR-011：真实 OpenAMSM 创建修改释放端到端验证

> 文档类型：软件需求（SR）  
> SR 版本：0.2.2  
> 状态：DRAFT（SR 实施主状态）；**设计待评审 / REVIEW_REQUESTED**，未获得实施 READY，产品验收 NOT_RUN  
> 创建日期：2026-11-25  
> 修订日期：2026-11-26  
> 所属阶段：Phase H  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.2.4 §5～10；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.2 §2～12；[演示验收基线](../验收与实施/演示验收基线.md) v0.3.21 §2～10  
> Acceptance：EX-20、OM-09、OM-11、OM-12（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查同一 UE/PSI 的 Create→Modify(QoS)→Release、N1/N2/PFCP 及 Owner 原始 Receipt/UNKNOWN/Reconcile、Replay 0 mutation。
- **已知依赖与未验证项：**Next 的 Phase C～G、1.6.0 正式 MAS Bundle/Provider 和隔离联测未满足；独立 EX-20/OM NOT_RUN。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

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

设计按 F06 与验收基线审查三段消息、原 Run、Owner 结果及清理顺序。运行组合场景时消费 SR-008、009、010 和指定业务包，先记录隔离实例、初始状态及受测版本。缺环境仅暂停该次真实 OM-11，不能用 fixture 替代。 设计可按 SR 管理规范 §6.1 单独评审。

## 5. 验收条件

1. 一个真实隔离 OpenAMSM Owner/SMF 和一个 UE/PSI 完成 Create → Modify → Release。
2. N1/N2 原始字节、ArtifactRef、Run/generation 和 continuation 关联可追溯。
3. Owner Receipt/Commit Proof/Reconcile 语义正确，UNKNOWN 不提升为 COMMITTED。
4. 无重复 mutation，最终状态与响应交付一致。
5. Agent Core、Resolver、Runtime、Plugin Manager 无 OpenAMSM 业务分支。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

### 实施位置与复验入口

以下路径为本 SR 的目标交付物。在 ca-agent-next 仓根运行，测试通过公开入口调用受测组件。目标位置为 `examples/openamsm/` 与 Next 组合测试入口。先记录隔离实例、各发布资产、固定版本、专用 UE/PSI、初始会话与仅限该实例的复位命令。从 env-5gc-sim 的场景驱动保存三组私有请求身份样本：同内容同 ID 重试、不同内容同 ID 冲突、同内容新 ID 独立操作。记录请求数、响应通道与 Owner mutation 数，首组不得重复 mutation，冲突组不得新增 mutation。对同一 UE 连续运行 Create/Modify/UE Release，关联三次请求、原始 N1/N2、PFCP、Owner Receipt、原 Run/generation 与最终清理。未提供隔离配置或组件版本时入口报环境缺失并记 BLOCKED，不能用合成包通过。

验收命令为 `python -m unittest discover -s tests -p test_openamsm.py -v`。必须发现并执行本节正反例；发现 0 个测试或跳过必需用例时，退出码 0 也不能计入 PASS。逐个 Acceptance ID 回填受测 SHA、命令、预期与实测值及日志位置。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-agent-next（组合验收）。env-5gc-sim 为输入对端，读取已提供的请求/重放 fixture；需要修改对端时另按该仓 SR 登记 |
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

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史记录未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-011 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-011 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-011 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05/F06 与 Acceptance 基线版本引用 | 对齐最新 OpenAMSM 业务设计和 Artifact 边界 | Issue #12 |
| 2026-11-25 | 0.1.4 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05 设计依据至 v0.4.1；同步 Host Artifact Store v1 已冻结、Next Host 未实现和 Codec Consumer 分层状态 | 避免 SR-011 继续引用已被替代的 F05 v0.3.0 | Issue #12；F05 v0.4.1；SR-009、SR-010 |
| 2026-11-25 | 0.1.5 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F06 与 Acceptance 基线版本至 v0.2.2 / v0.2.5；同步 F05 v0.4.1 | 保证 SR-011 的集成目标、Artifact 边界和验收入口引用同一轮设计基线 | Issue #12；F05 v0.4.1；F06 v0.2.2；Acceptance v0.2.5 |
| 2026-11-25 | 0.1.6 | 未记录（历史资料未提供） | 历史记录未细分 | 将 Acceptance 基线引用更新至 v0.2.6 | 对齐演示验收基线最终修订，避免 SR-011 指向旧验收快照 | Issue #12；Acceptance v0.2.6 |
| 2026-11-25 | 0.1.7 | Codex / GPT-6 | §5 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-011 |
| 2026-11-26 | 0.1.8 | 未记录（历史资料未提供） | §5、6 | §5、6 指定隔离对端复验的实施仓与身份样本；同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.9 | Codex / GPT-6 | §4～5 | Codex / GPT-6，§4～5。分别登记设计输入、实施接入和验收依赖。 | 使 Harness 能按当前阶段判定启动与验收条件 | Issue #12、#21 |
| 2026-11-26 | 0.2.0 | GPT-6.2（ChatGPT） | 文档头部 | 将 Acceptance 设计依据更新至 v0.3.8 | 避免真实 OpenAMSM E2E 设计继续引用旧验收基线 | Issue #26 |
| 2026-11-26 | 0.2.1 | GPT-6.2（ChatGPT） | 文档头部 | 将 Acceptance 设计依据更新至 v0.3.9 | 与 SR-002 集成后当前演示验收基线保持一致 | PR #25；Issue #26 |
| 2026-11-26 | 0.2.2 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
