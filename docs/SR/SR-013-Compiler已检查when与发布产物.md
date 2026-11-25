# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.2.0  
> 状态：DRAFT（设计补充待评审；不得据此启动产品实施）  
> 创建日期：2026-11-25  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实现、生产准入、Owner Trust 治理、自动发布及真实 5GC/MAS 资格。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。功能归属：EC02 Compiler、F08 技能编译与发布；消费端关联 F02。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.0、[F08 技能编译与发布设计说明书](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md) v0.3.0、[F02 Skill 管理与选择设计说明书](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md) §7/§11、CA-SL v1alpha5 正式来源 SHA 18d8184367982ccbc835756136c4a53f9096c3a0。

目标仓：odango-chan/ca-skill-compiler。实施 Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。文档刷新 Issue：[Next #14](https://github.com/odango-chan/ca-agent-next/issues/14)。目标代码基线：Compiler v2.1.0，commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb。规范依赖：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 已合并，正式发布身份见 [ca-skills release record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。

## 1. 目标、范围与契约边界

为 CA-SL v1alpha5 的可选 assurance/contract.yaml.when 提供 Compiler 发布阶段静态检查、跨语言 CheckedExpr、版本化 Runtime Artifact、Build/Verify 和正式发布证据。

必须保持：

- CA-SL languageTarget 仍为 connectionagent.io/v1alpha5。
- 已发布 Artifact v1alpha5 完全冻结。
- Development Artifact v1alpha1 完全冻结并继续 NOT_ADMITTED。
- 单一 Go Compiler Core；Native CLI 与 WASM Worker 共用。
- Compiler 只负责源解析、静态检查、链接、Artifact、Build/Verify 和发布证据。
- Agent 只消费已发布 Bundle；Agent 不内置 Compiler、不调用 Compiler、不实现 Skill Admission。
- when 只在 assurance/contract.yaml；不在 SKILL.md Front Matter；不新增 constraint.yaml、activation.yaml 或第二份 Contract；不进入 predicates.yaml。
- Next 的 Artifact 导入、Catalog、Skill Resolver 和运行时求值由 SR-004/005/006 负责，不混入本 SR 的 Compiler 代码范围。

## 2. 前置条件、固定输入和当前状态

| 项目 | 固定值 / 状态 |
|---|---|
| CA-SL | connectionagent.io/v1alpha5，规范来源 SHA 18d8184367982ccbc835756136c4a53f9096c3a0 |
| Compiler | v2.1.0；PoC 源基线 255ab85fa5abb4b0bf36656bf64250cafebf45cb |
| Go PoC 环境 | Go 1.26.6、cel-go 0.33.2、cel.dev/expr 0.25.1、Go protobuf 1.36.10 |
| Python PoC 环境 | CPython 3.14.6、cel-expr-python 0.1.4、protobuf 7.36.2 |
| 目标仓写入授权 | 产品实现前须再次确认；本轮文档 PR 不授予 Compiler 写入权限 |
| 合并 / 发布 | 必须单独授权；本轮不包含 |
| 规范门槛 | 已满足；正式源 SHA 已固定 |
| PoC | AC-013-01 隔离 PoC 报告为 PASS；证据提交尚未推送，独立复核待完成 |
| 产品实施 | AC-013-02～04 NOT_RUN；AC-013-05 BLOCKED |

SR-013 整体仍为 DRAFT。AC-013-01 的隔离 PoC 完成不自动把 SR-013 提升为 READY，也不授权修改 Compiler 主线、合并 PR 或发布 Release。

| AC | 当前状态 | 下一步 |
|---|---|---|
| AC-013-01 | PASS（隔离 PoC 报告）；独立复核 NOT_RUN | 获取本地证据提交 78dddd5 并完成独立复核；不得把报告当产品实现 | 
| AC-013-02 | NOT_RUN | 正式 Contract.when AST、G.4、Schema-aware Guard / Nullable lowering | 
| AC-013-03 | BLOCKED（依赖 AC-013-02 和 Owner Gate） | Compiler Owner 确认新版 Artifact API 与 Manifest | 
| AC-013-04 | NOT_RUN | 新版 Build / Verify、Go/Python、Native/WASM/Chromium 与旧契约回归 | 
| AC-013-05 | BLOCKED（依赖 AC-013-01～04 和发布授权） | 经授权发布 Compiler Release 并记录资产和 smoke 证据 | 

## 3. AC-013-01：Schema-aware Go/Python 隔离 PoC

### 3.1 结果摘要

| 验收项 | 报告结果 |
|---|---|
| 真实 Schema 管线 | PASS：使用 Development 多 Skill 共享 Lock fixture；逐 Skill 解析 Request Schema |
| Schema 解析 | PASS：buildSchemaRegistry → resolveReferenceFrom → resolveSchemaRoot |
| DescriptorSet | PASS：由 Schema Registry 解析结果生成 FileDescriptorSet |
| Nullable 三态 | PASS：[T, "null"] 通过 oneof { value, is_null } 区分 Missing / Explicit Null / Value |
| CheckedExpr | PASS：Go 生成标准 cel.expr.CheckedExpr Any 和类型描述 |
| Python 消费 | PASS：Python 只调用 env.deserialize(bytes)，未解析或重编源表达式 |
| 跨语言用例 | PASS：同一产物 18/18 结果一致 |
| 正向求值 | PASS：true、false、缺 event 导致的求值错误 |
| 字段语义 | PASS：同一 optional + nullable 字段的 Missing 与显式 null 可区分 |
| 表达式结构 | PASS：AND / OR / NOT、嵌套路径 |
| 数值 | PASS：int64 与 double 边界用例 |
| 静态拒绝 | PASS：6/6，包括未知字段、缺 has、缺 non-null 守卫、int/double 混用、不安全 OR、跨 Skill 借用 |
| 多 Skill Lock | PASS：Schema 根和字段引用隔离 |

### 3.2 执行环境与命令

- Compiler 隔离源：255ab85fa5abb4b0bf36656bf64250cafebf45cb。
- Go：Windows amd64，Go 1.26.6、cel-go 0.33.2、cel.dev/expr 0.25.1、Go protobuf 1.36.10。
- Python：CPython 3.14.6、cel-expr-python 0.1.4、protobuf 7.36.2。
- go vet ./internal/compiler：退出码 0。
- go test -run '^TestAC013PocGenerate$'：退出码 0。
- Python 直接加载 Go 生成的同一组 protobuf 产物：18/18 一致。
- 完整命令、退出码、版本、哈希和逐项结果见本地证据单 .agent-tmp/ac-013-01-poc/EVIDENCE.md。

### 3.3 产物与回填位置

- 证据单：.agent-tmp/ac-013-01-poc/EVIDENCE.md。
- 产物目录：.agent-tmp/ac-013-01-poc/artifacts/，含 cases.json 及逐用例 .checked.pb / .types.pb。
- 隔离源码：compiler-255ab85/internal/compiler/ac013_poc_test.go。
- SR 回填提交：78dddd5，本地分支 docs/ac-013-01-poc-evidence，基于 Next PR #7 的 f93975f。该分支和证据尚未推送到远端；当前远端无法独立读取这些文件。
- 上述是用户提供的执行报告与本地证据定位；本轮尚未独立复跑或审查该本地提交。独立复核状态：NOT_RUN。

### 3.4 未覆盖边界

以下明确不是 AC-013-01 已验证范围，必须在正式实现阶段处理或按规范明确拒绝：

- 深层 optional ancestor 的完整守卫传播。
- 数组相关表达式和 size。
- 枚举约束及其底层 CEL 类型映射。
- 完整 G.4 布尔组合和复杂事实汇合。
- 多 Skill 同时命中后的 LLM 消歧。

最后一项属于 Host/Skill Resolver，归 F02 / SR-005/006，不是 Compiler 的 AC-013-02 静态检查。AC-013-01 已通过的多 Skill Lock 隔离是 Compiler Schema scope 验收，二者不能混淆。

### 3.5 结论边界

AC-013-01 可记录为 **PASS（隔离 PoC 范围）**，但必须同时保留以下状态：

- 独立证据审查：NOT_RUN。
- Compiler 产品代码实现：NOT_RUN。
- 新 Runtime Artifact API：未定稿。
- Build/Verify 产品门禁：NOT_RUN。
- Compiler Release：未发布。

PoC 中复用 Development Schema/Lock fixture 只证明共享 Schema 解析机制和序列化互操作，不允许正式产品路径依赖 Development Artifact 或改变 Development v1alpha1。

## 4. AC-013-02：正式 Contract.when AST 与 G.4 静态检查

### 4.1 实施输入

- CA-SL v1alpha5 固定规范 SHA。
- Compiler v2.1.0 / 255ab85fa5abb4b0bf36656bf64250cafebf45cb。
- AC-013-01 隔离 PoC 和 EVIDENCE.md。
- Compiler 当前 api.go、inherited_semantics.go、cel_check.go、schema_registry.go、development_link.go 与多 Skill Lock fixture。

### 4.2 实施步骤

1. 在现有 Contract parser / AST 中增加可选 when 字段，保留原始表达式和 SourcePath 行列；不创建第二个 YAML parser。
2. 将 when 纳入正式 CA-SL v1alpha5 发布语义链。没有 when 时不生成程序；when 必须是非空字符串。
3. 从当前 Skill 的 Contract.requestSchema 建立独立 Schema Root 和闭包；复用现有 Schema Registry/Reference Resolver。必要时提取共享内部解析层，禁止把 Development Build 请求和产物作为正式发布路径。
4. 按 CA-SL G.4 建立 event.type + typed input CEL 环境；禁止 DynType。
5. 使用 cel-go AST 执行 G.4 白名单检查、静态字段/类型验证和 bool 结果检查。
6. 实现 path-sensitive Guard Facts：has、null/non-null、AND、OR、NOT 和左到右短路。所有 optional ancestor 和 nullable ancestor 都必须有可证明守卫。
7. 对 nullable [T, null] 使用 AC-013-01 验证的 oneof wrapper 表示，完成作者 AST 到 typed wire AST 的 lowering；生成表达式仍由 cel-go 检查。
8. 输出标准 CheckedExpr Any 和同一 Schema 闭包的 FileDescriptorSet；保留原始源码路径与表达式位置。
9. 增加 SA-004/005 与 G.4 正负 fixture，覆盖嵌套 optional、数组 size、enum/const、数值边界和完整布尔组合。
10. 对多 Skill 共享 Lock 的每个 Request Schema 独立构建类型环境，拒绝跨 Skill 私有字段引用。

### 4.3 必须拒绝的输入

- 非法 CEL、空 when、非 bool 结果。
- input 成员引用但没有 requestSchema。
- 未知字段、无法解析的 Schema Reference。
- optional 字段缺少 has 守卫。
- nullable 字段缺少非 null 守卫。
- 不安全 OR、无法证明安全的深层路径。
- int64/double 隐式混用、非有限 double。
- G.4 禁止语法：数组索引/切片、动态成员、对象构造、宏/推导式、未声明函数、反射、时钟、随机数和外部数据。
- 跨 Skill 私有 Schema/Descriptor 引用。

语义不合规使用现有 CEL_INVALID；不另造诊断码。每个诊断必须能定位到 Skill、assurance/contract.yaml、行列、字段路径和失败原因。

### 4.4 AC-013-02 验收

- SA-004/005 的正负例符合正式 CA-SL v1alpha5。
- G.4 支持项均有正例；禁止项均有静态拒绝例。
- Missing / Explicit Null / Value、has/non-null 守卫和 AND/OR/NOT 事实传播有 Go 测试。
- 多 Skill 共享 Lock 时每个 Skill 的 Request Schema root 隔离。
- 诊断 SourcePath、行列准确。
- GOWORK=off go test ./internal/compiler -count=1 与 GOWORK=off go vet ./internal/compiler 通过。
- 未完成任何一类语法/守卫验证，不得宣称完整 AC-013-02 PASS。

## 5. AC-013-03：新版 Runtime Artifact 契约

### 5.1 版本决策

设计推荐候选 API：Artifact 为 connectionagent.io/compiler-artifact/v2alpha1，BuildResult 为 connectionagent.io/compiler-build-result/v2alpha1。BuildRequest 保持 connectionagent.io/compiler-build-request/v1alpha5，DependencyInspection 保持 connectionagent.io/compiler-dependency-inspection/v1alpha5，除非实际 DTO 审计证明需要升级。languageTarget 仍为 connectionagent.io/v1alpha5。

新 Compiler 版本采用固定 API 集，不在同一二进制中双轨支持旧/新 BuildResult，不增加版本 dispatch、fallback 或兼容路由；旧 v2.1.0 Release 保留冻结 Artifact/BuildResult v1alpha5 历史行为。

**Owner Gate：** Compiler Owner 必须在 AC-013-03 代码实施前确认 Artifact 与 BuildResult 两个 API 名称。若拒绝，先在 EC02 / SR-013 中更新决策及理由；Harness 不得自行改用 v1alpha6、Development v1alpha2 或其他临时名字。

### 5.2 候选文件

~~~text
manifest.json
skills/<skill-name>/compiled/procedure.json
skills/<skill-name>/compiled/ingress-links.json
skills/<skill-name>/compiled/when.checked.pb
skills/<skill-name>/compiled/when.types.pb
~~~

when.*.pb 仅在 Skill 声明 when 时存在。最终文件名和 Manifest 字段以 Compiler Owner 批准后的版本化 Schema 为准；不得保留多个兼容别名。

### 5.3 Manifest 必需语义

每个有 when 的 Skill 必须能够从 Manifest 精确确定：

新版 Manifest 保留现有 v1alpha5 顶层字段语义，skills[] 保留 name、sourceDigest、sourceFiles、compiledFiles、waitLinks，并为有 when 的 Skill 增加可选 when 对象。该对象至少记录 checkedExprPath、descriptorSetPath、input 被引用时的 requestSchemaRef 与 resolvedRequestSchemaPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）。

when.checked.pb 与 when.types.pb 同时进入该 Skill 的 compiledFiles[] 和 Manifest outputFiles[]；逐文件 sha256 复用既有 outputFiles 机制，不增加额外摘要字段。Any type URL 固定为 type.googleapis.com/cel.expr.CheckedExpr；payload 为标准 cel.dev/expr.CheckedExpr。DescriptorSet 是标准 google.protobuf.FileDescriptorSet。

### 5.4 AC-013-03 验收

- 新 Artifact API 与 BuildResult API、JSON Schema、Go DTO/Assembler/Verifier 和文件布局经 Compiler Owner 确认；建议 Schema 路径为 contracts/v2alpha1/artifact-manifest.schema.json 与 contracts/v2alpha1/build-result.schema.json。BuildRequest 维持现有 v1alpha5，除非有实际输入契约变更；新 Compiler 不做旧/新 BuildResult 双版本 dispatch。
- 有 when 与无 when 两类 Skill 的 Manifest 正确。
- CheckedExpr / DescriptorSet 文件路径、Schema identity、SourcePath 和源码位置闭合。
- 多 Skill 文件与 Descriptor 归属无冲突。
- 新 API 与旧冻结 Artifact v1alpha5、Development v1alpha1 完全隔离。
- 版本化 Schema、Golden 和文档同时更新；旧 Golden 不得被修改来适配新格式。

## 6. AC-013-04：Build / Verify 与产品门禁

### 6.1 Build

- 正式 v1alpha5 单一 Core 解析和静态检查。
- 对有 when 的 Skill 生成 CheckedExpr Any 与 DescriptorSet。
- 按新版 Manifest 装配确定性 Artifact。
- 无错误时返回完整 Artifact；任何错误都返回空 OutputFiles，不返回部分产物。
- RFC 8785 JCS、排序和现有确定性规则保持；不写时间、随机值或环境路径。

### 6.2 Verify

- 验证 Artifact API / languageTarget。
- 验证 Manifest、路径、文件清单、重复归属和必需文件。
- 验证 Any type URL、CheckedExpr protobuf、bool 类型和 DescriptorSet。
- 验证所有类型引用可解析，Request Schema identity 与该 Skill 一致。
- 验证 SourcePath、表达式位置、程序文件与 Manifest 一致。
- 验证不存在跨 Skill Descriptor 引用。
- 新版 BuildResult 使用唯一的 v2alpha1 Verify 路径，执行完整重建和逐文件比较或 Compiler Owner 批准的等价确定性复验；现有 CLI 写盘前 Verify 的不变量必须保留。旧 v1alpha5 Verify 行为由旧 v2.1.0 Release 保持，不在新二进制内兼容路由。
- 新版失败行为不改变冻结 v1alpha5 与 Development v1alpha1 的 Verify。

### 6.3 必跑命令

~~~bash
GOTOOLCHAIN=go1.27.4 GOWORK=off go test ./... -count=1
GOTOOLCHAIN=go1.27.4 GOWORK=off go vet ./...
GOTOOLCHAIN=go1.27.4 CGO_ENABLED=0 GOWORK=off go build ./...
GOTOOLCHAIN=go1.27.4 CGO_ENABLED=0 GOOS=js GOARCH=wasm GOWORK=off go build -o dist/skillc.wasm ./cmd/skillc-wasm
GOTOOLCHAIN=go1.27.4 GOWORK=off go test ./cmd/skillc -count=1 -run TestCLIEndToEnd -v
GOTOOLCHAIN=go1.27.4 GOWORK=off node scripts/chromium-parity.mjs
git diff --check
~~~

还必须在 CI 中执行 Go→Python 同一产物互操作。Python 测试命令以实际新增/现有测试入口为准；不得在没有测试脚本时编造命令。固定 Python、cel-expr-python 和 protobuf 版本。

### 6.4 AC-013-04 验收

- 新版 Build / Verify 正向、负向、损坏产物、缺文件、缺 Descriptor、错误 Any type URL 和多 Skill 隔离全部通过。
- 新版重复 Build 字节确定。
- 冻结 Artifact v1alpha5 与 Development v1alpha1 Golden 字节、Schema 和 Verify 行为不变。
- Native、WASM、CLI E2E、Chromium Worker parity 与 Python 互操作全部有真实执行日志。
- 每项记录受测 SHA、环境、版本、命令、退出码、预期、实际和证据位置。

## 7. AC-013-05：Compiler Release 与消费输入

AC-013-05 只验收 Compiler 新版 Runtime Artifact 的正式 Release 输入，不代表 ca-skills Bundle 已发布，也不代表 Next Runtime 已通过。

前置条件：

- AC-013-01～04 均有可复核 PASS。
- Compiler Owner 确认 Release 版本、Artifact API 和资产清单。
- 用户/项目负责人明确授权发布。

执行与证据：

1. 生成正式 Release tag 和 commit identity。
2. 发布 Compiler 二进制/必要资产及新版 Artifact Schema、Manifest、文件布局和说明。
3. 固定 Release tag、commit SHA、资产名称/下载地址、Artifact API、languageTarget。
4. 运行一次实际 Build / Verify smoke，保存完整命令、环境、输出和日志。
5. 更新 EC02/F08 与本 SR 的正式发布链接。

ca-skills 的 Skill Bundle 组装与发布由 SR-023 负责；Next 导入与运行时消费由 SR-004/005/006 负责。没有发布授权时保持 BLOCKED，不创建 Release。

## 8. 依赖、实施顺序与停止条件

~~~text
AC-013-01  隔离 PoC（报告 PASS；独立复核待完成）
     |
     v
AC-013-02  正式 Contract.when / G.4 / Schema-aware 编译
     |
     v
AC-013-03  新版 Runtime Artifact API / Manifest / 文件布局
     |
     v
AC-013-04  Build / Verify / Native-WASM-Chromium / Python parity
     |
     v
AC-013-05  经授权 Compiler Release
     |
     +----> SR-023：ca-skills Bundle 发布
     |
     +----> SR-004/005/006：Next 导入、Catalog、Resolver 和运行时验收
~~~

停止规则：

- Go/Python 对同一产物结果不一致：保存最小复现、双方原始字节和环境，停止依赖该结果的后继阶段。
- G.4 规则与 lowering 无法保持语义：停止，不能用 DynType、自制 evaluator 或运行期异常绕过。
- Schema Resolver 需要 Development 专用状态才能工作：先抽取共享内部能力，不能让正式 Artifact 依赖 Development API。
- Compiler Owner 未批准新 Artifact API：停止 AC-013-03，不写入猜测字段。
- 冻结 Artifact Golden 发生变化：停止并修复兼容性，不更新 Golden 掩盖差异。
- Native/WASM/Chromium/Python 任一门禁失败：记录 FAIL，不发布。
- 目标仓写入权限、PR 合并或 Release 授权缺失：只做只读检查或已授权范围内的工作，不越权。

恢复时先重新核对规范 SHA、Compiler HEAD、Issue #61、目标分支、权限和最后一个已通过 Acceptance；从第一个未通过阶段继续，不重跑或覆盖已通过证据。

## 8.1 DeepSeek Harness Goal 执行约束

SR-013 达到 READY 且文档门禁通过后，实施使用一个连续 Goal，避免将 AC 拆成彼此失去上下文的零散任务：

- 模式：DeepSeek Harness Goal。
- 模型：DeepSeek 最新 Flash。
- 推理强度：low。
- 顺序：AC-013-01 证据复核 → AC-013-02 → AC-013-03 → AC-013-04 → AC-013-05。
- 允许在同一个 Goal 内按依赖连续处理多个 AC；不得并行执行有依赖关系的阶段，不得跳过失败阶段。
- 每个 AC 仍需独立记录 Issue #61 关联、提交、测试、受测 SHA 和证据；不得把一个总的 PASS 替代逐 AC 验收。
- AC-013-03 只有在 Compiler Owner 已确认 Artifact API 后才可继续；没有确认就停在 Owner Gate，不得自行更换版本名。
- AC-013-05 必须再次检查发布授权；没有明确授权时只完成 Release 前检查，不创建 Tag 或 Release。
- 若远端找不到本地证据提交 78dddd5、EVIDENCE.md 或其 Artifact，必须标记证据不可访问并请求提供；不得假装已复核，也不得用聊天报告替代独立复核。
- Compiler 代码变更在 ca-skill-compiler 仓执行；Next 仅维护中央设计、SR 和验收证据。ca-skills Bundle CI 与 Next Runtime 消费端仍按 SR-023、SR-004/005/006 分别处理。
- 只有 G1～G10 文档门禁、SR READY、依赖检查和目标仓写入授权全部满足后，才生成一个完整可复制的 Goal 提示词。提示词必须包含固定文档 SHA、Issue #61、各 AC 顺序、精确命令、停止规则、非目标和证据格式。

## 9. 非目标

本 SR 不实施：

- Next Agent Runtime、SkillCatalog、Resolver、Continuation 或 Python 导入代码；这些由 SR-004/005/006 负责。
- ca-skills Bundle CI；由 SR-023 负责。
- Compiler 内的 Tool/Owner 执行、网络访问或 Runtime。
- CA-SL v1alpha6、旧版兼容映射、冻结 Artifact 修改。
- Development Artifact 作为发布 Bundle。
- Agent Skill Admission、生产授权、签名、Trust Registry、额外 SHA-256、生产资格或 5GC/MAS 认证。

## 10. READY 与完成定义

SR-013 达到 READY 前必须：

1. 本设计经评审，EC02 / F08 / F02 / CA-SL 规范和本 SR 一致。
2. AC-013-01 的本地证据已可访问并完成独立审查，或明确保留审查阻塞及授权阶段。
3. Compiler #61 仍开放且范围一致；Compiler 目标 SHA 和 Go/Python 环境可运行。
4. 目标仓写入授权、分支和实施 Issue 明确。
5. AC-013-03 的 Artifact API Owner Gate 有明确执行方式。
6. 每项 AC 的 Acceptance、命令、退出条件、证据格式和停止/恢复条件完整。

SR-013 只有 AC-013-01～05 均达到各自通过条件，Compiler Release 有授权且证据可复核，才可报告 Compiler 交付完成。SR-023、SR-004/005/006 的 Bundle/Agent 验收不得由 SR-013 代替。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 登记 Compiler 实施及验收范围 | 建立 #61 的 Next 实施与交接入口 | SR-013、SR-004/005 |
| 2026-11-25 | 0.1.1 | Codex | 全文 | 登记 M.4 / SA 的规范一致性门槛 | 防止消费端被要求调用 Compiler 或做 Admission | SR-013 |
| 2026-11-25 | 0.1.2 | Codex | 全文 | 更新设计评审引用 | 跟踪 #88 修订复审 | SR-013 |
| 2026-11-25 | 0.1.3 | Codex | 全文 | 固定正式规范来源及仍待核验的启动条件 | 固定语言基线 | SR-013、Next #5 |
| 2026-11-25 | 0.1.4 | Codex | AC-013-01 | 记录实跑环境与 CheckedExpr Any 交换探针 | 提供最小互操作起点 | SR-013 |
| 2026-11-25 | 0.1.5 | Codex | AC-013-01 | 记录 typed Go/Python 结果和 null 映射反例 | 缩小 PoC 缺口 | SR-013 |
| 2026-11-25 | 0.1.6 | Codex | AC-013-01/02 | 记录 nullable oneof 候选和作者语法转换缺口 | 明确守卫检查需求 | SR-013 |
| 2026-11-25 | 0.1.7 | Codex | AC-013-01 | 记录可复跑的源 AST 转换试验 | 为 Schema-aware PoC 提供起点 | SR-013 |
| 2026-11-25 | 0.1.8 | Codex | AC-013-01 | 放行隔离 PoC 执行单 | 提供明确 DSH 执行范围 | SR-013 |
| 2026-11-25 | 0.1.9 | Codex | 全文 | 固定正式 CA-SL v1alpha5 规范 SHA 和阶段门槛 | 合并 Next PR #7 / #9 相关基线 | SR-013、PR #7、PR #9 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 全文 | 回填 AC-013-01 18/18 隔离 PoC 报告；明确本地证据和独立复核边界；修复旧证据块；细化 AC-013-02～05 的实现、Artifact、Build/Verify、发布、测试和恢复门禁 | 使 SR-013 达到 DeepSeek Harness low-effort 可执行粒度 | Next Issue #14、Compiler #61、IR-003 |
