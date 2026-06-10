# M3-S2 Window Classifier Calibrated Standardization Short Train

Date: 2026-06-06

Status: negative integration evidence; behavior still held.

## Question

The previous observation-replay classifier run showed a split between local
training-batch success and saved-policy behavior: replay batches separated
positive and negative logits, but deterministic saved-model probes still did
not fire. This slice tested whether the failure came from unstable classifier
input standardization being refreshed from a random replay batch on every
auxiliary step.

## Change Under Test

- Added a deterministic latest-balanced replay calibration batch for M3-S2
  window classifier standardization.
- Refreshed classifier input standardization only once at the start of each
  auxiliary update instead of every separate update step.
- Bounded the calibration batch by `m3s2_window_classifier_replay_batch_size`.
  The first full-capacity attempt pushed several thousand observation rows
  through the temporal transformer and failed with CUDA
  `invalid configuration argument`.

## Evidence

Focused tests:

```text
./.venv/bin/python -m pytest \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_window_classifier_replay_calibration_is_latest_balanced_population \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_window_classifier_replay_balances_single_class_rollouts -q

2 passed
```

Full 8k run:

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/
```

Training still reported local replay-batch separation near the end:

- `m3s2/window_classifier_positive_logit_mean ~= 2.25`
- `m3s2/window_classifier_negative_logit_mean ~= -3.06`
- `m3s2/window_classifier_accuracy ~= 0.921`

But the fixed-trajectory chain probe failed for both the last checkpoint and
the final saved model:

- `checkpoints/model_8192_steps.zip`
  - current quality logit mean: `-9.495816`
  - current quality boundary count: `0 / 1040`
  - fresh standardized linear probe: pass, `1040 / 1040` quality and
    `0 / 840` prewindow
  - verdict first breakpoint: `m3_head_optimization_conditioning`
- `final_model.zip`
  - current quality logit mean: `-9.902827`
  - current quality boundary count: `0 / 1040`
  - fresh standardized linear probe: pass, `1040 / 1040` quality and
    `0 / 840` prewindow
  - verdict first breakpoint: `m3_head_optimization_conditioning`

Deterministic environment probe for `final_model.zip`:

- `release_count = 0`
- `a7_quality_window_step_count = 1080`
- `a7_quality_window_m3_window_classifier_logit_mean = -9.852545`
- `policy_event_mode_fire_once_count = 0`

## Interpretation

Calibrating standardization deterministically removes one source of random
coordinate drift, but it does not repair the learned executable boundary.
The classifier can still fit the fixed hold-trajectory latent quickly when
trained directly, so the representation and adapter remain sufficient.

The surviving failure is the online optimization contract: the auxiliary
window classifier learns the sampled replay batch but does not preserve the
same boundary on the deterministic executable trajectory. This is no longer
well explained by missing labels, missing observation signal, C2/ROE masks, or
action adapter transport.

Follow-up localization tightened this statement: the saved
`m3_window_classifier_input_mean/std` buffers themselves are a breakpoint. On
the fixed `model_event_hold` trajectory, saved buffers keep quality rows at
`0 / 1080` boundary crossings; recomputing only those buffers on the fixed
batch raises quality crossings to `1053 / 1080` without changing classifier
weights. See
[m3_s2_window_classifier_standardization_contract_probe_20260606.md](m3_s2_window_classifier_standardization_contract_probe_20260606.md).

## Consequence

Further coefficient tuning on the current online auxiliary head is unlikely to
be the right next step. The next model-contract slice should first repair the
classifier standardization contract: remove mutable population standardization
from the executable path, or calibrate and freeze it on the same
execution-support distribution used by deterministic evaluation.
