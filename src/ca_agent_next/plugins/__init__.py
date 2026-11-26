"""SR-003 唯一 Plugin Manager 与 Plugin Package/IPC v1alpha1 适配。

包根 ``ca_agent_next`` 的公共导出保持 SR-002 的固定列表；Plugin 相关类型只从
本子包导出，不新增包根公共符号。
"""

from __future__ import annotations

from .errors import PluginError, PluginErrorCode
from .manifest import (
    EXTENSION_KEYS,
    IPC_API_VERSION,
    PACKAGE_API_VERSION,
    EventBinding,
    PluginManifest,
    ResponseBinding,
    load_manifest,
)
from .manager import (
    CancelledOutcome,
    DeliveryOutcome,
    FrameRecord,
    IngressRecord,
    PluginManager,
    PluginProcess,
    PluginState,
    PluginTimeouts,
    ToolInvocation,
    ToolOutcome,
    ToolStatus,
)

__all__ = [
    "PluginManager",
    "PluginProcess",
    "PluginState",
    "PluginTimeouts",
    "ToolInvocation",
    "ToolOutcome",
    "ToolStatus",
    "DeliveryOutcome",
    "CancelledOutcome",
    "IngressRecord",
    "FrameRecord",
    "PluginManifest",
    "EventBinding",
    "ResponseBinding",
    "PluginError",
    "PluginErrorCode",
    "load_manifest",
    "PACKAGE_API_VERSION",
    "IPC_API_VERSION",
    "EXTENSION_KEYS",
]
