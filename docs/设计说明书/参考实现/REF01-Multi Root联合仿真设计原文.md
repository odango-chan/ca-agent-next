> 迁移来源：ca-agent-demo/docs/design/multi-root-joined-simulation.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：多 Root、统一 Tool Registration 与 joined simulation 设计  
> 迁移追踪：ca-agent-next Issue #12。该仓是 Python Generic Agent Host 参考实现，不是 Next 目标架构的自动实现证明。

---

# Multi-Root Joined Simulation — Seam and Acceptance Matrix

- **Status:** implemented and executed (2026-11-11) for the mechanism matrix below; package-level clean-wheel independence is still pending.
- **Normative architecture:** [generic-agent-host-architecture.md](generic-agent-host-architecture.md).
- **Acceptance test:** `tests/integration/test_multi_root_joined_simulation.py`.
- **Example bundles:** `examples/fivegc_joined/`, `examples/non_5gc_joined/`, `examples/skills/edge-cache-warmup/`.

## 1. What the simulation proves

One Generic Resident Host serves **two Roots from different business domains in the same deployment**:

| Root | Source | Domain |
| --- | --- | --- |
| `establish-pdu-session` | repository `skills/` | 5GC PDU Session |
| `edge-cache-warmup` | `examples/skills/` (explicit example source root) | edge cache |

The simulation uses the real production mechanisms — generic v0.5 deployment loader, exact artifact Admission, shared Link/Admission core, Tool contract registry + manual registration validator, Root-scoped scripts, invocation-scoped Operation allowlist, per-Root readiness gate and the single Runtime. Only the Tool implementations and observation sources are local deterministic example code.

It does **not** prove live 5GC behavior, real Fabric/Provider wiring, or production qualification of the example Skill. Those remain out of scope.

## 2. Seam map

### 2.1 Example deployment and composition (`examples/fivegc_joined/`)

| File | Role |
| --- | --- |
| `deployment.py` | Builds/writes the example v0.5 deployment document (`configVersion`, `rootSkills`, `skillSourceRoots`, `rootRouting`, `journal`, `lifecycleBinding`, `integration`), and loads it through the real generic `load_resident_deployment` with an injected example integration loader. |
| `composition.py` | Composition root: loads the admitted closure for both Roots, builds Tool contract/capability catalogs (production + example), loads the one union registration, constructs the Host service (`HostService`), readiness probe, ingress and delivery, and returns `JoinedSimulationWorld`. |
| `local_fivegc_tools.py` | Local deterministic 5GC Tool operations and observation sources used only for the example (declared but not a production implementation). Also exposes `WAIT_SPECS` used to prove per-Root wait derivation. |
| `observations.py` | Example observation sources for the two Roots' refs. |

### 2.2 Example assets (`examples/non_5gc_joined/`, `examples/skills/`)

| Path | Role |
| --- | --- |
| `examples/skills/edge-cache-warmup/` | Example-only executable Root Skill (`SKILL.md`, `assurance/*`, `schemas/*`, `scripts/*`, `references/*`). |
| `examples/non_5gc_joined/tool-contracts/edge-cache.tool.yaml` | Example-only Tool contract: three Operations with input/output schemas and expected Effects. |
| `examples/non_5gc_joined/tool-contracts/capabilities/edge-cache.capabilities.yaml` | Example-only Capability → Operation contract. |
| `examples/non_5gc_joined/tool-registration.yaml` | **The one** deployment-level union registration: all 12 5GC Operations + the three example cache Operations. |
| `examples/non_5gc_joined/tools/local_cache.py` | Example-only in-memory deterministic implementation (`example.local.cache_store`), injected via `ToolImplementationCatalog`; never imported from configuration text. |
| `examples/non_5gc_joined/joined-simulation/runner.py` | Example composition-root entry point for the bundle; it is example data, not a second Host/executor. The accepted Joined Simulation mechanism evidence is the test below, which composes via `examples/fivegc_joined/`. |

The one union registration source is verified by the test (`len(*registration*.yaml) == 1`). `tools/registrations/default.yaml` remains the production registration; the example file is deployment input for this simulation, not a second production authority.

## 3. Per-Root readiness and isolation

- `ResidentHost.preflight()` publishes `root_ready` / `root_reasons` for each declared Root plus deployment-level `ready`.
- The test deliberately removes one 5GC implementation (`createdsession.pcf_hold`) and asserts:
  - `root_ready[establish-pdu-session] is False` with a reason containing `OPERATION_BACKEND_MISSING:ca.session.pcf_hold.bind`;
  - `root_ready[edge-cache-warmup] is True`;
  - the Host remains READY (another Root can serve);
  - the 5GC invocation fails closed at Root eligibility and never executes;
  - the cache Root still executes successfully.
- A missing dependency therefore isolates to the Root that requires it; it must not take down the whole deployment or leak a default Skill's assets into the other Root.

## 4. Isolation dimensions

| Dimension | Mechanism | Evidence |
| --- | --- | --- |
| Scripts | `resident/root_scripts.py` — one `RootScopedScriptBackend` per admitted Root artifact; executing a script identity outside the current Root's allowlist raises `RootScriptDispatchError`. | `test_scripts_wait_specs_and_observations_are_bound_to_the_selected_root` (cache script rejected under the 5GC Root lineage; each Root's backend resolves its own artifact) |
| Wait specs | Derived per selected exact artifact, not from a Service default Skill. | same test: 5GC wait specs non-empty; cache wait specs `{}` |
| Observations | Observation refs come from each Root's admitted artifact / deployment observation adapters; a Root cannot request another Root's refs. Tool output is never injected as observation evidence. | same test: 5GC observation requests never start with `edge_cache.`; cache requests are within its two declared refs |
| Capabilities / Operations | Invocation-scoped allowlist from the selected artifact (`runtime/capability_scope.py`). | `test_invocation_operation_allowlist_denies_cross_root_dispatch`: cache allowlist = `{cache.object.read, cache.object.upsert, cache.propagation.read}`; 5GC allowlist disjoint; a cache invocation restricted to `sbi.udm.sm_data.get` terminates `UNRESOLVED`; the same linked procedure succeeds with its own allowlist |
| Tool registration | One deployment-level union; per-Root subset derived from the exact artifact. | `test_two_...` (single registration file) and `test_union_registration_and_effect_mismatch_fail_closed` |
| Skill source root | Explicit `skillSourceRoots`; example Skill invisible without it. | `test_example_skill_is_invisible_without_an_explicit_source_root` |
| Production / examples | Production package imports nothing from `examples/` or `tests/`; only `cli/main.py` may use the guarded optional import. | `test_production_package_has_no_example_or_test_dependency` |

## 5. Acceptance matrix

Executed evidence (2026-11-11, current working tree):

```bash
$env:UV_CACHE_DIR="$PWD\.uv-cache"; uv run --no-sync pytest -q tests/integration/test_multi_root_joined_simulation.py
# 7 passed, 2 warnings in 7.59s
```

| # | Acceptance requirement | Test | Status |
| --- | --- | --- | --- |
| 1 | One Host, two different-domain Roots both READY and both execute through the single chain; two completed invocations; one registration file only. | `test_two_different_domain_roots_are_ready_and_execute_through_one_host` | PASS (executed 2026-11-11) |
| 2 | One Root NOT_READY does not block the other; 5GC fails closed at eligibility; cache still succeeds. | `test_one_root_not_ready_does_not_block_the_other_root` | PASS (executed 2026-11-11) |
| 3 | Root-scoped scripts, wait specs and observations; no cross-Root reuse; Tool output is not observation evidence. | `test_scripts_wait_specs_and_observations_are_bound_to_the_selected_root` | PASS (executed 2026-11-11) |
| 4 | Invocation-scoped Operation allowlist denies cross-Root dispatch; same procedure succeeds with its own allowlist. | `test_invocation_operation_allowlist_denies_cross_root_dispatch` | PASS (executed 2026-11-11) |
| 5 | Union registration binds the allowed-Root Operation union; missing Operation, unknown implementation and Effect mismatch fail closed. | `test_union_registration_and_effect_mismatch_fail_closed` | PASS (executed 2026-11-11) |
| 6 | Example Skill is invisible without an explicit source root and admits normally with one. | `test_example_skill_is_invisible_without_an_explicit_source_root` | PASS (executed 2026-11-11) |
| 7 | Production package has no `examples/` or `tests/` imports; CLI is the only guarded composition-root exception. | `test_production_package_has_no_example_or_test_dependency` | PASS (executed 2026-11-11) |
| 7b | Examples-removal independence of the installed product: wheel does not package `examples/`, and an installed `ca-plan` still imports/starts and serves `version` / `host`. | clean-wheel smoke (no repository `examples/` on path) | **PENDING** |

`<!-- EVIDENCE: run the clean-wheel install smoke on the final tree; record wheel name, venv path, import/resource/CLI output. Do not mark 7b PASS before it is executed. -->`

## 6. What remains explicitly example-only

- `edge-cache-warmup` is not a production Skill, is not packaged into the wheel, and is not a Root candidate for any production deployment. Promoting it requires a separate production review and a move into the normal Skill asset authority.
- The example Tool contract/registration/implementation are deployment inputs for this simulation only; they are never discovered automatically and never become part of the production Tool catalog.
- The Joined Simulation is local deterministic evidence. It is not a live 5GC, Fabric or Provider acceptance run.
