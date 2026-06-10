# Joint 命令链与汇报基线

语言：
- 英文主文：[command_link_and_reporting_baseline.md](command_link_and_reporting_baseline.md)
- 中文辅文：`command_link_and_reporting_baseline.zh.md`

状态：`2026-06-10`，与活跃 `MissionCommandCore` target metadata 对齐的权威 joint command-link contract。

本文档记录 `MissionCommand`、`CommandLink`、`DataLink` 和 `ROE` 在 joint/common core 中的最小闭环。

目标不是把所有真实 C2 能力都建出来，而是定义一个已经与当前运行时和测试对齐的最小合同。

## 1. 最小闭环

当前 joint 命令闭环是：

`TaskOrder -> LeaderIntent -> MissionCommand -> CommandLink -> Execution -> Report -> DataLink`

这是当前代码库里最小且有用的边界。

- `TaskOrder` 负责发起任务意图
- `LeaderIntent` 负责收敛领导者的战术决策
- `MissionCommand` 负责变成可执行的命令状态
- `CommandLink` 负责投递时序、积压和顺序
- `Execution` 负责消费命令
- `Report` 负责回传状态和结果
- `DataLink` 负责共享航迹和汇报数据

## 2. `MissionCommand` 作为可执行合同

`MissionCommand` 是运行时可直接消费的命令对象。

当前 common 部分已经包含：

- `command_code`
- `cmd_heading_deg`
- `cmd_altitude_m`
- `cmd_speed_mps`
- `route_ref_id`
- `active`

命令合同还携带 authority 相关字段：

- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `authorization_to_fire`

它还携带 command-context target provenance 字段，用于支撑 ROE 与 assignment
决策，但不让 common core 负责 track fusion：

- `threat_state`
- `assigned_target_track_id`
- `assigned_target_source_id`
- `assigned_target_snapshot_time_s`

运行时测试已经说明，这些字段会经过 Python bindings、episode state 序列化和 controller 导入/导出流程保持一致。

## 3. 通用命令与军种专用命令字段

common 命令层应保持中性且小。

通用示例：

- `command_code`
- `target_heading`
- `target_altitude`
- `target_speed`
- `roe_state`
- authority holder / grantor 字段
- threat 与 assigned-target provenance 字段

军种专用示例：

- 空军：
  - `recovery_base_id`
  - `recovery_runway_id`
  - `recovery_approach_type`
  - `takeoff_procedure_id`
  - `takeoff_clearance_id`
  - `takeoff_interval_s`
  - `runway_slot_id`
  - `formation_id`
  - `form_offset_x`
  - `form_offset_y`
  - `form_offset_z`
- 海军：
  - `reference_entity_id`
  - `station_radius_m`
  - `station_bearing_deg`
  - `embarked_helo_entity_id`
  - `launch_helo`
  - `recover_helo`
  - `relay_oth_targeting`

测试已经把这些军种专用字段视为 `MissionCommand` 的有效扩展，但它们不应反过来重定义 joint/common core 的命名边界。

## 4. `CommandLink`

`CommandLink` 是命令生成和命令消费之间的投递与排序层。

当前运行时已经体现出的最小语义包括：

- 可以有积压
- 可以有延迟
- 命令顺序很重要
- 命令到达不等于命令生成

这已经足以把 `CommandLink` 和命令对象本身区分开。

common core 里的 `CommandLink` 应负责：

- 投递延迟
- pending queue 行为
- 优先级和重排规则
- 传输边界的丢弃或丢失处理

它不应负责：

- 平台运动逻辑
- 武器逻辑
- 航迹融合逻辑
- 军种专用执行语义

## 5. `DataLink`

`DataLink` 是共享信息交换层，承载航迹和汇报数据。

在这个项目里，`DataLink` 应理解为：

- 共享航迹
- 共享汇报
- 共享战术态势数据

不应把它当成纯粹的 raw contact dump。common core 更适合使用 `track/report` 语义，因为这与当前运行时方向一致，也更干净。

## 6. `ROE`

`ROE` 是可执行命令合同的一部分。

当前测试表明，这里已经形成了一个最小但真实的合同：

- `roe_state` 是状态值，不只是布尔开关
- `authorization_to_fire` 是挂在命令上的授权门
- 交战 authority 可以用 holder 和 grantor ID 表示

最小可用解释是：

- `roe_state` 表示当前规则状态
- `engagement_authority_holder_id` 表示谁持有当前 authority
- `engagement_authority_grantor_id` 表示 authority 的来源
- `assigned_target_id` 表示 authority 决策绑定的目标
- `threat_state` 携带当前 runtime profile 使用的 command-context threat classification
- `assigned_target_track_id` 在 provenance 可用时标识 assigned target 使用的 track record
- `assigned_target_source_id` 标识提供 assigned target 或 track context 的来源
- `assigned_target_snapshot_time_s` 记录 assigned target context 的 snapshot time
- `authorization_to_fire` 表示当前命令是否允许开火

这只是最小合同，不是完整 doctrine 模型。但它足以保持运行时一致、可测。

## 7. 闭环语义

最小闭环应保持这些性质：

- 命令生成和命令投递是分开的
- 投递顺序有意义
- 报告数据可以经由 data link 回流
- ROE 和 authority 跟着命令走，而不是挂在命令外面

这就是 common core 和 service profile 之间的实用分界。

## 8. 边界总结

建议按下面方式划分：

- `joint/common core`
  - 关系词汇
  - authority scope
  - 通用命令合同
  - 命令投递语义
  - 汇报共享语义
- `service profile`
  - 空军、海军或早期 ground 的解释方式
- `platform/task specialization`
  - 实际运动、站位、回收和武器执行
