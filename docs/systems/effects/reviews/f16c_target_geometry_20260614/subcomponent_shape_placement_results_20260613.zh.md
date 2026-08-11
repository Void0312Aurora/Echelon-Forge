# R17 子部件形状与摆放候选结果

生成日期：2026-06-13

更新：当前 packet 后续已推进到 R21。R17 最初创建 `14` 个形状/摆放候选；
R18 将其中 `4` 个零外露候选固化到 review-only 生成规则，R19 增加中心线候选，
R20 增加最新摆放候选，R21 将已接受的最新摆放固化到生成规则。因此下方当前
JSON/CSV 现在记录 `shape_placement_candidate_count=0`、`runtime_active_component_count=0`；
R17 指标作为历史证据保留。

## 产物

| 产物 | 路径 |
| --- | --- |
| 候选 JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| 候选 CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| 复核页面 | 已退役中间 shape-placement 视图；当前可视化结果见 [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| 当前空队列总览 | 已从当前最终结果面移除 |

## 结果

R17 针对 R16 中仍然露出整机 top/side/front silhouette 的 `14` 个
receiver prior / held split segment，生成了审阅用的子部件形状与摆放候选。

这一层保留已有公开尺寸或声明的名义尺寸，不通过缩小部件来让图变好看；
它只改变候选形状族，并在 `1` 个项目上沿用 R16 量到的中心点微调候选。
运行时 damage model 没有激活这些候选。

| 指标 | 数值 |
| --- | ---: |
| 来源约束检查项 | 34 |
| 来源外露项 | 14 |
| 形状/摆放候选 | 14 |
| 保留名义尺寸 | 14 |
| 可降低外露采样的候选 | 13 |
| 可完全清零外露采样的候选 | 4 |
| 候选后仍未解决 | 10 |
| 形状候选无改善 | 1 |
| 当前外露采样数 | 63 |
| 候选外露采样数 | 25 |
| 外露采样减少量 | 38 |
| runtime active component | 0 |

代表项：

- `iff_interrogator`：`rounded_lru_ellipsoid`，外露采样从 `1` 降为 `0`。
- `inertial_navigation_unit`：`rounded_lru_ellipsoid`，外露采样从 `1` 降为 `0`。
- `engine_core_afterburner_segment`：`segmented_engine_afterburner_capsule` 加 `0.207628 m` 中心点微调候选，外露采样从 `4` 降为 `0`。
- `cockpit_crew_station`：当前 ellipsoid 仍然 `5 -> 5`，说明它不是简单换形状能解决，需要新的座舱/前机身跨区摆放或 envelope 模型。

## 边界

这不是已接受的运行时几何。R17 是 R16 诊断和后续 prior rule 修正之间的
设计候选层。候选后仍未解决的项目，需要继续研究真实尺寸、锥台/截面模型，
或跨区域中心线几何，再考虑进入运行时 damage component。
