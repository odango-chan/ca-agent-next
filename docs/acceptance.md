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
- one Assurance-backed Echo Skill that can run in both Deterministic and LLM-guided modes;
- one SKILL.md-only Echo guidance Skill that is LLM-guided only;
- source and compiled-Artifact import cases;
- a deterministic fake Model client for selection and LLM-guided Action tests.

Suggested layout (adapt to actual code; do not create empty folders):

~~~text
examples/echo/
  plugin/
    plugin.yaml
    schemas/
  skills/
    echo-assured/
      SKILL.md
      assurance/
        contract.yaml
        procedure.yaml
        predicates.yaml
    echo-guidance/
      SKILL.md
  interface/                 # Compiler-owned Echo Tool Interface Package
  scenarios/
    deterministic/
    llm-guided/
    import-source/
    import-artifact/
    selection/
    authoring/
tests/
  acceptance/
    test_echo_plugin.py
    test_skill_import.py
    test_skill_selection.py
    test_runtime_action_boundary.py
~~~

The Plugin manifest declares Event types and Schemas; it does not name a Skill or business Contract Package. The Skill's optional Assurance declares Goal, request/context requirements, Capabilities and optional when. The Plugin exports the Echo Tool; it does not authorize its invocation.

## 3. Required acceptance cases

| ID | Mechanism | Required proof |
|---|---|---|
| EX-01 | Python Host | Host, Agent loop, Skill Importer, Resolver and Runtime run as Python modules; no Go Agent Core is introduced. |
| EX-02 | Plugin lifecycle | One Python Plugin Manager starts one independent Go Plugin process, completes handshake, correlates frames and shuts it down. |
| EX-03 | Unified extensions | The same Plugin process exposes Event ingress, Delivery and Tool invocation; one manager discovers and routes all extensions. |
| EX-04 | Event Schema | Host validates the normalized Event type and payload against the Plugin-owned Event Schema. The Event contains no Skill ID or business Contract Package reference. |
| EX-05 | SKILL.md-only import | A package containing SKILL.md and no assurance directory imports directly without invoking the Compiler and is LLM-guided only. |
| EX-06 | Assurance source import | A source package with assurance/ invokes the CA-SL Compiler automatically; only successful Build/Inspect/Verify and Host Admission make it available. |
| EX-07 | Compiled Artifact import | An already compiled Skill Artifact is inspected, verified and admitted directly; no rebuild/recompile command is invoked. |
| EX-08 | Invalid Assurance | An incomplete, malformed or compiler-rejected Assurance package fails import. It is never downgraded to SKILL.md-only. |
| EX-09 | when selection | A valid assurance/contract.yaml when is statically checked and evaluated against event.type and input; true/false/error and multiple-match behavior follow §4. |
| EX-10 | Semantic selection | Skills without when, including SKILL.md-only Skills, are selected semantically from their imported SKILL.md descriptions; no CEL field is added to SKILL.md. |
| EX-11 | Mode derivation | No Assurance means LLM-guided only. Valid Assurance permits both modes. No supportedModes field exists. |
| EX-12 | LLM Skill Authoring | LLM-created/edited SKILL.md-only content imports directly. LLM-created/edited Assurance source follows the normal Compiler import path before deterministic use. |
| EX-13 | LLM Action proposal | An individual LLM Action proposal is validated by Runtime Action Boundary and does not invoke the Compiler or create a temporary Procedure. |
| EX-14 | Shared Action boundary | Deterministic and LLM-guided modes submit the same Runtime Action Request, authorization, Tool Plugin dispatch and outcome path. |
| EX-15 | READ Observation provenance | READ Tool result becomes an Observation with Tool/Interface/Invocation/Result provenance; it is not confused with model text. |
| EX-16 | Mutation outcome | A MUTATION Tool cannot become COMMITTED from HTTP success or LLM text; Owner Receipt/Commit Proof is required where its Interface Package says so. UNKNOWN remains UNKNOWN. |
| EX-17 | End-to-end delivery | Event → Task → Skill → Run → Tool Plugin → result/Evidence → Host response → originating Plugin delivery succeeds. |
| EX-18 | Plugin package | Load a valid YAML plugin.yaml. Reject malformed YAML, duplicate/unknown fields, unsupported versions, invalid Schema references, path escape and handshake mismatch without registering extensions. No package signature or extra SHA-256 snapshot is required. |
| EX-19 | Continuation | Resume the exact pending Run with original bindings. Duplicate and invalid deliveries cause no new selection or execution advance. |
| EX-20 | Business neutrality | Add a second independently owned Event/Skill/Interface fixture by installing its Plugin and Skill assets and changing deployment inputs only. The same Host, Resolver, Runtime and Plugin Manager build works without business-specific Core code. |

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

The Event Plugin declares only normalized Event types and Schemas. There is no Event→Skill or Event→Mode mapping table. when belongs only to assurance/contract.yaml. predicates.yaml remains execution-time business evaluation.

### 4.2 Execution mode

- Skill selection always precedes mode selection.
- No Assurance: LLM-guided only.
- Valid Assurance: Deterministic and LLM-guided.
- Invalid present Assurance: import failure; no downgrade.
- No supportedModes declaration.
- Both modes use the same Runtime Action Boundary and Tool Plugin path.

### 4.3 Procedure and Action source

- Deterministic mode executes only a Compiler-validated and admitted Procedure Artifact.
- An LLM-proposed individual Action is not a Procedure and is not compiled.
- LLM-created/edited Assurance source is compiled through the Skill Importer before deterministic execution.
- The first Demo gate covers a static Procedure. Additional Procedure-generation/patch mechanisms require their own Example and acceptance tests.

## 5. Compiler and Tool Plugin integration

- Python invokes the canonical CA-SL Compiler interface for Assurance source Check/Build and Artifact Inspect/Verify. Do not copy Go Compiler source or reimplement its semantics.
- At this document revision, support for refreshed CA-SL v1alpha5 contract.when and the Assurance-free SKILL.md import path must be verified against the Compiler owner. Do not silently strip when or claim an unsupported Compiler release works.
- Importing a compiled Artifact invokes Inspect/Verify and Host Admission but not Build.
- The Echo Tool Interface Package is consumed from its canonical Compiler-owned format. Do not duplicate ToolCatalog or calculate an additional Host-side package digest.
- The Tool Plugin process is loaded through the unified Plugin Manager. A temporary adapter may consume ca-client-tools.provider/v2 behind the same manager.
- No separate Provider Manager, Tool registry or authorization path.

The Echo Plugin may be a tiny Go process. It does not require a live OpenAMSM deployment or production Provider credentials.

## 6. Definition of Demo acceptance

Accept the architecture MVP only when EX-01 through EX-20 pass, the Assurance-backed Echo Skill runs in both modes, the SKILL.md-only Skill runs without Compiler invocation, the same Plugin process supports Event/Delivery/Tools, source and compiled-Artifact import behave differently as specified, and a second business works without business-specific Core changes.

This does not claim live OpenAMSM qualification, production readiness or complete 3GPP protocol parity.

## 7. Explicit non-goals

Do not add extra SHA-256 package/event snapshot hashing, package signatures, Trust Registry, Domain/Task Contract Packages, a second Skill descriptor, supportedModes, legacy compatibility, Marketplace, installer, automatic download, hot reload, production HA, distributed failover, complex multi-tenant/security governance, central business registry, distributed Event Bus, separate artifact database, complex compensation orchestration or elaborate DFX merely to pass the Demo.

Keep basic YAML/Schema/version/reference validation, path containment, clear errors, minimal correlation and truthful test evidence.
