# `src/core/mission/episode/detail` Boundary

`mission/episode/detail` contains the internal business helpers for `ExecutionEpisodeController`. Headers here exist to split implementation files and support reuse within a single domain; they are not stable APIs across layers.

## Allowed

- Mission-command JSON round-tripping and route waypoint materialization.
- Post-waypoint transitions, landing transitions, and controller pre-step behavior updates.
- Reward breakdown aggregation and stable JSON output.

## Forbidden

- Being included directly by `interfaces/python`, `runtime/facade`, `gpu`, or `core/engine`.
- Defining new public episode contracts; public contracts belong in `mission/episode`.
- Implementing pure reward/objective/termination formulas; those belong in `mission/runtime`.

## Dependency Direction

This directory may depend on `mission/episode` and `mission/runtime`. New helpers should stay under the `episode_controller_detail` namespace so they are not mistaken for public APIs.
