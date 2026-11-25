# Architecture baseline — Python Core, unified Plugin, optional Assurance

**Status:** target architecture for ca-agent-next; implementation NOT_STARTED.
**Audit source:** ca-agent-demo main 57e277ff9094dad93543df46910a12a1dbbaf560 plus open PR #246 / #249 reviewed on 2026-11-25.
**Scope:** Demo-level mechanism implementation, not Production Qualification.

## 1. Repository evolution and language

~~~text
ca-agent-demo (primary source: existing Python mechanisms + tests)
       |
       | selective reuse, simplification and redesign
       v
ca-agent-next (new Python Agent Core / Host / Runtime)
       |
       | acceptance complete, promotion review
       v
ca-agent (stable implementation target; not source for this redesign)
~~~

- Agent Core, Host, Agent Model Loop, Skill Importer, Skill Resolver and Runtime in next are Python.
- Plugins are independent processes. Go is appropriate for OpenAMSM and Tool Plugin implementations; it is not the Agent Core language.
- ca-skill-compiler, ca-client-tools, ca-skills and Plugin repositories remain independent package owners. Do not copy their implementations into next.

## 2. Skill package and execution modes

Every published Skill package has one required Agent-facing `SKILL.md`. Deterministic execution is optional and is provided only by a Compiler-generated, published Assurance Artifact.

The authoring repository may contain `assurance/contract.yaml`, `procedure.yaml` and `predicates.yaml`. Those source files are Compiler inputs; they are not Agent runtime inputs and are not required in the published runtime package.

| Published package shape | LLM-guided | Deterministic |
|---|---:|---:|
| SKILL.md-only package, no compiled Assurance Artifact | Yes | No |
| SKILL.md + valid compiled Assurance Artifact | Yes | Yes |
| Package declares Assurance but compiled Artifact is absent, invalid or incompatible | Import fails | Import fails |

Normative rules:

1. SKILL.md is required for every published Skill and contains the Agent-facing description, usage guidance and natural-language applicability.
2. Assurance is optional in the authoring source. Its source contract remains inside `assurance/`; it is compiled and verified before publication.
3. The Agent accepts only the published compiled Assurance Artifact. It never imports Assurance source YAML, invokes a Compiler or compiles a Skill.
4. A published package without a compiled Assurance Artifact is LLM-guided only. A package that declares Assurance but has missing/invalid compiled files or unresolved dependencies fails import; it is never silently downgraded.
5. The Importer performs only basic structural checks and local dependency resolution. The Demo has no separate Skill Admission, approval, trust evaluation or production authorization mechanism.
6. Do not add supportedModes, a second LLM Contract, a separate applicability.yaml, activation.yaml, constraint.yaml or another Skill descriptor.
7. predicates.yaml is for execution-time business predicates only. It does not select Skills.

## 3. Published Skill import lifecycle

Compiler and Agent Importer are separate processes and separate lifecycle stages. Compiler belongs to the external authoring/release toolchain; it is not embedded in Agent and is never invoked by Agent.

| Published input | Agent import path | Compiler behavior in Agent |
|---|---|---|
| SKILL.md-only package | Parse basic metadata, check safe paths/references, import guidance | None |
| SKILL.md + compiled Assurance Artifact | Check supported Artifact format/version, required files and references; parse CEL/type data; resolve local Tool/Capability dependencies | None |
| Assurance source YAML without a compiled Artifact | Not a supported runtime package; report missing published Artifact | Never compile or fall back |

External publication pipeline:

~~~text
Authoring source (SKILL.md + optional assurance/*.yaml)
   |
   v
External CA-SL Compiler: Check / Build
   |
   v
Compiler Verify
   |
   v
Publish runtime Skill bundle (SKILL.md + compiled Artifact + optional references)
~~~

Agent import pipeline:

~~~text
Published Skill bundle
   |
   v
Skill Importer
   |
   +--> basic format / manifest / required-file / path / reference checks
   |
   +--> deserialize compiled CEL and type data (if Assurance exists)
   |
   +--> resolve declared Tool / Capability dependencies against installed Plugins
   |
   v
Build candidate SkillCatalog generation
   |
   v
Atomically publish active generation
~~~

Additional rules:

- Compiler owns CA-SL parsing, static semantics, linking, Build and Verify before publication. Agent does not call its CLI/API, copy its code or reproduce its validation.
- The Agent Importer does not run Compiler Inspect/Verify and does not perform a separate Artifact Admission. It only checks that the published bundle is structurally readable and that its local dependencies can be resolved.
- Required files/references missing, unsupported manifest/Artifact format, unsafe paths, malformed CEL/type data or unresolved Tool/Capability dependencies cause a clear import error.
- The Agent does not import or execute Assurance source YAML and does not automatically compile or repair a package.
- Editing SKILL.md updates Agent-facing guidance. Editing Assurance source happens in the external authoring/release workflow; a new compiled Artifact must be published before the Agent imports the update.
- An individual LLM Action proposal is not Skill source and does not invoke Compiler.

## 4. Skill-first selection and optional contract.when

Every fresh business request binds a Skill before execution. Exact continuations are resolved against the original pending Run before fresh Skill selection.

### 4.1 Selection declarations

- A Skill with Assurance may declare the optional top-level contract.yaml field when.
- when is a pure CEL boolean used only during Skill selection.
- Its input environment is the normalized Event metadata, including event.type, and the Event payload exposed as input.
- The Event Plugin validates the normalized payload against its Event Schema. If `when` reads any `input` member, the Assurance Contract MUST declare `requestSchema`; the Compiler statically checks those fields against that Schema. Host validates the same normalized input against a declared candidate `requestSchema` before evaluating `when`.
- when may inspect only the declared Event metadata and input fields. It cannot query Tools, inspect runtime Observations, read mutable Host state or perform side effects.
- SKILL.md natural-language usage guidance is used for semantic selection of unguarded Skills. It does not gain a second CEL field.
- predicates.yaml remains exclusively for execution-time business facts.

Example:

~~~yaml
# assurance/contract.yaml
when: 'event.type == "nsmf.create-sm-context" && input.requestType == 1'
~~~

### 4.2 Candidate resolution

1. Validate and deduplicate the Event envelope/payload. Resolve an exact continuation first; a continuation never re-enters fresh Skill selection.
2. Pin the active in-memory SkillCatalog generation for this fresh Event. A package with invalid Assurance was rejected at import and is not a candidate; do not scan package directories on this path.
3. Evaluate the precompiled `when` program for each eligible Assurance Skill that declares it, using this Event's current values. A true result is an explicit match. False excludes that Skill. A runtime evaluation error fails closed, excludes that Skill and records a diagnostic. A statically invalid expression prevents Compiler publication.
4. If one explicit true match exists, select it without an LLM call. If multiple explicit true matches exist, the LLM may disambiguate only within that exact set; validate the returned Skill identity.
5. If there are no explicit true matches, form the unguarded semantic candidate set from Skills without when. This includes SKILL.md-only Skills and valid Assurance Skills whose contract omits when. Use their SKILL.md descriptions for semantic selection; the LLM cannot invent a Skill outside the imported set.
6. If the applicable candidate set is empty, stop or request the missing information. A Skill whose when evaluated false or errored is not reintroduced as an unguarded candidate.
7. Bind the exact selected Skill package and, when Assurance exists, its exact published Artifact and Capability requirements.
8. Select Deterministic or LLM-guided mode only after Skill binding.

There is no Event-to-Skill table, Event-to-mode table, business-contract package registry or domain-specific Host route. The Plugin does not name a Skill.

### 4.3 Core-owned in-memory SkillCatalog

SkillCatalog is a Python Agent Core / Host mechanism. It is deliberately separate from Plugin Manager: Plugin Manager owns Plugin lifecycle, IPC and Event/Delivery/Tool extension dispatch; it neither owns Skill assets nor performs Skill selection.

The Catalog is an immutable, process-local snapshot built at startup and on an explicit Skill import/update operation. It is the active read model for Skill discovery and selection; published package files remain the source of truth, not the Catalog itself.

Each Catalog entry retains, as applicable:

- Skill identity and published package reference;
- the full imported SKILL.md text plus lightweight candidate metadata derived from it;
- Assurance presence and the published compiled Artifact reference;
- the deserialized `when` program and its CEL profile/type environment;
- the Request Schema/type information needed by selection;
- declared Capability requirements and resolved local callable references.

Residency and loading rules:

1. Read and parse SKILL.md once when importing/updating a published package. Keep its full text in memory. Semantic selection uses bounded candidate metadata derived from this in-memory content; after selection, provide the full SKILL.md text from memory, not by rereading disk.
2. For a published Assurance Artifact, parse its supported manifest and required references, then deserialize the CheckedExpr and type descriptors once. The Agent does not compile or statically re-check the source CEL expression.
3. Every fresh Event evaluates the cached program against that Event's current `event.type` and `input`. Do not cache a prior Event's true/false/error result: two Events for the same Skill may have different payloads. Duplicate Event handling and exact continuation resolution happen before fresh selection, so a replay/continuation does not cause a new evaluation.
4. Register SKILL.md-only Skills in the same Catalog. They have no `when` program and remain semantic candidates when the explicit-match set is empty.
5. Keep small Skill metadata, SKILL.md text, CEL programs, Schema/type information and resolved Artifact references resident. Load `references/` and large knowledge assets only when the selected Skill needs them. A large Procedure payload may be materialized after selection and cached for that Catalog generation; it must not trigger per-Event package scans.
6. Build a candidate generation off-path. An explicit update activates it with one atomic snapshot swap only after the requested package's basic structure, Artifact references and local dependencies are checked. If the update fails, retain the previous active generation. This is ordinary import validation, not a separate admission stage.
7. A fresh Invocation pins the Catalog generation used for selection. Its Skill text, Artifact and Capability/callable bindings remain from that generation even after a newer generation is activated. Retain an old generation while any Invocation still references it, then reclaim it.
8. Use a simple process-local monotonically increasing generation number for this Demo. Do not add a distributed cache, Redis, content digest, package signature or another integrity mechanism.

The Event hot path is therefore: validate/deduplicate Event → resolve exact continuation (if any) → pin active Catalog generation for a fresh Event → evaluate in-memory `when` programs → perform semantic selection only among unguarded in-memory candidates if there is no explicit match → bind Skill → select execution mode. It does not read SKILL.md, scan Skill directories or invoke Compiler.

### 4.4 Compiler-to-Runtime `when` Artifact boundary

CA-SL v1alpha5 Appendix M defines the author expression and static typing rules. `event.type` is string; `input` is typed from the exact `Contract.requestSchema`; accessing an input member without `requestSchema` is `CEL_INVALID`. The independent Compiler owns G.4 static validation and checked-program generation; Python Resolver owns per-Event evaluation.

The Compiler's existing published `compiler-artifact/v1alpha5` contract is frozen and must remain byte-identical. The separate Development Artifact v1alpha1 is explicitly `NOT_ADMITTED` and contains development-only Host Admission requirements; it is not a runtime Skill package and must not be imported by the Agent.

The proposed work is tracked by [ca-skill-compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61): the Compiler must define a new versioned **published runtime Artifact** contract capable of carrying the checked `when` program. Its exact Artifact API version is Compiler-owned and must not be confused with the CA-SL language version: `languageTarget` remains `connectionagent.io/v1alpha5`. Do not mutate the frozen Artifact v1alpha5 contract or use Development Artifact v1alpha1/v1alpha2 as the runtime package.

The preferred interchange is a standard `google.api.expr.CheckedExpr` wrapped in `google.protobuf.Any`, plus a `google.protobuf.FileDescriptorSet` for the exact Event and Request Schema type environment. Go `cel-go` produces the checked expression; Python `cel-expr-python` deserializes and evaluates the same program. This is a target, not a PASS claim: Compiler must first prove Go-to-Python round-trip and G.4 optional/null semantics with real fixtures. Do not substitute `DynType`, a Python-only parser, a custom CEL interpreter or a per-Event Compiler subprocess.

At runtime the Agent only checks basic format/required-file/reference structure, deserializes the checked program and resolves local Tool/Capability dependencies. It does not run Compiler Verify, perform Skill Admission or make a trust/production-authorization decision.

See [技能目录与编译器运行时接口设计说明书](集成设计/技能目录与编译器运行时接口设计说明书.md) for the detailed contract, PoC and stop conditions.

## 5. One extension mechanism: Plugin

A Plugin is the generic extension/package/process unit managed by one Python Plugin Manager. One Plugin process may expose one or more extension kinds.

| Extension | Direction | Responsibility |
|---|---|---|
| event.ingress | Plugin → Host | Publish a normalized Event |
| event.delivery | Host → Plugin | Deliver a structured response to the originating protocol |
| tools | Host → Plugin | Export callable Tool operations |

A Tool is a callable operation exported by a Plugin's `tools` extension, not a process, package/import unit, manager or Runtime. A Tool Plugin is a Plugin that exposes the `tools` extension and may export one or more Tool operations. A Plugin may expose Event ingress, Delivery and Tools together. All Tool operations are discovered and dispatched through the same Plugin Manager and their owning Interface Package; there is no separate Tool registry or lifecycle.

### 5.1 One Plugin Manager and IPC

- One Python Plugin Manager owns process start/stop, handshake, IPC, correlation, extension discovery and dispatch.
- One Plugin IPC envelope and one process lifecycle serve all extension kinds.
- Event, Tool and Delivery are extension methods, not separate managers or protocols.
- The existing ca-client-tools.provider/v2 process may initially be adapted by a Tool-extension driver inside the unified Plugin Manager. This is a migration adapter, not a permanent Provider Manager.
- Do not create a second Tool registry, Provider Manager, authorization path or Runtime.
- The Plugin Manager transports calls. It does not select Skills, authorize business actions or decide whether an Owner mutation committed.

Native package format and the minimal Demo IPC are defined in [Plugin Package v1alpha1](plugin-package.md).

### 5.2 Extension ownership

| Repository / package | Extension role | Responsibility |
|---|---|---|
| ca-openamsm-plugin | Event ingress + delivery | SBI HTTP/2 ingress, JSON/multipart parsing, Content-ID association, normalized Event publication and SBI response encoding/delivery; preserve original N1/N2 bytes |
| ca-client-tools | Tool Plugin | Existing OpenAMSM callable operations and, when published, protocol Codec Tool operations using its shared Go codec packages |
| Echo Example Plugin | Combined | Minimal Event ingress/delivery and one or more Tools |

`ca-openamsm-plugin` and `ca-client-tools` remain independently owned projects. The Event Plugin is not a Tool Provider or Owner client. The Tool Plugin does not own SBI ingress, Skill selection or Runtime authorization. Neither Plugin chooses the Skill.

The Event Plugin performs the protocol work required to parse and normalize the SBI request, including multipart and Content-ID handling. It may extract only the minimum NAS discriminator needed to normalize an Event when one SBI operation is shared by multiple business cases (for example, distinguishing Modify from UE-requested Release on UpdateSMContext). This is protocol-to-Event classification, not Skill selection or full business decoding. The selected Skill is still chosen by the Host Resolver. Deeper NAS/NGAP fields remain on-demand through a Codec Tool in the existing `tools` extension.

### 5.3 On-demand protocol Codec Tools

- Add Codec operations to the existing `ca-client-tools` Tool Plugin through its canonical Tool Interface Package; do not create a separate Codec Manager, Tool registry or new Plugin system for this Demo.
- The Tool Plugin may expose related operations such as NAS/NGAP/PFCP Decode and Encode, but only for the exact protocol/message subset implemented and tested by its shared Go codec packages.
- A Codec Tool accepts a Host-owned artifact reference (or a structured message when appropriate) and returns either a structured JSON projection or an output artifact reference.
- The selected Skill decides whether decoding is needed. If it is not, it passes the original artifact reference to the relevant business Tool without invoking Codec.
- Decode is read-only with respect to the original artifact. The decoded projection never replaces or silently re-encodes the original N1/N2 bytes.
- Codec Tools use the same Runtime Action Boundary, Capability authorization, Plugin Manager and Provider adapter as every other Tool. No direct Skill-to-Worker call and no Host-side duplicate codec.
- The current `ca-client-tools/protocol/nas5gsm` library is a narrow pure codec package, not yet an Agent-callable Tool. The Tool operation and Schema must be exported by the canonical Interface Package before Skills can invoke it.

## 6. Contract and schema ownership

| Material | Owner | Rule |
|---|---|---|
| Plugin identity, process and extension declarations | Plugin package | One YAML manifest |
| Normalized Event type and Event payload Schema | Event Plugin package | No business Contract Package and no Skill ID |
| Agent-facing usage and semantic guidance | SKILL.md | Required for every Skill |
| Goal, request/context requirements, dependencies, Capability Grants, when | assurance/contract.yaml | Present only for deterministic-capable Skills |
| Procedure graph and execution predicates | Assurance source | CA-SL Compiler validates them |
| Tool IDs, input/output Schemas, Effects, Capability membership and Owner outcome contracts | Tool Interface Package | Existing canonical authority; do not duplicate ToolCatalog |
| Tool implementation and private runtime binding | Tool Plugin | Executable implementation only |
| Runtime authorization, Outcomes and Evidence | Python Runtime | One common boundary for both modes |
| 3GPP SBI protocol Schema | Applicable 3GPP OpenAPI | Reuse the standard request/response and multipart definitions; do not invent a replacement SBI Schema |
| NAS / NGAP protocol Schema | Applicable 3GPP TS definitions, including ASN.1 where applicable | Use standard protocol definitions for Codec input/output; not every protocol has an official YAML |
| Codec Tool input/output Schema | Tool Interface Package | Defines the callable operation and structured result/artifact-reference contract |
| Skill requestSchema | Skill Assurance | Describes only the business input the Skill actually consumes; it need not duplicate the complete protocol Schema |

Rules:

- Do not add Domain Contract Package, TaskContract Package or another business-contract layer.
- The Event Plugin declares event.type and its normalized payload Schema. It does not publish a business Goal or a Skill mapping.
- The normalized Event payload is the input offered to Skill selection. The selected Skill's requestSchema, if present, must accept it. Do not invent a generic business projection layer.
- The Skill Contract is part of Assurance, not a global registry and not a required file for ordinary Skills.
- Tool Interface Package remains the sole authority for callable contracts. Plugin manifests reference it; they do not duplicate its Tool definitions.

## 7. Runtime and Action boundary

| Component | Owns | Does not own |
|---|---|---|
| Python Host / Agent | Model loop, reasoning, Skill discovery/selection, Context assembly, Skill import orchestration | Direct Tool invocation or authoritative business truth |
| SkillCatalog | Core-owned immutable in-memory Skill index, cached guidance/selection programs and Catalog generations | Plugin lifecycle, Tool dispatch or Owner truth |
| Skill | SKILL.md guidance; optional Assurance contract and Procedure | Plugin lifecycle or Tool implementation |
| External CA-SL Compiler | Assurance source validation, linking, Build and Verify before publication | Agent Runtime, Skill selection, Tool execution or Skill Admission |
| Python Runtime | Run state, Action validation, declared Capability/callable scope checks, Tool dispatch, Outcomes/Evidence, Wait/Resume/Reconcile | Compiler, Skill Admission, trust evaluation or LLM Model Loop |
| Deterministic Procedure Engine | Advance a published compiled Procedure and derive the next Action | Independent Tool dispatch or Capability scope checks |
| Plugin Manager | Process lifecycle, IPC and extension dispatch | Skill selection, authorization or Owner truth |
| Tool Plugin | Execute the requested Tool and return its result/receipt | Granting itself permission or inventing Owner outcomes |
| Owner | Authoritative external business state and commit result | Agent reasoning |

### 7.1 Three distinct flows

**A. Import SKILL.md-only published package**

~~~text
SKILL.md-only published package
   |
   v
Skill Importer: basic structure / path / reference checks
   |
   v
Build candidate Catalog generation
   |
   v
Atomically publish active generation
~~~

No Assurance and no Compiler invocation.

**B. Publish a Skill with Assurance (external to Agent)**

~~~text
SKILL.md + assurance source YAML (authoring repository)
   |
   v
External CA-SL Compiler: Check / Build
   |
   v
Compiler Verify
   |
   v
Publish SKILL.md + compiled runtime Artifact
~~~

The Agent is not part of this build/release path and never receives or compiles the Assurance source.

**C. Import a published compiled Skill Artifact**

~~~text
SKILL.md + published compiled Assurance Artifact
   |
   v
Skill Importer
   |
   +--> basic format / manifest / required-file / path / reference checks
   |
   +--> deserialize CEL / type data
   |
   +--> resolve local Tool / Capability dependencies
   |
   v
Build candidate SkillCatalog generation
   |
   v
Atomically publish active generation
~~~

No Compiler invocation, Compiler Verify command or Skill Admission stage. Missing/invalid files or unresolved dependencies fail import with a diagnostic.

**D. LLM Action vs Skill Authoring**

- An LLM-proposed individual Action is validated by the Runtime Action Boundary. It is not compiled into a temporary Procedure.
- An LLM-created or LLM-edited SKILL.md-only package follows the ordinary no-Assurance import path.
- An LLM-created or LLM-edited Assurance source is not executable as-is; it must be compiled and published by the external toolchain before Agent import.

### 7.2 Shared Action path

- Deterministic mode derives an Action from the published compiled Procedure.
- LLM-guided mode proposes an Action from Skill-scoped Context.
- Both submit the same conceptual RuntimeActionRequest to the same Runtime Action Boundary.
- Runtime validates the Action Schema, selected Skill scope, declared Capability/callable membership and Effect before dispatching through the Plugin Manager. This is an invocation boundary, not Skill Admission or production authorization.
- LLM cannot call Plugins directly, widen Capability grants, fabricate Evidence or declare an Owner mutation COMMITTED.
- READ results remain Observations with provenance. MUTATION results follow their Owner Receipt/Commit Proof contract; UNKNOWN remains UNKNOWN.

## 8. End-to-end flow

~~~mermaid
flowchart TB
  SOURCE[Assurance source in authoring repository] --> COMP[External CA-SL Compiler: Check / Build]
  COMP --> VERIFY[Compiler Verify]
  VERIFY --> RELEASE[Publish SKILL.md + compiled runtime Artifact]
  SKILLONLY[SKILL.md-only package] --> IMPORT[Agent Skill Importer]
  RELEASE --> IMPORT
  IMPORT --> CHECK[Basic format / file / path / reference checks]
  CHECK --> CEL[Deserialize CEL / type data and resolve local Tool dependencies]
  CEL --> CANDIDATE[Build candidate SkillCatalog generation]
  CANDIDATE --> SWAP[Atomic activate immutable Catalog generation]

  EXT[External Event / User Task] --> EP[Event Plugin]
  EP --> PM[One Python Plugin Manager]
  PM --> HOST[Python Host / Agent]
  HOST --> CONT{Exact continuation?}
  CONT -->|yes| RESUME[Resume original Run with pinned generation]
  CONT -->|no| PIN[Pin active SkillCatalog generation]
  PIN --> RESOLVER[Skill Resolver: in-memory only]
  RESOLVER --> WHEN{Precompiled Assurance when matches?}
  WHEN -->|explicit match| SELECT[Bind exact Skill]
  WHEN -->|no explicit match| SEMANTIC[Semantic candidates from cached SKILL.md metadata]
  SEMANTIC --> SELECT
  SELECT --> GUIDANCELOAD[Use full SKILL.md from memory]
  GUIDANCELOAD --> MODE{Execution mode}
  MODE -->|Deterministic| PROC[Published compiled Procedure Artifact]
  MODE -->|LLM-guided| LOOP[LLM Model Loop]
  PROC --> ACTION[RuntimeActionRequest]
  LOOP --> ACTION
  ACTION --> RT[One Runtime Action Boundary]
  RESUME --> RT
  RT --> PM
  PM --> TOOL[Tool Plugin]
  TOOL --> OWNER[Owner]
  OWNER --> RESULT[Tool Result / Receipt]
  RESULT --> RT
  RT --> RESPONSE[Structured Host Response]
  RESPONSE --> PM
  PM --> EP
~~~

The diagram describes the target flow, not current implementation status. A published Skill must pass basic import checks and have its local dependencies resolved before it enters the Catalog. This Demo has no separate Skill Admission mechanism. A Skill that declares Assurance but lacks a valid compiled Artifact is an import error, never a fallback LLM-only Skill.

## 9. What is reused from ca-agent-demo

- Reuse selected Python Agent/model adapter, Formal Resolver primitives, Context, Tool contract validation, Outcome/Evidence and Run mechanisms after dependency/test review.
- Replace current deployment-owned structuredEventRoutes / Root Routing with Skill package selection using Assurance contract.when plus SKILL.md semantic candidates.
- Do not copy the 5GC-specific Root routing profile or Nsmf orchestration into Core.
- Use the generic Provider loader from PR #246 as implementation evidence, but absorb process management into the one Plugin Manager.
- Use PR #249 Event/Delivery IPC ideas selectively; its Agent-default / Skill-optional execution model is not the target.
- Do not reuse MockCompiler as the real Compiler or assume MockRuntime is the final Runtime.

## 10. External reusable projects and known implementation gap

- ca-skill-compiler v2.1.0: independent Go Compiler. Python consumes its CLI/API; do not copy its source or reimplement semantics.
- ca-client-tools v1.2.0: independent Go Tool Plugin and Interface Package. Adapt provider/v2 behind the unified Plugin Manager initially.
- ca-skills: canonical CA-SL Skill sources and language specification. Same-version v1alpha5 refresh proposal [PR #88](https://github.com/odango-chan/ca-skills/pull/88) adds optional Assurance and contract.when; Compiler support remains a separate dependency gate.
- ca-openamsm-plugin: independent Go Event Plugin. Align its contract before implementation.
- **Known gate:** ca-skills PR #88 is OPEN; Compiler implementation is tracked by [Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61). Compiler v2.1.0 does not yet establish refreshed `contract.when` support or Python CheckedExpr interoperability. SKILL.md-only packages import directly. Assurance Skills require a new versioned published runtime Artifact contract; the Agent never compiles or runs Compiler Verify. See [the Chinese integration design](集成设计/技能目录与编译器运行时接口设计说明书.md).

## 11. Demo-level non-goals

Do not add:

- extra SHA-256 hashing for Plugin packages or Event snapshots;
- package/file integrity frameworks, package signatures or a Trust Registry;
- Domain Contract Packages, TaskContract Packages or a second Skill descriptor;
- separate Provider Manager, Tool registry, Runtime or authorization path;
- legacy format compatibility or automatic migration;
- Marketplace, installer, automatic package downloads, filesystem watchers or generic Plugin hot reload. Explicit Skill import/update with atomic SkillCatalog generation activation is allowed and required;
- Skill Admission, approval workflows, Owner Trust, package signatures, Trust Registry, production authorization or qualification machinery;
- production HA, complex multi-tenant governance, distributed Event Bus or broad DFX.

Keep basic YAML/Schema/version/reference validation, path containment, clear errors, explicit process configuration, minimal correlation and runnable acceptance Examples. Existing Compiler/Interface Package identities remain governed by their owning contracts; do not add a second Host-side digest or integrity system.


## 12. OpenAMSM integration boundary and current dependencies

This section makes the target boundary explicit for the joint ca-agent-next / ca-openamsm-plugin implementation. The authoritative native Plugin Package and IPC contract is [Plugin Package v1alpha1](plugin-package.md); binary handoff is [Plugin Artifact Handoff](plugin-artifact-handoff.md). The corresponding OpenAMSM adapter proposal is [ca-openamsm-plugin PR #1](https://github.com/odango-chan/ca-openamsm-plugin/pull/1), which must follow this contract rather than define a parallel one.

### 12.1 Skill-first OpenAMSM flow

Every fresh OpenAMSM business Event binds a Skill before execution. The Event Plugin publishes only the normalized SBI operation, validated input and artifact references. It never selects or names a Skill.

The existing CA-SL packages are the business source:

- establish-pdu-session-mas;
- modify-pdu-session-mas;
- release-pdu-session-mas.

Their optional assurance/contract.yaml.when fields are the only formal selectors. Create, Modify and UE-requested Release must be distinguished from normalized Event metadata and validated request fields. In particular, UE-requested PDU Session Release must not be confused with AMF/network-initiated ReleaseSMContext. The exact SBI operation, NAS discriminator and Event Schema field mapping must be verified against the current OpenAMSM OpenAPI and existing Host ingress before implementation; do not guess a route or duplicate business rules in the Plugin.

The Host resolves the Skill, then derives the mode from Assurance presence/validity. No Assurance means LLM-guided only; valid Assurance enables Deterministic or LLM-guided; invalid Assurance is an import failure. Both modes use the same Runtime Action Boundary.

### 12.2 Ownership

| Concern | Owner |
|---|---|
| Nsmf/Namf HTTP/2 listener, JSON/multipart and Content-ID parsing, normalized Event publication and SBI response encoding; preserve original N1/N2 bytes | ca-openamsm-plugin |
| Plugin lifecycle, common IPC, Event Schema validation and dispatch | One Python Plugin Manager in ca-agent-next |
| Skill import, when evaluation, Skill selection and mode derivation | Python Host / Skill Resolver |
| Run identity, continuation, retry/replay, response obligations and resource/alias mapping | Python Host / Runtime |
| N1/N2 staging, ArtifactStore custody, Run association and authorization | Python Host / Runtime |
| Callable IDs, IO Schemas, Effects, Capability membership, private bindings, Owner calls and published Codec Tool operations | ca-client-tools |
| SM Context identity, actual business state and authoritative mutation result | OpenAMSM Owner / SMF |
| CA-SL syntax and compiled Artifact | ca-skills specification + ca-skill-compiler |

ca-openamsm-plugin is not a Tool Provider, Owner client, Skill Resolver, RunStore, Runtime or Artifact database. ca-client-tools is represented as the tools extension behind the same Plugin Manager. Its current provider/v2 process protocol is adapted inside that manager; it does not create a second Provider Manager.

### 12.3 Binary handoff

N1/N2 bytes move through the Host-owned local staging and ArtifactStore contract. They are not Base64-encoded in IPC and are not persisted by the Plugin. Host imports inbound files before accepting an Event, returns opaque artifactRefs, authorizes each Runtime/Tool use, stages outbound bytes for a specific response obligation and cleans temporary files. No extra Plugin/Event/Artifact SHA-256 or content digest is introduced.

The artifact handoff is transport/custody, not a mandatory decode step. A Skill may pass an artifactRef directly to an OpenAMSM business Tool. When it needs protocol fields, it invokes a Codec Tool exposed by `ca-client-tools` through the same Runtime Action Boundary. The Tool Provider resolves the invocation-scoped artifact through the existing Host artifact channel and returns a structured JSON projection. The original artifact remains unchanged and available for forwarding or response composition. Codec Encode, when needed, returns an output artifact for the Host to stage for the originating Event Plugin.

The current `protocol/nas5gsm` package is not itself an Agent-callable Tool. Only merged/released Codec operations with declared Interface Package Schemas and qualified message coverage may be used by Skills.

### 12.4 Dependency and evidence status — 2026-11-25

| Dependency / evidence | Current state | Consequence |
|---|---|---|
| ca-skills PR #88 | OPEN; same-identifier CA-SL v1alpha5 refresh proposes optional Assurance and contract.when | Normative language refresh is not merged. Keep the dependency explicit. |
| ca-skill-compiler v2.1.0 | Released for CA-SL v1alpha5; support for the proposed contract.when field is not established by current evidence | Deterministic Assurance source import is blocked until the Compiler owner verifies/implements the refreshed field. SKILL.md-only import is Host behavior and does not require Compiler support. |
| ca-client-tools v1.2.0 | Released Tool Interface Package and Provider runtime bindings; existing process protocol is provider/v2 | Reuse through the single Plugin Manager's Tool adapter. Do not copy the Tool catalog or Owner bindings into the Event Plugin. |
| ca-client-tools PR #39 | OPEN; Phase B final pass, Phase C consumer migration not started | Codec is not yet a merged/released dependency. NAS has 8 qualified message types; N2 has 7 qualified roots within evidenced scope; NGAP has 0 CA-qualified full PDUs. |
| ca-agent-demo PR #246 | OPEN; G5 synthetic Owner E2E reports 22 passing tests; real isolated Scheme C G6 is NOT_RUN/BLOCKED and G7 is PARTIAL | Reuse generic Provider implementation evidence selectively; do not treat synthetic G5 as real OpenAMSM E2E. |
| ca-openamsm-plugin PR #1 | OPEN/DRAFT; design only | Align the proposal with this contract before Go implementation. |

The ca-client-tools Provider's existing Host-to-Provider artifact channel has acceptance-fixture evidence, but the production catalog does not yet prove a generic real-NF SBI multipart binding. Keep real OpenAMSM binary/multipart Provider consumption as a separate E2E gate; do not infer it from the Plugin-to-Host staging contract.

No Production Qualification is claimed.
