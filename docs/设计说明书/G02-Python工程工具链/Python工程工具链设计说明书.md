# G02：Python 工程工具链与环境管理设计说明书

> 文档类型：工程治理功能设计说明书  
> 文档版本：0.2.5\
> 状态：Review #6083225844 对固定 Head `42a7fe2ce7826b7cda74110e843f39401571299c` 给出 CHANGES_REQUESTED（0 P0 / 4 P1 / 3 P2）；本轮按 Issue #12 整改中；SR-028 仍 DRAFT、AC-028-01～10 产品验收 NOT_RUN、READY=0\
> 修订日期：2026-11-27\
> 功能节点：G02 Python 工程工具链与环境管理  
> 关联需求：[IR-007](../../IR/IR%20总登记册.md#ir-007)、[SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md)  
> 追踪 Issue：[ca-agent-next #12](https://github.com/odango-chan/ca-agent-next/issues/12)（当前整改）；原设计 Issue [#35](https://github.com/odango-chan/ca-agent-next/issues/35) 已 CLOSED，仅作历史来源  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级供应链安全治理、跨仓批量迁移、Agent Runtime 架构变更

## 0. 设计评审入口（2026-11-26）

本设计与 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) 由 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 统一追踪；原设计 Issue #35 已 CLOSED。最新独立复评为 [PR #46 Review #6083225844](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6083225844)，固定 Head `42a7fe2ce7826b7cda74110e843f39401571299c` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`，结论 CHANGES_REQUESTED（0 P0 / 4 P1 / 3 P2）。四项 P1 均阻断 READY；本轮仅修订设计与验收定义，不授权产品实施。

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
- 当前基线 `.gitignore` 已有独立 `.venv/` 规则；实施时必须保留。只有目标分支确实缺失该规则时才追加，且不得重复或删除其他 ignore 规则；不得提交 `.venv/`。以 `git check-ignore .venv/pyvenv.cfg` 验证。
- 不设置共享的 `UV_PROJECT_ENVIRONMENT`；项目命令不得使用 `--system`、`--active` 或其他绕过项目环境的选项。
- 不得在系统 Python 中执行 `pip install -e .`，不得依赖另一 worktree 安装的 editable distribution。
- uv 的下载缓存可由 uv 自身跨 worktree 复用；缓存不等于虚拟环境，不共享 site-packages。
- 每个 worktree 执行 `uv sync` 后，当前项目 distribution metadata 必须来自当前 checkout，不能读取另一 worktree 的安装信息。

### 3.6 统一命令入口

从仓库根目录执行。实施者首次添加依赖组后用 `uv lock` 生成锁文件，与 `pyproject.toml` 一起提交。下列命令面向已有锁文件的干净 checkout 和 CI。

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv lock --check
```

测试和 Smoke 使用项目环境；完成 sync 后统一禁止命令隐式同步：

```bash
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
uv run --no-sync --locked --group dev --extra plugins python scripts/review_context.py --help
```

#### 本地 Go Echo 前置（AC-028-06）

`tests/test_plugin.py` 的 `setUpModule()` 会调用 `ensure_echo_binary()`；完整测试会执行 Plugin 测试。`examples/echo/plugin/go.mod` 的 Go directive 为 `1.24`，不是 Go patch 版本 pin。干净 checkout 中 `bin/` 被忽略且可能没有二进制；不得依赖另一 checkout 的旧二进制。运行测试门禁前必须确认 Go 命令可用、记录完整 `go version`，设置并验证 `GOWORK=off`，删除当前平台旧二进制后从该模块源码构建。

Linux/macOS/Git Bash（从仓库根目录执行；子 shell 保证构建后仍处于仓库根目录）：

```bash
set -euo pipefail
ROOT="$(pwd -P)"
(
  cd "$ROOT/examples/echo/plugin"
  export GOWORK=off
  go version
  test "$(go env GOWORK)" = "off"
  GOOS="$(go env GOOS)"
  mkdir -p bin
  rm -f bin/echo-plugin bin/echo-plugin.exe
  if [ "$GOOS" = "windows" ]; then
    BINARY=bin/echo-plugin.exe
  else
    BINARY=bin/echo-plugin
  fi
  go build -trimpath -o "$BINARY" .
)
test "$(pwd -P)" = "$ROOT"
```

Windows PowerShell（从仓库根目录执行；`finally` 保证恢复 Location）：

```powershell
$ErrorActionPreference = 'Stop'
Push-Location examples/echo/plugin
try {
    $env:GOWORK = 'off'
    go version
    if ($LASTEXITCODE -ne 0) { throw 'Go toolchain is unavailable' }
    $gowork = (go env GOWORK)
    if ($LASTEXITCODE -ne 0 -or $gowork -ne 'off') { throw 'GOWORK must be off' }
    $goos = (go env GOOS)
    if ($LASTEXITCODE -ne 0) { throw 'go env GOOS failed' }
    New-Item -ItemType Directory -Force bin | Out-Null
    Remove-Item bin/echo-plugin -ErrorAction SilentlyContinue
    Remove-Item bin/echo-plugin.exe -ErrorAction SilentlyContinue
    if ($goos -eq 'windows') {
        go build -trimpath -o bin/echo-plugin.exe .
    } else {
        go build -trimpath -o bin/echo-plugin .
    }
    if ($LASTEXITCODE -ne 0) { throw 'Go Echo build failed' }
} finally {
    Pop-Location
}
```

Go 版本必须满足 `go.mod` 的 `go 1.24` directive；不在本 SR 另行固定 Go patch。二进制名称必须由目标 `GOOS` 决定，与 `tests/plugin_test_support.py::echo_binary_name()` 的 Windows `.exe` 规则一致。Plugin 测试 helper 会在 Go 可用时再次从源码构建；AC-028-06 仍要求显式前置构建成功，不能利用测试 helper 在 Go 缺失时回退到忽略目录中的陈旧二进制。

#### 统一 unittest 门禁脚本（新增 `scripts/unittest_gate.py`）

CI 和本地验收不得直接依赖 `unittest` 的零退出码判断 PASS，因为标准 unittest 对 skipped 用例仍可能返回 0。实施时必须新增仅依赖 Python 标准库的 `scripts/unittest_gate.py`，按 Host、Plugin、Review Context、完整总计四个范围执行测试；即使某一范围失败，也继续执行其余范围并写出全部报告，最后统一返回非零。

接口：

```bash
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite host --output-dir "$EVIDENCE_DIR/a-host-gate"
```

`--suite` 可重复，取值为 `host`、`plugin`、`review-context`、`total`；不传时运行全部四项。每项的 discovery 范围分别是 `tests/test_host.py`、`tests/test_plugin.py`、`tests/test_review_context.py` 和 `tests/test*.py`。脚本必须通过 `unittest.TestLoader.discover(start_dir=tests, top_level_dir=tests, pattern=...)` 加载，不依赖 `tests/__init__.py`。

脚本的规范性算法与报告字段：

1. 每个范围使用独立 `TestLoader` 和 `TextTestRunner`，记录 `suite.countTestCases()` 为 `discovered`，`result.testsRun` 为 `tests_run`，并记录 `failures`、`errors`、`skipped`、`expected_failures`、`unexpected_successes`、`loader_errors`。
2. `passed = tests_run - failures - errors - skipped - expected_failures - unexpected_successes`；不得用 `discovered - failures` 推算通过数。
3. 单范围 PASS 当且仅当 `discovered > 0`、`tests_run == discovered`、`failures == errors == skipped == expected_failures == unexpected_successes == loader_errors == 0`。任何 0 tests、skip、失败、错误、expected failure、unexpected success 或加载错误均失败。
4. 每项分别写入 `<suite>.json` 与 `<suite>.log`；总计写入 `summary.json`，包含各范围字段和整体 `exit_code`。日志保留完整 unittest 输出/traceback。脚本即使某项失败也继续执行其他范围，全部报告落盘后才返回 `1`；脚本自身发生报告/运行错误返回非零。
5. `--suite host` 仅执行 Host 范围，供 worktree A→B→A 单独验证；仍执行相同的 `discovered>0`、`skipped=0` 等断言。

实现不得引入第三方测试框架或新的运行时依赖。该脚本由 SR-028 实施阶段创建；本设计中的接口、字段、退出条件和 CI 调用为规范性要求。

Host Smoke 另行记录 stdout/stderr/退出码；必须退出 0、stderr 为空，成功 stdout 符合演示验收基线。

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

### 3.8 与 SR-001 Workflow 的衔接及双平台触发验收

[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) 已合入当前设计基线（merge commit `7a0fac41e573021207ab8201bbc718718c451e50`）。目标树已有 `.github/workflows/review-context.yml`、`scripts/review_context.py`、`tests/test_review_context.py` 和 `.github/workflows/sr003-plugin-ci.yml`。SR-028 在独立实施 PR 迁移两个 Workflow 的 Python 安装、测试和脚本入口；不得修改 PR #32 历史分支。

#### SR-003 双平台矩阵

迁移后的 `.github/workflows/sr003-plugin-ci.yml` 目标矩阵必须明确为：

| Runner | Python | Go |
|---|---|---|
| `ubuntu-latest` | `3.12` | 从 `examples/echo/plugin/go.mod` 读取，满足 `go 1.24` |
| `windows-latest` | `3.14.6` | 从 `examples/echo/plugin/go.mod` 读取，满足 `go 1.24` |

不得使用浮动的 Windows `3.14`。两个矩阵 Job 均显式安装/查找矩阵解释器，记录 `python --version`；Windows 必须精确断言 `Python 3.14.6`。两个 Job 的 uv sync/run 必须显式传入 `--python "$PY"`。Linux Job 使用 `shell: bash`，Windows Job 使用 `shell: pwsh`；分别使用 Bash 的 `PY="$(uv python find "$PYTHON_VERSION")"` 和 PowerShell 的 `$PY = (uv python find $env:PYTHON_VERSION)` 原生变量语法。命令示例按对应 shell 单独给出，不得跨 shell 复制变量表达式。

拟实施的矩阵步骤（示例不是运行证据）：

```yaml
env:
  GOWORK: 'off'
  PYTHONUTF8: '1'
  PYTHON_VERSION: ${{ matrix.python-version }}
steps:
  - uses: actions/checkout@v4
  - uses: astral-sh/setup-uv@1db35dd8eee11c5894872e0b383ae6c406cf738d # v10.4.0
    with:
      version: '0.13.10'
  - uses: actions/setup-go@v5
    with:
      go-version-file: examples/echo/plugin/go.mod
      cache: false
  - name: Record Go version
    shell: bash
    run: go version
  - name: Build native Go Echo Plugin
    shell: bash
    working-directory: examples/echo/plugin
    run: |
      set -euo pipefail
      mkdir -p bin
      if [ "$RUNNER_OS" = "Windows" ]; then
        rm -f bin/echo-plugin.exe
        go build -trimpath -o bin/echo-plugin.exe .
      else
        rm -f bin/echo-plugin
        go build -trimpath -o bin/echo-plugin .
      fi
  - name: Install and test Linux matrix Python
    if: runner.os == 'Linux'
    shell: bash
    run: |
      set -euo pipefail
      uv python install "$PYTHON_VERSION"
      PY="$(uv python find "$PYTHON_VERSION")"
      "$PY" --version
      uv sync --python "$PY" --locked --group dev --extra plugins
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_host.py -v
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_plugin.py -v
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_review_context.py -v
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -v
      uv run --python "$PY" --locked --group dev --extra plugins python -m ca_agent_next --smoke
  - name: Install and test Windows matrix Python
    if: runner.os == 'Windows'
    shell: pwsh
    run: |
      $ErrorActionPreference = 'Stop'
      uv python install $env:PYTHON_VERSION
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      $PY = (uv python find $env:PYTHON_VERSION)
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      $version = (& $PY --version)
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      Write-Host $version
      if ($version -ne 'Python 3.14.6') { throw "Expected Python 3.14.6, got $version" }
      uv sync --python "$PY" --locked --group dev --extra plugins
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_host.py -v
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_plugin.py -v
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -p test_review_context.py -v
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -v
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --locked --group dev --extra plugins python -m ca_agent_next --smoke
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

矩阵 Job 还必须保存 Host、Plugin、Review Context、完整总计的 discovered/passed/failures/errors/skipped/exit code；所有必需套件和总计 discovered 均大于 0，必需用例 skipped=0，failures/errors=0，退出码为 0。Go Echo build、compileall 和证据采集仍保留。`GOWORK=off` 必须应用于 Go 构建与 Plugin 测试。

#### paths 与独立堆叠验证 PR

迁移后的 `sr003-plugin-ci.yml` 的 `pull_request.paths` 至少包括 `pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`、`src/**`、`tests/**`、`examples/echo/**`、`scripts/review_context.py`、`docs/SR/SR-003-*`、`.github/workflows/review-context.yml` 和 `.github/workflows/sr003-plugin-ci.yml` 自身。每一类指定单文件变更均须触发两个矩阵 Job。`review-context.yml` 保持 PR 事件入口，运行 Review Context 测试与生成器；其项目解释器固定使用 CPython 3.14.6，依赖安装使用 uv locked 模式。

“仅修改 `review-context.yml`”必须用独立堆叠验证 PR 证明，不能用主实施 PR 内某个单文件 commit 冒充，因为 `paths` 按 PR base...head 的累积文件差异判定：

1. 主实施 PR 完成 pyproject/uv.lock/.python-version、两个 Workflow 和相关配置迁移，先核验其常规双平台 CI 与 Review Context 生成器。
2. 创建验证分支，以主实施 PR 的 head branch 作为验证 PR 的 base；该 base 已包含更新后的 `sr003-plugin-ci.yml`，其中 paths 明确包含 `.github/workflows/review-context.yml`。
3. 验证 PR 相对 base 的三点差异文件清单必须且只能是 `.github/workflows/review-context.yml`。仅在该文件增加一条路径验证注释，不修改其他文件。打开 PR 后再向同一文件推送第二个 commit，产生 `pull_request.synchronize`。
4. 对同一次 synchronize，核验 Review Context Workflow 与 SR-003 Workflow 均由相同 PR number 和 head SHA 触发；Review Context Job 成功，SR-003 的 Ubuntu 3.12 与 Windows 3.14.6 两个 Job 均实际运行且非 skipped。保存两个 Run URL、事件、head SHA、Job 日志、解释器版本和测试统计。
5. 验证 PR 不合并；主实施 PR 和验证 PR 的合并都须另行授权。

PR #32 原有 pip/单 Ubuntu Run 只证明迁移前 SR-001 基线有效，不得计为 uv、双平台、paths 触发或 AC-028-07/08 PASS。

## 4. 本地与 CI 流程

### 4.1 新 worktree 与 A→B→A 隔离验收

AC-028-05 必须用两个临时 detached worktree 执行 A→B→A，不得只分别在两个目录跑一次 happy path：

```bash
ROOT="$(pwd)"
git worktree add --detach ../.sr028-a HEAD
git worktree add --detach ../.sr028-b HEAD

cd ../.sr028-a
unset UV_PROJECT_ENVIRONMENT
uv python install
uv sync --locked --group dev --extra plugins
uv run --locked --group dev --extra plugins python -c 'import importlib.metadata as m, json, pathlib, sys, urllib.parse, urllib.request, ca_agent_next; root=pathlib.Path.cwd().resolve(); venv=(root/".venv").resolve(); d=json.loads(m.distribution("ca-agent-next").read_text("direct_url.json")); source=pathlib.Path(urllib.request.url2pathname(urllib.parse.urlparse(d["url"]).path)).resolve(); module=pathlib.Path(ca_agent_next.__file__).resolve(); assert pathlib.Path(sys.prefix).resolve()==venv and (venv/"pyvenv.cfg").is_file(); assert module.is_relative_to(root/"src") and d["dir_info"]["editable"] is True and source==root; print(json.dumps({"root":str(root),"venv":str(venv),"module":str(module),"source":str(source)}))' > /tmp/sr028-a-paths.json
uv run --locked --group dev --extra plugins python -m unittest discover -s tests -p test_host.py -v

cd ../.sr028-b
unset UV_PROJECT_ENVIRONMENT
uv python install
uv sync --locked --group dev --extra plugins
uv run --locked --group dev --extra plugins python -c 'import importlib.metadata as m, json, pathlib, sys, urllib.parse, urllib.request, ca_agent_next; root=pathlib.Path.cwd().resolve(); venv=(root/".venv").resolve(); d=json.loads(m.distribution("ca-agent-next").read_text("direct_url.json")); source=pathlib.Path(urllib.request.url2pathname(urllib.parse.urlparse(d["url"]).path)).resolve(); module=pathlib.Path(ca_agent_next.__file__).resolve(); assert pathlib.Path(sys.prefix).resolve()==venv and (venv/"pyvenv.cfg").is_file(); assert module.is_relative_to(root/"src") and d["dir_info"]["editable"] is True and source==root; print(json.dumps({"root":str(root),"venv":str(venv),"module":str(module),"source":str(source)}))' > /tmp/sr028-b-paths.json
uv run --locked --group dev --extra plugins python -m unittest discover -s tests -p test_host.py -v

cd ../.sr028-a
unset UV_PROJECT_ENVIRONMENT
uv run --locked --group dev --extra plugins python -c 'import importlib.metadata as m, json, pathlib, sys, urllib.parse, urllib.request, ca_agent_next; root=pathlib.Path.cwd().resolve(); venv=(root/".venv").resolve(); d=json.loads(m.distribution("ca-agent-next").read_text("direct_url.json")); source=pathlib.Path(urllib.request.url2pathname(urllib.parse.urlparse(d["url"]).path)).resolve(); module=pathlib.Path(ca_agent_next.__file__).resolve(); assert pathlib.Path(sys.prefix).resolve()==venv and (venv/"pyvenv.cfg").is_file(); assert module.is_relative_to(root/"src") and d["dir_info"]["editable"] is True and source==root; print(json.dumps({"root":str(root),"venv":str(venv),"module":str(module),"source":str(source)}))' > /tmp/sr028-a-return-paths.json
uv run --locked --group dev --extra plugins python -m unittest discover -s tests -p test_host.py -v
python -c 'import json; from pathlib import Path; a=json.loads(Path("/tmp/sr028-a-paths.json").read_text()); b=json.loads(Path("/tmp/sr028-b-paths.json").read_text()); a2=json.loads(Path("/tmp/sr028-a-return-paths.json").read_text()); assert all(a[k]!=b[k] for k in ("root","venv","module","source")); assert a2==a; print("A/B/A isolation PASS")'

cd "$ROOT"
git worktree remove --force ../.sr028-a
git worktree remove --force ../.sr028-b
rm -f /tmp/sr028-a-paths.json /tmp/sr028-b-paths.json /tmp/sr028-a-return-paths.json
```

保存 A/B 各自 root、`.venv`、`sys.prefix`、`ca_agent_next.__file__` 和 `direct_url.json` 的 file URL。必须观察到 A 与 B 的路径不同；B sync 后再次进入 A，不重新 sync，A 的路径仍指向 A 且 Host 测试通过。Windows 在 Git Bash 或 WSL 中执行此 Bash 验收；不将 PowerShell 变量语法混入该命令块。

### 4.2 依赖更新与锁漂移负例

正常依赖更新流程：

1. 修改 `pyproject.toml` 中明确归属的运行时依赖或 dependency group。
2. 执行 `uv lock` 更新 `uv.lock`。
3. 审阅直接/传递依赖变化和 Python marker。
4. 执行 `uv lock --check`、`uv sync --locked --group dev --extra plugins`、三个独立 unittest 套件、完整 unittest 和 Smoke。
5. 在同一 Commit 提交 pyproject.toml 与 uv.lock；CI 只执行 locked 安装，不重新解析。

AC-028-04 的失败路径必须在干净临时 worktree 执行，使用 Bash（Windows 使用 Git Bash/WSL），步骤固定如下：

```bash
ROOT="$(pwd)"
git worktree add --detach ../.sr028-lock-drift HEAD
cd ../.sr028-lock-drift
unset UV_PROJECT_ENVIRONMENT
uv python install
uv sync --locked --group dev --extra plugins
uv lock --check
python -c 'from pathlib import Path; p=Path("pyproject.toml"); s=p.read_text(); old="PyYAML>=6.0,<7"; assert s.count(old)==1; p.write_text(s.replace(old,"PyYAML>=6.0,<8",1))'
set +e
uv lock --check > /tmp/sr028-lock-check.log 2>&1
lock_check_rc=$?
set -e
test "$lock_check_rc" -ne 0
cat /tmp/sr028-lock-check.log
git diff --exit-code -- uv.lock
set +e
uv sync --locked --group dev --extra plugins > /tmp/sr028-sync-locked.log 2>&1
sync_locked_rc=$?
set -e
test "$sync_locked_rc" -ne 0
cat /tmp/sr028-sync-locked.log
git diff --exit-code -- uv.lock
git restore -- pyproject.toml
git diff --exit-code -- pyproject.toml uv.lock
cd "$ROOT"
git worktree remove --force ../.sr028-lock-drift
```

两条失败命令的输出必须明确说明锁文件与项目声明不一致/需要更新；保存完整 stdout/stderr 与各自非零退出码。每条失败命令后 `git diff --exit-code -- uv.lock` 必须成功，恢复后 pyproject.toml 与 uv.lock 均无差异。禁止用损坏 TOML/锁文件代替依赖声明漂移负例；不得运行 `uv lock` 修复该临时负例。

### 4.3 CI

1. Checkout 当前 PR HEAD，并记录 base/head SHA。
2. 通过固定 setup-uv action 安装 uv 0.13.10。
3. 按项目 `.python-version` 安装根环境 CPython 3.14.6；SR-003 矩阵另外显式安装 Ubuntu 3.12 或 Windows 3.14.6。
4. 通过 `setup-go@v5` 和 `go-version-file: examples/echo/plugin/go.mod` 安装满足 Go 1.24 directive 的 Go；记录 `go version`，设置 `GOWORK=off` 并构建 Go Echo。
5. 使用 `uv sync --python "$PY" --locked --group dev --extra plugins`，之后用同一个 `$PY` 执行 Host、Plugin、Review Context、完整 unittest 和 Smoke。
6. 每个矩阵 Job 保存各测试范围的 discovered/passed/failures/errors/skipped/exit code；所有必需测试发现数大于 0、skipped/failures/errors 为 0，退出码为 0。
7. 任一锁文件漂移、依赖缺失、测试失败、必需用例 skipped、0 tests 或环境创建失败均使 Job 失败；不得降级为 pip 临时安装。

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
| I1 | 根 Python 项目采用 uv | SR-028 READY、独立实施 Issue | pyproject、uv.lock、.python-version、保留 .venv ignore、Go 前置和本地测试 |
| I2 | GitHub Actions 迁移 | I1；目标分支含已合并的 SR-001 和 SR-003 工作流 | 迁移 review-context 与 sr003-plugin-ci；固定双平台矩阵、Go 构建、统计门槛及独立堆叠路径验证 PR |
| I3 | 环境隔离与锁漂移验收 | I1 | 执行两个 worktree 的 A→B→A 和临时声明漂移 fail-closed 负例 |
| I4 | 当前文档入口刷新 | I1～I3 | 更新 README、Agent、SR-002/SR-003 当前复验命令和演示验收基线；历史 pip 证据只读保留 |

I1 与 I3 可在 SR-028 实施 Issue 内按依赖顺序执行；I2 只在 SR-001 Workflow 已进入目标分支后执行；I4 在命令与 Workflow 迁移验收完成后执行。任何阶段依赖未满足时只暂停对应阶段/AC，不把无关设计评审阻塞。

## 7. 验收映射

具体验收 ID、命令和证据要求以 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) v0.2.6 为准：AC-028-01～03 元数据/版本/依赖分组；AC-028-04 锁漂移 fail-closed；AC-028-05 双 worktree A→B→A；AC-028-06 本地 Go、测试计数与 Smoke；AC-028-07 双平台 CI 与独立堆叠 paths 验证 PR；AC-028-08 Review Context 真实 PR Artifact；AC-028-09 范围边界；AC-028-10 当前文档入口刷新。

设计文档、示例 YAML、历史 pip Run 或迁移前 Artifact 均不构成 uv 实施 PASS。每项产品 AC 只有在固定受测 SHA 上真实运行并留存命令、环境、结果和证据后才可更新状态。

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
| 2026-11-27 | 0.2.4 | GPT-6.2（ChatGPT） | §0、§3.5～3.8、§4.1～4.3、§6～§7 | 按 Review #6082874849 补齐 Go 1.24 前置与 GOWORK=off、锁漂移负例、双 worktree A→B→A、测试统计、Windows 3.14.6、独立堆叠验证 PR 和文档验收映射；修正 `.venv/` 既有规则表述 | 关闭 SR-028 的实施歧义，同时保持所有产品 AC NOT_RUN 和 SR DRAFT | Issue #12；PR #46；Review #6082874849；SR-028 v0.2.6 |
