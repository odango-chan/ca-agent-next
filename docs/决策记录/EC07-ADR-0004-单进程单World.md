> 迁移来源：env-5gc-sim/docs/decisions/ADR-0004-one-process-one-world.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：源仓架构决策记录；仅适用于 env-5gc-sim 所有权边界。  
> 迁移追踪：ca-agent-next Issue #12。以下保留原始决策和状态。

---

# ADR-0004 — One Process One World

Status: Accepted  
Version: v0.1  
Date: 2026-09-18

## Context

`env-5gc-sim` 的首个 N4/PFCP reference-simulation slice 需要把 owner-local WorldStore、C2/C6 API、Sandbox Environment、CA Lab process lifecycle 和 Service Fabric endpoint registration 连接起来。

一个进程承载多个 world 虽然可能提高资源密度，但会立即引入：

- world router；
- per-world endpoint registration namespace；
- reset/cleanup 与并发 world lifecycle；
- process readiness 与单 world readiness 分离；
- 更复杂的 generation fence；
- 更难验证的 Lab Instance / Environment ownership。

首片目标优先保证 correctness、隔离和可验收性，而不是进程密度。

## Decision

首个 process profile 采用：

```text
one env-5gc-sim process
  = one live materialized world
  = one WorldStore
  = one worldRef
  = one current worldGeneration
  = one scheduler binding
  = one simulated SMF/UPF endpoint set
```

同一 Environment 的 reset 可以复用同一进程：

```text
same worldRef
new worldGeneration
worldRevision -> 0
seed reapplied
external bindings revalidated/reregistered
```

Environment create/reuse/delete 仍由 Sandbox/Lab owner 管理，`env-5gc-sim` 不成为 Environment manager。

## Consequences

正面：

- Lab Instance 与 simulator process 一一对应；
- Environment/world ownership 清晰；
- reset/generation fence 简单且可机械验证；
- endpoint registration 不需要 multi-world routing；
- 一个 process crash 不影响其他 Environment；
- readiness 可以直接表达“当前 world + required bindings 是否可用”。

代价：

- 多 Environment 需要多个 simulator process；
- 高密度 benchmark 可能需要更多 OS process；
- 未来若需要 multi-world，需要新增 process profile/版本化设计。

## Reset consequence

同一 process reset：

```text
worldRef stays stable
worldGeneration changes
worldRevision resets
old-generation callback/read/operation must fail closed
```

不能通过复用同一 generation 来“清空状态”。

## Rejected alternatives

### A. 一个全局 simulator process 管所有 world

拒绝作为首片默认。会把 world registry、multi-tenant reset、endpoint routing 和 process readiness 同时引入，扩大故障域。

### B. 每次 reset 都强制重启 process

拒绝作为唯一机制。Environment reset 需要能验证 generation fence 与旧 callback 失效，不应把所有正确性都寄托在 OS process teardown。

### C. worldRef 每次 reset 都变化

拒绝作为同一 Environment reset 的默认语义。worldRef 表示逻辑 materialized world identity，worldGeneration 才是 reset/recreate fence。

## Invariants

```text
one process serves one current live world in the first profile.
one WorldStore is the sole worldRevision authority.
same-world reset changes generation, not worldRef.
old-generation work never mutates the new generation.
multi-world is a future explicit process profile, not an accidental extension.
process identity is not 5GC domain identity.
```
