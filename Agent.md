# Agent.md — Repository instructions

These instructions apply to every coding agent, automation, and VibeCoding session working in this repository.

## 1. Read before changing anything

For every non-trivial task, read in this order:

1. `README.md` — repository purpose and current status.
2. `docs/architecture.md` — canonical architecture and ownership boundaries.
3. `docs/acceptance.md` — required runnable Examples, acceptance gates, and non-goals.
4. The specific code, package contract, and tests being changed.

If implementation and documentation disagree, do not silently invent a third design. Identify the conflict and update the canonical architecture/decision first.

## 2. Repository boundary

- `ca-agent-next` is the isolated next-generation Agent implementation and mechanism-validation workspace.
- `ca-agent` is the current stable baseline; do not modify it from this repository's tasks.
- `ca-agent-demo` is a mechanism prototype/reference; do not modify it from this repository's tasks.
- Do not create another Agent, Runtime, Example, or contract repository unless the user explicitly changes this decision.
- Do not copy the old implementation wholesale. Reuse only pieces that fit the new architecture and can be justified by the acceptance example.

## 3. Contract ownership

- Shared/public contracts define **mechanisms only**: generic envelopes, IPC, lifecycle, package import/discovery, selection interaction, Runtime Action, Observation/Evidence, and delivery mechanics.
- Never add business Goal enumerations, OpenAMSM concepts, Create/Modify/Release, SUPI/QFI, or other domain vocabulary to the shared mechanism contract.
- Business contracts travel with the package that owns their meaning: Plugin, domain package, Skill, or Owner Interface Package. Consumers import them by versioned package reference.
- Plugin owns protocol Event/Manifest schemas; Skill owns Goal applicability, Context Requirements, Capabilities, Procedures, Predicates, constraints, and completion conditions; Owner Interface Package owns Tool/Operation/input/output/Receipt semantics; Provider package owns implementation and binding.
- Do not create a central business Goal Registry, Event-to-Skill mapping, or Event-to-Mode mapping.
- Adding a Skill, Plugin, or Provider for an existing business contract must not require business-specific Agent Core changes.

## 4. Skill-first and Formal-first are mandatory

- Every business execution must first resolve and bind a Skill. No generic Agent path may call business Tools outside a selected Skill.
- Formal Skill Resolver filters imported Skill packages using the Task's business-contract reference and input, Skill applicability, schema validity, Host Base Capability Envelope, required context, and available Artifact/Variant.
- Zero eligible candidates: stop or request missing input. Never ask the LLM to invent a Skill.
- One eligible candidate: select directly; do not call the LLM.
- Multiple candidates: use deterministic rules first. Only unresolved ambiguity may invoke LLM fallback, restricted to the eligible candidates. Validate the exact returned Skill identity.
- Keep selection stages separate: Skill Selection → Procedure Selection/Source Resolution → Resource Binding. Apply Formal-first at each stage.
- LLM proposals are proposals, not executable Procedures. STATIC, LLM_PROPOSAL, FALLBACK, and PATCH-DERIVED sources must converge through deterministic validation/compilation and exact Artifact/Variant binding.
- FALLBACK may select only a published deterministic Procedure explicitly marked fallback-eligible. If facts are insufficient, UNKNOWN remains unresolved, or no valid fallback exists, stop.

## 5. Execution modes and Runtime boundary

- Select execution mode only after a Skill is selected.
- The two modes are Deterministic Procedure and LLM-guided execution. Use a requested mode or generic deployment default/policy constrained by the Skill's supported modes; do not map Events to modes.
- LLM participation in Skill/Procedure selection does not itself make the Run LLM-guided.
- Host/Agent owns the model loop, reasoning, Context assembly, and Action proposal.
- Runtime owns the Skill Run, exact Capability binding, shared Action Request boundary, admission/authorization, Tool dispatch, effects, outcomes/evidence, and Wait/Resume/Reconcile.
- The deterministic Procedure Engine may live inside Runtime. The LLM Model Loop must not.
- Both execution modes must use the same Runtime Action Boundary and Provider path. Never add a second Provider/authorization/dispatch path for LLM.
- Agent must not bypass the selected Skill, widen its Capabilities, call Providers directly, or declare an Owner operation committed.

## 6. Context and facts

Preserve the distinction between fact sources:

- Plugin Event: external Push input.
- Tool READ result: Pull Observation.
- Runtime/Owner Evidence: authoritative execution facts.
- Skill package: Context Requirements, business constraints, Capabilities, and completion criteria.

Host assembles the Model-visible Context from these sources and retains lightweight provenance references. Context is a view, not a new authority. Model-generated text is not an Observation; a Tool response is not automatically a committed outcome.

## 7. Example-first development

- Keep Examples in `examples/`; do not create a separate `ca-example` repository at this stage.
- Every new externally observable extension or execution mechanism must add a new runnable Example case and an automated Acceptance Test in the same change set.
- Examples must consume public mechanism contracts and the same external package/IPC boundaries that a real extension uses.
- Examples must not import Agent `internal` packages or require business-specific Agent Core changes.
- Internal refactoring with no new externally observable mechanism does not require a new Example.
- The initial planned vertical example is Echo: its own business contract, independent Go Plugin, Skill package, Provider, deterministic and LLM-guided scenarios, and response delivery. Do not claim it exists until it is implemented and tested.

## 8. Demo-level scope

Build the smallest credible mechanism demonstration. Keep basic schema validation, clear errors, simple package loading, minimal Event/Task correlation, and useful logs.

Do not introduce production HA, complex multi-tenant isolation, enterprise security governance, elaborate DFX/SLO systems, Marketplace, central business registry, distributed Event Bus, complex compensation orchestration, or broad legacy-version compatibility unless the user explicitly re-scopes the project.

Demo-level simplification does not permit bypassing Skill-first selection, Capability boundaries, or the shared Runtime Action Boundary.

## 9. Implementation workflow

For each change:

1. State the mechanism or behavior being added and the smallest runnable Example that proves it.
2. Implement the smallest vertical slice; avoid speculative frameworks and unused abstractions.
3. Add/update the Example and automated Acceptance Test in the same change set.
4. Run focused tests and relevant repository checks; report exact commands and results.
5. Update the canonical architecture/acceptance docs when behavior or a mechanism changes.
6. Distinguish DESIGN, IMPLEMENTED, and PASS. Do not claim an acceptance result without running its test.
7. Keep changes scoped to this repository. Do not silently edit sibling repositories or add cross-repository compatibility work.
