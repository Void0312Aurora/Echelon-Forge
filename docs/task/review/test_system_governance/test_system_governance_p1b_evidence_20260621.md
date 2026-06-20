# Test System Governance P1-B Evidence 2026-06-21

Status: `2026-06-21` complete for evidence reconciliation and refreshed by the
closeout snapshot; does not accept overall test-system health.

## Scope

This note reconciles three different evidence sources that had previously been
easy to conflate:

- Static active-test audit from `tools/runners/audit_test_system.py`.
- Pytest collection from the current non-archive working tree.
- Local Python coverage from the existing `.coverage` artifact and the retained
  coverage runner metadata.

It does not run the full test suite and does not produce C++ coverage.

## Static Active-Test Audit

Command:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format json
```

Initial observed headline values:

| Metric | Value |
| --- | ---: |
| Active tracked test files | 341 |
| Active tracked Python files | 255 |
| Active tracked `test_*.py` files | 211 |
| Static AST test items | 3064 |
| Pytest smoke entries | 51 |
| Pytest smoke files | 49 |
| Contract JSON files | 59 |
| Contract smoke specs | 10 |
| Risk-flagged Python files | 151 |
| Hidden mixin test files | 16 |
| Mixin wrapper files | 5 |

Closeout refresh:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 20
# Active test files: 341; static test items: 3145; risk-flagged Python files: 151
```

Interpret the `3064` AST item value above as the initial P1-B snapshot. The
accepted closeout snapshot uses `3145` static test items after the P2 structural
splits landed.

Interpretation:

- This audit intentionally uses `git ls-files tests`, so it reports tracked
  active files and excludes `archive` / `Archive` path segments.
- It is an AST inventory, not a pytest execution inventory. Mixin inheritance,
  parametrization, and current untracked work can make pytest collection differ.
- New untracked files in this branch are not counted by this audit until they
  become tracked.

## Pytest Collection

Command:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests --ignore=tests/archive
```

Outcome:

- `1917 tests collected in 3.46s`.
- One Eventlet deprecation warning was emitted from
  `examples/viz/runtime/viz_session.py`.
- A nanobind leak diagnostic was emitted after collection for `ef_py.Side`
  instances and type metadata.

Interpretation:

- This was the initial P1-B working-tree pytest collection surface, not the same
  thing as the tracked-file audit.
- Collection succeeded, but the nanobind diagnostic is a collection-time side
  effect that should remain visible in future runner or binding cleanup work.
- Collection count does not prove behavior coverage or domain correctness.

Closeout refresh:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests --ignore=tests/archive
# 2000 tests collected
```

The closeout count supersedes the initial `1917` snapshot for the accepted
governance slice. Future working-tree-only tests may change pytest collection
again; use the tracked active-test audit when the question is the maintained
tracked surface.

## Local Python Coverage Artifact

Local artifact:

```bash
stat -c '%n %s bytes %y' .coverage
# .coverage 98304 bytes 2026-06-20 02:39:01.832636548 +0800

source tools/maintenance/cmo_env.sh
cmo_python -m coverage debug data
# has_arcs: False
# 189 files

source tools/maintenance/cmo_env.sh
cmo_python -m coverage report --skip-empty
# TOTAL 34407 statements, 11945 missed, 65% covered
```

Closeout refresh:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m coverage report --skip-empty
# TOTAL 34376 statements, 11916 missed, 65% covered
```

The 65% total remained stable; the closeout snapshot supersedes the initial
statement/miss counts for the accepted governance slice.

Measured source roots:

- `gym_envs/`
- `python/`

Not measured by this artifact:

- C++ `src/`.
- Archived tests or archive-derived evidence.
- Whole-project capability coverage.
- Branch coverage, because `coverage debug data` reports `has_arcs: False`.

Interpretation:

- The local `.coverage` artifact is useful as a Python smoke/focused baseline
  over `gym_envs` and `python`.
- The 65% total is not a business capability acceptance metric.
- No C++ coverage conclusion follows from this artifact.

## Coverage Runner Metadata

Command:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/measure_test_coverage.py \
  --skip-python \
  --skip-cpp \
  --output-dir /tmp/cmo-coverage-metadata-p1b
```

Metadata outcome:

```json
{
  "python_sources": ["gym_envs", "python"],
  "suite": "/home/void0312/Workshop/CMO/tests/smoke/ci_smoke_suite.json",
  "cpp_object_dir": "/home/void0312/Workshop/CMO/build-workshop",
  "results": []
}
```

Interpretation:

- The retained coverage runner defaults align with the local `.coverage`
  source-root interpretation: Python coverage is scoped to `gym_envs` and
  `python`.
- The runner can produce C++ coverage through `gcovr`, but only when a suitable
  coverage-instrumented object directory is available.

## P1-B Conclusion

Accepted for P1-B:

- Static active-test audit, pytest collection, and coverage evidence now have
  separate names and boundaries.
- Initial and closeout working-tree pytest collection counts are recorded.
- Local `.coverage` source roots and exclusions are recorded.
- The collect-time nanobind leak diagnostic is retained as a residual signal.

Not accepted:

- Full-suite pass.
- Full Python coverage sufficiency.
- Any C++ coverage claim.
- Any assertion that static risk reduction equals behavior preservation.

## Follow-On

- P2-B may start against `tests/architecture/damage_model/*` now that P1-B has
  separated static audit, collection, and coverage semantics.
- P3-A should still wait for replacement checks and suite-tier decisions.
- A future C++ coverage slice needs a coverage-instrumented build directory and
  `gcovr` evidence, not the Python `.coverage` file.
