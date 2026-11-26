# A 批 Echo Plugin 原生 IPC 对测结果

- 运行时间：2026-11-26T09:31:38+0800 → 2026-11-26T09:31:40+0800
- 设计基线：`odango-chan/ca-agent-next@5b097e28e7197603cf3f00e103a0315c4bce0d79`
- 示例 Plugin：`examples/echo/plugin/plugin.yaml`
- 实际二进制：`examples/echo/plugin/bin/echo-plugin.exe`
- 构建命令：`go build -trimpath -o bin/echo-plugin.exe .`（cwd=`examples/echo/plugin/`；Linux/macOS 输出 `bin/echo-plugin`）
- 测试命令：`python tests/run_batch_a.py`（cwd=仓库根目录）
- 实际启动的进程：`examples/echo/plugin/bin/echo-plugin.exe serve`（每个用例一份全新进程；同一未修改二进制）
- 测试 Host：`tests/conformance/host_a.py`；负例注入：`tests/conformance/host_a.py::Mutator`

| 用例 ID | 两端进程及版本 | 输入或变异 | 预期 | 实测 | 状态 | 证据路径 |
|---|---|---|---|---|---|---|
| A00-fixture | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | parse §5.1 fenced JSONL block | 12 frames in request/reply order with the documented message types | 12 frames, types=ok | PASS | `tests/evidence/batchA/A00-fixture/summary.json` |
| A01-echo-12-frames | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | none (§5.1 exact frames) | real two-process round trip with all 12 frames and exact correlations | 12/12 frames match §5.1; registry=3 extensions; completions=2; delivery=delivered; exit=0 | PASS | `tests/evidence/batchA/A01-echo-12-frames/transcript.ndjson` |
| A02-ready-missing-extension | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound mutation removes tools from plugin.ready.extensions | whole-package registration count = 0; handshake not accepted | reported extensions=['event.ingress', 'event.delivery']; registered_extensions=0; handshake=rejected | PASS | `tests/evidence/batchA/A02-ready-missing-extension/transcript.ndjson` |
| A03-duplicate-messageid | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound mutation rewrites tools.result.messageId to already-used m3 | duplicate messageId rejected; original tools.invoke not completed | duplicate rejected; pending_invoke=1; completions=0 | PASS | `tests/evidence/batchA/A03-duplicate-messageid/transcript.ndjson` |
| A04-unknown-correlation | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound mutation rewrites tools.result.correlationId to unknown-corr | unknown correlationId rejected; original tools.invoke not completed | unknown correlation rejected; pending_invoke=1; completions=0 | PASS | `tests/evidence/batchA/A04-unknown-correlation/transcript.ndjson` |
| A05-wrong-invocation | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound mutation keeps correlationId=m5 but rewrites payload.invocationId to invX | operation identity mismatch rejected; original tools.invoke not completed | wrong invocationId rejected; pending_invoke=1; completions=0 | PASS | `tests/evidence/batchA/A05-wrong-invocation/transcript.ndjson` |
| A06-ack-runid | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side outbound mutation injects runId=run-1 into ingress.ack | receiver plugin declares protocol violation; no Host identity accepted | plugin stderr PROTOCOL_VIOLATION field=runId; exit=2 | PASS | `tests/evidence/batchA/A06-ack-runid/transcript.ndjson` |
| A07-delivery-wrong-id | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound mutation rewrites delivery.result.deliveryId to delX | response obligation del1 not marked delivered | wrong deliveryId rejected; obligation del1=pending; delivered_count=0 | PASS | `tests/evidence/batchA/A07-delivery-wrong-id/transcript.ndjson` |
| A08-terminal-twice | Python 3.14.6 test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0 | test-side inbound duplication emits tools.result twice for the same correlation | original operation completes exactly once; second terminal reply rejected | completions=1; duplicate_terminal=1; exit=0 | PASS | `tests/evidence/batchA/A08-terminal-twice/transcript.ndjson` |

## 判定说明

- `PASS` 只用于真实 Go 子进程用例；`A00-fixture` 是文档 JSONL 解析检查，不计作真实进程 PASS。
- 负例不由示例 Plugin 内置模式产生：测试端在 Host 收发边界改写/复制帧；示例实现每个用例都是同一份未修改二进制。
- 证据目录 `tests/evidence/batchA/<case>/` 含脱敏 NDJSON、Plugin stderr 与 summary。

总入口：`python tests/run_batch_a.py`（从仓库根目录执行）；本次退出码 0。