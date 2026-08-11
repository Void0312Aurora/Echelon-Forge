# MLF-9 Report Integration Result

Status: `2026-06-19` P4 initial pass.

Companion:
[missile_lethality_pk_statistical_trends_report_integration_20260619.zh.md](missile_lethality_pk_statistical_trends_report_integration_20260619.zh.md).

## Result

`tools/diagnostics/air_combat_weapon_employment_process_probe.py` now embeds an
`mlf9_statistical_trends` payload in the process-probe result. The report is
built from the probe's retained `lethality_chain_rows`, using
`tools/diagnostics/mlf9_statistical_trends.py`.

The process-probe CLI also accepts:

```bash
--mlf9_report_json_out <path>
--mlf9_group_by miss_distance_bucket,break_mode
--mlf9_confidence_level 0.95
```

When `--mlf9_report_json_out` is provided, the MLF-9 report is written as a
standalone JSON artifact. When it is omitted, the report remains embedded in
the process-probe JSON payload only.

## Retention Boundary

The integrated report declares:

- `sample_source`: `process_probe_lethality_chain_rows`
- `report_surface`: `process_probe_retained_diagnostics_artifact`
- `authority_boundary.real_world_pk`: `false`
- `authority_boundary.weapon_specific_lethality`: `false`
- `authority_boundary.target_specific_lethality`: `false`
- `authority_boundary.calibration_authority`: `false`
- `authority_boundary.reward_authority`: `false`
- `authority_boundary.entity_deletion_authority`: `false`

This keeps MLF-9 as a diagnostics/report artifact. It does not feed reward
terms, training success claims, entity deletion, runtime damage physics, or
calibration gates.

## Validation

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows
```

Result:

- `3 passed`.

## Follow-Up

Focused validation is recorded in
[missile_lethality_pk_statistical_trends_validation_20260619.md](missile_lethality_pk_statistical_trends_validation_20260619.md).
Any later closeout should keep real-world Pk and calibration held.
