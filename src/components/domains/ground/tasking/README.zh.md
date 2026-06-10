# `src/components/domains/ground/tasking` 边界

本目录是早期 ground tasking DTO 的维护中 C++ owner-slice 归属点。它只覆盖
G0/G1 static task 与 status 基础设施。

## 允许

- `TaskOrderGround`、`LeaderIntentGround`、`PilotReportGround` owner slice。
- `GroundTaskMode`、`GroundStatusPhase` 这类 ground static task/status 枚举。
- objective/area 引用、static occupy/support task mode、tactical commander
  ID，以及 `1 Hz` tasking cadence baseline。
- 供 flat compatibility shell 与 maintained batch contract 使用的 projection
  helper。

## 禁止

- route movement、terrain passability、sensing、fires、damage、suppression、
  logistics 或 combat outcome 语义。
- ground-only runtime loop 或私有 command/status pipeline。
- Python binding 代码；binding 属于 `src/interfaces/python`。

## 当前切片

当前字段刻意保持静态：

- `ground_task_mode`
- `ground_status_phase`
- `objective_area_id`
- `objective_node_id`
- `ground_commander_id`
- `tactical_cadence_hz`
- `PilotReportGround` 上的 `readiness_ratio`

这些字段让 G0/G1 ground task/status chain 能被 C++ 和 Python 寻址，但不释放
G2 movement。
