# Skill 管理与选择设计说明书

> 文档类型：机制设计说明书  
> 状态：**设计待评审**（唯一新目标 CA-SL 1.6.0；全链路不兼容任何旧作者语法、Build DTO、Artifact、Bundle；1.6.0 产品未发布）
> 文档版本：0.3.6
> 功能归属：F02 — Skill 管理与选择  
> 关联 SR：SR-004、SR-005、SR-006、SR-032    
> 全局评审范围：继承根目录 Agent.md 的 review_scope    
> 本文局部非目标：以本文范围与非目标章节为准；无额外扩展  
> 修订日期：2026-11-27\
> 适用范围：Skill 包导入、SkillCatalog、Resolver、已发布 CA-SL Runtime Artifact 与 Python CEL Runtime

关联需求项见 [IR-003](../../IR/IR%20总登记册.md#ir-003)、[IR-008](../../IR/IR%20总登记册.md#ir-008)。共享资源与 Host Script Execution 的设计增量由 Issue #49 / SR-032 追踪。

## 1. 设计目标

Agent 只消费已发布 Skill 包，不承担 CA-SL 源码编译、Artifact 发布或独立 Skill Admission。SkillImporter 负责读取 SKILL.md、检查发布包基本结构和必需文件、解析本地依赖，并返回已验证的 import candidate。SkillCatalog 由 Core/Host 拥有；候选的 generation 构建、原子激活、旧代际保留和 Invocation pinning 由 SR-005 负责，Importer 不直接修改活动 Catalog。

作者源的 CA-SL 静态检查、Procedure 编译、when 类型检查、Artifact 构建和发布由 ca-skill-compiler 及外部发布流程负责。Agent 不调用 Compiler Check/Build/Inspect/Verify，不重写 Compiler 语义。

## 2. 作者源与运行时发布包

必须区分两个生命周期：

### 2.1 作者源

作者源由 Skill 作者和 ca-skills 维护，形态为：

~~~text
skills/<skill-id>/
├── SKILL.md
├── schemas/                    # 可选，共享 YAML Schema 资源
├── scripts/                    # 可选，共享 Script 源码
│   ├── manifest.yaml           # 存在可执行 Script 时必需
│   └── *.py
├── references/                 # 可选
├── assets/                     # 可选
└── assurance/                  # 可选
    ├── contract.yaml
    ├── procedure.yaml
    └── predicates.yaml
~~~

SKILL.md 必须存在，其 YAML Front Matter 按 [Agent Skills Specification](https://agentskills.io/specification) 处理，不属于 CA-SL v1alpha5 语法。必需字段为 `name` / `description`；`name` 1～64 字符、匹配包根目录名、只允许小写字母/数字/连字符且不得有首尾/连续连字符；`description` 1～1024 字符且非空。可选字段为 `license`、`compatibility`（1～500 字符）、`metadata`（string→string）和实验性 `allowed-tools`。Next 严格拒绝未知 Front Matter 字段；`allowed-tools` 只作为元数据，不授予 Callable/Capability 权限。assurance/ 可选；schemas/、scripts/、references/、assets/ 是不依赖 Assurance 的 Package 根目录共享资源。Schema 文件以 YAML 1.2 表示 JSON Schema 数据模型；Script Registry scripts/manifest.yaml 声明精确 entrypoint、purpose、input/output Schema 与 llmInvocable。LLM 可读取共享资源；仅 llmInvocable=true 的 transform Script 且 Host 配置 `scriptExecution.llmEnabled=true`（默认 false）时，才可通过 host.skill-script.execute 调用。新作者源的唯一目标为 **CA-SL 1.6.0 Capability-first**，现仍未正式发布；历史 v1alpha5 作者源码与 Release 保留追溯，不能当作 1.6.0 输入或自动迁移。存在 Assurance 时由外部 Compiler 按已正式发布的版本处理。contract.yaml 位于 assurance/ 内，不是每个 Skill 的必需文件。when 是 contract.yaml 的可选字段；assurance/predicates.yaml 只承载执行期业务判断。

### 2.2 运行时发布包

Next Agent 消费外部发布的运行包：

~~~text
published-skills/<skill-id>/
├── SKILL.md
├── schemas/                    # 若有，共享 Schema 原始资源
├── scripts/                    # 若有，Script 源码与 manifest.yaml
├── references/                 # 若有
├── assets/                     # 若有
└── <Compiler-generated runtime Artifact files>  # 仅 Assurance Skill 存在
~~~

Bundle 始终保留共享资源原始文件。无 Assurance 的 Skill 不生成 Compiler Runtime Artifact，但可以携带并使用 schemas/、scripts/、references/ 和 assets/。发布包的精确 Artifact 文件清单、Manifest、Script 引用闭包和类型数据以 Compiler 正式发布契约为准；Bundle 中 SKILL.md、共享资源与 Compiler Artifact 的关联方式以 ca-skills Bundle 契约为准。Agent 不推断或重新构建 Artifact 内部语义，不把作者源中的 assurance/ 文件当作可直接执行的运行时 Artifact。当前 F08/SR-013 仍有未冻结的 Runtime Artifact API，SR-027 尚未交付正式 Bundle；在两者发布前，不得实现或声称 Assurance Bundle 可导入。

### 2.3 Agent 支持的输入契约

| 输入 | 版本/语义 | Agent 处理 |
|---|---|---|
| 无 Assurance（可含 schemas/、scripts/、references/、assets/） | Agent Skills Specification；没有 Assurance 作者源和 Runtime Artifact | 可导入；仅 LLM-guided；仅在 `scriptExecution.llmEnabled=true` 时可调用 Registry 显式开放的 Script |
| 当前冻结 Compiler Artifact | `connectionagent.io/compiler-artifact/v1alpha5`；不含新版 Request Schema 根/闭包和 when CheckedExpr/DescriptorSet | 不作为本设计的当前 Assurance Runtime Bundle；SR-004 拒绝该 API，不推断缺失语义 |
| Development Artifact | `connectionagent.io/compiler-development-artifact/v1alpha1`；`executionStatus=NOT_ADMITTED` | 必须拒绝，不得运行 |
| CA-SL 1.6.0 Runtime Artifact（未发布） | ca-skills 1.6.0 + SR-029 Capability Binding + Compiler #61 / SR-013 新 API 联合交付；准确 `languageTarget` 机器标识尚待发布 | **唯一新增 Assurance 支持目标**；只按正式 Release 的 apiVersion/Manifest/Binding 消费 |
| CA-SL 1.6.0 Capability-first | Next Issue #40 / SR-029 统一版本策略；尚未发布 | 设计目标；旧 v1alpha5 发布物保留历史身份，不做兼容别名 |

当前 v1alpha5 冻结 Artifact 缺少 F08 要求的 Request Schema 发布快照/闭包，且不能提供 when CheckedExpr/DescriptorSet。由于 Bundle 不携带 Assurance 作者源，Agent 无法仅凭旧 Manifest 证明作者源未声明 requestSchema；因此本设计不接受旧 Artifact 作为通用 Assurance Runtime 输入。新版 API 的精确名称、字段和文件路径只以 Compiler #61 正式发布契约为准，不能采用 F08 中尚待 Compiler Owner 批准的候选值。

## 3. 三种导入形态

| 输入 | Agent 处理 | Compiler 调用 |
|---|---|---|
| 无 Assurance 的 Skill Package（可附 schemas/、scripts/、references/、assets/） | 读取指导与共享资源，校验 Script Registry，返回 candidate，由 Catalog 原子激活；仅 LLM-guided | 不调用 |
| SKILL.md + 已发布 Assurance Artifact | 基本结构/必需文件/格式/类型数据检查，解析 Tool/Capability 及 contexts Schema 闭包，返回 candidate，由 Catalog 原子激活 | 不调用 |
| 无效或不完整的发布包 | 显式导入失败，不得降级为 SKILL.md-only | 不调用 |

Agent 不接收尚未发布的 Assurance 作者源作为可执行 Skill。LLM 创建或修改 Assurance 源码后，必须经外部发布流程编译并发布新的运行包，才能进入 Agent Catalog。LLM 创建或修改没有 Assurance 的 Package（含共享资源）则可按普通导入流程更新；Host Script Execution 只调用 Registry 中显式登记的包内入口。

## 4. 发布 Artifact 消费边界

Agent 只执行以下消费端检查：

- SKILL.md 存在且可读取。
- Artifact 的 apiVersion 必须属于 SR-004 明确支持的 Compiler 正式 Runtime Artifact API；当前目标是 Compiler/SR-029 联合发布的 **CA-SL 1.6.0** Runtime Artifact（精确机器标识仍待发布）。历史冻结 Artifact v1alpha5、Development Artifact v1alpha1、未知 API 均拒绝，不做兼容映射。
- 必需 Artifact 文件存在且路径位于包根目录内。
- Manifest 引用的文件、Schema/type data 和本地依赖可解析；scripts/manifest.yaml 中每个 file、entrypoint、inputSchema / outputSchema 都必须在当前 Package snapshot 内精确解析，拒绝路径穿越、缺文件、未知 Script ID、错误 purpose 或无效 Schema。
- LLM Script Action 只允许 host.skill-script.execute；Runtime 必须校验当前 Run / Skill / Package snapshot、Registry llmInvocable 标记和 `scriptExecution.llmEnabled=true`，并按该 Script 的 inputSchema / outputSchema 验证。模型不得提供路径、模块、函数、代码或命令。
- 新版 **CA-SL 1.6.0** Artifact 必须包含 Compiler 静态解析的唯一 Capability→Callable Binding，携带精确依赖包身份、kind、Effect、Schema、operation/observation exports 并供 Runtime 生成闭合 Callable allowlist；具体 Manifest 字段与路径由 SR-029 + Compiler #61 / SR-013 正式契约冻结。Callable 依赖可来自 Provider Interface 或业务 Owner Contract；contexts 的 Schema-only 依赖按 §2.3 保存，仅贡献 Schema。Provider Interface 快照按 `provider.yaml.interfacePackagePath` / `interfaceSnapshotDigest` 固定；Owner publication 由 Runtime Bindings sidecar identity 固定。旧 v1alpha5 MAS alias/Callable 作者格式属于冻结历史，不得拿来作为 1.6.0 运行时数据。
- when 的 CheckedExpr 和类型描述数据可被指定 Python CEL Runtime 反序列化。
- Artifact 文件、路径或依赖不满足要求时给出明确错误并拒绝导入。所有旧 CA-SL / 旧 Build DTO / 旧 Manifest / 旧 Runtime Artifact / v1alpha6 候选包均明确拒绝；不进行版本协商、兼容映射、旧 Scope 重解释、自动迁移、回退或混合 Catalog。

Agent 不执行 Compiler 的 Inspect/Verify 命令，不重复做 CA-SL 静态类型检查、链接、Procedure Graph 校验或 Artifact 自校验，不建立 Skill Admission、Owner Trust 或生产授权阶段。Compiler 的构建与发布流程必须保证发布物符合其自身契约。

## 5. SkillCatalog 生命周期

SkillCatalog 属于 Python Agent Core / Host，不属于 Plugin Manager。它是进程内不可变快照，包含：

- Skill ID、包引用和发布 Artifact 引用；
- 完整 SKILL.md 文本及由其生成的轻量候选元数据；
- 是否存在有效发布 Assurance Artifact；
- 已反序列化的 when 程序、CEL Profile 和类型环境；
- 发布 Artifact 声明的 Callable/Capability 依赖引用，以及其 dependency alias、stable package identity 和 export closure。注意：冻结 CA-SL v1alpha5 Artifact 的 dependencyClosure 不包含 dependency version / snapshotDigest；不能将其表述为逐 Skill 字节级依赖锁。

只有 Contract.contexts 可通过显式 alias 使用 Host Context 的导出。Importer 按正式 Manifest 和安装快照核对 Package identity、alias、Schema export 及全部传递 $ref，将精确 Schema 闭包连同来源保存到 candidate。缺 alias、缺 export、零 Schema 导出、断裂或歧义 $ref、伪造 Callable 均拒绝整份 candidate。Schema-only 不产生 Capability Binding、Action Scope 或 Tool Effect。requestSchema 根必须属于本 Skill。

有 when 时 SR-004 在返回 candidate 前一次性反序列化 CheckedExpr、构造 Program 与类型环境。SR-005 直接保留这些对象和 Schema 快照。构造失败不返回 candidate，激活失败不改变活动代。

Importer 对调用方提供的已物化包根目录执行消费端检查，返回 import candidate；不负责下载/解包 Bundle，也不直接激活 Catalog。SR-005 使用一个或多个已验证 candidate 构造候选 Catalog generation；基本检查和依赖解析全部成功后原子激活，任何失败保留旧 generation。每个 Invocation 固定其选择时的 generation。references/ 和大型知识材料按需加载，不在每次 Event 选择时扫描目录或读取文件。

Agent 不实现文件监视器、自动下载、分布式缓存或通用 Plugin 热更新。支持的更新入口是显式 Skill import/update。

## 6. Skill 选择语义

1. 先按 IPC 规范校验 Event 的逻辑身份和规范化内容（含 payload、业务元数据与 Artifact 原始字节）。同身份同内容幂等复用；同身份异内容冲突且零新增 Run/dispatch；不同逻辑身份独立处理。
2. 精确 continuation 优先，恢复原 Run，不重新选择 Skill。
3. 对新 Event 固定当前 Catalog generation。
4. 对新 Event，按各已发布 Assurance Skill 声明的 `requestSchema` 验证规范化 payload。失败时记录关联 Skill 和失败原因的输入校验诊断，在两个候选集合之外处理该 Skill，跳过 CEL。通过或无需 Schema 校验的 Skill 若声明 `when`，使用 Artifact 中已检查的 CEL 程序求值。
5. when=true 形成显式候选；when=false 排除；运行期求值错误 fail-closed 并排除该 Skill。
6. 一个显式候选直接选择；多个显式候选只允许在精确候选集合内由 LLM 消歧，并校验返回的 Skill ID。
7. 没有显式候选时，只对 SKILL.md-only 和通过前述 Schema 资格检查、未声明 when 的 Assurance Skill 做 SKILL.md 语义选择。
8. when=false 或求值错误的 Skill 不得重新进入无条件语义候选集合。
9. 无候选时澄清或拒绝；不得无 Skill 绑定地回退到 Generic Agent。
10. 精确绑定 Skill 后，才选择 Deterministic 或 LLM-guided 模式。

直接文本只对无 when 且无必需 Schema 的候选做语义选择。即使某个 when 仅引用 event.type 且该 Skill 无 requestSchema，也须在 CEL 求值前排除。禁止补造 event.type 或 typed input。空集进入澄清，CEL 与 Tool dispatch 均为零。

Continuation 仅用协议身份和 correlation 查原 Run。Skill、Artifact、generation、Node/Wait 位置均取自原 Run；消息夹带冲突身份、错 correlation 或已结束 Run 则拒绝，合法重复按原结果幂等应答，迟到消息隔离。以上路径均零重选、零 CEL 重算，拒绝或重放时新增 mutation 为零。

**以上是 Next 面向 CA-SL 1.6.0 的目标 Resolver 规则**，设计依据是 SR-029 + 本 F02（新 ca-skills 正式语言发布后以正式规范核对）；历史 v1alpha5 M.3/SA-012 仅为语义追溯，不再构成新 Resolver 的规范输入或测试正例。

when 只能读取规范化 Event 的 event.type 和 Contract.requestSchema 声明的 input 字段，不得访问 Tool、Observation、Runtime Context、时钟或可变 Host 状态。读取 input 成员必须由作者源 Contract 声明 requestSchema，并由外部 Compiler 在发布前静态检查。

### 6.1 决定性选择表与边界

| 新 Event 资格 | 显式 when 候选 | 无 when 候选 | 处理 |
|---|---|---|---|
| Request Schema 校验失败 | 排除，跳过 CEL | 排除 | 记录 Skill ID + Schema 失败诊断，不启动该 Skill |
| when=true | 保留 | 无关 | 仅在显式 true 集合内选择；一个直接绑定、多个由模型在该集合内消歧 |
| when=false / CEL evaluation error | 排除 | 无关 | 不再回退到无条件候选；错误保持可观察但不扩大可选集合 |
| 无任何 when=true | 空 | 可纳入已通过资格的 SKILL.md-only / Assurance(no when) | 语义选择仍只允许返回精确候选 ID |
| 无有效候选 | 空 | 空 | 澄清或拒绝，禁止 Generic Agent 无 Skill 回退 |
| continuation 指向现有 Run | 不重新求值 | 不重新求值 | 仅恢复绑定的 Skill + 固定 Catalog generation；缺失或过期则拒绝 |

没有 typed input 的直接文本只能进入无 when 且无需 requestSchema 的集合；模型不能用文本/元数据授予 Callable Scope。所有选择动作记录 eventId、Catalog generation、最终 Skill ID、候选集合与拒绝原因（不持久化业务秘密），重复 Event/Continuation 不应增加 dispatch 次数。外部正式 1.6.0 when/Schema Descriptor 元数据缺失时，不得按“无 when”处理，而应作为无效 Assurance 包导入失败。

## 7. when 程序的发布与运行时接口

作者源中的 when 位于 assurance/contract.yaml，由 ca-skill-compiler 在发布前完成解析、类型检查和 CA-SL G.4 静态校验，并将已检查程序及其类型环境放入发布运行时 Artifact。

Next 只在导入阶段反序列化发布 Artifact 中的程序与类型数据，并保存在对应 Catalog generation 中；不解析 CEL 源字符串、不重复静态检查、不调用 Compiler。每个新 Event 使用当前 event.type 和 input 独立求值。

CheckedExpr、google.protobuf.Any、FileDescriptorSet、DescriptorPool、字段缺失与 null 语义、G.4 optional/nullable 守卫，以及 Go/Python 互操作的具体设计，统一见[Skill 管理与选择设计说明书 §11](#11-compiler-发布物与-python-cel-运行时互操作)。本说明书只定义导入和选择消费端行为，不重复维护 CEL 二进制格式。

## 8. 执行模式派生

| Skill 状态 | 可用模式 |
|---|---|
| 无 Assurance Artifact（可含共享资源） | LLM-guided only；如 Registry 声明 llmInvocable Script 且 `scriptExecution.llmEnabled=true`，可用 host.skill-script.execute |
| 有效发布 Assurance Artifact（可含共享资源） | Deterministic 或 LLM-guided；两种模式共用同一份 Schema / Script |
| Assurance Artifact、Script Registry 或资源引用缺失 / 格式错误 / 依赖不完整 | 导入失败，不得降级 |

不增加 supportedModes 字段。执行模式从发布包是否含有效 Assurance Artifact 派生。SKILL.md-only Skill 不得启动确定性 Procedure。

## 9. 外部依赖与状态边界

- SKILL.md Front Matter 以 [Agent Skills Specification](https://agentskills.io/specification) 为格式权威（本次核对日期 2026-11-26）；CA-SL v1alpha5 不定义该 Front Matter。
- ca-skills PR #88 已合并；当前 CA-SL v1alpha5 正式来源固定为 SHA `18d8184367982ccbc835756136c4a53f9096c3a0`，release record 位于 ca-skills main `780497a2918ad3e7bdff554ab64b0ba627e867e0`。该记录证明语言规范发布，不代表 Skill Bundle 已发布。
- ca-skill-compiler Issue #61 仍 OPEN：Compiler v2.1.0 保留冻结 Artifact v1alpha5 和 Development v1alpha1；新版 Runtime Artifact API、Request Schema 根/闭包与 CheckedExpr/DescriptorSet 尚未发布。**SR-029 的 1.6.0 Capability Binding 还需联合纳入新 Release**；单独完成历史 v1alpha5 when 不构成 1.6.0 产品门槛。详见本说明书 §11。
- ca-agent-next：只负责已发布包的消费、Catalog、选择和 Runtime，不调用 Compiler。Host Resource Access 让 LLM 按需读取当前 Skill 的 schemas/、scripts/、references/ 和 assets/；Host Script Execution Capability 仅调用 Registry 的 allowlisted transform Script，不改变业务 Capability grants，也不允许模型任意 Python 执行。**新 Agent 的 Assurance Catalog 只接受 CA-SL 1.6.0 Bundle；不存在旧版导入适配层，也不允许在同一运行时加载历史 v1alpha5 Skill。**新运行包必须是 **CA-SL 1.6.0** 的正式 Compiler Artifact（准确 `languageTarget` 待冻结）；Manifest 应提供唯一 Capability→Callable Binding、精确依赖身份和可生成闭合 Callable Scope 的必要元数据；Provider Interface Package 与 Owner Contract Package 必须分别解析。新版 Manifest 的字段名、结构和引用路径尚未由 Compiler Owner 冻结，不能沿用旧字段猜测实现。Provider Interface bytes 必须匹配 provider.yaml 的 `interfaceSnapshotDigest`；Owner Contract 的实际部署版本由 Provider Runtime Bindings sidecar 的 stableId、version、publicationDigest、manifestDigest 固定，Agent 必须校验已安装 Owner publication 与 sidecar 一致。不得将 Owner ToolCatalog 当成 Provider Interface Package。冻结 Artifact API v1alpha5 不作为本 SR 的 Assurance Runtime 输入。
- Development v1alpha1 Artifact 虽然携带 packageId/version/snapshotDigest 的 Dependency Lock，但 executionStatus 固定 `NOT_ADMITTED`，不是当前 Agent 的运行时输入；不能把该 profile 的 Lock 能力套用到冻结 Artifact API v1alpha5 或新版 Runtime Artifact。新版 API 是否包含 per-Skill digest pin 及其字段，必须由 Compiler #61 正式契约决定。
- ca-skills Bundle 组装和发布由 SR-027 负责；当前 SR-027 DRAFT，ca-skills 尚无与新 Runtime Artifact API 匹配的正式 Bundle。编译器二进制 Release、作者源或本地临时 Build 输出都不能替代 Bundle 正式发布证据。
- **Next Issue #40 已将目标定为 CA-SL 1.6.0（不使用 v1alpha6）**。新作者语法只引用 Capability，编译器产生一对一 Callable Binding；Next 的新运行时从 Binding 验证唯一 Callable Scope，不接受历史 v1alpha5 Artifact，也不直接读取未编译 Capability 原文。
- 当前 CA-SL v1alpha5 MAS 作者源以 `dependencies.mas: urn:openamsm:mas:tool-contracts` 引用 Owner 契约，并通过 `capabilities` / `mas::CALLABLE` 声明与调用 Owner 能力。Compiler 的 v1alpha5 Build 在编译期通过 `resolvedDependencies` 和 `trustedBuildContext` 完成静态 Owner/Capability 链接；这是作者语义和构建职责说明，不代表冻结 Artifact API v1alpha5 可被本 SR 导入。新版 **1.6.0** Runtime Artifact 必须包含已编译 Capability Binding（含 Capability ID 和唯一 Callable 及其 kind/Effect/Schema）、精确 operation/observation Callable exports 与依赖身份；字段与闭包格式由 SR-029 与 Compiler #61/SR-013 联合冻结。Runtime 可以读取 **Artifact 中已检查的 Capability Binding**，但不能直接解析作者源或查询 Provider 私有 backend Catalog 扩权。Development v1alpha1 的 `package.json` / Interface Package / Dependency Lock 是独立构建 profile，永远 NOT_ADMITTED。Agent 不调用任一 Compiler profile。
- cel-expr-python：作为 Python Runtime 的 CEL 反序列化/求值依赖，版本固定并以跨语言 fixtures 验收。

Agent 不调用 Compiler Inspect/Verify，也不实现 Skill Admission。Compiler 在发布前完成 Build/Verify；ca-skills 组装并发布 Bundle；Agent 只做消费端基本结构检查和依赖解析。Importer 返回候选，Catalog 激活归 SR-005。

## 10. 验收要求

- 无 Assurance 包不调用 Compiler；Importer 按 Agent Skills Specification 校验 Front Matter，并检查共享资源 / Script Registry；Catalog 激活后仅 LLM-guided。Host 仅在 llmInvocable 与 `scriptExecution.llmEnabled=true` 同时满足时提供 host.skill-script.execute；`allowed-tools` 不构成业务 Capability 授权，也不授予任意脚本执行权限。
- Assurance Bundle 仅接受 Compiler 正式发布的新版 Runtime Artifact API 与 ca-skills 正式 Bundle；不接受冻结 Artifact v1alpha5、Development v1alpha1 或未知 API。
- Assurance 作者源存在但没有受支持 Runtime Artifact 时明确失败，不得降级为 SKILL.md-only。
- Importer 只返回候选；Catalog generation、原子激活、失败回滚和 Invocation pinning 由 SR-005 验收。
- 已发布 Assurance Artifact 包不调用任何 Compiler 命令。
- 缺失文件、未知 Artifact 格式、无效 CEL/type data、路径越界和未解析依赖均导入失败，不降级。
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

Agent 不调用 Compiler Check/Build/Inspect/Verify，不导入 Assurance 作者源作为运行时 Artifact，不建立独立 Skill Admission。现有冻结 Artifact `connectionagent.io/compiler-artifact/v1alpha5` 不包含新版 Request Schema 快照/闭包和 when CheckedExpr/DescriptorSet，SR-004 不将其作为当前 Assurance Bundle 导入。新版本化发布 Runtime Artifact API 由 Compiler #61 / SR-013 冻结；Next 只按正式 Release 消费，不扩展冻结格式。Development v1alpha1 永远 NOT_ADMITTED，不得作为运行时输入。

### 11.2 CheckedExpr 与类型环境

Compiler 负责在发布前对 when 进行解析、类型检查和 CheckedExpr 生成。发布 Artifact 必须提供 Python Runtime 可消费的标准 checked program 表示，以及求值所需类型环境（例如 DescriptorSet）。精确 Artifact 版本、Manifest 字段、文件名和 Any 类型 URL 由 EC02 正式契约定义；Next 不自造文件名或字段。

Next 在 Skill 导入时反序列化已检查程序和类型环境，建立运行时 Program。Event 热路径不解析 CEL 源、不执行类型检查、不编译，也不调用 Compiler。

### 11.3 数据映射与跨语言一致性

- event.type 是规范化 Event 类型；input 的类型来源是 Contract.requestSchema。
- 类型环境必须表达字段、枚举、嵌套结构和可选/空值语义。
- Go Compiler 与 Python Runtime 使用同一组权威 fixtures，至少覆盖 true、false、缺失字段、null/optional、枚举、嵌套字段和类型错误。
- Python 求值结果必须与 Compiler 的标准 fixtures 一致。
- 不实现第二个 CEL Parser/Type Checker，不把 CEL 源码转成自定义 AST，不以动态类型逃逸静态约束。

如果 ca-skills 规范或 Compiler 发布契约尚未正式可用，相关消费实现标记 BLOCKED / NOT_VERIFIED；不得猜测或临时发明 Artifact 格式。

### 11.4 外部依赖与验收

- EC01 ca-skills：作者格式与 when 语义权威；SR-027 负责 Bundle 组装与正式发布。
- EC02 ca-skill-compiler：CheckedExpr、类型环境和新版 Runtime Artifact 发布契约权威；SR-013 / Compiler #61 负责交付。
- SR-004：包导入、Manifest/文件/依赖消费端检查，返回 import candidate。
- SR-005：SkillCatalog 驻留、generation 原子激活和已检查 when 程序消费。
- SR-006：when 选择、语义选择和 Continuation。
- Acceptance：SR-004 AC-004-01～06；系统 EX-05～08/11/12；EX-21～EX-29 由 SR-005/006 等共同承担。


本节是设计要求，不代表 Go → Python CEL 互操作或 Next Runtime 已通过。

## 12. 中央设计移交与实现证据

按 [CA-SL 发布与候选](../../规范/CA-SL语言基线与版本规范.md) 确认 when 的发布状态。[F08 编译与发布](../F08-技能编译与发布/技能编译与发布设计说明书.md)负责组装 Bundle，EC02 负责生成已检查程序，Next 由 SR-004～006 消费与验收；F09 Studio 维护作者编辑。SR-004 只负责返回已验证 import candidate；SR-005 负责 Catalog generation；SR-006 负责选择与 Continuation。Compiler API 和 Bundle 生产依赖分别由 SR-013、SR-027 提供。Issue #40 / SR-029 定义的 **CA-SL 1.6.0** 是下一正式产品目标；历史 v1alpha5 规范和产物继续冻结但不作为新 Runtime 输入。1.6.0 未正式发布前相关实施仍 BLOCKED。


## 13. 3GPP 原版 OpenAPI 直接引用与 Event 选择 / Codec Result 分段（IR-009）

3GPP SBI 类型来源为 SR-031 原样代发布的 OpenAMSM OpenAPI 3.0 Source Bundle。原始 YAML / 相对 `$ref` 不改写。CA-SL 1.6.0 的 Skill-owned `requestSchema` 根继续遵循本地 G.4；在显式声明并 pin Source Bundle dependency 后，可以直接引用原版 OAS 3.0 `components/schemas`，由 Compiler 按 OAS 3.0 Schema Object dialect 解析，不要求额外 Adapter。Host Context 仍只经 `Contract.contexts` 引用。

F02 保持 **Event Schema → Skill 自有 `requestSchema` → `when` → candidates**。T1 只使用已验证 SBI / 归一化 Event 中实际到场的字段、业务 operation identity、最小 discriminator 和受授权原始 Artifact 引用；NAS-only 的 PDU Session Type / SSC mode 不得成为 T1 必填。Resolver 不在 T1 调 Codec，也不因引用 OAS3 Schema 而执行解码。

T2 的 Provider Codec Result 只在选定 Skill Procedure 的 READ 后可用，且必须符合正式 Output Schema / 消息 Profile；后续 Node 通过显式 SourcePath 使用。0xD4 / N2 completion 只续跑旧 Run，不重新选择 / 评估 when。Codec Result 不等于 Owner Proof。

没有正式 Source Bundle / Compiler OAS3 Resolver / Codec Provider 时，只阻塞实际声明相应依赖的 Skill 子路径；无 Codec 的 Skill 不受影响。所有产品 AC 未执行，CA-SL 1.6.0-only，无旧版兼容或默认值补造。

## 修订记录



| 日期 | 版本 | 修订者/模型 | 章节 | 修订内容 | 原因 | 关联 |
|---|---|---|---|---|---|---|
| 2026-11-25 | 0.1.0 | 历史修订者/模型未记录 | 原第 1～10 章 | 既有 Skill 导入/选择设计基线 | 初始设计登记；逐章历史记录未建立 | SR-004～006 |
| 2026-11-25 | 0.2.0 | GPT-6.2（ChatGPT） | 第 11 章及全文归属 | 合并 CEL 互操作设计，明确 EC01/EC02 权威和 Next 消费边界 | 避免 Skill 功能拆成多份设计说明书 | F02；SR-004～006；EC01/EC02；PR #1 |
| 2026-11-25 | 0.2.1 | 未记录 | 全文 | 刷新需求追踪、目录或证据引用 | 对齐最新分支与 IR/SR 基线 | 见关联 SR |
| 2026-11-25 | 0.2.2 | Codex / GPT-6 | §12 | 记录中央规范与 Compiler/Studio/Next 分工 | 跨仓设计移交 | IR-006 |
| 2026-11-25 | 0.2.3 | Codex / GPT-6 | §6 | 明确 Event Request Schema 资格与诊断次序 | 对齐 CA-SL 候选 M.3／SA-012 | IR-003、SR-006、EX-10 |
| 2026-11-25 | 0.2.4 | GPT-6.2（ChatGPT） | §4、§5、§9 | 将 Tool/Capability 依赖解析扩展为 Provider Interface 与 Owner Contract 两类精确快照，并明确 MAS `mas` dependency | 对齐 ca-skills v1alpha5 MAS 作者源与 Compiler 冻结 Build / Development 分离路径 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.2.5 | GPT-6.2（ChatGPT） | §4、§5、§9 | 更正冻结 v1alpha5 Artifact 不含 dependency snapshotDigest 的事实，明确 Owner version pin 由 Provider sidecar / 部署配置提供 | 避免把 Development v1alpha1 Lock 能力误认为当前 Agent 运行期能力 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.2.6 | GPT-6.2（ChatGPT） | §4、§9 | 补充 provider.yaml interfaceSnapshotDigest 对 Provider Interface snapshot 的部署级固定 | 与 Owner Contract sidecar pin 一起覆盖当前 Tools 依赖的两种外部契约 | IR-006 · SR-015 · Issue #12 |
| 2026-11-25 | 0.2.7 | GPT-6.2（ChatGPT） | §7、§11、§12 | 保留 F02 v0.2.6 已有的 when/Request Schema 语义与 Provider pin，刷新 Compiler/F08/SR-013 的最新设计引用 | 与 SR-013、F08、EC02 Compiler 新设计保持同一版本基线 | Issue #12；IR-003；SR-013 |
| 2026-11-25 | 0.2.8 | GPT-6.2（ChatGPT） | §7、§11、§12 | 同步 F08、EC02 Compiler 与 SR-013 最新设计版本引用，保留 F02 已冻结的 when/Request Schema 语义 | 统一 Compiler 设计闭环版本 | Issue #14；IR-003；SR-013 |
| 2026-11-25 | 0.2.9 | GPT-6.2（ChatGPT） | §7 | 修复 CA-SL v1alpha5 when 发布/运行时依赖的失效锚点，指向当前语言基线 §3 | 不改变 M.3/SA-012 语义；使候选资格引用可导航 | IR-003；Issue #12 |
| 2026-11-25 | 0.2.10 | Codex / GPT-6 | 正文 | §6、追踪 对齐语言发布与 Compiler/Bundle 职责 | 消除执行歧义并同步中央设计 | Issue #12 |
| 2026-11-26 | 0.2.11 | GPT-6.2（ChatGPT） | §4、§9 | 明确冻结 v1alpha5 Artifact 不序列化 Skill Capability ID；Compiler Build-time 校验作者源 Capability，Runtime Scope 只从 operation/observation exports 建立 | 对齐 F03.05 与 Compiler v2.1.0 frozen artifact schema，避免实现者读取不存在字段 | IR-006 · SR-015 · Issue #12 |
| 2026-11-27 | 0.3.1 | Codex / GPT-6 | §6 | 对齐 Event 身份冲突和直接文本选择规则 | 落实 PR #46 第二轮独立评审 | Issue #12，PR #46 |

| 2026-11-26 | 0.2.12 | GPT-6.2（ChatGPT） | §1～5、§9～12、修订记录 | 区分 Importer candidate 与 SR-005 Catalog 激活；明确冻结 Artifact v1alpha5、Development v1alpha1、新 Runtime Artifact API 的消费矩阵；同步 CA-SL v1alpha5 固定 SHA、Compiler #61 / SR-013、SR-027 Bundle 和 Issue #40 v1alpha6 边界 | 防止把旧冻结 Artifact/Development Artifact 当作当前可运行 Bundle，避免在 Manifest/Bundle 契约未冻结时让 SR-004 或 Harness 猜测实现 | Issue #43；SR-004；SR-013；SR-027；Issue #40 |
| 2026-11-26 | 0.2.13 | GPT-6.2（ChatGPT） | §9、修订记录 | 明确 F03.05 的 v1alpha5 依赖/Callable 语义是语言与构建语义，不代表冻结 Artifact API v1alpha5 可导入；新版 Runtime Artifact 的字段映射必须由 Compiler #61 正式冻结 | 避免把旧 Artifact 的 dependencyClosure 字段猜测为新 Runtime Artifact API 的字段 | Issue #43；SR-004；SR-013 |
| 2026-11-26 | 0.2.14 | GPT-6.2（ChatGPT） | §2.1、§2.3、§9～10、修订记录 | 固定 SKILL.md Front Matter 使用 Agent Skills Specification（name/description 与可选字段）；明确它与 CA-SL v1alpha5 assurance/ 语法分离，allowed-tools 不授予运行权限 | 防止把 CA-SL Contract 误作 SKILL.md Front Matter，避免把实验性 allowed-tools 当作 Capability Grant | Issue #43；Agent Skills Specification；SR-004 |
| 2026-11-26 | 0.2.15 | GPT-6.2（ChatGPT） | 文档头、§2～4、§9、§12、修订记录 | 按 Issue #40 将新 Assurance 消费版本改为 CA-SL 1.6.0，固定已编译 Capability→Callable Binding 与新 Runtime API 联合门槛 | 避免用 v1alpha6 候选或旧 v1alpha5 Callable Artifact 作为新运行包，保留历史冻结身份 | Issue #40/#43；SR-029；SR-004；SR-013 |
| 2026-11-26 | 0.2.16 | GPT-6.2（ChatGPT） | §4、§9、修订记录 | 新 Agent 导入/Catalog 全面拒绝历史语言与旧 Artifact、无双轨并存或 fallback | 实现 1.6.0 单版本运行时，不让历史数据混入当前 Skill 执行 | Issue #40/#43；SR-004；SR-005 |
| 2026-11-26 | 0.2.17 | GPT-6（ChatGPT） | 文档头、修订记录 | 将 CA-SL 1.6.0-only 的目标设计明确推进待独立评审；完整规范/API/Bundle 未发布 | 保持设计评审与实施 READY、产品 RELEASED 分离 | Issue #40；SR-029；PR #44 |
| 2026-11-26 | 0.2.18 | GPT-6（ChatGPT） | 核心规范与验收章节 | 去除 v1alpha5 M.3 规范依赖；新增 1.6.0 Resolver 结果表、拒绝和 continuation invariants | 为 SR-005/006 提供唯一可审查的选择语义 | Issue #12/#40；SR-005/006；SR-029 |
| 2026-11-27 | 0.3.0 | Codex / GPT-6 | §2～6 | 固定 Schema-only、Program 归属及 Resolver 输入边界 | 落实首轮独立评审，区分设计依据与实测证据 | Issue #12，PR #46 |
| 2026-11-27 | 0.3.2 | ChatGPT / GPT-6 | 3GPP Schema/Codec 分阶段消费 | 对齐 SR-031 公共类型、T1 Request 与 T2 Codec Result，新增分期拒绝/验收范围 | 修复标准输入来源与实现门禁的跨仓断点 | IR-009；Issue #47；SR-031/026 |
| 2026-11-27 | 0.3.3 | ChatGPT / GPT-6 | 3GPP 原版发布裁决 | 版本随 OpenAMSM、原版 YAML 完全不改；将只读 Source Bundle 与可选 Adapter / Codec Output 分离 | 防止标准原件被类型适配误改 | Issue #47；SR-031/026 |
| 2026-11-27 | 0.3.4 | ChatGPT / GPT-6.2 | §13 | 改为原版 OAS3 组件直接引用与 T1/T2 阶段约束；移除 Adapter 前置 | 对齐原始标准直接引用与 Compiler dialect-aware 解析 | IR-009；Issue #47；SR-031/013/026 |
| 2026-11-27 | 0.3.5 | GPT-6.2（ChatGPT） | §2～5、§8～10 | 将 schemas/scripts 作为根目录共享资源，允许无 Assurance Skill 使用资源；增加 Host Script Execution Capability 的导入与运行边界 | 使 LLM-guided 与 Deterministic 共用资源，同时不授予任意 Python 执行 | Issue #49；IR-008；SR-032 |
| 2026-11-27 | 0.3.6 | GPT-6.2（ChatGPT） | §2、§4、§8、§10 | 将 Host Script Execution 的 LLM 暴露条件统一为 Registry 标记与 `scriptExecution.llmEnabled` 双门禁；统一 Assurance 文件路径 | 消除 F02 与 CA-SL / Host 配置之间的口径歧义 | Issue #49；IR-008；SR-032 |
