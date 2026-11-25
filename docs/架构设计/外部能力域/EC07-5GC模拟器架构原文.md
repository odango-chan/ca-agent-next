> 迁移来源：env-5gc-sim/docs/architecture/env-5gc-sim-architecture.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 源文档定位：EC07 env-5gc-sim 模拟器总体架构原文  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# env-5gc-sim 架构与仓库边界

Status: Accepted  
Version: v0.7
Date: 2026-10-21

## 1. 目的

本文定义 `env-5gc-sim` 的目标定位、ownership、跨仓边界和长期依赖方向。

`env-5gc-sim` is the stable deterministic reference backend and remains in maintenance mode. The primary real-5GC validation path is `env-open5gs` plus `env-5gc-real`. This document preserves the simulator's ownership and semantic comparison boundaries; it does not make Open5GS parity a simulator expansion roadmap.

跨仓完整 simulation flow 见 `odango-chan/connectionagent/docs/simulation-end-to-end.md`；本文只定义 simulator 自己拥有什么、如何和 Runtime/Sandbox/Service Fabric/real 5GC integration 连接。

## 2. 一句话定位

```text
env-5gc-sim
  = ConnectionAgent deterministic 5GC reference world implementation
  = simulated 5GC domain-state authority
  = simulated 5GC fact/read source
  = simulated NF/reference behavior owner
  != Sandbox platform
  != Runtime / Harness
  != Network Observation owner
  != real Open5GS adapter
```

它回答：

> 在受控模拟 5GC 世界里，UE、注册、会话、PFCP/QoS、用户面等业务状态是什么，以及 simulated NF 在收到确定输入后如何改变这些状态？

## 3. 为什么独立拆仓

旧 `ca-sandbox` 同时混合：

```text
Environment lifecycle
fault orchestration
Observation / GroundTruth / Control
5GC domain state
5GC reference behavior
```

最后两项属于独立 5GC domain。拆出后形成：

```text
                         ConnectionAgent semantic layer
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
                env-5gc-sim                 env-5gc-real
           deterministic reference           real adapter
                  world                           │
                                                  ▼
                                           unmodified Open5GS
```

目标是 semantic parity，不是复制 Open5GS 内部实现。

## 4. env-5gc-sim owns

```text
5GC simulated domain state
  - UE identity/context
  - registration/auth/security state
  - AMF-side session/context where modeled
  - SMF/PDU Session state
  - DNN / S-NSSAI / PDU address
  - PFCP/resource state
  - QoS flows
  - UP connection / reachability state

Deterministic simulated NF/state-machine behavior
  - AMF/SMF/UPF-like reference endpoint behavior
  - request handling / response generation
  - deterministic pre-state validation
  - explicit commit points

5GC source-fact read/query seam
  - stable current-state reads
  - Runtime read-only Capability backend
  - Runtime ObservationSource backend

Simulation fixtures / seeds
  - deterministic initial 5GC domain state

Evaluator-only Source Fact read seam
  - only where evaluation needs restricted access to owner-native facts
```

具体字段、状态和值域由 domain/state/design 正文冻结，不能把 legacy Go struct 直接当 public contract。

## 5. env-5gc-sim does not own

```text
Agent-facing MCP
ConnectionAgent Tool eligibility
Runtime Capability admission
Authorization / Assurance
Procedure / Predicate verdict
ProviderContract / ProviderBinding authority
Runtime Outcome / OUTCOME_UNKNOWN / Reconcile policy
Environment lifecycle
fault policy / experiment scheduling
Network Observation / FabricEvent
protocol-boundary fault enforcement
Benchmark Verdict
GroundTruth access policy/publication
real Open5GS lifecycle/integration authority
```

保持：

```text
simulated 5GC source fact
!= Network Observation
!= Runtime execution fact
!= Predicate verdict
!= Benchmark Verdict
```

## 6. 与 ca-sandbox 的边界

```text
ca-sandbox
  = Environment generation / lifecycle semantics
  = deterministic scheduler / clock semantic owner
  = Sandbox-owned Environment / control Source Facts

ca-lab
  = Environment process / resource materialization

ca-benchmarks
  = Benchmark Case / GroundTruth / FaultProfile authoring

ca-benchmark-engine
  = Intervention orchestration
  = Oracle / Validity / Verdict

env-5gc-sim
  = simulated 5GC world/state
  = simulated NF behavior
  = 5GC operation + fact/read source
```

### 6.1 Environment lifecycle

Sandbox owns the Environment generation/reset semantics；ca-lab materializes/process-hosts the required resources，并由 composition attach `env-5gc-sim` world：

```text
Environment
  -> owns lifecycle/composition
  -> binds env-5gc-sim world/instance
  -> binds Service Fabric simulation lane
  -> binds Runtime Provider/read/ObservationSource
```

`env-5gc-sim` 不升级成平台 Environment manager。

### 6.2 5GC facts 不经 Sandbox relay

目标：

```text
Runtime read-only Capability ─┐
                              ├─> env-5gc-sim fact/read seam
Runtime ObservationSource ────┘
```

Sandbox 当前 `:8789` 中 5GC Observation 只属于迁移兼容；消费者切换后删除 relay。

Sandbox 继续发布自己拥有的 Environment/control Source Facts，但不复制 5GC state，也不接管 Benchmark intervention 或 Fabric boundary-fault facts。

### 6.3 GroundTruth 与 evaluator-only Source Fact

普通 Runtime 只能使用 admitted ordinary facts/evidence；评测若需要读取受限的 simulator state，则通过明确的 evaluator-only Source Fact seam 访问。

```text
ca-benchmarks GroundTruth
  = gold expected result

env-5gc-sim evaluator-only Source Fact
  = restricted owner-native actual fact

ca-benchmark-engine
  = Oracle / comparison / Verdict
```

因此 evaluator-only Source Fact 不是 private GroundTruth，也不是 Oracle。

## 7. 与 env-fabric 的边界

这是 simulation 架构中的关键边界。

```text
env-5gc-sim
  = simulated protocol participant / message source

env-fabric
  = protocol-boundary mediation
  = Network Observation owner
  = protocol-boundary fault enforcement
```

### 7.1 Simulation Network Observation

即使没有真实 socket/packet，Network Observation 仍统一由 Service Fabric 产生：

```text
source simulated NF
  -> simulated protocol message/envelope
  -> Service Fabric SIMULATED lane
  -> Network Observation / forwarding disposition
  -> destination simulated NF when delivered
```

`env-5gc-sim` 不发布第二套 `FabricEvent` / `NetworkObservation`。

详细局部设计见 `docs/design/network-observation-and-service-fabric.md`，架构决策见 `ADR-0003`。

### 7.2 真实与模拟 acquisition

```text
Simulation:
env-5gc-sim -> Service Fabric SIMULATED

Real NF:
unmodified Open5GS -> Service Fabric REAL_INLINE
```

两边使用相同 semantic Network Observation vocabulary，并通过 provenance 区分 acquisition mode。

## 8. Protocol fault 边界

协议边界 fault 不再由 simulator shortcut 直接改变 operation outcome。

以下由 Service Fabric 执行：

```text
drop
delay
reorder
message-level mutate/corrupt when supported
```

ca-benchmarks owns authored FaultProfile；ca-benchmark-engine owns intervention orchestration / binding；Service Fabric owns executable boundary lease、concrete enforcement、Network Observation 与 BoundaryFaultReceipt；simulator endpoint only changes domain state when a message is delivered and handled。

Simulator 可以支持 deterministic endpoint fixture，例如：

```text
NF rejects request
subscription/policy failure
resource exhaustion
unsupported request
```

这些是 endpoint behavior，不是 network fault。

### 8.1 Commit 与 response delivery 分离

例如 PFCP：

```text
request delivered to UPF-sim
  -> UPF-sim may commit PFCP resource
  -> response candidate generated
  -> response goes through Service Fabric separately
```

因此：

```text
response dropped
!= PFCP resource rolled back
```

这使 `OUTCOME_UNKNOWN` / reconcile 场景可以真实表达。

## 9. 与 ca-runtime 的边界

Runtime owns：

```text
Capability admission
RuntimeHost
Authorization / Assurance
Procedure
ProviderContract / ProviderBinding
ObservationSource binding/acquisition
NormalizedObservation / Evidence
Predicate verdict
Outcome / OUTCOME_UNKNOWN
Reconcile / Recovery
Tool eligibility
```

### 9.1 Agent read

```text
Agent
  -> ca-mcp
  -> Runtime read-only Capability
  -> env-5gc-sim fact/read seam
  -> ToolResult
```

普通管理/事实查询不要求伪造协议消息，因此可以不经过 Fabric。

### 9.2 Mutation

高层路径：

```text
Agent
  -> ca-mcp
  -> RuntimeHost
  -> Runtime admitted Capability
  -> ProviderBinding
  -> env-5gc-sim business operation
```

若 operation 内含被建模的 N2/N3/N4/N11 exchange，则具体 simulated message 必须经过 Service Fabric simulation lane，而不是 endpoint 之间直接跳状态。

### 9.3 Assurance

```text
Predicate
  -> Runtime ObservationSource
     ├─ env-5gc-sim 5GC domain facts
     └─ env-fabric Network Observation when required
  -> Evidence
  -> PASS / FAIL / UNKNOWN
```

Runtime 不读取 simulator private memory，也不把 simulator internal struct 当 Provider/Observation schema。

## 10. 与 ca-mcp 的边界

没有直接依赖：

```text
Agent-facing MCP = ca-mcp
```

`env-5gc-sim` 不建立 MCP Server。Agent 只看到 Runtime admitted Capability 经 ca-mcp 映射后的 Tool。

## 11. 与 env-5gc-real / unmodified Open5GS 的关系

```text
env-5gc-sim
  = reference simulated backend + fact source

env-5gc-real
  = real 5GC operation/fact adapter family

unmodified Open5GS
  = real target implementation
```

目标：

```text
same Runtime semantic Capability / Predicate expectation
                 │
          ┌──────┴──────┐
          ▼             ▼
     env-5gc-sim   env-5gc-real -> Open5GS
```

切换 simulation / real_nf 尽量只改变 Provider/ObservationSource/Fabric acquisition binding，不改变 Skill、Predicate 和 Agent-facing Tool 语义。

## 12. Deterministic ordering / scheduler

ca-sandbox 拥有 reference-simulation deterministic scheduler/clock 语义；ca-lab 负责相应资源 materialization。Simulation Environment 必须为 `env-5gc-sim` 与 Service Fabric simulated lane 绑定同一 scheduler domain。

需要支持：

```text
logical sequence
causal ordering
repeatable delay/reorder
scheduled delivery
world/source revision correlation
```

组件本地 wall clock 不能作为跨组件因果 authority。

具体 scheduler machine contract 后续冻结。

## 13. Protocol fidelity

首版采用：

```text
Level 1 — semantic protocol envelope
```

至少表达 interface/protocol/message kind/direction/transaction/correlation/fault-match fields，支撑 drop/delay/reorder/timeout/UNKNOWN。

后续按需增加：

```text
Level 2 — encoded protocol message/packet
```

用于 IE/header corruption、parser、协议互操作等测试。

不因为 Level 2 可能存在，就把首版 simulator 做成另一个 Open5GS。

## 14. Public / private boundary

至少区分：

```text
stable operation contract
stable 5GC fact/read contract
simulated protocol-envelope producer contract
private simulator implementation
evaluator-only Source Fact seam
```

内部 map/cache/FSM bookkeeping 不是 public schema。

## 15. 现有 ca-sandbox/simulator 迁移分类

迁入/重写：

```text
5GC domain state
registration/session/PFCP/QoS/connectivity transitions
5GC business operation behavior
5GC source-state query logic
5GC endpoint/protocol-event generation
5GC fixtures/seeds
```

按 owner 分流、不能迁入 simulator：

```text
ca-sandbox
  - Environment generation / lifecycle semantics
  - deterministic scheduler
  - Sandbox-owned Environment/control facts
  - non-5GC workload state where owned

ca-lab
  - process/resource materialization

ca-benchmarks
  - Benchmark Case / GroundTruth / FaultProfile authoring

ca-benchmark-engine
  - Intervention orchestration / Oracle / Validity / Verdict
```

迁到/绑定 Service Fabric，而不是搬入 simulator：

```text
protocol-boundary drop/delay/reorder/mutate
Network Observation owner-native output
message forwarding disposition
protocol-event FaultReceipt
```

旧 `UnknownDisposition / StateMutation / responseSuppressed` 类 simulator shortcut 只能作为 migration inventory，不成为新 contract。

## 16. Dependency direction

```text
Sandbox Environment composition + scheduler binding
   -> env-5gc-sim lifecycle/seed/evaluator-only Source Fact seams

ca-lab
   -> process/resource materialization

ca-benchmark-engine
   -> pre-resolved intervention binding
   -> env-fabric executable boundary lease

env-5gc-sim protocol candidate
   -> env-fabric simulated acquisition

Runtime Provider/read adapter
   -> env-5gc-sim stable operation/fact contract

Runtime ObservationSource
   -> env-5gc-sim domain facts
   -> env-fabric Network Observation

env-5gc-sim
   -X-> ca-runtime internals
   -X-> ca-mcp
   -X-> Agent Host
```

如需 neutral shared schema，应通过 owner contract/ADR 明确，不直接反向依赖 private package。

## 17. Machine-contract readiness

仓库边界、C2/C6 owner-local human design、one-process-one-world process profile 与 HTTP/JSON owner API 已冻结；当前不再把这些 ownership/transport choices 当成开放问题。详见 ADR-0004、ADR-0005 与 `design/versioning-and-compatibility.md`。

本仓拥有：

```text
C2 env-5gc-sim world identity / generation / revision + typed fact/read
   -> DESIGN FROZEN
   -> canonical schema / implementation OPEN

C6 env-5gc-sim operation contract
   -> DESIGN FROZEN
   -> canonical schema / implementation OPEN

Process owner surface
   -> DESIGN FROZEN
   -> ProcessConfig/Identity/Health/Reset/Error canonical schema PRESENT
   -> owner HTTP OpenAPI 3.1 PRESENT
   -> implementation OPEN
```

C2 同时包含 evaluator-only Source Fact 的访问边界，但不拥有 Benchmark GroundTruth / Oracle。

本仓消费但不重新定义：

```text
C1 Sandbox Environment identity / deterministic scheduler binding
C3/C4 Service Fabric simulated acquisition / Network Observation contracts
C5 Benchmark Engine intervention binding + Fabric executable lease
C7 Runtime Provider/read/ObservationSource binding
C8 typed evidence closure / retention requirements
```

首个 N4/PFCP slice 可以在 broader 5GC domain 扩展仍处于 Proposed 时开始实现；前提是只使用已经冻结的首片 state/operation/fact semantic，不把未冻结的 registration/N11/N2/N3/QoS 扩展偷带进实现。

## 18. 不变量

```text
env-5gc-sim owns simulated 5GC domain state and NF behavior.
env-5gc-sim does not own Network Observation.
env-fabric owns Network Observation for simulated and real acquisition.
Protocol-boundary faults are enforced at Service Fabric, not by editing simulator outcome.
5GC domain facts remain direct from the actual fact owner to Runtime.
Response delivery is separate from destination-side domain commit.
Runtime owns Assurance/Outcome/Reconcile/Tool eligibility.
ca-sandbox owns Environment generation and deterministic scheduler semantics.
ca-lab owns process/resource materialization.
First process profile is one process / one live world; same-world reset changes worldGeneration.
env-5gc-sim owner transport is HTTP/JSON; ca-mcp remains the only Agent-facing MCP.
ca-benchmarks owns Benchmark Case/GroundTruth/FaultProfile authoring.
ca-benchmark-engine owns intervention orchestration and Oracle/Validity/Verdict.
GroundTruth is Benchmark-authored gold truth; evaluator-only Source Fact is a restricted access policy.
Open5GS is a semantic reference, not a struct-copy template.
```

## GroundTruth 术语基线

```text
GroundTruth = ca-benchmarks 标准答案 / gold expected result
env-5gc-sim = simulated 5GC Authoritative Source Fact owner
evaluator-only = Source Fact access policy
```

本仓不拥有 GroundTruth。需要隐藏评测事实时，本仓只提供 evaluator-only Source Fact seam；Evaluator/Engine 使用 Evidence + Oracle 与 Benchmark GroundTruth 比较。


## No mandatory projection layer

Reference simulation core path does not insert a simulator-owned projection between source facts/protocol semantics and their consumers.

~~~text
5GC fact -> direct governed read
protocol candidate -> Service Fabric acquisition input
Fabric -> owner-native Network Observation output
~~~

UI/evaluator derived views remain optional end-stage consumers, not intermediate authorities.
