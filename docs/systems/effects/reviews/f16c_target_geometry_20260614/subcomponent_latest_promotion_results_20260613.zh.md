# TG-P6-R21 最新子部件候选固化结果

状态：`2026-06-13` pass as review-only latest placement promotion；`TG-P7`
runtime activation 仍因跨区 ownership held。

英文辅文：
[subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md)。

## 范围

R21 将已经审阅过的 R19/R20 最新子部件摆放，从诊断候选层固化到 review-only
生成规则。它不激活运行时损伤投影，也不声明真实 F-16 内部工程几何。

已固化 receiver prior：

- R18 保留：`iff_interrogator`、`inertial_navigation_unit`。
- R21 新增：`apg68_radar_array`、`cockpit_crew_station`、
  `center_fuselage_fuel_cell`、`engine_core`、`afterburner_nozzle`、
  `left_wing_fuel_cell`、`right_wing_fuel_cell`。

已固化 held split segment：

- R18 保留：`engine_core_afterburner_segment`、
  `engine_core_hot_section_segment`。
- R21 新增：`engine_core_forward_compressor_segment`、
  `wing_spar_center_left_inner_wing_segment`、
  `wing_spar_center_right_inner_wing_segment`。

## 结果

生成后的 packet：
[review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json)。

重新生成后的关键计数：

- `internal_component_prior_shape_promotion_count=9`
- `cross_region_held_segment_shape_promotion_count=5`
- `airframe_constraint_silhouette_exposure_item_count=0`
- `airframe_constraint_size_or_shape_review_item_count=0`
- `subcomponent_shape_placement_candidate_count=0`
- `runtime_active_component_count=0`

固化后 shape-placement report 预期为空：
[subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json)。
已退役视图入口仅作为历史审计语境记录。

## 边界

- 运行时近炸、连续杆和破片投影行为未改变。
- `engine_core` 和 `wing_spar_center` 仍需明确接受 ownership、拆分，或有意继续 held 后，才能进入 `TG-P7`。
- 已固化形状只是公开尺寸或网格审阅代理，不是权威 F-16 部件边界。
- 不声明真实武器 Pk、击毁、结构解体、残骸或 wreck 行为。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/systems/effects/reviews/f16c_target_geometry_20260614/review_packets/f16c_20260611
```

聚焦测试结果：`2 passed`。
