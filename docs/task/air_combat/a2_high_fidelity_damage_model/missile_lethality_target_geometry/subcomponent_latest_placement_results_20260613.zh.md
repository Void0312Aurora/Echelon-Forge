# R20 最新子部件摆放候选结果

生成日期：2026-06-13

更新：R21 已将这些最新摆放固化到 review-only 生成规则，因此当前
shape-placement packet 已是空队列。下方 R20 指标作为历史证据保留。见
[subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md)。

## 产物

| 产物 | 路径 |
| --- | --- |
| 候选 JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| 候选 CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| 复核页面 | [review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html) |
| 当前空队列总览 | [review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg) |

## 结果

R20 解决了 R19 剩余的两个问题，并把可视复核面改成只展示最新子部件候选层。旧的 current、
R17 shape 和 R19 centerline 几何仍保留在 JSON/CSV 里作为 trace 字段，但不再画进主复核图例。

新的 R20 最新候选：

- `apg68_radar_array`：保留 aperture 名义尺寸，把体积移动到 radome / forward-fuselage 交界候选位置，而不是继续放在 radome tip 附近。
- `cockpit_crew_station`：保留 crew envelope 名义尺寸，把体积移动到 canopy / forward-fuselage 包络下方，而不是继续放在鼻部侧的锚点。

| 指标 | 数值 |
| --- | ---: |
| 最新子部件候选 | 10 |
| 最新候选中已清零外露 | 10 |
| 最新候选后仍未解决 | 0 |
| 最新候选外露采样 | 0 |
| 相对当前外露形状的减少量 | 56 |
| R19 之后的增量减少量 | 3 |
| runtime active component / segment | 0 |

## 图例

- 灰色：mesh-derived 整机线框 silhouette。
- 蓝色：最新子部件候选。

## 边界

R20 仍不激活运行时投影，也不声称真实内部工程几何。它只生成保留名义尺寸、且在采样意义上清零整机
silhouette 外露的最新复核候选。
