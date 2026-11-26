"""A 批：Python test Host + examples/echo/plugin 真实 Go 子进程。

Negative cases are injected here, by the test end:
  * inbound mutation rewrites/duplicates frames emitted by the example plugin;
  * outbound mutation rewrites a frame the Host sends to the plugin.
The Go example has no test-only modes and is reused unchanged by every case.
"""

from __future__ import annotations

import copy
import json
import os
import platform
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from .common import CaseResult, EVIDENCE, FIXTURES, Redactor, Transcript, rel, write_json, write_text

API_VERSION = "connectionagent.io/plugin-ipc/v1alpha1"
MANIFEST_EXTENSIONS = ["event.ingress", "event.delivery", "tools"]
KNOWN_TYPES = {
    "host.initialize",
    "plugin.ready",
    "ingress.event",
    "ingress.ack",
    "tools.invoke",
    "tools.result",
    "delivery.dispatch",
    "delivery.result",
    "host.cancel",
    "plugin.cancelled",
    "host.shutdown",
    "plugin.stopped",
}
TOP_LEVEL = {"apiVersion", "messageId", "correlationId", "type", "payload"}
REPLIES = {"plugin.ready", "tools.result", "delivery.result", "plugin.cancelled", "plugin.stopped"}
UNSOLICITED = {"ingress.event"}
FLOW_SKIP = {"plugin.ready", "ingress.event", "host.initialize", "host.shutdown"}


class ProtocolError(RuntimeError):
    pass


class Fixture:
    def __init__(self, path: Path) -> None:
        self.frames = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(self.frames) != 12:
            raise SystemExit(f"fixture must have 12 frames, got {len(self.frames)}")
        self.by_type = {frame["type"]: frame for frame in self.frames}
        if len(self.by_type) != 12:
            raise SystemExit("fixture frame types are not unique")

    def payload(self, message_type: str) -> dict[str, Any]:
        return copy.deepcopy(self.by_type[message_type]["payload"])

    def frame(self, message_type: str) -> dict[str, Any]:
        return copy.deepcopy(self.by_type[message_type])


def _get_path(value: Any, path: list[str]) -> Any:
    cursor = value
    for key in path:
        cursor = cursor[key]
    return cursor


def _set_path(value: Any, path: list[str], replacement: Any) -> None:
    cursor = value
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement


class Mutator:
    """Applies one-shot inbound/outbound frame mutations from a negative fixture."""

    def __init__(self, spec: dict[str, Any] | None) -> None:
        self.spec = spec or {}
        self.inbound = copy.deepcopy(self.spec.get("inbound", []))
        self.outbound = copy.deepcopy(self.spec.get("outbound", []))
        self._applied: set[int] = set()

    def _apply_rules(self, frame: dict[str, Any], rules: list[dict[str, Any]], direction: str) -> list[dict[str, Any]]:
        produced = [copy.deepcopy(frame)]
        for index, rule in enumerate(rules):
            key = (direction, index)
            if key in self._applied:
                continue
            if rule.get("matchType") != frame["type"]:
                continue
            if "messageId" in rule and frame.get("messageId") != rule["messageId"]:
                continue
            self._applied.add(key)
            action = rule["action"]
            if action == "set":
                target = copy.deepcopy(produced[0])
                _set_path(target, rule["path"], copy.deepcopy(rule["value"]))
                produced[0] = target
            elif action == "remove_array_item":
                target = copy.deepcopy(produced[0])
                array = _get_path(target, rule["path"])
                array.remove(rule["value"])
                produced[0] = target
            elif action == "duplicate":
                duplicate = copy.deepcopy(produced[0])
                duplicate["messageId"] = rule["secondMessageId"]
                produced.append(duplicate)
            else:
                raise ProtocolError(f"unknown mutation action {action!r}")
        return produced

    def inbound_frames(self, frame: dict[str, Any]) -> list[dict[str, Any]]:
        return self._apply_rules(frame, self.inbound, "inbound")

    def outbound_frame(self, frame: dict[str, Any]) -> dict[str, Any]:
        return self._apply_rules(frame, self.outbound, "outbound")[0]

    def describe(self) -> str:
        if not self.spec:
            return "none (§5.1 exact frames)"
        parts = []
        for direction in ("inbound", "outbound"):
            for rule in self.spec.get(direction, []):
                parts.append(f"{direction}:{rule['matchType']}:{rule['action']}")
        return ", ".join(parts)


class Host:
    def __init__(self, executable: Path, case: str, directory: Path, fixture: Fixture, spec: dict[str, Any] | None) -> None:
        self.executable = executable
        self.case = case
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.fixture = fixture
        self.mutator = Mutator(spec)
        self.spec = spec or {}
        self.redactor = Redactor()
        self.transcript = Transcript(directory / "transcript.ndjson", self.redactor)
        self.proc: subprocess.Popen[str] | None = None
        self.incoming: queue.Queue[str | None] = queue.Queue()
        self.deferred: list[dict[str, Any]] = []
        self.stderr_lines: list[str] = []
        self._stderr_lock = threading.Lock()
        self.sent_ids: set[str] = set()
        self.seen_ids: set[str] = set()
        self.pending: dict[str, dict[str, Any]] = {}
        self.completions = 0
        self.duplicate_terminal = 0
        self.obligations: dict[str, str] = {}
        self.violations: list[str] = []
        self.frames: list[dict[str, Any]] = []
        self.unexpected: list[dict[str, Any]] = []

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [str(self.executable), "serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=str(self.directory),
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        self.transcript.event(
            {"kind": "process", "event": "started", "pid": self.proc.pid, "argv": [str(self.executable), "serve"], "case": self.case}
        )

    def _read_stdout(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            self.incoming.put(line)
        self.incoming.put(None)

    def _read_stderr(self) -> None:
        assert self.proc and self.proc.stderr
        for line in self.proc.stderr:
            text = line.rstrip("\n")
            with self._stderr_lock:
                self.stderr_lines.append(text)
            self.transcript.event({"kind": "stderr", "text": text})

    def send(self, frame: dict[str, Any]) -> None:
        assert self.proc and self.proc.stdin
        frame = self.mutator.outbound_frame(frame)
        message_id = frame["messageId"]
        if message_id in self.sent_ids:
            raise ProtocolError(f"host attempted duplicate outgoing messageId {message_id}")
        self.sent_ids.add(message_id)
        if frame["type"] in {"tools.invoke", "delivery.dispatch"}:
            self.pending[message_id] = {"type": frame["type"], "operation": self._operation_id(frame)}
        if frame["type"] == "delivery.dispatch":
            self.obligations[self.fixture.payload("delivery.dispatch")["deliveryId"]] = "pending"
        line = json.dumps(frame, ensure_ascii=False, separators=(",", ":")) + "\n"
        self.transcript.frame("HOST->PLUGIN", frame)
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    @staticmethod
    def _operation_id(frame: dict[str, Any]) -> str:
        payload = frame["payload"]
        return str(payload.get("invocationId") or payload.get("deliveryId") or payload.get("eventId") or "")

    def _envelope(self, frame: Any) -> dict[str, Any]:
        if not isinstance(frame, dict):
            raise ProtocolError("frame is not an object")
        unknown = set(frame) - TOP_LEVEL
        if unknown:
            raise ProtocolError(f"unknown top-level fields {sorted(unknown)}")
        if frame.get("apiVersion") != API_VERSION:
            raise ProtocolError(f"bad apiVersion {frame.get('apiVersion')!r}")
        for key in ("messageId", "type", "payload"):
            if key not in frame:
                raise ProtocolError(f"missing {key}")
        if not isinstance(frame["messageId"], str) or not frame["messageId"]:
            raise ProtocolError("messageId must be a non-empty string")
        if frame["type"] not in KNOWN_TYPES:
            raise ProtocolError(f"unknown type {frame['type']!r}")
        if frame["type"] in REPLIES and not frame.get("correlationId"):
            raise ProtocolError(f"{frame['type']} missing correlationId")
        if frame["type"] in UNSOLICITED and frame.get("correlationId") is not None:
            raise ProtocolError("ingress.event must not carry correlationId")
        if not isinstance(frame["payload"], dict):
            raise ProtocolError("payload must be an object")
        if frame["type"] == "ingress.ack":
            allowed = {"eventId", "disposition", "error"}
            extra = set(frame["payload"]) - allowed
            if extra:
                raise ProtocolError(f"ingress.ack carries forbidden fields {sorted(extra)}")
        return frame

    def _accept(self, frame: dict[str, Any]) -> dict[str, Any]:
        frame = self._envelope(frame)
        if frame["messageId"] in self.seen_ids:
            self.violations.append(f"duplicate_incoming_message_id:{frame['messageId']}")
            self.transcript.event({"kind": "violation", "code": "DUPLICATE_MESSAGE_ID", "messageId": frame["messageId"]})
            raise ProtocolError(f"duplicate incoming messageId {frame['messageId']}")
        self.seen_ids.add(frame["messageId"])
        self.frames.append(frame)
        self.transcript.frame("PLUGIN->HOST", frame)
        return frame

    def receive(self, timeout: float = 3.0) -> dict[str, Any]:
        if self.deferred:
            return self._accept(self.deferred.pop(0))
        assert self.proc is not None
        try:
            line = self.incoming.get(timeout=timeout)
        except queue.Empty:
            raise ProtocolError(f"timeout waiting for plugin frame ({timeout}s)") from None
        if line is None:
            raise ProtocolError("plugin stdout closed")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProtocolError(f"invalid JSON from plugin: {exc}") from exc
        mutated = self.mutator.inbound_frames(raw)
        self.deferred.extend(mutated[1:])
        return self._accept(mutated[0])

    def wait_for(self, message_type: str, correlation_id: str | None = None, timeout: float = 3.0) -> dict[str, Any]:
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise ProtocolError(f"timeout waiting for {message_type}")
            frame = self.receive(remaining)
            if frame["type"] == message_type and (correlation_id is None or frame.get("correlationId") == correlation_id):
                return frame
            self.unexpected.append(frame)

    def wait_stderr(self, needle: str, timeout: float = 3.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._stderr_lock:
                if any(needle in line for line in self.stderr_lines):
                    return True
            time.sleep(0.02)
        return False

    def wait_exit(self, timeout: float = 5.0) -> int | None:
        assert self.proc is not None
        try:
            return self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            self.proc.stdin.close()  # type: ignore[union-attr]
        except Exception:
            pass
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)

    def stderr_text(self) -> str:
        with self._stderr_lock:
            return "\n".join(self.stderr_lines) + ("\n" if self.stderr_lines else "")

    def complete(self, reply: dict[str, Any], operation_id: str) -> None:
        correlation = reply.get("correlationId")
        if correlation not in self.pending:
            if correlation in self.sent_ids:
                self.duplicate_terminal += 1
                self.violations.append(f"terminal_reply_for_completed_request:{correlation}")
                self.transcript.event({"kind": "violation", "code": "DUPLICATE_TERMINAL", "correlationId": correlation})
                raise ProtocolError(f"duplicate terminal reply for {correlation}")
            self.violations.append(f"unknown_correlation:{correlation}")
            self.transcript.event({"kind": "violation", "code": "UNKNOWN_CORRELATION", "correlationId": correlation})
            raise ProtocolError(f"unknown correlationId {correlation}")
        expected = self.pending[correlation]["operation"]
        if expected and operation_id != expected:
            self.violations.append(f"wrong_operation_id:{operation_id}!={expected}")
            self.transcript.event(
                {"kind": "violation", "code": "WRONG_OPERATION_ID", "correlationId": correlation, "expected": expected, "actual": operation_id}
            )
            raise ProtocolError(f"operation identity mismatch {operation_id} != {expected}")
        del self.pending[correlation]
        self.completions += 1
        self.transcript.event({"kind": "completion", "correlationId": correlation, "operationId": operation_id})

    def validate_ready(self, frame: dict[str, Any]) -> bool:
        payload = frame["payload"]
        exact = (
            payload.get("pluginId") == "example.echo"
            and payload.get("pluginVersion") == "1.0.0"
            and payload.get("ipcVersion") == API_VERSION
        )
        extensions = payload.get("extensions")
        exact_ext = (
            isinstance(extensions, list)
            and all(isinstance(item, str) for item in extensions)
            and len(extensions) == len(set(extensions))
            and set(extensions) == set(MANIFEST_EXTENSIONS)
        )
        return exact and exact_ext

    def validate_event(self, frame: dict[str, Any]) -> None:
        if frame["payload"] != self.fixture.payload("ingress.event"):
            raise ProtocolError(f"ingress.event payload differs from §5.1: {frame['payload']}")
        if frame.get("messageId") != "m3":
            raise ProtocolError(f"ingress.event messageId {frame.get('messageId')} != m3")

    def validate_result(self, frame: dict[str, Any]) -> None:
        payload = frame["payload"]
        if payload.get("invocationId") != "inv1" or payload.get("result") != {"text": "hello"} or "error" in payload:
            raise ProtocolError(f"tools.result payload invalid: {payload}")

    def validate_delivery_result(self, frame: dict[str, Any]) -> str:
        payload = frame["payload"]
        if payload.get("deliveryId") != "del1" or payload.get("disposition") != "delivered" or payload.get("statusCode") != 200:
            raise ProtocolError(f"delivery.result payload invalid: {payload}")
        if self.obligations.get("del1") != "pending":
            raise ProtocolError("obligation del1 was not pending")
        self.obligations["del1"] = "delivered"
        return "delivered"

    def validate_cancelled(self, frame: dict[str, Any]) -> None:
        payload = frame["payload"]
        if payload.get("targetOperationId") != "inv1" or payload.get("disposition") != "too_late":
            raise ProtocolError(f"plugin.cancelled payload invalid: {payload}")

    def validate_stopped(self, frame: dict[str, Any]) -> None:
        if frame["payload"].get("inFlightCount") != 0:
            raise ProtocolError(f"plugin.stopped payload invalid: {frame['payload']}")

    def prime_handshake(self, send_ack: bool = True) -> None:
        self.send(self.fixture.frame("host.initialize"))
        self.wait_for("plugin.ready", "m1")
        self.wait_for("ingress.event")
        if send_ack:
            self.send(self.fixture.frame("ingress.ack"))
            if not self.wait_stderr("ACK_ACCEPTED"):
                raise ProtocolError("plugin did not accept ingress.ack")


def _case_dir(case: str) -> Path:
    path = EVIDENCE / "batchA" / case
    path.mkdir(parents=True, exist_ok=True)
    return path


def _result(case: str, processes: str, mutation: str, expected: str) -> CaseResult:
    directory = _case_dir(case)
    return CaseResult(
        case_id=case,
        processes=processes,
        input_mutation=mutation,
        expected=expected,
        evidence=[rel(directory / "transcript.ndjson")],
    )


def _finish(host: Host, directory: Path, result: CaseResult, actual: str, status: str, notes: str = "") -> CaseResult:
    write_text(directory / "plugin.stderr.log", host.stderr_text(), host.redactor)
    write_text(directory / "host.log", "\n".join(host.violations) + ("\n" if host.violations else ""), host.redactor)
    host.stop()
    write_json(
        directory / "summary.json",
        {
            "case": result.case_id,
            "status": status,
            "actual": actual,
            "violations": host.violations,
            "completions": host.completions,
            "duplicateTerminal": host.duplicate_terminal,
            "pending": host.pending,
            "obligations": host.obligations,
            "frames": len(host.frames),
            "stderr": host.stderr_text(),
        },
        host.redactor,
    )
    result.actual = actual
    result.status = status
    result.notes = notes
    return result


PROCESSES = f"Python {platform.python_version()} test Host <-> examples/echo/plugin Go Echo Plugin 1.0.0"


def _spec(name: str) -> dict[str, Any]:
    path = FIXTURES / "negative" / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"negative fixture missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def case_fixture_check(fixture: Fixture) -> CaseResult:
    directory = _case_dir("A00-fixture")
    expected_types = [
        "host.initialize",
        "plugin.ready",
        "ingress.event",
        "ingress.ack",
        "tools.invoke",
        "tools.result",
        "delivery.dispatch",
        "delivery.result",
        "host.cancel",
        "plugin.cancelled",
        "host.shutdown",
        "plugin.stopped",
    ]
    actual_types = [frame["type"] for frame in fixture.frames]
    ok = actual_types == expected_types and all(frame["apiVersion"] == API_VERSION for frame in fixture.frames)
    write_json(directory / "summary.json", {"case": "A00-fixture", "status": "PASS" if ok else "FAIL", "frameTypes": actual_types})
    result = CaseResult(
        "A00-fixture",
        PROCESSES,
        "parse §5.1 fenced JSONL block",
        "12 frames in request/reply order with the documented message types",
        evidence=[rel(directory / "summary.json")],
    )
    result.actual = f"{len(fixture.frames)} frames, types={'ok' if ok else 'mismatch'}"
    result.status = "PASS" if ok else "FAIL"
    result.notes = "fixture check only; never counted as a real-process PASS"
    return result


def case_normal(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A01-echo-12-frames"
    directory = _case_dir(case)
    result = _result(case, PROCESSES, "none (§5.1 exact frames)", "real two-process round trip with all 12 frames and exact correlations")
    host = Host(executable, case, directory, fixture, None)
    host.start()
    try:
        host.send(fixture.frame("host.initialize"))
        ready = host.wait_for("plugin.ready", "m1")
        if not host.validate_ready(ready):
            raise ProtocolError(f"plugin.ready does not match Manifest: {ready['payload']}")
        registry = len(MANIFEST_EXTENSIONS)
        event = host.wait_for("ingress.event")
        host.validate_event(event)
        host.send(fixture.frame("ingress.ack"))
        if not host.wait_stderr("ACK_ACCEPTED"):
            raise ProtocolError("plugin did not accept ingress.ack")
        host.send(fixture.frame("tools.invoke"))
        host.complete(host.wait_for("tools.result", "m5"), "inv1")
        host.send(fixture.frame("delivery.dispatch"))
        host.complete(host.wait_for("delivery.result", "m7"), "del1")
        delivery_state = host.validate_delivery_result(host.frames[-1])
        host.send(fixture.frame("host.cancel"))
        host.validate_cancelled(host.wait_for("plugin.cancelled", "m9"))
        host.send(fixture.frame("host.shutdown"))
        host.validate_stopped(host.wait_for("plugin.stopped", "m11"))
        exit_code = host.wait_exit(5)
        if exit_code != 0:
            raise ProtocolError(f"plugin exit code {exit_code}")
        expected_plugin_frames = [fixture.frames[index] for index in (1, 2, 5, 7, 9, 11)]
        if [frame["type"] for frame in host.frames] != [frame["type"] for frame in expected_plugin_frames]:
            raise ProtocolError(f"plugin frame order/type mismatch: {[f['type'] for f in host.frames]}")
        for index, (expected, actual) in enumerate(zip(expected_plugin_frames, host.frames), start=1):
            if expected != actual:
                raise ProtocolError(f"plugin frame {index} differs from §5.1 fixture:\n expected={expected}\n actual={actual}")
        actual = (
            f"12/12 frames match §5.1; registry={registry} extensions; completions={host.completions}; "
            f"delivery={delivery_state}; exit={exit_code}"
        )
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_ready_missing_extension(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A02-ready-missing-extension"
    directory = _case_dir(case)
    spec = _spec("A02-ready-missing-extension")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.send(fixture.frame("host.initialize"))
        ready = host.wait_for("plugin.ready", "m1")
        reported = ready["payload"].get("extensions")
        registry = len(MANIFEST_EXTENSIONS) if host.validate_ready(ready) else 0
        if registry != 0:
            raise ProtocolError(f"partial registration accepted: {reported}")
        exact = [frame for frame in fixture.frames if frame["type"] == "plugin.ready"][0]
        if ready["payload"]["extensions"] == exact["payload"]["extensions"]:
            raise ProtocolError("inbound mutation was not applied")
        actual = f"reported extensions={reported}; registered_extensions={registry}; handshake=rejected"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_duplicate_message_id(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A03-duplicate-messageid"
    directory = _case_dir(case)
    spec = _spec("A03-duplicate-messageid")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.prime_handshake()
        host.send(fixture.frame("tools.invoke"))
        try:
            host.receive(2.0)
            raise ProtocolError("host accepted the duplicate-messageId reply")
        except ProtocolError as exc:
            if "duplicate incoming messageId" not in str(exc):
                raise
        pending = sum(1 for item in host.pending.values() if item["type"] == "tools.invoke")
        if pending != 1 or host.completions != 0:
            raise ProtocolError(f"invoke completed incorrectly: pending={pending} completions={host.completions}")
        actual = f"duplicate rejected; pending_invoke={pending}; completions={host.completions}"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_unknown_correlation(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A04-unknown-correlation"
    directory = _case_dir(case)
    spec = _spec("A04-unknown-correlation")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.prime_handshake()
        host.send(fixture.frame("tools.invoke"))
        try:
            host.complete(host.receive(2.0), "inv1")
            raise ProtocolError("host accepted an unknown correlationId")
        except ProtocolError as exc:
            if "unknown correlationId" not in str(exc):
                raise
        pending = sum(1 for item in host.pending.values() if item["type"] == "tools.invoke")
        if pending != 1 or host.completions != 0:
            raise ProtocolError(f"invoke completed incorrectly: pending={pending} completions={host.completions}")
        actual = f"unknown correlation rejected; pending_invoke={pending}; completions={host.completions}"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_wrong_invocation(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A05-wrong-invocation"
    directory = _case_dir(case)
    spec = _spec("A05-wrong-invocation")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.prime_handshake()
        host.send(fixture.frame("tools.invoke"))
        try:
            host.complete(host.receive(2.0), "invX")
            raise ProtocolError("host completed a mismatched invocationId")
        except ProtocolError as exc:
            if "operation identity mismatch" not in str(exc):
                raise
        pending = sum(1 for item in host.pending.values() if item["type"] == "tools.invoke")
        if pending != 1 or host.completions != 0:
            raise ProtocolError(f"invoke completed incorrectly: pending={pending} completions={host.completions}")
        actual = f"wrong invocationId rejected; pending_invoke={pending}; completions={host.completions}"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_ack_run_id(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A06-ack-runid"
    directory = _case_dir(case)
    spec = _spec("A06-ack-runid")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.send(fixture.frame("host.initialize"))
        host.wait_for("plugin.ready", "m1")
        host.wait_for("ingress.event")
        host.send(fixture.frame("ingress.ack"))
        if not host.wait_stderr("PROTOCOL_VIOLATION", 3.0):
            raise ProtocolError("plugin did not report a protocol violation")
        if not host.wait_stderr("field_or_id=runId", 2.0):
            raise ProtocolError("violation did not identify runId")
        exit_code = host.wait_exit(3)
        actual = f"plugin stderr PROTOCOL_VIOLATION field=runId; exit={exit_code}"
        return _finish(host, directory, result, actual, "PASS" if exit_code == 2 else "FAIL")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_delivery_wrong_id(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A07-delivery-wrong-id"
    directory = _case_dir(case)
    spec = _spec("A07-delivery-wrong-id")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.prime_handshake()
        host.send(fixture.frame("tools.invoke"))
        host.complete(host.wait_for("tools.result", "m5"), "inv1")
        host.send(fixture.frame("delivery.dispatch"))
        try:
            host.complete(host.receive(2.0), "delX")
            raise ProtocolError("host accepted a wrong deliveryId")
        except ProtocolError as exc:
            if "operation identity mismatch" not in str(exc):
                raise
        state = host.obligations.get("del1")
        if state == "delivered":
            raise ProtocolError("obligation del1 was incorrectly marked delivered")
        actual = f"wrong deliveryId rejected; obligation del1={state}; delivered_count=0"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def case_terminal_twice(fixture: Fixture, executable: Path) -> CaseResult:
    case = "A08-terminal-twice"
    directory = _case_dir(case)
    spec = _spec("A08-terminal-twice")
    result = _result(case, PROCESSES, spec["description"], spec["expected"])
    host = Host(executable, case, directory, fixture, spec)
    host.start()
    try:
        host.prime_handshake()
        host.send(fixture.frame("tools.invoke"))
        host.complete(host.wait_for("tools.result", "m5"), "inv1")
        try:
            host.complete(host.receive(2.0), "inv1")
            raise ProtocolError("host counted the second terminal reply as a completion")
        except ProtocolError as exc:
            if "duplicate terminal reply" not in str(exc):
                raise
        if host.completions != 1 or host.duplicate_terminal != 1:
            raise ProtocolError(f"completions={host.completions} duplicate_terminal={host.duplicate_terminal}")
        host.send(fixture.frame("host.shutdown"))
        host.wait_for("plugin.stopped", "m11")
        exit_code = host.wait_exit(5)
        actual = f"completions=1; duplicate_terminal=1; exit={exit_code}"
        return _finish(host, directory, result, actual, "PASS")
    except Exception as exc:  # noqa: BLE001
        return _finish(host, directory, result, f"FAIL: {exc}", "FAIL")


def run(executable: Path) -> list[CaseResult]:
    fixture = Fixture(FIXTURES / "echo-12-frames.jsonl")
    results = [case_fixture_check(fixture)]
    for function in (
        case_normal,
        case_ready_missing_extension,
        case_duplicate_message_id,
        case_unknown_correlation,
        case_wrong_invocation,
        case_ack_run_id,
        case_delivery_wrong_id,
        case_terminal_twice,
    ):
        results.append(function(fixture, executable))
    return results
