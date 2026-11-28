# Issue #95 固定源静态取证与中央设计移交

> 状态：静态核验记录，不代表产品实施、运行测试或 E2E 验收。\
> 固定 Next 快照：`93f1389e7c5968cd30e8a74137207094864ecca0`。\
> 固定 PR Base：`3c7c48383c52504a4861900bc1f8b731442f16c2`。\
> 追踪：[Issue #95](https://github.com/odango-chan/ca-agent-next/issues/95)。

## 1. 口径

本目录的 `PASS` 只表示该行注明的静态核验范围完成。没有本轮真实运行证据的项目保持 `NOT_RUN`；依赖未发布契约、Owner 决定或授权的项目保持 `BLOCKED`。历史报告和 CI 只作为带来源的历史记录，不能替代本轮验收。外部仓库全部只读。

执行前通过 `gh pr view 46` 确认 PR #46 OPEN、Head/Base 与上述值一致；通过 `git merge-base --is-ancestor 93f1389e7c5968cd30e8a74137207094864ecca0 refs/remotes/origin/pr/46` 确认固定 Head 属于 PR 历史。启动检查点见 [Issue #95 评论](https://github.com/odango-chan/ca-agent-next/issues/95#issuecomment-7211029498)。中央输入只取固定快照，不取当前工作分支或较新的默认分支。

## 2. 报告索引

| SR | 静态报告 | 本 Goal 范围 |
|---|---|---|
| SR-012 | [Compiler 原始设计资产](SR-012.md) | AC-012-01 Next→源仓静态部分、03 |
| SR-013 | [Compiler when / Artifact 归档](SR-013.md) | AC-013-01：FAIL（归档一致性）；历史结果与本轮复跑分开 |
| SR-016 | [Skill Studio 历史实现](SR-016.md) | MIG-016-01、AC-016-09 静态 PASS；六宿主及其余产品 AC NOT_RUN/BLOCKED |
| SR-017 | [业务 Plugin](SR-017.md) | AC-017-01/03/04 静态 PASS；02 FAIL（设计缺项）；运行 NOT_RUN |
| SR-018 | [Owner](SR-018.md) | AC-018-01/02 FAIL；04 静态 PASS；Release 与运行 NOT_RUN/BLOCKED |
| SR-019 | [Mock AMF](SR-019.md) | AC-019-01/04 静态 PASS；02 FAIL；03 NOT_RUN |
| SR-020 | [Python Host](SR-020.md) | AC-020-01/02/04 静态 PASS；03 NOT_RUN |
| SR-021 | [Go Native Host](SR-021.md) | AC-021-01/02/04 静态 PASS；03 NOT_RUN |
| SR-022 | [Runtime 执行内核](SR-022.md) | AC-022-01/02/04 静态 PASS；03 NOT_RUN |
| SR-023 | [Skill 作者源与语言规范](SR-023.md) | AC-023-01～03 静态 PASS；04 BLOCKED/NOT_RUN |
| SR-030 | [Host Context Schema-only Publisher](SR-030.md) | AC-030-01、06/07 静态 PASS；02～05 BLOCKED/NOT_RUN |

## 3. 11 项独立完成矩阵

“完成”指本 Goal 授权的静态核验已完成，不等于整项 SR、产品或 E2E 通过。各 AC 的真实状态如下；范围外项目不升级为 PASS。

| SR | 独立静态工作 | 逐 AC 实际状态 |
|---|---|---|
| SR-012 | Compiler 218/12 文件集合、12 blob、三份正文 diff | 01 **PASS（仅 Next→源仓）**；02 **NOT_RUN**；03 **PASS（冻结决策/Harness 门槛静态对照）** |
| SR-013 | PR #18 59 文件、58 清单、36 pb、历史结果和内部一致性 | 01 **FAIL（归档一致性）**；02 **NOT_RUN**；03 **BLOCKED**；04 **NOT_RUN**；05/06 **BLOCKED**；本轮复跑 **NOT_RUN** |
| SR-016 | 14 对迁移原文、状态模型、实时 PR/Issue、六宿主入口 | MIG-016-01 **PASS**；AC-016-01 **NOT_RUN（定义缺失）**；02～08 **BLOCKED/NOT_RUN**；09 **PASS（静态状态模型）**；10 **BLOCKED/NOT_RUN**；六宿主全部 **NOT_RUN** |
| SR-017 | main/候选 tree/blob、OpenAPI、peer、F06 与权责 | 01 **PASS（静态移交）**；02 **FAIL（候选设计缺项/冲突）**；03 **PASS（静态权责映射）**；04 **PASS（证据分层）**；运行 **NOT_RUN** |
| SR-018 | Owner 59 blob、23+2、24/25、摘要、Receipt/Proof/QoS/Reconcile | 01 **FAIL（source/step 定位不一致）**；02 **FAIL（非 Release：Evidence/Schema/exact-original 缺陷）**；03 **BLOCKED**；04 **PASS（静态边界）**；Release **BLOCKED/NOT_RUN** |
| SR-019 | 12 份架构/ADR、peer 源码、场景与联合 fixture | 01 **PASS（来源/边界）**；02 **FAIL（联合 fixture 缺项）**；03 **NOT_RUN**；04 **PASS（静态分工）** |
| SR-020 | Python Host 6/6 原文、符号、OPEN PR、Publisher 边界 | 01/02 **PASS（静态）**；03 **NOT_RUN**；04 **PASS（静态边界）** |
| SR-021 | Go Host Task/Artifact 2/2 原文、current/vNext、v1 contract | 01/02 **PASS（静态）**；03 **NOT_RUN**；04 **PASS（静态晋级边界）** |
| SR-022 | Runtime 10/10 原文、执行符号、采用排除与 SR-007 映射 | 01/02 **PASS（静态）**；03 **NOT_RUN**；04 **PASS（静态映射）** |
| SR-023 | 10 份源文、两个 JSON、Release Record、三份 MAS 源 | 01～03 **PASS（静态）**；04 **BLOCKED/NOT_RUN** |
| SR-030 | 固定路径与独立 blob 的 Subject Schema 字节、Provenance | 01 **PASS（274 字节固定源）**；02/03/05 **BLOCKED**；04 **NOT_RUN**；06/07 **PASS（设计约束）** |

## 4. 固定源与 SHA 清单

以下均为实际读取的完整提交；详细 tree/blob、版本和 API 见各报告。固定 Next 审计输入始终为 `93f1389e7c5968cd30e8a74137207094864ecca0`，后续中央证据提交不反向改写该快照。

| 对象 | 固定提交及关键身份 |
|---|---|
| Compiler / SR-012、013 | `255ab85fa5abb4b0bf36656bf64250cafebf45cb`；v2.1.0 annotated tag `11ff20cd138d69fd04dcf08785937efcd26a9a7c` → `b67fbb56c34d15b8d5a0903c8a7ca93d608f8f65`；Issue #61 OPEN |
| AC-013-01 归档 | Next `c3e5bb78ff49306329bcbc2387da6108280903bc`；isolated-poc tree `8c25f20f5a349809ba3e75fb2d0789aafac50735`；清单 blob `a27ae96483e335cb63da168bf7f03ddd994c36c2` |
| Studio / SR-016 | main `5b666c0ef754ed32fa37c97ce2429f328c70477f`；六宿主入口 `79bd2c3f64a90e7f0f169204c866a3218655bab1`；14 对迁移 blob 见报告 |
| Plugin / SR-017 | main `eb83c8f2e83dbcdc56b484126b2acf9e8f2a7397`；Draft PR #1 `e7027c805fedcd986e8f756d43fd997245ca6504`；architecture `9bc2c78fce6df33e54877e336ee10af4405dcb81` |
| Owner / SR-018 | `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550`；59 个 v1alpha4 blob；ToolCatalog `88d9709aac62c6d608d057dc797ada6f2189611f`；CapabilityContracts `4fdd22f0eda2c2f2b5096cd167bc705f5a29e06e` |
| Mock AMF / SR-019 | `6ba1dc47049013e19d93222fb308ffead7eb4c0e`；Modify `66d43e60c846a581a37c4e679c0211499fcfa5c4`；Release `7806851cdd323200215b44fa9c70c9bff4090cdd` |
| Python Host / SR-020、030 | `57e277ff9094dad93543df46910a12a1dbbaf560`；Subject Schema blob `4faee66642b8bc5eb2e45c131be4688b982037d8`，SHA-256 `1147f48e2a45405c07d32b8a09f79f151c292cd3711b1fd97c2fd1a3e5485675` |
| Go Host / SR-021 | `447d0cce7e42c7c1184b11fb2563792eead68d51`；Artifact contract `2c0b07f2eaff3bc1020bfc6775ef9bf09e3052ae`，同一文档 blob `d35e5859855992f6e1327ce10b069ef6d126c0b2` |
| Runtime / SR-022 | `9db2230c172da8742ecfc5049cbfbd1a71b7828f`；10 份固定设计 blob 与执行符号见报告 |
| ca-skills / SR-023 | main `780497a2918ad3e7bdff554ab64b0ba627e867e0`；v1alpha5 `18d8184367982ccbc835756136c4a53f9096c3a0`；规范 blob `1b6f194839af1329ffb69ea044bea336eb1e286f` |
| F06 交叉输入 / SR-017～019 | env-openamsm `dc83ccbf5be54dcc7112dd43ba95ea6fa5975550` 的 TS29502 blob `3572be0315a782691ce8b5546b7bc1d5b22fcd64`；env-5gc-sim `6ba1dc47049013e19d93222fb308ffead7eb4c0e` |

## 5. 设计与现状差异、外部依赖和未决事项

1. **统一未发布边界**：1.6.0 的正式 Schema、languageTarget、Package、Compiler DTO/Artifact、Golden、Bundle 和 Release 均未交付。文档中的 `/2` Artifact/BuildResult、候选 languageTarget 与 SemVer 没有被当成冻结契约。
2. **Compiler #61 旧目标**：其正文仍以 v1alpha5 when 为目标并建议尽量复用旧接口；Next 的 1.6.0-only/无兼容目标尚需 Compiler Owner 闭合。
3. **AC-013-01 归档缺陷**：`audit.json` 的 py-results bytes/SHA 陈旧；`SHA256SUMS` 以 `/` 开头导致原复验命令不可搬移；`vet.log` 未归档。58/58 哈希匹配只覆盖路径归一化后的文件完整性。
4. **Plugin 候选缺口**：payload.request、N2 双类 continuation、同请求双路、冲突/n2SmInfoExt1 与实际 Schema 未闭合，旧 ack 句违反 Host/Plugin 权责。
5. **Owner 静态缺陷**：Modify source/step 不一致，两个 Evidence 参数无目标，resolved 输出缺 `reDispatched`，0023 未完整执行 exact-original 再绑定；0021 不能自动弥补包装路径。
6. **Mock 联合输入缺口**：基础场景存在，但缺同请求双路、`X-CA-Request-Id` 重试、旧 generation 迟到 0xD4、冲突/n2SmInfoExt1 和 Owner outcome 联合证明。
7. **Studio 历史/目标分层**：#272 实时已 MERGED（`a8633553615d786e360a62c2b0042a27ae92d9d3`），与固定文本旧状态不同；#276/#269 仍 OPEN；旧 Development/CI 不进入新 1.6.0 验收，六宿主仍缺真实证据。
8. **参考实现不能替代 Next**：Python 内容寻址 Artifact、Go ProductTask/tool-mcp-gw、旧 Runtime DIRECT/Callable 路径均不采用；Go Host 晋级 NOT_DECIDED，Next Python Runtime 未实施。
9. **语言历史与目标分层**：v1alpha5 Release Record 与 main Proposed 头部并存；旧 `mas::` 作者源不自动迁移。固定快照目录树错误已由独立提交 `67c5ade947f7f69c4c4411033b60f846e80dc732` 修正。
10. **静态 FAIL 的后续责任**：归档、Plugin、Owner、Mock 的修复需各自获授权的后续 PR；本 Goal 未修改外部仓，也未把后续需求写成已完成。

## 6. 中央文档修改与验证

本 Goal 在 Next 共修改 29 个不同文件：11 份对应 SR；本目录 1 份索引与 11 份 SR 报告；`CA-SL 1.6.0完整语言规范.md`；`文档总目录与索引.md`、`功能树与需求追踪基线.md`、`SR 总索引.md`、`实施状态总览.md`、`跨仓设计资产迁移与一致性审计.md`。未修改外部仓库文件，未改变父级 SR 主状态，未实施 SR-025 Owner Publisher 或 SR-030 正式 Publisher。

执行的检查均为静态检查：`git diff --check`、Git tree/blob/路径集合比较、原始字节 SHA-256、源文与中央正文 diff、相对 Markdown 文件目标存在性检查、PR/远端 SHA 回读。没有运行 Go、Python、npm、Browser、Compiler、NF、Next Runtime 或 E2E。报告中的历史测试数字仅保留来源。

可审查入口为 [Draft PR #98](https://github.com/odango-chan/ca-agent-next/pull/98)，Base 为固定 PR #46 Head `93f1389e7c5968cd30e8a74137207094864ecca0`。最终远端提交以 PR 页面与 Issue #95 最终检查点的完整 SHA 为准。

## 7. 修订记录

| 日期 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-27 | kimi-k3.1-pro | 全文 | 固定审计快照、证据口径与 SR-012 报告入口 | 建立可复验的中央移交记录 | Issue #95；PR #46 |
| 2026-11-27 | kimi-k3.1-pro | §2～6 | 汇总 11 项逐 AC 矩阵、固定源、设计差异、未决事项和中央修改清单 | 完成静态交付复核而不扩大为产品验收 | Issue #95；Draft PR #98 |
