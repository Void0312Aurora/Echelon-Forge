# A2 High-Fidelity Damage Model

Status: `2026-06-19` active follow-on index plus local archive registry. The
sealed base A2 research/candidate package remains in the outer air-combat
archive:
[archive/a2_high_fidelity_damage_model](../archive/a2_high_fidelity_damage_model/README.md).
Completed or superseded local MLF follow-ons have been physically moved under
this directory's [archive/](archive/README.md) tree and are registered in
[archive_registry.md](archive_registry.md).

This root intentionally keeps only live, retained, or planning entries so the
A2 follow-on surface does not flatten into a long list of completed projects.

## Live / Retained Entries

- [damage_consequence_reward_surface/README.md](damage_consequence_reward_surface/README.md):
  active bounded training-feedback work for damage consequences rather than a
  single kill flag.
- [missile_lethality_target_geometry/README.md](missile_lethality_target_geometry/README.md):
  accepted / retained follow-on promoted from the hitbox-geometry gap issue. It
  keeps reviewable F-16C outer regions, component bindings, distance diagnostics,
  fine geometry proxies, surface/internal receiver priors, and cross-region
  split receiver handoff evidence. It does not claim true F-16 engineering
  geometry, default runtime replacement, training benefit, structural breakup,
  debris/wreck, Pk, or weapon-specific lethality.

## Archived / Registered Entries

Use [archive_registry.md](archive_registry.md) for the compact registry. The
physical evidence packets are under [archive/](archive/README.md):

- [archive/missile_lethality_model_foundation/README.md](archive/missile_lethality_model_foundation/README.md):
  MLF-1 chain-contract foundation and phase-boundary evidence.
- [archive/missile_lethality_geometry_fuze/README.md](archive/missile_lethality_geometry_fuze/README.md):
  MLF-2 missile approach-geometry and fuze-evaluation evidence.
- [archive/missile_lethality_proximity_fuze_realism/README.md](archive/missile_lethality_proximity_fuze_realism/README.md):
  accepted-with-residuals proximity-fuze realism evidence slice.
- [archive/missile_lethality_warhead_effects/README.md](archive/missile_lethality_warhead_effects/README.md):
  MLF-3 generic warhead-effects, fragment/blast-load, and diagnostics evidence.
- [archive/missile_lethality_continuous_rod/README.md](archive/missile_lethality_continuous_rod/README.md):
  MLF-4 continuous-rod and cutting-mechanism fact evidence.
- [archive/missile_lethality_component_failure/README.md](archive/missile_lethality_component_failure/README.md):
  MLF-5 component vulnerability and failure-fact evidence.
- [archive/missile_lethality_structural_failure/README.md](archive/missile_lethality_structural_failure/README.md):
  accepted / archived MLF-6 structural-failure and airframe-breakup fact writer.
- [archive/missile_lethality_secondary_consequence_coupling/README.md](archive/missile_lethality_secondary_consequence_coupling/README.md):
  accepted / archived MLF-7 secondary consequence coupling. The runtime bridge
  consumes archived MLF-6 breakup facts, writes bounded consequences into
  maintained aircraft damage, platform damage, and loss-state surfaces, and
  emits chain-linked `platform_consequence` diagnostics.
- [archive/missile_lethality_debris_wreck_lifecycle/README.md](archive/missile_lethality_debris_wreck_lifecycle/README.md):
  accepted / archived MLF-8 debris and wreck lifecycle evidence. The runtime
  records diagnostics-only detached-part and terminal-wreck lifecycle facts
  linked to accepted MLF-6/MLF-7 evidence, while keeping first-class debris/wreck
  entities, debris physics, reward authority, Pk, and calibration authority
  refused.

The current geometry-fidelity gap is tracked on the issue board:
[Lethality Hitbox Geometry Fidelity Gap](../../issues/lethality_hitbox_geometry_fidelity_gap/README.md).
The first mainline execution entry for that issue has been closed against the
geometry-only acceptance gate:
[missile_lethality_target_geometry/README.md](missile_lethality_target_geometry/README.md).

MLF-8 (debris/wreck lifecycle) is accepted and archived:
[archive/missile_lethality_debris_wreck_lifecycle/README.md](archive/missile_lethality_debris_wreck_lifecycle/README.md).
The old active path is only a compatibility pointer:
[missile_lethality_debris_wreck_lifecycle/README.md](missile_lethality_debris_wreck_lifecycle/README.md).
MLF-9 (Pk/statistical trends) and MLF-10 (calibration gates) still need
separate follow-on subprojects. Do not continue inside archived MLF-1 through
MLF-8 or proximity-fuze realism packages. These follow-ons do not reopen the
sealed A2 package or create A9.

Reopen this line only through an explicit authority-promotion or new research
request. Default air-combat work continues from [../README.md](../README.md).
