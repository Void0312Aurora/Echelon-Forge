# MLF-7 Secondary Consequence Coupling — Dispatch Queue

Status: `2026-06-18` updated dispatch queue. `MLF-7A-X1` through `MLF-7H-C1`
are closed for the accepted engineering-proxy MLF-7 slice.

Parent task clusters:
[missile_lethality_secondary_consequence_coupling_task_clusters_20260618.md](missile_lethality_secondary_consequence_coupling_task_clusters_20260618.md)

Current status:
[missile_lethality_secondary_consequence_coupling_current_status_20260618.md](missile_lethality_secondary_consequence_coupling_current_status_20260618.md)

## Queue Summary

| Packet | Cluster | Suggested owner | Dispatch state | Allowed write set | Validation / return gate |
| --- | --- | --- | --- | --- | --- |
| `MLF-7A-X1` | `MLF-7A Boundary And Index` | main thread | complete | subproject docs and parent README links | P0 docs exist and parent navigation links MLF-7 |
| `MLF-7B-X1` | `MLF-7B Consequence Inventory` | main thread | complete | `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md` | Inventory lists fact inputs, candidate writes, execution order, diagnostics, tests, and forbidden direct writes |
| `MLF-7C-X1` | `MLF-7C Coupling Contract` | main thread | complete | `missile_lethality_secondary_consequence_coupling_contract_20260618.md` | Contract maps each break mode to bounded consequence writes and cadence |
| `MLF-7D-W1` | `MLF-7D Runtime Bridge` | main thread | complete / focused-pass | `src/systems/combat/structural_consequence_system.h`, registration file, focused C++ tests | Runtime writes cite P2 contract rows and pass focused no-false-positive tests |
| `MLF-7E-W1` | `MLF-7E Loss-State And Consequence Diagnostics` | main thread | complete / event-pass | event-store interface/store, `StructuralBreakupState`, focused C++ tests | Diagnostics show chain-linked consequence deltas and loss-state transitions |
| `MLF-7F-T1` | `MLF-7F Focused Validation` | main thread | complete / focused-pass | `src/tests/test_structural_failure_system.cpp`, `CMakeLists.txt` | Named lane covers every break mode, no-breakup, idempotence, and direct-lifecycle refusal |
| `MLF-7G-C1` | `MLF-7G Regression Smoke` | main thread | complete / broad-pass | test execution notes; no oracle updates required | Broad lane green: 447 passed |
| `MLF-7H-C1` | `MLF-7H Acceptance And Archive Boundary` | main thread | complete / archived | docs/index and parent archive registry | Acceptance package updates status, residuals, parent navigation, and archive boundary |

## Dispatch Rules

- `MLF-7A-X1` through `MLF-7H-C1` are closed for the accepted slice.
- Future work should open MLF-8/9/10 packets rather than extending MLF-7 unless
  an MLF-7 regression is found.
- Follow [Subagent Usage Policy](../../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Packet Briefs

### `MLF-7B-X1` — Consequence Inventory

Dispatch state: complete.

Goal: produce a doc-only inventory that lets P2 decide exactly what MLF-7 may
read, what it may write, and what it must not touch.

Worker prompt:

```text
You are working in /home/void0312/Workshop/CMO on MLF-7B Consequence Inventory.
Do not edit runtime code. Do not create debris/wreck, Pk, weapon-specific,
training-reward, or direct-delete behavior. Read the MLF-7 README, current
status, task clusters, and dispatch queue first. Then write
missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md.

Inventory:
- MLF-6 fact inputs:
  src/components/combat/structural_failure.h
  src/runtime/contracts/engagement_contracts.h
  src/core/engine/engagement_event_types.h
  src/runtime/facade/runtime_facade_types.h
  tools/diagnostics/structural_breakup_export.py
- Candidate maintained consequence surfaces:
  src/components/domains/air/combat/damage_air.h
  src/components/combat/common/damage_common.h
  src/components/physics/performance.h
  src/components/physics/dynamics.h
  src/systems/combat/damage_system_air.h
  src/systems/combat/damage_system_common.h
  src/core/engine/simulation_kernel_systems.cpp
- Existing evidence to preserve:
  docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_structural_failure/README.md
  docs/systems/effects/reviews/damage_effect_chain_20260608/README.md

The inventory must include:
- every StructuralBreakupState field and helper MLF-7 may read;
- every StructuralBreakupEvent field MLF-7 may use for chain linkage or diagnostics;
- every candidate AircraftDamageState, PlatformDamageState, Health, FlightModel,
  Propulsion, Mass, Sensor, or event/probe surface MLF-7 might write;
- the current execution order of AircraftDamageStateUpdate and StructuralFailureUpdate;
- forbidden direct writes, including entity deletion, debris/wreck lifecycle, Pk,
  stock weapon truth, and training reward changes.

Return with status, touched files, commands/outcomes, remaining paths, behavior
risks, and integration notes.
```

Allowed writes:

- `missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md`
- Optional status-only edits to this dispatch queue and
  [current status](missile_lethality_secondary_consequence_coupling_current_status_20260618.md)
  after the inventory is complete.

Validation:

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling
```

Closure gate: inventory exists, all referenced paths are either linked or named
plainly, and P2 has enough information to decide approved writes.

### `MLF-7C-X1` — Coupling Contract

Dispatch state: complete.

Goal: define the approved consequence mapping before code. This packet is still
docs-only.

Required contract decisions:

- Map `wing_loss`, `tail_loss`, `engine_detach`, `fuselage_rupture`, and
  `multi_axis` to bounded consequence deltas.
- State whether MLF-7 writes `AircraftDamageState::structural_integrity`, other
  aircraft damage scalars, `PlatformDamageState` capabilities, or loss-state
  inputs.
- Decide cadence: accept a tested one-tick delay, or explicitly change pipeline
  order with tests.
- State no-breakup behavior and zero false-positive guard.
- State escalation rules for `MissionKill`, `MobilityKill`, `SensorKill`, and
  `Lost`, if any.

Allowed writes:

- `missile_lethality_secondary_consequence_coupling_contract_20260618.md`
- Optional status rows after contract review.

Validation:

```bash
git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_secondary_consequence_coupling
```

Closure gate: every runtime write planned for 7D cites a row in the contract.

### `MLF-7D-W1` — Runtime Bridge

Dispatch state: complete / focused-pass.

Goal: implement the narrow bridge from archived MLF-6 breakup facts to only the
P2-approved maintained consequence surfaces.

Likely write surfaces, subject to P2:

- `src/systems/combat/structural_consequence_system.h` or an approved adjacent
  combat-damage file.
- `src/core/engine/simulation_kernel_systems.cpp`.
- Focused C++ tests, preferably in `src/tests/test_structural_failure_system.cpp`
  or a new MLF-7-specific test file.

Mandatory return evidence:

- Each read field from `StructuralBreakupState` or `StructuralBreakupEvent`.
- Each written field and the exact P2 contract row authorizing it.
- Execution-order behavior and test evidence.
- Confirmation that no debris entity lifecycle, Pk projection, or direct entity
  deletion was added.

### `MLF-7E-W1` — Consequence Diagnostics

Dispatch state: complete / event-pass.

Goal: make the handoff visible without inventing new authority.

Possible write surfaces, subject to P2/P4:

- Event-store/facade surfaces that already carry engagement diagnostics.
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py` or a narrow
  adjacent diagnostic probe.
- Targeted Python tests under `tests/runtime/air_combat/` or `tests/tools/`.

Closure gate: diagnostics show the breakup fact, consequence delta, loss-state
transition if any, `chain_id`, and causal continuity without last-event guessing.
Satisfied by the chain-linked `platform_consequence` focused test.

### `MLF-7F-T1` — Focused Validation

Dispatch state: complete / focused-pass.

Goal: add named focused tests for MLF-7 behavior.

Required coverage:

- no-breakup produces zero MLF-7 consequence deltas;
- each single mode has the P2-approved bounded consequence;
- multi-axis behavior follows the P2 contract;
- irreversible upstream breakup state does not produce duplicate deltas unless
  P2 explicitly authorizes cadence;
- direct entity lifecycle remains absent.

Validation command will be finalized after 7D chooses the test lane. Expected
shape:

```bash
cmake --build build-workshop -j 2
ctest --test-dir build-workshop -R structural --output-on-failure
```

### `MLF-7G-C1` — Regression Smoke

Dispatch state: complete / broad-pass.

Goal: run broader maintained smoke lanes and separate inherited failures from
MLF-7 regressions.

Expected command:

```bash
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/
```

Closure gate: satisfied by
`PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
-> 447 passed.

### `MLF-7H-C1` — Acceptance And Archive Boundary

Dispatch state: complete.

Goal: close the package without overstating authority.

Allowed writes:

- MLF-7 README/status/task-cluster/dispatch/acceptance docs.
- Parent A2 and air-combat navigation docs.
- Archive movement completed after the explicit user request; parent registry
  now owns discovery for the closed packet.

Closure gate: accepted/retained/deferred boundaries are synchronized, MLF-8/9/10
residuals remain explicit, and the package does not claim real-world lethality,
Pk, weapon-specific truth, or debris/wreck lifecycle.

## Worker Packet Checklist

Every worker response must include:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Runtime packets must additionally cite the P2 contract row that authorizes each
consequence write.
