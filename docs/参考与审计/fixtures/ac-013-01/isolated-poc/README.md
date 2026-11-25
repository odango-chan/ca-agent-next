# AC-013-01 隔离 PoC 证据归档

本目录归档 SR-013 / AC-013-01 的隔离 PoC 证据，使未参与实验的复核者仅依赖本仓库即可独立复现与判断。**该 PoC 不是 Compiler 产品实现，也不是产品验收结论。**

- 受测 Compiler 基线：`odango-chan/ca-skill-compiler@255ab85fa5abb4b0bf36656bf64250cafebf45cb`
- CA-SL 规范：`odango-chan/ca-skills@18d8184367982ccbc835756136c4a53f9096c3a0`
- 原始证据提交（Next）：`320d5afec41a181d7c11700c407b726cf151b5e0`（其前身为 `78dddd5`，见提交 trailer）
- 关联：Issue #17、PR #18、SR-013

## 目录结构

```text
isolated-poc/
  README.md                     本说明
  reproduction.md               独立复跑步骤与预期输出
  EVIDENCE.md                   原始执行者证据单（保持原样，未改写）
  ac013_poc_test.go             PoC 生成器/校验器源码
  ac013_det_probe_test.go       确定性序列化探针
  python_verify.py              Python 直接加载 Go 产物并求值
  audit_evidence.py             证据完整性审计脚本
  audit.json                    审计输出
  cases.json                    18 个用例的作者表达式与预期
  py-results.json               Python 逐用例结果
  artifacts/                    36 个 protobuf（18 checked + 18 types）
  go-test.log                   原始工作区 Go 测试日志（UTF-8 转码）
  python.log                    原始工作区 Python 验证日志（UTF-8 转码）
  determinism-probe-original.log  原始副本探针输出
  determinism-probe-repro.log     干净副本探针输出
  determinism/                  两独立输出目录的 SHA-256 清单与比对
  repro/                        干净副本复跑的日志与比对
  ac013-poc.patch               相对 255ab85 的完整实验补丁
  SHA256SUMS                    本目录除自身外全部文件的 SHA-256
```

## 证据来源与状态

| 证据 | 来源 | 状态 |
|---|---|---|
| `artifacts/`、`cases.json`、`py-results.json`、`EVIDENCE.md`、`go-test.log`、`python.log` | 原始隔离工作区 `.agent-tmp/ac-013-01-poc/` 的归档副本 | VERIFIED |
| `repro/` | 在干净的 `255ab85` worktree 中用同一源码重新执行 | VERIFIED |
| `determinism/` | 同一源码写入两个全新输出目录后逐文件比对 | VERIFIED |
| `ac013-poc.patch` | 干净副本中以 `git diff` 生成 | VERIFIED |

原始工作区路径仅在复现说明中作为来源记录，不要求复核者访问。

## 结果摘要

- Python 直接 `env.deserialize` Go 生成的 `cel.expr.CheckedExpr` Any，**18/18** 与 Go 结果一致。
- 缺失、显式 null、有效值三态可区分（同一 optional+nullable 字段）。
- AND / OR / NOT、嵌套路径、`int64` 最大值、finite double 最大值均覆盖。
- 6 类静态拒绝全部符合预期；缺 `event` 的求值错误返回 UNKNOWN，不作为匹配成功。
- 两个干净输出目录的 37 个生成文件（36 个 `.pb` + `cases.json`）**逐字节一致**。
- 默认 `proto.Marshal` 对 `CheckedExpr` 的 map 字段不稳定；确定性选项下 200 次序列化只产生 1 种字节。

## 明确边界

- 本归档只覆盖 AC-013-01；AC-013-02～05 为 NOT_RUN / BLOCKED。
- 不证明 Compiler 产品 Build/Verify、发布 Artifact 或 Next 消费实现已完成。
- 确定性 PASS 是 PoC 级结论，不等于 AC-013-03 的编译产品 Build 确定性验收。

复跑方法见 [reproduction.md](reproduction.md)。
