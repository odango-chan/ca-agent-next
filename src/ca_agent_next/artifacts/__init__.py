"""Host-owned ArtifactStore 与 ``ca-host.artifact-store/v2`` no-hash channel。

本模块只实现 Next 1.6.0 Demo 的 Host 侧 Artifact 交接边界：

- Host 生成随机 opaque ``artifactRef``；引用不编码路径、URL、mediaType、size
  或内容摘要。
- 每份材料绑定 ``invocationId`` / ``direction`` / ``slot``；读取与发布都必须
  精确匹配当前 Invocation 的声明。
- Artifact 原始字节只在 Host 与 Provider 进程的 loopback HTTP/1.1 channel 中
  传输，不进入 Plugin NDJSON、不使用 Base64。
- v2 不计算、不传输、不校验 SHA-256 / checksum / digest。历史 v1 SHA-256
  契约不在此实现，也不提供 Adapter、双轨或 fallback。
- 大小、聚合计费、附件数量、TTL、取消与原子发布由 Store 统一执行；未完成
  的输出在提交前不可读。

设计依据：F05 v0.4.15 §5、§6.2、§9～§11；F03.05 v0.4.12 §8.1；SR-010
AC-010-01～05。本模块不定义 Provider v2 的 catalog / invoke DTO；那是
``ca_agent_next.plugins.provider_v2`` 的职责。
"""

from __future__ import annotations

import base64
import hmac
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Self

__all__ = [
    "ARTIFACT_CHANNEL_API_VERSION",
    "ArtifactBinding",
    "ArtifactChannelServer",
    "ArtifactDirection",
    "ArtifactError",
    "ArtifactErrorCode",
    "ArtifactLimits",
    "ArtifactStore",
    "StagedOutput",
]

ARTIFACT_CHANNEL_API_VERSION = "ca-host.artifact-store/v2"

_REF_PATTERN = re.compile(r"^art_[A-Za-z0-9_-]{43}$")
_MAX_ERROR_BODY = 4096


class ArtifactErrorCode:
    """ArtifactStore / Channel 的稳定错误码。"""

    ARTIFACT_REFERENCE_INVALID = "ARTIFACT_REFERENCE_INVALID"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    ARTIFACT_EXPIRED = "ARTIFACT_EXPIRED"
    ARTIFACT_SLOT_MISMATCH = "ARTIFACT_SLOT_MISMATCH"
    ARTIFACT_DIRECTION_MISMATCH = "ARTIFACT_DIRECTION_MISMATCH"
    ARTIFACT_MEDIA_TYPE_MISMATCH = "ARTIFACT_MEDIA_TYPE_MISMATCH"
    ARTIFACT_QUOTA_EXCEEDED = "ARTIFACT_QUOTA_EXCEEDED"
    ARTIFACT_CONFIGURATION_INVALID = "ARTIFACT_CONFIGURATION_INVALID"
    ARTIFACT_TRANSFER_FAILED = "ARTIFACT_TRANSFER_FAILED"
    ARTIFACT_CHANNEL_NOT_CONFIGURED = "ARTIFACT_CHANNEL_NOT_CONFIGURED"


class ArtifactError(Exception):
    """安全的结构化错误；``message`` 不含路径、字节或凭据。"""

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


class ArtifactDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_int(value: object, name: str) -> int:
    if not _is_int(value) or value <= 0:
        raise ArtifactError(
            ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
            f"{name} must be a positive integer",
        )
    return int(value)


def _non_blank(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactError(
            ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
            f"{name} must be a non-empty string",
        )
    return value


@dataclass(frozen=True)
class ArtifactLimits:
    """Host 部署配置的 channel / store 边界。

    这些是部署值，不是协议常量；Provider 在 initialize 中只收到有效 bounds。
    """

    max_artifact_bytes: int = 8 * 1024 * 1024
    max_aggregate_bytes: int = 32 * 1024 * 1024
    max_attachments: int = 8
    request_timeout_ms: int = 10000
    ttl_seconds: float = 300.0

    def validate(self) -> None:
        _positive_int(self.max_artifact_bytes, "maxArtifactBytes")
        _positive_int(self.max_aggregate_bytes, "maxAggregateBytes")
        _positive_int(self.max_attachments, "maxAttachments")
        _positive_int(self.request_timeout_ms, "requestTimeoutMs")
        if not isinstance(self.ttl_seconds, (int, float)) or isinstance(
            self.ttl_seconds, bool
        ):
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "ttlSeconds must be a positive number",
            )
        if self.ttl_seconds <= 0:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "ttlSeconds must be a positive number",
            )
        if self.max_artifact_bytes > self.max_aggregate_bytes:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "maxArtifactBytes must not exceed maxAggregateBytes",
            )


@dataclass(frozen=True)
class ArtifactBinding:
    """一份已发布 Artifact 的 Host 视图；不包含文件路径。"""

    artifact_ref: str
    invocation_id: str
    direction: ArtifactDirection
    slot: str
    media_type: str
    byte_length: int
    created_at: float
    expires_at: float

    def public_view(self) -> Mapping[str, Any]:
        return {
            "artifactRef": self.artifact_ref,
            "direction": self.direction.value,
            "slot": self.slot,
            "mediaType": self.media_type,
            "byteLength": self.byte_length,
        }


@dataclass
class _Entry:
    binding: ArtifactBinding
    path: Path


@dataclass
class _InvocationState:
    invocation_id: str
    output_slots: dict[str, str]
    aggregate_bytes: int = 0
    attachments: int = 0
    released: bool = False
    release_reason: str | None = None


def _new_ref() -> str:
    token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    return "art_" + token.rstrip("=")


class ArtifactStore:
    """唯一 Host-owned ArtifactStore。

    所有公开方法线程安全。引用只在本 Store 内有效；Store 关闭后全部清除。
    """

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        *,
        limits: ArtifactLimits | None = None,
        clock: Any = None,
    ) -> None:
        self._limits = limits or ArtifactLimits()
        self._limits.validate()
        self._clock = clock or time.time
        self._lock = threading.RLock()
        self._entries: dict[str, _Entry] = {}
        self._invocations: dict[str, _InvocationState] = {}
        self._closed = False
        self._owner_root_created = False
        if root is None:
            owner = Path(tempfile.mkdtemp(prefix="ca-agent-next-artifacts-"))
            self._owner_root_created = True
        else:
            owner = Path(root)
            owner.mkdir(parents=True, exist_ok=True)
        # 每个 Store 使用独立工作目录；路径不进入任何公开视图。
        self._work = Path(tempfile.mkdtemp(prefix="store-", dir=str(owner)))
        self._root = owner

    @property
    def limits(self) -> ArtifactLimits:
        return self._limits

    @property
    def closed(self) -> bool:
        return self._closed

    def create_invocation(
        self,
        invocation_id: str,
        *,
        output_slots: Mapping[str, str] | None = None,
    ) -> None:
        invocation = _non_blank(invocation_id, "invocationId")
        with self._lock:
            self._require_open()
            state = self._invocations.get(invocation)
            if state is None:
                state = _InvocationState(invocation, {})
                self._invocations[invocation] = state
            if state.released:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                    "invocation artifacts were released",
                )
            for slot, media_type in dict(output_slots or {}).items():
                _non_blank(slot, "slot")
                _non_blank(media_type, "mediaType")
                state.output_slots[slot] = media_type

    def publish_input(
        self,
        invocation_id: str,
        slot: str,
        media_type: str,
        data: bytes,
    ) -> ArtifactBinding:
        """Host 发布一份输入材料；调用方必须先完成授权与 Schema 校验。"""
        return self._publish(
            invocation_id, ArtifactDirection.INPUT, slot, media_type, data
        )

    def publish_output(
        self,
        invocation_id: str,
        slot: str,
        media_type: str,
        data: bytes,
    ) -> ArtifactBinding:
        """Host 原子发布一份 Provider 输出；slot/mediaType 必须预先声明。"""
        return self._publish(
            invocation_id, ArtifactDirection.OUTPUT, slot, media_type, data
        )

    def begin_output(
        self,
        invocation_id: str,
        slot: str,
        media_type: str,
    ) -> StagedOutput:
        """开始一次流式输出；提交前不可读，abort/超时自动清除。"""
        invocation = _non_blank(invocation_id, "invocationId")
        slot_name = _non_blank(slot, "slot")
        media = _non_blank(media_type, "mediaType")
        with self._lock:
            self._require_open()
            state = self._invocations.get(invocation)
            if state is None or state.released:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                    "invocation is not registered or was released",
                )
            declared = state.output_slots.get(slot_name)
            if declared is None:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_SLOT_MISMATCH,
                    "slot is not declared for this invocation output",
                )
            if declared != media:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_MEDIA_TYPE_MISMATCH,
                    "mediaType does not match the declared output slot",
                )
            if state.attachments + 1 > self._limits.max_attachments:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                    "invocation attachments exceed maxAttachments",
                )
            state.attachments += 1
        try:
            return StagedOutput(self, invocation, slot_name, media)
        except BaseException:
            self._release_attachment(invocation)
            raise

    def authorize(
        self,
        artifact_ref: str,
        *,
        invocation_id: str,
        slot: str,
        direction: ArtifactDirection,
    ) -> ArtifactBinding:
        """绑定校验：引用、Invocation、direction、slot、TTL 缺一不可。"""
        ref = _non_blank(artifact_ref, "artifactRef")
        invocation = _non_blank(invocation_id, "invocationId")
        slot_name = _non_blank(slot, "slot")
        with self._lock:
            self._require_open()
            entry = self._entries.get(ref)
            if entry is None:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                    "artifact reference is unknown",
                )
            binding = entry.binding
            if binding.invocation_id != invocation:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                    "artifact reference is not bound to this invocation",
                )
            if binding.direction is not direction:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_DIRECTION_MISMATCH,
                    "artifact reference direction does not match the transfer",
                )
            if binding.slot != slot_name:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_SLOT_MISMATCH,
                    "artifact reference slot does not match the declared slot",
                )
            if self._clock() >= binding.expires_at:
                self._drop_entry_locked(ref)
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_EXPIRED,
                    "artifact reference has expired",
                )
            return binding

    def read_input(
        self, artifact_ref: str, *, invocation_id: str, slot: str
    ) -> bytes:
        payload, _binding = self.read_input_view(
            artifact_ref, invocation_id=invocation_id, slot=slot
        )
        return payload

    def read_input_view(
        self, artifact_ref: str, *, invocation_id: str, slot: str
    ) -> tuple[bytes, ArtifactBinding]:
        with self._lock:
            binding = self.authorize(
                artifact_ref,
                invocation_id=invocation_id,
                slot=slot,
                direction=ArtifactDirection.INPUT,
            )
            entry = self._entries[artifact_ref]
            return entry.path.read_bytes(), binding

    def read_output(
        self, artifact_ref: str, *, invocation_id: str, slot: str
    ) -> bytes:
        with self._lock:
            self.authorize(
                artifact_ref,
                invocation_id=invocation_id,
                slot=slot,
                direction=ArtifactDirection.OUTPUT,
            )
            entry = self._entries[artifact_ref]
            return entry.path.read_bytes()

    def binding(self, artifact_ref: str) -> ArtifactBinding | None:
        with self._lock:
            entry = self._entries.get(artifact_ref)
            return None if entry is None else entry.binding

    def inputs_for(self, invocation_id: str) -> tuple[ArtifactBinding, ...]:
        with self._lock:
            return tuple(
                entry.binding
                for entry in self._entries.values()
                if entry.binding.invocation_id == invocation_id
                and entry.binding.direction is ArtifactDirection.INPUT
            )

    def outputs_for(self, invocation_id: str) -> tuple[ArtifactBinding, ...]:
        with self._lock:
            return tuple(
                entry.binding
                for entry in self._entries.values()
                if entry.binding.invocation_id == invocation_id
                and entry.binding.direction is ArtifactDirection.OUTPUT
            )

    def release(self, invocation_id: str, *, reason: str = "released") -> int:
        """取消/超时/Provider 退出时清除该 Invocation 的全部材料。"""
        invocation = _non_blank(invocation_id, "invocationId")
        with self._lock:
            state = self._invocations.get(invocation)
            removed = 0
            for ref in [
                ref
                for ref, entry in self._entries.items()
                if entry.binding.invocation_id == invocation
            ]:
                if self._drop_entry_locked(ref):
                    removed += 1
            if state is not None:
                state.released = True
                state.release_reason = reason
                state.aggregate_bytes = 0
                state.attachments = 0
            return removed

    def expire(self, *, now: float | None = None) -> int:
        """清除过期材料；返回清除数量。"""
        current = self._clock() if now is None else now
        with self._lock:
            expired = [
                ref
                for ref, entry in self._entries.items()
                if current >= entry.binding.expires_at
            ]
            removed = 0
            for ref in expired:
                if self._drop_entry_locked(ref):
                    removed += 1
            return removed

    def stats(self) -> Mapping[str, int]:
        with self._lock:
            return {
                "artifacts": len(self._entries),
                "invocations": len(self._invocations),
                "totalBytes": sum(
                    entry.binding.byte_length for entry in self._entries.values()
                ),
            }

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            for entry in self._entries.values():
                _unlink(entry.path)
            self._entries.clear()
            for state in self._invocations.values():
                state.released = True
                state.aggregate_bytes = 0
                state.attachments = 0
        shutil.rmtree(self._work, ignore_errors=True)
        if self._owner_root_created:
            shutil.rmtree(self._root, ignore_errors=True)

    # -- internal -----------------------------------------------------

    def _require_open(self) -> None:
        if self._closed:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_NOT_FOUND, "artifact store is closed"
            )

    def _publish(
        self,
        invocation_id: str,
        direction: ArtifactDirection,
        slot: str,
        media_type: str,
        data: bytes,
    ) -> ArtifactBinding:
        invocation = _non_blank(invocation_id, "invocationId")
        slot_name = _non_blank(slot, "slot")
        media = _non_blank(media_type, "mediaType")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                "artifact data must be bytes",
            )
        payload = bytes(data)
        with self._lock:
            self._require_open()
            state = self._invocations.get(invocation)
            if state is None:
                state = _InvocationState(invocation, {})
                self._invocations[invocation] = state
            if state.released:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                    "invocation artifacts were released",
                )
            if len(payload) > self._limits.max_artifact_bytes:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                    "artifact exceeds maxArtifactBytes",
                )
            if direction is ArtifactDirection.OUTPUT:
                declared = state.output_slots.get(slot_name)
                if declared is None:
                    raise ArtifactError(
                        ArtifactErrorCode.ARTIFACT_SLOT_MISMATCH,
                        "slot is not declared for this invocation output",
                    )
                if declared != media:
                    raise ArtifactError(
                        ArtifactErrorCode.ARTIFACT_MEDIA_TYPE_MISMATCH,
                        "mediaType does not match the declared output slot",
                    )
            self._reserve(state, len(payload), 1)
            try:
                path = self._write_atomically(payload)
            except ArtifactError:
                state.aggregate_bytes = max(0, state.aggregate_bytes - len(payload))
                state.attachments = max(0, state.attachments - 1)
                raise
            binding = self._binding_for(
                invocation, direction, slot_name, media, len(payload)
            )
            self._entries[binding.artifact_ref] = _Entry(binding, path)
            return binding

    def _reserve(
        self, state: _InvocationState, additional_bytes: int, attachments: int
    ) -> None:
        if (
            state.aggregate_bytes + additional_bytes
            > self._limits.max_aggregate_bytes
        ):
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                "invocation aggregate bytes exceed maxAggregateBytes",
            )
        if state.attachments + attachments > self._limits.max_attachments:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                "invocation attachments exceed maxAttachments",
            )
        state.aggregate_bytes += additional_bytes
        state.attachments += attachments

    def _release_attachment(self, invocation_id: str) -> None:
        with self._lock:
            state = self._invocations.get(invocation_id)
            if state is not None and state.attachments > 0 and not state.released:
                state.attachments -= 1

    def _binding_for(
        self,
        invocation_id: str,
        direction: ArtifactDirection,
        slot: str,
        media_type: str,
        byte_length: int,
    ) -> ArtifactBinding:
        now = self._clock()
        return ArtifactBinding(
            artifact_ref=_new_ref(),
            invocation_id=invocation_id,
            direction=direction,
            slot=slot,
            media_type=media_type,
            byte_length=byte_length,
            created_at=now,
            expires_at=now + self._limits.ttl_seconds,
        )

    def _write_atomically(self, payload: bytes) -> Path:
        temporary = self._work / f".tmp-{uuid.uuid4().hex}"
        final = self._work / f"{uuid.uuid4().hex}.bin"
        try:
            with open(temporary, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, final)
        except OSError:
            _unlink(temporary)
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                "artifact could not be stored atomically",
            ) from None
        return final

    def _drop_entry_locked(self, artifact_ref: str) -> bool:
        entry = self._entries.pop(artifact_ref, None)
        if entry is None:
            return False
        _unlink(entry.path)
        state = self._invocations.get(entry.binding.invocation_id)
        if state is not None and not state.released:
            state.aggregate_bytes = max(
                0, state.aggregate_bytes - entry.binding.byte_length
            )
            state.attachments = max(0, state.attachments - 1)
        return True

    def _commit_staged(self, staged: _StagedCursor) -> ArtifactBinding:
        with self._lock:
            self._require_open()
            state = self._invocations.get(staged.invocation_id)
            if state is None or state.released:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                    "invocation artifacts were released",
                )
            if staged.byte_length > self._limits.max_artifact_bytes:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                    "artifact exceeds maxArtifactBytes",
                )
            # begin_output 已预留 1 个附件；聚合计费在提交时按实际长度补足。
            extra = staged.byte_length
            if state.aggregate_bytes + extra > self._limits.max_aggregate_bytes:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                    "invocation aggregate bytes exceed maxAggregateBytes",
                )
            state.aggregate_bytes += extra
            final = self._work / f"{uuid.uuid4().hex}.bin"
            try:
                os.replace(staged.temporary, final)
            except OSError:
                _unlink(staged.temporary)
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                    "artifact could not be published atomically",
                ) from None
            binding = self._binding_for(
                staged.invocation_id,
                ArtifactDirection.OUTPUT,
                staged.slot,
                staged.media_type,
                staged.byte_length,
            )
            self._entries[binding.artifact_ref] = _Entry(binding, final)
            return binding


@dataclass
class _StagedCursor:
    invocation_id: str
    slot: str
    media_type: str
    temporary: Path
    byte_length: int = 0


class StagedOutput:
    """流式输出句柄；必须 ``commit()`` 才可读，``abort()`` 清除临时文件。"""

    def __init__(
        self,
        store: ArtifactStore,
        invocation_id: str,
        slot: str,
        media_type: str,
    ) -> None:
        temporary = store._work / f".upload-{uuid.uuid4().hex}"
        try:
            descriptor = os.open(
                temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except OSError:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                "artifact staging could not be created",
            ) from None
        self._store = store
        self._cursor = _StagedCursor(invocation_id, slot, media_type, temporary)
        self._stream = os.fdopen(descriptor, "wb")
        self._outcome: str | None = None
        self._lock = threading.Lock()

    @property
    def byte_length(self) -> int:
        return self._cursor.byte_length

    def write(self, chunk: bytes) -> None:
        with self._lock:
            if self._outcome is not None:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                    "staged output is already finished",
                )
            if not isinstance(chunk, (bytes, bytearray, memoryview)):
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                    "artifact chunks must be bytes",
                )
            payload = bytes(chunk)
            if (
                self._cursor.byte_length + len(payload)
                > self._store.limits.max_artifact_bytes
            ):
                self._abort_locked()
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                    "artifact exceeds maxArtifactBytes",
                )
            self._stream.write(payload)
            self._cursor.byte_length += len(payload)

    def commit(self) -> ArtifactBinding:
        with self._lock:
            if self._outcome is not None:
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                    "staged output is already finished",
                )
            try:
                self._stream.flush()
                os.fsync(self._stream.fileno())
            except OSError:
                self._abort_locked()
                raise ArtifactError(
                    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                    "artifact could not be staged",
                ) from None
            finally:
                self._stream.close()
            try:
                binding = self._store._commit_staged(self._cursor)
            except BaseException:
                self._abort_locked()
                raise
            self._outcome = "committed"
            return binding

    def abort(self) -> None:
        with self._lock:
            if self._outcome is not None:
                return
            self._abort_locked()

    def _abort_locked(self) -> None:
        self._outcome = "aborted"
        try:
            self._stream.close()
        except OSError:  # pragma: no cover - 已关闭或底层断开
            pass
        _unlink(self._cursor.temporary)
        self._store._release_attachment(self._cursor.invocation_id)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._outcome is None:
            self.abort()


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


class _ChannelHandler(BaseHTTPRequestHandler):
    """loopback v2 channel 的 HTTP/1.1 处理器。"""

    protocol_version = "HTTP/1.1"
    server_version = "ca-agent-next-artifact-channel"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:
        # 不记录 URL、header 或字节；只保留安全诊断由调用方决定。
        return

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    # -- dispatch -----------------------------------------------------

    def _handle(self, method: str) -> None:
        self.close_connection = True
        channel: ArtifactChannelServer = self.server.artifact_channel  # type: ignore[attr-defined]
        try:
            self.connection.settimeout(channel.request_timeout_seconds)
        except OSError:  # pragma: no cover - 连接已关闭
            return
        if not channel.authorized(self.headers.get("Authorization")):
            self._send_error(401, ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                             "process token is invalid")
            return
        if method == "GET":
            self._handle_get(channel)
        else:
            self._handle_post(channel)

    def _handle_get(self, channel: ArtifactChannelServer) -> None:
        prefix = "/v2/artifacts/"
        if not self.path.startswith(prefix):
            self._send_error(404, ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                             "artifact endpoint is unknown")
            return
        artifact_ref = self.path[len(prefix):].split("?", 1)[0]
        if not _REF_PATTERN.fullmatch(artifact_ref):
            self._send_error(404, ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                             "artifact reference is invalid")
            return
        invocation_id = self.headers.get("X-CA-Invocation")
        slot = self.headers.get("X-CA-Slot")
        if not invocation_id or not slot:
            self._send_error(400, ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                             "invocation and slot headers are required")
            return
        try:
            payload, binding = channel.store.read_input_view(
                artifact_ref, invocation_id=invocation_id, slot=slot
            )
        except ArtifactError as error:
            self._send_artifact_error(error)
            return
        self.send_response(200)
        self.send_header("Content-Type", binding.media_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):  # pragma: no cover
            return
        channel.record_get()

    def _handle_post(self, channel: ArtifactChannelServer) -> None:
        if self.path.split("?", 1)[0] != "/v2/artifacts":
            self._send_error(404, ArtifactErrorCode.ARTIFACT_NOT_FOUND,
                             "artifact endpoint is unknown")
            return
        invocation_id = self.headers.get("X-CA-Invocation")
        slot = self.headers.get("X-CA-Slot")
        media_type = self.headers.get("Content-Type")
        raw_length = self.headers.get("Content-Length")
        if not invocation_id or not slot or not media_type or raw_length is None:
            self._send_error(400, ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID,
                             "invocation, slot, media type and length are required")
            return
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self._send_error(400, ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                             "Content-Length is invalid")
            return
        if length < 0:
            self._send_error(400, ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                             "Content-Length is invalid")
            return
        if length > channel.store.limits.max_artifact_bytes:
            self._send_error(413, ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED,
                             "artifact exceeds maxArtifactBytes")
            return
        try:
            staged = channel.store.begin_output(invocation_id, slot, media_type)
        except ArtifactError as error:
            self._send_artifact_error(error)
            return
        remaining = length
        try:
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    staged.abort()
                    self._send_error(
                        400,
                        ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                        "artifact upload ended before Content-Length",
                    )
                    return
                staged.write(chunk)
                remaining -= len(chunk)
            binding = staged.commit()
        except ArtifactError as error:
            staged.abort()
            self._send_artifact_error(error)
            return
        except (TimeoutError, OSError):
            staged.abort()
            self._send_error(400, ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED,
                             "artifact upload failed")
            return
        body = json.dumps(
            {"artifactRef": binding.artifact_ref}, separators=(",", ":")
        ).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):  # pragma: no cover
            return
        channel.record_post()

    # -- response -----------------------------------------------------

    def _send_artifact_error(self, error: ArtifactError) -> None:
        status = _STATUS_BY_CODE.get(error.code, 409)
        self._send_error(status, error.code, error.message)

    def _send_error(self, status: int, code: str, message: str) -> None:
        body = json.dumps(
            {"error": {"code": code, "message": message}}, separators=(",", ":")
        ).encode("utf-8")
        if len(body) > _MAX_ERROR_BODY:  # pragma: no cover - 固定短消息
            body = b'{"error":{"code":"INTERNAL","message":"error"}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):  # pragma: no cover
            return


_STATUS_BY_CODE = {
    ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID: 409,
    ArtifactErrorCode.ARTIFACT_NOT_FOUND: 404,
    ArtifactErrorCode.ARTIFACT_EXPIRED: 410,
    ArtifactErrorCode.ARTIFACT_SLOT_MISMATCH: 409,
    ArtifactErrorCode.ARTIFACT_DIRECTION_MISMATCH: 409,
    ArtifactErrorCode.ARTIFACT_MEDIA_TYPE_MISMATCH: 415,
    ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED: 413,
    ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID: 400,
    ArtifactErrorCode.ARTIFACT_TRANSFER_FAILED: 400,
    ArtifactErrorCode.ARTIFACT_CHANNEL_NOT_CONFIGURED: 503,
}


class _ChannelHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], handler: Any, channel: Any) -> None:
        self.artifact_channel = channel
        super().__init__(address, handler)


class ArtifactChannelServer:
    """Host 为单个 Provider 进程创建的 loopback HTTP/1.1 listener。

    ``base_url`` 只能是 ``http://127.0.0.1:<ephemeral>``；token 只保存在内存，
    不进入 argv、环境变量或日志。本类不拥有 Store 生命周期。
    """

    def __init__(
        self,
        store: ArtifactStore,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        process_token: str | None = None,
    ) -> None:
        if host != "127.0.0.1":
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "artifact channel must bind to 127.0.0.1",
            )
        if not _is_int(port) or port < 0 or port > 65535:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "artifact channel port is invalid",
            )
        token = process_token or secrets.token_urlsafe(32)
        if not isinstance(token, str) or len(token) < 32:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CONFIGURATION_INVALID,
                "artifact channel process token is invalid",
            )
        self._store = store
        self._token = token
        self._host = host
        self._requested_port = port
        self._server: _ChannelHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._gets = 0
        self._posts = 0

    @property
    def store(self) -> ArtifactStore:
        return self._store

    @property
    def request_timeout_seconds(self) -> float:
        return self._store.limits.request_timeout_ms / 1000.0

    @property
    def started(self) -> bool:
        return self._server is not None

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise ArtifactError(
                ArtifactErrorCode.ARTIFACT_CHANNEL_NOT_CONFIGURED,
                "artifact channel is not started",
            )
        host, port = self._server.server_address[0], self._server.server_address[1]
        return f"http://{host}:{port}"

    @property
    def counters(self) -> Mapping[str, int]:
        with self._lock:
            return {"gets": self._gets, "posts": self._posts}

    def start(self) -> ArtifactChannelServer:
        with self._lock:
            if self._server is not None:
                return self
            server = _ChannelHTTPServer(
                (self._host, self._requested_port), _ChannelHandler, self
            )
            self._server = server
            self._thread = threading.Thread(
                target=server.serve_forever,
                name="artifact-channel",
                kwargs={"poll_interval": 0.05},
                daemon=True,
            )
            self._thread.start()
        return self

    def stop(self) -> None:
        with self._lock:
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=2.0)

    def authorized(self, header: str | None) -> bool:
        if not isinstance(header, str):
            return False
        prefix = "Bearer "
        if not header.startswith(prefix):
            return False
        return hmac.compare_digest(header[len(prefix):], self._token)

    def contract(self) -> Mapping[str, Any]:
        """Provider ``initialize.artifactChannel`` 的闭合对象。"""
        limits = self._store.limits
        return {
            "apiVersion": ARTIFACT_CHANNEL_API_VERSION,
            "baseUrl": self.base_url,
            "processToken": self._token,
            "requestTimeoutMs": limits.request_timeout_ms,
            "maxArtifactBytes": limits.max_artifact_bytes,
            "maxAggregateBytes": limits.max_aggregate_bytes,
            "maxAttachments": limits.max_attachments,
        }

    def record_get(self) -> None:
        with self._lock:
            self._gets += 1

    def record_post(self) -> None:
        with self._lock:
            self._posts += 1

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()
