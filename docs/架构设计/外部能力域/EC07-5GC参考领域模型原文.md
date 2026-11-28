> 迁移来源：env-5gc-sim/docs/architecture/domain-model.md  
> 固定源提交：6ba1dc47049013e19d93222fb308ffead7eb4c0e  
> 源文档定位：EC07 5GC 参考领域模型原文  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# 5GC Reference Domain Model

Status: Accepted  
Version: v0.4  
Date: 2026-09-20  
Scope status: N4/PFCP first-slice baseline Accepted; broader 5GC expansion remains Proposed

## 1. 目的

本文定义 `env-5gc-sim` 的 5GC reference domain model 方向。

目标不是完整复制 Open5GS，也不是把当前 `ca-sandbox/simulator` 的 `registered bool` / `session ACTIVE` 直接搬过来，而是建立一个：

```text
足够贴近真实 5GC 生命周期
足够稳定，不绑定 Open5GS 内部 struct 布局
足够确定性，适合故障注入与 Benchmark
足够可观察，可以与 unmodified Open5GS 做语义对照
```

的模拟世界模型。

首个 N4/PFCP slice 的具体 C2/C6 字段与 wire shape 已由对应 design 和 canonical schema 冻结；本文负责冻结其对象边界、source-of-truth 分离和状态建模原则。broader registration/N11/N2/N3/QoS/connectivity 扩展仍需在进入对应 scope 时继续评审。

## 1.1 Accepted scope

本文件的 `Accepted` 不表示“完整 5GC 模型已经设计完毕”。当前 normative baseline 只覆盖首个 N4/PFCP vertical slice 需要的稳定语义：

```text
one world -> explicit generation/revision fence
one mutable domain fact -> one authoritative source
registered UE deterministic seed
SMF session state != PFCP resource state != connectivity
derived business view != second mutable truth
KNOWN_ABSENT != KNOWN_NEGATIVE != UNAVAILABLE
simulator deterministic domain truth != caller knowledge / Runtime Outcome
```

以下仍是后续 scope，不阻塞首片实现：

```text
dynamic registration procedure completeness
full AMF security / mobility behavior
full N11/N2/N3 protocol behavior
broader QoS/connectivity semantics
full real_nf/Open5GS parity qualification
```

进入这些 scope 时必须先更新对应 canonical design/schema；不得把本文的方向性描述直接当成未评审的新 wire contract。

## 2. 核心结论：不要用一个“全局业务状态”替代分布式 5GC context

5GC 的注册和会话事实分散在不同 NF / protocol context 中。

因此 `env-5gc-sim` 不采用：

```text
UE.Registered bool
PduSession.State = ACTIVE
```

作为唯一 source of truth。

目标模型是：

```text
Simulated5GCWorld
  ├─ AMF domain
  │    ├─ UE Context
  │    ├─ Registration/GMM state
  │    ├─ Access/CM state
  │    ├─ Security context
  │    └─ AMF PDU-session references/context
  │
  ├─ SMF domain
  │    ├─ SMF UE Context
  │    └─ SM Session Context
  │         ├─ PDU session identity
  │         ├─ DNN / S-NSSAI
  │         ├─ PDU address
  │         ├─ UP connection state
  │         ├─ QoS flows
  │         └─ N4/PFCP relationship
  │
  └─ User-plane domain
       ├─ PFCP session/resource state
       └─ traffic/reachability state
```

上层的“UE 已注册”“PDU Session 已建立”“用户面可达”都是从这些 source state 派生的业务视图，而不是第二份可变 truth。

## 3. World 根对象

概念上：

```text
Simulated5GCWorld
  - clock / deterministic scheduler ref
  - AMF contexts
  - SMF contexts
  - user-plane/PFCP contexts
  - optional subscriber/profile fixtures
```

World 是 simulator instance 内部的受控状态容器。

它不等于 Sandbox Environment：

```text
Sandbox Environment
  -> owns Environment generation + deterministic scheduler semantics
  -> binds one Simulated5GCWorld when using this backend

ca-lab
  -> materializes/process-hosts the required resources

Benchmark/Fault/Evaluation ownership remains outside the World:
  ca-benchmarks -> GroundTruth / FaultProfile
  ca-benchmark-engine -> Intervention / Oracle / Verdict
  env-fabric -> boundary fault / Network Observation
```

## 4. UE Identity

建议稳定 identity 至少区分：

```text
SUPI
SUCI when relevant
PEI when relevant
5G-GUTI / temporary identity when modeled
```

长期 subject identity 以稳定 ConnectionAgent subject ref / SUPI 关联，不用 Open5GS 内部 pool ID 作为跨仓 identity。

原则：

```text
Open5GS internal object id
!= env-5gc-sim public UE identity
```

## 5. AMF UE Context

`AmfUeContext` 表达 AMF 侧当前掌握的 UE context，而不是笼统的“UE 状态”。

建议至少拆成以下维度。

### 5.1 Registration / RM state

业务稳定维度：

```text
DEREGISTERED
REGISTERED
```

它对应 5GMM registration management 的长期状态，而 authentication、security mode、initial context setup 等属于 procedure phase，不应永久编码成互斥的业务终态。

### 5.2 Registration procedure phase

为模拟过程、故障和 UNKNOWN 场景，需要单独记录当前过程阶段，例如概念上：

```text
IDLE
IDENTITY_RESOLUTION
AUTHENTICATION
SECURITY_MODE
INITIAL_CONTEXT_SETUP
DEREGISTRATION
EXCEPTION / RECOVERY
```

具体枚举需在 state-machine design 中根据 Open5GS/5GMM 行为进一步核对。

保持：

```text
registration management state
!= current procedure phase
```

这比当前 simulator 的多个 boolean 更接近真实状态机，也避免组合出不可能状态。

### 5.3 CM / access state

注册状态不等于当前 RAN connection 状态。

应独立表达概念上的：

```text
CONNECTED
IDLE
```

以及当前 serving RAN context identity（如果该场景需要）。

因此：

```text
REGISTERED + IDLE
```

是合法状态，不能把“没有当前 NG connection”解释为“未注册”。

### 5.4 Security context

Security 不是一个 `SecurityEstablished bool` 就结束。

reference model 至少需要区分：

```text
context absent
context available/present
context valid/usable
selected algorithms / key-generation identity where test-relevant
```

具体 cryptographic material 默认不需要完整模拟；只有影响流程决策/验证的语义进入 stable domain model。

## 6. AMF Session Context

AMF 侧会持有与 PDU Session/SM Context 相关的 session context，例如：

```text
PDU Session Identity (PSI)
SM Context reference/presence
DNN
S-NSSAI
RAN binding/ref where relevant
release/setup progress facts
```

AMF session context 的存在：

```text
!= SMF session fully established
!= PFCP session established
!= user plane reachable
```

该区别是可靠性场景必须保留的。

## 7. SMF UE Context

`SmfUeContext` 负责把一个 SUPI 与其 SMF session contexts 关联。

不把 SMF 内部 hash/list/pool identity 公开成 domain contract。

概念关系：

```text
SmfUeContext
  1 -> N SmSessionContext
```

## 8. SM Session Context

`SmSessionContext` 是当前 ConnectionAgent 主要关注对象之一。

稳定业务维度建议包括：

```text
identity
  - SUPI
  - PDU Session ID / PSI

selection/configuration
  - DNN
  - S-NSSAI
  - PDU session type when relevant
  - SSC mode when relevant

addressing
  - allocated UE IPv4/IPv6 where modeled

control-plane lifecycle
  - SM context presence/lifecycle
  - current procedure phase

user-plane connection
  - UP connection state

N4/PFCP relationship
  - PFCP session/resource state

QoS
  - QoS flow collection
  - QFI / 5QI and only test-relevant QoS attributes
```

这些维度不应被压成一个单独 `ACTIVE/INACTIVE` 字段。

## 9. PFCP / User-plane Context

为支持 `OUTCOME_UNKNOWN`、PFCP response loss、reconcile 等 reliability case，必须允许：

```text
SM Context state
PFCP session/resource state
User-plane traffic reachability
```

出现暂时不一致。

因此建议至少概念区分：

```text
PfcpSessionContext
  - local/remote session identity where test-relevant
  - lifecycle/procedure phase
  - installed resource summary

UserPlaneState
  - bound PDU session ref
  - reachability / traffic validation state
```

关键不变量：

```text
PFCP establishment response observed
!= business PDU session necessarily established

PDU session context exists
!= user-plane traffic necessarily reachable
```

## 10. QoS Flow

QoS 不应该只是 `fiveQi *int` 挂在 Session 上。

目标模型至少支持：

```text
PDU Session
  -> 0..N QoS Flow

QoS Flow
  - QFI
  - 5QI
  - only additional attributes needed by supported cases
```

不要为了模拟完整 3GPP QoS 参数而过度建模；字段按 Skill/Benchmark/real parity 需求扩展。

## 11. Derived Business Views

Agent、Runtime read-only Capability、Runtime ObservationSource 或 evaluator 都不应直接依赖 simulator internal struct。

应从 source state 派生稳定业务视图，例如概念上：

```text
RegistrationView
  - subject exists / known
  - registration management state
  - current procedure phase if public
  - CM state
  - security context summary

PduSessionView
  - exists
  - SUPI / PSI
  - DNN / S-NSSAI
  - SM context summary
  - UP connection summary
  - PFCP/resource summary where allowed
  - QoS summary

ConnectivityView
  - current reachability
  - probe/source provenance where the owning fact/read contract exposes it
```

Derived view 是函数/投影结果，不是第二份独立可变状态。

## 12. 明确区分 ABSENT、NEGATIVE 与 UNKNOWN

这是现有 simulator 需要修正的重要语义。

必须区分：

```text
KNOWN ABSENT
  = subject/session 被明确观察为不存在

KNOWN NEGATIVE
  = subject存在，但业务状态明确为否
  = 例如已知 UE 当前 DEREGISTERED

UNKNOWN / NOT OBSERVABLE
  = 无法建立该事实
```

不能用一个 `NOT_FOUND` 同时表达“明确不存在”和“无法观察”。

Source-query resolution 的 machine 语义由 env-5gc-sim C2 fact/read contract 冻结；Runtime ObservationSource 可以再做受治理归一，但不能抹掉这种信息差异。

## 13. 单一 source of truth

禁止当前 simulator 里的这类双写继续扩散：

```text
registered map[string]bool
+
registrationState.Registered
```

目标规则：

```text
一个 domain fact 只有一个 authoritative mutable location
其他 bool/status/view 必须派生
```

同理：

```text
session exists
SM context exists
PFCP exists
connectivity
```

分别属于不同事实，不能互相复制成同步维护的冗余 flag。

## 14. State transition 原则

所有 mutation 通过显式 state transition 执行：

```text
command/input
  -> validate pre-state
  -> deterministic transition
  -> produce effect/result
  -> expose new source state
```

Endpoint fixture 可以确定性改变 endpoint transition/result；protocol-boundary fault 只能通过 Service Fabric 是否/何时 delivery 来影响 endpoint 输入。必须明确：

```text
response dropped by Fabric
!= state transition skipped

OUTCOME_UNKNOWN to caller
!= simulator domain truth unknown
```

simulator 内部必须始终知道受控世界真正发生了什么；Runtime 是否知道是另一层语义。

## 15. 与 Open5GS 的关系

当前核对表明 Open5GS 本身也把这些概念拆开：

```text
AMF UE context + GMM FSM
AMF PDU-session context
SMF UE context
SMF session context + FSM
PFCP session context
UP connection state
DNN / S-NSSAI / PAA
QoS flows
```

本仓会参考这些**语义分层**，但不会复制其完整结构或生命周期 bookkeeping。

具体 source baseline 与字段/语义映射见后续 `design/open5gs-alignment.md`。

## 16. 当前暂不建模

除非具体 Skill/Benchmark/real parity 需要，首版不追求完整模拟：

```text
完整 NRF/SCP lifecycle
完整 UDM/UDR subscriber database behavior
完整 PCF policy engine
完整 charging/CHF
完整 roaming V-SMF/H-SMF
所有 handover/mobility 分支
所有 NAS/PFCP timer
完整 crypto
```

但 domain model 必须留出后续扩展空间，不能用当前 happy path 的 bool 结构堵死。

## 17. 首版重点

建议首批闭合：

```text
UE identity
AMF registration/RM state
CM state
security-context summary
AMF session context
SMF session context
DNN / S-NSSAI / IP
PFCP session/resource summary
QoS flows
user-plane connectivity
```

直接覆盖 ConnectionAgent 当前注册、PDU session、QoS、connectivity 与 reliability use cases。

## 18. 不变量

```text
Registration state, procedure phase and CM state are separate dimensions.
AMF session, SMF session, PFCP session and user-plane reachability are separate facts.
Derived business views are not mutable source-of-truth copies.
Known absent, known negative and unknown are distinct.
One domain fact has one authoritative mutable location.
Simulator domain truth remains deterministic even when caller outcome is unknown.
Open5GS semantic layering is referenced; Open5GS internal struct layout is not copied as public contract.
```
