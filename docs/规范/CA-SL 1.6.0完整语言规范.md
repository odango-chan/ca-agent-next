# CA-SL 1.6.0 完整语言规范（中央设计稿）

> 文档类型：CA-SL 作者语言规范（中央规范性设计稿）
> 文档版本：0.2.5
> 语言版本：CA-SL 1.6.0
> languageTarget 候选：connectionagent.io/v1.6.0（本设计建议值；发布前由 ca-skills 与 Compiler Owner 在正式 Schema / Golden 中确认）
> 状态：**DRAFT / REVIEW_REQUESTED**；CA-SL 1.6.0 唯一正式语言设计，Assurance 可选；有 Assurance Skill 时 `assurance/contract.yaml` 可声明顶层 `when`；`SKILL.md` Front Matter 不声明 when；无 Assurance Skill 不声明 when；未发布、未冻结。
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 修订日期：2026-11-26
> 规范所有者：ca-agent-next（中央设计）；正式作者 Schema / Golden / Release 由 ca-skills 发布
> 关联：IR-003、IR-008；Issue #40、#49；SR-023、SR-029、SR-013、SR-027、SR-032
> 本文局部非目标：Compiler API / Artifact 字段级 Schema、Provider / Owner 发布物字段、Agent Runtime 实现、生产 Admission、签名、Trust Registry、生产 Qualification

本文是 CA-SL 1.6.0 的完整中央作者语言设计稿，覆盖源码角色、Contract、Procedure、PredicateSet、Context、Request Schema、Capability、when、Evidence、Outcome、Script Runner 和版本边界。它不是 ca-skills 已发布的语言规范，也不授权下游实现。

历史 [CA-SL v1alpha5 完整语言规范](CA-SL%20v1alpha5完整语言规范.md)及其 Release Record 仅作只读来源审计；不得把本文理解为 v1alpha5 的兼容解析器、别名、自动迁移或双轨实现。新 1.6.0 源码必须按本文重新编写。

## 1. 规范用语、范围与原则

本文中的 MUST / MUST NOT / REQUIRED / SHOULD / SHOULD NOT / MAY 按 RFC 2119 / RFC 8174 理解。未特别说明时，“拒绝”指 Compiler Check / Link 阶段 fail-closed，且不得产生可发布 Runtime Artifact。

CA-SL 1.6.0 定义 Skill 可选 Assurance 的作者语言。SKILL.md Front Matter 按 Agent Skills Specification 处理，CA-Agent 不在其中增加 `when` 扩展。`when` 是 `assurance/contract.yaml` 的可选顶层 Contract 字段，表达包级 Skill 选择条件；Compiler 从唯一 Contract 读取、类型检查并编译它。没有 Assurance 的 Skill 没有 `contract.yaml`，因此不声明 `when`；若 SKILL.md Front Matter 出现 `when`，必须按未知字段拒绝，不得静默忽略或兼容。语言负责表达确定性执行契约，不负责 Agent 推理、Plugin 生命周期、Provider 私有实现、Owner 业务状态或 Compiler 的部署。

1. 新作者语言和新产品链唯一目标为 CA-SL **1.6.0**。
2. 新 Parser、Check、Link、Build、Verify、Runtime Artifact、Bundle、Agent Importer / Runtime、Skill Studio / LSP 只支持 1.6.0。
3. 不提供 v1alpha5 / v1alpha6 解析器、别名、语法映射、版本协商、双轨编译、旧 Artifact 导入、自动转换、迁移工具或 fallback。
4. 历史 v1alpha5 文件、Schema、Golden、Release Record 和字节保持只读；其设计可作为重新审查语义的来源，但不是新语言的规范性输入。
5. Skill-facing 接口只声明 Capability。每个公开 Capability 与一个公开 Callable 双向一对一；Callable ID 只存在于 Package / Compiler / Runtime / Provider 内部。
6. Procedure 的 Operation / Observation 是 Node 阶段，不是作者级 Operation ID。
7. Assurance 是可选的；存在但无效时必须拒绝导入，不得降级成无 Assurance Package。
8. Demo 不做 SHA-256 / checksum / digest 内容校验、签名、Trust Registry 或生产准入。外部 digest 字段仅为元数据，不重新计算、不比对、不作为 Build / Verify / Runtime 门禁；Source Bundle 原件要求的 byte-for-byte 相等比较是原始字节比较，不使用哈希。此限制不改变 Host Runtime 的授权边界与 Owner Commit Proof。

## 2. 语言分层与包形状

每个 Skill Package 必须有 SKILL.md。共享资源位于 Skill Package 根目录；可选 Assurance 仅放置确定性执行契约：

~~~text
skill-root/
  SKILL.md
  schemas/                    # 可选，共享 Schema 资源
  scripts/                    # 可选，共享 Script 资源
    manifest.yaml             # 存在可执行 Script 时必需
    *.py
  references/                 # 可选，共享参考资料
  assets/                     # 可选，共享静态资源
  assurance/                  # 可选
    contract.yaml
    procedure.yaml
    predicates.yaml
~~~

- SKILL.md：Agent-facing 身份、用途和指导；Front Matter 只遵循 Agent Skills Specification，不声明 `when`、业务 Capability Grant 或 Procedure。
- schemas/：Skill Package 自有 Schema 资源；LLM 可读取，Host 可用于结构化输入/输出校验，Assurance 可引用。文件使用 YAML 1.2 表示 JSON Schema 数据模型，扩展名为 `.schema.yaml`；JSON Schema 语义仍遵循 §12 的 G.4 Profile。
- scripts/：Skill Package 自有 Python Script 源码；LLM 可读取，Assurance 可引用；所有登记脚本均通过统一 Host Script Runner 执行。
- scripts/manifest.yaml：Script ID、精确入口、用途、输入/输出 Schema；它是资源索引，不是第二份 Skill Descriptor，也不授予业务 Capability。
- references/、assets/：按需读取的共享参考资料和静态资源，不是隐式 Runtime 输入。
- assurance/contract.yaml：唯一 Contract；包含可选顶层 `when`、Request Schema、Context、依赖、业务 Capability Grants、全局前置引用和动作预算。
- assurance/procedure.yaml：唯一入口 Procedure DAG、显式输入绑定、Node 四阶段和阶段路由。
- assurance/predicates.yaml：可复用 Predicate 定义及其参数 / Evidence 契约；没有 Predicate 时仍须存在合法空 PredicateSet。

没有 assurance/ 的 Skill 仍可携带 schemas/、scripts/、references/ 和 assets/，并仅支持 LLM-guided；由于没有 `contract.yaml`，不声明 `when`，由 Agent 基于 SKILL.md 语义进行候选选择。SKILL.md Front Matter 若出现 `when`，Importer 必须按未知字段拒绝，不得静默忽略或兼容旧入口。LLM 可通过 Host Script Execution Capability 调用 `scripts/manifest.yaml` 登记的脚本；不设置逐脚本可调用标记或额外 Host 开关。存在 assurance/ 时，contract.yaml、procedure.yaml、predicates.yaml、被引用的共享 Schema / Script、依赖和所有静态语义必须全部有效，才同时具备 Deterministic 与 LLM-guided 两种模式。Assurance 无效时必须拒绝导入，不得静默降级。不得新增 constraint.yaml、activation.yaml、applicability.yaml、第二份 Skill Descriptor 或 Domain Contract Package；predicates.yaml 只描述执行期 Predicate，不参与 Skill 选择。

## 3. 核心术语与所有权

| 术语 | 1.6.0 定义 | 权威来源 |
|---|---|---|
| Skill | SKILL.md 与可选 Assurance 构成的可导入单元 | Skill Package |
| Contract | Assurance 的公共输入、Skill 选择条件、Context、依赖和 Capability Grant 作者契约 | contract.yaml |
| Procedure | 静态确定性执行图 | procedure.yaml |
| PredicateSet | 可复用的纯判断定义 | assurance/predicates.yaml |
| Shared Resource | LLM、Host 和可选 Assurance 共用的 Schema / Script / references / assets；资源身份相对 Skill Package 根目录 | Skill Package root |
| Script Registry | Package-local Script ID、入口、purpose、输入/输出 Schema；不授予业务 Capability | scripts/manifest.yaml |
| Host Script Execution Capability | Host-owned system Capability；只执行当前 Skill Registry 中显式允许的 Script ID | Host Runtime / built-in Tools Extension |
| Node | Procedure 图中的执行节点，最多声明四个业务阶段 | procedure.yaml |
| Capability | Skill-facing 的业务能力身份 / 授权项 | Owner Contract Package 或 Provider Interface Package |
| Callable | Package 内稳定的公开调用身份，含 kind、Effect、Input / Output Schema | ToolCatalog / Provider Package |
| backendOperationId | Provider 私有后端路由身份 | Provider Runtime Bindings |
| Observation | Node 的只读查询阶段；其 Capability 必须映射 kind=observation 且 Effect=READ | Procedure + Package |
| Evidence | 支持业务事实的来源、Scope、Correlation、Freshness 和完整性依据 | Owner / Evidence Contract + Host |
| Reconcile | 原 Mutation 的内部提交结果确认路径，不是作者阶段或 Skill-facing Capability | Owner Contract + Runtime Coordinator |
| Context | Host 按授权装配的只读上下文；不等于模型可见的全部内部状态 | Host Context Package + Host |
| Request | 当前 Event / 用户请求经 Schema 验证后的输入 | Contract.requestSchema + Host |

Skill 不定义 Owner Outcome、Receipt、Commit Proof、Evidence Guarantee、Callable Effect 或 Provider backendOperationId；它只能引用受信发布物并显式传递参数。

## 4. Contract 字段与唯一作者入口

contract.yaml 是唯一 Contract。它不需要 apiVersion / kind 包装；语言版本由正式 BuildRequest / Compiler Target 指定。

规范性字段：

| 字段 | 必需 | 语义与约束 |
|---|---:|---|
| when | 否 | 可选的纯 CEL 布尔 Skill 选择表达式；只读取 event.type 与 requestSchema 类型化的 input；Compiler 静态检查并编译 |
| precondition | 否 | 单一全局门禁引用，精确为 NodeId.precondition；不是 Predicate 列表 |
| requestSchema | 否 | Skill 公共请求 Schema 根的相对路径；有请求输入时声明 |
| contexts | 否 | 一个映射，集中声明所有 Host Context 名称到精确 Schema 引用；不再建立平级 subject / facts / ingress 顶层字段 |
| dependencies | 否 | Alias → 稳定 Package ID；不得写 Git URL、分支、获取指令或作者自选 Callable |
| capabilities | 否 | Skill 请求的 Capability ID 列表；不接受 Callable ID / Operation ID |
| limits.maxActions | 否 | 正整数业务动作预算上界；Host / Deployment 只能进一步收紧 |

示例：

~~~yaml
when: 'event.type == "nsmf.create-sm-context" && has(input.requestType) && input.requestType == "INITIAL_REQUEST"'
precondition: validate-request.precondition
requestSchema: schemas/create-request.schema.yaml
dependencies:
  mas: urn:openamsm:mas:tool-contracts
  host-context: urn:connectionagent:ca:host-context
contexts:
  subject: host-context::urn:connectionagent:ca:context:subject:v1
capabilities:
  - mas.sc.context.create
  - mas.se.establishment-event.record
limits:
  maxActions: 12
~~~

**不定义 goal 字段。** Skill 的目的由 SKILL.md 描述；Procedure 的最终业务成功证明由一个可达 Postcondition 阶段的聚合 PASS 直接路由 SUCCEEDED。不得在 Contract、Postcondition 阶段或 Predicate 成员增加 goal 字段。

Contract 的 precondition 是至多一个全局阶段引用；该引用必须指向真实、可达的 Node precondition。Node 的 precondition / postcondition 各自是单一阶段对象，内部必须使用非空、有序的 predicates 列表；即使只有一个 Predicate 也必须使用列表。

## 5. Context、Request Schema 与显式输入

### 5.1 Request Schema

- `requestSchema` 指向 Skill Package 根目录下由 Skill 自己拥有的 `.schema.yaml` 入口文件，定义规范化 Event payload 的业务输入契约；路径始终相对 Skill Package 根目录，不相对 `assurance/`。源文件采用 YAML 1.2 序列化 JSON Schema 数据模型，Compiler 解析为 JSON 数据模型。若入口为本地 G.4 Schema 根，则按 G.4 Profile 校验；若入口为纯单 `$ref` OAS3 根引用别名，则该目标和其外部闭包按 OAS 3.0 Schema Object dialect 校验，不把外部目标套入 G.4。
- Host 先验证 Plugin Event Schema，再独立验证 Skill Request Schema；两者不是同一 Schema，也不得把完整 3GPP multipart Schema 复制到 Skill。
- `requestSchema` 必须指向 Skill Package 根目录下的 Skill-owned `.schema.yaml` 入口文件。若入口是本地 G.4 对象 Schema，根必须明确 `additionalProperties: false` 并保持闭合；若入口文件仅含一个 `$ref`、精确指向显式 pin 的 OpenAPI 3.0 `components/schemas`，则它是跨 dialect 引用别名，不是本地对象 Schema，不对别名文件套用 G.4 对象闭合断言。别名文件不得包含 `$ref` 以外的兄弟关键字；目标和完整可达闭包按 OAS 3.0 原生语义验证。
- 对存在 Assurance 的 Skill，Contract 顶层 `when` 与 Contract `requestSchema` 是否存在相互独立。只使用 event.type 的 `when` 不要求 requestSchema；`when` 访问 input 成员时必须在 `assurance/contract.yaml` 声明 requestSchema。可选字段必须先以 `has(input.field)` 守卫，并依赖左到右 `&&` 短路事实后再读取。无 Assurance Skill 没有 Contract，不声明 when；任何 Skill 的 SKILL.md Front Matter `when` 都是非法未知字段。
- 只要 Contract 声明 requestSchema，即使 when 不存在或只读取 event.type，Compiler 仍必须验证并把 Request Schema 根和完整资源闭包发布到新 Runtime Artifact。
- 未知 Schema 关键字、循环引用、开放对象、未解析引用或不支持方言均拒绝；不得静默忽略关键字或猜测类型。

### 5.2 Contexts

- contexts 是 Host Context Schema 引用的唯一聚合字段；不建立平级 subjectSchema、factsSchema、ingressSchema 或 contextSchema 入口。
- 每个 contexts 成员引用已声明 dependency Alias 下的精确 Schema ID；同一 Context Schema 不得通过别名或模糊名称重复声明。
- Host Context Package 可以是 Schema-only Package：允许 0 Capability / 0 Callable exports，只提供显式 Schema exports；不得为了满足旧 Package 结构虚构 Tool 或 Callable。
- Context 是 Host-owned、只读、按当前 Invocation 绑定的视图。未声明、未授权或不属于当前 Run 的 Context 不可访问。

### 5.3 Procedure.inputs 与 arguments

Procedure.inputs 是本 Procedure 唯一的命名输入映射，值必须是精确的 context SourcePath：

~~~yaml
start: validate-request
inputs:
  supi: context.subject.supi
  psi: context.request.pduSessionId
nodes:
  validate-request:
    precondition:
      predicates:
        - predicate: request.valid
          arguments:
            - inputs.supi
            - inputs.psi
      routes:
        FAIL: SAFE_STOPPED
        UNKNOWN: UNRESOLVED
~~~

- Procedure.inputs 只负责把 context.* 显式绑定为 Procedure 局部输入名；不得隐式复制整个 Context。
- 每个 Operation / Observation / Predicate 调用点都必须显式写 arguments；参数名、数量、顺序和类型必须匹配目标 Schema / Predicate 签名。
- arguments 值只允许受支持 SourcePath 或标量字面量；不支持动态表达式、隐式转发、自动 null、参数猜测或重排。
- Node 输出必须通过精确的 NodeId.Stage.output SourcePath 显式传递；只有 Operation / Observation 阶段产生可绑定 output。
- context、inputs、已声明 Node Producer 和标量字面量之外的根均拒绝。

## 6. Procedure、Node 与四阶段

Procedure 只有一张静态有向无环图（DAG），必须有 `start` 和 `nodes`。start 必须引用真实 Node；Node ID 不得与保留根或终态冲突；未知、悬空、循环和歧义路由均阻断构建。

一个 Node 可按固定顺序声明以下业务阶段，每个阶段最多一次：

1. `precondition`：调用有序 Predicate 列表；全部 PASS 才产生聚合 PASS。
2. `operation`：二选一调用一个 `kind=operation` 的公开 Capability（Effect 由目标 Package 决定，可为 READ 或 MUTATION），或引用一个 `purpose=transform` 的 Package-local Script ID；两者互斥。Script 不是业务 Capability，不进入 `contract.capabilities`。
3. `observation`：调用一个 `kind=observation` 且 Effect=READ 的公开 Capability；不得产生副作用。
4. `postcondition`：调用有序 Predicate 列表；全部 PASS 才产生聚合 PASS。

Node 可以省略不适用阶段，但必须至少声明一个业务阶段。阶段按上述顺序执行；正常 Outcome 在非末阶段自动进入下一阶段，末阶段必须显式路由。阶段 `routes` 属于该阶段，不得跨阶段借用。Procedure 不支持动态生成节点、任意循环、嵌套 Procedure Call、Wait 字段或同名自动绑定。

**成功边规则：** 唯一允许请求 Invocation `SUCCEEDED` 的边，是一个可达 Postcondition 阶段的聚合 PASS 直接指向 `SUCCEEDED`。Operation / Observation / Precondition 不得直接证明最终成功；任何分支都不得复用另一条分支的旧 PASS。

### 6.1 规范性 YAML 结构文法

以下文法是 CA-SL 1.6.0 的作者对象结构，不是示意性自由 YAML。字段名、层级、基数和参数形状均为规范要求；未知字段、重复 Mapping Key、错误类型或未列出的结构必须拒绝。

结构记法：`map(key: Type, ...)` 表示 YAML 映射；`list<Type>` 表示 YAML 序列；字段后的 `?` 表示可省略；`NonEmptyList<T>` 表示非空序列。

~~~ebnf
Contract              = map(when?: CELExpression,
                            precondition?: NodeId ".precondition",
                            requestSchema?: PackageSchemaPath,
                            contexts?: map<ContextName, QualifiedSchemaId>,
                            dependencies?: map<Alias, StablePackageId>,
                            capabilities?: list<CapabilityId>,
                            limits?: map(maxActions?: PositiveInteger)) ;

Procedure             = map(start: NodeId,
                            inputs?: map<InputName, ContextSourcePath>,
                            nodes: map<NodeId, Node>) ;

Node                  = map(precondition?: PredicateStage,
                            operation?: OperationStage,
                            observation?: ObservationStage,
                            postcondition?: PredicateStage) ;

PredicateStage        = map(predicates: NonEmptyList<PredicateCall>,
                            routes?: OutcomeRoutes) ;

PredicateCall         = map(predicate: PredicateId,
                            arguments: list<Expression>) ;

OperationStage        = CapabilityOperation | ScriptOperation ;
CapabilityOperation   = map(capability: CapabilityId,
                            arguments: map<InputName, Expression>,
                            routes?: OutcomeRoutes) ;
ScriptOperation       = map(script: ScriptId,
                            arguments: map<InputName, Expression>,
                            routes?: OutcomeRoutes) ;

ObservationStage      = map(capability: CapabilityId,
                            arguments: map<InputName, Expression>,
                            routes?: OutcomeRoutes) ;

PredicateSet          = map(predicates: map<PredicateId, Predicate>) ;
Predicate             = map(parameters: NonEmptyList<ParameterDeclaration>,
                            evidence?: EvidenceRequirements,
                            evaluator: CELEvaluator | PredicateScriptEvaluator) ;
ParameterDeclaration  = map(ParameterName: PrimitiveType | QualifiedSchemaId) ;
CELEvaluator          = map(type: "cel", expression: CELExpression) ;
PredicateScriptEvaluator = map(type: "script", script: ScriptId) ;

OutcomeRoutes         = map<StageOutcome, RouteTarget> ;
RouteTarget           = NodeId | TerminalStatus ;
TerminalStatus        = "SUCCEEDED" | "FAILED" | "UNRESOLVED" | "SAFE_STOPPED" ;
Expression            = SourcePath | ScalarLiteral ;
~~~

### 6.2 arguments 与输入对象的精确形状

- `Procedure.inputs` 是 Procedure 唯一的命名输入映射；每个值必须是已声明 Host Context 的精确 SourcePath。它只把 `context.*` 显式绑定为 `inputs.*`，不得隐式复制整个 Context。
- `operation.capability`、`operation.script` 和 `observation.capability` 的 `arguments` 必须是具名映射。键对应目标 Callable Input Schema 或 Script `inputSchema` 的属性名；零参数调用写 `arguments: {}`。
- `precondition.predicates[]` 和 `postcondition.predicates[]` 中每个 Predicate Call 的 `arguments` 必须是有序列表，位置与 `Predicate.parameters` 严格对应；零参数 Predicate 写 `arguments: []`。
- 每个参数值只允许受支持 SourcePath 或 YAML 1.2 标量字面量；不允许内联对象/数组、动态表达式、隐式转发、自动 null、参数猜测或重排。
- SourcePath 只允许 `context.<name>...`、`inputs.<name>...`，以及已在当前可达路径成功产生的 `<node-id>.operation.output...` / `<node-id>.observation.output...`。Predicate 阶段不产生可绑定 output。
- 不定义 `wait.output` 或任何 Wait 专用 Producer。未知根、未声明路径、不可达 Producer、当前分支尚未产生的输出均拒绝。

### 6.3 routes 与阶段推进

- `routes` 只能位于具体阶段映射根，不得写在 Node 根或单个 Predicate Call 成员内。
- Predicate 阶段的 Outcome 为 PASS / FAIL / UNKNOWN。Script Operation 的 Outcome 为 SUCCEEDED / FAILED。Capability Operation / Observation 的可用 Outcome 由已链接的正式 Capability / Owner Contract 和 Runtime 保留 Outcome 联合确定；不得由作者自行扩展。
- 当前阶段后仍有同 Node 后续阶段时，正常 Outcome 自动进入下一阶段，不得在该阶段 `routes` 中重复声明正常 Outcome。阶段是 Node 最后一个已声明阶段时，正常 Outcome 必须显式路由。
- 所有合法非正常 Outcome 必须有显式路由。目标只能是同一 Procedure 的 Node ID 或四种 TerminalStatus。多个 Outcome 可以指向同一目标；无默认分支。
- DAG 静态检查必须覆盖所有可达路由；禁止循环、悬空目标、跨 Procedure 引用和对不可用 Producer 的引用。

### 6.4 Capability 与 Script 的作者边界

- Contract 只列业务 Capability ID；Operation / Observation 只写 Capability ID，不写 Callable ID、Owner alias、backendOperationId 或 Provider selector。
- 一个 Node 的 Operation 只能是一个业务 Operation Capability 或一个纯本地 transform Script，不能同时声明，也不能在同一阶段调用多个目标。
- Observation 只能引用 kind=observation 且 Effect=READ 的业务 Capability。
- Script ID 仅来自当前 Skill Package 的 Script Registry；Script 不是业务 Capability，不进入 `contract.capabilities`。
- 一个公开 Capability 与一个公开 Callable 双向一对一；这是 Package 导出约束，不限制同一 Capability 被多个 Skill / Node 引用。

## 7. Capability、Callable 与 Plugin 契约

- Contract.capabilities 只声明业务 Capability ID；Procedure 的业务 `operation.capability` / `observation.capability` 只写 Capability ID。Package-local `operation.script` 是独立的 Script Registry 引用分支，不是 Capability，与 `operation.capability` 互斥。
- 每个 Skill-facing Capability 恰有一个公开 Callable；每个公开 Callable 恰属于一个 Skill-facing Capability。双向基数均为 1。
- Callable ID 只存在于 Package、Compiler、Runtime、Provider 内部 Binding / Trace / 诊断，不得进入 Skill 作者源或模型 Action 参数。
- Compiler 必须在显式依赖闭包中唯一解析 Capability，检查 Grant、Owner / Package identity、Capability→Callable cardinality、Callable→Capability cardinality、kind、Effect、Input / Output Schema。
- Provider 可以在一个公开 Callable 内部使用多个 backendOperationId / handler，但路由条件必须来自 Callable Input Schema 的封闭 enum / tagged union；不得由 LLM 选择或使用自由字符串 / URL / 动态 Catalog。
- 业务 Capability Operation 只接受 kind=operation；Effect 由 ToolCatalog 决定。Package-local Script 是 `operation.script` 的独立分支，不是 Capability；与 `operation.capability` 互斥。
- Observation 阶段只接受 kind=observation 且 Effect=READ。
- Capability 可被多个 Skill 或 Node 重复引用；一对一约束是 Package 导出关系，不限制引用次数。
- Owner / Provider 的 Capability 与 Callable 不能跨 Package 拼接；所有身份和 Schema 必须来自同一精确发布快照。
- MAS.RECONCILE 是 Runtime Coordinator internal-only target，不是 Skill-facing Capability；普通 Skill / LLM Action 在 Provider IPC 前拒绝，诊断 INTERNAL_RECONCILE_ONLY，IPC 次数为零。MAS.RECEIPT_QUERY 仍是受 Capability / Scope 约束的普通 READ。

## 8. PredicateSet 与 Script

### 8.1 PredicateSet 的作者结构

`assurance/predicates.yaml` 的唯一根字段是 `predicates`。每个 Predicate 以稳定 Predicate ID 为键，并声明有序 `parameters`、可选 `evidence` 和唯一 `evaluator`。

~~~yaml
predicates:
  qos.request.valid:
    parameters:
      - request: schemas/qos-request.schema.yaml
    evaluator:
      type: cel
      expression: request.pduSessionId > 0 &&
        request.target5qi >= 1 && request.target5qi <= 255

  qos.change.confirmed:
    parameters:
      - result: mas::urn:openamsm:mas:schema:qos-change-result:v1
      - sessionRef: host-context::urn:connectionagent:context:session-ref:v1
    evidence:
      requires:
        result:
          - mas.qos.change
    evaluator:
      type: cel
      expression: result.status == "APPLIED" &&
        result.sessionRef == sessionRef
~~~

规则：

- `parameters` 是非空有序列表；每个成员必须是单键映射，键为参数名，值为 Primitive Type 或精确 Schema 引用。同一 Predicate 内参数名唯一。
- `evidence.requires` 只能引用已声明参数；Evidence 保证必须来自正式 Owner / Package 契约，不能由作者注释或 Script 创建。
- `evaluator` 恰好一个：`type: cel` 搭配 `expression`，或 `type: script` 搭配 Registry Script ID。
- Precondition / Postcondition 的每个 Predicate Call 必须提供完整有序 arguments，数量和类型与参数签名完全一致。
- Predicate 的结果严格为 PASS / FAIL / UNKNOWN。UNKNOWN 不是 FAIL，也不得提升为 PASS。
- Predicate 不得调用 Tool / Observation、访问网络、文件系统、时钟、随机数或可变全局 Context。

### 8.2 Script Registry

Script 是 Skill Package 根目录共享资源，不属于 `assurance/`。源码位于 `scripts/`，唯一 Registry 位于 `scripts/manifest.yaml`。Registry 每项必须声明：

- `file`：相对 Skill Package 根目录的精确文件路径，必须位于 `scripts/`；
- `entrypoint`：文件中的一个顶层函数名，不接受动态模块名、属性链或命令；
- `purpose`：只能是 `transform` 或 `predicate`，仅约束 CA-SL Assurance 的静态引用位置；
- `inputSchema`：Package 根目录下 `schemas/*.schema.yaml` 的精确路径；
- `outputSchema`：transform 必需，指向 Package 根目录下 `schemas/*.schema.yaml`；predicate 不声明该字段，其输出使用本节固定的 PredicateEvaluationResult 契约。

Script ID 在同一 Package 内唯一且稳定。Registry 不包含 `llmInvocable`、权限开关或调用者名单。

~~~yaml
scripts:
  normalize-qos:
    file: scripts/normalize_qos.py
    entrypoint: run
    purpose: transform
    inputSchema: schemas/normalize-qos-input.schema.yaml
    outputSchema: schemas/normalize-qos-output.schema.yaml

  qos-is-valid:
    file: scripts/qos_is_valid.py
    entrypoint: evaluate
    purpose: predicate
    inputSchema: schemas/qos-valid-input.schema.yaml
~~~

### 8.3 Script 输入、Evidence 与输出契约

**Transform Script**

- Procedure 的 `operation.script` 只能引用 `purpose=transform`。
- 具名 `arguments` 按 Script `inputSchema` 的属性名组装为一个 JSON Object；Host 在调用前校验完整输入 Schema。
- Runner 调用唯一入口 `run(input: JSONValue) -> JSONValue`；正常返回值必须通过 Registry 的 `outputSchema`，通过后才产生 Operation SUCCEEDED 和 `<node-id>.operation.output`。
- Script 不得自行读取 Context、文件或环境；所需数据必须通过 arguments 显式传入。

**Predicate Script**

- Predicate 的 `evaluator.script` 只能引用 `purpose=predicate`。
- Predicate 的有序 arguments 按 `Predicate.parameters` 的参数名组装为 JSON Object；Host 额外注入只读保留命名空间 `evidence`。业务参数不得命名为 `evidence`。
- `input.evidence` 的形状固定为 `{ parameterName: { refs: string[] } }`；每个 Predicate 参数都具有一个 `refs` 数组，没有适用 Evidence 时为空数组。Registry 的 predicate `inputSchema` 必须描述全部业务参数和该保留 Evidence projection；它只包含 Runtime 已附加到本次 Predicate 调用的 Evidence Ref，不包含可由 Script 创建的证明。
- 唯一入口为 `evaluate(input: PredicateInput) -> PredicateEvaluationResult`。PredicateInput 包含声明的业务参数和 Host 注入的 Evidence projection。
- PredicateEvaluationResult 固定为闭合 JSON Object：`result` 为 PASS / FAIL / UNKNOWN，`reasonCode` 为非空字符串，`evidenceUsed` 为字符串数组。缺失字段、额外字段、非法枚举或类型错误均为无效结果。
- Runtime 在路由前检查 `evidenceUsed` 中每个 Ref 是否属于本次输入 `input.evidence.<parameter>.refs` 的并集。Script 不得创建、重绑、扩大或伪造 Evidence；LLM 直接调用 Predicate Script 时 Host 注入空 Evidence projection，因此 `evidenceUsed` 必须为空。
- CEL Predicate 与 Script Predicate 使用相同 PASS / FAIL / UNKNOWN 语义和 Runtime Evidence 检查。

**LLM 与确定性执行的统一调用能力**

- Host-owned system Capability `host.skill-script.execute` 对当前 Skill Registry 中登记的全部 Script ID 开放，不按 `purpose` 过滤；LLM、Procedure 和 Predicate 使用同一 Script Runner、同一脚本字节、Registry 和 I/O Schema。
- Action 输入固定为 `scriptId` 与 JSON `input`。Transform 的 input 按 Registry `inputSchema` 验证；Predicate 的 input 仅包含其业务参数，Host 追加空的只读 Evidence projection。模型不得提交 Evidence、file、entrypoint、模块名、函数名、代码、解释器参数或任意命令。
- LLM 调用 Predicate Script 的返回值只是普通计算结果，不会代替 Assurance Predicate 阶段，不产生 Evidence，也不能单独证明 Goal。只有 Runtime 执行 Procedure 中已链接的 Predicate 调用，才会把结果纳入该阶段聚合和路由。
- 不存在逐脚本 LLM 可调用标记，不存在 `scriptExecution.llmEnabled` 或其他 LLM 专用开关。Registry 登记即表示脚本属于当前 Skill 的共享本地计算能力。
- `purpose` 只约束 Assurance 静态引用：`operation.script` 只能引用 transform；Predicate evaluator 只能引用 predicate。它不限制 LLM 的 Script ID 调用范围。

### 8.4 Script 执行错误与纯本地边界

- Registry 缺失、字段不完整、路径越界、入口不唯一或 Schema 无效：导入 / Compiler 阶段拒绝，诊断 `SCRIPT_REGISTRY_INVALID` 或 `SCRIPT_CONTRACT_INVALID`，不产生可执行 Artifact。
- Script ID 不存在或不属于当前 Package snapshot：调用前拒绝，诊断 `SCRIPT_NOT_FOUND`。
- 输入不符合 inputSchema：拒绝执行，诊断 `INPUT_VALIDATION_FAILED`；不调用 entrypoint、不产生 output。
- Transform entrypoint 抛出未处理异常：诊断 `SCRIPT_EXECUTION_FAILED`，该 Operation 阶段产生 FAILED，无成功 output。
- Transform 超过 Host 固定的单次 Script 执行预算（Demo 默认 5000ms，且不得超过 Run 剩余 Deadline）：诊断 `SCRIPT_TIMEOUT`，该 Operation 阶段产生 FAILED，无成功 output。Run 全局 Deadline / Cancellation 优先，按 Runtime 全局停止处理。
- Transform 正常返回但不符合 outputSchema：诊断 `OUTPUT_SCHEMA_INVALID`，隔离输出，该 Operation 阶段产生 FAILED。
- Predicate Script 抛异常、超时、返回值不符合 PredicateEvaluationResult 或 Evidence Ref 校验失败：分别记录 `SCRIPT_EXECUTION_FAILED`、`SCRIPT_TIMEOUT`、`PREDICATE_RESULT_INVALID`、`PREDICATE_EVIDENCE_INVALID`；该 Predicate 结果为 UNKNOWN，不得产生 PASS。
- 普通 LLM Script Action 发生上述错误时，Action 返回明确失败诊断，不产生业务 Capability Outcome / Evidence，不改变 Run 的业务成功状态。

所有 Script 必须是确定性、无外部副作用的本地计算：不得访问网络、任意宿主文件系统、子进程、环境秘密、时钟、随机数或动态加载；不得调用 Tool / Capability、Plugin 或 Owner，也不得制造 Receipt、Commit Proof 或 Evidence。需要外部副作用时必须调用正式业务 Capability。Host Script Execution 是受限的包内入口调用，不是模型提供代码的 Python REPL，也不构成生产级恶意代码隔离或 Admission。

## 9. Contract.when 与 Skill 选择

`when` 是 `assurance/contract.yaml` 的可选顶层 CEL 字段，仅当 Skill 存在有效 `assurance/` 时允许声明。它不属于 SKILL.md Front Matter、Procedure、PredicateSet、Precondition 或 Postcondition。无 Assurance Skill 没有 Contract，不声明 `when`；SKILL.md Front Matter 出现 `when` 必须拒绝。表达式必须是纯表达式，静态结果类型必须为 bool。

允许的变量只有：
- event.type：Host 验证后的规范化 Event 类型字符串；
- input：当前规范化 Event payload，静态类型来自本 Skill 的 requestSchema。

when 不得读取 Context、Tool Result、Observation、Evidence、环境变量、时钟或可变 Host 状态；不得调用 Tool、查询网络或产生副作用。

1.6.0 CEL Profile（本设计冻结候选）：
- 允许布尔常量、确定性标量常量、静态字段点访问、括号、!、&&、||、==、!=、同数值类型比较、has(x.field)、size(x)。
- has 仅检查已声明属性是否存在；size 仅适用于 string / array。
- 可空属性读取必须有同一短路表达式中的非 null 守卫；可选字段必须有 has 守卫。
- 禁止宏 / 推导式、动态索引、切片、对象构造、动态成员名、反射、自定义函数、时间、随机数和外部数据。
- int64 与 double 不隐式混合；溢出、非有限值或不能证明类型安全时拒绝或在运行期 UNKNOWN。
- input 任一字段被引用时必须声明 requestSchema；否则 CEL_INVALID。

选择顺序：
1. 先解析精确 Continuation；Continuation 使用原 Run 的 Skill / Artifact / Capability Binding，不重新选择或重新求值 when。
2. 对每个已导入 Assurance Skill，先验证其 requestSchema（若声明），再求值 when。
3. when=true 集合恰有一个时直接选择；多个时仅允许 LLM 在精确 true 集合内消歧。
4. 没有显式 true 匹配时，未声明 when 的有效 Skill 构成语义候选集合；集合为空则停止或请求输入。
5. when=false 或运行期求值错误的 Skill 必须排除，不能重新加入未声明 when 的候选集合。
6. 模型提出候选集合外的 Skill ID 必须拒绝。不得走 unbound Generic Agent fallback。

## 10. 异步 Operation 与 Host Runtime 控制边界

**CA-SL 1.6.0 不定义 Skill 层的 `wait`、`await`、polling Node、Wait-only Node、`wait.output` 或 Wait 专用 timeout route。** Procedure 源码中出现这些字段或结构必须作为未知字段 / 不支持语法拒绝。

异步协议交互属于执行该协议动作的 Tool / Provider / SMF Operation。负责该动作的 Operation 必须在返回最终结果时提供规范化输出和适用 Evidence；Procedure 只在该 Operation 返回最终 Outcome 后继续推进。不得把一个尚未完成的协议动作拆成作者级 Wait Loop，也不得要求 Skill 作者自行轮询。

Host / Runtime 仍负责 Deadline、Cancellation、Correlation、Budget、UNKNOWN、迟到结果责任和必要的 Reconcile；READ / Observation 仍通过已声明并授权的普通 READ Capability 执行。这些是 Runtime 控制和受治理查询，不是 Skill 作者定义的 Wait 语法或额外阶段。

例如，N4 Session 建立、RAN signaling / adoption 和 N4 forwarding 修改均属于对应 SMF / Provider Operation 的内部完成责任。具体真实 Tool / Owner 契约必须由其发布者确认；本节不虚构 callable 名称或产品实现状态。

## 11. Observation、Evidence、Outcome 与恢复

Observation 是只读事实查询，必须保留 Producer、Scope、Correlation、Freshness 和来源；查询失败、来源不匹配、Schema 无效或证据不足不得构造成功事实。

Evidence 是业务事实的可信来源依据，不是业务 Payload，也不能由模型文本、普通布尔值或 Artifact 存在性替代。Evidence Descriptor / Guarantee 由可信 Owner / Package 发布；Host / Runtime 按契约验证，Skill Script 不得创建或扩大 Evidence。

Mutation 提交状态：
- COMMITTED：必须有精确绑定原始 Invocation 的 Owner Receipt / Commit Proof。
- NOT_COMMITTED：必须有 Owner 对未发生副作用及适用失败类别的证明。
- UNKNOWN：可能已发生副作用但无法证明终态；保持 UNKNOWN，禁止重新发起同一 Mutation。

Reconcile 仅由 Runtime Coordinator 使用原 Mutation 的 originalInvocationId、Scope、Correlation 和受信内部绑定执行；不重放业务 Mutation，不由 Skill / LLM 直接调用。Receipt Query 是普通受控 READ。

Procedure / Runtime Outcome 至少区分：
- Predicate：PASS / FAIL / UNKNOWN。
- 普通调用：SUCCEEDED / FAILED；Runtime 可产生 DENIED / UNKNOWN。
- Mutation：另可有 NOT_COMMITTED / OUTCOME_UNKNOWN；受信恢复已提交但没有承诺普通成功输出时可产生 Runtime COMMITTED。
- Invocation 终态：SUCCEEDED / FAILED / UNRESOLVED / SAFE_STOPPED。

Owner 不得声明 Runtime 保留的 DENIED、OUTCOME_UNKNOWN、COMMITTED 或 Invocation 终态。未知 Owner Outcome 必须隔离并 fail-closed。

## 12. Request Schema / CEL 的 JSON Schema Profile

本地 Request Schema 采用 JSON Schema Draft 2020-12 的显式有限子集；正式发布前由 ca-skills / Compiler 在 Schema / Golden 冻结关键字集合。允许的本地断言关键字：`$ref`、`type`、`properties`、`required`、`additionalProperties`、`items`、`minItems`、`maxItems`、`minLength`、`maxLength`、`minimum`、`maximum`、`exclusiveMinimum`、`exclusiveMaximum`、`enum`、`const`。

允许的本地非断言注解：`$schema`、`$id`、`title`、`description`、`default`、`examples`。default 不得合成输入值。本地 G.4 不支持 `$defs`、`definitions`、`allOf`、`anyOf`、`oneOf`、`not`、`if/then/else`、`pattern`、`patternProperties`、`unevaluatedProperties`、`contains`、`prefixItems`、`format`、动态引用和未声明扩展关键字。

- `type` 仅允许单值 string / integer / number / boolean / object / array / null，或恰好两个成员的 [T, "null"]。
- `additionalProperties` 只允许 true / false；用于 SourcePath 的本地对象必须闭合并声明 additionalProperties=false。
- `items` 仅允许单一 Schema，不允许 tuple 数组。
- 本地 G.4 引用必须解析到精确 Schema ID 和受信依赖快照；循环引用拒绝。

### 12.1 显式 OpenAPI 3.0 外部类型引用（IR-009）

CA-SL 1.6.0 增加受限的跨 dialect 引用入口，不是把 OpenAPI 3.0 并入 G.4：

1. `requestSchema` 始终指向 Skill Package 根目录下由 Skill 自己拥有的 `.schema.yaml` 入口文件。入口文件有且只有两种形式：**本地 G.4 根**（根及本地节点均遵循 G.4，根对象必须闭合并声明 `additionalProperties: false`）；或**OAS3 根引用别名**（文件内容恰好只有一个 `$ref`，指向已 pin Source Bundle 中精确的 OAS 3.0 `components/schemas`，不含 `type`、`properties`、`required`、`additionalProperties` 等兄弟关键字）。后者是 Package-owned 引用入口，但目标 Schema 根按 OAS 3.0 dialect 解释，不是 G.4 对象根。不得为满足 G.4 闭合要求在外部目标周围合成 wrapper 或复制字段。
2. 仅当 Skill 显式声明并锁定 OpenAMSM OpenAPI Source Bundle dependency 时，OAS3 根引用别名或本地 G.4 Schema 节点才可引用该 Bundle 中精确的 OAS 3.0 `components/schemas` 目标；引用必须绑定唯一 dependency alias、源文件和 JSON Pointer。相对引用以引用所在文件为基准按 RFC 3986 解析；fragment 按 RFC 6901 解码。`../` 只有在规范化后的目标仍位于 pin 的 Source Root 内时才允许。
3. 引用闭包以明确选定的消费根为边界，只递归解析该根可达的 `$ref`。Plugin ingress 的选定面是 operation identity + `requestBody`（当前 `PostSmContexts` 进入 `jsonData`）；Compiler 的选定面是精确 Schema Component pointer。原始根 YAML 中其他 operation 的引用不自动进入闭包，也不得要求消费端全局 eager resolve；若未来消费 response / callback，必须将其作为额外选定根显式 pin。
4. 外部目标按 OpenAPI 3.0 Schema Object 语义解析，不套用 G.4 白名单。必须保留可达的 `nullable`、`oneOf`、`anyOf`、`allOf`、`format`、`pattern`、`additionalProperties`、`items`、`enum`、`required`、`default` 等语义；不得重写、丢弃、降级或投影。特别是 OAS3 Schema Object 未声明 `additionalProperties` 时，按 OAS 3.0 默认语义处理（允许额外属性），不得补写 `false`。其组合语义分别为：`allOf` 交集（所有子 Schema 均须满足）、`anyOf` 至少一个分支满足、`oneOf` 恰好一个分支满足。
5. `requestSchema` 不得直接引用 Path Item、Operation、RequestBody、Response 或完整 multipart envelope；完整 operation / multipart 由 Plugin 原生 OAS3 ingress consumer 负责。NAS / NGAP binary slot 不构成解码后字段 Schema。
6. Resolver 必须显式跟踪每个节点的 dialect：本地 G.4 节点按 G.4 解析；进入 pin 后的 OAS3 目标后，其所有可达 `$ref` 均继续按同一 OAS3 Source Bundle / OAS 3.0 dialect 解析。OAS3 闭包不得反向引用 Skill-local G.4 文件，不得跳到其他 dependency 或 Source Bundle。禁止任意网络 URL、dynamic latest、未声明依赖、绝对路径、规范化后逃出 pin Source Root 的路径、Bundle 外文件、未解析 pointer、跨 OpenAMSM commit 混源和循环闭包；运行期不得下载未锁定资源。仅选定闭包内的未解析引用构成错误，闭包外未选定 operation 的引用不构成当前消费失败。
7. Compiler / Host 必须采用 dialect-aware Resolver / Validator。CEL 静态类型推导对 `anyOf` / `oneOf` 只无条件暴露在每个可满足分支中均声明、均列入 `required` 且类型一致的字段；其他字段必须按 optional 建模，不得无条件访问。若在同一左到右 `&&` 表达式中先通过 `has(input.field)` 守卫，则右侧可基于 path-sensitive short-circuit facts 安全读取该字段；无守卫时拒绝。`allOf` 按交集合并属性约束和 required 集合，冲突类型拒绝；`nullable` 的 Null 与 Missing 必须区分。分支可用性不能证明时禁止猜测。
8. 可达 OAS3 Schema 出现尚未支持的关键字 / 语义时，以稳定 `SCHEMA_INVALID` 失败并输出文件 / pointer / SourcePath；不得静默忽略或生成部分 Artifact。
9. dependency alias、URI / pointer wire 编码、Source Bundle identity 与 Lock 字段由 ca-skills / Compiler Owner 在正式 CA-SL 1.6.0 Schema / Golden 冻结；本设计不预造机器字段名。

此规则只解决原版 OpenAPI 组件的精确类型引用；不允许把完整 SBI multipart 复制进 Skill，不让 when 调用 Codec，也不改变 Host Context 只能通过 `Contract.contexts` 引用的约束。

**PostSmContexts 的真实输入字段核对（固定 OpenAMSM 来源）：** Plugin 从 TS 29.502 `PostSmContexts.requestBody` 的 `multipart/related` 中提取 `jsonData`；该 JSON 对象引用 `#/components/schemas/SmContextCreateData`，因此规范化给 CEL 的 `input` 根对象就是 `SmContextCreateData`，`requestType` 的路径为 `input.requestType`。固定原版 `SmContextCreateData.requestType` 引用同文件 `#/components/schemas/RequestType`；`RequestType` 是字符串类型，枚举包含 `INITIAL_REQUEST`、`EXISTING_PDU_SESSION`、`INITIAL_EMERGENCY_REQUEST`、`EXISTING_EMERGENCY_PDU_SESSION`，并保留 OAS3 的未来字符串扩展分支。该属性不在 `SmContextCreateData.required` 列表中，是可选字段；因此正例必须先用 `has(input.requestType)` 守卫，再比较字符串 `"INITIAL_REQUEST"`。未守卫直接读取可选字段必须得到 `CEL_INVALID`；比较整数仍是类型错误。固定来源为 OpenAMSM commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`、文件 `upstream/openamsm/lib/sbi/support/r19-20260402-openapitools-7.20.0/standard/TS29502_Nsmf_PDUSession.yaml`、Git blob `3572be0315a782691ce8b5546b7bc1d5b22fcd64`。Skill 的 `requestSchema` 入口文件仍由 Skill 自己拥有；它可以是仅含 `$ref` 的引用别名，直接指向精确 OAS3 Component。原件不复制、不重写、不投影。

## 13. 静态检查与稳定诊断

Compiler 必须先安全解析 YAML，再建立统一 AST / SourcePath，随后执行结构、字段、标识符、依赖、Schema、Capability Link、Procedure Graph、CEL、Predicate / Evidence 和 Script Registry / Script Contract 检查。未知字段、重复 YAML Key、自定义 Tag、循环 Alias、未知根类型和不确定标量必须拒绝。

最低诊断集合：

| 类别 | 稳定诊断 |
|---|---|
| YAML / 字段 | YAML_PARSE_ERROR、UNKNOWN_FIELD、DUPLICATE_ID、IDENTIFIER_INVALID |
| Contract / Package | REQUEST_SCHEMA_MISSING、REQUEST_SCHEMA_INVALID、CONTEXT_SCHEMA_UNDECLARED、CONTEXT_SCHEMA_MISMATCH、DEPENDENCY_SNAPSHOT_MISSING、DEPENDENCY_ID_MISMATCH、SCHEMA_MISSING、SCHEMA_INVALID |
| Capability Link | CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_GRANT_UNUSED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH、CAPABILITY_BINDING_MISSING |
| Procedure / SourcePath | PROCEDURE_START_MISSING、NODE_ID_RESERVED、CONTROL_FLOW_CYCLE、CONTROL_FLOW_DANGLING、CONTROL_FLOW_AMBIGUOUS、SOURCE_PATH_INVALID、SOURCE_NOT_AVAILABLE、INPUT_TYPE_MISMATCH、INPUT_NULLABILITY_MISMATCH |
| Predicate / Evidence | PREDICATE_GROUP_INVALID、PREDICATE_ARITY_MISMATCH、PREDICATE_TYPE_MISMATCH、PREDICATE_EVIDENCE_REQUIRED、PREDICATE_EVIDENCE_UNSATISFIABLE、EVIDENCE_GUARANTEE_LINK_INVALID |
| CEL / when | CEL_INVALID |
| Script | SCRIPT_REGISTRY_INVALID、SCRIPT_CONTRACT_INVALID、SCRIPT_NOT_FOUND、SCRIPT_EXECUTION_FAILED、SCRIPT_TIMEOUT、INPUT_VALIDATION_FAILED、OUTPUT_SCHEMA_INVALID、PREDICATE_RESULT_INVALID、PREDICATE_EVIDENCE_INVALID |
| Outcome / Reconcile | ROUTE_OUTCOME_MISSING、ROUTE_OUTCOME_UNKNOWN、ROUTE_NORMAL_OUTCOME_NOT_ALLOWED、FINAL_POSTCONDITION_MISSING、SUCCESS_BYPASSES_FINAL_POSTCONDITION、RECONCILE_CONTRACT_INVALID、RETRY_CONTRACT_INVALID |

诊断必须带 SourcePath / 行列位置、稳定 Code、简短原因和必要的依赖 / Node / Capability 上下文。诊断失败不得产生部分 Runtime Artifact。未使用依赖可以警告；不可达 Node 可以警告，但所有 Node 仍须通过语法和链接检查。

## 14. Package、Compiler 与 Runtime 的边界

- CA-SL 只定义作者源语义；Compiler 定义 Check / Link / Build / Verify 和 Runtime Artifact。
- Interface Package 可以只导出 Schema；Schema-only Package 的 Capability / Callable exports 数量均为零是合法情况。
- Capability Package 必须满足一对一；Owner 的 internal-only Reconcile 不属于 Skill-facing exports。
- 新 Runtime Artifact 必须包含已检查 Capability Binding、Request Schema 根与完整闭包、when CheckedExpr / DescriptorSet（若有）、Procedure、Script Registry 中被引用的精确 Script entrypoint / Schema 资源闭包及可执行文件清单；Bundle 同时保留供 LLM 读取的共享资源原始文件。精确字段与 API 由 EC02 / SR-013 的 Compiler 契约冻结。无 Assurance 包不生成 Runtime Artifact，但其共享资源仍随 Bundle 发布并由 Host 导入校验。
- Agent 不内置 Compiler，不调用 Check / Build / Verify；只导入正式发布的 1.6.0 Bundle。
- Skill Studio 只编辑 1.6.0；Package Explorer 以 Capability 为唯一作者可见能力导航，不显示平级 Tools / Operations / Callable 树。
- Host Context Package 的源码身份、上传来源和导入快照属于 Studio Project Lock / Import Provenance，不是 Package Manifest 的额外字段；不得增加 sourceStatus、包级 hash、签名或 Trust Registry 来弥补。
- Host 提供只读 system Capability `host.skill-resource.read`，供当前 Run 的 LLM 按需读取当前 Skill Package snapshot 内的文本资源。请求只含 Package-relative `path`；`skillId` 与 snapshot 由 Host 从当前 Run 绑定，不接受模型指定。
- Resource Read 允许 `SKILL.md`、`assurance/`（存在时）、`schemas/`、`scripts/`、`references/`、`assets/` 中的已导入文件；拒绝绝对路径、`..`、反斜杠、符号链接逃逸、Package 外路径、未登记文件和跨 Skill 读取。
- 仅返回受支持 UTF-8 文本资源；单文件读取上限为 1 MiB，超限完整拒绝、不截断。响应包含精确相对路径、媒体类型、原始文本内容和字节数。
- 稳定拒绝诊断：`RESOURCE_PATH_INVALID`、`RESOURCE_NOT_FOUND`、`RESOURCE_TOO_LARGE`、`RESOURCE_MEDIA_TYPE_UNSUPPORTED`、`RESOURCE_SNAPSHOT_UNAVAILABLE`。该 Action 只读、不属于业务 Capability，不改变 Capability Scope，不通过宿主文件系统路径暴露 Package 内容。

## 15. 安全、版本与不兼容

1. 新 Compiler 必须先固定唯一语言目标再解析；只接受 CA-SL 1.6.0。
2. languageTarget 的中央建议值为 connectionagent.io/v1.6.0；ca-skills 与 Compiler 正式发布必须采用经评审批准的同一值，不得分别发明别名。
3. 1.6.0 与旧 v1alpha5 / v1alpha6 候选完全不兼容。新系统拒绝旧源、旧 DTO、旧 Artifact、旧 Bundle 和未知 languageTarget。
4. 不提供转换器、迁移命令、旧语法分支、fallback 或混合 Catalog；旧 Skill 由作者按 1.6.0 重新编写、重新 Check / Build / Verify / Bundle。
5. 不增加生产 Admission、签名、额外摘要、Trust Registry、复杂 IAM 或 Agent 内置 Compiler。
6. CA-SL 规范 Release、Compiler Release、Owner / Provider Package Release、Bundle Release、Agent / Studio 消费验收是独立门槛；一个通过不得替代另一个。

## 16. 1.6.0 最小正负符合性矩阵

| 输入 / 场景 | 必需结果 |
|---|---|
| 无 Assurance、无共享资源 | 可导入；仅 LLM-guided；不调用 Compiler |
| 无 Assurance、含 schemas/ 与 scripts/manifest.yaml | 可导入；仅 LLM-guided；Host 校验共享资源；提供 Host Resource Read；Script Registry 非空时提供 Host Script Execution Capability，且全部登记 Script 可调用；不调用 Compiler |
| 完整有效 Assurance | 只有正式 1.6.0 Compiler Build / Verify / Bundle 后才可导入 |
| Assurance 目录缺文件或无效 | 拒绝；不得降级 |
| Contract 只声明 Capability，唯一映射 Callable | Link 通过 |
| Capability 零 / 多 Callable，Callable 多 Capability | 静态拒绝，不生成部分 Artifact |
| Operation 引用 observation kind 或 Observation 引用 MUTATION | 静态拒绝 |
| 仅 event.type 的 when，无 requestSchema | 可通过 CEL 静态检查 |
| when 引用 input 但无 requestSchema | CEL_INVALID |
| `input.requestType` 为可选字段 | 无 `has` 守卫时 `CEL_INVALID`；先 `has(input.requestType)` 再访问时通过类型检查 |
| 3GPP `input.requestType == 1` | CEL 类型不匹配，`CEL_INVALID`，拒绝 |
| OAS3 根引用别名文件恰好只有一个 `$ref`，目标位于 pin 闭包 | 按 OAS3 dialect 验证目标和可达闭包，保留原始默认语义，通过 |
| OAS3 根引用别名文件含 `additionalProperties: false` 等兄弟 Schema 关键字 | `SCHEMA_INVALID`，拒绝；不得把 OAS3 目标投影为 G.4 |
| OAS3 Schema 未声明 `additionalProperties` | 保留 OAS 3.0 默认允许额外属性的语义，不得补写 `false` |
| requestSchema 存在但无 when | Schema 仍验证并发布闭包 |
| Schema-only Package：0 Capability / 0 Callable，含已声明 Schema export | 可作为 Contract.contexts 的 Host Context Schema 依赖；requestSchema 仍必须指向 Skill 自有请求 Schema |
| 未声明依赖却引用 Capability / Schema | 静态拒绝 |
| 多个 when=true | 仅在精确 true 候选集合内消歧 |
| when=false / runtime error | 排除，不重新加入无 when 集合 |
| Procedure 中出现 `wait` / `await` / `wait.output` / polling 语法 | 拒绝为未知字段或不支持语法；异步完成由 Tool / Provider / SMF Operation 与 Host Runtime 负责 |
| 普通 Skill / LLM 调用 MAS.RECONCILE | IPC=0，INTERNAL_RECONCILE_ONLY |
| LLM 调用任意已登记 transform / predicate Script | 通过同一 Host Script Runner；Predicate 返回值仅为普通计算结果，不构成 Assurance 阶段 PASS / Evidence |
| 模型提交任意 Python 代码、路径或未登记 Script ID | Runtime 在 Script Runner 前拒绝；不创建进程、不执行代码 |
| 旧 v1alpha5 / Development Artifact / Bundle | 新 Compiler / Agent / Studio 明确拒绝 |

## 17. v1alpha5 完整规范的逐项处置表

此表用于证明迁移审查没有把旧规范中的关键语义静默丢弃。它不是旧语法兼容表；每一项在 1.6.0 中按本文件的新字段 / 新身份重新定义。

| 历史 v1alpha5 来源范围 | 1.6.0 处置 |
|---|---|
| §1～9 背景、术语、责任边界、Schema / ToolCatalog / Capability | 采用核心概念；重写 Capability / Callable 一对一与 Package 所有权；移除旧作者 Callable 引用 |
| §10～11 文件、YAML、Contract | 重写为本文件 §2～5；无 goal 字段；新增 contexts；Capability-only；when / requestSchema 仍为 Contract 顶层 |
| §12～14 Procedure、Arguments、PredicateSet | 采用静态 DAG / 四阶段 / 显式 arguments / PredicateSet；重写 Capability 引用和 Procedure.inputs |
| §15～18 Observation、Evidence、Fact | 采用只读 Observation、Owner Evidence、Scope / Correlation / Freshness 与 UNKNOWN 不提升规则 |
| §19～25 Invocation、READ / MUTATION、Reconcile、Outcome、错误 | 采用 Invocation、READ / MUTATION、Outcome 和恢复语义；Skill 层不定义 Wait / await / polling；异步由 Operation 与 Host Runtime continuation 负责；Reconcile 仅内部 |
| §26～31 5GC 教学示例 | 不作为新规范示例；由当前 OpenAMSM Create / Modify / Release 1.6.0 Capability 示例替代 |
| §32～35 Script、Cases、Dependencies、Studio | 采用纯本地 Script、显式依赖闭包与 LSP；移除旧 Alias::Callable |
| §36～41 参考语言与定位 | 仅资料性参考，不产生作者语义 |
| §42～45 安全、版本、冻结 | 重写为 1.6.0 单版本、无兼容、无迁移 |
| §46～91 技术解释 / 历史裁决 | 作为设计依据审查；有规范效力的内容必须在本文件对应条款中重新表述，不直接引用旧条款作为 1.6.0 规范 |
| 附录 A～K 决策、诊断、符合性、Schema / Evidence / CEL | 逐项审查；本文件 §12～13 重新冻结当前 Schema / CEL / 诊断；未纳入的历史诊断不自动成为 1.6.0 要求 |
| 附录 L Node-entry Event Wait | **不纳入 CA-SL 1.6.0 Skill 作者语法**；不定义 Wait Node、wait 字段、wait.output、await 或 polling。异步协议完成由 Tool / Provider / SMF Operation 与 Host Runtime 负责；不得从历史附录恢复作者级 Wait 语法 |
| 附录 M Optional Assurance / when | 采用 Optional Assurance 与 `assurance/contract.yaml` 顶层 `when` 选择模型；按本文件 §2、§4、§9、§16 重新定义 1.6.0 |

任何历史条款未明确映射到本文件、F02、F03.05、F04、F05、F06、F08、F09 或 EC02 的规范性要求，必须在独立评审中作为遗漏处理；不得由实现者自行沿用旧语义。

## 18. 评审与发布门槛

- 当前是中央完整设计稿，必须经独立设计评审后才能冻结。
- ca-skills 负责发布 1.6.0 作者 Schema、完整规范、机器 languageTarget、Golden 和正式 Release Record。
- Compiler 负责新 Parser / AST / Check / Link / BuildRequest / BuildResult / Artifact / Verify；SR-013 / Compiler Issue #61 负责实现与产品证据。
- Owner / Provider 分别发布满足一对一映射的 Package；Host Context Publisher 只发布 Schema-only Package。
- SR-027 负责新 Bundle；SR-004～006 负责导入、Catalog、Resolver；F04 负责 Runtime Action Boundary；F09 / SR-016 负责 Studio。
- 未正式发布前，所有产品实现和运行验收保持 NOT_RELEASED / NOT_RUN；本设计通过不代表实施 READY。

## 19. OpenAMSM 原版 OpenAPI 直接引用与 Skill 分阶段输入（IR-009）

**原版来源与选定闭包**：SR-031 逐字节代发布 OpenAMSM 实际支持的 OAS 3.0 YAML。当前核验入口为 TS 29.502 `PostSmContexts.requestBody` → `multipart/related` → `jsonData` → `#/components/schemas/SmContextCreateData`；在固定 OpenAMSM commit 上，该 Schema Component 的可达闭包为 4 份原版 YAML / 102 个 Schema Component，不复制全部 472 份 standard YAML。原始文件和相对 `$ref` 一字不改。Source Bundle 不是 Capability Package，也不是自动的 G.4 Schema-only Package。未选定 operation 的 refs 不要求 eager resolve；消费端只解析显式 pin 的选定闭包。

**直接引用**：Skill-owned `requestSchema` 入口文件可采用本地 G.4 闭合对象根，或仅含一个 `$ref` 的 OAS3 根引用别名。别名直接指向显式 pin Source Bundle 中原版文件的精确 `#/components/schemas/...`，不附加 G.4 siblings；Compiler 从该目标开始按 OAS 3.0 Schema Object dialect 解析整个外部可达闭包，保留 `allOf` / `anyOf` / `oneOf` / `nullable` / `pattern` / `additionalProperties` / `format` 等原语义，包括未声明 `additionalProperties` 时 OAS3 的默认允许语义；不生成 Adapter / Projection、不复制字段或改写原件。缺少 Resolver、运行期 Validator 或 Golden 时相关 AC BLOCKED / NOT_RUN。

**Ingress 与执行期分离**：Plugin T0 依据 TS 29.502 operation 的选定 `requestBody` 校验 SBI JSON / multipart / Content-ID / N1/N2/N2 Ext1 binary slots；T1 `when` 只读取已规范化且到场的 Event / Request 字段。对 `PostSmContexts`，`n1SmMsg.contentId`、`n2SmInfo.contentId`、`n2SmInfoExt1.contentId` 必须分别匹配 N1、N2、N2 Ext1 对应 binary part 的 `Content-ID`；引用目标缺失、重复 ID、错槽或媒体类型不符均拒绝。未被 JSON 引用的 part 不得交给 Codec；额外或未引用 part 的拒绝 / 忽略必须由选定 ingress profile 明确规定，不从 OpenAPI Schema 隐含推断。被选 Skill 的 Procedure 在 T2 才能调用授权 Codec READ，消费 Provider 正式 Output Schema。NAS-only PDU Session Type / SSC mode 不得在 T1 无来源时成为必填；Codec Result 不能替代 Owner Receipt / Commit Proof。

**NAS / NGAP**：TS 29.502 binary slot 不定义 NAS IE / NGAP ASN.1 字段。Result Schema 由 SR-026 Provider 基于 OpenAMSM 实际支持的 TS 24.501 / TS 38.413 来源和已资格化消息 Profile 发布；未发布的消息类型保持 BLOCKED，不伪造官方 YAML。

Host Context Schema-only Package 仍只经 `Contract.contexts` 引用，与 OpenAPI Source Bundle 不混同。CA-SL 1.6.0 唯一新语言，不提供旧版兼容。
## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | GPT-6（ChatGPT） | 全文 | 建立 CA-SL 1.6.0 完整作者语言规范中央设计稿，定义 Capability-only、contexts、when、Request Schema、Procedure、PredicateSet、Wait、Evidence、Outcome、无兼容及 v1alpha5 全文逐项处置 | 版本基线与 SR-029 局部语法草案不足以替代完整语言规范，防止 Harness 从历史文件自行推断 | Issue #12/#40；IR-008；SR-029、SR-013、SR-027 |
| 2026-11-26 | 0.1.1 | GPT-6（ChatGPT） | §4、§16、修订记录 | 明确 requestSchema 指向 Skill 自有 Schema，Host Context Schema-only Package 仅通过 Contract.contexts 引用 | 避免将 Host Context Package 当作 Request Schema 根，统一 Contract.requestSchema 与 contexts 的不同所有权 | Issue #12/#40；SR-029、SR-030；PR #46 |
| 2026-11-26 | 0.1.2 | GPT-6（ChatGPT） | 文档头、修订记录 | 补齐根 Agent.md review_scope 标准声明，保持完整规范进入独立评审时的统一治理范围 | 避免正式 CA-SL 规范稿因缺少全局评审范围而无法生成 Review Context | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.1.3 | ChatGPT / GPT-6 | 3GPP Schema 与阶段输入补充 | 明确公共 Schema-only 导出、选择期 Request 与执行期 Codec Result 的 Link / 业务字段来源 | 关闭 Create 选择前依赖 NAS 解码的循环、固定跨包类型门禁 | IR-009；Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.1.4 | ChatGPT / GPT-6 | 本轮 IR-009 设计修正 | 固定 OpenAMSM 版本 + 原版 YAML 逐字节代发布；显式区分可选 Adapter 与 Provider Codec 输出 | 落实原版 YAML 不得改动、消除误把原版当 G.4 的风险 | Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.1.5 | ChatGPT / GPT-6.2 | §12、§19 | 保留本地 G.4 有限子集，增加 pin 后 OAS3 Schema Component 的 dialect-aware 直接引用；移除强制 Adapter | 遵循原版 OpenAPI 直接引用、不重写标准 | IR-009；Issue #47；SR-013/031 |
| 2026-11-27 | 0.1.6 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | §12.1、§19；§2、§3、§5、§6、§8、§14、§16 | 冻结选定消费面与 lazy `$ref` 闭包；补齐 OAS3 组合 / nullable / pattern / additionalProperties 语义及 Content-ID 到 multipart slot 的精确映射；将 schemas/scripts 提升为 Skill Package 根目录共享资源；定义 YAML Schema 源、Script Registry、Host Script Execution Capability 与 Assurance / LLM 共用资源路径 | 防止对未选定 operation 全局解析，并确保 SBI 二进制引用与 MIME part 一致；修复可选 Assurance 导致 LLM-only Skill 无法使用 Schema / Script 的结构矛盾，禁止模型任意 Python 执行 | Issue #47；SR-031/010/013；EC01/EC02；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.7 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | §12.1、§19；§7～§8 | 将 union 字段推导收紧为每分支 required；明确未引用 multipart part 不得交给 Codec，但是否拒绝由 ingress profile 决定；明确业务 Operation Capability 与 `operation.script` 的互斥语法分支，避免把 Package-local Script 误列为业务 Capability | 避免把可选字段误判为必有，避免超出原版 OAS3 schema 的额外拒绝；保持 Capability-only 授权模型，同时让 Procedure 明确引用共享 Script Registry | Issue #47；SR-031/010/013；EC01/EC02；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.8 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | §12.1；§2、§7 | 将 Ingress 摘要中的二进制槽明确为 N1/N2/N2 Ext1，与三组 Content-ID 绑定保持一致；统一无 Assurance Package 的术语，避免误读为只能包含 SKILL.md 单文件 | 避免摘要遗漏 N2 Ext1 槽；明确无 Assurance 包仍可携带共享 Schema / Script / references / assets | Issue #47；SR-010/031；EC01/F06；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.1.9 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | §1 Demo 限制；§2、§8、§16 | 明确 Demo 全链路不做 SHA-256 / checksum / digest 内容校验，Source Bundle 只做原始 bytes 比较；删除 `llmInvocable` 与 `scriptExecution.llmEnabled` 双重门禁；LLM、Procedure 和 Predicate 统一调用当前 Package Registry 中的脚本 | 统一语言规范与 Compiler / Provider / ArtifactStore 的 Demo 边界；Demo 不区分脚本调用者权限；保留固定 Package snapshot、精确入口、I/O Schema 和无副作用边界 | Issue #47；SR-010/013/031；EC02/F03.05；Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.2.0 | GPT-6.2（ChatGPT） | §1～§18 | 恢复原有四阶段 DAG / arguments / PredicateSet 结构语法，补齐 Predicate Evidence 与 Script 输入输出 / 异常契约；删除 Skill 层 Node-entry Wait / await / polling；定义 Host Resource Read Action 与完整 Script Registry 调用模型 | 避免作者语法重构和 Wait 回流；使 CA-SL 1.6.0 的机器形状、运行时边界和评审验收闭合 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.2.1 | GPT-6.2（ChatGPT） | §6.1、§8.3、§17 | 修正文法记法，明确 Predicate Script inputSchema 包含 Host Evidence projection，并将 v1alpha5 Node-entry Wait 附录明确裁决为不纳入 1.6.0 | 防止历史 Wait 语义回流，补齐 Predicate 输入 Schema 与原有语法迁移依据 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.2.2 | GPT-6.2（ChatGPT） | §1～§5、§9、EBNF、修订记录 | 将 `when` 定义为有 Assurance Skill 的 SKILL.md Front Matter 扩展字段，从 Contract YAML 中移除；明确无 Assurance Skill 不声明 when | 对齐已确认的 SKILL 入口方案，保证无 Assurance 包不依赖未编译的 CEL；历史错误入口判断，已由 0.2.4 撤销，不构成兼容方案| Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.2.3 | GPT-6.2（ChatGPT） | §1～§5、§9、§12、§19、修订记录 | 合并 CA-Agent Assurance-only SKILL.md Front Matter.when / 无 Assurance 禁用 when 规则与原版 3GPP OpenAPI 3.0 外部 Schema dialect、直接引用和闭包验证 | 保持选择期字段不进入 Contract YAML，同时确保 Compiler 可消费未投影的原版 OpenAPI schema；历史错误入口判断，已由 0.2.4 撤销，不构成兼容方案| Issue #47/#49；IR-008/009；SR-013/031/032 |
| 2026-11-27 | 0.2.4 | GPT-6.2（ChatGPT） | §1～§5、§6.1、§9、§12.1、§17、修订记录 | 恢复 `assurance/contract.yaml` 顶层 `when` 为唯一作者入口；SKILL.md Front Matter 不声明 when；补入 PostSmContexts / SmContextCreateData / RequestType 的固定原版 OpenAPI 字段与字符串枚举证据 | 撤销误引入的 Front Matter 入口，确保 Compiler、作者规范和 3GPP 原版契约一致 | Issue #49；IR-008/009；SR-013/031/032；F02/F08/F09 |

| 2026-11-27 | 0.2.5 | GPT-6.2（ChatGPT） | §4、§5.1、§12.1、§13、§19、修订记录 | 为 3GPP 可选 requestType 增加 has 守卫；定义 Skill-owned 纯 $ref OAS3 根引用别名，明确 G.4 闭合对象与外部 OAS3 dialect 的边界、默认 additionalProperties 语义、Resolver 方向和 Golden 正负例 | 避免可选字段 CEL 访问与原版 OAS3 直接引用被 G.4 根闭合规则迫使投影/复制字段；保持上游原件不变 | Issue #49；IR-008/009；SR-013/031；F08；PR #52 |
