# F-16C proxy target-geometry lethality reference, 2026-06-15

本文件是当前保留的杀伤模型参考入口。旧的单层热图、top-view 采样散点和几何人工复核页面不再作为当前结果面；需要引用当前趋势、变量或位置语义时，优先使用本文件列出的标准化数据和图。

## 范围

- 数据库范围：opt-in proxy database，默认数据库不被替换。
- 目标：F-16C Block 50 proxy damage geometry。
- 战斗部族：`blast_fragmentation`、`continuous_rod`。
- 概率字段：`proxy_component_failure_probability`，即 primary component row failure probability。
- 权限边界：synthetic debug profiles；不是真实 Pk、不是确定性引信验收、不是真实武器结构击毁权威。`structural_breakup_events` 仅作为当前 MLF-6 工程代理事实写入验证面。
- 速度标准：所有概率采样的 `missile_velocity_body_mps` 指向局部原点 `(0, 0, 0)`，速度模长 `900 m/s`；原点样本无方向，保留 `[0, 0, 0]` 作为内部位置诊断点。

## 保留资料

| 用途 | 文件 |
| --- | --- |
| 标准化数据与元数据 | [target_geometry_proxy_standoff_grid_probe_20260615.json](review_packets/f16c_20260611/target_geometry_proxy_standoff_grid_probe_20260615.json) |
| 近炸矩阵结构损伤与部件失效报告 | [target_geometry_lethality_matrix_probe_20260614.json](review_packets/f16c_20260611/target_geometry_lethality_matrix_probe_20260614.json) |
| 外部 standoff x z 层概率矩阵 | [target_geometry_proxy_standoff_grid_z_layers_20260615.png](review_packets/f16c_20260611/target_geometry_proxy_standoff_grid_z_layers_20260615.png), [svg](review_packets/f16c_20260611/target_geometry_proxy_standoff_grid_z_layers_20260615.svg) |
| 中心线 z 切片概率矩阵 | [target_geometry_proxy_centerline_z_heatmap_20260615.png](review_packets/f16c_20260611/target_geometry_proxy_centerline_z_heatmap_20260615.png), [svg](review_packets/f16c_20260611/target_geometry_proxy_centerline_z_heatmap_20260615.svg) |
| `x,y=-12..12 m` 位置语义网格 | [target_geometry_proxy_xy_position_class_grid_20260615.png](review_packets/f16c_20260611/target_geometry_proxy_xy_position_class_grid_20260615.png), [svg](review_packets/f16c_20260611/target_geometry_proxy_xy_position_class_grid_20260615.svg) |
| 支撑输入：整机 top contour | [whole_airframe_contour_containment_20260614.json](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json) |
| 支撑输入：proxy database | [target_geometry_training_proxy_database_20260613](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json) |

## 自变量

- `warhead_family`: `blast_fragmentation`, `continuous_rod`
- `aspect`: 8 个 top-view 外部方向，仅用于确定外部 standoff 采样点。
- `standoff_distance_m`: `0.5, 1, 2, 4, 8, 14`
- `local_up_m`: 外部 standoff 层为 `-2, -1, 0, 1, 2`
- `centerline_z_levels_m`: `-6, -4, -2, -1, 0, 1, 2, 4, 6`
- `xy_grid`: `x,y=-12..12 m`，步长 `2 m`，`z=0`

## 位置标记

- `in-comp`: 采样点落入具体 component AABB。
- `in-box`: 采样点落入 hitbox，但未落入具体 component。
- `in-top`: 采样点在 top-view 轮廓投影内，但不在 hitbox/component 内。
- `external`: 采样点在 top-view 轮廓外。

## 复现

```powershell
.\.venv\Scripts\python.exe tools\geometry\target_geometry_proxy_standoff_grid_probe.py
.\.venv\Scripts\python.exe -m pytest tests\tools\test_target_geometry_lethality_matrix_probe.py tests\tools\test_target_geometry_damage_event_trace.py -q
```

当前验证：`11 passed`。

## 当前 MLF-6 结构断裂读数

最新 `target_geometry_proxy_standoff_grid_probe_20260615.json` 重新生成后：

- 总样本：`480`
- `structural_breakup_observed_record_count`: `43`
- `blast_fragmentation`: `3` 条，均为 `0.5 m` beam 近炸，`wing_loss`
- `continuous_rod`: `40` 条，均为左右 beam 方位 `wing_loss`
- `continuous_rod` 按 standoff 统计：`0.5 m = 10/40`、`1 m = 10/40`、
  `2 m = 10/40`、`4 m = 10/40`、`8 m = 0/40`、`14 m = 0/40`
- 小型 `target_geometry_lethality_matrix_probe_20260614.json` 是 48 个
  event-run 的 default/proxy 对照矩阵，报告 10 个 structural-breakup event：
  default/proxy 各 5，均为 continuous-rod wing-side case；`right_beam_far_14m`
  仍为非断裂。
- 该读数是当前工程代理：连续杆 beam 侧 4 m 内偏强但方向合理；不声明真实武器
  结构杀伤概率或严格数值权威。

代表性连续杆记录：

| case | standoff | z | mode | detached part | structure delta | primary component |
| --- | ---: | ---: | --- | --- | ---: | --- |
| `right_beam_standoff_0p5m` | `0.5` | `0.0` | `wing_loss` | `right_wing` | `-0.096169` | `right_wing_fuel_cell` |
| `right_beam_standoff_4p0m` | `4.0` | `0.0` | `wing_loss` | `right_wing` | `-0.053005` | `right_aileron_actuator` |
| `left_beam_zp1p0m_standoff_0p5m` | `0.5` | `1.0` | `wing_loss` | `left_wing` | `-0.159892` | `left_aileron_actuator` |
