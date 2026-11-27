# SR-028：Python 工程工具链与 uv 环境管理

> 文档类型：软件需求（SR）  
> SR 版本：0.2.5\
> 修订日期：2026-11-27\
> 状态：DRAFT（实施主状态）；独立模型 Review #6082541121（固定 Head 3d5f17b7；Base 3c7c4838）：APPROVE_FOR_READY（仅 G02 设计；uv 与双平台迁移 AC 未运行）；当前后续 Head 待独立复评，READY=0。
> 创建日期：2026-11-26  
> 所属阶段：G02 工程治理支撑  
> 上游需求：[IR-007](../IR/IR%20总登记册.md#ir-007)  
> 设计依据：[G02 Python 工程工具链与环境管理设计说明书](../设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md) v0.2.3 §1～§8；[SR-002](SR-002-Python%20核心与宿主基础骨架.md) v0.2.10 §2.1；[SR 管理规范](../规范/SR%20管理规范.md) v0.7.0\
> 设计/治理 Issue：[ca-agent-next #35](https://github.com/odango-chan/ca-agent-next/issues/35)（不是实施 Issue）  
> 目标仓：`odango-chan/ca-agent-next`  
> 历史复核输入：PR #46 @ `c3bf36a75199901a06479d52534747224ae6db46`（非当前 Head）；第三轮评审读取 PR #46 完整当前提交，后续实施 Goal 另行固定最终获批设计 SHA。
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：其他仓库迁移、生产级供应链安全、运行时架构改造和完整 Python 版本矩阵资格认证

## 0. 本轮设计评审入口（2026-11-26）

本 SR 已依据 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 与 [Issue #35](https://github.com/odango-chan/ca-agent-next/issues/35) 提交独立设计评审。**SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 不等于实施 READY、独立 APPROVED 或 uv 实测 PASS。**

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
4. 生成并提交 `uv.lock`；添加纯文本 `.python-version`（内容仅为 `3.14.6`），并向 `.gitignore` 追加独立行 `.venv/`，保留既有规则。
5. 统一本地和 CI 的安装、测试、Smoke、脚本执行命令为 `uv sync --locked` / `uv run --locked`。
6. 在独立 worktree 中验证每个 checkout 使用自己的 `.venv/`，不共享 site-packages 或 editable distribution metadata。
7. 从含 SR-001/SR-003 的目标分支迁移现有工作流的 Python 安装入口，保留 G02 §3.8 的双平台回归；在真实 PR Workflow 中运行完整单元测试和上下文生成器。
8. 更新 README/Agent 协作入口和受影响命令文档，记录实际 uv/Python 版本、命令、环境和测试证据。

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

- G02 v0.2.0 与 SR-002 v0.2.10 的 Python distribution/build metadata 是稳定输入。
- 设计评审不依赖 SR-001 的代码合并；可以独立评审 uv 与 worktree 方案。

### 4.2 实施依赖

- AC-028-01～AC-028-06：SR-028 达到 READY、独立实施 Issue 建立后即可执行，不依赖 Agent Runtime 产品阶段。
- AC-028-07（CI 环境与测试入口）和 AC-028-08（SR-001 Workflow/Artifact 迁移）：所需 SR-001 Workflow 与脚本已随 PR #32 合入。独立实施 PR 核对目标分支仍含这些入口及 SR-003 回归工作流后，按 G02 §3.8 迁移与复验。既有成功结果不计为迁移 PASS。
- SR-028 当前没有实施 Issue。Issue #35 只负责中央设计和治理文档，不授予代码、配置或 Workflow 写入授权。

## 5. Acceptance

| ID | 验收条件 | 必需证据 |
|---|---|---|
| AC-028-01 | 根 pyproject 保留 `ca-agent-next`、版本 `0.1.0`、`requires-python >=3.11`、setuptools build backend、src package discovery 和空运行时依赖；保留 SR-003 的 plugins extra，仅增加 uv 与开发依赖配置 | pyproject diff；distribution metadata 检查；确认 PyYAML 不在 Requires-Dist runtime metadata |
| AC-028-02 | `.python-version` 文件内容精确为 `3.14.6`；uv CLI 固定为 0.13.10；setup-uv 使用 v10.4.0 不可变 commit `1db35dd8eee11c5894872e0b383ae6c406cf738d` 并显式设置 version | 文件内容、`uv --version`、`python --version`、Workflow 日志和配置 |
| AC-028-03 | PyYAML 位于 `[dependency-groups].dev`，不进入 Agent Core 运行时依赖 | pyproject/uv.lock；distribution metadata 测试 |
| AC-028-04 | `uv.lock` 已提交且与 pyproject 一致；锁文件漂移时 `uv lock --check` / `uv sync --locked` 必须失败，不自动改写锁文件 | clean checkout 的 locked sync 与负例 |
| AC-028-05 | 每个 worktree 使用独立 `.venv/`；`.venv/` 被 Git 忽略（`git check-ignore .venv/pyvenv.cfg` 成功）；`uv sync` 将当前 checkout 项目安装到该环境；两个并行 worktree 的 editable metadata 和测试互不污染 | 两个 worktree 的 `.venv` 路径、ignore 结果、distribution metadata 和测试输出 |
| AC-028-06 | 当前基线可用的完整 unittest 与 Host Smoke 使用 `uv run --locked --group dev --extra plugins` 通过，记录 Host、Plugin、Review Context 的发现数及失败/跳过数；生成器、Summary 及三文件 Artifact 由 AC-028-08 在真实 PR 验收 | 命令、CPython 3.14.6、完整测试结果和 Smoke 输出 |
| AC-028-07 | GitHub Actions 使用 G02 §3.7 固定 setup-uv YAML、uv 0.13.10、`uv python install`；各矩阵令 PY 指向已安装的矩阵解释器（Windows 使用 PowerShell 对应变量）。依次执行 `uv sync --python "$PY" --locked --group dev --extra plugins`、`uv run --python "$PY" --locked --group dev --extra plugins python -m unittest discover -s tests -v`、`uv run --python "$PY" --locked --group dev --extra plugins python -m ca_agent_next --smoke`；G02 §3.8 的每一类变更均触发双平台完整回归，以仅修改 .github/workflows/review-context.yml 的真实 PR 为独立触发用例，核对同一次 synchronize 的 Ubuntu 3.12 和 Windows 3.14 两个非 skipped Job。保留 docs/SR/SR-003-* 与 Go Echo 构建，不执行 pip 临时安装 | Workflow diff、真实 PR Run 和 Job 日志；核对 action commit 与版本输入 |
| AC-028-08 | SR-001 Workflow 已集成后，将其迁移到 uv；真实 `pull_request` Run 中上下文生成器成功，Artifact 恰含三份预期文件 | SR-001 集成基线 SHA、真实 Run URL、Summary 和下载核对后的 Artifact 文件清单 |
| AC-028-09 | 不修改其他仓库、不改变运行时依赖和 setuptools backend、不引入额外签名/hash/Trust Registry 机制 | PR 文件清单、pyproject metadata、设计/实施边界审查 |

所有 AC 必须逐项记录受测 SHA、环境、命令、预期/实际结果和证据。未执行保持 NOT_RUN；依赖未满足的 AC 记录 BLOCKED，不得推导 PASS。

## 6. 交付门禁

- 设计评审通过后，先将 SR-028 更新为 READY，再创建独立实施 Issue。
- 实施分支从最新目标恢复分支基线创建，使用 `chore/issue-<编号>-sr-028-uv-python-toolchain`。
- pyproject.toml 与 uv.lock 必须在同一提交中更新；不得提交 `.venv/`。
- 每个实现批次 Commit + Push，并通过 GitHub API 核对远端分支 SHA。
- PR 必须关联实施 Issue、SR-028、G02 固定设计 SHA，并逐项回填 AC。
- 不得修改 main、合并 PR 或发布 Release，除非另有明确授权。

## 7. 当前状态与停止条件

SR-028 当前为 DRAFT。G02/SR-028 的设计 PR 尚待独立评审；不得创建实施 Issue、修改 `pyproject.toml`、生成 `uv.lock`、添加 `.python-version`、修改 Workflow 或向 DeepSeek Harness 发出实施提示词。

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
