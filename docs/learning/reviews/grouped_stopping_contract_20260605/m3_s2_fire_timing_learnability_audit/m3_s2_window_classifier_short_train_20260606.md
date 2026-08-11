# M3-S2 Window Classifier Short Train

Status: `2026-06-06` implemented integration slice; behavioral fire timing remains held.

Parent:

- [M3-S2 Fire-Timing Learnability Audit](README.md)

## Boundary

This slice implements the user-facing modeling decision that air-combat fire
timing should first learn to identify a high-quality launch window, then convert
that window decision into an executable one-shot fire pulse.

It does not claim learned fire timing success. The acceptance question here is:
can an explicit window classifier be wired, trained, and observed separately
from the older cumulative-hazard / stopping-head objective?

## Implementation

- `HierarchicalMoEExecutionPolicy` now supports a dedicated
  `m3_window_classifier_head` with optional LayerNorm and an independent
  optimizer lane.
- `hybrid_event_use_m3_window_classifier_head` routes the executable hybrid
  hold/fire logit delta through the classifier output. If both classifier and
  stopping-head adapters are enabled, the classifier adapter is the active
  executable path.
- `AdaptiveKLPPO` now supports `m3s2_window_classifier_*` knobs. The auxiliary
  objective uses existing grouped sidecar rows:
  - positive rows: legal supported `quality_mask = true`;
  - negative rows: legal supported rows outside the quality window.
- The classifier loss is a balanced BCE plus optional negative-logit ceiling and
  positive-logit floor terms.
- The nonfinite probe training loop was updated so active runs with
  `diagnostics.nonfinite_probe = true` execute and log the classifier update.

## Verification

```bash
python -m compileall -q \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

```bash
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  >/dev/null
```

```bash
python -m pytest \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  -q
```

Result: `83 passed in 33.08s`.

Focused classifier acceptance:

- Policy tests confirm the classifier head is disabled by default, has its own
  optimizer lane when enabled, and can override executable fire-event logits.
- PPO warmup tests confirm one grouped sidecar with quality mask
  `(False, False, True, True)` can train the classifier so positive logits exceed
  negative logits while only classifier parameters change.

## Short Train

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_8k_20260606_r1
```

Artifacts:

- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_stochastic_probe.json`

Key training observations:

| Step | Positive rows | Negative rows | Positive logit mean | Negative logit mean | Classifier note |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2048 | 0 | 1024 | 0.0 | -0.266 | No quality-window positives in that rollout batch. |
| 3072 | 900 | 124 | -0.0909 | -0.0991 | Positives appear, but separation is tiny. |
| 4096 | 900 | 124 | 0.0274 | 0.0146 | Accuracy reflects class imbalance more than boundary quality. |
| 5120 | 900 | 124 | 0.0119 | 0.0100 | Boundary remains near-random. |
| 6144 | 900 | 124 | 0.00854 | 0.00656 | Boundary remains near-random. |
| 7168 | 200 | 824 | 0.0239 | -0.0124 | More negatives appear, but separation remains weak. |
| 8192 | 0 | 1024 | 0.0 | -0.387 | Final batch again has no positives. |

## Learned-Policy Probes

Deterministic probe:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_window_classifier_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max_steps 2400 \
  --json_out experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_deterministic_probe.json
```

Stochastic probe uses the same command with `--stochastic`.

| Probe | Release count | First release | Quality-window rows | Event fire prob mean in open mask | Final missiles |
| --- | ---: | ---: | ---: | ---: | ---: |
| deterministic | 0 | n/a | 1080 | 0.262445 | 4 |
| stochastic | 1 | 5 | 0 | 0.253977 | 3 |

## Diagnosis

The window classifier slice is wired and trainable in the focused synthetic
sidecar test, but the active 8k Stage-1 run still fails behaviorally:

- deterministic policy never releases, despite `1080` quality-window rows;
- stochastic policy releases early at step `5`, before any quality-window row;
- online classifier logits do not form a stable prewindow-vs-quality boundary;
- rollout batches alternate between no-positive windows and highly imbalanced
  positive-heavy windows.

This narrows the current root: the failure is no longer simply "the model has no
separate window concept." The next diagnostic should audit the classifier
training distribution and update target directly:

1. whether sidecar batches should rebalance at the group/window level rather
   than per-row;
2. whether the classifier should be trained on an offline forced-hold window
   dataset before being attached to executable action;
3. whether the active process probe should log `m3_window_classifier` logits
   directly, rather than inferring them through the event adapter.
