# SR-010：OpenAMSM 工具插件与按需编解码集成

> 文档类型：软件需求（SR）  
> SR 版本：0.1.3  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Plugin平台设计说明书](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md) v0.3.1 §8；[Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) v0.2.0 全文；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.3.0 §5～10；[公共契约与所有权规范](../规范/公共契约与所有权规范.md) v0.2.1 §2、5、6、8  
> Acceptance：OM-04、OM-10、OM-13（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

通过唯一 Plugin Manager 接入 ca-client-tools，并让 Skill 通过普通 Tool Action 按需调用已发布的 Codec Operation。

## 2. 实施范围

- 将 ca-client-tools provider/v2 适配在统一 Plugin Manager 的 tools Extension 内。
- Codec Decode/Encode/最小分类操作必须先发布在权威 Tool Interface Package。
- Skill 需要结构化协议字段时调用 Codec Tool；不需要时直接传原始 artifactRef。
- Codec 输出 JSON 投影或新 Artifact Reference；原始 Artifact 不被替换。

## 3. 非目标

- 不把当前纯 Go codec library 误报为已发布 Agent-callable Tool。
- 不创建独立 Codec Plugin/Manager，不在 Host/Event Plugin 复制编解码实现。
- 不宣称未验收的全量 NGAP 支持。

## 4. 依赖与前置条件

SR-003、SR-007、SR-009；外部依赖为 ca-client-tools Codec API 发布与准确消息子集资格。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. ca-client-tools 经同一 Plugin Manager tools Extension 调用。
2. Interface Package 明确声明 Codec Callable ID、输入输出 Schema 和 Artifact 语义。
3. no-decode Skill 不调用 Codec；decode-required Skill 经 Runtime Action Boundary 调用 Codec。
4. Decode 不修改原始字节；不支持消息明确失败。
5. 仅使用实际发布并验收的 NAS/N2 消息子集。

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
| 2026-11-25 | 0.1.0 | 建立初始需求草案 | 从当前架构、设计说明书和 Acceptance 分解 | SR-010 |
| 2026-11-25 | 0.1.1 | 中文化 SR 标题和文件名；需求范围及验收条件未变 | 落实中文文档命名规范 | SR-010 |
| 2026-11-25 | 0.1.2 | 补齐 IR、设计章节与验收追踪 | 对齐最新分支与 IR/SR 基线 | SR-010 |
| 2026-11-25 | 0.1.3 | 补齐 F03.05 Provider v2 消费设计，并更新 F05 / 公共契约引用 | Tool Interface / Owner Contract / Provider Runtime Bindings 已有独立中央设计 | Issue #12 |
