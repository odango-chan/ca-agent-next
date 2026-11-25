# AC-013-01 隔离 PoC 独立复跑说明

目标：仅使用本仓库归档的证据与说明，在固定 Compiler 版本上复现 Go/Python 一致性与序列化确定性。

## 1. 环境

| 组件 | 版本 |
|---|---|
| OS / 架构 | Windows（本证据在 Windows amd64 采集；Linux 同样适用） |
| Go | 1.26.6 |
| cel-go | v0.33.2 |
| cel.dev/expr | v0.25.1 |
| Go protobuf | v1.36.10 |
| CPython | 3.14.6 |
| cel-expr-python | 0.1.4 |
| Python protobuf | 7.36.2 |

## 2. 获取固定 Compiler 源码

```bash
git clone https://github.com/odango-chan/ca-skill-compiler.git
cd ca-skill-compiler
git checkout 255ab85fa5abb4b0bf36656bf64250cafebf45cb
```

应用实验补丁（只新增两个测试文件，不修改产品代码）：

```bash
git apply /path/to/isolated-poc/ac013-poc.patch
```

或直接复制：

```bash
cp isolated-poc/ac013_poc_test.go            internal/compiler/
cp isolated-poc/ac013_det_probe_test.go      internal/compiler/
```

## 3. Python 环境

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/Scripts/python.exe cel-expr-python==0.1.4 protobuf==7.36.2
```

（Linux 为 `.venv/bin/python`。）

## 4. 生成与双端校验

在 Compiler 仓库根目录：

```bash
export GOWORK=off
export AC013_OUT=/tmp/ac013-out
go vet ./internal/compiler
go test ./internal/compiler -run '^TestAC013PocGenerate$' -count=1 -v
.venv/bin/python /path/to/isolated-poc/python_verify.py /tmp/ac013-out
```

预期：

- `go test` 输出 `--- PASS: TestAC013PocGenerate`，退出码 0；日志包含 6 行 `rejected ...`。
- `python_verify.py` 输出 18 行 `OK`，末行 `total=18 failed=0`，退出码 0。

### 与归档产物逐字节比较

36 个 `.pb` 与 `cases.json` 的清单见 `determinism/det-a.sha256`（37 条：36 个 `.pb` + `cases.json`）：

```bash
cd /tmp/ac013-out
grep -v '^#' /path/to/isolated-poc/determinism/det-a.sha256 | sha256sum -c -
```

归档目录内全部文件（含源码与日志）的清单见 `SHA256SUMS`：

```bash
cd /path/to/isolated-poc
sha256sum -c SHA256SUMS
```

## 5. 确定性专项

同一源码、两个全新输出目录：

```bash
AC013_OUT=/tmp/ac013-a go test ./internal/compiler -run '^TestAC013PocGenerate$' -count=1
AC013_OUT=/tmp/ac013-b go test ./internal/compiler -run '^TestAC013PocGenerate$' -count=1
diff <(cd /tmp/ac013-a && sha256sum * | sort) <(cd /tmp/ac013-b && sha256sum * | sort)
```

预期无差异；`determinism/compare.json` 记录 `compared_files=37, byte_mismatches=0`。

序列化探针：

```bash
go test ./internal/compiler -run '^TestAC013DeterminismProbe$' -count=1 -v
```

预期 `deterministic_marshal_distinct=1`、`anypb_marshalfrom_deterministic_distinct=1`；默认序列化与 `anypb.New` 会出现多种字节（数量随进程变化，非固定值）。

## 6. 完整性审计

```bash
.venv/bin/python /path/to/isolated-poc/audit_evidence.py \
  /tmp/ac013-out \
  /path/to/isolated-poc
```

审计读取同目录的 `python_verify.py`、`go-test.log`。若日志文件名不同，先复制为 `go-test.log`。

预期关键字段：`pairing_ok=true`、`type_url_ok=true`、`deserialize_ok=true`、
`python_all_ok=true`、`static_rejection_count=6`、`go_test_pass=true`。

## 7. 已知限制

- 本 PoC 复用 Development 多 Skill 共享 Lock fixture 与 Skill 自有 Schema，未接 v1alpha5 发布 Build 路径。
- 仅覆盖单层必填对象嵌套；深层可选祖先、数组、枚举、完整 G.4 布尔组合未覆盖。
- 作者表达式的 guard/降级规则是 PoC 逻辑，不是 Compiler 产品规则；wire 表示与 Artifact API 仍待 Compiler Owner 定稿。
- 确定性结论仅针对本 PoC 的 `CheckedExpr` / `Any` / `FileDescriptorSet` 序列化，不等于 AC-013-03 的产品 Build 确定性验收。
