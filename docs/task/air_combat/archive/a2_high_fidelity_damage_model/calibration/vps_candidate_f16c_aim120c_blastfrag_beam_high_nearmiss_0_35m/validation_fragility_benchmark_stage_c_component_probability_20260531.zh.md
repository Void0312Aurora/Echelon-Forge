# Validation Fragility Benchmark - Stage C Component Probability

状态：`blocked / benchmark_manifest_only / non-authoritative / stage_c_component_probability_only / 2026-05-31`。

本文档记录 Stage C `right_aileron_actuator` fragility benchmark evidence 包。对应工具为
[damage_model_candidate_artifacts.py](../../../../../../tools/maintenance/damage_model_candidate_artifacts.py) `component-fragility-benchmark`。
retained artifact 位于
[stage_c_fragility_benchmark_20260531](retained_artifacts/stage_c_fragility_benchmark_20260531)。

当前没有独立 `right_aileron_actuator` fragility truth / benchmark。本文档和 retained JSON 因此只能作为
blocked benchmark manifest 与 author-side comparison/probe，不能作为 authority、不能替换 stock
`synthetic_sigmoid` baseline，也不能越过 Stage B effect-scale release gate。

## 1. Gate Result

| residual | benchmark evidence status | gate result | 本包新增证据 | 仍阻塞的证据 |
|---|---|---|---|---|
| `RES-009` | `blocked_missing_independent_fragility_truth` | `blocked` | author-side three-point candidate curve；candidate row vs `synthetic_sigmoid` delta table；blocked replacement decision | 独立 actuator fragility curve / benchmark；reviewer-owned candidate-vs-truth scoring |
| `RES-010` | `blocked_pending_formal_result_closeout_and_signoff` | `blocked` | retained blocked benchmark manifest；可运行 comparison/probe entry point | formal result closeout、manifest promotion、independent signoff |
| `RES-011` | `blocked_missing_truth_labels_and_uncertainty_bounds` | `blocked` | candidate repeatability metrics；blocked calibration-score ledger | truth labels、Brier/log-loss/ECE、reviewer-accepted uncertainty bounds |
| `RES-012` | `blocked_pending_independent_result_level_audit` | `blocked` | candidate/baseline/output/truth separation trace；non-circularity guard | reviewer-owned result-level independence audit 与 benchmark/input separation signoff |

总体 gate result：`blocked`。`replacement_allowed=false`，`stage_c_component_probability_authority_ready=false`。

## 2. Benchmark Candidate Curve

当前 curve 只来自 Stage C author-side surface probe，曲线类型为
`author_side_three_point_piecewise_linear_candidate`，不是独立 fragility truth。

| probe | candidate row | standoff order key m | candidate probability | source | truth role |
|---|---|---:|---:|---|---|
| `inner` | `component-inner` | `5.5` | `0.52` | `vulnerability_evidence_row` | `candidate_input_not_independent_fragility_truth` |
| `middle` | `component-middle` | `5.8` | `0.37` | `vulnerability_evidence_row` | `candidate_input_not_independent_fragility_truth` |
| `outer` | `component-outer` | `6.0` | `0.21` | `vulnerability_evidence_row` | `candidate_input_not_independent_fragility_truth` |

候选概率随 probe 顺序单调下降，满足 author-side surface hygiene；但这只说明候选曲线可审，不说明真实 actuator fragility。

## 3. Candidate vs Synthetic Sigmoid

| probe | candidate p | synthetic_sigmoid p | delta | ratio | replacement conclusion |
|---|---:|---:|---:|---:|---|
| `inner` | `0.52` | `0.0024010146067079048` | `0.5175989853932921` | `216.57510893404597` | `replacement_blocked_no_independent_truth` |
| `middle` | `0.37` | `0.001813348290361158` | `0.3681866517096388` | `204.0424346314124` | `replacement_blocked_no_independent_truth` |
| `outer` | `0.21` | `0.0016625621124417252` | `0.20833743788755826` | `126.31107038255736` | `replacement_blocked_no_independent_truth` |

汇总指标：

| metric | value |
|---|---:|
| `mean_candidate_probability` | `0.3666666666666667` |
| `mean_synthetic_sigmoid_probability` | `0.0019589750031702626` |
| `mean_absolute_difference_vs_synthetic_sigmoid` | `0.36470769166349637` |
| `max_absolute_difference_vs_synthetic_sigmoid` | `0.5175989853932921` |
| `min_candidate_to_synthetic_sigmoid_ratio` | `126.31107038255736` |
| `max_candidate_to_synthetic_sigmoid_ratio` | `216.57510893404597` |

结论：candidate rows 与 baseline `synthetic_sigmoid` 明显不同，但 `synthetic_sigmoid` 不是 truth，candidate rows 也不是
truth。该 comparison 只能证明差异和替代风险，不能证明 accuracy。因此 `replacement_allowed=false`。

## 4. Uncertainty / Calibration

| item | result |
|---|---|
| metric status | `blocked_calibration_truth_missing_author_side_metrics_only` |
| repeatability anchor | `middle` |
| seeds | `20260526 / 20260527 / 20260528` |
| component probability CV | `0.0` |
| mechanism load CVs | fragment density `0.0`；fragment energy `0.0`；penetration margin `0.0`；blast impulse `0.0` |
| author-side repeatability result | `pass_candidate_only` |

Calibration scoring 当前全部 blocked：

| metric | status | blocked by |
|---|---|---|
| `brier_score_vs_independent_truth` | `not_computed` | `missing_independent_truth_labels` |
| `log_loss_vs_independent_truth` | `not_computed` | `missing_independent_truth_labels` |
| `calibration_curve_or_ece` | `not_computed` | `missing_independent_truth_distribution` |

覆盖限制：只有 3 个固定 seeds、3 个 near-miss probe 点、没有独立 damage/no-damage labels、没有 reviewer-accepted uncertainty interval。

## 5. Independence Trace

| layer | artifact | role | forbidden use |
|---|---|---|---|
| candidate input | `INPUT-FRAG-BENCH-001` | candidate evidence-row curve inputs | independent benchmark truth |
| synthetic baseline | `BASELINE-FRAG-BENCH-001` | delta comparator only | release-grade fragility truth |
| benchmark output | `RESULT-FRAG-BENCH-001` | blocked comparison and shortest evidence path | authority evidence |
| independent truth | missing | required independent actuator fragility curve / benchmark | n/a |

Trace status 为 `candidate_inputs_and_synthetic_baseline_separated_but_truth_missing`；
independent result audit result 为 `blocked`。本包没有把 candidate rows 与自身比较成 truth，也没有把
`synthetic_sigmoid` 当成 release-grade benchmark。

## 6. Retained Artifacts And Guards

| artifact | schema | role |
|---|---|---|
| `stage_c_fragility_benchmark.json` | `a2.stage_c_fragility_benchmark.v1` | blocked right_aileron_actuator fragility benchmark evidence manifest |
| `candidate_vs_synthetic_sigmoid_comparison.json` | `a2.stage_c_fragility_benchmark_comparison.v1` | author-side delta comparison and blocked calibration ledger |
| `manifest.json` | `a2.stage_c_fragility_benchmark_retained_manifest.v1` | retained manifest with fail-closed authority guards |

| guard | value |
|---|---|
| `authority_granted` | `false` |
| `replacement_allowed` | `false` |
| `stock_component_probability_authority` | `false` |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |
| `external_truth_present` | `false` |
| `stage_b_dependency_preserved_as_blocked` | `true` |

## 7. Reproduction

```bash
python tools/maintenance/damage_model_candidate_artifacts.py component-fragility-benchmark --retained-dir docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/stage_c_fragility_benchmark_20260531
pytest -q tests/architecture/damage_model/test_component_fragility_validation.py
```
