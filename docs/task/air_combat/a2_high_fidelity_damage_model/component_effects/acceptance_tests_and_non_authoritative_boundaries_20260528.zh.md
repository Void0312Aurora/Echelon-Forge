# 验收测试建议和 Non-Authoritative 边界

状态：`2026-05-28` 测试路线。本文列出后续 component/platform consequence model 的验收建议，并冻结哪些断言不得被写成 authoritative truth。

## 验收测试分层

建议将测试分为五层：

| 层级 | 目标 | 示例断言 |
|---|---|---|
| schema/lint | 组件和依赖图数据可加载、命名稳定、旧格式兼容 | 所有代表平台 component 有 name/system/redundancy group，typed dependency 可兼容旧 `system+scale` |
| deterministic local hit | 固定局部命中点验证组件 identity 和后果方向 | 命中右 aileron 降 roll authority，命中 radar 降 sensor，不误降 fuel |
| graph propagation | 验证冗余组和依赖传播 | 同组多成员累计损伤降低 group availability，hydraulic pump 影响 flight_control dependency |
| platform consequence | 验证 overlay 到 flight/sensor/fuel/fire/crew consumers | fire 随时间拖累结构/航电/机组，fuel leak 消耗 FuelSystem，sensor range/Pd 下降 |
| live missile smoke | 验证真实发射链路能产出事件和报告 | live missile 记录 EffectsEvent/DamageReport、目标一致、HP-first bypass 不回归 |

## 建议新增或保持的测试主题

- `component_inventory_schema_lint_for_representative_aircraft`：检查五类代表平台的 hitbox/component/redundancy/dependency 最小字段。
- `component_dependency_edges_remain_backward_compatible`：旧 `dependencies: [{system, scale}]` 和新 typed dependency 同时可加载。
- `local_hit_reports_primary_component_identity_and_group_state`：固定局部命中后 event 记录 primary component、system、redundancy group、integrity、group availability。
- `redundant_group_second_member_damage_reduces_availability`：同组第二成员受损时 group availability 继续下降。
- `dependency_damage_propagates_without_cross_system_bleed`：控制作动器影响 hydraulic/flight_control，不误降 data_link；data_link 不误降 hydraulic。
- `flight_control_axis_damage_derives_axis_authority`：roll/pitch/yaw 组件分别影响对应 axis。
- `hydraulic_damage_degrades_control_authority_over_time`：hydraulic availability 下降后 flight_control 继续被拖累。
- `fuel_storage_damage_causes_leak_not_immediate_thrust_loss`：fuel cell hit 触发 leak/quantity 后果，但 engine hit 才强影响 propulsion。
- `engine_fuel_feed_damage_can_reduce_propulsion`：fuel feed/control 组件通过 fuel/engine dependency 降低推进。
- `fire_cascade_is_bounded_and_auditable`：active fire 后续传播到结构、航电、液压、机组，但 severity 保持 0-1。
- `sensor_payload_damage_affects_sensor_metrics`：radar/sensor payload 命中降低 range/Pd 或增加 noise。
- `mission_crew_damage_affects_c2_sensor_exploitation`：E-3 mission operator consoles 命中降低 mission/sensor exploitation，不直接 mobility kill。
- `crew_station_damage_affects_pilot_control_path`：cockpit crew station 命中影响 pilot/control 和 forced landing 风险。
- `structured_air_physical_effects_do_not_write_rl_score`：物理 effects path 不直接写 RL Score。
- `live_missile_structured_air_records_damage_report_without_hp_first_kill`：真实导弹链路记录 structured damage report，但 HP 不作为 kill authority。

## 断言风格

测试应优先固定：

- 字段存在、来源可审计、provenance 不丢失。
- 方向正确，例如 sensor hit 降 sensor，fuel hit 增 leak，hydraulic hit 降 control。
- 有界性，例如 integrity/capability/severity 保持 0-1。
- 单调性，例如连续损伤不能恢复组件完整性，除非未来显式 repair model。
- 隔离性，例如非相关系统不被误降。
- 分层性，例如 local diagnostics 固定精确后果，live missile 只验证链路和事件。

测试不应固定：

- 未校准的真实 Pk、真实失效概率或真实 kill threshold。
- 未授权的 deterministic fuze 起爆/杀伤结论。
- 精确火灾传播速率、燃油泄漏速率、液压压力曲线。
- 真实机型敏感组件位置、真实系统架构或真实冗余切换逻辑。
- “单发必杀”或“进入 fuze radius 必命中”。

## Non-Authoritative 边界

当前 component/platform consequence model 的非权威边界如下：

1. 当前五个平台的组件 inventory 是代表性工程样例，不是正式平台脆弱性数据库。
2. 当前 component failure probability 是合成 scaffold 或测试 fixture 通路，不是校准概率。
3. 当前 redundancy/dependency graph 是可审计传播入口，不是真实飞机系统图。
4. 当前 warhead spatial sampling 是参数化机制证据，不是真实破片云、真实连续杆切割或真实爆轰载荷模型。
5. 当前 vulnerability profile/evidence gate 可以证明 synthetic/unauthorized 数据不放行，但不意味着已有正式 calibrated dataset。
6. 当前 proximity fuze 仍保留 RNG gate，deterministic fuze 未放行。
7. 当前 `DamageReport` 和 RL shaping 消费物理后果，但 reward 不能反向定义物理 authority。
8. 当前 `Lost`、`MissionKill`、`MobilityKill`、`SensorKill` 可作为仿真状态和训练读数，但未校准前不得解释为真实 kill probability。

## Release Checklist

后续每次放大 component effects 行为面时，建议至少检查：

- 是否新增或修改 event/report 字段，并保持 append-only/兼容缺省。
- 是否新增 JSON schema 或 loader 行为，并提供旧数据兼容测试。
- 是否把工程参数标注为 synthetic/engineering/provenance。
- 是否有 local deterministic test 覆盖组件 identity 和后果方向。
- 是否有 graph propagation test 覆盖依赖和冗余。
- 是否有 live missile smoke 证明真实链路仍产出 `EffectsEvent`/`DamageReport`。
- 是否避免 physical effects path 直接写 RL Score。
- 是否明确未授权数据不能授予 Pk、deterministic fuze 或真实组件失效 probability。

