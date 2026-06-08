# M3-S2 Direct Fire-Boundary Continuation 2026-06-08

Status: `behavior improved / still held`.

## Question

After the 2026-06-07 direct fire-boundary wiring fix, can continuing from the
accepted r3 checkpoint produce a deterministic learned release without changing
A3/A5 legality, `air_combat_hybrid_v1`, the active M3-S2 config, or the damage
model?

## Method

The run initializes from the previous r3 final model but writes a separate
experiment directory:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_direct_fire_boundary_initfrom_8k_20260608_r1 \
  --init_from experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/final_model.zip \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260608 \
  --diagnostics \
  --diagnostics_every 2048
```

Result: training completed for `8192` steps.

Artifacts:

- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_stochastic_probe.json`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/nonfinite_probe_report.json`

## Training Observations

- The direct fire-boundary update remains live; `m3s2/fb_*` metrics appear
  throughout the run when support rows exist.
- Boundary crossings are still unstable. Examples:
  - step `1024`: `fb_cross_ratio = 0.703`, `fb_cross_in_window_ratio = 1.0`;
  - step `1536`: `fb_cross_ratio = 0.91`, `fb_cross_in_window_ratio = 0.914`;
  - step `6144`: `fb_cross_ratio = 0.73`, `fb_cross_in_window_ratio = 0.957`;
  - step `7936`: `fb_positive_count = 168`, but `fb_cross_count = 0`.
- At diagnostics step `6144`, the event head crosses deterministic event mode:
  `diag/pi_event_fire_p_mean = 0.517` and `diag/pi_event_mode_fire_frac = 1`.
  The same diagnostics point still records `diag/action_fire_weapon_frac = 0`
  and `diag/a5_fire_once_requested_count = 0`.
- At final diagnostics step `8192`, the event head is again over the open-window
  threshold: `diag/pi_event_fire_p_mean = 0.634` and
  `diag/pi_event_mode_fire_frac = 1`, while `diag/action_fire_weapon_frac = 0`
  and `diag/a5_fire_once_requested_count = 0` remain in the callback window.

## Learned-Policy Probes

Deterministic probe:

- `first_release_step = 423`
- `fire_once_requested_count = 1`
- `fire_once_accepted_count = 1`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `effects_event_count = 1`
- `damage_report_count = 1`
- `last_effect_miss_distance_m = 6.0240553390109595`
- `last_damage_system_health_delta = 0.0`
- `last_damage_loss_state = combat_capable`
- `final_missiles = 3`
- `final_target_health = 40.0`

Stochastic probe:

- `first_release_step = 290`
- `fire_once_requested_count = 2`
- `fire_once_accepted_count = 1`
- `fire_once_rejected_count = 1`
- `fire_once_rejected_reason_counts = {"weapon_not_ready": 1}`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `effects_event_count = 0`
- `damage_report_count = 0`
- `final_missiles = 3`
- `final_target_health = 40.0`

## Decision

This is the first active M3-S2 evidence where the deterministic learned policy
executes one legal authorized release. That is a meaningful behavior improvement
over the 2026-06-07 r3 run.

It is still not accepted as learned fire-timing closure:

- the deterministic release is a single-seed, single-episode probe;
- stochastic probing still makes an extra `weapon_not_ready` rejected request;
- quality-window timing is not yet clean because stochastic release occurs
  before any recorded quality-window rows;
- the deterministic shot records effects and a damage report, but no health
  drop or mission/mobility/sensor kill;
- the current damage result stays within the A8 boundary: it is a non-authority
  effects-chain observation, not a Pk or AIM-120C kill claim.

Next work should treat this as `behavior improved / held`: preserve the direct
fire-boundary owner and investigate the remaining event-mode to action-pulse
diagnostic gap, stochastic rejected-request path, and post-release effect
quality without weakening A3/A5 release legality.
