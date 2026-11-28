# CA-SL Compiler 设计说明书

> 文档版本：0.2.23\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first 增量设计；实施及外部发布仍 NOT_RUN）
> 修订日期：2026-11-28\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、签名、Trust Registry、生产资格及真实 5GC/MAS 认证。

关联 [IR-003](../../IR/IR%20总登记册.md#ir-003)、[IR-006](../../IR/IR%20总登记册.md#ir-006)、[SR-012](../../SR/SR-012-Compiler设计归档与跨仓收敛.md)、[SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)、[SR-030](../../SR/SR-030-Host%20Context%201.6.0%20Schema-only%20Interface%20Package%20Publisher.md)、[Next Issue #14](https://github.com/odango-chan/ca-agent-next/issues/14) 和 [Compiler Issue #62](https://github.com/odango-chan/ca-skill-compiler/issues/62)（#61 仅历史 v1alpha5 范围）。

## 1. 权威与版本边界

1. CA-SL 作者语义由 ca-skills 拥有。**唯一新产品语言目标为 CA-SL 1.6.0（尚未发布）**；中央机器 languageTarget 已固定为 connectionagent.io/v1.6.0，正式 Schema / Golden / Release 仍由 ca-skills 发布。历史 v1alpha5 [normative SHA 18d8184](https://github.com/odango-chan/ca-skills/tree/18d8184367982ccbc835756136c4a53f9096c3a0) 仅作只读审计，不进入新 Parser/Build。
2. Compiler 产品基线为 v2.1.0；本轮实现审查基线为 [ca-skill-compiler commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb](https://github.com/odango-chan/ca-skill-compiler/tree/255ab85fa5abb4b0bf36656bf64250cafebf45cb)。
3. 已发布 Artifact **connectionagent.io/compiler-artifact/v1alpha5** 完全冻结，保持 Manifest、文件布局、字节、Build/Verify 行为及 Golden 不变。
4. Development Artifact **connectionagent.io/compiler-artifact/development/v1alpha1** 完全冻结，继续 **NOT_ADMITTED**；不得把它当作 Agent 可运行发布包。
5. Contract.when、Request Schema 根/闭包与 Capability→Callable Binding 必须共同进入**CA-SL 1.6.0 新 Runtime Artifact**；机器 API 身份和 languageTarget 按 §5.1.1 由 Next 中央固定，生产 Owner 发布正式 Schema / Golden / CLI / Release。新版不接受旧 v1alpha5 Artifact/BuildRequest/BuildResult，也不提供旧版 fallback。
6. Compiler 不执行 Skill、Tool、Observation、Python Script、网络或 Runtime 选择。Agent 不调用 Compiler；消费端设计由 F02 与 SR-004/005/006 负责。

## 2. 单一 Core、当前实现基线与复用边界

Native CLI 与 Go/WASM Worker 必须继续调用同一个 Go Compiler Core。现有公开入口、统一 AST、静态语义、链接和 Artifact 装配是唯一实现路径，不新增第二套 Compiler。

当前代码审查定位（基线 SHA 见 §1）：

| 位置 | 当前职责 | SR-013 要求 |
|---|---|---|
| internal/compiler/api.go | Check / Build / InspectDependencies / VerifyBuildResult 等公开入口和 DTO | 复用现有公开入口；只有新 Artifact 契约确实需要时才新增版本化 DTO/API |
| internal/compiler/inherited_semantics.go | 既有 CA-SL 语义主链 | Contract.when 进入同一 Skill 语义链，不建立平行解析器 |
| internal/compiler/cel_check.go | 现有 Predicate CEL 检查 | 复用 cel-go 与 G.4 白名单思想；不能把当前 Predicate 检查误认为已实现 Contract.when |
| internal/compiler/schema_registry.go | Schema Registry、引用和闭包相关能力 | 复用解析能力并建立逐 Skill Request Schema 类型环境 |
| internal/compiler/v1alpha5_artifact.go、v1alpha5_artifact_verify.go、contracts/v1alpha5/artifact-manifest.schema.json | 冻结 v1alpha5 Artifact 只输出 procedure.json / ingress-links.json；sourceFiles 只记录源路径，不携带本地 Request Schema 字节 | 新 1.6.0 必须发布已验证的 dialect-aware Request Schema 描述，供 Host 运行期按 M.3 验证 Event input：本地 G.4 根及本地闭包进入 Artifact；外部 OAS3 根别名只引用精确 pin 的 Source Bundle 根与可达闭包，不复制或投影原件；不得修改冻结 v1alpha5 |
| internal/compiler/development_link.go、development_multi_skill_test.go | Development Link / 多 Skill Lock 测试 | 仅作为 Schema 作用域和多 Skill fixture 的参考；不是正式发布 Artifact 路径 |

AC-013-01 的 PoC 通过 Development 多 Skill 共享 Lock fixture，复用了 buildSchemaRegistry、resolveReferenceFrom 和 resolveSchemaRoot 等真实 Schema 解析能力。这证明的是可复用的 Schema 解析与跨语言序列化路径，不代表产品 Build 应调用 validateDevelopmentRequest、buildDevelopmentLinkScope 或 newDevelopmentSemantics。

**正式实现约束：** 新 when/Capability 编译必须进入**唯一 CA-SL 1.6.0 Core 和新 BuildRequest/BuildResult**；旧 v1alpha5 Parser/Build 与 v2.1.0 Development Build 只作算法、Schema Registry 和 Golden 历史审计。共享纯解析/闭包算法可以提取，但不能让新 Compiler 引入旧语法/Artifact/DTO 的兼容路由，旧发布字节不修改。

## 3. Contract.when 静态编译设计

### 3.1 作者源与 AST

- 唯一作者位置：skills/<skill-name>/assurance/contract.yaml 的可选顶层 when。
- when 是非空 YAML 字符串；其内容仅允许 CA-SL **1.6.0 正式作者规范**所冻结的 CEL bool 剖面；历史 G.4 仅是候选算法证据，静态结果类型必须为 bool。
- ContractAST 增加可选 when 节点，并保留原始表达式、SourcePath、行列范围。
- 不在 SKILL.md Front Matter 增加 when；不创建 constraint.yaml、activation.yaml、Applicability Package 或第二份 Contract；不把 when 放进 predicates.yaml。
- 不声明 when 的 Skill 不生成 CheckedExpr 或 DescriptorSet 文件；Agent 端按正式 CA-SL 选择规范处理未声明 when 的候选。
- 空字符串、非字符串、非法 CEL、未知字段、无效类型及不允许的语法，使用现有 CA-SL 诊断体系阻断构建。语义错误使用 CEL_INVALID；不得另造一套互不兼容的 WHEN 诊断码。

### 3.2 CEL 输入环境

每个 Skill 独立建立 CEL 类型环境：

| 变量 | 类型 | 来源 |
|---|---|---|
| event.type | string | Host 已验证的规范化 Event 类型；这是本规范唯一固定的 Event metadata 字段 |
| input | 当前 Skill Request Schema 的闭合对象类型 | assurance/contract.yaml 的 requestSchema 及其已解析 Schema 闭包 |

约束：

- when 只能读取 event.type 与当前 Skill requestSchema 中显式声明的 input 字段。
- when 引用 input 成员而没有 requestSchema，静态报 CEL_INVALID。
- 不允许读取 Runtime Context、Observation、Tool Result、Evidence、环境变量、时钟、文件、网络或可变 Host 状态。
- Event 的规范化与 Plugin Event Schema 校验由 Host/Plugin 边界负责；Compiler 只按 CA-SL 规范为 event.type 建立固定类型。
- 每个 Skill 使用自己的 Request Schema 根、Reference 闭包和类型环境。共享 Lock 不等于共享所有 Skill 的私有 Schema 根。

### 3.3 G.4 CEL 表达式剖面

Compiler 必须实现 CA-SL **1.6.0 正式冻结的 CEL 剖面**（可采用历史 G.4 Guard/短路安全规则，但不得把 v1alpha5 当成新语言身份），不得因 cel-go 支持更多语法而扩大作者语言范围。

| 类别 | 允许范围 |
|---|---|
| 值类型 | string、int64、finite binary64 double、bool、null、nullable T、闭合 object、array/list<T> |
| 访问 | 已声明字段的静态点访问 |
| 布尔逻辑 | !、&&、||、括号 |
| 比较 | ==、!=；同一数值类型的大小比较 |
| 存在判断 | has(x.field) |
| 长度 | size(x)，仅 string / array |
| Schema 约束 | required / optional、nullable、enum、const、范围和数组元素约束按已冻结 Schema 赋值规则检查 |

必须拒绝：所有算术运算符、动态索引、切片、动态成员名、对象构造、宏/推导式、反射、未声明函数、时间、随机数、外部数据访问及 G.4 未允许的结构。数组可以作为静态 Schema 类型并参与 size，但不允许数组索引。字符串只允许 == / !=；null 只允许相等/不等比较；大小比较仅限同一数值类型。has(x.field) 只检查已声明属性是否在本次对象中出现。枚举、const、范围、长度和数组元素约束由 G.4 Schema 验证保留；CEL 类型映射不得丢失底层标量类型或放宽这些约束。

CEL int 是有符号 64 位；double 是有限 IEEE-754 binary64。int/double 不隐式混合。静态不能证明表达式最终为 bool、字段类型或数值语义时，报 CEL_INVALID。

### 3.4 Schema-aware 类型检查与 Skill 隔离

正式编译按以下逻辑执行：

1. 对每个 Skill 读取同一次规范化 YAML 解析产生的 Contract AST。
2. 若该 Skill 声明 Contract.requestSchema，定位 Request Schema 根并解析 $ref 闭包，验证根类型、闭合性、字段、必需性、可空性、enum/const、范围和数组元素。若 when 实际引用 input，则 requestSchema 必须存在；若 when 只引用 event.type，则不要求声明 requestSchema，也不得虚构 input 类型。
3. 复用 Compiler 现有 Schema Registry 与 Reference Resolver。必要时抽取共享内部函数，但不得把 Development Build 的 Request/Artifact 契约搬进正式发布链。
4. 每个 when 的 CEL 环境始终包含统一 Host Event 的 event.type 类型；仅当表达式引用 input 时，才把当前 Skill 的 Request Schema 闭包加入类型环境和 DescriptorSet。event-only when 不依赖 Request Schema。若 Contract 已声明 requestSchema，即使 when 不引用 input，也仍须按 G.4 验证并在新版 Artifact 中发布该 Schema 快照，供 Host 按 M.3 验证 Event payload。
5. 未知字段、缺失 Reference、跨 Skill 私有 Schema 借用、类型不匹配、非 bool 结果及 G.4 禁止语法均在 Compiler 静态阶段拒绝。
6. 多 Skill 共享 Lock 时，对每个 Skill 单独建立 Root/Scope。共享依赖可以复用相同的权威依赖身份，但不得把 Skill A 的私有字段注册到 Skill B 的 CEL 环境。

### 3.5 Missing / Explicit Null / Value 与类型 Lowering

JSON Schema 的 [T, "null"] 必须保留三个互不混淆的状态：

| 语义状态 | Wire 表示 |
|---|---|
| Missing：字段不存在 | 外层 nullable wrapper 字段未设置 |
| Explicit Null：字段存在且值为 null | 外层 wrapper 存在，oneof 选择 is_null 分支 |
| Concrete Value：字段存在且有值 | 外层 wrapper 存在，oneof 选择 value: T 分支 |

对 nullable T，Compiler 生成的类型描述中使用可缺失的 wrapper message，oneof 包含 value 与 is_null。该 wrapper 是 CEL wire/type lowering，不改变作者 Schema，也不向作者暴露新的 CA-SL 字段。

语义映射：

- has(input.x) 判断外层字段是否存在。
- input.x == null 判断字段存在且选择显式 null 分支。
- input.x != null 判断字段存在且选择 concrete value 分支。
- 读取 concrete scalar/object/array 值必须经过存在和非 null 事实证明，再映射到 wrapper.value。
- 非 nullable optional 字段仍必须保留 Missing 与 Value 的 presence 语义。

AC-013-01 已验证 optional + nullable scalar 的三态 wire 表示和 Go/Python 一致性。其他受支持 Schema 类型、深层 optional ancestor 和完整 G.4 组合仍须在 AC-013-02/04 验收，不得由该单一字段 PoC 外推为已通过。

### 3.6 Guard / Short-circuit 静态事实分析

守卫分析必须基于 cel-go AST 和类型化字段路径，不允许用字符串匹配或正则表达式替代。

事实规则：

- has(x) 的 true 分支建立 present(x)；false 分支建立 missing(x)。
- x != null 在 present(x) 已成立时，其 true 分支建立 nonNull(x)。
- x == null 在 present(x) 已成立时，其 true 分支建立 isNull(x)。
- A && B 中 B 继承 A 为 true 时成立的事实。
- A || B 中 B 继承 A 为 false 时成立的事实。
- !A 交换 A 的 true/false 分支事实。
- 分支汇合时只保留所有可达分支都成立的事实；不能证明安全的读取静态拒绝。
- 嵌套路径中每个 optional ancestor 均需有相应存在守卫；每个 nullable ancestor 均需有非 null 守卫。

Lowering 必须保留作者表达式的左到右短路语义，并将作者层的 has/null/value 事实映射到 wire descriptor 的 presence / oneof 分支检查。Lowering 后仍由同一 cel-go 对生成的 typed expression 做最终检查并导出 CheckedExpr。不能用运行期异常替代静态守卫检查，也不能把不安全 OR 降级为可能匹配成功的表达式。

### 3.7 诊断与源码定位

- 保留 assurance/contract.yaml 中 when 的原始 SourcePath、行、列及表达式范围。
- CEL parse、类型、字段、守卫、G.4 表达式结构、input 缺少 requestSchema 和 lowering 错误使用现有 CEL_INVALID。
- Contract Schema 根缺失/引用无法解析/Schema 不满足 G.4 时，沿用 SCHEMA_MISSING / SCHEMA_INVALID；Contract 中未知字段沿用 UNKNOWN_FIELD。不得把所有 Schema 解析失败误报成 CEL_INVALID。
- 错误信息至少指出 Skill、SourcePath、表达式位置、字段路径和失败原因。
- 不引入新的诊断注册表或独立诊断阶段。
- 未知、错误或不能求值的表达式不得生成可执行 Artifact。

## 4. Go → Python CheckedExpr 互操作契约

### 4.1 标准消息

- Go Compiler 使用 cel-go 解析和检查源表达式，导出标准 cel.dev/expr.CheckedExpr Protobuf。
- 用 google.protobuf.Any 包装；互操作验证要求 Any type URL 为 type.googleapis.com/cel.expr.CheckedExpr。不得直接把 cel-go 的旧 google.api.expr.v1alpha1.CheckedExpr type URL 当成 Python 可消费类型。
- 同一 Skill Artifact 的 when.types.pb 携带 google.protobuf.FileDescriptorSet，包含 event.type；当 when 引用 input 时再包含该 Skill Request Schema 的必要类型闭包。DescriptorSet 只提供 CEL 类型描述，不完整表达 enum、const、minLength、数值范围等 G.4 Schema 断言，不能替代 Host 运行期 Request Schema 验证所需的 Schema 快照。
- Python 固定版本 cel-expr-python 使用 Env.deserialize(bytes) 直接加载同一 Any；DescriptorSet 用于构造对应 DescriptorPool 和 typed activation。
- Python 不解析 CEL 源字符串、不重新编译、不自行实现 CEL Parser/Type Checker，不使用 DynType 逃逸静态类型。
- 导入阶段反序列化一次；每个新 Event 仅传入新的 typed activation 求值。此消费端生命周期由 F02 / SR-004/005 负责。

### 4.2 已验证互操作基线

AC-013-01 报告采用 Go 1.26.6、cel-go 0.33.2、Go protobuf 1.36.10、CPython 3.14.6、cel-expr-python 0.1.4、Python protobuf 7.36.2。产品实现必须将实际依赖版本固定在 Compiler / Runtime 各自依赖文件中，并在 CI 中复跑；不能仅把 PoC 环境版本写入文档就视为产品依赖已锁定。

## 5. 新版发布 Runtime Artifact 设计

### 5.1 版本隔离

- connectionagent.io/compiler-artifact/v1alpha5 保持完全不变。
- Development v1alpha1 保持完全不变并继续 NOT_ADMITTED。
- 新发布 Runtime Artifact 使用唯一 1.6.0 版本化 Manifest/文件布局，languageTarget 与 BuildRequest / DependencyInspection / BuildResult / Artifact API 身份按 §5.1.1 由 Next 中央固定；正式 Schema / Golden / Release 仍待生产仓发布；不兼容旧包。
- 新 Compiler 只实现 §5.1.1 固定的 Artifact / BuildResult / BuildRequest / DependencyInspection API；新 Runtime Build 只产生 Artifact / BuildResult /2，VerifyBuildResult 只接受该结果契约。不在同一二进制中双轨支持旧/新 Runtime BuildResult，不增加版本 dispatch、fallback 或兼容路由。旧 v2.1.0 Release 及其 Artifact/BuildResult v1alpha5 保持不可变历史发布。Development Build 继续使用其独立 v1alpha1 API/Artifact 家族，不因 when 扩展。
- 不把 Development 专用 executionStatus=NOT_ADMITTED、hostAdmission 或 Skill Admission 状态写入新发布 Runtime Artifact。

### 5.1.1 中央冻结的 1.6.0 机器契约目标（尚未发布）

本设计在 Next 冻结唯一目标值，生产仓负责实现和发布，不再把机器标识留给 Compiler Owner 在实施时临时选择：

| 契约 | 唯一目标标识 |
|---|---|
| CA-SL languageTarget | connectionagent.io/v1.6.0 |
| BuildRequest | connectionagent.io/compiler-build-request/2 |
| DependencyInspection | connectionagent.io/compiler-dependency-inspection/2 |
| BuildResult | connectionagent.io/compiler-build-result/2 |
| Runtime Artifact Manifest | connectionagent.io/compiler-artifact/2 |
| Compiler Release SemVer | 3.0.0（从 v2.1.0 进行不兼容主版本升级；不发布 alpha / rc） |

以上是中央设计目标，不表示这些 API、Schema、Golden、可执行文件或 Release 已经存在。ca-skill-compiler#61 的目标是 CA-SL v1alpha5，保留为历史设计/实现记录，不得用于 1.6.0 实施、验收或发布；CA-SL 1.6.0-only Compiler 实施 Issue [#62](https://github.com/odango-chan/ca-skill-compiler/issues/62) 已存在；本仓 SR-013 的具体实施阶段仍须满足 READY/授权门槛，并在 #62 记录受测设计 SHA，不再重复创建新 Issue。

新版本不接受旧 v1alpha5 Runtime Artifact、旧 Build DTO 或 Development Artifact 作为输入；不做兼容映射、fallback、自动迁移或双轨 Parser。

### 5.2 候选文件布局

新版 Runtime Artifact 必须同时解决两类不同的运行时输入：Request Schema 校验数据与可选 when 程序。候选布局如下，精确文件名由 Compiler Owner 在 AC-013-03 定稿：

~~~text
manifest.json
skills/<skill-name>/compiled/procedure.json
skills/<skill-name>/compiled/ingress-links.json
skills/<skill-name>/compiled/request-schema/descriptor.json
skills/<skill-name>/compiled/request-schema/g4/root.json
skills/<skill-name>/compiled/request-schema/g4/resources/<resource>.json
skills/<skill-name>/compiled/when.checked.pb
skills/<skill-name>/compiled/when.types.pb
~~~

- 只要 Contract 声明 requestSchema，就必须在 Artifact 中输出 dialect-aware Request Schema 描述；与 when 是否存在、是否读取 input 无关。本地 G.4 根及本地 `$ref` 闭包规范化为 Artifact 文件；纯 `$ref` OAS3 根别名不生成 G.4 副本，改由 Manifest 引用显式 pin 的 Source Bundle 及其选定可达 OAS3 闭包。
- 没有声明 requestSchema 时不输出 Request Schema 文件；event-only when 仍可编译，DescriptorSet 只需包含 event.type。
- 只有声明 when 的 Skill 才输出 when.checked.pb 和 when.types.pb；无 when 时不生成空表达式或占位文件。
- when.checked.pb 是 Any 序列化字节；when.types.pb 是 CEL 类型所需的 FileDescriptorSet。Request Schema 的本地 G.4 Artifact 文件保留完整 G.4 断言，不能用 DescriptorSet 代替；外部 OAS3 Schema 不转换为 G.4 文件，原版 YAML bytes 由锁定 Source Bundle 保留并按 OAS 3.0 dialect 解析。
- 本地 G.4 Schema 资源若声明 `$id`，必须保留精确值并由 Manifest 资源表映射至 Artifact path；外部 OAS3 资源以 Source Bundle dependency identity + 原始 source file + JSON Pointer 标识，允许原件未声明 `$id`，不得虚构 URI。运行期不得访问远端或作者工作区。
- 文件路径和资源映射是本设计候选值，Compiler Owner 必须在正式 Artifact Schema、Golden 和 PR 中定稿，不得同时保留多个兼容别名布局。

### 5.3 Manifest 最小语义

新 Manifest **只由 1.6.0 唯一正式 Schema 定义**；候选语义包含 apiVersion、languageTarget、validationScope、generator、dependencyClosure、skills、outputFiles、已检查 capabilityBindings、when 和 Request Schema 闭包。任何历史 v1alpha5 字段名只可经新 Owner 明确裁决复用，**不能接受旧 Manifest/BuildResult 作为新 DTO**。每个 Skill 的 identity、编译文件、Wait/Continuation linkage 必须可确定性重建；不生成或校验 sourceDigest。

每个声明 Contract.requestSchema 的 Skill 增加 requestSchema 元数据对象，至少记录：

1. sourceRef：Contract.requestSchema 的作者相对路径。
2. rootDialect：明确为本地 G.4 或外部 OAS 3.0 Schema Object。
3. rootLocation：本地 G.4 记录 Artifact rootPath 和可选 rootSchemaId（仅原根声明 `$id` 时）；外部 OAS3 记录 Source Bundle dependency identity、原始 source file 与 JSON Pointer，不要求根有 `$id`，也不生成 G.4 Artifact path。
4. resources[]：闭包中每个已解析资源的精确身份和 dialect。若为本地 G.4，记录 `schemaId`（若声明）与 Artifact path，覆盖完整、无循环的本地 G.4 `$ref` 闭包；若为外部 OAS3，记录 Source Bundle dependency identity、原始 source file、JSON Pointer 和 OAS 3.0 Schema Object dialect，不提供 G.4 Artifact path。外部 OAS3 根没有 `$id` 时，以 dependency identity + source file + JSON Pointer 标识，不虚构 URI。

requestSchema 对象与 when 是否存在无关；Host 依照 CA-SL **1.6.0** 正式 requestSchema/when 契约使用它验证 Event payload。若为本地 G.4，根与本地闭包文件进入该 Skill 的 compiledFiles[] 和 Manifest outputFiles[]；若为外部 OAS3，原版 YAML 文件由精确 pin 的 Source Bundle dependency 提供，不进入 Compiler 生成的 compiledFiles[] / outputFiles[]，只在 Manifest 的 dependencyClosure / resources[] 中记录精确引用。Source Bundle 在 Published Skill Bundle 中只保留一次，运行期不得访问远端。

仅为声明 when 的 Skill 增加 when 元数据对象，至少记录 checkedExprPath、descriptorSetPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）。当表达式引用 input 时，when 元数据还记录 requestSchemaRef 与 resolvedRequestSchemaLocation；后者按 requestSchema.rootDialect 使用带类型的位置引用（本地 G.4 为 Artifact path；外部 OAS3 为 dependency identity + source file + JSON Pointer），并必须指向同一 Skill 的 requestSchema descriptor。只访问 event.type 时可省略这两个引用字段。没有 when 时不输出 when 元数据。

建议字段名和文件名是本设计的实现默认值；Compiler Owner 在 AC-013-03 冻结 JSON Schema 前确认。when.checked.pb 与 when.types.pb 必须同时进入 compiledFiles[] 和 Manifest outputFiles[]；本地 G.4 规范化根/资源文件也进入这两个清单；外部 OAS3 原版文件由 Source Bundle dependency 提供，只进入 dependencyClosure / resources[] 引用，不进入 Compiler 生成的 compiledFiles[] / outputFiles[]。Manifest 不定义 `outputFiles[].sha256` 或 `sourceDigest`；`outputFiles[]` 只保留实际生成文件的路径 / 角色等非摘要元数据。Build / Verify 检查路径、文件存在性、Schema、依赖闭包和语义结果，不计算或比较 SHA-256 / checksum / digest。

## 6. Build / Verify 责任与行为

### 6.1 Build

1. 通过新 **CA-SL 1.6.0** 单一 Parser/AST/Check/BuildRequest/DependencyInspection；先按 SR-029 静态检查 Capability→唯一 Callable、kind/Effect/Schema/Package/Scope，再执行 when/Request Schema 静态分析，旧语言不能进入新入口。
2. 对声明 requestSchema 的 Skill 生成 dialect-aware Schema 闭包描述，作为 Host 运行期输入校验数据；本地 G.4 根及完整本地闭包规范化进入 Artifact，外部 OAS3 根及完整可达闭包以精确 pin 的 Source Bundle 引用表示；即使没有 when 也必须输出该描述。
3. 对有 when 的 Skill 执行 §3 的 dialect-aware Schema 检查、Guard 分析和 typed lowering。本地 G.4 使用 G.4 检查；外部根别名使用 OAS 3.0 Schema Object 语义。只有表达式引用 input 时才使用该 Skill 的 Request Schema 类型环境；event-only when 不要求 requestSchema。
4. 生成 CheckedExpr Any 与对应 DescriptorSet。
5. 按新 Runtime Artifact Manifest 组装完整产物；没有 when 的 Skill 不生成 when 文件。
6. 使用 RFC 8785 JCS、稳定排序和既有确定性约束；不得写入时间、随机值、绝对宿主路径或环境相关数据。
7. 任何静态检查或装配失败都返回完整诊断和空 OutputFiles，不返回部分 Artifact。

### 6.2 Verify

新版 Verify 必须检查：

- Artifact API version 与 languageTarget 精确受支持。
- Manifest、文件清单、路径、重复归属和必需文件完整。
- 每个已声明 Request Schema 的根与全部资源按其声明 dialect 可解析：本地 G.4 保留精确 `$id`（若声明）、G.4 关键字和约束；外部 OAS3 保留 Source Bundle pin、原始文件 / JSON Pointer 及 OAS 3.0 Schema Object 语义（不要求 `$id`）；不存在未解析、越界或重复资源。
- 每个 CheckedExpr Any 可反序列化，type URL 与标准类型一致。
- 每个 DescriptorSet 可解析，所有 CheckedExpr 类型引用均可解析。
- CheckedExpr 最终类型为 bool；引用 input 时，其类型闭包必须与该 Skill 的 Request Schema root/closure 精确匹配。event-only when 不得被强制要求 Request Schema。
- when 源路径/位置、程序路径和 DescriptorSet 路径相互一致。
- 不存在跨 Skill 私有 Schema 或 Descriptor 引用。
- 无 when 的 Skill 不得带伪造/空的 when 程序；但若其 Contract 声明 requestSchema，仍必须携带 dialect-aware Schema 描述（本地 G.4 Artifact 或外部 OAS3 Source Bundle 引用）。
- DescriptorSet 只负责 CEL 类型，不得被当作完整 JSON Schema 验证器；本地 G.4 Request Schema Artifact 必须保留 G.4 的 enum/const/范围/长度/数组约束；外部 OAS3 Request Schema 必须保留其原生约束语义，不得套用 G.4 白名单或默认闭合规则。
- BuildResult、Manifest 与 OutputFiles 的集合和字节一致。

新版 Verify 仅接受 1.6.0 新 BuildRequest/BuildResult/Artifact，执行完整重建/逐文件比较或 Compiler Owner 冻结的等价确定性复验；新 Compiler 不支持任何旧 v1alpha5 DTO、Artifact、双轨 dispatch 或兼容 fallback。旧 v2.1.0 Release 保留旧 BuildResult/Artifact v1alpha5 的原有行为；历史 Development Build 只保留在旧 v2.1.0 Release 中作只读审计，新 Compiler 不提供 v1alpha1 兼容执行入口。当前 CLI 已在写入目录前用同一 Verify 函数验证成功 BuildResult；新版本必须保持“先 Verify、后原子写盘”的既有不变量，不得假设存在一个已发布 Artifact 的独立 CLI verify 子命令。

### 6.3 历史契约留档与新版拒绝（非兼容）

每次新增 Artifact 版本都必须执行：

- 冻结发布 Artifact v1alpha5 的机器 Schema、Golden 字节和旧 v2.1.0 Release Verify 行为不变；新 Compiler 不提供旧 Runtime API 兼容路由，必要的历史复验使用固定 Golden/旧 Release。
- Development Artifact v1alpha1 的机器 Schema、Golden 字节、NOT_ADMITTED 与独立 Development Verify 行为不变；不新增 Development v1alpha2，也不把 Development 输出用于 Agent Bundle。
- 新 Runtime Artifact 与 BuildResult 分别维护版本化 Schema（建议 contracts/2/artifact-manifest.schema.json 与 contracts/2/build-result.schema.json）、Golden、正负例和版本说明。
- 不得通过更新旧 Golden 来掩盖旧契约变化。

## 7. 测试矩阵与产品门禁

| 类别 | 必测内容 |
|---|---|
| 作者格式 | 无 when、合法 when、空值、非字符串、重复 YAML Key、未知旧字段 |
| G.4 正例 | event.type-only（无 requestSchema）、typed input（有 requestSchema）、字段点访问、括号、布尔逻辑、比较、has、size、数组字段与枚举/const Schema 约束 |
| G.4 负例 | 未知字段、缺 requestSchema、非 bool、宏/推导式、动态索引、切片、对象构造、动态成员、外部函数、未支持语法 |
| Presence / Null | Missing、Explicit Null、Value；optional 守卫；nullable 非 null 守卫；嵌套 optional ancestor |
| Boolean Flow | AND、OR、NOT、安全/不安全 OR、左到右短路和事实汇合 |
| Numeric | int64 最小/最大值、finite double、非有限值拒绝、int/double 混用拒绝 |
| Isolation | 多 Skill 共享 Lock、每 Skill Request Schema 根、跨 Skill 字段借用拒绝 |
| Serialization | Go CheckedExpr Any + DescriptorSet；Python 直接反序列化同一字节；18/18 PoC 基线扩展为正式 fixtures |
| Artifact | 新版 Build/Verify、Request Schema 根/闭包发布与验证、损坏文件拒绝、缺失 Descriptor 拒绝、无 when、重复构建确定性 |
| Version rejection | 新 Compiler 对全部历史 v1alpha5 Build DTO、Artifact、Development v1alpha1 和未知 languageTarget 显式拒绝；旧 Release/Golden 只读归档不计入 1.6.0 PASS |
| Platform | Native、WASM、CLI E2E、真实 Chromium Worker parity |

Compiler 产品回归命令以 Compiler 仓库当前脚本和 CI 为准，SR-013 固定以下必需门禁：

~~~bash
GOTOOLCHAIN=go1.27.4 GOWORK=off go test ./... -count=1
GOTOOLCHAIN=go1.27.4 GOWORK=off go vet ./...
GOTOOLCHAIN=go1.27.4 CGO_ENABLED=0 GOWORK=off go build ./...
GOTOOLCHAIN=go1.27.4 CGO_ENABLED=0 GOOS=js GOARCH=wasm GOWORK=off go build -o dist/skillc.wasm ./cmd/skillc-wasm
GOTOOLCHAIN=go1.27.4 GOWORK=off go test ./cmd/skillc -count=1 -run TestCLIEndToEnd -v
GOTOOLCHAIN=go1.27.4 GOWORK=off node scripts/chromium-parity.mjs
git diff --check
~~~

Chromium parity 脚本使用真实 Headless Chrome；若默认路径不可用，必须通过 CHROME_PATH 指向本机/CI 实际安装的 Chrome 或 Chromium。另需固定并实跑 Python cel-expr-python / protobuf 互操作测试。若现有仓库没有对应 Python 测试脚本，AC-013-04 必须新增可由 CI 调用的测试入口；提示词不得编造一个不存在的命令。每项记录仓库、受测 SHA、环境、依赖版本、命令、退出码和证据位置。

## 8. 发布边界与外部消费

- Compiler 的职责止于 Check、Build、Verify、Artifact Schema、Compiler Release 和可复现证据。
- ca-skills CI 负责选取并固定稳定 Compiler Release、编译 Assurance Skill、验证结果，并按 ca-skills Bundle 契约组装 SKILL.md 与发布 Artifact。该工作由 F08 与 SR-027 追踪，不属于历史 Compiler #61，也不属于新版 Compiler #62 的 Bundle 发布职责。
- Next Agent 只消费正式发布 Bundle；导入、Catalog、CEL 反序列化和每 Event 求值由 F02 / SR-004/005/006 验收。Next 不内置 Compiler、不调用 Compiler 命令、不实现 Skill Admission。
- Compiler Release、ca-skills Bundle Release、Next Runtime E2E 是三个独立证据层。一个通过不能替代另一个。

## 9. 当前状态与 SR-013 阶段关系

- CA-SL v1alpha5 规范来源和语言标识已固定。
- AC-013-01 隔离 PoC 的固定归档、18/18 报告和完整性复核见 SR-013 §3；本轮复跑 NOT_RUN。
- AC-013-02 正式 Contract.when 编译：NOT_RUN。
- AC-013-03 新版 Runtime Artifact Schema/API：机器身份已由 Next 按 §5.1.1 固定；正式 Schema / Golden / CLI / Release 待 Compiler Owner 实现和发布。
- AC-013-04 Build/Verify 与产品门禁：NOT_RUN。
- AC-013-05 Compiler Release 资产：依赖 AC-013-01～04、AC-013-06 和单独发布授权，BLOCKED。
- AC-013-06 Schema-only Package / Schema dependency closure / 零 Capability roots：BLOCKED / NOT_RUN，联合 SR-030 AC-030-03。
- SR-013 整体保持 DRAFT；本设计补充不代表 Compiler 产品代码已实施、PR 已合并或 Release 已发布。

## 10. Capability 静态链接与 Runtime Artifact v2 绑定

### 10.1 输入语义

本节是 SR-029 对 1.6.0 新 Runtime Artifact /2 的增量要求。机器身份已按 §5.1.1 固定；新契约只面向 CA-SL 1.6.0。v1alpha5 / Compiler v2.1.0 已发布路径保持冻结，Development v1alpha1 继续 NOT_ADMITTED。

Contract.capabilities 是 Capability Grant 列表；Procedure 的 operation.capability / observation.capability 是使用点。dependencies 仍提供精确 Owner Contract / Provider Interface Package 快照。Skill 作者源不出现 Callable ID。

### 10.2 Link 算法

Compiler 对每个 Procedure Capability 使用点执行以下确定性步骤：

1. 校验 Capability ID 格式，并确认它已列在同一 Skill Contract.capabilities 中。
2. 在该 Skill 的显式 dependency closure 中查找 Capability export；必须恰好命中一个 Package。零个报 CAPABILITY_UNRESOLVED；多个报 CAPABILITY_AMBIGUOUS。
3. 读取该 Capability 的公开 Callable membership；数量必须恰好为 1。零个或多个报 CAPABILITY_CALLABLE_CARDINALITY_INVALID。
4. 检查该 Callable 只归属一个 Skill-facing Capability；重复归属报 CALLABLE_CAPABILITY_CARDINALITY_INVALID。
5. 在同一 Package / Owner 的 ToolCatalog 中解析 Callable；Owner、ID、kind、Effect、Input/Output Schema 必须唯一一致。
6. operation.capability 必须匹配 kind=operation；observation.capability 必须匹配 kind=observation 且 Effect=READ。Operation Effect 由 ToolCatalog 决定，不由 Skill 声明。
7. 复用现有 Schema closure、Evidence、Scope identity / provenance、Mutation Receipt / Commit Proof / Reconcile 校验；Reconcile 不作为普通 Capability 导出。
8. 对未被任何 Procedure 使用的 Grant 报 CAPABILITY_GRANT_UNUSED；不得因未使用而保留隐式授权。

Schema-only 依赖规则：显式依赖闭包可以包含仅导出 Schema 的 Interface Package，其 Capability / Callable exports 均为零；**Host Context** Schema-only Package 仅经 Contract.contexts 的显式 Schema export 引用进入 closure；**3GPP Common** Schema-only Package 可由 Skill-owned requestSchema 内的精确 $ref 和依赖声明引用其公共类型 export（不成为 Request 根）。Compiler 将两类实际引用的 Schema export 与完整 $ref 闭包纳入 Schema dependency closure，不为任一 Schema-only Package 建立 Capability grant、Callable binding 或 Tool allowlist。零 Capability roots 不要求 Schema dependency closure 为空；只有不存在外部 Capability 和外部 Schema 引用时，Package dependency closure 才为空。

Link 阶段不访问 Provider 动态 catalog，也不选择 backendOperationId。Provider 内部的多 handler 路由由 Callable 的封闭 Input Schema 决定。

### 10.3 Artifact v2 Capability Binding

中央设计目标已冻结：languageTarget=connectionagent.io/v1.6.0；BuildRequest=connectionagent.io/compiler-build-request/2；DependencyInspection=connectionagent.io/compiler-dependency-inspection/2；BuildResult=connectionagent.io/compiler-build-result/2；Runtime Artifact=connectionagent.io/compiler-artifact/2；Compiler Release=3.0.0。正式 Schema、Golden、CLI 与 Release 尚未发布；生产 Owner 按该目标实现，不得自行改名或增加兼容入口。

每个 Skill 的 Manifest 增加 capabilityBindings[]。每项至少包含：

- capabilityId：作者源使用的 Capability ID；
- dependencyId / stablePackageId：解析来源；
- owner 或 publisher identity：所属契约权威；
- callableId：唯一内部 Callable ID；
- kind / effect：ToolCatalog 或 Interface Package 的规范值；
- inputSchemaRef / outputSchemaRef：对应 Package 的精确 Schema 引用。

编译后的 Procedure 节点保留 capabilityId；capabilityBindings[] 是 capabilityId 到 callableId 的唯一内部映射。Schema-only Package 的 Schema exports 仅进入 Schema dependency closure，不生成 capabilityBindings、Callable allowlist 或 Tool Effect。Manifest 的 dependencyClosure.exports[] 仍列出精确 operation / observation Callable exports，Runtime 继续从该闭包建立 Callable allowlist。Capability ID 不是运行时模型选择器；Callable ID 不暴露给模型。

### 10.4 稳定诊断与失败行为

至少定义以下稳定诊断：CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_GRANT_UNUSED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH、CAPABILITY_BINDING_MISSING。

任何 Capability Link、Schema、Evidence、Scope 或 Artifact 装配错误均返回完整诊断和空 OutputFiles，不生成部分 Artifact。禁止 fallback 到 v1alpha5、Development 或动态 Provider catalog。

### 10.5 不变量

- v1alpha5 已发布 Artifact / Golden 和 Compiler v2.1.0 不变。
- 新 Artifact v2 只支持 languageTarget 1.6.0；新 Compiler 不解析旧版语法、旧 Build DTO 或 Artifact。
- Development v1alpha1 Schema / Golden 不变并继续 NOT_ADMITTED。
- 不增加包级 hash、签名、Trust Registry、Admission 或新的 Capability Manager；复用现有 Package identity、Schema 和文件清单机制。
- Capability↔Callable Binding 由 SR-029 设计；Schema-only Package 由 CA-SL 1.6.0 规范 / SR-030 定义；SR-013 继续跟踪 when / Request Schema / Schema-only closure / Build / Verify / Release 的 Compiler 实施，AC-013-03 与 AC-013-06 必须消费本节唯一 Artifact v2 目标。

**1.6.0-only 设计评审硬门槛：** 新 Compiler Parser/Check/Build/Verify/BuildRequest/BuildResult/Artifact 只支持 1.6.0。 此章节仅描述目标设计，外部代码/Release/E2E 均 NOT_RUN。


## 11. 新 1.6.0 编译合同的设计评审与发布门槛

| 边界 | 当前可评审决议 | 实施前由谁冻结 |
|---|---|---|
| 作者与语言 | 仅 1.6.0 Contract/Procedure/when/Capability；旧 Alias::Callable 全拒绝 | Next：languageTarget 唯一值；ca-skills：正式作者 Schema、Golden 与 Release |
| 一对一 Link | Owner 旧两项 N1 Parser 必须由 Owner 分别签认移除或改造为纯业务 READ，公开基数可能为 22/22、23/23 或 24/24，未签认前不固定数量；Provider 查询子集 2/2，含 Codec 全量 3/3（单包和跨包均须双向唯一）；Reconcile internal-only；每公开 Callable 仅一 Capability | Owner/Provider 发布新 Package/Schema 与最终成员数；Compiler 不猜测 |
| Capability roots 与 Schema dependency closure | 零 Capability roots 合法；若有 contexts Schema-only 引用，Package dependency closure 可非空；仅无外部 Capability / Schema 引用时整体闭包为空 | Compiler：新 BuildRequest / DependencyInspection 必须区分 Capability roots 与 Schema-only 依赖 |
| Schema-only Interface Package | 显式导出 Schema、0 Capability / 0 Callable，可作为 contexts Schema 依赖；不产生 Capability grant、Callable binding、Tool allowlist 或 Tool Effect | Compiler 1.6.0 Package Schema / Link / Build / Verify；SR-013 AC-013-06 与 SR-030 AC-030-03 联合验收 |
| when 与 Request Schema | input 使用需 Schema；event.type-only 不要求；Guard/nullable 静态检查；有 Schema 时无 when 也发布根闭包 | ca-skills 新 CEL 剖面 + Compiler CheckedExpr/DescriptorSet |
| 唯一 Build/Verify | 只接受 1.6.0 DTO 与 Runtime Artifact；文件、绑定、Schema、结果可确定性 Verify；旧 DTO/包拒绝 | Compiler 新 CLI/DTO/Manifest/Golden/Node/WASM |
| 消费 | Agent 只导入新发布 Bundle，Studio 使用相同新 Compiler/Package，不自制 Linker | SR-004、SR-016、SR-027 的正式模块 AC |

上述目标规则已经可供设计评审；精确字段和可执行命令尚未发行，必须等正式发布后才能宣称对应产品验收 PASS。旧 v2.1.0 Development v1alpha1 和 v1alpha5 的历史设计/Golden 不在新二进制内实现兼容分支。

## 12. OpenAMSM 原版 OpenAPI 3.0 引用与 Compiler dialect-aware Resolver（IR-009）

- **SR-031 Source Bundle**：ca-skills 原样代发布 OpenAMSM 实际支持的 OpenAPI 3.0 YAML 与已选 operation / Schema Component 的完整可达 `$ref` 闭包。原文件 bytes、路径和相对 `$ref` 不改；Source Bundle 不是 Interface Package，不导出 Capability / Callable。
- **本地 G.4 与外部 OAS 3.0 分离**：Skill-owned `requestSchema` 根及本地 Schema 节点继续使用 CA-SL 1.6.0 G.4。只有在 Skill 显式声明并 pin Source Bundle dependency 后，才能引用其中精确的 `#/components/schemas/...`；目标由 OAS 3.0 Schema Object validator 解释，不套用 G.4 白名单，不做 projection / Adapter。
- **选定根与 lazy Resolver**：Compiler 的根是精确 Schema Component JSON Pointer；Plugin ingress 的根是固定 operation identity + `requestBody` surface（当前 `PostSmContexts` 的 `jsonData`）。先解析原版根 YAML，再仅递归解析该根可达的 refs；不得 eager resolve 根文件中未选定 operation 的全部 refs。相对 `$ref` 以引用所在文件为基准按 RFC 3986 解析；fragment 按 RFC 6901 解码。`../` 仅在规范化后的目标仍位于 pin 的 Source Root 内时允许；拒绝任意 scheme / authority / query、绝对路径、逃出 Source Root 的路径、非法 pointer escape、Bundle 外文件、unresolved in-scope ref、cross-commit mixing、non-schema pointer 和循环引用。未选定闭包外 refs 不构成当前消费失败。Build / Verify 必须离线使用锁定快照。
- **真实来源闭包基线**：在 OpenAMSM commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 上，`PostSmContexts.requestBody → jsonData → SmContextCreateData` 静态引用遍历得到 4 份原版 YAML、102 个可达 Schema Component，无未解析目标或循环。闭包为 TS 29.502、TS 29.571、TS 29.510 NFManagement、TS 29.518 Namf Communication；不是全目录 472 份 YAML。
- **Dialect-aware 验证**：本地节点使用 G.4 validator；外部目标及其可达引用使用 OpenAPI 3.0.0 Schema Object semantics。当前固定闭包实际包含 `allOf` 1、`anyOf` 25、`oneOf` 3、`nullable` 2、`format` 4（实际值为 `uuid` / `date-time` / `byte`）、`pattern` 42、`additionalProperties` 3（本快照三处均为 Schema Object）、`items` 23、`enum` 27、`required` 26、`default` 21 个关键字出现项；这些计数是该 source commit 的审计证据，Golden 应覆盖各实际出现语义，不应当作未来版本的固定数量。组合语义为 `allOf` 交集、`anyOf` 至少一个分支、`oneOf` 恰好一个分支；`pattern`、schema-valued `additionalProperties`、`nullable`、`format` 等不得丢弃 / 改写。OAS3 允许 boolean-valued `additionalProperties`，当前快照没有该形式；实现遇到时须按 OAS3 处理或明确 fail-closed，不得静默忽略。`default` 仅为注解，不自动填充输入。若可达闭包含不支持语义，使用 `SCHEMA_INVALID` 拒绝并输出 source file / JSON Pointer / Skill SourcePath；不得生成部分 Artifact。
- **CEL 类型环境**：对 `anyOf` / `oneOf`，只有在每个可满足分支中均声明、均列入 `required` 且类型一致的字段，才能作为无条件可访问字段；其他字段仅在 CEL 类型系统显式支持 optional 时按 optional 暴露，否则不允许无条件访问。`allOf` 按交集组合属性约束并合并 required 集合，类型冲突拒绝；`nullable` 的 Null 与 Missing 分开处理。无法证明可用性的字段不进入无条件类型环境，不猜测为某个类型。Plugin 的完整 operation / multipart 校验仍由 SR-010 原生 OAS consumer 负责，Compiler 不复制 operation 逻辑。
- **Host Context**：SR-030 Schema-only Package 仍只由 `Contract.contexts` 引用；它与 OpenAPI Source Bundle 是不同依赖 kind。两者都不产生 Capability / Callable Scope。
- **Artifact 表示与机器字段门禁**：本地 G.4 根使用规范化 Artifact 文件；外部 OAS3 根必须以纯 `$ref` 别名解析到显式 pin 的 Source Bundle，Artifact/Manifest 记录 Source Bundle dependency identity、source commit / Git blob pin、原始文件路径、根与传递引用的 JSON Pointer、每项资源的 OAS3 dialect 和完整选定闭包；原始 YAML bytes 在 Bundle 中保留一次，绝不投影、改写或复制为 G.4。运行期只从本地锁定 Bundle snapshot 解析。Source Bundle dependency kind、alias / URI / JSON Pointer wire 编码、Manifest / Lock / Build DTO 字段、OAS 3.0 validator 版本与 Golden 必须由 ca-skills / Compiler Owner 在正式 1.6.0 Schema / Golden 中冻结。当前没有正式发布，不允许 Harness 猜字段或宣称 READY。

SR-013 AC-013-07 需验证原版组件直接引用、跨文件 CommonData 闭包、OAS 3.0 语义保真、G.4 / OAS3 dialect 边界、CEL 类型可确定性和 fail-closed。Source Bundle 原件 byte-compare PASS 不能代替 Compiler 产品 AC。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 Compiler 设计基线 | 集中维护及验证交接 | IR-006、SR-012、Next #2 |
| 2026-11-25 | 0.1.1 | Codex | §5 | 加入 Goal 的实施门槛、恢复点和完成判据 | 支持分阶段执行及阻塞后恢复 | IR-006、SR-012、Next #2、PR #3 |
| 2026-11-25 | 0.1.2 | Codex | §5–6 | 明确分阶段输入、退出条件、证据包及实施 SR 边界 | 降低 Harness 自主执行时的裁量 | IR-006、SR-012、Next #2、PR #3、Compiler #61 |
| 2026-11-25 | 0.1.3 | Codex | §5–6 | 绑定 Compiler 实施 SR | 明确 Goal 执行及验收入口 | SR-013、Compiler #61 |
| 2026-11-25 | 0.1.4 | Codex | §7 | 登记规范与 Next 的职责冲突及 READY 判定 | 防止 DSH 误执行 M.4 | SR-013、ca-skills #88 |
| 2026-11-25 | 0.1.5 | Codex | §7 | 复审 #88 修订并更新发现状态 | 区分候选文本已解决与正式实施门槛 | SR-013、ca-skills #88 |
| 2026-11-25 | 0.1.6 | Codex | §6–7 | 固定已发布规范 SHA | ca-skills #89 固定规范来源 | SR-013 |
| 2026-11-25 | 0.1.7 | Codex | §7 | 回链实跑预检 | 记录已验证的交换路径和剩余范围 | SR-013 |
| 2026-11-25 | 0.1.8 | Codex | §5–7 | 更新隔离 PoC 入口 | 为 AC-013-01 提供可复现起点 | SR-013 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 补齐 Contract.when AST、G.4、Schema/Guard/Nullable lowering、CheckedExpr/DescriptorSet、新版 Artifact、Build/Verify、测试与发布边界；修正旧提示词和过期状态 | AC-013-01 已产生真实隔离 PoC 结果，后续阶段需要达到 Harness low-effort 可执行粒度 | Issue #14、SR-013、Compiler #61、F02、F08 |
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §2–7 | 补充 Contract.requestSchema 的独立运行期发布快照，区分 G.4 Schema 验证与 CEL DescriptorSet；明确 event.type-only when 不要求 requestSchema | 对齐 CA-SL v1alpha5 M.2/M.3，修复 Host 运行期缺少 Request Schema 数据的发布契约缺口 | Issue #14、SR-013、Compiler #61、F02、F08 |
| 2026-11-25 | 0.2.2 | GPT-6.2（ChatGPT） | §5.3 | 明确根 Schema 未声明 $id 时使用 sourceRef/rootPath，不虚构 Schema URI；仅真实声明的 $id 进入资源映射 | 避免将 G.4 非强制的根 $id 变成额外作者约束 | Issue #14、SR-013、Compiler #61 |
| 2026-11-25 | 0.2.3 | GPT-6.2（ChatGPT） | §1～9 | 同步 F02/F08/SR-013 新版本，并将 AC-013-01 证据状态明确为报告 PASS、远端证据未归档、独立复核未运行 | 防止隔离 PoC 报告被误认作 Compiler 产品发布或完整 SR 验收 | Issue #14；PR #16/#18；SR-013 |
| 2026-11-25 | 0.2.4 | GPT-6.2（ChatGPT） | §1～9 | 同步 F02/F08/SR-013 最新版本引用，明确 AC-013-01 证据 commit 远端不可检索、证据未归档 | 防止报告 PASS 被误报为独立复核或产品实现 PASS | Issue #14；PR #16/#18；SR-013 |
| 2026-11-25 | 0.2.5 | Codex | 正文 | 同步隔离 PoC 的固定归档与复跑状态 | 核对 Issue #12 与固定提交 | Issue #12 |
| 2026-11-26 | 0.2.6 | Codex / GPT-6 | 见本行变更 | 将实际 Bundle CI/发布归入 ca-skills 生产端 SR-027 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.7 | Codex / GPT-6 | 见本行变更 | 将未发布 Runtime Artifact 与 BuildResult 的候选版本段改为纯数字 2，保留 Owner 冻结门禁 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.8 | GPT-6（ChatGPT） | 新增 1.6.0 目标章节、状态及修订记录 | 移植一对一 Binding / Selector / Action 设计并标为待评审 | 无旧版兼容或产品完成承诺 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.9 | GPT-6（ChatGPT） | §1、§5～7、修订记录 | 移除新 Compiler 复用 v1alpha5 BuildRequest/DependencyInspection/Verify 的旧假设，唯一目标为 1.6.0 DTO/Artifact，历史包在新版明确拒绝 | 贯彻 Issue #40 全链路无兼容、无双轨/迁移；准确机器标识待 Compiler Owner 冻结 | Issue #40；SR-029；SR-013 |
| 2026-11-26 | 0.2.10 | GPT-6（ChatGPT） | 规范性设计与验收门槛 | 修复 Parser/Build/Manifest 的 v1alpha5 新实现要求，并补齐 1.6.0 空根与发布职责 | 修复新旧语言/能力运行时冲突 | Issue #12/#40；SR-013/025/029；PR #46 |
| 2026-11-26 | 0.2.11 | GPT-6（ChatGPT） | §1、§9～§11、修订记录 | 明确 Schema-only Interface Package 仅由 Contract.contexts 引用并进入 Schema dependency closure，且零 Capability roots 与零 Package dependency closure 是不同概念；增加 SR-013 AC-013-06 / SR-030 AC-030-03 联合验收入口 | 防止 Compiler Linker 把 Schema-only Package 错误当成 Capability root，或要求虚构 Callable 满足旧结构 | Issue #12/#40；SR-013、SR-029、SR-030；PR #46 |
| 2026-11-26 | 0.2.12 | GPT-6（ChatGPT） | §10.2、§11.1、修订记录 | 收紧 Schema-only Package 的引用入口为 Contract.contexts，requestSchema 仍由 Skill 自有 Schema 提供 | 与 CA-SL 1.6.0 / SR-030 的 Request Schema 与 Host Context Schema 所有权边界一致 | Issue #12/#40；CA-SL 1.6.0；SR-013、SR-030；PR #46 |
| 2026-11-27 | 0.2.13 | Codex / GPT-6 | Provider 一对一映射 | 区分查询 2/2 与包含 Codec 的 3/3 | 与 SR-029、F06 的发布范围对齐 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.14 | ChatGPT / GPT-6 | 3GPP Schema 与阶段输入补充 | 明确公共 Schema-only 导出、选择期 Request 与执行期 Codec Result 的 Link / 业务字段来源 | 关闭 Create 选择前依赖 NAS 解码的循环、固定跨包类型门禁 | IR-009；Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.2.15 | ChatGPT / GPT-6 | 本轮 IR-009 设计修正 | 固定 OpenAMSM 版本 + 原版 YAML 逐字节代发布；显式区分可选 Adapter 与 Provider Codec 输出 | 落实原版 YAML 不得改动、消除误把原版当 G.4 的风险 | Issue #47；SR-031/026/013 |
| 2026-11-27 | 0.2.16 | ChatGPT / GPT-6.2 | §12 | 以原生 OAS3 外部 Schema Component 引用替代强制 Adapter；定义 dialect-aware Resolver、pin、嵌套 refs、类型推导与失败门槛 | G.4 与 OAS 3.0 是不同 dialect，不能用投影替代原版标准 | IR-009；Issue #47；SR-013/031 |
| 2026-11-27 | 0.2.17 | ChatGPT / GPT-6.2 | §12 | 明确 selected-surface lazy Resolver、RFC 3986 / 6901 引用解析、PostSmContexts 四文件闭包及实际 OAS3 关键字 / 组合类型推导 | 避免全文件 eager resolve、漏锁传递引用和把 union / allOf 语义混为一谈 | IR-009；Issue #47；SR-013/031；EC01 |
| 2026-11-27 | 0.2.18 | ChatGPT / GPT-6.2 | §12 | 将 CEL union 字段收紧为各分支 required；核准实际 additionalProperties / format 形态与 default 注解语义 | 防止静态类型误判可选字段，并使 Golden 覆盖真实 OAS3 dialect | IR-009；Issue #47；SR-013/031；EC01 |
| 2026-11-27 | 0.2.19 | ChatGPT / GPT-6.2 | §12 Manifest / Build / Verify | 移除 sourceDigest 与 outputFiles SHA-256；Build / Verify 不计算或比较 SHA-256 / checksum / digest | 遵守 Demo 全链路无 hash 校验要求，避免 Compiler 产物另行引入完整性门禁 | IR-009；Issue #47；SR-013；CA-SL 1.6.0 |
| 2026-11-27 | 0.2.20 | ChatGPT（GPT-6.2） | §1、§5.2～§5.3、§6、§12 | 将 Request Schema Artifact / Manifest 闭包按 dialect 分型；本地 G.4 写入规范化 Artifact，外部 OAS3 只引用精确 pin 的 Source Bundle 原件及 JSON Pointer；when 类型位置引用也改为 dialect-aware | 使 Build/Verify、Manifest、Bundle、Host 对 OAS3 原始 bytes、Schema 定位与运行期离线闭包有唯一一致的所有权表达 | Issue #49/#47；IR-008/009；SR-013/031；PR #52 |
| 2026-11-28 | 0.2.21 | GPT-6.2（ChatGPT） | 文档头、§1、修订记录 | 同步 1.6.0-only Compiler 实施入口至 #62，并纳入 PR #52 作者资源 / Script Registry 与 OAS3 dialect-aware Artifact 表示 | 避免 1.6.0 实施继续指向历史 #61；保持本地 G.4 与外部 OAS3 的 Artifact/Manifest 分型 | Issue #40/#47/#49/#62；IR-008/009；SR-013/031/032；PR #52/#115 |
| 2026-11-28 | 0.2.22 | GPT-6.2（ChatGPT） | §1、§5.1、§5.1.1、修订记录 | 固定 CA-SL 1.6.0 languageTarget、Compiler 3.0.0 与四项机器 API /2 目标 | 将 Compiler 机器契约从 Owner 待命名候选收敛为 Next 唯一设计目标，保留正式 Schema/Release 未发布状态 | Issue #113；SR-013；SR-027；F08；CA-SL 1.6.0；PR #115 |
| 2026-11-28 | 0.2.23 | GPT-6（ChatGPT） | §5.1、§9、§11、修订记录 | 修复重复创建 Compiler #62 Issue 口径；Bundle 归 ca-skills；Owner 最终 22/23/24 一对一基数需两项 Parser 分别签认 | 避免 EC02 意外回退 F06/SR-029/EC05 已确定的责任与条件合同 | Issue #50/#40/#113；Compiler #62；PR #115 |
