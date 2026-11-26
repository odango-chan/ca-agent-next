"""SR-002 独立单元测试。

覆盖 AC-002-01～AC-002-08：包身份、公共类型、ModelClient 注入与调用次数、
Smoke 成功路径、失败路径与 CLI 诊断、unittest 执行、无 Provider/网络依赖、
业务中立与提议不执行。

只通过公开入口（包根、规范模块、``Host.handle_event``、``main``）验证。
"""

from __future__ import annotations

import io
import json
import math
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
from decimal import Decimal
from importlib import metadata
from pathlib import Path
from unittest import mock

import ca_agent_next
from ca_agent_next import (
    AgentLoop,
    Context,
    Event,
    Host,
    HostError,
    HostResult,
    ModelClient,
    ModelProposal,
    ModelRequest,
    Run,
)
from ca_agent_next.__main__ import main

_UNSET = object()

SMOKE_STDOUT = (
    '{"schema_version":1,"status":"ok","event_id":"smoke-event-001",'
    '"model_calls":1,"proposal":{"kind":"smoke.echo","payload":'
    '{"message":"smoke-ok"}}}\n'
)
CLI_USAGE_STDERR = (
    '{"schema_version":1,"error":{"code":"CLI_USAGE_ERROR",'
    '"message":"invalid command line usage"}}\n'
)


class FakeModelClient:
    """记录完整请求、调用次数、返回值或异常。"""

    def __init__(self, proposal: object = _UNSET, error: BaseException | None = None) -> None:
        self.requests: list[ModelRequest] = []
        self.calls = 0
        self.proposal = (
            ModelProposal(kind="test.echo", payload={"ok": True})
            if proposal is _UNSET
            else proposal
        )
        self.error = error

    def propose(self, request: ModelRequest) -> object:
        self.calls += 1
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.proposal


def make_event(**overrides: object) -> Event:
    data: dict[str, object] = {
        "event_id": "event-001",
        "ingress_id": "ingress-001",
        "event_type": "test.event",
        "payload": {"message": "hello"},
        "source": {"protocol": "test", "peerId": "local"},
    }
    data.update(overrides)
    return Event(**data)  # type: ignore[arg-type]


class HostErrorAssertions(unittest.TestCase):
    def assert_host_error(
        self,
        exc: BaseException,
        code: str,
        message: str,
    ) -> None:
        self.assertIsInstance(exc, HostError)
        assert isinstance(exc, HostError)
        self.assertEqual(exc.code, code)
        self.assertEqual(exc.safe_message, message)
        self.assertEqual(str(exc), message)

    def assert_event_invalid(self, event: object) -> None:
        fake = FakeModelClient()
        factory = mock.Mock(return_value="run-001")
        host = Host(fake, run_id_factory=factory)
        with self.assertRaises(HostError) as ctx:
            host.handle_event(event)  # type: ignore[arg-type]
        self.assert_host_error(ctx.exception, "EVENT_INVALID", "event is invalid")
        self.assertEqual(fake.calls, 0)
        factory.assert_not_called()

    def assert_proposal_invalid(self, proposal: object) -> None:
        fake = FakeModelClient(proposal=proposal)
        factory = mock.Mock(return_value="run-001")
        host = Host(fake, run_id_factory=factory)
        with self.assertRaises(HostError) as ctx:
            host.handle_event(make_event())
        self.assert_host_error(
            ctx.exception, "MODEL_PROPOSAL_INVALID", "model proposal is invalid"
        )
        self.assertEqual(fake.calls, 1)
        factory.assert_called_once_with()


class PackageIdentityTests(unittest.TestCase):
    """AC-002-01：Python 包安装、发行包身份、导入路径。"""

    def test_public_exports_and_all_order(self) -> None:
        self.assertEqual(
            list(ca_agent_next.__all__),
            [
                "JSONValue",
                "Event",
                "Context",
                "Run",
                "ModelRequest",
                "ModelProposal",
                "HostResult",
                "ModelClient",
                "AgentLoop",
                "Host",
                "HostError",
            ],
        )
        for name in ca_agent_next.__all__:
            self.assertTrue(hasattr(ca_agent_next, name), name)

    def test_canonical_module_paths_export_types(self) -> None:
        from ca_agent_next import contracts, host, model_client, model_loop

        for name in (
            "JSONValue",
            "Event",
            "Context",
            "Run",
            "ModelRequest",
            "ModelProposal",
            "HostResult",
            "HostError",
        ):
            self.assertTrue(hasattr(contracts, name), name)
        self.assertIs(model_client.ModelClient, ModelClient)
        self.assertIs(model_loop.AgentLoop, AgentLoop)
        self.assertIs(host.Host, Host)
        self.assertIs(host.HostError, contracts.HostError)
        self.assertIs(ca_agent_next.HostError, contracts.HostError)

    def test_host_error_is_single_type_defined_in_contracts(self) -> None:
        from ca_agent_next import contracts, host, model_loop

        self.assertIs(contracts.HostError, host.HostError)
        self.assertIs(contracts.HostError, model_loop.HostError)
        self.assertIs(ca_agent_next.HostError, host.HostError)
        self.assertEqual(contracts.HostError.__module__, "ca_agent_next.contracts")

    def test_distribution_metadata(self) -> None:
        dist = metadata.distribution("ca-agent-next")
        self.assertEqual(dist.metadata["Name"], "ca-agent-next")
        self.assertEqual(dist.version, "0.1.0")
        self.assertEqual(dist.metadata["Requires-Python"], ">=3.11")
        self.assertIsNone(dist.metadata.get("Requires-Dist"))

    def test_import_package_uses_src_layout(self) -> None:
        package_dir = Path(ca_agent_next.__file__).resolve().parent
        self.assertEqual(package_dir.name, "ca_agent_next")
        self.assertEqual(package_dir.parent.name, "src")


class ContractTypeTests(unittest.TestCase):
    """AC-002-02：公共类型、字段默认值、冻结语义与 HostError 身份。"""

    def test_event_source_defaults_to_empty_mapping(self) -> None:
        event = Event(
            event_id="e-1",
            ingress_id="i-1",
            event_type="t",
            payload={"k": "v"},
        )
        self.assertEqual(dict(event.source), {})
        self.assertEqual(dict(event.payload), {"k": "v"})
        self.assertEqual(event.artifact_refs, ())
        self.assertIsNone(event.external_request_id)
        self.assertIsNone(event.response_channel_id)

    def test_event_payload_is_required(self) -> None:
        with self.assertRaises(TypeError):
            Event(event_id="e-1", ingress_id="i-1", event_type="t")  # type: ignore[call-arg]

    def test_context_defaults_to_empty_mapping(self) -> None:
        self.assertEqual(dict(Context().values), {})

    def test_public_dataclasses_are_frozen(self) -> None:
        event = make_event()
        context = Context()
        run = Run(run_id="r-1", event_id="e-1")
        request = ModelRequest(run=run, event=event, context=context)
        proposal = ModelProposal(kind="k", payload={})
        result = HostResult(run=run, proposal=proposal)
        for obj, attr in (
            (event, "event_id"),
            (context, "values"),
            (run, "run_id"),
            (request, "run"),
            (proposal, "kind"),
            (result, "proposal"),
        ):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, attr, "changed")

    def test_host_error_accepts_only_fixed_codes_and_messages(self) -> None:
        for code, message in (
            ("EVENT_INVALID", "event is invalid"),
            ("MODEL_CLIENT_FAILED", "model client failed"),
            ("MODEL_PROPOSAL_INVALID", "model proposal is invalid"),
            ("HOST_INTERNAL_ERROR", "host internal error"),
        ):
            err = HostError(code, message)
            self.assertEqual(err.code, code)
            self.assertEqual(err.safe_message, message)
            self.assertEqual(str(err), message)

        with self.assertRaises(ValueError):
            HostError("UNKNOWN_CODE", "event is invalid")
        with self.assertRaises(ValueError):
            HostError("CLI_USAGE_ERROR", "invalid command line usage")
        with self.assertRaises(ValueError):
            HostError("EVENT_INVALID", "something else")

    def test_host_error_is_exception(self) -> None:
        self.assertTrue(issubclass(HostError, Exception))


class HostSuccessTests(HostErrorAssertions):
    """AC-002-02/03：Host 最小处理流程、空 Context、一次模型调用。"""

    def test_handle_event_returns_result_and_calls_model_once(self) -> None:
        event = make_event()
        proposal = ModelProposal(kind="test.echo", payload={"ok": True})
        fake = FakeModelClient(proposal=proposal)
        host = Host(fake, run_id_factory=lambda: "run-001")

        result = host.handle_event(event)

        self.assertIsInstance(result, HostResult)
        self.assertEqual(result.run, Run(run_id="run-001", event_id="event-001"))
        self.assertIs(result.proposal, proposal)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(len(fake.requests), 1)

        request = fake.requests[0]
        self.assertIsInstance(request, ModelRequest)
        self.assertIs(request.event, event)
        self.assertIs(request.run, result.run)
        self.assertIsInstance(request.context, Context)
        self.assertEqual(dict(request.context.values), {})

    def test_context_is_created_empty_and_does_not_copy_event_fields(self) -> None:
        event = make_event(
            payload={"message": "hello", "nested": {"a": 1}},
            source={"protocol": "test"},
            external_request_id="ext-1",
            response_channel_id="channel-1",
            artifact_refs=("artifact-1",),
        )
        fake = FakeModelClient()
        host = Host(fake, run_id_factory=lambda: "run-ctx")
        host.handle_event(event)
        self.assertEqual(dict(fake.requests[0].context.values), {})

    def test_artifact_refs_are_passed_through_unchanged(self) -> None:
        event = make_event(artifact_refs=("ref-a", "ref-b"))
        fake = FakeModelClient()
        Host(fake, run_id_factory=lambda: "run-1").handle_event(event)
        self.assertEqual(fake.requests[0].event.artifact_refs, ("ref-a", "ref-b"))

    def test_nested_json_payload_is_preserved(self) -> None:
        payload = {
            "none": None,
            "true": True,
            "false": False,
            "int": 42,
            "float": 1.5,
            "str": "text",
            "list": [None, True, 1, 2.5, "s", [], {}],
            "map": {"nested": {"deep": [1, {"k": "v"}]}},
        }
        event = make_event(payload=payload)
        fake = FakeModelClient()
        Host(fake, run_id_factory=lambda: "run-1").handle_event(event)
        self.assertEqual(fake.requests[0].event.payload, payload)
        self.assertIs(fake.requests[0].event.payload["true"], True)

    def test_default_run_id_is_uuid4_hex(self) -> None:
        fake = FakeModelClient()
        host = Host(fake)
        first = host.handle_event(make_event())
        second = host.handle_event(make_event())
        self.assertRegex(first.run.run_id, re.compile(r"^[0-9a-f]{32}$"))
        self.assertRegex(second.run.run_id, re.compile(r"^[0-9a-f]{32}$"))
        self.assertNotEqual(first.run.run_id, second.run.run_id)

    def test_each_handle_event_creates_one_run_and_one_call(self) -> None:
        fake = FakeModelClient()
        factory = mock.Mock(side_effect=["run-1", "run-2"])
        host = Host(fake, run_id_factory=factory)
        event = make_event()
        first = host.handle_event(event)
        second = host.handle_event(event)
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(fake.calls, 2)
        self.assertEqual(first.run.run_id, "run-1")
        self.assertEqual(second.run.run_id, "run-2")
        self.assertIsNot(first.run, second.run)

    def test_event_payload_is_not_mutated(self) -> None:
        event = make_event(payload={"message": "hello"})
        before = dict(event.payload)
        Host(FakeModelClient(), run_id_factory=lambda: "run-1").handle_event(event)
        self.assertEqual(dict(event.payload), before)


class EventValidationTests(HostErrorAssertions):
    """AC-002-02/05：Event 字段与递归 JSONValue 校验。"""

    def test_non_event_objects_are_rejected(self) -> None:
        for value in (None, {}, object(), "event"):
            with self.subTest(value=value):
                self.assert_event_invalid(value)

    def test_blank_identity_fields_are_rejected(self) -> None:
        for field in ("event_id", "ingress_id", "event_type"):
            for value in ("", "   ", "\t\n"):
                with self.subTest(field=field, value=value):
                    self.assert_event_invalid(make_event(**{field: value}))
            with self.subTest(field=field, value=123):
                self.assert_event_invalid(make_event(**{field: 123}))

    def test_payload_must_be_mapping(self) -> None:
        for value in ([], "payload", 1, None, ("a",)):
            with self.subTest(value=value):
                self.assert_event_invalid(make_event(payload=value))

    def test_source_must_be_mapping_when_provided(self) -> None:
        for value in (None, [], "source", 1):
            with self.subTest(value=value):
                self.assert_event_invalid(make_event(source=value))

    def test_optional_ids_allow_none_or_non_blank_strings(self) -> None:
        for field in ("external_request_id", "response_channel_id"):
            for value in ("", "   ", 123, []):
                with self.subTest(field=field, value=value):
                    self.assert_event_invalid(make_event(**{field: value}))
        fake = FakeModelClient()
        Host(fake, run_id_factory=lambda: "run-1").handle_event(
            make_event(external_request_id="ext-1", response_channel_id="channel-1")
        )
        self.assertEqual(fake.calls, 1)

    def test_artifact_refs_must_be_non_blank_string_tuple(self) -> None:
        for value in (
            ["ref"],
            ("",),
            ("   ",),
            (1,),
            "ref",
            None,
        ):
            with self.subTest(value=value):
                self.assert_event_invalid(make_event(artifact_refs=value))
        fake = FakeModelClient()
        Host(fake, run_id_factory=lambda: "run-1").handle_event(
            make_event(artifact_refs=("ref",))
        )
        self.assertEqual(fake.calls, 1)

    def test_non_finite_floats_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.assert_event_invalid(make_event(payload={"v": value}))

    def test_non_string_mapping_keys_are_rejected(self) -> None:
        for payload in ({1: "v"}, {"outer": {2: "v"}}, {None: "v"}):
            with self.subTest(payload=payload):
                self.assert_event_invalid(make_event(payload=payload))

    def test_non_json_objects_are_rejected(self) -> None:
        for value in (
            b"bytes",
            bytearray(b"bytes"),
            Path("file.txt"),
            Decimal("1.5"),
            {1, 2},
            (1, 2),
            object(),
            complex(1, 2),
        ):
            with self.subTest(value=type(value).__name__):
                self.assert_event_invalid(make_event(payload={"v": value}))

    def test_cyclic_containers_are_rejected(self) -> None:
        cyclic_list: list[object] = []
        cyclic_list.append(cyclic_list)
        self.assert_event_invalid(make_event(payload={"v": cyclic_list}))

        cyclic_map: dict[str, object] = {}
        cyclic_map["self"] = cyclic_map
        self.assert_event_invalid(make_event(payload=cyclic_map))

        left: dict[str, object] = {}
        right: dict[str, object] = {"left": left}
        left["right"] = right
        self.assert_event_invalid(make_event(payload={"v": left}))

    def test_invalid_event_does_not_call_model_or_run_id_factory(self) -> None:
        fake = FakeModelClient()
        factory = mock.Mock(return_value="run-1")
        host = Host(fake, run_id_factory=factory)
        with self.assertRaises(HostError) as ctx:
            host.handle_event(make_event(event_id=""))
        self.assert_host_error(ctx.exception, "EVENT_INVALID", "event is invalid")
        self.assertEqual(fake.calls, 0)
        factory.assert_not_called()


class RunIdFactoryTests(HostErrorAssertions):
    """AC-002-05：run_id 工厂调用次数与失败映射。"""

    def test_factory_is_called_exactly_once_after_validation(self) -> None:
        fake = FakeModelClient()
        factory = mock.Mock(return_value="run-xyz")
        host = Host(fake, run_id_factory=factory)
        result = host.handle_event(make_event())
        factory.assert_called_once_with()
        self.assertEqual(result.run.run_id, "run-xyz")
        self.assertEqual(fake.calls, 1)

    def test_factory_exception_maps_to_host_internal_error(self) -> None:
        fake = FakeModelClient()
        host = Host(fake, run_id_factory=mock.Mock(side_effect=RuntimeError("boom")))
        with self.assertRaises(HostError) as ctx:
            host.handle_event(make_event())
        self.assert_host_error(
            ctx.exception, "HOST_INTERNAL_ERROR", "host internal error"
        )
        self.assertEqual(fake.calls, 0)

    def test_invalid_factory_results_map_to_host_internal_error(self) -> None:
        for value in ("", "   ", 123, None, b"run"):
            with self.subTest(value=value):
                fake = FakeModelClient()
                host = Host(fake, run_id_factory=lambda: value)  # type: ignore[arg-type,return-value]
                with self.assertRaises(HostError) as ctx:
                    host.handle_event(make_event())
                self.assert_host_error(
                    ctx.exception, "HOST_INTERNAL_ERROR", "host internal error"
                )
                self.assertEqual(fake.calls, 0)


class ModelClientBoundaryTests(HostErrorAssertions):
    """AC-002-03/05：注入、恰好一次、异常映射、无重试。"""

    def test_model_client_is_injected_and_request_is_recorded(self) -> None:
        fake = FakeModelClient()
        host = Host(fake, run_id_factory=lambda: "run-1")
        event = make_event()
        host.handle_event(event)
        request = fake.requests[0]
        self.assertEqual(request.run.run_id, "run-1")
        self.assertIs(request.event, event)
        self.assertEqual(dict(request.context.values), {})

    def test_client_exception_maps_to_model_client_failed_once(self) -> None:
        fake = FakeModelClient(error=RuntimeError("secret-token=abc"))
        host = Host(fake, run_id_factory=lambda: "run-1")
        with self.assertRaises(HostError) as ctx:
            host.handle_event(make_event())
        self.assert_host_error(
            ctx.exception, "MODEL_CLIENT_FAILED", "model client failed"
        )
        self.assertEqual(fake.calls, 1)
        self.assertNotIn("secret-token", str(ctx.exception))
        self.assertNotIn("RuntimeError", str(ctx.exception))

    def test_client_host_error_is_also_mapped_to_model_client_failed(self) -> None:
        fake = FakeModelClient(
            error=HostError("HOST_INTERNAL_ERROR", "host internal error")
        )
        host = Host(fake, run_id_factory=lambda: "run-1")
        with self.assertRaises(HostError) as ctx:
            host.handle_event(make_event())
        self.assert_host_error(
            ctx.exception, "MODEL_CLIENT_FAILED", "model client failed"
        )
        self.assertEqual(fake.calls, 1)

    def test_client_is_not_retried_after_failure(self) -> None:
        fake = FakeModelClient(error=ValueError("nope"))
        host = Host(fake, run_id_factory=lambda: "run-1")
        for _ in range(3):
            with self.assertRaises(HostError):
                host.handle_event(make_event())
        self.assertEqual(fake.calls, 3)


class ProposalValidationTests(HostErrorAssertions):
    """AC-002-05：Proposal 类型、kind 和 payload 校验。"""

    def test_invalid_proposal_values_are_rejected(self) -> None:
        cyclic: list[object] = []
        cyclic.append(cyclic)
        invalid_values: list[object] = [
            None,
            object(),
            {"kind": "k", "payload": {}},
            ModelProposal(kind="", payload={}),
            ModelProposal(kind="   ", payload={}),
            ModelProposal(kind=123, payload={}),  # type: ignore[arg-type]
            ModelProposal(kind="k", payload=[]),  # type: ignore[arg-type]
            ModelProposal(kind="k", payload=None),  # type: ignore[arg-type]
            ModelProposal(kind="k", payload={"v": object()}),
            ModelProposal(kind="k", payload={"v": math.nan}),
            ModelProposal(kind="k", payload={1: "v"}),
            ModelProposal(kind="k", payload={"v": cyclic}),
        ]
        for proposal in invalid_values:
            with self.subTest(proposal=proposal):
                self.assert_proposal_invalid(proposal)

    def test_valid_nested_proposal_is_returned_unchanged(self) -> None:
        proposal = ModelProposal(
            kind="test.proposal",
            payload={"steps": [{"name": "echo", "args": {"text": "hi"}}]},
        )
        fake = FakeModelClient(proposal=proposal)
        result = Host(fake, run_id_factory=lambda: "run-1").handle_event(make_event())
        self.assertIs(result.proposal, proposal)
        self.assertEqual(fake.calls, 1)


class CliUsageTests(HostErrorAssertions):
    """AC-002-05：CLI 参数错误映射为 CLI_USAGE_ERROR，退出码 2。"""

    def run_main(self, argv):  # type: ignore[no-untyped-def]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_unknown_or_extra_arguments(self) -> None:
        for argv in (
            [],
            ["--unknown"],
            ["--help"],
            ["--smoke", "extra"],
            ["--smoke", "--smoke"],
            ["smoke"],
            [""],
        ):
            with self.subTest(argv=argv):
                code, out, err = self.run_main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertEqual(err, CLI_USAGE_STDERR)
                self.assertEqual(json.loads(err)["error"]["code"], "CLI_USAGE_ERROR")

    def test_argv_none_uses_process_arguments(self) -> None:
        with mock.patch.object(sys, "argv", ["ca_agent_next"]):
            code, out, err = self.run_main(None)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, CLI_USAGE_STDERR)

        with mock.patch.object(sys, "argv", ["ca_agent_next", "--smoke"]):
            code, out, err = self.run_main(None)
        self.assertEqual(code, 0)
        self.assertEqual(out, SMOKE_STDOUT)
        self.assertEqual(err, "")

    def test_usage_error_is_not_host_error(self) -> None:
        self.assertFalse(issubclass(HostError, type(None)))
        with self.assertRaises(ValueError):
            HostError("CLI_USAGE_ERROR", "invalid command line usage")


class CliSmokeSuccessTests(unittest.TestCase):
    """AC-002-04：默认 Smoke 成功路径。"""

    def run_main(self, argv):  # type: ignore[no-untyped-def]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_default_smoke_success_contract(self) -> None:
        code, out, err = self.run_main(["--smoke"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, SMOKE_STDOUT)
        self.assertEqual(out.count("\n"), 1)

        payload = json.loads(out)
        self.assertEqual(
            payload,
            {
                "schema_version": 1,
                "status": "ok",
                "event_id": "smoke-event-001",
                "model_calls": 1,
                "proposal": {
                    "kind": "smoke.echo",
                    "payload": {"message": "smoke-ok"},
                },
            },
        )
        self.assertEqual(payload["model_calls"], 1)

    def test_default_smoke_is_deterministic(self) -> None:
        first = self.run_main(["--smoke"])
        second = self.run_main(["--smoke"])
        self.assertEqual(first, second)

    def test_default_smoke_opens_no_network_socket(self) -> None:
        with mock.patch("socket.socket", side_effect=AssertionError("network access")):
            code, out, err = self.run_main(["--smoke"])
        self.assertEqual((code, out, err), (0, SMOKE_STDOUT, ""))


class CliFailureTests(unittest.TestCase):
    """AC-002-05：Host 失败映射、退出码 1、stdout/stderr 行为。"""

    def run_main(self, argv, **kwargs):  # type: ignore[no-untyped-def]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv, **kwargs)
        return code, out.getvalue(), err.getvalue()

    def test_model_client_failure_via_injected_client(self) -> None:
        fake = FakeModelClient(error=RuntimeError("token=super-secret"))
        code, out, err = self.run_main(["--smoke"], model_client=fake)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(
            err,
            '{"schema_version":1,"error":{"code":"MODEL_CLIENT_FAILED",'
            '"message":"model client failed"}}\n',
        )
        self.assertEqual(fake.calls, 1)
        self.assertNotIn("super-secret", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(err.count("\n"), 1)

    def test_invalid_proposal_via_injected_client(self) -> None:
        fake = FakeModelClient(proposal={"kind": "k", "payload": {}})
        code, out, err = self.run_main(["--smoke"], model_client=fake)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(
            err,
            '{"schema_version":1,"error":{"code":"MODEL_PROPOSAL_INVALID",'
            '"message":"model proposal is invalid"}}\n',
        )
        self.assertEqual(fake.calls, 1)

    def test_no_traceback_on_host_failure(self) -> None:
        fake = FakeModelClient(error=ValueError("boom"))
        _code, _out, err = self.run_main(["--smoke"], model_client=fake)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("ValueError", err)


class BusinessNeutralityTests(unittest.TestCase):
    """AC-002-07/08：无网络/Provider 初始化，业务中立，提议不执行。"""

    PACKAGE_FILES = sorted(
        Path(ca_agent_next.__file__).resolve().parent.glob("*.py")
    )

    def test_package_has_expected_modules(self) -> None:
        names = {path.name for path in self.PACKAGE_FILES}
        self.assertEqual(
            names,
            {
                "__init__.py",
                "__main__.py",
                "contracts.py",
                "host.py",
                "model_client.py",
                "model_loop.py",
            },
        )

    def test_no_network_provider_or_environment_initialization(self) -> None:
        forbidden = (
            "import socket",
            "import ssl",
            "import urllib",
            "from urllib",
            "import http",
            "from http",
            "import requests",
            "import httpx",
            "import aiohttp",
            "os.environ",
            "getenv(",
            "api_key",
            "apikey",
        )
        for path in self.PACKAGE_FILES:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, text)

    def test_no_business_specific_domains(self) -> None:
        forbidden = ("openamsm", "5gc", "ngap", "open5gs", "sbi")
        for path in self.PACKAGE_FILES:
            lowered = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, lowered)

    def test_proposal_is_only_returned_not_executed(self) -> None:
        proposal = ModelProposal(kind="test.echo", payload={"message": "smoke-ok"})
        fake = FakeModelClient(proposal=proposal)
        result = Host(fake, run_id_factory=lambda: "run-1").handle_event(make_event())
        self.assertEqual(fake.calls, 1)
        self.assertIs(result.proposal, proposal)
        self.assertEqual(set(vars(fake)), {"requests", "calls", "proposal", "error"})


class TestDiscoverySanityTests(unittest.TestCase):
    """AC-002-06：确认测试模块自身被真实发现并执行。"""

    def test_test_module_is_real(self) -> None:
        self.assertTrue(callable(main))
        self.assertTrue(callable(Host.handle_event))
        self.assertTrue(hasattr(AgentLoop, "run_once"))
        self.assertTrue(issubclass(type(ModelClient), type))


if __name__ == "__main__":
    unittest.main()
