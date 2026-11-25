# 仓库协作指引

本文件是 ca-agent-next 自动化和 AI 编码协作的唯一入口规则。正文使用中文；架构和机制的权威定义位于 docs，不得把本文件扩展成第二份架构文档。

## 一、开始任务前

非简单任务必须先阅读：

1. README.md。
2. docs/架构设计/CA Agent Next 架构设计.md。
3. docs/治理/文档总目录与索引.md。
4. docs/规范/文档编写与治理规范.md、docs/规范/文件结构规范.md。
5. 与任务对应的规范和设计说明书。
6. docs/验收与实施/演示验收基线.md、docs/验收与实施/实施路线与阶段门槛.md。
7. docs/规范/SR 管理规范.md、docs/治理/SR 总索引.md 和 docs/治理/实施状态总览.md。
8. docs/SR/ 中与本次任务相关的 SR 及其设计依据、验收条件。
9. 相关实现、测试、外部仓库接口和当前 PR/Commit 证据。

如果实现与规范不一致，先报告具体文件、接口和差异，不得自行创造第三套定义。状态快照必须在实施前重新核对。

## 二、仓库与语言边界

- Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 使用 Python。
- 独立 Plugin 可以使用 Go；Go Plugin 不代表 Go Host。
- ca-agent-demo 是既有 Python 代码和测试证据来源，只能按文件和依赖关系选择性复用，不得整体复制。
- ca-agent-next 是独立的新实现，不以 ca-agent 的 Go 源码作为本次重构基础。
- ca-skill-compiler、ca-skills、ca-client-tools、ca-openamsm-plugin 是独立权威仓，不复制它们的实现或语言语义。
- 未经用户明确授权，不修改兄弟仓库，不合并 PR，不发布 Release。

## 三、Plugin 与 Tool 架构硬约束

- 全系统只有一个 Plugin Manager，负责 Plugin 加载、生命周期、握手、IPC、关联和 Extension 分发。
- Plugin 是包/独立进程和生命周期单元，可导出 event.ingress、event.delivery、tools 中的一种或多种 Extension。
- Tool 是 Plugin 导出的可调用 Operation，不是独立进程、Plugin Manager、Runtime 或 Registry。
- Tool Plugin 是导出 tools Extension 的 Plugin；一个 Plugin 可导出多个 Capability 和多个 Operation。
- Tool 的 Callable ID、输入/输出 Schema、Effect、Capability 归属和 Owner 结果语义，以其权威 Tool Interface Package 为准。
- Plugin Manager 不选择 Skill、不授权 Action、不判断 Owner 是否 COMMITTED。
- 不建立独立 Provider Manager、Tool Registry、Codec Manager、Event Registry 或第二条授权/分发路径。
- ca-client-tools 的 Provider v2 可以在迁移期由统一 Plugin Manager 内部适配，不得形成永久第二套 Manager。
- ca-openamsm-plugin 只负责 SBI Event ingress / Delivery，不负责 Skill 选择、Owner Tool 或 Runtime。

## 四、Skill 与 Assurance 硬约束

- 每个 Skill 必须包含 SKILL.md。
- 作者源 assurance/ 可选；存在时按 CA-SL v1alpha5 规则提供完整 Assurance 源文件集合。
- Agent 只消费已发布 Skill 包：SKILL.md-only 包直接导入；含 Assurance 的包必须携带受支持的 Compiler 发布 Artifact。
- Agent 不导入 Assurance 作者源 YAML，不调用 Compiler Check/Build/Inspect/Verify，不重编译、不重建发布 Artifact，也不实现独立 Skill Admission。
- 没有有效 Assurance Artifact 时只能 LLM-guided；存在有效 Artifact 时可 Deterministic 或 LLM-guided；Artifact 缺失、格式错误、引用缺失或依赖未解析时导入失败，绝不静默降级。
- Skill 选择只使用 assurance/contract.yaml 的可选 when（CEL）。predicates.yaml 仅用于执行期业务判断。
- when 只读取规范化 Event 的 event.type 和 Contract.requestSchema 声明的 input；不调用 Tool、不读取 Observation、不访问可变 Host 状态。
- 不增加 activation.yaml、constraint.yaml、supportedModes、第二份 LLM Contract、Domain/Task Contract Package 或重复 Skill Descriptor。
- CA-SL v1alpha5 是唯一作者格式；语言解析、静态检查、链接和 Artifact 发布语义归 ca-skill-compiler。

## 五、SkillCatalog 与选择流程

- SkillCatalog 由 Python Core/Host 拥有，是进程内不可变快照；不属于 Plugin Manager。
- 启动或显式导入/更新时读取 Skill 包、缓存完整 SKILL.md、候选元数据、发布 Artifact 引用、已反序列化 when 程序和类型环境。
- 每个新 Event 用当前 input 求值；只缓存程序，不缓存上一个 Event 的 true/false 结果。
- 更新成功后原子激活新 generation；更新失败保留旧 generation；在途 Invocation 固定原 generation。
- references/ 和大型知识材料按需加载；不要求文件监视器、自动下载、分布式缓存或通用热更新。
- 精确 continuation 优先恢复原 Run，不重新选择 Skill。
- 一个 when=true 直接选择；多个 true 只在精确候选集合内消歧；没有 true 时只对未声明 when 的 Skill 做 SKILL.md 语义选择。
- when=false 或运行期错误的 Skill 不得重新进入无条件候选；无候选时澄清或拒绝，不得无 Skill 绑定地回退到 Generic Agent。

## 六、Runtime 与 Action Boundary

- Deterministic Procedure Engine 和 LLM Model Loop 是不同的 Action 提议来源，但必须经过同一个 Runtime Action Boundary。
- Host 不直接调用 Plugin Tool；Runtime 负责当前 Run、Skill 声明 Callable Scope、Schema、Effect、Artifact 引用和状态检查。
- Plugin Manager 只负责分发；Tool Plugin 负责执行；Owner 是业务状态和提交结果的最终权威。
- READ Tool 结果是带来源的 Observation；Owner Receipt / Commit Proof 是业务结果 Evidence；模型生成文本不是事实证据。
- HTTP 200、IPC 成功或 Delivery 成功不能替代 Owner 提交证明；UNKNOWN 不得映射为 COMMITTED。
- Wait/Resume/Continuation 必须关联原 Run、业务身份和等待代际，不能用 HTTP/2 stream ID 替代 Run ID。

## 七、SBI 二进制与 Codec

- SBI 不限于 JSON，可包含 multipart/related 和原始二进制。
- Event Plugin 负责协议解析、Content-ID 关联和原始字节暂存；Host 管理 ArtifactStore、artifactRef、Run 关联和访问授权。
- 原始二进制不进入 NDJSON 帧或模型 Context。
- Skill 需要结构化 NAS/NGAP 字段时，按需调用 ca-client-tools tools Extension 中正式发布的 Codec Operation；不需要时传递原始 artifactRef。
- 不新增 Codec Plugin/Manager，不在 Host 复制深度协议解码器；未资格化的消息子集不得声称支持。

## 八、Demo 禁止项与正确性底线

Demo 阶段不建设生产级可靠性与安全 DFX，不增加额外 SHA-256/内容完整性机制、包签名、Trust Registry、生产密钥管理、HA/DR/SLA、复杂分布式总线或多租户治理。

以下属于功能正确性，不能以 Demo 为由省略：输入/Schema/版本/路径校验；契约不匹配时报错；失败时 fail-closed；UNKNOWN 不得提升为 COMMITTED；Owner Receipt/Commit Proof 不能被 HTTP 成功或 Plugin 传输成功替代；关键机制有自动化测试和真实可追溯证据。

## 九、SR 驱动实施规则

- 每项正式实施必须关联 docs/SR/ 中的 SR；SR 文件是需求范围和验收条件的权威记录。
- 只实施状态为 READY 且依赖满足的 SR；DRAFT、BLOCKED、SUPERSEDED、CANCELLED 均不得实施。
- 实施 PR 必须引用 SR ID；更新 SR 的 Issue/PR/Commit、测试命令和 Acceptance 证据。
- 设计文档刷新先做版本差异和 SR 影响分析；新增要求创建新 SR，改变既有要求创建替代 SR，纯编辑不创建 SR。
- SR 进入 IMPLEMENTED 不代表 VERIFIED；所有验收条件真实通过后才能 VERIFIED。
- 每轮同步更新 SR 总索引和实施状态总览。

## 十、文档变更规则

- 架构边界变化：更新唯一总体架构、必要的决策记录和索引。
- 机制行为变化：更新对应设计说明书。
- 文件结构、字段、协议或公共契约变化：更新唯一规范并核对所有消费者。
- 新增外部可观察机制：同一变更必须增加可运行 Example 和 Acceptance。
- 所有文档使用中文正文和中文主题文件名；代码、字段、标准术语保留精确原文。
- 新增、移动、废弃文档必须同步更新文档总目录和收敛台账。
- 设计、实现、测试通过是三种不同状态，不得混写。


## 十、评审范围与边界

- 项目级目标、必须范围、始终必须满足的正确性要求、非目标和评审策略，以本文件末尾唯一的 review_scope 区块为准。
- 必须遵守 docs/规范/文档编写与治理规范.md 中的统一评审规则。
- 本次 SR/PR/Acceptance 可以缩小全局范围，不得自行扩大；默认只评审本次变更及其直接依赖。
- 明确排除的生产级能力缺失，不得单独认定为当前缺陷、P0/P1 或合并阻塞。
- 基本输入/Schema/版本/路径校验、fail-closed、Runtime Capability/callable scope、Owner Receipt/Commit Proof、UNKNOWN、Continuation、原始二进制载荷保真和必需 Example/Acceptance 始终属于当前正确性要求。
- 如果认为某项非目标是当前目标成立的必要条件，标记 SCOPE_DECISION_REQUIRED，给出证据并等待用户确认；不得自行修改范围或要求实施 Agent 扩建。
- BLOCKER 必须追溯到具体要求并给出可复核证据；生产最佳实践、未来风险或个人偏好本身不足以构成 BLOCKER。
- 分类使用 BLOCKER、NON_BLOCKING、OUT_OF_SCOPE、DEFERRED、UNVERIFIED、SCOPE_DECISION_REQUIRED。分类与 P0/P1/P2 优先级分开判断。
- 如果 CI 已生成评审上下文，评审 Agent 必须使用；如果生成物不存在，必须手动读取本区块，不得假设自动注入已完成。

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

## 十一、修订记录

| 日期 | 修订 | 说明 |
|---|---|---|
| 2026-11-25 | R2 | 增加机器可读项目评审范围、统一评审边界和 SR 追踪入口。 |
