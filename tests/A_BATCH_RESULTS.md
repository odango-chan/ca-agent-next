# A 批 Echo Plugin 原生 IPC 交付报告

本报告对应追加要求：A 批长期保留的 Go Echo Plugin 落到 `ca-agent-next` 仓库，Python 测试 Host、断言和负例 fixtures 放到 `tests/`，并从仓库根目录复跑。

## 最终文件路径

| 内容 | 路径 |
|---|---|
| Go 源码 | `examples/echo/plugin/main.go` |
| Go module | `examples/echo/plugin/go.mod` |
| Plugin Manifest | `examples/echo/plugin/plugin.yaml` |
| 请求 Schema | `examples/echo/plugin/schemas/echo-request.json` |
| 响应 Schema | `examples/echo/plugin/schemas/echo-response.json` |
| 构建与运行说明 | `examples/echo/plugin/README.md` |
| Python 测试 Host 与断言 | `tests/conformance/host_a.py` |
| 测试端负例注入 | `tests/conformance/host_a.py::Mutator` |
| 12 帧 fixture | `tests/fixtures/echo-12-frames.jsonl` |
| 负例 fixtures | `tests/fixtures/negative/*.json`（7 个） |
| 一条命令入口 | `tests/run_batch_a.py` |
| 测试说明 | `tests/README.md` |

## 构建命令

从 `examples/echo/plugin/` 执行：

```powershell
go build -trimpath -o bin/echo-plugin.exe .
```

Linux / macOS：

```bash
go build -trimpath -o bin/echo-plugin .
```

`plugin.yaml` 的 `process.executable` 为包根相对的 `bin/echo-plugin`；Windows 实际文件为 `bin/echo-plugin.exe`。构建产物目录 `bin/` 已被忽略。

## 启动命令

```powershell
.\bin\echo-plugin.exe serve
```

`serve` 与 `plugin.yaml` 的 `process.args: [serve]` 一致。手工单帧初始化可验证 `plugin.ready` 与 `ingress.event`。

## 测试命令

从仓库根目录一条命令：

```powershell
python tests/run_batch_a.py
```

该命令实际执行：

1. 校验 `plugin.yaml`、三个 Extension 和两个 Schema；
2. 从 `examples/echo/plugin/` 构建 `bin/echo-plugin.exe`；
3. 以 `examples/echo/plugin/bin/echo-plugin.exe serve` 为 argv 启动真实 Go 子进程；
4. 运行 A00–A08，写 `tests/evidence/` 与生成报告。

## 实际启动的进程

每个用例启动一份全新的同一二进制：

```text
<repo>/examples/echo/plugin/bin/echo-plugin.exe serve
```

示例 Plugin 没有 `ECHO_CASE` 或任何测试专用分支。正常用例与全部负例复用同一份未修改 Go 实现；负例由 Python 测试端在 Host 收发边界改写/复制帧。

## 用例结果（本次运行）

| 用例 ID | 输入或变异 | 预期 | 实测 | 状态 |
|---|---|---|---|---|
| A00-fixture | 解析 §5.1 JSONL | 12 帧类型/顺序正确 | 12 frames，types=ok | PASS |
| A01-echo-12-frames | 无变异，真实双进程 | 12 帧逐字段等于 §5.1 | 12/12 帧一致；registry=3；completions=2；exit=0 | PASS |
| A02-ready-missing-extension | 测试端从 ready.extensions 删除 `tools` | 整包注册数 0 | registered_extensions=0，handshake rejected | PASS |
| A03-duplicate-messageid | 测试端把 result.messageId 改为已用 `m3` | 重复 messageId 被拒，原 invoke 未完成 | pending_invoke=1，completions=0 | PASS |
| A04-unknown-correlation | 测试端把 correlationId 改为 `unknown-corr` | 未知关联被拒，原 invoke 未完成 | pending_invoke=1，completions=0 | PASS |
| A05-wrong-invocation | 测试端把 payload.invocationId 改为 `invX` | 操作身份不匹配被拒，原 invoke 未完成 | pending_invoke=1，completions=0 | PASS |
| A06-ack-runid | 测试端向 ack 注入 `runId=run-1` | 接收端判定协议违规 | `PROTOCOL_VIOLATION ... field_or_id=runId`，exit=2 | PASS |
| A07-delivery-wrong-id | 测试端把 deliveryId 改为 `delX` | 原义务不标 delivered | obligation del1=pending，delivered_count=0 | PASS |
| A08-terminal-twice | 测试端复制同一 tools.result | 原操作只完成一次 | completions=1，duplicate_terminal=1 | PASS |

结果：`9/9 PASS`，`FAIL=0`，命令退出码 0。A00 仅为 fixture 检查；A01–A08 均为真实 Go 子进程。

## 证据

- `tests/evidence/results.json`：机器可读结果；
- `tests/evidence/A_BATCH_RESULTS.md`：每次运行生成的逐例表；
- `tests/evidence/batchA/<case>/transcript.ndjson`：真实收发帧（脱敏）；
- `tests/evidence/batchA/<case>/plugin.stderr.log`：Plugin stderr；
- `tests/evidence/batchA/<case>/summary.json`：pending/completions/obligations；
- `tests/evidence/batchA/go-build.log`：构建命令、cwd 与退出码；
- `tests/fixtures/negative/*.json`：每个负例的单点注入规则。

## 干净 checkout 验证

从交付标签 `a-batch-echo-clean` 创建独立 worktree 后重新执行：

1. 按示例说明构建并以 `serve` 启动 → `plugin.ready` + `ingress.event`，退出码 0；
2. `python tests/run_batch_a.py` → A00–A08 全部 PASS，退出码 0，实际二进制路径为干净 worktree 内的 `examples/echo/plugin/bin/echo-plugin.exe`。

该验证不使用主工作区已有的 `bin/` 或 `tests/evidence/`；构建与证据均在干净 worktree 内重新生成。

## 与 B 批的关系

本追加只调整 A 批 Echo 示例落点和验收入口；B 批 Provider v2 的真实二进制对测与三份上游/发行证据保持原状，不因本次迁移改变。
