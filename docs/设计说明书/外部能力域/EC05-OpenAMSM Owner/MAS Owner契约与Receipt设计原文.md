> 迁移来源：env-openamsm/docs/mas-owner-contracts-and-receipt.md  
> 固定源提交：dc83ccbf5be54dcc7112dd43ba95ea6fa5975550  
> 原始状态：Owner v1alpha4 发布、持久 Receipt、Commit Proof 和 exact-original Reconcile 的实现设计  
> 迁移追踪：ca-agent-next Issue #12。源仓未提供独立 Owner 总体架构文档；本组原文是 Owner 设计/实现证据，Next 架构将标记为实现派生重建。

---

# MAS Owner contracts, durable receipt and exact-original reconcile

Status: **implemented in this repository; verified offline (publication/Schema
tests and the SMF build). Live acceptance on the isolated `ac` lab is recorded
by ca-agent-demo evidence and is not claimed here.**

Owner: `openamsm.smf.mas`. Packages: `urn:openamsm:mas:tool-contracts`
(`v1alpha4`). Compiler pin: `skillc v2.0.2` (`ca-skill-compiler` tag `v2.0.2`,
commit `be6fa6288515aa6da16387bf7f44388d36970a9e`).

## 1. Formal publication

`contracts/mas/operations.yaml` is the reviewed Owner declaration. It covers
only the operations the merged Scheme C Owner executes: the 13 establishment
callables and the 9 Scheme C Modify/Release callables (23 in total). The
OES-shaped legacy callables (`m0/m3/m4/m5/r2-r6`) are deliberately not
published and are listed as such in the manifest.

`contracts/mas/publish.py` deterministically generates `contracts/mas/v1alpha4/`:

| Artifact | Contents |
|---|---|
| `tool-catalog.yaml` | ToolCatalog `connectionagent.io/toolcatalog/v1alpha4`; one contract per callable with Effect, Owner outcomes, input/output `$ref`, Evidence Guarantee binding, and for MUTATION a `receiptSchema` plus a `commitProof` bound to `originalInvocationId` |
| `schemas/*.schema.json` | closed input/output JSON Schemas (`additionalProperties: false`), draft 2020-12, unique URN `$id` |
| `evidence-guarantees.yaml` | one descriptor per operation: authority, producer, subject/PDU-session scope, invocation correlation, exact selection, freshness |
| `capability-contracts.yaml` | capability → exact callable requirements (the deployment still grants them) |
| `receipt.schema.json`, `proof.schema.json` | durable receipt and terminal commit proof (`COMMITTED` / `NOT_COMMITTED`) |
| `deployment-binding.yaml` | Owner id, product/version, upstream commit, build identity (upstream tree + patch series digest), allowed deployment ids, owner-instance prefix |
| `manifest.json` | Owner identity, build identity, per-artifact digests and the publication digest |

Validation:

```bash
python contracts/mas/publish.py --check        # tree is current
CA_CLIENT_TOOLS_ROOT=../ca-client-tools \
  python -m unittest tests.test_mas_publication -v
```

The tests validate the ToolCatalog/CapabilityContracts bytes against the
vendored Compiler v2.0.2 Schemas, reject any `fixture-*` / `urn:example:` /
`wtlab:` identity, prove every MUTATION has a receipt + proof + failure class,
and cross-check the Provider typed table and the C receipt table against the
declaration.

## 2. Durable mutation receipt

Patch `patches/openamsm/0023-mas-durable-receipt.patch` adds
`src/smf/mas/common/mas-receipt.[ch]` and a minimal hook in the existing
orchestration SBI. It does not change the MAS business procedure.

An invoke may carry the trusted Host/Provider binding (private fields, never
Skill arguments):

```json
{"originalInvocationId": "...", "deploymentId": "...",
 "ownerInstanceId": "...", "callable": "UPN.MODIFY_QOS_DELTA", ...}
```

When `OPENAMSM_MAS_RECEIPT_DIR` is set:

1. an unpublished callable is refused (`400 CALLABLE_NOT_PUBLISHED`);
2. an existing receipt for the exact key is refused (`409
   DUPLICATE_ORIGINAL_INVOCATION`) — the Owner never dispatches the same
   original invocation twice, even after a restart;
3. a MUTATION writes a `PREPARED` record (temp file + `fsync` + atomic rename +
   directory `fsync`) **before** the first dispatch; failure to record refuses
   the mutation (`503 RECEIPT_UNAVAILABLE`);
4. on completion the `TERMINAL` record is written before the answer is sent and
   returned as `receipt` in the invoke response.

The key is `sha256(deploymentId, ownerInstanceId, originalInvocationId)`; the
file name is that digest. `OPENAMSM_BUILD_IDENTITY` (set by the deployment)
records the exact Owner build.

Terminal state:

| State | Meaning |
|---|---|
| `COMMITTED` | the returned Owner result proves the effect (PFCP accept, PCF transaction, local state, AN F-TEID/confirmation, local marker) |
| `NOT_COMMITTED` | the Owner proved that no effect happened (validation/compat/not-implemented rejection) |
| `UNKNOWN` | the mutation may have happened but the Owner cannot prove the final result (e.g. `qos_delta_state=PFCP_APPLIED_N1N2_FAILED`, an unknown PFCP deletion, a timeout, or a crash with a `PREPARED` record) |

The receipt embeds owner identity, original invocation, operation (callable /
MAS / op / stepId / effect), SUPI / PSI / sessionRef / Owner-private generation,
transaction correlation (correlation id, frame epoch, N4 SEID, policy
association, release txn/generation) and the result digest. An HTTP 200, the
in-process idempotency cache or a process-local "already applied" marker never
produces a receipt.

`POST /nsmf-mas-orchestration/v1/receipt` (orchestration token) returns the
receipt for the exact key. A `PREPARED` record is reported as `state=UNKNOWN`.

## 3. Exact-original reconcile

`POST /nsmf-mas-orchestration/v1/reconcile` requires the exact
`originalInvocationId` / `deploymentId` / `ownerInstanceId` plus `operator` and
`reason`. It is read-only:

- `COMMITTED` / `NOT_COMMITTED` terminal receipt → returned unchanged (idempotent); a terminal `UNKNOWN` stays open to exact-original reconcile;
- `UNKNOWN` PFCP deletion → resolved only from the existing PFCP deletion /
  reconcile state of the **same** SUPI+PSI session (`ACCEPTED`/`REJECTED`, or
  the existing `CONFIRMED_DELETED`/`CONFIRMED_PRESENT` decision). The existing
  evidence-bearing PFCP reconcile endpoint remains the capability that records
  a new operator/UPF observation;
- any other `UNKNOWN` → `resolved=false` with
  `OWNER_CANNOT_PROVE_ORIGINAL_OUTCOME`; the record stays `UNKNOWN`.

Reconcile never re-sends a mutation, never rebinds the receipt to another
invocation or generation, and never turns PFCP deletion confirmation into a
general success proof for other operations.

## 4. Crash, corruption and duplicate behavior

- A receipt file that exists but cannot be parsed still counts as an existing
  occurrence: the mutation is refused (`503`/`409`) rather than re-dispatched.
- A directory `flock` serializes the `PREPARED` check/write and terminal writes
  across processes sharing one receipt directory (one SMF is the normal
  deployment; the lock removes the check-then-write race for a second process
  or an operator tool).

`OPENAMSM_TEST_RECEIPT_CRASH_AFTER_PREPARE` is an acceptance-only seam: the SMF
exits right after the `PREPARED` fsync and before dispatch. After restart the
receipt is `UNKNOWN`, reconcile returns unresolved (unless the exact PFCP state
proves otherwise) and a duplicate invoke is refused with `409` instead of being
executed again.

## 5. Limits

- Receipts are durable Owner evidence, not a second business-state authority:
  no separate database and no new state machine.
- `sessionGeneration` is the Owner-private release/PFCP generation when the
  operation has one; otherwise it is `"0"` for that operation.
- A receipt records the Owner effect only. It does not prove RAN/UE acceptance
  beyond what the operation's completion already proves.
- Receipt storage is a local filesystem directory; TLS/PKI and log-redaction
  work are outside this change.
