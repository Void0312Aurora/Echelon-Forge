# A2 高真实度空战毁伤模型

状态：`2026-05-26` Phase 0 已接受；Phase 1 最小补丁已开始并通过聚焦测试；Phase 2 已从 generated fallback 推进到首批 authored aircraft hitbox 覆盖，并新增飞机专用 `AircraftDamageState` overlay、overlay-driven 飞行动力学/推进/传感器派生、受损结构在高动压/高速包线下继续劣化的最小闭环、火灾/燃油泄漏/液压损伤的最小时间级联，以及 aileron/elevon/rudder/flap/thrust-vector/cyclic/collective 等命名控制组件损伤下推 roll/pitch/yaw authority 与 control-asymmetry 的最小 overlay；Phase 3 已从最小 `WarheadProfile` 数据通路推进到首个弹头族 effects 分配补丁、按弹头族 footprint 的近炸空间投射闭环、最小 relative-velocity-axis 空间方向耦合、引爆姿态轴驱动的参数化 orientation-pattern 证据、hitbox armor / projected exposure / warhead mechanism 的可审计采样脚手架、surface-incidence obliquity 证据字段、机制特定组件阈值、首个合成组件失效概率采样增量、显式 `FuzeProfile` 证据面、proximity fuze delay 的最小延迟爆轰调度、首个 fuze type trigger semantics 行为分支、首个组件级几何入口、数据库级 F-16/Su-35/MQ-9/MH-60R/E-3 代表性组件几何样例、`EffectsEvent` 主组件身份证据、critical/redundancy 对组件失效概率的最小语义，以及组件 `dependencies` 到相关系统/overlay 的最小传播脚手架；Phase 5 已启动 synthetic vulnerability evidence scaffold、补入 calibrated evidence gate，并把 vulnerability profile/evidence/authority/scale 和 surface-incidence row gate 写入 `EffectsEvent` 审计面。当前闭合了 PN miss-distance baseline、HP-first bypass 反转、live missile `EffectsEvent/DamageReport` 记录、structured-air physical effects 不直接写 RL `Score` 的行为/静态守卫、aircraft damage-state 同步、nose/fuselage/wing 命中后果分化、F-16/Su-35/MQ-9/MH-60R/E-3 结构化 authored hitbox 回归，当前 aircraft units 库全部达到 20+ 代表组件、补齐机制阈值且组件中心位于父 hitbox 内，air-specific structure/flight-control/hydraulic/propulsion/fuel/avionics/crew overlay 回归，overlay 下推 FlightModel/Propulsion/fuel leak 的动态约束回归，燃油泄漏真实消耗 `FuelSystem` / `Mass` 燃油质量回归，火灾/液压/燃油级联持续影响结构、航电、机组、飞控和平台能力回归，航电/机组损伤下推传感器 range/Pd/noise/track-memory 回归，命名控制组件损伤下推 roll/pitch/yaw authority 与 control-asymmetry 并收紧 turn-rate 回归，受损机体 high-energy flutter/overstress 暴露回归，warhead family/mass/lethal-radius/synthetic provenance 与 fuze type/trigger-radius/delay/reliability/synthetic provenance 进入 missile runtime、`EffectsEvent`，diagnostics-only 局部命中 effects 差异测试、距离衰减近炸场投射测试、弹头族 footprint 覆盖测试、continuous-rod velocity-axis 与 detonation-attitude-axis 近炸方向性测试、surface-incidence obliquity 证据测试、armor/exposure 机制采样测试、component-threshold 机制敏感度测试、component-failure probability 采样测试、F-16/Su-35 与 UAV/直升机/C2 代表性数据库组件主命中证据测试、组件冗余/关键性失效概率调制测试、组件依赖传播到液压/飞控/航电 overlay 的回归测试、fuze profile runtime/event 测试、fuze delay detonation-time 回归、contact fuze 不把 near-miss radius 误当作接触触发的回归、timed fuze 不依赖近炸门而按发射后延时独立起爆的回归，以及组件化 wing hitbox 内 fuel cell / flight-control actuator 局部命中分化回归，`EffectsEvent` 已补 miss distance、目标机体系起爆点、闭合速度、导弹速度轴、引爆姿态轴、direct/projection 命中形态、空间效应尺度、装甲耦合尺度、投影暴露尺度、机制效应尺度、surface-incidence cos、组件阈值尺度、组件失效概率、失效采样值、失效触发次数、组件命中数量、主组件名称/系统/冗余组/关键性、引信类型、触发半径、延迟、可靠性、synthetic 标记，以及 vulnerability profile/evidence/authority/provenance/aspect/closure/scale 等证据字段，且 `detonation_time_s` 能按 `fuze_delay_s` 晚于 `nearest_approach_time_s`；F-16 synthetic vulnerability profile 对弹头族/aspect/closure/near-miss 的 structured damage 调制测试、synthetic vulnerability 不具备 Pk/确定性引信权威的 evidence-gate 回归、vulnerability 调制进入事件审计面的回归、surface-incidence 只作为 evidence/row gate 的回归，以及空战 reward surface 对非终局 `DamageReport` 连续毁伤信号的一次性消费回归。

本子项目承接两份 forward 评估：

- [空战毁伤模型评估](../../../forward/air_combat_damage_model_evaluation_20260522.md)
- [代码现实交叉评估](../../../forward/air_combat_damage_model_cross_eval_20260522.md)

它服务于 `1v1` 真实度梯度课程，但不是 RL 便利性任务。高真实度毁伤模型的目标是让武器事件先产生物理可解释的局部结构/子系统毁伤，再从平台状态推导 mission kill、sensor kill、mobility kill、forced landing 或 lost。训练 reward、课程捷径和 legacy `health` 读数只能消费这些结果，不能反向定义物理毁伤权威。

## 设计立场

不可妥协原则：

- `Health.current_hp` 可以保留为兼容读数，但不能作为空战毁伤和击杀权威；
- 权威输入来自 weapon event：近炸/撞击、引信状态、miss distance、相对几何、战斗部类型、目标脆弱性；
- 毁伤首先作用到局部结构、飞控、推进、燃油、传感器、座舱/飞行员等子系统；
- 平台 kill state 必须从子系统和结构状态推导，而不是由单一 `damage` 标量直接扣血得到；
- 随机性只能表示显式建模的不确定性或物理采样，不能掩盖缺失几何、缺失脆弱性或缺失引信模型；
- RL reward 和课程 shaping 属于消费层，不属于 physical effects authority。

## 当前问题

当前代码存在两个并行毁伤路径：

- legacy air path：`Health` 存在且没有结构化 hitbox 时，直接 `hp -= missile.damage`，`hp <= 0` 即摧毁；
- naval subsystem path：`HitboxConfig + SystemHealth + PlatformDamageState` 通过局部 hitbox 和子系统状态推导能力损失。

Phase 0 审计修正了一点：多数带 `airframe.length_m` 的飞机在 spawn 时已经会生成 procedural hitbox，并挂载 `SystemHealth` 与 `PlatformDamageState`。但是交叉评估中的核心问题仍成立：legacy HP 分支在 `default_effects_model.cpp` 中先执行，并且可以在几何/子系统毁伤前提前 `return`。这意味着任何“飞机子系统毁伤”实现，如果不先处理 HP-first bypass，就可能永远不会成为权威路径。

## Phase 0 预检门

Phase 1 行为代码不得开始，除非下列门全部关闭并记录。当前 `A2-P0.1` 到 `A2-P0.6` 均已闭合，证据记录见 Phase 0 审计：

- `PlatformLossState` 枚举审计：确认没有 raw integer 比较依赖 `Lost = 4`；如果需要 `ForcedLanding`，只能 append-only 或采用 aircraft overlay state；
- Python health observer 审计：盘点 `health > 0`、`get_unit_health`、`is_unit_active` 等调用，准备 HP 从权威杀伤变为派生读数后的语义迁移；
- `ShipPlatform` filter 审计：确认 `NavalDamageStateUpdate` 与其他 ship-only 系统边界，决定新增 aircraft damage update 还是泛化 damage update；
- aircraft JSON inventory：列出所有飞机类型，决定 per-aircraft authored hitboxes 还是 generated whole-aircraft fallback；
- `Score` write-point 审计：把 effects model 内的 kill reward / kills_confirmed 写点迁移计划记录清楚；
- PN miss-distance benchmark：在 head-on、tail-chase、beam、high-off-boresight 等几何上测量当前制导 miss distance 分布，再决定是否移除 RNG fuze。

当前 Phase 0 证据：

- [Phase 0 预检审计 - 2026-05-26](phase0_preflight_20260526.zh.md)

P0.6 基线摘要：

| 几何 | `proximity_min_dist_m` | 判读 |
|----|----:|----|
| head-on | 10.36 m | 可达近炸窗口，但默认生成 hitbox 未必必然有结构交点 |
| tail-chase | 7446.37 m | 明显能量/追赶不可达 |
| beam | 501.30 m | 横穿 LOS rate 下 miss distance 明显放大 |
| high-off-boresight | 0.02 m | 可形成稳定结构命中，用作 Phase 1 live missile regression |

因此 deterministic fuze 继续暂缓：当前 miss distance 已呈现明显几何差异，不能在缺少 warhead/fuze/脆弱性校准前简单移除 RNG hit roll。

## 实施阶段

### Phase 1：飞机结构化 hitbox 与 HP bypass 反转

状态：`minimal_patch_in_progress / focused tests passing`。

目标：

- 让带结构化毁伤状态的飞机不再通过 HP-first branch 直接击杀；
- 飞机 spawn path 能挂载 `HitboxConfig`、`SystemHealth`、`PlatformDamageState` 或等价 aircraft damage state；
- kill state 从平台毁伤状态推导；
- reward/score 写入从 physical effects path 解耦。

本轮已完成的最小补丁：

- structured aircraft / C2Node 若同时具备 `HitboxConfig + SystemHealth + PlatformDamageState`，不再进入 legacy HP-first kill branch；
- structured aircraft physical effects path 不直接写 `Score.total_reward` / `hits_landed` / `kills_confirmed`；毁伤事实通过 `EffectsEvent` / `DamageReport` 暴露，由消费层解释；
- `debug_apply_proximity_hit` 对 structured aircraft 使用目标中心线合成命中点，避免 F-16 generated hitbox 被调试命中点绕开；
- `debug_apply_local_proximity_hit` 允许用目标机体系局部坐标构造 diagnostics-only 命中，用于稳定验证不同 hitbox 后果；
- `ProximityFuze` live missile 路径会围绕 effects model 记录 `EffectsEvent` 与 `DamageReport`；
- 新增 `AircraftDamageStateUpdate`，只同步 Aircraft/C2Node 的 damage-state kill flags 和 `Lost` 析构，不移除或泛化舰船 `ShipPlatform` filter；
- 默认 1v1 发射测试改为守卫“不误锁/不误伤友方 + 事件目标一致”，不再要求默认几何一发必杀。

风险：中高。它会改变导弹命中飞机后的主行为路径。

### Phase 2：飞机子系统级联效果

状态：`overlay_dynamic_coupling_started / focused tests passing`。

目标：

- 推进：推力衰减、单发/双发差异、火焰熄灭；
- 飞控/液压：操纵面效率、速率限制、控制延迟；
- 结构：g-limit、flutter boundary、翼梁/蒙皮损伤；
- 燃油：泄漏、起火、续航/返场约束；
- 传感器/航电：雷达、RWR、数据链、导航能力下降；
- 座舱/飞行员：任务能力和控制能力下降。

风险：中。需要触及飞行动力学和传感器行为消费层。

当前已完成的最小结构化效果：

- nose/radar 命中会降低 sensor capability，并降低雷达 `max_range`；
- fuselage engine/fuel 命中会降低 mobility capability，削弱推力并增加 fuel leak；
- wing/flight_control 命中会降低机动能力，收紧 `max_g`、`max_turn_rate`、`max_accel`、`max_climb_rate`；如果 authored wing 同时保护油箱，也会触发 fuel leak；
- 单次近炸事件对 structured aircraft 的平台级 mission/mobility/sensor/survivability 扣减按能力类别归一化，避免 authored hitbox 越细、重叠越多就把一枚近炸放大成直接 `Lost`；
- E-3 C2Node 已补 authored hitbox：cockpit/command、radar/data-link、fuel/avionics、engine、wing/flight-control；
- F-16、Su-35、MQ-9、MH-60R、E-3 已补 authored structured hitbox，覆盖座舱/传感器、机身燃油/航电/数据链、推进、机翼/旋翼/飞控等首批关键区域；
- 新增测试证明上述三类后果不会退化为同一种 damage scalar。
- 新增 `AircraftDamageState` 作为飞机专用 overlay，记录 `structural_integrity`、`flight_control_integrity`、`hydraulic_integrity`、`hydraulic_pressure_availability`、`roll_control_integrity`、`pitch_control_integrity`、`yaw_control_integrity`、`control_asymmetry`、`propulsion_integrity`、`fuel_system_integrity`、`avionics_integrity`、`crew_effectiveness`、`pilot_effectiveness`、`mission_crew_effectiveness`、`command_navigation_integrity`、`fire_severity`、`fuel_leak_severity`、`fuel_imbalance_severity`、`flammable_fluid_exposure`、`ignition_source_severity`、`fire_suppression_integrity`、engine/wing/fuselage/mission fire-zone severity 与 forced-landing / subsystem-kill 标志；
- effects model 会把 authored hitbox 命中映射到 air-specific overlay，再由 overlay 下推到兼容层 `PlatformDamageState`，避免后续飞机毁伤继续挤在舰船语义字段里；
- 新增 diagnostics-only `debug_get_aircraft_damage_state`，用于回归验证不同 hitbox 对飞机专用子系统的影响。
- 新增 `AircraftDamageBaseline`，保留飞机初始 FlightModel/Propulsion/fuel-leak 基线；`AircraftDamageStateUpdate` 每帧从 overlay 派生 `max_turn_rate`、`max_accel`、`max_climb_rate`、`max_g`、`max_speed`、推力和燃油泄漏，而不是在命中瞬间一次性手改动力学字段；
- 新增最小 control-axis overlay：aileron/elevon/rudder/flap/thrust-vector/cyclic/collective 等命名控制组件命中会按组件名称降低 `roll_control_integrity`、`pitch_control_integrity` 或 `yaw_control_integrity`，单侧控制面和推力矢量损伤会提高 `control_asymmetry`；`AircraftDamageStateUpdate` 先把这些轴向字段下推到 `FlightModel.max_turn_rate`、`max_accel`、`max_climb_rate`、`landing_speed` 与 `taxi_turn_rate` 等外层约束，但仍未改写核心飞控 torque law；
- 新增最小 hydraulic pressure overlay：hydraulic pump/source 命中会降低 `hydraulic_pressure_availability`，flight-control actuator/servo 的 `hydraulic_power` 依赖会产生较小压力损失；`AircraftDamageStateUpdate` 会把压力不足与 `hydraulic_integrity` 一起投射到 flight-control 派生和 mobility capability。该字段是 pressure/capacity 工程代理，不是液压回路、管线、蓄压器或压力-作动器曲线。
- 拆分 propulsion 与 fuel：油箱命中会降低燃油系统并增加 fuel leak，但不再直接等价发动机/推进损伤；发动机/推进命中才降低 thrust baseline 派生值。
- fuel feed/control 与 fuel storage 后果继续分化：命名 `*_fuel_feed` / `*_fuel_control*` 组件和 `edge_type=fuel_feed` 依赖会额外降低 `propulsion_integrity`，表示最小 engine starvation 后果；普通 wing/fuselage fuel cell 仍主要造成 fuel/fuel leak/fire risk，不直接等价 thrust loss；命名 left/right wing fuel storage 会额外写入 `fuel_imbalance_severity` 并随时间轻微增加 control asymmetry / 降低 roll authority，中心机身 fuel cell 和 engine fuel feed 不触发该左右不平衡语义。
- 新增最小 fire-source / suppression / zone overlay：fuel/hydraulic leak 会累积 `flammable_fluid_exposure`，engine/avionics/mission-system 损伤会累积 `ignition_source_severity`，E-3 engine fire bottle 已从普通 `fuel` 组件改为 `fire_suppression` 组件；`AircraftDamageStateUpdate` 会从 `ComponentDamageState` 的 suppression 组件/冗余组可用性派生 `fire_suppression_integrity`，并在命名冗余组存在时优先消费组可用性而不是单件完整性，随后保守调制 fire growth / extinguish decay。本轮还新增 engine bay、wing、fuselage、mission bay 四个 fire-zone severity，用组件/系统命名把局部火源投射到不同二次损伤方向：engine zone 偏 propulsion/fuel，wing zone 偏 flight-control/hydraulic/fuel/structure，fuselage zone 偏 crew/structure，mission zone 偏 avionics/mission crew/command-navigation。该路径只证明局部 fire-zone 代理能进入组件状态和级联，不是校准起火概率、灭火成功概率、舱段火灾模型或真实平台 fire-system authority。
- 新增 `structural_overstress` 与 `flutter_exposure` 诊断记忆：结构已受损的 aircraft 会在高动压/高 Mach 包线中持续累积暴露，并缓慢降低 `structural_integrity`，随后通过既有 overlay 派生进一步收紧 `max_g` 等飞行动力学限制；
- 该闭环显式避免把普通受损巡航或低速失速误判为 flutter：受损结构是前置条件，失速贡献还需要 high-energy gate，因此它是 Phase 2 的最小高能包线退化模型，不是完整结构疲劳/颤振求解器。
- 新增传感器基线派生：`AircraftDamageBaseline` 记录初始 `Sensor` range、Pd、噪声和 track memory；`AircraftDamageStateUpdate` 每帧按 `avionics_integrity`、`crew_effectiveness`、`mission_crew_effectiveness` 与 `command_navigation_integrity` 派生传感器能力，使 cockpit/avionics/mission/command 命中会降低 BVR 感知能力，而 wing/flight-control 命中不会误降传感器。
- 新增最小机组/任务岗位后果分解：F-16 cockpit crew station 命中主要降低 `pilot_effectiveness` 并下推机动/飞控派生；E-3 mission operator consoles 命中主要降低 `mission_crew_effectiveness` 并下推任务/传感器能力；E-3 command/navigation suite 命中主要降低 `command_navigation_integrity` 并下推任务/传感器能力。新增 `test_phase2_crew_consequences_distinguish_pilot_mission_and_command_roles` 回归证明三类命中不会继续退化为单一 `crew_effectiveness` 标量。
- 新增最小损伤级联：`AircraftDamageStateUpdate` 每帧从 fuel leak severity 扣减 `FuelSystem` 内/外挂油并同步 `Mass` 燃油质量；火灾会按燃油、液压、航电损伤、可燃流体暴露、点火源和泄漏活动持续升高，并受 fire suppression integrity 保守抑制，随后传播到结构、航电、机组、液压和燃油系统；液压损伤会继续拖累飞控并增加结构过载暴露；这些级联也会下推平台 mission/sensor/mobility/survivability 能力。

仍未完成：完整飞控/液压控制律耦合、控制面力矩/速率/延迟、液压回路依赖、完整火灾传播/舱段/烧穿时间线、真实 suppression bottle/nozzle/agent/distribution 模型、冗余系统依赖图、flutter 边界、真实座舱/飞行员生理伤害与人员替代/任务流程模型、战斗部空间效应模型、确定性引信和脆弱性/Pk 校准。当前 authored hitbox、overlay 与级联是工程化结构化内容，不应宣称为全高保真 vulnerability evidence。

### Phase 3：战斗部 profile

状态：`profile_fuze_delay_started / focused tests passing`。

目标：

- 从单一 `damage` 标量转到 `WarheadProfile`；
- 支持 blast、fragmentation、continuous rod、hit-to-kill 等族；
- 旧 weapon JSON 可通过 synthetic profile 兼容加载，但必须在诊断中标记为 synthetic。

当前已完成的最小数据通路：

- `warhead.type/mass_kg/lethal_radius/damage` 从 weapon JSON 进入 `MissileTuningDefinition`；
- 运行时 `MissileTuning` 与 `Missile` 携带 `WarheadProfile`，并保留 `damage_scalar_synthetic` 以标明旧标量兼容层；
- `EffectsEvent` 暴露 `warhead_mass_kg`、`warhead_lethal_radius_m`、`warhead_profile_synthetic`、`damage_scalar_synthetic`；
- `EffectsEvent` 同步暴露 `miss_distance_m`、目标机体系 `detonation_local_forward/right/up_m`、`closure_mps`、`missile_axis_forward/right/up` 和 `warhead_orientation_axis_forward/right/up`，用于审计近炸几何、局部起爆点、速度轴与引爆姿态轴的弹头 footprint 方向性；
- live proximity fuze 的 `effect_family` 不再硬编码为固定字符串，而是来自 missile warhead profile；
- AIM-120C、AIM-9X、R-77-1 现有 JSON 在缺少显式 `damage` 时会以 warhead mass 生成 synthetic damage scalar，并在 diagnostics 中标记。
- `default_effects_model` 对 structured aircraft 引入首个弹头族 effects 分配：blast 更偏结构/火灾/破口，blast-fragmentation 保持平衡基线，continuous rod 更偏机翼/飞控/结构切割类后果，hit-to-kill 更偏局部系统杀伤且低火灾扩散；
- 新增 diagnostics-only `debug_apply_profiled_local_proximity_hit`，用于在固定目标机体系命中点下对比不同 `WarheadProfile`，避免把弹头族 effects 测试绑定到导弹飞行几何随机性。
- 新增近炸空间投射最小闭环：structured aircraft 若没有直接 hitbox 交点，会在战斗部 lethal radius 的保守局部范围内寻找受影响 hitbox，并按弹头族设定投射半径、衰减曲线和最大影响 hitbox 数；blast/fragmentation 类宽域弹头优先按区域 hitbox 形成有限多区域覆盖，避免被同一翼面内多个细组件候选挤占 footprint，continuous rod 较窄，hit-to-kill 保持强局部化；远离机体的 near miss 仍保持无结构化毁伤。
- 近炸投射已改为按系统类别保留局部场强：同一近炸事件可以覆盖多个区域，但某个弱覆盖系统不会把最近 hitbox 的强场错误套用到所有子系统，因此近炸侧掠仍弱于直接命中对应关键 hitbox。
- 新增最小 relative-velocity-axis 空间方向耦合：无直接 hitbox 交点的近炸投射会把导弹速度轴转入目标机体系，并按候选 hitbox 相对该轴的径向/轴向关系调制 footprint；continuous rod 对横向扫掠机翼/飞控更敏感，hit-to-kill 更偏轴向局部，blast/fragmentation 只做较弱方向修正。
- 新增首个 warhead spatial sampling evidence：近炸投射不再只记录最近 N 个 hitbox 和距离衰减，还会按弹头族生成参数化采样证据。fragmentation / blast-fragmentation 使用战斗部质量推导破片样本数、目标暴露面积、球面稀释和距离能量尺度，估算破片命中数与命中比例；continuous rod 使用杆段样本数、目标展向、环形扫掠几何、速度轴横向权重和引爆姿态轴 orientation-pattern 权重估算杆命中数。该采样会调制近炸候选 effect scale，并通过 `EffectsEvent` 暴露 `warhead_spatial_sample_count`、`warhead_spatial_hit_estimate`、`warhead_spatial_hit_fraction`、`warhead_spatial_energy_scale`、`warhead_spatial_pattern_scale`、`warhead_orientation_axis_forward/right/up` 与 `warhead_orientation_pattern_scale`。
- 新增首个 warhead mechanism sampling scaffold：直接命中和近炸投射都会消费 authored hitbox 的 `armor_mm`、局部投影暴露面积、弹头族机制容量、距离质量和 velocity-axis 权重；低装甲/高暴露 hitbox 会得到更强机制尺度，高装甲/低暴露 hitbox 会削弱 effects severity。fragmentation / blast-fragmentation 载荷现在额外记录 `mechanism_fragment_areal_density_per_m2`，以参数化方式暴露破片数、爆距球面稀释、姿态 pattern 和目标暴露面积形成的破片通量/面密度证据；blast / blast-fragmentation 载荷现在额外记录 Hopkinson-Cranz / Sachs 风格的 `mechanism_blast_scaled_distance_m_kg13`，使超压/冲量代理至少能反查到装药质量与爆距尺度，而不是只暴露结果化压力值。
- 新增 surface-incidence obliquity evidence：effects model 会从局部命中点、候选 hitbox / component 的轴对齐表面法向和目标机体系导弹速度轴估算 `surface_incidence_cos`，并在事件顶层暴露为 `mechanism_surface_incidence_cos`、在主组件暴露为 `component_primary_mechanism_surface_incidence_cos`、在每个 `ComponentMechanismLoadRow` 暴露为 `mechanism_surface_incidence_cos`。该值被限制在 `[0, 1]`，用于区分近似法向入射和擦掠/斜入射；无有效导弹轴或无有效几何时为 `0`。它是 obliquity 证据，不是杀伤、Pk、确定性引信或校准穿透/切割权威。
- 新增首个 component-threshold scaffold：同一 hitbox 内的 `flight_control`、`fuel`、`radar/avionics`、`engine`、`cockpit/crew` 和 `structure` 不再共享完全相同的系统扣减尺度，而是按弹头族机制使用不同敏感度；例如 continuous rod 对飞控/结构更敏感，blast 对燃油/结构更敏感，hit-to-kill 对局部传感器/座舱/发动机更敏感。
- 新增首个合成 component-failure probability scaffold：直接命中和近炸投射会按 system severity、mechanism scale、component threshold scale、未校准 mechanism-load evidence（破片能量、破片面密度、穿透裕度、爆轰超压与冲量、连续杆切割裕度）和 direct/projection 形态生成概率，使用导弹 RNG 进行可重复采样；若采样触发，则给对应 aircraft overlay / platform damage 施加额外失效冲击。授权 vulnerability evidence row 仍会覆盖该 synthetic sigmoid 概率，并在事件面标记为 calibrated row 来源。
- 新增显式 `FuzeProfile` 数据通路：weapon JSON、`MissileTuning`、运行时 `Missile` 和 `EffectsEvent` 记录 fuze `type`、`trigger_radius_m`、`delay_s`、`reliability`、`synthetic` 与 provenance；AIM-120C/R-77-1 先标为 radar proximity，AIM-9X 先标为 laser proximity。
- live proximity fuze 继续使用最近点后一帧触发判定和 RNG hit gate，但现在由 `FuzeProfile.trigger_radius_m` 决定触发半径，并用 `FuzeProfile.reliability` 调制既有命中概率；`delay_s` 会把 effects 结算调度到 `nearest_approach_time_s + delay_s`，使 `detonation_time_s` 与 `nearest_approach_time_s` 在事件中真实分离。
- 新增首个 fuze type trigger semantics 行为分支：`radar_proximity` / `laser_proximity` / `proximity` 仍按近炸触发半径工作；`contact` / `impact` 不再把近炸半径当作触发条件，而是要求导弹位置到目标 authored hitbox 表面进入很小的接触容差，避免“近失但未接触”被误记录为接触起爆；当前 live contact/impact 事件还会记录表面距离、穿入深度、接触容差和是否进入 hitbox 的几何证据；`timed` 按发射后 `delay_s` 独立调度起爆，即使未进入近炸门也会生成可审计的 timed-fuze event，后续是否造成毁伤仍由战斗部 footprint / hitbox 几何决定。
- 新增首个 proximity-fuze target-signature scaffold：`radar_proximity` 会按目标 RCS/aspect 代理调制有效引信可靠度，`laser_proximity` 会按目标 hitbox 投影几何代理调制有效引信可靠度；`EffectsEvent` 记录 `fuze_signature_source`、`fuze_target_signature`、`fuze_signature_scale` 与 `fuze_effective_reliability`。该调制仍保留 RNG gate，只是让近炸引信开始消费目标反射/几何证据，不等价于校准雷达/激光引信模型。
- 新增首个组件级几何入口：`damage_model.hitboxes[].components[]` 可声明 hitbox 内的组件名称、系统、局部 offset/size、armor、threshold scale、按弹头族区分的 `mechanism_thresholds`、冗余组和关键性；loader 会保留该数据，effects model 在直接命中和 continuous-rod / hit-to-kill 等窄 footprint 近炸投射中优先按组件局部几何/装甲/组件机制阈值采样，blast/fragmentation 类宽 footprint 近炸则优先保留区域 hitbox 覆盖以体现邻近区域效应。F-16 数据库已从首个 wing fuel cell / aileron actuator / wing spar 样例扩展到 22 个代表组件，覆盖 fire-control radar、cockpit、nose avionics、IFF、fuselage fuel、mission computer、data link、navigation、power bus、flight-control computer、engine core、afterburner nozzle、engine fuel control、hydraulic pump、rudder actuator、wing fuel、aileron、leading-edge flap actuator 和 wing spar 等挂点，并为这些 fighter 组件声明 blast / fragmentation / blast-fragmentation / continuous-rod / hit-to-kill 机制阈值；Su-35S 已扩展到 23 个代表组件，覆盖 nose radar/cockpit/avionics/IRST、fuselage fuel/avionics/data-link/navigation/power/flight-control computer、左右发动机 core/fuel-feed/thrust-vector actuator 和机翼 fuel/elevon/leading-edge flap/spar 组件与同类机制阈值；MQ-9、MH-60R、E-3 已分别扩展到 23/22/27 个代表性 UAV/直升机/C2 组件，覆盖任务传感器、指挥/数据链、任务处理、电源生成/分配、推进/传动、燃油、飞控作动器和结构翼梁等关键件，并为这些代表性组件补齐同一组工程化机制阈值。测试证明 fuel cell 命中只触发 fuel/fuel leak，engine fuel feed/control 命中可额外降低 propulsion，aileron/elevon actuator 命中只触发 flight_control/hydraulic，新增 fighter nose/avionics/engine 与 20+ 组件覆盖能在 runtime `EffectsEvent` 中报告主组件身份并产生对应 overlay 后果，组件级 `mechanism_thresholds` 会改变同一组件的 component-threshold scale 与合成失效概率，且 UAV/直升机/C2 的主组件身份、冗余组成员数、组件完整性与 overlay 后果可由运行时事件追溯。
- critical/redundancy 已进入最小失效概率语义：同几何和弹头下，非关键、具冗余组的 actuator 会降低 component-failure probability；本轮进一步新增 `ComponentDamageState` 运行时记忆，把组件完整性、命名冗余组、组成员数、组失效数和组可用性作为状态保存，并让 F-16 / Su-35S 的 wing fuel cell、aileron/elevon actuator、wing spar 样例以及 MQ-9/MH-60R/E-3 的代表性组件从裸数字 `redundancy_group` 升级到命名 `redundancy_group_id`。连续命中同一作动器会累计降低该组件完整性，同时冗余组可用性仍保留另一侧成员贡献；这是最小冗余依赖图入口，不是完整液压/飞控/电源依赖网络。
- 新增首个组件依赖传播脚手架：组件可声明 `dependencies`，loader 和 factory 会初始化依赖系统，effects model 在组件完整性/冗余组可用性下降时把影响传播到依赖系统与 aircraft overlay。当前数据覆盖 F-16/Su-35/MQ-9/MH-60R/E-3 的飞控作动器到 `hydraulic` / `flight_control`，UAV/直升机传感器与 E-3 rotodome radar 到 `avionics` / `mission_systems` / `data_link`，以及当前 aircraft units 库代表性电源/数据链组件到 `flight_control` / `data_link` / `mission_systems` / `avionics` 的最小依赖；测试证明飞控组件命中会拖累 hydraulic/flight-control/axis overlay，E-3 radar 组件命中会拖累 avionics overlay，电源/数据链组件命中会拖累对应航电、飞控或任务相关 overlay。本轮进一步让 `delay_s>0` 的 typed dependency 先进入运行时 pending queue，并由 `AircraftDamageStateUpdate` 在后续帧到期后投射到系统/overlay/platform，`delay_s==0` 保持立即传播；`electrical_power`、`data_path`、`crew_operated`、`cooling`、`control_signal` 和 `structural_support` 也开始有最小 edge-specific routing，分别投射到电源/航电/任务、数据链/指挥导航、机组操作、冷却失效、控制信号和结构支撑后果线，并以回归固定不误降 fuel/propulsion/hydraulic 等无关轴。该机制仍不是完整液压、电源、数据链和飞控网络，也不是真实依赖延迟求解器。
- `EffectsEvent` 进一步暴露 `direct_hitbox_intersection`、`projected_hitbox_count`、`spatial_effect_scale`、`mechanism_armor_scale`、`mechanism_exposure_scale`、`mechanism_effect_scale`、`mechanism_surface_incidence_cos`、`warhead_spatial_sample_count`、`warhead_spatial_hit_estimate`、`warhead_spatial_hit_fraction`、`warhead_spatial_energy_scale`、`warhead_spatial_pattern_scale`、`warhead_orientation_axis_forward/right/up`、`warhead_orientation_pattern_scale`、`component_threshold_scale`、`component_failure_probability`、`component_failure_probability_source`、`component_failure_probability_calibrated`、`component_failure_probability_evidence_dataset_ref`、`component_failure_sample`、`component_failure_count`、`component_hit_count`、`component_mechanism_load_rows`、`component_primary_name`、`component_primary_system`、`component_primary_redundancy_group`、`component_primary_critical`、`component_primary_redundancy_group_id`、`component_primary_integrity`、`component_primary_mechanism_fragment_energy_j`、`component_primary_mechanism_fragment_areal_density_per_m2`、`component_primary_mechanism_penetration_margin`、`component_primary_mechanism_blast_overpressure_kpa`、`component_primary_mechanism_blast_impulse_kpa_ms`、`component_primary_mechanism_blast_scaled_distance_m_kg13`、`component_primary_mechanism_rod_cut_margin`、`component_primary_mechanism_surface_incidence_cos`、`component_redundancy_group_availability`、`component_redundancy_group_member_count`、`component_redundancy_group_failed_count`、`detonation_heading_deg`、`detonation_pitch_deg`、`detonation_roll_deg`、`fuze_type`、`fuze_trigger_radius_m`、`fuze_delay_s`、`fuze_reliability`、`fuze_signature_source`、`fuze_target_signature`、`fuze_signature_scale`、`fuze_effective_reliability`、`fuze_contact_surface_distance_m`、`fuze_contact_penetration_depth_m`、`fuze_contact_surface_tolerance_m`、`fuze_contact_inside_hitbox` 与 `fuze_profile_synthetic`，使一次杀伤结果可以从几何、引爆姿态、引信、弹头族、目标结构、空间采样、机制采样、候选组件机制载荷、入射角代理、组件失效概率来源/采样结果/authority 状态及其 weapon/aspect/closure/miss-distance 匹配轴、组件身份、组件状态记忆和冗余组可用性证据回溯，而不是只依赖日志。

仍未完成：真实破片云/连续杆空间采样、由战斗部姿态/引爆姿态驱动的校准方向性毁伤效应、雷达/激光近炸引信的校准 RCS/反射触发条件、接触引信穿入/延迟/失效模式的校准模型、定时引信校准/漂移/战术设定来源、引信失效模式校准、未来新增飞机的 20-50 项组件级数据、校准组件级失效概率、完整冗余系统依赖图、按目标脆弱性证据校准的 blast/fragment/rod/HTK 参数、目标脆弱性/Pk 校准。当前 Phase 3 只关闭“profile 数据面可见、能影响结构化空中目标 effects 分配、近炸点能按弹头族 footprint 与距离衰减投射到受影响 hitbox，blast/fragmentation 类宽域近炸不会因组件候选而丢失相邻区域覆盖，破片/连续杆类近炸具备参数化空间采样证据，破片载荷能暴露并按 row gate 消费 areal-density 证据，blast 类载荷能暴露并按 row gate 消费 scaled-distance 证据，surface-incidence cos 能进入机制载荷事件面并按 row gate 消费，连续杆类近炸能受导弹速度轴和引爆姿态轴方向影响，live missile 的引爆姿态可进入事件审计面并派生 orientation-pattern 证据，contact/impact/timed fuze 至少开始改变触发条件，contact/impact live event 能审计表面距离与穿入深度，radar/laser proximity fuze 开始消费目标签名代理并记录事件审计，组件级几何入口可被 effects model 消费，当前 aircraft units 库 F-16/Su-35/MQ-9/MH-60R/E-3 均达到 20+ 代表组件且 runtime 可追溯，代表性 fighter/UAV/直升机/C2 组件可以声明并消费按弹头族区分的工程化机制阈值，组件完整性和命名冗余组可用性可在运行时累计并审计，首个组件依赖可传播到相关系统/overlay，且 fuze/armor/exposure/mechanism/surface-incidence/component-threshold/component-identity/component-failure 证据可审计”的最小门。新增 `EffectsEvent` 几何、引爆姿态、引信、空间采样、orientation-pattern、surface-incidence 和机制字段只是后续引信/Pk/姿态效应校准的可审计输入；由于当前 proximity fuze 仍以最近点后一帧作为触发判定，`closure_mps` 可合法为 0，不能据此放行确定性引信。warhead spatial sampling、fragment areal-density proxy、blast scaled-distance proxy、surface-incidence proxy、detonation-attitude orientation evidence、fuze reliability/signature proxy、contact penetration evidence、armor/exposure/component-threshold/component-identity/component-failure 采样、组件 `mechanism_thresholds` 和 component dependencies 仍是工程化脚手架，不等价于已校准破片云、Sachs 爆轰传播、连续杆切割、方向性战斗部效应、引信性能、组件失效概率、完整冗余依赖图或命中概率权威。

### Phase 4：确定性引信，暂缓

目标是把当前 RNG hit probability 替换为 geometry-first fuze/effects 模型。但它必须等待 PN miss-distance benchmark。否则可能把当前唯一的 evasion 影响点移除，导致高机动目标和低机动目标在杀伤结果上过于确定。

### Phase 5：脆弱性 / Pk 证据集成

状态：`synthetic_evidence_scaffold_started / calibrated_gate_added`。

目标是引入 weapon/target/aspect/closure/miss-distance 相关的证据表或函数。Pk 曲线只能校准物理模型，不能替代 `EffectsEvent`、`DamageReport` 和平台状态。

当前窄域收口任务定义见：

- [A2 窄域 Authority 闭环任务定义 - AIM-120C-class blast-fragmentation -> F-16C Block 50](narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md)

当前最小闭环：

- 新增 `AircraftVulnerabilityProfile` runtime component，字段覆盖弹头族 scale、nose/beam/tail aspect scale、high/low closure scale、near-miss/direct-hit scale、`synthetic`、`provenance` 与 calibration authority gate；
- `damage_model.vulnerability` 可从 aircraft JSON 进入 `UnitDefinition`、spawn 到 entity，并作为 survivability capability evidence 暴露；
- F-16 先接入一份 `synthetic=true` 的 vulnerability scaffold，provenance 明确标注为 A2-P5 synthetic scaffold，不能用于 deterministic fuze/Pk 声称；
- Su-35、MQ-9、MH-60R、E-3 已补 neutral synthetic target-family vulnerability scaffold，默认 scale 保持 1.0，仅证明 fighter/UAV/直升机/C2 目标族的运行时 evidence gate 覆盖面，不改变未校准毁伤强度；
- `default_effects_model` 在 structured aircraft path 中消费该 profile：它调制 physical effects severity，而不是替代 hitbox、warhead profile、miss-distance 和 platform damage state；
- 新增 diagnostics-only `debug_apply_profiled_local_proximity_hit_with_velocity`，用于固定 warhead/local hit point 并显式设置合成导弹速度，从而回归 aspect/closure 对 vulnerability 调制的影响。
- 新增 evidence gate 字段：`calibrated`、`evidence_dataset_ref`、`calibration_status`、`evidence_dataset_valid`、`pk_authority`、`deterministic_fuze_authority`；profile 自声明不再足以进入权威语义；
- loader 会在数据库加载时读取 `damage/vulnerability_evidence/*.json` descriptor；只有 profile 满足 `synthetic=false + calibrated=true + calibration_status=calibrated`，且 `evidence_dataset_ref` 指向已加载、target 匹配、descriptor 自身 `calibration_status=calibrated`，声明当前 `schema_version`、非空 `source_ref` / `provenance`、`weapon_family`、`aspect_bucket`、`closure_bucket`、`miss_distance_bucket` 证据轴，并且 descriptor 来源为 `external_calibration_dataset` 或带可审计 `validation_manifest` 的 `validated_physics_surrogate` 时，`evidence_dataset_valid` 才为真；`validation_artifact_ref` 不再单独构成 surrogate 授权条件；
- `pk_authority` 必须由该 descriptor 授予；`deterministic_fuze_authority` 继续 deferred，当前 vulnerability descriptor 不放行确定性引信。缺失 descriptor、synthetic placeholder descriptor、target/status/证据轴不匹配或未授权的能力都会被强制关闭；
- descriptor 可声明 `effect_scale_authority` / `component_failure_probability_authority` 并携带 `rows[]` 校准数据行；只有 gate 已通过且 descriptor 明确授予相应 authority 时，`default_effects_model` 才会按 weapon family / aspect / closure / miss-distance 匹配数据行，并分别用行内 family/aspect/closure/miss-distance/effect scale 或 component-failure probability 驱动 vulnerability 调制与组件失效概率；component-specific rows 可进一步声明 `component_name` / `component_system` / `component_redundancy_group_id`，并优先于全局概率行；rows 可声明 `min_*/max_*` 机制载荷门槛（破片能量、破片面密度、穿透裕度、爆轰超压/冲量、blast scaled distance、连续杆切割裕度、surface-incidence cos），使授权 effect-scale row 与 component-failure row 都只有在当前事件/候选组件的实际 mechanism-load vector 落入对应区间时才会被消费；授权 rows 必须声明 `row_id` / `source_ref` / `provenance`，缺少这些元数据的 rows 不会进入运行时 evidence row 集合；descriptor 的 `schema_version`、`source_kind`、`source_ref`、`validation_artifact_ref` 与 surrogate validation manifest 元数据会随 profile 进入运行时，并在 `EffectsEvent.vulnerability_evidence_*` 暴露；被消费的 effect-scale row 元数据会进入顶层 `EffectsEvent.vulnerability_effect_scale_*`，被消费的 component-failure row 元数据会进入顶层 `EffectsEvent.component_failure_probability_*` 和对应 `ComponentMechanismLoadRow`，用于从事件反查具体校准数据行；
- factory capability bundle 区分 `aircraft_vulnerability_synthetic_profile` 与 `aircraft_vulnerability_calibrated_profile`，避免把工程 scaffold 当作校准证据；
- 新增 diagnostics-only `debug_get_aircraft_vulnerability_evidence_state`，暴露 `[present, synthetic, calibrated_evidence, pk_authority, deterministic_fuze_authority, evidence_dataset_valid]`，用于测试和审计 evidence gate。
- 新增 diagnostics-only `debug_get_aircraft_vulnerability_authority_state`，暴露 `[present, synthetic, calibrated_evidence, effect_scale_authority, component_failure_probability_authority, pk_authority, deterministic_fuze_authority, evidence_dataset_valid]`，用于把“row-backed authority 是否已放行”与 `Pk` / `deterministic_fuze` gate 分开审计。
- 新增只读 vulnerability evidence descriptor fixtures：`examples/config/database/damage/vulnerability_evidence/a2_synthetic_f16_aim120_placeholder.json` 固定 placeholder 形状，`examples/config/database/damage/vulnerability_evidence/a2_vulnerability_evidence_schema_fixture.json` 固定 `a2.vulnerability_evidence.v1` row 形状、机制载荷区间字段和 component-specific 字段；二者都保持 authority=false，不参与 damage 计算，也不授予 Pk 或 deterministic fuze authority。
- 新增 runtime 回归 `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_scaffold.py`：即使 aircraft JSON 伪造 `calibrated=true` 并指向 `a2_blastfrag_validation_scaffold.py` 生成的 schema-aligned non-authoritative draft，运行时也只允许该 descriptor 元数据进入 `EffectsEvent.vulnerability_evidence_*` 审计面，不会把 `engineering_surrogate + unvalidated + authority=false` 草案误提升为 row-backed authority。
- `EffectsEvent` 现在同步暴露 vulnerability 审计字段：profile 是否存在、是否 synthetic、calibrated evidence / Pk / deterministic-fuze authority、descriptor valid/ref、descriptor schema/source/validation artifact、surrogate validation manifest metadata、calibration status、provenance、aspect bucket、family/aspect/closure/miss-distance/effect scale，以及 effects model 实际使用的径向 `vulnerability_closure_mps`。这些字段用于把脆弱性调制从日志提升到事件证据面，不构成 Pk 或确定性引信权威。

新增回归用临时数据库证明：伪造 `calibrated=true` 的 aircraft JSON 在缺少 descriptor 时不会获得权威，synthetic placeholder descriptor 即使被改成请求 authority 也不会放行，缺失 evidence axes、当前 schema 版本或 source ref 的 descriptor 不会放行，未知/工程化 source kind 或缺少验证 manifest 的 physics surrogate 不会放行，只有测试 fixture 中非 synthetic 且校准状态、target、weapon/aspect/closure/miss-distance 证据轴齐备，并来自允许 source kind 且具备 schema/source/provenance 的 descriptor 才能按字段授予 Pk；deterministic-fuze authority 仍固定不由 vulnerability descriptor 放行。新增 target-family scaffold 回归证明 F-16/Su-35/MQ-9/MH-60R/E-3 的 synthetic vulnerability profile 均会进入运行时，但 evidence state 仍固定为 non-authoritative。新增 rows fixture 进一步证明：descriptor 授予 `effect_scale_authority` 时，匹配数据行会驱动事件中的 vulnerability scale，并在 `EffectsEvent` 标记 `vulnerability_effect_scale_source=vulnerability_evidence_row` 与对应 row id/source/provenance；带机制载荷门槛的 effect-scale row 会按实际载荷过滤，不能仅凭 weapon/aspect/closure/miss-distance 粗桶覆盖；fragment areal-density、blast scaled-distance 与 surface-incidence cos 都可作为 effect-scale row 的适用门槛。descriptor 授予 `component_failure_probability_authority` 时，匹配数据行会覆盖组件失效概率，并在 `EffectsEvent` 标记 `component_failure_probability_source=vulnerability_evidence_row`、`component_failure_probability_calibrated=true` 与对应 dataset ref；component-specific probability row 会优先于同一 descriptor 内的全局 row，并在 `ComponentMechanismLoadRow` 暴露 evidence component name/system/redundancy-group provenance；component-failure probability row 的机制载荷门槛会按当前候选组件实际 `fragment_energy_j / fragment_areal_density_per_m2 / penetration_margin / blast_overpressure_kpa / blast_impulse_kpa_ms / rod_cut_margin / surface_incidence_cos` 过滤，不满足门槛的高概率 row 不会被误消费，同一 descriptor 内可用低/高载荷 bucket 区分概率；被消费的 row id/source/provenance 会随顶层事件和组件候选行一起导出，避免后续校准审计只能由概率值反推数据来源；缺少 row id/source/provenance 的 rows 即使处于已授权 descriptor 中也不会被消费；descriptor 未授予对应 authority 时，即便 rows 存在也不会被消费，事件仍标记为 `profile_scale` 或 `synthetic_sigmoid`。所有 fixture 只证明门控和数据通路机制，不构成项目真实校准数据。

仍未完成：外部或校准来源的 target/weapon vulnerability 表、按目标类别扩展的 calibrated evidence dataset、正式 Pk/kill-chain 校准和 deterministic fuze 放行证据。当前只是让脆弱性证据行和组件级条件失效概率具备受控接入和事件审计路径，并防止 aircraft JSON 自声明、synthetic scaffold、synthetic descriptor 或未授权 rows 被误提升为 Pk/引信权威。

### Reward / score 消费层

状态：`structured_air_effects_guarded / consumer_migration_started`。

当前 structured aircraft effects path 已有两类证据：

- 行为回归：`test_structured_air_damage_does_not_write_rl_score_from_physical_effects` 固定结构化毁伤会产生 `DamageReport.system_health_delta < 0`，但 attacker `AgentObservation.total_reward` 不变；
- 静态守卫：`test_a2_structured_air_effects_do_not_write_rl_score_authority` 固定 `default_effects_model` 的 structured-air 分支不能写 `score->...`，legacy HP path 的历史 score 写入仍被隔离在 `if (hp && !structured_air_target)` 内。

本轮已启动 consumer 迁移：

- 新增空战消费层 helper，默认只在 `air_combat` 场景或显式开关下启用；
- 1v1 terminal override 不再只看 `sim.is_unit_active(target)`，会将近期 `DamageReport.loss_state_to`、`destroyed`、`mission_kill`、`mobility_kill`、`sensor_kill` 解释为战斗可行动性；
- conditional objective 的 `target_active` / `target_health` 兼容字段在目标被 `DamageReport` 判定为 neutralized 时派生为 inactive / 0，避免旧条件目标继续把 HP 当权威；
- `apply_air_combat_reward_surface` 会读取未消费过的近期 `DamageReport`，用 `system_health_delta` 与 `platform_damage_state_delta` 派生目标毁伤进展、自身受损惩罚和 loss-state progression 奖惩；它只消费事件事实，不写回 physical effects authority；
- 新增 `test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win`：目标实体仍 active、HP 不变，但 `DamageReport.loss_state_to == mobility_kill` 时，1v1 运行层给出 `combat_win`；
- 新增 `test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once`：非终局结构毁伤可产生训练 shaping，同一 report 不会被重复计分。

仍未完成：当前连续 shaping 还是最小消费层，尚未覆盖全量 subsystem capability 曲线、课程级统计和 Pk/evidence 校准；它不能反向定义物理毁伤权威，也不能作为 deterministic fuze 放行依据。

阶段零固定动作注意事项：当前 fixed-fire smoke 能验证发射链路，但仍受 Phase 4 尚未放行的 RNG fuze 影响。一次真实导弹最近距离进入 fuse radius 后仍可能随机未命中，因此 smoke 不应断言“单发必然 combat_win”；确定性引信仍必须等待 warhead/fuze/vulnerability calibration。

## 非目标

- 不为了短训练 reward 简化物理杀伤；
- 不用单一 `damage` scalar 冒充高真实度战斗部；
- 不把 `health <= 0` 继续作为带结构化毁伤状态飞机的权威 kill 判据；
- 不在缺少 PN miss-distance 证据前移除 RNG fuze；
- 不在 Phase 0 前改动 `PlatformLossState` 枚举值。

## 主要写入面

- `src/models/weapons/default_effects_model.cpp`
- `src/systems/combat/damage_system.h`
- `src/components/combat/damage.h`
- `src/content/unit_definition.h`
- `src/content/unit_definition_loader.cpp`
- `examples/config/database/aircraft/**/*.json`
- `examples/config/database/weapons/air_to_air/**/*.json`
- `src/runtime/contracts/engagement_contracts.h`
- RL / runtime consumers that currently read `health` or direct score writes

## 验收信号

最低验收不以“训练更容易”为标准，而以物理语义为标准：

- structured aircraft target 不能被 HP-first bypass 击杀；
- missile event 至少产生可检查的 `EffectsEvent` / `DamageReport` / subsystem mutation；
- `EffectsEvent` 至少暴露可检查的 miss distance、局部起爆点、闭合速度和导弹速度轴几何证据；
- `EffectsEvent` 至少暴露可检查的 direct/projection 命中形态、空间效应尺度、装甲耦合尺度、投影暴露尺度、机制效应尺度，以及未校准的破片能量、破片面密度、穿透裕度、爆轰超压/冲量、blast scaled distance、连续杆切割裕度、surface-incidence cos 等机制载荷证据；
- `EffectsEvent` 至少暴露 component-threshold 尺度，证明同一弹头事件没有把所有受保护系统当作同一通用标量；
- `EffectsEvent` 至少暴露 component-failure probability/source/calibrated/dataset/row-id/source-ref/provenance/sample/count，证明组件级概率采样会消费未校准机制载荷证据，且授权 row 覆盖仍能在事件面审计；vulnerability evidence rows 若声明机制载荷门槛，必须按当前组件实际 mechanism-load vector 过滤，不能只靠 weapon/aspect/closure/miss-distance 粗桶覆盖概率；surface-incidence gate 只能筛选适用 row，不能独立授予 kill/Pk/deterministic fuze/calibrated lethality authority；测试 fixture 不构成正式 Pk 权威；
- `EffectsEvent` 至少暴露 component hit count、candidate component mechanism-load rows 和 primary component identity，证明组件级几何与载荷选择不是只在日志中存在；每个 row 还会携带 component-failure probability/source/calibrated/dataset/sample，证明 row 级 provenance 可以随组件候选一起被审计。
- `EffectsEvent` 至少暴露 vulnerability profile/evidence/authority/provenance/aspect/closure/scale/source/evidence-row 字段，证明脆弱性调制可以在事件面审计，并能区分 profile-scale 与 authorized row-scale；synthetic profile、synthetic descriptor 或缺少 row provenance metadata 的 rows 仍不能获得 Pk 或 deterministic-fuze authority；
- `EffectsEvent` 至少暴露 contact/impact fuze 的表面距离、穿入深度、接触容差和 inside-hitbox 布尔值，证明接触引信不是由近炸半径替代；该字段仍是几何审计脚手架，不是校准接触引信穿入/延迟/失效模型；
- `EffectsEvent` 至少暴露 live missile 引信 armed 时冻结的 `detonation_heading_deg`、`detonation_pitch_deg`、`detonation_roll_deg`，以及由该姿态派生的 `warhead_orientation_axis_forward/right/up` 与 `warhead_orientation_pattern_scale`，证明战斗部/引爆姿态可进入参数化方向证据；这些字段仍不是校准方向性破片云或连续杆效应模型；
- F-16/Su-35 数据库级 20+ 代表组件样例能区分 wing fuel cell、aileron/elevon actuator、nose radar、mission computer、engine core、navigation/power、thrust-vector/leading-edge actuator 等命中后果，并能体现 per-component `mechanism_thresholds`、critical/redundancy 对失效概率的最小调制；
- MQ-9、MH-60R、E-3 的代表性组件样例能在运行时事件中报告主组件身份、冗余组成员数、组件完整性、per-component `mechanism_thresholds` 和对应 overlay 后果，证明组件化数据模式覆盖 fighter 以外的 UAV/直升机/C2 平台；
- 组件 `dependencies` 至少能把飞控作动器影响传播到液压/飞控 overlay，并把 E-3 mission radar 影响传播到航电/任务系统 overlay；`delay_s>0` 的 dependency 至少能先排队、后到期传播；该字段仍是最小依赖脚手架，不是完整依赖网络；
- typed dependency edge 至少能区分 `electrical_power`、`data_path`、`crew_operated` 和 `cooling` 的主要后果线，并证明 data-path 不误降 hydraulic/fuel/propulsion、crew-operated 不误降 hydraulic/fuel；
- lateral fuel storage 命中至少能报告 `fuel_imbalance_severity` 并在后续帧轻微投射到 control asymmetry / roll authority；中心机身 fuel cell 与 engine fuel feed 不应误触发该左右不平衡语义；
- engine/wing/fuselage/mission fire-zone 命中至少能写入对应 zone severity，并在后续帧产生不同二次损伤方向；该字段仍是工程化 compartment scaffold，不是 fire-zone/热释放/通风/烟雾权威；
- hydraulic source 命中至少能写入 `hydraulic_pressure_availability`，并在后续帧把压力不足投射到 flight-control/turn-rate；该字段仍是 pressure/capacity 工程代理，不是真实液压回路或压力曲线；
- 不同 hitbox 命中能产生不同能力后果；
- HP 只作为派生兼容读数存在；
- reward/score 消费毁伤报告和 kill state，不写回 physical effects authority；
- legacy smoke 可以通过兼容读数继续运行，但测试明确区分 legacy HP path 与 structured damage path。

## 推荐验证

Phase 0：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py \
  tests/runtime/engagement \
  tests/world_batch/test_world_batch_runtime.py
```

架构边界：

```bash
bash -lc 'source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json'
```

Phase 1 后必须新增专用测试，至少覆盖：

- structured aircraft hitbox 命中；
- HP-first bypass 被禁止；
- aircraft damage update 不依赖 `ShipPlatform`；
- `DamageReport` loss state 和派生 `Health` 一致。

当前聚焦验证：

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py::AirCombat1v1FireMissileTests::test_fired_missile_does_not_retarget_friendly_and_records_engagement \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_target_uses_damage_state_instead_of_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_damage_does_not_write_rl_score_from_physical_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aileron_component_damage_derives_roll_axis_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_avionics_and_crew_damage_derives_sensor_performance \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_damaged_airframe_high_speed_envelope_accumulates_structural_damage \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_e3_sentry_c2node_uses_authored_structured_damage_model \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_aircraft_database_units_have_authored_structured_damage_models \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_definition_missile_tuning_flows_into_launch_runtime \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_global_warhead_profile_override_flows_into_runtime_and_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_family_changes_structured_air_effect_distribution \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_proximity_field_projects_near_miss_onto_nearest_air_hitbox \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_spatial_projection_respects_warhead_family_footprint \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_continuous_rod_near_miss_uses_relative_velocity_axis \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_surface_incidence_cos_reports_obliquity_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_database_f16_component_geometry_reports_primary_component \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_database_su35_component_geometry_reports_primary_component \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_representative_aircraft_database_components_cover_uav_helo_c2 \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_representative_aircraft_components_report_runtime_identity \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_dependencies_are_authored_for_representative_control_and_mission_components \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_mission_component_dependency_damage_propagates_to_avionics_overlay \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_redundancy_reduces_failure_probability \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_aircraft_vulnerability_profile_modulates_structured_damage \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_vulnerability_adjustment_is_recorded_on_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_vulnerability_claim_requires_dataset_descriptor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_descriptor_cannot_grant_vulnerability_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_grants_only_requested_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_requires_evidence_axes \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_validated_physics_surrogate_requires_auditable_manifest \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_validated_physics_surrogate_exports_manifest_metadata \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_can_grant_pk_but_deterministic_fuze_remains_deferred \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_vulnerability_rows_drive_effects_event_scales \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_vulnerability_rows_require_effect_scale_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_effect_scale_rows_can_use_surface_incidence_gate \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_rows_drive_component_failure_probability \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_require_probability_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_can_use_surface_incidence_gate \
  tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries
```

结果：`cmake --build build-workshop --target ef_py -j4` 已通过；空战 guard、evidence descriptor、engagement contract、launch adapter 与 binding 聚焦子集已通过，`135 passed, 96 subtests passed`；`git diff --check` 已通过。

## 外部评审

- [高保真要求独立评审](review_high_fidelity_requirements_20260526.zh.md) — 从空战杀伤建模领域要求出发，定义高保真的实质标准，独立于项目自身文档。

## 后续入口

- [任务簇](high_fidelity_damage_model_cluster_20260526.zh.md)
- [A2 数据收集入口](data_collection/README.zh.md)
- [surface-incidence evidence/row gate 进展记录 - 2026-05-28](surface_incidence_evidence_gate_20260528.zh.md)
