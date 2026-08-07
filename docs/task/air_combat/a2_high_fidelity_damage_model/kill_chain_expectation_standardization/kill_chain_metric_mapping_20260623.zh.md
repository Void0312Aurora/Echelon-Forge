# 杀伤链指标映射

状态：`2026-06-23`，用于
[杀伤链期望标准化](README.zh.md) 的 P3 pass 指标映射。本文是 docs-only
字段契约；不运行仿真，不重调 runtime 参数，不编辑 descriptor，不声明真实
AIM-120C / F-16C / Pk 权威。

英文规范页：
[kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md)

Schema label：`a2.kill_chain_metric_mapping.v0`

## 输入

- P1 合同：
  [kill_chain_idealized_expectation_contract_20260621.zh.md](kill_chain_idealized_expectation_contract_20260621.zh.md)
- P2 场景矩阵：
  [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md)
- 当前 decoupled diagnostics surface：
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)
- 当前 lethality abstraction：
  [lethality_abstraction.py](../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_abstraction.py)
- 当前 scalar ledger：
  [lethality_scalar_ledger.py](../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_scalar_ledger.py)
- 当前 runtime contract 字段：
  [engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)

## P3 边界

P3 只回答“每个 heatmap cell 应读取或派生哪些报告字段”。它不回答：

- `R_fuze` 或 `R_effect` 的米制校准值；
- 部件失效概率阈值；
- 真实武器 / 真实目标 authority；
- Pk、reward 或实体删除 authority；
- 是否应该修改 runtime 参数。

字段可用性按以下标签记录：

| 标签 | 含义 |
| --- | --- |
| `runtime-current` | 当前 runtime facade 或 engagement events 已能直接导出。 |
| `diagnostic-current` | 当前 diagnostics 已能从 chain rows / scalar ledger 导出。 |
| `derived-report` | P3/P4 报告可由已声明 profile 和 runtime facts 派生。 |
| `planned-harness` | P4 harness 必须作为输入元数据或新增报告列提供。 |
| `held-authority` | 需要未来 admission gate；P3 不消费为校准依据。 |

## 阶段指标映射

| Metric id | 阶段 / owner | 字段 | 来源 | 用途 | 可用性 |
| --- | --- | --- | --- | --- | --- |
| `KCES-M0` | `launch_window` / harness metadata | `profile_id`, `grid_tier`, `case_id`, `target_motion_layer`, `range_km`, `offset_deg`, `signed_bearing_deg`, `seed`, `launch_class` | P2 heatmap 和 P4 case generator；当前 guidance probe 已有 `case_id`, `range_m`, `bearing_deg`, `seed` | 给 heatmap cell 分组，并带入 `N/M/O` 期望类别。 | `planned-harness` + partial `runtime-current` |
| `KCES-M1` | `guidance_approach` / `approach` | `nearest_distance_m`, `nearest_approach_time_s`, `truth_min_distance_m`, `closest_point_local_forward_m`, `closest_point_local_right_m`, `closest_point_local_up_m`, `closure_mps`, `max_achieved_lateral_g` | `guidance_cases[].nearest_miss_distance_m`, `truth_min_distance_m`, `max_achieved_lateral_g`, `runtime_facade.approach_fact.*`, `lethality_chain_stage_abstractions[].observed.*` | 判断是否进入 `R_fuze`，并把制导 / 运动学问题和杀伤问题分离。 | `runtime-current` / `diagnostic-current` |
| `KCES-M2` | `guidance_approach` / `approach` | `R_fuze_m`, `rho_fuze`, `entered_R_fuze`, `guidance_expectation_status` | `R_fuze_m` 来自 profile-declared proxy；`rho_fuze = nearest_distance_m / R_fuze_m` | 将 `N/M/O` 期望转成可报告的归一化制导指标。 | `derived-report`; `R_fuze_m` is `planned-harness` until declared |
| `KCES-M3` | `fuze_decision` | `fuze_triggered`, `fuze_reason`, `detonated`, `outcome_state`, `detonation_probability`, `fuze_quality`, `sensor_opportunity_score`, `terminal_track_valid`, `target_detected`, `target_detection_confidence`, `target_detection_threshold`, `detonation_point_source`, `trigger_radius_m` | `guidance_cases[].fuze_*`, `runtime_facade.fuze_decision.*`, `lethality_chain_stage_abstractions[].observed.*` | 解释 `entered_R_fuze` 后是否触发；不提供确定性引信 authority。 | `runtime-current` / `diagnostic-current` |
| `KCES-M4` | `warhead_load_field` | `R_effect_variant`, `R_effect_m`, `rho_effect_case`, `rho_effect_component`, `effect_band`, `effect_family`, `lethal_radius_m`, `spatial_effect_scale`, `mechanism_effect_scale`, `fragment_energy_j`, `fragment_areal_density_per_m2`, `penetration_margin`, `blast_overpressure_kpa`, `blast_impulse_kpa_ms`, `blast_scaled_distance_m_kg13`, `rod_cut_margin`, `surface_incidence_cos` | `runtime_facade.warhead_load_field.*`, `component_loads[]`, P3 variant rules | 把近炸后的载荷场与制导 / 引信分离，支持 `REV-*` sensitivity rows。 | `runtime-current` + `derived-report` |
| `KCES-M5` | `warhead_load_field` / component load rows | `component_name`, `component_system`, `component_redundancy_group_id`, `component_distance_m`, `component_effect_scale`, `spatial_intersection_fraction`, `pattern_weight`, `orientation_weight`, `receiver_exposure_fraction`, `armor_transmission`, `sampling_confidence`, `load_intensity_scale` | `runtime_facade.warhead_load_field.component_loads[]` | 解释“触发但组件载荷弱 / 强”的部件级来源。 | `runtime-current` |
| `KCES-M6` | `component_response` | `component_response_row_count`, `failure_probability`, `failure_sample`, `failure_mode`, `failure_severity`, `integrity_before`, `integrity_after`, `integrity_delta`, `component_response_band`, `sampled_failure` | `runtime_facade.component_responses[]`, `runtime_facade.component_response.*`, component-response abstraction | 只在 fuze/load 成功后评价目标响应；不得补偿 `R_fuze` 外 miss。 | `runtime-current` + `derived-report` |
| `KCES-M7` | `consequence_projection` | `outcome_state`, `component_hit_count`, `component_failure_count`, `primary_component_name`, `primary_component_system`, `primary_component_integrity`, `redundancy_group_availability`, `air_system_hit_flags`, `air_system_spatial_scales`, `vulnerability_scale_trace`, `mission_kill`, `mobility_kill`, `sensor_kill`, `destroyed` | `runtime_facade.consequence_projection.*`, consequence abstraction | 作为下游观察，不反推制导 / 引信 / 载荷期望。 | `runtime-current` / `diagnostic-current` |
| `KCES-M8` | owner guard / scalar ledger | `scalar_id`, `current_owner_stage`, `intended_owner_stage`, `producer_stage`, `producer_field`, `consumer_fields`, `coupling_flags`, `calibration_ready` | `lethality_chain_scalar_ledger`, `lethality_chain_scalar_coupling_summary` | P4 单层校准 guard；确认一次只改变一个 layer。 | `diagnostic-current` |

## 派生字段规则

`nearest_distance_m` 的读取优先级：

```text
nearest_distance_m =
  guidance_cases[].nearest_miss_distance_m
  or runtime_facade.approach_fact.closest_distance_m
  or guidance_cases[].truth_min_distance_m
```

`rho_fuze`：

```text
rho_fuze = nearest_distance_m / R_fuze_m
entered_R_fuze = rho_fuze <= 1.0
```

P3 不选择 `R_fuze_m`。P4 harness 必须显式声明 `R_fuze_m` 的 profile 来源；
如果只引用当前仓库 proxy trigger radius，也必须把它标为 engineering proxy。

`rho_effect` 有两个层级：

```text
rho_effect_case = nearest_distance_m / R_effect_m
rho_effect_component = component_loads[].distance_m / R_effect_m
```

`rho_effect_case` 用于 heatmap 总览；`rho_effect_component` 用于部件级响应解释。
若 component load rows 存在，P4 报告应优先用 `rho_effect_component` 解释
`component_response`。

`effect_band` 使用 P1 合同的定性分区：

| 条件 | `effect_band` |
| --- | --- |
| `rho_effect <= 0.25` | `core` |
| `0.25 < rho_effect <= 0.50` | `effective` |
| `0.50 < rho_effect <= 0.80` | `outer_effective` |
| `0.80 < rho_effect <= 1.00` | `edge` |
| `rho_effect > 1.00` | `outside_effect` |
| `R_effect_m` 未声明 | `unclassified_missing_R_effect` |

`component_response_band` 不在 P3 中量化。P3 只要求报告：
`failure_probability`、`failure_sample`、`sampled_failure`、`integrity_delta`、
`failure_mode` 和 `failure_severity`。概率阈值和完整度分区进入 P4 或后续
admission work。

Post-P5 补充：[组件响应量化阈值附录](kill_chain_component_response_quantization_20260705.zh.md)
现已定义 task-local v0 诊断分区。该附录不改写 P3 的历史边界；P3 仍只是字段映射，
附录只为后续 before/after report 提供可复用的 `component_response` 量化口径。

标准化期望包络：
[空空杀伤链期望包络](../../../../domains/air/work/issues/kill_chain_expectation_envelope.zh.md)
使用本 P3 字段映射和 P5 后 response bands，定义 standards-layer planning-supplement
labels，例如 `envelope_cell_status` 和 `envelope_owner_stage`。该包络不是当前
runtime contract，也不授予 calibration authority。

## R_effect Variant 映射

| Variant id | `R_effect_m` 来源 | P3 状态 | 报告要求 |
| --- | --- | --- | --- |
| `REV-RUNTIME-PROJECTION` | 导弹发射时快照中的当前 runtime 空间投影半径 `missile_runtime_projection.resolved_projection_radius_m`。该值由 runtime 战斗部族、`lethal_radius_m`、`projection_radius_fraction` 和投影 clamp 共同解析，不等于致死半径本身。 | selected | 输出 `R_effect_source=missile_runtime_projection.resolved_projection_radius_m`，并标注 `authority_level=runtime_projection_comparison`；不得作为理想化标准。 |
| `REV-EQ-FUZE` | `R_effect_m = R_fuze_m`。 | selected | sensitivity 上界；报告必须标注 `derived_from_fuze_radius=true`。 |
| `REV-SMALLER-LOAD` | P4 harness 显式声明的 `declared_effect_radius_m`，且必须满足 `< R_fuze_m`。 | selected but value-held | 没有默认米制值；若未声明，输出 `unclassified_missing_R_effect`。 |
| `REV-DECLARED-EFFECT` | 未来 review/admitted evidence row。 | held | 不进入当前 P3/P4 默认校准。 |

`R_effect_variant` 默认是离线评价维度。除非 P4 证明实现必须重跑 runtime，
否则 `REV-*` 不应乘进 simulation case 数。

## Heatmap 报告行 Schema

P4 输出的每个 heatmap report row 至少应包含：

| 字段组 | 必填字段 |
| --- | --- |
| `identity` | `schema_version`, `profile_id`, `case_id`, `grid_tier`, `sample_index`, `seed` |
| `launch_window` | `target_motion_layer`, `range_km`, `offset_deg`, `signed_bearing_deg`, `launch_class` |
| `guidance_approach` | `nearest_distance_m`, `nearest_approach_time_s`, `closure_mps`, `max_achieved_lateral_g`, `R_fuze_m`, `rho_fuze`, `entered_R_fuze`, `guidance_expectation_status` |
| `fuze_decision` | `fuze_triggered`, `fuze_reason`, `detonated`, `detonation_probability`, `fuze_quality`, `terminal_track_valid`, `target_detected`, `detonation_point_source` |
| `warhead_load_field` | `R_effect_variant`, `R_effect_m`, `R_effect_source`, `rho_effect_case`, `effect_band`, `component_load_row_count`, `strongest_component_effect_scale`, `weakest_component_effect_scale` |
| `component_response` | `component_response_row_count`, `max_failure_probability`, `sampled_failure_count`, `min_integrity_delta`, `primary_failure_mode`, `component_response_band` |
| `consequence_projection` | `outcome_state`, `component_hit_count`, `component_failure_count`, `primary_component_system`, `mission_kill`, `mobility_kill`, `sensor_kill`, `destroyed` |
| `guards` | `scalar_owner_guard_status`, `unexpected_stage_delta`, `authority_boundary_status`, `runtime_parameter_retuning` |

推荐的 `guidance_expectation_status`：

| `launch_class` | 条件 | 状态 |
| --- | --- | --- |
| `N` | `entered_R_fuze=true` | `satisfied` |
| `N` | `entered_R_fuze=false` | `guidance_or_model_residual` |
| `M` | 任意结果 | `observed_marginal`，并保留 stage facts |
| `O` | `entered_R_fuze=false` | `negative_control_satisfied` |
| `O` | `entered_R_fuze=true` 或出现强 load / response | `negative_control_alert` |

推荐的 `authority_boundary_status`：

| 条件 | 状态 |
| --- | --- |
| `runtime_parameter_retuning=false` 且 `calibration_authority=false` 且 `real_world_pk=false` | `engineering_proxy_guarded` |
| 任一字段试图声明真实 weapon/target/Pk authority | `authority_violation` |

## 采样层级映射

| Sampling tier | P3 字段要求 | P4 用途 |
| --- | --- | --- |
| `anchor-grid` | 必须完整输出所有 `KCES-M0` 到 `KCES-M8` 字段；允许 1 seed。 | smoke 和 report schema 验证。 |
| `recommended-main-grid` | 必须输出 signed bearing heatmap，并为每个 `N/M/O` cell 保留分组字段。 | 第一轮校准热图和连续性检查。 |
| `boundary-refinement` | 必须引用原始 coarse cell，并记录 `refinement_reason=N/M_boundary` 或 `M/O_boundary`。 | 防止粗网格误判。 |
| `expanded-maneuver-grid` | 必须记录目标机动 profile id、机动强度和目标加速度摘要。 | 机动层成熟后扩展一般性。 |

## P3 收口

P3 当前为 pass。它完成了：

- 将 P2 的 heatmap cell、采样层级和 `R_effect_variant` 映射到 stage-report 字段；
- 区分 `runtime-current`、`diagnostic-current`、`derived-report`、`planned-harness`
  和 `held-authority`；
- 明确 `rho_fuze`、`rho_effect_case` 和 `rho_effect_component` 的派生规则；
- 明确 `REV-SMALLER-LOAD` 需要 P4 显式声明 `declared_effect_radius_m`，没有默认值；
- 给 P4 提供 heatmap report row schema 和 guard 字段。

P3 不解决：

- 具体参数值；
- P4 harness 的 CLI / 并行执行设计；
- 概率阈值或完整度阈值；
- standards promotion；
- 真实 authority admission。

这些进入 P4/P5 或未来 evidence 工作。
