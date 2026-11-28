> 迁移来源：ca-agent-demo/docs/design/createdsession-current-implementation-baseline.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：当前 main 的实现基线和证据摘要  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；证据的当前有效性需按具体 main/PR/测试 SHA 单独核验。

---

> **HISTORICAL / SUPERSEDED (2026-11-11):** non-normative history/evidence. Current authority: docs/design/generic-agent-host-architecture.md and docs/work/generic-agent-host-final-convergence-20261110.md.

> **HISTORICAL — 5GC BUSINESS / PROTOCOL EVIDENCE ONLY** **5GC / PDU Session business and protocol evidence only.** The entire body below contains dated implementation snapshots, old commands and external-owner evidence; it does not describe the current Generic Agent Host architecture or guarantee that the recorded code/status remains current. Revalidate every code and runtime claim against the current owner repository and commit. Do not use this file as a Host migration plan. Current architecture and task authority: [Generic Agent Host execution routes](execution-routes.md) and [final convergence Goal](../work/generic-agent-host-final-convergence-20261110.md).

# CreatedSession 当前实施基准（2026-10-30）

> **Historical W0 policy snapshot（2026-11-09）**：5gc-intent policy boundary 的 business intent absent -> establish-pdu-session default；present-valid -> existing Intent / Root routing；present-invalid / unknown / ambiguous -> fail closed。默认仍须 deployment allowlist / exact Admission / READY。当前 main 尚未接入该 policy，Resident 仍固定 Skill，wheel 未打包 5gc-intent / establish。当前 Fabric flat v0.1 无业务 intent / 自然语言字段；intent_ref 是 action correlation。本文其余业务步骤与 P8-D4 运行证据按各自历史日期理解，不代表当前 main 重跑通过。见 [W0 audit](w0-system-audit.md) 与 [任务包](../work/runtime-mechanism-convergence-task-package.md)。

> **历史用途**：记录当时 `ca-agent-demo` 确定性 CreatedSession 开发的入口、代码状态和业务/协议证据。本文不再提供当前实施入口或任务边界；所有状态必须按对应日期和 SHA 理解，不得从文件日期推导当前 PASS。

> **W0 证据边界**：P8-D4 的核心网业务执行历史 PASS 不等于 Fabric HELD action terminal responsibility 已闭合。归档 \`resident-shutdown-attempt2.json\` 记录 \`pendingHeldActions=1\`、\`UNRESOLVED\`、\`STOPPED_WITH_RESPONSIBILITY_RETAINED\`。不要把资源 Finalize PASS、Runtime SUCCEEDED 或 SMF waiter delivery 误写成 Fabric action disposition PASS。完整分析见 [W0 系统审计](w0-system-audit.md)。

## 0. 项目定位与范围冻结

当前项目定位为 **Controlled Resident Agent Demo**：以单实例、顺序 Invocation、确定性 Skill/Runtime 和真实网络工具交互，验证 Agent 能否按既定业务流程推进真实 5GC PDU Session 建立。目标是验证 Agent 的业务编排与真实网络闭环，不是建设通用生产级 Agent 平台。

- **运行模型**：一个 Resident deployment、一个稳定 reference journal、同一 journal 同时最多一个活动 Host；Host 顺序处理 Invocation，每次 Invocation 创建独立 Runtime。Skill 的 `assurance/procedure.yaml` 是确定性执行图，Predicate/Observation/Verification 提供事实与完成判定。
- **安全底座**：保留精确 NetworkIntent/Source 身份绑定、Mutation 外部副作用前持久化 Registration、Reject POST 前持久化 Attempt、Mutation/Reject 在 Journal 内原子互斥、未知结果 fail-closed、责任留存、单实例进程锁和有界安全 Shutdown。这些机制直接保护真实网络操作与实验可信度，不因“Demo 简化”而删除。
- **锁的边界**：当前 POSIX `flock` 只保护共享同一稳定 journal 的本机进程实例；它不是跨主机分布式锁、租约或 HA 机制。一个 journal 一次只允许一个活动 Host，不代表支持多实例部署。
- **D2 历史基线**：PR #138 于 2026-11-04 合入 main；本文 D2 设计与本地测试数字是 2026-10-30 候选快照。当前 W0 目标是把 D2 Resident 壳收编为唯一 Host，不再保留 CreatedSession 第二套执行路径。
- **明确非目标**：多实例 HA、自动故障转移、通用分布式锁/租约、自动未知结果对账与恢复平台、Runtime snapshot/restore、多租户部署、生产级监控运维平台、通用 Agent Host Framework，以及继续抽象通用 Journal/Lifecycle Framework。
- **变更准入**：新增工作必须直接影响（1）Demo 核心能力，（2）真实网络操作安全，或（3）实验结果可信度；实现成本很低且能避免严重事故的保护可适度保留。其他生产化复杂度延期。
- **通信与信任边界**：Demo P0 不建设生产级 SBI TLS/mTLS 或 OAuth2 代理语义；当前 N11 使用 H2C。复用现有 Demo/Provider/Fabric 通信路径与信任配置，不把某条内部接口的 mTLS 泛化成所有 SBI 的要求。既有专用契约仍须遵守，例如 Provider → Fabric C intent-query 的 mTLS 与精确证书 pin；不得擅自取消。禁止新建 CA/PKI、证书签发、TLS/身份基础设施，也不得为测试关闭现有校验；只有真实运行证据表明已有握手或证书配置故障时才做针对性修复。
- **现有代码约束（已按既有契约对齐）**：五类 Demo → Provider adapter（dispatch、prepare、transfer、operation-context、pcf-create-inputs）已统一到共享明文 HTTP transport：只接受固定白名单 `http://` origin，禁用 ambient proxy 与自动重定向，保留有界响应与错误分类；不再要求 CA bundle、client certificate、private key，也不创建 TLS context。Provider 侧以自身 `runtimeCallerCidrs` 做部署层准入，Demo 仍携带完整 environment/subject/invocation/transaction/operation 绑定，socket 到达不构成业务授权。这是受控本地 Demo 的传输调整，不是生产明文许可，也不是新的 PKI 工作项。

后续主要研发目标转为真实 Fabric/Provider/SMF/RAN/N4/UE 接点与完整 PDU Session E2E；D3 只按证据和依赖逐项推进，不以扩展 D2 Host 代替真实网络集成。

## 1. 资料权威性与阅读顺序

1. **架构决策**：[`sandbox/docs/design/createdsession-agent-orchestration.md`](https://github.com/odango-chan/sandbox/blob/main/docs/design/createdsession-agent-orchestration.md) 及 [N1/N2 设计](https://github.com/odango-chan/sandbox/blob/main/docs/design/createdsession-n1n2-verification.md)。既有的 Agent/SMF/Fabric 分工不因局部实现受阻而重新选择。
2. **本 Demo 可执行业务来源**：`skills/establish-pdu-session/assurance/procedure.yaml` 定义确定性执行顺序和前、后置步骤，`contract.yaml` 定义完成要求，`predicates.yaml` 定义事实；`SKILL.md` 是面向模型的业务指导，不是第二份执行图。
3. **具体 owner 实现和接口**：Demo 仅为引用实现与适配；真实 Provider/Fabric/Open5GS 行为以各 owner 已合并代码、明确候选 PR 和可追溯运行证据为准。设计文字、接口候选、注册的 Observation ref 或 synthetic 测试都不能升级为真实 owner 事实。
   **特别注意：** Sandbox 总设计页头的 `Proposed / Implementation: NOT_STARTED / Acceptance: NOT_RUN` 是 2026-10-22 的历史状态标记，不应解释为 2026-10-29 的所有仓库均无实现；其中的既定职责原则继续作为架构依据，实际代码和验收状态必须按本页第 3 节及当前 owner 证据核对。**该历史说明截至原文档快照；此次架构正文的响应交付边界已在 Sandbox 修正，但并未将相关组件标记为 PASS。**
4. **历史材料**：`createdsession-runtime-implementation-plan.md`、`createdsession-runtime-implementation-handoff.md`、`createdsession-runtime-prerequisite-matrix.md` 的旧 D0–D7 施工命令、旧 PR #110 基线和早期 Toolchain 兼容检查**仅供追溯，不是现行 Goal**。历史记录原样保留；发生冲突时，不按其旧施工指令执行。
5. **仓库规则**：仍须遵守 `AGENTS.md`、`configs/component-map.yaml` 和 component boundaries。对外仓写入需要单独授权，本文不扩大权限。

## 2. 已敲定的系统行为（目标；不等于已经实现）

- Fabric 捕获 **AMF 的同一次 CreateSMContext**：向 Agent 提供可追溯的触发/输入，同时使原 Open5GS SMF 保有建立原生会话上下文的请求路径；**原 HTTP 请求只能有一个响应 owner**。不得把双路业务输入误实现为双重 HTTP 应答。
- Agent 按 Skill **独立决定** UDM Get、UDM Subscribe、PCF Create、NAS/N2 SM 内容和后续步骤；通过获准 Provider/Fabric/SCP 路径主动执行。**SMF 出站请求不是 Agent 决策触发器，也不能当作 Agent 的响应。**
- Fabric 按本次操作及当前会话实例治理 **SMF 与 Agent 的竞争 SBI 副作用**。不能凭 SUPI/PSI、服务名、时间接近度或本地 reservation 猜全局唯一 owner；不能一律放行重复操作或一律阻断委托给 SMF 的 N2。
- 当前 Open5GS SMF 仍提供原生会话状态机及 **PFCP/N4**，不修改上游源码。Agent 的决策**不能为迎合 SMF waiter 而改变**。对于**当前完整真实 E2E**，已经选择 Fabric 将 Agent 主动 SBI 得到的真实 NF 响应安全交付给原 SMF 对应 waiter，让其继续地址分配、PCF 和 N4；**这是当前完整 E2E 所需的实施机制，不是可省略的优化**。该交付的结果**不是 Agent 独立决策或自身已完成 SBI 步骤的门槛**；若无法精确证明操作、实例、原 waiter、真实响应语义及资源/callback 责任的兼容性，则 fail-closed，保留 Agent 已完成步骤事实；依赖 SMF 地址分配、PCF 消费或 N4 的后续步骤必须 BLOCKED，E2E 保持 BLOCKED/UNKNOWN，不能伪造交付成功。
- **B 资源所有权**：UDM SDM Subscribe、PCF SMPolicyControl Create 均由 Agent 按 Skill 主动执行；其 Location、callback、后续通知/更新、对账、清理及移交由 Agent 侧明确管理者负责。原 SMF 只消费经过 Fabric 安全关联的兼容响应，不因保存了 201/Location 而自动取得资源所有权；Fabric 还必须治理原 SMF 可能发起的重复 Create、Update/Delete 与 Unsubscribe。
- **通知和 N4**：当前 pinned Open5GS 2.8.0 的 SM-policy producer 只构造 `notificationUri/update`；Provider callback 对固定 `/update` 的兼容不代表存在 SM-policy `/terminate` producer。Agent-owned callback 只接收实际 producer 发出的通知；其他通知必须先核实其 producer、URI 和资源语义，不能从事件名称推导路由。对于已证明的 UpdateNotify，仍须在证明 PCF association 与当前原 SMF `smContextRef` 的精确映射、通知来源和资源状态后，Fabric 才能兼容交付给原 SMF。**当前 Agent 没有 N4/PFCP 工具；所有 PFCP 建立、修改、释放均由原生 SMF 执行**。callback 204、兼容交付与真实 N4/UPF 成功要分别验证；接点未验收时不得声明通过。
- NAS/N2 SM 业务由 Agent 决策、Provider 受约束编解码及准备、Fabric/SCP 交付；AMF/gNB 保有外层 NGAP、N2/SCTP 和 NAS transport/security。后续 AMF `UpdateSMContext` 原请求归 SMF 处理，可向 Agent 提供获准真实外部事件；不能由 Agent 并行应答其副本。
- **三种结论分别记录**：Agent Procedure outcome、临时 SMF 兼容结果、真实 RAN/N4/UE 会话结果。HTTP 200/201、COMMITTED、HELD 的处置、PFCP 发送、已注册 Observation 或模型结论均不能单独证明 PDU Session 建立成功。

以上为既有设计基线，**响应交付已选定 ≠ Fabric 已实现或已验证**。不能据此推断当前 Fabric 已完成双路分发、逐操作 SMF 出站治理或安全 waiter 交付；独立 Agent-only 的 A 片段不能冒充完整 E2E。

## 3. 代码和证据快照

**2026-10-29 至 30 审计快照**：Demo `eb421c9a5cd0fdc912a71c84a11fb10a2a486d03`；Provider `0f1c451537e133ab3cd2cf00c0a0b4456b4f6124`；Fabric `cb3b884197221c8534d6d518ffcdff16a929fca6`；Sandbox `23b87eb51fa54941fc307812dde48c2e49884ae0`。完整版本清单、复现方式和日志见 [审计记录](../../artifacts/reviews/20261030-execution-routes-audit/README.md)。

本轮 Demo main 的 `UV_FROZEN=1 make verify`：**977 passed / 1 skipped / 2 deselected**；docs/source validator 通过。已按 Git blob 核对源文件。Provider/Fabric 本轮只读核对，未重跑其本地门禁，未执行真实 5GC E2E。不要把 Demo 本地通过写成外部组件或联合 live PASS。

本工作分支（PR #137）已合并为 main `bf445ad777149af5af2dfa0a5bdea18d0451303e`：
合并前 `UV_FROZEN=1 make verify` 为 **1036 passed / 1 skipped / 2 deselected**；
CreatedSession 专项 368 passed；`test_createdsession_runtime_source_freeze.py` 45 passed；
`scripts/validate_docs.py` 与 `git diff --check` PASS。同上，这只是本地门禁。

**D2 Resident Host（2026-10-30 候选快照，PR #138 已于 2026-11-04 合入）**：
在 main `bf445ad` 之上完成单实例 Resident 组合入口与有限故障保护：严格部署配置、
READY 门禁、持久 HELD-action 责任、封闭状态机、进程独占锁、Mutation/Reject 原子互斥、
duplicate Reject 本地去重、完整 NetworkIntentV2 身份绑定、顺序 Invocation 与安全 Shutdown。
本地门禁证据：Held 专项 **49 passed**；Resident 专项 **114 passed**；
CreatedSession 专项 **531 passed**；`UV_FROZEN=1 make verify` **1199 passed / 1 skipped / 2 deselected**；
原代码候选的 docs validator 与 `git diff --check` PASS（本次文档范围更新后需本地复跑）。Fabric/Provider 为本地协议双替身或本地假 HTTP 服务，
**不是 live 5GC**；真实 ingress、dispatch、SMF waiter、RAN/N4/UE 仍未验收。
完整说明见 [Resident Agent Host](createdsession-resident-host.md) 与
[D2 审计记录](../../artifacts/reviews/20261030-createdsession-d2-resident-host/README.md)。

| 组成 | 已可确认 | 仍属候选或未建立 |
| --- | --- | --- |
| Demo resident | #129/#130 的 resident/Predicate 修正已在 main；`createdsession_service.py` 顺序服务、`createdsession_provider_resident.py` 组件装配与 coverage 已实现；D2 新增 `createdsession_resident_config.py`、`createdsession_resident_host.py`、`createdsession_held_disposition.py`、`scripts/run-createdsession-resident.py`，并在 journal 增加 `held_actions` 持久责任表；R4-B P2 已让 READY 需求从已准入 artifact 派生，expected Effect 由 Host 能力契约独立提供 | coverage 只证明注册/契约完整性；缺真实 external source 时仍拒绝 READY；D2 只在本地 Fake Fabric/Provider 下验收，真实 ingress/dispatch/RAN/N4/UE 未验收。旧 #120/#121/#122 已关闭；#122 的 YAML 展平/Toolchain 适配不纳入本路线 |
| D2 resident host（PR #138，2026-11-04 MERGED；历史本地证据） | 单实例 Resident 组合入口；持久 HELD-action 责任；封闭状态机；本机 `flock`；Mutation/Reject 原子互斥；duplicate Reject 本地去重；flat 消息身份绑定；顺序 Invocation 与安全 Shutdown | Held 49 passed；Resident 114 passed；CreatedSession 531 passed；`make verify` 1199 passed / 1 skipped / 2 deselected；原代码候选 docs validator / diff check PASS（本次文档更新后需本地复跑）；Fake Fabric/Provider 集成 PASS | 真实 Fabric ingress/source/reject、Provider dispatch、SMF waiter、owner-native Observation、RAN/N4/UE 均未由该候选本地门禁验收；D2 不提供 HA/自动恢复 |
| A 阶段真实 UDM Get | 2026-10-27 历史 source-bound HTTP 200 与 `subscription_usable=PASS`，固定 503 结束 HELD，mutation count 0 | 仅 A-only 历史切片；本轮没有复跑，不证明 B/C、原 SMF N4 或完整 UE 会话 |
| Demo #133 | PTI `1..254` 语义已由 PR #137 整合并进入 main `bf445ad`（0/255 拒绝；raw ingress 可携带 `0..255`，消费者校验仍为 `1..254`） | main 已包含该消费契约；Provider 两侧 schema/validator 均为 `1..254` |
| Demo #134 | PCF create-inputs readiness 与 create governance 分离已由 PR #137 整合并进入 main `bf445ad` | governance source 缺失继续 UNKNOWN/BLOCKED；不是 PCF Create live PASS |
| Provider B/C | #39/#41 及 #43/#44/#45/#46 已合入；有 callback/resource journal、精确 replay lineage、C service、PCF create-inputs；`callbackDeliveryPath` 已支持固定 `/update` | 创建输入不证明无冲突或授权；Provider 内预留不排除 SMF 竞争发送；回调接收不证明 SMF 消费；真实 B/C 未联合验收 |
| Fabric | #77 的 opt-in UpdateSMContext/N2 source journal 已在 main；已有源码审计显示透明主线和独立 governed/dispatch 组件 | 本轮未重审全部 Fabric 代码；未有 current-instance join、authenticated source query、双路 ingress、SMF waiter 安全交付的联合通过证据 |
| 完成事实 | P8-A2 起全部 owner-native ref 都有当前实现（见 §3 的 P8-A2 段） | 仍无 live 5GC 结果：RAN/N4 观测只在 component 与 HTTP Joined 层验收；`createdsession.ue_sm_configuration` 已从 Skill 成功条件中删除 |

下一步不再按旧 D1/D2/D3 逐单推进；PR #138 已合入 main，D2 单实例能力作为历史安全基线保留。当前施工顺序以 [W0 系统完整审计](w0-system-audit.md) 与 [统一收敛任务包](../work/runtime-mechanism-convergence-task-package.md) 为准：W1 Root eligibility → W2 5gc-intent policy → W3 单一 Resident Host → W4 Link / Admission 收敛。LLM #119 的未合入状态另见 [LLM 审计](llm-skill-execution-implementation-audit.md)，不能把它的测试结果合计到此处。

**D1 跨阶段引用修正（2026-10-30，本分支）：** PCF create inputs
`pcfCreateInputsRef` 与 operation context `contextRef` 已按语义类型分开。
UDM Subscribe 不再读取不存在的 `policy-create` operation context：它消费
PCF inputs handle 的 lifecycle/invocation 绑定，要求 handle 回显的
`ingressRef` 与本次 dispatch 的 `ingressRef` 精确相等，并在 Runtime 本地重算
selection digest 与 Provider 返回值精确比较。N4 initial-resource wait 不再
把 PCF inputs handle 当 operation context，而是用
`currentSessionInstanceRef` 作为 typed session-instance join。详细类型表、
阶段、Provider/Demo 责任划分和 fail-closed 规则见
[CreatedSession 跨阶段引用类型](createdsession-cross-phase-reference-types.md)。
这是本地契约与组合测试结论，不是 live Provider/5GC PASS。Provider 的 UDM
dispatch **在 dispatch 内部自行注册 callback binding 并持久化 operation
intent**（已核对 Provider `main` `0f1c451` 的 `createdsession_dispatch.go`
与 `intent_store.go`），因此不存在“必须由外部 owner 预先注册 intent”的前置
缺口；live 仍缺 Provider 私有 profile 绑定、可达 callback/durable store、
Fabric→UDM 路由和真实 5GC 执行。

**P6 候选（2026-11-02，分支 `codex/createdsession-p6-hold-lifecycle`，基线 `codex/createdsession-pcf-pren4-inputs@b514500`）：**
上段 D1 的“UDM Subscribe 消费 PCF inputs handle”已被本轮**取代**：该 handle 依赖尚未发生的 SMF PCF Create，属于未来依赖。
当前 authored 顺序为 `UDM Get → Select Configuration → UDM Subscribe → PCF Hold Binding → PCF Pre-N4 Inputs → PCF Create → N4 Wait`：

- UDM Subscribe 只使用 exact Provider UDM record + 受治理 selection + operator pins；
- PCF Create 阶段先 `ca.session.pcf_hold.bind` 选出一个 Fabric-issued
  `PCF_SM_POLICY_CREATE` hold（精确 environment/lifecycle/SUPI/PDU Session），
  再用同一 `holdRef` 读取 Pre-N4 inputs，最后在 operation identity/commitment
  确定后 claim，并立即以同一 `waiterRef`/`operationRef`/`transactionRef`/
  `agentOperationDigest` 发送 Provider mutation；
- `createdsession.pcf.create_governed` 仍无 owner source（Fabric 3e8e416 无
  lifecycle isolation / competing-create 记录），保持 UNKNOWN；
- `Provider ↔ Fabric` 的 held-request digest 前缀不一致（Fabric 裸 hex，
  Provider 要求 `sha256:`）被记录为 `EXTERNAL_SEMANTIC_MISMATCH`，pinned 组合下
  Provider Pre-N4 read 只能 UNAVAILABLE；
- 本地门禁 `UV_FROZEN=1 make verify` 1328 passed / 1 skipped / 2 deselected；
  仅 Component/Joined 证据，**不是 live PASS**，本次未占用真实 Fabric lane。

**P6.1（2026-11-02，分支 `codex/createdsession-p6a-hold-completion`，基线 `codex/createdsession-p6-hold-lifecycle@4b0c60a`）：**

- **Held-request digest 前缀不一致已修复（owner: env-fabric）。** Fabric 在
  Held Request Read 的 wire projection 边界输出 `sha256:<hex>`，并用实际
  held bytes 重算校验；内部 hold digest / `agentOperationDigest` 语义未变。
  真实 Fabric handler → 真实 Provider reader 的 HTTP joined gate PASS
  （Provider 独立重算 digest 成功，owner result schema 直接校验通过）。
- **UDM Subscribe 已进入正常 Skill 执行链。** 新增
  `ca.session.udm_hold.bind` + `createdsession.udm.hold_bound`，只按 UDM
  Hold 实际字段（path SUPI、body DNN/S-NSSAI）匹配，不要求 PDU Session 或
  policy association；`sbi.udm.sdm_subscription.create` 从 bind 输出取
  `waiterRef`（仅 Runtime 控制上下文），在 Agent OperationRef/TransactionRef/
  commitment 确定后 claim，并以完全相同关联字段 dispatch。
- **PCF Governance 部分可用、总体仍 UNKNOWN。** Fabric 新增只读短时治理投影
  （hold / Agent authorization / competing create `NOT_FORWARDED`），Demo
  ObservationSource 已消费；但 `lifecycleIsolationState=CLEAN` 仍缺
  `env-open5gs`/Sandbox owner 声明与 evidence ref，因此 Predicate 保持
  UNKNOWN、PCF Create 保持阻塞。不得从 hold 存在推断 isolation。
- 本地门禁 `UV_FROZEN=1 make verify` 1361 passed / 1 skipped；证据见
  [P6.1 记录](../../artifacts/reviews/20261102-createdsession-p6a-hold-completion/README.md)。
  真实 Fabric lane 仍被并发实验占用，`LIVE_NOT_RUN`；无 201/ResourceRef/原始
  SMF waiter 的 live 证据。

**P6.2（2026-11-02，分支 `codex/createdsession-p6b-pcf-isolation`，基线 `codex/createdsession-p6a-hold-completion@c976bcb`）：**

- **lifecycle isolation 不再缺少 owner source，但不是新平台。** env-fabric
  新增 run-scoped operator 声明
  `createdsession-lifecycle-isolation/v0alpha1`（私有文件 + operator SHA-256
  pin）。Fabric 用自身实际部署与 held request 逐字段核对（lane 地址、上游
  SCP、SMF 地址分类与真实来源地址、SMF 自己声明的 PCF target），并要求只
  允许一个 `AGENT_BOUND_CALL` 发送者、`ungovernedSendPaths` 为空、证据在
  ≤24h 有效窗口内。任一不符继续 `UNKNOWN` 并给出稳定 reason；只有全部满足才
  投影 `CLEAN` + name 的 `lifecycleIsolationEvidenceRef`。
- **Demo 侧消费同一投影，未新增判断。** Observation 现在把 owner schema
  `$id` 与其真实 digest 写入 `schema_ref`/`schema_digest`（此前 digest 为空），
  vendored 副本 `734748a8…` 由单测与 `$id` 共同钉住。
- **Joined 证据（真实 handler → 真实 Demo consumer over HTTP）**：
  匹配声明 → `CLEAN` → Predicate `PASS`；无声明 → `UNKNOWN`；已转发 →
  Predicate `FAIL`。治理 read 不 claim、不 dispatch（hold 仍 PENDING，SCP 调用 0）。
- **仍不是 live PASS。** 真实 Fabric lane 仍被 PID 2871767 占用，未抢占/未重启，
  未签发任何真实 `CLEAN`，`LIVE_NOT_RUN`。证据见
  [P6.2 记录](../../artifacts/reviews/20261102-createdsession-p6b-pcf-isolation/README.md)。

**P7（2026-11-02，分支 `codex/createdsession-p7-n4-observation`，基线 `codex/createdsession-p6b-pcf-isolation@2e8c2f9`）：**

- **Pre-N4 基线成为 PCF Create 的硬前置。** 新增
  `createdsession.n4.baseline_clear`：在 `npcf-sm-policy-control-create` 的
  Pre-N4 inputs 之后、create mutation 之前，用真实 SMF 只读读取出
  `createdsession.n4_baseline`。只有**完整分页、精确 SUPI/PSI、且没有当前 N4
  SEID pair** 的 SMF 结果才投影 `NO_N4_PAIR`；已存在 pair 投影
  `EXISTING_PAIR` 并拒绝本次新会话关联。读取失败、歧义或不完整一律 `UNKNOWN`，
  绝不把 `UNAVAILABLE` 当 absence。
- **Post-N4 ObservationSource 已实现。**
  `createdsession.n4_initial_resources` 现在消费 Provider 新增的
  `n4.initial_resources.snapshot` 只读投影：精确 SUPI/PSI、当前
  `open5gs-session:<N4 pair>`、SMF/UPF source digest、唯一 pair match count、
  `defaultFlowInstalled`、`uplinkEndpointBound`、`observedAt` 与稳定
  reasonCode。Provider 仍持有 SEID join；Demo 不接收原始 SEID、Subscriber 数据
  或整份 UPF session。
- **Baseline 与 Post 的关联。** `pcfPolicyAssociationRef` 只标识 Pre-N4
  create attempt 与 Lifecycle，不作为 N4 实例。Post 读取要求同一
  ue/psi/pti/requestType/ingress/lifecycle selector、同一 baseline、PCF
  association 已 COMMITTED、baseline 在 create 之前且未过期；新 pair 不得来自
  baseline，同一 Lifecycle 内重复读取必须保持同一已确认实例，pair 变化返回
  `UNKNOWN`。
- **N4 Wait 的 `KNOWN_ABSENT` 修复。** 已证明“尚无 N4 pair”对 initial
  establishment 是继续有界等待，不再被当成 SUCCEEDED；其他等待仍按声明的
  权威 negative fact 语义处理。Wait 的观察 ref、freshness、scope 与 absence
  策略均来自已准入 Procedure/Predicate 声明，仍使用既有 deadline、
  observation budget 与 cancel。
- **HTTP Joined（本地，非 live）。** Provider 真实 handler + 真实 Open5GS
  SMF/UPF reader（测试源）→ Demo 真实 `ProviderObservationClient` +
  N4 sources + `PredicateEngine`：baseline `NO_N4_PAIR` → 新唯一 pair →
  Predicate `PASS`；SMF pair 但 UPF pair 缺失 → `UNKNOWN`。证据见
  [P7 记录](../../artifacts/reviews/20261102-createdsession-p7-n4-observation/README.md)。
- **仍不是 live PASS。** 未占用真实 Fabric SBI lane，未执行真实 PCF Live
  create，未重编译或修改 Open5GS。真实 RAN/N4/UE 最终事实仍为后续接点。

**P8（2026-11-02，分支 `codex/createdsession-p8-harness-lane-ownership`，基线
`codex/createdsession-p7-n4-observation@6e48e88`）：**

- **Harness 进程归属收敛。** `scripts/run-createdsession-provider-live-e2e.py`
  不再按二进制名扫描并终止进程。每个 run 目录有稳定 `runId`，子进程带
  `CA_CREATEDSESSION_RUN_ID` / `CA_CREATEDSESSION_RUN_DIR`，停止前核对
  PID + start-time + executable + runId + argv 指向的本 run 目录；任一不满足
  就不发送信号。原 `stop_by_binary` 已删除。
- **共享 listener 只读判定。** 启动前通过 `/proc/net/tcp{,6}` → socket inode →
  `/proc/*/fd` 确定 `10.30.30.1:7777`（SMF 唯一 SBI 出口）、`127.0.0.1:9443`、
  `:7788`、`:9444`、`:18080` 的 owner。非本 run 拥有时报
  `LIVE_LANE_OWNED_BY_ANOTHER_RUN`，不 kill、不重启、不清理其他运行目录。
  新增只读 `lane-status` 子命令。
- **本轮现场。** 共享 SBI ingress 仍由另一实验（PID 2871767
  `env-fabric-dispatch-live`，其本地运行目录属于该实验）持有；Provider PID
  2871776 同理。因此真实 Resident Host、UDM/PCF/N4/Prepare/C Transfer 与 UE
  数据面全部 **NOT_RUN**，分类 `LIVE_LANE_OWNED_BY_ANOTHER_RUN`。
- **`/pdu-info` 导出能力已核实。** 部署中的 SMF/UPF 二进制确实包含
  `smf_n4_seid` / `upf_n4_seid` 导出（overlay `0001-smf-pdu-info-export-n4-seids.patch`），
  因此缺 `upf_n4_seid` 只按 context inactive 解释，不据此声称 `NO_N4_PAIR`。
- **证据。** [P8 记录](../../artifacts/reviews/20261102-createdsession-p8-live-lane-ownership/README.md)。

**P8-A2（2026-11-03，分支 `codex/createdsession-p8a2-core-network-observations`，
基线 `codex/createdsession-p8a1-resident-forward@0ab7b3a`、Provider
`codex/createdsession-p7-n4-observation@b5b0d59`）：**

- **业务完成标准收敛到核心网事实。** CreatedSession 的后期成功条件只有两个
  核心网事实：SMF 已采纳本次会话的 RAN/N2 资源；SMF/UPF 已为同一 N4 Session
  配置有效的下行转发资源。UE 内部状态（NAS PS-ACTIVE、TUN、Ping）不是
  Agent 可观测的业务事实，本轮从 Skill 成功条件中**删除**：
  `createdsession.ue.configuration_accepted` Predicate、
  `await-ue-session-configuration` 子过程、`ue-configuration` wait purpose、
  contract postcondition 与全部 Case/测试引用都已移除。没有新增任何返回固定
  PASS 的 Predicate，也没有用 UERANSIM/Manifest/Ping 代替核心网观测。
- **RAN 采纳的权威来源是 SMF owner 投影。** `smf.ran_setup.snapshot` 复用
  `SMFContextReader`，要求精确 SUPI/PSI、当前 N4 pair、SMF 报告的
  `n3.gnb` 地址+非零 TEID、可识别的 required QFI、`pdu_state=active`，并做
  前后两次读的一致性确认。`n3.gnb` 在 pinned Open5GS 中只由
  `src/smf/ngap-handler.c:ngap_handle_pdu_session_resource_setup_response_transfer()`
  从 NGAP `PDU_RES_SETUP_RSP` 写入 `smf_sess_t.remote_dl_ip/remote_dl_teid`，
  且写入发生在 `num_of_qos_flow_modified > 0` 之后；`pdu_state` 单独**不能**
  作为采纳证据（它在 N2 响应前是 `inactive`，且其他 N3 状态也会让它变 active）。
- **未使用 Fabric N2 Source Store。** Fabric 的
  `ExtractSetupResponseTransfer` / `updateSMContextSourceStore` 自述
  “source authentication、持久化/读取访问、operation/session-generation 关联
  仍未解决，SourceRecord 分类不是 owner 身份证明”，且是 opt-in 加密本地
  journal、没有只读查询接口。SMF owner 投影已能严格证明采纳，因此不引入
  第二个 N2 事件平台，也不把未鉴权字节当成身份证据。
- **N4 Forwarding 单独观测。** `n4.forwarding_resources.snapshot` 用同一 SMF
  fact 做 UPF join，要求唯一 N4 pair、SMF 快照前后一致，并要求：默认 QFI 的
  下行 PDR（`src_if=Core`，经共享 QER 取得 QFI）→ FAR（`dst_if=Access`）带
  PFCP FORW bit，且 FAR 的 Outer Header Creation 的 TEID 与地址等于 SMF 的
  gNB N3 端点；QER 上下行 Gate 都开放。**“FAR 存在”不等于“下行隧道就绪”**：
  pinned SMF 在 N2 响应前把下行 FAR 建成 `BUFF|NOCP` 且没有 outer header
  creation。
- **UPF overlay 最小只读新增。** `env-open5gs`
  `0002-upf-session-info.patch` 在 `far[]` 增加可选
  `outerHeaderCreation{gtpu4,gtpu6,teid,addr4,addr6}`，纯拷贝
  `far->outer_header_creation`；不新增端口/服务，不导出 UE 数据或 PFCP 原文。
  未改 pristine upstream；series identity 变为
  `69296cc8d8e36f34bb66e4c7be91408b3489997f835e69ca786e7f359c468aac`。
- **`bindingStatus` 与 PDU 活动解耦。** 审计发现 `pdu_state` 在 N2 响应前恒为
  `inactive`（`remote_ul_teid`/`remote_dl_teid` 都为 0），原 P7 把
  `bindingStatus=STALE` 绑到 `pdu_state`，会使 initial N4 gate 在 RAN 响应前
  永远无法通过。现 `bindingStatus` 只表达“精确 pair + 快照已确认”，PDU 活动
  由 `smfPduState` 单独上报。
- **Lifecycle 绑定。** RAN 观测要求 P7 initial N4 读在该时刻**没有** SMF 采纳的
  RAN 端点（`smfRanEndpointPresent=false`），且 Post-N4 实例等于 P7 已确认实例；
  因此旧会话、上次实验或复用 pair 都不能造成 PASS。证据不足一律 `UNKNOWN`，
  绝不把“暂时读不到”当成“拒绝”。
- **Resident 装配。** `createdsession.ran_setup_result` 与
  `createdsession.n4_forwarding_resources` 现在是 Host 内部注册的
  Provider-backed owner（`INTERNAL_OBSERVATION_REFS`），不再要求外部注入；
  `externalObservationRefs` 因此为空。P7 N4 initial source 与 P8-A1 PCF
  governance source 保留；重复注入内部 owner 仍被拒绝；`check_coverage()`
  未删除、未绕过。
- **门禁。** Demo `UV_FROZEN=1 make verify`、docs validator；Provider
  build/test/race/vet/tidy 与两条 HTTP Joined；env-open5gs pinned SHA 校验、
  patch 应用、native build、projection 与 Provider-contract tests。真实 5GC
  live 仍未执行。证据见
  [P8-A2 记录](../../artifacts/reviews/20261103-createdsession-p8a2-core-network-observations/README.md)。

**P8-D1（2026-11-03，分支 `codex/createdsession-p8d1-n1n2-hold-association`，
基线 `codex/createdsession-p8c2-full-live-e2e@369cf32`）：**

- **缺口补齐，业务节点未扩张。** 只改 `namf-communication-n1n2-message-transfer`：
  新增 `ca.session.n1n2_hold.bind`（READ，不 claim/不发送）+
  `createdsession.n1n2_hold` Observation +
  `createdsession.n1n2.hold_bound` Predicate，并把 bind 放在 Prepare 之后
  （避免短 hold budget 被 Prepare 消耗）；transfer 增加 `waiterRef` binding。
- **Claim 属于 transfer mutation 的原子授权边界。** 迁移后的顺序是
  读取已绑定 hold → 校验 Prepare artifact/context 与 PDU Session →
  生成确定性 operationRef/transactionRef 与 `n1n2_operation_association_digest()` →
  `register_operation` + 持久化 commitment（含首次 deadline）→ claim →
  以同一 `waiterRef`/`agentOperationDigest` 调 Provider C transfer。
  `n1n2_operation_association_digest()` 绑定 operation、operationRef、transactionRef、
  environment、subject、lifecycle、operationContextRef、artifactRef/Digest、
  N1/N2 instance、target 与 holdRef；它不是原始 SMF held-request digest。
- **三种身份严格分开。** Fabric `N1N2InstanceRef(SUPI, PSI)` =
  `pdu-session:<supi>:psi-<1..15>`；Provider `currentSessionInstanceRef` 是
  N4/artifact 资源实例；Agent commitment 是自己的操作承诺。Fabric gate 用前者
  校验 Provider association，Agent 不解码 NAS/NGAP/multipart。
- **AMF target 必须来自 operator 声明。** 部署新增必填
  `amfTarget.origin`；Bind 要求 hold scope 的 `target-apiroot:<origin>` 与之完全相等。
  未声明 target 的部署（v0.3 legacy 也带该字段）在 Bind 前 fail closed。
- **失败语义。** Bind 失败/过期：不 claim、不发送；commitment 不能持久化：不 claim；
  claim 明确拒绝：不发送；claim 超时/未知：`OUTCOME_UNKNOWN`，保留责任且不自动重试；
  Provider 失败：由 Provider journal/lookup 分类；同 operationRef 重投复用本地 claim 与
  持久 commitment（同一 deadline），Fabric/Provider journal 不二次发送；
  同一 hold 换 operationRef/commitment 被拒绝。
- **Resident 装配与 Coverage。** Host 内部新增 N1/N2 Hold Store、Bind backend、
  ObservationSource 与 Transfer claim 依赖；coverage 由 authored 源派生
  （实测 12 operations / 18 observations；原写 19 为笔误，`missingObservations=[]`），
  重复注册仍拒绝；`amfTarget` 纳入 profile digest。
- **证据层级。** 组件测试 + `LOCAL_HTTP_CONTRACT_JOINED`（真实 Demo client/Runtime
  over sockets，Fabric/Provider 为逐字段转录的本地双替身）；
  真实 Fabric handler 的 C transfer/单发送者 joined gate 只读执行
  （env-fabric `TestCreatedSessionCTransferJoinedAuthorizationAndDelivery`）。
  **不是 live 5GC，`LIVE_NOT_RUN`；真实 UE/AMF/RAN/N4 未执行。**
  完整记录见 [P8-D1 记录](../../artifacts/reviews/20261103-createdsession-p8d1-n1n2-hold-association/README.md)。

### P8-D2 真实 live 结果（2026-11-04）

在 pinned env-fabric `2e11c93` + ca-provider-5gc `fce0fd9` + P8-A2 Overlay 上做了
两次真实 UE 请求（第二次在 Demo 修复后）：

- **已真实通过：** UDM Hold/Claim/真实响应交付、PCF Create 真实 201 + Location +
  原 SMF waiter delivery、Initial N4、Provider Prepare、`ca.session.n1n2_hold.bind`
  + `createdsession.n1n2.hold_bound`、Agent commitment 先于 claim 持久化、
  Fabric 真实 `grantRef`、Provider C Transfer 带同一 association、Fabric 单发送者
  reservation、**N1/N2 只发一次且真实 AMF 收到**、真实 AMF 响应写回原 SMF waiter。
- **第一个外部阻塞：** Open5GS 2.8.0 AMF 以 `400 / No N1 SM Content` 拒绝消息。
  env-fabric `internal/createdsessiontransfer/processor.go::buildN1N2Multipart`
  把 part 头写成 `Content-Id: <5GNASMessage>`，而 pinned Open5GS
  `lib/sbi/message.c::ogs_sbi_find_part_by_content_id` 按原始头值 `strcmp`，
  不剥离角括号。**owner = env-fabric（本轮只读，无修改授权）**。
- **Demo 侧缺陷（已修）：** 第 1 次 attempt 的 Fabric C profile
  `requester.nfIdentityBindingRef` 与 Provider intent 的
  `providerNfIdentityBindingRef` 由同一 harness 用两个字面量生成，Fabric 在
  reservation 前拒绝（`NOT_SENT`）；已改为单一共享常量并加 profile 对齐单测。
  另一个 Demo 缺陷：`cause: null` 使 `transfer-start-evaluation-input` schema
  校验失败，把确定的 AMF 4xx 降级为 UNKNOWN；schema 已接受 `string | null`，
  但该分类修复**未**在第三次真实尝试中复验。
- **未达成：** `N1N2_C_TRANSFER_LIVE_PASS`、`CREATEDSESSION_CORE_NETWORK_LIVE_PASS`；
  RAN Adoption / N4 Forwarding / 成功 Resource Finalize 均 **NOT_RUN**。
  完整证据见 [P8-D2 记录](../../artifacts/reviews/20261104-createdsession-p8d2-n1n2-live-e2e/README.md)。

### P8-D4 真实 live 最终结果（2026-11-04）

在 P8-D3 修复后的 env-fabric `8eeba8c` + ca-provider-5gc `fce0fd9` + P8-A2 Overlay 上
做了两次真实 UE 请求（各自独立 runId / lifecycleRef / runDir / journal）：

- **AMF 接受 N1/N2（PASS）：** Fabric 真实发出 `Content-Id: 5GNASMessage` /
  `N2SmInformation`（JSON `contentId` 与 MIME 头同源、无角括号），SCP 逐字节转发，
  真实 AMF 返回 **200 + `{"cause":"N1_N2_TRANSFER_INITIATED"}`**，日志中
  `No N1 SM Content` 为 0；N1/N2 仍 **只发送一次**，单发送者 1 条 grant，
  原 SMF waiter 收到同一真实 200 并继续（AMF → SMF `sm-contexts/1/modify`）。
- **Demo 侧缺陷（已修）：** 第 1 次尝试在 AMF 接受后把 RAN Adoption 误判为
  `UNRESOLVED`（`WAIT_BUDGET_EXHAUSTED`，3 次观测共用 0.37 ms）。根因是
  Post-N4 的 `ca.session.evidence.await` 只带 operation-context 句柄，而 SMF owner
  要求本 attempt 的 `ueRef/pduSessionId/pti/requestType/ingressRef`；修复为
  “Post-N4 等待必须携带 attempt selector（缺失 fail closed）”+ 业务 YAML 传入
  selector + 部署侧 0.25 s backoff 与 64 观测预算，并新增 3 个回归。
- **最终结果：** 第 2 次真实请求在同一次 Skill 执行中
  `createdsession.ran.setup_accepted` / `createdsession.n4.forwarding_ready` /
  `createdsession.resources.managed` 全部 **PASS**，Runtime 终态 `SUCCEEDED`，
  `CREATEDSESSION_CORE_NETWORK_LIVE_PASS`。UE `PS-ACTIVE` 仅作补充事实，
  不要求 TUN/Ping。完整证据见
  [P8-D4 记录](../../artifacts/reviews/20261104-createdsession-p8d4-final-live-e2e/README.md)。

## 4. 待解问题：先看业务时序，再决定代码

**已补充真实 Open5GS 2.8.0 源码审查：** [CreatedSession × Open5GS 真实执行依赖核对](createdsession-open5gs-v280-execution-dependencies.md)。原生时序已确认：
`UDM Get → SMF 本地地址分配 → UDM Subscribe → AMF CreateSMContext 201 → PCF Create → PFCP Establishment → SMF 原生 N1N2 Transfer → AMF N2 结果/必要时 PFCP Modification`。
**没有“PCF 之后才分配 UE 地址”的原生环形依赖**；真正待闭合的是**已选 Fabric → SMF 响应交付在真实环境中的精确接点和可消费性**、同一 PCF session/callback 归属冲突以及原 SMF 的竞争 N1N2。该核对为源码证据，不是 Fabric 路由已接通或 live B/C PASS。


1. **原始 CreateSMContext：** 是否在目标部署确实被送达原 SMF，Agent 是否同时得到同源触发？必须确认一次原 HTTP 响应归属及不同路径的异常行为。
2. **已选 Fabric → SMF 交付链：** 对 UDM Get、Subscribe、PCF Create 逐操作检查 SMF 原 waiter、Agent 真实请求/响应、当前会话/尝试、SO 与 NF 资源/callback 语义，明确 Fabric 如何安全交付而不重复执行 NF 创建；再核实 SMF 地址分配、PCF 消费与 N4。**方案已选定，接点未实测**；不能凭 SUPI/PSI 直接把 Agent HTTP response 冒充 SMF 原事务。独立 UDM Get 双读不应被擅自替换为新主路线。
**B 资源与原生 SMF N4 的操作级收敛设计：** [Sandbox B §7.2：当前会话绑定、Provider callback、SMF 通知和释放兼容](https://github.com/odango-chan/sandbox/blob/main/docs/design/createdsession-resource-lifecycle.md)。这是既有“Agent-owned 资源、Fabric 兼容交付、原 SMF 执行全部 PFCP”路线的细化，**不是已接线或 live PASS**。弱模型不得因为此设计新建 callback 服务、PFCP 工具或全局 identity/ownership 数据库。

**旧 callback finding 已修复于 Provider main**：[`callbackDeliveryPath`](https://github.com/odango-chan/ca-provider-5gc/blob/0f1c451537e133ab3cd2cf00c0a0b4456b4f6124/internal/providerapi/createdsession_callbacks.go) 接受 token 本身与 token 后固定 `/update`，拒绝其他嵌套 suffix；#44 已合并。当前 pinned PCF producer 的实际 URI 是 `notificationUri/update`。不把 `/terminate` 当成必须同时增加的路径，不重建 callback 平台。剩余验收是实际 producer 的投递、持久化、当前 association 绑定和 SMF 消费；代码支持 URI 不等于这些接点已经 live 通过。

Fabric 关联需要：同次 AMF CreateSMContext source 和 SMF 201 Location（**当前 SMF instance + smContextRef + lifecycle**）绑定到 Agent PCF Create 的真实 201 Location / Provider callbackBindingRef/resourceRef。Open5GS smContextRef 是 session pool index，不是永久全局 ID；不得按 SUPI/PSI、相似 URI 或相近时间推断关联。NF callback 204、Fabric 的原 SMF 事件投递、SMF QoS 处理、N4/UPF 完成分别留证。

原 SMF 的 [`smf_sbi_cleanup_session`](https://github.com/odango-chan/env-open5gs/blob/main/upstream/open5gs/src/smf/sbi-path.c#L852-L935) 会发 PCF Delete / UDM Unsubscribe 等请求以推进释放状态机。Fabric **不能一律 503 阻断，也不能放行重复删除 Agent-owned 资源**：须将获准 Agent 资源清理的真实 NF 结果按原 SMF waiter 精确兼容交付；无法安全做到则标记 release BLOCKED，不制造 204 或 TerminateNotify 来绕过。初始 Establishment E2E 与后续 Update/Release 独立分阶段验收，后者不应先于前者成为全面施工前提。

3. **PCF Create 前置、创建后归属及通知兼容：** 创建前验证授权、实例、冲突/副作用归属；创建后验证真实 association、Agent-owned callback/持续管理，以及 `association → 当前 SMF smContextRef` 的可信绑定。原 SMF 对当前 pinned Open5GS SM-policy UpdateNotify 的消费能力，及任何其他实际 producer 所发事件的消费能力，均须按本次生命周期分别验证；不能由 `201` 或 callback `204` 推断 N4 成功。当前 `EXCLUSIVE` 缺真实 owner 证明；不要为了通过测试改成 true 或弱化安全门槛。
4. **AMF transfer：** 上下文 READ 不建立发送预留；Provider 在 mutation 内的预留解决自身重放，不能证明原 SMF 未发送。先明确 Fabric 逐操作处置，再校准 Demo 前置检查和实际动作时序。
5. **N2/RAN/N4/UE：** 先打通 owner 原始事件及当前会话实例的真实关联，再接入 Demo Predicate；不把可解码消息或已登记 ref 当作 RAN/N4/UE 完成证据。

缺真实环境、现有 owner 接口或正确身份关联时，只报告对应 BLOCKED/UNKNOWN，不生成凭空接口，也不将这些 blocker 转成通用 PKI、TLS、Toolchain 或 Runtime 建设任务。

### 4.1 跨层矛盾处理规则（不是新增架构）

当 Sandbox 已确定的业务责任、Demo 当前 Skill 前置/后置条件、Provider/Fabric
真实 owner 接口或运行证据不一致时，**先判断要求的事实是否在该操作之前就有可能成立**，
再判断来源、执行时序与责任 owner；不得默认“上层 Predicate 写了，就必须继续扩建
下层基础设施直到它变成 true”。

1. **架构职责不因实现困难自动变更**；具体 Skill 表达式可以在专项设计审查后
   调整，以正确区分业务前置许可、mutation 副作用及创建后的独立事实。
2. **已有 owner 明确返回的 false / UNKNOWN / UNAVAILABLE 不能被 Demo、
   fixture 或缺证据的身份标签覆写为 true**。缺失真实来源或安全关联的，
   只阻塞对应操作/验收；不得为了消除阻塞发明新 TLS/PKI、
   全局 reservation、通用可信数据库或第二套 Runtime。
3. **PCF 例子**：`procedure.yaml` 在 UDM Subscribe 前验证
   `createdsession.policy_context.ready`，而 `predicates.yaml`
   目前要求 `associationOwnership == "EXCLUSIVE"`；
   Provider #39 对未证明的归属正确保持
   `PCF_ASSOCIATION_OWNERSHIP_UNVERIFIED`。须核对“创建前无冲突且有权发起”
   与“创建后 association 归属”的不同时间语义，评审是否要改 Skill
   时序/校验要求；#134 的 create-inputs 与 governance 分离已由 PR #137 整合到工作分支。
   **2026-11-03 P8-C2 live 更新**：真实 PCF create 已 PASS（真实 PCF 201 +
   `Location /sm-policies/13`、原 SMF waiter delivery、SMF 消费后继续 Initial N4），
   见 [P8-C2 记录](../../artifacts/reviews/20261103-createdsession-p8c2-full-live-e2e/README.md)。
   **不能提前制造 EXCLUSIVE 或取消安全检查**。
4. **Transfer 例子**：`procedure.yaml` 在
   `sbi.amf.n1n2.transfer` 前验证 `createdsession.delivery_context.ready`（该 Predicate 已是纯输入事实，
   不再要求 `uniqueSenderReserved`）。**2026-11-03 P8-C2 live 阻塞**：
   Skill 的 transfer 节点只绑定 `operationContextRef`/`runtimeInvocationRef`/
   `lifecycleRef`/`responseArtifactRef`，而 `runtime/createdsession_transfer_backend.py`
   只消费调用方给出的 `waiterRef` + `agentOperationDigest` 且明确不自行派生；
   仓库中不存在 N1/N2 hold bind/claim 操作，于是 Fabric 在任何 reservation/dispatch
   之前按 `N1N2_ASSOCIATION_REQUIRED` 拒绝，effect 为 `NOT_SENT`。
   **2026-11-03 P8-D1 修正（本分支）**：新增 `ca.session.n1n2_hold.bind`（READ）、
   `createdsession.n1n2_hold` / `createdsession.n1n2.hold_bound`，并在
   `sbi.amf.n1n2.transfer` mutation 内生成 operation identity 与
   `n1n2_operation_association_digest()` commitment、先持久化再 claim、最后以同一
   association 调用 Provider。业务 YAML 只在 `namf-communication-n1n2-message-transfer`
   节点增加 Bind 与 Predicate，并给 transfer 增加 `waiterRef` binding；UDM/PCF/N4/RAN 语义未变。
   真实 E2E 仍未重启（`LIVE_NOT_RUN`），本轮证据为组件与本地 HTTP joined。
   **不能把 Provider 内部幂等预留当作全局唯一发送证明**。
5. 如实记录所采用的语义修正、受影响的实际源与测试，必须由**单独限定范围的
   实施任务**授权修改业务 YAML / owner 代码；这份文档不实施这些修改，
   也不自动扩大跨仓写权限。

### 4.2 D3 真实接点与外部 Observation owner

D3 的工作单元按实际执行依赖排序；可独立验证的操作不必等待所有 owner 同时齐备，但任何依赖缺失都必须只阻塞相应步骤，不得伪造事实。

1. **真实 Fabric ingress/disposition**：D3-A1 consumer 已按 producer 已验收代码适配 flat Agent message v0.1：`GET /v1/network-intents/next` 返回只含 11 个业务成员的 body，action identity 与 revision 只走 `X-Env-Fabric-Action-Ref` / `X-Env-Fabric-Action-Revision` 响应头，两条 control 路由共用私有 bearer token，`/n1-sm` 与 NetworkIntentV2 均已删除。本仓 L1 mechanism 与 L2 Fake Integration 有本地证据；真实 Fabric + Demo joined 与真实 ingress/reject 仍为 `NOT_RUN`，不得读成本轮 PASS。接口映射见 [Fabric HELD Ingress 接口](createdsession-fabric-ingress-interface.md)。
2. **Provider operation dispatch（复用既有通信与信任路径）**：逐操作验证 UDM Get、UDM Subscribe、PCF Create、AMF N1/N2 Transfer 的真实 endpoint/profile、请求与响应关联、operationRef、mutation certainty 和资源责任。不得把 mTLS 设为通用 SBI 前置条件，也不新建 CA/PKI/证书体系；按具体既有接口契约使用其现有信任机制。五类 Demo → Provider adapter 已按 Provider HTTP-only 契约迁移为固定白名单 `http://`，不再携带证书材料；Provider 侧调用方准入由 `runtimeCallerCidrs` 承担，业务身份和 fail-closed 检查保持不变。UDM Get 的 2026-10-27 A-only 历史实测只是受限切片，不代表当前 D2 Resident 链路或 B/C 已通过。
3. **Fabric → 原 SMF waiter 响应交付（贯穿验证）**：对会影响原生 SMF 继续推进的每个 Agent 主动 SBI 操作，逐个证明真实 NF 响应与原 SMF waiter、当前 SMF instance、`smContextRef`、lifecycle/operation 的精确关联，以及唯一响应 owner。此机制是完整真实 E2E 的必要条件；不能等到所有 Agent 操作结束后再笼统验收，也不能把 Agent 收到 200/201 当作 SMF 已消费。
4. **按 Skill 时序接入四个 owner-native Observation**（P8-A2 起 UE 观测已删除）：配置中出现 ref 或 Host READY 不代表 owner 已提供事实。每个 owner 必须从真实权威来源产生带当前实例/请求关联的 Observation，并由 Predicate 按下表验证。

| External Observation ref | Skill 使用阶段 | 必须提供的权威事实（按当前 Predicate） |
| --- | --- | --- |
| `createdsession.pcf_create_governance` | **PCF Create 之前**的治理前置条件 `createdsession.pcf.create_governed` | 当前 lifecycle isolation 为 `CLEAN` 并有 evidence ref；原 SMF competing Create 为 `NOT_FORWARDED` 并有治理 ref。不能从 PCF inputs readiness 或 Provider 自身幂等预留推断。 |
| `createdsession.n4_initial_resources` | PCF Create 后，等待初始 N4 session establishment | 当前 session-instance 通过本次 await 的精确 sessionInstanceRef/lifecycleRef 关联；Predicate 要求 default flow 已安装、uplink endpoint 已绑定且 bindingStatus 为 `CURRENT`。Agent 不执行 PFCP/N4。 |
| `createdsession.ran_setup_result` | Agent 发起 AMF N1/N2 transfer 后，等待 SMF 采纳 RAN 资源 | Provider `smf.ran_setup.snapshot`：精确 SUPI/PSI、当前 N4 pair、SMF `n3.gnb` 地址+非零 TEID、required QFI 可识别、`pdu_state=active`、快照前后一致；结果为 `ACCEPTED`、required flow 匹配、current instance 绑定。 |
| `createdsession.n4_forwarding_resources` | 原生 SMF 完成所需 N4 forwarding convergence 后 | Provider `n4.forwarding_resources.snapshot`：同一 N4 pair、下行 PDR（Core，经 QER 取得 QFI）→ FAR（Access）带 FORW、FAR Outer Header Creation == SMF gNB 端点、QER 上下行 gate 开放。 |
| ~~`createdsession.ue_sm_configuration`~~ | **已删除**（P8-A2） | UE 内部状态不是 Agent 可观测的业务事实，不再是 Skill 成功条件；替代判定由 SMF 采纳的 RAN 资源与 SMF/UPF 下行转发事实承担，而不是把 `ue.configuration_accepted` 改义。 |

5. **完整 E2E 验收**：在真实 Open5GS/SMF、SCP、Fabric、Provider、AMF/gNB/RAN、UPF/N4 和 UERANSIM/UE 环境中，按当前 authored Procedure 完成流程；分别留存 Agent Procedure outcome、Fabric waiter delivery/SMF consumption、四类 owner-native facts、资源责任和核心网侧会话结果（SMF 采纳的 RAN/N2 与 SMF/UPF 下行转发；不声称 UE 本地状态或数据面 Ping）。当前这些 live 证据尚未齐备，完整 E2E 为 `NOT_RUN`，不得标记 PASS。

当前外部状态应按层报告：Demo mechanism/local tests 已通过；Fake Fabric/Provider protocol integration 已通过；真实 Fabric HELD ingress/source/reject、Provider operation dispatch、Observation owner 的生产来源、Fabric→SMF waiter 成功响应交付及真实 RAN/N4 事实仍为 `EXTERNAL BLOCKED` / `NOT_RUN`。五类 adapter 已完成 HTTP-only 迁移；Provider HTTP-only 收尾合并前不宣称三仓联合 PASS。

D3-A1 额外记录两项契约修正：(1) flat 消息的 `dnn` / `sst` / `sd` 在 producer 侧仍是 `omitempty`，Demo 按 wire 契约接受其缺席，并在材料化之前以 `required_pdu_request` 失败封闭，使该失败仍由唯一 disposition owner 对精确 action 投递 reject；(2) flat 消息不携带 action deadline，也没有 raw N1 source 读取，因此 journal 的 `deadline` 记录为缺失、`requestedPduSessionType` / `requestedSscMode` 只能来自可信 operator 部署资料（admitted operation-context selection，无默认值），本仓不再解码 NAS。

## 5. 后续工作的范围与验收边界

- **D2 安全机制保留、第二执行路径收编**：PR #138 已于 2026-11-04 合入；单实例锁、Journal、Mutation/Reject 互斥、身份绑定与安全 Shutdown 仍是必须保持的安全机制，但不再冻结为 CreatedSession 专属第二 Host。按 W0 统一 Host 任务包收敛。
- **下一研发目标是 D3 真实网络接点**，按 §4.2 的依赖顺序逐项验证；不以增加 Host 测试或生产化平台能力替代真实 Fabric/Provider/SMF/RAN/N4/UE 集成。
- **写权限仍按仓库隔离**：本仓文档/代码工作只限 `ca-agent-demo`；Provider、Fabric、Runtime、Sandbox 等 owner 仓默认只读。跨仓修改必须另行明确授权，不从依赖缺口推导写入权限。
- `ca-skills`、`ca-skill-toolchain`、`ca-runtime`、`ca-agent`、`sandbox` 不因 CreatedSession 缺口自动成为施工仓；纯 LLM 路线 A 与确定性路线 D 独立，A 继续保留但当前不优先。
- 真实执行必须分别记录 Agent SBI 结果、Fabric 对原 SMF waiter 的响应交付、SMF 消费、RAN/N4/UE owner-native 事实和资源责任。HTTP 200/201、Provider mutation COMMITTED、Observation ref 已注册或 Fake Integration PASS 均不能单独证明 PDU Session 建立成功。
- `CREATEDSESSION_RESIDENT_READY`/coverage 只表示必要 owner 已注册且覆盖门禁通过；真实性、当前实例及最终会话状态由运行时 Observation 独立裁决。**不注入虚假 owner source 让 READY 变绿**。
- 本文提供实施状态；[实施手册](../work/execution-routes/README.md) 提供 D3 工作单元、依赖顺序和停止条件。每次只执行一个获准目标，不形成无限制跨仓 Goal。

## 6. 历史入口

旧 D0–D7 checklist、PR #110 施工提示词、旧 authoring compatibility 结论和历史证明仍见：
`createdsession-runtime-implementation-plan.md`、
`createdsession-runtime-implementation-handoff.md`、
`createdsession-runtime-prerequisite-matrix.md`。
它们保留审计价值，但**其旧执行指令不再有效**。
