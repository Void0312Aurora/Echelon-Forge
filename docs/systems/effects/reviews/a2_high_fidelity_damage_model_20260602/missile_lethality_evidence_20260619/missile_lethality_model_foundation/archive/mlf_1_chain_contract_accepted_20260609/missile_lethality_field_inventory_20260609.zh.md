# MLF-1A 导弹杀伤链字段盘点

状态：`2026-06-09` MLF-1A 文档完成 / 未改运行逻辑。

语言：

- 中文主文：`missile_lethality_field_inventory_20260609.zh.md`
- 英文辅文：[missile_lethality_field_inventory_20260609.md](missile_lethality_field_inventory_20260609.md)

输入现状：

- 子项目入口：[README.zh.md](README.zh.md)
- MLF-1 合同：[missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- 任务簇：[missile_lethality_model_foundation_task_clusters_20260609.zh.md](missile_lethality_model_foundation_task_clusters_20260609.zh.md)
- 合同定义：[../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- 最近事件包：[../../../../../src/core/engine/engagement_event_types.h](../../../../../../../../src/core/engine/engagement_event_types.h)
- 事件记录：[../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- Python binding：[../../../../../src/interfaces/python/bindings_runtime.cpp](../../../../../../../../src/interfaces/python/bindings_runtime.cpp)
- 诊断 probe：[../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)
- 奖励消费：[../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)

## 结论

现有字段足以证明“发射、效果、损伤报告、诊断导出、训练消费”已经连上，但它不是 MLF-1 要求的分阶段杀伤链合同。核心问题有三类：

1. `EffectsEvent` 同时承载最近接近、命中/起爆几何、引信、战斗部、空间覆盖、部件载荷、脆弱性证据和部件摘要，字段结构化存在，但阶段边界不结构化。
2. `DamageReport` 有结构化 kill/loss 标志，但仍用 `hp_delta`、`system_health_delta` 和字符串化 `platform_damage_state_delta` 表达后果摘要，不能替代部件前后状态、平台子系统状态和结构失效事件。
3. Python binding 暴露了 C++ 合同的大部分字段；诊断 probe 只输出最后一条 `last_effect_*` / `last_damage_*` 摘要；奖励侧主要消费 `DamageReport`、飞机/触地 debug state 和字符串 delta。训练端是消费端，不是杀伤链事实来源。

本盘点不提出长期保留旧字段。短期过渡只能用于把 diagnostics、reward 和测试从旧字段迁到标准字段；删除点和负责人见“旧字段删除/迁移候选”。

## 现有出口总览

| 出口 | 当前内容 | 结构化程度 | 主要风险 | 后续归属 |
| --- | --- | --- | --- | --- |
| `LaunchEvent` | 请求/事件 id、接受状态、发射器、弹药、生成弹体、时间、producer | 结构化 | 与后续效果/损伤主要靠 event store 查找和 `DiagnosticsTrace` 补链路 | `launch` 阶段，保留并补公共头 |
| `MunitionLifecyclePacket` | 弹体、攻击方、目标/track、发射事件、active、seeker、燃料、burnout、`fuze_state`、时间 | 结构化，但未进入 `RecentEngagementEvents` | 是状态快照，不解释最近点、引信触发或未触发原因 | `missile_state` 低频状态，不替代事件 |
| `EffectsEvent` | 起爆/最近点/引信/战斗部/空间覆盖/部件载荷/证据/脆弱性摘要 | 字段结构化，阶段混杂 | 后续破片、切割、结构断裂继续塞入会扩大歧义 | 拆成 `nearest_approach`、`fuze`、`warhead`、`spatial_coverage`、`component_load` 等字段组 |
| `ComponentMechanismLoadRow` | 单个部件身份、距离、直击、机制载荷、依赖传播、失效概率、证据 | 结构化 row | 目前嵌在 `EffectsEvent` 中，没有独立事件身份和上游引用 | 稳定为 `ComponentLoadEvent` / `ComponentDamageEvent` 输入 |
| `DamageReport` | source effect、HP/系统 delta、字符串平台 delta、kill 标志、loss 转换、destroyed | 部分结构化 | `hp_delta` 和字符串 delta 容易被误读为完整损伤事实 | 拆成平台后果、部件损伤、生命周期投影 |
| `DiagnosticsTrace` | chain、launch、munition、effects、damage report 引用 | 结构化引用 | 只有引用，没有各阶段状态、原因、证据等级 | 公共头和链路索引来源 |
| `RecentEngagementEvents` | `launch_events`、`effects_events`、`damage_reports`、`diagnostics_traces` | 结构化容器 | 不含 `MunitionLifecyclePacket`，也没有分阶段 lethality events | 临时导出口，后续可承载标准事件 |
| Python binding | 暴露上述合同对象和字段 | 结构化 API | 暴露旧字段会被下游继续依赖 | MLF-1B/1D 迁到标准字段后删除旧出口 |
| diagnostics probe | `effects_event_count`、`damage_report_count`、最后效果/损伤字段 | 扁平摘要 | `last_*` 不能重建一枚弹的完整链路 | MLF-1C 改为按 `chain_id + stage` 输出 |
| reward runtime | 消费 damage report、飞机损伤 debug state、触地 debug state、动作/ROE | 消费端结构化程度不一 | 字符串 delta 和终局判断可能被误读为杀伤事实 | MLF-1D 只读标准事实投影 |

## 按阶段字段盘点

| 阶段 | 现有字段 | 来源 | 当前是否结构化 | 是否混在 `EffectsEvent` | Python binding | diagnostics 消费 | reward 消费 | 迁移判断 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 发射 | `LaunchRequest.request_id`、`shooter`、`target_entity`、`target_track_id`、`station_id`、`mount_id`、`requested_munition_family`、`authority`、`requested_time_s`、`merge_policy` | `engagement_contracts.h` | 是 | 否 | 是 | 间接通过发射/弹药数量、action 列诊断 | 奖励只通过导弹数量变化和动作状态判断 release shaping | 保留为 `LaunchRequest`，补公共头后接 `chain_id` |
| 发射 | `LaunchEvent.event_id`、`request_id`、`accepted`、`rejection_reason`、`selected_launcher`、`selected_munition`、`ammo_delta`、`cooldown_delta_s`、`spawned_munition`、`has_spawned_munition`、`event_time_s`、`producer_node_id` | `engagement_contracts.h`；`record_legacy_launch_event()` 写入 | 是 | 否 | 是 | `missile_release`、`missile_release_delta`、`missiles_remaining`、`spawned_units` 等训练/诊断派生值，不直接逐字段读 `LaunchEvent` | release shaping / C2 ROE 通过 missile count 和 action state 消费，不读 launch event | 保留；`event_id` 可作为 `chain_id` 优先来源 |
| 导弹状态 | `MunitionLifecyclePacket.packet_id`、`munition`、`attacker`、`target_entity`、`target_track_id`、`launch_event_id`、`active`、`seeker_mode`、`guidance_cadence_s`、`track_memory_state`、`fuel_remaining_fraction`、`burnout`、`max_flight_time_s`、`fuze_state`、`source_time_s` | `engagement_contracts.h` | 是，但当前不是 `RecentEngagementEvents` 的导出向量 | 否 | 是 | 未见 probe 直接消费 | 未见 reward 直接消费 | 作为 `missile_state` 快照保留；不能承担最近接近或引信判定事实 |
| 最近接近/命中几何 | `nearest_approach_time_s`、`miss_distance_m`、`detonation_local_forward_m`、`detonation_local_right_m`、`detonation_local_up_m`、`detonation_heading_deg`、`detonation_pitch_deg`、`detonation_roll_deg`、`closure_mps`、`missile_axis_forward/right/up`、`quality`、`confidence` | `EffectsEvent` | 字段结构化，但阶段未独立 | 是 | 是 | `last_effect_miss_distance_m`、`last_effect_detonation_local_*`，summary 还算 norm | reward 不消费 | MLF-2 前迁到 `NearestApproachEvent`；未起爆也应可报告 |
| 引信 | `trigger_type`、`outcome_state`、`detonation_time_s`、`fuze_type`、`fuze_trigger_radius_m`、`fuze_delay_s`、`fuze_reliability`、`fuze_profile_synthetic`、`fuze_signature_source`、`fuze_target_signature`、`fuze_signature_scale`、`fuze_effective_reliability`、`fuze_contact_surface_distance_m`、`fuze_contact_penetration_depth_m`、`fuze_contact_surface_tolerance_m`、`fuze_contact_inside_hitbox`、`direct_hitbox_intersection` | `EffectsEvent` | 字段结构化，但缺显式 `armed/triggered/failure_reason/sample` | 是 | 是 | `last_effect_fuze_type`、`last_effect_direct_hitbox_intersection` | reward 不消费 | MLF-2 前迁到 `FuzeEvaluationEvent`；旧字段只作来源字段 |
| 战斗部机制 | `effect_family`、`warhead_mass_kg`、`warhead_lethal_radius_m`、`warhead_profile_synthetic`、`damage_scalar_synthetic`、`mechanism_armor_scale`、`mechanism_exposure_scale`、`mechanism_effect_scale`、`mechanism_fragment_energy_j`、`mechanism_fragment_areal_density_per_m2`、`mechanism_penetration_margin`、`mechanism_blast_overpressure_kpa`、`mechanism_blast_impulse_kpa_ms`、`mechanism_blast_scaled_distance_m_kg13`、`mechanism_rod_cut_margin`、`mechanism_surface_incidence_cos` | `EffectsEvent`；同类机制字段也在 `ComponentMechanismLoadRow` | 结构化，但事件级和部件 row 级混在一起 | 是 | 是 | 未见 probe 输出这些机制字段 | reward 不消费 | MLF-3/4 迁到 `WarheadMechanismEvent`，部件 row 只保留部件局部载荷 |
| 空间覆盖 | `projected_hitbox_count`、`spatial_effect_scale`、`warhead_spatial_sample_count`、`warhead_spatial_hit_estimate`、`warhead_spatial_hit_fraction`、`warhead_spatial_energy_scale`、`warhead_spatial_pattern_scale`、`warhead_orientation_axis_forward/right/up`、`warhead_orientation_pattern_scale` | `EffectsEvent` | 结构化，但和效果事件混杂 | 是 | 是 | `last_effect_projected_hitbox_count` | reward 不消费 | MLF-3 前迁到 `SpatialCoverageEvent`，与部件暴露分开 |
| 部件载荷 | `component_mechanism_load_rows`；row 内 `component_name`、`component_system`、`component_redundancy_group_id`、`direct_hit`、`distance_m`、`effect_scale`、机制载荷、依赖传播、失效概率、证据、失效模式 | `ComponentMechanismLoadRow` 嵌入 `EffectsEvent` | row 内结构化 | row 嵌入 `EffectsEvent` | 是 | probe 只输出 `last_effect_component_hit_count`，不展开 row | reward 不消费 row | MLF-3/5 稳定为独立 `ComponentLoadEvent`，用公共头追溯上游 |
| 部件/平台损伤 | `component_threshold_scale`、`component_failure_probability*`、`component_failure_sample`、`component_failure_count`、`component_hit_count`、`component_primary_*`、`component_redundancy_group_*`、`vulnerability_*` | 多数在 `EffectsEvent`，row 中也有失效概率/模式 | 结构化，但“预测/证据/实际损伤”混杂 | 是 | 是 | `last_effect_component_hit_count`，不输出失效模式 | reward 不消费这些字段 | 预测和证据迁到 vulnerability/profile；实际前后状态迁到 `ComponentDamageEvent` |
| 部件/平台损伤 | `DamageReport.hp_delta`、`system_health_delta`、`platform_damage_state_delta`、`mission_kill`、`mobility_kill`、`sensor_kill`、`survivability_kill`、`forced_landing`、`flight_control_kill`、`propulsion_kill`、`crew_kill`、`loss_state_from`、`loss_state_to`、`destroyed`、`report_time_s` | `DamageReport`；`simulation_kernel_engagement_event_store.cpp` 从 before/after snapshot 写入 | kill/loss 结构化；delta 摘要不充分；`platform_damage_state_delta` 是字符串 | 否 | 是 | `last_damage_*` 摘要 | `_recent_damage_reports()`、`_apply_report_shaping()`、`combat_entity_terminal_state()` 消费 report；字符串 delta 被 `_parse_platform_damage_delta()` 解析 | MLF-1D 迁到标准平台后果字段；旧 delta 只做短期过渡 |
| 结构失效 | 当前没有 `breakup_state`、`detached_part`、`structural_break`、`airframe_breakup` 等独立事件；只有 `AircraftDamageState.structural_integrity`、`structural_overstress`、`flutter_exposure` 可被 reward debug snapshot 读取 | reward runtime 通过 `debug_get_aircraft_damage_state()` 的字段表消费飞机状态 | 部分结构化状态存在，结构失效事件缺失 | 否 | 不属于 engagement binding | diagnostics probe 未见消费 | damage consequence shaping 可消费结构完整度/过载/颤振变化 | MLF-6 前预留 `StructuralBreakupEvent`；不能用 `destroyed` 或 ground crash 代替空中解体 |
| 生命周期 | `DamageReport.loss_state_from/to`、`destroyed`；触地 debug fields `on_ground`、`terrain_z`、`lifecycle`、`impact_h_speed`、`impact_sink_rate`、`impact_severity`、`gear_stress`、`gear_collapsed`、`on_runway` | `DamageReport`；reward runtime 的 `_GROUND_CONTACT_STATE_FIELDS` | 部分结构化，触地状态不在 engagement event 合同内 | 否 | `DamageReport` 是；ground debug state 另走 sim debug API | probe 输出 `last_damage_loss_state`、`last_damage_destroyed` | terminal state 和 consequence shaping 消费 `loss_state_to`、`destroyed`、ground lifecycle/impact | MLF-8 前迁到 `LifecycleTransitionEvent`；训练终局只消费，不拥有事实 |
| 训练投影 | `reward_terms`、release shaping、C2 ROE 分类、damage shaping、damage consequence shaping、`combat_entity_terminal_state()` 输出 `neutralized/actionable/reason/damage_report_id/loss_state/ground_*` | `air_combat.py` 和 probe CSV row | 消费端结构化，不是物理事实结构 | 否 | 不适用 | probe 输出 reward totals、C2、action、last effect/damage 摘要 | reward 自身消费上述状态并产出 reward terms | MLF-1D 迁到 `TrainingProjectionEvent` 或统一投影；训练不得反推杀伤事实 |

## 关键字段归属说明

| 字段族 | 当前真实来源 | 当前解释边界 | 标准链路目标 |
| --- | --- | --- | --- |
| `chain_id` | `DiagnosticsTrace.chain_id`，event store 优先用 `launch_event_id`，否则用 `effects_event_id` | 目前是引用关系，不携带阶段状态 | 所有阶段公共头字段 |
| `source_event_id` | `DamageReport.source_event_id` 指向 `EffectsEvent.event_id` | 只能说明 damage report 来源于哪个 effect，不说明部件/平台后果细节 | `ComponentDamageEvent` / `PlatformConsequenceEvent` 使用 `parent_event_id` |
| `quality` / `confidence` | `EffectsEvent` | 只描述该效果记录质量/置信度，不能当真实 Pk | 公共头或阶段诊断置信度 |
| `vulnerability_pk_authority` | `EffectsEvent` 的 vulnerability 字段 | 只能是证据/权限标记，不是 MLF 基础阶段的真实 Pk 声明 | MLF-9 低细节/统计校验层再处理 |
| `destroyed` | `DamageReport` 根据实体失活或 `loss_state_to == lost` 写入 | 终局摘要，不区分空中解体、触地损毁、删除或残骸生命周期 | 生命周期和结构失效事件拆分 |
| `ground_lifecycle` | reward terminal helper 从 debug ground contact state 生成 | 训练终局投影，不在 engagement 合同内 | `LifecycleTransitionEvent` 的事实字段，reward 只读 |

## 旧字段删除/迁移候选

这些字段不是长期兼容承诺。若 MLF-1B/1C/1D 必须短暂双写或读取旧字段，只能作为迁移手段，并在对应 worker 的验收包里写清删除点。

| 候选 | 当前消费者 | 为什么危险 | 迁移方向 | 删除点 | 负责人 |
| --- | --- | --- | --- | --- | --- |
| `last_effect_miss_distance_m` | diagnostics probe CSV 和 episode summary | “最后一条效果”不等于当前弹链路，也不能表达未起爆最近点 | `NearestApproachEvent.miss_distance_m`，按 `chain_id + stage` 输出多行 | MLF-1C probe 支持 staged projection 后删除 | `MLF-1C` |
| `last_effect_detonation_local_forward_m/right_m/up_m` | diagnostics probe CSV 和 summary | 只抓最后起爆局部位置；未起爆/多弹/多目标会误导 | `NearestApproachEvent.local_*` 和 `FuzeEvaluationEvent.detonation_*` 分开 | MLF-1C 标准字段落地后删除 | `MLF-1C` |
| `last_effect_direct_hitbox_intersection` | diagnostics probe | 把 contact/hitbox 几何和引信结果压成一个最后值 | `FuzeEvaluationEvent.contact_*` + `SpatialCoverageEvent.projected_hitbox_count` | MLF-1C 标准字段落地后删除 | `MLF-1C` |
| `last_effect_projected_hitbox_count` | diagnostics probe | 空间覆盖摘要缺少方向、采样和部件暴露上下文 | `SpatialCoverageEvent.*` | MLF-1C 标准字段落地后删除 | `MLF-1C` |
| `last_effect_component_hit_count` | diagnostics probe | 只给数量，不给部件身份、机制载荷、失效模式 | `ComponentLoadEvent` / `ComponentDamageEvent` 展开 row | MLF-1C 能展开 component rows 后删除 | `MLF-1C` |
| `last_effect_fuze_type` | diagnostics probe | 引信类型不是引信判定原因；仍缺 armed/triggered/failure | `FuzeEvaluationEvent.fuze_type`、`triggered`、`failure_reason` | MLF-1C 标准投影后删除；更完整引信字段由未来独立 MLF-2 子项目处理 | `MLF-1C` / future standalone `MLF-2` |
| `last_damage_report_id` | diagnostics probe | 只定位最后损伤报告，不保证同一枚弹链路 | staged projection 中的 `damage_report_id` / `parent_event_id` | MLF-1C 标准 projection 后删除 | `MLF-1C` |
| `last_damage_loss_state` | diagnostics probe | loss 摘要不能区分部件损伤、结构解体、触地残骸 | `PlatformConsequenceEvent.loss_state_*` + `LifecycleTransitionEvent` | MLF-1C/1D 完成后删除 | `MLF-1C` / `MLF-1D` |
| `last_damage_system_health_delta` | diagnostics probe | 单一最小能力 delta 会掩盖具体子系统和方向 | 标准平台后果字段：mission/mobility/sensor/survivability before/after 或 delta | MLF-1D reward/probe 迁移后删除 | `MLF-1D` |
| `last_damage_mission_kill` / `mobility_kill` / `sensor_kill` / `destroyed` | diagnostics probe | 终局摘要容易替代完整杀伤解释 | `PlatformConsequenceEvent` + `LifecycleTransitionEvent` 的 stage row | MLF-1C projection 可读标准事件后删除 | `MLF-1C` |
| `DamageReport.hp_delta` | Python binding；潜在外部消费者 | HP delta 不是高保真杀伤事实，也不表达部件/平台前后状态 | component/platform before-after 状态；如保留只做低细节投影 | MLF-1D 消费端不再依赖后，MLF-1E 确认删除 | `MLF-1D` / `MLF-1E` |
| `DamageReport.system_health_delta` | diagnostics probe；reward `_apply_report_shaping()` | 聚合 delta 对训练有用，但不应冒充杀伤链事实 | `PlatformConsequenceEvent` 明确各能力 before/after/delta，reward 从投影读 | MLF-1D 迁移 reward 后删除或降级为 derived projection | `MLF-1D` |
| 字符串 `DamageReport.platform_damage_state_delta` | reward `_parse_platform_damage_delta()` | 字符串 `mission=...,mobility=...` 需要解析，字段名/单位/缺失值都不稳定 | 结构化 `mission_capability_delta`、`mobility_capability_delta`、`sensor_capability_delta`、`survivability_margin_delta` | MLF-1D reward 改读结构化字段后删除 | `MLF-1D` |
| `DamageReport.destroyed` 作为唯一终局 | diagnostics probe；reward terminal | 会混淆实体删除、lost、触地残骸和空中解体 | `LifecycleTransitionEvent` 区分整机、迫降体、坠毁残骸、碎片 | MLF-8 前可短期投影，MLF-1D 不再把它当唯一事实 | `MLF-1D` / `MLF-8` |
| `EffectsEvent.component_primary_*` | Python binding；潜在诊断 | “主部件”摘要会遮蔽多部件载荷和冗余组传播 | 展开 `ComponentLoadEvent` / `ComponentDamageEvent` rows | MLF-1C component row projection 后删除摘要出口 | `MLF-1C` |
| `EffectsEvent.vulnerability_*` 混在效果事件中 | Python binding；潜在诊断 | 证据/校准/权限字段和本次效果结果混在一起 | vulnerability profile/evidence 子对象，事件只引用 profile/evidence id | MLF-1B DTO 设计后迁移，MLF-1E 确认旧出口删除 | `MLF-1B` / `MLF-1E` |

## MLF-1 后续最小命名目标

| 标准阶段 | 推荐对象 | 最低字段 |
| --- | --- | --- |
| 公共头 | `LethalityChainHeader` | `schema_version`、`chain_id`、`event_id`、`parent_event_id`、`stage`、`status`、`reason`、`source_time_s`、`source_frame`、`munition`、`shooter`、`target`、`producer_node_id`、`fidelity_mode`、`evidence_level`、`confidence` |
| 发射 | `LaunchEvent` 扩展或投影 | 现有字段 + 公共头 |
| 导弹状态 | `MunitionStateSnapshot` | `active`、`seeker_mode`、`fuel_remaining_fraction`、`burnout`、`track_memory_state`、`fuze_state` |
| 最近接近 | `NearestApproachEvent` | `miss_distance_m`、`nearest_approach_time_s`、`local_forward/right/up_m`、`closure_mps`、`aspect_bucket` |
| 引信 | `FuzeEvaluationEvent` | `fuze_type`、`armed`、`triggered`、`failure_reason`、`delay_s`、`reliability`、`sample`、`contact_*` |
| 战斗部 | `WarheadMechanismEvent` | `mechanism_family`、`fragment_*`、`blast_*`、`rod_cut_margin`、`evidence_level` |
| 空间覆盖 | `SpatialCoverageEvent` | `sample_count`、`hit_estimate`、`hit_fraction`、`energy_scale`、`pattern_scale`、`orientation_axis_*` |
| 部件载荷 | `ComponentLoadEvent` | component identity、direct hit、distance、mechanism loads、dependency propagation、profile refs |
| 部件损伤 | `ComponentDamageEvent` | component before/after integrity、failure modes、severity、probability/sample refs |
| 平台后果 | `PlatformConsequenceEvent` | mission/mobility/sensor/survivability before/after、aircraft consequence flags、secondary fire/leak/control/propulsion fields |
| 结构失效 | `StructuralBreakupEvent` | breakup state、detached part refs、airframe break mode、cause event |
| 生命周期 | `LifecycleTransitionEvent` | from/to lifecycle、ground lifecycle、wreck entity、debris count、terminal projection id |
| 训练投影 | `TrainingProjectionEvent` | consumed event ids、reward terms、terminal reason、consumer version；只读事实，不生成事实 |

## 验收判断

`MLF-1A Field Inventory` 的文档验收条件已经满足：

- 字段表覆盖了发射、导弹状态、最近接近/命中几何、引信、战斗部机制、空间覆盖、部件载荷、部件/平台损伤、结构失效、生命周期、训练投影。
- 每类字段都标明了来源、结构化程度、是否混在 `EffectsEvent`、Python binding、diagnostics 和 reward 消费状态。
- 旧字段删除/迁移候选已经列出，尤其包含 `last_effect_*`、`last_damage_*`、`hp_delta`、`system_health_delta`、字符串化 `platform_damage_state_delta`、`destroyed` 摘要和 `component_primary_*`。
- 本文没有把旧字段写成长期兼容面；短期过渡只作为 MLF-1C/1D/1E 的迁移手段。
- 本文未调整 AIM-120C/MQ-9、未修改运行逻辑。
