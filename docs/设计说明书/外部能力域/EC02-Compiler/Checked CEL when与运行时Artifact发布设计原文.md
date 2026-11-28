> 迁移来源：ca-skill-compiler Issue #61  
> 固定来源：Issue #61，最后更新时间 2026-11-25 07:41 UTC  
> 原始状态：OPEN；完整设计/交接方案，实施尚未完成  
> 迁移追踪：ca-agent-next Issue #12。以下保留 Issue 正文；其中“PR #88 OPEN”等状态是原始撰写时的历史描述，当前状态以恢复清单的最新核对为准。

---

## 目标

为 CA-SL v1alpha5 的 `assurance/contract.yaml.when` 提供 Compiler 可在**发布阶段**生成、Python Agent 可在**运行阶段**直接加载的已静态检查 CEL 程序 Artifact。

**Agent 只导入发布好的 Skill。Agent 不内置、不调用 Compiler，也不实现独立 Skill Admission。** 本 Issue 只负责独立 Compiler 的源码静态编译、发布 Artifact 与 Verify，不实现 Agent Runtime。

CA-SL 规范来源：[ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88)。该 PR 合并并更新正式规范发布记录前，本 Issue 不得宣称最终语言符合性。

## 现状审计（Compiler v2.1.0）

已核对源码和正式契约：

1. 现有发布 Artifact `connectionagent.io/compiler-artifact/v1alpha5` 已冻结，不能原地增加 `when` 文件/字段或改变语义。
2. Development Artifact v1alpha1 已冻结，Manifest 和 BuildResult 固定 `executionStatus=NOT_ADMITTED`，并带有 Development 专用 Host Admission Requirements。它是 Development 输出，不是 Agent 可运行的发布 Skill Artifact。
3. `internal/compiler/cel_check.go` 使用 `cel-go v0.33.2` 做 Predicate CEL 解析、类型检查和 G.4 AST 白名单检查；它不是 Contract.when 实现。现有外部 Schema Predicate 参数路径使用 `cel.DynType`，不足以证明 when 对 Request Schema 字段的静态类型。
4. `ContractAST` 当前没有 `when` 节点；当前语义管线没有生成 Skill 选择程序。
5. Development Request Schema 已由 `schema_registry.go` 解析和闭包验证；新增 when 应复用该 Schema 解析能力，不能再造一套 Schema Resolver。
6. 现有发布 Artifact v1alpha5 和 Development v1alpha1 必须保持冻结字节与语义。

## 契约版本决策

**本 Issue 的目标是新版、可发布、可运行的 Compiler Artifact，而不是 Development Artifact。**

| 契约 | 决策 |
|---|---|
| CA-SL languageTarget | 保持 `connectionagent.io/v1alpha5`；不引入 CA-SL v1alpha6 |
| 已发布 Artifact v1alpha5 | 完全不变 |
| Development Artifact v1alpha1 | 完全不变；保留 NOT_ADMITTED 语义，但不作为 Agent 运行包 |
| 新发布运行时 Artifact | 新增 Compiler-owned 版本化 Artifact Manifest/文件布局 |
| Artifact API 版本名 | 由 Compiler Owner 根据现有版本策略决定；它与 CA-SL languageTarget 是两个独立版本维度 |
| BuildRequest / BuildResult | 尽量复用现有接口；若新 Artifact 格式要求新的 BuildResult/Verify API，只升级实际必需的契约并说明理由，不修改旧契约 |

新发布运行时 Artifact **不得**包含 Development 专用的 `executionStatus=NOT_ADMITTED`、`hostAdmission` requirements 或 Skill Admission 状态。不要把 Development v1alpha1 或任何未来 Development v1alpha2 作为 Agent 发布运行包。

## 1. CEL 编译与静态检查

1. 在同一 CA-SL v1alpha5 解析/语义管线中识别可选顶层 `contract.when`。
2. 复用 `cel-go` Parser/Type Checker 和现有 G.4 AST 白名单；不得创建第二个 CEL Parser，也不得因 CEL 引擎支持更多语法而扩大 G.4。
3. 静态类型环境：`event.type` 为 string；`input` 来自当前 Skill 的 `Contract.requestSchema` 和已解析 G.4 Schema 闭包。
4. 访问 input 成员而没有 requestSchema、未知字段、类型不匹配、非 bool 结果、缺少可选/可空字段守卫、G.4 禁止结构，均报 `CEL_INVALID`。
5. 保留 G.4 数值语义：int64 / finite binary64、int/double 不隐式混合、可选字段 has 守卫、nullable 字段 null 守卫。
6. 保留 YAML source path、line、column 和 CEL SourceInfo，诊断定位到 `assurance/contract.yaml.when`。
7. 没有 when 的 Assurance Skill 不生成选择程序；SKILL.md-only Skill 不进入 Compiler Build。

## 2. Compiler → Python Runtime 标准 CEL 交换格式

优先采用 CEL 标准已检查 AST Protobuf：

- Go Compiler 使用 `cel-go` 的 `AstToCheckedExpr` 导出 `google.api.expr.CheckedExpr`。
- 使用标准 `google.protobuf.Any` 包装 CheckedExpr。
- Python Runtime 使用固定版本 `cel-expr-python` 的 `Env.deserialize()` 加载同一 CheckedExpr。
- 同一 Artifact 携带标准 `google.protobuf.FileDescriptorSet`，覆盖 Event 和该 Skill Request Schema 的精确类型闭包。
- Python 反序列化一次后，重复使用同一 Expression/Program 对不同 Event activation 求值；不解析原始 CEL 字符串、不重新做静态类型检查。

参考：
- [cel-go AstToCheckedExpr](https://pkg.go.dev/cel.dev/cel-go/cel#AstToCheckedExpr)
- [cel-expr-python CheckedExpr 序列化/反序列化实现](https://github.com/cel-expr/cel-python/blob/main/cel_expr_python/py_cel_expression.cc)
- [CEL AST Protobuf 互操作规范](https://github.com/cel-expr/cel-spec)

建议文件名（最终由 Compiler PR 定稿）：
- `skills/<skill>/compiled/when.checked.pb`：标准 Any，payload 为 CheckedExpr。
- `skills/<skill>/compiled/when.types.pb`：FileDescriptorSet。

Manifest 为每个有 when 的 Skill 记录程序路径、Descriptor 路径、Request Schema 精确身份（若访问 input）、源码路径和表达式位置。复用新版发布 Artifact 现有的文件清单/自校验机制；不新增额外 SHA-256、签名、Trust Registry 或包完整性机制。

### 类型与数据映射

- 不得把 input 退化为 DynType。
- 复用 Schema Registry 的 G.4 Schema 闭包，确定性生成 Go/Python 都可加载的 DescriptorSet。
- 运行时 activation 必须保留 G.4 的字段缺失、nullable/null、has 守卫和数值语义。
- 若 DescriptorSet 无法无损表达 G.4 optional/null 语义，先做最小 PoC 并停止；不得用自制 CEL evaluator、无类型 dyn 或私有解释器绕过。

## 3. 新版发布运行时 Artifact

1. 新增版本化的发布 Artifact Manifest Schema 与必要的 Go DTO/Assembler/Verifier。
2. 保留已冻结发布 Artifact v1alpha5 和 Development Artifact v1alpha1 的 Schema、Golden、Verify 行为与字节不变。
3. 对声明 when 的 Skill 输出 CheckedExpr Any 和 FileDescriptorSet，并由新 Manifest 精确引用。
4. 新 Manifest 继续使用 Compiler 自己的发布 Artifact 文件清单/校验机制，不新增独立完整性或信任系统。
5. 新发布 Artifact 不携带 `executionStatus=NOT_ADMITTED`、`hostAdmission` 或 Skill Admission 状态。
6. Build/Verify 对新版发布 Artifact 完整重建并逐文件比较；失败不返回部分 Artifact。
7. Artifact 的 `languageTarget` 仍是 `connectionagent.io/v1alpha5`。
8. 外部发布工具链将 `SKILL.md` 与 Compiler 产出的运行时 Artifact 组装为发布 Skill Bundle；Agent 只消费该 Bundle。

## 4. 跨语言验收

### Compiler 静态 Fixture

- SA-004：合法 event.type + typed input，结果 bool。
- SA-005：未知字段、缺少 requestSchema、非 bool、非法 CEL、非法 G.4 结构全部 CEL_INVALID。
- 可选属性：合法 has 短路守卫；未守卫读取拒绝。
- nullable 属性：null 守卫与缺失/空值边界。
- 数值：int64 边界、double 有限性、int/double 混合拒绝。
- G.4 禁止项：数组索引、宏/推导式、对象构造、动态成员、未声明函数拒绝。
- 多 Skill 不同 Request Schema；共享 Lock 时类型环境隔离。
- 无 when 的 Assurance Skill 不生成选择程序文件。

### Python Runtime 互操作 Fixture

必须使用 Compiler 实际产出的文件：

1. Go cel-go 编译 → CheckedExpr Any + DescriptorSet。
2. Python cel-expr-python Env.deserialize() 加载同一 CheckedExpr。
3. 加载同一 DescriptorSet，构造 event/input activation。
4. 对同一 Expression 输入多个 Event，验证 true / false / evaluation error。
5. Go 与 Python 对相同规范 fixtures 结果一致；运行期错误 fail-closed，不把 UNKNOWN/error 提升为 true。

### 产品回归

必须实跑并记录：

```bash
GOWORK=off go test ./... -count=1
GOWORK=off go vet ./...
CGO_ENABLED=0 GOWORK=off go build ./...
CGO_ENABLED=0 GOOS=js GOARCH=wasm GOWORK=off go build -o dist/skillc.wasm ./cmd/skillc-wasm
GOWORK=off go test ./cmd/skillc -count=1 -run TestCLIEndToEnd -v
CHROMIUM_PARITY=1 GOWORK=off go test ./internal/parity -count=1 -run TestChromiumWorkerParity -v
git diff --check
```

另需固定 Python、cel-expr-python、protobuf 版本并实跑互操作测试。未执行写 NOT_RUN；环境阻断写 BLOCKED。

## 5. 分阶段实施

- **P0 PoC：** 等 ca-skills #88 合并并固定规范 SHA；先验证 cel-go CheckedExpr Any 能否被 cel-expr-python 反序列化，验证 DescriptorSet 与 G.4 optional/null 语义。失败即停止。
- **P1 Contract/AST：** 新增 Contract.when AST、Schema-aware 静态检查和 SA fixtures。
- **P2 发布 Artifact：** 新增版本化发布运行时 Artifact Manifest、CheckedExpr/DescriptorSet、Build/Verify 和确定性 Golden。
- **P3 发布验收：** Native/WASM/Chromium parity、Go/Python 规范 fixtures、Compiler Release。
- **P4 Next 集成：** 由 ca-agent-next 实现发布 Skill Bundle 导入、基本结构/引用检查、Tool/Capability 依赖解析、CEL 反序列化、内存 Catalog 和 per-Event 求值。Next 不调用 Compiler。

## 6. 非目标

- 不改变 CA-SL languageTarget，不增加 CA-SL v1alpha6 或旧版本兼容。
- 不修改冻结发布 Artifact v1alpha5 或 Development Artifact v1alpha1。
- 不在 Agent 内置/调用 Compiler，不在 Compiler 中执行 when。
- 不引入 Agent Skill Admission、审批、Owner Trust、签名、Trust Registry、生产授权或资格流程。
- 不把 when 混入 predicates.yaml。
- 不让 SKILL.md-only Skill 调用 Compiler。
- 不引入第二套 CEL Parser/Interpreter、私有 CEL 方言、per-Event Compiler subprocess。
- 不增加额外 SHA-256、包管理器、分布式缓存或自动更新机制。
- 不将 Compiler Build/Verify PASS 解释为 Owner/Provider Trust、5GC E2E 或 Production Qualification。

## 验收完成条件

- [ ] ca-skills #88 已合并，规范发布记录已更新，固定准确 CA-SL 源 SHA。
- [ ] cel-go → CheckedExpr Any → cel-expr-python 的真实互操作 PoC PASS。
- [ ] G.4 Schema-aware 静态类型与可选/可空守卫 fixtures PASS。
- [ ] 新版发布运行时 Artifact 契约发布；旧发布 Artifact v1alpha5 和 Development v1alpha1 不变。
- [ ] Build/Verify、Native/WASM/Chromium parity 与全部 Compiler 产品门禁 PASS。
- [ ] Python Runtime 互操作结果与 Go 规范 fixtures 一致。
- [ ] 发布包可被 Agent 基础导入检查和本机 Tool/Capability 依赖解析。
- [ ] Release SHA、资产、命令和证据记录齐全；未执行项如实 NOT_RUN。

相关：
- [ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88)
- [ca-agent-next PR #1](https://github.com/odango-chan/ca-agent-next/pull/1)
- [Compiler v2.1.0 release](https://github.com/odango-chan/ca-skill-compiler/releases/tag/v2.1.0)

## Next / DeepSeek Harness handoff

Consumer-side design and implementation prompt are in [ca-agent-next PR #1](https://github.com/odango-chan/ca-agent-next/pull/1):
- [技能目录与编译器运行时接口设计说明书](https://github.com/odango-chan/ca-agent-next/blob/docs/architecture-baseline-20261125/docs/%E9%9B%86%E6%88%90%E8%AE%BE%E8%AE%A1/%E6%8A%80%E8%83%BD%E7%9B%AE%E5%BD%95%E4%B8%8E%E7%BC%96%E8%AF%91%E5%99%A8%E8%BF%90%E8%A1%8C%E6%97%B6%E6%8E%A5%E5%8F%A3%E8%AE%BE%E8%AE%A1%E8%AF%B4%E6%98%8E%E4%B9%A6.md)
- [DeepSeek Harness 实施提示词](https://github.com/odango-chan/ca-agent-next/blob/docs/architecture-baseline-20261125/docs/%E5%AE%9E%E6%96%BD%E8%AE%A1%E5%88%92/DeepSeek%20Harness%E5%AE%9E%E6%96%BD%E6%8F%90%E7%A4%BA%E8%AF%8D.md)

The Harness must first prove Go cel-go → Python cel-expr-python CheckedExpr/DescriptorSet interoperability. Agent must import published runtime Artifacts only, without Compiler or Skill Admission. These are design/handoff documents, not implementation evidence.
