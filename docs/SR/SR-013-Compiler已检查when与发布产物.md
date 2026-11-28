# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.2.43\
> 状态：整项 DRAFT；阶段 READY（中央只读核验，仅 AC-013-01 历史隔离 PoC/归档完整性范围）；AC-013-01 固定归档完整性与历史 PoC 独立复验 PASS（Issue #102；PR #110 修复快照 `39ccb00be8d14f7f1be7b02061454e9b927471b8`）；`vet.log` NOT_ARCHIVED / NOT_INDEPENDENTLY_VERIFIABLE；AC-013-02～06 产品仍 NOT_RUN/BLOCKED；AC-013-07 BLOCKED / NOT_RUN；when 唯一来自 assurance/contract.yaml。
> 下一步：按本 SR 已冻结的 CA-SL 1.6.0 / Compiler 3.0.0 / API /2 契约推进 AC-013-02～07 的正式输入与独立评审；AC-013-01 仅为历史隔离 PoC/归档完整性 PASS，不授权 Compiler 产品实现、发布或 Next Runtime 验收。
> 阶段依据：[独立评审 #77](https://github.com/odango-chan/ca-agent-next/issues/77#issuecomment-7209276846)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。  
> 工作项：[阶段工作项 #95](https://github.com/odango-chan/ca-agent-next/issues/95)。
> 创建日期：2026-11-25  
> 修订日期：2026-11-28\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实现、生产准入、Owner Trust 治理、自动发布及真实 5GC/MAS 资格。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。功能归属：EC02 Compiler、F08 技能编译与发布；消费端关联 F02。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.22、[F08 技能编译与发布设计说明书](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md) v0.3.34、[F02 Skill 管理与选择设计说明书](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md) v0.4.3、[CA-SL 1.6.0 中央语言设计](../规范/CA-SL%201.6.0完整语言规范.md) v0.2.10、[SKILL 作者规范](../规范/SKILL作者规范.md) v0.2.4。

目标仓：odango-chan/ca-skill-compiler。实施 Issue：[Compiler #62](https://github.com/odango-chan/ca-skill-compiler/issues/62)。文档刷新 Issue：[Next #14](https://github.com/odango-chan/ca-agent-next/issues/14)。目标代码基线：Compiler v2.1.0，commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb。历史来源：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 已合并，正式发布身份见 [ca-skills release record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。

## 0. 本轮设计评审入口（2026-11-26）

**第三轮独立模型评审记录**：[GitHub Review #6082541121](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6082541121)，固定 Head `3d5f17b7f921788d5d38378edb2a14165ea0e03e` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`；`APPROVE_FOR_READY` 仅限原 Compiler 设计与 AC-013-01 归档复核，不代表后续 Head 已复评或产品 AC PASS。

本 SR 纳入 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计评审批次。**SR 实施主状态依旧为 `DRAFT`；设计 `REVIEW_REQUESTED` 不等于独立 APPROVED、实施 READY 或产品 PASS。** 单版本决定见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**1.6.0 when、Request Schema、1:1 Capability Binding、Build/Verify、Runtime Artifact/Manifest 和 Golden 验收。
- **阻塞/未验证：**旧 AC-013-01 PoC 不是新产品发布；正式 Schema/机器标识/DTO 未冻结，AC-013-02～06 NOT_RUN / BLOCKED（含 Schema-only Package 与零 Capability roots 规则）。
- **通用架构约束：**新 CA-SL 作者源、Compiler API/Build DTO、Runtime Artifact、Bundle、Studio 与 Agent Importer/Runtime **只支持 1.6.0**；Skill 只选择 Capability ID，公开 Capability↔Callable 双向一对一。languageTarget、Compiler 3.0.0 与 BuildRequest / DependencyInspection / BuildResult / Artifact /2 机器身份已由 Next 中央固定；生产者负责发布 Schema / Golden / Release。历史版本材料只读留档；不做别名、兼容、双轨、迁移或 fallback。不得推测尚未发布的实际资产。
- **评审输出：**逐项核对范围、非目标、外部 Owner、错误/状态语义、Acceptance 与证据路径。设计无独立结论写 `PENDING_REVIEW`；未发布依赖写 `BLOCKED`；未运行测试写 `NOT_RUN`。当前不得派发 DeepSeek Harness 实施任务。

## 1. 目标、范围与契约边界

为下一正式 **CA-SL 1.6.0** 的有 Assurance Skill 可选 `assurance/contract.yaml` 顶层 `when` 提供 Compiler 发布阶段静态检查、跨语言 CheckedExpr、Request Schema、Schema-only Interface Package 依赖和 SR-029 唯一 Capability→Callable Binding，构建全新的单版本 BuildRequest/BuildResult、Runtime Artifact、Check/Build/Verify 和正式发布证据。SKILL.md Front Matter 不声明 when；无 Assurance Skill 没有 Contract、不声明 when，不进入 Compiler 构建。历史 v1alpha5 PoC/发行物仅做审计，不能复用其 Build DTO 或计作新版产品验收。

必须保持：

- **唯一新 CA-SL 语言目标为 1.6.0**；准确 `languageTarget` 机器标识由 ca-skills / Compiler Owner 联合正式冻结；新版 Compiler/Agent 拒绝旧 v1alpha5 与未发布的候选语言。
- 已发布 Artifact v1alpha5 完全冻结。
- Development Artifact v1alpha1 完全冻结并继续 NOT_ADMITTED。
- 单一 Go Compiler Core；Native CLI 与 WASM Worker 共用。
- Compiler 只负责源解析、静态检查、链接、Artifact、Build/Verify 和发布证据。
- Agent 只消费已发布 Bundle；Agent 不内置 Compiler、不调用 Compiler、不实现 Skill Admission。
- `when` 唯一位于有 Assurance Skill 的 `assurance/contract.yaml` 顶层；SKILL.md Front Matter 不包含 when，出现时按未知字段拒绝。无 Assurance Skill 没有 Contract、不声明 when。不得新增 constraint.yaml、activation.yaml 或第二份 Contract；when 不进入 predicates.yaml。
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
| PoC | [修复后固定归档](../参考与审计/fixtures/ac-013-01/isolated-poc)；PR #110 合并至专用证据分支 `docs/ac-013-01-poc-evidence` @ `39ccb00be8d14f7f1be7b02061454e9b927471b8`；Issue #102 独立 detached checkout 复验 58/58、SHA256SUMS、audit_evidence.py、Python 18/18 PASS；`vet.log` NOT_ARCHIVED |
| 产品实施 | AC-013-02/04 NOT_RUN；AC-013-03/05/06 BLOCKED（依赖正式 Schema / Package Schema / 发布授权） |

SR-013 整体仍为 DRAFT。AC-013-01 的隔离 PoC 完成不自动把 SR-013 提升为 READY，也不授权修改 Compiler 主线、合并 PR 或发布 Release。

| AC | 当前状态 | 下一步 |
|---|---|---|
| AC-013-01 | PASS（固定归档完整性及历史隔离 PoC 独立复验，2026-11-28） | #110 完整 59 Blob 归档树（58 个清单覆盖文件 + SHA256SUMS）；专用证据分支 merge `39ccb00be8d14f7f1be7b02061454e9b927471b8`；58/58 清单、独立 checksum、audit_evidence.py、Python 18/18；`vet.log` NOT_ARCHIVED；不代表产品 Build/Verify |
| AC-013-02 | NOT_RUN | 正式 assurance/contract.yaml 顶层 when AST、G.4、Schema-aware Guard / Nullable lowering | 
| AC-013-03 | NOT_RUN（机器身份已固定；等待 AC-013-02、正式 Schema / Golden 与 Compiler 实现） | Compiler Owner 按 §5.1 固定 API /2 契约发布 Manifest Schema / Golden | 
| AC-013-04 | NOT_RUN | 新版 Build / Verify、Go/Python、Native/WASM/Chromium 与旧契约回归 | 
| AC-013-05 | BLOCKED（依赖 AC-013-01～04、AC-013-06 和发布授权） | 经授权发布 Compiler Release 并记录资产和 smoke 证据 |
| AC-013-06 | BLOCKED（依赖 1.6.0 Package Schema / DependencyInspection / Golden） | 验证 Schema-only Package、Schema closure 与零 Capability roots 的分离语义；与 SR-030 AC-030-03 联合验收 |

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
- 原始 EVIDENCE.md 记录 `go vet ./internal/compiler` 退出码 0，但固定归档不存在 `vet.log`；历史退出码不可独立复核，状态 `NOT_ARCHIVED / NOT_INDEPENDENTLY_VERIFIABLE`。
- go test -run '^TestAC013PocGenerate$'：退出码 0。
- Python 直接加载 Go 生成的同一组 protobuf 产物：18/18 一致。
- 原始执行记录与归档完整性审计见固定归档 `EVIDENCE.md`；独立 detached checkout 复验命令、环境、退出码和完整 stdout 见 [Issue #102 复验记录](https://github.com/odango-chan/ca-agent-next/issues/102#issuecomment-7224448257)。

### 3.3 产物与回填位置

- 证据单：docs/参考与审计/fixtures/ac-013-01/isolated-poc/EVIDENCE.md。
- 产物目录：docs/参考与审计/fixtures/ac-013-01/isolated-poc/artifacts/，含 cases.json 及逐用例 .checked.pb / .types.pb。
- 隔离源码：compiler-255ab85/internal/compiler/ac013_poc_test.go。
- 修复前归档的历史来源为 [PR #18](https://github.com/odango-chan/ca-agent-next/pull/18)；当前修复后归档以 [PR #115 固定证据目录](../参考与审计/fixtures/ac-013-01/isolated-poc/README.md) 为唯一入口，完整 59 Blob（58 个清单覆盖文件 + SHA256SUMS）已纳入本分支。Issue #102 独立 detached checkout 复验 58/58、SHA256SUMS、audit_evidence.py、Python 18/18 PASS；原始提交 78dddd5 仅保留历史追溯。
- Issue #102 的 detached checkout 复验覆盖归档完整性、58/58 清单、SHA256SUMS、audit_evidence.py 与 Python 18/18；本轮未重新运行 Go 产品测试。`vet.log` 未归档，因此历史 `go vet` 退出码不可独立复核，保持 NOT_ARCHIVED / NOT_INDEPENDENTLY_VERIFIABLE。

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

## 4. AC-013-02：CA-SL 1.6.0 Contract.when、Request Schema 与静态检查

### 4.1 唯一目标与可复用输入

- **唯一规范输入**是 ca-skills 正式冻结的 **CA-SL 1.6.0** 作者 Schema、规范条款与 Golden（发布前按 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 候选语义进行设计评审；实施前必须校验发布身份）。历史 v1alpha5 SHA、Compiler v2.1.0 和 AC-013-01 PoC 仅供算法、性能、Guard Facts 与跨语言类型互操作参考；不能作为新 Parser 的合法语言入口。
- 对新 Compiler Parser、AST、SourcePath 与 Check 使用同一 1.6.0 作者契约；不新增独立 YAML parser，也不加载旧版作者源。`assurance/contract.yaml` 顶层 `when` 为 Assurance Skill 的可选非空 CEL bool 字段；无 when 则无 CheckedExpr。Contract.requestSchema 可独立声明，不与 when 强制捆绑。SKILL.md Front Matter 不声明 when；无 Assurance Skill 没有 Contract、不声明 when，且不进入 Compiler Check / Build。
- 新 Compiler 必须先完成 SR-029 的 Capability→唯一 Callable Link 静态规则：未声明、未解析、重复归属、多成员、kind/Effect/Schema 不符均拒绝；只有全部 Skill 输入通过才能产出 Artifact，绝不从旧 Alias::Callable 反推新 Capability。

### 4.2 实施算法与结果

1. 将 `assurance/contract.yaml` 顶层 `when` 与同一 Contract 的 `requestSchema` 接入唯一 1.6.0 Parser、AST 与 SourcePath，保留精确文件/行列；`when` 仅在 Assurance Package 中合法；SKILL.md Front Matter 出现 `when` 按未知字段拒绝；旧 v1alpha5 Contract/Procedure 和旧 BuildRequest 一律拒绝。
2. 每个 Skill 独立建立 `event.type` 类型环境；只有 when 引用 `input` 时，必须存在已声明 Request Schema，使用对应 Schema Registry/root/$ref 闭包加载输入字段类型。单纯 `event.type` 判断不强制声明 requestSchema；已声明的 Schema 无论 when 是否引用仍需完整校验和发布。
3. 仅允许规范规定的 CEL 白名单：静态成员路径、bool 结果、显式 `has`、null/non-null guard 与左到右 AND/OR/NOT 的 path-sensitive short-circuit facts；所有 optional/nullable 祖先必须被证明安全，禁止 DynType、数组索引、动态构造、未声明函数、时钟、随机数、外部状态。
4. 对 nullable 联合类型使用经 AC-013-01 隔离验证的 oneof wrapper **算法**重新按 1.6.0 类型 Schema 落地；CheckedExpr 为标准 protobuf `cel.expr.CheckedExpr`，Any type URL 为 `type.googleapis.com/cel.expr.CheckedExpr`；DescriptorSet 为标准 `google.protobuf.FileDescriptorSet`。
5. CheckedExpr 与 FileDescriptorSet 按 Skill 独立输出，Only event-type when 不引入不必要的 input 类型闭包；Schema root/完整资源闭包、类型与 SourcePath 在 Manifest 里必须可相互定位。

**PostSmContexts 原版 OpenAPI 正例与类型负例：**`nsmf.create-sm-context` 的 `input` 根是 `PostSmContexts` multipart 中 `jsonData` 对应的 `SmContextCreateData`。该组件的 `requestType` 引用 `RequestType`，其 OAS3 Schema 为 string / string enum（保留未来字符串扩展）；该属性不在 `SmContextCreateData.required` 中，是可选字段。因此 `has(input.requestType) && input.requestType == "INITIAL_REQUEST"` 在 event 判断后的左到右 `&&` 守卫中必须通过类型检查；直接读取 `input.requestType` 而无 `has` 守卫必须以 `CEL_INVALID` 拒绝；`input.requestType == 1` 必须以类型错误拒绝。固定 OpenAMSM 来源 commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`，原始 TS29502_Nsmf_PDUSession.yaml blob `3572be0315a782691ce8b5546b7bc1d5b22fcd64`；不得复制或改写上游 OAS3.
6. 诊断沿用当前中央 Compiler 规范语义：非法 CEL、类型不符、未知 input 成员/无声明 Schema 报 `CEL_INVALID`；Schema root/$ref 缺失报 `SCHEMA_MISSING` 或 `SCHEMA_INVALID`；未知作者字段报 `UNKNOWN_FIELD`；Capability/Cardinality 依 SR-029 的明确诊断枚举。诊断必须附 Skill、源码路径、行列和字段路径，不得吞错或降级成功。
7. 输入顺序变化、并行 Skill、不同 Request Schema 同名字段和重复构建必须保持严格闭包隔离与确定性。任何失败没有部分 Artifact/BuildResult outputFiles。

### 4.3 AC-013-02 独立验收矩阵（新规范正负例）

| 样例 | 预期 |
|---|---|
| 有 Assurance、无 when、无 requestSchema | 静态校验通过，无 CheckedExpr/Schema 资产 |
| 有 Assurance、event.type-only Contract.when，未声明 requestSchema | 通过；checked bool program 存在、input type closure 为空 |
| 无 Assurance 且 SKILL.md Front Matter 声明 when | 不进入 Compiler；由 SR-004 Importer 按未知字段明确拒绝，无 candidate |
| 声明 requestSchema、event.type-only when | 通过；requestSchema 根和完整资源仍发布 |
| Contract.when 引用 input 字段 + 正确 Request Schema | 通过；CheckedExpr 与 DescriptorSet 路径、类型、SourcePath 闭合 |
| input when 无 requestSchema、未知字段、缺 optional/null 守卫、非 bool、非法 CEL | `CEL_INVALID`，具体失败位置可定位，产物为空 |
| 缺 Schema 根、缺 $ref、冲突或越界资源 | `SCHEMA_MISSING` / `SCHEMA_INVALID`，不得误报 CEL_INVALID |
| 多 Skill 共用 Lock、字段同名但 Schema 不同 | 独立类型环境，拒绝跨 Skill 引用 |
| 同一个新 Skill 的错误 Capability 多成员/双重归属/Effect 不匹配 | 按 SR-029 fail-closed；不能因 when 通过而跳过 Capability Link |
| 历史 v1alpha5 源/旧 BuildRequest 或未知语言 | 明确拒绝，不做翻译、alias 或兼容 |

验收命令：在目标 `ca-skill-compiler` 已冻结的新 1.6.0 分支运行 `GOWORK=off go test ./internal/compiler -count=1` 与 `GOWORK=off go vet ./internal/compiler`，新 fixture 和实际测试名由实施 PR 固定，记录测试数、受测 SHA、预期/实测与 SourcePath。**在 ca-skills 1.6.0 正式规范/Schema 尚未发布前，算法可供设计评审但本 AC 不允许产品 PASS。**

## 5. AC-013-03：新版 Runtime Artifact 契约

### 5.1 版本决策

中央冻结唯一机器契约目标（尚未发布）：CA-SL languageTarget=connectionagent.io/v1.6.0；BuildRequest=connectionagent.io/compiler-build-request/2；DependencyInspection=connectionagent.io/compiler-dependency-inspection/2；BuildResult=connectionagent.io/compiler-build-result/2；Runtime Artifact=connectionagent.io/compiler-artifact/2；Compiler Release SemVer=3.0.0（从 v2.1.0 进行不兼容主版本升级，不发布 alpha/rc）。这些是 Next 中央设计目标，不表示 Schema、Golden、二进制或 Release 已存在。

新 Compiler Runtime Build 只产生 2 BuildResult / Artifact，VerifyBuildResult 只接受该新结果契约；不在同一二进制中双轨支持旧/新 Runtime BuildResult，不增加版本 dispatch、fallback 或兼容路由。旧 v2.1.0 Release 保留冻结 Artifact/BuildResult v1alpha5 历史行为；历史 Compiler v2.1.0 的 Development Build 及 v1alpha1 API/Artifact 只留在**旧版发布物**中作审计，不作为新 Compiler 的输入/备用实现。

**发布边界：**Compiler Owner 按以上固定标识实现并发布正式 Schema、Golden、CLI 与 Release；若实现证明目标不可行，必须先回到 Next 更新 EC02 / SR-013 并完成设计复评，Harness 不得自行改名、引入 alpha/rc、兼容 API 或 fallback。

### 5.2 候选文件

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

Contract 声明 requestSchema 时必须存在 dialect-aware 闭包描述，与 when 是否存在无关；本地 G.4 根及完整本地闭包规范化为 Artifact 文件；纯 `$ref` OAS3 根别名不生成 G.4 副本，而是通过 Manifest 精确引用 pin 后的 Source Bundle 根与可达闭包。when.*.pb 仅在 Skill 声明 when 时存在。最终文件名和 Manifest wire 字段以 Compiler Owner 批准后的版本化 Schema 为准；不得保留多个兼容别名。

### 5.3 Manifest 必需语义

新 Manifest **只由 1.6.0 的唯一正式 Schema 定义**；可复用有用字段的含义，但不得把 v1alpha5 Manifest 或旧 BuildResult 当成兼容输入。每个声明 requestSchema 的 Skill 必须有 requestSchema 对象，记录 sourceRef、root dialect 和完整 resources[]。本地 G.4 根记录 Artifact rootPath、可选 rootSchemaId（仅该根声明 `$id` 时记录）及本地闭包的 schemaId/artifactPath；外部 OAS3 根记录 Source Bundle dependency identity、source commit / Git blob pin、原始 source file、JSON Pointer 和每项资源的 OAS3 dialect，不虚构 `$id` 或 G.4 Artifact path。该对象与 when 是否存在无关，供 Host 按正式 **CA-SL 1.6.0** Request Schema/when 契约验证 Event payload。只有生成的本地 G.4 文件进入 compiledFiles[] / Manifest outputFiles[]；原版 OAS3 YAML 属于锁定 Source Bundle dependency，在 Published Bundle 中保留一次，不列为 Compiler 输出文件，运行期离线解析。

每个有 when 的 Skill 增加 when 对象，记录 checkedExprPath、descriptorSetPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）；仅当表达式引用 input 时，额外记录 requestSchemaRef 与 resolvedRequestSchemaLocation；该位置引用按 requestSchema.rootDialect 区分本地 G.4 Artifact path 或外部 OAS3 dependency identity + source file + JSON Pointer，并与同一 Skill 的 requestSchema 元数据一致。when.checked.pb 与 when.types.pb 同时进入 compiledFiles[] 和 Manifest outputFiles[]。Manifest `outputFiles[]` 只列文件路径 / 角色等非摘要元数据；不定义 `sha256` / `sourceDigest` / `dependencyDigest` / `packageDigest`。Build / Verify 只检查路径、存在性、Schema、依赖闭包和语义结果，不计算或比较 SHA-256 / checksum / digest。Any type URL 固定为 type.googleapis.com/cel.expr.CheckedExpr；payload 为标准 cel.dev/expr.CheckedExpr。DescriptorSet 是标准 google.protobuf.FileDescriptorSet，只承担 CEL 类型描述，不替代 G.4 Schema 验证数据。

### 5.4 AC-013-03 验收

- 新 Artifact API 与 BuildResult API、JSON Schema、Go DTO/Assembler/Verifier 和文件布局经 Compiler Owner 确认；建议 Schema 路径为 contracts/2/artifact-manifest.schema.json 与 contracts/2/build-result.schema.json。**BuildRequest 必须一并升级为唯一 1.6.0-only DTO**，包括语言标识、Capability Link 所需的准确依赖快照/Owner 身份；不能保留 v1alpha5 BuildRequest，不做旧/新 BuildResult 双版本 dispatch。
- 覆盖 requestSchema / when 的所有组合：无二者、仅 requestSchema、仅 event.type when、requestSchema + event.type when、requestSchema + input when；input when 无 requestSchema 必须 CEL_INVALID。
- 声明 requestSchema 的 Skill 无论是否声明 when，Manifest 都包含已验证的 dialect-aware Schema 根与完整闭包：本地 G.4 以规范化 Artifact 文件表示；外部 OAS3 以精确 pin 的 Source Bundle 引用表示，原版 bytes 不复制、不投影、不改写；未声明 requestSchema 时不输出 Schema 描述或文件。
- CheckedExpr / DescriptorSet 文件路径、Schema identity、SourcePath 和源码位置闭合。
- 多 Skill 文件与 Descriptor 归属无冲突。
- 新 API 与旧冻结 Artifact v1alpha5、Development v1alpha1 完全隔离。
- 版本化 Schema、Golden 和文档同时更新；旧 Golden 不得被修改来适配新格式。

## 6. AC-013-04：Build / Verify 与产品门禁

### 6.1 Build

- 仅按正式 CA-SL **1.6.0** 进行单一 Parser/AST/静态检查，按 SR-029 校验公开 Capability↔Callable 双向一对一，Procedure 只携带 Capability ID；不得解析旧 v1alpha5。
- 对声明 requestSchema 的 Skill 生成 dialect-aware 闭包描述：本地 G.4 根及完整本地闭包规范化写入 Artifact；外部 OAS3 根及完整可达闭包只记录精确 Source Bundle dependency、source file / JSON Pointer 和 OAS3 dialect。Host 运行期只从 Published Bundle 内的锁定快照校验，不访问远端。
- 对有 when 的 Skill 生成 CheckedExpr Any 与 DescriptorSet；仅当 when 引用 input 时，DescriptorSet 才纳入该 Request Schema 类型闭包。
- 按新版 Manifest 装配确定性 Artifact。
- 无错误时返回完整 Artifact；任何错误都返回空 OutputFiles，不返回部分产物。
- RFC 8785 JCS、排序和现有确定性规则保持；不写时间、随机值或环境路径。
- 所有 protobuf 产物（包括 `cel.expr.CheckedExpr`、`google.protobuf.FileDescriptorSet`、Any wrapper）必须使用 Go protobuf `proto.MarshalOptions{Deterministic:true}` 编码；Any 内层消息先按确定性模式编码。DescriptorSet 的 FileDescriptor、dependency、message/field declaration 与 source info 顺序必须由稳定排序生成。禁止使用默认 `proto.Marshal` 作为产品 Artifact 序列化路径。
- 确定性保证绑定同一固定 Compiler Release / protobuf runtime 版本与相同输入；不声称跨任意 protobuf runtime 版本的字节兼容。

### 6.2 Verify

- 验证 Artifact API / languageTarget。
- 验证 Manifest、路径、文件清单、重复归属和必需文件。
- 验证已声明 Request Schema 的根与全部资源按声明 dialect 可解析：本地 G.4 保留精确 `$id`（若声明）和 G.4 约束；外部 OAS3 保留精确 Source Bundle pin、source file / JSON Pointer 与 OAS 3.0 原生约束语义，不要求 `$id`，不得投影为 G.4；无未解析/越界/重复资源。
- 验证 Any type URL、CheckedExpr protobuf、bool 类型和 DescriptorSet。
- 验证所有类型引用可解析，Request Schema identity 与该 Skill 一致。
- 验证 SourcePath、表达式位置、程序文件与 Manifest 一致。
- 验证不存在跨 Skill Descriptor 引用。
- 对相同固定输入执行两次全新 Build；逐个比较所有 `.pb` 文件的原始字节，验收记录必须列出每个路径及 `changed_between_runs=0`；任一 `.pb` 不同即 AC-013-04 FAIL，不得只凭 JCS/JSON 一致宣称 Build 确定。
- 新 Runtime Build 只接受 CA-SL 1.6.0 的**新 BuildRequest/BuildResult/Artifact**；VerifyBuildResult 只验证该唯一新结果，执行完整重建和逐文件比较或 Compiler Owner 批准的等价确定性复验。旧 BuildRequest v1alpha5、旧 Artifact/Bundle/Development v1alpha1 均被新 Compiler/Agent 拒绝，无兼容、自动迁移或 fallback。旧 v1alpha5 Runtime Verify 行为由旧 v2.1.0 Release 保持，不在新二进制内兼容路由；历史 Development Verify 仅由旧 v2.1.0 发布物保留供审计，**新 Compiler 不提供兼容调用入口**。现有 CLI 写盘前 Verify 的不变量必须保留。
- 旧 v2.1.0 Release 继续保持历史原状；本新 Compiler 不内置旧 v1alpha5 或 Development v1alpha1 Runtime Verify 兼容路由。

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
- 新版重复 Build 字节确定：对 `when.checked.pb`、`when.types.pb` 及其他所有 `.pb` 逐文件记录两次独立 Build 的 SHA/字节比较结果，必须 `changed_between_runs=0`；同时记录完整 Artifact 的字节比较。默认 protobuf 序列化导致的任何 `.pb` 差异均 FAIL，即使 JSON/JCS 部分完全一致。
- **零 Capability roots 正例**：合法 Assurance 没有外部 Capability 引用时，BuildRequest 的 Capability roots 可以为空；若也没有外部 Schema 引用，Package dependency closure 可以为空，并产生不含外部 Tool Effect 的新 1.6.0 Artifact。若 Contract.contexts 显式引用 Schema-only Package，则 dependency closure 必须包含该 Package 的精确 Schema export / $ref 闭包，但 Capability roots、Callable bindings 仍为空；该组合由 AC-013-06 独立验收。**反例**：引用任何外部 Capability 却缺少显式依赖，静态报告 `CAPABILITY_UNRESOLVED` 且 outputFiles 为空；不得把“零 Capability roots”错误解释成“禁止 Schema-only 依赖”，也不得为旧非空根限制虚构 Tool / Callable。
- 冻结 Artifact v1alpha5 的 Schema/Golden 与旧 v2.1.0 Release Verify 行为不变；新 Runtime Build 不提供旧 BuildResult v1alpha5 兼容路由。Development v1alpha1 的 Schema/Golden 和独立 Verify 行为只在**旧 v2.1.0 发布物**中保留，不作为新 Compiler 的兼容 API 或 Agent 发布包。
- Native、WASM、CLI E2E、Chromium Worker parity 与 Python 互操作全部有真实执行日志。
- 每项记录受测 SHA、环境、版本、命令、退出码、预期、实际和证据位置。

## 7. AC-013-05：Compiler Release 与消费输入

AC-013-05 只验收 Compiler 新版 Runtime Artifact 的正式 Release 输入，不代表 ca-skills Bundle 已发布，也不代表 Next Runtime 已通过。

前置条件：

- AC-013-01～04、AC-013-06 均有可复核 PASS。
- Compiler Owner 确认 Release 版本、Artifact API 和资产清单。
- 用户/项目负责人明确授权发布。

执行与证据：

1. 生成正式 Release tag 和 commit identity。
2. 发布 Compiler 二进制/必要资产及新版 Artifact Schema、Manifest、文件布局和说明。
3. 固定 Release tag、commit SHA、资产名称/下载地址、Artifact API、languageTarget。
4. 运行一次实际 Build / Verify smoke，保存完整命令、环境、输出和日志。
5. 更新 EC02/F08 与本 SR 的正式发布链接。

ca-skills 的 Skill Bundle 组装与发布由 SR-027 负责；Next 导入与运行时消费由 SR-004/005/006 负责。没有发布授权时保持 BLOCKED，不创建 Release。

## 8. AC-013-06：Schema-only Interface Package 与零 Capability roots

本 AC 与 SR-030 AC-030-03 联合验收 Compiler 对 Host Context Schema-only Package 的消费能力。它是 Compiler 模块 AC，不是 Studio 导入验收，也不把 SR-030 Publisher 未运行的状态升级为 PASS。

### 8.1 冻结语义

- 正式 CA-SL 1.6.0 Interface Package Schema 必须允许合法的 Schema-only Package：至少一个显式 Schema export，Capability exports = 0，Callable exports = 0；不得要求 ToolCatalog、Evidence 或 Runtime Binding，也不得生成合成 Tool / Callable。
- **Host Context** Schema-only Package 只有在 Skill 的 Contract.contexts 显式引用其 Schema export 时，才进入闭包；新增 **3GPP Common** Schema-only Package 允许由 Skill 自有 requestSchema 中的精确公共类型 $ref（与显式依赖 alias）引用进入闭包，根仍属于 Skill。两类均必须拒绝未声明依赖、未导出 Schema ID 或未闭合的 $ref，且不生成 Capability/Callable Scope。
- Compiler 必须区分 **Capability roots** 与 **Schema dependency closure**。零 Capability roots 是合法情况；Schema-only Package 可形成非空 Schema dependency closure，但不得产生 Capability grant、Callable binding、Tool allowlist 或外部 Tool Effect。
- 只有当 Skill 没有任何外部 Capability 引用、也没有任何外部 Schema 引用时，整个 Package dependency closure 才为空。不得把空 Capability roots 与空 Package dependency closure 混为一谈。
- 精确 Manifest / BuildRequest / DependencyInspection 字段由 Compiler Owner 在正式 1.6.0 Schema / Golden 中冻结；本 AC 只冻结上述语义，不预先发明 wire field 名称。

### 8.2 独立验收矩阵

| 场景 | 输入 | 预期 |
|---|---|---|
| 本地 Schema、零外部依赖 | Assurance 声明自己的 requestSchema，无外部 Capability / Schema 引用 | Capability roots 为空、Package dependency closure 为空；Build / Verify 成功，不产生外部 Tool Effect |
| Host Context Schema-only 依赖 | Contract.contexts 显式引用 SR-030 包的唯一 Schema export；该 Package 有 Schema、0 Capability、0 Callable | Schema dependency closure 包含精确 Package / Schema / $ref 闭包；Capability roots 与 Callable bindings 仍为空；Build / Verify 成功 |
| 缺少依赖声明 | contexts 指向未声明 Alias 或未导出的 Schema ID | 静态拒绝；不从无关项目 Package 推断；无 Artifact |
| 非法 Schema-only Package | 0 Capability / 0 Callable 且没有 Schema export，或夹带 ToolCatalog / Evidence / Runtime Binding | Package Schema / Link 拒绝；不得合成 Callable |
| 误把 Schema-only 当 Capability | Procedure 引用某 Capability，但唯一依赖只提供 Schema export | CAPABILITY_UNRESOLVED；无部分 Artifact |
| 旧版或不匹配语言 | v1alpha5 / Development v1alpha1、错误 languageTarget、未知 Package Schema | 明确拒绝；无转换、fallback 或混合 Catalog |

### 8.3 证据与跨宿主要求

- 正例至少包含一个与 SR-030 AC-030-03 对应的固定 Host Context Package fixture；负例覆盖缺失 Alias、缺失 Schema export、零 Schema exports、伪造 Callable 和旧 languageTarget。
- 同一固定输入在 Go Native、WASM Worker 与 Chromium Worker 得到一致的 Link / Build / Verify 结果和诊断。
- 记录 Compiler 受测 SHA、正式 Package Schema / Golden SHA、命令、环境、输入 ZIP / Lock、预期与实测、Artifact 输出和日志位置。
- AC-013-06 在 Compiler Owner 未冻结 Schema / DTO / Golden 前保持 BLOCKED / NOT_RUN；不得用 SR-024 历史 v1alpha5 Publisher 或 synthetic Package 代替正式新版正例。

## 9. 依赖、实施顺序与停止条件

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
AC-013-06  Schema-only Package / Schema closure / zero Capability roots
     |
     v
AC-013-05  经授权 Compiler Release
     |
     +----> SR-027：ca-skills Bundle 构建与发布
     |
     +----> SR-004/005/006：Next 导入、Catalog、Resolver 和运行时验收
~~~

停止规则：

- Go/Python 对同一产物结果不一致：保存最小复现、双方原始字节和环境，停止依赖该结果的后继阶段。
- G.4 规则与 lowering 无法保持语义：停止，不能用 DynType、自制 evaluator 或运行期异常绕过。
- Schema Resolver 需要 Development 专用状态才能工作：先抽取共享内部能力，不能让正式 Artifact 依赖 Development API。
- Compiler Owner 未批准新 Artifact API：停止 AC-013-03，不写入猜测字段。
- 历史 Golden 被改写时恢复留档输入；新 1.6.0 Golden 不匹配时记录差异并停止该 AC。禁止在新二进制增加旧格式兼容入口。
- Native/WASM/Chromium/Python 任一门禁失败：记录 FAIL，不发布。
- 目标仓写入权限、PR 合并或 Release 授权缺失：只做只读检查或已授权范围内的工作，不越权。

恢复时先重新核对规范 SHA、Compiler HEAD、Issue #62、目标分支、权限和最后一个已通过 Acceptance；从第一个未通过阶段继续，不重跑或覆盖已通过证据。

### 9.1 DeepSeek Harness Goal 执行约束

SR-013 达到 READY 且文档门禁通过后，实施使用一个连续 Goal，避免将 AC 拆成彼此失去上下文的零散任务：

- 模式：DeepSeek Harness Goal。
- 模型：DeepSeek 最新 Flash。
- 推理强度：low。
- 顺序：AC-013-01 证据复核 → AC-013-02 → AC-013-03 → AC-013-04 → AC-013-06 → AC-013-05。
- 允许在同一个 Goal 内按依赖连续处理多个 AC；不得并行执行有依赖关系的阶段，不得跳过失败阶段。
- 每个 AC 仍需独立记录 Issue #62 关联、提交、测试、受测 SHA 和证据；不得把一个总的 PASS 替代逐 AC 验收。
- AC-013-03 使用 §5.1 已固定的 Artifact / BuildResult / BuildRequest / DependencyInspection API /2 与 languageTarget；待 AC-013-02 和正式 Schema / Golden 输入具备后实施。若生产实现证明目标不可行，先回到 Next 更新设计并复评，不得自行更换版本名。
- AC-013-06 必须先有 Compiler Owner 正式 Schema/DTO/Golden 与 SR-030 对应 Package fixture；不支持 0 Capability / 0 Callable 时停止并修订中央 Package 契约，禁止生成合成 Tool/Callable。
- AC-013-05 必须再次检查发布授权；没有明确授权时只完成 Release 前检查，不创建 Tag 或 Release。
- 若无法读取固定的 PR #18 归档、EVIDENCE.md 或其 Artifact，必须标记证据不可访问并请求提供；不得假装已复核，也不得用聊天报告替代独立复核。
- Compiler 代码变更在 ca-skill-compiler 仓执行；Next 仅维护中央设计、SR 和验收证据。ca-skills Bundle CI 与 Next Runtime 消费端仍按 SR-027、SR-004/005/006 分别处理。
- 只有 G1～G10 文档门禁、SR READY、依赖检查和目标仓写入授权全部满足后，才生成一个完整可复制的 Goal 提示词。提示词必须包含固定设计 SHA、已核实覆盖该阶段的实施 Issue、各 AC 顺序、精确命令、停止规则和证据格式。每批立即 Commit、Push，核对远端 ref SHA 与受测提交。

## 10. 非目标

本 SR 不实施：

- Next Agent Runtime、SkillCatalog、Resolver、Continuation 或 Python 导入代码；这些由 SR-004/005/006 负责。
- ca-skills Bundle CI；由 SR-027 负责。
- Compiler 内的 Tool/Owner 执行、网络访问或 Runtime。
- 旧 CA-SL 语法兼容、旧 Build DTO / Artifact / Bundle 兼容、双版本、版本协商、迁移工具、fallback、冻结历史 Artifact 修改；唯一新目标是 1.6.0，不使用 v1alpha6 命名。
- Development Artifact 作为发布 Bundle。
- Agent Skill Admission、生产授权、签名、Trust Registry、额外 SHA-256、生产资格或 5GC/MAS 认证。

## 11. READY 与完成定义

SR-013 达到 READY 前必须：

1. 本设计经评审，EC02 / F08 / F02 / CA-SL 规范和本 SR 一致。
2. AC-013-01 的本地证据已可访问并完成独立审查，或明确保留审查阻塞及授权阶段。
3. Compiler #62 仍开放且范围一致；Compiler 目标 SHA 和 Go/Python 环境可运行。
4. 目标仓写入授权、分支和实施 Issue 明确。
5. AC-013-03 的机器 API 身份已由 Next 固定；正式 Schema / Golden / Manifest 由 Compiler Owner 按该目标实现并发布。
6. AC-013-06 的 Schema-only 正负例、零 Capability roots / Schema dependency closure 区分和跨宿主命令完整。
7. 每项 AC 的 Acceptance、命令、退出条件、证据格式和停止/恢复条件完整。

SR-013 只有 AC-013-01～06 均达到各自通过条件，Compiler Release 有授权且证据可复核，才可报告 Compiler 交付完成。SR-027、SR-004/005/006 的 Bundle/Agent 验收不得由 SR-013 代替。

## 12. CA-SL 1.6.0 统一新接口与设计评审门槛

- 本 SR 的 **设计待评审** 不意味着 Compiler 已实现或 READY；AC-013-02～06 的新产品 Build/Verify/Golden / Release 必须独立通过。
- 新版 Compiler 只处理 CA-SL 1.6.0 Capability-first 源码。Contract/Procedure 的 Capability ID 经 SR-029 定义的一对一约束绑定到唯一 Callable；严格校验 kind、Effect、Input/Output Schema、Owner/Provider Package identity，Artifact 保存已编译的 Binding。
- 与 when/Request Schema 相关的 CheckedExpr、DescriptorSet、Schema 根与 $ref 闭包和 Binding 使用同一个正式 1.6.0 Runtime Artifact。其 BuildRequest、BuildResult、DependencyInspection 和 Verify 使用唯一 1.6.0 DTO；不兼容历史 v1alpha5 和 Development v1alpha1 运行输入。
- 中央机器身份已固定为 languageTarget connectionagent.io/v1.6.0、Compiler 3.0.0 与 BuildRequest / DependencyInspection / BuildResult / Artifact /2；ca-skills / Compiler Owner 负责按该目标发布 Schema、Golden、CLI 和 Release。历史 Go/Python CEL PoC 可作为算法审计，但不能宣称 1.6.0 产品 PASS。
- 相关设计门禁为 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md)、[SR-004](SR-004-已发布技能包导入.md)、[SR-027](SR-027-技能Bundle构建与发布.md)。按 §9、§11 评审各阶段 READY。Compiler Release 是 AC-013-05 的交付结果；禁止把它列为 AC-013-02～04 或 AC-013-06 的启动条件。AC-013-06 使用按正式 Schema 生成的真实 Publisher 候选做联合验证，记录候选来源和受测 Compiler 提交；AC-013-05 另验发行资产。当前设计仍待独立评审。

## 13. AC-013-07：原版 OpenAPI 3.0 直接引用与执行期 Codec Result

新增独立 AC-013-07，不追溯改变 AC-013-01～06 的既有评审状态。本 AC 撤销“必须先发布 G.4 Adapter 才能引用 3GPP 类型”的假设。SR-031 发布不可变 OpenAMSM OpenAPI Source Bundle；Compiler 通过显式 pin 的 dependency 直接解析原版 OAS3 Schema Component。Skill-owned `requestSchema` 入口文件有两种形式：本地 G.4 Schema 根（根对象闭合），或仅含一个 `$ref` 的 OAS3 根引用别名（无兄弟 Schema 关键字）；后者目标按 OAS 3.0 dialect 验证，不转换、不投影、不改原件。

| 子例 | 固定输入 | 必须结果 |
|---|---|---|
| 07a Source Bundle pin | OpenAMSM commit `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`；TS 29.502 / 29.571 / 29.510 NFManagement / 29.518 Namf 四个 Git blob、各自标准版本、选定 surface | Lock 唯一不可变；仅锁 Git blob / byte length 与原始 bytes；dynamic latest / 混源 / 缺文件拒绝，不新增 per-file digest / package hash |
| 07b operation / schema ref | `PostSmContexts.requestBody` → `multipart/related` → `jsonData` → `#/components/schemas/SmContextCreateData`；102 个可达 Schema Component、四文件闭包 | 原生 OAS3 解析；仅解析选定 surface 的可达 refs；未选定 operation refs 不 eager resolve；选定闭包所有 refs 同一 snapshot，原件 byte 不变 |
| 07c dialect boundary | `requestSchema` 为本地 G.4 根或纯 `$ref` OAS3 根别名；真实闭包含 `anyOf` / `oneOf` / `allOf` / `nullable` / `format` / `pattern` / `additionalProperties` | G.4 根闭合并声明 `additionalProperties: false`；纯引用别名仅含 `$ref`、不附加 G.4 siblings；外部按 OAS3 Schema Object 验证，保留组合语义和默认值，不投影 |
| 07d type inference | CEL 读取 OAS3 Schema Component 字段，含 union / intersection / optional / nullable / 不同分支类型 | `anyOf` / `oneOf` 只无条件暴露在每个可满足分支均声明、均 required 且同类型的字段；可选字段必须作为 optional 建模，并且只有在同一左到右 `&&` 表达式中由 `has(input.field)` 守卫后才允许读取；`allOf` 按交集组合；Null 与 Missing 分离；歧义字段静态拒绝 |
| 07e stage availability | T1 when / Request；T2 已选 Procedure Codec READ Output / SourcePath | when 不读 T2 Result、不调用 Codec；T2 Result 只能由后继 Node 显式引用 |
| 07f failure isolation | 缺 dependency、错误 alias/path/pointer、非法 pointer escape、规范化后逃出 Source Root、选定闭包 nested ref 缺失、unsupported OAS keyword、跨 source commit、dynamic latest、OAS3 alias 文件包含兄弟 Schema 关键字、OAS3 闭包反向引用 G.4 本地文件 | `SCHEMA_INVALID` / 稳定诊断，Build 无部分 Artifact；选定闭包外 refs 不阻塞当前消费；允许规范化后仍在 Source Root 内的 `../`；逃出 Source Root 拒绝；不回退 Adapter / projection |
| 07g Bundle / Verify | 固定 Source Bundle + Skill Request + Provider Output Schema + Host Context / Owner dependencies | 离线 Build / Verify；Lock 保存选定闭包；无 Codec Skill 不强制依赖 Source Bundle / Codec |
| 07h 3GPP optional-field CEL Golden | 原版 `SmContextCreateData.requestType` optional string enum；同一 Schema / DescriptorSet | `has(input.requestType) && input.requestType == "INITIAL_REQUEST"` 通过；无 `has` 守卫的直接读取为 `CEL_INVALID`；整数比较为类型错误 |
| 07i OAS3 omitted additionalProperties | pin 后原版 OAS3 Schema Object 未声明 `additionalProperties` | 按 OAS 3.0 默认语义允许额外属性；Resolver / Validator 不得补写 `false` 或按 G.4 闭合规则拒绝 |
| 07j Artifact dialect closure | 同一 Request Schema 分别使用本地 G.4 根和纯 `$ref` OAS3 根别名；OAS3 闭包跨 TS 29.502 / 29.571 等 Source Bundle 文件 | G.4 根与本地闭包规范化为 Artifact 文件；OAS3 根 / 每项可达资源在 Manifest 中记录精确 Source Bundle dependency pin、source file、JSON Pointer 和 OAS3 dialect；原版 YAML bytes 在 Bundle 中保留一次，不复制、不投影、不列入 compiledFiles/outputFiles；Host 离线读取同一锁定快照 |

OpenAPI operation / multipart ingress 验证由 SR-010 负责；Compiler 负责 Request Schema 跨 dialect 引用和类型检查。Artifact / Manifest 必须区分“编译生成的本地 G.4 文件”与“外部 OAS3 Source Bundle 引用”：后者的每项资源以 Source Bundle dependency identity + 原始文件路径 + JSON Pointer + OAS3 dialect 标识，原始 YAML bytes 只在 Source Bundle 中出现一次，且不得计入 Compiler outputFiles。Build / Verify 与 Host 均只使用锁定 Bundle snapshot，离线完成解析。NAS / NGAP Output Schema 由 SR-026 Provider 发布，不能用 SBI binary slot 代替。一个 Codec Capability 是否可用单一封闭 Output Schema + 固定 enum selector 表达多 Profile，必须以 Provider Golden 证明；否则另提设计，不能静默增加 Callable 或放宽 1:1。

**产品门槛**：正式 Source Bundle dependency kind、URI / JSON Pointer wire 表示、Resolver / Validator 版本、Build DTO / Lock 字段和 Golden 未冻结前，`AC-013-07=BLOCKED/NOT_RUN`。SR-031 byte-compare 可独立验收，不得升级 Compiler AC。

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
| 2026-11-26 | 0.2.10 | GPT-6（ChatGPT） | 文档互引与修订记录 | 刷新当前生效版本引用：Compiler 正式设计 F08 版本引用同步，1.6.0-only 未发布 | 防止待审文档引用旧版本 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.11 | GPT-6（ChatGPT） | 标题层级/修订记录 | 调整新增 §11 以及历史 §8.1 层级，移除重复二级标题 | 满足 Markdown 设计评审门禁，避免编号或治理表歧义 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.12 | GPT-6（ChatGPT） | 活跃版本互引与修订记录 | Compiler 实施设计引用 F08 新唯一 1.6.0 Build DTO 版本 | 不将旧基线或历史修订版本冒充当前待评审设计 | Issue #40；SR-029 |
| 2026-11-26 | 0.2.13 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记统一 1.6.0 专项设计评审、阻塞与证据边界；不改变产品实施主状态 | 设计集中评审、避免历史来源冒充新发布 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.2.14 | GPT-6（ChatGPT） | 核心规范与验收章节 | 重写 AC-013-02 新规范算法/正负矩阵，修复旧 BuildRequest/Parser/Manifest/Development 兼容冲突 | 收敛 CA-SL 1.6.0 单版本可评审契约；旧 PoC 只作证据 | Issue #12/#40；SR-013；SR-029；PR #46 |
| 2026-11-26 | 0.2.15 | GPT-6（ChatGPT） | 设计依据与新版本路径 | 刷新 1.6.0 正式目标设计引用：v0.2.9→v0.2.10、v0.3.12→v0.3.13 | 避免旧 Compiler/Publisher 章节被当成新实施入口 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.2.16 | GPT-6（ChatGPT） | 最终一致性复评 / 规范性描述 | 补齐零外部根依赖的 Build/Verify 正反验收、旧 Development 仅历史保留及 1.6.0 Request Schema 权威 | 消除 1.6.0 与历史 Development 的模糊措辞，修正后续评审的可执行门槛 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.2.17 | GPT-6（ChatGPT） | §1～§2、AC-013-04～06、依赖图、READY 与修订记录 | 新增 AC-013-06，定义 Schema-only Interface Package 与零 Capability roots / 非空 Schema dependency closure 的区别；修正 AC-013-04 对空 roots/closure 的表述 | SR-030 已要求 Host Context Schema-only Package，但 SR-013 原先缺少对应 Compiler AC；防止 Compiler 将零 Capability roots 错误解释为零 Schema dependencies，或虚构 Tool/Callable | Issue #12/#40；SR-029、SR-030；EC02；F08；PR #46 |
| 2026-11-26 | 0.2.18 | GPT-6（ChatGPT） | AC-013-06 语义边界、READY 定义、修订记录 | 将 Schema-only Package 的使用范围收敛为 Contract.contexts；明确 requestSchema 始终由 Skill 自有 Schema 提供 | 与 CA-SL 1.6.0 Request Schema / Context Schema 所有权边界保持一致 | Issue #12/#40；CA-SL 1.6.0；SR-030；PR #46 |
| 2026-11-26 | 0.2.19 | Codex / GPT-6 | 设计依据、§9、§11～12 | 修复 F08 链接、Bundle 归属和发布依赖方向，明确候选联验与推送证据 | 避免以 Compiler 自身 Release 阻塞实现，或拿旧 Golden 做兼容 | Issue #12/#40，PR #46，SR-013/027/030 |
| 2026-11-27 | 0.2.20 | Codex / GPT-6 | 评审入口 | 回填独立评审批准评议的具体范围 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.21 | Codex / GPT-6 | 评审状态 | 登记第二轮限定范围及外部依赖 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.22 | ChatGPT / GPT-6；GPT-6（ChatGPT） | 3GPP Schema 与阶段输入补充；§2、§6.1～6.4、修订记录 | 明确公共 Schema-only 导出、选择期 Request 与执行期 Codec Result 的 Link / 业务字段来源；明确 CheckedExpr/DescriptorSet/Any 的确定性 protobuf 序列化与逐 `.pb` 字节验收；统一 AC-013-02/04 NOT_RUN、AC-013-03/05/06 BLOCKED；按版本恢复连续修订账本 | 关闭 Create 选择前依赖 NAS 解码的循环、固定跨包类型门禁；处理独立模型 Review #6082541121 的 R3-SR013-01/02 与 R3-LEDGER-01，避免 protobuf 默认 Marshal 导致 Build 非确定及状态表冲突 | IR-009；Issue #47；SR-031/026/013；Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.23 | ChatGPT / GPT-6；GPT-6（ChatGPT） | 本轮 IR-009 设计修正；§0、文档头、修订记录 | 固定 OpenAMSM 版本 + 原版 YAML 逐字节代发布；显式区分可选 Adapter 与 Provider Codec 输出；将历史 fd80c74 评审登记替换为正式 Review #6082541121 的固定 Head/Base；明确 P2 修订发生在后续 Head，必须重新独立复评 | 落实原版 YAML 不得改动、消除误把原版当 G.4 的风险；防止把不可访问或不同 Head 的评审记录混为一谈 | Issue #47；SR-031/026/013；Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.24 | ChatGPT / GPT-6.2；Codex / GPT-6 | AC-013-07；文档头 | 改为原版 OAS3 组件直接引用；新增跨 dialect Resolver、闭包、语义保真、CEL 类型推导和 T1/T2 负例；登记阶段 READY（中央只读核验）及 AC 范围与工作项 #95 | 撤销强制 Adapter 假设，避免复制或改写标准；按单项独立评审推进 | IR-009；Issue #47；SR-031/010/026/027；Issue #12、#77；PR #46 |
| 2026-11-27 | 0.2.25 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | AC-013-07；§0、§4、AC-013-02、依赖图、修订记录 | 固定 PostSmContexts requestBody 四文件 / 102 Component 选定闭包、lazy resolution、真实 OAS3 keyword 与 allOf/union 类型规则；移除额外 Source Bundle digest 要求；将 Compiler 输入的 `when` 来源改为有 Assurance Skill 的 SKILL.md Front Matter；明确无 Assurance Skill 不声明 when 且不进入 Compiler | 使跨 dialect Resolver 的验收与真实 OpenAMSM Schema 结构一致；对齐用户确认的入口决策，避免 Compiler 继续读取已废弃的 Contract.when；历史错误入口判断，已由 0.2.30 撤销，不构成兼容方案| IR-009；Issue #47；SR-031/010/027；EC01/EC02；Issue #49；IR-008；SR-032；F02/F08 |
| 2026-11-27 | 0.2.26 | ChatGPT / GPT-6.2；GPT-6.2（ChatGPT） | AC-013-07；文档头、设计依据 | 将 CEL union 静态可访问字段收紧为每个分支 required，optional 仅在 CEL 明确支持时暴露；同步 F02、F08、CA-SL 1.6.0 与 SKILL 作者规范的最新版本引用 | 避免把 Schema 中声明但并非必填的字段误判为总是存在；防止 SR-013 继续引用旧版作者入口或过期的 Resolver / Bundle 设计 | IR-009；Issue #47；SR-031/010；EC01/EC02；Issue #49；IR-008；SR-032；F02/F08 |
| 2026-11-27 | 0.2.27 | ChatGPT / GPT-6.2 | Manifest / Build / Verify | 移除 outputFiles SHA-256 与 sourceDigest；不执行 hash / checksum / digest 校验 | 保持 Compiler 产物与 Demo 全链路无 hash 校验边界一致 | IR-009；Issue #47；SR-031；EC02/F08 |
| 2026-11-27 | 0.2.28 | GPT-6.2（ChatGPT） | PR #46 / PR #48 集成刷新 | 合并 Compiler AC-013-01 阶段状态与 IR-009 原版 OAS3 直接引用、选定闭包和无 hash Build/Verify 设计 | 解决堆叠基线漂移，保留 PR #46 最新阶段门槛与 PR #48 的 Compiler dialect 设计 | Issue #47/#12；PR #46/#48；IR-009；SR-013/031 |
| 2026-11-27 | 0.2.29 | GPT-6.2（ChatGPT） | 文档头、AC-013-01、AC-013-07、修订记录 | 合并 AC-013-01 中央只读核验阶段 READY 与有 Assurance Skill 的 Front Matter.when、无 Assurance 不编译规则；保留 3GPP OAS3 直接引用及无 hash Build/Verify | 同步 PR #46 阶段门槛与 Issue #49 作者入口，避免把 Contract.when 作为 Compiler 输入；历史错误入口判断，已由 0.2.30 撤销，不构成兼容方案| Issue #47/#49/#77；IR-008/009；SR-013/031/032 |
| 2026-11-27 | 0.2.30 | GPT-6.2（ChatGPT） | 文档头、§1、§4、AC-013-02、修订记录 | 将 Compiler 唯一输入源恢复为 assurance/contract.yaml 顶层 when；SKILL.md Front Matter 不声明 when；补入 PostSmContexts requestType 字符串枚举的真实类型正负例 | 撤销 Front Matter 回归，固定 Compiler 对 3GPP 原版 OpenAPI 输入字段的类型检查要求 | Issue #49；IR-008/009；SR-031/032；F02/F08/F09 |
| 2026-11-28 | 0.2.39 | GPT-6.2（ChatGPT） | 文档头、§1、§4～§7、修订记录 | 同步 F08 v0.3.33、EC02 v0.2.21、CA-SL v0.2.9 与 Compiler #62 的 1.6.0-only 实施入口 | 避免 SR-013 继续指向历史 #61；保持 OAS3 Resolver / Validator / Golden 仍 BLOCKED / NOT_RUN | Issue #40/#47/#62；IR-008/009；SR-013/031/032；PR #52/#115 |
| 2026-11-28 | 0.2.40 | GPT-6.2（ChatGPT） | 文档头、§5.1、§12、修订记录 | 固定 CA-SL languageTarget 及 Compiler 3.0.0 / BuildRequest / DependencyInspection / BuildResult / Artifact /2 机器契约 | 消除 Compiler Owner 实施期临时命名空间，明确中央设计冻结与正式产品发布的状态边界 | Issue #113；EC02；F08；SR-027；Compiler #62；PR #115 |

| 2026-11-27 | 0.2.31 | GPT-6.2（ChatGPT） | §4.2、AC-013-07、设计依据、修订记录 | 将 3GPP 可选 requestType 的 has 守卫纳入正负 Golden；明确纯 $ref OAS3 根引用别名与 G.4 本地闭合根的两种 requestSchema 入口及 dialect-aware 验收 | 消除可选字段 CEL 访问与 G.4 根闭合 / OAS3 原版直接引用冲突，不投影或改写标准 | Issue #49；IR-009；SR-031；F08；PR #52 |

| 2026-11-27 | 0.2.32 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 CA-SL v0.2.6 的 G.4 closed-object / OAS3 native open-object 边界 | 确保 SR-013 AC-013-07 所依据的规范已消除开放对象语义冲突 | Issue #49；IR-009；PR #52 |

| 2026-11-27 | 0.2.33 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 F02 v0.4.3 的 purpose-specific Script Registry 消费契约 | 保持 Compiler 发布与 Importer 对 transform / predicate Script 输入输出语义一致 | Issue #49；IR-008；SR-004/007/032；PR #52 |

| 2026-11-27 | 0.2.34 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 SKILL 作者规范 v0.2.2 的 Node 粒度最终 Predicate 例外 | 保持 Compiler / 作者规范引用与当前 Node 结构裁决一致 | Issue #49；IR-008；SR-032；PR #52 |

| 2026-11-27 | 0.2.35 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 F08 v0.3.31 对 AC-013-07 OAS3 dependency wire / Resolver / Golden BLOCKED 门槛的表述 | 保持 SR-013 与 F08 产品阻塞状态一致 | Issue #49；IR-009；PR #52 |

| 2026-11-27 | 0.2.36 | GPT-6.2（ChatGPT） | 文档头、设计依据、修订记录 | 同步 SKILL 作者规范 v0.2.3 的完整正向 Procedure Node 结构 | 保持 Compiler / 作者规范示例与 Node 阶段文法一致 | Issue #49；IR-008；SR-032；PR #52 |
| 2026-11-27 | 0.2.37 | ChatGPT（GPT-6） | 设计依据、修订记录 | 同步 CA-SL v0.2.7 与作者规范 v0.2.4 的 Node 示例与 Predicate 规则修正；不改变 Compiler Owner 的 AC-013-07 BLOCKED / NOT_RUN 状态 | 保持 Compiler 设计依赖和作者规范当前候选一致 | Issue #49；IR-008/009；SR-013/032；PR #52 |
| 2026-11-27 | 0.2.38 | ChatGPT（GPT-6.2） | 文档头、§5.2～§5.4、§6、§13 | 将 Request Schema Manifest / Artifact 闭包改为 dialect-aware：本地 G.4 生成文件，外部 OAS3 保留 Source Bundle pin / source file / JSON Pointer 引用；新增 07j 验收，并统一 when 的 Schema 位置引用与 Verify dialect 检查 | 使 AC-013-07 从语言层 dialect 规则闭合到 Artifact、Bundle、Host 与 when 类型定位，同时保持 wire contract / Resolver / Golden 未发布时 BLOCKED / NOT_RUN | Issue #47/#49；IR-008/009；SR-031；PR #52 |
| 2026-11-28 | 0.2.41 | GPT-6.2（ChatGPT） | 文档头、§3.2～§3.3、AC-013-01、修订记录 | 纳入 PR #110 修复后的完整 59 Blob 归档树与 Issue #102 独立 detached checkout 复验；将 58/58、checksum、audit_evidence.py、Python 18/18 记录为归档/历史 PoC 范围 PASS，并保留 vet.log 未归档 | 避免沿用 #107 的旧 FAIL 或 #115 的本地 .agent-tmp 路径；不将历史 PoC 扩大为 Compiler 1.6.0 产品验收 | Issue #102；PR #110；PR #115 |
| 2026-11-28 | 0.2.42 | GPT-6.2（ChatGPT） | §3.2～§3.3、AC-013-01、修订记录 | 将专用证据分支完整 59 Blob 归档树纳入 PR #115（58 个清单覆盖文件 + SHA256SUMS），不再仅登记五份修复元数据文件 | 确保 58/58 独立复验结论对应当前集成树中完整可搬移的归档材料 | Issue #102；PR #110；PR #115 |
| 2026-11-28 | 0.2.43 | GPT-6.2（ChatGPT） | 文档头、§1、§3.2～§3.3、修订记录 | 同步 EC02/F08/CA-SL 当前版本；将修复后归档的唯一入口改为 PR #115 已纳入的完整 59 Blob 目录；区分 Python 18/18 复验与未重新运行的 Go 产品测试、未归档 vet.log | 消除旧 PR #18 修复前归档链接和“未复验”表述与 Issue #102 实际证据之间的矛盾 | Issue #102；PR #110/#115 |
