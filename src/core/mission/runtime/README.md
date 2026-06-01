# `src/core/mission/runtime` Boundary

`mission/runtime` hosts the pure computation entry points for mission, objective, reward, termination, and execution runtime. It produces runtime products that are reused by the episode controller, GPU helpers, Python bindings, and the underlying facade implementation.

The mature execution runtime remains air-oriented, but the boundary should be
described as domain-aware rather than flight-only: it consumes component DTOs
and mission inputs prepared by higher layers, while naval tasking/evidence
surfaces and early ground-aware setup stay outside the pure runtime owner. This
directory must not claim ownership of full naval or ground runtime semantics.

## Allowed

- Mission observation, step, frame, and episode runtime inputs/products.
- Deterministic evaluation of objective, reward, and termination.
- Pure C++ computation that depends only on component DTOs, geometry runtime, and local numerical helpers.
- Domain-neutral runtime products that can be reused by facade/binding layers without importing those layers.

## Forbidden

- `ExecutionEpisodeController` state import/export.
- Mission-command JSON round-tripping, route transitions, and reward breakdown JSON.
- Python/nanobind bindings and facade request/result adaptation.
- Ground movement, sensing, terrain, fires, damage, or complete land-domain runtime.

## Dependency Direction

This directory may be included by `mission/episode`, the underlying implementation of `runtime/facade`, `interfaces/python` bindings, and GPU helpers. It should not include `mission/episode` or `runtime/facade`.
