# G02：Python 工程工具链与环境管理设计说明书

> 文档类型：工程治理功能设计说明书  
> 文档版本：0.2.13\
> 状态：第七轮 SR-028 专项独立 Review [#6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#issuecomment-6084094037) 对固定设计快照给出 APPROVE_FOR_READY（0 P0 / 0 P1 / 2 非阻断 P2）；设计阶段已 READY。PR #99 源 Head `83d23e8c04b1c05eb304c2a24a3392f6459ed0f1` 的独立复核 #6094704264 记录 IMPLEMENTED，AC-028-01～10 候选证据已归档。13 个变更路径已逐项对照 PR #115：六个核心实现 Blob 完全一致，其余 7 个治理/文档路径由 #115 更新版本承接。 PR #112 源 Head `dbc0bcbb3a125f143d3648d2cb0331f01368f379` 的 P2-01/P2-02 已关闭；独立 评审评论 #6096938405 给出限定 APPROVE_FOR_READY（0 P0 / 0 P1 / 0 P2）。策略 Bootstrap 47/47、Review Context、SR-003 Ubuntu/Windows 266/266 均 SUCCESS；PR #112 仍 Draft，不合并。 PR #97 源 Head `66a82f09445d5fc32971e91d02b51b7ad6d4ece0` 的状态审计 评审评论 #6096959653 确认 READY 仅代表设计快照；实施证据来自 #99 的 IMPLEMENTED 复核。六份治理文档由 #115 更新版本承接，不原样覆盖；PR #97 不合并。 PR #115 唯一 mainline 集成入口仍为 OPEN / Draft（Base main @ b2ed5eb84114f9c2556a0cd06ed974887b1b70ad），本次代码与策略核验快照 Head `609fb12612c8990a37ba0e174cfacadfd7a7c5d9`；Review Context #46130016832 SUCCESS，Python Toolchain Policy Bootstrap #46130016864 SUCCESS（48/48），SR-003 Regression #46130016833 SUCCESS（Ubuntu 重跑与 Windows 均为 Host 52/52、Plugin 87/87、Review Context 84/84、Total 271/271）。Ubuntu 首次执行在 `test_process_exit_clears_extensions` 出现一次 IPC_TIMEOUT；同一 SHA 的失败 Job 重跑后 271/271 通过，未修改测试或产品代码，作为时序风险保留。当前未合入 main，未标 VERIFIED/RELEASED；PR #115 全量独立复评仍待完成。
> 修订日期：2026-11-28\
> 功能节点：G02 Python 工程工具链与环境管理  
> 关联需求：[IR-007](../../IR/IR%20总登记册.md#ir-007)、[SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md)  
> 追踪 Issue：[ca-agent-next #12](https://github.com/odango-chan/ca-agent-next/issues/12)（当前整改）；原设计 Issue [#35](https://github.com/odango-chan/ca-agent-next/issues/35) 已 CLOSED，仅作历史来源  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级供应链安全治理、跨仓批量迁移、Agent Runtime 架构变更

## 0. 第七轮设计批准与当前实施状态（2026-11-28）

本设计与 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) 由 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 统一追踪；原设计 Issue #35 已 CLOSED。第七轮专项独立复评为 [PR #46 评审评论 #6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#issuecomment-6084094037)，固定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`，结论 APPROVE_FOR_READY（0 P0 / 0 P1 / 2 非阻断 P2）；该结论仅限设计快照。PR #99 源 Head `83d23e8c04b1c05eb304c2a24a3392f6459ed0f1` 的独立复核 #6094704264 记录 IMPLEMENTED，AC-028-01～10 候选证据已归档。13 个变更路径已逐项对照 PR #115：六个核心实现 Blob 完全一致，其余 7 个治理/文档路径由 #115 更新版本承接。 PR #112 源 Head `dbc0bcbb3a125f143d3648d2cb0331f01368f379` 的 P2-01/P2-02 已关闭；独立 评审评论 #6096938405 给出限定 APPROVE_FOR_READY（0 P0 / 0 P1 / 0 P2）。策略 Bootstrap 47/47、Review Context、SR-003 Ubuntu/Windows 266/266 均 SUCCESS；PR #112 仍 Draft，不合并。 PR #97 源 Head `66a82f09445d5fc32971e91d02b51b7ad6d4ece0` 的状态审计 评审评论 #6096959653 确认 READY 仅代表设计快照；实施证据来自 #99 的 IMPLEMENTED 复核。六份治理文档由 #115 更新版本承接，不原样覆盖；PR #97 不合并。 PR #115 唯一 mainline 集成入口仍为 OPEN / Draft（Base main @ b2ed5eb84114f9c2556a0cd06ed974887b1b70ad），本次代码与策略核验快照 Head `609fb12612c8990a37ba0e174cfacadfd7a7c5d9`；Review Context #46130016832 SUCCESS，Python Toolchain Policy Bootstrap #46130016864 SUCCESS（48/48），SR-003 Regression #46130016833 SUCCESS（Ubuntu 重跑与 Windows 均为 Host 52/52、Plugin 87/87、Review Context 84/84、Total 271/271）。Ubuntu 首次执行在 `test_process_exit_clears_extensions` 出现一次 IPC_TIMEOUT；同一 SHA 的失败 Job 重跑后 271/271 通过，未修改测试或产品代码，作为时序风险保留。当前未合入 main，未标 VERIFIED/RELEASED；PR #115 全量独立复评仍待完成。

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

1. 每个范围使用独立 `unittest.TestLoader` 和 `unittest.TextTestRunner`。`discovered` 取 `suite.countTestCases()`，`tests_run` 取 `result.testsRun`；`failures`、`errors`、`skipped`、`expected_failures`、`unexpected_successes` 分别取 `TestResult` 对应列表的条目数。`loader_errors` 精确定义为本次独立 `TestLoader` 在 `discover()` 后其 `loader.errors` 列表的条目数（`len(loader.errors)`），每个列表元素计 1，不按多行 traceback 拆分；`loader_error_messages` 原样保存该列表。若 `discover()` 本身抛出异常而未返回 suite，将完整异常文本记录到 `discovery_exception`，该范围直接失败；若 discovery 正常完成，JSON 字段 `discovery_exception` 必须写为 `null`；此时 `loader_errors` 仍只表示 `len(loader.errors)`，不把异常重复计入该字段。
2. `passed = tests_run - failures - errors - skipped - expected_failures - unexpected_successes`；不得用 `discovered - failures` 推算通过数。
3. 单范围 `exit_code` 为 `0` 当且仅当 `discovered > 0`、`tests_run == discovered`、`failures == errors == skipped == expected_failures == unexpected_successes == loader_errors == 0` 且 `discovery_exception` 为 JSON `null`；否则为 `1`。`loader_errors` 与 `errors` 是不同阶段的观测字段：加载错误可能同时产生 `_FailedTest` 并出现在 `TestResult.errors`，此时两字段可同时计数，但不得相加或去重；PASS 必须分别满足两者为 0。任何 0 tests、skip、失败、错误、expected failure、unexpected success、加载诊断或 discovery 异常均失败。
4. 每项分别写入 `<suite>.json` 与 `<suite>.log`；每个 `<suite>.json` 必须包含该范围的 `exit_code`（仅允许 `0` 或 `1`）、所有统计字段、`loader_error_messages` 和 `discovery_exception`。总计写入 `summary.json`，其中每个已选范围保留自己的 `exit_code`，并有独立的整体 `exit_code`。整体 `exit_code` 仅在所有已选范围的 `exit_code` 均为 0 且所有报告成功写入时为 0，否则为 1；进程退出码必须与整体 `exit_code` 一致。日志保留完整 unittest 输出/traceback。脚本即使某项失败也继续执行其他范围，全部报告落盘后才返回；报告/运行错误必须使整体退出码非零。
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
- 完成唯一一次 `uv sync --locked` 后，测试和项目脚本使用 `uv run --no-sync --locked --group dev --extra plugins ...`；禁止测试步骤自动同步。
- Workflow 不得通过 `pip install PyYAML`、`pip install -e .` 或全局 site-packages 临时补依赖。
- 可使用 setup-uv 自带的缓存；不另写自定义包缓存协议。

首版 CI 命令顺序（setup-uv action 已完成后）：

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
```

### 3.8 与 SR-001 Workflow 的衔接及双平台触发验收

[PR #32](https://github.com/odango-chan/ca-agent-next/pull/32) 已合入当前设计基线（merge commit `7a0fac41e573021207ab8201bbc718718c451e50`）。目标树已有 `.github/workflows/review-context.yml`、`scripts/review_context.py`、`tests/test_review_context.py` 和 `.github/workflows/sr003-plugin-ci.yml`。SR-028 在独立实施 PR 迁移两个 Workflow 的 Python 安装、测试和脚本入口；不得修改 PR #32 历史分支。

#### SR-003 双平台矩阵

迁移后的 `.github/workflows/sr003-plugin-ci.yml` 目标矩阵必须明确为：

| Runner | Python | Go |
|---|---|---|
| `ubuntu-latest` | `3.12` | 从 `examples/echo/plugin/go.mod` 读取，满足 `go 1.24` |
| `windows-latest` | `3.14.6` | 从 `examples/echo/plugin/go.mod` 读取，满足 `go 1.24` |

不得使用浮动的 Windows `3.14`。两个矩阵 Job 均显式安装/查找矩阵解释器，记录 `python --version`；Windows 必须精确断言 `Python 3.14.6`。两个 Job 的 uv sync/run 必须显式传入 `--python "$PY"`。Python/uv 步骤在 Linux 使用 `shell: bash`、在 Windows 使用 `shell: pwsh`；Go Echo 构建步骤在两个 Runner 上均使用 `shell: bash`。Windows Git Bash 下 `go env GOOS` 为 `windows` 时必须生成并清理 `echo-plugin.exe`。不得把 Python/uv shell 约定扩大到 Go 步骤。

拟实施的矩阵步骤（示例不是运行证据；以下片段位于具体 Job 下）：

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - os: ubuntu-latest
        python-version: '3.12'
      - os: windows-latest
        python-version: '3.14.6'
runs-on: ${{ matrix.os }}
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
      rm -f bin/echo-plugin bin/echo-plugin.exe
      if [ "$(go env GOOS)" = "windows" ]; then
        go build -trimpath -o bin/echo-plugin.exe .
      else
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
      mkdir -p artifacts/sr028/unittest-gate
      uv sync --python "$PY" --locked --group dev --extra plugins
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/sr028/unittest-gate
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python -m compileall -q src tests
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python tests/capture_sr003_evidence.py > artifacts/sr028/sr003-evidence.json
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
      New-Item -ItemType Directory -Force artifacts/sr028/unittest-gate | Out-Null
      uv sync --python "$PY" --locked --group dev --extra plugins
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/sr028/unittest-gate
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python -m compileall -q src tests
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      uv run --python "$PY" --no-sync --locked --group dev --extra plugins python tests/capture_sr003_evidence.py > artifacts/sr028/sr003-evidence.json
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  - name: Upload SR-028 test and Plugin evidence
    if: always()
    uses: actions/upload-artifact@v4
    with:
      name: sr028-${{ matrix.os }}-${{ matrix.python-version }}
      path: artifacts/sr028/
      if-no-files-found: error
```

两个矩阵 Job 都必须通过 `scripts/unittest_gate.py` 自动运行 Host、Plugin、Review Context 和完整总计；脚本逐范围断言 `discovered>0`、`tests_run=discovered`、`failures/errors/skipped/expected_failures/unexpected_successes/loader_errors=0` 且 `discovery_exception=null`，并在任何范围失败时最终非零退出。每项 JSON、log、summary、Smoke 和 Go Echo 证据由 `if: always()` Artifact 上传步骤保存。只记录绿色 Job 不足以 PASS；必须检查 gate 报告中四个范围的字段和退出码。`GOWORK=off` 必须应用于 Go 构建与 Plugin 测试。

#### Review Context Workflow：诊断 Artifact 与正式 Artifact 分离

`.github/workflows/review-context.yml` 在迁移后使用相同 uv 版本与 `uv sync --locked`。诊断证据目录与生成器正式输出目录必须是两个不同目录：

- 正式输出目录：`$RUNNER_TEMP/review-context/`，仅允许包含 `review-scope.json`、`评审上下文.md`、`统一评审提示词.md` 三个完成态文件；Workflow Summary 位于 `$RUNNER_TEMP/review-context-summary.md`，不放入该目录。
- 诊断目录：`$RUNNER_TEMP/review-context-diagnostics/`，不得放入上述三个正式输出文件。Job 开始时先创建该目录并写入 `run-context.txt`，记录 PR number、base SHA、head SHA、run ID 和 run attempt，确保即使早期步骤失败也有诊断 Artifact 可上传。

Review Context gate 使用 `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite review-context --output-dir "$RUNNER_TEMP/review-context-diagnostics/unittest-gate"`。诊断目录至少保留 `unittest-gate/review-context.json`、`unittest-gate/review-context.log`、`unittest-gate/summary.json`。生成器步骤执行时，必须将 stdout、stderr 分别保存为 `generator.stdout.log`、`generator.stderr.log`，将真实进程退出码保存为 `generator.exit-code`，并生成 `generator-output-manifest.txt`；manifest 对三个预期正式文件逐一记录文件名、PRESENT/MISSING 和字节数，不计算 hash，不复制文件内容。
对应步骤必须按以下顺序实现（变量沿用 Workflow 已定义的 `PR_NUMBER`、`BASE_SHA`、`HEAD_SHA`）：

```yaml
- name: Prepare Review Context diagnostic evidence
  if: always()
  shell: bash
  run: |
    set -euo pipefail
    diagnostics_dir="$RUNNER_TEMP/review-context-diagnostics"
    mkdir -p "$diagnostics_dir/unittest-gate"
    {
      printf 'pr_number=%s\n' "$PR_NUMBER"
      printf 'base_sha=%s\n' "$BASE_SHA"
      printf 'head_sha=%s\n' "$HEAD_SHA"
      printf 'generator_base_sha=%s\n' "$BASE_SHA"
      printf 'failure_injection=none\n'
      printf 'run_id=%s\n' "$GITHUB_RUN_ID"
      printf 'run_attempt=%s\n' "$GITHUB_RUN_ATTEMPT"
    } > "$diagnostics_dir/run-context.txt"

- name: Run Review Context unittest gate
  shell: bash
  run: |
    set -euo pipefail
    uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite review-context --output-dir "$RUNNER_TEMP/review-context-diagnostics/unittest-gate"

- name: Generate review context
  id: generate
  shell: bash
  run: |
    set -euo pipefail
    work_dir="$RUNNER_TEMP/review-context"
    diagnostics_dir="$RUNNER_TEMP/review-context-diagnostics"
    summary_file="$RUNNER_TEMP/review-context-summary.md"
    rm -rf "$work_dir"
    mkdir -p "$work_dir"
    if uv run --no-sync --locked --group dev --extra plugins python scripts/review_context.py \
      --base "$BASE_SHA" \
      --head "$HEAD_SHA" \
      --out "$work_dir" \
      --summary "$summary_file" \
      --event-path "$GITHUB_EVENT_PATH" \
      > "$diagnostics_dir/generator.stdout.log" \
      2> "$diagnostics_dir/generator.stderr.log"; then
      generator_rc=0
    else
      generator_rc=$?
    fi
    printf '%s\n' "$generator_rc" > "$diagnostics_dir/generator.exit-code"
    : > "$diagnostics_dir/generator-output-manifest.txt"
    for name in 'review-scope.json' '评审上下文.md' '统一评审提示词.md'; do
      file="$work_dir/$name"
      if [ -f "$file" ]; then
        bytes="$(wc -c < "$file" | tr -d '[:space:]')"
        printf '%s\tPRESENT\t%s\n' "$name" "$bytes" >> "$diagnostics_dir/generator-output-manifest.txt"
      else
        printf '%s\tMISSING\t0\n' "$name" >> "$diagnostics_dir/generator-output-manifest.txt"
      fi
    done
    if [ "$generator_rc" -eq 0 ]; then
      test -f "$work_dir/review-scope.json"
      test -f "$work_dir/评审上下文.md"
      test -f "$work_dir/统一评审提示词.md"
    fi
    exit "$generator_rc"
```

诊断 Artifact 上传步骤必须排在上述生成器步骤之后、成功 Summary/失败报告和正式 Artifact 上传步骤之前；使用 `if: always()`。`Report failure` 步骤使用 `if: failure()`，并排在正式 Artifact 之前；正式 Artifact 必须是 Job 最后一步，且仅在诊断 Artifact、生成器、成功 Summary 等所有前置步骤均成功时按 `if: success()` 上传。

必须先上传诊断 Artifact，再执行成功 Summary（`if: success()`）或失败报告（`if: failure()`）；正式三文件 Artifact 上传步骤必须排在失败报告步骤之后，作为 Job 的最后一个步骤，并保持 `if: success()`。这样任一 gate、生成器、诊断上传或 Summary/失败报告步骤失败时，正式 Artifact 均不会执行；正式 Artifact 上传成功后也不再有后续步骤将该 Run 改为失败。诊断 Artifact 的名称固定为 `review-context-diagnostics-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，上传条件为 `if: always()`，路径仅为 `$RUNNER_TEMP/review-context-diagnostics/`，`if-no-files-found: error`，保留 30 天。它用于失败诊断，不是完成态交付物；即使 gate 或生成器失败，也必须尝试上传。

正式完成态 Artifact 沿用现有名称 `review-context-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，上传条件必须保持 `if: success()`，`if-no-files-found: error`，保留 30 天；`path` 必须显式列出且只能列出 `$RUNNER_TEMP/review-context/review-scope.json`、`$RUNNER_TEMP/review-context/评审上下文.md`、`$RUNNER_TEMP/review-context/统一评审提示词.md`。不得将 gate、日志、manifest、Summary 或其他文件加入该 Artifact。上传后下载解包，文件集合必须恰好为这三份，不得多也不得少。

失败语义：gate 失败时生成器和正式 Artifact 上传步骤不得执行；生成器失败时诊断 Artifact 仍上传，正式 Artifact 因 `if: success()` 不执行；诊断 Artifact 上传失败也必须阻止后续成功 Summary/正式 Artifact。任何失败 Run 均不得产生正式完成态 Artifact。成功 Run 必须同时产生诊断 Artifact 和恰含三份文件的正式 Artifact。诊断 Artifact 的上传不能改变或放宽正式 Artifact 的成功条件。

拟实施的 Review Context Workflow 上传步骤（正式三文件步骤保留现有契约）：

```yaml
- name: Upload Review Context diagnostic evidence
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: review-context-diagnostics-pr-${{ github.event.pull_request.number }}-${{ github.run_id }}-${{ github.run_attempt }}
    path: ${{ runner.temp }}/review-context-diagnostics/
    if-no-files-found: error
    retention-days: 30

- name: Write workflow summary
  if: success()
  run: |
    set -euo pipefail
    summary_file="$RUNNER_TEMP/review-context-summary.md"
    artifact_name="review-context-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
    {
      cat "$summary_file"
      echo ""
      echo "### 入口"
      echo ""
      echo "- Workflow Run：${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      echo "- Artifact：${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}#artifacts"
      echo "  名称 \`$artifact_name\`"
    } | tee -a "$GITHUB_STEP_SUMMARY"

- name: Report failure
  if: failure()
  run: |
    {
      echo "## Review Context 生成失败"
      echo ""
      echo "本 Job 失败，未上传正式完成态 Artifact。诊断 Artifact 单独保留；具体错误见对应步骤日志。"
      echo ""
      echo "- Workflow Run：${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
    } >> "$GITHUB_STEP_SUMMARY"

- name: Upload review context artifacts
  if: success()
  uses: actions/upload-artifact@v4
  with:
    name: review-context-pr-${{ github.event.pull_request.number }}-${{ github.run_id }}-${{ github.run_attempt }}
    path: |
      ${{ runner.temp }}/review-context/review-scope.json
      ${{ runner.temp }}/review-context/评审上下文.md
      ${{ runner.temp }}/review-context/统一评审提示词.md
    if-no-files-found: error
    retention-days: 30
```

AC-028-08 必须用真实成功 PR Run 下载核对两个 Artifact；另用一个受控负例 PR 验证“测试门禁通过、生成器失败”的真实 Workflow 路径。**负例 PR 必须保持 head 版 `Agent.md` 与有效 `review_scope` 不变**，不得通过破坏它触发生成器失败（测试模块在导入时从仓库根 `Agent.md` 派生全部 fixture，这样做会先使 gate 失败）。负例只在该临时 PR 的 `.github/workflows/review-context.yml` 中，将生成器命令的 `--base "$BASE_SHA"` 临时替换为 `--base "0000000000000000000000000000000000000000"`；同时将 `run-context.txt` 的 `generator_base_sha` 记录为该全零 SHA、`failure_injection=invalid-base`，但 `base_sha` 仍记录真实 PR base。预期 Review Context gate 全部通过，生成器实际执行并以非零退出，stderr 包含 `base 提交对象不可读取`；诊断 Artifact 必须包含 gate PASS JSON/log/summary、generator stdout/stderr/exit-code 与 manifest（三个正式文件均为 MISSING），正式三文件 Artifact 不存在。无效 `review_scope` 的拒绝能力由现有 `test_validation_failure_writes_no_artifact` 与 `test_subprocess_returns_non_zero_with_location` 在临时 Git 仓库中的单元测试覆盖；这两项必须随 gate 通过。负例 PR 不得合并；取得负例证据后，恢复 `--base "$BASE_SHA"`、`generator_base_sha=$BASE_SHA`、`failure_injection=none`，在恢复后的新 Head 上重新运行成功路径并核验两个 Artifact，最后关闭负例 PR（未合并）。

#### paths 与独立堆叠验证 PR

迁移后的 `sr003-plugin-ci.yml` 的 `pull_request.paths` 至少包括 `pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`、`src/**`、`tests/**`、`examples/echo/**`、`scripts/review_context.py`、`scripts/unittest_gate.py`、`docs/SR/SR-003-*`、`.github/workflows/review-context.yml` 和 `.github/workflows/sr003-plugin-ci.yml` 自身。每一类指定单文件变更均须触发两个矩阵 Job。

“仅修改 `review-context.yml`”必须用独立堆叠验证 PR 证明，不能用主实施 PR 内某个单文件 commit 冒充，因为 `paths` 按 PR base...head 的累积文件差异判定：

1. 主实施 PR 完成 pyproject/uv.lock/.python-version、`scripts/unittest_gate.py` 和两个 Workflow 迁移，先核验其常规双平台 CI 与 AC-028-06/08。
2. 创建验证分支，以主实施 PR 的 head branch 作为验证 PR 的 base；该 base 已包含更新后的 `sr003-plugin-ci.yml`，其中 paths 明确包含 `.github/workflows/review-context.yml`。
3. 验证 PR 相对 base 的三点差异文件清单必须且只能是 `.github/workflows/review-context.yml`。仅在该文件增加一条路径验证注释，不修改其他文件。打开 PR 后再向同一文件推送第二个 commit，产生 `pull_request.synchronize`。
4. 对同一次 synchronize，核验 Review Context Workflow 与 SR-003 Workflow 均由相同 PR number 和 head SHA 触发；Review Context Job 成功，SR-003 的 Ubuntu 3.12 与 Windows 3.14.6 两个 Job 均实际运行且非 skipped。保存两个 Run URL、事件、head SHA、Job 日志、解释器版本、四范围 gate JSON/log 和退出码。
5. 验证 PR 不合并；主实施 PR 和验证 PR 的合并都须另行授权。

PR #32 原有 pip/单 Ubuntu Run 只证明迁移前 SR-001 基线有效，不得计为 uv、双平台、paths 触发或 AC-028-07/08 PASS。
## 4. 本地与 CI 流程

### 4.1 新 worktree 与 A→B→A 隔离验收

AC-028-05 必须在干净 checkout 中用两个临时 detached worktree 执行 A→B→A。整个块从第一条命令启用 `set -euo pipefail`；`trap` 只清理 worktree，不删除证据，并必须保留原始退出码。任何创建、sync、断言、Host 测试、比较或清理失败均使整段非零退出。

```bash
set -euo pipefail
ROOT="$(pwd -P)"
test -f "$ROOT/pyproject.toml"
if [ -n "${SR028_EVIDENCE_DIR:-}" ]; then
  EVIDENCE_DIR="$SR028_EVIDENCE_DIR"
  test ! -e "$EVIDENCE_DIR"
  mkdir -p "$EVIDENCE_DIR"
else
  EVIDENCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sr028-ab-a-evidence.XXXXXX")"
fi
EVIDENCE_DIR="$(cd "$EVIDENCE_DIR" && pwd -P)"
case "$EVIDENCE_DIR/" in "$ROOT/"*) echo 'Evidence directory must be outside the repository' >&2; exit 2 ;; esac
WORKTREE_PARENT="$(mktemp -d "${TMPDIR:-/tmp}/sr028-ab-a-worktrees.XXXXXX")"
A_PATH="$WORKTREE_PARENT/a"
B_PATH="$WORKTREE_PARENT/b"
A_ADDED=0
B_ADDED=0
cleanup() {
  local original_rc=$?
  local cleanup_rc=0
  local cmd_rc=0
  trap - EXIT
  set +e
  cd "$ROOT"
  cmd_rc=$?
  if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  if [ "$B_ADDED" -eq 1 ]; then
    git -C "$ROOT" worktree remove --force "$B_PATH"
    cmd_rc=$?
    if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  fi
  if [ "$A_ADDED" -eq 1 ]; then
    git -C "$ROOT" worktree remove --force "$A_PATH"
    cmd_rc=$?
    if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  fi
  rmdir "$WORKTREE_PARENT"
  cmd_rc=$?
  if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  printf 'SR028_EVIDENCE_DIR=%s\n' "$EVIDENCE_DIR"
  if [ "$original_rc" -ne 0 ]; then exit "$original_rc"; fi
  if [ "$cleanup_rc" -ne 0 ]; then exit "$cleanup_rc"; fi
}
trap cleanup EXIT
git worktree add --detach "$A_PATH" HEAD
A_ADDED=1
git worktree add --detach "$B_PATH" HEAD
B_ADDED=1

capture_env() {
  local label="$1"
  local worktree="$2"
  (
    cd "$worktree"
    uv run --no-sync --locked --group dev --extra plugins python - "$worktree" "$EVIDENCE_DIR/$label.json" "$EVIDENCE_DIR/$label.direct_url.json" <<'PY'
import importlib.metadata as metadata
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
import ca_agent_next
root = pathlib.Path(sys.argv[1]).resolve()
report_path = pathlib.Path(sys.argv[2])
direct_url_path = pathlib.Path(sys.argv[3])
raw = metadata.distribution("ca-agent-next").read_text("direct_url.json")
assert raw is not None, "direct_url.json is missing"
direct = json.loads(raw)
url = direct["url"]
parsed = urllib.parse.urlparse(url)
assert parsed.scheme == "file", url
source = pathlib.Path(urllib.request.url2pathname(parsed.path)).resolve()
venv = (root / ".venv").resolve()
sys_prefix = pathlib.Path(sys.prefix).resolve()
executable = pathlib.Path(os.path.abspath(sys.executable))
module = pathlib.Path(ca_agent_next.__file__).resolve()
editable = direct.get("dir_info", {}).get("editable") is True
assert (venv / "pyvenv.cfg").is_file(), venv
assert sys_prefix == venv, (sys_prefix, venv)
assert executable.is_relative_to(venv), (executable, venv)
assert module.is_relative_to(root / "src"), (module, root / "src")
assert editable, direct
assert source == root, (source, root)
report = {"root":str(root),"venv":str(venv),"sys_prefix":str(sys_prefix),"executable":str(executable),"module":str(module),"direct_url":url,"direct_url_source":str(source),"editable":editable}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
direct_url_path.write_text(raw + "\n", encoding="utf-8")
PY
    git -C "$worktree" check-ignore -v .venv/pyvenv.cfg > "$EVIDENCE_DIR/$label.git-check-ignore.txt"
    test -s "$EVIDENCE_DIR/$label.git-check-ignore.txt"
  )
}

run_host() {
  local label="$1"
  local worktree="$2"
  (
    cd "$worktree"
    if uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite host --output-dir "$EVIDENCE_DIR/$label-host-gate" > "$EVIDENCE_DIR/$label-host-gate.stdout.log" 2>&1; then rc=0; else rc=$?; fi
    printf '%s\n' "$rc" > "$EVIDENCE_DIR/$label-host-gate.exit-code"
    cat "$EVIDENCE_DIR/$label-host-gate.stdout.log"
    test "$rc" -eq 0
  )
}

cd "$A_PATH"
unset UV_PROJECT_ENVIRONMENT
uv python install
uv sync --locked --group dev --extra plugins
capture_env a-before "$A_PATH"
run_host a-before "$A_PATH"

cd "$B_PATH"
unset UV_PROJECT_ENVIRONMENT
uv python install
uv sync --locked --group dev --extra plugins
capture_env b "$B_PATH"
run_host b "$B_PATH"

cd "$A_PATH"
unset UV_PROJECT_ENVIRONMENT
# 关键：返回 A 后只允许 --no-sync；不得执行 uv sync 或普通 uv run。
capture_env a-return "$A_PATH"
run_host a-return "$A_PATH"
uv run --no-sync --locked --group dev --extra plugins python - "$EVIDENCE_DIR" <<'PY'
import json, pathlib, sys
evidence = pathlib.Path(sys.argv[1])
a = json.loads((evidence / "a-before.json").read_text(encoding="utf-8"))
b = json.loads((evidence / "b.json").read_text(encoding="utf-8"))
a2 = json.loads((evidence / "a-return.json").read_text(encoding="utf-8"))
for key in ("root", "venv", "sys_prefix", "executable", "module", "direct_url", "direct_url_source"): assert a[key] != b[key], (key, a[key], b[key])
assert a2 == a, (a, a2)
assert (evidence / "a-before.direct_url.json").read_bytes() == (evidence / "a-return.direct_url.json").read_bytes()
assert (evidence / "a-before.git-check-ignore.txt").read_text() == (evidence / "a-return.git-check-ignore.txt").read_text()
print("A/B/A isolation PASS; A return used --no-sync")
PY
printf 'A→B→A evidence retained at: %s\n' "$EVIDENCE_DIR"
```

Windows 本地执行此 Bash 块时使用 Git Bash 或 WSL；不得在 PowerShell 中粘贴 Bash 块。A→B→A 的 Python 检查、Host 测试和比较全部通过 `uv run --no-sync --locked ...` 运行；返回 A 后绝不执行 `uv sync`、`uv python install` 或普通 `uv run`。`--no-sync` 是本验收的关键条件，防止 uv 自动修复 editable metadata 污染。

证据目录必须保留，不得由 trap 或后续 cleanup 删除。A-before、B、A-return 三份 JSON 必须包含 root、venv、sys_prefix、executable、module、原始 `direct_url` URL、解析后的 direct_url_source、editable；并分别保留原始 `direct_url.json`、`git check-ignore -v` 输出、Host gate JSON/log/exit code。将该目录作为验收附件归档，报告中记录绝对路径、受测 SHA 和附件位置。

### 4.2 依赖更新与锁漂移负例

正常依赖更新流程：

1. 修改 `pyproject.toml` 中明确归属的运行时依赖或 dependency group。
2. 执行 `uv lock` 更新 `uv.lock`。
3. 审阅直接/传递依赖变化和 Python marker。
4. 执行 `uv lock --check`、`uv sync --locked --group dev --extra plugins`、统一 unittest gate 和 Smoke。
5. 在同一 Commit 提交 `pyproject.toml` 与 `uv.lock`；CI 只执行 locked 安装，不重新解析。

AC-028-04 的失败路径必须在干净临时 worktree 执行。整个 Bash 块从第一条命令启用 `set -euo pipefail`，`trap` 清理 worktree 并保留原始退出码；初始 sync/lock-check 两条正例必须明确成功。只允许在两条预期失败命令的 `if` 条件中捕获退出码。

```bash
set -euo pipefail
ROOT="$(pwd -P)"
EVIDENCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sr028-lock-evidence.XXXXXX")"
WORKTREE_PARENT="$(mktemp -d "${TMPDIR:-/tmp}/sr028-lock-worktree.XXXXXX")"
LOCK_PATH="$WORKTREE_PARENT/lock-drift"
LOCK_ADDED=0
cleanup() {
  local original_rc=$?
  local cleanup_rc=0
  local cmd_rc=0
  trap - EXIT
  set +e
  cd "$ROOT"
  cmd_rc=$?
  if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  if [ "$LOCK_ADDED" -eq 1 ]; then
    git -C "$ROOT" worktree remove --force "$LOCK_PATH"
    cmd_rc=$?
    if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  fi
  rmdir "$WORKTREE_PARENT"
  cmd_rc=$?
  if [ "$cmd_rc" -ne 0 ] && [ "$cleanup_rc" -eq 0 ]; then cleanup_rc=$cmd_rc; fi
  printf 'SR028_LOCK_EVIDENCE_DIR=%s\n' "$EVIDENCE_DIR"
  if [ "$original_rc" -ne 0 ]; then exit "$original_rc"; fi
  if [ "$cleanup_rc" -ne 0 ]; then exit "$cleanup_rc"; fi
}
trap cleanup EXIT
git worktree add --detach "$LOCK_PATH" HEAD
LOCK_ADDED=1
cd "$LOCK_PATH"
unset UV_PROJECT_ENVIRONMENT
uv python install
if uv sync --locked --group dev --extra plugins > "$EVIDENCE_DIR/positive-sync.log" 2>&1; then
  printf '0\n' > "$EVIDENCE_DIR/positive-sync.exit-code"
else
  rc=$?
  printf '%s\n' "$rc" > "$EVIDENCE_DIR/positive-sync.exit-code"
  cat "$EVIDENCE_DIR/positive-sync.log"
  exit "$rc"
fi
if uv lock --check > "$EVIDENCE_DIR/positive-lock-check.log" 2>&1; then
  printf '0\n' > "$EVIDENCE_DIR/positive-lock-check.exit-code"
else
  rc=$?
  printf '%s\n' "$rc" > "$EVIDENCE_DIR/positive-lock-check.exit-code"
  cat "$EVIDENCE_DIR/positive-lock-check.log"
  exit "$rc"
fi
uv run --no-sync --locked --group dev --extra plugins python -c 'from pathlib import Path; p=Path("pyproject.toml"); s=p.read_text(encoding="utf-8"); old="PyYAML>=6.0,<7"; assert s.count(old)==1, "expected exactly one PyYAML constraint"; p.write_text(s.replace(old,"PyYAML>=6.0,<8",1), encoding="utf-8")'
git diff -- pyproject.toml > "$EVIDENCE_DIR/pyproject-drift.diff"
if uv lock --check > "$EVIDENCE_DIR/negative-lock-check.log" 2>&1; then
  echo 'FAIL: uv lock --check unexpectedly accepted a stale lockfile' >&2
  exit 1
else
  lock_check_rc=$?
fi
printf '%s\n' "$lock_check_rc" > "$EVIDENCE_DIR/negative-lock-check.exit-code"
test "$lock_check_rc" -ne 0
grep -Eiq 'lockfile.*needs to be updated' "$EVIDENCE_DIR/negative-lock-check.log"
git diff --exit-code HEAD -- uv.lock
test -z "$(git status --porcelain -- uv.lock)"
if uv sync --locked --group dev --extra plugins > "$EVIDENCE_DIR/negative-sync-locked.log" 2>&1; then
  echo 'FAIL: uv sync --locked unexpectedly accepted a stale lockfile' >&2
  exit 1
else
  sync_locked_rc=$?
fi
printf '%s\n' "$sync_locked_rc" > "$EVIDENCE_DIR/negative-sync-locked.exit-code"
test "$sync_locked_rc" -ne 0
grep -Eiq 'lockfile.*needs to be updated' "$EVIDENCE_DIR/negative-sync-locked.log"
git diff --exit-code HEAD -- uv.lock
test -z "$(git status --porcelain -- uv.lock)"
git restore --source=HEAD --worktree -- pyproject.toml
git diff --exit-code HEAD -- pyproject.toml uv.lock
test -z "$(git status --porcelain -- pyproject.toml uv.lock)"
printf 'Lock-drift evidence retained at: %s\n' "$EVIDENCE_DIR"
```

正例失败会立即终止，不会进入负例；负例只有在退出码非零且 stdout/stderr 匹配 `lockfile ... needs to be updated` 诊断后才算预期失败。每次负例后都证明 `uv.lock` 的 tracked diff 和 status 均为空。恢复后 `pyproject.toml` 与 `uv.lock` 均必须干净。任何正例、诊断、锁文件不变断言、恢复或 cleanup 失败均使整个块非零退出；cleanup 不删除证据目录，也不能覆盖原始失败码。证据目录需归档并记录绝对路径、受测 SHA、正/负例日志与退出码。

### 4.3 CI

1. Checkout 当前 PR HEAD，并记录 base/head SHA。
2. 通过固定 setup-uv action 安装 uv 0.13.10。
3. 按项目 `.python-version` 安装根环境 CPython 3.14.6；SR-003 矩阵另外显式安装 Ubuntu 3.12 或 Windows 3.14.6。
4. 通过 `setup-go@v5` 和 `go-version-file: examples/echo/plugin/go.mod` 安装满足 Go 1.24 directive 的 Go；记录 `go version`，设置 `GOWORK=off` 并构建 Go Echo。Go 构建步骤统一使用 Bash；Windows Runner 的 `go env GOOS` 必须选择 `.exe` 输出名。
5. 使用 `uv sync --python "$PY" --locked --group dev --extra plugins` 完成唯一一次环境同步；其后的测试、compileall、Smoke 和证据脚本统一使用 `uv run --python "$PY" --no-sync --locked --group dev --extra plugins ...`，不得在测试阶段隐式修复环境。
6. 使用 `scripts/unittest_gate.py` 一次运行 Host、Plugin、Review Context、完整总计四个范围。脚本必须逐范围保存 JSON/log，自动断言 discovered>0、tests_run=discovered、failures/errors/skipped/expected_failures/unexpected_successes/loader_errors 均为 0，且 `discovery_exception` 为 JSON `null`，并在任一范围失败时最终非零退出。
7. `actions/upload-artifact@v4` 必须在 `if: always()` 下上传 gate JSON/log、Smoke 与 Go Echo 证据；Artifact 不存在或文件缺失不得被记为验收 PASS。
8. 任一锁文件漂移、依赖缺失、测试失败、必需用例 skipped、0 tests、脚本错误或环境创建失败均使 Job 失败；不得降级为 pip 临时安装。

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

I1 与 I3 可在 SR-028 实施 Issue 内按依赖顺序执行；I2 只在 SR-001 Workflow 已进入目标分支后执行，并包含 `scripts/unittest_gate.py`、双平台自动门禁和 Artifact；I4 在命令与 Workflow 迁移验收完成后执行。任何阶段依赖未满足时只暂停对应阶段/AC，不把无关设计评审阻塞。

## 7. 验收映射

具体验收 ID、命令和证据要求以 [SR-028](../../SR/SR-028-Python工程工具链与uv环境管理.md) v0.2.11 为准：AC-028-01～03 元数据/版本/依赖分组；AC-028-04 锁漂移 fail-closed；AC-028-05 双 worktree A→B→A；AC-028-06 本地 Go、测试计数与 Smoke；AC-028-07 双平台 CI 与独立堆叠 paths 验证 PR；AC-028-08 Review Context 真实 PR Artifact；AC-028-09 范围边界；AC-028-10 当前文档入口刷新。

设计文档、示例 YAML、历史 pip Run 或迁移前 Artifact 均不构成 uv 实施 PASS。每项产品 AC 只有在固定受测 SHA 上真实运行并留存命令、环境、结果和证据后才可更新状态。

## 8. 参考

- [uv 官方文档：Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
- [uv 官方 CLI：uv sync / uv run / uv lock](https://docs.astral.sh/uv/reference/cli/)
- [uv 0.13.10 Release](https://github.com/astral-sh/uv/releases/tag/0.13.10)
- [setup-uv v10.4.0 Release](https://github.com/astral-sh/setup-uv/releases/tag/v10.4.0)

## 9. 实施后当前复验入口（SR-028 v0.2.15，2026-11-28）

本设计 §3.6/§3.7 的命令已由 Issue #96 / PR #99 落地并已选择性整合到 PR #115 mainline candidate。PR #99 源 Head `83d23e8c04b1c05eb304c2a24a3392f6459ed0f1` 的独立复核 #6094704264 记录 IMPLEMENTED，AC-028-01～10 候选证据已归档。13 个变更路径已逐项对照 PR #115：六个核心实现 Blob 完全一致，其余 7 个治理/文档路径由 #115 更新版本承接。 PR #112 源 Head `dbc0bcbb3a125f143d3648d2cb0331f01368f379` 的 P2-01/P2-02 已关闭；独立 评审评论 #6096938405 给出限定 APPROVE_FOR_READY（0 P0 / 0 P1 / 0 P2）。策略 Bootstrap 47/47、Review Context、SR-003 Ubuntu/Windows 266/266 均 SUCCESS；PR #112 仍 Draft，不合并。 PR #97 源 Head `66a82f09445d5fc32971e91d02b51b7ad6d4ece0` 的状态审计 评审评论 #6096959653 确认 READY 仅代表设计快照；实施证据来自 #99 的 IMPLEMENTED 复核。六份治理文档由 #115 更新版本承接，不原样覆盖；PR #97 不合并。 PR #115 唯一 mainline 集成入口仍为 OPEN / Draft（Base main @ b2ed5eb84114f9c2556a0cd06ed974887b1b70ad），本次代码与策略核验快照 Head `609fb12612c8990a37ba0e174cfacadfd7a7c5d9`；Review Context #46130016832 SUCCESS，Python Toolchain Policy Bootstrap #46130016864 SUCCESS（48/48），SR-003 Regression #46130016833 SUCCESS（Ubuntu 重跑与 Windows 均为 Host 52/52、Plugin 87/87、Review Context 84/84、Total 271/271）。Ubuntu 首次执行在 `test_process_exit_clears_extensions` 出现一次 IPC_TIMEOUT；同一 SHA 的失败 Job 重跑后 271/271 通过，未修改测试或产品代码，作为时序风险保留。当前未合入 main，未标 VERIFIED/RELEASED；PR #115 全量独立复评仍待完成。 当前复验入口：

```bash
uv python install
uv sync --locked --group dev --extra plugins
uv lock --check
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke
```

Go Echo 前置（在 `examples/echo/plugin/`，`GOWORK=off`）：`go build -trimpath -o bin/echo-plugin .`，Windows 目标为 `bin/echo-plugin.exe`。CI 矩阵、paths 与诊断/正式 Artifact 契约见 §3.8；锁漂移、A→B→A 隔离和双平台 Run 的实测证据记录在实施 Issue #96 与实施 PR #99，不在本设计文档中重复或改写。PR #115 当前 Head 的双平台复验未完成前，候选证据不得升级为 mainline VERIFIED。

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
| 2026-11-27 | 0.2.4 | GPT-6.2（ChatGPT） | §0、§3.5～3.8、§4.1～4.3、§6～§7 | 按 评审评论 #6082874849 补齐 Go 1.24 前置与 GOWORK=off、锁漂移负例、双 worktree A→B→A、测试统计、Windows 3.14.6、独立堆叠验证 PR 和文档验收映射；修正 `.venv/` 既有规则表述 | 关闭 SR-028 的实施歧义，同时保持所有产品 AC NOT_RUN 和 SR DRAFT | Issue #12；PR #46；评审评论 #6082874849；SR-028 v0.2.6 |
| 2026-11-27 | 0.2.5 | GPT-6.2（ChatGPT） | §0、§3.6～3.8、§4.1～4.3、§6～§7 | 按 评审评论 #6083225844 修复 Bash fail-open：锁漂移与 A→B→A 从块首 fail-fast 并使用保码 cleanup trap；A 返回阶段全部改用 `uv run --no-sync`；新增标准库 unittest gate 并在双平台 Workflow 自动断言 skipped=0/非空测试且上传报告；Python 检查使用显式 uv 项目环境；补齐 A/B/A sys.prefix、原始 direct_url、ignore 证据持久化；Go 构建子 shell 恢复 CWD，按 GOOS 生成 Windows `.exe`，澄清 Workflow shell 边界 | 消除 R028-10～16 的 fail-open、自动同步、CI skipped 假 PASS、隐式解释器及跨平台/证据歧义；保持产品 AC NOT_RUN 与 SR DRAFT | Issue #12；PR #46；评审评论 #6083225844；SR-028 v0.2.7 |
| 2026-11-27 | 0.2.6 | GPT-6.2（ChatGPT） | 文档头、§0、§3.6、§3.8、SR 引用 | 按第五轮 评审评论 #6083641266 修复 Review Context 诊断 Artifact 与三文件正式 Artifact 的契约冲突；明确 `loader_errors` 来源/计数及 discovery 异常；统一逐范围与整体 `exit_code` | 关闭 R028-17 P1 与 R028-18 P2，确保失败诊断可留存且失败 Run 不产生完成态 Artifact；产品 AC 仍 NOT_RUN | Issue #12；PR #46；评审评论 #6083641266；SR-028 v0.2.8 |
| 2026-11-27 | 0.2.7 | GPT-6.2（ChatGPT） | 文档头、§0、§3.6、§3.8、§4.3、§7 | 按第六轮 评审评论 #6083872622 修复 AC-028-08 受控负例：保留有效 Agent.md 与测试门禁，通过临时 Workflow PR 将生成器 `--base` 注入全零 SHA 形成可执行失败路径；run-context 记录实际/注入 SHA 与模式；补齐 AC 证据中的负例不合并、恢复后成功重跑；统一 gate 的 `discovery_exception=null` 断言 | 关闭 R028-21 P1 与 R028-22/23 P2；不修改测试代码或产品 Workflow，不将设计整改视为产品实施，SR-028 继续 DRAFT / NOT_RUN | Issue #12；PR #46；评审评论 #6083872622；SR-028 v0.2.9 |
| 2026-11-28 | 0.2.8 | GPT-6（ChatGPT） | 文档头、§0、修订记录 | 更新 SR-028 第七轮专项设计批准和 #96/#97/#99/#112 的当前状态/固定基线 | 避免把第六轮历史评审当作最新状态，或将旧快照候选实施混入当前恢复分支产品状态 | Issue #12；Issue #96；PR #46/#97/#99/#112；评审评论 #6084094037 |
| 2026-11-28 | 0.2.9 | GPT-6.2（ChatGPT） | 文档头、§0、§7、修订记录 | 将 SR-028 当前版本、#96/#97/#99/#112 状态和候选实施证据边界同步到 G02 | 防止旧版本指针及历史第六轮门槛继续误导实施者 | Issue #12/#96；PR #46/#97/#99/#112；评审评论 #6084094037/#6094704264/#6086849161 |
| 2026-11-28 | 0.2.10 | GPT-6.2（ChatGPT） | 文档头、§0、§7、§9、修订记录 | 将 SR-028 当前状态更新为 IN_PROGRESS，纳入 PR #99 已实现并进入 PR #115 候选的 uv 入口，补充当前复验命令与门槛 | 区分设计 READY、候选实现证据、mainline 集成和最终 VERIFIED 状态 | Issue #96；PR #99/#112/#115；SR-028 v0.2.12 |
| 2026-11-28 | 0.2.11 | GPT-6.2（ChatGPT） | 文档头、§0、§9、修订记录 | 更新 PR #112 P2 修复与 45/45 策略测试，记录共享策略已选择性纳入 PR #115，区分一次性 Bootstrap 与 main 合入后的可信策略 | 使 G02 的工程基线状态与 SR-028、策略规范及唯一 mainline 收敛入口一致 | Issue #50/#96/#111；PR #99/#112/#115；SR-028 v0.2.13 |
| 2026-11-28 | 0.2.12 | GPT-6.2（ChatGPT） | 文档头、§0、§9、修订记录 | 同步 #99 文件级收编、#112 P2 独立复评、#97 READY 状态来源与 PR #115 双平台重跑证据 | 使 G02 与 SR-028、SR 索引和唯一 mainline 集成入口保持一致 | Issue #50/#96/#111；PR #97/#99/#112/#115 |
| 2026-11-28 | 0.2.13 | GPT-6.2（ChatGPT） | §0、§9、修订记录 | 跟随 SR-028 v0.2.15 修正当前实施状态与 P2 独立复评引用 | 避免 G02 入口继续引用过期 SR-028 版本 | Issue #50/#96/#111；SR-028 v0.2.15；PR #99/#112/#115 |
