# TARGET01 — ca-agent Go Native Agent Host 当前架构重建

> 文档类型：外部目标/参考架构（实现派生重建）  
> 文档版本：0.1.0  
> 状态：依据当前 main README、Agent Contract 与 Host Artifact Store 设计重建；不是 Next Python Host 的目标设计  
> 功能归属：TARGET01；关联 F01、F02、F04、F05、G01  
> 修订日期：2026-11-25  
> 实现基线：ca-agent main 447d0cce7e42c7c1184b11fb2563792eead68d51

## 1. 定位

ca-agent 是 ConnectionAgent 官方 Go Native Agent Host。它负责 Intent 理解、Agent 侧路由、模型规划、Skill Context 组装、ProductTask 生命周期、Host 侧轨迹和 Host-local Artifact Store。受治理的副作用执行由独立 ca-runtime 和 Tool MCP Gateway 拥有。

~~~text
ProductTask v2 ingress
  -> ca-agent Native Host
       ├─ Intent / routing / model planning
       ├─ Skill eligibility / exact Skill load
       ├─ Context assembly / model-visible projection
       ├─ AgentInstance / ProductTask lifecycle
       ├─ Host trajectory / correlation
       └─ Host Artifact Store
  -> standard MCP client
  -> tool-mcp-gw
  -> RuntimeHost.v1
  -> ca-runtime
  -> Provider / Owner / Outcome / Reconcile
~~~

## 2. Host 所有权

Host 拥有 Intent、ProductTask、AgentInstance、模型交互、Agent 侧活动轨迹、Skill Context 装配、模型可见 Context、Host MCP 客户端集成和本地可靠性状态。Host 可以缩小可见 Tool surface，但不能扩大 Runtime 解析的 Toolset。

Host 不拥有 Provider wire protocol、Provider Catalog、Runtime Procedure 确定性执行、ProviderBinding、权威 Outcome、Reconcile、Runtime RunEvent、Service Fabric Observation、5GC/Environment 真相、GroundTruth 或 Benchmark Verdict。

## 3. ProductTask 与 Runtime Run 分离

ProductTask 是 Agent Host 拥有的业务任务生命周期；Runtime Run 是 Runtime 拥有的执行实例。一个 ProductTask 可关联零个、一个或多个 Runtime Run。Task、模型请求、Agent 私有会话和 Runtime Run 不得通过时间戳或相似 payload 推断成同一身份。

当前规范入口是 benchmark-neutral /api/v2/tasks。旧 /api/v1/tasks 是 v2 owner ledger 的兼容投影；旧 Lab bridge、direct RuntimeHost executor 已删除，不应重新引入为新消费者。

## 4. Tool 发现与执行

AgentInstance 或 MCP client generation 初始化时，Host 调用标准 MCP tools/list 并缓存 Server Tool Catalog。Goal + Skill 选择之后，Runtime/Harness 解析 Goal-scoped Toolset，Host 再与缓存 Catalog 求交集，形成请求可见的执行 Tool 集。缓存是 Catalog 发现结果，不是权限授予；Goal 到达不代表 Tool 权限变化。

执行调用走标准 MCP client → tool-mcp-gw → RuntimeHost.v1 → ca-runtime。Host 不自行执行 Provider，不拥有 Runtime Admission 或 Owner mutation 结果。

## 5. Context 与 Artifact

Host 负责 BaseContext、PlanningContext、ModelVisibleContext、ContextRequirement/Offer 和 NEED_CONTEXT 流程的 Host 侧装配。Host Artifact Store 负责 Artifact Reference 发放/解析、访问控制、配额、生命周期和发布。SBI Tool Provider 的 invocation-scoped artifact stream 由 Host 内部适配；这些接口不是模型可见 Tool，也不绕过 Runtime。

## 6. 与 Next 的关系

TARGET01 仅提供 Go Host 的实现和语义参考。Next 当前目标是 Python Host + 唯一 Plugin Manager + Next Runtime Action Boundary；不得将 ca-agent 的 ProductTask v2、MCP Gateway、Planning V2 或 Go Artifact Store 直接当成 Next 已有组件。只有当 Next 自己的架构/验收明确选择晋级时，才能形成迁移任务。

## 7. 当前实现审计

README 声明 canonical ProductTask v2 Host path 已实现并有 owner evidence；Planning V2 context assembly 仍标为 vNext，GOAL_PLANNING、Context Loader、revisioned PlanningContext、ModelVisibleContext 和 ContextOffer/NEED_CONTEXT 未声明实现。模型 live leg 受外部 provider entitlement 阻断。Host Artifact Store v1 有独立契约文档，不能据此推断 Next F05 已实现。

## 8. 来源材料

- [Agent Task Machine Contracts 原文](../../设计说明书/目标参考/TARGET01-Go%20Agent%20Task%20Machine契约原文.md)
- [Host Artifact Store v1 原文](../../设计说明书/目标参考/TARGET01-Go%20Host%20Artifact%20Store契约原文.md)
- [ca-agent main README](https://github.com/odango-chan/ca-agent/blob/447d0cce7e42c7c1184b11fb2563792eead68d51/README.md)
- [Frozen Agent Contract](https://github.com/odango-chan/ca-agent/blob/447d0cce7e42c7c1184b11fb2563792eead68d51/docs/agent.md)

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 从 ca-agent 当前 README 和冻结契约重建 Go Host 架构，明确与 Next 的非继承关系 | Issue #12；SR-021 |
