# CA Agent Next

CA Agent Next 是下一代通用 Agent 的独立实现仓，目标是用尽可能少的机制，通过 Skill 与 Plugin 扩展不同业务，而不为每个业务修改 Agent Core。

**Agent Core / Host / Runtime 固定使用 Python。** 独立运行的 Plugin 可以使用 Go；Go Plugin 不意味着 Go Agent Core。

**当前状态：** PR #1 是架构与文档基线，仍需评审；本仓尚无已验收的 Agent Runtime 实现。文档设计、代码实现和 Acceptance 结果必须分别表述。

## 仓库职责

| 仓库 | 职责 |
|---|---|
| ca-agent-demo | 既有 Python Agent/Host/Runtime 代码、测试和复用证据；逐文件选择性复用 |
| ca-agent-next | 新一代 Python Agent Core / Host / Runtime 实现 |
| ca-agent | 当前稳定实现及后续晋级目标 |
| ca-skill-compiler | CA-SL 编译、链接、Artifact Build/Verify 和发布工具链 |
| ca-skills | CA-SL 规范与 Skill 作者源 |
| ca-client-tools | Go Tool 实现、Tool Interface Package 和 Owner 交互 |
| ca-openamsm-plugin | 独立 Go OpenAMSM SBI Event ingress / Delivery Plugin |

演进路径：

~~~text
ca-agent-demo（代码/测试证据）→ ca-agent-next（新 Python 实现）→ ca-agent（验收后晋级）
~~~

## 从这里开始

- [文档总目录与索引](docs/治理/文档总目录与索引.md) — 所有正式文档入口。
- [CA Agent Next 架构设计](docs/架构设计/CA%20Agent%20Next%20架构设计.md) — 本仓唯一总体架构。
- [文档编写与治理规范](docs/规范/文档编写与治理规范.md) — 文档语言、目录、命名和维护规则。
- [Skill / Assurance 格式规范](docs/规范/SKILL%20与%20Assurance%20格式规范.md) — Skill 作者源与发布运行包边界。
- [Plugin 包与 IPC 协议规范](docs/规范/Plugin%20包与%20IPC%20协议规范.md) — Manifest v1alpha1 和 IPC v1alpha1。
- [公共契约与所有权规范](docs/规范/公共契约与所有权规范.md) — Event、Tool、Owner、Skill 和 Artifact 的权威来源。
- [Demo 验收基线](docs/验收与实施/Demo%20验收基线.md) — Echo 与 OpenAMSM 的验收门槛。
- [DeepSeek Harness 实施提示词](docs/验收与实施/DeepSeek%20Harness%20实施提示词.md) — 仅针对本仓的分阶段实施任务。

## Skill 模型

每个 Skill 都必须有 SKILL.md，Assurance 是可选的：

- 只有 SKILL.md：仅 LLM-guided，不具备确定性执行。
- SKILL.md + 有效发布 Assurance Artifact：支持 Deterministic 和 LLM-guided。
- 发布 Artifact 缺失、格式错误或依赖无法解析：导入失败，不得降级。
- when 在作者源 assurance/contract.yaml 中定义，由外部 Compiler 在发布前静态检查。
- Agent 只消费已发布 Artifact，不调用 Compiler Check/Build/Inspect/Verify，也不设置独立 Skill Admission。
- SkillCatalog 在内存中缓存 SKILL.md、候选元数据和已反序列化的 when 程序；每个新 Event 使用当前 input 独立求值。

## Plugin 与协议载荷

Plugin 是统一 Plugin Manager 管理的独立包/进程，可暴露 event.ingress、event.delivery、tools 中的一种或多种 Extension。Tool 是 Plugin 的 Callable Operation，不是独立进程。不存在第二 Provider Manager、Tool Registry 或 Codec Manager。

SBI 不限于 JSON。Event Plugin 解析 JSON / multipart/related 和 Content-ID，保留原始二进制；Host 管理 ArtifactStore 和 opaque artifactRef。Skill 需要 NAS/NGAP 结构化字段时，按需调用 ca-client-tools Tool Plugin 的 Codec Operation；不需要时直接传递原始 artifactRef。

## Example-first 开发

第一个垂直示例为 Echo：Python Agent Core、一个独立 Go Plugin（同进程暴露 Event/Delivery/Tools）、一个 SKILL.md-only Skill 和一个含已发布 Assurance Artifact 的 Skill。

每个新增外部可观察机制都必须在同一变更中增加可运行 Example 和自动化 Acceptance。Echo 通过后，再以 OpenAMSM 作为第二个业务证明：只通过 Plugin、Skill、Tool Interface Package 和部署配置新增业务，不修改 Agent Core。

## Demo 范围

本仓证明通用机制和基本正确性，不进行生产级资格认证。可靠性与安全 DFX 暂按 Demo 场景处理。

不要增加额外 SHA-256 包完整性机制、包签名、Trust Registry、Domain/Task Contract Package、旧版兼容、Marketplace、自动下载、文件监视器、通用 Plugin 热更新、生产 HA/DR/SLA 或复杂多租户治理。

基本 YAML/Schema/版本/路径检查、明确错误、fail-closed、Owner outcome 正确性、最小日志和自动化测试仍然必须具备。
