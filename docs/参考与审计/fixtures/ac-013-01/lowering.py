from pathlib import Path
from cel_expr_python import cel
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

root = Path(__file__).parent
types = descriptor_pb2.FileDescriptorSet.FromString((root / "lowered.types.pb").read_bytes())
pool = descriptor_pool.DescriptorPool()
for proto in types.file:
    pool.Add(proto)
input_type = message_factory.GetMessageClass(pool.FindMessageTypeByName("ac013.Input"))
env = cel.NewEnv(descriptor_pool=pool)
program = env.deserialize((root / "lowered.checked.pb").read_bytes())
for kind, input_value, expected in [
    ("create", input_type(count={"count": (1 << 63) - 1}), "true"),
    ("modify", input_type(count={"count": (1 << 63) - 1}), "false"),
    ("create", input_type(), "false"),
    ("create", input_type(count={"is_null": True}), "false"),
]:
    actual = str(program.eval(data={"kind": kind, "input": input_value}))
    assert actual == expected, (kind, actual, expected)
    print("python", kind, input_value.HasField("count"), actual)
try:
    value = program.eval(data={"input": input_type(count={"count": (1 << 63) - 1})})
except RuntimeError as error:
    print("python missing kind:", error)
else:
    assert "kind" in str(value) and str(value) not in ("true", "false"), value
    print("python missing kind:", value)
assert input_type(count={"is_null": True}).HasField("count")
assert input_type(count={"is_null": True}).count.WhichOneof("state") == "is_null"
assert not input_type().HasField("count")
print("null and missing remain distinct")

