# 通用 Agent Core 与 Host 设计说明书

> 文档类型：功能设计说明书  
> 文档版本：0.2.0  
> 状态：Next 目标设计；本仓实现状态需独立验收，不以参考仓 PASS 代替  
> 功能归属：F01 — 通用 Agent Core 与 Host  
> 关联 SR：SR-002、SR-020、SR-021  
> 修订日期：2026-11-25  
> 适用范围：Python Host、Agent Core、Model Loop、Event/Run 协调、Runtime/Plugin 边界

关联 IR-002、IR-006。参考架构原文见 §12。

## 1. 目标与原则

定义一个与 OpenAMSM、5GC、任何业务域无关的 Agent Core 和 Python Host。业务能力通过 Event Plugin、Skill、Tool Interface Package 和部署配置提供。新增业务不应要求修改 Core、Host、Skill Resolver 或 Runtime 中的业务专用分支。

必须保持：
- Core、Host、Model Loop、Skill Importer/Resolver、Runtime 使用 Python。
- Native Plugin 可使用 Go 或其他语言，但统一由 Python Plugin Manager 管理。
- Event Plugin 只规范化 Event；Skill Resolver 选择 Skill；Runtime 执行 Action；Owner 决定业务提交。
- 模型只能提出 Action，不能直接执行 Tool 或宣布 Owner Outcome。
- Deterministic 与 LLM-guided 两种执行模式共用 Runtime Action Boundary。

## 2. 组件与职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Host | 进程入口、配置、Plugin Manager 装配、Event 接收协调、Run/Response 生命周期 | 业务协议业务逻辑、Owner 状态 |
| Agent Core | 通用 Event/Goal 协调、Context 组装、Skill/Mode 流程协调 | OpenAMSM 路由表、5GC 状态机 |
| Model Loop | Model Client、模型输入投影、受约束 Action 提议 | 直接调用 Plugin、授权、提交判断 |
| Skill Importer / Catalog | 导入已发布 Skill Bundle、构建不可变 Catalog generation | 编译作者源、生产准入 |
| Skill Resolver | 对新 Event 选择精确 Skill；Continuation 恢复原 Skill | 业务执行 |
| Runtime | Run 状态、Action Boundary、Procedure、Wait/Resume、Outcome 解释 | Plugin 进程生命周期、模型推理 |
| Plugin Manager | Plugin 包/进程、IPC、Extension 分发 | Skill 选择、Owner outcome |
| Host ArtifactStore | 原始字节、opaque refs、Run/Invocation 关联与访问控制 | 协议业务解码 |

## 3. 进程与主要数据流

~~~text
外部业务请求
  -> Native Event Plugin
  -> Plugin Manager / ingress Extension
  -> Host Event Validator
  -> Event Deduplication / Response Obligation
  -> Skill Resolver (F02)
  -> Run Creation / Skill Binding
  -> Context Assembly
  -> Deterministic Procedure Engine OR LLM Model Loop
  -> Runtime Action Boundary (F04)
  -> Plugin Manager / tools Extension
  -> Tool Provider / Owner
  -> Outcome + Evidence
  -> Host Response Assembly
  -> Plugin Manager / delivery Extension
  -> 原始外部响应通道
~~~

Host 不要求 Event Plugin 知道 Run ID，也不允许 Plugin 自己决定 Skill。Host 负责把 Event、Run、Skill、Catalog generation、Artifact refs 和 responseObligation 关联起来。

## 4. Event、Run 与响应义务

Event 是外部协议归一化后的输入；Run 是 Host 为一次业务执行创建的生命周期身份；responseObligation 是 Host 对外部请求必须完成的响应义务。三者不能混用。

Host 至少维护：
- Event identity、ingressId、eventType、externalRequestId；
- 规范化 payload 和 Artifact refs；
- Run ID、绑定 Skill、Artifact identity、Catalog generation；
- responseObligationId、原始 responseChannelId；
- invocation refs、当前执行状态和结果；
- 重复请求、Continuation、Delivery 状态。

重复 externalRequestId：
- 内容和 Artifact bytes 可证明相同时，关联已有 Run 或既有结果，不重复 mutation；
- 同 ID 内容冲突、身份缺失或无法证明相等时，拒绝并输出诊断；
- Continuation 必须精确绑定原 Run，不重新选择 Skill。

## 5. Model Loop 与 Action 提议

Model Loop 不承担 Tool dispatch。每一轮模型输入由 Host 组装，至少包含：
- 当前 Goal/Event 的规范化视图；
- 已绑定 Skill 的 SKILL.md；
- 当前允许的 Callable 描述和 Schema 摘要；
- 已授权 Context / Observation；
- 当前 Run 位置和剩余 response obligation。

模型输出必须转换为结构化 Action Proposal。Host/Runtime 校验 Skill identity、Callable ID、参数 Schema、Artifact refs、Run state 和 invocation identity 后，才允许调用 Plugin。模型输出格式错误、未知 Callable、参数不完整或越权时停止，不自动猜测修复。

Model Client 是可替换适配器；自动化测试必须支持 Fake Model Client。模型 Provider、Gateway URL、模型 ID 和凭据属于部署配置，不进入业务 Skill 契约。

## 6. Context 与 Artifact 协调

Core 只协调 Context 需求，不拥有业务事实。Observation 必须经只读 Tool 能力获取；Owner Receipt/Commit Proof 由 Owner 发布并由 Runtime 解释。原始 N1/N2 等二进制由 Host ArtifactStore 管理，模型只看到明确允许的结构化投影和 Artifact metadata，不直接看到原始字节。

Context 与 Artifact 的详细契约见 F05。Model Loop 不得将模型生成内容伪装成 Observation 或 Evidence。

## 7. 新业务扩展模型

新增一个业务域的最小扩展：
1. Event/Delivery Plugin 声明协议 Event 和响应；
2. 一个或多个 Skill 定义适用条件和执行流程；
3. Tool Interface Package 定义外部 Callable 与 Schema；
4. Tool Plugin 适配对应 Provider；
5. Owner 实现业务状态和权威结果；
6. 部署配置将上述资产装配到 Host。

禁止新增 Event→Skill 业务路由表、Event→Mode 表、业务专用 Python Handler、重复 Tool Catalog 或 Owner 状态机。

## 8. 配置与启动

Host 启动时加载基础配置、Plugin manifests、Tool Interface Packages 和已发布 Skill Bundles；任何必需依赖加载失败时不得部分启用业务。配置包含 Plugin 安装位置、Model Client/Gateway、Skill Bundle 位置、Artifact staging/store 和日志级别。凭据通过部署安全配置提供，不接受业务 Event 注入 Provider Key。

Demo 以单 Host 进程和本机/内网 Plugin 进程为基线；不要求 HA、分布式调度或在线 Marketplace。

## 9. 失败与恢复

| 场景 | 处理 |
|---|---|
| Plugin 未 READY | 对应 Extension 不可用；不启动业务 Run |
| Event Schema 无效 | 拒绝 Event |
| 无匹配 Skill | 明确拒绝/澄清；不走 unbound fallback |
| 多个精确候选 | 只允许在候选集合内消歧 |
| Model 输出无效 | 不调用 Tool，保留诊断 |
| Runtime 拒绝 Action | 返回明确错误，不扩大权限 |
| Owner UNKNOWN | 保持 UNKNOWN，按 F04 精确 Receipt/Reconcile |
| Delivery UNKNOWN | 记录 response obligation 状态，不重放 mutation |

## 10. Demo 范围与非目标

要求具备单机可运行、可诊断、模块隔离、重复请求保护、统一 Action Boundary 和可复核的 Owner Outcome。暂不建设生产级 HA/DR、SLA、跨地域调度、复杂租户平台、生产 Skill Admission、签名/Trust Registry 或多层自动恢复系统。

## 11. 验收

- Core/Host/Model Loop 为 Python；业务逻辑不进入 Core。
- 一个 Echo Plugin 可触发至少一个 Skill，完成一次 LLM-guided Action 和一次 Deterministic Action。
- 新 Event 先绑定 Skill；没有候选时不执行。
- 所有模型 Action 都通过 Runtime Action Boundary。
- 重复 Event、Continuation 和 Delivery retry 不产生重复 mutation。
- Tool、Owner 和 Artifact 权限边界由测试证明。
- 新增业务不需要修改 Core/Resolver/Runtime 的业务分支。
- 参考仓的测试和 E2E 不作为 Next PASS；Next 必须在自己的分支和受测 SHA 上提供证据。

## 12. 参考架构与实现状态

- [ca-agent-demo Generic Host 规范架构原文](../../架构设计/参考实现/REF01-Python%20Generic%20Agent%20Host规范架构.md)
- [ca-agent-demo 执行路线原文](../参考实现/REF01-Generic%20Host执行路线原文.md)
- [ca-agent Go Host 当前架构重建](../../架构设计/目标参考/TARGET01-Go%20Agent%20Host当前架构重建.md)
- [ca-runtime 参考架构](../../架构设计/参考实现/REF02-CA%20Runtime架构.md)
- [Plugin 平台设计](../F03-Plugin平台/Plugin平台设计说明书.md)
- [Skill 管理与选择设计](../F02-Skill管理与选择/Skill管理与选择设计说明书.md)
- [Runtime 执行设计](../F04-Runtime执行/Runtime执行设计说明书.md)

当前 Next 的架构/设计文档与外部参考实现已迁入，但本轮未宣称 Next Host 代码、Plugin Manager 或端到端验收已完成。ca-agent-demo、ca-runtime、ca-agent 的状态分别在各自参考架构和实现审计中记录。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Core/Host/Model Loop 和业务中立基线 | SR-002 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 补齐 Event/Run/Response、Action Boundary、配置、失败恢复和跨仓实现差异 | Issue #12；SR-020、SR-021 |
