# Python 工程工具链与实施基线规范

> 文档类型：工程治理规范  
> 文档版本：0.1.0  
> 状态：DRAFT（本规范由 Issue #111 跟踪；评审合并前作为本任务明确授权的过渡执行规则，合并后成为 Next 根 Python 工程的权威工具链与分支继承规范）  
> 修订日期：2026-11-27  
> 适用仓库：`odango-chan/ca-agent-next` 根 Python 工程  
> 设计与实施来源：[G02 Python 工程工具链与环境管理](../设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md)、[SR-028](../SR/SR-028-Python工程工具链与uv环境管理.md)、[Issue #96](https://github.com/odango-chan/ca-agent-next/issues/96)、[PR #99](https://github.com/odango-chan/ca-agent-next/pull/99)  
> 本规范追踪：[Issue #111](https://github.com/odango-chan/ca-agent-next/issues/111)；堆叠治理 PR：[PR #112](https://github.com/odango-chan/ca-agent-next/pull/112)（Draft）  
> 本文局部非目标：不自动迁移其他仓库，不改变 Agent/Host/Runtime 行为，不建立生产级供应链安全或包准入机制

## 1. 目的与原则

SR-028 的交付不是只供 SR-028 自己使用的一套工具，而是 `ca-agent-next` 根 Python 工程的共享工程工具链。SR-028 AC-028-01～10 已在 Issue #96 留存 PASS 证据；后续 SR 只要修改本仓 Python 源码、测试、脚本、依赖或 Python CI，就必须继承同一工具链基线。

**不得因为 PR #99 尚未合入 main，就允许其他 Python 实施分支继续使用 pip。** 通过 PR 堆叠和共享基线分支继承工具链，不要求提前合并 PR #99，也不允许把 SR-028 实施代码塞进设计 PR 的 Base 分支。

本规范只定义工程工具链、实施分支继承和验收入口；不替代各 SR 的设计、READY、实施授权和 Acceptance。

## 2. 唯一工具链基线

Next 根 Python 工程的权威配置为：

| 项目 | 唯一基线 |
|---|---|
| 项目依赖声明与构建元数据 | 根目录 `pyproject.toml` |
| 依赖锁文件 | 根目录 `uv.lock`，唯一锁文件 |
| Python 包管理/运行工具 | uv CLI `0.13.10` |
| 默认开发解释器 | CPython `3.14.6`，由根目录 `.python-version` 指定 |
| 包元数据下限 | `requires-python >=3.11`；不代表 3.11～3.13 已通过版本矩阵 |
| 项目虚拟环境 | 每个 checkout/worktree 独立的根目录 `.venv/` |
| 开发/测试依赖 | PEP 735 `[dependency-groups].dev` |
| Plugin 额外依赖 | 既有 `[project.optional-dependencies].plugins` |
| CI uv 安装 | `astral-sh/setup-uv@1db35dd8eee11c5894872e0b383ae6c406cf738d`，并显式指定 `0.13.10` |

不得以 SR 编号、实施批次、分支或 worktree 为理由建立第二套 Python 项目依赖入口。根项目不得新增 `requirements.txt`、pip-tools constraints、Poetry/Conda 锁文件或另一份依赖锁。不得在根项目 CI、本地验收或 Harness 提示词中使用 `pip install`、`python -m pip install` 或裸 `python` 作为项目依赖安装/测试入口。

历史 SR、历史受测 SHA 和历史报告中的 pip 命令是不可改写的历史记录，不得为了统一入口而篡改；它们也不得被复制为当前分支的新执行命令。

## 3. 适用范围

本规范适用于任何修改下列内容的 Next 实施分支或 PR：

- `src/**` 中的 Python 源码；
- `tests/**` 中的 Python 测试、测试辅助代码或测试数据生成脚本；
- `scripts/**` 中由根 Python 工程运行的脚本；
- 根目录 `pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`；
- 调用 Python 安装、测试、Smoke、Review Context 或其他根项目脚本的 GitHub Actions Workflow；
- 同时包含上述内容的跨模块、跨 SR 或系统集成实施。

纯文档变更、只修改独立 Go Plugin 且不触及根 Python 测试/脚本/Workflow 的分支，不因本规范而强制增加 Python 依赖安装步骤；但不得借此引入第二套根 Python 依赖管理方式。

本规范**不自动适用于** `ca-agent-demo`、`ca-agent`、`ca-runtime`、`ca-skills`、Compiler、Skill Studio、OpenAMSM Plugin、Mock AMF 或其他独立仓库。跨仓迁移必须由各自的 SR/Issue 明确授权和验收。

## 4. 共享实施基线与分支继承

### 4.1 当前过渡基线

截至 2026-11-27：

- SR-028 实施 PR [#99](https://github.com/odango-chan/ca-agent-next/pull/99) 的 Head 为 `83d23e8c04b1c05eb304c2a24a3392f6459ed0f1`，Base 为 PR #46 Head `93f1389e7c5968cd30e8a74137207094864ecca0`。
- PR #99 为 OPEN、未合并；其 13 文件实施差异必须保持独立，不得把本规范的治理改动追加到 PR #99。
- 本规范分支 `docs/issue-111-shared-uv-implementation-baseline` 从上述 PR #99 Head 精确派生，并通过堆叠 PR 将规范文件与 SR-028 产品实施隔离。

**在 PR #99 尚未集成、且本规范堆叠分支仍是当前已核验共享基线时，新的 Next 根 Python 实施分支必须从 `docs/issue-111-shared-uv-implementation-baseline` 的最新远端 Head 派生；对应实施 PR 的 Base 必须是该分支或其后继共享基线分支。** 不得从缺少 uv 工具链的 `main`、仅含设计的 PR #46 Base 分支或其他旧分支直接开始 Python 实施。

当前分支名与 SHA 是过渡快照，不是永久常量。开始每项任务前必须从 Issue #111 和本规范重新读取当前共享基线指针，并核对远端实际 Head；不得照抄历史 SHA。

### 4.2 共享基线的后续切换

1. PR #99 合入其设计集成目标后，先核验目标分支确实包含根 `pyproject.toml`、`uv.lock`、`.python-version`、统一 Workflow 和测试门禁，且 PR #99 的产品验收证据与文件差异完整保留。
2. 本规范堆叠 PR 随后必须按实际合并结果更新 Base/分支关系；若合并策略造成原始分支不再是目标分支祖先，建立继承最新集成基线的后继分支并按受控方式重放治理提交。不得假定 squash merge 自动保留原分支 SHA。
3. 如果 PR #46、PR #97 或其他直接设计/治理依赖先推进，导致共享分支落后于当前获准的设计集成基线，则先建立刷新后的共享基线：以最新获准集成 Head 为起点，受控重放 SR-028 实施提交，核验 PR #99 原始分支不变、实施文件差异仍符合预期、CI/Review 重新通过，再让新实施分支继承该后继基线。
4. 只有当包含 uv 工具链的共享基线已经合入当前主集成分支，并且该分支的文件与 CI 入口通过实际核验后，才可将该主集成分支作为新的默认共享基线。不能仅凭 PR 显示 MERGED 就跳过文件和 CI 核验。
5. 每次切换都必须在 Issue #111 更新共享基线分支、完整 SHA、来源 PR、Base、核验结果和生效时间；README/Agent/本规范中的临时指针同步刷新。

### 4.3 新建 Python 实施分支的强制步骤

在任何代码修改前：

1. 读取本规范、Issue #111、目标 SR 和对应设计基线。
2. 获取当前共享基线分支的最新远端 Head，并记录完整 SHA。
3. 确认该 Head 包含根 `pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`、`scripts/unittest_gate.py` 和当前 Python CI Workflow。
4. 从该 Head 创建实施分支；记录 `git rev-parse HEAD`、分支名和远端分支引用。
5. 用 `git merge-base --is-ancestor <shared-baseline-sha> HEAD` 确认共享基线确实是当前分支祖先；并检查 `git diff --stat <shared-baseline-sha>...HEAD`，确认没有意外带入其他 SR 的实施差异。
6. PR Base 指向当前共享基线分支或明确记录的后继集成分支；不得将 Python 实施 PR 直接指向缺少 uv 的设计分支或旧 main。

任一条件无法核验时，停止 Python 实施并报告 `PYTHON_TOOLCHAIN_BASELINE_MISSING`。不得退回 pip，不得临时创建 requirements 文件绕过门禁。

## 5. 本地、测试与 CI 命令

从仓库根目录执行。首次安装或依赖声明变化后：

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv lock --check
```

同步成功后，测试、Smoke 和项目脚本一律禁止隐式同步，统一使用：

```bash
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
uv run --no-sync --locked --group dev --extra plugins python scripts/review_context.py --help
```

具体 SR 可增加针对性测试，但不得用针对性测试替代其要求的统一门禁。修改依赖时必须在同一提交中审阅 `pyproject.toml` 与 `uv.lock`；先执行 `uv lock` 更新锁，再执行 `uv lock --check`、统一测试门禁和目标 SR AC。不得在 CI 中自动改写锁文件；CI 必须使用 `--locked`。

所有 Python Workflow 必须使用固定的 setup-uv action commit 和显式 uv `0.13.10`，安装与运行命令遵守 SR-028 已验收入口。不能通过增加一条仅在某个分支运行的 pip Workflow 形成旁路。

### 5.1 Worktree 隔离

- 每个 Git worktree 使用自己目录下的 `.venv/`；禁止多个 worktree 共用虚拟环境或 site-packages。
- 不设置共享的 `UV_PROJECT_ENVIRONMENT`，不使用 `--system`、`--active` 绕过项目环境。
- uv 下载缓存可以由 uv 自身复用，但缓存不是虚拟环境。
- 新增或改变依赖、Python 版本、安装入口或 Workflow 时，按对应 SR Acceptance 运行所要求的隔离与回归验证；不得把 SR-028 已通过的 AC 当作其他分支的自动 PASS。

## 6. 已存在分支的迁移与审计

既有 Python 分支不因本规范发布而自动视为合规。每个分支继续实施前必须审计：

- 是否包含当前共享基线的完整祖先关系；
- 是否具有唯一 `pyproject.toml`/`uv.lock`、正确 `.python-version` 和当前统一 Workflow；
- 是否仍有新增加的 pip 安装、requirements 文件或第二套锁文件；
- 本地/CI 命令是否使用 uv 的 locked 入口；
- worktree 是否使用独立 `.venv/`；
- PR Base 与共享基线是否一致，累积 diff 是否只包含本 SR 允许的文件。

若缺少共享基线：

1. 先停止该分支上的新 Python 实施，不得继续使用 pip。
2. 对个人且未共享的短期分支，可从最新共享基线建立新分支，并只重放该分支自身、可独立识别的提交。
3. 对多人共享、受保护、已发布或属于他人工作的分支，不得擅自 rebase、强推或改写历史；先提出迁移方案并取得必要授权。
4. 迁移后重新核对 Base、merge-base、完整 diff、冲突解决、锁文件和 CI。不得把无关设计/实施提交带入当前 PR。
5. 无法安全迁移时报告 `PYTHON_TOOLCHAIN_BASELINE_MIGRATION_BLOCKED`，等待处理；绝不以 pip 作为临时豁免。

## 7. Harness 与交付要求

每个 Next 根 Python 实施 Goal 的提示词必须显式包含：

- 当前共享基线分支、完整 Head SHA、来源 PR、目标 PR Base；
- 新实施分支名称和从共享基线派生的证明；
- 根 Python 唯一工具链与当前安装/测试命令；
- 依赖变化时同步更新 `pyproject.toml`/`uv.lock` 的要求；
- worktree 独立 `.venv/` 要求；
- 对应 SR 的逐项 AC、目标测试和停止条件；
- 禁止 pip/requirements 第二入口及禁止基线缺失时回退；
- 每个独立工作项完成后即时 Commit、Push，并核对远端 SHA；
- PR 不得自动合并；合并、改 Base、rebase/强推和发布仍按各自授权边界执行。

Goal 在开始前建立 GitHub 检查点，执行期间每完成一个独立工作项立即更新并读回核验。工具链基线缺失、设计 SHA 漂移或分支继承无法证明时，停止受影响工作，不阻塞与其无关的文档/非 Python 任务。

## 8. 变更边界

本规范不改变 SR-028 AC-028-01～10 的定义、测试结果或 VERIFIED/IMPLEMENTED 状态判据；不要求重跑已通过的 SR-028 产品验收。它把已验收的工具链作为同一仓库其他 Python 工作的共享前置条件。

本规范不改变其他仓库的包管理器，不规定独立 Go Plugin 的 Go 依赖管理，也不要求所有 SR 都执行 Python 测试。只有触及本规范第 3 节范围的 Next 分支才必须继承 uv 基线。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Next 根 Python 工程共享 uv 工具链、实施分支继承、堆叠 PR、已有分支迁移和 Harness 提示词约束 | 避免 SR-028 尚未进入 main 时其他 Python 实施分支绕过 uv，形成多套依赖入口 | Issue #111；Issue #96；PR #99；SR-028；G02 |
