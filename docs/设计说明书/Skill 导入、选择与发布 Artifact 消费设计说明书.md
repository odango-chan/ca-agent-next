# Skill 导入、选择与发布 Artifact 消费设计说明书

> 文档类型：机制设计说明书  
> 状态：目标机制设计；Artifact 互操作部分依赖外部 Compiler 发布  
> 修订日期：2026-11-25  
> 适用范围：Skill 包导入、SkillCatalog、Resolver、已发布 CA-SL Runtime Artifact 与 Python CEL Runtime

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
~~~

发布包的精确 Artifact 文件清单、Manifest 和类型数据以 Compiler 发布契约为准。Agent 不推断或重新构建 Artifact 内部语义，不把作者源中的 assurance/ 文件当作可直接执行的运行时 Artifact。

## 3. 三种导入形态

| 输入 | Agent 处理 | Compiler 调用 |
|---|---|---|
| 只有 SKILL.md 的 Skill 包 | 读取指导和候选元数据，加入 Catalog；仅 LLM-guided | 不调用 |
| SKILL.md + 已发布 Assurance Artifact | 基本结构/必需文件/格式/类型数据检查，解析 Tool/Capability 依赖，加入 Catalog | 不调用 |
| 无效或不完整的发布包 | 显式导入失败，不得降级为 SKILL.md-only | 不调用 |

Agent 不接收尚未发布的 Assurance 作者源作为可执行 Skill。LLM 创建或修改 Assurance 源码后，必须经外部发布流程编译并发布新的运行包，才能进入 Agent Catalog。LLM 创建或修改 SKILL.md-only 包则可按普通 Skill 导入流程更新。

## 4. 发布 Artifact 消费边界

Agent 只执行以下消费端检查：

- SKILL.md 存在且可读取。
- Artifact 的格式标识受当前 Agent 支持。
- 必需 Artifact 文件存在且路径位于包根目录内。
- Manifest 引用的文件、Schema/type data 和本地依赖可解析。
- Tool/Capability 依赖能够解析到当前部署已安装的 Interface Package。
- when 的 CheckedExpr 和类型描述数据可被指定 Python CEL Runtime 反序列化。
- Artifact 文件、路径或依赖不满足要求时给出明确错误并拒绝导入。

Agent 不执行 Compiler 的 Inspect/Verify 命令，不重复做 CA-SL 静态类型检查、链接、Procedure Graph 校验或 Artifact 自校验，不建立 Skill Admission、Owner Trust 或生产授权阶段。Compiler 的构建与发布流程必须保证发布物符合其自身契约。

## 5. SkillCatalog 生命周期

SkillCatalog 属于 Python Agent Core / Host，不属于 Plugin Manager。它是进程内不可变快照，包含：

- Skill ID、包引用和发布 Artifact 引用；
- 完整 SKILL.md 文本及由其生成的轻量候选元数据；
- 是否存在有效发布 Assurance Artifact；
- 已反序列化的 when 程序、CEL Profile 和类型环境；
- 发布 Artifact 声明的 Callable/Capability 依赖引用。

初始化、显式导入或更新时读取包内容并构造候选 Catalog generation。基本检查和依赖解析全部成功后原子激活；任何失败保留旧 generation。每个 Invocation 固定其选择时的 generation。references/ 和大型知识材料按需加载，不在每次 Event 选择时扫描目录或读取文件。

Agent 不实现文件监视器、自动下载、分布式缓存或通用 Plugin 热更新。支持的更新入口是显式 Skill import/update。

## 6. Skill 选择语义

1. 校验并去重 Event。
2. 精确 continuation 优先，恢复原 Run，不重新选择 Skill。
3. 对新 Event 固定当前 Catalog generation。
4. 对声明 when 的已发布 Assurance Skill，使用 Artifact 中已检查的 CEL 程序求值。
5. when=true 形成显式候选；when=false 排除；运行期求值错误 fail-closed 并排除该 Skill。
6. 一个显式候选直接选择；多个显式候选只允许在精确候选集合内由 LLM 消歧，并校验返回的 Skill ID。
7. 没有显式候选时，只对没有声明 when 的 Skill 进行 SKILL.md 语义选择。
8. when=false 或求值错误的 Skill 不得重新进入无条件语义候选集合。
9. 无候选时澄清或拒绝；不得无 Skill 绑定地回退到 Generic Agent。
10. 精确绑定 Skill 后，才选择 Deterministic 或 LLM-guided 模式。

when 只能读取规范化 Event 的 event.type 和 Contract.requestSchema 声明的 input 字段，不得访问 Tool、Observation、Runtime Context、时钟或可变 Host 状态。读取 input 成员必须由作者源 Contract 声明 requestSchema，并由外部 Compiler 在发布前静态检查。

## 7. CEL CheckedExpr 与类型环境

Compiler Issue #61 跟踪 Development Artifact v1alpha2 对已检查 CEL 程序的发布格式。目标互操作格式是标准 google.api.expr.CheckedExpr（由 google.protobuf.Any 包装）及对应 FileDescriptorSet；由 cel-go 生成、cel-expr-python 消费。CA-SL 语言标识保持 connectionagent.io/v1alpha5，不增加 v1alpha6。

Agent 侧只做：

1. 在导入时加载发布 Artifact 中的 CheckedExpr Any 和 DescriptorSet。
2. 使用指定版本的 cel-expr-python 反序列化一次，建立可重复执行的 Program/类型环境。
3. 将 Program、DescriptorPool 和 Skill 的类型绑定保留在 Catalog generation 中。
4. 每个新 Event 使用当前 event.type/input 构造 activation 并独立求值。
5. 不缓存跨 Event 的 true/false/error 结果；相同程序可以因输入不同得到不同结果。
6. 不在 Event 热路径解析 CEL 源字符串、静态类型检查或启动 Compiler 进程。

字段缺失与 null 的差异、G.4 optional/nullable 守卫、int64/binary64 规则必须由外部 Compiler 的发布程序和 Python CEL Runtime 互操作测试证明。若发布 Artifact 无法反序列化或类型数据不完整，导入失败，不得用 DynType 或自制解释器绕过。

## 8. 执行模式派生

| Skill 状态 | 可用模式 |
|---|---|
| 无 Assurance Artifact | LLM-guided only |
| 有效发布 Assurance Artifact | Deterministic 或 LLM-guided |
| Artifact 缺失、格式错误或依赖不完整 | 导入失败 |

不增加 supportedModes 字段。执行模式从发布包是否含有效 Assurance Artifact 派生。SKILL.md-only Skill 不得启动确定性 Procedure。

## 9. 外部依赖与状态边界

- ca-skills PR #88：同标识 CA-SL v1alpha5 的 optional Assurance/when 刷新；实施前重新确认合并与正式规范状态。
- ca-skill-compiler Issue #61：Development Artifact v1alpha2 与 CheckedExpr/DescriptorSet 发布格式；Compiler 负责源码静态检查和发布。
- ca-agent-next：只负责已发布包的消费、Catalog、选择和 Runtime，不调用 Compiler。
- cel-expr-python：作为 Python Runtime 的 CEL 反序列化/求值依赖，版本固定并以跨语言 fixtures 验收。

注意：ca-skill-compiler Issue #61 早期说明中如仍要求 Next 调用 Inspect/Verify 或做 Skill Admission，应按本设计的最新消费边界重新对齐；本仓不实现这两项。

## 10. 验收要求

- SKILL.md-only 包不调用 Compiler，进入 Catalog 后仅 LLM-guided。
- 已发布 Assurance Artifact 包不调用任何 Compiler 命令。
- 缺失文件、未知 Artifact 格式、无效 CEL/type data、路径越界和未解析依赖均导入失败，不降级。
- when 在发布前静态检查；Agent 导入时反序列化一次；每个新 Event 独立求值。
- when=false / error 的 Skill 不进入语义候选；多 true 只在精确集合内消歧。
- Catalog 更新原子激活；失败保留旧代际；Invocation 固定 generation。
- Event 热路径无 Skill 文件读取、Artifact 文件读取、目录扫描和 Compiler 调用。
- Continuation 恢复原 Run，不重新选择 Skill。
- SKILL.md 全文来自内存；references/ 按需加载。
- Go CheckedExpr → Any → Python cel-expr-python 的实际互操作 fixture 与 CA-SL G.4 语义一致。

以上是设计验收要求，不代表 Compiler 发布、Python Runtime 实现或 Next E2E 已经通过。
