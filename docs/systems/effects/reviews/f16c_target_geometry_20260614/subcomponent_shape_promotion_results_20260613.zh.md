# R18 子部件形状候选固化结果

生成日期：2026-06-13

更新：R21 后续已将已接受的最新摆放固化，因此当前 shape-placement packet
已是空队列。下方 R18 指标作为历史证据保留。见
[subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md)。

## 产物

| 产物 | 路径 |
| --- | --- |
| 内部先验 JSON | [review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json) |
| 内部先验 CSV | [review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv) |
| 跨区分段 JSON | [review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json) |
| 跨区分段 CSV | [review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv) |
| 整机约束 JSON | [review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json) |
| 剩余形状候选 JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| 剩余形状候选视图 | 已退役中间 shape-placement 视图；当前可视化结果见 [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| 当前空队列总览 | 已从当前最终结果面移除 |

## 结果

R18 将 R17 中已经把整机 silhouette 外露采样清零的 4 个形状/摆放候选固化到
review-only 先验生成规则里。这一步不代表运行时 damage geometry 已接受。

固化到内部 receiver prior 的规则：

- `iff_interrogator`：从 OBB 盒改为 rounded-LRU ellipsoid，保留公开
  APX-family LRU 名义尺寸。
- `inertial_navigation_unit`：从 OBB 盒改为 rounded-LRU ellipsoid，保留
  LN-260 级别名义尺寸。

固化到跨区 held segment 的规则：

- `engine_core_afterburner_segment`：从 x 轴 cylinder 改为 x 轴 capsule，并应用
  R17 量到的 `0.207628 m` 中心点偏移候选。
- `engine_core_hot_section_segment`：从 x 轴 cylinder 改为 ellipsoid。

| 指标 | 数值 |
| --- | ---: |
| 固化的内部 receiver prior | 2 |
| 固化的 held split segment | 2 |
| 固化项目总数 | 4 |
| 整机约束检查项 | 34 |
| 固化后仍外露项 | 10 |
| 固化后仍需尺寸/形状复核项 | 10 |
| 剩余形状/摆放候选 | 10 |
| 剩余候选中可降低外露的项 | 9 |
| 剩余候选中可完全清零外露的项 | 0 |
| 剩余未解决候选 | 10 |
| 固化后当前外露采样数 | 56 |
| 固化后候选外露采样数 | 25 |
| 固化后候选外露采样减少量 | 31 |
| runtime active component / segment | 0 |

## 剩余待复核项

这些项目仍需要更可靠的真实尺寸、锥台/截面几何，或跨区域中心线摆放，之后才能考虑运行时激活：

- `apg68_radar_array`
- `cockpit_crew_station`
- `center_fuselage_fuel_cell`
- `engine_core`
- `afterburner_nozzle`
- `left_wing_fuel_cell`
- `right_wing_fuel_cell`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_right_inner_wing_segment`

## 边界

R18 只把 R17 中零外露的候选从设计候选层推进到 review-only 生成规则。近炸投影运行时仍然保持
现有激活边界，`engine_core` 和 `wing_spar_center` 的跨区 ownership 仍为 held。
