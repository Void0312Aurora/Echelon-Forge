# Validation Run Manifest - Stage B Effect Scale

状态：`author_side_executed / non-authoritative / release_blocked / stage_b_effect_scale_only`。

本文档固化 2026-05-31 的 Stage B `effect_scale_authority_only` author-side run manifest 与
benchmark/result execution record。它只减少 author-side 未完成项，不替代 independent review，
不创建 runtime descriptor，也不授予 `effect_scale_authority`、`component_failure_probability_authority`、
`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `run_id` | `STAGE-B-ES-RUN-20260531-001` |
| `run_status` | `author_side_executed_non_authoritative` |
| `release_target` | `effect_scale_authority_only` |
| `seed` | `20260529` |
| `sample_count` | `4096` |
| `standoff_m` | `0.35` |
| `closure_mps` | `900.0` |
| `scope_probe_standoffs_m` | `0.25 / 0.35 / 0.45` |
| `scope_probe_closures_mps` | `700 / 900 / 1100` |
| `closeout_tool_ref` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `release-governance effect-scale-closeout` |
| `retained_closeout_artifact_ref` | [stage_b_release_closeout.json](retained_artifacts/stage_b_effect_scale_20260531/stage_b_release_closeout.json) |

## 2. 复现命令

```bash
python tools/maintenance/damage_model.py release-governance effect-scale-closeout --output docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/stage_b_effect_scale_20260531/stage_b_release_closeout.json
python tools/maintenance/damage_model.py candidate-artifacts effect-scale-result-pack
python tools/maintenance/damage_model.py release-governance effect-scale-readiness
```

这些命令只生成 candidate / author-side artifact。即使 hard gates 全部通过，
`hard_gate_pass_is_release` 仍必须保持 `false`。

## 3. Benchmark / Result Execution Record

| 项 | 当前结果 |
|---|---|
| `criteria_count` | `18` |
| `passed_criteria_count` | `18` |
| `failed_criteria_count` | `0` |
| `failed_criteria_ids` | `[]` |
| `all_hard_gates_pass` | `true` |
| `hard_gate_pass_is_release` | `false` |
| `execution_status` | `author_side_hard_gates_passed_non_release` |

当前 author-side 结果包固定了下列内容 hash：

| `artifact_id` | artifact | `sha256` | 当前角色 |
|---|---|---|---|
| `ART-SCAFFOLD-001` | validation scaffold snapshot | `393feb97603dc618e315888732c6e6c5f02990b84ce1dfa1c28f7adc42e293cc` | candidate benchmark hygiene input |
| `ART-SCOPE-PROBE-001` | scope boundary probe snapshot | `4321242f12c6f5878f19e8989d05e46b87f96ece37a00f1f1470e72584e2d1cf` | candidate scope / leakage audit input |
| `ART-STAGE-B-SNAPSHOT-001` | Stage B hard-gate snapshot | `d2b4c32e5ffa18bab86fd6645be8e5df1584384d49e1f2c9762d472997e4eb36` | candidate hard-gate result table input |

## 4. Focused Residual Gate Result

| residual | 当前 gate result | author-side closeout | release result |
|---|---|---|---|
| `RES-007` | `author_scope_closeout_passed_pending_independent_review` | 三点 near-miss bucket probe 已执行并通过 monotonic / bucket consistency checks。 | `blocked`，仍需 bucket sensitivity 与 independent review。 |
| `RES-008` | `author_scope_closeout_passed_pending_independent_review` | `beam/high` scope guard、closure probe 与 out-of-scope rejection 已固化。 | `blocked`，candidate closure-sensitive response 仍不是 reviewed closure physics。 |
| `RES-010` | `author_execution_record_passed_pending_independent_review` | run manifest、result execution record 与 artifact hash chain 已固化。 | `blocked`，仍缺 independent reviewer signoff；formal validation manifest 不得提升为 `validated`。 |
| `RES-011` | `author_uncertainty_closeout_passed_pending_independent_review` | seed-window CV 结果已纳入 closeout。 | `blocked`，仍缺 coverage 解释和 independent uncertainty review。 |
| `RES-012` | `author_independence_trace_complete_pending_independent_review` | benchmark/input dependency trace 已固化。 | `blocked`，仍缺 independent benchmark/input separation audit。 |

## 5. Release Decision

| 字段 | 值 |
|---|---|
| `release_ready` | `false` |
| `release_blocked` | `true` |
| `current_hard_gate_snapshot_pass` | `true` |
| `hard_gate_pass_is_release` | `false` |
| `blocked_even_when_hard_gates_pass` | `true` |
| `stage_c_component_probability_release_included` | `false` |
| `stock_runtime_authority_granted` | `false` |

## 6. Remaining Release Dependencies

| dependency | 状态 | 关联 residual |
|---|---|---|
| independent review | `blocked` | `RES-007/008/010/011/012` |
| release-grade provenance / surrogate identity | `blocked` | `RES-001/002` |
| stock runtime descriptor | `forbidden` | `RES-013/014-boundary` |

## 7. 当前判定

当前 Stage B effect-scale author-side run / result closeout 已完成到可交付 independent review 的形状；
但 release 仍被 independent review、release-grade provenance / identity 和 stock boundary 阻塞。
不得把本次 `18/18` hard-gate pass 叙述为 release-ready。
