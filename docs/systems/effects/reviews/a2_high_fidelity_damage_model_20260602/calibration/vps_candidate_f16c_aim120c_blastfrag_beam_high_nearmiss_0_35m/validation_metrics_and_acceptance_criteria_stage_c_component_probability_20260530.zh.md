# Validation Metrics And Acceptance Criteria - Stage C Component Probability

状态：`frozen_pre_run / candidate / non-authoritative / stage_c_component_probability_only`。

本文档用于把当前候选包的 Stage C `component_failure_probability_authority` 候选评审门槛在结果
closeout 前冻结下来，优先服务于：

- `AIM-120C-class blast_fragmentation -> F-16C_Block50`
- `beam / high / near_miss_0_35m`
- `right_aileron_actuator` component-specific probability candidate

本文档不是 validation result，不创建 runtime descriptor，不授予
`component_failure_probability_authority`、`effect_scale_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_target` | `a2.vulnerability_surrogate_validation.v1` |
| `criteria_status` | `frozen_pre_run_stage_c_component_probability_candidate_only` |
| `primary_release_scope` | `component_failure_probability_authority_only` |
| `effect_scale_dependency_status` | `stage_b_review_track_retained_separately` |
| `validation_metrics_ref` | `self` |
| `validation_acceptance_criteria_ref` | `self` |
| `review_status` | `author_frozen_pending_independent_review` |
| `runtime_descriptor_action` | `forbidden_until_fragility_review_record_and_result_closeout_exist` |

## 2. 冻结原则

1. 本文所有门槛在 Stage C result closeout 前冻结，不得根据结果回填或放宽。
2. 本文只冻结 Stage C component-specific probability 候选评审的最小门槛，不把 `Pk`、deterministic fuze 或全平台 kill assessment 混入同一轮 release。
3. 即使本文 hard gate 后续都通过，只要：
   - fragility / uncertainty / independence residual 未关闭，
   - component-specific provenance 未独立审阅，
   - stock descriptor 未单独审议，
   仍不得宣称 stock authority 已放行。
4. 当前 Stage C 仍依赖 Stage B narrow-scope 边界；若 scope / geometry / mechanism residual 未关闭，Stage C 也不得单独越过这些边界。
5. 本文冻结的是 Stage C candidate review hygiene，不是“真实组件失效概率曲线已校准”的结论。

## 3. Stage C Hard Gates

下表定义 Stage C `component_failure_probability_authority` 候选评审所需的 hard gates。
所有 hard gate 都必须满足，才允许把结果带入下一轮 Stage C authority review。

| `criteria_id` | 输入 | metric / field | 冻结门槛 | 失败含义 |
|---|---|---|---|---|
| `BFM-CRIT-CP-001` | runtime-aligned baseline event | `component_primary_name` | `right_aileron_actuator` | 当前候选路径没有稳定绑定到目标组件，Stage C 停止。 |
| `BFM-CRIT-CP-002` | descriptor candidate | `source_kind` | `validated_physics_surrogate` | descriptor 种类不合法，Stage C 停止。 |
| `BFM-CRIT-CP-003` | descriptor candidate | calibrated-shape marker | `candidate descriptor must keep calibrated-form review shape` | 候选 descriptor 形状不完整，Stage C 停止。 |
| `BFM-CRIT-CP-004` | descriptor candidate | `effect_scale_authority` | `false` | Stage C 非法混入 effect-scale authority，Stage C 停止。 |
| `BFM-CRIT-CP-005` | descriptor candidate | probability-authority candidate flag | `must stay enabled for candidate review shape only` | 当前 snapshot 甚至没有 probability authority candidate，Stage C 停止。 |
| `BFM-CRIT-CP-006` | descriptor candidate | `pk_authority` | `false` | 非法混入 Pk authority，Stage C 停止。 |
| `BFM-CRIT-CP-007` | descriptor candidate | `deterministic_fuze_authority` | `false` | 非法混入 deterministic fuze authority，Stage C 停止。 |
| `BFM-CRIT-CP-008` | component-specific row | `component_name` | `right_aileron_actuator` | row 未指向目标组件，Stage C 停止。 |
| `BFM-CRIT-CP-009` | component-specific row | `component_system` | `flight_control` | row 缺少稳定系统归属，Stage C 停止。 |
| `BFM-CRIT-CP-010` | component-specific row | `component_redundancy_group_id` | `lateral_flight_control_actuators` | row 缺少稳定冗余组归属，Stage C 停止。 |
| `BFM-CRIT-CP-011` | component-specific row | `component_failure_probability` | `0 <= x <= 1` | 概率字段无效，Stage C 停止。 |
| `BFM-CRIT-CP-012` | component-specific row | `min_blast_scaled_distance_m_kg13` | `<= primary_row_value` | mechanism-load gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-013` | component-specific row | `max_blast_scaled_distance_m_kg13` | `>= primary_row_value` | mechanism-load gate 上界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-014` | component-specific row | `min_fragment_areal_density_per_m2` | `<= primary_row_value` | fragment-density gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-015` | component-specific row | `max_fragment_areal_density_per_m2` | `>= primary_row_value` | fragment-density gate 上界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-016` | component-specific row | `min_surface_incidence_cos` | `<= primary_row_value` | surface-incidence gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-017` | component-specific row | `max_surface_incidence_cos` | `>= primary_row_value` | surface-incidence gate 上界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-018` | component-specific row | `min_fragment_energy_j` | `<= primary_row_value` | fragment-energy gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-019` | component-specific row | `max_fragment_energy_j` | `>= primary_row_value` | fragment-energy gate 上界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-020` | component-specific row | `min_penetration_margin` | `<= primary_row_value` | penetration-margin gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-021` | component-specific row | `max_penetration_margin` | `>= primary_row_value` | penetration-margin gate 上界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-022` | component-specific row | `min_blast_impulse_kpa_ms` | `<= primary_row_value` | blast-impulse gate 下界不覆盖当前主组件载荷，Stage C 停止。 |
| `BFM-CRIT-CP-023` | component-specific row | `max_blast_impulse_kpa_ms` | `>= primary_row_value` | blast-impulse gate 上界不覆盖当前主组件载荷，Stage C 停止。 |

## 4. Stage C Release Notes

即使第 3 节全部满足，当前 Stage C 也只允许导出如下结论：

- 当前候选 package 已经具备 component-specific probability review 所需的最小 candidate hygiene；
- 可以把结果提交到下一轮 Stage C narrow-scope authority 审阅；
- 仍不能把结果自动写入 stock runtime descriptor；
- 仍不能上卷成 `Pk`、mission-kill probability 或 deterministic fuze authority。

## 5. Deferred / Open Gates

下列内容明确不因为本文冻结而自动完成：

| `deferred_id` | 领域 | 当前状态 | 为什么仍 open |
|---|---|---|---|
| `BFM-DEF-CP-001` | fragility calibration curve | `open` | 当前只有 component-specific candidate row，没有独立 fragility curve。 |
| `BFM-DEF-CP-002` | probability uncertainty | `open` | 当前没有独立 Brier/log-loss/calibration-curve/coverage closeout。 |
| `BFM-DEF-CP-003` | component truth and geometry audit | `open` | `right_aileron_actuator` 仍是 repo projection candidate，不是真值数据库。 |
| `BFM-DEF-CP-004` | independent validation and review | `open` | 当前 Stage C 仍来自 runtime-aligned test-local exercise。 |

## 6. 仍然保留的边界

本文冻结之后，以下边界依然成立：

- `RES-009` 不会因为本文冻结就自动关闭；还需要 fragility residual、uncertainty 和独立 review closeout。
- `RES-013` 和 `RES-014` 不在本包内关闭。
- 当前 package 仍保持 `candidate / non-authoritative / not_run`。

## 7. 来源依据

本 artifact 的冻结依据来自：

- [梯度真实性原则](../../../../../standards/gradient_realism_principles.zh.md)
- [A2 数据来源准入规则](../../data_collection/source_admission_rules_20260528.zh.md)
- [A2 窄域 Authority 闭环任务定义](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md)
- [Validation Report Draft](validation_report_draft.zh.md)
- [Flight-Control / Hydraulic / Fuel / Fire / Sensor / Crew 后果模型路线](../../component_effects/platform_consequence_model_roadmap_20260528.zh.md)
- [验收测试建议和 Non-Authoritative 边界](../../component_effects/acceptance_tests_and_non_authoritative_boundaries_20260528.zh.md)

## 8. 当前判定

当前判定为：

> `validation metrics and acceptance criteria are now frozen for Stage C component-specific probability candidate review, but fragility calibration, uncertainty, independent review and stock authority remain pending`.
