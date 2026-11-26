"""唯一 Plugin Manager 内的 Tools Extension Driver 接口边界。

本模块只固定 SR-003 真正承诺的那条缝：**Manager 面向的通用 Driver 能力**。
它不定义 Provider v2 的 wire contract。Provider v2 的 catalog descriptor、
Effect、request/response media type、Schema、Source Pin、Artifact Slot、
绝对 RFC3339 UTC deadline、``producerInvocationId``、typed MAS 可选
``hostInvocation`` 等具体数据合同，由 SR-010 在 F03.05 设计门禁通过后定义
并实现；本 SR 不提前冻结、也不伪实现它们。

设计依据：

- ``docs/设计说明书/F03-Plugin平台/Plugin平台设计说明书.md`` §3、§5；
- ``docs/设计说明书/F03-Plugin平台/Tool Interface 与 Provider 集成设计说明书.md``
  v0.3.9 §3、§6.3～§6.4、§11.1——**目标设计；SR-015 设计移交 IMPLEMENTED，但 SR-010 仍为 DRAFT**，
  是后续 Provider 集成的目标设计输入，不是 SR-003 已冻结的实施契约；
- ``docs/SR/SR-003-统一插件管理器与扩展通信.md`` §2、§5（本 SR 只固定 Manager
  面向的 Driver 边界，真实 Provider v2 数据合同与适配归 SR-010）。

边界规则：

1. 只有一个 Plugin Manager；本接口不创建第二个 Manager、Registry 或授权路径。
2. Manager 只依赖本模块的通用 Driver 能力，不依赖任何 Provider v2 私有 DTO。
3. Driver 只做进程/协议适配；进程生命周期、超时、关闭与 pending 收敛仍由
   Manager/PluginProcess 拥有，Driver 不自行重试或伪造成功。
4. 私有 backend ID 只在 Driver 内部使用，不进入 Runtime 或模型上下文。
5. 同一 Callable 不得在两个 Driver 中注册后自动 fallback；部署只选择一个精确
   包和 Driver。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover - 仅用于类型检查，避免与 manager 循环导入
    from .manager import CancelledOutcome, DeliveryOutcome, ToolOutcome

__all__ = [
    "PROVIDER_V2_PROTOCOL",
    "DriverProtocol",
    "ToolInvocationHandle",
    "ToolsExtensionDriver",
    "ProviderV2ToolsExtensionDriver",
]

PROVIDER_V2_PROTOCOL = "ca-client-tools.provider/v2"
"""Provider v2 的精确进程协议标识（F03.05 §6.3）。

SR-003 只固定这个协议标识字符串，使部署与 Manager 能区分“要不要把这个
pluginId 当作 Provider v2 处理”。该协议的具体帧与字段由 SR-010 定义。
"""


class DriverProtocol(str, Enum):
    """部署选定的 Tools Extension 传输协议。"""

    NATIVE_PLUGIN = "connectionagent.io/plugin-ipc/v1alpha1"
    PROVIDER_V2 = PROVIDER_V2_PROTOCOL


class ToolInvocationHandle(Protocol):
    """Manager 与 Driver 共用的待决 Tool 句柄。"""

    invocation_id: str
    callable_id: str

    def done(self) -> bool: ...

    def wait(self, timeout: float | None = None) -> "ToolOutcome": ...


class ToolsExtensionDriver(ABC):
    """Tools Extension Driver 的稳定接口（SR-003 唯一承诺的 Driver 缝）。

    Manager 只依赖本接口。Native Plugin 由 ``PluginProcess`` 直接承担；
    Provider v2 由 SR-010 实现 :class:`ProviderV2ToolsExtensionDriver`。实现
    必须复用 Manager 的进程生命周期、超时和关闭语义，并返回统一的
    ``ToolOutcome`` / ``DeliveryOutcome`` / ``CancelledOutcome``。

    本接口刻意保持协议无关：它不出现 Provider v2 的 catalog descriptor、
    Effect、media type、Schema、Source Pin、Artifact Slot、绝对 deadline 等
    字段。任何 Driver 只要实现下列成员即可被同一个 Manager 管理，因此
    SR-010 补齐 Provider v2 数据合同时不需要改动本接口，也不会破坏其它
    协议的 Driver。
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
    """Provider v2 Tools Extension 的适配扩展点（具体实现归 SR-010）。

    SR-003 只承诺两件事：

    1. Provider v2 也是 :class:`ToolsExtensionDriver`，因此由**同一个**
       Plugin Manager 管理，不新增第二个 Manager、Registry 或 Provider
       生命周期入口；
    2. 协议标识固定为 :data:`PROVIDER_V2_PROTOCOL`，Extension 固定为
       ``tools``。

    本类**不再声明 Provider v2 专用的抽象方法**，因为这些方法的输入/输出
    需要 F03.05 §6.4 的完整数据合同（catalog 的 supported/unsupported 分区
    与每个 backend 的 descriptor、Effect、request/response media type、
    Schema、Source Pin、Artifact Slot、绝对 RFC3339 UTC deadline、
    ``producerInvocationId``、typed MAS 可选 ``hostInvocation`` 等），而
    F03.05 v0.3.7 的文档状态仍是“目标设计；待评审”。在 SR-003 里预先冻结
    这些字段会产生一个 SR-010 必须推翻的假契约。

    因此：Provider v2 的 wire DTO、帧编码/解析、catalog 对账、deadline 与
    artifact slot 语义由 **SR-010** 在其设计门禁完成后定义。SR-010 增加 v2
    专用成员时必须保持本类的通用 Driver 语义不变，并继续由唯一 Manager
    统一管理进程生命周期。
    """

    @property
    def protocol(self) -> str:
        return PROVIDER_V2_PROTOCOL

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({"tools"})
