# CA Agent Next

CA Agent Next 是下一代通用 Agent 的独立实现仓。目标是用尽可能少、可验证的机制证明：通用 Agent 可以通过 Skill 和 Plugin 扩展不同业务，而不需要为每个业务修改 Agent Core。

**语言决策：Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 固定使用 Python。** 独立 Plugin 可以使用 Go；Go Plugin 不意味着 Go Host。

> 当前设计评审范围见[SR 总索引](docs/治理/SR%20总索引.md)。24 项 DRAFT SR 已请求独立设计评审。SR-001/002/003 模块已 VERIFIED，SR-024 的 VERIFIED 限于历史 Publisher，SR-015 已 IMPLEMENTED。新 1.6.0 产品链及系统 EX 仍待验收。

## 从这里开始

1. [功能树与需求追踪基线](docs/治理/功能树与需求追踪基线.md) — 先识别 Feature / IR / SR，再按功能加载资料。
2. [CA Agent Next 架构设计](docs/架构设计/CA%20Agent%20Next%20架构设计.md) — 唯一总体架构。
3. [文档总目录与索引](docs/治理/文档总目录与索引.md) — 正式文档入口。
4. [SR 管理规范](docs/规范/SR%20管理规范.md) — SR、Issue、PR、Commit 和验收追踪规则。
5. [文档编写与治理规范](docs/规范/文档编写与治理规范.md) — 功能设计与修订记录要求。
6. [Python 工程工具链与实施基线规范](docs/规范/Python工程工具链与实施基线规范.md) — 根 Python 工程唯一 uv 工具链、共享实施分支继承与迁移规则。
7. [演示验收基线](docs/验收与实施/演示验收基线.md) — Echo 与 OpenAMSM 的 EX/OM 验收门槛。
8. [仓库协作指引](Agent.md) — 自动化协作入口和不可违反的约束。

[IR 总登记册](docs/IR/IR%20总登记册.md)记录需求项、Issue 协作入口和 SR 分解。

## 当前开发与复验入口（SR-028 迁移后）

自 SR-028 起，本仓根 Python 工程统一使用 uv `0.13.10` 解析、锁定和运行依赖；`uv.lock` 是唯一锁文件，`.python-version` 精确为 `3.14.6`（`requires-python >=3.11` 仍只是包元数据下限，不代表 3.11～3.13 版本矩阵已通过）。历史 pip 命令只保留在各 SR 与验收记录的原始受测环境中（见 SR-002、SR-003、演示验收基线），不作为当前入口。

该工具链是整个 Next 根 Python 工程的共享基线，不限于 SR-028；所有触及根 Python 源码、测试、脚本、依赖或 Python CI 的实施分支都必须从[当前共享基线](docs/规范/Python工程工具链与实施基线规范.md)派生，禁止回退 pip。PR #99 尚未合入期间，当前过渡基线由[治理 PR #112](https://github.com/odango-chan/ca-agent-next/pull/112)的堆叠分支提供；每次实施前必须重新核对 Issue #111 中的远端分支与完整 SHA。在该 Workflow 进入仓库默认分支后，普通 PR 由[可信默认分支策略 Workflow](.github/workflows/python-toolchain-policy-trusted.yml) 检查基线继承和新增命令；[Bootstrap/锁一致性 Workflow](.github/workflows/python-toolchain-policy.yml) 执行一次性引导与 `uv lock --check`。普通 PR 的目标分支须将 `Python Toolchain Policy / Python Toolchain Policy` 和 `Python Toolchain Policy Bootstrap / Python Lock Consistency` 设为 Required；PR #112 首次合并前，接收分支还须将 `Python Toolchain Policy Bootstrap / Bootstrap Policy Check` 设为 Required；`pull_request_target` 可信检查只有在 Workflow 进入默认分支后才会启动。

```bash
# 前置：Go 1.24+（满足 examples/echo/plugin/go.mod 的 go 1.24 directive）
go version

# 安装/同步（首次或依赖声明变化后；本地与 CI 一致使用 --locked）
uv python install
uv sync --locked --group dev --extra plugins
uv lock --check

# 本地测试门禁：Host / Plugin / Review Context / 完整总计，skipped=0，任一失败即非零
uv run --no-sync --locked --group dev --extra plugins python scripts/unittest_gate.py --output-dir artifacts/unittest-gate

# Host Smoke（stdout 固定单行 JSON，stderr 为空）
uv run --no-sync --locked --group dev --extra plugins python -m ca_agent_next --smoke

# Review Context 生成器
uv run --no-sync --locked --group dev --extra plugins python scripts/review_context.py --help
```

Go Echo Plugin 构建（Plugin 测试前置）：在 `examples/echo/plugin/` 下设置 `GOWORK=off` 后执行 `go build -trimpath -o bin/echo-plugin .`；Windows 目标文件名为 `bin/echo-plugin.exe`。GitHub Actions 入口为 `.github/workflows/sr003-plugin-ci.yml`（Ubuntu Python 3.12 / Windows Python 3.14.6 矩阵）与 `.github/workflows/review-context.yml`（诊断与正式 Artifact 分离）。

## 文档体系

正式文档和 IR/SR 数量见[文档索引](docs/治理/文档总目录与索引.md#3-文档数量快照)。

架构设计与设计说明书在 docs 下同级。总体架构下可按领域、子系统和模块维护多份架构与设计文档。见[外部能力域架构总览](docs/架构设计/外部能力域架构总览.md)；SR 记录需求范围和验收条件，不替代功能设计。F07 示例与验收由统一验收基线承载。

## 跨仓任务入口

项目群任务统一从本仓发起。先查[各仓功能子树](docs/治理/功能树与需求追踪基线.md#51-按仓功能子树)，在本仓登记或选用明确覆盖目标仓改动的 SR，达到 READY 后再实施，随后回填目标仓 PR、Commit 与验收证据。

## 仓库职责与外部能力

| 功能/能力 | 实现及发布仓 | Next 的责任 |
|---|---|---|
| Agent Core / Host / Runtime | ca-agent-next | Python 新实现 |
| Skill 作者规范与业务 Skill（EC01） | ca-skills | 消费 SKILL.md 与发布输入 |
| CA-SL Compiler / Artifact 发布（EC02） | ca-skill-compiler | 只消费已发布 Runtime Artifact |
| Tool Interface / Provider / Codec（EC03） | ca-client-tools | 通过唯一 Plugin Manager 的 tools Extension 调用；契约消费设计见 F03.05 |
| OpenAMSM SBI Event / Delivery Plugin（EC04） | ca-openamsm-plugin | 消费统一 Plugin Package/IPC 和 Artifact Handoff |
| OpenAMSM Owner（EC05） | env-openamsm 等 Owner 仓 | 消费权威 Receipt / Commit Proof |
| Skill Studio（EC06） | ca-skill-studio-demo | 作者工作台、Source-first、LSP、AI Authoring，不执行 Skill |
| 5GC Simulator / Mock AMF（EC07） | env-5gc-sim | 参考模拟器与协议测试对端，不拥有 OpenAMSM 会话状态 |
| Python Host 参考实现（REF01） | ca-agent-demo | 逐文件选择性复用代码和测试 |
| Go Runtime 参考（REF02） | ca-runtime | 仅用于 Runtime/Procedure/Predicate 语义对照，不是 Next 实现 |
| 协议标准（REF03） | 3GPP / OpenAPI | 固定标准版本和消息子集，不重新定义标准 |
| 后续晋级目标（TARGET01） | ca-agent | Next 验收后评估晋级 |

Next 是项目群架构、设计、规范和治理规则的唯一集中入口。ca-skills、Compiler、Tool/Provider、OpenAMSM Plugin/Owner、Mock AMF、Skill Studio、Python/Go Runtime 等外部仓的架构、设计和规范原文均迁入本仓，并由功能树映射到权威设计；外部仓继续维护实现代码、测试、发布、部署、运行与故障排查资料，并链接回本仓对应设计。迁移状态见[原始架构与设计资产恢复清单](docs/参考与审计/原始架构与设计资产恢复清单.md)和[跨仓设计资产迁移与一致性审计](docs/参考与审计/跨仓设计资产迁移与一致性审计.md)。

## 架构要点

- 全系统只有一个 Plugin Manager。Plugin 可导出 event.ingress、event.delivery、tools 中一种或多种 Extension。
- Tool 是 Plugin 导出的 Callable Operation，不是独立进程或 Manager。
- 每个 Skill 必须有 SKILL.md；Assurance 可选。无 Assurance 仅 LLM-guided；有效发布 Artifact 支持 Deterministic 和 LLM-guided；无效 Artifact 导入失败。
- when 是可选 Assurance Contract 中的 CEL 选择表达式；predicates.yaml 只用于执行期业务判断。
- CA-SL 1.6.0 是唯一新目标。作者只引用 Capability ID，Compiler 将其链接到唯一公开 Callable；Runtime 在 Scope 内分发。Agent 只消费正式发布的 Assurance Bundle，不调用 Compiler，不实现 Skill Admission。
- Deterministic 与 LLM-guided 经过同一个 Runtime Action Boundary。
- SBI 可携带 JSON 和 multipart 二进制。Event Plugin 处理外部协议；Host 管理 ArtifactStore；Codec 按需作为现有 Tool Plugin 的 Operation 调用。

## 实施顺序

所有变更先关联 Issue，新分支使用[分支命名规范](docs/规范/文档编写与治理规范.md#14-分支命名与生命周期)。Harness 默认采用 Goal 模式，提示词在[文档门禁](docs/规范/文档编写与治理规范.md#13-执行提示词交付门禁)通过后生成。

模块评审按各 SR 的直接输入展开。SKILL.md-only 导入可以单独评审；正式 Assurance 导入等待新版 Compiler 和 Bundle。OpenAMSM Go Plugin 可用测试 Host 做独立模块验收；与 Next 的系统组合安排在 Echo E2E 通过后。设计、代码、模块 AC 与系统 EX 分别记录证据。

## Demo 范围

本仓证明机制正确性和可扩展性，不做生产级资格认证。可靠性与安全 DFX 暂不展开生产方案；不增加 HA/DR/SLA、包签名、Trust Registry、生产密钥管理或复杂多租户治理。基本输入校验、明确错误、fail-closed、Owner 结果语义、最小可观测性和自动化验收仍必须具备。
