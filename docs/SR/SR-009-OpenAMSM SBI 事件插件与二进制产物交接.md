# SR-009：OpenAMSM SBI 事件插件与二进制产物交接

> 文档类型：软件需求（SR）  
> SR 版本：0.2.0  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.2 §1～13、16；[业务接入与OpenAMSM集成设计说明书](../设计说明书/F06-业务接入与集成/业务接入与OpenAMSM集成设计说明书.md) v0.2.4 §2～5；[插件包与进程通信协议规范](../规范/插件包与进程通信协议规范.md) v0.2.4 §6～8  
> Acceptance：OM-01～OM-03、OM-05～OM-08、OM-14、OM-15（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

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

## 4. 依赖与前置条件

SR-008、SR-003；输入是 SR-017 固定的候选设计及 F03/F05 正式接口，按阶段确认批准的设计 SHA。该仓现有实现不作为开发自身的前置。

设计使用 SR-017 登记的 EC04 候选 SHA 和 F03/F05 契约。独立 Plugin 用测试 Host 验收 ingress、staging 与 delivery。接入实际 Next Host 时消费 SR-003，第二业务系统集成使用 SR-008 Echo 证据。候选协议变化须重新评审受影响的字段。 设计可按 SR 管理规范 §6.1 单独评审。

## 5. 验收条件

1. 严格使用 Plugin Package/IPC v1alpha1。
2. JSON 与 multipart/Content-ID 映射正确，原始二进制字节保持不变。
3. Plugin 只发布符合 Plugin IPC v1alpha1 的相对 stagingPath、slot、mediaType 和 byteLength 描述符；不得发布绝对路径或 artifactRef。Host 导入 ArtifactStore 的验收属于 SR-010，不计入本 Plugin 仓单独验收。
4. UpdateSMContext 对 0xC9 与 0xD1 分类正确；畸形/未知/不支持类型 fail-closed。
5. Delivery 只访问本次 responseObligation 授权的输出。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

### Plugin 独立验收与组合证据

建议实现位置为 `cmd/openamsm-plugin`，从插件仓根执行 `go test ./... -count=1` 和 `go build ./cmd/openamsm-plugin`。用测试 Host 经 stdin/stdout 握手驱动进程，回放 Create、0xC9、0xD1、截断与歧义 discriminator 的 SBI 样本，记录归一化 Event、slot、相对路径、字节比对及 delivery correlation。对重复请求使用同一协议身份。OM-02/05～08 中涉及选技、ArtifactStore、精确 Run 与去重的断言须另附 Next 组合证据；模拟 Host 的通过只覆盖 Plugin 一侧。

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
