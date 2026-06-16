# A2 TG F-16C 精细几何代理验收记录

状态：`2026-06-14` accepted。验收门被收束为精细几何建模本身；TG-P7 运行时/训练材料只作为下游交接证据保留，不再作为本子项目闭合条件。

## 验收判断

结论：本子项目的 F-16C 精细几何工程代理已闭合，可以归档为 retained archive record。

这里的“工程代理”不是放弃工程化要求，而是明确证据等级：它应当能作为后续近炸、连续杆、破片和部件承接建模的工程代理输入；但它不能被声明为真实 F-16C 厂商工程图纸、真实内部设备边界、真实 Pk 或具体弹种杀伤率。

## 验收项

| 验收项 | 证据 | 判断 |
| --- | --- | --- |
| 来源/尺度/坐标轴可追溯 | [manifest.json](../../review_packets/f16c_20260611/manifest.json) 记录 Sketchfab CC-BY-4.0 来源、hash、坐标轴映射、公开尺寸误差；缩放后长度误差 `+0.09%`、翼展 `-3.37%`、高度 `-4.50%` | pass |
| 旧命中盒缺口被量化 | manifest 记录当前命中盒高度误差约 `-75.41%`，并保留 `26` 个旧部件和 `4` 个 hitboxes 的基线 | pass |
| 外壳区域存在且可视化 | [f16c_geometry_mapping_candidate_20260611.json](../../review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json)、[scene.html](../../review_packets/f16c_20260611/scene.html)、三视图 SVG | pass |
| 旧部件绑定闭合 | [component_binding_report_20260611.json](../../review_packets/f16c_20260611/component_binding_report_20260611.json)：`component_count=26`、`bound_component_count=26`、`needs_review_count=0`、`hard_blocker_count=0`、`geometry_review_required_count=0` | pass |
| 测试点距离诊断闭合 | [review_point_diagnostics_20260611.json](../../review_packets/f16c_20260611/review_point_diagnostics_20260611.json)：`review_point_count=10`、`zero_outer_distance_without_component_candidate_count=0`；`nose_axis_4m` 可解释为外壳/候选部件几何问题 | pass |
| 精细代理不靠膨胀兜底 | [fine_geometry_proxy_candidate_20260611.json](../../review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)：`proxy_count=14`、`mesh_derived_silhouette_count=14`、`mesh_source_vertex_count=13415`、`inflated_fallback_count=0`、`total_proxy_support_volume_ratio=0.55404` | pass |
| 表面部件候选闭合 | [surface_component_candidate_20260611.json](../../review_packets/f16c_20260611/surface_component_candidate_20260611.json)：`surface_component_count=14`、`needs_review_count=0`、`missing_existing_runtime_component_relation_count=0`、`side_sign_hard_blocker_count=0` | pass |
| 语义外壳体积候选闭合 | [semantic_damage_geometry_candidate_20260611.json](../../review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json)：`semantic_volume_component_count=14`、`runtime_parse_ready_component_count=14`、`runtime_active_component_count=0` | pass |
| 内部 receiver 先验受约束 | [internal_component_prior_candidate_20260611.json](../../review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json)：`internal_component_prior_count=26`、`constrained_inside_count=26`、`post_constraint_outside_count=0`、`shape_promotion_count=9` | pass |
| 父子布局和跨区 held 可审阅 | [semantic_parent_child_layout_candidate_20260611.json](../../review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)、[cross_region_held_component_segments_20260611.json](../../review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json)：`parent_semantic_component_count=14`、`bound_receiver_component_count=26`、`held_segment_count=8`、`outside_whole_airframe_segment_count=0` | pass |
| R22 跨区 ownership 候选可交接 | [cross_region_ownership_split_candidate_20260611.json](../../review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json)：`parent_decision_count=2`、`split_receiver_candidate_count=8`、`runtime_parse_ready_split_candidate_count=8`、`runtime_active_split_component_count=0` | pass |
| 整机投影网格诊断记录 follow-up protrusions，但不改变几何验收 | [whole_airframe_contour_containment_20260614.json](../../review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json)、[whole_airframe_contour_containment_results_20260614.zh.md](../../whole_airframe_contour_containment_results_20260614.zh.md)：`contour_method=projected_mesh_triangle_union`、`exceeds_tolerance_item_count=10`、`runtime_active_component_count=0`；这些是 retained review-only follow-up items，不是默认 runtime 改动，也不是验收回退 | pass with retained follow-up |
| 最终复核证据已收缩 | 当前保留整机投影网格轮廓、语义体积、内部 prior、父子布局和后续 placement 视图；旧的 `75` 页 component-review 中间包已从当前结果面退役 | pass |
| 聚焦测试通过 | `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/tools/test_airframe_geometry_review.py` | pass, `5 passed` |
| 文档/路径空白检查通过 | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py` | pass, no output |

## 不作为闭合门的材料

以下材料保留为下游 handoff，不再作为“精细几何建模是否闭合”的验收门：

- `target_geometry_runtime_activation_candidate_20260613.*`
- `target_geometry_runtime_behavior_regression_20260613.*`
- `target_geometry_training_proxy_database_20260613*`
- `target_geometry_damage_event_trace_20260614.json`
- `target_geometry_training_probe_32k_20260614.json`

这些材料说明 split receiver 代理可被显式 opt-in 路径消费，但不证明默认路径应替换、不证明 policy/reward 已消费、不证明训练效果、不证明目标击毁或结构后果。

## 归档边界

本子项目到此闭合。后续如需推进默认 runtime replacement、policy/reward 诊断、杀伤概率、结构解体、残骸、Pk 或其他机型复用，应另建或进入对应子项目，不继续向本几何包追加新的验收门。
