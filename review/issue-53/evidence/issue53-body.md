## 目标

审查并整合 `docs/refresh-current-state-20261126` 相对 `docs/restore-original-designs-20261125` 的 6 个独有提交和 16 份文档差异，形成单一、准确的恢复集成文档基线。

## 关联

- 父级恢复与资产迁移：[Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)
- 主干同步治理：[Issue #50](https://github.com/odango-chan/ca-agent-next/issues/50)
- 主干同步规范与计划：[PR #51](https://github.com/odango-chan/ca-agent-next/pull/51)

## 固定审计输入（2026-11-27）

- restore HEAD：`34e99e0cc54cc82b6b40040286fc84673432ef76`
- refresh HEAD：`f63bbce2709284c97d8cd150343d491a3f2958db`
- merge base：`32c7c1be5e93bddc83349234476b2ffa09e1ca23`
- restore 相对 refresh：21 个独有提交；refresh 相对 restore：6 个独有提交。
- 两分支 tree 均为 197 tracked files / 157 Markdown；GitHub recursive tree 返回 247 entries，其中 197 blobs、50 directory tree nodes。
- refresh 六个提交：
  - `04e4d12` refresh F09/F02/F08 and ready SR-025 publisher design
  - `08953c2` sync architecture and governance state; link SR-025 issue
  - `adb2c3f` refresh cross-repository audits, inventory and indexes
  - `c05d30a` close SR-025 issue trace and align F09 revision references
  - `68030be` reconcile current SR-003 and Skill Studio status references
  - `f63bbce` finalize current SR-003 and F09 index alignment

## 范围

对 16 个差异文件逐一处置，重点纳入仍有效的 SR-025 READY / ca-client-tools #43 OPEN、CA-SL v1alpha5 Release Record、F02/F08/F09 更新、Studio 与外部 Publisher 当前状态、文档索引/目录修订记录。

必须保留 restore 中更新的 SR-003 VERIFIED、PR #34/#41/#42 的合并和双平台证据、AC-003-01～04 模块门槛，以及系统 EX NOT_RUN。不得用 refresh 在 #42 之前的 SR-003 IN_PROGRESS / READY 旧快照覆盖这些更新。

## 强约束

- 保留两个原始分支和六个 refresh 提交，不 force-push、不 rebase、不改写、不删除分支。
- 在新分支上以正常提交形成手工整合，并以 PR 目标为 restore 分支；不直接更新 restore 或 main。
- 外部仓状态必须以本次实际查询为准；历史快照必须注明日期。
- SR 状态统计必须重新计算，不能沿用 refresh 中 SR-003 旧状态。当前应区分 4 VERIFIED、1 READY（SR-025）、1 IMPLEMENTED（SR-015）、21 DRAFT。
- 文件统计以 Git tree 的 blob 为准：两分支当前均为 197 tracked files / 157 Markdown；247 个 recursive tree entries 包含 50 个目录节点，不能将 entries 总数误当作文件数。
- 每个更新文件必须有修订记录并关联本 Issue。
- PR 保持 Draft，等待独立评审；不得自动合并。

## 验收

- 16 份文件均有处置矩阵：纳入、手工整合、保留 restore 最新版本/不纳入，并说明依据。
- 所有有效内容进入新整合分支，SR-003 当前 VERIFIED 证据不被降级。
- 重新核对 197 tracked files / 157 Markdown；247 recursive tree entries 含 50 个目录节点。文档目录、SR 总索引、功能树、实施状态、F09/F02/F08 交叉引用已同步。
- 16 份文档共检查 504 个 Markdown 链接目标，未发现断裂的本地文件目标；此结果不代替 PR CI 和独立评审。
- 创建以 restore 为 base 的 Draft PR，记录准确 base/head SHA、差异和检查结果。
- 原始 refresh 与 restore 分支均保持不变；main 不变。

## 当前交付（2026-11-27）

- 整合分支：`docs/issue-53-refresh-state-reconciliation` @ `7452f60ccbc68e1468b52018f59bdc2347cc32d5`。
- Draft PR：[ #54 Reconcile refresh-current-state into restore baseline](https://github.com/odango-chan/ca-agent-next/pull/54)，base `docs/restore-original-designs-20261125` @ `34e99e0cc54cc82b6b40040286fc84673432ef76`，16 files changed。
- PR #54 首次 Review Context #191 在旧 Head `65149f6` 上 80 项测试 PASS，但正式文档头检查失败；已修复总体架构 review_scope 声明。当前 Head `7452f60ccbc68e1468b52018f59bdc2347cc32d5` 的 Review Context Run #192 / #193 / #194 均 SUCCESS；Run #192 已上传 Artifact `review-context-pr-54-45931351062-1`。尚无 Review；PR 未合并。
- 该 PR 仅进入 restore 候选，不进入 main；SR 状态未修改。

