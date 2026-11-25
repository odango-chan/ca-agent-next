# 仓库协作指引

本文是 ca-agent-next 自动化与 AI 编码协作的入口规则，不是第二份架构文档。功能分类、需求、设计章节和外部能力导航以《功能树与需求追踪基线》为准。

**强制追踪：任何变更批次开始前必须关联 GitHub Issue；没有覆盖本次范围的 Issue，不得开始修改。** 文档、架构、规范、源码、配置、Schema、测试、CI、迁移、删除和重构均适用。纯文档/治理变更也必须有 Issue，但不因此强制制造无实际需求含义的 SR。

需求入口见[IR 总登记册](docs/IR/IR%20总登记册.md)和[SR 总索引](docs/治理/SR%20总索引.md)。实施批次先确认 IR、目标 SR、设计章节与 Acceptance ID。Next 仅启动 READY 且依赖满足的 SR。按 SR 回填实施 PR/Commit、受测 SHA、命令、环境及验收结果。

## 1. 任务开始流程

1. 阅读 README.md、本文和 docs/治理/功能树与需求追踪基线.md。
2. 查找覆盖本次变更的 GitHub Issue；不存在时先创建 Issue，再开始任何文件修改。Issue 必须写清目标、范围、非目标和验收；范围扩大时先更新 Issue。
3. 根据 Issue、用户任务或 PR 识别仓库、功能树节点、IR 和 SR。纯文字/治理变更若不改变需求、行为或验收，可只关联 Issue，不必人为创建 SR。
4. 若涉及可实施需求，检查 SR 状态、依赖和 Acceptance；只有 READY 且依赖满足的 SR 才能实施。DRAFT / BLOCKED 不得直接实施。
5. 按功能树读取该节点关联的全部必要总体/领域/模块架构文档、设计说明书、规范、外部来源基线和验收要求；一个功能节点可能关联多篇文档，不得假设只有一篇。
6. 实施前核对仓库、分支、HEAD、工作区和外部依赖当前状态。
7. 实施后回填 Issue、IR/SR（适用时）、PR、Commit、Test 和验收证据。

不要要求每项任务阅读所有设计文档。跨功能任务才同时加载多个 Feature。

## 2. 仓库与语言边界

- Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 使用 Python。
- 独立 Plugin 可以使用 Go；Go Plugin 不代表 Go Host。
- ca-agent-demo 是既有 Python 实现和测试证据来源，只能逐文件选择性复用，不得整体复制。
- ca-skill-compiler、ca-skills、ca-client-tools、ca-openamsm-plugin、env-openamsm 等保有独立实现、测试、构建和发布职责；项目群架构、模块设计与规范统一迁入 ca-agent-next，原仓保留必要运行/操作文档并链接中央设计。
- 所有项目群任务从本仓进入。修改协作仓须获得当前任务的授权，并在本仓登记覆盖目标仓、变更范围和验收的 SR。SR 达到 READY 且依赖满足后方可实施，再回填目标仓 PR、Commit 和验收证据。READY 仅表示具备实施条件，不授予写入权限。合并 PR 和发布 Release 需要单独授权。

## 3. 不可违反的架构约束

- 全系统只有一个 Plugin Manager；Plugin 是独立包/进程，可导出 Event ingress、Event delivery、Tools Extension。
- Tool 是 Plugin 导出的 Callable Operation，不是独立进程、Manager 或 Registry。
- 不建立第二 Provider Manager、Tool Registry、Codec Manager、Event Registry 或第二套 IPC。
- 每个 Skill 必须有 SKILL.md；Assurance 可选。无 Assurance 仅 LLM-guided；有效发布 Artifact 支持 Deterministic 和 LLM-guided；无效发布 Artifact 导入失败。
- when 是可选 Assurance Contract 的纯 CEL Skill 选择表达式；predicates.yaml 只用于执行期业务判断。
- Agent 只消费外部已发布 Runtime Artifact，不调用 Compiler Check/Build/Inspect/Verify，不建立 Skill Admission，不导入作者源作为运行时 Artifact。
- Skill 选择先于模式选择；精确 Continuation 恢复原 Run，不重新选择 Skill。
- SkillCatalog 由 Core/Host 拥有；更新原子切换 generation；在途 Invocation 固定 generation。
- Deterministic 与 LLM-guided 共用 Runtime Action Boundary；LLM 不得直接调用 Plugin 或扩大 Callable Scope。
- Owner Receipt / Commit Proof 是 mutation 结果权威；HTTP 200、IPC 成功或 Delivery 成功不能替代；UNKNOWN 不得变成 COMMITTED。
- SBI 可携带 JSON、multipart 和二进制。Event Plugin 处理协议；Host 管理 ArtifactStore；Codec 按需作为现有 Tool Plugin 的 Operation 调用。
- 不增加 activation.yaml、constraint.yaml、supportedModes、Domain/Task Contract Package、第二份 Skill Descriptor、旧版兼容、额外 SHA-256、签名或 Trust Registry。

## 4. Demo DFX 边界

可靠性与安全 DFX 暂不展开生产级方案：不要求生产 HA/DR、SLA、企业 IAM、生产密钥管理、包签名、Trust Registry 或复杂安全运营。

以下属于基本正确性，不能以 Demo 为由省略：输入/Schema/版本/Manifest/路径校验、明确错误、fail-closed、Runtime Callable Scope、Owner Commit Proof、UNKNOWN、Continuation 精确关联、二进制载荷保真和自动化验收。

## 5. 文档变更规则

- 每个变更批次必须先关联 Issue；每个 PR 正文必须引用一个或多个 Issue（例如 `Refs #5`）。Commit 通过所属 PR 追溯到 Issue；禁止无 Issue 的孤立提交/PR。
- 功能增强更新对应功能节点的权威架构/设计文档；新增独立能力时先登记功能树节点，再按复杂度新增一篇或多篇架构/设计文档。
- 功能树与文档为多对多关系：一个节点可关联多篇总体/领域/模块架构和设计文档；一篇文档也可覆盖多个紧密关联节点。不得规定“一个 Feature 只能有一篇设计文档”。
- 总体架构全局只保留一份；领域、子系统和模块架构文档可以有多份，放在 `docs/架构设计/` 的分层目录中。详细机制仍可放在 `docs/设计说明书/`。
- 功能树允许不定深度，各分支按真实职责和边界展开；中间分类节点不强制创建 SR，能独立实施和验收的节点才分解 SR。
- 新需求或行为/验收变化需登记 IR/SR；纯文字、排版、索引或治理刷新若不改变需求语义，可只关联 Issue，不制造空 SR。
- 每份正式架构/设计/规范/治理/验收文档维护完整修订记录，记录日期、修订者/模型、章节、修改内容、原因和关联功能节点/IR/SR/Issue/PR/Commit。历史未记录的信息不得猜测。
- 项目群所有域（包括外部能力域）的架构、模块设计和规范集中在 Next；外部仓保留实现、测试、构建、发布、部署和运行说明，并链接回 Next 对应章节。迁移须保留源仓、源 Commit/PR、原路径、状态和差异。

## 5.1 DeepSeek Harness 文档执行基线

- 文档可执行性以 DeepSeek Harness 在默认模型配置下的独立执行能力为标准，不以人工“看得懂”作为完成标准。
- 默认模型 API alias：`deepseek-flash`（使用 DeepSeek 当前最新 Flash 模型）；默认 `reasoning_effort=low`。不得依赖服务端默认值，因为 DeepSeek API 的默认 effort 为 high；必须显式传入 low。
- 每次可执行性资格验证记录 Harness 版本/配置 Commit、模型 alias、模型列表查询时的展示名称、`reasoning_effort`、运行时间、Issue/SR、设计文档 Commit、执行命令、结果和证据位置。模型 alias 是滚动入口，不是不可变模型快照。
- 设计文档必须给出目标、范围/非目标、模块职责/边界、接口与 Schema、数据/状态、正常与异常流程、目标仓库及代码定位、实施步骤、可执行命令、预期结果、验收证据和未决事项。
- Low 是文档可执行性基线；不得通过升高推理强度、人工口头补充或实施 Agent 自行发明架构来弥补文档缺口。发现冲突或必要信息缺失时，停止受影响工作并报告。
- 文档静态检查与真实 Harness 执行验证分开记录。静态检查通过不等于 Harness 已验证；未运行的模型执行验证必须标记 `NOT_RUN`。CI 不得伪称已完成模型执行验证。

## 6. 全局评审范围（机器可读）

以下 review_scope 是 CI 与评审 Harness 的权威输入。修改时必须按 SR-GOV-001 的要求展示范围差异，不得随意删减或另建第二份配置。

<!-- REVIEW_SCOPE:BEGIN -->
~~~yaml
review_scope:
  schema_version: 1
  profile: demo_prototype
  target:
    description: >-
      建设业务中立的 Python Agent Core，通过可导入 Skill、Plugin 和 Tool Interface Package 扩展业务；
      以 Generic Echo 验证公共机制，再以 OpenAMSM 作为第二个独立业务，验证不修改 Core 即可接入，
      最终完成真实 OpenAMSM Create、Modify、UE-requested Release 的 Demo E2E。
    sequence:
      - generic_echo_vertical_e2e
      - openamsm_second_business_without_core_business_changes
      - real_openamsm_create_modify_release_e2e
  in_scope:
    - id: generic_agent_core
      description: Python Agent Core/Host/Runtime 保持业务中立，新增业务不要求修改 Core 业务路由或状态机。
    - id: unified_plugin
      description: 唯一 Plugin Manager、Plugin Package、IPC 和 Event/Delivery/Tools Extension 分发。
    - id: skill_import_selection
      description: 已发布 Skill 包导入、Core-owned SkillCatalog、when 选择和 Continuation 优先。
    - id: published_assurance
      description: 消费外部 Compiler 发布的 Assurance Artifact；Agent 不内置、不调用 Compiler。
    - id: runtime_action_boundary
      description: Deterministic 与 LLM-guided 共用 Runtime Action Boundary 和 Tool Plugin 路径。
    - id: owner_outcome_semantics
      description: Receipt、Commit Proof、Outcome、UNKNOWN、Wait/Resume/Reconcile 的正确语义。
    - id: event_binary_handoff
      description: SBI JSON/multipart、Content-ID、N1/N2 原始二进制与 Host-owned Artifact Handoff。
    - id: business_neutrality_e2e
      description: Echo 后接入 OpenAMSM，验证新增业务不要求修改 Agent Core，并完成声明的 Demo E2E。
    - id: runnable_examples_acceptance
      description: 新增外部可观察机制必须有可运行 Example 和自动化 Acceptance。
  always_required:
    - id: basic_validation
      description: 基本输入、Schema、版本、Manifest、引用和路径校验；错误明确并 fail-closed。
    - id: runtime_scope_checks
      description: Runtime 必须检查所选 Skill 声明的 Capability/callable scope；LLM 不得绕过 Runtime 直接调用 Plugin。
    - id: owner_commit_proof
      description: 需要 Owner 提交证明的 mutation 不得由 HTTP/IPC 成功或模型文本判定为 COMMITTED；UNKNOWN 保持 UNKNOWN。
    - id: continuation_and_replay
      description: 重复 Event、Continuation 和旧消息不得导致重复 mutation 或推进错误 Run。
    - id: binary_payload_fidelity
      description: 原始 N1/N2 字节、Content-ID 关联和 artifactRef 的来源及传递边界必须正确。
    - id: evidence_integrity
      description: DESIGN、IMPLEMENTED、PASS、NOT_RUN、BLOCKED 必须按真实证据区分，不得虚报测试或 E2E。
  non_goals:
    - id: production_ha_dr
      description: 生产级 HA、跨区域容灾、自动故障转移和灾难恢复。
    - id: production_sla_capacity
      description: 生产级容量规划、弹性扩缩容、性能 SLA/SLO 和多地域部署。
    - id: enterprise_iam_governance
      description: 企业级身份联邦、SSO、集中式生产 IAM 生命周期和复杂多租户治理；不包括 Runtime 基本 Capability/callable scope 检查。
    - id: production_trust_admission
      description: 独立 Skill Admission、生产审批、Owner Trust 治理和 Trust Registry。
    - id: extra_package_integrity
      description: 新增包签名、额外 SHA-256/Digest 或另一套包完整性体系；上游契约已有要求除外。
    - id: production_key_management
      description: 生产级密钥托管、轮换和生命周期管理平台。
    - id: production_security_operations
      description: SIEM、安全运营平台、生产级审计流水线和合规报表体系；不包括必要的诊断日志。
    - id: marketplace_and_auto_install
      description: Marketplace、通用安装器、自动下载、文件监听和通用 Plugin 热更新。
    - id: full_protocol_qualification
      description: 超出当前 Acceptance 声明子集的完整 3GPP 全量协议符合性。
    - id: production_qualification
      description: 生产发布准入、商业 SLA、正式 Production Qualification 和认证。
  review_policy:
    default_review_target: changed_files_and_direct_dependencies
    blocker_requires_traceable_requirement: true
    blocker_requires_verifiable_evidence: true
    missing_non_goal_capability_is_blocking: false
    production_best_practice_alone_is_defect: false
    scope_change_requires_user_approval: true
    unresolved_scope_conflict: SCOPE_DECISION_REQUIRED
    findings_must_include_requirement_location_evidence_and_current_goal_impact: true
  finding_classes:
    - BLOCKER
    - NON_BLOCKING
    - OUT_OF_SCOPE
    - DEFERRED
    - UNVERIFIED
    - SCOPE_DECISION_REQUIRED
~~~
<!-- REVIEW_SCOPE:END -->

## 7. 修订记录

| 日期 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 历史修订者/模型未记录 | 原第 1～11 节及 review_scope | 既有协作约束和机器可读评审范围；逐章历史记录未建立 | 原始修订者未记录，本轮不臆造 | PR #1 |
| 2026-11-25 | GPT-6.2（ChatGPT） | 第 1～6 节 | 将功能识别和按需阅读流程交给功能树，精简硬约束，保留 review_scope 原始区块 | Agent.md 过长且重复设计细节 | F01～F07、G01；SR-001～011；PR #1 |
| 2026-11-25 | Codex | 第 2 节 | 明确跨仓写入须获当前任务授权 | 区分实施就绪与写入授权 | PR #1 |
| 2026-11-25 | Codex / GPT-6 | §2、§5 | 明确中央设计归属 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | GPT-6.2（ChatGPT） | §1、§5、§5.1 | 强制 Issue 追踪；允许多层功能树、多篇模块架构文档和外部域设计集中；明确 DeepSeek Flash + Low 执行基线 | 使治理规范可追踪且文档可由低推理强度 Harness 独立执行 | Issue #5；IR-006 |
