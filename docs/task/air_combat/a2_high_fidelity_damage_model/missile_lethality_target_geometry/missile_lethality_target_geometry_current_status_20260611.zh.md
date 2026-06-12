# A2 目标几何建模当前状态

状态：`2026-06-13` TG-P6-R21 latest subcomponent placement promotion
applied / TG-P7 runtime activation 因跨区 ownership 继续 held。
父级入口和 issue 已把 F-16 几何细化从问题记录推进到可执行子项目；第一版来源/轴向/尺度
manifest、外壳区域候选、部件绑定报告、离线审阅页、测试点距离诊断、带 mesh-derived silhouette
的精细代理候选包、逐区域人工审阅 dashboard、外形命中到部件损伤的表面部件候选表，以及
可视化人工复核 triage 页面、独立部件视图、第一轮人工目检结论、五组只读 subagent 独立评估、
R10 修正快照、R11 修复结果、R12 语义损伤几何候选包、R13 内部 receiver 先验约束包、R18 子部件形状候选固化包、R19 子部件中心线摆放候选包、R20 最新子部件摆放候选包和 R21 最新子部件候选固化包已生成；最新 packet 已修复左右映射、
runtime receiver 组件、翼面部件位置、radar/IFF 和 nozzle 源盒，并开始输出 parse-ready
语义外壳体积部件候选、constrained internal receiver priors、promoted review-only
subcomponent shape rules、local centerline placement candidates、latest subcomponent placement candidates 和 promoted R21 latest placement rules；active runtime projection 在 `TG-P7` 前仍 held。

英文辅文：[missile_lethality_target_geometry_current_status_20260611.md](missile_lethality_target_geometry_current_status_20260611.md)。

## 已知事实

| 项 | 当前事实 | 影响 |
| --- | --- | --- |
| 运行时视觉模型 | `examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb` | 可继续供前端显示使用 |
| 审计模型 | `examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf` | 后续几何审阅从 glTF 读取节点、网格和外包 |
| 来源和许可 | Sketchfab `F16-C Falcon`，Carlos.Maciel，CC-BY-4.0 | 可作为主线外形审阅候选，但仍需署名和边界说明 |
| 公开尺寸 | F-16C 当前数据库记录 length `15.06 m`，wingspan `9.96 m`，height `4.88 m` | 几何代理必须用这些量级做缩放审计 |
| 当前命中盒 | 合并外包约 `15.3 m x 9.8 m x 1.2 m` | 长宽接近公开量级，高度严重不足 |
| 暴露症状 | 鼻向 4 m 近炸点贴近外壳却可能无部件损伤 | 需要外壳距离、部件距离和候选部件数诊断 |
| TG-P1 manifest | [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json) | 新模型 scale 后长度误差约 `+0.09%`，翼展约 `-3.37%`，高度约 `-4.50%`；旧命中盒高度误差约 `-75.41%` |
| 节点语义 | glTF 实际 mesh 节点为 `Object_*`；intake metadata 保留 `Canopy01_1`、`EngineL01_17` 等提示名 | P2 不能只靠 glTF 节点名自动分区，需要位置规则和人工映射 |
| TG-P2 外壳区域 | [f16c_geometry_mapping_candidate_20260611.json](review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json) | 已生成 `14` 个低精度区域；`x=4m` 落在 `forward_fuselage`，`x=6m` 落在 `nose_radome` |
| TG-P4 审阅包 | [scene.html](review_packets/f16c_20260611/scene.html)、[top.svg](review_packets/f16c_20260611/top.svg)、[side.svg](review_packets/f16c_20260611/side.svg)、[front.svg](review_packets/f16c_20260611/front.svg) | 三视图叠加外壳区域、旧命中盒、部件盒和编号测试点 |
| TG-P3 部件绑定 | [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json)、[component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv) | R11 修复后，`26` 个部件中 `26` 个已绑定，`0` 个仍是 `needs_review`，`0` 个仍是左右符号阻塞，`2` 个是 review-only 跨区语义，`0` 个是 geometry-review-required 坏盒 |
| TG-P5 距离诊断 | [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)、[review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv) | 覆盖 `10` 个测试点；修正外形区域后 `2` 个点位于外壳区域内；`nose_axis_4m` 距 `dedicated_canopy_surface_component` 为 `0.125 m`，候选部件 `7` 个 |
| TG-P6 设计草案 | [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md) | 定义从长方体升级到倾斜盒、薄棱柱、凸包和简化外壳网格的顺序 |
| TG-P6 mesh-derived 精细代理轮廓 | [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)、[fine_proxy_top.svg](review_packets/f16c_20260611/fine_proxy_top.svg)、[fine_proxy_side.svg](review_packets/f16c_20260611/fine_proxy_side.svg)、[fine_proxy_front.svg](review_packets/f16c_20260611/fine_proxy_front.svg) | 已从 `13,415` 个审计 glTF 顶点为 `14` 个 review-only 代理生成 top/side/front convex hull silhouettes；机头、座舱、主翼和平尾已改用审计网格位置和节点名单；`inflated_fallback_count=0`，support volume ratio 为 `0.55404` |
| TG-P6 人工审阅 dashboard | [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html) | 逐区域卡片显示局部 top/side/front 视图，叠加 source bounds、support bounds、mesh silhouette、部件盒、节点筛选策略、fallback 禁用策略、flags 和 candidate/review 状态 |
| TG-P6 表面部件候选 | [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json)、[surface_component_candidate_20260611.csv](review_packets/f16c_20260611/surface_component_candidate_20260611.csv) | 已把 `14` 个外壳区域整理为审阅用表面部件；`0` 个仍需人工复核，`0` 个 runtime receiver link 缺失，`0` 个 surface 被左右符号阻塞，`8` 个带跨区语义 held/candidate |
| TG-P6 可视化复核 triage | [human_review_triage.html](review_packets/f16c_20260611/human_review_triage.html) | 按左右符号、部件位置、表面部件交接和测试点几何 sanity 分组；每项先写明复核问题、观察位置和需要做出的决策，再显示局部 top/side/front 叠加图 |
| TG-P6 独立部件复核视图 | [component_review_views/index.html](review_packets/f16c_20260611/component_review_views/index.html)、[component_review_views/manifest.json](review_packets/f16c_20260611/component_review_views/manifest.json) | 已重新生成 `75` 个独立页面和对应 top/side/front SVG：`26` 个部件、`29` 个表面交接、`20` 个测试点候选；subagent 可按分组独立评估 |
| TG-P6 语义损伤几何候选 | [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json)、[semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv)、[semantic_damage_geometry_views/index.html](review_packets/f16c_20260611/semantic_damage_geometry_views/index.html) | R12 输出 `14` 个语义外壳体积候选和 `14` 个 `runtime_component_json_candidate`；runtime schema/loader 已能解析这些几何字段，`8` 个 handoff 仍因跨区 ownership held，`runtime_active_component_count=0` |
| TG-P6 内部 receiver 先验几何 | [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json)、[internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv)、[internal_component_prior_views/index.html](review_packets/f16c_20260611/internal_component_prior_views/index.html)、[manifest](review_packets/f16c_20260611/internal_component_prior_views/manifest.json) | R13 为 `26` 个现有 receiver 生成 sphere/cylinder/capsule/ellipsoid 先验并用父外壳 support bounds 或跨区 union 约束；`post_constraint_outside_count=0`，`cross_region_held_prior_count=2`，`runtime_active_component_count=0`；当前入口为 HTML/SVG 页面和 manifest |
| TG-P6 语义父子部件布局 | [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)、[semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv)、[semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html)、[manifest](review_packets/f16c_20260611/semantic_parent_child_layout_views/manifest.json) | R14 将主审阅视图收敛为 `14` 个父外壳部件，并把 `26` 个 receiver prior 叠加到对应父图上；R15 将跨区 held receiver 画成红色分段，而不是单一 held 大块；当前入口为 HTML/SVG 页面和 manifest |
| TG-P6 跨区 held 分段 | [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json)、[cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv)、[semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html) | R15 将 `engine_core` 拆成 `3` 个审阅用发动机分段，将 `wing_spar_center` 拆成 `5` 个审阅用翼梁分段；`held_segment_count=8`，`outside_whole_airframe_segment_count=0`，`runtime_active_segment_count=0`，跨区 ownership 仍保持 held |
| TG-P6 整机约束修正候选 | [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json)、[airframe_constraint_correction_candidate_20260611.csv](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv)、[overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg) | R16/R18 对全部 `34` 个 receiver prior / held split segment 做 shape-aware top/side/front 整机 silhouette 诊断；R21 最新候选固化后，`silhouette_exposure_item_count=0`，`size_or_shape_review_item_count=0`，`runtime_active_component_count=0` |
| TG-P6 子部件形状/摆放候选 | [subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json)、[subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv)、[subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html) | R17 生成保留名义尺寸的候选形状族；R18 固化前 `4` 个零外露候选；R19 增加局部中心线候选；R20 解决 radar/cockpit 剩余摆放；R21 将已接受的最新摆放固化到 review-only 规则，当前 `subcomponent_shape_placement_candidate_count=0`，`latest_candidate_total_outside_sample_count=0` |
| TG-P6 人工目检结论 | [human_review_findings_20260612.zh.md](human_review_findings_20260612.zh.md) | R7 历史快照：左右符号、鼻锥 radar/IFF、发动机/喷口和表面到运行时部件交接在 R9/R10 细化和 R11 修复前曾阻塞 `TG-P7` |
| TG-P6 独立 subagent 评估 | [subagent_independent_review_findings_20260612.zh.md](subagent_independent_review_findings_20260612.zh.md) | 五组只读评估完成；R9 快照把 `engine_core` 和 `wing_spar_center` 改为跨区语义 held/条件接受，并将 afterburner/nozzle、左右符号、radar/IFF 和缺失 runtime relation 列为修复目标 |
| TG-P6 subagent 修正结果 | [subagent_correction_results_20260612.zh.md](subagent_correction_results_20260612.zh.md) | R10 历史快照：两个写入范围受限的 subagent 修复 `apg68_radar_array`、`iff_interrogator` 和 `afterburner_nozzle`，补充跨区 review semantics，并重新生成 packet；R10 剩余的左右符号和缺失 receiver 阻塞已被 R11 替代 |
| TG-P6 几何修复结果 | [geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md) | R11 修复左右区域映射、翼面和翼根部件位置、座舱盖/进气道/平尾显式 receiver，以及直接 surface handoff 规则；component 和 surface `needs_review` 计数均为 `0` |
| TG-P6 语义损伤几何实现 | [semantic_damage_geometry_results_20260612.zh.md](semantic_damage_geometry_results_20260612.zh.md) | R12 增加语义体积候选生成、独立语义体积复核页面和 runtime component geometry schema 解析，同时保持 active runtime 行为 held |
| TG-P6 内部部件先验约束实现 | [internal_component_prior_results_20260612.zh.md](internal_component_prior_results_20260612.zh.md) | R13 增加内部 receiver 简单形状先验、外壳约束和独立复核页面；该层是 review-only，不是真实内部工程几何 |
| TG-P6 语义父子布局实现 | [semantic_parent_child_layout_results_20260612.zh.md](semantic_parent_child_layout_results_20260612.zh.md) | R14 增加 `14` 父几何部件主视图，把 `12` 个 extra receiver slot 作为子层叠到父图上，而不是作为独立主视图审阅 |
| TG-P6 跨区 held 分段实现 | [cross_region_held_segment_results_20260612.zh.md](cross_region_held_segment_results_20260612.zh.md) | R15 将两个红色 held receiver 拆成更小的 owner-region 分段供目检，同时保持 runtime activation 和 ownership acceptance 为 false |
| TG-P6 整机约束修正实现 | [airframe_constraint_correction_results_20260612.zh.md](airframe_constraint_correction_results_20260612.zh.md) | R16 增加 shape-aware 整机 silhouette 诊断和 center-shift candidate，作为继续修改尺寸/形状前的机器复核层 |
| TG-P6 子部件形状/摆放实现 | [subcomponent_shape_placement_results_20260613.zh.md](subcomponent_shape_placement_results_20260613.zh.md) | R17 为 `14` 个仍外露的子部件设计候选形状族和三视图复核页，保留名义尺寸不缩小，并将未解决项保持为后续真实尺寸、锥台/截面或跨区中心线建模任务 |
| TG-P6 子部件形状候选固化实现 | [subcomponent_shape_promotion_results_20260613.zh.md](subcomponent_shape_promotion_results_20260613.zh.md) | R18 将 `iff_interrogator`、`inertial_navigation_unit`、`engine_core_afterburner_segment` 和 `engine_core_hot_section_segment` 固化到 review-only 生成规则；剩余形状/摆放复核项为 `10`，runtime activation 仍为 `0` |
| TG-P6 子部件中心线摆放实现 | [subcomponent_centerline_placement_results_20260613.zh.md](subcomponent_centerline_placement_results_20260613.zh.md) | R19 为剩余 `10` 个形状/摆放项增加保留尺寸的局部中心线候选；`8` 个清零采样外露，`2` 个仍未解决 |
| TG-P6 最新子部件摆放实现 | [subcomponent_latest_placement_results_20260613.zh.md](subcomponent_latest_placement_results_20260613.zh.md) | R20 解决 radar 和 cockpit 剩余问题，并将主复核图例收敛为灰色整机线框加蓝色最新子部件候选 |
| TG-P6 最新子部件候选固化实现 | [subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md) | R21 将已接受的最新摆放固化到 review-only prior 和 held-segment 生成规则：`internal_component_prior_shape_promotion_count=9`，`cross_region_held_segment_shape_promotion_count=5`，`airframe_constraint_silhouette_exposure_item_count=0`，runtime activation 仍为 `0` |
| Stage-C guard 对齐 | [component_probability_surface_probe.py](../../../../../tools/maintenance/candidate_artifacts/component_probability_surface_probe.py) | 修复后的侧向部件几何会产生 `surface_incidence_cos=0.0`；Stage-C surface probe gate 已同步，component-specific rows 不再回退到 `global-fallback` |

## 当前边界

- 本状态只证明 TG-P1 来源/尺度 manifest、TG-P2 外壳区域候选、TG-P3 部件绑定、TG-P4 审阅包、
  TG-P5 测试点距离诊断、TG-P6 review-only mesh-derived 精细代理轮廓、表面部件候选、可视化 triage、
  独立部件复核视图、第一轮人工目检结论、五组 subagent 独立评估、第一轮 subagent 修正、R11 几何修复、
  R12 语义损伤几何候选、R13 内部 receiver 先验约束候选、R14 语义父子布局、R15 跨区 held
  分段、R16 整机 silhouette 诊断、R17 形状/摆放候选、R18 零外露形状固化、R19 中心线摆放候选、R20 最新摆放候选和 R21 最新摆放固化已完成，不证明 runtime activation 已完成。
- 当前 Sketchfab 模型只作为外形审阅候选，不提供真实内部部件边界。
- 旧 FlightGear F-16 已归档为 GPL v2 强候选来源，不进入主线派生几何。
- 运行时近炸投影仍按现有逻辑运行。R12-R21 只是把语义体积部件候选、内部 receiver
  先验约束、held 分段、形状诊断、形状候选、promoted review-only 形状规则、中心线候选和最新摆放候选做成
  review/parse-ready 形态，供审阅后受控激活。

## 下一步

1. 决定 `engine_core` 是继续作为 cross-region boundary candidate，还是拆分为 intake、aft engine bay 和 nozzle receiver。
2. 决定 `wing_spar_center` 是继续作为 cross-region semantic hold，还是拆分为 center-fuselage、wing-root 和 wing-skin receiver。
3. 只有在这些 ownership 语义被明确接受、拆分或继续 held，并补齐 runtime 测试后，才考虑激活
   parse-ready 的 `runtime_component_json_candidate` 或 internal receiver prior candidate。

## 验证提醒

每轮变更至少运行：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

当前聚焦测试：

```bash
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py
```

任何 `TG-P7` 激活前的更宽运行时检查：

```bash
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
pytest -q tests/architecture/damage_model
```

当前 R21 聚焦结果：`2 passed`；review packet 已重新生成。
