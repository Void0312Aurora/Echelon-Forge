# `src/components/tasking` 边界

`components/tasking` 是编队、任务分配、leader intent、pilot report 和 C2 状态 DTO 的归属目录。它描述“意图与任务状态”，不描述底层飞行动作如何被物理系统执行。

## 允许

- `TaskType`、`LeaderPhase`、`ServiceProfile` 等 tasking enum。
- `TaskOrder`、`LeaderIntent`、`PilotReport`。
- 可被 mission runtime、facade、Python binding 读写的轻量任务状态。

## 禁止

- `PilotAction`、`MissionCommand`、`CommandLink` 和 legacy movement/action command；这些进入 `components/command`。
- waypoint transition、landing transition 或任务 JSON 解释逻辑；这些属于 `core/mission`。
- 物理控制、传感器、武器、数据链 tick 逻辑。
- Python binding 代码。

## 依赖方向

tasking DTO 位于数据层。`core/mission` 可以解释它，`systems/` 可以消费它，`runtime/facade` 可以批量设置和导出它，但它不能依赖这些上层。

## 迁移备注

已落地：

- `tasking_enums.h`
- `task_order.h`
- `leader_intent.h`
- `pilot_report.h`

旧 `components/physics/action.h` 已降级为 compatibility umbrella include。新代码应 include 具体头文件。
