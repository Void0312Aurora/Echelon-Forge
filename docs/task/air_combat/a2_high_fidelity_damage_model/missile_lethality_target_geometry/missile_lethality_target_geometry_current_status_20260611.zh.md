# A2 目标几何建模当前状态

状态：`2026-06-14` TG-P7-R5 split-receiver damage-event trace passes；
默认 runtime projection 和维护中的 F-16 unit database 仍未改变。
父级入口和 issue 已把 F-16 几何细化从问题记录推进到可执行子项目；第一版来源/轴向/尺度
manifest、外壳区域候选、部件绑定报告、离线审阅页、测试点距离诊断、带 mesh-derived silhouette
的精细代理候选包、逐区域人工审阅 dashboard、外形命中到部件损伤的表面部件候选表，以及
可视化人工复核 triage 页面、独立部件视图、第一轮人工目检结论、五组只读 subagent 独立评估、
R10 修正快照、R11 修复结果、R12 语义损伤几何候选包、R13 内部 receiver 先验约束包、R18 子部件形状候选固化包、R19 子部件中心线摆放候选包、R20 最新子部件摆放候选包、R21 最新子部件候选固化包、R22 跨区 ownership 拆分候选包、TG-P7-R1 runtime activation candidate packet、TG-P7-R2 runtime behavior regression packet、TG-P7-R3 training proxy database packet、TG-P7-R4 active training probe result 和 TG-P7-R5 damage-event trace result 已生成；最新 packet 已修复左右映射、
runtime receiver 组件、翼面部件位置、radar/IFF 和 nozzle 源盒，并开始输出 parse-ready
语义外壳体积部件候选、constrained internal receiver priors、promoted review-only
subcomponent shape rules、local centerline placement candidates、latest subcomponent placement candidates、promoted R21 latest placement rules、R22 parse-ready split receiver candidates、TG-P7-R1 带 feature flag 的 `damage_model.hitboxes[].components` patch candidate、TG-P7-R2 in-memory behavior regression、TG-P7-R3 opt-in proxy runtime database、TG-P7-R4 active 8k training comparison，以及 TG-P7-R5 targeted trace；proxy component event names 已观测到全部 `8` 个 split receivers，但默认 active runtime projection 仍未改变。

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
| TG-P6 跨区 ownership 拆分候选 | [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json)、[cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv)、[scene.html](review_packets/f16c_20260611/scene.html) | R22 建议仅在 `8` 个 split receiver candidates 被明确接受并测试后，才退役父级 `engine_core` 与 `wing_spar_center` receiver；`runtime_parse_ready_split_candidate_count=8`，`runtime_active_split_component_count=0`，ownership acceptance 仍为 false |
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
| TG-P6 跨区 ownership 拆分实现 | [cross_region_ownership_split_results_20260613.zh.md](cross_region_ownership_split_results_20260613.zh.md) | R22 为两个剩余 cross-region held 父级 receiver 输出 review-only ownership decisions 和 parse-ready AABB fallback split receiver records；父级 receiver retirement 和 runtime activation 仍未接受 |
| TG-P7 运行时激活候选实现 | [target_geometry_runtime_activation_results_20260613.zh.md](target_geometry_runtime_activation_results_20260613.zh.md)、[target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json)、[target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv) | TG-P7-R1 将 R22 split payload 转换为带 feature flag 的 `damage_model.hitboxes[].components` patch candidate：`candidate_component_count=8`，`runtime_schema_parse_ready_component_count=8`，`unit_database_patch_component_count=8`，`parent_receiver_retirement_candidate_count=2`，`runtime_active_component_count=0`，C++ unit-definition loader parse smoke 通过 |
| TG-P7 运行时行为回归实现 | [target_geometry_runtime_behavior_regression_results_20260613.zh.md](target_geometry_runtime_behavior_regression_results_20260613.zh.md)、[target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json)、[target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv) | TG-P7-R2 只在内存中应用 component patch 并验证：`base_component_count=26`，`projected_component_count=32`，`retired_parent_component_count=2`，`split_component_added_count=8`，`duplicate_component_name_count=0`，`behavior_regression_pass=true` |
| TG-P7 训练代理数据库实现 | [target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md)、[target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json)、[target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/) | TG-P7-R3 生成完整 opt-in proxy runtime database 和 active training config：默认 database components `26`，proxy database components `32`，proxy 路径 active split receivers `8`，duplicate names `0`，`runtime.database_path` 已接入 training bootstrap 和 `train.py`，repository unit database modified `false`，RuntimeFacade proxy database load 通过，并且本地 `64`-step CPU training smoke 完成 |
| TG-P7 active training probe | [target_geometry_training_probe_results_20260614.zh.md](target_geometry_training_probe_results_20260614.zh.md) | TG-P7-R4 完成 proxy 和 baseline 两个 active `8192`-step CUDA `WorldBatchVecEnv` 运行。Proxy final `ep_len_mean=662`、`ep_rew_mean=-282`；baseline final `ep_len_mean=677`、`ep_rew_mean=-235`。两者都在 `/tmp/cmo_tg_p7_active_probe` 下写出 checkpoints 和 final models |
| TG-P7 damage-event trace | [target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)、[target_geometry_damage_event_trace_20260614.json](review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json) | TG-P7-R5 对默认和 proxy database 执行固定 synthetic blast-fragmentation debug hits。Proxy event names 观测到全部 `8` 个 split receivers，默认 event names 观测到 `0` 个 split receivers，proxy retired parent rows observed `0`，`all_trace_cases_pass=true` |
| Stage-C guard 对齐 | [component_probability_surface_probe.py](../../../../../tools/maintenance/candidate_artifacts/component_probability_surface_probe.py) | 修复后的侧向部件几何会产生 `surface_incidence_cos=0.0`；Stage-C surface probe gate 已同步，component-specific rows 不再回退到 `global-fallback` |

## 当前边界

- 本状态只证明 TG-P1 来源/尺度 manifest、TG-P2 外壳区域候选、TG-P3 部件绑定、TG-P4 审阅包、
  TG-P5 测试点距离诊断、TG-P6 review-only mesh-derived 精细代理轮廓、表面部件候选、可视化 triage、
  独立部件复核视图、第一轮人工目检结论、五组 subagent 独立评估、第一轮 subagent 修正、R11 几何修复、
  R12 语义损伤几何候选、R13 内部 receiver 先验约束候选、R14 语义父子布局、R15 跨区 held
  分段、R16 整机 silhouette 诊断、R17 形状/摆放候选、R18 零外露形状固化、R19 中心线摆放候选、R20 最新摆放候选、R21 最新摆放固化、R22 ownership 拆分候选包、TG-P7-R1 runtime activation candidate packet、TG-P7-R2 in-memory behavior regression packet、TG-P7-R3 opt-in training proxy database packet、TG-P7-R4 active training probe 和 TG-P7-R5 targeted damage-event trace 已完成，不证明默认 runtime activation 已应用。
- 当前 Sketchfab 模型只作为外形审阅候选，不提供真实内部部件边界。
- 旧 FlightGear F-16 已归档为 GPL v2 强候选来源，不进入主线派生几何。
- 运行时近炸投影在默认路径仍按现有逻辑运行。TG-P7-R5 让带 feature flag 的
  `damage_model.hitboxes[].components` projection 可通过 `runtime.database_path`
  显式选择；仓库 unit database 未修改，默认路径保持 `26` components，proxy 路径为 `32`
  components，并且全部 `8` 个 proxy split receivers 已有 runtime component event-trace 覆盖。

## 下一步

1. 使用 TG-P7 proxy config 安排更长 opt-in proxy training 切片。
2. 增加 split-receiver damage-event exposure 的下游 policy/reward 诊断。
3. 将默认路径替换保留为后续独立验收决策。

## 验证提醒

每轮变更至少运行：

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

当前聚焦测试：

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
pytest -q tests/tools/test_airframe_geometry_review.py
pytest -q tests/tools/test_target_geometry_damage_event_trace.py
pytest -q tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
python tools/geometry/target_geometry_damage_event_trace.py --output docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tools/geometry/target_geometry_damage_event_trace.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/tools/test_target_geometry_damage_event_trace.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py examples/config/training/active/air_combat
```

任何默认路径替换前的更宽运行时检查：

```bash
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
pytest -q tests/architecture/damage_model
```

当前 TG-P7-R3 聚焦结果：Python geometry review tests `2 passed`；training
bootstrap 和 entry contracts `28 passed`；C++ loader smoke `24 passed`；review
packet 已重新生成；RuntimeFacade proxy database load 返回 `runtime_load_ok=true`；
本地 64-step CPU proxy training smoke 已完成，并写出
`/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/final_model.zip`；
active 8k proxy 和 baseline probes 均已完成，并在 `/tmp/cmo_tg_p7_active_probe`
下写出 final models；targeted TG-P7-R5 damage-event trace test `1 passed`，
proxy event names 已观测到全部 `8` 个 split receivers。
