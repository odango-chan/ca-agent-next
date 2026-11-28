# SR-011：真实 OpenAMSM 创建修改释放端到端验证

> 文档类型：软件需求（SR）  
> SR 版本：0.3.4\
> 状态：整项 DRAFT；限定设计已认可，等待直接依赖。AC-011-06 静态架构断言。  
> 下一步：已获限定设计认可。组合实现具备后检查 Core 零业务分支；01～05 等同批 Bundle、Compiler Verify、Provider/Owner Package 和隔离对端。  
> 阶段依据：[独立评审 #75](https://github.com/odango-chan/ca-agent-next/issues/75#issuecomment-7210271472)，评审 Head `ee73ad48f9cf4132561f7a72065086ef00bb3606`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。
> 创建日期：2026-11-25  
> 修订日期：2026-11-27\
> 所属阶段：Phase H  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.3.1 §4.1、§5～10；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.5 §2～12；[演示验收基线](../验收与实施/演示验收基线.md) v0.3.24 §2～10\
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

## 4. 依赖与分阶段门槛（遵循 SR 管理规范 §6.1）

| 依赖类型 | 权威输入 | 适用门槛 |
|---|---|---|
| 设计 | F06 / F04 / F05、SR-029 1.6.0 Capability/Owner 语义和最新验收基线 | 设计阶段确认 Owner/Host/Plugin 和 Run 权威边界 |
| 实施 | SR-008 Echo 组合、SR-009 Event Plugin、SR-010 Provider+Artifact、Owner/Simulator 隔离环境 | 真实完整 E2E 要有各组件模块证据与明确环境 |
| 模块验收 | 实际 ca-skills 1.6.0 MAS 三份 Skill Bundle、Compiler Verify、Owner Receipt/Commit Proof、Mock AMF、PFCP/N1/N2 | 阻塞真实运行型 AC；不能以历史 Demo 环境或 synthetic fixture 代替 |
| 系统 EX/OM | EX-20、OM-09/11/12，真实 SMF/UE 隔离实例 | 系统 EX/OM 证据必须在全部模块 AC 后单独登记 |

**设计评审与实施 READY 独立判定**：本 SR 的功能职责、已知目标契约、失败路径和下面每项模块 AC 足够完整即可请求设计评审；不得要求“全部前置 SR VERIFIED”作为统一前置。实际实施按本次 Scope 逐阶段检查所消费的已发布能力；缺失时仅相应 AC 标记 BLOCKED/NOT_RUN，系统 EX/OM 不倒灌模块门禁。Owner/Provider/Compiler 的未知机器标识、Schema 和 API 只能由对应 Owner 正式发布，Harness 不得推测。新 Skill/Artifact/Runtime 接口只接受 CA-SL 1.6.0 / Capability-first，不提供旧版兼容。

## 5. 独立模块验收条件（正例、反例与证据）

| 模块 AC | 固定输入/操作 | 预期、诊断与隔离 |
|---|---|---|
| AC-011-01 | 固定隔离环境、各组件/Package Release SHA、UE/PSI、场景前 Session 状态 | 环境/资产完整才启动；缺任何新 1.6.0 包则 BLOCKED 而不是合成包 PASS |
| AC-011-02 | 真实 Create，随后同 UE/PSI Modify（含 QoS）与 UE-requested Release | Owner 与 SMF 状态、N1/N2/PFCP、三次请求/响应身份及最终 Release 状态精确匹配 |
| AC-011-03 | 同 ID 同内容重试、同 ID 不同内容冲突、同内容新 ID 独立 Invocation | 首项无重复 mutation；冲突不变更；新 ID 只按真实 Owner/Scope 规则执行，不串入旧 Run |
| AC-011-04 | 响应丢失、Owner UNKNOWN；对同一 releaseTxn 分别执行 N1→N2、N2→N1 两种到达顺序；两笔并发事务 A/B 的 N1-A→N2-B→N1-B→N2-A 交错；重复、迟到 N1/N2；旧 generation、错 smContextRef、错 Session、互换两路 Receipt/Proof；执行精确 Reconcile | UNKNOWN 不提升 COMMITTED；只有同一 Run、同一 Owner generation/releaseTxn、正确 SUPI/PSI 且各自 originalInvocationId/Proof/Scope 全匹配的 N1 与 N2 两路确认都成立后才允许清理。单路、乱序、交错、重复、迟到、旧代际或错 Session 均不得误确认/触发清理，新增 mutation=0；旧代际明确返回 `STALE_SM_CONTEXT`，不污染新 generation。 |
| AC-011-05 | 原始 N1/N2 Artifact bytes、Run/generation、continuation 与本次 callback responseObligation；重放旧 generation/context 的 N1 与 N2 回调 | 所有引用同一实际请求；跨 Run/旧 generation 被拒并返回 `STALE_SM_CONTEXT`，不清理、不新增 mutation；当前 callback 的 responseObligation 与原 Run 执行身份分离；最终 Delivery/SMF projection 一致 |
| AC-011-06 | 静态与运行追踪检查 Agent Core/Resolver/Plugin Manager 源码 | 无 OpenAMSM 业务条件分支；新增业务只改变 Plugin/Skill/Package/部署配置；系统 EX/OM 单独复验 |

### 5.1 实现落点、运行和取证

**隔离联测**。环境命令按 env-openamsm `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`、env-5gc-sim `6ba1dc47049013e19d93222fb308ffead7eb4c0e` 登记。每次从干净隔离实例开始，只操作该实例。记录实际 checkout SHA、配置路径、监听地址与 logs。以下为 Bash 命令。

| 阶段和工作目录 | 命令和通过条件 |
|---|---|
| 资产，Next | 由联测配置给出已物化的五个路径。执行 `for p in "${CREATE_BUNDLE:?}" "${MODIFY_BUNDLE:?}" "${RELEASE_BUNDLE:?}" "${PROVIDER_PACKAGE:?}" "${OWNER_PACKAGE:?}"; do test -e "$p" \|\| exit 1; done`。再按正式 Manifest 逐一核对 release identity、Schema-only 闭包、Compiler Verify 记录与部署快照；任一不符则停止。|
| NF，env-openamsm | 依次运行 `./bin/env-openamsm doctor`、`./bin/env-openamsm verify-upstream`、`./bin/env-openamsm build`、`./bin/env-openamsm configure --profile local`、`sudo ./bin/env-openamsm start --profile local`。配置时由隔离环境提供 ENV_OPENAMSM_QUERY_TOKEN。|
| NF 就绪 | `./bin/env-openamsm status` 后运行 `./bin/env-openamsm smoke`；记录 SCP/SMF/UPF、Owner build identity 与本轮 UE/PSI 的无会话前态。局部 smoke 成功只满足环境预检。|
| Peer，env-5gc-sim | `go build -o mock-amf ./cmd/mock-amf`；`./mock-amf run --config "${MOCK_AMF_CONFIG:?}" --scenario "${LIFECYCLE_SCENARIO:?}" --json`。配置必须走 SCP 指向本轮 Next 入口，使用同一 UE/PSI，保存回调、PFCP 和 Owner 证据。|
| 清理/隔离 | 停止接收新请求，先排空旧 listener 的在途回调并轮换 listener（记录旧/新地址及排空完成），再对隔离测试 peer 使用 `curl --fail --http2-prior-knowledge -H 'Content-Type: application/json' -d '{"reuseKeys":true}' "${PEER_URL:?}/mock-amf/v1/reset"`，断言 generation 前进；使用旧 generation/context 的回调得到 STALE_SM_CONTEXT 且零 mutation，再以同一 SUPI/PSI 创建新会话。无法证明排空时使用全新进程、listener 和空状态；进程已退出时使用新监听地址/空状态启动下一轮。回收本轮 Host 和 peer，运行 `sudo ./bin/env-openamsm stop`。NF 停止或 peer reset 均不能充当 Owner 释放证据。|

真实 Next 部署配置、同一批 1.6.0 资产及指向它们的 lifecycle scenario 尚缺；AC-011-01～06 保持 BLOCKED。禁止用旧快照重放或单元测试替代。

- 目标实现：`examples/openamsm/ 与 Next 公开组合验收入口`；测试入口：`python -m unittest discover -s tests -p test_openamsm.py -v`。若实现前目标仓文件/命令尚未存在，由具体实施 PR 在模块范围内创建并登记，**不得以不存在的脚本退出 0 或 0 discovered tests 作为 PASS**。
- 使用本 SR 明示的最小正负例与计数型测试 Provider/Mock；真实 Publisher、新 Compiler、Owner 收据、隔离环境等数据只从固定 SHA 的正式发布物读取。模拟输入能验证本地行为，但**不能替代**要求正式外部源的 AC。
- 每项 AC 单独记录受测代码 SHA、设计 Head、外部 Package/Schema/API 版本、命令、环境、测试数量、预期/实测、失败诊断与证据路径。未执行始终 NOT_RUN；输入缺失标记 BLOCKED；系统 EX/OM 必须用独立组合证据交付。

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
| 2026-11-26 | 0.2.3 | GPT-6（ChatGPT） | §4～§5 | 按治理 §6.1 拆分设计/实施/模块/系统依赖；补齐 AC-011-xx 正反验收 | 解除全局 VERIFIED 门槛与缺模块 AC 问题，避免 Harness 猜测/EX 倒灌 | Issue #12/#40；PR #46；SR 管理规范 §6.1 |
| 2026-11-26 | 0.2.4 | GPT-6（ChatGPT） | 文档头、设计依据 | 同步本次 1.6.0 实质整改后的权威 Feature/Compiler 文档版本 | 保证 SR 新旧规范引用与固定审核 Head 一致 | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.3.0 | Codex / GPT-6 | §5.1、AC-011-04/05 | 登记隔离环境入口与逐路确认收据 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.1 | Codex / GPT-6 | §5.1 | 隔离复用 SUPI/PSI 前排空并轮换 listener，验证过期回调 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.2 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | 隔离真实 NF、旧 listener 排空、新 generation/key reuse 与两路 Owner Proof 的场景及停止条件已写明；真实组合输入未齐；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-011 |
| 2026-11-27 | 0.3.3 | GPT-6（ChatGPT） | AC-011-04/05、文档头、修订记录 | 增加 N1/N2 两种顺序、跨事务交错、迟到回调、旧 generation 和错 Session 的独立断言；将 STALE_SM_CONTEXT 映射到模块 AC | 处理独立模型 Review #6082541121 的 P1 R3-SR011-01，避免仅覆盖重复/迟到 N2 而漏掉乱序和交错清理 | Issue #12；PR #46；F06 v0.3.1；Review #6082541121 |
| 2026-11-27 | 0.3.4 | Codex / GPT-6 | 文档头 | 登记限定设计已认可，等待直接依赖及 AC 范围 | 按单项独立评审推进 | Issue #12、#75；PR #46 |
