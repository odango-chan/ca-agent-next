"""``python -m ca_agent_next --smoke`` 最小 Smoke CLI。

CLI 只接受单一参数 ``--smoke``；默认使用进程内 Fake ModelClient，不读取
Provider 配置、不需要 API Key、不访问网络。所有失败只向 stderr 输出一行紧凑
JSON，失败时 stdout 为空。
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence

from .contracts import Event, HostError, ModelProposal, ModelRequest
from .host import Host
from .model_client import ModelClient

__all__ = ["main"]

_SCHEMA_VERSION = 1
_CLI_USAGE_ERROR = "CLI_USAGE_ERROR"
_CLI_USAGE_MESSAGE = "invalid command line usage"
_SMOKE_RUN_ID = "smoke-run-001"


class _SmokeModelClient:
    """默认进程内 Fake ModelClient；记录真实收到的请求。"""

    def __init__(self) -> None:
        self.calls: list[ModelRequest] = []

    def propose(self, request: ModelRequest) -> ModelProposal:
        self.calls.append(request)
        return ModelProposal(kind="smoke.echo", payload={"message": "smoke-ok"})


class _RecordingModelClient:
    """统计实际 ``propose`` 调用次数的透明包装。"""

    def __init__(self, inner: ModelClient) -> None:
        self._inner = inner
        self.call_count = 0

    def propose(self, request: ModelRequest) -> ModelProposal:
        self.call_count += 1
        return self._inner.propose(request)


def _smoke_event() -> Event:
    return Event(
        event_id="smoke-event-001",
        ingress_id="smoke",
        event_type="ca-agent-next.smoke",
        payload={"message": "hello"},
        source={"protocol": "smoke", "peerId": "local"},
    )


def _write_error(code: str, message: str) -> None:
    line = json.dumps(
        {
            "schema_version": _SCHEMA_VERSION,
            "error": {"code": code, "message": message},
        },
        separators=(",", ":"),
        ensure_ascii=False,
    )
    sys.stderr.write(line + "\n")


def _write_success(result_event_id: str, model_calls: int, proposal: ModelProposal) -> bool:
    try:
        line = json.dumps(
            {
                "schema_version": _SCHEMA_VERSION,
                "status": "ok",
                "event_id": result_event_id,
                "model_calls": model_calls,
                "proposal": {
                    "kind": proposal.kind,
                    "payload": proposal.payload,
                },
            },
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except Exception:
        return False
    sys.stdout.write(line + "\n")
    return True


def main(
    argv: Sequence[str] | None = None,
    *,
    model_client: ModelClient | None = None,
) -> int:
    """CLI 入口；返回进程退出码。"""
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["--smoke"]:
        _write_error(_CLI_USAGE_ERROR, _CLI_USAGE_MESSAGE)
        return 2

    if model_client is None:
        smoke_client = _SmokeModelClient()
        client: ModelClient = smoke_client
    else:
        recorder = _RecordingModelClient(model_client)
        client = recorder
    host = Host(client, run_id_factory=lambda: _SMOKE_RUN_ID)

    try:
        result = host.handle_event(_smoke_event())
    except HostError as exc:
        _write_error(exc.code, exc.safe_message)
        return 1
    except Exception:
        _write_error("HOST_INTERNAL_ERROR", "host internal error")
        return 1

    model_calls = (
        len(smoke_client.calls) if model_client is None else recorder.call_count
    )
    if not _write_success(result.run.event_id, model_calls, result.proposal):
        _write_error("HOST_INTERNAL_ERROR", "host internal error")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
