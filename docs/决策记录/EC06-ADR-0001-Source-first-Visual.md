> 源仓：`odango-chan/ca-skill-studio-demo`  
> 源路径：`docs/decisions/0001-source-first-visual.md`  
> 固定源提交：`5b666c0ef754ed32fa37c97ce2429f328c70477f`  
> 源文件 Git blob：`e661ea073fe0da1fca31d50a2da2c9af66cb08f4`  
> 原始状态：Accepted（2026-11-03）。本文件保留原始决策；仅将两个相对引用改为 Next 中对应的原文归档路径，不改变决策内容。当前工作台设计以 [F09](../设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md) 为准。  
> 迁移追踪：ca-agent-next Issue #12。

---

# ADR-0001 · Source-first Visual Editing

**Status: Accepted · Date: 2026-11-03**

## Context

Skill Studio 用 React Flow + ELK 展示真实 Skill `procedure.yaml`。若 Graph 成为另一份可保存的业务定义，视觉节点与原始 YAML 可能漂移；早期 Python POC 也不应该与已合入的 JavaScript 编辑器形成双权威。

## Decision

1. 用户当前的原始 Source/工作副本是唯一业务真源；Semantic Projection、React Flow、Inspector 和 ELK 位置是派生视图。
2. Visual mutation 只能使用明确准入的 Typed Source Patch：精准 Source Span、完整 Revision、预览 Diff、用户确认、重新投影、Undo/Redo。
3. 无法安全处理的未知结构，回退 Source-only；不通过整篇 YAML 序列化抹除注释、顺序或未知字段。
4. 不在 Studio 设计第二套 Skill DSL、Runtime Tool 资格或 5GC 状态机。

## Alternatives rejected

Graph JSON authoritative、同时维护 YAML/Graph 两个可保存业务模型、强行把 Python POC 合入现有 Runtime 作为编辑服务。

## Consequences

部分编辑器功能必须保持有限或 Proposed，直到 Parser/补丁/负面测试证明安全。接受 UI 的保守范围，而不牺牲 Source 的可审查性。详见 [Architecture](../架构设计/外部能力域/EC06-Skill%20Studio所有权与源码边界原文.md)、[Workbench](../设计说明书/外部能力域/EC06-Skill%20Studio/Authoring%20Workbench设计原文.md)。


## 迁移修订记录

| 日期 | 中央副本版本 | 修订者 | 修改内容 | 原因/影响 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 首次迁入；修复 Studio boundaries 与 Authoring Workbench 的相对链接 | 保留 Source-first 决策并使引用可在中央仓库导航；决策语义未变 | Issue #12；F09 |