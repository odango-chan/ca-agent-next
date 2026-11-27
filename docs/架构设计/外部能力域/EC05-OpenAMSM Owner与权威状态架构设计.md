# EC05 — OpenAMSM Owner 与权威状态架构设计

> 文档类型：外部能力域架构设计（实现派生重建）  
> 文档版本：0.1.2\
> 状态：依据当前 main 代码、Owner 声明、契约和验收材料重建；源仓没有独立总体架构文档  
> 功能归属：EC05；关联 F04、F05、F06、F07  
> 关联需求：IR-004、IR-005；SR-007、SR-010、SR-011、SR-018、SR-025\
> 修订日期：2026-11-25  
> 实现基线：env-openamsm main dc83ccbf5be54dcc7112dd43ba95ea6fa5975550\
> 全局评审范围：继承根目录 Agent.md 的 review_scope\
> 本文局部非目标：不重建 Agent Runtime、Provider、Plugin 或 Studio 内部实现；不扩展到生产级 DFX 或全量 3GPP 资格

## 1. 架构定位与权威归属

OpenAMSM SMF MAS Owner 是 5GC 会话业务状态和副作用的权威执行者。它承载具体业务 Operation，掌握 SM Context、Policy、PFCP、N1/N2 过程和最终提交事实。Agent 负责流程编排，Tool Provider 负责契约化调用适配，Runtime 负责统一 Action Boundary 与 Run 结果解释；三者均不得伪造 Owner 提交事实。

~~~text
Next Agent / Runtime
  -> Runtime Action Boundary
  -> Plugin Manager / Tool Extension
  -> ca-client-tools Provider
  -> OpenAMSM MAS SBI
  -> MAS Owner operations
       ├─ SC: session context lifecycle
       ├─ PA: policy association
       ├─ UPN: UPF / PFCP
       ├─ SSM: N1/N2 signalling and confirmation
       ├─ SE: event exposure
       ├─ IAM / UPS / CA / SAA: supporting operations
       └─ MAS: receipt query / exact-original reconcile
~~~

Owner 的权威结果必须来自 Owner 返回的 typed output、durable Receipt 和 Commit Proof。HTTP 200、进程内缓存、Agent 自己的推断、旧 Run 的消息或模拟状态都不能代替提交证明。

## 2. Owner 发布物与契约层

Owner 以 contracts/mas/operations.yaml 作为声明源，由 publish.py 生成 v1alpha4 发布目录。当前 main 的 operations.yaml 包含：

- 23 个 MAS 业务 Callable；
- 2 个独立证据读取 Callable：MAS.RECEIPT_QUERY 与 MAS.RECONCILE；
- 生成的 ToolCatalog、Capability Contracts、输入/输出 JSON Schema、Evidence Guarantees、Receipt/Proof/Reconcile Schemas、Deployment Binding 与 Manifest。

ToolCatalog 描述 Callable ID、Effect、Capability、输入输出 Schema 和 Owner 结果语义。MUTATION Callable 必须有 Receipt Schema、Commit Proof 和精确原始 Invocation 关联。READ Callable 不得被误报为副作用提交。

Owner 声明源、发布产物、Provider 绑定与 Skill 作者源分别归属不同仓库；Next 只消费正式发布契约，不复制 Owner 操作实现。

## 2.1 CA-SL 1.6.0 Capability-first 发布目标

本节是 Next 新目标设计，不改写 env-openamsm v1alpha4 已发布字节和现有业务实现。

| 项目 | 历史 Owner v1alpha4 | 新 CA-SL 1.6.0 目标 |
|---|---|---|
| CapabilityContracts | 24 Capability / 25 Callable membership；唯一多成员项为 mas.se.events.emit | 24 Capability / 24 public Callable；establishment / release marker 两种事件分别成为 Capability |
| Reconcile | mas.reconcile.exact_original 曾出现在 Skill-facing CapabilityContracts | 从 Skill-facing CapabilityContracts 移除；MAS.RECONCILE 保留 ToolCatalog 和 Mutation Reconcile binding，Runtime Coordinator internal-only |
| Receipt Query | MAS.RECEIPT_QUERY 为普通受控 READ | 保持普通 Skill-facing READ Capability / Callable |
| ToolCatalog | 25 contracts（21 MUTATION + 4 READ） | 保留 25 contracts；不删除内部 Reconcile contract |
| 发布 | v1alpha4 Owner source / package | SR-025 重新发布 1.6.0 Capability-first Package；新发布物尚未交付 |

新作者不得写 Owner Callable ID。Compiler 必须从显式依赖 Package 唯一解析 Capability→Callable，并校验 kind、Effect、Schema、Owner identity；不得以旧 24/25 membership 或旧 Artifact 作为新输入。具体新 Package Schema / Publisher 版本由 SR-025 与 Compiler 1.6.0 契约冻结。

## 3. Owner 组件边界

| 子域 | 权威职责 | 关键边界 |
|---|---|---|
| SC | SM Context 创建、注册、释放与生命周期 | 只有 Owner 决定 Session Context 最终状态 |
| PA | PCF Policy Association 创建、更新、删除 | Policy 结果不是 UPF 状态 |
| UPN | UP Session、PFCP Session 与 QoS/QER 修改 | PFCP request/response 是真实副作用边界 |
| SSM | N1/N2 消息解析、构造、等待和确认 | 以明确的 NAS/NGAP 消息类型和事务身份关联 |
| SE | Owner 事件/Release Marker | 事件标记不能替代实际资源清理 |
| IAM / UPS / CA / SAA | 地址、Anchor、Charging、Secondary Auth 等支持能力 | 只暴露已发布的具体 Callable |
| MAS common | Receipt、Commit Proof、查询和精确 Reconcile | 不引入第二份业务数据库或独立业务状态机 |

## 4. Durable Mutation Receipt

对 MUTATION，Owner 在首次派发副作用之前写入 PREPARED Receipt，使用临时文件、fsync、原子 rename 和目录 fsync；终态 Receipt 在响应发出前写入。重复的 originalInvocationId 不得再次派发。Receipt key 绑定 deploymentId、ownerInstanceId 和 originalInvocationId。

终态语义：

| 状态 | 含义 | Runtime 处理 |
|---|---|---|
| COMMITTED | Owner 能证明该原始调用的效果已提交 | 只有有效 Commit Proof 才可作为成功 |
| NOT_COMMITTED | Owner 能证明没有产生副作用 | 可报告明确失败；不能当作成功 |
| UNKNOWN | 副作用可能发生，但 Owner 无法证明终态 | 保持未知，禁止把 UNKNOWN 映射成 COMMITTED |

Receipt 包含 Owner 身份、原始 Invocation、Callable、业务主体（SUPI/PSI/sessionRef）、Owner generation、事务关联和结果摘要。Receipt 查询按完全相同的 originalInvocationId/deploymentId/ownerInstanceId 读取。

## 5. Exact-original Reconcile

Reconcile 是只读、精确绑定的结果判定，不是重放业务操作。请求必须绑定原始 Invocation、deployment、Owner instance，并带 operator/reason。它只允许读取同一事务可证明的 Owner/PFCP 事实：

- 已终态 Receipt 原样返回；
- PFCP deletion UNKNOWN 只能基于同一 SUPI/PSI、generation、step、correlation、epoch、N4 SEID 和 UPF 身份做显式判定；
- 不具备原始事务证明时保持 UNKNOWN；
- 不重发 mutation、不换绑其他 Session、不将 PFCP deletion 结论推广为其他 Callable 的成功证明。

## 6. Create、Modify、UE-requested Release 业务链

### 6.1 Create

创建链按已发布 Owner Callable 执行：Subscription validation、Secondary Auth（按契约）、SM Context、UECM registration、Policy association、UP anchor、Address allocation、Charging、UP Session establishment 和必要的 signalling/exposure。每一步输入输出由 Owner ToolCatalog 与 Schema 固定。只有 Owner 证明的结果才能推进后续步骤。

### 6.2 Modify

UE Modify 的输入是 5GSM PDU Session Modification Request，NAS message type 0xC9。只读 parse 得到 QFI、5QI、GFBR/MBR；UPN 按 typed QoS delta 执行 QER modification（PFCP 52/53），再由 SSM 完成 N1/N2 delivery。PFCP 已应用但 N1/N2 transfer 失败时，Owner 必须返回失败/未知语义，不得报成功。Agent 不解码 NAS、不计算 QER、不直接修改 Owner state。

### 6.3 UE-requested Release

UE-requested Release 的 NAS message type 是 0xD1，与 AMF/network-initiated ReleaseSMContext 不得混为一谈。SSM 解析请求并构造 N1 Release Command（0xD3）和 N2 PDU Session Resource Release Command。Agent 只负责将命令交给对端并关联原始 Run。N1 Release Complete（0xD4）与 N2 PDU_RES_REL_RSP 是两个独立确认，必须绑定同一 generation、releaseTxn 和原始 Run。两者都到达后，才执行 Policy 删除、PFCP Session Deletion（54/55）、Release Event 和 SM Context finalize。

## 7. 失败、重放与并发约束

- Owner mutation 使用稳定 originalInvocationId，重复调用不得再次产生副作用。
- Receipt 不可解析、持久化失败或原始调用重复时，拒绝派发。
- UNKNOWN 不能被迟到消息、缓存、HTTP 状态或不同 generation 的结果提升。
- PFCP deletion UNKNOWN 阻断普通删除重试和 Context finalize，只有显式 exact-original reconcile 可以解除受限 finalize gate。
- N1/N2 迟到、重复、乱序或身份不匹配必须 fail closed。
- Owner 的业务状态与 Agent/Runtime 的调用者知识分离。

## 8. 当前实现审计

| 能力 | 当前证据 | 状态 |
|---|---|---|
| Owner 发布声明 | contracts/mas/operations.yaml、contracts/mas/v1alpha4/** | IMPLEMENTED |
| 23 业务 Callable + 2 证据 READ | 当前 operations.yaml 实际枚举 25 条；其中最后两条为 RECEIPT_QUERY / RECONCILE | IMPLEMENTED |
| Durable Receipt / Commit Proof | docs/mas-owner-contracts-and-receipt.md、patches/openamsm/0023-mas-durable-receipt.patch | IMPLEMENTED；源仓单测/构建有证据 |
| Exact-original Reconcile | docs/scheme-c-pfcp-reconcile.md、Owner PR #21 的设计与证据记录 | IMPLEMENTED；源仓文档声明真实 ac 栈验收 |
| Scheme C Modify | docs/scheme-c-owner-qos-delta.md、Owner patches 0006～0010 | IMPLEMENTED；源仓记录真实 PFCP 52/53 和 N1/N2 路径 |
| UE-requested Release | Owner patches 0011～0017、N1 0xD1 / 0xD4 和 N2 response binding | IMPLEMENTED；源仓记录真实隔离 E2E |
| Next Plugin / Runtime 端到端调用 | EC04 Plugin main 尚无代码，ca-agent-demo PR #246 未合并 | NOT_IMPLEMENTED / NOT_RUN |
| Production Qualification | 本项目 Demo 非目标 | NOT_CLAIMED |

## 9. 非目标

不新增 Owner 数据库、独立业务状态机、通用 Saga 引擎、额外信任注册中心、生产级 HA/DR 或跨 Owner 全局事务。Owner 只声明并执行其实际支持的 Operation。

## 10. 来源材料

- [MAS Owner Receipt / Proof 原文](../../设计说明书/外部能力域/EC05-OpenAMSM%20Owner/MAS%20Owner契约与Receipt设计原文.md)
- [Scheme C Modify / Release 原文](../../设计说明书/外部能力域/EC05-OpenAMSM%20Owner/Scheme%20C%20Modify与Release%20Owner设计原文.md)
- [PFCP UNKNOWN Reconcile 原文](../../设计说明书/外部能力域/EC05-OpenAMSM%20Owner/PFCP%20UNKNOWN%20Reconcile与重启恢复设计原文.md)

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 根据 Owner 发布声明、Receipt、Scheme C 设计和当前主线文件重建架构；标记为实现派生重建，避免虚构原始架构文档 | Issue #12；SR-018 |

| 2026-11-26 | 0.1.1 | GPT-6（ChatGPT） | 1.6.0 新目标与历史边界 | 增加 1.6.0 Owner Capability 24/24 目标与 Reconcile internal-only 边界，保留 v1alpha4 为历史实现基线 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.1.2 | GPT-6（ChatGPT） | 文档头、§2.1、修订记录 | 补齐治理要求的全局评审范围与局部非目标；将 SR-025 纳入 1.6.0 Publisher 关联 | 使正式文档通过 review_scope 头部门禁，并显式追踪 Owner 新发布责任 | Issue #12/#40；SR-025；PR #46 |
