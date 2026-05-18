# `src/core/mission` Boundary

`core/mission` owns the task runtime needed by the training mainline: mission, objective, reward, termination, and execution episodes. It interprets tasking/command data and produces runtime products, but it does not define low-level components or provide Python bindings.

## Allowed

- Mission runtime, objective runtime, reward runtime, and termination runtime.
- `ExecutionEpisodeController` and its state import/export.
- Mission command codecs, episode transitions, and reward breakdown helpers.
- Pure C++ episode products for `WorldBatchRuntime` or `RuntimeFacade`.

## Forbidden

- ECS system tick logic.
- Implementations of physics integration, sensor scanning, or weapon guidance.
- Python/nanobind bindings.
- Training config parsing and UI/API adaptation.

## Current Structure

```text
mission/
  runtime/
  episode/
    detail/
```

- `runtime/`: pure mission/runtime kernels and runtime products, including mission, objective, reward, termination, observation, step, frame, and episode runtime. This layer does not own episode controller state and does not interpret Python or facade contracts.
- `episode/`: episode state, batch preparation, and `ExecutionEpisodeController`. This layer assembles scenario/env state into runtime inputs and applies runtime products back onto episode state.
- `episode/detail/`: internal helpers used only by the episode controller, including mission-command codecs, post-waypoint/landing transitions, and reward breakdown JSON. External code should not include headers from here directly unless it is extending the same detail-domain split during controller refactoring.

When adding new mission JSON fields, transition rules, or reward breakdown terms in the future, place them first in the corresponding helper under `episode/detail/` instead of stuffing them back into the controller main file. New pure reward/objective/termination computation should live in `runtime/`; new episode state import/export or batch-prepare contracts should live in `episode/`.

## Dependency Direction

This layer may consume `components/command`, `components/tasking`, the public API of `core/engine`, and mission-related DTOs. It should not depend on `runtime/facade` or `interfaces/python`.

`episode/` may depend on `runtime/`. `runtime/` should not depend on `episode/`. `episode/detail/` may depend on `episode/` and `runtime/`, but should not become a public cross-layer entry point.
