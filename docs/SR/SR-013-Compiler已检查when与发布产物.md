# SR-013 Compiler 已检查 when 与发布产物

> 文档版本：0.1.1  
> 状态：DRAFT  
> 创建日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：Next 消费端实施、生产准入、Owner Trust 治理及自动发布。

上游 [IR-003](../IR/IR%20总登记册.md#ir-003)。设计依据：[EC02 Compiler 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.1.4 §1–7 和 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) §1–5。SR-012 负责归档。

目标仓：`odango-chan/ca-skill-compiler`。范围覆盖 Go/Python 互操作 PoC、Compiler Contract AST 与语义检查、新版 Artifact Schema、Build/Verify、fixture、Golden 和产品门禁。保持单一 Go Core、语言 v1alpha5、冻结发布 Artifact v1alpha5 及 Development v1alpha1；Development 继续 `NOT_ADMITTED`。Next SR-004/005 消费实际发布 Bundle，运行时无 Compiler 或 Skill Admission。

启动条件：本 SR 经评审达到 READY，ca-skills #88 的 M.4 与 SA 导入职责已与 Next 对齐、正式发布且固定规范 SHA，具备目标仓写入授权和可运行 Go/Python 环境。PoC 为本 SR 的第一段验收；通过后再要求 Compiler Owner 确认新版 Artifact API 版本和布局。合并或发布另行授权。

| 验收 ID | 通过条件 | 当前证据 |
|---|---|---|
| AC-013-01 | Go 生成的 CheckedExpr Any 与 FileDescriptorSet 被固定版本 Python 直接加载；G.4 跨语言 fixture 对 true/false/error、缺失/null 与数值边界一致 | NOT_RUN |
| AC-013-02 | #61 的静态正负例、诊断位置和多 Skill 共享 Lock 时的类型隔离全部符合预期 | NOT_RUN |
| AC-013-03 | 新版 Build/Verify 确定、损坏时 fail-closed；冻结机器契约及两条冻结产物路径对基准的 Golden 字节一致 | NOT_RUN |
| AC-013-04 | #61 指定的 Go 测试、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 与 diff check 全部通过 | NOT_RUN |
| AC-013-05 | 经授权发布后，记录可下载的实际 Bundle、Release SHA、资产、契约版本与验证日志，供 SR-004/005 使用 | BLOCKED：依赖 AC-013-01～04 与发布授权 |

Issue：[Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。规范依赖：[ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88)。设计 PR：[Next #3](https://github.com/odango-chan/ca-agent-next/pull/3)。实施 PR、Commit、实际命令、环境、受测 SHA 和证据待回填。替代关系：无。

## 修订记录

| 日期 | 版本 | 修订内容 | 原因 | 影响 SR |
|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex 登记 Compiler 实施及验收范围 | 建立 #61 的 Next 实施与交接入口 | SR-013、SR-004/005 |
| 2026-11-25 | 0.1.1 | 登记 M.4 / SA 的规范一致性门槛 | 防止消费端被要求调用 Compiler 或做 Admission | SR-013 |
