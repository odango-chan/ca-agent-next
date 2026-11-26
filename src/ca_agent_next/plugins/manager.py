"""唯一 Plugin Manager：包加载、子进程生命周期、IPC 与 Extension 分发。

Manager 是 SR-003 的唯一 Plugin 入口。它注入既有 F01 ``Host``，Event 只能
经由 ``Host.handle_event(Event) -> HostResult`` 进入 Agent Core；Manager 不
创建第二个 Host、AgentLoop、ModelClient、Provider Manager、Tool Registry 或
Codec Manager，也不承担 Skill 选择、Callable Scope 授权或 Owner Outcome
判断。

公开门面：:

    PluginManager(host, *, timeouts=None, config=None)
    PluginManager.start(manifest_path) -> PluginProcess
    PluginManager.invoke_tool(plugin_id, callable_id, arguments, ...) -> ToolOutcome
    PluginManager.invoke_tool_async(...) -> ToolInvocation
    PluginManager.dispatch_delivery(plugin_id, ...) -> DeliveryOutcome
    PluginManager.cancel_operation(plugin_id, invocation_id, ...) -> CancelledOutcome
    PluginManager.stop(plugin_id) / PluginManager.shutdown_all()

进程状态机：CONFIGURED → STARTING → READY / NOT_READY → STOPPING → STOPPED。

设计依据：SR-003 §2～§5；F03 §3～§10；Plugin IPC v1alpha1 §4～§5。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Mapping
from concurrent.futures import Future, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..contracts import Event, HostError, is_json_value
from .errors import PluginError, PluginErrorCode
from .ipc import Frame, PendingRequest, PendingRegistry, encode_frame, parse_frame
from .manifest import IPC_API_VERSION, PluginManifest, load_manifest, validate_instance

__all__ = [
    "PluginManager",
    "PluginProcess",
    "PluginState",
    "PluginTimeouts",
    "ToolStatus",
    "ToolOutcome",
    "ToolInvocation",
    "DeliveryOutcome",
    "CancelledOutcome",
    "IngressRecord",
    "FrameRecord",
]

_LOG = logging.getLogger("ca_agent_next.plugins")


class PluginState(str, Enum):
    CONFIGURED = "CONFIGURED"
    STARTING = "STARTING"
    READY = "READY"
    NOT_READY = "NOT_READY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ToolStatus(str, Enum):
    RESULT = "result"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ABORTED = "aborted"


_DELIVERY_DISPOSITIONS = frozenset({"delivered", "failed", "unknown"})
_CANCEL_DISPOSITIONS = frozenset({"cancelled", "too_late", "unsupported"})
_ACK_DISPOSITIONS = frozenset(
    {"accepted", "duplicate_attached", "conflict", "rejected"}
)


@dataclass(frozen=True)
class PluginTimeouts:
    """集中配置的超时值；测试可注入较短的值。"""

    start: float = 10.0
    request: float = 10.0
    cancel: float = 5.0
    shutdown: float = 5.0
    terminate: float = 3.0
    grace_ms: int = 1000


@dataclass(frozen=True)
class CancelledOutcome:
    target_operation_id: str
    disposition: str
    cancel_message_id: str
    correlation_id: str


@dataclass(frozen=True)
class ToolOutcome:
    invocation_id: str
    callable_id: str
    status: ToolStatus
    result: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None
    message_id: str | None = None
    cancellation: CancelledOutcome | None = None


@dataclass(frozen=True)
class DeliveryOutcome:
    delivery_id: str
    response_obligation_id: str
    status: str
    status_code: int | None = None
    message_id: str | None = None
    error: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class IngressRecord:
    message_id: str
    disposition: str
    event: Event | None
    ack_payload: Mapping[str, Any]
    host_called: bool
    error_code: str | None = None


@dataclass(frozen=True)
class FrameRecord:
    direction: str
    frame: Mapping[str, Any]


def _non_blank_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _payload_keys(payload: Mapping[str, Any]) -> frozenset[str]:
    return frozenset(key for key in payload if isinstance(key, str))


class PluginProcess:
    """一个已加载 Manifest 的 Plugin 子进程及其 Extension 注册状态。"""

    def __init__(
        self,
        manifest: PluginManifest,
        host: Any,
        timeouts: PluginTimeouts,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        self._manifest = manifest
        self._host = host
        self._timeouts = timeouts
        self._config = dict(config or {})
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._state = PluginState.CONFIGURED
        self._extensions: frozenset[str] = frozenset()
        self._proc: subprocess.Popen[bytes] | None = None
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._pending = PendingRegistry()
        self._seq = 0
        self._handshake_done = False
        self._handshake_error: PluginError | None = None
        self._initialize_message_id: str | None = None
        self._write_closed = False
        self._eof = False
        self._ready_event = threading.Event()
        self._stopped_event = threading.Event()
        self._exited_event = threading.Event()
        self._diagnostics: deque[str] = deque(maxlen=200)
        self._frames: list[FrameRecord] = []
        self._ingress_records: list[IngressRecord] = []
        self._inbound_message_ids: set[str] = set()
        self._event_fingerprints: dict[str, tuple[str, str]] = {}
        self._tool_terminals: dict[str, ToolOutcome] = {}
        self._delivery_terminals: dict[str, DeliveryOutcome] = {}
        self._tool_dispatches = 0
        self._delivery_dispatches = 0
        self._unmatched_replies = 0
        self._duplicate_inbound = 0
        self._protocol_violations = 0

    # -- 只读视图 ----------------------------------------------------------

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    @property
    def plugin_id(self) -> str:
        return self._manifest.plugin_id

    @property
    def pid(self) -> int | None:
        proc = self._proc
        return None if proc is None else proc.pid

    @property
    def state(self) -> PluginState:
        with self._lock:
            return self._state

    @property
    def extensions(self) -> frozenset[str]:
        with self._lock:
            return self._extensions if self._state is PluginState.READY else frozenset()

    @property
    def timeouts(self) -> PluginTimeouts:
        return self._timeouts

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def frames(self) -> tuple[FrameRecord, ...]:
        with self._lock:
            return tuple(self._frames)

    @property
    def ingress_records(self) -> tuple[IngressRecord, ...]:
        with self._lock:
            return tuple(self._ingress_records)

    @property
    def diagnostics(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._diagnostics)

    @property
    def tool_dispatches(self) -> int:
        return self._tool_dispatches

    @property
    def delivery_dispatches(self) -> int:
        return self._delivery_dispatches

    @property
    def unmatched_replies(self) -> int:
        return self._unmatched_replies

    @property
    def duplicate_inbound_frames(self) -> int:
        return self._duplicate_inbound

    @property
    def protocol_violations(self) -> int:
        return self._protocol_violations

    def tool_terminal(self, invocation_id: str) -> ToolOutcome | None:
        with self._lock:
            return self._tool_terminals.get(invocation_id)

    def delivery_terminal(self, response_obligation_id: str) -> DeliveryOutcome | None:
        with self._lock:
            return self._delivery_terminals.get(response_obligation_id)

    # -- 生命周期 ----------------------------------------------------------

    def start(self) -> "PluginProcess":
        with self._lock:
            if self._state is not PluginState.CONFIGURED:
                raise PluginError(
                    PluginErrorCode.INVALID_ARGUMENT,
                    "plugin process has already been started",
                    details={"pluginId": self.plugin_id, "state": self._state.value},
                )
            self._state = PluginState.STARTING

        command = [str(self._manifest.executable_path), *self._manifest.args]
        kwargs: dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "cwd": str(self._manifest.package_root),
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self._proc = subprocess.Popen(command, **kwargs)
        except OSError as exc:
            with self._lock:
                self._state = PluginState.NOT_READY
            raise PluginError(
                PluginErrorCode.PROCESS_START_FAILED,
                "plugin process could not be started",
                details={"reason": type(exc).__name__},
            ) from None

        self._reader = threading.Thread(
            target=self._read_stdout,
            name=f"plugin-{self.plugin_id}-stdout",
            daemon=True,
        )
        self._stderr_reader = threading.Thread(
            target=self._read_stderr,
            name=f"plugin-{self.plugin_id}-stderr",
            daemon=True,
        )
        self._reader.start()
        self._stderr_reader.start()

        initialize_message_id = self._send(
            "host.initialize",
            {
                "pluginId": self._manifest.plugin_id,
                "expectedVersion": self._manifest.version,
                "ipcVersion": IPC_API_VERSION,
                "config": dict(self._config),
            },
        )
        self._initialize_message_id = initialize_message_id

        if not self._ready_event.wait(self._timeouts.start):
            self._terminate()
            with self._lock:
                self._state = PluginState.NOT_READY
                self._extensions = frozenset()
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "plugin did not complete the handshake before the startup timeout",
                details={"pluginId": self.plugin_id},
            )

        if self._handshake_error is not None:
            error = self._handshake_error
            self._terminate()
            with self._lock:
                self._state = PluginState.NOT_READY
                self._extensions = frozenset()
            raise error
        with self._lock:
            ready = self._state is PluginState.READY
        if not ready:
            # 进程在握手完成前退出（例如 startup fault）：不得视为已就绪。
            self._terminate()
            with self._lock:
                self._state = PluginState.NOT_READY
                self._extensions = frozenset()
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "plugin did not complete the handshake before the startup timeout",
                details={"pluginId": self.plugin_id},
            )
        return self

    def stop(self) -> None:
        with self._lock:
            if self._state is PluginState.STOPPED:
                return
            self._state = PluginState.STOPPING
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                self._send("host.shutdown", {"gracePeriodMs": self._timeouts.grace_ms})
            except PluginError:
                pass
            self._stopped_event.wait(self._timeouts.shutdown)
        self._terminate()
        self._finalize_exit()
        with self._lock:
            self._state = PluginState.STOPPED
            self._extensions = frozenset()

    def wait_for_exit(self, timeout: float | None = None) -> bool:
        return self._exited_event.wait(self._timeouts.terminate if timeout is None else timeout)

    def wait_for_ingress(self, count: int, timeout: float | None = None) -> bool:
        limit = self._timeouts.start if timeout is None else timeout
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            with self._lock:
                if len(self._ingress_records) >= count:
                    return True
            time.sleep(0.005)
        return False

    def wait_for(self, predicate: Callable[["PluginProcess"], bool], timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate(self):
                return True
            time.sleep(0.005)
        return False

    # -- 进程 I/O ----------------------------------------------------------

    def _read_stderr(self) -> None:
        proc = self._proc
        if proc is None or proc.stderr is None:
            return
        try:
            for raw in proc.stderr:
                line = raw.decode("utf-8", errors="replace").rstrip()
                if not line:
                    continue
                with self._lock:
                    self._diagnostics.append(line)
                _LOG.debug("plugin %s stderr: %s", self.plugin_id, line)
        except (OSError, ValueError):
            return

    def _read_stdout(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        try:
            while True:
                raw = proc.stdout.readline()
                if not raw:
                    break
                if not raw.strip():
                    continue
                try:
                    frame = parse_frame(raw)
                except PluginError as exc:
                    self._on_protocol_error(exc)
                    continue
                try:
                    self._dispatch(frame)
                except Exception:  # pragma: no cover - 防御性
                    _LOG.exception("plugin %s failed to handle frame", self.plugin_id)
        except (OSError, ValueError):
            pass
        finally:
            self._finalize_exit()

    def _on_protocol_error(self, error: PluginError) -> None:
        with self._lock:
            self._protocol_violations += 1
            self._diagnostics.append(f"PROTOCOL_VIOLATION {error.details}")
            if not self._handshake_done and self._handshake_error is None:
                self._handshake_error = error
                self._handshake_done = True
                self._ready_event.set()

    def _dispatch(self, frame: Frame) -> None:
        with self._lock:
            if frame.message_id in self._inbound_message_ids:
                self._duplicate_inbound += 1
                self._diagnostics.append(
                    f"DUPLICATE_INBOUND_MESSAGE_ID {frame.message_id} {frame.type}"
                )
                return
            self._inbound_message_ids.add(frame.message_id)
            handshake_done = self._handshake_done

        self._record_frame("plugin->host", frame.as_mapping())

        if not handshake_done and frame.type != "plugin.ready":
            self._on_protocol_error(
                PluginError(
                    PluginErrorCode.IPC_PROTOCOL_VIOLATION,
                    "plugin sent a frame before the handshake completed",
                    details={"type": frame.type},
                )
            )
            return

        if frame.type == "plugin.ready":
            self._on_ready(frame)
        elif frame.type == "ingress.event":
            self._on_ingress(frame)
        elif frame.type == "tools.result":
            self._on_tools_result(frame)
        elif frame.type == "delivery.result":
            self._on_delivery_result(frame)
        elif frame.type == "plugin.cancelled":
            self._on_cancelled(frame)
        elif frame.type == "plugin.stopped":
            self._stopped_event.set()
            self._exited_event.set()

    def _on_ready(self, frame: Frame) -> None:
        error: PluginError | None = None
        with self._lock:
            if self._handshake_done:
                self._protocol_violations += 1
                return
            self._handshake_done = True
            if frame.correlation_id != self._initialize_message_id:
                error = PluginError(
                    PluginErrorCode.HANDSHAKE_MISMATCH,
                    "plugin.ready does not correlate with host.initialize",
                )
            elif _payload_keys(frame.payload) != frozenset(
                {"pluginId", "pluginVersion", "ipcVersion", "extensions"}
            ):
                error = PluginError(
                    PluginErrorCode.HANDSHAKE_MISMATCH,
                    "plugin.ready payload does not match the handshake contract",
                )
            elif frame.payload.get("pluginId") != self._manifest.plugin_id:
                error = PluginError(
                    PluginErrorCode.HANDSHAKE_MISMATCH,
                    "plugin.ready pluginId does not match the manifest",
                )
            elif frame.payload.get("pluginVersion") != self._manifest.version:
                error = PluginError(
                    PluginErrorCode.HANDSHAKE_MISMATCH,
                    "plugin.ready pluginVersion does not match the manifest",
                )
            elif frame.payload.get("ipcVersion") != IPC_API_VERSION:
                error = PluginError(
                    PluginErrorCode.HANDSHAKE_MISMATCH,
                    "plugin.ready ipcVersion does not match the manifest",
                )
            else:
                raw_extensions = frame.payload.get("extensions")
                if not isinstance(raw_extensions, list) or not all(
                    isinstance(item, str) for item in raw_extensions
                ):
                    error = PluginError(
                        PluginErrorCode.HANDSHAKE_MISMATCH,
                        "plugin.ready extensions must be a string array",
                    )
                elif len(set(raw_extensions)) != len(raw_extensions):
                    error = PluginError(
                        PluginErrorCode.HANDSHAKE_MISMATCH,
                        "plugin.ready extensions contain duplicates",
                    )
                elif frozenset(raw_extensions) != self._manifest.extensions:
                    error = PluginError(
                        PluginErrorCode.HANDSHAKE_MISMATCH,
                        "plugin.ready extensions do not match the manifest",
                        details={
                            "declared": sorted(self._manifest.extensions),
                            "reported": sorted(raw_extensions),
                        },
                    )
                else:
                    self._extensions = frozenset(raw_extensions)
                    self._state = PluginState.READY
            if error is not None:
                self._handshake_error = error
                self._state = PluginState.NOT_READY
                self._extensions = frozenset()
                self._diagnostics.append(f"HANDSHAKE_MISMATCH {error.message}")
            self._ready_event.set()

    # -- Event ingress -----------------------------------------------------

    def _on_ingress(self, frame: Frame) -> None:
        payload = frame.payload
        event_value = payload.get("eventId")
        event_id = event_value if isinstance(event_value, str) else ""
        event, error_code, error_detail = self._validate_ingress(payload)

        if event is None:
            ack = {
                "eventId": event_id,
                "disposition": "rejected",
                "error": {
                    "code": error_code or "EVENT_REJECTED",
                    "message": error_detail or "event is invalid",
                    "retryable": False,
                },
            }
            self._try_send_ack(ack, frame.message_id)
            with self._lock:
                self._ingress_records.append(
                    IngressRecord(
                        message_id=frame.message_id,
                        disposition="rejected",
                        event=None,
                        ack_payload=ack,
                        host_called=False,
                        error_code=error_code,
                    )
                )
            return

        fingerprint = self._fingerprint(event)
        with self._lock:
            previous = self._event_fingerprints.get(event.event_id)
            if previous is not None:
                disposition = (
                    "duplicate_attached"
                    if previous[0] == fingerprint
                    else "conflict"
                )
        if previous is not None:
            if disposition == "duplicate_attached":
                ack = {"eventId": event.event_id, "disposition": disposition}
            else:
                ack = {
                    "eventId": event.event_id,
                    "disposition": disposition,
                    "error": {
                        "code": "EVENT_CONFLICT",
                        "message": "event identity conflicts with a previous event",
                        "retryable": False,
                    },
                }
            self._try_send_ack(ack, frame.message_id)
            with self._lock:
                self._ingress_records.append(
                    IngressRecord(
                        message_id=frame.message_id,
                        disposition=disposition,
                        event=event,
                        ack_payload=ack,
                        host_called=False,
                        error_code=None if disposition == "duplicate_attached" else "EVENT_CONFLICT",
                    )
                )
            return

        # 先登记指纹，保证并发重复 ingress 不会重复调用 Host。
        with self._lock:
            self._event_fingerprints[event.event_id] = (fingerprint, "accepted")

        host_called = False
        try:
            self._host.handle_event(event)
            host_called = True
            ack = {"eventId": event.event_id, "disposition": "accepted"}
            error_code = None
        except HostError as exc:
            host_called = True
            error_code = exc.code
            ack = {
                "eventId": event.event_id,
                "disposition": "rejected",
                "error": {
                    "code": exc.code,
                    "message": exc.safe_message,
                    "retryable": False,
                },
            }
        except Exception:
            host_called = True
            error_code = "HOST_ERROR"
            ack = {
                "eventId": event.event_id,
                "disposition": "rejected",
                "error": {
                    "code": "HOST_ERROR",
                    "message": "host rejected event",
                    "retryable": False,
                },
            }

        self._try_send_ack(ack, frame.message_id)
        with self._lock:
            self._ingress_records.append(
                IngressRecord(
                    message_id=frame.message_id,
                    disposition=ack["disposition"],
                    event=event,
                    ack_payload=ack,
                    host_called=host_called,
                    error_code=error_code,
                )
            )

    def _try_send_ack(self, ack: Mapping[str, Any], event_message_id: str) -> None:
        try:
            self._send("ingress.ack", ack, correlation_id=event_message_id)
        except PluginError as exc:
            with self._lock:
                self._diagnostics.append(f"ACK_NOT_SENT {exc.code}")

    def _validate_ingress(
        self, payload: Mapping[str, Any]
    ) -> tuple[Event | None, str | None, str | None]:
        allowed = {
            "eventId",
            "ingressId",
            "eventType",
            "externalRequestId",
            "responseChannelId",
            "source",
            "payload",
            "artifacts",
        }
        if _payload_keys(payload) - allowed:
            return None, "UNKNOWN_FIELD", "ingress.event payload has an unknown field"
        for required in ("eventId", "ingressId", "eventType", "source", "payload"):
            if required not in payload:
                return None, "MISSING_FIELD", f"ingress.event is missing {required}"

        event_id = payload["eventId"]
        ingress_id = payload["ingressId"]
        event_type = payload["eventType"]
        for name, value in (
            ("eventId", event_id),
            ("ingressId", ingress_id),
            ("eventType", event_type),
        ):
            if not _non_blank_str(value):
                return None, "FIELD_INVALID", f"ingress.event {name} is invalid"

        if ingress_id != self._manifest.plugin_id:
            return None, "INGRESS_ID_MISMATCH", "ingressId does not match the manifest id"
        binding = self._manifest.event_bindings.get(event_type)
        if binding is None:
            return None, "EVENT_TYPE_UNDECLARED", "eventType is not declared by the manifest"

        source = payload["source"]
        if not isinstance(source, Mapping):
            return None, "SOURCE_INVALID", "ingress.event source must be an object"
        if not is_json_value(source):
            return None, "SOURCE_INVALID", "ingress.event source is not a JSON object"
        for key in ("protocol", "peerId"):
            if not _non_blank_str(source.get(key)):
                return None, "SOURCE_INVALID", f"ingress.event source.{key} is invalid"

        artifacts = payload.get("artifacts", [])
        if not isinstance(artifacts, list):
            return None, "ARTIFACTS_INVALID", "ingress.event artifacts must be an array"
        if artifacts:
            return (
                None,
                "ARTIFACT_CHANNEL_NOT_CONFIGURED",
                "artifact staging is not part of this SR-003 slice",
            )

        body = payload["payload"]
        if not isinstance(body, Mapping):
            return None, "PAYLOAD_INVALID", "ingress.event payload must be an object"
        if not is_json_value(body):
            return None, "PAYLOAD_INVALID", "ingress.event payload is not valid JSON"
        schema_errors = validate_instance(binding.request_schema, body)
        if schema_errors:
            return (
                None,
                "PAYLOAD_SCHEMA_INVALID",
                "ingress.event payload does not match requestSchema",
            )

        external_request_id = payload.get("externalRequestId")
        response_channel_id = payload.get("responseChannelId")
        for name, value in (
            ("externalRequestId", external_request_id),
            ("responseChannelId", response_channel_id),
        ):
            if value is not None and not _non_blank_str(value):
                return None, "FIELD_INVALID", f"ingress.event {name} is invalid"

        event = Event(
            event_id=event_id,
            ingress_id=ingress_id,
            event_type=event_type,
            payload=dict(body),
            source=dict(source),
            external_request_id=external_request_id,
            response_channel_id=response_channel_id,
            artifact_refs=(),
        )
        return event, None, None

    @staticmethod
    def _fingerprint(event: Event) -> str:
        try:
            return json.dumps(
                {
                    "eventType": event.event_type,
                    "externalRequestId": event.external_request_id,
                    "responseChannelId": event.response_channel_id,
                    "source": event.source,
                    "payload": event.payload,
                },
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError):  # pragma: no cover - 已由校验排除
            return repr(event)

    # -- Tools / Delivery / Cancel 回复 ------------------------------------

    def _on_tools_result(self, frame: Frame) -> None:
        correlation_id = frame.correlation_id
        if correlation_id is None:
            return
        pending = self._pending.get(correlation_id)
        if pending is None or pending.kind != "tools":
            with self._lock:
                self._unmatched_replies += 1
            return

        payload = frame.payload
        allowed = {"invocationId", "result", "error"}
        if _payload_keys(payload) - allowed:
            return
        invocation_id = payload.get("invocationId")
        if not isinstance(invocation_id, str) or invocation_id != pending.operation_id:
            with self._lock:
                self._unmatched_replies += 1
            return
        has_result = "result" in payload
        has_error = "error" in payload
        if has_result == has_error:
            return
        if has_result and not is_json_value(payload["result"]):
            return
        if has_error:
            error = payload["error"]
            if not isinstance(error, Mapping):
                return
            if not _non_blank_str(error.get("code")) or not _non_blank_str(
                error.get("message")
            ):
                return

        pending = self._pending.pop_matching(correlation_id, "tools")
        if pending is None:
            return
        callable_id = str(pending.context.get("callableId", ""))
        if has_result:
            outcome = ToolOutcome(
                invocation_id=invocation_id,
                callable_id=callable_id,
                status=ToolStatus.RESULT,
                result=dict(payload["result"]) if isinstance(payload["result"], Mapping) else payload["result"],
                message_id=frame.message_id,
            )
        else:
            outcome = ToolOutcome(
                invocation_id=invocation_id,
                callable_id=callable_id,
                status=ToolStatus.ERROR,
                error=dict(payload["error"]),
                message_id=frame.message_id,
            )
        self._record_tool_terminal(outcome)
        if not pending.future.done():
            pending.future.set_result(outcome)

    def _on_delivery_result(self, frame: Frame) -> None:
        correlation_id = frame.correlation_id
        if correlation_id is None:
            return
        pending = self._pending.get(correlation_id)
        if pending is None or pending.kind != "delivery":
            with self._lock:
                self._unmatched_replies += 1
            return

        payload = frame.payload
        allowed = {"deliveryId", "disposition", "statusCode", "error"}
        if _payload_keys(payload) - allowed:
            return
        delivery_id = payload.get("deliveryId")
        if not isinstance(delivery_id, str) or delivery_id != pending.operation_id:
            with self._lock:
                self._unmatched_replies += 1
            return
        disposition = payload.get("disposition")
        if disposition not in _DELIVERY_DISPOSITIONS:
            return
        status_code = payload.get("statusCode")
        if status_code is not None and (
            not isinstance(status_code, int) or isinstance(status_code, bool)
        ):
            return
        error = payload.get("error")
        if error is not None and not isinstance(error, Mapping):
            return

        pending = self._pending.pop_matching(correlation_id, "delivery")
        if pending is None:
            return
        obligation_id = str(pending.context.get("responseObligationId", ""))
        outcome = DeliveryOutcome(
            delivery_id=delivery_id,
            response_obligation_id=obligation_id,
            status=disposition,
            status_code=status_code,
            message_id=frame.message_id,
            error=None if error is None else dict(error),
        )
        with self._lock:
            self._delivery_terminals.setdefault(obligation_id, outcome)
        if not pending.future.done():
            pending.future.set_result(outcome)

    def _on_cancelled(self, frame: Frame) -> None:
        correlation_id = frame.correlation_id
        if correlation_id is None:
            return
        pending = self._pending.get(correlation_id)
        if pending is None or pending.kind != "cancel":
            with self._lock:
                self._unmatched_replies += 1
            return

        payload = frame.payload
        allowed = {"targetOperationId", "disposition", "error"}
        if _payload_keys(payload) - allowed:
            return
        target = payload.get("targetOperationId")
        if not isinstance(target, str) or target != pending.operation_id:
            with self._lock:
                self._unmatched_replies += 1
            return
        disposition = payload.get("disposition")
        if disposition not in _CANCEL_DISPOSITIONS:
            return

        pending = self._pending.pop_matching(correlation_id, "cancel")
        if pending is None:
            return
        outcome = CancelledOutcome(
            target_operation_id=target,
            disposition=disposition,
            cancel_message_id=pending.message_id,
            correlation_id=correlation_id,
        )
        if not pending.future.done():
            pending.future.set_result(outcome)

        if disposition == "unsupported":
            return
        tool_pending = self._pending.pop_operation(target, "tools")
        if tool_pending is None:
            return
        cancelled = ToolOutcome(
            invocation_id=target,
            callable_id=str(tool_pending.context.get("callableId", "")),
            status=ToolStatus.CANCELLED,
            cancellation=outcome,
            message_id=frame.message_id,
        )
        self._record_tool_terminal(cancelled)
        if not tool_pending.future.done():
            tool_pending.future.set_result(cancelled)

    def _record_tool_terminal(self, outcome: ToolOutcome) -> None:
        with self._lock:
            self._tool_terminals.setdefault(outcome.invocation_id, outcome)

    # -- 出站请求 ----------------------------------------------------------

    def _next_message_id(self) -> str:
        with self._lock:
            self._seq += 1
            return f"h{self._seq}"

    def _send(
        self,
        message_type: str,
        payload: Mapping[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> str:
        message_id = self._next_message_id()
        frame = {
            "apiVersion": IPC_API_VERSION,
            "messageId": message_id,
        }
        if correlation_id is not None:
            frame["correlationId"] = correlation_id
        frame["type"] = message_type
        frame["payload"] = dict(payload)
        data = encode_frame(
            message_id, message_type, payload, correlation_id=correlation_id
        )
        with self._write_lock:
            proc = self._proc
            if proc is None or proc.poll() is not None or self._write_closed:
                raise PluginError(
                    PluginErrorCode.PROCESS_EXITED,
                    "plugin process is not accepting frames",
                )
            try:
                assert proc.stdin is not None
                proc.stdin.write(data)
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                self._write_closed = True
                raise PluginError(
                    PluginErrorCode.PROCESS_EXITED,
                    "plugin process is not accepting frames",
                ) from None
        self._record_frame("host->plugin", frame)
        return message_id

    def _record_frame(self, direction: str, frame: Mapping[str, Any]) -> None:
        with self._lock:
            self._frames.append(FrameRecord(direction=direction, frame=dict(frame)))

    def _begin_request(
        self,
        kind: str,
        operation_id: str,
        context: Mapping[str, Any] | None = None,
    ) -> PendingRequest:
        message_id = self._next_message_id()
        pending = PendingRequest(
            kind=kind,
            message_id=message_id,
            operation_id=operation_id,
            context=dict(context or {}),
        )
        self._pending.register(message_id, pending)
        return pending

    def _send_request(
        self,
        pending: PendingRequest,
        message_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        data = encode_frame(pending.message_id, message_type, payload)
        with self._write_lock:
            proc = self._proc
            if proc is None or proc.poll() is not None or self._write_closed:
                self._pending.pop_matching(pending.message_id, pending.kind)
                raise PluginError(
                    PluginErrorCode.PROCESS_EXITED,
                    "plugin process is not accepting frames",
                )
            try:
                assert proc.stdin is not None
                proc.stdin.write(data)
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                self._write_closed = True
                self._pending.pop_matching(pending.message_id, pending.kind)
                raise PluginError(
                    PluginErrorCode.PROCESS_EXITED,
                    "plugin process is not accepting frames",
                ) from None
        self._record_frame(
            "host->plugin",
            {
                "apiVersion": IPC_API_VERSION,
                "messageId": pending.message_id,
                "type": message_type,
                "payload": dict(payload),
            },
        )

    # -- 由 Manager 调用的分发操作 -----------------------------------------

    def begin_tool(
        self, callable_id: str, arguments: Mapping[str, Any], invocation_id: str, context: Mapping[str, Any] | None = None
    ) -> PendingRequest:
        pending = self._begin_request(
            "tools",
            invocation_id,
            {"callableId": callable_id, **(context or {})},
        )
        payload = {
            "invocationId": invocation_id,
            "callableId": callable_id,
            "arguments": dict(arguments),
            "invocationContext": {},
            "artifactRefs": [],
        }
        self._send_request(pending, "tools.invoke", payload)
        self._tool_dispatches += 1
        return pending

    def dispatch_delivery(
        self,
        *,
        delivery_id: str,
        response_obligation_id: str,
        response_channel_id: str,
        event_type: str,
        body: Any,
        status_code: int,
        headers: Mapping[str, str],
        timeout: float,
    ) -> DeliveryOutcome:
        pending = self._begin_request(
            "delivery",
            delivery_id,
            {"responseObligationId": response_obligation_id},
        )
        payload = {
            "deliveryId": delivery_id,
            "responseObligationId": response_obligation_id,
            "responseChannelId": response_channel_id,
            "eventType": event_type,
            "statusCode": status_code,
            "headers": dict(headers),
            "body": body,
            "artifacts": [],
        }
        self._send_request(pending, "delivery.dispatch", payload)
        self._delivery_dispatches += 1
        outcome = self._await(pending, timeout)
        if outcome is None:
            popped = self._pending.pop_matching(pending.message_id, "delivery")
            if popped is None and pending.future.done():
                return pending.future.result()
            timeout_outcome = DeliveryOutcome(
                delivery_id=delivery_id,
                response_obligation_id=response_obligation_id,
                status="unknown",
            )
            with self._lock:
                self._delivery_terminals.setdefault(
                    response_obligation_id, timeout_outcome
                )
            return timeout_outcome
        return outcome

    def cancel_operation(
        self, invocation_id: str, *, reason: str, timeout: float
    ) -> CancelledOutcome:
        pending = self._begin_request("cancel", invocation_id)
        payload = {"targetOperationId": invocation_id, "reason": reason}
        self._send_request(pending, "host.cancel", payload)
        outcome = self._await(pending, timeout)
        if outcome is None:
            popped = self._pending.pop_matching(pending.message_id, "cancel")
            if popped is None and pending.future.done():
                return pending.future.result()
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "plugin did not answer host.cancel before the timeout",
                details={"pluginId": self.plugin_id},
            )
        return outcome

    def expire(self, pending: PendingRequest) -> Future[Any] | None:
        """移除并返回超时请求的 future（已由其他路径完成时返回 None）。"""
        popped = self._pending.pop_matching(pending.message_id, pending.kind)
        if popped is None:
            return None
        return popped.future

    @staticmethod
    def _await(pending: PendingRequest, timeout: float) -> Any | None:
        try:
            return pending.future.result(timeout)
        except FutureTimeoutError:
            return None

    # -- 进程终止清理 ------------------------------------------------------

    def _terminate(self) -> None:
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            proc.wait(timeout=self._timeouts.terminate)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=self._timeouts.terminate)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=self._timeouts.terminate)
                except subprocess.TimeoutExpired:  # pragma: no cover
                    pass
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except (OSError, ValueError):
                pass

    def _finalize_exit(self) -> None:
        with self._lock:
            if self._eof:
                return
            self._eof = True
            if self._state is PluginState.STOPPING:
                self._state = PluginState.STOPPED
            elif self._state is not PluginState.STOPPED:
                self._state = PluginState.NOT_READY
            self._extensions = frozenset()
        self._abort_pending()
        self._ready_event.set()
        self._stopped_event.set()
        self._exited_event.set()

    def _abort_pending(self) -> None:
        for pending in self._pending.pop_all():
            if pending.future.done():
                continue
            if pending.kind == "tools":
                outcome = ToolOutcome(
                    invocation_id=pending.operation_id,
                    callable_id=str(pending.context.get("callableId", "")),
                    status=ToolStatus.ABORTED,
                )
                self._record_tool_terminal(outcome)
                pending.future.set_result(outcome)
            elif pending.kind == "delivery":
                pending.future.set_result(
                    DeliveryOutcome(
                        delivery_id=pending.operation_id,
                        response_obligation_id=str(
                            pending.context.get("responseObligationId", "")
                        ),
                        status="unknown",
                    )
                )
            else:
                pending.future.set_exception(
                    PluginError(
                        PluginErrorCode.PROCESS_EXITED,
                        "plugin process exited while the request was pending",
                    )
                )


class ToolInvocation:
    """一次 ``tools.invoke`` 的待决句柄。"""

    def __init__(
        self,
        process: PluginProcess,
        invocation_id: str,
        callable_id: str,
        pending: PendingRequest,
    ) -> None:
        self._process = process
        self.invocation_id = invocation_id
        self.callable_id = callable_id
        self._pending = pending

    @property
    def message_id(self) -> str:
        return self._pending.message_id

    def done(self) -> bool:
        return self._pending.future.done()

    def wait(self, timeout: float | None = None) -> ToolOutcome:
        effective = (
            self._process.timeouts.request if timeout is None else timeout
        )
        future = self._pending.future
        try:
            return future.result(effective)
        except FutureTimeoutError:
            pass
        if future.done():
            return future.result()
        expired = self._process.expire(self._pending)
        if expired is not None:
            outcome = ToolOutcome(
                invocation_id=self.invocation_id,
                callable_id=self.callable_id,
                status=ToolStatus.TIMEOUT,
            )
            self._process._record_tool_terminal(outcome)
            if not expired.done():
                expired.set_result(outcome)
            return outcome
        return future.result()


class PluginManager:
    """唯一 Plugin Manager 门面。"""

    def __init__(
        self,
        host: Any,
        *,
        timeouts: PluginTimeouts | None = None,
        config: Mapping[str, Any] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._host = host
        self._timeouts = timeouts or PluginTimeouts()
        self._config = dict(config or {})
        self._logger = logger or _LOG
        self._processes: dict[str, PluginProcess] = {}
        self._lock = threading.RLock()

    @property
    def timeouts(self) -> PluginTimeouts:
        return self._timeouts

    def start(
        self,
        manifest_path: str | os.PathLike[str],
        *,
        config: Mapping[str, Any] | None = None,
    ) -> PluginProcess:
        """校验整个 Manifest 后启动 Plugin 进程并完成握手。"""
        manifest = load_manifest(manifest_path)
        with self._lock:
            existing = self._processes.get(manifest.plugin_id)
            if existing is not None:
                raise PluginError(
                    PluginErrorCode.INVALID_ARGUMENT,
                    "plugin is already managed by this manager",
                    details={"pluginId": manifest.plugin_id},
                )
            process = PluginProcess(
                manifest,
                self._host,
                self._timeouts,
                config=self._config if config is None else config,
            )
            self._processes[manifest.plugin_id] = process
        process.start()
        return process

    def process(self, plugin_id: str) -> PluginProcess | None:
        with self._lock:
            return self._processes.get(plugin_id)

    def plugin_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._processes)

    def extensions(self, plugin_id: str) -> frozenset[str]:
        process = self.process(plugin_id)
        return frozenset() if process is None else process.extensions

    def pending_count(self, plugin_id: str) -> int:
        process = self.process(plugin_id)
        return 0 if process is None else process.pending_count

    @property
    def total_tool_dispatches(self) -> int:
        with self._lock:
            return sum(item.tool_dispatches for item in self._processes.values())

    @property
    def total_delivery_dispatches(self) -> int:
        with self._lock:
            return sum(item.delivery_dispatches for item in self._processes.values())

    def _require_ready(self, plugin_id: str) -> PluginProcess:
        process = self.process(plugin_id)
        if process is None:
            raise PluginError(
                PluginErrorCode.PLUGIN_NOT_READY,
                "plugin is not managed by this manager",
                details={"pluginId": plugin_id},
            )
        if process.state is not PluginState.READY:
            raise PluginError(
                PluginErrorCode.PLUGIN_NOT_READY,
                "plugin is not READY",
                details={"pluginId": plugin_id, "state": process.state.value},
            )
        return process

    def invoke_tool_async(
        self,
        plugin_id: str,
        callable_id: str,
        arguments: Mapping[str, Any],
        *,
        invocation_id: str | None = None,
    ) -> ToolInvocation:
        process = self._require_ready(plugin_id)
        if "tools" not in process.extensions:
            raise PluginError(
                PluginErrorCode.PLUGIN_NOT_READY,
                "plugin does not export the tools extension",
                details={"pluginId": plugin_id},
            )
        if not _non_blank_str(callable_id):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "callableId must be a non-empty string",
            )
        if not isinstance(arguments, Mapping) or not is_json_value(arguments):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "tool arguments must be a JSON object",
            )
        if invocation_id is None:
            invocation_id = uuid.uuid4().hex
        elif not _non_blank_str(invocation_id):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "invocationId must be a non-empty string",
            )
        pending = process.begin_tool(callable_id, arguments, invocation_id)
        return ToolInvocation(process, invocation_id, callable_id, pending)

    def invoke_tool(
        self,
        plugin_id: str,
        callable_id: str,
        arguments: Mapping[str, Any],
        *,
        invocation_id: str | None = None,
        timeout: float | None = None,
    ) -> ToolOutcome:
        handle = self.invoke_tool_async(
            plugin_id, callable_id, arguments, invocation_id=invocation_id
        )
        return handle.wait(timeout)

    def dispatch_delivery(
        self,
        plugin_id: str,
        *,
        response_obligation_id: str,
        response_channel_id: str,
        event_type: str,
        body: Any,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        delivery_id: str | None = None,
        timeout: float | None = None,
    ) -> DeliveryOutcome:
        process = self._require_ready(plugin_id)
        if "event.delivery" not in process.extensions:
            raise PluginError(
                PluginErrorCode.PLUGIN_NOT_READY,
                "plugin does not export the event.delivery extension",
                details={"pluginId": plugin_id},
            )
        for name, value in (
            ("responseObligationId", response_obligation_id),
            ("responseChannelId", response_channel_id),
            ("eventType", event_type),
        ):
            if not _non_blank_str(value):
                raise PluginError(
                    PluginErrorCode.INVALID_ARGUMENT,
                    f"{name} must be a non-empty string",
                )
        binding = process.manifest.response_bindings.get(event_type)
        if binding is None:
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "eventType is not declared by the event.delivery extension",
                details={"eventType": event_type},
            )
        if not is_json_value(body):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "delivery body must be a JSON value",
            )
        schema_errors = validate_instance(binding.response_schema, body)
        if schema_errors:
            raise PluginError(
                PluginErrorCode.DELIVERY_SCHEMA_INVALID,
                "delivery body does not match responseSchema",
                details={"eventType": event_type},
            )
        if not isinstance(status_code, int) or isinstance(status_code, bool):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT, "statusCode must be an integer"
            )
        if status_code < 100 or status_code > 599:
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "statusCode must be an HTTP status code",
            )
        headers_value: Mapping[str, str] = {}
        if headers is not None:
            if not isinstance(headers, Mapping):
                raise PluginError(
                    PluginErrorCode.INVALID_ARGUMENT, "headers must be an object"
                )
            for key, value in headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise PluginError(
                        PluginErrorCode.INVALID_ARGUMENT,
                        "headers must map strings to strings",
                    )
            headers_value = dict(headers)
        if delivery_id is None:
            delivery_id = uuid.uuid4().hex
        elif not _non_blank_str(delivery_id):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "deliveryId must be a non-empty string",
            )
        effective_timeout = (
            self._timeouts.request if timeout is None else timeout
        )
        return process.dispatch_delivery(
            delivery_id=delivery_id,
            response_obligation_id=response_obligation_id,
            response_channel_id=response_channel_id,
            event_type=event_type,
            body=body,
            status_code=status_code,
            headers=headers_value,
            timeout=effective_timeout,
        )

    def cancel_operation(
        self,
        plugin_id: str,
        invocation_id: str,
        *,
        reason: str = "caller_cancelled",
        timeout: float | None = None,
    ) -> CancelledOutcome:
        process = self._require_ready(plugin_id)
        if "tools" not in process.extensions:
            raise PluginError(
                PluginErrorCode.PLUGIN_NOT_READY,
                "plugin does not export the tools extension",
                details={"pluginId": plugin_id},
            )
        if not _non_blank_str(invocation_id):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT,
                "invocationId must be a non-empty string",
            )
        if not _non_blank_str(reason):
            raise PluginError(
                PluginErrorCode.INVALID_ARGUMENT, "reason must be a non-empty string"
            )
        effective_timeout = self._timeouts.cancel if timeout is None else timeout
        return process.cancel_operation(
            invocation_id, reason=reason, timeout=effective_timeout
        )

    def stop(self, plugin_id: str) -> None:
        process = self.process(plugin_id)
        if process is None:
            return
        process.stop()

    def shutdown_all(self) -> None:
        with self._lock:
            processes = list(self._processes.values())
        for process in reversed(processes):
            process.stop()
