# 海军观测合同

Language:
- English canonical: [obs.md](obs.md)
- Chinese companion: `obs.zh.md`

状态：`2026-06-10`，当前维护中的 naval mission observation 特化基线。

本文档定义当前 mode-based observation surface 暴露的 naval mission-observation
合同。它登记的是 `python/mission_obs_taxonomy.py` 中已经存在的 runtime 合同；
它不创建更宽泛的 naval sensor、fire-control 或 fleet-command ontology。

## 范围

这里维护的是 naval screen/station runtime 与测试使用的
`naval_screen_station_v1` 向量合同。

主要依据：

- [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py)
- [tests/runtime/naval/test_naval_station_policy_surface.py](../../../tests/runtime/naval/test_naval_station_policy_surface.py)

本文档不定义：

- 跨军种通用 observation ontology
- 维护中 station/screen 字段之外的舰艇 sensor contact
- naval weapons-outcome 或 fire-control acceptance
- Navy service profile 的替代文本

## Mode 合同

当前维护中的 naval mission-observation mode 是：

| Mode | 维度 | 作用 |
| :--- | ---: | :--- |
| `naval_screen_station_v1` | 23 | naval screen/station guidance，包含 contact、report-chain、ROE、assignment 与 relative-slot 字段 |

字段顺序本身就是合同的一部分。

## Naval Screen/Station 字段

`naval_screen_station_v1` 包含这些字段：

- `command_code`
- `target_heading_deg`
- `target_speed_mps`
- `station_radius_m`
- `station_bearing_deg`
- `station_error_m`
- `station_error_norm`
- `screen_separation_m`
- `screen_separation_error_m`
- `own_relative_x_m`
- `own_relative_y_m`
- `desired_relative_x_m`
- `desired_relative_y_m`
- `target_contact_present`
- `support_track_present`
- `report_chain_seen`
- `roe_state`
- `authorization_to_fire`
- `assigned_target_id`
- `assigned_target_source_id`
- `self_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

## 字段分组

Command-following 锚点：

- `command_code`
- `target_heading_deg`
- `target_speed_mps`

Station 与 screen geometry：

- `station_radius_m`
- `station_bearing_deg`
- `station_error_m`
- `station_error_norm`
- `screen_separation_m`
- `screen_separation_error_m`
- `own_relative_x_m`
- `own_relative_y_m`
- `desired_relative_x_m`
- `desired_relative_y_m`

Contact、report-chain 与 assignment state：

- `target_contact_present`
- `support_track_present`
- `report_chain_seen`
- `roe_state`
- `authorization_to_fire`
- `assigned_target_id`
- `assigned_target_source_id`

Relative role 与 slot 字段：

- `self_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

## Runtime 规则

- Mode 长度固定为 23 个字段。
- 字段顺序以
  [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py) 为准。
- 缺失 contact 或 support-track 状态通过已声明字段表达；本 mode 不临时扩张 contact array。
- 在当前 runtime taxonomy 中，本 mode 是 Python-owned，由 scenario-loader 的
  mission-observation 路径装配。

## 归属边界

应继续保留在 common core 的内容：

- command 与 authority carrier 的形状
- 可复用的 assignment identifier
- 跨军种 role/slot 挂点

应继续保留在 Navy service profile 的内容：

- task-group 与 task-unit 解释
- officer-in-tactical-command 语义
- Navy warfare-role 词汇

应继续保留在 naval specialization 的内容：

- screen/station geometry
- 海上 station-keeping error term
- 当前 naval screen runtime 使用的 support-track / report-chain readiness
- 作为 naval formation execution data 的 relative-slot 字段

## 非目标

本文档不标准化：

- 完整舰艇 sensor page
- 通用 maritime track-fusion model
- naval weapon effects
- fleet-level command-and-control behavior
- air-style altitude、runway 或 sortie-phase 字段
