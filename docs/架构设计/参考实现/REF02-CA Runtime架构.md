> 迁移来源：ca-runtime/docs/architecture/runtime-architecture.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 源文档定位：REF02 独立 Go Runtime 参考架构，不是 Next Python Runtime 的实现证明  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# ConnectionAgent Runtime 架构

Status: Accepted  
Version: v1.4  
Date: 2026-09-23

## 1. 定位

`ca-runtime` 是 ConnectionAgent 的**确定性可靠执行内核 / Harness authority**。它接收已经经过 Host/Agent 选择并满足 Runtime public contract 的执行请求，在唯一的 Runtime authority 内完成 capability admission、ConnectionAgent Tool eligibility、可靠性校验、副作用 dispatch、Outcome、Observation/Evidence 与恢复。

它不是 Agent Host，不拥有 LLM planning loop；也不是 MCP Gateway。Agent-facing MCP 已由独立 `tool-mcp-gw` owning。

## 2. 当前系统关系

```text
Goal / ProductTask / Agent Loop
        │
        ▼
Agent Host / DSH / Native Agent
        │ standard MCP
        ▼
      tool-mcp-gw
  Agent-facing edge adapter
        │ adapts to
        ▼
ca-runtime::RuntimeHost.v1    <- Runtime-owned public port
        │
        ▼
    Runtime core / Harness
        │
        ├─ Capability / Artifact admission
        ├─ CA Tool eligibility resolution
        ├─ RequestStore
        ├─ Authorization / Assurance
        ├─ ExecutableProcedure
        ├─ ProviderBinding / Dispatch
        ├─ Outcome / OUTCOME_UNKNOWN
        ├─ Observation / Evidence / Predicate
        ├─ Reconcile / Recovery
        └─ RunRecord / RunEvent
        │
        ▼
      Provider / ObservationSource
        │
        ▼
 Service Fabric / NF / Sandbox / External System
```

这里的 `Host -> tool-mcp-gw -> RuntimeHost` 只是 Agent Tool Call 的调用时序，不代表 `tool-mcp-gw` 在架构层级上位于 Runtime 之上。Runtime 是 core，`RuntimeHost.v1` 是 Runtime 自己拥有的 public port，`tool-mcp-gw` 只是该 port 的 Agent-facing adapter。System Control、Benchmark/Lab 等可信 consumer 可按各自 owner contract 直接使用 RuntimeHost。Host 负责把 Runtime 允许暴露的 ConnectionAgent Tool 机械注册给模型；Host 可以进一步收缩，但不能扩大 Runtime/Harness 给出的 ConnectionAgent capability eligibility。

## 3. Ownership

Runtime owns：

```text
RuntimeHost.v1
CapabilityContract.v1
ProviderContract.v1
Artifact / Variant runtime admission
ConnectionAgent capability eligibility / model-visible upper bound
requestId / RequestStore authority
Run / RunEvent authority
Deterministic Procedure execution
Authorization / Assurance
ProviderBinding / dispatch barrier
Runtime Outcome / OUTCOME_UNKNOWN
Observation binding / acquisition governance
Evidence / Predicate execution
Reconcile / Recovery
Runtime execution trajectory
```

Runtime does not own：

```text
Agent / LLM nondeterministic loop
Agent-facing MCP protocol adapter
Host-local non-ConnectionAgent Tools
Skill source authoring/compiler
Skill Qualification verdict
Benchmark Verdict / Certification
Sandbox Fault control / GroundTruth
Provider domain truth outside returned knowledge/evidence
whole Agent Session / Agent trajectory
```

Runtime 只能对 **ConnectionAgent Tool boundary** 给出 authoritative eligibility。若某个通用 Host 还挂载 shell、filesystem、browser 或其他 MCP server，这些额外工具由 Host/System composition 自己治理，不能被误写成 Runtime 已经控制整个 Agent Tool universe。

## 4. RuntimeHost.v1 是公开机器边界

Runtime 内部 package 不是跨仓 integration contract。外部 adapter/Host 必须面向 `RuntimeHost.v1`：

```text
tool-mcp-gw -> ca-runtime::RuntimeHost.v1
Console/control adapter -> ca-runtime::RuntimeHost query/control
Benchmark/Lab trusted integration -> ca-runtime::RuntimeHost
```

禁止把以下实现细节升级成跨仓 API：

```text
runtimeengine internals
RequestStore implementation
RunStore implementation
Provider implementation
private Procedure program counter
raw ObservationSource implementation
```

这样 Runtime 内部可以继续重构，而 tool-mcp-gw、Console、Benchmark 等只依赖稳定 owner contract。

## 5. Identity

```text
callId
  = upstream Agent/MCP trajectory correlation
  = Runtime 可记录，但不是 Runtime idempotency key

requestId
  = Runtime logical execution request idempotency identity
  = scope: (host, requestId)

runId
  = Runtime authoritative execution identity

operationRef
  = higher-level Product / Prepared Run / Control identity where contract需要
```

必须保持：

```text
JSON-RPC id != requestId
MCP session id != requestId
MCP task id != requestId
callId != requestId
```

Runtime RequestStore 拥有 durable claim/replay；tool-mcp-gw 不复制 replay database。

## 6. Capability Catalog 与 Tool eligibility

必须区分三个集合：

```text
A. Runtime Capability Catalog
   = Runtime 已 admission 的 ConnectionAgent Capability 全集

B. Runtime Resolved CA Toolset
   = 当前 resolved Agent / Skill / Context / Environment 最多允许模型看到的 CA Capability 子集

C. Host model-visible CA Tools
   = Runtime Resolved CA Toolset 经 tool-mcp-gw/Host 机械映射后的实际可见集合
```

保持：

```text
Host model-visible CA Tools
  ⊆ Runtime Resolved CA Toolset
  ⊆ Runtime Capability Catalog
```

Runtime/Harness 解析 authoritative CA Tool eligibility 时可以消费来自各 owner 的冻结输入，例如：

```text
selected/admitted Skill or Artifact
SkillContract allowedResources.capabilities
Context / Template resolved material
AgentProfile / System composition constraints
Environment capability availability
platform / security policy
implementation compatibility
```

这些输入的 source authority 不因此迁移到 Runtime；Runtime 负责把它们组合成**可执行时可验证的 ConnectionAgent capability eligibility boundary**。

`assurance/contract.yaml` 中的 `allowedResources.capabilities` 是 Skill 允许使用 Capability 的重要上限输入，但不是 MCP Tool catalog 本身，也不意味着列出的每个 Capability 都必须直接暴露给模型。最终是否 model-visible 还要经过 Runtime admission、effect/visibility metadata、Environment/Policy 等约束。

必须进一步区分：

```text
visible eligibility
  = 允许模型考虑/调用该 ConnectionAgent Capability

execution eligibility
  = 某一次实际调用继续通过 Authorization / Assurance / binding / dispatch gate
```

出现在模型 Tool 列表里不等于副作用已经授权。

当前 `TOOL-01 v2` 已实现并验证 `AGENT_INSTANCE_BASE` 与 `GOAL_EXECUTION` 两层 resolution。具体 request/response、digest、fail-closed 与 compatibility 语义见 `../design/resolved-ca-toolset.md`；live status 与 evidence 仍以 `../WORK.md` / `../TRACEABILITY.md` 为准。

## 7. Deterministic Procedure

Agent/Host 负责非确定性的目标理解、上下文组装，以及在 Runtime 允许暴露的 Toolset 中进行能力选择和规划。进入 Runtime 后，Runtime 只执行已经准入并冻结的 executable material。

目标模型：

```text
Runtime-resolved CA Toolset
        ↓
Agent decision / selected capability or procedure
        ↓
RuntimeHost request
        ↓
Artifact/Variant/entrypoint resolution
        ↓
ExecutableProcedure
        ↓
Authorization / Assurance / Binding
        ↓
Provider side effect or read path
        ↓
Outcome / Observation / Evidence / Reconcile
```

Runtime 当前架构只以 RuntimeHost / RunStore / Provider / Outcome / Evidence / Reconcile 为权威执行边界；测试或历史工具不得成为第二套运行时 authority。

## 8. Provider boundary

Provider 只报告它知道的 operation knowledge / result / evidence；Runtime 拥有最终执行语义：

```text
Provider reports knowledge.
Runtime owns authoritative Outcome.
Runtime owns OUTCOME_UNKNOWN handling.
Runtime owns Reconcile / retry fence.
```

Provider 可以通过 native、HTTP、gRPC、Service Fabric、MCP 等 transport 实现。Transport family 不改变 Runtime authority。

### Provider MCP 与 tool-mcp-gw

```text
Agent-facing call path:
Agent Host -> tool-mcp-gw -> ca-runtime::RuntimeHost.v1

Provider-facing:
Runtime -> MCP Provider adapter -> Provider MCP server
```

二者完全不同。Provider `tools/list` discovery 只用于 ProviderBinding admission，不能直接扩大 Agent Tool catalog。

## 9. Observation / Evidence

Observation 不按“给 Agent”或“给 Assurance”分成两套事实系统。

事实类型按来源/语义区分：

```text
Network Observation
  = 网络/协议边界发生了什么
  = typical owner: Service Fabric

Environment Observation
  = 当前环境/业务状态是什么
  = typical owner: Sandbox / Environment owner / admitted state source
```

同一套 Runtime Observation acquisition 基础设施可以被两类受治理消费者使用：

```text
Agent planning
  -> model uses Runtime-resolved admitted read-only Capability
  -> tool-mcp-gw Tool when MCP is used
  -> Runtime read-only execution
  -> ObservationSource / Provider read path
  -> trusted fact returned to Agent

Runtime Assurance
  -> Procedure / precondition / postcondition
  -> Predicate
  -> required Observation
  -> ObservationSource
  -> Evidence
  -> PASS / FAIL / UNKNOWN
```

`SKILL.md` 的默认职责不是枚举 Tool。它主要告诉模型：

```text
什么时候必须获得当前事实而不能猜
哪些事实之间不能相互推断
哪些业务边界不能绕过
```

模型通常应根据当前可见 read-only Tool 的 name/description/schema 自己选择合适的 Capability。只有存在领域歧义、多个 Tool 语义非常接近且模型容易选错时，`SKILL.md` 才需要显式推荐某个业务语义 Capability。

`SKILL.md` 不拥有 Tool eligibility、ObservationBinding、endpoint、Provider mapping、freshness 实现或 provenance wiring。

必须保持 authority 分离：

```text
Agent inspection result = planning input
Runtime Predicate result = assurance verdict
```

模型刚查询过某个事实，不代表 Runtime postcondition 自动 PASS；Runtime Assurance 也不依赖模型必须先查询。Runtime 可以在 binding/provenance/freshness 等条件满足时复用同一条 Observation，否则重新 acquire 或得到 `UNKNOWN`。

不引入额外的 `Planning Observation` 或 `Agent Observation Projection` 类型。

GroundTruth 仍属于 Environment/Evaluator owner，不能因为同样描述状态就自动进入 production Observation authority。

## 10. Run 与 trajectory

Runtime owns：

```text
RunRecord
RunEvent
Runtime ordered execution facts
Runtime Execution Trajectory
```

Agent Host owns：

```text
Goal / ProductTask
model request / response
planning / proposal
Agent turn/call activity
cross-Run Agent causal history
```

统一视图只能通过明确的 correlation refs 组合，不能创建第二个事实 authority。

## 11. Reliability

### Host RESULT_UNKNOWN

`tool-mcp-gw`/Host transport 没拿到确定 Runtime response，只能得到 Host-level uncertainty：

```text
Host RESULT_UNKNOWN
!= Runtime OUTCOME_UNKNOWN
```

### Runtime OUTCOME_UNKNOWN

Runtime 已进入 authoritative execution，并且外部副作用 commit knowledge 不确定时，Runtime 才产生 `OUTCOME_UNKNOWN` 并进入 Reconcile/Recovery。

### Disconnect

```text
caller wait lifecycle
!= Runtime business execution lifecycle
```

上游断开不能自动变成业务取消。显式 cancellation 必须走 Runtime-owned control contract。

## 12. Nodus

Runtime 先拥有正确的领域 contract；Nodus 只承载被多个独立消费者证明同义的薄机械能力，例如 canonical digest/profile/conformance。Nodus 不拥有 Runtime Outcome、Run sequence、ProviderBinding、Procedure progression 或 Agent trajectory。

详细见 `nodus-integration.md`。

## 13. Repository / Public Go Surface

`RuntimeHost.v1` 是跨仓 Runtime machine boundary；Runtime 内部 package 布局不得反向扩展成新的跨仓 contract。

顶层 Go package 是否 public 必须是显式兼容承诺，而不是历史目录遗留。每个 public root 至少需要：

```text
real cross-module consumer
+ owning contract
+ compatibility commitment
+ focused/consumer tests
```

默认规则：

```text
public by explicit contract
private/internal by default
provider/observation adapters are implementation details unless proven otherwise
stores/execution/composition are internal unless a stable Go API is explicitly owned
```

中央 Go layout profile 是当前 public/private surface 的 machine authority。新增或改变 public root 必须先证明真实 consumer、owner contract 与测试，并同步 `odango-chan/connectionagent/configs/go-repository-layout.json`。

禁止为了目录整齐而先搬 package、后补 consumer reasoning；也禁止长期保留无 consumer 的 forwarding package。

## 14. Compatibility policy

Runtime 不承诺已退休 surface 的兼容入口。Agent-facing MCP 归 `tool-mcp-gw`；Runtime-owned model/LLM bootstrap 不属于 Runtime；无真实 consumer 的旧 package/flag/alias 直接删除，不建立长期 forwarding shim。

Provider-side MCP adapter 是允许的 concrete Provider transport，不属于 Agent-facing MCP compatibility。

## 15. 架构不变量

```text
Runtime execution authority is transport-independent.
Agent-facing MCP belongs to tool-mcp-gw.
RuntimeHost.v1 is a ca-runtime-owned public port of the Runtime core.
Runtime/Harness owns authoritative ConnectionAgent capability eligibility.
Host-visible CA Tools are a subset of the Runtime-resolved CA Toolset.
Host may narrow ConnectionAgent Tools; it may not widen Runtime authority.
Tool visibility does not bypass per-call Authorization/Assurance.
Agent/LLM loop is outside Runtime.
Provider transport does not grant Agent authority.
requestId is Runtime idempotency identity.
Run/RunEvent are Runtime execution facts.
Provider reports knowledge; Runtime owns Outcome/Reconcile.
Agent read-only inspection and Assurance may share Observation acquisition/source.
Agent inspection result is planning input, never Predicate verdict authority.
Runtime Assurance does not depend on prior Agent inspection.
SKILL.md primarily defines epistemic/domain constraints; Tool selection is normally model-driven within the Runtime-resolved Toolset.
Network Observation and Environment Observation remain distinct fact classes.
Host RESULT_UNKNOWN != Runtime OUTCOME_UNKNOWN.
Transport disconnect != business cancellation.
OUTCOME_UNKNOWN never authorizes blind retry.
Execution governance is Runtime-owned GOVERNED | DIRECT and Benchmark-neutral.
Tool visibility and execution governance are independent axes.
DIRECT reuses Runtime ProviderBinding/transport and never executes Harness governance.
```