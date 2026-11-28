"""Plugin Manager 的稳定错误类型。

每个错误都携带机器可读的 ``code`` 与安全的 ``message``。错误文本不得包含
Plugin 进程诊断原文、凭据或未净化的外部输入。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = ["PluginError", "PluginErrorCode"]


class PluginErrorCode:
    """Plugin Manager 使用的固定错误码（只作为字符串常量集合）。"""

    MANIFEST_UNREADABLE = "MANIFEST_UNREADABLE"
    MANIFEST_SYNTAX = "MANIFEST_SYNTAX"
    MANIFEST_DUPLICATE_KEY = "MANIFEST_DUPLICATE_KEY"
    MANIFEST_UNKNOWN_FIELD = "MANIFEST_UNKNOWN_FIELD"
    MANIFEST_FIELD_INVALID = "MANIFEST_FIELD_INVALID"
    MANIFEST_VERSION_UNSUPPORTED = "MANIFEST_VERSION_UNSUPPORTED"
    MANIFEST_PATH_INVALID = "MANIFEST_PATH_INVALID"
    MANIFEST_SCHEMA_INVALID = "MANIFEST_SCHEMA_INVALID"
    HANDSHAKE_MISMATCH = "HANDSHAKE_MISMATCH"
    PROCESS_START_FAILED = "PROCESS_START_FAILED"
    PROCESS_EXITED = "PROCESS_EXITED"
    PLUGIN_NOT_READY = "PLUGIN_NOT_READY"
    IPC_PROTOCOL_VIOLATION = "IPC_PROTOCOL_VIOLATION"
    IPC_TIMEOUT = "IPC_TIMEOUT"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    DELIVERY_SCHEMA_INVALID = "DELIVERY_SCHEMA_INVALID"


class PluginError(Exception):
    """Plugin Manager 的公开异常。

    ``code`` 是 :class:`PluginErrorCode` 中的常量；``details`` 只包含安全的
    结构化上下文（字段名、ID、错误种类），不包含原始异常文本或凭据。
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = dict(details or {})
        super().__init__(f"{code}: {message}")

    def __repr__(self) -> str:  # pragma: no cover - 便于诊断
        return f"PluginError(code={self.code!r}, message={self.message!r})"
