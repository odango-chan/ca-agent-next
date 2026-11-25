# Agent.md — 仓库协作指引

本文是 ca-agent-next 的自动化与 AI 编码协作入口。所有正文使用中文；代码、API、字段名和标准术语保留原文。

## 1. 开始任务前必须阅读

非简单任务开始前，按顺序阅读：

1. README.md。
2. docs/治理/文档总目录与索引.md。
3. docs/规范/文档编写与治理规范.md。
4. docs/架构设计/CA Agent Next 架构设计.md。
5. 与任务相关的设计说明书和规范。
6. docs/验收与实施/Demo 验收基线.md。
7. docs/验收与实施/实施路线与阶段门槛.md。
8. 相关实现、外部接口、测试和当前 PR/Issue。

如果实现与规范不一致，停止并报告具体文件、接口和差异，不得自行创造第三套定义。

## 2. 仓库与语言边界

- Agent Core、Host、Agent Model Loop、Skill Importer、Skill Resolver 和 Runtime 使用 Python。
- 独立 Plugin 可以使用 Go；Go Plugin 不代表 Go Host。
- ca-agent-demo 是既有 Python 实现和测试证据来源，只能逐文件选择性复用。
- ca-agent-next 是独立的新实现，不整体复制 ca-agent-demo。
- ca-skill-compiler、ca-client-tools、ca-skills、ca-openamsm-plugin 和 ca-agent 是独立权威仓。
- 未经用户明确授权，不修改兄弟仓库。

## 3. Skill 与发布 Artifact 约束

- 每个 Skill 必须有 SKILL.md。
- Assurance 是可选的；没有 Assurance Artifact 时仅 LLM-guided。
- 有效发布 Assurance Artifact 支持 Deterministic 和 LLM-guided。
- 发布 Artifact 缺失、无效、格式不支持、必需文件不全或依赖无法解析时，导入失败，不得静默降级。
- 作者源中的 assurance/ 包含 contract.yaml、procedure.yaml、predicates.yaml；无 Predicate 时使用空 PredicateSet。
- Contract 位于可选 assurance/contract.yaml；when 是其中唯一正式 Skill 选择表达式。
- when 是发布前由外部 Compiler 静态检查的纯 CEL；predicates.yaml 只用于执行期业务判断。
- Agent 只消费外部发布的 Runtime Artifact；不调用 Compiler Check/Build/Inspect/Verify，不重写 Compiler 语义，不设置 Skill Admission。
- Agent 只做发布包基本结构、必需文件、格式、路径、类型数据和 Tool/Capability 依赖检查。
- SKILL.md-only 包直接导入，不调用 Compiler。
- LLM 创建或修改 Assurance 作者源后，必须经过外部发布流程生成 Artifact，才能作为确定性 Skill 使用。
- Skill 选择先于模式选择；精确 continuation 先恢复原 Run。
- when=true 的一个候选直接选择；多个候选只在精确集合内消歧；没有 true 时只对无 when 的 Skills 做 SKILL.md 语义选择；false/error 的 Skill 不得重新加入语义候选。
- SkillCatalog 属于 Python Core/Host，不属于 Plugin Manager。显式导入/更新读取 Skill 包并构建候选 generation，成功后原子激活；在途 Invocation 固定 generation。
- when 程序导入时反序列化一次，每个新 Event 使用当前 input 独立求值，不缓存跨 Event 结果。
- 不增加 activation.yaml、constraint.yaml、supportedModes、第二份 LLM Contract、Domain Contract Package、TaskContract Package 或 Event→Skill 表。

## 4. 统一 Plugin 机制

- 全系统只有一个 Plugin Manager。
- Plugin 是由统一 Manager 管理的独立包/进程，可导出 event.ingress、event.delivery、tools 中一种或多种 Extension。
- Tool 是 Plugin 的 Callable Operation，不是独立进程或 Manager。
- Tool Plugin 是导出 tools Extension 的 Plugin；一个 Plugin 可以暴露多个 Tool。
- Tool Interface Package 是 Callable ID、输入/输出 Schema、Effect、Capability 和 Owner outcome/receipt 语义的唯一权威来源。
- 不创建独立 Provider Manager、Tool Registry、Codec Manager 或第二套 IPC。
- ca-client-tools 通过同一个 Plugin Manager tools Extension 接入；provider/v2 适配只能作为 Manager 内部过渡 Driver。
- ca-openamsm-plugin 只负责 SBI Event ingress/Delivery，不选择 Skill，不实现 Owner Tools、RunStore 或 Runtime。
- Plugin Manifest 使用 YAML；不引入第二种 JSON Manifest。

## 5. Runtime 与 Owner 结果边界

- Deterministic Procedure Engine 与 LLM Model Loop 都必须经过同一个 Runtime Action Boundary。
- Runtime 检查当前 Skill 声明的 Callable Scope、Callable ID、输入 Schema、Effect、Artifact 引用和 Run 状态。
- LLM 不得直接调用 Plugin、扩大 Callable Scope、伪造 Observation/Evidence 或声明 Owner mutation 已提交。
- READ Tool 结果作为带来源的 Observation。
- MUTATION 结果按 Owner Receipt/Commit Proof 契约解释。
- HTTP 200、IPC 成功和 Delivery 成功不能替代 Owner Commit Proof。
- UNKNOWN 不得映射为 COMMITTED。

## 6. SBI 与二进制 Artifact

- SBI 可能包含 JSON、multipart/related 和二进制。
- Event Plugin 负责协议解析、Content-ID 关联和原始字节提取/编码。
- Host 拥有 staging 目录、ArtifactStore、opaque artifactRef、Run 关联和访问控制。
- 原始二进制不进入 NDJSON 或模型 Context；不使用 Base64 传输。
- Codec 按需作为 ca-client-tools 的 tools Extension Operation 调用；不得创建独立 Codec Manager 或复制 Codec 实现。
- Event Plugin 仅允许提取规范化 Event 所需的最小协议 discriminator，不做完整业务解码或 Skill 选择。

## 7. Demo 禁止项

不增加额外 SHA-256 包/事件摘要、包签名、Trust Registry、生产级安全上下文、密钥管理、高可用、灾备、复杂分布式总线、Marketplace、自动下载、文件监视器、通用 Plugin 热更新或生产 SLA。

以下属于功能正确性，不能以 Demo 为由省略：输入/版本/Schema 校验、路径边界、契约不匹配时报错、失败时 fail-closed、UNKNOWN 不得变成 COMMITTED、重复/过期 continuation 不得唤醒错误 Run。

## 8. 文档变更规则

- 架构边界变化：更新唯一架构设计、总目录和收敛计划。
- 机制行为变化：更新对应设计说明书。
- 文件/字段/协议变化：更新 docs/规范/ 对应规范，并检查所有消费者。
- 验收变化：更新 Demo 验收基线和实施路线。
- 外部实现变化：更新参考与审计，记录准确仓库、Commit/PR、测试命令和状态。
- 新增文档必须使用中文文件名并登记到文档总目录。
- 不得把设计目标写成实现 PASS，不得把 Demo PASS 写成 Production Qualification。

## 9. 测试与交付

真实执行测试并记录命令和结果。未执行写 NOT_RUN，环境阻断写 BLOCKED，失败写 FAIL。不要猜测测试状态，不要自动合并 PR 或发布 Release。
