<!-- Machine-translated draft generated on 2026-05-18 from src/components/README.md. Review before treating this file as authoritative. -->

# `src/components` 边界

`components/` 只保存 ECS component、轻量值类型和稳定 DTO-like struct。这里的类型可以被 `systems/`、`core/`、`runtime/facade` 和 `interfaces/python` 读取或绑定，但不应拥有运行时编排逻辑。

## 允许

- 纯数据字段、默认值、轻量 enum。
- 与 ECS storage 直接对应的状态组件。
- 跨层传递但不执行业务流程的 command/tasking DTO。
- 不依赖 Flecs world 的小型 helper 方法。

## 禁止

- system registration、tick/update、physics integration 或 mission state machine。
- Python/nanobind 绑定 helper。
- `SimulationKernel`、`WorldBatchRuntime`、`RuntimeFacade` 相关控制逻辑。
- 需要读取数据库、加载场景或访问 runtime owner 的逻辑。

## 子目录约定

- `basic/`：基础实体标签、阵营、位置、环境数据等底层 component。
- `combat/`：伤害、生命值、武器挂载、评分等战斗状态 component。
- `physics/`：物理状态、动力学、力、仪表和性能状态。
- `systems/`：通信、数据链、传感器、电子战、导航、后勤等平台系统状态 component。
- `visual/`：视觉传感器输入输出状态。
- `naval/`：舰艇、潜艇和舰载航空运作的 naval platform 状态 component。
- `command/`：目标目录，用于 pilot action、mission command、command link 和 legacy command DTO。
- `tasking/`：目标目录，用于 task order、leader intent、pilot report 和 C2/tasking enum。

## 当前阅读入口

- [basic/README.md](basic/README.md)
- [combat/README.md](combat/README.md)
- [physics/README.md](physics/README.md)
- [systems/README.md](systems/README.md)
- [visual/README.md](visual/README.md)
- [naval/README.md](naval/README.md)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## 当前文件落点

- `basic/`
  - `common.h`, `environment_data.h`, `tags.h`
- `combat/`
  - `damage.h`, `health.h`, `scoring.h`, `weapon.h`
- `physics/`
  - `dynamics.h`, `forces.h`, `instruments.h`, `performance.h`, `control_law.h`
  - `action.h` 仅保留兼容 umbrella 角色
- `systems/`
  - `comm.h`, `data_link.h`, `ew.h`, `logistics.h`, `navigation.h`, `sensor.h`, `track_management.h`
- `visual/`
  - `visual_sensor.h`
- `naval/`
  - `ship_platform.h`, `submarine_platform.h`, `embarked_air_ops.h`
- `command/`
  - `pilot_action.h`, `mission_command.h`, `command_link.h`, `legacy_command.h`
  - `common/mission_command_core.h`, `common/comm_message.h`
  - `air/mission_command_air.h`, `air/control_input_resolution.h`
  - `naval/mission_command_naval.h`
- `tasking/`
  - `task_order.h`, `leader_intent.h`, `pilot_report.h`, `tasking_enums.h`
  - `common/*`、`air/*`、`naval/*` 为分层后的子域入口

## 迁移备注

当前 `physics/action.h` 同时承载 command 与 tasking 类型。新增 command/tasking 类型应进入 `components/command` 或 `components/tasking`，不要继续扩展 `components/physics/action.h`。
