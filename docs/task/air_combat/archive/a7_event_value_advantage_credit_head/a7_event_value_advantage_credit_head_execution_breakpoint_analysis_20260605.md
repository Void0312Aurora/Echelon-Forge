# A7 Execution Breakpoint Analysis

Status: `2026-06-05` completed as structural root-cause evidence; held
outcome.

Parent: [README.md](README.md).

## Purpose

`A7-EVC-Y` proved that cross-rollout first-event credit state reaches training,
but the learned policy still holds deterministically and samples early when
stochastic. This note isolates the remaining breakpoint by comparing the same
post-X final model under three fixed-batch probes:

- label reconstruction on a no-release `hold` trajectory;
- offline credit-head-only fitting;
- offline event-logit fitting with either the current A7 delta-align objective
  or direct label supervision.

## Fixed Batch

Model:

```text
experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip
```

Scenario/config:

```text
scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
```

The hold-collector fixed batch used `1 x 2400` steps, seed `7`.

Label reconstruction:

| Metric | Value |
| --- | ---: |
| steps | `2400` |
| fire-open steps | `1880` |
| launch-open steps | `1040` |
| accepted releases | `0` |
| active labels | `1880` |
| `prewindow` negatives | `840` |
| `legal_open_quality` positives | `1040` |
| mass-capped positive weight | `1.0` |
| mass-capped negative weight | `1.0` |

This excludes missing labels as the current dominant fault. The post-X labels
are present, balanced after per-window mass caps, and aligned with the intended
prewindow/quality split.

## Current Policy Shape

On the same fixed batch, the learned event head is nearly flat:

| Slice | Event delta mean | Fire probability mean | Credit advantage mean | Argmax fire fraction |
| --- | ---: | ---: | ---: | ---: |
| active | `-0.9792` | `0.2731` | `0.00415` | `0.0` |
| `legal_open_quality` | `-0.9774` | `0.2734` | `0.00421` | `0.0` |
| `prewindow` | `-0.9813` | `0.2726` | `0.00407` | `0.0` |

The policy did not learn "hold before the quality window, fire in the quality
window". It learned a small positive credit advantage everywhere, while the
actual event-logit delta stayed below zero everywhere.

## Offline Credit Fit

`tools/diagnostics/a7_credit_head_offline_fit_probe.py` was run with the same
model/config, hold collector, `1 x 2400` steps, and `300` credit-head-only fit
steps.

Initial credit advantage:

| Slice | Advantage mean | Positive fraction |
| --- | ---: | ---: |
| `legal_open_quality` | `0.00421` | `1.0` |
| `prewindow` | `0.00407` | `0.925` |

After fitting only `hybrid_event_credit_head`:

| Slice | Advantage mean | Positive fraction |
| --- | ---: | ---: |
| `legal_open_quality` | `0.16646` | `1.0` |
| `prewindow` | `-0.21944` | `0.527` |

The credit head can move in the right direction on the fixed batch. The
remaining fault is therefore not simply "labels are absent" or "the credit head
cannot receive gradients".

## Event-Logit Fit

Two event-head-only objectives were compared on the same fixed batch.

Current A7 delta-align objective:

```text
target_delta = (Q_fire_once - Q_hold).detach()
```

After `300` steps training only `hybrid_event_head`:

| Slice | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `0.00758` | `0.50190` | `0.996` |
| `prewindow` | `0.00403` | `0.50101` | `0.585` |

This objective does not encode a robust signed decision boundary. When it works,
it pulls both positive and negative windows toward the small credit advantage
near zero. Deterministic selection then becomes a threshold accident; prewindow
rows also leak into `fire_once`.

Direct label BCE on event logits, training only `hybrid_event_head`:

| Slice | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `0.18575` | `0.54630` | `1.0` |
| `prewindow` | `0.02402` | `0.50617` | `0.643` |

Direct labels are stronger, but the frozen actor latent plus event head alone is
still not enough to suppress the bimodal negative set.

Direct label BCE on event logits, training `hybrid_event_head` plus
`mlp_extractor.policy_net`:

| Slice | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `1.25132` | `0.74852` | `0.891` |
| `prewindow` | `-9.43967` | `0.08289` | `0.017` |

This proves the model class can separate the timing windows when the actor
representation receives a direct signed event-logit training signal.

## Conclusion

The remaining root cause is the A7 value-to-policy execution contract, not
missile damage, A3/A5 legality, label starvation, or basic model capacity.

The specific failing link is:

```text
labels -> credit head -> tiny detached advantage -> smooth-L1 event-logit delta
```

That link is too weak and under-specified:

- `compute_first_event_credit_loss()` aligns event-logit delta to the detached
  credit advantage, not to a calibrated label target or margin.
- In the learned post-X model, the credit advantage is only about `0.004` on
  both prewindow and quality rows, so the event-logit target is effectively
  near zero.
- `a7_event_credit_delta_align_positive_only=true` removes negative-label
  pressure once the credit head goes negative; it protects shadow rows, but it
  also means ordinary prewindow negatives do not reliably push event logits
  below zero.
- The separate credit-head update uses detached actor latents, so it can improve
  the credit head without teaching the actor representation the timing
  discriminant needed by deterministic event-mode selection.

If the current alignment were made strong enough, it would tend to produce
near-threshold firing in both prewindow and quality rows. If it remains weak,
deterministic mode stays `hold`. Both outcomes match the observed failure modes.

## Next Contract Boundary

The next slice should not be another coefficient sweep. It should define a new
event-policy training contract with these properties:

- direct signed event-logit targets or margins for ordinary legal-open quality
  positives and prewindow negatives;
- a bounded actor-representation update lane for the event timing discriminant,
  instead of credit-head-only detached-latent learning;
- A3/A5 masks remain authoritative, with no runtime legality weakening;
- the credit head remains useful as value/diagnostic support, but not as the
  sole teacher for deterministic event-mode crossing.

A good candidate next subproject is an A7 follow-on contract for calibrated
event-logit margin distillation / actor-timing representation update.
