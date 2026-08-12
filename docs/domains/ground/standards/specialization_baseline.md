# Ground Specialization Baseline

Language: English canonical; [Chinese companion](specialization_baseline.zh.md).

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/standards/specialization_baseline.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

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
- `src/models/domains/ground/` owns an explicit effects placeholder route that
  preserves legacy finalize-only behavior. It is not a released Ground effects
  model.
- Native and compatibility-shell Ground scenarios use the shared loader and
  tasking bridge; they do not create a private Ground runtime path.

There is no accepted `src/systems/domains/ground/` owner. Absence of that
directory means Ground runtime-system ownership remains held; it does not grant
another domain authority over Ground execution semantics.

## Content And Capability Rules

- New maintained Ground unit definitions MUST use native Ground identity rather
  than an `Aircraft` substitute.
- `Ground_Platoon_MVP` MAY be used as evidence for native schema loading,
  static identity, health/state inspection, and the static task/status chain.
- Compatibility-shell scenarios that spawn `Aircraft` MAY remain as regression
  fixtures, but MUST declare that boundary and MUST NOT be cited as native
  Ground platform evidence.
- The current `ground_mobility_flat_deferred` declaration and
  `static_or_caller_initial_velocity_only` behavior MUST NOT be described as
  route movement or terrain mobility.
- A future Ground system, model, or scenario MUST extend shared runtime stages
  and contracts. It MUST NOT introduce a Ground-only scheduler, packet family,
  or command/status pipeline.

## Held Boundaries

The current maintained surface does not establish:

- route following, movement dynamics, terrain traversal, passability, cover,
  concealment, obstacles, or breach behavior;
- Ground sensing, line-of-sight computation, track fusion, data-link behavior,
  or observation export;
- direct fire, indirect fire, effects, damage, suppression, attrition, or combat runtime;
- logistics, sustainment, recovery, or a learned Ground policy;
- formal Ground `CommandPacket`, `ObservationPacket`, or `TrackPacket`
  specializations.

These areas require separate standards and acceptance evidence before a task or
scenario can claim them as maintained capabilities.

## Verification

Current evidence anchors:

- [Ground component boundary](../../../../src/components/domains/ground/README.md)
- [Ground tasking component boundary](../../../../src/components/domains/ground/tasking/README.md)
- [Ground model placeholder boundary](../../../../src/models/domains/ground/README.md)
- [Ground native platform schema tests](../../../../tests/runtime/ground/test_ground_native_platform_schema.py)
- [Ground native static scenario tests](../../../../tests/runtime/ground/test_ground_native_static_scenario.py)
- [Ground realism-gradient guardrails](../../../../tests/architecture/ground/test_realism_gradient_guardrails.py)

## Non-goals

This standard does not authorize work, define Army doctrine, or promote the
current static MVP into a complete land-warfare model. Active work and maturity
decisions belong with the [Ground owner](../../../domains/ground/README.md).
