# TM03 Launch Bridge Boundary Task Clusters

Status: active task-cluster packet opened on `2026-05-25`.

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
| `TM03-B Replacement Seam Decision` | open | Choose one narrow seam: launch service interface, component/event request, or another bounded option that removes `SimulationKernel&` from `systems/`. | Docs first; optional small design note under TM03 only. | No implementation until the seam decision names file ownership and tests. | Architecture review of source anchors and affected tests. | Serial next step; one design round. |
| `TM03-C Scoped Bridge Implementation` | gated | Remove direct `SimulationKernel` dependency from the two release system headers while preserving behavior. | Expected candidate files only after `TM03-B`: the two release system headers, a narrow core/interface or event/request file, `simulation_kernel_systems.cpp`, and focused tests. | No weapon API rewrite, no damage/effects change, no command/tasking semantics migration. | `cmake --build build-workshop --target ef_py -j4`; focused air/naval weapon tests; architecture grep guard that `src/systems/**release_system.h` does not include `core/engine/simulation_kernel.h`. | Gated after `TM03-B`; at most two implementation rounds before re-scope. |
| `TM03-D Closure Or Block Record` | gated | Publish pass or blocked state with residual ownership. | TM03 docs and index only. | No extra implementation. | `git diff --check`; validation from `TM03-C` or blocked evidence from `TM03-B`. | Serial final cluster. |

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
