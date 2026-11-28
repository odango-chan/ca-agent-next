> 迁移来源：env-5gc-sim/docs/decisions/ADR-0002-fact-owner-direct-observation.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：源仓架构决策记录；仅适用于 env-5gc-sim 所有权边界。  
> 迁移追踪：ca-agent-next Issue #12。以下保留原始决策和状态。

---

# ADR-0002 — 5GC Fact Owner Direct Observation

Status: Accepted  
Version: v0.2  
Date: 2026-09-18

## Context

`ca-sandbox` 的 legacy simulator 时代，5GC domain state、Observation HTTP surface、GroundTruth 与 Environment lifecycle 都位于同一仓，因此形成了：

```text
5GC simulator state
  -> Sandbox Observation API
  -> Runtime ObservationSource
```

随着 5GC reference world 抽离到 `env-5gc-sim`，继续保留这条路径会让 Sandbox 成为纯中转层，并制造不必要的事实 ownership 模糊。

同时真实 5GC 目标是改造后的 Open5GS；真实 UE/Session/QoS/connectivity 状态也不会天然属于 Sandbox。

## Decision

5GC domain Observation 改为 **fact-owner direct**。

Simulation：

```text
env-5gc-sim
  = simulated 5GC fact owner
```

Real NF：

```text
ca-provider-5gc -> modified Open5GS
  = real 5GC fact-source adapter / owner path
```

Runtime 两类消费者直接绑定对应 fact source：

```text
Runtime read-only Capability
  -> fact owner
  -> ToolResult
  -> Agent planning

Runtime ObservationSource
  -> fact owner
  -> NormalizedObservation / Evidence
  -> Predicate
```

允许两条路径共用底层 read implementation 或同一次 acquisition，只要 Runtime 能验证 binding、source identity、provenance、revision/freshness 与 reuse policy。

## Tool 与 Observation authority

Tool 不是事实 authority。

```text
Runtime read-only Capability / Tool
  = Agent-facing governed semantic entry

fact owner
  = business truth authority

Runtime ObservationSource
  = trusted acquisition / normalization governance

Predicate
  = assurance verdict authority
```

因此：

```text
ToolResult != Predicate verdict
Tool call != proof that postcondition passed
```

## Sandbox consequence

Sandbox 不再拥有“所有 Environment Observation”。

Sandbox 继续拥有：

```text
Environment generation / lifecycle semantics
deterministic scheduler / clock
Sandbox-owned Environment / control Source Facts
```

其他相关 authority 不因 fact-owner direct 而转移：

```text
ca-benchmarks
  -> GroundTruth / FaultProfile authoring

ca-benchmark-engine
  -> Intervention orchestration / Oracle / Verdict

ca-service-fabric
  -> Network Observation / boundary enforcement / BoundaryFaultReceipt
```

Sandbox 不再作为以下事实的目标中转 owner：

```text
UE registration
PDU Session / SM state
PFCP/resource state
QoS
user-plane connectivity
```

当前 `:8789` Observation HTTP API 中属于 5GC domain 的 refs/handlers 作为 migration compatibility 保留到 Runtime consumer 完成切换，随后删除。

## Observation class consequence

`Environment Observation` 表示“当前环境/业务状态是什么”，不是 repository ownership 标签。

因此：

```text
Environment Observation
!= Sandbox-owned Observation
```

同类事实可以来自：

```text
env-5gc-sim
modified Open5GS through ca-provider-5gc
other admitted environment fact owners
```

而 Network Observation 仍由 `ca-service-fabric` 等 network fact owner 提供。

## GroundTruth consequence

GroundTruth 与 actual Source Fact 必须分离：

```text
GroundTruth
  = ca-benchmarks authored gold expected result

env-5gc-sim hidden/current world fact
  = Authoritative Source Fact
  = evaluator-only when access policy requires

Oracle / Verdict
  = ca-benchmark-engine
```

`env-5gc-sim` 可以提供 evaluator-only Source Fact seam，但不提供 private GroundTruth/Oracle。该 seam 不自动进入 Runtime ordinary ObservationSource，也不成为 Agent Tool。

## Migration consequence

目标迁移：

```text
1. freeze env-5gc-sim stable fact/read contract
2. Runtime read-only Capability binds directly to it
3. Runtime ObservationSource binds directly to it
4. Sandbox keeps only Sandbox-owned Environment/control Source Facts
5. remove Sandbox 5GC Observation relay
```

真实 Open5GS integration 采用同一原则：只替换 fact-source binding，不改变 Skill/Predicate/Agent-facing read-only Capability 的稳定语义。

## Rejected alternatives

### A. Sandbox remains universal Observation gateway

Rejected because it creates an unnecessary relay, obscures fact ownership and makes real Open5GS integration depend on a simulation-platform surface.

### B. Each Tool owns and publishes its own Observation

Rejected because Tool is a governed semantic entry, not the underlying fact authority, and would duplicate state/acquisition semantics across Tools.

### C. Agent connects directly to fact owners

Rejected because Agent-facing ConnectionAgent Tools remain unified through `ca-mcp -> RuntimeHost -> ca-runtime`; fact-owner direct applies on the Runtime/backend side, not the Agent Host side.

## Invariants

```text
5GC facts come from the actual 5GC fact owner.
Runtime may use the same fact source for Agent reads and Assurance.
ToolResult is planning input; Predicate verdict remains Runtime authority.
Sandbox is not a universal 5GC Observation relay.
Environment Observation is a semantic class, not a Sandbox ownership label.
Agent-facing MCP remains ca-mcp.
GroundTruth remains Benchmark-authored gold truth; evaluator-only Source Facts remain restricted.
```
