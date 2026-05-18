<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/naval/minimal_task_structure.md. Review before treating this file as authoritative. -->

# 海军最小任务结构

本说明固定了WP7支持的最小有用海军任务结构。

## 范围

这些规则故意狭窄。它们旨在支持早期的联合开发衔接，而不是完整的舰队运行时。

支持的起始任务形态：

- `TASK_SCREEN`
- `TASK_SUPPORT`
- `TASK_PATROL`
- `TASK_RECOVER`

## 最小结构规则

当 `tasking_profile = naval` 或 `service_profile = Navy` 时：

- `task_group_id` 是主要的最小组织锚点。
- `parent_node_id` 是下一个后备组织锚点。
- `officer_in_tactical_command` 默认为 `task_group_id`，然后为 `parent_node_id`。
- `tactical_unit_type` 在存在 `task_group_id` 时默认为 `CommandNode`。

## 最小语义映射

`TASK_SCREEN`

- `task_family = Escort`
- `coordination_mode = Screen`
- `warfare_role_code = ScreenCommander`
- `naval_station_type = Screen`

`TASK_SUPPORT`

- `task_family = Escort`
- `coordination_mode = Support`
- `warfare_role_code = LogisticsCoordinator`
- `naval_station_type = Support`

`TASK_PATROL`

- `task_family = Patrol`
- `warfare_role_code = SeaControlCommander`
- `naval_station_type = PatrolStation`

`TASK_RECOVER`

- `task_family = Recover`
- `coordination_mode = Detached`

## 非目标

本文件不定义：

- 舰队机动逻辑
- 驻泊保持控制器
- 海军特定任务指挥层级
- 补给运行时
- 完整的航母或水面行动工作流
