# TG-P6-R13 内部部件先验几何约束结果

状态：`2026-06-12` applied / review-only prior candidate / active runtime
仍 held。英文辅文：[internal_component_prior_results_20260612.md](internal_component_prior_results_20260612.md)。

本轮补上“外壳区域作为父部件，内部 receiver 用简单先验体表示”的机制。它不尝试从外壳 mesh
反推出真实内部结构，而是用球、圆柱、胶囊体和椭球体构造低精度子部件候选，再用父外壳
support bounds 约束，避免旧 AABB receiver 露出机身或翼面。

## 已实现

| 切片 | 实现 | 边界 |
| --- | --- | --- |
| 子部件先验规则 | 为 `26` 个现有 receiver 生成 `sphere`、`cylinder`、`capsule`、`ellipsoid` 先验；规则记录 shape、axis、role 和 rationale。 | 先验来自工程直觉和现有配置，不是真实 F-16 内部布局。 |
| 外壳约束 | 每个 prior 先用旧 component AABB 的中心/尺度生成，再收缩或平移进语义外壳 `support_bounds`。 | 约束使用 review support bounds，不是闭合物理舱段。 |
| 跨区 held | `engine_core` 使用 intake / aft engine bay / nozzle 的 union 约束；`wing_spar_center` 使用 center fuselage / wings / wing roots 的 union 约束，并继续 held。 | 只证明能生成不露出的候选体，不接受 ownership。 |
| 审阅产物 | 新增 [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json)、[CSV](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv)、[独立视图](review_packets/f16c_20260611/internal_component_prior_views/index.html) 和 [view manifest](review_packets/f16c_20260611/internal_component_prior_views/manifest.json)。 | `runtime_active_component_count=0`；runtime 仍未改行为。 |

## Packet 摘要

- 内部 receiver prior：`26`。
- Shape 覆盖：`capsule=13`、`cylinder=4`、`ellipsoid=4`、`sphere=5`。
- 约束后露出外壳：`0`。
- 跨区 held prior：`2`，即 `engine_core` 和 `wing_spar_center`。
- 已激活 runtime prior：`0`。

## 预览入口

- 独立页面：
  [internal_component_prior_views/index.html](review_packets/f16c_20260611/internal_component_prior_views/index.html)
- 视图 manifest：
  [internal_component_prior_views/manifest.json](review_packets/f16c_20260611/internal_component_prior_views/manifest.json)

图层含义：

- 蓝色：原模型语义区域 mesh silhouette。
- 灰色：外壳约束 bounds。
- 紫色：旧 receiver AABB。
- 青色：约束后的先验体外包。
- 红色文字：跨区 ownership held。

## 剩余边界

- R13 不是真实内部舱段建模。它只把旧 receiver AABB 变成更合理的 review-only 先验体，并把它们约束在外壳范围内。
- `sphere` / `cylinder` / `capsule` / `ellipsoid` 目前作为 candidate primitive 记录；正式 runtime 激活仍需单独测试和接受。
- `engine_core` 与 `wing_spar_center` 仍然不能被单个外壳区域独占，需要拆分或显式接受跨区 ownership。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
```

聚焦结果：`tests/tools/test_airframe_geometry_review.py` 为 `2 passed`；重新生成 packet 后
`internal_component_prior_count=26`，`internal_component_prior_post_constraint_outside_count=0`。
