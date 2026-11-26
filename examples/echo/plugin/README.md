# Echo Plugin（Native Plugin IPC v1alpha1 示例）

这是 A 批协议对测长期保留的 Go Echo Plugin，位于：

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

## 构建

从本目录执行（Linux / macOS）：

```bash
go build -trimpath -o bin/echo-plugin .
```

Windows（本示例的 A 批实测平台）：

```powershell
go build -trimpath -o bin/echo-plugin.exe .
```

`go.mod` 声明 `go 1.24`，实际验证使用 Go 1.26.6。构建产物写入 `bin/`，该目录已被 `.gitignore` 忽略。

## 启动

```bash
./bin/echo-plugin serve
```

```powershell
.\bin\echo-plugin.exe serve
```

`serve` 来自 `plugin.yaml` 的 `process.args`。Plugin 只从 stdin 读取协议帧、只向 stdout 写协议帧；诊断写入 stderr。可用 `--version` 查看版本。

启动后发送 §5.1 的 `host.initialize` 帧，Plugin 会依次输出 `plugin.ready` 和 `ingress.event`；Host 回复 `ingress.ack` 后可继续 `tools.invoke`、`delivery.dispatch`、`host.cancel` 和 `host.shutdown`。完整 12 帧见
[`tests/fixtures/echo-12-frames.jsonl`](../../../tests/fixtures/echo-12-frames.jsonl)。

最小手工探测（单帧；真实 Host 交互见测试）：

```powershell
'{"apiVersion":"connectionagent.io/plugin-ipc/v1alpha1","messageId":"m1","type":"host.initialize","payload":{"pluginId":"example.echo","expectedVersion":"1.0.0","ipcVersion":"connectionagent.io/plugin-ipc/v1alpha1","config":{}}}' |
  .\bin\echo-plugin.exe serve
```

该命令会输出 `plugin.ready` 与 `ingress.event`，随后因 EOF 退出。完整双向流程需要测试 Host 保持进程并回复帧。

## Manifest 与校验规则

- `apiVersion` / `process.protocol` 固定为 `connectionagent.io/plugin-*` v1alpha1。
- `process.executable` 是包根相对的逻辑路径 `bin/echo-plugin`；Windows 实际文件为 `bin/echo-plugin.exe`，Host 按平台解析。
- 三个 Extension 与 `plugin.ready.extensions` 必须整包完全匹配：`event.ingress`、`event.delivery`、`tools`。
- Schema 都是闭合 object，`additionalProperties: false`，必需字符串 `text`。
- 示例不包含 Skill 选择、授权、Owner 提交判断或测试专用故障模式。

## 与 A 批测试的关系

从仓库根目录运行：

```powershell
python tests/run_batch_a.py
```

该命令会构建本目录的 Go 源码，并以 `echo-plugin serve` 启动真实子进程；正常用例与全部负例复用同一个二进制。负例由 Python 测试端在收发边界注入，不修改本示例实现。
