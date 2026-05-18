<!-- Machine-translated draft generated on 2026-05-18 from docs/manual/physics_engine_inventory.md. Review before treating this file as authoritative. -->

# 物理引擎基础清单（已实现）

> 目标：把仓库里**已经存在且在仿真循环中真实生效**的“物理/飞行动力学”基础按模块梳理出来，并给出对应代码入口，便于后续与 RL 训练对接、逐步替换掉奖励黑客式学习。

---

## 1) 仿真循环与管线（ECS）

### 1.1 SimulationKernel：注册组件、系统与更新顺序

- `SimulationKernel::step()` 以固定步长 `dt` 执行 `ecs.progress(dt)`。
- 系统注册（默认按注册顺序执行）：  
  `CommandLink -> ActionMapping -> CommandLag -> Control -> Guidance -> Movement -> Sensor -> DataLink -> Damage -> EW -> Logistics`

入口：
- `src/core/engine/simulation_kernel.cpp`

### 1.2 运动积分：MovementSystem（Velocity -> Transform）

- 每帧做最基本的积分：`Transform += Velocity * dt`。
- 根据水平速度 `atan2(vy, vx)` 反推 `heading`（NAV：0=North，顺时针为正）。

入口：
- `src/systems/physics/movement_system.h`

---

## 2) 物理/控制相关组件（Components）

### 2.1 基础状态

- `Transform {x,y,z, heading,pitch,roll}`：局部 ENU 坐标 + 欧拉角
- `Velocity {vx,vy,vz}`：线速度（m/s）

入口：
- `src/components/basic/common.h`

### 2.2 指令链（用于把 RL / 上层指令落到控制模型）

- `ActionCommand`：RL 的归一化动作（`turn_rate_cmd/accel_cmd/climb_rate_cmd`）+ 武器/EW/通信触发字段
- `ActionSpaceConfig`：把归一化动作映射到物理量的尺度与边界（`max_turn_rate/max_accel/max_climb_rate`，速度/高度上下限）
- `MovementCommand`：
  - 自动驾驶目标：`target_heading/target_speed/target_altitude`
  - 直接杆舵覆盖：`use_stick_control + stick_roll/stick_pitch/throttle_cmd/gear_handle`
  - `active`：是否生效
- `CommandLag / LaggedCommand`：一阶滞后（避免“瞬时改变目标”）
- `CommandLink / Pending*`：指令链延迟与丢包（用于“长机/僚机/数据链”类场景）

入口：
- `src/components/physics/action.h`
- `src/systems/core/operation_system.h`
- `src/systems/systems/command_link_system.h`

### 2.3 平台性能/包线

- `FlightModel`：速度包线与机动能力（`max_speed/min_speed/max_turn_rate/max_accel/max_climb_rate/max_g/min_g`）  
  + 地面操作参数：`takeoff_speed/landing_speed/taxi_turn_rate`
- `LandingGear`：跑道/非铺装能力、滚阻、结构极限、收放状态

入口：
- `src/components/physics/performance.h`

### 2.4 动力/质量/后勤（与能量模型强相关）

- `Mass`：`empty/fuel/stores` 与 `get_total_kg()`（控制模型可读取总重）
- `Propulsion`：`mil/AB thrust` + 状态
- `FuelSystem`：燃油量、流量、AB 状态（由 LogisticsSystem 更新）
- `MassProperties`：空重、当前总重、`drag_index`（目前用于存储“阻力索引”，但参考面积等仍有硬编码）

入口：
- `src/components/physics/dynamics.h`
- `src/components/systems/logistics.h`
- `src/systems/systems/logistics_system.h`

---

## 3) 环境模型（大气/地形/地表）

### 3.1 大气（密度/风）

- `IEnvironmentModel::get_atmosphere_at(x,y,z)` 返回 `AtmosphericData`：`air_density/pressure/temperature/wind_velocity/...`

入口：
- `src/core/interfaces/environment_model.h`
- `src/components/basic/environment_data.h`
- `src/models/environment/default_environment_model.cpp`

### 3.2 地形与地表类型（跑道/滑行道/软土/水域）

- `IEnvironmentModel::get_terrain_at(x,y)` 返回 `TerrainCell`：`SurfaceType + friction_mult + roughness + runway_heading ...`
- 默认实现中包含：
  - 规则化跑道/停机坪“覆盖层”
  - 低分辨率栅格底图（HardPacked/SoftDirt）

入口：
- `src/core/interfaces/environment_model.h`
- `src/models/environment/default_environment_model.cpp`

---

## 4) 控制模型（ControlModel）与“物理”落点

### 4.1 ControlSystem：把命令喂给 ControlModel

- 优先级：`MovementCommand(use_stick_control=true)`（直接杆舵）优先于 `LaggedCommand`（自动驾驶目标）。

入口：
- `src/systems/physics/control_system.h`

### 4.2 DefaultControlModel：两条动力学路径

> 这是当前“物理是否真的生效”的核心：同样是飞机，走哪条控制路径，决定是否会出现不符合现实的轨迹（例如几乎原地竖直爬升）。

1) **Stick 控制路径（更接近“动力学”）**  
   - 读取 `Mass/Propulsion/LandingGear`，计算推力、阻力、简单重力项，更新速度矢量  
   - 地面与空中分支均有（起飞环境 `F16TakeoffEnv` 使用这一条）

2) **Autopilot 目标路径（RTS/点质量/运动学为主）**  
   - 目标来自 `ActionMapping -> MovementCommand -> CommandLag`  
   - 历史上存在“把速度几乎全部分配给 vz、vx≈0”的漏洞（已通过爬升角/垂速命令生成修复）
   - 当前含有阻力与简化能量项，但仍需要进一步把“能量守恒/推重比/阻力”真正用于限制爬升与加速（这也是后续与训练对接的重点）

入口：
- `src/models/air/default_control_model.cpp`

---

## 5) 数据来源（数据库）

### 5.1 飞机/发动机/气动参数

- 飞机单位（质量、参考面积/阻力系数、FlightModel 包线、起落架等）：  
  `examples/config/database/aircraft/units/*.json`
- 发动机模块（推力、SFC 等）：  
  `examples/config/database/aircraft/modules/engines/*.json`

### 5.2 工厂装配（把 JSON 变成 ECS 组件）

- `load_unit_definitions_json()` 解析 JSON 到 `UnitDefinition`
- `DefaultUnitFactory::spawn()` 将 `UnitDefinition` 装配成实体（写入 `FlightModel/Mass/Propulsion/FuelSystem/MassProperties/...`）

入口：
- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`

---

## 6) Python / RL 对接入口（当前训练实际用到的 API）

### 6.1 ef_py 接口（Gym 环境调用）

- `set_action(entity_id, turn, accel, climb, fire, ...)`：走 autopilot 目标链路
- `set_stick_command(entity_id, roll, pitch, throttle, gear_down)`：走 stick 路径
- `set_command(entity_id, heading, speed, alt)`：直接设置 MovementCommand 目标

入口：
- `src/interfaces/python/python_module.cpp`

### 6.2 训练环境（当前用法）

当前维护入口已经收敛到通用 env 与 batch runtime，而不是早期每个任务一个
`f16_*_env.py` 文件：

- `gym_envs/universal_env.py`：执行层单机环境入口；可通过 scenario 与
  action mode 覆盖 takeoff / cruise / landing / air-combat 等任务线。
- `gym_envs/leader_env.py`：长机/上层决策环境入口，通过 execution backend
  驱动底层飞行。
- `python/rl/runtime/world_batch_vec_env.py`：维护中的 execution-layer batch
  rollout 入口。
- `python/rl/runtime/cooperative_world_batch_vec_env.py`：多机协同 execution
  rollout 入口。

历史备注：早期文档和实验曾使用 `gym_envs/f16_takeoff_env.py`、
`gym_envs/f16_cruise_waypoint_env.py`、`gym_envs/f16_departure_waypoint_env.py`
和 `gym_envs/f16_landing_waypoint_env.py` 这类专用文件名。当前仓库中这些
不再是维护入口；如果旧报告提到它们，应按 legacy 线索理解。

入口：
- `gym_envs/universal_env.py`
- `gym_envs/leader_env.py`
- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`

---

## 7) 当前缺口（对训练最关键）

1) **Autopilot 分支仍然偏“运动学写速度”**：阻力/能量项存在，但需要与“爬升/加速分配”绑定，避免奖励诱导的非现实机动。
2) **Stick 分支动力学非常简化**：目前没有显式升力/迎角模型，速度矢量基本跟随机头方向，会导致“俯仰=直接改变飞行轨迹”的简化现象。
3) **后勤/燃油与推力/节流的一致性**：当前燃油消耗用 `ActionCommand.accel_cmd` 近似“油门”，与 autopilot 的 `target_speed` 逻辑存在不一致。

这些缺口决定了“奖励/惩罚”很容易被钻空子；因此更推荐把物理约束（能量守恒、包线、地面接触规则）落到控制模型里，让学习只能在合理轨迹空间里探索。
