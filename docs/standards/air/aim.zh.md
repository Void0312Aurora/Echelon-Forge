# 空中任务命令与 Tasking 合同

Language:
- English canonical: `aim.md`
- Chinese companion: [aim.zh.md](aim.zh.md)

状态：`2026-05-18`，当前维护中的 air tasking 与 executable command 特化基线。

本文档定义下列 air 侧合同：

- `TaskOrderAir`
- `LeaderIntentAir`
- `MissionCommand` 中的 air-specialized 字段

它取代了早期把 air mission command 直接当作“全项目通用命令标准”的写法。

## 范围

主要依据：

- [src/components/tasking/air/task_order_air.h](../../../src/components/tasking/air/task_order_air.h)
- [src/components/tasking/air/leader_intent_air.h](../../../src/components/tasking/air/leader_intent_air.h)
- [src/components/command/common/mission_command_core.h](../../../src/components/command/common/mission_command_core.h)
- [src/components/command/air/mission_command_air.h](../../../src/components/command/air/mission_command_air.h)
- [gym_envs/scenario_loader/runtime_state.py](../../../gym_envs/scenario_loader/runtime_state.py)
- [tests/runtime/mission/test_mission_command_air_fields_roundtrip.py](../../../tests/runtime/mission/test_mission_command_air_fields_roundtrip.py)

## 分层

当前维护中的分层为：

- common core：
  - `TaskOrderCore`
  - `LeaderIntentCore`
  - `MissionCommandCore`
- air specialization：
  - `TaskOrderAir`
  - `LeaderIntentAir`
  - `MissionCommandAir`

代码里这些类型仍可能通过组合 struct 一起暴露，但字段归属仍然是分层的。

## Air 当前使用的 Common-Core Command 字段

当前 air runtime 仍依赖共享的 `MissionCommandCore` 字段：

- `command_code`
- `cmd_heading_deg`
- `cmd_altitude_m`
- `cmd_speed_mps`
- `route_ref_id`
- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `authorization_to_fire`
- `active`

这些字段不是 air 独有语义。air 会使用它们，但不拥有它们。

## Air-Specialized `MissionCommand` 字段

当前维护中的 air 扩展字段包括：

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

这些字段属于 air-specific 的执行/tasking 语义，不应因为它们今天出现在共享 runtime carrier 中，
就被提升成 common core。

## Air Tasking 字段

`TaskOrderAir` 当前承载的是上游 air tasking surface，包括：

- package / element / lead 标识
- station anchor 与 station geometry
- altitude/speed block 与 target 值
- recovery 配置
- takeoff procedure 与 runway slot
- formation template / contract / role 关联
- support-sector 与 mutual-support metadata

这属于 tasking 侧的空中组织语义，不是最终 executable command 对象。

## Air Leader-Intent 字段

`LeaderIntentAir` 当前承载的是 leader 侧 air decision surface，包括：

- `phase_id`
- `element_phase_id`
- `route_ref_id`
- recovery 与 approach 字段
- takeoff procedure / clearance / interval / runway slot
- formation mode 与 offset
- join / rejoin / split 标志
- support anchor 与 slot offset
- `approach_armed`、`commit_to_land`、`abort_flag`

它是 leader 侧的中间决策层，在映射到最终 `MissionCommand` 前存在。

## 当前维护中的 `command_code` 语义

当前 runtime 与测试实际使用的数值合同是：

- `0`: idle / hold
- `1`: takeoff
- `2`: vector / cruise / 直接 command-following
- `3`: waypoint 或 LNAV-style route navigation
- `4`: landing / final approach

这是当前维护中的实现合同。更大的宏命令目录如果还没有形成稳定 runtime 行为，不应在这里写成既成事实。

## Roundtrip 要求

当前 air command 合同必须能稳定穿过：

- JSON mission-command backfill/export
- execution-episode state import/export
- post-waypoint transition handoff
- takeoff/formation mode 下的 mission-observation assembly

这也是为什么 `recovery_*`、`takeoff_*`、`runway_slot_*`、`formation_*`
会被专门做 roundtrip 测试。

## 归属边界

应继续保留在 common core 的内容：

- command carrier 的骨架
- authority 与 ROE 字段
- 中性的 target heading / altitude / speed 参考

应继续保留在 air specialization 的内容：

- runway 与 recovery
- takeoff procedure 与 runway slot
- formation offset 与 air formation identifier
- approach / landing-specific leader intent

## 非目标

本文档不试图标准化完整的空战 task doctrine 目录，不试图穷举 CAP/BARCAP/TARCAP 体系，
也不试图预写所有未来 leader behavior。它只描述当前 runtime 与测试已经视作稳定的维护合同。
