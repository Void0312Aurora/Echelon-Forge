# MLF-10 Focused Validation

Status: `2026-06-19` P5 pass.

Chinese companion:
[missile_lethality_calibration_gates_validation_20260619.zh.md](missile_lethality_calibration_gates_validation_20260619.zh.md).

## Validated Surface

- P1 calibration-like evidence inventory.
- P2 admission contract and report schema.
- P3 deterministic admission-audit tooling.
- P4 current repository evidence manifest and retained report.
- Adjacent MLF-9 trend-report behavior.
- Existing A2 source-admission guardrails.

This validation does not test real-world Pk, deterministic fuze reliability,
weapon-specific lethality, target-specific lethality, runtime parameter
retuning, reward authority, or entity deletion.

## Commands And Results

```text
python -m py_compile \
  tools/diagnostics/calibration_admission_audit.py \
  tools/diagnostics/mlf9_statistical_trends.py \
  tests/tools/test_calibration_admission_audit.py \
  tests/tools/test_mlf9_statistical_trends.py
```

Result: pass.

```text
python -m pytest -q -p no:cacheprovider \
  --basetemp Temp/mlf10-validation-pytest \
  tests/tools/test_calibration_admission_audit.py \
  tests/tools/test_mlf9_statistical_trends.py \
  tests/architecture/damage_model/test_source_admission_audit.py
```

Result: `21 passed`.

The retained report was regenerated to `Temp/mlf10-validation-report.json` and
compared byte-for-byte with
[mlf10_calibration_admission_report_20260619.json](mlf10_calibration_admission_report_20260619.json).
Result: match.

`git diff --check` passed. Local Markdown validation covered 20 archive
Markdown files and 132 local links with `missing_local_links=0`.

## Current Evidence Decision

| Classification | Count |
| --- | ---: |
| `engineering_proxy` | 1 |
| `retained_non_authoritative` | 1 |
| `calibration_candidate` | 0 |
| `admitted` | 0 |
| `rejected` | 1 |
| `blocked` | 4 |

## P5 Decision

The gate infrastructure is ready for closure. Calibration authority remains
held because the current report admits no evidence.
