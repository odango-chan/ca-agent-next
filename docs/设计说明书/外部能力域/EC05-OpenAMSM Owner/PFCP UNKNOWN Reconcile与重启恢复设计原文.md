> 迁移来源：env-openamsm/docs/scheme-c-pfcp-reconcile.md  
> 固定源提交：dc83ccbf5be54dcc7112dd43ba95ea6fa5975550  
> 原始状态：PFCP UNKNOWN 精确绑定 Reconcile 与受限重启恢复设计  
> 迁移追踪：ca-agent-next Issue #12。源仓未提供独立 Owner 总体架构文档；本组原文是 Owner 设计/实现证据，Next 架构将标记为实现派生重建。

---

# Scheme C — PFCP `UNKNOWN` reconcile and restart recovery

**Status: implemented and verified on the real `ac` stack (2026-11-23).**
Owner PR #21; evidence `env-5gc-sim` PR #79
`artifacts/acceptance/20261123-scheme-c-reconcile/`.
Baseline: `d17699bf…` (P2) → final `93fcace589c40fc589bdcca947ab2a9108220dd96a05bf5e74379a7a88f9212b`.

This document owns the P3 design for `env-openamsm#23` (explicit reconcile) and
`env-openamsm#24` (restart recovery / lifecycle). It does not change the Scheme C
responsibility split: SSM (N1/N2 signalling), PA (policy), UPN (PFCP/UPF), SC
(session lifecycle), SE (events), Agent (orchestration). One logical SMF; the
Agent is not a second business-state authority and introduces no database.

## 1. PFCP deletion states

`NONE | IN_FLIGHT | ACCEPTED | REJECTED | UNKNOWN` (unchanged from P2).

`UNKNOWN` means the network outcome cannot be proven locally. It:

- blocks a normal `DELETE_UP_SESSION` retry (`mas_upnode_pfcp_del_blocks_retry`);
- blocks `RELEASE_SM_CONTEXT(finalize=1)` (`mas_upnode_pfcp_del_pending`);
- can never be turned into `ACCEPTED` by a late/stray response;
- can only be resolved by an explicit, bound, audited reconcile decision.

`CONFIRMED_DELETED` releases the finalize gate **only**. The raw
`pfcpDeleteState` stays `UNKNOWN`, the retry gate still sees `UNKNOWN`, and no
PFCP message is sent.

## 2. Binding captured before the deletion

`mas_upnode_pfcp_del_bind()` runs in `delete_release_invoke()` before
`mas_upnode_release()`:

- SUPI / PSI;
- `release_generation` from SSM;
- original `step_id` (`r-upn`) and `corr_id` (idempotency key);
- frame epoch (filled when the outcome becomes `UNKNOWN`, while the Frame is
  still active);
- `n4Seid` (`sess->upf_n4_seid`, the UPF-side SEID);
- target UPF identity from the PFCP node id (`ipv4:127.0.2.7`, `ipv6:…` or
  `fqdn:…`).

The reconcile request must match every field. This is what prevents a decision
from crossing sessions, generations or PFCP transactions.

## 3. `POST /nsmf-upn-context/v1/reconcile`

Owner SBI, guarded by the existing context-query token plus explicit
`reconcileId` / `operator` / `reason`. Path is dispatched before the read-only
`nsmf-upn-context/v1/query` sniffer; `query` is still served by the QueryContext
handler.

Request (abridged):

```json
{
  "reconcileId": "rec-…",
  "supi": "imsi-…", "pduSessionId": 6,
  "sessionGeneration": 1,
  "masStepId": "r-upn", "masCorrId": "txn-…:r-upn", "masEpoch": 1,
  "n4Seid": "1731", "upfId": "ipv4:127.0.2.7",
  "expectedDeleteState": "UNKNOWN",
  "operator": "acceptance-harness", "reason": "…",
  "evidence": {
    "source": "UPF_OBSERVATION",
    "observedAtUnix": 1763...,
    "raw": "<exact JSON body of GET /session-info?page=0&page_size=20>",
    "sha256": "<sha256 of raw>"
  }
}
```

Evidence variants:

| source | Accepted when | Decision |
| --- | --- | --- |
| `UPF_OBSERVATION` | raw JSON object with `items[]`, digest matches, ≤300 s old; the Owner itself looks up `upf_n4_seid` | target absent → `CONFIRMED_DELETED`; target present → `CONFIRMED_PRESENT` |
| `OPERATOR_ASSERTION` | `asserted=DELETED|PRESENT` + operator + reason | `CONFIRMED_*`, source recorded as `OPERATOR_ASSERTED` |
| missing/invalid | — | `UNRESOLVED` (recorded, gate stays closed) |

Responses (HTTP 200 for decisions): `outcome`, `evidenceSource`,
`pfcpDeleteState` (still `UNKNOWN`), `finalizeUnblocked`, `autoDelete: false`,
`observationDigest`, `recordedAt`.

Refusals: `400 STALE_OBSERVATION` / `OBSERVATION_DIGEST_MISMATCH` /
`INVALID_EVIDENCE` / `OPERATOR_AUTHORIZATION_REQUIRED`; `404 SESSION_NOT_FOUND`;
`409 NOT_UNKNOWN` / `BINDING_MISMATCH` / `TRANSACTION_IN_FLIGHT` /
`RECONCILE_CONFLICT`.

Idempotency: an identical terminal decision is a replay (no state change); a
different terminal outcome is `409`. `UNRESOLVED` may be retried.

Race safety:

- a late/duplicate PFCP deletion response after a reconcile decision is not
  claimable and cannot clear the context (`pfcp-sm.c`);
- UPF restoration uses `mas_upnode_pfcp_del_lifecycle_held()` and skips any
  session with an UNKNOWN or reconciled deletion;
- a second destructive deletion still requires a new explicit authorization and
  transaction; reconcile cannot produce one.

## 4. Agent restart recovery

The Agent keeps no durable business state. It bounds its own memory:

- `ASSOC_TTL_SEC` (600 s) reclaims terminal assocs into a bounded tombstone FIFO
  (`ASSOC_TOMBSTONE_MAX` 512);
- live idle assocs are capped at 24 h (`OPENAMSM_ASSOC_ACTIVE_IDLE_TTL_SEC`);
- `release_phase == UNKNOWN` is **never** swept;
- `ASSOC_MAX_ACTIVE` (4096) refuses new work instead of silently dropping an
  unresolved one; creating a new assoc over a live `SUPI:PSI` is refused;
- tombstones answer late duplicates (`RELEASE_COMPLETED` / `OUTCOME_UNKNOWN`).

`POST /nnwagent-admin/v1/release-recovery` is the only resume surface. It is
explicit (`operator`, `reason`, `confirm=RECOVER`, generation + txn) and reads
Owner QueryContext. It may resume **only** `r-sc` when:

1. SSM `releaseGeneration`/`releaseTxn` match;
2. `releaseN1Complete` and `releaseN2Complete` are true;
3. PFCP deletion is `ACCEPTED` or reconcile `CONFIRMED_DELETED`.

Otherwise it returns a specific `409` (`PRE_CONFIRMATION_INCOMPLETE`,
`NEEDS_OWNER_RECONCILE`, `PFCP_UNRESOLVED`, `CLEANUP_STATE_AMBIGUOUS`,
`GENERATION_MISMATCH`, `TRANSACTION_MISMATCH`, …). It never regenerates N1/N2
command bytes and never replays `r-pa`/`r-upn`/`r-se`.

Phase summary:

| Restart point | Recovery |
| --- | --- |
| `after_build` | **BLOCKED** (command bytes lost; no rebuild, no new release) |
| `before_cleanup` / partial cleanup | **BLOCKED** (cannot distinguish “not started” from partially applied without a durable step ledger) |
| `during_cleanup_pfcp` | explicit Owner reconcile; if `CONFIRMED_DELETED`, explicit `r-sc` resume |
| `before_sc_finalize` | explicit `r-sc` resume when PFCP is `ACCEPTED`/`CONFIRMED_DELETED` |

`/admin/statez` exposes bounded indexes, per-assoc release phase/generation and
the last tombstones for operator diagnosis.

## 5. Lab fault injection (inert by default)

- `OPENAMSM_TEST_PFCP_DROP_DEL_RESP=<supi:psi[,supi:psi]>` — drop only the
  Session Deletion **response**; the real request/response still happens, and
  the real PFCP timeout callback runs.
- `OPENAMSM_TEST_PFCP_DEL_SEID_OVERRIDE=<supi:psi>=<seid>` — send the deletion
  with a deliberately wrong SEID (UPF answers Session Context Not Found) while
  the target session remains. Combined with the drop seam this produces the real
  `CONFIRMED_PRESENT` case.

These seams are acceptance-only, do not fabricate a success, and are not used
in normal operation.

## 6. Verification

- C unit: `pfcp-reconcile-test` plus the P2 `release-finalize-test`,
  `pfcp-del-state-test`, `qos-delta-test` → PASS.
- Real E2E: `PFCP_UNKNOWN_EXPLICIT_RECONCILE` (deleted), `…_CONFIRMED_PRESENT`,
  `AGENT_RESTART_EXPLICIT_RECOVERY`, `CONCURRENT_RELEASE_VS_PFCP_TIMEOUT`, the
  four `AGENT_RESTART_*` gates, and the full Scheme C release/modify regression
  → PASS on the final build (evidence above).
- Python 107 unit tests → OK.

## 7. Limits

- `UPF_OBSERVATION` is attached by the authenticated operator channel and
  digest-bound; the Owner does not fetch the UPF endpoint itself.
- `CONFIRMED_PRESENT`/`UNRESOLVED` keep the context; a new deletion needs a
  separate authorized transaction (not added here).
- Owner idempotency cache is process-local; Agent assoc state is memory-only.
- Network-requested `ReleaseSMContext` is not implemented (`#10`).
