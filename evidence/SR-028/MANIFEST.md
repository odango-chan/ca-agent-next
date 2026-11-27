# SR-028 实施验收证据归档（Issue #96）

- 仓库：`odango-chan/ca-agent-next`
- 需求：SR-028 Python 工程工具链与 uv 环境管理（v0.2.9）；设计：G02 v0.2.7
- 实施 Issue：[#96](https://github.com/odango-chan/ca-agent-next/issues/96)
- 实施 PR：[#99](https://github.com/odango-chan/ca-agent-next/pull/99)（base `docs/issue-12-draft-design-review-20261126` @ `93f1389e7c5968cd30e8a74137207094864ecca0`）
- **固定实施快照**：`83d23e8c04b1c05eb304c2a24a3392f6459ed0f1`
- 归档时间：2026-11-27（Asia/Shanghai）
- 证据来源：本机实施验收运行的真实 JSON / 日志 / 退出码 / diff / CI Artifact 解包内容

## 1. 归档统计

- 文件数：**268**
- 未压缩大小：**952,974 bytes**（约 0.91 MB）
- 压缩包：`sr028-evidence.zip`（见 Issue #96 归档评论中的下载入口）
- 校验：压缩包 SHA-256 与每个文件的 SHA-256 见本文件末尾「完整文件清单」与 Issue 评论

## 2. 脱敏说明

- 扫描范围：全部归档文件；扫描项包括 `ghp_`/`gho_`/`github_pat_`/`Authorization`/`password`/`secret`/`cookie`/`token=`/`api_key`/`Bearer`/私钥头。**全部 0 命中**，未发现 Token、密码、Cookie 或认证信息。
- 唯一需要脱敏的是本机 Windows 用户目录名：将该目录名一致替换为 `<local-user>`（涉及 23 个文件、共 52 处，含 2 个 UTF-16LE 日志）。替换同时作用于绝对路径、`sys_prefix`、`executable`、`module`、`direct_url`、`direct_url_source` 字段。
- 替换规则对所有文件与 A/B/A 三侧完全一致，因此 **A-before 与 A-return 的逐字相等关系、A 与 B 的全字段互异关系不受破坏**；`direct_url.json` 的 `file:///.../<local-user>/...` 对照仍可核验。
- 未脱敏原件保留在本地归档目录（不上传）；如需核对原始路径，可在本地环境按同目录脚本复跑。

## 3. 排除项

- `tmp/`：Go 构建临时目录 / 缓存（`GOTMPDIR`），非验收证据。
- `inventory.txt`：本次归档清点的临时清单。
- 不包含 `.git`、`.venv`、`__pycache__` 或其他缓存。
- CI Artifact 的原始 ZIP 未重复打包，避免与 GitHub Run Artifact 重复；本归档包含其解包后的完整文件内容与 Run 元数据 JSON。

## 4. 复现命令与退出码

### AC-028-01～03（元数据 / uv / 依赖分组）

```bash
uv run --no-sync --locked --group dev --extra plugins \
  python sr028-evidence/scripts/ac028-01-03-evidence.py <evidence_dir>   # exit 0
uv lock --check                                                          # exit 0
```

证据：`ac-028-01-03/ac-028-01-03.json`（distribution/版本/Requires-Python/Requires-Dist/plugins extra/dev group/uv required-version/.python-version blob/workflow uv pin）、`pyproject.diff`、`uv-lock-check.log`。

### AC-028-04（锁漂移 fail-closed）

```bash
bash sr028-evidence/scripts/ac028-04-lock-drift.sh   # 整块 exit 0
```

| 检查项 | 退出码 |
|---|---|
| `uv sync --locked --group dev --extra plugins`（正例） | 0 |
| `uv lock --check`（正例） | 0 |
| `uv lock --check`（负例，pyproject 临时 `<7`→`<8`） | 1 |
| `uv sync --locked --group dev --extra plugins`（负例） | 1 |

两条负例日志均匹配 `lockfile ... needs to be updated`；每次负例后 `git diff --exit-code HEAD -- uv.lock` 与 `git status --porcelain -- uv.lock` 均通过；恢复后 `pyproject.toml`/`uv.lock` clean。证据：`ac-028-04/`。

### AC-028-05（A→B→A worktree 隔离）

```bash
bash sr028-evidence/scripts/ac028-05-worktree-isolation.sh   # 整块 exit 0
```

| 阶段 | Host gate 退出码 | 结果 |
|---|---|---|
| A-before | 0 | 52/52 |
| B | 0 | 52/52 |
| A-return（仅 `--no-sync --locked`） | 0 | 52/52 |

证据：`ac-028-05/{a-before,b,a-return}.json`、三份原始 `direct_url.json`、三份 `git check-ignore -v` 输出、三组 Host gate JSON/log/exit-code；脚本断言 A/B 七字段互异、A-return 与 A-before 逐字一致。

### AC-028-06（Go 前置 + 本地门禁 + Smoke）

```bash
go version                                        # go1.26.6 windows/amd64，满足 go.mod 的 go 1.24
GOWORK=off go env GOWORK                          # off
go env GOOS                                       # windows
# examples/echo/plugin 下：
GOWORK=off go build -trimpath -o bin/echo-plugin.exe .   # exit 0
uv run --no-sync --locked --group dev --extra plugins \
  python scripts/unittest_gate.py --output-dir <dir>     # exit 0
uv run --no-sync --locked --group dev --extra plugins \
  python -m ca_agent_next --smoke                        # exit 0，stderr 0 字节
```

四范围 gate：host 52/52、plugin 87/87、review-context 80/80、total 219/219；failures=errors=skipped=expected_failures=unexpected_successes=loader_errors=0；`discovery_exception=null`；整体 exit 0。证据：`ac-028-06/`，最终快照回归 `final-regression/`（tested-sha `83d23e8`）。

### AC-028-07 / AC-028-08（真实 GitHub Run）

| 用途 | Run | Head SHA | 结果 |
|---|---|---|---|
| 主 PR opened：SR-003 | [45953338978](https://github.com/odango-chan/ca-agent-next/actions/runs/45953338978) | `0c333f3` | ubuntu 3.12 + windows 3.14.6 success |
| 主 PR opened：Review Context | [45953339038](https://github.com/odango-chan/ca-agent-next/actions/runs/45953339038) | `0c333f3` | success，两个分离 Artifact |
| 主 PR synchronize：SR-003 | [45955482682](https://github.com/odango-chan/ca-agent-next/actions/runs/45955482682) | `83d23e8` | ubuntu 3.12 + windows 3.14.6 success，gate 219/219 |
| 主 PR synchronize：Review Context | [45955482683](https://github.com/odango-chan/ca-agent-next/actions/runs/45955482683) | `83d23e8` | success，正式 Artifact 恰三文件 |
| 堆叠 PR synchronize：Review Context | [45956150601](https://github.com/odango-chan/ca-agent-next/actions/runs/45956150601) | `fa6d7be` | success |
| 堆叠 PR synchronize：SR-003 | [45956150500](https://github.com/odango-chan/ca-agent-next/actions/runs/45956150500) | `fa6d7be` | 两个矩阵 Job success（非 skipped） |
| 受控负例：Review Context | [45956888727](https://github.com/odango-chan/ca-agent-next/actions/runs/45956888727) | `4fccd38` | failure（预期）：gate PASS 80/80、生成器 exit 3、stderr 含 `base 提交对象不可读取`、manifest 三文件 MISSING、无正式 Artifact |
| 受控负例：SR-003 | [45956888769](https://github.com/odango-chan/ca-agent-next/actions/runs/45956888769) | `4fccd38` | success |
| 恢复：Review Context | [45957598111](https://github.com/odango-chan/ca-agent-next/actions/runs/45957598111) | `069c59d` | success，`failure_injection=none`，两 Artifact |
| 恢复：SR-003 | [45957598133](https://github.com/odango-chan/ca-agent-next/actions/runs/45957598133) | `069c59d` | success |

证据：`ci-main-pr/`、`ci-main-pr-final/`、`stacked-verify/`（含 Run JSON、Artifact 解包内容、负例 `run-context.txt` 与 PR 文件清单 `pr100-negative-view.json`）。

## 5. AC 与证据映射

| AC | 证据目录/文件 | 关键判定 |
|---|---|---|
| AC-028-01 | `ac-028-01-03/ac-028-01-03.json`、`pyproject.diff` | distribution/版本/`>=3.11`/build backend/src discovery/空运行时依赖保留；plugins extra 保留 |
| AC-028-02 | `ac-028-01-03/ac-028-01-03.json`（`uv_version`、`python_version`、`python_version_file`、`workflow_uv`）、`uv-lock-check.log` | `.python-version` blob=`3.14.6\n`；uv=`0.13.10`；setup-uv commit+version 固定 |
| AC-028-03 | `ac-028-01-03/ac-028-01-03.json`（`checks.requires_dist`、`dev_group`） | PyYAML 仅在 `[dependency-groups].dev`，不在 `Requires-Dist` |
| AC-028-04 | `ac-028-04/*` | 正例 exit 0；两负例 exit 1 + 诊断匹配；`uv.lock` 未变；恢复 clean；整块 exit 0 |
| AC-028-05 | `ac-028-05/*` | 独立 `.venv`、七字段互异、A-before=A-return、`--no-sync`、三份 direct_url 与 ignore 输出、三次 Host gate 52/52 |
| AC-028-06 | `ac-028-06/*`、`final-regression/*` | Go directive 1.24 / 实机 go1.26.6 / GOWORK=off / `.exe` 构建 / CWD 恢复 / 四范围 gate 219 / Smoke |
| AC-028-07 | `ci-main-pr-final/*`、`stacked-verify/sync-*` | 双平台矩阵 Python 3.12 / 3.14.6、四范围 gate、同一 synchronize Head SHA 两个 Workflow |
| AC-028-08 | `ci-main-pr-final/review-context-*`、`stacked-verify/negative-*`、`stacked-verify/recovery-*` | 成功/负例/恢复三路径；诊断与正式 Artifact 分离；manifest MISSING/PRESENT |
| AC-028-09 | 全部 diff 文件与 `pr100-negative-view.json` | 无运行时/API 变更，无第二套依赖机制，未改 main/设计分支/治理分支 |
| AC-028-10 | `pr99-body-final.md`、`pr-body.md`、`issue-checkpoint-*.md` | README/Agent/SR-002/SR-003/演示基线/G02/SR-028 当前入口刷新，历史证据保留 |

## 6. 尚缺失 / 已知边界

1. paths 枚举中除 `.github/workflows/review-context.yml` 外的单文件触发未逐一构造 PR；由主 PR 累积 diff 与堆叠 PR 单文件触发实证覆盖，枚举本身完整。
2. AC-028-04/05 的 fail-closed Bash 块整体 stdout/stderr 未单独落盘（设计块只在失败时输出子日志）；子步骤日志、退出码、diff 与断言结果完整保留，块整体 exit 0 即全部断言通过。
3. CI Artifact 原始 ZIP 未重复打包；GitHub Run Artifact 在保留期（30 天）内可直接下载，本归档保存其解包内容与 Run 元数据。
4. AC-028-04/05 实际受测提交为 `0c333f3`（见各目录 `tested-sha.txt` / `provenance.txt`）；`83d23e8` 仅在其后追加 AC-028-10 文档刷新，不改变工具链与门禁行为。
5. 无 macOS 证据（不在本 AC 范围）。

## 7. 独立复核入口

1. 从 Issue #96 归档评论下载 `sr028-evidence.zip` 并解压。
2. 按本 MANIFEST 的 AC 映射逐项核对原始 JSON/log/exit-code；用末尾 SHA-256 清单校验文件完整性。
3. 对照 GitHub Run URL 核对 CI 结论与 Artifact 内容。
4. 如需复跑：使用 `scripts/` 下两个 Bash 块与一个 Python 采集脚本（复跑会生成新的证据目录，不改写本归档）。

## 8. 完整文件清单（含 SHA-256）

> 下表为归档内全部 268 个文件（不含本 `MANIFEST.md` 自身）。解压后可用任意 SHA-256 工具逐文件核对。

| # | 相对路径 | 大小(byte) | SHA-256 |
|---|---|---|---|
| 1 | `ac-028-01-03/ac-028-01-03.json` | 1731 | `a9ca6bba4757717a07e88507ec5980b296757100674d6aab1e1443964d913efb` |
| 2 | `ac-028-01-03/pyproject.diff` | 1554 | `91b95fa06197880fff9b64977a783a1acbf2fa2e257913756d7e14556297e120` |
| 3 | `ac-028-01-03/stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 4 | `ac-028-01-03/stdout.log` | 3464 | `2c5d129701cf60f79c4f9488354668e22faab97c68b3821cef4f2b0bb6924b22` |
| 5 | `ac-028-01-03/uv-lock-check.log` | 732 | `87d858a5b2ec07e7c035676dbb8c971efc035cbcd4d8d3fbe9cee8223cb26784` |
| 6 | `ac-028-04/negative-lock-check.exit-code` | 2 | `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865` |
| 7 | `ac-028-04/negative-lock-check.log` | 224 | `a51e4b8093bcfa8feb0b053fbd11d17cc015ca10ac0c4cfa66789e65b12be26a` |
| 8 | `ac-028-04/negative-sync-locked.exit-code` | 2 | `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865` |
| 9 | `ac-028-04/negative-sync-locked.log` | 224 | `79137e1aeab4fd8ad60bbb1ea4cc30b07c30b4a21c44c4099e8143ad31db0675` |
| 10 | `ac-028-04/positive-lock-check.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 11 | `ac-028-04/positive-lock-check.log` | 28 | `f7bdf44f74ace2d1d69b68eab9162745db8188cc605e1cbbfedc7a20d5456a78` |
| 12 | `ac-028-04/positive-sync.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 13 | `ac-028-04/positive-sync.log` | 762 | `003302431c6258c9356c0ae08490a64a9b9ac02572343341483aaa5f12fe484f` |
| 14 | `ac-028-04/provenance.txt` | 479 | `dfc268212ace1456c595e40ac25b7d66185038da34e4c41d9350aab16f18df35` |
| 15 | `ac-028-04/pyproject-drift.diff` | 241 | `d3f556cd57ea965125523ca70dba8fe049d90faf4c7bf025600b4ec7edd7113d` |
| 16 | `ac-028-04/tested-sha.txt` | 42 | `8be7476714edbfe9ccbe9bd4a43cc15117b1a30a986e14fed5bac57ec5242ae8` |
| 17 | `ac-028-05/a-before-host-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 18 | `ac-028-05/a-before-host-gate/host.log` | 6581 | `f4c74449fa4facd63246508ed71cfb255a224f2622065384003d867d53b6d545` |
| 19 | `ac-028-05/a-before-host-gate/summary.json` | 805 | `c1e0b85dde4d48df052416906171f029c6a3acfd11861e1af2b37a0591dc3e15` |
| 20 | `ac-028-05/a-before-host-gate.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 21 | `ac-028-05/a-before-host-gate.stdout.log` | 192 | `220dc699bb91b83d239aa8f96ed7e18b99ac4b46f156c866126d9eb4f34d8f24` |
| 22 | `ac-028-05/a-before.direct_url.json` | 145 | `fee8a63a1aeb9b39c36eb68a1aebca3a986673ab98e447e82e7698bd5c4bedfa` |
| 23 | `ac-028-05/a-before.git-check-ignore.txt` | 37 | `b244f7db2263fe70d37e408d6f3f6e4bc53b855405d27e6a39c74e865dff5267` |
| 24 | `ac-028-05/a-before.json` | 967 | `009d942c23f6734e96dc9fa8909471672fc6b4b916a2735adc0c95cd49d37173` |
| 25 | `ac-028-05/a-return-host-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 26 | `ac-028-05/a-return-host-gate/host.log` | 6581 | `f4c74449fa4facd63246508ed71cfb255a224f2622065384003d867d53b6d545` |
| 27 | `ac-028-05/a-return-host-gate/summary.json` | 805 | `854c2526f69086f6500683edc77099d301cbea893a12133b969f152f5d546c2e` |
| 28 | `ac-028-05/a-return-host-gate.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 29 | `ac-028-05/a-return-host-gate.stdout.log` | 192 | `220dc699bb91b83d239aa8f96ed7e18b99ac4b46f156c866126d9eb4f34d8f24` |
| 30 | `ac-028-05/a-return.direct_url.json` | 145 | `fee8a63a1aeb9b39c36eb68a1aebca3a986673ab98e447e82e7698bd5c4bedfa` |
| 31 | `ac-028-05/a-return.git-check-ignore.txt` | 37 | `b244f7db2263fe70d37e408d6f3f6e4bc53b855405d27e6a39c74e865dff5267` |
| 32 | `ac-028-05/a-return.json` | 967 | `009d942c23f6734e96dc9fa8909471672fc6b4b916a2735adc0c95cd49d37173` |
| 33 | `ac-028-05/b-host-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 34 | `ac-028-05/b-host-gate/host.log` | 6581 | `9b19b3f81015c36f6dbf33c714486574663386edc43adc39f8dd55e255f421ab` |
| 35 | `ac-028-05/b-host-gate/summary.json` | 805 | `4593476c37e81062a67012688e3dd3dbf1bf75bb7ef7001405b0ce4960e6d9e7` |
| 36 | `ac-028-05/b-host-gate.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 37 | `ac-028-05/b-host-gate.stdout.log` | 192 | `220dc699bb91b83d239aa8f96ed7e18b99ac4b46f156c866126d9eb4f34d8f24` |
| 38 | `ac-028-05/b.direct_url.json` | 145 | `e5eba1020bf2301dc153599fe016cf192d678aeb7fca3d6a9c7f31fb82294355` |
| 39 | `ac-028-05/b.git-check-ignore.txt` | 37 | `b244f7db2263fe70d37e408d6f3f6e4bc53b855405d27e6a39c74e865dff5267` |
| 40 | `ac-028-05/b.json` | 967 | `46b23aafaddc915e6a23668e2458a8e1d1fb3af5bfb0338a0d0fc25604355b4f` |
| 41 | `ac-028-05/provenance.txt` | 479 | `dfc268212ace1456c595e40ac25b7d66185038da34e4c41d9350aab16f18df35` |
| 42 | `ac-028-05/tested-sha.txt` | 42 | `8be7476714edbfe9ccbe9bd4a43cc15117b1a30a986e14fed5bac57ec5242ae8` |
| 43 | `ac-028-06/cwd-after.txt` | 65 | `a2fd38b74d52e4f7818581ef3a45121b53678efd05dc81c9e82e8c023c569af7` |
| 44 | `ac-028-06/cwd-before.txt` | 65 | `a2fd38b74d52e4f7818581ef3a45121b53678efd05dc81c9e82e8c023c569af7` |
| 45 | `ac-028-06/environment.txt` | 276 | `bfdb5afbfe04eaaeaf2d284332eb1c9eecb65520d744fb6b0cebf9de51be5878` |
| 46 | `ac-028-06/go-binary.txt` | 147 | `ce00479146ecb8624bc5920fbc7b00f56ce17e14d6cf81e9c8ab1522d0e8791c` |
| 47 | `ac-028-06/go-build.exit-code` | 3 | `13bf7b3039c63bf5a50491fa3cfd8eb4e699d1ba1436315aef9cbe5711530354` |
| 48 | `ac-028-06/go-env-goos.txt` | 12 | `c1bcc6dac2c0b2faea326af136c742e8783beef20a525710f5daed05d7ab7d05` |
| 49 | `ac-028-06/go-env-gowork.txt` | 8 | `06769d658e160cb481a506fbc3c2821720a6c921af95a875973f46e95246a951` |
| 50 | `ac-028-06/go-version.txt` | 72 | `81325324c116a61d6bdc2f661ac5d38a4abee44c67bc196967ede76deef5692a` |
| 51 | `ac-028-06/smoke.exit-code` | 3 | `13bf7b3039c63bf5a50491fa3cfd8eb4e699d1ba1436315aef9cbe5711530354` |
| 52 | `ac-028-06/smoke.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 53 | `ac-028-06/smoke.stdout.log` | 296 | `981042be8f09412b3dba0ccf8676215cba7ed66abe4f22fff6e7a56460ea468f` |
| 54 | `ac-028-06/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 55 | `ac-028-06/unittest-gate/host.log` | 6581 | `7afffc3b6a3ef9215d5fde3ebfebab7baa78d50ab76e6046baaec337f656c82a` |
| 56 | `ac-028-06/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 57 | `ac-028-06/unittest-gate/plugin.log` | 11839 | `cb582c048c85318ce5ed5ad4692789a13c3a610bb2cc5bb5046c9d7f021e016a` |
| 58 | `ac-028-06/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 59 | `ac-028-06/unittest-gate/review-context.log` | 9859 | `5b087199a385aefcb3ee864611804f55a6507272d953760046d763eac8ea3458` |
| 60 | `ac-028-06/unittest-gate/summary.json` | 1858 | `924452cadef7f391a3a2b384e9c23458164687089bd6233520f8d8b1f45a7a27` |
| 61 | `ac-028-06/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 62 | `ac-028-06/unittest-gate/total.log` | 28072 | `5dc446b6a603921584c47124c359ef803f32a3bc8c19379537415ffecdc3310b` |
| 63 | `ac-028-06/unittest-gate.exit-code` | 3 | `13bf7b3039c63bf5a50491fa3cfd8eb4e699d1ba1436315aef9cbe5711530354` |
| 64 | `ac-028-06/unittest-gate.stdout.log` | 1444 | `56ff9937d0870c504ea91ba0e18b83c1f43dff0377b95a89f08101f815364d25` |
| 65 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/generator-output-manifest.txt` | 101 | `0647784ebb126054d260b354bff3c17ce37012d48bf05449bad417b6c3790681` |
| 66 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/generator.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 67 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/generator.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 68 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/generator.stdout.log` | 358 | `5bb4fa5467310833d8763977c4f684e7204c3542409f7af0c1a1a6e3e4a8a154` |
| 69 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/python-version.txt` | 14 | `917601090ffb73a030e3eaa8b7a01c41400cad4b61366b4218d7756a5733b66c` |
| 70 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/run-context.txt` | 229 | `9fb5b36a76ab8d8026b3d87ac64913e43c33db7c2c4b35b493eef8e850e72877` |
| 71 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 72 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/unittest-gate/review-context.log` | 9773 | `e6deea1db08ee5a18c7996135d1b3aa20bf79a4a25bb6183f414f47410775492` |
| 73 | `ci-main-pr/review-context-artifacts/review-context-diagnostics-pr-99-45953339038-1/unittest-gate/summary.json` | 681 | `6c1b593d843f0148dd2fa9bfb9622e4d4a75a1852a39ae1ab56c5e664fe37e5a` |
| 74 | `ci-main-pr/review-context-artifacts/review-context-pr-99-45953339038-1/review-scope.json` | 5536 | `b5f33929f0ee059dfb5febe42e1b7785f0207eef5a170774566c3d6b2310794b` |
| 75 | `ci-main-pr/review-context-artifacts/review-context-pr-99-45953339038-1/统一评审提示词.md` | 8804 | `5893bfdd4f472dd3402a8219c6abc0c1f5c02ef91d84be9b3d26f33db8658571` |
| 76 | `ci-main-pr/review-context-artifacts/review-context-pr-99-45953339038-1/评审上下文.md` | 6573 | `959852a629e8603bf5a420732169dd8616b18e2d566a4eb8bf8cfc6a918083ae` |
| 77 | `ci-main-pr/review-context-run.json` | 5958 | `6286d801b3f547943d01bbd931804b80bb137bb8b6d32e61ef338e215f9d36e1` |
| 78 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/go-version.txt` | 33 | `07b0d66d21bcdfdc8456adcb17203f3af8656dc11549da62e6940f99b8d45444` |
| 79 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/python-version.txt` | 15 | `9d0ae83e540febd225949f3df4aba97c7a9f79fcf745d6c835780f52a57b50cf` |
| 80 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/run-context.txt` | 194 | `694a2d5e85becf352c3aa5ad997200b470fab88c1b3a9a0ab30d4586a27f5a37` |
| 81 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/smoke.stdout.log` | 146 | `367856635f4a784156f2c15ffbb60833b04b4fd7bf7a052ae73caab6bb6f7c99` |
| 82 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/sr003-evidence.json` | 2860 | `d2c6e944259f8137f6bf41cdba6e5bfef2f6e7fec849bb4536e74483da50c91b` |
| 83 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.json` | 311 | `930a92ab2eb0b9e9c3ed89675f30eddabbd8a8a89fcc15a57a6309594540e7cf` |
| 84 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.log` | 6524 | `a37ee759e936e20dbf39d117ec3f7bf515634ae9f48629ac22a9261e1106ce08` |
| 85 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.json` | 315 | `43b4456907a2416dcf4df7b1fc7459dfb66df08aa7c26e4657b82e6fb95c0723` |
| 86 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.log` | 11745 | `dd8288553aa6ac83c5603d941d45a8e7c3a898a54e39d918f7beb1db6c58105c` |
| 87 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 88 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.log` | 9773 | `a3b1eb194e0aef5e7f943dec38104a011b8c15e7fb2b6a07ed509cafe45e0ff3` |
| 89 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/summary.json` | 1736 | `ca846cc669916d7ad8eec698a52dbb2e4f403900370a30ea28ba5e3f2501c871` |
| 90 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.json` | 311 | `d52943005748b33b7b6ccea6abf54bf3ba831069075be63c7c681a33ce318b39` |
| 91 | `ci-main-pr/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.log` | 27845 | `243d3f9017106de422a1d24f872340ac5b4d6b783bdbf5d152d0efcb296506f7` |
| 92 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/go-version.txt` | 35 | `69889abdfc6e43c76e2f8f74c354996d6552bed712e97f5774fb2253d7db135f` |
| 93 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/python-version.txt` | 15 | `2b095b05c4093ebca54b87bd2c6a6f557935e6b3f8f506a0c2e5e294a763f4ad` |
| 94 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/run-context.txt` | 198 | `956fccaee472cb80f98c7989db4367aa675507b9737fc2036d4c7e81853a5cfc` |
| 95 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/smoke.stdout.log` | 147 | `d231fa7c7098b2ac036acf0a064984111ac894af85b6f3103bac79ee13363cba` |
| 96 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/sr003-evidence.json` | 2993 | `e51d81c8407479ad13b924038c9a24ddce497d7ab14135a76b96276850c4d59f` |
| 97 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 98 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.log` | 6581 | `74ccbf6c02a45a908bb651a4bd42f657979c183f4336f109f769c3c1437f9359` |
| 99 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 100 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.log` | 11839 | `d3c32ed8c001d8c2ffa369ca91487f13f2e8a05cc8e2dafeb33efcdc4fc10fb7` |
| 101 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 102 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.log` | 9859 | `135cd438b2bf0f41ef6a665fd46d5f093470ae9254898f0ab5f8454d9aae86de` |
| 103 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/summary.json` | 1796 | `1fcdb0d62006a5315621d2ff1c1f42827d04d820532fb5c87ecc47396dbf3e66` |
| 104 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 105 | `ci-main-pr/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.log` | 28072 | `368b914083e48ccbe414e3fa2d0ce12bc546d96909cce1a33ac49f03b5be28a3` |
| 106 | `ci-main-pr/sr003-run.json` | 10772 | `4c29781a99ea63ed6664147ccf2106bf8a0e69a3222e09c3732a74ded5bdc5f5` |
| 107 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/generator-output-manifest.txt` | 101 | `3dabe837567563605a21856a73378653b46c7cf345427d8119f18a05ccde84f2` |
| 108 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/generator.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 109 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/generator.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 110 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/generator.stdout.log` | 359 | `cf99e106c61b6b03e5ca852349a72d6cc3ddaa4898fdb8f7a2b43278485051df` |
| 111 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/python-version.txt` | 14 | `917601090ffb73a030e3eaa8b7a01c41400cad4b61366b4218d7756a5733b66c` |
| 112 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/run-context.txt` | 229 | `c2029cc1b5877dd54e7286e6876c5f3fb83144196a786290205e0796c29fb474` |
| 113 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 114 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/unittest-gate/review-context.log` | 9773 | `aa922578fbe1635656183e21cadee87b47f51250d8f1849248aa7d4a18c7ba8e` |
| 115 | `ci-main-pr-final/review-context-artifacts/review-context-diagnostics-pr-99-45955482683-1/unittest-gate/summary.json` | 681 | `dd342a8546c6201a25a6004e596e15ec89e2e4b94559d45b07c00733e13e77df` |
| 116 | `ci-main-pr-final/review-context-artifacts/review-context-pr-99-45955482683-1/review-scope.json` | 5536 | `b5f33929f0ee059dfb5febe42e1b7785f0207eef5a170774566c3d6b2310794b` |
| 117 | `ci-main-pr-final/review-context-artifacts/review-context-pr-99-45955482683-1/统一评审提示词.md` | 9211 | `8f22407c9aa1a62d62707f9164dac3faf01d8bc6b87e98c09254a0b648f6bbd6` |
| 118 | `ci-main-pr-final/review-context-artifacts/review-context-pr-99-45955482683-1/评审上下文.md` | 6980 | `0e82fe0543f006f4acbb321dac51240ee83116994639dbb2dd5f840852663717` |
| 119 | `ci-main-pr-final/review-context-run.json` | 5854 | `1d32b28fc1a1d67059e4dd39d50ea9c55a0497597d0ed9a1cd79e8ea6d2a6048` |
| 120 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/go-version.txt` | 33 | `07b0d66d21bcdfdc8456adcb17203f3af8656dc11549da62e6940f99b8d45444` |
| 121 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/python-version.txt` | 15 | `9d0ae83e540febd225949f3df4aba97c7a9f79fcf745d6c835780f52a57b50cf` |
| 122 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/run-context.txt` | 194 | `be6742a1df4ffb51506eb7034314301ea69a54abeb6caab56c48c62d7d45690a` |
| 123 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/smoke.stdout.log` | 146 | `367856635f4a784156f2c15ffbb60833b04b4fd7bf7a052ae73caab6bb6f7c99` |
| 124 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/sr003-evidence.json` | 2860 | `a0656c5cb45efc6194bb31351df4f74361e0642c876d481feaaef3081ca08b3f` |
| 125 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.json` | 311 | `930a92ab2eb0b9e9c3ed89675f30eddabbd8a8a89fcc15a57a6309594540e7cf` |
| 126 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.log` | 6524 | `eb1890c01d687f1396ce3f614de3b9ad962af58447cfc3a816ecf552f6a57cdb` |
| 127 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.json` | 315 | `43b4456907a2416dcf4df7b1fc7459dfb66df08aa7c26e4657b82e6fb95c0723` |
| 128 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.log` | 11745 | `19c8bee84c9c8e633dc5af774fb89db6449818ac9f2db47809c168604460f036` |
| 129 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 130 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.log` | 9773 | `5c39c7425f87a74e241e69d5d1441a737ba281988477a4ca791bf69b9d7f6b08` |
| 131 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/summary.json` | 1736 | `1eb9c9ac67490ab3405dac0df812e5db210535fbdd6cb432eca3e0b5ae1cae76` |
| 132 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.json` | 311 | `d52943005748b33b7b6ccea6abf54bf3ba831069075be63c7c681a33ce318b39` |
| 133 | `ci-main-pr-final/sr003-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.log` | 27845 | `107086405aee8c5ee95a28a3f8dfa13367e9b3676167981e96ad61d9c422e1cc` |
| 134 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/go-version.txt` | 35 | `69889abdfc6e43c76e2f8f74c354996d6552bed712e97f5774fb2253d7db135f` |
| 135 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/python-version.txt` | 15 | `2b095b05c4093ebca54b87bd2c6a6f557935e6b3f8f506a0c2e5e294a763f4ad` |
| 136 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/run-context.txt` | 198 | `9b9df277a7382f759a984beed3ca21d4ee7a40068b792022f39550d53cae4d3b` |
| 137 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/smoke.stdout.log` | 147 | `d231fa7c7098b2ac036acf0a064984111ac894af85b6f3103bac79ee13363cba` |
| 138 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/sr003-evidence.json` | 2993 | `94128eb6a7524c68b3aaf46beb6cbc8469788f0a4735a1d7f388dcf60c3d7616` |
| 139 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 140 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.log` | 6581 | `32e7db439729cd45bc6f0646f316d22df82b2bb6ef0044102940ae90b01dff34` |
| 141 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 142 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.log` | 11839 | `4ed37d321ead24e6d4bbe5200e4eef0ffe6c9c98db91934d6078f1030ab8010f` |
| 143 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 144 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.log` | 9859 | `86b4e03a4fb72746898f3a7966a9bb2a94f51978b7de042bd5a5fdc45876e0b2` |
| 145 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/summary.json` | 1796 | `a0f163b95504f462d7c11ea530aa440241221ce4f578e3a2caf72bdcf5b0c78d` |
| 146 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 147 | `ci-main-pr-final/sr003-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.log` | 28071 | `d33fadc8afe9912fc09369651458fa7747213c80b1c1a64936aaa27b4be0e14e` |
| 148 | `ci-main-pr-final/sr003-run.json` | 10668 | `a193bd4a55dc508b7a0420640b42bd06bdaef9e13a8ae35a4157d9a1d6ea4aae` |
| 149 | `final-regression/gate.stdout.log` | 1444 | `56ff9937d0870c504ea91ba0e18b83c1f43dff0377b95a89f08101f815364d25` |
| 150 | `final-regression/git-status.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 151 | `final-regression/smoke.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 152 | `final-regression/smoke.stdout.log` | 296 | `981042be8f09412b3dba0ccf8676215cba7ed66abe4f22fff6e7a56460ea468f` |
| 153 | `final-regression/tested-sha.txt` | 42 | `28c04ae9b4afb07771f5e68dab503874067cad0ae7555b7dc840f0d22de7db58` |
| 154 | `final-regression/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 155 | `final-regression/unittest-gate/host.log` | 6581 | `c8192fd41cae8f105e2bf537ee8b849fec867c64dce021da7f62c4b991fddbf3` |
| 156 | `final-regression/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 157 | `final-regression/unittest-gate/plugin.log` | 11839 | `f9b6422db22929e16d8f9bbb5579f9e55519d9bf9b1d42fae81c873a6f985e60` |
| 158 | `final-regression/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 159 | `final-regression/unittest-gate/review-context.log` | 9859 | `1de142b208a41e3f77ea0d687a9e035bab32b098653edd338592bba9116186ec` |
| 160 | `final-regression/unittest-gate/summary.json` | 1858 | `fd7131c809b3759706dbf2d200aaf4c5c702a7ee144d8ba2d32eba4d01e5dd29` |
| 161 | `final-regression/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 162 | `final-regression/unittest-gate/total.log` | 28072 | `5c4cfcaa13cc7032cf3c64368d445b0aaac47cc480bc236eaaacd3144871877b` |
| 163 | `final-regression/uv-lock-check.log` | 716 | `77072a5a6795fe1335091e83a835d87464bbd8817b53dc5dca2e1b5fdcae60fe` |
| 164 | `issue-checkpoint-1.md` | 1931 | `dc4355d55e9bf773ead50066b5c67195040ab124524de9a69f9f69ec255179ea` |
| 165 | `issue-checkpoint-3.md` | 8044 | `55be379a14e80f07fc2a6c7b1f40b716585acf216ac25966c3b14d0f184a6c9b` |
| 166 | `local/review-context-preview/out/review-scope.json` | 5536 | `b5f33929f0ee059dfb5febe42e1b7785f0207eef5a170774566c3d6b2310794b` |
| 167 | `local/review-context-preview/out/统一评审提示词.md` | 9092 | `d8b4491af116211297affb5bc9d0de89618d48717eb18782e796e4c405278655` |
| 168 | `local/review-context-preview/out/评审上下文.md` | 6819 | `1920fe96befb55032c8ad9365b4411cf0d26d286c0989647bd9a3e2e824b1f56` |
| 169 | `local/review-context-preview/stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 170 | `local/review-context-preview/stdout.log` | 934 | `357086ac33fa0aaba4d57b807f540e19aae7fd9ab0fbee8e2f59e15382ccbc21` |
| 171 | `local/review-context-preview/summary.md` | 1533 | `68b2ec835019ab91df5fb7102598d0cc5cfd20dfa577f98c812ce707fca9a803` |
| 172 | `local/smoke.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 173 | `local/smoke.stdout.log` | 150 | `3b9a0bc6ec00d26eb1cd4e7b1e1fbdb0faebec58be79706a4bf69c59a6760731` |
| 174 | `local/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 175 | `local/unittest-gate/host.log` | 6581 | `e99d5f547810c3fb1867743a4996a39e6323d344234b576b0ba2f5e69720a7b2` |
| 176 | `local/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 177 | `local/unittest-gate/plugin.log` | 11839 | `7686dcf841173882d8b4600507e4788f15d57e5872fdc5266a71b6558e5d8db8` |
| 178 | `local/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 179 | `local/unittest-gate/review-context.log` | 9859 | `13dd03a8572e550f7a3f7b871c34454668264532e342f0cb8020157c89eacbf9` |
| 180 | `local/unittest-gate/summary.json` | 1858 | `10bd96fa79c87b1eb0bb504823c1124847370b8e3bf0b5cc270b029c63a88a38` |
| 181 | `local/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 182 | `local/unittest-gate/total.log` | 28072 | `463fd18b7b7d14a28861b9b9d7a8ba70130e2c694fc0a32c876f0ff04687f6e9` |
| 183 | `local/unittest-gate-after-docs/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 184 | `local/unittest-gate-after-docs/host.log` | 6581 | `eccdc4c60406e7fa0c95019adedb9d20478dfd56e36bd36e4718f5bc402c785c` |
| 185 | `local/unittest-gate-after-docs/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 186 | `local/unittest-gate-after-docs/plugin.log` | 11839 | `aaace4ff127076ce8ad78c81fe0359f4328e7263ce968dcc66385998ad886f9e` |
| 187 | `local/unittest-gate-after-docs/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 188 | `local/unittest-gate-after-docs/review-context.log` | 9860 | `876a1747254f085a26378d8adf4da1a101cce14486d86855f287d0df1add83c1` |
| 189 | `local/unittest-gate-after-docs/summary.json` | 1858 | `07bdaabe2ff9a36597de3db2758f1c61f93d82be870a7ab0dad3d08e2c7e189a` |
| 190 | `local/unittest-gate-after-docs/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 191 | `local/unittest-gate-after-docs/total.log` | 28072 | `cca7d65821441f051f8a2fe2a56cf5eb0dd91516c98acafff85ca90564cefc2a` |
| 192 | `pr-body.md` | 1550 | `aceb379c276b39216d0fb24ad1e0d2b044898d016d846d4e57f32b0e6fe21cb7` |
| 193 | `pr100-close-comment.md` | 2202 | `e9b39faf77e41a58738dd8b3964f9e935b94b70d5aefa58fe4facb7e3e90f57f` |
| 194 | `pr99-body-final.md` | 4021 | `d8c6abf0d98075fcc6a2ba11dafea7c85c0541c7b8ab73bb5fffa473f400354e` |
| 195 | `scripts/ac028-01-03-evidence.py` | 4901 | `87e37705dc9c57fe794a6cd8facd6d0880da3a845c52c2d9a1025a24f706d783` |
| 196 | `scripts/ac028-04-lock-drift.sh` | 3180 | `56ed6aa0f34b851a9786f565737ac8d2dccf70ad57d27ef0d02dcb0bfc6168fe` |
| 197 | `scripts/ac028-05-worktree-isolation.sh` | 5319 | `862ccbe369679410fed000033ed579d371adb86911bbaf48be32bedf817e9649` |
| 198 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/generator-output-manifest.txt` | 92 | `f90596bed34d9bb322c0946648ca300214f0a439f3fb643e957371e44928452f` |
| 199 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/generator.exit-code` | 2 | `1121cfccd5913f0a63fec40a6ffd44ea64f9dc135c66634ba001d10bcf4302a2` |
| 200 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/generator.stderr.log` | 166 | `1ff02b799cdf110ef9701c32772d84ce852b276387ca04f0b0a5adb24510ea71` |
| 201 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/generator.stdout.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 202 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/python-version.txt` | 14 | `917601090ffb73a030e3eaa8b7a01c41400cad4b61366b4218d7756a5733b66c` |
| 203 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/run-context.txt` | 238 | `9ec971867782293172bbbab95c4bb04653988ef5e84b0e661b43a68a00ac9839` |
| 204 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 205 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/unittest-gate/review-context.log` | 9773 | `4215918670d18aed1bba08ce8bdbb7bf85f95c708019ae427df41390f40c67d7` |
| 206 | `stacked-verify/negative-artifacts/review-context-diagnostics-pr-100-45956888727-1/unittest-gate/summary.json` | 681 | `2363c0dbd703657d91a63b6493dac1abde4cebb59eccd318200c1c7e87c213b0` |
| 207 | `stacked-verify/negative-run-45956888727.json` | 5854 | `f9ba97399922505bc9b1c38cd13fc311f33edb7fde55f4501caec690843ecb33` |
| 208 | `stacked-verify/negative-run-45956888769.json` | 10668 | `f7f23ae210b392f45748def7060b7218855354907d37e7f423500f1f8bc97232` |
| 209 | `stacked-verify/pr100-negative-view.json` | 876 | `eb84576bdf5e343a03a911a969e8d617579825b906350c6fbdf0bf49bff9fe92` |
| 210 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/generator-output-manifest.txt` | 101 | `3cd48384dafe048f5a35f94bfc159171ab752b42ae0547c0e22800316dbca2ea` |
| 211 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/generator.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 212 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/generator.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 213 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/generator.stdout.log` | 358 | `331fd08dcb2388312b58c575386821b11f532a96eea4a872685ec854638da6c3` |
| 214 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/python-version.txt` | 14 | `917601090ffb73a030e3eaa8b7a01c41400cad4b61366b4218d7756a5733b66c` |
| 215 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/run-context.txt` | 230 | `c0784067479f44e8c5d0f9ca055549c4e900960e06542580abaeb6fd3587cf81` |
| 216 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 217 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/unittest-gate/review-context.log` | 9773 | `aaf2e44db8ebf9dc857d5cd674d5392beedf45f2f5e21f9a3e35109fec4045d4` |
| 218 | `stacked-verify/recovery-artifacts/review-context-diagnostics-pr-100-45957598111-1/unittest-gate/summary.json` | 681 | `61ee4bffac59cfaddc7cea34cd7120fd88cfbaa3a62419732724a5912ed4c5b6` |
| 219 | `stacked-verify/recovery-artifacts/review-context-pr-100-45957598111-1/review-scope.json` | 5536 | `b5f33929f0ee059dfb5febe42e1b7785f0207eef5a170774566c3d6b2310794b` |
| 220 | `stacked-verify/recovery-artifacts/review-context-pr-100-45957598111-1/统一评审提示词.md` | 8590 | `f262e118e06a56535c177982501e1d963f001154f4fbd797af58c9569a75248b` |
| 221 | `stacked-verify/recovery-artifacts/review-context-pr-100-45957598111-1/评审上下文.md` | 6360 | `9d7b5ef3fad6a4744846e4e2b616ddb0f8a973dab42d984e0c7b4d02f817e460` |
| 222 | `stacked-verify/recovery-run-45956888727.json` | 5854 | `f9ba97399922505bc9b1c38cd13fc311f33edb7fde55f4501caec690843ecb33` |
| 223 | `stacked-verify/recovery-run-45956888769.json` | 10668 | `f7f23ae210b392f45748def7060b7218855354907d37e7f423500f1f8bc97232` |
| 224 | `stacked-verify/recovery-run-45957598111.json` | 5854 | `c213b557e5408809481ef3e9c3ce97316add3b0f6a99327d140237e5f982d610` |
| 225 | `stacked-verify/recovery-run-45957598133.json` | 10668 | `77087ba6422ef15884a15b74e6ed75941ae79abc1f16a8a5b58b7c59ce18020c` |
| 226 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/generator-output-manifest.txt` | 101 | `3cd48384dafe048f5a35f94bfc159171ab752b42ae0547c0e22800316dbca2ea` |
| 227 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/generator.exit-code` | 2 | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| 228 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/generator.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 229 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/generator.stdout.log` | 358 | `a2fc420fbc065b99a36aa0cf31ce784db6cd0901d711f1abcbf5a741c86793b6` |
| 230 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/python-version.txt` | 14 | `917601090ffb73a030e3eaa8b7a01c41400cad4b61366b4218d7756a5733b66c` |
| 231 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/run-context.txt` | 230 | `d5fbd2d8d819a778430826bf8f6f02e1c50cf0f773b9ecd7f5f2f3c64f9bb148` |
| 232 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 233 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/unittest-gate/review-context.log` | 9773 | `eb5316397c2e0671916cee95366fcc1b3bcc0fae433898748bbb43e0725d7ef2` |
| 234 | `stacked-verify/sync-artifacts/review-context-diagnostics-pr-100-45956150601-1/unittest-gate/summary.json` | 681 | `6e8955daa68074edd65c4af762279596c518d92f4b07d53f0c0345209818afad` |
| 235 | `stacked-verify/sync-artifacts/review-context-pr-100-45956150601-1/review-scope.json` | 5536 | `b5f33929f0ee059dfb5febe42e1b7785f0207eef5a170774566c3d6b2310794b` |
| 236 | `stacked-verify/sync-artifacts/review-context-pr-100-45956150601-1/统一评审提示词.md` | 8590 | `7c1a971b74d55f79955362c572eaea4f05d4a4187971b375f34492725b600d7b` |
| 237 | `stacked-verify/sync-artifacts/review-context-pr-100-45956150601-1/评审上下文.md` | 6360 | `25c04f09ceb0c7026b26650bf399d4caece0be9723af3a1bbdb3b99a65a0f21d` |
| 238 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/go-version.txt` | 33 | `07b0d66d21bcdfdc8456adcb17203f3af8656dc11549da62e6940f99b8d45444` |
| 239 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/python-version.txt` | 15 | `9d0ae83e540febd225949f3df4aba97c7a9f79fcf745d6c835780f52a57b50cf` |
| 240 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/run-context.txt` | 195 | `96b08a953dbaa767018b18de75feddd2f128be88042026c4ade944439c4948f6` |
| 241 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/smoke.stdout.log` | 146 | `367856635f4a784156f2c15ffbb60833b04b4fd7bf7a052ae73caab6bb6f7c99` |
| 242 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/sr003-evidence.json` | 2860 | `fd3c8c07aef1ac08f6c3b58fea27048a6666bda8d1606a6b2e2e098bdc9156a8` |
| 243 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.json` | 311 | `930a92ab2eb0b9e9c3ed89675f30eddabbd8a8a89fcc15a57a6309594540e7cf` |
| 244 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/host.log` | 6524 | `a37ee759e936e20dbf39d117ec3f7bf515634ae9f48629ac22a9261e1106ce08` |
| 245 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.json` | 315 | `43b4456907a2416dcf4df7b1fc7459dfb66df08aa7c26e4657b82e6fb95c0723` |
| 246 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/plugin.log` | 11745 | `6ea72e8845aa9641072e433edb0fc7e84b293199cda199f03c7da2dd1a3bde36` |
| 247 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.json` | 331 | `5544fdad6b3cd969cc84ae6f9689de83ff29f203c9924aa247a2f3dd1d44b2a8` |
| 248 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/review-context.log` | 9773 | `33ef707b535afd10fac4778fe2e8df1e124337db9c2e599c35e1290870dbab8c` |
| 249 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/summary.json` | 1736 | `d22c1ab6824849ff3f14d9aab83cc02c063707fe3bfcd4569aa8cb8f5abd10c1` |
| 250 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.json` | 311 | `d52943005748b33b7b6ccea6abf54bf3ba831069075be63c7c681a33ce318b39` |
| 251 | `stacked-verify/sync-artifacts/sr028-ubuntu-latest-3.12/unittest-gate/total.log` | 27845 | `820b8b72dc0ae1cff40a2bda700ccb5768df83c1a56398f80287e2466acd88a2` |
| 252 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/go-version.txt` | 35 | `69889abdfc6e43c76e2f8f74c354996d6552bed712e97f5774fb2253d7db135f` |
| 253 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/python-version.txt` | 15 | `2b095b05c4093ebca54b87bd2c6a6f557935e6b3f8f506a0c2e5e294a763f4ad` |
| 254 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/run-context.txt` | 199 | `dbd132f9ddcf9cbebc28b723f380ebd7582ab8c96e8ceb09373b755527252990` |
| 255 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/smoke.stdout.log` | 147 | `d231fa7c7098b2ac036acf0a064984111ac894af85b6f3103bac79ee13363cba` |
| 256 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/sr003-evidence.json` | 2993 | `fd0442eb8e2cda897639541f580e1436db4ae28d905c0648e59c9ace57debfb0` |
| 257 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.json` | 327 | `a192fcdb981953daf5587ec0c5b9e4c87a4bfd920a6a825a0bf4a0be71168dd1` |
| 258 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/host.log` | 6581 | `b252f4949a36c794bb46ce641b3a37ee0961eacb2ae2faac72a4d6cdfbfb659b` |
| 259 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.json` | 331 | `7892ff21d2d95f9d29ae18c896b3dd0d4071c7148f38897f6493babecad78f60` |
| 260 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/plugin.log` | 11839 | `009cb65f252ff0da9c1642bb2dd1dc0d75f36b0196c3d871012adacd0566304a` |
| 261 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.json` | 347 | `2fe1275a4943739d850738cabe13b945eb648e0f4473e62aa80251d455ba58e8` |
| 262 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/review-context.log` | 9859 | `77b3a43ab3df8b4fa2ca4613aa69d347840c5b7173e44071d23e7fceda6d6edb` |
| 263 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/summary.json` | 1796 | `0289eb16e87cffb2c6c3313a41c2137553db0c5564193a0162bfc8e242e47f65` |
| 264 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.json` | 327 | `4f0bbcce41f3ae1dda4ed944a59c53169dbe2cf425e53ca7bf83155dda336da8` |
| 265 | `stacked-verify/sync-artifacts/sr028-windows-latest-3.14.6/unittest-gate/total.log` | 28072 | `ab6222ce21de864b23cdad4f47b90fbe880bc2b1161378a92915d33b3b39fc17` |
| 266 | `stacked-verify/sync-run-45956150500.json` | 10668 | `e7906f45ff2485bbd45cbfcc33e646399695b450b2b05474c02318072f65318a` |
| 267 | `stacked-verify/sync-run-45956150601.json` | 5854 | `2e28cf76ed97a4bf21bf04ed85911247259db4824c5b4262742e7fc082a92016` |
| 268 | `verify-pr-body.md` | 1424 | `6e8757f1b539cf3d9c0c699fc7535e645f80165ee1c3bbd05e401f102b02533c` |
