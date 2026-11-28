> 迁移来源：ca-agent-demo/docs/design/execution-routes.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：当前 main 单一执行链与 Root Routing / Admission / Planning V2 实现架构  
> 迁移追踪：ca-agent-next Issue #12。该仓是 Python Generic Agent Host 参考实现，不是 Next 目标架构的自动实现证明。

---

# Generic Agent Host 执行路线

- **状态：** 2026-11-11 当前实现；单一执行链已落地，v0.3/v0.4 与 legacy executor 已删除。
- **规范架构：** [Generic Agent Host 规范架构](generic-agent-host-architecture.md)。
- **身份与打包：** [Package Identity](package-identity.md)；**多 Root 验收：** [Multi-Root Joined Simulation](multi-root-joined-simulation.md)。
- **历史任务包：** [最终收敛 Goal](../work/generic-agent-host-final-convergence-20261110.md)（实施记录）与 [历史架构文档](5gc-agent-host-architecture.md)（非规范）。

## 1. 定位

本仓库是 **Generic Agent Host 的可运行参考实现**，不是 5GC Agent，也不是 CreatedSession Demo。Host 可承载不同业务领域的 Root Skill、不同 Tool / Integration 组合，以及 deterministic 与 LLM-assisted 两种执行方式。

PDU Session / 5GC / Fabric SBI 是当前主要业务与 Integration 样例，不是 Host、Agent 或 Runtime 的架构身份。GitHub 仓库名 `ca-agent-demo` 和本地 checkout 根目录保持不变；内部 distribution / import package / wheel data root 已使用 `ca-agent-host` / `ca_agent_host` / `share/ca-agent-host`。

## 2. 唯一执行链

```text
Ingress Adapter
  -> normalized Host request
  -> deployment Root routing（allowed Roots / structured event routes）
  -> exact Admission + request-specific Eligibility / per-Root READY
  -> selected exact Root artifact
  -> Direct Entry  OR  Planning V2 preparation
  -> shared Link / Admission core
  -> one Invocation / Runtime
  -> Agent-side Tool
  -> Integration adapter
  -> external owner / business system
  -> Observation / Wait / Reconcile
  -> terminal disposition / delivery / shutdown lifecycle
```

所有生产 Invocation 只经过这一条链：

- 没有 legacy configured-Skill executor，没有 `run_createdsession_agent` 分支，也没有 Service 同时挂两个执行器。
- 只接受 `ca-agent-host.resident-deployment/v0.5`；v0.3 / v0.4 明确拒绝，无迁移、无 adapter、无 fallback。
- Direct Entry 与 Planning V2 只有上游准备不同，必须收敛到同一 Link/Admission core 与同一 Runtime 生命周期。
- HTTP、SBI、CLI 等只是 ingress / 命令入口，不是 Skill routing policy，也不能绕过 Admission。

## 3. 职责边界

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| Ingress Adapter | 认证后的输入解析、协议字段校验、外部 correlation / delivery 映射 | 隐式默认 Skill、直接执行业务 Procedure |
| Generic Host / Resident | deployment composition、Root 候选范围、request / invocation 生命周期、并发与顺序、shutdown/drain、per-Root READY | 具体业务规则、某个 Skill 的默认资产、协议专属状态机 |
| Agent | Intent understanding、Root candidate selection、Planning V2 preparation、模型交互 | 未准入的 Runtime steps、权威副作用事实 |
| Skill | 业务 Goal、Procedure、Predicate、Scripts、Schemas、References、Capability 声明 | 公共 Runtime 安全门、外部 owner 状态 |
| Link / Admission Core | exact identity、材料解析、依赖闭包、冻结、来源与契约校验 | 按 Skill 名称特判 |
| Runtime | 冻结图执行、Tool dispatch、Effect、budget、Observation / Wait / Reconcile、终态 | 业务分支、PDU Session / CreatedSession 默认值 |
| Agent-side Tools | Operation / Capability contract、手工注册、受控投影与本地关联 | 复制外部 server、伪造外部权威状态 |
| Integrations | 外部 API / transport / protocol 的 consumer adapter | 成为 Host 的业务决策层 |
| Observability | 通用 Trace / Recorder / 持久化 / 诊断投影 | 业务成功真相的替代物 |
| Examples | 可运行示例、示例 Skill / Tool contract / registration、Joined Simulation composition | production Host / Runtime / Tool 实现 |
| Tests / Fixtures | 测试、契约快照、测试替身 | 生产运行时输入 |

跨 Skill 的安全不变量归 Host / Runtime / Tool contract；业务语义归 selected Skill；外部协议与权威状态归 Integration / external owner。

## 4. Root Routing、Admission 与 Planning

- Root Routing 从 deployment 允许、角色正确、exact Admission 成功且当前请求所需能力 READY 的候选中选择 Root。allowed Roots 与结构化事件路由来自 v0.5 deployment 的 `rootSkills` / `rootRouting`。
- 自然语言 / 语义判断可以使用模型，但模型只能选择已枚举的 exact eligible candidates；无法唯一选择、资格未知或 READY 不满足时 fail closed。
- 不允许把“所有 HTTP 请求”“intent absent”或未知输入映射为固定业务 Skill。
- **Direct Entry：** 选中 Root 的正式 entry Procedure 直接做 exact resolve、Link、Admission 与 freeze。
- **Planning V2：** Root 声明 planning surface 且输入足够时，执行 Goal lowering、Context、Formal / Semantic Planning、Binding 与 Replan；它是可复用可选能力，不是所有 Skill 的固定 hop。
- 两者最终都走 `runtime/linker.py` 的共享 Link/Admission core 与单 Runtime。
- `SkillContextLoader.catalog()` 不能代替 deployment allowlist、Admission 或 READY authority。

## 5. Multi-Root 绑定

采用 **deployment-level union + invocation-level exact subset**：

- 一个 deployment 只读取一份手工 Tool Registration，绑定所有 allowed Roots 所需 Operation 的并集。
- 每个 Root 从 selected exact artifact 推导 Capability closure、Operation subset、Scripts、Schemas、References、Wait Specs 与 Observation requirements。
- 每 Root 独立计算 READY（`ResidentHost.preflight().root_ready` / `.root_reasons`）；缺项只影响依赖它的 Root。
- Invocation 创建时冻结 selected exact artifact 与该 Root 的 Operation allowlist；Runtime dispatch 拒绝跨 Root 调用（`runtime/capability_scope.py`，`resident/capability_scope.py` 为 Resident 侧再导出）。
- Root-scoped scripts 由 `resident/root_scripts.py` 的 `RootScopedScriptBackend` 隔离。
- 不为每个 Root 创建独立 Tool Registration、Tool backend、Resident Service 或 Executor。
- v0.5 deployment 支持显式 `skillSourceRoots`；example Skill 只有在显式 source root 下才可见，无 `if examples/` 分支、无自动发现。

**Authority：** `tools/contracts/` 负责 Agent-side Operation input/output Schema 与 expected Effect；Capability contract 数据负责 Capability → Operation；Registration 只绑定 Operation → Implementation；Integration 提供实现。实现自报的 `effect_of()` 必须与 Tool contract 的 expected Effect 一致，不构成第二份 authority。

## 6. Deterministic 与 LLM-assisted

- Deterministic path：输入解析、路由、Admission、Link、Runtime 与副作用治理均可确定性验证。
- LLM-assisted path：模型可参与 Intent understanding、语义 Root selection、Planning V2；模型输出必须转成受约束候选材料，再经确定性 Admission / Runtime。
- 完整 LLM Skill executor / 自由形式多步动态执行循环当前延期但保留接口；未来接入必须复用同一 Host / Invocation / Tool / Journal / Effect / Reconcile 边界。
- 不能因为 LLM 路线延期就把 deterministic Host 固定成某个 Skill，也不能因为引入 LLM 另建副作用 authority。

## 7. 当前 5GC 样例的准确位置

```text
Fabric SBI adapter
  -> normalized Host request
  -> deployment Root routing / exact Admission / per-Root READY
  -> establish-pdu-session Skill
  -> shared Link / Admission core / single Runtime
  -> Agent-side 5GC Tools
  -> Provider / Fabric / Open5GS owners
```

边界：

- Fabric SBI 是一个 ingress adapter，不是 Generic Host 唯一允许的入口形态。
- 当前 flat v0.1 没有业务自然语言 intent；`intent_ref` 是 correlation identity，不是业务 intent。
- 不修改 Fabric wire contract 或其他 owner 仓库。
- 真实 5GC Live E2E 未执行（`NOT_RUN`），仍是独立授权门禁；历史 PASS 只能按原始证据范围引用。
- PDU Session、UDM、PCF、AMF、N1/N2、N4 等词只出现在相应 Skill / Tool / Integration / 协议契约 / 示例中，不得进入 Generic Host / Runtime 硬编码分支。

## 8. 验证与证据

```bash
uv sync
uv run --no-sync python scripts/validate_docs.py
uv run --no-sync pytest -q -m "not live_model"
git diff --check
```

Multi-Root Joined Simulation 的 7 项机制测试已在 2026-11-11 于当前工作树执行通过：

```bash
uv run --no-sync pytest -q tests/integration/test_multi_root_joined_simulation.py
# 7 passed
```

当前证据状态、占位符与未执行项见 [WORK](../WORK.md) 与 [TRACEABILITY](../TRACEABILITY.md)。未实际执行的命令不得报告 PASS。
