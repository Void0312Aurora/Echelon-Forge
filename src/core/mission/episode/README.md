# `src/core/mission/episode` Boundary

`mission/episode` owns execution-episode state DTOs, batched input preparation, and reward-breakdown serialization. Stateful step orchestration remains in the maintained Python mainline; this directory does not own a second episode controller.

## Allowed

- `ExecutionEpisodeState` import/export and evolution of its state fields.
- `StepEvaluationBatchConfig`, `StepEvaluationBatchEnvState`, and batch-prepare contracts.
- Stable reward-breakdown serialization for `ExecutionEpisodeRuntimeProducts`.

## Forbidden

- Direct implementation of reward/objective/termination formulas; those belong in `mission/runtime`.
- Python/nanobind bindings and facade adaptation.
- A parallel stateful episode stepping owner or mission-command transition codec.
- Exposing breakdown implementation helpers as public APIs across layers.

## Subdirectories

- `detail/`: private reward-breakdown implementation. External code should include the public episode header instead.

## Dependency Direction

This directory may depend on `mission/runtime`. It should not depend on `runtime/facade`, `interfaces/python`, or `gpu`.
