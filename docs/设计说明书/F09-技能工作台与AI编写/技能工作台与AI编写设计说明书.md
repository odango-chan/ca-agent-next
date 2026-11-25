# 技能工作台与AI编写设计说明书

> 文档类型：设计说明书  
> 文档版本：0.1.0  
> 状态：待评审  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产级准入、签名、完整性体系和 Trust Registry  

关联 IR-006、SR-016。基线为 [docs/architecture/studio-boundaries.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/architecture/studio-boundaries.md)、[docs/design/ai-procedure-authoring.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/design/ai-procedure-authoring.md)。

## 1. 编辑与语言服务

Theia 的 Package Explorer 以作者源码为工作区入口。可视化视图、导航与诊断来自同一源码和语言核心，未保存缓冲区及包代际变化要驱动刷新；Browser Worker 失效后要给出可见状态。编辑器维护诊断、语义 token、补全和导航，规范锁固定到已发布版本。Package View 的 Dependencies 与 Build Artifacts 使用各自数据源，源码修改保留文本与未改动区域。

## 2. AI 编写

上下文与变更集由编辑宿主管理。模型和独立 Gateway 返回候选提案；宿主校验语义操作，将其转换为可预览的源码补丁。应用前对同一候选执行 Compiler gate，用户保存后才持久化。编辑器及 Gateway 不负责 Skill 选择、Runtime 执行或 Tool 调用。

## 3. when 编写与验收

正式语言刷新后，Contract 字段提示与诊断对齐中央规范。支持可选顶层 when、Schema 类型与错误定位；原有无 when 包保行为。文本与 AI 编辑均保持可预览，不能把选择条件写入 Predicate。覆盖 Browser Worker、源码往返、已有包、有效与无效表达式、Compiler gate 与应用后再打开。

## 4. 历史决策

保留 [docs/decisions/0001-source-first-visual.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0001-source-first-visual.md) 与 [docs/decisions/0002-ide-host-spike.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0002-ide-host-spike.md)；Classic 为历史迁移证据。Package-first 见 [docs/decisions/0004-package-first-workspace.md](https://github.com/odango-chan/ca-skill-studio-demo/blob/5b666c0ef754ed32fa37c97ce2429f328c70477f/docs/decisions/0004-package-first-workspace.md)。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修改内容及原因 | 关联 |
|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex / GPT-6 | 全文 | 整合已核对的跨仓基线和候选变更，建立分仓验收入口。 | F09 · IR-006 · SR-016 |
