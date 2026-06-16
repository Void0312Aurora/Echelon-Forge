# 整机投影网格轮廓包含性结果

状态：`2026-06-14` tooling upgrade / retained diagnostic。F-16C 精细几何工程代理的验收状态（`accepted / retained`）不变。本记录只升级 `airframe_geometry_review.py` 中的 silhouette-containment 检查方法：把审计 glTF 的三角面投影到 top / side / front 三个视图，对投影面做 union，再用该投影网格 silhouette 检查 receiver 采样点。

英文辅文：[whole_airframe_contour_containment_results_20260614.md](whole_airframe_contour_containment_results_20260614.md)。

## 为什么升级

旧检查会隐藏或扭曲 protrusion：

1. 早期“整机 silhouette” 实际是多个分区凸包的并集。
2. 临时顶点 alpha-shape 使用了全部审计顶点，但会把机翼、尾翼、机身和外挂之间的空区桥接起来，导致飞机轮廓在图上不可信。
3. receiver 必须按自身投影形状采样，不能只靠稀疏 AABB 点。

最终诊断现在直接使用审计网格面：

- 轮廓方法：`projected_mesh_triangle_union`。
- 来源网格：每个视图 `4,504` 个审计 glTF 三角面。
- 三视图轮廓：`top=222`、`side=159`、`front=201` 个 contour 点；每个视图均得到 1 个 union polygon。
- receiver 采样：AABB/OBB 使用 9 点投影盒网格；ellipsoid 使用 24 点投影周界环；capsule 使用投影端帽环和中心线端点；thin-prism 使用平面足迹边界；frustum 使用两端截面环和中心线采样。
- 容差：`0.05 m`，这是 mesh / proxy 量化噪声的工程复核余量，不是物理间隙。

## 生成证据

- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json)
- [review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv)
- [review_packets/f16c_20260611/whole_airframe_contour_top.svg](review_packets/f16c_20260611/whole_airframe_contour_top.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_side.svg](review_packets/f16c_20260611/whole_airframe_contour_side.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_front.svg](review_packets/f16c_20260611/whole_airframe_contour_front.svg)
- [review_packets/f16c_20260611/whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)

每个 SVG 都绘制灰色投影审计网格 silhouette，并仅叠加 `26` 个当前 receiver prior：绿色表示在 `0.05 m` 容差内，红色表示 max outside distance 超过容差。`8` 个 review-only held split segment 已从最终结果面排除，避免把实验性分段误读为真实部件。

## 结果

`item_count = 26`（仅当前 receiver prior）。`excluded_review_only_split_segment_count = 8`。`exceeds_tolerance_item_count = 0`。`max_outside_distance_m = 0.0`。

全部 `26` 个 receiver prior 均在投影网格轮廓容差内。此前外露的两侧翼内油箱已改为随主翼平面轮廓的 swept thin-prism；`wing_spar_center` 已改为关于中线对称的 thin-prism carry-through strip；`afterburner_nozzle` 已改为 tapered frustum，而不是闭合 ellipsoid。

## 与旧结论的差异

上一轮投影网格结果里，`engine_core`、`cockpit_crew_station`、`afterburner_nozzle` 和 `inertial_navigation_unit` 在 side/front 视图出现外露；这些属于位置高度问题，已在不改变名义尺寸的前提下修正。后续 top-view 复核发现翼内油箱、翼梁和喷口的形状代理本身不合理；R22 将这些代理改为 shape-aware thin-prism/frustum，同时保持 review-only 边界。当前最终结果面继续排除 `8` 个不具备真实部件意义的 review-only held split segment，并且 `26` 个 receiver prior 均未超过投影网格轮廓容差。

## 边界

- 这是 silhouette-containment 的工具方法升级，不改变默认 F-16 unit damage database、TG-P7 opt-in training proxy、runtime activation、训练收益、Pk、结构解体、残骸或具体弹种杀伤结论。
- 投影网格轮廓只是 review-only diagnostic，不是 runtime collision mesh，也不是真实 F-16C 工程几何。
- `0.05 m` 容差是 mesh / proxy 量化噪声的工程复核余量，不是物理间隙。

## 验证

```powershell
.\.venv\Scripts\python.exe -m py_compile tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe -m ruff check tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe -m pytest -q tests/tools/test_airframe_geometry_review.py
.\.venv\Scripts\python.exe tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
git diff --check -- tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```
