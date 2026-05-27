# A2 高真实度空战毁伤模型任务簇 - 2026-05-26

状态：`A2-D0` 已接受；`2026-05-26` Phase 0 已接受，Phase 1 最小补丁正在推进，Phase 2 已从 generated fallback 推进到首批 authored aircraft hitbox 内容，并新增 `AircraftDamageState` 飞机专用 overlay、overlay-driven 飞行动力学/推进/传感器派生、受损结构在高动压/高速包线下继续劣化的最小闭环，以及火灾/燃油泄漏/液压损伤的最小时间级联，Phase 3 已从最小 `WarheadProfile` 数据通路推进到首个弹头族 effects 分配补丁、按弹头族 footprint 的近炸空间投射闭环、最小 relative-velocity-axis 空间方向耦合、`EffectsEvent` 几何与引爆姿态证据字段、引爆姿态轴驱动的参数化 orientation-pattern 证据、hitbox armor / projected exposure / warhead mechanism 可审计采样字段、机制特定 component-threshold 尺度字段、合成 component-failure probability 采样字段、显式 `FuzeProfile` 证据字段、proximity fuze delay 的最小延迟爆轰调度、首个 fuze type trigger semantics 行为分支、组件级几何入口、数据库级 F-16/Su-35/MQ-9/MH-60R/E-3 代表性组件样例、`EffectsEvent` 主组件身份字段、critical/redundancy 对组件失效概率的最小调制，以及组件依赖到相关系统/overlay 的最小传播，Phase 5 已启动 synthetic vulnerability evidence scaffold、补入 calibrated evidence gate，并把 vulnerability profile/evidence/authority/scale 写入 `EffectsEvent` 审计面；structured-air physical effects 已补“不直接写 RL Score”的行为/静态守卫；1v1 consumer 已从 terminal/objective 迁移推进到非终局 `DamageReport` 连续 shaping 的最小一次性消费。`PN miss-distance baseline` 已闭合，不再阻塞 HP-first bypass 最小反转；deterministic fuze 仍 deferred；contact/impact/timed 的触发语义已开始脱离单一 proximity radius，live missile 的引爆姿态也已可审计并能派生参数化方向证据，但这些仍不是校准引信或方向性战斗部效应模型。

## 决策

本任务簇采用 forward 评估中的严格立场：

1. 空战毁伤模型是高真实度仿真路径，不是 RL reward 快捷路径；
2. `Health.current_hp` 不再被规划为带结构化毁伤飞机的 kill authority；
3. Phase 1 前必须先完成 Phase 0 审计，否则 HP bypass 反转、飞机 hitbox 接入和 deterministic fuze 都不能开工；
4. `ForcedLanding` 不能通过重排现有 `PlatformLossState` 数值实现。若需要，优先 append-only 或 aircraft overlay state；
5. deterministic fuze 必须等待 PN miss-distance baseline matrix。

## 任务流

| 流 | 状态 | 目标 | 写入面 | 非目标 | 验证 | 退出条件 |
|----|------|------|--------|--------|------|----------|
| `A2-D0 文档与边界冻结` | accepted | 建立子项目，冻结高真实度毁伤原则和 Phase 0 gate。 | `docs/task/air_combat/a2_high_fidelity_damage_model/**`、air_combat 索引 | 行为代码 | 文档 diff、索引可达 | 子项目能作为后续实现入口 |
| `A2-P0.1 PlatformLossState 审计` | closed_for_design | 查明枚举值、raw int 比较、Python 暴露和序列化风险。 | 文档、必要时只读脚本 | 改枚举 | grep + 测试引用清单 | 得出 append-only/overlay 决策 |
| `A2-P0.2 health observer 审计` | closed_with_guard | 盘点 `health > 0`、`get_unit_health`、`is_unit_active` 的语义依赖。 | 文档、只读 probe | 改 reward/termination | 调用点表 | 明确 HP 派生读数迁移影响 |
| `A2-P0.3 ShipPlatform filter 审计` | closed_for_design | 判定 damage update 是新建 aircraft 系统还是泛化现有 naval 系统。 | 文档、只读 grep | 移除 filter | consumer matrix | 不破坏 ship-only 系统 |
| `A2-P0.4 Aircraft content inventory` | evidence_closed/content_gap_open | 列出飞机类型与 hitbox 缺口，选择 authored/generator 策略。 | 文档、数据库清单 | 批量填内容 | aircraft inventory | 每类飞机有明确 hitbox 路径 |
| `A2-P0.5 Score write-point 审计` | structured_air_guarded/consumer_started | 找出 effects model 中 reward/score 写点，设计事件消费层迁移。 | 文档、必要时测试计划 | 立即重构 legacy score | write-point list + guard tests | structured-air physical effects 不直接写 Score；1v1 terminal/objective 已开始消费 DamageReport |
| `A2-P0.6 PN miss-distance baseline` | closed_with_baseline | 构造 head-on / tail-chase / beam / high-off-boresight miss-distance 基线。 | benchmark/test docs，debug runtime probe | deterministic fuze | 可重复基线输出 | 已决定 Phase 4 继续 deferred |
| `A2-P1 Aircraft structured damage` | minimal_patch_in_progress | 反转 HP-first bypass，并让飞机走结构化毁伤路径。 | effects model、damage system、engagement event recorder、tests | deterministic fuze、warhead profile 全量实现 | focused combat tests | structured target 不被 HP-first bypass kill，live missile 能产出 DamageReport |
| `A2-P2 Aircraft subsystem effects` | overlay_dynamic_coupling_started | 飞机推进/飞控/结构/燃油/传感器/航电/飞行员级联效果。 | damage systems、flight/sensor consumers、aircraft JSON | Pk 曲线、全量 vulnerability 声称 | hitbox-specific tests | 不同 authored hitbox 后果可区分，且单次近炸不会因重叠 box 被重复放大；飞机专用 overlay 可审计并下推飞行动力学/推进约束 |
| `A2-P3 Warhead profile` | profile_fuze_component_identity_started | 引入 blast/frag/rod/HTK profile 与显式 fuze profile，旧 JSON synthetic 兼容，并让近炸空间 footprint 随弹头族、速度轴、引爆姿态轴、hitbox armor、projected exposure、组件机制阈值、组件身份、合成组件失效概率、组件 critical/redundancy、fuze reliability、fuze delay 调度、引爆姿态证据和 fuze type trigger semantics 变化。 | weapon definitions、loader、effects model、engagement contracts、aircraft database | external Pk 数据、完整破片云、校准姿态方向性效应、校准组件失效概率、校准引信性能、全库组件数据、完整冗余依赖图 | warhead runtime/effects tests | warhead/fuze family/mass/radius/delay/reliability/provenance 可审计，scalar damage 标记为兼容层；near miss 投射按弹头族半径/衰减/影响数量、relative velocity axis 和 detonation attitude axis 区分；contact/impact fuze 不再把 near-miss radius 当作触发条件；timed fuze 能按发射后 delay 独立起爆；EffectsEvent 暴露 miss distance、局部起爆点、引爆姿态、闭合速度、导弹速度轴、引爆姿态轴、orientation pattern scale、direct/projection 命中形态、fuze type/radius/delay/reliability、nearest approach 与 detonation time 分离、空间效应尺度、装甲耦合、投影暴露、机制效应尺度、component-threshold 尺度、component identity 和 component-failure probability/sample/count |
| `A2-P4 Deterministic fuze` | deferred | 几何优先引信/杀伤替代 RNG hit roll。 | fuze/damage system | 未验证 PN 前移除 RNG | miss-distance matrix + controlled fuze tests | evasion 通过 miss distance 生效 |
| `A2-P5 Vulnerability evidence` | event_audit_component_probability_rows_started | 引入 weapon/target/aspect/closure 脆弱性或 Pk 校准数据。 | content/data/contracts | 黑箱替代物理模型 | provenance/event tests | F-16 synthetic vulnerability profile 可审计并调制 physical effects；authority gate 与 `EffectsEvent.vulnerability_*` 可证明 synthetic/profile 自声明不放行 Pk/确定性引信；授权 rows 可驱动 scale 或组件失效概率，未授权 rows 不被消费 |

## Phase 0 证据表模板

每个 Phase 0 gate 关闭时，必须记录：

- grep / probe 命令；
- 发现的关键调用点；
- 风险等级；
- 是否允许进入下一阶段；
- 若允许，采用的迁移策略；
- 若不允许，阻塞原因和最小解除条件。

建议输出位置：

- `docs/task/air_combat/a2_high_fidelity_damage_model/phase0_preflight_YYYYMMDD.zh.md`

当前审计输出：

- [Phase 0 预检审计 - 2026-05-26](phase0_preflight_20260526.zh.md)

## Phase 1 最小补丁边界

Phase 1 的第一批代码变更应该足够小：

- 只针对带结构化 damage state 的 aircraft 禁用 HP-first bypass；
- 不改变 legacy 无 hitbox 目标的兼容行为；
- aircraft hitbox 可以先用明确标注的 generated whole-aircraft fallback，但必须仍走 structured damage path；
- `Score` 写入迁移可以先通过事件消费层最小实现，不把奖励逻辑留在 effects model；
- 新测试必须能证明 HP bypass 不再提前 `return`。

当前已完成的最小实现：

- `default_effects_model.cpp` 对 structured aircraft / C2Node 跳过 HP-first branch，legacy 非结构化目标仍保持旧 HP path；
- `debug_apply_proximity_hit` 对 structured aircraft 使用中心线合成 impact，保证调试命中能触达 generated hitbox；
- `ProximityFuze` live missile 路径通过 `EngagementEventRecorderRef` 记录 `EffectsEvent` 与 `DamageReport`；
- `AircraftDamageStateUpdate` 只同步 Aircraft/C2Node 的 capability kill flags 与 `Lost` 析构，不泛化舰船 `NavalDamageStateUpdate`；
- `AircraftDamageStateUpdate` 已开始消费 `AeroState`：结构受损后，高动压/高 Mach 暴露会累积 `flutter_exposure` / `structural_overstress` 并缓慢降低结构完整性；普通受损巡航和低速失速不会被直接当作 flutter；
- `AircraftDamageStateUpdate` 已开始从 aircraft overlay 派生传感器性能：航电/机组损伤会降低 range/Pd、增加噪声并缩短 track memory，非传感器/非航电命中不误降感知；
- `AircraftDamageStateUpdate` 已开始消费 control-axis overlay：aileron/elevon/rudder/flap/thrust-vector/cyclic/collective 等命名控制组件命中会降低 roll/pitch/yaw authority，单侧控制面或推力矢量损伤会提高 `control_asymmetry`，并下推到 turn-rate / mobility 派生约束；
- 默认 1v1 发射测试从“一发必杀”改为“不误锁/不误伤友方 + 事件目标一致”。

## Phase 2 authored hitbox 最小差异化

本轮已从 generated fallback 推进到首批 authored aircraft hitbox。它仍是工程校准的结构化内容，不宣称完整 vulnerability/Pk 证据闭环：

- nose/radar：降低 sensor capability 与 radar range；
- fuselage engine/fuel：降低 mobility capability、削弱推力、增加 fuel leak；
- wing/flight_control：降低 mobility capability，并收紧 `max_g`、`max_turn_rate`、`max_accel`、`max_climb_rate`；若 authored wing 同时保护 fuel，则触发 fuel leak；
- 单次近炸事件对 structured aircraft 的平台级能力扣减按类别归一化，避免重叠 authored hitbox 把一枚近炸重复放大成直接 `Lost`；
- diagnostics-only `debug_apply_local_proximity_hit` 用局部机体系坐标稳定命中指定 hitbox，避免测试依赖随机近炸几何。
- 新增 `AircraftDamageState` overlay，记录结构、飞控、液压、roll/pitch/yaw control authority、control asymmetry、推进、燃油、航电、机组、火灾、燃油泄漏、结构过载/颤振暴露、forced landing 和 subsystem kill 标志；
- authored hitbox 命中先更新飞机专用 overlay，再下推到兼容的 `PlatformDamageState` capability 字段，避免继续把飞机毁伤细节挤进舰船语义字段；
- diagnostics-only `debug_get_aircraft_damage_state` 用于验证 air-specific overlay。
- 新增 `AircraftDamageBaseline` 保存初始 FlightModel/Propulsion/fuel-leak 基线，damage update 每帧从 overlay 派生 turn rate、accel、climb、g-limit、speed、推力和 fuel leak；
- `AircraftDamageBaseline` 也保存初始 `Sensor` 基线，damage update 每帧从 `avionics_integrity` 与 `crew_effectiveness` 派生 BVR sensor range、detection probability、measurement noise 与 track memory；
- propulsion 与 fuel 在 overlay 中拆分：fuel hit 不再直接等价 thrust loss，engine/propulsion hit 才降低推力派生值。
- `AircraftDamageStateUpdate` 已补最小级联时间线：燃油泄漏会真实消耗 `FuelSystem` 内/外挂油并同步 `Mass` 燃油质量；火灾按燃油/液压/航电损伤和泄漏活动继续传播到结构、航电、机组、液压和燃油系统；液压损伤会继续拖累飞控并增加结构过载暴露；级联结果下推平台 mission/sensor/mobility/survivability 能力。
- 最小离散控制面接入已从 F-16 aileron 扩展到 rudder、leading-edge/inboard flap、Su-35 thrust-vector actuator、MH-60R cyclic/collective 等代表控制件：命中会降低对应 roll/pitch/yaw authority、记录 control asymmetry，并通过外层 FlightModel 派生收紧 turn rate；这仍不是完整控制律/力矩模型。

已补的 authored content：

- `E-3_Sentry_AWACS` 从 HP-only/C2Node 迁移到 authored structured damage path，覆盖 cockpit/command、radar/data-link、fuel/avionics、engine、wing/flight-control hitboxes；
- `F-16C_Block50` 覆盖 nose radar/cockpit、fuselage fuel/avionics/engine、aft engine/flight-control、wing flight-control/fuel；
- `Su-35S_Flanker-E` 覆盖 nose radar/cockpit、fuselage fuel/avionics/data-link、双发 engine/fuel、wing flight-control/fuel；
- `MQ-9_Reaper` 覆盖 sensor/navigation、fuel/data-link/avionics、engine/propeller、wing flight-control/fuel；
- `MH-60R_MVP` 覆盖 cockpit/sensor、fuel/avionics/data-link、engine/transmission、rotor/tail-rotor flight-control；
- 测试证明 E-3 radar hit 后 HP 不扣减、不析构，但 sensor capability、mission capability 与 radar range 会下降，并产生 `DamageReport`。

验收测试：

- `test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects`
- `test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems`
- `test_phase2_aileron_component_damage_derives_roll_axis_authority`
- `test_phase2_avionics_and_crew_damage_derives_sensor_performance`
- `test_phase2_aircraft_fire_fuel_and_hydraulic_damage_cascade_over_time`
- `test_phase2_damaged_airframe_high_speed_envelope_accumulates_structural_damage`
- `test_e3_sentry_c2node_uses_authored_structured_damage_model`
- `test_aircraft_database_units_have_authored_structured_damage_models`

## Phase 3 WarheadProfile 数据通路与首个 effects 分配

本轮关闭战斗部 profile 数据面，并开始让 profile 影响 structured aircraft effects 分配和近炸空间 footprint；仍不宣称完整战斗部空间效应：

- weapon JSON 的 `warhead.type/mass_kg/lethal_radius/damage` 进入 `MissileTuningDefinition`；
- `MissileTuning`、运行时 `Missile` 和 Python diagnostics 暴露 `WarheadProfile`；
- 没有显式 `damage` 的现有空空导弹以 warhead mass 生成 synthetic damage scalar，并通过 `damage_scalar_synthetic` 标记；
- `EffectsEvent` 增加 `warhead_mass_kg`、`warhead_lethal_radius_m`、`warhead_profile_synthetic`、`damage_scalar_synthetic`；
- `EffectsEvent` 增加 `miss_distance_m`、目标机体系 `detonation_local_forward/right/up_m`、`detonation_heading/pitch/roll_deg`、`closure_mps` 和 `missile_axis_forward/right/up`，用于记录近炸几何、引爆姿态和后续引信/Pk 校准输入；
- live proximity fuze 记录的 `effect_family` 来自 missile warhead profile，可覆盖为 `continuous_rod` 等族。
- `default_effects_model` 对 structured aircraft 引入弹头族 effects 分配：blast 偏结构/火灾，blast-fragmentation 为平衡基线，continuous rod 偏机翼/飞控，hit-to-kill 偏局部系统杀伤且低火灾扩散；
- 新增 diagnostics-only `debug_apply_profiled_local_proximity_hit`，用于固定局部命中点对比不同 `WarheadProfile` effects。
- 新增近炸空间投射：structured aircraft 无直接 hitbox 交点时，战斗部 lethal radius 的保守局部范围会按弹头族设定半径、衰减曲线和最大影响 hitbox 数；blast/fragmentation 类宽域弹头优先按区域 hitbox 覆盖多个邻近区域，避免同一翼面内多个组件候选挤占 footprint，continuous rod 更窄，hit-to-kill 保持局部化；远场 near miss 仍不产生结构化毁伤。
- 近炸投射按系统类别保留局部场强，避免一个弱覆盖系统套用最近 hitbox 的强场，从而保持“近炸弱于直接命中对应关键 hitbox”的回归约束。
- 近炸投射引入最小 relative-velocity-axis 耦合：导弹速度轴会转入目标机体系，continuous rod 对横向扫掠候选 hitbox 更敏感，hit-to-kill 更偏轴向局部，blast/fragmentation 只做较弱方向修正。
- live proximity fuze 结算会把最近距离和当前目标机体系起爆点写入事件；由于结算发生在最近点后一帧，`closure_mps` 可合法为 0，因此它是诊断证据而非确定性引信放行条件。
- live missile 会在引信 armed 时冻结 `detonation_heading_deg`、`detonation_pitch_deg`、`detonation_roll_deg`，延迟结算事件继续使用该姿态证据；effects model 还会把该姿态转成目标机体系 `warhead_orientation_axis_forward/right/up` 并派生 `warhead_orientation_pattern_scale`，但这仍是参数化证据，不等价于已校准的方向性破片云或连续杆效应。
- 新增 warhead spatial sampling evidence：fragmentation / blast-fragmentation 按战斗部质量、暴露面积、球面稀释和距离能量估算破片样本数、命中估计和命中比例；continuous rod 按杆段样本数、目标展向、环形扫掠几何、速度轴横向权重和引爆姿态轴 orientation-pattern 权重估算杆命中数。该证据会调制近炸候选 effect scale，并通过 `EffectsEvent` 暴露 sample count、hit estimate/fraction、energy scale、pattern scale、orientation axis 和 orientation pattern scale；它仍是参数化采样，不是校准破片云或完整连续杆切割模型。
- 新增首个机制采样脚手架：直接 hitbox 交叠与近炸空间投射都会消费 hitbox `armor_mm`、局部投影暴露面积、弹头族机制容量、距离质量和 velocity-axis 权重；同几何下低装甲翼面会比高装甲翼面承受更强飞控/液压/结构损伤。
- 新增首个机制特定 component-threshold scaffold：同一 hitbox 内的飞控、燃油、传感器/航电、发动机、座舱/机组和结构按弹头族使用不同敏感度，避免所有组件继续共享同一个通用 severity 标量。
- 新增首个合成 component-failure probability scaffold：直接命中和近炸投射会按 severity、mechanism scale、component threshold scale 与 direct/projection 形态采样组件失效；触发后把额外失效冲击写入 aircraft overlay / platform damage。
- F-16 数据库级组件样例已扩展到 22 个代表组件，覆盖 fire-control radar、cockpit、nose avionics、IFF、fuselage fuel、mission computer、data link、navigation、power bus、flight-control computer、engine core、afterburner nozzle、engine fuel control、hydraulic pump、rudder actuator、wing fuel、aileron、leading-edge flap actuator 和 wing spar 等挂点；
- Su-35S 数据库级组件样例已扩展到 23 个代表组件，覆盖 nose radar/cockpit/avionics/IRST、fuselage fuel/avionics/data-link/navigation/power/flight-control computer、左右发动机 core/fuel-feed/thrust-vector actuator 和机翼 fuel/elevon/leading-edge flap/spar 等挂点；
- MQ-9、MH-60R、E-3 已分别扩展到 23/22/27 个代表性组件：覆盖 UAV 传感器/数据链/任务处理/电源/推进/机翼飞控，直升机座舱/传感器/燃油/任务系统/电源/传动/旋翼与尾桨飞控，以及 C2 大型机 rotodome radar、任务系统、数据链/导航/电源、中机身燃油、发动机舱、机翼燃油/飞控/翼梁；这些样例证明组件化证据面已跨 fighter/UAV/直升机/C2 平台族运行，但仍不是全库所有飞机 20-50 项组件数据。
- `EffectsEvent` 新增 `component_hit_count`、`component_primary_name`、`component_primary_system`、`component_primary_redundancy_group` 和 `component_primary_critical`，使组件级几何命中可由事件面追溯，而不是只出现在日志中；
- component-failure probability 已开始消费组件 `critical` 与 `redundancy_group`：同几何下非关键、冗余 actuator 的失效概率低于单点关键 actuator；本轮新增 `ComponentDamageState` 运行时记忆和命名 `redundancy_group_id`，F-16/Su-35S wing fuel cell、aileron/elevon actuator、wing spar 样例以及 MQ-9/MH-60R/E-3 代表性组件会初始化组件完整性、冗余组成员数和组可用性。连续命中同一组件会累计降低 `component_primary_integrity`，而组可用性按同组其他成员贡献保留，作为最小冗余依赖图入口；它仍不是完整液压/飞控/电源依赖网络。
- 新增组件 `dependencies` 最小传播：组件可声明依赖系统，loader/factory 会初始化依赖系统，effects model 会在组件完整性/冗余组可用性下降后把影响传播到依赖系统与 aircraft overlay。当前覆盖飞控作动器到 hydraulic/flight_control、任务雷达到 avionics/mission_systems/data_link，以及代表性电源/数据链组件到 flight_control/data_link/mission_systems/avionics 等最小链路；这是冗余依赖图入口，不是完整系统网络。
- 新增显式 `FuzeProfile` 证据面：weapon JSON、运行时 missile 和 `EffectsEvent` 暴露 fuze type、trigger radius、delay、reliability 与 synthetic provenance；live proximity 仍不放行确定性引信，只用 trigger radius/reliability 调制现有 proximity/RNG gate，并用 delay 调度 delayed detonation。
- 新增首个 fuze type trigger semantics：`proximity` / `radar_proximity` / `laser_proximity` 继续按近炸触发半径工作；`contact` / `impact` 要求导弹进入目标 authored hitbox 表面接触容差，不再把 near-miss radius 误记录为接触引信起爆；当前 live contact/impact 事件还会把表面距离、穿入深度、接触容差和是否进入 hitbox 写入运行时与 `EffectsEvent`；`timed` 按发射后 `delay_s` 独立调度起爆，不依赖近炸门，远离目标时可记录 `detonated_no_effect`。
- 新增 proximity-fuze target-signature scaffold：`radar_proximity` 会按目标 RCS/aspect 代理调制有效引信可靠度，`laser_proximity` 会按目标 hitbox 投影几何代理调制有效引信可靠度，并在事件中暴露 `fuze_signature_source`、`fuze_target_signature`、`fuze_signature_scale` 与 `fuze_effective_reliability`。该路径只证明雷达/激光近炸引信开始消费目标签名证据，仍保留 RNG gate，不是校准引信模型。
- `EffectsEvent` 增加 `direct_hitbox_intersection`、`projected_hitbox_count`、`spatial_effect_scale`、`mechanism_armor_scale`、`mechanism_exposure_scale`、`mechanism_effect_scale`、`warhead_spatial_sample_count`、`warhead_spatial_hit_estimate`、`warhead_spatial_hit_fraction`、`warhead_spatial_energy_scale`、`warhead_spatial_pattern_scale`、`warhead_orientation_axis_forward/right/up`、`warhead_orientation_pattern_scale`、`component_threshold_scale`、`component_failure_probability`、`component_failure_probability_source`、`component_failure_probability_calibrated`、`component_failure_probability_evidence_dataset_ref`、`component_failure_sample`、`component_failure_count`、`component_hit_count`、`component_primary_name`、`component_primary_system`、`component_primary_redundancy_group`、`component_primary_critical`、`component_primary_redundancy_group_id`、`component_primary_integrity`、`component_redundancy_group_availability`、`component_redundancy_group_member_count`、`component_redundancy_group_failed_count`、`detonation_heading_deg`、`detonation_pitch_deg`、`detonation_roll_deg`、`fuze_type`、`fuze_trigger_radius_m`、`fuze_delay_s`、`fuze_reliability`、`fuze_signature_source`、`fuze_target_signature`、`fuze_signature_scale`、`fuze_effective_reliability`、`fuze_contact_surface_distance_m`、`fuze_contact_penetration_depth_m`、`fuze_contact_surface_tolerance_m`、`fuze_contact_inside_hitbox` 与 `fuze_profile_synthetic`，用于把一次 effects 结论回溯到几何、引爆姿态、引信、弹头族、目标结构、空间采样、机制采样、组件失效概率来源、组件身份、组件状态记忆和冗余组可用性证据。

验收测试：

- `test_definition_missile_tuning_flows_into_launch_runtime`
- `test_global_warhead_profile_override_flows_into_runtime_and_effects_event`
- `test_fuze_delay_schedules_detonation_after_nearest_approach`
- `test_fuze_event_records_detonation_attitude_evidence`
- `test_contact_fuze_does_not_trigger_from_near_miss_radius`
- `test_contact_fuze_records_surface_and_penetration_evidence`
- `test_timed_fuze_detonates_on_delay_without_proximity_gate`
- `test_phase3_warhead_family_changes_structured_air_effect_distribution`
- `test_phase3_proximity_field_projects_near_miss_onto_nearest_air_hitbox`
- `test_phase3_spatial_projection_respects_warhead_family_footprint`
- `test_phase3_continuous_rod_near_miss_uses_relative_velocity_axis`
- `test_phase3_warhead_spatial_sampling_reports_fragment_and_rod_evidence`
- `test_phase3_warhead_orientation_axis_modulates_rod_pattern_evidence`
- `test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor`
- `test_phase3_database_f16_component_geometry_reports_primary_component`
- `test_phase3_database_su35_component_geometry_reports_primary_component`
- `test_phase3_representative_aircraft_database_components_cover_uav_helo_c2`
- `test_phase3_representative_aircraft_components_report_runtime_identity`
- `test_phase3_component_dependencies_are_authored_for_representative_control_and_mission_components`
- `test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems`
- `test_phase3_mission_component_dependency_damage_propagates_to_avionics_overlay`
- `test_phase3_component_redundancy_reduces_failure_probability`
- `test_phase3_component_redundancy_group_tracks_cumulative_integrity`
- `test_phase5_aircraft_vulnerability_profile_modulates_structured_damage`
- `test_phase5_vulnerability_adjustment_is_recorded_on_effects_event`
- `test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority`
- `test_phase5_authorized_vulnerability_rows_drive_effects_event_scales`
- `test_phase5_vulnerability_rows_require_effect_scale_authority`
- `test_phase5_authorized_rows_drive_component_failure_probability`
- `test_phase5_component_failure_rows_require_probability_authority`
- `test_phase5_vulnerability_evidence_dataset_descriptor_loads_without_authority`
- `test_engagement_contract_header_exposes_lifecycle_effects_and_damage_surface`
- `test_weapon_launch_adapter_snapshots_cover_munition_effects_damage_trace_contract_fields`

## Phase 5 Vulnerability evidence scaffold

本轮启动脆弱性/Pk 证据入口，但仍不把 Pk 当作 physical effects authority：

- 新增 `AircraftVulnerabilityProfile`，可由 aircraft JSON 的 `damage_model.vulnerability` 进入 runtime component；
- profile 包含弹头族、aspect、closure、near-miss/direct-hit 调制项，以及 `synthetic`、`provenance`、`calibrated`、`evidence_dataset_ref`、`calibration_status`、`pk_authority`、`deterministic_fuze_authority`；
- F-16 先使用 synthetic scaffold，明确标注需要校准，不能据此声称确定性引信或 Pk 完成；
- Su-35、MQ-9、MH-60R、E-3 已补 neutral synthetic target-family vulnerability scaffold，默认 scale 保持 1.0，只扩展 fighter/UAV/直升机/C2 目标族的运行时 evidence gate 覆盖面，不把未校准假设写成杀伤强度；
- loader 会读取 `damage/vulnerability_evidence/*.json` descriptor，并对不满足 `synthetic=false + calibrated=true + calibration_status=calibrated + evidence_dataset_ref 指向已加载、非 synthetic、target 匹配、descriptor 自身 calibrated 且具备 weapon/aspect/closure/miss-distance 证据轴` 的 profile 强制关闭 calibrated evidence；
- Pk 与确定性引信 authority 必须由匹配 descriptor 逐项授予；缺失 descriptor、synthetic placeholder descriptor、target/status/证据轴不匹配或 descriptor 未授权的能力都会被关闭，即 aircraft JSON 自声明不能成为权威；
- capability bundle 区分 synthetic scaffold 与 calibrated profile，避免把工程调参误标为校准证据；
- `default_effects_model` 只用 profile 调制 structured aircraft effects severity，仍由 hitbox、warhead profile、miss-distance 与平台状态决定后果；
- 新增 velocity-aware diagnostics helper，用于验证 closure/aspect 对调制的影响；
- 新增 vulnerability evidence diagnostics helper，暴露 `[present, synthetic, calibrated_evidence, pk_authority, deterministic_fuze_authority, evidence_dataset_valid]`，用于验证 synthetic F-16 profile 和伪造 calibrated claim 只能作为调制输入，不能作为 Pk 或 deterministic fuze authority。
- 新增首个只读 vulnerability evidence dataset descriptor，固定 target/weapon/aspect/closure/miss-distance key 和 authority=false 元数据；该 descriptor 当前只证明 evidence 数据形状可审计，不参与 damage 计算，也不授予 Pk 或 deterministic fuze authority。
- 新增临时数据库回归：缺失 descriptor 不放行，synthetic placeholder descriptor 不放行，缺失 evidence axes 的 descriptor 不放行，非 synthetic 且 target/status/weapon/aspect/closure/miss-distance 证据轴齐备的测试 descriptor 才能按字段授予 Pk 或 deterministic-fuze authority。该测试 descriptor 只证明门控机制，不代表已有正式校准数据。
- 新增 target-family scaffold 回归：F-16/Su-35/MQ-9/MH-60R/E-3 的 vulnerability profile 都会进入运行时，但 evidence state 均为 `[present, synthetic, no calibrated evidence, no Pk authority, no deterministic-fuze authority, no valid dataset]`。
- `EffectsEvent` 新增 `vulnerability_profile_present`、`vulnerability_profile_synthetic`、`vulnerability_calibrated_evidence`、`vulnerability_pk_authority`、`vulnerability_deterministic_fuze_authority`、`vulnerability_evidence_dataset_valid/ref`、`vulnerability_calibration_status`、`vulnerability_provenance`、`vulnerability_aspect_bucket`、`vulnerability_family/aspect/closure/miss_distance/effect_scale` 和模型实际使用的径向 `vulnerability_closure_mps`。该事件面证明 vulnerability 调制可审计，但 synthetic profile、synthetic descriptor 或 JSON 自声明仍不能获得 Pk / deterministic-fuze authority。
- descriptor 可新增 `effect_scale_authority`、`component_failure_probability_authority` 与 `rows[]`，使通过 gate 的非 synthetic/calibrated dataset row 按 weapon family、aspect、closure 和 miss-distance 匹配并驱动 effects model 的 vulnerability scale 或组件失效概率；未授予对应 authority 的 rows 即使存在也不会被消费。`EffectsEvent` 会把组件失效概率来源标记为 `synthetic_sigmoid` 或 `vulnerability_evidence_row`，并携带 calibrated flag 与 dataset ref。当前 rows 仍只在测试 fixture 中证明数据通路，不代表已有正式 calibrated vulnerability/Pk 数据。

未完成项保持打开：正式 calibrated vulnerability/Pk dataset、目标族覆盖、外部/校准证据、正式 Pk/kill-chain 校准和 deterministic fuze 放行。

## Reward / score authority guard

本轮补齐 A2-P0.5 的 structured-air 最小防退化证据：

- `test_structured_air_damage_does_not_write_rl_score_from_physical_effects` 验证结构化空中目标毁伤会产生 `DamageReport`，但 attacker `AgentObservation.total_reward` 不被 physical effects path 改写；
- `test_a2_structured_air_effects_do_not_write_rl_score_authority` 静态固定 `default_effects_model` 的 structured-air 分支不能写 `score->...`；
- legacy HP path 的历史 `Score` 写入暂时保留在 `if (hp && !structured_air_target)` 中，作为兼容边界。

本轮 consumer 迁移启动：

- `gym_envs.scenario_loader.reward_runtime.air_combat` 提供空战 profile 识别和 `DamageReport` terminal 解释；
- 1v1 terminal override 会把 `lost`、`mobility_kill`、`mission_kill` 等 `DamageReport` 结果解释为目标不再具备战斗可行动性；
- conditional objective 的 `target_active` / `target_health` 兼容读数同步消费该 neutralized 语义；
- `apply_air_combat_reward_surface` 只读未消费过的近期 `DamageReport`，从 `system_health_delta` 与 `platform_damage_state_delta` 派生目标毁伤进展、自身受损惩罚和 loss-state progression 奖惩；
- `test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win` 固定“HP 不变、entity active、DamageReport mobility_kill”仍能触发 `combat_win`；
- `test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once` 固定非终局结构毁伤可以给 RL shaping，但同一 report 不会重复计分。

仍未完成：全量 subsystem capability 曲线、课程级训练统计、target-family vulnerability dataset 和 Pk/evidence calibration 还未系统性迁移；当前 shaping 不能反向定义物理毁伤权威。
阶段零 fixed-fire smoke 仍受 RNG fuze 影响：真实导弹进入 fuse radius 后仍可能随机未命中，因此 smoke 只证明发射链路和稳定运行；不得把单发必然 `combat_win` 作为 Phase 4 未放行前的验收。

## 风险与保护

- **行为突变风险**：已有 air combat tests 可能默认一次导弹命中直接击杀。Phase 1 必须保留 legacy fixture 或更新断言，使测试描述真实语义；
- **训练信号风险**：RL 可能失去连续 HP reward。应从 `DamageReport` 和 kill state 构造训练读数；
- **舰船回归风险**：泛化 `NavalDamageStateUpdate` 容易伤及 ship-only 系统。若证据不足，优先新建 aircraft damage update；
- **数据缺口风险**：已有 authored hitbox、当前 aircraft units 库 20+ 代表组件覆盖、组件 dependencies 最小传播、warhead/fuze profile plumbing、armor/exposure/component-threshold/component-identity/component-failure 机制采样仍是工程校准/数据通路，不允许声称已完成战斗部空间效应、破片云、连续杆切割、未来新增飞机组件数据、校准组件级失效概率、完整冗余依赖图、校准引信、脆弱性/Pk 全高保真闭环；
- **引信过确定风险**：没有 PN miss-distance 基线时，deterministic fuze 可能让 evasion 在 damage 上失效。

## 当前推荐下一步

继续 Phase 1/2/3 最小闭环，不启动 P4：

1. 保持 deterministic fuze deferred，不在 warhead/fuze/脆弱性校准前移除 RNG hit roll；
2. 用 live missile regression 固定 structured aircraft damage report；
3. 后续 Phase 2 应从首批 authored hitbox 继续推进到更细飞控/液压、结构 g-limit、flutter 边界、座舱/飞行员 overlay；
4. 后续 Phase 3 应推进 blast/fragment/rod/HTK 差异化 effects、warhead geometry sampling、全库组件数据和冗余依赖图；
5. 后续训练 reward 应消费 `DamageReport` / loss state / subsystem capability，而不是重新依赖 HP 连续扣减。

## 建议命令

边界 smoke：

```bash
bash -lc 'source tools/maintenance/cmo_env.sh && cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json'
```

当前空战固定链路：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py \
  tests/runtime/engagement
```

world-batch 契约：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/world_batch/test_world_batch_runtime.py \
  tests/runtime/facade/test_runtime_facade.py
```

## 退出状态

本任务簇只能以以下状态推进或关闭：

- `phase0 accepted`：六个预检门均有证据，允许设计 Phase 1 patch；
- `phase0 blocked`：任一预检门发现未处理的跨层风险，禁止行为代码；
- `phase1 accepted`：structured aircraft target 已能通过非 HP-first 权威路径产生 kill state；
- `deferred`：损伤模型被明确排在训练或可视化任务之后；
- `rejected`：仅当项目决定不追求高真实度毁伤模型时使用。
