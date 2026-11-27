# PR #54 独立技术与治理评审报告（Issue #53）

> 评审类型：独立、只读技术与治理评审  
> 评审时间：2026-11-27 11:39（Asia/Shanghai）  
> 技术结论：**REQUEST_CHANGES**  
> GitHub 留痕方式：**COMMENT**（当前身份 `odango-chan` 与 PR 作者相同，不能提交伪造 APPROVE）  
> 本报告不代表允许进入 main，也不修改任何 SR 状态。

## 1. 评审基线及 SHA

### 1.1 固定输入

| 项目 | 本轮实际结果 | 证据 |
|---|---|---|
| PR | [#54](https://github.com/odango-chan/ca-agent-next/pull/54)，OPEN / Draft，`mergeable=true`、`mergeable_state=clean` | GitHub PR API，快照见 `evidence/pr54.json` |
| 作者 / 当前身份 | `odango-chan` / `odango-chan` | PR API、`gh auth status` |
| Base | `docs/restore-original-designs-20261125` @ `34e99e0cc54cc82b6b40040286fc84673432ef76` | PR API、fetch 后 `git rev-parse` |
| Head | `docs/issue-53-refresh-state-reconciliation` @ `7452f60ccbc68e1468b52018f59bdc2347cc32d5` | PR API、`refs/pull/54/head` |
| Refresh 原分支 | `docs/refresh-current-state-20261126` @ `f63bbce2709284c97d8cd150343d491a3f2958db` | fetch 后 `git rev-parse` |
| 原共同祖先 | `32c7c1be5e93bddc83349234476b2ffa09e1ca23` | `git merge-base` |
| Issue | [#53](https://github.com/odango-chan/ca-agent-next/issues/53)，OPEN | `evidence/issue53.json`、`issue53-body.md` |
| 变更规模 | 42 commits；16 个修改文件；269 additions / 150 deletions | PR API、`git diff --numstat` |
| Review / Review Threads | 0 / 0；无未解决意见 | REST 与 GraphQL，见 `pr54-reviews.json`、`pr54-review-threads.json` |

历史基线 `34e99e0` / `f63bbce` / `32c7c1b` / `7452f60` 与本轮实际结果一致。没有复用旧 Head 的 CI 作为当前 Head 证据。

`32c7c1b..f63bbce`（即三点 `restore...refresh`）确为 16 份 refresh 修改文件；两点 `restore..refresh` 为 19 份，额外三份来自 restore 后续的 SR-003 更新，而不是 refresh 独有提交。§10 的“refresh 独有 6 提交涉及 16 文件”口径成立，但修复时应补充这三份排除项，避免两点/三点比较被混用。

### 1.2 当前 Head 的全部 Workflow / CI

GitHub `head_sha=7452f60ccbc68e1468b52018f59bdc2347cc32d5` 查询到且仅查询到以下四次 Review Context Run，全部 `completed / success`：

| Run number | Run ID | Head SHA | 结论 |
|---:|---:|---|---|
| 192 | [45931351062](https://github.com/odango-chan/ca-agent-next/actions/runs/45931351062) | `7452f60…` | SUCCESS |
| 193 | [45931389307](https://github.com/odango-chan/ca-agent-next/actions/runs/45931389307) | `7452f60…` | SUCCESS |
| 194 | [45931435003](https://github.com/odango-chan/ca-agent-next/actions/runs/45931435003) | `7452f60…` | SUCCESS |
| 195 | [45931519416](https://github.com/odango-chan/ca-agent-next/actions/runs/45931519416) | `7452f60…` | SUCCESS；有 Artifact `review-context-pr-54-45931519416-1` |

证据：`evidence/head-workflow-runs.json`、`head-check-runs.json`、`head-run-195-jobs.json`、`head-run-195-artifacts.json`。历史 #191 只属于旧 Head，不作为通过证据。上述 CI 仅证明 SR-001 Review Context 测试、头部校验和 Artifact 生成，不证明设计内容、链接、SR 状态或产品 Acceptance 正确。

## 2. PR 文件差异清单

| # | 文件 | + / - | 整合方式（§10） |
|---:|---|---:|---|
| 1 | `docs/IR/IR 总登记册.md` | 7 / 4 | 手工合并 |
| 2 | `docs/SR/SR-016-工作台设计移交与条件编辑.md` | 13 / 7 | 纳入并刷新 |
| 3 | `docs/SR/SR-025-MAS Owner Interface Package Publisher.md` | 18 / 12 | 直接纳入 |
| 4 | `docs/参考与审计/跨仓依赖与可行性审计.md` | 19 / 6 | 手工合并 |
| 5 | `docs/参考与审计/跨仓设计资产迁移与一致性审计.md` | 33 / 18 | 手工合并 |
| 6 | `docs/架构设计/CA Agent Next 架构设计.md` | 22 / 11 | 手工合并 |
| 7 | `docs/架构设计/外部能力域架构总览.md` | 10 / 8 | 纳入并刷新 |
| 8 | `docs/治理/SR 总索引.md` | 12 / 11 | 手工合并 |
| 9 | `docs/治理/功能树与需求追踪基线.md` | 10 / 9 | 手工合并 |
| 10 | `docs/治理/实施状态总览.md` | 14 / 14 | 手工合并 |
| 11 | `docs/治理/文档总目录与索引.md` | 11 / 10 | 纳入并校正 |
| 12 | `docs/治理/现有文档盘点与收敛计划.md` | 48 / 10 | 手工合并 |
| 13 | `docs/设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md` | 11 / 4 | 直接纳入 |
| 14 | `docs/设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md` | 8 / 6 | 直接纳入 |
| 15 | `docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md` | 22 / 12 | 纳入并刷新 |
| 16 | `docs/验收与实施/演示验收基线.md` | 11 / 8 | 手工合并 |

完整差异保存在 `evidence/pr54-base-head.diff`；refresh 原始差异保存在 `evidence/refresh-original-delta.diff`。

## 3. 16 份文件逐项评审结论

行号均指 Head `7452f60` 的 blob；问题详情见第 9 节。

| # | 文件 | 逐项结论 |
|---:|---|---|
| 1 | IR 总登记册 | 主体整合正确，L33 保留 SR-003 v0.3.11 模块 VERIFIED；L88 的 SR-025 v0.1.7 未随实际 v0.1.8 更新（P2-03）。 |
| 2 | SR-016 | refresh 的 READY Publisher、#272 MERGED、#276 DIRTY 与正确 Studio SHA 已纳入；但 L31 对 Host fixture provenance 的当前能力判断过宽且过时（P1-05），L11 的 F09 版本未同步（P2-03），历史 SHA 被回写（P2-04）。 |
| 3 | SR-025 | v0.1.8 / READY、AC-025-01～08、127 exports、Issue #43 和 NOT_STARTED/NOT_RUN 完整保留；L10 的 F09 设计版本未同步（P2-03），L76 将下一作者模型预先写成 v1alpha6，与 CA-SL 1.6.0 机器标识待冻结的方向冲突（P2-09）；本轮实质仅为版本/修订行追加（P3-02）。 |
| 4 | 跨仓依赖与可行性审计 | L100 把 #272 错写为 OPEN（P1-04）；L31 保留 23 SR/150 Markdown 旧统计（P2-08）；头版本 0.2.12 无对应修订记录（P2-02）；§8 仍是旧 SR-003 快照（P2-05）。 |
| 5 | 跨仓设计资产迁移与一致性审计 | L133 把 #272 错写为开放 Draft（P1-04）；L65 把已实现 Plugin Manager 写成未完成（P1-02）；§2 四列表被三列表覆盖且丢失 restore 有效约束（P2-01）；多处版本、基线和修订链未收敛（P2-03～05）。 |
| 6 | CA Agent Next 架构设计 | 核心架构边界未被改写；L245 的 Studio 完整 SHA 拼写错误（P1-03），L246/L253 保留旧 restore/PR Head（P2-05）。 |
| 7 | 外部能力域架构总览 | EC01～EC07、REF/TARGET 和当前 SR 状态整合基本正确；L67 当前快照日期仍为 11-26（P3-01）。 |
| 8 | SR 总索引 | 27 项清单及 4/1/1/21 统计正确；L97 仍把已关闭 PR #13 列入 OPEN/DRAFT（P2-06），与 restore 的同号修订记录发生碰撞（P2-04）。 |
| 9 | 功能树与需求追踪基线 | L202 把 #272 错写为 OPEN、L168 固定旧 Studio main（P1-04）；L122 保留旧 SR-003 Head（P2-05）；F09 版本指针和修订链未同步（P2-03/04）。 |
| 10 | 实施状态总览 | L17 DRAFT=22 使合计为 28（P1-01）；L92 把 SR-003 写成未集成且 Issue #28 OPEN（P1-02）；L66 的 sourceStatus 当前状态错误（P1-05）；另有多处旧基线/PR 状态（P2-05/06）。 |
| 11 | 文档总目录与索引 | 197/157/48 统计正确；L120 的迁移审计版本、L55/L158 的 F09 与 SR-016 版本过期（P2-03）；L65 的 13 与 L43 的 14 冲突（P2-08）；修订序号重复（P2-04）。 |
| 12 | 现有文档盘点与收敛计划 | L75 仍是 3 VERIFIED/2 READY，与 L67/L101 的 4/1 冲突（P1-02）；L5=0.3.17 而最后修订为 0.3.18（P2-02）；历史修订表格列数不一致（P2-01）。 |
| 13 | F02 Skill 管理与选择 | CA-SL Release Record、when、Runtime Artifact 和 Next 消费边界完整；L6/L11 两个不同“修订日期”（P2-02），本轮实质仅为头版本和修订行追加（P3-02）。 |
| 14 | F08 技能编译与发布 | 语言发布、Compiler、Bundle 与 Verify 边界正确；历史修订表多行列数不一致（P2-01），本轮实质仅为头版本和修订行追加（P3-02）。 |
| 15 | F09 Skill Studio | L147 把 #272 merge 与 main 混写（P2-07）；L153/L165 对默认 Host fixture provenance 的当前状态判断错误（P1-05）；设计版本、修订历史及日期存在 P2/P3 项。 |
| 16 | 演示验收基线 | SR-003 最终模块证据完整保留，系统 EX 未扩大；L142 自引用 v0.3.17 未随头部 v0.3.18 更新（P2-03），L214 把整合 PR 写成不存在的 PR #53 而非 #54（P2-06），修订链有缺项（P2-04）。 |

## 4. SR 状态核验表

### 4.1 27 项权威 SR 文件实测

通过 `git ls-tree` 和逐文件状态头重新计算，**27 项无重复、无漏项；4 VERIFIED / 1 READY / 1 IMPLEMENTED / 21 DRAFT**。权威 SR 文件本身符合预期；不一致发生在部分汇总/审计文档。

| SR | 实测状态 | 核验 |
|---|---|---|
| SR-001 | VERIFIED | 符合预期 |
| SR-002 | VERIFIED | 符合预期 |
| SR-003 | VERIFIED | 仅模块 AC-003-01～04；符合预期 |
| SR-004～SR-013（10 项） | DRAFT | 符合预期 |
| SR-015 | IMPLEMENTED | 符合预期；产品代码未因此自动完成 |
| SR-016～SR-023（8 项） | DRAFT | 符合预期 |
| SR-024 | VERIFIED | 符合预期 |
| SR-025 | READY | v0.1.8；符合预期 |
| SR-026～SR-028（3 项） | DRAFT | 符合预期 |

机器结果见 `validation-results.json`：`sr_total=27`，状态分布为 `DRAFT=21 / IMPLEMENTED=1 / READY=1 / VERIFIED=4`。

### 4.2 SR-003 专项

权威 SR-003 为 v0.3.11，AC-003-01～04 均已定义并有真实双平台 CI 支撑。PR [#34](https://github.com/odango-chan/ca-agent-next/pull/34)、[#41](https://github.com/odango-chan/ca-agent-next/pull/41)、[#42](https://github.com/odango-chan/ca-agent-next/pull/42) 均按顺序 MERGED 到 restore，不是 main。

| 证据 | 本轮独立查询结果 |
|---|---|
| PR #34 | Head `e8bcb1b89de5094a4b1b68f973af6720801c7fbd`；merge `32c7c1be…`；Head/Merge 同 tree |
| PR #41 | Head `f3f59b54e19d317e8e8056e5a15963c3fd038aaf`；merge `a899409e…`；Head/Merge 同 tree |
| PR #42 | Head `c57395504a470b5293a5749c58daafd6ad564ff2`；merge `34e99e0c…`；Head/Merge 同 tree |
| Linux / Windows | Run [45815167442](https://github.com/odango-chan/ca-agent-next/actions/runs/45815167442)、[45817800342](https://github.com/odango-chan/ca-agent-next/actions/runs/45817800342) 及补充 Run [45819344112](https://github.com/odango-chan/ca-agent-next/actions/runs/45819344112) 均为 SUCCESS；原始 Job 为 Ubuntu/Python 3.12 与 Windows/Python 3.14，各 87 Plugin + 52 Host + 80 Review Context tests OK |
| merge SHA post-merge CI | 三个 merge SHA 的直接 Workflow 查询均为 0；只能表述为 PR Head CI SUCCESS + 同 tree，不能声称 merge SHA 上重新运行 |
| 系统 EX-02/03/04/18 | **NOT_RUN**；模块 AC 不得扩大为系统验收 |

SR-003 模块 VERIFIED 有证据，但《实施状态总览》L92、《跨仓依赖与可行性审计》§8、《功能树》L122 等仍有旧状态/旧 Head，必须修复。

### 4.3 SR-025 专项

- 实际文件：v0.1.8 / READY；AC-025-01～08 全部存在，包身份、127 exports、56 payload、Build/Verify 正负例及 Release gate 完整。
- [ca-client-tools Issue #43](https://github.com/odango-chan/ca-client-tools/issues/43) 本轮 API 实测为 OPEN；main 为 `7bcb2614aa3615d8358df31eecefd0909e894e40`。
- 建议的 `internal/ownerinterfacepkg` 与 `cmd/ca-client-tools-owner-interface-release` 当前 main 均未发现；实施 PR/Commit 为空。
- 结论：READY 不得写成 IMPLEMENTED；Publisher 设计完成不得写成 Publisher 已实现；AC-025-01～08 保持 NOT_RUN。
- 独立源码探针 `validate_sr025_source.py` 实测 **PASS**：当前 main 与 source Revision 的 59 文件无差异，58 个 artifact digest 全匹配；25 published / 7 notPublished；24 Capability IDs / 25 members；25 EvidenceDescriptor；54 Schema 中公开闭包 53，唯一排除 `deployment-binding`；55 个原始 payload 为 80,479 bytes，导出总数 127。该结果支持 READY 的设计依据，但不代替 Publisher generate/verify、Compiler Build/Verify、go test 或 Release Acceptance。

## 5. 架构一致性审查结果

| 审查点 | 结果 | 证据与边界 |
|---|---|---|
| Agent 通用性 / 业务解耦 | PASS | 总体架构 L16～18、L95～105；OpenAMSM 仅经 Skill/Plugin/Package/配置接入 |
| Tool 作为特殊 Plugin | PASS | 总体架构 L146～158、F03.05 L19～22/L69～78；唯一 Plugin Manager，无第二 Registry |
| Skill 选择 / Procedure 执行边界 | PASS | 总体架构 L121～164；when 仅选择，predicates 仅执行期，Procedure 不直接调 Plugin |
| CA-SL 设计方向 | **当前 v1alpha5 历史基线正确；未来命名有 P2-09** | PR #51《主干收敛计划》L168-L183 和 PR #45 SR-029 L18-L20/L95-L100 均明确下一方向为 CA-SL 1.6.0、NOT_RELEASED、准确 languageTarget 待正式冻结；PR #54 不应提前引入该未来设计，但 SR-025 L76 也不应猜测为 v1alpha6 |
| Schema / Scripts 对 LLM 可用性 | PASS | SKILL.md 面向 Agent；requestSchema 驱动输入校验，references/大型材料按需加载；未引入第二 Descriptor |
| when 选择机制 | PASS | F02 L91～114、CA-SL Release Record L27～37；Schema 资格先于 CEL，false/error 不回退语义候选 |
| Provider / Interface Package / Runtime Bindings | PASS | F03.05 L80～90；公开 Callable、Owner 语义和私有 backend 映射分层 |
| Compiler / Skill Studio | PASS（目标边界）；实现状态有 P1 | F09 §4～6 只让 Studio 构造请求/保存快照，Compiler 负责链接/验证；P1-05 的当前 provenance 表述须纠正 |
| OpenAMSM Plugin 业务接入 | PASS | EC04 仅 ingress/delivery/staging，不选 Skill、不创建 Run、不实现 Owner |
| 旧设计 / 兼容设计回潮 | 未发现 P0 | 明确不引入 v1alpha6、activation/constraint、第二 Manager、旧版兼容层；但迁移审计发生有效内容覆盖，见 P2-01 |

未发现 P0 架构根本冲突。问题集中在当前状态、证据身份和文档整合可信度，而不是核心目标架构。

## 6. F02 / F08 / F09 专项审查

### 6.1 F02

- ca-skills #88/#89 均 MERGED，#87 OPEN；[Release Record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md) 为 FROZEN / RELEASED，规范提交 `18d8184367982ccbc835756136c4a53f9096c3a0`。
- when 的作者语义已发布，但 CheckedExpr/DescriptorSet Runtime Artifact 与 Go→Python 产品互操作仍由 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) OPEN 跟踪；Development NOT_ADMITTED 不得作为 Agent Runtime 输入。
- 结论：设计边界正确；头部重复日期必须修复。

### 6.2 F08

- Compiler v2.1.0 Release 实际存在且非 Draft/prerelease；语言规范 RELEASED 不等于 Compiler 新 Runtime Artifact、ca-skills Bundle Build/Verify 或 Next Runtime PASS。
- F08 §6 明确分离 SR-013 / SR-027 / SR-004～006 的验收责任，没有将语言规范发布等同产品发布。
- 结论：目标边界正确；修订表和纯版本递增记录需清理。

### 6.3 F09 / Studio 实时证据

| 项目 | 本轮实际状态 | 对 PR 文档的判断 |
|---|---|---|
| main | [`79bd2c3f64a90e7f0f169204c866a3218655bab1`](https://github.com/odango-chan/ca-skill-studio-demo/commit/79bd2c3f64a90e7f0f169204c866a3218655bab1) | SR-016/F09 正确；总体架构 L245 错误 |
| #261/#269/#279/#290/#295 | 均为 Issue、OPEN | 文档将其称为 PR 的位置应修正为 Issue |
| #272 | MERGED；merge [`a8633553615d786e360a62c2b0042a27ae92d9d3`](https://github.com/odango-chan/ca-skill-studio-demo/commit/a8633553615d786e360a62c2b0042a27ae92d9d3) | 仅 request builder；F09 L147 的 merge/main 写法需拆分 |
| #276 | OPEN / DRAFT / DIRTY；head `7d6adebaca12f09d5ddc5e04f7457b8c15aa595e`，base `3b3c4ac9…` | 未合入，历史 CI 不可复用 |
| ZIP Import | #267 MERGED `11b124679…`，#270 MERGED `d3b1d36e…` | 已合并，不应写成未实现；#261 完整验收仍 OPEN |
| Compiler v2.1.0 | request builder 已在 main；产品 adapter 仍固定 v2.0.2 | 不得声称产品切换完成 |
| Worker / VerifyDevelopment | #276 候选未合入；main Worker 无 buildDevelopment/verifyDevelopment | NOT_VERIFIED |
| Package Audit | 本地 audit 存在；v2.1.0 Development Build + Verify 权威门禁未切换 | NOT_VERIFIED |
| AI Gate | 旧 v2.0.2 精确候选 Check 存在；Development Build + Verify gate 未合入 | NOT_VERIFIED |
| sourceStatus provenance | 默认 Host Context Example 已显式保存 `DEVELOPMENT_FIXTURE`；普通 ZIP importer 并未全局添加 | PR 的“Host fixture provenance NOT_IMPLEMENTED”过宽且错误，见 P1-05 |
| no-root | request builder fail-closed；完整 UI/product 状态未证实 | 不得把构造器行为扩大为产品验收 |
| 双根 MAS Example | 双根声明存在；`mas=tool-catalog`、`ca-context=schema-bundle`，不是正式 interface-package | Build/Verify 仍被包类型阻塞，无双根 PASS |
| #295 相关修复 | #295 Issue OPEN；[#296](https://github.com/odango-chan/ca-skill-studio-demo/pull/296) 已 MERGED 到 main `73523df2f…` | OPEN 不等于修复未合入；应记录修复与剩余验收边界 |

关键源码证据：

- 默认 Example `files.json` 在 `ca-context.source` 中显式含 `sourceStatus=DEVELOPMENT_FIXTURE`：[`files.json#L192-L205`](https://github.com/odango-chan/ca-skill-studio-demo/blob/79bd2c3f64a90e7f0f169204c866a3218655bab1/site/samples/v1alpha5/files.json#L192-L205)。
- `prepareExampleHostContextDependency` 强制校验该字段并将完整 `source` 放入 lock：[`example-host-context-dependency.mjs#L10-L23`](https://github.com/odango-chan/ca-skill-studio-demo/blob/79bd2c3f64a90e7f0f169204c866a3218655bab1/experiments/ide-host/vscode/src/example-host-context-dependency.mjs#L10-L23)、[`L35-L42`](https://github.com/odango-chan/ca-skill-studio-demo/blob/79bd2c3f64a90e7f0f169204c866a3218655bab1/experiments/ide-host/vscode/src/example-host-context-dependency.mjs#L35-L42)。
- 普通 ZIP importer 仅保存 upload/contentDigest/packageId/version/publisher：[`dependency-integration.mjs#L330-L338`](https://github.com/odango-chan/ca-skill-studio-demo/blob/79bd2c3f64a90e7f0f169204c866a3218655bab1/experiments/ide-host/vscode/src/dependency-integration.mjs#L330-L338)。

## 7. 治理一致性审查结果

- **SR 权威文件统计正确**：27 项及 4/1/1/21 已由脚本重算。
- **汇总文档不一致**：实施状态表算术为 28；盘点 §6、实施关联段、若干审计快照仍保留旧 SR-003 状态。
- **Git tree 实测正确**：197 blobs / 157 Markdown；247 recursive entries 中 50 个 directory tree nodes。目录节点未计为文件。
- **追踪引用不一致**：错误 Studio SHA、旧 PR Head、PR #13 OPEN/CLOSED 冲突、PR #53/#54 混淆、多个版本指针未更新。
- **主干收敛计划已交叉核对**：PR #51 当前 Head `acb07bfbf7a01603b8ef86f8d3fc8785eb013196`，其《主干收敛计划》L147-L178 将 PR #54 限定为 Phase 1、仅进入 restore，再由 PR #44→#45→#46→#48 处理后续堆栈；PR #54 不应把后续 CA-SL 1.6.0 设计提前写成已发布。该计划本身仍为 DRAFT，不能当作合并授权。
- **整合保真性不足**：迁移审计四列表被覆盖为三列表，restore 的有效 Provider/CA-SL/Studio 约束被丢弃；多个同号修订记录碰撞或历史被回写。
- **静态门禁通过不代表治理通过**：Review Context SUCCESS 与 504 链接无断链均不能消除上述问题。

## 8. 独立验证结果

验证脚本：`validate_pr54.py`；完整机器结果：`validation-results.json`。脚本直接读取固定 Git 对象，不读取 PR 描述或旧验证报告。

| 检查 | 实际结果 |
|---|---|
| 16 文件 Markdown 解析 | 16/16 可由 `markdown-it-py 3.0.0` 解析；共 504 links |
| 本地文件链接 | 302 个本地链接，0 缺失路径 |
| 章节锚点 | 47 个可验证锚点，0 缺失 |
| 文档头 / 元数据 | **FAIL**：F02 两个冲突修订日期；两份文档头版本与最后修订不一致 |
| 版本与修订记录 | **FAIL**：依赖审计 0.2.12→最后 0.2.11；盘点 0.3.17→最后 0.3.18；另有修订碰撞 |
| Markdown 表格 | **FAIL**：迁移审计 4 行四列表被写成三列；盘点、F08、F09 历史修订表另有多行列数不一致 |
| SR 统计 | PASS：27；4/1/1/21，无重复漏项 |
| SR-025 固定源码探针 | **PASS**：59 文件、58 digest、25/7 operations、24/25 Capability、25 Evidence、53 Schema 闭包、127 exports、80,479 bytes；产品 AC 仍 NOT_RUN |
| 交叉引用语义 | **FAIL**：详见 P1/P2；路径存在不等于版本、SHA、状态正确 |
| Git tree | PASS：197 blobs / 50 trees / 247 entries / 157 Markdown |
| `git diff --check` | 31 处行尾空格；P3，不作为唯一阻断理由 |
| 本地 SR-001 回归 | **PASS：80/80**，Python 3.12.14，日志 `evidence/local-review-context-tests.txt` |
| 本地 Review Context 生成 | **PASS**：固定 Base/Head，16 文件，scope=UNCHANGED；日志 `evidence/local-review-context-generate.txt` |
| 当前 Head GitHub CI | PASS：Run #192～#195 均精确对应当前 Head；不代表本报告其他检查通过 |
| 独立静态总结果 | **FAIL：22 个结构/元数据错误（含同根重复计数）+ 1 个 whitespace warning** |

未执行项明确保持 NOT_RUN，不由 CI 或静态结果推断 PASS。

## 9. P0～P3 问题清单

### 9.1 P0

无。

### 9.2 P1（阻断 PR #54）

| ID | 文件与行号 | 问题、原则与实际影响 | 建议修复 | 阻断 |
|---|---|---|---|---|
| P1-01 | `docs/治理/实施状态总览.md:17,25` | DRAFT=22，而头部/权威 SR 为 21；22+1+0+1+4=28，与合计 27 冲突。违反状态统计唯一性，直接破坏治理可信度。 | 改为 DRAFT=21，并用脚本重算全表。 | 是 |
| P1-02 | `docs/治理/实施状态总览.md:92`；`docs/治理/现有文档盘点与收敛计划.md:75`；`docs/参考与审计/跨仓设计资产迁移与一致性审计.md:65` | 分别把 SR-003 写成“本地 PASS 未集成/Issue #28 OPEN”、3 VERIFIED/2 READY、Plugin Manager 未完成；与权威 SR-003、PR #34/#41/#42 和真实 CI 冲突。违反“不得用 refresh 旧状态覆盖 restore 权威状态”。 | 统一为 SR-003 模块 VERIFIED、4/1/1/21；Issue #28 CLOSED；历史状态只能放在明确历史段。 | 是 |
| P1-03 | `docs/架构设计/CA Agent Next 架构设计.md:245` | Studio 完整 SHA 写为 `79bd2c33615d…`，实际为 `79bd2c3f64a90e7f0f169204c866a3218655bab1`。错误的固定基线会使源码证据无法复核。 | 替换为实际完整 SHA，并重新核对所有派生链接。 | 是 |
| P1-04 | `docs/参考与审计/跨仓依赖与可行性审计.md:100`；`docs/参考与审计/跨仓设计资产迁移与一致性审计.md:133`；`docs/治理/功能树与需求追踪基线.md:168,202` | 多处仍把 #272 写成 OPEN/DRAFT，功能树还固定旧 main `5b666c0`；实际 #272 已 MERGED，当前 main 为 `79bd2c3f64…`。违反外部状态必须实查及“不得把候选当 main/把 main 当候选”的证据原则。 | 全部改为 #272 MERGED + merge `a863355…`，#276 才保持 OPEN/DRAFT/DIRTY；统一当前 main。 | 是 |
| P1-05 | `docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md:153,165`；`docs/治理/实施状态总览.md:66`；`docs/SR/SR-016-工作台设计移交与条件编辑.md:31` | 把 Host fixture provenance 概括为 NOT_IMPLEMENTED/当前 lock 未持久化，但当前 main 的默认 Host Context Example 已明确校验并保存 `sourceStatus=DEVELOPMENT_FIXTURE`。普通 ZIP importer 未全局添加是另一范围。错误状态会误导 SR-016 剩余实施与 AC 判定。 | 分开描述“默认 Host fixture provenance 已实现”与“普通 ZIP 全局策略/reload/双根 Development 验收仍未完成”；补 #296 与当前 main 证据，不扩大为完整 #269 PASS。 | 是 |

### 9.3 P2（必须列入修复清单；与 P1 一起阻止可靠整合）

| ID | 文件与行号 | 问题、原则与实际影响 | 建议修复 | 阻断 |
|---|---|---|---|---|
| P2-01 | `docs/参考与审计/跨仓设计资产迁移与一致性审计.md:29,31,36,37`；`docs/治理/现有文档盘点与收敛计划.md:139-143`；F08:127-130,134-135；F09:178-181 | 迁移审计四列表被三列表覆盖，restore 中完整 CA-SL 规范入口、Owner-linked 路径、artifactChannel fixtures/SHA256SUMS、Host-owned ToolCatalog 排除和 Studio 目录边界等有效内容丢失；其他修订表列数也不一致。违反整合不得丢弃有效内容与表格可解析性。 | 以 restore 四列为结构，融合 refresh 新状态并恢复有效约束；修正全部表格列数。 | 是（属于可靠整合缺口） |
| P2-02 | `docs/参考与审计/跨仓依赖与可行性审计.md:4,194`；`docs/治理/现有文档盘点与收敛计划.md:5,160`；F02:6,11 | 头版本与最后修订记录不一致；F02 同时存在 2026-11-27 和 2026-11-26 两个修订日期。违反版本治理规则。 | 依赖审计补 0.2.12 真实记录；盘点头部改 0.3.18；F02 只保留一个当前日期。 | 是 |
| P2-03 | IR:88；SR-016:11；SR-025:10；文档索引:55,120,158；功能树:131,154；迁移审计:29,36,66,72,73,260；Acceptance:142 | 多处设计/SR/审计版本指针落后于本轮实际文件（F09 0.3.10、F02 0.2.13、F08 0.3.9、SR-016 0.3.15、SR-025 0.1.8、迁移审计 0.4.36、Acceptance 0.3.18）。会导致实施者读取错误设计基线。 | 逐项同步版本；不要用全局替换改写明确历史记录。 | 是 |
| P2-04 | SR 总索引、功能树、实施状态、文档索引、迁移审计、Acceptance、SR-016、F09 的修订记录 | 两分支同版本号记录不同内容，Head 选择一方后丢失另一方；文档索引连续两个 0.4.31；若干净历史 `a863355` 被回写为 `79bd2c3`。违反“追加而非覆盖历史”。 | 保留双方原始条目和来源，给整合新增唯一递增版本；不得回写来源分支历史。 | 是 |
| P2-05 | 总体架构:246,253；实施状态:33；迁移审计:257；依赖审计:175；功能树:122 | 当前段仍固定 restore `32c7c1b` 和旧 PR Head `52f0fa32`，未保留 restore 后续 `34e99e0`、最终 Head `e8bcb1b`、PR #41/#42 与同 tree 证据。 | 更新当前基线；旧值只保留在明确历史段；区分 PR Head CI 与 merge SHA post-merge NOT_RUN。 | 是 |
| P2-06 | SR 总索引:97；实施状态:34,90；Acceptance:214 | PR #13 同时被写成 OPEN 和 CLOSED；Acceptance 把 Issue #53 错当整合 PR #53，实际整合 PR 为 #54。破坏追踪闭环。 | PR #13 单列为 CLOSED/superseded；Acceptance 改 PR #54 并核对链接。 | 是 |
| P2-07 | F09:147 | “merge/main SHA `79bd2c3…`”混合两个身份；#272 merge 实际为 `a863355…`，当前 main 才是 `79bd2c3…`。 | 分列 merge SHA 与当前 main SHA。 | 否（随 P1-04 一并修复） |
| P2-08 | 依赖审计:31；文档索引:43,65 | 当前表仍写 23 SR/150 Markdown/47 formal，与实际 27/157/48 冲突；文档索引本节 13 与 14 份设计冲突。 | 按 Git tree 和目录分类重算并统一。 | 否（随 P1/P2 统计修复一并处理） |
| P2-09 | `docs/SR/SR-025-MAS Owner Interface Package Publisher.md:76`；对照 PR #45 `docs/SR/SR-029…md:18-20,95-100` | 当前 READY SR 把 Issue #40 的未来作者模型命名为“v1alpha6 Capability-first”；后续总体方向和 SR-029 明确为 CA-SL 1.6.0，且准确机器标识待 ca-skills/Compiler 正式冻结、禁止提前猜测。该命名会把未冻结的未来契约误写成已确定标识。 | 改为“CA-SL 1.6.0 Capability-first（NOT_RELEASED；准确 languageTarget 待正式冻结）”，保持本 SR 的 v1alpha5 包不变。 | 是（属于权威 SR 交叉设计不一致） |

### 9.4 P3

| ID | 文件与行号 | 问题与影响 | 建议修复 | 阻断 |
|---|---|---|---|---|
| P3-01 | 外部能力域总览:67；F09:141 | 当前快照日期未随 11-27 内容更新。 | 同步快照日期或明确历史日期。 | 否 |
| P3-02 | SR-025、F02、F08 的头部与最后修订行 | 相对 refresh 主要只有版本/日期/修订行变化，却声明修改正文/重复已有修复，属于记录范围名实不符。 | 无实质正文变化时如实记录“恢复纳入与元数据同步”，不要重复声称正文修改。 | 否 |
| P3-03 | SR-016:11、SR-025:10 | 设计依据 metadata 行前多一个空格，格式不一致。 | 统一为标准 blockquote 头。 | 否 |
| P3-04 | Base→Head 全差异 | `git diff --check` 报告 31 处行尾空格。 | 清理非 intentional Markdown hard-break；若确需双空格换行，统一规范并避免无意义尾随空格。 | 否 |

## 10. 最终评审结论与文件级修复清单

### REQUEST_CHANGES

**PR #54 当前不能安全合入 `docs/restore-original-designs-20261125`。** 虽然 16 文件范围、核心架构、权威 SR 状态、SR-003/SR-025 关键证据、链接和当前 Head Review Context 均有可取之处，但 P1 状态错误、错误 SHA、SR 统计算术错误、外部实现状态误判，以及 P2 的有效内容覆盖和修订链破坏，使整合结果尚不可靠。

必须至少完成以下文件级修复并重新独立评审：

1. `docs/治理/实施状态总览.md`：修 DRAFT 算术、SR-003、sourceStatus、restore SHA、PR #13。
2. `docs/治理/现有文档盘点与收敛计划.md`：修 §6 统计、头版本和修订表；澄清 16/19 比较口径及三份排除项。
3. `docs/架构设计/CA Agent Next 架构设计.md`：修 Studio 完整 SHA 与当前 restore/PR Head。
4. `docs/参考与审计/跨仓依赖与可行性审计.md`：修 #272、统计、0.2.12 修订记录及 SR-003 当前快照。
5. `docs/参考与审计/跨仓设计资产迁移与一致性审计.md`：恢复四列表与 restore 有效内容，修 #272、Plugin Manager、版本和修订链。
6. `docs/设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md`：按默认 fixture/普通 ZIP/剩余验收三个范围重写 provenance，拆分 #272 merge/main。
7. `docs/SR/SR-016-工作台设计移交与条件编辑.md`：同步 F09 版本，准确界定已实现 provenance 与剩余 AC，不回写历史。
8. `docs/治理/功能树与需求追踪基线.md`：修 #272、Studio main、SR-003 Head、F09 版本和修订链。
9. `docs/治理/文档总目录与索引.md`、`docs/IR/IR 总登记册.md`、`docs/SR/SR-025-MAS Owner Interface Package Publisher.md`：同步版本指针，修目录计数和修订历史；SR-025 L76 改用 CA-SL 1.6.0 / NOT_RELEASED / 机器标识待冻结的准确边界，不猜测 v1alpha6。
10. `docs/治理/SR 总索引.md`、`docs/验收与实施/演示验收基线.md`：修 PR #13/#54、Acceptance 自版本与双方修订历史。
11. `docs/设计说明书/F02-Skill管理与选择/Skill管理与选择设计说明书.md`、`docs/设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md`、`docs/架构设计/外部能力域架构总览.md`：修重复日期、修订表、快照日期及名实不符记录。
12. 修复后重跑本报告全部静态检查、SR 统计、外部状态核验和新 Head 的 Review Context；不得复用 `7452f60` 的 CI 作为新 Head 通过证据。

## 11. GitHub Review 留痕链接

- 独立评审分支：[`review/issue-53-independent-20261127`](https://github.com/odango-chan/ca-agent-next/tree/review/issue-53-independent-20261127)。
- 首次完整报告提交：[`83c5ca2f9250ac80af54818f1dc0252c3e0be260`](https://github.com/odango-chan/ca-agent-next/commit/83c5ca2f9250ac80af54818f1dc0252c3e0be260)。
- PR #54 Review：[Review #6083215845](https://github.com/odango-chan/ca-agent-next/pull/54#pullrequestreview-6083215845)，状态 `COMMENTED`，绑定 Head `7452f60ccbc68e1468b52018f59bdc2347cc32d5`。
- Issue #53 更新：[Issue Comment #7209304348](https://github.com/odango-chan/ca-agent-next/issues/53#issuecomment-7209304348)。
- 本报告的最终提交 SHA 以独立评审分支当前 HEAD 为准；首次报告链接固定在 `83c5ca2`，不会随追加留痕而失效。

## 12. 未完成事项及其影响

| 项目 | 状态 | 影响 |
|---|---|---|
| SR-003 Linux/Windows 本地重跑 | NOT_RUN（本轮核对真实 GitHub 原始 Job/日志，而非本地重跑） | 不影响对既有 CI 真实性的判断；不得声称本轮本地双平台 PASS |
| 外部 Studio/Compiler/Publisher 产品测试 | NOT_RUN | 仅核对 GitHub 状态与固定源码；完整产品 Acceptance 仍 NOT_VERIFIED |
| 外部 HTTP URL 全量实时可达性 | NOT_RUN | 本地 Git 路径与 47 锚点已验证；不推断所有外部 URL 长期有效 |
| DeepSeek Harness 自动消费 Review Context Artifact | NOT_RUN | 本地生成与 GitHub Artifact 存在已验证，不声称外部自动消费 |
| CA-SL 1.6.0 正式规范与准确 languageTarget | NOT_RELEASED / 待正式冻结 | 已核对 PR #45 SR-029 的未来设计方向；不得把 1.6.0 或 v1alpha6 写成当前已发布契约 |
| #261/#269/#279/#290/#295 完整验收 | NOT_VERIFIED | OPEN Issue、局部 merged 能力和完整产品验收必须分开 |
| 本评审之后的新 Head | NOT_RUN | 修复一旦推送，必须重新固定 Base/Head/CI 并复审 |
