# Cross-Domain Systems

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/README.md`
Owner: `cross-domain simulation systems`
Last verified: `2026-08-08`

This target area owns environment, physics, sensing, command/tasking, weapons,
and effects/damage documentation that applies across mission domains. It keeps
shared mechanisms out of the `air`, `naval`, and `ground` ownership trees.
Current normative routes use this owner’s `standards/` surface; scoped work is
kept with the applicable nested owner. The current cross-domain realism gate is
[Gradient Realism Principles](standards/gradient_realism_principles.md).

## Current Owner Routes

- Environment owner: [environment systems](environment/README.md), including
  G0 and Arnis acceptance boundaries.
- Command/tasking issues: [C2 communication](command-tasking/work/issues/c2_communication.md) and [operation layer](command-tasking/work/issues/operation_layer.md).
- Command/tasking reference: [agency authority census](command-tasking/reference/agency_authority_census_20260721.md) and [authority-representation adjudication](command-tasking/reference/t9_authority_representation_adjudication_20260726.md).
- Physics issues: [physics engine roadmap](physics/work/issues/physics_engine_roadmap.md).
- Sensing issues: [sensor and situation plan](sensing/work/issues/sensor_situation.md).
- Weapons issues: [engagement roadmap](weapons/work/issues/weapons_engagement.md), [implementation notes](weapons/work/issues/weapons_engagement_impl.md), and [termination logic](weapons/work/issues/engagement_termination.md); retained guidance evidence is under [guidance mechanism review](weapons/reviews/kill_chain_guidance_mechanism_20260715/README.md).
- Effects issues: [damage-model calibration residuals](effects/work/issues/damage_model_calibration_residuals.md), [damage/control authority coupling](effects/work/issues/damage_control_authority_coupling_gap/README.md), and [lethality/geometry fidelity](effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.md).
- Effects reviews: [F-16C target geometry](effects/reviews/f16c_target_geometry_20260614/README.md), [fire-timing window diagnosis](effects/reviews/fire_timing_window_position_effect_20260615/README.md), and [kill-chain mechanism decoupling](effects/reviews/kill_chain_mechanism_decoupling_20260621/README.md).

`work/issues` pages are planning inputs, not implementation authority. Dated
reviews retain their original evidence boundary and are not current-state
reverification.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for another system-local standard, reference, work item, or review.
