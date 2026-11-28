> 迁移来源：env-5gc-sim/docs/design/network-observation-and-service-fabric.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：模拟协议 Envelope、Fabric Observation、Commit Point 与 response-loss 设计  
> 迁移追踪：ca-agent-next Issue #12。env-5gc-sim 同时包含 5GC reference simulator 与 Mock AMF test peer；两者在 Next 设计中分开描述。

---

# Simulated Protocol 与 Service Fabric 边界

Status: Accepted / Semantic Baseline  
Version: v0.3  
Date: 2026-09-22

## 1. 目的

本文定义 `env-5gc-sim` 如何产生模拟协议交互，以及这些交互如何通过 `env-fabric` 形成统一的 Network Observation 与协议边界故障语义。

跨仓完整端到端流程以 `odango-chan/connectionagent/docs/simulation-end-to-end.md` 为 authority；本文只定义 `env-5gc-sim` 一侧的局部 contract。

核心原则：

```text
env-5gc-sim owns simulated NF/domain behavior.
env-fabric owns Network Observation and protocol-boundary fault enforcement.
```

因此本仓不创建第二套 `FabricEvent` / `NetworkObservation` authority。

## 2. 两类事实必须分开

`env-5gc-sim` 直接拥有：

```text
UE registration state
AMF/SMF session context
PFCP/resource state
QoS state
user-plane reachability
simulated endpoint/NF behavior
```

Service Fabric 拥有：

```text
message candidate observed at mediated boundary
message forwarded / dropped / delayed / reordered / mutated
protocol transaction correlation
message/network ordering
capture/artifact refs when available
```

例如：

```text
env-5gc-sim:
  PFCP resource exists = true

Service Fabric:
  PFCP Session Establishment Response was dropped
```

两者可以同时为 Runtime/Benchmark 提供 Evidence，但互不替代。

## 3. 不允许的 shortcut

新的 simulator 不应继续用旧式：

```text
UnknownDisposition
StateMutation
responseSuppressed
```

之类字段直接把“协议边界故障 + domain effect + caller knowledge”揉成一个 simulator mutation result。

特别是：

```text
transition commits but response is lost
```

必须通过真实的模拟 endpoint + Service Fabric 边界表达，而不是由 simulator 一次调用直接伪造。

## 4. Simulated Protocol Message/Envelope

`env-5gc-sim` 在需要模拟协议交互时，应产生一个稳定的 protocol-message/envelope seam。

当前 C3 machine contract 已由 `env-fabric` 发布并被本仓 production adapter 消费：`SimulatedProtocolEnvelope` 属于 `env-fabric` 的 SIMULATED acquisition 输入合同；`env-5gc-sim` 直接作为 producer 使用 owner contract/fixture，不定义平行 projection。该 contract 至少表达：

```text
source endpoint ref
destination endpoint ref
interface
protocol
message kind
direction
transaction/session correlation material
subject refs when available
causal parent ref
logical ordering/time material
semantic payload or encoded payload descriptor
```

该 envelope 表示：

> simulated source endpoint 正准备在某协议边界发送一条消息。

它不是 Network Observation；是否真正 delivered、是否应用 fault、最终 Fabric event ref 由 Service Fabric 决定。

### 4.1 SIMULATED lane 的 emit / submit 语义

本文后续出现的“endpoint emits request/response”统一表示：

```text
env-5gc-sim endpoint
  -> build internal protocol message candidate
  -> encode owner-owned SimulatedProtocolEnvelope
  -> explicitly submit through C3 to Service Fabric
```

不表示：

```text
Service Fabric polls env-5gc-sim for messages
env-5gc-sim directly invokes the destination endpoint
env-5gc-sim creates FabricEvent / NetworkObservation
```

SIMULATED lane 的固定语义是：

```text
produce candidate
-> C3 submit
-> Fabric observe
-> Fabric disposition
-> delivery callback (if admitted)
-> endpoint ACK
-> Fabric DELIVERED (only after canonical ACK)
```

因此 Service Fabric 的“感知”发生在 producer 显式 submit 进入 Fabric authority boundary 时，不是轮询式发现。

## 5. Endpoint / Network 分工

一个需要 mediation 的协议 exchange：

```text
source simulated endpoint
  -> build message candidate
  -> C3 submit SimulatedProtocolEnvelope
  -> Service Fabric observes and assigns owner refs
  -> forwarding/fault disposition
  -> delivery callback
  -> destination simulated endpoint if delivered
  -> canonical ACK back to Service Fabric
```

因此：

```text
env-5gc-sim endpoint
  = protocol participant behavior + domain state transition

env-fabric
  = protocol boundary mediation + Network Observation + boundary fault
```

Service Fabric 不直接修改 AMF/SMF/UPF domain state；它只决定消息是否/何时/以什么允许的变体到达 destination endpoint。

## 6. Request/Response Commit Point

Simulator 必须明确每类 simulated NF 的 commit point。

以 PFCP Establishment 为例：

```text
SMF builds request candidate and submits it through C3
  -> no UPF resource exists yet

Fabric observes / assigns messageRef / forwards request
  -> UPF endpoint receives request through Fabric callback

UPF handles request
  -> PFCP resource transition commits

UPF builds response candidate and submits it through C3
  -> response delivery is a separate Fabric-owned network fact
```

因此：

```text
response dropped
!= UPF resource rolled back
```

这为 Runtime `OUTCOME_UNKNOWN` + reconcile 提供真实的非原子边界。

## 7. Happy Path

```text
simulated SMF
  -> build PFCP Establishment Request candidate
  -> C3 submit SimulatedProtocolEnvelope

Service Fabric
  -> accept submission / assign messageRef
  -> OBSERVE request
  -> disposition
  -> delivery callback to UPF

simulated UPF
  -> validate request
  -> create PFCP resource
  -> ACK request delivery
  -> build PFCP Establishment Response candidate
  -> C3 submit response envelope

Service Fabric
  -> accept submission / assign response messageRef
  -> OBSERVE response
  -> disposition
  -> delivery callback to SMF

simulated SMF
  -> consume response
  -> ACK response delivery
  -> advance SM session state
```

Network Observation 来自 Service Fabric；PFCP resource / SM Session facts 来自 `env-5gc-sim`。

## 8. Response-loss Fault

```text
simulated SMF
  -> build PFCP request candidate
  -> C3 submit request

Service Fabric
  -> OBSERVE / FORWARD / deliver request

simulated UPF
  -> commits PFCP resource
  -> build response candidate
  -> C3 submit response

Service Fabric
  -> OBSERVE response
  -> matches one-shot fault
  -> DROP response before SMF callback
  -> produces Network Observation / BoundaryFaultReceipt

simulated SMF
  -> remains without successful response knowledge
```

此时 simulator private/domain truth 与 caller knowledge可以不同：

```text
UPF domain truth:
  resource exists

SMF/provider-visible knowledge:
  response not received

Runtime:
  may become OUTCOME_UNKNOWN
```

`env-5gc-sim` 不应把 Runtime Outcome 写进自己的 world state。

## 9. Fault 分类

首个 response-loss slice 额外冻结：ca-benchmark-engine Intervention Controller 在 mutation 开始前直接向 Service Fabric 安装 executable boundary lease。Service Fabric 依据自己的 FabricEvent 与 shared deterministic scheduler 本地激活/命中；Sandbox/Lab 不作为 protocol intervention relay。



### 9.1 Protocol-boundary fault

以下由 Service Fabric 执行：

```text
drop
delay
reorder
message-level mutate/corrupt when fidelity supports it
```

ca-benchmarks owns authored FaultProfile；ca-benchmark-engine owns intervention orchestration；Service Fabric owns actual protocol-boundary enforcement facts。

### 9.2 Endpoint/reference-behavior fixture

Simulator 可以独立模拟：

```text
NF rejects request
subscription/policy causes deterministic failure
resource exhaustion fixture
unsupported operation
internal deterministic endpoint error
```

这些是 simulated NF behavior，不应记录成“network message dropped”。

首阶段继续排除不受协议边界控制的真实 NF internal timing-window fault，除非后续明确扩 scope。

## 10. Service Fabric Acquisition Mode

Simulation 使用：

```text
Service Fabric acquisitionMode = SIMULATED
```

Real Open5GS 使用：

```text
Service Fabric acquisitionMode = REAL_INLINE
```

二者应投影到相同的 semantic Network Observation vocabulary。

`env-5gc-sim` 不根据 mode 改写自己的业务事实 contract；mode 只影响 protocol-event acquisition/transport/provenance。

## 11. Fidelity Level

### Level 1 — Semantic protocol

最低必须支持：

```text
interface
protocol
message kind
direction
transaction/correlation refs
semantic fields required for matching
```

目标场景：

```text
drop / delay / reorder
timeout / response loss
OUTCOME_UNKNOWN
correlation / event-trigger DSL
```

### Level 2 — Encoded protocol

按需加入：

```text
real encoded PFCP/SBI/NAS/GTP message or packet
IE/header-level mutation
parser/interoperability behavior
PCAP-like encoded artifacts where meaningful
```

不因为未来 Level 2 需求，让首版 simulator 复制完整 Open5GS protocol stack。

## 12. Deterministic Ordering / Time

`env-5gc-sim` 与 Service Fabric simulated lane 必须共享 Environment-scoped deterministic ordering/scheduler context。

本仓至少需要接受/传播：

```text
logical sequence or causal token
logical time when required
scheduled-delivery identity
```

本仓不能用本地 wall clock 自行决定 delay/reorder 的 authoritative顺序。

deterministic scheduler/clock 的 reference-simulation 语义 owner 已冻结为 `ca-sandbox`；`ca-lab` 负责资源 materialization，simulator 与 Fabric 只消费同一 scheduler binding。Environment composition 必须保证二者位于同一 ordering domain。

## 13. Correlation

Simulator 只提供自己真正知道的关联信息：

```text
endpoint identity
UE / PDU Session subject refs
protocol transaction/session refs
causal parent message ref when known
Runtime invocation correlation supplied through admitted integration
```

禁止 simulator 或 Fabric 通过 timestamp proximity 猜 `runId` / Product Task identity。

跨域 correlation 必须由显式 ref 建立。

## 14. Agent Read 不自动经过 Fabric

管理/事实查询，例如：

```text
inspect registration
inspect PDU Session
inspect PFCP resource
```

可以直接走 `env-5gc-sim fact/read seam`，不要求伪造一条 N11/N4 消息。

只有 Capability 的业务语义本身要求真正的协议/traffic action，例如 active user-plane probe，才进入对应 Network Observation path。

## 15. 与 Runtime Assurance 的关系

Runtime 可以同时消费：

```text
env-5gc-sim domain fact
+
Service Fabric Network Observation
```

例如恢复逻辑可组合：

```text
Network:
  PFCP request forwarded
  PFCP response dropped

Domain:
  PFCP resource exists
```

但是否据此判定 `PASS / FAIL / UNKNOWN` 属于 Runtime Predicate/Assurance，不属于 simulator/Fabric。

## 16. 与 GroundTruth / evaluator-only Source Fact 的关系

跨仓冻结：

~~~text
GroundTruth
  = ca-benchmarks 的 gold expected result

env-5gc-sim hidden/current world facts
  = env-5gc-sim Authoritative Source Facts
  = evaluator-only when access policy requires
~~~

因此 exact endpoint commit disposition、hidden world state 等若只允许 Evaluator 读取，称为 evaluator-only Source Facts，而不是 private GroundTruth / Oracle Fact。

该 restricted seam 不经过 Service Fabric，也不自动进入普通 Runtime ObservationSource。Service Fabric 的 response dropped 则是独立 Network Source Fact/Evidence。

## 17. 当前 machine-contract 状态

首个 N4/PFCP slice 所需的 C1/C3/C4/C5 machine contract 已进入实际跨仓路径：

```text
Service Fabric-owned SimulatedProtocolEnvelope + endpoint registration/delivery
canonical messageRef / deliveryAttemptRef / ACK
FabricEvent / disposition / BoundaryFaultReceipt
Sandbox-owned scheduler binding consumed by simulator/Fabric
explicit transaction/correlation refs
fault match fields
semantic-only payload availability
```

`env-5gc-sim` 只消费这些 owner contract，不复制成第二套 Fabric authority。后续 encoded-payload / Level 2 fidelity 可以扩展 profile，但不改变本节的 submit/observe/ownership 语义。

## 18. 不变量

```text
env-5gc-sim owns simulated endpoint/domain behavior, not Network Observation.
SIMULATED protocol traffic enters Fabric only through explicit producer C3 submit; Fabric does not poll env-5gc-sim.
env-5gc-sim never bypasses Fabric by directly delivering a mediated protocol message to the destination endpoint.
Service Fabric owns Network Observation in simulation and real inline modes.
Network faults are enforced at the Fabric boundary.
Simulator endpoint/domain commit points are independent from response delivery.
Response loss does not roll back an already committed domain transition by definition.
Management fact reads do not need fake protocol traffic.
Simulation Level 1 uses semantic protocol events; full packet encoding is optional later fidelity.
Runtime Outcome and Predicate verdict remain outside env-5gc-sim.
```
