# 仓库协作指引

本文是 ca-agent-next 自动化与 AI 编码协作的入口规则，不是第二份架构文档。功能分类、需求、设计章节和外部能力导航以《功能树与需求追踪基线》为准。

需求入口见[IR 总登记册](docs/IR/IR%20总登记册.md)和[SR 总索引](docs/治理/SR%20总索引.md)。实施批次先确认 IR、目标 SR、设计章节与模块 Acceptance ID。Next 仅启动 READY 且当前实施阶段的实施依赖已满足的 SR。设计评审/READY 不得被下游实施依赖或系统级 EX 阻塞；依赖只阻塞实际消费它的阶段或 AC。模块 AC 与系统级 EX 分开管理，EX 不作为单个模块 SR 的默认实施前置条件。按 SR 回填实施 PR/Commit、受测 SHA、命令、环境及验收结果。

## 1. 任务开始流程

0. 创建或引用覆盖本批变更的 Issue，并按[治理规范](docs/规范/文档编写与治理规范.md#14-分支命名与生命周期)命名新分支。
1. 阅读 README.md、本文和 docs/治理/功能树与需求追踪基线.md。
2. 根据用户任务、Issue 或 PR 变更识别仓库、Feature / IR / SR。
3. 检查 SR 状态、依赖类型（设计/实施/模块验收/系统集成）和本次要执行的阶段/Acceptance；只检查本阶段直接消费的依赖。DRAFT / BLOCKED 不得直接实施；READY 仍须通过当前阶段实施门禁。不得把功能阶段顺序、文档引用或系统级 EX 推断成未登记的前置依赖。
4. 只读取对应功能设计说明书、相关规范、外部 EC 权威文档和验收要求。
5. 实施前核对仓库、分支、HEAD、工作区和外部依赖当前状态。
6. 实施后回填 SR、Issue、PR、Commit、Test 和验收证据。

不要要求每项任务阅读所有设计文档。跨功能任务才同时加载多个 Feature。

DeepSeek Harness 默认使用 Goal 模式。按[SR 管理规范](docs/规范/SR%20管理规范.md#9-deepseek-harness-goal-与交付门禁)组批，并在文档门禁和所需审查通过后生成执行提示词。

## 2. 仓库与语言边界

- Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 使用 Python。
- Python 工程工具链设计入口见 [G02 Python 工程工具链与环境管理](docs/设计说明书/G02-Python工程工具链/Python工程工具链设计说明书.md)；SR-028 当前为 DRAFT，uv 尚未实施。只有 SR-028 经评审达到 READY 并建立独立实施 Issue 后，才按其要求迁移依赖、锁文件、worktree 环境和 CI；不得将 uv 迁移混入 SR-001 PR #32。
- 独立 Plugin 可以使用 Go；Go Plugin 不代表 Go Host。
- ca-agent-demo 是既有 Python 实现和测试证据来源，只能逐文件选择性复用，不得整体复制。
- ca-skills、ca-skill-compiler、ca-client-tools、ca-openamsm-plugin、env-openamsm、env-5gc-sim、ca-skill-studio-demo 等保有独立实现和发布职责；ca-runtime 与 ca-agent 是参考/目标仓，不是 Next 运行时依赖。
- 项目群所有仓的架构设计、功能设计、协议规范和 ADR 统一集中在 ca-agent-next；其他实现仓保留源码、测试、发布、部署、运行和故障排查文档，并链接回本仓对应 Feature/设计章节。迁移原文必须保留源仓、源路径、固定 SHA 和原始状态，不能把历史提案改写成当前规范。
- 所有项目群任务从本仓进入。修改协作仓须获得当前任务的授权，并在本仓登记覆盖目标仓、变更范围和验收的 SR。SR 达到 READY 且当前实施阶段的实施依赖满足后方可实施，再回填目标仓 PR、Commit 和验收证据。设计/治理 Issue 与代码实施 Issue 分开；实施 Issue 必须在代码开始前创建。READY 仅表示具备实施条件，不授予写入权限。每批实现必须 Commit、Push 并核对远端 SHA；合并 PR 和发布 Release 需要单独授权。

- 规范或设计尚在评审时，负责人可按 [SR 管理规范 §8.2](docs/规范/SR%20管理规范.md#82-使用评审中的固定提交开展受限实施)批准固定 PR SHA，供 READY 阶段实施和验收。按 SR 记录范围、授权和证据。正式发布、集成和主分支可达性按各阶段要求核对。

## 3. 不可违反的架构约束

- 全系统只有一个 Plugin Manager；Plugin 是独立包/进程，可导出 Event ingress、Event delivery、Tools Extension。
- Tool 是 Plugin 导出的 Callable Operation，不是独立进程、Manager 或 Registry。
- 不建立第二 Provider Manager、Tool Registry、Codec Manager、Event Registry 或第二套 IPC。
- 每个 Skill 必须有 SKILL.md；schemas/、scripts/、references/、assets/ 是 Package 根目录共享资源，Assurance 可选且只含 contract.yaml / procedure.yaml / predicates.yaml。无 Assurance 仍可使用共享资源并仅 LLM-guided；有效发布 Assurance Artifact 支持 Deterministic 和 LLM-guided；无效 Assurance Artifact 导入失败。
- when 是可选 Assurance Contract 的纯 CEL Skill 选择表达式；predicates.yaml 只用于执行期业务判断。
- Skill 源编写与评审必须遵循[中央 SKILL 作者规范](docs/规范/SKILL作者规范.md)；CA-SL 1.6.0 完整语言规范仍是机器语义的唯一权威。作者规范还规定 Package 根目录共享 Schema / Script、Script Registry、Host Script Execution、SourcePath / arguments、when / Wait、Evidence / UNKNOWN、Node 四阶段与拆分 / 合并、注释原则及 AI Authoring 约束；v1alpha5 原文只读留档，不提供兼容或自动迁移。
- Agent 只消费外部已发布 Skill Bundle；存在 Assurance 时同时消费正式 Runtime Artifact。无 Assurance Bundle 可携带共享资源而不生成 Compiler Artifact；Agent 不调用 Compiler Check/Build/Inspect/Verify，不建立 Skill Admission，不把 Assurance 作者源作为运行时 Artifact。
- Skill 选择先于模式选择；精确 Continuation 恢复原 Run，不重新选择 Skill。
- SkillCatalog 由 Core/Host 拥有；更新原子切换 generation；在途 Invocation 固定 generation。
- Deterministic 与 LLM-guided 共用 Runtime Action Boundary；LLM 不得直接调用 Plugin 或扩大业务 Capability Scope。当前 Skill 有 `scripts/manifest.yaml` 登记脚本时，Host 即通过 host.skill-script.execute system Capability 向 LLM 提供同一 Script Runner；LLM 与 Assurance 使用相同脚本集合，不设置逐脚本标记或额外 Host 开关。不得执行模型提交代码、任意路径或命令。
- Owner Receipt / Commit Proof 是 mutation 结果权威；HTTP 200、IPC 成功或 Delivery 成功不能替代；UNKNOWN 不得变成 COMMITTED。
- SBI 可携带 JSON、multipart 和二进制。Event Plugin 处理协议；Host 管理 ArtifactStore；Codec 按需作为现有 Tool Plugin 的 Operation 调用。
- Event/Delivery Plugin 本地 staging 与 Host→Tool Artifact Channel 是两条不同路径。ca-host.artifact-store/v1 已冻结；ca-client-tools Provider v1.2.0 已实现消费，ca-agent Go Host main 447d0cc 有 P1 验收证据。Next Python Host 的 ArtifactStore / Channel 尚未实现，因此 Next 的 artifact-bearing Provider binding 仍必须 NOT_CONFIGURED，并在远端 I/O 前拒绝。必须遵循 v1 的随机 opaque artifactRef、Invocation/direction/slot 绑定、loopback HTTP/1.1 通道、大小/生命周期限制、逐 Artifact SHA-256 传输校验和原子发布；该 SHA-256 不是引用身份或内容寻址。不得把 Event stagingPath 传给 Provider，不得将原始 bytes/Base64 放入 NDJSON。
- 不增加 activation.yaml、constraint.yaml、supportedModes、Domain/Task Contract Package、第二份 Skill Descriptor、旧版兼容、额外 SHA-256、签名或 Trust Registry。
- **CA-SL 1.6.0 单版本、绝不兼容旧版（Issue #40 / IR-008 / SR-029）**：下一正式作者/Compiler/Runtime/Studio 语言目标只采用 1.6.0，不再使用 v1alpha6 命名。Skill 作者只引用 Capability ID，每个 Skill-facing Capability ↔ 唯一公开 Callable；Operation/Observation 是 Node 阶段，不创建独立 Operation ID。Compiler 将 Capability 静态链接为唯一 Callable Binding；Runtime 仅按已编译 Binding 的 Scope/kind/Effect/Schema 派发；Studio Package Explorer 只展示 Capability。
- 新 Compiler 的 Parser、BuildRequest/BuildResult、Check/Build/Verify、Runtime Artifact，Agent Importer/Runtime、Studio 和 ca-skills Bundle **一律不接受旧 CA-SL v1alpha5、旧 Build DTO、旧 Artifact/Bundle、旧式 Callable 作者源**。无兼容层、版本协商、双轨、别名、fallback、自动迁移或转换器。历史 Release/Golden 仅只读留档，不得作为 1.6.0 产品 PASS；旧 Skill 必须重写、重新编译和发布。
- CA-SL 1.6.0 机器 languageTarget、正式 Schema、Owner/Provider 一对一 Package、Compiler Artifact/Binding、Bundle 均须各 Publisher 冻结并有新 Golden/CI 实证；当前 **1.6.0 NOT_RELEASED**。设计文档标记为待评审并不等于 SR READY，更不等于代码实施授权。只读取本分支正式目标文档，不从历史参考原文构造新运行时兼容路径。

## 4. Demo DFX 边界

可靠性与安全 DFX 暂不展开生产级方案：不要求生产 HA/DR、SLA、企业 IAM、生产密钥管理、包签名、Trust Registry 或复杂安全运营。

以下属于基本正确性，不能以 Demo 为由省略：输入/Schema/版本/Manifest/路径校验、明确错误、fail-closed、Runtime Callable Scope、Owner Commit Proof、UNKNOWN、Continuation 精确关联、二进制载荷保真和自动化验收。

## 5. 文档变更规则

- 功能增强：更新对应 Feature 的原设计说明书和必要规范。
- 新增独立功能：先登记 Feature/SR，再新增功能设计说明书。
- 新需求：创建 SR；一个 SR 可对应多个 Issue，一个 Issue 可覆盖多个相关 SR，但必须逐项列明。
- 不因每个 Issue 新建设计文档；SR 记录需求范围和验收，功能设计说明书记录完整机制设计。
- 每份正式文档维护修订记录，记录日期、修订者/模型、章节、修改内容、原因和关联 Feature/SR/Issue/PR/Commit。历史未记录的信息不得猜测。
- 项目群设计按功能集中到 Next；移交须核对发布版本、中央章节、历史和目标仓 SR。
- 外部仓的架构、设计、规范、ADR 迁入 Next 后，外部仓只保留实现/测试/发布/运行资料及指向 Next 的链接；不得在兄弟仓维护第二份权威设计副本。迁移原文应放入参考/归档目录，附 source repository、source path、fixed SHA、source status；Next 目标设计必须从未实现视角独立写全，并另行核对当前代码/测试/PR/运行证据。
- 任何文档刷新都同步更新功能树、文档总索引、SR 总索引、实施状态和跨仓迁移审计；静态链接通过不代表设计 READY，设计 READY 不代表代码 PASS。

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
| 2026-11-25 | GPT-6.2（ChatGPT） | 第 2、3、5 节 | 明确外部架构/设计/规范/ADR 全部集中到 Next，兄弟仓只保留实现资料并链接回中央设计；增加未发布 Host→Tool Artifact Channel fail-closed 约束 | 防止设计分叉和 Provider 误用 Event staging | EC01～EC07、REF01～REF03；SR-015～SR-023；Issue #12 |
| 2026-11-25 | Codex | 第 2 节 | 明确跨仓写入须获当前任务授权 | 区分实施就绪与写入授权 | PR #1 |
| 2026-11-25 | Codex | 第 5 节 | EC02 Compiler 设计集中归档 | 明确设计与机器契约所有权 | SR-012、#2 |
| 2026-11-25 | Codex / GPT-6 | §2、§5 | 明确中央设计归属 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | Codex | §1 | 加入 Issue、分支命名和 Goal 入口 | 统一交接门禁 | [Issue #5](https://github.com/odango-chan/ca-agent-next/issues/5) |
| 2026-11-25 | Codex | 第 2 节 | 引用固定 PR SHA 的分阶段实施规则 | 支持先验证再定稿 | SR-013、PR #7 |
| 2026-11-25 | GPT-6.2（ChatGPT） | 第 3、4、7 节 | 更正 ca-host.artifact-store/v1 已冻结、Provider/Go Host 外部实现已存在、Next Python Host 尚未实现的三层状态；明确 SHA-256 仅为既有协议传输校验 | 消除 F05、F03.05 与源仓实现状态冲突，避免把外部 PASS 计入 Next | F05、F03.05、SR-009、SR-010；Issue #12 |
| 2026-11-26 | GPT-6.2（ChatGPT） | 第 1、2、5 节 | 明确设计/实施/AC/EX 分阶段门禁，分离设计与实施 Issue，并要求实施 Commit/Push 后核对远端 SHA | 防止独立 SR 被无关下游依赖或系统级 EX 阻塞，并确保交付可追溯 | Issue #21；SR 管理规范 §6.1；PR #20 |
| 2026-11-26 | GPT-6（ChatGPT） | §3、修订记录 | 明确 CA-SL 1.6.0 Capability-first 双向一对一、Compiler Binding、全链路绝不兼容旧版和设计待评审与实施 READY 分离 | 避免 Harness 为历史 v1alpha5 擅自构建兼容适配或提前实施 | Issue #40；IR-008；SR-029 |
| 2026-11-27 | GPT-6.2（ChatGPT） | §3、修订记录 | 将中央 SKILL 作者规范加入仓库协作入口，明确作者规范与 CA-SL 1.6.0 语言规范的权威边界 | 防止作者 / Harness 从历史 v1alpha5 资料或注释推断新版语法 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | GPT-6.2（ChatGPT） | §3、修订记录 | 扩展中央作者规范的协作摘要，覆盖 Package / Schema、数据流、when / Wait、Evidence / UNKNOWN 和 AI Authoring，而不只列 Node / 注释 | 避免 Agent.md 将规范范围缩窄，导致 Harness 漏读适用规则 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | GPT-6.2（ChatGPT） | §3、修订记录 | 将根目录共享资源、Host Script Execution system Capability 和无 Assurance Bundle 规则纳入全局架构约束 | 防止 Harness 将 schemas/scripts 放回可选 Assurance 或实现任意 Python 执行 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | GPT-6.2（ChatGPT） | §3、修订记录 | 删除 Host Script Execution 的逐脚本与 Host 配置双门禁，改为 LLM 与 Assurance 共用 Registry / Script Runner | 保持模型与确定性执行能力一致，同时禁止任意代码、路径和命令 | Issue #49；IR-008；SR-032 |
