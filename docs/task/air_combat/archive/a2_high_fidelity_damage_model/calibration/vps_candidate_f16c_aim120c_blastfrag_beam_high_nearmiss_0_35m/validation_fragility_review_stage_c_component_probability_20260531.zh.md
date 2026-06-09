# Validation Fragility Review Gate - Stage C Component Probability

状态：`blocked / candidate / non-authoritative / stage_c_component_probability_only / 2026-05-31`。

本文档记录 Stage C `right_aileron_actuator` fragility review gate。对应工具为
[a2_blastfrag_stage_c_fragility_review_gate.py](../../../../../../tools/maintenance/a2_blastfrag_stage_c_fragility_review_gate.py)。

本 review gate 只审查当前 retained prep/result surface 是否足够清楚地 fail-closed。它不创建
stock descriptor，不授予 `component_failure_probability_authority`、`pk_authority` 或
`deterministic_fuze_authority`，也不能越过 Stage B effect-scale release gate。

本轮 review gate 已消费上一轮 retained Stage C fragility benchmark artifact：
[stage_c_fragility_benchmark_20260531](retained_artifacts/stage_c_fragility_benchmark_20260531)。
该 artifact 提供 candidate-vs-`synthetic_sigmoid` delta evidence，但仍不是 independent truth。

## 1. Gate Result

| residual | review gate result | 当前可 review-pass 的项 | 仍阻塞的证据 |
|---|---|---|---|
| `RES-009` | `blocked` | `right_aileron_actuator` matrix identity、load-gate coverage、baseline replacement path fail-closed、candidate surface monotonicity、retained candidate-vs-`synthetic_sigmoid` delta evidence | 独立 component fragility curve / benchmark；candidate evidence-row 与独立 fragility truth 的 reviewer-owned comparison |
| `RES-010` | `blocked` | pre-run criteria entry、author-side result pack、review artifact inventory | `validated/passed` manifest、formal reviewer-owned result closeout、independent signoff |
| `RES-011` | `blocked` | fixed-seed author repeatability probe、uncertainty closeout plan | calibration / coverage scoring、三点 author-side probe 之外的 scenario spread、reviewer-accepted uncertainty bounds |
| `RES-012` | `blocked` | input/result separation trace、Stage B dependency interlock | reviewer-owned result-level independence audit、non-circular benchmark/input separation signoff |

结论：当前只能说 Stage C fragility review surface 已经可审、且 fail-closed 边界清楚；不能说
`RES-009/010/011/012` 已 close，也不能释放 component probability authority。

`RES-009` 的精确状态是：`candidate_vs_synthetic_delta_evidence_present=true`，
`independent_truth_present=false`，`replacement_allowed=false`。

## 2. Review-Passed Subchecks

| check | source matrix | review result | release effect |
|---|---|---|---|
| `FRAG-REVIEW-001` | `FRAG-MAT-CP-001` | `review_passed` | component identity 可作为 review entry，不是独立 truth |
| `FRAG-REVIEW-002` | `FRAG-MAT-CP-002` | `review_passed` | load-gate coverage 可供 reviewer audit，不释放 authority |
| `FRAG-REVIEW-003` | `FRAG-MAT-CP-003` | `review_passed` | baseline 仍为 `synthetic_sigmoid`，replacement 继续 blocked |
| `FRAG-REVIEW-004` | `FRAG-MAT-CP-004` | `review_passed` | candidate probabilities 在 inner/middle/outer probe 上单调，但仍只是 author-side behavior |
| `FRAG-REVIEW-005` | `FRAG-MAT-CP-005` | `review_passed` | fixed-seed repeatability 可交给 uncertainty reviewer，coverage 仍缺 |
| `FRAG-REVIEW-006` | `FRAG-MAT-CP-006` | `review_passed` | author-side separation trace 存在，independent result-level audit 仍缺 |
| `FRAG-REVIEW-007` | `FRAG-MAT-CP-007` | `review_passed` | Stage B blocked dependency 被保留，Stage C 不得独立 promotion |

## 3. Baseline Replacement Path

当前 baseline component probability source 仍是 `synthetic_sigmoid`。candidate surface 的三条 evidence row 为：

| probe | candidate row | probability source | current replacement result |
|---|---|---|---|
| `inner` | `component-inner` | `vulnerability_evidence_row` | `blocked` |
| `middle` | `component-middle` | `vulnerability_evidence_row` | `blocked` |
| `outer` | `component-outer` | `vulnerability_evidence_row` | `blocked` |

replacement path 已定义但未授权。最短补证路径是：先取得覆盖 frozen Stage C load band 的独立
`right_aileron_actuator` fragility benchmark，再用 reviewer-owned scoring 比较 candidate
evidence-row probabilities，最后在独立 signoff 后另走 stock descriptor admission review。

review gate 已读取 retained comparison artifact：
`candidate_vs_synthetic_sigmoid_comparison.json`。该 comparison 的 point count 为 `3`，且 SHA
校验通过；它只能证明 candidate rows 与 `synthetic_sigmoid` 存在 delta，不能证明 candidate
accuracy，也不能替代 independent actuator fragility truth。

## 4. Formal Result / Uncertainty / Independence

| lane | current review result | missing closeout |
|---|---|---|
| formal result closeout | `blocked` | validation manifest 仍未 reviewer-promoted；缺 formal result table 与 independent signoff |
| uncertainty | author repeatability `review_passed`，uncertainty closeout `blocked` | 缺 calibration/coverage scoring、seed/scenario spread、reviewer-accepted bounds |
| independence | author trace `review_passed`，independent audit `blocked` | 缺 result-level non-circularity audit 与 independent reviewer signoff |

## 5. Stage B / Upstream Interlock

| field | value |
|---|---|
| `stage_b_status` | `blocked_non_authoritative_stage_b_release_candidate` |
| `stage_b_release_target` | `effect_scale_authority_only` |
| `dependency_preserved_as_blocked` | `true` |
| `still_blocks_stage_c_authority` | `true` |
| `stage_c_authority_promotion_allowed` | `false` |

Stage C 只能推进 review hygiene。只要 Stage B effect-scale release gate 仍 blocked，Stage C
component probability 就不能被提升为 authority。

## 6. Authority Guards

| guard | value |
|---|---|
| `stock_component_probability_authority` | `false` |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |
| `replacement_allowed` | `false` |
| `candidate_vs_synthetic_delta_evidence_present` | `true` |
| `independent_fragility_truth_present` | `false` |

## 7. Shortest Remaining Paths

| residual | owner | forced review trigger |
|---|---|---|
| `RES-009` | independent fragility reviewer | readiness gate 不再输出 `BLOCK-CP-003`，且 retained benchmark evidence 可用 |
| `RES-010` | validation integrator + independent reviewer | readiness gate 不再输出 `BLOCK-CP-002`，且 validation manifest 由 reviewer promotion |
| `RES-011` | independent uncertainty reviewer | readiness gate 不再输出 `BLOCK-CP-004`，且 retained uncertainty coverage results 可用 |
| `RES-012` | independent independence reviewer | readiness gate 不再输出 `BLOCK-CP-001`，且 result-level independence signoff 已 retained |

## 8. Reproduction

```bash
python tools/maintenance/a2_blastfrag_stage_c_fragility_review_gate.py --output /tmp/a2_stage_c_fragility_review_gate.json
pytest -q tests/architecture/damage_model/test_component_fragility_validation_chain.py
```
