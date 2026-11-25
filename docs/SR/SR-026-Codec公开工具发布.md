# SR-026：Codec公开工具发布

> 文档类型：软件需求（SR）  
> SR 版本：0.1.1  
> 状态：DRAFT  
> 创建日期：2026-11-26  
> 上游需求：IR-006  
> 设计依据：F03.05 v0.3.7 §8.2、§11 与 EC03 外部生产端复验。  
> 关联 Issue：ca-agent-next#12（设计）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §4；本批仅验收指定 NAS Decode。

## 1. 目标与前置

目标仓 ca-client-tools，功能 F03.05 / EC03，消费方 ca-agent-next SR-010。中央依据为 F03.05 §8.2、§11 及 [Tool Interface 与 Provider 集成设计](../设计说明书/F03-Plugin平台/Tool%20Interface%20与%20Provider%20集成设计说明书.md#ec03-外部生产端与复验)。现状为 Provider v1.2.0 有 11 个 READ，Codec 候选 PR #39 有本地库和 Worker。先固定可复验的 Phase B revision，仅选已通过正反向 fixture 的一类 NAS Decode 做第一批。现有 11 个公开导出和 Owner 契约不包含此操作。

## 2. 在源仓交付

1. 以 `protocol/codec/nas.go` 的 DecodeNAS 与同目录测试为输入，固定一个已支持的消息类型、原始输入和预期 JSON。声明新的公开 Callable ID、Capability membership、READ、精确输入输出 Schema、输入 artifact slot 和媒体类型。READY 前由 Provider 所有者在本节登记精确 ID、Schema、handler 与版本，不由消费端命名。
2. 在 `internal/provider/` 接入进程内本地 handler，通过 Host artifact channel 取原字节；结果不经过远端 SBI，拒绝错误 slot、非法消息与超限。以现有 v2 schema 实测能否合法表示本地结果；若必须改变冻结 envelope，先给出版本化契约、Driver 选择和兼容测试，再启动该部分。
3. 同步 Provider 发布包生成器、公开 Interface、bindings 和私有 backend catalog；真实进程只在声明的 ID 上响应。将构建所得包交给 Next，禁止直接从分支代码导入 Go 库作为 Tool。包的新增版本使用纯数字 SemVer。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-026-01 | 在选定候选根运行 `go test ./protocol/codec/...`，记录受测 SHA、支持子集、具体 fixture 和测试数；截断/不支持的消息失败 |
| AC-026-02 | 在生产端运行 `go test ./internal/provider ./internal/runtimebindings ./internal/interfacepkg`，再用发行包的 `provider serve` 完成 initialize/catalog/invoke；断言精确投影、零远端 SBI 请求、原字节不变，缺通道时该绑定 unavailable |
| AC-026-03 | 用同一发行包和同一 fixture 执行 SR-010。先无 decode 声明验证零调用，再在有授权的 Skill 上验证一次调用；越权在派发前拒绝 |

## 4. 状态与非目标

源仓实施 Issue、PR、commit、正式包未登记，测试 NOT_RUN。前述公开 ID/Schema、版本与本地结果 profile 未冻结，维持 DRAFT。第一批不含 Encode、全量 NGAP、ext=1 或其他未经资格化消息。SR-015 的设计移交和 SR-010 已发布 Provider 部分可单独验收。无替代 SR。

### 首批 NAS 向量

固定 PR #39 `protocol/codec/codec_test.go::TestDecodeNASOpenAMSMVectors` 中的 `release-request`，原始四个 octet 为 `2e 05 01 d1`，Decoder 的消息类型应为 `PDUSessRelReq`，PSI=5、PTI=1。加入截断到三个 octet、同头但最后 octet 为 0xd4 的反例，后者是有效 Release Complete、超出首批指定的消息类型。以 `go test ./protocol/codec -run TestDecodeNASOpenAMSMVectors -count=1 -v` 单独核对原始库向量，再由公开 Provider 调用重跑。本节只定义第一批公开子集。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 内容 | 关联 |
|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | Codex / GPT-6 | 见本行变更 | 首次登记两端交付、独立复验与就绪条件 | Issue #12 |
| 2026-11-26 | 0.1.1 | Codex / GPT-6 | 见本行变更 | 固定实际 Codec 向量及验收结果；补齐正式文档的评审范围与非目标；绑定中央设计章节；列明依赖设计版本 | Issue #12 |
