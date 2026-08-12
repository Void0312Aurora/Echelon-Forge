# MLF-8 Dispatch Queue

Status: `2026-06-19` accepted / archived dispatch record for MLF-8 work.
MLF8-D1 is complete / inventory-pass, MLF8-D2 is complete / contract-pass,
MLF8-D3 is complete / focused-pass, MLF8-D4 is complete / focused-pass, and
MLF8-D5 is complete / accepted-archived. No worker is currently running.

Chinese companion:
[missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.zh.md).

## Queue Policy

- Do not create a new session thread.
- Dispatch only one write-capable runtime worker at a time.
- P1 and P2 may be prepared as read-only/document work, but P3 must wait for an
  accepted P2 contract.
- Do not edit archived MLF-1 through MLF-8 evidence packets except for broken
  links or explicitly confirmed upstream fact bugs.

## Planned Dispatches

| Dispatch | Cluster | Owner | Packet | Status |
| --- | --- | --- | --- | --- |
| `MLF8-D1` | `MLF-8-P1` | read-only diagnostics worker | Inventory current structural breakup, lifecycle, event, binding, facade, diagnostics, and reward surfaces. | complete / inventory-pass |
| `MLF8-D2` | `MLF-8-P2` | contract worker | Convert inventory into accepted lifecycle rows, producers, consumers, visibility, and forbidden outputs. | complete / contract-pass |
| `MLF8-D3` | `MLF-8-P3` | integration worker | Implement the accepted base lifecycle representation and focused C++ tests. | complete / focused-pass |
| `MLF8-D4` | `MLF-8-P4/P5` | diagnostics/validation worker | Add facade/binding/probe exposure and reward non-leakage tests. | complete / focused-pass |
| `MLF8-D5` | `MLF-8-P6/P7` | main thread | Run broad smoke, update status, and make acceptance/archive decision. | complete / accepted-archived |

## Ready Packet: MLF8-D1

```md
cluster: MLF-8-P1
mode: read-only diagnostics
goal: Inventory current surfaces that can support MLF-8 debris/wreck lifecycle.
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
- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_debris_wreck_lifecycle/*inventory*.md
- current status doc updates
non-goals:
- runtime edits
- reward edits
- Pk, calibration, selected debris-output authority
validation:
- cited source/test inventory
- git diff --check
```

Result:

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
goal: Convert P1 inventory into accepted lifecycle rows and pre-runtime guards.
read:
- missile_lethality_debris_wreck_lifecycle_inventory_20260619.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.md
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
- Pk, calibration, selected debris-output authority
validation:
- contract table inspection
- local markdown link check
- git diff --check
```

Result:

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
goal: Implement the accepted diagnostics-only base lifecycle representation.
read:
- missile_lethality_debris_wreck_lifecycle_contract_20260619.md
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
- debris physics, Pk, calibration, selected debris-output authority
- reward authority for diagnostics-only lifecycle rows
validation:
- focused C++ lifecycle/structural tests
- targeted reward non-leakage pytest
- git diff --check
```

Result:

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
goal: Validate lifecycle rows through maintained facade/binding/reward surfaces.
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

Result:

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
- lifecycle rows remain diagnostics-only; reward authority remains refused
integration notes:
- facade packet append/sort and diagnostics probe row projection now include LifecycleTransitionEvent
```

## Ready Packet: MLF8-D5

```md
cluster: MLF-8-P6/P7
mode: smoke/acceptance
goal: Run broader smoke, then accept/archive or explicitly hold MLF-8.
read:
- README.md
- missile_lethality_debris_wreck_lifecycle_current_status_20260619.md
- missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md
- missile_lethality_debris_wreck_lifecycle_contract_20260619.md
- src/runtime/facade/runtime_facade_packet.cpp
- tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py
write:
- current status and acceptance/archive docs if smoke passes or residuals are held
- parent navigation only after acceptance decision
non-goals:
- new runtime behavior
- reward authority, Pk, calibration, selected debris-output authority
- first-class debris/wreck ECS entities
validation:
- broader targeted pytest/CTest smoke chosen from touched surfaces
- git diff --check
```

Result:

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
- parent A2 README/archive registry and air-combat README files
commands/outcomes:
- ctest --test-dir build-workshop --output-on-failure -> 6 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py::GeometryAndEdgeCaseTests::test_live_controlled_geometry_varies_aspect_and_altitude_offset -vv -> 1 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py -> 11 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement -> 39 passed
- PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement -> 386 passed
- git diff --check -> pass
remaining paths:
- MLF-9 Pk/statistical trend projection remains a separate follow-on
- MLF-10 calibration and selected debris-output evidence remain separate follow-ons
behavior risks:
- high-altitude controlled-geometry smoke now explicitly expects `fuze_no_detonation` while still validating geometry fields
integration notes:
- focused MLF-8 lanes and broader air-combat/engagement smoke are clean; MLF-8
  is archived as diagnostics-only lifecycle evidence
```

## Blockers Before Runtime

- P1 inventory names exact current owners and gaps.
- P2 contract settles event shape, writer ownership, and `consumer_visibility`.
- Reward non-leakage is implemented before lifecycle writers are enabled.
