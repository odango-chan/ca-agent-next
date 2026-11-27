# SKILL 作者规范（CA-SL 1.6.0）

> 文档类型：Skill 作者规范（Next 中央规范性设计稿）  
> 文档版本：0.1.1  
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
  assurance/                 # 可选
    contract.yaml
    procedure.yaml
    predicates.yaml
    schemas/
    scripts/
  references/
~~~

| 文件 / 目录 | 作者职责 | 不应放入的内容 |
|---|---|---|
| SKILL.md | Agent-facing 身份、用途、适用场景、业务输入、完成语义、限制与指导 | Capability Grant、Procedure、when、Tool 权限、Provider 内部细节 |
| assurance/contract.yaml | 唯一作者 Contract：when、requestSchema、contexts、dependencies、capabilities、单一全局 precondition、limits | 第二份 Contract、独立 Goal 字段、Callable ID、下载 URL / branch / digest |
| assurance/procedure.yaml | 唯一静态 Procedure DAG、显式 inputs、Node 阶段和 routes | 动态生成图、隐式状态传递、私有 backendOperationId |
| assurance/predicates.yaml | Predicate 参数签名、Evidence 要求和 evaluator | Skill 选择条件、隐藏副作用 |
| assurance/schemas/ | Skill 自有 Request 根及明确声明的本地 Schema | 复制 Owner / Provider / Host 的外部 Schema |
| assurance/scripts/ | 可选的纯本地 Procedure / Predicate Script | HTTP、SBI、文件、数据库或 Provider 副作用 |
| references/ | 按需加载的协议说明、标准映射、长篇业务背景和来源材料 | 隐式 Runtime 输入或执行权限 |

旧版 ca-skills 的根目录 schemas/、scripts/、cases/ 等布局仅保留历史参考。除非 CA-SL 1.6.0 正式 Package Schema 明确增加，不得把旧目录结构直接搬入新版 Bundle。Skill Studio 的工作区目录（例如 lib / output）也不是 Skill Package 的作者文件。

### 3.1 SKILL.md

- 必须有 Agent Skills Specification 规定的 Front Matter；name 与包根目录一致，description 清楚描述 Skill 能做什么以及何时适用。
- 正文使用清晰、简洁的 Markdown，先写业务目标和适用范围，再写输入、完成条件、失败 / 不确定语义和限制。语言遵循项目与目标使用者的约定，并在同一 Skill Package 内保持一致；CA-SL 1.6.0 不规定 SKILL.md 正文语言。
- 不重复 Procedure 的逐节点执行细节。较长的 3GPP 条款映射、字段来源和历史决策放入 references。
- allowed-tools 即使存在也只是元数据，不授予 Capability、Callable 或 Runtime 权限。
- 不在 SKILL.md Front Matter 增加 when。选择条件只在 assurance/contract.yaml 的顶层 when。

## 4. CA-SL 1.6.0 作者契约边界

本节是作者检查清单；机器字段的最终定义以 CA-SL 1.6.0 语言规范和正式 Schema 为准。

| 位置 | 作者规则 |
|---|---|
| Contract.when | 可选的纯 CEL 选择表达式；只读取 event.type 和当前 Skill requestSchema 对应的 input；不是 SKILL.md 字段，也不是执行期 Predicate |
| Contract.requestSchema | Skill 自有公共 Request 根；有请求输入时必须声明；字段只能使用选择阶段已经可用的数据 |
| Contract.contexts | 集中声明 Host Context 的精确 Schema 引用；Host 拥有 Context，Skill 不复制 Host Schema |
| Contract.dependencies | Alias → 稳定 Package ID；不写 Git URL、分支、下载指令或作者自选 Callable |
| Contract.capabilities | 仅列公开 Capability ID；是授权请求，不等于依赖本身 |
| Contract.precondition | 可选且至多一个全局门禁引用，精确指向 NodeId.precondition；阶段内部使用有序 predicates 列表 |
| Contract.limits.maxActions | 可选正整数上界；只能收紧 Host / Deployment 的预算 |
| Procedure.arguments | 必须显式绑定；Operation / Observation / Script 使用命名映射，Predicate 使用匹配参数签名的有序列表 |
| Predicate | 只做纯判断；UNKNOWN 不得转 PASS；Evidence 要求必须由正式 Predicate 契约声明 |
| Observation | 只读查询，Capability 必须是 kind=observation 且 Effect=READ |
| Reconcile | Owner / Host / Runtime 的内部结果确认机制，不是 Skill-facing Capability、作者阶段或独立 Node |
| Goal | 不定义 Contract.goal；业务意图由 SKILL.md 描述，最终成功由可达 Postcondition 聚合 PASS 直接路由 SUCCEEDED |

### 4.1 Schema 所有权

- Skill 只拥有自己的 Request Schema 和真正由 Skill 定义的数据。
- Host 拥有 Context Schema；Evidence 的发布保证由 Owner / Package 定义，Host / Runtime 按契约验证并投影到 Predicate 输入。
- Owner / Provider Package 拥有 Operation、Observation 的 Input / Output Schema、Effect 和 Evidence 保证。
- 不把外部 Owner / Provider / Host Schema 复制到 Skill 包内；通过精确依赖和 Schema 引用使用。
- Owner Schema ID 内含的不可变版本标记必须原样保留。
- OpenAMSM 3GPP Source Bundle 是原版 OpenAPI 3.0 来源快照，不是 Capability Package；Skill 仅在显式 pin 依赖后引用精确 components/schemas，Compiler 按 OAS 3.0 dialect 解析，原版 YAML 不投影、不改写。
- NAS / NGAP Codec Output Schema 由 Provider 独立发布，不得从 SBI binary slot 或 3GPP OpenAPI transport schema 推导。

### 4.2 显式数据流

- Procedure.inputs 是唯一的命名输入映射；每个值必须是精确的 `context.*` SourcePath。Request 字段如需进入 Procedure，必须经 Host 声明并提供的 Context 路径（例如 `context.request.pduSessionId`），不得直接把 `request.*` 当作根。
- 每个 Operation / Observation / Predicate 调用点都必须显式写 `arguments`；参数名称、数量、顺序和类型必须匹配目标 Schema / Predicate 签名。Procedure Script 也必须显式绑定其输入。
- `arguments` 的值只允许 CA-SL 1.6.0 支持的 SourcePath 或标量字面量；禁止动态表达式、隐式转发、自动 null、参数猜测或重排。SourcePath 根只允许 `context`、`inputs` 和已声明 Node Producer；其他根拒绝。
- Node 输出必须通过精确的 `NodeId.Stage.output` SourcePath 显式传递；Wait 规范化输入使用 `NodeId.wait.output`。所有引用必须由正式语言 Schema / Compiler 检查，不得依靠字段名推断。
- Operation / Observation / Procedure Script 的 arguments 具体结构以 CA-SL 1.6.0 正式 Schema / Golden 为准；Predicate arguments 按 Predicate.parameters 的有序签名提供。本文不另行发明参数结构。

## 5. Procedure Node 的结构

每个业务 Node 最多各声明一个以下阶段，并按固定顺序执行：

1. Precondition
2. Operation
3. Observation
4. Postcondition

Node 至少包含一个阶段。阶段可以省略，但不得重排、重复或用注释补足。Precondition / Postcondition 阶段内部使用非空、有序的 predicates 列表。Operation 阶段最多调用一个公开 Capability 或一个纯本地 Procedure Script；Observation 阶段最多调用一个只读 Observation Capability。

Node-entry Wait 是目标 Node 入口的可选控制，不是第五阶段，不创建 Wait-only Node；作者不得写 await / poll 循环。Mutation Reconcile 是 Runtime / Owner 的内部流程，不创建作者 Reconcile Node。

## 6. Node 拆分与合并原则

### 6.1 一个 Node 表达一个主要业务动作边界

默认将一个 Node 设计为一个可解释的业务动作边界：最多一个主要 Operation（一个公开 Capability 调用，或一个纯本地 Procedure Script），可配套一个直接服务于同一动作的 Observation，以及该动作自己的 Precondition / Postcondition。

Node 不是 HTTP 请求、函数调用、文件、协议报文或 Provider backend operation 的包装单位。Node ID 表达业务动作，不表达实现细节。

### 6.2 必须拆分的情况

出现以下任一情况，应拆为多个 Node：

1. **需要调用两个不同的公开 Operation Capability。** 一个 Operation 阶段只有一个 Capability；顺序调用两个公开业务动作时，分别建 Node，并通过显式输出和 arguments 传递结果。
2. **存在独立业务提交边界。** 两个动作可以分别成功、失败、被拒绝或产生不同的业务结果，应分别表达。
3. **存在独立的证据或权威确认边界。** 例如不同协议响应、不同 Owner 结果或不同 generation / correlation，需要独立 READ / Postcondition 证明。
4. **存在真实业务分支或恢复路径。** 分支必须通过正式 Outcome 和 routes 表达；不同路径具有独立业务动作时建立对应 Node。
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
- **不得创建：**start-only Node、wait-only Node、reconcile-only Node、HTTP-only Node、Provider handler Node、单 Predicate Node 或仅为增加图节点数量而存在的空 Node。

### 6.5 Node 命名

- 使用稳定、可读的 kebab-case。
- 优先采用业务动词 + 业务对象，例如 create-context、apply-qos-change、verify-release-completion。
- 不使用 call-tool-1、operation-03、backend-op-x、http-post 或按文件行号命名。
- Node ID 在同一 Procedure 内唯一；重命名必须同步所有 start、routes、global precondition 和输出引用。
- Node ID 不得复用 Callable ID、backendOperationId 或协议内部消息 ID。

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

Skill-facing 执行语义必须由正式 Contract、Schema、Capability 引用、Predicate、arguments、Wait 或 routes 表达；Effect、Receipt、幂等性、重试、Reconcile 和权限边界则由对应 Owner / Provider / Host / Runtime 契约定义。若注释与机器契约冲突，以相应权威契约为准，并必须修复过期注释；不能让作者或 Runtime 通过注释猜测行为。

### 7.4 注释禁止事项

- 不重复字段名、Schema 描述或显而易见的代码行为。
- 不逐行解释 YAML 语法，不写“这里调用某 Capability”这种没有额外信息的注释。
- 不用注释保存临时调试输出、运行时 ID、用户数据、密钥、Token 或环境专属地址。
- 不留下没有关联 Issue 的 TODO / FIXME。
- 不引用浮动的 latest；引用标准、Owner 或外部文件时应给出版本、章节或固定源提交。
- 不保留与当前 1.6.0 契约冲突的 v1alpha5 说明。

### 7.5 注释示例

以下为 Procedure 片段，后续 `verify-context` Node 的定义省略；Mutation 的正常结果只路由到后续验证，不直接证明 Invocation 成功。

~~~yaml
nodes:
  # One public mutation boundary. The Owner owns the internal SBI/NAS/PFCP steps.
  create-context:
    operation:
      capability: mas.sc.context.create
      arguments:
        psi: inputs.psi
      routes:
        SUCCEEDED: verify-context
~~~

上例中的注释解释为什么不把 Owner 内部步骤拆成 Skill Node；真正的调用目标和参数仍由 capability / arguments 表达。若删除注释，执行语义不应改变。

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
| 在 SKILL.md Front Matter 写 when | 混淆 Agent 元数据与语言选择契约 | 写在 assurance/contract.yaml 顶层 |
| 把 Reconcile 写成一个作者 Node | 把 Host / Runtime 内部机制暴露给 Skill | 由 Owner Contract 和 Runtime 负责原始调用的结果确认 |

## 10. 作者自检清单

- [ ] Skill 具有可复用业务语义，不是单 Tool / 单 Provider call 的包装。
- [ ] SKILL.md 有符合 Agent Skills Specification 的 Front Matter；name / description 准确描述 Skill，正文简洁且语言一致。
- [ ] 新 Assurance 只使用 CA-SL 1.6.0；没有旧版字段、Callable 或兼容入口。
- [ ] Contract.when 位于 contract.yaml；只读取 event.type 和 requestSchema input。
- [ ] requestSchema、contexts、dependencies、capabilities 的所有权与身份准确。
- [ ] 每个 Node 的阶段顺序正确，每种阶段不重复。
- [ ] 每个 Operation 阶段最多一个 Capability / 纯 Script；每个 Observation 阶段最多一个 READ Capability。
- [ ] Node 拆分依据是业务动作、独立提交或证据边界，而不是 HTTP / Provider 内部步骤。
- [ ] Precondition / Postcondition 中的 Predicate 有序聚合，没有单 Predicate Node。
- [ ] 所有 arguments 和输出引用显式绑定，没有隐式上下文或字段猜测。
- [ ] UNKNOWN 没有被转成 PASS；最终 Postcondition PASS 直接路由 SUCCEEDED。
- [ ] 注释解释 why / source / 非显然约束；没有把执行语义写进注释。
- [ ] 引用的外部标准、Owner / Provider Schema 和 OpenAPI Source Bundle 已固定版本与来源。
- [ ] references 内容没有被误当作隐式 Runtime 输入。
- [ ] AI Authoring 的候选修改可由同一语言服务和正式 Compiler gate 检查。

## 11. 与 AI Authoring 的关系

Skill Studio 的文本编辑、AI Authoring 和代码评审必须使用同一份作者规范。AI 可以提出 Change Set，但不得：

- 把 Callable / backendOperationId 写入 Skill；
- 通过注释补足缺失的 Schema、arguments、Predicate 或 routes；
- 为了增加“可读性”机械拆分 Node；
- 将 Owner / Provider 内部协议步骤暴露为业务 Node；
- 擅自改变 Capability、Schema 或依赖身份；
- 将预览、静态诊断或模型自评显示为 Compiler Build / Verify PASS。

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
