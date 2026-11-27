# Studio 源码探针（固定 SHA `79bd2c3f64a90e7f0f169204c866a3218655bab1`）

本文件记录 2026-11-27 通过 GitHub Contents API（`Accept: application/vnd.github.raw`）读取的
`odango-chan/ca-skill-studio-demo` 固定提交源码；未使用工作区未提交内容。

## 1. 默认 Host Context Example 的 provenance 已实现

`site/samples/v1alpha5/files.json`（固定 blob 读取）第 192–205 行：

```json
{
  "id": "ca-context",
  "kind": "schema-bundle",
  "source": {
    "type": "git",
    "repository": "odango-chan/ca-agent-demo",
    "ref": "refs/heads/main",
    "path": "tests/fixtures/compiler/mas-v1alpha5-scheme-c/trusted/snapshots/ca-context",
    "packageId": "urn:connectionagent:ca:host-context",
    "version": "v1",
    "owner": "urn:connectionagent:owner:ca-context",
    "sourceStatus": "DEVELOPMENT_FIXTURE"
  },
  "resolvedRevision": "57e277ff9094dad93543df46910a12a1dbbaf560",
  ...
}
```

同一文件第 55–57 行显示 `mas` 的 `kind` 为 `tool-catalog`，不是正式 `interface-package`。

`experiments/ide-host/vscode/src/example-host-context-dependency.mjs` 第 10–23 行强制校验
`entry.id === "ca-context"`、`entry.kind === "schema-bundle"`、`entry.source.sourceStatus === "DEVELOPMENT_FIXTURE"`
等身份字段；第 37–41 行把完整 `source` 放入 `skillc.lock/v0.1` 的 lock entry：

```js
const declaration={id:entry.id,kind:entry.kind,source:entry.source};
const lock={...declaration,resolvedRevision:entry.resolvedRevision,
  snapshotDigest:snapshot.snapshotDigest,files:snapshot.files};
validateProjectConfiguration({skillsRoot:"skills",dependencies:[declaration],
  dependencyLock:{version:"skillc.lock/v0.1",entries:[lock]}});
```

结论：默认 Host Context Example 的 `sourceStatus=DEVELOPMENT_FIXTURE` 已校验并持久化到 lock。

## 2. 普通 ZIP importer 未形成全局 provenance

`experiments/ide-host/vscode/src/dependency-integration.mjs` 第 314–338 行的
`acquireInterfaceZip` 只保存：

```js
return {kind:"interface-package",
  source:{type:"interface-zip",
    upload:uploadName??filename,
    contentDigest:await sha256(raw),
    packageId:imported.manifest.packageId,
    version:imported.manifest.version,
    publisher:imported.manifest.publisher},
  files:imported.files};
```

全文件检索 `sourceStatus` 为 0 次命中；普通 ZIP 路径没有写入 `sourceStatus`，也没有全局
provenance/reload 策略。

## 3. 双根 MAS Example 仍非正式包类型

`files.json` 中 `mas` 为 `tool-catalog`、`ca-context` 为 `schema-bundle`；没有正式
`interface-package` 根。`#272` 只合并 request builder，`#276`（Worker/VerifyDevelopment）
仍 OPEN/DRAFT/DIRTY，因此双根 Development Build + Verify 无验收证据。

## 4. 外部对象身份

- `#272` MERGED，merge `a8633553615d786e360a62c2b0042a27ae92d9d3`，PR head `a542df4dc3c0fac1d31ce182107bad3211568470`。
- 当前 Studio `main` = `79bd2c3f64a90e7f0f169204c866a3218655bab1`。
- `#276` OPEN / Draft / `mergeable_state=dirty`，head `7d6adebaca12f09d5ddc5e04f7457b8c15aa595e`，base `3b3c4ac9d4b3a2f2e2380793d028d92f24c62c27`。
- `#296` MERGED，merge `73523df2f7538ad51d37f1eaca2a40ab07c1e9a1`；`#295` 仍为 OPEN Issue。
