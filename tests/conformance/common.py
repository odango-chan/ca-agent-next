"""Shared utilities for the A-batch Native Plugin IPC tests."""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO_ROOT / "tests"
EVIDENCE = TESTS_ROOT / "evidence"
FIXTURES = TESTS_ROOT / "fixtures"
PLUGIN_DIR = REPO_ROOT / "examples" / "echo" / "plugin"


class Redactor:
    """Removes credentials from evidence even though this batch uses none."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self.secrets = [item for item in secrets if item]
        self.patterns = [
            (re.compile(r'("processToken"\s*:\s*")[^"]*(")'), r"\1<redacted-processToken>\2"),
            (re.compile(r'("Authorization"\s*:\s*")[^"]*(")', re.I), r"\1<redacted-Authorization>\2"),
            (re.compile(r"(?im)^(authorization\s*:\s*).+$"), r"\1<redacted-Authorization>"),
        ]

    def __call__(self, text: str) -> str:
        for secret in self.secrets:
            text = text.replace(secret, "<redacted-secret>")
        for pattern, replacement in self.patterns:
            text = pattern.sub(replacement, text)
        return text


@dataclass
class CaseResult:
    case_id: str
    processes: str
    input_mutation: str
    expected: str
    actual: str = ""
    status: str = "NOT_RUN"
    evidence: list[str] = field(default_factory=list)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "caseId": self.case_id,
            "processes": self.processes,
            "inputMutation": self.input_mutation,
            "expected": self.expected,
            "actual": self.actual,
            "status": self.status,
            "evidence": self.evidence,
            "notes": self.notes,
        }


class Transcript:
    def __init__(self, path: Path, redactor: Redactor) -> None:
        self.path = path
        self.redactor = redactor
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        self._lock = threading.Lock()

    def frame(self, direction: str, frame: dict[str, Any]) -> None:
        self.event({"kind": "frame", "direction": direction, "frame": frame})

    def event(self, event: dict[str, Any]) -> None:
        line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **event}, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(self.redactor(line))


def write_text(path: Path, text: str, redactor: Redactor | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redactor(text) if redactor else text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any, redactor: Redactor | None = None) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", redactor)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)
