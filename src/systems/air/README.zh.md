# `src/systems/air` 边界

`systems/air` 拥有 air-domain flight control、aerodynamic state、propulsion
state 以及 aerodynamic force/moment effect 的逐 tick runtime system。这里消费共享物理组件、
command bridge state 与 air-specific tuning/damage state，但这些系统本身不是共享物理 primitive。

## 允许

- 飞行器控制、推进、气动状态、升阻力和气动力矩更新。
- 消费 `components/air`、`components/physics` 以及维护中的 air command bridge。
- 直接影响飞行动力学的 air-specific damage effect。

## 禁止

- force clear、leapfrog integration、ground contact 等共享积分 primitive。
- naval 或 ground platform movement、sensing、fires、damage ownership。
- 定义 ECS component、command/tasking DTO、Python binding、facade 或 batch runtime owner。

## 当前文件

- [aero_state_system.h](aero_state_system.h)
  - 计算 air-relative AoA、sideslip、dynamic pressure 和 Mach state。
- [aerodynamics_system.h](aerodynamics_system.h)
  - 施加 air-domain lift、drag、aero moment、stall 和 aircraft damage effect。
- [control_system.h](control_system.h)
  - 将 flight command state 接入可替换 air control model。
- [propulsion_system.h](propulsion_system.h)
  - 推进 jet propulsion spool、thrust、afterburner 和 fuel-basis helper state。

## 兼容性

旧的 `systems/physics/*` air-system 头文件保留为 include-only wrapper。
新增代码应直接 include 本目录。
