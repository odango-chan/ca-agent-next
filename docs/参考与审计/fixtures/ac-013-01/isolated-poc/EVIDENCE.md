# AC-013-01 隔离 PoC 执行证据

- 执行时间：2026-11-25 17:27–17:42（Asia/Shanghai）
- 依据：Next PR #7 `f93975f` 的 SR-013 §AC-013-01 阶段执行单（隔离 PoC 阶段 READY）
- 范围：本地临时副本的代码、fixture、测试与证据；未写入 Compiler 产品仓，未改冻结契约，未合并/发布。

## 1. 固定输入

| 项 | 值 |
|---|---|
| Compiler 基线 | `odango-chan/ca-skill-compiler@255ab85fa5abb4b0bf36656bf64250cafebf45cb`（隔离 worktree：`compiler-255ab85/`） |
| 原型来源 | Next PR #7 `5702e2c3dc19445cc807a598376451d10d61391d` |
| 执行单来源 | Next PR #7 `f93975fdd9c2e917c0b03bc9ac2b5494d145506f` |
| CA-SL 规范 | `odango-chan/ca-skills@18d8184367982ccbc835756136c4a53f9096c3a0` |
| Go | go1.26.6 windows/amd64 |
| Python | CPython 3.14.6（隔离 venv，`uv venv --python 3.14`） |
| cel-expr-python | 0.1.4 |
| Python protobuf | 7.36.2 |
| Compiler 依赖 | cel-go v0.33.2、cel.dev/expr v0.25.1、google.golang.org/protobuf v1.36.10 |

PoC 源码：`compiler-255ab85/internal/compiler/ac013_poc_test.go`
（SHA-256 `4b086c2fbd920d945b28b061c25f4733a6fc663f6435e3976053896f6e49de44`）
Python 验证器：`python_verify.py`
（SHA-256 `03113123c9fc92b2c5d3801c173dfaf35a2cf28e311b3c39ed9a504c62c783de`）

## 2. 命令与退出码

| 命令 | 目录 | 退出码 | 说明 |
|---|---|---|---|
| `GOWORK=off go vet ./internal/compiler` | `compiler-255ab85` | 0 | 静态检查通过 |
| `GOWORK=off go test ./internal/compiler -run '^TestAC013PocGenerate$' -count=1 -v` | `compiler-255ab85` | 0 | Go 生成产物、静态拒绝、Go 求值全部通过 |
| `python python_verify.py artifacts` | `.agent-tmp/ac-013-01-poc` | 0 | Python 直接 `env.deserialize` Go 产物，18/18 一致 |
| 连续两次 `go test … -count=1` 后比对 36 个 `.pb` | `compiler-255ab85` | 0 | 两次哈希完全一致（`changed_between_runs=0`） |

日志：`vet.log`、`go-test.log`、`python.log`。

**序列化确定性备注。** 首轮使用 `proto.Marshal` 默认选项时，`CheckedExpr` 的 `reference_map` / `type_map` 是 protobuf map，两次运行会产生不同字节（实测 34/36 文件变化），导致记录哈希不可复现。证据生成已改为 `proto.MarshalOptions{Deterministic: true}`（含 `anypb.MarshalFrom`），复跑两次哈希一致。该问题不影响语义，但说明未来 Artifact 若要求字节确定性，必须显式使用确定性序列化。

## 3. 实现路径（复用 Compiler 真实 Schema 管线）

1. 以 Development 多 Skill 共享 Lock fixture 为基础，增加第二个 Skill 与两个 Skill 各自的 Request Schema 根。
2. 通过 `validateDevelopmentRequest` → `buildDevelopmentLinkScope` → `legacyRequest` → `newDevelopmentSemantics` → `checkSourcesWithDevelopment` 进入同一 Core。
3. 对每个 Skill：`wp3aParseSkillAST` → `validateDependencyIdentity` → `buildSchemaRegistry` →
   `registry.local[skills/<skill>/schemas/request.yaml]` → `resolveReferenceFrom`（Skill 根 `$ref`）→ `resolveSchemaRoot`。
4. 从注册表解析出的 G.4 对象 Schema 生成 `FileDescriptorSet`：
   - 普通字段 → proto2 optional 标量/消息；
   - 可选字段用 `has()` 表达缺失；
   - `[T,"null"]` → oneof 包装消息 `{ T value = 1; bool is_null = 2; }`，可同时保留「缺失 / 显式 null / 原始值」。
5. 作者表达式经 guard 分析（`has`、`== null`、`!= null`、AND/OR/NOT 短路事实）后降级为 wire 表达式，再由 cel-go 编译并导出 `cel.expr.CheckedExpr`，用 `google.protobuf.Any` 包装。
6. Python 只调用 `cel.NewEnv(descriptor_pool=pool)` 与 `env.deserialize(bytes)`，不解析、不重新检查源表达式。

## 4. 正例结果（Go 与 Python 同一产物）

| # | Skill | 用例 | 输入要点 | 预期 | Go | Python |
|---|---|---|---|---|---|---|
| 1 | verify-ue-registration | true | kind=create, count=1 | true | true | true |
| 2 | verify-ue-registration | false | kind=modify | false | false | false |
| 3 | verify-ue-registration | missing_kind | 无 event | error | error | error |
| 4 | verify-ue-registration | missing_optional | note 缺失 | false | false | false |
| 5 | verify-ue-registration | present_optional | note="x" | true | true | true |
| 6 | verify-ue-registration | nullable_value | wrapped=5 | true | true | true |
| 7 | verify-ue-registration | nullable_null | wrapped 显式 null | false | false | false |
| 8 | verify-ue-registration | nullable_eq_null | both 显式 null | true | true | true |
| 9 | verify-ue-registration | both_absent | both 缺失 | false | false | false |
| 10 | verify-ue-registration | both_value | both="ok" | true | true | true |
| 11 | verify-ue-registration | nested | nested.inner="y" | true | true | true |
| 12 | verify-ue-registration | int64_max | count=9223372036854775807 | true | true | true |
| 13 | verify-ue-registration | double | ratio=2.5 | true | true | true |
| 14 | verify-ue-registration | double_max | ratio=1.7976931348623157e308 | true | true | true |
| 15 | verify-ue-registration | and_chain | AND 三条件 | true | true | true |
| 16 | verify-ue-registration | or_guarded | `!has(note) \|\| note=="x"` | true | true | true |
| 17 | verify-ue-registration | not | `!(count==2)` | true | true | true |
| 18 | verify-context-only | second_skill | token="t"（另一 Schema） | true | true | true |

Python 汇总：`total=18 failed=0`。

第 7、9 项使用同一 optional+nullable 字段：显式 null 时 `has(input.both) && input.both == null` 为 true，字段缺失时为 false，证明两种状态可区分。

## 5. 静态拒绝（Go 侧，均为 `CEL_INVALID` 语义）

| 用例 | 作者表达式 | 拒绝原因 |
|---|---|---|
| unknown_field | `input.unknown == 1` | 未知字段 |
| unguarded_optional | `input.note == "x"` | 缺少 `has` 守卫 |
| unguarded_nullable | `input.wrapped == 5` | 缺少非 null 守卫 |
| int_double_mix | `input.count == 1.0` | int 字段与 double 字面量 |
| unsafe_or | `has(input.note) \|\| input.note == "x"` | OR 左假时仍读取缺失字段 |
| cross_skill | `input.token == "t"`（Skill 1） | 借用另一个 Skill 的 Schema 字段 |

## 6. 产物与哈希（节选）

目录：`artifacts/`；`cases.json` SHA-256 `721991006f5d4bb63b624db7d8cfd7ad6df80b1e13f8ac97f92d3b79dc375bbc`。

- `verify-ue-registration-<case>.types.pb`：同一 Skill 全部一致，SHA-256 `cdb47fa59989840a4ea58b14464e66ec0557c0f997c5a188fd788cecf49e8215`
- `verify-context-only-second_skill.types.pb`：SHA-256 `cee03f2acef2759d42809e567495ee0f36e90f492402544805762ccdf83f3a70`
- `verify-ue-registration-true.checked.pb`：SHA-256 `d1782eb15e8b5842d390e9850577674e05224460153219b5a02baf404929af4e`
- `verify-ue-registration-nullable_eq_null.checked.pb`：SHA-256 `33ad1ab884c33322890aea17aa91ce3030d965e068fd47d3e0e5222dd5ecccb6`
- `verify-ue-registration-both_absent.checked.pb`：SHA-256 `33ad1ab884c33322890aea17aa91ce3030d965e068fd47d3e0e5222dd5ecccb6`（与 `nullable_eq_null` 相同：两者降级为同一 wire 表达式 `has(input.both) && has(input.both.is_null)`）
- `verify-context-only-second_skill.checked.pb`：SHA-256 `329bf1f151f6eaf9a5a24669cee7196e2cb04763c4954d565ecc74bd1fa9d769`

## 7. 对照阶段通过条件

| 条件 | 结果 |
|---|---|
| Go、Python 对同一实际产物正负例一致 | PASS（18/18） |
| 缺失 / 显式 null / 有效值 | PASS（第 6、7、9、10 项） |
| AND / OR / NOT 守卫 | PASS（第 15–17 项） |
| 嵌套路径 | PASS（第 11 项，单层必填对象） |
| int64 / finite double 边界 | PASS（第 12–14 项） |
| 未知字段与无守卫拒绝 | PASS（6 项） |
| 求值错误 | PASS（第 3 项） |
| 多 Skill Lock 隔离 | PASS（cross_skill 拒绝 + 第二 Skill 独立 Schema） |

**结论：AC-013-01 在隔离 PoC 范围内 PASS。**

## 8. 明确未覆盖（保持 NOT_RUN）

- 产品内实现：`ContractAST.when` 解析、Schema-aware 静态检查、发布 Artifact 字段与 Build/Verify（AC-013-02/03/04 全部 NOT_RUN）。
- 深层嵌套 + 可选/可空祖先链路；数组字段运行期；枚举与 `const`；多 Skill 同时 true 的消歧。
- 通用 OR/NOT 事实分析：当前仅实现左假分支的最小传播，未证明 G.4 任意布尔组合。
- 正式 Compiler Schema Registry 闭包仅通过 Development fixture 验证，未接 v1alpha5 发布 Build 路径。
- 作者表达式的最终类型规则仍待 Compiler Owner 定稿；本 PoC 的 wire 表示与 lower 规则不是冻结契约。

## 9. 回填与下一步

1. 分支 `docs/ac-013-01-poc-evidence` 已 rebase 到 `origin/main`（`b2ed5eb`）；原始提交 `78dddd5` 内容保留，重写后为 `320d5af`（提交 trailer 记录 `Original-Commit` 与 `Rebased-Onto`）。
2. 已创建 Issue #17 与 Draft PR #18（`docs: add AC-013-01 isolated PoC evidence`），等待独立评审；未合并、未发布。
3. 在 Compiler 产品分支实现 `ContractAST.when` 与同一 guard/降级管线（需 SR-013 READY 与目标仓写入授权）。
4. 扩展 Schema Registry 闭包、嵌套/数组、完整布尔组合与多 Skill 同时命中，作为 AC-013-02 输入。

## 10. 后续归档完整性审计补充（2026-11-27）

本节为后续审计附注，不改写上文 2026-11-25 的原始执行记录。

- 固定归档基线：Next PR #18 Head `c3e5bb78ff49306329bcbc2387da6108280903bc`。
- 原始证据表记录 `GOWORK=off go vet ./internal/compiler` 退出码为 0，但固定归档 tree 中**不存在 `vet.log`**。因此该历史退出码仅保留为原执行者记录，当前无法通过归档日志独立复核；不得用 `go-test.log` 或其他日志替代。
- 本轮未重新执行 `go vet`，也未生成或补造 `vet.log`。状态明确为：`NOT_ARCHIVED / NOT_INDEPENDENTLY_VERIFIABLE`。
- `py-results.json` 的归档实际大小为 2333 bytes，SHA-256 为 `f6abbc68db58590de3d4d261f02412ea2bcdb3f38765723c02d2cf5b9b62930f`；`audit.json` inventory 已同步为该归档文件的实际值。
- `SHA256SUMS` 已改为相对于本目录根的路径；清单覆盖 58 个归档文件（不含清单自身）。
- 历史 Go/Python 18/18、6 类静态拒绝及原有测试记录均保留。本附注不将其扩大为 Compiler 产品验收，也不改变 AC-013-02～06 的状态。

后续若重新执行 `go vet`，必须在固定 Compiler SHA 与补丁上真实运行，保存命令、环境、退出码和原始输出，再另行提交真实日志；不得将新运行结果伪装成 2026-11-25 的历史日志。
