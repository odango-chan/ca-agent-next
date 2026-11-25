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
| ca-client-tools | Independent Go Tool Plugin for OpenAMSM; consume its released package/process. Do not port or copy its implementation into Python. |
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
- [SkillCatalog and Compiler integration](docs/integration/skill-catalog-compiler-contract.md) — import/update lifecycle, hot-path residency, Catalog generations and portable compiled when requirement.
- [Plugin Package v1alpha1](docs/plugin-package.md) — YAML manifest, extensions and common IPC.
- [Demo audit](docs/audit/ca-agent-demo.md) — current source inventory and evidence.
- [Reuse and feasibility](docs/audit/reuse-and-feasibility.md) — copy vs adapt vs external dependency decisions.
- [DeepSeek Harness plan](docs/implementation/deepseek-harness-plan.md) — staged implementation task package.
- [Acceptance](docs/acceptance.md) — runnable Example and mechanism acceptance gates.

## Skill model at a glance

Every Skill has SKILL.md. The assurance/ directory is optional:

- No Assurance: LLM-guided only; import SKILL.md directly without Compiler.
- Valid Assurance: Deterministic and LLM-guided; source import automatically compiles before admission.
- Compiled Skill Artifact: Inspect/Verify and admit directly without rebuilding.
- Invalid present Assurance: fail import; never silently downgrade.

An optional top-level assurance/contract.yaml when is compiled once during import/update and evaluated for each fresh Event. All Skills, including SKILL.md-only Skills, live in the Core-owned in-memory SkillCatalog. Catalog updates activate atomically by generation; each Invocation pins its generation. predicates.yaml remains an execution-time business check. Individual LLM Action proposals use the common Runtime Action Boundary and are not compiled.

## Example-first development

Examples live in this repository under examples/; a separate ca-example repository is not needed.

Every new externally observable mechanism must add a new runnable Example case and an automated Acceptance Test in the same change set. Examples must exercise the same public Plugin/Skill/Runtime boundaries as independent packages. They must not import Agent Core internals.

The first planned vertical Example is Echo: Python Agent Core, one independently running Go Plugin exposing Event, Delivery and Tool extensions, one Assurance-backed Skill that runs in both modes, and one SKILL.md-only Skill that runs LLM-guided only. This is a plan, not an implementation claim.

## Scope

This is a Demo-level mechanism implementation, not a production platform. Keep basic YAML/Schema/version/reference validation, clear errors, simple package loading, minimal correlation, useful logs and executable tests.

Do not add extra SHA-256 package hashing, package signatures, Trust Registry, Domain/Task Contract Packages, legacy compatibility, Marketplace, filesystem watchers or generic Plugin hot reload, production HA, complex multi-tenant governance or broad DFX unless explicitly re-scoped. Explicit SkillCatalog import/update with atomic generation activation is in scope.
