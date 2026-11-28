> 迁移来源：ca-skill-studio-demo/docs/design/skill-lsp-l2-diagnostics.md  
> 固定源提交：5b666c0ef754ed32fa37c97ce2429f328c70477f  
> 原始状态：LSP 诊断、包代际与浏览器 Worker 设计  
> 迁移追踪：ca-agent-next Issue #12。以下保留源文内容；Studio 的已合并实现与部署状态以单独实现审计为准。

---

# Skill Language Service · L2-A versioned diagnostics bridge

**Status: Implemented; this document records the L2-A snapshot-session contract.**  
**Scope:** shared language analysis → LSP-shaped diagnostics and a disposable
snapshot session. The current product includes the browser LSP / Theia Worker
integration described by the companion L2-B document.

## Intent and boundary

This slice follows [Skill Language Service](skill-language-service.md) and
reuses `language/core/index.ts` from PR #103. It deliberately does **not**
modify `site/workspace.mjs`, `site/package-audit.mjs`, Theia `workbench.mjs`,
VS Code extension files, existing Visual Patch logic, or the formal Skill DSL.

### Versioned diagnostic contract

- The host supplies one complete Package snapshot per candidate analysis:
  current unsaved open text overrides persisted file text.
- Within a Package session, `generation` must increase. Each open
  TextDocument must advance its version when its contents change. Disk-only
  files can use version zero and may change between generations.
- An older asynchronous result is discarded when a newer generation arrives.
  `reset()` invalidates outstanding work and publishes empty diagnostic sets
  for the old Package. `dispose()` also prevents reuse.
- Files in another Package cannot be analyzed in the current session without
  an explicit reset. The shared core still validates Package URIs.
- A diagnostic maps only to a document with a matching relative path and
  version in the validated analysis. Unknown URI and malformed ranges are
  reported as unlocated findings, never placed on guessed text.
- Exact source offsets are JavaScript UTF-16 units; line-only warnings use
  a zero-width location at the start of their actual line. CRLF and Unicode
  offsets must be tested.
- Package-level NOT_CHECKED / BLOCKED audit status remains visible in Problems
  even when no exact source token exists. It is unlocated: do not manufacture a
  line-one squiggle, source range or clickable navigation target. Source-backed
  Package Audit findings use their exact YAML AST token ranges.
- Clearing diagnostics omits `version` rather than supplying a stale version.

### Browser Worker integration

L2-B implements the official `vscode-languageclient/browser` client and
`vscode-languageserver/browser` Worker on top of this transport-neutral
session. See [skill-lsp-l2-browser-worker.md](skill-lsp-l2-browser-worker.md)
for the snapshot protocol, diagnostic ownership and real Theia acceptance
evidence. The browser-only Theia 1.76 Chromium smoke requires Package analysis
to reach `SKILL LSP: READY`.

This document describes the reusable L2-A session contract; the combined
L2-A + L2-B implementation is now a real browser LSP server. Completion, hover,
definition/references, semantic tokens, Python type analysis and Runtime
validation remain outside this slice.

## Tests

`tests/skill-lsp-session.test.mjs` exercises diagnostic spans, CRLF/UTF-16,
unlocated failures, partial audits, concurrent stale generations, document
versions, cross-Package reset/disposal and failure-state cleanup. Existing
shared core and Theia regressions must continue to pass. CI/PAGES PASS is
only recorded after those checks actually complete.
