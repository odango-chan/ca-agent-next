# CA-SL 1.6.0 完整语言规范（中央设计稿）

> 文档类型：CA-SL 作者语言规范（中央规范性设计稿）
> 文档版本：0.1.6
> 语言版本：CA-SL 1.6.0
> languageTarget 候选：connectionagent.io/v1.6.0（本设计建议值；发布前由 ca-skills 与 Compiler Owner 在正式 Schema / Golden 中确认）
> 状态：**DRAFT / REVIEW_REQUESTED**；未发布、未冻结、不得作为已发布产品规范
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 修订日期：2026-11-26
> 规范所有者：ca-agent-next（中央设计）；正式作者 Schema / Golden / Release 由 ca-skills 发布
> 关联：IR-003、IR-008；Issue #40、#49；SR-023、SR-029、SR-013、SR-027、SR-032
> 本文局部非目标：Compiler API / Artifact 字段级 Schema、Provider / Owner 发布物字段、Agent Runtime 实现、生产 Admission、签名、Trust Registry、生产 Qualification

本文是 CA-SL 1.6.0 的完整中央作者语言设计稿，覆盖源码角色、Contract、Procedure、PredicateSet、Context、Request Schema、Capability、when、Wait、Evidence、Outcome、静态检查和版本边界。它不是 ca-skills 已发布的语言规范，也不授权下游实现。

历史 [CA-SL v1alpha5 完整语言规范](CA-SL%20v1alpha5完整语言规范.md)及其 Release Record 仅作只读来源审计；不得把本文理解为 v1alpha5 的兼容解析器、别名、自动迁移或双轨实现。新 1.6.0 源码必须按本文重新编写。

## 1. 规范用语、范围与原则

本文中的 MUST / MUST NOT / REQUIRED / SHOULD / SHOULD NOT / MAY 按 RFC 2119 / RFC 8174 理解。未特别说明时，“拒绝”指 Compiler Check / Link 阶段 fail-closed，且不得产生可发布 Runtime Artifact。

CA-SL 1.6.0 定义 Skill 可选 Assurance 的作者语言。它不定义 SKILL.md Front Matter；SKILL.md 使用 Agent Skills Specification。语言负责表达确定性执行契约，不负责 Agent 推理、Plugin 生命周期、Provider 私有实现、Owner 业务状态或 Compiler 的部署。

1. 新作者语言和新产品链唯一目标为 CA-SL **1.6.0**。
2. 新 Parser、Check、Link、Build、Verify、Runtime Artifact、Bundle、Agent Importer / Runtime、Skill Studio / LSP 只支持 1.6.0。
3. 不提供 v1alpha5 / v1alpha6 解析器、别名、语法映射、版本协商、双轨编译、旧 Artifact 导入、自动转换、迁移工具或 fallback。
4. 历史 v1alpha5 文件、Schema、Golden、Release Record 和字节保持只读；其设计可作为重新审查语义的来源，但不是新语言的规范性输入。
5. Skill-facing 接口只声明 Capability。每个公开 Capability 与一个公开 Callable 双向一对一；Callable ID 只存在于 Package / Compiler / Runtime / Provider 内部。
6. Procedure 的 Operation / Observation 是 Node 阶段，不是作者级 Operation ID。
7. Assurance 是可选的；存在但无效时必须拒绝导入，不得降级成 SKILL.md-only Skill。
8. Demo 不增加生产 Admission、签名、额外包级 hash、Trust Registry、复杂 IAM 或完整生产 DFX。

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

- SKILL.md：Agent-facing 身份、用途和指导；不声明业务 Capability Grant、Procedure 或 when。
- schemas/：Skill Package 自有 Schema 资源；LLM 可读取，Host 可用于结构化输入/输出校验，Assurance 可引用。文件使用 YAML 1.2 表示 JSON Schema 数据模型，扩展名为 `.schema.yaml`；JSON Schema 语义仍遵循 §12 的 G.4 Profile。
- scripts/：Skill Package 自有 Python Script 源码；LLM 可读取，Assurance 可引用，LLM 调用则必须经过 Host Script Execution Capability。
- scripts/manifest.yaml：Script ID、精确入口、用途、输入/输出 Schema 和 LLM 可调用标记；它是资源索引，不是第二份 Skill Descriptor，也不授予业务 Capability。
- references/、assets/：按需读取的共享参考资料和静态资源，不是隐式 Runtime 输入。
- assurance/contract.yaml：Skill 选择条件、Request Schema、Context、依赖、业务 Capability Grants、全局前置引用和动作预算。
- assurance/procedure.yaml：唯一入口 Procedure DAG、显式输入绑定、Node 阶段、Wait 和路由。
- assurance/predicates.yaml：可复用 Predicate 定义及其参数 / Evidence 契约；没有 Predicate 时仍须存在合法空 PredicateSet。

没有 assurance/ 的 Skill 仍可携带 schemas/、scripts/、references/ 和 assets/，并仅支持 LLM-guided；若脚本被明确标记为 llmInvocable 且 Host 策略启用，可通过 Host Script Execution Capability 调用。存在 assurance/ 时，contract.yaml、procedure.yaml、predicates.yaml、被引用的共享 Schema / Script、依赖和所有静态语义必须全部有效，才同时具备 Deterministic 与 LLM-guided 两种模式。Assurance 无效时必须拒绝导入，不得静默降级。不得新增 constraint.yaml、activation.yaml、applicability.yaml、第二份 Skill Descriptor 或 Domain Contract Package；predicates.yaml 只描述执行期 Predicate，不参与 Skill 选择。

## 3. 核心术语与所有权

| 术语 | 1.6.0 定义 | 权威来源 |
|---|---|---|
| Skill | SKILL.md 与可选 Assurance 构成的可导入单元 | Skill Package |
| Contract | Skill 选择、公共输入、Context、依赖和 Capability Grant 的唯一作者契约 | contract.yaml |
| Procedure | 静态确定性执行图 | procedure.yaml |
| PredicateSet | 可复用的纯判断定义 | assurance/predicates.yaml |
| Shared Resource | LLM、Host 和可选 Assurance 共用的 Schema / Script / references / assets；资源身份相对 Skill Package 根目录 | Skill Package root |
| Script Registry | Package-local Script ID、入口、purpose、Schema 与 LLM 可调用声明；不授予业务 Capability | scripts/manifest.yaml |
| Host Script Execution Capability | Host-owned system Capability；只执行当前 Skill Registry 中显式允许的 Script ID | Host Runtime / built-in Tools Extension |
| Node | Procedure 图中的执行节点，最多声明四个业务阶段及可选入口 Wait | procedure.yaml |
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
| when | 否 | 选择期纯 CEL 布尔表达式，只能读取 event.type 与当前 Skill requestSchema 的 input |
| precondition | 否 | 单一全局门禁引用，精确为 NodeId.precondition；不是 Predicate 列表 |
| requestSchema | 否 | Skill 公共请求 Schema 根的相对路径；有请求输入时声明 |
| contexts | 否 | 一个映射，集中声明所有 Host Context 名称到精确 Schema 引用；不再建立平级 subject / facts / ingress 顶层字段 |
| dependencies | 否 | Alias → 稳定 Package ID；不得写 Git URL、分支、获取指令或作者自选 Callable |
| capabilities | 否 | Skill 请求的 Capability ID 列表；不接受 Callable ID / Operation ID |
| limits.maxActions | 否 | 正整数业务动作预算上界；Host / Deployment 只能进一步收紧 |

示例：

~~~yaml
when: 'event.type == "nsmf.create-sm-context" && input.requestType == 1'
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

- requestSchema 指向 Skill Package 根目录下的 Skill 自有 Schema 资源，定义规范化 Event payload 的业务输入契约。源文件采用 YAML 1.2 序列化的 JSON Schema 数据模型（`.schema.yaml`）；Compiler 解析为 JSON 数据模型后按 G.4 JSON Schema Profile 校验。Schema 引用路径始终相对 Skill Package 根目录，不相对 assurance/。
- Host 先验证 Plugin Event Schema，再独立验证 Skill Request Schema；两者不是同一 Schema，也不得把完整 3GPP multipart Schema 复制到 Skill。
- requestSchema 根必须是闭合对象，明确 additionalProperties=false；完整 $ref 闭包必须可解析。
- requestSchema 是否存在与 when 是否存在相互独立。只使用 event.type 的 when 不要求 requestSchema；when 访问 input 成员时必须声明 requestSchema。
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
- Node 输出必须通过精确的 NodeId.Stage.output SourcePath 显式传递；Wait 规范化输入使用 NodeId.wait.output SourcePath。
- context、inputs、已声明 Node Producer 和标量字面量之外的根均拒绝。

## 6. Procedure、Node 与四阶段

Procedure 只有一张静态有向无环图（DAG），必须有 start 和 nodes。start 必须引用真实 Node；Node ID 不得与保留根或终态冲突；未知、悬空、循环和歧义路由均阻断构建。

一个 Node 可按固定顺序声明以下业务阶段，每个阶段最多一次：

1. precondition：调用有序 Predicate 列表；全部 PASS 才产生聚合 PASS。
2. operation：二选一调用一个 kind=operation 的公开 Capability（Effect 由目标 Package 决定，可为 READ 或 MUTATION），或引用一个 purpose=transform 的 Package-local Script ID；两者互斥。Script 不是业务 Capability，不进入 contract.capabilities。
3. observation：调用一个 kind=observation 且 Effect=READ 的 Capability；不得产生副作用。
4. postcondition：调用有序 Predicate 列表；全部 PASS 才产生聚合 PASS。

Node 可以省略不适用阶段，但必须至少声明一个业务阶段。阶段按上述顺序执行；正常 Outcome 在非末阶段自动进入下一阶段，末阶段必须显式路由。阶段 routes 属于该阶段，不得跨阶段借用。Procedure 不支持动态生成节点、任意循环、嵌套 Procedure Call 或同名自动绑定。

**成功边规则：** 唯一允许请求 Invocation SUCCEEDED 的边，是一个可达 Postcondition 阶段的聚合 PASS 直接指向 SUCCEEDED。Operation / Observation / Precondition 不得直接证明最终成功；任何分支都不得复用另一条分支的旧 PASS。

## 7. Capability、Callable 与 Plugin 契约

- Contract.capabilities 只声明 Capability ID；Procedure 的 operation / observation 阶段只写 capability。
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

predicates.yaml 定义具名 Predicate。每个 Predicate 声明有序 parameters、可选 Evidence requirements 和唯一 evaluator。每个 Predicate 调用的 arguments 数量与参数顺序必须精确一致。

Predicate 结果严格为：
- PASS：输入和 Evidence 足以支持命题成立；
- FAIL：输入和 Evidence 足以支持命题不成立；
- UNKNOWN：缺失、冲突、过期、Scope 不匹配、来源不可信或求值失败，无法可靠判断。

UNKNOWN 不是 FAIL，也不得提升为 PASS。Predicate 不得调用 Tool / Observation、访问网络、文件系统、时钟、随机数或可变全局 Context。

Script 是 Skill Package 的共享资源，不属于 assurance/。源码放在 `scripts/`，由 `scripts/manifest.yaml` 建立唯一的 package-local Script Registry。Registry 每个条目必须声明：
- `file`：相对 Skill Package 根目录的精确路径，必须位于 `scripts/`；
- `entrypoint`：该文件中的一个顶层函数名，不接受动态模块名、属性链或命令；
- `purpose`：只能是 `transform` 或 `predicate`；
- `inputSchema`：相对 Skill Package 根目录的 `schemas/*.schema.yaml`；
- `outputSchema`：`transform` 必需，引用相对根目录的 `schemas/*.schema.yaml`；`predicate` 不得声明此字段，其结果固定为 PASS / FAIL / UNKNOWN；
- `llmInvocable`：必需布尔值；仅 `purpose=transform` 可以为 true，Predicate Script 必须为 false。

Script ID 在同一 Skill Package 内唯一且稳定。Procedure 的 `operation.script` 只引用 `purpose=transform` 的 Script ID；Predicate 的唯一 `evaluator` 只引用 `purpose=predicate` 的 Script ID。所有 Script 输入和输出均为 JSON 值并按对应 Schema 验证。入口函数分别为 `run(input: JSONValue) -> JSONValue` 与 `evaluate(input: JSONValue) -> PASS|FAIL|UNKNOWN`。

Script Registry 示例：

~~~yaml
scripts:
  normalize-qos:
    file: scripts/normalize_qos.py
    entrypoint: run
    purpose: transform
    inputSchema: schemas/normalize-qos-input.schema.yaml
    outputSchema: schemas/normalize-qos-output.schema.yaml
    llmInvocable: true
  qos-is-valid:
    file: scripts/qos_is_valid.py
    entrypoint: evaluate
    purpose: predicate
    inputSchema: schemas/qos-valid-input.schema.yaml
    llmInvocable: false
~~~

Assurance Procedure 对 transform Script 的引用示例：

~~~yaml
operation:
  script: normalize-qos
  arguments:
    - inputs.qos
~~~

Predicate evaluator 只写 Registry Script ID，不写路径、模块名或函数名。

LLM 可以通过 Host 的只读 Skill Resource Access 读取 `scripts/` 下的源码和 Registry；读取不等于执行。LLM 只能通过 Host-owned system Capability `host.skill-script.execute` 调用 Registry 中 `llmInvocable=true` 的 transform Script，参数固定为 `scriptId` 与 `input`。Host 只解析当前已绑定 Skill 的固定 Package snapshot，并按条目验证输入 Schema、执行精确 entrypoint、验证输出 Schema；模型不得提交文件路径、模块名、函数名、代码、解释器参数或任意命令。Host 逻辑配置 `scriptExecution.llmEnabled` 默认为 false；只有部署显式设为 true，且当前 Skill 存在符合条件的 Script 时，才向模型暴露此 Action。该开关只控制 LLM Action 暴露，不改变 Assurance Procedure 对已编译 transform Script 的内部调用；Host Script Runner 本身仍受 Package Registry 与运行预算约束。

Deterministic Procedure 的 `operation.script` 由 Compiler / Runtime 映射到同一 Host Script Runner；Predicate evaluator 由 Runtime 内部纯求值入口调用，不暴露为 LLM Action。两种调用共享同一份脚本字节、Registry 和 Schema，不复制脚本或生成第二套定义。

所有 Script 必须是确定性、无外部副作用的本地计算：不得访问网络、任意宿主文件系统、子进程、环境秘密、时钟、随机数或动态加载；不得调用 Tool / Capability、Plugin 或 Owner，也不得制造 Receipt、Commit Proof 或 Evidence。需要外部副作用时必须调用正式业务 Capability，不得包进 Script。

Host Script Execution 是受限的包内入口调用，不是模型提供代码的 Python REPL，也不构成生产级恶意代码隔离或 Admission。Demo 按受控 Skill Package 来源处理脚本，并实施明确的入口 allowlist、输入/输出 Schema、超时和资源上限；不得声称具备生产级沙箱安全资格。

## 9. Contract.when 与 Skill 选择

when 是 contract.yaml 顶层可选 CEL 表达式；不属于 Procedure、PredicateSet、Precondition 或 Postcondition。它必须是纯表达式，静态结果类型必须为 bool。

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

## 10. Node-entry Wait

Wait 是可选 Node-entry 控制，不是第五个业务阶段、Wait-only Node、独立 Wait Node 或作者级 await / polling 循环。Wait 发生在目标 Node 的第一个业务阶段之前；事件接受后隐式进入该 Node 的第一个已声明业务阶段。

- Wait 由 Host Runtime 的内部 READ 触发机制执行；它不是 Skill-facing Capability，也不是业务 Mutation。
- Wait 必须引用显式依赖中的 package-scoped Ingress Operation / Event contract；该契约拥有协议来源、服务与操作身份、归一化 Request Schema、认证、Correlation 和重复 / 迟到处理规则。
- Skill 不得声明 payloadSchema、复制协议 Schema、创建全局 EventCatalog 或根据未认证 Body 选择 Schema。
- Wait 输出是 Integration 归一化后的 typed request，使用 NodeId.wait.output SourcePath；不得把原始 HTTP envelope、multipart 原始 bytes 或未授权路径直接交给模型。
- Wait 必须绑定精确 Run、Node occurrence、generation 和 Correlation；SUPI 单独不能被假定为充分唯一标识。
- Wait timeout 使用正的固定时长；只允许 Wait-scoped TIMEOUT 路由。事件接受是隐式正常边，不声明 EVENT_RECEIVED。
- 可选 response.after 将配对协议响应绑定到 Node completion boundary；它独立于 Invocation 最终终态，不能错误地提前发送 3GPP 成功响应。
- Wait 不能创建 Evidence、证明 Predicate 或满足最终成功条件。Event 到达后仍必须执行业务阶段和 Postcondition。
- 现有 Observation-based Runtime Evidence Wait 与 push-driven Event Wait 不同，不得混为同一机制。
- 普通 Skill / LLM 不得把 MUTATION Callable 填为 Wait READ trigger；例如 N1 / N2 确认 Mutation 不能冒充 Wait 触发器。

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
- Wait：TIMEOUT。
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

1. Skill 的 `requestSchema` 根始终由 Skill 自己声明，根及本地 Schema 节点仍遵循上面的 G.4 子集。
2. 仅当 Skill 显式声明并锁定 OpenAMSM OpenAPI Source Bundle dependency 时，本地 Schema 节点才可引用该 Bundle 中精确的 OAS 3.0 `components/schemas` 目标；引用包含源文件与 JSON Pointer，并经 dependency alias 绑定唯一快照。
3. 外部目标按 OpenAPI 3.0 Schema Object 语义解析，不套用 G.4 白名单，不把 `nullable`、`oneOf`、`anyOf`、`allOf`、`format` 重写、丢弃或降级；嵌套 `$ref` 在同一固定 Bundle 闭包中递归解析。
4. `requestSchema` 不得直接引用 Path Item、Operation、RequestBody、Response 或完整 multipart envelope；完整 operation / multipart 由 Plugin 原生 OAS3 ingress consumer 负责。
5. 禁止任意网络 URL、dynamic latest、未声明依赖、路径穿越、Bundle 外文件、未解析 pointer、跨 OpenAMSM commit 混源和循环闭包；运行期不得下载未锁定资源。
6. Compiler / Host 必须采用 dialect-aware Resolver / Validator；CEL 静态类型推导只暴露所有可达分支上类型一致且确定的字段。union 分支类型不一致或字段不确定时禁止猜测。
7. 可达 OAS3 Schema 出现尚未支持的关键字 / 语义时，以稳定 `SCHEMA_INVALID` 失败并输出文件 / pointer / SourcePath；不得静默忽略或生成部分 Artifact。
8. dependency alias、URI / pointer wire 编码、Source Bundle identity 与 Lock 字段由 ca-skills / Compiler Owner 在正式 CA-SL 1.6.0 Schema / Golden 冻结；本设计不预造机器字段名。

此规则只解决原版 OpenAPI 组件的精确类型引用；不允许把完整 SBI multipart 复制进 Skill，不让 when 调用 Codec，也不改变 Host Context 只能通过 `Contract.contexts` 引用的约束。

## 13. 静态检查与稳定诊断

Compiler 必须先安全解析 YAML，再建立统一 AST / SourcePath，随后执行结构、字段、标识符、依赖、Schema、Capability Link、Procedure Graph、CEL、Predicate / Evidence 和 Wait 检查。未知字段、重复 YAML Key、自定义 Tag、循环 Alias、未知根类型和不确定标量必须拒绝。

最低诊断集合：

| 类别 | 稳定诊断 |
|---|---|
| YAML / 字段 | YAML_PARSE_ERROR、UNKNOWN_FIELD、DUPLICATE_ID、IDENTIFIER_INVALID |
| Contract / Package | REQUEST_SCHEMA_MISSING、REQUEST_SCHEMA_INVALID、CONTEXT_SCHEMA_UNDECLARED、CONTEXT_SCHEMA_MISMATCH、DEPENDENCY_SNAPSHOT_MISSING、DEPENDENCY_ID_MISMATCH、SCHEMA_MISSING、SCHEMA_INVALID |
| Capability Link | CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_GRANT_UNUSED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH、CAPABILITY_BINDING_MISSING |
| Procedure / SourcePath | PROCEDURE_START_MISSING、NODE_ID_RESERVED、CONTROL_FLOW_CYCLE、CONTROL_FLOW_DANGLING、CONTROL_FLOW_AMBIGUOUS、SOURCE_PATH_INVALID、SOURCE_NOT_AVAILABLE、INPUT_TYPE_MISMATCH、INPUT_NULLABILITY_MISMATCH |
| Predicate / Evidence | PREDICATE_GROUP_INVALID、PREDICATE_ARITY_MISMATCH、PREDICATE_TYPE_MISMATCH、PREDICATE_EVIDENCE_REQUIRED、PREDICATE_EVIDENCE_UNSATISFIABLE、EVIDENCE_GUARANTEE_LINK_INVALID |
| CEL / when | CEL_INVALID |
| Wait | WAIT_INGRESS_EXPORT_NOT_FOUND、WAIT_INGRESS_EXPORT_AMBIGUOUS、WAIT_CORRELATION_BINDING_INVALID、WAIT_TIMEOUT_INVALID |
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
| 无 Assurance、含 schemas/ 与 scripts/manifest.yaml | 可导入；仅 LLM-guided；Host 校验共享资源并可按 Host 策略提供脚本 Capability；不调用 Compiler |
| 完整有效 Assurance | 只有正式 1.6.0 Compiler Build / Verify / Bundle 后才可导入 |
| Assurance 目录缺文件或无效 | 拒绝；不得降级 |
| Contract 只声明 Capability，唯一映射 Callable | Link 通过 |
| Capability 零 / 多 Callable，Callable 多 Capability | 静态拒绝，不生成部分 Artifact |
| Operation 引用 observation kind 或 Observation 引用 MUTATION | 静态拒绝 |
| 仅 event.type 的 when，无 requestSchema | 可通过 CEL 静态检查 |
| when 引用 input 但无 requestSchema | CEL_INVALID |
| requestSchema 存在但无 when | Schema 仍验证并发布闭包 |
| Schema-only Package：0 Capability / 0 Callable，含已声明 Schema export | 可作为 Contract.contexts 的 Host Context Schema 依赖；requestSchema 仍必须指向 Skill 自有请求 Schema |
| 未声明依赖却引用 Capability / Schema | 静态拒绝 |
| 多个 when=true | 仅在精确 true 候选集合内消歧 |
| when=false / runtime error | 排除，不重新加入无 when 集合 |
| Wait event 接受 | 进入目标 Node 首个业务阶段；不直接产生 Evidence / Goal 成功 |
| Wait timeout | 只走 TIMEOUT 路由；不触发 Mutation 重放 |
| 普通 Skill / LLM 调用 MAS.RECONCILE | IPC=0，INTERNAL_RECONCILE_ONLY |
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
| §19～25 Invocation、READ / MUTATION、Reconcile、Wait、Outcome、错误 | 采用结果与恢复语义；Wait 重写为 Node-entry Host Runtime READ trigger；Reconcile 仅内部 |
| §26～31 5GC 教学示例 | 不作为新规范示例；由当前 OpenAMSM Create / Modify / Release 1.6.0 Capability 示例替代 |
| §32～35 Script、Cases、Dependencies、Studio | 采用纯本地 Script、显式依赖闭包与 LSP；移除旧 Alias::Callable |
| §36～41 参考语言与定位 | 仅资料性参考，不产生作者语义 |
| §42～45 安全、版本、冻结 | 重写为 1.6.0 单版本、无兼容、无迁移 |
| §46～91 技术解释 / 历史裁决 | 作为设计依据审查；有规范效力的内容必须在本文件对应条款中重新表述，不直接引用旧条款作为 1.6.0 规范 |
| 附录 A～K 决策、诊断、符合性、Schema / Evidence / CEL | 逐项审查；本文件 §12～13 重新冻结当前 Schema / CEL / 诊断；未纳入的历史诊断不自动成为 1.6.0 要求 |
| 附录 L Node-entry Event Wait | 保留 Node-entry、typed input、Correlation、Response Obligation 等语义；新语法和 Host Runtime READ 边界以本文件 §10 为准 |
| 附录 M Optional Assurance / when | 采用 Optional Assurance 与 Contract.when 选择模型；按本文件 §2、§4、§9、§16 重新定义 1.6.0 |

任何历史条款未明确映射到本文件、F02、F03.05、F04、F05、F06、F08、F09 或 EC02 的规范性要求，必须在独立评审中作为遗漏处理；不得由实现者自行沿用旧语义。

## 18. 评审与发布门槛

- 当前是中央完整设计稿，必须经独立设计评审后才能冻结。
- ca-skills 负责发布 1.6.0 作者 Schema、完整规范、机器 languageTarget、Golden 和正式 Release Record。
- Compiler 负责新 Parser / AST / Check / Link / BuildRequest / BuildResult / Artifact / Verify；SR-013 / Compiler Issue #61 负责实现与产品证据。
- Owner / Provider 分别发布满足一对一映射的 Package；Host Context Publisher 只发布 Schema-only Package。
- SR-027 负责新 Bundle；SR-004～006 负责导入、Catalog、Resolver；F04 负责 Runtime Action Boundary；F09 / SR-016 负责 Studio。
- 未正式发布前，所有产品实现和运行验收保持 NOT_RELEASED / NOT_RUN；本设计通过不代表实施 READY。

## 19. OpenAMSM 原版 OpenAPI 直接引用与 Skill 分阶段输入（IR-009）

**原版来源**：SR-031 逐字节代发布 OpenAMSM 实际支持的 OAS 3.0 YAML 与所选 operation / Schema Component 的完整可达引用闭包。原始文件和相对 `$ref` 一字不改。Source Bundle 不是 Capability Package，也不是自动的 G.4 Schema-only Package。

**直接引用**：Skill-owned `requestSchema` 根仍是本地 G.4 闭合对象；显式依赖并 pin Source Bundle 后，可直接引用原版文件的精确 `#/components/schemas/...`。Compiler 对外部目标按 OAS 3.0 Schema Object dialect 解析，保留原语义；不生成 Adapter / Projection。缺少 Resolver、运行期 Validator 或 Golden 时相关 AC BLOCKED / NOT_RUN。

**Ingress 与执行期分离**：Plugin T0 依据 TS 29.502 operation 校验 SBI JSON / multipart / Content-ID / N1/N2 binary slots；T1 `when` 只读取已规范化且到场的 Event / Request 字段。被选 Skill 的 Procedure 在 T2 才能调用授权 Codec READ，消费 Provider 正式 Output Schema。NAS-only PDU Session Type / SSC mode 不得在 T1 无来源时成为必填；Codec Result 不能替代 Owner Receipt / Commit Proof。

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
| 2026-11-27 | 0.1.6 | GPT-6.2（ChatGPT） | §2、§3、§5、§6、§8、§14、§16 | 将 schemas/scripts 提升为 Skill Package 根目录共享资源；定义 YAML Schema 源、Script Registry、Host Script Execution Capability 与 Assurance / LLM 共用资源路径 | 修复可选 Assurance 导致 LLM-only Skill 无法使用 Schema / Script 的结构矛盾，禁止模型任意 Python 执行 | Issue #49；IR-008；SR-032 |
