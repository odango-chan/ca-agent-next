"""一次性证据采集：启动真实 Go Echo Plugin 并输出 PID/Extension 证据。

不是测试套件的一部分；仅用于生成 SR-003 交付报告中的可复验数据。
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path("tests").resolve()))
import plugin_test_support as support  # noqa: E402
from ca_agent_next.plugins import PluginManager, PluginTimeouts  # noqa: E402


def main() -> int:
    host = support.FakeHost()
    manager = PluginManager(
        host,
        timeouts=PluginTimeouts(start=6, request=2, cancel=2, shutdown=4, terminate=3, grace_ms=100),
    )
    with tempfile.TemporaryDirectory() as directory:
        package = support.copy_package(Path(directory) / "example.echo")
        process = manager.start(package)
        assert process.wait_for_ingress(1, 5.0)
        read = manager.invoke_tool(
            "example.echo", "echo.read", {"text": "hello"}, invocation_id="inv1"
        )
        describe = manager.invoke_tool(
            "example.echo", "echo.describe", {"text": "hello"}, invocation_id="inv2"
        )
        delivery = manager.dispatch_delivery(
            "example.echo",
            response_obligation_id="obl1",
            response_channel_id="ch1",
            event_type="echo.request",
            body={"text": "hello"},
            delivery_id="del1",
        )
        cancel = manager.cancel_operation("example.echo", "inv1")
        frames = [
            {"direction": record.direction, "type": record.frame["type"],
             "messageId": record.frame["messageId"],
             "correlationId": record.frame.get("correlationId")}
            for record in process.frames
        ]
        evidence = {
            "pluginId": process.plugin_id,
            "pid": process.pid,
            "state": process.state.value,
            "extensions": sorted(process.extensions),
            "registeredExtensions": len(process.extensions),
            "ingress": {
                "hostCalls": len(host.calls),
                "disposition": process.ingress_records[0].disposition,
                "ack": dict(process.ingress_records[0].ack_payload),
            },
            "tools": {
                "read": {"status": read.status.value, "result": dict(read.result or {})},
                "describe": {"status": describe.status.value, "result": dict(describe.result or {})},
                "distinctCallables": read.callable_id != describe.callable_id,
            },
            "delivery": {
                "status": delivery.status,
                "deliveryId": delivery.delivery_id,
                "responseObligationId": delivery.response_obligation_id,
            },
            "cancel": {
                "disposition": cancel.disposition,
                "targetOperationId": cancel.target_operation_id,
                "cancelMessageId": cancel.cancel_message_id,
            },
            "terminalReadStatus": process.tool_terminal("inv1").status.value,
            "golden": {
                "path": str(support.GOLDEN_PATH.relative_to(support.REPO_ROOT)),
                "sha256": support.golden_sha256(),
                "provenanceSha256": support.load_provenance()["sha256"],
                "frames": len(support.load_golden()),
            },
            "frames": frames,
        }
        manager.stop("example.echo")
        evidence["pendingAfterStop"] = process.pending_count
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
