"""Host：唯一对外执行入口 ``Host.handle_event``。

Host 校验 Event、创建 Run 与空 Context、构造 ModelRequest，并通过 AgentLoop
调用一次注入的 ModelClient。HostError 从 ``contracts`` 重导出，不重新定义。
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping

from .contracts import (
    Context,
    Event,
    HostError,
    HostResult,
    ModelRequest,
    Run,
    is_json_value,
)
from .model_client import ModelClient
from .model_loop import AgentLoop

__all__ = ["Host", "HostError"]


def _event_invalid() -> HostError:
    return HostError("EVENT_INVALID", "event is invalid")


def _host_internal_error() -> HostError:
    return HostError("HOST_INTERNAL_ERROR", "host internal error")


def _is_non_blank_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _default_run_id() -> str:
    return uuid.uuid4().hex


def _validate_event(event: object) -> None:
    """校验 Event 类型、全部字段与递归 JSONValue。"""
    if not isinstance(event, Event):
        raise _event_invalid()

    if not (
        _is_non_blank_str(event.event_id)
        and _is_non_blank_str(event.ingress_id)
        and _is_non_blank_str(event.event_type)
    ):
        raise _event_invalid()

    if not isinstance(event.payload, Mapping):
        raise _event_invalid()
    if not isinstance(event.source, Mapping):
        raise _event_invalid()

    try:
        if not is_json_value(event.payload) or not is_json_value(event.source):
            raise _event_invalid()
    except HostError:
        raise
    except Exception:
        raise _event_invalid() from None

    for value in (event.external_request_id, event.response_channel_id):
        if value is not None and not _is_non_blank_str(value):
            raise _event_invalid()

    if not isinstance(event.artifact_refs, tuple):
        raise _event_invalid()
    for ref in event.artifact_refs:
        if not _is_non_blank_str(ref):
            raise _event_invalid()


class Host:
    """业务中立的 Host 最小实现。"""

    def __init__(
        self,
        model_client: ModelClient,
        *,
        run_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._model_client = model_client
        self._loop = AgentLoop(model_client)
        self._run_id_factory = (
            _default_run_id if run_id_factory is None else run_id_factory
        )

    def handle_event(self, event: Event) -> HostResult:
        """校验 Event，创建 Run 与空 Context，执行一次 Model Loop。"""
        _validate_event(event)

        try:
            run_id = self._run_id_factory()
        except Exception:
            raise _host_internal_error() from None
        if not isinstance(run_id, str) or run_id.strip() == "":
            raise _host_internal_error()

        run = Run(run_id=run_id, event_id=event.event_id)
        context = Context()
        request = ModelRequest(run=run, event=event, context=context)

        try:
            proposal = self._loop.run_once(request)
        except HostError:
            raise
        except Exception:
            raise _host_internal_error() from None

        return HostResult(run=run, proposal=proposal)
