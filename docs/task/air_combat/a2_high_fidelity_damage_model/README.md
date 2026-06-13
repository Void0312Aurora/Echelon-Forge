# A2 High-Fidelity Damage Model

Status: `2026-06-11` archived pointer / active follow-on navigation. The full project package was moved to
[archive/a2_high_fidelity_damage_model](../archive/a2_high_fidelity_damage_model/README.md).

This path is retained only as a lightweight work statement for navigation.

The archived A2 package closed the research/candidate profile for the
air-combat high-fidelity damage-model line. It retains non-authoritative
blast-fragmentation evidence, accepted G1-G5 research packets, and a structured
aircraft damage/effects runtime record. It does not release stock authority,
Pk authority, deterministic fuze authority, or broader weapon-outcome
authority.

Current A2 follow-ons:

- [damage_consequence_reward_surface/README.md](damage_consequence_reward_surface/README.md):
  bounded training feedback for damage consequences rather than a single kill
  flag.
- [missile_lethality_model_foundation/README.md](missile_lethality_model_foundation/README.md):
  archived MLF-1 chain-contract foundation, retained as field and boundary
  evidence for later stages.
- [missile_lethality_geometry_fuze/README.md](missile_lethality_geometry_fuze/README.md):
  archived MLF-2 evidence package for missile approach geometry and fuze
  evaluation; it proves that nearest point, fuze evaluation, and detonation
  handoff are observable, but it does not implement fragmentation, structural
  breakup, Pk, or weapon-specific kill conclusions.
- [missile_lethality_warhead_effects/README.md](missile_lethality_warhead_effects/README.md):
  archived MLF-3 evidence package for post-detonation generic warhead effects,
  fragment/blast loads, spatial coverage, component load, diagnostics, and the
  no-detonation no-load gate; it does not implement continuous rod, component
  failure probability, structural breakup, debris/wreck, Pk, or weapon-specific
  kill conclusions.
- [missile_lethality_continuous_rod/README.md](missile_lethality_continuous_rod/README.md):
  archived MLF-4 evidence package for continuous-rod and cutting-mechanism
  facts; it proves the rod/cut exposure fact chain is observable, diagnosable,
  and projected into component-load rows, but it does not claim component
  failure, structural breakup, debris/wreck, Pk, or weapon-specific lethality.
- [missile_lethality_component_failure/README.md](missile_lethality_component_failure/README.md):
  archived MLF-5 evidence package for target component vulnerability and failure
  facts; it turns MLF-3/MLF-4 component-load/cut-exposure facts into component
  failure probability, failure mode, and state changes, then hands consequences
  to maintained damage/flight systems, but does not claim crash, structural
  breakup, debris/wreck, Pk, or weapon-specific lethality.
- [missile_lethality_target_geometry/README.md](missile_lethality_target_geometry/README.md):
  accepted / retained follow-on promoted from the hitbox-geometry gap issue; it
  has built reviewable F-16C outer regions, component bindings, distance
  diagnostics, fine geometry proxies, surface/internal receiver priors, and
  cross-region split receiver handoff evidence. It does not claim true F-16
  engineering geometry, default runtime replacement, training benefit,
  structural breakup, debris/wreck, Pk, or weapon-specific lethality.

The current geometry-fidelity gap is tracked on the issue board:
[Lethality Hitbox Geometry Fidelity Gap](../../issues/lethality_hitbox_geometry_fidelity_gap/README.md).
The first mainline execution entry for that issue has now been closed against
the geometry-only acceptance gate:
[missile_lethality_target_geometry/README.md](missile_lethality_target_geometry/README.md).

Follow-on structural breakup, wreck/debris, Pk, or weapon-specific
calibration need separate `docs/agent` subprojects and must not continue inside
the archived MLF-2, MLF-3, or MLF-4 packages. The continuous-rod fact chain is
archived; component-failure evidence is now traceable through the MLF-5 archive
pointer above. Structural breakup, wreck/debris, Pk, or weapon-specific
calibration still need follow-on subprojects. MLF-3/MLF-4 are archived; they do
not reopen the sealed A2 package.

These follow-ons do not reopen the sealed A2 package or create A9.

Reopen this line only through an explicit authority-promotion or new research
request. Default air-combat work continues from [../README.md](../README.md).
