# DeepSeek Harness implementation plan

**Target repository:** `odango-chan/ca-agent-next` only.  
**Agent Core language:** **Python**.  
**Plugin implementation language:** Go is allowed/expected for independent Example and OpenAMSM Plugins.  
**Source:** `ca-agent-demo` Python implementation and the audit documents in this repository.  
**Status:** task package for implementation; no code implementation is claimed by this document.

## 0. Mandatory preflight

Read `README.md`, `Agent.md`, `docs/architecture.md`, `docs/audit/ca-agent-demo.md`, `docs/audit/reuse-and-feasibility.md` and `docs/acceptance.md`.

Before coding:

1. Confirm current branch and clean working tree.
2. Record current `ca-agent-next` HEAD.
3. Keep Agent Core Python. Do not create Go Agent/Host/Runtime modules.
4. Treat `ca-agent-demo` as read-only source. Do not modify it.
5. Treat `ca-skill-compiler`, `ca-client-tools`, `ca-skills`, `ca-openamsm-plugin` and `ca-agent` as read-only dependencies for this task.
6. Do not start OpenAMSM/Nsmf migration. The first target is Echo.

## 1. Target architecture

Build one Python Agent Core and one Plugin Manager. A Plugin is one extension package/process and may expose:

- `event.ingress`: Plugin publishes normalized Event;
- `event.delivery`: Host returns a structured response to the originating Plugin;
- `tools`: Plugin exports callable operations.

A Tool is an operation exported by a Tool Plugin, not a separate process/manager/runtime. One Plugin may expose both Event and Tool extensions. Tool Interface Package remains the authority for callable ID, IO schemas, Effect, Capability membership and Owner outcome semantics.

Every business Event must resolve a Skill first using Formal-first selection. Only after exact Skill binding may the Host choose Deterministic or LLM-guided mode. Both modes submit the same Runtime Action Request to the same Runtime Action Boundary and Tool Plugin dispatch.

## 2. Phase A — Python Core skeleton and dependency map

**Allowed changes:** `ca-agent-next` only.  
**Source reference:** selected Python modules in `ca-agent-demo`; do not copy the repository wholesale.

Tasks:

1. Establish Python package, CLI entrypoint, configuration model and pytest layout.
2. Define the minimum generic contracts: Plugin identity/lifecycle, generic IPC envelope, extension descriptor, Event envelope, Task/Run reference, Runtime Action Request/Result, Tool result and structured response.
3. Define interfaces before concrete implementations; no business names in Core.
4. Selectively port the Intent/model boundary and Formal/Context primitives identified in the audit. Do not port `MockCompiler` or treat `MockRuntime` as final.
5. Keep a small dependency graph; no premature framework or abstract factory layers.

**Acceptance:** Python import/build and focused pytest pass; no Go Agent Core files; no business-specific routing table.

## 3. Phase B — Unified Plugin Manager and Echo Plugin

**Allowed changes:** `ca-agent-next` only.

Implement:

1. One Plugin Manager for process start/stop, handshake, IPC framing, correlation and extension discovery.
2. One generic Plugin manifest containing Plugin identity and extension declarations.
3. Event ingress/delivery extension.
4. Tool extension with operation dispatch. Tool Interface Package is imported by reference/digest; Plugin manifest does not duplicate ToolCatalog.
5. One Go Echo Plugin process exposing both `event.ingress` / `event.delivery` and at least one Tool operation.
6. Keep Plugin process independent of Python imports. Use stdio/NDJSON for Host IPC; external listener is not required for Echo.

**Acceptance:** Python Host starts one Go process, discovers both extension kinds, receives Event, invokes Echo Tool through Runtime, delivers a structured response to the same Plugin process, and shuts down cleanly. No separate Provider Manager.

**Migration note:** Existing `ca-client-tools.provider/v2` may later be adapted behind the Tool extension driver. Do not change or copy the Go repository in this phase.

## 4. Phase C — Package import and Formal-first Skill Resolver

**Allowed changes:** `ca-agent-next` only.

Tasks:

1. Import Plugin Event Contract and Skill/domain business-contract packages from their package-owned sources.
2. Make Skill applicability declarations part of the Skill package.
3. Implement Formal candidate filtering using exact contract reference, input Schema, applicability, Host Base Capability Envelope, Context requirements and available Artifact/Variant.
4. Implement 0/1/N behavior: 0 stop/ask; 1 direct select; N formal disambiguation; LLM fallback only for unresolved ambiguity within the eligible set.
5. Validate exact selected Skill package/artifact identity.
6. Do not implement Event→Skill config or Event→Mode config.

**Acceptance:** EX-05/EX-06 pass with deterministic fake Model client; no LLM call for 0/1/formally-resolved candidate cases; out-of-set candidate is rejected.

## 5. Phase D — Compiler integration and exact Artifact binding

**Allowed changes:** `ca-agent-next` only; consume external `skillc v2.1.0`.

Tasks:

1. Add a small Python subprocess client for pinned `skillc` commands.
2. Import exact Interface Package snapshots and Dependency Lock for Echo Tool interface.
3. Build/check/verify the Echo Skill using the real Go Compiler.
4. Implement/port only Host-side exact Artifact/Variant admission and Capability binding; verify source digest, package digest and Compiler identity.
5. Keep Compiler build/verify separate from Runtime authorization.

**Acceptance:** Echo Skill compiles with released `skillc v2.1.0`; Python Host loads the exact output Artifact; tampered source/artifact/interface snapshot is rejected. Do not copy Compiler Go source.

## 6. Phase E — One Runtime Action Boundary and two execution modes

**Allowed changes:** `ca-agent-next` only.

Tasks:

1. Implement one Python Runtime with Skill Run identity, exact Artifact/Capability binding, Action Request validation, authorization, Tool Plugin dispatch, Outcome/Evidence and basic Wait/Resume semantics.
2. Deterministic Procedure Engine derives the next Action from the validated Procedure.
3. LLM-guided Host Model Loop proposes the next Action from Skill-scoped Context.
4. Both paths submit the same Action Request to the same Runtime method and same Plugin Tool extension.
5. READ Tools produce Observation facts with provenance; MUTATION Tools preserve Owner Receipt/Commit Proof semantics where required.
6. No direct Agent→Plugin call, no duplicate Provider dispatcher and no second authorization path.

**Acceptance:** same Echo Skill succeeds in Deterministic and LLM-guided modes; traces show both entering the same Runtime Action boundary and same Tool Plugin operation. Unauthorized Capability and forged COMMITTED cases fail.

## 7. Phase F — Example-first regression and cleanup

**Allowed changes:** `ca-agent-next` only.

1. Make Echo a runnable Example under `examples/`.
2. Add automated Acceptance Tests for EX-01–EX-13.
3. Remove unused scaffolding, duplicated registries and obsolete adapters.
4. Update docs and record exact test commands/results.
5. Do not introduce production DFX or multi-tenant security frameworks.

**Acceptance:** all Echo acceptance tests pass; Example runs without external credentials; Python Core remains business-neutral.

## 8. Phase G — OpenAMSM integration (later, not part of Echo MVP)

Start only after Echo acceptance and review.

- Use `ca-openamsm-plugin` as Event Plugin for SBI ingress/delivery.
- Use `ca-client-tools v1.2.0` as Tool Plugin through the unified Plugin Manager; adapt its current Provider v2 protocol rather than copying its Go code.
- Consume `ca-skills` Create/Modify/Release CA-SL v1alpha5 packages.
- Invoke `ca-skill-compiler v2.1.0` from Python.
- Keep Nsmf Run lifecycle, RunStore, resource mapping, Host Artifact Store and Runtime outside the Event Plugin.
- Preserve Owner Receipt, Commit Proof, UNKNOWN and exact-original Reconcile semantics.
- Do not claim live Scheme C or Production Qualification unless the isolated real environment gate is executed.

This phase may require a later cross-repository contract alignment PR. Do not edit sibling repositories as part of the Echo MVP.

## 9. Explicit prohibitions

- Do not change Agent Core from Python to Go.
- Do not copy `ca-skill-compiler` or `ca-client-tools` Go source into next.
- Do not create a separate permanent Provider Manager alongside Plugin Manager.
- Do not create a second ToolCatalog or central business Goal Registry.
- Do not add Event→Skill or Event→Mode mapping tables.
- Do not let an Event bypass Skill selection.
- Do not let LLM invoke Plugins directly or declare Owner commit.
- Do not move NsmfRunExecutor, Owner claims, Receipt/Reconcile, or Skill Runtime into `ca-openamsm-plugin`.
- Do not start T3/OpenAMSM before Echo mechanism acceptance.
- Do not claim a test PASS unless the command was actually run and its output recorded.

## 10. Final report required from each phase

Report:

- changed files and commit;
- exact Python/Go commands executed and results;
- which Example case proves the mechanism;
- whether any external repository was modified (expected: no);
- remaining UNKNOWN/NOT_RUN gates;
- whether the next phase can start without changing the architecture.
