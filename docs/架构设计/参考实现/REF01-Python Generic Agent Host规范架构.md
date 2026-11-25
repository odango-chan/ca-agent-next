> 迁移来源：ca-agent-demo/docs/design/generic-agent-host-architecture.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 源文档定位：REF01 Python Generic Agent Host 当前 main 规范架构  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# Generic Agent Host — Normative Architecture

- **Status:** Normative for the current tree (2026-11-11). Supersedes all 5GC / CreatedSession-specific architecture documents.
- **Repository role:** runnable reference implementation of a Generic Agent Host, not a 5GC product demo.
- **Companion documents:** [Package identity](package-identity.md), [Multi-Root Joined Simulation](multi-root-joined-simulation.md), [Execution routes](execution-routes.md), [Current snapshot](../WORK.md), [Traceability](../TRACEABILITY.md).
- **Task history / convergence record:** [Generic Agent Host final convergence Goal](../work/generic-agent-host-final-convergence-20261110.md).
- **Next-release design only:** [CA Agent Host v0.5.0 Plugin Architecture](ca-agent-host-v0.5-plugin-architecture.md). This does not supersede the current-tree architecture before implementation and acceptance.

> Historical documents under `docs/design/` (5GC, CreatedSession, runtime-mechanism reuse) are evidence only. They are not authoritative for names, directories or execution paths. See the banner on each historical file.

## 1. Identity

| Item | Value |
| --- | --- |
| GitHub repository | `odango-chan/ca-agent-demo` (unchanged) |
| Local checkout root | `ca-agent-demo` (unchanged) |
| Python distribution | `ca-agent-host` |
| Import package | `ca_agent_host` under `src/` |
| Wheel runtime data root | `share/ca-agent-host` |
| Console script | `ca-plan = ca_agent_host.cli.main:main` |
| Project version | `0.4.0` (`pyproject.toml` / package metadata) |
| Repository target | Generic Agent Host reference implementation |

The pre-refactor identity `ca-agent-demo` / `ca_agent_demo` / `share/ca-agent-demo` is retired with no compatibility shim (no import alias, no re-export package, no old resource directory). Details and collision-check evidence are in [package-identity.md](package-identity.md).

PDU Session, 5GC, Fabric SBI, UDM/PCF/AMF/N1-N2/N4 are **business and Integration sample vocabulary**. They may appear in Skills, Agent-side Tool contracts, Integrations, examples, and domain tests; they must not become Generic Host / Runtime identity or default branches.

## 2. Component boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| Skill (`skills/`, example Skills under `examples/skills/`) | business Goal, Procedure, Predicates, Scripts, Schemas, References, declared Capabilities | generic Runtime safety gates, external owner state, second execution authority |
| Agent (`agent/`) | intent understanding, Root candidate selection, Planning V2 preparation, model interaction | un-admitted Runtime steps, authoritative side-effect facts |
| Host / Resident (`resident/`) | deployment contract, composition seam, request lifecycle, invocation, concurrency/ordering, readiness publication, shutdown/drain | business rules, protocol-specific state machines, Tool implementations |
| Runtime (`runtime/`) | Admission, Link, frozen execution, Tool dispatch, Effect, budgets, Observation/Wait/Reconcile, terminal outcomes | business branches, PDU Session / CreatedSession defaults |
| Agent-side Tools (`tools/`) | Tool Operation contracts (input/output/Effect), Capability → Operation contracts, manual registration, Agent-side implementations/adapters | external server state, Skill business rules, Runtime authority |
| Integrations (`integrations/`) | consumer adapters for external protocols/services and domain composition | external server authority, a second Host/Service/Runtime |
| Observability (`observability/`) | Trace events, recorder, persistence, projections, diagnostics | business success truth |
| CLI (`cli/`) | command entrypoints, terminal presentation, guarded example-command bridge | execution authority |
| `examples/` | example Skills, scenarios, deployment profiles, Tool contract fixtures, local deterministic Tools, Joined Simulation composition | production Host/Service/Ingress/Runtime/Tool registry, test fixtures |
| `tests/fixtures/` | test-only doubles and fixtures | production runtime inputs |
| `support/` | narrow cross-component adapters (`canonical`, `assets`, `strict_document`, `trace_stage`) | any canonical owner contract |

Canonical owner repositories remain the authority for Agent, Runtime, Skill Toolchain, Tool contracts and external owners. This repository holds reference implementations, not a second source of truth.

## 3. One execution chain

There is exactly one production Invocation path. A claimed request is normalized, routed against the deployment's allowed Roots, admitted with request-specific eligibility/READY, resolved to the selected exact Root artifact, prepared either by Direct Entry or by Planning V2, then executed by the shared Link/Admission core and the single Runtime.

```text
Ingress adapter
  -> normalized Host request
  -> deployment Root routing (allowed Roots / structured event routes)
  -> exact Admission + per-request eligibility / per-Root READY
  -> selected exact Root artifact
  -> Direct Entry  OR  Planning V2 preparation
  -> shared Link / Admission core
  -> one Invocation / Runtime
  -> Agent-side Tool
  -> Integration adapter
  -> external owner / business system
  -> Observation / Wait / Reconcile
  -> terminal disposition / delivery / shutdown lifecycle
```

Invariants:

- No legacy configured-Skill executor and no second execution branch. `run_createdsession_agent` and `CreatedSessionAgentService` are gone; `configs/component-map.yaml` lists them as forbidden source patterns.
- Only the current deployment contract version `ca-agent-host.resident-deployment/v0.5` is accepted. `ca-agent-host.resident-deployment/v0.3` and `/v0.4` are explicitly rejected by `resident/deployment.py`; there is no migration, adapter or fallback.
- The generic deployment loader validates the generic envelope and hands the domain `integration` object to an injected Integration loader. The Generic Host never invents a domain.
- Direct Entry and Planning V2 may differ in upstream preparation, but both converge on `runtime/linker.py`'s shared Link/Admission core and the same Invocation/Runtime lifecycle.
- No Service-level default Skill may provide scripts, wait specs, Tool readiness or observation requirements to another Root.

Key modules for the chain:

- normalization / routing: `agent/host/ingress.py`, `agent/host/routing.py`, `agent/host/root_routing_profile.py`, `agent/host/root_eligibility.py`
- admission / link: `runtime/admission.py` (`load_admitted_closure`), `runtime/linker.py` (`compile_link_admit_skill_entry`, shared core)
- execution: `runtime/engine.py`, `runtime/tool_contract.py`, `runtime/evidence_wait.py`, `runtime/outcomes.py`
- invocation/lifecycle: `resident/invocation.py`, `resident/service.py`, `resident/host.py`, `resident/ingress.py`, `resident/delivery.py`
- domain composition for the current 5GC sample: `integrations/fivegc/composition.py` (`build_fivegc_resident_host`, `load_fivegc_resident_host`)

## 4. Root routing, Admission and readiness

- The deployment declares its allowed Roots (`rootSkills`, optional `rootRouting`). `agent/host/root_routing_profile.py` parses and freezes the v0.5 routing profile; `root_eligibility.py` computes exact-candidate eligibility and stable reason codes.
- Admission is exact and per request. `runtime/admission.py` loads the admitted closure for the selected Skill identities; capability coverage, scripts, schemas, references, wait specs and observation requirements all come from the selected exact artifact.
- Readiness is per Root. `ResidentHost.preflight()` returns `root_ready` / `root_reasons` per Root and a deployment-level `ready`. A missing Operation backend, script, wait spec or observation source makes only the dependent Root NOT_READY; the Host can still be READY when at least one declared Root is READY.
- Root selection never falls back to "all HTTP requests", "intent absent", or a fixed business Skill. Unknown / ambiguous / NOT_READY cases fail closed.
- The READY publication signal is `AGENT_HOST_READY` (`resident/host.py`). The historical `CREATEDSESSION_RESIDENT_READY` signal no longer exists.

## 5. Multi-Root model

One Resident deployment can serve several Roots from different business domains. The model is **deployment-level union + invocation-level exact subset**:

1. **One union Tool registration per deployment.** The deployment reads exactly one manual registration file (`tools/registrations/default.yaml` for the production composition; `examples/non_5gc_joined/tool-registration.yaml` for the example Joined Simulation). It binds the union of Operations required by all allowed Roots. There is no per-Root registration, per-Root backend or per-Root executor.
2. **One deployment Capability contract union.** Capability → Operation mappings and Tool expected Effects are validated by the same `ToolContractRegistry` / `CapabilityContractRegistry` mechanisms.
3. **Per-Root READY.** Each Root's coverage is derived from its selected exact artifact; missing dependencies isolate to that Root.
4. **Invocation-scoped Operation allowlist.** `runtime/capability_scope.py` (`admitted_operation_allowlist`) derives the exact Operation set from the selected artifact's declared Capabilities/Operations and the deployment Capability contracts; `resident/capability_scope.py` re-exports it for the Resident side. The Runtime rejects dispatch outside the current invocation's allowlist, so Root A cannot call Root B's Operations.
5. **Root-scoped local-compute scripts.** `resident/root_scripts.py` (`RootScopedScriptBackend`) keeps one governed script backend per admitted Root artifact and rejects a script identity outside the executing Root's allowlist.
6. **Per-Root observations and wait specs.** Wait requirements are derived from the selected exact artifact (`runtime/evidence_wait.py` + domain wait derivation); Observation refs come from each Root's admitted artifact and the deployment's observation adapters. Tool output is never injected as observation evidence.
7. **Explicit Skill source roots.** The v0.5 deployment may declare `skillSourceRoots`; example Skills are visible only when an explicit example source root is configured and admitted through the normal loader. There is no `if examples/` branch and no auto-discovery.

Acceptance evidence for this model: [multi-root-joined-simulation.md](multi-root-joined-simulation.md) and `tests/integration/test_multi_root_joined_simulation.py`.

## 6. Directory ownership map

Verified from the current tree:

```text
src/ca_agent_host/
├── __init__.py
├── agent/
│   ├── domain.py, model_adapter.py, model_config.py, model_request.py
│   ├── host/           # routing, root eligibility, root routing profile, planning gate,
│   │                   # predefined, replan, execution_dag, goal_lowering,
│   │                   # semantic_frontier, skill_context, ingress, orchestrator,
│   │                   # scenario_host, routing_model; prompts/, schemas/
│   ├── intent/         # interpreter, model_adapter, stub, fixtures
│   ├── formal/         # search, operators, grounding, ranking, resolver, strategy,
│   │                   # predicate_dependencies
│   ├── semantic/       # chooser, model_adapter, stub
│   └── context/        # loader, projection, offers, requirements,
│                       # observation_resolver, predicate_resolver
├── runtime/            # admission, linker, engine, tool_contract, capability_contract,
│                       # capability_scope, coverage, governed_script, predicate_engine,
│                       # evidence_wait, frozen, identity, linked, outcomes, world, ...
│                       # observation/{model,source}
├── skill_toolchain/    # compiler, proposal, proposal_builder, digest, yamlutil
├── resident/           # host, composition, service, deployment, invocation, delivery,
│                       # ingress, lock, root_scripts, capability_scope
├── observability/      # events, store, progress, projections, diagnostics
├── cli/                # main.py, trace/render.py, trace/tui.py
├── integrations/       # fivegc, env_fabric, ca_provider_5gc, env_5gc_sim, tool_common
└── support/            # assets, canonical, strict_document, trace_stage

tools/                  # Agent-side Tool layer
├── contracts/          # *.tool.yaml; capabilities/*.capabilities.yaml
├── registrations/      # default.yaml + README
├── adapters/open5gs/   # Agent-side 5GC Tool implementations/compositions
├── registration.py     # manual registration loader / validator
├── capabilities.py     # Capability contract loader
└── transport/http.py

examples/               # example-only, never packaged, never imported by production
├── skills/edge-cache-warmup/
├── scenarios/
├── fivegc/
├── deployment-profiles/
├── non_5gc_joined/     # tool contracts, union registration, local deterministic Tool, runner
└── fivegc_joined/      # joined composition: composition.py, deployment.py,
                        # local_fivegc_tools.py, observations.py

skills/                 # Skill assets (production copy for the sample + prototype mirror)
planning/               # planning surfaces
tests/                  # unit, integration, e2e, scenarios, support, fixtures, contracts
configs/                # component map + example deployment/model profiles
scripts/                # validation, acceptance and verification utilities
```

## 7. Package, wheel and resource layout

`pyproject.toml` (setuptools backend) is the packaging authority:

- packages: `ca_agent_host`, `ca_agent_host.*`, `tools`, `tools.*` from `src` and `.`
- wheel data files under `share/ca-agent-host/`: Tool contracts and registrations, Toolchain schema snapshot, planning surfaces, and the packaged Skill assets (`5gc-file-transfer`, `ensure-pdu-session`, `ensure-session-qos`, `ensure-virtual-group`, `ue-registration`, `5gc-intent`, `establish-pdu-session`)
- package data: `ca_agent_host.agent.host` YAML/prompt/schema files, `ca_agent_host.integrations.ca_provider_5gc` pinned contracts, `ca_agent_host.integrations.env_fabric` pinned contracts, `tools.adapters.open5gs` README

The wheel does **not** package `examples/`. Installed production code resolves Skill/Tool resources from the installed package and `share/ca-agent-host`; it never depends on the repository checkout. See [package-identity.md](package-identity.md) for verification commands and the pending clean-wheel smoke evidence.

## 8. CLI surface

Production commands:

```text
ca-plan version [--json]
ca-plan host preflight --deployment PATH [--tool-registration PATH] [--skill SKILL] [--json]
ca-plan host serve     --deployment PATH [--tool-registration PATH] [--skill SKILL] [--preflight-only]
```

Example-only commands (available only when the repository `examples/` assets are importable):

```text
ca-plan run --scenario ... [--profile ...] [--owner-profile ...] [--intent ...] ...
ca-plan scenario list|show|check ...
ca-plan owner-profile list|show ...
ca-plan show RUN_ID [--tui|--detail|--raw]
```

`src/ca_agent_host/cli/main.py` is the single documented composition-root exception: it loads example-only command modules behind a guarded optional import (`_EXAMPLES_AVAILABLE`). An installed wheel without `examples/` still starts and exposes `version` and `host`; `run`/`scenario`/`owner-profile`/`show` print a clear "requires repository examples/" error instead of failing at import time. The `ca-plan` command name is unchanged.

## 9. Non-goals

- Not a 5GC Agent, CreatedSession service, or PDU-Session-specific product; 5GC remains the primary business/Integration sample.
- No v0.3/v0.4 deployment compatibility layer, migration adapter or fallback executor.
- No second Host, Service, Resident, Runtime, Tool registry or side-effect authority.
- No per-Root Tool registration/backend split.
- No automatic discovery of example Skills; no production dependency on `examples/` or `tests/`.
- No full LLM Skill executor in this increment; Planning V2 / Intent understanding / Root routing remain the supported model-assisted surfaces and future LLM execution must reuse the same Invocation/Tool/Journal/Runtime/Reconcile lifecycle.
- No modification of external owner repositories or the Fabric SBI wire contract.
- No claim of live 5GC acceptance; real 5GC Live E2E remains a separately authorized gate (`NOT_RUN` in this increment).

## 10. "Production never imports examples/tests" rule

This is a hard rule, not a convention:

- `configs/component-map.yaml` declares `productionMayImportExamples: false`, `productionMayImportTests: false`, `examplesArePythonProductionPackage: false`, `testFixturesAreProductionAssets: false`, and `architectureGuards.forbiddenSourcePatterns` includes `from examples`, `import examples`, `from tests`, `import tests`.
- `scripts/validate_docs.py` scans every `src/ca_agent_host/**/*.py` and fails on those patterns. The only allowed exception is `src/ca_agent_host/cli/main.py`, and only because its example imports are guarded by `_EXAMPLES_AVAILABLE` (an installed wheel without `examples/` still imports and starts).
- `tests/integration/test_multi_root_joined_simulation.py::test_production_package_has_no_example_or_test_dependency` asserts the same property and verifies the CLI guard.
- Example behavior is data + composition only: example Tool contracts, registration, local deterministic implementation and the Joined Simulation composition root live under `examples/` and inject themselves into the real generic Host; they never provide a second execution mechanism.

## 11. Verification

Local gates for the current tree:

```bash
uv sync
uv run --no-sync python scripts/validate_docs.py
uv run --no-sync pytest -q -m "not live_model"
git diff --check
```

Packaging gates:

```bash
uv build --wheel
# then install the wheel into a clean venv and run:
#   python -c "import ca_agent_host; import ca_agent_host.cli.main"
#   ca-plan version
#   ca-plan host preflight --deployment <v0.5 deployment>
```

Evidence status is tracked in [WORK.md](../WORK.md) and [TRACEABILITY.md](../TRACEABILITY.md). Do not report a gate as PASS unless the exact command was executed on the stated tree; clean-wheel install evidence is currently pending (see [package-identity.md](package-identity.md)).
