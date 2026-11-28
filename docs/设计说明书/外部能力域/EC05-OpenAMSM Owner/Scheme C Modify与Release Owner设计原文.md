> 迁移来源：env-openamsm/docs/scheme-c-owner-qos-delta.md  
> 固定源提交：dc83ccbf5be54dcc7112dd43ba95ea6fa5975550  
> 原始状态：Scheme C QoS Modify、UE-requested Release 和真实验收记录  
> 迁移追踪：ca-agent-next Issue #12。源仓未提供独立 Owner 总体架构文档；本组原文是 Owner 设计/实现证据，Next 架构将标记为实现派生重建。

---

# Owner `UPN.MODIFY_UP_SESSION` QoS delta（Scheme C 第 1 步）

状态：**Owner 能力已落地并可构建**；不声明 Scheme C E2E。配套设计见
`docs/scheme-c-ue-modify-design.md`（PR #19）。

## 1. 内容

`patches/openamsm/0006-owner-qos-delta.patch` 在既有 `UPN.MODIFY_UP_SESSION` 上补一个闭合的
typed QoS delta transaction，不新增 `UPN.MODIFY_QOS_FLOWS`：

```
qos_flows_delta = "1"
qfi             = 1..63
five_qi         = known GBR 5QI (optional)
gfbr_ul/gfbr_dl = bits/s
mfbr_ul/mfbr_dl = bits/s
```

- 严格校验：QFI 存在且有 QER、GBR 5QI、完整/一致的 GBR/MBR、`gbr <= mbr`、非零、无溢出；
  非 GBR flow 只有在给出完整目标集合时才允许转 GBR；
- 目标已存在 → `ALREADY`，不发 PFCP；否则复用 `smf_bearer_qos_update()` 与既有 PFCP QoS
  modification 路径，发送真实 Update QER（52/53），PFCP accept 后完成；N1/N2 发送失败时返回
  `PFCP_APPLIED_N1N2_FAILED`，绝不报成功；
- PFCP 发送前失败/响应拒绝 → 恢复 QoS/QER 快照；outstanding Frame 或非空
  `qos_flow_to_modify_list` → 拒绝；
- `/pdu-info` 增加只读的 per-flow `gbr_ul/gbr_dl/mbr_ul/mbr_dl`，供独立验收读取。

该实现源自已评审的 D5 Owner interface（`env-openamsm-d5` `docs/d5-owner-modify-interface.md`），
但本 PR 把它作为独立的 Owner 能力提交，不依赖 D5 profile/分支，也不使用 D5 的隔离配置。

## 2. 验证

- `./bin/env-openamsm build`：PASS，patch identity
  `f99b38f35bb7f0bac7fb5d1d747da5c8c5a630abd423235791191bfd739f1533`；
- `./tests/run_unit_tests.sh`：PASS（平台独立测试集）；
- 补丁对 `upstream/openamsm` 干净副本 `patch -p1 --dry-run` 通过；
- `/pdu-info` 投影随 patch 编译进 SMF（字段只在有 QoS flow 时输出）。

## 3. 尚未完成（本 PR 不声明）

1. `SSM` 的 N1 `0xC9` 解析 Operation（把原始 N1 变为 typed delta）；
2. NW-Agent facade 的 Modify transaction 编排（parse → UPN → signal）；
3. N1 `0xCB` + N2 `PDU_RES_MOD_REQ` 的 SSM 发送与 N2/N1 完成回调关联；
4. Scheme C 真实 E2E 与 `/pdu-info`/PFCP 证据；
5. CA-SL/Provider/CA Agent 更新（必须等 Owner 契约稳定）。

在这些完成前，`SCHEME_C_NW_AGENT_MODIFY_E2E` 保持 **NOT_RUN**。

## 4. SSM N1 parse branch（同一 PR 的第二个提交）

`patches/openamsm/0007-ssm-n1-modify-parse.patch` 在既有 `SSM.SIGNAL_UE_AN` 上增加一个**只读**
分支，避免为“解析 N1”新增 Catalog Operation：

```
parse_n1 = "1"
n1_sm    = hex(原始 5GSM PDU Session Modification Request 0xC9)
```

行为：用 pinned OpenAMSM `ogs_nas_5gsm_decode` + `ogs_nas_parse_qos_flow_descriptions` 解码，
输出 `qfi`、`five_qi`、`gfbr_ul/gfbr_dl`、`mfbr_ul/mfbr_dl`（bits/s）与
`requested_kind=qos_flow_descriptions`；要求恰好一个 QoS flow description。任何解码失败、
非 `0xC9`、缺少 requested QoS flow descriptions、多 flow 或不支持的参数都返回 VALIDATE。

它**不**修改 session state、不启动 PFCP、不发送 N1/N2；Agent 把输出绑定给
`UPN.MODIFY_UP_SESSION`，由后者执行真实 QER 修改，再由 SSM 的信令步骤发送 N1/N2。

构建验证：`./bin/env-openamsm build` PASS，patch identity
`cae11df4a1aa02f550d6be7da98aee327bf3c0de04f289db8c9ea5bc69f308cc`。

## 5. NW-Agent Scheme C Modify 编排（同一 PR 的第三个提交）

`patches/openamsm/0008-nw-agent-scheme-c-modify.patch` 修改 `tools/nw-agent`：

- 识别 Update 的 N1 `0xC9` 为新 UE Modify 事务（不是完成回调）；
- 调用 `SSM.SIGNAL_UE_AN` 的 `parse_n1=1` 分支，把原始 N1 hex 交给 Owner 解析；
- 把返回的 `qfi/five_qi/gfbr_*/mfbr_*` 绑定给 `UPN.MODIFY_UP_SESSION`（`qos_flows_delta=1`）；
- N1 `0xCC/0xCD` 或 N2 `PDU_RES_MOD_RSP` 不再启动 Modify 事务，而是转发给 SMF 作为
  native continuation（SMF 的 skip 集合允许这些完成消息在 `agent_step` 下走原生
  N2 modify response / PFCP DL_ONLY 更新）；
- Agent 不解析 NAS、不计算 QER，parse/apply 的 idempotencyKey 绑定 agent transaction。

`python -m py_compile` PASS；三个 patch（0006/0007/0008）对干净 upstream 联合 apply 通过。
真实 C E2E 仍需在 `agent_step` 栈上运行，当前 **NOT_RUN**。

## 6. 与 Scheme A 的非 GBR 对等修正

`patches/openamsm/0009-non-gbr-qos-delta.patch`：native A 对默认 5QI 9 flow 的 bitrate-only
修改会真实发 PFCP Update QER。为满足“A/C 使用同一 N1 向量与等价会话”的约束，C 的 UPN delta
允许 **5QI 不变 + 完整 GBR/MBR 集合** 的非 GBR 目标；5QI 变更为非 GBR、部分集合或反向值仍拒绝。

## 7. 真实 Scheme C E2E（2026-11-22）

`SCHEME_C_NW_AGENT_MODIFY_E2E` **PASS**：真实 `0xC9` → SCP → NW-Agent →
`SSM parse_n1` → `UPN.MODIFY_UP_SESSION` → PFCP 52/53 QER（MBR 500/1000、GBR
200/400）→ N1 `0xCB` + N2 `PDU_RES_MOD_REQ` → UE Complete/N2 Response →
独立 `/pdu-info` 显示精确 GBR/MBR。原始证据：`env-5gc-sim`
`artifacts/acceptance/20261122-scheme-c-ue-modify/`。

## 8. P0 Relay fail-closed 收敛（2026-11-22）

`patches/openamsm/0010-relay-fail-closed.patch` 修复 §7 运行留下的真实缺陷（Issue #22）：
UPN 在 PFCP 接受、N1/N2 交给 Agent Relay 后立即报成功，Relay 的 Namf Transfer 响应
并未参与判定。现在：

- `smf_namf_comm_send_n1_n2_message_transfer()` 返回 `bool`：xact 创建或发送失败即为
  false；`namf_peer=agent_relay` 明确配置时**不再回退 NRF discovery**。
- `mas_ssm_n1n2_transfer()` 传播该失败；n4 handler 只在 handoff 成功时调用
  `mas_upnode_qos_delta_await_namf()`，并保持 delta invoke parked。
- namf handler 先认领该 waiter：仅 `200/201 + N1_N2_TRANSFER_INITIATED` 完成
  `APPLIED`；`200 + N1_MSG_NOT_TRANSFERRED`、`202 ATTEMPTING_TO_REACH_UE`、非 2xx、
  缺失 rsp data、以及错误的 `param_state` 一律 fail closed
  （`PFCP_APPLIED_N1N2_FAILED`）。完成后到达的重复/迟到响应返回 `E_WAIT`，不会重放成功。
- `OGS_TIMER_SBI_CLIENT_WAIT` 对 `namf-comm` 的等待 delta 触发同样的 fail-closed 完成，
  超时不再让 Owner 调用永久 parked。

验证（隔离 `ac` 栈、真实 SMF/UPF/SCP/NW-Agent/Mock AMF）：

- C 单测：`tests/smf-oes` 的 `qos-delta-test` 新增 4 个 await/correlation/reject/late
  用例，全部 PASS；
- 正向 E2E：`await_namf` → `applied`（真实 Transfer ack 后 14 ms），UE Modify 仍 PASS，
  `/pdu-info` GBR 200/400、MBR 500/1000，PFCP 52/53 真实；
- 反向：Relay 返回 `N1_MSG_NOT_TRANSFERRED` 与 Transfer 无响应（10 s client-wait 超时，
  15 s 迟到 200 不再生效）两种运行都得到 `n1n2_failed`、无 `applied`，UE Modification
  Request 以 502 失败；PFCP 已应用的 QoS 按设计保留、不回滚。

证据：`env-5gc-sim artifacts/acceptance/20261122-scheme-c-relay-fail-closed/`。

## 9. P1 UE Release 纯 MAS 编排（2026-11-22）

`patches/openamsm/0011-ue-release-pure-mas.patch` + `0012-nw-agent-scheme-c-release.patch`
把 UE 发起的 PDU Session Release 放进 Scheme C 的 Agent→MAS 主链，不再把原始
Release Update 透传给 native GSM/OES。

### 9.1 Owner（SSM/UPN/PA/SC/SE）

- `SSM.SIGNAL_UE_AN parse_n1=1` 增加 5GSM `0xd1` 分支：用 pinned OpenAMSM 解码器
  校验 EPD/PSI/PTI/消息类型，输出 `release_intent=ue_requested`、`psi`、`pti`、
  `cause`，只读，不改状态、不发 PFCP。
- 同一 Operation 的 `release=1 mode=build`：由 SSM 构造 N1 Release Command（0xd3）
  与 N2 PDU Session Resource Release Command，以 hex 输出交给 Agent；SSM 记录
  `release_in_progress/command_built/generation/release_txn`，不发送 Namf、
  不 park、不删除 PFCP。重复 `0xd1` 在 Owner 侧拒绝。
- `release_confirm=n1|n2`：N1 Release Complete（0xd4）与 N2
  `PDU_RES_REL_RSP` 是独立的确认；必须与 build 时的 generation + Agent
  transaction 完全一致，重复、乱序、旧 generation 的确认返回 VALIDATE。
  只有两者都到齐才输出 `release_ready=1`。
- `UPN.DELETE_UP_SESSION(trigger=2)` 执行真实 PFCP Session Deletion（54/55）；
  `PA.DELETE_SM_POLICY`、`SE.EMIT_EVENTS`、`SC.RELEASE_SM_CONTEXT` 依次收口。
  SC 的 `finalize=1` 在 Orch 响应发出后清除 SMF Context（等价于 native
  finish 的清理，但不经过 OES workflow）。
- `smf_sbi_send_sm_context_status_notify()` 在 Scheme C 无 AMF client 时跳过
  通知而不是 `ogs_assert`。

### 9.2 Agent（NW-Agent）

- facade 识别 `0xd1`：调用 SSM parse → SSM build，把 Owner 构造的 N1/N2
  放进 `UpdateSMContext` 的 multipart 响应（TS 29.502）；Agent 不解析 NAS、
  不构造 NGAP、不计算 PFCP。
- `0xd4` / `PDU_RES_REL_RSP`：分别交给 SSM 确认；只有 `release_ready=1`
  才按 `PA → UPN → SE → SC` 调用正式 MAS Operation 清理，然后返回 204。
- 重复 `0xd1`、未到命令阶段的 `0xd4`、重复/迟到的 N2 Response 返回 409，
  不会重复删除或提前清理；清理步骤任一失败返回 502，绝不返回成功。

### 9.3 真实验收（2026-11-22）

隔离 `ac` profile、mandatory SCP、真实 OpenAMSM SMF/UPF/UDM/PCF/NW-Agent、
Mock AMF 发送真实 N1：

- 正常：`0xd1` → SCP → NW-Agent → SSM parse/build（0xd3 + N2 REL CMD）→
  `0xd4` + N2 REL RSP → PA DELETE_SM_POLICY → UPN DELETE_UP_SESSION
  （PFCP 54/55，UPF SEID 0xa51）→ SE RELEASED → SC RELEASE_SM_CONTEXT
  （finalize）。最终 `/pdu-info` 空、`[Removed] Number of SMF-Sessions is now 0`、
  `fivegs_upffunction_upf_sessionnbr 0`。
- 负例：命令前 `0xd4` = 409；重复 `0xd1` = 409；N2 RSP 先到 = 204 但无清理；
  重复 N2 RSP = 409；仅一次 PFCP deletion。
- 回归：Scheme C UE Modify（relay accept）仍 PASS。

证据：`ca-5gc-sim artifacts/acceptance/20261122-scheme-c-ue-release/`。

### 9.4 PFCP Deletion 超时/失败闭合（0013）

`patches/openamsm/0013-ue-release-pfcp-timeout.patch`：

- PFCP Session Deletion 无响应时，`sess_5gc_timeout()` 在 Scheme C 无 AMF stream
  的情况下不再 `ogs_assert(stream)`，而是向 parked 的 `DELETE_UP_SESSION` Frame
  投递 `result=TIMEOUT` 的 southbound 事件，Orch 调用以 502 失败结束。
- `SMF_TIMER_PFCP_NO_DELETION_RESPONSE` 不再清除仍有未决删除的 Session；
  保留 SM Context 供读取/恢复，重试的 `DELETE_UP_SESSION` 返回 `E_PFCP`
  而不是永久 park。
- 真实 `ac` 栈验证：删除 UPF 后发起 UE Release，N2/N1 完成请求得到 502
  `failedStep=r-upn`，无 204/成功；`No PFCP session deletion response` 与
  `PFCP deletion unresolved; retain SM context` 出现；`/pdu-info` 仍可见会话；
  再次确认返回 409。

### 9.5 只在成功时收口 SM Context（0014）

`patches/openamsm/0014-release-finalize-success-only.patch`：`SC.RELEASE_SM_CONTEXT` 的
`finalize=1` 只在 Orch 响应为成功时执行 `SMF_SESS_CLEAR`。若 UDM/UECM 收口失败，
Agent 收到失败，SMF 保留真实 Session，避免“失败但 Context 已被删除”的半释放状态。

### 9.6 TS 23.502 §4.3.4.2 符合性判定（2026-11-23，最终构建 93fcace）

对 UE 发起的 PDU Session Release（步骤 1a，非漫游/LBO，UP 连接激活，动态 PCC，
单会话）逐条核对 TS 23.502 V19.9.0 §4.3.4.1/§4.3.4.2 的规范文本：

- **强制发生**：N4 Session Release Request/Response（步骤 2a/2b，每 UPF 恰好一次）；
  N1 Release Command（步骤 3）；`Nudm_UECM_Deregistration`（步骤 15）；以及
  §4.3.4.1 的全部资源释放。
- **显式条件**：N2 Resource Release 仅在 UP 连接激活时包含（步骤 3/3a 的
  "shall"/"shall not"）；动态 PCC 时执行 PCF 终止（步骤 12）；仅当该 (DNN, S-NSSAI)
  的最后一个 PDU Session 时才 UDM SDM unsubscribe（步骤 14）。
- **显式并发**：N1 Release Complete（步骤 8–10）与 N2 Resource Release Ack
  （步骤 6–7）之间无先后约束（步骤 10 注："Steps 8-10 may happen before steps 6-7"）。
- **完成门禁**：步骤 11 等待 N1/N2 回复（"as needed"），随后
  `Nsmf_PDUSession_SMContextStatusNotify`；AMF 释放关联。
- **参考顺序**：图 4.3.4.2-1 与步骤编号把 N4 释放（步骤 2）画在 N1/N2 命令
  （步骤 3）之前、PCF 终止（步骤 12）画在步骤 11 之后；条文本身没有对
  2-vs-3 或 2-vs-12 的相对顺序写 "shall"。

当前 Scheme C 的实际顺序为：`SSM` parse/build（0xd1→0xd3 + N2 REL CMD）→
N1 0xd4 与 N2 REL RSP（任一顺序）→ `PA.DELETE_SM_POLICY` → `UPN.DELETE_UP_SESSION`
（真实 PFCP 54/55）→ `SE.EMIT_EVENTS` → `SC.RELEASE_SM_CONTEXT(finalize)`。
在已执行的配置下，步骤 2、3、11、12、14、15 与 §4.3.4.1 的强制/条件关系均发生且
恰好一次，显式并发允许被遵守；**没有必须修复的强制关系缺失**。因此**不因形式上的
步骤顺序改动代码**，最终构建保持 `93fcace…`。

已披露但不作为 PASS 的残余（详见 `ca-skills#83` §5.6.5）：

1. 未实现 UP 去激活分支：N2 无条件构造（该分支未被触发）；
2. 无 AMF client 时跳过步骤 11 的 `SMContextStatusNotify`；
3. SDM unsubscribe 以订阅状态为门，而非显式 (DNN, S-NSSAI) 最后会话判定；
4. `ac` 拓扑无 DN 实体，未验证 DN 通知；
5. PCF 终止先于 N4 释放：PCF 失败会阻断 N4 释放（fail-closed，不会误报成功）；
6. 未建模 "N1 not transferred" 完成路径。

`_release_cleanup` 内注释 "Order follows TS 23.502: policy termination,
user-plane release..." 的措辞不精确，以本节与 `ca-skills#83` §5.6 为准；
本轮不改该注释，避免改变已证据化的构建 identity。

## 10. P2 合并前可靠性收敛（2026-11-22）

本轮不新增业务能力，只收敛错误成功、错误清理、事务串扰和异常恢复缺陷。
补丁 `0015`–`0019`，构建 identity
`d17699bf3fe8198076bafb8c1c491b85b8e7e8dd00176e0912465fd93207502e`
（upstream `7dfe5a3d…`，patches `0001,0006-0019`）。

### 10.1 Release finalize 必须双字段成功（0015）

`0014` 使用 `status != OK && error_code != OK`，混合字段（一成功一失败）仍会
`SMF_SESS_CLEAR`。现在：

- `smf_mas_response_is_success()` 要求 `status == OK && error_code == OK`；
  不一致的组合映射为 `E_MAS`，不会变成 HTTP 200。
- `mas_orchestration_try_complete()` 的响应分支、finalize 判定和直接 invoke
  收尾全部使用 AND 语义；失败时保留 Session 并记录
  `release finalize fails closed`。
- 顺序固定为：发送响应 → 销毁 MAS Frame → `SMF_SESS_CLEAR`；Frame 销毁只
  释放 `invoke_frame`，bundle 直到 Session 释放才失效，无 use-after-free。
- 单测矩阵覆盖两字段的四种组合、WAIT/E_PENDING、未请求 finalize、UDM UECM
  失败和重复 finalize。

真实验收：杀掉 UDM 后在完成 N2 响应，SC 的 `DEREGISTER_UECM`（`r-sc`,
`nf_kind=UDM_UECM`）真实失败；Owner 返回 `502/E_SOUTHBOUND`，Agent 将该破坏性
步骤的不确定结果归为 `OUTCOME_UNKNOWN`（504），Session 保留，重试 409，UDM
恢复后不自动重放；PFCP 只有一次 deletion（54/55 同一 sequence）。

### 10.2 PFCP deletion 结果显式化（0017）

原实现用一个 bool 同时表示 in-flight 和 unknown，并在拒绝响应时提前清 guard，
迟到/游离的删除响应还可能走 legacy clear 路径。现在：

- `pfcp_del_state = NONE|IN_FLIGHT|ACCEPTED|REJECTED|UNKNOWN`；
  `mas_upnode_pfcp_del_complete(sess, accepted)` 区分接受与拒绝，超时进入
  `UNKNOWN`；`UNKNOWN` 不能作为普通 retry 重发删除。
- `mas_upnode_release_finalize_allowed()` 在响应成功之外还要求没有
  in-flight/unknown 的 PFCP deletion：未确认的用户面删除不能被信令成功掩盖。
- 重复 `DELETE_UP_SESSION` 在触碰原 Frame 之前拒绝，不再 orphan 第一条
  Invoke 的 Orch waiter。
- `pfcp-sm`、`gsm-sm` 的 legacy clear 入口和 `pfcp_restoration` 都跳过
  pending/unknown 删除的 Session；超时即使仍有 stream 也先失败闭合 parked
  Frame，不永久挂起。
- `UPN QueryContext` 暴露 `pfcpDeleteState` / `pfcpDeleteOutstanding`，未知状态
  可被外部观察。

真实验收：UPF 被杀后删除超时得到 502/UNKNOWN、Session 保留、重试 409 且不重发
删除。**未完成**：UPF 恢复后的显式 reconcile 操作不存在，UNKNOWN 仍是
BLOCKED，不能宣称可恢复。

### 10.3 Relay 事务精确关联（0016）

QoS delta 的 parked waiter 现在绑定四元组：

- 原始 MAS Invocation：`Frame.epoch` + `Frame.corr_id`；
- N1N2 Transfer 的 SBI transaction id（`smf_namf_comm_send_n1_n2_message_transfer`
  输出，经 SSM 保存，response 路径从 `sess->mas_namf_xact_id` 一次性消费）；
- 预期 `param_state`；
- 当前 Session。

其它 SBI transaction 的响应被忽略（继续等待），同一 transaction 但
generation/frame/param_state 不匹配则 fail closed；SBI client-wait timer 只有
命中自己的 transaction 才失败该 delta。显式 `agent_relay` 的 URL 为空或不可解析
时直接失败闭合，不再回退 NRF。`apply_transfer_side_effects()` 移到归属判定之后：
外来/迟到响应不会再 stash stream 或触发 retransfer。

单测覆盖 foreign xact、generation mismatch、reject、重复 response/timer、
无关 timeout；真实 relay accept/reject/hang 均 PASS。

### 10.4 并发与重启验收

- Mock AMF 增加真正的 `parallel` 步骤组（goroutine + WaitGroup），
  `env-5gc-sim artifacts/acceptance/20261122-scheme-c-release-reliability/`
  中两个并发场景（不同 SUPI 同 PSI、同 SUPI 不同 PSI）各跑
  Release ∥ Modify：只删除目标 Session，另一个保留；一次 54/55、一次 52/53；
  无 discard/nf mismatch/correlation mismatch。
- Agent 在 4 个 release 点被杀并重启：只返回 `OUTCOME_UNKNOWN`，不重建 N1/N2、
  不重发删除、不自动恢复；Owner 保留 Session。`0018` 补齐
  SSM/PA/SC 的 release 事实投影，`0019` 增加 fail-closed 的 restart 语义
  （`409 OUTCOME_UNKNOWN`、`release_phase=UNKNOWN`、ledger 先记 UNKNOWN）。
- 仍缺：Agent 无持久事务；`after_build` 中断不可恢复（命令字节只存在于丢失的
  HTTP 响应，Owner 的 `release_in_progress` 永久 sticky）；没有显式 reconcile
  surface。以上按 BLOCKED/限制报告，不用自动重试伪造 PASS。

### 10.5 P3 收敛（2026-11-23）

P2 遗留的三项已收敛，详见 `docs/scheme-c-pfcp-reconcile.md`：

- PFCP `UNKNOWN` 现在有显式、绑定 SUPI/PSI/generation/Invocation/SEID/UPF 且
  可审计的 Owner `POST /nsmf-upn-context/v1/reconcile`；`CONFIRMED_DELETED`
  只解除 finalize 门禁，不重发删除；`CONFIRMED_PRESENT`/`UNRESOLVED` 保持阻塞；
  `UPF_OBSERVATION` 与 `OPERATOR_ASSERTED` 严格区分。
- Agent 关联/事务生命周期有界化（terminal tombstone、TTL、active 上限、
  PSI 复用拒绝、UNKNOWN 永不回收），并提供显式的
  `POST /nnwagent-admin/v1/release-recovery`；`after_build` 与
  `before_cleanup` 仍明确 BLOCKED。
- 新增按 SUPI/PSI 精确定向的 PFCP 删除响应丢失注入与 SEID 错配注入，
  完成“正常 Release ∥ 目标 Session PFCP Timeout”的真实并发负例：
  A 正常清理、B 保持 UNKNOWN，A 的成功不解除 B，B 的失败不影响 A。

证据：`env-5gc-sim artifacts/acceptance/20261123-scheme-c-reconcile/`；
最终构建 `93fcace5…`；#23/#24 已在 PR #21 评论中记录修复与证据，按流程待合并后再关闭。
