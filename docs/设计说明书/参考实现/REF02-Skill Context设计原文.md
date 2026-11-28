> 迁移来源：ca-runtime/docs/design/skill-context.md  
> 固定源提交：9db2230c172da8742ecfc5049cbfbd1a71b7828f  
> 原始状态：ca-runtime Go Runtime 参考设计；不是 Next Python Runtime 的实现证明。  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容。

---

# RuntimeHost Skill Context Identity Contract

Status: Accepted  
Version: v2 target  
Date: 2026-09-20

## 1. 目的

本文冻结 RuntimeHost Skill Context 的目标机器语义，坚持 direct-first：RuntimeHost 直接消费 immutable Skill identity、直接返回 owner-native load result，不要求经过额外 snapshot/projection DTO。

核心修正：

```text
name-only Skill lookup
  -> compatibility baseline

RuntimeSkillIdentity-scoped load
  -> target
```

但与早先草案不同：**Skill context load 不要求 execution Artifact/Variant 已经先 bind。**

`RuntimeSkillIdentity` 已经唯一标识一个 Release materialization 产生的 immutable Runtime Bundle，因此模型选中 catalog entry 后，Loader 可以先安全加载该 frozen Skill context；后续 Harness 再绑定 execution Artifact/Variant，并验证 lineage compatibility。

## 2. 复用的 owner-native contract

Target 直接复用：

```text
RuntimeSkillIdentity
  = immutable Runtime Bundle identity

Runtime Bundle SKILL.md
  = exact frozen model context

SkillBuildArtifact / Variant
  = later execution material identity
```

Routing 候选不要求一个跨仓 model-visible Catalog DTO。Agent Host 根据 owner-native SkillEligibilityDecision 中的 eligible RuntimeSkillIdentity，直接读取对应 frozen Runtime Bundle `SKILL.md` frontmatter 的 name/version/description，组装当次 routing ModelInput。

不要求新的 Host path 经过：

```text
SkillCatalogSnapshot
SkillCatalogEntry
LoadedSkillSnapshot
ModelVisibleSkillDefinition
```

这些对象可以继续存在于 ca-skill-toolchain 当前 Session Runtime / compatibility behavior 中，但不是 RuntimeHost v2 的必经跨仓 contract。
## 3. 当前 v1 compatibility baseline

当前 RuntimeHost：

```text
GET  /api/host/v1/skills
POST /api/host/v1/skills:load
POST /api/host/v1/references:read
```

当前 load/read 主要按 Skill name：

```text
LoadSkill(ctx, name)
ReadSkillReference(ctx, skillName, referencePath)
```

现有实现内部会校验 Runtime Bundle digest / model context digest，已经比读取当前源码安全；但 Host wire request 仍无法显式指定 exact RuntimeSkillIdentity。

因此 v1 是有价值的实现基线，但不是新 cross-Host target。

## 4. 正式 routing/load 顺序

RuntimeHost 不拥有 Skill eligibility/model choice，只消费 Host 已经归一化完成的 exact identity：

```text
Agent Host
  SkillEligibilityDecision
  + model choice
  -> exact RuntimeSkillIdentity
        ↓
RuntimeHost /skills:load
        ↓
owner-native Skill load result
  exact RuntimeSkillIdentity
  contentHash/modelContextDigest
  exact frozen Runtime Bundle SKILL.md
        ↓
Host native surface / ModelInputSnapshot proves actual injection
        ↓
later Harness execution Artifact/Variant binding
        ↓
GOAL_EXECUTION Toolset
```

RuntimeHost 不需要接收或生成 candidate-set projection。
## 5. RuntimeSkillIdentity 是 load authority

已有 `runtime-skill-identity.schema.yaml`：

```text
skillName
version
releaseId
runtimeBundleDigest
profile.id
profile.version
profile.digest
```

该对象由 Release materialization 冻结，已经是 Runtime Bundle 的 machine identity。

所以模型不直接提供：

```text
releaseId
runtimeBundleDigest
profile digest
```

模型只在 Host 直接组装的 routing input 中选择自然 Skill identity（例如 name/version）。Host 根据 owner-native SkillEligibilityDecision 将该 choice 唯一归一化为 exact `RuntimeSkillIdentity`；无法唯一映射时 fail closed。

## 6. Skill context load surface

保留路径：

```text
POST /api/host/v1/skills:load
```

Target request：

```yaml
contractVersion: connectionagent.skill-context/v2

identity:
  skillName: release-pdu-session
  version: 1.2.0
  releaseId: 00000000-0000-0000-0000-000000000123
  runtimeBundleDigest: sha256:...
  profile:
    id: default
    version: v1
    digest: sha256:...
```

只传 exact `RuntimeSkillIdentity` 即可。Eligibility membership 已由 Agent Host 在调用 RuntimeHost 前验证；RuntimeHost 不接管第二次 Skill eligibility authority。

Runtime 必须：

```text
resolve exact Release/Runtime Bundle by RuntimeSkillIdentity
verify releaseId + runtimeBundleDigest + profile identity
verify Runtime Bundle manifest/modelContext digest
never substitute current/latest Skill by name
```

不新增 `sourceCatalogDigest` fence 到 RuntimeHost v2；否则 Runtime 会被迫依赖 Agent-side候选集/投影语义。
## 7. Response 是 RuntimeHost owner-native result

不新增 `SkillContextLoadReceipt`，也不要求转换成 `LoadedSkillSnapshot`。

Target response：

```yaml
contractVersion: connectionagent.skill-context/v2

identity: <RuntimeSkillIdentity>
modelContextDigest: sha256:...
contentHash: sha256:...
content: |
  <exact frozen Runtime Bundle SKILL.md>

onDemandReferences:
  - path: references/on-demand/foo.md
    digest: sha256:...
```

这个 response 本身就是 RuntimeHost owner-native fact/result。

`ca-skill-toolchain LoadedSkillSnapshot` 可以继续服务旧 Session Runtime；新的 Agent Host/Benchmark 不需要先把 RuntimeHost result 转写成 snapshot 才能引用。
## 8. Loaded 与 injected 必须分开

Toolchain 现有 ADR 已冻结：

```text
skill/loaded
  = Loader 已取得内容

skill/injected
  = 该 contentHash 真正进入下一次 model request
```

因此：

```text
RuntimeHost load success
!= model actually saw the Skill context
```

离线评测还需要 `skill/injected` 或等价 ModelInputSnapshot/source refs 证明模型真正看到该内容。

## 9. On-demand reference read

保留：

```text
POST /api/host/v1/references:read
```

target 不再只靠 `{skill, referencePath}`；必须 scope 到当前 loaded `RuntimeSkillIdentity`：

```yaml
contractVersion: connectionagent.skill-context/v2
identity: <RuntimeSkillIdentity>
referencePath: references/on-demand/foo.md
```

若已有 frozen reference digest，request/response 应携带或验证该 digest。

Reference 必须来自同一 immutable Runtime Bundle，不允许因为同名 Skill 更新而漂移。

## 10. GET /skills 的定位

`GET /api/host/v1/skills` 可以继续作为 Runtime context inventory / compatibility surface，但不是新的 Skill eligibility authority。

新的 cross-Host routing 不依赖 `SkillCatalogEntry` 或 RuntimeHost `SkillDescriptor` 作为 candidate schema。Host 按 eligible RuntimeSkillIdentity 直接从 exact frozen Runtime Bundle 读取 name/version/description 并组装 ModelInput。

当前 `SkillDescriptor` / Skill Catalog API 可以继续作为兼容或迁移数据源，但不能升级成新的 cross-Host candidate authority。

## 11. 与 execution binding 的关系

Context load 后，Harness 才需要形成 exact execution binding：

```text
selected RuntimeSkillIdentity
+ model planning / optional Variant selection
        ↓
Harness bind execution Artifact / Variant
```

Binding 必须验证：

```text
bound execution Artifact/Variant
  is lineage-compatible with
selected RuntimeSkillIdentity / release / Runtime Bundle
```

如果执行 Artifact 唯一，可以 load 后立即 deterministic bind；如果 Variant 需要模型选择，则先进行 bounded Variant decision。

## 12. 与 TOOL-01 GOAL_EXECUTION 的关系

```text
selected RuntimeSkillIdentity
+ bound Artifact / Variant
+ resource/capability requirements
+ Base Envelope / Profile / Context / Environment / security policy
        ↓
TOOL-01 GOAL_EXECUTION
        ↓
Goal-scoped Runtime Resolved Execution Toolset
```

保持：

```text
RuntimeHost Skill load result != Tool permission
Skill injection != Tool permission
model Skill choice != Tool permission
```

## 13. DSH / Native Host 映射

DSH 当前 `ca_load_skill(name)` 可作为 model choice + load-request transport：

```text
model Tool Call
  -> normalize against frozen SkillCatalogSnapshot
  -> exact RuntimeSkillIdentity
  -> /skills:load v2
  -> LoadedSkillSnapshot + exact Runtime Bundle SKILL.md
  -> DSH ToolResult
  -> later ModelInput injection proof
```

Native Agent/Nanobot 可以不用 Tool 表达 selection，但最终都使用同一 `RuntimeSkillIdentity -> LoadedSkillSnapshot` 语义。

## 14. Failure semantics

至少区分：

```text
SKILL_SELECTION_NOT_IN_FROZEN_CATALOG
SKILL_SELECTION_AMBIGUOUS
SKILL_RELEASE_MISMATCH
SKILL_CONTEXT_IDENTITY_MISMATCH
SKILL_CONTEXT_UNAVAILABLE
SKILL_REFERENCE_IDENTITY_MISMATCH
SKILL_REFERENCE_NOT_FOUND
```

具体 wire error code 可在实现/schema 中冻结，但 identity mismatch 不能 fallback 到 latest-by-name。

## 15. Migration

```text
v1
  skills:load {name}
  references:read {skill, referencePath}

v2 target
  skills:load {identity: RuntimeSkillIdentity}
  references:read {identity: RuntimeSkillIdentity, referencePath}
```

迁移规则：

```text
1. 保留 endpoint paths。
2. internal LoadSkill(name) helper 可暂留。
3. external Host target path 使用 exact RuntimeSkillIdentity。
4. v1 name-only result 不得标成 LoadedSkillSnapshot v2 proof。
5. 新 M6/Benchmark evidence 使用 frozen catalog + identity + loaded + injected closure。
```

## 16. 当前实现状态

截至 2026-09-18：

```text
Toolchain SkillCatalogEntry                                    EXISTS
Toolchain RuntimeSkillIdentity                                 EXISTS
Toolchain frozen Runtime Bundle SKILL.md contract              EXISTS
Toolchain historical SkillCatalogSnapshot/LoadedSkillSnapshot  EXISTS / compatibility

RuntimeHost GET /skills                                        EXISTS
RuntimeHost /skills:load name-only v1                          EXISTS / compatibility
RuntimeHost /skills:load identity v2                           IMPLEMENTED
RuntimeHost /references:read name/path v1                      EXISTS

skill-context/v2 identity reuse design                         FROZEN
RuntimeSkillIdentity Host request                              IMPLEMENTED
RuntimeSkillIdentity exact bundle verification                 IMPLEMENTED
Go Native exact-load raw request/result evidence refs           IMPLEMENTED
Runtime execution correlation carries Skill routing/load refs   IMPLEMENTED
restart RequestLineage preserves/reconstructs Skill provenance  IMPLEMENTED
RuntimeSkillIdentity-scoped reference read                     NOT IMPLEMENTED
cross-repo RuntimeSkillIdentity schema reuse/conformance       PARTIAL
```

## 17. 不变量

```text
Consume SkillCatalogEntry directly; do not create a second routing-candidate schema.
Consume RuntimeSkillIdentity directly; do not create a second load identity.
Return RuntimeHost owner-native load result directly; do not require a loaded-receipt projection.
Do not require SkillCatalogSnapshot/LoadedSkillSnapshot/ModelVisibleSkillDefinition on the new cross-Host path.

Model Skill choice != load success.
Load success != model injection.
Skill context injection != execution authority.

Execution Artifact/Variant binding may happen after Skill load.
Execution binding must remain lineage-compatible with selected RuntimeSkillIdentity.
GOAL_EXECUTION happens after execution binding.

No latest-by-name substitution.
On-demand reference reads remain scoped to the same RuntimeSkillIdentity.
```
