# Test System Governance Dispatch Queue 2026-06-20

Status: `2026-06-21` accepted queue for the first governance and
simplification wave; remaining blockers are retained in
[Test System Residual Governance](../../work/issues/test_system_residual_governance/README.md).

## Dispatch Principles

- Assign exactly one finite cluster from
  [test_system_governance_task_clusters_20260620.md](test_system_governance_task_clusters_20260620.md).
- Keep write sets disjoint unless a main-thread integration pass explicitly
  serializes them.
- Every packet must report commands, outcomes, remaining paths, behavior risks,
  and integration notes.
- Do not mark a docs-only pass as test-system acceptance.

## Queue

| Queue ID | Cluster | Owner | Goal | Write set | Validation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `Q0` | `P0-A` | Main thread | Create branch and standards-compliant subproject shell. | `docs/task/review/test_system_governance/**`, `docs/task/review/README*` | Link inspection; `git status --short`. | pass |
| `Q1` | `P1-A` | Main thread | Keep audit runner and runner tests green. | `tools/runners/audit_test_system.py`, `tests/runners/test_audit_test_system.py`, `tests/README.md` | `cmo_python -m pytest -q tests/runners`; ruff. | pass |
| `Q2` | `P1-B` | Diagnostics worker | Reconcile audit counts, pytest collect, and coverage report semantics. | Current status plus P1-B evidence note. | `cmo_python -m pytest --collect-only -q tests --ignore=tests/archive`; coverage report if available. | pass |
| `Q3` | `P2-A` | Implementation worker | Reduce `tests/tools` oversized snapshot tests. | `tests/tools/test_airframe_geometry_manifest.py`, `tests/tools/test_airframe_geometry_review_cli.py`, shared fixtures as needed. | Focused pytest for touched tests; audit markdown before/after. | accepted with dependency-complete behavior residual |
| `Q4` | `P2-B` | Implementation worker | Consolidate damage-model candidate/closeout test patterns. | `tests/architecture/damage_model/*.py`, helpers. | Focused pytest for touched files; audit markdown before/after. | accepted oversized single-test sweep; file-level residual retained |
| `Q5` | `P2-C` | Implementation worker | Clarify or justify `weapon_guidance_realism` mixin test collection. | `tests/runtime/air_combat/weapon_guidance_realism/*.py`, local docs if needed. | Pytest collect and focused pytest for package. | accepted documentation; behavior failure retained |
| `Q6` | `P3-A` | Integration worker | Align suite tiers after replacement checks land. | `tests/smoke/*.json`, `tests/suites/README.md`, `tests/README.md`. | Manifest tests and suite runner smoke command. | pass |
| `Q7` | `P4-A` | Main thread | Record accepted slice and residual map. | `test_system_governance_acceptance_20260620.md`, status docs. | Runner tests, focused tests, audit command. | pass |
| `Q8` | `P5-A` | Main thread | Sync indexes and archive/current boundary for the accepted slice. | `README*`, parent `README*`, archive README. | Local link inspection. | pass for current slice |

## Packet Template

```md
queue id:
cluster:
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Retained Blockers

- [Test System Residual Governance](../../work/issues/test_system_residual_governance/README.md)
  owns the current blockers after this queue's accepted slice.
- P2-A split the primary airframe tests, but behavior preservation still needs a
  dependency-complete execution rather than a skip.
- P2-B split ten damage-model files into focused tests and removed remaining
  `oversized_test_item` findings under `tests/architecture/damage_model`; the
  file-level literal/source-scan concentration remains a data-contract or tier
  decision.
- P2-C documented `weapon_guidance_realism` as a five-wrapper local/focused
  mixin suite and collected 192 tests, but full package execution reported
  45 failed, 167 passed, and 221 subtests passed. Do not promote this package
  into smoke while that behavior/test-expectation drift remains.
