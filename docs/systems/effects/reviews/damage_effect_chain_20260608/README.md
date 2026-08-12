# A8 Damage Effect Chain

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/damage_effect_chain_20260608/README.md`
Owner: `systems/effects`
Last verified: `2026-08-09`
Review basis: accepted bounded A8 damage/effects evidence and deferred residuals.

Status: retained accepted slice. The evidence explains the bounded path from
detonation through aircraft-part damage into propulsion, fuel, sensor, fire,
flight, and ground-contact responses. It does not claim real-world Pk,
deterministic fuze truth, aircraft-specific control-law calibration, or debris
authority.

Inputs:

- [Systems owner](../../../README.md)
- [F-16 target-geometry review](../f16c_target_geometry_20260614/README.md)
- [Lethality geometry issue](../../work/issues/lethality_hitbox_geometry_fidelity_gap/README.md)
- [Common damage component](../../../../../src/components/combat/common/damage_common.h)
- [Air damage component](../../../../../src/components/domains/air/combat/damage_air.h)
- [Air damage system](../../../../../src/systems/combat/damage_system_air.h)
- [Effects model](../../../../../src/models/weapons/default_effects_model.cpp)

Verification boundary: current engineering-proxy runtime behavior and focused
MQ-9/AIM-120C-like checks are retained; calibration-grade weapon/target truth
and first-class debris/residue remain deferred.
