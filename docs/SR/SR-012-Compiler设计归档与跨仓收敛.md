# SR-012 Compiler 设计归档与跨仓收敛

> 文档版本：0.1.3  
> 状态：DRAFT（SR 实施主状态）；**设计待评审 / REVIEW_REQUESTED**；实施/产品验收未升级  
> 上游 IR：IR-006  
> 创建日期：2026-11-25  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、5GC/MAS 认证及发布。

## 0. 本轮设计评审入口（2026-11-26）

本 SR 纳入 [Issue #12](https://github.com/odango-chan/ca-agent-next/issues/12) 的中央设计评审批次。**SR 实施主状态依旧为 `DRAFT`；设计 `REVIEW_REQUESTED` 不等于独立 APPROVED、实施 READY 或产品 PASS。** 单版本决定见 [SR-029](SR-029-Capability-first-Skill作者接口与Callable一对一绑定.md) / [PR #45](https://github.com/odango-chan/ca-agent-next/pull/45)。

- **本轮评审重点：**Compiler 活动设计与中央 EC02 文档的权威映射、历史冻结发布只读归档、源仓重复正文迁移后的路径。
- **阻塞/未验证：**Compiler #61 的 1.6.0 Artifact/API 与 Next main 尚未就绪；不能先替换源仓权威文档链接。
- **通用架构约束：**新 CA-SL 作者源、Compiler API/Build DTO、Runtime Artifact、Bundle、Studio 与 Agent Importer/Runtime **只支持 1.6.0**；Skill 只选择 Capability ID，公开 Capability↔Callable 双向一对一。历史版本材料只读留档；不做别名、兼容、双轨、迁移或 fallback。机器字段/ID 必须等待发布者冻结，不猜测。
- **评审输出：**逐项核对范围、非目标、外部 Owner、错误/状态语义、Acceptance 与证据路径。设计无独立结论写 `PENDING_REVIEW`；未发布依赖写 `BLOCKED`；未运行测试写 `NOT_RUN`。当前不得派发 DeepSeek Harness 实施任务。

目标是让 Next EC02 成为现行 Compiler 机制设计入口。设计依据为 [EC02 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.2.9 §1–4。

本 SR 的唯一实施仓为 `odango-chan/ca-skill-compiler`。Next 上的 EC02、IR/SR 和审计属于中央设计输入与结果回填。以 Compiler `255ab85fa5abb4b0bf36656bf64250cafebf45cb` 的 README.md、README.zh-CN.md 为导航入口，对 `git ls-tree -r --name-only HEAD docs` 中的活动设计逐项比对 EC02。仅在可定位到已评审的中央章节时将重复正文改为链接；无法对应的条目列为差异并保留原文。用 `git diff --name-status` 检查变更仅落在已登记的文档，逐个验证新增的中央链接在 Next 默认分支可达。保留机器契约、实现、测试、示例、运行说明和发布证据。其他协作仓仅在发现重复 EC02 设计后，通过覆盖目标仓的 SR 处理。语言规范仍由 ca-skills 管理。Compiler #61 的实现及版本发布单独追踪。

依赖：本设计完成评审并进入 Next main，中央链接可达，本 SR 达到 READY。跨仓实施按 Agent.md 执行。

| 验收 ID | 验收内容 | 证据状态 |
|---|---|---|
| AC-012-01 | EC02 设计、IR/SR、源 SHA、Issue、范围和修订可双向导航 | DESIGN |
| AC-012-02 | Compiler 默认分支的设计入口指向 Next；清理重复活动设计且保留冻结历史及机器契约，文档门禁通过 | NOT_RUN |
| AC-012-03 | 审查每项冻结决策及候选 when 的状态，提供可复核的 Harness 门槛和证据路径 | DESIGN |

Issue [Next #2](https://github.com/odango-chan/ca-agent-next/issues/2)；依赖工作 [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。实施 PR、Commit、受测 SHA 与测试证据待回填。替代关系：无。

## 修订记录

| 日期 | 版本 | 修订者 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 设计基线 | 集中维护及验证交接 | IR-006、SR-012、#2 |
| 2026-11-25 | 0.1.1 | Codex / GPT-6 | 正文 | 明确唯一实施仓与文档移交流程 | 消除执行歧义并同步中央设计 | Issue #12 SR-012 |
| 2026-11-25 | 0.1.2 | Codex / GPT-6 | 正文 | 同步所引权威设计版本 | 消除执行歧义并同步中央设计 | Issue #12 SR-012 |
| 2026-11-26 | 0.1.3 | GPT-6（ChatGPT） | 文档头、§0、设计依据 | 登记统一 1.6.0 专项设计评审、阻塞与证据边界；不改变产品实施主状态 | 设计集中评审、避免历史来源冒充新发布 | Issue #12；SR-029；PR #45 |
