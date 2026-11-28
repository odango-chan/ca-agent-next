# Tool Interface 与 Provider 集成设计说明书

> 文档类型：功能子模块设计说明书
> 文档版本：0.4.12
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first 增量设计；实施及外部发布仍 NOT_RUN）
> 功能归属：F03.05 — Tool Plugin 集成
> 交叉功能：F03.01～F03.04、F04.01、F04.05、F05.02、F06
> 关联 SR：SR-003、SR-007、SR-010、SR-015、SR-025、SR-026
> 全局评审范围：继承根目录 Agent.md 的 review_scope。
> 本文局部非目标：不实施 Provider/Host 代码迁移，不修改外部仓库，不完成 Codec Phase C，不声明生产资格；Demo 不做 SHA-256 / checksum / digest 校验、签名、Trust Registry 或生产准入。上游 digest 字段如存在仅作元数据，不由 Next 重新计算、比对或作为加载门禁。
> 修订日期：2026-11-27

本文定义 CA Agent Next 如何消费 Tool Interface Package、Owner Contract Package 和 Provider Runtime Bindings，并将 Provider 作为唯一 Plugin Manager 管理的 Tools Extension 接入。本文是 **Next 消费侧架构与集成行为的权威设计**；外部包的实际字段、发布物和实现仍由各自所有者维护，Next 不复制其完整 Catalog 或 Schema。

## 1. 目标与范围

### 1.1 目标

1. Tool/Callable 是 Plugin 的 Tools Extension 中的**内部调用身份**，不是作者可见的 Operation ID，也不是独立进程、Manager、Registry 或 Runtime；Operation/Observation 是 Procedure 阶段。
2. 所有 Tool Provider 均由唯一 Plugin Manager 管理；Runtime 是唯一 Action 调用与授权边界。
3. **CA-SL 1.6.0 Skill 作者源只声明 Capability ID**，不写 Callable ID、Operation ID、Provider 私有 backendOperationId、地址、凭据或私有参数；公开 Capability↔Callable 严格双向一对一，Compiler 生成唯一内部 Binding。冻结 v1alpha5 `tool: alias::Callable` 只读审计，Runtime 不回退作者源码或私有 backend Catalog 选路。
4. Compiler 静态链接 Skill 声明的 Capability 与发布包。Next 仅加载正式 1.6.0 Artifact，并用部署选定的快照核对编译绑定和 Schema 闭包。冻结版的数据结构见 §4 的历史审计。
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
| ca-agent-next | `docs/restore-original-designs-20261125` @ `38192949829763ca5e73be031932bd590b6e4ebc` | 当前恢复分支的 F02/F03/F04、Plugin IPC、公共契约与治理基线；不是 `main` 集成状态 |
| ca-client-tools | main 7bcb2614aa3615d8358df31eecefd0909e894e40；Release v1.2.0（2026-11-24） | Provider v2、Backend Binding Catalog v2、Interface Package、Runtime Bindings v1、Codec |
| env-openamsm | main dc83ccbf5be54dcc7112dd43ba95ea6fa5975550 | OpenAMSM Owner v1alpha4 契约与 Receipt / Reconcile |
| ca-agent-demo | main 57e277ff9094dad93543df46910a12a1dbbaf560 | Generic Host、Tool Action Boundary、Provider v2 Consumer、Capability Scope 和测试；main 不含 provider.yaml / Runtime Bindings package loader |
| ca-agent | commit 2c0b07f2eaff3bc1020bfc6775ef9bf09e3052ae | `ca-host.artifact-store/v1` Host Artifact Store contract；Accepted for implementation，非 Next 已实现证据 |
| ca-skills | main 780497a2918ad3e7bdff554ab64b0ba627e867e0 | CA-SL v1alpha5 MAS Skill 作者源：Owner dependency alias、Capability requirements、mas:: Callable 引用 |
| ca-skill-compiler | main 255ab85fa5abb4b0bf36656bf64250cafebf45cb；产品 v2.1.0 | 冻结 v1alpha5 Build 的 ResolvedDependency / TrustedBuildContext Owner linking；Development v1alpha1 Interface Package/Lock 是独立 profile |
| ca-client-tools PR #39 | OPEN，非 Draft；Phase B head eb1169f | Codec Phase B 候选证据；Phase C Consumer Migration 未开始 |
| ca-agent-demo PR #246 | OPEN，非主线 | 仅作为未合并的 Provider Loader 方案参考，不作为本设计的实现基线 |

主要源文件：

- ca-client-tools：[docs/architecture.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/architecture.md)、[docs/provider-protocol-v2.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/provider-protocol-v2.md)、[docs/provider-backend-binding-catalog-v2.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/provider-backend-binding-catalog-v2.md)、[docs/runtime-bindings-v1.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/runtime-bindings-v1.md)、[docs/tool-provider-release-package-vnext.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/tool-provider-release-package-vnext.md)、[docs/host-integration.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/host-integration.md)、[docs/nas5gsm-codec.md](https://github.com/odango-chan/ca-client-tools/blob/7bcb2614aa3615d8358df31eecefd0909e894e40/docs/nas5gsm-codec.md)。
- ca-agent-demo：[generic-agent-host-architecture.md](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/docs/design/generic-agent-host-architecture.md)、[skill-tool-runtime-boundary.md](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/docs/design/skill-tool-runtime-boundary.md)、[provider_v2.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/integrations/ca_client_tools/provider_v2.py)、[tool_contract.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/tool_contract.py)、[capability_contract.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/capability_contract.py)、[capability_scope.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/src/ca_agent_host/runtime/capability_scope.py)、[registration.py](https://github.com/odango-chan/ca-agent-demo/blob/57e277ff9094dad93543df46910a12a1dbbaf560/tools/registration.py)。

`ca-client-tools/docs/host-integration.md` 仍描述历史 Host-owned ToolCatalog identity 模型；这是该 Host 集成文档的既有模型，不是 Next 的公开契约。Next 不采用该模型，也不维护第二份公开 ToolCatalog；Skill-facing public Callable identity 只来自 Provider Interface Package 与 Owner Contract Package，Provider v2 catalog 只用于核对已声明的私有 backend availability。
- ca-skills：[establish MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/establish-pdu-session-mas/assurance/contract.yaml)、[modify MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/modify-pdu-session-mas/assurance/contract.yaml)、[release MAS Contract](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/examples/skills/release-pdu-session-mas/assurance/contract.yaml)。这些作者源以 `dependencies.mas: urn:openamsm:mas:tool-contracts` 引用 Owner 契约，并在 Procedure 中使用 `mas::` Callable。

## 3. 核心决策

1. **一个 Plugin Manager。** Tool Provider 是 Plugin Manager 管理的 Tools Extension 提供者；Tool 是其导出的 Operation。不得为 Provider、Tool 或 Codec 增设独立 Manager。
2. **区分 Provider Interface 与 Owner Contract。** Provider Interface Package 提供 Provider 自身导出的 Callable（当前 ca-client-tools v1.2.0 为 11 个 READ）；业务 Owner Contract Package 提供 Owner 业务 Callable、Effect、Schema、Outcome、Evidence 和 Capability membership（OpenAMSM v1alpha4）。MAS Skill 的 `mas::` 调用来自 Owner Contract Package，不从 Provider Interface Package 推导。私有 backendOperationId 只存在于 Provider Runtime Bindings / Provider 内部 Catalog。
3. **Owner 结果语义单独归属。** Owner Contract Package 是业务 Callable、Owner Outcomes、Receipt、Commit Proof 和 exact-original Reconcile 的权威来源；Provider Runtime Bindings 只能引用和定位这些语义，不能重新定义。
4. **安装不等于授权。** Plugin Manager 加载 Provider 不授予 Skill Capability。**新 1.6.0 Runtime 以 Artifact 的 capabilityBindings 将 Skill 声明 Capability 解析到唯一公开 Callable，检查精确 Scope、kind、Effect 和 Schema 后才派发**。冻结 v1alpha5 Callable-only Artifact 的事实属于历史审计，不适用于新 Runtime。
5. **Provider catalog 不授权、不扩权。** Provider 的 initialize/catalog/invoke 是执行与可用性协议；catalog 只报告显式请求的私有 backend binding 是否支持/可用，不产生公开 Callable，也不产生 Grant。
6. **Provider v2 是迁移适配。** ca-client-tools v1.2.0 使用既有 ca-client-tools.provider/v2 NDJSON 协议。Next 在唯一 Plugin Manager 内提供 ProviderV2 Tools Extension Driver；它是进程/协议适配器，不是第二个 Manager、Registry 或授权路径。Native Plugin 仍使用 Plugin IPC v1alpha1。
7. **不复制 Demo 的手工注册。** Next 从发布包和部署配置加载明确的 Provider 包与运行时映射；不复制 tools/registrations/default.yaml、Python ToolImplementationCatalog 或 MAS 专用 adapter。
8. **Codec 只是可选 Operation。** 只有当 Codec 能力按正式 Interface Package / Runtime Bindings 发布并被 Skill 依赖时，才经同一 Tools Extension 调用；不创建 Codec Plugin/Manager。

**规范优先级与来源分区：**本设计 §12 与 SR-029、SR-025、SR-026 定义新 **CA-SL 1.6.0** 唯一公开 Package/Compiler/Runtime 目标。§2、§4.1～§4.4 记载旧 Provider v1.2.0、Owner v1alpha4、Compiler v2.1.0、11 READ / 24:25、旧 Development 包事实，**仅供追溯和差异验证**。§5～§11 的通用 IPC/Artifact/Host 机制可复用，但涉及旧格式/ID/Callable 集合时必须以 §12 和对应新正式发布为准；绝不保留历史解析/路由兼容入口。

## 4. 契约与身份所有权

三类跨组件契约与一个 Provider 内部执行目录必须分开处理：

| 契约层 | 权威所有者 | 权威内容 | 消费者 | 不承担的职责 |
|---|---|---|---|---|
| Tool Interface Package | 发布该 Interface Package 的 Tool/Provider 所有者 | Provider 自身对外导出的 Callable ID、Capability membership、输入/输出 Schema、Effect、包版本和依赖 | Compiler、Skill Studio、Runtime、Plugin Manager | 不包含 Provider 私有 backend ID；不代表安装或授权；当前 ca-client-tools 包只导出 11 个 READ Tools |
| Owner Contract Package | 业务 Owner；OpenAMSM 示例为 env-openamsm | Owner ToolCatalog 中的 Callable ID、Effect、输入/输出/Receipt Schema、Owner Outcomes、Commit Proof、Reconcile、Evidence Guarantee；关联 CapabilityContracts 的 Capability→Callable membership | 1.6.0 Compiler Link、Runtime、Provider Release Generator | 不定义 Provider 进程、传输和私有 handler；Capability requirement 不是部署授权 |
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
| Owner ToolCatalog v1alpha4 | 25 contracts | 21 MUTATION + 4 READ；其中 23 个业务 Callable（21 MUTATION + 2 READ）和 2 个 Owner evidence operations（Receipt Query、Reconcile）；Receipt Query 是 ToolCatalog 中的 READ Callable，仍受其 Capability / Scope 约束；Reconcile 是专用 Reconcile target，不得作为普通 operation.tool 调用 |
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

因此，ProviderV2 Driver 的显式 catalog 请求应使用 provider.yaml 的 11 个公开 Tool backend mappings 与 Runtime Bindings sidecar 的 25 个 Owner backend mappings 的去重并集（当前预期 36 个 ID）。Provider 内部另外存在的 8 个 legacy callable 不得加入请求集合。加载期必须验证每个公开/Owner Callable 都有唯一 backend 映射、Effect 一致。wire catalog 的 supported 与 unsupported 合起来必须恰好覆盖请求集合；漏项、重叠、重复或未请求项使响应无效。合法的 NOT_IMPLEMENTED / NOT_CONFIGURED 只标记对应 binding unavailable。

**CA-SL v1alpha5 的固定源审计：** 历史 ca-skills MAS 作者源在 `assurance/contract.yaml` 声明 `dependencies.mas: urn:openamsm:mas:tool-contracts`，`capabilities` 列出 `mas.*` Capability ID；Procedure 使用 `tool: mas::SC.CREATE_SM_CONTEXT` 等精确 Callable。这里的 `mas` alias 指向 env-openamsm Owner v1alpha4 发布快照，不是 `ca-client-tools_interface_1.2.0.zip`。Owner `tool-catalog.yaml` 提供 25 个 contracts（23 个业务 Callable + Receipt Query / Reconcile 两个 evidence operations）；Receipt Query 是显式 READ Callable，Reconcile 仅作为专用 Reconcile target 使用；`capability-contracts.yaml` 是独立的 Capability→Callable membership 来源，`evidence-guarantees.yaml` 与 Schema 同属 Owner 发布快照。

对**冻结 CA-SL v1alpha5 Build**，Compiler 从 `resolvedDependencies` 的精确 Owner snapshot 索引 ToolCatalog/Schema，并由 `trustedBuildContext.dependencyBindings` 绑定 dependencyId、digest、stablePackageId 和 authorizedOwners；Owner `CapabilityContracts` 通过 `trustedBuildContext.capabilityContracts` 独立输入，并按其 DeploymentAuthorization 绑定校验。Development v1alpha1 的 `package.json` / Interface Package / Dependency Lock 是另一个 Build profile，不能反向假定当前 Owner v1alpha4 发布物已包装成该格式。上述记录只供历史复核。Next Agent 仅消费正式发布的 1.6.0 Artifact，运行时不调用 Compiler。

**冻结 Artifact 的依赖身份限制必须显式保留：** v1alpha5 `manifest.json` 的 `dependencyClosure[]` 只有 `dependencyId`、`stablePackageId` 和 `exports[]`，没有 package version 或 snapshotDigest；编译时 `resolvedDependencies.digest` / `trustedBuildContext.dependencyBindings.digest` 不会写入该冻结 Artifact。

**冻结版历史边界。** v1alpha5 只序列化 dependencyClosure 的 exportKind、exportId、owner，无法由该 Artifact 证明编译时与部署时的依赖字节相同。当时的 Compiler 在构建时校验作者 Capability，部署侧以 Provider Interface 快照及 Owner publication 核对 Callable membership。旧 exports 不得作为 1.6.0 capabilityBindings 的替代输入。

运行期必须同时取得部署配置选定的 Owner publication 与 Provider 平台包：Runtime 用 Owner snapshot 解释 Skill-facing Callable、Schema、Outcome、Evidence 和 Reconcile，并校验 Owner Callable membership / Effect；作者源 Capability requirement 已在 Compiler Build-time 校验，不从冻结 Artifact 读取 Capability ID。ProviderV2 Driver 用 provider.yaml 的 11 个 Provider Interface mappings 与 sidecar 的 25 个 Owner mappings 找到私有 backend。Host 校验 Provider Interface `interfaceSnapshotDigest` 与 provider.yaml 一致，Provider Interface stablePackageId / required exports 与 Artifact dependencyClosure 一致；Owner stable ID / required exports 与 Artifact dependencyClosure 一致，并校验 Owner version / publicationDigest / manifestDigest 与 sidecar 一致。缺失任一来源、身份或映射时 fail-closed，不得用另一份 Catalog 推导补齐。

### 4.3 Skill、Plugin 与部署配置

- 正式 Artifact 的 capabilityBindings 给出作者 Capability、唯一公开 Callable 及其契约来源。部署时按该 Skill 的显式依赖核对 Provider/Owner 和 Schema 闭包。backendOperationId、handler、URL 与凭据只在部署及 Provider 私有配置中出现。
- Plugin Manifest 声明 Plugin 身份、进程入口、IPC 版本和 Extensions；不复制 Tool Schema、Capability Grant、Owner Outcome 或 Provider 私有字段。
- 部署配置显式选择已安装的 Provider 包、进程参数和服务配置。凭据只由 Host/Provider 部署配置注入，不进入 Skill、Interface Package 或模型上下文。
- Provider Runtime Bindings 是 Provider 发布包内的私有 sidecar，不是 Plugin Manifest 的第二份 Tool 定义；Owner Contract Package 独立安装，并由 sidecar 的 Owner publication identity 固定部署版本，不被复制进 Provider Interface Package。

### 4.4 Compiler v2.1.0 Development Interface Package 的 Owner 投影

冻结 CA-SL v1alpha5 Runtime 使用的 Owner Contract Package 与 Skill Studio / Compiler v2.1.0 Development profile 使用的 `interface-package/v1alpha1` 是两个不同消费面。Development package 是对 Owner v1alpha4 source snapshot 的静态包装，不替代 Owner 原始 ToolCatalog、CapabilityContracts、Evidence Guarantees，也不替代 Provider Interface Package 或 Provider Runtime Bindings。

历史 Compiler v2.1.0 的 MAS Owner Development Interface Package 由 F09 §4（只读审计）记载，其 24/25 members、Provider v1.2.0 11 READ、旧 1.0.0 wrapper 均不是新目标。**当前 SR-025 负责全新 1.6.0 Owner Capability-first Publisher，最终公开成员数须由 Owner 对两项旧 Parser 分别签认后推导，不存在预先固定的 24/24 发布要求**；所需 Package Schema、Publisher version、合法身份与 Bindings 由 Owner/Compiler 正式发布；Provider 查询子集 2/2，加 Codec 后全量 3/3，由 ca-client-tools 发布，不能从旧数组直接转换。

**历史 Compiler v2.1.0 的** Development package version 必须为 exact SemVer，旧 wrapper 的 1.0.0 只供源审计；**新 1.6.0 Publisher 不得默认使用该版本或旧 package.json Schema**。Owner source version v1alpha4 不能冒充新语言或新 Package identity。必须保留 Owner source stable Package ID、ToolCatalog contract IDs、Owner outcomes、Receipt / Commit Proof / Reconcile 语义或冻结 v1alpha5 Runtime Owner linking。


## 5. 组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| CA-SL 1.6.0 Skill Author Source | 仅声明目标、Procedure、Capability ID grants / 使用点和业务参数；作者源只表达 Capability ID | 作者及模型 Action 不声明或选择 Callable ID、独立 Operation ID、backendOperationId、URL、Header、凭据或 Owner 结果 |
| CA-SL 1.6.0 Compiled Skill Artifact | 保存 Compiler 静态生成的 Procedure、唯一 `capabilityBindings`（Capability→公开 Callable）和精确依赖闭包 | 不接受作者或模型覆盖 Callable Binding；不暴露私有 backendOperationId、URL、Header、凭据 |
| Compiler | 只接受 CA-SL 1.6.0；执行新 Parser / AST / Check / Link / Build / Verify，生成 Request Schema closure 与唯一 capabilityBindings | 启动 Provider、检查运行时可用性、授权真实调用 |
| Plugin Manager | Provider 包加载、进程生命周期、握手、IPC correlation、Tools Extension 分发 | Skill 选择、Capability 授权、Owner Commit 判断 |
| ProviderV2 Tools Extension Driver | 读取 Provider v2 发布映射；启动 Provider；适配 initialize/catalog/invoke/cancel；把私有 backend ID 隐藏在 Host 内部 | 创建第二个 Provider Manager、复制 ToolCatalog、授予 Skill 权限 |
| Runtime Action Boundary | 检查当前 Run/Skill Scope、Capability Binding、内部 Callable、Schema、Effect、Artifact 来源和状态；解释 Owner Receipt / Outcome / UNKNOWN / Reconcile | 直接管理 Provider 进程或重写 Owner 业务规则 |
| Tool Provider | 执行发布包声明的 Operation，按协议返回结果和 Owner observation | 选择 Skill、扩张 Callable Scope、伪造 Owner Commit |
| Owner | 权威业务状态、提交、Receipt、Commit Proof 和 Reconcile 决策 | 由 Host/Plugin 推断或替代 |
| Host Artifact Store | 保存原始二进制和引用，限制其 Invocation / slot / direction | 让 Provider 自建第二个 Artifact 数据库 |

## 6. Provider 包加载与启动

### 6.1 输入

Plugin Manager 的部署配置为每个 Provider Extension 提供一个显式、已安装的本地 Provider 包路径。当前 ca-client-tools 输入是 v1.2.0 平台包，不是单独的 Interface Package ZIP。

加载所需材料：

- Provider provider.yaml；
- provider.yaml 指定的 runtime-bindings.yaml；
- 与 Provider sidecar 所引用 Owner identity 一致的 Owner Contract Package 安装快照（当前为 env-openamsm `urn:openamsm:mas:tool-contracts` v1alpha4），用于 Runtime 读取 Owner ToolCatalog / CapabilityContracts / Evidence / Schema；该快照不属于 Provider 包。Provider 包内的 Interface snapshot 由 provider.yaml 的 `interfacePackagePath` 选择；`interfaceSnapshotDigest` 若由上游发布，仅作元数据，Next 不计算、不比较。v1alpha5 Artifact dependencyClosure 不含 dependency snapshotDigest，不能据此声称 per-Skill digest pin。
- Provider 二进制；
- 同版本包内的 interface/ 快照；
- sidecar 引用的 Owner Contract 身份和 Schema 文件；
- Host 注入的服务配置和凭据（不得从包内不可信文本执行）。

### 6.2 校验与初始化顺序

Provider Package Loader、Provider initialize/catalog 是 **安装级生命周期**，只依赖已选 Provider 包、部署配置和部署选定的 Owner publication，不依赖当前 Skill Artifact。

1. **解析 Provider 包入口。** 使用严格 YAML 解析 provider.yaml；拒绝重复 key、未知字段、缺失必需字段和不支持的版本。
2. **约束 Provider 包内路径。** `interfacePackagePath`（目录及其完整文件树）、`runtimeBindingsPath`、sidecar 引用的 Schema 文件和可执行文件都必须解析在所选包根目录内；拒绝绝对路径、路径穿越和符号链接逃逸。对 `interfacePackagePath` 不得只校验目录入口或抽样文件；树内每个实际文件都必须受相同的根目录约束。部署选定的 Owner publication 是独立安装快照，不要求位于 Provider 包内。
3. **检查 Provider Interface snapshot。** 对 `interfacePackagePath` 指向的完整文件树检查路径、必需文件、Package 结构和声明版本；不得只检查 package.json 或抽样文件。若上游携带 `interfaceSnapshotDigest`，仅作为声明元数据，不计算、不比较，也不作为加载门禁。
4. **校验 Runtime Bindings sidecar 与 Owner publication。** 验证 sidecar 精确 API identity、Provider ID/version、Schema 文件闭包和唯一 binding ID；sidecar 的 Owner stableId/version/operations 必须与部署选定的 Owner publication 一致。`runtimeBindingsDigest`、`publicationDigest`、`manifestDigest` 若由上游携带，仅作元数据，不计算、不比较。不得把 Owner ToolCatalog 当成 Provider Interface Package，也不得自行生成缺失 Schema。
5. **校验静态映射与 Reconcile 关系。** 每个 Provider public mapping 必须与 Provider Interface Package 的 Callable ID、Effect 和 Schema 一致；每个 Owner Runtime Binding 的 ownerCallableId、runtimeOperationId、Effect、Schema 和 Capability membership 必须与部署选定的 Owner Contract 一致。publicCallableId、runtimeBindingId、runtimeOperationId 和 backendOperationId 在各自身份空间必须唯一。对每个 MUTATION 的 `commitProof.reconcile.bindingId`，必须在同一 sidecar 中解析到唯一 READ binding，并将被引用的 binding ID 汇总为 Next Runtime 的 internal-only Reconcile 集合。目标缺失、重复、Effect 非 READ 或引用不一致时 fail-closed。此阶段只验证 sidecar/Owner 静态映射，不读取或猜测 Provider 内部 Backend Catalog，也不要求当前 Skill Artifact 已存在。
6. **选择固定发布物并启动 Provider。** 部署配置 pin 精确 Provider Release tag、平台归档和安装目录；Demo 不下载 dynamic latest，不校验 `SHA256SUMS`、package checksum 或 executable digest。使用固定可执行文件和 argv（当前命令为 `provider serve`），不经 Shell 字符串解释。该流程依赖受控 Demo 环境，不构成生产级供应链验证。
7. **Provider initialize。** 发送 Host/Provider instance identity 与 frame、in-flight、call-duration limits；核对 Provider ID、版本、catalogVersion 和显式 catalog 查询所需的声明信息。`buildDigest`、`backendCatalogDigest` 若由上游返回，仅作诊断元数据，不由 Host 计算、比较或作为加载门禁。缺失 Provider identity/version、catalogVersion 或显式 catalog 不完整时 fail-closed。
8. **显式 catalog 查询。** 仅在 initialize 成功后，向 Provider 请求 provider.yaml 公开 bindings 与 Runtime Bindings sidecar 的精确 backendOperationId 去重并集（当前预期 36 个 ID）；校验 supported/unsupported 分区、描述符、Effect、catalogVersion 和请求顺序。backend ID 是否实际存在只在此步骤确认。无需新增 list-all 方法，也不得用 catalog 响应发现未声明的公开 Callable。
9. **发布可用 Extension。** 将明确可用的公开 Callable 绑定到该 Provider Extension。未配置或未实现的 binding 保留明确 unavailable 诊断，不得切换到其他 Provider、旧注册文件或默认业务 adapter。

**按 Skill 解析依赖。** Provider Package Loader 在安装期独立校验包。Importer 在产生 candidate 前拒绝旧版 Artifact。Resolver 对正式 1.6.0 Artifact 按 capabilityBindings 和部署快照核对 Package 身份、双向唯一映射、kind、Effect 和 I/O Schema，再为该 Skill 派生精确 Scope。Schema-only 闭包只导入声明的 Schema，不增加 Callable。任何缺失、歧义或不符都在激活前拒绝。

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
| initialize | hostInstanceId、providerInstanceId、limits；可选 artifactChannel | providerId、providerVersion、buildDigest、backendBindingCatalogDigest、catalogVersion、`limits`；有通道时 `artifactChannel` 只回报有效 bounds，不回显 processToken/baseUrl |
| catalog | backendOperationIds：唯一的精确 ID 数组 | supported、unsupported（NOT_IMPLEMENTED / NOT_CONFIGURED）、catalogVersion、仅 supported IDs 的 bindings 描述符；保持请求顺序 |
| invoke | backendOperationId、arguments、invocation（invocationId、producerInvocationId、deadline）；仅 typed MAS 可选 hostInvocation | Provider result envelope；MUTATION 只能走 typed MAS handler，genericSBI MUTATION 在远端 I/O 前拒绝；不得把 Owner Outcome 映射成 COMMITTED |
| cancel | targetRequestId | CANCEL_REQUESTED / ALREADY_COMPLETED / NOT_FOUND；取消不等于远端 mutation 回滚 |

initialize 的 limits 至少约束 maxFrameBytes、maxInFlight 和 maxCallDurationMs。可选 artifactChannel 是关闭对象，字段为 baseUrl、processToken、requestTimeoutMs、maxArtifactBytes、maxAggregateBytes、maxAttachments；缺失 channel 时 artifact-bearing binding 为 NOT_CONFIGURED，且必须在远端 I/O 前拒绝。显式提供格式非法的 channel 则 initialize 返回 PROVIDER_CONFIGURATION_INVALID，不进入 READY，不发 catalog 或 invoke。原始二进制通过 ca-host.artifact-store/v1 channel 传输，不进入 NDJSON。

catalog descriptor 只包含私有 backendOperationId、Effect、request/response media type、参数或 generic schema、source pin 和 Artifact slot 描述。不得包含服务 origin、URL、HTTP method、route template、header/token、公开 Callable ID、Capability ID、Owner Outcome 或 Evidence guarantee。catalog 是可用性核对，不是授权。

invoke 的 invocation.deadline 是绝对 RFC3339 UTC 时间。对 200 等 JSON 结果，Provider 返回 httpStatus + response；204/bodyless 结果只返回 httpStatus；有效 application/problem+json 作为 Provider 成功协议结果返回 httpStatus + problem。Provider 不解释 Owner 业务结果，也不自动 retry。

错误代码至少包括 PROTOCOL_VERSION_UNSUPPORTED、PROTOCOL_FRAME_INVALID、PROTOCOL_FRAME_TOO_LARGE、PROTOCOL_METHOD_UNSUPPORTED、PROTOCOL_REQUEST_ID_INVALID、PROVIDER_NOT_INITIALIZED、PROVIDER_ALREADY_INITIALIZED、PROVIDER_CONFIGURATION_INVALID、PROVIDER_BINDING_CATALOG_INVALID、BACKEND_OPERATION_UNSUPPORTED、BACKEND_ARGUMENTS_INVALID、CALL_DEADLINE_EXCEEDED、CALL_CANCELLED、REMOTE_TRANSPORT_ERROR、REMOTE_RESPONSE_INVALID、ARTIFACT_REFERENCE_INVALID、ARTIFACT_TRANSFER_FAILED、PROVIDER_INTERNAL、PROVIDER_SHUTTING_DOWN。错误 message/detail 不得包含凭据、远端 body、SUPI 或调用者私有值。

### 6.5 Provider package binding 与 Runtime Bindings sidecar（v1.2.0 历史实现审计）

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

provider.yaml 的 11 个 public READ mappings 与 sidecar 的 25 个 Owner mappings 是两个不同身份空间；Host 显式 catalog 请求使用两者的私有 backendOperationId 去重并集。启动时 Host 检查 Interface 完整文件树和 sidecar 结构，再校验 Provider initialize identity/version/catalogVersion 与显式 catalog 响应。`interfaceSnapshotDigest`、`runtimeBindingsDigest`、`backendCatalogDigest` 若存在仅作上游元数据，不计算、不比较，也不要求两端 digest 对账。

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
- Provider 启动时把 31 个 typed MAS Callables 和 2 个 evidence handlers 追加到基础 11 个 READ bindings，并把扩展后的 catalog digest 返回给 Host。Receipt Query 是只读 Owner evidence Callable；Reconcile 是专用只读 Reconcile target，均不重新派发 mutation。
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
          Artifact export Callable allowlist
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

1. 当前 Run 已绑定精确的正式 1.6.0 Skill Artifact 与已解析的依赖闭包；Owner Callable 必须解析到部署固定且与 Provider sidecar 一致的 Owner Contract snapshot，并满足 Artifact 的 stablePackageId / required exports；Provider READ Callable 必须解析到字节与 provider.yaml `interfaceSnapshotDigest` 一致的 Interface Package。Continuation 继续使用原 Run，不重新选 Skill。
2. 从当前 Run 固定的 1.6.0 Artifact 按请求的 Capability ID 查唯一公开 Callable。核对 Binding 所属 Package、kind、Effect 和输入输出 Schema，Provider 的私有路由不能扩大 Scope。
3. 同一 Callable 也只能反向归属于该公开 Capability。缺映射、双向歧义或 Snapshot 与契约源不符时，拒绝本次动作，Provider IPC 为零。
4. 当前 Run 的 Callable allowlist 必须排除所有由 Mutation `commitProof.reconcile.bindingId` 引用的 internal-only Reconcile binding；即使 Artifact export closure 包含对应 Owner READ export，普通 Skill/LLM Action 仍须在发送前拒绝，并返回稳定诊断 `INTERNAL_RECONCILE_ONLY`，Provider IPC 次数必须为零。Reconcile Coordinator 只能通过 Runtime 内部专用入口访问该 binding。
5. 输入符合该 Callable 实际所属契约源（Provider Interface Package 或 Owner Contract Package）的 Schema；未知字段、缺失字段、类型/范围错误均拒绝。
6. Effect 与发布契约一致；Provider catalog descriptor 与 Owner Contract / sidecar 不一致时 fail-closed。
7. Artifact Reference 由 Host 管理，且与当前 Run、Invocation、direction、slot 和 mediaType 一致。
8. 调用满足当前 Run 状态、deadline、预算与 continuation 约束。

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

**历史 Owner/Compiler 审计：** env-openamsm v1alpha4 将 `MAS.RECONCILE` 发布为普通 READ operation，并在 CapabilityContracts 中声明 `mas.reconcile.exact_original`。冻结 v1alpha5 Compiler 仅在某个 Mutation 的 `mutation.reconcile.callable` 明确指向该目标时，才会将其识别为 dedicated Reconcile 并拒绝普通 `operation.tool` 引用；该版 Owner 的 21 个 Mutation 未声明该字段。因此历史 Build 可能接受 Skill 对 `mas::MAS.RECONCILE` 的直接引用，Next 不得把编译期拒绝当作已具备保证。

Next Runtime 必须从已验证 sidecar 中所有 Mutation 的 `commitProof.reconcile.bindingId` 收集目标，并将目标 binding ID 从 Skill/LLM 的普通 dispatch surface 排除；目标必须在同一 sidecar 中唯一解析为 READ binding，否则 Provider package load fail-closed。即使 Artifact export closure 包含该 READ export，普通 Action 也必须返回 `INTERNAL_RECONCILE_ONLY` 且不发送 Provider 请求。Reconcile Coordinator 只可通过 Runtime 内部专用入口，使用原始 originalInvocationId、原 Run Owner scope 和 sidecar 声明参数调用该 binding；该入口不是第二份公开授权路径，也不接受模型提供的 invocation 或 Host-private 参数。

1. Runtime 保留原始 Callable、originalInvocationId、原始调用输出/私有材料引用和 Owner scope。
2. Reconcile 使用 Owner Contract 中声明、并由 sidecar Mutation `commitProof.reconcile.bindingId` 精确引用的 Reconcile binding 和同一 originalInvocationId。
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
Host Artifact Store 通过独立 loopback channel 管理 opaque reference、Invocation/direction/slot 绑定、原始 bytes、长度/数量配额、超时取消、过期清理和原子发布；新 1.6.0 Demo 目标为 ca-host.artifact-store/v2，不计算或校验 SHA-256 / checksum / digest。历史 ca-host.artifact-store/v1（commit 2c0b07f2eaff3bc1020bfc6775ef9bf09e3052ae）仍要求 SHA-256，仅作历史审计，不得复用；SR-010/F05 负责 v2 no-hash 设计与 Host 实现。

### 8.2 Codec

- Codec 的协议实现本身不是 Tool、Plugin 或授权机制；只有正式发布为 Callable Operation 后，才能作为现有 Tools Extension 的 Operation 使用。
- Codec 不拥有 Skill 选择、网络传输、Owner 状态或 Runtime；不建立独立 Codec Plugin/Manager。
- 只能使用发布契约明确标记并有证据支持的消息子集。reencodeVerified 不等于 qualified；不合格消息不得因 round-trip 相等而升级。
- ca-client-tools PR #39 当前为 OPEN，Phase B facade/worker 证据已记录，Phase C Consumer Migration 未开始。本 SR 不依赖 PR #39 合并，不声明 Next 已消费该 Codec。

### 8.2.1 Codec 公开 READ Operation（SR-026）

Codec 的公开入口是现有 ca-client-tools Provider Interface Package 中的一个本地 READ Callable Operation；它不是第二个 Plugin、Manager 或远程网络 Tool。Skill 只声明 Capability，Runtime 仍通过现有 Provider / Tool Action Boundary 派发；Codec 不执行 SBI 请求、不产生 Owner Mutation，也不替代 Owner 的业务解析能力。

**固定身份（中央设计目标，尚未发布）：**

| 项目 | 唯一目标值 |
|---|---|
| Capability ID | protocol.nas.5gsm.release-request.decode |
| Callable ID | ca-client-tools.codec.nas.5gsm.release-request.decode |
| Interface Package ID | urn:wtlab:ca-client-tools:openamsm-sbi-interface |
| Interface Package / Provider 目标版本 | 2.0.0（11→3 的破坏性公开接口收敛；纯数字 SemVer） |
| Runtime Bindings Sidecar | ca.tool-provider-runtime-bindings/v2 |
| Provider Wire Protocol | ca-client-tools.provider/v2（不升级线协议） |
| Host Artifact Channel | ca-host.artifact-store/v2（新 1.6.0 no-hash Demo Channel；v1 SHA-256 历史契约不复用） |
| 首批消息 | NAS 5GSM PDU Session Release Request，消息类型 0xD1 / PDUSessRelReq |

Provider Interface Package 的公开闭包固定为 3 Capability / 3 Callable：

| Capability | Callable |
|---|---|
| openamsm.smf.mas.context.read | ca-client-tools.openamsm.smf.mas.context.read |
| openamsm.nf.metrics.read | ca-client-tools.openamsm.nf.metrics.read |
| protocol.nas.5gsm.release-request.decode | ca-client-tools.codec.nas.5gsm.release-request.decode |

前两项分别用封闭的 contextKind、resourceKind selector 收敛历史私有 backend 路由；第三项是本 SR 新增的协议级 Codec 能力。每个 Capability 只能绑定一个 Callable；Callable 内部可使用私有 backend 选择，但 backend ID 不进入 Skill 作者源或公开 Capability 集合。

**输入契约：**公开 inputSchema 是 type: object、properties: {}、additionalProperties: false 的空闭合对象。原始 NAS 字节不是 Skill / LLM 参数，不接受 Base64、文件路径或任意 URL。Host 在完成 Capability 授权和公开 Schema 校验后，通过 Provider Runtime Bindings 私有参数注入当前 Invocation 的材料：

~~~yaml
apiVersion: ca.tool-provider-runtime-bindings/v2
privateArguments:
  - name: n1_sm
    source: PRIVATE_MATERIAL
    artifact:
      direction: INPUT
      slot: n1Message
      mediaType: application/vnd.3gpp.5gnas
      required: true
~~~

Provider catalog 对应 descriptor 必须声明 artifactSlots.inputs，pointer 为 /n1_sm、slot 为 n1Message、mediaType 为 application/vnd.3gpp.5gnas。Host 只注入绑定到当前 Invocation 的 artifactRef；该字段不进入公开 Input Schema，也不允许 Skill 自行构造。未配置 v2 Artifact Channel、slot 不匹配或引用不属于当前 Invocation 时，在派发前 fail-closed。

**输出契约：**Provider Interface Package 导出闭合的 schemas/codec/nas-pdu-session-release-request-output.schema.json。字段采用 3GPP 语义命名，不直接暴露 Free5GC Go struct 字段名或 ProjectToJSON 的反射字段名：

- protocol 固定 NAS；messageType 固定 PDU_SESSION_RELEASE_REQUEST；messageTypeCode 固定 209。
- header 必含 extendedProtocolDiscriminator（46）、pduSessionIdentity（1～15）和 procedureTransactionIdentity（0～254）。
- message 只暴露首批已资格化的结构字段；首批 Golden 未覆盖的 IE（包括当前 Codec 标记为 lossy / NOT_QUALIFIED 的 ePCO）不得作为可用业务字段返回。
- qualification 必含 complete、qualified、rawPreserved、structuralParse、projectionValid、reencodeEligible、reencodeVerified、consumedBits、totalBits 和 ieToDo。
- status 使用 SUCCESS、PARTIAL、UNSUPPORTED_MESSAGE、UNSUPPORTED_IE、DUPLICATE_IE、INVALID、NOT_QUALIFIED；diagnostics 使用稳定 code/message，并可带 IEI / offset。
- 不返回原始字节或 Base64；只返回 rawLength 和保留/往返验证标志。原始 Artifact 仍由 Host Artifact Store 持有。

只有 status=SUCCESS 且 complete=true、qualified=true、rawPreserved=true、projectionValid=true、reencodeVerified=true 时，Runtime 才能把解码结构作为有效 Observation。其他状态是显式结果，不得提升为 PASS；传输、Artifact 引用或 Provider 失败仍按 Provider READ 错误处理。

**执行路径：**Host 注入 invocation-scoped artifact reference → Provider Artifact Channel v2 读取原字节 → Provider 进程内直接调用 Go protocol/codec NAS Facade → 显式映射到上述 3GPP Output Schema → 返回 READ Observation。Provider 不启动 Python codec-worker 子进程，不向远端 SBI 转发，不修改原始 Artifact。Python Worker 仅是独立开发/消费入口，不是 Agent Runtime 依赖。

**首批范围与反例：**有效向量 2e 05 01 d1（PSI=5、PTI=1、Release Request）必须完整解析、字节往返一致并满足资格标志；截断输入 2e 05 01 必须 INVALID；Release Complete 向量 2e 05 07 d4 对本 Capability 必须 UNSUPPORTED_MESSAGE / MESSAGE_TYPE_OUT_OF_SCOPE，即使底层库能识别该消息也不得越过本次公开范围。其他 NAS / NGAP 类型不属于本次发布范围，扩展必须新增中央设计与 Golden，不得从底层库支持列表自动扩展公开 Schema。

该 Codec Capability 与 Owner 的 mas.ssm.n1.modify.parse、mas.ssm.n1.release.parse 是不同层次：后两者仍是 Owner 业务能力；本 Codec 只提供协议级 READ 解码，不替代 Owner Receipt、Reconcile、状态判定或提交证明。

### 8.3 1.6.0 Codec Provider 与 Owner N1 Parser 的唯一性审计

现有 ca-client-tools v1.2.0 的 **2 Capability / 11 READ Callable** 只是历史基数；新 Provider 目标为 **3 Capability / 3 唯一 Callable**：两个收敛查询入口加一个 SR-026 Codec READ。Codec 的公开机器 ID、输入/输出 Schema、封闭消息 Profile、slot/mediaType、handler 与发行版本由 ca-client-tools Publisher 冻结，未发布前不可配置为可用。首批 0xD1 Release Request 向量不证明 0xC9 Modify 或 NGAP 资格；这两类业务依赖分开标记 BLOCKED。

`env-openamsm@dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 的 `SSM.PARSE_N1_MODIFY` 虽声明 Effect=READ，但在 `0007-ssm-n1-modify-parse.patch` 中实际调用 `ogs_nas_5gsm_decode`；`SSM.PARSE_N1_RELEASE` 也已存在历史 Owner ToolCatalog，但其 handler 输入/语义须进一步核验。**READ ≠ 纯业务校验**。新版 Skill 的 NAS/NGAP 解码唯一归已资格化 Provider Codec；Owner 只能消费经 Result Schema 校验的 typed projection 作业务验证，并保留业务状态、mutation、Receipt/Proof/Reconcile。Owner 必须分别签认两个旧 Parser：双移除为候选 22/22；一项移除、一项重构为只消费已验证 Codec Result 的纯业务 READ 为候选 23/23；两项均重构为纯业务 READ 为候选 24/24；任一项未签认时成员数未冻结且不得发布。任何其他导出变化都必须重新计数。相关冻结门槛见 SR-029 §3/§10.1、F06 §7.1；不得把历史 Parser 自动视作新版 Callable，也不能在 Codec 未发布时做 fallback。

T1 只允许 Event Plugin 为共享 SBI Update 路径最小读取 NAS 消息类型作路由；正式协议 Decode 在绑定 Skill/Run 后的 T2 Provider READ 中执行，Host-owned Artifact channel 以 Invocation/slot 授权；Result Schema 未验证不得传给 Owner，不能构造 T1 when/input。二进制原始 bytes 保留为证据。

## 9. 失败语义

| 失败情形 | 处理位置 | 结果与约束 |
|---|---|---|
| Provider 包、Manifest、Interface Package 或 sidecar 结构无效 | Plugin Manager 加载期 | Provider Extension 不可用；明确报错，不降级、不 fallback |
| Owner Contract 版本或发布身份不匹配 | 包加载/Runtime 绑定校验 | 拒绝绑定；不得用相似字段或旧版映射补齐 |
| backendOperationId 不存在或 Provider catalog 返回 unsupported | ProviderV2 Driver | 对应 binding unavailable；不得重构 ID 或调用其他 backend |
| 缺 Capability Binding、Scope 越界或 Owner membership / Effect 无效 | Runtime Action Boundary | 拒绝动作，Provider IPC=0。 |
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
| runtime/capability_contract.py | 历史 Demo 中的 Capability / Operation 关系与独立 Effect 一致性检查 | 只复用 Effect 一致性检查；历史 Capability→多 Operation 关系不作为 CA-SL 1.6.0 目标语义，目标基数为 Capability ↔ Callable 双向一对一 |
| runtime/capability_scope.py | 历史 Demo 中按 Skill Artifact 解析 invocation-scoped Operation allowlist | 目标 Runtime 从唯一 Capability Binding 派生精确 Callable allowlist；作者源和模型 Action 只暴露 Capability ID |
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
- Compiler 通过正式 Package 将声明的 Capability 静态链接到唯一公开 Callable。Runtime 校验 1.6.0 Artifact 中的 capabilityBindings、契约来源、Scope、kind、Effect 和 Schema。
- Provider 启动握手、精确 catalog 查询、requestId 关联、cancel/timeout 和进程退出有自动化测试。
- 未绑定的 Capability、旧版 Artifact、Owner membership 或 Effect 不符、Schema 错误均在派发前拒绝。合法调用遇私有 backend 缺失或 Provider 不可用时明确报错。
- Skill/LLM 无法看到或构造 backendOperationId、服务 URL、凭据和 privateArguments。
- READ 输出经过 Schema 与来源校验；MUTATION 只有有效 Owner Receipt + Commit Proof 才能 COMMITTED。
- UNKNOWN 使用原始 Invocation identity 进行 Reconcile，零重复 mutation。
- Provider artifact-bearing operation 使用 Host Artifact Store；原始 N1/N2 bytes 保真。
- Codec 只在正式 Callable/Runtime Binding 发布且资格范围明确后按需接入。
- Echo 与 OpenAMSM 使用相同 Plugin Manager / Tools Extension 机制；新增业务不要求修改 Agent Core 的业务分支。

### 11.1 Next 侧实现分解（逻辑模块）

以下是后续代码 SR 必须落实的逻辑边界，不预设实现仓的文件路径；具体路径、分支、Issue、测试命令和 Owner 由代码实施 SR 指定。

| 逻辑模块 | 唯一职责 | 输入 / 输出边界 | 必须覆盖的验收用例 |
|---|---|---|---|
| Provider Package Loader（Plugin Manager 内） | 解析已安装 Provider 包，校验 provider.yaml、interfacePackagePath 完整文件树、Runtime Bindings sidecar、Owner publication 引用和包内路径 | 输入包根目录、部署配置、部署选定 Owner snapshot；输出只读 ProviderPackageDescriptor（Provider identity/version、公开 mappings、sidecar mappings、上游元数据、internal-only Reconcile set） | 重复 YAML key、未知版本、interfacePackagePath / runtimeBindingsPath / Schema / executable 路径穿越、绝对路径或符号链接逃逸、Owner identity 不匹配、Reconcile target 缺失/重复/非 READ 均拒绝加载；digest 元数据不做 mismatch 检查 |
| ProviderV2 Driver（Plugin Manager 内 Tools Extension） | 管理单个长生命周期 Provider 进程；实现 initialize/catalog/invoke/cancel、requestId correlation、limits 和安全关闭 | 输入已验证 descriptor 与 Host 注入配置；输出统一 Tools Extension 调用结果；私有 backendOperationId 只在 Driver 内部 | Provider identity/version/catalogVersion 与显式 catalog 对账；不做 SHA256SUMS 归档校验、Host executable digest 或 backendCatalogDigest 比对；乱序响应关联、重复/非法 requestId、超大 frame、in-flight 超限、cancel、EOF drain、Provider 崩溃、stderr/stdout 分离、禁止自动重试 |
| Contract Dependency Resolver（Runtime 内） | 在激活前解析每个 Skill 的 Provider、Owner 及 Schema 闭包 | 正式 1.6.0 Artifact 的 capabilityBindings、部署快照及 sidecar → 此 Skill 的精确 Binding 与 Scope | 逐包和合并快照均验证双向唯一；缺 export、错 Package/kind/Effect/Schema、陈旧代际和旧 Artifact 均拒绝。 |
| Runtime Action Boundary | 在 Provider IPC 前校验 Run/Skill Callable allowlist、Callable、Schema、Effect、HostInvocation、privateArguments 和 Artifact Reference | 输入 Runtime Action Request 与当前 Run Context；通过后输出 ProviderV2 Driver 的内部调用参数；拒绝时不发送 Provider 请求 | 未声明 Callable、internal-only Reconcile 普通调用（INTERNAL_RECONCILE_ONLY 且零 Provider IPC）、Owner membership/Effect 不一致、Schema 错误、Host scope 不匹配、Artifact slot/direction 不匹配均在远端 I/O 前拒绝；Coordinator 内部 Reconcile 使用原 originalInvocationId 成功 |
| Owner Outcome Resolver / Reconcile Coordinator（Runtime 内） | 按 Owner Contract 解释 Receipt、Commit Proof、UNKNOWN 和 exact-original Reconcile | 输入 Provider result、Owner snapshot、原始 Invocation 和 sidecar evidence binding；输出 Owner Outcome / Evidence / Reconcile 状态 | HTTP 2xx 不得单独 COMMITTED；Receipt/Proof 精确绑定才可 COMMITTED；UNKNOWN 不重发 mutation；Reconcile 使用原 originalInvocationId；重复 mutation 数为 0 |
| Host Artifact Adapter | 通过 Host Artifact Store channel 交接原始二进制，执行引用、大小、数量和 slot 边界检查 | 输入 Host artifactRef 与 Provider artifactChannel；输出受限 Artifact transfer；不把原始字节放入 NDJSON | channel 缺失、引用越界、size/aggregate/attachments 超限均在远端 I/O 前拒绝；禁止 Base64 和任意本地路径 |
| Plugin Manager Extension 注册 | 将 Native Plugin 和 ProviderV2 Driver 纳入同一 Manager 的生命周期与分发 | 输入唯一 Plugin Package/Extension descriptor；输出一个统一 Tools Extension 入口 | Native Plugin 与 Provider v2 并存；重复 Callable/冲突 mapping 拒绝；不存在第二 Manager、Registry、Runtime、授权路径或 fallback |

逻辑调用顺序固定为：安装级 Package Loader（含静态 sidecar/Owner/Reconcile 校验）→ 固定 Release tag / 平台归档选择（无 hash 校验）→ ProviderV2 Driver initialize/catalog → per-Skill Contract Dependency Resolver（import/update 或 generation 激活前）→ Runtime Action Boundary → ProviderV2 Driver invoke → Owner Outcome Resolver / Reconcile。Plugin Manager 只管理进程与 Extension；Runtime 只管理 Skill Scope、契约校验和 Owner 结果；Provider 不选择 Skill、不授权、不判断 COMMITTED。

### 11.2 当前外部证据边界

- ca-client-tools v1.2.0 已发布，Provider v2、公开 Interface Package 和 Runtime Bindings 是现行外部依赖。
- ca-client-tools PR #39 OPEN；Phase C 未开始，不是当前可用 Codec 消费实现。
- ca-agent-demo main 提供参考代码与测试，不等于 Next 已实施或已验收。
- Next 的 Plugin Manager、ProviderV2 Driver、Runtime Action Boundary 和跨仓集成验收均未由本 SR 执行；真实 Harness/代码执行保持 NOT_RUN。

### EC03 外部生产端与复验

Provider v1.2.0 固定源 `7bcb2614aa3615d8358df31eecefd0909e894e40`，以 `internal/provider/protocol.go`、`internal/provider/server_v2_test.go`、`internal/provider/artifact_protocol_test.go` 和 `contracts/host-artifact-store/v1/` 核对两端。在 ca-client-tools 根运行 `go test ./internal/provider ./internal/runtimebindings`，在 Next 执行 SR-010 的 channel 测试。分别捕获无通道、有效通道、显式非法通道的 initialize/catalog 帧以及 upstream 调用次数，保留测试用 token 的遮蔽结果。

Codec PR #39 的固定候选 `eb1169fe1d0e2e691d101908aad08ee8801da754` 在 `protocol/codec/nas.go` 暴露 Go 函数，未给出已发布 Tool Callable。由 [SR-026](../../SR/SR-026-Codec公开工具发布.md) 跟踪公开接口、Provider 本地执行与最小有效 NAS 子集；SR-010 消费其发布物，SR-015 仅恢复中央设计。

## 12. Capability-first 契约与基数审计（1.6.0 目标）

本节定义新作者版本的目标设计；本节不改变当前 Owner v1alpha4、ca-client-tools v1.2.0 或 CA-SL v1alpha5 已发布字节。

### 12.1 唯一 Skill-facing 映射

每个 Skill-facing Capability ↔ 一个公开 Callable，双向基数均为 1。CapabilityContracts / capabilities.json 当前的数组字段可保留，但 Compiler 必须检查每个 Capability 的公开 Callable membership 数量恰好为 1，并检查每个 Callable 只归属一个 Skill-facing Capability。Callable ID 仍是 Package / Compiler / Runtime 内部调用身份，不出现在 Skill 作者源。

### 12.2 当前 Owner CapabilityContracts v1alpha4 审计

来源：env-openamsm main dc83ccbf5be54dcc7112dd43ba95ea6fa5975550；capability-contracts.yaml blob 4fdd22f0eda2c2f2b5096cd167bc705f5a29e06e；ToolCatalog blob 88d9709aac62c6d608d057dc797ada6f2189611f。

| 当前关系 | 真实成员 | 审计结果 | 1.6.0 目标 |
|---|---|---|---|
| 24 个 Capability 条目 / 25 个 membership | 23 个单成员 Capability + mas.se.events.emit 的 2 个成员 | 唯一多成员 Capability 为 mas.se.events.emit | 拆分事件及排除 Reconcile 后，两个 Parser 决策前仅作为推导基数；双移除候选 22/22、一删一留候选 23/23、双保留为纯业务 READ 候选 24/24；以逐项签认后的实际导出重算，不冻结固定数量 |
| mas.se.events.emit | SE.EMIT_EVENTS；SE.EMIT_RELEASE_EVENT_C | Input Schema 不同：ESTABLISHED + sessionKeys；RELEASED marker。Evidence Guarantee 不同：se.establishment-event-recorded 与 se.release-event-marker-written | 分别导出 mas.se.establishment-event.record → SE.EMIT_EVENTS；mas.se.release-event-marker.write → SE.EMIT_RELEASE_EVENT_C |
| mas.reconcile.exact_original | MAS.RECONCILE | 当前 CapabilityContracts 中存在，但它是 Mutation Reconcile 专用 READ target | 从 Skill-facing CapabilityContracts 移除；保留 ToolCatalog contract、mutation.reconcile binding 和 Runtime internal-only Coordinator 路径 |
| mas.receipt.query | MAS.RECEIPT_QUERY | 普通 READ evidence Callable，受 Capability / Scope 约束 | 保留当前 Skill-facing Capability / Callable 一对一映射 |

现有 Owner ToolCatalog 的 **25 contracts（21 MUTATION + 4 READ）是 v1alpha4 历史基数**；MAS.RECONCILE 在新版仍为 internal-only，不可授予 Skill。拆分 `mas.se.events.emit` 并排除 Reconcile 后，必须以两项旧 Parser 的分别签认推导实际成员数，不设固定 24/24 门槛：

| `SSM.PARSE_N1_MODIFY` | `SSM.PARSE_N1_RELEASE` | 1.6.0 候选成员数 | 发布条件 |
|---|---|---|---|
| 移除 | 移除 | 22/22 | 两项均有 Owner 正式移除签认 |
| 移除 | 重构为纯业务 READ | 23/23 | 保留项只消费经 Codec Result Schema 验证的 typed projection，并有 Owner 正式签认 |
| 重构为纯业务 READ | 移除 | 23/23 | 保留项只消费经 Codec Result Schema 验证的 typed projection，并有 Owner 正式签认 |
| 重构为纯业务 READ | 重构为纯业务 READ | 24/24 | 两项均完成纯业务重构并分别签认 |
| 任一未签认 | 任一未签认 | 未冻结 | Publisher 必须拒绝 Release，不得猜测、自动删除或自动补齐成员 |

历史 ToolCatalog 成员数不等于新版公开 Package 成员数；不能未经签认就断言其余单成员身份均可原样沿用，任何其他导出变化均须重新计数，也不擅自修改旧 ToolCatalog。

事件拆分保留原有 ToolCatalog Schema 和 Evidence Guarantee，不把两种事件合并成泛化接口。建立事件仍使用 ESTABLISHED + sessionKeys 和 se.establishment-event-recorded；释放标记仍使用 RELEASED 与 se.release-event-marker-written。只替换 Skill-facing Capability ID，不更改 Owner 的业务副作用或保证含义。

### 12.3 当前 Provider Interface v1.2.0 审计

来源：ca-client-tools tag v1.2.0；provider-bindings.yaml blob 8e42e24eedc9e3211171f76a674c6be6bd6b1984。

| Capability | 当前公开 Callable | 当前契约 | 1.6.0 目标 |
|---|---:|---|---|
| openamsm.smf.mas.context.read | 8 | 全部 kind=observation、effect=READ；共用 mas-context-query-input 与 mas-context-result Schema | 一个公开 Callable；Input 增加封闭 contextKind 枚举 sc / pa / upn / ssm / iam / ups / ca / saa |
| openamsm.nf.metrics.read | 3 | 全部 kind=observation、effect=READ；共用 metrics-page-query 与 metrics-page Schema | 一个公开 Callable；Input 增加封闭 resourceKind 枚举 amf.ue-info / amf.gnb-info / smf.pdu-info |
| **Codec READ（ID 由 Provider 发布）** | **现有 v1.2.0 未发布** | PR #39 仅为内部 Codec 候选库/Worker，不等于 Interface Package | **一个独立 Capability 对应唯一 READ Callable**；0xD1 首批候选、0xC9/NGAP 均需各自资格化 Profile 与封闭 Result Schema |

第一组当前 backendOperationId 分别为 sc.query、pa.query、upn.query、ssm.query、iam.query、ups.query、ca.query、saa.query；第二组为 amf.ue-info.list、amf.gnb-info.list、smf.pdu-info.list。它们保留为 Provider 私有 backend 路由，不再作为 11 个 Skill-facing Callable。两个历史查询 Capability 各收敛为一个公开 Callable，另增加独立 Codec READ Capability/唯一 Callable，**Provider 新目标合计 3/3**。Callable ID、Codec Schema、slot/mediaType、Profile、handler 和包版本均必须由 ca-client-tools Publisher 正式冻结，不得根据 Capability 名称推造 callableId，也不得从当前 0xD1 库向量推断 0xC9/NGAP 合格。

封闭 selector 是 Callable Input Schema 的业务参数，不是 Callable 选择器。未知 selector、缺失 selector、跨组 selector 或 Schema 不匹配均在 Provider 调用前拒绝。不得使用任意字符串、动态 URL/path/header 或 Provider catalog 扩权。

### 12.3.1 Codec Capability 公开边界

SR-026 在两个通用 READ Capability 之外新增一个 Codec Capability / Callable，首批仅发布 NAS Decode 的已冻结消息子集。Provider 新公开面为两个通用 READ 1:1 加一个 Codec 1:1，合计 **3 Capability / 3 Callable**。若 Publisher 拆包，跨包合计仍须 3/3，Codec 自身必须 1/1。不得把两个通用 READ 的 2/2 误报为包含 Codec 的最终总数。Codec Capability ID、Input / Output Schema、支持消息子集和 Package 归属由 SR-026 / Publisher 在发布前冻结；不得沿用旧 11 个 READ Callable 作为新 Codec 接口。

### 12.4 Provider / Owner Package 的职责

- Owner CapabilityContracts 定义 Skill-facing Capability 与 Owner ToolCatalog Callable 的唯一关系；ToolCatalog 继续定义 Callable kind、Effect、Schema、Outcome、Receipt、Commit Proof、Evidence 和 Reconcile。
- Provider Interface Package 的 capabilities.json 定义 Provider 自身公开 Capability；tool-catalog.yaml 定义一个 Capability 对应的公开 Callable；Provider Runtime Bindings 将该 Callable 映射到一个或多个私有 backendOperationId。
- backendOperationId 可多对一地服务一个公开 Callable；公开 Callable 不得被多个 Capability 共享。
- Package 版本、Owner publication identity 和 Provider deployment pin 继续按既有 Package / sidecar 规则固定；不增加额外包级 hash、签名或 Trust Registry。

### 12.5 Compiler Link 与 Runtime Artifact

1.6.0 Contract.capabilities 只列 Capability ID；Procedure 使用 operation.capability / observation.capability。Compiler 在已声明依赖闭包中唯一解析 Capability，并依次验证 Grant、Capability→Callable cardinality、Callable→Capability cardinality、Owner / Package identity、kind、Effect、Input/Output Schema、Evidence 与既有 Scope 来源规则。

新版 Runtime Artifact v2 候选增加每个 Skill 的 capabilityBindings[]，每项至少记录 capabilityId、dependencyId、stablePackageId、Owner/Publisher identity、callableId、kind、effect、inputSchemaRef 和 outputSchemaRef。Procedure 编译节点保留 capabilityId；Artifact dependencyClosure.exports[] 仍输出精确 Callable exports，供 Runtime 建立 Callable allowlist。Callable ID 是 Artifact 的内部 Binding 数据，不是模型可选择的 Action 参数。

稳定诊断至少覆盖 CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH 和 CAPABILITY_BINDING_MISSING。任何链接失败都不得产生部分 Artifact。

### 12.6 Runtime Action 与 Reconcile

Runtime Action 以 Capability ID 为 Skill / Procedure 作者侧入口。Runtime 从当前 Artifact 的唯一 capabilityBindings 项解析 Callable ID，按现有精确 Callable allowlist、Schema、Effect、Run 状态和 Owner identity 检查后，在 Host / Plugin Manager 内部派发。模型不能提交或替换 Callable ID，也不能枚举 Provider backendOperationId。

普通 Skill / LLM Action 对 MAS.RECONCILE 必须在 Provider IPC 前拒绝，诊断 INTERNAL_RECONCILE_ONLY，Provider IPC 次数为零。Runtime Coordinator 只能使用原 Mutation Invocation / Scope / Correlation 的专用入口。Receipt Query 不适用此 Reconcile 排除规则。

### 12.7 版本边界

- CA-SL v1alpha5 与 Compiler v2.1.0 已发布语义和字节完全冻结；其中 tool: alias::Callable 的历史语义不变。
- CA-SL 1.6.0 是 Capability-first 唯一目标作者版本候选，尚未由 ca-skills 发布。
- Compiler Artifact API / BuildResult API 的新版本候选仍是 connectionagent.io/compiler-artifact/2 与 connectionagent.io/compiler-build-result/2；其 languageTarget 候选为 connectionagent.io/v1.6.0，并承载 Request Schema、when 和 capabilityBindings。正式发布前由 ca-skills / Compiler 在 Schema / Golden 中共同确认。
- 不提供 v1alpha5 / 1.6.0 双语法兼容、自动迁移、旧 Artifact 回退或 Development Artifact 运行时回退。Development v1alpha1 继续 NOT_ADMITTED。
- 本设计不修改任何下游仓；各仓实现必须由后续目标仓 SR 单独授权。

**1.6.0-only 设计评审硬门槛：** 旧 Owner/Provider Release 只是基数审计输入，必须按 1.6.0 新契约重新发布。 此章节仅描述目标设计，外部代码/Release/E2E 均 NOT_RUN。


### 12.8 新版公开能力拒绝矩阵

| 输入类别 | 唯一 1.6.0 行为 |
|---|---|
| 合法 1:1 Capability / Callable，kind/Effect/Schema 匹配 | Compiler 构建唯一 Binding，Runtime 经 Artifact Scope 分发内部 Callable |
| 旧 Owner 24 IDs/25 members（两个 Event Callable 共用一个 Capability） | 拒绝该旧一对二导出；Owner 必须拆分事件并对两个 Parser 分别签认，最终数量按 22/22、23/23、24/24 条件推导；未签认不得发布，不要求固定 24/24 |
| 旧 Provider 2 Capability/11 READ Callable | 拒绝作为新版公开面；新 Provider 目标为两个通用 READ 1:1 加一个 Codec 1:1，合计 3/3；两个 READ 使用封闭 contextKind/resourceKind selector |
| 旧 v1alpha5 Alias::Callable、Artifact、旧 Development 1.0.0 ZIP | 新 Authoring/Compiler/Agent/Studio 都拒绝，不转换、不 fallback |
| 模型指定 Callable/backendOperationId/URL 或自由文本 selector | IPC 前拒绝；Provider 只能用 Schema 闭合路由私有 handler |
| Skill/LLM 直接调用 internal-only MAS.RECONCILE | `INTERNAL_RECONCILE_ONLY`、IPC=0；Coordinator 仅按原 Mutation Reconcile |

### 12.6 OpenAMSM 原版 OpenAPI 3.0 直接消费与 Codec READ Output 隔离（IR-009）

- **标准来源**：ca-skills SR-031 原样代发布 OpenAMSM 实际支持的 OpenAPI 3.0 YAML Source Bundle；原始 bytes、相对路径和 `$ref` 不改。当前 `PostSmContexts.requestBody → multipart/related → jsonData → SmContextCreateData` 的可达闭包为四份原版 YAML / 102 个 Schema Component；只锁定选定根可达的跨文件 refs，不要求全目录 472 份 YAML。Source Bundle 不是 Interface Package，不导出 Capability / Callable。
- **原生消费**：Plugin / SR-010 按 OAS 3.0 解析选定 operation / requestBody / multipart / JSON / binary parts / media type / Content-ID；仅 lazy resolve 选定 surface 的 refs，不 eager resolve 未选定 operation。CommonData `RefToBinaryData.contentId` 必须精确关联 `n1SmMsg`→N1、`n2SmInfo`→N2、`n2SmInfoExt1`→N2 Ext1 的对应 part；Content-ID 重复、引用目标缺失、错槽或媒体类型不符均拒绝。未被 JSON 引用的 part 不得交给 Codec；额外或未引用 part 的拒绝 / 忽略由 ingress profile 明确规定。Compiler / SR-013 对显式 pin 的 Source Bundle 中 `components/schemas` 直接引用，使用 dialect-aware Resolver。相对 `$ref` 按 RFC 3986、fragment 按 RFC 6901 解析；允许规范化后仍在 Source Root 内的 `../`，拒绝逃出 Source Root。CA-SL 本地 G.4 不因外部 OAS3 引用而放宽；外部 OAS3 Schema Object 不做 Adapter / projection。
- **真正解码输出**：ca-client-tools / SR-026 拥有 Codec Tool Interface READ Capability ↔ 唯一 Callable 与正式 Output Schema；按与 OpenAMSM 支持基线一致的 NAS/NGAP Profile、授权 artifactRef/slot 返回结构化字段。TS 29.502 `format: binary` 与 MIME Content-ID 只定义传输和 part 关联，不能推断 NAS/NGAP Result Schema。首批仅 0xD1，Create / Modify / N2 需单独资格化；一个 Capability 覆盖多 Profile 时必须用 Golden 证明固定 selector 与单一 Output Schema 完整封闭且保持 1:1。
- **运行时**：T1 仅 Plugin Event / Skill-owned Request；T2 由已选 Procedure 经统一 Action Boundary / 唯一 Plugin Manager 使用 Codec READ，原 bytes 保留；Codec Result 不等于 Owner Receipt / Commit Proof。无 Codec 需求时 zero Codec IPC；需要但无发布时对应 AC BLOCKED。
- **基数**：Provider 查询 2/2 + 首批 Codec READ 1/1 = 3/3；Source Bundle 不计 Capability。实际 Package / Schema IDs、SemVer、handler、Golden 和正式 OpenAMSM source lock 未正式确认，产品 NOT_RELEASED / NOT_RUN。

[权威设计](../EC01-3GPP公共Schema/3GPP公共Schema发布与Skill分阶段消费设计说明书.md)。

### 12.7 Demo no-hash Artifact / Provider 边界（强制）

- Next Demo 不计算、不传输、不比较 SHA-256、checksum、digest 或 content-addressed identity；不实现签名、Trust Registry、生产级准入或供应链完整性门禁。
- `provider.yaml` / sidecar / Owner publication / Provider initialize 中的 `interfaceSnapshotDigest`、`runtimeBindingsDigest`、`backendCatalogDigest`、`publicationDigest`、`manifestDigest`、`buildDigest` 等若由上游携带，仅作为声明或诊断元数据，不由 Next 重新计算、比较或作为加载条件。
- Provider 包加载仍须检查路径在包根内、文件存在、YAML/schema 结构、Provider/Owner identity、版本、公开映射、Effect、Schema 闭包和显式 catalog 完整性；这些结构/语义校验不依赖 hash。
- Provider 发布物按精确 Release tag 和平台归档选择；Demo 不校验 `SHA256SUMS`、归档 checksum 或 executable digest。该约束不等于允许动态 latest 或任意路径执行。
- Host Artifact Channel 只管理 opaque reference、Invocation/direction/slot、原始 bytes、大小/数量配额、超时取消、过期清理和原子发布；不做 per-artifact SHA-256。外部 `ca-host.artifact-store/v1` 若强制 SHA-256，则与 Next Demo 不兼容，AC-010-03 保持 BLOCKED_EXTERNAL_INPUT，直至外部契约修订。
- 上游 Git blob ID 可作为 Source Bundle 原始 Git 对象身份；它不是 Next 计算的 digest，也不得转化为产品 Build / Verify hash 门禁。Source Bundle 的 byte-for-byte 比较是直接字节比较。
## 13. 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Tool Interface、Owner Contract、Provider Runtime Bindings 与唯一 Plugin Manager 的集成设计基线 | 将 EC03 原始设计资产映射到 F03.05，并基于 ca-agent-demo main 进行选择性复用审计 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | §4、§6、§7、§11 | 补齐 Provider v2 wire contract、Runtime Bindings、内部 Backend Catalog 与 11/25/31/44 库存闭合 | 按 ca-client-tools v1.2.0 源码和 Owner v1alpha4 生成器核对实际映射，避免混淆公开/私有 Callable 数量 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | §1～7、§11 | 区分 Provider Interface Package 与 Owner Contract dependency snapshot，补齐 CA-SL v1alpha5 `mas` alias 和冻结 Compiler Owner Link 路径 | 依据 ca-skills main MAS 作者源、Compiler v2.1.0 v1alpha5 API 与 env-openamsm Owner v1alpha4 publication 交叉核对，修正把 Owner Callable 误归到 Provider Interface Package 的歧义 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.1 | GPT-6.2（ChatGPT） | §1、§4、§6、§7 | 明确冻结 v1alpha5 Artifact dependencyClosure 不含 snapshotDigest；将 Owner version/publication/manifest digest 绑定定位到 Provider sidecar 与部署配置 | 防止把 Development v1alpha1 Lock 能力误认为 Agent 当前运行期能力，并记录 per-Skill pin 的未来边界 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.2 | GPT-6.2（ChatGPT） | §1、§4、§6、§7 | 补齐 provider.yaml 的 interfaceSnapshotDigest、runtimeBindingsDigest、公开→私有映射与 initialize/catalog digest 对账；明确 Provider Interface 与 Owner 的双部署 pin | 闭合 Provider package 实际发布结构与冻结 Artifact dependencyClosure 限制，依据 v1.2.0 Go generator 和 Runtime Bindings v1 contract | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.3 | GPT-6.2（ChatGPT） | §4.2、§6.5～§7.4 | 校正 Receipt Query 与 Reconcile 两个 Owner evidence operation 的 Skill 可见边界；Receipt Query 是受 Scope 约束的 READ Callable，Reconcile 是专用 target | 对齐 Compiler v1alpha5 Owner Link 对 dedicated Reconcile 的实际限制，避免将两者错误地一概视为不可调用 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.3.4 | GPT-6.2（ChatGPT） | §11 | 增加 Next 侧逻辑模块分解、输入/输出边界和最小自动化验收矩阵 | 使后续代码 SR 可直接按 Loader、Driver、Resolver、Action Boundary、Outcome/Reconcile、Artifact Adapter 和单一 Manager 分解实施 | IR-006 · SR-015 · Issue #12 |
| 2026-11-27 | 0.4.4 | Codex / GPT-6 | §1、4、6、7、11 | 移除 Callable-only Resolver 的现行指令，统一按 1.6.0 编译绑定派发 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-25 | 0.3.5 | GPT-6.2（ChatGPT） | §4.4 | 区分冻结 v1alpha5 Runtime Owner Contract 与 Compiler v2.1.0 Development Interface Package；将 MAS Owner Publisher 实施责任链接到 SR-025，并记录 package/source version 的 SemVer 决策门槛 | 防止把 Owner Contract、Provider Interface Package 和 Development wrapper 混为同一发布面 | Issue #12；F09 v0.3.5；SR-015；SR-025 |
| 2026-11-25 | 0.3.6 | Codex / GPT-6 | 正文 | 同步 Publisher 身份、版本和验收边界 | 消除执行歧义并同步中央设计 | Issue #12 |
| 2026-11-26 | 0.3.7 | Codex / GPT-6 | §4、§6、§8、§12 | 校正装载顺序、catalog 分区与 initialize 失败语义；补齐 ca-client-tools 两端及 Codec 发布归属 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.3.8 | GPT-6.2（ChatGPT） | §2～§8、§11 | 将 PR #13 已完成的 P1/P2 修正移植到当前恢复基线；明确 frozen v1alpha5 Capability 不序列化、Reconcile internal-only、完整 Interface tree 路径校验、安装级 Loader 与 per-Skill Resolver 分离；复用 v1.2.0 pinned Release `SHA256SUMS` 与 Host executable digest 对账；固定 Artifact Store 来源和 Host-owned ToolCatalog 不采用 | 防止设计版本倒挂，并让 F03.05 与 F02/F04/F06/公共契约使用同一执行边界 | IR-006 · SR-015 · Issue #12 |
| 2026-11-26 | 0.3.9 | GPT-6.2（ChatGPT） | 文档头、修订记录 | 回填 SR-015 设计迁移 PR #37 已合并到恢复分支 | 仅更新设计资产集成状态，不将 F03 Provider Runtime 或 Codec Consumer 误报为已实现 | Issue #12；SR-015；PR #37 |
| 2026-11-26 | 0.4.0 | GPT-6（ChatGPT） | 新增 1.6.0 目标章节、状态及修订记录 | 移植一对一 Binding / Selector / Action 设计并标为待评审 | 无旧版兼容或产品完成承诺 | Issue #40；SR-029 |
| 2026-11-27 | 0.4.1 | GPT-6.2（ChatGPT） | §1、§12、修订记录 | 明确 1.6.0 Skill 作者源只声明 Capability ID；Callable ID 仅作为编译后的内部 Binding 与运行时 dispatch 身份。 | 消除概述层“Capability / Callable”并列作者声明与 1.6.0 Capability-only 作者接口之间的歧义。 | Issue #40；SR-029；F04；F06 |
| 2026-11-27 | 0.4.2 | GPT-6.2（ChatGPT） | §10、§12、修订记录 | 将复用代码表中的 Capability→Operation 关系和 Operation allowlist 标记为历史机制，目标语义改为 Capability↔Callable 1:1 与 Callable allowlist | 防止旧 Demo 实现关系被误认为 1.6.0 规范要求 | Issue #40；SR-029；PR #45 |
| 2026-11-27 | 0.4.3 | GPT-6.2（ChatGPT） | §5、修订记录 | 将 CA-SL 1.6.0 Skill Author Source 与 Compiled Skill Artifact 分列：作者源仅声明 Capability ID，Artifact 保存 Compiler 生成的唯一 Capability→Callable Binding | 消除把 Capability / Callable 并列描述为作者依赖的歧义，保持 Callable 仅作为编译产物内部与 Runtime dispatch 身份 | Issue #40；SR-029；PR #45 |
| 2026-11-27 | 0.4.4 | GPT-6.2（ChatGPT） | F03.05 §5 | 分列历史 v1alpha5 Compiler 职责与 CA-SL 1.6.0 Compiler 目标职责，消除组件表版本混用。 | 明确历史实现与新目标模型边界，避免将旧 resolved dependency snapshots / Owner bindings 误读为 1.6.0 职责。 | Issue #40/#62；PR #45 |
| 2026-11-28 | 0.4.5 | GPT-6（ChatGPT） | §8.3 | 固定 3/3 Codec Provider 目标、READ 不等于纯业务 Parser 的源证据、Owner 两种条件基数与 T1/T2 限界 | 消除第六轮 P1-01 的 Provider/Owner 责任混合与隐式 fallback | Issue #40/#113；PR #45；SR-026/029；F06 |
| 2026-11-28 | 0.4.6 | GPT-6（ChatGPT） | §12.2～12.3 | 将基数表和正文同步为 Codec Provider 3/3、Owner 22/22 或 24/24 的条件目标，明确发布者未冻结身份/Schema | 消除正文 §12 与新增 §8.3 口径冲突，避免第七轮再次出现 2/2 旧目标 | Issue #40/#113；PR #45；SR-026/029 |
| 2026-11-26 | 0.4.1 | GPT-6（ChatGPT） | §1、§3～§4、§12 | 规范性目标限定 Capability-only；旧 Publisher 24:25/11 READ 降为审计，新增拒绝矩阵 | 解除新旧 Callable/Owner/Provider Published Package 混淆 | Issue #12/#40；SR-025/026/029；PR #46 |
| 2026-11-26 | 0.4.2 | GPT-6（ChatGPT） | 1.6.0 Capability / Codec 目标 | 修正 Skill 仅声明 Capability，补齐 Codec 第三个 1:1 公开能力并区分历史 Provider 2/11 | 修正历史 Callable-only 描述和 Provider 能力基数遗漏 | Issue #12/#40；SR-025/026/030 |
| 2026-11-27 | 0.4.3 | Codex / GPT-6 | Provider 一对一映射 | 区分查询 2/2 与包含 Codec 的 3/3 | 与 SR-029、F06 的发布范围对齐 | Issue #12，PR #46 |
| 2026-11-28 | 0.4.7 | GPT-6（ChatGPT） | §2、§5、§12 与修订记录 | 整合 #45 公开 Callable 的唯一 Binding、Skill 作者源与编译 Artifact 分层、#46 Provider/Codec 封闭路由；保留历史发布只读 | 不将公开 Tool 误作内部分发身份，维持 1.6.0-only | Issue #12；#40；PR #45；#46 |
| 2026-11-28 | 0.4.8 | GPT-6（ChatGPT） | §4.4、§8.3、§12.2、§12.8、修订记录 | 将 Owner Parser 数量从固定 24/24 改为逐项签认矩阵，补齐混合裁决与未签认阻断 | 避免合法 Owner Package 因固定成员数被误拒，并确保 Compiler 只接受 Owner 冻结的实际 1:1 成员 | Issue #12；SR-025；PR #46；Review #6095143611 |
| 2026-11-28 | 0.4.9 | GLM-5.3（DeepSeek Harness） | 修订记录 | 合并被空行拆断的孤儿修订表段为单一连续表格，不改变任何历史行内容 | 修复 R8-09 同类 Markdown 渲染断裂，保证修订数据完整可见 | Issue #12；PR #46；Review #6095143611 |
| 2026-11-28 | 0.4.12 | GPT-6.2（ChatGPT） | §8.1～8.3、修订记录 | 收编 SR-026 Codec 公开 READ 的固定 Capability/Callable/Package 2.0.0 契约，并改用 no-hash Artifact Channel v2 | 将 Codec 生产接口从候选转为中央固定设计，同时消除 v1 SHA-256 与 Demo 限制冲突 | Issue #113；SR-026；SR-010；F05；SR-029；PR #115 |
