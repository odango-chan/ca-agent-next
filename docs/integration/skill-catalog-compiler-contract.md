# SkillCatalog and Compiler Integration Requirements

**Status:** Next-side architecture/integration requirement; not a Compiler product contract and not an implementation claim.
**Applies to:** CA-SL v1alpha5 refresh proposal, Python Agent Core / Host / Skill Resolver, and the canonical Go CA-SL Compiler.
**Current dependency state:** ca-skills refresh [PR #88](https://github.com/odango-chan/ca-skills/pull/88) is OPEN. ca-skill-compiler v2.1.0 is released, but support for the proposed contract.when compiled Artifact representation and SKILL.md-only import boundary has not been established.

## 1. Ownership

| Concern | Owner | Responsibility |
|---|---|---|
| Skill source package and SKILL.md | Skill Importer / Agent Core | Read, validate basic package shape, retain Agent guidance |
| CA-SL source parsing and static validation | Go CA-SL Compiler | Parse Assurance source, validate Schema/Procedure/Predicate/CEL semantics, link and build Artifact |
| Compiled when representation | Compiler-owned versioned Artifact Contract | Define portable serialized checked program and type bindings |
| SkillCatalog | Python Agent Core / Host | Own imported Skill index, cached content/programs, active Catalog generations |
| when runtime evaluation | Python Skill Resolver / Runtime-side evaluator | Evaluate the precompiled program against each fresh Event |
| Plugin process lifecycle and Tool/Event IPC | Python Plugin Manager | Manage Plugin processes and dispatch extensions; no SkillCatalog ownership |

The Plugin Manager MUST NOT own the SkillCatalog, load Skill packages, evaluate when, or select Skills.

## 2. Core-owned in-memory SkillCatalog

SkillCatalog is a process-local immutable snapshot. Package files remain the source of truth; the Catalog is the active in-memory read model.

Each entry contains the applicable subset of:

- stable Skill identity and package/source reference;
- the full imported SKILL.md text plus lightweight candidate metadata derived from it;
- Assurance presence and import/admission status;
- the precompiled when program and its CEL profile/type environment, when declared;
- the validated Request Schema/type information used by when;
- the admitted Artifact reference and Capability requirements.

### Residency policy

| Data | Residency | Load point |
|---|---|---|
| Skill identity and selection metadata | In memory | Import/startup/update |
| Full SKILL.md text | In memory | Import/startup/update |
| Compiled when program and type environment | In memory | Assurance import/update |
| Artifact admission metadata/reference | In memory | Artifact admission |
| Small Procedure representation | May remain in memory | Import/admission |
| Large Procedure payload | Load after Skill selection; cache per Catalog generation if useful | First selected execution |
| references/ and large knowledge assets | Lazy | Only when selected Skill/context needs them |

Semantic selection MUST use metadata derived from the already imported SKILL.md; it MUST NOT reread package files. Once a Skill is selected, the full SKILL.md text is supplied from Catalog memory. Do not add a second Skill descriptor or require a new front-matter field solely for indexing.

## 3. Catalog lifecycle

### 3.1 Startup and explicit import/update

1. Read configured Skill package roots or compiled Artifact references.
2. Read and validate SKILL.md once for each package.
3. If assurance/ is absent, register an Agent-only entry without invoking Compiler.
4. If assurance/ exists, require the complete CA-SL source trio and invoke the canonical Compiler. Invalid Assurance is an import failure; never downgrade it.
5. Inspect/Verify and perform Host Admission for a compiled Artifact.
6. Build a candidate immutable Catalog generation containing all currently active entries plus the requested successful changes.
7. Publish the candidate by one atomic active-snapshot swap.

A failed package update MUST NOT partially mutate the active Catalog. If a requested replacement fails validation, keep the previous active entry/generation. An invalid new package is not added as a candidate.

### 3.2 Event hot path

For each fresh normalized Event:

1. Validate and deduplicate the Event envelope/payload.
2. Resolve an exact continuation first. A continuation resumes the original Run and its original Catalog generation; it does not re-run Skill selection.
3. For a new Invocation, take a reference to the current active Catalog generation.
4. Evaluate each eligible precompiled when program against this Event's current event.type and input.
5. Apply CA-SL Appendix M explicit-match and unguarded semantic-candidate rules.
6. Bind the selected Skill, Artifact and Capability requirements from the same pinned generation.
7. Supply full SKILL.md from memory and load any required lazy knowledge assets.

The hot path MUST NOT scan Skill directories, read SKILL.md, parse YAML, invoke Compiler, or compile CEL. It MUST NOT cache a when result across distinct Events: the same Skill's expression may return different values for different Event payloads.

A duplicate Event is deduplicated before fresh selection; it must not cause another when evaluation. A continuation uses the original Run binding and likewise bypasses fresh selection.

### 3.3 Generation pinning and reclamation

- A fresh Invocation pins the generation used to select its Skill.
- The pinned generation supplies the same SKILL.md content, compiled program, Artifact and Capability bindings for the lifetime of that Invocation.
- An explicit update may activate generation N+1 while generation N still has active Invocations.
- Keep N alive until its final referencing Invocation completes, then reclaim it.
- A monotonically increasing process-local generation number is sufficient for this Demo. It is not a content digest, package identity or integrity mechanism.

This is explicit Skill import/update, not a filesystem watcher, automatic package hot reload or generic Plugin hot reload. No Redis, distributed cache or cross-process Catalog service is required.

## 4. when source and type environment

The authoring rules come from CA-SL v1alpha5 Appendix M:

- event.type is the normalized Event type string.
- input is the normalized Event payload.
- If when accesses any member of input, assurance/contract.yaml MUST declare requestSchema; otherwise Compiler reports CEL_INVALID.
- The Compiler statically checks the expression against the declared Request Schema and the CA-SL v1alpha5 CEL G.4 profile.
- The final expression type MUST be bool.
- when is pure and may not access Runtime Context, Observations, Tool results, Evidence, environment variables, clock or mutable Host state.

The Event Plugin validates the payload against its Event Schema. When a candidate Assurance Contract declares requestSchema, Host validates the same normalized payload against that Request Schema before evaluating the candidate's when.

## 5. Compiler-owned compiled Artifact requirements

CA-SL Appendix M intentionally delegates the physical representation of compiled when to a separate Compiler Artifact Contract. Next therefore defines the consumer requirements, not new wire-field names.

The Compiler-owned Artifact MUST carry a portable, already checked representation of the selection program. A source expression string alone is insufficient for the Event hot path.

The representation must provide, directly or by an unambiguous binding:

1. **CEL profile identity:** the exact CA-SL v1alpha5 CEL G.4 subset/semantics under which the program was checked.
2. **Portable checked program:** a serialized AST/program that a supported Python Runtime evaluator can execute without reparsing or re-type-checking the source expression.
3. **Type environment:** event.type bound to string and input bound to the exact declared Request Schema/type used by static checking.
4. **Source diagnostics:** enough source-location information to report a runtime evaluation failure against the originating contract.yaml expression.
5. **Deterministic interchange:** the same compiled program and type binding must be consumable by the supported Compiler/Runtime implementations and pass the same normative fixtures.

The exact field names, encoding and compatibility/version policy belong to the Compiler's versioned Artifact Contract. Do not infer a wire schema from this document. The Compiler owner must choose and test a portable representation (for example, a checked CEL AST format) and define how the Python evaluator consumes it. If no compatible evaluator can consume the emitted program, the Compiler owner must define a supported portable execution interface before Next implements the Resolver.

### Runtime evaluation semantics

- true: the Skill is an explicit candidate.
- false: exclude the Skill; do not reintroduce it as an unguarded semantic candidate.
- evaluation error: fail closed, exclude the Skill and record a diagnostic.
- malformed, ill-typed, unknown-field or non-boolean source: Compiler error; do not admit the Artifact.

Python MUST NOT implement a second CA-SL parser/type checker, invent a broader CEL dialect, or spawn Compiler once per Event. Runtime evaluation reuses the in-memory compiled program and current Event values.

## 6. Frozen contract and dependency gate

The released Compiler v2.1.0 and its frozen machine contracts must not be silently mutated. If the existing Artifact format cannot carry the compiled selection program and its type environment, the Compiler owner must design, version, test and release a compatible Artifact contract. The CA-SL language identifier remains connectionagent.io/v1alpha5; this does not authorize silently changing a frozen Compiler wire contract.

Until all of the following are available, Next's Assurance source import and when Resolver integration remain BLOCKED:

- the CA-SL v1alpha5 refresh is reviewed/merged and its release record points to the normative revision;
- the Compiler accepts optional Assurance and validates contract.when per Appendix M;
- the Compiler emits the versioned portable compiled when representation;
- a supported Python Runtime evaluator consumes that representation and passes shared normative fixtures;
- Inspect/Verify validates the compiled selection metadata as part of the Artifact.

SKILL.md-only import and the in-memory Catalog structure can be implemented independently of this Compiler gate.

## 7. Required acceptance evidence

| Case | Required evidence |
|---|---|
| Import-once | Startup/import reads each SKILL.md once and registers both Agent-only and Assurance Skills |
| Compile-once | Assurance import compiles/type-checks when once; later Event selection does not invoke Compiler |
| Evaluate-per-Event | Different payloads for the same Skill produce independently evaluated results |
| No hot-path file I/O | Instrumented fresh Event selection performs no Skill package reads or directory scans |
| Semantic selection | Candidate metadata and full SKILL.md come from Catalog memory |
| Atomic update | Candidate generation becomes active in one swap only after successful validation |
| Failed update | Invalid replacement leaves the previous active generation unchanged |
| Invocation pinning | In-flight Invocation continues on its original generation after a newer generation activates |
| Replay/continuation | Duplicate Event and exact continuation do not repeat fresh selection or when evaluation |
| Lazy knowledge | References are not loaded until the selected Skill needs them |
| CEL parity | Python evaluation of the Compiler-emitted program matches CA-SL normative true/false/error fixtures |

These are design/acceptance requirements. They are NOT evidence that the current Compiler or Next implementation already passes them.
