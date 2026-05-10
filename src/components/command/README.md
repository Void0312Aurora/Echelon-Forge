# `src/components/command` 边界

`components/command` 是飞行员动作、任务命令、命令链路和 legacy 控制命令的归属目录。旧 `components/physics/action.h` 仍保留为 compatibility umbrella include。

## 允许

- `PilotAction` 及其 action-space 配置。
- `MissionCommand` 这类由上层任务或训练环境下发的执行命令 DTO。
- `MovementCommand`、`ActionCommand` 等 legacy command surface。
- `CommandLink`、`CommandLag`、pending command 这类命令链路状态。

## 禁止

- `TaskOrder`、`LeaderIntent`、`PilotReport` 等 C2/tasking 状态；这些进入 `components/tasking`。
- 物理积分、控制律执行、传感器扫描或武器制导逻辑。
- JSON codec、episode transition、reward breakdown；这些属于 `core/mission`。
- Python binding 代码。

## 依赖方向

command DTO 可以被 `systems/`、`core/engine`、`core/mission`、`runtime/facade` 和 `interfaces/python` 消费。它不反向依赖这些层。

## 迁移备注

已落地：

- `pilot_action.h`
- `mission_command.h`
- `command_link.h`
- `legacy_command.h`

新代码应 include 具体头文件，不应继续依赖 `components/physics/action.h`。
