# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.1.10  
> 状态：DRAFT  
> 创建日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实施、生产准入、Owner Trust 治理及自动发布。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.1.8 §1–7 和 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) §1–5。SR-012 负责归档。

目标仓：`odango-chan/ca-skill-compiler`。范围覆盖 Go/Python 互操作 PoC、Compiler Contract AST 与语义检查、新版 Artifact Schema、Build/Verify、fixture、Golden 和产品门禁。保持单一 Go Core、语言 v1alpha5、冻结发布 Artifact v1alpha5 及 Development v1alpha1；Development 继续 `NOT_ADMITTED`。Next SR-004/005 消费实际发布 Bundle，运行时无 Compiler 或 Skill Admission。

产品实施启动条件：本 SR 经评审达到 READY，ca-skills #88 的 M.4 与 SA 导入职责已与 Next 对齐、正式发布且固定规范 SHA，具备目标仓写入授权和可运行 Go/Python 环境。本地隔离 PoC 按下方阶段执行单执行；通过后再要求 Compiler Owner 确认新版 Artifact API 版本和布局。合并或发布另行授权。

| 验收 ID | 通过条件 | 当前证据 |
|---|---|---|
| AC-013-01 | Go 生成的 CheckedExpr Any 与 FileDescriptorSet 被固定版本 Python 直接加载；G.4 跨语言 fixture 对 true/false/error、缺失/null 与数值边界一致 | 隔离 PoC PASS（18/18，见「AC-013-01 隔离 PoC 执行结果」）；产品实现 NOT_RUN |
| AC-013-02 | #61 的静态正负例、诊断位置和多 Skill 共享 Lock 时的类型隔离全部符合预期 | NOT_RUN |
| AC-013-03 | 新版 Build/Verify 确定、损坏时 fail-closed；冻结机器契约及两条冻结产物路径对基准的 Golden 字节一致 | NOT_RUN |
| AC-013-04 | #61 指定的 Go 测试、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 与 diff check 全部通过 | NOT_RUN |
| AC-013-05 | 经授权发布后，记录可下载的实际 Bundle、Release SHA、资产、契约版本与验证日志，供 SR-004/005 使用 | BLOCKED：依赖 AC-013-01～04 与发布授权 |

Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。规范依赖：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88)。设计 PR：[Next #3](https://github.com/odango-chan/ca-agent-next/pull/3)。实施 PR、Commit、实际命令、环境、受测 SHA 和证据待回填。替代关系：无。

正式 CA-SL v1alpha5 规范固定为 `18d8184367982ccbc835756136c4a53f9096c3a0`，见 [ca-skills 正式发布记录](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。此门槛已满足。Next PR #3 已合并；SR-013 的实施范围与验收仍待负责人确认，AC-013-01 为进入 READY 后的首项验收。

### AC-013-01 环境预检与最小交换实验

- Compiler 源：`255ab85fa5abb4b0bf36656bf64250cafebf45cb`。Windows amd64，Go 1.26.6，cel-go 0.33.2，cel.dev/expr 0.25.1，Go protobuf 1.36.10；隔离环境 CPython 3.14.6，cel-expr-python 0.1.4，protobuf 7.36.2。
- `GOWORK=off go test ./internal/compiler -run '^$' -count=1` 退出 0，仅验证 Compiler 包能编译。Python 使用 `from cel_expr_python import cel` 与 `cel.NewEnv()`，可加载自己生成的表达式。
- 用 Go 编译常量 `true`。直接 `anypb.New(AstToCheckedExpr(...))` 产生 `type.googleapis.com/google.api.expr.v1alpha1.CheckedExpr`；Python `Env.deserialize` 拒绝，报告 INVALID_ARGUMENT。将 Go CheckedExpr protobuf 序列化，再解码为 `cel.dev/expr.CheckedExpr` 并用 `anypb.New` 包装，得到 `type.googleapis.com/cel.expr.CheckedExpr`；Python 直接加载该文件并求值为 true。以真实类型构造 Any，避免只替换类型 URL。
- 下一步按正式规范补完整 AC-013-01：Go 导出同一 typed when 的 Any 和 FileDescriptorSet；Python 用同一 DescriptorSet 构造 DescriptorPool；记录两端的 true/false/error、optional 与 null、数值边界和多 Skill 隔离。同一工具版本下重跑直接包装失败与标准类型成功的对照。仍须验证类型和语义字段在转换前后完整保留，由 Compiler Owner 据此定冻结的新 Artifact 字段。
- 本次是隔离工作区探针，未写入 Compiler 仓。AC-013-01 尚无完整验收证据。明确区分环境/常量探针通过、旧 Type URL 失败和 typed fixture 尚未运行。

### 已运行的 typed fixture 与未通过的 null 表示

使用同一组固定工具版本。Go 用 proto2 optional int64 构造 `ac013.Input.count`，静态编译 `kind == "create" && has(input.count) && input.count == 9223372036854775807`，导出实际 `cel.expr.CheckedExpr` Any 和 `FileDescriptorSet`。Python 以该文件构造 DescriptorPool、反序列化 Go 产物并调用同一表达式。Go 与 Python 均返回以下结果。

| 输入 | 预期与实际 |
|---|---|
| create，count 为 int64 最大值 | true |
| modify，count 为 int64 最大值 | false |
| create，count 缺失 | false |
| kind 缺失 | 求值失败；Python 返回 UNKNOWN，不能作为匹配 |

Go 静态编译另拒绝了未知字段和另一共享 descriptor 文件中未声明的字段。仅验证独立声明类型，实际 Compiler 多 Skill Lock 尚未验收。

**候选映射失败。** Python 动态 proto2 scalar message 中，传入 `count=None` 与省略 count 都令 `HasField("count")` 为 false。因此单一 optional scalar 映射不能承载 G.4 的显式 null 与缺失区别。AC-013-01 仍未通过。下一次验证应提出保留缺失、显式 null 与原始标量的候选表示，并同时证明 Go 静态类型与两端求值保持一致。未经该证据，不冻结新 Artifact 契约。该探针使用简化的 kind 字段和手工 descriptor，当前未验证正式 Event 对象、Schema Registry 生成路径、double 边界及产品级 Lock 隔离。

### Nullable 候选表示实跑与实现差异

使用同一 Go/Python 环境，将 nullable int64 表示为可缺失的消息字段，其 oneof 在已提供字段时区分显式 null 与 int64 分支。Go 导出实际 CheckedExpr Any 和同一 FileDescriptorSet，Python 直接反序列化。缺失时外层 `has` 为 false；显式 null 时外层 `has` 为 true、标量分支 `has` 为 false；int64 最大值按 int64 比较，两端结果一致。缺失 kind 的求值仍失败。该实验未使用 DynType，且未改变正式规范。

同一描述符直接编译原始作者表达式 `has(input.count) && input.count != null && input.count == 1` 失败：`_==_` 无 `(ac013.NullableInt, int)` 重载。已跑通的是手工写出的等价 wire 表达式。Compiler 固定基线的 `internal/compiler/cel_check.go` 也注明缺失 optional/null 守卫证明。因此 AC-013-01 仍未通过，且 AC-013-02 需要落实守卫检查。输入和输出格式仍待定稿。

下一步先用正式 G.4 规则实现并验证 Schema-aware 源表达式守卫检查，再在同一 Compiler Core 内验证从已检查的作者表达式到 typed wire AST 的转换。先覆盖 `has`、`== null`、`!= null`、安全标量读取和缺守卫拒绝，再扩至 G.4 允许的布尔组合、嵌套路径、有限 double 与跨 Skill 隔离。严禁以 wire 表达式替换作者语法、允许 DynType 或依赖运行时异常代替静态拒绝。候选 SHA 的证据按各自范围记录，由 Compiler Owner 在完整 PoC 通过后裁定 Artifact API。

### 作者表达式转换原型

[Go 原型](../参考与审计/fixtures/ac-013-01/lowering.go)读取原始 CEL，用 cel-go AST 对本样例的左到右短路守卫做检查，将 non-null guard 转成 scalar 分支存在检查，再用同一 CEL 库检查生成的表达式。直接加载其 CheckedExpr 和 DescriptorSet 的 [Python 验证](../参考与审计/fixtures/ac-013-01/lowering.py)实测与 Go 一致。缺少存在守卫、缺少非空守卫、错误的 OR 保护及 int/double 混用均被原型拒绝。Python 未重新编译源码。

复跑时固定 Compiler 到 `255ab85fa5abb4b0bf36656bf64250cafebf45cb`。将 Go 文件和 Python 文件复制到绝对路径的隔离证据目录。从 Compiler 源目录以 `GOWORK=off` 运行 `go run <证据目录>/lowering.go <证据目录>`，再用本节固定版本的 Python 运行同目录的 `lowering.py`。Go 生成 `lowered.checked.pb` 与 `lowered.types.pb`。

原型仅验证一个固定字段及有限运算。OR 负例是原型对该分支的拒绝，未证明通用 OR 分析。正式验收仍须覆盖 Schema Registry 闭包、嵌套路径、完整 G.4 布尔组合、有限 double、精确源诊断和实际多 Skill Lock。该原型作为 DSH 的复现输入，产品实现须在同一 Compiler Core 中复用现有 AST 和语义检查；不得将此固定字段原型并入产品。

### AC-013-01 隔离 PoC 执行结果（PASS）

在 Compiler `255ab85` 的隔离副本内，复用真实 `buildSchemaRegistry` / `resolveReferenceFrom` / `resolveSchemaRoot` 与多 Skill 共享 Lock fixture，为两个 Skill 各生成 Request Schema 的 `FileDescriptorSet`；`[T,"null"]` 用 oneof `{ value, is_null }` 包装，保持缺失、显式 null 与原始标量三态。作者表达式经 `has`、`== null`、`!= null` 与 AND/OR/NOT 短路事实检查后降级为 wire 表达式，再由 cel-go 编译并导出 `cel.expr.CheckedExpr` Any。Python 仅 `env.deserialize` 该产物，不解析源表达式。

| 项目 | 结果 |
|---|---|
| `GOWORK=off go vet ./internal/compiler` | 退出 0 |
| `GOWORK=off go test ./internal/compiler -run '^TestAC013PocGenerate$' -count=1 -v` | 退出 0 |
| `python_verify.py artifacts`（CPython 3.14.6 / cel-expr-python 0.1.4 / protobuf 7.36.2） | 退出 0，18/18 一致 |
| 缺失 / 显式 null / 有效值 | PASS：同一 optional+nullable 字段缺失为 false、显式 null 时 `== null` 为 true |
| AND / OR / NOT、嵌套路径、int64 与 finite double 边界 | PASS |
| 未知字段、缺 `has`、缺非 null 守卫、int/double 混用、不安全 OR、跨 Skill 借用 | 6/6 静态拒绝 |
| 求值错误 | PASS（缺 `event` 返回 UNKNOWN，不当作匹配） |
| 多 Skill Lock 隔离 | PASS（第二 Skill 使用自己的 Schema；跨 Skill 字段被拒） |

**AC-013-01 在隔离 PoC 范围内 PASS。** 证据：`.agent-tmp/ac-013-01-poc/EVIDENCE.md`、`go-test.log`、`python.log`、`artifacts/`（含 `cases.json` 与逐用例 `.checked.pb` / `.types.pb`）。本结论不外推为产品实现：`ContractAST.when`、Schema-aware 静态检查、发布 Artifact 字段与 Build/Verify 仍为 NOT_RUN；深层可选祖先、数组、枚举、完整布尔组合与 AC-013-02 待后续。新 Artifact API 仍由 Compiler Owner 定稿。

证据产物已改用确定性序列化：默认 `proto.Marshal` 对 `CheckedExpr` 的 `reference_map` / `type_map` 不稳定，同一输入两次运行会产生不同字节。该问题不影响求值语义，但未来发布 Artifact 若要求字节确定性，必须显式使用确定性序列化，供 AC-013-03 参考。

## AC-013-01 阶段执行单

**隔离 PoC 阶段：READY。** 本轮依据项目负责人委托处理到可执行位置，对隔离 PoC 作技术放行。SR-013 整体仍为 DRAFT。执行范围仅为本地临时副本的代码、fixture、测试与证据，Compiler 产品仓远程写入、契约定稿、合并、发布和 Next 消费实现各自沿用原门槛。

- 规范固定为 ca-skills `18d8184367982ccbc835756136c4a53f9096c3a0`，Compiler 目标为 `odango-chan/ca-skill-compiler` 的 `255ab85fa5abb4b0bf36656bf64250cafebf45cb` 的隔离副本。原型来源为 Next PR #7 固定提交 `5702e2c3dc19445cc807a598376451d10d61391d`。Go/Python 环境采用 AC-013-01 预检的固定版本。
- 先复跑 §作者表达式转换原型的文件和命令。Compiler 原仓基线已实跑 `GOWORK=off go test ./internal/compiler -count=1 -run 'TestDevelopmentMultiSkill|TestDevelopment.*Schema'`，退出 0。该结果仅覆盖现有 Schema/Lock，不覆盖新 `when`。
- 在隔离副本内利用 `buildSchemaRegistry`、`resolveReferenceFrom` 和 `resolveSchemaRoot` 获取每 Skill 的 Request Schema；使用 `TestDevelopmentMultiSkillSharedLockPasses` 的实际 Lock fixture 扩展两个 Skill 的独立 Schema。以注册表结果生成 DescriptorSet，保持每 Skill 的解析范围；拒绝跨 Skill 借用另一个 Schema 的字段。将固定字段原型替换为按 Schema 驱动的短路检查与转换，并从声明了真实 `event.type` 的作者表达式开始运行。
- 通过条件为重跑后 Go、Python 对同一实际产物的正负例一致，覆盖缺失/显式 null/有效值、AND/OR/NOT 守卫、嵌套路径、`int64` 和 finite double 边界、未知字段与无守卫拒绝、求值错误和多 Skill Lock 隔离。保留发布契约前的原始证据。缺少任一项时不写完整 PASS；将最小反例、失败命令、受测 SHA 和下一项可执行步骤记入证据单。完整 PASS 后交由 Compiler Owner 定稿新 Artifact API。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex 登记 Compiler 实施及验收范围 | 建立 #61 的 Next 实施与交接入口 | SR-013、SR-004/005 |
| 2026-11-25 | 0.1.1 | 登记 M.4 / SA 的规范一致性门槛 | 防止消费端被要求调用 Compiler 或做 Admission | SR-013 |
| 2026-11-25 | 0.1.2 | 更新设计评审引用 | 跟踪 #88 修订复审 | SR-013 |
| 2026-11-25 | 0.1.3 | 固定正式规范 SHA | ca-skills #89 已合并 | SR-013 |
| 2026-11-25 | 0.1.4 | 记录实跑环境与 CheckedExpr Any 交换探针 | 提供 AC-013-01 的可复用起点 | SR-013 |
| 2026-11-25 | 0.1.5 | 记录 typed Go/Python 结果和 null 映射反例 | 缩小 AC-013-01 剩余验证范围 | SR-013 |
| 2026-11-25 | 0.1.6 | 记录 nullable oneof 候选和作者语法转换缺口 | 明确 AC-013-01/02 的下一项实验 | SR-013 |
| 2026-11-25 | 0.1.7 | 记录可复跑的源 AST 转换试验 | 为完整 Schema-aware 实施提供验收起点 | SR-013 |
| 2026-11-25 | 0.1.8 | 放行隔离 AC-013-01 与记录既有 Schema/Lock 测试 | 提供明确的 DSH 下一步 | SR-013 |
| 2026-11-25 | 0.1.9 | 保留正式规范来源与分阶段执行条件 | 合并 main 的治理更新 | SR-013、PR #7 |
| 2026-11-25 | 0.1.10 | 回填隔离 PoC 的 Go/Python 一致结果并修复损坏的证据块 | 完成 AC-013-01 隔离阶段验收 | SR-013 |
