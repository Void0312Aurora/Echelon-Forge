# M3-S2 Chain Breakpoint Probe

Parent: [README.md](README.md).

Status: `2026-06-06` root-cause localization evidence.

## Purpose

This probe stops mechanism guessing and splits the fire-timing chain into
testable breakpoints:

```text
fixed forced-hold trajectory
  -> label/target support
  -> frozen actor latent separability
  -> M3 stopping-head optimization on frozen latent
  -> action-distribution adapter
  -> edge-trigger pulse semantics
  -> current learned policy
```

The key rule is that each segment must produce a yes/no result on the same
fixed real Stage-1 trajectory.

## Implementation

New diagnostic:

```text
tools/diagnostics/m3s2_chain_breakpoint_probe.py
```

Focused test:

```text
tests/training/test_fire_timing_fault_localization_contracts.py
```

Verification:

```bash
python -m compileall -q \
  tools/diagnostics/m3s2_chain_breakpoint_probe.py \
  tests/training/test_fire_timing_fault_localization_contracts.py

python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Result: `3 passed in 2.48s`.

## Runs

Primary run:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/m3s2_chain_breakpoint_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --model experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max-steps 2400 \
  --fit-steps 3000 \
  --fit-lr 0.01 \
  --json-out experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit.json
```

Learning-rate sensitivity run:

```text
experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit_lr003.json
```

## Results

Fixed forced-hold collection:

| Field | Value |
| --- | ---: |
| rows | 2400 |
| legal rows | 1880 |
| prewindow rows | 840 |
| quality rows | 1040 |
| accepted rollout events | 0 |

Breakpoint table:

| Segment | Result | Evidence |
| --- | --- | --- |
| Label/target support | pass | The fixed trajectory contains both prewindow (`840`) and quality (`1040`) rows. |
| Current learned policy | fail | Current M3 head and event distribution have `0 / 1040` quality boundary rows and event mode fires `0` times. |
| Frozen actor latent with standardized linear head | pass | Accuracy `1.0`; prewindow boundary `0 / 840`; quality boundary `1040 / 1040`; quality pulse can be separated with margin `10.698`. |
| Folded standardized head through action adapter | behavior pass | Event mode fires `0 / 840` prewindow rows and `1040 / 1040` quality rows; edge-trigger simulation produces one quality pulse at row `281`. |
| Direct raw M3 head on frozen latent | strict fail / near pass | With `lr=0.01`, leaves `6` prewindow boundary rows and misses `5` quality rows; with `lr=0.03`, leaves `4` prewindow boundary rows and misses `2` quality rows. |
| Edge-trigger transport | pass for folded head | One legal pulse, first pulse is quality, no prewindow pulse. |

The folded standardized head also reports `delta_identity_pass = false`
(`max_abs` difference around `3.52` to `4.23`), but this is a calibration
difference, not a behavior failure: the action mode and edge-trigger pulse are
correct after the folded head is installed.

## Verdict

The first failing breakpoint is no longer environment reachability, labels,
observation signal, actor latent capacity, action adapter behavior, or
edge-trigger semantics. All of those can pass on the fixed real trajectory.

The localized break is:

```text
m3_head_optimization_conditioning
```

In plain terms: the current actor latent already contains the window signal,
and a normalized linear stopping head can turn it into the correct executable
quality-window pulse. The online learned M3 head does not learn that calibrated
separator. Directly optimizing the raw M3 head on the frozen latent nearly
succeeds but leaves a handful of prewindow positives, which are catastrophic
for one-shot stopping because any prewindow rising edge consumes the shot.

The next repair should therefore target head normalization/calibration and the
online auxiliary optimization contract, not another reward tweak or a larger
sequence-memory model.
