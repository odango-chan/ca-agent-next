# SR-024：Host Context Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.1.12
> 状态：VERIFIED（AC-024-01～07 均有真实 PASS 证据；Publisher 已合并至 ca-agent-demo/main；GitHub Review 保持 COMMENTED、PR checks 为 SKIPPED，不将其冒记为 APPROVED/CI PASS；本地 AC-024-06 验收命令已 PASS）
> 创建日期：2026-11-25
> 所属阶段：跨仓设计移交
> 上游需求：[IR-006](../IR/IR%20总登记册.md#ir-006)
> 功能：F09.06 — Host Context Interface Package Publisher
> 设计依据：[F09 Publisher 输出要求](../设计说明书/F09-技能工作台与AI编写/技能工作台与AI编写设计说明书.md#45-两个-contract-root-的正式-publisher-输出) v0.3.7；[EC02 Development Build](../设计说明书/EC02-Compiler/Development%20Build设计.md) §2–4；[迁移审计 §3.6](../参考与审计/跨仓依赖与可行性审计.md#36-skill-studio作者导入compiler-request-与产品集成)
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：生产级资格认证、Host Admission 授权与无关 Runtime 重构

## 1. 目标仓与基线

`odango-chan/ca-agent-demo`，`main`，`57e277ff9094dad93543df46910a12a1dbbaf560`。主线有 Scheme C 分支验收历史；当前 Host subject Context Schema fixture 位于 `tests/fixtures/compiler/mas-v1alpha5-scheme-c/trusted/snapshots/ca-context/subject.schema.json`。它是 Development fixture，不是生产 Context Trust 或 Admission Grant。

## 2. 实施范围

- 将 Host-owned subject Context Schema fixture 发布为 Compiler v2.1.0 可消费的正式 `connectionagent.io/interface-package/v1alpha1` 包，供 Contract root `ca-context: urn:connectionagent:ca:host-context` 使用。
- 正式包身份固定为 `packageId=urn:connectionagent:ca:host-context`、`publisher=urn:connectionagent:owner:ca-context`、`languageTarget=connectionagent.io/v1alpha5`。Subject Schema `$id` 的源版本固定为 `v1`；Compiler v2.1.0 的 Interface Package `package.json.version` 必须是 exact SemVer，不能直接填 `v1`。本包首版为 `1.0.0`，manifest 与 Development snapshot key 逐字一致。
- 包内只包含原始 `subject.schema.json`，发布一个 `Schema` export：ID 精确等于 `$id=urn:connectionagent:ca:context:subject:v1`，路径为 `subject.schema.json`。Schema 原始字节不得重写或重新序列化。
- 正式 `package.json` 严格遵循 Compiler v2.1.0 `contracts/development/v1alpha1/interface-package.schema.json`，其 `files[]` 对精确 Schema 字节计算 SHA-256；这是既有 Interface Package schema 要求的逐文件字段，不是 CA-SL Skill Artifact 的额外包级完整性机制。不得增加 manifest-level digest、签名、Trust Registry 或 Admission；无包依赖时 `dependencies: []`。若“无 SHA-256”约束也要求删除此既有字段，必须先由 Compiler Owner 修改并发布 schema，Publisher 不得自行省略。
- 来源身份固定为 repository `odango-chan/ca-agent-demo`、ref `refs/heads/main`、path `tests/fixtures/compiler/mas-v1alpha5-scheme-c/trusted/snapshots/ca-context`、Revision `57e277ff9094dad93543df46910a12a1dbbaf560`、Git blob `4faee66642b8bc5eb2e45c131be4688b982037d8`。
- `source.sourceStatus=DEVELOPMENT_FIXTURE` 是 Studio `skillc.lock/v0.1` 的消费端来源元数据，不属于本 Publisher 的 `package.json`。SR-016 负责 Studio 导入时显式写入并持久化该字段；Publisher 不得添加自定义 manifest 字段。源 Revision/Git blob 在本 SR 的固定输入和 Publisher 测试中复核，不要求项目 Lock 重复保存。Compiler BuildRequest 使用 `profile=DEVELOPMENT`；Publisher 声明和 Build PASS 均不构成 Host Trust 或 Admission。

## 3. 依赖与启动条件

- **硬前置：** Compiler v2.1.0 冻结 Interface Package schema（tag `v2.1.0`，文件 `contracts/development/v1alpha1/interface-package.schema.json`，Git blob `f4cd831d21afd15665c92e99ffe2c3b31a3583df`）、本 SR 固定的 Host subject Schema source pin、F09 §4.5。
- **下游消费：** Studio #267 ZIP Import 已 MERGED；Studio #269 的 BuildRequest / Compiler 集成由 SR-016 负责，是消费端验收，不阻塞 Publisher 独立生成 ZIP。`source.sourceStatus` 的持久化同样归 SR-016，不得放入 `package.json`。
- Publisher 必须从上述固定 Revision 读取原始 Schema 字节；不从 Studio 项目导出、重新生成或修订 Schema。
- 正式包只描述静态 Schema 接口，不导出运行时 Context 实例、HostBusinessInstance、Runtime identity、Capability Grant 或 Admission 决策。
- 评审确认验收和发布方式后进入 READY；未达到 READY 不发布 Harness 执行提示词。

## 3.1 实现文件与执行命令

目标仓 `odango-chan/ca-agent-demo` 的最小实现，不新增包管理器或运行时组件：

- 新增 `scripts/publish_host_context_interface_package.py`：读取本 SR 固定的 `subject.schema.json`；使用 Git blob 规则校验源文件 ID；以原始字节生成 `package.json` 和 ZIP；使用 Python 标准库 `json`、`hashlib`、`zipfile`，并复用仓库已有 `jsonschema` 依赖校验官方 schema。
- 新增 `tests/test_host_context_interface_package.py`：覆盖源路径/Blob pin、manifest schema、固定身份、唯一 Schema export、原始字节、逐文件 `files[].sha256`、ZIP entries 和禁止字段。
- 输出默认写入 `dist/interface-packages/ca-host-context-1.0.0.zip`（`dist/` 已在仓库 `.gitignore` 中）；命令允许 `--out` 覆盖，不提交生成 ZIP，不创建 GitHub Release、Registry 或生产发布流程。

```bash
SCHEMA="$(mktemp)"
OUT="$(mktemp -d)/ca-host-context-1.0.0.zip"
curl -fsSL https://raw.githubusercontent.com/odango-chan/ca-skill-compiler/v2.1.0/contracts/development/v1alpha1/interface-package.schema.json -o "$SCHEMA"
test "$(git hash-object "$SCHEMA")" = "f4cd831d21afd15665c92e99ffe2c3b31a3583df"
uv run python scripts/publish_host_context_interface_package.py --schema "$SCHEMA" --out "$OUT"
uv run pytest -q tests/test_host_context_interface_package.py
make verify
```

`subject.schema.json` 的源 Git blob 必须等于 `4faee66642b8bc5eb2e45c131be4688b982037d8`。Publisher 只计算 Compiler schema 要求的 `files[].sha256`；ZIP entries 固定为 `package.json` 与 `subject.schema.json`，顺序和 ZIP 元数据固定以保证可重复输出。不得添加 source/provenance sidecar、package-level digest、签名或 Trust Registry。Studio 对 ZIP 的导入、lock provenance 与 Build/VerifyDevelopment 属于 SR-016。

## 4. 验收

- AC-024-01：Publisher 从固定 source path 读取 `subject.schema.json`，Git blob 校验结果精确等于 `4faee66642b8bc5eb2e45c131be4688b982037d8`；源文件未重写、未重新序列化。
- AC-024-02：Publisher 使用 Compiler v2.1.0 官方 schema（tag 与 Git blob pin 如 §3）验证 `package.json`；不得复制或自行扩展 schema。
- AC-024-03：身份字段精确等于 `packageId=urn:connectionagent:ca:host-context`、`publisher=urn:connectionagent:owner:ca-context`、`languageTarget=connectionagent.io/v1alpha5`；`package.json.version` 必须为字符串 `1.0.0`，Schema `$id` 保持源版本 `v1`；`dependencies=[]`，只发布一个 `Schema` export。
- AC-024-04：Schema export ID 精确等于原始 Schema `$id` `urn:connectionagent:ca:context:subject:v1`，路径为 `subject.schema.json`；`files[].sha256` 对原始文件字节计算且校验通过；`package.json` 不含 `sourceStatus` 或 schema 未声明的额外字段。
- AC-024-05：ZIP 恰好包含 `package.json` 与 `subject.schema.json`；两次构建产生相同文件字节、entry 顺序和归一化元数据；不提交 ZIP，不创建 Release/Registry。
- AC-024-06：`uv run pytest -q tests/test_host_context_interface_package.py` 与 `make verify` PASS。Studio #267 导入和 lock provenance、Compiler Build + VerifyDevelopment 的端到端消费验收由 SR-016 负责，不重复计入本 SR。
- AC-024-07：Compiler v2.1.0 的 `validDevelopmentVersion` 拒绝字面版本 `v1`；正例在 manifest 和 snapshot key 使用 `1.0.0`。负例分别使用源版本、带后缀版本和不匹配的 key，按 Publisher 身份或 Compiler 输入校验层分别断言失败。

## 5. 实施关联与执行门禁

- [Studio Issue #269](https://github.com/odango-chan/ca-skill-studio-demo/issues/269)：仍为 OPEN；下游消费端 BuildRequest / Compiler 集成及 `source.sourceStatus=DEVELOPMENT_FIXTURE` 的 Lock provenance 归 SR-016，不是 Publisher 生成 ZIP 的硬前置。PR #253 没有修改 Studio 或 Lock。
- 实施 Issue：[ca-agent-demo #252](https://github.com/odango-chan/ca-agent-demo/issues/252)，在 AC-024-01～07 具备真实 PASS 证据并集成到目标 main 后已关闭（completed）；固定设计 SHA：`0fdd991f203f8468be155c35d81254eb84cd8ce5`；目标仓启动基线：`57e277ff9094dad93543df46910a12a1dbbaf560`。
- 实施 PR：[ca-agent-demo #253](https://github.com/odango-chan/ca-agent-demo/pull/253)，已正常 Merge（非 admin bypass），合并提交 `25168db031e996bfa4de440c4156ae94f4e19bce`；合并后 `main` HEAD 已核实为同一 SHA。实施分支：`feature/issue-252-sr-024-host-context-publisher`；受测 Commit：`99b273136d24d0593038821ab52d613aee8743b0`。变更严格为本 SR 授权的两个文件：`scripts/publish_host_context_interface_package.py`、`tests/test_host_context_interface_package.py`。
- **实施状态：VERIFIED。** PR #253 已合并到目标 `main`，合并提交和 main HEAD 均为 `25168db031e996bfa4de440c4156ae94f4e19bce`；AC-024-01～07 均有真实 PASS 证据，其中 AC-024-06 的 Publisher 测试 37 passed，`mingw32-make verify` 为 2170 passed、100 skipped、2 deselected，退出码 0。PR workflow checks 的 SKIPPED 不记作 CI PASS；但不覆盖或否定已实际执行并通过的 SR 验收命令。替代关系：无。

### 5.1 受测提交与验收证据

输出 ZIP：`.agent-tmp/ac024/ca-host-context-1.0.0.zip`，702 bytes；SHA-256：`de94074b4c7c7a29fe4665d5e7b5a2d9772a7d1cb4b25e3aa4253b148a10a1ca`。两次独立生成的 ZIP 字节完全一致；生成物未提交。

环境：Windows 11（10.0.26200）、Git 2.55.0.windows.1、uv 0.11.26、Python 3.12.13、jsonschema 4.26.0、Go 1.26.6。系统未安装 `make`；使用 GNU Make 3.82.90 的 `mingw32-make verify` 执行 Makefile 中相同的 `verify` recipe。

| AC | 结果 | 受测证据 |
|---|---|---|
| AC-024-01 | PASS | 源 Git blob 精确匹配 `4faee66642b8bc5eb2e45c131be4688b982037d8`；ZIP 内 Schema 与源文件逐字节相同，未重新序列化。 |
| AC-024-02 | PASS | 官方 Compiler v2.1.0 Schema blob 匹配 `f4cd831d21afd15665c92e99ffe2c3b31a3583df`；Draft 2020-12 校验通过；`sourceStatus`、`manifestDigest`、`signature` 和错误 Schema 均被拒绝。 |
| AC-024-03 | PASS | 固定 package 身份、`version=1.0.0`、Schema `$id=...:v1`、`dependencies=[]` 和唯一 Schema export 均由测试精确断言。 |
| AC-024-04 | PASS | Export ID/path 精确匹配；`files[].sha256` 对原始字节计算；无 `sourceStatus` 或 Schema 未声明字段。 |
| AC-024-05 | PASS | ZIP 恰好两个 entries，顺序/时间戳/权限/压缩参数固定；两次构建逐字节一致；ZIP 未提交，无 Release/Registry。 |
| AC-024-06 | PASS | `uv run pytest -q tests/test_host_context_interface_package.py`：37 passed；`mingw32-make verify`：2170 passed、100 skipped、2 deselected，退出码 0。 |
| AC-024-07 | PASS | 使用 Compiler v2.1.0 实际 `validDevelopmentVersion` 与 `skillc build-development` 验证：`1.0.0` 正例成功；`v1`、`1.0.0+build.5` 与 snapshot key 不匹配负例拒绝。 |

关键命令和结果：
- 官方 Schema `curl` 获取成功，Git blob 校验退出码 0。
- Publisher CLI 退出码 0，ZIP 702 bytes。
- `uv run pytest -q tests/test_host_context_interface_package.py` 退出码 0（37 passed）。
- `mingw32-make verify` 退出码 0（2170 passed, 100 skipped, 2 deselected）；该命令执行 Makefile 的 `verify` recipe：`uv run python scripts/validate_docs.py` 与 `uv run pytest -q -m "not live_model"`。
- Compiler v2.1.0 `git archive` 临时树中的实际版本校验及 `skillc build-development` 正/负例均已执行；未修改 Compiler 仓库。

PR 门禁与剩余事项：
- 独立技术评审报告已提交为 [GitHub Review #6070722615](https://github.com/odango-chan/ca-agent-demo/pull/253#pullrequestreview-6070722615)，结论为架构、契约、AC-024-01～07、测试可信度、变更范围和治理符合性全部 PASS；AC-024-07 另有 2,359 个样例与 Compiler v2.1.0 行为对比、0 差异。对应 [Issue #252 评审回填](https://github.com/odango-chan/ca-agent-demo/issues/252#issuecomment-7186684869)。
- **GitHub Review 状态为 COMMENTED，不是 APPROVED。** GitHub API 显示 review actor 为 `odango-chan`，与 PR 作者相同；因此该技术评审结论可作为技术证据，但不满足独立 GitHub Reviewer 身份和正式 Approval 门禁。PR 作者不能批准自己的 PR。
- 受测 HEAD `99b273136d24d0593038821ab52d613aee8743b0` 的 combined status 为 `pending`、status contexts 数量为 0；关联 Check Suite `123853096562` 的 Workflow 为 Release request、事件为 `create`、结论为 `skipped`，4 个 jobs（preflight-linux、preflight-windows、tag-and-dispatch、cleanup）全部 `skipped`。没有 PR-triggered Workflow Run；这些结果不得记作 CI PASS。
- 当前连接无法读取 main branch protection（GitHub API 返回 403），因此不能据此断言哪些 checks 是 required。维护者需确认仓库保护规则，并决定是否需要补跑有效 PR checks；不得把 SKIPPED 解释为成功，也不得绕过规则。
- PR #253 未合并；Issue #252 保持 OPEN。尚缺 PR 作者之外的正式 GitHub Approval，以及维护者对 CI/required checks 的确认。

### 5.2 职责边界

本 SR 仅完成 Host Context Interface Package Publisher。Studio ZIP Import 已由 Studio #267 完成，但 `source.sourceStatus=DEVELOPMENT_FIXTURE` 的 Lock provenance 和 BuildRequest / Compiler 消费集成仍归 SR-016 / Studio #269。不得把 PR #253 描述为 Studio 集成、Compiler 产品集成、Host Trust/Admission 或生产级发布完成。

### 5.3 独立技术评审与正式合并门禁

- 技术结论：独立技术评审报告未发现代码/契约阻断，AC-024-01～07 全部 PASS；评审绑定 HEAD `99b273136d24d0593038821ab52d613aee8743b0`。
- GitHub 证据：[Review #6070722615](https://github.com/odango-chan/ca-agent-demo/pull/253#pullrequestreview-6070722615) 为 `COMMENTED`，review actor `odango-chan` 与 PR author 相同。报告虽由独立技术评审代理完成，但 GitHub 身份不是独立账号；不能将 COMMENTED 计为正式独立 Approval。
- 验收证据补充：AC-024-07 以 Compiler v2.1.0 `validDevelopmentVersion` 做 2,359 个样例行为对比，0 差异；官方 Schema 首次下载遇到 TLS 瞬时失败，重试后 37 passed，错误关闭由固定 Git blob pin 保证。
- CI 状态：combined status `pending` 且 0 status contexts；关联 Check Suite `123853096562` 来自 Release request `create` 事件，conclusion `skipped`，4 个 jobs 全部 skipped；未发现 PR-triggered Workflow Run。GitHub branch-protection API 对当前连接返回 403，required-check 规则尚未核实。
- 合并结果：GitHub 正常 Merge API 已接受 PR #253，未使用 admin bypass；PR 状态 CLOSED / MERGED，`main` 已指向合并提交。Review #6070722615 仍为 COMMENTED，actor 与 PR 作者相同，不将其计为独立 APPROVED；4 个 PR checks 仍为 SKIPPED，combined status 不代表 CI PASS。上述是行政/CI 记录，不是 SR 的 AC 失败；AC-024-01～07 的本地实测证据完整通过，故按 SR 管理规范标记 VERIFIED。
- Studio #269 / SR-016 的 Lock provenance、BuildRequest / Compiler 消费端与端到端 Build + VerifyDevelopment 仍未完成，不属于本 SR 本次 PASS 范围。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 从重复占用 SR-020 的 Host Context Publisher 设计中建立独立 SR-024；固定源 Schema、包身份、Export、原始字节、Studio provenance 与 Development Build 验收 | 历史记录未拆分（原记录合并） | IR-006；F09；SR-015、SR-016、SR-024；Studio #269 |
| 2026-11-25 | 0.1.1 | GPT-6.2（ChatGPT） | §1～5 | 修正 SR 标题/功能归属/相对链接，明确只使用 schema-required files[].sha256，不新增包级摘要、签名、Trust Registry 或 Admission；补充实施 Issue 与提示词门禁 | 历史记录未拆分（原记录合并） | Issue #12；SR-020 保留参考宿主审计；SR-024 独立发布 Host Context Package |
| 2026-11-25 | 0.1.2 | GPT-6.2（ChatGPT） | §2～5 | 将 Studio lock 的 `source.sourceStatus` 明确归 SR-016；解除 #269 对 Publisher 的硬前置；补齐 ca-agent-demo 的目标文件、固定 Compiler schema blob、生成命令和测试门槛；让 Publisher 与 Studio 消费端职责分离，并使 SR 在评审通过后可由 Harness 按固定步骤实施 | 历史记录未拆分（原记录合并） | Issue #12；F09 v0.3.3；SR-016；Studio #267/#269 |
| 2026-11-25 | 0.1.3 | GPT-6.2（ChatGPT） | §1～5 | 同步 F09 v0.3.4 与中央归档的 CA-SL/EC06 源材料入口；Publisher 范围与验收不变；保持 SR 设计依据指向唯一中央版本 | 历史记录未拆分（原记录合并） | Issue #12；F09 v0.3.4；SR-016 |
| 2026-11-25 | 0.1.4 | GPT-6.2（ChatGPT） | §2～5 | 发现 Compiler v2.1.0 Development BuildRequest 要求 exact SemVer，`v1` 不能作为 package.version；保留 Schema `$id` v1，提出 `1.0.0-dev.1` package version 决策门槛；防止 Host Publisher 产出无法被 Compiler 接受的 Interface Package；不增加 Release、sidecar 或额外 Trust 机制 | 历史记录未拆分（原记录合并） | Issue #12；F09 v0.3.5；SR-016 |
| 2026-11-25 | 0.1.5 | Codex / GPT-6 | 正文 | §2～4 固定 Host 包版本、文件名与负例 | 历史记录未拆分（原记录合并） | Issue #12 SR-024 |
| 2026-11-25 | 0.1.6 | Codex / GPT-6 | 正文 | 同步所引权威设计版本 | 历史记录未拆分（原记录合并） | Issue #12 SR-024 |
| 2026-11-25 | 0.1.7 | Codex / GPT-6 | 正文 | 同步本轮受影响的现行设计依据 | 历史记录未拆分（原记录合并） | Issue #12 SR-024 |
| 2026-11-26 | 0.1.8 | Codex / GPT-6 | §3、§5 | 记录固定输入的实测设计结论，分离设计 READY 与目标仓实施 Issue。 | 历史记录未拆分（原记录合并） | Issue #12、#21 |
| 2026-11-26 | 0.1.9 | GPT-6.2（ChatGPT） | §5 | 登记 ca-agent-demo 实施 Issue #252，并固定设计候选 SHA、目标 main SHA、AC 范围和非目标边界 | 完成 READY→跨仓实施 Issue 的追踪闭环，保持产品 AC NOT_RUN | Issue #26；ca-agent-demo #252 |
| 2026-11-26 | 0.1.10 | GPT-6.2（ChatGPT） | 头部、§5～§5.2 | 回填 ca-agent-demo PR #253 的受测 Commit、AC-024-01～07 实测 PASS、ZIP 身份、测试环境与结果；将 SR 状态转为 IN_PROGRESS，并记录独立 Review、PR CI 与合并待办 | 代码已推送但 PR 未合并；按 SR 状态机区分受测 PASS、代码集成和 VERIFIED，不提前宣称完成 | Issue #12；ca-agent-demo #252/#253 |
| 2026-11-26 | 0.1.11 | GPT-6.2（ChatGPT） | 头部、§5.1、§5.3 | 回填独立技术评审 Review #6070722615、AC-024-01～07 全 PASS 及 2,359 样例零差异；纠正 GitHub Review 身份为 PR 作者账号且状态仅 COMMENTED；登记 combined status pending、4 个 skipped checks、无 PR-triggered Run 和 branch-protection 读取限制 | 区分技术结论与 GitHub 独立身份审批、CI 门禁；合并前保持 IN_PROGRESS，不把 COMMENTED/SKIPPED 提升为 APPROVED/PASS | Issue #12；ca-agent-demo #252/#253；Review #6070722615；Issue comment #7186684869 |
| 2026-11-26 | 0.1.12 | GPT-6.2（ChatGPT） | 头部、§5、§5.3 | 回填 PR #253 正常合并、merge commit/main HEAD `25168db`、Issue #252 completed；确认 AC-024-01～07 全部满足并将 SR 转为 VERIFIED；保留 COMMENTED 与 SKIPPED 的真实记录，不宣称正式 APPROVE 或 CI PASS | 按 SR 状态机区分集成与验收；所有模块 AC 已有真实通过证据，PR 合并后达到 VERIFIED；不将非 AC 的 skipped workflow 误判为失败 | Issue #12；ca-agent-demo #252/#253；merge `25168db031e996bfa4de440c4156ae94f4e19bce`；AC-024-01～07 |
