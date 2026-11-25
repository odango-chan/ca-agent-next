# DeepSeek Harness 实施提示词：CEL when Artifact 与 SkillCatalog

**用途：** 将当前架构设计推进到可运行的 Compiler / Python Agent 实现。  
**任务入口：** [ca-skill-compiler Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)  
**Next 架构入口：** [ca-agent-next PR #1](https://github.com/odango-chan/ca-agent-next/pull/1)  
**语言规范依赖：** [ca-skills PR #88](https://github.com/odango-chan/ca-skills/pull/88)

## 可直接交给 Harness 的任务

你负责完成 CA-SL v1alpha5 的 \`contract.when\` Compiler 支持，以及 ca-agent-next 的 Core-owned SkillCatalog / Python Runtime 集成。必须先核对仓库当前状态、分支和提交，不得把本文中的状态快照当成永远有效的事实。

### 一、仓库与基线

按顺序检查：

1. \`odango-chan/ca-skills\`
   - PR #88，分支 \`refresh-ca-sl-v1alpha5-skill-selection-when\`。
   - 这是同一语言标识 \`connectionagent.io/v1alpha5\` 的刷新提案，不是 v1alpha6。
   - 核对 PR 是否已合并、正式规范发布记录是否已更新、最终规范 SHA 是什么。
   - 如果仍 OPEN：可以基于其候选分支做 PoC 和隔离实现，但不得宣称正式规范发布或最终产品符合性；不得自行修改/合并该 PR。

2. \`odango-chan/ca-skill-compiler\`
   - v2.1.0 发布源码基线：\`b67fbb56c34d15b8d5a0903c8a7ca93d608f8f65\`。
   - 当前实现任务：[Issue #61](https://github.com/odango-chan/ca-skill-compiler/issues/61)。
   - 从最新 \`main\` 创建独立实现分支，不直接提交 main，不合并 PR。

3. \`odango-chan/ca-agent-next\`
   - 在现有 PR #1 分支 \`docs/architecture-baseline-20261125\` 的最新 HEAD 上继续；先 fetch 最新提交，不能假设本提示词里的旧 SHA 仍是 HEAD。
   - PR #1 是架构/设计基线。运行时代码在独立实施分支开发，不要把实现代码直接塞进文档 PR，除非仓库当前分支策略明确要求如此。
   - 读取 \`Agent.md\`、\`docs/architecture.md\`、\`docs/acceptance.md\`、\`docs/implementation/deepseek-harness-plan.md\` 和中文设计文档 \`docs/集成设计/技能目录与编译器运行时接口设计说明书.md\`。

### 二、不可改变的架构决策

1. CA-SL 语言标识保持 \`connectionagent.io/v1alpha5\`，不增加 v1alpha6，不做旧版本兼容。
2. 冻结 v1alpha5 Build/Verify API 与 Artifact 字节完全不变。
3. Development Build v1alpha1 的五份冻结机器契约不原地修改。
4. 推荐只新增 Development Artifact Manifest \`connectionagent.io/compiler-development-artifact/v1alpha2\`；BuildRequest / BuildResult / Interface Package / Dependency Lock 仍使用现有 v1alpha1。若发现 BuildResult DTO 确实必须变化，先提供证据和版本化方案，暂停等待审查。
5. SkillCatalog 属于 Python Agent Core / Host，不属于 Plugin Manager。
6. SKILL.md-only Skill 由 Next Importer 直接导入，不调用 Compiler。
7. 存在 Assurance 时必须有完整 \`contract.yaml\`、\`procedure.yaml\`、\`predicates.yaml\`；无效 Assurance 是导入失败，不得降级。
8. \`when\` 只在 \`assurance/contract.yaml\`，是 Skill 选择期纯 CEL；\`predicates.yaml\` 仍是执行期业务判断。
9. 不新增 \`activation.yaml\`、\`constraint.yaml\`、第二份 Skill descriptor、Domain Contract Package、Event→Skill 表。
10. 不新增额外 SHA-256、签名、Trust Registry、分布式缓存、文件监听、自动下载或通用 Plugin 热更新。Compiler 既有 Artifact 文件清单/摘要按原契约复用，不扩张为新信任体系。
11. 不复制 Go Compiler，不在 Python 自己实现 CEL Parser、Type Checker 或 CEL Interpreter。
12. 所有新增/修改文档内容使用中文，新增文档文件名使用中文。代码符号、API 标识和规范原文按需要保留英文。

### 三、Phase 0：Compiler / Python CEL 互操作 PoC（先做，未通过不得进入 Artifact 定稿）

实际审计以下源码和契约：

- \`internal/compiler/cel_check.go\`
- \`internal/compiler/ast.go\`
- \`internal/compiler/inherited_semantics.go\`
- \`internal/compiler/schema_registry.go\`
- \`internal/compiler/schema_g4.go\`
- \`internal/compiler/development_api.go\`
- \`internal/compiler/development_build.go\`
- \`internal/compiler/development_artifact.go\`
- \`internal/compiler/development_request.go\`
- \`contracts/development/v1alpha1/\`
- \`go.mod\` 中的 cel-go 版本。

已知现状：\`cel_check.go\` 是 Predicate CEL 检查；其外部 Schema 参数路径会使用 \`cel.DynType\`，不能直接满足 Contract.when 对 Request Schema 的字段级静态检查。现有 Schema Registry 已经能解析 Request Schema 闭包，必须复用。

完成一个真实 PoC：

1. Go \`cel-go\` 在类型环境中编译一个合法表达式，导出标准 \`google.api.expr.CheckedExpr\`。
2. 用标准 \`google.protobuf.Any\` 包装并序列化。
3. Python 使用固定版本的 \`cel-expr-python\`，调用 \`Env.deserialize()\` 加载这份 Go 生成的 Any；不能用 Python 自己重新编译源字符串来冒充互操作。
4. 用相同 DescriptorSet/DescriptorPool 构造 \`event\` 与 \`input\` 的 protobuf activation。
5. 对同一个 Expression 分别输入两个不同 Event，验证 true / false / evaluation error。
6. 验证 G.4 可选字段缺失、nullable/null、int64、double 和短路守卫语义。
7. 记录 Python 版本、操作系统、cel-expr-python、protobuf 版本、Go 版本、命令、原始文件和结果。

重点验证：G.4 的字段缺失和 null 是两种不同状态。若标准 Protobuf Descriptor 表达不能无损保持该语义，立即停止，不得退化成 DynType 或自制解释器；给出可复现反例和替代方案供架构审查。

**Phase 0 通过条件：** Go 生成的 CheckedExpr Any 被 Python CEL Runtime 直接反序列化并重复执行；类型环境一致；G.4 的可选/可空和数值规范 fixture 全部通过。若失败，报告 BLOCKED，不进入最终 Artifact 字段定稿。

### 四、Phase 1：Compiler 增加 Contract.when 静态检查

在 \`ca-skill-compiler\` 实现分支：

1. 在 \`ContractAST\` 中解析顶层可选 \`when\`，保留 YAML source position。
2. 复用单一 CA-SL 解析和语义管线；冻结 v1alpha5 Build 行为必须保持字节级不变。
3. 使用 \`event.type: string\` 与该 Skill 精确 \`requestSchema\` 构建 CEL 静态类型环境。
4. 若表达式读取 input 成员而没有 requestSchema，报 \`CEL_INVALID\`。
5. 严格执行 G.4：闭合字段、静态点访问、bool 返回、可选字段 has 守卫、nullable null 守卫、int64/binary64 及禁止语法。
6. 不允许把 input 设为 DynType 来绕过字段检查。
7. 诊断必须定位到 \`skills/<skill>/assurance/contract.yaml\` 中的 when 表达式，保留 line/column。
8. 不影响 Predicate CEL 的执行期语义，不把 when 混进 predicates.yaml。

新增正反例至少覆盖 CA-SL Appendix M 的 SA-004、SA-005，并覆盖 G.4 可选/可空、未知字段、类型错配、非 bool、数值边界、禁止宏/索引等。

### 五、Phase 2：Development Artifact v1alpha2

只在 Phase 0 互操作通过后定稿并实现：

1. 新增 Artifact Manifest v1alpha2 机器 Schema 和 Go DTO/Assembler/Verifier。
2. 原 Development v1alpha1 的五份契约、Golden 和已发布产物保持不变。
3. 对声明 when 的 Skill 输出：
   - \`skills/<skill>/compiled/when.checked.pb\`：标准 Any，包含已检查 CheckedExpr；
   - \`skills/<skill>/compiled/when.types.pb\`：标准 FileDescriptorSet，覆盖 Event 与 Request Schema 的精确类型闭包。
4. Manifest 为每个 Skill 记录选择程序文件路径、Descriptor 文件路径、Request Schema 精确身份、源码路径和位置。
5. Manifest 继续使用现有 \`files[]\` 文件清单与 Artifact 自校验；不增加独立哈希或签名机制。
6. 无 when 的 Assurance Skill 不生成选择程序文件；SKILL.md-only Skill 不进入 Compiler。
7. \`BuildDevelopment\` / \`VerifyDevelopment\` 对新 Artifact 完整重建、逐文件字节比较；失败不返回部分 Artifact。
8. \`executionStatus\` 仍为 \`NOT_ADMITTED\`。
9. Native、WASM、Chromium Worker 对新 Artifact 文件字节保持一致。

### 六、Phase 3：Compiler 完整验收与发布

按 Compiler 当前正式验收要求实跑，至少包括：

\`\`\`bash
GOWORK=off go test ./... -count=1
GOWORK=off go vet ./...
CGO_ENABLED=0 GOWORK=off go build ./...
CGO_ENABLED=0 GOOS=js GOARCH=wasm GOWORK=off go build -o dist/skillc.wasm ./cmd/skillc-wasm
GOWORK=off go test ./cmd/skillc -count=1 -run TestCLIEndToEnd -v
CHROMIUM_PARITY=1 GOWORK=off go test ./internal/parity -count=1 -run TestChromiumWorkerParity -v
git diff --check
\`\`\`

还需执行 Go → Python CEL 互操作测试。没有真实执行的命令必须写 NOT_RUN；环境阻断写 BLOCKED；不得用源码审查代替测试 PASS。

完成后建立 Compiler PR，报告准确 HEAD SHA、契约路径、测试结果、CI 状态和 Release 阻塞项。不得合并。

### 七、Phase 4：Next SkillCatalog 基础设施

Compiler Artifact 契约有可用的实现分支和明确的文件布局后，在 \`ca-agent-next\` 独立实施分支开发：

1. 实现 Core-owned immutable SkillCatalog / CatalogGeneration。
2. 导入时读取所有 SKILL.md，缓存完整文本和语义候选元数据。
3. SKILL.md-only 直接入 Catalog，不调用 Compiler。
4. Assurance Source 调用 canonical Compiler Check/Build，随后 Inspect/Verify 和 Host Admission。
5. 已编译 Artifact 只 Inspect/Verify，不重新 Build。
6. 读取 Artifact v1alpha2 的 CheckedExpr Any / DescriptorSet；使用 \`cel-expr-python\` 反序列化一次并保留 Expression、DescriptorPool、Schema/type bindings。
7. 对每个 fresh Event 构造当前 activation 并求值；不缓存布尔结果，不读取磁盘，不启动 Compiler。
8. Runtime false/error fail-closed，排除 Skill；多个 true 只在精确集合内消歧。
9. SKILL.md 全文从内存提供；references/ 大型知识资产懒加载。
10. Catalog 更新先构建候选代际，成功后原子切换；失败保留旧代际。
11. 每个 Invocation 固定其 Catalog Generation；Continuation 沿用原 Run Generation。
12. Plugin Manager 不拥有 Catalog，不扫描 Skill，不参与 Skill 选择。

### 八、Phase 5：Next 验收

补齐 EX-21～EX-29：

- EX-21：Catalog 同时登记 SKILL.md-only 和 Assurance Skill。
- EX-22：Event 热路径没有 Skill 文件读取、目录扫描或 Compiler 调用。
- EX-23：when 编译/加载一次，不同 Event 独立求值。
- EX-24：重复 Event 和 continuation 不重复选择。
- EX-25：Catalog 原子更新，失败回滚。
- EX-26：Invocation 代际固定。
- EX-27：语义元数据和完整 SKILL.md 来自内存。
- EX-28：references 按需加载。
- EX-29：Python Runtime 对 Compiler CheckedExpr 的求值与 G.4 规范 fixtures 一致。

同时运行既有 EX-01～EX-20，不得因为新增 Catalog 功能破坏原 Plugin / Echo / OpenAMSM 架构验收。

### 九、停止条件

任一条件出现即停止对应阶段，提交最小复现和证据，不允许自行绕过：

- ca-skills #88 仍 OPEN 且没有可固定的规范候选 SHA；
- cel-expr-python 无法加载 Go 生成的 CheckedExpr Any；
- Request Schema Descriptor 无法无损表达 G.4 optional/null 语义；
- Go / Python 对同一 CheckedExpr 的规范 fixture 结果不一致；
- 需要修改冻结契约才能实现；
- 实现试图引入第二个 CEL Parser/Interpreter、DynType 逃逸、额外完整性/信任机制或 per-Event Compiler 调用；
- 任何测试没有真实执行，却准备标为 PASS。

### 十、交付报告

每个仓库分别报告：

- 仓库、分支、基线 SHA、最新 HEAD SHA；
- PR / Issue 链接和状态；
- 修改文件与契约版本；
- 实际执行的命令、测试数量和结果；
- Go / Python CEL 互操作证据；
- 未运行项和阻塞项；
- 对照架构文档的偏差。

不合并任何 PR，不发布任何 Release，不声称 Owner/Provider/Host/5GC 或 Production Qualification 已通过。
