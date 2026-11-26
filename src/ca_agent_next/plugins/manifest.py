"""Plugin Package v1alpha1 Manifest 加载与静态校验。

校验顺序固定为：YAML 1.2 安全解析 → 重复 Key → 结构与未知字段 → 版本 →
身份 → Extension → 包根相对路径 → JSON Schema（离线）。只有在
:func:`load_manifest` 返回之后，Manager 才允许启动 Plugin 进程。

设计依据：``docs/规范/插件包与进程通信协议规范.md`` §3、§4；
``docs/设计说明书/F03-Plugin平台/Plugin平台设计说明书.md`` §5。
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from .errors import PluginError, PluginErrorCode

__all__ = [
    "PACKAGE_API_VERSION",
    "IPC_API_VERSION",
    "PLUGIN_KIND",
    "EXTENSION_KEYS",
    "EventBinding",
    "ResponseBinding",
    "PluginManifest",
    "load_manifest",
    "validate_instance",
]

PACKAGE_API_VERSION = "connectionagent.io/plugin-package/v1alpha1"
IPC_API_VERSION = "connectionagent.io/plugin-ipc/v1alpha1"
PLUGIN_KIND = "Plugin"
EXTENSION_KEYS = frozenset({"event.ingress", "event.delivery", "tools"})

_PLUGIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+-]*$")


@dataclass(frozen=True)
class EventBinding:
    """``extensions.event.ingress.events`` 中的一条 Event 声明。"""

    event_type: str
    request_schema_path: str
    request_schema: Mapping[str, Any]


@dataclass(frozen=True)
class ResponseBinding:
    """``extensions.event.delivery.responses`` 中的一条响应声明。"""

    event_type: str
    response_schema_path: str
    response_schema: Mapping[str, Any]


@dataclass(frozen=True)
class PluginManifest:
    """已通过全部静态校验的 Plugin Package Manifest。"""

    manifest_path: Path
    package_root: Path
    api_version: str
    plugin_id: str
    version: str
    protocol: str
    executable_path: Path
    args: tuple[str, ...]
    extensions: frozenset[str]
    event_bindings: Mapping[str, EventBinding]
    response_bindings: Mapping[str, ResponseBinding]
    tools_interface_package: str | None

    def has_extension(self, name: str) -> bool:
        return name in self.extensions


def load_manifest(manifest_path: str | os.PathLike[str]) -> PluginManifest:
    """加载并校验 Plugin Package Manifest。

    任何失败都抛出 :class:`PluginError`，且不会启动进程。
    """
    path = Path(manifest_path)
    if path.is_dir():
        path = path / "plugin.yaml"
    path = path.resolve()
    if not path.is_file():
        raise PluginError(
            PluginErrorCode.MANIFEST_UNREADABLE,
            "manifest file does not exist",
            details={"path": path.name},
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PluginError(
            PluginErrorCode.MANIFEST_UNREADABLE,
            "manifest file cannot be read as UTF-8",
            details={"reason": type(exc).__name__},
        ) from None

    document = _parse_yaml(text)
    package_root = path.parent
    _check_document_shape(document)
    return _build_manifest(path, package_root, document)


# ---------------------------------------------------------------------------
# YAML 1.2 解析
# ---------------------------------------------------------------------------


def _parse_yaml(text: str) -> Mapping[str, Any]:
    yaml = YAML(typ="safe")
    # YAML 1.2 语义；不使用 PyYAML 的 1.1 隐式类型。
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    try:
        documents = [doc for doc in yaml.load_all(text)]
    except Exception as exc:  # ruamel 的异常类型随版本变化，统一按类别分流
        name = type(exc).__name__
        if name == "DuplicateKeyError":
            raise PluginError(
                PluginErrorCode.MANIFEST_DUPLICATE_KEY,
                "manifest contains duplicate YAML keys",
            ) from None
        if isinstance(exc, YAMLError):
            raise PluginError(
                PluginErrorCode.MANIFEST_SYNTAX,
                "manifest is not valid YAML",
            ) from None
        raise PluginError(
            PluginErrorCode.MANIFEST_SYNTAX,
            "manifest is not valid YAML",
            details={"reason": name},
        ) from None
    if len(documents) != 1:
        raise PluginError(
            PluginErrorCode.MANIFEST_SYNTAX,
            "manifest must contain exactly one YAML document",
            details={"documents": len(documents)},
        )
    document = documents[0]
    if not isinstance(document, Mapping):
        raise PluginError(
            PluginErrorCode.MANIFEST_FIELD_INVALID,
            "manifest root must be a YAML mapping",
        )
    return document


# ---------------------------------------------------------------------------
# 结构与字段校验
# ---------------------------------------------------------------------------


def _fail_unknown(where: str, key: object) -> None:
    raise PluginError(
        PluginErrorCode.MANIFEST_UNKNOWN_FIELD,
        "manifest contains an unknown field",
        details={"location": where, "field": str(key)},
    )


def _fail_invalid(where: str, reason: str) -> None:
    raise PluginError(
        PluginErrorCode.MANIFEST_FIELD_INVALID,
        "manifest field is invalid",
        details={"location": where, "reason": reason},
    )


def _mapping(
    value: object,
    where: str,
    *,
    allowed: frozenset[str],
    required: frozenset[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail_invalid(where, "expected mapping")
    for key in value:
        if not isinstance(key, str):
            _fail_invalid(where, "mapping keys must be strings")
        if key not in allowed:
            _fail_unknown(where, key)
    for key in required:
        if key not in value:
            _fail_invalid(where, f"missing required field {key}")
    return value


def _non_blank_str(value: object, where: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        _fail_invalid(where, "expected non-empty string")
    return value


def _sequence(value: object, where: str, *, non_empty: bool) -> list[Any]:
    if not isinstance(value, list):
        _fail_invalid(where, "expected sequence")
    if non_empty and not value:
        _fail_invalid(where, "sequence must not be empty")
    return value


def _check_document_shape(document: Mapping[str, Any]) -> None:
    top = _mapping(
        document,
        "manifest",
        allowed=frozenset({"apiVersion", "kind", "metadata", "process", "extensions"}),
        required=frozenset({"apiVersion", "kind", "metadata", "process", "extensions"}),
    )

    api_version = _non_blank_str(top["apiVersion"], "apiVersion")
    if api_version != PACKAGE_API_VERSION:
        raise PluginError(
            PluginErrorCode.MANIFEST_VERSION_UNSUPPORTED,
            "unsupported plugin package apiVersion",
            details={"apiVersion": api_version},
        )
    if _non_blank_str(top["kind"], "kind") != PLUGIN_KIND:
        raise PluginError(
            PluginErrorCode.MANIFEST_FIELD_INVALID,
            "manifest kind must be Plugin",
        )


# ---------------------------------------------------------------------------
# 构建不可变 Manifest
# ---------------------------------------------------------------------------


def _build_manifest(
    manifest_path: Path,
    package_root: Path,
    document: Mapping[str, Any],
) -> PluginManifest:
    top: Mapping[str, Any] = document
    metadata = _mapping(
        top["metadata"],
        "metadata",
        allowed=frozenset({"id", "version"}),
        required=frozenset({"id", "version"}),
    )
    plugin_id = _non_blank_str(metadata["id"], "metadata.id")
    if not _PLUGIN_ID_RE.match(plugin_id):
        _fail_invalid("metadata.id", "invalid plugin id")
    version = _non_blank_str(metadata["version"], "metadata.version")
    if not _VERSION_RE.match(version):
        _fail_invalid("metadata.version", "invalid plugin version")

    process = _mapping(
        top["process"],
        "process",
        allowed=frozenset({"executable", "args", "protocol"}),
        required=frozenset({"executable", "protocol"}),
    )
    executable = _non_blank_str(process["executable"], "process.executable")
    protocol = _non_blank_str(process["protocol"], "process.protocol")
    if protocol != IPC_API_VERSION:
        raise PluginError(
            PluginErrorCode.MANIFEST_VERSION_UNSUPPORTED,
            "unsupported plugin IPC protocol",
            details={"protocol": protocol},
        )
    args_raw = process.get("args", [])
    args: list[str] = []
    for index, arg in enumerate(_sequence(args_raw, "process.args", non_empty=False)):
        if not isinstance(arg, str):
            _fail_invalid(f"process.args[{index}]", "expected string")
        args.append(arg)

    extensions_raw = top["extensions"]
    if not isinstance(extensions_raw, Mapping):
        _fail_invalid("extensions", "expected mapping")
    if not extensions_raw:
        _fail_invalid("extensions", "at least one extension is required")
    extensions: set[str] = set()
    for key in extensions_raw:
        if not isinstance(key, str) or key not in EXTENSION_KEYS:
            raise PluginError(
                PluginErrorCode.MANIFEST_UNKNOWN_FIELD,
                "manifest declares an unknown extension",
                details={"location": "extensions", "field": str(key)},
            )
        extensions.add(key)

    event_bindings: dict[str, EventBinding] = {}
    if "event.ingress" in extensions:
        ingress = _mapping(
            extensions_raw["event.ingress"],
            "extensions.event.ingress",
            allowed=frozenset({"events"}),
            required=frozenset({"events"}),
        )
        events = _sequence(
            ingress["events"], "extensions.event.ingress.events", non_empty=True
        )
        for index, item in enumerate(events):
            where = f"extensions.event.ingress.events[{index}]"
            entry = _mapping(
                item,
                where,
                allowed=frozenset({"type", "requestSchema"}),
                required=frozenset({"type", "requestSchema"}),
            )
            event_type = _non_blank_str(entry["type"], f"{where}.type")
            if event_type in event_bindings:
                raise PluginError(
                    PluginErrorCode.MANIFEST_FIELD_INVALID,
                    "duplicate event type declaration",
                    details={"eventType": event_type},
                )
            schema_rel = _non_blank_str(
                entry["requestSchema"], f"{where}.requestSchema"
            )
            schema_path, schema = _load_schema(
                package_root, schema_rel, f"{where}.requestSchema"
            )
            event_bindings[event_type] = EventBinding(
                event_type=event_type,
                request_schema_path=schema_rel,
                request_schema=schema,
            )

    response_bindings: dict[str, ResponseBinding] = {}
    if "event.delivery" in extensions:
        delivery = _mapping(
            extensions_raw["event.delivery"],
            "extensions.event.delivery",
            allowed=frozenset({"responses"}),
            required=frozenset({"responses"}),
        )
        responses = _sequence(
            delivery["responses"],
            "extensions.event.delivery.responses",
            non_empty=True,
        )
        for index, item in enumerate(responses):
            where = f"extensions.event.delivery.responses[{index}]"
            entry = _mapping(
                item,
                where,
                allowed=frozenset({"eventType", "responseSchema"}),
                required=frozenset({"eventType", "responseSchema"}),
            )
            event_type = _non_blank_str(entry["eventType"], f"{where}.eventType")
            if event_type in response_bindings:
                raise PluginError(
                    PluginErrorCode.MANIFEST_FIELD_INVALID,
                    "duplicate delivery event type declaration",
                    details={"eventType": event_type},
                )
            schema_rel = _non_blank_str(
                entry["responseSchema"], f"{where}.responseSchema"
            )
            schema_path, schema = _load_schema(
                package_root, schema_rel, f"{where}.responseSchema"
            )
            del schema_path
            response_bindings[event_type] = ResponseBinding(
                event_type=event_type,
                response_schema_path=schema_rel,
                response_schema=schema,
            )

    tools_interface_package: str | None = None
    if "tools" in extensions:
        tools = _mapping(
            extensions_raw["tools"],
            "extensions.tools",
            allowed=frozenset({"interfacePackage"}),
            required=frozenset({"interfacePackage"}),
        )
        tools_interface_package = _non_blank_str(
            tools["interfacePackage"], "extensions.tools.interfacePackage"
        )

    executable_path = _resolve_package_file(
        package_root, executable, "process.executable", allow_windows_suffix=True
    )

    return PluginManifest(
        manifest_path=manifest_path,
        package_root=package_root,
        api_version=PACKAGE_API_VERSION,
        plugin_id=plugin_id,
        version=version,
        protocol=protocol,
        executable_path=executable_path,
        args=tuple(args),
        extensions=frozenset(extensions),
        event_bindings=event_bindings,
        response_bindings=response_bindings,
        tools_interface_package=tools_interface_package,
    )


# ---------------------------------------------------------------------------
# 包根相对路径与离线 JSON Schema
# ---------------------------------------------------------------------------


def _resolve_package_file(
    package_root: Path,
    relative: str,
    location: str,
    *,
    allow_windows_suffix: bool = False,
) -> Path:
    if "\x00" in relative:
        _fail_path(location, "path contains NUL")
    if relative.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", relative):
        _fail_path(location, "absolute paths are not allowed")
    normalized = relative.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if any(part in ("..",) for part in parts):
        _fail_path(location, "path traversal is not allowed")
    if not parts:
        _fail_path(location, "empty path")

    root = package_root.resolve()
    candidate = root.joinpath(*parts)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        _fail_path(location, "path escapes the package root")

    if not resolved.is_file() and allow_windows_suffix and os.name == "nt":
        suffixed = Path(str(resolved) + ".exe")
        try:
            suffixed_resolved = suffixed.resolve()
            suffixed_resolved.relative_to(root)
        except (OSError, RuntimeError, ValueError):
            _fail_path(location, "path escapes the package root")
        if suffixed_resolved.is_file():
            return suffixed_resolved

    if not resolved.is_file():
        _fail_path(location, "path does not point to a file")
    return resolved


def _fail_path(location: str, reason: str) -> None:
    raise PluginError(
        PluginErrorCode.MANIFEST_PATH_INVALID,
        "manifest path is invalid",
        details={"location": location, "reason": reason},
    )


def _load_schema(
    package_root: Path, relative: str, location: str
) -> tuple[Path, Mapping[str, Any]]:
    path = _resolve_package_file(package_root, relative, location)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PluginError(
            PluginErrorCode.MANIFEST_SCHEMA_INVALID,
            "schema file cannot be read as UTF-8",
            details={"location": location, "reason": type(exc).__name__},
        ) from None
    try:
        document = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        raise PluginError(
            PluginErrorCode.MANIFEST_SCHEMA_INVALID,
            "schema file is not valid JSON",
            details={"location": location},
        ) from None
    if not isinstance(document, dict):
        raise PluginError(
            PluginErrorCode.MANIFEST_SCHEMA_INVALID,
            "schema document must be a JSON object",
            details={"location": location},
        )
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        raise PluginError(
            PluginErrorCode.MANIFEST_SCHEMA_INVALID,
            "schema document is not a valid Draft 2020-12 schema",
            details={"location": location, "reason": exc.validator},
        ) from None
    _check_local_refs(document, document, location)
    return path, document


def _check_local_refs(
    node: object, root: Mapping[str, Any], location: str
) -> None:
    """拒绝远程/外部 ``$ref`` 与 ``$dynamicRef``，并要求文档内引用可解析。

    Schema 校验必须完全离线；实现只接受同一文档内的 ``#`` 片段引用。
    ``$dynamicRef`` 与 ``$ref`` 受同一离线边界约束，不能作为绕过入口；纯
    ``#anchor`` 形式的动态引用交由 Draft 2020-12 的动态作用域解析，但其目标
    仍必须留在同一文档内。
    """
    if isinstance(node, Mapping):
        for ref_key in ("$ref", "$dynamicRef"):
            ref = node.get(ref_key)
            if ref is None:
                continue
            if not isinstance(ref, str) or not ref.startswith("#"):
                raise PluginError(
                    PluginErrorCode.MANIFEST_SCHEMA_INVALID,
                    f"schema uses a non-local {ref_key}; offline validation is required",
                    details={"location": location, "keyword": ref_key},
                )
            if ref_key == "$ref" or ref.startswith("#/"):
                if _resolve_pointer(root, ref) is _MISSING:
                    raise PluginError(
                        PluginErrorCode.MANIFEST_SCHEMA_INVALID,
                        f"schema {ref_key} cannot be resolved inside the document",
                        details={"location": location, "ref": ref},
                    )
        for key, value in node.items():
            if key in ("$ref", "$dynamicRef"):
                continue
            _check_local_refs(value, root, location)
    elif isinstance(node, list):
        for item in node:
            _check_local_refs(item, root, location)


_MISSING = object()


def _resolve_pointer(document: Mapping[str, Any], ref: str) -> object:
    if ref == "#":
        return document
    if not ref.startswith("#/"):
        return _MISSING
    current: object = document
    for raw in ref[2:].split("/"):
        token = urllib.parse.unquote(raw).replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                return _MISSING
            current = current[token]
        elif isinstance(current, list):
            try:
                index = int(token)
            except ValueError:
                return _MISSING
            if index < 0 or index >= len(current):
                return _MISSING
            current = current[index]
        else:
            return _MISSING
    return current


def validate_instance(
    schema: Mapping[str, Any], instance: object
) -> list[str]:
    """用离线 Validator 校验实例，返回安全错误路径列表（空表示通过）。"""
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in validator.iter_errors(instance):
        path = "/".join(str(part) for part in error.absolute_path)
        errors.append(path or "<root>")
    return errors
