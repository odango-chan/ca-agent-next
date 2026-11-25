# Agent.md — Repository instructions

These instructions apply to every coding agent, automation and VibeCoding session working in this repository.

## 1. Read before changing anything

For every non-trivial task, read:

1. `README.md`
2. `docs/architecture.md`
3. `docs/audit/ca-agent-demo.md`
4. `docs/audit/reuse-and-feasibility.md`
5. `docs/acceptance.md`
6. `docs/implementation/deepseek-harness-plan.md`
7. The relevant source, package contracts and tests.

If implementation and documentation disagree, stop and report the exact conflict. Do not silently invent a third design.

## 2. Language and repository lineage — mandatory

- **Agent Core, Host, Agent loop, Skill Resolver and Runtime in `ca-agent-next` are Python. Do not implement or migrate Agent Core to Go.**
- Go is appropriate for independently running Plugin executables. A Go Plugin does not imply a Go Host.
- `ca-agent-demo` is the primary source/evidence repository. Audit and selectively reuse its Python implementation.
- `ca-agent-next` is a clean, isolated Python implementation, not a wholesale copy of `ca-agent-demo`.
- `ca-agent` is the stable implementation and eventual promotion target, not the source tree for this redesign.
- Keep all implementation changes in `ca-agent-next` unless the user explicitly authorizes another repository.

## 3. Unified Plugin mechanism — mandatory direction

- A Plugin is the generic extension/package/process unit managed by one Plugin Manager.
- A Plugin may expose one or more extension kinds: `event.ingress`, `event.delivery`, and `tools`.
- A **Tool Plugin** is a Plugin whose exported extension is one or more callable Tools. A Plugin may expose both Events and Tools; do not require one process per Tool.
- A Tool is an exported callable operation, not a process. Its input/output Schema, Effect, Capability membership and Owner outcome/receipt semantics remain in its owning Interface Package.
- Do not create separate permanent Plugin Manager and Provider Manager subsystems, separate Tool registries, or separate authorization/dispatch paths.
- Runtime Action dispatch goes through the Plugin Manager to the selected Tool Plugin. The Runtime remains the sole authorization and outcome authority.
- During migration, an adapter may speak the existing `ca-client-tools.provider/v2` process protocol. Keep it behind the unified Plugin mechanism; do not fork/copy the Go Provider or establish a second Runtime.
- `ca-openamsm-plugin` is an Event Plugin; `ca-client-tools` is an OpenAMSM Tool Plugin. They remain independently owned packages/processes and must not duplicate each other's business implementation.

## 4. Contract ownership

- Shared/public contracts define **mechanisms only**: Plugin lifecycle/IPC, generic Event/Task/Run envelopes, extension discovery, selection request/result, Runtime Action, Observation/Evidence and delivery mechanics.
- Do not put business Goal enums, OpenAMSM, Create/Modify/Release, SUPI/QFI or domain-specific mappings into shared mechanism contracts.
- Plugin packages own protocol Event declarations and payload Schemas.
- A domain contract package owns shared business meaning when needed.
- Skill packages own business applicability, Goal, Context Requirements, Capability declarations, Procedures, Predicates, constraints and completion conditions.
- Tool Interface Packages own callable IDs, input/output Schemas, Effects, Capability membership and Owner Receipt/Commit/Reconcile semantics.
- Tool Plugin packages own executable implementation and private runtime bindings. The Plugin manifest references the Interface Package; it must not author a duplicate ToolCatalog.
- Compiler contracts and CA-SL v1alpha5 are consumed from their canonical owners. Do not create competing schemas or copy external authorities into Agent Core.

## 5. Skill-first and Formal-first are mandatory

- Every business request/event must resolve and bind a Skill before business execution. There is no generic LLM path that bypasses Skill selection and directly calls Tools.
- A Plugin emits a normalized Event/Task intent plus a business-contract package reference and payload. It must not name a Skill or choose an execution mode.
- Formal Resolver filters imported Skill packages using business-contract reference, input Schema, Skill applicability, Host Base Capability Envelope, required Context and available Artifact/Variant.
- 0 eligible Skills: stop or request missing input; do not ask the LLM to invent one.
- 1 eligible Skill: select directly without LLM.
- N candidates: apply formal rules first. Only unresolved ambiguity may invoke LLM, restricted to the eligible candidate set. Host validates the exact returned Skill identity.
- Selection stages remain separate: Skill Selection → Procedure Selection/Source Resolution → exact Artifact/Variant and Capability Binding.
- LLM proposals are proposals, not executable Procedures. STATIC, LLM_PROPOSAL, FALLBACK and PATCH-DERIVED sources must converge through deterministic validation/compilation.
- FALLBACK may select only a published deterministic Procedure explicitly marked fallback-eligible. UNKNOWN or missing facts remain unresolved.

## 6. Execution modes and Runtime

- Choose execution mode only after a Skill is selected. The two modes are Deterministic Procedure and LLM-guided execution, constrained by the selected Skill's supported modes and a generic request/deployment default.
- LLM participation in Skill/Procedure selection does not itself make the Run LLM-guided.
- Python Host/Agent owns model loop, reasoning, Context assembly, selection orchestration and Action proposal.
- Python Runtime owns Skill Run, exact Artifact/Capability binding, common Action Request boundary, admission/authorization, Plugin Tool dispatch, effects, outcomes/evidence and Wait/Resume/Reconcile.
- The deterministic Procedure Engine may live inside Runtime. The LLM Model Loop must not.
- Both modes use exactly the same Runtime Action boundary and Tool Plugin path.
- LLM cannot call a Plugin directly, widen Capabilities or declare an Owner mutation committed.

## 7. Context and provenance

- Plugin Event is external Push input.
- Tool READ result is a Pull Observation.
- Runtime/Owner Receipt and Commit Proof are execution Evidence.
- Selected Skill package supplies Context Requirements, business constraints and declared Capabilities.
- Host assembles Model-visible Context and keeps lightweight source references. Model-generated text is not an Observation; a Tool response is not automatically a committed outcome.

## 8. External projects: reuse, do not copy

- `ca-skill-compiler`: consume the pinned Go `skillc` executable/API. Python may wrap the CLI and validate/admit the exact Artifact. Do not copy the Go compiler into this repository or reimplement its compiler semantics.
- `ca-client-tools`: consume the released Go Tool Plugin process and Interface Package. Do not copy/translate its Go implementation into Python.
- `ca-skills`: import/use published CA-SL v1alpha5 Skill package assets. Do not copy 5GC business logic into Host.
- `ca-openamsm-plugin`: consume as an independent Go Event Plugin after its contract is aligned with this architecture.
- Reuse Python code from `ca-agent-demo` selectively, only after file-level dependency and test review.

## 9. Example-first development

- Keep runnable Examples in `examples/`; do not create a separate `ca-example` repository.
- Every new externally observable extension or execution mechanism must add a new runnable Example case and an automated Acceptance Test in the same change set.
- Examples must use public package/Plugin/Runtime boundaries and must not import Agent Core internals.
- The initial Echo Example should exercise Event ingress and Tool invocation through one Plugin mechanism, and run the same selected Skill in both Deterministic and LLM-guided modes.
- Internal refactoring without a new externally observable mechanism does not require a new Example.

## 10. Demo-level scope and implementation workflow

Keep basic schema validation, clear failures, simple package loading, minimal Task/Event correlation, and useful logs.

Do not add production HA, complex multi-tenant/security governance, elaborate DFX/SLO systems, Marketplace, central business registry, distributed Event Bus, complex compensation orchestration or broad legacy compatibility unless explicitly re-scoped.

For each change:

1. Name the mechanism and its runnable Example.
2. Implement the smallest vertical slice.
3. Add the Example and automated Acceptance Test in the same change set.
4. Run focused Python tests; build/test any Go Example Plugin separately.
5. Record exact commands/results and distinguish DESIGN, IMPLEMENTED and PASS.
6. Update canonical docs when behavior or ownership changes.
7. Do not modify sibling repositories unless explicitly instructed.
