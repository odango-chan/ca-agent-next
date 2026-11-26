# SR-025：MAS Owner 1.6.0 Capability-first Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.1.11
> 状态：DRAFT（SR 实施主状态）；**设计待评审 / REVIEW_REQUESTED**；不授予实施 READY，产品验收原状态不变；PR #46 首轮 CHANGES_REQUESTED，修订待复评  
> 创建日期：2026-11-25
> 修订日期：2026-11-27  
> 所属阶段：外部 Publisher 实施移交
> 上游需求：[IR-006](../IR/IR%20总登记册.md#ir-006)
> 功能：F03.05 / EC03（消费方关联 F09.07）
> 设计依据：[F03.05 Tool Interface / Provider 设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) v0.4.3；[F09 新版 1.6.0 设计 §5～§9](../设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md) v0.3.15；[SR-015](SR-015-工具契约设计移交.md)；[EC02 新 1.6.0 Compiler 设计](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.13 与 [SR-013](SR-013-Compiler已检查when与发布产物.md)；历史 Compiler v2.1.0 Development BuildRequest 仅供审计
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：Provider v2 重构、Host Runtime Binding 重构、生产级 Trust/Admission/签名或额外包完整性体系；历史 v1alpha4/v1alpha5 Development Bundle 仅供源审计

## 0. 本轮设计评审入口（2026-11-26）

本 SR 已提交 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计审查；**主状态 `DRAFT` 与设计 `REVIEW_REQUESTED` 独立，实施 READY/产品 PASS 均未获得**。新语言架构见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 和 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮审查重点：**核查 MAS Owner 发布者、Schema/Evidence/Callable 导出闭包、正式包可复现性及 Compiler Link 输入。
- **未发布/未证据项：**原方案针对 v1alpha4 Owner source / Compiler v2.1.0 Development Package；新 CA-SL 1.6.0 的公开 Capability↔Callable 一对一及新版 Bundle 必须重新发布，不能沿用旧 Bundle 作新正例。
- **统一目标：**CA-SL **1.6.0 ONLY**；Skill-facing 只有 Capability ID，公开 Capability↔Callable 严格双向一对一；旧语言、Compiler DTO、Artifact、Bundle、别名、fallback 与迁移兼容均禁止。旧源 Schema/fixture/发布身份只用于只读历史审计；新机器契约由发布者冻结，不得自行猜测。
- **评审退出：**逐项核查范围/非目标、外部契约、失败语义和 AC；外部新合同未发布为 `BLOCKED`、产品未运行为 `NOT_RUN`。在独立评审通过前不得向 Harness 交付实施提示词。

## 1. 目标仓与基线

- 目标仓：`odango-chan/ca-client-tools`，目标分支 `main`，审计基线 `7bcb2614aa3615d8358df31eecefd0909e894e40`。
- Owner source：`contracts/owner/openamsm-mas/v1alpha4`；source tag `v1.2.0` 对应 Revision `fc44c3a745c68443fcfb12054c7eadf0ed7cc3f7`；source buildIdentity `sha256:ac834080f31ff0fa91b9eb846fa47c889a94837fc1f37ec2034190e4e83085c0`。
- 当前 main 与 v1.2.0 tag 的 Owner source 目录 59 个文件（manifest + 58 artifacts）逐个 blob 相同。
- 当前 `manifest.json` 的 `operations` 有 25 个已发布 contracts，`notPublished` 另列 7 个旧 Callable；这与 Provider 内部 Catalog 的 8 个 legacy typed callables 是两套不同清单。

## 2. 目标与规范契约

本 SR **仅定义新 CA-SL 1.6.0 MAS Owner Interface Package Publisher**，目标仓仍为 `odango-chan/ca-client-tools`，由 Owner `env-openamsm` 冻结其权威 Skill-facing Capability contracts 与新发布来源；Compiler 正式 Bundle/Runtime Artifact 由 SR-013/027 分别负责。本 SR 不在 Next 或 Studio 本地转换旧 Package。

### 2.1 新发布契约（需 Owner/Compiler 正式冻结）

- 唯一语言目标 **CA-SL 1.6.0**；准确 `languageTarget`、Interface Package `apiVersion`、Schema/文件名、Publisher package `version` 和 Builder CLI 由 ca-skills / Compiler / Owner 发布，不得假定旧 `connectionagent.io/v1alpha5`、`interface-package/v1alpha1`、旧 `1.0.0` 仍合法。
- 目标 Owner **24 个 Skill-facing Capability ↔ 24 个公开 Callable**，严格双向一对一；**25 个 Owner ToolCatalog contracts** 保持原业务语义，其中 `MAS.RECONCILE` 是 Runtime Coordinator internal-only target，不属于 Skill-facing Capability。详见 [SR-029 §3/§6](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md)。
- 原 `mas.se.events.emit` 一对二（`SE.EMIT_EVENTS`、`SE.EMIT_RELEASE_EVENT_C`）必须拆为 `mas.se.establishment-event.record` 和 `mas.se.release-event-marker.write`：Input Schema、Effect、Evidence Guarantee 分开保留，不能伪合并为一种动态 Callable。
- `MAS.RECEIPT_QUERY` 是可对 Skill 授权的 READ Capability/Callable；`MAS.RECONCILE` 虽保留 Owner ToolCatalog/Runtime Bindings，但任何普通 Skill/LLM/Studio 补全不得将其当作公开 Capability。所有公开 Callable 都应恰好有一个 Capability，只有 Reconcile 这类明确 internal-only callable 被排除于公开双射。
- Owner 权威发布应明确每个 Capability 的全局 ID、唯一 Callable ID、kind、Effect、输入/输出 Schema、Evidence / Receipt/Commit Proof 描述和 Owner identity。Publisher 只验证并输出 Owner 已冻结的事实；不能由 ca-client-tools 根据旧数组猜测新 Identity/Schema、生成新业务语义或改变 Owner guarantee。
- 不引入生产 Trust Registry/Admission/签名，也不依赖额外包级 SHA-256 机制；若正式新版 Package Schema 自身规定逐文件完整性字段，则只依其 schema，不在 Next 发明新字段。

### 2.2 当前历史输入（仅审计，不满足新发布条件）

Owner `v1alpha4` source 的 `tool-catalog.yaml` 含 25 published contracts、旧 CapabilityContracts 为 24 IDs / 25 memberships；其 `manifest.json` 源 Revision、buildIdentity、53 Schema/25 Evidence 等统计只用来做**新旧语义差异核对**。Compiler v2.1.0 Development v1alpha1 的 `package.json`、`tool-catalog.yaml`、`capability-catalog.yaml`、`1.0.0`、`BuildDevelopment`/`VerifyDevelopment`、旧 bundle digest 属冻结历史，不是本 SR 1.6.0 Publisher 的正式输出或正例。

## 3. Owner/Publisher 交接与实现责任

1. **Owner（env-openamsm）发布输入：**冻结 24/24 mapping、事件拆分的两个 Schema/Evidence identity、Receipt Query READ、Reconcile internal-only binding 及包来源身份；登记源仓 PR/SHA/正式契约版本。Owner 的业务语义与权威 Evidence 不允许由 Publisher 改写。
2. **ca-client-tools Publisher 校验：**精确读取 Owner 正式输入，验证 24/24 双向一对一、无空/双成员、无重复 Callable、与 ToolCatalog export 一致；公开 Capability 不包含 Reconcile；Schema 所需 $ref 全部可解析，Effect/kind/Evidence identity 与 Owner 一致。输入不符必须拒绝整个发布候选，不能自动补一项或删字段继续发布。
3. **输出：**按 Compiler Owner 正式冻结的 1.6.0 Interface Package Schema 打包，仅包含声明允许导出的 Package identity、Capability/Callable/Schema/Evidence 和闭包，复用既有统一发布流水线；**Package 不能由 Studio 包装或转换**，不输出 Owner Trust/Runtime 权限。版本与机器标识以批准的 Publisher release record 为准。
4. **消费：**Compiler 基于该 Package + Skill 显式依赖做 Capability→唯一 Callable 链接，并产出 1.6.0 Runtime Artifact；Skill Studio 通过新 ZIP Import/Lock 原样导入（SR-016）；Agent 只消费已发布 Bundle，不调用 Compiler。
5. **失败原子性：**任何 Schema 失效、发布输入身份不匹配、旧 languageTarget、重复 membership 或不兼容 Parser 均不产出可发布 Bundle。Publisher 的 Release 必须明确记录源 SHA、Compiler tag/API、Package version、目标资产和 Verify 证据；发布授权仍独立。

## 4. 依赖分类与停机条件

| 类别 | 依赖 | 阶段门禁 |
|---|---|---|
| 设计 | SR-029 Capability↔Callable 与本 SR 的包发布职责/验收 | 可先独立评审，不要求产品已有 Release |
| 实施 | env-openamsm 新 24/24 Owner 规范；ca-skills 正式 1.6.0；Compiler 的新 Package/Link DTO | 真实 Publisher 实施时必须固定发布证据；否则 BLOCKED |
| 模块验收 | 目标仓一份合法的 1.6.0 Package 候选和负例、对应新 Compiler 验证器 | 仅在完成该 AC 时依赖，不能拿旧 v2.1.0 BuildDevelopment 冒充 |
| 系统集成 | SR-016 Studio MAS Example / Next E2E | 不作为本 Publisher 模块设计 READY 前置 |

如 Owner 不批准原 Capability 拆分、或拒绝排除 internal-only Reconcile，返回 SR-029 修改设计并重新独立评审，**不得自行对外发布一个“近似一对一”的包**。若新版 CLI/Schema 尚未发布，可准备测试矩阵与源差异审计，但不得发布资产或报告 AC PASS。

## 5. AC-025-01～08（新 1.6.0 独立验收）

| AC | 正/负输入与操作 | 预期 |
|---|---|---|
| AC-025-01 | 固定 Owner 新发布源 SHA、24/24 mapping、25 ToolCatalog/历史差异 | 有可复核 Owner 权威来源；历史 24/25 仅审计 |
| AC-025-02 | 合法 1.6.0 Package ID/版本/Publisher/languageTarget 与旧 v1alpha5 / v1alpha1 反例 | 仅正式新 Schema 验证通过；旧/未知版本拒绝 |
| AC-025-03 | Schema/Evidence/Callable 闭包、引用完整性；缺 $ref、重复导出 | 合法闭包通过，丢失/重复任何成员 fail-closed |
| AC-025-04 | 24/24 双向一对一；旧一对二 mas.se.events.emit、重复 Callable、Reconcile Skill-facing 反例 | 全部异常拒绝，正确拆分 + internal-only 保留 |
| AC-025-05 | 两个不同 Event Schema/Guarantee、Receipt Query/Receipt Proof、Reconcile 原始 invocation | 两种事件不能互换；READ 与内部 Reconcile 不混用 |
| AC-025-06 | 同一 Owner 输入重复构建 + 来源包缺失或损坏 | 输出稳定可重验；失败零部分可发布资产 |
| AC-025-07 | **正式新 1.6.0** Compiler Schema/Build/Verify 使用一个 Capability-first MAS synthetic Skill | 通过**唯一新 1.6.0 Compiler** 的正式 Check/Build/Verify 接口；历史 `build-development` / `verify-development` 不能算 PASS；记录精确命令、结果与诊断 |
| AC-025-08 | ca-client-tools 正式流水线发布、下载并复核新 Package | 记录授权 Release、资产路径、Owner SHA、Compiler API/tag、包版本、Verify 输出；无产品发布授权不得宣称通过 |

未冻结的准确字段/CLI/Schema 名称由目标 Owner 通过独立 Issue/PR 明确，不由 DeepSeek Harness 猜测。系统 EX/MAS E2E 和运行时 Owner Outcome 不在本模块 AC 之内。

## 6. 实施关联

| 项目 | 状态 |
|---|---|
| 目标仓 | `odango-chan/ca-client-tools` |
| 设计 Issue | [Next #12](https://github.com/odango-chan/ca-agent-next/issues/12)、[Next #40](https://github.com/odango-chan/ca-agent-next/issues/40) |
| 新 Owner 1.6.0 发布与 Package 机器 Schema | NOT_RELEASED；实施入口需在本 SR 独立批准后创建 |
| 实施 Issue / PR / Commit | NOT_CREATED / NOT_RUN |
| 验收 | AC-025-01～08 全部 NOT_RUN / 依赖正式发布部分 BLOCKED |

本 SR 的新规范性 §2～§6 已替换历史 v1alpha5 Development Publisher 方案。历史源输入可作为审计证据，不再构成新版本合法构建/消费路径；待正式设计评审通过、分类型依赖和对应 Publisher/Compiler 发布获得授权后，才提供针对可执行阶段的 Harness Goal。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | §1～6 | 新增 ca-client-tools MAS Owner Development Interface Package Publisher 独立实施 SR；固定 Owner source、25/24/25/53 exports、127 exports、56 payload files、Compiler Build/Verify gate 和 Release 集成；记录 SemVer 映射待用户确认。 | IR-006 · F03.05 · F09 · SR-015 · SR-016 · SR-024 · Issue #12 |

| 2026-11-25 | 0.1.1 | GPT-6.2（ChatGPT） | §2～7 | 补齐 AC-025-01～08，明确 package.version SemVer 决策门槛、导出闭包、负向测试和既有 Release 流程 ；让 ca-client-tools Publisher 达到可评审、可执行的 SR 粒度；不在决策确认前生成实施提示词 | Issue #12；F03.05；F09；SR-015、SR-016、SR-024 |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | 正文 | §2、4～6 固定 MAS 包身份，解除 Publisher 对下游 Studio 的循环前置 | Issue #12 SR-025 |
| 2026-11-25 | 0.1.3 | Codex / GPT-6 | 正文 | §6 明确发布者独立验收输入；同步所引权威设计版本；清理重复基线指针 | Issue #12 SR-025 |
| 2026-11-25 | 0.1.4 | Codex / GPT-6 | 正文 | AC-025-07 固定 v2.1.0 真实 CLI 和复验输入；同步本轮受影响的现行设计依据 | Issue #12 SR-025 |
| 2026-11-26 | 0.1.5 | Codex / GPT-6 | 见本行变更 | 同步设计依据到本次复审的修订版本 | Issue #12 |
| 2026-11-26 | 0.1.6 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 提交设计待评审、明确新旧契约/验收隔离并保留 DRAFT 主状态 | Issue #12；PR #45；SR-029 |
| 2026-11-26 | 0.1.7 | GPT-6（ChatGPT） | 目标合同、实施 AC 和旧版留档 | 原旧 v1alpha5 Development Publisher 实施与验收全部替换为 1.6.0 Owner 24/24 能力映射、验收及分类型依赖 | Issue #12/#40；SR-016/025/029；PR #46 |

| 2026-11-26 | 0.1.8 | GPT-6（ChatGPT） | 设计依据与新版本路径 | 刷新 1.6.0 正式目标设计引用：v0.4.0→v0.4.1、v0.3.10→v0.3.11、历史 F09 §4.5→新 §5-9 | Issue #12/#40；PR #46 |
| 2026-11-26 | 0.1.9 | GPT-6（ChatGPT） | 文档头与 1.6.0 当前设计依据 | 修复 PR #46 Review Context 文档头检查及旧 Development Build 设计依据，更新新 Compiler/SR-013 正式入口 | Issue #12/#40；PR #46；CI #45837224652 |

| 2026-11-26 | 0.1.10 | GPT-6（ChatGPT） | 最终一致性复评 / 规范性描述 | AC-025-07 明确唯一新 1.6.0 Compiler，不混用 Development profile | Issue #12/#40；PR #46 |
| 2026-11-27 | 0.1.11 | Codex / GPT-6 | 文档头 | 统一中央权威文档的相对路径与版本 | Issue #12，PR #46 |
