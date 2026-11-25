> 迁移来源：ca-runtime/docs/design/pdu-assurance-contract.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# PDU Session assurance: source-native facts vs composite facts

Status: Accepted  
Version: v1.0  
Date: 2026-10-22  
Tracking: ca-runtime#168, ca-runtime#164, env-open5gs#15, ca-skills#19

## 1. Decision

Runtime does **not** require every 5GC backend to populate one universal strong PDU Session snapshot.

Two classes are distinct:

```text
source-native / source-provable Observation
  = a fact the selected owner can actually prove with its own lifecycle semantics

environment-owned composite Observation
  = a stronger fact directly owned by an environment whose model explicitly
    defines that composite semantic
```

The existing `pdu.session.snapshot` remains admitted as an environment-owned
composite Observation. The reference simulator may bind it because the
simulator owns the complete PDU Session world model and can authoritatively
produce `established`, `qosSatisfied`, and definite absence/negative
semantics.

Real Open5GS currently MUST NOT bind `pdu.session.snapshot`. The pinned
Open5GS v2.8.0 source audit in env-open5gs#15 concluded that the current core
owner state cannot safely prove canonical `established=true` or
`established=false`.

This is an availability difference between admitted environment bindings, not
a request to weaken the Observation schema.

## 2. Real Open5GS source-native facts

The accepted real path currently exposes:

```text
smf.pdu_session.context
  scope: {ueRef, pduSessionId}
  value:
    psi
    dnn
    sNssai
    pduState

upf.pfcp_session.resources
  scope: {ueRef, pduSessionId}
  value:
    pdr[]
    far[]
    qer[]
```

These Observations preserve source-owned semantics.

They do not imply:

```text
pdu.session.snapshot.established
pdu.session.snapshot.qosSatisfied
user-plane connectivity
UE-side state
PFCP transaction history
```

The exact SMF-to-UPF owner-state join is useful evidence, but it does not
upgrade either source-native Observation into a canonical establishment
boolean.

## 3. Simulator composite semantics

The deterministic reference simulator may expose:

```text
PDU_SESSION
  established
  qosSatisfied
  dnn
  sNssai
```

and Runtime may normalize the admitted subset through
`pdu.session.snapshot`.

That is safe only because the simulator is the owner of that modeled world
state and its fact-read contract can return definite FOUND / KNOWN_ABSENT /
KNOWN_NEGATIVE semantics.

A simulator-owned composite does not create a cross-environment requirement:

```text
simulator can prove X
!=
every real backend must synthesize X
```

## 4. Binding rule

Observation catalog membership means:

> this Observation semantic is known to Runtime and may be used by an admitted
> Artifact when the selected deployment has a trusted binding that can prove it.

It does **not** mean:

> every deployment must provide this Observation.

Therefore:

```text
selected deployment has admitted binding
  -> acquire and evaluate under ordinary Runtime rules

selected deployment has no admitted binding
  -> unavailable / UNKNOWN

adapter cannot prove required value
  -> unavailable / UNKNOWN
```

Runtime and deployment composition must not manufacture an absent value merely
to satisfy a catalog shape.

## 5. UNKNOWN is not absence

For current real Open5GS:

```text
exact SMF context unavailable
!= session absent

missing AMF PSI activation bit
!= session absent

SMF up_cnx_state NULL / DEACTIVATED
!= established=false

empty PDR/FAR/QER
!= established=false
```

The real read surfaces do not provide a snapshot revision/global absence
contract strong enough to turn an unmatched page walk into canonical
`established=false`.

Consequently:

```text
UNAVAILABLE / UNKNOWN
!= FAIL
!= KNOWN_ABSENT
!= permission to create
```

This distinction is especially important for mutation Procedures.

## 6. Skill predicate guidance

Skill owns predicate semantics; Runtime owns trusted evaluation.

For real Open5GS, prefer predicates whose names state exactly what their source
facts prove, for example:

```text
target context matches requested PSI/DNN/S-NSSAI
current UPF PFCP resources are observed
```

Do not rename those facts to stronger semantics such as:

```text
session established
session ready
QoS satisfied
```

unless an admitted owner contract actually proves those meanings.

The concrete exported Predicate identities and Procedure branches are owned by
ca-skills#19.

## 7. Mutation consequence

A Procedure must not use unavailable evidence as a reason to mutate.

Unsafe:

```text
pdu_session.established != PASS
  -> create session
```

or:

```text
SMF exact context unavailable
  -> assume absent
  -> create session
```

A real mutation path needs a separate safe contract, such as an authoritative
absence fact, owner-supported idempotent operation semantics, or a reconcile
contract that makes ambiguity safe. That design is outside this Runtime
contract decision.

## 8. QoS and connectivity

Keep these independent:

```text
session target/context evidence
UPF PFCP resource evidence
QoS satisfaction
user-plane connectivity
```

PDR/FAR/QER presence, FAR action, QER gate state, or QFI does not automatically
prove the user-facing QoS requirement.

Connectivity may be a Skill postcondition, but it must have its own trusted
owner/source contract. It is not a substitute for session establishment.

## 9. UERANSIM and Fabric boundaries

UERANSIM is an external acceptance/benchmark oracle only. Runtime and Provider
must not query it to construct production PDU Session truth.

Fabric remains the protocol/network-event owner. It is not required for the
current SMF-to-UPF owner-state join and protocol evidence must not be silently
promoted to current domain state.

## 10. Current environment matrix

| Semantic | Reference simulator | Real Open5GS |
| --- | --- | --- |
| `pdu.session.snapshot.established` | owner-provable composite | unavailable / UNKNOWN |
| `pdu.session.snapshot.qosSatisfied` | owner-provable composite | unavailable / UNKNOWN |
| exact DNN/S-NSSAI target context | simulator owner fact | `smf.pdu_session.context` |
| current UPF PFCP resources | simulator owner fact / PFCP fact | `upf.pfcp_session.resources` |
| authoritative session absence | owner-defined simulator resolution | not currently proven |
| user-plane connectivity | separate owner fact | separate contract required |

## 11. Follow-up ownership

```text
ca-runtime#168
  = this platform binding/semantic boundary

ca-runtime#164
  = real Open5GS canonical establishment gap remains fail-closed

ca-skills#19
  = rebase session predicates and mutation applicability on source-provable facts

ca-agent-demo#85
  = mirror frozen Skill contracts after ca-skills#19
```

No new Open5GS overlay follows from this decision.
