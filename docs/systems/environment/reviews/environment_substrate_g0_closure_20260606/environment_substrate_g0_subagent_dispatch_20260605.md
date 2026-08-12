# Environment Substrate G0 Subagent Dispatch

Status: `2026-06-05` read-only diagnostics dispatch record for
[README.md](README.md).

## Authority

Dispatch follows:

- [Subproject creation standard](../../../../engineering/automation/rules/subproject_creation_standard.md)
- [Subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.md)
- [Document authority map](../../../../engineering/automation/rules/document_authority_map.md)

The main thread owns integration and final scope decisions. Subagents are
diagnostics-only for this G0 pass.

## Dispatch Rules Applied

- Each diagnostics worker maps to one named environment-branch evidence slice.
- Workers are read-only and must not edit files.
- Workers must not create new conversation threads.
- Workers must not revert unrelated edits or edits made by other workers.
- No worker may claim terrain generation, weather simulation, hydrodynamics,
  movement, LOS, cover, fires, damage, combat, or runtime release.
- Main thread must integrate returned evidence before it becomes package
  evidence.

## Dispatch Packets

| Packet | Worker | Scope | Files / surfaces | Write set | Required return | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `TERR-DIAG-A` | `Averroes` | C++ terrain/environment foundation | `src/core/interfaces/environment_model.h`, `src/models/environment/default_environment_model.cpp`, `src/runtime/contracts/world_batch_contracts.h`, `src/core/engine/world_batch_setup_helper.h`, related README/tests | none, read-only | files inspected; existing mechanisms; limitations; architecture implications; held capabilities | pass |
| `TERR-DIAG-B` | `Descartes` | Python scenario/compiler/runtime terrain setup | `python/scenario/compiler/*`, `python/scenario/runtime/*`, `tests/scenario`, `tests/world_batch`, `tests/runtime/core` | none, read-only | files inspected; existing mechanisms; limitations; architecture implications; held capabilities | pass |
| `ENV-BRANCH-DIAG-A` | `Huygens` | Existing non-terrain environment branches | C++ and Python atmosphere/weather, wind, illumination/sun, maritime/ocean, hydrology, and dynamic-environment hints | none, read-only | files inspected; existing mechanisms; limitations; architecture implications; behavior risks; held capabilities | pass |
| `ENV-BRANCH-DIAG-B` | `Pascal` | Branch ontology and component gap review | G0 architecture docs, terrain-branch docs, source inventory, task clusters | none, read-only | branch/component/catalog gaps; rejected alternatives; integration notes; held capabilities | pass |
| `ENV-BRANCH-DIAG-C` | `Carson` | Projection and validator gate review | world-batch setup, scenario compiler/runtime setup, environment model, relevant tests | none, read-only | accepted/rejected compatibility projections; validator classes; evidence requirements; held gates | pass |

## Returned Diagnostics Summary

`TERR-DIAG-A` found that the C++ side is a query and compatibility-consumer
surface:

- `IEnvironmentModel` exposes atmosphere, elevation, LOS, weather attenuation,
  terrain cells, rectangular zones, wind, terrain profile, and maritime state.
- `DefaultEnvironmentModel` uses a fixed 20 km by 20 km 100 m raster base,
  SoftDirt/HardPacked checkerboard, `flat` versus legacy Gaussian elevation,
  and z-ordered rectangular overlays.
- `WorldTerrainAssignment` and `WorldZoneDefinition` carry only global terrain
  type and rectangle-like surface overrides.
- Existing consumers such as ground contact, visual cues, sensor LOS elevation,
  and GPU visual snapshots are query/display/compatibility consumers, not land
  terrain owners.

`TERR-DIAG-B` found that the Python side is setup plumbing:

- `terrain_type` is a global string with `flat` default and explicit legacy
  compatibility tagging.
- `environment.zones` compiles rectangle-like `surface` entries into six coarse
  surface codes.
- Runtime/batch setup forwards terrain, wind, zones, and spawns through
  maintained setup contracts.
- Scenario generation metadata already has deterministic seed, generator
  version, and evidence refs, but it is not a terrain generator contract.

Combined implications:

- Do not extend loose `environment.zones` or `WorldZoneDefinition` into the
  canonical terrain schema.
- Use a manifest-first terrain system with layer stack, tile scheme, object
  identity, component registry, catalogs, relationships, provenance, validators,
  projection profiles, and derived-product gates.
- Current C++ and Python surfaces should remain compatibility projection/query
  targets until separate runtime gates are accepted.
- Validators must catch unsupported or misspelled zone/projection semantics
  instead of silently degrading rich terrain data to default SoftDirt-style
  setup.

Held capabilities remain: terrain generator implementation, large-area terrain
generation, C++ terrain-runtime ownership for any domain, movement/passability,
LOS, cover/concealment, sensing/contact reports, fires, damage, suppression,
dynamic terrain state, and full village firefight behavior.

`ENV-BRANCH-DIAG-A` returned `pass` and found that current non-terrain support is
uneven:

- atmosphere/weather/sun are query hooks: simple atmosphere, no-op weather
  attenuation, and fixed sun direction do not prove weather or illumination
  branches;
- wind is a maintained global setup field with speed, direction-from, and shear,
  not wind volumes, gusts, or time evolution;
- maritime is a global runtime-layout override with sea state, wave heading, and
  wave period, and existing naval consumers may read it;
- hydrology and dynamic environment are not maintained substrate branches today.

`ENV-BRANCH-DIAG-B` returned `pass` and confirmed that the current ontology can
support cross-branch objects if G0 records extra contracts:

- explicit branch, component, layer, catalog, and projection registries;
- branch descriptors with version, ownership, static/dynamic status, geometry,
  temporal support, allowed components, validators, projection targets, and
  conflicts;
- branch membership roles instead of bare IDs;
- `properties{}` as metadata-only, never a behavior escape hatch;
- explicit rejected alternatives such as terrain-only root, domain-owned schema,
  feature-label schema roots, branch inheritance trees, and G0 parser/projection
  implementation.

`ENV-BRANCH-DIAG-C` returned `pass` and defined the fail-closed projection
matrix:

- terrain may project only to global terrain type or explicitly simplified
  rectangular surface zones;
- wind may project only to current global wind setup fields;
- maritime may project only to current global runtime-layout maritime fields;
- atmosphere/weather, illumination, and dynamic environment remain manifest-only
  in G0-J;
- hydrology may only use a lossy rectangular water/wet/soft surface projection
  when dropped hydrology attributes are recorded;
- every successful projection needs source object IDs, branch membership,
  component IDs, profile IDs, target setup surface, simplification method,
  dropped attributes, provenance, and a no-held-capability-release flag.

## Integration Target

Returned diagnostics should be integrated into:

- [environment_substrate_g0_source_inventory_20260605.md](environment_substrate_g0_source_inventory_20260605.md)
- [environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md)
- [environment_substrate_g0_terrain_system_architecture_20260605.md](environment_substrate_g0_terrain_system_architecture_20260605.md)
- [environment_substrate_g0_task_clusters_20260605.md](environment_substrate_g0_task_clusters_20260605.md)

## Worker Packet Template

```md
status: pass | partial | blocked | failed
touched files: none expected for diagnostics
files inspected:
commands/outcomes:
existing mechanism summary:
structural limitations:
architecture implications:
behavior risks:
explicit held capability claims:
integration notes:
```

## Acceptance Boundary

Diagnostics packets can support G0 architecture evidence only if they remain
read-only, cite current repo files, and preserve the held boundary for terrain
generation, weather simulation, hydrodynamics, movement, LOS, cover, fires,
damage, combat, and full environment/domain runtime.
