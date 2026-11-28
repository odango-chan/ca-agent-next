"""SR-010 模块验收：AC-010-01～AC-010-05。

覆盖 Host-owned ArtifactStore、``ca-host.artifact-store/v2`` no-hash channel、
唯一 Plugin Manager 内的 Provider v2 Driver、取消/超时/退出清理，以及
no-decode / 缺 Codec 的 fail-closed 路径。

测试 Provider 是 ``tests/fixtures/provider_v2_fake.py`` 计数型进程；它不是
正式 Provider，也不构成 AC-010-09 互操作证据。运行方式：

    uv run --no-sync --locked --group dev --extra plugins python -m unittest discover -s tests -p test_artifact_channel.py -v
"""

from __future__ import annotations

import json
import shutil
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ca_agent_next.artifacts import (
    ARTIFACT_CHANNEL_API_VERSION,
    ArtifactChannelServer,
    ArtifactDirection,
    ArtifactError,
    ArtifactErrorCode,
    ArtifactLimits,
    ArtifactStore,
)
from ca_agent_next.plugins import (
    ArtifactSlotSpec,
    PluginError,
    PluginErrorCode,
    PluginManager,
    ProviderBindingSpec,
    ProviderLimits,
    ProviderV2Config,
    StdioProviderV2Driver,
    ToolStatus,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FAKE_PROVIDER = Path(__file__).resolve().parent / "fixtures" / "provider_v2_fake.py"
NAS_MEDIA = "application/vnd.3gpp.5gnas"
JSON_MEDIA = "application/json"
PROVIDER_ID = "ca-test.provider"
PROVIDER_VERSION = "2.0.0"
CATALOG_VERSION = "cat-1"


def _new_ref_pattern() -> str:
    return r"^art_[A-Za-z0-9_-]{43}$"


def _http(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], bytes]:
    request = Request(url, method=method, headers=dict(headers or {}), data=body)
    try:
        with urlopen(request, timeout=10) as response:
            return (
                response.status,
                {key.lower(): value for key, value in response.headers.items()},
                response.read(),
            )
    except HTTPError as error:
        try:
            return (
                error.code,
                {key.lower(): value for key, value in error.headers.items()},
                error.read(),
            )
        finally:
            error.close()


def _raw_partial_post(
    host: str,
    port: int,
    *,
    headers: dict[str, str],
    body: bytes,
    declared_length: int,
) -> int:
    """发送短于 Content-Length 的 POST，返回 Host 状态码。"""
    lines = [
        "POST /v2/artifacts HTTP/1.1",
        f"Host: {host}:{port}",
        "Connection: close",
    ]
    lines.extend(f"{key}: {value}" for key, value in headers.items())
    lines.append(f"Content-Length: {declared_length}")
    payload = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + body
    with socket.create_connection((host, port), timeout=10) as connection:
        connection.sendall(payload)
        connection.shutdown(socket.SHUT_WR)
        chunks: list[bytes] = []
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    response = b"".join(chunks)
    first_line = response.split(b"\r\n", 1)[0].decode("latin-1")
    return int(first_line.split(" ")[1])


def _assert_no_digest(headers: dict[str, str]) -> None:
    for key in headers:
        lowered = key.lower()
        if "sha256" in lowered or "digest" in lowered or "checksum" in lowered:
            raise AssertionError(f"unexpected digest header: {key}")


class _StoreTestCase(unittest.TestCase):
    def _store(self, **limit_overrides: object) -> ArtifactStore:
        values = {
            "max_artifact_bytes": 16,
            "max_aggregate_bytes": 32,
            "max_attachments": 4,
            "ttl_seconds": 60.0,
        }
        values.update(limit_overrides)
        limits = ArtifactLimits(**values)  # type: ignore[arg-type]
        store = ArtifactStore(self._tmp, limits=limits)
        self.addCleanup(store.close)
        return store

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="ca-artifact-test-")
        self.addCleanup(shutil.rmtree, self._tmp, True)


class ArtifactStoreTests(_StoreTestCase):
    def test_reference_is_opaque_and_does_not_encode_identity(self) -> None:
        store = self._store()
        store.create_invocation("inv-secret")
        binding = store.publish_input(
            "inv-secret", "n1Message", NAS_MEDIA, b"\x2e\x05\x01\xd1"
        )

        self.assertRegex(binding.artifact_ref, _new_ref_pattern())
        self.assertNotIn("inv-secret", binding.artifact_ref)
        self.assertNotIn("n1Message", binding.artifact_ref)
        self.assertNotIn("/", binding.artifact_ref)
        self.assertNotIn(".", binding.artifact_ref)
        self.assertEqual(binding.byte_length, 4)
        self.assertEqual(binding.media_type, NAS_MEDIA)
        self.assertEqual(binding.direction, ArtifactDirection.INPUT)
        public = binding.public_view()
        self.assertNotIn("path", public)
        self.assertNotIn("url", public)
        self.assertNotIn("digest", public)

    def test_input_round_trip(self) -> None:
        store = self._store()
        store.create_invocation("inv-1")
        binding = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abc")
        self.assertEqual(
            store.read_input(
                binding.artifact_ref, invocation_id="inv-1", slot="n1Message"
            ),
            b"abc",
        )

    def test_cross_invocation_reference_is_rejected(self) -> None:
        store = self._store()
        store.create_invocation("inv-1")
        binding = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abc")
        with self.assertRaises(ArtifactError) as context:
            store.read_input(
                binding.artifact_ref, invocation_id="inv-2", slot="n1Message"
            )
        self.assertEqual(
            context.exception.code, ArtifactErrorCode.ARTIFACT_REFERENCE_INVALID
        )

    def test_direction_and_slot_mismatch_are_rejected(self) -> None:
        store = self._store()
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        source = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abc")
        with self.assertRaises(ArtifactError) as wrong_direction:
            store.authorize(
                source.artifact_ref,
                invocation_id="inv-1",
                slot="n1Message",
                direction=ArtifactDirection.OUTPUT,
            )
        self.assertEqual(
            wrong_direction.exception.code,
            ArtifactErrorCode.ARTIFACT_DIRECTION_MISMATCH,
        )
        with self.assertRaises(ArtifactError) as wrong_slot:
            store.read_input(
                source.artifact_ref, invocation_id="inv-1", slot="decoded"
            )
        self.assertEqual(
            wrong_slot.exception.code, ArtifactErrorCode.ARTIFACT_SLOT_MISMATCH
        )
        output = store.publish_output("inv-1", "decoded", JSON_MEDIA, b"{}")
        with self.assertRaises(ArtifactError) as output_as_input:
            store.read_input(
                output.artifact_ref, invocation_id="inv-1", slot="decoded"
            )
        self.assertEqual(
            output_as_input.exception.code,
            ArtifactErrorCode.ARTIFACT_DIRECTION_MISMATCH,
        )
        self.assertEqual(
            store.read_output(
                output.artifact_ref, invocation_id="inv-1", slot="decoded"
            ),
            b"{}",
        )

    def test_expired_reference_is_rejected_and_removed(self) -> None:
        clock = [1000.0]
        store = ArtifactStore(
            self._tmp,
            limits=ArtifactLimits(ttl_seconds=10),
            clock=lambda: clock[0],
        )
        self.addCleanup(store.close)
        store.create_invocation("inv-1")
        binding = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abc")
        clock[0] += 11
        with self.assertRaises(ArtifactError) as context:
            store.read_input(
                binding.artifact_ref, invocation_id="inv-1", slot="n1Message"
            )
        self.assertEqual(context.exception.code, ArtifactErrorCode.ARTIFACT_EXPIRED)
        self.assertIsNone(store.binding(binding.artifact_ref))
        self.assertEqual(store.stats()["artifacts"], 0)

    def test_per_artifact_quota(self) -> None:
        store = self._store(max_artifact_bytes=4, max_aggregate_bytes=64)
        store.create_invocation("inv-1")
        with self.assertRaises(ArtifactError) as context:
            store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"12345")
        self.assertEqual(
            context.exception.code, ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED
        )

    def test_aggregate_quota(self) -> None:
        store = self._store(max_artifact_bytes=8, max_aggregate_bytes=10)
        store.create_invocation("inv-1")
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"12345678")
        with self.assertRaises(ArtifactError) as context:
            store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        self.assertEqual(
            context.exception.code, ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED
        )
        self.assertEqual(store.stats()["artifacts"], 1)

    def test_attachment_quota(self) -> None:
        store = self._store(
            max_artifact_bytes=4, max_aggregate_bytes=64, max_attachments=2
        )
        store.create_invocation("inv-1")
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"a")
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"b")
        with self.assertRaises(ArtifactError) as context:
            store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"c")
        self.assertEqual(
            context.exception.code, ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED
        )

    def test_release_clears_all_invocation_material(self) -> None:
        store = self._store()
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        source = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abc")
        output = store.publish_output("inv-1", "decoded", JSON_MEDIA, b"{}")
        self.assertEqual(store.release("inv-1", reason="cancelled"), 2)
        self.assertEqual(store.stats()["artifacts"], 0)
        for binding, direction in (
            (source, ArtifactDirection.INPUT),
            (output, ArtifactDirection.OUTPUT),
        ):
            with self.assertRaises(ArtifactError) as context:
                store.authorize(
                    binding.artifact_ref,
                    invocation_id="inv-1",
                    slot=binding.slot,
                    direction=direction,
                )
            self.assertEqual(
                context.exception.code, ArtifactErrorCode.ARTIFACT_NOT_FOUND
            )
        self.assertEqual(store.release("inv-1"), 0)

    def test_oversized_staged_write_aborts_and_frees_slot(self) -> None:
        store = self._store(
            max_artifact_bytes=4, max_aggregate_bytes=16, max_attachments=1
        )
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        staged = store.begin_output("inv-1", "decoded", JSON_MEDIA)
        with self.assertRaises(ArtifactError) as context:
            staged.write(b"12345")
        self.assertEqual(
            context.exception.code, ArtifactErrorCode.ARTIFACT_QUOTA_EXCEEDED
        )
        staged.abort()
        self.assertEqual(store.outputs_for("inv-1"), ())
        retry = store.begin_output("inv-1", "decoded", JSON_MEDIA)
        retry.write(b"ok")
        self.assertEqual(retry.commit().byte_length, 2)

    def test_staged_output_is_not_readable_until_commit(self) -> None:
        store = self._store()
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        staged = store.begin_output("inv-1", "decoded", JSON_MEDIA)
        staged.write(b"ab")
        self.assertEqual(store.outputs_for("inv-1"), ())
        self.assertEqual(store.stats()["artifacts"], 0)
        staged.write(b"c")
        binding = staged.commit()
        self.assertEqual(binding.byte_length, 3)
        outputs = store.outputs_for("inv-1")
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].artifact_ref, binding.artifact_ref)
        self.assertEqual(
            store.read_output(
                binding.artifact_ref, invocation_id="inv-1", slot="decoded"
            ),
            b"abc",
        )

    def test_aborted_output_leaves_no_artifact_and_frees_attachment(self) -> None:
        store = self._store(
            max_artifact_bytes=8, max_aggregate_bytes=16, max_attachments=1
        )
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        staged = store.begin_output("inv-1", "decoded", JSON_MEDIA)
        staged.write(b"ab")
        staged.abort()
        self.assertEqual(store.outputs_for("inv-1"), ())
        self.assertEqual(store.stats()["artifacts"], 0)
        # abort 释放了唯一的 attachment 预留，下一次仍可发布。
        retry = store.begin_output("inv-1", "decoded", JSON_MEDIA)
        retry.write(b"z")
        self.assertEqual(retry.commit().byte_length, 1)


class ArtifactChannelTests(_StoreTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.store = ArtifactStore(
            self._tmp,
            limits=ArtifactLimits(
                max_artifact_bytes=8,
                max_aggregate_bytes=16,
                max_attachments=3,
                request_timeout_ms=2000,
                ttl_seconds=60,
            ),
        )
        self.addCleanup(self.store.close)
        self.channel = ArtifactChannelServer(self.store).start()
        self.addCleanup(self.channel.stop)
        self.contract = self.channel.contract()
        self.store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        self.source = self.store.publish_input(
            "inv-1", "n1Message", NAS_MEDIA, b"\x2e\x05\x01\xd1"
        )

    def _headers(
        self, *, invocation: str = "inv-1", slot: str = "n1Message"
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.contract['processToken']}",
            "X-CA-Invocation": invocation,
            "X-CA-Slot": slot,
        }

    def test_contract_is_closed_v2_no_hash(self) -> None:
        self.assertEqual(
            self.contract["apiVersion"], ARTIFACT_CHANNEL_API_VERSION
        )
        self.assertEqual(ARTIFACT_CHANNEL_API_VERSION, "ca-host.artifact-store/v2")
        self.assertTrue(self.contract["baseUrl"].startswith("http://127.0.0.1:"))
        self.assertNotIn("sha256", json.dumps(self.contract).lower())
        self.assertNotIn("digest", json.dumps(self.contract).lower())

    def test_token_is_required(self) -> None:
        status, _, body = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/{self.source.artifact_ref}",
            headers={"X-CA-Invocation": "inv-1", "X-CA-Slot": "n1Message"},
        )
        self.assertEqual(status, 401)
        self.assertIn(b"ARTIFACT_REFERENCE_INVALID", body)
        status, _, _ = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/{self.source.artifact_ref}",
            headers={
                "Authorization": "Bearer wrong-token",
                "X-CA-Invocation": "inv-1",
                "X-CA-Slot": "n1Message",
            },
        )
        self.assertEqual(status, 401)

    def test_get_returns_exact_bytes_without_digest_headers(self) -> None:
        status, headers, body = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/{self.source.artifact_ref}",
            headers=self._headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body, b"\x2e\x05\x01\xd1")
        self.assertEqual(headers["content-type"], NAS_MEDIA)
        self.assertEqual(headers["content-length"], "4")
        _assert_no_digest(headers)

    def test_get_rejects_wrong_invocation_slot_and_output(self) -> None:
        url = f"{self.contract['baseUrl']}/v2/artifacts/{self.source.artifact_ref}"
        status, _, body = _http(url, headers=self._headers(invocation="inv-2"))
        self.assertEqual(status, 409)
        self.assertIn(b"ARTIFACT_REFERENCE_INVALID", body)
        status, _, body = _http(url, headers=self._headers(slot="decoded"))
        self.assertEqual(status, 409)
        self.assertIn(b"ARTIFACT_SLOT_MISMATCH", body)
        output = self.store.publish_output("inv-1", "decoded", JSON_MEDIA, b"{}")
        status, _, body = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/{output.artifact_ref}",
            headers=self._headers(slot="decoded"),
        )
        self.assertEqual(status, 409)
        self.assertIn(b"ARTIFACT_DIRECTION_MISMATCH", body)

    def test_get_rejects_unknown_and_malformed_references(self) -> None:
        status, _, _ = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/art_" + "A" * 43,
            headers=self._headers(),
        )
        self.assertEqual(status, 404)
        status, _, _ = _http(
            f"{self.contract['baseUrl']}/v2/artifacts/../../etc/passwd",
            headers=self._headers(),
        )
        self.assertEqual(status, 404)

    def test_post_publishes_output_and_returns_opaque_reference(self) -> None:
        headers = self._headers(slot="decoded")
        headers["Content-Type"] = JSON_MEDIA
        status, response_headers, body = _http(
            f"{self.contract['baseUrl']}/v2/artifacts",
            method="POST",
            headers=headers,
            body=b"{}",
        )
        self.assertEqual(status, 201)
        reference = json.loads(body)["artifactRef"]

        self.assertRegex(reference, _new_ref_pattern())
        outputs = self.store.outputs_for("inv-1")
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].artifact_ref, reference)
        self.assertEqual(
            self.store.read_output(reference, invocation_id="inv-1", slot="decoded"),
            b"{}",
        )
        _assert_no_digest(response_headers)

    def test_post_rejects_missing_headers_bad_media_and_quota(self) -> None:
        base = f"{self.contract['baseUrl']}/v2/artifacts"
        headers = self._headers(slot="decoded")
        headers["Content-Type"] = JSON_MEDIA
        status, _, _ = _http(base, method="POST", headers=headers, body=b"")
        # 空 body 是合法 Artifact；仍必须成功原子发布。
        self.assertEqual(status, 201)
        self.store.release("inv-1")
        self.store.create_invocation("inv-2", output_slots={"decoded": JSON_MEDIA})

        headers = self._headers(invocation="inv-2")
        headers["Content-Type"] = JSON_MEDIA
        status, _, body = _http(base, method="POST", headers=headers, body=b"{}")
        self.assertEqual(status, 409)
        self.assertIn(b"ARTIFACT_SLOT_MISMATCH", body)

        headers = self._headers(invocation="inv-2", slot="decoded")
        headers["Content-Type"] = NAS_MEDIA
        status, _, body = _http(base, method="POST", headers=headers, body=b"{}")
        self.assertEqual(status, 415)
        self.assertIn(b"ARTIFACT_MEDIA_TYPE_MISMATCH", body)

        headers = self._headers(invocation="inv-2", slot="decoded")
        headers["Content-Type"] = JSON_MEDIA
        headers["Content-Length"] = "9"
        status, _, body = _http(base, method="POST", headers=headers, body=b"123456789")
        self.assertEqual(status, 413)
        self.assertIn(b"ARTIFACT_QUOTA_EXCEEDED", body)

    def test_post_partial_body_is_discarded(self) -> None:
        headers = self._headers(slot="decoded")
        headers["Content-Type"] = JSON_MEDIA
        status = _raw_partial_post(
            "127.0.0.1",
            int(self.contract["baseUrl"].rsplit(":", 1)[1]),
            headers=headers,
            body=b"ab",
            declared_length=8,
        )
        self.assertEqual(status, 400)
        self.assertEqual(self.store.outputs_for("inv-1"), ())

    def test_expired_reference_returns_410(self) -> None:
        clock = [1000.0]
        store = ArtifactStore(
            self._tmp,
            limits=ArtifactLimits(ttl_seconds=5, request_timeout_ms=2000),
            clock=lambda: clock[0],
        )
        self.addCleanup(store.close)
        channel = ArtifactChannelServer(store).start()
        self.addCleanup(channel.stop)
        store.create_invocation("inv-exp")
        binding = store.publish_input("inv-exp", "n1Message", NAS_MEDIA, b"x")
        clock[0] += 6
        status, _, body = _http(
            f"{channel.contract()['baseUrl']}/v2/artifacts/{binding.artifact_ref}",
            headers={
                "Authorization": f"Bearer {channel.contract()['processToken']}",
                "X-CA-Invocation": "inv-exp",
                "X-CA-Slot": "n1Message",
            },
        )
        self.assertEqual(status, 410)
        self.assertIn(b"ARTIFACT_EXPIRED", body)


class _ProviderTestCase(_StoreTestCase):
    def _make_driver(
        self,
        *,
        with_channel: bool = True,
        mode: str = "normal",
        unsupported: list[str] | None = None,
        catalog_omit: list[str] | None = None,
        provider_version: str = PROVIDER_VERSION,
        artifact_limits: ArtifactLimits | None = None,
        register: bool = True,
    ) -> tuple[StdioProviderV2Driver, PluginManager, Path, Path]:
        tmp = Path(self._tmp)
        trace = tmp / "trace.jsonl"
        marker = tmp / "marker"
        fake_bindings = [
            {
                "backendOperationId": "backend.codec",
                "effect": "READ",
                "artifactSlots": {
                    "inputs": [
                        {
                            "pointer": "/n1_sm",
                            "slot": "n1Message",
                            "mediaType": NAS_MEDIA,
                            "required": True,
                        }
                    ],
                    "outputs": [
                        {
                            "pointer": "/decoded",
                            "slot": "decoded",
                            "mediaType": JSON_MEDIA,
                            "required": True,
                        }
                    ],
                },
            },
            {"backendOperationId": "backend.plain", "effect": "READ"},
            {
                "backendOperationId": "backend.optional",
                "effect": "READ",
                "artifactSlots": {
                    "inputs": [
                        {
                            "pointer": "/n1_sm",
                            "slot": "n1Message",
                            "mediaType": NAS_MEDIA,
                            "required": False,
                        }
                    ]
                },
            },
        ]
        config_path = tmp / "provider-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "providerId": PROVIDER_ID,
                    "providerVersion": PROVIDER_VERSION,
                    "catalogVersion": CATALOG_VERSION,
                    "bindings": fake_bindings,
                    "unsupported": list(unsupported or []),
                    "catalog_omit": list(catalog_omit or []),
                    "mode": mode,
                    "outputHex": "0a0b0c",
                    "trace": str(trace),
                    "marker": str(marker),
                }
            ),
            encoding="utf-8",
        )
        host_bindings = (
            ProviderBindingSpec(
                "test.codec.decode",
                "backend.codec",
                input_slots=(
                    ArtifactSlotSpec("/n1_sm", "n1Message", NAS_MEDIA, True),
                ),
                output_slots=(
                    ArtifactSlotSpec("/decoded", "decoded", JSON_MEDIA, True),
                ),
            ),
            ProviderBindingSpec("test.plain.read", "backend.plain"),
            ProviderBindingSpec(
                "test.codec.optional",
                "backend.optional",
                input_slots=(
                    ArtifactSlotSpec("/n1_sm", "n1Message", NAS_MEDIA, False),
                ),
            ),
        )
        limits = ArtifactLimits(
            max_artifact_bytes=64,
            max_aggregate_bytes=256,
            max_attachments=4,
            request_timeout_ms=5000,
            ttl_seconds=60,
        )
        if artifact_limits is not None:
            limits = artifact_limits
        config = ProviderV2Config(
            provider_id=PROVIDER_ID,
            provider_version=provider_version,
            catalog_version=CATALOG_VERSION,
            executable=sys.executable,
            args=(str(FAKE_PROVIDER), "--config", str(config_path)),
            cwd=str(REPO_ROOT),
            bindings=host_bindings,
            limits=ProviderLimits(
                max_frame_bytes=256 * 1024,
                max_in_flight=4,
                max_call_duration_ms=5000,
            ),
            artifact_limits=limits if with_channel else None,
            artifact_root=tmp / "artifact-store",
            initialize_timeout=5.0,
            request_timeout=5.0,
            shutdown_timeout=2.0,
        )
        driver = StdioProviderV2Driver(config)
        manager = PluginManager(object())
        self.addCleanup(manager.shutdown_all)
        if register:
            manager.register_driver(driver)
        return driver, manager, trace, marker

    @staticmethod
    def _trace(path: Path) -> list[dict[str, object]]:
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _wait_trace(
        self, path: Path, event: str, timeout: float = 5.0
    ) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for record in self._trace(path):
                if record.get("event") == event:
                    return record
            time.sleep(0.02)
        self.fail(f"trace event {event!r} was not observed")


class ProviderV2InitializeTests(_ProviderTestCase):
    def test_manager_initializes_provider_and_partitions_bindings(self) -> None:
        driver, manager, trace, marker = self._make_driver()
        self.assertTrue(marker.is_file())
        self.assertEqual(driver.state, "READY")
        self.assertEqual(driver.binding_status("test.codec.decode"), "READY")
        self.assertEqual(driver.binding_status("test.plain.read"), "READY")
        self.assertEqual(
            set(driver.available_callables()),
            {"test.codec.decode", "test.plain.read", "test.codec.optional"},
        )
        self.assertEqual(driver.counters["initialize"], 1)
        self.assertEqual(driver.counters["catalog"], 1)
        events = [record["event"] for record in self._trace(trace)]
        self.assertEqual(events[:3], ["start", "initialize", "catalog"])
        self.assertIn(PROVIDER_ID, manager.plugin_ids())

    def test_missing_channel_marks_artifact_bindings_not_configured(self) -> None:
        driver, manager, trace, _ = self._make_driver(with_channel=False)
        self.assertEqual(driver.binding_status("test.codec.decode"), "NOT_CONFIGURED")
        self.assertEqual(driver.binding_status("test.plain.read"), "READY")
        outcome = manager.invoke_tool(
            PROVIDER_ID,
            "test.plain.read",
            {},
            invocation_id="inv-plain",
            timeout=5,
        )
        self.assertEqual(outcome.status, ToolStatus.RESULT)
        self.assertEqual(outcome.result["codecCalls"], 0)
        self.assertEqual(outcome.result["channelConfigured"], False)
        self.assertEqual(driver.counters["invoke"], 1)
        self.assertNotIn("artifactGets", driver.counters)
        with self.assertRaises(PluginError) as context:
            manager.invoke_tool(
                PROVIDER_ID,
                "test.codec.decode",
                {},
                invocation_id="inv-codec",
                timeout=5,
            )
        self.assertEqual(
            context.exception.code, PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED
        )
        self.assertEqual(driver.counters["invoke"], 1)
        invoke_events = [
            record
            for record in self._trace(trace)
            if record["event"] == "invoke_start"
        ]
        self.assertEqual(len(invoke_events), 1)

    def test_invalid_channel_configuration_fails_before_process_start(self) -> None:
        with self.assertRaises(PluginError) as context:
            self._make_driver(
                artifact_limits=ArtifactLimits(max_artifact_bytes=0)
            )
        self.assertEqual(
            context.exception.code,
            PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
        )
        self.assertFalse((Path(self._tmp) / "marker").exists())

    def test_invalid_channel_bounds_fail_before_process_start(self) -> None:
        with self.assertRaises(PluginError) as context:
            self._make_driver(
                artifact_limits=ArtifactLimits(
                    max_artifact_bytes=16, max_aggregate_bytes=8
                )
            )
        self.assertEqual(
            context.exception.code,
            PluginErrorCode.PROVIDER_CONFIGURATION_INVALID,
        )
        self.assertFalse((Path(self._tmp) / "marker").exists())

    def test_unsupported_backend_is_not_available(self) -> None:
        driver, manager, trace, _ = self._make_driver(
            unsupported=["backend.codec"]
        )
        self.assertEqual(
            driver.binding_status("test.codec.decode"), "NOT_IMPLEMENTED"
        )
        with self.assertRaises(PluginError) as context:
            manager.invoke_tool(
                PROVIDER_ID,
                "test.codec.decode",
                {},
                invocation_id="inv-codec",
                timeout=5,
            )
        self.assertEqual(
            context.exception.code, PluginErrorCode.BACKEND_OPERATION_UNSUPPORTED
        )
        self.assertEqual(driver.counters["invoke"], 0)
        self.assertEqual(
            [record for record in self._trace(trace) if record["event"] == "invoke_start"],
            [],
        )

    def test_catalog_must_partition_every_requested_backend(self) -> None:
        with self.assertRaises(PluginError) as context:
            self._make_driver(catalog_omit=["backend.plain"])
        self.assertEqual(
            context.exception.code,
            PluginErrorCode.PROVIDER_BINDING_CATALOG_INVALID,
        )

    def test_provider_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaises(PluginError) as context:
            self._make_driver(provider_version="9.9.9")
        self.assertEqual(
            context.exception.code, PluginErrorCode.HANDSHAKE_MISMATCH
        )
        self.assertTrue((Path(self._tmp) / "marker").exists())

    def test_duplicate_driver_registration_is_rejected(self) -> None:
        driver, manager, _, _ = self._make_driver()
        with self.assertRaises(PluginError) as context:
            manager.register_driver(StdioProviderV2Driver(driver._config))
        self.assertEqual(context.exception.code, PluginErrorCode.INVALID_ARGUMENT)


class ProviderV2InvokeTests(_ProviderTestCase):
    def test_invoke_reads_input_and_publishes_output_through_v2_channel(self) -> None:
        driver, manager, trace, _ = self._make_driver()
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input(
            "inv-1", "n1Message", NAS_MEDIA, b"\x2e\x05\x01\xd1"
        )
        outcome = manager.invoke_tool(
            PROVIDER_ID,
            "test.codec.decode",
            {},
            invocation_id="inv-1",
            timeout=5,
        )
        self.assertEqual(outcome.status, ToolStatus.RESULT)
        self.assertEqual(outcome.result["received"][0]["status"], 200)
        self.assertEqual(outcome.result["received"][0]["byteLength"], 4)
        self.assertEqual(
            outcome.result["received"][0]["contentType"], NAS_MEDIA
        )
        self.assertFalse(outcome.result["received"][0]["digestHeader"])
        self.assertEqual(outcome.result["codecCalls"], 1)
        self.assertEqual(outcome.result["outputPostStatus"], 201)
        outputs = store.outputs_for("inv-1")
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].slot, "decoded")
        self.assertEqual(
            store.read_output(
                outputs[0].artifact_ref,
                invocation_id="inv-1",
                slot="decoded",
            ),
            b"\x0a\x0b\x0c",
        )
        self.assertEqual(driver.counters["artifactGets"], 1)
        self.assertEqual(driver.counters["artifactPosts"], 1)
        get_events = [
            record for record in self._trace(trace) if record["event"] == "artifact_get"
        ]
        self.assertEqual(len(get_events), 1)
        self.assertFalse(get_events[0]["digestHeader"])

    def test_cross_invocation_artifact_is_rejected_before_invoke(self) -> None:
        driver, manager, trace, _ = self._make_driver()
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-a", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-a", "n1Message", NAS_MEDIA, b"abcd")
        with self.assertRaises(PluginError) as context:
            manager.invoke_tool(
                PROVIDER_ID,
                "test.codec.decode",
                {},
                invocation_id="inv-b",
                timeout=5,
            )
        self.assertEqual(
            context.exception.code, PluginErrorCode.ARTIFACT_REFERENCE_INVALID
        )
        self.assertEqual(driver.counters["invoke"], 0)
        self.assertEqual(
            [
                record
                for record in self._trace(trace)
                if record["event"] == "invoke_start"
            ],
            [],
        )

    def test_missing_required_input_is_rejected_before_invoke(self) -> None:
        driver, manager, _, _ = self._make_driver()
        with self.assertRaises(PluginError) as context:
            manager.invoke_tool(
                PROVIDER_ID,
                "test.codec.decode",
                {},
                invocation_id="inv-empty",
                timeout=5,
            )
        self.assertEqual(
            context.exception.code, PluginErrorCode.ARTIFACT_REFERENCE_INVALID
        )
        self.assertEqual(driver.counters["invoke"], 0)

    def test_caller_supplied_artifact_ref_is_never_forwarded(self) -> None:
        driver, manager, _, _ = self._make_driver()
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        forged = "art_" + "A" * 43
        outcome = manager.invoke_tool(
            PROVIDER_ID,
            "test.codec.optional",
            {"/n1_sm": {"artifactRef": forged}},
            invocation_id="inv-1",
            timeout=5,
        )
        self.assertEqual(outcome.status, ToolStatus.RESULT)
        self.assertEqual(outcome.result["received"], [])
        self.assertEqual(outcome.result["codecCalls"], 0)
        self.assertEqual(driver.counters["artifactGets"], 0)

    def test_authorized_ref_replaces_caller_field(self) -> None:
        driver, manager, _, _ = self._make_driver()
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"\x2e\x05\x01\xd1")
        forged = "art_" + "A" * 43
        outcome = manager.invoke_tool(
            PROVIDER_ID,
            "test.codec.decode",
            {"/n1_sm": {"artifactRef": forged}},
            invocation_id="inv-1",
            timeout=5,
        )
        self.assertEqual(outcome.status, ToolStatus.RESULT)
        self.assertEqual(outcome.result["received"][0]["byteLength"], 4)
        self.assertNotEqual(
            outcome.result["received"][0]["status"], 404
        )

    def test_partial_output_upload_is_discarded(self) -> None:
        driver, manager, _, _ = self._make_driver(mode="partial_upload")
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        outcome = manager.invoke_tool(
            PROVIDER_ID,
            "test.codec.decode",
            {},
            invocation_id="inv-1",
            timeout=5,
        )
        self.assertEqual(outcome.status, ToolStatus.RESULT)
        self.assertEqual(outcome.result["outputPostStatus"], 400)
        self.assertEqual(store.outputs_for("inv-1"), ())
        self.assertEqual(driver.counters["artifactPosts"], 0)


class ProviderV2LifecycleTests(_ProviderTestCase):
    def test_cancel_releases_invocation_artifacts(self) -> None:
        driver, manager, trace, _ = self._make_driver(mode="slow_invoke")
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        source = store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        handle = manager.invoke_tool_async(
            PROVIDER_ID, "test.codec.decode", {}, invocation_id="inv-1"
        )
        self._wait_trace(trace, "invoke_start")
        cancelled = manager.cancel_operation(
            PROVIDER_ID, "inv-1", reason="test", timeout=5
        )
        self.assertEqual(cancelled.disposition, "cancelled")
        self.assertEqual(store.inputs_for("inv-1"), ())
        self.assertIsNone(store.binding(source.artifact_ref))
        outcome = handle.wait(5)
        self.assertEqual(outcome.status, ToolStatus.CANCELLED)
        self.assertEqual(driver.state, "READY")

    def test_timeout_terminates_provider_and_releases_artifacts(self) -> None:
        driver, manager, _, _ = self._make_driver(mode="slow_invoke")
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        handle = manager.invoke_tool_async(
            PROVIDER_ID, "test.codec.decode", {}, invocation_id="inv-1"
        )
        outcome = handle.wait(0.5)
        self.assertEqual(outcome.status, ToolStatus.TIMEOUT)
        self.assertEqual(store.inputs_for("inv-1"), ())
        self.assertEqual(driver.state, "STOPPED")

    def test_provider_exit_mid_invoke_cleans_pending(self) -> None:
        driver, manager, _, _ = self._make_driver(mode="exit_on_invoke")
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        handle = manager.invoke_tool_async(
            PROVIDER_ID, "test.codec.decode", {}, invocation_id="inv-1"
        )
        outcome = handle.wait(5)
        self.assertEqual(outcome.status, ToolStatus.ABORTED)
        self.assertEqual(store.inputs_for("inv-1"), ())
        self.assertEqual(driver.state, "STOPPED")
        self.assertEqual(driver.counters["protocolViolations"], 0)

    def test_close_releases_all_invocation_material(self) -> None:
        driver, manager, _, _ = self._make_driver()
        store = driver.artifact_store
        assert store is not None
        store.create_invocation("inv-1", output_slots={"decoded": JSON_MEDIA})
        store.publish_input("inv-1", "n1Message", NAS_MEDIA, b"abcd")
        manager.shutdown_all()
        self.assertEqual(driver.state, "STOPPED")
        self.assertTrue(store.closed)
        self.assertEqual(store.inputs_for("inv-1"), ())


if __name__ == "__main__":
    unittest.main()