> 迁移来源：.agents/skills/create-connectionagent-skill/SKILL.md  
> 固定源提交：780497a2918ad3e7bdff554ab64b0ba627e867e0  
> 固定源 Blob SHA：dd6ef655839fe31ed28ae4ad865d5c0241a29ef4  
> 原始状态：ca-skills 内部 Skill 创建工作流；旧工具链说明  
> 迁移追踪：ca-agent-next Issue #49 / SR-032。本文保留原始内容供溯源；其 CA-SL v1alpha5 字段、目录和示例不构成 CA-SL 1.6.0 规范。  
> 注意：原文相对链接按 ca-skills 原目录解析；当前权威规则以 Next 的《SKILL 作者规范》和 CA-SL 1.6.0 语言设计为准。
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：只读历史源文归档；不作为 CA-SL 1.6.0 规范或产品验收证据，不改写原文及源相对链接。

---

---
name: create-connectionagent-skill
description: Use when authoring, reviewing or refreshing ConnectionAgent Skill source in ca-skills. Apply the current CA-SL v1alpha5 specification and keep historical 5GC packages on their documented source baseline.
---

# Author ConnectionAgent Skill source

## Choose the source baseline

- Read the [current CA-SL specification](../../../docs/skill-language-spec.md) and [authoring guide](../../../docs/authoring.md). Use the [v1alpha5 examples](../../../examples/README.md) for new source.
- Read the [legacy 5GC baseline](../../../docs/current-5gc-skill-baseline.md) before editing packages under `skills/`. Preserve business ordering and callable identities unless the requested migration changes them.
- Read [Skill granularity](references/skill-granularity.md) when deciding whether a behavior belongs in a Skill, Tool or routing policy.

## Author and review

1. Keep `SKILL.md` focused on goal, applicability, supported profile, business inputs, completion and uncertainty. Put protocol and source traceability in `references/`.
2. For deterministic Skills, maintain `assurance/contract.yaml`, `procedure.yaml` and `predicates.yaml`. Use explicit arguments, exact callable exports and a final Postcondition that proves the Goal. Read the [syntax references](references/authoring-syntax.md) for the authoritative sections.
3. Put Skill-owned Schemas in `schemas/`. Link caller-supplied Owner contracts for Tool, Host and Observation types. Keep local computation in pure Scripts and derive Script inputs from the declared source bindings or Predicate signature.
4. Record semantic cases under `cases/<case>/case.yaml` and optional model knowledge under `references/`. Keep verification results tied to the gate that actually ran.

Run `make verify` for repository checks. Report Compiler, linking, Runtime and live acceptance separately when their respective implementations have been exercised.
