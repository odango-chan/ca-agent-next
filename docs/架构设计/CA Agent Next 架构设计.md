# CA Agent Next 架构设计

> 文档类型：总体架构设计\
> 状态：目标架构基线；SR-002 Python Host/Model Loop 最小切片 VERIFIED；SR-003 v0.3.11 VERIFIED（模块 AC-003-01～04）；PR #34/#41/#42 已合入恢复分支，双平台 CI SUCCESS；系统 EX-02/03/04/18 未完成；CA-SL 1.6.0 Capability-first 架构增量待评审，产品未发布
> 文档版本：0.4.16
> 修订日期：2026-11-28
> 适用范围：ca-agent-next 通用 Agent Core、Host、Runtime、Skill 与 Plugin 公共机制\
> 权威边界：本文是本仓唯一总体架构文档；字段级契约见规范，机制细节见设计说明书\
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展

关联需求项见 [IR-002](../IR/IR%20总登记册.md#ir-002)、[IR-003](../IR/IR%20总登记册.md#ir-003)、[IR-004](../IR/IR%20总登记册.md#ir-004)、[IR-005](../IR/IR%20总登记册.md#ir-005)。

## 1. 架构目标

CA Agent Next 是一个通用 Agent。Agent Core 不内置 OpenAMSM、5GC 或其他业务的专用路由、业务枚举、业务 Schema、Owner 操作和业务状态机。新增业务应通过引入 Skill、Plugin、Tool Interface Package 和部署配置完成，不要求修改 Agent Core。

本阶段以 Demo 原型验证：Python Agent Core 能先选择并绑定 Skill 再执行；唯一 Plugin Manager 管理独立进程 Plugin，并统一分发 Event ingress、Tool invocation 和 Event delivery；可选 Assurance 提供确定性执行能力；Deterministic 与 LLM-guided 共享 Runtime Action Boundary；SBI 可携带 JSON 与二进制；Echo 通过后，OpenAMSM 作为第二个业务接入而不增加 Core 业务分支。

## 2. 范围与非目标

### 2.1 本阶段范围

- Python Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime。
- 唯一 Plugin Manager、Plugin Package、统一 IPC 与 Extension 分发。
- Skill 包结构、可选 Assurance、已发布 Artifact 消费、SkillCatalog 和 Skill 选择。
- 统一 Action Boundary、Run、Context、Outcome/Evidence 和 Wait/Resume。
- Host-owned Artifact Handoff、SBI JSON/multipart 接入和按需 Codec Tool。
- Echo 第一垂直示例，随后接入 OpenAMSM。

### 2.2 非目标

本阶段不是生产平台，不做生产级 HA/DR、SLA、容量规划、多地域部署、复杂多租户治理、Marketplace、自动安装器、自动下载、通用热更新或分布式 Event Bus。

安全与可靠性 DFX 暂按 Demo 场景处理，不建设生产级安全信任体系、签名、Trust Registry、密钥管理或复杂容灾机制。但基本输入/Schema/版本/路径校验、明确错误、fail-closed、最小可观测性和自动化测试属于功能正确性，不能省略。

不实现 CA-SL 第二套语言解析器，不做旧版兼容或自动迁移，不复制 Compiler、Tool Plugin 或业务 Skill 的实现。

### 2.3 评审范围继承

本文继承 Agent.md 中的项目级 review_scope，不重复维护另一份范围清单。评审必须严格检查本节声明的 Demo 核心机制和基本正确性；对全局范围明确排除的生产级能力，不得因缺失而阻塞当前交付。如果认为某项非目标是当前目标成立的必要条件，按统一评审规范标记 SCOPE_DECISION_REQUIRED，等待用户决策。

## 3. 仓库职责与语言边界

| 仓库 / 域 | 实现与发布职责 | Next 的使用方式 |
|---|---|---|
| ca-agent-next | 新一代 Agent Core、Python Host、Runtime 和公共机制 | 唯一中央设计/治理仓；Python 新实现 |
| ca-agent-demo / REF01 | 既有 Python Generic Host、Context、ArtifactStore、Provider 和 Development 测试证据 | 逐文件审计、选择性复用；不整仓复制 |
| ca-runtime / REF02 | Go Runtime Host、Procedure、Provider、Predicate、Observation 参考 | 语义/实现对照，不是 Next 运行时 |
| ca-agent / TARGET01 | Go Native Host、ProductTask、Artifact Store 和 Host Contract | 后续晋级目标，不作为本次 Python 重构源码 |
| ca-skills / EC01 | Agent Skills SKILL.md、CA-SL **1.6.0-only** 新 Assurance 作者规范与业务 Skill（历史 v1alpha5 仅归档） | 唯一新作者与 Bundle 发布输入；Agent 只消费正式 1.6.0 发布 Bundle |
| ca-skill-compiler / EC02 | CA-SL 检查、链接、Build、Verify 和 Artifact 发布 | 外部工具链；Next 不调用 Compiler |
| ca-client-tools / EC03 | Tool Interface Package、Provider v2、Runtime Bindings、SBI Client、Codec | 通过唯一 Plugin Manager 的 tools Extension 接入 |
| ca-openamsm-plugin / EC04 | OpenAMSM SBI Event ingress / Delivery | 独立 Go Event/Delivery Plugin |
| env-openamsm / EC05 | OpenAMSM MAS Owner、Receipt、Commit Proof、Reconcile 和业务状态 | Owner 权威；Next 消费，不复制 Owner 状态 |
| ca-skill-studio-demo / EC06 | Theia Browser、Package/Source-first、LSP、AI Authoring | Skill 作者工作台，不执行 Skill |
| env-5gc-sim / EC07 | 5GC reference simulator、Mock AMF SBI test peer | 独立测试对端；Mock AMF 不是 Owner |
| ai-gateway / ca-dsh / G01 | 模型服务网关和 DeepSeek Harness 执行环境 | 工程基础设施，不是 Agent Core/Runtime |

Agent Core、Host、Importer、Resolver 和 Runtime 使用 Python。独立 Plugin 可以使用 Go。Go Plugin 不意味着 Go Host，也不改变 Core 的语言决策。

**设计权威边界：** ca-agent-next 是项目群架构、设计、规范和 ADR 的唯一中央入口。外部实现仓继续维护源码、测试、发布、部署、运行和故障排查材料，并链接回本仓对应 Feature。迁入的原始资料必须保留 source repository、source path、fixed SHA 和 source status；历史提案不能伪装成当前目标设计。详细映射见[外部能力域架构总览](外部能力域架构总览.md)、[功能树](../治理/功能树与需求追踪基线.md)和[跨仓迁移审计](../参考与审计/跨仓设计资产迁移与一致性审计.md)。

## 4. 总体组件架构

~~~mermaid
flowchart TB
  EXT[外部系统 / 用户] --> EP[Event Plugin]
  EP --> PM[唯一 Plugin Manager]
  PM --> HOST[Python Host / Agent Core]
  HOST --> RES[Skill Resolver]
  RES --> CAT[Core-owned SkillCatalog]
  RES --> LOOP[LLM Model Loop]
  LOOP --> ACTION[统一 Runtime Action Boundary]
  PROC[Deterministic Procedure Engine] --> ACTION
  ACTION --> RT[Python Runtime]
  RT --> PM
  PM --> TP[Tool Plugin]
  TP --> OWNER[业务 Owner]
  OWNER --> TP
  TP --> RT
  RT --> HOST
  HOST --> DP[Event Delivery Extension]
  DP --> EXT
  PUB[外部 Skill 发布流程] --> ART[已发布 Skill Artifact]
  ART --> IMP[Skill Importer]
  IMP --> CAT
  HOST --> STORE[Run / Context / ArtifactStore]
~~~

该图表示逻辑责任边界，不代表所有组件必须部署为独立进程。Plugin 是独立进程；Host、Resolver、Runtime 和 Catalog 属于 Python Agent 运行时。Compiler/发布流程在 Agent 外部，不是 Agent 运行时组件。

## 5. 核心组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Host / Agent Core | 模型循环、Event 编排、Skill 选择协调、Context 组装、Run 生命周期和响应义务 | 直接绕过 Runtime 调用 Tool、决定 Owner 业务事实 |
| Skill Importer | 读取 SKILL.md 和已发布 Artifact，检查基本结构/必需文件/依赖，生成 Catalog 候选代际 | 调用 Compiler、Build/Verify、Skill Admission |
| SkillCatalog | 进程内 Skill 快照、缓存的 SKILL.md、候选元数据、已反序列化 when 程序和代际 | Plugin 生命周期、Tool 调度 |
| Skill Resolver | 精确 continuation 优先；对新 Event 评估 when 并完成候选选择 | 执行 Procedure 或直接调用 Tool |
| Runtime | Run 执行、Declared Callable Scope 检查、Action 分发、Outcome/Evidence、Wait/Resume/Reconcile | Compiler 调用、Skill Admission、生产级授权、LLM Model Loop、外部 SBI 协议解析 |
| Procedure Engine | 推进已发布 Artifact 中的确定性 Procedure 并提出 Action | 独立授权或直接调用 Plugin |
| Plugin Manager | Plugin 进程生命周期、握手、IPC、关联与 Extension 分发 | Skill 选择、Action 授权、Owner 结果判断 |
| Plugin | 实现声明的 Event、Delivery 或 Tool Extension | 选择 Skill、授予 Capability、改变 Owner 结果 |
| Owner | 权威业务状态、Receipt 和最终提交结果 | Agent 推理 |

## 6. Skill 模型与发布 Artifact

每个 Skill 必须包含 SKILL.md。作者源中的 assurance/ 是可选的：

| 发布包形态 | LLM-guided | Deterministic |
|---|---:|---:|
| 只有 SKILL.md，没有 Assurance Artifact | 支持 | 不支持 |
| SKILL.md + 有效已发布 Assurance Artifact | 支持 | 支持 |
| 包声明了 Assurance Artifact，但产物或必需文件缺失、格式不支持或依赖无法解析 | 导入失败 | 导入失败 |

没有 Assurance Artifact 时只能走 LLM-guided；有有效发布 Artifact 时可选择 Deterministic 或 LLM-guided；Artifact 存在但无效时整个 Skill 导入失败，禁止静默降级。

SKILL.md 是 Agent-facing 的自然语言指导。Procedure 是唯一确定性执行图。LLM 提出的单个 Action 不是 Skill 源码，不调用 Compiler，而是进入统一 Runtime Action Boundary。

## 7. Skill 导入与选择

Agent 只消费已发布 Skill 包，不负责从作者源构建 Artifact：

1. SKILL.md-only 包直接导入，不调用 Compiler。
2. 含已发布 Assurance Artifact 的包，执行基本结构、必需文件、格式、类型数据和依赖检查后导入。
3. 缺失文件、格式不支持、CEL/type data 损坏、路径不安全或 Tool/Capability 依赖无法解析时，导入失败；不得降级成 SKILL.md-only。

Agent 不调用 Compiler 的 Check/Build/Inspect/Verify，不实现独立 Skill Admission。发布前的 CA-SL 语法、类型、链接和 Artifact 完整验证属于外部 Compiler/发布流程。Agent 只做消费端必要的结构检查与依赖解析，不重复实现 Compiler 语义。

SkillCatalog 由 Core/Host 拥有，是进程内不可变快照。启动或显式导入/更新时读取 SKILL.md 和 Artifact 一次，反序列化已检查的 when 程序，构建新代际并在全部成功后原子激活。在途 Invocation 固定其开始时使用的 Catalog 代际。新 Event 每次用当前输入求值，不缓存上一个 Event 的布尔结果；references 和大型知识资产按需加载。

新 Event 的选择顺序：

1. 校验并去重 Event。
2. 精确 continuation 优先，恢复原 Run，不重新选择 Skill。
3. 固定当前 Catalog 代际。
4. 先以每个 Assurance Skill 声明的完整 requestSchema 校验规范化输入；失配时记录诊断并排除该 Skill。对合格且声明 when 的 Skill 使用发布 Artifact 中已检查的 CEL 程序求值。
5. 一个显式匹配直接选择；多个显式匹配只允许在精确匹配集合内消歧。
6. 没有显式匹配时，只对 SKILL.md-only 和已通过适用 Schema 校验且没有声明 when 的 Skill 使用 SKILL.md 语义选择。
7. when=false 或运行期错误的 Skill 不得重新进入无条件语义候选。
8. 无候选则澄清或拒绝，不允许无 Skill 绑定地回退到 Generic Agent。

when 是纯 CEL Skill 选择表达式，作者源位置为可选 Assurance 的 contract.yaml；predicates.yaml 只用于执行期业务判断。不新增 activation.yaml、constraint.yaml、独立 Package 或第二份 Contract。

### 7.1 标准 Request 与业务 Owner Contract 的分离

CA-Agent 优先消费已有的权威标准契约；标准未覆盖的业务语义由对应业务 Owner 定义自己的契约（例如 MAS Owner Contract Package）。二者可以在同一 Skill 中组合，但必须保留各自来源、Schema、版本和所有权。标准定义的协议字段及其语义不得被业务契约覆盖；当 3GPP SBI Request 触发 MAS 业务操作时，Request 仍是 3GPP 契约，MAS Contract 约束 Owner Capability / Callable 及其结果，Procedure 显式映射二者，不把 MAS 字段注入 3GPP JSON。

- 标准已定义的内容直接使用 OpenAMSM 实际支持版本对应的原版 OpenAPI 3.0 契约；不得复制、改写或投影原始 YAML。
- `PostSmContexts` 的选定消费面为 `requestBody → multipart/related → jsonData → SmContextCreateData`。Host 从规范化 Event payload 的 `request` 成员提取 jsonData 对象作为 Skill Request；若 `requestSchema` 直接引用 `SmContextCreateData`，CEL `input` 就是该对象根，`requestType` 路径为 `input.requestType`，不是 `input.request.requestType`，也不是完整 multipart envelope。
- N1/N2/N2 Ext1 bytes 保留为独立 Artifact slots。SBI JSON 直接按原版 OAS3 Schema 验证，不调用 Codec；只有 Skill 选定后，Procedure 确实需要 NAS/NGAP 内部字段时才调用已资格化 Codec READ。
- 如果入站接口没有适用的标准契约，则使用对应业务 Owner / Event Plugin 正式发布的领域 Request Schema。Owner Callable IO Schema 不自动成为 Event Request Schema；Owner 必须明确发布该输入 Schema 才可作为来源。
- 同一 Skill 同时引用标准 Request 与领域 Owner Contract 时，保持两套契约分离，并在 Procedure 中显式映射 Request 字段到 Capability arguments；不得扁平化、重命名或将领域字段伪装成标准字段。

**when 唯一入口**：有 Assurance 的 Skill 才能在 `assurance/contract.yaml` 声明可选顶层 `when`；SKILL.md YAML Front Matter 不声明 `when`，无 Assurance Skill 没有 Contract，不声明 `when`。`when` 只读取 Publisher 冻结的 `event.type` 与当前已验证 Request Schema 根对应的 `input`，不得读取 Context、Tool Result、Observation、Evidence 或 T2 Codec Result；`predicates.yaml` 只用于执行期业务判断。

### 7.2 Package 根目录共享资源与 Host-owned system Capability

Skill Package 的共享资源位于 Package 根目录，与可选的 `assurance/` 并列：

- `schemas/`：共享 YAML Schema 资源；
- `scripts/manifest.yaml` 与 `scripts/`：Script Registry 和登记源码；
- `references/`、`assets/`：参考资料与静态资源；
- `assurance/`：仅包含 `contract.yaml`、`procedure.yaml`、`predicates.yaml`，整体可选。

无 Assurance Package 仍可携带上述共享资源，按 LLM-guided Skill 导入，不调用 Compiler、不声明 Contract / `when`、不生成 Runtime Artifact。有 Assurance 时必须完整校验作者源并消费正式发布 Artifact；缺失或无效不得降级。根目录资源不得复制到 `assurance/`。

Host 提供两个 Host-owned system Capability，均通过现有唯一 Plugin Manager / Tools Extension 路径，不创建第二 Manager、Registry 或 IPC：

1. `host.skill-resource.read`：只读当前 Run 固定 Skill Package snapshot 中经登记的 UTF-8 文本资源，供 LLM / AI Authoring 按需读取 schemas、Script Registry、脚本源码和 references。必须校验相对包内路径与资源类型；不得读取其他 Skill / Run、宿主任意路径、包外资源或写入资源。读取不等于执行。
2. `host.skill-script.execute`：Host 按当前 Run 固定 Package Registry，以精确 `scriptId` 和 JSON `input` 执行已登记的 transform / predicate Script；LLM 与 Assurance 共用同一 Script Runner，不设置逐脚本 `llmInvocable` 标记或第二套 allowlist。模型不得提交代码、路径、命令或自定义入口。Predicate Script 被 LLM 直接调用时，其返回值不产生 Evidence 或 Assurance Outcome。

Script 只能进行纯本地计算，不访问网络、任意文件系统、子进程、环境秘密、时钟、随机数、动态加载、Tool / Capability 或外部副作用。Script 的 purpose 约束 Assurance 静态引用位置，不是 LLM 调用权限开关。具体 Registry、I/O Schema、Runner 与错误语义见 CA-SL 1.6.0、F03、F04、F05 和 SR-032。

## 8. Plugin 与 Tool 统一机制

全系统只有一个 Plugin Manager。Plugin 是独立包/进程和生命周期管理单元，可导出一种或多种 Extension：

- event.ingress：Plugin 向 Host 发布规范化 Event。
- event.delivery：Host 要求 Plugin 向原始协议通道交付响应。
- tools：Plugin 向 Host 暴露可调用 Tool Operation。

Tool 是 Plugin 的 Operation，不是独立进程、Manager 或 Runtime。Tool Plugin 是导出 tools Extension 的 Plugin。一个 Plugin 可以同时导出 Event、Delivery 和多个 Tool Operation。不得增加独立 Provider Manager、Tool Registry、Codec Manager 或第二条授权/分发路径。

Provider 自有 Tool 的公开 Callable、Schema、Effect 和 Capability 归 Provider Interface Package。MAS 等业务 Owner 的公开 Callable、Schema、Effect、Capability、权威业务结果、Receipt、Commit Proof 与 Reconcile 均归 Owner Contract；部署侧按已发布绑定交接 Artifact；Provider Runtime Bindings 映射 Provider 私有 Backend operation。三者边界见 [F03.05 Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) 和[公共契约与所有权规范](../规范/公共契约与所有权规范.md)。

Plugin Manifest 只声明进程和 Extension，不复制 Callable 定义。Provider v2 是 Provider 自身的进程协议，不是 Next Plugin IPC；唯一 Plugin Manager 通过 ProviderV2 Driver 适配它。

## 9. Runtime 与统一 Action Boundary

Deterministic Procedure Engine 和 LLM Model Loop 是两种 Action 提议来源，二者都必须经过同一个 Runtime Action Boundary。Runtime 在分发前检查 Run、选中 Skill 的声明 Callable Scope、Tool Schema、Effect、Artifact 引用和当前 Run 状态，再通过 Plugin Manager 调用 Tool。

这不是生产级 Skill Admission 或生产授权体系。Demo 只实现与当前 Skill/Tool 契约相符的基本调用范围检查。LLM 不得直接调用 Plugin、扩大 Skill 声明的调用范围、伪造 Observation/Evidence 或宣称 Owner mutation 已提交。

READ Tool 结果作为带来源的 Observation；MUTATION 结果依据 Owner Receipt/Commit Proof 判断。HTTP 200、IPC 成功或 Delivery 成功都不能替代 Owner 提交证明；UNKNOWN 必须保持 UNKNOWN。

## 10. SBI 二进制载荷与 Codec

SBI 不限于 JSON。Event Plugin 负责 HTTP/SBI 外层解析、JSON、multipart/related、Content-ID 关联和原始 N1/N2 字节提取；Host 管理本地 staging、ArtifactStore、opaque artifactRef、Run 关联和访问授权。原始字节不进入 NDJSON 帧或模型 Context。

必须区分两条二进制路径：

1. Event/Delivery Plugin ↔ Host：通过 Host 创建的本地 inbound/outbound staging directory 和相对 stagingPath 描述符交接。Host 校验 slot、路径边界和真实 byteLength，再导入 ArtifactStore。
2. Host/Runtime ↔ Tool Plugin：Tool 只能访问当前 Invocation 授权的 Artifact。其二进制传输依赖独立 Host Artifact Store Channel，不得使用 Event stagingPath，也不得把原始 bytes/Base64 塞进 NDJSON。

**当前限制：** `ca-host.artifact-store/v1` 已冻结（contract pin `2c0b07f`）并作为历史外部契约保留：ca-client-tools Provider v1.2.0 已实现 consumer 与共享 fixtures；ca-agent Go Host main `447d0cc` 的 P1 外部参考验收为 43/43（read-only 11/11），real-NF multipart 仍 NOT_VERIFIED；其逐 Artifact SHA-256 仅属历史传输校验。Next 1.6.0 的唯一目标为 `ca-host.artifact-store/v2`（no-hash：随机 opaque artifactRef、Invocation/direction/slot、mediaType/byteLength/配额、原子发布），不计算、不传输、不校验 SHA-256/checksum/digest，不提供 v1↔v2 兼容。Next Python Host 的 v2 channel server/adapter 尚未实现；在 SR-010 完成并通过共享 fixtures 前，所有 artifact-bearing Provider binding 必须 NOT_CONFIGURED，并在任何远端 I/O 前拒绝。不得自行发明 Provider 私有文件路径协议。

Codec 不作为 Agent Core 的内置能力。Skill 不需要协议内部字段时，直接把授权 artifactRef 交给业务 Tool；需要结构化字段时，按需调用 ca-client-tools tools Extension 中正式发布的 Codec Callable。Codec 解码结果不能替换原始字节。Event Plugin 只允许为共享 SBI Operation 提取最小必要 NAS discriminator 来规范化 Event，不承担完整协议解码或 Skill 选择。只声明实际发布和测试过的 NAS/NGAP 消息子集。

## 11. 关键端到端流程

~~~mermaid
sequenceDiagram
  participant X as 外部 SBI / 用户
  participant P as Event Plugin
  participant H as Python Host
  participant S as Skill Resolver
  participant R as Runtime
  participant M as Plugin Manager
  participant T as Tool Plugin
  participant O as Owner
  X->>P: Event / SBI 请求
  P->>M: 规范化 Event + Artifact 描述符
  M->>H: ingress.event
  H->>S: 校验 Event / 解析 continuation
  S->>S: 固定 Catalog 代际并选择 Skill
  S-->>H: 精确 Skill 绑定
  H->>R: 启动或恢复 Run
  R->>M: 已检查 Skill Callable Scope 的 Action
  M->>T: tools.invoke
  T->>O: Owner 操作
  O-->>T: 结果 / Receipt / Commit Proof
  T-->>M: tools.result
  M-->>R: Tool 结果
  R-->>H: Outcome / Evidence
  H->>M: delivery.dispatch
  M->>P: 响应交付
  P-->>X: SBI 响应
~~~

## 12. Demo 阶段的正确性与 DFX 边界

当前只要求 Demo 场景下的基本可运行性和机制正确性，不做生产级可靠性、安全和运维 DFX。仍必须满足：

- 输入、Schema、版本、Manifest 和路径错误明确失败。
- IPC 关联错误、Plugin 握手不匹配、Callable Scope 不匹配均 fail-closed。
- Owner Receipt/Commit Proof 语义不能被 HTTP 成功或传输成功替代。
- UNKNOWN 不得映射为 COMMITTED。
- 重复 Event、Continuation 和旧消息不得造成重复 mutation 或唤醒错误 Run。
- 每个新增外部可观察机制都有可运行 Example 和自动化 Acceptance。

## 13. 当前依赖与实施顺序

| 阶段 | 目标 | 当前状态 |
|---|---|---|
| A | Python Core / Host / Runtime 基础骨架 | PARTIAL（SR-002 VERIFIED；完整 Runtime 与 EX-01 未完成） |
| B | 唯一 Plugin Manager、Package/IPC | VERIFIED（模块 AC-003-01～04 PASS；系统 EX-02/03/04/18 NOT_RUN） |
| C | 已发布 Skill Artifact 消费与 SkillCatalog | NOT_STARTED |
| D | Skill Resolver 与执行模式派生 | NOT_STARTED |
| E | 统一 Runtime Action Boundary | NOT_STARTED |
| F | Echo 垂直 E2E | NOT_STARTED |
| G | OpenAMSM Plugin 与 Skill/Tool 集成 | Echo 通过后开始 |
| H | 真实 OpenAMSM Create → Modify → Release E2E | NOT_RUN |

外部依赖状态快照（截至 2026-11-27）：

- ca-skills main `780497a2918ad3e7bdff554ab64b0ba627e867e0`；PR #88/#89 MERGED，PR #87 OPEN；CA-SL v1alpha5 Release Record 固定规范提交 `18d8184367982ccbc835756136c4a53f9096c3a0`。
- ca-skill-compiler v2.1.0 已发布；旧 Issue #61 OPEN（仅 v1alpha5 历史范围）；CA-SL 1.6.0-only Compiler 新契约与 Runtime Artifact 由 [Issue #62](https://github.com/odango-chan/ca-skill-compiler/issues/62) OPEN 跟踪，尚未完成。
- ca-client-tools main `7bcb2614aa3615d8358df31eecefd0909e894e40`，Provider v1.2.0 RELEASED；PR #38/#39 OPEN；MAS Owner Publisher 由 SR-025 READY / [Issue #43](https://github.com/odango-chan/ca-client-tools/issues/43) 跟踪，尚未实施。
- env-openamsm PR #26/#27 已合并；MAS Owner v1alpha4 与 Receipt/Proof/Reconcile 已进入主线。
- env-5gc-sim PR #79 已合并；Mock AMF Modify 测试场景进入主线。
- ca-openamsm-plugin main 只有 README；PR #1 OPEN/Draft。
- ca-agent-demo main `25168db031e996bfa4de440c4156ae94f4e19bce`；PR #219/#253 MERGED；SR-024 VERIFIED、AC-024-01～07 PASS；Review COMMENTED、4 个 PR checks SKIPPED；Development 不等于 Production Qualification。
- ca-skill-studio-demo main `79bd2c3f64a90e7f0f169204c866a3218655bab1`；#267/#270/#272 MERGED（#272 merge `a8633553615d786e360a62c2b0042a27ae92d9d3`）；Issue #261/#269/#279/#290/#295 OPEN；#276 OPEN/DRAFT/DIRTY；#296 MERGED（`73523df2f7538ad51d37f1eaca2a40ab07c1e9a1`）；Pages 最新部署 SHA 未重新核验。
- ca-agent-next main `b2ed5eb84114f9c2556a0cd06ed974887b1b70ad` 未修改；PR #34 的 merge commit 为 `32c7c1be5e93bddc83349234476b2ffa09e1ca23`，PR #41 的 merge commit 为 `a899409ea7bf2ffde20ea2d62a9b4a310fb5638c`，PR #42 的 merge commit 为 `34e99e0cc54cc82b6b40040286fc84673432ef76`，该快照时 restore HEAD 为 `34e99e0`；PR #13 CLOSED/superseded。`32c7c1b` 是 PR #34 merge 和 restore↔refresh 分叉点，不是当前 restore HEAD。系统 EX 和 merge-commit post-merge exact verification 仍 NOT_RUN。

外部 Compiler/语言规范发布是 Agent 的外部依赖，不意味着 Next 需要集成 Compiler 命令。外部仓 PASS 不计入 Next PASS；实施前必须刷新准确 SHA、发布物、PR 和测试范围。

## 当前实现状态快照（2026-11-27）

- Phase A：SR-002 Python Host + Model Loop 最小切片 VERIFIED，AC-002-01～08 PASS；完整 Runtime、EX-01 和 CPython 全矩阵仍未完成。
- Phase B：SR-003 v0.3.11 VERIFIED（模块 AC-003-01～04）；PR #34 head `e8bcb1b` / merge `32c7c1b`，PR #41 head `f3f59b5` / merge `a899409`，PR #42 head `c573955` / merge `34e99e0`，均已合入 restore，且每组 Head/Merge tree 完全一致。Ubuntu/Python 3.12 与 Windows/Python 3.14 双平台模块 CI SUCCESS（87 Plugin / 52 Host / 80 Review Context tests）；当前 restore HEAD `34e99e0`。系统 EX-02/03/04/18 与 merge-commit post-merge exact verification 仍 NOT_RUN，Provider v2 wire DTO 与完整 Runtime E2E 由后续 SR 单独验收。
- Skill Studio：main `79bd2c3`；#267/#270/#272 MERGED（#272 merge `a863355`）；#261/#269/#279/#290/#295 OPEN，#276 OPEN/DRAFT/DIRTY；#296 MERGED（`73523df2f`）。默认 Host Context Example provenance 已实现；普通 ZIP 全局 provenance/reload 与双根正式包消费验收仍未完成。SR-024 VERIFIED，SR-025 READY / ca-client-tools #43 OPEN。
- CA-SL：v1alpha5 RELEASED，规范提交 `18d8184367982ccbc835756136c4a53f9096c3a0`；Compiler #61 仅跟踪 v1alpha5 历史范围；1.6.0-only 新 Runtime Artifact / Go-Python 产品互操作由 Compiler #62 OPEN 跟踪，尚未完成。
- 本架构描述目标与当前差异；外部仓 main/PR 状态不等于 Next 实现或系统 Acceptance。

### PR #54 评审快照（2026-11-27）

- 第二轮历史复评输入：Base `34e99e0cc54cc82b6b40040286fc84673432ef76`，Head `50a1c1496525c961b2ca6b1f9daaf2fb26ab3657`，`git merge-base(Base, Head)` 为 `34e99e0`；refresh 原分支为 `f63bbce2709284c97d8cd150343d491a3f2958db`，与 restore 的分叉点为 `32c7c1b`。该 Head 仅是第二轮历史评审输入。
- 第三轮当前复审与验证：Base `34e99e0cc54cc82b6b40040286fc84673432ef76`，Head `1f1234065be1f849dad2d17a91eaff986d384df5`；PR OPEN / Draft / MERGEABLE / CLEAN，16 files，未合并。GitHub Actions Run #319 (`45961614681`) SUCCESS，SR-001 回归 80/80、review_scope 机器校验 PASS；Artifact `review-context-pr-54-45961614681-1` 精确绑定该 Head。第三轮独立复审结论 `APPROVE_WITH_NON_BLOCKING_FOLLOWUPS`，仅保留 5 项 P3 非阻断 follow-ups。`git merge-base(Base, Head)` 为 `34e99e0`。
- GitHub Branch API 显示 main/restore/refresh `protected=false`，不应称为已启用分支保护；本任务仍禁止直接修改这些分支。

## 14. 详细设计与规范入口

- [F01 通用 Agent Core 与 Host](../设计说明书/F01-通用Agent核心与Host/通用Agent核心与Host设计说明书.md)
- [F02 Skill 管理与选择](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md)
- [F03 Plugin 平台](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md)
- [F03.05 Tool Interface 与 Provider 集成](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md)
- [F04 Runtime 执行](../设计说明书/F04-Runtime执行/Runtime执行设计说明书.md)
- [F05 Context 与 Artifact 管理](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md)
- [F06 业务接入与 OpenAMSM 集成](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md)
- [F08 技能编译与发布](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md)
- [F09 技能工作台与 AI 编写](../设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md)
- [外部能力域架构总览](外部能力域架构总览.md)
- [文档总目录与索引](../治理/文档总目录与索引.md)
- [功能树与需求追踪基线](../治理/功能树与需求追踪基线.md)
- [CA-SL v1alpha5 完整规范](../规范/CA-SL%20v1alpha5完整语言规范.md)
- [Plugin Package / IPC 规范](../规范/插件包与进程通信协议规范.md)
- [公共契约与所有权规范](../规范/公共契约与所有权规范.md)
- [演示验收基线](../验收与实施/演示验收基线.md)


## 15. CA-SL 1.6.0 Capability-first 总体架构约束（设计待评审）

新版本明确以 **CA-SL 1.6.0** 为**唯一新语言与运行输入**，不采用 v1alpha6 命名，也不兼容已冻结的 v1alpha5。该决策属于 [IR-008](../IR/IR%20总登记册.md#ir-008) / [SR-029](../SR/SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [Issue #40](https://github.com/odango-chan/ca-agent-next/issues/40)。

| 组件 | 1.6.0 唯一职责 | 不可跨越的边界 |
|---|---|---|
| ca-skills / EC01 | SKILL.md 使用 Agent Skills Specification；Assurance/Contract/Procedure 只出现 Capability ID，正式发布 1.6.0 Schema/机器标识和作者实例 | 不允许旧 Callable 作者语法或自动迁移 |
| Owner/Provider Package / F03.05 | Skill-facing Capability 与公开 Callable 双向一对一；两个 OpenAMSM 事件独立 Capability；Provider 封闭 selector 在内部路由 backendOperationId | 不以安装 Plugin 赋予 Grant；Reconcile 仅 Runtime internal-only |
| ca-skill-compiler / EC02 | 唯一 1.6.0 Parser/Linker/Check/Build/Verify；静态产生唯一 Capability→Callable Binding、Request Schema/when Runtime Artifact 和新 Build DTO | 不接受旧 v1alpha5 BuildRequest/Result、Artifact 或作者源；不在 Agent 内编译 |
| ca-skills 发布 / F08 | 重新编写/编译/验证 1.6.0 Skill，组装同语言版本的正式 Bundle | 不复用旧构建脚本作为 PASS，不发布部分成功批次 |
| Agent Importer/Catalog / F02 | 仅消费已发布 1.6.0 Assurance Bundle；Importer 返回候选，Catalog 原子激活；SKILL.md-only 仍可 LLM-guided | 无旧 Bundle 解析、混合 Catalog、fallback、自动转换或版本协商 |
| Runtime / F04 | 以 Capability 为作者侧 Action 入口，从 Artifact Binding 得到唯一 Callable，再执行 Scope/kind/Effect/Schema/Run 检查和 Plugin 分发 | 模型不可选择 Callable、backendOperationId 或 internal-only Reconcile |
| Skill Studio / F09 | Package Explorer 仅展示 Capability；LSP/AI Authoring 仅生成 1.6.0 Capability 作者字段 | 无平级 Tools/Operations 作者树、旧项目兼容或自动迁移 |

**当前阶段**：本新增章节及相关子架构**待独立评审**；1.6.0 正式语法、机器标识、Compiler API/Binding、Owner/Provider Package、Bundle、Studio 与 Agent/E2E 均未实施/发布。既有 SR-002/003 模块 VERIFIED 不构成 1.6.0 产品 PASS。

## 修订记录

| 日期 | 文档版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.2.0 | 历史修订者/模型未记录 | 第 1～14 章 | 既有总体架构基线；逐章历史记录未建立 | 原始修订者未记录，本轮不臆造 | PR #1 |
| 2026-11-25 | 0.2.1 | 历史修订者/模型未记录 | 范围与评审章节 | 增加全局评审范围继承规则 | 既有治理要求 | PR #1 |
| 2026-11-25 | 0.3.0 | GPT-6.2（ChatGPT） | 第 14～15 章 | 将设计入口改为功能文档，新增 F01/F06，统一功能树导航 | 以功能树作为架构到需求和详细设计的统一入口 | F01～F07；SR-001～SR-011；PR #1 |
| 2026-11-25 | 0.3.1 | 历史修订者/模型未记录 | 全文 | 刷新需求追踪、目录或证据引用 | 对齐当时分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.3.2 | Codex | §6 | 澄清已声明 Assurance Artifact 缺失的失败条件 | 对齐既有 Skill 导入规则 | SR-004；PR #1 |
| 2026-11-25 | 0.3.3 | Codex / GPT-6 | §3 | 提出集中设计与分仓交付边界 | IR-006 设计移交 | IR-006 |
| 2026-11-25 | 0.4.0 | GPT-6.2（ChatGPT） | §3、§8、§10、§13–14 | 纳入 EC01～EC07/REF/TARGET/G01 职责，补齐 F03.05、Artifact Channel 未发布边界、最新外部 PR/Release 状态和完整设计入口 | 纠正外部域遗漏、过期依赖快照和 Provider/Artifact 边界 | Issue #12；SR-015～SR-023 |
| 2026-11-25 | 0.4.1 | GPT-6.2（ChatGPT） | §10、外部依赖快照 | 纠正 Host Artifact Store Channel 生命周期；同步 Provider v1.2.0、Go Host P1 外部参考与 Next Python Host 未实现状态；区分 Mock AMF Codec C1 | 统一总体架构、F05、Plugin IPC 和验收基线中的协议状态 | Issue #12；SR-009、SR-010、SR-011、SR-015 |
| 2026-11-25 | 0.4.2 | Codex / GPT-6 | 正文 | §7 对齐 M.3 输入校验与候选排除顺序 | 消除执行歧义并同步中央设计 | Issue #12 |
| 2026-11-26 | 0.4.3 | Codex / GPT-6 | 见本行变更 | §Tool 更正业务公共契约所有权 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.4.4 | GPT-6.2（ChatGPT） | 文档头、§13～§14 | 更新 ca-skills、ca-client-tools、ca-agent-demo、Studio 与 Next 当前 main/PR 状态；记录 #34 MERGED 到恢复分支及 SR-025 READY/#43 OPEN | 避免将 PR 合并、模块 CI 和系统 EX 混为一谈；同步外部 Publisher 与 Studio 消费状态 | Issue #12；IR-006；SR-003、SR-016、SR-024、SR-025；ca-client-tools #43；Studio #269/#272/#276 |
| 2026-11-27 | 0.4.5 | GPT-6.2（ChatGPT） | 文档头、§13～§14 | 将 Studio main 更新为 `79bd2c3`；按 SR-003 v0.3.11 和 PR #41/#42 回填模块 VERIFIED 与双平台 CI，保留系统 EX NOT_RUN | 整合外部状态时保留恢复分支较新的模块验收结果，不将历史 IN_PROGRESS 快照带入当前架构状态 | Issue #53；Issue #12；SR-003、SR-016、SR-024、SR-025；PR #34/#41/#42；Studio #261/#269/#272/#276/#279/#290/#295 |
| 2026-11-27 | 0.4.6 | GPT-6.2（ChatGPT） | 文档头 | 将全局 review_scope 声明调整为仓库治理规范要求的唯一规范文本；局部非目标继续由独立章节承载 | 修复 Review Context 正式文档头检查失败，不改变总体架构语义 | Issue #53；PR #54 |
| 2026-11-27 | 0.4.7 | GPT-6.2（ChatGPT） | §13～§14 | 修正 Studio main 完整 SHA、#272 merge SHA 与 #296 merge 状态；明确 restore 当前 HEAD 和 PR #34/#41/#42 merge chain、PR #54 仅目标 restore | 避免把外部 main、PR merge SHA、PR head 和恢复分支 merge commit 混为同一身份 | Issue #53；Issue #12；PR #34/#41/#42/#54；Studio #261/#267/#269/#270/#272/#276/#279/#290/#295/#296 |
| 2026-11-27 | 0.4.8 | GPT-6.2（ChatGPT） | 外部依赖快照、当前实现状态快照、修订记录 | 区分 PR #34 merge 与当前 restore HEAD；补齐 PR #34/#41/#42 merge chain、SR-003 tree/测试证据和 PR #54 第二轮评审 Base/Head/merge-base；标注 main/restore/refresh 的 branch protection API 观察 | 防止将历史分叉点误作当前 HEAD，明确第二轮评审的固定基线及分支保护真实状态 | Issue #53；PR #34/#41/#42/#54；SR-003；restore 34e99e0；refresh f63bbce |
| 2026-11-27 | 0.4.9 | GPT-6.2（ChatGPT） | PR #54 当前快照、修订记录 | 区分第二轮复评历史 Head `50a1c149` 与修复后当前 Head `99a26c5`；记录 Run #312 SUCCESS、80/80 回归、review_scope PASS 和精确绑定当前 Head 的 Artifact | 防止继续引用已过期评审 Head；保留 PR OPEN/Draft、未合并和 restore/main 未修改的边界 | Issue #53；PR #54；Run #312；Artifact `review-context-pr-54-45959283144-1` |
| 2026-11-27 | 0.4.10 | GPT-6.2（ChatGPT） | PR #54 验证快照、修订记录 | 将 `99a26c5` 明确为 Run #312 的最近已验证检查点，而非随后版本指针同步提交后的当前 PR Head | 避免架构快照硬编码 PR 自身的过期 Head；当前 PR Head 始终以远端 PR #54 引用为准 | Issue #53；PR #54；Run #312；Artifact `review-context-pr-54-45959283144-1` |
| 2026-11-27 | 0.4.11 | GPT-6.2（ChatGPT） | 文档头、外部依赖快照、§13～§14、修订记录 | 修正外部依赖快照日期与 restore HEAD 时态；修复元数据块末行反斜杠；将 PR #54 历史评审与第三轮 Run #319/Artifact 当前验证信息移入评审快照小节 | 消除历史时点混杂、元数据字面反斜杠和导航章节错置；让当前验证证据精确绑定最终 Head | Issue #53；PR #54；R3-P3-01/02/05；Run #319；Artifact `review-context-pr-54-45961614681-1` |
| 2026-11-27 | 0.4.12 | GPT-6.2（ChatGPT） | 文档头、§15、修订记录 | 整合 1.6.0-only Capability-first 设计与最新恢复基线；设计待评审，实施/发布 NOT_RUN | 整合 PR #45 的 CA-SL 1.6.0 Capability-first 设计与恢复分支最新状态，避免回滚已合入的 #44 及后续基线。 | Issue #12/#40/#43；PR #44/#45 |
| 2026-11-27 | 0.4.13 | GPT-6.2（ChatGPT） | 总体架构外部依赖状态 | 更新 Compiler 跨仓状态，明确 #61 历史范围和 #62 的 1.6.0 新目标追踪。 | 使总体架构的外部依赖快照与新建的 1.6.0 实施 Issue 一致。 | Issue #40/#62；PR #45 |
| 2026-11-28 | 0.4.14 | GPT-6.2（ChatGPT） | §7.1、修订记录 | 加入标准契约优先与业务 Owner 契约补位；明确 3GPP Request 与 Owner Callable Contract 分离、jsonData Request 根和 `assurance/contract.yaml` 唯一 when 入口 | 防止领域字段污染标准请求、误把 Owner Callable IO 当 Event Request，或回退 Front Matter.when 旧方案 | Issue #47/#49；IR-009；SR-031/010/013/026；PR #48/#101/#115 |
| 2026-11-28 | 0.4.15 | GPT-6.2（ChatGPT） | §7.2、修订记录 | 补齐 Package 根目录共享资源、无 Assurance Package 与 Host Resource Read / Script Runner 的总体架构边界 | 使总体架构与 SR-032、CA-SL 1.6.0、F01～F05、F08/F09 作者体系一致，不把共享资源误归入 Assurance | Issue #49；IR-008；SR-004/007/032；PR #52/#115 |
| 2026-11-28 | 0.4.16 | DeepSeek Harness / deepseek-v4.1-flash-1017 | §10、修订记录 | 明确 ca-host.artifact-store/v1 仅为历史外部契约（SHA-256 非 Next 要求），Next 1.6.0 唯一目标为 v2 no-hash，并保持 v2 channel NOT_IMPLEMENTED/NOT_CONFIGURED 边界 | 消除总体架构“当前限制”仍把 v1 SHA-256 作为 Next 实现要求的 P1 冲突 | F05、SR-010；Issue #50；PR #115 |
