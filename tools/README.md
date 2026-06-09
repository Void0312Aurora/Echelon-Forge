# Tools README

`tools/` now groups maintained scripts by function instead of keeping every entrypoint at top level.

## Domain Posture

- Most general eval examples here still target air/execution tasks; cooperative/common is covered by the maintained SB3 and leader diagnostics paths.
- For active training/eval parity, prefer configs that use the runtime-facade/world-batch path. Direct `UniversalEnv` tools are compatibility diagnostics unless they explicitly opt into `runtime_compatibility_enabled`.
- Naval N4 has a maintained scoped gate in `tools/eval/eval_naval_n4_baseline.py`.
- Ground tasking/schema bootstrap does not yet have a maintained eval or diagnostic runner in `tools/`; do not infer full ground runtime support from this catalog.

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
  - Air/execution task evaluator for `stable_flight`, `takeoff_roll`, `centerline`, and `waypoint_nav` across `world_model` and `scripted` backends. It is a raw-`UniversalEnv` compatibility path, not a multi-domain acceptance gate.
- [eval_sb3.py](eval/eval_sb3.py)
  - Unified SB3 evaluator for `single` and `cooperative` execution policies with mode-specific metrics. `single` uses WorldBatchRuntime when `runtime.world_batch_vec_env=true`; otherwise it falls back to the raw-`UniversalEnv` compatibility path. `cooperative` uses `CooperativeWorldBatchVecEnv`.
- [eval_naval_n4_baseline.py](eval/eval_naval_n4_baseline.py)
  - Scoped N4 naval cooperative gate for stationing, pre-fire ROE hold reward terms, and contact-evidence plumbing. This is not a learned-policy acceptance.
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
- [air_combat_stage0_process_probe.py](diagnostics/air_combat_stage0_process_probe.py)
  - Scoped air-combat stage-0/stage-1 process probe for weapon-employment/debug traces and hybrid action metrics on the compatibility env path.
- [analyze_cooperative_observation_scales.py](diagnostics/analyze_cooperative_observation_scales.py)
  - Observation-scale sampler for cooperative execution configs; useful for numeric hygiene, not a training runner.
- [trace_training_nonfinite_source.py](diagnostics/trace_training_nonfinite_source.py)
  - Focused cooperative training NaN/Inf tracer that reconstructs the maintained cooperative flow and stops with a JSON report.
- [README.md](diagnostics/README.md)
  - Diagnostics catalog and scope notes.

## Runners

- [run_scenario_contract.py](runners/run_scenario_contract.py)
  - Runs one or more JSON contracts from `tests/contracts/`, or a checked-in suite manifest such as `tests/smoke/ci_contract_suite.json`.
- [run_pytest_suite.py](runners/run_pytest_suite.py)
  - Runs a checked-in pytest suite manifest such as `tests/smoke/ci_smoke_suite.json` and fails early on stale path entries.
  - Suite entries may be directories, files, or pytest node IDs such as `tests/foo/test_bar.py::test_case`; node ID entries still validate the base path before invoking pytest.
- [run_sim_kernel_contracts.py](runners/run_sim_kernel_contracts.py)
  - Thin wrapper around the contract-batch runner with the default `sim_kernel` group.

## Maintenance

- [redundancy_audit.py](maintenance/redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](maintenance/cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.
- [isolate_repro_workspace.sh](maintenance/isolate_repro_workspace.sh)
  - Moves selected experiment/dataset directories aside to create a smaller repro workspace.
- [translate_docs_batch.py](maintenance/translate_docs_batch.py)
  - Audits bilingual coverage and batch-translates Markdown doc peers with an OpenAI-compatible API.
- A2 `a2_blastfrag_*.py`, `a2_candidate_vps_bundle.py`, and `a2_retained_manifest_integrity.py`
  - Task-specific A2 candidate/retained-artifact governance helpers. They are non-authoritative maintenance gates and are not part of the runtime product surface.

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

Run the scoped naval N4 gate:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/eval/eval_naval_n4_baseline.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --steps 1200
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

- New raw-env/task-metric eval behavior should extend `tools/eval/eval_task.py` and `tools/eval/task_eval_driver.py`, with explicit compatibility handling where needed, not add per-task wrapper scripts.
- New maintained SB3 evaluation behavior should extend `tools/eval/eval_sb3.py` and `tools/eval/sb3_eval_base.py`, not reintroduce split single/cooperative wrappers.
- Shared eval bootstrap should come from `tools.eval.eval_utils`, not copied setup blocks.
- JSON-contract entrypoints should prefer `tools/runners/run_scenario_contract.py` over one-off wrappers.
- Maintained diagnostics should prefer `tools/diagnostics/benchmark.py` for single benchmark families and `tools/diagnostics/run_benchmark_suite.py` for multi-job suites.
- Cooperative trajectory diagnostics should extend `tools/diagnostics/diagnose_cooperative_trajectory.py` and `tools/diagnostics/cooperative_trajectory_base.py`, not add task-specific wrapper CLIs.
- Ad hoc probes and matrix sweeps belong under `tools/diagnostics/`.
- Cleanup/audit helpers belong under `tools/maintenance/`.
- Archived scratch scripts should move to `tools/archive/`, not stay at repo root.
