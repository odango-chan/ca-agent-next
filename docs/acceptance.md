# MVP acceptance

**Status:** architecture documented; implementation NOT_STARTED; acceptance NOT_RUN.
**Language:** Python Agent Core; independent Go Example Plugin.
**Scope:** Demo-level mechanism proof only, not Production Qualification.

## 1. Example-first rule

Every new externally observable mechanism must add a runnable Example case and an automated Acceptance Test in the same change set. Examples live under examples/; no separate ca-example repository.

Examples consume the public Plugin/Skill/Runtime boundaries and must not import Agent Core internals. An internal refactor with no new externally observable mechanism does not need a new Example.

## 2. First vertical Example: Echo

One independently running Go Plugin exposes Event ingress, Delivery and at least one Tool operation through the same Plugin Manager and process.

The Example contains:
- one published Assurance-backed Echo Skill that can run in both Deterministic and LLM-guided modes;
- one published SKILL.md-only Echo guidance Skill that is LLM-guided only;
- published Artifact import cases (valid, malformed, unsupported format, missing files and unresolved dependencies);
- a deterministic fake Model client for selection and LLM-guided Action tests.

Compiler source/build/release is an external toolchain concern. Next acceptance consumes a prebuilt published Artifact fixture; it does not import Assurance source or invoke Compiler.

Suggested layout (adapt to actual code; do not create empty folders):

~~~text
examples/echo/
  plugin/
    plugin.yaml
    schemas/
  published-skills/
    echo-assured/
      SKILL.md
      <Compiler-generated runtime Artifact files>
    echo-guidance/
      SKILL.md
  interface/                 # Compiler-owned Echo Tool Interface Package
  scenarios/
    deterministic/
    llm-guided/
    import-published-artifact/
    selection/
tests/
  acceptance/
    test_echo_plugin.py
    test_skill_import.py
    test_skill_selection.py
    test_runtime_action_boundary.py
~~~

The Plugin manifest declares Event types and Schemas; it does not name a Skill or business Contract Package. The Skill's published compiled Assurance declares Procedure, request/context requirements, Capabilities and optional when. The Plugin exports the Echo Tool; Runtime checks that an Action stays within the selected Skill's declared callable scope.

## 3. Required acceptance cases

| ID | Mechanism | Required proof |
|---|---|---|
| EX-01 | Python Host | Host, Agent loop, Skill Importer, Resolver and Runtime run as Python modules; no Go Agent Core is introduced. |
| EX-02 | Plugin lifecycle | One Python Plugin Manager starts one independent Go Plugin process, completes handshake, correlates frames and shuts it down. |
| EX-03 | Unified extensions | The same Plugin process exposes Event ingress, Delivery and Tool invocation; one manager discovers and routes all extensions. |
| EX-04 | Event Schema | Host validates the normalized Event type and payload against the Plugin-owned Event Schema. The Event contains no Skill ID or business Contract Package reference. |
| EX-05 | SKILL.md-only import | A package containing SKILL.md and no assurance directory imports directly without invoking the Compiler and is LLM-guided only. |
| EX-06 | Published Assurance Artifact import | A published package containing SKILL.md and a Compiler-generated runtime Artifact is imported without invoking Compiler; basic format/manifest/required-file/reference/type-data checks and local Tool/Capability dependency resolution succeed. |
| EX-07 | Import is not compilation or admission | Agent never invokes Compiler Check/Build/Inspect/Verify and has no Skill Admission stage; it loads the published Artifact after basic structural checks and dependency resolution. |
| EX-08 | Invalid published Artifact | Missing required compiled files, unsupported Artifact format, malformed CEL/type data, unsafe paths or unresolved Tool/Capability dependencies fail import with explicit diagnostics; never downgrade to SKILL.md-only. |
| EX-09 | when selection | The external Compiler statically checks when before publication; Agent loads the checked program from the published Artifact and evaluates it against event.type and input. True/false/error and multiple-match behavior follow §4. |
| EX-10 | Semantic selection | Skills without when, including SKILL.md-only Skills, are selected semantically from their imported SKILL.md descriptions; no CEL field is added to SKILL.md. |
| EX-11 | Mode derivation | No Assurance means LLM-guided only. Valid Assurance permits both modes. No supportedModes field exists. |
| EX-12 | LLM Skill Authoring | LLM-created/edited SKILL.md-only content imports directly. LLM-created/edited Assurance source is not executable until an external publishing workflow compiles and publishes its Artifact; Agent never invokes Compiler. |
| EX-13 | LLM Action proposal | An individual LLM Action proposal is validated by Runtime Action Boundary and does not invoke the Compiler or create a temporary Procedure. |
| EX-14 | Shared Action boundary | Deterministic and LLM-guided modes submit the same Runtime Action Request, declared Skill callable-scope checks, Tool Plugin dispatch and outcome path. No separate Skill Admission or production authorization is implemented. |
| EX-15 | READ Observation provenance | READ Tool result becomes an Observation with Tool/Interface/Invocation/Result provenance; it is not confused with model text. |
| EX-16 | Mutation outcome | A MUTATION Tool cannot become COMMITTED from HTTP success or LLM text; Owner Receipt/Commit Proof is required where its Interface Package says so. UNKNOWN remains UNKNOWN. |
| EX-17 | End-to-end delivery | Event → Task → Skill → Run → Tool Plugin → result/Evidence → Host response → originating Plugin delivery succeeds. |
| EX-18 | Plugin package | Load a valid YAML plugin.yaml. Reject malformed YAML, duplicate/unknown fields, unsupported versions, invalid Schema references, path escape and handshake mismatch without registering extensions. No package signature or extra SHA-256 snapshot is required. |
| EX-19 | Continuation | Resume the exact pending Run with original bindings. Duplicate and invalid deliveries cause no new selection or execution advance. |
| EX-20 | Business neutrality | After Echo passes, add OpenAMSM as the second independently owned Event/Skill/Interface package by installing its Plugin and Skill assets and changing deployment inputs only. The same Host, Resolver, Runtime and Plugin Manager build works without business-specific Core code. |
| EX-21 | Core-owned SkillCatalog | Startup/import registers all valid Skills, including SKILL.md-only Skills, in one immutable in-memory Catalog owned by Core/Host; Plugin Manager does not own or scan Skill packages. |
| EX-22 | Hot-path residency | After Catalog activation, fresh Event selection performs no Skill-directory scan, SKILL.md/Artifact file read or Compiler invocation. Full SKILL.md text and deserialized when programs are served from memory. |
| EX-23 | when publish-once / load-once / evaluate-per-Event | External Compiler compiles/type-checks when before publication; Agent deserializes the checked program once on import. Two fresh Events with different inputs evaluate the same in-memory program independently and may produce different results; no previous boolean result is reused. |
| EX-24 | Replay and continuation | A duplicate Event is deduplicated before fresh selection; an exact continuation resumes its original Run and pinned Catalog generation without reevaluating when. |
| EX-25 | Atomic Catalog update | An explicit update builds a candidate generation off-path and atomically activates it only after basic package/Artifact checks and dependency resolution. A failed update leaves the active generation unchanged. No Skill Admission stage exists. |
| EX-26 | Invocation generation pinning | An Invocation selected under generation N continues using N's SKILL.md, published Artifact and Capability/callable bindings after generation N+1 is activated; new Invocations use N+1. |
| EX-27 | SKILL.md and semantic metadata residency | Semantic candidate selection uses metadata derived from cached SKILL.md; after selection the full SKILL.md is supplied from memory without rereading the package file. |
| EX-28 | Lazy knowledge assets | references/ and large knowledge assets are not loaded during every Event selection; they are loaded only when the selected Skill/context needs them. |
| EX-29 | Compiler/Runtime when parity | The published runtime Artifact carries the Compiler-owned portable checked when program and CEL profile/type bindings. Python Runtime deserializes it on import and evaluates it against current event.type/input with results matching CA-SL normative fixtures; no Python reparse or per-Event Compiler call. |

## 4. Skill selection and mode behavior

### 4.1 Skill selection

| Candidate state | Required behavior |
|---|---|
| Assurance Skill with when = true; exactly one match | Select directly without an LLM call |
| Assurance Skills with when = true; multiple matches | Offer only those exact matches for LLM disambiguation |
| No true when matches | Offer only unguarded Skills (no when) for semantic selection from SKILL.md |
| No unguarded candidate | Stop or request missing input |
| when = false | Exclude the guarded Skill; do not reintroduce it as an unguarded candidate |
| when runtime evaluation error | Fail closed, exclude the Skill and record a diagnostic |
| malformed/non-boolean/ill-typed when | Compiler rejects the Assurance source |
| LLM returns an unoffered Skill identity | Reject the result |
| Continuation | Resume the original Run before fresh selection |

The Event Plugin declares only normalized Event types and Schemas. There is no Event→Skill or Event→Mode mapping table. when belongs only to assurance/contract.yaml. predicates.yaml remains execution-time business evaluation. The Resolver reads an immutable Core-owned in-memory SkillCatalog snapshot; it does not read package files on each Event. It evaluates each compiled when program for each fresh Event, without caching the result.

### 4.2 Execution mode

- Skill selection always precedes mode selection.
- No published Assurance Artifact: LLM-guided only.
- Valid published Assurance Artifact: Deterministic and LLM-guided.
- Assurance source or invalid/missing compiled Artifact in a package that declares Assurance: import failure; no downgrade.
- No supportedModes declaration.
- Both modes use the same Runtime Action Boundary and Tool Plugin path.

### 4.3 Procedure and Action source

- Deterministic mode executes only a Compiler-built and verified published Procedure Artifact.
- An LLM-proposed individual Action is not a Procedure and is not compiled.
- LLM-created/edited Assurance source is not compiled by Agent; it must be compiled and published externally before its Artifact can be imported for deterministic execution.
- The first Demo gate covers a static Procedure. Additional Procedure-generation/patch mechanisms require their own Example and acceptance tests.

## 5. Compiler and Tool Plugin integration

- CA-SL Compiler is an independent authoring/release toolchain. It performs source Check/Build/Verify before publication; Agent never invokes Compiler. Do not copy Go Compiler source or reimplement its semantics.
- Compiler v2.1.0 does not yet establish refreshed CA-SL v1alpha5 contract.when support. [Compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) tracks a new versioned published runtime Artifact and cel-go → cel-expr-python CheckedExpr interoperability. The Agent imports published bundles only and never invokes Compiler. See [技能目录与编译器运行时接口设计说明书](集成设计/技能目录与编译器运行时接口设计说明书.md). Do not silently strip when or claim an unsupported release works.
- Target behavior: external Compiler parses/type-checks when once before publication and emits CheckedExpr + DescriptorSet; Python Runtime deserializes once on import and evaluates the same program for every fresh Event. No raw CEL parsing/type-checking on the Event hot path.
- Importing a compiled Artifact does not invoke any Compiler command or Skill Admission. The Agent performs only basic structural/reference checks and local dependency resolution.
- The Echo Tool Interface Package is consumed from its canonical Compiler-owned format. Do not duplicate ToolCatalog or calculate an additional Host-side package digest.
- The Tool Plugin process is loaded through the unified Plugin Manager. A temporary adapter may consume ca-client-tools.provider/v2 behind the same manager.
- No separate Provider Manager, Tool registry or authorization path.

The Echo Plugin may be a tiny Go process. It does not require a live OpenAMSM deployment or production Provider credentials.

## 6. Definition of Demo acceptance

Accept the architecture MVP only when EX-01 through EX-29 pass, the Assurance-backed Echo Skill runs in both modes, the SKILL.md-only Skill runs without Compiler invocation, the same Plugin process supports Event/Delivery/Tools, SKILL.md-only and published compiled-Assurance imports behave as specified, SkillCatalog residency/generation tests pass, and a second business works without business-specific Core changes.

This does not claim live OpenAMSM qualification, production readiness or complete 3GPP protocol parity.

## 7. Explicit non-goals

Do not add extra SHA-256 package/event snapshot hashing, package signatures, Trust Registry, Skill Admission, approval workflows, Owner Trust, production authorization, Domain/Task Contract Packages, a second Skill descriptor, supportedModes, legacy compatibility, Marketplace, installer, automatic download, filesystem watchers or generic Plugin hot reload, production HA, distributed failover, complex multi-tenant/security governance, central business registry, distributed Event Bus, separate artifact database, complex compensation orchestration or elaborate DFX merely to pass the Demo. Explicit SkillCatalog import/update with atomic generation activation is in scope; it is not a general Plugin hot-reload system.

Keep basic YAML/Schema/version/reference validation, path containment, clear errors, minimal correlation and truthful test evidence.


## 8. OpenAMSM integration acceptance — after Echo

**Current status:** NOT_STARTED. These gates are target acceptance criteria, not implementation or test claims.

| ID | Gate | Required evidence |
|---|---|---|
| OM-01 | Contract alignment | OpenAMSM Plugin uses the exact connectionagent.io/plugin-package/v1alpha1 manifest and connectionagent.io/plugin-ipc/v1alpha1 envelope/messages from docs/plugin-package.md. No ca-agent-host.plugin/v0 alias remains. |
| OM-02 | Skill-first selection | Fresh Create/Modify/UE-requested Release Events bind the existing ca-skills Skills before mode selection. when lives only in assurance/contract.yaml. No Generic Agent path runs without a selected Skill. |
| OM-03 | Event mapping | Event Plugin maps the SBI operation and JSON fields to a base Event type, and extracts only the minimal NAS message discriminator needed for shared UpdateSMContext cases (Modify versus UE-requested Release). This is protocol-to-Event normalization, not Skill selection or full decode. The Host Resolver selects the Skill from the normalized Event. UE-requested Release is not conflated with network-initiated ReleaseSMContext. |
| OM-04 | Tool integration | ca-client-tools v1.2.0 is invoked through the one Plugin Manager tools extension adapter. No copied ToolCatalog, private Owner map, MAS Python backend or second Provider Manager is introduced. |
| OM-05 | Binary ingress | Original N1/N2 multipart bytes are staged by Plugin, imported by Host ArtifactStore, associated with the correct Run and exposed only as authorized artifactRefs. No Base64 or Plugin database. |
| OM-06 | Binary delivery | Host stages only authorized outbound N1/N2 artifacts for the exact responseObligationId; Plugin encodes the correct SBI response and reports delivery disposition. |
| OM-07 | Continuation | N1 Release Complete (0xD4) and N2 PDU Session Resource Release Response, where applicable, resume the exact original Run/SUPI/PSI/generation. Stale or duplicate messages do not wake a newer Run or repeat a mutation. |
| OM-08 | Retry and response obligations | Stable externalRequestId is mapped from actual protocol identity. Same-request retry attaches a new response obligation to the original Run; a conflicting reuse fails closed. HTTP/2 stream IDs are not logical Run IDs. |
| OM-09 | Owner outcomes | Create → Modify → Release uses actual OpenAMSM Owner; Receipt, Commit Proof, UNKNOWN and Reconcile semantics remain authoritative. HTTP success and delivery success do not imply business COMMITTED. |
| OM-10 | Codec scope | Consume only merged/released Codec APIs and the explicitly qualified NAS/N2 message subset. NGAP full-PDU qualification is not claimed; Phase C consumer integration must be complete for the exact used paths. |
| OM-11 | Real isolated E2E | One UE/PSI completes Create → Modify → Release against real isolated OpenAMSM/Owner with raw N1/N2, Run/Wait evidence and zero duplicate mutation. Synthetic Owner tests do not satisfy this gate. |
| OM-12 | Zero Core business coupling | After Echo acceptance, OpenAMSM is added through Plugin package, Skills and deployment configuration; no OpenAMSM-specific branch is added to Agent Core, Resolver, Runtime or Plugin Manager. |
| OM-13 | On-demand Codec | A Skill that does not need protocol fields passes the original artifactRef without invoking Codec. A Skill that needs fields calls the published Codec Tool through the same Runtime Action Boundary and receives structured JSON. Decode never replaces the original N1/N2 bytes. |
| OM-14 | Protocol Schema ownership | SBI request/response and multipart structure follow the applicable 3GPP OpenAPI; NAS/NGAP Codec structures follow the relevant 3GPP definitions. Skill requestSchema contains only the business fields the Skill consumes; no duplicate or rewritten 3GPP Schema is introduced. |
| OM-15 | Minimal routing classifier | The shared Codec implementation can classify the exact NAS message discriminator needed for UpdateSMContext (including the qualified Modify and UE-requested Release message types). The Event Plugin uses only that minimal classifier; unsupported, malformed or ambiguous messages fail explicitly and are never mapped to a Skill by guesswork. No duplicate parser is added.

### 8.1 External dependency gates

| Dependency | State on 2026-11-25 | Required before claiming the corresponding gate |
|---|---|---|
| ca-skills PR #88 | OPEN, not merged; proposes same-identifier CA-SL v1alpha5 optional Assurance and contract.when | Merge/review the language refresh and align the three existing MAS Skills' when fields. |
| ca-skill-compiler v2.1.0 | Released; refreshed contract.when not supported/verified | [Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) defines a versioned published runtime Artifact and CheckedExpr/DescriptorSet handoff. Agent imports published Artifacts only and never invokes Compiler. |
| ca-client-tools v1.2.0 | Released; Provider v2 process | Integrate through the unified Plugin Manager adapter; separately verify real SBI multipart Artifact use through the Provider channel. |
| ca-client-tools PR #39 | OPEN; Phase B final pass, Phase C not started | Merge/release and complete consumer integration for the exact codec calls used. NAS: 8 qualified; N2: 7 scoped qualified; NGAP: 0 CA-qualified full PDUs. |
| ca-agent-demo PR #246 | OPEN; synthetic G5 22 passed; real G6 NOT_RUN/BLOCKED; G7 PARTIAL | Treat only as reusable evidence. Run the new Host + Plugin + Provider + real Owner path independently. |

The Provider's Host-to-Provider Artifact channel has acceptance-fixture evidence; the production catalog's real-NF SBI multipart binding remains NOT_VERIFIED. OM-05/OM-06 and OM-11 must include the exact real path, not just fixture coverage.

## 9. Acceptance order

1. Complete Core and common Plugin Manager gates EX-01 through EX-19 and SkillCatalog gates EX-21 through EX-29.
2. Pass the Generic Echo vertical E2E.
3. Use OpenAMSM as the second independent business and prove EX-20: add its Plugin, Skills and Tool package through package/deployment changes only, without modifying Agent Core, Resolver, Runtime or Plugin Manager.
4. Freeze the OpenAMSM Event Schema, exact SBI operation mapping, externalRequestId and continuation correlation.
5. Implement the Go OpenAMSM Event Plugin and Host Artifact Handoff.
6. Integrate ca-client-tools v1.2.0 through the common Plugin Manager tools extension.
7. Pass OM-01 through OM-15. Keep every unrun real-lab gate explicitly NOT_RUN.
