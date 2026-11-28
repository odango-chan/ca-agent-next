"""SR-003 模块验收：AC-003-01～AC-003-04。

所有 Lifecycle/IPC/Tools/Delivery/Cancellation 用例都通过真实 Go Echo
Plugin 子进程执行；Manifest 负例在握手前被拒绝。运行方式：

    python -m unittest discover -s tests -p test_plugin.py -v
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plugin_test_support as support  # noqa: E402

from ca_agent_next.contracts import HostError  # noqa: E402
from ca_agent_next.plugins import (  # noqa: E402
    CancelledOutcome,
    DeliveryOutcome,
    DriverProtocol,
    PluginError,
    PluginErrorCode,
    PluginManager,
    PluginProcess,
    PluginState,
    PluginTimeouts,
    PROVIDER_V2_PROTOCOL,
    ProviderV2ToolsExtensionDriver,
    ToolOutcome,
    ToolStatus,
    ToolsExtensionDriver,
    load_manifest,
)
from ca_agent_next.plugins import driver as driver_module  # noqa: E402
from ca_agent_next.plugins import manager as manager_module  # noqa: E402
from ca_agent_next.plugins.ipc import PendingRegistry, PendingRequest  # noqa: E402

BASE_MANIFEST = support.manifest_text()


def _timeouts(**overrides: float) -> PluginTimeouts:
    values: dict[str, float] = {
        "start": 6.0,
        "request": 0.6,
        "cancel": 1.5,
        "shutdown": 4.0,
        "terminate": 3.0,
        "grace_ms": 100,
    }
    values.update(overrides)
    return PluginTimeouts(**values)  # type: ignore[arg-type]


def setUpModule() -> None:  # noqa: N802 - unittest 约定
    support.ensure_echo_binary()


class _ManagerTestCase(unittest.TestCase):
    timeouts = _timeouts()

    def setUp(self) -> None:
        self.host = support.FakeHost()
        self.manager = PluginManager(self.host, timeouts=self.timeouts)
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.package = support.copy_package(self.tmp / "example.echo")

    def tearDown(self) -> None:
        self.manager.shutdown_all()

    def _fresh_manager(self, **timeouts: float) -> PluginManager:
        return PluginManager(self.host, timeouts=_timeouts(**timeouts))

    def _new_package(self, **kwargs: object) -> Path:
        destination = self.tmp / f"package-{uuid.uuid4().hex}"
        return support.copy_package(destination, **kwargs)  # type: ignore[arg-type]

    def _start(self, package: Path | None = None):
        return self.manager.start(package or self.package)

    def assert_no_dispatch(self) -> None:
        self.assertEqual(self.manager.total_tool_dispatches, 0)
        self.assertEqual(self.manager.total_delivery_dispatches, 0)

    def assert_rejected_without_registration(
        self,
        manager: PluginManager,
        package: Path,
        expected_code: str | None = None,
    ) -> PluginError:
        with self.assertRaises(PluginError) as caught:
            manager.start(package)
        error = caught.exception
        if expected_code is not None:
            self.assertEqual(error.code, expected_code, error)
        self.assertEqual(manager.extensions("example.echo"), frozenset())
        self.assertEqual(manager.total_tool_dispatches, 0)
        self.assertEqual(manager.total_delivery_dispatches, 0)
        with self.assertRaises(PluginError):
            manager.invoke_tool("example.echo", "echo.read", {"text": "x"})
        return error


# ---------------------------------------------------------------------------
# AC-003-01：Manifest / Schema
# ---------------------------------------------------------------------------


class ManifestValidationTests(_ManagerTestCase):
    """AC-003-01：非法包必须在握手前拒绝，注册数 0，派发数 0。"""

    def test_valid_manifest_loads_all_extensions(self) -> None:
        manifest = load_manifest(self.package)
        self.assertEqual(manifest.plugin_id, "example.echo")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.api_version, "connectionagent.io/plugin-package/v1alpha1")
        self.assertEqual(manifest.protocol, "connectionagent.io/plugin-ipc/v1alpha1")
        self.assertEqual(
            manifest.extensions,
            frozenset({"event.ingress", "event.delivery", "tools"}),
        )
        self.assertEqual(set(manifest.event_bindings), {"echo.request"})
        self.assertEqual(set(manifest.response_bindings), {"echo.request"})
        self.assertIn(manifest.executable_path.name, {"echo-plugin", "echo-plugin.exe"})
        self.assertEqual(manifest.args, ("serve",))
        self.assertEqual(manifest.tools_interface_package, "urn:example:echo:interface")

    def test_yaml_syntax_error_rejected(self) -> None:
        package = self._new_package(text=BASE_MANIFEST + "\n  broken: [\n")
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SYNTAX
        )

    def test_duplicate_yaml_key_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "  id: example.echo", "  id: example.echo\n  id: example.echo", 1
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_DUPLICATE_KEY
        )

    def test_unknown_top_level_field_rejected(self) -> None:
        package = self._new_package(text=BASE_MANIFEST + "\nunknownField: true\n")
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_UNKNOWN_FIELD
        )

    def test_unknown_nested_field_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "  version: 1.0.0", "  version: 1.0.0\n  labels: {}", 1
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_UNKNOWN_FIELD
        )

    def test_unsupported_package_api_version_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "connectionagent.io/plugin-package/v1alpha1",
            "connectionagent.io/plugin-package/v1alpha2",
            1,
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_VERSION_UNSUPPORTED
        )

    def test_unsupported_ipc_protocol_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "protocol: connectionagent.io/plugin-ipc/v1alpha1",
            "protocol: connectionagent.io/plugin-ipc/v2",
            1,
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_VERSION_UNSUPPORTED
        )

    def test_missing_required_field_rejected(self) -> None:
        text = BASE_MANIFEST.replace("  id: example.echo\n", "", 1)
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_FIELD_INVALID
        )

    def test_invalid_request_schema_json_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-request.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_invalid_response_schema_document_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-response.json").write_text(
            json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "nonsense"}),
            encoding="utf-8",
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_remote_schema_ref_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-request.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {"text": {"$ref": "https://example.com/remote.json"}},
                }
            ),
            encoding="utf-8",
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_remote_dynamic_ref_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-request.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "text": {
                            "$dynamicRef": "https://example.com/remote-dynamic.json"
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_unresolvable_local_dynamic_ref_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-response.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$dynamicRef": "#/$defs/missing",
                }
            ),
            encoding="utf-8",
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_unresolvable_local_schema_ref_rejected(self) -> None:
        package = self._new_package()
        (package / "schemas" / "echo-response.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$ref": "#/$defs/missing",
                }
            ),
            encoding="utf-8",
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    # -- P2-01：本地命名 Anchor 的存在性校验 ---------------------------------

    def _write_request_schema(self, package: Path, document: object) -> None:
        (package / "schemas" / "echo-request.json").write_text(
            json.dumps(document), encoding="utf-8"
        )

    def test_valid_local_json_pointer_ref_accepted(self) -> None:
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {"textNode": {"type": "string"}},
                "properties": {"text": {"$ref": "#/$defs/textNode"}},
            },
        )
        manifest = load_manifest(package)
        self.assertEqual(manifest.plugin_id, "example.echo")

    def test_valid_dynamic_anchor_reference_accepted(self) -> None:
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {"textNode": {"$dynamicAnchor": "node", "type": "string"}},
                "properties": {"text": {"$dynamicRef": "#node"}},
            },
        )
        manifest = load_manifest(package)
        self.assertEqual(manifest.plugin_id, "example.echo")

    def test_dynamic_ref_falls_back_to_plain_anchor(self) -> None:
        # Draft 2020-12 §8.2.3.2：动态作用域找不到同名 $dynamicAnchor 时，
        # $dynamicRef 退回 $ref 语义，因此 $anchor 声明的名称同样可解析。
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {"textNode": {"$anchor": "plainNode", "type": "string"}},
                "properties": {"text": {"$dynamicRef": "#plainNode"}},
            },
        )
        manifest = load_manifest(package)
        self.assertEqual(manifest.plugin_id, "example.echo")

    def test_missing_dynamic_ref_anchor_rejected(self) -> None:
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"text": {"$dynamicRef": "#missing-anchor"}},
            },
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_missing_plain_anchor_ref_rejected(self) -> None:
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"text": {"$ref": "#missing-anchor"}},
            },
        )
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )

    def test_unsupported_local_fragment_form_rejected(self) -> None:
        package = self._new_package()
        self._write_request_schema(
            package,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {"textNode": {"$dynamicAnchor": "node", "type": "string"}},
                "properties": {"text": {"$dynamicRef": "#node/child"}},
            },
        )
        error = self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_SCHEMA_INVALID
        )
        self.assertIn("unsupported local fragment", error.message)

    def test_path_traversal_in_schema_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "requestSchema: schemas/echo-request.json",
            "requestSchema: ../outside.json",
            1,
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_PATH_INVALID
        )

    def test_path_traversal_in_executable_rejected(self) -> None:
        text = BASE_MANIFEST.replace(
            "executable: bin/echo-plugin", "executable: ../echo-plugin", 1
        )
        package = self._new_package(text=text)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_PATH_INVALID
        )

    def test_symlink_escape_rejected(self) -> None:
        package = self._new_package()
        outside = self.tmp / "outside-schemas"
        outside.mkdir()
        (outside / "echo-request.json").write_text(
            (package / "schemas" / "echo-request.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        target = package / "schemas"
        for child in target.iterdir():
            child.unlink()
        target.rmdir()
        support.make_dir_link(target, outside)
        self.assert_rejected_without_registration(
            self.manager, package, PluginErrorCode.MANIFEST_PATH_INVALID
        )

    def test_handshake_missing_extension_rejected(self) -> None:
        package = self._new_package(
            args=["serve", "--extensions=event.ingress,event.delivery"]
        )
        manager = self._fresh_manager()
        captured: dict[str, PluginProcess] = {}
        original_start = PluginProcess.start

        def capture(process: PluginProcess) -> PluginProcess:
            captured["process"] = process
            return original_start(process)

        with mock.patch.object(PluginProcess, "start", capture):
            error = self.assert_rejected_without_registration(
                manager, package, PluginErrorCode.HANDSHAKE_MISMATCH
            )
        self.assertIn("extensions", error.message)
        process = captured["process"]
        self.assertNotEqual(process.state, PluginState.READY)
        self.assertEqual(process.extensions, frozenset())
        self.assertTrue(process.wait_for_exit(5.0))
        # 握手失败同样不留下有效的 Manager-owned Process 注册。
        self.assertIsNone(manager.process("example.echo"))
        self.assertEqual(manager.plugin_ids(), ())

    def test_handshake_extra_extension_rejected(self) -> None:
        package = self._new_package(
            args=["serve", "--extensions=event.ingress,event.delivery,tools,metrics"]
        )
        manager = self._fresh_manager()
        self.assert_rejected_without_registration(
            manager, package, PluginErrorCode.HANDSHAKE_MISMATCH
        )

    def test_handshake_timeout_rejected(self) -> None:
        # 真正超时：子进程保持存活但不发送 ready。测试超时和 EOF 互不混淆。
        package = self._new_package(args=["serve", "--fault=stall-before-ready"])
        manager = self._fresh_manager(start=0.6)
        self.assert_rejected_without_registration(
            manager, package, PluginErrorCode.IPC_TIMEOUT
        )

    def test_process_exit_before_ready_is_not_a_timeout(self) -> None:
        # no-ready 立即退出应报告 PROCESS_EXITED，而非伪造等满超时。
        package = self._new_package(args=["serve", "--fault=no-ready"])
        manager = self._fresh_manager()
        error = self.assert_rejected_without_registration(
            manager, package, PluginErrorCode.PROCESS_EXITED
        )
        self.assertEqual(error.details.get("phase"), "before")


# ---------------------------------------------------------------------------
# AC-003-02：Lifecycle / IPC
# ---------------------------------------------------------------------------


class LifecycleIpcTests(_ManagerTestCase):
    """AC-003-02：一个 PID、三类 Extension、12 帧 golden、关联与清理。"""

    def test_start_registers_three_extensions_for_one_process(self) -> None:
        process = self._start()
        try:
            self.assertEqual(process.state, PluginState.READY)
            self.assertEqual(
                process.extensions,
                frozenset({"event.ingress", "event.delivery", "tools"}),
            )
            self.assertIsInstance(process.pid, int)
            self.assertGreater(process.pid or 0, 0)
            self.assertEqual(self.manager.plugin_ids(), ("example.echo",))
            ready_frames = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "plugin.ready"
            ]
            self.assertEqual(len(ready_frames), 1)
            self.assertEqual(
                ready_frames[0]["payload"]["extensions"],
                ["event.ingress", "event.delivery", "tools"],
            )
            self.assertIsNotNone(ready_frames[0]["correlationId"])
        finally:
            self.manager.stop("example.echo")
        self.assertEqual(process.state, PluginState.STOPPED)
        self.assertEqual(process.extensions, frozenset())
        self.assertEqual(process.pending_count, 0)

    def test_golden_twelve_frames_replay(self) -> None:
        golden = support.load_golden()
        self.assertEqual(len(golden), 12)
        host_ids = {"m1", "m4", "m5", "m7", "m9", "m11"}
        plugin_ids = {"m2", "m3", "m6", "m8", "m10", "m12"}
        self.assertEqual({frame["messageId"] for frame in golden}, host_ids | plugin_ids)
        self.assertEqual(
            {frame["messageId"] for frame in golden if frame["messageId"] in host_ids},
            host_ids,
        )
        provenance = support.load_provenance()
        digest = support.golden_sha256()
        self.assertEqual(digest, provenance["sha256"])
        self.assertEqual(provenance["frameCount"], 12)

        binary = support.ensure_echo_binary()
        proc = subprocess.Popen(
            [str(binary), "serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(binary.parent),
        )
        try:

            def send(frame: dict) -> None:
                assert proc.stdin is not None
                proc.stdin.write(
                    (json.dumps(frame, ensure_ascii=False) + "\n").encode("utf-8")
                )
                proc.stdin.flush()

            def receive() -> dict:
                assert proc.stdout is not None
                line = proc.stdout.readline()
                self.assertTrue(line, "plugin closed stdout before replying")
                return json.loads(line.decode("utf-8"))

            send(golden[0])
            received = [receive(), receive()]
            send(golden[3])
            send(golden[4])
            received.append(receive())
            send(golden[6])
            received.append(receive())
            send(golden[8])
            received.append(receive())
            send(golden[10])
            received.append(receive())
            assert proc.stdin is not None
            proc.stdin.close()
            self.assertEqual(proc.wait(timeout=10), 0)
            stderr = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    if stream is not None:
                        stream.close()
                except OSError:
                    pass

        expected = [golden[index] for index in (1, 2, 5, 7, 9, 11)]
        self.assertEqual(received, expected)
        self.assertIn("STOPPED_SENT", stderr)

    def test_manager_golden_trajectory(self) -> None:
        process = self._start()
        try:
            self.assertTrue(process.wait_for_ingress(1, 5.0))
            ingress = process.ingress_records[0]
            self.assertEqual(ingress.disposition, "accepted")
            self.assertTrue(ingress.host_called)
            self.assertEqual(len(self.host.calls), 1)

            result = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "hello"},
                invocation_id="inv1",
            )
            self.assertEqual(result.status, ToolStatus.RESULT)
            self.assertEqual(dict(result.result or {}), {"text": "hello"})

            delivery = self.manager.dispatch_delivery(
                "example.echo",
                response_obligation_id="obl1",
                response_channel_id="ch1",
                event_type="echo.request",
                body={"text": "hello"},
                status_code=200,
                delivery_id="del1",
            )
            self.assertEqual(delivery.status, "delivered")
            self.assertEqual(delivery.delivery_id, "del1")
            self.assertEqual(delivery.response_obligation_id, "obl1")
            self.assertEqual(delivery.status_code, 200)

            cancelled = self.manager.cancel_operation("example.echo", "inv1")
            self.assertEqual(cancelled.disposition, "too_late")
            self.assertEqual(cancelled.target_operation_id, "inv1")

            terminal = process.tool_terminal("inv1")
            self.assertIsNotNone(terminal)
            assert terminal is not None
            self.assertEqual(terminal.status, ToolStatus.RESULT)
            self.assertEqual(dict(terminal.result or {}), {"text": "hello"})
            self.assertEqual(process.pending_count, 0)

            ack_frames = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "ingress.ack"
            ]
            self.assertEqual(len(ack_frames), 1)
            ack_payload = ack_frames[0]["payload"]
            self.assertLessEqual(set(ack_payload), {"eventId", "disposition", "error"})
            self.assertEqual(ack_payload, {"eventId": "evt1", "disposition": "accepted"})
            ack_text = support.compact_json(ack_payload)
            for leaked in ("run-test-001", "artifactRef", "stagingPath", "skill"):
                self.assertNotIn(leaked, ack_text)
        finally:
            self.manager.stop("example.echo")
        self.assertEqual(process.pending_count, 0)
        self.assertEqual(process.state, PluginState.STOPPED)

    def test_duplicate_message_id_does_not_double_complete(self) -> None:
        package = self._new_package(args=["serve", "--fault=duplicate-result"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "dup"},
                invocation_id="inv-dup",
            )
            self.assertEqual(outcome.status, ToolStatus.RESULT)
            self.assertTrue(
                process.wait_for(lambda p: p.duplicate_inbound_frames >= 1, 3.0)
            )
            self.assertEqual(process.pending_count, 0)
            terminal = process.tool_terminal("inv-dup")
            assert terminal is not None
            self.assertEqual(dict(terminal.result or {}), {"text": "dup"})
        finally:
            self.manager.stop("example.echo")

    def test_unknown_correlation_id_does_not_complete(self) -> None:
        package = self._new_package(args=["serve", "--fault=unknown-correlation-id"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "orphan"},
                invocation_id="inv-orphan",
            )
            self.assertEqual(outcome.status, ToolStatus.TIMEOUT)
            self.assertGreaterEqual(process.unmatched_replies, 1)
            self.assertEqual(process.pending_count, 0)
            # 请求超时后进程必须退出并注销 Extension，不能再保持 READY。
            self.assertEqual(process.state, PluginState.NOT_READY)
            self.assertEqual(process.extensions, frozenset())
            self.assertEqual(self.manager.extensions("example.echo"), frozenset())
            self.assertTrue(process.wait_for_exit(10.0))
            self.assertIsNotNone(process._proc)
            assert process._proc is not None
            self.assertIsNotNone(process._proc.poll())
            self.assertEqual(process.tool_dispatches, 1)
            with self.assertRaises(PluginError):
                self.manager.invoke_tool(
                    "example.echo", "echo.read", {"text": "after-timeout"}
                )
        finally:
            self.manager.stop("example.echo")

    def test_wrong_invocation_id_does_not_complete(self) -> None:
        package = self._new_package(args=["serve", "--fault=wrong-invocation-id"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "mismatch"},
                invocation_id="inv-mismatch",
            )
            self.assertEqual(outcome.status, ToolStatus.TIMEOUT)
            self.assertGreaterEqual(process.unmatched_replies, 1)
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_out_of_order_replies_are_correlated(self) -> None:
        package = self._new_package(args=["serve", "--fault=out-of-order"])
        process = self.manager.start(package)
        try:
            first = self.manager.invoke_tool_async(
                "example.echo", "echo.read", {"text": "one"}, invocation_id="inv-one"
            )
            second = self.manager.invoke_tool_async(
                "example.echo", "echo.read", {"text": "two"}, invocation_id="inv-two"
            )
            first_outcome = first.wait(5.0)
            second_outcome = second.wait(5.0)
            self.assertEqual(first_outcome.status, ToolStatus.RESULT)
            self.assertEqual(second_outcome.status, ToolStatus.RESULT)
            self.assertEqual(dict(first_outcome.result or {}), {"text": "one"})
            self.assertEqual(dict(second_outcome.result or {}), {"text": "two"})
            self.assertEqual(first_outcome.invocation_id, "inv-one")
            self.assertEqual(second_outcome.invocation_id, "inv-two")
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_duplicate_terminal_frame_is_ignored(self) -> None:
        package = self._new_package(args=["serve", "--fault=duplicate-terminal"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "terminal"},
                invocation_id="inv-terminal",
            )
            self.assertEqual(outcome.status, ToolStatus.RESULT)
            self.assertTrue(process.wait_for(lambda p: p.unmatched_replies >= 1, 3.0))
            terminal = process.tool_terminal("inv-terminal")
            assert terminal is not None
            self.assertEqual(terminal.status, ToolStatus.RESULT)
            self.assertEqual(dict(terminal.result or {}), {"text": "terminal"})
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_process_exit_clears_extensions(self) -> None:
        # 故障 peer 发送有效 ready 后立即退出。start 可能先观察 READY
        # 并返回，也可能先观察 EOF 并以 PROCESS_EXITED 拒绝注册；
        # 两种调度都必须释放所有 Extension，绝不返回假 READY。
        package = self._new_package(args=["serve", "--fault=crash-after-ready"])
        captured: dict[str, PluginProcess] = {}
        original_start = PluginProcess.start

        def capture(process: PluginProcess) -> PluginProcess:
            captured["process"] = process
            return original_start(process)

        with mock.patch.object(PluginProcess, "start", capture):
            try:
                process = self.manager.start(package)
            except PluginError as error:
                self.assertEqual(error.code, PluginErrorCode.PROCESS_EXITED)
                self.assertEqual(error.details.get("phase"), "after")
                process = captured["process"]
                self.assertIsNone(self.manager.process("example.echo"))

        self.assertTrue(
            any(record.frame["type"] == "plugin.ready" for record in process.frames)
        )
        self.assertTrue(process.wait_for_exit(5.0))
        self.assertNotEqual(process.state, PluginState.READY)
        self.assertEqual(process.extensions, frozenset())
        self.assertEqual(self.manager.extensions("example.echo"), frozenset())
        self.assertEqual(process.pending_count, 0)
        with self.assertRaises(PluginError):
            self.manager.invoke_tool("example.echo", "echo.read", {"text": "x"})

    def test_ready_then_eof_before_start_lock_reports_process_exited(self) -> None:
        # 同步控制 Reader 的锁，强制实现此前 CI 偶发的 ready -> EOF
        # 先于 start 状态检查顺序；无需 sleep、超时放宽或概率性压测。
        package = self._new_package(args=["serve", "--fault=crash-after-ready"])
        original_on_ready = PluginProcess._on_ready

        def ready_then_eof(process: PluginProcess, frame: object) -> None:
            with process._lock:
                original_on_ready(process, frame)  # type: ignore[arg-type]
                self.assertIs(process._state, PluginState.READY)
                process._finalize_exit()

        manager = self._fresh_manager()
        with mock.patch.object(PluginProcess, "_on_ready", ready_then_eof):
            error = self.assert_rejected_without_registration(
                manager, package, PluginErrorCode.PROCESS_EXITED
            )
        self.assertEqual(error.details.get("phase"), "after")

    def test_shutdown_leaves_no_pending_requests(self) -> None:
        process = self._start()
        self.assertTrue(process.wait_for_ingress(1, 5.0))
        self.manager.stop("example.echo")
        self.assertEqual(process.pending_count, 0)
        self.assertEqual(process.state, PluginState.STOPPED)
        stopped = [
            record.frame
            for record in process.frames
            if record.frame["type"] == "plugin.stopped"
        ]
        self.assertEqual(len(stopped), 1)
        self.assertEqual(stopped[0]["payload"], {"inFlightCount": 0})


# ---------------------------------------------------------------------------
# #119：Echo fixture 的接收侧 IPC 负例（真实 Go 二进制）
# ---------------------------------------------------------------------------


class EchoReceiverProtocolTests(unittest.TestCase):
    """向真实 Echo 进程注入 Host->Plugin 帧，不依赖 Manager 发送侧校验。"""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.binary = support.ensure_echo_binary()

    @classmethod
    def _run(cls, *frames: dict) -> subprocess.CompletedProcess[str]:
        binary = cls.binary
        payload = "".join(
            json.dumps(frame, ensure_ascii=False, separators=(",", ":")) + "\n"
            for frame in frames
        )
        return subprocess.run(
            [str(binary), "serve"],
            cwd=binary.parent,
            input=payload,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def assert_violation(self, frames: list[dict], code: str) -> None:
        completed = self._run(*frames)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("PROTOCOL_VIOLATION", completed.stderr)
        self.assertIn(f"code={code}", completed.stderr)
        emitted = [
            json.loads(line)
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        self.assertNotIn(
            "delivery.result",
            [frame["type"] for frame in emitted],
            "invalid dispatch must not be acknowledged as delivered",
        )

    def test_ack_rejects_invalid_receiver_payload(self) -> None:
        golden = support.load_golden()
        for name, changes, code in [
            ("accepted-error", {"error": {"code": "UNEXPECTED"}}, "ACK_UNEXPECTED_ERROR"),
            ("duplicate-error", {"disposition": "duplicate_attached", "error": {}}, "ACK_UNEXPECTED_ERROR"),
            ("nested-run", {"disposition": "conflict", "error": {"code": "CONFLICT", "details": {"runId": "secret"}}}, "ACK_ERROR_UNEXPECTED_FIELD"),
            ("nested-channel", {"disposition": "rejected", "error": {"details": {"responseChannelId": "secret"}}}, "ACK_ERROR_UNEXPECTED_FIELD"),
            ("error-skill-id", {"disposition": "rejected", "error": {"skillId": "secret"}}, "ACK_ERROR_UNEXPECTED_FIELD"),
            ("error-wrong-shape", {"disposition": "conflict", "error": "oops"}, "ACK_ERROR_INVALID"),
            ("error-code-nested", {"disposition": "rejected", "error": {"code": {"artifactRef": "secret"}}}, "ACK_ERROR_INVALID"),
            ("error-retryable-type", {"disposition": "rejected", "error": {"retryable": "yes"}}, "ACK_ERROR_INVALID"),
            ("correlation", {"_correlationId": "unknown-message"}, "ACK_CORRELATION_MISMATCH"),
            ("event-id", {"eventId": "wrong-event"}, "ACK_CORRELATION_MISMATCH"),
        ]:
            with self.subTest(name=name):
                ack = json.loads(json.dumps(golden[3]))
                if "_correlationId" in changes:
                    ack["correlationId"] = changes["_correlationId"]
                else:
                    ack["payload"].update(changes)
                self.assert_violation([golden[0], ack], code)

    def test_ack_accepts_safe_rejection_error_and_empty_event_id(self) -> None:
        golden = support.load_golden()
        safe = json.loads(json.dumps(golden[3]))
        safe["payload"] = {
            "eventId": "evt1",
            "disposition": "rejected",
            "error": {
                "code": "EVENT_INVALID",
                "message": "invalid input",
                "retryable": False,
            },
        }
        finished = self._run(golden[0], safe, golden[10])
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertIn("ACK disposition=rejected", finished.stderr)

        # A malformed ingress still gets an ack for its original event ID.
        custom = support.compact_json(
            {
                "eventId": "",
                "ingressId": "example.echo",
                "eventType": "echo.request",
                "responseChannelId": "ch-custom",
                "source": {"protocol": "echo", "peerId": "test-peer"},
                "payload": {"text": "hello"},
                "artifacts": [],
            }
        )
        invalid_ack = json.loads(json.dumps(golden[3]))
        invalid_ack["correlationId"] = "x1"
        invalid_ack["payload"] = {
            "eventId": "",
            "disposition": "rejected",
            "error": {"code": "FIELD_INVALID", "message": "invalid"},
        }
        finished = subprocess.run(
            [str(self.binary), "serve", f"--ingress={custom}"],
            cwd=self.binary.parent,
            input="".join(
                json.dumps(frame) + "\n"
                for frame in (golden[0], invalid_ack, golden[10])
            ),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(finished.returncode, 0, finished.stderr)

    def test_delivery_rejects_missing_and_ill_typed_fields(self) -> None:
        golden = support.load_golden()
        for name, field, value, expected in [
            ("missing-obligation", "responseObligationId", None, "DELIVERY_REQUIRED_FIELD"),
            ("empty-obligation", "responseObligationId", "", "DELIVERY_REQUIRED_FIELD"),
            ("missing-channel", "responseChannelId", None, "DELIVERY_REQUIRED_FIELD"),
            ("empty-channel", "responseChannelId", "", "DELIVERY_REQUIRED_FIELD"),
            ("missing-event-type", "eventType", None, "DELIVERY_REQUIRED_FIELD"),
            ("missing-headers", "headers", None, "DELIVERY_REQUIRED_FIELD"),
            ("headers-array", "headers", [], "DELIVERY_REQUIRED_FIELD"),
            ("missing-body", "body", None, "DELIVERY_REQUIRED_FIELD"),
            ("decimal-status", "statusCode", 201.5, "DELIVERY_STATUS_INVALID"),
            ("negative-status", "statusCode", -1, "DELIVERY_STATUS_INVALID"),
            ("missing-delivery", "deliveryId", None, "DELIVERY_IDENTITY_MISMATCH"),
        ]:
            with self.subTest(name=name):
                dispatch = json.loads(json.dumps(golden[6]))
                if value is None:
                    dispatch["payload"].pop(field, None)
                else:
                    dispatch["payload"][field] = value
                self.assert_violation([golden[0], golden[3], dispatch], expected)

    def test_delivery_accepts_null_body_without_relaxing_fields(self) -> None:
        golden = support.load_golden()
        dispatch = json.loads(json.dumps(golden[6]))
        dispatch["payload"]["body"] = None
        completed = self._run(golden[0], golden[3], dispatch, golden[10])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        messages = [
            json.loads(line)
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        self.assertEqual(
            sum(frame["type"] == "delivery.result" for frame in messages),
            1,
        )


# ---------------------------------------------------------------------------
# AC-003-03：Event ingress
# ---------------------------------------------------------------------------


def _ingress_payload(**overrides: object) -> dict:
    payload = {
        "eventId": "evt-custom",
        "ingressId": "example.echo",
        "eventType": "echo.request",
        "externalRequestId": "client-custom",
        "responseChannelId": "ch-custom",
        "source": {"protocol": "echo", "peerId": "test-peer"},
        "payload": {"text": "hello"},
        "artifacts": [],
    }
    payload.update(overrides)
    return payload


class EventIngressTests(_ManagerTestCase):
    """AC-003-03：声明、Source、Schema、映射、Host 调用次数与 ack 安全。"""

    def _start_with_events(self, events: list[dict]):
        args = ["serve"] + [
            f"--ingress={support.compact_json(event)}" for event in events
        ]
        package = self._new_package(args=args)
        process = self.manager.start(package)
        self.assertTrue(
            process.wait_for_ingress(len(events), 5.0),
            f"expected {len(events)} ingress records",
        )
        return process

    def test_valid_event_maps_to_f01_and_calls_host_once(self) -> None:
        process = self._start()
        try:
            self.assertTrue(process.wait_for_ingress(1, 5.0))
            record = process.ingress_records[0]
            self.assertEqual(record.disposition, "accepted")
            self.assertTrue(record.host_called)
            self.assertEqual(len(self.host.calls), 1)
            event = self.host.calls[0]
            self.assertIs(event, record.event)
            self.assertEqual(event.event_id, "evt1")
            self.assertEqual(event.ingress_id, "example.echo")
            self.assertEqual(event.event_type, "echo.request")
            self.assertEqual(event.external_request_id, "client-1")
            self.assertEqual(event.response_channel_id, "ch1")
            self.assertEqual(
                event.source, {"protocol": "echo", "peerId": "test-peer"}
            )
            self.assertIn("peerId", event.source)
            self.assertEqual(dict(event.payload), {"text": "hello"})
            self.assertEqual(event.artifact_refs, ())
            self.assertLessEqual(
                set(record.ack_payload), {"eventId", "disposition", "error"}
            )
        finally:
            self.manager.stop("example.echo")

    def test_undeclared_event_type_rejected_and_host_not_called(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(eventType="echo.undeclared")]
        )
        record = process.ingress_records[0]
        self.assertEqual(record.disposition, "rejected")
        self.assertFalse(record.host_called)
        self.assertEqual(record.error_code, "EVENT_TYPE_UNDECLARED")
        self.assertEqual(self.host.calls, [])

    def test_ingress_id_mismatch_rejected(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(ingressId="other.plugin")]
        )
        record = process.ingress_records[0]
        self.assertEqual(record.error_code, "INGRESS_ID_MISMATCH")
        self.assertEqual(self.host.calls, [])

    def test_missing_source_rejected(self) -> None:
        payload = _ingress_payload()
        payload.pop("source")
        process = self._start_with_events([payload])
        record = process.ingress_records[0]
        self.assertEqual(record.error_code, "MISSING_FIELD")
        self.assertEqual(self.host.calls, [])

    def test_invalid_source_protocol_rejected(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(source={"protocol": "", "peerId": "peer"})]
        )
        self.assertEqual(process.ingress_records[0].error_code, "SOURCE_INVALID")
        self.assertEqual(self.host.calls, [])

    def test_invalid_source_peer_id_rejected(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(source={"protocol": "echo", "peerId": 7})]
        )
        self.assertEqual(process.ingress_records[0].error_code, "SOURCE_INVALID")
        self.assertEqual(self.host.calls, [])

    def test_payload_schema_violation_rejected(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(payload={"text": "hello", "extra": 1})]
        )
        self.assertEqual(process.ingress_records[0].error_code, "PAYLOAD_SCHEMA_INVALID")
        self.assertEqual(self.host.calls, [])

    def test_payload_missing_required_property_rejected(self) -> None:
        process = self._start_with_events([_ingress_payload(payload={})])
        self.assertEqual(process.ingress_records[0].error_code, "PAYLOAD_SCHEMA_INVALID")
        self.assertEqual(self.host.calls, [])

    def test_artifact_descriptors_rejected_without_mapping(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(artifacts=[{"slot": "input", "mediaType": "text/plain", "required": True}])]
        )
        record = process.ingress_records[0]
        self.assertEqual(record.error_code, "ARTIFACT_CHANNEL_NOT_CONFIGURED")
        self.assertIsNone(record.event)
        self.assertEqual(self.host.calls, [])

    def test_empty_event_id_rejected(self) -> None:
        process = self._start_with_events([_ingress_payload(eventId="")])
        self.assertEqual(process.ingress_records[0].error_code, "FIELD_INVALID")
        self.assertEqual(self.host.calls, [])

    def test_unknown_ingress_field_rejected(self) -> None:
        process = self._start_with_events(
            [_ingress_payload(skillId="must-not-be-accepted")]
        )
        self.assertEqual(process.ingress_records[0].error_code, "UNKNOWN_FIELD")
        self.assertEqual(self.host.calls, [])

    def test_duplicate_event_is_attached_without_second_host_call(self) -> None:
        duplicate = _ingress_payload()
        process = self._start_with_events([duplicate, duplicate])
        first, second = process.ingress_records
        self.assertEqual(first.disposition, "accepted")
        self.assertEqual(second.disposition, "duplicate_attached")
        self.assertFalse(second.host_called)
        self.assertEqual(len(self.host.calls), 1)

    def test_conflicting_event_identity_rejected(self) -> None:
        process = self._start_with_events(
            [
                _ingress_payload(payload={"text": "first"}),
                _ingress_payload(payload={"text": "second"}),
            ]
        )
        first, second = process.ingress_records
        self.assertEqual(first.disposition, "accepted")
        self.assertEqual(second.disposition, "conflict")
        self.assertEqual(second.error_code, "EVENT_CONFLICT")
        self.assertEqual(len(self.host.calls), 1)

    def test_host_failure_is_reported_without_internal_identity(self) -> None:
        self.host.error = HostError("EVENT_INVALID", "event is invalid")
        process = self._start()
        try:
            self.assertTrue(process.wait_for_ingress(1, 5.0))
            record = process.ingress_records[0]
            self.assertEqual(record.disposition, "rejected")
            self.assertTrue(record.host_called)
            self.assertEqual(record.ack_payload["error"]["code"], "EVENT_INVALID")
            self.assertLessEqual(
                set(record.ack_payload), {"eventId", "disposition", "error"}
            )
            self.assertNotIn("run-test-001", support.compact_json(record.ack_payload))
        finally:
            self.manager.stop("example.echo")


# ---------------------------------------------------------------------------
# AC-003-04：Tools / Delivery / Cancellation
# ---------------------------------------------------------------------------


class ToolsDeliveryCancellationTests(_ManagerTestCase):
    """AC-003-04：多 Callable、精确关联、pending cancellation 与迟到隔离。"""

    def _tool_frames(self, process, frame_type: str) -> list[dict]:
        return [
            record.frame
            for record in process.frames
            if record.frame["type"] == frame_type
        ]

    def test_two_callables_share_one_pid_and_correlate_independently(self) -> None:
        process = self._start()
        try:
            read = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "alpha"},
                invocation_id="inv-read",
            )
            describe = self.manager.invoke_tool(
                "example.echo",
                "echo.describe",
                {"text": "beta"},
                invocation_id="inv-describe",
            )
            self.assertEqual(read.status, ToolStatus.RESULT)
            self.assertEqual(describe.status, ToolStatus.RESULT)
            self.assertEqual(read.invocation_id, "inv-read")
            self.assertEqual(describe.invocation_id, "inv-describe")
            self.assertNotEqual(read.callable_id, describe.callable_id)
            self.assertEqual(read.callable_id, "echo.read")
            self.assertEqual(describe.callable_id, "echo.describe")
            self.assertEqual(dict(read.result or {}), {"text": "alpha"})
            describe_result = dict(describe.result or {})
            self.assertEqual(describe_result.get("callableId"), "echo.describe")
            self.assertEqual(
                describe_result.get("operations"),
                ["echo.read", "echo.describe", "echo.wait"],
            )
            self.assertGreater(process.pid or 0, 0)

            invokes = {
                frame["payload"]["invocationId"]: frame
                for frame in self._tool_frames(process, "tools.invoke")
            }
            self.assertEqual(set(invokes), {"inv-read", "inv-describe"})
            self.assertEqual(invokes["inv-read"]["payload"]["callableId"], "echo.read")
            self.assertEqual(
                invokes["inv-describe"]["payload"]["callableId"], "echo.describe"
            )
            results_by_correlation = {
                frame["correlationId"]: frame
                for frame in self._tool_frames(process, "tools.result")
            }
            for invocation_id, invoke_frame in invokes.items():
                result_frame = results_by_correlation[invoke_frame["messageId"]]
                self.assertEqual(
                    result_frame["payload"]["invocationId"], invocation_id
                )
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_delivery_correlates_response_obligation(self) -> None:
        process = self._start()
        try:
            outcome = self.manager.dispatch_delivery(
                "example.echo",
                response_obligation_id="obl-A",
                response_channel_id="ch-A",
                event_type="echo.request",
                body={"text": "bye"},
                status_code=200,
                headers={"content-type": "application/json"},
                delivery_id="del-A",
            )
            self.assertEqual(outcome.status, "delivered")
            self.assertEqual(outcome.delivery_id, "del-A")
            self.assertEqual(outcome.response_obligation_id, "obl-A")
            self.assertEqual(outcome.status_code, 200)
            terminal = process.delivery_terminal("obl-A")
            self.assertIsNotNone(terminal)
            assert terminal is not None
            self.assertEqual(terminal.status, "delivered")

            dispatch_frames = [
                frame
                for frame in self._tool_frames(process, "delivery.dispatch")
                if frame["payload"]["deliveryId"] == "del-A"
            ]
            self.assertEqual(len(dispatch_frames), 1)
            self.assertEqual(
                dispatch_frames[0]["payload"]["responseObligationId"], "obl-A"
            )
            self.assertEqual(
                dispatch_frames[0]["payload"]["responseChannelId"], "ch-A"
            )
            result_frames = [
                frame
                for frame in self._tool_frames(process, "delivery.result")
                if frame["correlationId"] == dispatch_frames[0]["messageId"]
            ]
            self.assertEqual(len(result_frames), 1)
            self.assertEqual(result_frames[0]["payload"]["deliveryId"], "del-A")
        finally:
            self.manager.stop("example.echo")

    def test_wrong_delivery_id_does_not_mark_delivered(self) -> None:
        package = self._new_package(args=["serve", "--fault=wrong-delivery-id"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.dispatch_delivery(
                "example.echo",
                response_obligation_id="obl-bogus",
                response_channel_id="ch-A",
                event_type="echo.request",
                body={"text": "bye"},
                delivery_id="del-expected",
                timeout=0.6,
            )
            self.assertEqual(outcome.status, "unknown")
            terminal = process.delivery_terminal("obl-bogus")
            self.assertIsNotNone(terminal)
            assert terminal is not None
            self.assertNotEqual(terminal.status, "delivered")
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_pending_cancellation_and_late_result(self) -> None:
        process = self._start()
        try:
            waiting = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "hold", "emitLateResult": True},
                invocation_id="inv-wait",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            self.assertFalse(waiting.done())

            cancelled = self.manager.cancel_operation("example.echo", "inv-wait")
            self.assertIsInstance(cancelled, CancelledOutcome)
            self.assertEqual(cancelled.disposition, "cancelled")
            self.assertEqual(cancelled.target_operation_id, "inv-wait")

            cancel_frames = [
                frame
                for frame in self._tool_frames(process, "host.cancel")
                if frame["payload"]["targetOperationId"] == "inv-wait"
            ]
            self.assertEqual(len(cancel_frames), 1)
            self.assertEqual(cancelled.cancel_message_id, cancel_frames[0]["messageId"])
            cancelled_frames = [
                frame
                for frame in self._tool_frames(process, "plugin.cancelled")
                if frame["payload"]["targetOperationId"] == "inv-wait"
            ]
            self.assertEqual(len(cancelled_frames), 1)
            self.assertEqual(
                cancelled_frames[0]["correlationId"], cancel_frames[0]["messageId"]
            )
            self.assertEqual(cancelled_frames[0]["payload"]["disposition"], "cancelled")

            tool_outcome = waiting.wait(3.0)
            self.assertEqual(tool_outcome.status, ToolStatus.CANCELLED)
            self.assertIsNone(tool_outcome.result)
            self.assertIsNotNone(tool_outcome.cancellation)

            invoke_frame = next(
                frame
                for frame in self._tool_frames(process, "tools.invoke")
                if frame["payload"]["invocationId"] == "inv-wait"
            )
            self.assertTrue(
                process.wait_for(
                    lambda p: any(
                        record.frame["type"] == "tools.result"
                        and record.frame["correlationId"] == invoke_frame["messageId"]
                        for record in p.frames
                    ),
                    3.0,
                ),
                "late tools.result was not observed",
            )
            terminal = process.tool_terminal("inv-wait")
            assert terminal is not None
            self.assertEqual(terminal.status, ToolStatus.CANCELLED)
            self.assertIsNone(terminal.result)
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_late_result_does_not_complete_other_request(self) -> None:
        process = self._start()
        try:
            first = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "first", "emitLateResult": True},
                invocation_id="inv-first",
            )
            second = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "second", "emitLateResult": False},
                invocation_id="inv-second",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 2, 3.0))

            self.manager.cancel_operation("example.echo", "inv-first")
            first_outcome = first.wait(3.0)
            self.assertEqual(first_outcome.status, ToolStatus.CANCELLED)

            self.assertTrue(
                process.wait_for(
                    lambda p: any(
                        record.frame["type"] == "tools.result"
                        and record.frame["payload"].get("invocationId") == "inv-first"
                        for record in p.frames
                    ),
                    3.0,
                )
            )
            self.assertFalse(second.done(), "late result completed the other request")
            self.assertEqual(process.pending_count, 1)

            self.manager.cancel_operation("example.echo", "inv-second")
            second_outcome = second.wait(3.0)
            self.assertEqual(second_outcome.status, ToolStatus.CANCELLED)
            self.assertIsNone(second_outcome.result)
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")

    def test_too_late_keeps_original_terminal(self) -> None:
        process = self._start()
        try:
            result = self.manager.invoke_tool(
                "example.echo",
                "echo.read",
                {"text": "hello"},
                invocation_id="inv1",
            )
            self.assertEqual(result.status, ToolStatus.RESULT)
            cancelled = self.manager.cancel_operation("example.echo", "inv1")
            self.assertEqual(cancelled.disposition, "too_late")
            terminal = process.tool_terminal("inv1")
            assert terminal is not None
            self.assertEqual(terminal.status, ToolStatus.RESULT)
            self.assertEqual(dict(terminal.result or {}), {"text": "hello"})
            self.assertEqual(process.pending_count, 0)
        finally:
            self.manager.stop("example.echo")


# ---------------------------------------------------------------------------
# P1-01：cancellation too_late / unsupported 不得终结原 Tool 操作
# ---------------------------------------------------------------------------


class CancellationOrderingTests(_ManagerTestCase):
    """P1-01：取消回复与原操作终态分离。"""

    def _cancel_before_result(self, fault: str, disposition: str) -> None:
        package = self._new_package(args=["serve", f"--fault={fault}"])
        process = self.manager.start(package)
        try:
            waiting = self.manager.invoke_tool_async(
                "example.echo",
                "echo.read",
                {"text": "completed-before-cancel"},
                invocation_id="inv-ordered",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            cancelled = self.manager.cancel_operation("example.echo", "inv-ordered")
            self.assertEqual(cancelled.disposition, disposition)
            self.assertEqual(cancelled.target_operation_id, "inv-ordered")
            outcome = waiting.wait(5.0)
            self.assertEqual(outcome.status, ToolStatus.RESULT)
            self.assertEqual(
                dict(outcome.result or {}),
                {"text": "completed-before-cancel"},
            )
            terminal = process.tool_terminal("inv-ordered")
            assert terminal is not None
            self.assertEqual(terminal.status, ToolStatus.RESULT)
            self.assertEqual(process.pending_count, 0)
            cancel_frames = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "plugin.cancelled"
            ]
            self.assertEqual(len(cancel_frames), 1)
            self.assertEqual(
                cancel_frames[0]["payload"]["disposition"], disposition
            )
        finally:
            self.manager.stop("example.echo")

    def test_too_late_before_original_result_keeps_pending_and_accepts_result(self) -> None:
        self._cancel_before_result("cancel-too-late-late-result", "too_late")

    def test_unsupported_before_original_result_keeps_pending_and_accepts_result(self) -> None:
        self._cancel_before_result("cancel-unsupported-late-result", "unsupported")


# ---------------------------------------------------------------------------
# P1-02：请求超时必须终止进程、注销 Extension 并收敛其他 pending
# ---------------------------------------------------------------------------


class RequestTimeoutLifecycleTests(_ManagerTestCase):
    """P1-02：所有请求超时路径都不得让 Plugin 继续 READY。"""

    def test_delivery_timeout_terminates_process(self) -> None:
        package = self._new_package(args=["serve", "--fault=wrong-delivery-id"])
        process = self.manager.start(package)
        try:
            outcome = self.manager.dispatch_delivery(
                "example.echo",
                response_obligation_id="obl-timeout",
                response_channel_id="ch-A",
                event_type="echo.request",
                body={"text": "bye"},
                delivery_id="del-timeout",
                timeout=0.6,
            )
            self.assertEqual(outcome.status, "unknown")
            self.assertEqual(process.delivery_dispatches, 1)
            self.assertEqual(process.state, PluginState.NOT_READY)
            self.assertEqual(process.extensions, frozenset())
            self.assertEqual(process.pending_count, 0)
            self.assertTrue(process.wait_for_exit(10.0))
            terminal = process.delivery_terminal("obl-timeout")
            assert terminal is not None
            self.assertEqual(terminal.status, "unknown")
        finally:
            self.manager.stop("example.echo")

    def test_cancel_timeout_terminates_process_and_aborts_tool(self) -> None:
        package = self._new_package(args=["serve", "--fault=cancel-no-reply"])
        process = self.manager.start(package)
        try:
            waiting = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "hold"},
                invocation_id="inv-cancel-timeout",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            with self.assertRaises(PluginError) as caught:
                self.manager.cancel_operation(
                    "example.echo", "inv-cancel-timeout", timeout=0.4
                )
            self.assertEqual(caught.exception.code, PluginErrorCode.IPC_TIMEOUT)
            self.assertEqual(process.state, PluginState.NOT_READY)
            self.assertEqual(process.extensions, frozenset())
            self.assertEqual(process.pending_count, 0)
            outcome = waiting.wait(3.0)
            self.assertEqual(outcome.status, ToolStatus.UNKNOWN)
            self.assertTrue(process.wait_for_exit(10.0))
        finally:
            self.manager.stop("example.echo")

    def test_timeout_aborts_other_pending_and_does_not_retry(self) -> None:
        package = self._new_package(args=["serve", "--fault=unknown-correlation-id"])
        process = self.manager.start(package)
        try:
            blocked = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "still-held"},
                invocation_id="inv-blocked",
            )
            timed_out = self.manager.invoke_tool_async(
                "example.echo",
                "echo.read",
                {"text": "no-correlation"},
                invocation_id="inv-timeout",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 2, 3.0))
            first = timed_out.wait(2.0)
            self.assertEqual(first.status, ToolStatus.TIMEOUT)
            second = blocked.wait(3.0)
            self.assertEqual(second.status, ToolStatus.UNKNOWN)
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.state, PluginState.NOT_READY)
            self.assertEqual(process.extensions, frozenset())
            self.assertEqual(process.tool_dispatches, 2)
            dispatches = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "tools.invoke"
            ]
            self.assertEqual(len(dispatches), 2)
        finally:
            self.manager.stop("example.echo")


# ---------------------------------------------------------------------------
# P1-03：PendingRegistry 身份唯一
# ---------------------------------------------------------------------------


class PendingRegistryTests(unittest.TestCase):
    """P1-03：注册冲突原子拒绝，清理不误删其他请求索引。"""

    def _request(self, kind: str, operation_id: str) -> PendingRequest:
        return PendingRequest(
            kind=kind, message_id=f"m-{operation_id}", operation_id=operation_id
        )

    def test_duplicate_correlation_id_rejected(self) -> None:
        registry = PendingRegistry()
        registry.register("c1", self._request("tools", "inv-1"))
        with self.assertRaises(PluginError):
            registry.register("c1", self._request("tools", "inv-2"))
        self.assertEqual(len(registry), 1)
        self.assertEqual(registry.operation_ids(), frozenset({("tools", "inv-1")}))

    def test_duplicate_operation_identity_rejected(self) -> None:
        registry = PendingRegistry()
        registry.register("c1", self._request("tools", "inv-1"))
        with self.assertRaises(PluginError):
            registry.register("c2", self._request("tools", "inv-1"))
        self.assertEqual(len(registry), 1)
        original = registry.pop_operation("inv-1", "tools")
        assert original is not None
        self.assertEqual(original.message_id, "m-inv-1")

        # 同一 kind 下的 deliveryId 也必须唯一，不能覆盖已有 delivery 索引。
        registry.register("d1", self._request("delivery", "del-1"))
        with self.assertRaises(PluginError):
            registry.register("d2", self._request("delivery", "del-1"))
        self.assertEqual(len(registry), 1)
        delivery = registry.pop_operation("del-1", "delivery")
        assert delivery is not None
        self.assertEqual(delivery.message_id, "m-del-1")

    def test_same_operation_id_across_kinds_is_distinct(self) -> None:
        registry = PendingRegistry()
        registry.register("c1", self._request("tools", "inv-1"))
        registry.register("c2", self._request("cancel", "inv-1"))
        self.assertEqual(len(registry), 2)
        self.assertIsNotNone(registry.pop_operation("inv-1", "cancel"))
        self.assertIsNotNone(registry.pop_operation("inv-1", "tools"))

    def test_completed_request_does_not_remove_new_index(self) -> None:
        registry = PendingRegistry()
        first = self._request("tools", "inv-reused")
        registry.register("c1", first)
        self.assertIsNotNone(registry.pop_matching("c1", "tools"))
        second = PendingRequest(
            kind="tools", message_id="m-second", operation_id="inv-reused"
        )
        registry.register("c2", second)
        self.assertIsNone(registry.pop_matching("c1", "tools"))
        self.assertEqual(len(registry), 1)
        found = registry.pop_operation("inv-reused", "tools")
        assert found is not None
        self.assertEqual(found.message_id, "m-second")

    def test_manager_rejects_duplicate_invocation_id(self) -> None:
        host = support.FakeHost()
        manager = PluginManager(host, timeouts=_timeouts())
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        package = support.copy_package(tmp / "example.echo")
        process = manager.start(package)
        try:
            manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "first"},
                invocation_id="inv-unique",
            )
            with self.assertRaises(PluginError) as caught:
                manager.invoke_tool_async(
                    "example.echo",
                    "echo.wait",
                    {"text": "second"},
                    invocation_id="inv-unique",
                )
            self.assertEqual(caught.exception.code, PluginErrorCode.INVALID_ARGUMENT)
            self.assertEqual(process.pending_count, 1)
            cancelled = manager.cancel_operation("example.echo", "inv-unique")
            self.assertEqual(cancelled.target_operation_id, "inv-unique")
        finally:
            manager.shutdown_all()


# ---------------------------------------------------------------------------
# P1-04：shutdown 确认关联与 inFlightCount 校验
# ---------------------------------------------------------------------------


class ShutdownConfirmationTests(_ManagerTestCase):
    """P1-04：plugin.stopped 必须关联 host.shutdown 且 payload 合法。"""

    def _stop_with_fault(self, fault: str, expected_diagnostic: str) -> None:
        package = self._new_package(args=["serve", f"--fault={fault}"])
        process = self.manager.start(package)
        self.manager.stop("example.echo")
        self.assertEqual(process.state, PluginState.STOPPED)
        self.assertEqual(process.extensions, frozenset())
        self.assertEqual(process.pending_count, 0)
        self.assertGreaterEqual(process.protocol_violations, 1)
        self.assertTrue(
            any(expected_diagnostic in line for line in process.diagnostics),
            process.diagnostics,
        )
        self.assertTrue(process.wait_for_exit(10.0))

    def test_wrong_shutdown_correlation_rejected(self) -> None:
        self._stop_with_fault(
            "shutdown-wrong-correlation", "SHUTDOWN_CORRELATION_MISMATCH"
        )

    def test_bool_inflight_count_rejected(self) -> None:
        self._stop_with_fault("shutdown-bad-inflight", "SHUTDOWN_INFLIGHT_INVALID")

    def test_negative_inflight_count_rejected(self) -> None:
        self._stop_with_fault(
            "shutdown-negative-inflight", "SHUTDOWN_INFLIGHT_INVALID"
        )

    def test_duplicate_stopped_rejected(self) -> None:
        self._stop_with_fault("shutdown-duplicate", "SHUTDOWN_DUPLICATE")

    def test_nonzero_inflight_does_not_fake_success(self) -> None:
        process = self._start()
        try:
            waiting = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "pending-at-shutdown"},
                invocation_id="inv-shutdown",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            self.manager.stop("example.echo")
            stopped = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "plugin.stopped"
            ]
            self.assertEqual(len(stopped), 1)
            self.assertEqual(stopped[0]["payload"], {"inFlightCount": 1})
            self.assertEqual(process.shutdown_in_flight, 1)
            outcome = waiting.wait(3.0)
            self.assertEqual(outcome.status, ToolStatus.UNKNOWN)
            self.assertIsNone(outcome.result)
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.state, PluginState.STOPPED)
        finally:
            self.manager.stop("example.echo")

    # -- P2-04：inFlightCount 语义边界 ---------------------------------------

    def test_normal_shutdown_reports_no_divergence(self) -> None:
        process = self._start()
        try:
            self.manager.stop("example.echo")
            self.assertEqual(process.shutdown_in_flight, 0)
            self.assertFalse(process.shutdown_in_flight_divergent)
            self.assertFalse(
                any(
                    "SHUTDOWN_INFLIGHT_DIVERGENCE" in line
                    for line in process.diagnostics
                ),
                process.diagnostics,
            )
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.protocol_violations, 0)
        finally:
            self.manager.stop("example.echo")

    def test_reported_zero_while_host_pending_stays_unknown(self) -> None:
        """Plugin 自报 0 不能被当作 Host 待决操作的终态依据。"""
        package = self._new_package(args=["serve", "--fault=shutdown-zero-inflight"])
        process = self.manager.start(package)
        try:
            waiting = self.manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "pending-with-zero-report"},
                invocation_id="inv-zero-report",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            self.manager.stop("example.echo")
            stopped = [
                record.frame
                for record in process.frames
                if record.frame["type"] == "plugin.stopped"
            ]
            self.assertEqual(len(stopped), 1)
            self.assertEqual(stopped[0]["payload"], {"inFlightCount": 0})
            self.assertEqual(process.shutdown_in_flight, 0)
            self.assertTrue(process.shutdown_in_flight_divergent)
            self.assertTrue(
                any(
                    "SHUTDOWN_INFLIGHT_DIVERGENCE plugin=0 host=1" in line
                    for line in process.diagnostics
                ),
                process.diagnostics,
            )
            # 自报计数不一致只是诊断，不升级为协议违规。
            self.assertEqual(process.protocol_violations, 0)
            outcome = waiting.wait(3.0)
            self.assertEqual(outcome.status, ToolStatus.UNKNOWN)
            self.assertIsNone(outcome.result)
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.state, PluginState.STOPPED)
        finally:
            self.manager.stop("example.echo")

    def test_reported_excess_without_host_pending_is_diagnostic_only(self) -> None:
        package = self._new_package(args=["serve", "--fault=shutdown-excess-inflight"])
        process = self.manager.start(package)
        try:
            self.manager.stop("example.echo")
            self.assertEqual(process.shutdown_in_flight, 1)
            self.assertTrue(process.shutdown_in_flight_divergent)
            self.assertEqual(process.protocol_violations, 0)
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.state, PluginState.STOPPED)
        finally:
            self.manager.stop("example.echo")

    def test_shutdown_timeout_keeps_unconfirmed_operations_unknown(self) -> None:
        package = self._new_package(args=["serve", "--fault=shutdown-no-reply"])
        manager = self._fresh_manager(shutdown=0.4)
        process = manager.start(package)
        try:
            waiting = manager.invoke_tool_async(
                "example.echo",
                "echo.wait",
                {"text": "pending-at-timeout"},
                invocation_id="inv-timeout-unknown",
            )
            self.assertTrue(process.wait_for(lambda p: p.pending_count == 1, 3.0))
            manager.stop("example.echo")
            outcome = waiting.wait(3.0)
            self.assertEqual(outcome.status, ToolStatus.UNKNOWN)
            self.assertEqual(process.pending_count, 0)
            self.assertEqual(process.state, PluginState.STOPPED)
        finally:
            manager.shutdown_all()

    def test_shutdown_timeout_still_reliably_terminates(self) -> None:
        package = self._new_package(args=["serve", "--fault=shutdown-no-reply"])
        manager = self._fresh_manager(shutdown=0.4)
        process = manager.start(package)
        try:
            started = time.monotonic()
            manager.stop("example.echo")
            elapsed = time.monotonic() - started
            self.assertGreaterEqual(elapsed, 0.3)
            self.assertEqual(process.state, PluginState.STOPPED)
            self.assertEqual(process.extensions, frozenset())
            self.assertEqual(process.pending_count, 0)
            self.assertTrue(process.wait_for_exit(10.0))
            assert process._proc is not None
            self.assertIsNotNone(process._proc.poll())
        finally:
            manager.shutdown_all()


# ---------------------------------------------------------------------------
# P1-05：启动失败不遗留子进程
# ---------------------------------------------------------------------------


class StartupRollbackTests(_ManagerTestCase):
    """P1-05：Popen 前完成消息构造；Popen 后异常必须回收进程。"""

    def test_non_json_config_fails_before_popen(self) -> None:
        with mock.patch(
            "ca_agent_next.plugins.manager.subprocess.Popen"
        ) as popen:
            with self.assertRaises(PluginError) as caught:
                self.manager.start(self.package, config={"bad": object()})
            popen.assert_not_called()
        self.assertEqual(caught.exception.code, PluginErrorCode.INVALID_ARGUMENT)
        self.assertEqual(self.manager.plugin_ids(), ())
        self.assertEqual(self.manager.extensions("example.echo"), frozenset())

    def test_post_popen_failure_terminates_process(self) -> None:
        captured: dict[str, PluginProcess] = {}

        def boom(process: PluginProcess, *args: object, **kwargs: object) -> None:
            captured["process"] = process
            raise RuntimeError("boom")

        with mock.patch.object(PluginProcess, "_write_outbound", boom):
            with self.assertRaises(PluginError) as caught:
                self.manager.start(self.package)
        self.assertEqual(caught.exception.code, PluginErrorCode.PROCESS_START_FAILED)
        # P2-03：启动失败的对象不得继续作为有效的 Manager-owned Process 注册。
        self.assertIsNone(self.manager.process("example.echo"))
        self.assertEqual(self.manager.plugin_ids(), ())
        process = captured["process"]
        self.assertEqual(process.state, PluginState.NOT_READY)
        self.assertEqual(process.extensions, frozenset())
        self.assertEqual(process.pending_count, 0)
        self.assertTrue(process.wait_for_exit(10.0))
        assert process._proc is not None
        self.assertIsNotNone(process._proc.poll())

    def test_start_failure_does_not_leave_registration(self) -> None:
        with mock.patch.object(
            PluginProcess, "_write_outbound", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(PluginError):
                self.manager.start(self.package)
        self.assertEqual(self.manager.plugin_ids(), ())
        self.assertIsNone(self.manager.process("example.echo"))
        self.assertEqual(self.manager.total_tool_dispatches, 0)

    def test_same_plugin_id_can_be_restarted_after_failure(self) -> None:
        with mock.patch.object(
            PluginProcess, "_write_outbound", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(PluginError):
                self.manager.start(self.package)
        self.assertEqual(self.manager.plugin_ids(), ())

        process = self.manager.start(self.package)
        try:
            self.assertEqual(self.manager.plugin_ids(), ("example.echo",))
            self.assertIs(self.manager.process("example.echo"), process)
            self.assertEqual(
                process.extensions,
                frozenset({"event.ingress", "event.delivery", "tools"}),
            )
            outcome = self.manager.invoke_tool(
                "example.echo", "echo.read", {"text": "after-restart"}
            )
            self.assertEqual(outcome.status, ToolStatus.RESULT)
        finally:
            self.manager.stop("example.echo")
        self.assertEqual(process.state, PluginState.STOPPED)

    def test_start_failure_does_not_affect_other_plugins(self) -> None:
        host = support.FakeHost()
        manager = PluginManager(host, timeouts=self.timeouts)
        driver = _FakeToolsDriver("driver.healthy")
        manager.register_driver(driver)
        try:
            with mock.patch.object(
                PluginProcess, "_write_outbound", side_effect=RuntimeError("boom")
            ):
                with self.assertRaises(PluginError):
                    manager.start(self.package)
            self.assertEqual(manager.plugin_ids(), ("driver.healthy",))
            self.assertIs(manager.driver("driver.healthy"), driver)
            self.assertTrue(driver.started)
            self.assertEqual(driver.state, "READY")
            self.assertIsNone(manager.process("example.echo"))
        finally:
            manager.shutdown_all()
        self.assertTrue(driver.closed)


# ---------------------------------------------------------------------------
# P1-06 / P1-A：Provider v2 Driver 契约边界（SR-003 只固定 Manager 面向的缝）
# ---------------------------------------------------------------------------

_PROVIDER_V2_ONLY_DTO_NAMES = (
    "ProviderLimits",
    "ProviderBinding",
    "ProviderPackageDescriptor",
    "ProviderInitializeResult",
    "ProviderCatalogEntry",
    "ProviderCatalogResult",
    "ProviderInvocation",
    "ProviderCancelResult",
)


class _FakeInvocation:
    def __init__(self, invocation_id: str, callable_id: str) -> None:
        self.invocation_id = invocation_id
        self.callable_id = callable_id
        self._outcome = ToolOutcome(
            invocation_id=invocation_id,
            callable_id=callable_id,
            status=ToolStatus.RESULT,
            result={"driver": True},
        )

    def done(self) -> bool:
        return True

    def wait(self, timeout: float | None = None) -> ToolOutcome:
        return self._outcome


class _FakeToolsDriver(ToolsExtensionDriver):
    def __init__(
        self,
        plugin_id: str = "driver.tools",
        *,
        fail_start: bool = False,
        protocol: str = DriverProtocol.NATIVE_PLUGIN.value,
    ) -> None:
        self._plugin_id = plugin_id
        self._fail_start = fail_start
        self._protocol = protocol
        self._state = "CONFIGURED"
        self.started = False
        self.closed = False

    @property
    def plugin_id(self) -> str:
        return self._plugin_id

    @property
    def protocol(self) -> str:
        return self._protocol

    @property
    def extensions(self) -> frozenset[str]:
        if self._state != "READY":
            return frozenset()
        return frozenset({"tools", "event.delivery"})

    @property
    def state(self) -> str:
        return self._state

    @property
    def pending_count(self) -> int:
        return 0

    def start(self) -> None:
        if self._fail_start:
            raise RuntimeError("driver start failed")
        self.started = True
        self._state = "READY"

    def invoke_tool_async(
        self,
        callable_id: str,
        arguments,
        *,
        invocation_id: str,
        timeout: float,
    ):
        return _FakeInvocation(invocation_id, callable_id)

    def dispatch_delivery(self, **kwargs) -> DeliveryOutcome:
        return DeliveryOutcome(
            delivery_id=kwargs["delivery_id"],
            response_obligation_id=kwargs["response_obligation_id"],
            status="delivered",
        )

    def cancel_operation(
        self, invocation_id: str, *, reason: str, timeout: float
    ) -> CancelledOutcome:
        return CancelledOutcome(
            target_operation_id=invocation_id,
            disposition="cancelled",
            cancel_message_id="driver-cancel",
            correlation_id="driver-cancel",
        )

    def close(self) -> None:
        self.closed = True
        self._state = "STOPPED"


class DriverBoundaryTests(unittest.TestCase):
    """P1-06 / P1-A：唯一 Manager 内的稳定 Driver 缝；不冻结 Provider v2 DTO。"""

    def test_provider_driver_is_an_extension_point_not_a_wire_contract(self) -> None:
        self.assertEqual(PROVIDER_V2_PROTOCOL, "ca-client-tools.provider/v2")
        self.assertTrue(
            issubclass(ProviderV2ToolsExtensionDriver, ToolsExtensionDriver)
        )
        # SR-003 不声明 Provider v2 专用操作：抽象方法集合只等于通用缝减去
        # 本类固定实现的 protocol/extensions。
        self.assertEqual(
            ProviderV2ToolsExtensionDriver.__abstractmethods__,
            ToolsExtensionDriver.__abstractmethods__ - {"protocol", "extensions"},
        )
        self.assertNotIn("initialize", ToolsExtensionDriver.__dict__)
        self.assertNotIn("catalog", ToolsExtensionDriver.__dict__)
        with self.assertRaises(TypeError):
            ProviderV2ToolsExtensionDriver()  # type: ignore[abstract]

    def test_provider_driver_pins_protocol_and_tool_extension(self) -> None:
        class _Probe(ProviderV2ToolsExtensionDriver):
            plugin_id = "probe.provider"  # type: ignore[assignment]
            state = "READY"  # type: ignore[assignment]
            pending_count = 0  # type: ignore[assignment]

            def start(self) -> None: ...
            def invoke_tool_async(self, *a, **k): ...  # type: ignore[override]
            def dispatch_delivery(self, **k): ...  # type: ignore[override]
            def cancel_operation(self, *a, **k): ...  # type: ignore[override]
            def close(self) -> None: ...

        probe = _Probe()
        self.assertEqual(probe.protocol, PROVIDER_V2_PROTOCOL)
        self.assertEqual(probe.extensions, frozenset({"tools"}))

    def test_public_driver_surface_has_no_provider_v2_wire_dtos(self) -> None:
        for name in _PROVIDER_V2_ONLY_DTO_NAMES:
            self.assertNotIn(name, driver_module.__all__)
            self.assertFalse(hasattr(driver_module, name), name)
        self.assertEqual(
            tuple(driver_module.__all__),
            (
                "PROVIDER_V2_PROTOCOL",
                "DriverProtocol",
                "ToolInvocationHandle",
                "ToolsExtensionDriver",
                "ProviderV2ToolsExtensionDriver",
            ),
        )

    def test_manager_does_not_reference_provider_v2_dtos(self) -> None:
        source = inspect.getsource(manager_module)
        for name in _PROVIDER_V2_ONLY_DTO_NAMES:
            self.assertNotIn(name, source)
        # Manager 的公共导出同样不含 Provider v2 私有 DTO。
        self.assertNotIn("ProviderPackageDescriptor", manager_module.__dict__)

    def test_manager_dispatches_through_generic_driver_only(self) -> None:
        """缺少 SR-010 字段不影响 SR-003：通用 Driver 即可完成全部调用。"""
        host = support.FakeHost()
        manager = PluginManager(host, timeouts=_timeouts())
        driver = _FakeToolsDriver("driver.generic")
        manager.register_driver(driver)
        try:
            self.assertTrue(driver.started)
            self.assertIn("driver.generic", manager.plugin_ids())
            self.assertEqual(
                manager.extensions("driver.generic"),
                frozenset({"tools", "event.delivery"}),
            )
            outcome = manager.invoke_tool("driver.generic", "anything", {"x": 1})
            self.assertEqual(outcome.status, ToolStatus.RESULT)
            cancelled = manager.cancel_operation("driver.generic", "inv-driver")
            self.assertEqual(cancelled.disposition, "cancelled")
            delivery = manager.dispatch_delivery(
                "driver.generic",
                response_obligation_id="obl-d",
                response_channel_id="ch-d",
                event_type="driver.event",
                body={},
            )
            self.assertEqual(delivery.status, "delivered")
            with self.assertRaises(PluginError):
                manager.register_driver(_FakeToolsDriver("driver.generic"))
        finally:
            manager.shutdown_all()
        self.assertTrue(driver.closed)

    def test_driver_start_failure_rolls_back_registration(self) -> None:
        host = support.FakeHost()
        manager = PluginManager(host, timeouts=_timeouts())
        driver = _FakeToolsDriver("driver.broken", fail_start=True)
        with self.assertRaises(RuntimeError):
            manager.register_driver(driver)
        self.assertIsNone(manager.driver("driver.broken"))
        self.assertNotIn("driver.broken", manager.plugin_ids())
        self.assertTrue(driver.closed)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
