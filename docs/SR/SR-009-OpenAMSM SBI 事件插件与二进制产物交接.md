# SR-009：OpenAMSM SBI 事件插件与二进制产物交接

> 文档类型：软件需求（SR）  
> SR 版本：0.2.2  
> 状态：DRAFT（SR 实施主状态）；**设计待评审 / REVIEW_REQUESTED**，未获得实施 READY，产品验收 NOT_RUN  
> 创建日期：2026-11-25  
> 修订日期：2026-11-26  
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.2 §1～13、16；[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.2.6 §2～5；[插件包与进程通信协议规范](../规范/插件包与进程通信协议规范.md) v0.2.5 §6～8  
> Acceptance：OM-01～OM-03、OM-05～OM-08、OM-14、OM-15（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 0. 本轮设计评审入口（2026-11-26）

**状态边界：**本文已提交中央设计评审，SR 主状态仍为 `DRAFT`；`REVIEW_REQUESTED` 仅代表评审候选，不代表独立 APPROVE、实施 `READY`、已有产品或系统验收 PASS。设计追踪 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12)，统一单版本决策见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) 与 [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**核查 ingress/delivery 插件职责、multipart/Content-ID 字节保真、Host-owned staging/ArtifactStore 与失败重放。
- **已知依赖与未验证项：**Owner/Provider/Go Host 外部证据不等于 Next Python Host/Plugin 实现；正式 1.6.0 Skill 选择留给 Core；系统 OM 未执行。
- **跨模块约束：**凡涉及新 Skill/Assurance/Compiler/Runtime/Studio/Bundle 的输入输出，只支持 **CA-SL 1.6.0**、Skill-facing Capability ID 和唯一公开 Capability↔Callable 绑定；**无** v1alpha5、旧 Build DTO、旧 Artifact/Bundle、别名、Fallback 或迁移兼容。历史文件和冻结版本保留为只读审计材料，不是新实施目标。具体产品契约与机器标识必须待 Owner 发布，不得推测。
- **评审交付：**评审者依据本 SR 已声明范围、非目标、Acceptance/EX/OM、功能设计与最新规范提出逐项结论；P0/P1 指向当前 Demo 承诺的实际矛盾。审查未完成/依赖未发布/产品未运行必须分别保留 `PENDING_REVIEW` / `BLOCKED` / `NOT_RUN`，不能升级为实施资格。

## 1. 目标

实现独立 Go OpenAMSM Event/Delivery Plugin，通过统一 Plugin Package/IPC 接入 SBI JSON 与 multipart 二进制，并由 Host 管理 ArtifactStore。

## 2. 实施范围

- SBI HTTP/2 ingress、JSON/multipart/related 解析和 Content-ID 关联。
- Plugin 仅通过 Host 提供的 inbound/outbound staging directory 写入/读取原始 N1/N2 文件描述符；不拥有 ArtifactStore，不生成 artifactRef。Host 导入/导出由 Next SR-010 承载。
- 将规范化 Event 发布给 Host，并执行 SBI Delivery 编码。
- 对共享 UpdateSMContext 仅提取最小 NAS discriminator，区分 Modify 与 UE-requested Release；Host Resolver 仍负责选择 Skill。
- 保留 externalRequestId、responseObligation、Run/continuation 关联。

## 3. 非目标

- 不在 Plugin 中选择 Skill、执行业务逻辑或调用 Owner。
- 不完整解码 NAS/NGAP，不复制 Codec 实现。
- 不使用 Base64、Plugin 自有 Artifact 数据库或额外摘要机制；不实现 ca-host.artifact-store/v1 channel server，也不接收/生成 Host artifactRef。

## 4. 依赖与分阶段门槛（遵循 SR 管理规范 §6.1）

| 依赖类型 | 权威输入 | 适用门槛 |
|---|---|---|
| 设计 | F03 Plugin/IPC、F05 Artifact、F06 和 SR-017 源候选设计 | Plugin 只做 Event/Delivery/Staging；Skill 选择归 Core |
| 实施 | Plugin Package/IPC v1alpha1 已冻结规范、Plugin 自身独立 Go 进程 | 可用测试 Host 单独实施/验收 Plugin，无需 Next Skill/Owner |
| 模块验收 | SBI 原始 Create/Update/multipart/NAS 字节样本与测试 Host | 不依赖真实 Owner；固定 0xC9 Modify / 0xD1 Release discriminator |
| 系统 OM | OM-01～03/05～08/14/15 与完整 Next Host + Mock AMF | 只能在组合环境验收；不代替 Plugin 单模块 AC |

**设计评审与实施 READY 独立判定**：本 SR 的功能职责、已知目标契约、失败路径和下面每项模块 AC 足够完整即可请求设计评审；不得要求“全部前置 SR VERIFIED”作为统一前置。实际实施按本次 Scope 逐阶段检查所消费的已发布能力；缺失时仅相应 AC 标记 BLOCKED/NOT_RUN，系统 EX/OM 不倒灌模块门禁。Owner/Provider/Compiler 的未知机器标识、Schema 和 API 只能由对应 Owner 正式发布，Harness 不得推测。新 Skill/Artifact/Runtime 接口只接受 CA-SL 1.6.0 / Capability-first，不提供旧版兼容。

## 5. 独立模块验收条件（正例、反例与证据）

| 模块 AC | 固定输入/操作 | 预期、诊断与隔离 |
|---|---|---|
| AC-009-01 | Plugin 启动，经 stdin/stdout IPC 版本握手与 capabilities discovery | Plugin Package/IPC v1alpha1 协议通过；非法版本与超帧明确拒绝 |
| AC-009-02 | Create/Update JSON 与 multipart/related Content-ID、原始 N1/N2 bytes | 归一化 Event 包含正确 correlation/slot/mediaType/byteLength，原字节逐位相同 |
| AC-009-03 | Staging 仅可提交相对路径、声明 slot；绝对路径、路径穿越、artifactRef 反例 | 非法描述拒绝；Plugin 不直接创建 Host artifactRef/ArtifactStore |
| AC-009-04 | 合法 0xC9 Modify、0xD1 UE Release、截断或未知 NAS discriminator | 各合法类型准确分类，非法/歧义 fail-closed；不在插件内调用业务 Owner |
| AC-009-05 | responseObligation 对应可用 Delivery 与错 externalRequestId、过期/越权输出 | 仅本次授权 response 交付；串单/过期拒绝，不发出错误 2xx |
| AC-009-06 | 重复请求与多并发回放，不同 correlation 的 raw fixtures | 原始 bytes/correlation 不混淆；本模块只证明 Plugin ingress/delivery，不宣称 Next 去重/Run 或 OM E2E |

### 5.1 实现落点、运行和取证

- 目标实现：`cmd/openamsm-plugin（ca-openamsm-plugin）`；测试入口：`go test ./... -count=1 && go build ./cmd/openamsm-plugin`。若实现前目标仓文件/命令尚未存在，由具体实施 PR 在模块范围内创建并登记，**不得以不存在的脚本退出 0 或 0 discovered tests 作为 PASS**。
- 使用本 SR 明示的最小正负例与计数型测试 Provider/Mock；真实 Publisher、新 Compiler、Owner 收据、隔离环境等数据只从固定 SHA 的正式发布物读取。模拟输入能验证本地行为，但**不能替代**要求正式外部源的 AC。
- 每项 AC 单独记录受测代码 SHA、设计 Head、外部 Package/Schema/API 版本、命令、环境、测试数量、预期/实测、失败诊断与证据路径。未执行始终 NOT_RUN；输入缺失标记 BLOCKED；系统 EX/OM 必须用独立组合证据交付。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-openamsm-plugin |
| GitHub Issue | 未创建 |
| 实施 PR | 未创建 |
| Commit | 无 |
| 实施状态 | NOT_STARTED |
| 验收证据 | NOT_RUN |

ca-agent-next PR #1 是设计基线 PR，不是本 SR 的实现 PR，不得在此标记实施完成。

## 7. 变更与替代关系

- supersedes：无
- superseded by：无
- 影响分析：初始分解；等待设计基线评审。
- 本 SR 的范围和验收条件在进入 READY 后冻结。后续发生语义变化时创建新的 SR 并引用本 SR，不覆盖历史要求。

### EC04 源仓验收入口

以 [F06 两端实施矩阵](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md#ec04-两端实现与逐例复核) 的 operationId、固定 OpenAPI、peer 输入与 MAS 作者契约制作 fixtures。先在 ca-openamsm-plugin 以独立测试 Host 核对双向 IPC、HTTP 与 staging，再在 ca-agent-next 接真实子进程。分别记录外部仓和中央仓的 SHA、命令、测试数、输入投影及结果。授权跨仓后按上述归属修改，不能只改 Host 使 fixture 通过。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 未记录（历史资料未提供） | 历史记录未细分 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-009 |
| 2026-11-25 | 0.1.1 | 未记录（历史资料未提供） | 历史记录未细分 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-009 |
| 2026-11-25 | 0.1.2 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-009 |
| 2026-11-25 | 0.1.3 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05/F06/Plugin IPC 设计版本，并将 Go Event/Delivery Plugin 的实施目标仓更正为 ca-openamsm-plugin | 设计仓与实际代码仓分离；防止将插件实现错误归入 Next Host | Issue #12 |
| 2026-11-25 | 0.1.4 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05 至 v0.4.0，并将 Event/Delivery Plugin 的 staging 职责与 Next Host ArtifactStore / Tool Channel 明确分离 | 防止把 Host 实现责任错误计入 ca-openamsm-plugin；Host 侧由 SR-010 追踪 | Issue #12；SR-009、SR-010 |
| 2026-11-25 | 0.1.5 | 未记录（历史资料未提供） | 历史记录未细分 | 更新 F05/F06/Plugin IPC 设计依据至当前版本；同步冻结的 Host Artifact Store v1 与 Codec Consumer 分层状态 | 避免 SR-009 继续指向过期设计版本，确保 Plugin staging 和 Host→Tool Channel 的实施边界一致 | Issue #12；F05 v0.4.1；F06 v0.2.2；Plugin IPC v0.2.2 |
| 2026-11-25 | 0.1.6 | Codex / GPT-6 | §4～5 | Codex / GPT-6 · §4～5 清除自依赖，区分协议组件和组合验收 | 对齐当前架构与实施门禁 | Issue #12 SR-009 |
| 2026-11-26 | 0.1.7 | 未记录（历史资料未提供） | 历史记录未细分 | 补齐外部实现输入及两端验收 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.8 | 未记录（历史资料未提供） | 历史记录未细分 | 同步设计依据到本次复审的修订版本 | 对齐跨仓实现与独立复验 | Issue #12 |
| 2026-11-26 | 0.1.9 | Codex / GPT-6 | §4～5 | Codex / GPT-6，§4～5。分别登记设计输入、实施接入和验收依赖。 | 使 Harness 能按当前阶段判定启动与验收条件 | Issue #12、#21 |
| 2026-11-26 | 0.2.0 | GPT-6.2（ChatGPT） | 文档头部 | 将 Plugin IPC 设计依据更新至 v0.2.4 | 与当前 12 帧协议和 SR-003 使用同一冻结规范版本 | Issue #26 |
| 2026-11-26 | 0.2.1 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记独立设计待评审批次、专项审查重点与缺失输入，保留 SR DRAFT/产品 NOT_RUN | 按 1.6.0-only / Capability-first 设计集中审查；避免提前授予实施门禁 | Issue #12；SR-029；PR #45 |
| 2026-11-26 | 0.2.2 | GPT-6（ChatGPT） | §4～§5 | 按治理 §6.1 拆分设计/实施/模块/系统依赖；补齐 AC-009-xx 正反验收 | 解除全局 VERIFIED 门槛与缺模块 AC 问题，避免 Harness 猜测/EX 倒灌 | Issue #12/#40；PR #46；SR 管理规范 §6.1 |
