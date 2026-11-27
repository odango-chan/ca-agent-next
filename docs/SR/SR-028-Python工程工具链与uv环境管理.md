# SR-028：Python 工程工具链与 uv 环境管理

> 文档类型：软件需求（SR）  
> SR 版本：0.2.10\
> 修订日期：2026-11-27\
> 状态：READY（实施主状态）；第七轮独立模型 Review [#6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6084094037)（Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`）：APPROVE_FOR_READY（0 P0 / 0 P1 / 2 P2）；实施 Issue [#96](https://github.com/odango-chan/ca-agent-next/issues/96) 已建立；AC-028-01～10 产品执行全部 NOT_RUN。两个非阻断 P2 纳入实施证据要求\
> 创建日期：2026-11-26  
> 所属阶段：G02 工程治理支撑  
> 上游需求：[IR-007](../IR/IR%20总登记册.md#ir-007)  
> 设计依据：[G02 Python 工程工具链与环境管理设计说明书](../设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md) v0.2.8 §1～§8；[SR-002](SR-002-Python%20核心与宿主基础骨架.md) v0.2.10 §2.1；[SR 管理规范](../规范/SR%20管理规范.md) v0.8.1 §6.1、§8.2、§8.3\
> 设计/治理 Issue：[ca-agent-next #12](https://github.com/odango-chan/ca-agent-next/issues/12)；实施 Issue：[ca-agent-next #96](https://github.com/odango-chan/ca-agent-next/issues/96)；原设计 Issue [#35](https://github.com/odango-chan/ca-agent-next/issues/35) 已 CLOSED，仅作历史来源\
> 目标仓：`odango-chan/ca-agent-next`  
> 最新独立复评：PR #46 Review [#6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6084094037)，固定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`；平台事件 COMMENTED，独立模型结论 APPROVE_FOR_READY（0 P0 / 0 P1 / 2 P2）。两个 P2 不阻断 READY，但必须按实施 Issue #96 在 AC-028-08 证据回填时关闭\
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：其他仓库迁移、生产级供应链安全、运行时架构改造和完整 Python 版本矩阵资格认证

## 0. 第七轮独立设计复评与实施 READY（2026-11-27）

第七轮独立复评 [PR #46 Review #6084094037](https://github.com/odango-chan/ca-agent-next/pull/46#pullrequestreview-6084094037) 绑定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2`，模型结论为 `APPROVE_FOR_READY`（0 P0 / 0 P1 / 2 P2），平台事件为 `COMMENTED`。独立评审确认 AC-028-01～10 全部 DESIGN_PASS；产品执行仍全部 NOT_RUN。R028-21 已 CLOSED；两个非阻断 P2 分别为受控负例 PR 的 base/来源分支及单文件 diff 约束、AC-028-08 证据列对 run-context 三行和负例 PR 文件清单的核验。用户已批准将 SR-028 提升为 READY，并按 SR 管理规范 §8.2 在未合并候选设计 SHA 上开展范围受限实施；正式实施追踪为 [Issue #96](https://github.com/odango-chan/ca-agent-next/issues/96)。

- **评审范围：**核查 uv 版本/锁文件、worktree 虚拟环境隔离、与现有 setuptools 工程共存、CI 与回退/失败路径。
- **外部依赖/证据状态：**设计可独立评审；SR-028 无实施 Issue，不应把 PR #32 的既有 CI 验收误作 uv 迁移 PASS。
- **评审必须确认：**明确每项 AC 的文件和命令、预期、依赖与非目标，记录不满足项；只有设计审查通过才可将 SR 送实施 READY 并另开实施 Issue。当前不执行依赖迁移，不改变 Python Runtime 架构。

## 1. 目标

在 `ca-agent-next` 根 Python 项目统一采用 uv 管理依赖解析、锁文件、解释器、worktree 虚拟环境和项目命令，确保本地、多个 worktree 和 GitHub Actions 使用一致且可复现的依赖集合。

本 SR 只覆盖 Next 根 Python 项目。其他仓库不得因本 SR 自动迁移。

## 2. 实施范围

1. 在根 `pyproject.toml` 中固定 uv CLI 版本要求，并使用 PEP 735 dependency group 管理开发/测试依赖。
2. 保留原有项目元数据、`requires-python >=3.11`、`setuptools.build_meta` 构建后端和空运行时依赖集合。
3. 将 SR-001 所需 PyYAML 放入 `dev` 依赖组，不进入 `[project].dependencies`。
4. 生成并提交 `uv.lock`；添加纯文本 `.python-version`（内容仅为 `3.14.6`）；核实并保留 `.gitignore` 中现有独立 `.venv/` 忽略规则，仅在确实缺失时追加，禁止重复或删除其他规则。
5. 统一本地和 CI 的安装、测试、Smoke、脚本执行命令为 `uv sync --locked` / `uv run --locked`。
6. 在独立 worktree 中验证每个 checkout 使用自己的 `.venv/`，不共享 site-packages 或 editable distribution metadata。
7. 从含 SR-001/SR-003 的目标分支迁移现有工作流的 Python 安装入口，保留 G02 §3.8 的双平台回归；新增仅依赖标准库的 `scripts/unittest_gate.py`，自动运行 Host、Plugin、Review Context 和完整总计并 fail-closed；在真实 PR Workflow 中运行测试门禁和上下文生成器，上传 JSON/log 证据。
8. 更新 `README.md`、`Agent.md`、`docs/SR/SR-002-Python 核心与宿主基础骨架.md`、`docs/SR/SR-003-统一插件管理器与扩展通信.md`、`docs/验收与实施/演示验收基线.md` 及 G02/SR-028 中的当前复验入口，记录实际 uv/Python/Go 版本、命令、环境和证据。只更新当前复验命令；不得改写带历史受测 SHA 的 pip 命令、原始运行记录或 VERIFIED 证据。具体文件与验收归属见 AC-028-10。

不得在 SR-001 PR #32 分支中实施上述迁移。

## 3. 非目标

- 不改变 Agent Core、Host、Model Loop、Runtime、Skill 或 Plugin 的运行时行为和公开 API。
- 不改变 distribution 名称、import package、项目版本、Python 元数据下限或 setuptools 构建后端。
- 不把 PyYAML 或其他开发工具放入运行时依赖。
- 不迁移 ca-agent-demo、ca-agent、ca-runtime、Compiler、Skill Studio 或其他仓库。
- 不引入 requirements.txt/pip-tools/Poetry/Conda 的第二套项目依赖管理入口。
- 不新增自定义包签名、额外 SHA-256、Trust Registry、生产级依赖扫描或复杂供应链安全治理。
- 不以 `requires-python >=3.11` 声明替代实际 Python 版本矩阵测试；首版只按 G02 固定的 CPython 3.14.6 验收。

## 4. 依赖与阶段门禁

### 4.1 设计依赖

- G02 v0.2.7 与 SR-002 v0.2.10 的 Python distribution/build metadata 是稳定输入；SR-003 v0.3.11 的 Go Echo 构建和 Plugin 测试是本地完整测试的直接前置。
- 设计评审不依赖 SR-001 的代码合并；可以独立评审 uv 与 worktree 方案。

### 4.2 实施依赖

- AC-028-01～AC-028-06：SR-028 达到 READY、独立实施 Issue 建立后即可执行，不依赖 Agent Runtime 产品阶段。
- AC-028-07（CI 环境与测试入口）和 AC-028-08（SR-001 Workflow/Artifact 迁移）：所需 SR-001 Workflow 与脚本已随 PR #32 合入。独立实施 PR 核对目标分支仍含这些入口及 SR-003 回归工作流后，按 G02 §3.8 迁移与复验。既有成功结果不计为迁移 PASS。
- SR-028 的实施 Issue 为 [#96](https://github.com/odango-chan/ca-agent-next/issues/96)；设计/治理整改由 Issue #12 跟踪，原 Issue #35 已 CLOSED。实施从 PR #46 Head `93f1389e7c5968cd30e8a74137207094864ecca0` 派生独立分支，按 §8.2 限定在候选设计基线上执行；不得修改 PR #46 分支或 main。
- 第七轮两个非阻断 P2 由 Issue #96 作为实施补证要求：受控负例 PR 必须以已包含 SR-028 Workflow 迁移和 `scripts/unittest_gate.py` 的实施分支为 base，head 累积 diff 仅含 `.github/workflows/review-context.yml`；AC-028-08 必须核验诊断 Artifact 的 `run-context.txt` 中真实 `base_sha`、全零 `generator_base_sha`、`failure_injection=invalid-base` 三行及负例 PR 文件清单。

## 5. Acceptance

| ID | 验收条件 | 必需证据 |
|---|---|---|
| AC-028-01 | 根 pyproject 保留 `ca-agent-next`、版本 `0.1.0`、`requires-python >=3.11`、setuptools build backend、src package discovery 和空运行时依赖；保留 SR-003 的 plugins extra，仅增加 uv 与开发依赖配置 | pyproject diff；distribution metadata 检查；确认 PyYAML 不在 Requires-Dist runtime metadata |
| AC-028-02 | `.python-version` 文件内容精确为 `3.14.6`；uv CLI 固定为 0.13.10；setup-uv 使用 v10.4.0 不可变 commit `1db35dd8eee11c5894872e0b383ae6c406cf738d` 并显式设置 version | 文件内容、`uv --version`、`uv run --no-sync --locked --group dev --extra plugins python --version`、Workflow 日志和配置 |
| AC-028-03 | PyYAML 位于 `[dependency-groups].dev`，不进入 Agent Core 运行时依赖 | pyproject/uv.lock；distribution metadata 测试 |
| AC-028-04 | 在干净临时 worktree 先以明确正例证明 `uv sync --locked --group dev --extra plugins` 与 `uv lock --check` 均退出 0；随后只把 `pyproject.toml` 中唯一的 `PyYAML>=6.0,<7` 临时改为 `PyYAML>=6.0,<8`，不运行 `uv lock`。两条负例分别在 `if` 中捕获退出码，必须非零且诊断匹配 `lockfile ... needs to be updated`；每次失败后 `git diff --exit-code HEAD -- uv.lock` 与 `git status --porcelain -- uv.lock` 均证明锁文件未变化。恢复 pyproject 后两文件均 clean。整个 Bash 块从首行 `set -euo pipefail`，EXIT trap 清理 worktree、保留原始退出码并保留证据目录；初始正例、修改、诊断、锁文件断言、恢复或 cleanup 任一失败均整体非零。修改约束的 Python 命令必须使用已 locked sync 的 `uv run --no-sync --locked --group dev --extra plugins python -c ...`，不得调用裸 `python` | 干净基线 SHA；两条正例的日志/退出码；临时依赖约束 diff；两条负例完整 stdout/stderr、诊断匹配结果和非零退出码；每次 `uv.lock` 未变化证明；恢复后的 clean diff；EXIT trap 清理结果；保留的证据目录绝对路径 |
| AC-028-05 | 用两个临时 Git worktree 执行 A→B→A：A sync/断言/Host gate，B sync/断言/Host gate，再返回 A，不重新 sync 而重复断言和 Host gate。每次先清除继承的 `UV_PROJECT_ENVIRONMENT`。A/B 各自断言 `.venv/pyvenv.cfg` 存在、`sys.prefix` 指向本 worktree `.venv`、`sys.executable` 位于本 venv、`ca_agent_next.__file__` 位于本 worktree `src/`，`direct_url.json` 的 `dir_info.editable=true` 且原始 file URL 指向本 worktree。返回 A 的检查、Host gate 和最终比较必须全部通过 `uv run --no-sync --locked --group dev --extra plugins`，不得运行 `uv sync`、`uv python install` 或普通 `uv run`。A-before/A-return 的完整环境 JSON 与 direct_url.json 必须逐字一致；A/B 的 root、venv、sys.prefix、executable、module、direct_url URL 和 source 必须不同。脚本从首行 `set -euo pipefail`，EXIT trap 清理 worktree、保留原始退出码；证据目录不随 cleanup 删除 | 两个 worktree 的创建/清理命令与 trap 退出码；A-before/B/A-return 三份完整 JSON（root、venv、sys_prefix、executable、module、原始 direct_url URL、direct_url_source、editable）；三份原始 direct_url.json；A/B/A 的 `git check-ignore -v .venv/pyvenv.cfg` 输出；三次 Host gate JSON/log/exit code；A-before 与 A-return 的逐字相等证明；证据目录绝对路径和归档附件 |
| AC-028-06 | 本地完整测试前必须具备 Go 工具链。`examples/echo/plugin/go.mod` 的 Go directive 为 `1.24`；记录满足该 directive 的实际 `go version`，构建前设置并验证 `GOWORK=off`，从 Plugin 模块目录按 `GOOS` 构建 Echo，Windows 目标文件名必须为 `echo-plugin.exe`。构建命令不得污染后续仓库根 CWD。随后使用 `scripts/unittest_gate.py` 分别运行 Host、Plugin、Review Context 和完整总计四个范围，并执行 Host Smoke | Go 版本、`go env GOWORK=off`、GOOS、Linux/Windows 对应 Go build 命令与二进制路径、构建前后 CWD；四范围 gate JSON/log/summary/exit code；Smoke stdout/stderr/exit code；完整环境和受测 SHA。统计规则见 §5.1 |
| AC-028-07 | GitHub Actions 固定 setup-uv/uv 版本。SR-003 矩阵为 Ubuntu Python `3.12` 和 Windows Python `3.14.6`；Python/uv 步骤分别使用 Bash/PowerShell，Go 构建步骤均使用 Bash；显式选择并记录 `--python`，Windows 精确断言 `Python 3.14.6`；Go 使用 `setup-go@v5` 的 `go-version-file`，设置 `GOWORK=off`，Windows GOOS 构建 `.exe`。`pull_request.paths` 必须覆盖且至少包含：`pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`、`src/**`、`tests/**`、`examples/echo/**`、`scripts/review_context.py`、`scripts/unittest_gate.py`、`docs/SR/SR-003-*`、`.github/workflows/review-context.yml`、`.github/workflows/sr003-plugin-ci.yml`。两个矩阵 Job 在 sync 后必须通过 `uv run --python "$PY" --no-sync --locked ... scripts/unittest_gate.py` 自动运行 Host、Plugin、Review Context、完整总计四范围；每个范围必须 `discovered>0`、`tests_run=discovered`、`failures=errors=skipped=expected_failures=unexpected_successes=loader_errors=0`、`discovery_exception` 为 JSON `null`且逐范围 `exit_code=0`。任何 skip/0 tests/失败都使 Job 非零。SR-003 矩阵诊断证据仍由 `if: always()` Artifact 保存。Review Context Workflow 必须分别上传诊断 Artifact（名称 `review-context-diagnostics-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，`if: always()`）和正式三文件 Artifact（名称 `review-context-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，`if: success()`、`if-no-files-found: error`）；两者不得混装。除主实施 PR 外，必须按 §5.2 建立独立堆叠验证 PR，其 base 为已包含迁移的实施 PR 分支，累积 diff 只能包含 `.github/workflows/review-context.yml`；在同一次 `pull_request.synchronize`、同一 Head SHA 下核验 Review Context Job 与 Ubuntu 3.12/Windows 3.14.6 两个非 skipped SR-003 Job | Workflow diff；两个 PR 的 base/head SHA 与文件清单；同一 synchronize 事件的 PR number/head SHA；两个 Workflow Run URL；SR-003 两个 Job 的实际 Python/Go 版本、四范围 gate 报告/Artifact、逐范围和整体退出码；Review Context 的两个 Artifact 名称、文件清单及成功/失败路径；Review Context Job 日志。示例 YAML 不是 PASS 证据 |
| AC-028-08 | SR-001 Workflow 已集成后，将 Review Context 安装/测试入口迁移到 uv。成功 `pull_request` Run 必须产生两个分离 Artifact：诊断 Artifact `review-context-diagnostics-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，`if: always()`，包含 run-context、Review Context gate JSON/log/summary、生成器 stdout/stderr/exit-code 和输出 manifest，但不得包含三份正式文件；正式完成态 Artifact `review-context-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`，仅 `if: success()` 上传，`if-no-files-found: error`，必须作为 Job 最后一步且位于 `if: failure()` 失败报告步骤之后；生成器退出 0 前必须逐一断言三份输出文件均存在，缺少任一文件即失败并禁止正式上传；解包后恰含 `review-scope.json`、`评审上下文.md`、`统一评审提示词.md` 三份文件且无其他文件。**受控负例 PR 必须保持 head 版 `Agent.md` 与有效 `review_scope` 不变**，不得通过破坏 `review_scope` 触发生成器失败（测试 fixture 在模块导入时从根 `Agent.md` 派生，会先令 gate 失败）。负例仅在临时 PR 的 `.github/workflows/review-context.yml` 中，将生成器 `--base "$BASE_SHA"` 替换为全零 SHA `0000000000000000000000000000000000000000`；run-context 同时记录真实 `base_sha`、注入的 `generator_base_sha` 和 `failure_injection=invalid-base`。Review Context gate 必须全部通过；生成器必须实际执行并非零退出，stderr 包含 `base 提交对象不可读取`；诊断 Artifact 必须含 gate PASS JSON/log/summary、generator stdout/stderr/exit-code 和 manifest（三个正式文件均标记 MISSING），正式 Artifact 不存在。无效 `review_scope` 的拒绝能力由现有 `test_validation_failure_writes_no_artifact` 与 `test_subprocess_returns_non_zero_with_location` 临时仓库单元测试覆盖，且两项随 gate 通过。负例 PR 不得合并；恢复生成器 `--base "$BASE_SHA"`、`generator_base_sha=$BASE_SHA`、`failure_injection=none` 后，在恢复后的新 Head 重跑成功路径并核验两个 Artifact，最后关闭负例 PR（未合并） | 成功真实 Run URL/事件/base/head SHA、Summary、两个 Artifact 名称与下载清单、正式 Artifact 三文件逐一内容核对；负例 PR URL、未合并/关闭状态、负例 Head SHA、`Agent.md` blob SHA 与有效内容证明；负例 Run URL 和事件/base/head SHA；Review Context gate PASS JSON/log/summary 与逐范围退出码；生成器 stdout/stderr（含预期 `base 提交对象不可读取`）、非零 `generator.exit-code`、manifest 三项均 MISSING；诊断 Artifact 存在且正式 Artifact 不存在；两个无效 `review_scope` 单元测试名称、执行结果和 gate PASS 证据；恢复后的 commit/Head SHA、成功 Run URL、正常 `generator_base_sha`/`failure_injection=none`、两个 Artifact 下载清单及成功内容核对；测试统计和逐范围/整体退出码 |
| AC-028-09 | 不修改其他仓库、不改变运行时依赖和 setuptools backend、不引入额外签名/hash/Trust Registry 机制；不得修改 Agent Runtime 行为或公开 API | PR 文件清单、pyproject metadata、设计/实施边界审查 |
| AC-028-10 | 当前工具链复验入口必须同步到 `README.md`、`Agent.md`、SR-002、SR-003、演示验收基线及 G02/SR-028。README/Agent 提供当前安装、测试、Smoke 和 Go Echo 前置入口；SR-002/SR-003/演示基线保留原始 pip 受测命令、SHA、时间与 PASS 事实，只新增明确标记为 SR-028 迁移后复验的 uv 命令，不覆盖或重写历史证据。不得把当前 uv 复验入口误写成 SR-002/SR-003 原始验收环境 | 上述每份文件的 diff 与逐文件核对清单；当前命令可执行入口；历史 pip 命令及受测 SHA 前后对照；README/Agent 与 SR-028 AC 的双向映射 |

所有 AC 必须逐项记录受测 SHA、环境、命令、预期/实际结果和证据。未执行保持 NOT_RUN；依赖未满足的 AC 记录 BLOCKED，不得推导 PASS。

### 5.1 AC-028-06 测试命令与统计规则

本地从仓库根目录、CPython 3.14.6 和已完成 `uv sync --locked --group dev --extra plugins` 的环境执行；Plugin 测试前必须先按 G02 §3.6 构建 Go Echo。所有测试命令均使用 `--no-sync --locked`，不得在验收过程中自动修复环境。

| 统计范围 | 命令/选择器 |
|---|---|
| Host | `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite host --output-dir "$EVIDENCE_DIR/host"` |
| Plugin | `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite plugin --output-dir "$EVIDENCE_DIR/plugin"` |
| Review Context | `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite review-context --output-dir "$EVIDENCE_DIR/review-context"` |
| 完整总计 | `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --suite total --output-dir "$EVIDENCE_DIR/total"` |
| 全部四范围 | `uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir "$EVIDENCE_DIR/unittest-gate"` |
| Host Smoke | `uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke` |

`scripts/unittest_gate.py` 是 SR-028 实施范围内新增的标准库脚本；`--suite` 可重复，省略时运行全部四范围。每个范围通过 `unittest.TestLoader.discover` 单独加载，discovery 目录为 `tests`，pattern 分别为 `test_host.py`、`test_plugin.py`、`test_review_context.py`、`test*.py`；不要求 `tests/__init__.py`。

每个范围必须记录 `discovered`、`tests_run`、`passed`、`failures`、`errors`、`skipped`、`expected_failures`、`unexpected_successes`、`loader_errors`、`loader_error_messages`、`discovery_exception` 和逐范围 `exit_code`。`discovered` 取 `suite.countTestCases()`；`passed = tests_run - failures - errors - skipped - expected_failures - unexpected_successes`。`loader_errors` 精确定义为该范围独立 `TestLoader` 在 `discover()` 后 `len(loader.errors)`；`loader_error_messages` 原样保存 `loader.errors` 列表。`errors` 是 `TextTestResult.errors` 的条目数；加载失败可能同时形成 `_FailedTest` 并计入 `errors`，不对两字段相加或去重，二者必须分别为 0。若 `discover()` 抛出异常，完整记录在 `discovery_exception`，该范围失败。单范围 `exit_code=0` 当且仅当 `discovered>0`、`tests_run==discovered`、failures/errors/skipped/expected_failures/unexpected_successes/loader_errors 全部为 0 且 `discovery_exception` 为 JSON `null`，否则为 1。每项 JSON 记录自己的 `exit_code`；`summary.json` 同时记录各范围 `exit_code` 和整体 `exit_code`。整体退出码仅在所有已选范围均为 0 且所有报告写入成功时为 0，否则为 1；进程退出码必须与整体值一致。脚本即使某范围失败也必须继续执行其他范围、写出每个范围 JSON/log 和总 `summary.json`，最后统一按整体退出码返回；不得用人工查看绿色 Job 替代该自动门禁。

Host Smoke 必须退出 0，成功 stdout 符合演示验收基线，stderr 为空。所有 gate JSON/log、summary、Smoke 输出均须保留并绑定受测 SHA。

### 5.2 AC-028-07 独立路径触发 PR 时序

1. 主实施 PR 完成 uv、锁文件、解释器、Go、`scripts/unittest_gate.py` 和两个 Workflow 的迁移；其累积 diff 可以包含全部实施文件。先核验主实施 PR 的常规 CI、四范围 gate 自动门禁与 AC-028-06/08。
2. 在主实施 PR 分支仍可用时，创建一个独立堆叠验证分支，并以主实施 PR 的 head branch 作为验证 PR 的 base。base 已包含 `sr003-plugin-ci.yml` 对 `.github/workflows/review-context.yml` 的 paths 规则。
3. 验证 PR 相对该 base 的三点差异文件清单必须且只能是 `.github/workflows/review-context.yml`。只在该文件增加一条明确的路径验证注释即可，不修改其他文件；打开 PR 后，再向同一文件推送第二个 commit，以产生可核对的 `pull_request.synchronize` 事件。SR-003 两个矩阵 Job 的诊断 gate JSON/log/summary Artifact 按 `if: always()` 上传。Review Context Workflow 必须上传两个互相独立的 Artifact：诊断 Artifact `review-context-diagnostics-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}` 按 `if: always()` 上传，仅含 run-context、gate JSON/log/summary、生成器日志/退出码/manifest；正式 Artifact `review-context-pr-${PR_NUMBER}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}` 仅按 `if: success()` 上传，且文件清单只能是三份正式输出；`if: failure()` 失败报告必须先于正式 Artifact，正式 Artifact 必须是 Job 最后一步。诊断目录不得包含正式三文件，正式 Artifact 不得包含 gate/log/manifest；`if-no-files-found: error` 必须保留。核验 Artifact 内容而非只核验 Run conclusion。
4. 对该次 synchronize，核对 Review Context Workflow 与 SR-003 Workflow 都由同一 PR number、同一 head SHA 触发；Review Context Job 成功，SR-003 Ubuntu 3.12 与 Windows 3.14.6 两个 Job 均实际执行且非 skipped。保存两个 Run URL、事件、head SHA、Job 日志和测试统计。
5. 不得用主实施 PR 中某个只修改单文件的 commit 代替本验证，因为 `paths` 根据 PR base...head 累积差异判定。验证 PR 不合并；主实施 PR 和验证 PR 的合并均须另行授权。

## 6. 交付门禁

- 设计评审通过后，先将 SR-028 更新为 READY，再创建独立实施 Issue。
- 实施分支从最新目标恢复分支基线创建，使用 `chore/issue-<编号>-sr-028-uv-python-toolchain`。
- pyproject.toml 与 uv.lock 必须在同一提交中更新；不得提交 `.venv/`。
- 每个实现批次 Commit + Push，并通过 GitHub API 核对远端分支 SHA。
- PR 必须关联实施 Issue、SR-028、G02 固定设计 SHA，并逐项回填 AC。
- 不得修改 main、合并 PR 或发布 Release，除非另有明确授权。

## 7. 当前状态与停止条件

SR-028 当前为 READY，正式实施追踪为 [Issue #96](https://github.com/odango-chan/ca-agent-next/issues/96)。第七轮独立复评 Review #6084094037 对固定 Head `93f1389e7c5968cd30e8a74137207094864ecca0` / Base `3c7c48383c52504a4861900bc1f8b731442f16c2` 给出 APPROVE_FOR_READY（0 P0 / 0 P1 / 2 P2）。AC-028-01～10 产品执行全部 NOT_RUN；不得将设计 PASS 或旧 Run 45947586118 当作 uv 产品验收。两个非阻断 P2 按 Issue #96 纳入实施证据，完成前不得将 AC-028-08 标记 PASS。实施仅基于候选设计 SHA 按 SR 管理规范 §8.2 受限执行，不修改 PR #46、PR #32 历史分支或 main。

若评审发现 G02 与 SR-002 的 setuptools/运行时依赖约束冲突，先修订设计，不允许实施者自行选择替代后端或把开发依赖升级为运行时依赖。

## 修订记录


| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | GPT-6.2（ChatGPT） | 全文 | 新建 Python 工程工具链与 uv 环境管理 SR，定义范围、阶段依赖、AC 和交付门禁 | 将 uv 迁移与 SR-001 实施修复分离，避免把工具链变更混入已有功能 PR | Issue #35；IR-007；G02 |
| 2026-11-26 | 0.1.1 | GPT-6.2（ChatGPT） | §2、§4～§5 | 将 review_context.py 的执行前置明确绑定 PR #32 集成；把当前基线 unittest/Host Smoke 与后续 Workflow 迁移验收分离 | 保证 SR-028 的独立 I1 可先行实施，不要求引用尚未集成的脚本；避免 AC-028-06/07/08 重复或提前要求 | Issue #35；PR #32；G02 |
| 2026-11-26 | 0.1.2 | GPT-6.2（ChatGPT） | §2、§5 | 补齐 `.python-version`、`.gitignore`、setup-uv action 固定配置、`uv sync` 项目安装与构建可复现边界的明确验收 | 使 DeepSeek Harness 可按固定文件内容/配置实现，并防止对 wheel 级可复现性作超范围承诺 | Issue #35；G02 v0.1.2 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 提交设计待评审、明确新旧契约/验收隔离并保留 DRAFT 主状态 | 统一中央评审批次，防止旧版发布证据冒充新版资格 | Issue #12；PR #45；SR-029 |
| 2026-11-26 | 0.1.4 | Codex / GPT-6 | §2、§4、AC-028-01/05～08 | 复核 PR #32/#34 集成后的工作流与真实依赖，修正完整测试命令 | 避免等待已合并 PR 或漏装 plugins extra | Issue #12/#35，PR #46，SR-028 |
| 2026-11-27 | 0.2.0 | Codex / GPT-6 | AC-028-07 | 完整 Plugin 依赖、矩阵和触发条件 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.1 | Codex / GPT-6 | AC-028-07 | 增加只改 Review Context workflow 的双平台证据 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |
| 2026-11-27 | 0.2.2 | GPT-6（ChatGPT） | 第三轮设计自评/历史修订表 | uv 锁、worktree、完整 Plugin/Host/Review Context 和仅改 Workflow 的双平台触发验收已明确；真实 CI 尚未运行；将第二轮结论保留为历史、登记第三轮独立复评候选并按版本整理记录 | 设计范围可供外部评审而不提前授权代码实施或夸大 AC 状态 | Issue #12；PR #46；SR-028 |
| 2026-11-27 | 0.2.3 | GPT-6（ChatGPT） | 设计依据/修订记录 | 将 AC-028-07 对应的 G02 跨 OS 显式 --python 命令参考统一到 v0.2.2；模块主状态仍 DRAFT | 不让实施方误将 Bash 与 PowerShell 环境变量混用或在 Ubuntu 3.12 误装默认 3.14.6 | Issue #12/#35；PR #46；G02 |
| 2026-11-27 | 0.2.4 | GPT-6（ChatGPT） | 设计依据、修订记录 | 同步 G02 v0.2.3 关于 Go 工具链与 Python 矩阵执行的准确描述；AC 未执行 | 保持独立设计评审的版本引用一致 | Issue #12/#35；PR #46；G02 |
| 2026-11-27 | 0.2.5 | GPT-6（ChatGPT） | 文档头、评审状态、修订记录 | 将第三轮独立模型 Review #6082541121 的限定结论替换第三轮自评状态 | 区分工具链设计认可与 uv / 双平台产品验收 | Issue #12；PR #46；Review #6082541121 |
| 2026-11-27 | 0.2.6 | GPT-6.2（ChatGPT） | §2、§4～§7、AC-028-04～10 | 按 Review #6082874849 补齐锁漂移负例、双 worktree A→B→A、Go 前置与完整测试统计、Windows 3.14.6、独立堆叠 PR 时序和文档验收 AC；修正版本导航及 `.venv/` 规则；保持 DRAFT/NOT_RUN | 关闭 R028-01～09 的设计缺口，不把文档整改误作产品实施或 READY | Issue #12；PR #46；Review #6082874849；G02 v0.2.4 |
| 2026-11-27 | 0.2.7 | GPT-6.2（ChatGPT） | 文档头、§0、§2、§4、AC-028-04～07、§5.1～5.2 | 按 Review #6083225844 补齐锁漂移/Worktree fail-fast 与保码 cleanup、A 返回 `--no-sync`、显式 uv 项目解释器、标准库 unittest gate 自动断言 skipped=0 和 discovered>0、双平台 Artifact、A/B/A 完整 sys.prefix/direct_url/ignore 证据，以及 Go CWD/Windows `.exe` 规则；产品 AC 全部仍 NOT_RUN | 修复四项阻断 READY 的 P1 和三项 P2，不把设计整改当成产品实施或验收 | Issue #12；PR #46；Review #6083225844；G02 v0.2.5 |
| 2026-11-27 | 0.2.8 | GPT-6.2（ChatGPT） | 文档头、§0、AC-028-07/08、§5.1～5.2、§7 | 按第五轮 Review #6083641266 分离 Review Context 诊断 Artifact 与三文件正式 Artifact；恢复完整 paths 枚举；定义 `loader_errors`/`loader_error_messages`/`discovery_exception`；统一逐范围与整体 `exit_code` | 关闭 R028-17 P1、R028-18/19/20 P2，避免诊断文件污染 AC-028-08 完成态交付；保持 DRAFT 与全部产品 AC NOT_RUN | Issue #12；PR #46；Review #6083641266；G02 v0.2.6 |
| 2026-11-27 | 0.2.9 | GPT-6.2（ChatGPT） | 文档头、§0、AC-028-08、§5.1、修订记录 | 按第六轮 Review #6083872622 修复受控负例的 gate/生成器先后矛盾：改为有效 Agent.md + 测试 gate PASS + 临时 Workflow PR 注入无效 base SHA 触发生成器失败；补齐负例 PR 不合并、恢复后成功重跑的证据；明确 discovery_exception 成功时为 JSON null | 关闭 R028-21 P1 与 R028-22/23 P2；保留 invalid review_scope 单元测试覆盖，产品 AC 仍全部 NOT_RUN，SR 保持 DRAFT | Issue #12；PR #46；Review #6083872622；G02 v0.2.7 |

| 2026-11-27 | 0.2.10 | GPT-6.2（ChatGPT） | 文档头、§0、§4.2、§7、修订记录 | 回填第七轮 Review #6084094037 的固定 Head/Base 与 APPROVE_FOR_READY；SR-028 提升 READY，建立实施 Issue #96；将两个非阻断 P2 纳入实施证据要求并固定 §8.2 候选设计基线 | 允许在不合并 PR #46 的前提下启动范围受限实施，同时保持 AC-028-01～10 产品执行 NOT_RUN | Issue #12；Issue #96；PR #46；Review #6084094037；G02 v0.2.8 |