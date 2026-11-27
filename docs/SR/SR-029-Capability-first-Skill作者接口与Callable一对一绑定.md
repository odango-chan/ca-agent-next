# SR-029：Capability-first Skill 作者接口与 Callable 一对一绑定

> 文档类型：软件需求（SR）  
> SR 版本：0.2.9\
> 状态：DRAFT。Issue #90 在 Head `42a7fe2c` 对 AC-029-10 给出 CHANGES_REQUESTED；§10 已修订，待独立复评。
> 创建日期：2026-11-26  
> 修订日期：2026-11-27\
> 上游需求：[IR-008](../IR/IR%20总登记册.md#ir-008)；关联需求：[IR-003](../IR/IR%20总登记册.md#ir-003)  
> 功能：F02、F03.05、F04、F06、F08、F09、EC02  
> 设计 Issue：[ca-agent-next #40](https://github.com/odango-chan/ca-agent-next/issues/40)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §12（不包含下游仓代码修改、产品实施/发行或旧版兼容）
> 中央架构来源基线（不含本 SR 文件）：PR #44 Head 7f83bf6135d4572dca7d3d5bdb6243765440b0f6
> 复评入口：PR #46，`docs/issue-12-draft-design-review-20261126`
> 本 SR 性质：中央架构与规范设计；不授权修改任何下游实现仓

## 0. 设计评审与无兼容门槛

本 SR 仅是 CA-SL 1.6.0 Capability-first 的待评审设计。**无兼容**指：新作者规范、Compiler Parser/BuildRequest/BuildResult/Check/Build/Verify、Runtime Artifact、Agent Importer/Runtime、Studio 与 Bundle 全部只接受 1.6.0。没有旧包解析、别名、映射、双轨、版本协商、fallback、自动迁移或混合 Catalog。旧 Skill 必须人工重新编写、重新编译并发布，历史 v1alpha5 规范和 Golden 仅做只读审计。

Skill-facing Capability 与公开 Callable 严格双向一对一；Operation / Observation 只是 Node 阶段，Callable 和 backendOperationId 只保留在 Package/Compiler/Provider/Runtime 内部。1.6.0 的机器标识、正式 Schema、新 Compiler API、Owner/Provider Package、发布 Bundle 和跨仓 Golden 尚待外部 Publisher 冻结，**不能据本设计启动产品实施**。

## 1. 目标与范围

建立 Capability-first Skill 作者模型，使 Skill 只声明业务 Capability，不直接引用 Owner / Provider Callable ID。每个 Skill-facing Capability 必须唯一映射一个公开 Callable；Callable ID 只存在于 Package、Compiler、Runtime 和 Provider 的内部绑定 / 诊断中。

本 SR 同时闭合 CA-SL 作者语法、Owner / Provider Package、Compiler Link、Runtime Artifact / Action Boundary、Skill Studio Package Explorer，以及 OpenAMSM Create / Modify / Release 的真实示例映射。

本 SR 是中央设计候选，仅可提交独立技术评审，不表示实现可启动、下游已发布或 E2E 通过。

## 2. 固定基线与来源证据

| 来源 | 固定版本 / SHA | 本 SR 使用范围 |
|---|---|---|
| ca-skills | main 780497a2918ad3e7bdff554ab64b0ba627e867e0；CA-SL v1alpha5 发布规范 18d8184367982ccbc835756136c4a53f9096c3a0 | 当前 Contract.capabilities 与 tool: alias::Callable 作者源；v1alpha5 正式发布语义 |
| env-openamsm | main dc83ccbf5be54dcc7112dd43ba95ea6fa5975550；CapabilityContracts blob 4fdd22f0eda2c2f2b5096cd167bc705f5a29e06e；ToolCatalog blob 88d9709aac62c6d608d057dc797ada6f2189611f | Owner v1alpha4 Capability / Callable / Schema / Evidence / Reconcile |
| ca-client-tools | Release tag v1.2.0；provider-bindings blob 8e42e24eedc9e3211171f76a674c6be6bd6b1984 | Provider Interface 11 个 READ Callable、2 个 Capability、私有 backendOperationId |
| ca-skill-compiler | 产品 v2.1.0；Compiler 设计由 Next EC02 / SR-013 追踪 | v1alpha5 冻结 Build；Artifact v2 / BuildResult v2 候选 Owner Gate |
| ca-skill-studio-demo | 当前 main / PR 状态以 SR-016、F09 为准 | Package Explorer、LSP、AI Authoring 消费边界；本 SR 不写该仓 |

以上来源是历史基数审计证据，不表示 1.6.0 已发布，也不授权下游写入或任何兼容。

## 3. 当前契约基数审计

### 3.1 Owner CapabilityContracts v1alpha4

当前共有 24 个 Capability 条目、25 个 Callable membership。唯一多成员 Capability 是 mas.se.events.emit，关联 SE.EMIT_EVENTS 与 SE.EMIT_RELEASE_EVENT_C。

两个 Callable 的 Input Schema 不同：SE.EMIT_EVENTS 要求 event=ESTABLISHED 和 sessionKeys；SE.EMIT_RELEASE_EVENT_C 要求 ev=RELEASED。它们的 Evidence Guarantee 也不同：se.establishment-event-recorded 与 se.release-event-marker-written。因此不得把它们当成等价实现或硬合并为泛化 Callable。

目标拆分为：

| Capability ID | 唯一 Callable | 保留的契约语义 |
|---|---|---|
| mas.se.establishment-event.record | SE.EMIT_EVENTS | ESTABLISHED + sessionKeys；se.establishment-event-recorded |
| mas.se.release-event-marker.write | SE.EMIT_RELEASE_EVENT_C | RELEASED marker；se.release-event-marker-written |

当前 mas.reconcile.exact_original / MAS.RECONCILE 出现在 CapabilityContracts，但它是 Runtime internal-only Reconcile target。目标 CapabilityContracts 移除此 Skill-facing Capability；MAS.RECONCILE 仍保留在 Owner ToolCatalog 和 Mutation Reconcile binding 中。mas.receipt.query / MAS.RECEIPT_QUERY 仍保留普通 READ Callable / Capability 语义。

因此目标 Owner Skill-facing CapabilityContracts 为 24 个 Capability / 24 个 Callable membership；Owner ToolCatalog 仍为 25 个 contracts（21 MUTATION + 4 READ），不删除 Reconcile 契约。

### 3.2 Provider Interface v1.2.0

当前 Provider Interface 有 2 个 Capability、11 个公开 READ Observation Callable：

- openamsm.smf.mas.context.read：8 个 Callable，共用 mas-context-query-input 和 mas-context-result Schema。
- openamsm.nf.metrics.read：3 个 Callable，共用 metrics-page-query 和 metrics-page Schema。

目标各收敛为一个公开 Callable，Capability ID 分别保持 openamsm.smf.mas.context.read 和 openamsm.nf.metrics.read。SMF Context Read 的 Input 增加封闭 contextKind 枚举 sc / pa / upn / ssm / iam / ups / ca / saa；NF Metrics Read 的 Input 增加封闭 resourceKind 枚举 amf.ue-info / amf.gnb-info / smf.pdu-info。现有 8+3 个 backendOperationId 作为 Provider 私有实现路由保留，不再作为 11 个 Skill-facing Callable。

两个通用查询 READ 构成 2/2 子集。加入 SR-026 的一个 Codec READ 后，Provider 全量为 3 Capability / 3 公开 Callable。逐 Package 与跨 Package 合并均检查双向唯一，重复或缺项均失败。

## 4. 规范性设计决策

### 4.1 Capability ↔ Callable 一对一

- 每个 Skill-facing Capability 恰好映射一个公开 Callable。
- 每个公开 Callable 恰好属于一个 Skill-facing Capability。
- Capability 可以被多个 Skill 或 Procedure Node 重复引用；不改变 Package 内部的一对一映射。
- 一个 Capability 不得包含零个或多个公开 Callable；一个 Callable 不得被多个 Capability 共享。
- 公开 Callable 可由多个 Provider 内部 backendOperationId / handler 实现，但必须由 Callable Input Schema 的封闭 enum / tagged union 决定；不接受任意字符串、模型选择或动态 catalog 扩权。
- 若两个入口的业务语义、Schema、Effect 或 Evidence Guarantee 不同，应拆成两个 Capability / Callable，不为追求复用而合并。

### 4.2 Operation / Observation

Operation / Observation 是 CA-SL Procedure Node 阶段，不新增 Operation ID 身份。Callable.kind 决定阶段：

- operation.capability → kind=operation；Effect 由 ToolCatalog 决定，可为 READ 或 MUTATION。
- observation.capability → kind=observation 且 Effect=READ。
- Skill 不声明或覆盖 Callable.kind、Effect、Schema、Evidence 或 Owner identity。

### 4.3 Reconcile 与 Receipt Query

MAS.RECONCILE 是 Runtime Coordinator 的 internal-only target，不是 Skill-facing Capability。普通 Skill / LLM Action 在 Provider IPC 前拒绝并返回 INTERNAL_RECONCILE_ONLY，Provider IPC 次数必须为零。Coordinator 仅按原 Mutation Invocation、Scope 和 Correlation 调用。

MAS.RECEIPT_QUERY 继续是受 Capability / Scope 约束的普通 READ Callable，不适用 Reconcile 排除规则。

## 5. CA-SL 1.6.0 作者语法草案（待正式规范冻结）

CA-SL v1alpha5 已正式发布并冻结：其 operation.tool / observation.tool 继续表示 Alias::Callable，不做重解释或自动迁移。

Capability-first 直接使用 CA-SL 1.6.0 下一正式版本目标（尚未发布）。准确 languageTarget 机器标识由 ca-skills / Compiler 正式 Schema 与 Golden 冻结，禁止提前猜测。下列 Contract 是示例候选而非已冻结语法：

~~~yaml
dependencies:
  mas: urn:openamsm:mas:tool-contracts
capabilities:
  - mas.sc.context.create
  - mas.se.establishment-event.record
~~~

Procedure 外部调用只引用 Capability：

~~~yaml
record-session-establishment-event:
  operation:
    capability: mas.se.establishment-event.record
    arguments:
      ue_identity: context.supi
      psi: context.request.pduSessionId
      event: "ESTABLISHED"
      sessionKeys: create-sm-context.operation.output.session_keys
~~~

~~~yaml
emit-release-event:
  operation:
    capability: mas.se.release-event-marker.write
    arguments:
      ue_identity: context.supi
      psi: context.request.pduSessionId
      ev: "RELEASED"
~~~

~~~yaml
read-sm-context:
  observation:
    capability: openamsm.smf.mas.context.read
    arguments:
      contextKind: sc
      supi: context.supi
      pduSessionId: context.request.pduSessionId
~~~

dependencies 仍固定精确 Package 来源；Procedure 不再写 dependency alias::Callable。Compiler 在显式依赖闭包中唯一解析 Capability ID。未声明 Grant、未解析、重复导出和跨包歧义均 fail-closed。operation.script、when、Predicate、Precondition、Postcondition、Wait 和 Continuation 语义不变。

## 6. Package / Publisher 契约

Owner CapabilityContracts 与 Provider Interface Package capabilities.json 是 Skill-facing Capability 来源；ToolCatalog / Provider tool-catalog.yaml 是 Callable 契约来源。当前数组结构可保留，但每个 Skill-facing Capability 的 membership 数量必须为 1，每个 Callable 只能归属一个 Capability。

Owner 1.6.0 目标：

- 24 Skill-facing Capability / 24 Callable membership。
- 事件 Capability 拆分为 establishment-event.record 与 release-event-marker.write。
- 从 Skill-facing CapabilityContracts 移除 mas.reconcile.exact_original。
- Owner ToolCatalog 保留原 25 contracts 和 Reconcile 专用契约。

Provider Interface 目标：

- 两个通用查询 READ 构成 2/2 子集。加入 SR-026 的一个 Codec READ 后，Provider 全量为 3 Capability / 3 公开 Callable。逐 Package 与跨 Package 合并均检查双向唯一，重复或缺项均失败。
- 11 个原 backendOperationId 保留为 Provider 私有路由。
- SMF / NF 查询通过封闭 selector 字段进入同一个公开 Callable，不公开 11 个独立 Callable。

Package 版本由各 Publisher 在后续目标仓 SR 中固定；本 SR 不擅自发明 Owner / Provider 版本号，也不修改任何下游 Package。

## 7. Compiler Link 与 Runtime Artifact

Compiler 必须对每个 Capability 使用点执行：

1. Capability ID 必须出现在当前 Skill Contract.capabilities。
2. 在显式依赖闭包中唯一命中一个 Capability export。
3. 该 Capability 必须恰有一个 Callable membership。
4. 该 Callable 只能归属一个 Skill-facing Capability。
5. 同一 Package / Owner ToolCatalog 中 Callable ID、Owner、kind、Effect、Input/Output Schema 必须一致。
6. Procedure 阶段必须与 Callable.kind 匹配；Observation 还必须 Effect=READ。
7. 复用既有 Schema closure、Evidence、Scope identity / provenance、Receipt / Commit Proof / Reconcile 校验。
8. 未使用 Grant 报 CAPABILITY_GRANT_UNUSED；不生成部分 Artifact。

稳定诊断至少包括：CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_GRANT_UNUSED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH、CAPABILITY_BINDING_MISSING。

Compiler Artifact / BuildResult v2 候选只面向 languageTarget=（1.6.0 的机器标识待正式冻结）。每个 Skill 的 capabilityBindings[] 至少记录 capabilityId、dependencyId、stablePackageId、Owner / Publisher identity、callableId、kind、effect、inputSchemaRef 和 outputSchemaRef。Procedure 节点保留 capabilityId；Artifact dependencyClosure.exports[] 保留精确 Callable allowlist。Callable ID 是内部 Binding，不是模型 Action 参数。

v1alpha5 已发布 Artifact、Compiler v2.1.0 历史行为和 Golden 不变；Development v1alpha1 保持冻结并 NOT_ADMITTED。Artifact v2 / BuildResult v2 API 名称仍须 Compiler Owner Gate 确认；新 Compiler/Agent 不提供任何旧版语法、旧 Build DTO/Artifact/Bundle、双轨或 fallback。

## 8. Runtime Action Boundary

Runtime 以 Capability ID 为 Skill / Procedure 作者侧 Action 入口，从当前 Artifact 的唯一 capabilityBindings 项解析 Callable ID。通过精确 Callable allowlist、Package identity、kind、Effect、Schema、Run 状态、HostInvocation、Scope、deadline 和 budget 检查后，才经唯一 Plugin Manager 的 Tools Extension / ProviderV2 Driver 内部派发。

模型不能提交或替换 Callable ID，也不能枚举 backendOperationId。Provider 可在一个 Callable 内按封闭 Schema selector 选择私有 backend。MAS.RECONCILE 仅允许 Runtime Coordinator 内部入口使用。

## 9. Skill Studio Package Explorer / LSP

- Package Explorer 以 Capabilities 为唯一 Skill-facing 能力导航；不展示平级 Tools / Operations / Callable 树。
- Capability 详情可显示描述、kind、Effect、Schema、Evidence 和来源 Package。
- Callable ID 只出现在内部 Binding 详情或编译诊断，不作为作者可选入口。
- LSP 对 Contract.capabilities、operation.capability、observation.capability 提供补全、悬停、定义跳转和静态诊断；来源为已导入 Package，不是 Provider 动态 catalog。
- AI Authoring 只能生成 Capability ID，不得生成 Callable ID 或 backendOperationId。
- **新 Studio 仅接受 1.6.0 项目**。v1alpha5 作者源码和旧项目快照只能作为历史审计资料保留，不能导入新版 Studio，不提供转换/自动迁移、双语法或混合语言项目。

## 10. OpenAMSM 示例映射

以下按原 Procedure 的节点顺序列出全部 `tool: mas::…` 引用。固定作者源为 ca-skills `780497a2918ad3e7bdff554ab64b0ba627e867e0`，对应 [Create Procedure](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/establish-pdu-session-mas/assurance/procedure.yaml)、[Modify Procedure](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/modify-pdu-session-mas/assurance/procedure.yaml)、[Release Procedure](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/release-pdu-session-mas/assurance/procedure.yaml)。Callable 列省略共同的 `mas::` 前缀。目标列取自 §2 固定 Owner CapabilityContracts，并应用 §3.1 的两项事件拆分。

| Skill | v1alpha5 Owner Callable | 1.6.0 设计目标 Capability |
|---|---|---|
| Create | `SC.VALIDATE_SUBSCRIPTION` | `mas.sc.subscription.validate` |
| Create | `SAA.SECONDARY_AUTH` | `mas.saa.secondary.auth` |
| Create | `SC.CREATE_SM_CONTEXT` | `mas.sc.context.create` |
| Create | `SC.REGISTER_UECM` | `mas.sc.uecm.register` |
| Create | `PA.CREATE_SM_POLICY` | `mas.pa.sm.policy.create` |
| Create | `UPS.DECIDE_ANCHOR` | `mas.ups.anchor.decide` |
| Create | `IAM.ALLOCATE_ADDRESS` | `mas.iam.address.allocate` |
| Create | `PA.UPDATE_SM_POLICY` | `mas.pa.sm.policy.update` |
| Create | `CA.CREATE_CHARGING` | `mas.ca.charging.create` |
| Create | `UPN.CREATE_UP_SESSION` | `mas.upn.up.session.create` |
| Create | `SSM.SIGNAL_UE_AN` | `mas.ssm.ue.an.signal` |
| Create | `UPN.MODIFY_UP_SESSION` | `mas.upn.up.session.modify` |
| Create | `SE.EMIT_EVENTS` | `mas.se.establishment-event.record` |
| Modify | `SSM.PARSE_N1_MODIFY` | `mas.ssm.n1.modify.parse` |
| Modify | `UPN.MODIFY_QOS_DELTA` | `mas.upn.up.qos.delta` |
| Release | `SSM.PARSE_N1_RELEASE` | `mas.ssm.n1.release.parse` |
| Release | `SSM.BUILD_RELEASE_COMMAND` | `mas.ssm.n1.release.build` |
| Release | `SSM.RELEASE_CONFIRM_N1` | `mas.ssm.n1.release.confirm.n1` |
| Release | `SSM.RELEASE_CONFIRM_N2` | `mas.ssm.n1.release.confirm.n2` |
| Release | `PA.DELETE_SM_POLICY_C` | `mas.pa.sm.policy.delete` |
| Release | `UPN.DELETE_UP_SESSION` | `mas.upn.up.session.delete` |
| Release | `SE.EMIT_RELEASE_EVENT_C` | `mas.se.release-event-marker.write` |
| Release | `SC.RELEASE_SM_CONTEXT_C` | `mas.sc.context.release` |

AC-029-10 按 Skill 分别提取并去重 `mas::` 引用，与表中对应 Callable 集合做双向差集。Create 应有 13 项、Modify 2 项、Release 8 项；遗漏、额外引用或同一目标绑定多个 Callable 均不满足此项设计。按 §3.1 分别核对两项事件的 Schema 与 Evidence Guarantee，Modify 保留 QoS Delta、Receipt、UNKNOWN 与原 N1/N2 流程。表格只覆盖三个 Procedure 实际使用的 Owner Callable。Owner 全包目标 24/24 见 §3.1，Provider 查询与 Codec 的闭包另见 AC-029-05。正式作者源、Owner 发布和运行验收仍按各自门槛取证。

## 11. 实施分解与跨仓责任

本 SR 只完成中央设计。后续代码实施必须先按目标仓拆分独立实施 SR / Issue，至少覆盖：

1. ca-skills：1.6.0 规范、作者语法、Owner-linked Create / Modify / Release 示例和发布记录。
2. env-openamsm：Owner CapabilityContracts 事件拆分、Reconcile Capability 移除及新 Owner Package 发布。
3. ca-client-tools：Provider Interface 两个通用 Callable、selector Schema 和内部 backend 路由。
4. ca-skill-compiler：1.6.0 Parser / Linker、Artifact v2 capabilityBindings、Build / Verify / Golden。
5. ca-agent-next：F02 / F04 Runtime 消费和 Action Boundary。
6. ca-skill-studio-demo：Package Explorer、LSP、Completion、AI Authoring。
7. ca-skills Bundle / OpenAMSM E2E：按固定 Compiler / Package / Skill 发布物完成端到端回归。

实施顺序：先冻结 1.6.0 作者格式、Owner/Provider 一对一映射与 Schema；ca-skills 正式发布 1.6.0；Compiler 发布新 BuildRequest/BuildResult/Artifact/唯一 Capability Binding；Runtime/Studio 消费；MAS Skill 由作者按 1.6.0 重新编写、重新 Build/Verify/Bundle 后才跑真实 E2E。每个目标仓另设实施 Issue/AC 与授权；本 SR 待评审不代表实施 READY。

## 12. 非目标

- 不修改已发布 CA-SL v1alpha5、Compiler v2.1.0 Artifact / Golden。
- 不做旧版本兼容、自动迁移或双语法运行时。
- 不新增 Capability Manager、Tool Registry、Provider Manager 或第二套 IPC。
- 不增加生产 Admission、签名、Trust Registry、额外包级 hash、复杂 IAM 或生产 Qualification。
- 不把 Provider 私有 backendOperationId 提升为 Skill-facing Callable。
- 不修改 ca-skills、ca-skill-compiler、ca-client-tools、env-openamsm、ca-skill-studio-demo 的代码、文档、Issue 或 PR。

## 13. 验收条件

| AC | 验收内容 | 结果 |
|---|---|---|
| AC-029-01 | Owner CapabilityContracts 当前 24/25 基数与唯一多成员关系有固定来源审计 | 来源审计已记录，待独立评审 |
| AC-029-02 | Provider Interface 当前 2/11 基数、8+3 查询分组与共享 Schema 有固定来源审计 | 来源审计已记录，待独立评审 |
| AC-029-03 | Capability ↔ Callable 双向一对一、Operation/Observation kind、Effect、Schema 规则明确 | 设计已记录，待独立评审 |
| AC-029-04 | Owner 事件 Capability 拆分、Reconcile internal-only、Receipt Query 保留规则明确 | 设计已记录，待独立评审 |
| AC-029-05 | 查询 2/2、含 Codec 全量 3/3；单包及跨包重复绑定或漏 Codec 均失败；封闭 selector 只选择私有 backend | 设计已记录，待独立评审 |
| AC-029-06 | 1.6.0 正式命名、完全无兼容/自动迁移、准确机器标识与作者 Schema 发布责任清晰 | 待独立设计评审 |
| AC-029-07 | Compiler Link、诊断、Artifact v2 capabilityBindings 与 Build/Verify 边界明确 | 设计已记录，待独立评审 |
| AC-029-08 | Runtime Action、Callable allowlist、Reconcile 内部入口明确 | 设计已记录，待独立评审 |
| AC-029-09 | Skill Studio Capability-only Explorer / LSP / AI Authoring 明确 | 设计已记录，待独立评审 |
| AC-029-10 | MAS Create / Modify / Release 的 1.6.0 Capability 映射与业务语义保持边界明确 | §10 按固定源逐项对照 13/2/8；待独立复评 |
| AC-029-11 | F02/F03/F03.05/F04/F06/F08/F09/EC02、IR/SR、版本规范/功能树/目录与 SR-004 一致；核查 EC02《工具链设计》、三层旧包拒绝与当前导航。查询子集 2/2，含 Codec 的总闭包 3/3；逐包检查唯一性，跨包重复也须拒绝，缺 Codec 不得计全量通过。实际发布前仅验设计 | 待静态检查与独立评审 |
| AC-029-12 | 未修改下游仓；未把设计目标误报为实现或 E2E PASS | 待独立评审 |

## 14. 依赖与状态边界

- 设计依据：SR-015 的历史 Tool/Provider 审计，SR-004 1.6.0-only Importer，SR-013 新 Compiler Artifact，SR-027 正式 Bundle；旧 v1alpha5 仅留档。
- SR-029 的设计不依赖 Compiler / Provider / Studio 代码已实现；稳定契约足以完成设计评审。
- SR-013 需要将 when/Schema/Artifact 与 SR-029 Capability Binding 一并升级为 1.6.0-only 新 Compiler API；旧 when 设计/旧 CI 不能证明 1.6.0 发布。
- 当前 GitHub Issue #40 是设计 Issue，不是下游实施 Issue。
- 本轮 DeepSeek Harness、Compiler Build / Verify、Studio 浏览器测试、MAS E2E 均 NOT_RUN；未修改下游仓。

## 15. 设计评审记录

- 2026-11-26，GPT-6（ChatGPT）：将历史基数审计移植到最新 1.6.0-only 中央设计分支，提交待评审；未声称正式 APPROVE。
- GitHub PR 保持 Draft；未提交正式 APPROVE、未合并 PR、未修改 main。
- 待评审仅为技术设计审查状态；不是实施 READY、Compiler/Runtime/Studio 产品实现证据或 E2E PASS。

## 修订记录


| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Capability-first Skill 作者接口、一对一 Callable、Package cardinality 审计及 Compiler / Runtime / Studio 闭环 | 消除 Skill 源码与 Provider / Owner 内部 Callable ID 的耦合，并明确 v1alpha5 冻结与 1.6.0 候选边界 | IR-008、IR-003、Issue #40 |
| 2026-11-26 | 0.2.0 | GPT-6（ChatGPT） | §0～15、修订记录 | 移植 Capability-first 与 Owner/Provider cardinality 审计，刷新为 1.6.0-only、无旧兼容，状态改为待独立评审 | 保留历史基数证据、明确设计评审与产品交付分离 | Issue #40；SR-029；SR-004；SR-013；SR-027 |
| 2026-11-26 | 0.2.1 | GPT-6（ChatGPT） | 版本隔离与修订记录 | 补齐 Studio 拒绝旧项目边界，设计待评审 | 避免历史代码/测试被视为新版有效输入 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.2 | GPT-6（ChatGPT） | 标题层级/修订记录 | 修正历史修订表列数与独立设计评审状态 | 满足 Markdown 设计评审门禁，避免编号或治理表歧义 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.3 | GPT-6（ChatGPT） | 文档头与修订记录 | 补齐 formal SR 正式 review_scope 与非目标声明 | 解除 PR #45 当前 Head Review Context formal-doc 校验失败 | Issue #40；PR #45 |
| 2026-11-26 | 0.2.4 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 提交设计待评审、明确新旧契约/验收隔离并保留 DRAFT 主状态 | 统一中央评审批次，防止旧版发布证据冒充新版资格 | Issue #12；PR #45；SR-029 |
| 2026-11-27 | 0.2.5 | Codex / GPT-6 | §3.2、§6、AC-029-05/11 | 区分查询子集与 Provider 全量 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.6 | Codex / GPT-6 | AC-029-11 | 覆盖 F03 主设计、EC02 工具链与跨包版本导航 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.7 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | CA-SL 1.6.0-only、Owner 24/24、Provider 查询 2/2 与含 Codec 3/3、旧包拒绝及跨包双射已明确；生产者机器契约另行冻结；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-029 |
| 2026-11-27 | 0.2.8 | GPT-6（ChatGPT） | 文档头、评审状态、修订记录 | 将第三轮独立模型 Review #6082541121 的限定结论替换第三轮自评状态 | 区分中央语言/作者模型设计认可与生产者正式机器契约发布 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.9 | Codex / GPT-6 | 文档头、§10、AC-029-10 | 补全三个 Procedure 共 23 条 Owner 映射与集合核验规则，区分架构来源与评审入口 | 处理 R1-SR029-01/02 | Issue #12、#90；PR #46 |
