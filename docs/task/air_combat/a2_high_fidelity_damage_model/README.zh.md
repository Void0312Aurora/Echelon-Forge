# A2 高真实度空战毁伤模型

状态：`2026-05-26` Phase 0 已接受；Phase 1 最小补丁已开始并通过聚焦测试；Phase 2 已从 generated fallback 推进到首批 authored aircraft hitbox 覆盖，并新增飞机专用 `AircraftDamageState` overlay、overlay-driven 飞行动力学/推进/传感器派生、受损结构在高动压/高速包线下继续劣化的最小闭环，以及火灾/燃油泄漏/液压损伤的最小时间级联；Phase 3 已从最小 `WarheadProfile` 数据通路推进到首个弹头族 effects 分配补丁、按弹头族 footprint 的近炸空间投射闭环、最小 relative-velocity-axis 空间方向耦合、hitbox armor / projected exposure / warhead mechanism 的可审计采样脚手架、机制特定组件阈值、首个合成组件失效概率采样增量、显式 `FuzeProfile` 证据面、proximity fuze delay 的最小延迟爆轰调度、首个 fuze type trigger semantics 行为分支，以及首个组件级几何入口；Phase 5 已启动 synthetic vulnerability evidence scaffold，并补入 calibrated evidence gate。当前闭合了 PN miss-distance baseline、HP-first bypass 反转、live missile `EffectsEvent/DamageReport` 记录、structured-air physical effects 不直接写 RL `Score` 的行为/静态守卫、aircraft damage-state 同步、nose/fuselage/wing 命中后果分化、F-16/Su-35/MQ-9/MH-60R/E-3 结构化 authored hitbox 回归，air-specific structure/flight-control/hydraulic/propulsion/fuel/avionics/crew overlay 回归，overlay 下推 FlightModel/Propulsion/fuel leak 的动态约束回归，燃油泄漏真实消耗 `FuelSystem` / `Mass` 燃油质量回归，火灾/液压/燃油级联持续影响结构、航电、机组、飞控和平台能力回归，航电/机组损伤下推传感器 range/Pd/noise/track-memory 回归，受损机体 high-energy flutter/overstress 暴露回归，warhead family/mass/lethal-radius/synthetic provenance 与 fuze type/trigger-radius/delay/reliability/synthetic provenance 进入 missile runtime、`EffectsEvent`，diagnostics-only 局部命中 effects 差异测试、距离衰减近炸场投射测试、弹头族 footprint 覆盖测试、continuous-rod velocity-axis 近炸方向性测试、armor/exposure 机制采样测试、component-threshold 机制敏感度测试、component-failure probability 采样测试、fuze profile runtime/event 测试、fuze delay detonation-time 回归、contact fuze 不把 near-miss radius 误当作接触触发的回归、timed fuze 不依赖近炸门而按发射后延时独立起爆的回归，以及组件化 wing hitbox 内 fuel cell / flight-control actuator 局部命中分化回归，`EffectsEvent` 已补 miss distance、目标机体系起爆点、闭合速度、导弹速度轴、direct/projection 命中形态、空间效应尺度、装甲耦合尺度、投影暴露尺度、机制效应尺度、组件阈值尺度、组件失效概率、失效采样值、失效触发次数、引信类型、触发半径、延迟、可靠性和 synthetic 标记等证据字段，且 `detonation_time_s` 能按 `fuze_delay_s` 晚于 `nearest_approach_time_s`；F-16 synthetic vulnerability profile 对弹头族/aspect/closure/near-miss 的 structured damage 调制测试、synthetic vulnerability 不具备 Pk/确定性引信权威的 evidence-gate 回归，以及空战 reward surface 对非终局 `DamageReport` 连续毁伤信号的一次性消费回归。

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
- F-16、Su-35、MQ-9、MH-60R 已补 authored structured hitbox，覆盖座舱/传感器、机身燃油/航电/数据链、推进、机翼/旋翼/飞控等首批关键区域；
- 新增测试证明上述三类后果不会退化为同一种 damage scalar。
- 新增 `AircraftDamageState` 作为飞机专用 overlay，记录 `structural_integrity`、`flight_control_integrity`、`hydraulic_integrity`、`propulsion_integrity`、`fuel_system_integrity`、`avionics_integrity`、`crew_effectiveness`、`fire_severity`、`fuel_leak_severity` 与 forced-landing / subsystem-kill 标志；
- effects model 会把 authored hitbox 命中映射到 air-specific overlay，再由 overlay 下推到兼容层 `PlatformDamageState`，避免后续飞机毁伤继续挤在舰船语义字段里；
- 新增 diagnostics-only `debug_get_aircraft_damage_state`，用于回归验证不同 hitbox 对飞机专用子系统的影响。
- 新增 `AircraftDamageBaseline`，保留飞机初始 FlightModel/Propulsion/fuel-leak 基线；`AircraftDamageStateUpdate` 每帧从 overlay 派生 `max_turn_rate`、`max_accel`、`max_climb_rate`、`max_g`、`max_speed`、推力和燃油泄漏，而不是在命中瞬间一次性手改动力学字段；
- 拆分 propulsion 与 fuel：油箱命中会降低燃油系统并增加 fuel leak，但不再直接等价发动机/推进损伤；发动机/推进命中才降低 thrust baseline 派生值。
- 新增 `structural_overstress` 与 `flutter_exposure` 诊断记忆：结构已受损的 aircraft 会在高动压/高 Mach 包线中持续累积暴露，并缓慢降低 `structural_integrity`，随后通过既有 overlay 派生进一步收紧 `max_g` 等飞行动力学限制；
- 该闭环显式避免把普通受损巡航或低速失速误判为 flutter：受损结构是前置条件，失速贡献还需要 high-energy gate，因此它是 Phase 2 的最小高能包线退化模型，不是完整结构疲劳/颤振求解器。
- 新增传感器基线派生：`AircraftDamageBaseline` 记录初始 `Sensor` range、Pd、噪声和 track memory；`AircraftDamageStateUpdate` 每帧按 `avionics_integrity` 与 `crew_effectiveness` 派生传感器能力，使 cockpit/avionics 命中会降低 BVR 感知能力，而 wing/flight-control 命中不会误降传感器。
- 新增最小损伤级联：`AircraftDamageStateUpdate` 每帧从 fuel leak severity 扣减 `FuelSystem` 内/外挂油并同步 `Mass` 燃油质量；火灾会按燃油、液压、航电损伤和泄漏活动持续升高并传播到结构、航电、机组、液压和燃油系统；液压损伤会继续拖累飞控并增加结构过载暴露；这些级联也会下推平台 mission/sensor/mobility/survivability 能力。

仍未完成：更细的飞控/液压控制律耦合、离散控制面失效、完整火灾传播/抑制/烧穿时间线、冗余系统依赖图、flutter 边界、座舱/飞行员更细粒度后果、战斗部空间效应模型、确定性引信和脆弱性/Pk 校准。当前 authored hitbox、overlay 与级联是工程化结构化内容，不应宣称为全高保真 vulnerability evidence。

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
- `EffectsEvent` 同步暴露 `miss_distance_m`、目标机体系 `detonation_local_forward/right/up_m`、`closure_mps` 和 `missile_axis_forward/right/up`，用于审计近炸几何、局部起爆点和弹头 footprint 方向性；
- live proximity fuze 的 `effect_family` 不再硬编码为固定字符串，而是来自 missile warhead profile；
- AIM-120C、AIM-9X、R-77-1 现有 JSON 在缺少显式 `damage` 时会以 warhead mass 生成 synthetic damage scalar，并在 diagnostics 中标记。
- `default_effects_model` 对 structured aircraft 引入首个弹头族 effects 分配：blast 更偏结构/火灾/破口，blast-fragmentation 保持平衡基线，continuous rod 更偏机翼/飞控/结构切割类后果，hit-to-kill 更偏局部系统杀伤且低火灾扩散；
- 新增 diagnostics-only `debug_apply_profiled_local_proximity_hit`，用于在固定目标机体系命中点下对比不同 `WarheadProfile`，避免把弹头族 effects 测试绑定到导弹飞行几何随机性。
- 新增近炸空间投射最小闭环：structured aircraft 若没有直接 hitbox 交点，会在战斗部 lethal radius 的保守局部范围内寻找受影响 hitbox，并按弹头族设定投射半径、衰减曲线和最大影响 hitbox 数；blast/fragmentation 可形成多区域覆盖，continuous rod 较窄，hit-to-kill 保持强局部化；远离机体的 near miss 仍保持无结构化毁伤。
- 近炸投射已改为按系统类别保留局部场强：同一近炸事件可以覆盖多个区域，但某个弱覆盖系统不会把最近 hitbox 的强场错误套用到所有子系统，因此近炸侧掠仍弱于直接命中对应关键 hitbox。
- 新增最小 relative-velocity-axis 空间方向耦合：无直接 hitbox 交点的近炸投射会把导弹速度轴转入目标机体系，并按候选 hitbox 相对该轴的径向/轴向关系调制 footprint；continuous rod 对横向扫掠机翼/飞控更敏感，hit-to-kill 更偏轴向局部，blast/fragmentation 只做较弱方向修正。
- 新增首个 warhead mechanism sampling scaffold：直接命中和近炸投射都会消费 authored hitbox 的 `armor_mm`、局部投影暴露面积、弹头族机制容量、距离质量和 velocity-axis 权重；低装甲/高暴露 hitbox 会得到更强机制尺度，高装甲/低暴露 hitbox 会削弱 effects severity。
- 新增首个 component-threshold scaffold：同一 hitbox 内的 `flight_control`、`fuel`、`radar/avionics`、`engine`、`cockpit/crew` 和 `structure` 不再共享完全相同的系统扣减尺度，而是按弹头族机制使用不同敏感度；例如 continuous rod 对飞控/结构更敏感，blast 对燃油/结构更敏感，hit-to-kill 对局部传感器/座舱/发动机更敏感。
- 新增首个合成 component-failure probability scaffold：直接命中和近炸投射会按 system severity、mechanism scale、component threshold scale 和 direct/projection 形态生成概率，使用导弹 RNG 进行可重复采样；若采样触发，则给对应 aircraft overlay / platform damage 施加额外失效冲击。
- 新增显式 `FuzeProfile` 数据通路：weapon JSON、`MissileTuning`、运行时 `Missile` 和 `EffectsEvent` 记录 fuze `type`、`trigger_radius_m`、`delay_s`、`reliability`、`synthetic` 与 provenance；AIM-120C/R-77-1 先标为 radar proximity，AIM-9X 先标为 laser proximity。
- live proximity fuze 继续使用最近点后一帧触发判定和 RNG hit gate，但现在由 `FuzeProfile.trigger_radius_m` 决定触发半径，并用 `FuzeProfile.reliability` 调制既有命中概率；`delay_s` 会把 effects 结算调度到 `nearest_approach_time_s + delay_s`，使 `detonation_time_s` 与 `nearest_approach_time_s` 在事件中真实分离。
- 新增首个 fuze type trigger semantics 行为分支：`radar_proximity` / `laser_proximity` / `proximity` 仍按近炸触发半径工作；`contact` / `impact` 不再把近炸半径当作触发条件，而是要求导弹位置到目标 authored hitbox 表面进入很小的接触容差，避免“近失但未接触”被误记录为接触起爆；`timed` 按发射后 `delay_s` 独立调度起爆，即使未进入近炸门也会生成可审计的 timed-fuze event，后续是否造成毁伤仍由战斗部 footprint / hitbox 几何决定。
- 新增首个组件级几何入口：`damage_model.hitboxes[].components[]` 可声明 hitbox 内的组件名称、系统、局部 offset/size、armor、threshold scale 和冗余组占位；loader 会保留该数据，effects model 在直接命中和近炸投射中优先按组件局部几何/装甲/阈值采样，未命中组件时再回退到旧 hitbox-level `systems`。当前测试用组件化 wing hitbox 证明 fuel cell 命中只触发 fuel/fuel leak，而 aileron actuator 命中只触发 flight_control/hydraulic。
- `EffectsEvent` 进一步暴露 `direct_hitbox_intersection`、`projected_hitbox_count`、`spatial_effect_scale`、`mechanism_armor_scale`、`mechanism_exposure_scale`、`mechanism_effect_scale`、`component_threshold_scale`、`component_failure_probability`、`component_failure_sample`、`component_failure_count`、`fuze_type`、`fuze_trigger_radius_m`、`fuze_delay_s`、`fuze_reliability` 与 `fuze_profile_synthetic`，使一次杀伤结果可以从几何、引信、弹头族、目标结构、机制采样和组件失效采样证据回溯，而不是只依赖日志。

仍未完成：真实破片云/连续杆空间采样、显式战斗部姿态/引爆姿态、雷达/激光近炸引信的 RCS/反射触发条件、接触引信穿入深度、定时引信校准/漂移/战术设定来源、引信失效模式校准、全库 20-50 项组件级飞机数据、校准组件级失效概率、冗余系统依赖图、按目标脆弱性证据校准的 blast/fragment/rod/HTK 参数、目标脆弱性/Pk 校准。当前 Phase 3 只关闭“profile 数据面可见、能影响结构化空中目标 effects 分配、近炸点能按弹头族 footprint 与距离衰减投射到受影响 hitbox，连续杆类近炸能受导弹速度轴方向影响，contact/impact/timed fuze 至少开始改变触发条件，组件级几何入口可被 effects model 消费，且 fuze/armor/exposure/mechanism/component-threshold/component-failure 证据可审计”的最小门。新增 `EffectsEvent` 几何、引信和机制字段只是后续引信/Pk 校准的可审计输入；由于当前 proximity fuze 仍以最近点后一帧作为触发判定，`closure_mps` 可合法为 0，不能据此放行确定性引信。fuze reliability、armor/exposure/component-threshold/component-failure 采样也是工程化脚手架，不等价于已校准破片云、连续杆切割、引信性能、组件失效概率或命中概率权威。

### Phase 4：确定性引信，暂缓

目标是把当前 RNG hit probability 替换为 geometry-first fuze/effects 模型。但它必须等待 PN miss-distance benchmark。否则可能把当前唯一的 evasion 影响点移除，导致高机动目标和低机动目标在杀伤结果上过于确定。

### Phase 5：脆弱性 / Pk 证据集成

状态：`synthetic_evidence_scaffold_started / calibrated_gate_added`。

目标是引入 weapon/target/aspect/closure/miss-distance 相关的证据表或函数。Pk 曲线只能校准物理模型，不能替代 `EffectsEvent`、`DamageReport` 和平台状态。

当前最小闭环：

- 新增 `AircraftVulnerabilityProfile` runtime component，字段覆盖弹头族 scale、nose/beam/tail aspect scale、high/low closure scale、near-miss/direct-hit scale、`synthetic`、`provenance` 与 calibration authority gate；
- `damage_model.vulnerability` 可从 aircraft JSON 进入 `UnitDefinition`、spawn 到 entity，并作为 survivability capability evidence 暴露；
- F-16 先接入一份 `synthetic=true` 的 vulnerability scaffold，provenance 明确标注为 A2-P5 synthetic scaffold，不能用于 deterministic fuze/Pk 声称；
- `default_effects_model` 在 structured aircraft path 中消费该 profile：它调制 physical effects severity，而不是替代 hitbox、warhead profile、miss-distance 和 platform damage state；
- 新增 diagnostics-only `debug_apply_profiled_local_proximity_hit_with_velocity`，用于固定 warhead/local hit point 并显式设置合成导弹速度，从而回归 aspect/closure 对 vulnerability 调制的影响。
- 新增 evidence gate 字段：`calibrated`、`evidence_dataset_ref`、`calibration_status`、`pk_authority`、`deterministic_fuze_authority`；只有 `synthetic=false`、`calibrated=true`、`calibration_status=calibrated` 且有非空 dataset ref 时，profile 才允许进入 Pk authority / deterministic-fuze authority 语义；
- loader 会对不满足证据门的 profile 强制关闭 `pk_authority` 与 `deterministic_fuze_authority`；
- factory capability bundle 区分 `aircraft_vulnerability_synthetic_profile` 与 `aircraft_vulnerability_calibrated_profile`，避免把工程 scaffold 当作校准证据；
- 新增 diagnostics-only `debug_get_aircraft_vulnerability_evidence_state`，暴露 `[present, synthetic, calibrated_evidence, pk_authority, deterministic_fuze_authority]`，用于测试和审计 evidence gate。

仍未完成：外部或校准来源的 target/weapon vulnerability 表、按目标类别扩展的 evidence dataset、正式 Pk/kill-chain 校准和 deterministic fuze 放行证据。当前只是让脆弱性证据进入模型、影响 physical effects，并防止 synthetic scaffold 被误提升为 Pk/引信权威。

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
- `EffectsEvent` 至少暴露可检查的 direct/projection 命中形态、空间效应尺度、装甲耦合尺度、投影暴露尺度和机制效应尺度；
- `EffectsEvent` 至少暴露 component-threshold 尺度，证明同一弹头事件没有把所有受保护系统当作同一通用标量；
- `EffectsEvent` 至少暴露 component-failure probability/sample/count，证明组件级概率采样进入 effects 事件证据面；该字段仍是合成脚手架，不是 Pk 权威；
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
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_aircraft_vulnerability_profile_modulates_structured_damage \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries
```

结果：聚焦空战文件已通过，`43 passed, 12 subtests passed`。

## 外部评审

- [高保真要求独立评审](review_high_fidelity_requirements_20260526.zh.md) — 从空战杀伤建模领域要求出发，定义高保真的实质标准，独立于项目自身文档。

## 后续入口

- [任务簇](high_fidelity_damage_model_cluster_20260526.zh.md)
