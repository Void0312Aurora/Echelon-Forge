# Ground Command And Route Owner GC-0 Census

Language: English canonical; Chinese companion: not maintained (English-only
work surface).

Document kind: `evidence`
Lifecycle: `draft`
Canonical: `docs/domains/ground/work/issues/ground_command_and_route_owner_gc0_census.md`
Owner: `domains/ground`
Last verified: `2026-10-01`
Content status: read-only grep and targeted reads on branch
`codex/army-gc0-fact-census` at base `3e6ce9956` (army integration on origin/main
`71912e2a7`). No code was built or run. Every claim cites a `file:line` on that
base. Items this census could not settle say so.

Parent plan: [Ground Command And Route Owner Plan](ground_command_and_route_owner_plan.md),
packet GC-0.

## F1 — Reflection of variable-length members (D5)

- Flecs reflection already carries `std::vector<T>` members through an opaque
  adapter. `vector_support<T>` is defined at
  `src/core/engine/state_transfer_component_reflection.cpp:62-78` (serialize,
  count, ensure_element, resize). `std::string` uses `string_support` at `:51`.
- Registered components with a vector member on this base:
  `GroundWeaponState::weapons` (`:191-194`), `NavalWeaponSystem::mounts`
  (`:413-415`), `MountedSonars::mounts` (`:946-947`), `CommQueue::inbox`
  (`:948`), `ContactList::contacts` (`:949`), `Loadout::stations` (`:960`), and
  the `MountedSensors` and aero-table members (`:1002-1003`, `:1114-1122`).
- Conclusion for reflection: a `GroundRouteExecutionState` holding
  `std::vector<GroundRouteWaypoint>` is reflectable with the existing pattern
  (one `ecs.component<std::vector<GroundRouteWaypoint>>().opaque(vector_support<...>)`
  line plus the member line). Reflection is not the constraint.
- CUDA-resident fixture contracts: see F9.

Side finding (not in the plan): the `MissionCommandGround` reflection at
`state_transfer_component_reflection.cpp:731-737` lists `ground_task_mode`,
`objective_area_id`, `objective_node_id`, `ground_commander_id`, and
`tactical_cadence_hz`. It does not list `stance`, which the struct has at
`src/components/domains/ground/command/mission_command_ground.h:24` and the
maintained batch apply writes at
`src/runtime/contracts/world_batch_contracts.h:513`. Whether reflection-based
state transfer drops `stance` today was not run. GC-2 must reflect `stance`
together with the new route directive and add a reflection round-trip test that
covers every `MissionCommandGround` field.

## F2 — `route_ref_id` derivation and consumption today (D2, Q1)

- Field: `MissionCommandCore::route_ref_id` at
  `src/components/command/common/mission_command_core.h:13`; reflected at
  `state_transfer_component_reflection.cpp:697`; bound at
  `src/interfaces/python/bindings_command_mission_command.cpp:24` and, as
  `MissionCommandSharedCoreDirective::route_ref_id`, at
  `src/interfaces/python/bindings_runtime_tasking.cpp:17`. The maintained batch
  contract carries it inside `shared_core`
  (`world_batch_contracts.h:449`, applied whole at `:483`).
- Air derivation (Python only): `python/rl/profile/air_profile.py:403-451`.
  An explicit positive `route_ref_id` on the mission command or mission config
  wins (`:410-422`). Otherwise the id is `_stable_ref_id` over the waypoint list,
  each entry `{idx, x, y, z, speed_mps, radius_m, waypoint_mode}` rounded to
  3 decimals (`:430-446`). `_stable_ref_id` (`:393-400`) is SHA-1 of the
  sorted-key compact JSON, first 8 bytes big-endian, with 0 mapped to 1.
- The same function is duplicated at `python/rl/tasking/leader_tasking.py:220`
  and `python/scenario/compiler/common.py:203`. The scenario compiler resolves
  the id with the same payload at `python/scenario/compiler/waypoint_cache.py:162-184`
  and writes it back to the mission command at `:210-213` and `:223-226`.
- Ground: `python/rl/profile/ground_profile.py:503-505` returns `0`
  unconditionally.
- Native consumers: none interpret it. Outside reflection and bindings, the only
  C++ hits are `ExecutionEpisodeState::cached_route_ref_id`
  (`src/core/mission/episode/execution_episode_state.h:44-45`, equality at
  `execution_episode_state.cpp:76-77`). No file under `src/systems/` or
  `src/runtime/` reads it. Air waypoint following resolves geometry from the
  loader's waypoint list, not from the id.
- Consequence: Ground interpreting `route_ref_id` under `DeclaredRoute` collides
  with no native reader. The id is a content hash, not a key into any native
  catalog today, so GC-3's route catalog is the first native id-to-geometry map.
  The Air payload includes `z`, `speed_mps`, and `waypoint_mode`, which Ground
  routes do not have. Ground should reuse the hash function, not the Air payload:
  its canonical payload is `{idx, x, y, arrival_radius_m}` plus a domain tag, so
  the same polyline cannot hash to an Air route id. The hash must move to one
  shared helper rather than a fourth copy.

## F3 — Air 500 m arrival default (D2, Q4)

- `SpatialRouteWaypoint::radius_m = 500.0` at
  `src/core/geometry/spatial_query_runtime.h:27` (struct at `:23-31`).
- It is consumed with a further floor, `std::max(1.0, wp.radius_m)`, at
  `src/core/geometry/spatial_query_runtime.cpp:263`, and drives the capture and
  sequence gates at `:267-280` and `:330-335`. Air arrival there is
  end-position-and-gate based, not swept.
- Conclusion: the plan is correct that the struct default and its 1 m floor must
  not be reused for Ground. A Ground waypoint type must have no default radius.

## F4 — Maintained command batch shape (D1, D2, GC-2)

- `MissionCommandMaintainedBatchContract` at
  `src/runtime/contracts/world_batch_contracts.h:444-464`. Field list (X-macro)
  `src/runtime/contracts/detail/tasking/mission_command_maintained_batch_contract.inc`:
  `shared_core`, `air_recovery`, `air_takeoff`, `air_formation`,
  `naval_stationing`, `naval_embarked_helo`, `ground_static_task`.
- Ground slice type: `MissionCommandGround::StaticTaskDirective`
  (`mission_command_ground.h:8-17`): `ground_task_mode`, `objective_area_id`,
  `objective_node_id`, `ground_commander_id`, `tactical_cadence_hz`, `stance`.
- Projection shell to contract: `world_batch_contracts.h:466-478`. Apply
  contract to shell: `:480-514`, Ground fields at `:507-513`.
  `WorldMissionCommandMaintainedAssignment`: `:525-535`.
- Facade entry: `RuntimeFacade::set_mission_commands_maintained_batch` at
  `src/runtime/facade/runtime_facade_command_api.cpp:21-24`; it injects
  `InputBatch{.mission_commands = assignments}`. Files that reference it:
  `src/core/engine/world_batch_runtime.{h,cpp}`,
  `src/runtime/facade/internal/flecs_cpu_backend.cpp`,
  `src/runtime/facade/runtime_facade_packet.cpp`,
  `src/interfaces/python/bindings_runtime_facade.cpp`,
  `src/interfaces/python/bindings_runtime_engine.cpp`,
  `python/rl/runtime/world_batch/adapter.py`,
  `python/rl/runtime/world_batch/_shared_ops.py`.
- Conclusion: the GC-2 shape is one new directive field
  (`ground_route`, type `MissionCommandGround::RouteDirective`) in the `.inc`,
  one projection line, and one apply block. `route_ref_id` itself needs no new
  transport because it already rides in `shared_core`.

## F5 — Information-state labels and their owners (D4, Q2)

- Layers in `src/runtime/contracts/policy_contracts.h:59-65`: `WorldTruth`,
  `SensedState`, `TrackState`, `SharedTacticalPicture`, `AgentObservation`,
  `DecisionBelief`. The closed set is enforced at `:159-166`.
- Source labels at `:73-86`: `facade_observation_packet`,
  `agent_observation_adapter_projection`, `sensed_state_packet`,
  `track_state_packet`, `shared_tactical_picture_adapter_projection`,
  `world_truth_diagnostics`, `observation_derived_belief`. Each label is bound to
  one layer and one maintained status at `:215-255`.
  `facade_observation_packet` is `AgentObservation` + `maintained` (`:218-221`).
- An agent role may consume only `AgentObservation` or `DecisionBelief` at
  `maintained` status (`:362-375`). `WorldTruth` or any `diagnostics_only`
  source forces a diagnostics-only belief (`:523-532`, `:534-553`).
- The six layers are defined normatively by
  `docs/architecture/standards/simulation_system_architecture_design.md:125-161`,
  Lifecycle `maintained`, Owner `architecture/system-design`. Agent Observation
  is defined there as the "consumer-shaped observation packet sampled at a
  declared barrier" exposing "only fields allowed by the view spec" (`:138`) and
  as "what an agent is allowed to see" (`:141`). It is not defined as sensed
  data; sensing is `SensedState` (`:135`).
- `architecture/cross-domain-agency` docs
  (`docs/architecture/work/issues/cross_domain_scripted_agent_system_plan.md`,
  Owner at `:9`) contain no statement on terrain, map, or prior information
  state. A search of `docs/architecture/` for terrain-prior, map-derived, or
  authored-prior wording returns nothing.
- Conclusion: a new layer `TerrainPrior` is a change to a maintained standard
  owned by `architecture/system-design`, plus a code change in
  `policy_contracts.h` gated by `architecture/cross-domain-agency`. Neither
  owner has a position on record. The existing contract already admits a cheaper
  route: an own-state terrain block inside the facade observation packet is
  `AgentObservation` with source label `facade_observation_packet`, which is
  maintained and consumable by an agent role. The plan's objection that
  `AgentObservation` "would overstate what the unit perceived" does not match
  the standard's definition. See Q2 in the plan.

## F6 — Hard-coded 5 m spacings and the raster lookup (D3, GC-1)

There are three 5 m literals in the Ground terrain path, not one.

1. Transition verdict sampling:
   `src/models/environment/default_environment_model.cpp:718-719`
   (`std::ceil(observation.distance_m / 5.0)`), loop `:721-735`, verdict `:740`.
2. Transition movement-cost sampling, a separate copy:
   `src/systems/domains/ground/movement_effects.h:110-111`
   (`std::ceil(distance / 5.0)`), averaged at `:127-131`.
3. Slope central difference: `kSampleHalfSpanM = 5.0` in the default
   `IEnvironmentModel::get_ground_slope_deg` at
   `src/core/interfaces/environment_model.h:36-49` (10 m baseline, independent of
   raster step).

Lookup semantics:

- Cell lookup is nearest-cell, not interpolated. `ArnisRaster::index_for` at
  `default_environment_model.cpp:122-141` uses `std::llround((x - origin.x) / step_x)`
  with a 0.51-cell acceptance window. Sample points are cell centres at
  `origin + i*step`; cell edges are at `origin + (i +- 0.5)*step`. Grid
  traversal in GC-1 must use those edges.
- Elevation is the same nearest-cell lookup (`:153-160`, used at `:470-478`), so
  the slope in (3) is a finite difference of a piecewise-constant field.
- Landcover is nearest-cell (`:162-169`). Declared bridge and river features
  override landcover by point-in-feature tests (`river_at` at `:117-120`, the
  override at `:595-601`). Outside the raster the cell fails closed to
  `Obstacle` (`:626-632`).
- `step_x`/`step_y` are read from the bundle manifest artifact metadata
  `step_xy_m` (`:926-937`; elevation and landcover steps must agree to 1e-9) and
  stored at `:993-994`.
- Precedent: terrain line of sight already samples at the raster's own step,
  `min(|step_x|, |step_y|)`, and reports it as `sample_spacing_m`
  (`default_environment_model.cpp:757-761`).

## F7 — Consumers of `GroundTransitionObservation.passable` (D3, GC-1)

Struct: `src/core/interfaces/environment_model.h:90-98`.

| Consumer | Location | Kind |
| --- | --- | --- |
| `GroundInfantryMovement` stop on blocked | `src/systems/domains/ground/movement_system.h:112` | runtime |
| `evaluate_transition_movement_effects` embeds the transition | `src/systems/domains/ground/movement_effects.h:104-131` | runtime policy |
| `SimulationKernel::get_ground_transition_observation` tuple slot 1 | `src/core/engine/simulation_kernel.cpp:442` | native probe |
| `SimulationKernel::get_ground_transition_movement_observation` tuple slot 1 | `src/core/engine/simulation_kernel.cpp:462` | native probe |
| Probe dict field `passable` | `python/rl/ground/native_probe.py:76` | Python probe |

Not consumers of the native field: `python/rl/ground/infantry_proxy.py:258` and
`tests/training/test_ground_infantry_proxy.py:156,170` read the proxy's own plan
object.

## F8 — Arnis manifest digests and eastern-plain raster step (D4, GC-1)

- The bundle manifest carries a SHA-256 per artifact:
  `tests/scenario/fixtures/environment_substrate/arnis_bundle_v1/eastern_plain_infantry_phase1/expected/bundle.json:17`
  (provenance), `:60` (elevation raster), `:107` (landcover raster), `:130` and
  `:149` (vector features). The bundle directory also has a `checksums.sha256`
  file. The field overlay has a `sha256` key at
  `.../eastern_plain_infantry_phase1/field_overlay.json:725`; what it digests
  was not checked.
- The native loader neither reads nor verifies any of them: there is no
  `sha256` or `digest` reference in
  `src/models/environment/default_environment_model.cpp`
  (`load_arnis_terrain_bundle` at `:859`, `load_arnis_field_overlay` at
  `:1020`). Whether a SHA-256 implementation is already linked into the native
  build was not checked.
- Eastern-plain metric step: `step_xy_m = [1.00000861243566, -1.0002542170071909]`
  (`bundle.json:47-50`), `world_shape [1335, 1717]` (`:54-57`). The 5 m spacing
  in F6 therefore skips about four of every five cells. A one-cell water or
  obstacle feature can fall between samples on this fixture.

## F9 — CUDA-resident fixture contracts (D5)

- No `src/runtime/contracts/cuda_resident*.h` contract names a Ground
  component. The only Ground reference is the string `"ground"` in the bounded
  Air execution forbidden-feature list at
  `src/runtime/contracts/cuda_resident_backend_admission.h:145-161` (`:159`).
- Conclusion: a new Ground component, with or without a vector member, does not
  enter any resident fixture contract. This was checked by grep, not by building
  the CUDA target.

## F10 — Scenario-declared terrain for world creation (GC-4a, GC-5)

- `WorldTerrainAssignment` carries only `world_index` and `terrain_type`
  (`src/runtime/contracts/detail/platform/world_terrain_assignment.inc`).
  `WorldBatchRuntime` passes the type to `set_terrain_type` at
  `src/core/engine/world_batch_runtime.cpp:501-512`.
- The scenario compiler accepts only the procedural types
  `{flat, legacy, hill, gaussian_hill, mountain}`
  (`python/scenario/compiler/common.py:116-117`).
- `scenarios/ground/ground_platoon_native_static_occupy_v1.json:72` declares
  `terrain_type: flat`. The only bundle reference in a profile,
  `examples/viz/profiles/ground_chicago_environment_debug.json:6`, is labelled
  display-only (`:3`).
- Conclusion: today no scenario can declare an Arnis bundle or overlay for world
  creation. The only load path is the native-probe pair. GC-4a must add the
  declaration to `WorldTerrainAssignment`, the scenario compiler, and the world
  setup.

## F11 — Facade observation content for a Ground entity (D4)

- `ObservationBatchPacket` fields
  (`src/runtime/facade/detail/batch/observation_batch_packet.inc:7-13`):
  `snapshot_version`, `barrier_id`, `source_time_s`, `provenance` (default
  `AgentObservation` / `facade_observation_packet` / `maintained`), `refs`,
  `agent_observations`, `instrument_states`.
- `AgentObservation` (`src/core/interfaces/observation.h:30-50`) is generic own
  kinematics, health, contacts, RWR, and Air-shaped systems fields
  (`gear_state`, `throttle`). It has no terrain, stance, or Ground task field.
- Not verified: whether the exporter emits an `AgentObservation` row for a Ground
  entity at all. GC-4a's parity test settles it.

## F12 — Ground native-probe bindings and callers (D6)

Bindings in `bind_simulation_kernel_diagnostics_ground_native_probe_surface`
(`src/interfaces/python/bindings_core_kernel_diagnostics_ground.cpp:13`); the
allowlist is `tests/architecture/structural_boundaries/helpers.py:419-431`, with
its comment at `:414-417`.

| Binding | Def line | Python callers |
| --- | --- | --- |
| `load_arnis_terrain_bundle` | `:16` | `python/rl/ground/native_probe.py`; `tests/runtime/ground/test_ground_infantry_native_unit.py`; `tests/runtime/ground/test_ground_scripted_native_replay.py` |
| `load_arnis_field_overlay` | `:18` | `native_probe.py`; `test_ground_infantry_native_unit.py`; `test_ground_scripted_native_replay.py`; `tests/training/test_ground_infantry_contracts.py` |
| `get_ground_terrain_observation` | `:21` | `native_probe.py`; `test_ground_infantry_native_unit.py` |
| `get_ground_slope_deg` | `:29` | `native_probe.py`; `test_ground_infantry_native_unit.py` |
| `get_ground_movement_effect_observation` | `:32` | `native_probe.py`; `test_ground_infantry_contracts.py` |
| `get_ground_field_semantic_observation` | `:43` | `native_probe.py`; `test_ground_infantry_native_unit.py`; `test_ground_infantry_contracts.py` |
| `get_ground_transition_observation` | `:54` | `native_probe.py`; `test_ground_infantry_native_unit.py`; `test_ground_infantry_contracts.py` |
| `get_ground_transition_movement_observation` | `:65` | `native_probe.py`; `test_ground_infantry_native_unit.py`; `test_ground_infantry_contracts.py` |
| `fire_ground_weapon` | `:78` | `test_ground_infantry_native_unit.py:481,500,511,535,605` only |
| `fire_ground_weapon_from_mission_command` | `:81` | `native_probe.py`; `python/tasking_contracts/ground/capability.py`; `python/tasking_contracts/ground/execution.py`; `test_ground_infantry_native_unit.py`; `test_ground_scripted_native_replay.py`; `test_ground_infantry_contracts.py` |
| `get_ground_weapon_state` | `:85` | `native_probe.py`; `test_ground_infantry_native_unit.py`; `test_ground_scripted_native_replay.py`; `test_ground_infantry_contracts.py` |

Def lines for multi-line `.def(` entries are the line holding the name string.
The scripted model (`python/tasking_contracts/ground/`) depends on
`fire_ground_weapon_from_mission_command`, which stays held. It does not call the
raw `fire_ground_weapon`. Native C++ callers: `movement_effects.h` is included by
`src/core/engine/simulation_kernel.cpp:18` for the probe tuples, so `core/engine`
reaches into `systems/` today.

## F13 — Census pin and literal sites (D5, GC-3)

- Pin: `tools/maintenance/runtime_composition_evidence_contract.py:167`
  (`census != (88, 3, 35)`), message at `:174`.
- Component-count literal `88`: `src/tests/test_composition_lifecycle.cpp:624,646`;
  `tests/architecture/composition/test_runtime_composition_evidence_contract.py:60`;
  `tests/architecture/composition/test_runtime_profile_projection_contract.py:46`;
  `tests/architecture/composition/test_simulation_composition_contract.py:188,212`.
  Resolved-system-count literals (`35`) were not enumerated; D5-C would need that
  sweep.

## F14 — The `army-los` line (GC-1 entry)

- `codex/army-ground-line-of-sight` tip `c8a869223` is not an ancestor of the
  base or of origin/main, but its content is already on the base: a two-dot diff
  `3e6ce9956..c8a869223` over `environment_model.h`, `default_environment_model.cpp`,
  `state_transfer_component_reflection.cpp`, and `ground_capabilities.h` is
  empty. The terrain line-of-sight query is on the base at
  `environment_model.h:145` and `default_environment_model.cpp:744-769`.
- It adds no registered component. It gives the existing
  `GroundInfantryCapability` posture-geometry members (reflection at
  `state_transfer_component_reflection.cpp:180-181`), and the pin at its tip is
  still `(88, 3, 35)` (`runtime_composition_evidence_contract.py:167` at
  `c8a869223`).
- The session brief says another line is editing the environment model. The
  worktree `codex/army-env-raster-edge` sits at the base and was not inspected.
  That line, not `army-los`, is the live file conflict for GC-1.
