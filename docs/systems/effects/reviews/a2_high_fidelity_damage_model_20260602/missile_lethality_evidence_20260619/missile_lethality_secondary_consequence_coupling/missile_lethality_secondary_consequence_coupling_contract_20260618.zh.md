# MLF-7 二次后果耦合 — 耦合契约

状态：`2026-06-18`，初始 runtime bridge 已接受本契约。本契约只有工程代理权威；
它不是真实世界杀伤、Pk 或平台特定校准权威。

## 契约决策

MLF-7 使用 `StructuralBreakupState` 作为 runtime 事实源。bridge 在
`StructuralFailureUpdate` 后运行，把有边界值写入维护中的 aircraft damage 和
platform damage 表面，然后调用 `sync_platform_damage_loss_state`。

bridge 不改变现有 `AircraftDamageStateUpdate` 顺序。因此 aircraft damage 和
loss-state 字段在同一 tick 更新，而 `FlightModel`、`Propulsion`、`Sensor`、`Mass`
和 `FuelSystem` 在下一 tick 消费新的 damage state。

诊断上，MLF-7 将最后发出的 structural-breakup event id 存到
`StructuralBreakupState`，并且只有 bridge 实质改变维护中的 aircraft/platform 状态时，
才发出 `PlatformConsequenceEvent`。该事件使用 structural-breakup event 作为
`parent_event_id`，并保持同一 `chain_id`。

## 模式映射

| 断裂模式 | 飞机后果 | 平台后果 | 失能规则 |
| --- | --- | --- | --- |
| no breakup / `Intact` | 不写入 | 不写入 | 不改变 |
| `wing_loss` | `structural_integrity <= 0.70`、`flight_control_integrity <= 0.72`、`roll_control_integrity <= 0.55`、`hydraulic_pressure_availability <= 0.82`、`control_asymmetry >= 0.35`、forced landing | `mobility_capability <= 0.35`、`survivability_margin <= 0.70`；forced landing 经维护中 helper 将 mobility 投影到 `<= 0.25` | 维护阈值触发时成为 `MobilityKill` |
| `tail_loss` | `flight_control_integrity <= 0.60`、`pitch_control_integrity <= 0.45`、`yaw_control_integrity <= 0.50`、`hydraulic_integrity <= 0.78`、`hydraulic_pressure_availability <= 0.76`、`control_asymmetry >= 0.20`、forced landing | `mobility_capability <= 0.30`、`survivability_margin <= 0.75`；forced landing 将 mobility 投影到 `<= 0.25` | 维护阈值触发时成为 `MobilityKill` |
| `engine_detach` | `propulsion_integrity <= 0.30`、`fuel_system_integrity <= 0.72`、`fuel_leak_severity >= 0.30`、`flammable_fluid_exposure >= 0.25`、`ignition_source_severity >= 0.20`、forced landing | `mobility_capability <= 0.30`、`survivability_margin <= 0.72`；forced landing 将 mobility 投影到 `<= 0.25` | 维护阈值触发时成为 `MobilityKill` |
| `fuselage_rupture` | `structural_integrity <= 0.50`、`fuel_system_integrity <= 0.65`、`crew_effectiveness <= 0.85`、`pilot_effectiveness <= 0.88`、`fuel_leak_severity >= 0.45`、`fire_severity >= 0.15`、`fuselage_fire_zone_severity >= 0.20`、forced landing | `mission_capability <= 0.65`、`survivability_margin <= 0.50`；forced landing 将 mobility 投影到 `<= 0.25` | maintained helper 可设为 `MobilityKill`；无直接删除 |
| `multi_axis` | `structural_integrity <= 0.20`、control axes `<= 0.25-0.30`、hydraulic availability `<= 0.30`、propulsion `<= 0.25`、command/navigation `<= 0.45`、`control_asymmetry >= 0.65`、`structural_overstress >= 0.75`、forced landing | `mobility_capability <= 0.0`、`mission_capability <= 0.25`、`sensor_capability <= 0.50`、`survivability_margin <= 0.0` | `airframe_breakup` 为真时通过 `sync_platform_damage_loss_state(..., force_lost=true)` 成为 `Lost` |

## 守卫

- 所有写入都是幂等的上下限投影；同一个不可逆断裂状态不会产生重复 runaway delta。
- bridge 忽略非飞机实体。
- bridge 不写 HP。
- bridge 不创建残骸/碎片实体。
- bridge 不删除实体。
- bridge 不创建 Pk、stock weapon truth 或训练奖励输出。
- `PlatformConsequenceEvent` 输出只是 diagnostics-only 工程代理，不是校准杀伤或奖励权威。

## 证据

- 实现：
  [src/systems/combat/structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h)
- 聚焦验证：
  [src/tests/test_structural_failure_system.cpp](../../../../../../../src/tests/test_structural_failure_system.cpp)
- 通过命令：
  `cmake --build build-workshop --target ef_test -j 2`
- 通过命令：
  `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure`
- 通过命令：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
- 通过命令：
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
