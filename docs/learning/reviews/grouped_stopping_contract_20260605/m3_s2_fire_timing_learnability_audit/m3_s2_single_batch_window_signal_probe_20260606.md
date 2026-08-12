# M3-S2 Single-Batch Window Signal Probe - 2026-06-06

Parent: [README.md](README.md).

Status: `root-cause evidence`; the signal exists in observations and frozen
policy features, but the current M3-S2 executable-action contract admits a
global high-signal failure mode.

## Question

The boundary-dedicated short train moved the event logit upward but still did
not produce deterministic release. This probe asks a harder diagnostic
question:

If one fixed forced-hold Stage-1 batch contains both prewindow and quality-window
rows, can the current policy path overfit the correct window split?

## Batch

All probes use the same latest short-train model and collect one forced-hold
episode so the one-shot event support is not consumed:

```text
model = experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
steps = 2400
legal_rows = 1880
prewindow_rows = 840
quality_rows = 1040
accepted_count = 0
launch_min_age = 32
```

The mission observation contains direct separating fields:

| Field | Prewindow | Quality window |
| --- | --- | --- |
| `launch_window_open` | always `0` | always `1` |
| `target_range_m` | mean `13127.2` | mean `19407.0` |
| `target_track_age_s` | mean `2.30833` | mean `1.35962` |

`quality_window_ready`, `legal_open_age_steps`, and `launch_window_age_steps`
remain zero in this batch, so the maintained split currently relies on
`launch_window_open` plus the sidecar age rule rather than those explicit age
fields.

## Probes

### Boundary-Only Overfit

Artifact:

```text
experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json
```

Overrides:

```text
quality_boundary_coef = 100
early_mass_coef = 0
no_event_coef = 0
delay_coef = 0
deadline_coef = 0
contrastive_margin_coef = 0
scope = current
update_steps = 120
learning_rate = 0.001
reset_optimizer_state = true
```

Result:

| Metric | Before | After |
| --- | ---: | ---: |
| `prewindow_boundary_count` | `0` | `840` |
| `quality_boundary_count` | `0` | `1040` |
| `prewindow_logit_mean` | `-5.477109` | `24.141708` |
| `quality_logit_mean` | `-5.477063` | `24.180077` |

This proves the parameter path can cross the deterministic boundary, but the
boundary-only target is not a timing discriminator. It creates all-high
transport.

### Active-Contract Overfit

Artifact:

```text
experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json
```

Same batch, active config loss coefficients, `scope = current`,
`update_steps = 120`, `learning_rate = 0.001`, reset optimizer state.

Result:

| Metric | Before | After |
| --- | ---: | ---: |
| `prewindow_boundary_count` | `0` | `840` |
| `quality_boundary_count` | `0` | `1040` |
| `prewindow_logit_mean` | `-5.477109` | `20.376913` |
| `quality_logit_mean` | `-5.477063` | `20.474621` |

The active contract also falls into all-high transport. The early-mass and
contrastive terms are not sufficient to make the supported batch learn a clean
prewindow/quality split once the quality-boundary anchor dominates.

### Row-Wise BCE On Current Action Path

Artifacts:

```text
experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json
```

Labels are direct and balanced by semantics: legal prewindow rows are `0`,
quality-window rows are `1`.

| Scope | Accuracy | Negative boundary count | Positive boundary count | Verdict |
| --- | ---: | ---: | ---: | --- |
| `current` | `0.553191` | `840 / 840` | `1040 / 1040` | majority-class all-positive |
| `current_plus_features` | `0.553191` | `840 / 840` | `1040 / 1040` | majority-class all-positive |

This does not prove the observations are uninformative. It proves the current
event/action transport path can absorb the direct label as a global bias.

### Frozen Feature Signal

Artifact:

```text
experiments_tmp/m3s2_window_signal_feature_probe_20260606.json
```

A separate linear probe is trained on frozen inputs:

| Input | Accuracy | Negative boundary count | Positive boundary count |
| --- | ---: | ---: | ---: |
| raw mission fields (`launch_window_open`, range, track age) | `1.000000` | `0 / 840` | `1040 / 1040` |
| frozen extractor features | `1.000000` | `0 / 840` | `1040 / 1040` |
| frozen actor latent | `1.000000` | `0 / 840` | `1040 / 1040` |

This localizes the failure away from environment signal and away from the
temporal feature extractor. The actor latent already contains a linearly
separable window signal.

### Frozen-Latent Event Head

Artifact:

```text
experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json
```

With the latent and base action delta frozen, a newly initialized event head
trained with balanced BCE reaches:

```text
accuracy = 0.944149
positive boundary = 1040 / 1040
negative boundary = 105 / 840
```

This is not accepted behavior, but it shows that an isolated calibrated event
head is much closer to the desired contract than the current mixed action-delta
training path.

## Decision

The current failure is no longer best described as "the model cannot see the
fire window." The fixed batch has direct separating mission fields, and frozen
features/actor latent make the split linearly separable.

The failing object is the executable event-logit training contract:

- a quality-boundary anchor alone is existential and positive-only, so the
  easiest solution is raising all legal logits;
- the active grouped loss still admits that all-high solution under strong
  boundary pressure;
- the early-mass penalty is too weak relative to the boundary anchor and can
  become ineffective once hazard saturates;
- `fire_event_logit_delta` is not a standalone stopping head, but a difference
  between transport action coordinates after base `action_net` and
  `hybrid_event_head` adjustment.

The next repair should be a model-contract change, not another training-length
change:

1. train a dedicated stopping/event head against a calibrated signed target;
2. keep prewindow negatives explicit, preferably as balanced BCE or a hard
   cumulative-hazard constraint;
3. convert the selected stopping boundary into an executable low-high-low pulse
   only after the stopping head crosses a deterministic threshold;
4. keep the current transport delta as an adapter output, not the primary
   learning object.
