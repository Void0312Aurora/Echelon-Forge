# `src/systems` 边界

`systems/` 保存 ECS system registration 和每 tick mutation 逻辑。这里的代码消费 `components/` 与 `models/`，并由 `core/engine` 注册和调度。

内置 component/system graph 的 owner-admission declaration 位于
`system_contribution_registry.h`；其 implementation 与 native kernel entry 位于
`core/engine`。package 或 discovery order 不得成为 Flecs execution order。

本层是 multi-domain aware，但成熟度不均：air execution 现在由 `domains/air` 显式拥有，
physics 保留共享 primitive，naval 的舰艇/潜艇和舰载航空 token system 位于
`domains/naval`，ground 只限 terrain/ground-contact primitive，不是 full land
movement、sensing、fires 或 damage runtime。

## 允许

- Flecs system/query 注册函数。
- 每 tick 对 ECS component 的更新逻辑。
- 调用 `models/` 中的可替换模型实现。
- 使用 `core/interfaces` 中的模型接口。
- 受限的 naval platform/runtime tick 和共享 ground-contact physics primitive。

## 禁止

- 定义新的 ECS component 或 command/tasking DTO。
- 拥有 world lifecycle、batch runtime、episode controller 或 facade。
- Python binding 或外部 API 适配。
- 读取训练配置、场景文件或直接管理多 world。
- movement/sensing/fires/damage ownership split 明确前的 native ground-domain runtime loop。

## 子目录约定

- `core/`：通用 operation / lifecycle system。
- `domains/`：域自有 runtime system。当前已有 `air/` 与 `naval/` owner；新增域 runtime owner 应放到这里，而不是继续摊到 `systems/` 根目录。
- `physics/`：force clear、force projection、integration、ground contact、instrument 等共享物理 primitive。
- `combat/`：伤害、制导和战斗效果系统。
- `systems/`：平台系统 runtime，例如 command link、data link、EW、logistics、navigation、sensor、track manager。
- `visual/`：视觉观测 system。

## 当前阅读入口

- [core/README.md](core/README.md)
- [domains/README.md](domains/README.md)
- [physics/README.md](physics/README.md)
- [combat/README.md](combat/README.md)
- [systems/README.md](systems/README.md)
- [visual/README.md](visual/README.md)

## 当前文件落点

- `core/`
  - `operation_system.h`
- `domains/`
  - `air/aero_state_system.h`, `air/aerodynamics_system.h`,
    `air/control_system.h`, `air/propulsion_system.h`
  - `naval/ship_motion_system.h`, `naval/submarine_motion_system.h`,
    `naval/embarked_air_ops_system.h`,
    `naval/naval_mission_weapon_release_system.h`,
    `naval/naval_logistics_system.h`
- `physics/`
  - `force_clear_system.h`, `force_system.h`, `ground_contact_system.h`
  - `instrument_system.h`, `leapfrog_system.h`, `movement_system.h`, `rotational_system.h`
- `combat/`
  - `damage_system_common.h`, `damage_system_air.h`, `damage_system_naval.h`, `damage_system_ground.h`
  - `guidance_system.h`, `pilot_weapon_release_system.h`
- `systems/`
  - `command_link_system.h`, `data_link_system.h`, `ew_system.h`
  - `logistics_system.h`, `navigation_system.h`, `sensor_system.h`, `sonar_system.h`, `track_manager_system.h`
- `visual/`
  - `visual_system.h`

## 迁移备注

`systems/systems` 命名过宽。新增平台系统可以暂放此目录，但应在下一轮重命名评估中收敛为更明确的业务名，例如 `systems/platform` 或 `systems/avionics`。
