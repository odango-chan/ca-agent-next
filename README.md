# CA Agent Next

**Purpose:** an isolated next-generation Agent implementation, evolved from `ca-agent-demo`, with a deliberately small mechanism surface and runnable Examples.

**Agent Core language: Python.** This is a fixed architecture decision for `ca-agent-next`. Go is used by independently running Plugins such as `ca-openamsm-plugin` and `ca-client-tools`; it does not imply a Go Agent Core.

**Current status:** architecture/audit documents are under review in PR #1. This repository still has no Agent implementation. Do not mistake the design baseline for an implemented or accepted runtime.

## Repository evolution

| Repository | Role |
|---|---|
| [ca-agent-demo](https://github.com/odango-chan/ca-agent-demo) | **Primary evolution source.** Existing Python Agent/Host/Runtime mechanisms, runnable examples, tests, and implementation evidence are audited here. Reuse selectively; do not copy the whole repository. |
| **ca-agent-next** | New, isolated **Python** implementation. Reorganize and simplify mechanisms against the agreed target architecture. |
| [ca-agent](https://github.com/odango-chan/ca-agent) | Current stable implementation and eventual promotion target. It is not the source tree for this redesign. |
| [ca-skill-compiler](https://github.com/odango-chan/ca-skill-compiler) | Independent Go Compiler; consume its released executable/API. Do not copy its Go implementation into next. |
| [ca-client-tools](https://github.com/odango-chan/ca-client-tools) | Independent Go Tool Plugin for OpenAMSM; consume its released package/process. Do not port or copy its implementation into Python. |
| [ca-openamsm-plugin](https://github.com/odango-chan/ca-openamsm-plugin) | Independent Go Event Plugin for OpenAMSM protocol ingress/delivery. |
| [ca-skills](https://github.com/odango-chan/ca-skills) | CA-SL v1alpha5 language and published business Skill sources. Consume/import Skill packages; do not embed business logic in Agent Core. |

Promotion flow:

`ca-agent-demo` (source/evidence) → `ca-agent-next` (new Python implementation) → `ca-agent` (promotion after acceptance).

For the next major redesign after promotion, create a fresh `ca-agent-next`. Keep the stable `ca-agent` tree intact during this experiment.

## Start here

- [Agent instructions](Agent.md) — mandatory rules for coding agents and VibeCoding.
- [Architecture](docs/architecture.md) — Python Core, unified Plugin model, Skill-first selection, Runtime boundary and data flow.
- [Demo audit](docs/audit/ca-agent-demo.md) — current source inventory and evidence.
- [Reuse and feasibility](docs/audit/reuse-and-feasibility.md) — copy vs adapt vs external dependency decisions.
- [DeepSeek Harness plan](docs/implementation/deepseek-harness-plan.md) — staged implementation task package.
- [Acceptance](docs/acceptance.md) — runnable Example and mechanism acceptance gates.

## Example-first development

Examples live in this repository under `examples/`; a separate `ca-example` repository is not needed.

Every new externally observable mechanism must add a new runnable Example case and an automated Acceptance Test in the same change set. Examples must exercise the same public Plugin/Skill/Runtime boundaries as independent packages. They must not import Agent Core internals.

The first planned vertical Example is **Echo**: Python Agent Core, one independently running Go Plugin that can expose both an Event extension and a Tool extension, an Echo-owned business contract, one Skill, and deterministic plus LLM-guided runs. This is a plan, not an implementation claim.

## Scope

This is a **Demo-level mechanism implementation**, not a production platform. Keep basic schema validation, clear errors, package identity, minimal correlation, useful logs and executable tests. Defer production HA, complex security governance, multi-tenant isolation, Marketplace, distributed Event Bus, complex compensation orchestration and broad legacy compatibility unless explicitly re-scoped.
