# Tool Interface 与 Provider 集成设计说明书

> 文档类型：功能子模块设计说明书
> 文档版本：0.3.2
> 状态：目标设计；待评审
> 功能归属：F03.05 — Tool Plugin 集成
> 交叉功能：F03.01～F03.04、F04.01、F04.05、F05.02、F06
> 关联 SR：SR-003、SR-007、SR-010、SR-015
> 全局评审范围：继承根目录 Agent.md 的 review_scope。
> 本文局部非目标：不实施 Provider/Host 代码迁移，不修改外部仓库，不完成 Codec Phase C，不声明生产资格。
> 修订日期：2026-11-25

本文定义 CA Agent Next 如何消费 Tool Interface Package、Owner Contract Package 和 Provider Runtime Bindings，并将 Provider 作为唯一 Plugin Manager 管理的 Tools Extension 接入。本文是 **Next 消费侧架构与集成行为的权威设计**；外部包的实际字段、发布物和实现仍由各自所有者维护，Next 不复制其完整 Catalog 或 Schema。

## 1. 目标与范围

### 1.1 目标

1. Tool 是 Plugin 导出的 Callable Operation，不是独立进程、Manager、Registry 或 Runtime。
2. 所有 Tool Provider 均由唯一 Plugin Manager 管理；Runtime 是唯一 Action 调用与授权边界。
3. Skill 只声明其依赖的 Capability / Callable，不接触 Provider 私有 backend ID、服务地址、凭据或私有 Host 参数。
4. Compiler 构建时使用精确的 Provider Interface / Owner Contract 依赖快照；冻结 v1alpha5 Artifact 仅记录 dependency alias、stablePackageId 和导出集合，不携带依赖版本或 snapshotDigest。Next 的 Demo 部署因此通过 provider.yaml 的 `interfacePackagePath` / `interfaceSnapshotDigest` 固定 Provider Interface snapshot，并通过 Provider Runtime Bindings 的 Owner stable ID、version、publicationDigest 和 manifestDigest 固定 Owner 发布物；不得宣称 Artifact 本身实现了逐 Skill 的字节级依赖锁。
5. Owner 对业务状态、Receipt、Commit Proof 和 Reconcile 负责；Provider/IPC/HTTP 成功不构成业务提交证明。
6. 复用 ca-agent-demo 已有的 Schema 校验、Effect 一致性、精确 Callable Scope、UNKNOWN 和 exact-original reconcile 机制，但不把 Demo 的手工注册、5GC 业务装配或第二份契约源搬进 Next。

### 1.2 范围

- Tool Interface Package 与 Skill 编译依赖的关系。
- Owner Contract Package 与业务结果语义的权威归属。
- Provider Runtime Bindings、Provider v2 进程协议及私有 backend 映射。
- Plugin Manager 的 Tools Extension 加载、启动、握手、调用和错误处理。
- Runtime Action Boundary、Capability / Callable Scope、Schema、Effect、Owner Receipt 与 Reconcile 的协作。
- 二进制 Artifact 与按需 Codec Operation 的边界。
- ca-agent-demo 可复用代码和不可复用业务代码的审计结论。

### 1.3 非目标

- 新建 Tool Manager、Provider Manager、Tool Registry、Codec Manager、Event Registry 或第二套 Runtime。
- 在 Agent Core 中维护业务 ToolCatalog、Provider 私有 backend 映射或 Owner 状态映射副本。
- 把 Provider 的动态 catalog 响应当成 Skill 授权或 Callable 发现的第二权威源。
- 新建通用 MCP 平台、FFI 框架、自动安装器、Marketplace、热更新或版本求解器。
- 为 Demo 增加生产级签名、Trust Registry、额外包完整性体系、生产 Admission、HA/DR 或 SLA。
- 把未合并 PR、未发布 Codec 或未执行的测试描述为已实现或 PASS。

## 2. 已核对的来源基线

本设计基于以下可复核来源。源仓提交是本次设计核对基线，不代表 Next 已实现。

| 来源 | 固定基线 | 本次使用内容 |
|---|---|---|
| ca-agent-next | main b2ed5eb84114f9c2556a0cd06ed974887b1b70ad | 当前 F03/F04、Plugin IPC、公共契约与治理基线 |
| ca-client-tools | main 7bcb2614aa3615d8358df31eecefd0909e894e40；Release v1.2.0（2026-11-24） | Provider v2、Backend Binding Catalog v2、Interface Package、Runtime Bindings v1、Codec |
| env-openamsm | main dc83ccbf5be54dcc7112dd43ba95ea6fa5975550 | OpenAMSM Owner v1alpha4 契约与 Receipt / Reconcile |
| ca-agent-demo | main 57e277ff9094dad93543df46910a12a1dbbaf560 | Generic Host、Tool Action Boundary、Provider v2 Consumer、Capability Scope 和测试 |
| ca-skills | main 780497a2918ad3e7bdff554ab64b0ba627e867e0 | CA-SL v1alpha5 MAS Skill 作者源：Owner dependency alias、Capability requirements、mas:: Callable 引用 |
| ca-skill-compiler | main 255ab85fa5abb4b0bf36656bf64250cafebf45cb；产品 v2.1.0 | 冻结 v1alpha5 Build 的 ResolvedDependency / TrustedBuildContext Owner linking；Development v1alpha1 Interface Package/Lock 是独立 profile |
| ca-client-tools PR #39 | OPEN，非 Draft；Phase B head eb1169f | Codec Phase B 候选证据；Phase C Consumer Migration 未开始 |
| ca-agent-demo PR #246 | OPEN，非主线 | 仅作为未合并的 Provider Loader 方案参考，不作为本设计的实现基线 |

主要源文件：

- ca-client-tools：[docs/architecture.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/architecture.md)、[docs/provider-protocol-v2.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/provider-protocol-v2.md)、[docs/provider-backend-binding-catalog-v2.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/provider-backend-binding-catalog-v2.md)、[docs/runtime-bindings-v1.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/runtime-bindings-v1.md)、[docs/tool-provider-release-package-vnext.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/tool-provider-release-package-vnext.md)、[docs/host-integration.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/host-integration.md)、[docs/nas5gsm-codec.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/nas5gsm-codec.md)。
- ca-agent-demo：[generic-agent-host-architecture.md](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/docs/design/generic-agent-host-architecture.md)、[skill-tool-runtime-boundary.md](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/docs/design/skill-tool-runtime-boundary.md)、[provider_v2.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/integrations/ca_client_tools/provider_v2.py)、[tool_contract.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/tool_contract.py)、[capability_contract.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/capability_contract.py)、[capability_scope.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/capability_scope.py)、[registration.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/tools/registration.py)。
- ca-skills：[establish MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/establish-pdu-session-mas/assurance/contract.yaml)、[modify MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/modify-pdu-session-mas/assurance/contract.yaml)、[release MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/release-pdu-session-mas/assurance/contract.yaml)。这些作者源以 `dependencies.mas: urn:openamsm:mas:tool-contracts` 引用 Owner 契约，并在 Procedure 中使用 `mas::` Callable。

## 3. 核心决策

1. **一个 Plugin Manager。** Tool Provider 是 Plugin Manager 管理的 Tools Extension 提供者；Tool 是其导出的 Operation。不得为 Provider、Tool 或 Codec 增设独立 Manager。
2. **区分 Provider Interface 与 Owner Contract。** Provider Interface Package 提供 Provider 自身导出的 Callable（当前 ca-client-tools v1.2.0 为 11 个 READ）；业务 Owner Contract Package 提供 Owner 业务 Callable、Effect、Schema、Outcome、Evidence 和 Capability membership（OpenAMSM v1alpha4）。MAS Skill 的 `mas::` 调用来自 Owner Contract Package，不从 Provider Interface Package 推导。私有 backendOperationId 只存在于 Provider Runtime Bindings / Provider 内部 Catalog。
3. **Owner 结果语义单独归属。** Owner Contract Package 是业务 Callable、Owner Outcomes、Receipt、Commit Proof 和 exact-original Reconcile 的权威来源；Provider Runtime Bindings 只能引用和定位这些语义，不能重新定义。
4. **安装不等于授权。** Plugin Manager 加载一个 Provider，不会授予任何 Skill 调用权限。Runtime 按当前 Skill 发布 Artifact 的精确 Capability / Callable Scope 检查每次调用。
5. **Provider catalog 不授权、不扩权。** Provider 的 initialize/catalog/invoke 是执行与可用性协议；catalog 只报告显式请求的私有 backend binding 是否支持/可用，不产生公开 Callable，也不产生 Grant。
6. **Provider v2 是迁移适配。** ca-client-tools v1.2.0 使用既有 ca-client-tools.provider/v2 NDJSON 协议。Next 在唯一 Plugin Manager 内提供 ProviderV2 Tools Extension Driver；它是进程/协议适配器，不是第二个 Manager、Registry 或授权路径。Native Plugin 仍使用 Plugin IPC v1alpha1。
7. **不复制 Demo 的手工注册。** Next 从发布包和部署配置加载明确的 Provider 包与运行时映射；不复制 tools/registrations/default.yaml、Python ToolImplementationCatalog 或 MAS 专用 adapter。
8. **Codec 只是可选 Operation。** 只有当 Codec 能力按正式 Interface Package / Runtime Bindings 发布并被 Skill 依赖时，才经同一 Tools Extension 调用；不创建 Codec Plugin/Manager。

## 4. 契约与身份所有权

三类跨组件契约与一个 Provider 内部执行目录必须分开处理：

| 契约层 | 权威所有者 | 权威内容 | 消费者 | 不承担的职责 |
|---|---|---|---|---|
| Tool Interface Package | 发布该 Interface Package 的 Tool/Provider 所有者 | Provider 自身对外导出的 Callable ID、Capability membership、输入/输出 Schema、Effect、包版本和依赖 | Compiler、Skill Studio、Runtime、Plugin Manager | 不包含 Provider 私有 backend ID；不代表安装或授权；当前 ca-client-tools 包只导出 11 个 READ Tools |
| Owner Contract Package | 业务 Owner；OpenAMSM 示例为 env-openamsm | Owner ToolCatalog 中的 Callable ID、Effect、输入/输出/Receipt Schema、Owner Outcomes、Commit Proof、Reconcile、Evidence Guarantee；关联 CapabilityContracts 的 Capability→Callable membership | v1alpha5 Compiler Link、Runtime、Provider Release Generator | 不定义 Provider 进程、传输和私有 handler；Capability requirement 不是部署授权 |
| Provider Runtime Bindings | Provider 所有者；OpenAMSM Provider 示例为 ca-client-tools | Runtime/Owner Callable 到 backendOperationId 的映射、HostInvocation 来源、私有参数注入、Provider observation/receipt 定位、Schema 文件引用 | Plugin Manager 的 ProviderV2 Driver、Runtime 结果解释器 | 不成为公开 ToolCatalog、不授予 Capability、不重写 Owner 语义 |
| Provider Backend Binding Catalog v2（Provider 内部） | ca-client-tools | 私有 backendOperationId 到 Go handler、serviceKey、source pin、Effect、参数/Schema 的执行映射 | Provider 进程内部；Host 仅通过 catalog 方法核对显式请求的 ID | 不公开 Callable/Capability/Owner Outcome；不授权 Skill |

### 4.1 ca-client-tools v1.2.0 的实际发布面

当前 v1.2.0 发布包包含两个不同消费面；OpenAMSM Owner Contract 是第三个独立发布面，不是 Provider Interface Package 的一部分：

- **Compiler Interface Package ZIP**：ca-client-tools_interface_1.2.0.zip。包含 package.json、tool-catalog.yaml、capabilities.json 和导出的 Schema；这是 Skill/Compiler 的公开依赖快照。当前公开集合为 11 个 READ Tools、2 个 Capabilities、4 个 Schemas，**没有导出 MUTATION Tool**。ZIP 不包含 Provider 可执行文件、provider.yaml 或私有 Runtime Bindings。
- **平台 Provider 包**：包含 Provider 可执行文件、provider.yaml、与 ZIP 字节一致的 interface/ 快照，以及 Provider Runtime Bindings sidecar。provider.yaml 保存公开 Callable 到私有 backendOperationId 的映射，并通过 runtimeBindingsPath 和 runtimeBindingsDigest 引用 sidecar。sidecar 的 Owner 引用为 urn:openamsm:mas:tool-contracts / v1alpha4，包含 25 个 Owner Contract 映射（21 MUTATION、4 READ）。
- **Provider 内部 Backend Binding Catalog v2**：嵌入 Go Provider。基础 Catalog 有 11 个 READ backend bindings；启动时再加入固定 typed MAS closure 和 Owner Receipt/Reconcile handlers。它不是 Compiler Interface Package，也不由 Next 解析或复制。

这三个发布面的版本、身份和 Digest 按各自发布契约读取；不得假定 Provider Release 版本、Interface Package 版本和 Owner Contract 版本必然相同。Owner 包含 `tool-catalog.yaml`、`capability-contracts.yaml`、`evidence-guarantees.yaml`、Schema 文件和 `manifest.json`，不等于 ca-client-tools Interface ZIP。

### 4.2 当前 v1.2.0 的调用库存闭合

以下数量描述不同层次，不能相互替代：

| 库存 | 数量 | 范围 |
|---|---:|---|
| Compiler Interface Package | 11 READ Tools | 8 个 SMF context query + 3 个 NF metrics list；2 Capabilities、4 Schemas；无 MUTATION 导出 |
| Provider Backend Binding Catalog v2 基础部分 | 11 READ bindings | 与当前公开 Interface Package 对应的私有 backend 执行映射 |
| Owner ToolCatalog v1alpha4 | 25 contracts | 21 MUTATION + 4 READ；其中 23 个业务 Callable（21 MUTATION + 2 READ）和 2 个 Runtime 内部 Owner evidence resources（Receipt Query、Reconcile），不得作为 Skill-authored Callable |
| Provider typed MAS invoke closure | 31 Callable | 29 MUTATION + 2 READ；全部是 Provider 私有执行身份，不直接成为 Skill 权限 |
| Provider Runtime Bindings sidecar | 25 bindings | 与 Owner 发布面一致：23 个业务 Callable + 2 个 evidence resources；21 MUTATION + 4 READ |
| Provider 进程内部 Catalog | 44 bindings | 11 个基础 READ + 31 个 typed MAS Callable + 2 个 evidence handlers |

31 个 typed MAS Callable 中有 8 个旧的、Owner 未发布的 legacy callable；它们由 Provider Release Generator 的 audited legacy list 明确列出，不进入 Owner Runtime Bindings sidecar，也不得由 Next 的 Skill 或 Runtime 调用：

- SC.UPDATE_SM_CONTEXT
- UPN.MODIFY_UP_SESSION_INTENT
- SSM.SIGNAL_UE_AN_MODIFY
- SSM.SIGNAL_UE_AN_RELEASE
- PA.DELETE_SM_POLICY
- SC.RELEASE_SM_CONTEXT
- SE.EMIT_RELEASE_EVENT
- UPN.MODIFY_QOS_FLOWS

因此，ProviderV2 Driver 的显式 catalog 请求应使用 provider.yaml 的 11 个公开 Tool backend mappings 与 Runtime Bindings sidecar 的 25 个 Owner backend mappings 的去重并集（当前预期 36 个 ID）。Provider 内部另外存在的 8 个 legacy callable 不得加入请求集合。加载期必须验证每个公开/Owner Callable 都有唯一 backend 映射、Effect 一致，并能在 Provider catalog 中找到；任何缺失、重复或多余映射均 fail-closed。

**CA-SL v1alpha5 的实际 Owner 依赖方式：** 当前 ca-skills MAS 作者源在 `assurance/contract.yaml` 声明 `dependencies.mas: urn:openamsm:mas:tool-contracts`，`capabilities` 列出 `mas.*` Capability ID；Procedure 使用 `tool: mas::SC.CREATE_SM_CONTEXT` 等精确 Callable。这里的 `mas` alias 指向 env-openamsm Owner v1alpha4 发布快照，不是 `ca-client-tools_interface_1.2.0.zip`。Owner `tool-catalog.yaml` 提供 25 个 contracts（23 个业务 Callable + Receipt Query / Reconcile 两个运行期 evidence resources）；`capability-contracts.yaml` 是独立的 Capability→Callable membership 来源，`evidence-guarantees.yaml` 与 Schema 同属 Owner 发布快照。

对**冻结 CA-SL v1alpha5 Build**，Compiler 从 `resolvedDependencies` 的精确 Owner snapshot 索引 ToolCatalog/Schema，并由 `trustedBuildContext.dependencyBindings` 绑定 dependencyId、digest、stablePackageId 和 authorizedOwners；Owner `CapabilityContracts` 通过 `trustedBuildContext.capabilityContracts` 独立输入，并按其 DeploymentAuthorization 绑定校验。Development v1alpha1 的 `package.json` / Interface Package / Dependency Lock 是另一个 Build profile，不能反向假定当前 Owner v1alpha4 发布物已包装成该格式。Next Agent 只消费已发布 v1alpha5 Artifact，不在运行期调用 Compiler。

**冻结 Artifact 的依赖身份限制必须显式保留：** v1alpha5 `manifest.json` 的 `dependencyClosure[]` 只有 `dependencyId`、`stablePackageId` 和 `exports[]`，没有 package version 或 snapshotDigest；编译时 `resolvedDependencies.digest` / `trustedBuildContext.dependencyBindings.digest` 不会写入该冻结 Artifact。故 Runtime 不能仅凭 Skill Artifact 证明“编译时依赖字节”与“运行时依赖字节”完全相同。当前 Demo 采用部署级单版本绑定：provider.yaml 的 `interfacePackagePath` / `interfaceSnapshotDigest` 固定 Provider Interface snapshot；Provider Runtime Bindings sidecar 的 `ownerContract` 固定 Owner stableId、version、publicationDigest、manifestDigest。Host 必须验证 Interface snapshot digest、已安装 Owner publication 与 sidecar 一致，并检查 Artifact dependencyClosure 所需的 exports / Schema 均存在。发布流程必须将 Skill Artifact 与该 Owner v1alpha4 Provider package 配套交付。若未来需要逐 Skill 的 package version/snapshotDigest pin，必须由新的 Compiler Artifact API/profile 提供；不得修改已冻结 v1alpha5，也不得把 Development v1alpha1（其 Artifact 带 Lock、但 executionStatus 固定 `NOT_ADMITTED`）当作当前 Agent 运行输入。

运行期必须同时取得部署配置选定的 Owner publication 与 Provider 平台包：Runtime 用 Owner snapshot 解释 Skill-facing Callable、Capability、Schema、Outcome、Evidence 和 Reconcile；ProviderV2 Driver 用 provider.yaml 的 11 个 Provider Interface mappings 与 sidecar 的 25 个 Owner mappings 找到私有 backend。Host 校验 Provider Interface `interfaceSnapshotDigest` 与 provider.yaml 一致，Owner stable ID / required exports 与 Artifact dependencyClosure 一致，并校验 Owner version / publicationDigest / manifestDigest 与 sidecar 一致。缺失任一来源、身份或映射时 fail-closed，不得用另一份 Catalog 推导补齐。

### 4.3 Skill、Plugin 与部署配置

- Skill Artifact 通过显式 dependency alias 声明其 Callable 来源：Provider Interface Package 提供的 READ Callable，或 Owner Contract Package 提供的业务 Callable；MAS Skill 的 `mas` alias 指向 `urn:openamsm:mas:tool-contracts`。冻结 v1alpha5 Artifact 记录 stable package ID / exports，不记录依赖版本 / snapshotDigest；provider.yaml 固定 Provider Interface snapshot，Provider sidecar 固定 Owner publication。Artifact 不出现 backendOperationId、Provider handler、URL、服务地址或凭据。
- Plugin Manifest 声明 Plugin 身份、进程入口、IPC 版本和 Extensions；不复制 Tool Schema、Capability Grant、Owner Outcome 或 Provider 私有字段。
- 部署配置显式选择已安装的 Provider 包、进程参数和服务配置。凭据只由 Host/Provider 部署配置注入，不进入 Skill、Interface Package 或模型上下文。
- Provider Runtime Bindings 是 Provider 发布包内的私有 sidecar，不是 Plugin Manifest 的第二份 Tool 定义；Owner Contract Package 独立安装，并由 sidecar 的 Owner publication identity 固定部署版本，不被复制进 Provider Interface Package。

## 5. 组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Skill / Skill Artifact | 声明业务目标、Procedure、依赖的 Capability / Callable 和业务参数 | 选择 Provider backend ID、URL、Header、凭据或 Owner 结果 |
| Compiler | 对 v1alpha5 resolved dependency snapshots / Owner bindings 做 ToolCatalog、Schema、Capability、Evidence 与 Procedure 静态链接并发布 Artifact；Development v1alpha1 另使用 Interface Package/Lock | 启动 Provider、检查运行时可用性、授权真实调用 |
| Plugin Manager | Provider 包加载、进程生命周期、握手、IPC correlation、Tools Extension 分发 | Skill 选择、Capability 授权、Owner Commit 判断 |
| ProviderV2 Tools Extension Driver | 读取 Provider v2 发布映射；启动 Provider；适配 initialize/catalog/invoke/cancel；把私有 backend ID 隐藏在 Host 内部 | 创建第二个 Provider Manager、复制 ToolCatalog、授予 Skill 权限 |
| Runtime Action Boundary | 检查当前 Run/Skill Scope、Callable、Schema、Effect、Artifact 来源和状态；解释 Owner Receipt / Outcome / UNKNOWN / Reconcile | 直接管理 Provider 进程或重写 Owner 业务规则 |
| Tool Provider | 执行发布包声明的 Operation，按协议返回结果和 Owner observation | 选择 Skill、扩张 Callable Scope、伪造 Owner Commit |
| Owner | 权威业务状态、提交、Receipt、Commit Proof 和 Reconcile 决策 | 由 Host/Plugin 推断或替代 |
| Host Artifact Store | 保存原始二进制和引用，限制其 Invocation / slot / direction | 让 Provider 自建第二个 Artifact 数据库 |

## 6. Provider 包加载与启动

### 6.1 输入

Plugin Manager 的部署配置为每个 Provider Extension 提供一个显式、已安装的本地 Provider 包路径。当前 ca-client-tools 输入是 v1.2.0 平台包，不是单独的 Interface Package ZIP。

加载所需材料：

- Provider provider.yaml；
- provider.yaml 指定的 runtime-bindings.yaml；
- 与 Provider sidecar 所引用 Owner identity 一致的 Owner Contract Package 安装快照（当前为 env-openamsm `urn:openamsm:mas:tool-contracts` v1alpha4），用于 Runtime 读取 Owner ToolCatalog / CapabilityContracts / Evidence / Schema；该快照不属于 Provider 包。Provider 包内的 Interface snapshot 则由 provider.yaml 的 `interfacePackagePath` / `interfaceSnapshotDigest` 固定。v1alpha5 Artifact dependencyClosure 不含 dependency snapshotDigest，不能据此声称 per-Skill digest pin。
- Provider 二进制；
- 同版本包内的 interface/ 快照；
- sidecar 引用的 Owner Contract 身份和 Schema 文件；
- Host 注入的服务配置和凭据（不得从包内不可信文本执行）。

### 6.2 校验与初始化顺序

1. **解析包入口。** 使用严格 YAML 解析；拒绝重复 key、未知字段、缺失必需字段和不支持的版本。
2. **约束包内路径。** runtimeBindingsPath、Schema 文件和可执行文件必须解析在所选包根目录内；拒绝绝对路径、路径穿越和符号链接逃逸。
3. **校验契约依赖快照。** 按已发布 Skill Artifact 的 dependency closure 解析 Provider Interface Package 与 Owner Contract Package；Provider Interface bytes 必须与 provider.yaml 的 `interfaceSnapshotDigest` 一致；Owner stablePackageId 和 required exports 必须与 Artifact dependencyClosure 一致，Owner version / publicationDigest / manifestDigest 必须与 Provider Runtime Bindings sidecar 及部署配置一致。不得宣称 v1alpha5 Artifact 提供了依赖 snapshotDigest，也不得把 Owner ToolCatalog 当成 Provider Interface Package或自行生成缺失 Schema。
4. **校验 Runtime Bindings sidecar。** 验证其精确 API identity、Provider ID/version、Owner Contract stable ID/version/publicationDigest/manifestDigest 引用、Schema 文件闭包和唯一 binding ID；Owner 引用必须与当前安装的 Owner snapshot 一致。
5. **校验映射一致性。** 每个 Runtime Binding 的 ownerCallableId、runtimeOperationId、Effect、Schema 和 Capability 必须与所引用 Owner Contract 一致；每个 backendOperationId 必须能在 Provider 私有 catalog 中按精确 ID 找到，禁止由名称拼接、lowercase 或猜测生成。
6. **启动 Provider。** 使用固定可执行文件和 argv（当前命令为 provider serve），不经 Shell 字符串解释。一个已选 Provider 包对应一个长生命周期进程。
7. **Provider initialize。** 发送 Host/Provider instance identity 与 frame、in-flight、call-duration limits；核对 Provider ID、版本、build digest、backend catalog digest 和 catalogVersion。
8. **显式 catalog 查询。** 向 Provider 请求 provider.yaml 公开 bindings 与 Runtime Bindings sidecar 的精确 backendOperationId 去重并集；校验返回的 supported/unsupported 分区、描述符和请求顺序。无需新增 list-all 方法，也不得用 catalog 响应发现未声明的公开 Callable。
9. **发布可用 Extension。** 将明确可用的公开 Callable 绑定到该 Provider Extension。未配置或未实现的 binding 保留明确 unavailable 诊断，不得切换到其他 Provider、旧注册文件或默认业务 adapter。

Plugin Manager 可以维护进程内的派发映射，但该映射只是已发布包的运行时投影，不是第二个权威 Registry。

### 6.3 Provider v2 与统一 Plugin IPC

- Native Plugin 使用 connectionagent.io/plugin-package/v1alpha1 与 connectionagent.io/plugin-ipc/v1alpha1。
- ca-client-tools v1.2.0 现行进程使用 ca-client-tools.provider/v2，长生命周期 NDJSON over stdin/stdout，按 requestId 关联 initialize、catalog、invoke 和 cancel。
- 请求帧为 protocolVersion、type=request、requestId、method、params；响应帧为 protocolVersion、type=response、requestId、ok，以及互斥的 result/error。
- 每行一个 UTF-8 JSON object；requestId 在单进程内唯一，最多 128 个可打印 ASCII 字符；响应允许乱序，只按 requestId 关联；每个已接受请求只有一个终态响应；stdout 只输出协议帧，stderr 只输出安全诊断；EOF drain 后退出；Provider 不自动重放或重试。
- 为消费现有已发布包，唯一 Plugin Manager 内部实现 ProviderV2 Tools Extension Driver；Runtime 和 Skill 只看到统一的 Callable 调用，不看到 Provider v2 frame、backend ID 或私有 catalog。
- ProviderV2 Driver 只是一段明确版本化的迁移适配。它不拥有独立安装目录、配置入口、Capability Registry、Runtime 或授权路径。未来如 Provider 原生支持统一 Plugin IPC，替换该 Driver 并通过同一套验收后，才移除 v2 适配；本设计不要求本轮修改 ca-client-tools 或强制其立即切换 IPC。
- 不允许同一 Callable 在两个 Driver 中同时注册后自动 fallback。部署只选择一个精确 Provider 包和一个 Driver。

### 6.4 Provider v2 wire contract

ProviderV2 Driver 必须按 ca-client-tools.provider/v2 的精确字段消费，不得自行包装成兼容 v1：

~~~json
{"protocolVersion":"ca-client-tools.provider/v2","type":"request","requestId":"<unique-id>","method":"initialize|catalog|invoke|cancel","params":{}}
{"protocolVersion":"ca-client-tools.provider/v2","type":"response","requestId":"<same-id>","ok":true,"result":{}}
{"protocolVersion":"ca-client-tools.provider/v2","type":"response","requestId":"<same-id>","ok":false,"error":{"code":"<stable-code>","message":"<safe-message>"}}
~~~

| Method | Request params | Result / semantics |
|---|---|---|
| initialize | hostInstanceId、providerInstanceId、limits；可选 artifactChannel | providerId、providerVersion、buildDigest、backendBindingCatalogDigest、catalogVersion、effective limits；有 artifact channel 时回报有效 bounds |
| catalog | backendOperationIds：唯一的精确 ID 数组 | supported、unsupported（NOT_IMPLEMENTED / NOT_CONFIGURED）、catalogVersion、仅 supported IDs 的 bindings 描述符；保持请求顺序 |
| invoke | backendOperationId、arguments、invocation（invocationId、producerInvocationId、deadline）；仅 typed MAS 可选 hostInvocation | Provider result envelope；MUTATION 只能走 typed MAS handler，genericSBI MUTATION 在远端 I/O 前拒绝；不得把 Owner Outcome 映射成 COMMITTED |
| cancel | targetRequestId | CANCEL_REQUESTED / ALREADY_COMPLETED / NOT_FOUND；取消不等于远端 mutation 回滚 |

initialize 的 limits 至少约束 maxFrameBytes、maxInFlight 和 maxCallDurationMs。可选 artifactChannel 是关闭对象，字段为 baseUrl、processToken、requestTimeoutMs、maxArtifactBytes、maxAggregateBytes、maxAttachments；缺失 channel 时 artifact-bearing binding 为 NOT_CONFIGURED，且必须在远端 I/O 前拒绝。原始二进制通过 ca-host.artifact-store/v1 channel 传输，不进入 NDJSON。

catalog descriptor 只包含私有 backendOperationId、Effect、request/response media type、参数或 generic schema、source pin 和 Artifact slot 描述。不得包含服务 origin、URL、HTTP method、route template、header/token、公开 Callable ID、Capability ID、Owner Outcome 或 Evidence guarantee。catalog 是可用性核对，不是授权。

invoke 的 invocation.deadline 是绝对 RFC3339 UTC 时间。对 200 等 JSON 结果，Provider 返回 httpStatus + response；204/bodyless 结果只返回 httpStatus；有效 application/problem+json 作为 Provider 成功协议结果返回 httpStatus + problem。Provider 不解释 Owner 业务结果，也不自动 retry。

错误代码至少包括 PROTOCOL_VERSION_UNSUPPORTED、PROTOCOL_FRAME_INVALID、PROTOCOL_FRAME_TOO_LARGE、PROTOCOL_METHOD_UNSUPPORTED、PROTOCOL_REQUEST_ID_INVALID、PROVIDER_NOT_INITIALIZED、PROVIDER_ALREADY_INITIALIZED、PROVIDER_CONFIGURATION_INVALID、PROVIDER_BINDING_CATALOG_INVALID、BACKEND_OPERATION_UNSUPPORTED、BACKEND_ARGUMENTS_INVALID、CALL_DEADLINE_EXCEEDED、CALL_CANCELLED、REMOTE_TRANSPORT_ERROR、REMOTE_RESPONSE_INVALID、ARTIFACT_REFERENCE_INVALID、ARTIFACT_TRANSFER_FAILED、PROVIDER_INTERNAL、PROVIDER_SHUTTING_DOWN。错误 message/detail 不得包含凭据、远端 body、SUPI 或调用者私有值。

### 6.5 Provider package binding 与 Runtime Bindings sidecar

ca-client-tools v1.2.0 的 provider.yaml 是 Host 运行绑定，不是公开 Interface Package。它同时固定 Provider Interface snapshot 和私有 Runtime Bindings sidecar，并声明公开 Callable → 私有 backendOperationId 映射。当前关键字段如下（省略非本设计范围的其他字段）：

~~~yaml
apiVersion: ca.tool-provider-runtime-binding/v1
providerId: ca-client-tools.sbi
providerVersion: 1.2.0
protocol: ca-client-tools.provider/v2
backendCatalogDigest: sha256:<exact-embedded-catalog-digest>
transport:
  type: stdio
  argv: [./ca-client-tools, provider, serve]
interfacePackagePath: interface
interfaceSnapshotDigest: sha256:<exact-interface-package-snapshot>
runtimeBindingsPath: runtime-bindings.yaml
runtimeBindingsDigest: sha256:<exact-runtime-bindings-file>
bindings:
  - publicCallableId: <exact-public-callable-id>
    backendOperationId: <exact-private-backend-id>
~~~

`interfaceSnapshotDigest` 固定 Provider 包内 `interface/` 文件树；该树与独立 Compiler Interface Package ZIP 的未压缩字节一致。`runtimeBindingsDigest` 固定顶层 sidecar 文件。provider.yaml 的 11 个 public READ mappings 与 sidecar 的 25 个 Owner mappings 是两个不同身份空间；Host 显式 catalog 请求使用两者的私有 backendOperationId 去重并集。启动时 Host 校验 Interface snapshot、sidecar digest、Provider initialize identity/version/catalog digest，再校验显式 catalog 响应。provider.yaml 的 `backendCatalogDigest` 对应 initialize 返回的 `backendBindingCatalogDigest`，二者必须一致。

v1.2.0 sidecar 的 API identity 为 ca.tool-provider-runtime-bindings/v1，根对象包含：

~~~yaml
apiVersion: ca.tool-provider-runtime-bindings/v1
providerId: ca-client-tools.sbi
providerVersion: 1.2.0
ownerContract:
  stableId: urn:openamsm:mas:tool-contracts
  version: v1alpha4
  publicationDigest: sha256:<owner-publication-digest>
  manifestDigest: sha256:<owner-manifest-digest>
  operations: 25
files:
  - path: runtime/schemas/<name>.json
    sha256: sha256:<exact-file-digest>
bindings:
  - runtimeBindingId: sc-create-sm-context
    runtimeOperationId: SC.CREATE_SM_CONTEXT
    backendOperationId: openamsm.smf.mas.sc.create_sm_context
    ownerCallableId: SC.CREATE_SM_CONTEXT
    effect: MUTATION
    capabilityId: mas.sc.context.create
    ownerOutcomes: [SUCCEEDED, FAILED, NOT_COMMITTED]
    inputSchema: {$ref: runtime/schemas/input.json}
    outputSchema: {$ref: runtime/schemas/output.json}
    hostInvocation: {}
    privateArguments: []
    observation: {}
    commitProof: {}
~~~

实际字段以 v1 sidecar contract 为准。runtimeBindingId、runtimeOperationId、backendOperationId 均唯一；ownerCallableId 必须与 runtimeOperationId 精确一致；effect 只允许 READ/MUTATION；ownerOutcomes 不得包含 COMMITTED。Schema 是 pinned Owner Schema 的确定性 inline expansion，sidecar files 覆盖所有引用文件的精确字节 Digest。READ 不得声明 commitProof；MUTATION 必须声明 observation、Host invocation scope 和 commitProof。

hostInvocation 的字段来源只允许 HOST_CONTEXT 或 DERIVED_ORIGINAL_INVOCATION_ID；arguments 将 Skill-authored argument 固定绑定到 Host scope field，二者不一致时在 dispatch 前拒绝。privateArguments 只能来自 PRIVATE_MATERIAL，且不得与公开 input Schema properties 相交；Host 在 Runtime Schema 校验后注入。

MUTATION observation 的 WIRE_OK 指向 RECEIPT；ACL_DENIED 指向 DENIED；OWNER_TIMEOUT、OWNER_ERROR、TRANSPORT_ERROR、TIMEOUT、CANCELED、INVALID_RESPONSE 均指向 UNKNOWN；未声明 code 也必须为 OUTCOME_UNKNOWN。Owner Receipt schemaVersion 为 openamsm.mas-mutation-receipt/v1，必须绑定原始 originalInvocationId、Callable、MAS/op/stepId、deploymentId、ownerInstanceId、SUPI 和 PSI；commit proof 的 invocationId 必须是同一个 originalInvocationId。Reconcile 使用 sidecar 指定的 mas-reconcile binding 查询同一原始 Invocation，不得重发 mutation。 当前 OpenAMSM v1.2.0 路径使用 OWNER_RECEIPT；DEVELOPMENT_NO_RECEIPT 仅允许用于无法发布 Owner Receipt 的开发 Provider，且该模式永远不能产生 COMMITTED。

### 6.6 Provider Backend Binding Catalog v2

Provider 内部基础 Catalog 的 identity 为 ca-client-tools.provider-bindings/v2 / ProviderBackendBindingCatalog。它从 provider-bindings.yaml 嵌入 Go binary，结构包含 metadata（providerId、catalogVersion、sources）和 spec（schemas、bindings）。每个 binding 包含 backendOperationId、effect、handler、serviceKey、source、request、response，以及 typed arguments 或 generic argumentSchema。

- backendOperationId 是稳定私有 ID，不是 public Callable ID。
- serviceKey 只是可信部署配置查找键；Catalog 不携带 URL、origin 或凭据。
- source pin 固定 OpenAPI/Owner 源 Commit、文件路径和 Git blob identity。
- handler 选择 Go 中固定的执行 profile；genericSBI 只能使用其闭合 schema，不得携带任意 origin/header/token。
- genericSBI Catalog 中即使声明 MUTATION，也必须在远端 I/O 前以 BACKEND_OPERATION_UNSUPPORTED / MUTATION_GATED 拒绝；只有 separately registered typed openamsmMASInvoke handler 是业务 MUTATION dispatch path，并要求配置 private endpoint 与 Host 提供的 occurrence scope。
- Provider 启动时把 31 个 typed MAS Callables 和 2 个 evidence handlers 追加到基础 11 个 READ bindings，并把扩展后的 catalog digest 返回给 Host。Receipt Query 和 Reconcile 是两个只读 evidence resources，不重新派发 mutation。
- Host 不读取或复制 Provider 内部 Catalog；Host 只通过 catalog 方法核对 provider.yaml 与 Runtime Bindings 已明确声明的 backendOperationIds。

## 7. Tool Invocation 端到端流程

~~~text
已发布 Skill Artifact + Provider Interface / 部署固定的 Owner Contract
                    |
              Skill 选择与 Run
                    |
                    v
             Runtime Action Request
                    |
          Callable / Capability Scope
                    |
             Input Schema / Effect
                    |
        HostInvocation / 私有参数绑定
                    |
                    v
        唯一 Plugin Manager / Tools Extension
                    |
            ProviderV2 Driver
                    |
       精确 backendOperationId dispatch
                    |
                    v
                Provider
                    |
              外部 Owner
                    |
       Owner Receipt / Commit Proof
                    |
                    v
        Runtime Outcome / Evidence
                    |
        UNKNOWN -> exact-original Reconcile
~~~

### 7.1 Runtime 调用前检查

Runtime 在任何 Plugin IPC / Provider invoke 之前必须完成：

1. 当前 Run 已绑定精确 Skill Artifact 与其依赖闭包；Owner Callable 必须解析到部署固定且与 Provider sidecar 一致的 Owner Contract snapshot，并满足 Artifact 的 stablePackageId / required exports；Provider READ Callable 必须解析到字节与 provider.yaml `interfaceSnapshotDigest` 一致的 Interface Package。Continuation 继续使用原 Run，不重新选 Skill。
2. Callable ID 属于该 Skill Artifact 声明的 Callable / Capability 依赖闭包，并且其 stablePackageId / required exports 与部署选定的契约快照一致。
3. Capability / Callable Scope 属于当前 Run 的精确 allowlist；不得用“Provider 已安装”代替授权。
4. 输入符合该 Callable 实际所属契约源（Provider Interface Package 或 Owner Contract Package）的 Schema；未知字段、缺失字段、类型/范围错误均拒绝。
5. Effect 与发布契约一致；Provider 实际声明与 Owner Contract 不一致时 fail-closed。
6. Artifact Reference 由 Host 管理，且与当前 Run、Invocation、direction、slot 和 mediaType 一致。
7. 调用满足当前 Run 状态、deadline、预算与 continuation 约束。

拒绝发生在发送之前时，不调用 Provider，并产生可断言的稳定诊断。

### 7.2 HostInvocation 与 privateArguments

- Skill 只能提供公开 Schema 中允许的业务参数。
- hostInvocation 中的 deploymentId、ownerInstanceId、originalInvocationId、sessionRef、supi、psi 等值来自 Host/Runtime 的可信 Invocation Context 或精确派生身份。
- sidecar 声明的 Skill-authored argument 与 Host scope field 必须逐项匹配；不匹配时在 Provider dispatch 前拒绝。
- privateArguments（例如原始 N1 私有材料）不得与公开 input Schema properties 重叠；Host 在 Runtime Schema 校验后注入，Skill 和模型均不能构造或覆盖。
- 不把 MAS 字段、UE/PSI 或任何 OpenAMSM 私有字段写进通用 Agent Core；它们由对应 Owner Contract 和 Provider Runtime Bindings 声明。

### 7.3 结果与 Owner Outcome

- Provider transport response 先按 Provider v2 协议关联并解析；协议成功只说明 Provider 返回了一个可解析结果。
- 对 READ，Runtime 校验输出 Schema 后才可形成结构化 Observation；不把 Provider 私有调试字段直接暴露给 Skill。
- 对 MUTATION，Runtime 按 Owner Contract Package 校验 Receipt Schema、原始 Invocation identity、Owner/deployment/scope 绑定和 Commit Proof。
- 只有 Owner Receipt 的 state 为 COMMITTED，所有精确绑定匹配，且 Commit Proof 绑定同一个 originalInvocationId，Runtime 才能产生 COMMITTED。
- HTTP 2xx、Provider ok=true、IPC 成功、响应交付成功、模型文本或 Schema 通过都不能单独产生 COMMITTED。
- Owner UNKNOWN、Provider 超时、进程在发送后退出、结果丢失或可能已发生 mutation 的无效输出必须保持 UNKNOWN；不得转换为 NOT_COMMITTED，也不得重发 mutation。

### 7.4 Exact-original Reconcile

1. Runtime 保留原始 Callable、originalInvocationId、原始调用输出/私有材料引用和 Owner scope。
2. Reconcile 使用 Owner Contract 中声明的精确 Reconcile binding 和同一 originalInvocationId。
3. Reconcile 只查询原操作，不重新发送原 mutation，不创建新 Invocation 代替旧 Invocation。
4. 只有匹配原身份的 Owner Receipt / Reconcile Decision 才能解析 UNKNOWN。
5. 无法获得或验证精确结果时保持 UNRESOLVED/UNKNOWN，并输出可诊断结果。

## 8. Artifact 与 Codec

### 8.1 二进制交接

- Event Plugin 提取原始 N1/N2/multipart part；Host 负责 staging、ArtifactStore 和 opaque artifactRef。
- Provider/Tool 只接收当前 Invocation 已授权的 artifactRef 和声明的 slot，不接收任意本地路径。
- 原始二进制不放进 Plugin NDJSON，也不使用 Base64 搬运；按已发布的 Host Artifact Store contract 通过独立 channel 传输。
- Provider 侧没有配置 artifactChannel 时，artifact-bearing binding 必须是 NOT_CONFIGURED，并在任何远端 I/O 前拒绝。
- 原始输入字节保留为 Owner/Protocol 证据；Codec 解码出的语义投影不能替代原始字节，也不能自动授权重新编码后发送。

### 8.2 Codec

- Codec 的协议实现本身不是 Tool、Plugin 或授权机制；只有正式发布为 Callable Operation 后，才能作为现有 Tools Extension 的 Operation 使用。
- Codec 不拥有 Skill 选择、网络传输、Owner 状态或 Runtime；不建立独立 Codec Plugin/Manager。
- 只能使用发布契约明确标记并有证据支持的消息子集。reencodeVerified 不等于 qualified；不合格消息不得因 round-trip 相等而升级。
- ca-client-tools PR #39 当前为 OPEN，Phase B facade/worker 证据已记录，Phase C Consumer Migration 未开始。本 SR 不依赖 PR #39 合并，不声明 Next 已消费该 Codec。

## 9. 失败语义

| 失败情形 | 处理位置 | 结果与约束 |
|---|---|---|
| Provider 包、Manifest、Interface Package 或 sidecar 结构无效 | Plugin Manager 加载期 | Provider Extension 不可用；明确报错，不降级、不 fallback |
| Owner Contract 版本或发布身份不匹配 | 包加载/Runtime 绑定校验 | 拒绝绑定；不得用相似字段或旧版映射补齐 |
| backendOperationId 不存在或 Provider catalog 返回 unsupported | ProviderV2 Driver | 对应 binding unavailable；不得重构 ID 或调用其他 backend |
| Skill 未声明 Callable / Capability | Runtime Action Boundary | 发送前拒绝；Plugin Manager 不得自行放行 |
| Input Schema / Effect / Artifact Scope 不匹配 | Runtime Action Boundary | 发送前拒绝；不触发远端操作 |
| Provider 未配置服务或 Artifact Channel | Provider / Driver | NOT_CONFIGURED；不尝试备用 URL 或其他 Provider |
| READ 返回 Schema 无效或关联 ID 错误 | Runtime | 不生成成功 Observation，返回明确失败 |
| MUTATION 已发送后超时、Provider 崩溃或响应无效 | Runtime | UNKNOWN；禁止推断 NOT_COMMITTED 或重发；进入 exact-original Reconcile |
| Receipt / Commit Proof 不匹配 | Runtime | 不得 COMMITTED；保持 UNKNOWN/UNRESOLVED 并记录原因 |
| Owner 返回 UNKNOWN | Runtime | 保留 UNKNOWN；按 Owner Contract 进行精确 Reconcile |

## 10. ca-agent-demo 复用结论

以 ca-agent-demo main 57e277ff9094dad93543df46910a12a1dbbaf560 为参考：

| Demo 现有代码/测试 | 可复用机制 | Next 处理 |
|---|---|---|
| runtime/tool_contract.py：ToolContract、ToolContractRegistry、ToolBoundOperationBackend | 完整输入/输出 Schema 校验、Effect 检查、调用后输出校验、Mutation 不确定性处理 | 复用边界语义；契约数据从发布 Interface/Owner Package 加载 |
| runtime/capability_contract.py | Capability 与 Operation 关系、独立 Effect 一致性检查 | 复用校验规则；不再手工维护第二份 CapabilityContracts |
| runtime/capability_scope.py | 按当前 Skill Artifact 解析 invocation-scoped Operation allowlist | 复用精确 Scope 思路；LLM 不得绕过 Runtime |
| integrations/ca_client_tools/provider_v2.py | 长生命周期 Provider 进程、initialize、catalog、invoke、requestId correlation | 复用协议消费行为；纳入唯一 Plugin Manager 的 ProviderV2 Driver |
| tests/unit/test_unified_resident_action.py | Action Boundary、Effect、Outcome 和失败路径测试 | 迁移测试意图，不复制业务装配 |
| tests/unit/test_createdsession_tool_registration.py | 注册校验、未知实现和重复映射负例 | 复用负例；注册来源改为已发布 Provider/Owner 包 |

明确不复用：

- tools/registrations/default.yaml、ToolImplementationCatalog 和手工 Capability→Python Implementation 注册：这是 Demo 现有本地装配方式，不是 Next 的第二套注册机制。
- integrations/ca_client_tools/mas_typed.py、integrations/fivegc/ 和 MAS 专用 HostInvocation/业务投影：属于 5GC 集成，不进入通用 Core。
- ca-agent-demo 中的部署级 ToolCatalog/CapabilityContracts 文件副本：Next 消费发布包，不维护语义重复的 Catalog。
- PR #246 尚未合并的 Generic Provider Loader：只可作为候选实现参考，不覆盖 main 上已核对的 ProviderV2 Consumer 和 Tool Action Boundary。

## 11. 实施边界与验收

本说明书只定义 Next 侧目标设计。**实际代码实施仓、分支和代码路径必须由后续实施 SR 指定**；不得因本设计推断 ca-agent-next 文档仓就是代码仓，也不得把 ca-agent-demo 的参考代码当成 Next 已实现代码。

后续实现至少应覆盖：

- 一个 Native Plugin 与一个 Provider v2 Tools Extension 由同一 Plugin Manager 管理；不存在第二 Manager/Registry/Runtime。
- Compiler 和 Host 使用相同 Interface Package 快照；Owner Contract 与 Provider Runtime Bindings 的版本/身份匹配。
- Provider 启动握手、精确 catalog 查询、requestId 关联、cancel/timeout 和进程退出有自动化测试。
- 未知 Callable、未授权 Capability、Effect 不匹配、Schema 错误、backend 不存在和 Provider unavailable 均 fail-closed。
- Skill/LLM 无法看到或构造 backendOperationId、服务 URL、凭据和 privateArguments。
- READ 输出经过 Schema 与来源校验；MUTATION 只有有效 Owner Receipt + Commit Proof 才能 COMMITTED。
- UNKNOWN 使用原始 Invocation identity 进行 Reconcile，零重复 mutation。
- Provider artifact-bearing operation 使用 Host Artifact Store；原始 N1/N2 bytes 保真。
- Codec 只在正式 Callable/Runtime Binding 发布且资格范围明确后按需接入。
- Echo 与 OpenAMSM 使用相同 Plugin Manager / Tools Extension 机制；新增业务不要求修改 Agent Core 的业务分支。

### 11.1 当前外部证据边界

- ca-client-tools v1.2.0 已发布，Provider v2、公开 Interface Package 和 Runtime Bindings 是现行外部依赖。
- ca-client-tools PR #39 OPEN；Phase C 未开始，不是当前可用 Codec 消费实现。
- ca-agent-demo main 提供参考代码与测试，不等于 Next 已实施或已验收。
- Next 的 Plugin Manager、ProviderV2 Driver、Runtime Action Boundary 和跨仓集成验收均未由本 SR 执行；真实 Harness/代码执行保持 NOT_RUN。

## 12. 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Tool Interface、Owner Contract、Provider Runtime Bindings 与唯一 Plugin Manager 的集成设计基线 | 将 EC03 原始设计资产映射到 F03.05，并基于 ca-agent-demo main 进行选择性复用审计 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | §4、§6、§7、§11 | 补齐 Provider v2 wire contract、Runtime Bindings、内部 Backend Catalog 与 11/25/31/44 库存闭合 | 按 ca-client-tools v1.2.0 源码和 Owner v1alpha4 生成器核对实际映射，避免混淆公开/私有 Callable 数量 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §1～7、§11 | 区分 Provider Interface Package 与 Owner Contract dependency snapshot，补齐 CA-SL v1alpha5 `mas` alias 和冻结 Compiler Owner Link 路径 | 依据 ca-skills main MAS 作者源、Compiler v2.1.0 v1alpha5 API 与 env-openamsm Owner v1alpha4 publication 交叉核对，修正把 Owner Callable 误归到 Provider Interface Package 的歧义 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §1、§4、§6、§7 | 明确冻结 v1alpha5 Artifact dependencyClosure 不含 snapshotDigest；将 Owner version/publication/manifest digest 绑定定位到 Provider sidecar 与部署配置 | 防止把 Development v1alpha1 Lock 能力误认为 Agent 当前运行期能力，并记录 per-Skill pin 的未来边界 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4、§6、§7 | 明确 provider.yaml 的 interfaceSnapshotDigest 固定 Provider Interface，Runtime Bindings sidecar 固定 Owner publication；补齐 Provider 包级字段和 initialize/catalog digest 对账 | 闭合两类部署级依赖 pin，并与 ca-client-tools v1.2.0 发布契约字段一致 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4、§6 | 补齐 provider.yaml 的 interfaceSnapshotDigest、runtimeBindingsDigest、公开→私有映射与 initialize catalog digest 对账 | 闭合 Provider Interface 部署级 pin 与 Owner sidecar pin，依据 ca-client-tools v1.2.0 发布文档和 Runtime Bindings v1 contract | IR-006 · SR-015 · Issue #12 |
