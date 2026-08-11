# R19 子部件中心线摆放候选结果

生成日期：2026-06-13

更新：R20 后续解决了 R19 剩余的两个问题，R21 又将已接受的最新摆放固化到
review-only 生成规则。当前 packet 已是空 shape-placement 队列；R19 指标作为历史证据保留。见
[subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md)。

## 产物

| 产物 | 路径 |
| --- | --- |
| 候选 JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| 候选 CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| 复核页面 | 已退役中间 shape-placement 视图；当前可视化结果见 [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| 当前空队列总览 | 已从当前最终结果面移除 |

## 结果

R19 为 R18 后剩余的 `10` 个形状/摆放复核项增加局部中心线摆放候选。它保留名义尺寸和
R17 候选形状族，只应用局部 silhouette 搜索得到的中心线偏移。新的中心线候选仍然是
review-only，不是运行时 damage component。

| 指标 | 数值 |
| --- | ---: |
| R18 后剩余形状/摆放项 | 10 |
| R19 中心线候选 | 10 |
| 保留名义尺寸 | 10 |
| 可降低外露的中心线候选 | 10 |
| 可完全清零外露的中心线候选 | 8 |
| 中心线候选后仍未解决 | 2 |
| R19 前 shape-candidate 外露采样 | 25 |
| R19 后 centerline-candidate 外露采样 | 3 |
| R19 增量外露采样减少量 | 22 |
| 相对当前外露形状的减少量 | 53 |
| runtime active component / segment | 0 |

采样意义上已经清零的中心线候选：

- `center_fuselage_fuel_cell`
- `engine_core`
- `afterburner_nozzle`
- `left_wing_fuel_cell`
- `right_wing_fuel_cell`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_right_inner_wing_segment`

R19 后仍未清零：

- `apg68_radar_array`：中心线候选后外露采样 `2 -> 1`；需要 radome/radar-aperture 截面模型。
- `cockpit_crew_station`：中心线候选后外露采样 `5 -> 2`；需要 canopy 加 forward-fuselage 的 crew-envelope 模型。

## 图例

- 灰色：mesh-derived 整机线框 silhouette。
- 红色：当前仍外露的形状。
- 橙色或绿色：R17 形状候选。
- 青色：R19 中心线候选，采样外露已清零。
- 紫色：R19 中心线候选，采样外露仍未清零。

## 边界

R19 不缩小名义尺寸，不声称真实内部工程几何，也不激活运行时投影。`8` 个零外露中心线候选仍需语义复核，
之后才能考虑固化到 prior 或 held-segment 生成规则。
