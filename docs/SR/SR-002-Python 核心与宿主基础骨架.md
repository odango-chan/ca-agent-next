# SR-002：Python 核心与宿主基础骨架

> 文档类型：软件需求（SR）  
> SR 版本：0.2.0  
> 状态：DRAFT；本轮设计修订待评审，不允许代码实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase A  
> 上游需求：[IR-002](../IR/IR%20总登记册.md#ir-002)  
> 设计依据：[CA Agent Next 架构设计](../架构设计/CA%20Agent%20Next%20架构设计.md) v0.4.3 §3～5；[通用 Agent Core 与 Host 设计说明书](../设计说明书/F01-通用Agent核心与Host/通用Agent核心与Host设计说明书.md) v0.3.0 §2～5  
> Acceptance：AC-002-01～AC-002-08（本 SR 模块验收）；EX-01（系统级验收，不作为本 SR 的独立门禁，见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

建立业务中立的 Python Agent Core / Host 最小骨架，提供可安装的 Python 包、稳定的 Host 公开入口和可注入的 Model Client，使一次规范化 Event 能经过最小 Model Loop 并返回结构化 Model Proposal。

本 SR 只交付 Host + Model Loop 基础切片。Model Proposal 是未执行的提议，不代表 Tool 调用、Runtime Outcome 或 Owner 提交。

## 2. 实施范围

### 2.1 Python 包与入口

- Distribution 名称：`ca-agent-next`。
- Import package：`ca_agent_next`。
- 源码根目录：`src/ca_agent_next/`。
- 最小模块：
  - `__init__.py`：包身份与公开导出。
  - `__main__.py`：`python -m ca_agent_next --smoke` 入口。
  - `contracts.py`：Event、Context、Run、ModelRequest、ModelProposal、HostResult。
  - `model_client.py`：ModelClient Protocol。
  - `model_loop.py`：AgentLoop。
  - `host.py`：Host。
- 项目根目录提供 `pyproject.toml`；使用 src layout 和 setuptools build backend。
- Python 元数据声明 `requires-python = ">=3.11"`。本批固定验收解释器为 CPython 3.14.6；一次本机验收不代表已验证整个版本范围。
- 本 SR 的运行时代码只使用 Python 标准库；不增加运行时第三方依赖。

### 2.2 公共类型与调用边界

F01 §5.1～5.5 定义以下公开类型和方法，SR-002 按该定义实现，不自行改名或增加第二套契约：

- `Event`：规范化事件，含 event_id、ingress_id、event_type、payload，以及可选 external_request_id、response_channel_id、source、opaque artifact_refs。
- `Context`：本次调用可见的最小上下文值；不在本 SR 定义 Observation/Evidence 或 ArtifactStore 语义。
- `Run`：本次调用的 run_id 与 event_id；不在本 SR 实现持久化、Continuation 或状态机。
- `ModelRequest`：Run、Event 和 Context 的只读组合。
- `ModelProposal`：模型提议的 kind 与 payload；不表示已执行 Action。
- `HostResult`：Run 与 ModelProposal。
- `ModelClient`：由调用方注入的同步 Protocol，方法为 `propose(request: ModelRequest) -> ModelProposal`。
- `AgentLoop`：构造时注入 ModelClient；`run_once(request)` 对 ModelClient 调用恰好一次，不重试。
- `Host`：构造时注入 ModelClient；公开 `handle_event(event: Event) -> HostResult`。Host 创建最小 Run/Context 并调用 AgentLoop。

Host 不创建真实模型客户端、不读取 Provider/Gateway 环境变量、不拥有注入 ModelClient 的资源生命周期。ModelClient 由应用组合入口创建和管理。测试使用 Fake ModelClient。

### 2.3 Host 最小处理流程

1. 接收已规范化 Event。
2. 校验必需字段和基础类型；无效输入返回明确错误，不调用 ModelClient。
3. 创建本次 Run 和最小 Context。
4. 构造 ModelRequest。
5. AgentLoop 调用注入的 ModelClient 一次。
6. 校验 ModelProposal 的类型与必需字段。
7. 返回 HostResult。

SR-002 不实现 Event 去重、Continuation、Skill 选择、Plugin 分发、Artifact staging/store、Runtime 执行、Owner Outcome 或持久化；这些由后续 SR 和对应 Feature 设计负责。Event 的 artifact_refs 在本 SR 中只作为不透明引用保留，不读取或传输原始字节。

## 3. 非目标

- 不迁移或复制整个 ca-agent-demo。
- 不引入 OpenAMSM、5GC、SBI、NAS、NGAP 或其他业务专用逻辑。
- 不实现 Plugin Manager、Skill Importer、SkillCatalog、Resolver、Runtime、Tool dispatch 或 Owner 状态机。
- 不实现真实模型 Provider、HTTP/Gateway 客户端、API Key、模型选择配置或重试。
- 不内置 Compiler，不读取 Skill 作者源，不执行 Skill。
- 不引入生产级 DFX、包签名、额外 SHA-256、Trust Registry 或 Skill Admission。
- 不把 Model Proposal 当作可执行 Action 或 COMMITTED 结果。

## 4. 依赖与前置条件

- SR-002 没有前置 SR 依赖；可独立实施和验收。
- SR-003 依赖 SR-002 VERIFIED，并复用 F01 定义的 Event、Host.handle_event、HostResult 和 ModelClient 注入边界。
- EX-01 是系统级语言/装配门槛，需等待 SR-002、SR-004、SR-005、SR-006、SR-007 各自模块验收完成后联合执行；EX-01 不阻塞 SR-002 的独立验收。
- ca-agent-demo 仅为只读参考：main SHA `57e277ff9094dad93543df46910a12a1dbbaf560`。可参考 `pyproject.toml` 的 src layout、`src/ca_agent_host/agent/model_adapter.py` 的 Protocol 注入方式和 `tests/unit/chat_model_fakes.py` 的调用记录 Fake；不得复制其 distribution `ca-agent-host`、import package `ca_agent_host`、CLI `ca-plan`、完整 Resident/Runtime 或业务实现。参考仓 PASS 不计为 Next 验收证据。

## 5. 模块验收

本 SR 的独立验收为 AC-002-01～AC-002-08，详细通过条件见[演示验收基线 §3.1](../验收与实施/演示验收基线.md)。至少执行以下命令：

```text
python -m pip install -e .
python -c "import ca_agent_next; from ca_agent_next.host import Host; from ca_agent_next.model_client import ModelClient"
python -m ca_agent_next --smoke
python -m unittest discover -s tests -p "test_host.py" -v
```

测试必须覆盖正常路径和失败路径；unittest 必须实际发现并执行测试。输出 `Ran 0 tests`、跳过必需用例或只执行导入检查，均不能计为 PASS。

### 5.1 固定 Smoke 契约

- 命令：`python -m ca_agent_next --smoke`。
- Smoke 固定 Event：
  - event_id：`smoke-event-001`
  - ingress_id：`smoke`
  - event_type：`ca-agent-next.smoke`
  - payload：`{"message":"hello"}`
  - source：`{"protocol":"smoke","peer_id":"local"}`
- Smoke 使用进程内 Fake ModelClient，不读取真实 Provider 配置、不访问网络、不要求 API Key。
- Fake 返回 ModelProposal：kind 为 `smoke.echo`，payload 为 `{"message":"smoke-ok"}`。
- 成功 stdout 为单行紧凑 JSON，字段集合和类型固定：

```json
{"schema_version":1,"status":"ok","event_id":"smoke-event-001","model_calls":1,"proposal":{"kind":"smoke.echo","payload":{"message":"smoke-ok"}}}
```

- 成功退出码为 0；成功时 stderr 为空；stdout 不得混入日志、调试信息或额外文本。
- 失败时 stdout 为空；stderr 只输出一行 JSON 诊断：

```json
{"schema_version":1,"error":{"code":"MODEL_CLIENT_FAILED","message":"model client failed"}}
```

- 稳定错误码：`CLI_USAGE_ERROR`、`EVENT_INVALID`、`MODEL_CLIENT_FAILED`、`MODEL_PROPOSAL_INVALID`、`HOST_INTERNAL_ERROR`。
- CLI 参数/调用方式错误退出码为 2；Host、ModelClient 或 Proposal 运行失败退出码为 1。失败不得输出 traceback、凭据、token 或完整敏感请求内容。
- `model_calls` 由 Fake ModelClient 的调用记录产生；必须等于 1。不得用 Host 自报计数替代 Fake 的实际调用记录。

## 6. 实施位置与复验入口

目标交付位置：

```text
pyproject.toml
src/ca_agent_next/
  __init__.py
  __main__.py
  contracts.py
  model_client.py
  model_loop.py
  host.py
tests/
  test_host.py
```

在仓库根目录执行第 5 节命令。测试通过公开入口调用受测组件，不直接调用私有 helper。Fake ModelClient 必须记录收到的 ModelRequest、调用次数和返回值/异常，以便断言一次输入恰好一次模型调用。

## 7. 实施关联与状态

| 项目 | 当前值 |
|---|---|
| 设计修订 Issue | [ca-agent-next #19](https://github.com/odango-chan/ca-agent-next/issues/19) |
| 设计评审 PR | 本 Issue 对应的 Draft PR，创建后回填 |
| 实施 Issue | 尚未创建；SR-002 达到 READY 后再创建 |
| 实施仓库 | ca-agent-next |
| 实施 PR / Commit | 无 |
| 实施状态 | NOT_STARTED |
| AC-002-01～AC-002-08 | NOT_RUN |
| EX-01 系统级验收 | NOT_RUN |

本轮文档修订、Issue 和设计 PR 不代表代码已实施。SR-002 在设计评审通过、范围/依赖/验收完整后才可转为 READY。

## 8. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：将原先直接引用的 EX-01 拆分为 SR-002 自身 AC-002-01～AC-002-08 与系统级 EX-01；不改变 F01 业务中立边界，不把 SR-004/005/006/007 的责任移入 SR-002；为 SR-003 固定 Host 公共复用入口。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续改变既有范围、接口或验收时，按 SR 管理规范创建替代 SR，不覆盖历史要求。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-002 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实文档命名规范 | SR-002 |
| 2026-11-25 | 0.1.2 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-002 |
| 2026-11-25 | 0.1.3 | 校正当前设计依据版本 | 核对 Issue #12 与固定提交 | SR-002 |
| 2026-11-25 | 0.1.4 | 固定目标代码位置、复验入口及可观察断言 | 对齐当前架构与实施门禁 | Issue #12 |
| 2026-11-26 | 0.1.5 | 同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.0 | 将 EX-01 明确为系统级门槛；新增 AC-002-01～AC-002-08、固定 Smoke 输入/输出/错误码、ModelClient 注入和 SR-003 复用边界 | 使 SR-002 可独立实施和验收，避免被后续模块阻塞 | Issue #19；IR-002；SR-003 |
