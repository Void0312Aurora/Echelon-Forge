# TM03 Launch Bridge Boundary Task Clusters

Status: closed task-cluster packet on `2026-05-25`.

This document is the finite dispatch surface for
[TM03 Launch Bridge Boundary](README.md). It exists to prevent the launch-bridge
residual from turning into an open-ended P7 redesign.

## 1. Boundary Rule

TM03 is limited to the two explicit release bridges:

- `src/systems/combat/pilot_weapon_release_system.h`
- `src/systems/naval/naval_mission_weapon_release_system.h`

The initial source fact is that both helpers include
`core/engine/simulation_kernel.h` and capture `SimulationKernel&`, while
`src/core/engine/simulation_kernel_systems.cpp` registers them with `*this`.

## 2. Cluster Plan

| Cluster | Status | Goal | Write scope | Non-goals | Validation | Dependency / round cap |
|---------|--------|------|-------------|-----------|------------|------------------------|
| `TM03-A Source Fact Freeze` | pass / recorded | Freeze the exact bridge facts and classify the residual. | TM03 docs only. | No code changes, no P7 redesign. | `rg -n "SimulationKernel&|core/engine/simulation_kernel.h|fire_.*weapon" src/systems src/core/engine`; source anchors in TM03 README. | Completed by this packet; no repair round. |
| `TM03-B Replacement Seam Decision` | pass / selected | Choose one narrow seam: launch service interface, component/event request, or another bounded option that removes `SimulationKernel&` from `systems/`. | `src/core/interfaces/weapon_release_service.h`, the two release helpers, `simulation_kernel_systems.cpp`, focused guard tests, and TM03 docs. | No P7 event queue, no implementation-copy of weapon selection, no runtime facade expansion. | Architecture review selected `IWeaponReleaseService` because `systems/` may consume `core/interfaces` contracts and existing weapon API behavior can stay centralized. | Completed in one design round. |
| `TM03-C Scoped Bridge Implementation` | pass | Remove direct `SimulationKernel` dependency from the two release system headers while preserving behavior. | `src/core/interfaces/weapon_release_service.h`; `src/core/engine/simulation_kernel.h`; `src/core/engine/simulation_kernel_systems.cpp`; `src/systems/combat/pilot_weapon_release_system.h`; `src/systems/naval/naval_mission_weapon_release_system.h`; `tests/architecture/structural_boundaries/test_structural_guardrails.py`; TM03 docs. | No weapon API rewrite, no damage/effects change, no command/tasking semantics migration. | `cmake --build build-workshop --target ef_py -j4` passed; focused air/naval weapon tests passed; architecture guard and grep confirmed no direct `SimulationKernel` helper dependency. | Completed in one implementation round. |
| `TM03-D Closure Or Block Record` | pass / closed | Publish pass or blocked state with residual ownership. | TM03 docs and simulation-architecture indexes only. | No extra implementation. | `git diff --check` passed; validation from `TM03-C` recorded in the TM03 README. | Closed serially after `TM03-C`. |

## 3. Dispatch Queue

| Dispatch | Cluster | Model / reasoning | Owner type | Write scope | Parallel-safe | Expected packet |
|----------|---------|-------------------|------------|-------------|---------------|-----------------|
| `TM03-B1 seam decision` | `TM03-B` | `gpt-5.4`, high | architecture/design worker or main thread | TM03 docs only | No; it selects the implementation boundary. | `status`, selected seam, rejected alternatives, file ownership, tests, residual risks. |
| `TM03-C1 bridge implementation` | `TM03-C` | `gpt-5.4`, high | implementation worker | Files named by `TM03-B` only | No; writes touch shared C++ runtime boundary. | `status`, touched files, commands/outcomes, behavior risks, integration notes. |
| `TM03-D1 closure record` | `TM03-D` | `gpt-5.4-mini`, xhigh | integration/docs worker | TM03 docs and indexes only | No; closure stays serial. | Final validation matrix or blocked record. |

## 4. Worker Packet Requirements

Every delegated result must return:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Rules:

- `partial` does not unlock implementation or closure.
- A blocked result must name owner, reason, replacement condition, validation gap,
  and forced review trigger.
- Implementation workers must not touch broader P7 weapon selection, damage, or
  effects logic unless TM03 is explicitly re-scoped.
