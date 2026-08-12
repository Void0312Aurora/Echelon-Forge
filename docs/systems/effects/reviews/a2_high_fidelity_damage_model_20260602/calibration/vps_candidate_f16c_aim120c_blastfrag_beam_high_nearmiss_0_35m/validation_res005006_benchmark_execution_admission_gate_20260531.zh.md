# Validation RES-005/006 Benchmark Execution Admission Gate - 2026-05-31

状态：`partial_fail_closed_benchmark_execution_admission_gate / non-authoritative / hash-only`。

本文记录 `A2-RES005006-BENCH-EXECUTION-ADMISSION` 对既有 mechanism comparison hash evidence 的执行/准入加固结果。对应工具为
[damage_model.py](../../../../../../../tools/maintenance/damage_model.py) `benchmark-evidence benchmark-execution-admission`。

本文不修改 runtime、stock descriptor、source rights/provenance/stage-c 工具、`residual_register`、`game/**` 或既有 mechanism comparison 工具/测试；不把 BEC-O/TP-21 source presence、cached hash、headless reopen/recalculate 或 vocabulary hash 当 calibration；不释放 `effect_scale_authority`、`component_failure_probability_authority`、`Pk` 或 deterministic fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.res005006_benchmark_execution_admission_gate.v1` |
| `retained_artifact` | [benchmark_execution_admission_gate.json](retained_artifacts/res005006_benchmark_execution_admission_20260531/benchmark_execution_admission_gate.json) |
| `retained_artifact_sha256` | `430afb766fa278df1944e005dede11b94647ac96651a0fa3af82536a4e6c3a0c` |
| `retained_manifest` | [manifest.json](retained_artifacts/res005006_benchmark_execution_admission_20260531/manifest.json) |
| `retained_manifest_sha256` | `c7704ce2593a5b21a69019b3cbab273f1c847ffcd8a8d4461c211189ae9a49fa` |
| `input mechanism comparison status` | `partial_fail_closed_mechanism_comparison_hash_manifest` |

## 2. Gate Result

| residual | gate result | current evidence | still blocked by |
|---|---|---|---|
| `RES-005` | `blocked_fail_closed_tp21_selected_debris_outputs_missing` | TP-21 payload hash and controlled criteria vocabulary hash remain available; no source prose/table copied. | reviewer-selected TP-21 debris comparison case artifacts are missing: page/section provenance outside this package plus hash-only selected debris outputs. |
| `RES-006` | `blocked_fail_closed_beco_recalculation_not_admitted` | Local LibreOffice headless reopen/recalculate completed and retained 9 hash-only selected output comparisons. | all 9 recalculated selected output hashes differ from the cached hash anchors, so BEC-O execution evidence is not admitted. |

当前真实关闭的 residual：`none`。

## 3. BEC-O Execution Status

Local tooling detection found `LibreOffice 24.2.7.2 420(Build:2)` via `/usr/bin/libreoffice`; no dependency install or network fetch was attempted.

Execution status：`reopen_recalculate_completed_hash_only_outputs_retained`。

Admission status：`false`。The headless spreadsheet execution completed, but selected output hashes differed from cached anchors for:

| comparison id |
|---|
| `BEC-O-METRIC-DEFAULT-001` |
| `BEC-O-METRIC-DEFAULT-002` |
| `BEC-O-METRIC-DEFAULT-003` |
| `BEC-O-METRIC-DEFAULT-004` |
| `BEC-O-METRIC-DEFAULT-005` |
| `BEC-O-METRIC-DEFAULT-006` |
| `BEC-O-METRIC-DEFAULT-007` |
| `BEC-O-METRIC-DEFAULT-008` |
| `BEC-O-METRIC-DEFAULT-009` |

Raw selected spreadsheet values、formula text、temporary workbook copy、stdout/stderr 均未 retained。当前 evidence 只能说明：本机具备 headless reopen/recalculate path，且该 path 生成了 hash-only selected outputs；它不能替代 reviewer spreadsheet execution review 或 tolerance policy。

## 4. TP-21 Debris Output Requirements

TP-21 仍只保留 controlled criteria vocabulary/hash 和 selected-output requirements。当前未发现 reviewer-selected debris comparison case artifacts，因此本 gate 不定义新的 TP-21 debris comparison cases，也不复制 source prose/tables。

必须补齐的 selection artifact：

| requirement | status |
|---|---|
| reviewer-selected concrete TP-21 debris comparison cases | missing |
| page/section provenance retained outside this package | missing |
| hash-only selected debris comparison outputs | missing |
| allowed-output review confirming no prose/table dataset copy | missing |

## 5. Tolerance And Benchmark Consumption

| policy field | value |
|---|---|
| `tolerance_policy.policy_status` | `fail_closed_exact_hash_policy_only` |
| `raw_numeric_tolerance_admitted` | `false` |
| `benchmark_consumption_decision.decision` | `not_consumed_fail_closed` |
| `benchmark_consumed_for_release` | `false` |
| `release_grade_validated` | `false` |

当前只允许 exact selected hash equality 作为 hash anchor check；没有 release-grade numeric tolerance、allowed-output signoff 或 benchmark-consumption chain。Retained evidence 不得用于 release benchmark consumption。

## 6. Authority Guards

| guard | value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `runtime_authority_granted` | `false` |
| `fragment_mechanism_authority_granted` | `false` |
| `blast_mechanism_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |

## 7. Verification

```bash
python3 tools/maintenance/damage_model.py benchmark-evidence benchmark-execution-admission
pytest -q tests/architecture/damage_model/test_benchmark_evidence_admission.py
```
