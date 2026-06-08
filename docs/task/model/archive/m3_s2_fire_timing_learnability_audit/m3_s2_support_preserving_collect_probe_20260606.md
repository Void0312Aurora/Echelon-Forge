# M3-S2 Support-Preserving Collect Probe - 2026-06-06

Parent: [README.md](README.md).

Status: `partial repair evidence`; support collapse is repaired in training
collection, but learned deterministic fire timing remains held.

## Question

If stochastic rollout sampling can consume the one-shot event before the
quality window, can the learner keep the M3-S2 quality-window rows alive by
forcing hold during collection while still training the executable
`fire_once` event logits?

This probe tests a training contract change, not a runtime C2/ROE change. The
support-preserving path rewrites training-rollout actions only. Evaluation
probes still use the learned policy without the shield.

## Implementation

Code and config:

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - adds `early_survival_coef`, which penalizes direct prewindow survival loss
    in addition to the existing early-mass budget;
  - retains zero default behavior for existing M3-S1 callers.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - adds M3-S2 support-preserving collection knobs;
  - computes legal-open and quality-ready masks from the same A6 launch-window
    observation path used by the event-window sidecar;
  - forces training-rollout action index `9` (`fire_once`) to `0.0` under the
    shield and recomputes log-probability under the current distribution;
  - logs hold/candidate/quality counts as first-class `m3s2/*` scalars.
- `python/rl/support/nonfinite_probe.py`
  - mirrors the same support-preserving action rewrite and logging while the
    non-finite probe monkey patch is installed.
- Active config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
  - `m3s2_event_window_early_survival_coef = 8.0`
  - `m3s2_event_window_support_preserving_collect_enabled = true`
  - `m3s2_event_window_support_preserving_hold_quality_enabled = true`

The first iteration held only before the quality window. The accepted test run
below holds through the full legal-open collection window so stochastic samples
cannot erase the quality-window rows during training.

## Validation

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/hmoe/test_m3s1_grouped_stopping.py \
  tests/hmoe/test_hmoe_ppo_warmup.py
```

Outcome: pass.

```bash
pytest tests/hmoe/test_m3s1_grouped_stopping.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/training/test_air_combat_active_training_entries.py -q
```

Outcomes:

- `10 passed`
- `24 passed`
- `16 passed`

Focused coverage includes:

- early-survival penalty punishes high prewindow mass;
- support-preserving masks hold until quality readiness and, when enabled,
  continue holding during the full legal-open window;
- the active M3-S2 config carries the new support-preserving knobs.

## Short Training

Primary artifact:

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/
```

Training-support comparison:

| Run | Shield | Accepted events | Early-prefix groups | Window groups | Active groups | Closed rows | Boundary crosses |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `m3s2_event_window_8k_20260605_r2` | none | max `3`, final `0` | max `3` | max `1`, final `0` | final `0` | final `1024` | `0` |
| `m3s2_support_preserve_8k_20260606_r1` | pre-quality | max `2`, final `0` | max `1` | max `4`, final `0` | final `0` | final `1024` | `0` |
| `m3s2_support_preserve_8k_20260606_r2` | whole legal-open | `0` throughout | `0` throughout | max `4`, final `0` | min `4`, final `4` | max `4`, final `0` | `0` |

The whole-window shield changes the failing training-support metric:

- old event-window training ended with `grouped_active_group_count = 0` and
  `closed_mask_row_count = 1024`;
- whole-window support-preserving training ended with
  `grouped_active_group_count = 4`, `grouped_active_row_count = 1024`, and
  `closed_mask_row_count = 0`;
- `accepted_event_count = 0` throughout the shielded run, so collection no
  longer burns the one-shot before the learner observes supported rows.

The final update has `window_group_count = 0` because that rollout segment had
legal-open no-window support, not because the state machine closed the fire mask
after an early sample.

## Learned-Policy Probes

Deterministic probe:

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_deterministic_probe.json
```

| Metric | Value |
| --- | ---: |
| `release_count` | `0` |
| `fire_mask_open_step_count` | `1880` |
| `a7_prewindow_step_count` | `800` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.003296760` |
| `policy_event_mode_fire_once_count` | `0` |
| `a7_prewindow_event_fire_prob_mean` | `0.003266293` |
| `a7_prewindow_event_fire_prob_cum` | `0.927001125` |
| `a7_quality_window_event_fire_prob_mean` | `0.003259922` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

Stochastic probe:

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_stochastic_probe.json
```

| Metric | Value |
| --- | ---: |
| `release_count` | `1` |
| `first_release_step` | `61` |
| `a7_prewindow_step_count` before release | `56` |
| `a7_quality_window_step_count` before release | `0` |
| `a7_prewindow_event_fire_prob_cum` | `0.166411451` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

The evaluation probes therefore separate two issues:

- support-preserving collection fixes the training-data support collapse;
- the learned policy still does not create a deterministic `fire_once` pulse,
  and its stochastic event probability is still high enough to sample early.

## Decision

This repair is accepted only as a diagnostic/training-support repair. It proves
that the previous support-collapse mechanism was real and can be blocked during
collection.

It is not a behavioral fire-timing solution:

- deterministic evaluation still records `0` releases with `1080`
  quality-window steps;
- `boundary_cross_count` remains `0` throughout training;
- prewindow cumulative event risk remains orders of magnitude above the
  desired `0.02` scale;
- stochastic evaluation can still fire before the quality window.

The remaining root cause is now narrower: actor/event training can preserve
rows and reach executable logits, but it still fails to transport the learned
window target into a deterministic low-high-low event pulse. The next slice
should focus on an event-to-pulse adapter or a stronger signed event-logit
actor objective with explicit prewindow survival and quality-window crossing
targets. M2 memory should remain secondary unless it owns that adapter.
