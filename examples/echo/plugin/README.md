# Echo Plugin（Native Plugin IPC v1alpha1 示例）

这是 SR-003 统一 Plugin Manager 的 Go Echo 测试对端，位于：

```text
examples/echo/plugin/
├── main.go                    # UTF-8 NDJSON over stdin/stdout
├── go.mod                     # 独立模块，无第三方依赖
├── plugin.yaml                # connectionagent.io/plugin-package/v1alpha1
├── schemas/
│   ├── echo-request.json      # 闭合 object，必需 string text
│   └── echo-response.json     # 闭合 object，必需 string text
└── README.md
```

默认调用（`plugin.yaml` 的 `process.args: [serve]`）逐帧复现
`docs/规范/插件包与进程通信协议规范.md` §5.1 的固定 12 帧 golden，包括原始
messageId `m2`/`m3`/`m6`/`m8`/`m10`/`m12`。golden 文件为
[`tests/fixtures/echo-12-frames.jsonl`](../../../tests/fixtures/echo-12-frames.jsonl)，
其字节不得修改。

## 构建

从本目录执行（Linux / macOS）：

```bash
go build -trimpath -o bin/echo-plugin .
```

Windows：

```powershell
go build -trimpath -o bin/echo-plugin.exe .
```

`go.mod` 声明 `go 1.24`，实际验证使用 Go 1.26.6。构建产物写入 `bin/`，该目录已被
`.gitignore` 忽略。

## 启动

```bash
./bin/echo-plugin serve
```

```powershell
.\bin\echo-plugin.exe serve
```

`serve` 来自 `plugin.yaml` 的 `process.args`。Plugin 只从 stdin 读取协议帧、只向
stdout 写协议帧；诊断写入 stderr。可用 `--version` 查看版本。

启动后发送 §5.1 的 `host.initialize` 帧，Plugin 会依次输出 `plugin.ready` 和
`ingress.event`；Host 回复 `ingress.ack` 后可继续 `tools.invoke`、
`delivery.dispatch`、`host.cancel` 和 `host.shutdown`。

最小手工探测（单帧；真实 Host 交互见测试）：

```powershell
'{"apiVersion":"connectionagent.io/plugin-ipc/v1alpha1","messageId":"m1","type":"host.initialize","payload":{"pluginId":"example.echo","expectedVersion":"1.0.0","ipcVersion":"connectionagent.io/plugin-ipc/v1alpha1","config":{}}}' |
  .\bin\echo-plugin.exe serve
```

该命令会输出 `plugin.ready` 与 `ingress.event`，随后因 EOF 退出。完整双向流程需要
测试 Host 保持进程并回复帧。

## Callable

同一 Plugin 进程导出三个 `tools` Callable：

| Callable | 行为 |
|---|---|
| `echo.read` | 立即返回 `{"text": <arguments.text>}`；`inv1` + `hello` 保持 golden `m6` |
| `echo.describe` | 立即返回 `callableId` 与本进程导出的 operations |
| `echo.wait` | 保持 pending，直到 `host.cancel` 命中其 `invocationId`；`arguments.emitLateResult=true` 时在 `plugin.cancelled` 之后追加一帧迟到 `tools.result` |

`echo.wait` 用于受控 pending cancellation 测试；迟到结果只用于验证隔离，不会改变
原操作终态。

## Manifest 与校验

- `apiVersion` / `process.protocol` 固定为 `connectionagent.io/plugin-*` v1alpha1。
- `process.executable` 是包根相对的逻辑路径 `bin/echo-plugin`；Windows 实际文件为
  `bin/echo-plugin.exe`，Host 按平台解析。
- 三个 Extension 与 `plugin.ready.extensions` 必须整包完全匹配：`event.ingress`、
  `event.delivery`、`tools`。
- Schema 都是闭合 object，`additionalProperties: false`，必需字符串 `text`。
- 示例不包含 Skill 选择、授权、Owner 提交判断或生产语义。

## 测试专用开关（不属于 Plugin 协议）

以下参数只用于 SR-003 负例，默认调用从不使用：

| 参数 | 用途 |
|---|---|
| `--fault=<mode>` | `no-ready`、`crash-after-ready`、`duplicate-result`、`duplicate-terminal`、`unknown-correlation-id`、`wrong-invocation-id`、`out-of-order`、`wrong-delivery-id`、`cancel-no-reply`、`cancel-too-late-late-result`、`cancel-unsupported-late-result`、`shutdown-no-reply`、`shutdown-wrong-correlation`、`shutdown-bad-inflight`、`shutdown-negative-inflight`、`shutdown-duplicate`、`shutdown-zero-inflight`（自报 0 但仍有挂起）、`shutdown-excess-inflight`（自报比实际多 1） |
| `--extensions=<a,b,c>` | 覆盖 `plugin.ready.extensions`，验证握手整包匹配 |
| `--ingress=<json>` | 覆盖默认 `ingress.event` payload，可重复 |

测试通过 Manifest 的 `process.args` 传入这些参数，因此仍由真实的独立子进程执行。

## 与测试的关系

从仓库根目录运行：

```powershell
python -m unittest discover -s tests -p test_plugin.py -v
```

测试会构建本目录的 Go 源码，并以 `echo-plugin serve` 启动真实子进程；golden 回放、
Event ingress、双 Callable、Delivery 与 cancellation 都由 SR-003 的 Python Plugin
Manager 驱动。构建失败时测试直接报错，不会跳过必需用例。
