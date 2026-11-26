"""唯一 Plugin Manager 内的 Tools Extension Driver 接口边界。

本模块固定 Native Plugin 与 Provider v2 两种 Tools Extension 传输之间的稳定
边界。它只定义接口与数据合同，不启动 Provider 进程、不读取 Provider 包、不
实现 ``ca-client-tools.provider/v2`` 帧；实际 Provider v2 适配由 SR-010 按本
接口独立实现。

设计依据：

- ``docs/设计说明书/F03-Plugin平台/Plugin平台设计说明书.md`` §3、§5；
- ``docs/设计说明书/F03-Plugin平台/Tool Interface 与 Provider 集成设计说明书.md``
  §3、§6.3～§6.4、§11.1（ProviderV2 Driver 与单一 Manager 边界）；
- ``docs/SR/SR-003-统一插件管理器与扩展通信.md`` §2、§5（本 SR 只固定接口，
  真实 Provider/Channel 互操作归 SR-010）。

边界规则：

1. 只有一个 Plugin Manager；本接口不创建第二个 Manager、Registry 或授权路径。
2. Driver 只做进程/协议适配；进程生命周期、超时、关闭与 pending 收敛仍由
   Manager/PluginProcess 拥有，Driver 不自行重试或伪造成功。
3. 私有 ``backendOperationId`` 只在 Driver 内部使用，不进入 Runtime 或模型上下文。
4. 同一 Callable 不得在两个 Driver 中注册后自动 fallback；部署只选择一个精确
   包和 Driver。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover - 仅用于类型检查，避免与 manager 循环导入
    from .manager import CancelledOutcome, DeliveryOutcome, ToolOutcome

__all__ = [
    "PROVIDER_V2_PROTOCOL",
    "DriverProtocol",
    "ProviderLimits",
    "ProviderBinding",
    "ProviderPackageDescriptor",
    "ProviderInitializeResult",
    "ProviderCatalogEntry",
    "ProviderCatalogResult",
    "ProviderInvocation",
    "ProviderCancelResult",
    "ToolInvocationHandle",
    "ToolsExtensionDriver",
    "ProviderV2ToolsExtensionDriver",
]

PROVIDER_V2_PROTOCOL = "ca-client-tools.provider/v2"
"""Provider v2 的精确进程协议标识（F03.05 §6.3）。"""


class DriverProtocol(str, Enum):
    """部署选定的 Tools Extension 传输协议。"""

    NATIVE_PLUGIN = "connectionagent.io/plugin-ipc/v1alpha1"
    PROVIDER_V2 = PROVIDER_V2_PROTOCOL


@dataclass(frozen=True)
class ProviderLimits:
    """initialize 请求中的进程内 limits（F03.05 §6.4）。"""

    max_frame_bytes: int
    max_in_flight: int
    max_call_duration_ms: int


@dataclass(frozen=True)
class ProviderBinding:
    """一条已发布 Callable → Provider 私有 backend 的映射。"""

    runtime_operation_id: str
    backend_operation_id: str
    effect: str


@dataclass(frozen=True)
class ProviderPackageDescriptor:
    """SR-010 Provider Package Loader 的输出；本 SR 只固定只读形状。"""

    provider_id: str
    provider_version: str
    package_root: Path
    interface_snapshot_digest: str
    runtime_bindings_digest: str
    backend_catalog_digest: str
    bindings: tuple[ProviderBinding, ...]

    def backend_operation_ids(self) -> tuple[str, ...]:
        """返回去重且保持发布顺序的私有 backend ID 集合。"""
        seen: set[str] = set()
        ordered: list[str] = []
        for binding in self.bindings:
            if binding.backend_operation_id in seen:
                continue
            seen.add(binding.backend_operation_id)
            ordered.append(binding.backend_operation_id)
        return tuple(ordered)

    def binding_for(self, runtime_operation_id: str) -> ProviderBinding | None:
        for binding in self.bindings:
            if binding.runtime_operation_id == runtime_operation_id:
                return binding
        return None


@dataclass(frozen=True)
class ProviderInitializeResult:
    """Provider initialize 响应的已校验投影。"""

    provider_id: str
    provider_version: str
    build_digest: str
    backend_catalog_digest: str
    catalog_version: str
    max_frame_bytes: int | None = None
    max_in_flight: int | None = None
    max_call_duration_ms: int | None = None


@dataclass(frozen=True)
class ProviderCatalogEntry:
    """显式 catalog 请求中的单个 backend 结论。"""

    backend_operation_id: str
    supported: bool
    code: str | None = None


@dataclass(frozen=True)
class ProviderCatalogResult:
    """catalog 响应；supported/unsupported 必须恰好覆盖请求集合。"""

    entries: tuple[ProviderCatalogEntry, ...]
    catalog_version: str


@dataclass(frozen=True)
class ProviderInvocation:
    """Provider invoke 的协议无关输入。"""

    invocation_id: str
    backend_operation_id: str
    arguments: Mapping[str, Any]
    deadline_ms: int | None = None


@dataclass(frozen=True)
class ProviderCancelResult:
    """Provider cancel 的稳定结论（CANCEL_REQUESTED / ALREADY_COMPLETED / NOT_FOUND）。"""

    target_request_id: str
    disposition: str


class ToolInvocationHandle(Protocol):
    """Manager 与 Driver 共用的待决 Tool 句柄。"""

    invocation_id: str
    callable_id: str

    def done(self) -> bool: ...

    def wait(self, timeout: float | None = None) -> "ToolOutcome": ...


class ToolsExtensionDriver(ABC):
    """Tools Extension Driver 的稳定接口。

    Manager 只依赖本接口；Native Plugin 由 ``PluginProcess`` 直接承担，Provider
    v2 由 SR-010 实现 :class:`ProviderV2ToolsExtensionDriver`。Driver 的实现
    必须复用 Manager 的进程生命周期、超时和关闭语义，并返回统一的
    ``ToolOutcome`` / ``DeliveryOutcome`` / ``CancelledOutcome``。
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """部署内唯一的 Plugin/Provider 标识。"""

    @property
    @abstractmethod
    def protocol(self) -> str:
        """``DriverProtocol`` 中的精确协议字符串。"""

    @property
    @abstractmethod
    def extensions(self) -> frozenset[str]:
        """已完成握手并注册的 Extension 集合。"""

    @property
    @abstractmethod
    def state(self) -> str:
        """READY / NOT_READY / STOPPED 等稳定状态文本。"""

    @property
    @abstractmethod
    def pending_count(self) -> int:
        """尚未获得终态的请求数。"""

    @abstractmethod
    def start(self) -> None:
        """启动并完成握手；失败必须自行清理，不得留下运行中的孤儿进程。"""

    @abstractmethod
    def invoke_tool_async(
        self,
        callable_id: str,
        arguments: Mapping[str, Any],
        *,
        invocation_id: str,
        timeout: float,
    ) -> ToolInvocationHandle:
        """发起一次 Tools Extension 调用；callableId 与 backend ID 的映射由 Driver 内部决定。"""

    @abstractmethod
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
    ) -> "DeliveryOutcome":
        """分发一次 Delivery；Driver 不解释 Owner outcome。"""

    @abstractmethod
    def cancel_operation(
        self, invocation_id: str, *, reason: str, timeout: float
    ) -> "CancelledOutcome":
        """取消一次操作；取消不等于 Owner 回滚。"""

    @abstractmethod
    def close(self) -> None:
        """关闭进程/通道并收敛全部 pending；必须幂等。"""


class ProviderV2ToolsExtensionDriver(ToolsExtensionDriver):
    """Provider v2 Tools Extension 的接口边界（SR-010 实现）。

    实现必须按 ``ca-client-tools.provider/v2`` 消费 initialize/catalog/invoke/
    cancel，按 requestId 关联乱序响应，并由 Manager 统一管理进程生命周期。
    Provider v2 的 NDJSON 帧由 Driver 编码/解析，但进程启动、超时、关闭和
    pending 收敛必须复用本包的 Plugin Manager/PluginProcess 机制；不得在
    Driver 内另建进程管理循环、第二 Manager 或凭据入口。本 SR 不提供真实
    实现，也不改变 Native Plugin IPC。
    """

    @property
    def protocol(self) -> str:
        return PROVIDER_V2_PROTOCOL

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({"tools"})

    @property
    @abstractmethod
    def descriptor(self) -> ProviderPackageDescriptor:
        """已验证的 Provider 包描述符。"""

    @property
    @abstractmethod
    def limits(self) -> ProviderLimits:
        """initialize 使用的进程内 limits。"""

    @abstractmethod
    def initialize(
        self,
        *,
        host_instance_id: str,
        provider_instance_id: str,
        artifact_channel: Mapping[str, Any] | None = None,
    ) -> ProviderInitializeResult:
        """发送 initialize 并校验 Provider 身份/版本/catalog digest。"""

    @abstractmethod
    def catalog(
        self, backend_operation_ids: Sequence[str]
    ) -> ProviderCatalogResult:
        """对显式请求的 backend ID 做 catalog 对账。"""

    @abstractmethod
    def invoke_backend(
        self, request: ProviderInvocation, *, timeout: float
    ) -> "ToolOutcome":
        """按 requestId 关联 Provider invoke 响应。"""

    @abstractmethod
    def cancel_backend(
        self, target_request_id: str, *, timeout: float
    ) -> ProviderCancelResult:
        """发送 Provider cancel 并返回稳定结论。"""
