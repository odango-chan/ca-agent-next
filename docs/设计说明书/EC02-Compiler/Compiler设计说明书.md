# CA-SL Compiler 设计说明书

> 文档版本：0.2.16\
> 状态：**设计待评审**（CA-SL 1.6.0 Capability-first 增量设计；实施及外部发布仍 NOT_RUN）
> 修订日期：2026-11-27
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、签名、Trust Registry、生产资格及真实 5GC/MAS 认证。

关联 [IR-003](../../IR/IR%20总登记册.md#ir-003)、[IR-006](../../IR/IR%20总登记册.md#ir-006)、[SR-012](../../SR/SR-012-Compiler设计归档与跨仓收敛.md)、[SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)、[Next Issue #14](https://github.com/odango-chan/ca-agent-next/issues/14) 和 [Compiler Issue #62](https://github.com/odango-chan/ca-skill-compiler/issues/62)（CA-SL 1.6.0-only）；旧 [Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) 仅保留 v1alpha5 历史范围。

## 1. 权威与版本边界

1. CA-SL 作者语义由 ca-skills 拥有。**唯一新产品语言目标为 CA-SL 1.6.0（尚未发布）**；准确机器 languageTarget 待 ca-skills / Compiler Owner 冻结。历史 v1alpha5 [normative SHA 18d8184](https://github.com/odango-chan/ca-skills/tree/18d8184367982ccbc835756136c4a53f9096c3a0) 仅作只读审计，不进入新 Parser/Build。
2. Compiler 产品基线为 v2.1.0；本轮实现审查基线为 [ca-skill-compiler commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb](https://github.com/odango-chan/ca-skill-compiler/tree/255ab85fa5abb4b0bf36656bf64250cafebf45cb)。
3. 已发布 Artifact **connectionagent.io/compiler-artifact/v1alpha5** 完全冻结，保持 Manifest、文件布局、字节、Build/Verify 行为及 Golden 不变。
4. Development Artifact **connectionagent.io/compiler-artifact/development/v1alpha1** 完全冻结，继续 **NOT_ADMITTED**；不得把它当作 Agent 可运行发布包。
5. Contract.when、Request Schema 根/闭包与 Capability→Callable Binding 必须共同进入**CA-SL 1.6.0 新 Runtime Artifact**；API 版本和语言机器标识独立，由正式 Owner Gate 冻结。新版不接受旧 v1alpha5 Artifact/BuildRequest/BuildResult，也不提供旧版 fallback。
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
| internal/compiler/v1alpha5_artifact.go、v1alpha5_artifact_verify.go、contracts/v1alpha5/artifact-manifest.schema.json | 冻结 v1alpha5 Artifact 只输出 procedure.json / ingress-links.json；sourceFiles 只记录源路径，不携带本地 Request Schema 字节 | 新 2 必须发布已验证 Request Schema 根与完整 G.4 引用闭包，供 Host 按 CA-SL 1.6.0 正式输入契约验证 Event input；具体 M.3 等价规则由 1.6.0 Publisher 冻结，不得直接沿用冻结 v1alpha5 |
| internal/compiler/development_link.go、development_multi_skill_test.go | Development Link / 多 Skill Lock 测试 | 仅作为 Schema 作用域和多 Skill fixture 的参考；不是正式发布 Artifact 路径 |

AC-013-01 的 PoC 通过 Development 多 Skill 共享 Lock fixture，复用了 buildSchemaRegistry、resolveReferenceFrom 和 resolveSchemaRoot 等真实 Schema 解析能力。这证明的是可复用的 Schema 解析与跨语言序列化路径，不代表产品 Build 应调用 validateDevelopmentRequest、buildDevelopmentLinkScope 或 newDevelopmentSemantics。

**1.6.0 正式实现约束：** 新 when 编译必须进入 CA-SL 1.6.0 唯一 Runtime Build 路径和统一 Go Compiler Core。若现有 Schema Registry 实现被 Development 入口包裹，先将必要的纯解析/闭包能力抽到共享内部层，再由正式与 Development 语义路径各自调用；不得让正式发布 Build 依赖 Development Request、Development Artifact、Host Admission Requirements 或 NOT_ADMITTED 状态，也不得改变 Development v1alpha1 的契约与行为。

## 3. Contract.when 静态编译设计

### 3.1 作者源与 AST

- 唯一作者位置：skills/<skill-name>/assurance/contract.yaml 的可选顶层 when。
- when 是非空 YAML 字符串；其内容是 CA-SL 1.6.0 正式规范冻结的 G.4 CEL 表达式；v1alpha5 G.4 仅作历史审计参考，不自动继承，静态结果类型必须为 bool。
- ContractAST 增加可选 when 节点，并保留原始表达式、SourcePath、行列范围。
- 不在 SKILL.md Front Matter 增加 when；不创建 constraint.yaml、activation.yaml、Applicability Package 或第二份 Contract；不把 when 放进 predicates.yaml。
- 不声明 when 的 Skill 不生成 CheckedExpr 或 DescriptorSet 文件；Agent 端按正式 CA-SL 选择规范处理未声明 when 的候选。
- 空字符串、非字符串、非法 CEL、未知字段、无效类型及不允许的语法，使用现有 CA-SL 诊断体系阻断构建。语义错误使用 CEL_INVALID；不得另造一套互不兼容的 WHEN 诊断码。

### 3.2 CEL 输入环境

每个 Skill 独立建立 CEL 类型环境：

| 变量 | 类型 | 来源 |
|---|---|---|
| event.type | string | 当前候选：Host 规范化的 Event 类型字段；Event envelope、metadata 字段集/类型和规范化规则由 ca-skills Publisher 在 CA-SL 1.6.0 正式规范中冻结；不是已冻结或唯一字段 |
| input | 当前 Skill Request Schema 的闭合对象类型 | assurance/contract.yaml 的 requestSchema 及其已解析 Schema 闭包 |

约束：

- when 只能读取 ca-skills Publisher 已在 CA-SL 1.6.0 正式规范中冻结的 Event metadata 字段，以及当前 Skill requestSchema 中显式声明的 input 字段。当前候选只使用 `event.type`；不得将它视为唯一或已冻结的 Event 字段。
- when 引用 input 成员而没有 requestSchema，静态报 CEL_INVALID。
- 不允许读取 Runtime Context、Observation、Tool Result、Evidence、环境变量、时钟、文件、网络或可变 Host 状态。
- Event envelope、metadata 字段集/类型与规范化规则由 ca-skills Publisher 在 CA-SL 1.6.0 正式规范中冻结；Host/Plugin 边界负责按该契约校验和规范化。Compiler 只为 Publisher 已冻结且表达式实际引用的 Event metadata 字段建立类型描述；当前 `event.type` 仅为候选。
- 每个 Skill 使用自己的 Request Schema 根、Reference 闭包和类型环境。共享 Lock 不等于共享所有 Skill 的私有 Schema 根。

### 3.3 G.4 CEL 表达式剖面

以下 G.4 / CEL 语法表是 Next 当前候选剖面；只有 ca-skills Publisher 将其纳入并冻结于 CA-SL 1.6.0 正式规范后，Compiler 才能按该剖面实施。冻结前不得将候选函数/宏、存在性与短路规则当作已发布契约。Compiler 不得因 cel-go 支持更多语法而自行扩大最终语言范围。

| 类别 | 允许范围 |
|---|---|
| 值类型 | string、int64、finite binary64 double、bool、null、nullable T、闭合 object、array/list<T> |
| 访问 | 已声明字段的静态点访问 |
| 布尔逻辑 | !、&&、\|\|、括号 |
| 比较 | ==、!=；同一数值类型的大小比较 |
| 存在判断 | has(x.field) |
| 长度 | size(x)，仅 string / array |
| Schema 约束 | required / optional、nullable、enum、const、范围和数组元素约束按已冻结 Schema 赋值规则检查 |

必须拒绝：所有算术运算符、动态索引、切片、动态成员名、对象构造、宏/推导式、反射、未声明函数、时间、随机数、外部数据访问及 G.4 未允许的结构。数组可以作为静态 Schema 类型并参与 size，但不允许数组索引。字符串只允许 == / !=；null 只允许相等/不等比较；大小比较仅限同一数值类型。has(x.field) 只检查已声明属性是否在本次对象中出现。枚举、const、范围、长度和数组元素约束由 G.4 Schema 验证保留；CEL 类型映射不得丢失底层标量类型或放宽这些约束。

CEL int 是有符号 64 位；double 是有限 IEEE-754 binary64。int/double 不隐式混合。静态不能证明表达式最终为 bool、字段类型或数值语义时，报 CEL_INVALID。

### 3.4 Schema-aware 类型检查与 Skill 隔离

正式编译按以下逻辑执行：

1. 对每个 Skill 读取同一次规范化 YAML 解析产生的 Contract AST。
2. 若该 Skill 声明 Contract.requestSchema，定位 Skill-owned G.4 Request Schema 根并解析完整 `$ref` 闭包。G.4 规则只校验该根；若引用原版 OpenAPI 3.0 Schema components，必须由 dialect-aware resolver 按 OAS3 语义解析和保留其约束，不得将 OAS3 资源强制套入 G.4、改写原件或静默丢弃 OAS3 关键字。若 when 实际引用 input，则 requestSchema 必须存在；若 when 只引用 event.type，则不要求声明 requestSchema，也不得虚构 input 类型。
3. 复用 Compiler 现有 Schema Registry 与 Reference Resolver。必要时抽取共享内部函数，但不得把 Development Build 的 Request/Artifact 契约搬进正式发布链。
4. 每个 when 的 CEL 环境只包含 Publisher 已冻结且表达式实际引用的 Event metadata 字段类型；当前候选 `event.type` 只有在 Publisher 正式冻结后才可注入。仅当表达式引用 input 时，才把当前 Skill 的 Request Schema 类型闭包加入类型环境和 DescriptorSet。event-only when 不依赖 Request Schema。若 Contract 已声明 requestSchema，即使 when 不引用 input，也仍须发布该 Skill-owned G.4 根及其 dialect-aware 引用资源，供 Host 按 Publisher 正式冻结的 Event/Input 校验契约验证 payload。
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
- 同一 Skill Artifact 的 when.types.pb 携带 google.protobuf.FileDescriptorSet，只包含该表达式实际引用且已由 Publisher 冻结的 Event metadata 字段类型；当前候选 `event.type` 只有在冻结后且被表达式引用时才包含。当 when 引用 input 时再包含该 Skill Request Schema 的必要类型闭包。DescriptorSet 只提供 CEL 类型描述，不完整表达 enum、const、minLength、数值范围等 G.4 Schema 断言，不能替代 Host 运行期 Request Schema 验证所需的 Schema 快照。
- Python 固定版本 cel-expr-python 使用 Env.deserialize(bytes) 直接加载同一 Any；DescriptorSet 用于构造对应 DescriptorPool 和 typed activation。
- Python 不解析 CEL 源字符串、不重新编译、不自行实现 CEL Parser/Type Checker，不使用 DynType 逃逸静态类型。
- 导入阶段反序列化一次；每个新 Event 仅传入新的 typed activation 求值。此消费端生命周期由 F02 / SR-004/005 负责。

### 4.2 已验证互操作基线

AC-013-01 报告采用 Go 1.26.6、cel-go 0.33.2、Go protobuf 1.36.10、CPython 3.14.6、cel-expr-python 0.1.4、Python protobuf 7.36.2。产品实现必须将实际依赖版本固定在 Compiler / Runtime 各自依赖文件中，并在 CI 中复跑；不能仅把 PoC 环境版本写入文档就视为产品依赖已锁定。

## 5. 新版发布 Runtime Artifact 设计

### 5.1 版本隔离

- connectionagent.io/compiler-artifact/v1alpha5 保持完全不变。
- Development v1alpha1 保持完全不变并继续 NOT_ADMITTED。
- 新发布 Runtime Artifact 使用唯一 1.6.0 版本化 Manifest/文件布局，准确 languageTarget 由 ca-skills / Compiler 正式冻结；不兼容旧包。
- 建议的新 Artifact API 候选为 connectionagent.io/compiler-artifact/2；对应的新 BuildResult API 候选为 connectionagent.io/compiler-build-result/2。**两者均为本设计提案，不是已冻结 API。** 新 BuildRequest / BuildResult / DependencyInspection 必须提供只面向 1.6.0 的唯一新 DTO 与机器身份；**禁止复用旧 v1alpha5 BuildRequest/DependencyInspection 作为新入口**，具体 Schema 由 Compiler Owner 冻结。新 Compiler 版本的正式 Runtime Build 只产生 2 BuildResult / Artifact，VerifyBuildResult 只接受该结果契约；不在同一二进制中双轨支持旧/新 Runtime BuildResult，不增加版本 dispatch、fallback 或兼容路由。旧 v2.1.0 Release 及其 Artifact/BuildResult v1alpha5 保持不可变历史发布。Development Build 继续使用其独立 v1alpha1 API/Artifact 家族，不因 when 扩展。AC-013-03 开始前 Compiler Owner 必须书面确认两个新 API version；如采用其他命名，先更新本节和 SR-013，再实施。Harness 不得自行发明第三个版本名。
- 不把 Development 专用 executionStatus=NOT_ADMITTED、hostAdmission 或 Skill Admission 状态写入新发布 Runtime Artifact。

### 5.2 候选文件布局

**Request Schema 与 OpenAPI dialect 边界：** `Contract.requestSchema` 的根是 Skill 自己维护的 G.4 文档；G.4 约束只适用于这个 Skill-owned root。该根可以直接引用 OpenAMSM 对应版本的原版 3GPP/OpenAPI 3.0 Schema components。原始 OpenAPI YAML 的 source bytes、相对 `$ref`、components 结构和 OAS3 dialect 必须保持不变；禁止改写、重新序列化、投影为 G.4 或强制生成 Adapter。Compiler 内部必须由 dialect-aware resolver 按资源来源 dialect 解析 `$ref`：Skill-owned root 按 G.4，原版 OpenAPI Schema Object 按 OAS3。内部类型分析/降低不得改变被引用源文件字节或静默丢弃 OAS3 语义。

该原则只冻结源文件与 dialect 边界；跨 dialect `$ref` 的具体解析算法、资源身份表示、Manifest 字段及 OAS3 conformance matrix 仍待 Compiler Owner / SR-031（PR #48）正式设计冻结。PR #48 尚未合并，本说明书不复制或预先批准其中未冻结的实现细节；未冻结前不得宣称跨 dialect resolver 已交付，也不得要求修改原版 3GPP YAML。

新版 Runtime Artifact 必须同时解决两类不同的运行时输入：Request Schema 校验数据与可选 when 程序。候选布局如下，精确文件名由 Compiler Owner 在 AC-013-03 定稿：

~~~text
manifest.json
skills/<skill-name>/compiled/procedure.json
skills/<skill-name>/compiled/ingress-links.json
skills/<skill-name>/compiled/request-schema/root.json
skills/<skill-name>/compiled/request-schema/resources/<resource>.json
skills/<skill-name>/compiled/when.checked.pb
skills/<skill-name>/compiled/when.types.pb
~~~

- 只要 Contract 声明 requestSchema，就必须输出 Skill-owned G.4 Request Schema 根及完整、可解析的 `$ref` 资源闭包；与 when 是否存在、是否读取 input 无关。根文件保留作者源字节；闭包中的原版 OAS3 资源保留原始字节和 OAS3 dialect，由 dialect-aware resolver 解析，不得转换为 G.4。
- 没有声明 requestSchema 时不输出 Request Schema 文件；只引用 Publisher 已冻结 Event metadata 字段的 event-only when 仍可编译，DescriptorSet 只包含表达式实际引用的 Event metadata 字段类型。当前候选仅为 `event.type`；Publisher 冻结前不得视为可实施正例。
- 只有声明 when 的 Skill 才输出 when.checked.pb 和 when.types.pb；无 when 时不生成空表达式或占位文件。
- when.checked.pb 是 Any 序列化字节；when.types.pb 是 CEL 类型所需的 FileDescriptorSet。Request Schema 文件保留完整 G.4 断言，不能用 DescriptorSet 代替。
- 根 Schema 与所有闭包资源保留精确 $id；Artifact 内部以 Manifest 的资源表完成 ID 到文件路径映射，运行期不得访问远端或作者工作区。
- 文件路径和资源映射是本设计候选值，Compiler Owner 必须在正式 Artifact Schema、Golden 和 PR 中定稿，不得同时保留多个兼容别名布局。

### 5.3 Manifest 最小语义

CA-SL 1.6.0 新 Manifest 由 Compiler Owner 重新冻结唯一 Schema；允许复用语义仍适用的字段名称，但不得以兼容旧 v1alpha5 Manifest 为目标，也不得直接修改冻结旧 Schema。新版 Schema 必须明确 apiVersion、languageTarget、validationScope、generator、dependencyClosure、skills、outputFiles、Request Schema root/resources、when CheckedExpr/DescriptorSet 和 capabilityBindings 的唯一结构及相互约束。

每个声明 Contract.requestSchema 的 Skill 增加 requestSchema 元数据对象，至少记录：

1. sourceRef：Contract.requestSchema 的作者相对路径。
2. rootPath：Artifact 内根 Schema 文件路径。
3. rootSchemaId：若根 Schema 声明 $id，则记录其精确值；未声明时省略，不得为其虚构 URI 身份，根以 sourceRef + rootPath 标识。
4. resources[]：覆盖完整、无循环的 `$ref` 闭包，并保留每个资源的原始引用身份、来源 dialect 与 Artifact path；源资源声明 `$id` 时保留其精确值，未声明时不得虚构 URI。原版 OAS3 components 的资源身份/字段映射由 Compiler Owner 在 SR-031 / PR #48 的 dialect-aware 设计中冻结，不得强制其满足 G.4 `schemaId` 形态。

requestSchema 对象与 when 是否存在无关；Host 依照 CA-SL 1.6.0 Publisher 正式冻结的 Event/Input 校验契约使用它。v1alpha5 M.3 仅作历史参考，不自动继承。所有根/资源文件同时进入该 Skill 的 compiledFiles[] 和 Manifest outputFiles[]；原版 OAS3 资源以原始字节进入资源快照，不做 dialect 投影。

仅为声明 when 的 Skill 增加 when 元数据对象，至少记录 checkedExprPath、descriptorSetPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）。当表达式引用 input 时，when 元数据还记录 requestSchemaRef 与 resolvedRequestSchemaPath，且必须与同一 Skill 的 requestSchema.rootSchemaId / sourceRef 一致；只访问 event.type 时可省略这两个引用字段。没有 when 时不输出 when 元数据。

建议字段名和文件名是本设计的实现默认值；Compiler Owner 在 AC-013-03 冻结 JSON Schema 前确认。when.checked.pb 与 when.types.pb 必须同时进入 compiledFiles[] 和 Manifest outputFiles[]；Request Schema 根与资源闭包也必须进入相同清单。outputFiles[].sha256 复用既有逐文件字节校验，sourceDigest 复用现有字段。不得增加第二套哈希字段、独立 SHA-256 体系、签名、Trust Registry 或包准入机制。

## 6. Build / Verify 责任与行为

### 6.1 Build

1. 通过 CA-SL 1.6.0 唯一新版本入口和正式解析/语义链；旧 v1alpha5 Build 入口由历史 Release 保持不变。
2. 对声明 requestSchema 的 Skill 发布 Skill-owned G.4 Schema 根和完整 dialect-aware 资源闭包，作为 Host 运行期输入校验数据；即使没有 when 也必须输出。原版 OAS3 资源保留原始 source bytes / `$ref`，不改写、不投影。
3. 对有 when 的 Skill 执行 §3 的 Schema-aware G.4 检查、Guard 分析和 typed lowering。只有表达式引用 input 时才使用 Request Schema 类型环境；event-only when 不要求 requestSchema。
4. 生成 CheckedExpr Any 与对应 DescriptorSet。
5. 按新 Runtime Artifact Manifest 组装完整产物；没有 when 的 Skill 不生成 when 文件。
5. 使用 RFC 8785 JCS、稳定排序和既有确定性约束；不得写入时间、随机值、绝对宿主路径或环境相关数据。
6. 任何静态检查或装配失败都返回完整诊断和空 OutputFiles，不返回部分 Artifact。

### 6.2 Verify

新版 Verify 必须检查：

- Artifact API version 与 languageTarget 精确受支持。
- Manifest、文件清单、路径、重复归属和必需文件完整。
- Skill-owned G.4 Request Schema 根按 G.4 验证；引用的 OAS3 Schema resources 按 OpenAPI 3.0 dialect-aware 解析并保留其原生约束。原始 source bytes 与相对 `$ref` 不变；不存在未解析、越界或重复资源。
- 每个 CheckedExpr Any 可反序列化，type URL 与标准类型一致。
- 每个 DescriptorSet 可解析，所有 CheckedExpr 类型引用均可解析。
- CheckedExpr 最终类型为 bool；引用 input 时，其类型闭包必须与该 Skill 的 Request Schema root/closure 精确匹配。event-only when 不得被强制要求 Request Schema。
- when 源路径/位置、程序路径和 DescriptorSet 路径相互一致。
- 不存在跨 Skill 私有 Schema 或 Descriptor 引用。
- 无 when 的 Skill 不得带伪造/空的 when 程序；但若其 Contract 声明 requestSchema，仍必须携带 Schema 根和闭包。
- DescriptorSet 只负责 CEL 类型，不得被当作完整 Schema 验证器；Request Schema 快照必须保留 Skill-owned G.4 根的 enum/const/范围/长度/数组约束，并保留被引用 OAS3 resources 的原生 dialect 约束，不得静默投影或丢弃 OAS3 关键字。
- BuildResult、Manifest 与 OutputFiles 的集合和字节一致。

新版 Verify 仅接受 1.6.0 新 BuildRequest/BuildResult/Artifact，执行完整重建/逐文件比较或 Compiler Owner 冻结的等价确定性复验；新 Compiler 不支持任何旧 v1alpha5 DTO、Artifact、双轨 dispatch 或兼容 fallback。旧 v2.1.0 Release 保留旧 BuildResult/Artifact v1alpha5 的原有行为；Development Build 仍由独立 Development API v1alpha1 处理。当前 CLI 已在写入目录前用同一 Verify 函数验证成功 BuildResult；新版本必须保持“先 Verify、后原子写盘”的既有不变量，不得假设存在一个已发布 Artifact 的独立 CLI verify 子命令。

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
| Presence / Null | Missing、Explicit Null、Value；optional `has()` 守卫；nullable 非 null 守卫；嵌套 optional ancestor；缺失 requestType 在守卫后得到 false 而非 CEL error；无守卫读取作为负例 |
| Boolean Flow | AND、OR、NOT、安全/不安全 OR、左到右短路和事实汇合 |
| Numeric | int64 最小/最大值、finite double、非有限值拒绝、int/double 混用拒绝 |
| Isolation | 多 Skill 共享 Lock、每 Skill Request Schema 根、跨 Skill 字段借用拒绝 |
| Serialization | Go CheckedExpr Any + DescriptorSet；Python 直接反序列化同一字节；18/18 PoC 基线扩展为正式 fixtures |
| Artifact | 新版 Build/Verify、Skill-owned G.4 根与 dialect-aware `$ref` 闭包发布/验证、原版 OAS3 source bytes 和相对 `$ref` 保持不变、无强制 Adapter、损坏文件拒绝、缺失 Descriptor 拒绝、无 when、重复构建确定性 |
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
- ca-skills CI 负责选取并固定稳定 Compiler Release、编译 Assurance Skill、验证结果，并按 ca-skills Bundle 契约组装 SKILL.md 与发布 Artifact。该工作由 F08 与 SR-027 追踪，不归入 Compiler #62 的代码实现。
- Next Agent 只消费正式发布 Bundle；导入、Catalog、CEL 反序列化和每 Event 求值由 F02 / SR-004/005/006 验收。Next 不内置 Compiler、不调用 Compiler 命令、不实现 Skill Admission。
- Compiler Release、ca-skills Bundle Release、Next Runtime E2E 是三个独立证据层。一个通过不能替代另一个。

## 9. 当前状态与 SR-013 阶段关系

- CA-SL 1.6.0 normative source、Schema 和 languageTarget 尚未正式发布/冻结；v1alpha5 规范 SHA 仅用于历史审计。
- AC-013-01 隔离 PoC 的固定归档、18/18 报告和完整性复核见 SR-013 §3；本轮复跑 NOT_RUN。
- AC-013-02 正式 Contract.when 编译：NOT_RUN。
- AC-013-03 新版 Runtime Artifact Schema/API：待 Compiler Owner 对 §5.1 候选版本作明确确认。
- AC-013-04 Build/Verify 与产品门禁：NOT_RUN。
- AC-013-05 Compiler Release 资产：依赖 AC-013-01～04 和单独发布授权，BLOCKED。
- SR-013 整体保持 DRAFT；本设计补充不代表 Compiler 产品代码已实施、PR 已合并或 Release 已发布。

## 10. Capability 静态链接与 Runtime Artifact v2 绑定

### 10.1 输入语义

本节是 SR-029 对现有 Artifact v2 候选的增量要求。新候选只面向 CA-SL 1.6.0；v1alpha5 / Compiler v2.1.0 已发布路径保持冻结，Development v1alpha1 继续 NOT_ADMITTED。

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

Link 阶段不访问 Provider 动态 catalog，也不选择 backendOperationId。Provider 内部的多 handler 路由由 Callable 的封闭 Input Schema 决定。

### 10.3 Artifact v2 Capability Binding

既有候选 API connectionagent.io/compiler-artifact/2 与 connectionagent.io/compiler-build-result/2 保持候选名称；本次将其唯一 languageTarget 更新为 （1.6.0 languageTarget 机器标识待发行方冻结）。它们尚未通过 Compiler Owner Gate，不是已冻结 API。新 BuildRequest 必须 1.6.0-only，精确字段经 Compiler Owner Gate 冻结。

每个 Skill 的 Manifest 增加 capabilityBindings[]。每项至少包含：

- capabilityId：作者源使用的 Capability ID；
- dependencyId / stablePackageId：解析来源；
- owner 或 publisher identity：所属契约权威；
- callableId：唯一内部 Callable ID；
- kind / effect：ToolCatalog 或 Interface Package 的规范值；
- inputSchemaRef / outputSchemaRef：对应 Package 的精确 Schema 引用。

编译后的 Procedure 节点保留 capabilityId；capabilityBindings[] 是 capabilityId 到 callableId 的唯一内部映射。Manifest 的 dependencyClosure.exports[] 仍列出精确 operation / observation Callable exports，Runtime 继续从该闭包建立 Callable allowlist。Capability ID 不是运行时模型选择器；Callable ID 不暴露给模型。

### 10.4 稳定诊断与失败行为

至少定义以下稳定诊断：CAPABILITY_UNRESOLVED、CAPABILITY_AMBIGUOUS、CAPABILITY_NOT_GRANTED、CAPABILITY_GRANT_UNUSED、CAPABILITY_CALLABLE_CARDINALITY_INVALID、CALLABLE_CAPABILITY_CARDINALITY_INVALID、CAPABILITY_PHASE_KIND_MISMATCH、CAPABILITY_SCHEMA_MISMATCH、CAPABILITY_BINDING_MISSING。

任何 Capability Link、Schema、Evidence、Scope 或 Artifact 装配错误均返回完整诊断和空 OutputFiles，不生成部分 Artifact。禁止 fallback 到 v1alpha5、Development 或动态 Provider catalog。

### 10.5 不变量

- v1alpha5 已发布 Artifact / Golden 和 Compiler v2.1.0 不变。
- 新 Artifact v2 只支持 languageTarget 1.6.0；新 Compiler 不解析旧版语法、旧 Build DTO 或 Artifact。
- Development v1alpha1 Schema / Golden 不变并继续 NOT_ADMITTED。
- 不增加包级 hash、签名、Trust Registry、Admission 或新的 Capability Manager；复用现有 Package identity、Schema 和文件清单机制。
- 本节由 SR-029 设计；SR-013 继续跟踪 when / Request Schema / Build / Verify / Release 的 Compiler 实施，AC-013-03 必须消费本节唯一 Artifact v2 目标。

**1.6.0-only 设计评审硬门槛：** 新 Compiler Parser/Check/Build/Verify/BuildRequest/BuildResult/Artifact 只支持 1.6.0。 此章节仅描述目标设计，外部代码/Release/E2E 均 NOT_RUN。


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
| 2026-11-27 | 0.2.10 | GPT-6.2（ChatGPT） | §2～7、§9、修订记录 | 将 when、G.4、Build/Verify、Manifest 和 Request Schema 的规范性目标统一为 CA-SL 1.6.0；旧 v1alpha5 仅作冻结历史与回归基线。 | 防止新 Compiler 沿用旧 v1alpha5 Build/Manifest/DTO 契约，保持与 SR-013、F08、SR-029 一致。 | Issue #40；SR-013；SR-029；F08 |
| 2026-11-27 | 0.2.11 | GPT-6.2（ChatGPT） | §2、§5.3、修订记录 | 同步 Compiler 1.6.0-only 新契约的 M.3 / Request Schema Owner Gate 与跨文档当前版本引用；旧 v1alpha5 仅保留历史冻结语义。 | 避免将历史 v1alpha5 规范或 DTO 隐式复用为 CA-SL 1.6.0 的规范性输入。 | Issue #40；SR-004/013/027/029；EC02；F08；PR #45 |
| 2026-11-27 | 0.2.12 | GPT-6.2（ChatGPT） | §3.3、修订记录 | 修复 G.4 布尔运算符 `\|\|` 在 Markdown 表格中被识别为列分隔符，保留原有 1.6.0 语义 | 确保 CA-SL 1.6.0-only 评审输入和当前文档结构无歧义。 | Issue #40/#12；PR #45；SR-013/SR-029 |
| 2026-11-27 | 0.2.13 | GPT-6.2（ChatGPT） | §3.4、§5.2～§5.3、§6.1、§7、修订记录 | 明确 Skill-owned G.4 Request Schema root 与原版 OpenAPI 3.0 resources 的 dialect-aware $ref 边界；原件 source bytes/$ref 不变，不要求 Adapter；具体 resolver/Manifest 细节留给 SR-031/PR #48 冻结 | 避免 G.4 profile 误约束原版 OAS3 components，并防止在 PR #48 未合并时提前声称实现细节已冻结 | Issue #40；SR-013；SR-031；PR #45/#48 |
| 2026-11-27 | 0.2.14 | GPT-6.2（ChatGPT） | §6.2 Verify、测试矩阵、修订记录 | 修正 Verify 对混合 G.4/OAS3 引用资源的 dialect-aware 验收，保留 OAS3 原生约束与 source bytes | 避免 Verify 将 G.4 根规则错误应用到原版 OpenAPI 3.0 resources | Issue #40；PR #45；SR-004/013/027；SR-031/PR #48 |
| 2026-11-27 | 0.2.15 | GPT-6.2（ChatGPT） | §3.2～§3.5、§4.1、§5.2、修订记录 | 将 Event metadata/event.type 与 CEL has/短路剖面标记为 Publisher 冻结前候选；DescriptorSet 只收录实际引用的已冻结字段 | 避免将 event.type 单字段假设和候选 CEL 宏误报为已发布规范 | Issue #40/#49；SR-013/029；PR #45/#52 |
| 2026-11-27 | 0.2.16 | GPT-6.2（ChatGPT） | EC02 设计入口与发布责任 | 将 EC02 当前 Compiler 实施入口改为 #62，保持 #61 的历史版本范围不变。 | 区分 Compiler 新目标与历史发布资产的责任边界。 | Issue #40/#62；PR #45 |
