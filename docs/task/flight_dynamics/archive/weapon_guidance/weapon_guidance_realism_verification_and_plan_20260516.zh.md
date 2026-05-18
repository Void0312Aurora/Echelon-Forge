# 武器系统与制导回路真实化核实与落地方案

状态：`2026-05-16` 方向三核实与实施方案版。

关联输入：

- [武器系统与制导回路现实性分析](weapon_guidance_realism_analysis_20260516.zh.md)
- [DefaultGuidanceModel](../../../../src/models/weapons/default_guidance_model.cpp)
- [DefaultEffectsModel](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem / ProximityFuze](../../../../src/systems/combat/damage_system.h)
- [SimulationKernel 武器 API](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [EW System](../../../../src/systems/systems/ew_system.h)

文档定位：

- 核实现有方向三调研结论哪些属实，哪些需要修正或补充。
- 给出按当前 ECS / model / system 边界可落地的实现方案。
- 整理导弹、导引头、近炸/毁伤所需的可用参考数据源。
- 给出建议优先级，作为后续真实化开发入口。

---

## A. 核实结论

### A.1 已核实属实的结论

1. `PN 目前并不是“加速度制导 + 自动驾驶仪”`，而是“LOS 角速率驱动的速度向量旋转”。
   - 代码位置：[default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - 具体表现：
     - `omega = (R x Vrel) / |R|^2` 后直接形成 `rate_x/y/z`。
     - 使用 Rodrigues 旋转更新速度方向。
     - 旋转后再把速度模长强制归一到 `missile.max_speed`。
   - 这意味着当前模型没有“法向加速度指令 -> 过载约束 -> 弹体响应”这一层。

2. `导弹能量学当前基本缺失` 属实，而且比原文档说得更明确。
   - 代码位置：[default_guidance_model.cpp:266](../../../../src/models/weapons/default_guidance_model.cpp)
   - 当前导弹不存在：
     - 助推/续航/滑翔分段
     - 阻力随速度/高度变化
     - 转弯诱导阻力
     - 质量随推进剂消耗变化
   - 发射时虽然继承了载机初速，但下一次 guidance tick 就被重置为 `max_speed`。

3. `导引计算仍直接使用目标真值` 属实。
   - 代码位置：[default_guidance_model.cpp:117](../../../../src/models/weapons/default_guidance_model.cpp)
   - 当前虽然先从导弹自身 `ContactList` 里选目标，但 PN 计算阶段仍直接读取目标的 `Transform` 和 `Velocity`。
   - 因此现有实现是“传感器决定看见谁，真值决定怎么打”，并不是真正意义上的 seeker-only guidance。

4. `诱饵/干扰当前只是粗糙近似` 属实。
   - 导引头侧：
     - [default_guidance_model.cpp:93](../../../../src/models/weapons/default_guidance_model.cpp) 仅按 `signal_strength` 选最强目标。
   - 传感器侧：
     - [default_sensor_model.cpp:252](../../../../src/models/systems/default_sensor_model.cpp) 对噪声压制干扰仅做一个 burn-through 距离门限。
     - [default_sensor_model.cpp:268](../../../../src/models/systems/default_sensor_model.cpp) 对热诱饵仅用 `Lifetime` 判定为“flare-like high IR source”。
   - 投放侧：
     - [ew_system.h](../../../../src/systems/systems/ew_system.h) 仅生成一个低速高 RCS 的 chaff 实体或继承速度的 flare 实体，没有时间强度曲线、角分离逻辑和 kinematic rejection。

5. `近炸引信当前是最近点启发式，不是定向/预测式引信` 属实。
   - 代码位置：[damage_system.h](../../../../src/systems/combat/damage_system.h)
   - 当前逻辑是：
     - 跟踪距离最小值
     - 一旦开始远离，且最近距离小于 `fuse_distance`，则判为可起爆
     - 再叠加一个基于 `quality * evasion` 的概率
   - 这不区分前向破片锥、相对方位、range-rate lead trigger。

6. `毁伤模型当前是 HP 与几何命中盒并存的双轨模型` 属实。
   - 代码位置：[default_effects_model.cpp:116](../../../../src/models/weapons/default_effects_model.cpp)
   - HP 路径可直接摧毁实体，几何路径则会进一步做系统级毁伤。
   - 这两条路径的物理含义不统一。

7. `命中盒体轴坐标变换存在姿态近似` 属实。
   - 当前仓库其实已经有共享变换工具 [common.h](../../../../src/components/basic/common.h)，支持完整 `heading/pitch/roll` 的 `world_to_body`。
   - [default_effects_model.cpp:32](../../../../src/models/weapons/default_effects_model.cpp) 仍在使用本地的简化 `world_to_body()`，且 `local_z = dz`，忽略了 pitch/roll。

8. `发射包线当前基本不存在` 属实。
   - 代码位置：[simulation_kernel_weapon_api.cpp:79](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
   - 当前只要求：
     - 有接触
     - 有弹
     - 不在冷却
   - 没有 LAR、LOBL/LOAL 区分、最小射程、最大动力射程、离轴角限制、能量可达性判断。

### A.2 需要修正或收窄的结论

1. `“导引头是完整机载雷达副本”` 这个说法需要收窄。
   - 更准确的说法应是：
     - 当前导弹 seeker 复用了通用 `Sensor` / `ContactList` 管线；
     - 这条管线已经包含视场、扫描周期、检测概率、噪声、Doppler notch、噪声干扰压制等简化能力；
     - 但它没有按 missile seeker 的工作模式做专门建模。

2. `“完全使用真值做制导”` 需要修正为更精确的描述。
   - 更准确的说法应是：
     - `target selection / lock retention` 依赖 seeker `ContactList`；
     - `relative geometry / LOS rate / closing speed for PN` 仍直接读取 target truth。

3. `“导弹没有任何抗干扰/抗诱饵能力”` 需要改为分层说法。
   - 雷达感知侧已有：
     - Doppler notch
     - simple burn-through
   - 红外/诱饵侧没有：
     - flare rise/decay
     - centroid tracking
     - kinematic rejection
     - track gate memory / seduction hysteresis

4. `“锁定距离与 FOV 完全不真实”` 需要补充“这是当前默认 tuning，而不一定是结构上不可表达”。
   - 当前默认值确实夸张：
     - `seeker_fov_deg = 180`
     - `seeker_lock_range = 30000`
   - 但这些值来自 [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp) 的默认 tuning，而不是框架硬编码成不可改。

### A.3 需要补充的新结论

1. `当前代码已经具备导弹真实化所需的一部分公共底座，可复用而不必重写物理内核`。
   - 可直接复用：
     - [aero_state_system.h](../../../../src/systems/physics/aero_state_system.h) 的 `dynamic_pressure` / `Mach`
     - [force_system.h](../../../../src/systems/physics/force_system.h) 的 atmosphere access
     - [common.h](../../../../src/components/basic/common.h) 的 body/world 坐标变换
     - [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp) 的 detection noise / track memory / EW hooks
   - 所以后续不必做完整 6DoF missile body dynamics，先做 `3DoF + accel/autopilot surrogate + seeker state` 就能显著提升可信度。

2. `当前 Missile 组件字段不够承载真实化参数`。
   - 代码位置：[weapon.h](../../../../src/components/combat/weapon.h)
   - 缺少的关键状态包括：
     - 推进段时间/推力/质量
     - 当前 seeker 模式
     - seeker track state / filtered LOS
     - autopilot commanded / achieved lateral accel
     - warhead / fuze 类型
     - 近炸预测状态

3. `当前测试树已经有合适挂点，但还没有真实性守门测试`。
   - 已有武器链测试主要在：
     - [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)
     - [test_air_combat_1v1_fixture.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fixture.py)
   - 目前主要覆盖“能否发射、能否看见、是否大致能杀伤”，还没有：
     - 能量衰减
     - PN 过载约束
     - seeker noise / filter
     - flare/chaff seduction trend
     - near miss / fuse timing / damage-layer consistency

---

## B. 实现方案

### B.1 总体落地原则

1. 第一阶段不追求完整 6DoF 导弹刚体模型，采用 `3DoF 质点 + 加速度指令 + 一阶自动驾驶仪 + 动压/过载限制`。
2. 导引头和传感器不分家重写，而是在现有 `Sensor -> ContactList -> GuidanceModel` 链条中增加 missile seeker 专属状态。
3. 命中/近炸/毁伤拆成三层：
   - `intercept / miss geometry`
   - `fuze / warhead effectiveness`
   - `damage / subsystem consequences`
4. 所有新参数优先进 `MissileTuning` 和 `Missile` 组件，不把状态散落到多个系统私有变量中。

### B.2 组件与配置扩展

#### 1. 扩展 `MissileTuning`

文件落点：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)

建议新增字段：

- 动力学/能量
  - `boost_time_s`
  - `sustain_time_s`
  - `boost_thrust_n`
  - `sustain_thrust_n`
  - `reference_area_m2`
  - `cd0_subsonic`
  - `cd0_supersonic`
  - `induced_drag_k`
  - `lift_slope_per_rad`
  - `max_lateral_g`
  - `autopilot_tau_s`
  - `max_accel_response_g_per_s`
- seeker
  - `seeker_type`
  - `seeker_activation_range_m`
  - `seeker_gimbal_limit_deg`
  - `seeker_ifov_deg`
  - `bearing_filter_tau_s`
  - `range_filter_tau_s`
  - `track_break_time_s`
  - `countermeasure_reject_gain`
- fuze / warhead
  - `warhead_type`
  - `warhead_mass_kg`
  - `fragment_cone_half_angle_deg`
  - `fragment_velocity_mps`
  - `fuse_arm_time_s`
  - `fuse_sensor_fov_deg`
  - `fuse_delay_s`
  - `impact_fuze_enabled`
- 发射条件
  - `min_launch_range_m`
  - `max_launch_off_boresight_deg`
  - `lobl_required`
  - `midcourse_datalink_supported`

#### 2. 扩展 `Missile` 运行时组件

文件落点：

- [weapon.h](../../../../src/components/combat/weapon.h)

建议新增运行时状态：

- `double burnout_time_s`
- `double current_speed_mps`
- `double achieved_lateral_accel_mps2`
- `double commanded_lateral_accel_mps2`
- `double filtered_bearing_deg`
- `double filtered_elevation_deg`
- `double filtered_range_m`
- `double bearing_rate_deg_s`
- `double elevation_rate_deg_s`
- `double track_age_s`
- `double last_valid_track_time_s`
- `int seeker_mode`
- `bool seeker_has_range`
- `bool fuze_armed`
- `double predicted_time_to_go_s`
- `double closest_approach_time_s`

### B.3 导弹能量/动力学

#### 1. 用现有环境模型做 3DoF 能量积分

主要修改文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)

实现方式：

1. 发射时设置：
   - 初始总质量 `Mass{empty, fuel, stores=0}`
   - `burnout_time_s = launch_time + boost + sustain`
   - `current_speed_mps = |v0|`
2. guidance tick 内根据当前时间和高度求：
   - `rho`、`speed_of_sound`
   - `q_bar = 0.5 * rho * V^2`
   - `Mach = V / a`
3. 推力分段：
   - `t < boost_time_s` -> `boost_thrust_n`
   - `boost <= t < boost+sustain` -> `sustain_thrust_n`
   - 其后为 `0`
4. 阻力分段：
   - `Cd = Cd0(Mach) + induced_drag_k * Cl_equiv^2`
   - 一阶版本中 `Cl_equiv` 可由当前法向加速度近似反推
5. 速度积分：
   - 沿速度方向做 `a_tangential = (T - D)/m`
6. 质量积分：
   - 推进期按常数质量流率减少 `fuel_mass_kg`

#### 2. 用过载约束替代固定 turn-rate

核心替换：

- 现有 `missile.turn_rate` 改为兼容字段，但真实化路径以 `max_lateral_g` 为主。

计算方式：

1. PN 先算 `a_cmd_lat`
2. 根据动压和限制求可达法向加速度：
   - `a_avail = min(max_lateral_g * g, q_bar_based_limit)`
3. 再经过一阶 autopilot：
   - `a_achieved += (a_cmd_clamped - a_achieved) * dt / tau`
4. 用 `omega_turn = a_achieved / max(V, eps)` 更新速度方向

### B.4 PN 从速度旋转改为加速度/近似过载约束

主要修改文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

建议分两步走：

#### Phase 1: 向量 PN + 加速度代理

1. 保留 `omega = (R x Vrel) / |R|^2`
2. 使用较稳定的向量 PN 形式：
   - `a_cmd = N * Vc * (omega x v_hat_m)`
3. 去掉 Rodrigues 直接几何旋转的主导地位，改成：
   - 先积分 `a_achieved`
   - 再由 `a_achieved` 改变 `v_hat`

#### Phase 2: 加入近似 autopilot

1. 一阶加速度响应：
   - `a_achieved_dot = (a_cmd_sat - a_achieved) / tau`
2. 速率限制：
   - `|da/dt| <= max_accel_response`
3. 大离轴时降低有效导航比：
   - `N_eff = N0 * clamp(Vc / V, 0, 1) * clamp(cos(gamma), 0, 1)`

### B.5 导引头测量与滤波

主要修改文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [sensor.h](../../../../src/components/systems/sensor.h)

#### 1. 先切断 guidance 对 truth position/velocity 的依赖

实现原则：

- guidance 只读 `best_det`
- 不再读取 target entity 的 `Transform/Velocity`

#### 2. 用轻量滤波器估计 LOS 与 LOS rate

一阶可落地方案：

- bearing / elevation 用 `alpha-beta` 或指数平滑差分
- radar seeker 才直接用 noisy range
- IR seeker 默认 `seeker_has_range = false`

推荐实现：

1. 对每个 tick 的 `bearing/elevation/range` 做 unwrap 后滤波
2. 用上次滤波值估计角速率
3. `Vc` 对 radar 可由 range-rate 或 closing_speed 近似
4. `IR` 若无 range，则采用弱化版 angular PN / lead pursuit

#### 3. seeker 模式分段

建议在当前结构中先支持三态：

- `Midcourse`
- `TerminalActive`
- `TerminalIR`

规则建议：

- `ARH`：中制导靠 launch track memory，进入 `seeker_activation_range_m` 后转 terminal active
- `SARH`：若 shooter track 丢失或 illumination 不满足，则失效
- `IR`：发射前若 `lobl_required`，则必须 missile seeker 在发射时已有 valid detection

### B.6 诱饵 / 干扰简化

主要修改文件：

- [ew_system.h](../../../../src/systems/systems/ew_system.h)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [ew.h](../../../../src/components/systems/ew.h)

#### 1. Flare 简化

建议新增 `DecoySignature` 组件：

- `type = flare/chaff`
- `rise_time_s`
- `peak_strength`
- `decay_tau_s`
- `drag_scale`

行为：

- flare 初始继承载机速度
- 在 0.2-0.5s 内快速升到峰值
- 随后按指数衰减
- 速度因阻力快速下降

导引头选择逻辑：

- 不再仅选瞬时最强信号
- 若目标与 flare 角分离小于 `ifov`，跟踪 centroid
- 若角分离足够，按 `signal_strength * kinematic_consistency_score` 选 track

#### 2. Chaff / noise jammer 简化

现有 radar sensor 已有：

- burn-through
- notch

建议补：

- chaff 的 Doppler rapidly collapses toward 0
- missile ARH seeker 对 `closing_speed` 异常低、角速率异常快的接触降权
- DRFM / RGPO / VGPO 暂不做完整欺骗回波，只做：
  - 虚假 range pull-away
  - 若 seeker filter 没有 reject，则导致 terminal miss 增大

### B.7 命中 / 近炸 / 毁伤分层

#### 1. 近炸层

主要修改文件：

- [damage_system.h](../../../../src/systems/combat/damage_system.h)

建议逻辑：

1. 在最近接近前后，根据相对位置 `r` 和相对速度 `v_rel` 估计 `t_ca`
2. 若 `0 <= t_ca <= dt_window`，预测最近点
3. 最近点小于 `fuse_distance` 且引信已解锁/解保，则起爆
4. 以 missile forward axis 和 target line-of-sight 的夹角决定 warhead effectiveness

#### 2. 战斗部有效性层

建议新增到 `DefaultEffectsModel` 之前的中间计算，或直接内聚在 effects model：

- 输入：
  - `closest_approach`
  - `relative_aspect`
  - `warhead_type`
  - `fragment_cone_half_angle`
- 输出：
  - `structural_hit_score`
  - `subsystem_hit_candidates`
  - `blast_overpressure_score`

#### 3. 毁伤层

主要修改文件：

- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- [damage.h](../../../../src/components/combat/damage.h)

建议改造：

1. 降低 `Health` 的主导地位
2. `SystemHealth` 改为连续降级
3. functional consequence 也改为连续
4. 命中盒坐标变换统一改用 [common.h](../../../../src/components/basic/common.h) 的 `Math::world_to_body`

### B.8 发射包线

主要修改文件：

- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)

第一阶段先做 4 个硬门槛：

1. `range` 必须在 `[min_launch_range, seeker/kinematic max]`
2. `abs(bearing)` 必须小于 `max_launch_off_boresight_deg`
3. 若 `lobl_required`，则 missile seeker 在 launch frame 必须有 valid detect
4. 若 `midcourse_datalink_supported == false` 且 target 超出 autonomous basket，则禁止发射

### B.9 测试方案落点

建议首批新增测试文件：

- `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`

首批守门项：

1. `energy_profile_boost_coast`
2. `turn_costs_energy`
3. `lateral_accel_limit_respected`
4. `seeker_noise_filter_is_not_truth_lock`
5. `flare_can_seduce_ir_but_not_always`
6. `chaff_affects_radar_more_than_ir`
7. `closest_approach_fuze_timing`
8. `damage_layering_continuous`

---

## C. 数据源建议

### C.1 可靠度分层

1. `一级：官方 / 厂商 / 军种事实页`
2. `二级：长期维护的军工资料站 / 国会研究处 / 专业媒体资料卡`
3. `三级：学术 / 技术综述 / 教材`
4. `四级：仿真社区 / 开源游戏配置 / 论坛经验值`

### C.2 建议直接使用的来源

#### 1. 官方/厂商/军种页

- RTX AIM-9X 页面：
  - [AIM-9X Sidewinder Missile](https://www.rtx.com/raytheon/what-we-do/sea/aim-9x-sidewinder-missile)
  - 可用于确认：
    - `IR tracking`
    - `Block II LOAL`
    - `weapon datalink`
    - `redesigned fuze`

- MBDA Meteor 页面：
  - [Meteor](https://www.mbda-systems.com/products/air-dominance/meteor)
  - 可用于确认：
    - 重量 `190kg`
    - 长度 `3.7m`
    - 直径 `178mm`
    - `ramjet`
    - `active radar`
    - `large no-escape zone`

#### 2. 半官方 / 长期维护资料站

- Designation Systems AIM-120：
  - [AIM-120 AMRAAM](https://www.designation-systems.net/dusrm/m-120.html)
  - 可用于确认：
    - `inertial autopilot`
    - `mid-course updates via data link`
    - `active radar terminal homing`
    - `WDU-33/B fragmentation warhead`
    - `FZU-49/B smart proximity fuze`
    - 典型射程区间、最小射程的公开引用值

- Designation Systems AIM-9：
  - [AIM-9 Sidewinder](https://www.designation-systems.net/dusrm/m-9.html)
  - 可用于确认：
    - 历代 Sidewinder seeker / warhead / proximity fuze 的变化
    - 早期型号视场、跟踪率、最大过载、有效 kill radius 等典型量级

- Air & Space Forces AIM-120 数据卡：
  - [AIM-120](https://www.airandspaceforces.com/weapons/aim-120/)
  - 可用于确认：
    - `boost-sustain solid-propellant rocket motor`
    - `active radar terminal / inertial midcourse`
    - `HE blast-fragmentation`
    - 近期型别差异，如 D / D3 的数据链、抗干扰、范围提升

#### 3. 制导/控制/滤波技术资料

- JHU APL Technical Digest：
  - `Principles of Homing Guidance`
  - `Overview of Missile Flight Control Systems`
  - 适合用于：
    - PN 基本形式
    - effective navigation constant
    - acceleration autopilot
    - seeker / guidance / control 分层

- Zarchan 系列公开引用与相关论文
  - 适合用于：
    - 向量 PN 的实现选择
    - `a_cmd = N * Vc * (...)` 形式的 sanity check

- 开放获取的 seeker LOS rate estimation / strapdown seeker 论文
  - 适合用于：
    - `alpha-beta` / `Kalman` / `UKF` 的轻量化选择

### C.3 建议优先收集的参数

1. `导弹几何与质量`
2. `推进体制`
3. `制导体制`
4. `导引头约束`
5. `战斗部/引信`

### C.4 参数初始化建议

对于拿不到公开精确值的量，建议先用区间初始化：

1. `autopilot_tau_s`
   - 先用 `0.06 - 0.15 s`
2. `max_lateral_g`
   - 近程格斗弹先用 `25 - 40 g`
   - 中距空空弹先用 `20 - 35 g`
3. `seeker_ifov_deg`
   - 先用 `1 - 3 deg`
4. `flare rise / decay`
   - `rise 0.1 - 0.3 s`
   - `strong phase 1 - 3 s`
5. `fragment cone half-angle`
   - 先用 `15 - 35 deg`

---

## D. 建议优先级

### D.1 P0：必须先做

1. `切断 guidance 对 target truth 的直接依赖`
2. `把恒速速度旋转改成“加速度指令 + 一阶 autopilot + 速度积分”`
3. `补导弹动力学/能量最小模型`
4. `补真实性守门测试`

### D.2 P1：应尽快跟进

1. `seeker filter 与 seeker mode`
2. `flare/chaff 简化抗干扰`
3. `发射包线硬门槛`

### D.3 P2：第二阶段完善

1. `近炸 lead trigger + 战斗部方向性`
2. `毁伤从 HP 主导转向 subsystem/structure 主导`
3. `连续降级的系统功能后果`
4. `HOJ / SARH / datalink` 的更细分支

### D.4 不建议在当前阶段优先做的内容

1. 完整 6DoF 导弹刚体 + fins + body rates
2. 完整 DRFM 欺骗链路
3. 高保真碎片弹道与穿甲
4. 机密级或过度细粒度型号参数复现

---

## 建议的首轮实施顺序

1. 扩展 `MissileTuning` / `Missile` 组件。
2. 重写 `DefaultGuidanceModel` 的核心状态推进：
   - seeker-only measurement
   - filtered LOS
   - PN accel command
   - autopilot lag
   - boost/coast + drag + mass
3. 补 `test_weapon_guidance_realism_guards.py`。
4. 给 `EW` 和 `Sensor` 增加 flare/chaff 的最小可信曲线与 reject 规则。
5. 再改 `DamageSystem` 和 `DefaultEffectsModel` 的近炸/毁伤分层。

如果只允许本方向先做一件事，那就先做：

`“去 truth guidance + 上 3DoF 加速度/能量模型”`

这是后续所有 seeker、规避、诱饵、LAR、命中概率问题能否被正确表达的前提。
