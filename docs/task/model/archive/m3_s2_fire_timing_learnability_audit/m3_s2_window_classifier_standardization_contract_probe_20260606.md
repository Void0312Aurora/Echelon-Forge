# M3-S2 Window Classifier Standardization Contract Probe - 2026-06-06

## Purpose

This probe follows the post-calibrated-standardization failure where training
logs reported separated replay batches, but the deterministic execution probe
still produced no release. The question was whether the remaining no-fire
behavior came from trajectory mismatch, stochastic-vs-deterministic mismatch,
or a deeper classifier/head contract issue.

## Diagnostic Change

- `tools/diagnostics/fire_timing_fault_localization_probe.py --mode real_update` now supports
  `--collector-action model_event_hold`.
- `model_event_hold` preserves the model action and only forces hybrid action
  index `9` (`fire_once`) to `0.0`, matching the support-preserving collection
  contract more closely than the older hard-coded `hold` action.
- `tools/diagnostics/fire_timing_fault_localization_probe.py --mode chain_breakpoint` now accepts
  `--collector-action` and records
  `window_classifier_fixed_batch_recalibration`.
- The recalibration probe saves and restores the model buffers. It does not
  modify the model artifact.

## Verification

```bash
./.venv/bin/python -m pytest tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Outcome: `5 passed`.

## Trajectory-Mismatch Checks

Model:

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/final_model.zip
```

Hard hold and model-event-hold both fail in the same way:

| Collector | Quality rows | Current quality logit mean | Quality boundary | First breakpoint |
| --- | ---: | ---: | ---: | --- |
| `hold` | `1040` | `-9.902827` | `0 / 1040` | `m3_head_optimization_conditioning` |
| `model_event_hold` | `1080` | `-9.837499` | `0 / 1080` | `m3_head_optimization_conditioning` |
| `model_event_hold --stochastic` | `1080` | `-9.653772` | `0 / 1080` | `m3_head_optimization_conditioning` |

This rules out the earlier hard-hold diagnostic mismatch as the primary
no-fire cause. It also rules out deterministic-vs-stochastic collection as the
primary cause.

## Optimization Budget Check

The same fixed `model_event_hold` batch was also probed with the short online
budget (`64` steps, `fit_lr = 0.003`). A fresh linear head reached
`1078 / 1080` quality-boundary rows, while a direct head trained from the
current M3 head reached `1080 / 1080` quality-boundary rows but retained
`13` prewindow positives. This shows that the frozen actor latent carries the
window signal and the head can move under the online-scale budget, although the
strict one-shot stopping contract is still not fully satisfied.

Artifact:

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_fit64_lr003.json
```

## Standardization Contract Breakpoint

The enhanced chain probe then recomputed the classifier input standardization
buffers on the collected fixed batch, without changing classifier weights.

Artifact:

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_recalibration_r1.json
```

Key fields:

| Metric | Saved buffer | Fixed-batch recalibrated buffer |
| --- | ---: | ---: |
| prewindow logit mean | `-13.132194` | `-3.017594` |
| quality logit mean | `-9.837499` | `2.195754` |
| prewindow boundary | `0 / 800` | `232 / 800` |
| quality boundary | `0 / 1080` | `1053 / 1080` |
| event-mode fire count | `0` | `1285` |
| event-mode fire in quality rows | `0` | `1053` |

Buffer-shift diagnostics:

| Metric | Value |
| --- | ---: |
| saved fixed-batch z mean abs mean | `2.439337` |
| saved fixed-batch z std mean | `0.633167` |
| mean delta L2 | `2.462030` |
| std ratio mean | `0.633167` |
| std ratio min | `0.055305` |
| std ratio max | `3.032915` |

## Interpretation

The strongest current root cause is not lack of a window signal, not the
action adapter, and not the hard-hold diagnostic trajectory. The classifier
weights contain a usable timing signal, but the saved
`m3_window_classifier_input_*` standardization buffers are calibrated to the
latest balanced replay/support distribution rather than to a stable execution
distribution. On the fixed execution-support trajectory, those buffers shift
both prewindow and quality rows far into the negative logit region.

Recalibrating the buffers on the fixed batch immediately restores quality-window
positive logits. This does not make the policy accepted, because it also creates
prewindow positives. It does, however, explain the observed no-fire plateau:
the executable classifier path is being evaluated under an inference-time
normalization contract that is not aligned with the trajectory where it must
fire.

## Consequence

Further coefficient tuning is unlikely to root-fix this. The next repair should
treat standardization as a model-contract problem:

- either remove the mutable population standardizer from the executable
  classifier path and rely on per-sample `LayerNorm` plus the linear head;
- or replace latest-balanced replay calibration with a stable, execution-support
  population normalizer that is frozen before evaluation;
- or train and execute the classifier under the exact same normalized feature
  contract, with post-update diagnostics on the fixed execution-support batch.

The current slice remains held until deterministic execution produces a
single-pulse quality-window release without prewindow pulse consumption.
