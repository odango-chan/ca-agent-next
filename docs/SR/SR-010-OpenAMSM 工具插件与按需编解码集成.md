# SR-010：OpenAMSM 工具插件与按需编解码集成

> 文档类型：软件需求（SR）  
> SR 版本：0.1.7  
> 状态：DRAFT；设计基线待评审，不允许实施  
> 创建日期：2026-11-25  
> 所属阶段：Phase G  
> 上游需求：[IR-005](../IR/IR%20总登记册.md#ir-005)  
> 设计依据：[Plugin平台设计说明书](../设计说明书/F03-Plugin平台/Plugin平台设计说明书.md) v0.3.2 §8；[Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md) v0.3.6 全文；[Context与Artifact管理设计说明书](../设计说明书/F05-Context与Artifact管理/Context与Artifact管理设计说明书.md) v0.4.1 §5～10；[公共契约与所有权规范](../规范/公共契约与所有权规范.md) v0.2.4 §2、5、6、8  
> Acceptance：OM-04、OM-10、OM-13（见[演示验收基线](../验收与实施/演示验收基线.md)）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：见第 3 节

## 1. 目标

通过唯一 Plugin Manager 接入 ca-client-tools，并在 Next Python Host 实现 Host-owned ArtifactStore 与冻结的 ca-host.artifact-store/v1 channel，使 Skill 能通过普通 Tool Action 按需调用 Provider/Codec Operation。

## 2. 实施范围

- 将 ca-client-tools provider/v2 适配在统一 Plugin Manager 的 tools Extension 内，不增加第二个 Provider Manager。
- 在 Next Host 实现 Host-owned ArtifactStore 和 `ca-host.artifact-store/v1` loopback HTTP/1.1 channel；Host 在 Provider `initialize` 中传入闭合 `artifactChannel`，由 Provider 使用 GET 输入 / POST 输出交接原始 bytes。
- Artifact reference 使用 Host 生成的随机 opaque token，并绑定 invocation、direction、slot；不包含路径、URL、mediaType、size 或 digest。
- Provider `artifactSlots` 必须来自可信 Backend Catalog；原始 bytes 不进入 NDJSON、不使用 Base64、不暴露任意本地路径。
- 按 v1 contract 完成逐 Artifact SHA-256 传输校验、大小/数量配额、超时/取消、过期清理和输出原子发布；该摘要不是引用身份、内容寻址或去重。
- 缺少 `artifactChannel` 时 artifact-bearing binding 必须 `NOT_CONFIGURED`，并在远端 SBI I/O 前拒绝。
- Codec Decode/Encode/最小分类操作必须先发布在权威 Tool Interface Package；Skill 需要结构化协议字段时才调用 Codec Tool。
- Codec 输出 JSON 投影或新 Artifact Reference；原始 Artifact 不被替换。

## 3. 非目标

- 不把当前纯 Go codec library 误报为已发布 Agent-callable Tool。
- 不创建独立 Codec Plugin/Manager，不在 Host/Event Plugin 复制编解码实现。
- 不宣称未验收的全量 NGAP 支持。
- 不实现新的 content-addressed artifact identity、去重、额外 package hash、签名或 Trust Registry；仅实现 v1 channel 已规定的逐 Artifact 传输校验。
- 不允许 Provider 自行选择文件路径、远端 URL 或凭据。

## 4. 依赖与前置条件

SR-003、SR-007、SR-009；外部依赖为 ca-client-tools Provider v1.2.0 / Codec API、冻结的 ca-host.artifact-store/v1 契约与共享 conformance fixtures。ca-agent Go Host P1 仅作为外部参考证据，不计入 Next 验收。

进入 READY 前必须确认所有前置 SR 已 VERIFIED，或在 SR 中明确记录并批准并行实施理由；外部依赖必须有可核对的版本、接口和可用证据。

## 5. 验收条件

1. ca-client-tools Provider v2 经同一 Plugin Manager 的 tools Extension 调用；不存在第二 Provider Manager。
2. Next Host ArtifactStore 生成 v1 合规随机 opaque `artifactRef`，并将引用绑定到当前 Invocation、direction 和 slot；拒绝跨 Invocation、跨方向、跨 slot 或未声明位置的引用。
3. Host 在 `initialize` 中提供 v1 闭合 `artifactChannel`，只监听 `127.0.0.1` ephemeral port；省略通道时 initialize 可成功，artifact-bearing binding 报 `NOT_CONFIGURED`；显式非法配置时 initialize 返回 `PROVIDER_CONFIGURATION_INVALID`，无后续 catalog/invoke。两类路径均不产生远端 I/O。
4. Provider 可按 v1 contract GET 输入 Artifact、POST 输出 Artifact；Host 校验媒体类型、Content-Length、SHA-256、配额和 invocation/slot 绑定，输出仅在整个结果校验通过后原子发布。
5. 取消、超时、Provider 退出、无效结果和部分上传均清理 staged outputs；过期引用不可读取。
6. Next Host 通过 ca-host.artifact-store/v1 共享 conformance fixtures，覆盖 reference、bootstrap、GET/POST、slot、quota、expiry、partial-write、atomic publication 和 error mapping；使用确定性本地 upstream，不声称真实 NF multipart 已验收。
7. Interface Package 明确声明 Codec Callable ID、输入输出 Schema 和 Artifact 语义；Codec 操作只在正式发布后可调用。
8. no-decode Skill 不调用 Codec；decode-required Skill 经 Runtime Action Boundary 调用 Codec；Decode 不修改原始字节，不支持消息明确失败。
9. 仅使用实际发布并验收的 NAS/N2 消息子集。

验收时必须引用演示验收基线中的对应 Acceptance ID，并记录真实执行命令、测试结果、Example 和覆盖范围。未执行项保持 NOT_RUN。

### 实施位置与复验入口

以下路径为本 SR 的目标交付物。在 ca-agent-next 仓根运行，测试通过公开入口调用受测组件。目标位置为 `src/ca_agent_next/plugins/` 与 Host ArtifactStore 实现。按 ca-client-tools v1.2.0 的 `contracts/host-artifact-store/v1/` fixtures 启动独立 Provider。缺通道、跨 slot、过期和截断输出均有输入，记录真实 GET/POST、发布/清理结果与 upstream 调用次数。配置缺失时上游调用为零；无已发布 Codec Callable 时将 decode-required 记为 BLOCKED，生产端由 SR-026 跟踪，可独立验收现有 Provider v2 路径。

验收命令为 `python -m unittest discover -s tests -p test_artifact_channel.py -v`。必须发现并执行本节正反例；发现 0 个测试或跳过必需用例时，退出码 0 也不能计入 PASS。逐个 Acceptance ID 回填受测 SHA、命令、预期与实测值及日志位置。

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
| 2026-11-25 | 0.1.4 | 将 ca-host.artifact-store/v1 Host 端实现、Provider artifactChannel bootstrap/GET/POST、原子输出发布和共享 fixtures 纳入 Next 工具集成验收；同步 F03.05/F05/公共契约版本 | 当前 Provider v1.2.0 已有 channel consumer 与冻结契约，Next Host 仍需实现并独立验收；不能把 ca-agent Go Host PASS 计入 Next | Issue #12；SR-010、SR-015 |
| 2026-11-25 | 0.1.5 | 更新 F05 设计依据至 v0.4.1；明确 Mock AMF Codec C1 PR #86 不构成 Agent Tool/Provider Consumer，也不解除 Next Host Channel 的 NOT_IMPLEMENTED 门槛 | 对齐 Host ArtifactStore 与 Codec 的最新跨仓状态，避免把测试对端迁移误判为 Next 实施 | Issue #12；F05 v0.4.1；F06 v0.2.2 |
| 2026-11-25 | 0.1.6 | Codex / GPT-6 · §5 固定目标代码位置、复验入口及可观察断言；同步所引权威设计版本 | 对齐当前架构与实施门禁 | Issue #12 SR-010 |
| 2026-11-26 | 0.1.7 | §5 对齐真实 Provider v2，分别验收消费与外部发布 | 对齐跨仓实现与独立复验 | Issue #12 |
