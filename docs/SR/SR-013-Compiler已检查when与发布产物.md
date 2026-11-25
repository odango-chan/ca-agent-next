# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.1.4  
> 状态：DRAFT  
> 创建日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实施、生产准入、Owner Trust 治理及自动发布。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.1.7 §1–7 和 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) §1–5。SR-012 负责归档。

目标仓：`odango-chan/ca-skill-compiler`。范围覆盖 Go/Python 互操作 PoC、Compiler Contract AST 与语义检查、新版 Artifact Schema、Build/Verify、fixture、Golden 和产品门禁。保持单一 Go Core、语言 v1alpha5、冻结发布 Artifact v1alpha5 及 Development v1alpha1；Development 继续 `NOT_ADMITTED`。Next SR-004/005 消费实际发布 Bundle，运行时无 Compiler 或 Skill Admission。

启动条件：本 SR 经评审达到 READY，ca-skills #88 的 M.4 与 SA 导入职责已与 Next 对齐、正式发布且固定规范 SHA，具备目标仓写入授权和可运行 Go/Python 环境。PoC 为本 SR 的第一段验收；通过后再要求 Compiler Owner 确认新版 Artifact API 版本和布局。合并或发布另行授权。

| 验收 ID | 通过条件 | 当前证据 |
|---|---|---|
| AC-013-01 | Go 生成的 CheckedExpr Any 与 FileDescriptorSet 被固定版本 Python 直接加载；G.4 跨语言 fixture 对 true/false/error、缺失/null 与数值边界一致 | 预检已有证据；完整验收 NOT_RUN |
| AC-013-02 | #61 的静态正负例、诊断位置和多 Skill 共享 Lock 时的类型隔离全部符合预期 | NOT_RUN |
| AC-013-03 | 新版 Build/Verify 确定、损坏时 fail-closed；冻结机器契约及两条冻结产物路径对基准的 Golden 字节一致 | NOT_RUN |
| AC-013-04 | #61 指定的 Go 测试、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 与 diff check 全部通过 | NOT_RUN |
| AC-013-05 | 经授权发布后，记录可下载的实际 Bundle、Release SHA、资产、契约版本与验证日志，供 SR-004/005 使用 | BLOCKED：依赖 AC-013-01～04 与发布授权 |

Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。规范依赖：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88)。设计 PR：[Next #3](https://github.com/odango-chan/ca-agent-next/pull/3)。实施 PR、Commit、实际命令、环境、受测 SHA 和证据待回填。替代关系：无。

正式 CA-SL v1alpha5 规范固定为 `18d8184367982ccbc835756136c4a53f9096c3a0`，见 [ca-skills 正式发布记录](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。此门槛已满足。Next PR #3 已合并；SR-013 的实施范围与验收仍待负责人确认，AC-013-01 为进入 READY 后的首项验收。

### AC-013-01 环境预检与最小交换实验

- Compiler 源：`255ab85fa5abb4b0bf36656bf64250cafebf45cb`。Windows amd64，Go 1.26.6，cel-go 0.33.2，cel.dev/expr 0.25.1，Go protobuf 1.36.10；隔离环境 CPython 3.14.6，cel-expr-python 0.1.4，protobuf 7.36.2。
- `GOWORK=off go test ./internal/compiler -run '^

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex 登记 Compiler 实施及验收范围 | 建立 #61 的 Next 实施与交接入口 | SR-013、SR-004/005 |
| 2026-11-25 | 0.1.1 | 登记 M.4 / SA 的规范一致性门槛 | 防止消费端被要求调用 Compiler 或做 Admission | SR-013 |
| 2026-11-25 | 0.1.2 | 更新设计评审引用 | 跟踪 #88 修订复审 | SR-013 |
| 2026-11-25 | 0.1.3 | 固定正式规范 SHA | ca-skills #89 已合并 | SR-013 |
` 退出 0，仅验证 Compiler 包能编译。Python 使用 `from cel_expr_python import cel` 与 `cel.NewEnv()`，可加载自己生成的表达式。
- 用 Go 编译常量 `true`。直接 `anypb.New(AstToCheckedExpr(...))` 产生 `type.googleapis.com/google.api.expr.v1alpha1.CheckedExpr`；Python `Env.deserialize` 拒绝，报告 INVALID_ARGUMENT。将 Go CheckedExpr protobuf 序列化，再解码为 `cel.dev/expr.CheckedExpr` 并用 `anypb.New` 包装，得到 `type.googleapis.com/cel.expr.CheckedExpr`；Python 直接加载该文件并求值为 true。以真实类型构造 Any，避免只替换类型 URL。
- 下一步按正式规范补完整 AC-013-01：Go 导出同一 typed when 的 Any 和 FileDescriptorSet；Python 用同一 DescriptorSet 构造 DescriptorPool；记录两端的 true/false/error、optional 与 null、数值边界和多 Skill 隔离。同一工具版本下重跑直接包装失败与标准类型成功的对照。仍须验证类型和语义字段在转换前后完整保留，由 Compiler Owner 据此定冻结的新 Artifact 字段。
- 本次是隔离工作区探针，未写入 Compiler 仓。AC-013-01 尚无完整验收证据。明确区分环境/常量探针通过、旧 Type URL 失败和 typed fixture 尚未运行。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex 登记 Compiler 实施及验收范围 | 建立 #61 的 Next 实施与交接入口 | SR-013、SR-004/005 |
| 2026-11-25 | 0.1.1 | 登记 M.4 / SA 的规范一致性门槛 | 防止消费端被要求调用 Compiler 或做 Admission | SR-013 |
| 2026-11-25 | 0.1.2 | 更新设计评审引用 | 跟踪 #88 修订复审 | SR-013 |
| 2026-11-25 | 0.1.3 | 固定正式规范 SHA | ca-skills #89 已合并 | SR-013 |
| 2026-11-25 | 0.1.4 | 记录实跑环境与 CheckedExpr Any 交换探针 | 提供 AC-013-01 的可复用起点 | SR-013 |
