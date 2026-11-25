# CA-SL Compiler 设计说明书

> 文档版本：0.1.0  
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

## 5. DeepSeek Harness 提示词

~~~text
在 odango-chan/ca-agent-next 从 Agent.md、功能树 EC02/F02、SR-012、SR-004/005 与《跨仓互操作实施任务说明》开始。记录 Next、Compiler 和 ca-skills 的目标 ref 与 HEAD SHA，核对工作区、Issue 与 PR 状态。继承 Agent.md 的 review_scope。只处理目标范围及直接依赖。

先做只读预检。核对 Compiler v2.1.0、冻结 Build/Verify Artifact v1alpha5、Development v1alpha1 NOT_ADMITTED，以及 ca-skills #88 和 Compiler #61。任何目标 SR 未 READY、规范未发布、固定输入缺失或未经授权写目标仓时，输出 BLOCKED 和解除条件。可以继续查阅证据，不修改实现。

满足门槛后，从已发布 ca-skills 规范固定 SHA。先执行 Go cel-go → CheckedExpr Any + FileDescriptorSet → 固定版本 cel-expr-python 的最小 PoC。使用实际 Compiler 产物，验证 true/false/error、未知字段、optional/nullable 缺失与 null、int64/finite binary64、不同 Skill 的 Schema 隔离及共享 Lock。任一语义不一致则停止并附最小复现。通过后按 #61 实现新版发布 Artifact，保持冻结格式和 Development 字节不变。Next 只导入外部发布 Bundle，校验引用与作用域并加载已检查程序。不要调用 Compiler、引入 Skill Admission、扩大 G.4 或增加 Trust Registry。

Compiler 门禁在产品仓按 #61 运行 Go test、vet、Native/WASM 构建、CLI E2E、真实 Chromium Worker parity 和 git diff --check。Next 执行各 READY SR 指定的 Acceptance。每条结果记录需求、命令、环境与版本、实际退出码、受测 SHA 和证据链接。区分 PASS、FAIL、NOT_RUN 和 BLOCKED。逐条列出 BLOCKER、NON_BLOCKING、UNVERIFIED 及影响。保持 PR 未合并，不发布版本。
~~~

## 修订记录

| 日期 | 版本 | 修订者 | 章节 | 修改内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | Codex | 全文 | 建立 EC02 设计基线 | 集中维护及验证交接 | IR-006、SR-012、#2 |
