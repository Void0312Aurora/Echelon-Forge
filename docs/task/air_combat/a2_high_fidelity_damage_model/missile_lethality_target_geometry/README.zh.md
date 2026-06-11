# A2 目标外形与部件几何建模

状态：`2026-06-12` active follow-on / TG-P6 human review dashboard complete and manual review required。该子项目从
[杀伤链命中盒几何保真度缺口](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.zh.md)
提升而来，用于把 F-16 从少量大长方体推进到可审阅的外壳、部件区和距离诊断。

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
| 运行时接入 | held | 本项目先做审阅包和诊断字段 | 未经审阅前不改近炸投影主路径 |

## 范围

纳入：

- 建立 F-16 几何 manifest：来源、hash、坐标轴、尺度、外包尺寸和公开尺寸误差。
- 从 glTF 审计模型生成低精度外壳区域：机鼻、座舱、机身、进气道、机翼、翼根、发动机、尾翼和垂尾。
- 将现有 `f16c_block50.json` 部件盒绑定到外壳区域，标出明显不合理的位置和尺寸。
- 输出静态审阅包：HTML 场景、顶视/侧视/正视 SVG、manifest、部件绑定表和测试点诊断表。
- 对 MLF-5 暴露的鼻向、尾向、侧向、上下方位测试点计算最近外壳距离、最近部件距离和候选部件数。
- 在审阅包和距离诊断通过后，设计更贴近外形的精细几何代理：倾斜盒、凸包或简化外壳网格，
  并说明连续杆/破片路径是否应使用路径或扫掠求交。
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
| `P6 Fine Geometry Proxy` | 把低精度盒子推进到更贴近外形的代理 | P4/P5 审阅和诊断通过 | review-only OBB、薄棱柱、凸包候选、mesh-derived silhouette、距离差和叠加图存在 | pass as review candidate |
| `P7 Runtime Interface Decision` | 决定是否把外壳代理接入近炸投影 | P6 代理通过审阅或明确 held | 形成有测试的 runtime 接入或 held 决议 | planned |

## 任务簇

- 任务簇计划：
  [missile_lethality_target_geometry_task_clusters_20260611.zh.md](missile_lethality_target_geometry_task_clusters_20260611.zh.md)
- 当前状态：
  [missile_lethality_target_geometry_current_status_20260611.zh.md](missile_lethality_target_geometry_current_status_20260611.zh.md)
- 第一轮派发队列：
  [missile_lethality_target_geometry_dispatch_queue_20260611.zh.md](missile_lethality_target_geometry_dispatch_queue_20260611.zh.md)
- 精细几何代理设计草案：
  [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md)

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
  当前 `22` 个部件均有候选外壳区域，其中 `7` 个需要人工复核：`6` 个是左右翼命名与坐标正负号，
  `1` 个是 `wing_spar_center` 跨单侧翼区。
- 离线审阅页：[scene.html](review_packets/f16c_20260611/scene.html)。
  三视图现在叠加显示外壳区域、旧命中盒、部件盒和编号测试点。
- 测试点距离诊断：
  [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)、
  [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv)。
  当前覆盖 `10` 个鼻向、尾向、侧向、上方和下方点；`6` 个点位于外壳区域内。
  `nose_axis_4m` 位于 `forward_fuselage`，最近部件是 `cockpit_crew_station`，距离 `0.2 m`，
  候选部件数为 `6`；`nose_axis_6m` 位于 `nose_radome`，并进入 `apg68_radar_array`
  等部件盒。
- [fine_geometry_proxy_design_20260611.zh.md](fine_geometry_proxy_design_20260611.zh.md)：
  TG-P6 第一版精细几何代理设计，定义 `obb`、`thin_prism`、`convex_hull` 和
  `simplified_shell` 的用途、边界和运行时前置条件。
- 精细几何代理候选：
  [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)、
  [fine_proxy_top.svg](review_packets/f16c_20260611/fine_proxy_top.svg)、
  [fine_proxy_side.svg](review_packets/f16c_20260611/fine_proxy_side.svg)、
  [fine_proxy_front.svg](review_packets/f16c_20260611/fine_proxy_front.svg)。
  TG-P6-R3 已从 `13,415` 个审计 glTF 顶点为全部 `14` 个 review-only 代理生成 top/side/front convex hull
  silhouettes；`8` 个区域直接使用源边界筛选，`6` 个区域使用记录过的 inflated-bound fallback，进入
  `TG-P7` 前仍是高优先级人工复核项。
- 人工审阅 dashboard：
  [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html)。
  TG-P6-R4 增加逐区域卡片，包含局部 top/side/front 放大图、部件叠加、inflation 指标、hull 点数、
  review flags 和 candidate/review/hold 状态。
- `pytest -q tests/tools/test_airframe_geometry_review.py`：`2 passed`。

## 验收门

本子项目只有在以下条件满足后才能标记 accepted：

- F-16 审阅包能离线打开，并同时显示外形、旧命中盒、部件盒和测试点。
- manifest 记录 GLB/glTF 双模型分工、来源、hash、坐标轴、尺度和公开尺寸误差。
- 至少覆盖鼻向、尾向、侧向、上方和下方测试点，并输出最近外壳距离、最近部件距离和候选部件数。
- 4 m 鼻向贴近外壳样例能被解释为具体几何/方向/候选部件问题，而不是无说明的零损伤。
- 所有文档继续拒绝真实 F-16 工程几何、真实 Pk、结构解体、残骸或具体弹种击毁声明。

## 残余和下一步

- MQ-9 几何可作为后续机型复用目标，但第一轮只做 F-16。
- 运行时近炸投影是否消费外壳代理，需要在审阅包、距离诊断和精细几何代理审阅通过或在 `TG-P7`
  明确 held 后再决定。
- 结构解体、碎裂/残骸和 Pk 仍是后续独立子项目，不能并入本几何子项目。

## Archive

历史或被替换的状态、派发和审阅记录在出现 closeout surface 后移入
[archive/README.zh.md](archive/README.zh.md)。
