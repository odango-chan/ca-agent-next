# SR-027：技能Bundle构建与发布

> 文档类型：软件需求（SR）  
> SR 版本：0.1.1  
> 状态：DRAFT  
> 创建日期：2026-11-26  
> 上游需求：IR-006  
> 设计依据：F08 v0.3.7 §4、§6。  
> 关联 Issue：ca-agent-next#12（设计）  
> 全局评审范围：继承根目录 Agent.md 的 review_scope
> 本文局部非目标：见 §4；本批限外部构建与发布。

## 1. 目标与前置

目标仓 ca-skills，功能 F08 / EC01，中央依据为 [F08 发布设计 §4](../设计说明书/F08-技能编译与发布/技能编译与发布设计说明书.md#4-ca-skills-ci-编译与-bundle-组装)。基线 `780497a2918ad3e7bdff554ab64b0ba627e867e0`。SR-023 交付作者规范，SR-013 交付需要 checked when 的 Compiler Release，SR-004 与 SR-008 消费发布物。固定作者 SHA、Compiler 发布 tag 与可执行文件、适用的 Runtime Artifact API。某一 Skill 需要下一版 Artifact 时单列等待。

## 2. 在源仓交付

以 `scripts/compile_mas_v1alpha5.py`、`tests/test_compile_mas_v1alpha5.py`、`.github/workflows/source-hygiene.yml` 为起点。现有 MAS 脚本面向 v2.0.2，源文件卫生检查不能证明已发布 Bundle。为本批指定的 Echo 作者源、MAS 作者源分别建立构建输入清单。Echo 在该基线缺失，准备 SR-008 所用的指导包和带 Assurance 的 Echo，登记路径、Capability、请求/响应样例及预期。MAS 输入选 `examples/skills/{establish,modify,release}-pdu-session-mas`，逐个给出依赖和 Verify 日志。

CI 对同一批次一次解析并固定 Compiler 发行版，逐包构建与验证成功后组装发布目录。指导包只含作者入口及声明的资源；确定性包随附已验证的 Runtime Artifact。输出记录作者 revision、Compiler 实际版本、API、资产路径、各包结果。发布前在临时目录验证，失败不上传部分批次；由授权的发布步骤消费同一份候选。

## 3. 验收与退出条件

| ID | 入口与判据 |
|---|---|
| AC-027-01 | ca-skills 根运行 `python -m unittest discover -s tests -p test_compile_mas_v1alpha5.py -v` 和 `python scripts/verify_docs.py`；为 Bundle 正例和 Verify 失败新增可独立运行的测试并登记命令、发现数与日志 |
| AC-027-02 | CI 在干净 checkout 生成候选。逐项查 SKILL.md、所声明的资源及可选 Assurance 对应产物；损坏 Artifact 使当批发布数为零。Development Artifact 不进入 Runtime Bundle |
| AC-027-03 | 使用同一候选在 Next 执行 SR-004 导入与 SR-008 Echo；原始作者 checkout 和 Compiler 从 Host 运行环境移除后依然可运行。分别记录构建、发布及消费状态 |

## 4. 状态与非目标

中央设计 Issue #12；ca-skills 实施 Issue、实施 PR、构建证据和正式发行资产尚未登记。READY 前固定首批作者源、Bundle 的具体文件清单、可用 Compiler 版本与匹配 Verify 命令；候选构建和正式发布分别登记。状态 DRAFT，测试 NOT_RUN。Next 不编译，Compiler 不负责组装 Bundle。无替代 SR。

## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 内容 | 关联 |
|---|---|---|---|---|---|
| 2026-11-26 | 0.1.0 | Codex / GPT-6 | 见本行变更 | 首次登记两端交付、独立复验与就绪条件 | Issue #12 |
| 2026-11-26 | 0.1.1 | Codex / GPT-6 | 见本行变更 | 补齐正式文档的评审范围与非目标；列明依赖设计版本；同步设计依据到本次复审的修订版本 | Issue #12 |
