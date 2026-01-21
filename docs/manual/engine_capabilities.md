# 当前引擎能力说明（更新版）

你现在拥有的是一个基于 **ECS（flecs）** 的仿真内核，整体仍属于 MVP 级别，但已经包含了“可用于训练”的物理/控制/传感器等基础模块。下面描述以“当前仓库实现”为准。

## 1) 核心能力（现在能做什么）

### A. 固定步长仿真循环 + 可复现性
- 固定 `dt` 推进世界（默认 60Hz），支持 reset seed 复现实验。
- 系统管线有明确顺序：指令链/动作映射/滞后/控制/运动积分/传感器/伤害/EW/后勤等。

### B. 单位装配（数据库 -> 组件）
- 支持从 `examples/config/database` 的 JSON 装配单位（飞机/导弹/平台模块等）。
- 关键组件包括：`Transform/Velocity/FlightModel/LandingGear/Mass/Propulsion/FuelSystem/...`

### C. 运动与控制（关键）
- **MovementSystem**：对 `Velocity` 做积分更新位置与航向。
- **ControlModel（DefaultControlModel）**：
  - 支持两类控制输入：  
    1) **autopilot 目标控制**：目标航向/速度/高度（RL 巡航/航路点任务使用）  
    2) **stick 直接控制**：roll/pitch/throttle/gear（RL 起飞任务使用）
  - 含地面逻辑：跑道/滑行道速度限制、非铺装/水面判断、滚阻/制动等（用于 crash 判定与地面运动）

### D. 环境（基础版）
- 大气：温度/气压/密度/风（ISA 简化）
- 地形/地表：跑道/滑行道/软土/水域等 SurfaceType，提供摩擦与跑道航向信息

### E. 感知/交战（基础版）
- 传感器系统：扫描与 track 记忆、接入 `SensorModel`
- 武器/制导/伤害/EW/数据链：存在基础系统与组件，适合后续扩展战术层训练

## 2) 关键局限（对“训练学歪”最敏感的部分）

- **飞行动力学仍然是简化点质量/包线模型**：没有完整 6DoF、升力/迎角/稳定性导数等；部分路径属于“运动学写速度”，需要用能量守恒/推阻比等约束来缩小可探索空间。
- **后勤与节流一致性仍需加强**：燃油消耗目前用动作近似“油门”，与 autopilot 的目标速度控制并不完全一致。
- **环境/地形仍是程序化简化**：适合 RL 初期训练，但距离真实机场/地形仍有差距。

## 3) 与 RL 的接口（现成）

- `ef_py.SimulationKernel.set_action(...)`：归一化 autopilot 动作（turn/accel/climb）
- `ef_py.SimulationKernel.set_stick_command(...)`：直接杆舵（roll/pitch/throttle/gear）

更详细的“物理引擎基础清单”见：`docs/manual/physics_engine_inventory.md`。
