# Ground Command And Route Owner Plan

Language: English canonical; Chinese companion: not maintained (English-only
work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/domains/ground/work/issues/ground_command_and_route_owner_plan.md`
Owner: `domains/ground`
Last verified: `2026-10-01`
Content status: read-only repository analysis on origin/main `71912e2a7` plus the
Ground scripted admission ledger entry on `codex/army-ground-integration`
(`204a15918`). This document proposes decisions and sequencing. It authorizes no
implementation.

Terms used below:

- WP5 means the cross-domain plan's "Ground admission and capability gate"
  package and its 2026-10-01 scripted admission slice.
- WP6 means the cross-domain plan's "Multi-unit, communication, and cross-domain
  coordination" package.
- GC-n means a work packet defined by this plan.

Inputs:

- [Native Runtime Blockers](../active/eastern_plain_infantry_training_v1/native_runtime_blockers.md),
  "Remaining unblock package", items 1 and 2
- [Ground owner README](../../README.md)
- [Ground specialization baseline](../../standards/specialization_baseline.md)
- [Ground minimal task structure](../../standards/minimal_task_structure.md)
- [Ground Systems Owner Admission](../../reviews/ground_systems_owner_admission_20260921/README.md)
- [Cross-Domain Scripted Agent System Plan](../../../../architecture/work/issues/cross_domain_scripted_agent_system_plan.md):
  the Ground admission and multi-unit coordination packages, and the 2026-10-01
  Ground scripted admission ledger entry
- [Runtime Composition Registry Sync](../../../../architecture/work/issues/runtime_composition_registry_sync.md),
  Repair Order and the layered-army-stack addendum
- [Stable Entity Identity For Stochastic Draws](../../../../architecture/work/issues/stable_entity_identity_for_stochastic_draws.md)

## Scope

This plan covers unblock items 1 and 2:

1. define the native action/command component and its relationship to the
   maintained command-chain batch bindings;
2. extend the bounded vector sampling into route/passability and observation
   provenance as runtime contracts rather than fixture-local assumptions.

Items 3 to 5 are out of scope. Item 3 (wider Arnis acceptance) is an entry
condition for a production RL adapter. Item 4 (proxy retention) is unchanged.
Item 5 (authored hitboxes, line-of-sight, cover) belongs to the line-of-sight
work running in `.worktrees/army-los`. This plan names where it touches that
work but does not plan it.

The outcome this plan unblocks:

- the scripted Ground model from the Ground admission slice can run from a
  maintained scenario through
  `RuntimeFacade`/`WorldBatch`, not the quarantined native-probe bindings on a
  bare `SimulationKernel`;
- a production Ground RL adapter can then be built on the same contracts once
  item 3 is satisfied. This plan does not release that adapter.

## Problem And Evidence

### Command side

- `MissionCommandGround`
  ([`mission_command_ground.h`](../../../../../src/components/domains/ground/command/mission_command_ground.h))
  carries only static task metadata: `ground_task_mode`, objective area/node,
  commander id, `tactical_cadence_hz`, and `stance`. Its boundary README
  ([`command/README.md`](../../../../../src/components/domains/ground/command/README.md))
  explicitly disallows route-following fields until a runtime owner is accepted.
- Motion intent is read from the shared core: `cmd_heading_deg` and
  `cmd_speed_mps` in
  [`mission_command_core.h`](../../../../../src/components/command/common/mission_command_core.h).
  The same core already carries `route_ref_id`, which Ground never interprets.
  `python/rl/profile/ground_profile.py::infer_route_ref_id` returns `0`
  unconditionally; Air derives it from a canonical waypoint payload
  (`python/rl/profile/air_profile.py::infer_route_ref_id`).
- `GroundInfantryMovement`
  ([`movement_system.h`](../../../../../src/systems/domains/ground/movement_system.h))
  consumes `MoveStatic` as one heading/speed step per tick and treats
  `OccupyStatic`/`SupportStatic` as zero-velocity holds. It has no route,
  leg, or arrival concept.
- The maintained batch contract already transports the Ground slice.
  `MissionCommandMaintainedBatchContract`
  ([`world_batch_contracts.h`](../../../../../src/runtime/contracts/world_batch_contracts.h),
  around line 444) has a `ground_static_task` field that the apply function
  writes into the compatibility shell. The nanobind class
  ([`bindings_runtime_tasking.cpp`](../../../../../src/interfaces/python/bindings_runtime_tasking.cpp),
  around line 125) exposes it. The facade entry is
  `RuntimeFacade::set_mission_commands_maintained_batch`
  ([`runtime_facade_command_api.cpp`](../../../../../src/runtime/facade/runtime_facade_command_api.cpp)),
  driven by the window coordinator's `apply_mission_commands`. The binding note
  says the trailing Ground fields on `TaskOrder`, `LeaderIntent`, and
  `PilotReport` maintained contracts remain held.
- `python/rl/ground/command.py` projects heading/speed/stance/static-task into
  both the kernel shell and `WorldMissionCommandMaintainedAssignment`. It raises
  on any `route_intent != "direct"` because the native command has no route
  field. That refusal is correct and must stay until a field exists.

### Route, passability, and observation side

- `IEnvironmentModel::get_ground_transition_observation`
  ([`environment_model.h`](../../../../../src/core/interfaces/environment_model.h))
  returns a `passable` verdict. The verdict is computed inside the shared
  environment model
  ([`default_environment_model.cpp`](../../../../../src/models/environment/default_environment_model.cpp),
  around line 712): water and obstacle block, and a declared bridge feature
  admits. That is an infantry mobility policy living in a domain-neutral owner.
  The 2026-09-28 move of stance semantics into `movement_effects.h` already
  established the direction that Ground semantics leave the environment.
- The same function samples the segment at a hard-coded `5.0` m spacing
  (`std::ceil(distance_m / 5.0)`). The value is not derived from the loaded
  raster's metric step. When the raster step is finer than 5 m, a feature one
  cell wide can fall between samples, and any fixed spacing can miss a segment
  that clips a cell corner. The spacing is also not reported to the
  caller, so a trace cannot say which resolution produced a verdict.
- Route sequencing exists only in Python tooling.
  `GroundInfantryNativeProbe.validate_waypoint_sequence()` and its waypoint
  advancement in `python/rl/ground/native_probe.py` (`waypoint_state`,
  `_waypoint_index`) are fixture-local bookkeeping marked `native_probe_only`.
  `GroundFieldProxy.plan_bridge_route()` is `engineering_proxy_only`.
- Observation is a set of untyped tuples read one by one through the
  native-probe surface
  ([`bindings_core_kernel_diagnostics_ground.cpp`](../../../../../src/interfaces/python/bindings_core_kernel_diagnostics_ground.cpp)).
  None of the tuples carries the information-state layer, the terrain bundle
  identity, the overlay identity, or the sampling resolution. The facade
  `ObservationBatchPacket` already carries an `InformationStateSource
  provenance` field
  ([`observation_batch_packet.inc`](../../../../../src/runtime/facade/detail/batch/observation_batch_packet.inc)),
  but there is no Ground terrain block in it.
- Every one of these names sits on
  `BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST` in
  `tests/architecture/structural_boundaries/helpers.py`. The comment there says a
  reviewed Ground owner package must replace them with a facade/contract before
  any name is promoted.

### Consumers that are blocked

- The scripted model `ground.infantry.objective_occupy_scripted` lives in
  `python/tasking_contracts/ground/` on `codex/army-ground-integration`
  (`204a15918`); it is not yet on origin/main. Its ledger entry records that the
  HEI replay used the quarantined native-probe kernel surface and a
  scenario-declared fixture contact. Its first follow-up is "a facade/`WorldBatch`
  Ground command and observation route (entry: a reviewed Ground owner package
  replacing the native-probe bindings)". It is the package this plan defines.
- `python/rl/ground/native_env.py` is the only Gymnasium surface and is
  `native_probe_only`.

### Composition cost baseline

The composition census pin in
`tools/maintenance/runtime_composition_evidence_contract.py` is
`(88, 3, 35)` (components, kernel systems, resolved systems) on this base. Any
new registered component or system changes the pin and forces the full causal
regeneration chain from the registry-sync Repair Order: the census pin, the
profile projection, the Cordis artifact and descriptor pins, the Cordis producer
outputs, the provenance and diagnostics fixtures, rebuilding the parity probe,
conformance binary, and `ef_py`, the P7 host/batch parity capture (on HEI by
the current convention), the P8 migration closure, and the test literals in
`src/tests/test_composition_lifecycle.cpp` and the three composition contract
tests. A census change also moves raw Flecs ids, which flips two Air realism
nodes until the stable-entity-identity fix lands. Those flips are a known
residual and not evidence against Ground.

## Decisions

Each decision lists the options, a recommendation, and its cost. Where the
answer depends on a fact this analysis did not verify, the decision names the
packet that must establish it.

### D1 — Native action/command carrier

| Option | Description | Cost |
| --- | --- | --- |
| A | Add a Ground per-tick action component analogous to Air `PilotAction` | New component, census bump, and a second authority for the same motion. Ground has no inner control loop that would interpret a command into actuator inputs, so the extra layer has nothing to own. |
| B | Keep `MissionCommand` (shared core + `MissionCommandGround` slice) as the only command authority. Extend the Ground slice for route intent (D2). | No new component. Changes the MissionCommand layout (see D2 cost). |

Recommendation: B. The RL action and the scripted decision both project into
the maintained `MissionCommandMaintainedBatchContract` through
`build_ground_infantry_maintained_assignment`, and the production path is the
facade batch setter, not `SimulationKernel.set_mission_command`. The kernel
single-entity setter remains a compatibility surface used by tests and
diagnostics. One command authority keeps the trace honest: what the decision
layer emits is what the movement system reads.

### D2 — Where route intent and the waypoint sequence live

| Option | Description | Cost |
| --- | --- | --- |
| A | Inline fixed-capacity waypoint array in `MissionCommandGround` | Capacity is a magic number. It enlarges every MissionCommand on every domain because the shell is flat, and it moves through every reflection, JSON, episode-equality, and batch surface. |
| B | Command carries a reference: a new `GroundRouteDirective` in `MissionCommandGround` with `route_intent` (`Direct`, `DeclaredRoute`). The existing shared-core `route_ref_id` names the route. Geometry lives in a scenario-authored route catalog; execution progress lives in a Ground execution-state component (D5). | One enum field on the Ground slice plus contract plumbing. Requires a route catalog owner and a progress owner. |
| C | Separate per-entity `GroundRouteIntent` component with its own batch contract and binding | New component and a parallel command pipeline, which the command README forbids ("replacing the accepted tasking bridge with a ground-only command pipeline"). |

Recommendation: B.

- `route_ref_id` is already shared-core, transported by `shared_core` in the
  maintained batch contract, and reflected. Ground adopts the Air identity
  convention: the id is derived from the canonical route geometry, not from
  load order or Flecs ids, so it is stable across composition changes.
- `route_ref_id` is interpreted by Ground only when
  `route_intent == DeclaredRoute`. `Direct` keeps today's heading/speed
  semantics unchanged.
- Each declared waypoint carries an authored arrival radius. There is no Ground
  default. In particular the Air `SpatialRouteWaypoint::radius_m = 500.0`
  default must not leak into Ground. Load-time validation rejects a missing,
  non-finite, or non-positive radius.
- Arrival is tested on the swept tick segment: the closest approach of the
  tick's start-to-end segment to the waypoint is within the radius. A test on the
  end position alone would make a valid radius depend on step size and speed, and
  a fast step could skip a waypoint. The swept test needs no step-dependent lower
  bound and no tuned tolerance.
- Waypoint geometry never enters the command. The command says which route and
  how to execute it; the catalog says what the route is.

Cost of B: adding a field to `MissionCommandGround` changes the MissionCommand
layout. The packet must update `mission_command_ground_*` projections, the
schema-owned `.inc` field list for the maintained batch contract (owned by
`tools/maintenance/dto_schema`), `apply_mission_command_maintained_batch_contract_to_compatibility_shell`,
`state_transfer_component_reflection.cpp`, JSON round-trip, episode equality,
and the nanobind class. It does not add a registered component, so the census
pin should not move. Whether the Cordis or P7 hashes move because of a layout
change is not assumed. GC-2 measures it and regenerates whatever moves.

`TaskOrderGround` and `LeaderIntentGround` do not gain route fields in this plan
(see Held Items). The scripted model and an RL adapter emit MissionCommand
assignments directly, which is enough for the outcome this plan unblocks.

### D3 — Who owns route/passability

| Option | Description | Cost |
| --- | --- | --- |
| A | `IEnvironmentModel` grows route and passability products | Puts infantry mobility policy in the shared environment. This repeats the stance mistake undone on 2026-09-28 and makes Naval/Air consumers carry Ground semantics. |
| B | A Ground-owned system computes everything, including terrain sampling | Duplicates raster access and bridge geometry outside the environment owner. Two terrain readers would drift. |
| C | Split by kind. The environment returns domain-neutral segment facts: per-traversed-cell surface class and path length, declared-feature membership (water body, bridge deck), elevation and slope, and source provenance (D4). A Ground-owned pure policy turns facts into the infantry passability verdict and movement cost. | Moves the `passable` verdict out of `default_environment_model.cpp` and changes the transition observation shape. Every consumer of `GroundTransitionObservation.passable` must move to the Ground verdict in the same packet. |

Recommendation: C.

- The segment query visits every raster cell the segment crosses (grid
  traversal over the loaded `step_x`/`step_y`), instead of sampling at a spacing.
  No spacing parameter remains to tune, and corner clips are not missed. For
  per-cell classes the movement cost becomes a path-length-weighted average,
  which is exact for a piecewise-constant raster. Declared bridge and water
  features are vector geometry, so their membership is a segment-geometry
  intersection, not a raster lookup. The traversal method and traversed cell
  count are part of the returned facts. Removing the `5.0` m literal is part of
  this decision, not a later cleanup.
- The infantry passability policy (what blocks, how a declared bridge admits) and
  the movement cost policy (`evaluate_transition_movement_effects`) sit together
  under the Ground owner. Both the movement system and the facade route
  validation query (D4, GC-4) call the same function, so the native trace and
  the export cannot disagree.
- Placement: the policy is stateless. Under the layering rule it belongs in
  `src/models/domains/ground/` (systems may include models; models must not
  include systems). Today `movement_effects.h` sits in
  `src/systems/domains/ground/`. Relocating it is not required for correctness,
  because runtime may call systems. The owner should decide whether GC-1 moves
  it (open question Q3).
- Route planning (finding a route) stays held. The Ground owner validates and
  executes declared routes only.

### D4 — How observation provenance is carried

| Option | Description | Cost |
| --- | --- | --- |
| A | Keep per-tuple probe reads; add provenance fields to each tuple | Leaves the observation on the quarantined kernel surface. Each tuple re-invents identity fields. |
| B | Add a typed Ground terrain block to the facade observation export. A `GroundTerrainQueryProvenance` record is attached per block. The packet-level `InformationStateSource` carries a new terrain-prior source label. | Touches the facade observation contract and `policy_contracts.h` labels. Needs review from `architecture/cross-domain-agency`. |
| C | Label the terrain block `WorldTruth` diagnostics | Honest about origin but makes it `diagnostics_only` under `decision_belief_requires_diagnostics_only`. A scripted or learned policy could then never consume it on a maintained path. |

Recommendation: B.

- `GroundTerrainQueryProvenance` carries the terrain bundle digest, the field
  overlay digest, raster `step_x`/`step_y`, the traversal method and traversed cell
  count, and the query kind (own-cell, segment, route leg). The digests are computed when the
  bundle and overlay are loaded. This analysis did not verify whether the Arnis
  manifest already carries per-file digests. GC-0 establishes that, and the
  loader reuses them if present.
- Information-state label: map-derived terrain facts are authored prior
  knowledge available to the unit, like a map. They are not live truth about
  other entities, and they are not sensed. They need their own maintained label,
  for example information-state layer `TerrainPrior` with source label
  `ground_terrain_database_prior`. The existing labels in
  [`policy_contracts.h`](../../../../../src/runtime/contracts/policy_contracts.h)
  have no slot for this. `AgentObservation` and `SensedState` would overstate
  what the unit perceived; `WorldTruth` would forbid use. Adding the label is a
  cross-domain contract change and needs that owner's acceptance (open question
  Q2).
- Hostile contacts are not part of this block. Ground sensing stays held, and
  the scripted model keeps reading its assigned target from its own mission
  command.
- Execution evidence: the movement system records what it consumed each tick
  (resolved leg, blocked reason, the traversed cell count and length-weighted
  multiplier it applied, provenance digest reference) in the execution-state component (D5).
  The export reads that record. It does not recompute a transition, which is what
  the probe does today.

### D5 — Whether a new ECS component or system is added

| Option | Description | Census after | Cost |
| --- | --- | --- | --- |
| A | No component. Route following stays in the decision layer, which issues `Direct` legs. | `(88, 3, 35)` | No regeneration. But the native command still cannot represent a route, leg arrival depends on decision cadence (at 1 Hz and 1.5 m/s a unit runs past a waypoint by up to 1.5 m), and the route stays decision-layer bookkeeping. This does not meet item 2. |
| B | One per-entity `GroundRouteExecutionState` component (route ref, leg index, leg status, last-step evidence). Route following is a phase inside the existing `GroundInfantryMovement`. The catalog is reached through a world-scoped ref if needed. | `(89, 3, 35)` or `(90, 3, 35)` | One regeneration chain. `GroundInfantryMovement` takes on leg resolution. |
| C | New component(s) plus a separate `GroundRouteFollowing` system stage ahead of movement | `(89 or 90, 3, 36)` | One regeneration chain plus a new stage in the resolved plan, stage-order evidence, and a P7 semantic reference change. Gives a cleaner single-purpose stage. |

Recommendation: B, with all registry additions landed in one packet (GC-3) so
the regeneration chain runs exactly once.

- The second component is conditional. If state-transfer reflection and the
  CUDA-resident fixture contracts accept a component with a variable-length
  member, the resolved waypoint list is copied into `GroundRouteExecutionState`
  when the command is applied, and no catalog ref is needed: `(89, 3, 35)`. If
  they do not, the component holds only the reference and progress, and a
  world-scoped `GroundRouteCatalogRef` (modelled on `EnvironmentModelRef`) gives
  the movement system the geometry: `(90, 3, 35)`. GC-0 answers this before
  GC-3 starts. The plan does not guess.
- C is not rejected on principle. If the owner prefers the separate stage (open
  question Q5), the cost row above applies and the same single-packet rule holds.
- The movement system must never write `MissionCommand`. Commands are inputs.
  Route following resolves a heading for the tick internally and records it in
  the execution state.

Cost common to B and C: the full regeneration chain on the shared composition
pins. That includes a P7 recapture on HEI and a P8 closure update. Census bumps
from other lines (`.worktrees/army-los` may add a line-of-sight or rifle-gate
component) must be serialized with GC-3 on main, or batched into it by
agreement. Two lines must not bump the pin independently.

### D6 — Retiring or promoting the native-probe bindings

| Option | Description | Cost |
| --- | --- | --- |
| A | Promote the probe names as-is to maintained `SimulationKernel` API | Makes the compatibility kernel a production surface and keeps untyped, unprovenanced tuples. |
| B | Replace each name with a facade/contract successor. Prove parity on the shared fixture, then delete the name and shrink the allowlist. Delete the allowlist constant once it is empty. | Needs successors (GC-4, GC-5) and a parity test per name. |
| C | Keep the probe surface indefinitely beside the facade | Two observation authorities; the allowlist becomes permanent. |

Recommendation: B. The allowlist only shrinks. No new name is ever added to it
to carry facade work.

| Probe name | Successor | Packet |
| --- | --- | --- |
| `load_arnis_terrain_bundle`, `load_arnis_field_overlay` | Scenario-declared environment content loaded at world creation by the scenario loader, with digests recorded | GC-4, GC-5 |
| `get_ground_terrain_observation`, `get_ground_slope_deg`, `get_ground_movement_effect_observation`, `get_ground_field_semantic_observation` | Ground own-state terrain block in the facade observation export (D4) | GC-4 |
| `get_ground_transition_observation`, `get_ground_transition_movement_observation` | Facade route validation batch query plus the per-tick execution record (D3, D4, D5) | GC-4 |
| `fire_ground_weapon` | None. A raw release without command authority has no production role. Retire it once no test needs it. | GC-6 |
| `fire_ground_weapon_from_mission_command`, `get_ground_weapon_state` | Out of scope. Held with the direct-fire and line-of-sight owner (item 5). They stay on the allowlist. | held |

Retiring the probe caller also removes `python/rl/ground/native_probe.py` from
the P8 caller inventory under `simulation_kernel.default_compatibility`, which
changes the P8 closure. GC-6 regenerates it.

## Work Packets

Dependency order. "C++" marks packets that need a native build; "regen" marks
packets that run the composition regeneration chain.

```text
GC-0 ──┬── GC-1 (C++) ──┬── GC-4a (C++/Py) ──┐
       │                │                    ├── GC-5 (Py/content) ── GC-6 (C++/Py, regen P8)
       └── GC-2 (C++) ──┴── GC-3 (C++, regen) ── GC-4b (C++/Py) ──┘
```

GC-1 and GC-2 can run in parallel. GC-4a can start after GC-1 without waiting
for GC-3. Everything else is serial.

### GC-0 — Contract census (docs and read-only probes, no C++)

- Scope: establish the facts the decisions depend on.
  - Can state-transfer reflection and the CUDA-resident fixture contracts carry
    a component with a variable-length member? (D5)
  - Does the Arnis manifest carry per-file digests? (D4)
  - List every consumer of `GroundTransitionObservation.passable`.
  - Can the scenario loader spawn native Ground infantry and declare a terrain
    bundle and overlay for world creation? `ground_platoon_native_static_occupy_v1`
    proves platoon spawn, not terrain.
  - What does the facade observation export include for a Ground entity today?
  - What are the raster metric steps of the eastern-plain fixture? Is
    `get_terrain_at` a nearest-cell or an interpolated lookup, and how is slope
    computed? Grid traversal must follow the lookup's own cell definition.
  - Which components does the `army-los` line plan to register?
- Write set: an evidence section appended to this plan, or a sibling evidence
  file under `docs/domains/ground/work/issues/`.
- Acceptance evidence: each question answered with a file and line or command
  output; unanswerable items marked as such.
- Entry condition: this plan reviewed and D1 to D6 accepted or amended.

### GC-1 — Environment facts / Ground policy split (C++, no registry change)

- Scope: D3. The environment transition query returns domain-neutral facts
  from exact grid traversal, with a provenance record. The infantry passability verdict
  moves to the Ground policy beside `evaluate_transition_movement_effects`.
  `GroundInfantryMovement` and every consumer listed in GC-0 use the Ground
  verdict. The `5.0` m literal is removed. The bundle and overlay loaders record
  digests.
- Write set: `src/core/interfaces/environment_model.h`,
  `src/models/environment/default_environment_model.cpp`, the Ground policy
  header (`src/systems/domains/ground/movement_effects.h`, or a new
  `src/models/domains/ground/` home if Q3 says move it),
  `src/systems/domains/ground/movement_system.h`, the native-probe binding
  translation for the changed tuple shape, `python/rl/ground/native_probe.py`
  where it reads the verdict, and the Ground runtime and training tests.
- Acceptance evidence:
  - on a synthetic raster, a one-cell water feature narrower than the old 5 m
    spacing is blocked, and so is a segment that only clips a water cell's
    corner;
  - the eastern-plain native acceptance suite and the bridge crossing pass;
  - every changed movement trace value is listed before and after with its
    cause (exact traversal). No silent behaviour drift.
  - `IEnvironmentModel` no longer contains an infantry verdict.
  - The census pin is unchanged (checked, not assumed).
- Entry condition: GC-0. The `army-los` line has landed on main, or the two
  owners have agreed a merge order, because both touch `environment_model.h`
  and the default environment model.

### GC-2 — Ground route directive in the command contract (C++ and bindings)

- Scope: D1 and D2. Add `GroundRouteIntent` and a
  `MissionCommandGround::RouteDirective`. Project it through the maintained
  batch contract, reflection, JSON, episode equality, and nanobind.
  `command.py` accepts `route_intent="declared_route"` with a `route_ref_id` and
  keeps rejecting every other non-direct value. Execution is not wired yet: a
  `DeclaredRoute` command reaching the movement system before GC-3 must stop the
  unit and report it as unexecuted. It must not fall back to direct heading.
- Write set: `src/components/domains/ground/command/` (header and README),
  `src/components/domains/ground/tasking/ground_tasking_enums.h`,
  `src/runtime/contracts/world_batch_contracts.h` and its schema-owned `.inc`
  (through `tools/maintenance/dto_schema`), `src/core/engine/state_transfer_component_reflection.cpp`,
  `src/interfaces/python/bindings_runtime_tasking.cpp`,
  `src/interfaces/python/bindings_command_mission_command.cpp`,
  `src/systems/domains/ground/movement_system.h` (the fail-closed stop only),
  `python/rl/ground/command.py`, and the tests.
- Acceptance evidence:
  - round-trip of the new directive through the kernel shell and the maintained
    batch contract;
  - JSON and episode-equality tests;
  - a negative test that `DeclaredRoute` without GC-3 stops and is reported;
  - `command.py` tests for accept and reject;
  - the measured effect on the census, Cordis, and P7 hashes, with whatever moved
    regenerated.
- Entry condition: GC-0. Parallel with GC-1.

### GC-3 — Route catalog and native route execution (C++, regen)

- Scope: D2 and D5. Add the scenario content schema for declared Ground routes:
  a polyline with an authored arrival radius per waypoint and a content-derived
  `route_ref_id`. Add load-time validation: every leg passes the GC-1 Ground
  verdict, and every radius is present, finite, and positive. Arrival uses the
  swept-segment test from D2. Add `GroundRouteExecutionState` (and `GroundRouteCatalogRef`
  if GC-0 requires it). Add the route-following phase in `GroundInfantryMovement`
  with leg advancement on arrival and the per-tick execution record. Then run the
  regeneration chain once, in the Repair Order.
- Write set: `src/components/domains/ground/` (new execution-state header and
  README), the scenario/content loader for routes, `src/systems/domains/ground/movement_system.h`,
  the component registry entry, and the composition evidence surfaces listed in
  Composition cost baseline.
- Acceptance evidence:
  - a declared route on the eastern-plain fixture that crosses the declared
    bridge executes to completion with leg transitions in the record;
  - a route with an impassable leg is rejected at load with the leg index and
    reason;
  - a route with a missing or non-positive radius is rejected;
  - a waypoint passed through mid-tick, with the end position outside the radius,
    still advances the leg;
  - same-seed replay is byte-identical;
  - the census pin moves to the value GC-0 predicted;
  - Cordis `npm test` is green;
  - P7 is recaptured and P8 regenerated;
  - the two Air realism flips are attributed to the stable-identity residual and
    nothing else flips.
- Entry condition: GC-1 and GC-2 on main. No other line has an unmerged census
  bump. GC-0's reflection answer is recorded.

### GC-4a — Facade Ground terrain observation and route validation (C++ and Python)

- Scope: D4 and D6. Add the Ground own-state terrain block in the facade
  observation export with `GroundTerrainQueryProvenance` and the terrain-prior
  label. Add a facade route validation batch query that calls the same Ground
  policy as movement. Terrain bundle and overlay become scenario-declared and are
  loaded at world creation.
- Write set: `src/runtime/facade/` observation and query surfaces and their
  `.inc` lists, `src/runtime/contracts/policy_contracts.h` (label only, after Q2
  is accepted), the scenario loader environment declaration, nanobind
  registration for the new facade surfaces, and tests.
- Acceptance evidence:
  - parity test: for the eastern-plain fixture, each probe tuple equals the
    corresponding facade field at the same positions and stance;
  - provenance digests match the loaded files;
  - a `DecisionBelief` built from the block validates under
    `decision_belief_has_valid_provenance` without `diagnostics_only`.
- Entry condition: GC-1. Q2 is accepted by `architecture/cross-domain-agency`.

### GC-4b — Facade route execution export (C++ and Python)

- Scope: export `GroundRouteExecutionState` (leg, status, last-step evidence)
  in the Ground observation block.
- Write set: the facade observation surfaces from GC-4a, and tests.
- Acceptance evidence: the exported record equals the component value each
  tick. A blocked step reports the reason the movement system recorded, not a
  recomputation.
- Entry condition: GC-3 and GC-4a.

### GC-5 — Scenario-routed scripted Ground AI through the facade (Python and content)

- Scope: a maintained Ground scenario declaring the eastern-plain terrain, a
  declared route, and the single soldier. The scripted Ground model is routed by
  the scenario manifest through `DecisionRuntimeRoster`. It emits maintained
  MissionCommand assignments through the facade batch path and reads the facade
  observation. Its `route_intent` becomes `declared_route` where the scenario
  supplies one.
- Write set: `python/tasking_contracts/ground/` (once on main), the scenario
  and manifest content, the Ground capability label declaration and its tests
  (`route_execution_declared` moves from held to `admitted_bounded`;
  `route_planning` stays held), and the Ground admission ledger entry in the cross-domain
  plan.
- Acceptance evidence:
  - the facade replay reproduces the Ground admission HEI evidence classes (move, latched
    hold, cadence, byte-identical same-seed replay) without touching any
    native-probe name;
  - a structural test asserts that the routed path imports no
    `native_probe_only` surface.
- Entry condition: GC-4b. `codex/army-ground-integration` (the Ground
  scripted admission slice) is on main.

### GC-6 — Native-probe retirement (C++ and Python, P8 regen)

- Scope: D6. Delete the successor-covered names from
  `bind_simulation_kernel_diagnostics_ground_native_probe_surface`, remove them
  from `BINDINGS_GROUND_NATIVE_PROBE_ALLOWLIST`, and retire `fire_ground_weapon`.
  Reimplement or delete `native_probe.py` and `native_env.py` over the facade.
  Regenerate the P8 caller inventory.
- Write set: `src/interfaces/python/bindings_core_kernel_diagnostics_ground.cpp`,
  the `SimulationKernel` methods that only those bindings call,
  `tests/architecture/structural_boundaries/helpers.py`,
  `python/rl/ground/native_probe.py`, `python/rl/ground/native_env.py`, the P8
  closure, and the blockers document and Ground baseline wording.
- Acceptance evidence:
  - the allowlist contains only the held fire/weapon names;
  - the structural boundary tests are green;
  - the native acceptance suite runs through the facade;
  - P8 is regenerated.
- Entry condition: GC-5 parity accepted.

## Held Items

| Item | Why held |
| --- | --- |
| Route planning and path finding, including promoting `GroundFieldProxy.plan_bridge_route()` | No accepted planner owner. Declared-route validation is the bounded claim. |
| General passability mask or route-level cost grid | No consumer needs it for declared routes. It would be a new environment product with its own provenance. |
| Route fields on `TaskOrderGround`, `LeaderIntentGround`, `PilotReportGround` | The binding note holds their trailing Ground fields. This plan's consumers emit MissionCommand directly. Adding them needs a standards update to `minimal_task_structure.md`. |
| Multi-unit routes and formation | Belongs to the cross-domain multi-unit coordination package. There is no Ground formation owner. |
| Acceleration, fatigue, and turning dynamics | No Ground dynamics owner. Movement remains a bounded kinematic step. |
| Line-of-sight, cover, concealment, authored hitboxes | Item 5. Owned by the `army-los` line. |
| Ground sensing and hostile track export in the observation block | Ground sensing is held. Contacts stay scenario-declared. |
| Fire/weapon probe names (`fire_ground_weapon_from_mission_command`, `get_ground_weapon_state`) | Successor belongs with the direct-fire and line-of-sight owner. |
| Production Ground RL adapter (`train.py`, `WorldBatch` training entry) | Needs item 3 (wider-map acceptance) on top of GC-6. The training contract stays `contract_only`. |
| CUDA-resident Ground execution | No resident Ground stage; GC-0 only checks that the new component does not break the fixture contracts. |
| Proxy retirement (`infantry_proxy.py`, `proxy_env.py`) | Item 4. They stay as diagnostics until native behaviour supersedes them. |

## Risks

- Census collisions: GC-3 and any `army-los` component addition both move the
  shared pin. Mitigation: serialize on main, and GC-3's entry condition requires
  no unmerged bump.
- Air realism flips on every census change, until stable entity identity lands.
  Mitigation: attribute the flips explicitly. Do not pin or allowlist them.
- `route_ref_id` meaning across domains: Air treats it as a content hash of
  scenario waypoints. If Ground used a load-order key, joint tooling could
  misread it. Mitigation: use the same content-derived convention, interpreted
  only under `DeclaredRoute` on Ground entities.
- Exact traversal changes existing traces (GC-1). Mitigation: a before/after
  table with causes. Nothing is left unexplained.
- The MissionCommand layout change in GC-2 touches every domain's
  serialization surfaces. Mitigation: GC-2 measures and regenerates any moved
  hash in the same packet.
- Cross-owner contract: the terrain-prior label changes `policy_contracts.h`.
  If it is refused, GC-4a must fall back to a labelled `diagnostics_only` export.
  That keeps the scripted AI on diagnostics and blocks GC-5. This is the
  largest schedule risk.
- External dependency: the Ground scripted admission slice is not on main.
  GC-5 cannot start until
  `codex/army-ground-integration` lands.
- Evidence host: P7 recapture follows the HEI convention. HEI availability
  gates GC-3 and GC-6.
- Scope creep: a declared-route executor invites planner requests. The held
  table and the capability labels must keep `route_planning` held.

## Open Questions For The Owner

1. Q1: Accept reuse of shared-core `route_ref_id` with the content-derived
   convention? The alternative is a Ground-owned route id field.
2. Q2: Will `architecture/cross-domain-agency` admit a terrain-prior
   information-state label as a maintained observation source?
3. Q3: Should the stateless Ground mobility policy move from
   `src/systems/domains/ground/movement_effects.h` to
   `src/models/domains/ground/` as part of GC-1?
4. Q4: Accept fail-closed loading when a Ground waypoint has no authored arrival
   radius, plus the swept-segment arrival test? This deliberately breaks reuse of
   the Air `SpatialRouteWaypoint` default and its end-position semantics.
5. Q5: Should route following be a phase in `GroundInfantryMovement` (D5-B) or
   its own stage (D5-C, one more resolved system)?
6. Q6: Retire the raw `fire_ground_weapon` binding in GC-6, or keep it as a
   diagnostics-only name with the held fire surfaces?
