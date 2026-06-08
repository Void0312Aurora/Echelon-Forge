# M3-S2 Fire-Closure Batch Validation 2026-06-08

Status: `bounded firing gate accepted / timing and effects quality held`.

## Question

After the A5 weapon-arm action-frame fix, does the active M3-S2 model satisfy
the previously held multi-seed, multi-episode firing-closure gate?

This validation checks only release closure:

- the model requests `fire_once`;
- A5 accepts that request;
- one missile is actually released;
- the release is authorized;
- there are no rejected `fire_once` requests;
- there are no violation releases or repeat releases before assessment.

Damage, effects, target-health drop, and kill-chain outcomes are explicitly out
of scope for this gate.

## Model And Runtime

- Model:
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- Scenario:
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- Train config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
- Action mode: `air_combat_hybrid_v1`
- Max steps per episode: `800`

## Gate

Every checked episode must satisfy:

- `fire_once_requested_count = 1`
- `fire_once_accepted_count = 1`
- `fire_once_rejected_count = 0`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `first_release_step` is reported.

No bounded rejected-request exception was used in this validation.

## Commands

Deterministic batch:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --episodes 8 \
  --seed 20260608 \
  --max_steps 800 \
  --csv_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/deterministic_seed20260608_ep8_800.csv \
  --json_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/deterministic_seed20260608_ep8_800.json
```

Stochastic batch:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --mode model \
  --stochastic \
  --model experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --episodes 8 \
  --seed 20260608 \
  --max_steps 800 \
  --csv_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/stochastic_seed20260608_ep8_800.csv \
  --json_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/stochastic_seed20260608_ep8_800.json
```

## Results

Deterministic batch:

| Seeds | Episodes | Passed | Failed | Release steps | Rejected | Violations | Repeats |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20260608..20260615` | 8 | 8 | 0 | `423, 509, 510, 512, 546, 548, 507, 584` | 0 | 0 | 0 |

Stochastic batch:

| Seeds | Episodes | Passed | Failed | Release steps | Rejected | Violations | Repeats |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20260608..20260615` | 8 | 8 | 0 | `283, 282, 282, 282, 323, 322, 282, 285` | 0 | 0 | 0 |

Combined firing gate:

- episodes checked: `16`
- episodes passed: `16`
- episodes failed: `0`
- first-release step range: `282..584`
- total rejected `fire_once` requests: `0`
- total violation releases: `0`
- total repeat-before-assessment releases: `0`
- effects-event episodes in this batch: `0`
- damage-report episodes in this batch: `0`

## Decision

The active M3-S2 model now passes the bounded multi-seed, multi-episode firing
closure gate for this scenario/config pair. This upgrades the firing part of the
direct fire-boundary owner from `batch closure pending` to `bounded firing gate
accepted`.

This does not accept timing quality, effects quality, target damage, or kill
chain behavior. Those remain separate A8/model-evidence questions.

Training can continue with the release gate treated as closed for this active
slice: future failures should not be debugged first as "the model cannot fire"
unless this batch gate regresses.
