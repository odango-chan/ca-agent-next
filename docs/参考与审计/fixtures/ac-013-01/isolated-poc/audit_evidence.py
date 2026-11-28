"""Independent audit of the AC-013-01 isolated PoC evidence directory.

Reads the archived/current artifacts, checks pairing, Any type URL, descriptor
loading, Python direct-deserialize behaviour and result consistency. Writes
audit.json next to EVIDENCE.md.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

from cel_expr_python import cel
from google.protobuf import any_pb2, descriptor_pb2, descriptor_pool, message_factory

ART = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ART.parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ftype(path):
    suffix = path.suffix
    if suffix == ".pb":
        return "protobuf"
    if suffix == ".json":
        return "json"
    if suffix == ".go":
        return "go-source"
    if suffix == ".py":
        return "python-source"
    if suffix == ".log":
        return "log"
    if suffix == ".md":
        return "markdown"
    return "other"


def role(name):
    if name == "cases.json":
        return "case table"
    if name == "py-results.json":
        return "python results"
    if name.endswith(".checked.pb"):
        return "CheckedExpr Any"
    if name.endswith(".types.pb"):
        return "FileDescriptorSet"
    return "other"


def package_for(skill):
    return "ac013b" if skill == "verify-context-only" else "ac013a"


cases_doc = json.loads((ART / "cases.json").read_text(encoding="utf-8"))
cases = cases_doc["cases"]

inventory = []
for path in sorted(ART.iterdir()):
    if path.is_file():
        inventory.append(
            {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "type": ftype(path),
                "role": role(path.name),
            }
        )

findings = {}
ids = [c["id"] for c in cases]
findings["case_count"] = len(cases)
findings["case_ids"] = ids
findings["checked_files"] = sorted(p.name for p in ART.glob("*.checked.pb"))
findings["types_files"] = sorted(p.name for p in ART.glob("*.types.pb"))

# Pairing: every case has exactly one checked and one types file.
pairing_errors = []
for c in cases:
    prefix = f"{c['skill']}-{c['id']}"
    for suffix in (".checked.pb", ".types.pb"):
        if not (ART / (prefix + suffix)).is_file():
            pairing_errors.append(prefix + suffix)
findings["pairing_errors"] = pairing_errors
findings["pairing_ok"] = not pairing_errors

# Any type URL and payload validity via env.deserialize.
type_urls = {}
deserialize_failures = []
for c in cases:
    prefix = f"{c['skill']}-{c['id']}"
    raw = (ART / (prefix + ".checked.pb")).read_bytes()
    any_msg = any_pb2.Any.FromString(raw)
    type_urls.setdefault(any_msg.type_url, 0)
    type_urls[any_msg.type_url] += 1
    types = descriptor_pb2.FileDescriptorSet.FromString(
        (ART / (prefix + ".types.pb")).read_bytes()
    )
    pool = descriptor_pool.DescriptorPool()
    for proto in types.file:
        pool.Add(proto)
    env = cel.NewEnv(descriptor_pool=pool)
    try:
        env.deserialize(raw)
    except Exception as error:  # noqa: BLE001 - audit records the failure
        deserialize_failures.append([prefix, str(error)])
findings["type_urls"] = type_urls
findings["type_url_ok"] = list(type_urls) == ["type.googleapis.com/cel.expr.CheckedExpr"]
findings["deserialize_failures"] = deserialize_failures
findings["deserialize_ok"] = not deserialize_failures

# DescriptorSet loadability and expected messages.
descriptor_errors = []
descriptor_messages = {}
for name in sorted({c["skill"] for c in cases}):
    prefix = f"{name}-{cases[0]['id']}" if False else None
    any_case = next(c for c in cases if c["skill"] == name)
    types = descriptor_pb2.FileDescriptorSet.FromString(
        (ART / f"{name}-{any_case['id']}.types.pb").read_bytes()
    )
    pool = descriptor_pool.DescriptorPool()
    for proto in types.file:
        pool.Add(proto)
    pkg = package_for(name)
    try:
        found = []
        for msg in ("Input", "Event"):
            message_factory.GetMessageClass(pool.FindMessageTypeByName(f"{pkg}.{msg}"))
            found.append(msg)
        descriptor_messages[name] = found
    except Exception as error:  # noqa: BLE001
        descriptor_errors.append([name, str(error)])
findings["descriptor_messages"] = descriptor_messages
findings["descriptor_errors"] = descriptor_errors
findings["descriptor_ok"] = not descriptor_errors

# Python verifier must deserialize, never recompile.
python_source = (OUT / "python_verify.py").read_text(encoding="utf-8")
findings["python_uses_deserialize"] = "env.deserialize(" in python_source
findings["python_recompiles"] = bool(
    re.search(r"\.compile\(", python_source) or re.search(r"env\.parse\(", python_source)
)

# Result consistency.
results = json.loads((ART / "py-results.json").read_text(encoding="utf-8"))
findings["python_result_count"] = len(results)
findings["python_all_ok"] = all(r["ok"] and r["actual"] == r["want"] for r in results)
findings["unknown_not_match"] = next(
    r for r in results if r["id"] == "missing_kind"
)["actual"] == "error"

# Static rejections recorded in the Go log.
def read_text(path):
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le")
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be")
    return raw.decode("utf-8", errors="replace")


go_log = read_text(OUT / "go-test.log")
rejected = re.findall(r"rejected (\w+):", go_log)
findings["static_rejections"] = sorted(set(rejected))
findings["static_rejection_count"] = len(set(rejected))
findings["go_test_pass"] = "--- PASS: TestAC013PocGenerate" in go_log

# Coverage checks.
findings["coverage"] = {
    "true": "true" in ids,
    "false": "false" in ids,
    "missing_optional": "missing_optional" in ids,
    "explicit_null": "nullable_null" in ids and "nullable_eq_null" in ids,
    "optional_nullable_missing_vs_null": "both_absent" in ids and "nullable_eq_null" in ids,
    "and": "and_chain" in ids,
    "or": "or_guarded" in ids,
    "not": "not" in ids,
    "nested": "nested" in ids,
    "int64": "int64_max" in ids,
    "double": "double" in ids and "double_max" in ids,
    "multi_skill": "second_skill" in ids,
}

audit = {"inventory": inventory, "findings": findings}
(OUT / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

print(json.dumps({k: v for k, v in findings.items() if k not in ("case_ids",)}, indent=2, ensure_ascii=False))

