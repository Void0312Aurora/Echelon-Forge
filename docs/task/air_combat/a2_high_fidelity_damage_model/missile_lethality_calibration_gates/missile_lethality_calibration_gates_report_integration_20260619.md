# MLF-10 Retained Report Integration

Status: `2026-06-19` P4 complete.

Chinese companion:
[missile_lethality_calibration_gates_report_integration_20260619.zh.md](missile_lethality_calibration_gates_report_integration_20260619.zh.md).

## Retained Inputs And Outputs

- Current evidence manifest:
  [mlf10_calibration_evidence_manifest_20260619.json](mlf10_calibration_evidence_manifest_20260619.json)
- Generated admission report:
  [mlf10_calibration_admission_report_20260619.json](mlf10_calibration_admission_report_20260619.json)

Generation command:

```text
python tools/diagnostics/mlf10_calibration_admission.py \
  --manifest_json docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_calibration_gates/mlf10_calibration_evidence_manifest_20260619.json \
  --json_out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json \
  --report_surface mlf10_retained_diagnostics_artifact
```

## Current Result

| Classification | Count |
| --- | ---: |
| `engineering_proxy` | 1 |
| `retained_non_authoritative` | 1 |
| `calibration_candidate` | 0 |
| `admitted` | 0 |
| `rejected` | 1 |
| `blocked` | 4 |

The blocked records are:

- Stage B effect-scale authority candidate;
- Stage C component-failure probability candidate;
- TP-21 selected debris evidence;
- BEC-O recalculated blast evidence.

MLF-6 remains an engineering proxy. MLF-9 remains a retained synthetic trend
input. The rejected-source policy category remains ineligible.

## Integration Boundary

This integration is a retained diagnostics artifact only:

- no runtime parameter is changed;
- no stock descriptor is created;
- no reward or entity-deletion consumer reads the report;
- no Pk or deterministic-fuze claim is promoted;
- the report is deterministic for a fixed manifest.
