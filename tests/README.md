# A 批 Echo Plugin 协议对测

本目录保存 Native Plugin IPC v1alpha1 Echo 示例的 Python 测试 Host、协议断言与负例 fixtures。被测示例在 [`examples/echo/plugin/`](../examples/echo/plugin/)，是长期保留的 Go 实现。

## 一条命令

从仓库根目录：

```powershell
python tests/run_batch_a.py
```

该命令会：

1. 校验 `examples/echo/plugin/plugin.yaml`、三个 Extension 和两个 Schema；
2. 从 `examples/echo/plugin/` 执行 `go build`，生成 `examples/echo/plugin/bin/echo-plugin[.exe]`；
3. 以 `echo-plugin serve` 启动真实 Go 子进程；
4. 运行 `A00`–`A08`，写出 `tests/evidence/`、`tests/evidence/A_BATCH_RESULTS.md`，并给出稳定交付报告 [`A_BATCH_RESULTS.md`](A_BATCH_RESULTS.md)；
5. 任一用例 `FAIL` 时退出码为 1。

前置：Python 3.11+（验证使用 3.14.6）、PyYAML、Go 1.24+（验证使用 1.26.6）。

## 目录

```text
tests/
├── run_batch_a.py             # 唯一入口：构建示例并执行全部 A 批用例
├── conformance/
│   ├── common.py              # 证据、脱敏、结果结构
│   └── host_a.py              # Python 测试 Host、协议断言、测试端负例注入
├── fixtures/
│   ├── echo-12-frames.jsonl   # 设计 §5.1 的 12 帧
│   ├── echo-12-frames.provenance.json
│   └── negative/              # 七个单点负例的注入规则
│       ├── A02-ready-missing-extension.json
│       ├── A03-duplicate-messageid.json
│       ├── A04-unknown-correlation.json
│       ├── A05-wrong-invocation.json
│       ├── A06-ack-runid.json
│       ├── A07-delivery-wrong-id.json
│       └── A08-terminal-twice.json
├── evidence/                  # 运行生成（脱敏 NDJSON、stderr、summary）
├── A_BATCH_RESULTS.md         # 稳定交付报告（文件路径、命令、结果、干净 checkout）
└── README.md
```

## 负例注入模型

Go Echo Plugin 没有 `ECHO_CASE` 之类的测试模式。`tests/conformance/host_a.py::Mutator` 在 Host 的收发边界执行一次性改写：

- **inbound**：改写或复制 Plugin 发出的帧（ready 缺 Extension、重复 messageId、未知 correlationId、错误 invocationId、错误 deliveryId、重复终态）；
- **outbound**：改写 Host 将发送的帧（`ingress.ack` 注入 `runId`）。

每个用例启动一份全新的同一二进制，因此负例不会污染正常链路，也不会让示例实现为了测试而分叉。

## 证据

- `tests/evidence/results.json`：机器可读汇总；
- `tests/evidence/A_BATCH_RESULTS.md`：每次运行生成的逐例结果表；
- `tests/evidence/batchA/<case>/transcript.ndjson`：真实收发帧（已脱敏）；
- `tests/evidence/batchA/<case>/plugin.stderr.log`：Plugin stderr；
- `tests/evidence/batchA/<case>/summary.json`：断言结果、pending/completions、obligations；
- `tests/evidence/batchA/go-build.log`：构建命令、工作目录与退出码。
