# Reuse and feasibility audit

**Audit date:** 2026-11-25.  
**Target:** Python Agent Core in `ca-agent-next`; independent Go Plugins.  
**Rule:** preserve independently owned mature projects as dependencies; reuse Python source from ca-agent-demo selectively.

## Current target decisions (supersede earlier proposals in this audit)

This audit records repository evidence as observed on 2026-11-25. The following target decisions are authoritative for next and supersede any earlier proposal below that conflicts:

- Every Skill has SKILL.md. assurance/ is optional and contains CA-SL deterministic execution assets; contract.yaml stays inside assurance/.
- No Assurance means LLM-guided only. Valid Assurance supports both Deterministic and LLM-guided. Invalid present Assurance is an import error, never a downgrade.
- Optional assurance/contract.yaml.when is the only formal Skill-selection expression. predicates.yaml remains execution-time business evaluation. Skills without when, including SKILL.md-only Skills, are semantic candidates from SKILL.md.
- Skill source with Assurance is automatically compiled before admission. SKILL.md-only source imports without Compiler. A compiled Artifact is inspected/verified/admitted without rebuilding.
- Individual LLM Actions go through the common Runtime Action Boundary and are not compiled. LLM-created/edited Assurance source follows the normal source-import/Compiler path.
- One Plugin Manager owns Event ingress, Delivery and Tools extensions. Tools are a Plugin extension, not a separate Provider Manager.
- No Domain Contract Package, TaskContract Package, extra Plugin-package SHA-256 hashing, package signatures or Trust Registry.
- SkillCatalog is owned by Python Agent Core/Host, not Plugin Manager. It is an immutable in-memory snapshot containing all imported Skills, cached SKILL.md text/selection metadata and precompiled Assurance when programs.
- when is compiled/type-checked once on import/update and evaluated for every fresh Event using current input; do not cache event-specific results. Semantic candidates come from the same Catalog; references remain lazy-loaded.
- Explicit Skill import/update builds a candidate Catalog generation and atomically activates it on success. Each Invocation pins its generation; failed updates preserve the active generation. No watcher, distributed cache or generic Plugin hot reload.
- The CA-SL v1alpha5 refresh and matching Compiler when Artifact support are a dependency gate, not an already completed implementation.

## 1. Repository snapshot

| Repository | Observed baseline | Language / release | Current evidence | Decision |
|---|---|---|---|---|
| `ca-agent-demo` | main `57e277ff9094dad93543df46910a12a1dbbaf560` | Python; `ca-agent-host 0.4.0` per main README | Existing Python Agent/Host/Runtime/Resident/Context; PR #246 adds generic Provider path; PR #249 is Plugin design only | Primary source for selective Python reuse |
| `ca-agent-next` | main `952a23f8303f5f6cfaff4a88e63de214d856252b`; PR #1 branch `docs/architecture-baseline-20261125` | Target Python; documentation-only PR | No implementation files on main; PR #1 refreshes the target architecture and Harness handoff | New Python implementation workspace |
| `ca-agent` | main `447d0cce7e42c7c1184b11fb2563792eead68d51` | Go | Stable existing implementation | Promotion target, not source |
| `ca-skill-compiler` | main `255ab85fa5abb4b0bf36656bf64250cafebf45cb` | Go; latest release **v2.1.0** | Stateless compiler; CLI + Go/WASM Worker; CA-SL v1alpha5; Build/Verify and Development Build/Verify | Direct external executable/API dependency; do not copy |
| `ca-client-tools` | main `7bcb2614aa3615d8358df31eecefd0909e894e40` | Go; latest release **v1.2.0** | Provider v2 process, one Go-owned Tool source, Compiler Interface Package, runtime binding sidecar | Tool Plugin dependency; do not copy |
| `ca-skills` | main `b06f72baae3eb3d578c489f950a325e2d63d556f` | CA-SL v1alpha5 sources/spec and Python validation tests | Contains Establish, Modify and Release MAS Skill examples; v1alpha5 refresh for optional Assurance and contract.when is a separate required change | Import/use Skill packages; no business logic copied to Host |
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
- CA-SL refresh proposal [ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88) defines contract.when and explicitly delegates its physical compiled representation to a Compiler-owned Artifact Contract. Current v2.1.0 support for that refreshed representation is not established.

**DECISION — direct dependency, no code copy**

- Python Skill Importer invokes the canonical `skillc` executable for Assurance source Check/Build and Artifact Inspect/Verify. SKILL.md-only source does not invoke Compiler; an already compiled Artifact is inspected/verified without rebuilding.
- Pass the exact Assurance source root and the dependency inputs required by the Compiler contract; capture structured output and exit status.
- Compiler must parse/type-check when once and emit a portable checked program bound to the CA-SL CEL profile and the event.type/input type environment. Python Runtime evaluates that program per fresh Event; it must not reparse raw CEL on the hot path. The exact wire representation is a Compiler-owned, versioned Artifact contract; do not mutate a frozen contract in place.
- SkillCatalog is a Next-owned Core mechanism: retain when programs and SKILL.md content in memory; the Compiler does not own Catalog residency, Event evaluation results or atomic generation swaps.
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
- The Go Provider owns SBI client transport, typed OpenAMSM clients, private argument projection and Owner calls. Host/Runtime own Skill Capability authorization, Run identity and final outcomes.
- `protocol/nas5gsm` is a pure Go codec library for a narrow 5GSM Establishment Request slice; it is not yet an Agent-callable Tool. The current public Interface Package does not expose it as a Codec Tool. ca-client-tools PR #39 is OPEN; use only the exact merged/released message subset and do not claim full NGAP parity.

**DECISION — Tool Plugin, do not copy or translate**

- Treat `ca-client-tools` as a Plugin exporting the `tools` extension.
- Plugin YAML manifest references the Interface Package using its canonical package contract; it does not duplicate ToolCatalog or invent an additional Plugin-level digest.
- Use the existing Go executable and published package. No Go-to-Python translation.
- Initial next implementation may adapt `ca-client-tools.provider/v2` behind the unified Plugin Manager's Tool extension driver. This avoids rewriting a mature released protocol while preventing a separate Provider Manager/Runtime.
- Keep the Interface Package as the Tool contract authority and Runtime as the only authorization/outcome authority.
- Expose protocol Codec operations, when ready, through this same `tools` extension and Interface Package. A Skill calls Decode only when it needs protocol fields; otherwise it passes the original Host artifact reference to a business Tool. No separate Codec Plugin/Manager or duplicate Host decoder.
- Do not move OpenAMSM Tool implementation into `ca-openamsm-plugin`.

**Current integration caveat:** ca-agent-demo PR #246 is still OPEN. It reports G5 synthetic Owner 22 passed, but live Scheme C G6 remains NOT_RUN/BLOCKED; its generic Provider loader is a branch input, not mainline accepted code.

### 2.3 ca-skills — optional Assurance source, not Host code

**EVIDENCE**

- Main `b06f72ba` publishes CA-SL v1alpha5 and includes `establish-pdu-session-mas`, `modify-pdu-session-mas` and `release-pdu-session-mas` source examples.
- Tests include `tests/test_compile_mas_v1alpha5.py` and `tests/test_mas_lifecycle_procedures.py`.
- README states that linking/running the examples requires trusted Owner contracts and deployment bindings; examples do not claim live qualification.

**DECISION**

- Every package has SKILL.md. Packages with assurance/ contain contract.yaml, procedure.yaml and the Predicate definitions they use; packages without assurance/ are LLM-guided only.
- Source packages with Assurance are compiled before admission. SKILL.md-only packages import without Compiler. Already compiled Artifacts are inspected/verified/admitted without rebuilding.
- The optional top-level assurance/contract.yaml.when is used for Skill selection; predicates.yaml remains execution-time business evaluation.
- The v1alpha5 refresh is not yet evidence that the released Compiler supports the portable compiled when Artifact. Verify this Compiler behavior before implementation claims. SKILL.md-only import is a Next-owned Importer path and must bypass Compiler.
- The SkillCatalog/generation lifecycle is a new Next mechanism, not a proven reusable ca-agent-demo subsystem. Reuse Formal Resolver and admission primitives selectively; implement immutable Catalog snapshots and Invocation generation pinning in Next.
- Do not copy Create/Modify/Release business logic into Agent Core. Echo is the first mechanism proof; OpenAMSM Skills are a later real-domain integration.

### 2.4 ca-openamsm-plugin — Event ingress/delivery Plugin, not a Tool Provider

**EVIDENCE**

- Main `eb83c8f2` contains only README; no implementation code.
- PR #1 is OPEN/DRAFT, head `1d37c4a`, and remains design-only. Its README/architecture now target the exact Next Plugin Package/IPC v1alpha1 and Host Artifact Handoff contract.
- PR #1 uses Skill-first event consumption. There is no unbound Generic LLM Agent fallback.
- The Event Plugin is not a Provider, Codec Tool implementation or Owner client. `ca-client-tools` remains the Tool Plugin; its current pure NAS codec package is not yet an Agent-callable Codec Tool.

**DECISION**

- Keep the repository independent and Go.
- It implements `event.ingress` and `event.delivery`, not MAS Owner Tools, Skill selection, RunStore or Runtime.
- It owns SBI HTTP/2 ingress, JSON/`multipart/related` parsing, Content-ID association, raw N1/N2 extraction/staging, normalized Event publication and SBI response encoding/delivery.
- It preserves original N1/N2 bytes and does not eagerly deep-decode protocol IEs for business reasoning.
- It consumes Codec Tools exposed by `ca-client-tools` when a selected Skill requests protocol fields. Reuse shared Go codec packages; do not copy a decoder or create a second Codec Plugin/Manager.
- Fresh Events always enter the Host Skill Resolver first. The Event Plugin never chooses the Skill or execution mode.
- Keep the exact Next manifest/IPC and Host Artifact Handoff as the only target contract. Do not reuse `ca-agent-host.plugin/v0` or introduce aliases.

## 3. What may be copied from ca-agent-demo into next

The following means selective Python source reuse after tests/import review, not an instruction to copy entire directories.

| Demo source | Recommendation | Why / work |
|---|---|---|
| `agent/intent/`, model adapter/request types | **COPY + ADAPT (S)** | Python Agent boundary already exists; strip Demo-specific composition |
| `agent/formal/{search,grounding,operators,ranking}` | **COPY + ADAPT (M)** | Useful deterministic reasoning primitives; adapt selection to Assurance contract.when plus semantic SKILL.md candidates |
| `agent/host/root_eligibility.py`, `routing.py` | **ADAPT (M)** | Reuse candidate/exclusion types; replace structured Event→Root mapping with optional contract.when and unguarded SKILL.md semantic candidates |
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

**Overall: FEASIBLE**, with staged implementation. The external Compiler and Tool Plugin are independent release artifacts; Python Core can orchestrate them without sharing language/runtime. The refreshed CA-SL/Compiler behavior is a prerequisite gate for Assurance source import, not an assumption that v2.1.0 already supports contract.when and its portable checked-program representation. SKILL.md-only import is Host behavior, not a Compiler feature.

Critical work:

1. **Unify Plugin/Tool extension management.** Current PR #246 has a generic Provider Manager/ToolComposition; PR #249 proposes a separate Plugin Manager. Next should have one Plugin Manager with Event and Tool extension kinds.
2. **Resolve Skill-first conflict.** PR #249 and ca-openamsm-plugin PR #1 currently describe Agent-default/Skill-optional. Next must bind a Skill first for every fresh business Event.
3. **Replace Event→Root mapping.** Current Demo structuredEventRoutes is not the target. Use optional Assurance contract.when for explicit matches and SKILL.md semantic selection for unguarded Skills.
4. **Refresh CA-SL and Compiler support.** The v1alpha5 spec must define contract.when and optional Assurance; the Compiler must support the grammar, static type-checking and portable compiled Artifact representation. Next's Skill Importer separately handles SKILL.md-only packages without invoking Compiler. Demo MockCompiler is not a substitute.
5. **Add the Core-owned SkillCatalog.** Build the immutable in-memory selection read model, compile when on import/update, evaluate it per fresh Event, atomically swap generations and pin each Invocation. This is a Next-owned mechanism; do not assume Demo has an equivalent reusable Catalog.
6. **Simplify Resident/Runtime.** Current Demo includes Nsmf-specific execution and durable recovery; Echo should prove the common mechanism without copying all of it.
7. **Respect current gate state.** PR #246 is OPEN; synthetic G5 22 passed does not equal live Scheme C G6. Do not migrate OpenAMSM until the generic Echo mechanism is accepted.

The largest architectural risk is not Python↔Go interop. Both existing Go executables already use long-lived stdio/NDJSON. The main risks are preserving two extension managers, reintroducing business Contract Packages, or compiling individual LLM Actions. One Plugin Manager, one Skill Importer and one Runtime Action Boundary keep this tractable.

## 6. Status vocabulary

- **EVIDENCE:** directly checked source, release or PR status.
- **INFERENCE:** architectural conclusion from the evidence.
- **PROPOSAL:** target next implementation decision.
- `NOT_RUN` / `NOT_VERIFIED`: no evidence was available; do not infer PASS.


## 7. Joint implementation gates refreshed on 2026-11-25

- ca-agent-next PR #1 is the single target specification for Plugin Package v1alpha1, Plugin IPC v1alpha1, Skill-first selection and Host Artifact Handoff. It remains OPEN and is not yet merged or implemented.
- ca-openamsm-plugin PR #1 is design-only and must reference the Next contract. It must not retain the old ca-agent-demo plugin/v0 protocol or Generic-Agent-default flow.
- ca-skills PR #88 is OPEN and proposes the same-identifier v1alpha5 Assurance/when refresh. Compiler v2.1.0 is released, but the new when field and portable checked-program representation are not yet evidenced as supported. The SKILL.md-only path is owned by the Next Host importer and bypasses Compiler.
- ca-client-tools v1.2.0 is the Tool implementation. Its Provider v2 process is adapted behind the one Plugin Manager. The production Provider catalog's real-NF SBI multipart binding remains NOT_VERIFIED even though the Host-to-Provider Artifact channel has fixture evidence.
- ca-client-tools PR #39 is OPEN: Phase B final pass; Phase C consumer migration NOT_STARTED. NAS has 8 CA-qualified message types, N2 has 7 scoped qualified roots, and NGAP has 0 CA-qualified full PDUs.
- ca-agent-demo PR #246 is OPEN: synthetic Owner G5 reports 22 passing tests; real isolated Scheme C G6 is NOT_RUN/BLOCKED and G7 is PARTIAL. This is not real OpenAMSM E2E evidence.
- The three OpenAMSM MAS Skills already exist in ca-skills. Their when selectors and live integration against the exact refreshed source revision remain to be completed.
