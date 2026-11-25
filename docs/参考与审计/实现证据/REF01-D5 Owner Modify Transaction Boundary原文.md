> 迁移来源：ca-agent-demo/docs/design/D5_OWNER_MODIFY_TRANSACTION_BOUNDARY.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：Modify/Release Owner 事务边界与验收证据  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；证据的当前有效性需按具体 main/PR/测试 SHA 单独核验。

---

# D5 Owner Modify transaction boundary (ADR)

**Status:** accepted for the Development profile (2026-11-21).
**Supersedes:** the “proposed analysis only / OpenAMSM not writable” framing in
`docs/work/mas-e2e/d5-modify-owner-transaction-boundary-20261121.md`.
**Scope:** the D5 Owner QoS Modify capability implemented in the isolated
`env-openamsm-d5` worktree. Production admission is **not** claimed.

## Decision

Use the **MAS-native** boundary (Option A), inside the existing
`UPN.MODIFY_UP_SESSION` fused operation. No new MAS operation, callable, step
or second Modify engine is introduced.

```text
CA-SL Modify procedure
  m0  SC.UPDATE_SM_CONTEXT                       (existing)
  m3  UPN.MODIFY_UP_SESSION_INTENT               (existing; no AN change)
  m4  SSM.SIGNAL_UE_AN_MODIFY                    (existing; already-known tuple)
  m5  UPN.MODIFY_UP_SESSION  + qos_flows_delta   (this ADR)
        Owner: validate -> stage GBR/MBR -> PFCP QoS Modify
               -> native N1/N2 Modify dispatch
               -> complete the exact MAS invoke (APPLIED)
  postcondition: independent /pdu-info read + N2 Modify Response ledger
                 + PFCP QER before/after
```

The CA-SL procedure remains the business authority (precondition, invocation,
postcondition). The Owner owns the PFCP/N1/N2 mechanics and the exact
transaction state. The Host does not execute an SMF protocol state machine.

### Why not the controlled native transaction (Option B)

Option B would require the Host to own an AMF Nsmf Update stream across
processes and forward the original N1 bytes into the SMF. That is not available
through the existing typed Provider boundary, and exposing it would duplicate
stream ownership that the SMF already has. Option A reuses
`gsm_handle_pdu_session_modification_*`’s state model, `smf_bearer_qos_update`,
`smf_5gc_pfcp_send_qos_flow_list_modification_request`, and the existing
Network-requested N1/N2 transfer path.

## Chosen real delta

**A consistent 5QI + GBR/MBR modification of an existing QoS flow.**

The D5 scenario changes QFI 1 from 5QI 9 / non-GBR to 5QI 1 with
GFBR 100 000 bit/s and MFBR 200 000 bit/s (UL and DL). The 5QI and the complete
GBR/MBR set are applied together; the Owner rejects a bitrate-only delta on a
non-GBR flow, a partial target set, and any `gbr > mbr`. This is a legal QoS
Flow modification, not the forbidden injection of GBR/MBR into a 5QI 9 flow.

The pre-existing-GBR-flow path remains supported (same validation), but the
final Development E2E uses the existing flow because the current SMF binds
dedicated PCC-rule flows **after** it has built the initial N2 Setup Request;
a pre-created dedicated GBR flow therefore arrives as a second N2 Modify and
was not the minimal D5 transaction. The 5QI+GBR modification is atomic at the
Owner, PFCP-visible (QER) and N1/N2-visible (5QI/QoS parameters).

- Input: `qfi`, `fiveQi`, `gfbr_ul`, `gfbr_dl`, `mfbr_ul`, `mfbr_dl`.
- Target state: 5QI and the four GBR/MBR values after the merge.
- ARP / session-AMBR / flow add / flow delete remain out of scope.
- Independent proof: `/pdu-info` projects per-flow `5qi` and
  `gbr_ul/gbr_dl/mbr_ul/mbr_dl`; PFCP Session Modification carries the Update
  QER; the N2 Modify exchange is recorded by the Mock AMF.

## Input contract

```text
qos_flows_delta = "1"          (closed marker)
qfi             = 1..63, existing flow
five_qi         = known 5QI; the target must be a GBR 5QI
gfbr_ul/gfbr_dl = decimal bits/s, 1..OGS_MAX_BITRATE_NGAP
mfbr_ul/mfbr_dl = decimal bits/s, 1..OGS_MAX_BITRATE_NGAP
```

Validation (all fail closed before any state change):

- full-string decimal only; no sign, whitespace, trailing junk or overflow;
- QFI must resolve to exactly one existing QoS flow;
- target 5QI must be known and a GBR 5QI, with a QER;
- after merge all four values must be non-zero and `gbr <= mbr` per direction;
- a non-GBR → GBR conversion must state the complete target set;
- the session must not have an outstanding MAS frame or a non-empty
  `qos_flow_to_modify_list` (never mutate another flow by accident);
- no delta vs current state → `ALREADY`, no PFCP.

## Completion semantics

`UPN.MODIFY_UP_SESSION` returns:

| Output | Meaning |
| --- | --- |
| `qos_delta_state=APPLIED` | PFCP QoS Modify accepted and the native N1/N2 Modify has been handed to the relay |
| `qos_delta_state=ALREADY` | target state already equal to the request; no PFCP was sent |
| `n1n2_dispatched=1` | N1/N2 dispatch succeeded (best-effort relay send checked) |
| `qfi`, `five_qi`, `gfbr_*`, `mfbr_*` | exact applied target |

`n3_synced` is **not** written by this transaction and is not used as the
completion proof. `APPLIED` is deliberately not “the RAN/UE accepted”: the N2
Modify Response is a separate native continuation. The Skill Predicate closes
the Owner transaction at `PFCP_APPLIED` + `N1N2_DISPATCHED`; it does **not**
claim `RAN_MODIFICATION_CONFIRMED`. That level requires the observed N2 Modify
Response, and `TARGET_STATE_VERIFIED` requires an independent Owner read. Both
are recorded as separate E2E acceptance gates, never inferred from `APPLIED`.

### Failure and recovery

- PFCP send failure before the wire: restore the pre-delta QoS/QER state,
  destroy the parked frame, return `FAILED`.
- PFCP reject: `mas_upnode_qos_delta_failed()` restores state, destroys the
  frame, returns `FAILED`.
- N1/N2 dispatch failure: the delta stays applied (the UPF may have accepted
  it); the invoke fails and the Provider records `UNKNOWN`, never success.
- PFCP timeout: no completion; the Provider times out to `UNKNOWN`; no second
  dispatch.
- Owner restart: no durable MAS receipt is published, so an in-flight delta
  becomes `UNKNOWN`; no guessed success. Production Receipt/Reconcile remains
  `NOT_CLAIMED`.
- A Modify Run never creates a second PDU Session, never clears
  `n3_synced` to force PFCP, and never re-dispatches on UNKNOWN.

## Idempotency

`already` compares the full target set with the authoritative flow state, not
merely the presence of an input. A repeated invoke with the same target returns
`ALREADY` with no PFCP. A different target on the same session is a new
mutation only through a new Skill invocation with a new exact request digest.

## Residual risks (documented, not hidden)

1. The PFCP QER Update cannot carry 5QI/ARP. The 5QI is carried by N1/N2 and
   the QER carries the GBR/MBR; ARP remains out of scope. The Owner validates
   the 5QI against the known GBR set, but only the QER bitrates are
   independently observable at the UPF.
2. The later `PDU_RES_MOD_RSP` triggers the existing `DL_ONLY|ACTIVATE` PFCP
   modification; if the MAS frame is already completed, that response does not
   complete it again. The session-context/exposure side effect of that branch
   is pre-existing and outside this transaction.
3. There is no durable Owner receipt/reconcile producer; the Development
   profile only claims `APPLIED` at dispatch, and Production remains
   `D5_PRODUCTION_QUALIFICATION_NOT_CLAIMED`.
4. A GBR flow prerequisite is environment setup, not a source shortcut. The
   isolated E2E profile must establish it legally before the delta.

## Acceptance labels

- `D5_OWNER_MODIFY_TRANSACTION_CONTRACT_PASS` only when the contract above is
  implemented and the validation/negative tests pass.
- `D5_OWNER_SAFE_IMPLEMENTATION_PASS` only with the isolated build + unit
  negatives.
- `D5_OWNER_NATIVE_QOS_MODIFY_PASS` only with a real PFCP 52/53 QER delta on the
  target flow and an independent read.
- `D5_MODIFY_TARGET_POSTCONDITION_PASS` only with the postcondition read and
  N2 continuation evidence (where applicable).
- `D5_PRODUCTION_QUALIFICATION_NOT_CLAIMED` always.
