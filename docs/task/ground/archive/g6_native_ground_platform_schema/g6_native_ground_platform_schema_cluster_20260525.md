# G6-E Native Ground Platform Schema Cluster

Status: `2026-05-26` accepted for `G6-E0`; `G6-E1` source-inventory/design
preflight is accepted; `G6-E2` native schema implementation is accepted;
`G6-E3` integration/release vote accepts native schema evidence only. No
route-move scenario is released.

## Decision

G6-E uses a schema-first, movement-deferred package boundary.

The next credible Ground/Army implementation step is not route movement. It is
the smallest native ground platform schema that can be loaded, spawned, and
identified through maintained shared runtime surfaces.

## Implementation Target

The target entity is a starter platoon-scale ground platform token:

- canonical source name candidate: `Ground_Platoon_MVP`;
- public type: `Ground`;
- service profile: `Army`;
- specialization/tasking profile: `ground`;
- first platform family: `dismounted_unit`;
- first doctrine family: `land_tactics`;
- mobility declaration: `ground_mobility_flat_deferred`;
- motion behavior: static or caller-provided initial velocity only, with no
  maintained route-following claim;
- sensing, fires, damage, suppression, logistics, and terrain behavior:
  deferred.

The starter platform may expose enough static mobility metadata to bound future
movement tests, but that metadata must not move the unit or claim `G2` route
movement by itself.

## E2 Implementation Evidence

Accepted implementation surface:

- `src/components/basic/common.h` adds `UnitType::Ground`.
- `src/content/unit_definition_loader.cpp` admits `type = "Ground"`.
- `src/models/core/default_unit_factory.h` emits
  `ground_mobility_flat_deferred` mobility evidence and `land_tactics` doctrine
  evidence for native ground definitions.
- `src/interfaces/python/bindings_core.cpp` exposes `ef_py.UnitType.Ground` and
  maps the UnitType overload to `Ground_Platoon_MVP`.
- `examples/config/database/ground/units/ground_platoon_mvp.json` adds the
  first auto-loaded native ground unit definition.
- `tests/runtime/ground/test_ground_native_platform_schema.py` proves
  load/spawn/identity/static-inspection/negative-schema behavior.

The implementation does not add a ground movement component, route-following
system, terrain model, sensing model, fires model, damage model, combat path,
facade expansion, or private `systems/ground/` runtime stack.

Direct probe:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python - <<'PY'
from python.testing.runtime import ensure_repo_imports, resolve_repo_path
ensure_repo_imports()
import ef_py
sim = ef_py.SimulationKernel()
print(hasattr(ef_py.UnitType, "Ground"))
print(sim.load_database(resolve_repo_path("examples", "config", "database")))
entity = int(sim.spawn_unit(ef_py.Side.Blue, "Ground_Platoon_MVP", 10, 20, 0, 45, 0, 0, 0, 0, 0))
print(entity > 0)
print(sim.get_unit_type(entity), int(ef_py.UnitType.Ground))
print(tuple(sim.get_unit_position(entity)))
print(tuple(sim.get_unit_velocity(entity)))
print(sim.get_unit_heading(entity))
print(list(sim.get_unit_health(entity)))
PY
# True
# True
# True
# 11 11
# (10.0, 20.0, 0.0)
# (0.0, 0.0, 0.0)
# 45.0
# [100.0, 100.0]
```

Focused validation:

```bash
cmake --build build-workshop --target ef_py -j2
# [100%] Built target ef_py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/ground/test_ground_native_platform_schema.py
# 5 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/ground/test_ground_native_platform_schema.py \
  tests/contracts/unit/ground \
  tests/architecture/ground/test_realism_gradient_guardrails.py \
  tests/runtime/ground/test_ground_mvp_scenario.py \
  tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py \
  tests/leader/test_tasking_profile_contracts.py
# 24 passed
```

## E3 Release Vote

Decision: accepted for native schema evidence only.

This closes the `G6-D1/D2` native-schema blocker that prevented a ground entity
from being loaded, spawned, and identified through maintained shared surfaces.
It does not close the `G2` movement gate.

Next authorized action:

- a later G6-D3/G6-F route-move release vote may be opened using this native
  schema evidence as an input.

Still not authorized:

- `ground_platoon_flat_route_move_v1`;
- route following, speed/acceleration updates, stuck/off-route checks, or
  terrain passability;
- terrain-aware movement, line-of-sight sensing, contact reports, fires,
  effects, suppression, damage, combat, or logistics behavior.

## E1 Source Inventory Result

Observed source facts:

- `src/components/basic/common.h::UnitType` is the public runtime identity used
  by `KeyEntity`.
- `src/content/unit_definition_loader.cpp::parse_unit_type()` is the current
  type-name admission point for auto-loaded database JSON.
- `load_unit_definitions_json()` recursively auto-loads only `.json` files, so
  the existing `ground_platoon_starter.seed` can remain a planning seed.
- `DefaultUnitFactory::build_platform_capability_bundle_template()` already
  builds capability-bundle evidence from `UnitDefinition` fields.
- `DefaultUnitFactory::spawn()` already materializes entities with `Transform`,
  `Velocity`, `Alliance`, `KeyEntity`, and `Health` for any admitted
  definition.
- `SimulationKernel::get_unit_type()` is already bound to Python, so E2 does
  not need a new identity getter.
- Current probe evidence remains negative:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python - <<'PY'
from python.testing.runtime import ensure_repo_imports, resolve_repo_path
ensure_repo_imports()
import ef_py
sim = ef_py.SimulationKernel()
print(hasattr(ef_py.UnitType, "Ground"))
print(sim.load_database(resolve_repo_path("examples", "config", "database")))
entity = int(sim.spawn_unit(ef_py.Side.Blue, "Ground", 0, 0, 0, 0, 0, 0, 0, 0, 0))
print(entity)
print(sim.get_unit_type(entity))
PY
# False
# True
# 0
# 0
```

## E1 Design Decision

Accepted path for E2:

- use `UnitType::Ground` as the public identity;
- parse `type = "Ground"` in `parse_unit_type()`;
- add one auto-loadable JSON named `Ground_Platoon_MVP`;
- keep the existing `.seed` file as planning/contract context;
- reuse `DefaultUnitFactory::spawn()` type-name materialization;
- add ground capability-bundle evidence in the existing mobility/doctrine
  capability families, without adding new runtime contract constants;
- use existing Python `get_unit_type()` for identity evidence;
- keep E2 limited to load/spawn/identity/static runtime inspection.

Rejected or deferred paths:

- `UnitType::GroundUnit`: too narrow and less consistent with existing public
  enum names.
- Maintained typed-platform/facade materialization: useful later, but not the
  smallest E2 path because type-name/default factory already owns runtime load
  and spawn evidence.
- New movement-specific component such as `GroundMobilityProfile`: deferred
  until route-move or speed-envelope tests require maintained fields.
- Using `Facility` or `C2Node`: remains rejected as a ground substitute.

## Minimum File Surface For E2

Likely implementation write surface:

- `src/components/basic/common.h`
  - add `UnitType::Ground`;
- `src/content/unit_definition_loader.cpp`
  - parse `type = "Ground"` and optionally read minimal ground metadata;
- `src/content/unit_definition.h`
  - add only optional static metadata if E2 needs it for evidence; avoid
    movement-specific maintained behavior fields;
- `src/models/core/default_unit_factory.h`
  - add load/materialization support, optional built-in fallback if needed,
    ground capability evidence, and spawn-plan admission;
- `src/interfaces/python/bindings_core.cpp`
  - expose `ef_py.UnitType.Ground` and default UnitType spawn mapping only if a
    default type-name is added;
- `examples/config/database/ground/units/ground_platoon_mvp.json`
  - add one auto-loadable native ground unit definition;
- `tests/runtime/ground/test_ground_native_platform_schema.py`
  - add load/spawn/identity/static inspection tests plus negative malformed
    schema coverage.

Possible supporting surfaces if the maintained typed platform setup path is
used:

- `src/runtime/contracts/platform_capability_contracts.h`;
- `src/runtime/contracts/world_batch_contracts.h`;
- `src/runtime/facade/runtime_facade.cpp`;
- `src/interfaces/python/bindings_runtime.cpp`.

These supporting surfaces are not released for E2 by the accepted E1 path. They
must stay untouched unless implementation discovers a hard blocker that forces
re-scoping.

## Required Evidence

The implementation package must provide:

- a load probe proving `sim.load_database("examples/config/database")` accepts
  `examples/config/database/ground/units/ground_platoon_mvp.json`;
- a spawn probe proving `spawn_unit(..., "Ground_Platoon_MVP", ...)`
  materializes a non-null entity;
- a Python identity assertion proving the entity is native ground and not an
  `Aircraft`, `Ship`, `Submarine`, `Facility`, or `C2Node` substitute;
- runtime inspection assertions for position, velocity, heading, instrument or
  observation state where currently maintained, and health;
- capability evidence that includes ground platform/mobility family labels
  without claiming movement behavior;
- a negative test proving unknown or malformed ground schema requests fail
  closed instead of silently falling back to another type.

Recommended focused validation commands:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/ground/test_ground_native_platform_schema.py \
  tests/contracts/unit/ground
```

The exact test file names may change during implementation, but the evidence
categories above must remain.

## Task Clusters

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `G6-E0 Native Schema Planning` | main-thread integration | current main thread | Record the minimum native ground platform schema package and release gate. | `docs/task/ground/g6_native_ground_platform_schema/**`, ground README/queue/progress/plan sync | runtime implementation, scenario files, route movement, terrain, sensing, fires, damage, combat | `git diff --check -- docs/task/ground`; focused ground guardrail tests | finite implementation clusters and acceptance gate recorded | depends on accepted G6-D1/D2 preflight | 1 documentation round | accepted |
| `G6-E1 Source Inventory And Design Preflight` | main-thread diagnostics | current main thread | Confirm selected identity path: public `UnitType` versus maintained typed-platform capability materialization. | read-only diagnostics plus this package/queue/progress sync | code edits, scenario release, movement implementation | source inventory plus proposed patch/test list | selects the smallest implementation path and names blocked alternatives | after G6-E0 | 1 diagnostics round | accepted |
| `G6-E2 Native Schema Implementation` | main-thread implementation | current main thread | Implement one runtime-loadable native ground platform schema and focused tests. | approved source/test/content files from E1 only | route movement, terrain, sensing, fires, damage, combat, broad facade growth | focused C++/Python build plus runtime ground tests | native entity loads, spawns, and is inspectable without substitute type fallback | after accepted E1 release | at most 2 implementation rounds | accepted |
| `G6-E3 Integration And Release Vote` | main-thread integration | current main thread | Decide whether native schema evidence is sufficient to unblock a later route-move implementation vote. | ground docs/queue/progress sync only unless a fix is explicitly released | route-move implementation | focused tests from E2 plus docs check | accepts native schema evidence; route movement remains held for later vote | after E2 | 1 integration round | accepted |

## Guardrails

- `G6-E` does not release `ground_platoon_flat_route_move_v1`.
- `Facility` and `C2Node` remain unacceptable substitutes for native ground
  movement evidence.
- A static native ground entity may close schema identity, but it does not close
  the G2 movement gate.
- Capability names may declare future ground mobility families only as schema
  evidence; movement behavior needs a later route-move package.
- Any implementation must reuse shared content, platform factory, runtime, and
  binding surfaces instead of adding a private ground runtime stack.

## E1 Answers

- Public identity: `UnitType::Ground`.
- Starter JSON: `type = "Ground"` and name `Ground_Platoon_MVP`.
- Movement-specific components: not required for E2.
- Python identity hook: existing `get_unit_type()` plus `ef_py.UnitType.Ground`.
- Content placement: add a `.json` beside the existing `.seed`; do not replace
  the `.seed` planning file.

## Exit State

After G6-E3, native schema evidence is accepted and may feed a later G6-D3/G6-F
route-move release vote. Route movement remains blocked until that later vote
explicitly accepts a bounded route-move implementation.
