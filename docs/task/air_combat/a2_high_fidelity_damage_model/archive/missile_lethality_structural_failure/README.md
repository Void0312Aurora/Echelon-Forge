# MLF-6 Structural Failure And Airframe Breakup

Status: `2026-06-18` accepted / archived MLF-6 v10 evidence. P1/P2 design,
P3 state machine, P4 event writer, P5 diagnostics export, P6 focused
validation, and P7 broader regression are implemented with evidence. P7 passes
the full `tests/runtime/air_combat/` + `tests/world_batch/` lane after
obsolete-oracle updates. v10 additionally fixes the close continuous-rod
near-field model so structural cut-mode severity is visible to the breakup
state machine and retained proxy standoff reports show beam-side wing-loss
events through 4 m, while 8 m and 14 m remain non-breakup. The package is now
physically archived under the local A2 registry by explicit user instruction.

Language:

- English canonical: [README.md](README.md)
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 task index: [../../README.md](../../README.md)
- MLF-1 chain contract (authoritative MLF phase definitions and boundaries):
  [../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md)
- MLF-5 component failure archive (upstream output, the only MLF-6 consumption surface):
  [../missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.md](../missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/README.md)
- A2 target geometry retained follow-on (F-16C 32-component receiver map):
  [../../missile_lethality_target_geometry/README.md](../../missile_lethality_target_geometry/README.md)
- A8 damage effect chain (existing fire/fuel/sensor/engine propagation MLF-7 will extend):
  [../../../archive/a8_damage_effect_chain/README.md](../../../archive/a8_damage_effect_chain/README.md)
- F-16C unit database (current component definitions MLF-6 must classify):
  [../../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json)
- Subproject creation standard:
  [../../../../../agent/rules/subproject_creation_standard.md](../../../../../agent/rules/subproject_creation_standard.md)
- Realism authority boundary:
  [../../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../../standards/foundation/realism_authority_boundary.zh.md)
- Structural breakup contract and runtime writer:
  [../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h)
  (`StructuralBreakupEvent`, lines 213-221)
- Engagement event types:
  [../../../../../../src/core/engine/engagement_event_types.h](../../../../../../src/core/engine/engagement_event_types.h)
  (`RecentEngagementEvents::structural_breakup_events`)
- MLF-5 component damage state (live ECS component, MLF-6 consumption surface):
  [../../../../../../src/components/combat/common/damage_common.h](../../../../../../src/components/combat/common/damage_common.h)
  (`ComponentDamageState`)
- Aircraft damage system (where MLF-6 system registers):
  [../../../../../../src/systems/combat/damage_system_air.h](../../../../../../src/systems/combat/damage_system_air.h)
  (`AircraftDamageStateUpdate` — line 344)

## Purpose

MLF-6 is the sixth phase of the Missile Lethality Framework. Its single
deliverable is the **Structural Breakup Fact Writer**: a mechanism that reads
accumulated MLF-5 component-damage state from the live ECS and writes
`StructuralBreakupEvent` rows into the existing event store, with traceable
causation via `cause_event_id`.

Currently the simulation reduces all structural damage to a scalar
`structural_integrity` (1.0 → 0.0). A wing-spar fracture and an engine-core
fracture both subtract from the same scalar, producing identical downstream
behavior. MLF-6 replaces this undifferentiated degradation with named,
component-aware breakup facts: *which* structural group failed, in *what* mode,
to *what* degree.

### What MLF-6 explicitly does NOT do

The MLF-1 contract assigns flight-dynamics consequences to
**MLF-7 (Secondary Consequence Coupling)**, whose entry condition is MLF-6
acceptance. MLF-6 writes facts; MLF-7 consumes them. Specifically, MLF-6 does
not:

- Modify `aerodynamics_system.h` lift/drag/pitch/yaw/roll/thrust modifiers.
- Modify `AircraftDamageState` scalar fields (`structural_integrity`,
  `flight_control_integrity`, `propulsion_integrity`, etc.).
- Add or change loss-state classification rules.
- Bridge breakup state to flight dynamics in any form.

These all belong in MLF-7, where the MLF-1 contract authorizes `damage/air`
write surfaces. MLF-6's write surface is `damage/physics` only.

MLF-6 is the bottleneck that unblocks both MLF-7 and MLF-8. Without named
breakup facts, neither flight-dynamics coupling nor wreck/debris lifecycle can
begin.

## Critical Design Decisions (P0 — Frozen)

These decisions were debated during P0 self-review and are now frozen. Any
revision must reopen P0.

### D1: MLF-6 consumes live ECS `ComponentDamageState`, not event-store rows

MLF-5's `ComponentDamageEvent` is a diagnostic/recording artifact written after
the fact. The live truth is `ComponentDamageState` on each aircraft entity,
updated every timestep by `AircraftDamageStateUpdate`. MLF-6 reads this ECS
component directly.

Rationale: the event store is a log, not a reactive signal. Tracking cumulative
damage from event rows would require MLF-6 to replay history. Reading the live
ECS component gives per-timestep cumulative state for free.

### D2: MLF-6 does not modify any *existing* ECS component; writes a *new* one

The existing `structural_integrity` scalar remains untouched by MLF-6. It
continues to degrade via `accumulate_aircraft_structural_envelope_damage` and
`default_effects_air_domain.h`. MLF-6 adds breakup facts as a parallel,
component-aware stream via two new outputs: a `StructuralBreakupState` ECS
component (D7) and `StructuralBreakupEvent` rows (event store).

MLF-7 will later decide whether to:
- Read breakup events and set `structural_integrity` as a function of breakup
  state, or
- Read breakup events directly and bypass the scalar for flight-dynamics
  clamping.

### D3: `detached_part_ref` is a diagnostic string label, not a world entity reference

`StructuralBreakupEvent::detached_part_ref` is a stable string identifier
(e.g. `"left_wing"`, `"right_stabilator"`, `"engine_core"`). MLF-6 does not
create, destroy, or detach ECS entities. MLF-8 will later consume these labels
to create persistent wreck/debris entities.

### D4: Breakup state machine is per-airframe, cumulative, and irreversible

Structure can only degrade forward: `intact` → `partial_detachment` →
`partial_breakup` → `full_breakup`. Once a break mode is asserted, it stays
asserted. Multiple break modes can be active simultaneously (e.g. wing_loss +
engine_detach). A single timestep can transition through multiple states if
the cumulative component damage warrants it.

### D5: Integration point — new ECS system after `AircraftDamageStateUpdate`

MLF-6 registers a new `OnUpdate` system (`StructuralFailureUpdate`) that runs
after `AircraftDamageStateUpdate` in the same phase. It reads
`ComponentDamageState` (already updated by the damage system). It writes two
outputs: a new ECS component `StructuralBreakupState` (D7) and
`StructuralBreakupEvent` rows into `RecentEngagementEvents`.

### D6: Loss-state interaction is deferred to MLF-7

MLF-6 writes `StructuralBreakupEvent` facts and `StructuralBreakupState` (D7).
It does not touch `PlatformDamageState::loss_state`, `Health::current_hp`, or
`sync_platform_damage_loss_state`. Whether `full_breakup` implies `Lost` is
MLF-7's decision, not MLF-6's.

### D7: Irreversible breakup state is stored in a new ECS component `StructuralBreakupState`

The per-airframe irreversible state machine (D4) is persisted in a **new**
ECS component `StructuralBreakupState`, attached to the aircraft entity.
This component holds `breakup_state` and the active `break_mode` bitmask,
and is updated each tick by `StructuralFailureUpdate`.

This is the only mechanism that satisfies all requirements:
- **Irreversible by construction**: the component values only transition forward;
  there is no code path that reverts `full_breakup` → `intact`.
- **Survives world-batch serialization**: as a standard ECS component, it is
  included in snapshot/restore cycles without custom logic.
- **Survives save/load and replay**: the component is part of the ECS world state.
- **Queryable by downstream systems**: MLF-7 can `get<StructuralBreakupState>()`
  without parsing event-store history.
- **Clear reset semantics**: entity destruction removes the component; entity
  creation starts at `breakup_state = intact`.

`StructuralBreakupState` is NOT a replacement for `structural_integrity`; the
scalar continues to exist and degrade independently. MLF-7 decides how to
reconcile the two (D2).

This component should be defined in a new header
`src/components/combat/structural_failure.h` (or an adjacent path consistent
with the project's component layout).

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-5 component damage | accepted / archived | `ComponentDamageState` ECS component maintains cumulative per-component integrity, redundancy availability, and failure modes | Does not claim structural breakup |
| `StructuralBreakupEvent` contract | active / writer connected | `engagement_contracts.h` — `breakup_state`, `break_mode`, `detached_part_ref`, `detached_part_count`, `airframe_breakup`, `cause_event_id`; `structural_failure_system.h` writes transition events | MLF-6 facts only; no aero/loss coupling |
| `structural_breakup_events` vector | active / populated by P4 writer | `engagement_event_types.h`; `simulation_kernel_engagement_event_store.cpp`; facade + Python bindings pass through; `tools/diagnostics/structural_breakup_export.py` exports rows; `structural_failure_break_modes` validates break-mode coverage | Collector stores breakup facts; P7 broad regression is green; MLF-6 still does not consume aero/loss-state authority |
| Near-field cumulative wing-loss rule | active / calibrated in v10 | `structural_failure_system.h`; `structural_failure_state`, `structural_failure_break_modes`, and `test_continuous_rod_surface.py`; `target_geometry_proxy_standoff_grid_probe_20260615.json` reports 43 structural breakup records: blast_fragmentation 3, continuous_rod 40; continuous_rod beam-side 0.5/1/2/4 m records break, 8/14 m records do not | Engineering proxy only; no real weapon structural-kill or Pk authority |
| `structural_integrity` scalar | active / untouched by MLF-6 | `damage_air.h:114`; degrades via `accumulate_aircraft_structural_envelope_damage` and `default_effects_air_domain.h` | MLF-6 does not read or write this field |
| `ComponentDamageState` (ECS) | active / MLF-6 consumption surface | `damage_common.h:171-` — `component_integrity`, `component_failure_mode`, `redundancy_group_availability`, `has_fire_suppression_components` | MLF-6 reads this; does not mutate it |
| Flight dynamics | active / deferred to MLF-7 | `aerodynamics_system.h:219` clamps by `structural_integrity` | MLF-6 does not modify aero |
| Loss-state classification | active / deferred to MLF-7 | `damage_system_common.h:403-423` | MLF-6 does not modify loss-state logic |

## Scope

In scope:

- **Inventory** every `ComponentDamageState` field, every current F-16C component
  name, and every `structural_integrity` write site (read-only).
- **Design** a component-to-break-mode mapping table: which F-16C component
  failures, at what cumulative integrity thresholds, trigger which break modes.
- **Implement** the structural breakup state machine as a new ECS system
  (`StructuralFailureUpdate`) that reads `ComponentDamageState`, writes a new
  `StructuralBreakupState` ECS component (D7), and classifies the airframe
  into `breakup_state` + active `break_mode` set.
- **Write** `StructuralBreakupEvent` rows into `RecentEngagementEvents`, with
  `cause_event_id` referencing the most recent `ComponentDamageEvent::event_id`
  for each contributing component group.
- **Populate** `breakup_state`, `break_mode`, `detached_part_ref` (string label),
  `detached_part_count`, `airframe_breakup` (boolean), and `cause_event_id`.
- **Add** focused C++ tests for each break mode using controlled
  `ComponentDamageState` inputs.
- **Add** Python diagnostics export for `structural_breakup_events`.
- **Ensure** zero false positives: an undamaged airframe produces zero breakup
  events.

Out of scope:

- **No flight-dynamics modification.** Lift/drag/pitch/yaw/roll/thrust response
  to breakup belongs in MLF-7.
- **No `structural_integrity` modification.** The scalar path continues
  unchanged; MLF-7 decides whether and how to bridge it.
- **No loss-state modification.** Whether breakup implies `Lost` belongs in
  MLF-7.
- **No wreck/debris lifecycle.** Detached parts are string labels in events;
  their persistence as world entities belongs in MLF-8.
- **No Pk authority, deterministic kill claims, or real-weapon calibration.**
- **No structural model for naval or ground platforms.** Air-only.
- **No reopening of sealed MLF-1 through MLF-5 packages.**
- **No secondary consequence modeling.** Fire, fuel, hydraulic propagation
  through breakup pathways belongs in MLF-7.

## Phase Plan

Phase granularity matches MLF-5's pattern: one focused concern per phase, each
with a narrow write set and a testable exit condition.

| Phase | Goal | Entry condition | Exit condition | Write surface | Status |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, design decisions D1-D7, forbidden claims. | User request to create MLF-6. | README v2, task clusters, status, dispatch queue, acceptance draft exist; parent READMEs link MLF-6. | docs only | complete |
| `P1 Inventory` | Map every `ComponentDamageState` field, every F-16C component name, and every `structural_integrity` write site MLF-6 must NOT touch. | P0 complete. | Inventory doc lists all consumed fields, all F-16C component names with structural group classifications, and all forbidden write sites. | docs only | complete |
| `P2 Break-Mode Mapping` | Design the component-to-break-mode classification table: which components at which integrity thresholds trigger wing_loss / tail_loss / engine_detach / fuselage_rupture. | P1 inventory complete. | Mapping table exists; each F-16C component is classified into exactly one structural group or `none`; threshold rules are explicit. | docs only | complete |
| `P3 State Machine` | Implement the structural breakup state machine as a new ECS system (`StructuralFailureUpdate`). | P2 mapping table approved. | System reads `ComponentDamageState`, applies P2 mapping rules, and tracks per-airframe `breakup_state` and active `break_mode` set internally. No event writing yet. | `src/components/combat/structural_failure.h`, `src/systems/combat/structural_failure_system.h`, `src/tests/test_structural_failure_system.cpp` | complete |
| `P4 Event Writer` | Write `StructuralBreakupEvent` rows into `RecentEngagementEvents` when state transitions or new break modes activate. | P3 state machine passes focused tests. | Event rows are populated with correct `breakup_state`, `break_mode`, `detached_part_ref`, `detached_part_count`, `airframe_breakup`, and `cause_event_id`. | `src/systems/combat/structural_failure_system.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/core/interfaces/engagement_event_recorder.h`, `src/runtime/facade/runtime_facade.cpp` | complete |
| `P5 Diagnostics` | Add thin Python probe on existing `StructuralBreakupEvent` bindings. | P4 event writer passes focused tests. | Python probe exports breakup facts per `chain_id` via existing facade surface; no new binding layer. | `tools/diagnostics/structural_breakup_export.py`, `tests/tools/test_structural_breakup_export.py` | complete |
| `P6 Validation` | Run focused tests for each break mode, full regression smoke, and zero-regression check vs main. | P4 + P5 pass. | Every P2 break mode has a focused C++ test; no-damage baseline produces zero events; `ctest -R structural_failure` passes. Full air_combat/world_batch regression remains P7. | `src/tests/test_structural_failure_system.cpp`, `CMakeLists.txt` | complete |
| `P7 Closure` | Sync docs, index, archive boundary, and residual register. | P6 passes. | P7 evidence recorded; full broad lane is green; package archived under the local A2 registry. | docs only | complete / archived |

## Task Clusters

- Task cluster plan: [missile_lethality_structural_failure_task_clusters_20260617.md](missile_lethality_structural_failure_task_clusters_20260617.md)

## Outputs And Evidence

Planned outputs (one per phase):

- `P1`: `missile_lethality_structural_failure_component_inventory_20260617.md` —
  every `ComponentDamageState` field, every F-16C component name with structural
  group, every `structural_integrity` write site (forbidden touch list).
- `P2`: `missile_lethality_structural_failure_break_mode_mapping_20260617.md` —
  component→break-mode classification table with integrity thresholds.
- `P3`: `src/components/combat/structural_failure.h` and
  `src/systems/combat/structural_failure_system.h` — state machine
  implementation with focused doctest coverage.
- `P4`: Event writer extension to P3 code; event-store integration; focused
  `structural_failure_events` doctest coverage.
- `P5`: `tools/diagnostics/structural_breakup_export.py` — thin Python probe
  consuming existing `StructuralBreakupEvent` facade/binding surface
  (`bindings_runtime.cpp:449-457`, `bindings_core.cpp`). No new binding layer.
- `P6`: `src/tests/test_structural_failure_system.cpp` —
  `structural_failure_break_modes` focused doctest suite plus named CTest lanes.

Existing evidence consumed (read-only):

| Source | What MLF-6 reads | How |
| --- | --- | --- |
| `damage_common.h` `ComponentDamageState` | `component_integrity`, `component_failure_mode`, `redundancy_group_availability` | ECS `get<ComponentDamageState>()` in `StructuralFailureUpdate` |
| `f16c_block50.json` | Component names, system groups, structural parent regions | Read during P2 mapping design |
| `engagement_contracts.h` | Contract shape for `StructuralBreakupEvent`; canonical `structural_breakup` lethality-chain stage | P4 event schema |
| `engagement_event_types.h` | `RecentEngagementEvents::structural_breakup_events` vector | P4 append/store target |

Deliberately NOT read or written by MLF-6:

| Field / System | Why excluded |
| --- | --- |
| `AircraftDamageState::structural_integrity` | MLF-7 decision surface |
| `AircraftDamageState::flight_control_integrity` | MLF-7 decision surface |
| `AircraftDamageState::propulsion_integrity` | MLF-7 decision surface |
| `FlightModel` (max_g, min_g, etc.) | MLF-7 write surface |
| `Propulsion` (mil_thrust_n, ab_thrust_n) | MLF-7 write surface |
| `PlatformDamageState::loss_state` | MLF-7 decision surface |
| `Health::current_hp` | MLF-7 decision surface |

## Acceptance Gate

This subproject can be marked accepted only when:

**P2 mapping**:
- Every F-16C component (from `f16c_block50.json` and TG-P7 split receivers) is
  classified into a structural group: `wing_left`, `wing_right`, `tail_left`,
  `tail_right`, `vertical_tail`, `engine_left`, `engine_right`, `fuselage`, or
  `none`.
- Each structural group has an explicit integrity-drop threshold that triggers
  its break mode.

**P3 state machine**:
- The `StructuralFailureUpdate` system reads `ComponentDamageState` and produces
  correct `breakup_state` transitions.
- State is irreversible and cumulative (per D4).
- Multiple break modes can activate in the same timestep.
- `StructuralBreakupState` (new ECS component, D7) is written with correct
  `breakup_state` and `break_mode` bitmask; values only transition forward.
- `StructuralBreakupEvent` rows are written when state transitions or new
  break modes activate.

**P4 event writer**:
- Controlled component-failure inputs produce correct `StructuralBreakupEvent`
  rows: `break_mode` matches P2 classification, `breakup_state` reflects
  cumulative severity, `detached_part_ref` is a stable string label,
  `cause_event_id` references the most recent relevant component-damage event.
- A no-damage baseline produces zero events (no false positives).
- `airframe_breakup = true` only when `breakup_state == full_breakup`.

**P5 diagnostics**:
- Python probe exports breakup facts per `chain_id` with all event fields.
- `pytest -q tests/tools/test_structural_breakup_export.py` passes.

**P6 validation**:
- Focused C++ tests cover: wing_loss, tail_loss, engine_detach, fuselage_rupture,
  multi_axis, and no-damage zero-event.
- `ctest --test-dir build-workshop -R structural_failure --output-on-failure`
  passes.
- Full `tests/runtime/air_combat/` and `tests/world_batch/` suites were
  executed for P7. After obsolete-oracle updates, the full lane now reports
  `447 passed`.

**P7 closure**:
- P7 evidence is recorded and the broad regression lane is green.
- Residual map explicitly defers aerodynamics bridging, loss-state integration,
  wreck/debris lifecycle, and Pk to MLF-7 / MLF-8 / MLF-9.
- Archive movement is complete by explicit user instruction; the package is
  registered in the local A2 archive registry.
- All forbidden claims remain refused.

## Residuals And Next Steps

Immediate:

- **P7 Accepted / Archived**: MLF-6 focused lanes and the broader
  `tests/runtime/air_combat/` + `tests/world_batch/` lane are green, and the
  packet is now archived under the local A2 registry.

Follow-on (MLF-6 evidence is now archived input):

- **MLF-7**: Secondary consequence coupling — read `StructuralBreakupEvent`
  facts, bridge them to `structural_integrity` / flight dynamics / loss-state.
  Authorized write surface: `damage/air/physics/tests`.
- **MLF-8**: Debris/wreck lifecycle — create persistent world entities from
  `detached_part_ref` labels. Authorized write surface: `runtime/tests`.

Deferred:

- Pk/statistical calibration (MLF-9).
- AIM-120C/MQ-9 structural-kill calibration (MLF-10).
- Naval/ground platform structural failure.

## Archive

This subproject is now itself an archived local A2 record. The parent archive
registry is [../README.md](../README.md), and the subproject's own nested
archive placeholder remains [archive/README.md](archive/README.md).
