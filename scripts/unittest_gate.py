"""SR-028 统一 unittest 门禁脚本（仅标准库）。

按 G02 §3.6 / SR-028 §5.1 运行 Host、Plugin、Review Context 和完整总计四个范围，
逐范围断言 ``discovered > 0``、``tests_run == discovered``、失败/错误/跳过/预期失败/
意外成功/加载错误全部为 0 且 ``discovery_exception`` 为 JSON ``null``。某个范围失败
时仍继续执行其余范围并写出全部报告，最后统一按整体 ``exit_code`` 返回。

示例::

    python scripts/unittest_gate.py --output-dir artifacts/unittest-gate
    python scripts/unittest_gate.py --suite host --output-dir artifacts/host-gate
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import platform
import sys
import unittest
from pathlib import Path
from typing import Any

SUITE_PATTERNS: dict[str, str] = {
    "host": "test_host.py",
    "plugin": "test_plugin.py",
    "review-context": "test_review_context.py",
    "total": "test*.py",
}
SUITE_ORDER: tuple[str, ...] = ("host", "plugin", "review-context", "total")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_suite(name: str, tests_dir: Path) -> dict[str, Any]:
    """运行单个范围，返回报告字典；不因失败抛出。"""
    pattern = SUITE_PATTERNS[name]
    loader = unittest.TestLoader()
    stream = io.StringIO()
    discovery_exception: str | None = None
    suite: unittest.TestSuite | None = None
    try:
        suite = loader.discover(
            start_dir=str(tests_dir),
            pattern=pattern,
            top_level_dir=str(tests_dir),
        )
    except BaseException as exc:  # noqa: BLE001 - 任意 discovery 异常都必须失败并记录
        discovery_exception = f"{type(exc).__name__}: {exc}"

    loader_errors = list(loader.errors)
    discovered = suite.countTestCases() if suite is not None else 0

    tests_run = 0
    failures = 0
    errors = 0
    skipped = 0
    expected_failures = 0
    unexpected_successes = 0
    if suite is not None:
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        expected_failures = len(result.expectedFailures)
        unexpected_successes = len(result.unexpectedSuccesses)

    passed = (
        tests_run
        - failures
        - errors
        - skipped
        - expected_failures
        - unexpected_successes
    )
    exit_code = 1 if (
        discovered <= 0
        or tests_run != discovered
        or failures
        or errors
        or skipped
        or expected_failures
        or unexpected_successes
        or loader_errors
        or discovery_exception is not None
    ) else 0
    return {
        "suite": name,
        "pattern": pattern,
        "discovered": discovered,
        "tests_run": tests_run,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "expected_failures": expected_failures,
        "unexpected_successes": unexpected_successes,
        "loader_errors": len(loader_errors),
        "loader_error_messages": loader_errors,
        "discovery_exception": discovery_exception,
        "exit_code": exit_code,
        "_log": stream.getvalue(),
    }


def _write_reports(
    report: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """写出单范围 JSON/log；写失败时把该范围 exit_code 置为 1。"""
    name = report["suite"]
    log_text = report.pop("_log")
    serializable = {k: v for k, v in report.items() if not k.startswith("_")}
    try:
        (output_dir / f"{name}.log").write_text(log_text, encoding="utf-8")
    except OSError as exc:
        serializable["report_write_error"] = f"{type(exc).__name__}: {exc}"
        serializable["exit_code"] = 1
    try:
        (output_dir / f"{name}.json").write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        serializable["report_write_error"] = f"{type(exc).__name__}: {exc}"
        serializable["exit_code"] = 1
    return serializable


def _print_report(report: dict[str, Any]) -> None:
    print(
        f"[{report['suite']}] discovered={report['discovered']} "
        f"tests_run={report['tests_run']} passed={report['passed']} "
        f"failures={report['failures']} errors={report['errors']} "
        f"skipped={report['skipped']} "
        f"expected_failures={report['expected_failures']} "
        f"unexpected_successes={report['unexpected_successes']} "
        f"loader_errors={report['loader_errors']} "
        f"discovery_exception={report['discovery_exception']!r} "
        f"exit_code={report['exit_code']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SR-028 fail-closed unittest gate")
    parser.add_argument(
        "--suite",
        action="append",
        choices=sorted(SUITE_PATTERNS),
        default=None,
        help="可重复；省略时运行全部四个范围",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/unittest-gate",
        help="JSON/log/summary 输出目录（默认 artifacts/unittest-gate）",
    )
    args = parser.parse_args(argv)

    selected = args.suite if args.suite else list(SUITE_ORDER)
    # 去重并保持稳定顺序
    ordered: list[str] = []
    for name in SUITE_ORDER:
        if name in selected and name not in ordered:
            ordered.append(name)
    if not ordered:
        print("no suites selected", file=sys.stderr)
        return 1

    root = _repo_root()
    tests_dir = root / "tests"
    output_dir = Path(args.output_dir).resolve()

    reports: dict[str, dict[str, Any]] = {}
    write_failures = 0
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"cannot create output dir {output_dir}: {exc}", file=sys.stderr)
        return 1

    for name in ordered:
        try:
            report = _run_suite(name, tests_dir)
        except BaseException as exc:  # noqa: BLE001 - 范围级异常必须转化为报告失败
            report = {
                "suite": name,
                "pattern": SUITE_PATTERNS[name],
                "discovered": 0,
                "tests_run": 0,
                "passed": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "expected_failures": 0,
                "unexpected_successes": 0,
                "loader_errors": 0,
                "loader_error_messages": [],
                "discovery_exception": f"{type(exc).__name__}: {exc}",
                "exit_code": 1,
                "_log": "",
            }
        serialized = _write_reports(report, output_dir)
        if "report_write_error" in serialized:
            write_failures += 1
        reports[name] = serialized
        _print_report(serialized)

    overall_exit_code = 1 if (
        write_failures
        or any(report["exit_code"] != 0 for report in reports.values())
    ) else 0
    summary = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo_root": str(root),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "suites": {
            name: {
                key: value
                for key, value in report.items()
                if key not in {"loader_error_messages"}
            }
            for name, report in reports.items()
        },
        "overall_exit_code": overall_exit_code,
        "exit_code": overall_exit_code,
    }
    try:
        (output_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"cannot write summary.json: {exc}", file=sys.stderr)
        overall_exit_code = 1

    print(f"overall_exit_code={overall_exit_code}")
    return overall_exit_code


if __name__ == "__main__":
    sys.exit(main())
