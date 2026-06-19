# MLF-10 Admission Audit Tooling

Status: `2026-06-19` P3 complete.

Chinese companion:
[missile_lethality_calibration_gates_audit_tooling_20260619.zh.md](missile_lethality_calibration_gates_audit_tooling_20260619.zh.md).

## Implementation

- Tool:
  [mlf10_calibration_admission.py](../../../../../../tools/diagnostics/mlf10_calibration_admission.py)
- Focused tests:
  [test_mlf10_calibration_admission.py](../../../../../../tests/tools/test_mlf10_calibration_admission.py)
- Contract:
  [missile_lethality_calibration_admission_contract_20260619.md](missile_lethality_calibration_admission_contract_20260619.md)

The tool reads an `mlf10.calibration_evidence_manifest.v1` object, recalculates
every evidence decision, and writes an
`mlf10.calibration_admission_report.v1` report. It does not trust an input
`admitted` label and does not modify runtime state.

## Covered Decisions

Focused fixtures cover:

- admitted `effect_scale_authority` after every v1 gate passes;
- retained engineering proxies;
- retained MLF-9-style synthetic reports;
- fail-closed rights and source gates;
- v1-forbidden Pk requests;
- rejected sources;
- manifest-level non-claim failures;
- CLI retained-report output;
- the current repository manifest with zero admitted evidence.

## Validation

```text
python -m py_compile \
  tools/diagnostics/mlf10_calibration_admission.py \
  tests/tools/test_mlf10_calibration_admission.py

python -m pytest -q -p no:cacheprovider \
  --basetemp Temp/mlf10-pytest-current \
  tests/tools/test_mlf10_calibration_admission.py
```

Result: `7 passed`.

## Boundary

The positive admitted fixture proves only that the contract has a reachable
positive branch. It does not admit repository evidence. The current repository
manifest remains fail-closed.
