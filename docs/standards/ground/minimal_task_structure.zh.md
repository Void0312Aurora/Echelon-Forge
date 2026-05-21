# Ground 最小任务结构

Language:
- 英文主文：`minimal_task_structure.md`
- 中文辅文：[minimal_task_structure.zh.md](minimal_task_structure.zh.md)

状态：`2026-05-21` G0 最小 tasking 基线。

本说明冻结 G1 工作必须遵守的最小有用 ground tasking 结构。

它刻意保持狭窄。它要表达的是：在 runtime 行为实现前，共享合同、Army
service profile 与专门的 `ground` 层之间最小需要接上的语义。

## 范围

支持的起始任务形态：

- `TASK_MOVE`
- `TASK_OCCUPY`
- `TASK_SUPPORT`

这三项是 G0 唯一的起始任务形态。它们是第一批 ground-domain tasking 计划所需
的最小入口，不需要先引入 air sortie 语言、naval station-keeping 语义，或尚未
冻结的 ground execution surface。

延后的任务形态：

- `TASK_SCREEN`
- `TASK_SECURE`
- `TASK_PATROL`
- `TASK_DIRECT_FIRE`
- `TASK_INDIRECT_FIRE`
- `TASK_SUSTAIN`

这些延后形态都是合理的 ground task 候选，但它们需要比 G0 更多的 mobility、
sensing、fires 或 sustainment 语义。
在后续 accepted plan 提升它们之前，它们不得被视为 first-wave task order、
enum default 或必需的 profile output。

## 分层结构规则

当 `tasking_profile = ground`、`tasking_profile = land` 或
`service_profile = Army` 时：

- 归一后的维护 profile 是 `ground`
- `tactical_unit_type` 在第一 maintained 切片中默认指向 platoon-centered tactical unit
- `parent_node_id` 是优先的 command-hierarchy 锚点
- `supported_node_id` 与 `supporting_node_id` 表达 support relationship
- `task_group_id` 仍是共享的可选组织挂点，不是 land task 的主要所有者
- company、battalion、brigade、division 与 corps 可作为 scenario 或 tasking
  metadata 存在，但第一批 tight-loop task owner 以 platoon 为中心

## 最小语义映射

ground specialization 吸收的最小语义集是：

- `ground`
- `platoon`
- `move`
- `occupy`
- `support`
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`

### `TASK_MOVE`

- 语义：让以 platoon 为中心的单位向 route、phase line 或 objective reference 机动
- 当 `Maneuver` enum 存在时，`task_family = Maneuver`；否则使用最接近的通用 route/movement family，并把 ground-specific meaning 保留在 tasking profile
- 预期 owner：以 platoon 为中心的 tactical unit；更高 echelon 仍是 scenario 或 tasking metadata
- 默认 `coordination_mode = Independent`，除非声明 support relationship
- `parent_node_id` 是 command owner fallback
- `supported_node_id / supporting_node_id` 可选
- precise route traversal、movement dynamics、terrain interaction、sensing cadence 与 execution command surface 延后

### `TASK_OCCUPY`

- 语义：移动到并保持一个 ground objective、battle position 或 named area
- 当 `Maneuver` enum 存在时，`task_family = Maneuver`；否则使用最接近的通用 task family，并在 ground profile 中保留 `occupy` 语义
- 预期 owner：以 platoon 为中心的 tactical unit；此任务不会把 company、battalion、brigade、division 或 corps 提升为 tight-loop owner
- 默认 `coordination_mode = Independent`
- `parent_node_id` 是 command owner fallback
- occupation 只是 tasking intent；terrain realism、cover、concealment、obstacle/breach behavior、damage effects 与 detailed occupation geometry 延后

### `TASK_SUPPORT`

- 语义：以 supporting relationship 支援另一个 ground unit 或 task node
- 当 `Support` enum 存在时，`task_family = Support`；否则使用具备支援含义的通用 family，并在 tasking profile 中保留 ground-specific meaning
- `coordination_mode = Support`
- 已知时，`supporting_node_id` 应标识支援单位
- 已知时，`supported_node_id` 应标识被支援单位或任务节点
- support 只表达 relationship 与 intent；fires、sustainment、logistics-specific behavior、damage effects、observation export 与 track fusion 延后

## Agency 默认值

第一版 ground tasking profile 应识别这些 role 默认值：

| Role | Authority scope | Typical task responsibility |
|------|-----------------|-----------------------------|
| `ground_squad_leader` | squad | 执行已分配的 move/occupy/support task |
| `ground_platoon_commander` | platoon | 拥有第一波 tasking 与 delegation |
| `ground_company_commander` | company | 协调 platoon；runtime coordination 延后 |

## Information 默认值

第一版 ground tasking profile 应假设：

- ground sensing 受 terrain masking 与 line-of-sight 约束
- shared tactical picture 受 radio range 与 relay topology 约束
- maintained ground policy 不应直接消费 world truth
- formal `ObservationPacket` 与 `TrackPacket` surface 延后

## Clock 默认值

第一版 ground tasking profile 应假设：

- 基础战术评估节奏：`1 Hz`
- movement 与 sensing cadence：延后
- 后续任何低频 ground update 仍必须进入共享 causal-temporal scheduler 与 evidence model

## 延后真实性护栏

G0 起始 tasking 不得要求维护以下实现：

- observation export 或 track fusion
- movement dynamics 或 route traversal
- direct fires 或 indirect fires
- logistics、sustainment 或 recovery flow
- damage、effects、suppression 或 attrition behavior
- terrain traversal、cover、concealment、obstacles 或 breach realism

这些主题仍是有效的未来 ground 工作，但不属于 G0 最小任务词汇。

## 非目标

本文件不定义：

- ground movement dynamics
- terrain traversal、cover、concealment 或 breach behavior
- direct-fire 或 indirect-fire runtime
- logistics 或 sustainment runtime
- ground-specific `MissionCommand` 字段
- observation export schema
- damage 或 effects behavior

它存在的目的是冻结最小有用合同，而不是描述完整 land warfare model。
