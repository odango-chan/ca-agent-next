# CA-SL Compiler 设计说明书

> 文档版本：0.2.0  
> 状态：设计补充待评审；Compiler 实施由 SR-013 跟踪  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、签名、Trust Registry、生产资格及真实 5GC/MAS 认证。

关联 [IR-003](../../IR/IR%20总登记册.md#ir-003)、[IR-006](../../IR/IR%20总登记册.md#ir-006)、[SR-012](../../SR/SR-012-Compiler设计归档与跨仓收敛.md)、[SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)、[Next Issue #14](https://github.com/odango-chan/ca-agent-next/issues/14) 和 [Compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。

## 1. 权威与版本边界

1. CA-SL 作者语义由 ca-skills 拥有。当前目标保持 **connectionagent.io/v1alpha5**；本设计固定的规范来源为 [ca-skills commit 18d8184367982ccbc835756136c4a53f9096c3a0](https://github.com/odango-chan/ca-skills/tree/18d8184367982ccbc835756136c4a53f9096c3a0)。
2. Compiler 产品基线为 v2.1.0；本轮实现审查基线为 [ca-skill-compiler commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb](https://github.com/odango-chan/ca-skill-compiler/tree/255ab85fa5abb4b0bf36656bf64250cafebf45cb)。
3. 已发布 Artifact **connectionagent.io/compiler-artifact/v1alpha5** 完全冻结，保持 Manifest、文件布局、字节、Build/Verify 行为及 Golden 不变。
4. Development Artifact **connectionagent.io/compiler-artifact/development/v1alpha1** 完全冻结，继续 **NOT_ADMITTED**；不得把它当作 Agent 可运行发布包。
5. Contract.when 需要新的、独立版本化的发布 Runtime Artifact。它的 Artifact API 版本与 CA-SL languageTarget 是两个独立版本维度；新产物仍声明 **languageTarget=connectionagent.io/v1alpha5**。
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
| internal/compiler/development_link.go、development_multi_skill_test.go | Development Link / 多 Skill Lock 测试 | 仅作为 Schema 作用域和多 Skill fixture 的参考；不是正式发布 Artifact 路径 |

AC-013-01 的 PoC 通过 Development 多 Skill 共享 Lock fixture，复用了 buildSchemaRegistry、resolveReferenceFrom 和 resolveSchemaRoot 等真实 Schema 解析能力。这证明的是可复用的 Schema 解析与跨语言序列化路径，不代表产品 Build 应调用 validateDevelopmentRequest、buildDevelopmentLinkScope 或 newDevelopmentSemantics。

**正式实现约束：** 新 when 编译必须进入正式 CA-SL v1alpha5 发布 Build 的统一 Core。若现有 Schema Registry 实现被 Development 入口包裹，先将必要的纯解析/闭包能力抽到共享内部层，再由正式与 Development 语义路径各自调用；不得让正式发布 Build 依赖 Development Request、Development Artifact、Host Admission Requirements 或 NOT_ADMITTED 状态，也不得改变 Development v1alpha1 的契约与行为。

## 3. Contract.when 静态编译设计

### 3.1 作者源与 AST

- 唯一作者位置：skills/<skill-name>/assurance/contract.yaml 的可选顶层 when。
- when 是非空 YAML 字符串；其内容是 CA-SL v1alpha5 G.4 允许的 CEL 表达式，静态结果类型必须为 bool。
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

Compiler 必须实现 CA-SL v1alpha5 G.4，不得因 cel-go 支持更多语法而扩大语言范围。

| 类别 | 允许范围 |
|---|---|
| 值类型 | string、int64、finite binary64 double、bool、null、nullable T、闭合 object、array/list<T> |
| 访问 | 已声明字段的静态点访问 |
| 布尔逻辑 | !、&&、||、括号 |
| 比较 | ==、!=；同一数值类型的大小比较 |
| 存在判断 | has(x.field) |
| 长度 | size(x)，仅 string / array |
| Schema 约束 | required / optional、nullable、enum、const、范围和数组元素约束按已冻结 Schema 赋值规则检查 |

必须拒绝：动态索引、切片、动态成员名、对象构造、宏/推导式、反射、未声明函数、时间、随机数、外部数据访问、算术类型隐式混用及 G.4 未允许的结构。数组可以作为静态 Schema 类型并参与 size，但不允许数组索引。枚举约束由 Schema 闭包和输入校验保留；CEL 类型映射不得丢失底层标量类型或放宽 enum/const 约束。

CEL int 是有符号 64 位；double 是有限 IEEE-754 binary64。int/double 不隐式混合。静态不能证明表达式最终为 bool、字段类型或数值语义时，报 CEL_INVALID。

### 3.4 Schema-aware 类型检查与 Skill 隔离

正式编译按以下逻辑执行：

1. 对每个 Skill 读取同一次规范化 YAML 解析产生的 Contract AST。
2. 从该 Skill 的 Contract.requestSchema 定位 Request Schema 根；解析 $ref 闭包，验证根类型、闭合性、字段、必需性、可空性、enum/const、范围和数组元素。
3. 复用 Compiler 现有 Schema Registry 与 Reference Resolver。必要时抽取共享内部函数，但不得把 Development Build 的 Request/Artifact 契约搬进正式发布链。
4. 以当前 Skill 的 Request Schema 闭包构造 CEL 类型环境和 DescriptorSet。event.type 使用统一 Host Event 类型定义。
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
- CEL parse、类型、字段、守卫、G.4 结构和 lowering 错误统一进入现有 Compiler Diagnostic[]，语义不合规使用 CEL_INVALID。
- 错误信息至少指出 Skill、SourcePath、表达式位置、字段路径和失败原因。
- 不引入新的诊断注册表或独立诊断阶段。
- 未知、错误或不能求值的表达式不得生成可执行 Artifact。

## 4. Go → Python CheckedExpr 互操作契约

### 4.1 标准消息

- Go Compiler 使用 cel-go 解析和检查源表达式，导出标准 cel.dev/expr.CheckedExpr Protobuf。
- 用 google.protobuf.Any 包装；互操作验证要求 Any type URL 为 type.googleapis.com/cel.expr.CheckedExpr。不得直接把 cel-go 的旧 google.api.expr.v1alpha1.CheckedExpr type URL 当成 Python 可消费类型。
- 同一 Skill Artifact 携带 google.protobuf.FileDescriptorSet，包含 event.type 与该 Skill Request Schema 的必要类型闭包。
- Python 固定版本 cel-expr-python 使用 Env.deserialize(bytes) 直接加载同一 Any；DescriptorSet 用于构造对应 DescriptorPool 和 typed activation。
- Python 不解析 CEL 源字符串、不重新编译、不自行实现 CEL Parser/Type Checker，不使用 DynType 逃逸静态类型。
- 导入阶段反序列化一次；每个新 Event 仅传入新的 typed activation 求值。此消费端生命周期由 F02 / SR-004/005 负责。

### 4.2 已验证互操作基线

AC-013-01 报告采用 Go 1.26.6、cel-go 0.33.2、Go protobuf 1.36.10、CPython 3.14.6、cel-expr-python 0.1.4、Python protobuf 7.36.2。产品实现必须将实际依赖版本固定在 Compiler / Runtime 各自依赖文件中，并在 CI 中复跑；不能仅把 PoC 环境版本写入文档就视为产品依赖已锁定。

## 5. 新版发布 Runtime Artifact 设计

### 5.1 版本隔离

- connectionagent.io/compiler-artifact/v1alpha5 保持完全不变。
- Development v1alpha1 保持完全不变并继续 NOT_ADMITTED。
- 新发布 Runtime Artifact 使用独立版本化 Manifest/文件布局，languageTarget 仍为 connectionagent.io/v1alpha5。
- 建议的新 Artifact API 候选为 connectionagent.io/compiler-artifact/v2alpha1，用于表达与冻结 v1alpha5 不兼容的发布结构。**这是本设计提案，不是已冻结 API。** AC-013-03 开始前 Compiler Owner 必须书面确认 API version；如采用其他命名，先更新本节和 SR-013，再实施。Harness 不得自行发明第三个版本名。
- 不把 Development 专用 executionStatus=NOT_ADMITTED、hostAdmission 或 Skill Admission 状态写入新发布 Runtime Artifact。

### 5.2 候选文件布局

在现有发布产物结构上按需增加 when 文件；精确文件清单由 Compiler Owner 在 AC-013-03 定稿：

~~~text
manifest.json
skills/<skill-name>/compiled/procedure.json
skills/<skill-name>/compiled/ingress-links.json
skills/<skill-name>/compiled/when.checked.pb
skills/<skill-name>/compiled/when.types.pb
~~~

- 只有声明 when 的 Skill 才输出 when.checked.pb 和 when.types.pb。
- 无 when 的 Assurance Skill 不生成空表达式或占位文件。
- when.checked.pb 是 Any 序列化字节；when.types.pb 是 FileDescriptorSet。
- 文件路径是本设计的建议值，Compiler Owner 必须在正式 Artifact Schema、Golden 和 PR 中定稿，不得同时保留多个别名布局。

### 5.3 Manifest 最小语义

Manifest 对每个有 when 的 Skill 至少记录：

1. CheckedExpr 文件路径。
2. DescriptorSet 文件路径。
3. 当表达式引用 input 时使用的 Request Schema 精确身份；仅引用 event.type 时可省略。
4. 作者源路径 assurance/contract.yaml。
5. when 表达式的精确源码位置。
6. 该 Skill 的程序与 DescriptorSet 归属，确保 Verify 能拒绝跨 Skill 引用。

字段命名以 Compiler Owner 定稿的版本化 JSON Schema 为准；以上是必须具备的语义，不授权 Agent 自造字段。继续复用新版 Artifact 已有的文件清单、自校验与确定性机制，不增加额外 SHA-256 体系、签名、Trust Registry 或包准入机制。

## 6. Build / Verify 责任与行为

### 6.1 Build

1. 通过现有单一版本入口和正式 CA-SL v1alpha5 解析/语义链。
2. 对有 when 的 Skill 执行 §3 的 Schema-aware G.4 检查、Guard 分析和 typed lowering。
3. 生成 CheckedExpr Any 与对应 DescriptorSet。
4. 按新 Runtime Artifact Manifest 组装完整产物；没有 when 的 Skill 不生成 when 文件。
5. 使用 RFC 8785 JCS、稳定排序和既有确定性约束；不得写入时间、随机值、绝对宿主路径或环境相关数据。
6. 任何静态检查或装配失败都返回完整诊断和空 OutputFiles，不返回部分 Artifact。

### 6.2 Verify

新版 Verify 必须检查：

- Artifact API version 与 languageTarget 精确受支持。
- Manifest、文件清单、路径、重复归属和必需文件完整。
- 每个 CheckedExpr Any 可反序列化，type URL 与标准类型一致。
- 每个 DescriptorSet 可解析，所有 CheckedExpr 类型引用均可解析。
- CheckedExpr 最终类型为 bool，类型闭包与该 Skill Request Schema 精确匹配。
- when 源路径/位置、程序路径和 DescriptorSet 路径相互一致。
- 不存在跨 Skill 私有 Schema 或 Descriptor 引用。
- 无 when 的 Skill 不得带伪造/空的 when 程序。
- BuildResult、Manifest 与 OutputFiles 的集合和字节一致。

新版 Verify 必须按 Compiler #61 的要求对新版本产物执行完整重建/逐文件比较或等价的确定性复验；若现有 VerifyBuildResult 无法表达该语义，新增版本化 Verify 入口，不改变冻结 v1alpha5 的行为。CLI 只有 Verify 通过后才能写入输出目录。

### 6.3 旧契约回归

每次新增 Artifact 版本都必须执行：

- 冻结发布 Artifact v1alpha5 的机器 Schema、Golden 字节和 Verify 行为不变。
- Development Artifact v1alpha1 的机器 Schema、Golden 字节、NOT_ADMITTED 与 Verify 行为不变。
- 新 Runtime Artifact 单独维护 Schema、Golden、正负例和版本说明。
- 不得通过更新旧 Golden 来掩盖旧契约变化。

## 7. 测试矩阵与产品门禁

| 类别 | 必测内容 |
|---|---|
| 作者格式 | 无 when、合法 when、空值、非字符串、重复 YAML Key、未知旧字段 |
| G.4 正例 | event.type、typed input、字段点访问、括号、布尔逻辑、比较、has、size、数组字段与枚举/const Schema 约束 |
| G.4 负例 | 未知字段、缺 requestSchema、非 bool、宏/推导式、动态索引、切片、对象构造、动态成员、外部函数、未支持语法 |
| Presence / Null | Missing、Explicit Null、Value；optional 守卫；nullable 非 null 守卫；嵌套 optional ancestor |
| Boolean Flow | AND、OR、NOT、安全/不安全 OR、左到右短路和事实汇合 |
| Numeric | int64 最小/最大值、finite double、非有限值拒绝、int/double 混用拒绝 |
| Isolation | 多 Skill 共享 Lock、每 Skill Request Schema 根、跨 Skill 字段借用拒绝 |
| Serialization | Go CheckedExpr Any + DescriptorSet；Python 直接反序列化同一字节；18/18 PoC 基线扩展为正式 fixtures |
| Artifact | 新版 Build/Verify、损坏文件拒绝、缺失 Descriptor 拒绝、无 when、重复构建确定性 |
| Compatibility | 冻结 v1alpha5 和 Development v1alpha1 Golden/字节回归 |
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

另需固定并实跑 Python cel-expr-python / protobuf 互操作测试。若现有仓库没有对应 Python 测试脚本，AC-013-04 必须新增可由 CI 调用的测试入口；提示词不得编造一个不存在的命令。每项记录仓库、受测 SHA、环境、依赖版本、命令、退出码和证据位置。

## 8. 发布边界与外部消费

- Compiler 的职责止于 Check、Build、Verify、Artifact Schema、Compiler Release 和可复现证据。
- ca-skills CI 负责选取并固定稳定 Compiler Release、编译 Assurance Skill、验证结果，并按 ca-skills Bundle 契约组装 SKILL.md 与发布 Artifact。该工作由 F08 与 SR-023 追踪，不归入 Compiler #61 的代码实现。
- Next Agent 只消费正式发布 Bundle；导入、Catalog、CEL 反序列化和每 Event 求值由 F02 / SR-004/005/006 验收。Next 不内置 Compiler、不调用 Compiler 命令、不实现 Skill Admission。
- Compiler Release、ca-skills Bundle Release、Next Runtime E2E 是三个独立证据层。一个通过不能替代另一个。

## 9. 当前状态与 SR-013 阶段关系

- CA-SL v1alpha5 规范来源和语言标识已固定。
- AC-013-01 隔离 PoC：用户报告 Go/Python 18/18 一致，见 SR-013 §3；本地证据尚未推送，独立复核仍待完成。
- AC-013-02 正式 Contract.when 编译：NOT_RUN。
- AC-013-03 新版 Runtime Artifact Schema/API：待 Compiler Owner 对 §5.1 候选版本作明确确认。
- AC-013-04 Build/Verify 与产品门禁：NOT_RUN。
- AC-013-05 Compiler Release 资产：依赖 AC-013-01～04 和单独发布授权，BLOCKED。
- SR-013 整体保持 DRAFT；本设计补充不代表 Compiler 产品代码已实施、PR 已合并或 Release 已发布。

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
