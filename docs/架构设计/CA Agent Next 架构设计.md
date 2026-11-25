# CA Agent Next 架构设计

> 文档类型：总体架构设计  
> 状态：目标架构基线，随 PR #1 评审；尚未实现、尚未验收  
> 修订日期：2026-11-25  
> 适用范围：ca-agent-next 通用 Agent Core、Host、Runtime、Skill 与 Plugin 公共机制  
> 权威边界：本文是本仓唯一总体架构文档；字段级契约见规范，机制细节见设计说明书

## 1. 架构目标

CA Agent Next 是一个通用 Agent。Agent Core 不内置 OpenAMSM、5GC 或其他业务的专用路由、业务枚举、业务 Schema、Owner 操作和业务状态机。新增业务应通过引入 Skill、Plugin、Tool Interface Package 和部署配置完成，不要求修改 Agent Core。

本阶段以 Demo 原型验证以下命题：

1. 一个 Python Agent Core 能够先选择并绑定 Skill，再执行该 Skill。
2. 一个统一 Plugin Manager 能管理独立进程 Plugin，并统一分发 Event ingress、Tool invocation 和 Event delivery。
3. 每个 Skill 都有 SKILL.md；可选 Assurance 决定是否具备确定性 Procedure 执行能力。
4. Deterministic 与 LLM-guided 两种模式共享同一个 Runtime Action Boundary。
5. SBI Event 可以携带 JSON 和二进制内容；Plugin 负责协议接入，Host 负责 Artifact 托管，Codec 按需作为 Tool 调用。
6. Echo 通过后，OpenAMSM 作为第二个独立业务接入，不需要增加 Core 业务分支。

## 2. 范围与非目标

### 2.1 本阶段范围

- Python Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime。
- 唯一 Plugin Manager、Plugin Package、统一 IPC 与 Extension 分发。
- Skill 包结构、可选 Assurance、SkillCatalog、Skill 选择与 Compiler 集成边界。
- 统一 Action Boundary、Run、Context、Outcome/Evidence 和 Wait/Resume。
- Host-owned Artifact Handoff、SBI JSON/multipart 接入和按需 Codec Tool。
- Echo 第一垂直示例，随后接入 OpenAMSM。

### 2.2 非目标

本阶段不是生产平台，不做生产级 HA/DR、SLA、容量规划、多地域部署、复杂多租户治理、Marketplace、自动安装器、自动下载、通用热更新或分布式 Event Bus。

安全与可靠性 DFX 暂按 Demo 场景处理，不建设生产级安全信任体系、签名、Trust Registry、密钥管理或复杂容灾机制。但基本输入/Schema/版本/路径校验、明确错误、fail-closed、最小可观测性和自动化测试属于功能正确性，不能省略。

不实现 CA-SL 第二套语言解析器，不做旧版兼容或自动迁移，不复制 Compiler、Tool Plugin 或业务 Skill 的实现。

## 3. 仓库职责与语言边界

| 仓库 | 权威职责 | Next 的使用方式 |
|---|---|---|
| ca-agent-next | 新一代 Agent Core、Host、Runtime 和公共机制 | Python 新实现 |
| ca-agent-demo | 既有 Python 实现、测试和复用证据 | 逐文件审计、选择性复用 |
| ca-agent | 当前稳定实现 | 后续晋级目标，不作为本次重构源码 |
| ca-skill-compiler | CA-SL 解析、静态检查、链接、Build、Inspect、Verify 和 Artifact | 调用正式发布的 CLI/API，不复制实现 |
| ca-skills | CA-SL 规范和业务 Skill 源 | 导入 Skill，不复制业务逻辑 |
| ca-client-tools | Tool 实现、Tool Interface Package 和 Owner 交互 | 作为导出 tools Extension 的 Plugin 接入 |
| ca-openamsm-plugin | OpenAMSM SBI Event ingress / Delivery | 作为独立 Event Plugin 接入 |

Agent Core、Host、Importer、Resolver 和 Runtime 使用 Python。独立 Plugin 可以使用 Go。Go Plugin 不意味着 Go Host，也不改变 Core 的语言决策。

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
  IMP[Skill Importer] --> CAT
  IMP --> COMP[CA-SL Compiler]
  COMP --> IMP
  HOST --> STORE[Run / Context / ArtifactStore]
~~~

该图表示逻辑责任边界，不代表所有组件必须部署为独立进程。Plugin 是独立进程；Host、Resolver、Runtime 和 Catalog 属于 Python Agent 运行时。

## 5. 核心组件职责

| 组件 | 负责 | 不负责 |
|---|---|---|
| Host / Agent Core | 模型循环、Event 编排、Skill 选择协调、Context 组装、Run 生命周期和响应义务 | 直接绕过 Runtime 调用 Tool、决定 Owner 业务事实 |
| Skill Importer | 识别 SKILL.md-only、Assurance 源码和已编译 Artifact；编排编译、验证与 Admission | 重写 CA-SL 编译语义 |
| SkillCatalog | 进程内 Skill 快照、缓存的 SKILL.md、候选元数据、已编译 when 程序和代际 | Plugin 生命周期、Tool 调度 |
| Skill Resolver | 精确 continuation 优先；对新 Event 评估 when 并完成候选选择 | 执行 Procedure 或直接调用 Tool |
| Runtime | Run 执行、Admission、Capability/Effect 校验、Action 分发、Outcome/Evidence、Wait/Resume/Reconcile | LLM Model Loop、外部 SBI 协议解析 |
| Procedure Engine | 推进已验证的 CA-SL Procedure 并提出 Action | 独立授权或直接调用 Plugin |
| Plugin Manager | Plugin 进程生命周期、握手、IPC、关联与 Extension 分发 | Skill 选择、Action 授权、Owner 结果判断 |
| Plugin | 实现声明的 Event、Delivery 或 Tool Extension | 选择 Skill、授予 Capability、改变 Owner 结果 |
| Owner | 权威业务状态、Receipt 和最终提交结果 | Agent 推理 |

## 6. Skill 模型与执行模式

每个 Skill 必须包含 SKILL.md。assurance/ 是可选目录：

| Skill 包形态 | LLM-guided | Deterministic |
|---|---:|---:|
| 只有 SKILL.md，没有 assurance/ | 支持 | 不支持 |
| SKILL.md + 有效 Assurance | 支持 | 支持 |
| SKILL.md + 已导入的有效编译 Artifact | 支持 | 支持 |
| assurance/ 存在但不完整或无效 | 导入失败 | 导入失败 |

Skill 选择先于执行模式选择。没有 Assurance 时只能走 LLM-guided；有有效 Assurance 时可选择 Deterministic 或 LLM-guided；Assurance 存在但无效时整个 Skill 导入失败，禁止静默降级。

SKILL.md 是 Agent-facing 的自然语言指导。Procedure 是唯一确定性执行图。LLM 提出的单个 Action 不是 Skill 源码，不调用 Compiler，而是进入统一 Runtime Action Boundary。

## 7. Skill 导入与选择

Importer 支持三种输入：

1. 只有 SKILL.md 的源码包：直接导入，不调用 Compiler。
2. 含 assurance/ 的源码包：自动调用 CA-SL Compiler，随后 Inspect/Verify 和 Host Admission。
3. 已编译 Skill Artifact：直接 Inspect/Verify 和 Host Admission，不重新 Build。

SkillCatalog 由 Core/Host 拥有，是进程内不可变快照。启动或显式导入/更新时读取包内容、编译 when、构建新代际并在全部成功后原子激活。在途 Invocation 固定其开始时使用的 Catalog 代际。新 Event 每次用当前输入求值，不缓存上一个 Event 的布尔结果；references 和大型知识资产按需加载。

新 Event 的选择顺序：

1. 校验并去重 Event。
2. 精确 continuation 优先，恢复原 Run，不重新选择 Skill。
3. 固定当前 Catalog 代际。
4. 对声明 assurance/contract.yaml.when 的 Skill，使用 Compiler 预编译的 CEL 程序评估当前 Event。
5. 一个显式匹配直接选择；多个显式匹配只允许在精确匹配集合内消歧。
6. 没有显式匹配时，只对没有声明 when 的 Skill 使用 SKILL.md 语义选择。
7. when=false 或运行期错误的 Skill 不得重新进入无条件语义候选。
8. 无候选则澄清或拒绝，不允许无 Skill 绑定地回退到 Generic Agent。

when 是纯 CEL Skill 选择表达式；predicates.yaml 只用于执行期业务判断。when 位于可选 Assurance 的 contract.yaml，不新增 activation.yaml、constraint.yaml、独立 Package 或第二份 Contract。

## 8. Plugin 与 Tool 统一机制

全系统只有一个 Plugin Manager。Plugin 是独立包/进程和生命周期管理单元，可导出一种或多种 Extension：

- event.ingress：Plugin 向 Host 发布规范化 Event。
- event.delivery：Host 要求 Plugin 向原始协议通道交付响应。
- tools：Plugin 向 Host 暴露可调用 Tool Operation。

Tool 是 Plugin 的 Operation，不是独立进程、Manager 或 Runtime。Tool Plugin 是导出 tools Extension 的 Plugin。一个 Plugin 可以同时导出 Event、Delivery 和多个 Tool Operation。不得增加独立 Provider Manager、Tool Registry、Codec Manager 或第二条授权/分发路径。

Tool 的 Callable ID、输入/输出 Schema、Effect、Capability 归属和 Owner outcome/receipt 语义，以其拥有者发布的 Tool Interface Package 为准。Plugin Manifest 只声明进程和 Extension，不复制 Tool 定义。

## 9. Runtime 与统一 Action Boundary

Deterministic Procedure Engine 和 LLM Model Loop 是两种 Action 提议来源，二者都必须经过同一个 Runtime Action Boundary。Runtime 在分发前校验 Run、Skill/Artifact Admission、Capability、Effect、输入 Schema、Artifact 引用和当前 Run 状态，再通过 Plugin Manager 调用 Tool。

LLM 不得直接调用 Plugin、扩大 Capability、伪造 Observation/Evidence 或宣称 Owner mutation 已提交。READ Tool 结果作为带来源的 Observation；MUTATION 结果依据 Owner Receipt/Commit Proof 判断。HTTP 200、IPC 成功或 Delivery 成功都不能替代 Owner 提交证明；UNKNOWN 必须保持 UNKNOWN。

## 10. SBI 二进制载荷与 Codec

SBI 不限于 JSON。Event Plugin 负责 HTTP/SBI 外层解析、JSON、multipart/related、Content-ID 关联和原始 N1/N2 字节提取；Host 管理 staging、ArtifactStore、opaque artifactRef、Run 关联和访问授权。原始字节不进入 NDJSON 帧或模型 Context。

Codec 不作为 Agent Core 的内置能力。Skill 不需要协议内部字段时，直接把原始 artifactRef 交给业务 Tool；需要结构化字段时，按需调用 ca-client-tools 的 tools Extension 中发布的 Codec Operation。Codec 解码结果不能替换原始字节。Event Plugin 只允许为共享 SBI Operation 提取最小必要 NAS discriminator 来规范化 Event，不承担完整协议解码或 Skill 选择。

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
  R->>M: 已授权的 Tool Action
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
- IPC 关联错误、Plugin 握手不匹配、Capability 不匹配均 fail-closed。
- Owner Receipt/Commit Proof 语义不能被 HTTP 成功或传输成功替代。
- UNKNOWN 不得映射为 COMMITTED。
- 重复 Event、Continuation 和旧消息不得造成重复 mutation 或唤醒错误 Run。
- 每个新增外部可观察机制都有可运行 Example 和自动化 Acceptance。

## 13. 当前依赖与实施顺序

| 阶段 | 目标 | 当前状态 |
|---|---|---|
| A | Python Core / Host / Runtime 基础骨架 | NOT_STARTED |
| B | 唯一 Plugin Manager、Package/IPC | NOT_STARTED |
| C | Skill Importer、Compiler 接口和 SkillCatalog | 外部 Compiler when 互操作待完成 |
| D | Skill Resolver 与执行模式派生 | NOT_STARTED |
| E | 统一 Runtime Action Boundary | NOT_STARTED |
| F | Echo 垂直 E2E | NOT_STARTED |
| G | OpenAMSM Plugin 与 Skill/Tool 集成 | Echo 通过后开始 |
| H | 真实 OpenAMSM Create → Modify → Release E2E | NOT_RUN |

当前依赖状态快照：ca-skills PR #88 仍需核对是否合并；ca-skill-compiler v2.1.0 尚未证明支持新 contract.when 和 Python CheckedExpr 互操作，Issue #61 跟踪 Development Artifact Manifest v1alpha2；ca-client-tools PR #39 的 Codec Consumer Migration 需按实际使用范围验收；ca-openamsm-plugin PR #1 为设计提案。所有状态在实施前必须重新核对，不得将旧快照当作当前事实。

## 14. 详细设计与规范入口

- [Plugin 管理与通信设计说明书](../设计说明书/Plugin%20管理与通信设计说明书.md)
- [Skill 导入、选择与 Compiler 集成设计说明书](../设计说明书/Skill%20导入、选择与%20Compiler%20集成设计说明书.md)
- [Runtime 与 Action Boundary 设计说明书](../设计说明书/Runtime%20与%20Action%20Boundary%20设计说明书.md)
- [事件接入与 Artifact Handoff 设计说明书](../设计说明书/事件接入与%20Artifact%20Handoff%20设计说明书.md)
- [文档总目录与索引](../治理/文档总目录与索引.md)
- [Demo 验收基线](../验收与实施/Demo%20验收基线.md)
