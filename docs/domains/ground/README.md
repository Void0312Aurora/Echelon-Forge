# Ground Mission Domain

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/README.md`
Owner: `domains/ground`
Last verified: `2026-09-24`

The Ground owner defines land-domain specialization semantics without turning
Army service doctrine into a private runtime stack. It owns Ground-specific
platform identity and static task/status vocabulary. Joint relationships,
Army service-profile interpretation, and cross-domain runtime architecture
remain with their respective owners.

## Current Authority

- [Ground Specialization Baseline](standards/specialization_baseline.md):
  canonical Ground identity, owner boundaries, accepted implementation surface,
  and held runtime claims.
- [Ground Minimal Task Structure](standards/minimal_task_structure.md):
  the maintained `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` static
  task/status contract.

## Current Implemented Surface

- `army`, `ground`, `land`, and `ServiceProfile.Army` route through the
  maintained `ground` tasking profile.
- `Ground_Platoon_MVP` is a runtime-loadable native `UnitType::Ground` content
  definition for static schema and scenario-loader evidence.
- Ground-owned component slices carry static command/task/status fields through
  `TaskOrder`, `LeaderIntent`, `PilotReport`, and `MissionCommand` compatibility
  shells.
- The maintained tasking cadence baseline is `1 Hz`.
- `Ground_Infantry_Soldier_MVP` is a native individual Ground fixture. The
  `GroundInfantryMovement` system consumes an admitted `MoveStatic` command,
  applies deterministic surface, slope, and vegetation speed costs through the
  shared `IEnvironmentModel`, and advances a bounded horizontal kinematic step.
  The kernel also exposes the owner-derived movement-effect multipliers to the
  native training probe. This
  is a single-agent movement primitive, not route following, passability,
  formation, or full land-combat dynamics. The admission record is
  [Ground Infantry Movement v1](work/active/ground_infantry_movement_v1/README.md).
- The default environment provider can explicitly load the verified Arnis
  continuous elevation/landcover raster pair, and the maintained kernel exposes
  bounded terrain and movement-effect observation tuples for training adapters. Tree-line/settlement
  semantics, general passability, and track/sensor observation export remain
  held; bounded river/bridge surface sampling is admitted.
- `GroundWeaponState` and `SimulationKernel.fire_ground_weapon` now admit a
  bounded native direct-fire slice for the individual infantry fixture: a
  tracked hostile Ground target, finite rifle range, ammunition, cooldown, and
  the shared effects/damage bridge are required. This is a deterministic
  close-range proxy; it does not claim line of sight, cover, suppression,
  ballistics, indirect fire, or a complete fire-control model.
- `src/systems/domains/ground/damage_system_ground.h` registers `GroundDamageStateUpdate`
  as a `domain = ground` system at stage 30 of the default composition. It matches
  the spawned ground entity and advances the ground-owned
  `GroundPlatformDamageState`, and the effects route into that state is reachable: the
  component id is resolved once per world in the composition path, so a structural hit
  produces the ground consequence instead of the placeholder fallback's all-zero
  destruction. Measured `2026-09-22` and recorded in the
  [DM-G1 repair package](work/active/ground_damage_effects_route_repair/README.md). The
  [Ground Systems Owner Admission](reviews/ground_systems_owner_admission_20260921/README.md)
  package reconciled that placement and is accepted.
- `src/systems/domains/ground/` owns the bounded infantry movement and damage
  responses; weapon release remains an explicit core-service seam. It is not a
  complete Ground runtime-system owner. Route movement, passability, sensing,
  indirect fires, effects beyond the shared damage bridge, suppression,
  logistics, and Ground observation export remain held as capabilities.

Directory placement does not broaden those claims. The current evidence proves
native identity and a static task/status chain, not a complete land-combat
runtime.

## Current Related Routes

- [Environment systems](../../systems/environment/README.md): cross-domain
  substrate contracts and retained G0/Arnis acceptance boundaries.
- [Ground defect inventory](reviews/ground_domain_defect_inventory_20260522.md):
  dated review snapshot; open items require current reverification.

The authorized Ground work surface was
[Ground Systems Owner Admission](reviews/ground_systems_owner_admission_20260921/README.md),
now an accepted review record: it admitted `src/systems/domains/ground/` as the Ground
per-tick systems owner. Its declaration cluster reconciled this page and the specialization
baseline, so the reachability status of the effects route is stated here
rather than described as a placeholder. Every reading inside that record is the
pre-repair measurement that located the cause; the route is reachable now. Archive records
may provide provenance but do not redefine the standards above.

Open work that outlived the admission record, restated here rather than left inside it: the
`DM-G1` repair has landed with its own package. The mobility expectation it left open was
decided on `2026-09-28`: withdrawn and pinned, because Ground mechanism-load estimation is
not admitted, so no warhead family reaches the chassis mobility branches. What remains
open is the component-attributed mobility follow-up recorded there; a `ground_p2_stage_node`
package, because the only Ground-claimed stage has no registered node; and an
archive-ledger registration for the retired `docs/task/ground/` records, which belongs to
documentation governance.

## Related Owners

- [Joint mission domain](../joint/README.md): shared authority and common-core
  command relationships.
- [US Army service profile](../joint/service_profiles/standards/army_profile.md):
  Army organization and service-level interpretation.
- [Runtime workflow and contract baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md):
  shared stage and runtime boundaries.
