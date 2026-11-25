# DeepSeek Harness implementation plan

**Target repository:** odango-chan/ca-agent-next only.
**Agent Core language:** Python.
**Plugin implementation language:** Go is allowed/expected for independent Example and OpenAMSM Plugins.
**Source:** ca-agent-demo Python implementation and the audit documents in this repository.
**Status:** task package for implementation; no code implementation is claimed by this document.

## 0. Mandatory preflight

Read README.md, Agent.md, docs/architecture.md, docs/audit/ca-agent-demo.md, docs/audit/reuse-and-feasibility.md, docs/plugin-package.md, docs/plugin-artifact-handoff.md, docs/acceptance.md, [技能目录与编译器运行时接口设计说明书](../集成设计/技能目录与编译器运行时接口设计说明书.md) and [DeepSeek Harness 实施提示词](../实施计划/DeepSeek%20Harness实施提示词.md).

Before coding:

1. Confirm current branch and clean working tree.
2. Record current ca-agent-next HEAD.
3. Keep Agent Core Python. Do not create Go Agent/Host/Runtime modules.
4. Treat ca-agent-demo as read-only source. Do not modify it.
5. Treat ca-skill-compiler, ca-client-tools, ca-skills, ca-openamsm-plugin and ca-agent as read-only dependencies unless the user separately authorizes a cross-repository change.
6. Do not start OpenAMSM/Nsmf migration. The first target is Echo.
7. Read current CA-SL v1alpha5 and Compiler release contracts. CA-SL refresh PR #88 is OPEN; Compiler v2.1.0 does not establish `contract.when` or Python CheckedExpr interoperability. Compiler Issue #61 tracks a new Development Artifact Manifest v1alpha2 while preserving frozen v1alpha5 and Development v1alpha1 contracts. First complete the Go cel-go → Python cel-expr-python CheckedExpr/DescriptorSet PoC and Compiler PR; only then unblock Next Assurance import/Resolver. SKILL.md-only import is Host-owned and bypasses Compiler. Do not strip fields, fake Compiler success or implement a second Compiler in Python.

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

Do not add package signatures, Trust Registry, extra SHA-256 snapshot hashing, separate Provider Manager, filesystem watchers or generic Plugin hot reload. SkillCatalog explicit import/update is a separate Core-owned lifecycle.

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

**External dependency gate:** [Compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) must deliver a reviewed Development Artifact Manifest v1alpha2, standard CheckedExpr Any + DescriptorSet, and real Python CEL interoperability. The CA-SL refresh [PR #88](https://github.com/odango-chan/ca-skills/pull/88) must be merged and its exact normative SHA pinned before claiming final language conformance. Do not modify frozen v1alpha5 or Development v1alpha1 contracts. SKILL.md-only import is a Next-owned Importer path and bypasses Compiler, so it can be implemented independently. If the Compiler release/artifact is unavailable, keep Assurance source import and Resolver integration BLOCKED; do not silently strip when or claim the old release is compatible.

**Acceptance:** SKILL.md-only import succeeds without Compiler invocation; Assurance source uses the released Artifact v1alpha2 and passes Inspect/Verify + Host Admission; compiled Artifact import does not Build; invalid Assurance fails closed; import/update builds a candidate Catalog generation and atomically activates only after success. Phase C remains blocked until Compiler Issue #61 and CA-SL PR #88 gates are satisfied. Detailed interchange contract: [技能目录与编译器运行时接口设计说明书](../集成设计/技能目录与编译器运行时接口设计说明书.md).

## 5. Phase D — Skill Resolver and mode derivation

**Allowed changes:** ca-agent-next only.

Implement:

1. Resolve exact continuations before fresh Skill selection.
2. Resolve from the active immutable in-memory SkillCatalog generation pinned for this fresh Event. Do not scan package directories or reread SKILL.md/Assurance files on the Event hot path; do not use deployment-owned Event→Skill tables or business Contract Packages.
3. For Assurance Skills, use the Catalog's already deserialized CEL Expression (loaded from Artifact v1alpha2 CheckedExpr Any and DescriptorSet by `cel-expr-python`) against this Event's normalized event.type and input. Compiler parses/type-checks once during Build; Python loads the CheckedExpr once during Catalog import/update. Every fresh Event gets a new activation and independent evaluation; do not cache the boolean result. Static invalidity is a Compiler error; false and runtime evaluation error exclude the Skill.
4. If exactly one explicit true match exists, select it without LLM. If multiple true matches exist, offer only those candidates to the LLM.
5. If no explicit true match exists, form semantic candidates from unguarded Skills (no when), using cached candidate metadata derived from SKILL.md. This includes SKILL.md-only Skills and Assurance Skills whose Contract omits when. After selection, provide the full SKILL.md content from Catalog memory; do not reread the package file.
6. Never reintroduce a false/error guarded Skill into the unguarded set. Validate the exact Skill identity returned by the model.
7. Derive supported modes from Assurance presence/validity. No Assurance means LLM-guided only; valid Assurance means both modes; invalid Assurance means import failure. Do not add supportedModes.
8. Select execution mode only after exact Skill binding.

**Acceptance:** EX-09/EX-10/EX-11 and EX-21/EX-22/EX-23/EX-27/EX-29 pass with deterministic fake Model client; Compiler-generated CheckedExpr is deserialized once by Python and matches Go/G.4 fixtures; no business-specific route configuration; false/error candidates are excluded and out-of-set IDs rejected. The Resolver uses only the pinned Catalog snapshot and never invokes Compiler or filesystem reads during selection.

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
2. Add Echo Acceptance Tests for EX-01 through EX-19 and EX-21 through EX-29. Reserve EX-20 for Phase G's OpenAMSM second-business proof.
3. Exercise Event → Skill import/selection → Run → Tool → Outcome/Evidence → response delivery.
4. Exercise SKILL.md-only import, Assurance source import, compiled Artifact import, and LLM Skill Authoring.
5. Exercise Catalog residency, no per-Event file reads/Compiler calls, compile-once/evaluate-per-Event behavior, duplicate/continuation bypass, atomic update, failed-update rollback, generation pinning and lazy references (EX-21–EX-28).
6. Exercise the same Assurance-backed Skill in both modes.
7. Exercise the individual LLM Action path without Compiler.
8. Remove unused scaffolding, duplicated registries and obsolete adapters.
9. Update docs and record exact test commands/results.

**Acceptance:** Echo cases EX-01–EX-19 and EX-21–EX-29 pass or are explicitly BLOCKED by the external Compiler Artifact contract; Python Core remains business-neutral; one Plugin process supports Event, Delivery and Tools. EX-20 is completed in Phase G.

## 8. Phase G — OpenAMSM Plugin contract and integration

Start only after the Generic Echo vertical E2E passes. OpenAMSM is the second independent business used to prove that the same Core accepts a new Plugin/Skill/Tool package without business-specific Core code.

Tasks:

1. Align ca-openamsm-plugin with docs/plugin-package.md and docs/plugin-artifact-handoff.md. The Next documents are the sole target contract; do not reuse ca-agent-demo's ca-agent-host.plugin/v0 protocol.
2. Implement SBI HTTP/2 ingress, normalized Event publication, multipart/Content-ID parsing, raw N1/N2 artifact handoff and response Delivery in the independent Go Plugin. For shared operations such as UpdateSMContext, extract only the minimal NAS discriminator needed to normalize the Event type, reusing the shared codec implementation; do not eagerly deep-decode every NAS/NGAP IE for business reasoning or choose the Skill in the Plugin.
3. Use ca-client-tools v1.2.0 as the OpenAMSM Tool Plugin through the one Plugin Manager tools extension adapter. Keep its provider/v2 translation inside that manager; do not create a second Provider Manager.
4. Add Codec Tool operations to that existing tools extension only after the operation and Schema are published in the canonical Interface Package. Reuse the accepted Go codec package/Worker/Facade; do not create a separate Codec Plugin/Manager or duplicate decoding in Host/Event Plugin.
5. Import the existing Establish, Modify and UE-requested Release Skills from ca-skills. Do not copy business procedures into the Plugin or Agent Core.
6. Freeze the exact mapping from OpenAMSM OpenAPI operations and normalized Event fields to Skill when selectors. In particular, distinguish UE-requested PDU Session Release from network-initiated ReleaseSMContext.
7. Implement Host-owned inbound/outbound N1/N2 staging using docs/plugin-artifact-handoff.md. Do not use Base64, a Plugin database, extra SHA-256 or a new Artifact service.
8. Preserve Host Run lifecycle, response obligations, resource mapping, Owner Receipt/Commit Proof, UNKNOWN and exact-original Reconcile semantics.
9. Make Codec invocation Skill-driven: no-decode Skills pass original artifactRefs to business Tools; Skills needing protocol fields call Codec through the common Runtime Action Boundary. Keep the original bytes unchanged for forwarding and response composition.

**External gates:** ca-skills PR #88 remains OPEN until rechecked. Compiler Issue #61 must produce the versioned Artifact and Python CEL interoperability before any Assurance `when` conformance claim. ca-client-tools PR #39 is OPEN with Phase B final pass and Phase C not started. Do not claim a dependency is merged/released or a codec message is qualified unless the exact evidence exists.

**Acceptance:** OM-01 through OM-10 and OM-13/OM-15 pass on fixtures and exact protocol vectors before live E2E. The OpenAMSM Plugin contains no Skill selection, Owner operation map, RunStore, Runtime or authorization logic.

## 9. Phase H — Real OpenAMSM Create → Modify → Release E2E

Run only after Phase G contract and integration tests pass.

1. Use one real isolated OpenAMSM Owner/SMF and one UE/PSI.
2. Run Create, then Modify, then UE-requested Release through the new Next Host and Go Plugin.
3. Preserve the original N1/N2 bytes and Content-ID associations through Host ArtifactStore and Provider invocation.
4. Prove the Release continuation resumes the exact original Run and generation using N1 Release Complete (0xD4) and N2 PDU Session Resource Release Response where applicable.
5. Verify Owner Receipt/Commit Proof/Reconcile, terminal state, response Location/status and no duplicate mutation.
6. Keep synthetic Owner acceptance separate from real isolated Owner evidence.

**Acceptance:** OM-11 passes with a real isolated Owner. Synthetic G5 or offline fixture tests do not satisfy this gate. No Production Qualification is claimed.

The current authorization covers documentation alignment in ca-agent-next and ca-openamsm-plugin. Cross-repository implementation code changes require their own explicit phase authorization.

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
- Do not start OpenAMSM implementation before Echo acceptance. OpenAMSM itself is the second-business zero-Core-change proof.
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
