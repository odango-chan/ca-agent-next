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

Every Skill package has one required Agent-facing SKILL.md. Deterministic execution is optional and is introduced only by the presence of a valid assurance directory.

~~~text
skills/<skill-name>/
├── SKILL.md
├── assurance/                 # Optional; enables Deterministic execution
│   ├── contract.yaml
│   ├── procedure.yaml
│   └── predicates.yaml        # Required; empty PredicateSet when unused
├── schemas/                   # Skill-owned request and other schemas
├── scripts/                   # Skill-owned deterministic scripts
└── references/                # Optional Agent knowledge material
~~~

| Package shape | LLM-guided | Deterministic |
|---|---:|---:|
| SKILL.md only; no assurance directory | Yes | No |
| SKILL.md + valid assurance source | Yes | Yes |
| SKILL.md + imported compiled Assurance Artifact | Yes | Yes |
| Assurance directory exists but is incomplete or invalid | Import fails | Import fails |

Normative rules:

1. SKILL.md is required for every Skill and contains the Agent-facing description, usage guidance and natural-language applicability.
2. The assurance directory is optional. Its contract.yaml belongs inside assurance; it is not a mandatory file for every Skill.
3. A valid Assurance enables both execution modes. The selected mode is chosen after exact Skill selection.
4. If assurance is absent, the Skill is LLM-guided only. The Agent follows SKILL.md and the common Runtime Action Boundary.
5. If assurance is present but malformed, incomplete, unsupported or fails compilation/admission, reject the Skill import. Never silently downgrade it to SKILL.md-only.
6. Do not add supportedModes, a second LLM Contract, a separate applicability.yaml, activation.yaml, constraint.yaml or another Skill descriptor.
7. predicates.yaml is for execution-time business predicates only. It does not select Skills.

## 3. Skill source and Artifact import lifecycle

The Skill Importer recognizes three inputs. It does not implement a second Compiler or package manager.

| Input | Import path | Compiler behavior |
|---|---|---|
| SKILL.md-only source package | Parse basic Skill metadata and import Agent guidance | No Compiler invocation |
| Source package with assurance/ | Validate package shape, invoke CA-SL Compiler, then inspect/admit the generated Artifact | Automatically compile before admission |
| Already compiled Skill Artifact | Inspect, verify and admit the supplied Artifact | Do not rebuild or recompile |

Additional rules:

- The Compiler owns CA-SL parsing, semantic checks, linking and Artifact generation. Python invokes the released Compiler interface; it must not reimplement Compiler semantics.
- Source with Assurance is not executable until the Compiler succeeds and Host admission succeeds.
- An imported compiled Artifact is not recompiled. The Host uses the Compiler's Inspect/Verify contract and then performs its own deployment/Capability admission.
- A failed build, verify or admission is a hard error. Do not strip assurance files, ignore an unknown field or fall back to LLM-guided mode.
- Editing only SKILL.md updates the Agent-facing guidance; it does not require rebuilding an unchanged Assurance Artifact.
- Editing contract.yaml, procedure.yaml, predicates.yaml or another Assurance source dependency triggers a new Compiler build and Artifact admission.
- LLM-created or LLM-edited Skill source follows this same import path. Creating a source file does not itself make it executable.
- An individual LLM Action proposal is not Skill source and does not invoke the Compiler.

## 4. Skill-first selection and optional contract.when

Every fresh business request binds a Skill before execution. Exact continuations are resolved against the original pending Run before fresh Skill selection.

### 4.1 Selection declarations

- A Skill with Assurance may declare the optional top-level contract.yaml field when.
- when is a pure CEL boolean used only during Skill selection.
- Its input environment is the normalized Event metadata, including event.type, and the Event payload exposed as input.
- The Event Plugin validates the normalized payload against its Event Schema. A candidate Assurance requestSchema, when declared, must also accept the same input before its when expression is evaluated.
- when may inspect only the declared Event metadata and input fields. It cannot query Tools, inspect runtime Observations, read mutable Host state or perform side effects.
- SKILL.md natural-language usage guidance is used for semantic selection of unguarded Skills. It does not gain a second CEL field.
- predicates.yaml remains exclusively for execution-time business facts.

Example:

~~~yaml
# assurance/contract.yaml
when: 'event.type == "nsmf.create-sm-context" && input.requestType == 1'
~~~

### 4.2 Candidate resolution

1. Validate the Event envelope and payload. Resolve an exact continuation first; a continuation never re-enters fresh Skill selection.
2. Load available Skill packages. A package with invalid Assurance is rejected at import and is not a candidate.
3. Evaluate when for each imported Assurance Skill that declares it. A true result is an explicit match. False excludes that Skill. A runtime evaluation error fails closed, excludes the Skill and records a diagnostic. A statically invalid expression prevents Assurance compilation/admission.
4. If one explicit true match exists, select it without an LLM call. If multiple explicit true matches exist, the LLM may disambiguate only within that exact set; validate the returned Skill identity.
5. If there are no explicit true matches, form the unguarded semantic candidate set from Skills without when. This includes SKILL.md-only Skills and valid Assurance Skills whose contract omits when. Use their SKILL.md descriptions for semantic selection; the LLM cannot invent a Skill outside the imported set.
6. If the applicable candidate set is empty, stop or request the missing information. A Skill whose when evaluated false or errored is not reintroduced as an unguarded candidate.
7. Bind the exact selected Skill package and, when Assurance exists, its exact admitted Artifact and Capability requirements.
8. Select Deterministic or LLM-guided mode only after Skill binding.

There is no Event-to-Skill table, Event-to-mode table, business-contract package registry or domain-specific Host route. The Plugin does not name a Skill.

## 5. One extension mechanism: Plugin

A Plugin is the generic extension/package/process unit managed by one Python Plugin Manager. One Plugin process may expose one or more extension kinds.

| Extension | Direction | Responsibility |
|---|---|---|
| event.ingress | Plugin → Host | Publish a normalized Event |
| event.delivery | Host → Plugin | Deliver a structured response to the originating protocol |
| tools | Host → Plugin | Export callable Tool operations |

A Tool is an operation exported by a Plugin, not a process, manager or Runtime. A Tool Plugin is simply a Plugin that exports Tools. A Plugin may expose Event ingress, delivery and Tools together.

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
| ca-openamsm-plugin | Event ingress + delivery | Protocol decoding/normalization and protocol response encoding |
| ca-client-tools | Tools | OpenAMSM callable operations, private bindings and Owner-facing calls |
| Echo Example Plugin | Combined | Minimal Event ingress/delivery and one or more Tools |

ca-openamsm-plugin and ca-client-tools remain independently owned projects. Do not move MAS Owner calls into the Event Plugin. Neither Plugin chooses the Skill or owns Runtime authorization.

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
| Skill | SKILL.md guidance; optional Assurance contract and Procedure | Plugin lifecycle or Tool implementation |
| CA-SL Compiler | Assurance source validation, linking and Artifact generation/inspection | LLM Action execution or business Runtime |
| Python Runtime | Run state, admission, Capability authorization, Action validation, Tool dispatch, Outcomes/Evidence, Wait/Resume/Reconcile | LLM Model Loop or Plugin protocol parsing |
| Deterministic Procedure Engine | Advance a validated Procedure and derive the next Action | Independent Tool dispatch or authorization |
| Plugin Manager | Process lifecycle, IPC and extension dispatch | Skill selection, authorization or Owner truth |
| Tool Plugin | Execute the requested Tool and return its result/receipt | Granting itself permission or inventing Owner outcomes |
| Owner | Authoritative external business state and commit result | Agent reasoning |

### 7.1 Four distinct flows

**A. Import SKILL.md-only source**

~~~text
SKILL.md
   |
   v
Skill Importer
   |
   v
LLM-guided Skill available
~~~

No Assurance and no Compiler invocation.

**B. Import source with Assurance**

~~~text
SKILL.md + assurance source
   |
   v
Skill Importer
   |
   v
CA-SL Compiler: Check / Build
   |
   v
Artifact Inspect / Verify
   |
   v
Host Admission
   |
   v
Skill available in both modes
~~~

**C. Import a compiled Artifact**

~~~text
SKILL.md + compiled Skill Artifact
   |
   v
Skill Importer
   |
   v
Artifact Inspect / Verify
   |
   v
Host Admission
   |
   v
Skill available in both modes
~~~

No rebuild.

**D. LLM Action vs Skill Authoring**

- An LLM-proposed individual Action is validated by the Runtime Action Boundary. It is not compiled into a temporary Procedure.
- An LLM-created or LLM-edited SKILL.md-only package follows the ordinary no-Assurance import path.
- An LLM-created or LLM-edited Assurance source follows the source import and Compiler path before it can be used deterministically.

### 7.2 Shared Action path

- Deterministic mode derives an Action from the admitted Procedure.
- LLM-guided mode proposes an Action from Skill-scoped Context.
- Both submit the same conceptual RuntimeActionRequest to the same Runtime Action Boundary.
- Runtime validates Schema, selected Skill scope, Capability, Effect, budget and admission before dispatching through the Plugin Manager.
- LLM cannot call Plugins directly, widen Capability grants, fabricate Evidence or declare an Owner mutation COMMITTED.
- READ results remain Observations with provenance. MUTATION results follow their Owner Receipt/Commit Proof contract; UNKNOWN remains UNKNOWN.

## 8. End-to-end flow

~~~mermaid
flowchart TB
  EXT[External Event / User Task] --> EP[Event Plugin]
  EP --> PM[One Python Plugin Manager]
  PM --> HOST[Python Host / Agent]
  HOST --> CONT{Exact continuation?}
  CONT -->|yes| RESUME[Resume original Run]
  CONT -->|no| IMPORT[Skill Importer]
  IMPORT --> SOURCE{Input kind}
  SOURCE -->|SKILL.md only| GUIDANCE[LLM-guided Skill]
  SOURCE -->|Assurance source| COMP[CA-SL Compiler]
  SOURCE -->|Compiled Artifact| VERIFY[Artifact Inspect / Verify]
  COMP --> VERIFY
  VERIFY --> ADMIT[Host Admission]
  ADMIT --> RESOLVER[Skill Resolver]
  GUIDANCE --> RESOLVER
  RESOLVER --> WHEN{Assurance when matches?}
  WHEN -->|explicit match| SELECT[Bind exact Skill]
  WHEN -->|no explicit match| SEMANTIC[Semantic candidates from SKILL.md]
  SEMANTIC --> SELECT
  SELECT --> MODE{Execution mode}
  MODE -->|Deterministic| PROC[Validated Procedure]
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

The diagram describes the target flow, not current implementation status. A Skill must be imported and admitted before selection. A Skill with invalid Assurance is not a fallback LLM-only Skill.

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
- **Known gate:** current compiler support for the refreshed contract.when and SKILL.md-only package import is not yet established by this documentation review. Do not claim support, strip the field or implement a second compiler in Python. The Compiler owner must deliver/verify the matching v1alpha5 behavior before deterministic source import can pass.

## 11. Demo-level non-goals

Do not add:

- extra SHA-256 hashing for Plugin packages or Event snapshots;
- package/file integrity frameworks, package signatures or a Trust Registry;
- Domain Contract Packages, TaskContract Packages or a second Skill descriptor;
- separate Provider Manager, Tool registry, Runtime or authorization path;
- legacy format compatibility or automatic migration;
- Marketplace, installer, hot reload or automatic package downloads;
- production HA, complex multi-tenant governance, distributed Event Bus, broad DFX or production qualification machinery.

Keep basic YAML/Schema/version/reference validation, path containment, clear errors, explicit process configuration, minimal correlation and runnable acceptance Examples. Existing Compiler/Interface Package identities remain governed by their owning contracts; do not add a second Host-side digest or integrity system.
