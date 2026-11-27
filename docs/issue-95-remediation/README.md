# Issue #95 后续整改总览

> 文档性质：后续整改追踪，不覆盖、不改写 Issue #95 固定源静态审计证据。
> 固定 Next 审计输入：`93f1389e7c5968cd30e8a74137207094864ecca0`
> 审计移交 PR #98 Head：`2b430c81c66728c4328dec64dfdc3c0438ead43a`
> 目录树修正提交：`67c5ade947f7f69c4c4411033b60f846e80dc732`，已包含在 PR #98 Head 历史中。
> 总追踪：[Issue #95](https://github.com/odango-chan/ca-agent-next/issues/95)；本轮中央文档收敛：[Issue #106](https://github.com/odango-chan/ca-agent-next/issues/106)。

## 1. 处理原则

1. Issue #95 的固定源、原始 SHA、逐 AC 状态和 FAIL/BLOCKED/NOT_RUN 结论作为不可变审计记录保留。
2. 既有设计评审的 `APPROVE_FOR_READY` 只表示限定设计范围获批，不代表固定源码、候选包、产品实现或运行验收通过。
3. 外部仓源代码在本轮中央整改中保持只读；可以按仓库边界在目标仓创建独立实施/测试 Issue。实际代码、生成器、构建和运行测试必须在目标仓 Issue/PR 执行；Next 只维护设计、跨仓映射和证据状态。
4. 不推测尚未发布的 CA-SL 1.6.0 Package Schema、languageTarget、SemVer、BuildRequest、DependencyInspection、Bundle 或 API。
5. 不改变任何父级 SR 主状态；每个 AC 只在其对应证据完整、复验通过后更新。

## 2. 整改任务矩阵

| SR / AC | 当前审计结论 | 具体整改 | 追踪 |
|---|---|---|---|
| SR-013 / AC-013-01 | **FAIL**（历史 PoC 18/18 保留；归档完整性未闭合） | 修正 `audit.json` 的 py-results 登记；将 SHA256SUMS 改为归档相对路径；vet.log 只能补真实日志，否则明确标记未归档/不可复核；干净 checkout 复验 | [#102](https://github.com/odango-chan/ca-agent-next/issues/102) |
| SR-017 / AC-017-02 | **FAIL**（候选设计/契约缺项） | 补 payload.request、operationId、Update 可选 n2.request、三类 N2 continuation、同请求双路、冲突/未知/Content-ID/n2SmInfoExt1 负例；清除 ack 暴露 Host Run/responseObligation/artifactRef 的旧句 | [#103](https://github.com/odango-chan/ca-agent-next/issues/103) |
| SR-018 / AC-018-01/02 | **FAIL（固定 main @ dc83ccbf）**；候选分支仅静态修正 | 候选分支 `fix/sr-018-owner-evidence-exact-reconcile` @ `c83be9c` 已静态核对 source/step、Evidence、条件 Receipt Schema 和 exact-original binding；58/58 Manifest artifact SHA 核对通过，但 `publish.py --check`、Python、19 Patch、C/native 和真实 PFCP UNKNOWN E2E 未运行、未合并。源仓执行与必要修正由 env-openamsm#28 承接；AC 不提前提升。**Release 子项另有历史 Owner/隔离 E2E PASS（限定）**，证据由 PR #21 + env-5gc-sim run-manifest 固定；不代表 Next/Network Release/Production。 | [Next #104](https://github.com/odango-chan/ca-agent-next/issues/104)；[env-openamsm#11](https://github.com/odango-chan/env-openamsm/issues/11)；[env-openamsm#28](https://github.com/odango-chan/env-openamsm/issues/28)；[env-5gc-sim#79](https://github.com/odango-chan/env-5gc-sim/pull/79) |
| SR-019 / AC-019-02 | **FAIL**（联合 fixture 缺项） | 补同请求 N1+N2 双路、X-CA-Request-Id 重试、旧 generation 迟到 0xD4、冲突 discriminator/n2SmInfoExt1 和 Owner outcome 联合证据；Mock 不拥有 Host Run/Owner 状态 | [#105](https://github.com/odango-chan/ca-agent-next/issues/105) |
| SR-016 / AC-016-01 | **NOT_RUN**（固定 SR 正文缺独立定义） | 澄清 MIG-016-01 与 AC-016-01 的关系；补 AC 输入/步骤/验收，或明确二者独立并修正旧评审回填 | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-016 / AC-016-02～08/10 | **BLOCKED / NOT_RUN** | 等正式 1.6.0 Package、Compiler、Provider/Owner 输入和同一发布批次六宿主证据；#272 合并不等于新版产品 PASS | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-030 / AC-030-02/03/05 | **BLOCKED** | 等正式 Package Schema、languageTarget、Compiler 验证入口和 Golden；不猜测机器契约 | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |
| SR-030 / AC-030-04 | **NOT_RUN** | 中央设计补充 ZIP 元数据归一、entry/Manifest 稳定排序、两次构建逐字节比较和正式 Schema 校验判据 | [#106](https://github.com/odango-chan/ca-agent-next/issues/106) |

## 3. 既有设计评审与后续静态审计的关系

| 评审 Issue | 既有设计结论 | Issue #95 后续核验 | 后续动作 |
|---|---|---|---|
| [SR-013 #77](https://github.com/odango-chan/ca-agent-next/issues/77) | 设计 APPROVE_FOR_READY（限定） | AC-013-01 归档完整性 FAIL；设计通过不抵销固定归档差异 | #102 |
| [SR-016 #78](https://github.com/odango-chan/ca-agent-next/issues/78) | 设计 APPROVE_FOR_READY（限定） | AC-016-01 定义/编号映射冲突；六宿主仍 NOT_RUN | #106 |
| [SR-017 #79](https://github.com/odango-chan/ca-agent-next/issues/79) | 静态设计 APPROVE_FOR_READY（限定） | 固定候选缺现行 F06 payload/continuation/负例，AC-017-02 FAIL | #103 |
| [SR-018 #80](https://github.com/odango-chan/ca-agent-next/issues/80) | 历史 Owner 静态移交 APPROVE_FOR_READY（限定） | 固定 main 发现 source/step、Evidence、Reconcile 缺陷，AC-018-01/02 FAIL；候选分支 c83be9c 静态整改待运行验收 | [Next #104](https://github.com/odango-chan/ca-agent-next/issues/104)；[env-openamsm#28](https://github.com/odango-chan/env-openamsm/issues/28) |
| [SR-019 #81](https://github.com/odango-chan/ca-agent-next/issues/81) | Mock peer 静态设计 APPROVE_FOR_READY（限定） | 联合 fixture 不完整，AC-019-02 FAIL；AC-019-03 NOT_RUN | #105 |
| [SR-030 #91](https://github.com/odango-chan/ca-agent-next/issues/91) | Schema-only 设计 APPROVE_FOR_READY（限定） | AC-030-01/06/07 静态 PASS；02/03/05 BLOCKED；04 NOT_RUN | #106 |

这些不是互相覆盖的评审：设计结论保持其原始快照含义；后续固定源审计新增的是实现/归档/fixture 层证据。两者均保留。

## 4. 当前仍必须保持的状态

- SR-013 AC-013-01：FAIL，直到归档整改和独立复验完成。
- SR-013 AC-013-02/04：NOT_RUN；AC-013-03/05/06：BLOCKED。
- SR-016 AC-016-01：定义缺失，不能判 PASS；六宿主全部 NOT_RUN。
- SR-017 AC-017-02：FAIL；运行验收 NOT_RUN。
- SR-018 AC-018-01/02：固定 main 审计 FAIL；候选分支 c83be9c 未合并、运行 NOT_RUN；AC-018-03 BLOCKED；AC-018-04 仅静态 PASS；Release 子项历史 Owner / 隔离 `ac` E2E PASS（限定），Network ReleaseSMContext #10、Next E2E 和 Production 不声明。
- SR-019 AC-019-02：FAIL；AC-019-03 NOT_RUN。
- SR-030 AC-030-02/03/05：BLOCKED；AC-030-04 NOT_RUN；静态 PASS 只限 AC-030-01/06/07。

## 5. 执行顺序

1. #102：修复 AC-013-01 中央归档的客观完整性问题，并独立复验。
2. #106：修复中央 SR/AC 编号、固定路径、职责和确定性验收判据。
3. #104：完成 Next 中央设计要求与跨仓边界登记；Owner 源实现、Publisher/Python/Patch/C/native 与 PFCP E2E 转由 [env-openamsm#28](https://github.com/odango-chan/env-openamsm/issues/28) 执行，完成后回填证据并复核 AC。
4. #103：按固定 F06/3GPP OpenAPI 补齐 Plugin Event payload 与 continuation 契约。
5. #105：补齐 Mock AMF 联合 fixture；与 #103 使用同一 F06 语义，不让 Mock 自行定义 Host/Owner 身份。

上述顺序不代表可绕过目标仓授权或外部正式契约；所有实施任务须先核对其固定源和当前 Head。

## 6. 非目标

- 本整改分支不修改 ca-openamsm-plugin、env-openamsm、env-5gc-sim、ca-skill-compiler 等外部仓源代码；SR-018 的 Owner 实施/测试工作已按边界登记到 [env-openamsm#28](https://github.com/odango-chan/env-openamsm/issues/28)。
- 不把历史 PoC、旧 CI、旧 Studio PR 或 Mock 通过记录升级为 1.6.0 产品证据。
- 不合并 PR #98 或本整改 PR，不发布、不更改父级 SR 状态。
