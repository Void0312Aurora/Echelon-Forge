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

- [eval_centerline.py](/home/void0312/CMO/tools/eval/eval_centerline.py)
  - Runway centerline deviation summary for world-model checkpoints.
- [eval_centerline_scripted.py](/home/void0312/CMO/tools/eval/eval_centerline_scripted.py)
  - Scripted takeoff centerline summary.
- [eval_stable_flight.py](/home/void0312/CMO/tools/eval/eval_stable_flight.py)
  - Stable-flight tracking summary for world-model checkpoints.
- [eval_stable_flight_scripted.py](/home/void0312/CMO/tools/eval/eval_stable_flight_scripted.py)
  - Stable-flight tracking summary for scripted control.
- [eval_takeoff_roll.py](/home/void0312/CMO/tools/eval/eval_takeoff_roll.py)
  - Takeoff roll, wheel-off, and liftoff summary for world-model checkpoints.
- [eval_takeoff_roll_scripted.py](/home/void0312/CMO/tools/eval/eval_takeoff_roll_scripted.py)
  - Takeoff roll summary for scripted control.
- [eval_waypoint_nav.py](/home/void0312/CMO/tools/eval/eval_waypoint_nav.py)
  - Waypoint-navigation summary for world-model checkpoints.
- [eval_waypoint_nav_scripted.py](/home/void0312/CMO/tools/eval/eval_waypoint_nav_scripted.py)
  - Waypoint-navigation summary for scripted control.
- [eval_sb3_policy.py](/home/void0312/CMO/tools/eval/eval_sb3_policy.py)
  - Generic SB3 execution-policy evaluator from a train config.
- [eval_utils.py](/home/void0312/CMO/tools/eval/eval_utils.py)
  - Shared bootstrap, env construction, and stat formatting.
- [world_model_eval_utils.py](/home/void0312/CMO/tools/eval/world_model_eval_utils.py)
  - Shared checkpoint loading and recurrent world-model rollout helpers.
- [waypoint_eval_utils.py](/home/void0312/CMO/tools/eval/waypoint_eval_utils.py)
  - Shared waypoint mission-status parsing and geometry metrics.

## Diagnostics

- [leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py)
  - Maintained leader-layer throughput probe for `auto/subproc/shared/dummy`.
- [README.md](/home/void0312/CMO/tools/diagnostics/README.md)
  - Diagnostics catalog and scope notes.

## Runners

- [run_scenario_contract.py](/home/void0312/CMO/tools/runners/run_scenario_contract.py)
  - Runs one or more JSON contracts from `tests/contracts/`.

## Maintenance

- [redundancy_audit.py](/home/void0312/CMO/tools/maintenance/redundancy_audit.py)
  - Audits duplicate/temp-like workspace content.
- [cleanup_redundancy.py](/home/void0312/CMO/tools/maintenance/cleanup_redundancy.py)
  - Dry-run or apply cleanup for cache/temp artifacts.

## Archive

- [README.md](/home/void0312/CMO/tools/archive/README.md)
  - Scope note for archived root-level probes.
- [batch_api_probe.py](/home/void0312/CMO/tools/archive/batch_api_probe.py)
  - Quick manual probe for the C++ batch preparation API.
- [world_batch_vec_env_benchmark.py](/home/void0312/CMO/tools/archive/world_batch_vec_env_benchmark.py)
  - Archived vec-env throughput benchmark that predates the current diagnostics layout.

## Common Usage

Run contracts:

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
python tools/runners/run_scenario_contract.py --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts:

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/env/mission_obs/mission_obs_nav_v1.json
```

Run a scripted eval:

```bash
python tools/eval/eval_stable_flight_scripted.py \
  --scenario scenarios/stable_flight/stable_flight_stresswind_rewardbalance_v3.json \
  --episodes 10 \
  --max_steps 2000
```

Audit and dry-run cleanup:

```bash
python tools/maintenance/redundancy_audit.py --roots tests tools scenarios
python tools/maintenance/cleanup_redundancy.py --roots tests tools --include_named_tmp_dirs
```

Probe leader-layer throughput:

```bash
./.venv/bin/python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 24 \
  --vec_backend shared
```

## Maintenance Guidance

- New maintained eval entrypoints belong under `tools/eval/`, not top-level `tools/`.
- Shared eval bootstrap should come from `tools.eval.eval_utils`, not copied setup blocks.
- JSON-contract entrypoints should prefer `tools/runners/run_scenario_contract.py` over one-off wrappers.
- Ad hoc probes and matrix sweeps belong under `tools/diagnostics/`.
- Cleanup/audit helpers belong under `tools/maintenance/`.
- Archived scratch scripts should move to `tools/archive/`, not stay at repo root.
