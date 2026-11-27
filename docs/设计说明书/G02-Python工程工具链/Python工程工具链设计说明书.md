# G02：Python 工程工具链与环境管理设计说明书

> 文档类型：工程治理功能设计说明书  
> 文档版本：0.2.3\
> 状态：设计第三轮自评候选 / REVIEW_REQUESTED；SR-028 主状态仍 DRAFT、实施 NOT_READY、uv 产品验收 NOT_RUN\
> 修订日期：2026-11-27\
> 功能节点：G02 Python 工程工具链与环境管理  
> 关联需求：[IR-007](../../IR/IR%20总登记册.md#ir-007)、[SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md)  
> 追踪 Issue：[ca-agent-next #35](https://github.com/odango-chan/ca-agent-next/issues/35)  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级供应链安全治理、跨仓批量迁移、Agent Runtime 架构变更

## 0. 设计评审入口（2026-11-26）

本设计与 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) 一同提交独立设计评审，关联 [Issue #35](https://github.com/odango-chan/ca-agent-next/issues/35) / [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)。审查 uv/pin/lock、Python 3.14.6 基线、Worktree 隔离、setuptools 不变、GitHub Actions 与 AC-028-01～09 的实际命令及退出条件。

**设计待评审与实施 READY 分离：**PR #32 的评审上下文 CI 已完成，不构成 uv 迁移验收；SR-028 保持 DRAFT。评审未通过不得生成实施提示词，不开展跨仓批量迁移或不必要的生产供应链 DFX。

## 1. 目标

为 `ca-agent-next` 根 Python 项目建立单一、可复现、按 worktree 隔离的工程工具链，统一 Python 解释器、项目元数据与依赖声明、依赖解析和锁文件、本地虚拟环境、脚本/测试命令以及 GitHub Actions 安装和测试入口。

本设计只管理开发、构建和测试环境，不改变 Agent Core 的运行时架构、业务行为或 Python 公共 API。

## 2. 现状与问题

当前根目录 `pyproject.toml` 定义 distribution `ca-agent-next`、版本 `0.1.0`、`requires-python >=3.11`，使用 `setuptools.build_meta`，核心运行时 `dependencies=[]`。SR-003 的 `[project.optional-dependencies].plugins` 提供 `ruamel.yaml>=0.18,<0.19` 与 `jsonschema>=4.23,<5`。保留现有 extra 及其约束，完整测试显式选用 `dev` 和 `plugins`。SR-002 已在 CPython 3.14.6 上完成模块验收。

SR-001 的 PR #32 需要 PyYAML 执行仓库内评审上下文脚本和测试；当前实现由 Workflow 临时执行 pip 安装，依赖未进入项目元数据。实施报告还记录了共享 Python 环境被另一 worktree 的 editable 安装污染，导致 distribution metadata 测试失败。

问题不是 setuptools 不合适，而是缺少统一的环境和依赖锁定入口。本设计保留 setuptools，只引入 uv 管理 Python 项目的解析、同步和命令执行。

## 3. 设计决策

### 3.1 工具职责

| 工具/文件 | 唯一职责 |
|---|---|
| `pyproject.toml` | PEP 621 项目元数据、Python 版本约束、运行时依赖、开发依赖组、构建后端和 uv 工具版本要求 |
| `uv.lock` | 由 uv 根据 pyproject.toml 生成的解析结果；提交到 Git，作为 CI/本地同步的可复现依据 |
| `.python-version` | 本仓开发与 CI 的解释器基线；首版固定为 CPython 3.14.6，与 SR-002 已记录的验收解释器一致 |
| `.venv/` | 当前 checkout/worktree 独占的项目虚拟环境；不提交 Git |
| uv CLI | 依赖锁定、环境同步、解释器安装和项目命令执行 |
| `astral-sh/setup-uv` | GitHub Actions 中安装指定 uv CLI 版本并启用官方缓存 |

uv 不替换构建后端。当前构建后端继续使用：

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

### 3.2 Python 版本

- `pyproject.toml` 继续声明 `requires-python = ">=3.11"`，不改变 SR-002 已冻结的包元数据约束。
- `.python-version` 首版文件内容精确为 `3.14.6`（纯文本、无前缀/引号/注释），作为本仓开发和 CI 的实际验收解释器。
- CI 记录实际 `python --version`。
- `requires-python >=3.11` 不等于 3.11、3.12、3.13 等版本矩阵已通过；除非另有 Acceptance，不得宣称全版本兼容性已验证。
- 改变 `.python-version` 属于工程基线变更，必须更新 SR-028 证据并执行完整测试，不允许因 uv 自动下载新版本而静默改变验收解释器。

### 3.3 依赖分组

运行时依赖与开发/测试依赖必须分离：

- `[project].dependencies` 只放 Agent Core 安装后实际运行所需的第三方包。当前继续为空，不因 SR-001 工具脚本引入 PyYAML。
- `[dependency-groups].dev` 放仓库开发、测试和 CI 工具依赖。SR-001 使用的 PyYAML 放入该组，首版约束为 `PyYAML>=6.0,<7`。
- PEP 735 dependency groups 不进入 wheel 的运行时依赖元数据。
- 新增运行时依赖必须由相应产品 SR/设计确认；不得把开发工具放进 `dependencies`，也不得为了让脚本可运行而扩大 Agent Core 运行时依赖。

首版 pyproject 目标增量：

```toml
[dependency-groups]
dev = [
    "PyYAML>=6.0,<7",
]

[tool.uv]
required-version = "==0.13.10"
```

原有 `[build-system]`、`[project]` 的 name/version/requires-python/dependencies 和 setuptools package discovery 配置保持不变；新增开发依赖组和 uv 配置不构成运行时依赖。

### 3.4 uv 与锁文件

- 本设计基线日期为 2026-11-26，uv CLI 固定为 `0.13.10`。
- `pyproject.toml` 的 `[tool.uv].required-version` 固定要求 `==0.13.10`；CI 的 setup-uv action 显式安装同一 CLI 版本。
- `uv.lock` 是唯一锁文件，必须提交。不得另建 requirements.txt、pip-tools constraints 或第二套依赖锁。
- 依赖声明变化时，在本地执行 `uv lock`，审阅 pyproject.toml 与 uv.lock 的同一提交，再运行完整测试。
- CI 使用 `--locked`：锁文件与项目声明不一致时直接失败，不得在 CI 中自动重写 uv.lock。
- `uv.lock` 使用 uv 原生格式。允许其原生记录 package source、version、marker 和锁定所需元数据；不另建项目自定义 SHA-256 清单、签名、Trust Registry 或包准入机制。

### 3.5 Worktree 环境隔离

- 每个 Git worktree 在自己的工作目录创建独立 `.venv/`；不得让多个 worktree 指向同一个虚拟环境目录。`uv sync` 默认将当前项目安装到该环境（项目开发模式），因此 distribution metadata 必须来自当前 checkout。
- `.venv/` 必须作为独立行追加到仓库 `.gitignore`，不得覆盖或删除现有 ignore 规则；不得提交 `.venv/`。实施时以 `git check-ignore .venv/pyvenv.cfg` 验证。
- 不设置共享的 `UV_PROJECT_ENVIRONMENT`；项目命令不得使用 `--system`、`--active` 或其他绕过项目环境的选项。
- 不得在系统 Python 中执行 `pip install -e .`，不得依赖另一 worktree 安装的 editable distribution。
- uv 的下载缓存可由 uv 自身跨 worktree 复用；缓存不等于虚拟环境，不共享 site-packages。
- 每个 worktree 执行 `uv sync` 后，当前项目 distribution metadata 必须来自当前 checkout，不能读取另一 worktree 的安装信息。

### 3.6 统一命令入口

从仓库根目录执行。实施者首次添加依赖组后用 `uv lock` 生成锁文件，与 pyproject.toml 一起提交。下列命令面向已有锁文件的干净 checkout 和 CI。

```bash
uv python install
uv sync --locked --group dev --extra plugins
```

测试和 Smoke：

```bash
uv run --locked --group dev --extra plugins python -m unittest discover -s tests -v
uv run --locked --group dev --extra plugins python -m ca_agent_next --smoke
```

目标分支已包含 SR-001 生成器。用同一环境检查 CLI，真实 PR 的 Summary 与三文件 Artifact 另由 AC-028-08 检查。

```bash
uv run --locked --group dev --extra plugins python scripts/review_context.py --help
```

锁文件检查：

```bash
uv lock --check
```

依赖更新时先编辑 pyproject.toml，再执行 `uv lock`，审阅锁文件差异后提交两者；普通测试和 CI 不得使用不带 `--locked` 的命令隐式更新锁文件。

### 3.7 GitHub Actions

setup-uv 的固定调用配置：

```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@1db35dd8eee11c5894872e0b383ae6c406cf738d # v10.4.0
  with:
    version: "0.13.10"
```

- 使用官方 `astral-sh/setup-uv` action；本设计基线采用 action v10.4.0 的不可变 commit `1db35dd8eee11c5894872e0b383ae6c406cf738d`，并显式设置 `version: "0.13.10"`。
- 使用 `uv python install` 从 `.python-version` 安装项目解释器。
- 使用 `uv sync --locked --group dev --extra plugins` 安装当前项目及开发依赖。
- 测试和项目脚本使用 `uv run --locked --group dev --extra plugins ...`。
- Workflow 不得通过 `pip install PyYAML`、`pip install -e .` 或全局 site-packages 临时补依赖。
- 可使用 setup-uv 自带的缓存；不另写自定义包缓存协议。

首版 CI 命令顺序（setup-uv action 已完成后）：

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv run --locked --group dev --extra plugins python -m unittest discover -s tests -v
uv run --locked --group dev --extra plugins python -m ca_agent_next --smoke
```

### 3.8 与 SR-001 Workflow 的衔接

[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) 已合入恢复分支（`7a0fac41e573021207ab8201bbc718718c451e50`）。目标树已有 `.github/workflows/review-context.yml`、`scripts/review_context.py`、`tests/test_review_context.py` 和 SR-003 Plugin 回归工作流。SR-028 在独立实施 PR 迁移安装入口。AC-028-07 核验完整测试与 Smoke；AC-028-08 在同一受测提交的真实 PR Run 核对生成器、Summary 和三份规定文件。

保留 `.github/workflows/sr003-plugin-ci.yml` 的 Linux/Python 3.12 和 Windows/Python 3.14 矩阵、Go Echo 构建及证据步骤。该工作流迁移安装和测试入口时，为每个任务的 uv sync/run 显式传入 `--python` 和矩阵解释器，保留 `--locked --group dev --extra plugins`；根环境和 Review Context 使用项目的 3.14.6。完整回归的 pull_request paths 至少覆盖 pyproject.toml、uv.lock、.python-version、src/**、tests/**、examples/echo/**、scripts/review_context.py、docs/SR/SR-003-*、.github/workflows/review-context.yml 及 .github/workflows/sr003-plugin-ci.yml 自身。逐类单文件变更均应触发两项矩阵任务。只改 Review Context workflow、`.python-version` 或 `uv.lock` 时也须能在 pull_request 上找到两项 Job。

**AC-028-07 跨 OS 无猜测命令参考**：新的 SR-003 regression Job 在 checkout + 固定 setup-uv action 之后，分别在 `ubuntu-latest` 的 `3.12` 和 `windows-latest` 的 `3.14.6` 运行。为了不让默认 .python-version 的 3.14.6 覆盖 Linux 3.12，两个矩阵单元都使用显式 `--python`。以下是**拟实施的 Workflow 步骤示例**，并非已运行 CI；用 `shell: bash` 使 Windows/Linux 使用同一变量语法（保留现有 Go Echo 独立 Go 构建；compileall 与 Python 证据生成步骤通过已安装的矩阵 Python 运行）：

```yaml
- name: Install matrix Python
  shell: bash
  run: uv python install "${{ matrix.python-version }}"
- name: Sync and test with matrix Python
  shell: bash
  run: |
    PY="$(uv python find '${{ matrix.python-version }}')"
    uv sync --python "$PY" --locked --group dev --extra plugins
    uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -v
    uv run --python "$PY" --locked --group dev --extra plugins python -m ca_agent_next --smoke
```

若目标 Job 仍沿用 PowerShell，则应明确使用 `$PY = (uv python find $env:PYTHON_VERSION)` 并将 `$PY` 传给每个 `uv ... --python`；不得把 Bash `$PY` 原样当 PowerShell 变量，也不得执行隐式默认解释器来替代矩阵。仅更新 `.github/workflows/review-context.yml` 的真实 PR 仍必须触发 `sr003-plugin-ci.yml` 的两项 Job，且从实际 Actions 日志核对解释器和测试总数，不能把上述 YAML 示例计为 AC PASS。
迁移前的成功日志只证明原环境。

## 4. 本地与 CI 流程

### 4.1 新 worktree

1. 创建 worktree 后，在该 worktree 根目录运行 `uv python install`。
2. 运行 `uv sync --locked --group dev --extra plugins`，由 uv 在当前 worktree 创建 `.venv/`。
3. 通过 `uv run --locked --group dev --extra plugins` 运行测试、Smoke 和仓库脚本。
4. 不复制其他 worktree 的 `.venv`，不复用其 editable 安装。

### 4.2 依赖更新

1. 修改 `pyproject.toml` 中明确归属的运行时依赖或 dependency group。
2. 执行 `uv lock` 更新 `uv.lock`。
3. 审阅直接/传递依赖变化和 Python marker。
4. 执行 `uv lock --check`、`uv sync --locked --group dev --extra plugins`、完整 unittest 和 Smoke。
5. 在同一 Commit 提交 pyproject.toml 与 uv.lock；CI 只执行 locked 安装，不重新解析。

### 4.3 CI

1. Checkout 当前 PR HEAD。
2. 通过固定版本的 setup-uv action 安装 uv 0.13.10。
3. 按 `.python-version` 安装 CPython 3.14.6。
4. 运行 locked sync。
5. 运行完整 unittest、Host Smoke 和本 PR 所需的仓库脚本。
6. 任一锁文件漂移、依赖缺失、测试失败或环境创建失败均使 Job 失败；不得降级为 pip 临时安装。

## 5. 兼容性与责任边界

- 不修改 Agent Core、Host、Model Loop、Runtime 的运行时架构或公开 API。
- 不改变 distribution 名称 `ca-agent-next`、import package `ca_agent_next`、版本 `0.1.0`、`requires-python >=3.11`、setuptools build backend 或当前空运行时依赖集合。
- 不把 PyYAML 或其他开发工具放入 Agent Core 运行时依赖。
- 不迁移 ca-agent-demo、ca-agent、ca-runtime、Compiler、Skill Studio 或其他仓库；其他仓库采用 uv 必须单独登记并核对其目标仓构建/发布边界。
- 不新增 Docker/容器化开发环境、私有包代理、企业制品库、供应链安全平台、包签名、Trust Registry、生产级依赖扫描或多平台完整 Python 版本资格矩阵。
- uv.lock 的标准锁定语义不是新增业务 Artifact 完整性机制；不得再造自定义 hash/signature 流程。
- 本 SR 保证项目运行时/开发依赖解析与虚拟环境可复现；不承诺对 setuptools 等隔离构建环境依赖或 wheel 字节级产物提供可复现构建，也不新增构建供应链治理。

## 6. 实施阶段与依赖

| 阶段 | 范围 | 依赖 | 说明 |
|---|---|---|---|
| D0 | 设计评审 | 无 | 本文与 SR-028 评审通过后，SR-028 才可 READY |
| I1 | 根 Python 项目采用 uv | SR-028 READY、独立实施 Issue | pyproject、uv.lock、.python-version、.gitignore、测试命令 |
| I2 | GitHub Actions 迁移 | I1；目标分支含已合并的 SR-001 和 SR-003 工作流 | 更新 review-context Workflow，运行完整测试与生成器，禁止改动 SR-001 分支 |
| I3 | 环境隔离验收 | I1 | 至少两个独立 worktree 验证 .venv 与 distribution metadata 不互相污染 |

I1 与 I3 可在 SR-028 实施 Issue 内按依赖顺序执行；I2 只在 SR-001 Workflow 已进入目标分支后执行。任何阶段依赖未满足时只暂停对应阶段/AC，不把无关设计评审阻塞。

## 7. 验收映射

具体验收 ID、命令和证据要求以 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) 为准。本设计不将文档评审或示例命令视为实现 PASS。

## 8. 参考

- [uv 官方文档：Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [uv 官方 CLI：uv sync / uv run / uv lock](https://docs.astral.sh/uv/reference/cli/)
- [uv 0.13.10 Release](https://github.com/astral-sh/uv/releases/tag/0.13.10)
- [setup-uv v10.4.0 Release](https://github.com/astral-sh/setup-uv/releases/tag/v10.4.0)

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 新建 G02 Python 工程工具链与环境管理设计；固定 uv、锁文件、依赖分组、Python 基线、worktree 隔离、CI 入口和 SR-001 Workflow 阶段依赖 | 解决共享 Python 环境污染和 Workflow 临时安装未声明依赖的问题，同时保持 setuptools 与 Agent Core 运行时依赖边界 | Issue #35；IR-007；SR-028 |
| 2026-11-26 | 0.1.1 | GPT-6.2（ChatGPT） | §3.6、§6 | 明确 review_context.py CLI 只在 PR #32 集成后可执行，避免将尚不存在于当前基线的脚本列为 I1 命令 | 消除 SR-028 独立 I1 可实施性与 SR-001 下游依赖之间的命令歧义 | Issue #35；PR #32；SR-028 |
| 2026-11-26 | 0.1.2 | GPT-6.2（ChatGPT） | §3.2、§3.5、§3.7、§5 | 固定 `.python-version` 文件内容、`.gitignore` 追加方式、setup-uv 精确 YAML 调用和 `uv sync` 项目安装语义；限定可复现承诺边界 | 进一步消除 Harness 对文件内容、CI action 配置、worktree editable 安装及构建可复现范围的猜测 | Issue #35；IR-007；SR-028 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 文档头、设计评审、修订记录 | 新增设计待评审入口、评审覆盖与实施门禁隔离 | 纳入统一 23 SR 设计评审批次，避免把历史 CI 当成 uv 迁移 PASS | Issue #12/#35；SR-028 |
| 2026-11-26 | 0.1.4 | Codex / GPT-6 | §2、§3.5～3.8、§6 | 对齐实际工作流、plugins extra、首次锁定与干净安装命令 | 使完整测试在新 worktree 能发现并加载 Plugin 回归，保留双平台覆盖 | Issue #12/#35，PR #46，SR-028 |
| 2026-11-27 | 0.2.0 | Codex / GPT-6 | §3.8 | 固定完整回归触发范围 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.1 | Codex / GPT-6 | §3.8 | 补全双平台路径触发范围 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.2 | GPT-6（ChatGPT） | §3.8、文档头、修订记录 | 增加 uv 双平台矩阵 Python 显式选择的可执行 YAML 示例和 PowerShell 分支说明 | 避免 Harness 在 Windows 把 Bash 变量误用或因 .python-version 让 Ubuntu 3.12 误用 3.14.6；仍需真实 CI 独验 | Issue #12/#35；PR #46；SR-028 |
| 2026-11-27 | 0.2.3 | GPT-6（ChatGPT） | §3.8、修订记录 | 澄清 Go Echo 由 Go 工具链构建，Python compileall/证据脚本才使用矩阵 Python | 消除示例描述中将 Go build 错写成通过 Python 运行的歧义 | Issue #12/#35；PR #46；SR-028 |
