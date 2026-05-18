# 飞行动力学真实化 P0 实施包

状态：`2026-05-16` P0 开工包。

关联输入：

- [飞行动力学现实性分析与空战前置门槛](flight_dynamics_realism_analysis_20260516.zh.md)
- [AeroStateSystem](../../../../src/systems/physics/aero_state_system.h)
- [AerodynamicsSystem](../../../../src/systems/physics/aerodynamics_system.h)
- [ForceSystem](../../../../src/systems/physics/force_system.h)
- [DefaultControlModel](../../../../src/models/air/default_control_model.cpp)
- [LogisticsSystem](../../../../src/systems/systems/logistics_system.h)
- [DefaultEnvironmentModel](../../../../src/models/environment/default_environment_model.cpp)
- [FlightDynamics 粗真实性守门测试](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)

文档目标：

- 把飞行动力学真实化方向收敛成一个可直接开工的 `P0` 实施包。
- 明确本轮只做参数骨架、状态骨架、推进骨架和最小真实性验证。
- 避免过早进入大范围机型化或全包线高保真实现。

---

## 1. P0 目标

P0 只解决“后续真实化能否在正确的骨架上推进”的问题，不解决“是否已经高保真”。

本轮必须达成的目标：

1. 为气动与推进真实化建立稳定的参数入口：
   - `aero_tuning`
   - `engine_tuning`
2. 为失速/高攻角恢复建立最小运行时状态：
   - `alpha_dot`
   - `stall_state`
   - `stall_progress`
3. 为发动机瞬态建立独立骨架：
   - `propulsion_system`
   - 推力状态与时间常数
   - 与燃油/仪表的一致性接口
4. 建立首批最小验证测试：
   - 油门阶跃响应
   - `AoA_dot / stall_state` 基础可观测性
   - 失速进入与恢复趋势守门
   - 参数默认回退路径不破坏现有主线

---

## 2. 非目标

以下内容明确不属于 P0：

1. 不做完整机型级 `Cl/Cd/Cm/Cn(M, alpha, beta)` 查表。
2. 不做完整控制面动力学、控制分配、`g-command` FBW。
3. 不做完整过失速/spin/wing rock 建模。
4. 不做惯量随外挂投放和燃油分布的联动重算。
5. 不做湍流、阵风、微下击暴流等环境增强。
6. 不做空战策略回训，只做最小真实性守门测试。

P0 的成功标准不是“飞得像 F-16”，而是“后续 P1/P2 可以在不返工数据结构的前提下继续往前做”。

---

## 3. 实施范围

### 3.1 需要新增的文件

建议新增：

1. [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)
   - 放 `AeroTuning`
   - 放 `EngineTuning`
   - 放 `StallState`
2. [src/systems/physics/propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
   - 负责 throttle -> thrust state 的推进瞬态
3. [tests/runtime/test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)
   - 新增 P0 骨架测试

### 3.2 需要修改的文件

建议修改：

1. [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)
   - 扩展 `Propulsion`
2. [src/components/physics/forces.h](../../../../src/components/physics/forces.h)
   - 扩展 `AeroState`
3. [src/content/unit_definition.h](../../../../src/content/unit_definition.h)
   - 为 `Airframe` / `Engine` 增加真实化可选字段
4. [src/content/unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
   - 读取 tuning 字段
5. [src/models/core/default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
   - 挂载 `AeroTuning` / `EngineTuning` / `StallState`
6. [src/systems/physics/aero_state_system.h](../../../../src/systems/physics/aero_state_system.h)
   - 生成 `alpha_dot`
7. [src/systems/physics/aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
   - 读取 `AeroTuning`
   - 更新 `stall_state / stall_progress`
8. [src/systems/physics/force_system.h](../../../../src/systems/physics/force_system.h)
   - 从“直接算推力”切到“消费 propulsion state”
9. [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h)
   - 油耗改读实际推力状态
10. [src/systems/physics/instrument_system.h](../../../../src/systems/physics/instrument_system.h)
    - 仪表改读实际发动机状态
11. [src/core/engine/simulation_kernel_systems.cpp](../../../../src/core/engine/simulation_kernel_systems.cpp)
    - 注册 `propulsion_system`

---

## 4. 字段设计

### 4.1 `AeroTuning`

落点建议：

- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

P0 只放一维分段和少量标量，不上二维查表。

建议字段：

```cpp
struct AeroTuning {
    bool enabled = false;

    double cl_alpha_per_deg = 0.1;
    double cl0 = 0.0;
    double cd0_clean = 0.02;
    double induced_drag_k = 0.1;
    double cm_alpha_per_rad = -0.8;
    double cm_q = -12.0;

    double alpha_stall_clean_deg = 15.0;
    double alpha_stall_flaps_full_deg = 21.0;
    double alpha_peak_offset_deg = 8.0;
    double alpha_deep_offset_deg = 18.0;

    double cl_peak_clean = 1.25;
    double cl_peak_flaps_full = 1.70;
    double cl_deep_clean = 0.22;
    double cl_deep_flaps_full = 0.32;

    double pitch_break_onset_deg = 16.0;
    double pitch_break_full_deg = 28.0;
    double pitch_break_cm_nose_down = -0.35;

    double post_stall_damp_floor = 0.25;

    std::vector<double> mach_breakpoints;
    std::vector<double> cl_alpha_scale_vs_mach;
    std::vector<double> cd0_add_vs_mach;
    std::vector<double> induced_drag_scale_vs_mach;
    std::vector<double> cm_alpha_scale_vs_mach;
    std::vector<double> stall_alpha_delta_deg_vs_mach;
};
```

设计意图：

- `enabled=false` 时保持当前默认行为，避免一次性冲击全仓库。
- `mach_breakpoints + values` 足够支撑 P1 的压缩性修正，不需要先引入复杂表引擎。
- `pitch_break_*` 是 P0 的关键，因为它决定后续恢复趋势能否从气动里长出来，而不是只靠 FBW 硬压。

### 4.2 `EngineTuning`

落点建议：

- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

建议字段：

```cpp
struct EngineTuning {
    bool enabled = false;

    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;

    double throttle_ab_threshold = 0.9;
    double throttle_idle_bias = 0.1;

    double tau_spool_up_s = 2.5;
    double tau_spool_down_s = 1.5;
    double tau_ab_light_s = 1.0;
    double tau_ab_extinguish_s = 0.5;

    double ram_rise_gain = 0.3;
    double ram_rise_mach_cap = 1.2;
    double ram_decay_start_mach = 1.5;
    double ram_decay_gain = 0.2;

    double thrust_sigma_exponent = 1.0;
    double thrust_theta_exponent = -0.5;

    double tsfc_mil_kg_per_ns = 0.0;
    double tsfc_ab_kg_per_ns = 0.0;
};
```

设计意图：

- `tau_spool_*` 是 P0 最核心的新物理时间常数。
- `ram_*` 允许先把现有 `1 + 0.3M` 从硬编码挪到配置层。
- `sigma/theta` 预留温度效应入口，但 P0 只要求字段先到位。

### 4.3 `Propulsion` 运行时状态

修改落点：

- [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)

建议新增字段：

```cpp
double throttle_command = 0.0;
double throttle_state = 0.0;
double dry_thrust_command_n = 0.0;
double dry_thrust_state_n = 0.0;
double ab_command = 0.0;
double ab_state = 0.0;
double current_tsfc = 0.0;
```

说明：

- `current_thrust_n` 和 `afterburner_active` 保留，避免影响现有外部接口。
- `throttle_state` 和 `ab_state` 让 `ForceSystem / LogisticsSystem / InstrumentSystem` 共享同一事实来源。

### 4.4 `AeroState` 与 `StallState`

修改落点：

- [src/components/physics/forces.h](../../../../src/components/physics/forces.h)
- [src/components/physics/flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)

建议新增字段：

```cpp
struct StallState {
    double stall_progress = 0.0;
    double time_in_stall_s = 0.0;
    bool is_stalled = false;
    bool pitch_break_active = false;
};
```

```cpp
// in AeroState
double angle_of_attack_rate_dps = 0.0;
double previous_angle_of_attack = 0.0;
```

说明：

- P0 不引入复杂 stall memory 模型，但至少要能观测“是否进入失速”和“alpha 正在多快变化”。
- `pitch_break_active` 用于测试和调试，也为后续仪表与 failfast 替代逻辑留出口。

---

## 5. 系统与代码落点

### 5.1 `propulsion_system`

新增文件：

- [src/systems/physics/propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)

职责边界：

1. 读取控制输入解算后的 throttle command
2. 读取 `EngineTuning`
3. 积分：
   - `throttle_command -> throttle_state`
   - `dry_thrust_command -> dry_thrust_state_n`
   - `ab_command -> ab_state`
4. 计算：
   - `current_thrust_n`
   - `afterburner_active`
   - `current_tsfc`
5. 不直接向 `ForceAccumulator` 施力

建议注册顺序：

`AeroStateSystem -> PropulsionSystem -> ForceSystem -> AerodynamicsSystem`

这样 `PropulsionSystem` 可以读到同帧的大气与马赫，又不会和 `ForceSystem` 职责重叠。

### 5.2 `force_system`

修改原则：

- 保留重力施加
- 保留鼻向推力投影
- 删除推力直接从 throttle 即时计算的主逻辑
- 改成消费 `Propulsion.current_thrust_n`

这一步是 P0 最关键的边界收敛：

- `ForceSystem` 负责“把已有推力状态作用到机体”
- `PropulsionSystem` 负责“求出这个推力状态”

### 5.3 `aero_state_system`

P0 只新增一项核心能力：

- `angle_of_attack_rate_dps`

实现方式：

1. 在每帧计算出 `alpha_raw`
2. 由 `alpha_raw - previous_angle_of_attack` 求差分
3. 做最小限度的 unwrap / clamp
4. 更新 `previous_angle_of_attack`

不在 P0 做：

- `beta_dot`
- 复杂滤波器
- 动态失速模型

### 5.4 `aerodynamics_system`

P0 只做三件事：

1. 当 `AeroTuning.enabled=false` 时保持当前默认逻辑
2. 当 `enabled=true` 时：
   - 用 `mach_breakpoints` 对 `Cl_alpha/Cd0/k/Cm_alpha/stall_alpha` 做一维调度
3. 更新 `StallState`
   - `stall_progress`
   - `is_stalled`
   - `pitch_break_active`

P0 推荐只加入一个最小 `pitch_break` 项：

```text
Cm_total = Cm_baseline + Cm_pitch_break(alpha, stall_progress)
```

不在 P0 做：

- `Cm_alpha_dot`
- `Cn_p`
- 非对称负迎角失速
- `beta` 对升力和失速的二阶耦合

### 5.5 `logistics_system` 与 `instrument_system`

两者都必须同步跟上 `Propulsion` 状态，否则会产生新的内部不一致：

1. [logistics_system.h](../../../../src/systems/systems/logistics_system.h)
   - 由“按 throttle 烧油”改成“按 `current_tsfc * current_thrust_n` 烧油”
2. [instrument_system.h](../../../../src/systems/physics/instrument_system.h)
   - `fuel_flow_kg_h`、`engine_rpm_pct` 改为读 `throttle_state / ab_state / current_tsfc`

---

## 6. 外部数据落地方式

### 6.1 数据来源分层

P0 只要求把数据入口打通，不要求所有字段都拿到官方值。

优先级建议：

1. `一手官方/科研`
   - NASA TP-1538
   - US Standard Atmosphere 1976
   - FAA 喷气机飞行教材
2. `公开仿真基线`
   - AeroBenchVVPython / AeroBenchVV
   - JSBSim / FlightGear F-16
3. `社区参考`
   - EM 图、手册摘录、论坛汇总

### 6.2 仓库内落地位置

P0 不新开数据目录，直接复用现有数据库结构：

1. 发动机参数：
   - `examples/config/database/aircraft/modules/engines/*.json`
2. 气动/平台参数：
   - 第一阶段先挂在 `examples/config/database/aircraft/units/*.json`
   - 如果后续需要多机共享，再拆 `modules/aero/`

### 6.3 推荐 JSON 形态

发动机模块建议支持：

```json
{
  "name": "f110_ge_129",
  "type": "Engine",
  "mil_thrust_n": 76000.0,
  "ab_thrust_n": 129000.0,
  "sfc_mil": 0.0,
  "sfc_ab": 0.0,
  "engine_tuning": {
    "enabled": true,
    "tau_spool_up_s": 2.5,
    "tau_spool_down_s": 1.5,
    "tau_ab_light_s": 1.0,
    "tau_ab_extinguish_s": 0.5,
    "ram_rise_gain": 0.3,
    "ram_rise_mach_cap": 1.2,
    "ram_decay_start_mach": 1.5,
    "ram_decay_gain": 0.2
  }
}
```

机体建议支持：

```json
{
  "name": "f16c_block50",
  "type": "Aircraft",
  "airframe": {
    "empty_mass_kg": 8570.0,
    "max_fuel_kg": 3100.0,
    "reference_area": 27.87,
    "wingspan_m": 9.45,
    "length_m": 15.06,
    "height_m": 4.88
  },
  "aero_tuning": {
    "enabled": true,
    "alpha_stall_clean_deg": 15.0,
    "pitch_break_onset_deg": 16.0,
    "pitch_break_full_deg": 28.0,
    "pitch_break_cm_nose_down": -0.35,
    "mach_breakpoints": [0.0, 0.6, 0.9, 1.1, 1.5, 2.0],
    "cl_alpha_scale_vs_mach": [1.0, 1.0, 1.12, 0.95, 0.75, 0.60],
    "cd0_add_vs_mach": [0.0, 0.0, 0.01, 0.035, 0.02, 0.015]
  }
}
```

### 6.4 P0 的数据使用原则

1. 宁可先用“血缘清楚的近似值”，也不要继续把关键效应硬编码死在系统里。
2. 所有非官方参数都要标注来源层级：
   - `official`
   - `research-derived`
   - `community-reference`
3. 文档或注释里要标明“这是趋势约束值”还是“拟合/近似工作值”。

---

## 7. 测试清单

### 7.1 必须新增的 P0 测试

建议新增：

- [tests/runtime/test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)

覆盖以下项目：

1. `throttle_step_response_is_not_instant`
   - `idle -> mil`
   - `mil -> ab`
   - 验证 `current_thrust_n` 不是一步跳满
2. `fuel_flow_tracks_actual_thrust_state`
   - 验证推力状态变化会带来燃油流量同步变化
3. `aoa_dot_is_reported_and_finite`
   - 基础抬头 probe 下 `AoA_dot` 有限、符号合理
4. `stall_state_enters_before_failfast_like_departure`
   - 验证高抬头时会先进入 `stall_state`
   - 不是只在极端姿态末端才触发失控逻辑
5. `pitch_break_adds_nose_down_recovery_trend`
   - 在相同初态下，开启 `pitch_break` 后应更早出现低头恢复趋势
6. `disabled_tuning_preserves_legacy_behavior_envelope`
   - `enabled=false` 时基础合同不要明显被打坏

### 7.2 建议扩展现有守门测试

在 [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/test_flight_dynamics_realism_guards.py) 上增加两类断言：

1. 记录 `AoA_dot` 峰值
2. 记录 `stall_state` 是否被触发

这样 P0 新增状态能立刻进入现有守门视角。

### 7.3 P0 不要求新增的测试

以下测试留到 P1/P2：

1. 跨声速包线定量验证
2. 完整 EM 图趋势验证
3. 高空高速加速时间标定
4. 多机型参数回归矩阵

---

## 8. 推荐实现顺序

建议按 6 步推进。

### Step 1. 先落组件与配置骨架

目标：

- 新增 `flight_dynamics_tuning.h`
- 扩展 `Propulsion`
- 扩展 `AeroState`
- 扩展 `UnitDefinition` 与 loader

完成标准：

- 不改运行逻辑
- 默认值下现有测试行为不变

### Step 2. 挂载默认工厂与数据库读取

目标：

- `default_unit_factory` 给实体挂 `AeroTuning` / `EngineTuning` / `StallState`
- `f16c_block50` / `f110_ge_129` 先各补一份最小 tuning

完成标准：

- 实体能读到配置
- 但未启用时不改变动力学主线

### Step 3. 新增 `propulsion_system`

目标：

- 实现 throttle state / AB state / current thrust skeleton
- 注册到系统顺序中

完成标准：

- `ForceSystem` 仍可运行
- `current_thrust_n` 开始由新系统生成

### Step 4. 接通燃油与仪表一致性

目标：

- `logistics_system` 改读实际推力状态
- `instrument_system` 改读实际发动机状态

完成标准：

- 推力、燃油、RPM 三者在同一条状态链上

### Step 5. 接通 `AoA_dot / StallState / 最小 pitch break`

目标：

- `aero_state_system` 输出 `AoA_dot`
- `aerodynamics_system` 更新 `stall_state`
- 增加一个最小 `pitch_break` 力矩项

完成标准：

- 不追求高保真
- 只要求高攻角进入后能观测到更像样的恢复趋势

### Step 6. 新增 P0 测试并回归

目标：

- 补 `test_flight_dynamics_p0_runtime_guards.py`
- 跑现有 `test_flight_dynamics_realism_guards.py`

完成标准：

- P0 新测试通过
- 现有守门测试不被明显破坏

---

## 9. 开工注意事项

1. P0 的最大风险不是公式不够准，而是把状态分散在多个系统里，导致后面每加一项真实化都要返工。
2. `propulsion_system` 一定要先把“谁负责计算推力状态”这件事收清楚。
3. `stall_state` 一定要先进入可观测层，否则后面很难区分“真实恢复不足”和“只是控制器在压住症状”。
4. 所有 tuning 都必须允许 `disabled=false/true` 回退，确保能和现有训练主线并存。

---

## 10. P0 完成判据

满足以下条件即可认为 P0 完成：

1. `AeroTuning / EngineTuning / StallState / Propulsion state` 已进入仓库主结构。
2. `Force / Logistics / Instruments` 已基于同一推进状态链工作。
3. `AoA_dot` 与 `stall_state` 已可在运行测试中观测。
4. 新增最小 P0 守门测试通过。
5. 现有飞行动力学粗真实性守门测试未出现明显回归。

P0 完成后，P1 才适合继续推进：

- 更完整的压缩性修正
- 更细的失速/恢复曲线
- 机型化发动机推力表
- 更可信的 FBW 包线调度
