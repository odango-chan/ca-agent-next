# DeepSeek Harness implementation plan

**Target repository:** odango-chan/ca-agent-next only.
**Agent Core language:** Python.
**Plugin implementation language:** Go is allowed/expected for independent Example and OpenAMSM Plugins.
**Source:** ca-agent-demo Python implementation and the audit documents in this repository.
**Status:** task package for implementation; no code implementation is claimed by this document.

## 0. Mandatory preflight

Read README.md, Agent.md, docs/architecture.md, docs/audit/ca-agent-demo.md, docs/audit/reuse-and-feasibility.md, docs/plugin-package.md, docs/acceptance.md and [the SkillCatalog/Compiler integration requirements](../integration/skill-catalog-compiler-contract.md).

Before coding:

1. Confirm current branch and clean working tree.
2. Record current ca-agent-next HEAD.
3. Keep Agent Core Python. Do not create Go Agent/Host/Runtime modules.
4. Treat ca-agent-demo as read-only source. Do not modify it.
5. Treat ca-skill-compiler, ca-client-tools, ca-skills, ca-openamsm-plugin and ca-agent as read-only dependencies unless the user separately authorizes a cross-repository change.
6. Do not start OpenAMSM/Nsmf migration. The first target is Echo.
7. Read the current CA-SL v1alpha5 and Compiler release contracts. If the refreshed when field or required import behavior is not supported, stop that subtask and report the exact external blocker. Do not strip fields, fake Compiler success or implement a second Compiler in Python.

## 1. Fixed target architecture

Build one Python Agent Core, one Skill Importer, one Skill Resolver, one Runtime and one Plugin Manager.

A Plugin is one independently running package/process and may expose:
- event.ingress: publish normalized Events;
- event.delivery: receive structured responses;
- tools: export callable Tool operations.

A Tool is an operation exported by a Plugin, not a separate process or manager. One Plugin may expose all three extension kinds. Tool Interface Packages remain the authority for callable IDs, IO Schemas, Effects, Capability membership and Owner outcome semantics.

Every fresh business Event resolves a Skill first. Exact continuations resume the original Run before fresh selection. Only after exact Skill binding may the Host choose Deterministic or LLM-guided mode. Both modes submit the same Runtime Action Request to the same Runtime Action Boundary and Tool Plugin dispatch.

## 2. Phase A — Python Core skeleton and dependency map

**Allowed changes:** ca-agent-next only.
**Source reference:** selected Python modules in ca-agent-demo; do not copy the repository wholesale.

Tasks:

1. Establish Python package, CLI entrypoint, configuration model and pytest layout.
2. Define minimum generic contracts: Plugin identity/lifecycle, IPC envelope, extension descriptor, normalized Event, Task/Run reference, Skill source/Artifact reference, Runtime Action Request/Result, Tool result and structured response.
3. Define interfaces before implementations; no business names in Core.
4. Define the Core-owned SkillCatalog and immutable CatalogGeneration interfaces before Resolver implementation. Catalog entries must represent both SKILL.md-only and Assurance Skills.
5. Selectively port Intent/model boundary and Formal/Context primitives identified in the audit. Do not port MockCompiler or treat MockRuntime as final.
6. Keep a small dependency graph; no premature framework or abstract factory layers.

**Acceptance:** Python import/build and focused pytest pass; Core exposes a process-local Catalog snapshot abstraction with generation pinning interfaces; no Go Agent Core files; no business-specific routing table.

## 3. Phase B — Unified Plugin Manager and package IPC

**Allowed changes:** ca-agent-next only.

Implement:

1. One Plugin Manager for process start/stop, handshake, NDJSON framing, correlation and extension discovery.
2. YAML plugin.yaml loading and basic manifest/Schema/version/path validation as specified in docs/plugin-package.md.
3. One extension registry/dispatcher for event.ingress, event.delivery and tools.
4. One Plugin process may advertise multiple extensions. Verify handshake identity/version/protocol/extensions against the manifest.
5. One Go Echo Plugin process exposing Event ingress, Delivery and at least one Tool operation.
6. Keep Plugin process independent of Python imports. Use stdio/NDJSON for Host IPC.

Do not add package signatures, Trust Registry, extra SHA-256 snapshot hashing, separate Provider Manager, hot reload or Marketplace.

**Acceptance:** Python Host starts one Go process, validates plugin.yaml, discovers all declared extension kinds, routes one test message per extension and shuts down cleanly. This phase does not yet require Skill selection or full business E2E.

## 4. Phase C — CA-SL Compiler integration and Skill Importer

**Allowed changes:** ca-agent-next only; consume the canonical external Compiler interface.

Implement one Skill Importer with these paths:

1. SKILL.md-only source: validate basic Skill metadata and import Agent guidance directly. Do not invoke Compiler.
2. Source with assurance/: require the CA-SL source layout; invoke the canonical Compiler Check/Build path, then Inspect/Verify the resulting Artifact and perform Host Admission.
3. Already compiled Skill Artifact: invoke Inspect/Verify and Host Admission directly. Do not invoke Build or recompile.
4. Present but incomplete/invalid Assurance: reject import. Never downgrade to SKILL.md-only.
5. Editing SKILL.md alone updates Agent guidance. Editing Assurance source or its compile dependencies triggers a new build and admission.
6. LLM-created/edited Skill source uses exactly the same import path as user-authored source.

Tasks:

- Add a small Python subprocess/API client for the released Compiler commands.
- Keep Compiler parsing, CA-SL semantics, linking and Artifact generation inside the Go Compiler.
- Keep Host Artifact admission and Capability binding separate from Compiler Build.
- Do not invent a second Artifact format, Skill Contract format or package integrity framework.
- Do not add Host-side SHA-256 package hashing or signature verification. Retain only the identity checks already required by the Compiler/Interface Package contracts.
- Build an immutable candidate SkillCatalog generation from successfully imported packages. Include SKILL.md-only entries; keep full SKILL.md text and compiled Assurance selection metadata in memory. A failed package update must not partially mutate the active generation.

**External dependency gate:** the refreshed CA-SL v1alpha5 contract.when grammar and portable compiled Artifact representation must be supported by the Compiler contract/release before Assurance import/Resolver conformance can pass. SKILL.md-only import is a Next-owned Importer path and does not invoke Compiler, so it can be implemented and tested independently. If current skillc lacks when support, record the precise missing behavior and stop; do not silently strip when or claim the old release is compatible.

**Acceptance:** SKILL.md-only import succeeds without Compiler invocation; Assurance source invokes Compiler and is admitted only after success; compiled Artifact is inspected/admitted without Build; invalid Assurance fails closed; import/update produces a candidate Catalog generation but does not expose it until atomic activation. Phase C remains blocked on the Compiler-owned when Artifact contract described in docs/integration/skill-catalog-compiler-contract.md.

## 5. Phase D — Skill Resolver and mode derivation

**Allowed changes:** ca-agent-next only.

Implement:

1. Resolve exact continuations before fresh Skill selection.
2. Resolve from the active immutable in-memory SkillCatalog generation pinned for this fresh Event. Do not scan package directories or reread SKILL.md/Assurance files on the Event hot path; do not use deployment-owned Event→Skill tables or business Contract Packages.
3. For Assurance Skills, evaluate the precompiled when program from the Catalog against this Event's normalized event.type and input. Compiler parses/type-checks it only on import/update. Every fresh Event is evaluated independently; do not cache the boolean result. Static invalidity is a Compiler error; false and runtime evaluation error exclude the Skill.
4. If exactly one explicit true match exists, select it without LLM. If multiple true matches exist, offer only those candidates to the LLM.
5. If no explicit true match exists, form semantic candidates from unguarded Skills (no when), using cached candidate metadata derived from SKILL.md. This includes SKILL.md-only Skills and Assurance Skills whose Contract omits when. After selection, provide the full SKILL.md content from Catalog memory; do not reread the package file.
6. Never reintroduce a false/error guarded Skill into the unguarded set. Validate the exact Skill identity returned by the model.
7. Derive supported modes from Assurance presence/validity. No Assurance means LLM-guided only; valid Assurance means both modes; invalid Assurance means import failure. Do not add supportedModes.
8. Select execution mode only after exact Skill binding.

**Acceptance:** EX-09/EX-10/EX-11 and EX-21/EX-22/EX-23/EX-27/EX-29 pass with deterministic fake Model client; no business-specific route configuration; false/error candidates are excluded and out-of-set IDs rejected. The Resolver uses only the pinned Catalog snapshot and never invokes Compiler or filesystem reads during selection.

## 6. Phase E — One Runtime Action Boundary and two execution modes

**Allowed changes:** ca-agent-next only.

Implement:

1. One Python Runtime with Run identity, Skill binding, pinned catalogGeneration, admission, Capability authorization, Action Request validation, Tool Plugin dispatch, Outcome/Evidence and basic Wait/Resume semantics. Each Invocation retains its generation until completion; a later Catalog activation affects only new Invocations.
2. Deterministic Procedure Engine derives the next Action from the admitted Procedure Artifact.
3. LLM-guided Host Model Loop proposes the next Action from Skill-scoped Context.
4. Both paths submit the same Action Request to the same Runtime method and same Plugin tools extension.
5. An individual LLM Action is validated by Runtime and never sent to Compiler.
6. An LLM-created/edited Assurance source is handled by Phase C Skill Importer; it must be compiled/admitted before deterministic use.
7. READ Tools produce Observation facts with provenance; MUTATION Tools preserve Owner Receipt/Commit Proof semantics where required.
8. Resolve exact continuations before the Resolver. Invalid or duplicate delivery cannot advance a Run.
9. No direct Agent→Plugin call, no duplicate Provider dispatcher and no second authorization path.

**Acceptance:** same Assurance-backed Echo Skill succeeds in Deterministic and LLM-guided modes; traces show both entering the same Runtime Action boundary and same Tool Plugin operation. The SKILL.md-only Echo Skill runs LLM-guided only. Unauthorized Capability and forged COMMITTED cases fail. LLM Action does not invoke Compiler.

## 7. Phase F — Echo vertical E2E and regression

**Allowed changes:** ca-agent-next only.

1. Make Echo a runnable Example under examples/.
2. Add Echo Acceptance Tests for EX-01 through EX-19 and EX-21 through EX-29. Reserve EX-20 for Phase G's second-business proof.
3. Exercise Event → Skill import/selection → Run → Tool → Outcome/Evidence → response delivery.
4. Exercise SKILL.md-only import, Assurance source import, compiled Artifact import, and LLM Skill Authoring.
5. Exercise Catalog residency, no per-Event file reads/Compiler calls, compile-once/evaluate-per-Event behavior, duplicate/continuation bypass, atomic update, failed-update rollback, generation pinning and lazy references (EX-21–EX-28).
6. Exercise the same Assurance-backed Skill in both modes.
7. Exercise the individual LLM Action path without Compiler.
8. Remove unused scaffolding, duplicated registries and obsolete adapters.
9. Update docs and record exact test commands/results.

**Acceptance:** Echo cases EX-01–EX-19 and EX-21–EX-29 pass or are explicitly BLOCKED by the external Compiler Artifact contract; Python Core remains business-neutral; one Plugin process supports Event, Delivery and Tools. EX-20 is completed in Phase G.

## 8. Phase G — Second independent business

Start after Echo acceptance and review.

1. Add an independent second business Event Plugin, Skill package and Tool Interface Package.
2. Include at least one SKILL.md-only Skill or Assurance-backed Skill to prove the package model is not Echo-specific.
3. Change only package assets and deployment configuration.
4. Do not add business-specific code to Agent Core, Skill Resolver, Runtime or Plugin Manager.

**Acceptance:** EX-20 passes with the same Host build. The second business works without modifying Python Core, Resolver, Runtime or Plugin Manager.

## 9. Phase H — OpenAMSM integration (later, not part of Echo MVP)

Start only after Echo and second-business mechanism acceptance.

- Use ca-openamsm-plugin as Event Plugin for SBI ingress/delivery.
- Use ca-client-tools v1.2.0 as Tool Plugin through the unified Plugin Manager; adapt its current Provider v2 protocol rather than copying its Go code.
- Consume ca-skills Create/Modify/Release CA-SL packages.
- Invoke the Compiler release that supports the refreshed v1alpha5 contract.when compiled Artifact representation. SKILL.md-only packages remain on Next's direct Importer path and never invoke Compiler. Python Runtime consumes the portable checked program specified by the Compiler-owned Artifact contract.
- Keep Nsmf Run lifecycle, resource mapping, Host Artifact Store and Runtime outside the Event Plugin.
- Preserve Owner Receipt, Commit Proof, UNKNOWN and exact-original Reconcile semantics.
- Do not claim live Scheme C or Production Qualification unless the isolated real environment gate is executed.

Cross-repository implementation changes require separate authorization and PRs.

## 10. Explicit prohibitions

- Do not change Agent Core from Python to Go.
- Do not copy ca-skill-compiler or ca-client-tools Go source into next.
- Do not create a separate permanent Provider Manager alongside Plugin Manager.
- Do not create a second ToolCatalog or central business Goal Registry.
- Do not add Domain Contract Package, TaskContract Package, a second Skill descriptor or supportedModes.
- Do not add Event→Skill or Event→Mode mapping tables.
- Do not add extra SHA-256 package hashing, package signatures, Trust Registry or package-integrity framework.
- Do not add legacy format compatibility or automatic migration.
- Do not scan Skill package files, parse SKILL.md or compile CEL on every Event. Do not cache when results across distinct Events.
- Do not put SkillCatalog under Plugin Manager or introduce a distributed cache. Explicit Catalog update is atomic; no filesystem watcher or generic Plugin hot reload.
- Do not compile individual LLM Action proposals or wrap each one in a temporary Procedure.
- Do not let LLM invoke Plugins directly or declare Owner commit.
- Do not move NsmfRunExecutor, Owner claims, Receipt/Reconcile or Skill Runtime into ca-openamsm-plugin.
- Do not start OpenAMSM before Echo and second-business acceptance.
- Do not claim a test PASS unless the command was actually run and its output recorded.

## 11. Final report required from each phase

Report:

- changed files and commit;
- exact Python/Go commands executed and results;
- which Example case proves the mechanism;
- whether any external repository was modified (expected: no unless separately authorized);
- remaining UNKNOWN/NOT_RUN gates;
- any external Compiler/spec dependency blocker;
- whether the next phase can start without changing the architecture.
