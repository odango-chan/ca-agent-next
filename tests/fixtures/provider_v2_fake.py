#!/usr/bin/env python3
"""SR-010 test-only Provider v2 peer (``ca-client-tools.provider/v2``).

This fixture is a counting, deterministic stand-in for a real Provider. It is
never part of the production package and must not be used as interop evidence
for AC-010-09. It speaks the closed NDJSON framing, consumes the Host-owned
``ca-host.artifact-store/v2`` channel (GET input / POST output, no SHA-256),
and records a machine-readable trace for test assertions.

Usage (from the repository root):
``uv run --no-sync --locked --group dev --extra plugins python
tests/fixtures/provider_v2_fake.py --config <config.json>``.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import socket
import sys
import threading
import time
import urllib.parse
from typing import Any

_WRITE_LOCK = threading.Lock()
_TRACE_LOCK = threading.Lock()
_CONFIG: dict[str, Any] = {}
_TRACE = None
_ACTIVE: dict[str, threading.Event] = {}
_ACTIVE_LOCK = threading.Lock()


def _trace(event: str, **fields: Any) -> None:
    path = _CONFIG.get("trace")
    if not path:
        return
    record = {"event": event, "ts": time.time(), **fields}
    with _TRACE_LOCK, open(path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _respond(request_id: str, ok: bool, *, result: Any = None, error: Any = None) -> None:
    frame: dict[str, Any] = {
        "protocolVersion": "ca-client-tools.provider/v2",
        "type": "response",
        "requestId": request_id,
        "ok": ok,
    }
    if ok:
        frame["result"] = result
    else:
        frame["error"] = error
    data = json.dumps(frame, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    with _WRITE_LOCK:
        sys.stdout.write(data + "\n")
        sys.stdout.flush()


def _binding(backend_operation_id: str) -> dict[str, Any] | None:
    for item in _CONFIG.get("bindings", []):
        if item.get("backendOperationId") == backend_operation_id:
            return item
    return None


def _pointer(document: Any, pointer: str) -> Any:
    current = document
    for raw in pointer.lstrip("/").split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _channel_headers(channel: dict[str, Any], invocation_id: str, slot: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {channel['processToken']}",
        "X-CA-Invocation": invocation_id,
        "X-CA-Slot": slot,
    }


def _get_artifact(
    channel: dict[str, Any], artifact_ref: str, invocation_id: str, slot: str
) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(channel["baseUrl"])
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.request(
            "GET",
            f"/v2/artifacts/{artifact_ref}",
            headers=_channel_headers(channel, invocation_id, slot),
        )
        response = connection.getresponse()
        body = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        record = {
            "status": response.status,
            "byteLength": len(body),
            "contentType": headers.get("content-type"),
            "declaredLength": headers.get("content-length"),
            "digestHeader": any(
                "sha256" in key or "digest" in key or "checksum" in key
                for key in headers
            ),
            "slot": slot,
        }
        _trace("artifact_get", **record)
        return record
    finally:
        connection.close()


def _post_artifact(
    channel: dict[str, Any],
    invocation_id: str,
    slot: str,
    media_type: str,
    payload: bytes,
    *,
    partial: bool,
) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(channel["baseUrl"])
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    headers = _channel_headers(channel, invocation_id, slot)
    headers["Content-Type"] = media_type
    headers["Content-Length"] = str(len(payload) + (16 if partial else 0))
    status = -1
    body = b""
    reference = None
    try:
        connection.putrequest("POST", "/v2/artifacts")
        for key, value in headers.items():
            connection.putheader(key, value)
        connection.endheaders()
        connection.send(payload)
        if partial and connection.sock is not None:
            connection.sock.shutdown(socket.SHUT_WR)
        try:
            response = connection.getresponse()
            status = response.status
            body = response.read()
            if status == 201:
                reference = json.loads(body.decode("utf-8")).get("artifactRef")
        except (OSError, ValueError, http.client.HTTPException):
            status = -1
        record = {
            "status": status,
            "slot": slot,
            "mediaType": media_type,
            "byteLength": len(payload),
            "artifactRef": reference,
            "partial": partial,
            "digestHeader": False,
        }
        _trace("artifact_post", **record)
        return record
    finally:
        connection.close()


def _handle_invoke(request_id: str, params: dict[str, Any]) -> None:
    backend_id = params.get("backendOperationId")
    invocation = params.get("invocation") or {}
    invocation_id = invocation.get("invocationId")
    arguments = params.get("arguments") or {}
    event = threading.Event()
    with _ACTIVE_LOCK:
        _ACTIVE[request_id] = event
    mode = _CONFIG.get("mode", "normal")
    _trace(
        "invoke_start",
        requestId=request_id,
        backendOperationId=backend_id,
        invocationId=invocation_id,
        deadline=invocation.get("deadline"),
    )
    try:
        if mode == "exit_on_invoke":
            _trace("provider_exit", requestId=request_id)
            os._exit(3)
        if mode == "slow_invoke":
            event.wait(30)
            _respond(
                request_id,
                False,
                error={"code": "CALL_CANCELLED", "message": "invocation cancelled"},
            )
            return
        binding = _binding(backend_id or "")
        if binding is None:
            _respond(
                request_id,
                False,
                error={
                    "code": "BACKEND_OPERATION_UNSUPPORTED",
                    "message": "unknown backend operation",
                },
            )
            return
        channel = _CONFIG.get("_channel")
        slots = (binding.get("artifactSlots") or {})
        received = []
        codec_calls = 0
        for spec in slots.get("inputs", []):
            value = _pointer(arguments, spec["pointer"])
            if not isinstance(value, dict) or not isinstance(value.get("artifactRef"), str):
                continue
            codec_calls += 1
            if channel is None:
                _respond(
                    request_id,
                    False,
                    error={
                        "code": "ARTIFACT_REFERENCE_INVALID",
                        "message": "no artifact channel configured",
                    },
                )
                return
            received.append(
                _get_artifact(
                    channel, value["artifactRef"], invocation_id, spec["slot"]
                )
            )
        output_ref = None
        output_status = None
        for spec in slots.get("outputs", []):
            if channel is None:
                continue
            payload = bytes.fromhex(_CONFIG.get("outputHex", "0a0b0c"))
            posted = _post_artifact(
                channel,
                invocation_id,
                spec["slot"],
                spec["mediaType"],
                payload,
                partial=(mode == "partial_upload"),
            )
            output_status = posted["status"]
            output_ref = posted["artifactRef"]
            break
        _respond(
            request_id,
            True,
            result={
                "backendOperationId": backend_id,
                "httpStatus": 200,
                "received": received,
                "codecCalls": codec_calls,
                "outputArtifactRef": output_ref,
                "outputPostStatus": output_status,
                "channelConfigured": channel is not None,
            },
        )
        _trace(
            "invoke_result",
            requestId=request_id,
            codecCalls=codec_calls,
            outputPostStatus=output_status,
        )
    except BaseException as error:  # noqa: BLE001 - test fixture boundary
        _trace("invoke_error", requestId=request_id, error=type(error).__name__)
        _respond(
            request_id,
            False,
            error={"code": "PROVIDER_INTERNAL", "message": "fixture failure"},
        )
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE.pop(request_id, None)


def _handle_cancel(request_id: str, params: dict[str, Any]) -> None:
    target = params.get("targetRequestId")
    with _ACTIVE_LOCK:
        event = _ACTIVE.get(target)
    if event is not None:
        event.set()
        _trace("cancel", targetRequestId=target, status="CANCEL_REQUESTED")
        _respond(request_id, True, result={"status": "CANCEL_REQUESTED"})
        return
    _trace("cancel", targetRequestId=target, status="NOT_FOUND")
    _respond(request_id, True, result={"status": "NOT_FOUND"})


def _handle_initialize(request_id: str, params: dict[str, Any]) -> None:
    channel = params.get("artifactChannel")
    if isinstance(channel, dict):
        _CONFIG["_channel"] = {
            "baseUrl": channel["baseUrl"],
            "processToken": channel["processToken"],
        }
    result: dict[str, Any] = {
        "providerId": _CONFIG["providerId"],
        "providerVersion": _CONFIG["providerVersion"],
        "catalogVersion": _CONFIG["catalogVersion"],
        "limits": params.get("limits"),
    }
    if isinstance(channel, dict):
        result["artifactChannel"] = {
            "apiVersion": channel["apiVersion"],
            "requestTimeoutMs": channel["requestTimeoutMs"],
            "maxArtifactBytes": channel["maxArtifactBytes"],
            "maxAggregateBytes": channel["maxAggregateBytes"],
            "maxAttachments": channel["maxAttachments"],
        }
    _trace("initialize", channelConfigured=isinstance(channel, dict))
    _respond(request_id, True, result=result)


def _handle_catalog(request_id: str, params: dict[str, Any]) -> None:
    requested = params.get("backendOperationIds") or []
    unsupported_ids = set(_CONFIG.get("unsupported", []))
    omitted_ids = set(_CONFIG.get("catalog_omit", []))
    supported = []
    unsupported = []
    for backend_id in requested:
        if backend_id in omitted_ids:
            continue
        if backend_id in unsupported_ids:
            unsupported.append(
                {"backendOperationId": backend_id, "reason": "NOT_IMPLEMENTED"}
            )
            continue
        binding = _binding(backend_id)
        if binding is None:
            unsupported.append(
                {"backendOperationId": backend_id, "reason": "NOT_IMPLEMENTED"}
            )
            continue
        descriptor: dict[str, Any] = {
            "backendOperationId": backend_id,
            "effect": binding.get("effect", "READ"),
        }
        slots = binding.get("artifactSlots")
        if slots:
            descriptor["artifactSlots"] = slots
        supported.append(descriptor)
    _trace(
        "catalog",
        requested=requested,
        supported=[item["backendOperationId"] for item in supported],
        unsupported=[item["backendOperationId"] for item in unsupported],
    )
    _respond(
        request_id,
        True,
        result={
            "catalogVersion": _CONFIG["catalogVersion"],
            "supported": supported,
            "unsupported": unsupported,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as stream:
        _CONFIG.update(json.load(stream))
    marker = _CONFIG.get("marker")
    if marker:
        with open(marker, "w", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    _trace("start", pid=os.getpid())
    if _CONFIG.get("exit_immediately"):
        return 2
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            return 4
        method = frame.get("method")
        request_id = frame.get("requestId")
        params = frame.get("params") or {}
        if not isinstance(request_id, str) or not isinstance(params, dict):
            return 5
        if method == "initialize":
            _handle_initialize(request_id, params)
        elif method == "catalog":
            _handle_catalog(request_id, params)
        elif method == "invoke":
            threading.Thread(
                target=_handle_invoke,
                args=(request_id, params),
                daemon=True,
            ).start()
        elif method == "cancel":
            _handle_cancel(request_id, params)
        else:
            _respond(
                request_id,
                False,
                error={
                    "code": "PROTOCOL_METHOD_UNSUPPORTED",
                    "message": "method is unsupported",
                },
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())