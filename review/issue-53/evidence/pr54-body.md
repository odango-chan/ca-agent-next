关联 [Issue #53](https://github.com/odango-chan/ca-agent-next/issues/53)，父级恢复追踪为 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)。

## 目的

将 `docs/refresh-current-state-20261126` 相对 `docs/restore-original-designs-20261125` 的有效状态更新手工整合到恢复基线。此 PR 目标是临时恢复分支，不是 main。

## 固定基线

- Base: `docs/restore-original-designs-20261125` @ `34e99e0cc54cc82b6b40040286fc84673432ef76`
- Head: `docs/issue-53-refresh-state-reconciliation` @ `7452f60ccbc68e1468b52018f59bdc2347cc32d5`
- Refresh source: `docs/refresh-current-state-20261126` @ `f63bbce2709284c97d8cd150343d491a3f2958db`
- Merge base: `32c7c1be5e93bddc83349234476b2ffa09e1ca23`
- Compare: 42 commits ahead / 0 behind，16 changed files。
- Source delta: refresh 独有 6 个提交，全部保留在原分支：
  - `04e4d12eda853462d5b4ff4597483c24b54bbf24`
  - `08953c2461ac3835e1f6909f46536ebb320df026`
  - `adb2c3fd290a30e808d864001392e7f9ed28e22a`
  - `c05d30a023f1cc51123cddd703450b886cc5faac`
  - `68030be5f4263756debb63d12825cc78296a39d3`
  - `f63bbce2709284c97d8cd150343d491a3f2958db`

## 处置原则与关键纠偏

- 对 16 份差异文件逐项处置；详细矩阵见本 PR 的 `docs/治理/现有文档盘点与收敛计划.md` §10。
- 手工整合有效的 SR-025 READY、F02/F08/F09、Publisher、Studio 和跨仓状态更新；没有 cherry-pick、merge、rebase 或覆盖任何原始分支。
- **保留 restore 后续 PR #41/#42 的 SR-003 v0.3.11 模块 VERIFIED 证据**。refresh 分支在 PR #41/#42 之前分叉，其 SR-003 IN_PROGRESS/READY 状态为旧快照，不得覆盖当前状态。
- 当前 SR 状态：4 VERIFIED（SR-001/002/003/024）、1 READY（SR-025）、1 IMPLEMENTED（SR-015）、21 DRAFT。SR-003 的 VERIFIED 仅限模块 AC-003-01～04；系统 EX-02/03/04/18、完整 Runtime 和 DeepSeek Harness 仍 NOT_RUN。
- SR-025 v0.1.8 为 READY；ca-client-tools #43 OPEN，Publisher 未实施，不得提前生成实施完成声明。
- Studio 当前 main 已核验为 `79bd2c3f64a90e7f0f169204c866a3218655bab1`；#272 MERGED、#276 OPEN/DRAFT/DIRTY；#261/#269/#279/#290/#295 OPEN。
- Git tree 统计按 blob 计算：197 tracked files / 157 Markdown；247 recursive tree entries 中有 50 个目录节点。
- 对 16 份文档执行相对 Markdown 链接路径检查，共检查 504 个链接，未发现断裂的本地文件目标。此检查不代替 CI/完整锚点校验。

## 验收与边界

- 本 PR 仅修改文档；不改 main、不更新 restore 原分支、不改变任何 SR 权威状态以外的证据。
- PR 保持 Draft，等待独立评审。
- 首次 Review Context #191（Head `65149f6`）的 80 项回归测试 PASS，但正式文档头检查因总体架构的 review_scope 行带额外文本而失败；已在当前 Head `7452f60` 修正为唯一规范声明。当前 Head `7452f60ccbc68e1468b52018f59bdc2347cc32d5` 的 Review Context Run #192 / #193 / #194 均 SUCCESS；Run #192 已上传 review-context Artifact（`review-context-pr-54-45931351062-1`）。80 项 SR-001 回归测试及正式文档头检查均通过。
- 不在本 PR 中合并；合并后仍只是进入 restore，不代表进入 main。

