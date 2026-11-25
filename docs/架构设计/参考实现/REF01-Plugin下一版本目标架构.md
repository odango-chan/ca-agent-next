> 迁移来源：ca-agent-demo/docs/design/ca-agent-host-v0.5-plugin-architecture.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 源文档定位：REF01 Generic Agent Host v0.5 Plugin 下一版本设计目标，非当前 main 实现  
> 迁移记录：ca-agent-next Issue #12。以下保留源文原貌；本文件不是 Next 目标设计，功能边界与当前实现状态以 Next 对应架构/设计说明书及实现审计为准。

---

# CA Agent Host v0.5.0 — Minimal Plugin Architecture (Demo)

- **Status:** next-version **design target**, not implemented or released (2026-11-23).
- **Scope:** `ca-agent-demo` is a Generic Agent Host *reference/demo*. Demonstrate that a second system can be attached without editing Host Core. Do not build a general-purpose Plugin marketplace, installation service or production governance platform.
- **Current baseline:** `ca-agent-host 0.4.0`; [current-tree architecture](generic-agent-host-architecture.md); [current status](../WORK.md); [Scheme C E2E evidence](../../artifacts/reviews/20261123-scheme-c-final/README.md). These remain authoritative for the running implementation.
- **Version distinction:** proposed distribution `v0.5.0` is not the existing `ca-agent-host.resident-deployment/v0.5` document version. No source/schema/version bump is implied by this design.
- **Tool cutover P0:** [Issue #241](https://github.com/odango-chan/ca-agent-demo/issues/241), one integrated Go Provider + Generic Host delivery. **Plugin follow-up:** [Issue #235](https://github.com/odango-chan/ca-agent-demo/issues/235).

## 1. One goal, two extension paths

**Goal:** Given a clean Host build, add an unrelated Tool Provider + Skill, or an unrelated external protocol adapter, using only external code/assets and deployment configuration. Do not edit `agent/`, `runtime/` or `resident/`.

| Requirement | Extension path | Plugin required? |
| --- | --- | --- |
| New Operation in an already supported Provider | Update the Provider's single built-in ToolCatalog and implementation, release the Provider, and update affected Skill | **No** |
| New conforming Tool Provider | Register the released Provider; Host reads its published ToolCatalog and uses existing Skill/Runtime authorization | **No** |
| New external ingress/protocol/callback response | Install an independently owned Plugin implementing the generic ingress/delivery seam | **Yes**, only for this extra protocol behavior |
| Long-lived Run/wake-up | Built-in Host orchestration (optional Temporal), not a business Plugin | **No** |

A Plugin is **not** a required wrapper around every Tool Provider, a second Tool API, a new Skill executor or a place for every externally maintained package. A Plugin may **reference** an existing Provider but MUST NOT copy its implementation or publish a conflicting ToolCatalog.

## 2. Component boundaries

| Component | Owner and responsibility |
| --- | --- |
| Agent | Intent, Skill selection and planning |
| Runtime | One CA-SL execution path; exact Artifact Admission/Link, Operation allowlist, Effect and Evidence semantics |
| Resident | One Host deployment; Run identity, request lifecycle, durable claim/correlation, readiness and delivery responsibility |
| Orchestration | Built-in Run continuation and optional Temporal scheduling; never a Plugin |
| Provider registry/adapter | Generic binding for external Provider v2 `initialize/catalog/invoke`; no MAS or 5GC callable map |
| Plugin registry/adapter | Generic loading/binding of external ingress and delivery handlers; no domain-specific `Nsmf`/`Namf` branches |
| Tool Provider | Implements Operations/Observations and actual Owner calls; publishes **one authoritative ToolCatalog in the same release**, with each Tool's public ID, input/output Schema and Effect |
| Plugin | Adapts protocol messages/events into the Host's generic request/event and delivers responses, without executing a Procedure |
| Skill | Business Goal/Procedure/Predicates and declared Capability requirements; independently published |

**Dependency direction:** Generic Core depends on public *interfaces*, not on any particular Plugin or Provider package. No Plugin/Provider imports from Host internals. An external implementation may live in another repository and be referenced by local deployment configuration; that does not require the Demo to implement a package manager.

Current implementations that must eventually disappear from Generic Host include `resident/composition.py` fields `nsmf_runtime` / `namf_relay_runtime` and the fixed `MAS_CALLABLES` / `MAS_OPERATION_IDS` maps in `integrations/ca_client_tools/mas_typed.py`. Do not simply rename `integrations/` to `plugins/`.

## 3. Minimum API and demo deployment

### 3.1 Tool Provider: use the protocol we already have

Keep `ca-client-tools.provider/v2` as the current **Tool Provider application protocol**, initially carried over `stdio`. The **v0.5 target** consumes the same released **Compiler-compatible Interface Package** as `ca-skill-compiler v2.1.0` (`interface/package.json`, ToolCatalog YAML, CapabilityCatalog and JSON Schemas), plus the generated `provider.yaml` runtime binding. Both views are built deterministically from one Go-owned **YAML** Tool source; no separate Host ToolCatalog or Schema authoring. The existing `catalog(backendOperationIds)` method verifies the private IDs listed in `provider.yaml`; a new list-all RPC is unnecessary. A generic Host adapter constructs Runtime bindings without MAS-specific Python tables. **Protocol** identifies `initialize/catalog/invoke`; **transport** identifies `stdio`.

For this **Demo**, treat the ToolCatalog from the **explicitly selected released Provider** as the authoritative Tool definition: there is no second Host-authored/Owner-signed ToolCatalog or duplicate Schema ledger. If a declared Schema is malformed, or Provider output disagrees with it, fail validation/invocation, correct the Go Provider and publish a new release. **Registration is still not authorization**: the selected Skill's Capability requirements and the Runtime's Root-scoped allowlist decide which registered Tools may be called. A declared `MUTATION` and HTTP success alone do not prove COMMITTED.

### 3.1.1 One-time Tool cutover and Go ownership

**Publication reference:** [ca-client-tools Provider Release Package vNext](https://github.com/odango-chan/ca-client-tools/blob/main/docs/tool-provider-release-package-vnext.md), updated in [PR #30](https://github.com/odango-chan/ca-client-tools/pull/30).

**Separate Studio/Compiler release asset:** the same Go release publishes a platform-neutral `ca-client-tools_interface_<version>.zip`, generated **once** from the canonical YAML and containing exactly the same `interface/` bytes as the runtime Provider archive (the ZIP stores `package.json` at its root). Studio imports or downloads this pinned Interface Package and locks its digest; the Host loads the matching interface tree from the selected platform runtime archive. The independent ZIP **never** carries a Go executable or `provider.yaml`. Tracked in [ca-client-tools#31](https://github.com/odango-chan/ca-client-tools/issues/31) and [Skill Studio#261](https://github.com/odango-chan/ca-skill-studio-demo/issues/261). This is a required **future release gate**, not functionality in v1.0.0. **YAML-first** means developer-maintained Provider Tool definitions and the Host runtime manifest use YAML; the frozen Compiler `interface/package.json` and generated JSON Schema/Capability exports remain JSON where the released Compiler expects them. Do **not** introduce a new Compiler parser or rename its package manifest.



This is a **single integrated Tool-system replacement**, not the first phase of a dual-registry rollout. The shipped `ca-client-tools v1.0.0` Provider v2 supports explicit private backend ID catalog queries but **does not ship** the proposed Compiler Interface Package or `provider.yaml`. The Go release tooling must generate both views from its canonical YAML definitions, and the Host must load them. Do not claim the current binary already supports the new package format.

- **Go `ca-client-tools`** owns MAS argument projection, 3GPP SBI request/response parsing, private binding identities and one canonical YAML Tool source generating the existing frozen Compiler ToolCatalog/Schema interface and a minimal Host `provider.yaml` binding. Do not maintain equivalent Python business tables.
- **Python Generic Host** owns process connection, Catalog load/registration, Root-scoped authorization, exact Run identity, and the Runtime's final Effect/Evidence/UNKNOWN/Reconcile decisions. Do not migrate these Host responsibilities into Go simply because IPC uses stdio.
- **Public vs private ID** may remain distinct, but their mapping is derived from the **same Provider-owned Catalog**, not from a second Host-maintained document. No implicit ID lowercasing or domain-specific Python mapping.
- **Release + runtime consistency** is a publication/integration smoke check against that one release artifact, not two separate contract authorities. Bad or inconsistent metadata must fail, be corrected and republished; no fallback compatibility implementation.
- The current `ca-client-tools v1.0.0` release's production Catalog remains **READ-only**; successful Scheme C Development mutation runs do not mean its published production Provider supports mutations. Updating the Go Provider for those Tools is a separate concrete release change within the complete Tool cutover.
- Old manual `ToolImplementationCatalog`, `tools/registrations/default.yaml`, `MAS_CALLABLES`, `MAS_OPERATION_IDS`, `_PROVIDER_ARGUMENTS`, and duplicate Tool adapters must be **removed at cutover** once the new complete path has passed its acceptance. No second lasting Python/Go Tool implementation.

### 3.2 Plugin: only the missing ingress/delivery seam

The minimum Plugin interface needs three concepts:

1. **Descriptor:** plugin ID, adapter API version, entrypoint/endpoint, and which of `ingress` / `delivery` it provides.
2. **Ingress:** authenticated external event → generic Host request, including stable event ID, source, correlation keys and private payload reference when necessary.
3. **Delivery:** Host result/outbox obligation → protocol response, preserving exact external request and Run correlation.

A Plugin can implement ingress alone, delivery alone or both. Observation sources may use the existing Observation boundary; do not invent a new plugin-specific Observation framework until needed.

**Illustration only — NOT an implemented or published manifest schema:**

```yaml
# operator-selected local Demo deployment configuration
providers:
  - id: example.network.provider
    protocol: ca-client-tools.provider/v2
    transport:
      type: stdio
      argv: [./bin/network-provider, provider, serve]

plugins:
  - id: example.external-protocol
    adapterApi: ca-agent-host.plugin/v0
    transport:
      type: stdio
      argv: [./bin/event-adapter, serve]
    extensions:
      - kind: ingress
        id: example.external-protocol.requests
        events:
          - type: example.work.requested
            schemaRef: ./contracts/work-request.schema.json
      - kind: delivery
        id: example.external-protocol.responses

# Illustrative routing fragment only; existing rootRouting fields are omitted.
# genericEventRoutes is a v0.5 target proposal, NOT current parser syntax.
rootRouting:
  genericEventRoutes:
    - ingressId: example.external-protocol.requests
      eventType: example.work.requested
      scopeRootSkills: [example.handle-work]
      intentAbsentTarget: example.handle-work
```

The `transport.argv` list is an **operator-approved process startup command**, executed once per Provider/Plugin process start **without shell interpretation**; it is **not** a Tool invocation command. The current concrete `ProviderV2Process.start()` launches `[binary, "provider", "serve"]` and communicates by long-lived NDJSON over stdin/stdout. Generic v0.5 registration should accept the declared argv instead of hardcoding those arguments. After startup, Host sends `initialize` and `catalog`, then many `invoke` requests over the **same connection**. An external adapter can be shipped separately without special release tooling in `ca-agent-demo`; no on-demand download or arbitrary Plugin Python import into Host.

**Do not create an unnecessarily elaborate Plugin wire protocol:** first reuse the existing generic `ServiceInvocation`/`InvocationSource`, Run storage and delivery boundaries; define only the small IPC/event mapping that is missing for an out-of-process adapter. If the seam already supports the use case, reuse it unchanged.

### 3.3 Plugin registration and event routing (configuration-only)

**The same zero-Core-code rule applies to Plugins as to Providers.** Installing a new external protocol adapter must require only its independently built executable, a deployment declaration, and existing/new Skill assets. No `register_openamsm_plugin()`, Python import, fixed `PluginId` enum, or hardcoded `if plugin == ...` in the Host.

**Registration at Host startup**, with no plugin installer/marketplace:

1. Read the operator's explicit `plugins` declarations. Connect/start each configured adapter once using its declared `transport` (`stdio` for this Demo).
2. Check that each adapter exposes the configured Plugin API and the named `ingress`/`delivery` extension IDs and event types. Resolve and validate the declared **normalized event Schema** for each ingress event. Missing/mismatched/duplicate IDs, missing Schema or invalid Schema fail that binding; do not silently choose a different adapter. This is *connectivity and binding validation*, not a full plugin trust/qualification workflow.
3. Register `ingressId → adapter process` and `deliveryId → adapter process` in the generic Host bridge. An inbound protocol event carries the exact declared `ingressId`, `eventType`, stable external request ID, correlation and safe payload reference; it enters the existing Host invocation/admission path.
4. The **Host's** `rootRouting` maps the normalized event to allowed Root Skills. The Plugin only emits events and returns protocol responses; it must not embed a Skill name or invoke Runtime directly. Delivery is selected by the original invocation's recorded response obligation, never by arbitrary Plugin preference.
5. Freeze bindings for the lifetime of the Demo Host process. To add/remove/change a Plugin or route, change deployment configuration and restart. No install API, hot reload or automatic software download.

### 3.4 Schema registration and ownership (no duplicate catalogs)

A Plugin registration MUST declare a **Schema reference for each normalized ingress event type** it emits. The external adapter owns its wire-format decoding and converts proprietary/3GPP messages into its declared normalized event; the Host validates **that normalized event**, not arbitrary raw network frames.

| Material | Publisher / authority | Registration source | Host validation |
| --- | --- | --- | --- |
| Plugin descriptor and common IPC/event envelope | Host Plugin API | built into Host + Plugin API version | reject unknown API/invalid envelope |
| Plugin normalized event payload | Plugin author | `events[].schemaRef` (operator-approved local file/asset) | load JSON Schema, check valid schema, check incoming payload |
| Tool Operation input/output and Effect | the installed/released Go Provider | the **Compiler Interface Package** in the release archive | validate exact Tool schemas and effects from the linked Interface Package against inputs/outputs |
| Private backend bindings / availability | the same Go Provider | generated `provider.yaml` and `initialize/catalog(backendOperationIds)` | match the declared private IDs to provider availability; missing Tool remains NOT_READY |
| Skill request and dependency Schemas | Skill/Compiler Artifact publisher | selected admitted Artifact | validate the request/arguments against exact selected Root contracts |

**Three distinct validation points:**

1. **Startup/preflight:** load the explicitly selected Provider release's **Interface Package + generated `provider.yaml`**, reject missing/duplicate Tool identities, invalid Schema references, unsupported Effects, mismatched snapshot digests and missing selected Skill dependencies. Resolve Plugin event Schema refs from approved local assets. No separate public ToolCatalog registry/service, network fetch or mandatory package signature.
2. **Ingress:** validate the Plugin's normalized event envelope and event payload against the event type's registered Schema **before** routing/admission. Source identity, exact event ID and correlation remain mandatory; Schema matching does not constitute authorization.
3. **After Root selection:** convert/project the validated event into the selected Skill's request input; validate against that Root's **own request Schema**, then run existing Admission/Tool checks. Do not assume that two individually valid Schemas make a particular projection compatible. If projection or request validation fails, reject the request; do not guess fields.

A delivery-only Plugin uses the Host-owned standard result/delivery envelope. It does **not** have to duplicate a Tool's output Schema or register the whole external wire response schema with the Host; protocol-specific response serialization belongs to that Plugin. A Plugin that exposes an additional normalized *outbound event type* must declare its payload Schema similarly if Host is expected to validate that event.

**No global Schema registry service and no duplicate ToolCatalog:** Plugin `schemaRef`, the **installed Provider's single Compiler Interface Package**, and the selected Skill Artifact form the deployment's resolved Schema set. Go Provider owns Tool definitions; Plugin owns event Schema; Skill owns request Schema. Host may freeze a Catalog digest for reproducibility but does not require independent Owner signing or cross-compare two separately authored Tool catalogs. Skill/Runtime authorization remains separate from published Tool metadata.

The illustrative `events` / `schemaRef` and `genericEventRoutes` keys are **v0.5 design proposals**, not supported by the existing deployment parser.

**Routing gap to implement once:** current `agent/host/root_routing_profile.py` accepts `structuredEventRoutes` with numeric `messageType` / optional `requestType` selectors, reflecting the 5GC sample. It **cannot yet route an arbitrary** `ingressId + eventType` from a non-5GC Plugin. The v0.5 target needs one generic event route selector (the illustrative `genericEventRoutes` above, or an equivalent minimal extension), backed by the existing allowed Root / per-Root READY rules. That is a one-time **generic** Host capability; subsequent Plugin registrations use only config.

**Plugin registry is intentionally small:** a dictionary of explicitly configured extension IDs and their running connection. It does not resolve dependencies, sign packages, store installation state, or supervise rolling upgrades. A Plugin exposing only `ingress`, only `delivery`, or both is valid. Plugin registration never implies Tool registration or Capability authorization.

**Negative checks for T2:** unknown/duplicate Plugin or extension ID, unadvertised event type, ambiguous/missing route, Plugin unavailable, mismatched external request correlation and unauthorized Root must not execute or fabricate a delivery success. These checks reuse Host routing/journal and do not create a second state machine.

### 3.5 Transport scope and boundaries

- **v0.5.0 Demo implements `stdio` only** for the generic Provider v2 connection and, if required by T2, the minimal out-of-process Plugin control/IPC. No HTTP or MCP transport implementation is required for this milestone.
- An eventual `http` transport would connect to an already running endpoint; it must preserve the Provider protocol semantics or use an explicit generic protocol adapter. It is not a new implementation of every Tool.
- **MCP is an application protocol, not merely a transport value.** Future MCP support needs a separate general MCP-to-Host Tool binding adapter; changing `type: stdio` to `type: mcp` alone cannot make a Provider v2 peer MCP-compatible.
- Transport details never appear in Skill, Capability or CA-SL Procedure. Registration resolves the Provider process/endpoint at Host startup, verifies Catalog and freezes the admitted bindings. Restart is sufficient for Demo configuration changes; no hot reconfiguration.
- The shown `transport` and `argv` keys are **design proposals, not accepted by the current deployment parser**. The example Plugin `stdio` control path is equally illustrative; its exact IPC messages are to be limited to what T2 needs.

### 3.6 Minimal lifecycle

Only require **configure → start/connect → ready/not-ready → stop** for the Demo. Use existing Host process supervision where available.

**Explicitly out of scope for v0.5.0:** Plugin marketplace, automatic installation/updating, mandatory package signatures/PKI, sophisticated version solver, hot reload, zero-downtime upgrade, rollback manager, generic sandbox/permissions UI, multi-tenant Plugin policies, and a separate full-featured Plugin lifecycle engine.

We still need clear failure reporting: absent process, invalid configuration, missing required Operation/handler and failed connection must result in the affected Root/ingress being NOT_READY or rejected. Minimal validation protects the Demo's correctness; it is not Production Qualification.

## 4. Keep the actual execution guarantees

Removing enterprise Plugin management does **not** remove fundamental Runtime correctness:

- Exactly one CA-SL Runtime. Neither a Plugin nor Temporal may decide or dispatch business Procedure nodes.
- Root-scoped Admission, Tool grants, Schema/Effect checks, and independent per-Root READY continue to apply.
- For protocol ingress, duplicate/mismatched events and wrong/late Run correlation are rejected or resolved against the original durable record; no silent second mutation.
- Ingress acceptance or a Provider's HTTP 200/204 is not proof of successful business mutation. Preserve current Development-vs-Production commit/evidence distinctions; UNKNOWN must not be upgraded to COMMITTED by the Plugin.
- Private 3GPP/N1/N2 and Owner transaction data remain outside public Skill/LLM inputs and ordinary traces.
- A failure in one external adapter must not secretly fall back to a different Owner or leak another Root's capabilities.

These are existing Host/Runtime trust semantics to **reuse**, not justification for a new Plugin-specific receipt database, retry engine or state machine.

## 5. OpenAMSM migration boundary

Do **not** freeze `ca-plugin-openamsm` as the only possible package split. Generic 3GPP SBI ingress/delivery may be reusable by other SMF owners, while OpenAMSM-specific MAS operations belong to its Tool Provider. Investigate the real coupling before choosing whether the first external Plugin is named `3gpp-sbi` or `openamsm`.

Preserve the existing Scheme C Development Create → Modify → Release evidence. Its live harness explicitly creates services and bypasses ordinary READY for a focused test: it does not yet prove that a declarative Plugin/Provider deployment works. Move code only after the normal Host path runs end-to-end; never delete legacy functionality merely to satisfy a folder-name target.

## 6. Small, separable acceptance gates

| Gate | Test | Success criterion |
| --- | --- | --- |
| **T1 — Zero-code Tool** | Independently released non-5GC Go Provider + compiled Skill, **no Plugin** | Compiler v2.1.0 links the released Interface Package; unchanged built Host wheel loads the **same package** + `provider.yaml`, validates existing `initialize/catalog/invoke`, genuine Admission/READY, Tool call and Evidence, **no Core code edit or duplicate ToolCatalog** |
| **T2 — Zero-code Protocol** | External non-5GC ingress/delivery Plugin, reusing an existing Provider + Skill | Built Host wheel; **config-only Plugin + normalized event Schema registration**, generic event→Root routing, exact Skill request Schema check, event→Run→result/response; reject bad event payload, duplicate/correlation failures; **no Core source edit** |
| **T3 — Existing 5GC regression** | Scheme C Create/Modify/Release after extraction | Real isolated lab, normal deployment/Admission/READY, no second Runtime; compare with existing Development evidence |

T1 and T2 are **the v0.5.0 Demo architecture proof**. T3 gates deletion of old 5GC wiring and is a separate migration milestone; do not pretend the old E2E test alone proves T1/T2.

Negative acceptance can be small but meaningful: unknown Operation, ungranted Capability, missing Provider, duplicate event with mismatched contents and UNKNOWN mutation do not proceed as success. No Plugin package-signing, marketplace or upgrade stress suite for this Demo.

## 7. Cutover boundary and subsequent Plugin work

**Do not implement Plugin while Tool P0 #241 is incomplete.** The Tool subsystem's final acceptance is a **single clean cutover**, not a staged Host merge with two production Tool registries. The Go Provider may need its own independently reviewable changes and release first; the Host remains on its previous baseline until the new generic connection, the published Go Catalog, existing READ acceptance, real Scheme C regressions and old Python Tool-path deletion have all been reconciled.

## 7. Implementation order and non-goals

1. **One complete Tool cutover first:** extend the Go-owned canonical YAML definitions and release generator to emit the existing frozen Compiler Interface Package plus `provider.yaml`; replace manual Tool registration, Python MAS mapping and duplicated Tool catalogs with a generic Host Registry. Compile Skills against the release itself and prove **T1** before merging the cutover. Do not leave an old Tool path as fallback.
2. **Plugin seam second:** minimal external ingress/delivery adapter using the Host's current invocation and durable handoff model. Prove **T2** with a non-5GC system.
3. **5GC extraction later:** move necessary protocol adapter code to external ownership, preserve existing Provider and Skill implementations, prove **T3**; only then remove dead Host-specific code.
4. **Built-in Temporal placement:** move from `integrations/temporal` to internal orchestration when convenient, without changing its execution semantics.

No second Runtime, no new CA-SL language version, no new Compiler role, no duplicated ToolCatalog authority, no generalized Plugin framework beyond demonstrated needs, no required cross-repository Tool contract governance in this Demo iteration, and **no claim of Production Qualification**.

**Review rule:** any proposed core change justified solely by an external domain should instead be rejected or reframed as a generic seam demonstrated with a non-5GC test. Record the specific zero-code proof, not just an architecture diagram.
