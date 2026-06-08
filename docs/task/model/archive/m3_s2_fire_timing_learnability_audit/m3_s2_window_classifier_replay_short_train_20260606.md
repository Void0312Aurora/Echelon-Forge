# M3-S2 Window Classifier Replay Short Train

Status: `2026-06-06` repair tested; classifier online batch metrics improved,
learned fire timing still held.

Parent:

- [M3-S2 Fire-Timing Learnability Audit](README.md)

## Boundary

This note records the follow-up repair after the initial dedicated
`m3_window_classifier_head` integration still failed to learn a stable online
window boundary.

The tested hypothesis was:

- online classifier updates were seeing pure or strongly imbalanced rollout
  chunks;
- a balanced replay buffer should force every auxiliary update to see both
  prewindow negatives and quality-window positives;
- replaying detached actor latents may become stale as PPO changes the actor, so
  observation replay should recompute current actor latents before training the
  classifier.

This slice does not claim behavioral acceptance. It asks whether replay repairs
the classifier-learning breakpoint and whether that transfers to final
deterministic/stochastic learned-policy probes.

## Implementation

- `AdaptiveKLPPO` now supports `m3s2_window_classifier_replay_*` knobs.
- The replay buffer can store either:
  - detached latent rows (`m3s2_window_classifier_replay_storage = "latent"`);
  - observation rows (`"observation"`), which recompute current actor latents at
    every classifier update.
- Active M3-S2 config now uses observation replay:
  - `m3s2_window_classifier_replay_enabled = true`;
  - `m3s2_window_classifier_replay_storage = "observation"`;
  - capacity `8192`, balanced batch size `1024`;
  - classifier update steps `64`, max grad norm `5.0`;
  - `m3_window_classifier_head_lr_scale = 100.0`.
- `air_combat_stage0_process_probe.py` now logs
  `policy_m3_window_classifier_*` per-step and per-episode summary fields.

## Verification

```bash
python -m compileall \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/policy_algo/policies.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/air_combat_stage0_process_probe.py
```

```bash
pytest \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_m3s2_chain_breakpoint_probe.py \
  -q
```

Focused results in this run:

- `tests/hmoe/test_hmoe_ppo_warmup.py`,
  `tests/training/test_air_combat_active_training_entries.py`, and
  `tests/diagnostics/test_m3s2_chain_breakpoint_probe.py`: `46 passed`.
- Broader HMoE/config sweep before observation replay: `84 passed`.

## Short Train A: Latent Replay

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_replay_8k_20260606_r1
```

Artifacts:

- `experiments_tmp/m3s2_window_classifier_replay_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_window_classifier_replay_8k_20260606_r1/m3s2_deterministic_probe_with_classifier.json`
- `experiments_tmp/m3s2_window_classifier_replay_8k_20260606_r1/m3s2_stochastic_probe.json`

Key evidence:

| Step | Replay used | Replay positives | Replay negatives | Positive logit mean | Negative logit mean |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | 0 | 0 | 1024 | 0.00 | -11.7 |
| 3072 | 1 | 900 | 1140 | 2.27 | -1.68 |
| 4096 | 1 | 1800 | 1270 | 2.38 | -1.41 |
| 8192 | 1 | 3800 | 3360 | 2.67 | -2.20 |

But the saved-model deterministic probe still failed:

| Metric | Value |
| --- | ---: |
| `release_count` | 0 |
| `a7_quality_window_step_count` | 1080 |
| `policy_m3_window_classifier_logit_mean` | -7.697 |
| `a7_quality_window_m3_window_classifier_logit_mean` | -7.721 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |

Diagnosis: latent replay separated old replay latents during training, but did
not transfer to the current actor representation at probe time.

## Short Train B: Observation Replay

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_obs_replay_8k_20260606_r1
```

Artifacts:

- `experiments_tmp/m3s2_window_classifier_obs_replay_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_window_classifier_obs_replay_8k_20260606_r1/m3s2_deterministic_probe_with_classifier.json`
- `experiments_tmp/m3s2_window_classifier_obs_replay_8k_20260606_r1/m3s2_stochastic_probe_with_classifier.json`

Key training evidence:

| Step | Replay used | Storage is observation | Positive logit mean | Negative logit mean | Note |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2048 | 0 | 1 | 0.00 | -11.7 | Only negative rows so far. |
| 3072 | 1 | 1 | 1.62 | -2.11 | Balanced replay active. |
| 4096 | 1 | 1 | 1.98 | -2.98 | Current training batch separates. |
| 6144 | 1 | 1 | 1.85 | -2.66 | Separation persists. |
| 8192 | 1 | 1 | 1.60 | -3.06 | Training batch still separates. |

Deterministic probe:

| Metric | Value |
| --- | ---: |
| `release_count` | 0 |
| `a7_quality_window_step_count` | 1080 |
| `policy_m3_window_classifier_logit_mean` | -8.335 |
| `a7_quality_window_m3_window_classifier_logit_mean` | -8.240 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |
| `policy_event_prob_fire_once_max` | 0.000655 |

Stochastic probe:

| Metric | Value |
| --- | ---: |
| `release_count` | 1 |
| `first_release_step` | 48 |
| `a7_quality_window_step_count` | 0 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |
| `a7_prewindow_m3_window_classifier_logit_mean` | -7.876 |

The stochastic release is an early sample before quality-window rows, not a
learned quality-window release.

## Diagnosis

Balanced replay repairs a real local problem: online classifier updates can now
see both classes and the training batch logit means separate.

It does not repair the behavioral policy:

- saved deterministic policies still keep the classifier and final fire event on
  the negative side throughout the actual evaluation trajectory;
- stochastic release remains a low-probability early sample, not a window-timed
  pulse;
- event-delta logs remain negative even when replay-batch classifier logits
  separate during training;
- observation replay reduces but does not eliminate the gap between training
  batch separation and saved-model rollout behavior.

Current localized breakpoint:

```text
sidecar/replay batch can train a classifier boundary
    -> but the saved actor/executable trajectory does not preserve that boundary
    -> fire event probability remains tiny
    -> deterministic policy does not release
```

The next repair should stop treating this as a replay-only issue. The likely
next candidates are:

1. actor trunk drift and PPO overwrite/dilution after classifier updates;
2. competition between legacy M3-S2 event-window/stopping losses and the
   executable classifier adapter;
3. missing current-trajectory classifier supervision at evaluation-like support;
4. event/action distribution calibration, because `fire_once` remains tiny even
   when auxiliary batch metrics look separated.
