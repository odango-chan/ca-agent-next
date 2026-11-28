> 迁移来源：ca-agent-demo/docs/design/createdsession-skill-vnext.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：Create Session Skill 的后续设计  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；证据的当前有效性需按具体 main/PR/测试 SHA 单独核验。

---

# CreatedSession Skill vNext：authoring model 与业务流程

**状态：AUTHORING_SEMANTICS_FROZEN / DEMO_REFERENCE_IMPLEMENTED / LIVE_BC_UNVERIFIED（2026-10-29）**
**追踪：ca-agent-demo#89**
**authoring source：`skills/establish-pdu-session/assurance/procedure.yaml`**

本文记录 CreatedSession 的业务语义和 authoring 规则。它不是 Runtime 执行图，不能代替当前 `assurance/procedure.yaml`。

> **现行实施入口：** [CreatedSession 当前实施基准](createdsession-current-implementation-baseline.md)。
> 本文件中的业务语义继续有效；下文 §13–§15 的“等待 Toolchain lowering”
> 和“下一步修改 schema/runtime”属于**原设计阶段的历史实施建议**，
> **不是当前确定性 Demo 路线的开发命令或验收门槛**。
> Demo-local Procedure lowering、前/后置执行和 36 Cases 曾通过本地
> 参考验收；这不表示正式 Toolchain 已获得资格，更不表示 B/C 已真实贯通。
> 不能为了满足过时的 Toolchain TODO 修改现有 Skill，亦不能因真实
> owner 前置证据不足而伪造 Predicate PASS。

## 1. 设计目标

CreatedSession 处理一次已经准入并精确绑定的 UE-requested initial PDU Session Establishment occurrence。

authoring source 应让读者优先看到 3GPP 业务顺序，而不是 Runtime 为执行、核验和恢复展开出的节点。

核心分层：

- **main node**：有业务意义的外部操作、mutation、异步网络过程或恢复边界；
- **preconditions**：进入 main operation 前必须完成的有序准备；
- **postconditions**：main operation 成功后必须成立的事实；
- **Predicate**：当前 occurrence 下的事实，结果为 PASS / FAIL / UNKNOWN；
- **Contract**：Procedure 最终成功条件；
- **lowering**：由 Toolchain/Runtime 负责把 authoring source 展开成可执行图。

不维护第二份手写 execution graph。

## 2. 当前支持范围

第一版 profile 仅支持：

- local / non-roaming UE-requested establishment；
- Request Type = initial request；
- IPv4；
- SSC mode 1；
- 一个 default non-GBR flow；
- 不要求 secondary PDU Session authentication/authorization；
- 不要求 conditional SM Policy Association Modification。

如果 admitted request 需要 DN-AAA secondary authentication/authorization，当前 Skill 不适用。
如果 policy trigger 要求 SM Policy Association Modification，也必须显式增加业务分支，不能把 Create 当成 Modification 已经完成。

## 3. 3GPP 对齐原则

当前命名锚点为 3GPP TS 23.502 V18.14.0 (Release 18) clause 4.3.2.2.1 的 UE-requested PDU Session Establishment。

author-facing main flow：

1. `Nudm_SDM_Get`
2. `Nudm_SDM_Subscribe`
3. `Npcf_SMPolicyControl_Create`
4. N4 Session Establishment
5. `Namf_Communication_N1N2MessageTransfer`
6. PDU Session Resource Setup
7. N4 Session Modification / forwarding convergence
8. completion convergence + resource-responsibility finalization

对应关系：

| CreatedSession | 3GPP 锚点 | 当前实现边界 |
| --- | --- | --- |
| admitted ingress | CreateSMContext / admitted initial request | Root 进入前已经完成 occurrence binding |
| `nudm-sdm-get` / `nudm-sdm-subscribe` | subscription retrieval / subscription for updates | Agent 发起 SBI |
| secondary authentication | conditional PDU Session authentication/authorization | 当前 profile 不支持；需要时拒绝适用 |
| `npcf-sm-policy-control-create` | SM Policy Association Establishment | Agent 发起 SBI |
| conditional policy modification | SM Policy Association Modification | 当前 profile 不隐式实现 |
| N4 Session Establishment | N4 Session Establishment/Modification Request/Response | 临时 SMF 执行 PFCP；Agent 等待权威结果 |
| `namf-communication-n1n2-message-transfer` | `Namf_Communication_N1N2MessageTransfer` | Agent 发起 SBI |
| PDU Session Resource Setup | N2 request / AN resource setup / N2 response | Agent 等待当前 transfer 对应结果 |
| N4 Session Modification | post-RAN N4 modification | 临时 SMF 执行；Agent 等待 forwarding evidence |

临时 SMF 的 CreateSMContext/UpdateSMContext compatibility transaction 不是 Agent 的业务决策来源。

## 4. 三层配置

### 4.1 Requested Session Parameters

来自当前 admitted occurrence：

- DNN；
- S-NSSAI；
- PDU Session ID；
- PTI；
- Request Type；
- Requested PDU Session Type；
- Requested SSC mode；
- serving PLMN。

这些字段必须属于同一个 occurrence。缺失、冲突或来源不明不能用 subscription default 静默补齐。

### 4.2 Subscription-Constrained Selection

由当前 UE request 与 `Nudm_SDM_Get` 的可信结果确定。

它表达“subscription 允许什么”，包括 DNN/slice/session type/SSC 约束以及供 policy 使用的 subscription 数据。

它不是 PCF 最终授权结果，也不是最终实际配置。

### 4.3 Effective Session Configuration

在 policy 结果和真实资源/分配上下文可用后形成。

它表达“本次会话实际上要交付什么”，至少逻辑上包含：

- effective DNN / S-NSSAI / session type / SSC；
- policy-authorized QoS / AMBR；
- 实际 UE address；
- current default flow / QFI；
- 当前 N3/N4 资源绑定；
- PDU SESSION ESTABLISHMENT ACCEPT 与 N2 SM information 的确定性输入。

三层不能互相代替。

### 4.4 Shared preparation results

A result consumed only by its producing business node remains local preparation. When
later business nodes also consume it, the result is shared procedure data semantically,
even though the current syntax names the producer through
`<node>.preconditions.<step>.output`.

| Producer step | Shared meaning | Consumers |
| --- | --- | --- |
| `select-subscription-configuration` | Subscription-Constrained Selection | Policy-context preparation, PCF Create and AMF delivery preparation |
| `resolve-policy-operation-context` | Occurrence-bound policy/N4 operation context | UDM Subscribe, PCF Create and initial N4 convergence |
| `resolve-effective-session-configuration` | Effective Session Configuration context | Establishment-response preparation, AMF transfer, PDU Session Resource Setup, N4 forwarding convergence and UE configuration wait |

For now, keep the references explicit. Do not promote pure preparation to a business node
just to shorten the path; do not duplicate it for each consumer; and do not introduce
implicit global state or YAML anchors.

These producer paths are a current syntax limitation, not a statement that the data is
private to the producing node. A typed procedure-scope output/context contract should be
considered only if the same need recurs across multiple Skills. This revision does not
add that syntax.

## 5. Preconditions

`preconditions` 是 main operation 的有序 entry phase。

允许：

- deterministic local script；
- read-only `ca.*` context/evidence acquisition；
- Predicate `verify`；
- read-only / convergence child Procedure。

禁止：

- NF/SBI mutation；
- 任何需要 reconcile 的 side effect；
- 隐藏资源创建；
- 本身应该成为业务/recovery boundary 的动作。

执行规则：

| precondition step | success | explicit failure | unknown |
| --- | --- | --- | --- |
| script / read-only call | next step | FAILED / DENIED → block FAILED | UNKNOWN → block UNRESOLVED |
| verify | PASS → next step | FAIL → block FAILED | UNKNOWN → block UNRESOLVED |
| read-only child Procedure | SUCCEEDED → next step | FAILED → block FAILED | UNRESOLVED → block UNRESOLVED |

所有 preconditions 成功后才允许 dispatch main operation。

第一次资源 mutation 之前失败，直接 FAILED / UNRESOLVED；资源责任激活之后失败，必须先走 finalization。

### 5.1 JIT admission recheck

`createdsession.ingress.eligible` 在 Root applicability 处用于 admission，但还必须在第一次资源 mutation `Nudm_SDM_Subscribe` 之前重新校验。

原因是入口 admission 与实际 mutation 之间存在时间窗口；不能用“几秒前曾经 PASS”作为现在仍有 authority 的证明。

`createdsession.lifecycle.ready` 同样在第一次资源 mutation 前校验。

## 6. Postconditions

A main node uses a `postconditions` block when operation success alone does not prove
the business fact required to continue.

The block uses the same `steps + on` organization as preconditions, but only permits
ordered Predicate verification:

```yaml
postconditions:
  steps:
    - verify: createdsession.example.first_fact
    - verify: createdsession.example.second_fact
  on:
    PASS: next-stage
    FAIL: finalize-failed
    UNKNOWN: finalize-unresolved
```

The names above are illustrative. This example does not move facts from different
3GPP/business stages into one node. Each block contains only facts that belong to its
own main operation or convergence procedure.

Evaluation is ordered and fail-fast:

- each step may contain `verify` and optional `with` bindings only;
- PASS continues to the next step;
- the first FAIL immediately takes the block's FAIL route;
- the first UNKNOWN immediately takes the block's UNKNOWN route;
- the block's PASS route is taken only when every step passes.

The route belongs to the block, not to each step. Successful operation outcomes enter
the block automatically:

- READ/local compute `SUCCEEDED` enters postconditions;
- MUTATION `COMMITTED` enters postconditions;
- neither outcome may bypass the block.

Therefore:

```text
COMMITTED != Predicate PASS != Procedure SUCCEEDED
```

A normal conjunction of independent facts belongs in the block. Do not create a composite
Predicate solely because the authoring form previously allowed only one postcondition.
A composite Predicate remains appropriate when the combined fact itself has a distinct
business meaning.

Node-level postconditions govern local business progression. They do not replace the
independent final acceptance requirements in `SkillContract.spec.postconditions`.

The current CreatedSession nodes each keep the postcondition relevant to their own
operation; the new block shape supports multiple facts where they genuinely belong
together without merging RAN, N4, UE or resource-responsibility stages.

## 7. Evidence provenance

Predicate 不允许按 latest-per-UE / latest-per-session 取证。

当前规则：

- UDM Get → exact invocation + transaction receipt；
- AMF N1N2 transfer acknowledgement → exact transfer operationRef；
- RAN setup / N4 forwarding / UE configuration 的 evidence wait → exact transfer operationRef；
- 对应最终 Predicate → current lifecycle；
- resource responsibility → current lifecycle。

如果 producer identity、lifecycle identity、scope 或 evidence provenance 缺失/歧义，结果不能是 PASS。

新的 admitted recovery decision 不得静默继承上一次 invocation 的 producer-bound evidence。

## 8. 异步网络过程

真正的异步网络过程不能被一次 `verify` 替代。

当前保留 child Procedure：

- `await-initial-n4-session-establishment`；
- `await-pdu-session-resource-setup`；
- `await-n4-forwarding-convergence`；
- `await-ue-session-configuration`。

child Procedure 使用 `ca.session.evidence.await` 获取/等待当前 occurrence 的权威 evidence，再以 Predicate 判定最终事实。

初始 UNKNOWN 可能只是网络还未收敛；只有 governed wait 结束后才能决定 FAILED / UNRESOLVED。

UE configuration convergence 是 final success 的完成条件，不伪装成 `N4 Modification -> UE Configuration` 的线性 3GPP stage。

## 9. Mutation uncertainty

mutation outcome domain：

- `COMMITTED`
- `NOT_COMMITTED`
- `OUTCOME_UNKNOWN`

任何 `OUTCOME_UNKNOWN`：

1. 停止业务推进；
2. reconcile exact original mutation；
3. 不 blind retry；
4. 不使用可能不存在的 output；
5. reconcile 得到 COMMITTED / NOT_COMMITTED / UNRESOLVED 都结束当前 invocation 为 SAFE_STOPPED；
6. 后续 continuation 必须是新的 admitted recovery decision。

这条规则适用于 UDM Subscribe、PCF Create、N1N2 transfer 以及 resource-responsibility mutation。

## 10. Resource responsibility

资源责任边界从第一次资源 mutation 开始。

- 第一次 mutation 前失败：不做资源 finalization；
- mutation 已开始后：每个 FAILED / UNRESOLVED / success exit 都必须完成 resource responsibility transfer；
- finalization 自己出现 mutation uncertainty 时同样 exact reconcile + SAFE_STOPPED；
- `createdsession.resources.managed` 必须绑定 current lifecycle。

显式 `finalize-success / finalize-failed / finalize-unresolved` 和 reconcile nodes 目前保留在 authoring source 中，因为它们虽然偏 execution-oriented，但可靠性边界明确。等多个 Skill 都出现同一模式后，再评估是否值得上移成 procedure-level 语法；当前不为了缩短 YAML 新增抽象。

## 11. Namespace

| namespace | 含义 |
| --- | --- |
| `sbi.*` | 真实 NF/SBI operation |
| `ca.*` | ConnectionAgent-owned capability；effect 可为 read/local compute/evidence wait/mutation |
| `skill.*` | Skill-local deterministic tool/evaluator |
| `createdsession.*` | CreatedSession Predicate / business fact |

namespace 表示 ownership，不表示 effect。effect 仍由 capability/tool metadata 决定。

3GPP operation 名尽量按 canonical token 转为 kebab-case：

- `Nudm_SDM_Get` → `nudm-sdm-get`
- `Nudm_SDM_Subscribe` → `nudm-sdm-subscribe`
- `Npcf_SMPolicyControl_Create` → `npcf-sm-policy-control-create`
- `Namf_Communication_N1N2MessageTransfer` → `namf-communication-n1n2-message-transfer`

## 12. Contract 与最终成功

最终成功由 Contract 独立要求：

- `createdsession.ran.setup_accepted == PASS`
- `createdsession.n4.forwarding_ready == PASS`
- `createdsession.resources.managed == PASS`

P8-A2 起 `createdsession.ue.configuration_accepted` 已删除：UE 内部状态（NAS
PS-ACTIVE、TUN、Ping）不是 Agent 可观测的业务事实，也不是本 Skill 的成功条件。

Root 到达 `done` 不是独立的成功证明。

状态域保持分离：

- Predicate：PASS / FAIL / UNKNOWN；
- mutation certainty：COMMITTED / NOT_COMMITTED / OUTCOME_UNKNOWN；
- Procedure terminal：SUCCEEDED / FAILED / UNRESOLVED / SAFE_STOPPED。

timeout 本身不等于 FAILED；缺失、过期、歧义 evidence 不能被猜成 PASS。

## 13. 原设计阶段的 Toolchain / Runtime lowering 约束（历史记录）

以下是当时对 lowering 的设计要求，不是对当前 Demo 的未完成任务清单。authoring source 可以领先正式 Toolchain pinned schema，但不能因此反向改坏业务语义；本仓现有可执行参考 lowering 应按当前代码和测试核对，不得依此节重新立项开发正式 Toolchain。

lowering 至少负责：

- 展开 `preconditions.steps`；
- 实现 precondition aggregate FAILED / UNRESOLVED route；
- 展开 `postconditions.steps`，只允许有序 Predicate verify + optional `with`；
- postcondition 首个 FAIL/UNKNOWN 即走 block route；仅全部 PASS 才走 PASS route；
- 禁止 step-level postcondition `on`；
- successful operation → postcondition phase；
- producer-bound `with/from` subject projection；
- evidence await；
- child Procedure context projection；
- native reconcile；
- terminal routing；
- trace identity；
- resource-responsibility execution。

lowered graph 是执行产物，不是新的 authoring source。

## 14. Cases 设计记录与现行状态区分

现有 36 个 Case 的业务目的和 expected terminal/postconditions 仍有价值，但旧的 exact trace 与 mock fixtures 是针对旧 execution graph 编写的。

在 lowering 语义冻结前，不应猜测迁移这些 flattened node IDs。

**上述判断是旧设计阶段的历史说明。** 截至 2026-10-24，
Demo-local 的 36 个 authored Cases 已经完成 compile → link → admission →
Runtime 的本地参考验收（详见 [当前实施基准](createdsession-current-implementation-baseline.md)
引用的历史证据）。此结果**不等同**于正式 Toolchain 资格或真实 B/C。
是否需要更新某个 Case，必须依据当前源码和回归失败，而不能依据
“等待 Toolchain lowering”重新执行一轮开发。

Case schema validation 不等于 workflow execution，也不等于 Runtime qualification。

## 15. 冻结结论

当前主业务 flow、pre/postcondition 语义、evidence provenance、mutation uncertainty 和 resource responsibility 仍是有效的业务设计背景。

**现行确定性 Demo 路线不以开发正式 lowering/schema/runtime 为下一步目标。**
下一步首先依据 [当前实施基准](createdsession-current-implementation-baseline.md)
核对已实现代码与真实 owner 的时序/来源缺口；如需调整 Skill 前置
业务事实，应先说明跨层冲突并进行专项评审，不得通过增加假来源
或新安全基础设施绕过真实执行阻塞。
