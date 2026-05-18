# 海军最小任务结构

本说明冻结当前运行时与任务计划必须支持的最小有用海军任务结构。

它仍然足够狭窄，但不再只是泛泛的占位说明。它要表达的是：共享合同、Navy service profile 与专门的 `naval` 层之间最小需要接上的语义。

## 范围

支持的起始任务形态：

- `TASK_SCREEN`
- `TASK_SUPPORT`
- `TASK_PATROL`
- `TASK_RECOVER`

这些是当前海上任务计划所需的最小入口，不需要先引入空军式编队语言。

## 分层结构规则

当 `tasking_profile = naval` 或 `service_profile = Navy` 时：

- `task_group_id` 是主要组织锚点。
- `parent_node_id` 是下一个后备组织锚点。
- `task_group` 是拥有任务的海军任务编组。
- `task_unit` 是该任务编组内的下级战术单元。
- `officer_in_tactical_command` 默认指向 `task_group` 所有者，然后回退到 `parent_node_id`。
- `tactical_unit_type` 仍是共享类型标签；当任务由编组拥有时，可继续默认为 `CommandNode`。

## 最小语义映射

海军 specialization 吸收的最小语义集是：

- `warfare_role_code`
- `officer_in_tactical_command`
- `screen`
- `support`
- `station`
- `recover`

### `TASK_SCREEN`

- `task_family = Escort`
- `coordination_mode = Screen`
- `warfare_role_code = ScreenCommander`
- `naval_station_type = Screen`
- `officer_in_tactical_command` 是承担 screen 的任务编组或任务单元。

### `TASK_SUPPORT`

- `task_family = Escort`
- `coordination_mode = Support`
- `warfare_role_code = SupportCoordinator`
- `naval_station_type = Support`
- `officer_in_tactical_command` 是承担 support 的任务编组或任务单元。

### `TASK_PATROL`

- `task_family = Patrol`
- `warfare_role_code = SeaControlCommander`
- `naval_station_type = PatrolStation`
- `officer_in_tactical_command` 是承担 patrol 的任务编组或任务单元。

### `TASK_RECOVER`

- `task_family = Recover`
- `coordination_mode = Recover`
- `warfare_role_code = RecoverCoordinator`
- `naval_station_type = Recover`
- `officer_in_tactical_command` 是承担 recovery 的任务编组或任务单元。

## 语义说明

- `screen` 表示围绕高价值力量的保护性位置部署。
- `support` 表示保障、护航或支援关系。
- `station` 表示需要保持或恢复的相对站位。
- `recover` 表示回收或返回控制语义，包括舰载航空器回收等场景。

## 非目标

本文件不定义：

- 舰队机动逻辑
- 驻站保持控制器
- 海军特定任务指挥层级的完整细化
- 补给运行时
- 完整的航母或水面行动工作流

它存在的目的是冻结最小有用合同，而不是描述完整 doctrine。
