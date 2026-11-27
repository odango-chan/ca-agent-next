# SKILL 作者规范（CA-SL 1.6.0）

> 文档类型：Skill 作者规范（Next 中央规范性设计稿）  
> 文档版本：0.2.0  
> 状态：**DRAFT / REVIEW_REQUESTED**（作者规则待独立评审；CA-SL 1.6.0 尚未由 ca-skills 正式发布）  
> 语言目标：CA-SL 1.6.0 only；不兼容任何历史作者语法  
> 功能归属：EC01 — Skill 作者规范与业务 Skill；消费端关联 F02 / F09  
> 关联需求：IR-008；Issue #49；SR-032；SR-023；SR-029  
> 固定设计基线：ca-agent-next 分支 docs/issue-47-3gpp-schema-codec-boundary，基线 SHA 4873608f5ca854a6bb47cf1a83cb9214da4ae202  
> 上游来源：ca-skills main 780497a2918ad3e7bdff554ab64b0ba627e867e0  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> Demo 限制与排除项：不增加生产级 Admission、Trust Registry、签名、额外 package digest、复杂 IAM、HA/DR 或生产 Qualification；本规范不授权任何外仓代码实施。

本文规定 Skill 作者应如何组织业务语义、选择粒度、拆分 Procedure Node、表达数据依赖和编写注释。**本文不重新定义 CA-SL 语法**：字段、类型、允许值、静态语义以 [CA-SL 1.6.0 完整语言规范](CA-SL%201.6.0完整语言规范.md)及其后续正式 Schema / Golden 为准；本文与语言规范冲突时，语言规范优先。

CA-SL 1.6.0 当前仍是中央设计稿，不是 ca-skills 的正式 Release。本文达到独立设计评审条件，不代表 1.6.0 已发布、Compiler 已实现或 Skill Bundle 已可交付。

## 1. 适用范围与作者原则

1. **业务意图优先。** Skill 描述可复用的产品 / 领域目标，不描述 Provider 的私有实现步骤。
2. **Capability-first。** Skill-facing 只引用公开 Capability ID；Capability 与公开 Callable 双向一对一。Skill 作者不选择 Callable ID、Operation ID 或 backendOperationId。
3. **确定性边界显式。** 能通过已声明的 Schema、Capability、Predicate、arguments 和 routes 确定的行为，不交给模型猜测；无法形式化的解释和指导留在 SKILL.md / references。
4. **契约优先于注释。** 执行要求必须进入正式机器契约；注释只解释原因、上下文和来源。
5. **最小而完整。** 不为了显得详细而过度拆分 Skill 或 Node，也不把多个独立业务动作塞进一个无法清晰证明的节点。
6. **来源可追溯。** 外部标准、Owner 约束和业务流程必须能追溯到准确版本、章节或固定源提交。
7. **新旧隔离。** 新作者源只按 CA-SL 1.6.0 编写；历史 v1alpha5 只读留档，不做语法兼容、字段映射、自动迁移或 fallback。

## 2. Skill 粒度：何时创建 Skill、何时保留 Capability

Skill package 粒度与 Procedure Node 粒度是两个不同问题，不能混为一谈。

### 2.1 创建 Skill

当行为具有可复用的产品 / 领域语义，且模型需要处理业务输入规范化、歧义消解、多个受治理动作的组合、明确的成功证明或 UNKNOWN 处理时，才创建可执行 Skill。

Skill 应是可发现、可复用的业务单元，不应只为某个 Benchmark、单个部署或某个 Provider 适配而存在。

### 2.2 保留为 Capability

如果行为只是低层副作用或只读查询，没有独立产品语义，应保留为 Provider / Runtime Capability，而不是包装成一个 Skill。典型情况包括单次协议调用、原始状态读取、环境专属适配动作。

**禁止一 Tool Call 一个 Skill。** 多个 Skill 可以复用同一公开 Capability；不同业务语义放在各自 Skill 中，底层能力不重复实现。

### 2.3 路由属于 Agent

Skill routing 是 Agent 的选择策略，不是先执行一个 Skill 再生成另一个 Skill 的执行链。领域词汇、归一化提示、适用性提示和歧义处理可以作为模型上下文，但不得重新引入 Routing Skill → ExecutionTarget → Executable Skill 的运行时授权链。

Benchmark / Sandbox 的注入故障、评分逻辑和专项证据不自动进入生产 Skill。先建立最小可复用业务 Skill，评估专用设置留在测试层。

## 3. Skill Package 结构与文件职责

CA-SL 1.6.0 当前中央设计的唯一作者包形状为：

~~~text
skill-root/
  SKILL.md
  schemas/                    # 可选，共享 YAML Schema 资源
  scripts/                    # 可选，共享 Script 源码
    manifest.yaml             # 存在可执行 Script 时必需
    *.py
  references/                 # 可选
  assets/                     # 可选
  assurance/                  # 可选
    contract.yaml
    procedure.yaml
    predicates.yaml
~~~

| 文件 / 目录 | 作者职责 | 不应放入的内容 |
|---|---|---|
| SKILL.md | Agent-facing 身份、用途、适用场景、业务输入、完成语义、限制与指导；Front Matter 只遵循 Agent Skills Specification | `when`、Capability Grant、Procedure、Tool 权限、Provider 内部细节 |
| assurance/contract.yaml | 唯一作者 Contract：可选顶层 when、requestSchema、contexts、dependencies、capabilities、单一全局 precondition、limits | 第二份 Contract、独立 Goal 字段、Callable ID、Git URL / branch / 下载指令 / 作者自选 Callable |
| assurance/procedure.yaml | 唯一静态 Procedure DAG、显式 inputs、Node 阶段和 routes | 动态生成图、隐式状态传递、私有 backendOperationId |
| assurance/predicates.yaml | Predicate 参数签名、Evidence 要求和 evaluator；没有 Predicate 时仍保留合法空 PredicateSet | Skill 选择条件、隐藏副作用 |
| schemas/ | Skill Package 自有 Schema；YAML 1.2 文件表示 JSON Schema 数据模型，LLM 可读、Host 可校验、Assurance 可引用 | 复制 Owner / Provider / Host 的外部 Schema |
| scripts/ | Skill Package 自有 Python Script 源码；LLM 可读、Assurance 可引用 | HTTP、SBI、文件、数据库或 Provider 副作用 |
| scripts/manifest.yaml | Script ID、精确入口、用途、输入/输出 Schema；是资源索引，不是 Skill Descriptor 或 Capability Grant | 任意路径、动态模块、模型提交代码或命令 |
| references/、assets/ | 按需加载的共享参考资料和静态资源 | 隐式 Runtime 输入或执行权限 |
| assurance/ | 可选的确定性契约；只包含 contract.yaml、procedure.yaml、predicates.yaml | 共享 Schema / Script 文件的第二份副本 |

没有 `assurance/` 的 Skill 仅支持 LLM-guided。存在 `assurance/` 时，`contract.yaml`、`procedure.yaml`、`predicates.yaml`（无 Predicate 时也须是合法空 PredicateSet）、Schema、依赖和所有静态语义必须全部有效，才同时具备 Deterministic 与 LLM-guided 两种模式；Assurance 不完整或无效时必须拒绝，不得静默降级为 LLM-guided。

`schemas/` 与 `scripts/` 是公共资源层，不随 Assurance 是否存在而移动。Schema 文件以 YAML 1.2 表示 JSON Schema 数据模型，扩展名使用 `.schema.yaml`；Contract、Script Registry 和脚本输入/输出 Schema 的路径均相对 Skill Package 根目录。

`Script Registry` 每个条目必须声明 Script ID、包内文件、顶层 entrypoint、purpose（transform / predicate）、inputSchema 和适用时的 outputSchema。Procedure Script 只引用 transform；Predicate evaluator 只引用 predicate。LLM 可以通过同一 Host Script Runner 调用当前 Skill Registry 中登记的全部脚本，不按 purpose 过滤；LLM、Procedure 和 Predicate 共用同一脚本字节、Registry 和 I/O Schema，不设置逐脚本 LLM 标记或额外 Host 开关。Predicate Script 的 LLM 调用只返回普通计算结果，不产生 Evidence 或 Assurance 阶段 Outcome。Host 仅解析当前 Skill 的固定 Package snapshot 和 Registry ID，不接受模型提供代码、路径、模块名、函数名或命令。

没有 Assurance 的 Skill 仍可拥有和使用这些公共资源，不需要 Compiler；Host Importer 负责共享资源与 Script Registry 的基本结构检查。存在 Assurance 时 Compiler 还必须验证其引用闭包。旧版 ca-skills 的其他目录（例如 cases/）不因此自动迁入新版；历史源结构只作追溯，不提供兼容。Skill Studio 的工作区目录（例如 lib / output）也不是 Skill Package 的作者文件。

### 3.1 SKILL.md

- 必须有 Agent Skills Specification 规定的 Front Matter；name 与包根目录一致，description 清楚描述 Skill 能做什么以及何时适用。
- 正文使用清晰、简洁的 Markdown，先写业务目标和适用范围，再写输入、完成条件、失败 / 不确定语义和限制。语言遵循项目与目标使用者的约定，并在同一 Skill Package 内保持一致；CA-SL 1.6.0 不规定 SKILL.md 正文语言。
- 不重复 Procedure 的逐节点执行细节。较长的 3GPP 条款映射、字段来源和历史决策放入 references。
- allowed-tools 即使存在也只是元数据，不授予 Capability、Callable 或 Runtime 权限。
- SKILL.md Front Matter 只使用 Agent Skills Specification 规定的标准字段；CA-Agent 不扩展 `when`。`when` 只能作为 `assurance/contract.yaml` 的可选顶层字段；没有 Assurance 的 Skill 没有 Contract，因此不声明 `when`。Front Matter 出现 `when` 必须按未知字段拒绝。

## 4. CA-SL 1.6.0 作者契约边界

本节是作者检查清单；机器字段的最终定义以 CA-SL 1.6.0 语言规范和正式 Schema 为准。

| 位置 | 作者规则 |
|---|---|
| Contract.when | `assurance/contract.yaml` 的可选顶层纯 CEL 选择表达式；仅适用于存在 Assurance 的 Skill；只读取 event.type 和当前 Skill requestSchema 对应的 input；不是 SKILL.md Front Matter 字段，也不是执行期 Predicate |
| Contract.requestSchema | Skill 自有公共 Request 根；有请求输入时必须声明；字段只能使用选择阶段已经可用的数据 |
| Contract.contexts | 集中声明 Host Context 的精确 Schema 引用；Host 拥有 Context，Skill 不复制 Host Schema |
| Contract.dependencies | Alias → 稳定 Package ID；不写 Git URL、分支、下载指令或作者自选 Callable |
| Contract.capabilities | 仅列公开 Capability ID；是授权请求，不等于依赖本身 |
| Contract.precondition | 可选且至多一个全局门禁引用，精确指向 NodeId.precondition；阶段内部使用有序 predicates 列表 |
| Contract.limits.maxActions | 可选正整数上界；只能收紧 Host / Deployment 的预算 |
| Procedure.arguments | 每个调用点必须显式绑定；具体结构由 CA-SL 1.6.0 正式 Schema / Golden 冻结；Predicate arguments 与 Predicate.parameters 的有序签名一致 |
| Predicate | 只做纯判断；UNKNOWN 不得转 PASS；Evidence 要求必须由正式 Predicate 契约声明；Predicate Script 通过 Registry 的 purpose=predicate 条目引用 |
| Operation | 一个 kind=operation 的公开 Capability，Effect 由 Package 定义（READ 或 MUTATION）；或一个 Registry 中 purpose=transform 的 Script ID | kind=observation Capability、Callable ID、backendOperationId、任意脚本路径 |
| Observation | 一个 kind=observation 且 Effect=READ 的公开 Capability；每个 Observation 阶段最多一个 | MUTATION Capability、Callable ID、backendOperationId |
| Reconcile | Owner / Host / Runtime 的内部结果确认机制，不是 Skill-facing Capability、作者阶段或独立 Node |
| Goal | 不定义 Contract.goal；业务意图由 SKILL.md 描述，最终成功由可达 Postcondition 聚合 PASS 直接路由 SUCCEEDED |

### 4.1 Schema 所有权

- Skill 只拥有自己的 Request Schema 和真正由 Skill 定义的数据；这些 Schema 放在根目录 `schemas/`，使用 YAML 1.2 序列化 JSON Schema 数据模型，供 LLM / Host / Assurance 共用。
- Host 拥有 Context Schema；Evidence 的发布保证由 Owner / Package 定义，Host / Runtime 按契约验证并投影到 Predicate 输入。
- Owner / Provider Package 拥有 Operation、Observation 的 Input / Output Schema、Effect 和 Evidence 保证。
- 不把外部 Owner / Provider / Host Schema 复制到 Skill 包内；通过精确依赖和 Schema 引用使用。外部 Schema 保留其发布格式与身份，不投影成 Skill 自有 Schema。
- Owner Schema ID 内含的不可变版本标记必须原样保留。
- OpenAMSM 3GPP Source Bundle 是原版 OpenAPI 3.0 来源快照，不是 Capability Package；Skill 仅在显式 pin 依赖后引用精确 components/schemas，Compiler 按 OAS 3.0 dialect 解析，原版 YAML 不投影、不改写。
- NAS / NGAP Codec Output Schema 由 Provider 独立发布，不得从 SBI binary slot 或 3GPP OpenAPI transport schema 推导。

### 4.2 显式数据流

- Procedure.inputs 是唯一的命名输入映射；每个值必须是精确的 `context.*` SourcePath。Request 字段如需进入 Procedure，必须经 Host 声明并提供的 Context 路径（例如 `context.request.pduSessionId`），不得直接把 `request.*` 当作根。
- 每个 Operation / Observation / Predicate 调用点都必须显式写 `arguments`；参数名称、数量、顺序和类型必须匹配目标 Schema / Predicate 签名。Procedure Script 通过 Registry Script ID 引用，并显式绑定其输入；不得在 Procedure 中直接写文件路径。
- `arguments` 的值只允许 CA-SL 1.6.0 支持的 SourcePath 或标量字面量；禁止动态表达式、隐式转发、自动 null、参数猜测或重排。SourcePath 根只允许 `context`、`inputs` 和已声明 Node Producer；其他根拒绝。
- Node 输出必须通过精确的 `NodeId.Stage.output` SourcePath 显式传递；只有 Operation / Observation 阶段产生可绑定 output。CA-SL 1.6.0 不定义 Wait、await、polling 或 `wait.output`。所有引用必须由正式语言 Schema / Compiler 检查，不得依靠字段名推断。
- Operation / Observation / Procedure Script 的 arguments 具体结构以 CA-SL 1.6.0 正式 Schema / Golden 为准；Predicate arguments 按 Predicate.parameters 的有序签名提供。本文不另行发明参数结构。


### 4.3 3GPP PostSmContexts 的原版 OpenAPI 与 when 示例

3GPP SBI 已有正式契约时，Skill 直接消费 pin 后的 OpenAMSM 原版 OpenAPI 3.0 Component，不另造字段投影。对于 `nsmf.create-sm-context`，`input` 是 Plugin 从 `PostSmContexts.requestBody` 的 `multipart/related` 中抽取并规范化后的 `jsonData` 对象；该对象的 Schema 根是 `#/components/schemas/SmContextCreateData`，不是整个 multipart envelope。

`assurance/contract.yaml`：

~~~yaml
when: 'event.type == "nsmf.create-sm-context" && input.requestType == "INITIAL_REQUEST"'
requestSchema: schemas/create-sm-context-request.schema.yaml
~~~

`schemas/create-sm-context-request.schema.yaml` 是 Skill-owned G.4 根；在显式 pin 的 OpenAMSM Source Bundle dependency 下，它必须直接引用 `TS29502_Nsmf_PDUSession.yaml#/components/schemas/SmContextCreateData`。引用的 dependency alias / wire 编码由 ca-skills 与 Compiler Owner 在正式 1.6.0 Schema / Golden 中冻结；本设计不猜造该机器字段或 URI 形式，也不复制、重写或投影上游 YAML。

原版 `SmContextCreateData.requestType` 引用同文件 `#/components/schemas/RequestType`；`RequestType` 是 string schema，枚举包含 `INITIAL_REQUEST`、`EXISTING_PDU_SESSION`、`INITIAL_EMERGENCY_REQUEST`、`EXISTING_EMERGENCY_PDU_SESSION`，另有 OAS3 未来字符串扩展分支。因此唯一正确的字段路径是 `input.requestType`，比较值是字符串 `"INITIAL_REQUEST"`，不是整数。固定来源：OpenAMSM commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`；原始文件 blob `3572be0315a782691ce8b5546b7bc1d5b22fcd64`。

## 5. Procedure Node 的结构

每个业务 Node 最多各声明一个以下阶段，并按固定顺序执行：

1. Precondition
2. Operation
3. Observation
4. Postcondition

Procedure 必须是单一静态 DAG，具有 `start` 和 `nodes`；不得动态生成节点、任意循环或嵌套 Procedure Call。Node 至少包含一个业务阶段。阶段可以省略，但不得重排、重复或用注释补足。Precondition / Postcondition 阶段内部使用非空、有序的 `predicates` 列表。Operation 阶段最多调用一个 `kind=operation` 的公开 Capability（Effect 由 Package 决定，可为 READ 或 MUTATION）或一个纯本地 Procedure Script；Observation 阶段最多调用一个 `kind=observation` 且 Effect=READ 的公开 Capability。各阶段的 `routes` 只作用于所属阶段，不得跨阶段借用。非末阶段的正常 Outcome 按语言规则进入下一阶段；当前 Node 的末阶段必须显式路由。

CA-SL 1.6.0 不定义 Skill 层的 Wait、await、polling Node、Wait-only Node、`wait.output` 或 Wait timeout route。异步协议交互属于 Tool / Provider / SMF Operation；Operation 负责在返回最终规范化结果和适用 Evidence 后才完成。Host / Runtime 管理 Deadline、Cancellation、Correlation、Budget、UNKNOWN、迟到结果责任和必要的 Reconcile。作者不得拆出等待节点、声明 Wait trigger、复制协议 Schema 或编写轮询循环。Mutation Reconcile 是 Runtime / Owner 的内部流程，不创建作者 Reconcile Node。

## 6. Node 拆分与合并原则

### 6.1 一个 Node 表达一个主要业务动作边界

默认将一个 Node 设计为一个可解释的业务动作边界：最多一个主要 Operation（一个公开 Capability 调用，或一个纯本地 Procedure Script），可配套一个直接服务于同一动作的 Observation，以及该动作自己的 Precondition / Postcondition。

Node 不是 HTTP 请求、函数调用、文件、协议报文或 Provider backend operation 的包装单位。Node ID 表达业务动作，不表达实现细节。

### 6.2 必须拆分的情况

出现以下任一情况，应拆为多个 Node：

1. **需要调用两个不同的公开 Operation Capability。** 一个 Operation 阶段只有一个 Capability；顺序调用两个公开业务动作时，分别建 Node，并通过显式输出和 arguments 传递结果。
2. **存在独立业务提交边界。** 两个动作可以分别成功、失败、被拒绝或产生不同的业务结果，应分别表达。
3. **存在独立的证据或权威确认边界。** 只有当证据具有独立生命周期、权威来源、Correlation / generation，或必须被多个后续业务动作单独消费时，才拆为独立 Node。若 READ / Postcondition 只是对同一 Operation 的直接确认，且结果只服务于该动作，应留在同一 Node 的 Observation / Postcondition。
4. **分支路径需要执行独立业务动作或恢复动作。** Outcome 本身不构成拆分理由：如果不同 Outcome 只需跳转到不同后续 Node 或终态，用当前阶段的 `routes` 表达；只有某条路径还需独立 Capability / 业务动作、独立提交边界或独立证据确认时，才建立对应 Node。
5. **一个 Node 已无法用一个 Operation + 可选 Observation 清楚解释。** 不得把多个 Mutation 藏在一个作者 Node 的说明或脚本中。

### 6.3 应保持在同一个 Node 的情况

满足以下条件时，优先保持一个 Node：

1. Precondition、一个 Operation、一个直接相关的 Observation 和 Postcondition 共同表达同一个业务动作。
2. 一个公开 Capability 内部包含多个 HTTP / SBI / NAS / N2 / PFCP / 数据库或 Provider handler 步骤；这些是 Owner / Provider 内部实现，不拆成 Skill Node。
3. 同一阶段有多个需要按顺序判断的 Predicate；保留在该阶段的 predicates 列表中，不为每个 Predicate 建 Node。
4. 同一阶段的不同 Outcome 只需要路由到不同后续节点或终态；用 routes 表达，不为每个 Outcome 机械复制一个 Node。
5. 只是字段重命名、投影或简单参数映射；优先用显式 arguments，不新增一个只做搬运的 Node。

### 6.4 特殊 Node

- **最终验证 Node：**当最终 Goal 需要独立聚合多个前序结果时，可以使用只含 Postcondition 的 Node；其聚合 PASS 必须直接路由 SUCCEEDED。
- **纯 Observation Node：**当一个 READ 是独立业务步骤或其证据要单独消费时，可以使用只含 Observation 的 Node。
- **纯 Script Node：**只有当本地纯转换具有明确的数据处理边界且无法用简单 arguments 表达时才使用；不得借 Script 隐藏副作用。
- **不得创建：**start-only Node、wait-only Node、reconcile-only Node、HTTP-only Node、Provider handler Node、单 Predicate Node 或仅为增加图节点数量而存在的空 Node。此处的 wait-only Node 仅作为明确禁止项，不表示 CA-SL 存在 Wait 语法。

### 6.5 Node 命名

- 使用稳定、可读的 kebab-case。
- 优先采用业务动词 + 业务对象，例如 create-context、apply-qos-change、verify-release-completion。
- 不使用 call-tool-1、operation-03、backend-op-x、http-post 或按文件行号命名。
- Node ID 在同一 Procedure 内唯一；重命名必须同步所有 start、routes、global precondition 和输出引用。
- Node ID 不得复用 Callable ID、backendOperationId 或协议内部消息 ID。


### 6.6 已核对真实样本的使用方式

以下样本均来自固定的 ca-skills v1alpha5 源提交，只用于核对业务动作和证据边界；**Node 数量、旧 `tool:` 字段、Callable 名称和旧 arguments 结构都不是 1.6.0 的迁移目标**。

| 历史样本 | 固定源文件 | 观察到的结构性事实 | 1.6.0 作者裁决 |
|---|---|---|---|
| Create | `examples/skills/establish-pdu-session-mas/assurance/procedure.yaml`（14 个历史 Node） | 覆盖订阅校验、SM Context、策略、UPF、N4、接入信令和最终建立验证 | 不把每个历史 Tool 调用机械映射为新 Capability / Node；先按新 Owner 发布的 Capability 边界重新归并，最终建立状态仍须由可达 Postcondition 证明 |
| Modify | `examples/skills/modify-pdu-session-mas/assurance/procedure.yaml`（4 个历史 Node） | 将原始 N1 解码、QoS Delta Mutation 和最终完成验证分开表达 | 解码与修改是两个不同公开动作时必须分 Node；NAS 字节或 PFCP/N1/N2 内部步骤本身不是 Node |
| Release | `examples/skills/release-pdu-session-mas/assurance/procedure.yaml`（10 个历史 Node） | 区分 N1 解析、命令构建、N1/N2 确认、资源清理和最终释放验证 | 只有独立公开动作、独立提交或独立确认边界才拆分；Owner 内部协议子步骤不拆成 Skill Node |

这些样本是历史行为证据，不保证旧 Tool 与未来 Capability 一对一对应。新作者不得从旧 Callable 名称、旧 Node 数量或旧参数结构推导 1.6.0 契约；缺少正式 Capability / Schema / Evidence 发布物时必须等待生产者输入，不得自行补造。

### 6.7 完整正向示例：QoS 调整 Skill

以下示例给出一份完整的 1.6.0 作者源结构，展示自定义 MAS 请求契约、共享 Schema / Script、Procedure.inputs、四阶段、显式 arguments、routes、Predicate Evidence 和 Node 拆分。该 QoS 示例使用 MAS 自定义 Event / Request Schema，不代表 3GPP SBI 契约；3GPP 原版 OpenAPI 用法见 §4.3。外部 `host-context` 与 `mas` Package ID / Schema / Capability / Evidence ID 是教学占位符，真实 Skill 必须替换为 Owner / Host 已正式发布并固定版本的身份；本例不声称已通过正式 Compiler Golden。

Package：

~~~text
qos-adjustment/
  SKILL.md
  schemas/
    qos-request.schema.yaml
    normalize-qos-input.schema.yaml
    normalize-qos-output.schema.yaml
  scripts/
    manifest.yaml
    normalize_qos.py
  assurance/
    contract.yaml
    procedure.yaml
    predicates.yaml
~~~

`SKILL.md`：

~~~markdown
---
name: qos-adjustment
description: Validate and apply a requested PDU Session QoS adjustment.

---

# QoS adjustment

Use this Skill when an authorized request asks to change the QoS parameters of an existing PDU Session. A completed change must be confirmed by the Owner result and the declared postcondition.
~~~

`schemas/qos-request.schema.yaml`：

~~~yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: urn:example:qos-adjustment:qos-request:v1
type: object
properties:
  adjustmentType:
    type: string
    enum: [QOS_ADJUSTMENT]
  pduSessionId:
    type: integer
    minimum: 1
  target5qi:
    type: integer
    minimum: 1
    maximum: 255
  gbrUlKbps:
    type: integer
    minimum: 0
  gbrDlKbps:
    type: integer
    minimum: 0
required: [adjustmentType, pduSessionId, target5qi, gbrUlKbps, gbrDlKbps]
additionalProperties: false
~~~

`schemas/normalize-qos-input.schema.yaml`：

~~~yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: urn:example:qos-adjustment:normalize-qos-input:v1
type: object
properties:
  request:
    $ref: qos-request.schema.yaml
required: [request]
additionalProperties: false
~~~

`schemas/normalize-qos-output.schema.yaml`：

~~~yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: urn:example:qos-adjustment:normalize-qos-output:v1
type: object
properties:
  pduSessionId:
    type: integer
    minimum: 1
  qos:
    type: object
    properties:
      fiveQi:
        type: integer
        minimum: 1
        maximum: 255
      gbrUlKbps:
        type: integer
        minimum: 0
      gbrDlKbps:
        type: integer
        minimum: 0
    required: [fiveQi, gbrUlKbps, gbrDlKbps]
    additionalProperties: false
required: [pduSessionId, qos]
additionalProperties: false
~~~

`scripts/manifest.yaml`：

~~~yaml
scripts:
  normalize-qos:
    file: scripts/normalize_qos.py
    entrypoint: run
    purpose: transform
    inputSchema: schemas/normalize-qos-input.schema.yaml
    outputSchema: schemas/normalize-qos-output.schema.yaml
~~~

`scripts/normalize_qos.py`：

~~~python
def run(input):
    request = input["request"]
    return {
        "pduSessionId": request["pduSessionId"],
        "qos": {
            "fiveQi": request["target5qi"],
            "gbrUlKbps": request["gbrUlKbps"],
            "gbrDlKbps": request["gbrDlKbps"],
        },
    }
~~~

`assurance/contract.yaml`：

~~~yaml
when: 'event.type == "mas.qos.adjust-request" && input.adjustmentType == "QOS_ADJUSTMENT"'
requestSchema: schemas/qos-request.schema.yaml
dependencies:
  host-context: urn:example:host-context
  mas: urn:example:mas-qos-contracts
contexts:
  request: host-context::urn:example:host-context:schema:request-context:v1
  session: host-context::urn:example:host-context:schema:session-context:v1
capabilities:
  - mas.session.qos.modify
limits:
  maxActions: 4
~~~

`assurance/procedure.yaml`：

~~~yaml
start: validate-request
inputs:
  request: context.request.payload
  sessionRef: context.session.sessionRef

nodes:
  validate-request:
    precondition:
      predicates:
        - predicate: qos.request.valid
          arguments:
            - inputs.request
      routes:
        PASS: normalize-qos
        FAIL: FAILED
        UNKNOWN: UNRESOLVED

  normalize-qos:
    operation:
      script: normalize-qos
      arguments:
        request: inputs.request
      routes:
        SUCCEEDED: modify-qos
        FAILED: FAILED

  modify-qos:
    # This remains one business action; provider-internal SBI/PFCP steps are not Nodes.
    operation:
      capability: mas.session.qos.modify
      arguments:
        sessionRef: inputs.sessionRef
        pduSessionId: normalize-qos.operation.output.pduSessionId
        qos: normalize-qos.operation.output.qos
      routes:
        FAILED: SAFE_STOPPED
        DENIED: FAILED
        NOT_COMMITTED: FAILED
        OUTCOME_UNKNOWN: UNRESOLVED
    postcondition:
      predicates:
        - predicate: qos.change.confirmed
          arguments:
            - modify-qos.operation.output
            - inputs.sessionRef
      routes:
        PASS: SUCCEEDED
        FAIL: SAFE_STOPPED
        UNKNOWN: UNRESOLVED
~~~

`assurance/predicates.yaml`：

~~~yaml
predicates:
  qos.request.valid:
    parameters:
      - request: schemas/qos-request.schema.yaml
    evaluator:
      type: cel
      expression: request.adjustmentType == "QOS_ADJUSTMENT" &&
        request.pduSessionId > 0 &&
        request.target5qi >= 1 &&
        request.target5qi <= 255

  qos.change.confirmed:
    parameters:
      - result: mas::urn:example:mas:schema:qos-change-result:v1
      - sessionRef: host-context::urn:example:host-context:schema:session-ref:v1
    evidence:
      requires:
        result:
          - mas.session.qos.change
    evaluator:
      type: cel
      expression: result.status == "APPLIED" &&
        result.sessionRef == sessionRef
~~~

作者检查要点：

- 选择条件位于 `assurance/contract.yaml` 顶层 `when`；引用的 `input` 字段由同一 Contract 的 `requestSchema` 定义。SKILL.md Front Matter 不声明 `when`。
- `schemas/` 与 `scripts/` 位于 Package 根目录，不因是否存在 Assurance 而移动。
- `normalize-qos` 是一个纯本地 transform Script，arguments 组装为一个 JSON Object 并由 inputSchema 校验。
- `modify-qos` 只表达一个公开业务 Capability；Provider 内部 SBI / PFCP 子步骤不拆成 Skill Node。
- 最终成功必须经过 Postcondition PASS；UNKNOWN 进入 UNRESOLVED，不能由 HTTP 200 或 Script 输出替代 Owner Evidence。
- LLM 可通过相同 Script Runner 调用 `normalize-qos`；该调用结果只是普通计算输出，不会执行业务 Capability，也不会使 Procedure 自动通过。

## 7. 注释原则

ca-skills 的已核对作者指南、作者模型、Granularity、Syntax、Package Layout 和 Schema Ownership 原文没有定义一套独立、完整的 YAML 注释规范。本节是 Next 新增的作者规则：它根据 CA-SL 的机器契约边界和真实 Procedure 样本明确“注释解释什么、不能决定什么”。

### 7.1 注释的目的

注释只解释机器结构无法表达的作者意图，重点回答：

- **Why：**为什么需要这个 Node、Predicate、分支或特殊映射；为什么此处不能合并。
- **Business context：**该动作对应哪个业务步骤、业务边界或重要限制。
- **Source traceability：**非显而易见的字段来源、协议标准章节、Owner 文档版本或固定源提交。
- **Non-obvious mapping：**参数单位、编码转换、枚举映射、输入可用阶段或特殊输出路径的原因。
- **Intentional omission：**为什么某个常见动作、重试或副作用被明确排除。

### 7.2 注释粒度

1. 不要求每个字段、每行或每个简单 Node 都有注释。
2. 对非显而易见的业务边界、协议约束、特殊映射或刻意省略，应在最靠近相关 Node / 字段的位置写简短注释。
3. Node 注释优先解释“为什么它是一个独立业务动作”，而不是复述 Node ID 或 Capability 名称。
4. 复杂标准映射、长篇背景和来源链放在 references；Procedure 注释只保留理解当前结构所必需的摘要。
5. 一个注释只说明一个主题；避免把整个业务流程、错误矩阵和运行手册塞入 YAML。

### 7.3 注释不得承载执行语义

以下内容不得只写在注释里：

- 必填 / 可选、类型、默认值、单位、范围、枚举、Schema 约束；
- 调用哪个 Capability、传入哪些 arguments、结果从哪里读取；
- Predicate 判定条件、Evidence 要求、Outcome 和 routes；
- READ / MUTATION Effect、幂等性、重试、Reconcile、超时或权限边界；这些属于 Capability Package、Owner / Provider Contract、Host / Runtime 契约的相应所有权层，不由 Skill 注释定义；
- 成功、失败、UNKNOWN、终态和业务完成证明。

Skill-facing 执行语义必须由正式 Contract、Schema、Capability 引用、Predicate、arguments 或 routes 表达；Effect、Receipt、幂等性、重试、Reconcile 和权限边界则由对应 Owner / Provider / Host / Runtime 契约定义。若注释与机器契约冲突，以相应权威契约为准，并必须修复过期注释；不能让作者或 Runtime 通过注释猜测行为。

### 7.4 注释禁止事项

- 不重复字段名、Schema 描述或显而易见的代码行为。
- 不逐行解释 YAML 语法，不写“这里调用某 Capability”这种没有额外信息的注释。
- 不用注释保存临时调试输出、运行时 ID、用户数据、密钥、Token 或环境专属地址。
- 不留下没有关联 Issue 的 TODO / FIXME。
- 不引用浮动的 latest；引用标准、Owner 或外部文件时应给出版本、章节或固定源提交。
- 不保留与当前 1.6.0 契约冲突的 v1alpha5 说明。

### 7.5 注释示例

反例（注释承担执行语义）：

~~~yaml
# 错误：必须先 READ 到 qosFlow 已更新，才能把这次 Mutation 判为成功。
~~~

这句话实际定义了成功条件和必需的 READ，却没有可供 Compiler 检查的 Predicate、Evidence 与 Postcondition；不能只留在注释里。

正例（注释解释作者意图）：

~~~yaml
# 此 Node 保留为独立 QoS 修改动作；PFCP、N1 和 N2 子步骤由 Owner 在一个公开 Capability 内完成。
~~~

该注释只解释 Node 粒度和 Owner 边界。真正的调用目标、arguments、Outcome、Evidence 和 routes 必须由 CA-SL 1.6.0 的正式作者结构及对应 Owner / Runtime 契约表达。删除正例注释不应改变执行语义。

SKILL.md 正文与 YAML 注释遵循项目语言约定，并在同一 Skill Package 内保持一致；注释应简洁、可读，不因语言选择改变 CA-SL 语义。Next 的规范、设计和迁移文档使用中文。

## 8. 命名与表达约定

| 对象 | 规则 |
|---|---|
| Skill name | 遵循 Agent Skills Specification：小写 ASCII、数字与连字符；目录名一致 |
| SKILL.md description | 描述能力和适用时机，不堆叠实现细节 |
| Contract 字段 | 严格使用 CA-SL 1.6.0 正式字段；不得发明别名 |
| Node ID | 推荐 kebab-case、业务动词 + 对象；这是作者风格约定，不扩展 CA-SL 1.6.0 标识符语法，最终合法性以正式 Schema / Compiler 检查为准 |
| Capability ID | 原样使用 Owner / Provider 发布的公开 ID，不缩写、不拼接 Callable |
| Predicate ID | 稳定、表达业务事实；参数顺序由 Predicate.parameters 固定 |
| Schema 属性 | 严格匹配被引用 Schema；不在作者侧重命名外部字段 |
| 文件名 | 推荐 kebab-case；目录层级严格按 CA-SL 1.6.0 包形状 |
| 注释 | 遵循项目语言约定并保持包内一致；说明 why / 来源 / 非显然约束，不替代字段语义 |

不得在 Skill 作者源中出现 Operation ID、Callable ID、backendOperationId、ProviderBinding 或部署 endpoint 作为 Skill-facing 选择目标。

## 9. 反例与正确做法

| 反例 | 问题 | 正确做法 |
|---|---|---|
| 每个 Provider 内部 HTTP / NAS / PFCP handler 建一个 Node | 暴露实现细节，破坏 Capability 抽象 | 一个公开 Operation Capability 一个主要动作 Node；内部步骤留在 Owner / Provider |
| 一个 Node 连续描述两个不同 Mutation | 单个 Operation 阶段无法准确表达 | 拆成两个 Node，显式传递第一个结果 |
| 每个 Predicate 单独建 Node | 将判断列表误作业务动作 | 放在同一 Precondition / Postcondition 的有序 predicates 列表 |
| 为每个 Outcome 复制一套 Node | 图膨胀且重复业务逻辑 | 使用 routes 表达分支 |
| 用注释写“必须 READ 后才能成功” | Compiler 无法校验 | 声明 Observation、Predicate、Evidence 和 Postcondition |
| 用一个 Script 包装 HTTP / 文件 / 数据库调用 | 通过本地 Script 绕过 Capability / Effect | 副作用必须由公开 Capability 承担；Script 只做纯本地计算 |
| 在 Skill 中引用旧版 Callable 别名 | 把内部调用身份泄漏给作者 | 只声明 Capability ID |
| 在没有 Assurance 的 Skill 中声明 when | 无 Assurance 包没有 Contract，不编译确定性选择条件；Front Matter 的 when 是非法未知字段 | 只允许存在 Assurance 的 Skill 在 assurance/contract.yaml 声明可选顶层 when |
| 把 Reconcile 写成一个作者 Node | 把 Host / Runtime 内部机制暴露给 Skill | 由 Owner Contract 和 Runtime 负责原始调用的结果确认 |

## 10. 作者自检清单

- [ ] Skill 具有可复用业务语义，不是单 Tool / 单 Provider call 的包装。
- [ ] SKILL.md 有符合 Agent Skills Specification 的 Front Matter；name / description 准确描述 Skill，正文简洁且语言一致。
- [ ] 新 Assurance 只使用 CA-SL 1.6.0；没有旧版字段、Callable 或兼容入口。
- [ ] 有 Assurance 时，可选 `when` 位于 `assurance/contract.yaml` 顶层；SKILL.md Front Matter 不声明 `when`；无 Assurance Skill 不声明 `when`；引用 `input` 时 `requestSchema` 必须存在。
- [ ] requestSchema、contexts、dependencies、capabilities 的所有权与身份准确。
- [ ] Procedure 是单一静态 DAG；每个 Node 的阶段顺序正确，每种阶段不重复；末阶段正常 Outcome 显式路由。
- [ ] 每个 Operation 阶段最多一个 Capability / 纯 Script；每个 Observation 阶段最多一个 READ Capability。
- [ ] Node 拆分依据是业务动作、独立提交或证据边界，而不是 HTTP / Provider 内部步骤。
- [ ] Precondition / Postcondition 中的 Predicate 有序聚合，没有单 Predicate Node。
- [ ] 所有 arguments 和输出引用显式绑定，没有隐式上下文或字段猜测。
- [ ] UNKNOWN 没有被转成 PASS；最终 Postcondition PASS 直接路由 SUCCEEDED。
- [ ] Procedure 不包含 Wait / await / polling / `wait.output`；异步完成由 Tool / Provider / SMF Operation 与 Host Runtime 负责。
- [ ] Outcome-only 分支使用 routes；只有独立业务动作、提交或证据边界才拆 Node。
- [ ] Create / Modify / Release 历史样本只用于识别业务边界，不复制旧 Callable / Node / arguments 结构。
- [ ] 注释解释 why / source / 非显然约束；没有把执行语义写进注释。
- [ ] 引用的外部标准、Owner / Provider Schema 和 OpenAPI Source Bundle 已固定版本与来源。
- [ ] references 内容没有被误当作隐式 Runtime 输入。
- [ ] AI Authoring 的候选修改可由同一语言服务和正式 Compiler gate 检查。

## 11. 与 AI Authoring 的关系

Skill Studio 的文本编辑、AI Authoring 和代码评审必须使用同一份作者规范。AI 可以通过 Host Resource Read 按需读取当前 Package snapshot 中的 schemas/、scripts/manifest.yaml、scripts/ 源码与 references；可以通过正常 Agent Runtime 的 host.skill-script.execute 调用当前 Skill Registry 中登记的全部脚本（包括 transform 和 predicate），并与 Assurance 共用同一 Script Runner。不得在 Studio Worker / AI Authoring 中创建第二套 Python 执行器，也不得：

- 把 Callable / backendOperationId 写入 Skill；
- 通过注释补足缺失的 Schema、arguments、Predicate 或 routes；
- 为了增加“可读性”机械拆分 Node；
- 将 Owner / Provider 内部协议步骤暴露为业务 Node；
- 擅自改变 Capability、Schema 或依赖身份；
- 将预览、静态诊断或模型自评显示为 Compiler Build / Verify PASS；
- 在当前 Procedure-only Change Set 中修改 schemas/、scripts/ 或 scripts/manifest.yaml；
- 通过任意路径、模块名、代码或命令绕过 Host Script Execution Capability。

Apply 前仍须由用户确认，并对同一候选源码与依赖锁执行正式 Compiler gate。当前 F09 只定义目标设计，Studio 的 1.6.0 Authoring / LSP / Compiler 产品验收仍 NOT_RUN。

## 12. 来源迁移与裁决

固定源仓为 ca-skills main 780497a2918ad3e7bdff554ab64b0ba627e867e0。下表给出本轮核对的源路径与 Git blob SHA；Next 中保留的历史原文均标记为非规范来源。

| 来源主题 | ca-skills 源路径 | 固定 Blob SHA | 迁移裁决 |
|---|---|---|---|
| 中文作者指南 | docs/authoring.zh-CN.md | 9643747efa942f9402384457856a836ca6213ac2 | 已迁入 Next 历史原文；只提取仍有效的作者原则 |
| 英文作者指南 | docs/authoring.md | e19768a72ade5481637fb6253c4773c85cbed5b2 | 新增只读原文归档 |
| 作者模型 | docs/authoring-model.md | 3d63b5f3c8a58c6a86c85adfca5c95b9ec9fb429 | 已迁入 Next 历史原文；旧语法不作为新输入 |
| Skill Granularity | .agents/skills/create-connectionagent-skill/references/skill-granularity.md | c0c52f0a4717b00ede89309264f1e46ca04f5a54 | 区分 Skill / Capability / Agent routing；不等同 Node 拆分规则 |
| Authoring Syntax 导航 | .agents/skills/create-connectionagent-skill/references/authoring-syntax.md | c4768dbce8d1f1a8744da3f37ec1950c683a59b5 | 只作旧规范章节导航 |
| Package Layout | docs/project-layout.md | b133dd6e3c7caa6824e09d3fdbf15e85d6fd4966 | 提取目录和责任边界；旧目录结构不直接沿用 |
| Schema Ownership | docs/schema-ownership.md | 0ea47fb973815adcff5a48b58686336ddd89b7b2 | 提取所有权原则；字段按 1.6.0 重建 |
| Create Skill 工作流 | .agents/skills/create-connectionagent-skill/SKILL.md | dd6ef655839fe31ed28ae4ad865d5c0241a29ef4 | 提取创建 / 复核流程；旧工具链命令不迁入 |
| Create Procedure 示例 | examples/skills/establish-pdu-session-mas/assurance/procedure.yaml | 63c56d0ec7591a757862a4ff54a189dda56a9144 | 只作为业务动作粒度与最终证明节点的历史样本 |
| Modify Procedure 示例 | examples/skills/modify-pdu-session-mas/assurance/procedure.yaml | b019da3638297c06baffd07fb17ba6d97e852138 | 只作为多业务动作分 Node 的历史样本 |
| Release Procedure 示例 | examples/skills/release-pdu-session-mas/assurance/procedure.yaml | 2aadc6e1e1c387fe2a3197f2e4720622eafd77c8 | 只作为独立协议确认 / 业务结果边界的历史样本 |

已迁入 Next 的历史原文：[CA-SL 作者指南中文原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL作者指南原文.md)、[CA-SL 作者模型原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL作者模型原文.md)、[英文作者指南原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL作者指南英文原文.md)、[Skill Granularity 原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL%20Skill%20Granularity%20原文.md)、[Authoring Syntax 原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL%20Authoring%20Syntax%20原文.md)、[Package Layout 原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL%20Package%20Layout%20原文.md)、[Schema Ownership 原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL%20Schema%20Ownership%20原文.md)、[Create Skill 工作流原文](../设计说明书/外部能力域/EC01-CA-SL/CA-SL%20Create%20Skill%20工作流原文.md)。

迁移说明：

1. 原 Skill Granularity 定义的是 Skill package 与 Capability / routing policy 的边界，不是 Procedure Node 的拆分规则；本规范分开定义两种粒度。
2. 已核对的 ca-skills 作者文档没有独立、完整的 YAML 注释规范。本节注释规则是 Next 新增的明确约束，不伪称为旧文档原文。
3. Create / Modify / Release 示例只用于核对业务动作、协议确认和最终证明的边界；示例中的 v1alpha5 语法、Callable 身份和目录不得复制到 1.6.0。
4. CA-SL 1.6.0 语法权威仍是语言规范；本规范负责作者表达质量、Node 粒度和注释约束。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 从 ca-skills 作者指南、作者模型、Granularity、Package Layout、Schema Ownership、创建工作流和真实 Skill 样本中提炼仍有效原则；按 CA-SL 1.6.0 重建作者包、Node 粒度与注释规则 | Issue #49；IR-008；SR-032；SR-023/029 |
| 2026-11-27 | 0.1.1 | GPT-6.2（ChatGPT） | §3.1、§4.1～4.2、§7～8、§10 | 修正 Procedure.inputs 仅允许 context SourcePath 的边界，补充 SourcePath 根与 Node Producer 引用；移除无依据的英文强制要求；区分 Skill 作者语义与 Owner / Runtime 契约所有权；修复示例的正常路由 | 避免作者指南超出 CA-SL 1.6.0 语言稿或引入无依据的语言约束 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.2 | GPT-6.2（ChatGPT） | §3、§5、§7、§10 | 补充 Assurance 有效性与模式边界、空 PredicateSet、静态 DAG 和 Node-entry Wait 的作者要求；将代码示例缩为不伪装可构建的注释片段 | 避免作者误把参考片段当作完整 1.6.0 Procedure 或把无效 Assurance 静默降级 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.3 | GPT-6.2（ChatGPT） | §4、§5 | 将 arguments 结构明确留给正式 1.6.0 Schema / Golden，不再由作者规范预设映射形状；补充 Wait 事件接受的隐式正常边约束 | 避免作者规范超出当前语言设计已冻结的语法边界 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.4 | GPT-6.2（ChatGPT） | §4～§7、§10、§12 | 对齐 Operation / Observation kind 与 Effect，明确 routes 的阶段归属、Wait timeout、分支拆分边界；加入 Create / Modify / Release 样本结构性裁决和注释正反例 | 消除 Node 过度拆分歧义，补齐 AC 所需的真实样本解释和注释反例 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.5 | GPT-6.2（ChatGPT） | §3～§5、§10～§11 | 将 schemas/scripts 定为根目录共享资源，补充 Script Registry、Host Script Execution Capability、YAML Schema 源和 LLM-only Package 规则 | 确保 LLM 与 Assurance 使用同一资源，禁止模型任意 Python 执行 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.6 | GPT-6.2（ChatGPT） | §3、§11 | 明确 LLM Script Action 同时受 Registry `llmInvocable` 与 Host `scriptExecution.llmEnabled`（默认 false）约束 | 防止仅靠 Skill 包内标记就意外暴露 Host 脚本执行能力 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.7 | GPT-6.2（ChatGPT） | §3、§11 | 删除逐脚本 `llmInvocable` 和 Host `scriptExecution.llmEnabled`；LLM 与 Assurance 共用 Script Runner | 让 Demo 的模型调用能力与确定性执行能力一致，避免重复授权配置 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.8 | GPT-6.2（ChatGPT） | §3～§6、§7、§10～§11 | 删除作者级 Node-entry Wait / await / polling 规则；补齐完整正向 Skill 示例、共享资源读取和 transform / predicate 全 Registry 调用原则 | 回归既定 CA-SL 作者语法边界，证明作者仅凭规范可写出无 Wait 的 1.6.0 Skill | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.9 | GPT-6.2（ChatGPT） | §2～§4、§6、§9～§10 | 将 `when` 从 `assurance/contract.yaml` 移至 SKILL.md Front Matter，限定仅有 Assurance 的 Skill 可声明；无 Assurance Skill 不声明 when | 对齐既定 Skill 入口决策，避免无 Assurance 包引入未经 Compiler 检查的 CEL 选择条件；历史错误入口判断，已由 0.2.0 撤销，不构成兼容方案| Issue #49；IR-008；SR-032 |

| 2026-11-27 | 0.2.0 | GPT-6.2（ChatGPT） | §3～§4、§6.7、§9～§10、修订记录 | 将 `when` 恢复为 assurance/contract.yaml 顶层唯一入口；SKILL.md Front Matter 不声明 when；拆分 MAS 自定义 QoS 示例与 3GPP 原版 OpenAPI Create 示例，并将 requestType 修正为字符串枚举 | 撤销误引入的 Front Matter 方案；避免把自定义字段误当作 3GPP SBI Schema | Issue #49；IR-008/009；SR-013/031/032；F02/F08/F09 |
