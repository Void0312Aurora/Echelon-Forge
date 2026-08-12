# A6 Launch-Window Label Density Imbalance

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/launch_window_label_imbalance/README.md`
Owner: `learning/air-combat-training`
Last verified: `2026-08-08`

Status: `2026-06-04` open; deterministic `fire_once` argmax does not cross
under L contract despite `34.6%` open-window event probability. This issue is
now routed into A7 as a balancing requirement, not as a standalone L-tuning
repair.

First observed: `2026-06-04`, during A6-EVT-M short learned-policy probe.

Issue class: positive/negative training-label density imbalance under a
gated launch-window contract.

## Summary

A6-EVT-K (event-head optimization lane) proved the masked `hold/fire_once`
event decision can cross deterministic argmax. Its learned release collapsed
to near-immediate authorization/contact (step 2).

A6-EVT-L added a launch-window timing contract that gates positives through a
quality window and converts early accepted releases into negative labels.
A6-EVT-M ran the short learned-policy probe:

- deterministic: `0` requests, `0` releases, open-window event probability
  `34.6% / 35.0%`;
- stochastic: `3/3` authorized single releases at steps `7`, `43`, `4`.

The L contract suppressed deterministic early fire, but also pushed
deterministic argmax below the crossing threshold. This is a label density
imbalance, not an update-strength or gradient-routing problem — K already
proved those are functional.

## Current Evidence

A6-EVT-M probe against the L active config
`air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json`:

| Signal | Value | Interpretation |
| --- | --- | --- |
| Deterministic requests | `0` | Masked argmax never selects `fire_once`. |
| Open-window fire probability | `34.6% / 35.0%` | Some states learned high probability, but expected delta is negative. |
| Stochastic requests | `3/3` authorized, steps `7/43/4` | Sampling overcomes moderate probability; one-shot discipline holds. |
| Violation / repeat / budget | `0` across all probes | A3/A5 legality is intact. |

Mid-training diagnostics at ~30720 timesteps:

| Signal | Value |
| --- | --- |
| `event_logit_delta_mean_open` | `-2.19` |
| `event_fire_prob_mean_open` | `0.10` |
| `pi_event_mode_fire_frac` | `0` |

Relevant L config parameters:

| Parameter | Value | Effect |
| --- | --- | --- |
| `a6_first_event_curriculum_coef` | `0.0` | No guided positives during training. |
| `a6_first_event_deadline_weight` | `1.0` | Positive only after ≥64 quality-window steps. |
| `a6_first_event_deadline_min_window_age_steps` | `64` | High bar; many episodes end before reaching this. |
| `a6_first_event_launch_window_prewindow_hold_weight` | `0.3` | Negative label on every pre-window step. |
| `a6_first_event_launch_window_early_accept_weight` | `1.0` | Full penalty on early accepted fire. |
| `a6_first_event_launch_window_min_window_age_steps` | `32` | Quality window opens late. |

## Root Cause

The L contract creates a severe positive/negative label density skew:

1. **Quality window rarely opens**: the range gate (`8000–30000 m`),
   track-age gate (`≤5 s`), and minimum window age (`32` steps) combine to
   make the quality window narrow.
2. **Deadline positives are scarce**: they require `64` steps inside an
   already-rare quality window. Many episodes conclude before this threshold.
3. **Pre-window negatives are dense**: `prewindow_hold_weight=0.3` fires on
   every legal-open step before the quality window.
4. **Curriculum is disabled**: `curriculum_coef=0.0` means no bootstrap
   positives to guide early learning.
5. **Net gradient pulls fire probability downward**: the expected logit delta
   stays negative (`-2.19` at ~30720 steps), so deterministic argmax remains
   on `hold`.

The positive/negative label ratio in a typical rollout is heavily skewed
toward negatives, and the loss is a simple BCE with per-sample weights — it
has no mechanism to compensate for class imbalance.

## Comparison Against A6-EVT-K

| Dimension | A6-EVT-K (no L) | A6-EVT-M (with L) |
| --- | --- | --- |
| Deterministic requests | 1 (step 2) | 0 |
| Open-window fire prob | ~67.9% | 34.6% / 35.0% |
| `event_logit_delta_mean_open` | +0.747 | -2.19 |
| `pi_event_mode_fire_frac` | 1 | 0 |
| Early-fire suppression | None | Effective |
| Timing quality | Immediate release | Fire suppressed entirely |

L solved K's early-fire problem but overshot: the negative signal is strong
enough to prevent any deterministic fire, not just early fire.

## Impact

- **Blocks A6 acceptance**: the acceptance gate requires deterministic
  `fire_once` probability/mode to move materially from the A5 baseline and
  either execute an authorized first release or record a precise held blocker.
- **Stochastic-only behavior is not acceptance**: stochastic probing preserves
  one-shot discipline but does not prove deterministic learned-policy
  behavior.
- **Not a reward-only legality regression**: A3/A5 masks remain authoritative.
  The fix should adjust label semantics, not weaken runtime constraints.

## Non-Claims

- This is not evidence that the event-head optimization lane (K) is broken.
- This is not evidence that the launch-window contract (L) is the wrong
  approach — it correctly identified the early-fire problem.
- This is not a vote for M2 release or sequence-native PPO.
- This is not a claim that the current range gate, track-age gate, or window
  age thresholds are wrong in absolute terms — they are bootstrap settings,
  not doctrine.

## Hypotheses

1. **Primary**: positive labels (deadline, curriculum) are too sparse
   relative to negative labels (pre-window hold, early-accepted), so net
   gradient suppresses fire probability below deterministic argmax.
2. **Secondary**: disabling curriculum (`coef=0.0`) removes the only
   early-training bridge that could establish a fire baseline before the
   quality window tightens.
3. **Secondary**: the quality-window gate (range + track age + window age)
   may be too restrictive for the current S1 non-maneuvering-target scenario.
4. **Tertiary**: BCE with per-sample weights has no built-in class-balance
   correction; even a 1:10 positive-to-negative ratio in active labels
   produces a net negative gradient.

## Related Domain Context

- A6 subproject:
  [docs/learning/reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/README.md](../../../reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/README.md)
- A6-EVT-M launch-window evidence:
  [docs/learning/reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md](../../../reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md)
- A6-EVT-L launch-window contract:
  [docs/learning/reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md](../../../reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md)
- A6-EVT-K event-head evidence:
  [docs/learning/reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md](../../../reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.md)
- Label builder:
  [python/rl/policy_algo/first_event_hazard.py](../../../../../python/rl/policy_algo/first_event_hazard.py)
- Training entry:
  [python/rl/policy_algo/ppo_adaptive_kl.py](../../../../../python/rl/policy_algo/ppo_adaptive_kl.py)

## Next Gates

The next repair gate is A7
([air-combat A7](../../../reviews/optimal_stopping_model_selection_20260605/a7_event_value_advantage_credit_head_20260604/README.md)).
The label-density finding becomes a guardrail for the A7 objective:

1. **Window-balanced target mass**: cap positive and negative weight per
   first-shot window so dense pre-window negatives cannot dominate rare
   quality-window positives.
2. **Counterfactual hold/fire credit**: train `Q_hold` and `Q_fire_once` so
   pre-quality states receive hold credit relative to early fire, rather than
   only another negative fire label.
3. **Shadow quality target**: prevent early stochastic accepted releases from
   erasing later quality-window evidence when policy-observed contact/C2 facts
   still expose it.
4. **Adaptive label scheduling as guardrail only**: use minimum positive-mass
   or confidence checks to stabilize A7, not as the primary repair.

Any fix must:

- keep A3/A5 legality unchanged (masks and state-machine remain
  authoritative);
- produce a deterministic probe where `fire_once` requests > 0 and releases
  occur inside the quality window;
- keep stochastic one-shot discipline and zero violations;
- report cumulative pre-window early-fire probability;
- keep M2 held.

## Acceptance For Closure

- Deterministic probe shows ≥1 authorized release not at near-immediate
  authorization/contact.
- Event probability crosses 50% in open-window steps at evaluation time.
- Zero violation, repeat, or budget issues across deterministic and
  stochastic probes.
- A3/A5 masks and state-machine suppression are not weakened.
- The config change is documented as a bootstrap re-balance, not as
  real-world launch-zone doctrine.
