# `src/core/mission/episode` Boundary

`mission/episode` owns execution-episode state, batched input preparation, and controller orchestration. It transforms scenario/env state into `mission/runtime` inputs and applies runtime products back onto episode state.

## Allowed

- `ExecutionEpisodeState` import/export and evolution of its state fields.
- `StepEvaluationBatchConfig`, `StepEvaluationBatchEnvState`, and batch-prepare contracts.
- The prepare/evaluate/step coordination logic of `ExecutionEpisodeController`.

## Forbidden

- Direct implementation of reward/objective/termination formulas; those belong in `mission/runtime`.
- Python/nanobind bindings and facade adaptation.
- Exposing the controller's internal JSON codecs, transitions, and breakdown helpers as public APIs across layers.

## Subdirectories

- `detail/`: private helpers for the controller. External code generally should not include headers from here.

## Dependency Direction

This directory may depend on `mission/runtime`. It should not depend on `runtime/facade`, `interfaces/python`, or `gpu`.
