# CA-SL Compiler 设计说明书

> 文档版本：0.1.8  
> 状态：待评审；IR-006 / SR-012 / #2  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、5GC/MAS 认证及发布。

关联 [IR-006](../../IR/IR%20总登记册.md#ir-006)、[SR-012](../../SR/SR-012-Compiler设计归档与跨仓收敛.md) 和 [Next #2](https://github.com/odango-chan/ca-agent-next/issues/2)。

## 1. 权威与版本

CA-SL v1alpha5 语言和 IngressCatalog 由 ca-skills 发布；已发布 JSON Schema、fixture 和 golden 由 ca-skill-compiler 维护。EC02 维护机制设计，F02 维护 Next 消费行为。Compiler 产品为 v2.1.0，语言目标仅 `connectionagent.io/v1alpha5`。冻结 Build/Verify v1alpha5 Artifact 保留 `generator.version=v2.0.2`、布局、字节和复验语义。Development v1alpha1 独立版本化，始终 `NOT_ADMITTED`。参见[冻结 API](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/contracts/v1alpha5/README.md)和 [Development API](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/contracts/development/v1alpha1/README.md)。

## 2. 单一 Core 与入口

Native CLI 与 Go/WASM Worker 调用同一个 Go Core。Check 返回诊断，InspectDependencies 解释依赖和链接，Build 通过静态校验后组装确定性产物，冻结 VerifyBuildResult 校验成功结果及产物树自洽；Development Verify 使用原请求重建并比较。失败不返回部分产物。Transport 解码、版本、路径、限制、可信上下文先于 YAML 解析；统一 AST 管线依序完成 Contract/Predicate/Script、标识和依赖绑定、Owner/Tool/Capability/Evidence 链接、Schema 闭包与赋值/CEL 检查、Procedure 图与 Wait/Mutation/Evidence 语义检查。Compiler 不执行 Tool、Python、网络过程或 Runtime。参见[源码入口](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/api.go)、[冻结 Artifact 布局](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-artifact-v1alpha5.md)、[核心 API 源设计](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-core-v1alpha5.md)。

冻结 Build 成功返回 `connectionagent.io/compiler-build-result/v1alpha5`、排序的 OutputFiles 和 DependencyClosure。失败返回空 OutputFiles 和空 DependencyClosure。输出为 RFC 8785 JCS：顶层 `manifest.json`、每 Skill 的 `compiled/procedure.json` 与 `compiled/ingress-links.json`。源码只记录路径与域分离摘要。Manifest 记录静态验证范围、生成器、依赖闭包、Skill 源与编译文件、Wait 的 ingress/response 绑定，以及除 Manifest 自身外的文件 SHA-256。序列化、排序与摘要不依赖时间、环境或输入文件顺序。Verify 拒绝路径重复、非规范 JSON、错误版本、未知或缺失文件、摘要不符、重复归属、Wait/Ingress/response 元数据不一致及结果闭包与 Manifest 不一致。CLI 验证通过后才写入新建或空输出目录。

## 3. 机制与职责

- [工具链机制设计](工具链设计.md)定义编译、Interface Link 和发布边界，以及外部 Host/Owner 责任。
- [Development Build 设计](Development%20Build设计.md)定义精确身份、快照和 Lock 闭包、Schema 作用域、多 Skill 每 Skill Root 及共同闭包、Capability requirement 与复验。
- [Evidence 与 Owner Trust 职责设计](Evidence职责设计.md)定义静态 Evidence 链接、精确 Owner 来源与外部待决 Requirement。Compiler 校验声明与引用，不授予权限、确认 Owner 信任或判定实际 mutation COMMITTED。Capability Requirement 不是 Capability Grant。
- F02 仅导入外部已发布 Bundle。Development 产物及其 Host Admission Requirements 不能作为 Next 导入契约。Next 运行时不调用 Compiler。

## 4. 一致性审查与交接

| 分类 | 证据与结论 |
|---|---|
| BLOCKER | [ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 尚开放。when 正式规范和固定 SHA 是 Compiler #61 的 P0 门槛。 |
| BLOCKER | [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) 尚开放。当前 `ContractAST` 无 when；既有 Predicate CEL 路径的 DynType 不能满足 typed input。必须先证明 CheckedExpr Any 与 DescriptorSet 的 Go/Python 互操作及 optional/null 语义，再定新版发布 Artifact。 |
| BLOCKER | Next SR-004/005 的正式发布 Artifact、互操作证据与 READY 门槛尚未满足。严禁用 Development v1alpha2 名义交付运行包。 |
| NON_BLOCKING | 既有核心说明中出现旧产品版本；版本以 v2.1.0 发布记录为准。源实现报告的旧版本号和 PASS 属历史执行。 |
| NON_BLOCKING | 冻结 API 与 Development 两套入口是不同输出契约，复用同一 Core。真实 MAS 离线输入及产品资格是独立验收，见 Compiler #53。 |
| UNVERIFIED | 本轮仅核对冻结契约、源码文件和历史报告，Compiler 回归、Go/Python PoC 与 Next 导入测试均 NOT_RUN。 |

复核入口：[Development 实现与验收报告](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-development-build-implementation-report.zh-CN.md)、[Schema Registry](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/schema_registry.go)、[Development Link](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_link.go)、[多 Skill Lock 测试](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_multi_skill_test.go)、[Evidence Owner 测试](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_evidence_owner_test.go)。历史版本设计见[冻结归档](https://github.com/odango-chan/ca-skill-compiler/tree/72b41548a9c4d29c6c49abed117a04a963454f22/docs/design)。

## 5. DeepSeek Harness Goal 提示词

将以下任务粘贴到 Goal 模式。若界面已启用 Goal 模式，去掉首行的 `/goal` 命令前缀。

~~~text
/goal 推进 CA-SL v1alpha5 已检查 when 的 Compiler → Python Runtime 交付，直至目标 SR 的必需验收全部有可复核证据，或已完成所有可独立推进的工作且具体外部门槛仍阻塞。保持冻结 v1alpha5 Build/Verify 与 Development v1alpha1 的契约、字节和行为。未经用户授权不得合并 PR 或发布版本。

入口：odango-chan/ca-agent-next PR #3 的 EC02 Compiler 设计说明书、Agent.md 的 review_scope、功能树 EC02/F02、SR-012、SR-013、SR-004/005 和《跨仓互操作实施任务说明》。上游追踪 odango-chan/ca-skills PR #88、odango-chan/ca-skill-compiler Issue #61。以本文 §6 的阶段输入与证据包作为交接清单。执行前逐仓记录目标 ref、HEAD SHA、工作区状态、目标 SR 和 Acceptance ID。

0. AC-013-01 隔离 PoC 阶段按 SR-013 的阶段执行单为 READY。可在隔离副本直接执行该阶段；下列各产品阶段仍逐项核对 READY 与授权。
1. 先做只读预检。复核语言规范是否已合入并发布、#61 的范围与依赖、目标 SR 是否 READY、目标仓写入授权、可运行环境与固定输入。逐项记录阻塞、解除条件、权威链接和可独立推进的工作。无写入权限或目标 SR 未 READY 时保留源码与治理状态，继续只读核对。不得把上游 PR 打开、历史 PASS 或设计文档当作当前验收。
2. 已获授权且门槛满足后，固定正式语言规范 SHA 及 Go/Python/CEL/protobuf 版本。先执行 Go cel-go → CheckedExpr Any + FileDescriptorSet → cel-expr-python 的最小 PoC。用实际输出验证 true/false/error、未知字段、缺失与 null、数值边界以及共享 Lock 下的多 Skill 类型隔离。发现语义差异，保存最小复现与证据并暂停依赖该 PoC 的阶段。
3. PoC 通过后，按 #61 实施版本化发布 Artifact。复用同一 Compiler Core，冻结产物保留原字节，Development 继续 NOT_ADMITTED。发布产物和 SR-004/005 门槛满足后，Next 仅消费外部发布 Bundle，执行结构、引用和 callable scope 检查并加载已检查程序。Agent 不调用 Compiler，不引入 Skill Admission、Owner Trust Registry 或第二套 CEL 实现。
4. 在 Compiler 仓执行 #61 的 Go test、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 和 git diff --check。对 Next 执行目标 READY SR 指定的 Acceptance。每项记录需求 ID、执行命令、环境与版本、受测 SHA、退出码和证据链接。需要合并或发布才能解除门槛时报告待授权事项。
5. 每轮保留可恢复交接：最后完成阶段、仓库与 SHA、变更或 PR、验收结果、阻塞及第一个可执行的恢复步骤。恢复后先重新核对 ref 与门槛，再从第一个未验收阶段继续。只有全部必需验收 PASS 才报告目标完成。外部阻塞时以 BLOCKED 收尾，附已做的预检与解除条件；不得把阻塞交接写成完成。
~~~

## 6. 实施输入与验收交接

以[跨仓互操作实施任务说明](../../验收与实施/跨仓互操作实施任务说明.md)的阶段步骤、[演示验收基线](../../验收与实施/演示验收基线.md)和对应 READY SR 的验收 ID 为准。以下证据包用于阶段间交接。归档 SR-012 的权限范围只覆盖文档收敛，Compiler 实施由 [SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md) 覆盖实际代码和测试改动。

| 阶段 | 必需输入 | 可继续的条件 | 必交证据 |
|---|---|---|---|
| 0 门禁 | Next 设计 ref；各仓 HEAD；CA-SL 规范发布记录；目标 SR、授权和 Acceptance | Compiler 实施 SR 已登记并 READY；#88 正式规范可固定 SHA；环境可运行 | 逐仓 ref/SHA、SR/Issue、权限、环境、未满足门槛及解除条件 |
| 1 CEL PoC | 固定规范 SHA；固定 Go/Python/CEL/protobuf 版本；#61 §1–2 样例 | Python 加载 Go 生成的同一 Any 与 DescriptorSet；同一真值表与错误语义；G.4 缺失与 null 行为一致 | 可复跑命令、输入与预期表、原始两个 protobuf 文件、Go/Python 实际结果和最小失败样例 |
| 2 Compiler 契约与回归 | PoC PASS；Compiler Owner 确认的新 Artifact API 版本与文件布局 | 验证新版成功、损坏产物拒绝、失败时空结果、多 Skill 类型隔离；两个冻结 profile 的机器契约与 Golden 对基准字节一致 | 契约 diff、fixture/golden、冻结产物比较、#61 全部门禁日志与受测 SHA |
| 3 Next 导入与验收 | 正式发布的新版 Compiler 契约与实际 Bundle；READY 的 SR-004/005；涉及 Resolver/Continuation 时另核对 SR-006 | Bundle 导入和拒绝路径符合 SR；导入时一次反序列化；Catalog 原子切换与代际固定；Event 热路径仅求值；阶段必需 Acceptance 全 PASS | Release SHA/资产、Bundle 来源、以 SR 为单位的 Acceptance 表与执行日志 |

PoC 至少覆盖：同一程序对多个 Event 分别得到 true、false 和运行期错误；未知字段、缺 Request Schema、非 bool 及禁用语法在 Compiler 静态阶段失败；可选字段缺失、显式 null、带守卫可安全求值；不同 Skill 共用 Lock 时，使用另一 Skill 的 Schema 或 Descriptor 不能放宽原 Skill 的类型环境。使用正式规范给出的预期并保留实际诊断，任何差异都阻断依赖阶段。

验收记录每行至少包含 `stage | SR/Acceptance | repository@SHA | fixture/source | command | environment | expected | actual/exit_code | result | evidence`。门槛缺失且尚未运行时记录 `BLOCKED` 并附解除条件。未运行且无外部阻塞的检查记 `NOT_RUN`。只对实跑并符合预期的记录写 `PASS`。需要 Owner 裁定 Artifact API、评审 READY 或授权发布时，保留已通过的独立阶段证据及第一个恢复步骤。

正式 CA-SL v1alpha5 规范固定为 `18d8184367982ccbc835756136c4a53f9096c3a0`，见 [ca-skills 正式发布记录](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。此门槛已满足。Next PR #3 已合并；SR-013 的实施范围与验收仍待负责人确认，AC-013-01 为进入 READY 后的首项验收。

## 7. 技术评审与 READY 判定

复核基线：Next PR #3 的 `380092b6133140c05a087c63f848a17ab1850905`、ca-skills #88 的 `2eedf4231075b6c589212d7d25576c7abbe6a5d9`、Compiler #61 与 v2.1.0 冻结契约。以下为静态评审，产品验收未运行。

| 结论 | 要求和证据 | 处理 |
|---|---|---|
| BLOCKER | [ca-skills #88 附录 M.4 / SA-002、009、011](https://github.com/odango-chan/ca-skills/blob/2eedf4231075b6c589212d7d25576c7abbe6a5d9/docs/skill-language-spec.v1alpha5.zh-CN.md#m4-skill-import-与编译边界) 将 Compiler Check/Build、Inspect/Verify 和 Host Admission 写成 Skill Importer 的 MUST；Next Agent.md 与 Compiler #61 排除 Agent Compiler 调用及独立 Skill Admission。 | 规范负责人应明确作者源编译与资格流程属于外部工具链或独立产品 profile，并明确 published Bundle 消费路径的必需行为。更新对应 SA 用例，明确 Next 可声明的符合范围。冲突解决并正式发布前，不把 M.4 导入要求下发给 DSH。 |
| 待澄清 | #88 §12.8 / M.3 要求先校验 Request Schema，语义候选条款又以未声明 when 为条件；SA-008 未给出未声明 when 且 Request Schema 不匹配的预期。 | 在规范中补一条带具体 payload 的负例，明确其是否加入语义候选及诊断。DSH 不自行把 Request Schema 不符当作运行期 CEL error。 |
| 待验证 | #88 M.2 继承 G.4，声明唯一字段、bool、纯表达式及 Request Schema 类型来源。SA-004/005 有编译正负例；缺失、显式 null、has 守卫与数值边界仍需 AC-013-01 的真实 Go/Python 输入输出验证。 | 按正式规范为同一 fixture 固定输入、预期及错误阶段；不得以文档校验代替运行证据。 |
| NON_BLOCKING | 编译单核与发布边界与 Next 方向一致；两种 Verify 的具体行为已分别列出。 | 历史样例、机器 Schema 和 release evidence 保留固定 SHA。 |

以上为首轮评审记录。复审 [ca-skills #88 修订提交](https://github.com/odango-chan/ca-skills/commit/697246a967067cdeddb01c2f43b11a3e56afa480) 后，M.4 与 SA-002/009/011 已明确外部编译发布与 Agent 导入的职责。§12.8、M.3 和 SA-012 已明确 Request Schema 不符时排除候选并记录诊断。两项评审发现已在候选文本中解决。该提交的 source-hygiene PASS；AC-013-01 仍为 NOT_RUN。

正式规范门槛已解除。SR-013 保持 DRAFT，待负责人确认实施范围与 READY 后执行 AC-013-01。PoC 通过后由 Compiler Owner 裁定新版 Artifact API。

AC-013-01 的 Windows 环境和常量交换已预检。Go 默认 CheckedExpr Any 类型标识在 Python 下被拒绝；使用 `cel.expr.CheckedExpr` 重新构造 Any 后常量求值通过。完整 typed fixture 未执行，见 SR-013 的预检记录。

AC-013-01 的隔离 PoC 已可启动，正式产品实施仍按 SR-013 的后续阶段条件执行。先执行 SR-013 的阶段执行单。

## 修订记录

| 日期 | 版本 | 修订者 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 设计基线 | 集中维护及验证交接 | IR-006、SR-012、#2 |
| 2026-11-25 | 0.1.1 | Codex | §5 | 加入 Goal 的实施门槛、恢复点和完成判据 | 支持分阶段执行及阻塞后恢复 | IR-006、SR-012、#2、PR #3 |
| 2026-11-25 | 0.1.2 | Codex | §5–6 | 明确分阶段输入、退出条件、证据包及实施 SR 边界 | 降低 Harness 自主执行时的裁量 | IR-006、SR-012、#2、PR #3、Compiler #61 |
| 2026-11-25 | 0.1.3 | Codex | §5–6 | 绑定 Compiler 实施 SR | 明确 Goal 执行及验收入口 | SR-013、Compiler #61 |
| 2026-11-25 | 0.1.4 | Codex | §7 | 登记规范与 Next 的职责冲突及 READY 判定 | 防止 DSH 误执行 M.4 | SR-013、ca-skills #88 |
| 2026-11-25 | 0.1.5 | Codex | §7 | 复审 #88 修订并更新发现状态 | 区分候选文本已解决与正式实施门槛 | SR-013、ca-skills #88 |
| 2026-11-25 | 0.1.6 | Codex | §6–7 | 固定已发布规范 SHA | ca-skills #89 已合并 | SR-013 |
| 2026-11-25 | 0.1.7 | Codex | §7 | 回链实跑预检 | 记录已验证的交换路径和剩余范围 | SR-013 |
| 2026-11-25 | 0.1.8 | Codex | §5–7 | 更新 Goal 的隔离 PoC 入口 | 供 DSH 独立开展 AC-013-01 | SR-013 |
