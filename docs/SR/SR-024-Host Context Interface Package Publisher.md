# SR-024：Host Context Interface Package Publisher

> 文档类型：软件需求（SR）
> SR 版本：0.1.10
> 状态：IN_PROGRESS（设计 READY；目标仓实现已推送，PR #253 OPEN；AC-024-01～07 在受测 PR head 实测 PASS，等待独立评审与合并）
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
- 实施 Issue：[ca-agent-demo #252](https://github.com/odango-chan/ca-agent-demo/issues/252)，保持 OPEN，等待独立评审和 PR 合并；固定设计 SHA：`0fdd991f203f8468be155c35d81254eb84cd8ce5`；目标仓启动基线：`57e277ff9094dad93543df46910a12a1dbbaf560`。
- 实施 PR：[ca-agent-demo #253](https://github.com/odango-chan/ca-agent-demo/pull/253)，OPEN、非 Draft、目标 `main`、`mergeable=true` / `mergeable_state=clean`；未合并。实施分支：`feature/issue-252-sr-024-host-context-publisher`。受测 Commit 与当前远端 head：`99b273136d24d0593038821ab52d613aee8743b0`。变更严格为本 SR 授权的两个文件：`scripts/publish_host_context_interface_package.py`、`tests/test_host_context_interface_package.py`。
- **实施状态：IN_PROGRESS。** 代码已实现并推送，AC-024-01～07 均在受测 PR head 上有实际执行证据；PR 尚未合并，因此尚未达到 IMPLEMENTED。合并后复核集成基线，再按 SR 管理规范决定是否转 VERIFIED。替代关系：无。

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
- GitHub 当前未返回该 head 的 PR-triggered Workflow Run；可见的 Release-request `create` 事件运行及其 Jobs 均为 `SKIPPED`，不得记作 CI PASS。
- PR 当前没有独立 Review。PR 作者不能批准自己的 PR；已在 PR #253 请求独立 Reviewer。未执行合并。
- Issue #252 保持 OPEN；独立 Reviewer 正式审查/批准（如仓库规则要求）及所需 PR checks 是合并前事项。

### 5.2 职责边界

本 SR 仅完成 Host Context Interface Package Publisher。Studio ZIP Import 已由 Studio #267 完成，但 `source.sourceStatus=DEVELOPMENT_FIXTURE` 的 Lock provenance 和 BuildRequest / Compiler 消费集成仍归 SR-016 / Studio #269。不得把 PR #253 描述为 Studio 集成、Compiler 产品集成、Host Trust/Admission 或生产级发布完成。


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
