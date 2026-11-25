# CA Agent Next

**Purpose:** an isolated workspace for the next-generation Agent architecture, its smallest runnable mechanisms, and their acceptance examples.

**Current status:** architecture baseline is being documented. This repository was created empty; no Agent implementation or mechanism acceptance is claimed yet.

## Repository roles

| Repository | Role |
|---|---|
| [ca-agent](https://github.com/odango-chan/ca-agent) | Current stable Go Agent baseline. Reference HEAD: `447d0cce7e42c7c1184b11fb2563792eead68d51` (2026-11-18). |
| [ca-agent-demo](https://github.com/odango-chan/ca-agent-demo) | Mechanism prototype and cross-component design/acceptance reference. |
| **ca-agent-next** | Isolated next-generation implementation, runnable examples, and acceptance tests. |

When the next implementation satisfies its acceptance baseline, it can be promoted to `ca-agent`. For the following major redesign, create a fresh `ca-agent-next`. Keep the old stable baseline intact during the experiment; do not mix old and new architecture in one working tree.

## Start here

- [Agent instructions](Agent.md) — mandatory rules for coding agents and VibeCoding.
- [Architecture baseline](docs/architecture.md) — contract ownership, selection, execution, Runtime, and end-to-end flow.
- [MVP acceptance](docs/acceptance.md) — runnable-example rule, first example, acceptance gates, and non-goals.

## Example-first development

Examples live in this repository under `examples/`; a separate `ca-example` repository is not needed at this stage.

Every new externally observable extension or execution mechanism must include, in the same change set:

1. at least one runnable Example that consumes the public mechanism boundary; and
2. an automated Acceptance Test proving that Example works.

An Example must not import Agent `internal` packages or require business-specific changes to Agent Core. Internal refactoring that adds no externally observable mechanism does not require a new Example.

The first planned vertical example is an Echo domain with its own business contract, an independent Go Plugin, a Skill package, a Provider, deterministic and LLM-guided scenarios, and response delivery. It is a plan, not an implemented feature.

## Scope

This is a **Demo-level mechanism implementation**, not a production platform. Keep basic schema validation, clear errors, minimal event/task correlation, and useful logs. Do not add production HA, complex security governance, multi-tenant isolation, Marketplace, central business registries, distributed event buses, complex compensation orchestration, or broad legacy compatibility unless a later task explicitly changes scope.
