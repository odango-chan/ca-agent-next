> 迁移来源：ca-runtime/docs/design/predicate-runtime.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# Predicate Runtime 与 Expression 边界

Status: Accepted  
Version: v1.0  
Date: 2026-09-17

## 1. 定位

Runtime Predicate 负责把**可信 Observation/Evidence**确定性地映射为 Procedure/Assurance 可消费的判断结果。它不调用 LLM，也不让 Provider/Adapter直接拥有 `PASS / FAIL / UNKNOWN` 语义。

```text
trusted Observation source
        ↓
Normalized Observation / Evidence
        ↓
Runtime Predicate evaluator
        ↓
PASS / FAIL / UNKNOWN
        ↓
Verify / bounded Decision / Assurance / Recovery policy
```

Benchmark Oracle 不进入该链；模型可见 business query 也不自动成为 trusted Evidence。

## 2. Ownership

Observation/Evidence adapter负责：

```text
acquire concrete fact
normalize provider/environment-specific shape
attach source/binding/provenance
report missing/invalid/stale acquisition knowledge
```

Runtime Predicate evaluator负责：

```text
frozen definition/expression
value/result conversion
tri-state fail-closed semantics
Procedure/Assurance-facing result
```

Adapter不得直接返回 Runtime Predicate verdict来绕过 frozen contract。

## 3. Tri-state

Runtime需要保留：

```text
PASS
FAIL
UNKNOWN
```

缺失、无效、过期、无法匹配或 evaluation error不能被默认升级成 PASS。具体 site可以有更严格规则，但未知事实必须 fail closed。

## 4. PredicateDefinition / bundle material

Predicate定义来自经过 Toolchain build/freeze 的 immutable Artifact/Runtime Bundle material。Production Runtime不回读 author workspace，也不允许 deployment adapter选择另一份未冻结 definition。

目标链：

```text
authoring predicate source
  -> Toolchain validate/freeze
  -> Artifact / Runtime Bundle
  -> Runtime load/verify
  -> Predicate evaluator
```

## 5. Observation provenance

Predicate只消费满足 Runtime contract 的 Observation/Evidence。至少需要能够验证：

```text
source identity
binding identity
observation/catalog identity
freshness / observation time where required
```

身份缺失或 mismatch属于 contract failure；事实本身 missing/invalid/stale通常形成 `UNKNOWN`，具体错误分类以 machine contract为准。

## 6. Expression / CEL

Runtime 当前存在 CEL-based Predicate/Observation expression site。目标不是在 Runtime 中维护私有 CEL 方言，而是与 Nodus `cel-v1` 一类 shared profile/conformance 对齐。

正确职责：

```text
Toolchain Compile/Check
  = authoring-time static admission

Runtime Compile/Program materialization
  = frozen source在兼容 profile下生成进程内 executable

Runtime Eval
  = data-dependent evaluation
```

Artifact通常冻结 expression source + profile identity，而不是冻结进程内 `cel.Program`。

## 7. Static admission 与 Runtime evaluation

使用 Dyn root 时，Toolchain只能拒绝静态可证明的问题，例如：

```text
syntax/check error
undeclared root
forbidden extension/profile mismatch
Bool site可静态证明返回非 Bool
```

以下错误可能必须在 Runtime data-dependent evaluation时发现：

```text
Dyn field absent
real value type mismatch
map/list content-dependent access failure
native result conversion failure
```

因此不能把 Runtime expression compile/eval简化成“只做重复校验”。

## 8. Site contract

不同 expression site有不同领域返回合同：

```text
Procedure applicability / Observation when / Predicate
  -> Bool / tri-state conversion

Observation scope
  -> object/map-like normalized scope according to Runtime contract
```

共享 `cel-v1` 只能固定 mechanics/conformance，不能擅自把所有 site结果收敛成同一种语义。

## 9. Legacy shorthand

历史 compact scope/shorthand 若仍存在，只能作为显式 compatibility seam：

```text
artifact/profile = cel-v1
  -> CEL failure is error

explicit legacy artifact/profile
  -> legacy compatibility adapter
```

不能长期用“CEL compile失败后猜另一种格式”作为标准格式探测。

## 10. Provider independence

Provider output结构可以不同：free5GC/Open5GS/Service Fabric/MCP adapter都可能有不同字段。共享 Runtime不直接硬编码具体 backend JSON path。

```text
provider-specific value
  -> deployment Observation adapter
  -> normalized Observation/Evidence
  -> shared Predicate semantics
```

## 11. 不变量

```text
Predicate semantics belong to Runtime, not Provider adapters.
Unknown/missing evidence fails closed.
Agent-visible query != trusted Runtime Evidence.
Benchmark Oracle != Runtime Predicate.
Toolchain static admission != Runtime data-dependent evaluation.
Shared CEL profile does not move Runtime site semantics into Nodus.
```