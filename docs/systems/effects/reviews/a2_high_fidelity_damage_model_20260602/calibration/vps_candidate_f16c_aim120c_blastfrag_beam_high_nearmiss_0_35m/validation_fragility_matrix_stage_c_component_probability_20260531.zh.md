# Validation Fragility Matrix - Stage C Component Probability

状态：`prepared / candidate / non-authoritative / stage_c_component_probability_only / 2026-05-31`。

本文档记录 Stage C `right_aileron_actuator` component-specific probability 的 fragility validation
prep matrix。它来自
[damage_model.py](../../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts component-fragility-validation-prep`，
用途是把当前 candidate gate 推进到“可请求独立 fragility review 的输入包”状态。

本文档不创建 runtime descriptor，不授予 stock component probability authority，不授予
`pk_authority`，不授予 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.stage_c_fragility_validation_prep.v1` |
| `prep_status` | `prepared_non_authoritative_stage_c_fragility_validation_review_inputs` |
| `readiness_level` | `fragility_review_input_packet_ready_but_authority_release_blocked` |
| `target_type` | `F-16C_Block50` |
| `weapon_family` | `blast_fragmentation` |
| `scope` | `beam / high / near_miss_0_35m` |
| `component_name` | `right_aileron_actuator` |
| `component_system` | `flight_control` |
| `component_redundancy_group_id` | `lateral_flight_control_actuators` |

## 2. RES-009/010/011/012 Current Gate Result

| residual | current gate result | blocking condition | prep output added | closeout still required |
|---|---|---|---|---|
| `RES-009` | `blocked_non_authoritative` | `BLOCK-CP-003` | fragility matrix plus baseline replacement path | independent component fragility benchmark / curve review proving the candidate row is not synthetic or test-local truth |
| `RES-010` | `blocked_non_authoritative` | `BLOCK-CP-002` | executable review matrix plus artifact inventory | formal Stage C result table, validation manifest update and independent reviewer signoff |
| `RES-011` | `blocked_non_authoritative` | `BLOCK-CP-004` | uncertainty probe handoff plus closeout plan | probability uncertainty coverage with accepted metrics and reviewer-owned bounds |
| `RES-012` | `blocked_non_authoritative` | `BLOCK-CP-001` | independence trace plus Stage B interlock | result-level benchmark/input separation audit by an independent reviewer |

## 3. Fragility Validation Matrix

| matrix id | residual links | current author-side result | review question | release interpretation |
|---|---|---|---|---|
| `FRAG-MAT-CP-001` | `RES-009`, `RES-010` | `pass_candidate_only` | Is the review surface locked to `right_aileron_actuator` and the lateral flight-control actuator redundancy group? | Component identity is reviewable, not independently audited truth. |
| `FRAG-MAT-CP-002` | `RES-009`, `RES-010` | `pass_candidate_only` | Do selected candidate rows cover the primary mechanism-load gate band? | Load-gate coverage is ready for reviewer audit, not authority release. |
| `FRAG-MAT-CP-003` | `RES-009` | `blocked_expected_non_authoritative` | Is the baseline still `synthetic_sigmoid`? | Baseline replacement remains forbidden until fragility closeout exists. |
| `FRAG-MAT-CP-004` | `RES-009`, `RES-011` | `pass_candidate_only` | Is the author-side surface monotonic with standoff inside the narrow bucket? | Monotonic behavior is an author-side review input only. |
| `FRAG-MAT-CP-005` | `RES-011` | `pass_candidate_only` | Is the fixed-seed repeatability probe stable enough for uncertainty review handoff? | Repeatability exists for the toy probe, but uncertainty coverage remains open. |
| `FRAG-MAT-CP-006` | `RES-012` | `prepared_pending_independent_audit` | Are input/tuning artifacts separated from output/result artifacts? | Separation trace is ready to inspect, but independent audit is not closed. |
| `FRAG-MAT-CP-007` | `RES-010`, `RES-012` | `dependency_preserved_as_blocked` | Does Stage C preserve the blocked Stage B effect-scale dependency? | Stage C cannot outrun blocked Stage B. |

## 4. Baseline Replacement Path

Current stock baseline remains:

| field | value |
|---|---|
| `baseline_component_probability_source` | `synthetic_sigmoid` |
| `baseline_authority_role` | `stock_runtime_baseline_remains_closed` |
| `replacement_allowed_now` | `false` |

Candidate evidence-row surface prepared for review:

| probe | candidate row | candidate probability | source | authority interpretation |
|---|---|---:|---|---|
| `inner` | `component-inner` | `0.52` | `vulnerability_evidence_row` | author-side candidate row only |
| `middle` | `component-middle` | `0.37` | `vulnerability_evidence_row` | author-side candidate row only |
| `outer` | `component-outer` | `0.21` | `vulnerability_evidence_row` | author-side candidate row only |

Replacement sequence remains gated:

1. Keep `synthetic_sigmoid` as non-authoritative stock baseline.
2. Run independent fragility validation against this frozen matrix.
3. Close `RES-009`, `RES-010`, `RES-011` and `RES-012` with reviewer-owned records.
4. Re-check Stage B effect-scale release dependency before Stage C promotion.
5. Only then consider a separate stock descriptor admission review.

## 5. Authority Guards

| guard | value |
|---|---|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `stock_component_probability_authority` | `false` |
| `pk_authority` | `false` |
| `deterministic_fuze_authority` | `false` |
| `stage_b_dependency_preserved_as_blocked` | `true` |

## 6. Current Conclusion

Current conclusion:

> Stage C component-probability fragility review inputs are prepared for independent review request, but independent review, uncertainty closeout, Stage B release dependency and stock authority admission remain blocked.
