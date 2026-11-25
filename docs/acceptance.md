# MVP acceptance

**Status:** architecture documented; implementation **NOT_STARTED**; acceptance **NOT_RUN**.  
**Language:** Python Agent Core; independent Go Example Plugin.  
**Scope:** Demo-level mechanism proof only.

## 1. Example-first rule

Every new externally observable mechanism must add a new runnable Example case and automated Acceptance Test in the same change set. Examples live under `examples/`; no separate `ca-example` repository.

Examples consume the public Plugin/Skill/Runtime boundaries and must not import Agent Core internals. An internal refactor with no new externally observable mechanism does not need a new Example.

## 2. First vertical Example: Echo

One independently running Go Plugin exposes both an Event extension and a Tool extension. The Python Agent Core consumes the Event, selects a Skill formally, then executes the same Skill in two modes.

Suggested layout (adapt to actual code; do not create empty folders):

```text
examples/echo/
  contracts/             # Echo-owned business contract and Event payload schema
  plugin/                # standalone Go Plugin: event.ingress + event.delivery + tools
  skill/                 # one Echo Skill; declares business-contract applicability
  interface/             # Echo Tool Interface Package and Schemas
  scenarios/
    deterministic/       # same Skill, validated static Procedure
    llm-guided/          # same Skill, model proposes next Action
    selection/           # 0 / 1 / ambiguous N candidate cases
tests/
  acceptance/
    test_echo_plugin.py
```

The Plugin manifest references the Echo-owned business contract and its Event Schema. It does not name the Echo Skill. The Skill declares that it supports the Echo business contract and declares the Echo Tool Capability. The Plugin exports the Echo Tool operation; it does not authorize its own invocation.

Use a deterministic fake Model client in tests. A real-model smoke test is optional and is not a gate for the first mechanism proof.

## 3. Required acceptance cases

| ID | Mechanism | Required proof |
|---|---|---|
| EX-01 | Python Host | Host, Agent loop, Resolver and Runtime run as Python modules; no Go Agent Core is introduced. |
| EX-02 | Plugin lifecycle | Python Plugin Manager starts one independent Go Plugin process, completes handshake, correlates frames and shuts it down. |
| EX-03 | Unified extensions | The same Plugin process exposes Event ingress/delivery and Tool invocation; one manager discovers and routes both. |
| EX-04 | Event contract import | Host loads the Plugin-owned Event manifest/Schema and validates a normalized Event. No event-specific Host handler. |
| EX-05 | Skill package discovery | Host discovers imported Skill packages and matches business-contract references against Skill applicability; no central business registry or Event→Skill map. |
| EX-06 | Formal-first Skill selection | Exercise every case in the selection table, including out-of-set model results. |
| EX-07 | Execution mode | Mode is selected only after exact Skill binding and is constrained by that Skill's supported modes. |
| EX-08 | Deterministic execution | Compiler-validated Artifact/Variant is executed by the deterministic Procedure Engine. |
| EX-09 | LLM-guided execution | Agent receives Skill-scoped Context and proposes Actions; cannot call Plugin directly or widen Capability. |
| EX-10 | Shared Action boundary | Both modes enter the same Runtime Action Request, authorization, Tool Plugin dispatch and outcome path. |
| EX-11 | READ Observation provenance | READ Tool result becomes an Observation with Tool/Package/Invocation/Result provenance; it is not confused with model text. |
| EX-12 | Mutation outcome | A MUTATION Tool cannot become COMMITTED from HTTP success or LLM text; Owner Receipt/Commit Proof is required where its Interface Package says so. |
| EX-13 | End-to-end delivery | Event → Task → Skill → Run → Tool Plugin → result/evidence → Host response → originating Plugin delivery succeeds in both modes. |
| EX-14 | Plugin package | Load a valid installed Echo package. Reject a malformed manifest, escaping entry point, changed snapshot and handshake mismatch without registering extensions. |
| EX-15 | Continuation | Resume the exact pending Run with original bindings. Duplicate and invalid deliveries cause no new selection or execution advance. |
| EX-16 | Business neutrality | Add a second independently owned Event/Skill/Interface fixture by installing packages and changing deployment inputs only. Validate exact contract matching, candidate isolation and Capability-scoped dispatch with the same Host build. |
| EX-17 | Lightweight Skill | A lightweight Contract can carry `when` and execute LLM-guided with trusted session authorization. Check that its route grants no Tool permissions. Verify an unchanged legacy Skill and a complete Contract with `when` against the declared compatibility path. |

## 4. Selection and mode behavior

### Skill Selection

| Formal outcome | Required behavior |
|---|---|
| One eligible explicit true match | Select directly with no model call |
| Multiple eligible explicit true matches | Offer only exact matching candidates to the model |
| Zero explicit true matches | Offer only eligible unguarded candidates, including a singleton |
| Empty applicable tier | Stop or request missing input |
| False, malformed CEL or evaluation error | Exclude the guarded Skill and report errors |
| Continuation | Resume the original Run before selection or return an appropriate invalid/duplicate result |

### Execution mode

- Skill is always selected first.
- Deterministic and LLM-guided are the only two execution modes.
- LLM-assisted Skill selection does not imply LLM-guided execution.
- The selected Skill's declared supported modes constrain the choice.
- Both modes use the same Runtime Action Boundary and Tool Plugin.

### Procedure source

The first Demo gate covers `STATIC`. Add a runnable Example and acceptance test with each subsequent Procedure source. All executable Procedures pass deterministic validation, Compiler build and exact Artifact/Variant binding.

## 5. Compiler and Tool Plugin integration

- Python invokes a pinned `skillc v2.1.0` executable for check/build/verify; no Go Compiler source is copied.
- Echo Tool Interface Package is consumed by Compiler and Runtime from the same immutable package bytes.
- Tool Plugin process is loaded through the unified Plugin Manager.
- During initial integration, a Tool-Plugin driver may adapt `ca-client-tools.provider/v2`; it must not introduce a separate permanent Provider Manager or Tool authorization path.

The Echo example may use its own tiny Go Tool Plugin. It does not require a live OpenAMSM deployment or production Provider credentials.

## 6. Definition of Demo acceptance

Accept the architecture MVP only when EX-01 through EX-17 pass, the same Skill runs in both modes, the same Plugin process supports both Event and Tool extensions, and no business-specific Agent Core code is needed to add the Example.

This does not claim live OpenAMSM qualification, production readiness or complete 3GPP protocol parity.

## 7. Explicit non-goals

Do not add production HA, distributed failover, complex multi-tenant/security governance, Marketplace, central business registry, distributed Event Bus, separate artifact database, complex compensation orchestration, broad legacy compatibility or elaborate DFX merely to pass the Demo.
