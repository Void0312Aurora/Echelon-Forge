# 跨区 Held 分段结果 - 2026-06-12

R15 将两个红色跨区 held receiver prior 拆成更小的 owner-region 审阅分段，
避免父子几何预览里继续显示单一 held 大块。

## 输出

| 产物 | 结果 |
| --- | --- |
| 分段报告 | [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json)、[CSV](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv) |
| 父子布局报告 | [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)、[CSV](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv) |
| 复核页面 | 中间 parent-child 视图已退役；当前可视化结果见 [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |

## 计数

| 指标 | 数值 |
| --- | ---: |
| held parent components | `2` |
| held split segments | `8` |
| `engine_core` segments | `3` |
| `wing_spar_center` segments | `5` |
| outside whole-airframe segments | `0` |
| runtime active segments | `0` |

## 分段策略

- `engine_core` 仍保持 held，但显示为
  `engine_core_afterburner_segment`、`engine_core_hot_section_segment` 和
  `engine_core_forward_compressor_segment`。
- `wing_spar_center` 仍保持 held，但显示为左内翼、左翼根、中央承力盒、
  右翼根和右内翼翼梁分段。
- 红色现在表示 held split segment。绿色/青色仍表示普通 actual-size
  receiver prior。灰色是整机线框，蓝色是父语义区域。

## 边界

该层仍是 review-only 几何。它不激活 runtime component，不接受跨区 ownership，
也不声明真实 F-16 内部工程几何。
