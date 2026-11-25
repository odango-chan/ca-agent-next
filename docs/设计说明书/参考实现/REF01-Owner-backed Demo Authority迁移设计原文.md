> 迁移来源：ca-agent-demo/docs/design/owner-backed-demo-authority-migration.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：Demo Owner-backed authority 迁移设计  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；证据的当前有效性需按具体 main/PR/测试 SHA 单独核验。

---

# Owner-backed Demo Authority Migration

Status: DESIGN FROZEN FOR IMPLEMENTATION
Tracking: #34
Mechanical implementation contract: `docs/design/owner-backed-demo-migration-implementation.md`
Date: 2026-10-10

**CLI naming update (#36):** the business Scenario is `hero`; execution backing
is selected through the `owner-backed` Execution Profile. Supplying owner URLs
normally selects that profile automatically. Owner truth, identity authority,
reset fencing, and no-fallback requirements are unchanged.

## 1. Purpose

This design removes the remaining Demo-local identity and world-truth shortcuts
from the canonical sim-backed Planning V2 Hero.

The target is not “replace every constant with an HTTP call”. The target is a
clean authority split:

```text
tool-common
  = user-visible/logical/domain identity authority

env-5gc-sim
  = deterministic simulated 5GC + user-plane/session-activity fact owner
  = deterministic simulated 5GC mutation owner

ca-agent-demo
  = Intent / Skill / Planning / Assembly / Runtime orchestration / trace
  = consumer of admitted owner facts
```

The canonical Demo must be able to answer:

```text
“UE-B 是谁？”
  -> tool-common evidence

“UE-B 的 Session 10 现在是否承载 video？”
  -> env-5gc-sim C2 SourceFact evidence
```

without falling back to a Planning Mock fixture.

### 1.1 Implementation rule: observability ships with the owner call

Owner-backed acquisition and its trace are one deliverable.

Do not implement:

```text
owner integration now
-> Observation/identity trace later
```

Instead:

```text
Common Provider lookup introduced
-> SUBJECT_IDENTITY_REQUESTED / RESOLVED / SNAPSHOT_FROZEN introduced in the same phase

env-5gc-sim activity observation introduced
-> OBSERVATION_REQUESTED / OWNER_FACT_REQUESTED / OWNER_FACT_RESULT /
   OBSERVATION_NORMALIZED introduced in the same phase

Context resolver admits the fact
-> CONTEXT_FACT_ADMITTED introduced in the same phase
```

The later Inspector/TUI phase only groups and presents already-persisted
evidence. It must not be the first place the evidence exists.

For a low-capability implementation agent, the normative step-by-step file,
DTO, test, failure, and Exit Gate instructions are in
`owner-backed-demo-migration-implementation.md`. If that implementation
contract and a developer guess differ, follow the implementation contract and
raise the concrete conflict on #34 rather than improvising.

## 2. Scope and non-goal

This design covers:

- independently deployed `tool-common` identity read/control surfaces;
- independently deployed `env-5gc-sim serve-standalone`;
- canonical sim-backed `ca-plan` execution;
- exact identity binding and fencing;
- owner-native session activity;
- owner-backed Planning Context;
- Observation acquisition lineage;
- model-facing context hygiene;
- removal/isolation of Demo-local shortcuts.

This design does not:

- add production `ca-runtime` as a dependency;
- change Agent-facing `tool-mcp-gw`;
- make `tool-common` part of `env-5gc-sim`;
- make `env-5gc-sim` resolve user-visible aliases;
- make `env-5gc-sim` choose Planning strategies;
- move candidate-session search policy into `env-5gc-sim`;
- invent a second identity semantic contract or a Planning-Mock-owned identity API;
- add a redundant Common Provider `serve-standalone` mode;
- change hidden-provider / chain-of-thought observability policy;
- require backward compatibility with accidental Demo-local DTOs.

## 3. Existing accepted owner contracts

### 3.1 Common subject identity owner

`tool-common` already freezes the canonical capability:

```text
subject.identity.lookup@v1
```

Request:

```json
{"reference": "UE-B"}
```

Successful semantic result:

```json
{
  "status": "RESOLVED",
  "reference": "UE-B",
  "subjectRef": "receiver-b",
  "canonicalName": "UE-B",
  "matchedBy": "NAME",
  "identities": {
    "5gc.supi": "001010000000002"
  },
  "mappingRevision": "trial-...",
  "provenance": {
    "configDigest": "sha256:...",
    "entryCount": 2
  }
}
```

The compatibility capability `ue.identity.lookup@v1` remains supported but
the new canonical Demo path consumes the domain-neutral result.

The process is independently deployable. ADR-0002 / tool-common#6
freezes the target owner transport as HTTP/JSON:

```text
tool-common serve --config <file>

provider listener
  GET  /identity
  GET  /healthz
  GET  /readyz
  POST /v1/subject-identities/lookup

control listener
  GET  /identity
  GET  /healthz
  GET  /readyz
  POST /internal/v1/subject-identities/configure
  POST /internal/v1/subject-identities/reset
```

The two listeners remain intentionally separate trust surfaces.
`tool-mcp-gw` is the Agent-facing MCP; Common Provider is a backend owner.
Planning Mock P1 MUST wait for the stable HTTP owner API from
`tool-common#6` rather than implementing against the historical
Provider-side MCP wire.

### 3.2 Simulated 5GC fact/mutation owner

`env-5gc-sim` already owns the canonical simulated facts needed for:

- UE registration;
- registration context;
- PDU Session lifecycle / identity / DNN / S-NSSAI;
- QoS;
- user-plane connectivity;
- PFCP resources;
- transfer participants/endpoints;
- virtual group state;
- transfer QoS;
- C6 mutation.

The standalone owner profile already exposes the same C2/C6 HTTP surface as
the integrated process and does not require Sandbox or Service Fabric.

## 4. Current authority leaks

The current implementation has a correct owner-backed base but still contains
the following shortcuts.

### 4.1 Direct alias-to-SUPI authority in Planning Mock

Current scenario manifests contain:

```yaml
participants:
  aliasToSupi:
    UE-A: "001010000000001"
    UE-B: "001010000000002"
```

`load_scenario()` and the canonical sim path turn this directly into
`owner_identity_map`.

`src/ca_agent_demo/integrations/env_5gc_sim/identity.py` then implements:

```text
alias -> mapping lookup -> SUPI
```

and the resulting map is used for Planning Predicate acquisition and Runtime
request materialization.

This bypasses the admitted `tool-common` authority.

### 4.2 Direct active-video authority in Planning Mock

Current sim scenario manifests contain:

```yaml
semanticSessionFacts:
  - ownerAlias: UE-B
    pduSessionId: 10
    carryingService: video
```

The current canonical sim preparation reads this value into
`HeroScenario.carrying_service`, then directly creates a ContextFact similar
to:

```text
hero.session.10.carryingService = video
authority/source = Demo-local scenario material
```

Candidate bindings may additionally carry the same `carryingService`
attribute.

Therefore the Planning model can learn the key Hero semantic without observing
the 5GC owner.

### 4.3 Pre-authored virtual-group identity

The sim candidate path still constructs group material containing a concrete
`group-id: vg-1`.

The accepted sim-backed design requires the prepare path to preserve
owner-generated groupId lineage. A pre-run VG identifier is therefore not a
canonical owner-backed input.

### 4.4 Observation acquisition is hard to inspect

The current PredicateEngine emits `OBSERVATION_ACQUIRED` only after:

```text
ObservationSource.acquire(...)
```

has completed.

The persisted trace therefore does not make the entire acquisition path
obvious:

```text
why this observation was requested
-> stable observation request
-> provider-specific owner query
-> raw owner resolution / SourceFact
-> normalization rule
-> normalized value
-> Predicate / ContextFact consumption
```

### 4.5 Observability metadata leaks into model input

Current model-visible fact serialization can include fields such as:

- fact id;
- source ref;
- BaseContext / ContextRequirement origin;
- resolver id;
- introduced revision;
- trace/correlation identifiers.

These are useful for Inspector provenance but mostly irrelevant to semantic
selection.

## 5. Authority model after migration

### 5.1 Identity

```text
user-visible reference
  -> tool-common
  -> logical subjectRef
  -> namespaced domain identities
```

The authoritative mapping is not stored in the Planning Host.

### 5.2 5GC/session state

```text
exact 5gc.supi + domain subject
  -> env-5gc-sim C2
  -> SourceFact
```

The authoritative current world is not stored in the Planning Host.

### 5.3 Planning interpretation

```text
business Goal/open constraint
+ selected Root Skill semantics
+ Host-projected owner facts
+ Host-enumerated hard-valid candidates
  -> bounded semantic selection
```

Neither owner decides the Planning strategy.

### 5.4 Bootstrap authoring

A Demo must still author an initial test environment.

Bootstrap authoring is allowed to say:

```text
for this scenario configure:
  UE-B -> receiver-b -> 001010000000002

for this scenario seed:
  PDU Session 10
  active video activity
```

but runtime code may only learn the resulting state from the owners.

Therefore:

```text
bootstrap input
!= runtime fact authority
```

## 6. Canonical run topology

```text
┌─────────────────────────┐
│ tool-common      │
│                         │
│ provider listener       │◄──── identity read
│ control listener        │◄──── trusted bootstrap only
└─────────────────────────┘

┌─────────────────────────┐
│ env-5gc-sim              │
│ serve-standalone        │◄──── C2 read / C6 mutation / reset
└─────────────────────────┘

┌─────────────────────────┐
│ ca-plan                 │
│                         │
│ Intent / Routing        │
│ Identity acquisition    │
│ Context / Formal        │
│ Semantic Planning       │
│ Assembly / Runtime      │
│ Trace                   │
└─────────────────────────┘
```

No process owns another process lifecycle in the externally managed profile.

## 7. CLI and deployment contract

Preferred user-facing profile:

```bash
tool-common serve --config common.json
env-5gc-sim serve-standalone --config sim.json

uv run ca-plan run \
  --scenario hero \
  --sim-url http://127.0.0.1:8787 \
  --identity-provider-url http://127.0.0.1:8790 \
  --intent "把文件传给 UE-B，但别影响它现在正在看的视频。"
```

Rules:

- explicit URL or explicit environment variable only;
- no port scan;
- no process autodiscovery;
- no implicit localhost default on the canonical path;
- `ca-plan` does not stop externally managed owner processes;
- read and control Common Provider endpoints are never conflated.

Trusted acceptance/bootstrap tooling may additionally accept:

```text
--identity-control-url
```

to seed/reset the mapping before the Host run.

The canonical Host receives only the read endpoint.

Suggested environment fallbacks:

```text
CA_5GC_SIM_URL
CA_COMMON_IDENTITY_PROVIDER_URL
CA_COMMON_IDENTITY_CONTROL_URL   # bootstrap/acceptance only
```

If existing CLI naming conventions require another exact spelling, preserve
the semantics above rather than inventing discovery.

The Common Provider client is a strict synchronous HTTP/JSON owner client,
parallel in style to `FiveGCSimClient`. It must not depend on an MCP SDK and
must not preserve the retired Provider-side MCP protocol.

## 8. Frozen identity binding

### 8.1 Data shape

Introduce one typed attempt/run-scoped identity binding conceptually:

```text
ResolvedSubjectIdentity
  reference
  subject_ref
  canonical_name
  matched_by
  identities
  mapping_revision
  config_digest
  entry_count
```

For 5GC execution, the Host derives:

```text
5gc.supi
```

from the frozen canonical `identities` map.

### 8.2 Validation

Only `RESOLVED` is executable.

```text
RESOLVED
  -> freeze exact binding

NOT_FOUND
  -> planning blocked / clarification required

AMBIGUOUS
  -> planning blocked / clarification required

transport/protocol/config error
  -> fail closed
```

No fallback is allowed to:

- Demo manifest aliases;
- first matching SUPI;
- latest UE;
- Benchmark truth;
- env-5gc-sim registration enumeration.

### 8.3 Fence

All subject lookups used to materialize one Planning attempt must have the same:

```text
mappingRevision
configDigest
```

A mixed revision/digest set is a failed identity snapshot.

An accepted attempt never silently re-resolves a subject onto a new revision.

A later explicitly authorized replan may reacquire identity only if the Host
defines that as a new Context revision and re-runs grounding. First
implementation should prefer keeping the run-scoped binding stable.

## 9. Where identity resolution occurs

Identity lookup is not an Intent Interpreter responsibility and is not a Skill
body side effect.

Canonical ordering:

```text
ProductTask.intent
-> business-only ProducedGoal
-> exact Root Skill routing
-> derive grounded identity requirements from business refs
-> tool-common lookup
-> freeze identity binding
-> owner-backed Planning Context / Formal grounding
```

This preserves:

- Intent business-only semantics;
- Skill routing before domain-specific Planning;
- explicit Context acquisition;
- deterministic owner identity before C2/C6.

Both sender and receivers used by execution must be resolved through the same
identity snapshot even when the user only names the receiver.

The scenario may still provide the sender's business reference as task/bootstrap
input. It does not provide the execution SUPI directly to canonical Host code.

## 10. Owner-native session activity

### 10.1 Why a separate fact

Do not overload `PDU_SESSION`.

These are distinct facts:

```text
session exists
session established
session QoS
user-plane connectivity
current service/application activity
```

The domain model already separates session lifecycle from user-plane state.
The Hero requires one additional current activity dimension.

### 10.2 World state

Add a separate owner-local state keyed by exact PDU Session identity,
conceptually:

```text
SessionActivityKey
  SUPI
  PDUSessionID

SessionActivityState
  Active
  ServiceClass
```

It is not duplicated into `PDUSessionState`.

State invariants:

- key SUPI/session id must be valid;
- if an activity refers to a Session, the Session must exist in the same world;
- `active=true` requires a non-empty service class;
- first Hero value is `video`;
- activity mutation is not required by this migration unless a later scenario
  needs it.

### 10.3 C2 fact semantic

Freeze:

```text
factSemantic = PDU_SESSION_ACTIVITY
recordFamily = 5gc.pdu_session_activity
recordType   = PduSessionActivityFact.v1

subjectRef:
  kind: PDU_SESSION
  supi
  pduSessionId
```

Value:

```json
{
  "active": true,
  "serviceClass": "video"
}
```

Resolution:

```text
FOUND
  owner has a modeled activity state

KNOWN_ABSENT
  owner authoritatively has no activity record for the Session

UNAVAILABLE / INDETERMINATE
  owner cannot currently establish the fact

INVALID_QUERY
  caller/integration defect
```

Do not map UNKNOWN to “not video”.

### 10.4 Seed/reset

The existing registered-active-session seed must gain deterministic activity
provisioning or an equally explicit owner seed extension.

Preferred bootstrap shape:

```json
{
  "sessionActivities": [
    {
      "supi": "001010000000002",
      "pduSessionId": 10,
      "active": true,
      "serviceClass": "video"
    }
  ]
}
```

The value may originate from Demo/acceptance bootstrap material, but once
seeded the only runtime authority is env-5gc-sim C2.

Do not require a second simulator process or a Planning Mock-side activity
registry.

## 11. Stable Observation mapping

Add:

```text
pdu.session.activity.snapshot
  -> PDU_SESSION_ACTIVITY
```

The generic prototype request remains:

```text
ObservationRequest
  observation_ref = pdu.session.activity.snapshot
  scope:
    supi
    pduSessionId
  correlation_refs
```

`FiveGCSimObservationSource` is the only layer that knows this maps to the
owner-specific C2 semantic.

Normalization:

```text
FOUND
  -> {"active": bool, "serviceClass": string}

KNOWN_ABSENT
  -> deterministic definite absence shape

UNAVAILABLE / INDETERMINATE
  -> UNKNOWN observation
```

## 12. Planning semantic ContextFact

The current direct fact:

```text
hero.session.10.carryingService = video
```

must disappear from canonical sim BaseContext.

Preferred semantic fact exposed to Planning:

```text
pdu.session.activity
subject:
  5gc.supi
  pdu-session-id
value:
  active
  serviceClass
authority:
  env-5gc-sim
```

This is a read-only semantic Context fact, not necessarily a Predicate verdict.

Do not invent a dummy Predicate solely to move `video` through the existing
Predicate resolver.

Add a narrow read-only Context resolver over `ObservationSource` if needed.

## 13. Formal candidate boundary

Owner facts and candidate semantics must remain distinct.

Allowed candidate material:

```text
candidate identity
bounded resource/session binding
Host-owned strategy class/dimensions
machine-derived hard-validity
```

Forbidden candidate shortcut:

```text
candidate.attributes.carryingService = video
```

when the value is meant to describe current owner state.

The strategy descriptors remain Host-owned:

```text
reuse-existing:
  ACTIVE_SESSION_IMPACT=TOUCHES_ACTIVE_SESSION
  RESOURCE_REUSE_MODE=REUSE_EXISTING

use-additional:
  ACTIVE_SESSION_IMPACT=AVOIDS_ACTIVE_SESSION
  RESOURCE_REUSE_MODE=ALLOCATE_ADDITIONAL
```

They do not move into either provider.

## 14. Candidate Session IDs

```text
candidatePduSessionIds = [11, 12]
```

does not automatically move to env-5gc-sim.

It currently represents a bounded Host/Scenario search/allocation domain, not
an observed current-state fact.

Keep it outside the simulator until a real allocation authority is explicitly
introduced.

env-5gc-sim may prove:

```text
Session 11 absent
Session 12 absent
```

but it does not decide which IDs the Planner is allowed to enumerate.

## 15. Network policy

DNN / S-NSSAI / requested 5QI remain task/environment policy input.

The simulator materializes and proves the current state produced by that policy
but does not become the global policy author.

This matches the existing `SeedNetworkPolicy` provenance design.

## 16. Virtual-group groupId

Canonical prepare must not pre-author an owner-generated group identity.

Remove:

```text
group-id = vg-1
```

from canonical prepare candidate/request material when it precedes
`VIRTUAL_GROUP_CREATE`.

Required lineage:

```text
VIRTUAL_GROUP_CREATE
  -> owner result.output.groupId
  -> frozen continuation/output binding
  -> assign/reconcile/read
```

Release-only paths that begin with a concrete existing group may still require
a concrete group id from owner-backed Context.

Add a source audit proving canonical prepare contains no `vg-1` fixture.

## 17. Observation lineage design

### 17.1 Goal

For every model-visible or Predicate-consumed owner fact, a human must be able
to answer:

```text
who asked?
what stable observation was requested?
what owner query was issued?
what did the owner return?
how was it normalized?
where was the normalized fact consumed?
```

without rereading a live owner.

### 17.2 Events

Persist these events/materials.

#### OBSERVATION_REQUESTED

Before acquisition:

```text
observation_ref
scope
correlation refs
consumer kind
consumer identity
attempt
```

Consumer examples:

```text
PredicateDefinition exact identity
ContextRequirement id
direct semantic context requirement
```

#### OWNER_FACT_REQUESTED

Before C2 request submission:

```text
owner = env-5gc-sim
factSemantic
subjectRef
readMode = CURRENT
worldRef
worldGeneration
correlation refs
```

Do not dump transport credentials.

#### OWNER_FACT_RESULT

After strict owner response validation:

```text
resolution
factSemantic
subjectRef
SourceFact ref/material
worldRef
worldGeneration
evaluatedWorldRevision
reasonCode
content/schema provenance
```

For transport failure, persist the safe failure classification rather than
inventing a SourceFact.

#### OBSERVATION_NORMALIZED

After pure provider-specific normalization:

```text
observation_ref
status
normalized semantic value
normalized digest
source fact refs
normalizer identity/version
```

#### PREDICATE_EVALUATED

Existing Predicate verdict event remains the assurance sink.

#### CONTEXT_FACT_ADMITTED

For direct semantic Context facts, persist:

```text
fact semantic/key
value
subject
authority
source observation material
PlanningContext introduced revision
visibility
```

### 17.3 Event order

For a direct Context fact:

```text
CONTEXT_REQUIREMENT / semantic need
< OBSERVATION_REQUESTED
< OWNER_FACT_REQUESTED
< OWNER_FACT_RESULT
< OBSERVATION_NORMALIZED
< CONTEXT_FACT_ADMITTED
< MODEL_VISIBLE_CONTEXT_BUILT
```

For a Predicate:

```text
PREDICATE evaluation start
< OBSERVATION_REQUESTED
< OWNER_FACT_REQUESTED
< OWNER_FACT_RESULT
< OBSERVATION_NORMALIZED
< PREDICATE_EVALUATED
```

### 17.4 Persisted material only

Inspector/TUI must project stored material.

Reopening a completed run must not:

- call tool-common;
- call env-5gc-sim;
- reread a current Skill;
- reread a current scenario manifest;
- reconstruct evidence from current code.

## 18. Identity lookup trace

Identity acquisition gets the same provenance quality.

Recommended events:

```text
SUBJECT_IDENTITY_REQUESTED
SUBJECT_IDENTITY_RESOLVED
IDENTITY_SNAPSHOT_FROZEN
```

Persist:

```text
reference
semantic status
subjectRef / canonicalName
namespaced identities
mappingRevision
configDigest
entryCount
provider endpoint identity (safe)
```

Do not persist Authorization headers or hidden transport secrets.

The Planning model normally does not need mapping revision or config digest.

## 19. Model-facing context hygiene

Trace provenance and model semantic input are separate projections.

### 19.1 Persisted source ContextFact

May contain rich evidence:

```text
fact_id
semantic key
value
subject
authority
source_ref
freshness
origin
requirement id/reason/source
resolver id
introduced revision
source event/material refs
```

### 19.2 Effective model-facing fact

Preferred minimal shape:

```json
{
  "key": "pdu.session.activity",
  "subject": {
    "pduSessionId": 10
  },
  "value": {
    "active": true,
    "serviceClass": "video"
  }
}
```

Whether exact SUPI is model-visible should follow least-information need. The
candidate/Goal may already identify UE-B; if the SUPI is not semantically
needed by the chooser, omit it from the model projection while retaining it in
Host provenance.

Authority/freshness may be included only when they affect semantic
interpretation.

### 19.3 Audit-only fields

Keep out of the effective prompt unless a concrete semantic need is proven:

- fact ids/digests;
- owner source refs;
- resolver ids;
- ContextRequirement ids;
- introduced revision;
- model-call ids;
- Goal digest;
- event/material refs;
- identity mapping revision/digest.

Request Assembly must still retain them.

## 20. Scenario manifest after migration

The scenario remains useful as authoring/bootstrap material.

Preferred conceptual split:

```text
business task
  sender reference
  receiver references
  transfer id
  urgency
  duration
  requested network policy
  bounded candidate domain

bootstrap
  Common Provider identity entries
  env-5gc-sim seed/reset material
```

During migration, existing `aliasToSupi` / `semanticSessionFacts` fields
may temporarily remain in YAML, but:

- Host/Planning code must not read `aliasToSupi` for execution identity;
- Host/Planning code must not read `semanticSessionFacts` for current state;
- only bootstrap tooling may transform them into owner control/seed requests.

After canonical acceptance, rename/move these fields so their bootstrap-only
role is mechanically obvious.

## 21. Fixture-backed hero profile

`--scenario hero` remains useful.

Its meaning after this migration:

```text
fixture-backed offline mechanism regression
```

It may retain:

- in-process identity fixture;
- RuntimeWorld fixture facts/outcomes;
- deterministic local fake world;
- no external provider dependency.

It must not be used as evidence for:

- owner-backed identity;
- owner-backed 5GC truth;
- external process lifecycle;
- strongest Demo acceptance.

Documentation/CLI output should identify it as fixture-backed when relevant.

## 22. Canonical owner-backed Hero

The strongest human-facing Demo is the Hero Scenario executed with separately
managed `tool-common` and `env-5gc-sim` owners. In normal use, owner URLs
resolve the profile automatically:

```bash
uv run ca-plan run \
  --scenario hero \
  --sim-url http://127.0.0.1:8787 \
  --identity-provider-url http://127.0.0.1:9801 \
  --intent "把文件传给 UE-B，但别影响它现在正在看的视频。"
```

`--profile owner-backed` remains an explicit override for readiness checks,
debugging, and fail-fast validation.

Required owners:

```text
Common Provider read endpoint
env-5gc-sim C2/C6 endpoint
```

Required runtime facts:

```text
identity -> Common Provider
registration/session/QoS/connectivity/activity/VG -> env-5gc-sim
```

No synthetic fallback is allowed if either owner is unavailable.

## 23. Common Provider bootstrap

Acceptance harness may provision:

```text
UE-A
  subjectRef: sender-a
  name: UE-A
  identities:
    5gc.supi: 001010000000001

UE-B
  subjectRef: receiver-b
  name: UE-B
  identities:
    5gc.supi: 001010000000002
```

through:

```text
configure_subject_identity
```

with an explicit mapping revision.

The Host must then independently call:

```text
lookup_subject_identity
```

on the provider listener.

Provisioning success is not runtime lookup evidence.

## 24. env-5gc-sim bootstrap

Acceptance harness seeds/reset the owner world with:

- exact registered SUPIs;
- protected Session 10;
- baseline network policy;
- active session activity `video`;
- any other already accepted owner-local seed state.

The Host then independently proves the required facts through C2.

Reset success is not Planning Context evidence.

## 25. Source-audit rules

Add deterministic source checks for the canonical sim path.

Forbidden canonical dependencies after migration:

```text
resolve_owner_supi(...)
owner_identity_map[...] for runtime resolution
scenario.carrying_service for Planning truth
semanticSessionFacts -> ContextFact
candidate.attributes.carryingService from fixture
fixture:hero-world in owner-backed profile model-visible facts
demo-scenario:hero in owner-backed profile model-visible facts
pre-run vg-1 in canonical prepare
```

Allowed:

- the fixture-backed `hero` path;
- tests explicitly named fixture/mechanism;
- bootstrap code that provisions the external owners.

## 26. Failure semantics

### 26.1 Common Provider

```text
RESOLVED
  -> usable exact binding

NOT_FOUND / AMBIGUOUS
  -> planning blocked / clarification-required semantic path

malformed response / endpoint mismatch / protocol failure
  -> integration failure, fail closed

revision/digest mismatch across attempt lookups
  -> identity snapshot failure
```

Do not translate NOT_FOUND into a fake SUPI.

### 26.2 Session activity

```text
FOUND active video
  -> semantic fact available

KNOWN_ABSENT / inactive
  -> definite fact; Skill may decide the protection constraint is not currently
     attached to an active video

UNAVAILABLE / INDETERMINATE / transport failure
  -> unknown; do not assume safe-to-touch
```

The Gate/Context policy must not convert unknown activity into an
`AVOIDS_ACTIVE_SESSION` preference or a deterministic permission.

## 27. Replan semantics

Stable replan feedback remains Runtime-owned.

Identity and owner facts are reacquired only through the same explicit Context
rules.

Do not:

- mutate `owner_identity_map`;
- carry a scenario shortcut into a second attempt;
- infer post-mutation truth from C6 success.

A committed mutation still requires fresh C2 verification.

## 28. Acceptance matrix

### A01 — Common Provider independent process

- start only `tool-common`;
- provider/control listeners READY;
- seed through control;
- lookup through provider;
- prove cross-surface routes are unavailable.

### A02 — identity lookup snapshot

- resolve UE-A/UE-B;
- same mapping revision/digest;
- exact distinct SUPIs;
- persist lookup evidence.

### A03 — identity negative

- NOT_FOUND blocks;
- AMBIGUOUS blocks;
- no manifest fallback.

### A04 — owner-native session activity

- env-5gc-sim C2 returns PDU_SESSION_ACTIVITY for UE-B/10;
- SourceFact provenance valid;
- no Planning Mock activity registry.

### A05 — Observation lineage

- raw trace contains the full request/query/result/normalization/admission chain;
- TUI can navigate it;
- persisted reopen requires no owner.

### A06 — prompt hygiene

- Planning effective request contains active-video semantic value;
- no audit-only provider/Context plumbing unless semantically necessary;
- Request Assembly retains full provenance.

### A07 — canonical live Hero

- real Intent model;
- real Skill Routing model;
- real bounded Planning model;
- Common Provider identity;
- env-5gc-sim C2/C6;
- select additional-session strategy;
- bind the expected bounded additional session;
- Runtime succeeds;
- independent C2 oracle passes.

### A08 — no canonical shortcut

Source/test guard proves canonical sim path cannot succeed when:

- Common Provider is unavailable but manifest still contains aliasToSupi;
- activity C2 is unavailable but manifest still contains video bootstrap input.

Expected result is BLOCKED/FAILED, never fixture fallback.

### A09 — no pre-authored VG id

Canonical prepare contains no `vg-1` pre-run identity and preserves
owner-generated groupId continuation.

### A10 — external lifecycle

Stopping `ca-plan` does not stop either owner process.
Restarting one owner does not silently cause the Host to bind another
generation/revision.

## 29. Migration phases

The detailed mechanical contract for every phase is
`docs/design/owner-backed-demo-migration-implementation.md`.

### P0 — design + characterization

- source-audit the current shortcuts;
- freeze characterization tests before removal.

### P1 — Common Provider read integration + identity trace

- depends on the stable HTTP owner API from `tool-common#6`;
- implement a strict synchronous HTTP/JSON `subject.identity.lookup@v1`
  adapter;
- freeze one identity snapshot with revision/digest fence;
- emit `SUBJECT_IDENTITY_REQUESTED`, `SUBJECT_IDENTITY_RESOLVED`,
  and `IDENTITY_SNAPSHOT_FROZEN` in this phase.

### P2 — env-5gc-sim activity owner

- add separate session-activity world state;
- seed/reset support;
- `PDU_SESSION_ACTIVITY` C2 semantic/schema/SourceFact;
- owner console evidence and contract tests;
- do not overload `PDUSessionState`.

### P3 — owner-backed activity Context + acquisition trace

- add `pdu.session.activity.snapshot` mapping/normalization;
- emit `OBSERVATION_REQUESTED -> OWNER_FACT_REQUESTED ->
  OWNER_FACT_RESULT -> OBSERVATION_NORMALIZED` as part of the owner call;
- add direct read-only Context resolver;
- emit per-fact `CONTEXT_FACT_ADMITTED`;
- remove local sim activity Context injection.

### P4 — remove canonical identity/activity shortcuts

- route all sim C2/C6 identity through the frozen Common Provider snapshot;
- remove canonical runtime dependence on `aliasToSupi`,
  `semanticSessionFacts`, `owner_identity_map`, and activity candidate
  attributes;
- add mandatory no-fallback negative tests.

### P5 — VG identity cleanup

- remove pre-run `vg-1`;
- preserve owner-generated groupId output/continuation lineage.

### P6 — Inspector/TUI evidence navigation

- do not add new acquisition semantics here;
- group the P1/P3 persisted identity/Observation evidence;
- keep live progress concise;
- prove persisted-only reopen while both owners are unavailable.

### P7 — model context minimization

- separate semantic model projection from audit provenance;
- remove trace-only IDs/digests from the effective prompt unless semantically
  required;
- preserve full Request Assembly/source provenance;
- keep digest/equality tests on the effective request.

### P8 — acceptance

- external Common Provider;
- external env-5gc-sim;
- live model Hero;
- full repository gates;
- update #34 with exact repository SHAs, owner fences, run id, and acceptance
  evidence.

## 30. Repository changes expected

### ca-agent-demo

Expected areas:

```text
src/ca_agent_demo/
  host/
  context/
  observation/
  semantic/
  sim/
  trace/
  demo/cli.py

demo/scenarios/
scripts/
tests/
docs/
```

Do not create a generic Provider framework solely for this Demo. Use a narrow
identity-provider adapter and stable typed result.

### tool-common

No semantic redesign is required. The transport dependency is
`tool-common#6`, which replaces historical Provider-side MCP with the
owner-native HTTP/JSON API frozen by ADR-0002.

Planning Mock must consume that published owner API; it must not invent a
temporary identity route or preserve the MCP wire.

### env-5gc-sim

Expected areas:

```text
internal/world/
internal/fixture/
internal/fact/
internal/config/
schemas/v1alpha1/
observability / focused tests
```

The new activity fact must pass the same strict owner contract discipline as
existing C2 facts.

## 30.1 Common Provider and simulator transport rule

Both are backend owners and both use owner-native HTTP/JSON in the target
architecture:

```text
tool-common
  semantic: subject.identity.lookup@v1
  wire:     HTTP/JSON owner API

env-5gc-sim
  semantic: C2 / C6
  wire:     HTTP/JSON owner API
```

They do not need identical domain schemas or route families.

Do not add MCP to `env-5gc-sim` for symmetry. Do not preserve Provider-side MCP
in `tool-common` for symmetry with historical Runtime patterns. MCP
remains at the Agent edge through `tool-mcp-gw`.

## 31. Verification gates

Planning Mock:

```bash
uv sync
uv run python -c "import ca_agent_demo"
uv run python scripts/validate_docs.py
uv run pytest -q
make verify
git diff --check
```

tool-common integration:

```text
go build ./...
go vet ./...
go test ./...
plus independent process provider/control smoke
```

env-5gc-sim:

```text
go build ./...
go vet ./...
go test -count=1 ./...
go test -race ./internal/...
python3 scripts/contract_gate.py
git diff --check
```

Live acceptance must record exact:

- repository SHAs;
- Common Provider revision/digest;
- simulator worldRef/generation/revisions;
- run id;
- model call counts;
- final Runtime result;
- independent owner oracle result.

## 32. Exit condition

The migration is complete only when the canonical sim-backed live Hero has no
runtime-truth dependency on Planning Mock scenario fixtures for either identity
or current 5GC/session activity.

The evidence chain must read:

```text
UE-B
  -> tool-common
  -> 5gc.supi
  -> env-5gc-sim C2
  -> active video SourceFact
  -> normalized ContextFact
  -> selected Root Skill semantics
  -> hard-valid strategy candidates
  -> bounded model selection
  -> deterministic Assembly/Admission
  -> env-5gc-sim C6
  -> fresh env-5gc-sim C2 verification
  -> SUCCESS
```

and the same completed run must remain fully inspectable after both owner
processes are unavailable.
