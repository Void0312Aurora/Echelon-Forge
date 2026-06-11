# A2 高保真杀伤模型验收与 CI 矩阵 - 2026-05-28

状态：`validation_matrix_draft / docs_only`。

本文只定义 A2 高保真杀伤模型的验收分类、剩余测试矩阵、训练消费边界和 CI lane。它不改变代码，不把任何 synthetic / fixture / engineering scaffold 提升为物理权威。

补充门禁：

- [BFM-BM-006 Source Trace Manifest Gate - 2026-05-28](bfm_bm_006_source_trace_manifest_gate_20260528.zh.md)：当前已实现的 A2 source trace / rights / authority 行政准入门禁。

## 1. 当前已锁住测试分类

| 分类 | 已锁住代表测试 | 当前锁住的事实 | 不锁住的事实 |
|------|----------------|----------------|--------------|
| Phase 0 / 制导与 miss-distance 基线 | `test_debug_runtime_exposes_proximity_fuze_miss_distance_state`、`test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries` | runtime 可审计 `proximity_min_dist_m` / `proximity_last_dist_m` / `proximity_engaged`；head-on / tail-chase / beam / high-off-boresight 几何能产生稳定差异 | 不证明确定性引信、不证明 Pk、不证明真实导引头误差模型 |
| Phase 1 / structured-air HP bypass | `test_structured_air_target_uses_damage_state_instead_of_hp_first_kill`、`test_live_missile_hit_records_structured_air_damage_without_hp_first_kill` | 带 structured damage 的 Aircraft / C2Node 不再由 HP-first branch 直接杀伤；live missile 可记录 `EffectsEvent` / `DamageReport` | 不证明全部飞机高保真，不证明一次导弹必杀 |
| RL Score 解耦 | `test_structured_air_damage_does_not_write_rl_score_from_physical_effects`、`test_a2_structured_air_effects_do_not_write_rl_score_authority` | structured-air physical effects path 不直接写 RL `Score`；训练侧必须消费事件或 damage report | 不证明 reward shaping 是物理模型，也不证明 reward 可反推真实毁伤 |
| Phase 2 / aircraft subsystem 与 cascade | `test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`、`test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems`、`test_phase2_aircraft_fire_fuel_and_hydraulic_damage_cascade_over_time`、`test_phase2_damaged_airframe_high_speed_envelope_accumulates_structural_damage` | authored hitbox 可产生不同 subsystem 后果；最小 fuel / fire / hydraulic / high-energy airframe cascade 可审计 | 不证明完整飞控、液压、电气、火灾或结构失效物理 |
| Phase 3 / warhead 与 fuze evidence surface | `test_global_warhead_profile_override_flows_into_runtime_and_effects_event`、`test_global_fuze_profile_override_flows_into_runtime_and_effects_event`、`test_fuze_delay_schedules_detonation_after_nearest_approach`、`test_contact_fuze_does_not_trigger_from_near_miss_radius`、`test_timed_fuze_detonates_on_delay_without_proximity_gate` | `WarheadProfile` / `FuzeProfile` 字段进入 runtime 与 event；contact / impact / timed 不再全等价于 proximity radius | 不证明校准引信可靠性、破片云、连续杆切割或 blast propagation |
| Phase 3 / mechanism 与 component evidence | `test_phase3_warhead_spatial_sampling_reports_fragment_and_rod_evidence`、`test_phase3_warhead_mechanism_load_evidence_tracks_mechanism_family`、`test_phase3_primary_component_reports_mechanism_load_vector`、`test_phase3_component_failure_probability_consumes_mechanism_load_evidence` | 事件面可审计 mechanism load、component identity、threshold scale、synthetic failure probability、redundancy / dependency scaffold | 不证明组件失效概率已校准 |
| Phase 5 / calibrated evidence gate | `test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority`、`test_phase5_calibrated_vulnerability_claim_requires_dataset_descriptor`、`test_phase5_validated_physics_surrogate_requires_auditable_manifest`、`test_phase5_authorized_vulnerability_rows_drive_effects_event_scales`、`test_phase5_effect_scale_rows_can_use_surface_incidence_gate`、`test_phase5_component_failure_rows_can_use_surface_incidence_gate`、`test_phase5_component_failure_rows_require_probability_authority` | synthetic profile、缺失 descriptor、无 provenance row、未授权 row 均不能获得 authority；授权 fixture row 只能证明门控和数据通路；surface-incidence 只作为 effect-scale / component-failure row gate | 不证明已有正式 calibrated Pk / vulnerability dataset |
| Database content scaffold | `test_aircraft_database_units_have_authored_structured_damage_models`、`test_phase3_current_aircraft_unit_database_has_20_plus_component_models`、`test_phase3_current_aircraft_unit_component_centers_stay_inside_parent_hitboxes`、`test_phase3_representative_aircraft_database_components_cover_uav_helo_c2` | F-16 / Su-35 / MQ-9 / MH-60R / E-3 代表内容具备 authored structured hitbox 与组件样例 | 不证明全库覆盖或组件参数真实校准 |
| Engagement contract / binding surface | `test_engagement_contract_header_exposes_lifecycle_effects_and_damage_surface`、`test_weapon_launch_adapter_snapshots_cover_munition_effects_damage_trace_contract_fields`、`test_effects_event_public_fields_match_expected_binding_surface`、`test_damage_report_public_fields_match_expected_binding_surface`、`test_trace_chain_links_track_launch_munition_effects_damage_and_observation_version` | `EffectsEvent`、`DamageReport`、component load row 和 trace 字段不会静默漂移 | 不证明字段含义已物理校准 |
| RL / scenario consumer | `test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win`、`test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once`、`test_stage0_drone_weapon_employment_fixed_fire_smoke_reaches_weapon_release` | 训练和场景层可消费 `DamageReport` 做 terminal / shaping；fixed-fire smoke 只验证链路与稳定性 | 不定义物理权威，不证明单发必杀，不放行 deterministic fuze |
| Source trace / rights manifest | `tests/architecture/damage_model/test_source_admission_audit.py`、`tools/maintenance/damage_model_source_governance.py admission-audit` | source ledger、source pin / gap update、candidate validation manifest 会被准入审计；意外 validation pass、calibration pass 或 runtime authority 授权会失败关闭 | 不运行 benchmark，不证明任何物理模型或校准数据有效 |

## 2. 高保真剩余测试矩阵

| 领域 | 仍需新增或扩展的测试 | 放行条件 | 当前不能宣称 |
|------|----------------------|----------|--------------|
| guidance / miss-distance | 1. 把 head-on / tail-chase / beam / high-off-boresight 扩展为带目标末端机动、导引头视场、track memory、能量状态的参数矩阵。2. 记录 nearest approach time、detonation time、LOS rate、achieved lateral g、seeker valid track。3. 验证 evasion 主要通过 miss distance 和 seeker / fuze 证据影响 mechanism load。 | 同一 weapon / target / geometry 在固定 seed 下输出稳定；规避动作能改变 miss distance 或 seeker state；下游 event 消费真实 miss distance 字段。 | 不能把当前 PN 基线等同为导引头或末端规避高保真模型。 |
| fuze | 1. proximity / radar proximity / laser proximity 分别测试目标签名、姿态、RCS / exposure proxy 对 `fuze_effective_reliability` 的影响。2. contact / impact 测试表面距离、穿入深度、表面容差和延迟起爆。3. timed 测试独立延迟、远离目标 no-effect event、发射安全窗口。4. 引信失效模式与延迟漂移必须进入 event。 | fuze trigger、detonation point、delay、failure reason 可审计；未授权 deterministic-fuze authority 时仍 fail closed。 | 不能用 `fuze_reliability` 参数或 fixture row 放行确定性引信。 |
| warhead mechanism | 1. fragment / blast-fragmentation：破片数量、能量、面密度、入射角、遮挡、穿透 margin 的候选组件行。2. continuous rod：杆环方向、目标交线、rod cut margin 和 posture pattern。3. blast：scaled distance、overpressure、impulse、反射 / 遮挡代理。4. HTK：局部碰撞、穿透和动能损伤路径。 | 同一命中几何下，不同 warhead family 产生可解释的 component mechanism load 差异；event 能回溯 mechanism load 到 component row。 | 当前 sampling / scale 仍是参数化证据，不是破片云、杆切割或 blast 物理求解。 |
| calibrated evidence | 1. 引入一个窄域 weapon-target-aspect-closure-miss-distance 的非 synthetic descriptor。2. 验证 `external_calibration_dataset` 或带完整 `validation_manifest` 的 `validated_physics_surrogate` 才能授权。3. 验证 row 级 source/provenance、机制载荷门槛和 component-specific override。4. 验证 PK authority 与 deterministic-fuze authority 独立 gate。 | 只有 scope 匹配、schema/source/provenance 完整、calibrated 且授权字段明确的 row 被消费；event 记录 dataset、row id、source、provenance、calibrated flag。 | 不能把 synthetic profile、schema fixture、engineering surrogate 或 JSON 自声明当作 calibrated evidence。 |
| damage cascade | 1. fuel leak 到燃油耗尽、mass 变化、火灾传播、灭火或抑制状态。2. hydraulic 回路到控制面 authority、卡滞 / 漂移 / 非对称控制。3. electrical / avionics / datalink / mission system 依赖切换。4. structural overstress 到 g-limit、flutter、翼梁或尾翼失效。5. crew / pilot / mission crew 的角色化时间线。 | cascade 结果由 component damage state 和依赖图驱动；每帧派生值可审计；同一 report 不被重复消费。 | 当前 cascade 是最小闭环，不是完整系统网络或人员伤害模型。 |
| database content | 1. 代表 5 机型从 20+ component scaffold 扩展到关键系统 completeness checklist。2. 新增 aircraft units 必须携带 airframe、authored hitbox、component、dependency、threshold、vulnerability scaffold 的最小 schema test。3. 区分 generated fallback、authored scaffold、calibrated content。4. 建立 content diff gate，防止新增飞机退回 HP-only。 | 每个目标族至少有可审计 authored path；新增飞机不能静默缺失 structured damage；calibrated 字段必须由 descriptor gate 证明。 | 当前代表数据库不等于全库高保真内容。 |

## 3. RL / 训练消费边界

训练消费层只能读取物理层已经产出的事实，不能反向定义物理事实。

允许训练消费的输入：

- `DamageReport.loss_state_to`、`mission_kill`、`mobility_kill`、`sensor_kill`、`survivability_kill`；
- `DamageReport.system_health_delta`、`platform_damage_state_delta`、一次性非终局 shaping 所需的 report id；
- `EffectsEvent` 中的 weapon / fuze / warhead / miss-distance / vulnerability evidence 审计字段；
- aircraft overlay 或 subsystem capability 的只读派生值；
- legacy 非结构化目标的兼容 HP 读数。

训练消费层不得定义的物理权威：

- reward term、`combat_win_bonus`、`total_reward` 不能证明目标真实被击杀；
- `test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win` 只证明 scenario consumer 能把 `DamageReport` 解释为训练终局；
- `test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once` 只证明非终局 damage report 可被训练 shaping 一次性消费；
- `test_stage0_drone_weapon_employment_fixed_fire_smoke_reaches_weapon_release` 只证明发射链路和运行稳定性；
- `test_structured_air_damage_does_not_write_rl_score_from_physical_effects` 只证明 physical effects 不写 RL score；
- 任何 RL / scenario / eval 测试都不能放行 Pk、deterministic fuze、warhead mechanism、component failure probability 或 calibrated vulnerability authority。

CI 中的命名建议：

- `physical-authority`：只放物理层、事件层、数据库 gate 和 authority gate 测试；
- `training-consumer`：只放 `DamageReport` / reward / scenario 消费测试；
- `smoke`：只证明链路可运行，不用于物理结论。

## 4. 并行测试 lane 命令

以下 lane 可在 CI 中并行运行。每条 lane 都假设从仓库根目录执行。

### Lane A - guidance / miss-distance / structured-air live path

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_debug_runtime_exposes_proximity_fuze_miss_distance_state \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_target_uses_damage_state_instead_of_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill
```

### Lane B - fuze / warhead mechanism evidence

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_global_fuze_profile_override_flows_into_runtime_and_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_fuze_delay_schedules_detonation_after_nearest_approach \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_contact_fuze_does_not_trigger_from_near_miss_radius \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_contact_fuze_records_surface_and_penetration_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_timed_fuze_detonates_on_delay_without_proximity_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_fuze_event_records_detonation_attitude_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_global_warhead_profile_override_flows_into_runtime_and_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_family_changes_structured_air_effect_distribution \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_spatial_sampling_reports_fragment_and_rod_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_surface_incidence_cos_reports_obliquity_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_blast_scaled_distance_tracks_standoff_and_pressure \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_fragment_areal_density_tracks_standoff \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_orientation_axis_modulates_rod_pattern_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_mechanism_load_evidence_tracks_mechanism_family
```

### Lane C - component / damage cascade / database content

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_named_control_components_derive_axis_specific_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_hydraulic_supply_damage_tracks_pressure_availability \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_avionics_and_crew_damage_derives_sensor_performance \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_crew_consequences_distinguish_pilot_mission_and_command_roles \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_fire_fuel_and_hydraulic_damage_cascade_over_time \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_lateral_fuel_storage_damage_tracks_fuel_imbalance \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_fire_suppression_integrity_reduces_fire_cascade_growth \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_fire_zone_scaffold_localizes_secondary_damage_paths \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_damaged_airframe_high_speed_envelope_accumulates_structural_damage \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_primary_component_reports_mechanism_load_vector \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_typed_dependency_edge_types_route_to_distinct_aircraft_overlays \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_typed_dependency_delay_queues_then_applies_cascade \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_engine_fuel_feed_damage_can_reduce_propulsion \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_failure_probability_consumes_mechanism_load_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_current_aircraft_unit_database_has_20_plus_component_models \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_current_aircraft_unit_component_centers_stay_inside_parent_hitboxes \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_e3_fire_bottles_are_authored_as_suppression_components \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_representative_aircraft_database_components_cover_uav_helo_c2 \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_aircraft_database_units_have_authored_structured_damage_models
```

### Lane D - calibrated evidence / authority gate

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_representative_aircraft_vulnerability_scaffolds_are_non_authoritative \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_vulnerability_claim_requires_dataset_descriptor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_descriptor_cannot_grant_vulnerability_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_requires_evidence_axes \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_requires_schema_and_source_ref \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_descriptor_requires_authoritative_source_kind \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_validated_physics_surrogate_requires_auditable_manifest \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_can_grant_pk_but_deterministic_fuze_remains_deferred \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_vulnerability_rows_drive_effects_event_scales \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_rows_require_row_provenance_metadata \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_effect_scale_rows_respect_mechanism_load_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_effect_scale_rows_can_use_surface_incidence_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_can_use_surface_incidence_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_require_mechanism_load_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_require_probability_authority \
  tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py
```

### Lane E - contract / binding / trace surface

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/engagement/test_engagement_contract_shape.py::test_engagement_contract_header_exposes_lifecycle_effects_and_damage_surface \
  tests/runtime/engagement/test_launch_adapter_static_shape.py::test_weapon_launch_adapter_snapshots_cover_munition_effects_damage_trace_contract_fields \
  tests/runtime/engagement/test_diagnostics_trace_contract.py::DiagnosticsTraceContractTests::test_trace_chain_links_track_launch_munition_effects_damage_and_observation_version \
  tests/runtime/engagement/test_munition_damage_adapter.py::MunitionDamageAdapterTests::test_synthetic_proximity_hit_fits_effects_event_and_damage_report_shape \
  tests/runtime/bindings/test_bindings_engagement_surface.py::BindingsEngagementSurfaceTests::test_component_mechanism_load_row_public_fields_match_expected_binding_surface \
  tests/runtime/bindings/test_bindings_engagement_surface.py::BindingsEngagementSurfaceTests::test_effects_event_public_fields_match_expected_binding_surface \
  tests/runtime/bindings/test_bindings_engagement_surface.py::BindingsEngagementSurfaceTests::test_damage_report_public_fields_match_expected_binding_surface
```

### Lane F - RL / training consumer boundary

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_damage_does_not_write_rl_score_from_physical_effects \
  tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_stage0_drone_weapon_employment_fixed_fire_smoke_reaches_weapon_release
```

## 5. 最小 CI gate

最小 gate 用于阻止 A2 高保真杀伤模型发生语义退化。它应小于完整 lane 矩阵，但必须覆盖五类风险：HP-first 回退、miss-distance 退化、authority gate 误放行、event contract 漂移、RL Score 回写。

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_target_uses_damage_state_instead_of_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_damage_does_not_write_rl_score_from_physical_effects \
  tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_validated_physics_surrogate_requires_auditable_manifest \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_can_use_surface_incidence_gate \
  tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py \
  tests/runtime/engagement/test_engagement_contract_shape.py::test_engagement_contract_header_exposes_lifecycle_effects_and_damage_surface \
  tests/runtime/bindings/test_bindings_engagement_surface.py::BindingsEngagementSurfaceTests::test_effects_event_public_fields_match_expected_binding_surface \
  tests/runtime/bindings/test_bindings_engagement_surface.py::BindingsEngagementSurfaceTests::test_damage_report_public_fields_match_expected_binding_surface \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win
```

最小 gate 判定规则：

- 任一 physical-authority 测试失败：阻塞合入。
- 任一 authority gate 测试失败：阻塞合入，禁止以更新 fixture 方式绕过。
- RL consumer 测试失败：阻塞训练入口，但不允许用 reward 逻辑修改 physical effects 结论。
- smoke 失败：阻塞运行链路；smoke 通过不代表物理验收通过。

建议保留现有 smoke suite 作为独立基础门：

```bash
source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

A2 source trace / rights 门禁：

```bash
source tools/maintenance/cmo_env.sh && cmo_python tools/maintenance/damage_model_source_governance.py admission-audit
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q tests/architecture/damage_model/test_source_admission_audit.py
```

在候选来源包升级为 validation run 前，应额外运行：

```bash
source tools/maintenance/cmo_env.sh && cmo_python tools/maintenance/damage_model_source_governance.py admission-audit --strict
```

## 6. 验收结论边界

当前 A2 可验收为：`组件级几何、机制证据面、事件审计、authority gate 和训练消费边界已被测试锁住`。

当前 A2 仍不能验收为：

- 完整高保真杀伤链；
- calibrated Pk 模型；
- deterministic fuze；
- 校准 warhead spatial effects；
- 校准 component failure probability；
- 全库 aircraft vulnerability content；
- reward 定义物理杀伤权威。
