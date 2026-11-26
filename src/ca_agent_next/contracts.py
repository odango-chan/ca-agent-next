"""公共契约类型。

依据：SR-002 v0.2.9 §2.2 与 F01 v0.3.6 §5.1～§5.4。

HostError 只在本题定义一次；``host.py`` 只重导出该类型，不得重新定义。
本切片只使用 Python 标准库。
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TypeAlias, Union

__all__ = [
    "JSONValue",
    "Event",
    "Context",
    "Run",
    "ModelRequest",
    "ModelProposal",
    "HostResult",
    "HostError",
]

JSONValue: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    list["JSONValue"],
    Mapping[str, "JSONValue"],
]

#: HostError 唯一允许的错误码及其固定安全消息（F01 §5.4）。
HOST_ERROR_MESSAGES: Mapping[str, str] = {
    "EVENT_INVALID": "event is invalid",
    "MODEL_CLIENT_FAILED": "model client failed",
    "MODEL_PROPOSAL_INVALID": "model proposal is invalid",
    "HOST_INTERNAL_ERROR": "host internal error",
}


class HostError(Exception):
    """稳定 Host 错误。

    构造签名固定为 ``HostError(code: str, safe_message: str)``；``code`` 仅允许
    ``EVENT_INVALID``、``MODEL_CLIENT_FAILED``、``MODEL_PROPOSAL_INVALID`` 和
    ``HOST_INTERNAL_ERROR``，且 ``safe_message`` 必须是对应固定安全消息。
    ``CLI_USAGE_ERROR`` 是 CLI-only 诊断，不属于 HostError。
    """

    def __init__(self, code: str, safe_message: str) -> None:
        expected = HOST_ERROR_MESSAGES.get(code)
        if expected is None:
            raise ValueError(f"unsupported Host error code: {code!r}")
        if safe_message != expected:
            raise ValueError(f"safe message for {code} must be {expected!r}")
        self.code = code
        self.safe_message = safe_message
        super().__init__(safe_message)


def is_json_value(value: object) -> bool:
    """判断 ``value`` 是否为合法递归 JSON 值。

    允许 ``None``、``bool``、``int``、有限 ``float``、``str``、``list`` 和键为
    ``str`` 的 ``Mapping``；拒绝非有限浮点数、非字符串对象键、循环容器、``bytes``、
    ``Path``、``Decimal``、``tuple``、``set`` 及任意其他 Python 对象。
    ``bool`` 在 ``int`` 之前单独判定，不把布尔值当作整数处理。
    """
    return _is_json_value(value, set())


def _is_json_value(value: object, active: set[int]) -> bool:
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        marker = id(value)
        if marker in active:
            return False
        active.add(marker)
        try:
            for item in value:
                if not _is_json_value(item, active):
                    return False
            return True
        finally:
            active.discard(marker)
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active:
            return False
        active.add(marker)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    return False
                if not _is_json_value(item, active):
                    return False
            return True
        finally:
            active.discard(marker)
    return False


@dataclass(frozen=True)
class Event:
    """外部协议归一化后的输入。

    字段约束由 ``Host.handle_event`` 在接收时校验；本数据类只固定形状并阻止字段
    重新赋值。``payload`` 必需，``source`` 可省略且缺省为空映射。
    """

    event_id: str
    ingress_id: str
    event_type: str
    payload: Mapping[str, JSONValue]
    source: Mapping[str, JSONValue] = field(default_factory=dict)
    external_request_id: str | None = None
    response_channel_id: str | None = None
    artifact_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Context:
    """本次 Run 的最小上下文；本切片固定为空。"""

    values: Mapping[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True)
class Run:
    """Host 为一次业务执行创建的生命周期身份。"""

    run_id: str
    event_id: str


@dataclass(frozen=True)
class ModelRequest:
    """交给 ModelClient 的模型请求。"""

    run: Run
    event: Event
    context: Context


@dataclass(frozen=True)
class ModelProposal:
    """模型返回的结构化提议，不是已执行动作。"""

    kind: str
    payload: Mapping[str, JSONValue]


@dataclass(frozen=True)
class HostResult:
    """Host 处理一次 Event 的结果。"""

    run: Run
    proposal: ModelProposal
