# MLF-9 Pk Statistical Trends Dispatch Queue

Status: `2026-06-19` queue closed for the accepted / archived
[MLF-9 Pk Statistical Trends](README.md) slice. `MLF9-Q0` through `MLF9-Q6`
are complete.

## Queue

| Item | Cluster | Owner | Write set | Timing | Required return |
| --- | --- | --- | --- | --- | --- |
| `MLF9-Q0` | `MLF9-P0` | main thread | MLF-9 docs and parent A2 README files | Now | Subproject exists, parent links exist, docs diff check result |
| `MLF9-Q1` | `MLF9-P1` | main thread or read-only diagnostics worker | MLF-9 inventory/status docs only | After Q0 | Accepted upstream fields, missing joins, safe implementation write sets |
| `MLF9-Q2` | `MLF9-P2` | main thread | MLF-9 contract docs, optional schema tests | After Q1 | Metric contract with row shape, denominator, buckets, uncertainty, non-claims |
| `MLF9-Q3` | `MLF9-P3` | implementation worker | diagnostics/replay tooling and focused tests | After Q2 | Deterministic fixture reports and focused validation |
| `MLF9-Q4` | `MLF9-P4` | integration worker | report artifacts, probe/docs integration | After Q3 | Report exposure with no reward/training/calibration leakage |
| `MLF9-Q5` | `MLF9-P5` | main thread | validation/status docs; scoped tests if needed | After Q4 | Focused and smoke validation outcomes |
| `MLF9-Q6` | `MLF9-P6` | main thread | MLF-9 closeout docs and parent indexes | After Q5 | Accepted/held decision, residual map, archive/index sync |

## Active Packet

No active packet remains for the accepted simulation-trend/report slice. The
evidence package has been moved under the parent A2 local archive, and the old
active path is a compatibility pointer.

Expected validation:

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows
```

## Hold Conditions

- Stop if the available upstream rows cannot define an honest denominator.
- Stop if implementation would need to modify archived MLF evidence
  evidence instead of consuming accepted outputs.
- Stop if a requested output would imply real-world Pk or weapon-specific
  calibration before MLF-10.

## Completed Packets

| Date | Item | Status | Evidence |
| --- | --- | --- | --- |
| `2026-06-19` | `MLF9-Q0` | pass | Subproject docs and parent A2 links created; `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model` passed; local Markdown link inspection over 12 files found 0 missing links. |
| `2026-06-19` | `MLF9-Q1` | pass | Inventory names accepted MLF-5..8 inputs, diagnostics row gaps, safe write sets, and held calibration/debris/reward surfaces. |
| `2026-06-19` | `MLF9-Q2` | initial pass | Metric contract defines row source, denominators, outcome buckets, grouping fields, and uncertainty labels; diagnostics row surface now exposes `structural_breakup`; focused validation reports `47 passed`. |
| `2026-06-19` | `MLF9-Q3` | initial pass | `tools/diagnostics/mlf9_statistical_trends.py` summarizes explicit row fixtures into bounded trend payloads; `tests/tools/test_mlf9_statistical_trends.py` reports `2 passed`. |
| `2026-06-19` | `MLF9-Q4` | initial pass | Process probe embeds `mlf9_statistical_trends` and can write `--mlf9_report_json_out`; focused integration validation reports `3 passed`. |
| `2026-06-19` | `MLF9-Q5` | pass | Focused validation reports `50 passed`, clean `git diff --check`, and 0 missing local Markdown links over 20 docs. |
| `2026-06-19` | `MLF9-Q6` | pass | Acceptance record marks the bounded simulation-trend/report slice accepted / archived; real-world Pk and calibration remain held; old active path is a compatibility pointer. |
