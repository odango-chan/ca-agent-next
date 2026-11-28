> 迁移来源：ca-runtime/docs/design/pre-dispatch-binding-barrier.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# Pre-dispatch Binding Barrier

Status: Accepted  
Version: v1.0  
Date: 2026-09-17

## 1. 目的

部署 binding / discovery drift必须在真实副作用 dispatch barrier之前被发现。否则 Runtime会先记录“已开始 dispatch”，再发现实际 Provider binding 已漂移，把本应 `invocation=0` 的前置拒绝错误地升级成 post-dispatch uncertainty。

目标顺序：

```text
Executable Action
  -> Authorization
  -> Assurance
  -> Runtime builds invocation identity
  -> DispatchPreparer / binding resolver
  -> exact ProviderBinding frozen
  -> authoritative action.dispatched fact
  -> Provider.Invoke
```

## 2. Runtime-owned identity

Runtime拥有并冻结调用身份，例如：

```text
invocationId
inputDigest
idempotency material
run/request correlation
```

Deployment binding component只能返回/确认允许它 owning 的 binding material，例如：

```text
tool/operation ref
bindingDigest
discoveryDigest where applicable
provider identity
```

它不能改写 Runtime-owned identity。

## 3. DispatchPreparer 不是 Provider

Pre-dispatch component只做：

```text
binding existence check
frozen/live digest conformance
discovery generation/digest check
capability -> provider exact mapping
binding identity freeze
```

它不得：

```text
执行 Provider operation
调用 Service Fabric/NF side effect
使用 side-effect credential做业务调用
根据 live discovery扩大 callable authority
在 binding mismatch后“选一个差不多”的 operation
```

失败必须发生在 authoritative dispatch fact之前，Provider invocation count保持 0。

## 4. Authoritative dispatch fact

只有 pre-dispatch gate全部通过后，Runtime才写入 authoritative dispatch fact并进入 Provider。

当前 canonical event vocabulary以 `RunEvent.v1` 为准；历史 `tool.dispatch.started` 等兼容命名不得重新成为产品 authority。

关键语义是：

```text
dispatch fact durable/authoritative
  -> Runtime can no longer assume side effect did not happen
```

## 5. Post-dispatch uncertainty

mutation越过 barrier后，如果 Provider只返回 transport error/无可信结果：

```text
ExecutionDisposition = DISPATCHED
commit knowledge = uncertain
  -> Runtime OUTCOME_UNKNOWN when contract applies
  -> Reconcile
  -> retry fence
```

Runtime不能直接把 Go/HTTP/MCP error当作“没有提交，可以再试一次”。

Read-only失败可以使用独立 bounded policy，但不影响 mutation safety。

## 6. Procedure 共用同一 barrier

所有 Runtime副作用都必须走同一 safety kernel：

```text
Agent-selected admitted capability
        ┐
        ├-> Runtime Action Kernel -> Binding Barrier -> Provider
        │
frozen Procedure Action
        ┘
```

ExecutableProcedure不能有绕过 binding barrier 的私有 dispatch实现。

## 7. Deployment

Production manifest选择 component/provider identity，不嵌入模型可见的 raw endpoint/credential。具体 Provider transport由进程/环境装配。

Provider MCP、Service Fabric、native NF 等 concrete adapter都必须服从同一 barrier。

## 8. 与 tool-mcp-gw 无关

`tool-mcp-gw` 只把 Agent MCP Tool Call映射到 RuntimeHost Execute。它不解析/提交 ProviderBinding，也不参与 pre-dispatch binding选择。

```text
tool-mcp-gw
  -> RuntimeHost request
  -> Runtime resolves admitted capability/procedure
  -> Runtime binding barrier
```

## 9. 不变量

```text
Binding drift is rejected before authoritative dispatch.
External caller never supplies ProviderBinding authority.
All side effects cross the same binding barrier.
Post-dispatch mutation uncertainty is not a normal retryable error.
Provider transport family does not weaken the barrier.
```