# MLF-10 Retained Report 集成

状态：`2026-06-19` P4 complete。

英文主文：
[missile_lethality_calibration_gates_report_integration_20260619.md](missile_lethality_calibration_gates_report_integration_20260619.md)。

## Retained 输入和输出

- 当前 evidence manifest：
  [mlf10_calibration_evidence_manifest_20260619.json](mlf10_calibration_evidence_manifest_20260619.json)
- 生成的 admission report：
  [mlf10_calibration_admission_report_20260619.json](mlf10_calibration_admission_report_20260619.json)

生成命令：

```text
python tools/diagnostics/calibration_admission_audit.py \
  --manifest_json docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/mlf10_calibration_evidence_manifest_20260619.json \
  --json_out docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json \
  --report_surface mlf10_retained_diagnostics_artifact
```

## 当前结果

| Classification | Count |
| --- | ---: |
| `engineering_proxy` | 1 |
| `retained_non_authoritative` | 1 |
| `calibration_candidate` | 0 |
| `admitted` | 0 |
| `rejected` | 1 |
| `blocked` | 4 |

Blocked records 是：

- Stage B effect-scale authority candidate；
- Stage C component-failure probability candidate；
- TP-21 selected debris evidence；
- BEC-O recalculated blast evidence。

MLF-6 保持 engineering proxy；MLF-9 保持 retained synthetic trend input；
rejected-source policy category 继续 ineligible。

## 集成边界

该集成只属于 retained diagnostics artifact：

- 不修改 runtime 参数；
- 不创建 stock descriptor；
- 没有 reward 或 entity-deletion consumer 读取报告；
- 不提升 Pk 或 deterministic-fuze claim；
- 固定 manifest 下报告是确定性的。
