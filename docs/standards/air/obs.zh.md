# 飞行员观测合同

Language:
- English canonical: `obs.md`
- Chinese companion: [obs.zh.md](obs.zh.md)

状态：`2026-05-18`，当前维护中的 air mission observation 特化基线。

本文档定义的是当前 runtime 和测试实际使用的 air mission-observation 合同，而不是试图覆盖
“真实飞行员可能看到的全部仪表、雷达页面或感知信息”。

## 范围

这里维护的是 mode-based 的 `mission_observation` 向量合同。

主要依据：

- [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py)
- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [src/core/mission/runtime/mission_runtime.h](../../../src/core/mission/runtime/mission_runtime.h)
- [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py)

本文档不定义：

- 通用环境观测字典的全部字段
- 泛化的 sensor contacts 或 RWR 页面
- joint/common-core 的统一观测 ontology

## Mode 合同

当前维护中的 `mission_observation` mode 有：

| Mode | 维度 | 作用 |
| :--- | ---: | :--- |
| `basic` | 4 | 最小 command-following 基线 |
| `nav_v1` | 11 | 早期 waypoint navigation 合同 |
| `nav_v2` | 14 | 当前维护中的 route/LNAV 合同 |
| `nav_v2_formation_v1` | 17 | `nav_v2` 加编队偏移 |
| `nav_v2_formation_role_v1` | 21 | 编队偏移加 role/slot 字段 |
| `nav_v2_cooperative_takeoff_v1` | 25 | route、takeoff、formation、role 合同 |

字段顺序本身就是合同的一部分。

## 共享基础字段

所有 mode 都以这 4 个字段开头：

1. `command_code`
2. `target_heading_deg`
3. `target_altitude_m`
4. `target_speed_mps`

这 4 个字段是当前 air runtime 中最稳定的 command-following 锚点。

## Navigation 字段

`nav_v1` 追加：

- `active_wp_idx`
- `total_wps`
- `dist_m`
- `xtk_m`
- `dtg_m`
- `direct_bearing_deg`
- `desired_leg_track_deg`

`nav_v2` 则切换为当前维护中的 LNAV-style 集合：

- `selected_steerpoint`
- `steerpoint_mode_code`
- `dist_m`
- `bearing_rel_deg`
- `altitude_delta_m`
- `cdi_norm`
- `track_angle_error_deg`
- `leg_distance_remaining_m`
- `next_turn_deg`
- `distance_to_turn_m`

这些字段的权威索引标签以
[python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py) 为准。

## Formation 字段

`nav_v2_formation_v1` 追加：

- `form_offset_x_m`
- `form_offset_y_m`
- `form_offset_z_m`

这些字段属于 air specialization，不属于 common core。

`nav_v2_formation_role_v1` 再追加：

- `self_role_code`
- `self_formation_role_code`
- `relative_slot_code`
- `reference_relative_slot_code`

这些字段把 common/service 的 role 语义桥接进 air formation surface。

## Cooperative Takeoff 字段

`nav_v2_cooperative_takeoff_v1` 追加 air takeoff/tasking 字段：

- `takeoff_procedure_code`
- `takeoff_clearance_code`
- `takeoff_interval_s`
- `runway_slot_code`

同时保留上面的 formation/role 字段。

这个 mode 是当前 cooperative takeoff guidance 的 air 合同，不是跨域通用起飞 schema。

## Runtime 规则

- 即使 route guidance 不可用，mode 长度仍保持固定。
- 当 route guidance 不可用时，导航段按零填充。
- 字段可见性取决于 mode。
- formation 与 takeoff 字段只在声明它们的 mode 中出现。

## 归属边界

应继续保留在 common core 的内容：

- 抽象的 command-following 锚点
- 能跨军种成立的 role/slot 语义

应继续保留在 air specialization 的内容：

- runway / takeoff 专用字段
- route / LNAV / ILS 语义
- formation offset 与空中 role 细节

## 非目标

本文档不标准化：

- `oat`
- `wind_vec`
- `rwr_state`
- `radar_contacts`
- `missile_count`

这些内容即使存在于更广的环境观测面中，也不属于本文定义的维护中 air mission-observation contract。
