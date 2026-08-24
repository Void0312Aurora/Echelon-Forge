# `src/core/mission/episode/detail` Boundary

`mission/episode/detail` contains private implementation files for the remaining episode utilities. They are not stable APIs across layers.

## Allowed

- Reward-breakdown aggregation and stable JSON output.
- Small helpers used only by the public utility declared in `mission/episode`.

## Forbidden

- Being included directly by `interfaces/python`, `runtime/facade`, `gpu`, or `core/engine`.
- Defining new public episode contracts; public contracts belong in `mission/episode`.
- Implementing pure reward/objective/termination formulas; those belong in `mission/runtime`.

## Dependency Direction

This directory may depend on `mission/episode` and `mission/runtime`. Keep implementation-only helpers in an anonymous namespace so they cannot become accidental cross-layer APIs.
