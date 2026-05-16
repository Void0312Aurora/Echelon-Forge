# P8 协同执行管线发现与计划

状态：进行中，记录 `2026-05-11` 的设施盘点、设计约束、已验证前置结论与下一批工作切口。

文档定位：

- 本文档不是新的重构授权单，而是 P8 协同训练方向的发现记录与执行前计划。
- 目标是复用既有 runtime / batch / leader-tasking 设施，避免把“双机”做成新的专用孤岛。
- 本文档中的 P8 第一阶段只把双机巡航作为最小验收场景；实现形态必须面向 `N` 个同 world 可控平台。

## 一、核心结论

P8 不应新建一条只服务 `TwoShipEnv` 的专用管线。

当前项目已经具备协同执行所需的大部分底座：

- `RuntimeFacade` / `WorldBatchRuntime` 已经以 `WorldEntityRef(world_index, entity_id)` 为批量访问单位。
- batch runtime 已支持对任意实体批量写入 `PilotAction`、`MissionCommand`、`TaskOrder`、`LeaderIntent`、`PilotReport`。
- batch runtime 已支持对任意实体批量读取 `AgentObservation`、`InstrumentState` 与 command/tasking/report 对象。
- `ScenarioRuntime` 已能在同一 world 中 spawn 多实体，并保留 `entities: name -> entity_id` 映射。
- `ScriptedC2TaskManager` / `RuleBasedLeaderPhaseManager` 已经提供脚本化任务/长机层基础。
- `LeaderBatchedVecEnv` 与 `LeaderWorldBatchExecutionRuntimeGroup` 已经验证过“高层窗口 + 批量执行策略推理 + shared WorldBatchRuntime”的调度思想。

真正缺口在 Python 训练/环境包装层：

- 现有 `UniversalEnv` / `WorldBatchVecEnv` 主要按“每个 world 一个 `agent_id`”组织执行训练。
- 现有 observation builder 以单 agent 为中心，尚未把同 world 内的多个可控成员组织成同一协同批。
- 现有训练入口只有 `execution` / `leader` 两类 `agent_layer`，尚未显式表达“同 world 多实体协同执行”。

因此 P8 第一刀应该补的是：

```text
同一 world 内多可控实体的 roster / refs / observation / action 映射层
```

而不是新增一个双机专用环境。

## 二、设计边界

### 2.1 长机层不是长机飞机

本项目中的“长机层 / element lead layer”是战术意图生成层，不等同于 lead aircraft 的飞行执行。

正确链路是：

```text
C2 / TaskOrder
  -> Coordination Director / Element Lead Layer
  -> per-platform LeaderIntent / MissionCommand
  -> per-platform execution policy
  -> PilotAction
  -> WorldBatchRuntime step
```

因此：

- 长机层可以脚本化。
- lead aircraft 本身仍应由执行层 policy 或执行控制器飞行。
- wingman 也由同一执行层管线飞行。

### 2.2 双机只是 `N=2`

P8 第一阶段用双机巡航验收，但接口不应出现只适配双机的硬编码。

推荐抽象：

- `world_index`
- `entity_id`
- `entity_name`
- `team_id` / `element_id`
- `role_code`
- `formation_role_id`
- `relative_slot_code`
- `reference_entity_name` / `reference_entity_id`
- `policy_route`

双机是一个 element 的两个成员；四机是更多 roster 成员与更多 slot assignment。

这些字段属于 roster / routing / logging 元数据，不等价于 execution policy 输入。P8-A 不应因为共享模型方便而把它们直接塞进执行层观测。

### 2.3 策略管线优先于共享模型

共享执行模型是策略路由的一种配置，不是 P8 的核心目标。

同一管线应支持：

- 所有成员共享一个 execution policy。
- 按 role 使用不同 policy。
- 某些成员脚本化，某些成员 RL。
- 后续把脚本化 coordination director 替换成 RL 或规划器。

### 2.4 观测必须遵守现实可获得原则

执行层输入的唯一准入标准是：现实中飞行员能够通过简令、座舱仪表、任务系统、无线电、目视、雷达、IRST、RWR 或数据链接收到。

训练便利性、共享模型便利性、reward 计算便利性、调试便利性都不能成为 policy 输入字段的准入理由。执行层 policy 不是仿真 kernel 的观察者，也不是训练器内部状态的消费者。

允许进入 policy 的信息应能解释为：

- 自身座舱/仪表可见。
- mission computer / 数据链 / 无线电收到的任务或编队指令。
- 已分配的队形阵位与任务简令。
- 对友机的目视、传感器或数据链可获得相对信息。

不可直接进入 policy：

- 无条件全局真值坐标与速度。
- reward 内部使用的完美误差。
- 未来指令、脚本内部状态、训练器特权状态。
- 未经过传感器/数据链/任务系统建模的其他平台状态。
- 只为区分共享模型分支而设计、但飞行员现实中不会以该形式接收的工程标签。

## 三、已有设施盘点

### 3.1 C++ runtime / facade

可复用设施：

- `RuntimeFacade`
  - `set_pilot_actions_batch`
  - `set_mission_commands_batch`
  - `set_task_orders_batch`
  - `set_leader_intents_batch`
  - `set_pilot_reports_batch`
  - `export_observation_packet`
  - `step_execution_batch`
- `WorldBatchRuntime`
  - 任意 `WorldEntityRef` 的批量 command / observation / step helper。
  - sensor / visual / comm candidate 批量查询。

设计含义：

- P8 不需要从底层新建“多机 runtime”。
- 应把同一 world 内的多个成员展开成 refs 批，再复用已有 batch API。

### 3.2 Scenario runtime

可复用设施：

- scenario 中 `entities` 可声明多个平台。
- `apply_world_layout_to_kernel` 与 `load_compiled_scenario_batch` 会返回完整 `entities` 映射。
- 现有 `agent_id` 只是第一个 `is_agent` 的兼容入口，不代表 scenario 只能控制一个实体。

缺口：

- 需要在配置或 scenario metadata 中定义 active controllable roster。
- 需要明确哪些实体进入 policy batch，哪些实体是 scripted / passive。

### 3.3 Python batch / leader 设施

可复用设施：

- `WorldBatchVecEnv` 已经有批量 reset、命令同步、动作下发、step、观测回读路径。
- `_RuntimeFacadeAdapter` 已经集中封装 facade 与兼容 runtime 访问。
- `LeaderBatchedVecEnv` 已有 `ExecutionBatchPredictor`，可对一批执行层观测做一次 policy forward。
- `LeaderWorldBatchExecutionRuntimeGroup` 已有 shared world-batch execution runtime 的调度经验。
- `LeaderWindowRuntimeAdapter` 已把高层 decision window 与低层 execution rollout 分离。

缺口：

- `WorldBatchVecEnv` 当前按 env/world 粒度组织 policy batch，而非按 `WorldEntityRef` 粒度。
- 执行层 observation builder 当前只构造单机输入。
- train config 还没有 `cooperative_execution` 入口。

## 四、执行层输入链路盘点与补齐原则

本节先盘点现有 execution policy 输入链路，再讨论是否需要补齐字段；不讨论 reward/logging 使用的特权评估量。

关键约束：

- 第一版不允许因为训练方便而把 tasking / formation 数据模型字段整包塞进执行层。
- 以当前实际执行层策略输入约 `26` 个标量为预算基准；P8-A 不按 runtime 可导出的全量 observation dict 扩张。
- P8-A 先复用现有 `MissionCommand`、`contacts`、`visual`、sensor / datalink 链路；只有现有现实信息产品无法到达 policy 时，才补最小字段。
- 新增输入必须先被定义为现实飞行员会接收的信息产品，再进入 policy；不能先为训练挑字段，再倒推现实解释。
- 训练器内部用于 reward 的精确误差，默认不进入 policy。

### 4.1 自身平台观测：沿用现有输入

继续保留现有执行层输入：

- `instruments`
- `contacts`
- `rwr`
- `mission`
- `visual`，若训练配置启用
- `proprio`，若训练配置启用

这些对应自身座舱、传感器和任务引导产品。

### 4.2 mission command 链路

P8-A 第一版不新增“角色编号”或“队伍编号”。角色应由任务/编队管线决定，执行策略只接收飞行员实际会拿到的任务指令、编队指令和传感器信息。

现有 `MissionCommand` 已经有执行层指令入口：

```cpp
int formation_id;
double form_offset_x;
double form_offset_y;
double form_offset_z;
```

因此 P8-A 第一优先级不是另造 `station_*` 输入，而是检查并打通现有 command -> mission observation 链路。当前 `MissionObservationInputs` / `compute_mission_observation` 只输出 `command_code`、heading、altitude、speed 和 nav tail，尚未把 `MissionCommand.form_offset_x/y/z` 暴露给执行策略。

建议只把现有 `MissionCommand` 的编队 offset 纳入 `mission` block：

| 输入 | 含义 | 现实来源 | 是否必需 |
| --- | --- | --- | --- |
| `formation_id` | 编队/队形指令编号，若现实任务系统提供 | 任务简令 / 任务系统 / 无线电 | 可选 |
| `form_offset_x` | 分配阵位相对参考/队形坐标的纵向偏移 | 编队指令 | 必需 |
| `form_offset_y` | 分配阵位相对参考/队形坐标的横向偏移 | 编队指令 | 必需 |
| `form_offset_z` | 分配阵位相对参考/队形坐标的高度偏移 | 编队指令 | 条件必需 |

说明：

- 这些字段已经在 `MissionCommand` / `LeaderIntent` / Python binding 中存在，不应再设计一套平行输入。
- `form_offset_*` 是飞行员会收到的编队/阵位指令，不是实时误差。
- lead aircraft 可收到 `0,0,0` 或 element 级命令；不需要给 policy 一个 `formation_role`。
- wingman 的左右、trail、echelon 等由 offset 自然表达，不需要再塞 `wingman_slot_id` 或 `relative_slot_code`。

### 4.3 contacts / radar / datalink 现状与缺口

现有 C++ `TrackData` 已经包含：

```cpp
id, range, azimuth, elevation, closing_speed, time_since_update, source, classification
```

但当前 execution observation 的 `contacts` token 只导出：

```text
range, azimuth, elevation, closing_speed, time_since_update
```

这意味着 policy 能看到目标运动量，但看不到 track 来源和识别结果。对协同编队而言，参考机应来自现实信息源：

- 目视：visual ARB 已有 `team` channel，可看到友机在视野中的方位/深度/径向速度类视觉产品。
- 雷达/传感器：`DefaultSensorModel` 产出 bearing/range/elevation/closing/signal，并进入 `TrackDatabase`。
- 数据链：`TrackManagerSystem` 已支持 `ReportContact` 消息生成 DataLink track。
- IFF/识别：`TrackData.classification` 已存在，但当前执行层 contact vector 没有暴露。

因此第一版不应新增 `ref_*` 平行字段；应优先评估是否把现有 `TrackData.source` / `classification` 作为 contact token 的现实航电产品暴露。如果没有友机识别/数据链来源，模型就不能凭空知道哪个 contact 是长机/僚机。

### 4.4 第一版暂不新增的输入

以下输入即使能在现实中找到来源，第一版也先不新建独立字段，避免绕开已有链路：

- `formation_mode_id`
  - 现实来源：无线电/任务系统。
  - 暂缓原因：P8-A 只做巡航保持，模式可固定；模式状态留在 mission/leader 管线，不直接塞入 policy。
- `wingman_command_mode`
  - 现实来源：无线电/数据链。
  - 暂缓原因：第一版只做 hold slot，不做 rejoin/support/abort 切换；若要表达，也应先映射成 `MissionCommand` 的具体命令或 offset。
- 独立 `ref_*` 字段
  - 暂缓原因：参考机信息应优先来自 `contacts`、visual ARB、sensor / datalink track。`closing_speed` 已在 contact token，参考机高低可由 `elevation` / visual 产品表达。

### 4.5 明确不进入第一版 policy 的输入

以下量不进入 P8-A 第一版执行策略：

- `team_id_norm`
- `element_id`
- `role_code`
- `formation_role`
- `relative_slot_code`
- `wingman_slot_id`
- `formation_template_id`
- `formation_contract_id`
- `formation_error_m`
- `slot_lateral_error_m`
- `slot_longitudinal_error_m`
- `slot_vertical_error_m`
- 全局坐标下参考机位置 / 速度。
- 未经过传感器、目视或数据链建模的完美友机状态。

这些可以保留在 scenario/config、command/tasking/report 或 reward/logging 中，但不作为第一版 execution policy 输入。

### 4.6 当前平台自身任务命令输入

现有 `mission` block 已有 command code / heading / altitude / speed 等任务观测。P8 需要确保每个成员获得的是自己的 per-platform command：

- lead aircraft：跟踪 element 级巡航/航路命令。
- wingman：在相同 element 意图下，额外带阵位/参考平台约束。

不建议把所有 team 成员共享同一份 mission vector 后让模型猜角色。

### 4.7 不进入执行策略、只用于 reward/logging 的量

以下量可以用于 reward、diagnostics、contract、可视化，但默认不直接进入 policy：

- `formation_error_m`
- `slot_lateral_error_m`
- `slot_longitudinal_error_m`
- `slot_vertical_error_m`
- 最小 separation 统计。
- 全局世界坐标下的完美友机位置/速度。
- team-level success/failure internal state。

若后续确实希望把某种 error 作为 policy 输入，必须先把它建模为现实座舱产品，例如 formation cue / datalink steering cue，并写清来源、延迟与可用性。

换言之，能否进入 policy 不取决于它对训练是否有用，而取决于飞行员是否真的能收到这个信息产品。

## 五、下一步执行计划

下一步不从“新增双机输入”开始，而从现有链路的可用性验证开始。每一刀都必须回答两个问题：

- 这个信息现实飞行员从哪里收到？
- 这个信息当前已有链路是否已经能送到 execution policy？

### P8-A1：设施验证 probe

目标：

- 不新增大抽象，先证明已有 runtime 可承载同 world 多实体控制。

内容：

- 构造一个最小双机空中巡航 scenario。
- 同 world spawn 两架 Blue aircraft。
- 从 `entities` 映射构造两个 `WorldEntityRef`。
- 批量读取 `ObservationBatchPacket`。
- 批量下发两份 `PilotAction`。
- step 后验证两机状态均变化。

验收：

- probe 或 pytest 在 `.venv` + `PYTHONPATH=build-workshop` 下通过。
- 不依赖 `agent_id` 之外的专用 C++ 新接口。

当前进展：

- 已补 `tests/world_batch/test_world_batch_runtime.py::test_world_batch_runtime_controls_multiple_entities_within_same_world`。
- 已在 `.venv` + `PYTHONPATH=build-workshop` 下通过。
- 当前结论是：`WorldBatchRuntime` 现有 `WorldEntityRef -> get_*_batch / set_pilot_actions_batch / step_batch` 链路足以承载同 world 多实体执行控制，不需要先新增双机专用 runtime。

### P8-A2：现有 mission command 编队字段链路验证

目标：

- 验证 `MissionCommand.formation_id` / `form_offset_x/y/z` 能否从 leader/tasking 管线进入 kernel。
- 明确它们当前是否已经进入 execution policy 的 `mission` observation。

内容：

- 构造一份带 `form_offset_x/y/z` 的 `LeaderIntent` 或 `MissionCommand`。
- 通过已有 `set_mission_commands_batch` / `build_kernel_mission_command` 下发。
- 读取 kernel 中对应实体的 mission command，确认字段保真。
- 构造当前 `mission` observation，确认现状：`compute_mission_observation` 目前只输出 command/heading/altitude/speed/nav tail。

验收：

- 形成一个 contract/probe，锁定“现有 command 字段存在但 observation 未暴露”的事实。
- 不改变默认 `mission_obs_mode`，避免破坏 P5/P7 冻结模型。

当前进展：

- 已补 `tests/runtime/test_leader_tasking_runtime.py::test_build_kernel_mission_command_maps_formation_offsets`，确认 `LeaderIntent -> MissionCommand` 映射已包含 `formation_id / form_offset_x/y/z`。
- 已补 `tests/world_batch/test_world_batch_runtime.py::test_world_batch_runtime_mission_command_roundtrip_preserves_formation_offsets`，确认沿既有 command-link 使用方式时，kernel mission command roundtrip 可保留编队 offset。
- 已补 `tests/runtime/test_mission_runtime.py::test_loader_mission_observation_current_contract_ignores_formation_offsets`，确认当前 `MissionObservationInputs` / `compute_mission_observation` 仍只暴露 command/heading/altitude/speed/nav tail，尚未把编队 offset 暴露给执行策略。

补充说明：

- 当前 `.venv` 下整文件运行 `tests/runtime/test_mission_runtime.py` 会被已有 `UniversalEnv` 测试触发的 `gymnasium` 依赖拦住；P8-A2 新增的定向合同测试本身已通过。
- 这一阶段仍未修改默认 `mission_obs_mode` 和旧 observation shape。

### P8-A3：cooperative mission observation 最小扩展

目标：

- 只在协同执行入口中，把现实可接收的编队指令送入 policy。

建议：

- 增加显式 opt-in 的 mission observation mode 或配置开关，例如 `nav_v2_formation_v1`。
- 在该模式下追加现有 `MissionCommand` 的 `form_offset_x/y/z`，必要时追加 `formation_id`。
- 保持 `basic` / `nav_v1` / `nav_v2` 默认维度不变。

验收：

- 单机旧训练配置 observation shape 不变。
- 协同执行配置能获得 per-platform formation command。
- 测试必须说明这些字段的现实来源是任务简令 / 任务系统 / 无线电编队指令。

进入条件：

- P8-A1 / P8-A2 已完成后，再做最小 opt-in 扩展。
- 第一刀只补 `mission` 现有链路，不引入新的平行 `station_*` 观测块。

当前进展：

- 已新增显式 opt-in mission observation mode：`nav_v2_formation_v1`。
- 已沿既有 `mission_cmd -> MissionObservationInputs -> compute_mission_observation` 链路把 `form_offset_x / form_offset_y / form_offset_z` 接入该模式。
- 旧模式 `basic / nav_v1 / nav_v2` 的输出维度保持不变；新模式维度为 `17 = 4 + 10 + 3`。
- 已显式保证在“没有 route guidance、但存在编队指令”的情况下，`nav` tail 归零而 `formation` tail 仍保留，不会被一并清零。
- 已同步打通 Python loader / env 配置 / GPU batch export / CUDA mission packing。
- 已补定向合同测试，覆盖：
  - 新模式追加编队 offset；
  - 无 route guidance 时仍保留编队 offset；
  - 旧 `nav_v2` 模式继续忽略编队 offset；
  - `nav_v2_formation_v1` loader / batch export 形状与数值合同。

当前结论：

- P8-A3 已完成，且保持了对 P5/P7 冻结单机模型默认观测形状的兼容。
- 下一阶段不应再往 `mission` block 塞工程标签；后续切口应转向 A4/A6，继续核验并补齐现有 `contacts / visual / datalink` 现实信息链路。

### P8-A4：contacts / visual / radar 识别链路验证

目标：

- 不新增 `ref_*` 平行字段，先确认现有传感器产品是否足以识别友机/参考机。

内容：

- 构造双机同 world 场景，确保 sensor / visual 可见。
- 检查 `AgentObservation.contacts` 中 `TrackData.source` / `classification` 是否被正确设置。
- 检查当前 execution contact token 是否丢弃了 `source` / `classification`。
- 检查 visual ARB 的 `team` 通道能否稳定表达友机视觉线索。

验收：

- 若 contacts 识别信息足够，后续只扩展 contact token，不新增 reference 输入。
- 若 contacts 识别信息不足，先补 sensor / datalink / track manager，而不是让 policy 直接看参考机真值。

当前进展：

- 已补 `tests/runtime/test_mission_runtime.py::test_execution_contact_runtime_contract_drops_source_and_classification`。
- 已确认当前 execution contact token 仍为固定 `5` 列，导出字段只有 `range / azimuth / elevation / closing_speed / time_since_update`；`TrackData.source / classification` 仍不进入执行层 contact token。
- 已补 `tests/runtime/test_mission_runtime.py::test_visual_observation_team_channel_marks_friend_and_hostile`，确认 visual ARB `CH_TEAM` 通道已能输出 `-1 / 0 / +1` 的敌我标记。
- 已把 `TrackManagerSystem` 正式接入主 pipeline，并用现有 `Alliance` + `TrackSource` 逻辑填充 `TrackData.source / classification`。
- 已把 `DataLinkFusionSystem` 的既有共享内容落成 `ReportContact` 消息，让 wingman 可以通过现有消息/track 链路接到 lead 的共享 track。
- 已补 `examples/config/database/aircraft/units/f16c_block50.json` 的 `has_data_link / data_link_network_id`，使真实数据库蓝机具备可用数据链配置。
- 已补定向 live 合同测试，确认：
  - `AgentObservation.contacts` 可在真实飞行器配置下产出 `source=1` 的 radar track；
  - same-side shared track 能在后续帧进入 wingman 的 track picture，`source=3`；
  - `classification` 能稳定区分 `friendly` / `hostile`；
  - visual `team` 通道仍保持可用现实线索。

下一步优先级：

- A4 已完成。
- 后续优先转向 A6：继续核验并补齐现有 `contacts / visual / datalink` 现实信息链路在 policy 侧的最小输入合同，不再新增 `ref_*` 平行字段。

### P8-A5：roster 配置草案

目标：

- 明确 scenario/config 如何声明可控成员。

建议配置形态：

```json
{
  "cooperative_roster": {
    "team_id": 7001,
    "members": [
      {
        "entity": "Lead",
        "role_code": 21,
        "formation_role_id": "ElementLead",
        "relative_slot_code": 11,
        "policy_route": "shared_execution"
      },
      {
        "entity": "Wing",
        "role_code": 22,
        "formation_role_id": "Wingman",
        "wingman_slot_id": "Right",
        "relative_slot_code": 12,
        "reference_entity": "Lead",
        "policy_route": "shared_execution"
      }
    ]
  }
}
```

验收：

- 能从 scenario/config 解析出 `WorldEntityRef` 列表与 per-member role/slot metadata。
- 双机只是 `members.length == 2` 的特例。

当前状态：

- 已确认现有 `RuntimeFacade` / `WorldBatchRuntime` / `ScenarioLoader` 已具备按 `WorldEntityRef` 批量编排的底座。
- 目前还没有正式的 `cooperative_roster` 解析入口，因此 roster 仍停留在文档草案层。
- 下一步应先把协同巡航训练配置落到维护中的 active 目录，再补 roster 解析契约。

### P8-A6：执行观测链路补齐

目标：

- 不新建平行观测块，先补齐现有 mission / contact / visual 链路中的缺口。

要求：

- 若需要编队指令，优先把现有 `MissionCommand.form_offset_x/y/z` 接入 mission observation。
- 若需要识别参考机，优先检查 `contacts` 是否应暴露现有 `TrackData.source` / `classification`。
- 视觉参考优先复用 visual ARB 的 `team`、depth、angular size、radial velocity 等通道。
- 不把 reward 内部误差直接暴露给策略。
- 每个新增字段必须在代码注释或 contract 中说明“飞行员如何收到它”；说不清来源的字段不得进入 observation space。

### P8-A7：共享策略推理路径

目标：

- 复用 `ExecutionBatchPredictor` 的思想，把 `N` 个成员观测 stack 后做一次 policy forward。

要求：

- 管线支持 shared policy。
- action 输出按 refs 还原成 `WorldPilotActionAssignment`。
- 保留未来 per-role policy routing 的接口位置。

当前进展：

- 已完成 cooperative execution 的 shared-policy 训练入口底座：`train.py` 现支持 `agent_layer = "cooperative_execution"`。
- 已新增 `CooperativeWorldBatchVecEnv`，当前以“每个 roster 成员一个 flat VecEnv slot、同 world 同步 step/reset”的方式打通 cooperative rollout。
- 当前实现已经支持 shared policy 的训练 smoke，与既有 `execution` / `leader` 路径兼容共存。
- `policy_route` 目前仍主要作为 roster / routing 元数据保留；多 policy / role-split 训练闭环仍是后续工作，而不是本阶段已完成项。

## 六、收束结论

P8 协同执行管线的最小闭环已经完成验证：

- 双机同 world 控制链路可用。
- 现有 `MissionCommand` 编队字段已可沿任务链进入协同执行入口。
- 协同执行的 mission observation 扩展已落成并保持 opt-in。
- contacts / visual / datalink 现实信息链路已完成最小合同核验。
- shared-policy cooperative rollout 与 benchmark 入口已经跑通。

因此，P8 现在应作为“已验证协同底座”的记录保留，不再继续向其中追加新输入族或新专用路径。它已经是当前协同训练推进线，而不是冻结历史线。后续回到主线训练时，优先分析的是：

1. 这些协同结论如何影响主线训练入口与配置边界。
2. 哪些现实可获得信息产品可以复用到主线，而不是只服务协同线。
3. 哪些协同能力应继续停留在显式 opt-in，而不进入默认训练面。

### P8-A8：双机巡航最小验收

目标：

- 以 `N=2` 验证协同执行管线。

验收指标：

- 两机均由执行策略/控制器输出动作，不把 lead aircraft 脚本化为运动轨迹。
- 长机层只生成 element 意图和 per-member command。
- wingman 能在短窗口内维持合理 separation，不发生近失撞。
- logging 中输出 slot/separation/closure 指标。

当前状态：

- P8 的输入链路与命令链路已完成前置核验，但双机巡航训练线尚未形成维护中的配置入口。
- 这意味着 P8 现在适合进入“协同巡航配置与场景编排”阶段，而不是直接把它视作已完成的双机训练基线。

## 六、暂不做

P8-A 暂不做：

- 双机起飞 / 降落。
- 双机对战 / self-play。
- 四机 package runtime。
- C2 端到端 RL。
- 无限制多智能体联合训练。
- 新增 C++ 多机专用 runtime。

这些应在协同执行管线和现实可观测输入稳定后再推进。
