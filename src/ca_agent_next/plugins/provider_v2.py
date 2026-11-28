"""``ca-client-tools.provider/v2`` 的唯一 Tools Extension Driver。

本模块实现 SR-010 的 Host 侧 Provider v2 适配缝：

- 进程、NDJSON 帧、initialize / catalog / invoke / cancel；
- initialize 传入闭合 ``artifactChannel``，catalog 按 artifact slot 判定
  ``READY`` / ``NOT_CONFIGURED`` / ``NOT_IMPLEMENTED``；
- 当前 Invocation 的输入 Artifact 只按 Host 侧声明注入 ``{"artifactRef": ...}``；
- 取消、超时、Provider 退出后释放该 Invocation 的全部材料；
- 仍由唯一个 ``PluginManager`` 通过 ``register_driver`` 管理生命周期。

它不创建第二个 Manager / Registry / Runtime，不解释 Owner Outcome，也不
创建 Skill 或 Capability。Provider v2 的公开 Capability ↔ Callable 映射由
部署输入（``ProviderBindingSpec``）投影，不是新的权威注册表。

设计依据：F03.05 v0.4.12 §6.3～§6.4、§8.1、§8.2.1；F05 v0.4.15 §5～§6、
§9～§11；SR-010 AC-010-01～05。v1 SHA-256 契约不在本模块实现。
"""

from __future__ import annotations

import copy
import json
import logging
import os
import subprocess
import threading
import uuid
from collections.abc import Mapping
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from ..artifacts import (
    ArtifactChannelServer,
    ArtifactError,
    ArtifactLimits,
    ArtifactStore,
)
from .driver import (
    PROVIDER_V2_PROTOCOL,
    ProviderV2ToolsExtensionDriver,
    ToolInvocationHandle,
)
from .errors import PluginError, PluginErrorCode
from .manager import (
    CancelledOutcome,
    DeliveryOutcome,
    ToolOutcome,
    ToolStatus,
)

__all__ = [
    "ArtifactSlotSpec",
    "ProviderBindingSpec",
    "ProviderLimits",
    "ProviderV2Config",
    "StdioProviderV2Driver",
]

_LOG = logging.getLogger("ca_agent_next.plugins.provider_v2")
_MAX_REQUEST_ID = 128
_RESPONSE_KEYS = frozenset(
    {"protocolVersion", "type", "requestId", "ok", "result", "error"}
)
_DEFAULT_HOST_INSTANCE = "ca-agent-next-host"


@dataclass(frozen=True)
class ProviderLimits:
    """initialize.limits 的 Host 侧边界；Provider 必须接受同一组值。"""

    max_frame_bytes: int = 1024 * 1024
    max_in_flight: int = 8
    max_call_duration_ms: int = 30_000

    def validate(self) -> None:
        for name, value in (
            ("maxFrameBytes", self.max_frame_bytes),
            ("maxInFlight", self.max_in_flight),
            ("maxCallDurationMs", self.max_call_duration_ms),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    f"{name} must be a positive integer",
                )
        if self.max_in_flight > 128:
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "maxInFlight must not exceed 128",
            )

    def wire(self) -> Mapping[str, int]:
        return {
            "maxFrameBytes": self.max_frame_bytes,
            "maxInFlight": self.max_in_flight,
            "maxCallDurationMs": self.max_call_duration_ms,
        }


@dataclass(frozen=True)
class ArtifactSlotSpec:
    """Host 部署声明的一个私有 Artifact slot；不是公开 Skill Schema。"""

    pointer: str
    slot: str
    media_type: str
    required: bool = True

    def validate(self) -> None:
        if not isinstance(self.pointer, str) or not self.pointer.startswith("/"):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "artifact slot pointer must be a JSON pointer",
            )
        if not isinstance(self.slot, str) or not self.slot.strip():
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "artifact slot name must be a non-empty string",
            )
        if not isinstance(self.media_type, str) or not self.media_type.strip():
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "artifact slot mediaType must be a non-empty string",
            )
        if not isinstance(self.required, bool):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "artifact slot required must be a boolean",
            )


@dataclass(frozen=True)
class ProviderBindingSpec:
    """部署选定的 public Callable → private backendOperationId 投影。"""

    callable_id: str
    backend_operation_id: str
    effect: str = "READ"
    input_slots: tuple[ArtifactSlotSpec, ...] = ()
    output_slots: tuple[ArtifactSlotSpec, ...] = ()

    def validate(self) -> None:
        for name, value in (
            ("callableId", self.callable_id),
            ("backendOperationId", self.backend_operation_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    f"{name} must be a non-empty string",
                )
        if self.effect not in {"READ", "MUTATION"}:
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "effect must be READ or MUTATION",
            )
        seen_slots: set[str] = set()
        for spec in (*self.input_slots, *self.output_slots):
            if not isinstance(spec, ArtifactSlotSpec):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "artifact slots must be ArtifactSlotSpec instances",
                )
            spec.validate()
            if spec.slot in seen_slots:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "artifact slot names must be unique per binding",
                )
            seen_slots.add(spec.slot)

    @property
    def artifact_bearing(self) -> bool:
        return bool(self.input_slots or self.output_slots)


@dataclass(frozen=True)
class ProviderV2Config:
    """部署固定的 Provider 进程与绑定快照。

    ``artifact_limits`` 为 ``None`` 表示未配置 channel；artifact-bearing
    binding 必须保持 ``NOT_CONFIGURED``。显式提供的 limits 在进程启动前
    校验，非法值 fail-closed，不产生任何远端 I/O。
    """

    provider_id: str
    provider_version: str
    executable: str
    catalog_version: str
    bindings: tuple[ProviderBindingSpec, ...]
    args: tuple[str, ...] = ()
    cwd: str | os.PathLike[str] | None = None
    limits: ProviderLimits = field(default_factory=ProviderLimits)
    artifact_limits: ArtifactLimits | None = None
    artifact_root: str | os.PathLike[str] | None = None
    host_instance_id: str = _DEFAULT_HOST_INSTANCE
    provider_instance_id: str | None = None
    producer_invocation_id: str | None = None
    initialize_timeout: float = 10.0
    request_timeout: float = 10.0
    shutdown_timeout: float = 2.0

    def validate(self) -> None:
        for name, value in (
            ("providerId", self.provider_id),
            ("providerVersion", self.provider_version),
            ("executable", self.executable),
            ("catalogVersion", self.catalog_version),
            ("hostInstanceId", self.host_instance_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    f"{name} must be a non-empty string",
                )
        if not isinstance(self.bindings, tuple) or not self.bindings:
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "bindings must be a non-empty tuple",
            )
        callables: set[str] = set()
        backends: set[str] = set()
        for binding in self.bindings:
            if not isinstance(binding, ProviderBindingSpec):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "bindings must be ProviderBindingSpec instances",
                )
            binding.validate()
            if binding.callable_id in callables:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "callableId must be unique per provider deployment",
                )
            if binding.backend_operation_id in backends:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "backendOperationId must be unique per provider deployment",
                )
            callables.add(binding.callable_id)
            backends.add(binding.backend_operation_id)
        if not isinstance(self.limits, ProviderLimits):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "limits must be ProviderLimits",
            )
        self.limits.validate()
        if self.artifact_limits is not None:
            if not isinstance(self.artifact_limits, ArtifactLimits):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "artifactLimits must be ArtifactLimits",
                )
            try:
                self.artifact_limits.validate()
            except ArtifactError as error:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    error.message,
                ) from None
        for name, value in (
            ("initializeTimeout", self.initialize_timeout),
            ("requestTimeout", self.request_timeout),
            ("shutdownTimeout", self.shutdown_timeout),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    f"{name} must be a positive number",
                )
            if value <= 0:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    f"{name} must be a positive number",
                )
        if not isinstance(self.args, tuple) or any(
            not isinstance(item, str) for item in self.args
        ):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "args must be a tuple of strings",
            )
        if self.provider_instance_id is not None and (
            not isinstance(self.provider_instance_id, str)
            or not self.provider_instance_id.strip()
        ):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "providerInstanceId must be a non-empty string when provided",
            )
        if self.artifact_root is not None and not isinstance(
            self.artifact_root, (str, os.PathLike)
        ):
            raise PluginError(
                PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                "artifactRoot must be a path",
            )


@dataclass
class _Pending:
    request_id: str
    method: str
    future: Future[Any] = field(default_factory=Future)


@dataclass
class _BindingState:
    spec: ProviderBindingSpec
    status: str = "NOT_CONFIGURED"
    descriptor: Mapping[str, Any] | None = None


@dataclass
class _ActiveInvocation:
    invocation_id: str
    callable_id: str
    request_id: str
    binding: ProviderBindingSpec


class _ProviderInvocationHandle:
    """Manager 可见的统一 Tool 句柄。"""

    def __init__(
        self,
        driver: StdioProviderV2Driver,
        invocation_id: str,
        callable_id: str,
        request_id: str,
        future: Future[Any],
    ) -> None:
        self._driver = driver
        self.invocation_id = invocation_id
        self.callable_id = callable_id
        self._request_id = request_id
        self._future = future

    @property
    def message_id(self) -> str:
        return self._request_id

    def done(self) -> bool:
        return self._future.done()

    def wait(self, timeout: float | None = None) -> ToolOutcome:
        effective = (
            self._driver.request_timeout if timeout is None else timeout
        )
        try:
            return self._future.result(effective)
        except FutureTimeoutError:
            pass
        if self._future.done():
            return self._future.result()
        self._driver._abandon_invocation(self.invocation_id, "timeout")
        return ToolOutcome(
            invocation_id=self.invocation_id,
            callable_id=self.callable_id,
            status=ToolStatus.TIMEOUT,
            message_id=self._request_id,
        )


class StdioProviderV2Driver(ProviderV2ToolsExtensionDriver):
    """Provider v2 的 stdio NDJSON Driver，由唯一 PluginManager 管理。"""

    def __init__(
        self,
        config: ProviderV2Config,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or _LOG
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._state = "CONFIGURED"
        self._proc: subprocess.Popen[bytes] | None = None
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._pending: dict[str, _Pending] = {}
        self._bindings: dict[str, _BindingState] = {}
        self._active: dict[str, _ActiveInvocation] = {}
        self._eof = False
        self._shutdown = False
        self._diagnostics: list[str] = []
        self._counters = {
            "initialize": 0,
            "catalog": 0,
            "invoke": 0,
            "cancel": 0,
            "protocolViolations": 0,
        }
        self._store: ArtifactStore | None = None
        self._channel: ArtifactChannelServer | None = None
        self._artifact_channel_config: Mapping[str, Any] | None = None

    # -- public properties -------------------------------------------

    @property
    def plugin_id(self) -> str:
        return self._config.provider_id

    @property
    def protocol(self) -> str:
        return PROVIDER_V2_PROTOCOL

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({"tools"})

    @property
    def state(self) -> str:
        return self._state

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    @property
    def request_timeout(self) -> float:
        return self._config.request_timeout

    @property
    def artifact_store(self) -> ArtifactStore | None:
        return self._store

    @property
    def artifact_channel(self) -> ArtifactChannelServer | None:
        return self._channel

    @property
    def counters(self) -> Mapping[str, int]:
        with self._lock:
            snapshot = dict(self._counters)
        if self._channel is not None:
            snapshot.update(
                {
                    "artifactGets": self._channel.counters["gets"],
                    "artifactPosts": self._channel.counters["posts"],
                }
            )
        return snapshot

    @property
    def diagnostics(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._diagnostics)

    def binding_status(self, callable_id: str) -> str | None:
        with self._lock:
            state = self._bindings.get(callable_id)
            return None if state is None else state.status

    def available_callables(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                callable_id
                for callable_id, state in self._bindings.items()
                if state.status == "READY"
            )

    # -- lifecycle ----------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if self._state != "CONFIGURED":
                raise PluginError(
                    PluginErrorCode.INVALID_ARGUMENT,
                    "provider driver has already been started",
                )
            self._state = "STARTING"
        try:
            self._config.validate()
            self._bindings = {
                binding.callable_id: _BindingState(spec=binding)
                for binding in self._config.bindings
            }
            if self._config.artifact_limits is not None:
                try:
                    self._store = ArtifactStore(
                        self._config.artifact_root,
                        limits=self._config.artifact_limits,
                    )
                    self._channel = ArtifactChannelServer(self._store).start()
                except (ArtifactError, OSError) as error:
                    message = getattr(error, "message", "artifact channel failed")
                    raise PluginError(
                        PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                        message,
                    ) from None
                self._artifact_channel_config = self._channel.contract()
            self._spawn()
            self._initialize()
            self._catalog()
        except BaseException:
            self._terminate("startup failure", release_all=True)
            raise
        with self._lock:
            self._state = "READY"

    def close(self) -> None:
        self._terminate("driver closed", release_all=True)

    def invoke_tool_async(
        self,
        callable_id: str,
        arguments: Mapping[str, Any],
        *,
        invocation_id: str,
        timeout: float,
    ) -> ToolInvocationHandle:
        with self._lock:
            if self._state != "READY":
                raise PluginError(
                    PluginErrorCode.PLUGIN_NOT_READY,
                    "provider is not READY",
                    details={"providerId": self._config.provider_id},
                )
            state = self._bindings.get(callable_id)
            if state is None:
                raise PluginError(
                    PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED,
                    "callable is not declared for this provider deployment",
                    details={"callableId": callable_id},
                )
            if state.status != "READY":
                raise PluginError(
                    PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED,
                    "binding is not available",
                    details={"callableId": callable_id, "status": state.status},
                )
            binding = state.spec
            if binding.artifact_bearing and self._channel is None:
                raise PluginError(
                    PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED,
                    "artifact-bearing binding requires an artifact channel",
                    details={"callableId": callable_id, "status": "NOT_CONFIGURED"},
                )
            prepared = self._prepare_arguments(binding, arguments, invocation_id)
            request_id = self._next_request_id()
            params: dict[str, Any] = {
                "backendOperationId": binding.backend_operation_id,
                "arguments": prepared,
                "invocation": {
                    "invocationId": invocation_id,
                    "producerInvocationId": (
                        self._config.producer_invocation_id or invocation_id
                    ),
                    "deadline": self._deadline(),
                },
            }
            pending = self._request_locked("invoke", params, request_id)
            self._active[invocation_id] = _ActiveInvocation(
                invocation_id, callable_id, request_id, binding
            )
            self._counters["invoke"] += 1
        self._write_request(request_id, "invoke", params)
        outcome_future: Future[Any] = Future()

        def _on_done(completed: Future[Any]) -> None:
            try:
                outcome = self._outcome_for(
                    invocation_id, request_id, completed
                )
            except BaseException as error:  # noqa: BLE001 - 收敛到句柄
                if not outcome_future.done():
                    outcome_future.set_exception(error)
                return
            if not outcome_future.done():
                outcome_future.set_result(outcome)

        pending.future.add_done_callback(_on_done)
        return _ProviderInvocationHandle(
            self, invocation_id, callable_id, request_id, outcome_future
        )

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
        raise PluginError(
            PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED,
            "provider v2 does not export the event.delivery extension",
        )

    def cancel_operation(
        self, invocation_id: str, *, reason: str, timeout: float
    ) -> CancelledOutcome:
        with self._lock:
            active = self._active.get(invocation_id)
            if active is None:
                return CancelledOutcome(
                    target_operation_id=invocation_id,
                    disposition="unsupported",
                    cancel_message_id="",
                    correlation_id="",
                )
            cancel_id = self._next_request_id()
            pending = self._request_locked(
                "cancel", {"targetRequestId": active.request_id}, cancel_id
            )
            self._counters["cancel"] += 1
        self._write_request(cancel_id, "cancel", {"targetRequestId": active.request_id})
        try:
            result = pending.future.result(timeout)
        except FutureTimeoutError:
            self._abandon_invocation(invocation_id, "cancel timeout")
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "provider did not acknowledge cancel before the timeout",
                details={"invocationId": invocation_id},
            ) from None
        except PluginError:
            self._abandon_invocation(invocation_id, "cancel failed")
            raise
        disposition = "unsupported"
        if isinstance(result, Mapping):
            raw = result.get("status")
            if raw == "CANCEL_REQUESTED":
                disposition = "cancelled"
            elif raw == "ALREADY_COMPLETED":
                disposition = "too_late"
            elif raw == "NOT_FOUND":
                disposition = "unsupported"
        if disposition == "cancelled":
            self._release_invocation(invocation_id, "cancelled")
        return CancelledOutcome(
            target_operation_id=invocation_id,
            disposition=disposition,
            cancel_message_id=cancel_id,
            correlation_id=cancel_id,
        )

    # -- private: startup --------------------------------------------

    def _spawn(self) -> None:
        command = [self._config.executable, *self._config.args]
        kwargs: dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if self._config.cwd is not None:
            kwargs["cwd"] = str(self._config.cwd)
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self._proc = subprocess.Popen(command, **kwargs)
        except OSError:
            raise PluginError(
                PluginErrorCode.PROCESS_START_FAILED,
                "provider process could not be started",
                details={"providerId": self._config.provider_id},
            ) from None
        self._reader = threading.Thread(
            target=self._read_stdout,
            name=f"provider-{self._config.provider_id}-stdout",
            daemon=True,
        )
        self._stderr_reader = threading.Thread(
            target=self._read_stderr,
            name=f"provider-{self._config.provider_id}-stderr",
            daemon=True,
        )
        self._reader.start()
        self._stderr_reader.start()

    def _initialize(self) -> None:
        params: dict[str, Any] = {
            "hostInstanceId": self._config.host_instance_id,
            "providerInstanceId": (
                self._config.provider_instance_id
                or f"{self._config.provider_id}-{uuid.uuid4().hex}"
            ),
            "limits": dict(self._config.limits.wire()),
        }
        if self._artifact_channel_config is not None:
            params["artifactChannel"] = dict(self._artifact_channel_config)
        request_id = self._next_request_id()
        pending = self._request_locked(
            "initialize", params, request_id, counted="initialize"
        )
        self._write_request(request_id, "initialize", params)
        try:
            result = pending.future.result(self._config.initialize_timeout)
        except FutureTimeoutError:
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "provider initialize did not complete before the timeout",
                details={"providerId": self._config.provider_id},
            ) from None
        finally:
            with self._lock:
                self._pending.pop(request_id, None)
        if not isinstance(result, Mapping):
            raise PluginError(
                PluginErrorCode.REMOTE_RESPONSE_INVALID,
                "provider initialize result must be an object",
            )
        if result.get("providerId") != self._config.provider_id:
            raise PluginError(
                PluginErrorCode.HANDSHAKE_MISMATCH,
                "provider identity does not match the deployment",
            )
        if result.get("providerVersion") != self._config.provider_version:
            raise PluginError(
                PluginErrorCode.HANDSHAKE_MISMATCH,
                "provider version does not match the deployment",
            )
        if result.get("catalogVersion") != self._config.catalog_version:
            raise PluginError(
                PluginErrorCode.HANDSHAKE_MISMATCH,
                "provider catalogVersion does not match the deployment",
            )
        wire_limits = result.get("limits")
        if wire_limits is not None:
            if not isinstance(wire_limits, Mapping):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "provider initialize limits must be an object",
                )
            for key in ("maxFrameBytes", "maxInFlight", "maxCallDurationMs"):
                value = wire_limits.get(key)
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value <= 0
                ):
                    raise PluginError(
                        PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                        "provider initialize limits are invalid",
                    )
        echo = result.get("artifactChannel")
        if echo is not None:
            if self._artifact_channel_config is None:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "provider reported an artifact channel that was not offered",
                )
            if not isinstance(echo, Mapping):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "provider artifactChannel acknowledgement must be an object",
                )
            forbidden = {"baseUrl", "processToken"}
            if forbidden & set(echo.keys()):
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "provider must not echo channel credentials",
                )
            allowed = {
                "apiVersion",
                "requestTimeoutMs",
                "maxArtifactBytes",
                "maxAggregateBytes",
                "maxAttachments",
            }
            if set(echo.keys()) - allowed:
                raise PluginError(
                    PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                    "provider artifactChannel acknowledgement has unknown fields",
                )
            expected = self._artifact_channel_config
            for key in allowed:
                if key in echo and echo[key] != expected.get(key):
                    raise PluginError(
                        PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
                        "provider artifactChannel bounds do not match the Host",
                    )

    def _catalog(self) -> None:
        backend_ids: list[str] = []
        for binding in self._config.bindings:
            if binding.backend_operation_id not in backend_ids:
                backend_ids.append(binding.backend_operation_id)
        request_id = self._next_request_id()
        params = {"backendOperationIds": backend_ids}
        pending = self._request_locked("catalog", params, request_id)
        self._write_request(request_id, "catalog", params)
        try:
            result = pending.future.result(self._config.request_timeout)
        except FutureTimeoutError:
            raise PluginError(
                PluginErrorCode.IPC_TIMEOUT,
                "provider catalog did not complete before the timeout",
            ) from None
        finally:
            with self._lock:
                self._pending.pop(request_id, None)
        if not isinstance(result, Mapping):
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "provider catalog result must be an object",
            )
        if result.get("catalogVersion") != self._config.catalog_version:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "provider catalogVersion mismatch",
            )
        supported = result.get("supported")
        unsupported = result.get("unsupported")
        if not isinstance(supported, list) or not isinstance(unsupported, list):
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog supported/unsupported must be arrays",
            )
        descriptors: dict[str, Mapping[str, Any]] = {}
        supported_ids: list[str] = []
        for item in supported:
            if not isinstance(item, Mapping):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog descriptor must be an object",
                )
            backend_id = item.get("backendOperationId")
            if (
                not isinstance(backend_id, str)
                or backend_id not in backend_ids
                or backend_id in descriptors
                or backend_id in supported_ids
            ):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog returned an unexpected or duplicate backend id",
                )
            supported_ids.append(backend_id)
            descriptors[backend_id] = item
        unsupported_ids: list[str] = []
        for item in unsupported:
            if not isinstance(item, Mapping):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog unsupported entry must be an object",
                )
            backend_id = item.get("backendOperationId")
            if not isinstance(backend_id, str) or backend_id not in backend_ids:
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog unsupported returned an unexpected backend id",
                )
            if backend_id in unsupported_ids or backend_id in supported_ids:
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog unsupported ids must be unique and disjoint",
                )
            unsupported_ids.append(backend_id)
        if sorted(supported_ids + unsupported_ids) != sorted(backend_ids):
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog did not partition every requested backend id",
            )
        # 请求顺序保持：catalog 的分区列表都必须是请求序列的子序列。
        if supported_ids != [item for item in backend_ids if item in supported_ids]:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog supported order does not match the request",
            )
        if unsupported_ids != [
            item for item in backend_ids if item in unsupported_ids
        ]:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog unsupported order does not match the request",
            )
        for binding in self._config.bindings:
            descriptor = descriptors.get(binding.backend_operation_id)
            state = self._bindings[binding.callable_id]
            if descriptor is None:
                state.status = "NOT_IMPLEMENTED"
                continue
            self._validate_descriptor(binding, descriptor)
            state.descriptor = descriptor
            if binding.artifact_bearing and self._channel is None:
                state.status = "NOT_CONFIGURED"
            else:
                state.status = "READY"
        with self._lock:
            self._counters["catalog"] += 1

    def _validate_descriptor(
        self, binding: ProviderBindingSpec, descriptor: Mapping[str, Any]
    ) -> None:
        effect = descriptor.get("effect")
        if effect is not None and effect != binding.effect:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog effect does not match the deployment binding",
            )
        slots = descriptor.get("artifactSlots")
        if slots is None:
            declared_inputs: list[ArtifactSlotSpec] = []
            declared_outputs: list[ArtifactSlotSpec] = []
        elif isinstance(slots, Mapping):
            declared_inputs = self._parse_slots(slots.get("inputs"), "inputs")
            declared_outputs = self._parse_slots(slots.get("outputs"), "outputs")
        else:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog artifactSlots must be an object",
            )
        if declared_inputs and not binding.input_slots:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog declares input artifacts not projected by the deployment",
            )
        if declared_outputs and not binding.output_slots:
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                "catalog declares output artifacts not projected by the deployment",
            )
        self._require_same_slots(binding.input_slots, declared_inputs, "input")
        self._require_same_slots(binding.output_slots, declared_outputs, "output")

    def _parse_slots(self, raw: object, direction: str) -> list[ArtifactSlotSpec]:
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                f"catalog artifactSlots.{direction} must be an array",
            )
        parsed: list[ArtifactSlotSpec] = []
        for item in raw:
            if not isinstance(item, Mapping):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    f"catalog artifactSlots.{direction} entries must be objects",
                )
            pointer = item.get("pointer")
            slot = item.get("slot")
            media_type = item.get("mediaType")
            required = item.get("required", True)
            if not isinstance(pointer, str) or not pointer.startswith("/"):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog artifact slot pointer is invalid",
                )
            if not isinstance(slot, str) or not slot:
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog artifact slot name is invalid",
                )
            if not isinstance(media_type, str) or not media_type:
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog artifact slot mediaType is invalid",
                )
            if not isinstance(required, bool):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    "catalog artifact slot required is invalid",
                )
            parsed.append(ArtifactSlotSpec(pointer, slot, media_type, required))
        return parsed

    def _require_same_slots(
        self,
        expected: tuple[ArtifactSlotSpec, ...],
        declared: list[ArtifactSlotSpec],
        direction: str,
    ) -> None:
        if len(expected) != len(declared):
            raise PluginError(
                PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                f"catalog {direction} artifact slot count does not match the deployment",
            )
        for host_slot, catalog_slot in zip(expected, declared):
            if (
                host_slot.pointer != catalog_slot.pointer
                or host_slot.slot != catalog_slot.slot
                or host_slot.media_type != catalog_slot.media_type
                or host_slot.required != catalog_slot.required
            ):
                raise PluginError(
                    PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
                    f"catalog {direction} artifact slots do not match the deployment",
                )

    # -- private: invocation ------------------------------------------

    def _prepare_arguments(
        self,
        binding: ProviderBindingSpec,
        arguments: Mapping[str, Any],
        invocation_id: str,
    ) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise PluginError(
                PluginErrorCode.BACKEND_ARGUMENTS_INVALID,
                "tool arguments must be a JSON object",
            )
        prepared = copy.deepcopy(dict(arguments))
        # 模型不可自行构造 artifactRef：所有调用参数中的该字段一律移除，
        # 只有 Host 在声明的私有 slot 上重新注入当前 Invocation 的授权引用。
        _strip_artifact_refs(prepared)
        if not binding.artifact_bearing:
            return prepared
        store = self._store
        if store is None:  # pragma: no cover - 由 available 状态先行拦截
            raise PluginError(
                PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED,
                "artifact store is not configured",
            )
        store.create_invocation(
            invocation_id,
            output_slots={
                spec.slot: spec.media_type for spec in binding.output_slots
            },
        )
        available = {
            item.slot: item for item in store.inputs_for(invocation_id)
        }
        for spec in binding.input_slots:
            # 公开参数不得携带模型自造的 artifactRef；先移除 Host 专属位置，
            # 再仅注入当前 Invocation 已授权的引用。
            _remove_pointer(prepared, spec.pointer)
            item = available.get(spec.slot)
            if item is None:
                if spec.required:
                    raise PluginError(
                        PluginErrorCode.ARTIFACT_REFERENCE_INVALID,
                        "required input artifact is not bound to this invocation",
                        details={"slot": spec.slot},
                    )
                continue
            if item.media_type != spec.media_type:
                raise PluginError(
                    PluginErrorCode.ARTIFACT_REFERENCE_INVALID,
                    "input artifact mediaType does not match the declared slot",
                    details={"slot": spec.slot},
                )
            _set_pointer(prepared, spec.pointer, {"artifactRef": item.artifact_ref})
        return prepared

    def _outcome_for(
        self, invocation_id: str, request_id: str, future: Future[Any]
    ) -> ToolOutcome:
        with self._lock:
            active = self._active.pop(invocation_id, None)
            callable_id = (
                active.callable_id if active is not None else ""
            )
            self._pending.pop(request_id, None)
        try:
            result = future.result()
        except PluginError as error:
            if error.code == PluginErrorCode.CALL_CANCELLED:
                self._release_invocation(invocation_id, "provider cancelled")
                return ToolOutcome(
                    invocation_id=invocation_id,
                    callable_id=callable_id,
                    status=ToolStatus.CANCELLED,
                    error={"code": error.code, "message": error.message},
                    message_id=request_id,
                )
            if error.code == PluginErrorCode.PROCESS_EXITED:
                self._release_invocation(invocation_id, "provider exited")
                return ToolOutcome(
                    invocation_id=invocation_id,
                    callable_id=callable_id,
                    status=ToolStatus.ABORTED,
                    error={"code": error.code, "message": error.message},
                    message_id=request_id,
                )
            return ToolOutcome(
                invocation_id=invocation_id,
                callable_id=callable_id,
                status=ToolStatus.ERROR,
                error={"code": error.code, "message": error.message},
                message_id=request_id,
            )
        if not isinstance(result, Mapping):
            return ToolOutcome(
                invocation_id=invocation_id,
                callable_id=callable_id,
                status=ToolStatus.ERROR,
                error={
                    "code": PluginErrorCode.REMOTE_RESPONSE_INVALID,
                    "message": "provider invoke result must be an object",
                },
                message_id=request_id,
            )
        return ToolOutcome(
            invocation_id=invocation_id,
            callable_id=callable_id,
            status=ToolStatus.RESULT,
            result=dict(result),
            message_id=request_id,
        )

    def _abandon_invocation(self, invocation_id: str, reason: str) -> None:
        with self._lock:
            active = self._active.pop(invocation_id, None)
            if active is not None:
                pending = self._pending.pop(active.request_id, None)
                if pending is not None and not pending.future.done():
                    pending.future.set_exception(
                        PluginError(
                            PluginErrorCode.CALL_DEADLINE_EXCEEDED,
                            "invocation was abandoned before completion",
                        )
                    )
        self._release_invocation(invocation_id, reason)
        self._terminate(f"invocation {reason}", release_all=False)

    def _release_invocation(self, invocation_id: str, reason: str) -> None:
        if self._store is not None:
            try:
                self._store.release(invocation_id, reason=reason)
            except ArtifactError:
                pass

    # -- private: frames ---------------------------------------------

    def _read_stdout(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:  # pragma: no cover
            return
        while True:
            try:
                line = proc.stdout.readline(
                    self._config.limits.max_frame_bytes + 1
                )
            except (OSError, ValueError):
                self._on_eof("stdout read failed")
                return
            if not line:
                self._on_eof("provider closed stdout")
                return
            if len(line) > self._config.limits.max_frame_bytes:
                self._protocol_failure(
                    PluginErrorCode.PROTOCOL_FRAME_TOO_LARGE,
                    "provider frame exceeds maxFrameBytes",
                )
                return
            try:
                frame = json.loads(
                    line.decode("utf-8"),
                    parse_constant=_reject_json_constant,
                    object_pairs_hook=_reject_duplicate_keys,
                )
            except (UnicodeDecodeError, ValueError):
                self._protocol_failure(
                    PluginErrorCode.PROTOCOL_FRAME_INVALID,
                    "provider frame is not valid UTF-8 JSON",
                )
                return
            self._on_frame(frame)

    def _read_stderr(self) -> None:
        proc = self._proc
        if proc is None or proc.stderr is None:  # pragma: no cover
            return
        while True:
            try:
                chunk = proc.stderr.read(4096)
            except (OSError, ValueError):
                return
            if not chunk:
                return
            # stderr 只保留长度，不保存原文，避免凭据/业务值进入日志。
            with self._lock:
                self._diagnostics.append("provider stderr chunk")
                if len(self._diagnostics) > 128:
                    del self._diagnostics[0]

    def _on_frame(self, frame: object) -> None:
        if not isinstance(frame, Mapping):
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider frame must be an object",
            )
            return
        if set(frame.keys()) - _RESPONSE_KEYS:
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider frame has unknown fields",
            )
            return
        if frame.get("protocolVersion") != PROVIDER_V2_PROTOCOL:
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_VERSION_UNSUPPORTED,
                "provider frame protocolVersion is unsupported",
            )
            return
        if frame.get("type") != "response":
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider frame type must be response",
            )
            return
        request_id = frame.get("requestId")
        if (
            not isinstance(request_id, str)
            or not request_id
            or len(request_id) > _MAX_REQUEST_ID
            or not request_id.isascii()
        ):
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_REQUEST_ID_INVALID,
                "provider response requestId is invalid",
            )
            return
        ok = frame.get("ok")
        if not isinstance(ok, bool):
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider response ok must be a boolean",
            )
            return
        has_result = "result" in frame
        has_error = "error" in frame
        if ok and not has_result or (not ok) and not has_error:
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider response must carry exactly one of result/error",
            )
            return
        if ok and has_error or (not ok) and has_result:
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider response result/error do not match ok",
            )
            return
        with self._lock:
            pending = self._pending.get(request_id)
        if pending is None:
            self._protocol_failure(
                PluginErrorCode.PROTOCOL_FRAME_INVALID,
                "provider response has no pending request",
            )
            return
        if ok:
            if not pending.future.done():
                pending.future.set_result(frame.get("result"))
            return
        error = frame.get("error")
        code = PluginErrorCode.REMOTE_RESPONSE_INVALID
        message = "provider returned an error"
        if isinstance(error, Mapping):
            raw_code = error.get("code")
            if isinstance(raw_code, str) and raw_code.isascii() and raw_code:
                code = raw_code[:96]
            raw_message = error.get("message")
            if isinstance(raw_message, str):
                message = raw_message.replace("\n", " ")[:200]
        if not pending.future.done():
            pending.future.set_exception(PluginError(code, message))

    def _protocol_failure(self, code: str, message: str) -> None:
        with self._lock:
            self._counters["protocolViolations"] += 1
            self._diagnostics.append(code)
        failure = PluginError(code, message)
        self._fail_pending(failure)
        self._terminate("provider protocol violation", release_all=True)

    def _on_eof(self, reason: str) -> None:
        with self._lock:
            if self._eof:
                return
            self._eof = True
        self._fail_pending(
            PluginError(
                PluginErrorCode.PROCESS_EXITED,
                "provider process exited",
            )
        )
        self._terminate(reason, release_all=True)

    def _fail_pending(self, error: PluginError) -> None:
        with self._lock:
            pending = list(self._pending.values())
            self._pending.clear()
            active = list(self._active.values())
        for item in pending:
            if not item.future.done():
                item.future.set_exception(error)
        for item in active:
            self._release_invocation(item.invocation_id, "provider failure")

    # -- private: requests -------------------------------------------

    def _next_request_id(self) -> str:
        return uuid.uuid4().hex

    def _request_locked(
        self,
        method: str,
        params: Mapping[str, Any],
        request_id: str,
        *,
        counted: str | None = None,
    ) -> _Pending:
        with self._lock:
            if len(self._pending) >= self._config.limits.max_in_flight:
                raise PluginError(
                    PluginErrorCode.PROVIDER_INTERNAL,
                    "provider maxInFlight is exhausted",
                )
            pending = _Pending(request_id=request_id, method=method)
            self._pending[request_id] = pending
            if counted is not None:
                self._counters[counted] = self._counters.get(counted, 0) + 1
            return pending

    def _write_request(
        self, request_id: str, method: str, params: Mapping[str, Any]
    ) -> None:
        frame = {
            "protocolVersion": PROVIDER_V2_PROTOCOL,
            "type": "request",
            "requestId": request_id,
            "method": method,
            "params": dict(params),
        }
        try:
            data = json.dumps(
                frame, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError):
            with self._lock:
                self._pending.pop(request_id, None)
            raise PluginError(
                PluginErrorCode.PROVIDER_INTERNAL,
                "provider request is not JSON-serializable",
            ) from None
        if len(data) + 1 > self._config.limits.max_frame_bytes:
            with self._lock:
                self._pending.pop(request_id, None)
            raise PluginError(
                PluginErrorCode.PROTOCOL_FRAME_TOO_LARGE,
                "provider request exceeds maxFrameBytes",
            )
        proc = self._proc
        if proc is None or proc.stdin is None:
            with self._lock:
                self._pending.pop(request_id, None)
            raise PluginError(
                PluginErrorCode.REMOTE_TRANSPORT_ERROR,
                "provider process is not running",
            )
        with self._write_lock:
            try:
                proc.stdin.write(data + b"\n")
                proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                with self._lock:
                    self._pending.pop(request_id, None)
                raise PluginError(
                    PluginErrorCode.REMOTE_TRANSPORT_ERROR,
                    "provider request could not be written",
                ) from None

    def _deadline(self) -> str:
        moment = datetime.now(UTC) + timedelta(
            milliseconds=self._config.limits.max_call_duration_ms
        )
        return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # -- private: shutdown -------------------------------------------

    def _terminate(self, reason: str, *, release_all: bool) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            active = list(self._active.values())
            self._active.clear()
            pending = list(self._pending.values())
            self._pending.clear()
            self._state = "STOPPED"
        for item in pending:
            if not item.future.done():
                item.future.set_exception(
                    PluginError(
                        PluginErrorCode.PROVIDER_SHUTTING_DOWN,
                        "provider driver is shutting down",
                    )
                )
        if release_all:
            for item in active:
                self._release_invocation(item.invocation_id, reason)
        proc = self._proc
        if proc is not None:
            try:
                if proc.stdin is not None:
                    proc.stdin.close()
            except OSError:
                pass
            try:
                proc.wait(timeout=self._config.shutdown_timeout)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:  # pragma: no cover
                    proc.kill()
                    proc.wait(timeout=1.0)
        if proc is not None:
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    if stream is not None:
                        stream.close()
                except OSError:
                    pass
        self._proc = None
        channel = self._channel
        self._channel = None
        if channel is not None:
            channel.stop()
        store = self._store
        self._store = None
        if store is not None:
            store.close()


def _set_pointer(document: dict[str, Any], pointer: str, value: Any) -> None:
    """把 Host 私有 Artifact 引用写入 JSON pointer；不改写公开 Schema。"""
    segments = pointer.lstrip("/").split("/")
    if not pointer.startswith("/") or not segments or any(not item for item in segments):
        raise PluginError(
            PluginErrorCode.BACKEND_ARGUMENTS_INVALID,
            "artifact slot pointer is invalid",
        )
    current: Any = document
    for raw in segments[:-1]:
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or key not in current:
            raise PluginError(
                PluginErrorCode.BACKEND_ARGUMENTS_INVALID,
                "artifact slot pointer parent does not exist",
            )
        current = current[key]
    key = segments[-1].replace("~1", "/").replace("~0", "~")
    if not isinstance(current, dict):
        raise PluginError(
            PluginErrorCode.BACKEND_ARGUMENTS_INVALID,
            "artifact slot pointer parent must be an object",
        )
    current[key] = value

def _remove_pointer(document: dict[str, Any], pointer: str) -> None:
    segments = pointer.lstrip("/").split("/")
    if not pointer.startswith("/") or not segments:
        return
    current: Any = document
    for raw in segments[:-1]:
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or key not in current:
            return
        current = current[key]
    if isinstance(current, dict):
        current.pop(segments[-1].replace("~1", "/").replace("~0", "~"), None)


def _strip_artifact_refs(document: Any) -> None:
    """递归移除调用参数中模型自造的 ``artifactRef`` 字段。"""
    if isinstance(document, dict):
        document.pop("artifactRef", None)
        for value in document.values():
            _strip_artifact_refs(value)
    elif isinstance(document, list):
        for value in document:
            _strip_artifact_refs(value)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result
