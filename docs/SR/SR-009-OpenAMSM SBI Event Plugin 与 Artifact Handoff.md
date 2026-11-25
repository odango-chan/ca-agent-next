# SR-009：OpenAMSM SBI Event Plugin 与 Artifact Handoff

> 文档类型：软件需求（SR）  
> SR 版本：0.1.0  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase G  
> 设计依据：事件接入与二进制产物交接设计说明书 §1～§6、§8～§10；插件包与进程通信协议规范  
> Acceptance：OM-01～OM-03、OM-05～OM-08、OM-14、OM-15  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

实现独立 Go OpenAMSM Event/Delivery Plugin，通过统一 Plugin Package/IPC 接入 SBI JSON 与 multipart 二进制，并由 Host 管理 ArtifactStore。

## 2. 实施范围

- SBI HTTP/2 ingress、JSON/multipart/related 解析和 Content-ID 关联。
- 原始 N1/N2 字节通过 Host staging 与 ArtifactStore 导入/导出。
- 将规范化 Event 发布给 Host，并执行 SBI Delivery 编码。
- 对共享 UpdateSMContext 仅提取最小 NAS discriminator，区分 Modify 与 UE-requested Release；Host Resolver 仍负责选择 Skill。
- 保留 externalRequestId、responseObligation、Run/continuation 关联。

## 3. 非目标

- 不在 Plugin 中选择 Skill、执行业务逻辑或调用 Owner。
- 不完整解码 NAS/NGAP，不复制 Codec 实现。
- 不使用 Base64、Plugin 自有 Artifact 数据库或额外摘要机制。

## 4. 依赖与前置条件

SR-008、SR-003；外部依赖为 ca-openamsm-plugin 设计/实现契约。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. 严格使用 Plugin Package/IPC v1alpha1。
2. JSON 与 multipart/Content-ID 映射正确，原始二进制字节保持不变。
3. Host 正确导入 ArtifactStore 并关联 Event/Run。
4. UpdateSMContext 对 0xC9 与 0xD1 分类正确；畸形/未知/不支持类型 fail-closed。
5. Delivery 只访问本次 responseObligation 授权的输出。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

## 6. 实施关联

| 项目 | 当前值 |
|---|---|
| 实施仓库 | ca-agent-next |
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

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-009 |
