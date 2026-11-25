# ca-agent-demo implementation audit

**Audit date:** 2026-11-25  
**Primary source:** `odango-chan/ca-agent-demo` main `57e277ff9094dad93543df46910a12a1dbbaf560`.  
**Additional review inputs:** PR #246 head `68a6f9e7723a0c2da1aebf5047c23ae96c5d237f` (OPEN); PR #249 head `dfbcc33467a1ea3b6fa45d661ac2e77bfd71423a` (OPEN).  
**Classification:** EVIDENCE = directly observed source/status; INFERENCE = assessment; PROPOSAL = next implementation direction.

## 1. Repository status and lineage

- **EVIDENCE:** Main README identifies the repository as a Generic Agent Host reference implementation, Python distribution `ca-agent-host`, import package `ca_agent_host`, current architecture version `0.4.0`, with one execution chain. It describes 5GC as a business/Integration example, not Host identity.
- **EVIDENCE:** Main HEAD is `57e277ff9094dad93543df46910a12a1dbbaf560`. The current main tree has Python `src/ca_agent_host/`, `tools/`, `skills/`, `examples/`, and pytest tests.
- **EVIDENCE:** Main README links `docs/design/generic-agent-host-architecture.md` as normative for the current tree and `docs/design/ca-agent-host-v0.5-plugin-architecture.md` as a next-version design target, not implemented.
- **INFERENCE:** `ca-agent-demo` is the right source for next's Python Core. Its current tree is already generic in package naming, but it contains historical and business-specific composition that must be audited at file level rather than copied by directory.
- **PROPOSAL:** Start next from selected modules/tests in this Python repository; do not start from `ca-agent`'s Go source.

## 2. Mechanism inventory

| Mechanism | Current evidence | State | Next disposition |
|---|---|---|---|
| Intent/Agent model boundary | `src/ca_agent_host/agent/intent/{interpreter,model_adapter,stub}.py`; `agent/model_adapter.py`, `model_request.py`; `tests/unit/test_intent_ingress.py` | Implemented in Demo | Reuse/adapt Python model boundary; keep model loop in Host/Agent |
| Formal search and plan binding | `agent/formal/{search,grounding,operators,ranking,resolver,strategy}.py`; `tests/unit/test_runtime_preconditions.py`, `test_skill_context.py` | Implemented, but selection layers differ from target | Reuse formal machinery selectively; add explicit package/Skill applicability Resolver |
| Root/Skill eligibility | `agent/host/root_eligibility.py`, `routing.py`, `root_routing_profile.py`; `tests/unit/test_resident_deployment_routing.py` | Implemented with deployment routing | Reuse eligibility concepts; replace structured Event→Root routing with package-owned applicability |
| LLM ambiguity selection | `agent/host/routing.py` (`SkillRoutingChooser`) and `agent/semantic/chooser.py` | Partly implemented | Adapt to strict Formal-first candidate restriction and exact identity validation |
| Context/Observation | `agent/context/{base,loader,projection,requirements,observation_resolver}.py`; `runtime/observation/{model,source}.py`; `tests/unit/test_skill_context.py` | Implemented | Reuse types/resolver ideas; simplify provenance model for next |
| Skill Artifact admission | `runtime/admission.py`, `runtime/compiler_artifact.py`, `runtime/compiler_skill.py`, `runtime/skill_assets.py` | Implemented Host-side checks | Reuse/adapt artifact admission and exact identity; align to Compiler v2.1.0 package/artifact contracts |
| Compiler implementation | `skill_toolchain/compiler.py` defines `MockCompiler`; `runtime/compiler_artifact.py` loads/admit artifacts | External compiler not embedded in this Python package | Do not treat MockCompiler as production compiler; invoke released Go skillc |
| Procedure linking | `runtime/linker.py`, `runtime/frozen.py`, `runtime/casl_adapter.py`; `tests/unit/test_compiler_skill_graph.py` | Implemented in Demo | Reuse only the generic runtime lowering/linking pieces needed after real Compiler artifact admission |
| Runtime execution | `runtime/engine.py` defines `MockRuntime`; `runtime/outcomes.py`, `runtime/evidence_wait.py`, `runtime/durable.py` | Demo implementation with mock-named engine and durable semantics | Reuse semantic boundaries and tests; build/simplify next's one Runtime rather than copy all code blindly |
| Tool Action boundary | `runtime/tool_contract.py` (`ToolContractRegistry`, `ToolBoundOperationBackend`); main test `tests/unit/test_unified_resident_action.py`. `test_tool_composition.py` is added on PR #246's open branch. | Implemented generic boundary | Strong reuse candidate; refactor backend target from Provider adapter to unified Plugin Tool extension |
| Host/Resident lifecycle | `resident/{host,service,invocation,delivery,ingress}.py` | Implemented | Reuse basic lifecycle/API; avoid copying 5GC composition and overgrown recovery machinery |
| Run / Artifact storage | `resident/run_store.py`, `artifact_store.py`; `tests/unit/test_durable_runtime.py`, `test_createdsession_resident_journal_durability.py` | Implemented with SQLite/content-addressed artifact mechanics | Reuse only minimal Task/Run correlation and Host artifact custody needed by Echo/T3 |
| Provider integration on main | `integrations/ca_client_tools/{provider_v2,mas_typed}.py`; `tests/unit/test_mas_typed_provider.py` | Present on main, includes a domain-specific MAS adapter | Do not carry MAS-specific tables/adapters into next |
| Generic Tool Plugin loader | PR #246 adds `src/ca_agent_host/providers/{manifest,interface,process,runtime,backend,service,runtime_bindings}.py`, plus `runtime/tool_composition.py` and Resident integration | Implemented on an OPEN branch, not main | Review and absorb into one Plugin Manager; do not create separate Provider Manager |
| Plugin Event ingress/delivery | PR #249 adds design docs only; no Plugin runtime source in main | Design only | Implement as Event extension of unified Plugin mechanism |
| 5GC SBI/Nsmf integration | `integrations/fivegc/nsmf_*.py`, `namf_relay*.py`, `nsmf_run_executor.py` in PR #246 | Mixed protocol and Host lifecycle responsibilities | Split by ownership; do not move whole directory to Plugin |
| Trace/diagnostics | `observability/{events,store,progress,projections,diagnostics}.py` | Implemented | Reuse minimal trace events useful for Demo debugging; avoid production observability platform |

## 3. Important incompatibilities with the target

### 3.1 Existing Event routing is not the target Skill Resolver

- **EVIDENCE:** `agent/host/root_routing_profile.py` parses a deployment-owned `StructuredEventRoute` with contract version/message type/request type; `root_eligibility.py` calls `match_structured_route()` before building eligible Roots.
- **INFERENCE:** This is a structured Event→Root route, even if the Skill itself is not hardcoded in Plugin code. It does not implement the desired package-owned Skill applicability model.
- **PROPOSAL:** In next, Event package declares business-contract reference + payload Schema; Skill package declares supported contract/applicability. Formal Resolver matches packages and filters candidates. No per-event Host mapping table.

### 3.2 Current Agent-first Plugin proposal conflicts with Skill-first

- **EVIDENCE:** PR #249 describes Generic LLM Agent as default Event consumer and CA-SL Skill as optional; PR #249 is design-only and OPEN.
- **EVIDENCE:** User's current target requires Skill selection first, Formal-first; only unresolved candidate ambiguity falls back to LLM; execution mode is selected after Skill binding.
- **PROPOSAL:** Do not copy PR #249's Agent-default/Skill-optional execution flow into next. Reuse its useful generic Event/Plugin/Artifact ideas only after adapting the flow to Skill-first.

### 3.3 Current Runtime and Compiler naming is not proof of real compiler integration

- **EVIDENCE:** `skill_toolchain/compiler.py` defines `MockCompiler`; `runtime/engine.py` defines `MockRuntime`. `agent/host/orchestrator.py` imports both in its current orchestration path.
- **INFERENCE:** These are valuable mechanism prototypes, but not substitutes for the released Go Compiler or a fully separated production runtime implementation.
- **PROPOSAL:** Integrate `skillc v2.1.0` as an external tool; keep Python Host admission and Runtime semantics separate.

## 4. PR/Issue evidence and status

| Reference | Current status | What it proves | What it does not prove |
|---|---|---|---|
| Issue #241 | OPEN | Tool subsystem cutover task | Final accepted live Scheme C gate |
| PR #246 | OPEN, head `68a6f9e` | Generic Provider loader, Interface Package loader, Runtime-only bindings, one ToolComposition; local G5 synthetic Owner evidence | Live isolated OpenAMSM Scheme C E2E; merge/production qualification |
| Issue #235 | OPEN | Deferred Plugin ingress/delivery scope after Tool P0 | Plugin runtime implemented |
| PR #249 | OPEN, head `dfbcc334`, docs-only | Event Contract, Plugin IPC/manifest and T2/T3 design proposals | Plugin runtime or T2/T3 PASS |

PR #246 comments record G5 as **22 passed** with a synthetic stateful Owner; real isolated Scheme C G6 remains **NOT_RUN/BLOCKED**. The PR also records Open5GS local Tool migration as partial. Do not turn synthetic G5 into a live OpenAMSM claim.

PR #246 review identifies the new generic Python loader modules under `providers/` and the single `ToolComposition`; these are review inputs, not merged main code. Main `57e277ff` does not contain that generic Provider cutover.

## 5. Reuse map

- **Reuse/adapt:** Python Agent/model adapter, Formal search/grounding, Context Loader, Skill Artifact admission, generic Tool contract validation, Outcome/Evidence semantics, minimal Run/Artifact store.
- **Refactor:** Skill selection to package applicability; Tool dispatch to Plugin Tool extension; Runtime/Host split; Context provenance.
- **Do not copy wholesale:** `integrations/fivegc/`, NsmfRunExecutor, current structured Event routing, `MockCompiler` as a real compiler, `MockRuntime` as an assumed final engine.
- **Do not migrate external Go projects into Python:** `ca-skill-compiler` and `ca-client-tools` remain independent executables/packages.

This audit is a source/status review, not a fresh execution of the Demo test suite. Test evidence is attributed to the cited PR/review records and exact test files.
