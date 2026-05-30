# Tools README

`tools/` now groups maintained scripts by function instead of keeping every entrypoint at top level.

## Layout

- `tools/eval/`
  - Model/scripted evaluation entrypoints plus shared eval helpers.
- `tools/diagnostics/`
  - Operator-facing probes, benchmarks, and matrix-style diagnostics.
- `tools/runners/`
  - Stable runners for JSON contract suites and similar maintained entrypoints.
- `tools/maintenance/`
  - Workspace audit and cleanup helpers.
- `tools/archive/`
  - Archived ad hoc probes migrated out of repo root.

## Eval

- [eval_task.py](eval/eval_task.py)
  - Unified task evaluator for `stable_flight`, `takeoff_roll`, `centerline`, and `waypoint_nav` across `world_model` and `scripted` backends.
- [eval_sb3.py](eval/eval_sb3.py)
  - Unified SB3 evaluator for `single` and `cooperative` execution policies with mode-specific metrics.
- [task_eval_driver.py](eval/task_eval_driver.py)
  - Shared implementation for single-agent task metrics and backend adapters.
- [eval_utils.py](eval/eval_utils.py)
  - Shared bootstrap, env construction, and stat formatting.
- [world_model_eval_utils.py](eval/world_model_eval_utils.py)
  - Shared checkpoint loading and recurrent world-model rollout helpers.
- [waypoint_eval_utils.py](eval/waypoint_eval_utils.py)
  - Shared waypoint mission-status parsing and geometry metrics.

## Diagnostics

- [benchmark.py](diagnostics/benchmark.py)
  - Unified benchmark CLI for maintained diagnostics families.
- [run_benchmark_suite.py](diagnostics/run_benchmark_suite.py)
  - Unified config-driven entrypoint for maintained benchmark suites under `tools/diagnostics/`.
- [arma_proxy_backend_stub.py](diagnostics/arma_proxy_backend_stub.py)
  - Minimal local TCP backend stub for the first-pass `@EchelonProxy` Arma bridge protocol.
- [arma_proxy_backend_echelon_env.py](diagnostics/arma_proxy_backend_echelon_env.py)
  - Echelon `UniversalEnv`-backed TCP backend that keeps Arma as a presentation shell while backend state steps in-repo.
- [diagnose_cooperative_trajectory.py](diagnostics/diagnose_cooperative_trajectory.py)
  - Unified cooperative trajectory replay/export CLI for `takeoff` and `takeoff_to_cruise`.
- [leader_perf_probe.py](diagnostics/leader_perf_probe.py)
  - Maintained leader-layer throughput probe for `auto/subproc/shared/dummy`.
- [README.md](diagnostics/README.md)
  - Diagnostics catalog and scope notes.

## Runners

- [run_scenario_contract.py](runners/run_scenario_contract.py)
  - Runs one or more JSON contracts from `tests/contracts/`.
- [run_pytest_suite.py](runners/run_pytest_suite.py)
  - Runs a checked-in pytest suite manifest such as `tests/smoke/ci_smoke_suite.json` and fails early on stale path entries.

## Maintenance

- [redundancy_audit.py](maintenance/redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](maintenance/cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](maintenance/isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.
- [translate_docs_batch.py](maintenance/translate_docs_batch.py)
  - Audits bilingual coverage and batch-translates Markdown doc peers with an OpenAI-compatible API.

## Archive

- [README.md](archive/README.md)
  - Scope note for archived root-level probes.
- [batch_api_probe.py](archive/batch_api_probe.py)
  - Quick manual probe for the C++ batch preparation API.
- [world_batch_vec_env_benchmark.py](archive/world_batch_vec_env_benchmark.py)
  - Archived vec-env throughput benchmark that predates the current diagnostics layout.
- [diagnose_training_matrix.py](archive/diagnose_training_matrix.py)
  - Archived helper that parses legacy `evaluate.py` text output for small model/scenario matrices.

## Common Usage

Run contracts:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/env/mission_obs/mission_obs_nav_v1.json
```

Run a scripted eval:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/eval/eval_task.py \
  --task stable_flight \
  --backend scripted \
  --scenario scenarios/stable_flight/stable_flight_stresswind_rewardbalance_v3.json \
  --episodes 10 \
  --max_steps 2000
```

Audit and dry-run cleanup:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/maintenance/redundancy_audit.py --roots tests tools scenarios
cmo_python tools/maintenance/cleanup_redundancy.py --roots tests tools --include_named_tmp_dirs
```

Probe leader-layer throughput:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 24 \
  --vec_backend shared
```

Run a maintained benchmark suite from one config:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/run_benchmark_suite.py \
  --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json
```

Run one maintained benchmark family:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family world_batch_runtime \
  --world-count 8 --setup-iters 64 --iters 512
```

Replay one cooperative trajectory diagnostic:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/diagnose_cooperative_trajectory.py \
  --task takeoff \
  --scenario scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json \
  --train_config examples/config/training/active/cooperative_interval_takeoff_departure_nav_v1.json \
  --model experiments/example/checkpoints/model.zip \
  --output /tmp/cooperative_takeoff_trace.png
```

## Maintenance Guidance

- New maintained task eval behavior should extend `tools/eval/eval_task.py` and `tools/eval/task_eval_driver.py`, not add per-task wrapper scripts.
- New maintained SB3 evaluation behavior should extend `tools/eval/eval_sb3.py` and `tools/eval/sb3_eval_base.py`, not reintroduce split single/cooperative wrappers.
- Shared eval bootstrap should come from `tools.eval.eval_utils`, not copied setup blocks.
- JSON-contract entrypoints should prefer `tools/runners/run_scenario_contract.py` over one-off wrappers.
- Maintained diagnostics should prefer `tools/diagnostics/benchmark.py` for single benchmark families and `tools/diagnostics/run_benchmark_suite.py` for multi-job suites.
- Cooperative trajectory diagnostics should extend `tools/diagnostics/diagnose_cooperative_trajectory.py` and `tools/diagnostics/cooperative_trajectory_base.py`, not add task-specific wrapper CLIs.
- Ad hoc probes and matrix sweeps belong under `tools/diagnostics/`.
- Cleanup/audit helpers belong under `tools/maintenance/`.
- Archived scratch scripts should move to `tools/archive/`, not stay at repo root.
