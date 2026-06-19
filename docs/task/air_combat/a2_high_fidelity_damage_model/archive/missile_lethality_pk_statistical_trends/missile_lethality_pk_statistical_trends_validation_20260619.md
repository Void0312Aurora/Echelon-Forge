# MLF-9 Focused Validation

Status: `2026-06-19` P5 pass.

Companion:
[missile_lethality_pk_statistical_trends_validation_20260619.zh.md](missile_lethality_pk_statistical_trends_validation_20260619.zh.md).

## Scope

This validation covers the current MLF-9 slice:

- `structural_breakup` row-surface exposure in the process probe.
- Deterministic MLF-9 trend extraction from explicit rows.
- Process-probe retained report integration through `mlf9_statistical_trends`
  and optional `--mlf9_report_json_out`.
- Documentation and local Markdown links for the MLF-9 working surface.

It does not validate real-world Pk, weapon-specific lethality, target-specific
lethality, public-outcome calibration, reward shaping, or entity deletion.

## Commands

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py

PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py::DiagnosticsProcessProbeSnapshotTests::test_run_probe_payload_and_chain_csv_include_lethality_chain_rows \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/tools/test_mlf9_statistical_trends.py

git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model \
  tools/diagnostics \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

Local Markdown link inspection covered the parent A2 README files and the MLF-9
directory.

## Results

- `py_compile`: pass.
- Focused pytest: `53 passed`.
- `git diff --check`: pass.
- Local Markdown link inspection: `20 markdown files; missing local links: 0`.

## Acceptance Readiness

The current slice is ready for `MLF9-Q6` closeout discussion. The accepted
portion should be limited to deterministic simulation-trend extraction and
retained diagnostics/report exposure. Calibration and real-world Pk remain
held.

## Residuals

- MLF-10 must own calibration gates, public outcome admission, and any future
  weapon/target-specific probability discussion.
- MLF-9 reports should remain labeled as synthetic simulation trends whenever
  they are exported or cited.
