# `src/components/command` 边界

`components/command` 是飞行员动作、任务命令、命令链路和 legacy 控制命令的归属目录。旧 `components/physics/action.h` 仍保留为 compatibility umbrella include。

和 tasking 一样，command 侧当前按 common foundation 加 domain extensions
说明，而不是 `air + ship` 二分法。`common` 承载跨域命令传输与共享执行意图，
`components/domains/<domain>/command` 承载各域扩展。ground movement、sensing、
fires、terrain 与 damage control 仍然 held。

## 允许

- `PilotAction` 及其 action-space 配置。
- `MissionCommand` 这类由上层任务或训练环境下发的执行命令 DTO。
- `MovementCommand`、`ActionCommand` 等 legacy command surface，但仅作为由显式 bridge seam 持有的 compatibility DTO。
- `CommandLink`、`CommandLag`、pending command 这类命令链路状态。

## 禁止

- `TaskOrder`、`LeaderIntent`、`PilotReport` 等 C2/tasking 状态；这些进入 `components/tasking`。
- 物理积分、控制律执行、传感器扫描或武器制导逻辑。
- JSON codec、episode transition、reward breakdown；这些属于 `core/mission`。
- Python binding 代码。

## 拆分方向

- `common command` 放跨域共享执行语义：例如 command transport、latency/drop、pending delivery，以及可复用于多个域的基础命令向量。
- `components/domains/air/command` 放当前明显航空化的执行面：现有 legacy flight control surface，以及带 route/recovery/takeoff/runway/formation 语义的 command 扩展。
- `components/domains/naval/command` 单独建模当前舰艇/海上执行 DTO slice，包括站位、舰载直升机发收舰、OTH relay 和 naval surface-engagement command code。不应把 air 的 heading/altitude/runway/recovery 组合直接泛化成 “ship command”。
- `components/domains/ground/command` 在 `MissionCommandGround` 中保存当前 static task metadata slice：objective/area 引用、static task mode、tactical commander ID 与 tactical cadence。在 ground schema/runtime owner 明确前，不要把 land movement/sensing/fires control 塞进 `common/`。

## `MissionCommand` 备注

`MissionCommand` 已完成 `common + air` 的第一阶段兼容拆分，但它仍然是 command 侧的高风险 consumer 汇聚点：

- 代码结构上，`mission_command.h` 现在只是兼容 umbrella，对外继续暴露 flat `MissionCommand`，底层已拆为 `common/mission_command_core.h` 与 `components/domains/<domain>/command/*`。
- 语义上，它依然深度耦合 air 执行面，并直接连到命令投递、mission episode 状态、mission runtime JSON codec、仪表/观测和 air control model。
- 因此后续工作应优先保持现有 flat 兼容层和 consumer 对称性，而不是在这一层贸然推进嵌套对象化或更广泛的领域执行拆分。

在代码层面，`CommandLink` 比 `MissionCommand` 更接近真正的共享核心；`MissionCommand` 目前仍更像“共享壳 + 大量 air 负载”。

## 依赖方向

command DTO 可以被 `systems/`、`core/engine`、`core/mission`、`runtime/facade` 和 `interfaces/python` 消费。它不反向依赖这些层。

maintained 的 air-control consumer 必须通过
`components/domains/air/command/control_input_resolution.h` 解析 legacy command fallback，不允许在各个
maintained system 内部继续手写 `MovementCommand`/`ActionCommand` 探测逻辑。

当前允许继续依赖 `legacy_command.h` 的显式 compatibility seam：

- `src/components/command/legacy_command_bridge.h`
- `src/systems/core/operation_system.h`
- `src/systems/systems/command_link_system.h`
- 其余由 architecture test 标注的 compatibility-only 或仍待迁移 consumer

## 迁移备注

已落地：

- `pilot_action.h`
- `mission_command.h`
- `command_link.h`
- `legacy_command.h`
- `components/domains/air/command/mission_command_air.h`
- `components/domains/naval/command/mission_command_naval.h`
- `components/domains/ground/command/mission_command_ground.h`

WP0 文档口径：

- 优先把真正共享的 command transport / base intent 识别出来。
- air 特有语义已从共享层中剥离到 `MissionCommandAir`，但当前仍保持 flat 兼容外壳。
- naval-specific command 语义已落到 `MissionCommandNaval`，不使用 “air + ship” 二分法。
- ground command 现在已有维护中的 static task metadata owner slice；route movement、terrain、sensing、fires、damage 与 combat command 语义仍 held。

新代码应 include 具体头文件，不应继续依赖 `components/physics/action.h`。
