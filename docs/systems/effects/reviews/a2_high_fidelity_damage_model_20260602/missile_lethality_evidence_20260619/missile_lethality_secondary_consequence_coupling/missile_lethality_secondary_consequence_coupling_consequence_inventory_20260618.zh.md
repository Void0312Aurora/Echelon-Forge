# MLF-7 二次后果耦合 — 后果盘点

状态：`2026-06-18`，初始 MLF-7 runtime bridge 所需盘点已完成。本盘点只授权
[structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h)
中的窄桥接。

## 读取输入

| 表面 | MLF-7 可读取字段 | runtime 用途 |
| --- | --- | --- |
| [StructuralBreakupState](../../../../../../../src/components/combat/structural_failure.h) | `breakup_state`、`active_break_modes`、`active_structural_groups`、`detached_part_count`、`airframe_breakup`、`last_breakup_event_id` | 后果投影的主要 runtime 事实源；`last_breakup_event_id` 将后果诊断关联到结构父事件 |
| [StructuralBreakupEvent](../../../../../../../src/runtime/contracts/engagement_contracts.h) | `header.chain_id`、`header.parent_event_id`、`header.event_id`、`breakup_state`、`break_mode`、`detached_part_ref`、`detached_part_count`、`airframe_breakup`、`cause_event_id` | 只作为诊断/export 输入；本切片不把事件作为 reactive runtime control signal |
| [KeyEntity](../../../../../../../src/components/basic/common.h) | `type` | 将 runtime bridge 限定到 `UnitType::Aircraft` |

## 已批准 Runtime 写入

| 表面 | 字段 | Owner | MLF-7 规则 |
| --- | --- | --- | --- |
| [AircraftDamageState](../../../../../../../src/components/domains/air/combat/damage_air.h) | `structural_integrity`、`flight_control_integrity`、`hydraulic_integrity`、`hydraulic_pressure_availability`、`roll_control_integrity`、`pitch_control_integrity`、`yaw_control_integrity`、`control_asymmetry`、`propulsion_integrity`、`fuel_system_integrity`、`crew_effectiveness`、`pilot_effectiveness`、`fire_severity`、`fuel_leak_severity`、`flammable_fluid_exposure`、`ignition_source_severity`、`fuselage_fire_zone_severity`、`structural_overstress`、`forced_landing_required` | Air damage model | 只通过 `apply_structural_breakup_consequence` 写有边界上下限；不做可累积 runaway 扣损 |
| [PlatformDamageState](../../../../../../../src/components/combat/common/damage_common.h) | `mission_capability`、`mobility_capability`、`sensor_capability`、`survivability_margin`、kill flags、`loss_state` | Common platform damage model | capability 有边界，然后通过 `sync_platform_damage_loss_state` 同步失能状态 |
| [Health](../../../../../../../src/components/combat/health.h) | `mission_kill`、`mobility_kill`、`sensor_kill` | Common loss-state mirror | 只由 `sync_platform_damage_loss_state` 更新；MLF-7 不扣 HP |
| [PlatformConsequenceEvent](../../../../../../../src/runtime/contracts/engagement_contracts.h) | `header`、before/after capability fields、kill flags、aircraft-damage before/after/delta strings、`loss_state_from`、`loss_state_to` | Engagement event diagnostics | 只有结构后果投影改变维护中状态且上游 structural event id 存在时记录 |

## 维护中的下游消费者

| 表面 | Owner | 节拍 |
| --- | --- | --- |
| [FlightModel](../../../../../../../src/components/physics/performance.h) | [damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h) 中的 `AircraftDamageStateUpdate` | bridge 在 `AircraftDamageStateUpdate` 后运行，因此下一 tick 消费 MLF-7 写入的 aircraft damage |
| [Propulsion](../../../../../../../src/components/physics/dynamics.h) | `AircraftDamageStateUpdate` | 同样下一 tick 投影 |
| [Sensor](../../../../../../../src/components/systems/sensor.h) | `AircraftDamageStateUpdate` | 同样下一 tick 投影 |
| [Mass](../../../../../../../src/components/physics/dynamics.h) 和 `FuelSystem` | `AircraftDamageStateUpdate` | 同样下一 tick 投影燃油泄漏 |

## 执行顺序

[simulation_kernel_systems.cpp](../../../../../../../src/core/engine/simulation_kernel_systems.cpp)
中的当前注册顺序：

1. `register_damage_system_common`
2. `register_aircraft_damage_system` / `AircraftDamageStateUpdate`
3. `register_structural_failure_system` / `StructuralFailureUpdate`
4. `register_structural_consequence_system` / `StructuralConsequenceUpdate`

结果：`StructuralConsequenceUpdate` 在结构断裂事实形成同一 tick 写入
`AircraftDamageState`、`PlatformDamageState` 和 loss-state mirror。`FlightModel`、
`Propulsion`、`Mass` 和 `Sensor` 在下一 tick 看到这些 aircraft-damage 字段。

## 禁止写入

- 不新增 `e.destruct()` 或目标实体删除。
- 不创建残骸/碎片实体或 detached ECS 生命周期。
- MLF-7 自身不扣 HP。
- 不新增 Pk / 统计杀伤投影。
- 不修改训练奖励。
- 不声明 weapon-specific、MQ-9、F-16C、AIM-120C、海军或地面杀伤权威。

## 证据

- Runtime bridge：
  [src/systems/combat/structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h)
- 注册：
  [src/core/engine/simulation_kernel_systems.cpp](../../../../../../../src/core/engine/simulation_kernel_systems.cpp)
- 聚焦测试：
  [src/tests/test_structural_failure_system.cpp](../../../../../../../src/tests/test_structural_failure_system.cpp)
- 验证：
  `cmake --build build-workshop --target ef_test -j 2`
- 验证：
  `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure`
- 验证：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
- 验证：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
