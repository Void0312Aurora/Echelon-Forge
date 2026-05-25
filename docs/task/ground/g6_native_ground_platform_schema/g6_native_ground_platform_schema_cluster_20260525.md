# G6-E Native Ground Platform Schema Cluster

Status: `2026-05-25` opened for `G6-E0`; implementation remains held until this
planning package is accepted. No route-move scenario is released.

## Decision

G6-E uses a schema-first, movement-deferred package boundary.

The next credible Ground/Army implementation step is not route movement. It is
the smallest native ground platform schema that can be loaded, spawned, and
identified through maintained shared runtime surfaces.

## Implementation Target

The target entity is a starter platoon-scale ground platform token:

- canonical source name candidate: `Ground_Platoon_MVP`;
- public type candidate: `Ground` or `GroundUnit`, pending implementation
  review;
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

## Minimum File Surface Candidate

Likely implementation write surface:

- `src/components/basic/common.h`
  - add a public native ground unit type only if selected as the maintained
    identity path;
- `src/content/unit_definition_loader.cpp`
  - parse the selected ground unit type and the minimal ground platform schema;
- `src/content/unit_definition.h`
  - add only the minimum structured fields needed to represent the native
    ground platform identity and static mobility envelope;
- `src/models/core/default_unit_factory.h`
  - add default ground definition or load/materialization support, capability
    bundle evidence, and spawn-plan admission;
- `src/interfaces/python/bindings_core.cpp`
  - expose enough identity for Python tests to assert native ground status;
- `examples/config/database/ground/units/*.json`
  - add one auto-loadable native ground unit definition;
- focused tests under `tests/runtime/ground/`, `tests/contracts/unit/ground/`,
  or the nearest existing platform-spawn test location.

Possible supporting surfaces if the maintained typed platform setup path is
used:

- `src/runtime/contracts/platform_capability_contracts.h`;
- `src/runtime/contracts/world_batch_contracts.h`;
- `src/runtime/facade/runtime_facade.cpp`;
- `src/interfaces/python/bindings_runtime.cpp`.

These supporting surfaces are not released by `G6-E0`; they must be justified
by the implementation review before editing.

## Required Evidence

The implementation package must provide:

- a load probe proving `sim.load_database("examples/config/database")` accepts
  the native ground JSON;
- a spawn probe proving `spawn_unit(..., selected_ground_type_name, ...)`
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
| `G6-E0 Native Schema Planning` | main-thread integration | current main thread | Record the minimum native ground platform schema package and release gate. | `docs/task/ground/g6_native_ground_platform_schema/**`, ground README/queue/progress/plan sync | runtime implementation, scenario files, route movement, terrain, sensing, fires, damage, combat | `git diff --check -- docs/task/ground`; focused ground guardrail tests | finite implementation clusters and acceptance gate recorded | depends on accepted G6-D1/D2 preflight | 1 documentation round | open |
| `G6-E1 Source Inventory And Design Preflight` | explorer or main-thread diagnostics | `gpt-5.4`, high | Confirm selected identity path: public `UnitType` versus maintained typed-platform capability materialization. | read-only diagnostics first; docs update only if released | code edits, scenario release, movement implementation | source inventory plus proposed patch/test list | selects the smallest implementation path and names blocked alternatives | after G6-E0 | 1 diagnostics round | planned |
| `G6-E2 Native Schema Implementation` | worker | `gpt-5.4`, high | Implement one runtime-loadable native ground platform schema and focused tests. | approved source/test/content files from E1 only | route movement, terrain, sensing, fires, damage, combat, broad facade growth | focused C++/Python build plus runtime ground tests | native entity loads, spawns, and is inspectable without substitute type fallback | after accepted E1 release | at most 2 implementation rounds | held |
| `G6-E3 Integration And Release Vote` | main-thread integration | current main thread | Decide whether native schema evidence is sufficient to unblock a later route-move implementation vote. | ground docs/queue/progress sync only unless a fix is explicitly released | route-move implementation | focused tests from E2 plus docs check | either accepts native schema evidence or records residual blockers | after E2 | 1 integration round | held |

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

## Open Questions For E1

- Should public identity be `UnitType::Ground` or `UnitType::GroundUnit`?
- Should the starter JSON use `type = "Ground"` or a more explicit platform
  family such as `type = "GroundUnit"` plus `platform_family`?
- Can minimal ground identity be represented without adding movement-specific
  components, or is a small static `GroundMobilityProfile` structure required
  for future speed-envelope assertions?
- Which existing runtime hook should Python use for entity identity: `UnitType`,
  `KeyEntity`, capability evidence, or a new narrow getter?
- Should the first auto-loadable JSON replace or sit beside the existing
  `.seed` planning file?

## Exit State

After G6-E0, the queue should point to `G6-E1` as the next decision step. Route
movement remains blocked until E2/E3 close native schema evidence and a later
G6-D3/G6-F release vote explicitly accepts route-move implementation.
