# Echelon Forge

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Echelon Forge is a multi-domain simulation and reinforcement-learning
workbench for air, naval, ground-tasking, cooperative command, and flight-task
research.

The repository combines:

- a C++ ECS simulation kernel built around `flecs`
- Python bindings exposed through `nanobind` as `ef_py`
- scenario compilation / runtime utilities
- Gymnasium-style training environments
- batch rollout and cooperative training infrastructure
- multi-domain scenario, content, and profile layers for air, naval, ground,
  and combined/cooperative tasks
- evaluation, diagnostics, and contract-style regression tooling

The project is still evolving, but the maintained mainline already supports:

- fixed-step simulation and deterministic reset seeds
- mission / command / reward / termination runtime
- takeoff, cruise, landing, and combined-task training lines
- cooperative execution experiments
- naval pre-fire tasking/contact/reporting fixtures
- ground tasking smoke fixtures and native platform-schema evidence
- active diagnostics and evaluation tooling

## Repository Status

This repository is an active research/engineering codebase, not a polished
product release.

That means:

- active plans and forward notes live under `docs/`
- some training lines are frozen baselines, others are active experiments
- the CPU runtime remains the canonical world-step truth
- GPU helper paths exist, but are still treated conservatively
- community contribution is currently issue-first and owner-scoped; see
  [CONTRIBUTING.md](CONTRIBUTING.md)

## Domain Maturity Snapshot

The repository is multi-domain, but the domains are not equally mature. Treat
the table below as an entry-map, not as a release promise.

| Area | Current status | Primary entrypoints |
| --- | --- | --- |
| Air / execution | Most mature runtime and training line; current best baseline for correctness hardening. | `scenarios/takeoff/`, `scenarios/cruise/`, `scenarios/landing/`, `examples/config/training/frozen/` |
| Cooperative / combined | Active integration line for multi-agent, leader/execution, and world-batch behavior. | `scenarios/combined/`, `python/rl/runtime/cooperative_world_batch_vec_env.py`, `gym_envs/leader_env.py` |
| Naval | Active domain with maintained N4-style pre-fire tasking, contact/reporting, screen/station, and evaluation gates. Weapon/damage outcome authority is still future work. | `scenarios/naval/`, `docs/task/naval/`, `docs/standards/naval/` |
| Ground | Early tasking/runtime bootstrap. Current fixtures validate shared command/status semantics and native platform-schema evidence, not full ground movement, sensing, fires, or damage. | `scenarios/ground/`, `docs/task/ground/`, `docs/standards/ground/` |
| Air combat / A2 | Focused combat and high-fidelity damage-model workline with retained evidence gates. It is one domain line, not the whole project identity. | `scenarios/air_combat/`, `docs/task/air_combat/` |
| Visualization / game | Exploratory operator and frontend surfaces backed by simulation runtime truth where maintained. | `examples/viz/`, `docs/task/viz/`, `docs/task/game/` |
| Model / world model | Planning and experimental policy/model work, including temporal HMoE and world-model utilities. | `docs/task/model/`, `docs/forward/models/`, `world_model_train.py` |

## Naming And Package Identity

The repository currently carries three related names. Use them deliberately:

- `Echelon Forge` is the human-facing project and repository name.
- `EchelonForge` is the CMake `project(...)` identifier and should remain
  stable unless a dedicated build-system migration is planned.
- `cmo` is the legacy Python distribution/install identifier in
  `pyproject.toml`, kept for compatibility with editable installs, local helper
  scripts, cached build artifacts, and downstream automation.

Do not treat `cmo` as a separate product name, and do not rename package ids,
CMake ids, helper names, or script paths opportunistically. A full naming
migration should be handled as its own scoped change with compatibility notes
and artifact/cache cleanup guidance.

## Quick Start

Local validation is expected to run inside the repository virtual environment:

```bash
source .venv/bin/activate
```

The maintained workspace convention is:

- repository virtual environment: `.venv`
- Python metadata and dependency groups: `pyproject.toml`
- Linux/macOS env helper: `tools/maintenance/cmo_env.sh`
- Windows/PowerShell env helper: `tools/maintenance/cmo_env.ps1`
- Linux/macOS build selection: prefer `CMO_BUILD_DIR`, otherwise auto-detect `build-workshop`, `build-gpu`, `build`, `build-facade-local`
- Windows build selection: prefer `CMO_BUILD_DIR`, otherwise auto-detect `build-local-win`, `build-workshop`, `build-gpu`, `build`, `build-facade-local`

Linux/macOS example:

```bash
python -m pip install pytest numpy
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_summary
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
```

Windows/PowerShell example:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest numpy
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\core\test_env_config.py
```

The current minimum smoke set used for repository validation is:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py ef_test -j4
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
cmo_python tools/runners/run_scenario_contract.py --suite tests/smoke/ci_contract_suite.json
```

On Windows, use the PowerShell helper and a Windows build directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py ef_test -j2
ctest --test-dir build-local-win -R ef_test_all --output-on-failure
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_scenario_contract.py --suite tests\smoke\ci_contract_suite.json
```

The Windows path above is scoped to the current local development workflow:
smoke tests and focused regressions. It does not claim that Windows cannot run
RL training; training workflows should be enabled deliberately when the local
dependencies, runtime artifacts, and run-output policy are ready.

Optional dependency groups are declared in `pyproject.toml`:

- `.[test]` declares the lightweight smoke/regression dependency set.
- `.[rl]` adds Gymnasium, Stable-Baselines3, and PyTorch for environment/runtime imports.
- `.[train]` adds the training stack plus TensorBoard.
- `.[world-model]` covers the world-model utilities.
- `.[dev]` is a convenience superset for local development, not a locked release environment.

Note: the maintained smoke workflow currently installs the small dependency set
directly and then uses `cmo_env.sh` / `cmo_env.ps1` to point Python at the
locally built extension. Because this is a scikit-build project,
`pip install -e ".[test]"` may attempt an editable package build; use it only
when you intentionally want to exercise package installation rather than the
fast local build loop.

No lockfile is checked in yet. Treat the optional dependency groups as minimum
capability declarations for smoke/runtime/training/world-model workflows, not as
reproducible experiment locks. Training result reproduction should record the
resolved package set with the run artifact until a dedicated lockfile policy is
introduced.

Configure and build the local extension:

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
```

When running Python-side tests or training on Linux/macOS, prefer the unified
repository helper:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_validate_rl  # Only needed before RL-capable runtime tests.
cmo_python -m pytest -q \
  tests/architecture/runtime_facade/test_layering.py \
  tests/architecture/build/test_cmake_target_readiness.py \
  tests/runtime/facade/test_runtime_facade.py \
  tests/world_batch/test_world_batch_runtime.py \
  tests/test_gpu_runtime_bindings.py
```

If you use a different build directory, export `CMO_BUILD_DIR=/path/to/build`
before sourcing `tools/maintenance/cmo_env.sh`, or set `$env:CMO_BUILD_DIR` before
calling `tools\maintenance\cmo_env.ps1` on Windows.

## Project Layout

- [src/](src/README.md): C++ kernel, mission runtime, runtime facade, Python bindings, GPU helpers.
- [python/](python/README.md): RL runtime, training helpers, scenario compiler/runtime, diagnostics support.
- [gym_envs/](gym_envs/README.md): `UniversalEnv`, cooperative/leader environment support, scenario loader.
- [scenarios/](scenarios/README.md): maintained scenario definitions grouped by task domain.
- [examples/](examples/README.md): config inputs, lightweight fixtures, visualization assets, and example-only surfaces.
- [tests/](tests/README.md): pytest suites, contract specs, runners, and fixtures.
- [tools/](tools/README.md): evaluation, diagnostics, runners, maintenance scripts.
- [scripts/](scripts/README.md): retained operator-facing wrappers and compatibility workflow shells.
- [docs/README.md](docs/README.md): manuals, plans, standards, forward notes, and artifact indexes.

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
- [docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md](docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md)

## Scenarios and Training Configs

Maintained scenarios live in [scenarios/](scenarios/README.md), grouped into:

- `takeoff/`
- `stable_flight/`
- `cruise/`
- `air_combat/`
- `naval/`
- `ground/`
- `landing/`
- `combined/`
- `templates/`
- `test/`

Training-config entrypoints:

- [examples/config/training/README.md](examples/config/training/README.md)
- [examples/config/training/active/README.md](examples/config/training/active/README.md)
- [examples/config/training/frozen/README.md](examples/config/training/frozen/README.md)

Other maintained config/content inputs live under:

- `examples/config/database/`
- `examples/config/diagnostics/`
- `examples/config/prefabs/`

Frozen configs are baseline/provenance references.
Active configs are where current training work continues.

Repository retention policy at a glance:

- `scenarios/` is versioned and treated as maintained repo input.
- `examples/config/` is versioned and keeps maintained plus frozen config entrypoints.
- `experiments/`, `datasets/`, and `output/` are runtime or artifact workspaces and remain ignored by default.
- Large run outputs should be preserved through reports, archived manifests, or retained diagnostics under documented artifact paths rather than by checking whole experiment directories into the main repo.

## Training

Current root/operator entrypoints:

- `train.py`
  - Main execution-layer, cooperative, and leader-layer training entrypoint.
- `world_model_train.py`
  - World-model training entrypoint; still a large root script and not yet
    fully split like `train.py`.
- `evaluate.py`
  - Historical root evaluator kept as a compatibility/operator surface.
- `tools/eval/*.py`
  - Maintained evaluation CLIs.
- `tools/runners/*.py`
  - Maintained contract and grouped regression runners.
- `scripts/README.md`
  - Small retained wrapper surface for workflows still worth keeping as shells.

Implementation for those entrypoints mostly lives in [python/README.md](python/README.md),
[gym_envs/README.md](gym_envs/README.md), and the C++ runtime/binding layers
under [src/README.md](src/README.md).

Example training entry:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name local_smoke \
  --output_base /tmp/cmo_smoke
```

Example policy evaluation:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/eval/eval_sb3.py \
  --mode single \
  --scenario scenarios/combined/takeoff_to_landing_continuous_eval_v1.json \
  --train_config examples/config/training/frozen/execution/p5_continuous_retrain_v1.json \
  --model path/to/model.zip \
  --episodes 8
```

## Diagnostics and Regression

Contract runner example:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Typical pytest groups:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
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

## License

Project code and maintained documentation are licensed under the
[Apache License 2.0](LICENSE).

Third-party assets and bundled third-party files keep their own licenses. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the current local notice
inventory.

## Working Conventions

- prefer `.venv` for repository-local validation
- prefer `tools/maintenance/cmo_env.sh` for maintained Linux/macOS shell workflows
- prefer `tools/maintenance/cmo_env.ps1` for maintained Windows/PowerShell workflows
- prefer repo-relative scenario paths
- keep new training configs in explicit subdirectories
- do not treat GPU helpers as canonical world-step truth without a dedicated freeze
- add README files when introducing new architectural directories
