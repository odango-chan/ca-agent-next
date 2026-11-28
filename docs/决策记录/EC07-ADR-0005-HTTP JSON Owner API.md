> 迁移来源：env-5gc-sim/docs/decisions/ADR-0005-http-json-owner-api.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：源仓架构决策记录；仅适用于 env-5gc-sim 所有权边界。  
> 迁移追踪：ca-agent-next Issue #12。以下保留原始决策和状态。

---

# ADR-0005 — C2/C6 Owner API 使用 HTTP/JSON，不恢复 Agent-facing MCP

Status: Accepted  
Version: v0.1  
Date: 2026-09-18

## Context

`env-5gc-sim` 需要为 Runtime、Lab 和受控 host integration 提供跨进程 owner surface。

当前已有：

- C2/C6 canonical JSON Schema；
- `ca-mcp` 作为唯一 Agent-facing MCP；
- Runtime transport-neutral ProviderContract / ProviderBinding；
- Sandbox 正在收缩 legacy Provider MCP；
- Service Fabric 拥有自己的 simulated acquisition/delivery contract。

如果 simulator 再直接暴露 Agent-facing MCP，会重复 Tool discovery/authorization，模糊 Runtime authority。

## Decision

首片 owner API 采用：

```text
HTTP transport
JSON payload
canonical C2/C6 schemas as body authority
```

Provider business listener route family：

```text
GET  /v1/world
POST /v1/facts/read
POST /v1/operations
```

Process lifecycle and trusted reset live on a separate Control listener under
`/management/v1/*` and `/internal/v1/world/reset`. Each listener serves its own
OpenAPI 3.1 at `/openapi.yaml` and docs at `/docs/`. Root identity/health aliases
and the PFCP delivery callback are removed; N4 uses PFCP/UDP.

`env-5gc-sim` 不提供 Agent-facing MCP，也不恢复 legacy Sandbox Provider MCP。

Runtime 通过自己的 admitted Provider/read adapter 调用该 owner API。

## Why HTTP/JSON

- C2/C6 已有 canonical JSON machine contract；
- 便于 process identity/readiness 与 Lab materialization；
- 便于保留 typed request/response evidence；
- 不要求 Runtime core绑定某一 RPC family；
- 不会把 Provider transport误当 Agent Tool surface。

HTTP/1.1 或 HTTP/2 只是 transport choice，不改变 semantic contract。

## Agent-facing consequence

目标链：

```text
Agent
-> ca-mcp
-> RuntimeHost / Runtime
-> admitted Capability / ProviderBinding
-> env-5gc-sim HTTP owner API
```

因此：

```text
env-5gc-sim HTTP endpoint discovery
!= Agent Tool discovery

env-5gc-sim operation schema
!= request/header.tools
```

## Runtime consequence

Runtime 保留：

- ProviderBinding；
- authoritative dispatch；
- ProviderKnowledge mapping；
- Outcome / OUTCOME_UNKNOWN；
- Reconcile；
- Tool eligibility。

`env-5gc-sim` 只返回 C2/C6 owner knowledge，不生成 Runtime Outcome。

## Host-control consequence

`/internal/v1/world/reset` 是 host-only control surface。

它不是 Runtime business Capability，也不得进入 Agent Toolset。

## Transport failure consequence

HTTP 连接问题不能改变 backend truth：

```text
client disconnect
response write failure
transport timeout
!= backend NOT_COMMITTED
!= retry authorization
```

一旦越过 authoritative backend dispatch barrier，backend lifecycle 与 HTTP request cancellation 解耦。

## Rejected alternatives

### A. env-5gc-sim 直接提供 Agent-facing MCP

拒绝。会形成第二 Agent-facing Tool authority，绕过 ca-mcp/Runtime eligibility。

### B. 恢复 Sandbox Provider MCP 并让 simulator复用

拒绝。legacy Sandbox MCP 正在退休，且会重新把 simulator耦合回 Sandbox transport。

### C. 只提供 in-process Go interface

拒绝作为唯一 surface。S3～S5 需要跨仓进程 materialization、identity、readiness 和真实 transport evidence。

### D. 现在就冻结 gRPC/protobuf

拒绝。当前 canonical contract 是 JSON Schema，首片没有足够收益引入第二 machine-shape authority。

## Future

未来 Runtime Provider adapter 若选择 MCP/gRPC 等内部 transport，必须单独版本化，并保持：

```text
Provider transport != Agent-facing MCP
transport schema != Runtime authorization
C2/C6 semantic authority remains explicit
```

## Invariants

```text
ca-mcp remains the single Agent-facing MCP.
env-5gc-sim exposes owner API, not Agent Tool API.
HTTP status and C2/C6 semantic result stay separate.
host reset is not a Runtime business capability.
transport ambiguity never authorizes blind retry.
canonical machine schemas, not handwritten HTTP structs, define payload shape.
```
