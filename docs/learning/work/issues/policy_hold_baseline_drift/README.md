# RL Policy Hold-Baseline Drift

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/policy_hold_baseline_drift/README.md`
Owner: `learning/policy-evaluation`
Last verified: `2026-08-08`

Status: deterministic N4 hold probe closed; retained as a tracking item for
off-station curricula and stochastic-policy acceptance.

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

## 2026-05-27 Small-Scope Repair Probes

A default-off training-side hold prior has been added:

- `AdaptiveKLPPO` supports `action_mean_regularization_coef` and
  `action_mean_regularization_target`;
- the regularizer constrains the current deterministic policy action toward a
  target action;
- the non-finite probe replaces the training loop, so the same loss and logs
  were mirrored there to avoid silently ignoring the config while diagnostics
  are enabled;
- the active naval screen-station smoke config now uses this hold prior and
  disables actor/critic feature-extractor sharing as a conservative diagnostic
  entry.

Results from 4096-step low-exploration probes replayed on the maintained
`WorldBatchVecEnv` path:

- zero-action baseline: `89.775565`;
- `coef=5`: deterministic replay `29.689964`, stochastic replay `6.865154`,
  deterministic action mean about `[+0.093636, -0.177952, -0.000888]`;
- `coef=50`: deterministic replay `63.706747`, stochastic replay `56.213039`,
  deterministic action mean about `[-0.042754, +0.009271, -0.041420]`;
- `coef=50` with `share_features_extractor=false`: deterministic replay
  `80.572003`, stochastic replay `73.745653`, deterministic action mean about
  `[-0.014999, -0.000956, -0.014365]`;
- `coef=500` with `share_features_extractor=false`: deterministic replay
  `85.676334`, stochastic replay `79.300771`, deterministic action mean about
  `[-0.000535, -0.012665, -0.000574]`.
- `coef=500`, `share_features_extractor=false`, `learning_rate=1e-4`, and
  `n_steps=batch_size=128`: deterministic replay `89.330973`, stochastic replay
  `78.927745`, deterministic action mean about
  `[+0.000879, -0.001092, -0.003074]`.
- same settings plus a `0.005` near-zero deadband for `naval_station3`, retrained
  for `4096` steps: deterministic replay `89.775565`, matching the zero-action
  baseline; stochastic replay `79.597278`; raw deterministic action mean about
  `[+0.000795, -0.001017, -0.003045]`, applied action mean about
  `[+0.0000007, -0.0000007, -0.0000026]`.

Confirmed detail: `SquashedDiagGaussianDistribution.mode()` returns the tanh
squashed action, so actor-mean regularization is applied in the actual action
space sent to the environment, not only to the unsquashed internal Gaussian
mean.

Conclusion: the cause has been narrowed to action-surface interpretation:
thousandths-scale policy-mean jitter was treated as a real station-order change,
which repeatedly triggered action penalties and station error. The small-scope
repair set, actor-mean hold prior, actor/critic feature decoupling, conservative
PPO batch/learning rate, and a `naval_station3` near-zero deadband, now lets the
N4 screen-station deterministic hold probe match the zero-action baseline.
Stochastic replay remains below baseline, so this conclusion covers only the
deterministic hold probe, not off-station curricula, stochastic acceptance,
weapon release, or combat.

## Related Domain Context

- Naval N5 action/observation split:
  [retained N4 action-surface repair](../../../../domains/naval/reviews/n5_rl_action_surface_split_20260527/README.md)
- N4 naval scenario under test:
  `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`
- Training config used for the first short probes:
  `examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json`

## 2026-05-27 Naval Infrastructure Closure Update

The N4 naval screen-station runtime no longer relies on reward cancellation for
airfield-only safety terms:

- naval tasking profiles disable runway-surface/off-runway interpretation before
  safety-runtime inputs are built;
- `naval_suppress_off_runway_penalty` is retired for naval profiles; turning it
  on now fails fast instead of masking an active `off_runway_penalty`;
- naval profiles do not build flight-shaping reward inputs, so `speed_reward`
  and `roll_stability` are no longer emitted as zero-valued naval reward terms.
- full step-info output for naval profiles filters airfield/landing diagnostics
  such as `on_runway`, `runway_cross_m`, `gear_collapsed`, and `gear_stress`,
  including the episode-controller mainline facade path.
- naval policy observations keep the existing `instruments` shape for model
  compatibility, but filter aircraft/airfield-specific fields such as IAS, Mach,
  barometric/radar altitude, AOA, gear/flaps/speedbrake, and ILS terms before
  exposing them to the policy; execution/runtime safety still uses the original
  instrument state internally. Naval loaders also disable execution-observation
  device export so the torch policy bridge reads the filtered buffer instead of
  bypassing this filter through a flat device view.
- naval tasking profiles fail fast on air-style action modes such as `takeoff4`;
  both single-slot and cooperative batch paths now apply `naval_station3` as
  station-order intent while sending only a neutral low-level ship carrier
  action.
- `naval_station3` deadbanding is now applied before recording policy
  proprioception/`last_action`, so the policy-visible previous action, reward
  action penalties, and the actual station-order command use the same applied
  command. A `0.004` tiny action is observed as `[0.0, 0.0, 0.0]` by
  `proprio`, `last_action`, and `_naval_station3_last_action` on the maintained
  world-batch path, cooperative path, explicit raw-compat `UniversalEnv`, and
  the single-world/leader compatibility runtime facades.

The zero-action baseline is unchanged at `89.775565` over `1200` steps, but the
reward breakdown now contains only naval station/contact/report/ROE terms plus
the zero-valued generic safety survival term. This is an infrastructure closure
step, not a claim about weapon release, damage, stochastic-policy acceptance, or
off-station station-order learning.

## 2026-05-27 Off-Station Reward-Reference Closure

A follow-up probe found a separate reward-reference hazard: if station reward
was evaluated against the policy-updated station command, a radius command could
move the scoring reference toward the ship and appear useful before the ship had
actually recovered to the original task station.

The N4 naval runtime now binds a reset-time station evaluation reference:

- `naval_station3` actions may still update the station command sent through
  the task/mission-command chain;
- station-error reward and `mission_status[0]` are evaluated against the
  original task station reference captured at reset;
- world-batch, cooperative, and raw `UniversalEnv` reset paths bind the same
  evaluation reference;
- focused runtime tests cover the world-batch and cooperative paths so a
  matched radius command cannot pull the reward reference onto the off-station
  ownship.

Maintained eval tooling now includes `--mode offstation_probe`. The probe can
derive a temporary DDG-inside-station scenario, and it can also run directly on
the maintained
`scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json`
scenario. With the DDG `1800 m` inside the nominal screen radius, the
zero-action scripted station hold reduces station error under the fixed
original-task reference. A matched radius command remains lower reward and ends
farther from the original task station because action cost and the fixed
reference are both active. The maintained recovery scenario enables
`naval_station_recovery_progress_bonus` so the curriculum signal is tied to real
station-error reduction rather than moving the scoring reference. This closes
the self-referential reward loophole and proves the scripted recovery gate; it
does not prove a learned off-station recovery policy.

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
actor into a non-zero deterministic command unless the hold prior, conservative
PPO settings, and `naval_station3` near-zero deadband are kept together. With
that small-scope repair set, the deterministic hold probe now matches the
zero-action baseline; stochastic acceptance and off-station learning remain
open.

## Hypotheses

Current leading hypotheses:

- the task is locally degenerate: at the initial station, exploration usually
  hurts, so the training signal is dominated by small noisy differences around
  a hold optimum;
- the current PPO probe uses very small rollouts, `n_steps=32`, `batch_size=32`,
  and `n_epochs=1`, so each update has little averaging and can move the actor
  based on a single small batch;
- increasing `n_steps=batch_size` to `128` and reducing the learning rate to
  `1e-4` brings deterministic replay close to the zero-action baseline, but
  does not match it;
- `naval_station3` needs a small deadband to express the engineering semantics
  of a hold command; otherwise numerical jitter is interpreted as a new
  station order on every step;
- actor/critic feature-extractor sharing lets value loss indirectly change the
  actor representation; disabling sharing reduces the drift but does not remove
  it;
- the logged KL can remain near zero in this configuration and does not prove
  that the post-update deterministic mean stayed near the hold policy;
- reward-level action penalties reduce the damage but do not explicitly
  constrain the actor mean around zero;
- the curriculum gives no positive reason to issue a corrective station-order
  command, and the off-station probe now prevents station commands from scoring
  by moving the reward reference, so learning a useful non-zero command still
  needs a separate curriculum.
- `naval_station_recovery_progress_bonus` is active only in the maintained
  off-station recovery entry; the normal contact-report and station-hold
  entries keep it disabled. This gives a stable scripted recovery gate without
  promoting learned off-station policy acceptance.

## Non-Claims

Do not claim the following while this issue is open:

- N4 naval formal RL training is successful;
- the trained N4 deterministic hold probe is better than the zero-action baseline;
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
  real positive value under the fixed original-task station reference, then
  compare against the hold baseline separately;
- migrate maintained eval tooling so formal validation uses the same
  `WorldBatchVecEnv` path as training.

Acceptance for any fix should include both reward and action-output evidence:

- zero-action baseline remains measured;
- off-station probes confirm station actions cannot move the reward reference
  onto the ownship;
- trained deterministic rollout beats or at least matches the baseline for the
  intended curriculum stage;
- deterministic action means and absolute means are reported;
- reward-term summaries confirm that contact/report/ROE chains still behave as
  expected.
