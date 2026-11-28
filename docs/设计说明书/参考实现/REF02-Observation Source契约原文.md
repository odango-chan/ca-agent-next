> 迁移来源：ca-runtime/docs/design/observation-source-contract.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# Runtime Observation Source Contract

Status: Accepted
Version: v1.5
Date: 2026-10-21

## 1. 定位

`ObservationSource` 是 deployment-owned 的可信事实获取 seam。它可以调用 Provider read path、5GC fact source、Service Fabric、Sandbox Environment/Fault source、Runtime state 或其他明确准入的数据源并归一化结果，但**不返回 Predicate verdict，也不拥有 Runtime freshness/UNKNOWN 语义**。

核心原则：

> **Runtime 直接绑定真正的 fact owner；不要求所有 Environment/业务 Observation 先经 Sandbox 中转。**

例如：

```text
5GC simulation facts
  -> env-5gc-sim

real 5GC facts
  -> ca-provider-5gc -> unmodified real 5GC external read seam

network/protocol facts
  -> env-fabric

environment/fault facts
  -> ca-sandbox
```

`Environment Observation` 是事实类别，不是 “Sandbox-owned Observation” 的同义词。

## 2. 两类消费者，共用事实基础设施

Runtime 中有两类消费者可以使用同一套 Observation acquisition 基础设施：

```text
Agent read-only Capability
  -> Runtime/Harness Tool eligibility + admission
  -> trusted fact acquisition
  -> Runtime governed ToolResult
  -> Agent

Runtime Assurance
  -> Predicate declares required Observation
  -> trusted fact acquisition
  -> NormalizedObservation + provenance
  -> Runtime validates provenance/freshness
  -> Predicate evaluator
  -> PASS / FAIL / UNKNOWN
```

两条链可以共用 `ObservationSource`、binding、normalization、provenance 与 freshness-aware cache，也可以共用同一次底层 source read；不需要建立第二套 Agent Observation backend。

但：

```text
ToolResult = planning input
Predicate result = assurance verdict authority
```

## 3. Agent 查询与 Assurance 的关系

Agent 不直接调用 raw `ObservationRef`、ObservationBinding、Sandbox trust surface 或 Service Fabric internal stream。

模型侧只看到 Runtime/Harness 允许暴露的业务语义 read-only Capability，例如“查询 UE 注册状态”“检查 PDU Session”“检查用户面连通性”。这些 Capability 必须同时满足：

```text
Runtime Capability admission
current resolved CA Tool eligibility
Skill/Artifact resource constraints where applicable
Environment / policy constraints
```

`SKILL.md` 默认职责不是逐个枚举 Tool，而是告诉模型：

```text
什么时候必须先获得当前事实
哪些状态不能靠其他事实推断
哪些业务边界不能绕过
```

Runtime 将 read-only Capability 绑定到可信事实 acquisition：

```text
Runtime Resolved CA Toolset
  -> Agent sees admitted read-only Tool
  -> Agent selects Tool
  -> tool-mcp-gw / RuntimeHost
  -> Runtime read-only Capability
  -> ObservationSource / Provider read path
  -> real fact owner
  -> trusted fact
```

Assurance 则由 Runtime 自己触发：

```text
Procedure / precondition / postcondition
  -> Predicate
  -> required Observation
  -> ObservationSource
  -> real fact owner
  -> Evidence
  -> PASS / FAIL / UNKNOWN
```

因此不是两套事实系统，而是**同一事实 owner 的两种受治理消费方式**。

## 4. Fact owner 与 Tool/Observation authority

必须区分：

```text
Fact owner
  = 谁拥有真实业务状态

Runtime read-only Capability
  = 给 Agent 的受治理业务语义入口

ObservationSource
  = Runtime 的可信事实 acquisition/normalization seam

Predicate
  = Runtime assurance verdict authority
```

所以：

```text
Tool does not own the fact.
ToolResult does not imply Predicate PASS.
ObservationSource does not own the underlying business truth.
```

以 5GC simulation 为例：

```text
env-5gc-sim fact/read seam
       ├─ Runtime read-only Capability -> ToolResult
       └─ Runtime ObservationSource -> NormalizedObservation -> Predicate
```

Sandbox 不需要在中间重新包装一层 5GC Observation。

## 5. Skill assurance 与 Agent-visible read-only Capability

Skill 的 `assurance/contract.yaml` 可以通过 `allowedResources.capabilities` 声明该 Skill 允许使用的 Capability 上限，例如包含查询/inspect 类 read-only Capability。

保持：

```text
allowedResources.capabilities
  = Skill 允许使用的 Capability universe / upper bound input

Runtime Resolved CA Toolset
  = 当前上下文中真正允许暴露给模型的 Capability 子集
```

前者不是 MCP Tool catalog，也不意味着其中所有 Capability 都直接 model-visible。Runtime/Harness 结合 Capability metadata、selected Skill/Artifact、Context/Template、AgentProfile/System、Environment availability、platform/security policy 等形成最终 eligibility。

Skill authoring 不需要把 ObservationBinding、raw ObservationRef 或 fact-owner endpoint 写进 `SKILL.md`。

## 6. Observation 复用

Agent read-only Capability 与 Runtime Assurance 可以复用同一条 acquisition result，只要 Runtime 能机械证明它满足当前 consumer 的要求：

```text
same fact/observation semantic
same environment / world / subject / parameters
same admitted binding identity
same source identity / compatible revision
valid provenance
freshness requirement satisfied
consumer policy permits reuse
```

如果任一条件不成立，Runtime 必须重新 acquire 或得到 `UNKNOWN`，不能因为“模型刚查过”就默认复用。

推荐结构：

```text
Runtime / Harness
  ├─ Resolved CA Tool eligibility
  ├─ read-only Capability execution
  └─ Assurance / Predicate
           │
           ▼
   Observation acquisition
   binding / cache / provenance
           │
           ▼
     ObservationSource
           │
           ▼
       Fact owner
```

不新增 `Planning Observation`、`Agent Observation Projection` 等第三种事实类型。

## 7. Observation 类型

Observation 的类型按事实语义/来源区分，而不是按 consumer 或 repository 名称区分：

```text
Network Observation
  = 网络/协议边界发生了什么
  = 典型 owner: env-fabric

5GC Domain / Environment Observation
  = 当前 UE / Session / QoS / connectivity 等业务状态是什么
  = simulation owner: env-5gc-sim
  = real_nf owner: env-5gc-real / unmodified real-5GC integration

Sandbox Environment/Fault Observation
  = Environment lifecycle / fault application / FaultReceipt 等 Sandbox-owned facts
```

例如：

```text
Network Observation:
  PFCP Session Establishment Response observed

5GC domain fact:
  PDU Session exists=true, SM state=operational

Sandbox fact:
  fault response-loss rule applied for invocation X
```

它们可在同一 Runtime Predicate/Case 中关联，但不能互相代替。

## 8. Provenance

Normalized Observation 至少要能表达/验证：

```text
sourceRef
bindingDigest or equivalent immutable binding identity
observation/catalog ref
source/world revision or fence where applicable
observedAt / freshness material where required
normalized value/content
Evidence refs / diagnostics where applicable
```

具体字段以 Runtime schema/code 为准。

Source/binding identity 缺失或与 resolved expectation 不匹配，必须在 Predicate evaluation 前 fail closed；read-only Capability 也不能把 provenance 不可信的数据升级成 trusted fact。

## 9. Missing / stale / invalid

具有合法 acquisition path 但事实：

```text
missing
invalid
stale
unavailable
```

在 Assurance 路径中通常进入 Runtime `UNKNOWN`，而不是由 adapter 自行判定 PASS/FAIL。具体 site 错误分类以 Predicate contract 为准。

在 Agent read-only Capability 路径中，应返回明确的 read result / unavailable knowledge，不得伪造成业务事实。

还必须区分：

```text
KNOWN_ABSENT
KNOWN_NEGATIVE
UNKNOWN / UNAVAILABLE
INVALID_QUERY
```

例如明确观察到“PDU Session 不存在”不是 ObservationSource unavailable。

## 10. Frozen material

Observation catalog / PredicateSet 等执行材料来自已验证 Artifact/Runtime Bundle/deployment material。Factory/Resolver 不得重新读取 mutable author workspace，也不得选择另一份 Bundle 改变当前 Run 语义。

Agent-visible read-only Capability 同样来自 Runtime admitted Capability catalog，并通过当前 Runtime-resolved CA Tool eligibility。Skill prose 不能扩大 Toolset、Authorization 或 Runtime admission。

## 11. Environment-specific adapter

以下属于 deployment/environment adapter：

```text
具体 fact owner endpoint/query 方式
Provider output 字段位置
enum -> normalized scalar/object mapping
credentials / transport / auth
source-specific identity/revision/timestamp acquisition
```

以下属于 Runtime/Harness：

```text
Capability admission / effect classification
ConnectionAgent Tool eligibility resolution
Observation binding resolution
expected binding/source identity validation
freshness contract / reuse policy
Predicate tri-state semantics
Assurance/Procedure use
Run/Evidence facts where contract requires
```

## 12. Sandbox migration rule

Legacy Sandbox `:8789` Observation API currently contains mixed fact domains. Target migration is:

```text
5GC facts
  -> direct Runtime binding to env-5gc-sim / env-5gc-real

Sandbox environment/fault facts
  -> may remain on Sandbox Observation surface
```

旧 5GC Observation relay 在消费者切换完成前可以兼容保留，但不得获得新消费者或成为新的 architecture dependency。

## 13. Benchmark GroundTruth 与 evaluator-only Source Facts

跨仓冻结：

```text
GroundTruth = ca-benchmarks 标准答案 / 金标准
Authoritative Source Fact = actual fact owner 的实际事实
```

Benchmark GroundTruth **不进入** Runtime ObservationSource，也不参与 Runtime Predicate / Outcome / Reconcile；Runtime 必须依据其正常 admitted Source Facts/Evidence 做可靠执行。

`env-5gc-sim` 等 owner 可以存在 evaluator-only Source Fact seam，但它属于 evaluation access policy。普通 Runtime ObservationSource 不得自动访问；Benchmark/Evaluator 应在 Runtime 之外独立收集这些事实。

```text
Runtime-visible Source Fact != evaluator-only Source Fact
Runtime Predicate verdict != Benchmark Oracle/Verdict
```

## 14. Schema

当前 normalized observation wire schema 位于：

```text
schemas/v1alpha1/normalized-observation.schema.yaml
```

本文不复制 schema 字段 authority。

## 15. 不变量

```text
ObservationSource acquires facts from the real fact owner; it does not decide Predicate verdicts.
Environment Observation is a fact class, not synonymous with Sandbox ownership.
Agent uses Runtime-resolved admitted read-only Capabilities, not raw ObservationRefs.
Agent inspection and Runtime Assurance may share the same fact source/acquisition.
Agent inspection result is planning input, never Assurance verdict authority.
Runtime Assurance does not depend on the Agent having inspected first.
Binding/source/provenance mismatch fails before Predicate evaluation.
Missing/invalid/stale facts do not become PASS by default.
Known absence is not source unavailability.
Network, 5GC-domain and Sandbox-environment facts keep their own authorities.
GroundTruth remains Benchmark-authored gold truth and is never a Runtime ObservationSource input; evaluator-only Source Facts stay outside ordinary Runtime execution.


## 16. Trial subject correlation boundary

Shared-Environment Benchmark execution introduces a correlation requirement that is related to, but not owned by, Runtime ObservationSource.

Runtime already guarantees Run-local lineage:

```text
runId
requestId
invocationId
toolCallId
procedureNodeId
```

These identify **which Runtime execution** produced a fact. They do not by themselves identify:

```text
which subscriber
which UE/device
which PDU Session
which PFCP session/resource
which protocol transaction
```

Do not solve this by copying SUPI/PDU Session IDs into every Runtime RunEvent.

Preferred closure:

```text
EvaluationTask / ExecutionAttempt
  -> TrialSubjectBinding
  -> Runtime request/runId binding
  -> provider invocation
  -> owner-native domain/protocol subject refs
```

Runtime should only expose subject/correlation material when it is already part of an admitted request/capability/provider contract. Benchmark Engine owns the cross-owner closure.

Observation cache reuse must therefore prove:

```text
same run/consumer scope
same Environment/world
same logical subject/parameters
same admitted binding/source
```

A same-environment observation for a different Trial subject is not reusable.

If a real 5GC deployment cannot map Trial subject to protocol/domain scope using external authoritative facts, shared-Environment subject-scoped evaluation is NOT_READY; do not add private 5GC hooks to Runtime to compensate.

## 17. Real Open5GS Registration source and retained evidence

For the first read-only Registration source, Runtime uses the canonical
`ObservationSource` resolver contract with the deployment-owned
`connectionagent.provider-observation/v1` request/result envelope. Runtime sends
only an already-resolved exact `subject.identities["5gc.supi"]`, the admitted
Observation ref, and Runtime correlation IDs. The Provider owns Open5GS
`/ue-info` acquisition and fact normalization; Runtime owns provenance
validation, freshness, UNKNOWN, and `ue.registered` verdict semantics. Missing
or ambiguous Registration remains unavailable and is never converted to
`KNOWN_ABSENT`.

Runtime retains each normalized Observation value, acquisition status, evidence
labels, and source/binding/correlation provenance in the emitted
`verification.completed` event at evaluation time. The retained snapshot omits
request scope and subject identity so Inspector can review the historical fact
without querying the live Provider again.

## 18. Source-native SMF PDU Session context

`smf.pdu_session.context` is a Runtime-owned Observation distinct from
`pdu.session.snapshot`. It means only that the authoritative SMF source
currently reported a PDU Session context matching the exact UE and PSI scope.

```text
scope: {ueRef, pduSessionId}
value: {psi, dnn, sNssai, pduState}
```

`pduState` preserves the source-native `active`, `inactive`, or `unknown`
value. In particular, `active` does not prove
`pdu.session.snapshot.established=true`, and `inactive` does not prove
`established=false`. This source does not prove PFCP/UPF resource installation,
UE-side PS-ACTIVE, TUN readiness, connectivity, or QoS.

Missing, duplicate, ambiguous, malformed, or otherwise unprovable source
results are `UNAVAILABLE`; Runtime Predicate evaluation follows the ordinary
`UNKNOWN`/blocked path. No absence boolean or `KNOWN_ABSENT` result is added.
The established snapshot contract remains unchanged. Open5GS S-NSSAI `sd=ffffff`
is the no-SD sentinel and normalizes to an omitted `sd` member, never an
ordinary SD value.

The narrow target Predicate (Skill-owned definition, Runtime-evaluated) may
PASS only when acquisition is `FOUND` and observed PSI, DNN, and S-NSSAI all
match the requested target under canonical normalization. Mismatch or invalid
target comparison follows the existing Predicate tri-state contract; source
uncertainty stays `UNAVAILABLE` and therefore evaluates `UNKNOWN`.

### Opt-in live joined acceptance

`TestLiveProviderRuntimeSMFContextPredicateAcceptance` in
`internal/provider/remoteobservation/` runs the Runtime remote source and
Predicate against a running `ca-provider-5gc` service configured with explicit
Open5GS `/pdu-info` and `/ue-info` endpoints. Supply `CA_LIVE_PROVIDER_URL`,
the exact canonical `CA_LIVE_5GC_SUPI`, `CA_LIVE_RUNTIME_RUN_ID`,
`CA_LIVE_PDU_SESSION_ID`, `CA_LIVE_DNN`, `CA_LIVE_SNSSAI_SST`, and optional
`CA_LIVE_SNSSAI_SD` from the operator-owned live UE/request configuration.
Never echo or retain the SUPI.

The positive case requires an observed exact context and a Runtime Predicate
`PASS`. It then tries alternate PSI values until the Provider reports an
unavailable exact context and verifies Runtime `UNKNOWN`. Setting
`CA_LIVE_ACCEPTANCE_EVIDENCE_PATH` writes the execution-time normalized
Predicate material and sanitized provenance with mode `0600`; the artifact omits subscriber identity and the raw Provider request; it retains only sanitized normalized observation and non-sensitive target/evaluation material needed to audit the Predicate. The ordinary RunStore event test
continues to verify that this same normalized material is retained in
`verification.completed` for replay without a source reread.

## 19. Source-native UPF PFCP resource Observation

`upf.pfcp_session.resources` is a separate read-only Observation for the
source-native PDR, FAR, and QER resources reported by Open5GS. Its scope is
`{ueRef, pduSessionId}` and its value contains exactly `{pdr, far, qer}`
arrays, including empty arrays. Runtime sends the exact canonical SUPI only
as transient Provider request input and the exact PSI; the Provider owns the
SMF/UPF exact-subject and exact-PSI join and must report exactly one matching
pair. Runtime accepts only the Provider's bounded normalized source
projection and safe provenance. It does not correlate by IP, TEID, timing, or
other heuristics.

This Observation says only what source-native UPF resource rows were
reported. It does not establish canonical PDU Session state, QoS satisfaction,
UE-side truth, user-plane connectivity, or Fabric state. Missing, duplicate,
ambiguous, malformed, or unprovable source data yields `UNAVAILABLE`, which
the Runtime Predicate path preserves as `UNKNOWN`; it is not a negative
resource assertion.

The opt-in `TestLiveProviderRuntimeUPFResourcesObservationAcceptance` in
`internal/app/upf_live_acceptance_test.go` exercises the real Provider
adapter, Runtime Observation/Predicate path, and RunStore retention. It uses
`CA_LIVE_PROVIDER_URL`, `CA_LIVE_5GC_SUPI`, `CA_LIVE_RUNTIME_RUN_ID`, and
`CA_LIVE_PDU_SESSION_ID`; identity is transient and must never enter logs or
evidence. The test checks an observed exact pair and a safe alternate-PSI
`UNKNOWN`, then verifies retained normalized data can be reviewed without a
Provider reread. An optional sanitized manifest path is
`CA_LIVE_ACCEPTANCE_EVIDENCE_PATH`.


## 20. Source-native facts and environment-owned composite facts

Observation catalog membership does not require every deployment to provide the same fact strength. A deployment may bind an Observation only when its selected owner can prove the complete admitted value semantics.

For PDU Session assurance, the canonical decision is documented in [pdu-assurance-contract.md](pdu-assurance-contract.md):

- real Open5GS uses narrow source-native `smf.pdu_session.context` and `upf.pfcp_session.resources` Observations;
- current real Open5GS does not bind `pdu.session.snapshot` because `established` / `qosSatisfied` are not source-provable;
- the deterministic reference simulator may continue binding `pdu.session.snapshot` because it directly owns that composite world fact;
- missing/unavailable real evidence remains UNKNOWN and is never converted to definite absence merely to satisfy a cross-environment shape.


## CreatedSession UDM Get candidate

The [UDM Get Runtime candidate](createdsession-udm-get-contract.md) proposes `sbi.operation.result` using the existing NormalizedObservation/ObservationCatalog envelopes. Its value contains immutable transaction evidence and original event time; historical acquisition does not refresh that time or imply current NF state. This candidate is not registered and does not extend the current source allowlist. Production adapter, binding admission and live qualification remain ca-runtime#172 work.
