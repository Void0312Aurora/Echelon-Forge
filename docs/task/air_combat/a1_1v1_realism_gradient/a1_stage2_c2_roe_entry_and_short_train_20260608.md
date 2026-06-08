# A1 Stage-2 C2/ROE Entry And Short Train 2026-06-08

Status: `stage-2 entry prepared / short train behavior preserved / not accepted`.

## Question

M3-S2 has bounded-accepted firing on the active Stage-1 C2/ROE scenario/config
pair. Can A1 now enter the higher-realism Stage-2 lane: a maneuvering red
fighter, no red weapons, and preserved blue single-shot release discipline?

This record covers the training entry and short-train behavior only. It does
not accept hits, damage, kills, or full `combat_win`.

## New Entry

New Stage-2 C2/ROE training-shaped scenario:

`scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json`

New active training config:

`examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`

Boundaries:

- Geometry, platforms, ammunition, and scripted red behavior inherit from the
  canonical Stage-2 evasive-fighter scenario.
- Red still has no usable missiles.
- Mission command fields now include the Stage-1 M3-S2 C2/ROE
  single-shot-then-assess state.
- The config inherits the M3-S2 direct fire-boundary owner without weakening
  A3/A5 legality or the one-shot state machine.

## Entry Probes

Stage-1 full aftermath-window baseline:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/baseline_deterministic_seed20260608_ep1_2400.json`
- model:
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- result: deterministic release at step `423`; effects/damage report at step
  `938`; target health stayed `40.0`; final termination was `combat_timeout`.

Old Stage-2 scenario with the Stage-1 config:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_smoke_model_seed20260608_ep1_64.json`
- result: runnable, but not a usable active Stage-2 C2/ROE entry;
  `policy_event_mask_fire_once_open_count = 0` and
  `authorized_window_step_count = 0`.

New Stage-2 C2/ROE oracle smoke:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_legal_mask_fire_range30k_seed20260608_ep1_3200.json`
- result: 30 km range-gated `legal_mask_fire` released once at step `1071`;
  requested / accepted / rejected was `1 / 1 / 0`;
  release / authorized / violation / repeat-before-assessment was
  `1 / 1 / 0 / 0`; effects/damage was `0 / 0`; final termination was
  `combat_timeout`.

M3-S2 Stage-1 final model transfer smoke:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_model_seed20260608_ep1_3200.json`
- result: deterministic release at step `1311`; requested / accepted /
  rejected was `1 / 1 / 0`; release / authorized / violation /
  repeat-before-assessment was `1 / 1 / 0 / 0`; effects/damage was `0 / 0`;
  final termination was `combat_timeout`.

## Stage-2 8k Short Train

Command:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1 \
  --init_from experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260608 \
  --diagnostics \
  --diagnostics_every 2048
```

Artifacts:

- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/checkpoints/`
- `experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/logs/`

Training observations:

- Training completed `8192` steps.
- Mid-run windows produced usable fire-boundary rows, for example around step
  `1536`: `m3s2/fb_active_count = 179`, `fb_cross_in_window_ratio = 1`.
- Row coverage was unstable later, with several rollout segments reporting
  `fb_active_count = 0`.
- Final diagnostics saw open mask and event-mode threshold crossing:
  `diag/pi_event_fire_mask_frac = 1`, `diag/pi_event_fire_p_mean = 0.568`,
  `diag/pi_event_mode_fire_frac = 1`.
- Training-time diagnostics still recorded no accepted release; saved-model
  probes are the behavior authority.

## Final Model Probes

Deterministic:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_after_8k_deterministic_seed20260608_ep1_3200.json`
- first release: step `1126`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- effects / damage: `0 / 0`
- final target health: `100.0`
- termination: `combat_timeout`

Stochastic:

- artifact:
  `experiments_tmp/a1_stage1_training_continuation_20260608_r1/stage2_c2_roe_after_8k_stochastic_seed20260608_ep1_3200.json`
- first release: step `1082`
- requested / accepted / rejected: `1 / 1 / 0`
- release / authorized / violation / repeat-before-assessment: `1 / 1 / 0 / 0`
- effects / damage: `0 / 0`
- final target health: `100.0`
- termination: `combat_timeout`

## Verdict

The Stage-2 C2/ROE entry is ready for the next training round: runtime accepts
the single-shot release discipline, the Stage-1 M3-S2 final model transfers to
one authorized release, and the post-8k deterministic and stochastic probes both
preserve one accepted authorized release.

Stage-2 is not accepted:

- This is single-seed deterministic/stochastic behavior, not batch validation.
- Fire-boundary row coverage was unstable during Stage-2 8k training.
- Final probes had no effects, damage, health drop, kill, or `combat_win`.
- The stochastic probe had `0` quality-window rows, so its clean release is not
  timing-quality evidence.

Next work should run a small Stage-2 firing-retention batch, then decide whether
to expand training or adjust Stage-2 window/support collection. Do not read this
record as Stage-2 combat-outcome closure.
