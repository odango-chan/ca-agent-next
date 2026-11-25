> 迁移来源：env-5gc-sim/docs/design/state-machine.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 原始状态：5GC Domain 状态与模拟 NF 状态机设计  
> 迁移追踪：ca-agent-next Issue #12。env-5gc-sim 同时包含 5GC reference simulator 与 Mock AMF test peer；两者在 Next 设计中分开描述。

---

# 5GC Simulator State-Machine Design

Status: Accepted  
Version: v0.7  
Date: 2026-09-20  
Scope status: N4/PFCP first-slice state-machine baseline Accepted; broader registration/N11/N2/N3/QoS state machines remain Proposed

## 1. 目的

本文定义 `env-5gc-sim` 首版状态机建模规则。

它不是 Open5GS FSM 的逐状态复制，也不是 3GPP 全流程模拟器；目标是保留 ConnectionAgent Skill、Harness、故障恢复与 Benchmark 所需要的关键 domain/intermediate state，使同一可靠性问题可在 reference simulation 与 unmodified Open5GS 上语义对照。

跨组件 protocol exchange / Network Observation 见 `network-observation-and-service-fabric.md`；S2 first-slice Store/commit/endpoint 的具体施工拓扑见 `owner-local-core.md`；跨仓 E2E 见 `odango-chan/connectionagent/docs/simulation-end-to-end.md`。

## 1.1 Accepted scope

当前 `Accepted` baseline 覆盖首片真正会实现和验收的状态机语义：

```text
world generation/revision fence
atomic commit and explicit partial-commit boundaries
minimal SM session lifecycle for create/release/recovery
minimal PFCP resource lifecycle
delivered request -> endpoint transition -> explicit commit
response candidate generation after domain commit
response loss does not roll back committed domain state
WAIT_EXPIRED / caller UNKNOWN does not create simulator UNKNOWN truth
exact PFCP cleanup + idempotent already-absent behavior
old-generation asynchronous work fails closed
```

registration dynamic flow、完整 N11/N2/N3、broader QoS/connectivity 等章节继续作为后续建模方向；只有进入对应 implementation scope 后才升级为该 scope 的 normative machine behavior。

## 2. 总体原则

Simulator state machine 只拥有：

```text
domain truth
endpoint procedure progress
endpoint-local commit state
```

不拥有：

```text
network delivery truth      -> Service Fabric
caller knowledge            -> caller/Runtime
Runtime Outcome             -> ca-runtime
Benchmark Verdict           -> ca-benchmark-engine
```

因此普通 endpoint transition：

```text
input command or delivered protocol message
        ↓
validate identity + pre-state
        ↓
advance endpoint procedure phase
        ↓
apply deterministic domain transition at explicit commit point
        ↓
update one authoritative source fact
        ↓
optionally generate next protocol-message candidate / backend result
```

必须保持：

```text
response lost
!= domain transition rolled back

Runtime OUTCOME_UNKNOWN
!= simulator domain truth unknown
```

### 2.1 Commit point 与 C2 worldRevision

每个明确的 simulator domain commit 都必须与 C2 revision 语义一致：

```text
one committed domain-state mutation batch
  -> advance worldRevision exactly once

read-only query
  -> no revision change

Fabric observes/forwards/drops a message
  -> no simulator revision change by itself

Fabric delivers a message
  -> destination endpoint may perform zero or more validated transitions
  -> each committed mutation batch advances revision deterministically
```

同一 protocol transaction 可以跨越多个 `worldRevision`；revision 不是 transaction sequence，也不是 Fabric sequence。

若一次 endpoint handler 原子地同时更新多个属于同一 commit point 的 domain fields，它们应共享同一个新 revision，避免消费者看到人为拆碎的中间状态。若真实可靠性场景需要暴露 partial commit，则必须显式拆成多个 commit point/revision，而不是在 read side 猜测。

## 3. Registration state machine

### 3.1 长期 RM state

```text
DEREGISTERED
REGISTERED
```

### 3.2 Procedure phase

首版：

```text
IDLE
IDENTITY
AUTHENTICATION
SECURITY_MODE
INITIAL_CONTEXT_SETUP
DEREGISTRATION
REMOVING
EXCEPTION
```

参考 Open5GS GMM 语义，但 handler 名不是 public ABI。

### 3.3 典型流程

```text
DEREGISTERED / IDLE
  -> IDENTITY
  -> AUTHENTICATION
  -> SECURITY_MODE
  -> INITIAL_CONTEXT_SETUP
  -> REGISTERED / IDLE-or-CONNECTED
```

失败时：

```text
procedure phase -> EXCEPTION
RM state remains last committed value
```

Authentication failure 不能先写 REGISTERED 再靠补偿撤回。

### 3.4 CM state

独立维度：

```text
IDLE
CONNECTED
```

可能组合：

```text
REGISTERED + CONNECTED
REGISTERED + IDLE
DEREGISTERED + CONNECTED  # transient where explicitly allowed
DEREGISTERED + IDLE
```

具体合法 transient 由 invariant 控制。

### 3.5 Security context

建议：

```text
ABSENT
PRESENT
VALID
INVALID
```

首版只模拟流程判定需要的语义，不模拟真实密钥推导。

注册业务完成至少由：

```text
RM == REGISTERED
+ required context consistency
```

派生，而不是看 `procedure phase == IDLE`。

## 4. PDU Session / SM state machine

PDU Session 不用一个 `ACTIVE` enum 覆盖所有事实。

### 4.1 SM lifecycle

首版建议：

```text
ABSENT
CREATING
ESTABLISHED
MODIFYING
RELEASING
FAILED_OR_RECOVERY
```

Open5GS 实际存在 wait_pfcp_establishment / operational / wait_pfcp_deletion 等阶段，因此保留中间状态是必要的。

### 4.2 UP connection state

```text
ACTIVATED
DEACTIVATED
UNKNOWN
```

它与 SM lifecycle 独立。

这里的 `UNKNOWN` 只有在它确实是 5GC domain semantic value 时才允许；“查询不到/调用方不知道”属于 acquisition/caller knowledge，不写入 source state。

### 4.3 PFCP resource state

首版 domain state：

```text
ABSENT
ESTABLISHING
ESTABLISHED
MODIFYING
DELETING
```

**不包含：**

```text
UNKNOWN_TO_CALLER
COMMITTED / NOT_COMMITTED caller-knowledge state
```

Simulator 对自己的 world state 是确定的；caller 是否知道该状态是 Runtime/Provider knowledge，不属于 PFCP resource enum。

必要时 endpoint operation 可以记录自己的明确 transition/commit fact，例如某 transaction 已应用，但这仍是 source fact，不是 Runtime Outcome。

## 5. Session establishment — protocol-aware flow

首版 N4/PFCP 路径：

```text
SM ABSENT
  -> Runtime/provider requests create
  -> SM CREATING
  -> allocate semantic session identity/config
  -> SMF-sim builds PFCP Establishment Request candidate
  -> Service Fabric SIMULATED lane
       observe / fault-match / deliver
  -> UPF-sim receives request only if delivered
  -> PFCP ESTABLISHING
  -> validate request
  -> COMMIT POINT: PFCP resource becomes ESTABLISHED
  -> UPF-sim builds PFCP Response candidate
  -> Service Fabric SIMULATED lane
       observe / fault-match / deliver
  -> SMF-sim receives response only if delivered
  -> establish required N3/UP summary where modeled
  -> SM ESTABLISHED
```

这里有两个独立事实：

```text
UPF-side PFCP resource committed
SMF-side success response received
```

不能合成一个 bool。

### 5.1 S2 reference commit topology

S2 reference implementation 把 first-slice create 的可见 domain commit 固定为：

```text
CP-CREATE-1: session -> CREATING
CP-CREATE-2: PFCP resource -> ESTABLISHED
CP-CREATE-3: session -> ESTABLISHED after terminal success response
```

每个 commit point 各推进一次 `worldRevision`。这是首片 owner-local implementation baseline，不把“固定加 3”升级成长期 wire contract；具体 Store/atomic commit/endpoint component test 规则以 `owner-local-core.md` 为准。

这使“PFCP 已提交但 SMF 尚未得到终态 response”的状态可以直接由 domain fact表达，而不用 private outcome shortcut。

### 5.2 Response loss

正确语义：

```text
Request delivered to UPF-sim
UPF-sim commits PFCP resource
UPF-sim generates success response
Service Fabric drops response
SMF-sim does not receive it
```

因此可以同时成立：

```text
env-5gc-sim domain fact:
  PFCP resource = ESTABLISHED

Service Fabric Network Observation:
  PFCP response = DROPPED

Runtime knowledge:
  OUTCOME_UNKNOWN until reconciled
```

Simulator 不通过 `public response suppressed` shortcut 直接制造这个场景。

## 6. Session modification

概念流程：

```text
SM ESTABLISHED
  -> MODIFYING
  -> build required protocol message candidate(s)
  -> Service Fabric mediation where protocol boundary is modeled
  -> destination endpoint applies transition at explicit commit point
  -> response mediation
  -> source endpoint advances state when response delivered
  -> ESTABLISHED
```

修改失败保留最后 committed source facts；如果真实 case 要模拟 partial effect，必须落到明确 domain object/commit point，不用 generic `FAILED` 覆盖真实状态。

## 7. Session release

典型 N4-aware release：

```text
SM ESTABLISHED
  -> RELEASING
  -> SMF-sim emits PFCP Deletion Request
  -> Fabric mediation
  -> UPF-sim receives request
  -> PFCP DELETING
  -> COMMIT POINT: PFCP resource becomes ABSENT
  -> response candidate
  -> Fabric mediation
  -> SMF-sim receives response
  -> remove/deactivate dependent SM/N3 state
  -> SM ABSENT
```

故障时可能短暂出现：

```text
PFCP resource absent
but SMF-side SM context still present/recovery
```

这正是多维状态模型的价值。

## 8. QoS transitions

QoS 按 Flow：

```text
Session -> QoSFlow[qfi]
```

首版支持：

```text
create default flow
modify 5QI / supported profile
remove flow where required
```

Session-level `qosSatisfied` 只能是 derived view，不是第二份 mutable truth。

涉及 N4/N2 等协议变化时，同样通过 Service Fabric mediated exchange 推进，而不是直接把网络消息效果折叠成一个 operation result。

## 9. Connectivity state

Connectivity 表示模拟用户面能否满足定义的 probe/traffic expectation。

Source state 最少：

```text
REACHABLE
UNREACHABLE
```

查询/acquisition 可另外得到：

```text
UNKNOWN / NOT_OBSERVABLE
```

但 query unknown 不写进 simulator business state。

Connectivity 可由明确 simulator facts/traffic behavior决定，例如：

```text
required PFCP/N3 resources
UP connection state
traffic gate / endpoint state
```

不能简单：

```text
SM ESTABLISHED -> REACHABLE
```

Active probe 若产生网络 traffic，Network Observation 由 Service Fabric 提供。

## 10. Fault 边界

### 10.1 Protocol/network fault

不属于 simulator state-machine fault seam。

```text
drop
delay
reorder
message-level mutate/corrupt
```

由 Service Fabric 执行；ca-benchmarks owns authored FaultProfile，ca-benchmark-engine owns intervention orchestration/binding，Service Fabric owns executable boundary lease 与 concrete enforcement。

### 10.2 Endpoint/reference-behavior fixture

Simulator 可以提供 deterministic endpoint fixture：

```text
reject request before commit
subscription/policy not eligible
resource unavailable
unsupported operation
internal endpoint error
```

它们明确改变 endpoint behavior/domain transition，而不是冒充 network drop。

### 10.3 禁止的长期 shortcut

不建立：

```text
COMMIT_AND_SUPPRESS_RESPONSE
UnknownDisposition
StateMutation controlling network outcome
generic Outcome field deciding commit + response + caller knowledge
```

这些只能作为 legacy migration inventory。

## 11. Reconcile 支持

Simulator 提供可信 source facts：

```text
PFCP resource exists?
SM session exists/current state?
QoS flow current value?
user-plane reachable?
```

Service Fabric 提供 Network Evidence：

```text
request forwarded?
response dropped/forwarded?
```

Runtime owns reconcile policy：

```text
continue
compensate
controlled retry
safe stop
```

普通 Runtime 不读取 evaluator-only Source Facts。

## 12. Derived business views

Simulator 可以提供 stable read model，但不拥有 Runtime Predicate verdict。

```text
RegistrationView.registered
  <- RM state

PduSessionView.established
  <- SM lifecycle + required resource criteria

ConnectivityView.reachable
  <- user-plane/reference traffic facts
```

Derived view 不是第二份 mutable source state。

## 13. Deterministic ordering / time

相同：

```text
initial world seed
Runtime/business operation sequence
simulated endpoint behavior fixtures
Service Fabric delivery/fault schedule
shared deterministic scheduler/time inputs
```

必须得到相同：

```text
env-5gc-sim domain transition sequence
Service Fabric Network-event ordering/dispositions
public backend results
evaluator-only Source Fact inputs
```

`env-5gc-sim` 与 Service Fabric simulated lane 必须共享 Environment-scoped deterministic ordering/scheduler domain。

本地 wall clock 不能决定 authoritative business/network outcome。

## 14. State machine 与 Network Observation 的边界

```text
env-5gc-sim state machine
  -> owns what each endpoint does when it receives an input
  -> owns endpoint commit point / domain state

env-fabric
  -> owns whether/when a protocol message reaches that endpoint
  -> owns Network Observation and boundary fault evidence
```

这个分工同时适用于 simulation/real_nf 的 semantic parity：真实 Open5GS 也可能在 response 被 Fabric drop 前已经 commit 内部资源。

## 15. 不变量

```text
Simulator source state contains domain truth, not caller knowledge.
Registration RM, procedure phase, CM and security remain separate.
SM lifecycle, PFCP resource, UP connection and connectivity remain separate.
One mutable fact has one authoritative storage location.
Protocol delivery/fault state belongs to Service Fabric, not simulator state enums.
Endpoint commit point is independent from response delivery.
Reconcile policy remains in Runtime; simulator supplies facts/operations only.
Derived business views are not secondary mutable state.
Determinism spans simulator + Fabric through a shared ordering/scheduler domain.
```
