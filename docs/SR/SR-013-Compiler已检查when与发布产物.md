# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.2.9\
> 状态：**DRAFT（设计待评审）**；CA-SL 1.6.0-only Compiler 新契约待 Owner 冻结；产品实施/发布 NOT_RUN  
> 创建日期：2026-11-25  
> 修订日期：2026-11-26  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实现、生产准入、Owner Trust 治理、自动发布及真实 5GC/MAS 资格。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。功能归属：EC02 Compiler、F08 技能编译与发布；消费端关联 F02。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.9、[F08 技能编译与发布设计说明书](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md) v0.3.10、[F02 Skill 管理与选择设计说明书](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md) §7/§11、CA-SL v1alpha5 正式来源 SHA 18d8184367982ccbc835756136c4a53f9096c3a0。

目标仓：odango-chan/ca-skill-compiler。实施 Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。文档刷新 Issue：[Next #14](https://github.com/odango-chan/ca-agent-next/issues/14)。目标代码基线：Compiler v2.1.0，commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb。规范依赖：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 已合并，正式发布身份见 [ca-skills release record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。

## 1. 目标、范围与契约边界

为下一正式 **CA-SL 1.6.0** 的可选 assurance/contract.yaml.when 提供 Compiler 发布阶段静态检查、跨语言 CheckedExpr、Request Schema 与 SR-029 唯一 Capability→Callable Binding，构建全新的单版本 BuildRequest/BuildResult、Runtime Artifact、Check/Build/Verify 和正式发布证据。历史 v1alpha5 PoC/发行物仅做审计，不能复用其 Build DTO 或计作新版产品验收。

必须保持：

- **唯一新 CA-SL 语言目标为 1.6.0**；准确 `languageTarget` 机器标识由 ca-skills / Compiler Owner 联合正式冻结；新版 Compiler/Agent 拒绝旧 v1alpha5 与未发布的候选语言。
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
| CA-SL | **1.6.0 NOT_RELEASED**，精确机器标识与正式 Schema 待 ca-skills 发布；v1alpha5 SHA 18d8184367982ccbc835756136c4a53f9096c3a0 仅历史审计 |
| Compiler | v2.1.0；PoC 源基线 255ab85fa5abb4b0bf36656bf64250cafebf45cb |
| Go PoC 环境 | Go 1.26.6、cel-go 0.33.2、cel.dev/expr 0.25.1、Go protobuf 1.36.10 |
| Python PoC 环境 | CPython 3.14.6、cel-expr-python 0.1.4、protobuf 7.36.2 |
| 目标仓写入授权 | 产品实现前须再次确认；本轮文档 PR 不授予 Compiler 写入权限 |
| 合并 / 发布 | 必须单独授权；本轮不包含 |
| 规范门槛 | **未满足**；CA-SL 1.6.0 规范/机器标识/Capability Binding 尚未正式发布；历史 v1alpha5 不能替代 |
| PoC | [PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN |
| 产品实施 | AC-013-02～04 NOT_RUN；AC-013-05 BLOCKED |

SR-013 整体仍为 DRAFT。AC-013-01 的隔离 PoC 完成不自动把 SR-013 提升为 READY，也不授权修改 Compiler 主线、合并 PR 或发布 Release。

| AC | 当前状态 | 下一步 |
|---|---|---|
| AC-013-01 | PASS（已归档的隔离 PoC 报告）；本轮复跑 NOT_RUN | 固定归档 SHA；产品验收继续按 AC-013-02～05 取证 |
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
- [PR #18 固定证据归档](https://github.com/odango-chan/ca-agent-next/tree/c3e5bb78ff49306329bcbc2387da6108280903bc/docs/参考与审计/fixtures/ac-013-01/isolated-poc)已核对 58 个文件与 SHA256SUMS；归档报告为 Go/Python 18/18，当前审计复跑 NOT_RUN。原始提交 78dddd5 的追溯保留在 PR #18 的提交 trailer。
- 已检查归档清单与 Git blob；PR #18 报告在干净 Compiler 基线独立复跑。当前审计未重新执行 Go/Python。

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

- 归档完整性复核：PASS；本轮独立复跑：NOT_RUN。
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
3. 对已声明的 Contract.requestSchema 复用现有 Schema Registry / Reference Resolver 建立逐 Skill 独立 Root 和闭包；若 when 只引用 event.type，则不要求 requestSchema；若 when 引用 input，则必须声明 requestSchema，否则按 SA-005 报 CEL_INVALID。必要时提取共享内部解析层，禁止把 Development Build 请求和产物作为正式发布路径。
4. 每个 when 环境始终包含 event.type；仅当表达式引用 input 时，才把该 Skill Request Schema 闭包加入 CEL 类型环境。event-only when 不得强制依赖 requestSchema；若 Contract 已声明 requestSchema，仍须按 G.4 验证并在新版 Artifact 输出供 Host 使用。禁止 DynType。
5. 使用 cel-go AST 执行 G.4 白名单检查、静态字段/类型验证和 bool 结果检查。
6. 实现 path-sensitive Guard Facts：has、null/non-null、AND、OR、NOT 和左到右短路。所有 optional ancestor 和 nullable ancestor 都必须有可证明守卫。
7. 对 nullable [T, null] 使用 AC-013-01 验证的 oneof wrapper 表示，完成作者 AST 到 typed wire AST 的 lowering；生成表达式仍由 cel-go 检查。
8. 输出标准 CheckedExpr Any 和对应 FileDescriptorSet；仅当表达式引用 input 时，DescriptorSet 才包含该 Skill Request Schema 类型闭包。保留原始源码路径与表达式位置。
9. 增加 SA-004/005 与 G.4 正负 fixture，覆盖 event.type-only 且无 requestSchema 的合法表达式、input 引用但无 requestSchema 的拒绝、声明 requestSchema 但 event.type-only 的合法表达式，以及嵌套 optional、数组 size、enum/const、数值边界和完整布尔组合。
10. 对多 Skill 共享 Lock 的每个 Request Schema 独立构建类型环境，拒绝跨 Skill 私有字段引用。

### 4.3 必须拒绝的输入

- 非法 CEL、空 when、非 bool 结果。
- input 成员引用但没有 requestSchema（CEL_INVALID）。
- when 引用未知 input 字段（CEL_INVALID）。
- Contract Schema $ref 缺失或无法解析时，使用既有 SCHEMA_MISSING / SCHEMA_INVALID；不得统一误报为 CEL_INVALID。
- optional 字段缺少 has 守卫。
- nullable 字段缺少非 null 守卫。
- 不安全 OR、无法证明安全的深层路径。
- int64/double 隐式混用、非有限 double。
- G.4 禁止语法：数组索引/切片、动态成员、对象构造、宏/推导式、未声明函数、反射、时钟、随机数和外部数据。
- 跨 Skill 私有 Schema/Descriptor 引用。

CEL 表达式、字段访问、守卫、非 bool 和缺少 input Schema 使用 CEL_INVALID；Schema 根/引用错误沿用 SCHEMA_MISSING / SCHEMA_INVALID；Contract 未知字段沿用 UNKNOWN_FIELD。不得另造诊断码。每个诊断必须能定位到 Skill、assurance/contract.yaml、行列、字段路径和失败原因。

### 4.4 AC-013-02 验收

- SA-004/005 的正负例符合正式 CA-SL v1alpha5。
- event.type-only when 在无 requestSchema 时可通过；引用 input 却未声明 requestSchema 时 CEL_INVALID；声明 requestSchema 的 event-only Skill 仍发布 Request Schema。
- G.4 支持项均有正例；禁止项均有静态拒绝例。
- Missing / Explicit Null / Value、has/non-null 守卫和 AND/OR/NOT 事实传播有 Go 测试。
- 多 Skill 共享 Lock 时每个 Skill 的 Request Schema root 隔离。
- 诊断 SourcePath、行列准确。
- GOWORK=off go test ./internal/compiler -count=1 与 GOWORK=off go vet ./internal/compiler 通过。
- 未完成任何一类语法/守卫验证，不得宣称完整 AC-013-02 PASS。

## 5. AC-013-03：新版 Runtime Artifact 契约

### 5.1 版本决策

设计推荐候选 API：Artifact 为 connectionagent.io/compiler-artifact/2，BuildResult 为 connectionagent.io/compiler-build-result/2。新 Runtime Build/DependencyInspection/BuildRequest 均必须提供 **仅支持 CA-SL 1.6.0** 的唯一新 DTO；不复用旧 v1alpha5 机器 API。精确 Schema、Artifact/BuildResult 版本与机器 languageTarget 均由 Compiler Owner Gate 冻结，不能预先把候选值当成已发布契约。

新 Compiler Runtime Build 只产生 2 BuildResult / Artifact，VerifyBuildResult 只接受该新结果契约；不在同一二进制中双轨支持旧/新 Runtime BuildResult，不增加版本 dispatch、fallback 或兼容路由。旧 v2.1.0 Release 保留冻结 Artifact/BuildResult v1alpha5 历史行为；Development Build 继续使用独立 v1alpha1 API/Artifact 家族。

**Owner Gate：** Compiler Owner 必须在 AC-013-03 代码实施前确认 Artifact 与 BuildResult 两个 API 名称。若拒绝，先在 EC02 / SR-013 中更新决策及理由；Harness 不得自行改用 v1alpha6、Development v1alpha2 或其他临时名字。

### 5.2 候选文件

~~~text
manifest.json
skills/<skill-name>/compiled/procedure.json
skills/<skill-name>/compiled/ingress-links.json
skills/<skill-name>/compiled/request-schema/root.json
skills/<skill-name>/compiled/request-schema/resources/<resource>.json
skills/<skill-name>/compiled/when.checked.pb
skills/<skill-name>/compiled/when.types.pb
~~~

request-schema 根与完整 G.4 $ref 资源闭包只要 Contract 声明 requestSchema 就必须存在，与 when 是否存在无关；when.*.pb 仅在 Skill 声明 when 时存在。最终文件名和 Manifest 字段以 Compiler Owner 批准后的版本化 Schema 为准；不得保留多个兼容别名。

### 5.3 Manifest 必需语义

Manifest 保留现有 v1alpha5 顶层字段语义。每个声明 requestSchema 的 Skill 必须有 requestSchema 对象，记录 sourceRef、rootPath、可选 rootSchemaId（仅根 Schema 声明 $id 时记录）和完整 resources[]（schemaId/path）；该对象与 when 是否存在无关，供 Host 按 CA-SL M.3 验证 Event payload。根与资源文件同时进入 compiledFiles[] 和 Manifest outputFiles[]。

每个有 when 的 Skill 增加 when 对象，记录 checkedExprPath、descriptorSetPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）；仅当表达式引用 input 时，额外记录 requestSchemaRef 与 resolvedRequestSchemaPath，并与同一 Skill 的 requestSchema 元数据一致。when.checked.pb 与 when.types.pb 同时进入 compiledFiles[] 和 Manifest outputFiles[]。逐文件 sha256 复用既有 outputFiles 机制，不增加额外摘要字段。Any type URL 固定为 type.googleapis.com/cel.expr.CheckedExpr；payload 为标准 cel.dev/expr.CheckedExpr。DescriptorSet 是标准 google.protobuf.FileDescriptorSet，只承担 CEL 类型描述，不替代 G.4 Schema 验证数据。

### 5.4 AC-013-03 验收

- 新 Artifact API 与 BuildResult API、JSON Schema、Go DTO/Assembler/Verifier 和文件布局经 Compiler Owner 确认；建议 Schema 路径为 contracts/2/artifact-manifest.schema.json 与 contracts/2/build-result.schema.json。BuildRequest 维持现有 v1alpha5，除非有实际输入契约变更；新 Compiler 不做旧/新 BuildResult 双版本 dispatch。
- 覆盖 requestSchema / when 的所有组合：无二者、仅 requestSchema、仅 event.type when、requestSchema + event.type when、requestSchema + input when；input when 无 requestSchema 必须 CEL_INVALID。
- 声明 requestSchema 的 Skill 无论是否声明 when，Manifest 都包含已验证 Schema 根与完整闭包；未声明 requestSchema 时不输出 Schema 文件。
- CheckedExpr / DescriptorSet 文件路径、Schema identity、SourcePath 和源码位置闭合。
- 多 Skill 文件与 Descriptor 归属无冲突。
- 新 API 与旧冻结 Artifact v1alpha5、Development v1alpha1 完全隔离。
- 版本化 Schema、Golden 和文档同时更新；旧 Golden 不得被修改来适配新格式。

## 6. AC-013-04：Build / Verify 与产品门禁

### 6.1 Build

- 正式 v1alpha5 单一 Core 解析和静态检查。
- 对声明 requestSchema 的 Skill 生成规范化 G.4 Schema 根与完整引用闭包，供 Host 运行期校验。
- 对有 when 的 Skill 生成 CheckedExpr Any 与 DescriptorSet；仅当 when 引用 input 时，DescriptorSet 才纳入该 Request Schema 类型闭包。
- 按新版 Manifest 装配确定性 Artifact。
- 无错误时返回完整 Artifact；任何错误都返回空 OutputFiles，不返回部分产物。
- RFC 8785 JCS、排序和现有确定性规则保持；不写时间、随机值或环境路径。

### 6.2 Verify

- 验证 Artifact API / languageTarget。
- 验证 Manifest、路径、文件清单、重复归属和必需文件。
- 验证已声明 Request Schema 的根与全部资源可解析，保留精确 $id 和 G.4 约束，无未解析/越界/重复资源。
- 验证 Any type URL、CheckedExpr protobuf、bool 类型和 DescriptorSet。
- 验证所有类型引用可解析，Request Schema identity 与该 Skill 一致。
- 验证 SourcePath、表达式位置、程序文件与 Manifest 一致。
- 验证不存在跨 Skill Descriptor 引用。
- 新 Runtime Build 只接受 CA-SL 1.6.0 的**新 BuildRequest/BuildResult/Artifact**；VerifyBuildResult 只验证该唯一新结果，执行完整重建和逐文件比较或 Compiler Owner 批准的等价确定性复验。旧 BuildRequest v1alpha5、旧 Artifact/Bundle/Development v1alpha1 均被新 Compiler/Agent 拒绝，无兼容、自动迁移或 fallback。旧 v1alpha5 Runtime Verify 行为由旧 v2.1.0 Release 保持，不在新二进制内兼容路由；Development Verify 继续使用独立 Development API v1alpha1。现有 CLI 写盘前 Verify 的不变量必须保留。
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

- 新版 Build / Verify 正向、负向、损坏产物、缺文件、缺 Descriptor、错误 Any type URL、Request Schema 根/资源缺失或引用不闭合和多 Skill 隔离全部通过。
- 覆盖 requestSchema/when 组合：无二者、仅 requestSchema、仅 event.type when、requestSchema + event.type when、requestSchema + input when；input when 无 requestSchema 必须 CEL_INVALID。
- 新版重复 Build 字节确定。
- 冻结 Artifact v1alpha5 的 Schema/Golden 与旧 v2.1.0 Release Verify 行为不变；新 Runtime Build 不提供旧 BuildResult v1alpha5 兼容路由。Development v1alpha1 的 Schema/Golden 和独立 Verify 行为不变，继续使用 Development 专用 API，不作为 Agent 发布包。
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

ca-skills 的 Skill Bundle 组装与发布由 SR-027 负责；Next 导入与运行时消费由 SR-004/005/006 负责。没有发布授权时保持 BLOCKED，不创建 Release。

## 8. 依赖、实施顺序与停止条件

~~~text
AC-013-01  隔离 PoC（归档报告 PASS；本轮复跑 NOT_RUN）
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
- 若无法读取固定的 PR #18 归档、EVIDENCE.md 或其 Artifact，必须标记证据不可访问并请求提供；不得假装已复核，也不得用聊天报告替代独立复核。
- Compiler 代码变更在 ca-skill-compiler 仓执行；Next 仅维护中央设计、SR 和验收证据。ca-skills Bundle CI 与 Next Runtime 消费端仍按 SR-027、SR-004/005/006 分别处理。
- 只有 G1～G10 文档门禁、SR READY、依赖检查和目标仓写入授权全部满足后，才生成一个完整可复制的 Goal 提示词。提示词必须包含固定文档 SHA、Issue #61、各 AC 顺序、精确命令、停止规则、非目标和证据格式。

## 9. 非目标

本 SR 不实施：

- Next Agent Runtime、SkillCatalog、Resolver、Continuation 或 Python 导入代码；这些由 SR-004/005/006 负责。
- ca-skills Bundle CI；由 SR-027 负责。
- Compiler 内的 Tool/Owner 执行、网络访问或 Runtime。
- 旧 CA-SL 语法兼容、旧 Build DTO / Artifact / Bundle 兼容、双版本、版本协商、迁移工具、fallback、冻结历史 Artifact 修改；唯一新目标是 1.6.0，不使用 v1alpha6 命名。
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

## 10. CA-SL 1.6.0 统一新接口与设计评审门槛

- 本 SR 的 **设计待评审** 不意味着 Compiler 已实现或 READY；AC-013-02～05 的新产品 Build/Verify/Golden / Release 必须独立通过。
- 新版 Compiler 只处理 CA-SL 1.6.0 Capability-first 源码。Contract/Procedure 的 Capability ID 经 SR-029 定义的一对一约束绑定到唯一 Callable；严格校验 kind、Effect、Input/Output Schema、Owner/Provider Package identity，Artifact 保存已编译的 Binding。
- 与 when/Request Schema 相关的 CheckedExpr、DescriptorSet、Schema 根与 $ref 闭包和 Binding 使用同一个正式 1.6.0 Runtime Artifact。其 BuildRequest、BuildResult、DependencyInspection 和 Verify 使用唯一 1.6.0 DTO；不兼容历史 v1alpha5 和 Development v1alpha1 运行输入。
- 精确 machine languageTarget、API 名称、字段、Schema 与 Golden 必须由 ca-skills / Compiler Owner 在正式 Issue/PR/Release 冻结；历史 Go/Python CEL PoC 可作为算法审计，但不能宣称 1.6.0 产品 PASS。
- 相关设计门禁为 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md)、[SR-004](SR-004-已发布技能包导入.md)、[SR-027](SR-027-技能Bundle构建与发布.md)，新 Release 未完成前不得给出 Compiler 产品实施 READY 或 Harness 提示词。

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
| 2026-11-25 | 0.2.1 | GPT-6.2（ChatGPT） | §4–7 | 增加 Request Schema 运行期投影与发布闭包，明确 event.type-only when 的合法路径、CEL 与 Schema 诊断边界和 AC 组合测试 | 对齐 CA-SL v1alpha5 M.2/M.3，补齐 Host 运行期验证所需的发布数据 | Next Issue #14、Compiler #61、F02、F08 |
| 2026-11-25 | 0.2.2 | GPT-6.2（ChatGPT） | §5.3 | 明确根 Schema 的 $id 可选，根身份可由作者 sourceRef 与 Artifact rootPath 确定 | 避免对 CA-SL 未要求的 Schema $id 增加新约束 | Next Issue #14、Compiler #61 |
| 2026-11-25 | 0.2.3 | GPT-6.2（ChatGPT） | §1～9 | 合并 PR #16 的完整 when/Request Schema/Compiler Artifact 设计；保留 AC-013-01 Go/Python 18/18 的隔离 PoC 报告，同时明确证据 commit 78dddd5 未在远端仓库找到、独立复核 NOT_RUN | 设计范围与阶段 PoC 证据分开，防止将报告结果升级为 Compiler 产品 PASS 或 SR VERIFIED | Issue #14；PR #16/#18；IR-003；F02 v0.2.7；F08 v0.3.3；EC02 Compiler v0.2.3 |
| 2026-11-25 | 0.2.4 | GPT-6.2（ChatGPT） | §1～9 | 同步 F02/F08/Compiler 设计版本引用；保留 AC-013-01 18/18 报告结果并明确证据未归档、独立复核未运行 | 避免不同文件引用不同版本或把报告状态升级为完整 SR 验收 | Issue #14；PR #16/#18 |
| 2026-11-25 | 0.2.5 | Codex | 正文 | 固定 PoC 归档并记录本轮完整性复核 | 核对 Issue #12 与固定提交 | Issue #12 |
| 2026-11-25 | 0.2.6 | Codex / GPT-6 | 正文 | 同步所引权威设计版本 | 消除执行歧义并同步中央设计 | Issue #12 SR-013 |
| 2026-11-26 | 0.2.7 | Codex / GPT-6 | 见本行变更 | 将实际 Bundle CI/发布归入 ca-skills 生产端 SR-027 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.8 | Codex / GPT-6 | 见本行变更 | 将未发布 Runtime Artifact 与 BuildResult 的候选版本段改为纯数字 2，保留 Owner 冻结门禁 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.2.9 | GPT-6（ChatGPT） | 文档头、§1～2、§5～6、§10、修订记录 | 把 Compiler 新产品规范统一为 CA-SL 1.6.0-only，移除 v1alpha5 BuildRequest/DependencyInspection/Runtime 兼容入口并增加 SR-029 Binding 门槛 | 不把历史 PoC、冻结发布源或旧 Build DTO 当作当前产品设计完成 | Issue #40；SR-029；Compiler #61 |
