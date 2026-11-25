# MVP acceptance

**Status:** architecture baseline documented; implementation **NOT_STARTED**; acceptance **NOT_RUN**.

This file defines the Demo-level proof required before the architecture is treated as implemented. It is intentionally a small mechanism checklist, not a production qualification plan.

## 1. Example-first rule

Every newly introduced externally observable extension or execution mechanism must add a **new runnable Example case** and an automated Acceptance Test in the same change set.

Examples are stored in this repository under `examples/`. A separate `ca-example` repository is not needed now.

An Example must exercise the public mechanism boundary as an independent consumer would. It must not import Agent `internal` packages or rely on business-specific Agent Core code.

An internal refactor that introduces no new externally observable mechanism does not need a new Example.

## 2. First vertical Example: Echo

Build one small Echo domain that can exercise the full path:

```text
examples/
  echo/
    contracts/       # Echo-owned business contract and payload schema
    plugin/          # independently runnable Go Plugin
    skill/           # independently importable Echo Skill package
    provider/        # Echo Tool Provider and binding
    scenarios/
      deterministic/ # same Skill, fixed Procedure
      llm-guided/    # same Skill, Agent chooses next Action
      selection/     # 0 / 1 / ambiguous N candidate cases
tests/
  acceptance/
    echo_test.go
```

Adjust the layout to the actual implementation; do not create empty directories just to match this sketch.

The Echo business contract belongs to the Echo example/package, not to shared mechanism contracts. The Plugin emits a generic envelope containing a reference to that contract and its payload; it does not name an Echo Skill. The Skill declares applicability to the Echo contract. The Provider exposes an atomic Tool through the shared Runtime Action Boundary.

Use a stub/fake Model client in automated tests so the selection and LLM-guided paths are reproducible without API credentials. A real-model smoke test may be added later, but is not required for the first mechanism acceptance.

## 3. Required acceptance cases

| ID | Mechanism | Required proof |
|---|---|---|
| EX-01 | Plugin loading and ingress | An independently built Go Plugin is loaded through the Plugin boundary and sends a valid Event. No Agent Core business code is added. |
| EX-02 | Package/Skill discovery | Host discovers the imported Echo Skill package from the available package set. No central business registry or Event-to-Skill mapping is used. |
| EX-03 | Formal-first Skill Selection | Zero candidates stops/asks for input; one candidate is selected without LLM; multiple candidates are first handled formally; only unresolved ambiguity invokes LLM with the eligible set. Invalid/out-of-set LLM choices are rejected. |
| EX-04 | Mode selection | Execution mode is selected only after exact Skill selection and is constrained by the Skill's supported modes. No Event-to-Mode mapping exists. |
| EX-05 | Deterministic execution | A validated Echo Procedure is bound to an exact Artifact/Variant and progressed by the Runtime Procedure Engine. |
| EX-06 | LLM-guided execution | The Agent receives Skill-scoped Context and proposes an Action; it cannot call the Provider directly or widen the Skill's Capabilities. |
| EX-07 | Shared Runtime Action Boundary | Deterministic and LLM-guided scenarios reach the same Action Request validation/dispatch path and the same Provider binding. |
| EX-08 | Context provenance | The model-visible Context distinguishes Plugin Event input, Tool READ Observation, Skill declarations, and Runtime Evidence with lightweight source references. |
| EX-09 | Provider extension | A new Echo Provider/Tool can be added through its package/binding without business-specific Agent Core changes. |
| EX-10 | End-to-end response | Event → Task → Skill → Run → Owner/Provider result → Host response → Plugin delivery completes for both execution modes. |

The exact test names may differ, but each case must be executable and linked from the implementation change.

## 4. Selection behavior to test

### Skill Selection

| Formal result | Expected behavior |
|---|---|
| 0 eligible Skills | Stop or request missing input. No LLM routing call. |
| 1 eligible Skill | Select it directly. No LLM routing call. |
| N candidates, formal rule yields one | Select the formal result. No LLM routing call. |
| N candidates remain ambiguous | LLM may choose only among those eligible candidates; Host validates the exact identity. |

### Procedure Selection

Apply the same Formal-first rule within the selected Skill. Any LLM proposal must be revalidated and resolved to an exact, validated Procedure Artifact/Variant before deterministic execution.

Test all supported Procedure source paths used by the implementation:

- `STATIC`;
- `LLM_PROPOSAL`;
- `FALLBACK`;
- `PATCH-DERIVED`.

Fallback is allowed only when the selected published deterministic Procedure explicitly declares fallback eligibility. Unresolved facts, unresolved UNKNOWN, or no eligible fallback must stop.

### Execution modes

The same selected Echo Skill must be runnable in:

- Deterministic mode: Procedure Engine chooses the next node.
- LLM-guided mode: Agent/LLM chooses the next Action.

Both must call the same Runtime Action Boundary. An LLM-assisted Skill/Procedure selection test must remain distinct from an LLM-guided execution test.

## 5. Definition of Demo acceptance

The architecture MVP is accepted when:

1. EX-01 through EX-10 pass in the repository's automated acceptance suite.
2. The same Echo Skill can run through both modes.
3. Both modes use the same Runtime Action boundary and Provider path.
4. Adding the Example Plugin, Skill, or Provider does not require business-specific Agent Core changes.
5. Each mechanism's Example and test are runnable from a documented command.

This is a mechanism demonstration only. It does not claim production readiness, real OpenAMSM qualification, or cross-Host parity.

## 6. Explicit non-goals

Do not add these merely to make the Demo look production-ready:

- high availability, distributed failover, or multi-region operation;
- complex multi-tenant isolation or enterprise IAM/security governance;
- elaborate DFX, SLO dashboards, or a production observability platform;
- Marketplace, central business Goal Registry, or distributed Event Bus;
- complex saga/compensation orchestration;
- broad legacy protocol/version compatibility;
- a separate `ca-example` repository.

Keep basic schema validation, clear failure messages, minimal correlation, and useful logs. If a later requirement truly needs one of the excluded areas, re-scope it explicitly instead of quietly expanding this Demo.
