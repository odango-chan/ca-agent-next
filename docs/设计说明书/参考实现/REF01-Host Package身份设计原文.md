> 迁移来源：ca-agent-demo/docs/design/package-identity.md  
> 固定源提交：57e277ff9094dad93543df46910a12a1dbbaf560  
> 原始状态：Generic Agent Host 包身份与无兼容迁移边界  
> 迁移追踪：ca-agent-next Issue #12。该仓是 Python Generic Agent Host 参考实现，不是 Next 目标架构的自动实现证明。

---

# Package Identity — Generic Agent Host

- **Status:** Frozen identity decision (2026-11-11); collision checks and the clean-wheel install smoke are complete (see §3).
- **Machine-readable authority:** `configs/component-map.yaml` → `packageIdentity`, `architectureGuards`, `migrationRules`.
- **Architecture context:** [generic-agent-host-architecture.md](generic-agent-host-architecture.md).
- **Validation:** `scripts/validate_docs.py` enforces the frozen identity marker set against `configs/component-map.yaml` and `pyproject.toml`.

## 1. Frozen identity

| Layer | Frozen value |
| --- | --- |
| GitHub repository | `odango-chan/ca-agent-demo` (not renamed) |
| Local checkout root | `ca-agent-demo` (not renamed or moved) |
| Python distribution | `ca-agent-host` |
| Import package | `ca_agent_host` |
| Import source root | `src/ca_agent_host` |
| Wheel runtime data root | `share/ca-agent-host` |
| Console script | `ca-plan` → `ca_agent_host.cli.main:main` |
| Project version | `0.4.0` (`pyproject.toml`; package metadata `ca-agent-host 0.4.0`) |
| Compatibility shim | `false` — none provided |

Only the internal Python package, module paths, resource paths and directory responsibilities changed. The GitHub repository name and the local checkout root stay `ca-agent-demo`; `ca-plan` keeps its name.

## 2. Retired identity

The pre-refactor identity is retired without a shim:

| Layer | Retired value | Disposition |
| --- | --- | --- |
| Distribution | `ca-agent-demo` | removed; not published / not installable from this tree |
| Import package | `ca_agent_demo` | removed; no re-export alias, no stub package |
| Wheel data root | `share/ca-agent-demo` | removed; no old resource directory alias |
| Production namespace | `ca_agent_demo.demo.*` | deleted or migrated by responsibility |
| Example assets | `demo/` | moved to repository-root `examples/` |

No `ca_agent_demo` package, shim, import alias or old resource path may return. Guards:

- `configs/component-map.yaml` → `packageIdentity.oldIdentityRetired`, `compatibilityShim: false`, `architectureGuards.forbiddenSourcePatterns` (`ca_agent_demo`, legacy CreatedSession class names) and `forbiddenProductionPaths` (`src/ca_agent_demo`, `src/ca_agent_host/demo`).
- `scripts/validate_docs.py` rejects a `pyproject.toml` that still mentions `ca_agent_demo`, a missing `ca_agent_host` discovery marker, example packaging under `share/ca-agent-host/examples`, and any surviving forbidden production path.
- `tests/unit/test_bootstrap.py` verifies the `src/` layout package and CLI module are importable.
- `tests/unit/test_repository_boundary_acceptance.py` verifies the generic Runtime has no `ca_agent_host.demo` dependency and no `createdsession_*.py` modules.

## 3. Collision-check evidence

The identity was frozen only after the WP0 checks. Recorded evidence (2026-11-11):

| Check | Result | Evidence |
| --- | --- | --- |
| PyPI normalized distribution name `ca-agent-host` | **No project found**: HTTP HEAD/GET for `https://pypi.org/pypi/ca-agent-host/json` returned 404 on 2026-11-11 (the GET timed out after the HEAD confirmed 404). | Executed by Lead on the final tree. |
| Import namespace `ca_agent_host` absent pre-refactor | **Absent** from the pre-refactor environment; the only installed package was `ca_agent_demo`. | `importlib.util.find_spec("ca_agent_host")` returned `None` before the rename. |
| Wheel data root `share/ca-agent-host` | **Chosen and implemented** in `pyproject.toml` `[tool.setuptools.data-files]`; no `share/ca-agent-demo` entry remains. | `pyproject.toml` |
| Console entrypoint `ca-plan` | **Unchanged name**, retargeted to `ca_agent_host.cli.main:main`; `tests/unit/test_host_cli.py::test_version_prints_package_identity` asserts `ca-plan` reports `ca-agent-host`. | `pyproject.toml`, `tests/unit/test_host_cli.py` |
| `pyproject.toml` + `uv.lock` consistency | `uv.lock` resolves `name = "ca-agent-host"`; `ca_agent_host.egg-info/PKG-INFO` reports `Name: ca-agent-host`, `Version: 0.4.0`. | `pyproject.toml`, `uv.lock`, build metadata |
| Clean-wheel build/install/import/CLI smoke | **PASS** on the final tree: wheel `ca_agent_host-0.4.0-py3-none-any.whl` built; installed into a fresh venv outside the checkout; `import ca_agent_host` → `0.4.0`; `runtime_asset_root()` → `<venv>/share/ca-agent-host`; `ca-plan version` → `ca-agent-host 0.4.0`; `ca-plan host --help` works; `ca-plan host preflight --deployment <v0.5 profile using the wheel data root>` → **READY** (`coveredOperations=12`, `coveredObservations=18`, `rootReady.establish-pdu-session=true`). | `docs/work/final-verification-20261111.md` §3. |

Version source: `pyproject.toml` declares `version = "0.4.0"` and `src/ca_agent_host/__init__.py`
declares the matching `__version__ = "0.4.0"`, so `ca-plan version` and the distribution
metadata agree.

## 4. Packaging rules

1. **Production package only.** `[tool.setuptools.packages.find]` includes `ca_agent_host`, `ca_agent_host.*`, `tools`, `tools.*` from `src` and `.`; it does not include `examples` or `tests`.
2. **Examples are not packaged.** No `share/ca-agent-host/examples*` data-file entry exists; the wheel must never contain `examples/`. The production CLI may load example commands only from a repository checkout, behind the guarded optional import.
3. **Tests are not packaged** as data files except the intentionally pinned Toolchain schema snapshot, which is upstream contract material packaged under `share/ca-agent-host/tests/contracts/ca-skill-toolchain/<sha>/`, not test fixtures.
4. **Runtime data root is `share/ca-agent-host`.** Wheel-installed Skill assets, planning surfaces, Tool contracts/registrations and pinned schemas resolve there (or from package data), not from the checkout.
5. **Package data** is limited to `ca_agent_host.agent.host` YAML/prompts/schemas, pinned Integration contracts (`ca_provider_5gc`, `env_fabric`) and the `tools.adapters.open5gs` README.
6. **No old-identity aliases.** Do not add a `ca_agent_demo` shim, a second data root, or a compatibility re-export to ease migration.

## 5. How to verify

Fast checks (no install):

```bash
grep -n 'name = "ca-agent-host"' pyproject.toml
grep -n 'share/ca-agent-host' pyproject.toml
grep -n 'ca-plan = "ca_agent_host.cli.main:main"' pyproject.toml
grep -n 'ca_agent_host' configs/component-map.yaml
uv run --no-sync python scripts/validate_docs.py
```

Full evidence (executed on the final tree; recorded in `docs/work/final-verification-20261111.md`):

```bash
uv sync
uv build --wheel
# inspect the wheel: no examples/, data under share/ca-agent-host/ only
uv run --no-sync python -c "import ca_agent_host, ca_agent_host.cli.main"
uv run --no-sync ca-plan version
# clean venv: install the built wheel, import the package, resolve packaged
# Skill/Tool resources, and run `ca-plan host preflight --deployment <v0.5 file>`
```

The clean-wheel smoke above was actually executed on the final tree; see the final verification record for the full command/output evidence.
