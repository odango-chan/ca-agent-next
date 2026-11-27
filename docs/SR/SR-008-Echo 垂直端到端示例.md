# SR-008：Echo 垂直端到端示例

> 文档类型：软件需求（SR）  
> SR 版本：0.2.2\
> 状态：DRAFT（实施主状态）；第二轮独立评审 CHANGES_REQUESTED（历史结论）；第三轮自评 **DESIGN_READY_FOR_INDEPENDENT_REVIEW**（仅设计评审候选，非独立批准或实施 READY）；产品 AC NOT_RUN/BLOCKED。
> 创建日期：2026-11-25  
> 修订日期：2026-11-27\
> 所属阶段：Phase F  
> 上游需求：[IR-004](../IR/IR%20总登记册.md#ir-004)  
> 设计依据：[演示验收基线](../验收与实施/演示验收基线.md) v0.3.24 §1～6；[实施路线与阶段门槛](../验收与实施/实施路线与阶段门槛.md) v0.2.15 §6\
> Acceptance：EX-17（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查一个 Go Plugin 组合 Event/Tool/Delivery、指导型与 Assurance Skill 的同链路、正反向和失败案例。
- **已知依赖与未验证项：**Echo 的新 Assurance Bundle 需要 1.6.0 重编译发布；旧版 Example/编译脚本不算新系统验收，EX-17 NOT_RUN。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

## 1. 目标

以业务中立 Echo 验证 Python Core、唯一 Plugin Manager、两种 Skill 形态、Resolver、Runtime 和 Delivery 的完整链路。

## 2. 实施范围

- 一个 Go Plugin 同时暴露 Event、Delivery 和 Tool。
- 一个 SKILL.md-only Skill 走 LLM-guided。
- 一个含有效发布 Assurance Artifact 的 Skill 验证 Deterministic 和 LLM-guided。
- 覆盖导入、选择、Action Scope、Outcome/Evidence 和响应交付。

## 3. 非目标

- 不引入 OpenAMSM 业务代码。
- 不以单元测试代替垂直 E2E。

## 4. 依赖与分阶段门槛（遵循 SR 管理规范 §6.1）

| 依赖类型 | 权威输入 | 适用门槛 |
|---|---|---|
| 设计 | F02/F03/F04/F08 与 SR-029 的 Skill/Tool/Run 统一目标 | 仅业务中立 Echo，公开 Capability 对应唯一 Callable |
| 实施 | SR-002/003 模块、SR-004～007 目标实现及 Echo Go Plugin 固定源码 | 独立的 Plugin 协议/LLM-only 子路径可先验收 |
| 模块验收 | SR-027 正式 1.6.0 Echo Assurance Bundle 和新 Compiler Verify 证据 | 阻塞 AC-008-02/03 的 双模式组合验收，不阻塞 SKILL-only 子用例 |
| 系统 EX | EX-17 与 Echo 完整系统组合 | 只在全部组件真实启动后才能报告系统 E2E PASS |

**设计评审与实施 READY 独立判定**：本 SR 的功能职责、已知目标契约、失败路径和下面每项模块 AC 足够完整即可请求设计评审；不得要求“全部前置 SR VERIFIED”作为统一前置。实际实施按本次 Scope 逐阶段检查所消费的已发布能力；缺失时仅相应 AC 标记 BLOCKED/NOT_RUN，系统 EX/OM 不倒灌模块门禁。Owner/Provider/Compiler 的未知机器标识、Schema 和 API 只能由对应 Owner 正式发布，Harness 不得推测。新 Skill/Artifact/Runtime 接口只接受 CA-SL 1.6.0 / Capability-first，不提供旧版兼容。

## 5. 独立模块验收条件（正例、反例与证据）

| 模块 AC | 固定输入/操作 | 预期、诊断与隔离 |
|---|---|---|
| AC-008-01 | 同一个 Go Plugin 暴露 Event/Tool/Delivery，SKILL.md-only Skill + Fake Model | 完成 Event→Skill→Run→文本 Delivery；无需 Compiler，未授权 Tool Action 拒绝 |
| AC-008-02 | 同一正式 1.6.0 Echo Assurance Bundle 的 Deterministic 模式 | 按已发布 Capability Binding 精确一次 Tool dispatch；以 Invocation 和 correlation 关联 READ Observation、返回 text=hello 和 Delivery。此 READ 无 Owner mutation 或 Commit Proof |
| AC-008-03 | 同一 1.6.0 Bundle 用 LLM-guided 模式请求合法与越权 Capability | 合法 Tool 走与确定性模式相同 Action Boundary；越权请求 IPC=0 |
| AC-008-04 | 重试 Event、丢失或错 correlation、超时/取消、旧 Artifact | 同 ID 同内容复用原 Run，重放新增 Tool dispatch=0；同 ID 异内容冲突无新增 Run；错 correlation、超时、取消后的迟到响应均拒绝交付。旧 Artifact 导入失败 |
| AC-008-05 | 独立进程 Host + Go Plugin + 两种发布包在固定环境组合运行 | 记录组件受测 SHA、真实调用/Delivery、Go 进程退出/临时目录清理；系统 EX-17 另行按完整标准验收 |

### 5.1 实现落点、运行和取证

**独立进程入口（SR-008 拟交付）**。当前 Next CLI 仅提供 `--smoke`。在 Example 中交付通用 Host 的薄启动器 `examples.echo.run`，使用真实 Host、Catalog、Plugin Manager 和子进程，Fake Model 只用于可重复选择。启动器不得在 Core 增加 Echo 分支。命令均从 Next 仓根执行。

| 步骤 | 命令或判据 |
|---|---|
| 构建插件 | 使用 Go 1.26.6（模块 go 1.24），记录 go version。Bash 设置 `export GOWORK=off`，PowerShell 设置 `$env:GOWORK='off'`。从仓根运行 `go -C examples/echo/plugin build -trimpath -o bin/echo-plugin .`，Windows 输出改为 bin/echo-plugin.exe。 |
| 部署与启动 | 启动器的 --skills 指向本批包父目录，--interface 指向同批正式 Echo Interface 解包根。按 Plugin manifest 声明的包身份核对导出及唯一 Binding。三个 --scenario 值和命令见下文；all 必须逐个启动新的 Host 和 Go Plugin。 |
| 就绪与取证 | 每场景记录实际 Host/Plugin PID、Skill/Artifact 身份、模式、模型 fixture 消费记录、Run、Invocation、dispatch、Delivery、退出码及临时目录回收。5 秒内收到匹配的 plugin.ready，30 秒内完成每场景；任何缺项返回 1。 |
| 退出 | 全部必需断言通过且 Plugin 正常关闭返回 0；运行错误、超时或证据缺失返回 1，非法 CLI 返回 2。所有分支回收子进程及临时目录。 |

**启动器参数与受测场景（待 SR-008 实施）**。从仓根新建 venv。令 ECHO_SKILLS 指向本次解包后的父目录，ECHO_INTERFACE 指向生产者交付的正式 Interface 根。以下相对部署位置由验收者从同批发布物物化。

```bash
export ECHO_SKILLS="$PWD/examples/echo/published-skills" ECHO_INTERFACE="$PWD/examples/echo/interface"
python -m venv .venv-echo
.venv-echo/bin/python -m pip install -e '.[plugins]'
.venv-echo/bin/python -m examples.echo.run --scenario all --model-fixture examples/echo/scenarios/model.json --plugin examples/echo/plugin/plugin.yaml --skills "$ECHO_SKILLS" --interface "$ECHO_INTERFACE" --timeout 30
```

```powershell
$env:ECHO_SKILLS = Join-Path $PWD 'examples/echo/published-skills'
$env:ECHO_INTERFACE = Join-Path $PWD 'examples/echo/interface'
python -m venv .venv-echo
.\.venv-echo\Scripts\python.exe -m pip install -e '.[plugins]'
.\.venv-echo\Scripts\python.exe -m examples.echo.run --scenario all --model-fixture examples/echo/scenarios/model.json --plugin examples/echo/plugin/plugin.yaml --skills $env:ECHO_SKILLS --interface $env:ECHO_INTERFACE --timeout 30
```

| --scenario | 独立输入、模型夹具与验收 |
|---|---|
| guide | 仅激活 echo-guide，输入 echo.request / hello。脚本模型选择该 Skill 并返回 hello；Tool dispatch=0，关联 Delivery 一次。 |
| deterministic | 仅激活 echo-assured，使用其已发布 Artifact。执行路径不取模型动作，恰好一次 READ，观察与 Delivery 均为 hello。 |
| guided | 激活与 deterministic 相同的 echo-assured。模型脚本先用正式 Binding 中的 Capability 发起 READ，再返回 hello；另起负例 Run 提议未绑定 Capability，新增 Tool IPC=0。 |

scenarios/model.json 是 SR-008 将交付的本地脚本夹具，按场景给出有序模型响应；合法 Capability 从已验证的部署 Binding 注入。响应耗尽、多余调用、模式/Skill 与期望不符均失败。部署前构建 Go，运行时用绝对路径启动 Host/Plugin，仅传系统启动必需变量及隔离临时目录，清除 PYTHONPATH、Compiler 路径和凭据。记录 Host 及子进程的实际启动命令，允许的子进程只有所选 Go Plugin，Compiler 启动数必须为零。all 要求三份独立证据齐备且必需跳过数为零。

当前启动器、正式包及上游模块齐备前，AC-008-05 / EX-17 保持 BLOCKED。单元测试入口：`python -m unittest discover -s tests -p test_echo.py -v`。若实现前目标仓文件/命令尚未存在，由具体实施 PR 在模块范围内创建并登记，**不得以不存在的脚本退出 0 或 0 discovered tests 作为 PASS**。
- 单元 fixture 仅验证本模块行为。Assurance 两种模式及 EX-17 使用同批 SR-027 Bundle 和 Echo Interface；READ 取证使用原始 Observation、Invocation 和 Delivery。
- 每项 AC 单独记录受测代码 SHA、设计 Head、外部 Package/Schema/API 版本、命令、环境、测试数量、预期/实测、失败诊断与证据路径。未执行始终 NOT_RUN；输入缺失标记 BLOCKED；系统 EX/OM 必须用独立组合证据交付。

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

### Echo 的外部交付

首批可执行 Echo 的作者源、固定 Compiler 和 Bundle 候选由 [SR-027](SR-027-技能Bundle构建与发布.md) 交付。测试 Host 与 Plugin 的协议 fixture 可以先验收。正式组合用例必须使用同一资产。


## 修订记录


| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史记录未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-008 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-008 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-008 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史记录未细分 | 校正当前设计依据版本 | 核对 Issue #12 与固定提交 | SR-008 |
| 2026-11-25 | 0.1.4 | Codex / GPT-6 | §5 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-25 | 0.1.5 | Codex / GPT-6 | §5 | Codex / GPT-6 · §5 明确 Echo 输入的发布方、缺件和恢复条件 | 对齐当前架构与实施门禁 | Issue #12 SR-008 |
| 2026-11-26 | 0.1.6 | 未记录（历史资料未提供） | 历史记录未细分 | 对齐外部 Echo 生产端 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.7 | Codex / GPT-6 | §4～5 | Codex / GPT-6，§4～5。分别登记设计输入、实施接入和验收依赖。 | 使 Harness 能按当前阶段判定启动与验收条件 | Issue #12、#21 |
| 2026-11-26 | 0.1.8 | GPT-6.2（ChatGPT） | §1 | 将 Acceptance 设计依据更新至 v0.3.8 | 避免 Echo 设计继续引用过期验收版本 | Issue #26 |
| 2026-11-26 | 0.1.9 | GPT-6.2（ChatGPT） | 文档头部 | 将 Acceptance 设计依据更新至 v0.3.9 | 与 SR-002 集成后当前演示验收基线保持一致 | PR #25；Issue #26 |
| 2026-11-26 | 0.1.10 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.1.11 | GPT-6（ChatGPT） | §4～§5 | 按治理 §6.1 拆分设计/实施/模块/系统依赖；补齐 AC-008-xx 正反验收 | 解除全局 VERIFIED 门槛与缺模块 AC 问题，避免 Harness 猜测/EX 倒灌 | Issue #12/#40；PR #46；SR 管理规范 §6.1 |
| 2026-11-27 | 0.2.0 | Codex / GPT-6 | §5.1 | 定义独立进程 Echo 的命令、时限和退出条件 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.1 | Codex / GPT-6 | AC-008-01～05、§5.1 | 规定三场景入口、READ 证据、干净进程与双平台运行方式 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.2 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | guide/deterministic/guided 三种独立进程场景、READ 与越权零分发可按文档复核；同批正式 Echo 发布物尚缺；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-008 |
