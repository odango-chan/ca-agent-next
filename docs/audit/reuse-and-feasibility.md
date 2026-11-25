# Reuse and feasibility audit

**Audit date:** 2026-11-25.  
**Target:** Python Agent Core in `ca-agent-next`; independent Go Plugins.  
**Rule:** preserve independently owned mature projects as dependencies; reuse Python source from `ca-agent-demo` selectively.

## 1. Repository snapshot

| Repository | Observed baseline | Language / release | Current evidence | Decision |
|---|---|---|---|---|
| `ca-agent-demo` | main `57e277ff9094dad93543df46910a12a1dbbaf560` | Python; `ca-agent-host 0.4.0` per main README | Existing Python Agent/Host/Runtime/Resident/Context; PR #246 adds generic Provider path; PR #249 is Plugin design only | Primary source for selective Python reuse |
| `ca-agent-next` | main `952a23f8303f5f6cfaff4a88e63de214d856252b`; PR #1 head `9c55d3cb01cb1721ec6f10bfbb06ba5baf48ed77` | Target Python; currently docs-only | No implementation files on main | New Python implementation workspace |
| `ca-agent` | main `447d0cce7e42c7c1184b11fb2563792eead68d51` | Go | Stable existing implementation | Promotion target, not source |
| `ca-skill-compiler` | main `255ab85fa5abb4b0bf36656bf64250cafebf45cb` | Go; latest release **v2.1.0** | Stateless compiler; CLI + Go/WASM Worker; CA-SL v1alpha5; Build/Verify and Development Build/Verify | Direct external executable/API dependency; do not copy |
| `ca-client-tools` | main `7bcb2614aa3615d8358df31eecefd0909e894e40` | Go; latest release **v1.2.0** | Provider v2 process, one Go-owned Tool source, Compiler Interface Package, runtime binding sidecar | Tool Plugin dependency; do not copy |
| `ca-skills` | main `b06f72baae3eb3d578c489f950a325e2d63d556f` | CA-SL v1alpha5 sources/spec and Python validation tests | Contains Establish, Modify and Release MAS Skill examples and lifecycle/compiler-gate tests | Import/use Skill packages; no business logic copied to Host |
| `ca-openamsm-plugin` | main `eb83c8f2e83dbcdc56b484126b2acf9e8f2a7397` | No implementation language detected; README only | PR #1 is OPEN/DRAFT design proposal, head `7940f733`; no Go implementation files on main | Future Go Event Plugin; implementation not started |
| `ca-agent-demo` PR #246 | head `68a6f9e7723a0c2da1aebf5047c23ae96c5d237f` | Python Host + Go Provider | G5 synthetic Owner 22 passed; G6 live Scheme C NOT_RUN/BLOCKED | Review/adapt the generic loader; do not assume merged |
| `ca-agent-demo` PR #249 | head `dfbcc33467a1ea3b6fa45d661ac2e77bfd71423a` | Docs-only | Proposed Plugin Contract v0 and Event path | Reuse concepts, not Agent-default/Skill-optional flow |

## 2. Mature project reuse decisions

### 2.1 ca-skill-compiler — direct external dependency

**EVIDENCE**

- Latest release is Go `ca-skill-compiler v2.1.0`; main `255ab85f`.
- README describes a deterministic, stateless compiler with one Go Core powering native CLI and Go/WASM Worker.
- Supported CA-SL target is `connectionagent.io/v1alpha5`.
- CLI provides frozen `check` / `build` / `inspect` / `verify` and Development `build-development` / `verify-development`.
- Compiler validates static source, links supplied immutable Interface Packages and emits deterministic Artifacts. It does not execute Tools, grant Host admission or qualify Owner behavior.

**DECISION — direct dependency, no code copy**

- Python Host invokes a pinned `skillc` executable as a subprocess for check/build/inspect/verify.
- Pass exact source roots, Interface Package snapshots and Dependency Lock; capture structured output and exit status.
- Host separately admits the exact Artifact/Variant and binds Capability requirements to the selected Run.
- Do not copy Go Compiler packages into next; do not reimplement compiler linking/validation in Python.
- Existing Demo `runtime/compiler_artifact.py` and `runtime/compiler_skill.py` are candidate Python Host-side Artifact admission/lowering adapters, not a replacement Compiler. Audit/adapt them against v2.1.0 output before reuse.
- Start with native CLI. Do not add WASM integration unless the actual deployment requires browser execution.

### 2.2 ca-client-tools — Tool Plugin, direct external dependency

**EVIDENCE**

- Latest release is Go `ca-client-tools v1.2.0`; main `7bcb2614`.
- `go.mod` declares module `github.com/odango-chan/ca-client-tools`.
- `docs/provider-protocol-v2.md` defines a long-lived stdio/NDJSON process with `initialize`, `catalog`, `invoke`, `cancel`, request correlation and negotiated bounds.
- `contracts/provider-bindings/v2/provider-bindings.yaml` is the Go-owned canonical Tool source. Release generates a Compiler Interface Package and runtime `provider.yaml` from that source.
- v1.2.0 publishes 11 public READ Tools and 2 Capabilities in the Interface Package, plus a separate Runtime-only sidecar with 25 bindings (21 MUTATION + 4 READ) under the exact Host scope contract. These are not 25 public Compiler Tools.
- The Go Provider owns SBI transport, typed OpenAMSM clients, private argument projection and Owner calls. Host/Runtime own Skill Capability authorization, Run identity and final outcomes.

**DECISION — Tool Plugin, do not copy or translate**

- Treat `ca-client-tools` as a Plugin exporting the `tools` extension.
- Plugin manifest references the exact Interface Package and runtime binding package/digest; it does not duplicate ToolCatalog.
- Use the existing Go executable and published package. No Go-to-Python translation.
- Initial next implementation may adapt `ca-client-tools.provider/v2` behind the unified Plugin Manager's Tool extension driver. This avoids rewriting a mature released protocol while preventing a separate Provider Manager/Runtime.
- Keep the Interface Package as the Tool contract authority and Runtime as the only authorization/outcome authority.
- Do not move OpenAMSM Tool implementation into `ca-openamsm-plugin`.

**Current integration caveat:** ca-agent-demo PR #246 is still OPEN. It reports G5 synthetic Owner 22 passed, but live Scheme C G6 remains NOT_RUN/BLOCKED; its generic Provider loader is a branch input, not mainline accepted code.

### 2.3 ca-skills — package import, not Host code

**EVIDENCE**

- Main `b06f72ba` publishes CA-SL v1alpha5 and includes `establish-pdu-session-mas`, `modify-pdu-session-mas` and `release-pdu-session-mas` source examples.
- Tests include `tests/test_compile_mas_v1alpha5.py` and `tests/test_mas_lifecycle_procedures.py`.
- README states that linking/running the examples requires trusted Owner contracts and deployment bindings; examples do not claim live qualification.

**DECISION**

- Consume Skill packages through the generic package/Compiler path.
- Do not copy Create/Modify/Release business logic into Agent Core.
- Echo is the first mechanism proof; OpenAMSM Skills are a later real-domain integration.

### 2.4 ca-openamsm-plugin — Event Plugin, not a Tool Provider

**EVIDENCE**

- Main `eb83c8f2` contains only README (one tree entry); no implementation code.
- PR #1 is OPEN/DRAFT, head `7940f733`, and proposes a standalone Go Event Plugin using `ca-agent-host.plugin/v0`, SBI ingress, protocol normalization and response delivery.
- Its current PR description says Generic LLM Agent is default and CA-SL Skill is optional. That conflicts with the user's latest Skill-first rule and must be corrected before implementation.
- PR #1 currently says `ca-client-tools` remains the sole Tool Provider; the next target architecture proposes representing it as a Tool Plugin under the same Plugin Manager.

**DECISION**

- Keep the repository independent and Go.
- It implements `event.ingress` and `event.delivery`, not MAS Owner Tools, Skill selection, RunStore or Runtime.
- Align its process/extension contract with the unified Plugin mechanism before writing implementation.
- Do not copy the whole Nsmf/Run execution chain from Demo.

## 3. What may be copied from ca-agent-demo into next

The following means selective Python source reuse after tests/import review, not an instruction to copy entire directories.

| Demo source | Recommendation | Why / work |
|---|---|---|
| `agent/intent/`, model adapter/request types | **COPY + ADAPT (S)** | Python Agent boundary already exists; strip Demo-specific composition |
| `agent/formal/{search,grounding,operators,ranking}` | **COPY + ADAPT (M)** | Useful deterministic reasoning primitives; new package-applicability resolver still required |
| `agent/host/root_eligibility.py`, `routing.py` | **ADAPT (M)** | Reuse candidate/exclusion types; replace structured Event→Root mapping and enforce LLM candidate restriction |
| `agent/context/`, `runtime/observation/` | **COPY + ADAPT (M)** | Useful read-only resolver and fact/provenance model; simplify |
| `runtime/tool_contract.py`, `runtime/outcomes.py` | **COPY + ADAPT (M)** | Strong existing shared Tool validation and outcome boundary; dispatch target becomes Plugin Tool extension |
| `runtime/compiler_artifact.py`, `runtime/compiler_skill.py` | **ADAPT (M)** | Host Artifact admission, not Compiler; verify against v2.1.0 |
| `runtime/linker.py`, `runtime/frozen.py`, `runtime/casl_adapter.py` | **REVIEW/ADAPT (L)** | Large dependency surface; retain only the exact CA-SL v1alpha5 integration needed after compiler artifact admission |
| `resident/invocation.py`, basic `resident/service.py` | **ADAPT (M)** | One Run/Invocation path; remove business composition and duplicate direct path |
| `resident/run_store.py`, `artifact_store.py` | **ADAPT (M)** | Reuse only minimum Task/Run correlation and Host-managed artifact custody needed by Demo |
| `observability/events.py` | **COPY/ADAPT (S)** | Lightweight trace events useful for VibeCoding acceptance |
| `integrations/fivegc/` and Nsmf Run executor | **DO NOT COPY WHOLESALE** | Mixed protocol, Host lifecycle, resource map and business orchestration; later split by ownership |
| `skill_toolchain/compiler.py` (`MockCompiler`) | **DO NOT USE AS REAL COMPILER** | Mock cache/proposal compiler only |
| `runtime/engine.py` (`MockRuntime`) | **REVIEW, DO NOT ASSUME FINAL** | Mock-named Demo engine; extract the Procedure/action semantics into next's single Runtime |
| PR #246 `providers/` loader and `ToolComposition` | **ADAPT INTO PLUGIN MANAGER (M/L)** | Valuable generic package/process/interface loading; absorb Tool process lifecycle, do not preserve separate Provider manager |
| PR #249 Plugin docs | **DESIGN INPUT ONLY** | Event/manifest/artifact ideas useful; Agent-default/Skill-optional flow is superseded |

## 4. Copy / dependency summary

| Asset | Action |
|---|---|
| Python Agent Core from ca-agent-demo | Selective source copy/adaptation into next |
| ca-skill-compiler Go source | **Do not copy**; invoke pinned release binary |
| ca-client-tools Go source | **Do not copy**; load pinned Tool Plugin release |
| ca-skills business Skill sources | Import/package; only create Echo Skill under next examples for first mechanism proof |
| ca-openamsm-plugin | Keep independent; align contract before implementation |
| ca-agent Go source | Do not copy; promotion target only |

## 5. Feasibility and critical gaps

**Overall: FEASIBLE**, with staged implementation. The external Compiler and Tool Provider are already independent release artifacts; Python Core can orchestrate them without sharing language/runtime.

Critical work:

1. **Unify Plugin/Tool extension management.** Current PR #246 has a generic Provider Manager/ToolComposition; PR #249 proposes a separate Plugin Manager. Next should have one Plugin Manager with Event and Tool extension kinds.
2. **Resolve Skill-first conflict.** PR #249 and ca-openamsm-plugin PR #1 currently describe Agent-default/Skill-optional. Next must implement Formal-first Skill selection for every business Event.
3. **Replace Event→Root mapping.** Current Demo `structuredEventRoutes` is not the target package-owned applicability model.
4. **Integrate real Compiler.** Demo's `MockCompiler` is not enough; call skillc v2.1.0 and admit exact Artifacts.
5. **Simplify Resident/Runtime.** Current Demo includes Nsmf-specific execution and durable recovery; Echo should prove the common mechanism without copying all of it.
6. **Respect current gate state.** PR #246 is OPEN; synthetic G5 22 passed does not equal live Scheme C G6. Do not migrate OpenAMSM until the generic Echo mechanism is accepted.

The largest architectural risk is not Python↔Go interop. Both existing Go executables already use long-lived stdio/NDJSON. The main risk is accidentally preserving two extension managers and two business selection paths. One Plugin Manager and one Runtime Action Boundary keep this tractable.

## 6. Status vocabulary

- **EVIDENCE:** directly checked source, release or PR status.
- **INFERENCE:** architectural conclusion from the evidence.
- **PROPOSAL:** target next implementation decision.
- `NOT_RUN` / `NOT_VERIFIED`: no evidence was available; do not infer PASS.
