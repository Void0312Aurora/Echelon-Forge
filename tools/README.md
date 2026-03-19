# Tools README

`tools/` contains repo-maintenance helpers, contract runners, and evaluation entry points.

The recent cleanup work is moving this directory toward shared bootstrap helpers instead of per-script copy/paste.

## Core Utilities

- [run_scenario_contract.py](/home/void0312/CMO/tools/run_scenario_contract.py)
  - Runs one or more JSON contracts from `tests/contracts/` and its category subfolders.
  - Supports mixed contract types in a single invocation.
  - Prints `SKIP` instead of failing when an optional dependency is missing.
- [eval_utils.py](/home/void0312/CMO/tools/eval_utils.py)
  - Shared repo bootstrap, argument helpers, env construction, and stat formatting for eval scripts.
- [world_model_eval_utils.py](/home/void0312/CMO/tools/world_model_eval_utils.py)
  - Shared checkpoint loading, observation preprocessing, actor dispatch, and recurrent world-model rollout state for world-model eval scripts.
- [waypoint_eval_utils.py](/home/void0312/CMO/tools/waypoint_eval_utils.py)
  - Shared waypoint mission-status parsing and geometry accuracy metrics used by waypoint evaluators.

## Top-Level Layout

- Top-level `tools/`
  - Stable entrypoints and shared helpers.
- `tools/diagnostics/`
  - Exploratory operator-facing diagnostics and matrix runners.

## Scripted Eval Entrypoints

- [eval_centerline_scripted.py](/home/void0312/CMO/tools/eval_centerline_scripted.py)
  - Scripted takeoff centerline deviation summary.
- [eval_stable_flight_scripted.py](/home/void0312/CMO/tools/eval_stable_flight_scripted.py)
  - Scripted stable-flight tracking summary.
- [eval_takeoff_roll_scripted.py](/home/void0312/CMO/tools/eval_takeoff_roll_scripted.py)
  - Scripted wheel-off/liftoff distance and timing summary.
- [eval_waypoint_nav_scripted.py](/home/void0312/CMO/tools/eval_waypoint_nav_scripted.py)
  - Scripted waypoint-navigation success and geometry summary.

These scripts now share common environment/bootstrap logic through `eval_utils.py`.
The world-model variants also share rollout/runtime code through `world_model_eval_utils.py`.

## Maintenance Helpers

- [redundancy_audit.py](/home/void0312/CMO/tools/redundancy_audit.py)
  - Audits candidate duplicate or temp-like directories/files.
- [cleanup_redundancy.py](/home/void0312/CMO/tools/cleanup_redundancy.py)
  - Deletes cache/temp artifacts in dry-run or apply mode.

## Diagnostics

- [tools/diagnostics/diagnose_training_matrix.py](/home/void0312/CMO/tools/diagnostics/diagnose_training_matrix.py)
  - Runs an evaluator over multiple model/scenario pairs and summarizes extracted metrics.
- [tools/diagnostics/sanity_check.py](/home/void0312/CMO/tools/diagnostics/sanity_check.py)
  - Lightweight kernel/API sanity probe for local debugging.

## Common Usage

Run contracts:

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
python tools/run_scenario_contract.py --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

Run multiple contracts:

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
python tools/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/env/mission_obs/mission_obs_nav_v1.json
```

Run the leader C2-parameter generalization contract:

```bash
python tools/run_scenario_contract.py --spec \
  tests/contracts/unit/training/leader_task_generalization_c2_params.json
```

Run a scripted eval:

```bash
python tools/eval_stable_flight_scripted.py \
  --scenario scenarios/stable_flight/stable_flight_stresswind_rewardbalance_v3.json \
  --episodes 10 \
  --max_steps 2000
```

Audit and dry-run cleanup:

```bash
python tools/redundancy_audit.py --roots tests tools scenarios
python tools/cleanup_redundancy.py --roots tests tools --include_named_tmp_dirs
```

Run a diagnostic matrix:

```bash
python tools/diagnostics/diagnose_training_matrix.py --help
```

## Maintenance Guidance

- If a new eval script needs the usual repo/build/env bootstrap, import from `eval_utils.py` instead of copying setup code.
- If a regression can be expressed as a JSON contract, prefer `tests/contracts/` plus `run_scenario_contract.py` over adding another one-off Python wrapper.
- If a script exists only to call one contract, consider folding it into an existing batch runner before adding a new top-level file.
- If a script is mainly for ad hoc inspection or checkpoint sweeps, place it under `tools/diagnostics/` instead of top-level `tools/`.
