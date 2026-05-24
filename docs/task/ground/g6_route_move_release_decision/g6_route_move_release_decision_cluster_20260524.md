# G6-D Route-Move Release-Decision Cluster

Status: `2026-05-24` accepted for `G6-D0 Route-Move Release Decision`.
`G6-D1`, `G6-D2`, and `G6-D3` remain held. No movement scenario is released.

Clusters:

- `G6-D0 Route-Move Release Decision`
- `G6-D1 Native Ground Platform Schema Preflight`
- `G6-D2 Movement Evidence Gate Preflight`
- `G6-D3 Serial Integration And Release Vote`

Round caps:

- `G6-D0`: one main-thread documentation round.
- `G6-D1`: one read-only diagnostics round plus at most one repair round.
- `G6-D2`: one read-only diagnostics round plus at most one repair round.
- `G6-D3`: one serial integration round.

## Decision

G6-D chooses the schema-first route for the first `G2` ground route-move
release.

Accepted posture:

- `ground_platoon_flat_route_move_v1` remains held.
- The current `Aircraft` compatibility spawn shell remains valid for G0/G1
  tasking/status/static fixtures only.
- `G2` route movement requires a runtime-loadable native ground platform schema
  before release.
- A future compatibility boundary may be proposed, but it cannot release a `G2`
  movement-realism scenario unless it proves the same critical points and
  explicitly names the shell, allowed proof, forbidden proof, and residuals.

Rejected posture:

- Do not use an `Aircraft` shell plus route-intent JSON as evidence for ground
  movement realism.
- Do not add `ground_platoon_flat_route_move_v1` as a compatibility-only G2
  fixture.
- Do not treat task-order route fields as movement-state evidence.

## Minimum G2 Critical Points

A later flat-route movement release must prove all of these before claiming
`G2` movement realism:

| Critical point | Minimum evidence |
|----------------|------------------|
| native ground entity | runtime-loadable entity/schema that is explicitly ground, not an airframe shell |
| route intent | ordered waypoints or route anchor fields mapped from accepted ground tasking inputs |
| movement state | position, heading/orientation, speed, and active movement status update from runtime state |
| ground speed envelope | speed min/max/defaults are ground-unit scoped and do not inherit aircraft cruise assumptions |
| cadence | movement evidence is sampled at the accepted ground tactical cadence or a documented compatible cadence |
| flat passability | the scenario states that only flat/passable movement is claimed and that terrain-aware degradation is deferred |
| off-route/stuck boundary | tests or contracts detect no-move, off-route, or unsupported-state cases rather than silently passing |
| deferred surfaces | terrain traversal, terrain masking, sensing, fires, damage, observation export, and combat remain explicitly deferred |

## Task Cluster

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `G6-D0 Route-Move Release Decision` | main-thread integration | current main thread | Record the selected route-move release posture and future dispatch surface. | `docs/task/ground/g6_route_move_release_decision/**`, ground README/queue/progress/plan sync | scenario files, tests, runtime code, native schema implementation, movement behavior | `git diff --check` over touched ground docs; focused architecture guard remains green | schema-first decision recorded; compatibility-shell G2 release rejected; finite follow-on packets named | blocks all later G2 route-move implementation | 1 documentation round | accepted |
| `G6-D1 Native Ground Platform Schema Preflight` | future explorer | `gpt-5.4`, high | Inventory the smallest runtime-loadable native ground platform schema path. | read-only diagnostics first; later docs only if explicitly released | scenario release, runtime movement, bindings, C++ DTO implementation | source inventory plus proposed validation commands | identifies minimal files, schema fields, loader risks, and blockers without editing implementation | parallel-safe with G6-D2 after G6-D0 | 1 diagnostics round plus at most 1 repair round | held |
| `G6-D2 Movement Evidence Gate Preflight` | future explorer | `gpt-5.4`, high | Define the exact test/evidence gates for flat route movement. | read-only diagnostics first; later tests only if explicitly released | platform schema implementation, terrain, sensing, fires, damage, combat | source inventory plus proposed tests/contracts | names state hooks and failure cases needed to prove movement, not just tasking intent | parallel-safe with G6-D1 after G6-D0 | 1 diagnostics round plus at most 1 repair round | held |
| `G6-D3 Serial Integration And Release Vote` | main-thread integration | current main thread | Accept or block route-move implementation release after D1/D2 evidence. | ground queue/progress/README sync and any approved cluster docs | implementation before preflight returns | focused docs check plus any D1/D2 proposed commands | either releases a bounded implementation cluster or records blocked residuals | dependency-gated after D1/D2 | 1 integration round | held |

## Distribution Packets

Future workers must follow the
[Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
and return the required packet format.

### `G6-D1 Native Ground Platform Schema Preflight`

```md
Cluster: G6-D1 Native Ground Platform Schema Preflight
Model / reasoning: gpt-5.4, high
Round cap: 1 diagnostics round plus at most 1 repair round
Goal: Identify the smallest runtime-loadable native ground platform schema path
needed before route-move release.
Write set: read-only diagnostics first; do not edit implementation files.
Non-goals: scenario release, movement dynamics, terrain, sensing, fires,
damage, C++ DTO implementation, bindings, or facade changes.
Validation: source inventory and proposed commands for loader/schema checks.
Closure gate: packet names minimal files, schema fields, loader compatibility
risks, tests required, and blockers.
Parallel/dependency: starts only after G6-D0; parallel-safe with G6-D2.
```

### `G6-D2 Movement Evidence Gate Preflight`

```md
Cluster: G6-D2 Movement Evidence Gate Preflight
Model / reasoning: gpt-5.4, high
Round cap: 1 diagnostics round plus at most 1 repair round
Goal: Define evidence gates proving flat route movement state rather than
route-intent JSON only.
Write set: read-only diagnostics first; do not edit implementation files.
Non-goals: platform schema implementation, terrain-aware movement, sensing,
fires, damage, combat, or observation export.
Validation: source inventory and proposed focused tests/contracts.
Closure gate: packet names state hooks, pass/fail cases, deferred surfaces, and
commands required before `ground_platoon_flat_route_move_v1` can be released.
Parallel/dependency: starts only after G6-D0; parallel-safe with G6-D1.
```

## Acceptance Criteria

G6-D0 is accepted only if all checks below are true:

- The release-decision package exists under
  `docs/task/ground/g6_route_move_release_decision/`.
- The package selects schema-first for the first `G2` route-move release.
- The package rejects compatibility-shell route movement as sufficient G2
  evidence.
- The package defines minimum G2 flat-route critical points.
- The package records future cluster goals, write sets, non-goals, validation,
  closure gates, dependency rules, round caps, and Model / reasoning.
- Ground README, bootstrap plan, dispatch queue, and progress tracking point to
  this decision without releasing a movement scenario.

Downstream implementation is blocked until G6-D3 accepts a bounded release
cluster after D1/D2 evidence.

## Verification Suggestions

Documentation check:

```bash
git diff --check -- docs/task/ground
```

Current guardrail check:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_ground_realism_gradient_guardrails.py
```

## Residual Map

Held:

- `ground_platoon_flat_route_move_v1`;
- runtime-loadable native ground platform schema;
- route movement runtime state update;
- terrain-aware movement, obstacle handling, cover, concealment, and
  line-of-sight;
- sensing, contact reporting, fires, effects, damage, suppression, combat, and
  sustainment.
