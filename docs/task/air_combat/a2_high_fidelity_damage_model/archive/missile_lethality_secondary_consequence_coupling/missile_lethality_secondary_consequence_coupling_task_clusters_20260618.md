# MLF-7 Secondary Consequence Coupling — Task Clusters

Status: `2026-06-18` finite task-cluster plan for
[README.md](README.md). P0-P7 are complete for the accepted engineering-proxy
MLF-7 slice; MLF-8/9/10 remain explicit follow-ons.

## Boundary Decision

This subproject advances MLF-7 only: secondary consequence coupling from MLF-6
breakup facts into maintained aircraft consequence surfaces. It may consume
`StructuralBreakupState` and `StructuralBreakupEvent`; it may write only the
consequence surfaces approved by P2.

It must not:

- Create wreck/debris entities or detach ECS entities. That is MLF-8.
- Implement Pk/statistical trends. That is MLF-9.
- Claim real weapon, AIM-120C, MQ-9, F-16C, naval, or ground lethality truth.
- Reopen sealed MLF-1 through MLF-5 archives.
- Add a direct kill or direct `e.destruct()` path outside maintained platform
  damage/loss-state logic.
- Treat archived MLF-6 acceptance evidence as MLF-7 implementation evidence.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-7A Boundary And Index` | main thread | n/a | Create MLF-7 subproject entry with README, task clusters, current status, dispatch queue, acceptance draft, archive placeholder, and parent navigation. | `docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_secondary_consequence_coupling/**`, parent README files | runtime edits, implementation claims | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_secondary_consequence_coupling docs/task/air_combat/a2_high_fidelity_damage_model/README*.md docs/task/air_combat/README*.md` | future agents can resume MLF-7 without chat history; P0 scope and non-goals are explicit | first, serial | 1 | complete |
| `MLF-7B Consequence Inventory` | main thread | n/a | Inventory MLF-7 inputs, candidate write surfaces, execution order, and forbidden direct-write paths. | `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md` | runtime edits | referenced paths exist; inventory lists `StructuralBreakupState`, `StructuralBreakupEvent`, `AircraftDamageState`, downstream consumers, `PlatformDamageState`, `Health`, and forbidden write surfaces | inventory complete; P2 can decide approved coupling | after 7A; serial | 1 | complete |
| `MLF-7C Coupling Contract` | main thread | n/a | Define break-mode to consequence mapping for `wing_loss`, `tail_loss`, `engine_detach`, `fuselage_rupture`, and `multi_axis`; decide cadence and loss-state thresholds. | `missile_lethality_secondary_consequence_coupling_contract_20260618.md` | runtime edits, calibration claims | doc review; every mode has explicit bounded effect and no-breakup guard; registration-order choice is recorded | contract accepted before code | after 7B; serial | 2 | complete |
| `MLF-7D Runtime Bridge` | main thread | n/a | Implement a bounded bridge from `StructuralBreakupState` to approved aircraft consequence state. | `src/systems/combat/structural_consequence_system.h`, `src/core/engine/simulation_kernel_systems.cpp`, focused tests | debris entities, Pk, stock lethality, direct deletion | focused C++ tests for no-breakup, wing loss, multi-axis, idempotence, same-tick bridge; build passes | approved surfaces update only through P2 contract; no false positives | after 7C; serial | 3 | complete / focused-pass |
| `MLF-7E Loss-State And Consequence Diagnostics` | main thread | n/a | Make consequence deltas and loss-state transitions visible with stable chain linkage. | event-store interface/store, `StructuralBreakupState`, focused C++ tests | training reward changes, Pk projection | tests show `chain_id` continuity from MLF-6 facts through consequence diagnostics | diagnostics can answer what changed and why without last-event guessing | after 7D | 2 | complete / event-pass |
| `MLF-7F Focused Validation` | main thread | n/a | Add named focused lanes covering no-breakup, break-mode consequences, multi-axis, irreversible state, loss-state escalation, and no direct entity lifecycle. | `src/tests/test_structural_failure_system.cpp`, `CMakeLists.txt` | broad oracle rewrites, training changes | `ctest --test-dir build-workshop -R 'structural_consequence|structural_failure' --output-on-failure` | focused lanes prove initial MLF-7 behavior and no false positives | after 7D | 2 | complete / focused-pass |
| `MLF-7G Regression Smoke` | main thread | n/a | Run broader air_combat/world_batch lanes and separate inherited residuals from MLF-7 regressions. | test execution; only obsolete-oracle updates if justified | new features | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` -> 447 passed | broad lanes green or documented as inherited/non-MLF-7 | after 7E+7F; serial | 2 | complete / broad-pass |
| `MLF-7H Acceptance And Archive Boundary` | main thread | n/a | Summarize evidence, update current status and parent navigation, record residuals for MLF-8/9/10, and prepare archive boundary. | docs/index only unless explicit archive instruction | archive movement without approval, overclaiming | docs diff check; focused and broad commands recorded | accepted package is honest and bounded | after 7G; serial | 1 | complete |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- `MLF-7B` and `MLF-7C` are mandatory before runtime writes.
- Do not allow two workers to edit the same coupling table, event contract, or
  loss-state rule concurrently.
- `MLF-7D` is serial after the contract. `MLF-7E` and `MLF-7F` may parallelize
  only if the write sets stay distinct.
- `MLF-7G` and `MLF-7H` are closed for this accepted slice.
- If a cluster exceeds its round cap, stop and re-scope before adding a new wave.
- Follow [Subagent Usage Policy](../../../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

For runtime clusters, packets must also include:

- Every `StructuralBreakupState` or `StructuralBreakupEvent` field read.
- Every `AircraftDamageState`, `PlatformDamageState`, `Health`, `FlightModel`,
  or `Propulsion` field written, with the P2 contract row that authorizes it.
- The execution-order/cadence decision and its test evidence.
- Confirmation that no debris entity lifecycle, Pk projection, or direct
  deletion rule was added.

## Validation Plan

Initial validation commands:

```bash
# Docs-only P0
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/archive/missile_lethality_secondary_consequence_coupling \
  docs/task/air_combat/a2_high_fidelity_damage_model/README*.md \
  docs/task/air_combat/README*.md

# Runtime implementation phases, once added
cmake --build build-workshop -j 2
ctest --test-dir build-workshop -R structural --output-on-failure
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/
```

## Acceptance Criteria

- [x] `MLF-7A`: subproject entry and parent navigation exist.
- [x] `MLF-7B`: consequence inventory complete.
- [x] `MLF-7C`: coupling contract accepted before code.
- [x] `MLF-7D`: runtime bridge consumes MLF-6 facts and writes only approved
  consequence surfaces.
- [x] `MLF-7E`: diagnostics show chain-linked consequence deltas.
- [x] `MLF-7F`: focused lanes cover the initial bridge, no-breakup guard, and
  no direct entity lifecycle.
- [x] `MLF-7G`: broader smoke is green or residuals are separated.
- [x] `MLF-7H`: residuals and archive boundary are synchronized.

## Residual Map

Follow-on:

- MLF-8: debris/wreck entity lifecycle.
- MLF-9: Pk/statistical trend projection.
- MLF-10: calibration gates for specific weapons/platforms.

Deferred:

- Naval and ground structural consequences.
- Real-world lethality authority.
