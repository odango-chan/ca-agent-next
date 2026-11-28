# Python 工程工具链与实施基线规范

> 文档类型：工程治理规范  
> 文档版本：0.2.4  
> 状态：DRAFT（PR #115 mainline candidate；仅在 PR #115 合入 main、共享基线祖先关系核验通过且 Required Checks 配置完成后生效）  
> 修订日期：2026-11-28  
> 适用仓库：`odango-chan/ca-agent-next` 根 Python 工程  
> 设计与实施来源：[G02 Python 工程工具链与环境管理](../设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md)、[SR-028](../SR/SR-028-Python工程工具链与uv环境管理.md)、[Issue #96](https://github.com/odango-chan/ca-agent-next/issues/96)、[PR #99](https://github.com/odango-chan/ca-agent-next/pull/99)  
> 本规范追踪：[Issue #111](https://github.com/odango-chan/ca-agent-next/issues/111)；堆叠治理 PR：[PR #112](https://github.com/odango-chan/ca-agent-next/pull/112)（Draft）  
> 本文局部非目标：不自动迁移其他仓库，不改变 Agent/Host/Runtime 行为，不建立生产级供应链安全或包准入机制

## 1. 目的与原则

SR-028 的交付不是只供 SR-028 自己使用的一套工具，而是 `ca-agent-next` 根 Python 工程的共享工程工具链。SR-028 AC-028-01～10 已在 Issue #96 留存 PASS 证据；后续 SR 只要修改本仓 Python 源码、测试、脚本、依赖或 Python CI，就必须继承同一工具链基线。

**不得因为 PR #115 尚未合入 main，就允许其他 Python 实施分支回退 pip。** SR-028 的 uv 产品实现已选择性纳入唯一 mainline PR #115；共享策略门禁也在该 PR 中作为候选集成。不得再将 PR #99 或 PR #112 作为独立 mainline 合并入口，也不得把 SR-028 产品实施塞回设计 PR 的 Base 分支。

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

### 4.1 当前唯一 mainline 候选基线

截至 2026-11-28：

- SR-028 实施 PR #99 的 Head 为 83d23e8c04b1c05eb304c2a24a3392f6459ed0f1。其 13 个变更路径已逐文件对照 PR #115；核心六项实现文件（.github/workflows/review-context.yml、.github/workflows/sr003-plugin-ci.yml、.python-version、pyproject.toml、scripts/unittest_gate.py、uv.lock）Blob 完全一致，其他文档以 PR #115 的较新版本为准。
- PR #99 的独立技术复核 #6094704264 记录 IMPLEMENTED，并核验 AC-028-01～10 候选证据。该结论不替代 PR #115 当前 Head 的双平台复验，也不代表已合入 main 或 VERIFIED。
- 共享策略源 PR #112 的 P2-01/P2-02 已在 Head bd5f390f1386cb57cce1f451426ed2d28f6ef7e9 修复；Bootstrap Policy Check、Python Lock Consistency、Review Context 已成功，策略单元测试 45/45 PASS，SR-003 双平台回归仍须以该 Head 的最终结果为准。PR #112 是策略源分支，不再是独立集成入口。
- PR #115 integration/issue-50-mainline-convergence 是唯一集成候选。PR #115 合入 main 前，策略仍处于候选状态；不得从缺少 uv 基线的 main 或 #99/#112 旧源分支另起并行 Python 实施。若有明确授权的紧急工作，只能堆叠在 PR #115 当前 Head，并在 Issue #50/#111 记录范围与 SHA。

PR #115 的候选集成提交完成后，.github/python-toolchain-baseline.json 的 baseline.sha 必须指向一个已包含全部必需产品文件和策略文件的祖先提交；清单的 allowed_base_refs 只允许 main。策略文件维护例外只允许 PR #115（policy_control_bootstrap_prs），不得作为普通实施 PR 的长期豁免。

### 4.2 PR #115 合入后的基线生效

1. PR #115 合入 main 前，核对根 pyproject.toml、uv.lock、.python-version、scripts/unittest_gate.py、两个产品 Workflow、策略脚本/测试/清单和两个策略 Workflow 均存在；核对 SR-028 状态、Issue #96 证据及当前双平台回归。
2. 合入后重新读取 main 的完整 HEAD，确认清单 baseline.sha 是 main 的祖先，且 main 在该 SHA 上包含全部 required_base_files 和 required_policy_files。如果 PR 使用 squash/rebase 导致该祖先关系不成立，必须先更新清单的 baseline.sha 为 main 上包含同一完整文件集合的提交，再重新运行策略验证；在此之前不得声称共享策略已生效。
3. pull_request_target 可信策略只在 Workflow 进入默认分支后才会激活。策略脚本、清单和 Workflow 均来自默认分支，只读取 PR Base/Head Git 对象，不 checkout 或执行 PR Head 代码。
4. 主干应配置 Python Toolchain Policy / Python Toolchain Policy 与 Python Toolchain Policy Bootstrap / Python Lock Consistency 为 Required Checks。PR #115 的一次性 Bootstrap Policy Check 仅验证候选基线文件和策略单元测试；Branch protection/Ruleset 尚未配置前，不得声称这些检查已形成合并阻断。
5. 只有在 main 文件、祖先关系、可信 Workflow 和 Required Checks 均实际核验通过后，才把 main 记录为当前共享基线，并在 Issue #111 更新完整 SHA、生效时间和来源。

### 4.3 新建 Python 实施分支的强制步骤

**PR #115 合入 main 之前：**不创建新的独立 Python 实施分支。若有明确授权的紧急工作，必须从 PR #115 当前远端 Head 派生，并以该集成分支为 Base；先更新 Issue #50/#111 的检查点，不得从旧 main、PR #99、PR #112 或 PR #46 设计分支派生。

**PR #115 合入 main 且 §4.2 全部通过之后：**

1. 读取本规范、Issue #111、目标 SR 和对应设计基线。
2. 获取 main 最新远端 Head，记录完整 SHA；确认其包含根 pyproject.toml、uv.lock、.python-version、.gitignore、scripts/unittest_gate.py、产品 Workflow 和全部策略文件。
3. 从该 SHA 创建实施分支，记录分支名、远端分支引用、git rev-parse HEAD。
4. 用 git merge-base --is-ancestor <shared-baseline-sha> HEAD 确认共享基线祖先关系；检查 git diff --stat <shared-baseline-sha>...HEAD，确认没有意外带入其他 SR 的实施差异。
5. 新实施 PR 的 Base 指向 main；不得把其他 SR 的实施分支当作共享基线。
6. 若任一条件无法核验，停止 Python 实施并报告 PYTHON_TOOLCHAIN_BASELINE_MISSING。不得退回 pip，不得临时创建 requirements 文件绕过门禁。
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

## 9. 自动 CI 工具链门禁

### 9.1 Workflow 与可信策略快照

新增两个 Workflow：

- .github/workflows/python-toolchain-policy-trusted.yml：pull_request_target 可信策略。普通 PR 的策略脚本、清单和 Workflow 来自默认分支；只 fetch PR Base/Head Git 对象，不 checkout 或执行 PR Head 代码。它验证 Base freshness、共享基线祖先、必需文件、锁文件/依赖变更、Python Workflow 和新增命令。
- .github/workflows/python-toolchain-policy.yml：pull_request Bootstrap 与 Head 的 Python Lock Consistency。PR #115 的一次性 Bootstrap Policy Check 验证候选基线文件、固定工具链和策略单元测试；Python Lock Consistency 在存在根 Python 工程时运行 uv lock --check。

可信 Workflow 只有在进入默认分支后才会激活。PR #115 尚未合入 main 时，不能把 pull_request_target 检查描述为已经生效。策略文件由默认分支提供，普通实施 PR 不得修改策略脚本、基线清单、可信 Workflow 或策略测试；唯一策略维护例外由清单 policy_control_bootstrap_prs 明确列出 PR #115。

### 9.2 触发范围与检查内容

门禁检查：

1. 普通 Python 实施 PR 的 Base 必须为 main；Base freshness 检查将远端分支最新 SHA 与 PR 事件 Base SHA 比较，漂移即失败。
2. PR Base 必须是清单 baseline.sha 的后代，并包含 pyproject.toml、uv.lock、.python-version、统一 unittest gate、策略文件和固定 setup-uv action 的 Python Workflows；PR Head 也必须保留这些文件、固定解释器/uv 版本和根 .venv/ 忽略规则。
3. 根目录新增 requirements*.txt、requirements*.in、constraints*.txt/.in、Pipfile*、poetry.lock、pdm.lock、rye.lock、pixi.lock、Conda/Mamba 环境或锁文件时失败；PEP 751 pylock.toml / pylock.*.toml 同样禁止作为第二锁文件；嵌套测试 fixture 不按根依赖入口处理。
4. 新增/修改的可执行命令行不得使用 pip/pip-tools/Pipenv（包括 uv pip install/sync）、Poetry/Conda/Mamba/PDM/Rye/Pixi，不得裸运行 Python unittest/pytest/compileall/Agent Smoke 或根脚本；所有 uv run 命令（包括 ruff/mypy 等工具）必须在命令前同时使用 uv run --no-sync --locked；依赖同步命令必须带 --locked。
5. uv run --no-project 只允许可信门禁中的固定标准库检查器和专用自测命令；禁止通过命令拼接扩大例外，不得将该例外用于应用测试。Workflow run 的 YAML 引号和 shell 连续命令也必须纳入检测。
6. 所有新增/修改的 Python Workflow 必须在真实 steps[].uses 中使用清单固定 SHA 的 setup-uv Action，并在同一 Action Step 的 with.version 中显式固定 uv 版本；其他位置的相同字符串不能满足检查。
7. 禁止设置共享 UV_PROJECT_ENVIRONMENT，禁止 uv run/sync --system 或 --active 绕过 worktree 本地 .venv/。
8. pyproject.toml 中依赖、动态依赖声明、Python 版本、dependency-groups 或 uv 解析配置变化时，同一 PR 必须更新 uv.lock；Head 工作流执行 uv lock --check 验证锁文件与项目配置同步。
9. 策略测试覆盖允许/拒绝命令、每条 uv run、shell/YAML 引号、锁文件范围、路径范围、Base freshness、共享基线继承、真实 setup-uv Step 和策略文件变更。

### 9.3 合并门禁

当可信 Workflow 已进入默认分支并开始运行后，普通 PR 的目标分支应同时将以下两个 Check 配置为 Required：

- Python Toolchain Policy / Python Toolchain Policy：可信 Base 策略检查；
- Python Toolchain Policy Bootstrap / Python Lock Consistency：PR Head 的锁文件一致性检查。

PR #115 的一次性 Bootstrap Policy Check 只用于本次候选基线集成；其 Bootstrap Policy Check 与 Python Lock Consistency 在 PR #115 上应作为候选集成检查。PR #115 合入 main 后，Bootstrap Policy Check 在普通 PR 中跳过，不应继续作为必需项；后续普通 PR 使用上面两项常规 Required Checks。

**Workflow 通过不等于已启用合并阻断。** 仓库管理员必须在实际接收 PR 的目标分支 Branch protection / Ruleset 中配置 Required Checks；未配置前，CI 只能提供自动失败状态，不能保证 GitHub 拒绝合并。不得把“Workflow 已存在”误报成“分支保护已配置”。

本门禁只约束 Next 根 Python 工程，不替代 SR 的设计 READY、实施授权、模块 AC 或系统 EX，也不自动改变其他仓库的 CI。
## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-27 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 建立 Next 根 Python 工程共享 uv 工具链、实施分支继承、堆叠 PR、已有分支迁移和 Harness 提示词约束 | 避免 SR-028 尚未进入 main 时其他 Python 实施分支绕过 uv，形成多套依赖入口 | Issue #111；Issue #96；PR #99；SR-028；G02 |
| 2026-11-27 | 0.2.0 | GPT-6.2（ChatGPT） | §9、修订记录 | 增加 Python Toolchain Policy CI、可信 Base 策略快照、命令/锁文件/基线继承检查与 Required Check 配置说明 | 将 uv 共享基线从提示词约束提升为自动 PR 检查，避免 PR 自行修改策略绕过门禁 | Issue #111；PR #112；PR #99 |
| 2026-11-27 | 0.2.1 | GPT-6.2（ChatGPT） | §9.2、修订记录 | 收紧 `--no-project` 例外，仅允许门禁自身标准库测试；增加 Windows `py` 裸入口检测 | 避免通过 `uv run --no-project` 绕开项目锁定环境 | Issue #111；PR #112 |
| 2026-11-27 | 0.2.2 | GPT-6.2（ChatGPT） | §9、修订记录 | 增加 `pull_request_target` 可信 Base 门禁、策略文件保护、Python Workflow 固定版本检查、`uv lock --check` 和 `uv sync --locked` 检查 | 防止 PR 修改自身 Workflow 绕过可信策略，并验证锁文件与配置一致 | Issue #111；PR #112 |
| 2026-11-27 | 0.2.3 | GPT-6.2（ChatGPT） | §9.1、§9.3、修订记录 | 明确 `pull_request_target` 从仓库默认分支加载 Workflow/策略，且必须进入默认分支后才激活；区分 PR #112 Bootstrap Required Check 与常规 PR Required Checks | 避免误判 PR Base Workflow 为可信来源，并明确过渡期实际门禁边界 | Issue #111；PR #112 |
| 2026-11-28 | 0.2.4 | GPT-6.2（ChatGPT） | §1、§4、§9、修订记录 | 将 SR-028 产品与共享策略收敛到唯一 PR #115；改为 main 合入后生效的 baseline.sha 祖先关系；P2-01/P2-02 修复并纳入每条 uv run、YAML run 引号和真实 setup-uv Step 检查 | 防止旧源分支成为第二集成入口，避免 PR #112 的旧 Base SHA 在新主线中失效 | Issue #50/#111；PR #99/#112/#115 |
