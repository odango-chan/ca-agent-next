# SR-002：Python 核心与宿主基础骨架

> 文档类型：软件需求（SR）  
> SR 版本：0.2.14  
> 修订日期：2026-11-26  
> 状态：VERIFIED；实现已集成，AC-002-01～AC-002-08 全部 PASS；EX-01 NOT_RUN  
> 创建日期：2026-11-25  
> 所属阶段：Phase A  
> 上游需求：[IR-002](../IR/IR%20总登记册.md#ir-002)  
> 设计依据：[CA Agent Next 架构设计](../架构设计/CA%20Agent%20Next%20架构设计.md) v0.4.3 §3～5；[通用 Agent Core 与 Host 设计说明书](../设计说明书/F01-通用Agent核心与Host/通用Agent核心与Host设计说明书.md) v0.3.6 §2～5  
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
  - `__init__.py`：导出本节列出的全部公共类型，并按下列顺序固定 `__all__`：`JSONValue`、`Event`、`Context`、`Run`、`ModelRequest`、`ModelProposal`、`HostResult`、`ModelClient`、`AgentLoop`、`Host`、`HostError`。
  - `__main__.py`：`python -m ca_agent_next --smoke` 入口。
  - `contracts.py`：JSONValue、Event、Context、Run、ModelRequest、ModelProposal、HostResult、HostError。
  - `model_client.py`：ModelClient Protocol。
  - `model_loop.py`：AgentLoop。
  - `host.py`：Host；从 `contracts.py` 导入并重导出 HostError，不重新定义。
- 项目根目录 `pyproject.toml` 固定以下构建与项目元数据；不得自行改用其他构建后端或增加运行时依赖：

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "ca-agent-next"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]
include = ["ca_agent_next*"]
```

- 本批固定验收解释器为 CPython 3.14.6；一次本机验收不代表已验证整个版本范围。
- 本 SR 的运行时代码只使用 Python 标准库；`setuptools` 仅为构建依赖，不是运行时依赖。

### 2.2 公共类型与调用边界

F01 v0.3.6 §5.1～5.5 定义以下公开类型和方法，SR-002 按该定义实现，不自行改名或增加第二套契约：

- `JSONValue`：递归 JSON 值；允许 `None`、`bool`、`int`、有限 `float`、`str`、`list[JSONValue]` 和 `Mapping[str, JSONValue]`。拒绝非有限浮点数、非字符串对象键、循环容器、bytes、Path、Decimal 和任意 Python 对象；校验布尔值时不得将其误判为整数。
- `Event`：冻结 dataclass；`event_id`、`ingress_id`、`event_type` 必须是非空且非全空白字符串；`payload` 必需且必须是 `Mapping[str, JSONValue]`；`source` 可省略，省略时默认为空 Mapping，显式提供时必须是 `Mapping[str, JSONValue]`；`external_request_id`、`response_channel_id` 可为 `None`，非空时必须是非空且非全空白字符串；`artifact_refs` 必须是 `tuple[str, ...]`，默认空 tuple，每项均为非空且非全空白字符串。
- `Context`：冻结 dataclass；`values` 为 `Mapping[str, JSONValue]`，默认空映射。本切片 Host 创建的 Context 固定为空，不从 Event 自动复制字段。
- `Run`：冻结 dataclass；`run_id` 和 `event_id` 必须是非空且非全空白字符串；不在本 SR 实现持久化、Continuation 或状态机。
- `ModelRequest`：冻结 dataclass，包含 run、event 和 context。
- `ModelProposal`：冻结 dataclass；`kind` 必须是非空且非全空白字符串；`payload` 必须是 `Mapping[str, JSONValue]`；不表示已执行 Action。
- `HostResult`：冻结 dataclass，包含 `run: Run` 与 `proposal: ModelProposal`。
- `ModelClient`：由调用方注入的同步 Protocol，方法为 `propose(request: ModelRequest) -> ModelProposal`。
- `AgentLoop`：构造时注入 ModelClient；`run_once(request)` 对 ModelClient 调用恰好一次，不重试。
- `HostError`：稳定错误异常，构造签名为 `HostError(code: str, safe_message: str)`；`code` 仅允许 Host 错误码 `EVENT_INVALID`、`MODEL_CLIENT_FAILED`、`MODEL_PROPOSAL_INVALID`、`HOST_INTERNAL_ERROR`；`CLI_USAGE_ERROR` 是 CLI-only 诊断，不是 HostError。`safe_message` 必须使用对应固定安全消息，不得包含原始凭据、模型响应或异常文本。
- `Host`：构造时注入 ModelClient；公开 `handle_event(event: Event) -> HostResult`。未提供 `run_id_factory` 时使用标准库 `uuid.uuid4().hex` 生成 `run_id`；Event 完整校验通过后、每次调用恰好生成一次。工厂异常或返回空白/非字符串 ID 时抛出 `HOST_INTERNAL_ERROR`，且不得调用 ModelClient。

HostError 定义在 `contracts.py`，供 `model_loop.py` 和 `host.py` 从同一位置导入；`host.py` 只重导出，不重复定义，避免 AgentLoop/Host 相互导入形成循环依赖。

公共导入路径固定为：`ca_agent_next.contracts` 导出 `JSONValue/Event/Context/Run/ModelRequest/ModelProposal/HostResult/HostError`；`ca_agent_next.model_client` 导出 `ModelClient`；`ca_agent_next.model_loop` 导出 `AgentLoop`；`ca_agent_next.host` 导出 `Host` 并从 contracts 重导出 `HostError`。包根 `ca_agent_next` 的 `__all__` 必须重导出上述全部名称。

冻结 dataclass 阻止字段重新赋值；`Mapping` 是公共只读接口约定，不宣称 Python 对象具备递归深冻结。生产者和 ModelClient 均不得在交接后修改映射或其嵌套值。

Host 不创建真实模型客户端、不读取 Provider/Gateway 环境变量、不拥有注入 ModelClient 的资源生命周期。ModelClient 由应用组合入口创建和管理。测试使用 Fake ModelClient。

### 2.3 Host 最小处理流程

1. 接收已规范化 Event。
2. 校验 Event 类型、全部字段和递归 JSONValue；无效输入抛出 `HostError(EVENT_INVALID, "event is invalid")`，不生成 Run ID、不调用 ModelClient。
3. 创建本次 Run 和最小 Context。
4. 构造 ModelRequest。
5. AgentLoop 调用注入的 ModelClient 一次。
6. AgentLoop 校验返回值必须是 `ModelProposal`，并校验 `kind` 与 `payload`；否则抛出 `HostError(MODEL_PROPOSAL_INVALID, "model proposal is invalid")`。
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
- SR-003 对 SR-002 的依赖是**实施依赖**：SR-003 代码实施启动前须确认 SR-002 VERIFIED；SR-003 的设计评审和 READY 不因 SR-002 尚未实施/验收而阻塞。SR-003 复用 F01 定义的 Event、Host.handle_event、HostResult 和 ModelClient 注入边界。
- EX-01 是系统级语言/装配门槛，需等待 SR-002、SR-004、SR-005、SR-006、SR-007 各自模块验收完成后联合执行；EX-01 不阻塞 SR-002 的独立验收。
- ca-agent-demo 仅为只读参考：main SHA `57e277ff9094dad93543df46910a12a1dbbaf560`。可参考 `pyproject.toml` 的 src layout、`src/ca_agent_host/agent/model_adapter.py` 的同步 `ChatModelTransport` Protocol，以及 `tests/unit/chat_model_fakes.py` 中记录 HTTP 请求的 `FakeHttpClient.calls` 模式；Next 的 typed `ModelClient.propose` 是独立公共契约，不是对 `ChatModelTransport.complete` 的直接复制。不得复制其 distribution `ca-agent-host`、import package `ca_agent_host`、CLI `ca-plan`、完整 Resident/Runtime 或业务实现。参考仓 PASS 不计为 Next 验收证据。

## 5. 模块验收

本 SR 的独立验收为 AC-002-01～AC-002-08，详细通过条件见[演示验收基线 §3.1](../验收与实施/演示验收基线.md)。至少执行以下命令：

```text
python -m pip install -e .
python -c "from ca_agent_next import JSONValue, Event, Context, Run, ModelRequest, ModelProposal, HostResult, ModelClient, AgentLoop, Host, HostError"
python -c "from ca_agent_next.contracts import HostError as A; from ca_agent_next.host import HostError as B; assert A is B"
python -m ca_agent_next --smoke
python -m unittest discover -s tests -p "test_host.py" -v
```

测试必须通过公共 Host/CLI 入口覆盖：Event 有效/无效及递归 JSONValue 边界、run_id 工厂调用次数与失败、Context 空值、ModelClient 恰好一次/异常/不重试、Proposal 类型与字段拒绝、CLI 参数错误及 stdout/stderr/退出码；并断言 `ca_agent_next.contracts.HostError is ca_agent_next.host.HostError`，确保重导出没有创建第二个异常类型。unittest 必须实际发现并执行测试；输出 `Ran 0 tests`、跳过必需用例或只执行导入检查，均不能计为 PASS。

### 5.1 固定 Smoke 契约

- 命令：`python -m ca_agent_next --smoke`。
- Smoke 固定 Event：
  - event_id：`smoke-event-001`
  - ingress_id：`smoke`
  - event_type：`ca-agent-next.smoke`
  - payload：`{"message":"hello"}`
  - source：`{"protocol":"smoke","peerId":"local"}`
- Smoke 使用进程内 Fake ModelClient，并将 run_id_factory 固定为返回 `smoke-run-001`；不读取真实 Provider 配置、不访问网络、不要求 API Key。
- Fake 返回 ModelProposal：kind 为 `smoke.echo`，payload 为 `{"message":"smoke-ok"}`。
- 成功 stdout 为单行紧凑 JSON，字段集合和类型固定：

```json
{"schema_version":1,"status":"ok","event_id":"smoke-event-001","model_calls":1,"proposal":{"kind":"smoke.echo","payload":{"message":"smoke-ok"}}}
```

- 成功退出码为 0；成功时 stderr 为空；stdout 不得混入日志、调试信息或额外文本。
- CLI 仅接受单一参数 `--smoke`；缺少该参数、出现未知参数或多余参数均为 `CLI_USAGE_ERROR`，退出码 2。
- CLI 使用自定义错误处理，不得让 argparse 默认用法文本或 traceback 混入 stderr。所有 CLI/Host 失败均只向 stderr 输出一行紧凑 JSON：`{"schema_version":1,"error":{"code":"<ERROR_CODE>","message":"<SAFE_MESSAGE>"}}`；失败时 stdout 为空。
- Host 运行失败退出码为 1；CLI 参数错误退出码为 2。错误码及固定安全消息见 F01 §5.4。ModelClient 的任何 `Exception`（包括其抛出的 HostError）均映射为 `MODEL_CLIENT_FAILED`；不重试、不透传异常文本。无效 Proposal 映射为 `MODEL_PROPOSAL_INVALID`。
- `__main__.py` 提供 `main(argv: Sequence[str] | None = None, *, model_client: ModelClient | None = None) -> int`；`model_client` 仅供单元测试注入，真实 CLI 不暴露 Provider 配置入口。正常 Smoke 未注入时使用进程内 Fake ModelClient。
- 成功 stdout JSON 及 `model_calls=1` 只适用于默认 CLI Smoke（未注入 `model_client`）；`model_calls` 必须来自默认 Fake 的实际调用记录，不得由 Host 自报。
- 测试注入的 `model_client` 仅用于 CLI 失败路径测试；注入型 `main()` 的成功输出及其 `model_calls` 不属于公开契约，不要求实现或断言。成功调用次数在 AgentLoop/Host 单元测试中直接读取测试 Fake 自身的调用记录。
- 失败不得输出 traceback、凭据、token 或完整敏感请求内容。

### 5.2 SR-028 迁移后当前复验入口（uv，2026-11-28）

§5 的 pip 命令是 SR-002 原始模块验收环境（CPython 3.14.6、pip）的历史记录，保留不改。自 SR-028 起，仓库根 Python 工程的当前复验入口统一为 uv 0.13.10 + `uv.lock`：

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite host --output-dir artifacts/unittest-gate/host
```

Host 范围仍要求 discovered>0、tests_run=discovered、failures/errors/skipped=0 且退出码 0 才计 PASS。PR #115 代码与策略核验 Head `609fb12612c8990a37ba0e174cfacadfd7a7c5d9` 的 SR-003 双平台回归中，Host 在 Ubuntu / Windows 均为 52/52 PASS；该结果是当前候选分支复验，不改变本 SR 的历史 AC-002-01～08 证据边界。

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
| 设计修订 Issue | [ca-agent-next #19](https://github.com/odango-chan/ca-agent-next/issues/19)（CLOSED / completed） |
| 设计评审 PR | [ca-agent-next #20](https://github.com/odango-chan/ca-agent-next/pull/20)（MERGED；目标恢复分支；merge commit `281ccb957b9222e72175e210d1afed177aa8a14f`） |
| 治理规则 Issue | [ca-agent-next #21](https://github.com/odango-chan/ca-agent-next/issues/21)（CLOSED / completed；SR 管理规范 v0.7.0、文档治理规范 v0.6.0） |
| 实施 Issue | [ca-agent-next #22](https://github.com/odango-chan/ca-agent-next/issues/22)（由本证据回填 PR #25 合并时关闭） |
| 实施 PR | [ca-agent-next #23](https://github.com/odango-chan/ca-agent-next/pull/23)（MERGED；目标恢复分支；merge commit `49964464e19d13d219ea0b3513d2223fe81d2435`） |
| 受测实施 Commit | `6628245978f1fbd1e1d1393b9338c908c962eb9e`（分支 `feature/issue-22-sr-002-python-host-skeleton`；远端 SHA 已核实） |
| 设计基线 | 实施时契约快照：F01 v0.3.6、SR-002 v0.2.9、Acceptance v0.3.8；当前 SR 状态记录为 v0.2.10。PR #20 后续仅修订治理元数据，未改变本 SR 契约 |
| 测试环境 | Windows；CPython 3.14.6；pip 26.1.2；setuptools>=68；运行时依赖为空 |
| 安装与 Smoke | `python -m pip install -e .` PASS；`python -m ca_agent_next --smoke` PASS，stdout 固定单行 JSON，stderr 为空 |
| 自动化测试 | `python -m unittest discover -s tests -p "test_host.py" -v`：52 passed / 0 failed / 0 errors / 0 skipped；`compileall` PASS |
| AC-002-01～AC-002-08 | **PASS**；逐项证据见 [PR #23](https://github.com/odango-chan/ca-agent-next/pull/23) 和 [Issue #22 实施证据](https://github.com/odango-chan/ca-agent-next/issues/22#issuecomment-7183057195) |
| 实施状态 | IMPLEMENTED |
| SR 验收状态 | VERIFIED（本 PR 合并后，AC 证据与受测 SHA 固定在目标基线） |
| EX-01 系统级验收 | NOT_RUN；由 SR-002/004/005/006/007 联合完成，不阻塞本 SR |
| Python 版本矩阵 | CPython 3.11/3.12/3.13 NOT_RUN；仅 CPython 3.14.6 已验证 |
| DeepSeek Harness | NOT_RUN；本批实现证据来自实施方本地命令和 Issue #22 回填 |
| CI | PR #23 未返回 GitHub Actions workflow runs / CI 结果；不得将本地测试报告描述为 GitHub CI PASS |

SR-002 的模块 AC-002-01～08 已全部通过，实施 PR #23 已集成。上述 VERIFIED 仅表示本 SR 的模块验收证据完整，不表示 EX-01、Python 版本矩阵、DeepSeek Harness、完整 Agent Runtime 或生产 Qualification 已通过。未运行项继续保持 NOT_RUN。
## 8. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：将原先直接引用的 EX-01 拆分为 SR-002 自身 AC-002-01～AC-002-08 与系统级 EX-01；不改变 F01 业务中立边界，不把 SR-004/005/006/007 的责任移入 SR-002；为 SR-003 固定 Host 公共复用入口。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续改变既有范围、接口或验收时，按 SR 管理规范创建替代 SR，不覆盖历史要求。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-002 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实文档命名规范 | SR-002 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-002 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 校正当前设计依据版本 | 核对 Issue #12 与固定提交 | SR-002 |
| 2026-11-25 | 0.1.4 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 固定目标代码位置、复验入口及可观察断言 | 对齐当前架构与实施门禁 | Issue #12 |
| 2026-11-26 | 0.1.5 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.0 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 将 EX-01 明确为系统级门槛；新增 AC-002-01～AC-002-08、固定 Smoke 输入/输出/错误码、ModelClient 注入和 SR-003 复用边界 | 使 SR-002 可独立实施和验收，避免被后续模块阻塞 | Issue #19；IR-002；SR-003 |
| 2026-11-26 | 0.2.1 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 补齐 Event/Context/Run/Proposal 字段类型、HostError 安全诊断和确定性 Smoke run_id；回填 Draft 设计 PR #20 | 消除 Harness 对类型、异常映射和 Smoke 稳定性的猜测 | Issue #19；PR #20 |
| 2026-11-26 | 0.2.2 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 将设计依据版本同步到 F01 v0.3.1 | 保证 SR-002 引用当前权威字段与错误契约 | Issue #19；F01 v0.3.1 |
| 2026-11-26 | 0.2.3 | 未记录（历史资料未提供） | 未记录（历史资料未提供） | 固定 HostError 构造签名、默认 UUID run_id 生成时机及 Event.source 可选语义 | 消除 Host 实现和 Fake 测试的剩余猜测 | Issue #19；F01 v0.3.3；PR #20 |
| 2026-11-26 | 0.2.4 | GPT-6.2（ChatGPT） | §2.1～§2.3、§5.1、§6 | 固定 pyproject 元数据、公开导出、Event/Context/JSONValue 校验、HostError 与 CLI 诊断 | 消除包身份、输入验证和失败路径的实现猜测，使 Harness 可按同一契约实施 | IR-002；F01；AC-002-01～08；Issue #19；PR #20 |
| 2026-11-26 | 0.2.5 | GPT-6.2（ChatGPT） | §2.1～§2.2、§5.3～§5.4 | 将 HostError 唯一定义位置固定为 contracts.py，由 host.py 重导出；明确 CLI_USAGE_ERROR 不属于 HostError；同步 F01 v0.3.5。 | 消除 ModelLoop/Host 循环依赖和 CLI/Host 错误类型混淆。 | Issue #19；F01 v0.3.5；SR-003；PR #20 |
| 2026-11-26 | 0.2.6 | GPT-6.2（ChatGPT） | §2.2、§5、§6 | 固定 SR-002 对 F01 v0.3.5 的精确版本引用，并增加 HostError 单一类型身份的导入/测试断言。 | 使模块重导出边界可由自动化测试验证，避免循环依赖或重复异常类。 | F01 v0.3.5；AC-002-06；Issue #19；PR #20 |
| 2026-11-26 | 0.2.7 | GPT-6.2（ChatGPT） | §4、§5.1、§7 | 根据独立评审 APPROVE_FOR_READY 将 SR-002 转为 READY；明确 SR-003 的实施依赖与设计评审分离，并限定注入型 ModelClient 仅用于 CLI 失败路径测试；同步 PR #20 状态。 | 关闭 P2-01/P3-01/P3-02，不扩大 SR-002 范围；保持 AC/EX 未运行状态真实。 | IR-002；Issue #19；Issue #21；PR #20；评审 SHA `888b8ba` |
| 2026-11-26 | 0.2.8 | GPT-6.2（ChatGPT） | 文档头部、§2 | 将当前设计依据和公共契约引用从 F01 v0.3.5 更新为 F01 v0.3.6；本次 F01 仅澄清 Smoke 注入测试边界，不改变 SR-002 类型契约。 | 确保 READY SR 引用当前权威设计版本，避免 Harness 读取过期版本号。 | Issue #19；Issue #21；F01 v0.3.6；PR #20 |
| 2026-11-26 | 0.2.9 | GPT-6.2（ChatGPT） | §7 | 创建并登记独立 SR-002 实施 Issue #22，固定其与设计 Issue #19、治理 Issue #21 和设计 PR #20 的关系。 | 满足 READY 后先建实施 Issue、再交付 Harness Goal 的治理顺序，避免设计 Issue 被误作实施授权。 | Issue #19；Issue #21；Issue #22；PR #20 |
| 2026-11-26 | 0.2.10 | GPT-6.2（ChatGPT） | §7、修订记录 | 回填 PR #23 的集成 Commit、受测 SHA、CPython 3.14.6 环境、安装/Smoke/52 项测试与 AC-002-01～08 PASS；将实施状态更新为 IMPLEMENTED、SR 状态更新为 VERIFIED。 | 使 SR 状态由 READY 随实际实现、模块验收和证据集成推进；明确 EX-01、版本矩阵与 DeepSeek Harness 仍 NOT_RUN。 | Issue #22；PR #23；merge commit `49964464`；证据 comment `7183057195`；PR #25 |
| 2026-11-27 | 0.2.11 | DeepSeek Harness（Goal 执行） | §5.2、修订记录 | 按 SR-028 新增迁移后当前 uv 复验入口（uv 0.13.10 + uv.lock + unittest gate --suite host），§5 原始 pip 验收命令、受测 SHA 与 52 项 PASS 记录保持原文 | 统一仓库当前工具链入口，同时不覆盖历史受测环境与 VERIFIED 证据 | Issue #96；PR #99；SR-028；G02 |
| 2026-11-28 | 0.2.12 | GPT-6.2（ChatGPT） | §5.2、修订记录 | 将 uv 当前复验入口同步到 mainline 集成候选；历史 pip 安装、受测 SHA 与原始 52 项 PASS 记录保持不变 | 保持 SR-002 原始 VERIFIED 证据与 SR-028 迁移后当前工具链分离 | Issue #96；PR #99；PR #115；SR-028 |
| 2026-11-28 | 0.2.13 | GPT-6.2（ChatGPT） | §5.2、修订记录 | 将 PR #115 当前候选的 Host 双平台 52/52 回归证据与历史 SR-002 VERIFIED 记录分开 | 避免把当前候选回归外推为历史受测 SHA 或扩展为系统 EX PASS | Issue #50/#96；PR #115；SR-028 v0.2.14 |
| 2026-11-28 | 0.2.14 | GPT-6.2（ChatGPT） | §5.2、修订记录 | 将当前工具链依据更新至 SR-028 v0.2.15，并保留 Host 双平台 52/52 候选复验边界 | 避免 SR-002 与 SR-028 版本引用不一致 | Issue #50/#96；PR #115；SR-028 v0.2.15 |
