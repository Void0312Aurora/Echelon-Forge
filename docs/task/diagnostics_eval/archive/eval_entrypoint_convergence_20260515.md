<!-- Machine-translated draft generated on 2026-05-18 from docs/task/diagnostics_eval/eval_entrypoint_convergence_20260515.zh.md. Review before treating this file as authoritative. -->

# Eval and Diagnostic Entry Convergence Master Plan

Status: Phase 1, Phase 2, Phase 3, Phase 4 completed.

Date: `2026-05-15`

## 1. Background

Recent explorations around HMoE, cooperative execution, terminal eval, and trajectory diagnostics have yielded many insights. The core runtime and training pipeline have gradually stabilized, but the evaluation and diagnostic script layer has experienced significant entry inflation:

- The same task often has two independent scripts: `world-model` and `scripted`.
- Different scripts repeatedly duplicate episode loops, metric sampling, environment construction, and output formatting.
- If this status quo continues, each new evaluation dimension will require copying more scripts.

This inflation leads to three direct problems:

- High maintenance cost: correcting a metric semantic requires syncing changes across multiple entries.
- High risk of behavioral drift: different entries easily fork on thresholds, defaults, and output fields.
- High collaboration cost: users find it difficult to determine "which script should be reused" rather than creating a new one.

## 2. Confirmed Findings

### 2.1 Clearly Existing Duplicate Clusters

Before convergence, `tools/eval` had 4 most obvious pairs of entries:

- `eval_stable_flight.py`
- `eval_stable_flight_scripted.py`
- `eval_takeoff_roll.py`
- `eval_takeoff_roll_scripted.py`
- `eval_centerline.py`
- `eval_centerline_scripted.py`
- `eval_waypoint_nav.py`
- `eval_waypoint_nav_scripted.py`

The differences between these scripts are mainly concentrated in:

- Different controller sources:
  - `world-model checkpoint`
  - `scripted controller`
- A few different default parameters:
  - `device`
  - `action_mode`
  - Whether to expose `--no_randomization`
- A few minor historical output details.

Beyond these, the following parts are highly duplicated:

- `argparse` common parameter assembly
- `UniversalEnv` construction
- episode reset / step / done loop
- `mission_status` parsing
- Metric aggregation and summary printing

### 2.2 Existing Generalization Foundations Are Already Present, but Not Implemented at the Entry Layer

The repository already has some shared utilities:

- [tools/eval/eval_utils.py](../../../../tools/eval/eval_utils.py)
- [tools/eval/waypoint_eval_utils.py](../../../../tools/eval/waypoint_eval_utils.py)
- [tools/eval/world_model_eval_utils.py](../../../../tools/eval/world_model_eval_utils.py)

This shows the problem is not "cannot abstract", but "abstraction is only done locally, not pushed to entry convergence".

### 2.3 Areas Not to Be Addressed in the Initial Phase

At the start of the initial phase, the following areas, while superficially similar, are not included in the first batch:

- `tools/diagnostics/diagnose_cooperative_takeoff_trajectory.py`
- `tools/diagnostics/diagnose_cooperative_takeoff_to_cruise_trajectory.py`
- HMoE / pipeline shell scripts in `scripts/*.sh`

Reasons:

- Cooperative trajectory diagnostics are not just "different entries", but also carry world/slot aggregation and chart semantic differences.
- These scripts recently served formal experiments, so the risk is higher than single-agent task evals.
- More suitable to be handled separately in a later phase.

## 3. Phased Freeze Plan

### 3.1 Phase 1: Single-Agent Task Eval Entry Convergence

Goal:

- Unify the single-agent task eval entry for `stable_flight / takeoff_roll / centerline / waypoint_nav`
- Remove the paired `scripted / world-model` shell scripts

Freeze Scope:

- Add shared evaluation driver
- Add formal unified CLI
- Delete old 8 task eval entry shells

Acceptance Criteria:

- Only one formal CLI remains for single-agent task eval
- No more copying of the full episode loop across multiple entries
- Syntax and `--help` smoke tests passed

Implementation Results:

- Added [tools/eval/task_eval_driver.py](../../../../tools/eval/task_eval_driver.py)
- Added [tools/eval/eval_task.py](../../../../tools/eval/eval_task.py)
- Deleted old 8 task eval entry shells

Smoke Tests Completed:

- `python -m py_compile tools/eval/task_eval_driver.py ...`
- `./.venv/bin/python tools/eval/eval_task.py --help`
- `./.venv/bin/python tools/eval/eval_task.py --task stable_flight --backend world_model --help`
- `./.venv/bin/python tools/eval/eval_task.py --task takeoff_roll --backend scripted --help`

Phase Notes:

- The `wheel_off` judgment for `takeoff_roll` retains the slight semantic difference between the historical scripted/world-model versions to avoid changing existing metric standards.
- `centerline` output style is unified, but metric content remains equivalent.

### 3.2 Phase 2: SB3 Eval Shared Base Convergence

Goal:

- Extract the shared base from the old dual entries `eval_sb3_policy.py` and `eval_sb3_cooperative_policy.py`
- Do not merge CLI, only reduce duplicate implementation

Freeze Scope:

- JSON configuration loading
- SB3 / AdaptiveKLPPO model loading
- `resolve_env_settings` override
- Common argparse parameters
- `json_out` file writing

Explicitly Not Done:

- Merge single-agent SB3 and cooperative SB3 into one command
- Rewrite cooperative world/slot aggregation logic

Implementation Results:

- Added [tools/eval/sb3_eval_base.py](../../../../tools/eval/sb3_eval_base.py)
- At phase 2 completion, the old dual entries have switched to the shared base
- Phase 4 further unified this into [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py)

Smoke Tests Completed:

- `python -m py_compile tools/eval/sb3_eval_base.py`
- Phase 4 unified CLI smoke test see `3.4`

### 3.3 Phase 3: Cooperative Trajectory Diagnostic Entry Convergence

Goal:

- Extract the shared base for cooperative trajectory diagnostics
- Converge `takeoff` and `takeoff_to_cruise` into one formal CLI

Freeze Scope:

- Shared configuration loading and model loading
- Shared cooperative env construction and curriculum application
- Shared trace sampling driver, export, and common plotting skeleton
- Unified cooperative trajectory CLI, and delete old dual entry shells

Explicitly Not Done:

- Force unification of slot summary schemas across different tasks
- Major changes to output chart semantics

Phase Judgment:

- The two scripts share a large skeleton, but have structural differences in sampling fields, slot summary, and chart panels
- These differences are better kept in task branch logic rather than maintaining two top-level entries

Implementation Results:

- Added [tools/diagnostics/cooperative_trajectory_base.py](../../../../tools/diagnostics/cooperative_trajectory_base.py)
- Added [tools/diagnostics/diagnose_cooperative_trajectory.py](../../../../tools/diagnostics/diagnose_cooperative_trajectory.py)
- Deleted old `tools/diagnostics/diagnose_cooperative_takeoff_trajectory.py`
- Deleted old `tools/diagnostics/diagnose_cooperative_takeoff_to_cruise_trajectory.py`

Smoke Tests Completed:

- `python -m py_compile tools/diagnostics/cooperative_trajectory_base.py tools/diagnostics/diagnose_cooperative_trajectory.py`
- `./.venv/bin/python tools/diagnostics/diagnose_cooperative_trajectory.py --help`
- `./.venv/bin/python tools/diagnostics/diagnose_cooperative_trajectory.py --task takeoff --help`

### 3.4 Phase 4: SB3 Eval Formal CLI Convergence

Goal:

- Converge single-agent `SB3` and cooperative `SB3` evaluation into one formal entry
- Clean up the last remaining CLI compatibility layer
- Switch scripts, documentation, and tests to the unified entry

Freeze Scope:

- Add unified CLI
- Delete old two `SB3` eval entries
- Migrate README, scripts, tests, and task documentation references

Acceptance Criteria:

- Only one formal `SB3` evaluation entry remains under `tools/eval/`
- Existing single-agent and cooperative evaluation JSON schema remain compatible
- `--help`, `py_compile`, and cooperative runtime smoke tests pass

Implementation Results:

- Added [tools/eval/eval_sb3.py](../../../../tools/eval/eval_sb3.py)
- Deleted old `tools/eval/eval_sb3_policy.py`
- Deleted old `tools/eval/eval_sb3_cooperative_policy.py`
- Related scripts, README, specialized documentation, and runtime tests have been migrated to the unified entry

Smoke Tests Completed:

- `python -m py_compile tools/eval/eval_sb3.py tools/eval/sb3_eval_base.py`
- `./.venv/bin/python tools/eval/eval_sb3.py --help`
- `./.venv/bin/python tools/eval/eval_sb3.py --mode single --help`
- `./.venv/bin/python tools/eval/eval_sb3.py --mode cooperative --help`
- `./.venv/bin/python -m pytest -q tests/eval/test_eval_sb3.py`

## 4. Documentation Constraints

This master plan is the only phase-planning document for this topic. All current freeze phases have been completed.

If further progress is made in the future:

- First, backfill the corresponding phase in this file.
- Only add auxiliary documents when recording detailed investigation notes for a specific topic.
- Auxiliary documents must not again assume the role of "phase plan" alongside this file.
