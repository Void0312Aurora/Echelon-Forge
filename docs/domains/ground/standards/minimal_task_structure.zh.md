# Ground 最小任务结构

语言：[英文规范页](minimal_task_structure.md)；本页为中文配套。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/minimal_task_structure.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

## 范围

本标准定义已经实现的 G0/G1 静态 Ground task/status 合同。它覆盖 profile
路由、三个已准入起始任务名、对应 common-core 默认值、Ground 自有静态字段，
以及向 `MissionCommandGround` 的投影。

它不释放 movement、terrain、sensing、fires、damage、logistics 或 Ground
execution system。

## Profile 与 Common 默认值

当显式 tasking profile 是 `army`、`ground` 或 `land`，或者 service profile
为 `ServiceProfile.Army` 且不存在冲突的显式 tasking profile 时，维护中的
tasking 路由是 `ground`。

所有已准入起始任务默认采用：

- `service_profile = Army`
- `tactical_unit_type = TacticalUnit`
- `authority_scope = Tactical`
- 以 platoon 为中心的第一波解释；更高 echelon 保持为 scenario 或 tasking
  metadata，而不是独立 tight-loop runtime owner

显式 tasking profile 的优先级高于推断的 service profile。未知显式 profile
名称必须 fail closed。

## 已准入起始任务

维护中的静态合同只准入以下起始任务名：

| Task name | `TaskFamily` | `GroundTaskMode` | 默认 relationship | 默认 coordination | 派生 status phase |
| --- | --- | --- | --- | --- | --- |
| `TASK_MOVE` | `Transit` | `MoveStatic` | `TACON` | `Independent` | `HoldingStatic` |
| `TASK_OCCUPY` | `Defend` | `OccupyStatic` | `TACON` | `Independent` | `OccupyingStatic` |
| `TASK_SUPPORT` | `Defend` | `SupportStatic` | `Support` | `Support` | `SupportingStatic` |

这些映射描述当前代码。当前 common `TaskFamily` enum 不含 `Maneuver` 或 Ground
专属 `Support` family：`TASK_MOVE` 映射到 `Transit`，`TASK_OCCUPY` 和
`TASK_SUPPORT` 映射到 `Defend`。支援差异通过
`CommandRelationship.Support`、`CoordinationMode.Support`、support ID 和
`GroundTaskMode.SupportStatic` 保留。

`MoveStatic` 是静态 task/status code，不得被引用为 route traversal 或
movement-dynamics 证据。

`TASK_SCREEN`、`TASK_SECURE`、`TASK_PATROL`、`TASK_DIRECT_FIRE`、
`TASK_INDIRECT_FIRE` 和 `TASK_SUSTAIN` 等其他候选名均未被本标准准入。
它们必须先具备独立语义和已接受的标准更新，才能成为 Ground 默认值或必需
profile output。

## Ground 自有静态字段

Ground owner slice 承载以下已接受字段：

- `ground_task_mode`
- status-bearing DTO 上的 `ground_status_phase`
- `objective_area_id`
- `objective_node_id`
- `ground_commander_id`
- `tactical_cadence_hz`
- `PilotReportGround` 上的 `readiness_ratio`

维护中的 tasking cadence 默认值是 `1 Hz`。

`TaskOrderGround`、`LeaderIntentGround` 和 `PilotReportGround` 拥有静态
task/status 字段。`MissionCommandGround` 是静态 task metadata 已接受的
command-side carrier。Flat `TaskOrder`、`LeaderIntent`、`PilotReport` 和
`MissionCommand` 结构继续作为投影这些 owner slice 的兼容 shell。

## 标识符与关系规则

- `parent_node_id` 是 command hierarchy fallback。
- `supported_node_id` 和 `supporting_node_id` 表达 support relationship。
- `task_group_id` 是可选共享组织挂点，不是主要 land task owner。
- 对 `TASK_SUPPORT`，supported node 是 objective-area 与 objective-node 的优先
  fallback，command hierarchy 提供 Ground commander fallback。
- 合法的显式字段必须优先于推断默认值。

## 场景证据边界

当前场景集证明两个有限表面：

- compatibility-shell fixture 在保留已声明非原生 spawn 边界的同时，验证归一后的
  Ground tasking 和静态 status propagation；
- `ground_platoon_native_static_occupy_v1` 验证原生 `Ground_Platoon_MVP`
  加载以及 Army/Ground `TASK_OCCUPY` 静态链。

这些 fixture 可以证明 `TaskOrder -> LeaderIntent -> PilotReport` 传播和
`MissionCommandGround` 静态投影。它们不得被作为 occupy geometry、route
movement、terrain effect、sensing、fires、damage 或 combat behavior 证据。

## Held 边界

以下内容仍不属于本任务合同：

- route following 与 movement dynamics；
- terrain traversal、masking、cover、concealment、obstacle 与 breach logic；
- Ground sensing、track fusion、shared-picture transport 与 observation export；
- direct fire、indirect fire、effects、damage、suppression 与 attrition；
- logistics、sustainment 与 recovery behavior；
- 正式 Ground `CommandPacket`、`ObservationPacket` 或 `TrackPacket` 特化。

## 验证

- [Ground profile 实现](../../../../python/rl/profile/ground_profile.py)
- [Tasking profile bridge](../../../../python/rl/tasking/bridge.py)
- [Ground task/status enum](../../../../src/components/domains/ground/tasking/ground_tasking_enums.h)
- [Ground command owner slice](../../../../src/components/domains/ground/command/mission_command_ground.h)
- [Tasking profile 合同测试](../../../../tests/leader/test_tasking_profile_contracts.py)
- [Ground tasking component 边界测试](../../../../tests/architecture/ground/test_tasking_component_boundary.py)
- [Ground runtime lifecycle bridge 测试](../../../../tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py)

## 相关文档

- [Ground owner 总览](../README.zh.md)
- [Ground 特化基线](specialization_baseline.zh.md)
- [Joint command 与 modeling 基线](../../joint/standards/command_and_modeling_baseline.zh.md)
