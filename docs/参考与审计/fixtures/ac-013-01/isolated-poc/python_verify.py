"""AC-013-01 Python side: load the Go-generated Any + FileDescriptorSet directly.

The program is deserialized from the checked expression produced by Go; the
source string is never parsed or re-checked here.
"""
import json
import sys
from pathlib import Path

from cel_expr_python import cel
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

ART = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts")
SPEC = json.loads((ART / "cases.json").read_text(encoding="utf-8"))


def build(cls, spec):
    kwargs = {}
    for name, value in spec.items():
        if isinstance(value, dict):
            field = cls.DESCRIPTOR.fields_by_name[name]
            child = message_factory.GetMessageClass(field.message_type)
            kwargs[name] = build(child, value)
        else:
            kwargs[name] = value
    return cls(**kwargs)


def load_skill(skill):
    package = "ac013b" if skill == "verify-context-only" else "ac013a"
    return package


results = []
for case in SPEC["cases"]:
    package = load_skill(case["skill"])
    types = descriptor_pb2.FileDescriptorSet.FromString(
        (ART / f"{case['skill']}-{case['id']}.types.pb").read_bytes()
    )
    pool = descriptor_pool.DescriptorPool()
    for proto in types.file:
        pool.Add(proto)
    input_cls = message_factory.GetMessageClass(
        pool.FindMessageTypeByName(package + ".Input")
    )
    event_cls = message_factory.GetMessageClass(
        pool.FindMessageTypeByName(package + ".Event")
    )
    env = cel.NewEnv(descriptor_pool=pool)
    program = env.deserialize(
        (ART / f"{case['skill']}-{case['id']}.checked.pb").read_bytes()
    )
    data = {"input": build(input_cls, case["input"])}
    if case.get("eventKind"):
        data["event"] = event_cls(type=case["eventKind"])
    try:
        value = program.eval(data=data)
        text = str(value)
        actual = text if text in ("true", "false") else "error"
    except Exception:  # evaluation failure is an explicit outcome
        actual = "error"
    results.append(
        {
            "id": case["id"],
            "skill": case["skill"],
            "want": case["want"],
            "actual": actual,
            "ok": actual == case["want"],
        }
    )

(ART / "py-results.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
failed = [r for r in results if not r["ok"]]
for r in results:
    print(f"python {r['skill']}/{r['id']}: {r['actual']} (want {r['want']}) {'OK' if r['ok'] else 'FAIL'}")
print(f"total={len(results)} failed={len(failed)}")
sys.exit(1 if failed else 0)
