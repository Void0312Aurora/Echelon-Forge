# Echelon Forge

Echelon Forge is a simulation and reinforcement-learning workbench for
air-combat and flight-task research.

The repository combines:

- a C++ ECS simulation kernel built around `flecs`
- Python bindings exposed through `nanobind` as `ef_py`
- scenario compilation / runtime utilities
- Gymnasium-style training environments
- batch rollout and cooperative training infrastructure
- evaluation, diagnostics, and contract-style regression tooling

The project is still evolving, but the maintained mainline already supports:

- fixed-step simulation and deterministic reset seeds
- mission / command / reward / termination runtime
- takeoff, cruise, landing, and combined-task training lines
- cooperative execution experiments
- active diagnostics and evaluation tooling

## Repository Status

This repository is an active research/engineering codebase, not a polished
product release.

That means:

- active plans and forward notes live under `docs/`
- some training lines are frozen baselines, others are active experiments
- the CPU runtime remains the canonical world-step truth
- GPU helper paths exist, but are still treated conservatively

## Quick Start

Local validation is expected to run inside the repository virtual environment:

```bash
source .venv/bin/activate
```

The maintained workspace convention is:

- repository virtual environment: `.venv`
- repository env helper: `tools/maintenance/cmo_env.sh`
- build selection: prefer `CMO_BUILD_DIR`, otherwise auto-detect `build-workshop`, `build-gpu`, `build`, `build-facade-local`

Example:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_summary
cmo_python -m pytest -q tests/runtime/test_env_config.py
```

Configure and build the local extension:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
```

When running Python-side tests or training, prefer the local build products:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest -q \
  tests/architecture/test_runtime_facade_layering.py \
  tests/architecture/test_cmake_target_readiness.py \
  tests/runtime/test_runtime_facade.py \
  tests/world_batch/test_world_batch_runtime.py \
  tests/test_gpu_runtime_bindings.py
```

If you use a different build directory, replace `build-workshop` consistently in
both `PYTHONPATH` and `CMO_BUILD_DIR`.

## Project Layout

- [src/](src/README.md): C++ kernel, mission runtime, runtime facade, Python bindings, GPU helpers.
- [python/](python/README.md): RL runtime, training helpers, scenario compiler/runtime, diagnostics support.
- [gym_envs/](gym_envs/README.md): `UniversalEnv`, cooperative/leader environment support, scenario loader.
- [scenarios/](scenarios/README.md): maintained scenario definitions grouped by task domain.
- [examples/](examples/README.md): examples, fixtures, training configs, visualization entrypoints.
- [tests/](tests/README.md): pytest suites, contract specs, runners, and fixtures.
- [tools/](tools/README.md): evaluation, diagnostics, runners, maintenance scripts.
- [docs/](docs): manuals, plans, standards, forward notes, artifact indexes.

## Architecture Boundary

The maintained dependency direction is:

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content
```

Key rules:

- `components/` holds ECS components and DTO-like structures
- `systems/` holds per-tick mutation logic
- `models/` holds replaceable domain models
- `core/engine` owns `SimulationKernel` and batch runtime
- `core/mission` owns mission runtime and episode orchestration
- `runtime/facade` is the maintained C++ application contract
- `interfaces/python` should stay as bindings/adaptation only

See also:

- [src/README.md](src/README.md)
- [src/core/README.md](src/core/README.md)
- [docs/manual/src_layer_map.md](docs/manual/src_layer_map.md)
- [docs/plan/architecture/src_layered_refactor_freeze.zh.md](docs/plan/architecture/src_layered_refactor_freeze.zh.md)

## Scenarios and Training Configs

Maintained scenarios live in [scenarios/](scenarios/README.md), grouped into:

- `takeoff/`
- `stable_flight/`
- `cruise/`
- `landing/`
- `combined/`
- `templates/`
- `test/`

Training-config entrypoints:

- [examples/config/training/README.md](examples/config/training/README.md)
- [examples/config/training/active/README.md](examples/config/training/active/README.md)
- [examples/config/training/frozen/README.md](examples/config/training/frozen/README.md)

Frozen configs are baseline/provenance references.
Active configs are where current training work continues.

## Training

Example training entry:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name local_smoke \
  --output_base /tmp/cmo_smoke
```

Example policy evaluation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python tools/eval/eval_sb3.py \
  --mode single \
  --scenario scenarios/combined/takeoff_to_landing_continuous_eval_v1.json \
  --train_config examples/config/training/frozen/execution/p5_continuous_retrain_v1.json \
  --model path/to/model.zip \
  --episodes 8
```

## Diagnostics and Regression

Contract runner example:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Typical pytest groups:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest -q \
  tests/runtime \
  tests/world_batch \
  tests/architecture
```

Diagnostic and benchmark scripts are centered under
[tools/diagnostics](tools/diagnostics).

## Current Reference Documents

- [docs/manual/engine_capabilities.md](docs/manual/engine_capabilities.md)
- [docs/manual/physics_engine_inventory.md](docs/manual/physics_engine_inventory.md)
- [docs/manual/src_layer_map.md](docs/manual/src_layer_map.md)
- [docs/reference_artifacts.md](docs/reference_artifacts.md)

## Forward Work

Forward-looking notes live under [docs/forward](docs/forward/README.md).

That includes the newly added HMoE design note for the execution policy:

- [docs/forward/models/hierarchical_moe_execution_policy.md](docs/forward/models/hierarchical_moe_execution_policy.md)

## Working Conventions

- prefer `.venv` for repository-local validation
- prefer `tools/maintenance/cmo_env.sh` for maintained shell workflows
- prefer repo-relative scenario paths
- keep new training configs in explicit subdirectories
- do not treat GPU helpers as canonical world-step truth without a dedicated freeze
- add README files when introducing new architectural directories
