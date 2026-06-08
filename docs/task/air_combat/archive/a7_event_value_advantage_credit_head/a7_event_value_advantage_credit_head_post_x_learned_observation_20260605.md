# A7 Post-X Learned Observation

Status: `2026-06-05` completed as bounded learned-policy evidence; held
outcome.

Parent: [README.md](README.md).

## Purpose

`A7-EVC-X` repaired rollout-boundary first-event credit state in focused tests:
chunked PPO rollouts can now carry same-episode context and recover the
shadow-quality positives that were present in the full episode. This note
records the post-X learned-policy observation and separates three questions:

- whether the repaired signal reaches training;
- whether deterministic policy execution crosses the `fire_once` event-mode
  threshold;
- whether stochastic execution preserves A3/A5 one-shot legality and produces
  missile effects.

## Run

Training command:

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --run_name a7_cross_rollout_state_32k_20260605_r1 \
  --output_base experiments_tmp \
  --seed 7
```

Output:

- Run directory:
  `experiments_tmp/a7_cross_rollout_state_32k_20260605_r1`
- Final model:
  `experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip`
- Completed `32768` timesteps.

## Training Observation

The X repair is active in the learned training path. Early in the run,
cross-rollout carried context restored shadow/projection activity that was
previously censored:

- at `3072` timesteps:
  `a7/evc_carried_shadow_positive_count_mean=693`,
  `a7/evc_cross_rollout_context_rows~=1024`,
  `a7/evc_cross_rollout_first_event_count_mean=699`,
  `a7/evc_proj_active_count_mean=346`, and
  `a7/event_credit_target_positive_frac=0.985`;
- between `5120` and `7168` timesteps,
  `a7/event_credit_advantage_mean` moved from `0.113` to `0.567`;
- later legal-open source rows stayed visible in several windows, for example
  `a7/evc_src_legal_open_quality_positive_count_mean=512` at `14336` and
  `15360` timesteps.

The improvement did not become stable policy acceptance. Later windows
oscillated:

- at `20480` timesteps, the diagnostic window had an open fire mask and
  `a6/event_fire_prob_mean_open=0.0877`, but `pi_event_mode_fire_frac=0` and
  `a7/evc_adv_mean_open=-0.437`;
- at `30720` timesteps, open-window event fire probability improved to
  `0.287`, but `pi_event_mode_fire_frac` remained `0` and no release executed;
- final `32768` timestep logs ended with
  `a7/event_credit_active_count_mean=512`,
  `a7/event_credit_target_positive_frac=0.77`, and
  `a7/event_credit_advantage_mean=-0.198`.

Interpretation: cross-rollout credit state is no longer the immediate training
path censoring fault. The remaining failure is closer to event-mode threshold /
policy execution and downstream launch/effects coupling than to missing
post-boundary labels alone.

## Process Probes

Deterministic probe:

```bash
python tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip \
  --episodes 2 \
  --max_steps 640 \
  --device auto \
  --json_out experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/a7_cross_rollout_deterministic_probe.json \
  --csv_out experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/a7_cross_rollout_deterministic_probe.csv
```

Result:

- `2/2` episodes had `0` releases.
- Final missiles stayed at `4`.
- Target health stayed at `40.0`.
- Open-window event fire probability was nonzero but below event-mode
  selection: mean `0.2736` / `0.2439`, max `0.2827` / `0.2648`.
- A7 quality-window advantage was positive in the deterministic rollouts:
  `0.00234` and `0.00994`, positive fraction `1.0`.
- `policy_event_mode_fire_once_count=0`.

Stochastic probe, `4 x 640` steps:

- `4/4` episodes sampled exactly one authorized release.
- Release steps were `6`, `45`, `3`, and `5`.
- `0` invalid attempts, `0` repeat releases, `0` shot-budget violations.
- No effects or damage events occurred within `640` steps.
- Target health stayed at `40.0`.

Long stochastic probe, `2 x 2400` steps:

- `2/2` episodes sampled exactly one authorized release.
- Release steps were `6` and `43`.
- Termination reason was `combat_timeout` for both episodes.
- `0` invalid attempts, `0` repeat releases, `0` shot-budget violations.
- `0` effects events and `0` damage reports.
- Target health stayed at `40.0`; closest geometric ranges were about
  `1610 m` and `1647 m`.

## Conclusion

Post-X evidence is mixed but not accepted:

- positive: the cross-rollout label repair enters training and early A7 credit
  signs improve;
- positive: stochastic execution now shows clean one-shot discipline in the
  observed probes;
- held: deterministic execution still chooses hold and records `0` releases;
- held: stochastic releases are still near-immediate/prewindow samples, not
  learned quality-window first-shot timing;
- held: even long stochastic episodes produce no effects/damage events after
  the single authorized release.

A7 should remain held. The next investigation should not be another coefficient
sweep. The current breakpoint is that learned event probability and credit can
be positive without becoming deterministic event-mode execution, and sampled
early releases do not lead to an observed missile effects/damage chain.
