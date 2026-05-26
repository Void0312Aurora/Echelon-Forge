# RL Policy Hold-Baseline Drift

Status: active issue; blocks formal-training claims for affected hold-style
tasks.

First observed: `2026-05-26`, during N4 naval screen-station RL validation.

Issue class: policy-update drift around a strong hold baseline.

## Summary

The first concrete instance was found in the N4 naval screen-station task:
the scenario starts at the desired station, and zero action is a strong and
measured baseline. The policy is initialized to zero action correctly, but
after PPO updates it learns a stable non-zero command even though that command
is worse than the zero-action baseline.

This should be treated as a general RL/training issue, not only a naval-domain
issue. Any future task where "keep current command" is the correct local
behavior can be affected.

## Current Evidence

Focused diagnosis on the N4 naval screen-station scenario showed:

- zero-action rollout: total reward `89.775565` over `1200` steps;
- trained deterministic rollout after the low-exploration/action-penalty probe:
  total reward `-3.1535` over `1200` steps;
- trained stochastic rollout from the same checkpoint: total reward about
  `-16.78`;
- untrained zero-head initialization rollout: total reward `89.775565`, with
  action mean exactly `[0.0, 0.0, 0.0]`;
- trained deterministic action mean:
  `[+0.077, -0.194, +0.024]`.

For the current `naval_station3` mapping, that deterministic action roughly
means:

- station bearing offset of about `+1.9 deg`;
- station radius reduction of about `350 m`;
- small positive speed bias.

The contact, shared-track, report-chain, and pre-fire ROE rewards still fire
normally. The failure is therefore not explained by a broken scenario or a
missing report chain. The actor moves away from a neutral hold command after
training.

## Related Domain Context

- Naval N5 action/observation split:
  [docs/task/naval/n5_rl_action_surface_split/README.md](../../naval/n5_rl_action_surface_split/README.md)
- N4 naval scenario under test:
  `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`
- Training config used for the first short probes:
  `examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json`

## Known Fixed Preconditions

Before this issue was split out, several earlier blockers were already
identified or repaired:

- the naval mission observation now has a dedicated `naval_screen_station_v1`
  vector instead of using the air formation-role observation surface;
- transformer mission preprocessing now treats the naval vector by naval field
  semantics instead of air-route semantics;
- `naval_station3` safe initialization zeros both bias and action-head weights;
- the reward surface can penalize needless station-order changes.

These fixes are necessary but not sufficient: PPO updates still drift the
actor into a non-zero deterministic command.

## Hypotheses

Current leading hypotheses:

- the task is locally degenerate: at the initial station, exploration usually
  hurts, so the training signal is dominated by small noisy differences around
  a hold optimum;
- the current PPO probe uses very small rollouts, `n_steps=32`, `batch_size=32`,
  and `n_epochs=1`, so each update has little averaging and can move the actor
  based on a single small batch;
- the logged KL can remain near zero in this configuration and does not prove
  that the post-update deterministic mean stayed near the hold policy;
- reward-level action penalties reduce the damage but do not explicitly
  constrain the actor mean around zero;
- the curriculum gives no positive reason to issue a corrective station-order
  command, so learning a useful non-zero command is not yet tested.

## Non-Claims

Do not claim the following while this issue is open:

- N4 naval formal RL training is successful;
- the trained N4 policy is better than the zero-action baseline;
- the issue is naval-only;
- contact/report-chain behavior is the main failure cause;
- weapon release, damage, or kill behavior is covered by this issue.

## Next Gates

The next repair work should choose one or more controlled paths:

- add an explicit actor-mean regularization or hold-command prior for
  hold-style tasks;
- reduce PPO update noise through larger rollout batches, lower learning rate,
  or more conservative actor updates, then re-check deterministic mean drift;
- add a behavior-cloning or constraint pass for neutral hold commands;
- build an off-station curriculum where non-zero station actions can produce
  real positive value, then compare against the hold baseline separately;
- migrate maintained eval tooling so formal validation uses the same
  `WorldBatchVecEnv` path as training.

Acceptance for any fix should include both reward and action-output evidence:

- zero-action baseline remains measured;
- trained deterministic rollout beats or at least matches the baseline for the
  intended curriculum stage;
- deterministic action means and absolute means are reported;
- reward-term summaries confirm that contact/report/ROE chains still behave as
  expected.
