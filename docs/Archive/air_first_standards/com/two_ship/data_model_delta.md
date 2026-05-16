# 双机阶段数据模型增量 (Data Model Delta for Two-Ship Stage)

> ARCHIVED NOTE (2026-03-23): 该文档属于第一版 air-specific 双机标准草案，现仅保留作历史参考。
> 当前标准化基线请改看 [docs/standards/README.md](/home/void0312/Workshop/CMO/docs/standards/README.md)。

本文档定义双机阶段相对于现有单机标准需要新增或收紧的数据结构。

## 1. 总原则

双机阶段不是简单给第二架飞机复制一份单机 `TaskOrder`。

必须增加：

- 编组身份
- 指挥从属
- 编队模板
- 协同状态
- 队内回报

否则系统会退化为两个并行单机 agent。

## 2. TaskOrder 增量

现有 [task_order_leader_standard.md](/home/void0312/Workshop/CMO/docs/Archive/air_first_standards/com/task_order_leader_standard.md) 已经预留了部分编队字段，但双机阶段需要把它们从“可选语义”收紧成“最小实现字段”。

### 2.1 新增强制字段

- `assignee_kind`
  取值建议：
  - `aircraft`
  - `element`
  - `package`
- `element_id`
- `package_id`
- `lead_aircraft_id`
- `formation_template_id`
- `formation_contract_id`

### 2.2 新增协同字段

- `formation_role_id`
  取值建议：
  - `element_lead`
  - `wingman`
- `wingman_slot_id`
  取值建议：
  - `left`
  - `right`
  - `trail`
- `join_policy_id`
- `rejoin_policy_id`
- `mutual_support_mode`
- `support_sector_id`

### 2.3 说明

在双机阶段：
- C2 应优先下达 `element` 级任务
- 单机级 `assignee_id` 只用于 fallback 或特殊 detach 情况

## 3. LeaderIntent 增量

现有单机 `LeaderIntent` 主要面向“单架 lead 的 phase 与 mission command”。

双机阶段建议新增：

- `element_phase_id`
- `formation_mode_id`
- `join_required_flag`
- `rejoin_required_flag`
- `split_flag`
- `support_anchor_x_m`
- `support_anchor_y_m`
- `support_slot_offset_x_m`
- `support_slot_offset_y_m`
- `wingman_command_mode`

说明：
- `LeaderIntent` 不应直接变成 wingman 的杆舵控制器
- 它应该表达“wingman 当前应保持什么协同状态”

## 4. PilotReport / WingmanReport 增量

双机阶段至少需要补充能反映编队状态的回报语义。

建议增加：

- `REP_JOINED`
- `REP_REJOINING`
- `REP_FORM_LOST`
- `REP_UNABLE_FORM`
- `REP_SUPPORTING`
- `WARN_SEPARATION`

最小状态值建议包括：

- `formation_error_m`
- `bearing_error_deg`
- `closure_mps`
- `separation_m`

## 5. Scenario 层增量

双机阶段场景必须新增：

- 多机 spawn 关系
- 机间 callsign / role
- 初始编队模板
- C2 的任务接收对象
- 默认链路约束

场景应能表达：

- 双机同场起飞
- 领僚不同初始位置
- 集合后进入 CAP / route
- RTB 时保持或解散编队

## 6. 观测空间增量

双机阶段长机 / 僚机观测必须增加队内相对量：

- `lead_relative_bearing_deg`
- `lead_relative_range_m`
- `lead_relative_altitude_m`
- `lead_relative_closure_mps`
- `slot_lateral_error_m`
- `slot_longitudinal_error_m`
- `slot_vertical_error_m`
- `line_of_sight_valid_flag`
- `link_available_flag`
- `lost_wingman_flag`

四机阶段才需要再增加：

- `other_element_relative_state`
- `package_anchor_state`

## 7. 不在本阶段进入运行时的数据

为保持双机阶段收敛，下列对象先不进入实时控制：

- 行政中队 / 大队编制树
- 大规模 sortie 排班与出动率模型
- 多个 package 之间的战区级协同

这些更适合作为：

- 场景元数据
- campaign / operation 层
- 后续任务生成器
