# Ground Specialization Baseline

Language: English canonical; [Chinese companion](specialization_baseline.zh.md).

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/specialization_baseline.md`
Owner: `domains/ground`
Last verified: `2026-09-24`

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
[Ground Damage Effects Route Repair](../../../domains/ground/work/active/ground_damage_effects_route_repair/README.md).

A reachable mechanism is still not a capability. This is not a released Ground effects
model: no Ground task, scenario, or observation claim may rest on it. One expectation
inside it stays open and unowned — a hit carrying neither a blast nor a mobility scale
leaves mobility at `1.0`, so one runtime test stays at `xfail(strict=True)` until an
owner decides whether the projection gains that term or the expectation is withdrawn.
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
The admission is recorded in [Ground Infantry Movement v1](../work/active/ground_infantry_movement_v1/README.md).

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

The current maintained surface does not establish:

- route following, acceleration/fatigue/formation dynamics, terrain traversal,
  passability, cover, concealment, obstacles, or breach behavior;
- Ground sensing, line-of-sight computation, track fusion, data-link behavior,
  or observation export;
- direct fire, indirect fire, effects, damage, suppression, attrition, or combat runtime;
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
- [Ground realism-gradient guardrails](../../../../tests/architecture/ground/test_realism_gradient_guardrails.py)

## Non-goals

This standard does not authorize work, define Army doctrine, or promote the
current static MVP into a complete land-warfare model. Active work and maturity
decisions belong with the [Ground owner](../../../domains/ground/README.md).
