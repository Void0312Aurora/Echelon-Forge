# Cross-Domain Systems

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/systems/README.md`
Owner: `cross-domain simulation systems`
Last verified: `2026-08-07`

This target area owns environment, physics, sensing, command/tasking, weapons,
and effects/damage documentation that applies across mission domains. It keeps
shared mechanisms out of the `air`, `naval`, and `ground` ownership trees.
Current normative and task routes remain under
[standards](../standards/README.md) and scoped task owners during migration.

## Current Owner Routes

- Command/tasking issues: [C2 communication](command-tasking/work/issues/c2_communication.md) and [operation layer](command-tasking/work/issues/operation_layer.md).
- Physics issues: [physics engine roadmap](physics/work/issues/physics_engine_roadmap.md).
- Sensing issues: [sensor and situation plan](sensing/work/issues/sensor_situation.md).
- Weapons issues: [engagement roadmap](weapons/work/issues/weapons_engagement.md), [implementation notes](weapons/work/issues/weapons_engagement_impl.md), and [termination logic](weapons/work/issues/engagement_termination.md).
- Effects reviews: [damage-model evaluation](effects/reviews/air_combat_damage_model_evaluation_20260522.md) and [cross-evaluation](effects/reviews/air_combat_damage_model_cross_eval_20260522.md).

`work/issues` pages are planning inputs, not implementation authority. Dated
reviews retain their original evidence boundary and are not current-state
reverification.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for another system-local standard, reference, work item, or review.
