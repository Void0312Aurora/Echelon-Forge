# MLF-8 派发队列

状态：`2026-06-19` accepted / archived MLF-8 派发记录。MLF8-D1 已
complete / inventory-pass，MLF8-D2 已 complete / contract-pass，MLF8-D3 已
complete / focused-pass，MLF8-D4 已 complete / focused-pass，MLF8-D5 已
complete / accepted-archived；当前没有 worker 正在运行。

英文规范页：
[missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.md](missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.md)。

## 队列规则

- 不创建新的会话线程。
- 同一时间只派发一个可写 runtime worker。
- P1 和 P2 可以作为只读/文档工作准备，但 P3 必须等待已验收 P2 contract。
- 除 broken link 或主线程明确确认的上游事实 bug 外，不编辑已归档 MLF-1 到 MLF-8
  证据包。

## 计划派发

| Dispatch | Cluster | Owner | Packet | Status |
| --- | --- | --- | --- | --- |
| `MLF8-D1` | `MLF-8-P1` | read-only diagnostics worker | 盘点当前 structural breakup、lifecycle、event、binding、facade、diagnostics 和 reward 表面。 | complete / inventory-pass |
| `MLF8-D2` | `MLF-8-P2` | contract worker | 将 inventory 转成已验收 lifecycle rows、producers、consumers、visibility 和 forbidden outputs。 | complete / contract-pass |
| `MLF8-D3` | `MLF-8-P3` | integration worker | 实现已验收基础生命周期表达和聚焦 C++ 测试。 | complete / focused-pass |
| `MLF8-D4` | `MLF-8-P4/P5` | diagnostics/validation worker | 添加 facade/binding/probe 暴露和 reward non-leakage 测试。 | complete / focused-pass |
| `MLF8-D5` | `MLF-8-P6/P7` | main thread | 跑更广 smoke，更新状态，并作验收/归档决策。 | complete / accepted-archived |

## Ready Packet: MLF8-D1

```md
cluster: MLF-8-P1
mode: read-only diagnostics
goal: 盘点可支持 MLF-8 残骸/碎片生命周期的当前表面。
read:
- src/components/combat/structural_failure.h
- src/runtime/contracts/engagement_contracts.h
- src/components/systems/logistics.h
- src/systems/physics/ground_contact_system.h
- src/systems/combat/damage_system_air.h
- src/core/engine/simulation_kernel_engagement_event_store.*
- src/interfaces/python/bindings_runtime.cpp
- src/runtime/facade/**
- tools/diagnostics/**
- gym_envs/scenario_loader/reward_runtime/air_combat.py
- tests/runtime/air_combat/**
write:
- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_debris_wreck_lifecycle/*inventory*.md
- current status doc updates
non-goals:
- runtime edits
- reward edits
- Pk, calibration, selected debris-output authority
validation:
- cited source/test inventory
- git diff --check
```

结果：

```md
status: pass
touched files:
- missile_lethality_debris_wreck_lifecycle_inventory_20260619.md
- missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md
commands/outcomes:
- source inventory found reusable DTO/binding/facade surfaces
- source inventory found no lifecycle event writer
- source inventory found reward currently consumes lifecycle events without diagnostics-only filtering
remaining paths:
- P2 lifecycle contract
behavior risks:
- diagnostics-only lifecycle rows can leak into reward unless P2/P3 adds a guard
integration notes:
- base MLF-8 should stay a thin lifecycle-event layer first
```

## Ready Packet: MLF8-D2

```md
cluster: MLF-8-P2
mode: contract
goal: 将 P1 inventory 转成已验收 lifecycle rows 和 runtime 前置守卫。
read:
- missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md
- src/runtime/contracts/engagement_contracts.h
- src/core/interfaces/engagement_event_recorder.h
- src/core/engine/simulation_kernel_engagement_event_store.*
- gym_envs/scenario_loader/reward_runtime/air_combat.py
- tests/runtime/air_combat/test_air_combat_reward_surface.py
write:
- missile_lethality_debris_wreck_lifecycle_contract_20260619.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md
- current status doc updates
non-goals:
- runtime edits
- reward edits
- first-class debris ECS entities
- Pk、calibration、selected debris-output authority
validation:
- contract table inspection
- local markdown link check
- git diff --check
```

结果：

```md
status: pass
touched files:
- missile_lethality_debris_wreck_lifecycle_contract_20260619.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md
commands/outcomes:
- accepted LifecycleTransitionEvent as the base carrier
- rejected first-class debris/wreck ECS entities for the base slice
- required diagnostics-only visibility and reward non-leakage before enabling writers
remaining paths:
- P3 runtime representation
behavior risks:
- lifecycle rows must not double-count existing ground-crash reward shaping
integration notes:
- parent StructuralBreakupEvent remains the detached-part label source
```

## Ready Packet: MLF8-D3

```md
cluster: MLF-8-P3
mode: integration
goal: 实现已验收的 diagnostics-only 基础 lifecycle 表达。
read:
- missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md
- src/runtime/contracts/engagement_contracts.h
- src/core/interfaces/engagement_event_recorder.h
- src/core/engine/simulation_kernel_engagement_event_store.*
- src/systems/combat/structural_failure_system.h
- src/systems/physics/ground_contact_system.h
- gym_envs/scenario_loader/reward_runtime/air_combat.py
write:
- src/core/interfaces/engagement_event_recorder.h
- src/core/engine/simulation_kernel_engagement_event_store.*
- src/systems/combat/structural_failure_system.h
- src/systems/physics/ground_contact_system.h
- gym_envs/scenario_loader/reward_runtime/air_combat.py
- focused tests
non-goals:
- first-class debris/wreck ECS entities
- debris physics、Pk、calibration、selected debris-output authority
- diagnostics-only lifecycle rows 的 reward authority
validation:
- focused C++ lifecycle/structural tests
- targeted reward non-leakage pytest
- git diff --check
```

结果：

```md
status: pass
touched files:
- src/core/interfaces/engagement_event_recorder.h
- src/core/engine/simulation_kernel_engagement_event_store.*
- src/systems/combat/structural_failure_system.h
- src/systems/physics/ground_contact_system.h
- gym_envs/scenario_loader/reward_runtime/air_combat.py
- src/tests/test_structural_failure_system.cpp
- tests/runtime/air_combat/test_air_combat_reward_surface.py
commands/outcomes:
- cmake --build build-workshop --target ef_test -j 2 -> pass
- cmake --build build-workshop --target ef_py -j 2 -> pass
- ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure -> 4 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_engagement_contract_shape.py -> 48 passed
remaining paths:
- P4/P5 diagnostics/facade validation
behavior risks:
- terminal wreck lifecycle helper is chain-linked to structural evidence only; general ground crashes remain existing ground lifecycle behavior
integration notes:
- all emitted MLF-8 lifecycle rows are diagnostics_only
```

## Ready Packet: MLF8-D4

```md
cluster: MLF-8-P4/P5
mode: diagnostics/validation
goal: 通过维护中的 facade/binding/reward 表面验证 lifecycle rows。
read:
- src/runtime/facade/runtime_facade_types.h
- src/runtime/facade/runtime_facade_packet.cpp
- src/interfaces/python/bindings_runtime.cpp
- tests/runtime/bindings/test_bindings_engagement_surface.py
- tests/runtime/engagement/test_engagement_contract_shape.py
- tests/runtime/air_combat/test_air_combat_reward_surface.py
write:
- focused facade/binding/diagnostic tests if coverage gaps remain
- current status doc updates
non-goals:
- new runtime behavior
- broad reward redesign
- first-class debris/wreck ECS entities
validation:
- targeted binding/facade/engagement pytest
- structural CTest lane
- git diff --check
```

结果：

```md
status: pass
touched files:
- src/runtime/facade/runtime_facade_packet.cpp
- tools/diagnostics/lethality_chain_contract.py
- tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/*
- src/tests/test_structural_failure_system.cpp
- tests/runtime/air_combat/test_continuous_rod_surface.py
- tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py
- tests/runtime/bindings/test_bindings_engagement_surface.py
- tests/runtime/engagement/test_engagement_contract_shape.py
- tests/runtime/engagement/test_facade_engagement_evidence_gates.py
- tests/runtime/facade/test_runtime_facade_core.py
commands/outcomes:
- cmake --build build-workshop --target ef_py -j 2 -> pass
- cmake --build build-workshop --target ef_test -j 2 -> pass
- ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure -> 4 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/test_continuous_rod_surface.py tests/runtime/air_combat/test_warhead_component_event_surface.py tests/runtime/air_combat/test_air_combat_reward_surface.py tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_engagement_contract_shape.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/facade/test_runtime_facade_core.py -> 99 passed
- git diff --check -> pass
remaining paths:
- P6 broader smoke
- P7 acceptance/archive decision
behavior risks:
- lifecycle rows 继续保持 diagnostics-only；reward authority 继续拒绝
integration notes:
- facade packet append/sort 和 diagnostics probe row projection 现在包含 LifecycleTransitionEvent
```

## Ready Packet: MLF8-D5

```md
cluster: MLF-8-P6/P7
mode: smoke/acceptance
goal: 运行更广 smoke，然后验收/归档或明确 hold MLF-8。
read:
- README.zh.md
- missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md
- src/runtime/facade/runtime_facade_packet.cpp
- tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py
write:
- smoke 通过或 residual 明确保留后更新 current status 和 acceptance/archive docs
- acceptance decision 后才更新父级导航
non-goals:
- new runtime behavior
- reward authority、Pk、calibration、selected debris-output authority
- first-class debris/wreck ECS entities
validation:
- 从 touched surfaces 选择更广 targeted pytest/CTest smoke
- git diff --check
```

结果：

```md
status: pass
touched files:
- README.md
- README.zh.md
- missile_lethality_debris_wreck_lifecycle_acceptance_20260619.md
- missile_lethality_debris_wreck_lifecycle_acceptance_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_current_status_20260619.md
- missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md
- missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md
- missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.md
- missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.zh.md
- parent A2 README/archive registry 和 air-combat README files
commands/outcomes:
- ctest --test-dir build-workshop --output-on-failure -> 6 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests::test_live_controlled_geometry_varies_aspect_and_altitude_offset -vv -> 1 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py -> 11 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement -> 39 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement -> 386 passed
- git diff --check -> pass
remaining paths:
- MLF-9 Pk / 统计趋势投影仍是独立 follow-on
- MLF-10 校准和 selected debris-output 证据准入仍是独立 follow-on
behavior risks:
- high-altitude controlled-geometry smoke 现在显式预期 `fuze_no_detonation`，同时继续验证 geometry fields
integration notes:
- focused MLF-8 lanes 和 broader air-combat/engagement smoke 都干净；MLF-8
  已作为 diagnostics-only lifecycle evidence 归档
```

## Runtime 前置阻塞

- P1 inventory 已命名精确当前 owner 和缺口。
- P2 contract 已确定 event shape、writer ownership 和 `consumer_visibility`。
- lifecycle writers 启用前已实现 reward non-leakage。
