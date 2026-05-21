# Maintenance README

`tools/maintenance/` holds workspace cleanup, audit, and local maintenance
helpers that are not part of the model/runtime product surface.

Current maintained helpers:

- [cmo_env.sh](cmo_env.sh)
  - Linux/macOS repository-local environment bootstrap and validation for
    `.venv`, `CMO_BUILD_DIR`, and `PYTHONPATH`.
- [cmo_env.ps1](cmo_env.ps1)
  - Windows/PowerShell repository-local environment bootstrap and validation
    for `.venv`, `CMO_BUILD_DIR`, `PYTHONPATH`, and `ef_py*.pyd` artifacts.
- [redundancy_audit.py](redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.
- [translate_docs_batch.py](translate_docs_batch.py)
  - Audits English/Chinese doc pairing coverage and batch-translates Markdown peer files through an OpenAI-compatible API.
  - Preserves Markdown link destinations by masking targets before translation and restoring them afterward.
  - Rewrites workspace-absolute repository file links into relative Markdown targets.
  - Generates and audits a bilingual cluster registry so paired docs can be checked for drift after one-sided edits.
- [wp_doc_closure_audit.py](wp_doc_closure_audit.py)
  - Audits simulation-architecture WP task/review closure, including required
    companions, acceptance review links, and WP-scoped Markdown link health.
  - Emits a read-only checklist or a generated closure summary for a closure
    subagent instead of rewriting README or review indexes on the main
    implementation path.

Maintenance guidance:

- Scripts here may be shell or Python, but they should be workspace-oriented and
  non-destructive by default.
- Maintained Linux/macOS shell workflows should prefer sourcing `cmo_env.sh`
  instead of duplicating `.venv` and build-dir detection logic.
- Maintained Windows workflows should prefer `cmo_env.ps1` instead of assuming
  WSL, `.venv/bin/python`, or Linux `.so` extension artifacts.
- Historical maintenance helpers should move to `tools/archive/legacy_scripts/`
  instead of accumulating here.
- Doc translation batches should prefer `translate_docs_batch.py` over ad hoc
  one-off scripts so file pairing and draft-note behavior stay consistent.

Recommended Linux/macOS usage:

```bash
python -m pip install pytest numpy
cmake -S . -B build-workshop -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
```

This mirrors the CI smoke boundary: install the small smoke dependency set,
build `ef_core` / `ef_py` with CMake, then use `cmo_env.sh` to expose the local
extension. Do not replace this fast loop with `pip install -e .` unless the goal
is specifically to test scikit-build editable installation behavior.

Direct script-mode entrypoints are also supported:

```bash
bash tools/maintenance/cmo_env.sh summary
bash tools/maintenance/cmo_env.sh validate
bash tools/maintenance/cmo_env.sh validate-rl
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/core/test_env_config.py
```

`validate` intentionally checks only the repository virtual environment and
local `ef_py` build artifact needed by smoke/runtime workflows. Use
`validate-rl` before RL-capable runtime tests; it imports `ef_py`, `gymnasium`,
`stable_baselines3`, and `torch` and reports the selected module locations.

Recommended Windows/PowerShell usage:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy

cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2

.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 validate-rl
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\core\test_env_config.py
```

Windows scope:

- The PowerShell helper is intended for local development smoke tests,
  structural tests, and focused runtime regressions.
- It does not define the local workstation's RL training capability. The
  default `validate` command checks build/runtime smoke prerequisites only.
  Run `validate-rl` after installing `.[rl]` or equivalent direct dependencies
  when a focused regression imports the RL stack.
- It intentionally runs beside `cmo_env.sh`; it should not replace the Linux
  CI workflow.

Recommended bilingual doc audit:

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json
```

By default this audits only the strict maintained bilingual surface
(entry/navigation pages, standards/governance, manuals, and stable plan
authority), not every dated task/history document under `docs/`.

To audit the broader shared docs tree on purpose:

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json \
  --full-tree
```

If that audit looks noisy after a large doc sweep, refresh the registry first:

```bash
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write
```

The audit compares current file hashes against the registry baseline, so a
stale baseline can look like drift even when the repo is just catching up.
The maintained hash now ignores leading machine-generated draft markers and
normalizes line endings, so Windows `CRLF` checkout noise should not turn the
entire registry into false `diverged` results by itself.

Generate or refresh the bilingual cluster registry baseline:

```bash
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write
```

If you deliberately want a full-tree registry instead of the maintained
surface registry:

```bash
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write --full-tree
```

By default, the audit skips local-only documentation surfaces that are commonly
ignored from the shared remote, including:

- `docs/Archive/`
- `docs/**/archive/`
- `docs/temp/`
- `docs/plan/results/`
- `docs/plan/architecture/review/`

To include them explicitly:

```bash
python3 tools/maintenance/translate_docs_batch.py audit --root docs --include-local-only
```

Recommended zh-to-en backfill for one maintained authority directory:

```bash
python3 tools/maintenance/translate_docs_batch.py translate \
  --root docs/plan/architecture \
  --pattern '*.zh.md' \
  --source-lang zh \
  --target-lang en \
  --only-missing
```

Normalize repo-internal links in existing Markdown files:

```bash
python3 tools/maintenance/translate_docs_batch.py rewrite-links \
  --files docs/task/flight_dynamics/program/*.md
```

Audit a WP closure package before assigning or accepting a closure lane:

```bash
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP9 --json
```

Use `--strict` when error-level closure gaps should fail the command. Warnings
are intended to be closure-subagent work items rather than main-lane blockers.

Required API environment variables for translation:

- `DOCS_TRANSLATE_BASE_URL`
- `DOCS_TRANSLATE_MODEL`
- `DOCS_TRANSLATE_API_KEY`

Supported fallback names loaded from repo-local `.env`:

- `BASE_URL`
- `MODEL`
- `API_KEY`
