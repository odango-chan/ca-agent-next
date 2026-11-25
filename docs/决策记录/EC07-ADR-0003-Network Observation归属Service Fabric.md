> 迁移来源：env-5gc-sim/docs/decisions/ADR-0003-network-observation-via-service-fabric.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：源仓架构决策记录；仅适用于 env-5gc-sim 所有权边界。  
> 迁移追踪：ca-agent-next Issue #12。以下保留原始决策和状态。

---

# ADR-0003 — Simulation Network Observation 统一经 Service Fabric

Status: Accepted  
Version: v0.2  
Date: 2026-09-18

## Context

`env-5gc-sim` 拆出后同时涉及两类事实：

```text
5GC domain fact
  = UE/Session/PFCP/QoS/connectivity 当前状态

Network Observation
  = N2/N3/N4/N11 协议边界发生了什么
```

如果 simulator 自己同时发布 Network Observation，会和真实环境中的 `ca-service-fabric` 形成两套网络事实 authority，并导致 simulation/real_nf Benchmark 使用不同事件语义。

旧 `ca-sandbox/simulator` 还存在通过 `UnknownDisposition`、`StateMutation`、response suppression 等 shortcut 同时表达 domain effect 与网络故障的历史实现，这不适合作为新架构长期 contract。

## Decision

Simulation 中的 Network Observation 继续由 `ca-service-fabric` 统一拥有。

```text
env-5gc-sim
  = simulated NF/domain behavior
  = simulated protocol message/event source

ca-service-fabric
  = simulated protocol mediation
  = protocol-boundary fault enforcement
  = Network Observation owner / output authority
```

目标链路：

```text
source simulated NF
  -> simulated protocol message/envelope
  -> Service Fabric SIMULATED lane
  -> delivery/fault disposition
  -> destination simulated NF when delivered
```

Service Fabric `SIMULATED` 与真实环境 `REAL_INLINE` acquisition 投影到同一 semantic FabricEvent/Network Observation vocabulary，并通过 provenance 区分 acquisition mode。

## Domain fact remains direct

本 ADR 不改变 ADR-0002 的 5GC fact-owner direct 原则。

```text
5GC Domain Observation
  Runtime -> env-5gc-sim fact/read seam

Network Observation
  Runtime -> ca-service-fabric
```

因此 simulation 下 Runtime 可以同时读取：

```text
env-5gc-sim:
  PFCP resource exists

ca-service-fabric:
  PFCP response dropped
```

两条事实各自保持 authority。

## Fault consequence

协议边界 fault：

```text
drop
delay
reorder
message-level mutate/corrupt where supported
```

由 Service Fabric 执行。

ca-benchmarks owns authored FaultProfile；ca-benchmark-engine owns intervention orchestration / executor binding；Service Fabric owns executable boundary lease、concrete boundary enforcement、Network Observation 与 BoundaryFaultReceipt；`env-5gc-sim` owns endpoint/domain effects after a delivered message。对于 Fabric-local intervention，Sandbox/Lab 不作为事件后的 relay。

Simulator 可以保留 deterministic endpoint failure fixture，例如 NF reject、资源不足或 policy failure，但不得把它伪装成“network response dropped”。

## Commit semantics

对于请求/响应协议：

```text
request delivered
-> destination endpoint may commit domain transition
-> response generated
-> response delivery is a separate network event
```

因此：

```text
response dropped
!= committed destination state rolled back
```

这使 response-loss case 可以自然产生 Runtime `OUTCOME_UNKNOWN`，再通过 domain fact + Network Evidence reconcile。

## Fidelity consequence

首版允许只使用 semantic protocol envelope：

```text
interface
protocol
message kind
direction
transaction/correlation material
fault-match semantic fields
```

不要求立刻构造完整 PFCP/NAS/SBI/GTP 二进制报文。

后续需要 parser/IE-level fault 时，可增加 encoded-protocol fidelity，但 Network Observation authority 不变。

## Ordering consequence

`env-5gc-sim` 和 Service Fabric simulated lane 必须绑定同一 Environment-scoped deterministic ordering/scheduler domain，避免多个组件各自用 wall clock 推导 delay/reorder/causality。

具体 scheduler machine contract 后续冻结。

## Rejected alternatives

### A. env-5gc-sim directly publishes Network Observation

拒绝。会建立 simulation-only network authority，与 real Service Fabric 分叉。

### B. protocol faults directly alter simulator mutation result

拒绝。无法真实表达“destination 已 commit、response 被网络丢失”这种跨边界 UNKNOWN。

### C. Service Fabric only exists for real packets

拒绝。Network Observation 是协议边界语义，不应由底层 acquisition 是否是 socket/packet 决定 owner。

## Invariants

```text
env-5gc-sim owns domain/NF behavior, not Network Observation.
ca-service-fabric owns Network Observation in simulation and real_nf.
Protocol-boundary faults are enforced by Service Fabric.
5GC domain facts remain fact-owner direct to Runtime.
Response delivery is separate from destination domain commit.
Simulation/real_nf share one semantic network-event vocabulary where fidelity permits.
```
