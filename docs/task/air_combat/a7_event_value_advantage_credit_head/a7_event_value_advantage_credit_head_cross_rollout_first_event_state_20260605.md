# A7 Cross-Rollout First-Event Credit State

Status: `2026-06-05` implementation pass; learned-policy behavior still held
pending a new observation run.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md).

## Purpose

`A7-EVC-W` showed that the first-event credit target is an episode-level
function, while the implementation evaluated it on PPO rollout-local chunks.
When stochastic exploration accepted a release before the quality window, and
the quality window arrived in a later rollout, `shadow_quality` positives existed
on the full episode but were missing from the training labels.

`A7-EVC-X` repairs that training-loop contract. It carries per-env episode
first-event context across PPO rollouts, then evaluates the existing label
builder with that context and slices the labels back to the current rollout.

## Implementation

Code changes:

- `python/rl/policy_algo/ppo_adaptive_kl.py` adds `_A7FirstEventRolloutRow` and
  per-env `_a7_first_event_rollout_history`.
- The cross-rollout path is gated to A7 credit labels when A6 hazard targets are
  not active and `launch_window_open` evidence is present.
- At label attach time, the current rollout is evaluated both locally and with
  any same-episode carried prefix. Only the current rollout slice is written to
  the rollout buffer.
- The history resets when `env_episode_id_after_rollout` shows that the env
  advanced to a new episode, including terminal events on the final step of a
  rollout.
- New A7 diagnostics are logged from both the normal PPO path and
  `NonFiniteTrainingProbe`:
  - `a7/evc_cross_rollout_context_rows`
  - `a7/evc_carried_shadow_pending_envs`
  - `a7/evc_carried_shadow_positive_count_mean`
  - `a7/evc_cross_rollout_first_event_count_mean`

The repair does not change A3/A5 runtime legality masks, event action
suppression, missile authority, reward shaping, or the policy action surface.

## Validation

Focused gates run in this slice:

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_cross_rollout_first_event_state_recovers_shadow_quality_after_boundary -q
pytest tests/hmoe/test_a6_first_event_hazard.py -q
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/first_event_hazard.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
```

Observed results:

- compileall: pass.
- New cross-rollout regression: `1 passed`.
- A6 first-event hazard tests: `20 passed`.
- HMoE/PPO warmup tests: `16 passed`.

The new regression constructs a 512-step episode with an accepted release at
index `5`, launch-window open from index `281`, and `128` step chunks. Full
episode labels contain `231` `shadow_quality` positives. Rollout-local chunk
labels without carried state contain `0` shadow positives. The carried-state
attach path reconstructs labels that match the full episode field-by-field and
recovers `128` carried shadow positives in the final chunk.

## Boundary

X is a focused implementation repair. It proves that the PPO rollout boundary no
longer deletes episode-level first-event credit in the covered scenario. It does
not accept A7 learned behavior yet: deterministic first release, stochastic
early-release probability, one-shot legality, and event-advantage signs still
need a new bounded learned-policy observation after this repair.

## Next Step

Run a short A7 observation with the repaired training-loop contract and compare
the new A7 diagnostics against V/W:

- `a7/event_credit_active_count_mean`
- `a7/evc_src_shadow_positive_count_mean`
- `a7/evc_carried_shadow_positive_count_mean`
- deterministic first-release timing
- stochastic early-release timing and one-shot violations
