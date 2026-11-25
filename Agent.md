# Agent.md — Repository instructions

These instructions apply to every coding agent, automation and VibeCoding session working in this repository.

## 1. Read before changing anything

For every non-trivial task, read:

1. README.md
2. docs/architecture.md
3. docs/plugin-package.md
4. docs/audit/ca-agent-demo.md
5. docs/audit/reuse-and-feasibility.md
6. docs/acceptance.md
7. docs/implementation/deepseek-harness-plan.md
8. The relevant source, package contracts and tests.

If implementation and documentation disagree, stop and report the exact conflict. Do not silently invent a third design.

## 2. Language and repository lineage — mandatory

- Agent Core, Host, Agent loop, Skill Importer, Skill Resolver and Runtime in ca-agent-next are Python. Do not implement or migrate Agent Core to Go.
- Go is appropriate for independently running Plugin executables. A Go Plugin does not imply a Go Host.
- ca-agent-demo is the primary source/evidence repository. Audit and selectively reuse its Python implementation.
- ca-agent-next is a clean, isolated Python implementation, not a wholesale copy of ca-agent-demo.
- ca-agent is the stable implementation and eventual promotion target, not the source tree for this redesign.
- Keep all implementation changes in ca-agent-next unless the user explicitly authorizes another repository.

## 3. Unified Plugin mechanism — mandatory direction

- A Plugin is the generic extension/package/process unit managed by exactly one Plugin Manager. Native packages follow Plugin Package v1alpha1 in docs/plugin-package.md.
- A Plugin may expose event.ingress, event.delivery, tools, or any combination of these extensions in one process.
- A Tool is a callable operation exported by a Plugin, not a process. A Tool Plugin is a Plugin that exports Tools. Do not require one process per Tool.
- Tool input/output Schemas, Effects, Capability membership and Owner outcome/receipt semantics remain in the owning Interface Package.
- Do not create separate permanent Plugin Manager and Provider Manager subsystems, separate Tool registries, or separate authorization/dispatch paths.
- Runtime Action dispatch goes through the Plugin Manager to the selected Tool extension. Runtime remains the sole authorization and outcome authority.
- During migration, an adapter may speak the existing ca-client-tools.provider/v2 process protocol. Keep it behind the unified Plugin Manager; do not fork/copy the Go Provider or establish a second Runtime.
- ca-openamsm-plugin is an Event Plugin; ca-client-tools is a Tool Plugin. They remain independently owned packages/processes and must not duplicate each other's business implementation.
- Plugin manifests are YAML-first. Do not introduce a second JSON manifest format.

## 4. Skill package and optional Assurance — mandatory

- Every Skill package has one required SKILL.md.
- assurance/ is optional. It contains the CA-SL deterministic execution source: contract.yaml, procedure.yaml and predicates.yaml when Predicate definitions are used.
- contract.yaml belongs inside assurance/. Do not move it to the Skill root or require it for every Skill.
- No Assurance means the Skill is LLM-guided only; there is no Deterministic execution path.
- Valid Assurance means the Skill supports both Deterministic and LLM-guided execution. Select the mode only after exact Skill binding.
- If Assurance exists but is incomplete, invalid, unsupported or fails compilation/admission, reject the import. Never silently downgrade to SKILL.md-only.
- Do not add supportedModes, a second LLM Contract, Domain Contract Package, TaskContract Package, applicability.yaml, activation.yaml, constraint.yaml or another Skill descriptor.
- SKILL.md is Agent-facing natural-language guidance. It is not a deterministic Procedure or a second CEL contract.
- predicates.yaml is execution-time business evaluation only; it does not select Skills.

## 5. Skill selection — mandatory

- Every fresh business request resolves and binds a Skill before execution. Exact continuations resume the original Run before fresh selection.
- An Assurance Skill may declare optional top-level contract.yaml.when. It is a pure CEL boolean over normalized event.type and input, used only during Skill selection.
- when is not a Predicate, not an execution-time business check, and not a field in SKILL.md.
- A true when result creates an explicit candidate. False excludes the Skill. Runtime evaluation error fails closed and excludes it with a diagnostic. A malformed/non-boolean/ill-typed expression is a Compiler error.
- One explicit true match selects directly. Multiple explicit true matches may be disambiguated by the LLM only within that exact candidate set.
- If there are no explicit true matches, semantic candidates are the imported Skills without when. This includes SKILL.md-only Skills and Assurance Skills whose Contract omits when. The Agent uses SKILL.md guidance and may choose only among imported candidates.
- A false/error guarded Skill must never be reintroduced into the unguarded semantic set.
- No Event→Skill mapping table, Event→Mode table, Domain Contract Package or business-specific Host routing.

## 6. Skill Import and Compiler — mandatory

- SKILL.md-only source imports directly without invoking the CA-SL Compiler.
- Source containing assurance/ automatically invokes the canonical CA-SL Compiler before Artifact admission.
- An already compiled Skill Artifact is inspected, verified and admitted directly; do not rebuild/recompile it.
- A failed Assurance build/verify/admission is a hard import error. Do not strip fields, ignore unknown syntax or downgrade to LLM-guided.
- Editing only SKILL.md updates Agent guidance and does not require rebuilding unchanged Assurance.
- Editing contract.yaml, procedure.yaml, predicates.yaml or another Assurance source dependency triggers a new Compiler build and admission.
- LLM-created/edited Skill source follows the same import path as user-authored source.
- An individual LLM Action proposal is not Skill source and is validated by Runtime Action Boundary. Do not compile it, create a temporary Procedure or invoke the Compiler for each Action.
- Do not copy the Go Compiler or reimplement its parsing/linking semantics in Python. Consume its canonical CLI/API.
- Current Compiler support for refreshed v1alpha5 contract.when and Assurance-free SKILL.md import must be verified. If unsupported, report the exact dependency blocker; never silently strip the field or claim support.

## 7. Execution modes and Runtime

- Choose execution mode only after a Skill is selected and bound.
- No Assurance: LLM-guided only. Valid Assurance: Deterministic or LLM-guided. Invalid Assurance: import failure.
- Python Host/Agent owns model loop, reasoning, Context assembly, Skill selection orchestration and Action proposal.
- Python Runtime owns Skill Run, Artifact/Capability admission, common Action Request boundary, authorization, Plugin Tool dispatch, Effects, Outcomes/Evidence and Wait/Resume/Reconcile.
- The deterministic Procedure Engine may live inside Runtime. The LLM Model Loop must not.
- Both modes use exactly the same Runtime Action Boundary and Tool Plugin path.
- LLM cannot call a Plugin directly, widen Capability, fabricate Evidence or declare an Owner mutation committed.

## 8. Context and provenance

- Plugin Event is external Push input.
- Tool READ result is a Pull Observation.
- Runtime/Owner Receipt and Commit Proof are execution Evidence.
- Selected Skill supplies SKILL.md guidance and, when Assurance exists, Context Requirements and declared Capabilities.
- Host assembles Model-visible Context and keeps lightweight source references. Model-generated text is not an Observation; a Tool response is not automatically a committed outcome.

## 9. External projects: reuse, do not copy

- ca-skill-compiler: consume the canonical Go skillc executable/API. Python may wrap the CLI and admit the exact Artifact. Do not copy Go Compiler source or reimplement its semantics.
- ca-client-tools: consume the released Go Tool Plugin process and Interface Package. Do not copy/translate its Go implementation into Python.
- ca-skills: consume CA-SL v1alpha5 Skill packages. The refreshed v1alpha5 adds contract.when and clarifies optional Assurance; do not create a competing CA-SL.
- ca-openamsm-plugin: consume as an independent Go Event Plugin after its contract is aligned with the unified Plugin mechanism and Skill-first flow.
- Reuse Python code from ca-agent-demo selectively, only after file-level dependency and test review.

## 10. Demo-level prohibitions and workflow

Do not add:

- extra SHA-256 hashing for Plugin packages/Event snapshots or a parallel package-integrity framework;
- package signatures or a Trust Registry;
- Domain Contract Packages, TaskContract Packages or a second Skill descriptor;
- supportedModes or a second LLM Contract;
- legacy format compatibility or automatic migration;
- Marketplace, installer, automatic package download or hot reload;
- separate Provider Manager, Tool registry, Runtime or authorization path;
- production HA, complex multi-tenant governance, distributed Event Bus or elaborate DFX.

Keep basic YAML/Schema/version/reference validation, path containment, clear errors, simple package loading, minimal Task/Event correlation and useful logs. Existing Compiler/Interface Package identity rules remain owned by their canonical contracts; do not add another Host-side hashing system.

For each change:

1. Name the mechanism and its runnable Example.
2. Implement the smallest vertical slice.
3. Add the Example and automated Acceptance Test in the same change set.
4. Run focused Python tests; build/test any Go Example Plugin separately.
5. Record exact commands/results and distinguish DESIGN, IMPLEMENTED and PASS.
6. Update canonical docs when behavior or ownership changes.
7. Do not modify sibling repositories unless explicitly instructed.
