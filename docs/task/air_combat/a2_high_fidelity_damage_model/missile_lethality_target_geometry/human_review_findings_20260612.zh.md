# F-16 目标几何人工目检结论

状态：`2026-06-12` visual review recorded / runtime interface held；已修正项目由 TG-P6-R10 追踪。

本记录是对
[review_packets/f16c_20260611/human_review_triage.html](review_packets/f16c_20260611/human_review_triage.html)
的第一轮人工目检结论。输入同时参考：

- [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json)
- [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json)
- [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)
- [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)

后续：[subagent_correction_results_20260612.zh.md](subagent_correction_results_20260612.zh.md)
记录 radar/IFF、nozzle 和 review semantics 的 scoped correction pass。

## 总结判断

TG-P6 的可视化复核入口有效地暴露了问题，但当前几何不能进入 `TG-P7` 运行时接入。

- `P6` 可以保持为 review-only candidate：外壳代理、表面部件候选、复核点和 triage 页面已经能解释问题。
- `P7` 必须 held：左右符号、鼻锥雷达/IFF 盒、发动机/喷口盒、表面到运行时部件交接仍有阻塞。
- 不应把这些结果声明为真实 F-16 工程几何、真实内部部件布局或已验收运行时损伤模型。

## 目检结论

| 区域 | 目检结论 | 处理决议 |
| --- | --- | --- |
| 左右翼和翼根 | `left_*` 部件成组绑定到 `right_wing`/`right_wing_root`，`right_*` 部件成组绑定到 `left_wing`/`left_wing_root`。这在顶视和正视图里是系统性镜像错位，不像 6 个孤立盒子错误。 | 先修坐标侧向约定或 left/right 命名映射；左右翼、翼根、翼面作动器和翼内油箱运行时交接全部 held。 |
| 机鼻/雷达/IFF | `apg68_radar_array` 和 `iff_interrogator` 对 `nose_radome` 的重叠为 `0.0`，中心在外。图上表现为旧部件盒与纠偏后的鼻锥外形高度/轴向不同步。 | 修 radar/IFF/nose 盒或外壳映射前，不接受 `surface_nose_radome` 交接。 |
| 4 m/6 m 鼻轴测试点 | `nose_axis_4m` 落在 `forward_fuselage`，最近部件 `cockpit_crew_station` 距 `0.2 m`，有 `6` 个候选；`nose_axis_6m` 最近外壳是 `nose_radome`，但点在 `apg68_radar_array` 盒内且外壳距离约 `0.349524 m`。 | 4 m 鼻向样例可解释为外壳/候选部件问题；6 m 暴露鼻锥外壳与旧雷达盒不一致。两者都只能作为诊断，不能直接接入近炸投影。 |
| 发动机核心 | `engine_core` 对 `aft_fuselage_engine` 只有低重叠，但中心仍在后发动机区域内，独立视图更像 aft bay/nozzle/tail-root 跨区边界。 | placement 可 review-only 条件接受；记录跨区语义，不按低 overlap 直接修盒子。 |
| 喷口/垂尾 | `afterburner_nozzle` 当前绑定到 `vertical_tail`，而 `surface_engine_nozzle` 又试图关联喷口、发动机核心和燃控。图上喷口和垂尾关系不干净。 | 修正喷口盒和区域归属；`surface_engine_nozzle` 与 `surface_vertical_tail_skin` 都 held。 |
| 中心翼梁/中心机身 | `wing_spar_center` 是跨机身/翼根的大跨度薄盒，低重叠符合可能的中心翼梁跨区语义；`surface_center_fuselage_skin` 另有 4 个 clean direct links。 | 中机身 4 个 clean links 可 review-only 接受；`wing_spar_center` held 为跨区语义待确认，不直接判为错误盒子。 |
| 座舱盖 | `surface_canopy` 没有专门运行时表面部件，只能关联 `cockpit_crew_station`。 | 增加 `dedicated_canopy_surface_component` 或明确 held。 |
| 进气道 | `surface_intake_lip_and_duct` 缺 `dedicated_intake_lip_or_duct_component`，且关联到仍需复核的 `engine_core`。 | 增加进气道/唇口运行时部件，或 held。 |
| 平尾 | 左右平尾表面没有内部部件链接，缺 `left/right_horizontal_tail_actuator_or_surface_component`。 | 增加平尾表面/作动器部件后再复核。 |
| 前机身蒙皮 | `surface_forward_fuselage_skin` 是当前唯一非人工复核表面，直接链接 `cockpit_crew_station`、`inertial_navigation_unit`、`nose_avionics_bay`。 | 可作为候选层面的相对干净项继续保留；仍不是运行时 accepted。 |
| 上/下方测试点 | `above_4m` 和 `below_4m` 没有近距离候选部件，图上也是远离外壳/部件的 sanity 点。 | 仅保留为诊断样例，不用于运行时投影决策。 |

## 必须修的项

1. 修复侧向符号/命名映射，并重新生成部件绑定、表面候选和 triage 页面。
2. 修复 `apg68_radar_array`、`iff_interrogator` 和 `nose_radome` 的高度/轴向关系。
3. 修复 `afterburner_nozzle`、`surface_engine_nozzle` 和 `vertical_tail` 之间的错误交接；`engine_core` 先记录为跨区边界候选。
4. 为 `surface_canopy`、`surface_intake_lip_and_duct`、左右平尾补显式运行时表面部件或写 held 决议。
5. 对 `wing_spar_center` 建立跨区语义；只有语义不能成立时再拆盒或重定位。

## 可接受的边界

- 可接受：TG-P6 复核产物本身作为 review-only 证据保留。
- 可接受：`surface_forward_fuselage_skin` 作为候选层面的相对干净表面继续跟踪。
- 不可接受：把当前表面部件候选直接接入近炸、连续杆或破片运行时投影。
- 不可接受：用当前结果声明真实内部部件几何、真实杀伤概率或具体弹种击毁结论。
