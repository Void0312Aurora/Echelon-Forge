# G6 Realism Gradient MVP Scenarios

Status: `2026-05-24` opened for the first ground domain realism-gradient MVP
scenario batch. `G6-A Planning Surface` and `G6-B G1 Scenario Implementation`
are implemented and locally validated.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn planning slice.

Inputs:

- [G5 MVP scenario](../g5_mvp_scenario/README.md)
- [Ground current progress](../ground_current_progress_20260524.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Define the first post-G5 ground scenario batch as a realism-gradient MVP, not as
a broad land-combat implementation.

G5 already proves the tasking smoke path:

`ScenarioLoader -> normalized ground TaskOrder -> LeaderIntent -> PilotReport`.

G6 records and begins the next safe release order:

1. keep G0/G5 tasking smoke as the existing baseline;
2. add G1 static occupy;
3. add G1 support relationship;
4. hold G2 flat route move until runtime-loadable ground platforms or an
   explicit compatibility boundary are accepted;
5. defer contact reporting, fires, effects, damage, and combat.

The `G6` phase name here is a project dispatch phase, not the
`G6 effects/damage/termination` row in the realism-gradient table.

## Output

- [G6 realism-gradient MVP scenario cluster](g6_realism_gradient_mvp_scenario_cluster_20260524.md)
- Canonical G1 scenarios:
  - `scenarios/ground/ground_platoon_static_occupy_v1.json`
  - `scenarios/ground/ground_platoon_support_relationship_v1.json`
- Focused validation:
  `tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py`

## Scope

In scope:

- one bounded planning surface named `G6-A Planning Surface`
- one bounded implementation slice named `G6-B G1 Scenario Implementation`
- first-batch scenario ordering by realism gradient
- explicit release gates for G1 static occupy and G1 support relationship
- a deferred path for G2 flat route move
- a residual map for G4 contact report and later fire/damage work
- subagent distribution constraints from the authoritative governance policy
- two G1 compatibility-shell scenario fixtures plus focused loader/tasking
  validation

Out of scope:

- runtime-loadable ground unit schemas
- movement release without a platform or compatibility decision
- terrain traversal, terrain masking, line-of-sight, sensing, contact reports,
  fires, effects, damage, suppression, or combat
- runtime code, Python profile changes, bindings, or C++ DTO changes

## Gate

G6-A is complete when the planning package states:

- the selected MVP scenario batch and release order;
- the gradient boundary between tasking-only, static spatial behavior, support
  relationship behavior, flat route movement, contact reporting, and fires or
  damage;
- that G1 scenarios prove only static occupy/support semantics and do not prove
  movement, terrain, sensing, fires, or damage;
- that G2 flat route move must wait for a runtime-loadable ground platform or a
  documented compatibility boundary before release;
- the task cluster goal, write set, non-goals, validation, closure gate,
  parallel/dependency relationship, round cap, and Model / reasoning field.

G6-B is complete when both G1 scenarios:

- load through `ScenarioLoader` against the standard example database;
- resolve through the maintained `ground` tasking profile;
- produce Army/common-core `TaskOrder`, `LeaderIntent`, and `PilotReport`
  status objects in the kernel;
- assert `realism_gradient.grade = G1`;
- explicitly defer movement, terrain, sensing, fires, damage, formal
  `CommandPacket`, `ObservationPacket`, and `TrackPacket` claims.

Validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py
```

## Residuals

- Resolve the G2 movement release boundary before publishing flat route move.
- Keep contact reports, observation export, fires, damage, suppression, and
  combat in later scoped work packages.
