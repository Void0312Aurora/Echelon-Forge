# Ground Specialization Baseline

Language: English canonical; [Chinese companion](specialization_baseline.zh.md).

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/specialization_baseline.md`
Owner: `domains/ground`
Last verified: `2026-10-01`

## Scope

This standard defines the stable Ground specialization boundary and the claims
supported by the current repository. It governs Ground identity, content and
component ownership, and the separation between accepted static infrastructure
and held execution behavior.

It does not own Joint command relationships, Army service organization, or
cross-domain runtime architecture.

## Normative Identity And Routing

- The maintained specialization name MUST be `ground`.
- The text aliases `army`, `ground`, and `land`, plus
  `ServiceProfile.Army`, MUST resolve through the maintained `ground` tasking
  profile.
- `Army` MUST remain the service profile. `land` MUST remain an alias. Neither
  name creates an additional runtime stack or documentation owner.
- An unknown explicit tasking profile or service-profile hint MUST fail closed;
  it MUST NOT silently fall back to Ground.
- Joint/common-core names and authority relationships MUST remain owned by
  [the Joint standards](../../joint/standards/command_and_modeling_baseline.md).
  Army-specific organization and service interpretation remain with the
  [Army service profile](../../joint/service_profiles/standards/army_profile.md).

## Accepted Implementation Baseline

The following surfaces are implemented and test-backed:

- `UnitType::Ground` is exposed through the Python binding.
- `Ground_Platoon_MVP` is a runtime-loadable native content definition with
  `specialization=ground`, `service_profile=Army`,
  `tasking_profile=ground`, `echelon=platoon`,
  `platform_family=dismounted_unit`, and `doctrine_family=land_tactics`.
- `src/components/domains/ground/` owns Ground component slices. The current
  command/tasking slices are static G0/G1 metadata, not execution dynamics.
- Native and compatibility-shell Ground scenarios use the shared loader and
  tasking bridge; they do not create a private Ground runtime path.
- `Ground_Infantry_Soldier_MVP` is a native individual fixture whose
  `MoveStatic` command is consumed by the bounded `GroundInfantryMovement`
  system. The system applies surface and slope speed costs and advances a
  horizontal kinematic step; it does not establish route following or a full
  infantry dynamics model.
- The default environment provider can explicitly load a verified Arnis
  `arnis_cmo_bundle.v1` continuous elevation/landcover raster pair through
  `SimulationKernel.load_arnis_terrain_bundle(bundle_root)`; this is an
  explicit provider load, not automatic runtime setup
  (`tests/runtime/ground/test_ground_infantry_native_unit.py`).
- The native provider samples declared Arnis hydrology and bridge road
  vectors for bounded point classification: river corridors are water and a
  declared bridge segment overrides them as a hard-packed crossing surface.
  This is bounded local sampling, not a route graph or general passability
  product (`tests/runtime/ground/test_ground_infantry_native_unit.py`).
- Movement cost is stance-, surface-, slope-, and vegetation-aware. A sampled
  one-tick transition observation (5 m segment intervals) supplies the
  average combined movement multiplier that `GroundInfantryMovement`
  consumes, and the same local transition check blocks any one-tick segment
  that intersects water or an unknown/obstacle cell without advancing the
  transform. This is a local segment-cost observation and transition block,
  not a route-level cost grid or general passability mask
  (`tests/runtime/ground/test_ground_infantry_native_unit.py`).
- A bounded native direct-fire slice is admitted for the infantry fixture:
  `GroundWeaponState` plus `SimulationKernel.fire_ground_weapon` require a
  tracked hostile Ground contact, finite rifle range, ammunition, and
  cooldown, and enter the shared effects/damage bridge on a successful shot.
  The shot is released only when the environment's terrain line-of-sight
  query reports the sight line visible, from the shooter's authored eye
  height to the target's authored centre-of-mass height for each held
  stance; blocked terrain, unknown terrain, or unauthored posture geometry
  rejects it before any round, cooldown, or hit roll is consumed. The
  posture heights are `engineering_proxy` content, not calibrated
  anthropometry. This is a deterministic close-range proxy; it does not
  claim cover, concealment, suppression, ballistics, indirect fire, or a
  complete fire-control model
  (`tests/runtime/ground/test_ground_infantry_native_unit.py`,
  `src/tests/test_ground_direct_fire_line_of_sight.cpp`).
  These native probe bindings live on the quarantined
  `bindings_core_kernel_diagnostics_ground.cpp` diagnostics surface, not the
  maintained `SimulationKernel` binding surface.
- A scripted decision model for the infantry fixture is registered behind the
  neutral `DecisionModelRegistry` as
  `ground.infantry.objective_occupy_scripted` (`adapter`, role
  `ground_infantry_controller`, `python/tasking_contracts/ground/`). It
  consumes only own position, own operational state, and the commander-issued
  assigned target and fire authorization read back from its own mission
  command, and emits the admitted command shape: `MoveStatic`
  heading/speed/stance with `route_intent=direct` until the task tolerance is
  reached, then a latched `OccupyStatic`/`SupportStatic` hold. A fire request
  is input-gated on that assignment and authorization; the native
  `fire_ground_weapon_from_mission_command` gate keeps holder, contact, range,
  ammunition, and cooldown authority, and the model writes no authority. On
  the native kernel it reaches and holds the objective, replays
  byte-identically for one seed, is accepted by the native gate when the
  soldier is the authority holder and rejected when another entity holds it,
  and makes identical decisions when only hostile geometry changes
  (`tests/runtime/ground/test_ground_scripted_native_replay.py`). The
  replay uses the quarantined native-probe surface, not a production
  `WorldBatch` path.
- Ground scripted capability labels are declared per capability in
  `python/tasking_contracts/ground/capability.py`. `admitted_bounded`, each
  with a named runtime owner: `single_unit_movement`, `static_hold`,
  `local_terrain_interaction`, `bounded_direct_fire_request`. `held`:
  `route_planning`, `general_passability`, `line_of_sight_cover_concealment`,
  `ground_sensing_track_export`, `observation_export`,
  `effects_damage_consequence`, `indirect_fire`, `suppression`, `logistics`,
  `multi_unit_formation`. A request for a held capability fails closed. The
  domain label is derived from the movement, terrain-interaction, sensing,
  fires, effects, damage, and observation-export gate and is
  `bounded_adapter` while any of those owners is held; it MUST NOT be
  reported as `playable`
  (`tests/architecture/tasking_contracts/test_ground_capability_labels.py`).

## Registered And Reachable, But Not A Capability

`src/models/domains/ground/` owns a structured ground effects route. It selects a
target only when the ground-owned `GroundPlatformDamageState` and the shared
hitbox, system-health, and platform-damage surfaces are all present, applies
warhead mechanism load into the ground state, projects that state onto the shared
capability fields, and then calls the shared finalize. The component id is resolved
once per world in the composition path and passed to the route — the effects unit no
longer resolves a component type to find it — so the route selects and the mechanism
runs. Measured `2026-09-22`: one structural hit against a spawned ground element
leaves the shared capability vector at `[0.8167, 1.0000, 0.9010, 0.8680]` rather than
the placeholder fallback's all-zero destroyed result, and every world of a
many-world process produces that same consequence. The repair and its measurements
are recorded in
[Ground Damage Effects Route Repair](../../../domains/ground/reviews/ground_damage_effects_route_repair_20260922/README.md).

A reachable mechanism is still not a capability. This is not a released Ground effects
model: no Ground task, scenario, or observation claim may rest on it. No Ground hit
degrades mobility today on the synthesized bootstrap surface every shipped Ground unit uses,
for any warhead family: the effects model estimates warhead mechanism load only for
structured air targets, so the chassis mobility and track branches cannot be reached on
that surface. On `2026-09-28` the expectation that a hit degrades mobility was withdrawn
rather than satisfied with uncalibrated physics. An authored Ground `damage_model` with an
`engine`/`fuel` system is a separate, known exposure: it reaches `mobility_capability`
through a pre-existing generic non-air system-name coefficient, recorded and scoped in the
route-repair package rather than claimed as Ground damage fidelity. The current contract is
pinned by a runtime test, and the component-attributed follow-up with its entry conditions
is recorded in the route-repair package.
See the
[DM-G1 reachability diagnosis](../../../systems/combat/reviews/ground_damage_reachability_20260921.md)
for the pre-repair measurement that located the cause.

`src/systems/domains/ground/` owns the Ground per-tick systems surface. The
ground damage response is registered from
`src/systems/domains/ground/damage_system_ground.h` as
`builtin.system.ground_damage` at stage 30 of the default composition, and it is
paired with `GroundInfantryMovement` from
`src/systems/domains/ground/movement_system.h` as
`builtin.system.ground_infantry_movement` at stage 34. That second system is a
bounded single-step consumer for the individual infantry fixture, not a release
of route movement, passability, sensing, fires, logistics, or observation export.
The admission is recorded in [Ground Infantry Movement v1](../reviews/ground_infantry_movement_v1_20260924/README.md).

## Content And Capability Rules

- New maintained Ground unit definitions MUST use native Ground identity rather
  than an `Aircraft` substitute.
- `Ground_Platoon_MVP` MAY be used as evidence for native schema loading,
  static identity, health/state inspection, and the static task/status chain.
- Compatibility-shell scenarios that spawn `Aircraft` MAY remain as regression
  fixtures, but MUST declare that boundary and MUST NOT be cited as native
  Ground platform evidence.
- The platoon `ground_mobility_flat_deferred` declaration and
  `static_or_caller_initial_velocity_only` behavior MUST NOT be described as
  route movement or terrain mobility. The individual infantry declaration may
  cite only the bounded `MoveStatic` surface/slope step admitted above.
- A future Ground system, model, or scenario MUST extend shared runtime stages
  and contracts. It MUST NOT introduce a Ground-only scheduler, packet family,
  or command/status pipeline.

## Held Boundaries

The current maintained surface does not establish, beyond the bounded local
slices admitted above:

- route following, waypoint/route planning, acceleration/fatigue/formation
  dynamics, a route graph, a general passability mask, or route-level
  river-crossing planning, obstacles, or breach behavior (the admitted surface
  is a local one-tick transition sample and block, not a route product);
- Ground sensing, line of sight beyond the bare-earth terrain gate on the
  bounded rifle, cover, concealment, track fusion, data-link behavior, or
  observation export beyond the bounded terrain/transition/field-semantic
  observation tuples named above;
- indirect fire, suppression, attrition, full fire control, ballistics, or a
  combat runtime
  (the admitted direct-fire slice is a deterministic close-range proxy on a
  quarantined diagnostics binding surface, not a fire-control or ballistics
  model, and the ground damage mechanism it feeds remains a reachable
  mechanism rather than a released effects capability);
- logistics, sustainment, recovery, or a learned Ground policy;
- formal Ground `CommandPacket`, `ObservationPacket`, or `TrackPacket`
  specializations.

These areas require separate standards and acceptance evidence before a task or
scenario can claim them as maintained capabilities. A reachable mechanism is not that
evidence: the ground damage mechanism now runs and produces the measured consequence
above for the hit the runtime suite exercises, and that still does not make effects,
damage, suppression, or attrition a Ground capability, a scenario claim, or a model the
domain may rely on.

## Verification

Current evidence anchors:

- [Ground component boundary](../../../../src/components/domains/ground/README.md)
- [Ground tasking component boundary](../../../../src/components/domains/ground/tasking/README.md)
- [Ground model boundary](../../../../src/models/domains/ground/README.md)
- [Ground native platform schema tests](../../../../tests/runtime/ground/test_ground_native_platform_schema.py)
- [Ground native static scenario tests](../../../../tests/runtime/ground/test_ground_native_static_scenario.py)
- [Ground native infantry movement test](../../../../tests/runtime/ground/test_ground_infantry_native_unit.py)
- [Ground damage response tests](../../../../tests/runtime/ground/test_ground_damage_response.py)
- [Ground scripted native replay tests](../../../../tests/runtime/ground/test_ground_scripted_native_replay.py)
- [Ground scripted capability label tests](../../../../tests/architecture/tasking_contracts/test_ground_capability_labels.py)
- [Ground realism-gradient guardrails](../../../../tests/architecture/ground/test_realism_gradient_guardrails.py)

## Non-goals

This standard does not authorize work, define Army doctrine, or promote the
current static MVP into a complete land-warfare model. Active work and maturity
decisions belong with the [Ground owner](../../../domains/ground/README.md).
