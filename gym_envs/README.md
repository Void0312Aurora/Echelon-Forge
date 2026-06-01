# `gym_envs/` Layer Responsibilities

`gym_envs/` is the training environment wrapper layer. It turns the kernel/runtime exposed by `ef_py`, the scenario runtime data from `python/scenario/compiler/` and `python/scenario/runtime/`, and training-side observation/action/reward logic into Gymnasium-style interfaces.

The main dependency flow is roughly:

```text
ef_py + python/scenario/compiler + python/scenario/runtime
  -> gym_envs/scenario_loader
    -> gym_envs/universal_env_parts
    -> gym_envs/universal_env.py
    -> gym_envs/leader_env.py
      -> python/rl/runtime + tools/eval + tests
```

## Allowed

- Gymnasium environment wrappers and reset/step/render organization.
- Python-side glue for scenario loading, reward, termination, and shaping.
- Bridging between the leader decision layer and the execution layer.
- Lightweight runtime adaptation around the `ef_py` kernel and observation assembly.

## Domain Posture

- The maintained environment path is still strongest for air/execution and cooperative/common training.
- Maintained production training reaches the runtime through `python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv` for execution and `python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv` for cooperative execution.
- `UniversalEnv` remains a stable import path for single-env compatibility, evaluation, and diagnostics, but its raw `ef_py.SimulationKernel` route is quarantined and requires `runtime_compatibility_enabled=True`.
- Naval hooks exist where explicitly listed, including station actions, screen behavior, scoped reward surfaces, and N4 contact-evidence plumbing through the runtime path.
- Ground-domain movement, sensing, terrain, fires, damage, and full runtime behavior are not implemented here. References to takeoff ground roll or runway geometry are air/execution runway-phase logic, not ground-domain support.

## Forbidden

- Re-implementing C++ kernel truth logic inside env files.
- Putting generic training algorithm logic directly into `gym_envs/`; that belongs in `python/rl/`.
- Adding more isomorphic env scripts for a single experiment instead of reusing the existing loader/runtime subdomains.
- Further growing single-file monster modules; prefer the existing split subpackages.

## Subdirectory Conventions

- [universal_env.py](universal_env.py)
  - Stable single-env import path for compatibility, evaluation, and diagnostics. It is not the default production training backend unless the raw-kernel compatibility flag is explicitly enabled.
- [universal_env_parts/](universal_env_parts)
  - Main implementation subdomain for `UniversalEnv`, maintaining action, observation, space, and step-info assembly logic.
- [leader_env.py](leader_env.py)
  - Environment for the leader decision layer, driving the underlying execution backend.
- `scenario_loader/`
  - Scenario loading plus mission-state, route, reward, shaping, and transition glue.
- `leader_env_parts/`
  - Split subdomain and shared services for `leader_env.py`.

## Current Entry Points for Reading

- [universal_env.py](universal_env.py)
- [universal_env_parts/__init__.py](universal_env_parts/__init__.py)
- [leader_env.py](leader_env.py)
- [scenario_loader/__init__.py](scenario_loader/__init__.py)
- [leader_env_parts/__init__.py](leader_env_parts/__init__.py)

## Current File Locations

- Root
  - [universal_env.py](universal_env.py)
    - Stable single-env compatibility/debug entry point. The main action/observation/space/info helpers have moved into `universal_env_parts/`; maintained execution training should normally use the world-batch runtime adapter.
  - [leader_env.py](leader_env.py)
    - Leader training environment, execution backend integration, and decision-interval control.
- `universal_env_parts/`
  - [actions.py](universal_env_parts/actions.py)
    - Pilot action construction, action normalization, and basic numeric transforms.
  - [naval_actions.py](universal_env_parts/naval_actions.py)
    - Scoped naval station-action adaptation for `naval_station3`.
  - [observations.py](universal_env_parts/observations.py)
    - General observation assembly and visual downsampling helpers.
  - [spaces.py](universal_env_parts/spaces.py)
    - Action/observation space definitions and mission observation dimension conventions.
  - [info.py](universal_env_parts/info.py)
    - Assembly of step info and terminal-only info.
- `scenario_loader/`
  - [core.py](scenario_loader/core.py)
    - `ScenarioLoader` owner and cross-subdomain orchestration.
  - [common.py](scenario_loader/common.py)
    - Shared constants, JSON handling, mode normalization, and common helpers.
  - [loading.py](scenario_loader/loading.py)
    - Scenario loading plus initialization of compiled scenario/runtime state.
  - [mission_observation.py](scenario_loader/mission_observation.py)
    - Mission observation assembly and encoding.
  - [route_generation.py](scenario_loader/route_generation.py)
    - Route generation and derived helpers.
  - [runtime_state.py](scenario_loader/runtime_state.py)
    - Loader/runtime-state structures and their connection to the current world state.
  - [step_evaluation.py](scenario_loader/step_evaluation.py)
    - Step-level termination, success, and reward decomposition helpers.
  - `behavior_runtime/`
    - Command chains, post-waypoint transitions, and scoped naval screen station hold.
  - `execution_runtime/`
    - Main step path, shadow state, and shaping path.
  - `navigation_runtime/`
    - Guidance and waypoint rewards.
  - `preparation_runtime/`
    - Mission, task-order, and waypoint preparation plus randomization.
  - `reward_runtime/`
    - Shaping inputs, objectives, safety constraints, compiled reward runtime, and scoped naval reward surfaces.
  - `spatial_runtime/`
    - Geometry, world transforms, and spatial helpers.
- `leader_env_parts/`
  - [common.py](leader_env_parts/common.py)
    - Shared helpers for JSON, angle handling, args stubs, and similar utilities.
  - [contracts.py](leader_env_parts/contracts.py)
    - Fields and clone helpers for leader intent, pilot report, and task order.
  - [bridges.py](leader_env_parts/bridges.py)
    - Leader command bridge.
  - [runtime_services.py](leader_env_parts/runtime_services.py)
    - Aggregation of leader runtime services.
  - [scripted_exec.py](leader_env_parts/scripted_exec.py)
    - Scripted executive controller.
  - [policy.py](leader_env_parts/policy.py)
    - Loading and adapting frozen execution policies.
  - `decision_runtime/`
    - Command interpretation, action decoding, observation building, and terminal context.
  - `execution_runtime/`
    - Construction of execution env/policy/runtime and state synchronization.

## Troubleshooting Guide

If you are looking into:

- "Why is the mission/waypoint state wrong after env reset?"
  - Start with `scenario_loader/loading.py` and `preparation_runtime/`
- "Why did a step go down this shaping/reward/termination branch?"
  - Start with `execution_runtime/`, `reward_runtime/`, and `step_evaluation.py`
- "Why is the mission observation layout or field set inconsistent?"
  - Start with `mission_observation.py` and `universal_env_parts/observations.py`
- "Why are action/space/info structured this way?"
  - Start with `universal_env_parts/`
- "Why was the leader policy output interpreted as this command?"
  - Start with `leader_env_parts/decision_runtime/`
- "Why does the leader environment use the frozen/scripted execution backend?"
  - Start with `leader_env_parts/execution_runtime/` and [leader_env.py](leader_env.py)
- "Why does direct `UniversalEnv(...)` construction fail?"
  - Check whether the caller is intentionally using the quarantined raw-kernel compatibility path and passes `runtime_compatibility_enabled=True`; otherwise prefer the world-batch runtime adapters.

## Migration Notes

- `scenario_loader/` has already been split by runtime subdomain. New loader logic should go into the corresponding package instead of expanding `core.py` into a grab bag again.
- `gym_envs/` should use the packaged scenario entry points under `python/scenario/compiler/` and `python/scenario/runtime/`.
- `python/scenario/diagnostics/` is diagnostics-only and must not become an environment default path.
- `universal_env.py` remains a stable single-env compatibility entry point, but maintained training should keep converging on runtime-facade/world-batch adapters.
- `leader_env.py` remains the stable entry point, but its implementation should continue to move down into `leader_env_parts/`.
- If the future design keeps only package entry points instead of root-level single-file env modules, make sure the import paths in `tools/`, `tests/`, and training entry points are migrated together first.
