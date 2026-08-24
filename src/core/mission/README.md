# `src/core/mission` Boundary

`core/mission` owns the task runtime needed by the training mainline: mission, objective, reward, termination, and execution episodes. It interprets tasking/command data and produces runtime products, but it does not define low-level components or provide Python bindings.

The current mission layer should be described as multi-domain aware rather than
air/flight-only. It is still most mature for air execution episodes; naval
`MissionCommand` fields are carried through bounded codec/state seams, while
tasking packet transport lives in the engine/runtime contract layers. Full
naval mission orchestration and full ground runtime behavior remain outside the
maintained mission scope.

## Allowed

- Mission runtime, objective runtime, reward runtime, and termination runtime.
- `ExecutionEpisodeState`, batch preparation, and reward-breakdown serialization.
- Pure C++ episode products for Python bindings, GPU helpers, or facade internals.
- Bounded storage and comparison of the `MissionCommand` compatibility shell in episode state.

## Forbidden

- ECS system tick logic.
- Implementations of physics integration, sensor scanning, or weapon guidance.
- Python/nanobind bindings.
- Training config parsing and UI/API adaptation.
- Full ground movement/sensing/fires/damage runtime or a native ground mission schema before that owner exists.

## Current Structure

```text
mission/
  runtime/
  episode/
    detail/
```

- `runtime/`: pure mission/runtime kernels and runtime products, including mission, objective, reward, termination, observation, step, frame, and episode runtime. This layer does not own stateful episode orchestration and does not interpret Python or facade contracts.
- `episode/`: episode state DTOs, batch preparation, and the public reward-breakdown utility.
- `episode/detail/`: private reward-breakdown implementation. External code should include the public header in `episode/`.

New pure reward/objective/termination computation belongs in `runtime/`; new episode-state or batch-prepare contracts belong in `episode/`. Stateful transition rules belong to the maintained Python orchestration rather than a new parallel C++ controller.

## Dependency Direction

This layer may consume `components/command`, `components/tasking`, the public API of `core/engine`, and mission-related DTOs. It should not depend on `runtime/facade` or `interfaces/python`.

`episode/` may depend on `runtime/`. `runtime/` should not depend on `episode/`. `episode/detail/` may depend on `episode/` and `runtime/`, but should not become a public cross-layer entry point.
