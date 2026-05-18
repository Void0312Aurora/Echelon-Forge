# `python/` Layer Responsibilities

`python/` is not a miscellaneous scripts directory. It is the Python support layer above the C++ runtime. It owns scenario compilation and realization, training callbacks, RL runtime adaptation, world model support, and testing runtime helpers.

The main dependency flow is roughly:

```text
src/interfaces/python -> ef_py
  -> python/scenario/compiler + python/scenario/runtime
     + python/env_config + python/mission_obs_taxonomy
    -> gym_envs/
      -> python/rl/
        -> tools/ + tests/
```

## Allowed

- Python runtime support modules reused by training entry points.
- Scenario compilation, world layout realization, and mission observation dimension conventions.
- RL runtime, vec-env, policy algo, and tasking glue.
- Training callbacks, benchmark helpers, and contract runner support.
- Pure Python components related to world models and offline datasets.

## Forbidden

- Dropping one-off manual diagnostics scripts directly into the `python/` root.
- Re-implementing environment responsibilities already maintained by `gym_envs/` at the `python/` root.
- Adding new flat single-file entry points for legacy compatibility instead of placing code in an existing subdomain.
- Putting long-lived C++ binding logic here; that belongs in `src/interfaces/python/`.

## Subdirectory Conventions

- `scenario/`
  - Main implementation for packaged scenario compilation and runtime, maintained in the `compiler/` and `runtime/` subdomains.
- `rl/`
  - Main Python RL line, including runtime, policy_algo, tasking, planning, profile, and support.
- `training/`
  - Support for the main `train.py` entry point, including CLI, bootstrap, experiment directories, and runtime orchestration.
- `testing/`
  - Testing runtime support, plus the main contract runner implementation under `contracts/`.
- `world_model/`
  - World model support such as Dreamer, replay, features, and networks.
- `models/`
  - Python-side model components, currently mainly training helpers such as feature extractors.

## Current Entry Points for Reading

- [scenario/compiler/](scenario/compiler)
- [scenario/runtime/](scenario/runtime)
- [rl/__init__.py](rl/__init__.py)
- [testing/contracts/](testing/contracts)
- [testing/runtime.py](testing/runtime.py)
- [world_model/dreamer.py](world_model/dreamer.py)
- [models/transformer.py](models/transformer.py)

## Compatibility Shims

- [scenario_compiler.py](scenario_compiler.py)
  - Root-level compatibility shim that only re-exports `python/scenario/compiler/`.
- [scenario_runtime.py](scenario_runtime.py)
  - Root-level compatibility shim that only re-exports `python/scenario/runtime/`.
- [testing/scenario_contract_runner.py](testing/scenario_contract_runner.py)
  - Compatibility shim that only re-exports the contract execution entry point from `python/testing/contracts/`.

## Current File Locations

- Root
  - [artifact_paths.py](artifact_paths.py)
    - Artifact path resolution and contract/eval path normalization.
  - [env_config.py](env_config.py)
    - Entry point for resolving training configs into environment settings.
  - [mission_obs_taxonomy.py](mission_obs_taxonomy.py)
    - Mission observation dimensions, field indices, and mode enums.
  - [scenario_compiler.py](scenario_compiler.py)
    - Compatibility shim; the main implementation has moved down into `python/scenario/compiler/`.
  - [scenario_runtime.py](scenario_runtime.py)
    - Compatibility shim; the main implementation has moved down into `python/scenario/runtime/`.
  - [training_callbacks.py](training_callbacks.py)
    - SB3 training diagnostics, curriculum, and training-time statistics callbacks.
- `scenario/`
  - `compiler/`
    - Main implementation for scenario JSON compilation, prefab merging, and preprocessing of routes, objectives, and layouts.
  - `runtime/`
    - Main implementation for realizing compiled scenarios into kernel/world-batch state, randomization, and roster mapping.
- `rl/`
  - `control/`
    - Scripted takeoff, landing, and stable-flight controllers and wrappers.
  - `tasking/`
    - Leader/tasking bridge, air/naval adapters, and common-core profile glue.
  - `runtime/`
    - Single-world, world-batch, leader-window, cooperative runtime, and vec-env adapters.
  - `policy_algo/`
    - PPO adaptive KL, custom rollout buffers, policies, and HMoE routing.
  - `planning/`
    - Planning helpers such as coarse route propagation.
  - `profile/`
    - Default values and inference for `common/air/naval` profiles.
  - `support/`
    - Benchmarking, nonfinite probes, and SB3 vec-env compatibility support.
- `testing/`
  - `runtime.py`
    - Repo/build path injection and import configuration for tests.
  - `contracts/`
    - Main JSON contract runner implementation, organized into submodules such as `env_regression`, `loader_command_chain`, `route_generator`, and `scripted_bridge`.
  - `scenario_contract_runner.py`
    - Compatibility shim; the main implementation has moved to `python/testing/contracts/`.
- `training/`
  - `cli.py`
    - The argparse parameter table for the `train.py` entry point.
  - `bootstrap.py`
    - Scenario/config validation, resume directory conventions, locks, seeds, and torch runtime bootstrap.
- `world_model/`
  - `dreamer.py`, `networks.py`, `features.py`, `replay.py`, `utils.py`
    - World model training, networks, features, and dataset support.
- `models/`
  - `transformer.py`
    - Reusable Transformer feature extractor and observation preprocessing for training.

## Troubleshooting Guide

If you are looking into:

- "Why does this training config map to these observation/action/environment settings?"
  - Start with [env_config.py](env_config.py)
- "Why was this scenario compiled into this route/objective/roster?"
  - Start with `python/scenario/compiler/`
- "How does the batch runtime apply a compiled scenario to the kernel?"
  - Start with `python/scenario/runtime/`
- "Where does the leader/tasking/HMoE training logic live?"
  - Start with `python/rl/tasking/` and `python/rl/policy_algo/`
- "Why does `train.py` enter this run directory, auto-resume, or set torch threads this way?"
  - Start with `python/training/`
- "Where do the training logs, regressions, and termination stats come from?"
  - Start with [training_callbacks.py](training_callbacks.py)
- "Why can't the contract runner or eval resolve an artifact?"
  - Start with [artifact_paths.py](artifact_paths.py) and `python/testing/contracts/`

## Migration Notes

- `python/rl/` has already been consolidated by subdomain. New RL logic should go into the appropriate package instead of restoring a flat file layout.
- `python/scenario/compiler/` and `python/scenario/runtime/` are the current main implementation entry points. `scenario_compiler.py` and `scenario_runtime.py` remain only as compatibility shims for legacy import paths.
- `python/testing/contracts/` is the main contract runner implementation entry point. `python/testing/scenario_contract_runner.py` remains only as a compatibility shim.
- If `world_model/` or `testing/` grows further, prefer splitting them into additional subpackages inside their own directories instead of falling back to root-level compatibility files.
