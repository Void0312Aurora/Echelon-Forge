# 整机约束修正候选结果 - 2026-06-12

R16 开始处理 actual-size receiver prior 的修正回路。在继续改尺寸或摆放前，
先加入机器可读的整机 silhouette 诊断。

## 输出

| 产物 | 结果 |
| --- | --- |
| 约束报告 | [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json)、[CSV](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv) |
| 当前 latest-placement 总览 | 已从当前最终结果面移除；当前可视化结果见 [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| 总览 packet | [scene.html](review_packets/f16c_20260611/scene.html) |

## 计数

| 指标 | 数值 |
| --- | ---: |
| checked items | `34` |
| receiver priors | `26` |
| held split segments | `8` |
| silhouette exposure items | `14` |
| center-shift reduces exposure | `1` |
| center-shift fully resolves exposure | `0` |
| size-or-shape review required | `13` |
| low-confidence but inside-airframe items | `9` |
| runtime active components | `0` |

## 当前发现

- 报告使用 shape-aware top/side/front 采样：OBB 使用矩形采样；ellipsoid、
  cylinder 横截面和 capsule 投影不会把外接矩形角点误当成几何。
- 当前只有 `engine_core_afterburner_segment` 可以通过中心移动降低 silhouette
  暴露，且仍未完全解决。
- 其余暴露项大多需要尺寸、形状或跨区摆放复核，而不是简单挪中心。例如：
  鼻部 radar/IFF、座舱/INS、中机身和机翼油箱、发动机/喷口几何，以及内翼翼梁分段。

## 边界

该层是诊断和修正候选层。它不缩小尺寸，不把 center-shift candidate 应用回先验规则，
不激活 runtime damage component，也不声明真实 F-16 内部工程几何。
