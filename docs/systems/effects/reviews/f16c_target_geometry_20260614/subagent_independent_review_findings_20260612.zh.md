# F-16 目标几何独立 subagent 评估汇总

状态：`2026-06-12` independent subagent review recorded / review-only / 部分项目已由 TG-P6-R10 修正接续。

本记录汇总 5 个只读 subagent 在中间 isolated-view packet 上完成的独立评估。该中间 packet 已从当前
最终结果面移除；本文件仅作为历史评估文字保留。当前 containment 证据以整机投影网格轮廓和后续
placement 队列为准。

后续：[subagent_correction_results_20260612.zh.md](subagent_correction_results_20260612.zh.md)
记录写入范围受限的修正回合。radar/IFF 和 nozzle 源盒已在该回合修复；在 R10 快照时，左右符号和
缺失 runtime receiver relation 仍 held。当前重生成 packet 状态以
[geometry_repair_results_20260612.zh.md](geometry_repair_results_20260612.zh.md) 为准。

R9 独立视图包快照包含 `85` 个页面：`22` 个现有部件绑定视图、`45` 个表面交接或缺失关系视图、
`18` 个测试点候选部件视图。全部产物都是 review-only，不是 runtime damage model、collision mesh、
真实 F-16 工程几何或真实武器杀伤权威。

## 评估结论

| 分组 | 独立结论 | 决议 |
| --- | --- | --- |
| 左右符号与翼面侧别 | 左右翼油箱、副翼作动器、前缘襟翼作动器和 beam 点呈系统性交叉；组件名、组件 `y` 符号、region 名和 nearest region 名称不自洽。 | 修复左右坐标/region 命名/绑定约定；翼面、翼根和 beam/wing projection 全部 held。 |
| 鼻部/雷达/前机身 | `apg68_radar_array`、`iff_interrogator` 对 `nose_radome` 为零重叠且在独立 side 视图中偏离 radome；`surface_nose_radome` clean direct links 为 `0`。`surface_forward_fuselage_skin` 有 3 个 clean candidate links。 | forward fuselage skin 可作为 review-only 相对干净候选；radar/IFF 修复或 held；nose radome handoff held。 |
| 发动机/尾喷/垂尾 | `engine_core` 在尾轴附近且中心在 `aft_fuselage_engine` 内，低 overlap 更像跨 aft bay/nozzle/tail-root 边界；`afterburner_nozzle` 轴向像尾喷但绑定到 `vertical_tail` 且相对 nozzle proxy 错层。 | `engine_core` placement 可条件接受为 review-only 跨区边界；`afterburner_nozzle` 必须修；`surface_engine_nozzle` held；垂尾与 `rudder_actuator` 可候选接受但 nozzle link 要移除或修复。 |
| 缺失运行时承接部件 | canopy、intake lip/duct、左右平尾几何表面都成立；问题是缺显式 runtime surface/actuator 承接关系。 | 接受为 review finding；分别新增/映射 `dedicated_canopy_surface_component`、`dedicated_intake_lip_or_duct_component`、左右平尾 surface/actuator，或显式 held。 |
| 中机身与大跨度部件 | `surface_center_fuselage_skin` 有 4 个 clean direct links，`wing_spar_center` 是横向大跨度薄盒，低 overlap 更像合理跨区结构待确认；`above_4m`/`below_4m` 是无近邻候选 sanity 点。 | 中机身 clean links 可 review-only 接受；`wing_spar_center` held 为跨区语义待确认，不按低 overlap 直接修；above/below 仅保留诊断。 |

## 修复优先级

1. 先修左右符号/region 命名/绑定约定，因为它污染翼面、翼根和 beam projection。
2. 修 `apg68_radar_array`、`iff_interrogator` 与 `nose_radome` 的高度/轴向关系。
3. 修 `afterburner_nozzle` 的 placement 和绑定，让喷口路径回到 `engine_nozzle`/尾喷语义。
4. 补 canopy、intake、左右平尾的显式 runtime surface/actuator relation，或写 held 决议。
5. 为 `wing_spar_center` 和 `engine_core` 记录跨区语义，不把低 overlap 自动等同于错误盒子。

## 已接受的 review-only 候选

- `surface_forward_fuselage_skin` 到 `cockpit_crew_station`、`inertial_navigation_unit`、`nose_avionics_bay` 可作为相对干净候选。
- `surface_aft_engine_bay_skin` 中 `electrical_power_bus`、`engine_fuel_control_unit`、`tail_hydraulic_pump` 可作为 clean direct links。
- `surface_center_fuselage_skin` 中 `center_fuselage_fuel_cell`、`data_link_terminal`、`flight_control_computer`、`mission_computer` 可作为 clean direct links。
- `surface_vertical_tail_skin` 与 `rudder_actuator` 可作为垂尾候选关系；`afterburner_nozzle` 相关关系不接受。

## 边界

- 缺 runtime relation 不等于表面不存在。
- 大跨度低 overlap 不自动等于几何错误。
- 测试点进入某个旧盒子不等于该旧盒子已通过几何复核。
- 当前所有结论都只是 review-only；不得据此接入近炸、连续杆、破片运行时投影，也不得声明真实内部结构、真实 Pk 或具体弹种击毁结论。
