> 迁移来源：ca-agent-demo/docs/design/skill-tool-runtime-boundary.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：SKILL / Script / Tool / Runtime / Adapter 的 Demo 职责边界  
> 迁移追踪：ca-agent-next Issue #12。该仓是 Python Generic Agent Host 参考实现，不是 Next 目标架构的自动实现证明。

---

> **2026-11-10 边界补充：** 需要区分独立 5GC 工具化项目与本仓 Agent-side Tools。外部 Provider / Fabric 项目拥有工具服务端 API、协议、网元交互、外部状态与 operation owner；本仓 tools/ 是 Skill → Agent Tool contract / registration / adapters / compositions，负责调用 / 组合这些外部工具。它不是外部工具服务端，也不应复制 Provider / Fabric 或 Open5GS 核心网。详见 [Agent-side Tools 与外部 5GC Tool 调用边界](root-tools-open5gs-layout.md)。

# SKILL / Script / Tool / Runtime / Adapter 职责边界（R5.7 设计决议）

**决定日期**：2026-11-06。**状态**：已确认的设计原则；R5.7 实现与本地验收见 [R5.7 记录](../../artifacts/reviews/20261106-r57-tool-schema-boundary/README.md)（未运行真实 UE/R6）。**范围**：`ca-agent-demo` 确定性 CreatedSession Demo，优先复用现有机制，不建设生产级权限、发布或 Tool 平台。本决议取代 [2026-11-05 旧方案](skill-owned-scripts-and-tools.md) 中“专属 READ/MUTATION Python 脚本随 SKILL 执行”的**默认施工方向**；旧文档保留为历史背景，不代表相关能力已实现。

## 1. 一句话原则

**SKILL 决定做什么及用哪些业务参数；Tool 声明可复用能力与参数契约；Runtime 统一校验并调度；Adapter/Owner 执行真实操作并证明结果。**

| 层 | 拥有的内容 | 不应拥有的内容 |
| --- | --- | --- |
| `skills/<name>/assurance/` | Procedure 的先后、`with/from` 来源、分支、前后置验证；Contract 完成目标；Predicate 业务事实与三态 | 网络地址、权限凭据、发送实现 |
| `skills/<name>/scripts/` | 有必要时的业务选择、计算、请求**业务参数**构造；受控纯计算 | HTTP/MCP/FFI 发送、密钥、任意 URL、operationRef 或发送成功声明；重复的 Tool Schema 验证 |
| `tools/`（Agent-side Tool layer） | Skill → Agent Tool 的稳定 Capability/Operation、input/output Schema、Effect、registration 与 adapters/compositions；调用 / 组合外部 5GC Tools | 外部 Provider/Fabric Tool server、Open5GS 核心网、特定 SKILL 的业务流程与第二套 Runtime/Capability 权威 |
| 通用 Runtime | 冻结准入、Script 来源/沙箱控制、`with/from` 绑定、调用 Tool 前按其 inputSchema 校验、验证输出结构和来源、调度、预算、结果/UNKNOWN/reconcile 传递 | 按 `createdsession`、UDM、PCF、AMF 名字特判业务；为每个 Script 复制 Tool 参数 Schema |
| 本仓 Agent-side Tool adapter | 调用 / 组合外部 5GC Tool API，做 Agent-side DTO projection、exact identity binding、local attempt metadata 与责任协调 | 取代外部服务端 owner、复制网络状态机或重新决定 SKILL 业务流程 |
| 外部 Provider / Fabric / Network owner | 服务端协议、真实目标 / NF、hold/claim、原 waiter、单发送者、外部 operation state 与 exact-original reconcile | 重新决定 Skill 的业务选择或下一跳 |

> `tools/` 已是本仓 Agent-side Tool layer；它调用 / 组合独立项目的外部 5GC Tool APIs。`tools/contracts/` 定义 Agent-facing Capability，不是外部 Tool server catalog。复用现有 `CompositeRuntimeOperationBackend`、`CapabilityContractRegistry`、外部 clients 与 Schema；不得复制 Provider / Fabric 服务端或建立第二份 Runtime / Capability authority。

## 2. Schema 的单一作者面

1. **Tool 提供 inputSchema / outputSchema，Runtime 在 Tool 边界统一校验。** Schema 与传输实现（Local、HTTP、将来 MCP/.so）解耦，且不能从具体 Adapter 的 URL 推导权限。
2. 专用于构造单个 Tool 请求的 Script **可不另建 input/output Schema**，不要求在 Python 里重复写字段类型、枚举、上下界检查；其输出经 `with/from` 绑定后由 Runtime 依据**完整 Tool inputSchema**校验。能直接用 `with/from` 表达的参数不需要 Script。
3. Script 有多个消费者、独立业务数据结构或 Predicate 需要结构化结果时，**允许**独立 Script Schema；但不要复制同一 Tool 请求结构。现有 4 个 `local_compute` Script 的 Schema 与行为不能为此任意删除。
4. **免去 Script 自行校验 ≠ 无校验**：Script 源码和依赖仍要冻结并受限执行；Runtime 仍证明输出来自本次 invocation 的真实 producer，拒绝替换、跨 invocation、未准入内容。
5. **Schema 合法 ≠ 调用获准/结果真实**：Owner/Adapter 必须独立核验受信主体、资源、hold、claim、输入来源、协议范围和当前实例。Provider/Fabric 自身的协议边界验证需要保留，不属于重复业务 Schema。
6. 若 Mutation 外部已可能发生而返回格式错误或超时，不得因 outputSchema 失败便宣称 `NOT_COMMITTED` 或再次发送；按既有 UNKNOWN + exact-original reconcile 处理。READ 的无效结果不能变成成功 Observation。

## 3. Tool 契约、执行与未来 MCP

稳定的 Operation ID、类型/Schema/Effect 由 Tool 契约定义，SKILL 在 Procedure 中沿用既有 `call`；Runtime 按现有 Registry 和 Effect 机制分派，不新增 `tool-call` DSL、第二条执行图或网络脚本解释器。工具提供结构化结果和原操作查询语义；MUTATION 保留持久 operationRef、单发送者与 UNKNOWN reconcile。

`tools/contracts/`、`tools/adapters/` 可在 R5.7 按**实际需求**创建：先做一条可运行的 Script → Tool inputSchema → Registry → 现有 Adapter 路径，复用现有 `integrations/`，不要求现阶段目录齐全。Adapter 可在保持同一逻辑 Tool 契约的条件下采用 HTTP 或本地实现；未来增加 MCP Server 或 FFI/.so Adapter **不是本轮验收前置**。

未来 MCP 映射：稳定名称→MCP tool name；input/output Schema→MCP 对应 Schema；tools/call→现有受控 Operation 调用。MCP 传输结果不自动成为 `COMMITTED`；真实效果与事实仍由 Owner 证明。

## 4. SBI 与 N1/N2 的分工

SKILL Script **可以构造逻辑目标和业务参数**，如 Session/UE 的业务选择以及 N1/N2 Prepare/Transfer 的已取得业务值；但不得决定未授权的 HTTP URL、伪造 NF/subject/hold/operationRef、调整安全 deadline 或产生“已发送”回执。目标 URL、部署 NF、发送授权、幂等身份和持久发送记录属于 Host/Tool/Owner。

当前已知可用路径：`Agent Demo → Provider HTTP Prepare → 受保护的 NAS N1 + NGAP N2 artifact → Provider HTTP Transfer → Fabric HTTP → SCP/AMF`，Fabric 保证原 SMF waiter 交付。**N1、N2 是两份待交付消息内容，不是 SKILL 分别发送的两个 HTTP 请求。**

Provider 具有 Go `c-shared` 的 `.so` API 原型，但目前该入口未装配跨进程 Policy/Ledger/Artifact 等依赖，不能替换已验证的 HTTP 真实链。未来如采用 FFI，只替换 Tool Adapter；先保证进程依赖、ABI/内存生命周期、持久回放、异常/并发和与 HTTP 相同的效果语义，不能把 `.so` 直接交给 Script 执行。

## 5. R5.7 的最小验收与非目标

- 真实选一项**确有业务计算需要**的请求构造，使用既有 Script → Procedure `with/from` → `call` → Tool；不能为增加文件数而造 Script。
- Runtime 从 Tool 提供的 schema 验证输入和输出；对缺字段、错误类型、错 producer/跨 invocation、无效输出做到拒绝，不触发额外网络发送；输出错误发生在外部发送后则保持 UNKNOWN。
- 同一 Tool 契约替换 Adapter 不改 SKILL；修改合规业务 Script 并重新准入后，Adapter/Runtime Python 不随之修改。
- 保留已通过的 PCF Script、UDM、N1/N2 Prepare/Transfer、journal、单发送者、原 SMF waiter、Case 32 和 exact-original reconcile 回归。
- **不做**任意网络 READ/MUTATION Python Script runner、完整 MCP Server、生产级授权/发布平台、全量 16 Backend 迁移、其他仓库改动或真实 UE/R6。正式 Finalizer 授权见 [延期 Issue #167](https://github.com/odango-chan/ca-agent-demo/issues/167)。

> **后续 R5.8 简化决议（2026-11-06）**：实现选择只依赖启动时手工指定的**一份 Tool 注册配置文件**，不依赖 `environmentRef`，也不构建动态 Tool/Environment Resolver；本地 Adapter 的薄执行入口可以集中放进 `tools/adapters/`。详见 [R5.8 手工 Tool 注册](r58-manual-tool-registration.md)。上述 R5.7 的 Schema 与 Runtime 边界保持有效。

## 6. 状态与执行入口

R5.6 已使 `build_pcf_policy_inputs.py` 在 SKILL 内构造策略输入，但**并不等于**已实现本决议的 Tool input/output Schema 驱动的统一 Runtime 校验或可换 Adapter 的 `tools/` 体系。R5.7 需基于最新 main 独立设计、实现与本地验证；旧设计若与本决议冲突，以本文为准。执行清单见 [Skill 整改](../work/execution-routes/skill-authoring-remediation.md)，归档审计见 [R5.5](../../artifacts/reviews/20261106-r55-skill-business-ownership/README.md)。

## 7. R5.8 最小实现（手工 Tool 注册）

R5.8 在 R5.7 边界上只增加**实现选择**，不增加新的 Tool 平台：

- SKILL 的 12 个 `allowedResources.capabilities` 与 Procedure `call:` 不变；
- `tools/contracts/` 继续定义 Schema、Effect 与 Reconcile 契约；
- `tools/registrations/default.yaml` 手工记录 Capability → Implementation ID；
- 启动时 `build_createdsession_agent_service` 读取一份注册、对显式
  `ToolImplementationCatalog` 校验并冻结绑定；不同启动可选择另一份文件，
  但一次 Invocation 不重新读取或切换；
- READY 仍由准入、独立 Capability Effect 契约与 coverage 决定；注册既不是授权
  也不是就绪；
- UNKNOWN mutation 只由收到原调用的实现执行 exact-original reconcile，禁止换
  实现重发；
- Agent 环境字段减负仅登记清单，见
  [Agent 环境字段减负清单](agent-environment-field-cleanup.md)，本轮不删除字段或
  修改扁平 ingress。

Implementation identity 来自 `demo/createdsession_service.py` 中显式构造的 Python
目录，不通过配置文本 import、扫描目录或执行代码。Provider-side MCP 未来可作为
另一种注册 Adapter；Agent-facing `tool-mcp-gw` 不参与 Tool 实现选择。
