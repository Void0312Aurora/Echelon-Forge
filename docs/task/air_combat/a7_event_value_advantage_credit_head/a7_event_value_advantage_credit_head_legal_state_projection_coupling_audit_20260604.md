# A7 Legal-State Projection And Coupling Audit

Status: `2026-06-04` `A7-EVC-K` structural audit pass; behavior remains held.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md).

## Question

`A7-EVC-J` fixed the confirmed label-censoring bug: early accepted stochastic
episodes can now expose later `shadow_quality` positives. The repaired short
run still does not learn accepted timing:

- deterministic probe: `0` releases, `1880` open-mask steps, quality-window
  A7 advantage mean about `-0.902`;
- stochastic probe: authorized one-shot releases at steps `4`, `43`, and `2`;
- TensorBoard: `a7/event_credit_target_positive_frac` rises to about `0.60`,
  but `a7/event_credit_advantage_mean` falls to about `-0.96`.

The K question is therefore: why do repaired positives not move legal-open
quality states toward positive `fire_once` advantage?

## Evidence

### Label Mass

The repaired stochastic probe must be reconstructed with the pre-step
`policy_event_mask_fire_once` / `event_action_mask_fire_once`, matching
`AdaptiveKLPPO.collect_rollouts()` behavior. A post-step `fire_mask` field is
already closed on the accepted row and is not equivalent to the training label
surface.

Using the repaired r1 stochastic CSV and A7 active config:

| Reconstruction | Active rows | Positive rows | Negative rows | Raw positive mass | Raw negative mass | Capped positive mass | Capped negative mass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| post-step `fire_mask` | `3` | `0` | `3` | `0.0` | `1.2` | `0.0` | `1.2` |
| pre-step event mask | `3286` | `3280` | `6` | `3280.0` | `4.2` | `3.0` | `3.0` |

The pre-step reconstruction exposes the J repair correctly:

| Source | Rows | Positive rows | Raw mass | Capped mass | Coupling |
| --- | ---: | ---: | ---: | ---: | --- |
| `prewindow` | `3` | `0` | `1.2` | `0.730159` | value + delta alignment |
| `early_accepted` | `3` | `0` | `3.0` | `2.269841` | value + delta alignment |
| `shadow_quality` | `3280` | `3280` | `3280.0` | `3.0` | value-only; excluded from delta alignment |

For the repaired deterministic probe:

| Source | Rows | Positive rows | Raw mass | Capped mass | Coupling |
| --- | ---: | ---: | ---: | ---: | --- |
| `prewindow` | `800` | `0` | `320.0` | `1.0` | value + delta alignment |
| `deadline` | `1080` | `1080` | `1080.0` | `1.0` | value + delta alignment |

This rules out "no positives" as the current blocker, but it also shows that
row counts are misleading: thousands of shadow positives become a total capped
positive mass of `3.0`.

### Policy-State Probe

The repaired deterministic probe has real legal-open quality states, but the
credit sign is still wrong:

| State group | Count | Fire probability mean | Event advantage mean |
| --- | ---: | ---: | ---: |
| legal-open pre-quality | `800` | `0.2549` | `-0.9021` |
| legal-open quality | `1080` | `0.2553` | `-0.9018` |

The repaired stochastic probe mostly produces closed-mask shadow states after
early release:

| State group | Count | Fire mask open | Event advantage mean |
| --- | ---: | ---: | ---: |
| pre-accept open rows | `6` | `6` | about `-0.92` |
| post-release track-quality shadow rows | `3280` | `0` | about `-0.90` |

The positive repaired evidence therefore lives mostly on `FiredAssess` /
closed-mask observations, not on legal-open quality observations where the
policy must actually choose `fire_once`.

### Coupling Path

The current implementation deliberately excludes `shadow_quality` rows from
delta alignment:

- value loss trains `Q_fire_once - Q_hold` on all active rows after mass caps;
- delta alignment trains event logits only where `source != shadow_quality`;
- this prevents illegal post-release closed-mask rows from directly teaching
  legal fire actions, which is correct for A3/A5 legality;
- but it also means most repaired positives cannot directly push the event
  logits toward `fire_once`.

The remaining direct policy signal in early stochastic trajectories is therefore
negative: `prewindow` and `early_accepted` rows are delta-aligned, while
`shadow_quality` rows are value-only.

## Diagnosis

The post-J blocker is not label censoring. It is projection and coupling.

`A7-EVC-J` creates counterfactual evidence in the target stream, but that
evidence is attached to post-release closed-mask states. The active event policy
needs a positive signal at legal-open quality states. The current A7 path has no
mechanism that projects the shadow evidence onto that legal-open decision
surface:

```text
early stochastic fire
  -> environment enters FiredAssess
  -> later quality facts exist
  -> J labels those later rows as shadow_quality positive
  -> delta alignment skips them because fire is illegal there
  -> event policy sees mostly early negative delta targets
  -> legal-open quality states remain negative
```

This explains the observed scalar pattern:

- `target_positive_frac` increases because many shadow rows are now active;
- `event_credit_delta_align_loss` becomes tiny because shadow positives are not
  aligned and non-shadow rows are already negative;
- `event_credit_advantage_mean` stays negative because value learning on
  closed-mask shadow states does not force legal-open quality states positive.

## Ruled-Out Primary Causes

| Candidate | Result |
| --- | --- |
| A3/A5 runtime legality | Not primary. The stochastic repaired probe keeps authorized one-shot discipline and zero unauthorized/repeat/budget violations. |
| Missing positives after J | Not primary. Pre-step reconstruction exposes thousands of `shadow_quality` positive rows. |
| HMoE redesign | Not promoted. The failure is visible at target projection / value-to-policy coupling before a hierarchy-attributable diagnosis is needed. |
| Coefficient-only tuning | Not a root fix. It can increase value loss pressure but does not create a legal-open projection target or safe positive delta alignment path. |

## Next Contract Direction

The next bounded slice should be `A7-EVC-L Legal-State Projection Contract`.
It should define one of these mechanisms before another learned-policy run:

1. Projected-observation distillation:
   create a counterfactual legal-open observation for `shadow_quality` rows
   using the later contact/geometry facts but legal first-shot C2/ROE mask
   semantics, then train positive value and policy coupling on that projected
   observation.

2. Sequence continuation value:
   separate "hold now reaches future quality" from "fire now is good" by adding
   a continuation/event-time value target. Use it to train pre-window hold
   preference and legal quality fire preference without treating closed-mask
   rows as legal actions.

3. Split-head contract:
   keep `shadow_quality` as a value-only survival/opportunity signal, but add a
   legal-open fire-advantage head or distillation anchor that receives positive
   targets only on legal-open projected states.

Immediate non-goals:

- do not simply enable delta alignment on closed-mask `shadow_quality` rows;
- do not weaken A3/A5 masks or `FiredAssess` suppression;
- do not launch another 32k training wave before the projection contract;
- do not promote HMoE redesign or M2 release from this evidence.

## Worker Packet

```md
status: pass; behavior held
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md
commands/outcomes:
- repaired r1 CSV label-mass reconstruction -> shadow positives restored but value-only after caps
- repaired r1 probe state summary -> legal-open quality advantage remains negative
- TensorBoard scalar read -> positive fraction rises while advantage remains negative
remaining paths:
- `A7-EVC-L Legal-State Projection Contract`
behavior risks:
- coefficient-only training can keep reinforcing the same projection gap
- enabling delta alignment on closed-mask rows would violate the A3/A5 boundary
integration notes:
- `experiments_tmp` remains evidence only and must not be staged
- HMoE gap remains a watch item, not the active A7 blocker
```
