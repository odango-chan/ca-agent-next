# CA Agent Next

**Purpose:** an isolated next-generation Agent implementation, evolved from ca-agent-demo, with a deliberately small mechanism surface and runnable Examples.

**Agent Core language: Python.** This is a fixed architecture decision for ca-agent-next. Go is used by independently running Plugins such as ca-openamsm-plugin and ca-client-tools; it does not imply a Go Agent Core.

**Current status:** architecture and implementation handoff documents are under review in PR #1. This repository still has no Agent implementation. Do not mistake the design baseline for an implemented or accepted runtime.

## Repository evolution

| Repository | Role |
|---|---|
| ca-agent-demo | Primary evolution source. Existing Python Agent/Host/Runtime mechanisms, runnable examples, tests and implementation evidence are audited here. Reuse selectively; do not copy the whole repository. |
| ca-agent-next | New, isolated Python implementation. Reorganize and simplify mechanisms against the agreed target architecture. |
| ca-agent | Current stable implementation and eventual promotion target. It is not the source tree for this redesign. |
| ca-skill-compiler | Independent Go Compiler; consume its released executable/API. Do not copy its Go implementation into next. |
| ca-client-tools | Independent Go OpenAMSM Tool implementation; consume its released package/process through the unified Plugin Manager tools extension. Do not port or copy its implementation into Python. |
| ca-openamsm-plugin | Independent Go Event Plugin for OpenAMSM protocol ingress/delivery. |
| ca-skills | CA-SL v1alpha5 language and published business Skill sources. Same-version refresh proposal [PR #88](https://github.com/odango-chan/ca-skills/pull/88) adds optional Assurance and contract.when; not yet merged. |

Promotion flow:

~~~text
ca-agent-demo (source/evidence) → ca-agent-next (new Python implementation) → ca-agent (promotion after acceptance)
~~~

For the next major redesign after promotion, create a fresh ca-agent-next. Keep the stable ca-agent tree intact during this experiment.

## Start here

- [Agent instructions](Agent.md) — mandatory rules for coding agents and VibeCoding.
- [Architecture](docs/architecture.md) — Python Core, optional Assurance, Core-owned in-memory SkillCatalog, Skill import/selection, unified Plugin and Runtime boundary.
- [Plugin Package v1alpha1](docs/plugin-package.md) — YAML manifest, extensions and complete common IPC contract.
- [Plugin Artifact Handoff](docs/plugin-artifact-handoff.md) — Host-owned N1/N2 staging, custody and delivery.
- [技能目录与编译器运行时接口设计说明书](docs/集成设计/技能目录与编译器运行时接口设计说明书.md) — Catalog 生命周期、CEL CheckedExpr 交换、新版发布运行时 Artifact 与运行时求值边界。
- [DeepSeek Harness 实施提示词](docs/实施计划/DeepSeek%20Harness实施提示词.md) — 可直接交给 Harness 的分阶段实施任务。
- [Demo audit](docs/audit/ca-agent-demo.md) — current source inventory and evidence.
- [Reuse and feasibility](docs/audit/reuse-and-feasibility.md) — copy vs adapt vs external dependency decisions.
- [DeepSeek Harness plan](docs/implementation/deepseek-harness-plan.md) — staged implementation task package.
- [Acceptance](docs/acceptance.md) — runnable Example and mechanism acceptance gates.

## Skill model at a glance

Every published Skill has SKILL.md. The assurance/ directory is optional in the authoring source:

- SKILL.md-only published Skill: LLM-guided only; import directly.
- Published Skill with compiled Assurance Artifact: supports Deterministic and LLM-guided execution.
- Assurance source YAML is compiled and verified by the independent Compiler before publication. The Agent never imports Assurance source, invokes Compiler or recompiles a Skill.
- A package declaring Assurance but missing its compiled Artifact, containing malformed/incompatible compiled data, or referring to unavailable Tools/Capabilities fails import with an explicit diagnostic; it is never silently downgraded.

The Agent Importer performs only basic published-package checks (supported manifest/Artifact format, required files and references, safe paths, parseable CEL/type data) and resolves Tool/Capability dependencies against locally installed Plugins. This is ordinary import validation, not Skill Admission, trust evaluation, approval or production authorization. The Demo has no separate Skill Admission mechanism.

An optional top-level authoring-source `assurance/contract.yaml.when` is compiled before publication. The Agent loads/deserializes the published CEL program once during import and evaluates it for each fresh Event. All Skills, including SKILL.md-only Skills, live in the Core-owned in-memory SkillCatalog. Catalog updates activate atomically by generation; each Invocation pins its generation. `predicates.yaml` remains an execution-time business check. Individual LLM Action proposals use the common Runtime Action Boundary and are not compiled.

## Plugin and protocol payload model

A Plugin is the common package/process unit managed by one Plugin Manager. It may expose `event.ingress`, `event.delivery`, `tools`, or a combination in one process. A **Tool Plugin** is a Plugin that exposes the `tools` extension; an individual Tool is a callable operation described by its owning Interface Package, not a separate process or import unit. There is no second Tool Registry or Provider Manager.

SBI is not JSON-only. The OpenAMSM Event Plugin parses SBI JSON and `multipart/related`, associates Content-ID values and preserves original binary parts through the Host-owned [Plugin Artifact Handoff](docs/plugin-artifact-handoff.md). A Skill may call a Codec Tool from the `ca-client-tools` Tool Plugin when it needs decoded fields; it may also pass the original artifact reference onward without decoding. For a shared SBI operation such as UpdateSMContext, the Event Plugin may extract only the minimum NAS discriminator needed to normalize the Event before Skill selection. This is not full decoding or business logic. Codec is not built into Agent Core or duplicated in the Event Plugin.

## Example-first development

Examples live in this repository under examples/; a separate ca-example repository is not needed.

Every new externally observable mechanism must add a new runnable Example case and an automated Acceptance Test in the same change set. Examples must exercise the same public Plugin/Skill/Runtime boundaries as independent packages. They must not import Agent Core internals.

The first planned vertical Example is Echo: Python Agent Core, one independently running Go Plugin exposing Event, Delivery and Tool extensions, one Assurance-backed Skill that runs in both modes, and one SKILL.md-only Skill that runs LLM-guided only. This is a plan, not an implementation claim.

## Scope

This is a Demo-level mechanism implementation, not a production platform. Keep basic YAML/Schema/version/reference validation, clear errors, simple package loading, minimal correlation, useful logs and executable tests.

Do not add extra SHA-256 package hashing, package signatures, Trust Registry, Domain/Task Contract Packages, legacy compatibility, Marketplace, filesystem watchers or generic Plugin hot reload, production HA, complex multi-tenant governance or broad DFX unless explicitly re-scoped. Explicit SkillCatalog import/update with atomic generation activation is in scope.
