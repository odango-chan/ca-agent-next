# SR-012 Compiler 设计归档与跨仓收敛

> 文档版本：0.1.0  
> 状态：DRAFT  
> 上游 IR：IR-006  
> 创建日期：2026-11-25  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、5GC/MAS 认证及发布。

目标是让 Next EC02 成为现行 Compiler 机制设计入口。设计依据为 [EC02 设计说明书](../设计说明书/EC02-Compiler/Compiler设计说明书.md) v0.1.0 §1–4。

范围为 ca-agent-next 的归档与跟踪，以及 ca-skill-compiler 的设计入口、重复设计正文和受影响的文档链接或清单。保留机器契约、实现、测试、示例、运行说明和发布证据。其他协作仓仅在发现重复 EC02 设计后，通过覆盖目标仓的 SR 处理。语言规范仍由 ca-skills 管理。Compiler #61 的实现及版本发布单独追踪。

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
