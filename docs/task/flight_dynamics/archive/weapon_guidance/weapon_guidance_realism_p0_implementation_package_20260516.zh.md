# 武器/制导真实化 P0 实施包

状态：`2026-05-16` P0 开工包。

关联文档：

- [武器系统与制导回路现实性分析](weapon_guidance_realism_analysis_20260516.zh.md)
- [武器系统与制导回路真实化核实与落地方案](weapon_guidance_realism_verification_and_plan_20260516.zh.md)

关联代码：

- [Missile 组件](../../../../src/components/combat/weapon.h)
- [SimulationKernel 武器接口](../../../../src/core/engine/simulation_kernel.h)
- [SimulationKernel 发射实现](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [默认制导模型](../../../../src/models/weapons/default_guidance_model.cpp)
- [默认传感器模型](../../../../src/models/systems/default_sensor_model.cpp)
- [武器链回归测试](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)

文档目的：

- 把方向三收敛成一个可以直接开工的 P0 包。
- 只覆盖最关键的三件事：
  - 切断 guidance 对 target truth 的直接依赖
  - 3DoF `boost/coast + drag + mass`
  - `PN 加速度指令 + 一阶 autopilot surrogate`

---

## 1. 目标

P0 的目标不是“做出完整导弹仿真器”，而是把当前武器链从“明显失真”推进到“趋势可信、可继续上层空战模拟”。

本包要求完成：

1. `Guidance truth cut`
   - `DefaultGuidanceModel` 不再直接读取目标 `Transform/Velocity` 参与 PN。
   - 制导主回路只消费 seeker `Detection` 和导弹自身历史状态。

2. `3DoF missile energy model`
   - 导弹速度不再每帧被强制归一到 `max_speed`。
   - 至少具备：
     - boost
     - sustain/coast
     - drag
     - propulsion mass depletion

3. `PN accel command + first-order autopilot`
   - 制导律输出从“角速率/速度旋转”转成“法向加速度指令”。
   - 用一阶响应近似导弹 autopilot，不引入完整 6DoF 刚体。

4. `P0 realism guard tests`
   - 给这三件事补首批守门测试，确保后续继续改时不会回退。

---

## 2. 非目标

P0 明确不做：

1. 完整 6DoF 导弹刚体、舵面、角速度和姿态闭环。
2. 完整 SARH / HOJ / DRFM / RGPO / VGPO 细节。
3. 完整近炸方向性、破片锥和 subsystem damage 重构。
4. 机型级高精度参数复刻。
5. 大范围数据库重构或统一武器内容系统。

P0 允许保留的近似：

1. `Detection` 仍沿用当前 `Sensor -> ContactList` 管线。
2. IR seeker 在第一版可以继续复用 `bearing/elevation/closing_speed`，但不得继续借用 target truth 位置。
3. autopilot 只做一阶加速度跟踪，不做内环角速率控制器。

---

## 3. P0 范围与交付物

### 3.1 范围内

1. `MissileTuning` 扩展到能表达 P0 所需的动力学和 seeker 参数。
2. `Missile` 运行时状态扩展到能保存：
   - filtered track
   - current energy state
   - commanded/achieved lateral acceleration
3. `fire_missile()` 初始化新字段。
4. `DefaultGuidanceModel` 改为：
   - seeker-only track update
   - PN accel command
   - first-order autopilot
   - thrust/drag/mass integration
5. 新增一组武器真实性守门测试。

### 3.2 范围外

1. `DefaultEffectsModel` 和 `DamageSystem` 只保留兼容，不纳入本次 P0 主实施。
2. EW 只做与 seeker 选择强相关的最小接口兼容，不做完整诱饵改造。
3. `Sensor` 通用模型不做大改，只在必要时做极小补充。

---

## 4. 需要新增/修改的具体文件

### 4.1 必改文件

1. [src/components/combat/weapon.h](../../../../src/components/combat/weapon.h)
   - 扩展 `Missile` 运行时状态。
   - 如有必要，新增 seeker/guidance mode 枚举。

2. [src/core/engine/simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
   - 扩展 `MissileTuning`。

3. [src/core/engine/simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
   - 初始化 P0 所需字段。
   - 保持默认参数兼容现有测试。

4. [src/models/weapons/default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - P0 主改造文件。
   - 替换 truth PN、恒速归一和固定 turn-rate 主逻辑。

5. [tests/runtime/air_combat/test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)
   - 新增 P0 守门测试文件。

### 4.2 可选新增文件

如果 `default_guidance_model.cpp` 体积增长过快，允许新增：

1. [src/models/weapons/missile_guidance_math.h](../../../../src/models/weapons/missile_guidance_math.h)
   - 向量工具
   - alpha-beta 过滤辅助
   - thrust/drag helper

2. [src/models/weapons/missile_guidance_types.h](../../../../src/models/weapons/missile_guidance_types.h)
   - 小型内部 struct / enum

P0 不建议新增新的 ECS system；主逻辑仍应放在 `DefaultGuidanceModel`。

---

## 5. 字段设计

### 5.1 `MissileTuning` P0 最小字段集

文件：

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)

建议新增：

```cpp
int seeker_type = 0;                 // 0=ARH, 1=IR, 2=SARH (P0 先主要用 0/1)
double seeker_activation_range_m;
double bearing_filter_tau_s;
double elevation_filter_tau_s;
double range_filter_tau_s;
double track_break_time_s;

double boost_time_s;
double sustain_time_s;
double boost_thrust_n;
double sustain_thrust_n;
double reference_area_m2;
double cd0_subsonic;
double cd0_supersonic;
double induced_drag_k;
double propellant_mass_kg;

double max_lateral_g;
double autopilot_tau_s;
double max_accel_response_g_per_s;
```

说明：

1. `seeker_type` 用 `int` 而不是新 enum 暴露到 facade，可减少本轮改动面。
2. `range_filter_tau_s` 对 IR 第一版可以忽略，但字段先留好。
3. `propellant_mass_kg` 放在 tuning 而不是 `Mass` 默认值里，便于后续数据库化。
4. `cd0_subsonic/cd0_supersonic` 足够支撑 P0；不做完整 Mach 表。

### 5.2 `Missile` P0 最小运行时状态

文件：

- [weapon.h](../../../../src/components/combat/weapon.h)

建议新增：

```cpp
int seeker_mode = 0;                 // 0=Track, 1=Memory, 2=Terminal

double filtered_bearing_deg = 0.0;
double filtered_elevation_deg = 0.0;
double filtered_range_m = 0.0;
double bearing_rate_deg_s = 0.0;
double elevation_rate_deg_s = 0.0;
double last_track_time_s = -1.0;

double current_speed_mps = 0.0;
double commanded_lateral_accel_mps2 = 0.0;
double achieved_lateral_accel_mps2 = 0.0;
double burnout_time_s = -1.0;
```

可选新增：

```cpp
bool seeker_has_valid_track = false;
bool seeker_has_range = true;
```

P0 刻意不在 `Missile` 中塞太多未使用字段，避免把第二阶段内容提前带进来。

### 5.3 `Mass` 使用方式

文件：

- [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)

P0 不修改 `Mass` 结构，只约定导弹实体按下面方式初始化：

1. `empty_mass_kg` = 壳体 + 战斗部 + 电子设备
2. `fuel_mass_kg` = 推进剂质量
3. `stores_mass_kg` = `0`

这样 guidance model 内可直接用 `mass.get_total_kg()`，不需要另加 missile-specific mass component。

---

## 6. 核心实现设计

### 6.1 切断 guidance 对 target truth 的直接依赖

主文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 约束：

1. 删除或停用以下路径：
   - `world.entity(missile.target_id).get<Transform>()`
   - `world.entity(missile.target_id).get<Velocity>()`
2. Guidance 只从 `best_det` 和导弹自身历史状态构造 LOS。
3. 必须允许“短时丢测但继续记忆制导”：
   - `current_time - last_track_time_s <= track_break_time_s`

P0 推荐做法：

1. 每个 guidance tick：
   - 先从 `ContactList` 选 best detection
   - 若找到：
     - 更新 `filtered_bearing/elevation/range`
     - 更新 `bearing_rate/elevation_rate`
     - `last_track_time_s = now`
   - 若未找到但仍在 `track_break_time_s` 内：
     - 进入 `Memory` 模式
     - 维持上次滤波状态，不再更新测量
   - 若超时：
     - 退出主动制导，保持当前速度方向飞行

这样做的结果是：

1. truth lock 被切断。
2. seeker 噪声与 scan 周期会真实进入制导回路。
3. 后续 flare/chaff 才真正有机会改变导引行为。

### 6.2 3DoF `boost/coast + drag + mass`

主文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 建议状态推进：

1. `V = |velocity|`
2. 从环境拿：
   - `rho`
   - `speed_of_sound`
3. 算：
   - `Mach`
   - `q_bar = 0.5 * rho * V^2`
4. 推力：
   - `t < boost_time_s`: `boost_thrust_n`
   - `boost <= t < boost+sustain`: `sustain_thrust_n`
   - else `0`
5. 阻力：
   - `cd0 = lerp(cd0_subsonic, cd0_supersonic, mach_blend)`
   - `D = q_bar * reference_area_m2 * (cd0 + induced_drag_term)`
6. 质量：
   - 在 boost+sustain 时间内线性烧蚀 `fuel_mass_kg`
7. 速度：
   - 沿航迹方向积分 `(T - D) / m`

P0 允许的近似：

1. 不显式积分重力沿航迹项，若会显著复杂化可暂时省略。
2. `induced_drag_term` 可先由 `achieved_lateral_accel` 近似构造，而不是严格从 `Cl` 反推。

### 6.3 PN 加速度指令 + 一阶 autopilot surrogate

主文件：

- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)

P0 推荐公式：

1. 用滤波后的 LOS 构造单位视线方向。
2. 用角速率近似 LOS rotation rate。
3. 计算：

```cpp
a_cmd_lat = N * Vc * lambda_dot_equiv;
```

或其向量形式近似：

```cpp
a_cmd_vec = N * Vc * (omega_los x v_hat);
```

4. 饱和到：

```cpp
a_cmd_sat = clamp(|a_cmd|, max_lateral_g * g)
```

5. 一阶 autopilot：

```cpp
a_achieved += (a_cmd_sat - a_achieved) * dt / autopilot_tau_s;
```

6. 再加一个建立速率限制：

```cpp
|da/dt| <= max_accel_response_g_per_s * g
```

7. 用：

```cpp
omega_turn = a_achieved / V
```

更新速度方向。

P0 的重点不是 PN 公式选哪一本教材版本，而是：

1. guidance 输出的是加速度量纲
2. 有过载饱和
3. 有响应滞后
4. 高速/低速与能量模型耦合

---

## 7. 测试清单

### 7.1 新增测试文件

- [tests/runtime/air_combat/test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)

### 7.2 P0 必测项

1. `test_missile_speed_profile_boost_then_decay`
   - 发射后前几秒速度上升。
   - 燃尽后速度开始下降。

2. `test_missile_mass_decreases_during_propulsion`
   - 推进期内 `fuel_mass_kg` 下降。
   - 燃尽后不再下降。

3. `test_guidance_no_longer_reads_target_truth`
   - 通过构造 seeker contact 并篡改/隔离 target truth access 路径，验证 guidance 仍可运行。
   - 更现实的做法是对比“只有 detection 更新时导弹轨迹改变；没有 detection 时进入 memory/straight-fly”。

4. `test_pn_outputs_bounded_lateral_accel`
   - commanded accel 可以大于可达值。
   - achieved accel 受 `max_lateral_g` 和 `autopilot_tau_s` 约束。

5. `test_large_turn_costs_speed`
   - 大离轴拦射末速低于小离轴直追。

6. `test_track_memory_timeout_reverts_to_ballistic_or_hold`
   - seeker 丢测后在 `track_break_time_s` 内继续 memory guidance。
   - 超时后不再继续更新导引。

### 7.3 P0 可选测试

1. `test_high_altitude_turn_authority_differs_from_low_altitude`
2. `test_scan_period_and_noise_affect_terminal_error_trend`

---

## 8. 外部数据落地方式

### 8.1 P0 不直接做数据库系统重构

P0 建议两层落地：

1. `代码层`
   - 先把经过筛选的参数放进 `MissileTuning` 默认值和测试专用 tuning。
2. `文档层`
   - 建一份可追溯参数表，记录来源和置信度。

### 8.2 推荐的数据落地文件

P0 建议新增一个轻量参考表：

- `docs/task/flight_dynamics/weapon_guidance/weapon_guidance_p0_reference_table_20260516.md`

表字段建议：

| family | parameter | value | unit | source | confidence | note |
| --- | --- | --- | --- | --- | --- | --- |

示例参数：

1. `aim_120_like`
   - `mass_total_kg`
   - `warhead_mass_kg`
   - `boost/sustain`
   - `guidance = inertial_midcourse + active_terminal`
2. `aim_9x_like`
   - `mass_total_kg`
   - `loal_supported`
   - `ir seeker`
   - `off_boresight class`

### 8.3 数据源使用原则

1. 一级源直接定类别和量级：
   - 厂商页
   - 军种事实页
2. 二级源补典型区间：
   - Designation Systems
   - FAS
   - Air & Space Forces 数据卡
3. 学术资料只用于：
   - PN / autopilot / filter 结构
   - 不直接给具体型号参数

### 8.4 P0 参数落地策略

P0 不追求“某型弹绝对真实”，只做两个类模板：

1. `arh_mraam_like`
   - 代表 AIM-120 / Meteor 一类中距主动弹的趋势
2. `ir_wvraam_like`
   - 代表 AIM-9X / IRIS-T 一类近距红外弹的趋势

这样能减少数据库压力，也能先把仿真规律跑顺。

---

## 9. 推荐实现顺序

推荐拆成 6 步：

1. `扩字段`
   - 修改 [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) 和 [weapon.h](../../../../src/components/combat/weapon.h)
   - 只加入 P0 最小字段，不写逻辑。

2. `补发射初始化`
   - 修改 [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
   - 给新字段合理默认值和初始化。
   - 保证老测试不因未初始化而炸掉。

3. `切断 truth guidance`
   - 修改 [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
   - 先把 target truth 读路径删掉，换成 detection + memory state。
   - 这一步先不做复杂能量模型。

4. `上 PN accel + autopilot surrogate`
   - 同文件继续改。
   - 先让 guidance 输出加速度，并有一阶跟踪与 G 限制。

5. `接入 boost/coast + drag + mass`
   - 仍在 guidance model 内完成。
   - 去掉 `velocity = max_speed normalized` 路径。

6. `补守门测试`
   - 新增 [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py)
   - 先守住 truth cut、speed profile、mass depletion、accel saturation、track memory timeout。

这个顺序的好处是：

1. 每一步都可单独跑测试。
2. 第 3 步完成后就已经切断最大失真源。
3. 第 4-5 步把动力学真实性逐步接上，不会一次性把问题揉在一起。

---

## 10. P0 完成判据

满足以下条件即可视为 P0 完成：

1. `DefaultGuidanceModel` 中不再直接读取目标 `Transform/Velocity` 做 PN。
2. 导弹速度曲线具备“推进升速、燃尽衰减”的基本趋势。
3. 导引响应表现出：
   - 加速度饱和
   - 一阶建立滞后
4. 新增 P0 守门测试全部通过。
5. 现有基础武器链测试不出现大面积回归。

如果 P0 做完后只带来一个变化，也应该是：

`导弹终于会因为看不准、转不动、掉能量而错过目标，而不是凭真值和恒速硬拐上去。`
