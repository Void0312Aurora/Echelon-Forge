# `src/runtime/contracts` Boundary

`runtime/contracts` stores the stable DTOs shared between `runtime/facade` and lower-level runtime owners. Types here may be referenced by the facade, engine, Python bindings, and tests, but they must not own world state, ECS registries, or system scheduling logic.

The contract surface is multi-domain/common-first. `world_batch_contracts.h`
currently carries typed platform setup, terrain/wind/zones, maintained
mission-command and tasking batch contracts with shared, air, and naval slices.
`engagement_contracts.h` carries track/contact evidence, launch requests/events,
munition lifecycle, effects, damage, and diagnostics trace DTOs used by the N4
pre-fire/contact plus bounded engagement-evidence path. Ground support here is
setup/evidence-aware only; no full ground movement, sensing, fires, damage, or
runtime contract is maintained yet.

`simulation_composition_contract.h` and the generated
`composition/simulation_composition_manifest.v1.schema.json` define the
host-neutral composition value contract. They name versions, scopes, services,
provider/system contributions, backend requests, evidence policy, and stable
validation errors. They do not construct providers, own scope resources, parse
Cordis objects, or register Flecs systems. The executable schema source and
canonical fixtures live in
`tools/maintenance/simulation_composition_contract.py` and
`tests/architecture/composition/fixtures/`.

## Allowed

- Lightweight references such as `WorldEntityRef`.
- DTOs for batch setup, commands, tasking, and episode-step requests.
- Request/result types composed only of value types, component DTOs, and mission runtime DTOs.
- Engagement/tasking evidence DTOs that remain pure contracts and do not execute domain logic.
- Host-neutral composition manifests, stable service keys, and pure validation/result values.

## Forbidden

- `SimulationKernel`, `WorldBatchRuntime`, or other owner classes.
- Flecs system registration, step scheduling, or GPU helper implementations.
- Python/nanobind binding logic.
- Pulling in `core/engine/*` just for include convenience.
- Expanding ground-specific runtime semantics before a maintained ground owner and schema exist.
- Provider construction, lifecycle effects, service locator state, or composition-time Flecs registration.

## Generated detail layout

Generated X-macro lists under `detail/` are grouped by contract domain:
`damage`, `engagement`, `kill_chain`, `learning`, `platform`, `scenario`, and
`tasking`. Keep new generated lists in the matching contract directory and
update the corresponding declarative source in
`tools/maintenance/dto_schema/schemas/<domain>/`; the schema and output domains
need not have the same name. Do not add flat `.inc` files directly to `detail/`.

## Migration Notes

This directory is the likely starting point for a future `ef_contracts` target. New facade-facing types should be placed here first and then consumed by the facade or engine implementation. When adding domain-specific fields, prefer `common` plus explicit domain slices over widening shared contracts with air-, naval-, or ground-only semantics.
