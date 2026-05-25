# G6-D Route-Move Release-Decision Cluster

Status: `2026-05-25` accepted for `G6-D0 Route-Move Release Decision`;
`G6-D1` and `G6-D2` preflight returned `preflight-only` with native-schema
blockers. `G6-D3` remains held. No movement scenario is released.

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
| `G6-D1 Native Ground Platform Schema Preflight` | main-thread diagnostics | current main thread | Inventory the smallest runtime-loadable native ground platform schema path. | read-only diagnostics; this cluster doc and queue/progress sync | scenario release, runtime movement, bindings, C++ DTO implementation | source inventory plus Python spawn probe | identifies minimal files, schema fields, loader risks, and blockers without editing implementation | parallel-safe with G6-D2 after G6-D0 | 1 diagnostics round plus at most 1 repair round | preflight-only accepted |
| `G6-D2 Movement Evidence Gate Preflight` | main-thread diagnostics | current main thread | Define the exact test/evidence gates for flat route movement. | read-only diagnostics; this cluster doc and queue/progress sync | platform schema implementation, terrain, sensing, fires, damage, combat | source inventory plus proposed tests/contracts | names state hooks and failure cases needed to prove movement, not just tasking intent | parallel-safe with G6-D1 after G6-D0 | 1 diagnostics round plus at most 1 repair round | preflight-only accepted |
| `G6-D3 Serial Integration And Release Vote` | main-thread integration | current main thread | Accept or block route-move implementation release after D1/D2 evidence. | ground queue/progress/README sync and any approved cluster docs | implementation before preflight returns | focused docs check plus any D1/D2 proposed commands | either releases a bounded implementation cluster or records blocked residuals | dependency-gated after D1/D2 | 1 integration round | held |

## D1 Native Schema Preflight Result

Status: `preflight-only accepted`; route-move implementation remains blocked.

Findings:

- The current source-controlled ground fixture is
  `examples/config/database/ground/units/ground_platoon_starter.seed`. Its
  `.seed` suffix intentionally prevents runtime database auto-loading.
- Runtime unit definitions are parsed by
  `src/content/unit_definition_loader.cpp::parse_unit_type()`. The accepted
  unit types are currently `Aircraft`, `Ship`, `Missile`, `Facility`, `C2Node`,
  `Sensor`, `Engine`, `EWSuite`, `RCSProfile`, and `Submarine`; there is no
  accepted `Ground` or `GroundUnit` type.
- The public `UnitType` enum in `src/components/basic/common.h` and Python
  binding in `src/interfaces/python/bindings_core.cpp` likewise expose no
  `Ground` value.
- Scenario materialization currently lowers entity `type` fields into
  `WorldSpawnRequest.type_name` / `ScenarioSpawnLayout.type_name`, then into
  `SimulationKernel::spawn_unit()` or batch runtime spawn requests.
- `SimulationKernel::spawn_unit(..., "Ground", ...)` rejects the request through
  the resolved platform spawn-plan chain with
  `resolved_platform_spawn_plan_type_name_not_found`.
- `Facility` or `C2Node` are not acceptable substitutes for G2 movement
  realism. They may be useful future static infrastructure shells, but they do
  not prove ground mobility, route following, or movement cadence.

Minimum implementation surface before route-move release:

- add an accepted native ground platform definition path, either as a new public
  `UnitType` or as an explicitly documented platform-family/capability-bundle
  materialization path that still produces an inspectable native ground entity;
- make the runtime database loader accept that ground platform schema without
  treating it as an airframe, ship, submarine, facility, or C2 node;
- expose enough Python/runtime identity to assert that a spawned entity is
  ground-native and not the current `Aircraft` compatibility shell;
- define starter ground mobility fields, at minimum flat-route speed envelope,
  movement cadence, and passability/deferred-terrain declarations;
- keep the path inside shared content/platform/runtime setup surfaces, not a
  private ground runtime stack.

Probe outcome:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python - <<'PY'
from python.testing.runtime import ensure_repo_imports, resolve_repo_path
ensure_repo_imports()
import ef_py
print(hasattr(ef_py.UnitType, "Ground"))
sim = ef_py.SimulationKernel()
print(sim.load_database(resolve_repo_path("examples", "config", "database")))
print(int(sim.spawn_unit(ef_py.Side.Blue, "Ground", 0, 0, 0, 0, 0, 0, 0, 0, 0)))
PY
# False
# True
# 0
```

## D2 Movement Evidence Gate Preflight Result

Status: `preflight-only accepted`; evidence gates are defined, but they cannot
release a movement scenario until D1's native schema blocker is closed.

Available evidence hooks:

- `SimulationKernel::get_unit_position()` returns runtime position from
  `Transform`.
- `SimulationKernel::get_unit_velocity()` and `get_unit_heading()` expose
  movement vectors and heading when bound/available.
- `SimulationKernel::get_instrument_state()` exposes `ground_speed` and
  `ground_track` through `InstrumentState`.
- `SimulationKernel::get_agent_observation()` exposes position, velocity,
  heading, speed, and health in the current observation shell.
- Batch/facade routes can use `get_agent_observations_batch()` and
  `get_instrument_states_batch()`.

Minimum future G2 tests:

- load a native ground entity, not an `Aircraft` compatibility shell;
- assert the scenario declares `realism_gradient.grade = G2`;
- assert route intent maps from accepted ground tasking fields or waypoint
  fields into the runtime setup;
- step the runtime and compare initial/final position to prove movement state,
  not just task-order intent;
- assert ground speed and ground track are finite, bounded by ground-unit speed
  limits, and do not inherit aircraft cruise assumptions;
- assert flat/passable-only terrain scope and explicit deferral of terrain-aware
  degradation, sensing, fires, damage, observation export, and combat;
- include at least one no-move or unsupported-state failure case so a missing
  movement update cannot pass silently.

Release vote:

- `ground_platoon_flat_route_move_v1` remains held.
- `G6-D3` must not release route-move implementation until a native ground
  schema implementation package closes D1's blocker.
- The next credible package is a native ground platform schema implementation
  cluster, not a movement scenario cluster.

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
