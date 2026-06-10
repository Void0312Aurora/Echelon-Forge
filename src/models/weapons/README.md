# `src/models/weapons` Boundary

`models/weapons` holds default model implementations and helpers for weapon
effects, guidance, hit detection, and naval weapon-mount selection.

The maintained scope is still the shared weapon/effects model layer. Naval
mount helpers support the current naval pre-fire and bounded
engagement-evidence path, but this directory does not own a complete naval
mission runtime or any ground fires/damage runtime.

## Allowed

- Effects model.
- Guidance model.
- Naval weapon-mount selection helpers.
- Purely computational weapon behavior models.

## Forbidden

- ECS system registration.
- Combat component definition.
- Python binding or mission episode orchestration.
- Ground fires or ground damage model ownership before a maintained ground runtime exists.

## Migration Notes

System scheduling is placed in `systems/combat`, state is placed in `components/combat`, and model implementations are placed in this directory.

`detail/default_effects_*_detail.inc` files are private implementation
fragments for `default_effects_model.cpp`. Namespace-level fragments keep helper
linkage local while splitting `on_proximity_hit` into direct-hit,
spatial-projection, system-effect, domain routing, result-population, and
legacy/fallback submodules. They are not standalone APIs or additional model
entry points.

`detail/default_effects_domain_routing_detail.inc` is the generic router for
Air/Naval/Ground effects ownership. Air consequence handling lives in
`models/domains/air/default_effects_air_domain.h`; naval and ground routes are explicit
placeholder owner shells until their damage fidelity work has runtime owners.
