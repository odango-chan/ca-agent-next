# 通用 Agent Core 与 Host 设计说明书

> 文档类型：功能设计说明书  
> 文档版本：0.3.8\
> 状态：Next 目标设计；本仓实现状态需独立验收，不以参考仓 PASS 代替  
> 功能归属：F01 — 通用 Agent Core 与 Host  
> 关联 SR：SR-002、SR-020、SR-021、SR-032  
> 修订日期：2026-11-26  
> 适用范围：Python Host、Agent Core、Model Loop、Event/Run 协调、Runtime/Plugin 边界

关联 IR-002、IR-006、IR-008。共享资源与 Host Script Execution 的设计增量由 Issue #49 / SR-032 追踪。参考架构原文见 §12。
> 全局评审范围：继承根目录 Agent.md 的 review_scope。  
> 本文局部非目标：业务专用协议、Owner 状态机与生产级部署。

## 1. 目标与原则

定义一个与 OpenAMSM、5GC、任何业务域无关的 Agent Core 和 Python Host。业务能力通过 Event Plugin、Skill、Tool Interface Package 和部署配置提供。新增业务不应要求修改 Core、Host、Skill Resolver 或 Runtime 中的业务专用分支。

必须保持：
- Core、Host、Model Loop、Skill Importer/Resolver、Runtime 使用 Python。
- Native Plugin 可使用 Go 或其他语言，但统一由 Python Plugin Manager 管理。
- Event Plugin 只规范化 Event；Skill Resolver 选择 Skill；Runtime 执行 Action；Owner 决定业务提交。
- 模型只能提出 Action，不能直接执行 Tool 或宣布 Owner Outcome。
- Deterministic 与 LLM-guided 两种执行模式共用 Runtime Action Boundary。

## 2. 组件与职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Host | 进程入口、配置、Plugin Manager 装配、Event 接收协调、Run/Response 生命周期 | 业务协议业务逻辑、Owner 状态 |
| Agent Core | 通用 Event/Goal 协调、Context 组装、Skill/Mode 流程协调 | OpenAMSM 路由表、5GC 状态机 |
| Model Loop | Model Client、模型输入投影、受约束 Action 提议 | 直接调用 Plugin、授权、提交判断 |
| ModelClient | 通过稳定 Protocol 接收 ModelRequest 并返回 ModelProposal；由组合入口注入 | Host 内部创建 Provider、Plugin dispatch、Owner outcome |
| Skill Importer / Catalog | 导入已发布 Skill Bundle、构建不可变 Catalog generation | 编译作者源、生产准入 |
| Skill Resolver | 对新 Event 选择精确 Skill；Continuation 恢复原 Skill | 业务执行 |
| Runtime | Run 状态、Action Boundary、Procedure、Wait/Resume、Outcome 解释 | Plugin 进程生命周期、模型推理 |
| Plugin Manager | Plugin 包/进程、IPC、Extension 分发 | Skill 选择、Owner outcome |
| Host ArtifactStore | 原始字节、opaque refs、Run/Invocation 关联与访问控制 | 协议业务解码 |

## 3. 进程与主要数据流

~~~text
外部业务请求
  -> Native Event Plugin
  -> Plugin Manager / ingress Extension
  -> Host Event Validator
  -> Event Deduplication / Response Obligation
  -> Skill Resolver (F02)
  -> Run Creation / Skill Binding
  -> Context Assembly
  -> Deterministic Procedure Engine OR LLM Model Loop
  -> Runtime Action Boundary (F04)
  -> Plugin Manager / tools Extension
  -> Tool Provider / Owner
  -> Outcome + Evidence
  -> Host Response Assembly
  -> Plugin Manager / delivery Extension
  -> 原始外部响应通道
~~~

Host 不要求 Event Plugin 知道 Run ID，也不允许 Plugin 自己决定 Skill。Host 负责把 Event、Run、Skill、Catalog generation、Artifact refs 和 responseObligation 关联起来。

## 4. Event、Run 与响应义务

Event 是外部协议归一化后的输入；Run 是 Host 为一次业务执行创建的生命周期身份；responseObligation 是 Host 对外部请求必须完成的响应义务。三者不能混用。

Host 至少维护：
- Event identity、ingressId、eventType、externalRequestId；
- 规范化 payload 和 Artifact refs；
- Run ID、绑定 Skill、Artifact identity、Catalog generation；
- responseObligationId、原始 responseChannelId；
- invocation refs、当前执行状态和结果；
- 重复请求、Continuation、Delivery 状态。

重复 externalRequestId：
- 内容和 Artifact bytes 可证明相同时，关联已有 Run 或既有结果，不重复 mutation；
- 同 ID 内容冲突、身份缺失或无法证明相等时，拒绝并输出诊断；
- Continuation 必须精确绑定原 Run，不重新选择 Skill。

## 5. Model Loop 与 Action 提议

Model Loop 不承担 Tool dispatch。每一轮模型输入由 Host 组装，至少包含：
- 当前 Goal/Event 的规范化视图；
- 已绑定 Skill 的 SKILL.md；
- 当前 Skill Package 根目录的 schemas/ 与 scripts/manifest.yaml、按需读取的 Script 源码 / references / assets；资源读取只限当前不可变 Package snapshot；
- 当前 Skill 已授权的 Capability 描述和公开 Input / Output Schema 摘要；模型不得看到 Callable ID 或 backendOperationId；
- 已授权 Context / Observation；
- 当前 Run 位置和剩余 response obligation。

模型输出必须转换为结构化 Action Proposal。Host / Runtime 校验 Skill identity、Capability ID、参数 Schema、Artifact refs、Run state 和 invocation identity；业务 Capability 从已验证 Artifact 的唯一 capabilityBinding 解析内部 Callable，才允许调用 Plugin。若 Action 为 Host Script Execution system Capability `host.skill-script.execute`，Runtime 则校验当前 Skill 的 scripts/manifest.yaml、llmInvocable 标记、Host policy 和输入 Schema，再由 Host 内建 Tools Extension 调用精确 Script entrypoint。模型不得提交或替换 Callable ID、backendOperationId、URL、Provider selector、脚本路径、代码或命令；未知 Capability、绑定歧义、参数不完整或越权时停止，不自动猜测修复。

Model Client 是可替换适配器；自动化测试必须支持 Fake Model Client。模型 Provider、Gateway URL、模型 ID 和凭据属于部署配置，不进入业务 Skill 契约。

本节开头的完整 Model Loop 输入描述目标架构在 Skill Resolver、SkillCatalog、Runtime 等后续模块就绪后的输入。SR-002 首个切片只组装规范化 Event、空 Context 和 Run；不提前实现 Skill 绑定、Callable 授权或 Runtime 输入投影。

### 5.1 SR-002 首个可交付切片：包身份与目录

SR-002 只建立以下 Python distribution 和 import identity：

`pyproject.toml` 的项目/构建段固定如下：

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

| 项目 | 固定值 |
|---|---|
| Distribution | `ca-agent-next` |
| Import package | `ca_agent_next` |
| 源码根目录 | `src/ca_agent_next/` |
| 模块入口 | `python -m ca_agent_next --smoke` |
| 项目元数据 | 根目录 `pyproject.toml`；项目版本 `0.1.0`；`requires-python = ">=3.11"`；`dependencies = []` |
| 构建配置 | `setuptools>=68`、`setuptools.build_meta`；包发现 `where = ["src"]`、`include = ["ca_agent_next*"]` |
| 运行时依赖 | 仅 Python 标准库；项目 `dependencies = []`，setuptools 仅为构建依赖 |
| 测试入口 | `tests/test_host.py`，标准库 `unittest` |

最小文件布局：

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

测试目标解释器为 CPython 3.14.6；元数据支持下限为 CPython 3.11。未在完整版本矩阵执行前，不得声称每个受支持版本均已验证。

ca-agent-demo 的当前身份是 distribution `ca-agent-host`、import package `ca_agent_host`、CLI `ca-plan`。Next 不复用这些身份，不添加兼容别名或重导出包。只参考其 `src/` 包布局、Protocol 注入和 Fake 调用记录模式。

`ca_agent_next.__init__` 必须按 `__all__` 导出：`JSONValue`、`Event`、`Context`、`Run`、`ModelRequest`、`ModelProposal`、`HostResult`、`ModelClient`、`AgentLoop`、`Host`、`HostError`。`contracts.py` 定义 JSONValue、数据类型和 HostError；`model_client.py` 定义 ModelClient；`model_loop.py` 从 contracts 导入 HostError 并定义 AgentLoop；`host.py` 定义 Host 并从 contracts 重导出 HostError。这样 HostError 只有一个定义位置，不产生 model_loop ↔ host 循环导入；不创建兼容别名。

### 5.2 Host 与 Model Loop 公共类型

SR-002 固定下列最小类型；字段名和含义以本表为准：

| 类型 | 字段/语义 |
|---|---|
| `JSONValue` | 递归 JSON 值：`None`、`bool`、`int`、有限 `float`、`str`、`list[JSONValue]` 或 `Mapping[str, JSONValue]`；拒绝非有限浮点数、非字符串对象键、循环容器、bytes、Path、Decimal 和任意 Python 对象；验证时先区分 bool 与 int |
| `Event` | 冻结 dataclass；`event_id`、`ingress_id`、`event_type` 为非空且非全空白字符串；`payload` 必需且为 `Mapping[str, JSONValue]`；`source` 可省略（缺省空 Mapping），显式提供时必须为 `Mapping[str, JSONValue]`；`external_request_id`、`response_channel_id` 为 `None` 或非空且非全空白字符串；`artifact_refs` 为 `tuple[str, ...]`，默认空 tuple，元素均非空且非全空白 |
| `Context` | 冻结 dataclass；`values` 为 `Mapping[str, JSONValue]`，默认空映射；SR-002 的 Host 初始 Context 固定为空，不从 Event 自动复制字段；不承载伪造的 Observation/Evidence |
| `Run` | 冻结 dataclass；`run_id`、`event_id` 为非空且非全空白字符串；不在 SR-002 切片实现持久化、Continuation 或状态机 |
| `ModelRequest` | 冻结 dataclass；包含 `run: Run`、`event: Event`、`context: Context` |
| `ModelProposal` | 冻结 dataclass；`kind` 为非空且非全空白字符串，`payload` 为 `Mapping[str, JSONValue]`；只是提议，不是已执行 Action |
| `HostResult` | 冻结 dataclass；包含 `run: Run` 与 `proposal: ModelProposal` |
| `HostError` | 在 `contracts.py` 定义的稳定异常；code 仅允许 `EVENT_INVALID`、`MODEL_CLIENT_FAILED`、`MODEL_PROPOSAL_INVALID`、`HOST_INTERNAL_ERROR`，并携带对应固定 safe_message；`host.py` 只重导出该类型 |

`artifact_refs` 只允许表示 Host-owned opaque reference；SR-002 不打开、复制或传输原始字节。Plugin 提供的 `stagingPath`、本地路径和原始 bytes 不得直接填入该字段；staging、ArtifactStore 和引用创建归 F05 / 对应 SR。

冻结 dataclass 只保证字段不能重新赋值；`Mapping` 是公共只读接口约定，不宣称 Python 对象具备递归深冻结。生产者和消费者不得在交接后修改映射或其嵌套值。

### 5.3 ModelClient 注入与 Host 公开 API

公开接口为同步调用，避免首个骨架同时引入异步运行时和 Provider 复杂度：

```python
# contracts.py
class HostError(Exception):
    def __init__(self, code: str, safe_message: str): ...

# model_client.py
class ModelClient(Protocol):
    def propose(self, request: ModelRequest) -> ModelProposal: ...

# model_loop.py
class AgentLoop:
    def __init__(self, model_client: ModelClient): ...
    def run_once(self, request: ModelRequest) -> ModelProposal: ...

# host.py
class Host:
    def __init__(
        self,
        model_client: ModelClient,
        *,
        run_id_factory: Callable[[], str] | None = None,
    ): ...
    def handle_event(self, event: Event) -> HostResult: ...
```

- `Host.handle_event` 校验 Event 类型、必需字段、可选字段、`artifact_refs` 和递归 JSONValue；输入无效时抛出 `HostError("EVENT_INVALID", "event is invalid")`，不生成 Run ID、不调用 ModelClient。
- Event 校验通过后，Host 恰好调用一次 `run_id_factory`；未注入时使用标准库 `uuid.uuid4().hex`。工厂异常、返回非字符串或空白 ID 时抛出 `HostError("HOST_INTERNAL_ERROR", "host internal error")`，不调用 ModelClient。
- Host 为 SR-002 初始切片创建空 `Context.values`，不从 Event 隐式复制上下文。
- `AgentLoop.run_once` 同步调用 `ModelClient.propose(request)` 恰好一次；任何 `Exception`（包括 ModelClient 抛出的 HostError）映射为 `MODEL_CLIENT_FAILED`，不重试。
- ModelClient 返回值不是 `ModelProposal`，或 `kind`/`payload` 不满足 §5.2 时，映射为 `MODEL_PROPOSAL_INVALID`；不 dispatch、不尝试猜测修复。
- Host 保留已知 `HostError`；其他未预期异常映射为 `HostError("HOST_INTERNAL_ERROR", "host internal error")`，不向 CLI 暴露原始异常文本。
- `AgentLoop.run_once` 对注入的 ModelClient 调用恰好一次；本切片不重试、不流式读取、不创建真实 Provider。
- ModelClient 由应用组合入口创建并注入。Host/AgentLoop 不读取环境变量、不创建 HTTP 客户端、不拥有注入对象的关闭责任。
- 测试用 Fake ModelClient 记录完整 ModelRequest、调用次数和返回值/异常；一次 `handle_event` 必须对应一次 `propose`。
- Host 的公开入口是 `Host.handle_event(Event) -> HostResult`。SR-003 的 Event ingress adapter 将 Plugin IPC 的规范化字段映射为 Event，并调用这个入口；不得在 Plugin Manager 内重建 Host、AgentLoop 或 ModelClient。

### 5.4 错误、Proposal 与生命周期边界

| 场景 | 错误码 | 固定 safe_message | 行为/退出码 |
|---|---|---|---|
| Event 类型、字段或 JSONValue 无效 | `EVENT_INVALID` | `event is invalid` | 不生成 Run ID、不调用 ModelClient；Host 抛出 HostError |
| ModelClient.propose 抛出任意 Exception | `MODEL_CLIENT_FAILED` | `model client failed` | 恰好一次调用、不重试；不透传异常文本；Host 抛出 HostError |
| ModelClient 返回值不是有效 ModelProposal | `MODEL_PROPOSAL_INVALID` | `model proposal is invalid` | 不 dispatch、不尝试猜测修复；Host 抛出 HostError |
| CLI 缺少 `--smoke`、出现未知参数或多余参数 | `CLI_USAGE_ERROR` | `invalid command line usage` | CLI-only 诊断，不构造或抛出 HostError；stderr 输出一行 JSON；退出码 2 |
| Run ID 工厂失败或其他未预期 Host 错误 | `HOST_INTERNAL_ERROR` | `host internal error` | Run ID 阶段失败时不调用 ModelClient；stderr 输出一行 JSON；退出码 1 |

Model Proposal 不会在 SR-002 内执行。它不会触发 Plugin、Tool、Runtime、Owner 或任何外部副作用。Host 只返回提议及 Run 标识；后续 Runtime Action Boundary 由 F04/SR-007 负责。

### 5.5 固定 Smoke 契约

命令为 `python -m ca_agent_next --smoke`，这是 CLI 唯一支持的调用方式。`__main__.py` 提供 `main(argv: Sequence[str] | None = None, *, model_client: ModelClient | None = None) -> int`；`model_client` 仅供测试注入，命令行不提供 Provider/网络配置入口。Smoke 以 `run_id_factory=lambda: "smoke-run-001"` 创建 Host，确保 Fake 收到的 Run 可重复。Smoke 使用固定 Event：event_id `smoke-event-001`、ingress_id `smoke`、event_type `ca-agent-next.smoke`、payload `{"message":"hello"}`、source `{"protocol":"smoke","peerId":"local"}`。进程内默认 Fake ModelClient 返回 kind `smoke.echo`、payload `{"message":"smoke-ok"}`。

成功时 stdout 只输出一行紧凑 JSON，字段结构如下；不得输出日志或额外文本：

```json
{"schema_version":1,"status":"ok","event_id":"smoke-event-001","model_calls":1,"proposal":{"kind":"smoke.echo","payload":{"message":"smoke-ok"}}}
```

成功退出码为 0，stderr 为空。所有失败均保持 stdout 为空，stderr 只输出一行紧凑 JSON：`{"schema_version":1,"error":{"code":"<ERROR_CODE>","message":"<SAFE_MESSAGE>"}}`。例如 ModelClient 失败为 `{"schema_version":1,"error":{"code":"MODEL_CLIENT_FAILED","message":"model client failed"}}`。CLI 参数错误退出 2，Host 运行错误退出 1；不得泄露 token、凭据、完整请求、异常文本或 traceback。

成功 stdout JSON（含 `model_calls=1`）只适用于未注入 `model_client` 的默认 CLI Smoke；计数来自默认进程内 Fake 的调用记录。`main(..., model_client=custom_fake)` 的注入入口只用于 CLI 失败路径测试；注入型成功调用的 stdout 和计数不属于 CLI 公共契约。成功调用次数在 AgentLoop/Host 单元测试中直接断言测试 Fake 的记录，不要求 ModelClient Protocol 暴露 `calls` 或 `call_count`。

复验命令：

```text
python -m pip install -e .
python -m ca_agent_next --smoke
python -m unittest discover -s tests -p "test_host.py" -v
```

测试必须覆盖成功、输入拒绝及递归 JSONValue 边界、run_id 工厂调用/失败、空 Context、ModelClient 一次调用/异常/不重试、Proposal 类型/字段拒绝、CLI 缺参/未知参数、错误 JSON 与 stdout/stderr/退出码；发现 0 个测试不能算 PASS。Smoke 不访问网络、不读取 Provider 配置、不需要 API Key。


## 6. Context 与 Artifact 协调

Core 只协调 Context 需求，不拥有业务事实。Observation 必须经只读 Tool 能力获取；Owner Receipt/Commit Proof 由 Owner 发布并由 Runtime 解释。原始 N1/N2 等二进制由 Host ArtifactStore 管理，模型只看到明确允许的结构化投影和 Artifact metadata，不直接看到原始字节。

Context 与 Artifact 的详细契约见 F05。Model Loop 不得将模型生成内容伪装成 Observation 或 Evidence。

## 7. 新业务扩展模型

新增一个业务域的最小扩展：
1. Event/Delivery Plugin 声明协议 Event 和响应；
2. 一个或多个 Skill 定义适用条件和执行流程；
3. Provider Interface Package 或业务 Owner Contract 按 Callable 归属定义公开接口与 Schema；
4. Tool Plugin 适配对应 Provider；
5. Owner 实现业务状态和权威结果；
6. 部署配置将上述资产装配到 Host。

禁止新增 Event→Skill 业务路由表、Event→Mode 表、业务专用 Python Handler、重复 Tool Catalog 或 Owner 状态机。

## 8. 配置与启动

Host 启动时加载基础配置、Plugin manifests、Tool Interface Packages 和已发布 Skill Bundles；任何必需依赖加载失败时不得部分启用业务。配置包含 Plugin 安装位置、Model Client/Gateway、Skill Bundle 位置、Artifact staging/store 和日志级别。凭据通过部署安全配置提供，不接受业务 Event 注入 Provider Key。

Demo 以单 Host 进程和本机/内网 Plugin 进程为基线；不要求 HA、分布式调度或在线 Marketplace。

## 9. 失败与恢复

| 场景 | 处理 |
|---|---|
| Plugin 未 READY | 对应 Extension 不可用；不启动业务 Run |
| Event Schema 无效 | 拒绝 Event |
| 无匹配 Skill | 明确拒绝/澄清；不走 unbound fallback |
| 多个精确候选 | 只允许在候选集合内消歧 |
| Model 输出无效 | 不调用 Tool，保留诊断 |
| Runtime 拒绝 Action | 返回明确错误，不扩大权限 |
| Owner UNKNOWN | 保持 UNKNOWN，按 F04 精确 Receipt/Reconcile |
| Delivery UNKNOWN | 记录 response obligation 状态，不重放 mutation |

## 10. Demo 范围与非目标

要求具备单机可运行、可诊断、模块隔离、重复请求保护、统一 Action Boundary 和可复核的 Owner Outcome。暂不建设生产级 HA/DR、SLA、跨地域调度、复杂租户平台、生产 Skill Admission、签名/Trust Registry 或多层自动恢复系统。

## 11. 验收

SR-002 的独立模块验收为 AC-002-01～AC-002-08，详见《演示验收基线》§3.1。EX-01 是系统级 Python 语言与装配门槛，需在 SR-002、SR-004、SR-005、SR-006、SR-007 各自模块验收通过后联合执行；不得要求 SR-002 单独通过完整 EX-01，也不得因后续 SR 未完成而阻塞 SR-002。

- Core/Host/Model Loop 为 Python；业务逻辑不进入 Core。
- 一个 Echo Plugin 可触发至少一个 Skill，完成一次 LLM-guided Action 和一次 Deterministic Action。
- 新 Event 先绑定 Skill；没有候选时不执行。
- 所有模型 Action 都通过 Runtime Action Boundary。
- 重复 Event、Continuation 和 Delivery retry 不产生重复 mutation。
- Tool、Owner 和 Artifact 权限边界由测试证明。
- 新增业务不需要修改 Core/Resolver/Runtime 的业务分支。
- 参考仓的测试和 E2E 不作为 Next PASS；Next 必须在自己的分支和受测 SHA 上提供证据。

## 12. 参考架构与实现状态

- [ca-agent-demo Generic Host 规范架构原文](../../架构设计/参考实现/REF01-Python%20Generic%20Agent%20Host规范架构.md)
- [ca-agent-demo 执行路线原文](../参考实现/REF01-Generic%20Host执行路线原文.md)
- [ca-agent Go Host 当前架构重建](../../架构设计/目标参考/TARGET01-Go%20Agent%20Host当前架构重建.md)
- [ca-runtime 参考架构](../../架构设计/参考实现/REF02-CA%20Runtime架构.md)
- [Plugin 平台设计](../F03-Plugin平台/Plugin平台设计说明书.md)
- [Skill 管理与选择设计](../F02-Skill管理与选择/Skill管理与选择设计说明书.md)
- [Runtime 执行设计](../F04-Runtime执行/Runtime执行设计说明书.md)

当前 Next 的架构/设计文档与外部参考实现已迁入，但本轮未宣称 Next Host 代码、Plugin Manager 或端到端验收已完成。ca-agent-demo、ca-runtime、ca-agent 的状态分别在各自参考架构和实现审计中记录。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Core/Host/Model Loop 和业务中立基线 | 历史记录未单独记录（原记录未区分修改内容与原因） | SR-002 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 补齐 Event/Run/Response、Action Boundary、配置、失败恢复和跨仓实现差异 | 历史记录未单独记录（原记录未区分修改内容与原因） | Issue #12；SR-020、SR-021 |
| 2026-11-26 | 0.2.1 | Codex / GPT-6 | 见本行变更 | 公共 Callable 按权威源消费 | 补齐正式文档的评审范围与非目标 | Issue #12 |
| 2026-11-26 | 0.3.0 | GPT-6.2（ChatGPT） | §2、§5、§11 | 固定 Next Python 包身份、Host/ModelClient 公共接口、Fake 注入、Smoke/错误契约和 SR-002/EX-01 验收分层 | 明确 SR-003 复用入口。使首个 Python Host 切片可独立实施和复验，且不复制 ca-agent-demo 的包身份或运行时。 | Issue #19；SR-002、SR-003；AC-002-01～08、EX-01 |
| 2026-11-26 | 0.3.1 | GPT-6.2（ChatGPT） | §5.2～5.5 | 固定 JSONValue、Event/Context 字段约束、HostError 与安全错误映射，并让 Smoke Run ID 确定化 | 使实现与测试可以直接按字段和错误语义执行。 | Issue #19；SR-002；PR #20 |
| 2026-11-26 | 0.3.2 | GPT-6.2（ChatGPT） | 修订记录 | 统一本次新增修订记录的六列格式 | 保持历史修改意图与关联追踪完整。 | Issue #19；PR #20 |
| 2026-11-26 | 0.3.3 | GPT-6.2（ChatGPT） | §5.2～5.4 | 明确 Event.source 可选、HostError 构造签名及默认 UUID run_id 的生成规则和时机 | 让 Host 公开契约和失败路径可直接实现与测试。 | Issue #19；SR-002；PR #20 |
| 2026-11-26 | 0.3.4 | GPT-6.2（ChatGPT） | §5.1～§5.5 | 固定包元数据、公开导出、Event/Context/JSONValue 校验、HostError/CLI 错误语义和 Smoke 契约 | 形成可独立实施与复验的 Python Host 契约，并明确与后续模块的边界 | IR-002；SR-002；SR-003；AC-002-01～08；Issue #19；PR #20 |
| 2026-11-26 | 0.3.5 | GPT-6.2（ChatGPT） | §5.1～5.4 | 固定 HostError 在 contracts.py 唯一定义、host.py 重导出，并将 CLI_USAGE_ERROR 明确为 CLI-only 诊断。 | 避免 ModelLoop/Host 循环导入及 CLI/Host 异常类型混淆。 | Issue #19；SR-002 v0.2.5；SR-003；PR #20 |
| 2026-11-26 | 0.3.6 | GPT-6.2（ChatGPT） | §5.5 | 澄清默认 Smoke Fake 的成功输出与测试注入边界；注入型 ModelClient 只用于 CLI 失败路径测试，成功调用次数由 Fake 单元测试记录断言。 | 消除任意注入 Fake 的调用计数接口歧义，不新增生产 Protocol 或公共属性。 | Issue #19；Issue #21；SR-002 v0.2.7；AC-002-01～08；PR #20 |

| 2026-11-26 | 0.3.7 | GPT-6（ChatGPT） | 当前目标契约 | 将 Model Loop 可见输入和 Action Proposal 从 Callable ID 改为 Capability ID，Callable 仅由 Host 从已验证 Binding 内部解析 | 切换到 1.6.0 Capability-first 单一作者入口 | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.3.8 | GPT-6.2（ChatGPT） | §5 | 将 Skill Package 根目录共享 Schema / Script 加入模型按需资源视图，并纳入 Host Script Execution system Capability 的 Action 校验 | 使 LLM 可以使用公共 Script，但不暴露宿主路径或任意代码执行 | Issue #49；IR-008；SR-032 |
