# CA-SL Compiler 设计说明书

> 文档版本：0.1.1  
> 状态：待评审；IR-006 / SR-012 / #2  
> 修订日期：2026-11-25  
> 全局评审范围：继承根目录 Agent.md 的 review_scope  
> 本文局部非目标：生产准入、Owner 信任运营、5GC/MAS 认证及发布。

关联 [IR-006](../../IR/IR%20总登记册.md#ir-006)、[SR-012](../../SR/SR-012-Compiler设计归档与跨仓收敛.md) 和 [Next #2](https://github.com/odango-chan/ca-agent-next/issues/2)。

## 1. 权威与版本

CA-SL v1alpha5 语言和 IngressCatalog 由 ca-skills 发布；已发布 JSON Schema、fixture 和 golden 由 ca-skill-compiler 维护。EC02 维护机制设计，F02 维护 Next 消费行为。Compiler 产品为 v2.1.0，语言目标仅 `connectionagent.io/v1alpha5`。冻结 Build/Verify v1alpha5 Artifact 保留 `generator.version=v2.0.2`、布局、字节和复验语义。Development v1alpha1 独立版本化，始终 `NOT_ADMITTED`。参见[冻结 API](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/contracts/v1alpha5/README.md)和 [Development API](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/contracts/development/v1alpha1/README.md)。

## 2. 单一 Core 与入口

Native CLI 与 Go/WASM Worker 调用同一个 Go Core。Check 返回诊断，InspectDependencies 解释依赖和链接，Build 通过静态校验后组装确定性产物，冻结 VerifyBuildResult 校验成功结果及产物树自洽；Development Verify 使用原请求重建并比较。失败不返回部分产物。Transport 解码、版本、路径、限制、可信上下文先于 YAML 解析；统一 AST 管线依序完成 Contract/Predicate/Script、标识和依赖绑定、Owner/Tool/Capability/Evidence 链接、Schema 闭包与赋值/CEL 检查、Procedure 图与 Wait/Mutation/Evidence 语义检查。Compiler 不执行 Tool、Python、网络过程或 Runtime。参见[源码入口](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/api.go)、[冻结 Artifact 布局](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-artifact-v1alpha5.md)、[核心 API 源设计](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-core-v1alpha5.md)。

冻结 Build 成功返回 `connectionagent.io/compiler-build-result/v1alpha5`、排序的 OutputFiles 和 DependencyClosure。失败返回空 OutputFiles 和空 DependencyClosure。输出为 RFC 8785 JCS：顶层 `manifest.json`、每 Skill 的 `compiled/procedure.json` 与 `compiled/ingress-links.json`。源码只记录路径与域分离摘要。Manifest 记录静态验证范围、生成器、依赖闭包、Skill 源与编译文件、Wait 的 ingress/response 绑定，以及除 Manifest 自身外的文件 SHA-256。序列化、排序与摘要不依赖时间、环境或输入文件顺序。Verify 拒绝路径重复、非规范 JSON、错误版本、未知或缺失文件、摘要不符、重复归属、Wait/Ingress/response 元数据不一致及结果闭包与 Manifest 不一致。CLI 验证通过后才写入新建或空输出目录。

## 3. 机制与职责

- [工具链机制设计](工具链设计.md)定义编译、Interface Link 和发布边界，以及外部 Host/Owner 责任。
- [Development Build 设计](Development%20Build设计.md)定义精确身份、快照和 Lock 闭包、Schema 作用域、多 Skill 每 Skill Root 及共同闭包、Capability requirement 与复验。
- [Evidence 与 Owner Trust 职责设计](Evidence职责设计.md)定义静态 Evidence 链接、精确 Owner 来源与外部待决 Requirement。Compiler 校验声明与引用，不授予权限、确认 Owner 信任或判定实际 mutation COMMITTED。Capability Requirement 不是 Capability Grant。
- F02 仅导入外部已发布 Bundle。Development 产物及其 Host Admission Requirements 不能作为 Next 导入契约。Next 运行时不调用 Compiler。

## 4. 一致性审查与交接

| 分类 | 证据与结论 |
|---|---|
| BLOCKER | [ca-skills #88](https://github.com/odango-chan/ca-skills/pull/88) 尚开放。when 正式规范和固定 SHA 是 Compiler #61 的 P0 门槛。 |
| BLOCKER | [Compiler #61](https://github.com/odango-chan/ca-skill-compiler/issues/61) 尚开放。当前 `ContractAST` 无 when；既有 Predicate CEL 路径的 DynType 不能满足 typed input。必须先证明 CheckedExpr Any 与 DescriptorSet 的 Go/Python 互操作及 optional/null 语义，再定新版发布 Artifact。 |
| BLOCKER | Next SR-004/005 的正式发布 Artifact、互操作证据与 READY 门槛尚未满足。严禁用 Development v1alpha2 名义交付运行包。 |
| NON_BLOCKING | 既有核心说明中出现旧产品版本；版本以 v2.1.0 发布记录为准。源实现报告的旧版本号和 PASS 属历史执行。 |
| NON_BLOCKING | 冻结 API 与 Development 两套入口是不同输出契约，复用同一 Core。真实 MAS 离线输入及产品资格是独立验收，见 Compiler #53。 |
| UNVERIFIED | 本轮仅核对冻结契约、源码文件和历史报告，Compiler 回归、Go/Python PoC 与 Next 导入测试均 NOT_RUN。 |

复核入口：[Development 实现与验收报告](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/docs/design/compiler-development-build-implementation-report.zh-CN.md)、[Schema Registry](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/schema_registry.go)、[Development Link](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_link.go)、[多 Skill Lock 测试](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_multi_skill_test.go)、[Evidence Owner 测试](https://github.com/odango-chan/ca-skill-compiler/blob/255ab85fa5abb4b0bf36656bf64250cafebf45cb/internal/compiler/development_evidence_owner_test.go)。历史版本设计见[冻结归档](https://github.com/odango-chan/ca-skill-compiler/tree/72b41548a9c4d29c6c49abed117a04a963454f22/docs/design)。

## 5. DeepSeek Harness Goal 提示词

将以下任务粘贴到 Goal 模式。若界面已启用 Goal 模式，去掉首行的 `/goal` 命令前缀。

~~~text
/goal 推进 CA-SL v1alpha5 已检查 when 的 Compiler → Python Runtime 交付，直至目标 SR 的必需验收全部有可复核证据，或已完成所有可独立推进的工作且具体外部门槛仍阻塞。保持冻结 v1alpha5 Build/Verify 与 Development v1alpha1 的契约、字节和行为。未经用户授权不得合并 PR 或发布版本。

入口：odango-chan/ca-agent-next PR #3 的 EC02 Compiler 设计说明书、Agent.md 的 review_scope、功能树 EC02/F02、SR-012、SR-004/005 和《跨仓互操作实施任务说明》。上游追踪 odango-chan/ca-skills PR #88、odango-chan/ca-skill-compiler Issue #61。执行前逐仓记录目标 ref、HEAD SHA、工作区状态、目标 SR 和 Acceptance ID。

1. 先做只读预检。复核语言规范是否已合入并发布、#61 的范围与依赖、目标 SR 是否 READY、目标仓写入授权、可运行环境与固定输入。逐项记录阻塞、解除条件、权威链接和可独立推进的工作。无写入权限或目标 SR 未 READY 时保留源码与治理状态，继续只读核对。不得把上游 PR 打开、历史 PASS 或设计文档当作当前验收。
2. 已获授权且门槛满足后，固定正式语言规范 SHA 及 Go/Python/CEL/protobuf 版本。先执行 Go cel-go → CheckedExpr Any + FileDescriptorSet → cel-expr-python 的最小 PoC。用实际输出验证 true/false/error、未知字段、缺失与 null、数值边界以及共享 Lock 下的多 Skill 类型隔离。发现语义差异，保存最小复现与证据并暂停依赖该 PoC 的阶段。
3. PoC 通过后，按 #61 实施版本化发布 Artifact。复用同一 Compiler Core，冻结产物保留原字节，Development 继续 NOT_ADMITTED。发布产物和 SR-004/005 门槛满足后，Next 仅消费外部发布 Bundle，执行结构、引用和 callable scope 检查并加载已检查程序。Agent 不调用 Compiler，不引入 Skill Admission、Owner Trust Registry 或第二套 CEL 实现。
4. 在 Compiler 仓执行 #61 的 Go test、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 和 git diff --check。对 Next 执行目标 READY SR 指定的 Acceptance。每项记录需求 ID、执行命令、环境与版本、受测 SHA、退出码和证据链接。需要合并或发布才能解除门槛时报告待授权事项。
5. 每轮保留可恢复交接：最后完成阶段、仓库与 SHA、变更或 PR、验收结果、阻塞及第一个可执行的恢复步骤。恢复后先重新核对 ref 与门槛，再从第一个未验收阶段继续。只有全部必需验收 PASS 才报告目标完成。外部阻塞时以 BLOCKED 收尾，附已做的预检与解除条件；不得把阻塞交接写成完成。
~~~

## 修订记录

| 日期 | 版本 | 修订者 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 设计基线 | 集中维护及验证交接 | IR-006、SR-012、#2 |
| 2026-11-25 | 0.1.1 | Codex | §5 | 加入 Goal 的实施门槛、恢复点和完成判据 | 支持分阶段执行及阻塞后恢复 | IR-006、SR-012、#2、PR #3 |
