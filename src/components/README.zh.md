# `src/components` 边界

`components/` 只保存 ECS 组件、轻量值类型和稳定的类 DTO 结构体。这里的类型可以被 `systems/`、`core/`、`runtime/facade` 和 `interfaces/python` 读取或绑定，但不应拥有运行时编排逻辑。

当前 component surface 是多域口径，而不是 flight-only：air 仍是最完整的执行面，naval 已有维护中的平台组件与 command/tasking DTO slice，ground 只通过共享类型、terrain、ground-contact primitive 和 typed setup evidence 表达。不要把这些 ground-aware primitive 当作完整陆域 component model。

## 允许

- 纯数据字段、默认值和轻量枚举。
- 与 ECS storage 直接对应的状态组件。
- 跨层传递但不执行业务流程的 command/tasking DTO。
- 不依赖 Flecs world 的小型辅助方法。

## 禁止

- system 注册、逐轮更新逻辑、物理积分或 mission 状态机。
- Python/nanobind 绑定辅助代码。
- `SimulationKernel`、`WorldBatchRuntime`、`RuntimeFacade` 相关控制逻辑。
- 需要读取数据库、加载场景或访问运行时所有者的逻辑。

## 子目录约定

- `basic/`：基础实体标签、阵营、位置、环境数据等底层组件。
- `domains/`：各域自有 component slice。当前已有 `air/`、`naval/`、`ground/`；新增域应放到这里，而不是继续摊到 `components/` 根目录。
- `combat/`：health、scoring 和共享 weapon/damage primitive 等跨域战斗状态。域专属 combat component 放在 `domains/<domain>/combat/`。
- `physics/`：共享物理状态、动力学、力、仪表、性能状态和当前 ground-contact primitive。
- `systems/`：通信、数据链、传感器、声呐、电子战、导航、后勤等跨域平台系统状态组件。
- `visual/`：视觉传感器输入输出状态。
- `command/`：共享 command shell、command link、legacy command DTO 与 command common foundation。域专属 command component 放在 `domains/<domain>/command/`。
- `tasking/`：共享 tasking shell 与 common C2/tasking foundation。域专属 tasking component 放在 `domains/<domain>/tasking/`。

## 当前阅读入口

- [basic/README.md](basic/README.md)
- [domains/README.md](domains/README.md)
- [combat/README.md](combat/README.md)
- [physics/README.md](physics/README.md)
- [systems/README.md](systems/README.md)
- [visual/README.md](visual/README.md)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## 当前文件落点

- `basic/`
  - `common.h`, `environment_data.h`, `tags.h`
- `domains/`
  - `air/platform/flight_dynamics_tuning.h`
  - `air/combat/damage_air.h`, `air/combat/weapon_air.h`
  - `air/command/mission_command_air.h`, `air/command/control_input_resolution.h`
  - `air/tasking/air_tasking_enums.h`, `air/tasking/task_order_air.h`,
    `air/tasking/leader_intent_air.h`, `air/tasking/pilot_report_air.h`
  - `naval/platform/ship_platform.h`, `naval/platform/submarine_platform.h`,
    `naval/platform/embarked_air_ops.h`
  - `naval/combat/damage_naval.h`, `naval/combat/weapon_naval.h`
  - `naval/command/mission_command_naval.h`
  - `naval/tasking/naval_tasking_enums.h`, `naval/tasking/task_order_naval.h`,
    `naval/tasking/leader_intent_naval.h`, `naval/tasking/pilot_report_naval.h`
  - `ground/combat/damage_ground.h`, `ground/combat/weapon_ground.h`
  - `ground/command/mission_command_ground.h`
  - `ground/tasking/ground_tasking_enums.h`, `ground/tasking/task_order_ground.h`,
    `ground/tasking/leader_intent_ground.h`, `ground/tasking/pilot_report_ground.h`
- `combat/`
  - `common/damage_common.h`, `common/weapon_common.h`
  - `health.h`, `scoring.h`
- `physics/`
  - `dynamics.h`, `forces.h`, `instruments.h`, `performance.h`, `control_law.h`, `propulsion_readouts.h`
  - `action.h` 仅保留 command/tasking compatibility umbrella 入口
- `systems/`
  - `comm.h`, `data_link.h`, `ew.h`, `logistics.h`, `navigation.h`, `sensor.h`, `sonar.h`, `track_management.h`
- `visual/`
  - `visual_sensor.h`
- `command/`
  - `pilot_action.h`, `mission_command.h`, `command_link.h`, `legacy_command.h`
  - `common/mission_command_core.h`, `common/comm_message.h`
- `tasking/`
  - `task_order.h`, `leader_intent.h`, `pilot_report.h`, `tasking_enums.h`
  - `common/*` 保存共享 C2/tasking foundation
  - `domains/ground/*` 目前仍局限于 G0/G1 tasking/status 与 native schema boundary 字段；land movement、sensing、fires、damage、terrain 和 combat runtime 仍保持 held。

## 迁移备注

当前 `physics/action.h` 同时承载 command 与 tasking 类型。新增共享 command/tasking 类型应进入 `components/command` 或 `components/tasking`；域专属扩展应进入 `components/domains/<domain>/{command,tasking}`。不要继续扩展 `components/physics/action.h`。
