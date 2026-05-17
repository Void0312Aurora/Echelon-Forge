# Tests README

`tests/` is being consolidated around a small set of reusable runners plus JSON contracts.

## Goals

- Reduce one-off Python regression scripts.
- Keep scenario/test intent explicit in data instead of re-encoding bootstrap logic in every file.
- Make it easier to batch-run related regressions from CI or local shells.

## Current Structure

- `runtime/`
  - Runtime-contract tests for mission, execution-step, and loader parity.
- `eval/`
  - Maintained CLI-level evaluation regression tests.
- `training/`
  - Train-entry and training-callback regression tests.
- `hmoe/`
  - HMoE routing, policy, bootstrap, and control-config regression tests.
- `world_batch/`
  - Batch kernel and vec-env adapter tests.
- `scenario/`
  - Scenario compiler and spatial-query tests.
- `leader/`
  - Leader-layer wiring and runtime-control tests.
- `runners/`
  - Batch runners for grouped JSON contract suites.
- `support/`
  - Shared fakes and helper fixtures used by multiple Python tests.
- `contracts/`
  - JSON specs for contract-driven regressions, grouped by category.
- `diagnostics/`
  - Remaining exploratory/debugging scripts that are not yet suitable as stable contracts.
  - This folder should not host stable regression tests; once a diagnostic becomes deterministic, migrate it back into `runtime/`, `world_batch/`, `scenario/`, `leader/`, or `contracts/`.
- `scenarios/`
  - Reusable scenario fixtures when inline JSON is not practical, for example imported prefab dependencies.

Standalone Python tests should now be the exception, not the default.

Manual one-off probes should not live at the top level of `tests/`.
If a file is primarily for human inspection rather than automated regression,
prefer `tools/diagnostics/` for maintained diagnostics or `tools/archive/` for
legacy/manual probes kept only for reference.

When a standalone test is needed, prefer:

- one focused file per runtime or adapter boundary
- small internal support modules under `tests/` for shared fakes/builders
- direct package imports instead of single-file compatibility shims

## Implementation Entry Points

- Contract execution logic now lives in [python/testing/contracts/](/home/void0312/Workshop/CMO/python/testing/contracts).
- [python/testing/scenario_contract_runner.py](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py) is a compatibility shim that re-exports the packaged contract runner.
- Scenario-side bootstrap logic used by tests now lives in `python/scenario/compiler/` and `python/scenario/runtime/`.
- [python/scenario_compiler.py](/home/void0312/Workshop/CMO/python/scenario_compiler.py) and [python/scenario_runtime.py](/home/void0312/Workshop/CMO/python/scenario_runtime.py) remain compatibility shims for older imports and should not be treated as the primary implementation surface.

## Contract Types

- `loader_command_chain`
  - Validates `TaskOrder -> LeaderIntent -> PilotReport -> MissionCommand` initialization and kernel sync.
- `route_generator`
  - Validates generated waypoint routes, geometry, reachability budget, mode cycling, and world-yaw behavior.
- `env_regression`
  - Validates `UniversalEnv` observation/reward/phase-transition behavior.
- `scripted_bridge`
  - Validates wrapper-driven scripted baselines against scenario success criteria.
- `unit_regression`
  - Validates pure-Python controller/config/loader/wrapper handoff logic without needing full scenario stepping.
  - Also hosts parameterized leader-task generalization checks that mutate C2 task inputs and validate emitted mission-command behavior.

Contract execution lives in [python/testing/contracts/](/home/void0312/Workshop/CMO/python/testing/contracts), with [python/testing/scenario_contract_runner.py](/home/void0312/Workshop/CMO/python/testing/scenario_contract_runner.py) retained only as a compatibility shim.

## How To Run

Run one contract directly:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts in one call:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/route_generator/route_generator_waypoint_modes.json
```

Run a batch runner:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tests/runners/test_contract_batches.py --group chain --group env

cmo_python tests/runners/test_contract_batches.py --group unit --group bridges --group route_generator

cmo_python tests/runners/test_contract_batches.py --group sim_kernel

cmo_python tests/runners/test_contract_batches.py --default-group sim_kernel

cmo_python tools/runners/run_sim_kernel_contracts.py
```

## Dependency Notes

- `gymnasium` is optional in this workspace.
- Contracts that instantiate `UniversalEnv` or wrappers will print `SKIP` when `gymnasium` is not installed.
- Kernel-only contracts such as `loader_command_chain` and many route-generator checks can still run without `gymnasium`.

## Authoring Guidance

Prefer a JSON contract when the regression is mainly:

- one scenario
- one reset/step/check flow
- deterministic numeric or structural assertions
- repeated `repo_root/build/PYTHONPATH` bootstrap

Prefer a standalone Python test only when you truly need:

- custom iterative control flow
- heavy monkeypatching
- nontrivial mocking that cannot be captured by a small dummy contract harness
- richer diagnostics than a contract can reasonably encode

## Naming Conventions

- `tests/contracts/route_generator/*.json`
  - Route generation and route geometry regressions.
- `tests/contracts/env/mission_obs/*.json`
  - Mission observation layout/content regressions.
- `tests/contracts/env/waypoint/*.json`
  - Waypoint reward/route shaping regressions.
- `tests/contracts/env/landing/*.json`
  - Landing/ILS guidance and reward regressions.
- `tests/contracts/env/takeoff/*.json`
  - Takeoff and departure environment regressions.
- `tests/contracts/env/render/*.json`
  - Render/visual-cache regressions.
- `tests/contracts/unit/**/*.json`
  - Pure logic, controller, loader, and config regressions.
- `tests/contracts/unit/comm/*.json`
  - Command-link, task-order, leader-intent, and leader-phase-manager regressions.
  - Includes common-core baseline contracts plus compatibility air-specific comm/tasking contracts.
- `tests/contracts/unit/kernel/*.json`
  - Kernel-driven flight regressions that step `SimulationKernel` directly with scripted pilot inputs.
  - Also hosts simulation guardrails for repeatability, sign consistency, coarse physical plausibility, and small parameter-scan realism checks.
- `tests/contracts/unit/scenarios/*.json`
  - Scenario-template and geometry regressions that validate static JSON content without stepping an env.
- `tests/contracts/unit/training/*.json`
  - Training/bootstrap regressions such as safe action-bias initialization.
- `tests/contracts/unit/wrappers/*.json`
  - Scripted wrapper mode selection, controller handoff, and residual-cap regressions.
- `tests/contracts/unit/world_model/*.json`
  - Replay-buffer and world-model dataset regressions.
- `tests/contracts/bridges/*.json`
  - Scripted wrapper bridge regressions.

## Current Contract Folders

- `tests/contracts/chain/`
  - Command-chain and kernel-sync contracts.
- `tests/contracts/bridges/`
  - Scripted wrapper bridge contracts.
- `tests/contracts/route_generator/`
  - Route generation geometry and budget contracts.
- `tests/contracts/env/mission_obs/`
  - Mission observation contracts.
- `tests/contracts/env/phase/`
  - Mission/phase transition contracts.
- `tests/contracts/env/landing/`
  - Landing/ILS objective, guidance, and reward contracts.
- `tests/contracts/env/waypoint/`
  - Waypoint shaping, tracking, and route semantics contracts.
- `tests/contracts/env/takeoff/`
  - Takeoff/taxi/climb environment contracts.
- `tests/contracts/env/render/`
  - Visual/render/cache environment contracts.
- `tests/contracts/unit/controllers/`
  - Scripted controller logic contracts.
- `tests/contracts/unit/comm/`
  - C2/tasking/command-link contracts for task orders, leader intent, pilot reports, and leader phase transitions.
  - Common-core baselines now live here alongside legacy air-specific contracts while the directory is being split into common-first families.
- `tests/contracts/unit/config/`
  - Config resolution contracts.
- `tests/contracts/unit/env/`
  - Loader/env utility contracts that do not need full scenario stepping.
- `tests/contracts/unit/kernel/`
  - Direct `SimulationKernel` flight regressions for takeoff, ground roll, and stable-flight control laws.
  - Also hosts core simulation guardrails for repeatability, sign consistency, coarse physical plausibility checks, and compact realism parameter scans.
- `tests/contracts/unit/scenarios/`
  - Static scenario/template geometry checks that validate mission JSON assumptions.
- `tests/contracts/unit/training/`
  - Training-time helper contracts that do not need full scenario stepping.
  - Includes leader-task parameter generalization contracts that vary CAP-task inputs and check mission-code reasonableness.
- `tests/contracts/unit/wrappers/`
  - Wrapper/controller handoff contracts driven by dummy observations and loader phases.
- `tests/contracts/unit/world_model/`
  - Replay/dataset contracts for offline or imitation-learning support code.
