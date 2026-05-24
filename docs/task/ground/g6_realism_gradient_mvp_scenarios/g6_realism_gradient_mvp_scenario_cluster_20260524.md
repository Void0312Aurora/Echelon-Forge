# G6 Realism Gradient MVP Scenario Cluster

Status: `2026-05-24` implemented for the planning surface and the first two G1
realism-gradient MVP scenario fixtures.

Clusters:

- `G6-A Planning Surface`
- `G6-B G1 Scenario Implementation`

Round caps:

- `G6-A`: one implementation round.
- `G6-B`: one implementation round plus at most one repair round.

## Decision

G6 opens a follow-on ground scenario subproject after G5 and releases the first
two G1 compatibility-shell fixtures.

Terminology note: the `G6` cluster name is a project dispatch phase, not the
domain-realism grade `G6 effects/damage/termination`. This cluster accepts only
`G1` static realism fixtures.

The first MVP batch should advance by domain-realism gradient:

1. `G0/G5 tasking smoke` remains the accepted baseline for ground tasking-chain
   participation.
2. `G1 static occupy` is the first new scenario.
3. `G1 support relationship` is the second new scenario.
4. `G2 flat route move` is a follow-on or optional candidate, not a first-batch
   release, until runtime-loadable ground platforms or an explicit
   compatibility boundary are accepted.
5. `G4 contact report` and `G5/G6 fire/damage` are deferred.

The first G1 scenarios prove only static occupy and support relationship
semantics. They must not be cited as evidence for movement, terrain traversal,
terrain masking, line-of-sight, sensing, fires, effects, damage, suppression,
or combat.

## Gradient Boundary

| Gradient | Scenario capability | Release posture | Proof allowed | Proof forbidden |
|----------|---------------------|-----------------|---------------|-----------------|
| `G0/G5` | tasking smoke | already accepted baseline | loader/profile tasking chain and Army/common-core status production | maintained ground platform, movement, terrain, sensing, fires, damage |
| `G1` | static occupy | first MVP batch | static occupy intent and static spatial anchoring | route movement, terrain traversal, sensing, fires, damage |
| `G1` | support relationship | first MVP batch | relationship between supported and supporting ground tasks | movement, terrain, sensing, fires, damage, contact report |
| `G2` | flat route move | follow-on or optional only | flat route intent after platform or compatibility release boundary exists | terrain traversal, obstacle modeling, LOS, sensing, fires, damage |
| `G4` | contact report | deferred | later observation/contact semantics | any first-batch proof |
| `G5/G6` | fire and damage | deferred | later fire/effects/damage semantics | any first-batch proof |

Critical boundary: `G2 flat route move` must not be released merely because a
JSON scenario can be shaped. It needs either a runtime-loadable ground platform
path or an explicit compatibility boundary documenting what shell is being used,
what it proves, and what it refuses to prove.

## First-Batch Scenario List

Implemented first batch:

- `ground_platoon_static_occupy_v1`: G1 static occupy fixture.
- `ground_platoon_support_relationship_v1`: G1 support relationship fixture.

Held for follow-on or optional release:

- `ground_platoon_flat_route_move_v1`: G2 flat route move candidate, gated by
  runtime-loadable ground platform availability or a documented compatibility
  boundary.

Deferred:

- contact report scenarios;
- fire, effects, damage, suppression, or combat scenarios.

## Task Cluster

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `G6-A Planning Surface` | worker | `gpt-5.4`, medium | Create the planning package for first-batch realism-gradient MVP scenarios. | `docs/task/ground/g6_realism_gradient_mvp_scenarios/**` | scenario files, tests, code, README indexes, dispatch queues | `git diff -- docs/task/ground/g6_realism_gradient_mvp_scenarios` | README and cluster doc record decision, gates, write set, distribution rules, and residual map | parallel-safe with G6-B because its write set is disjoint; downstream scenario release depends on this decision record | 1 round | accepted |
| `G6-B G1 Scenario Implementation` | worker | `gpt-5.4`, medium | Add the first two G1 static realism-gradient scenarios and focused validation. | `scenarios/ground/ground_platoon_static_occupy_v1.json`, `scenarios/ground/ground_platoon_support_relationship_v1.json`, `tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py` | docs/index edits, code, C++ DTOs, runtime platform schemas, movement, terrain, sensing, fires, damage | `python -m pytest tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py -q` | both fixtures load, resolve through ground profile, assert G1 boundaries, and preserve occupy/support common-core semantics | parallel-safe with G6-A because write sets are disjoint; final README/index sync is serial integration | 1 round plus at most 1 repair round | accepted |

## Write Set

G6-A allowed write set:

- `docs/task/ground/g6_realism_gradient_mvp_scenarios/README.md`
- `docs/task/ground/g6_realism_gradient_mvp_scenarios/g6_realism_gradient_mvp_scenario_cluster_20260524.md`

Forbidden for G6-A:

- `docs/task/ground/README*.md`
- `docs/task/ground/ground_subagent_dispatch_queue_*.md`
- `scenarios/**`
- `tests/**`
- `python/**`
- `src/**`
- standards indexes or unrelated task docs

G6-B allowed write set:

- `scenarios/ground/ground_platoon_static_occupy_v1.json`
- `scenarios/ground/ground_platoon_support_relationship_v1.json`
- `tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py`

## Acceptance Criteria

G6-A is accepted only if all checks below are true:

- The planning package is created under
  `docs/task/ground/g6_realism_gradient_mvp_scenarios/`.
- The package identifies `G6-A Planning Surface` as the named task cluster.
- The package records the first-batch decision: G1 static occupy and G1 support
  relationship are the first MVP scenario candidates.
- The package records that G2 flat route move is follow-on or optional until a
  runtime-loadable ground platform path or explicit compatibility boundary is
  accepted.
- The package records that G4 contact report and G5/G6 fire/damage are deferred.
- The package states that G1 scenarios prove only static occupy/support
  semantics and do not prove movement, terrain, sensing, fires, or damage.
- The package includes goal, write set, non-goals, validation, closure gate,
  parallel/dependency relationship, round cap, and Model / reasoning.
- No README index, dispatch queue, scenario, test, or code file is modified by
  this cluster.

G6-B is accepted only if all checks below are true:

- `ground_platoon_static_occupy_v1.json` is a `G1` scenario and documents its
  compatibility spawn shell.
- `ground_platoon_support_relationship_v1.json` is a `G1` scenario and
  documents its compatibility spawn shell.
- Both scenarios defer movement, terrain, sensing, fires, damage, formal
  `CommandPacket`, `ObservationPacket`, and `TrackPacket` claims.
- The focused test validates loader/profile resolution plus Army/common-core
  task, intent, and report status propagation.
- `TASK_OCCUPY` proves `Defend / TACON / Independent` semantics only.
- `TASK_SUPPORT` proves `Defend / Support / Support` semantics and preserves
  `supported_node_id` and `supporting_node_id`.

## Distribution Packet

Use this packet if the main thread dispatches follow-on implementation workers:

```md
Cluster: G6-A Planning Surface
Model / reasoning: gpt-5.4, medium
Round cap: 1 implementation round
Goal: Record the first-batch ground realism-gradient MVP scenario decision.
Write set: docs/task/ground/g6_realism_gradient_mvp_scenarios/**
Non-goals: scenarios, tests, code, README indexes, dispatch queues.
Validation: git diff -- docs/task/ground/g6_realism_gradient_mvp_scenarios
Closure gate: package records decision, gates, write set, residuals, and
subagent policy fields.
Parallel/dependency: parallel-safe with disjoint implementation workers; later
scenario release depends on this decision record.
```

Accepted G6-B packet:

```md
Cluster: G6-B G1 Scenario Implementation
Model / reasoning: gpt-5.4, medium
Round cap: 1 implementation round plus at most 1 repair round
Goal: Add G1 static occupy and support relationship scenarios plus focused
validation.
Write set: scenarios/ground/ground_platoon_static_occupy_v1.json,
scenarios/ground/ground_platoon_support_relationship_v1.json,
tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py
Non-goals: docs/index edits, code, native ground runtime, movement, terrain,
sensing, fires, damage.
Validation: python -m pytest
tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py -q
Closure gate: both scenarios load through ScenarioLoader, resolve to ground,
assert G1 boundary, and preserve expected common-core semantics.
Parallel/dependency: parallel-safe with G6-A; final integration is serial.
```

Worker result format must follow the authoritative
[Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md):

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Verification Suggestions

Documentation check for G6-A:

```powershell
git diff -- docs/task/ground/g6_realism_gradient_mvp_scenarios
```

Scenario validation for G6-B:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\ground\test_ground_realism_gradient_mvp_scenarios.py
```

Tests explicitly assert deferred surfaces so G1 fixtures cannot be treated as
proof of movement, terrain, sensing, fires, damage, observation export, or
combat.

## Residual Map

Compatibility-gated:

- release G2 flat route move only after runtime-loadable ground platforms are
  accepted or a compatibility boundary is written and approved.

Deferred:

- terrain traversal and terrain masking;
- line-of-sight and sensing;
- contact reporting and observation export;
- direct fire, indirect fire, effects, damage, suppression, and combat;
- broad mission-command expansion beyond the accepted tasking/profile chain.
