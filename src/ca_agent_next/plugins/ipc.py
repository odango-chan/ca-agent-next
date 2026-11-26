"""Plugin IPC v1alpha1 帧编解码与请求关联原语。

本模块只做协议层工作：UTF-8 NDJSON 帧的严格解析/编码，以及按
``correlationId`` 建立的 pending request 表。它不了解 Host、Extension 或
业务语义。

设计依据：``docs/规范/插件包与进程通信协议规范.md`` §5、§5.1。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from concurrent.futures import Future
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from .errors import PluginError, PluginErrorCode
from .manifest import IPC_API_VERSION

__all__ = [
    "IPC_API_VERSION",
    "HOST_TO_PLUGIN_TYPES",
    "PLUGIN_TO_HOST_TYPES",
    "Frame",
    "PendingRequest",
    "PendingRegistry",
    "encode_frame",
    "parse_frame",
]

HOST_TO_PLUGIN_TYPES = frozenset(
    {
        "host.initialize",
        "ingress.ack",
        "tools.invoke",
        "delivery.dispatch",
        "host.cancel",
        "host.shutdown",
    }
)
PLUGIN_TO_HOST_TYPES = frozenset(
    {
        "plugin.ready",
        "ingress.event",
        "tools.result",
        "delivery.result",
        "plugin.cancelled",
        "plugin.stopped",
    }
)

_FRAME_KEYS = frozenset({"apiVersion", "messageId", "correlationId", "type", "payload"})


class _DuplicateJsonKey(ValueError):
    pass


def _hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


@dataclass(frozen=True)
class Frame:
    """一条已解析的 IPC 帧。"""

    api_version: str
    message_id: str
    type: str
    payload: Mapping[str, Any]
    correlation_id: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        frame: dict[str, Any] = {
            "apiVersion": self.api_version,
            "messageId": self.message_id,
        }
        if self.correlation_id is not None:
            frame["correlationId"] = self.correlation_id
        frame["type"] = self.type
        frame["payload"] = dict(self.payload)
        return frame


def _is_non_blank_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def parse_frame(line: bytes | str) -> Frame:
    """严格解析一帧；任何协议错误都抛出 ``IPC_PROTOCOL_VIOLATION``。"""
    if isinstance(line, bytes):
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError:
            raise _violation("frame is not valid UTF-8") from None
    else:
        text = line

    try:
        document = json.loads(
            text,
            object_pairs_hook=_hook,
            parse_constant=_reject_constant,
        )
    except _DuplicateJsonKey:
        raise _violation("frame contains duplicate JSON keys") from None
    except (json.JSONDecodeError, ValueError):
        raise _violation("frame is not valid JSON") from None

    if not isinstance(document, dict):
        raise _violation("frame root must be a JSON object")
    for key in document:
        if key not in _FRAME_KEYS:
            raise _violation("frame contains an unknown field")
    for key in ("apiVersion", "messageId", "type", "payload"):
        if key not in document:
            raise _violation("frame is missing a required field")

    api_version = document["apiVersion"]
    if api_version != IPC_API_VERSION:
        raise _violation("frame apiVersion is not supported")
    message_id = document["messageId"]
    if not _is_non_blank_str(message_id):
        raise _violation("frame messageId is invalid")
    message_type = document["type"]
    if not _is_non_blank_str(message_type):
        raise _violation("frame type is invalid")
    if message_type not in PLUGIN_TO_HOST_TYPES:
        raise _violation("frame type is not sent by a plugin")
    payload = document["payload"]
    if not isinstance(payload, dict):
        raise _violation("frame payload must be a JSON object")
    correlation_id = document.get("correlationId")
    if correlation_id is not None and not _is_non_blank_str(correlation_id):
        raise _violation("frame correlationId is invalid")

    return Frame(
        api_version=api_version,
        message_id=message_id,
        type=message_type,
        payload=payload,
        correlation_id=correlation_id,
    )


def _violation(reason: str) -> PluginError:
    return PluginError(
        PluginErrorCode.IPC_PROTOCOL_VIOLATION,
        "plugin sent a frame that violates plugin-ipc/v1alpha1",
        details={"reason": reason},
    )


def encode_frame(
    message_id: str,
    message_type: str,
    payload: Mapping[str, Any],
    *,
    correlation_id: str | None = None,
) -> bytes:
    """编码一帧 UTF-8 NDJSON，键顺序固定为规范示例顺序。"""
    frame: dict[str, Any] = {
        "apiVersion": IPC_API_VERSION,
        "messageId": message_id,
    }
    if correlation_id is not None:
        frame["correlationId"] = correlation_id
    frame["type"] = message_type
    frame["payload"] = dict(payload)
    try:
        text = json.dumps(
            frame,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        raise PluginError(
            PluginErrorCode.INVALID_ARGUMENT,
            "outbound frame payload is not JSON serializable",
        ) from None
    return text.encode("utf-8") + b"\n"


@dataclass
class PendingRequest:
    """一条等待 plugin 回复的请求。"""

    kind: str
    message_id: str
    operation_id: str
    future: Future[Any] = field(default_factory=Future)
    context: dict[str, Any] = field(default_factory=dict)


class PendingRegistry:
    """以 correlationId 为键的线程安全 pending 表。"""

    def __init__(self) -> None:
        self._lock = RLock()
        self._pending: dict[str, PendingRequest] = {}
        self._by_operation: dict[tuple[str, str], str] = {}

    def __len__(self) -> int:
        with self._lock:
            return len(self._pending)

    def register(self, correlation_id: str, request: PendingRequest) -> None:
        with self._lock:
            self._pending[correlation_id] = request
            self._by_operation[(request.kind, request.operation_id)] = correlation_id

    def pop_matching(
        self, correlation_id: str, kind: str
    ) -> PendingRequest | None:
        """仅当 correlation 与 kind 都匹配时移除并返回请求。"""
        with self._lock:
            request = self._pending.get(correlation_id)
            if request is None or request.kind != kind:
                return None
            del self._pending[correlation_id]
            self._by_operation.pop((request.kind, request.operation_id), None)
            return request

    def pop_operation(self, operation_id: str, kind: str) -> PendingRequest | None:
        with self._lock:
            correlation_id = self._by_operation.get((kind, operation_id))
            if correlation_id is None:
                return None
            request = self._pending.get(correlation_id)
            if request is None or request.kind != kind:
                return None
            del self._pending[correlation_id]
            del self._by_operation[(kind, operation_id)]
            return request

    def pop_all(self) -> list[PendingRequest]:
        with self._lock:
            requests = list(self._pending.values())
            self._pending.clear()
            self._by_operation.clear()
            return requests

    def get(self, correlation_id: str) -> PendingRequest | None:
        with self._lock:
            return self._pending.get(correlation_id)

    def operation_ids(self) -> frozenset[tuple[str, str]]:
        with self._lock:
            return frozenset(self._by_operation)
