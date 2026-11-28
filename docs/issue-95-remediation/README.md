# Issue #95 后续整改总览

> 文档性质：后续整改追踪，不覆盖、不改写 Issue #95 固定源静态审计证据。
> 固定 Next 审计输入：`93f1389e7c5968cd30e8a74137207094864ecca0`
> 审计移交 PR #98 Head：`2b430c81c66728c4328dec64dfdc3c0438ead43a`
> 目录树修正提交：`67c5ade947f7f69c4c4411033b60f846e80dc732`，已包含在 PR #98 Head 历史中。
> 总追踪：[Issue #95](https://github.com/odango-chan/ca-agent-next/issues/95)；本轮中央文档收敛：[Issue #106](https://github.com/odango-chan/ca-agent-next/issues/106)。

## 1. 处理原则

1. Issue #95 的固定源、原始 SHA、逐 AC 状态和 FAIL/BLOCKED/NOT_RUN 结论作为不可变审计记录保留。
2. 既有设计评审的 `APPROVE_FOR_READY` 只表示限定设计范围获批，不代表固定源码、候选包、产品实现或运行验收通过。
3. 外部仓在本轮保持只读；实现任务只登记到中央 Issue，由后续获授权任务在目标仓实施。
4. 不推测尚未发布的 CA-SL 1.6.0 Package Schema、languageTarget、SemVer、BuildRequest、DependencyInspection、Bundle 或 API。
5. 不改变任何父级 SR 主状态；每个 AC 只在其对应证据完整、复验通过后更新。

## 2. 整改任务矩阵

| SR / AC | 当前审计结论 | 具体整改 | 追踪 |
|---|---|---|---|
| SR-013 / AC-013-01 | **PASS（归档完整性/历史 PoC 独立复验）**；`vet.log` 仍 NOT_ARCHIVED | PR #110 修复的完整 59 Blob 归档树（58 个清单覆盖文件 + SHA256SUMS）已在专用证据分支独立 detached checkout 复验：58/58、SHA256SUMS、audit_evidence.py、Python 18/18；不代表 Compiler 产品验收 | [#102](https://github.com/odango-chan/ca-agent-next/issues/102)；[PR #110](https://github.com/odango-chan/ca-agent-next/pull/110) |
| SR-017 / AC-017-02 | **FAIL**（候选设计/契约缺项） | 补 payload.request、operationId、Update 可选 n2.request、三类 N2 continuation、同请求双路、冲突/未知/Content-ID/n2SmInfoExt1 负例；清除 ack 暴露 Host Run/responseObligation/artifactRef 的旧句 | [#103](https://github.com/odango-chan/ca-agent-next/issues/103) |
| SR-018 / AC-018-01/02 | **FAIL**（固定 Owner source/step、Evidence、Schema、exact-original Reconcile） | 校准 source/step；修复 Evidence 参数引用；所有 resolved decision 满足 Schema；Reconcile 必须以原 Receipt/Invocation 身份重新绑定 generation/epoch/correlation/SEID/releaseTxn/UPF，不得按当前 SUPI/PSI Session 解除旧 UNKNOWN | [#104](https://github.com/odango-chan/ca-agent-next/issues/104) |
| SR-019 / AC-019-02 | **FAIL**（联合 fixture 缺项） | 补同请求 N1+N2 双路、X-CA-Request-Id 重试、旧 generation 迟到 0xD4、冲突 discriminator/n2SmInfoExt1 和 Owner outcome 联合证据；Mock 不拥有 Host Run/Owner 状态 | [#105](https://github.com/odango-chan/ca-agent-next/issues/105) |
| SR-016 / AC-016-01 | **NOT_RUN**（Issue #95 固定源缺独立定义；现行 SR-016 v0.3.41 已补正式 AC） | 保留历史缺项记录；现行 AC-016-01 与 MIG-016-01 已分离，验收尚未执行，不能沿用 MIG 的静态 PASS | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-016 / AC-016-02～08/10 | **BLOCKED / NOT_RUN** | 等正式 1.6.0 Package、Compiler、Provider/Owner 输入和同一发布批次六宿主证据；#272 合并不等于新版产品 PASS | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-030 / AC-030-02/03/05 | **BLOCKED** | 等正式 Package Schema、languageTarget、Compiler 验证入口和 Golden；不猜测机器契约 | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-030 / AC-030-04 | **NOT_RUN** | 中央设计补充 ZIP 元数据归一、entry/Manifest 稳定排序、两次构建逐字节比较和正式 Schema 校验判据 | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |

## 3. 既有设计评审与后续静态审计的关系

| 评审 Issue | 既有设计结论 | Issue #95 后续核验 | 后续动作 |
|---|---|---|---|
| [SR-013 #77](https://github.com/odango-chan/ca-agent-next/issues/77) | 设计 APPROVE_FOR_READY（限定） | Issue #95 固定快照曾发现归档 FAIL；Issue #102 / PR #110 后续修复并独立复验归档完整性 PASS，`vet.log` 仍未归档；设计认可不代表 Compiler 产品验收 | #102；PR #110 |
| [SR-016 #78](https://github.com/odango-chan/ca-agent-next/issues/78) | 设计 APPROVE_FOR_READY（限定） | 固定源时 AC-016-01 定义/编号映射冲突；现行正式 AC 已独立定义但仍 NOT_RUN，六宿主仍 NOT_RUN | #106 |
| [SR-017 #79](https://github.com/odango-chan/ca-agent-next/issues/79) | 静态设计 APPROVE_FOR_READY（限定） | 固定候选缺现行 F06 payload/continuation/负例，AC-017-02 FAIL | #103 |
| [SR-018 #80](https://github.com/odango-chan/ca-agent-next/issues/80) | 历史 Owner 静态移交 APPROVE_FOR_READY（限定） | 固定源码发现 source/step、Evidence、Reconcile 缺陷，AC-018-01/02 FAIL | #104 |
| [SR-019 #81](https://github.com/odango-chan/ca-agent-next/issues/81) | Mock peer 静态设计 APPROVE_FOR_READY（限定） | 联合 fixture 不完整，AC-019-02 FAIL；AC-019-03 NOT_RUN | #105 |
| [SR-030 #91](https://github.com/odango-chan/ca-agent-next/issues/91) | Schema-only 设计 APPROVE_FOR_READY（限定） | AC-030-01/06/07 静态 PASS；02/03/05 BLOCKED；04 NOT_RUN | #106 |

这些不是互相覆盖的评审：设计结论保持其原始快照含义；后续固定源审计新增的是实现/归档/fixture 层证据。两者均保留。

## 4. 当前仍必须保持的状态

- SR-013 AC-013-01：固定归档完整性及历史 PoC 独立复验 PASS（58/58、SHA256SUMS、audit_evidence.py、Python 18/18）；`vet.log` NOT_ARCHIVED / NOT_INDEPENDENTLY_VERIFIABLE；Compiler 产品 AC 仍 NOT_RUN。
- SR-013 AC-013-02/04：NOT_RUN；AC-013-03/05/06：BLOCKED。
- SR-016 AC-016-01：现行正式 AC 已定义并与历史 MIG-016-01 分离，但新 AC **NOT_RUN**、不能判 PASS；Issue #95 固定源的定义缺失结论保留为历史时点；六宿主全部 NOT_RUN。
- SR-017 AC-017-02：FAIL；运行验收 NOT_RUN。
- SR-018 AC-018-01/02：固定 main FAIL；AC-018-03 BLOCKED；AC-018-04 静态 PASS；历史 Owner / 隔离 UE-requested Release E2E 限定 PASS；当前候选 Reconcile、Network-requested ReleaseSMContext、Next E2E 均 NOT_RUN。
- SR-019 AC-019-02：FAIL；AC-019-03 NOT_RUN。
- SR-030 AC-030-02/03/05：BLOCKED；AC-030-04 NOT_RUN；静态 PASS 只限 AC-030-01/06/07。

## 5. 执行顺序

1. #102：归档修复与独立 detached checkout 复验已完成；PR #110 已合入专用证据分支 `docs/ac-013-01-poc-evidence` @ `39ccb00be8d14f7f1be7b02061454e9b927471b8`；本次 PR #115 选择性纳入完整 59 Blob 归档树。Compiler 产品验收仍 NOT_RUN。
2. #106：修复中央 SR/AC 编号、固定路径、职责和确定性验收判据。
3. #104：优先修复 Owner exact-original Reconcile 与 Evidence 闭包，避免跨代错误解除 UNKNOWN。
4. #103：按固定 F06/3GPP OpenAPI 补齐 Plugin Event payload 与 continuation 契约。
5. #105：补齐 Mock AMF 联合 fixture；与 #103 使用同一 F06 语义，不让 Mock 自行定义 Host/Owner 身份。

上述顺序不代表可绕过目标仓授权或外部正式契约；所有实施任务须先核对其固定源和当前 Head。

## 6. 非目标

- 不修改 ca-openamsm-plugin、env-openamsm、env-5gc-sim、ca-skill-compiler 等外部仓。
- 不把历史 PoC、旧 CI、旧 Studio PR 或 Mock 通过记录升级为 1.6.0 产品证据。
- 本文件仅跟踪整改；不据本次文档更新推定 PR #98/本整改 PR 已合并、产品已发布或父级 SR 主状态改变。

## 7. 修订记录

| 日期 | 修订者/模型 | 章节 | 修改及原因 | 关联 |
|---|---|---|---|---|
| 2026-11-28 | GPT-6（ChatGPT） | §2、§3、§4、§6 | 分离 Issue #95 历史缺定义与现行 SR-016 正式 AC 已定义但 NOT_RUN；避免将历史固定源缺陷误写为当前状态 | Issue #106；PR #107；SR-016 |
| 2026-11-28 | GPT-6.2（ChatGPT） | §2、§4～§6 | 回填 PR #110 后续归档独立复验 PASS、SR-018 历史 UE-requested Release 限定 PASS，并同步 SR-016 当前 AC-016-01 正式定义版本；保留 vet.log 未归档及产品 NOT_RUN 边界 | Issue #102/#104/#106；PR #107/#110/#114/#115 |
| 2026-11-28 | GPT-6.2（ChatGPT） | §2、§4～§6 | 补记 PR #115 已按固定 Blob SHA 纳入完整 59 Blob 归档树（58 个清单覆盖文件 + SHA256SUMS），不再将五份修复元数据误写为完整归档 | Issue #102；PR #110；PR #115 |
| 2026-11-28 | GPT-6.2（ChatGPT） | §2、修订记录 | 同步 SR-016 当前版本 v0.3.41；维持 AC-016-01 新定义 NOT_RUN 与历史固定源缺项结论的时点隔离 | Issue #106；PR #107/#115 |
