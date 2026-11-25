# Skill 管理与选择设计说明书

> 文档类型：机制设计说明书  
> 状态：目标机制设计；Artifact 互操作部分依赖外部 Compiler 发布  
> 文档版本：0.2.5  
> 功能归属：F02 — Skill 管理与选择  
> 关联 SR：SR-004、SR-005、SR-006    
> 全局评审范围：继承根目录 Agent.md 的 review_scope    
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  
> 修订日期：2026-11-25  
> 适用范围：Skill 包导入、SkillCatalog、Resolver、已发布 CA-SL Runtime Artifact 与 Python CEL Runtime

关联需求项见 [IR-003](../../IR/IR%20总登记册.md#ir-003)。

## 1. 设计目标

Agent 只消费已发布 Skill 包，不承担 CA-SL 源码编译、Artifact 发布或独立 Skill Admission。SkillImporter 负责读取 SKILL.md、检查发布包基本结构和必需文件、解析本地 Tool/Capability 依赖，并将有效 Skill 加入 Core-owned SkillCatalog。

作者源的 CA-SL 静态检查、Procedure 编译、when 类型检查、Artifact 构建和发布由 ca-skill-compiler 及外部发布流程负责。Agent 不调用 Compiler Check/Build/Inspect/Verify，不重写 Compiler 语义。

## 2. 作者源与运行时发布包

必须区分两个生命周期：

### 2.1 作者源

作者源由 Skill 作者和 ca-skills 维护，形态为：

~~~text
skills/<skill-id>/
├── SKILL.md
└── assurance/                 # 可选
    ├── contract.yaml
    ├── procedure.yaml
    └── predicates.yaml
~~~

SKILL.md 必须存在。assurance/ 可选；存在时由外部 Compiler 按 CA-SL v1alpha5 规则处理。contract.yaml 位于 assurance/ 内，不是每个 Skill 的必需文件。when 是 contract.yaml 的可选字段；predicates.yaml 只承载执行期业务判断。

### 2.2 运行时发布包

Next Agent 消费外部发布的运行包：

~~~text
published-skills/<skill-id>/
├── SKILL.md
└── <Compiler-generated runtime Artifact files>
    ├── normalized Request Schema root + G.4 $ref closure (if declared)
    └── CheckedExpr + DescriptorSet (if when is declared)
~~~

发布包的精确 Artifact 文件清单、Manifest 和类型数据以 Compiler 发布契约为准。声明 requestSchema 的 Skill 必须携带已验证的运行期 Schema 快照及完整闭包；它是输入校验数据，不是可执行 Assurance 源。Agent 不推断或重新构建 Artifact 内部语义，不把作者源中的 assurance/ 文件当作可直接执行的运行时 Artifact。

## 3. 三种导入形态

| 输入 | Agent 处理 | Compiler 调用 |
|---|---|---|
| 只有 SKILL.md 的 Skill 包 | 读取指导和候选元数据，加入 Catalog；仅 LLM-guided | 不调用 |
| SKILL.md + 已发布 Assurance Artifact | 基本结构/必需文件/格式/类型数据检查，加载已发布 Request Schema 快照（若声明）和 when 程序，解析 Tool/Capability 依赖，加入 Catalog | 不调用 |
| 无效或不完整的发布包 | 显式导入失败，不得降级为 SKILL.md-only | 不调用 |

Agent 不接收尚未发布的 Assurance 作者源作为可执行 Skill。LLM 创建或修改 Assurance 源码后，必须经外部发布流程编译并发布新的运行包，才能进入 Agent Catalog。LLM 创建或修改 SKILL.md-only 包则可按普通 Skill 导入流程更新。

## 4. 发布 Artifact 消费边界

Agent 只执行以下消费端检查：

- SKILL.md 存在且可读取。
- Artifact 的格式标识受当前 Agent 支持。
- 必需 Artifact 文件存在且路径位于包根目录内。
- Manifest 引用的文件、已声明 Request Schema 根与完整 G.4 $ref 闭包、CEL type data 和本地依赖可解析；Schema 不依赖远端或作者工作区。
- Tool/Capability 依赖能够解析到当前部署已安装的 Interface Package。
- when 的 CheckedExpr 和类型描述数据可被指定 Python CEL Runtime 反序列化。
- Request Schema 快照用于 Host Event input 校验；DescriptorSet 只用于 CEL 类型，不替代完整 JSON Schema 断言。
- Artifact 文件、路径或依赖不满足要求时给出明确错误并拒绝导入。

Agent 不执行 Compiler 的 Inspect/Verify 命令，不重复做 CA-SL 静态类型检查、链接、Procedure Graph 校验或 Artifact 自校验，不建立 Skill Admission、Owner Trust 或生产授权阶段。Compiler 的构建与发布流程必须保证发布物符合其自身契约。

## 5. SkillCatalog 生命周期

SkillCatalog 属于 Python Agent Core / Host，不属于 Plugin Manager。它是进程内不可变快照，包含：

- Skill ID、包引用和发布 Artifact 引用；
- 完整 SKILL.md 文本及由其生成的轻量候选元数据；
- 是否存在有效发布 Assurance Artifact；
- 已反序列化的 when 程序、CEL Profile 和类型环境；
- 每个已声明 requestSchema 的规范化 G.4 Schema 根、资源闭包和已构造的输入校验器；
- 发布 Artifact 声明的 Callable/Capability 依赖引用。

初始化、显式导入或更新时读取包内容并构造候选 Catalog generation。基本检查和依赖解析全部成功后原子激活；任何失败保留旧 generation。每个 Invocation 固定其选择时的 generation。references/ 和大型知识材料按需加载，不在每次 Event 选择时扫描目录或读取文件。

Agent 不实现文件监视器、自动下载、分布式缓存或通用 Plugin 热更新。支持的更新入口是显式 Skill import/update。

## 6. Skill 选择语义

1. 校验并去重 Event。
2. 精确 continuation 优先，恢复原 Run，不重新选择 Skill。
3. 对新 Event 固定当前 Catalog generation。
4. 对新 Event，按各已发布 Assurance Skill 声明的 `requestSchema` 快照验证同一规范化 payload。Schema 必须来自 Compiler Artifact 中已发布的 G.4 根与完整闭包，不读取作者源，也不依赖 DescriptorSet 推断 enum/const/范围等断言。未声明 requestSchema 时跳过该项校验；校验失败时记录关联 Skill 和原因、排除该 Skill 并跳过 CEL。通过或无需 Schema 校验的 Skill 若声明 `when`，使用 Artifact 中已检查的 CEL 程序求值。
5. when=true 形成显式候选；when=false 排除；运行期求值错误 fail-closed 并排除该 Skill。
6. 一个显式候选直接选择；多个显式候选只允许在精确候选集合内由 LLM 消歧，并校验返回的 Skill ID。
7. 没有显式候选时，只对 SKILL.md-only 和通过前述 Schema 资格检查、未声明 when 的 Assurance Skill 做 SKILL.md 语义选择。
8. when=false 或求值错误的 Skill 不得重新进入无条件语义候选集合。
9. 无候选时澄清或拒绝；不得无 Skill 绑定地回退到 Generic Agent。
10. 精确绑定 Skill 后，才选择 Deterministic 或 LLM-guided 模式。

无规范化 Event 的直接用户任务只走未声明 when 的语义候选路径。上面的 Event 资格规则取自 [CA-SL v1alpha5 候选 M.3／SA-012](../../规范/CA-SL语言基线与版本规范.md#31-候选复核结果)，实施以正式发布版本为准。

when 只能读取规范化 Event 的 event.type 和 Contract.requestSchema 声明的 input 字段，不得访问 Tool、Observation、Runtime Context、时钟或可变 Host 状态。读取 input 成员必须由作者源 Contract 声明 requestSchema，并由外部 Compiler 在发布前静态检查。

## 7. when 程序的发布与运行时接口

作者源中的 when 位于 assurance/contract.yaml，由 ca-skill-compiler 在发布前完成解析、类型检查和 CA-SL G.4 静态校验，并将已检查程序及其类型环境放入发布运行时 Artifact。对任何声明 requestSchema 的 Skill，Compiler 还必须发布规范化的 G.4 Request Schema 根与完整 $ref 闭包，即使该 Skill 没有 when 或 when 只读取 event.type。

Next 在导入阶段加载 Request Schema 快照并构造校验器；when 程序和 DescriptorSet 也在导入阶段反序列化一次，并保存在对应 Catalog generation 中。DescriptorSet 只表达 CEL 类型，不能替代 Request Schema 的 enum/const/范围/长度/数组等完整断言。不解析 CEL 源字符串、不重复静态检查、不调用 Compiler。每个新 Event 使用同一 normalized input 先执行 Request Schema 校验，再按规范求值 when。

CheckedExpr、google.protobuf.Any、FileDescriptorSet、DescriptorPool、字段缺失与 null 语义、G.4 optional/nullable 守卫，以及 Go/Python 互操作的 Compiler 侧设计，统一见 [EC02 Compiler 设计说明书 §3–7](../EC02-Compiler/Compiler设计说明书.md) 和 [SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)。本说明书只定义导入和选择消费端行为，不重复维护 CEL 二进制格式。

## 8. 执行模式派生

| Skill 状态 | 可用模式 |
|---|---|
| 无 Assurance Artifact | LLM-guided only |
| 有效发布 Assurance Artifact | Deterministic 或 LLM-guided |
| Artifact 缺失、格式错误或依赖不完整 | 导入失败 |

不增加 supportedModes 字段。执行模式从发布包是否含有效 Assurance Artifact 派生。SKILL.md-only Skill 不得启动确定性 Procedure。

## 9. 外部依赖与状态边界

- ca-skills PR #88：已合并；正式 CA-SL v1alpha5 来源固定为 18d8184367982ccbc835756136c4a53f9096c3a0，发布记录见 [ca-skills release record](https://github.com/odango-chan/ca-skills/blob/780497a2918ad3e7bdff554ab64b0ba627e867e0/docs/releases/ca-sl-v1alpha5.md)。
- ca-skill-compiler Issue #61：新版发布运行时 Artifact、Request Schema 快照/闭包与 CheckedExpr/DescriptorSet 格式；Compiler 侧详见 [EC02 Compiler 设计说明书 §3–7](../EC02-Compiler/Compiler设计说明书.md) 和 [SR-013](../../SR/SR-013-Compiler已检查when与发布产物.md)。
- ca-agent-next：只负责已发布包的消费、Catalog、选择和 Runtime，不调用 Compiler。
- cel-expr-python：作为 Python Runtime 的 CEL 反序列化/求值依赖，版本固定并以跨语言 fixtures 验收。

Agent 不调用 Compiler Inspect/Verify，也不实现 Skill Admission。Compiler 在发布前完成 Build/Verify；Agent 只做消费端基本结构检查和依赖解析。

## 10. 验收要求

- SKILL.md-only 包不调用 Compiler，进入 Catalog 后仅 LLM-guided。
- 已发布 Assurance Artifact 包不调用任何 Compiler 命令。
- 缺失文件、未知 Artifact 格式、无效 CEL/type data、Request Schema 根/闭包缺失或不一致、路径越界和未解析依赖均导入失败，不降级。
- 声明 requestSchema 的 Skill 在新 Event 选择前使用发布快照校验规范化 input；未声明 requestSchema 的 Skill 不强制 schema 校验。
- when 在发布前静态检查；Agent 导入时反序列化一次；每个新 Event 独立求值。
- when=false / error 的 Skill 不进入语义候选；多 true 只在精确集合内消歧。
- Catalog 更新原子激活；失败保留旧代际；Invocation 固定 generation。
- Event 热路径无 Skill 文件读取、Artifact 文件读取、目录扫描和 Compiler 调用。
- Continuation 恢复原 Run，不重新选择 Skill。
- SKILL.md 全文来自内存；references/ 按需加载。
- Go CheckedExpr → Any → Python cel-expr-python 的实际互操作 fixture 与 CA-SL G.4 语义一致；具体测试由发布产物互操作设计说明书追踪。

以上是设计验收要求，不代表 Compiler 发布、Python Runtime 实现或 Next E2E 已经通过。



## 11. Compiler 发布物与 Python CEL 运行时互操作

本节合并原独立《Skill 管理与选择设计说明书 §11》的 Next 消费端设计。Compiler 内部架构、静态检查、Linking 和发布实现仍由 EC02 ca-skill-compiler 维护；本节不复制 Compiler 内部设计。

### 11.1 发布与运行边界

Skill 发布和 Agent 运行是两个独立阶段：

- 发布阶段：作者源 → CA-SL Compiler Check / Build / Verify → 发布 Runtime Skill Bundle。
- 运行阶段：Agent 导入已发布 Bundle → 基本结构/文件/引用检查 → 本地依赖解析 → Catalog → Runtime。

Agent 不调用 Compiler Check/Build/Inspect/Verify，不导入 Assurance 作者源作为运行时 Artifact，不建立独立 Skill Admission。现有冻结 Artifact 契约与新版本化发布运行时 Artifact 的边界以 Compiler 契约为准；不得在 Next 内扩展冻结格式。

### 11.2 CheckedExpr 与类型环境

Compiler 负责在发布前对 when 进行解析、类型检查和 CheckedExpr 生成。发布 Artifact 必须提供 Python Runtime 可消费的标准 checked program 表示，以及求值所需类型环境（例如 DescriptorSet）。对每个声明 requestSchema 的 Skill，Artifact 还必须提供规范化 G.4 Schema 根和完整资源闭包，供 Host 运行期验证 Event input；它与 when 是否存在无关。

DescriptorSet 只用于 CheckedExpr 的类型解析，不完整承载 JSON Schema enum、const、范围、长度和数组元素约束，因此不能替代 Request Schema 快照。精确 Artifact 版本、Manifest 字段、文件名和 Any 类型 URL 由 [EC02 Compiler 设计说明书 §5–6](../EC02-Compiler/Compiler设计说明书.md) 与 Compiler Owner 批准后的版本化契约定义；Next 不自造文件名或字段。

Next 在 Skill 导入时反序列化已检查程序和类型环境，建立运行时 Program。Event 热路径不解析 CEL 源、不执行类型检查、不编译，也不调用 Compiler。

### 11.3 数据映射与跨语言一致性

- event.type 是规范化 Event 类型；input 的静态类型来源是 Contract.requestSchema。
- Host 的 Request Schema 校验使用同一发布快照和完整 G.4 约束；CEL DescriptorSet 只表达类型与字段，不替代 Schema 验证。
- 类型环境必须表达字段、枚举、嵌套结构和可选/空值语义。
- Go Compiler 与 Python Runtime 使用同一组权威 fixtures，至少覆盖 true、false、缺失字段、null/optional、枚举、嵌套字段和类型错误。
- Python 求值结果必须与 Compiler 的标准 fixtures 一致。
- 不实现第二个 CEL Parser/Type Checker，不把 CEL 源码转成自定义 AST，不以动态类型逃逸静态约束。

如果 ca-skills 规范或 Compiler 发布契约尚未正式可用，相关消费实现标记 BLOCKED / NOT_VERIFIED；不得猜测或临时发明 Artifact 格式。

### 11.4 外部依赖与验收

- EC01 ca-skills：作者格式与 when 语义权威。
- EC02 ca-skill-compiler：CheckedExpr、类型环境和 Runtime Artifact 发布契约权威。
- SR-005：SkillCatalog 驻留和已检查 when 程序消费。
- Acceptance：EX-21～EX-29，尤其 EX-23 和 EX-29。

本节是设计要求，不代表 Go → Python CEL 互操作或 Next Runtime 已通过。

## 12. 中央设计移交与实现证据

按 [CA-SL 发布与候选](../../规范/CA-SL语言基线与版本规范.md) 确认 when 的发布状态。[F08 技能编译与发布设计](../F08-技能编译与发布/技能编译与发布设计说明书.md)负责发布流水线；[EC02 Compiler 设计](../EC02-Compiler/Compiler设计说明书.md)负责 Compiler Artifact；Next 由 SR-004～006 消费与验收；F09 Studio 维护作者编辑。继续使用 §6 的优先次序和原有验收条件。


## 修订记录

| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 历史修订者/模型未记录 | 原第 1～10 章 | 既有 Skill 导入/选择设计基线 | 初始设计登记；逐章历史记录未建立 | SR-004～006 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 第 11 章及全文归属 | 合并 CEL 互操作设计，明确 EC01/EC02 权威和 Next 消费边界 | 避免 Skill 功能拆成多份设计说明书 | F02；SR-004～006；EC01/EC02；PR #1 |
| 2026-11-25 | 0.2.1 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.2 | Codex / GPT-6 | §12 | 记录中央规范与 Compiler/Studio/Next 分工 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.2.3 | Codex / GPT-6 | §6 | 明确 Event Request Schema 资格与诊断次序 | 对齐 CA-SL 候选 M.3／SA-012 | IR-003、SR-006、EX-10 |
| 2026-11-25 | 0.2.4 | GPT-6.2（ChatGPT） | §7、§9、§11 | 固定 CA-SL v1alpha5 正式来源并链接 EC02/SR-013 Compiler 设计 | 消除已合并规范仍标待确认及 Compiler/消费端设计入口不清 | Issue #14、SR-013、Compiler #61 |
| 2026-11-25 | 0.2.5 | GPT-6.2（ChatGPT） | §2–7、§11–12 | 明确 Request Schema 快照是独立运行期数据，DescriptorSet 不替代完整 G.4 Schema 校验；修正 F08 链接目标 | 对齐 CA-SL v1alpha5 M.3，闭合 Event input 校验的数据来源 | Issue #14、SR-013、Compiler #61 |
