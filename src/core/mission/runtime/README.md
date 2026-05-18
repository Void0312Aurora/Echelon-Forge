# `src/core/mission/runtime` Boundary

`mission/runtime` hosts the pure computation entry points for mission, objective, reward, termination, and execution runtime. It produces runtime products that are reused by the episode controller, GPU helpers, Python bindings, and the underlying facade implementation.

## Allowed

- Mission observation, step, frame, and episode runtime inputs/products.
- Deterministic evaluation of objective, reward, and termination.
- Pure C++ computation that depends only on component DTOs, geometry runtime, and local numerical helpers.

## Forbidden

- `ExecutionEpisodeController` state import/export.
- Mission-command JSON round-tripping, route transitions, and reward breakdown JSON.
- Python/nanobind bindings and facade request/result adaptation.

## Dependency Direction

This directory may be included by `mission/episode`, the underlying implementation of `runtime/facade`, `interfaces/python` bindings, and GPU helpers. It should not include `mission/episode` or `runtime/facade`.
