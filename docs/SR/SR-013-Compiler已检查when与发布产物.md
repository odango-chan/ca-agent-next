# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.2.28\
> 状态：整项 DRAFT；阶段 READY（中央只读核验）。AC-013-01 归档完整性。  
> 下一步：修复 PR #18 归档中 audit 登记不一致、绝对式校验路径及 vet 日志缺项后重新静态复核。复跑单列；02/04 NOT_RUN，03/05/06 等 Compiler Owner 与正式契约。\
> 阶段依据：[独立评审 #77](https://github.com/odango-chan/ca-agent-next/issues/77#issuecomment-7209276846)，评审 Head `42a7fe2ce7826b7cda74110e843f39401571299c`；本轮登记与实施入口见 [SR 总索引 §2.4](../治理/SR%20总索引.md)。  
> 工作项：[阶段工作项 #95](https://github.com/odango-chan/ca-agent-next/issues/95)。[本轮固定归档核验报告](../issue-95-fixed-source-handoff/SR-013.md)。
> 创建日期：2026-11-25  
> 修订日期：2026-11-28\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实现、生产准入、Owner Trust 治理、自动发布及真实 5GC/MAS 资格。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。功能归属：EC02 Compiler、F08 技能编译与发布；消费端关联 F02。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.13、[F08 技能编译与发布设计说明书](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md) v0.3.16、[F02 Skill 管理与选择设计说明书](../设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md) §7/§11、[CA-SL 1.6.0 中央语言设计](../规范/CA-SL%201.6.0完整语言规范.md)。

目标仓：odango-chan/ca-skill-compiler。新 1.6.0-only 实施 Issue：[Compiler #62](https://github.com/odango-chan/ca-skill-compiler/issues/62)；旧 #61 仅 v1alpha5 历史审计，不是本 SR 的实施入口。文档刷新 Issue：[Next #14](https://github.com/odango-chan/ca-agent-next/issues/14)。目标代码基线：Compiler v2.1.0，commit 255ab85fa5abb4b0bf36656bf64250cafebf45cb。历史来源：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 已合并，正式发布身份见 [ca-skills release record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。

## 0. 本轮设计评审入口（2026-11-26）

**第三轮独立模型评审记录**：[GitHub Review #6082541121](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6082541121)，固定 Head `3d5f17b7f921788d5d38378edb2a14165ea0e03e` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`；`APPROVE_FOR_READY` 仅限原 Compiler 设计与 AC-013-01 归档复核，不代表后续 Head 已复评或产品 AC PASS。

本 SR 纳入 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计评审批次。**SR 实施主状态依旧为 `DRAFT`；设计 `REVIEW_REQUESTED` 不等于独立 APPROVED、实施 READY 或产品 PASS。** 单版本决定见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**1.6.0 when、Request Schema、1:1 Capability Binding、Build/Verify、Runtime Artifact/Manifest 和 Golden 验收。
- **阻塞/未验证：**旧 AC-013-01 PoC 不是新产品发布；正式 Schema/机器标识/DTO 未冻结，AC-013-02～06 NOT_RUN / BLOCKED（含 Schema-only Package 与零 Capability roots 规则）。
- **通用架构约束：**新 CA-SL 作者源、Compiler API/Build DTO、Runtime Artifact、Bundle、Studio 与 Agent Importer/Runtime **只支持 1.6.0**；Skill 只选择 Capability ID，公开 Capability↔Callable 双向一对一。历史版本材料只读留档；不做别名、兼容、双轨、迁移或 fallback。机器字段/ID 必须等待发布者冻结，不猜测。
- **评审输出：**逐项核对范围、非目标、外部 Owner、错误/状态语义、Acceptance 与证据路径。设计无独立结论写 `PENDING_REVIEW`；未发布依赖写 `BLOCKED`；未运行测试写 `NOT_RUN`。当前不得派发 DeepSeek Harness 实施任务。

## 1. 目标、范围与契约边界

为下一正式 **CA-SL 1.6.0** 的可选 assurance/contract.yaml.when 提供 Compiler 发布阶段静态检查、跨语言 CheckedExpr、Request Schema、Schema-only Interface Package 依赖和 SR-029 唯一 Capability→Callable Binding，构建全新的单版本 BuildRequest/BuildResult、Runtime Artifact、Check/Build/Verify 和正式发布证据。历史 v1alpha5 PoC/发行物仅做审计，不能复用其 Build DTO 或计作新版产品验收。

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
| 产品实施 | AC-013-02/04 NOT_RUN；AC-013-03/05/06 BLOCKED（依赖正式 Schema / Package Schema / 发布授权） |

SR-013 整体仍为 DRAFT。AC-013-01 的隔离 PoC 完成不自动把 SR-013 提升为 READY，也不授权修改 Compiler 主线、合并 PR 或发布 Release。

| AC | 当前状态 | 下一步 |
|---|---|---|
| AC-013-01 | FAIL（归档完整性未完全闭合）；历史隔离 PoC 报告 18/18；本轮复跑 NOT_RUN | 修正 audit 登记、校验路径和 vet 日志缺项；产品验收继续按 AC-013-02～06 取证 |
| AC-013-02 | NOT_RUN | 正式 Contract.when AST、G.4、Schema-aware Guard / Nullable lowering | 
| AC-013-03 | BLOCKED（依赖 AC-013-02 和 Owner Gate） | Compiler Owner 确认新版 Artifact API 与 Manifest | 
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
- go vet ./internal/compiler：退出码 0。
- go test -run '^TestAC013PocGenerate$'：退出码 0。
- Python 直接加载 Go 生成的同一组 protobuf 产物：18/18 一致。
- 完整命令、退出码、版本、哈希和逐项结果见本地证据单 .agent-tmp/ac-013-01-poc/EVIDENCE.md。

### 3.3 产物与回填位置

- 证据单：.agent-tmp/ac-013-01-poc/EVIDENCE.md。
- 历史 PoC `artifacts/` 仅存 `.checked.pb` / `.types.pb`，`cases.json` 在归档根目录；历史审计结果与 #110 的独立证据分支修复按不同 SHA 分开，不代表 1.6.0 产品 PASS。
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

- 归档完整性复核：FAIL（本轮发现三处归档缺陷，详见第 13 节）；本轮独立复跑：NOT_RUN。
- Compiler 产品代码实现：NOT_RUN。
- 新 Runtime Artifact API：未定稿。
- Build/Verify 产品门禁：NOT_RUN。
- Compiler Release：未发布。

PoC 中复用 Development Schema/Lock fixture 只证明共享 Schema 解析机制和序列化互操作，不允许正式产品路径依赖 Development Artifact 或改变 Development v1alpha1。

## 4. AC-013-02：CA-SL 1.6.0 Contract.when、Request Schema 与静态检查

### 4.1 唯一目标与可复用输入

- **唯一规范输入**是 ca-skills 正式冻结的 **CA-SL 1.6.0** 作者 Schema、规范条款与 Golden（发布前按 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 候选语义进行设计评审；实施前必须校验发布身份）。历史 v1alpha5 SHA、Compiler v2.1.0 和 AC-013-01 PoC 仅供算法、性能、Guard Facts 与跨语言类型互操作参考；不能作为新 Parser 的合法语言入口。
- 对新 Compiler Parser、AST、SourcePath 与 Check 使用同一 1.6.0 作者契约；不新增独立 YAML parser，也不加载旧版作者源。Contract.when 为可选非空 CEL bool 表达式；无 when 则无 CheckedExpr。Contract.requestSchema 可独立声明，不与 when 强制捆绑。
- 新 Compiler 必须先完成 SR-029 的 Capability→唯一 Callable Link 静态规则：未声明、未解析、重复归属、多成员、kind/Effect/Schema 不符均拒绝；只有全部 Skill 输入通过才能产出 Artifact，绝不从旧 Alias::Callable 反推新 Capability。

### 4.2 实施算法与结果

1. 将 `assurance/contract.yaml.when` 和 `requestSchema` 接入唯一 1.6.0 Parser、AST 与 SourcePath，保留精确行列；旧 v1alpha5 Contract/Procedure 和旧 BuildRequest 一律拒绝。
2. 每个 Skill 独立建立 `event.type` 类型环境；只有 when 引用 `input` 时，必须存在已声明 Request Schema，使用对应 Schema Registry/root/$ref 闭包加载输入字段类型。单纯 `event.type` 判断不强制声明 requestSchema；已声明的 Schema 无论 when 是否引用仍需完整校验和发布。
3. 仅允许规范规定的 CEL 白名单：静态成员路径、bool 结果、显式 `has`、null/non-null guard 与左到右 AND/OR/NOT 的 path-sensitive short-circuit facts；所有 optional/nullable 祖先必须被证明安全，禁止 DynType、数组索引、动态构造、未声明函数、时钟、随机数、外部状态。
4. 对 nullable 联合类型使用经 AC-013-01 隔离验证的 oneof wrapper **算法**重新按 1.6.0 类型 Schema 落地；CheckedExpr 为标准 protobuf `cel.expr.CheckedExpr`，Any type URL 为 `type.googleapis.com/cel.expr.CheckedExpr`；DescriptorSet 为标准 `google.protobuf.FileDescriptorSet`。
5. CheckedExpr 与 FileDescriptorSet 按 Skill 独立输出，Only event-type when 不引入不必要的 input 类型闭包；Schema root/完整资源闭包、类型与 SourcePath 在 Manifest 里必须可相互定位。
6. 诊断沿用当前中央 Compiler 规范语义：非法 CEL、类型不符、未知 input 成员/无声明 Schema 报 `CEL_INVALID`；Schema root/$ref 缺失报 `SCHEMA_MISSING` 或 `SCHEMA_INVALID`；未知作者字段报 `UNKNOWN_FIELD`；Capability/Cardinality 依 SR-029 的明确诊断枚举。诊断必须附 Skill、源码路径、行列和字段路径，不得吞错或降级成功。
7. 输入顺序变化、并行 Skill、不同 Request Schema 同名字段和重复构建必须保持严格闭包隔离与确定性。任何失败没有部分 Artifact/BuildResult outputFiles。

### 4.3 AC-013-02 独立验收矩阵（新规范正负例）

| 样例 | 预期 |
|---|---|
| 无 when、无 requestSchema，合法 1.6.0 Skill | 静态校验通过，无 CheckedExpr/Schema 资产 |
| event.type-only when，未声明 requestSchema | 通过；checked bool program 存在、input type closure 为空 |
| 声明 requestSchema、event.type-only when | 通过；requestSchema 根和完整资源仍发布 |
| input 字段 when + 正确 Request Schema | 通过；CheckedExpr 与 DescriptorSet 路径、类型、SourcePath 闭合 |
| input when 无 requestSchema、未知字段、缺 optional/null 守卫、非 bool、非法 CEL | `CEL_INVALID`，具体失败位置可定位，产物为空 |
| 缺 Schema 根、缺 $ref、冲突或越界资源 | `SCHEMA_MISSING` / `SCHEMA_INVALID`，不得误报 CEL_INVALID |
| 多 Skill 共用 Lock、字段同名但 Schema 不同 | 独立类型环境，拒绝跨 Skill 引用 |
| 同一个新 Skill 的错误 Capability 多成员/双重归属/Effect 不匹配 | 按 SR-029 fail-closed；不能因 when 通过而跳过 Capability Link |
| 历史 v1alpha5 源/旧 BuildRequest 或未知语言 | 明确拒绝，不做翻译、alias 或兼容 |

验收命令：在目标 `ca-skill-compiler` 已冻结的新 1.6.0 分支运行 `GOWORK=off go test ./internal/compiler -count=1` 与 `GOWORK=off go vet ./internal/compiler`，新 fixture 和实际测试名由实施 PR 固定，记录测试数、受测 SHA、预期/实测与 SourcePath。**在 ca-skills 1.6.0 正式规范/Schema 尚未发布前，算法可供设计评审但本 AC 不允许产品 PASS。**

## 5. AC-013-03：新版 Runtime Artifact 契约

### 5.1 版本决策

设计推荐候选 API：Artifact 为 connectionagent.io/compiler-artifact/2，BuildResult 为 connectionagent.io/compiler-build-result/2。新 Runtime Build/DependencyInspection/BuildRequest 均必须提供 **仅支持 CA-SL 1.6.0** 的唯一新 DTO；不复用旧 v1alpha5 机器 API。精确 Schema、Artifact/BuildResult 版本与机器 languageTarget 均由 Compiler Owner Gate 冻结，不能预先把候选值当成已发布契约。

新 Compiler Runtime Build 只产生 2 BuildResult / Artifact，VerifyBuildResult 只接受该新结果契约；不在同一二进制中双轨支持旧/新 Runtime BuildResult，不增加版本 dispatch、fallback 或兼容路由。旧 v2.1.0 Release 保留冻结 Artifact/BuildResult v1alpha5 历史行为；历史 Compiler v2.1.0 的 Development Build 及 v1alpha1 API/Artifact 只留在**旧版发布物**中作审计，不作为新 Compiler 的输入/备用实现。

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

新 Manifest **只由 1.6.0 的唯一正式 Schema 定义**；可复用有用字段的含义，但不得把 v1alpha5 Manifest 或旧 BuildResult 当成兼容输入。每个声明 requestSchema 的 Skill 必须有 requestSchema 对象，记录 sourceRef、rootPath、可选 rootSchemaId（仅根 Schema 声明 $id 时记录）和完整 resources[]（schemaId/path）；该对象与 when 是否存在无关，供 Host 按正式 **CA-SL 1.6.0** Request Schema/when 契约验证 Event payload。根与资源文件同时进入 compiledFiles[] 和 Manifest outputFiles[]。

每个有 when 的 Skill 增加 when 对象，记录 checkedExprPath、descriptorSetPath、sourcePath 和 sourceRange（startLine/startColumn/endLine/endColumn）；仅当表达式引用 input 时，额外记录 requestSchemaRef 与 resolvedRequestSchemaPath，并与同一 Skill 的 requestSchema 元数据一致。when.checked.pb 与 when.types.pb 同时进入 compiledFiles[] 和 Manifest outputFiles[]。逐文件 sha256 复用既有 outputFiles 机制，不增加额外摘要字段。Any type URL 固定为 type.googleapis.com/cel.expr.CheckedExpr；payload 为标准 cel.dev/expr.CheckedExpr。DescriptorSet 是标准 google.protobuf.FileDescriptorSet，只承担 CEL 类型描述，不替代 G.4 Schema 验证数据。

### 5.4 AC-013-03 验收

- 新 Artifact API 与 BuildResult API、JSON Schema、Go DTO/Assembler/Verifier 和文件布局经 Compiler Owner 确认；建议 Schema 路径为 contracts/2/artifact-manifest.schema.json 与 contracts/2/build-result.schema.json。**BuildRequest 必须一并升级为唯一 1.6.0-only DTO**，包括语言标识、Capability Link 所需的准确依赖快照/Owner 身份；不能保留 v1alpha5 BuildRequest，不做旧/新 BuildResult 双版本 dispatch。
- 覆盖 requestSchema / when 的所有组合：无二者、仅 requestSchema、仅 event.type when、requestSchema + event.type when、requestSchema + input when；input when 无 requestSchema 必须 CEL_INVALID。
- 声明 requestSchema 的 Skill 无论是否声明 when，Manifest 都包含已验证 Schema 根与完整闭包；未声明 requestSchema 时不输出 Schema 文件。
- CheckedExpr / DescriptorSet 文件路径、Schema identity、SourcePath 和源码位置闭合。
- 多 Skill 文件与 Descriptor 归属无冲突。
- 新 API 与旧冻结 Artifact v1alpha5、Development v1alpha1 完全隔离。
- 版本化 Schema、Golden 和文档同时更新；旧 Golden 不得被修改来适配新格式。

## 6. AC-013-04：Build / Verify 与产品门禁

### 6.1 Build

- 仅按正式 CA-SL **1.6.0** 进行单一 Parser/AST/静态检查，按 SR-029 校验公开 Capability↔Callable 双向一对一，Procedure 只携带 Capability ID；不得解析旧 v1alpha5。
- 对声明 requestSchema 的 Skill 生成规范化 G.4 Schema 根与完整引用闭包，供 Host 运行期校验。
- 对有 when 的 Skill 生成 CheckedExpr Any 与 DescriptorSet；仅当 when 引用 input 时，DescriptorSet 才纳入该 Request Schema 类型闭包。
- 按新版 Manifest 装配确定性 Artifact。
- 无错误时返回完整 Artifact；任何错误都返回空 OutputFiles，不返回部分产物。
- RFC 8785 JCS、排序和现有确定性规则保持；不写时间、随机值或环境路径。
- 所有 protobuf 产物（包括 `cel.expr.CheckedExpr`、`google.protobuf.FileDescriptorSet`、Any wrapper）必须使用 Go protobuf `proto.MarshalOptions{Deterministic:true}` 编码；Any 内层消息先按确定性模式编码。DescriptorSet 的 FileDescriptor、dependency、message/field declaration 与 source info 顺序必须由稳定排序生成。禁止使用默认 `proto.Marshal` 作为产品 Artifact 序列化路径。
- 确定性保证绑定同一固定 Compiler Release / protobuf runtime 版本与相同输入；不声称跨任意 protobuf runtime 版本的字节兼容。

### 6.2 Verify

- 验证 Artifact API / languageTarget。
- 验证 Manifest、路径、文件清单、重复归属和必需文件。
- 验证已声明 Request Schema 的根与全部资源可解析，保留精确 $id 和 G.4 约束，无未解析/越界/重复资源。
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
- Schema-only Package 只有在 Skill 的 Contract.contexts 显式指向该 Package 的 Schema export 时，才进入该 Skill 的显式依赖闭包；未声明依赖、未导出 Schema ID 或未闭合的 $ref 必须 fail-closed。
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

恢复时先重新核对规范 SHA、Compiler HEAD、Issue #61、目标分支、权限和最后一个已通过 Acceptance；从第一个未通过阶段继续，不重跑或覆盖已通过证据。

### 9.1 DeepSeek Harness Goal 执行约束

SR-013 达到 READY 且文档门禁通过后，实施使用一个连续 Goal，避免将 AC 拆成彼此失去上下文的零散任务：

- 模式：DeepSeek Harness Goal。
- 模型：DeepSeek 最新 Flash。
- 推理强度：low。
- 顺序：AC-013-01 证据复核 → AC-013-02 → AC-013-03 → AC-013-04 → AC-013-06 → AC-013-05。
- 允许在同一个 Goal 内按依赖连续处理多个 AC；不得并行执行有依赖关系的阶段，不得跳过失败阶段。
- 每个 AC 仍需独立记录 Issue #61 关联、提交、测试、受测 SHA 和证据；不得把一个总的 PASS 替代逐 AC 验收。
- AC-013-03 只有在 Compiler Owner 已确认 Artifact API 后才可继续；没有确认就停在 Owner Gate，不得自行更换版本名。
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
3. Compiler **#62** 是 1.6.0-only 的实施入口，须核对正式 Contract/Schema/Golden 与可运行环境；旧 #61 只用于历史版本审计。
4. 目标仓写入授权、分支和实施 Issue 明确。
5. AC-013-03 的 Artifact API Owner Gate 有明确执行方式。
6. AC-013-06 的 Schema-only 正负例、零 Capability roots / Schema dependency closure 区分和跨宿主命令完整。
7. 每项 AC 的 Acceptance、命令、退出条件、证据格式和停止/恢复条件完整。

SR-013 只有 AC-013-01～06 均达到各自通过条件，Compiler Release 有授权且证据可复核，才可报告 Compiler 交付完成。SR-027、SR-004/005/006 的 Bundle/Agent 验收不得由 SR-013 代替。

## 12. CA-SL 1.6.0 统一新接口与设计评审门槛

- 本 SR 的 **设计待评审** 不意味着 Compiler 已实现或 READY；AC-013-02～06 的新产品 Build/Verify/Golden / Release 必须独立通过。
- 新版 Compiler 只处理 CA-SL 1.6.0 Capability-first 源码。Contract/Procedure 的 Capability ID 经 SR-029 定义的一对一约束绑定到唯一 Callable；严格校验 kind、Effect、Input/Output Schema、Owner/Provider Package identity，Artifact 保存已编译的 Binding。
- 与 when/Request Schema 相关的 CheckedExpr、DescriptorSet、Schema 根与 $ref 闭包和 Binding 使用同一个正式 1.6.0 Runtime Artifact。其 BuildRequest、BuildResult、DependencyInspection 和 Verify 使用唯一 1.6.0 DTO；不兼容历史 v1alpha5 和 Development v1alpha1 运行输入。
- 精确 machine languageTarget、API 名称、字段、Schema 与 Golden 必须由 ca-skills / Compiler Owner 在正式 Issue/PR/Release 冻结；历史 Go/Python CEL PoC 可作为算法审计，但不能宣称 1.6.0 产品 PASS。
- 相关设计门禁为 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md)、[SR-004](SR-004-已发布技能包导入.md)、[SR-027](SR-027-技能Bundle构建与发布.md)。按 §9、§11 评审各阶段 READY。Compiler Release 是 AC-013-05 的交付结果；禁止把它列为 AC-013-02～04 或 AC-013-06 的启动条件。AC-013-06 使用按正式 Schema 生成的真实 Publisher 候选做联合验证，记录候选来源和受测 Compiler 提交；AC-013-05 另验发行资产。当前设计仍待独立评审。

## 13. 本轮固定归档核验（Issue #95）

[完整报告](../issue-95-fixed-source-handoff/SR-013.md)基于固定 Next Head `93f1389e7c5968cd30e8a74137207094864ecca0` 与 PR #18 Head `c3e5bb78ff49306329bcbc2387da6108280903bc`。59 个归档文件中，`SHA256SUMS` 覆盖其余 58 个；将清单开头 `/` 归一化为归档相对路径后，额外/缺失文件均为 0、SHA-256 不匹配为 0。18 个历史结果与 36 个 protobuf 可读；本轮未运行 Go/Python。

本轮 AC-013-01 归档完整性判定为 **FAIL**，不是本轮复跑失败：

1. `audit.json` 将 `py-results.json` 登记为 2460 字节、SHA `17cdb49b…`，实际为 2333 字节、SHA `f6abbc68…`；后者与 `SHA256SUMS` 相符。
2. `SHA256SUMS` 全部路径以 `/` 开头，原说明的直接 `sha256sum -c SHA256SUMS` 不能作为可搬移的归档相对校验。
3. `EVIDENCE.md` 声明的 `vet.log` 未归档；历史 vet 结果不得当作本轮执行证据。

AC-013-02/04 仍 NOT_RUN，03/05/06 仍 BLOCKED。整项 DRAFT 主状态不变；本核验不实施 Compiler、不发布 Artifact，也不把历史报告或 CI 当当前产品验收。

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
| 2026-11-27 | 0.2.22 | GPT-6（ChatGPT） | §2、§6.1～6.4、修订记录 | 明确 CheckedExpr/DescriptorSet/Any 的确定性 protobuf 序列化与逐 `.pb` 字节验收；统一 AC-013-02/04 NOT_RUN、AC-013-03/05/06 BLOCKED；按版本恢复连续修订账本 | 处理独立模型 Review #6082541121 的 R3-SR013-01/02 与 R3-LEDGER-01，避免 protobuf 默认 Marshal 导致 Build 非确定及状态表冲突 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.23 | GPT-6（ChatGPT） | §0、文档头、修订记录 | 将历史 fd80c74 评审登记替换为正式 Review #6082541121 的固定 Head/Base；明确 P2 修订发生在后续 Head，必须重新独立复评 | 防止把不可访问或不同 Head 的评审记录混为一谈 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.24 | Codex / GPT-6 | 文档头 | 登记阶段 READY（中央只读核验）及 AC 范围与工作项 #95 | 按单项独立评审推进 | Issue #12、#77；PR #46 |
| 2026-11-27 | 0.2.25 | kimi-k3.1-pro | AC-013-01、§13、文档头 | 核对 58 项归档哈希与历史结果，发现 audit 登记不一致、绝对式校验路径及 vet 日志缺项；将本轮归档完整性记为 FAIL，复跑 NOT_RUN | 区分文件存在性、内部一致性和产品运行验收，避免过度判 PASS | Issue #95；PR #18 |
| 2026-11-28 | 0.2.28 | GPT-6（ChatGPT） | 头部、AC-013-01、实施前置 | 明确新版 Compiler #62，修正 cases.json 固定证据路径；历史 #110 已合独立证据分支但当前产品 AC 不升级 | 防止历史 #61/归档修复变成新 Compiler 产品资格 | Issue #12；#40；#102；PR #45；#46；#110 |
