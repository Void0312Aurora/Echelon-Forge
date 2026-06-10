# M3-S2 Window Classifier Execution-Support Short Train - 2026-06-06

## Purpose

This slice tested the hypothesis that the M3-S2 window-classifier no-fire
plateau came from two implementation contracts:

- PPO actor losses were allowed to backpropagate through the executable
  window-classifier event adapter.
- Window-classifier logs reported the last pre-step auxiliary loss, not the
  post-update saved head.

## Changes

- `HierarchicalMoEExecutionPolicy` now exposes
  `m3_window_classifier_event_adapter_detach` and the active M3-S2 config sets
  it to `true`.
- The executable adapter still uses `m3_window_classifier_head` to set the
  hold/fire logit difference, but the PPO actor/action-log-prob path no longer
  trains that supervised contract head back toward rollout hold actions.
- `_m3s2_window_classifier_auxiliary_update()` now evaluates post-step
  classifier loss, keeps the best selected classifier parameters on the
  auxiliary batch, restores them at the end, and reports the restored
  post-update metrics.

## Focused Verification

```bash
./.venv/bin/python -m py_compile \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/policy_algo/policies.py

./.venv/bin/python -m pytest \
  tests/policy/test_execution_policy_surface.py -k "m3_window_classifier" -q

./.venv/bin/python -m pytest \
  tests/training/test_air_combat_training_entry_contracts.py -k m3s2 -q
```

Outcome:

- `4 passed, 39 deselected`
- `1 passed, 15 deselected`

## Short-Train Evidence

Run:

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1
```

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_best_restore_8k_20260606_r1
```

Selected final training metrics:

| Metric | Value |
| --- | ---: |
| `m3s2/window_classifier_positive_logit_mean` | `1.39` |
| `m3s2/window_classifier_negative_logit_mean` | `-2.82` |
| `m3s2/window_classifier_accuracy` | `0.842` |
| `m3s2/window_classifier_replay_used` | `1` |
| `m3s2/boundary_cross_count` | `0` |
| `m3s2/event_logit_delta_mean` | `-1.22` |

Because the log is now post-restore, this is reliable evidence that the
classifier can separate the sampled replay/training support at the saved update
point.

## Deterministic Probe

Artifact:

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1/m3s2_deterministic_probe.json
```

Key result:

| Metric | Value |
| --- | ---: |
| `release_count` | `0` |
| `final_missiles` | `4` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_mode_fire_once_count` | `0` |
| `a7_quality_window_m3_window_classifier_logit_mean` | `-6.336187` |
| `a7_quality_window_m3_window_classifier_boundary_cross_count` | `0` |
| `a7_prewindow_m3_window_classifier_logit_mean` | `-6.782465` |

The policy still does not fire in deterministic execution.

## Chain Probe

Artifact:

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1/m3s2_chain_breakpoint_probe_final_model_event_hold.json
```

Fixed `model_event_hold` results:

| Head | Prewindow boundary | Quality boundary | Quality logit mean | Pass |
| --- | ---: | ---: | ---: | --- |
| current saved head | `0 / 800` | `0 / 1080` | `-6.339776` | no |
| direct trained raw head | `41 / 800` | `1080 / 1080` | `1.576526` | no, early prewindow positives |
| fresh standardized latent head | `0 / 800` | `1080 / 1080` | `9.599181` | yes |

Verdict remains:

```text
first_breakpoint = m3_head_optimization_conditioning
```

## Interpretation

The actor-gradient isolation and post-update restore are valid engineering
repairs, but they do not root-fix behavior. They remove two false explanations:

- the saved head is no longer merely an unlogged final-step overshoot;
- the actor loss is no longer directly training the classifier adapter back
  toward hold.

The remaining failure is a training-support contract mismatch. The classifier
separates the replay/training support seen by the auxiliary update, but the
same saved head is all-negative on the deterministic `model_event_hold`
execution support where it must fire. A fresh standardized linear head on that
exact execution latent separates perfectly, so the state signal and adapter
remain available.

## Consequence

Further coefficient tuning is not the next root fix. The next implementation
slice should train or calibrate the window classifier on the execution-support
distribution itself, or add an explicit fixed-support auxiliary calibration
gate. Until deterministic execution produces a single quality-window pulse,
M3-S2 behavior remains held.
