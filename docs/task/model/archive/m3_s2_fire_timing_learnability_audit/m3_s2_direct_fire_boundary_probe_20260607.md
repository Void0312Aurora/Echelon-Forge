# M3-S2 Direct Fire-Boundary Probe 2026-06-07

Status: `held behavior / accepted wiring fix`.

## Question

Can the active M3-S2 config make the existing `hybrid_event_head` the direct
executable fire-boundary owner while preserving HMoE, PPO, `air_combat_hybrid_v1`,
and the A5 runtime fire gate?

## Change

- The active M3-S2 config disables the M3 stopping-head and window-classifier
  event adapters.
- The direct `hybrid_event_head` is trained by a dedicated M3-S2 fire-boundary
  auxiliary update against the final executable fire-event logit delta.
- `NonFiniteTrainingProbe.traced_train()` now runs and logs that same direct
  fire-boundary update. Before this fix, active short training with nonfinite
  probe enabled silently bypassed the new update path.
- Fire-boundary logger keys use the short `m3s2/fb_*` prefix to avoid SB3 human
  logger truncation collisions.

## Verification

Focused tests:

```bash
python3 -m pytest -q \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

Result: `93 passed in 37.00s`.

Short train:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python3 train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_direct_fire_boundary_8k_20260607_r3 \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260607 \
  --diagnostics \
  --diagnostics_every 2048
```

Result: training completed for `8192` steps.

Artifacts:

- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/final_model.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_2048_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_4096_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_6144_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_8192_steps.zip`

## Observations

The wiring fix is real:

- `m3s2/fb_*` tags appear from step `512`.
- At step `512`, `m3s2/fb_active_count = 255`, `m3s2/fb_negative_count = 255`,
  and `m3s2/fb_grad_norm = 0.654093`.
- At positive-window updates, `m3s2/fb_grad_norm` repeatedly reaches about
  `1.36e3` to `1.40e3`, proving the direct boundary update is active.

The learned behavior is still held:

- At step `4096`, fire mask is open and `diag/pi_event_fire_p_mean = 0.373841`,
  up from the earlier no-update run's near-zero values, but
  `diag/pi_event_mode_fire_frac = 0`.
- At step `6144`, fire mask is open and `diag/pi_event_fire_p_mean = 0.489228`,
  still just below the deterministic mode threshold.
- At step `8192`, fire mask is open but `diag/pi_event_fire_p_mean = 0.0238934`
  after later negative-heavy updates pull the boundary back down.
- `diag/a5_fire_once_requested_count = 0`,
  `diag/a5_release_executed_count = 0`, and
  `diag/action_fire_weapon_frac = 0` at all diagnostics points.

The sidecar target distribution is unstable:

- Positive rows are intermittent: examples include `225` positives at steps
  `768`, `1024`, `1536`, `3840`; `206` at `4096`; `0` at multiple negative-only
  updates; and `165` at `8192`.
- Boundary crossing appears only transiently: `m3s2/fb_cross_ratio = 1` at
  `1536`, `0.925781` at `4096`, `0.058594` at `6400`, and `0` at the final
  `8192` update.
- Positive and negative logit means often move together, for example near
  `4096`: positive `0.057552`, negative `-0.094755`. This indicates the update
  has not formed a robust prewindow-versus-quality discriminator.

## Decision

Accept the wiring fix and reject behavioral acceptance.

The prior short-train no-effect result was caused by a concrete implementation
break: `NonFiniteTrainingProbe` patched `model.train()` with an older copy that
did not run the direct fire-boundary auxiliary update. After fixing that path,
the active train emits direct-boundary metrics and moves the executable fire
probability by two orders of magnitude.

However, the model still does not reliably cross the deterministic fire
threshold in the open window. The remaining issue is no longer "the update path
is missing"; it is the online target/support distribution and boundary
calibration still pulling the direct event head between positive-heavy,
negative-heavy, and empty support batches.
