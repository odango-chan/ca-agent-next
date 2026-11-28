> 迁移来源：ca-dsh/docs/architecture/ca-dsh-architecture.md  
> 固定源提交：3a44ff1ccde4d81993b67fa333574fd68a481870  
> 源文档定位：G01 DeepSeek Harness 架构原文  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# ca-dsh 架构与 Ownership

Status: Accepted  
Version: v1.1  
Date: 2026-09-21

## 1. 定位

`ca-dsh` 是 ConnectionAgent 的 **DeepSeek Harness Host Adapter**。

```text
ConnectionAgent
  resolves Agent/System/Profile/Environment
        ↓
DSH
  owns Agent Loop / LLM / Session / Host-native model context
        ↓
ca-dsh
  owns DSH-specific Host integration
        ↓
tool-mcp-gw
  owns Agent-facing MCP protocol surface
        ↓
ca-runtime
  owns governed execution / Tool eligibility / reliability authority
```

## 2. ca-dsh 拥有

- DSH plugin / Context integration；
- DSH-native Agent/Session/Tool glue；
- standard MCP client integration；
- Host-local least-privilege narrowing；
- stable Host correlation / mutation identity preservation；
- Host transport uncertainty handling；
- DSH trajectory / ModelInput / ModelOutput extraction；
- ConnectionAgent dedicated DSH profiles；
- DSH Runtime Pack build/verification；
- DSH-specific conformance tests。

## 3. ca-dsh 不拥有

```text
Runtime / Procedure execution
MCP Server authority
Runtime Resolved CA Toolset policy
Skill eligibility authority
Provider/NF authorization
Assurance / Reconcile
trusted GroundTruth
Benchmark verdict
Platform/System lifecycle authority
final product Distribution assembly
```

## 4. Target topology

```text
DSH AgentInstance
  ├─ Agent Loop
  ├─ LLM
  ├─ Session
  ├─ model context
  └─ ca-dsh Host integration
          ↓ standard MCP client
        tool-mcp-gw
          ↓ RuntimeHost.v1
       ca-runtime
          ↓
 Provider / Sandbox / Service Fabric / NF
```

Deployment invariant：

```text
DSH -> side-effecting Provider/NF   DENY
DSH -> tool-mcp-gw                       ALLOW
tool-mcp-gw -> ca-runtime                ALLOW
tool-mcp-gw -> NF                        DENY
ca-runtime -> Provider/NF           ALLOW
```

## 5. Current compatibility

当前仍保留：

```text
DSH
  -> ca-dsh direct ca_* Tool wrapper
  -> RuntimeHost.v1
  -> ca-runtime
```

它是 migration compatibility，不是 target architecture。删除规则见 `migration/implementation-plan.md`。

## 6. Tool authority

```text
Runtime Capability Catalog
  != AgentInstance Base CA Capability Envelope
  != tool-mcp-gw Server Tool Catalog
  != Goal-scoped Runtime Resolved Execution Toolset
  != Host model-visible Tools
```

Host 最终模型可见工具：

```text
Goal-scoped Runtime Resolved Execution Toolset
  ∩ tool-mcp-gw Server Tool Catalog
  ∩ Host-supported subset
  ∩ optional Host-local least-privilege narrowing
```

ca-dsh 只能机械收缩，不能通过 Goal 文本、Tool 名称、模型请求或本地策略扩大 owner toolset。

## 7. AgentInstance 与 Goal 生命周期

AgentInstance/client generation：

```text
resolved binding
 -> Base CA Capability Envelope
 -> acquire/reuse AgentInstance
 -> MCP initialize
 -> tools/list
 -> cached Server Tool Catalog
 -> READY
```

Goal：

```text
Goal
 -> SkillEligibilityDecision
 -> Skill routing
 -> exact RuntimeSkillIdentity
 -> model context
 -> Goal-scoped Runtime Resolved Execution Toolset
 -> Host mechanical intersection
 -> model execution
```

Goal arrival 不是 `tools/list` 必然触发器，也不是 Tool permission grant。

## 8. Reliability split

```text
Host RESULT_UNKNOWN
  = Host/MCP transport or reply ambiguity

Runtime OUTCOME_UNKNOWN
  = governed side-effect outcome ambiguity
```

二者禁止合并。Mutation stable requestId 必须跨 reconnect/recovery 保持，JSON-RPC id、callId、MCP session id 只做 correlation。

## 9. Distribution split

`ca-dsh` 产出 `ca-dsh.runtime-pack/v1`；`ca-console` 负责最终 Distribution assembly。Artifact ownership 不改变 Runtime/System authority。
