# A2 目标外形与部件几何建模

状态：`2026-06-14` active follow-on / TG-P7-R5 split-receiver
damage-event trace pass；默认 unit database 和默认 runtime path 仍未改变。该子项目从
[杀伤链命中盒几何保真度缺口](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)
提升而来，用于把 F-16 从少量大长方体推进到可审阅的外壳、表面部件、旧内部部件关联和距离诊断。

语言：

- 英文辅文：[README.md](README.md)
- 中文主文：`README.zh.md`

输入：

- A2 指针：[../README.zh.md](../README.zh.md)
- 几何缺口 issue：[../../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)
- 几何审阅工具设计：[../../../issues/lethality_hitbox_geometry_fidelity_gap/geometry_visual_review_design_20260611.zh.md](../../../issues/lethality_hitbox_geometry_fidelity_gap/geometry_visual_review_design_20260611.zh.md)
- F-16 可视化 GLB：[../../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb](../../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb)
- F-16 审计 glTF：[../../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf](../../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf)
- F-16 当前损伤几何：[../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../examples/config/database/aircraft/units/f16c_block50.json)

## 目的

当前杀伤链已经能把起爆后的载荷、切割暴露和部件失效写成可诊断事实，但目标几何仍过粗：
外形、命中盒、部件盒和测试点距离被混在一起。这个子项目的目标是先把 F-16 的外壳形状、
部件脆弱区和测试点距离变成可审阅的数据，再决定近炸投影是否接入新的外壳代理。

本项目不是“还原真实 F-16 内部工程结构”。它只建立一套来源清楚、尺度可查、人工可审阅的
低精度几何代理，用来支撑更合理的近炸、连续杆和破片投影诊断。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| F-16 视觉资产 | active candidate | Sketchfab CC-BY-4.0 GLB 已进入 registry | 只负责运行时显示，不直接作为每帧碰撞网格 |
| F-16 审计资产 | active candidate | glTF 原始包、解包文件、hash 和 attribution 已保留 | 只提供外形审阅基础，不证明真实内部部件边界 |
| 旧 FlightGear F-16 | rejected for mainline derivation | 已归档到 `assets/archive`，来源强候选为 GPL v2 FlightGear | 不进入主线派生几何 |
| 当前命中盒 | known gap | issue 已记录 4 m 鼻向近炸无部件损伤等症状 | 不能继续当作真实外形或真实部件布局 |
| 运行时接入 | opt-in training proxy trace pass | TG-P7-R5 在 R3/R4 trainability 检查后，已在 proxy runtime component event names 中观测到全部 `8` 个 split receivers | 默认 database 和主投影路径仍是对照路径 |

## 范围

纳入：

- 建立 F-16 几何 manifest：来源、hash、坐标轴、尺度、外包尺寸和公开尺寸误差。
- 从 glTF 审计模型生成低精度外壳区域：机鼻、座舱、机身、进气道、机翼、翼根、发动机、尾翼和垂尾。
- 将现有 `f16c_block50.json` 部件盒绑定到外壳区域，标出明显不合理的位置和尺寸。
- 输出静态审阅包：HTML 场景、顶视/侧视/正视 SVG、manifest、部件绑定表和测试点诊断表。
- 对 MLF-5 暴露的鼻向、尾向、侧向、上下方位测试点计算最近外壳距离、最近部件距离和候选部件数。
- 在审阅包和距离诊断通过后，设计更贴近外形的精细几何代理：倾斜盒、凸包或简化外壳网格，
  并说明连续杆/破片路径是否应使用路径或扫掠求交。
- 把每个外壳区域整理成一个审阅用表面部件，并列出它能牵连的现有内部部件、明显漂移项和缺失关系。
- 生成语义外壳体积部件候选、可被 runtime schema 解析的 component JSON、逐体积独立视图，以及 direct
  receiver 和 cross-region receiver 的明确交接状态。
- 为现有内部/系统 receiver 生成球、圆柱、胶囊体和椭球体先验候选，并用父外壳 support bounds 约束，
  避免旧 AABB receiver 露出外壳。
- 形成运行时接入设计，明确哪些几何事实能被近炸/连续杆/破片投影消费。

不纳入：

- 不声明真实 F-16C Block 50 工程几何、真实内部设备边界或真实弹种杀伤率。
- 不通过调高概率掩盖几何问题。
- 不在第一轮把高模网格直接用于每帧碰撞。
- 不生成结构解体、残骸、碎片对象、Pk 或具体弹种击毁结论。
- 不重开已归档的 MLF-2、MLF-3、MLF-4 或 MLF-5 包。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固定子项目边界、输入和禁止声明 | issue 已记录几何缺口 | README、任务簇、状态和派发队列存在 | pass |
| `P1 Source And Scale` | 解析 glTF、确认坐标轴和公开尺寸缩放 | F-16 双模型资产存在 | `manifest.json` 记录来源、hash、轴向和尺度 | pass |
| `P2 Outer Regions` | 生成可审阅外壳区域 | P1 manifest 存在 | 外壳区域 JSON 和三视图能显示主要区域 | pass |
| `P3 Component Binding` | 把现有部件盒绑定到外壳区域 | P2 区域存在 | 部件绑定报告列出过大、过小、错位和越界项 | pass |
| `P4 Review Packet` | 生成 HTML/SVG/CSV 审阅包 | P2/P3 数据存在 | 人能在图面上同时看见外形、旧盒、部件和测试点 | pass |
| `P5 Lethality Diagnostics` | 将测试点解释成外壳/部件距离和候选部件数 | P4 审阅包存在 | 4 m 鼻向等样例不再只有“非直接命中”这一种解释 | pass |
| `P6 Fine Geometry Proxy` | 把低精度盒子推进到更贴近外形的代理，并补上外形命中到部件损伤的审阅用中间层 | P4/P5 审阅和诊断通过 | review-only OBB、薄棱柱、凸包候选、mesh-derived silhouette、表面部件候选、语义体积部件候选、内部 receiver 先验约束候选、视觉复核卡片、距离差和叠加图存在 | pass as parse-ready candidate |
| `P7 Runtime Interface Decision` | 决定是否把外壳代理接入近炸投影 | P6 代理通过审阅或明确 held | 形成有测试的 runtime 接入或 held 决议 | TG-P7-R5 opt-in proxy trace pass |

## 任务簇

- 任务簇计划：
  [missile_lethality_target_geometry_task_clusters_20260611.zh.md](missile_lethality_target_geometry_task_clusters_20260611.zh.md)
- 当前状态：
  [missile_lethality_target_geometry_current_status_20260611.zh.md](missile_lethality_target_geometry_current_status_20260611.zh.md)
- 第一轮派发队列：
  [missile_lethality_target_geometry_dispatch_queue_20260611.zh.md](missile_lethality_target_geometry_dispatch_queue_20260611.zh.md)
- 精细几何代理设计草案：
  [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md)
- 人工目检结论：
  [human_review_findings_20260612.zh.md](human_review_findings_20260612.zh.md)
- 几何修复结果：
  [geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md)
- 语义损伤几何实现结果：
  [semantic_damage_geometry_results_20260612.zh.md](semantic_damage_geometry_results_20260612.zh.md)
- 内部部件先验几何约束结果：
  [internal_component_prior_results_20260612.zh.md](internal_component_prior_results_20260612.zh.md)
- 语义父子部件布局结果：
  [semantic_parent_child_layout_results_20260612.zh.md](semantic_parent_child_layout_results_20260612.zh.md)
- 最新子部件候选固化结果：
  [subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md)
- 跨区 ownership 拆分候选结果：
  [cross_region_ownership_split_results_20260613.zh.md](cross_region_ownership_split_results_20260613.zh.md)
- 运行时激活候选结果：
  [target_geometry_runtime_activation_results_20260613.zh.md](target_geometry_runtime_activation_results_20260613.zh.md)
- 运行时行为回归结果：
  [target_geometry_runtime_behavior_regression_results_20260613.zh.md](target_geometry_runtime_behavior_regression_results_20260613.zh.md)
- 训练代理数据库结果：
  [target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md)
- Active training probe 结果：
  [target_geometry_training_probe_results_20260614.zh.md](target_geometry_training_probe_results_20260614.zh.md)
- Damage-event trace 结果：
  [target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)

## 输出和证据

计划输出：

- `tools/geometry/airframe_geometry_review.py`：只读几何审阅包生成器。
- `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_<date>/`：
  HTML、SVG、manifest、CSV 和审阅摘要。
- `f16c_geometry_mapping_candidate_<date>.json`：外壳区域、节点来源和部件绑定候选。
- 聚焦测试：JSON/schema 检查、路径存在检查、几何 manifest 校验，以及至少一组 F-16 审阅包生成测试。

已生成：

- [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json)：
  TG-P1 来源、hash、轴向、尺度和旧命中盒外包对比 manifest。
- [review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json](review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json)：
  TG-P2 第一版外壳区域候选；包含 `14` 个低精度审阅区域，并记录 glTF 实际节点为 `Object_*`，
  因此不能只靠节点名自动分区。
- 三视图草图：
  [top.svg](review_packets/f16c_20260611/top.svg)、
  [side.svg](review_packets/f16c_20260611/side.svg)、
  [front.svg](review_packets/f16c_20260611/front.svg)。
- 部件绑定报告：
  [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json)、
  [component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv)。
  R11 修复后，`26` 个部件中 `26` 个已绑定，`0` 个仍是 `needs_review`，`0` 个仍是左右符号阻塞，
  `2` 个是 review-only 跨区语义，`0` 个仍是 geometry-review-required 坏盒。
- 离线审阅页：[scene.html](review_packets/f16c_20260611/scene.html)。
  三视图现在叠加显示外壳区域、旧命中盒、部件盒和编号测试点。
- 测试点距离诊断：
  [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)、
  [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv)。
  当前覆盖 `10` 个鼻向、尾向、侧向、上方和下方点；修正外形区域后 `2` 个点位于外壳区域内。
  `nose_axis_4m` 位于 `forward_fuselage`，最近部件是 `dedicated_canopy_surface_component`，距离 `0.125 m`，
  候选部件数为 `7`；`nose_axis_6m` 距 `nose_radome` 约 `0.35 m`，receiver 和部件盒修复后候选部件数为 `5`。
- [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md)：
  TG-P6 第一版精细几何代理设计，定义 `obb`、`thin_prism`、`convex_hull` 和
  `simplified_shell` 的用途、边界和运行时前置条件。
- 精细几何代理候选：
  [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)、
  [fine_proxy_top.svg](review_packets/f16c_20260611/fine_proxy_top.svg)、
  [fine_proxy_side.svg](review_packets/f16c_20260611/fine_proxy_side.svg)、
  [fine_proxy_front.svg](review_packets/f16c_20260611/fine_proxy_front.svg)。
  TG-P6-R3 已从 `13,415` 个审计 glTF 顶点为全部 `14` 个 review-only 代理生成 top/side/front
  convex hull silhouettes；机头、座舱、主翼和平尾区域已按审计网格位置纠偏，并使用显式节点名单筛选；
  `inflated_fallback_count=0`，缺少顶点时不再放大区域硬凑轮廓。
- 人工审阅 dashboard：
  [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html)。
  TG-P6-R4 增加逐区域卡片，包含局部 top/side/front 放大图、部件叠加、节点筛选策略、
  fallback 禁用策略、hull 点数、review flags 和 candidate/review 状态。
- 表面部件候选：
  [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json)、
  [surface_component_candidate_20260611.csv](review_packets/f16c_20260611/surface_component_candidate_20260611.csv)。
  TG-P6-R5 将 `14` 个外壳区域整理为审阅用表面部件，并列出每个表面部件可能牵连的现有内部部件。
  R11 后 `0` 个表面部件仍需人工复核，`0` 个 runtime receiver link 缺失，`0` 个 surface row 被左右符号阻塞，
  `8` 个带跨区语义 held/candidate。
- 可视化人工复核入口：
  [human_review_triage.html](review_packets/f16c_20260611/human_review_triage.html)。
  TG-P6-R6 按左右符号、部件位置、表面部件交接和测试点几何 sanity 将复核项整理成视觉卡片；
  每张卡先写明复核问题、观察位置和需要做出的决策，再给出局部 top/side/front 叠加图，复核不再依赖肉眼读 CSV。
- 独立部件复核视图：
  [component_review_views/index.html](review_packets/f16c_20260611/component_review_views/index.html)、
  [component_review_views/manifest.json](review_packets/f16c_20260611/component_review_views/manifest.json)。
  TG-P6-R8 现在重新生成 `75` 个 review-only 独立页面：`26` 个现有部件绑定视图、`29` 个表面到单个承接部件交接视图、
  `20` 个测试点候选部件视图；每页都有单独的 top/side/front SVG，后续 subagent 评估不再需要从拥挤总览图里猜。
- 语义损伤几何候选：
  [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json)、
  [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv)、
  [semantic_damage_geometry_views/index.html](review_packets/f16c_20260611/semantic_damage_geometry_views/index.html)。
  TG-P6-R12 输出 `14` 个语义外壳体积部件和 `14` 个 `runtime_component_json_candidate`。
  Runtime schema 与 loader 已能解析这些几何字段，但 `runtime_active_component_count=0`；
  在 `TG-P7` 前不静默改变现有杀伤行为。
- 内部 receiver 先验几何候选：
  [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json)、
  [internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv)、
  [internal_component_prior_views/index.html](review_packets/f16c_20260611/internal_component_prior_views/index.html)。
  TG-P6-R13 为 `26` 个现有 receiver 生成 sphere/cylinder/capsule/ellipsoid 先验，并用父外壳
  support bounds 或跨区 union 约束；`post_constraint_outside_count=0`，`cross_region_held_prior_count=2`，
  `runtime_active_component_count=0`。当前 HTML/SVG 入口：
  [index](review_packets/f16c_20260611/internal_component_prior_views/index.html)、
  [manifest](review_packets/f16c_20260611/internal_component_prior_views/manifest.json)。
- 语义父子部件布局：
  [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json)、
  [semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv)、
  [semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html)。
  TG-P6-R14 将主审阅视图收敛为 `14` 个基于几何建模的父外壳部件，并把 `26` 个 receiver prior
  叠加到对应父图上；当前 `extra_receiver_slot_count=12`，`cross_region_held_receiver_count=2`，
  `runtime_active_component_count=0`。TG-P6-R15 进一步为两个红色 held receiver 增加审阅用分段：
  [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json)、
  [cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv)。
  其中 `engine_core` 被拆成 `3` 个发动机分段，`wing_spar_center` 被拆成 `5` 个翼梁分段；
  `held_segment_count=8`，`outside_whole_airframe_segment_count=0`，runtime ownership 仍保持 held。
  当前 HTML/SVG 入口：
  [index](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html)、
  [manifest](review_packets/f16c_20260611/semantic_parent_child_layout_views/manifest.json)。
- 跨区 ownership 拆分候选：
  [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json)、
  [cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv)、
  [cross_region_ownership_split_results_20260613.zh.md](cross_region_ownership_split_results_20260613.zh.md)。
  TG-P6-R22 为 `engine_core` 与 `wing_spar_center` 提出父级 receiver retirement 决策，并输出
  `8` 个 parse-ready split receiver candidates。Payload 仍是 AABB fallback records，
  `runtime_active_split_component_count=0`，ownership acceptance 仍为 false。
- TG-P7 运行时激活候选：
  [target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json)、
  [target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv)、
  [target_geometry_runtime_activation_results_20260613.zh.md](target_geometry_runtime_activation_results_20260613.zh.md)。
  TG-P7-R1 将 R22 split payload 转换为
  `F-16C_Block50.damage_model.hitboxes[].components` 的 unit-database component patch candidate：
  `candidate_component_count=8`，`runtime_schema_parse_ready_component_count=8`，
  `unit_database_patch_component_count=8`，
  `parent_receiver_retirement_candidate_count=2`，
  `runtime_active_component_count=0`；C++ unit-definition loader smoke test
  已能解析同形态 split receiver geometry。
- TG-P7 运行时行为回归：
  [target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json)、
  [target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv)、
  [target_geometry_runtime_behavior_regression_results_20260613.zh.md](target_geometry_runtime_behavior_regression_results_20260613.zh.md)。
  TG-P7-R2 只在内存中应用 component patch：base components `26`，
  projected components `32`，retired parent components `2`，split additions
  `8`，duplicate component names `0`，`behavior_regression_pass=true`。
- TG-P7 训练代理数据库：
  [target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json)、
  [target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/)、
  [target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md)。
  TG-P7-R3 生成完整 opt-in proxy runtime database：F-16 proxy components 为
  `32`，默认 database 保持 `26`；training bootstrap 和 `train.py` 已接通
  `runtime.database_path`，并新增 `A2_TARGET_GEOMETRY_PROXY_F16C_R22` active
  world-batch probe config。本地 `64`-step CPU world-batch smoke 已在该 proxy path 上完成。
- TG-P7 active training probe：
  [target_geometry_training_probe_results_20260614.zh.md](target_geometry_training_probe_results_20260614.zh.md)。
  TG-P7-R4 运行 active `8192`-step CUDA world-batch proxy probe 和匹配的默认数据库
  baseline。两者都完成并写出 checkpoints；proxy run 选择
  `target_geometry_training_proxy_database_20260613`，baseline 仍在默认 database 上。
- TG-P7 damage-event trace：
  [target_geometry_damage_event_trace_20260614.json](review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json)、
  [target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)。
  TG-P7-R5 对默认 database 和 proxy database 执行固定 synthetic
  blast-fragmentation debug hits。Proxy event surface 观测到全部 `8` 个 split
  receivers，默认 event surface 观测到 `0` 个 split receiver 名称，且 proxy events
  没有回退到已退休 parent receiver 名称。
- 整机 silhouette 约束修正候选：
  [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json)、
  [airframe_constraint_correction_candidate_20260611.csv](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv)。
  TG-P6-R16 对全部 `34` 个 receiver prior 和 held split segment 做 shape-aware
  top/side/front 整机 silhouette 采样。R21 最新候选固化后，当前 packet 记录：
  `silhouette_exposure_item_count=0`、`center_shift_reduces_item_count=0`、
  `size_or_shape_review_item_count=0`、`runtime_active_component_count=0`。
  当前 latest-placement 总览：
  [overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg)。
- 子部件形状/摆放候选：
  [subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json)、
  [subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv)、
  [subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html)。
  TG-P6-R17 针对 R16 暴露的 `14` 个子部件生成候选形状族和候选摆放，
  保留名义尺寸不缩小；TG-P6-R18 先将 `4` 个零外露候选固化到 review-only
  prior / held-segment 生成规则；TG-P6-R19 增加局部中心线候选；TG-P6-R20
  解决剩余 radar 和 cockpit 摆放问题。TG-P6-R21 将已接受的最新摆放固化到
  review-only 生成规则后，当前 packet 记录：
  `shape_placement_candidate_count=0`，
  `latest_candidate_total_outside_sample_count=0`，
  `runtime_active_component_count=0`。shape-placement 视图入口保留为空队列审计轨迹。
- 子部件形状候选固化结果：
  [subcomponent_shape_promotion_results_20260613.zh.md](subcomponent_shape_promotion_results_20260613.zh.md)。
  TG-P6-R18 将 `iff_interrogator`、`inertial_navigation_unit`、
  `engine_core_afterburner_segment` 和 `engine_core_hot_section_segment` 从 R17
  候选层固化到 review-only 生成规则；runtime activation 仍为 `0`。
- 子部件中心线摆放候选结果：
  [subcomponent_centerline_placement_results_20260613.zh.md](subcomponent_centerline_placement_results_20260613.zh.md)。
  TG-P6-R19 为剩余 `10` 个形状/摆放项增加保留尺寸的中心线候选；其中 `8` 个清零采样外露，
  `apg68_radar_array` 和 `cockpit_crew_station` 仍未解决。
- 最新子部件摆放候选结果：
  [subcomponent_latest_placement_results_20260613.zh.md](subcomponent_latest_placement_results_20260613.zh.md)。
  TG-P6-R20 解决剩余的 radar 和 cockpit 摆放问题，并将主复核图收敛为灰色整机线框加蓝色最新子部件候选。
- 最新子部件候选固化结果：
  [subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md)。
  TG-P6-R21 将 R20 最新摆放固化到 review-only prior 和 held-segment 生成规则。
  当前计数为 `internal_component_prior_shape_promotion_count=9`、
  `cross_region_held_segment_shape_promotion_count=5`、
  `subcomponent_shape_placement_candidate_count=0`。
- 跨区 ownership 拆分结果：
  [cross_region_ownership_split_results_20260613.zh.md](cross_region_ownership_split_results_20260613.zh.md)。
  TG-P6-R22 将两个剩余 ownership blocker 整理成 `TG-P7` 前明确的 accept / reject / keep-held 决策；父级 receiver retirement 和 runtime activation 仍未接受。
- 运行时激活候选结果：
  [target_geometry_runtime_activation_results_20260613.zh.md](target_geometry_runtime_activation_results_20260613.zh.md)。
  TG-P7-R1 生成带 feature flag 的 patch candidate，包含 `8` 个 parse-ready split
  receiver records；仓库 unit database 未修改，activation 前仍需 behavior regression。
- 运行时行为回归结果：
  [target_geometry_runtime_behavior_regression_results_20260613.zh.md](target_geometry_runtime_behavior_regression_results_20260613.zh.md)。
  TG-P7-R2 将 patch target 修正为 `damage_model.hitboxes[].components`，并在内存中验证父级退役和 split 追加投影。
- 人工目检结论：
  [human_review_findings_20260612.zh.md](human_review_findings_20260612.zh.md)。
  R7 历史快照：第一轮目检结论把 TG-P6 复核产物保留为 review-only 证据，并因左右符号、鼻锥
  radar/IFF、发动机/喷口和表面到运行时部件交接 held `TG-P7`；这些 blocker 后续经 R9/R10 细化，
  并已被 R11 当前修复结果替代。
- 独立 subagent 评估汇总：
  [subagent_independent_review_findings_20260612.zh.md](subagent_independent_review_findings_20260612.zh.md)。
  五个只读 subagent 分别评估左右翼、鼻部、发动机/喷口、缺失承接部件和中机身跨区部件；
  评估修正了第一轮目检中的粗粒度判断：`engine_core` 和 `wing_spar_center` 先按跨区语义 held/条件接受；
  在 R9 快照时，左右符号、radar/IFF、afterburner/nozzle 和缺失 runtime relation 仍是硬修项。
- Subagent 修正结果：
  [subagent_correction_results_20260612.zh.md](subagent_correction_results_20260612.zh.md)。
  两个写入范围受限的 subagent 已修复 `apg68_radar_array`、`iff_interrogator` 和
  `afterburner_nozzle` 源盒，并补充跨区部件和缺失 runtime link 的 review semantics；这是 R10 历史修正快照。
- 几何修复结果：
  [geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md)。
  R11 修复左右区域映射、翼面和翼根部件位置、座舱盖/进气道/平尾显式 receiver 组件，以及直接 surface
  handoff 规则。当前 component 和 surface `needs_review` 计数均为 `0`；`TG-P7` 只因 `engine_core`
  与 `wing_spar_center` 跨区语义 ownership 仍需明确而继续 held。
- `pytest -q tests/tools/test_airframe_geometry_review.py`：`2 passed`。
- `./build-workshop/ef_test --test-suite=components_basic`：构建 `ef_test` 后 `23` 个 case 通过。
- `pytest -q tests/architecture/damage_model`：`177 passed`；其中包括修复后的
  Stage-C 部件失效概率 surface probe 继续选择 component rows，而不是回退到
  `global-fallback`。

## 验收门

本子项目只有在以下条件满足后才能标记 accepted：

- F-16 审阅包能离线打开，并同时显示外形、旧命中盒、部件盒和测试点。
- manifest 记录 GLB/glTF 双模型分工、来源、hash、坐标轴、尺度和公开尺寸误差。
- 至少覆盖鼻向、尾向、侧向、上方和下方测试点，并输出最近外壳距离、最近部件距离和候选部件数。
- 每个外壳区域都有审阅用表面部件候选，并能说明它和现有内部部件的关系是否可靠。
- 每个现有部件和高风险表面交接都有独立 top/side/front 复核视图，不依赖多个部件挤在同一张小图里。
- 每个语义外壳体积候选都有独立 top/side/front 复核视图，并明确 direct receiver 与 cross-region
  receiver 的交接状态。
- 每个现有内部/系统 receiver 都有先验几何、父外壳约束、约束前后越界比例和独立 top/side/front
  复核视图；该层不得被当作真实内部工程几何。
- TG-P7 proxy database 与默认 database 分离生成，F-16 components 为 `32`，
  duplicate component names 为 `0`，并且只能由显式 `runtime.database_path`
  training config 选择。
- TG-P7 proxy damage-event trace 能在 runtime component event names 中观测到全部
  `8` 个 split receivers，而默认 database 观测到 `0` 个 split receiver 名称。
- 4 m 鼻向贴近外壳样例能被解释为具体几何/方向/候选部件问题，而不是无说明的零损伤。
- 所有文档继续拒绝真实 F-16 工程几何、真实 Pk、结构解体、残骸或具体弹种击毁声明。

## 残余和下一步

- MQ-9 几何可作为后续机型复用目标，但第一轮只做 F-16。
- 运行时近炸投影仍未在默认 F-16 unit damage model 中消费该代理。TG-P7-R5 已提供 opt-in
  training proxy database，其中 `8` 个 split receiver records 在代理路径 event-observable，
  默认对照路径仍保持 `26` components；本地 `64`-step training smoke、active
  `8192`-step proxy/baseline probe 和 targeted damage-event trace 均已通过。下一步可以进入更长
  proxy training，并配套下游 policy/reward 诊断；默认路径替换仍需独立验收。
- 结构解体、碎裂/残骸和 Pk 仍是后续独立子项目，不能并入本几何子项目。

## Archive

历史或被替换的状态、派发和审阅记录在出现 closeout surface 后移入
[archive/README.zh.md](archive/README.zh.md)。
