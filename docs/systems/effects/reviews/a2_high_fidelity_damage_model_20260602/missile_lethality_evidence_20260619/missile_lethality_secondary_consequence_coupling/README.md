# MLF-7 Secondary Consequence Coupling

Status: `2026-06-18` accepted / archived. P1 inventory, P2 contract, P3 bridge,
P4 chain-linked consequence diagnostics, P5 focused C++ validation, P6 broad
runtime smoke, and P7 acceptance are complete for the bounded MLF-7 slice.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 follow-on index: [../../README.md](../../README.md)
- MLF-1 chain contract and phase boundaries:
  [../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md)
- MLF-6 structural failure fact writer (accepted / archived upstream evidence):
  [../missile_lethality_structural_failure/README.md](../missile_lethality_structural_failure/README.md)
- MLF-6 acceptance gate and deferred authorities:
  [../missile_lethality_structural_failure/missile_lethality_structural_failure_acceptance_20260617.md](../missile_lethality_structural_failure/missile_lethality_structural_failure_acceptance_20260617.md)
- A8 damage-effect chain accepted evidence:
  [../../../archive/a8_damage_effect_chain/README.md](../../../../../../../README.md)
- Subproject creation standard:
  [../../../../../agent/rules/subproject_creation_standard.md](../../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Realism authority boundary:
  ../../../../../standards/foundation/realism_authority_boundary.zh.md（`git show e8dc0b29~1:docs/standards/foundation/realism_authority_boundary.zh.md`）
- Structural breakup state:
  [../../../../../../src/components/combat/structural_failure.h](../../../../../../../src/components/combat/structural_failure.h)
- Aircraft damage and maintained consumers:
  [../../../../../../src/systems/combat/damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h)
- Loss-state helper:
  [../../../../../../src/systems/combat/damage_system_common.h](../../../../../../../src/systems/combat/damage_system_common.h)
- Pipeline registration:
  [../../../../../../src/core/engine/simulation_kernel_systems.cpp](../../../../../../../src/core/engine/simulation_kernel_systems.cpp)

## Purpose

MLF-7 is the seventh phase of the Missile Lethality Framework. Its job is to
consume the named breakup facts produced by MLF-6 and couple them into bounded
aircraft consequences through maintained simulation paths.

MLF-6 answers: "which structural part broke, in which mode, and with what
traceable cause?" MLF-7 answers the next question: "how should that breakup
change the aircraft's structural envelope, flight/control/propulsion capability,
platform loss state, and downstream diagnostic record?"

This is not a new direct-kill switch. Consequences must stay routed through
existing aircraft damage, flight, propulsion, platform-damage, and diagnostic
surfaces unless a future phase explicitly replaces those contracts.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-6 structural breakup facts | accepted / archived upstream input | `StructuralBreakupState` ECS component and `StructuralBreakupEvent` rows exist; focused and broad MLF-6 validation are green | MLF-6 still does not modify aero, `structural_integrity`, or loss state |
| `StructuralBreakupState` | active input | `src/components/combat/structural_failure.h` stores irreversible breakup state, active break modes, active structural groups, detached count, `airframe_breakup`, and the last emitted breakup event id | State is a fact source; MLF-7 consumes it through the bounded bridge rather than a direct kill path |
| `StructuralBreakupEvent` | active diagnostic input | MLF-6 event writer exports breakup rows with `chain_id`, `parent_event_id`, `cause_event_id`, break mode, and detached-part label | Events are records, not a reactive control signal by themselves |
| Aircraft damage scalar path | active maintained consumer | `damage_system_air.h` maps `AircraftDamageState` into `FlightModel`, `Propulsion`, `Sensor`, `Mass`, and `PlatformDamageState` | Existing scalar response is synthetic and not aircraft-specific control-law calibration |
| Loss-state path | active maintained consumer | `sync_platform_damage_loss_state` maps platform capabilities and HP to `CombatCapable`, mission/sensor/mobility kills, or `Lost` | MLF-7 must not silently create a new direct entity-destruction path |
| A8 damage-effect chain | archived accepted evidence | propulsion, wing/control aero, fuel/mass, fire, sensor/data-link, and original-entity ground-contact responses are observable | A8 explicitly deferred first-class debris/residue objects and real-world lethality authority |

## Scope

In scope:

- Inventory every current surface MLF-7 may read or write:
  `StructuralBreakupState`, `StructuralBreakupEvent`, `AircraftDamageState`,
  `FlightModel`, `Propulsion`, `PlatformDamageState`, `Health`, and maintained
  diagnostics.
- Define a bounded consequence contract for each MLF-6 break mode:
  `wing_loss`, `tail_loss`, `engine_detach`, `fuselage_rupture`, and
  `multi_axis`.
- Decide the cadence and registration point for the bridge from breakup facts to
  aircraft consequence state, including the known ordering issue that
  `AircraftDamageStateUpdate` currently runs before `StructuralFailureUpdate`.
- Implement consequence coupling through maintained aircraft damage paths, not
  through a separate one-off kill rule.
- Add focused C++ tests for no-breakup, each single break mode, multi-axis,
  irreversible state, loss-state escalation, and zero false positives.
- Add diagnostics that make the consequence handoff visible by `chain_id` and
  by target entity.
- Keep acceptance language at engineering-proxy level unless new authority
  evidence is admitted through a later calibration gate.

Out of scope:

- No wreck/debris entity lifecycle. Detached part labels become world entities
  only in MLF-8.
- No Pk or statistical lethality trend authority. That belongs to MLF-9.
- No weapon-specific or aircraft-specific calibration authority. That belongs
  to MLF-10 or a future calibration gate.
- No reopening of sealed MLF-1 through MLF-5 archives.
- No reopening of MLF-6 except to fix upstream fact bugs.
- No direct `e.destruct()` or target deletion outside maintained platform
  damage/loss-state paths.
- No stock AIM-120C, MQ-9, F-16C, naval, or ground-platform lethality claim.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Write surface | Status |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | Open the MLF-7 subproject, freeze non-goals, and link parent navigation. | User request to start considering MLF-7 and build the subproject. | README, task clusters, current status, dispatch queue, acceptance draft, and archive placeholder exist; parent READMEs link MLF-7. | docs only | complete |
| `P1 Consequence Inventory` | Inventory every input fact and every candidate consequence surface. | P0 docs exist. | Inventory lists read/write candidates, current owner, execution order, and forbidden direct-write surfaces. | docs only | complete |
| `P2 Coupling Contract` | Define the break-mode to consequence mapping and cadence. | P1 inventory complete. | Contract table states what each break mode may do to aircraft damage scalars, platform capability, and loss state. | docs only | complete |
| `P3 Runtime Bridge` | Implement the bounded bridge from structural breakup facts to aircraft consequence state. | P2 contract accepted. | Runtime consumes `StructuralBreakupState` and updates only approved maintained consequence surfaces. | `src/systems/combat/*`, `src/core/engine/simulation_kernel_systems.cpp`, focused C++ tests | complete / focused-pass |
| `P4 Consequence Events And Diagnostics` | Make the handoff visible in recent events/probes without inventing new authority. | P3 bridge passes focused tests. | Diagnostics show breakup fact, consequence deltas, loss-state transition, and chain linkage through `PlatformConsequenceEvent`. | event store / diagnostics / tests | complete / event-pass |
| `P5 Focused Validation` | Validate each break mode and no-false-positive guard. | P3 complete. | Named CTest lane covers no-breakup, wing loss, multi-axis, idempotence, same-tick bridge, and no direct entity lifecycle. | focused tests | complete / focused-pass |
| `P6 Regression Smoke` | Confirm broader air-combat and world-batch behavior is not accidentally rewritten. | P5 focused lanes pass. | Full maintained smoke lanes are green, with adjacent engagement/facade/binding tests green. | tests only | complete / broad-pass |
| `P7 Acceptance` | Sync docs, parent navigation, residuals, and archive boundary. | P6 complete or residuals explicitly held. | Acceptance package states exactly what MLF-7 proves and what remains deferred to MLF-8/9/10. | docs only | complete |

## Task Clusters

- Task cluster plan:
  [missile_lethality_secondary_consequence_coupling_task_clusters_20260618.md](missile_lethality_secondary_consequence_coupling_task_clusters_20260618.md)
- Current status:
  [missile_lethality_secondary_consequence_coupling_current_status_20260618.md](missile_lethality_secondary_consequence_coupling_current_status_20260618.md)
- Consequence inventory:
  [missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md](missile_lethality_secondary_consequence_coupling_consequence_inventory_20260618.md)
- Coupling contract:
  [missile_lethality_secondary_consequence_coupling_contract_20260618.md](missile_lethality_secondary_consequence_coupling_contract_20260618.md)
- Dispatch queue:
  [missile_lethality_secondary_consequence_coupling_dispatch_queue_20260618.md](missile_lethality_secondary_consequence_coupling_dispatch_queue_20260618.md)
- Acceptance gate:
  [missile_lethality_secondary_consequence_coupling_acceptance_20260618.md](missile_lethality_secondary_consequence_coupling_acceptance_20260618.md)

## Outputs And Evidence

Current outputs:

- P1 inventory of current fact inputs, consequence write candidates, and
  registration-order constraints.
- P2 coupling contract for each break mode and loss-state escalation condition.
- P3 runtime bridge consuming `StructuralBreakupState` through
  [structural_consequence_system.h](../../../../../../../src/systems/combat/structural_consequence_system.h).
- P4 event diagnostics linking structural-breakup parent events to
  `platform_consequence` records with before/after consequence deltas.
- P5 focused C++ tests and `structural_consequence` CTest lane.
- P6 broad runtime smoke evidence:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  -> 447 passed.
- Adjacent event/facade/binding/tool evidence:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
  -> 160 passed.
- P7 acceptance package with residuals explicitly deferred to MLF-8, MLF-9, and
  MLF-10.

Remaining outputs are follow-on phases only: MLF-8 debris/wreck lifecycle,
MLF-9 Pk/statistical trend projection, and MLF-10 calibration gates.

## Acceptance Gate

This subproject is accepted for the engineering-proxy MLF-7 slice because:

- MLF-6 accepted / archived evidence remains available as the upstream fact
  source.
- The P1 inventory and P2 coupling contract are complete and internally linked.
- Runtime changes, if any, consume MLF-6 facts and write only approved
  consequence surfaces.
- Focused tests prove each break mode has the expected bounded consequence and
  no-breakup cases remain unchanged.
- Broad air-combat/world-batch smoke remains green or residuals are documented
  as outside MLF-7.
- Documentation continues to refuse debris/wreck lifecycle, Pk authority,
  weapon-specific calibration, and real-world lethality claims.

## Residuals And Next Steps

Follow-on:

- MLF-8: debris/wreck lifecycle from `detached_part_ref` labels.
- MLF-9: Pk/statistical trend projection.
- MLF-10: calibration gates for specific weapons/platforms.

Deferred:

- Naval and ground structural consequence models.
- Direct crash/deletion rules outside the maintained platform damage lifecycle.

## Archive

MLF-7 has been physically archived under the parent A2 local archive and
registered in [../../archive_registry.md](../../../../../../task/review/archive/phase3c_closeout_20260808/archive_registry.md). The local
[archive/](archive/README.md) directory remains only for future superseded
records within this archived evidence packet.
