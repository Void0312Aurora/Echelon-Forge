# A5 Constrained Event Action Model Acceptance Gate

Status: `2026-06-03` held after evidence, not accepted. Structural
event-action, reward/config, and diagnostics gates have implementation evidence.
The short learned-policy probe fixed stochastic release discipline but did not
produce deterministic `fire_once`; final cross-doc held closure remains pending.

## Accepted Scope To Prove

A5 acceptance is about the S1 C2/ROE policy-facing weapon release event model.
It does not accept learned `1v1` tactical maturity beyond this gate, and it does
not release M2.

## Required Evidence

| Gate | Required evidence | Status |
| --- | --- | --- |
| Event action support | Accepted S1 C2/ROE entry exposes `hold/fire_once` or equivalent constrained event semantics. | pass: A5 event contract plus D/E implementation evidence |
| Mask legality | Fire is unavailable outside authorized event states by mask/state-machine support. | pass: runtime gate and policy mask tests |
| Post-launch suppression | Accepted `fire_once` enters assessment/no-fire state and prevents immediate repeat fire. | pass: runtime gate tests |
| Explicit reattack path | Follow-up fire requires `ReattackReady`, salvo, or another explicit authorization state. | pass: runtime state machine contract and tests |
| Policy semantics | Stochastic sampling, deterministic eval, log-prob, and entropy/stats all respect the same mask. | pass: HMoE policy tests |
| Reward boundary | Reward expresses outcome/timing/ammo/track preferences and does not serve as the primary legality mechanism. | pass: F reward/config cleanup |
| Diagnostics | Probes distinguish requested, executed, rejected, authorized, violation, repeated, and post-launch fire attempts. | pass: G diagnostics implementation |
| Learned evidence | Deterministic learned policy executes one authorized first shot, or held residual is narrowed outside reward-only tuning. | held evidence: stochastic discipline fixed; deterministic `fire_once` remains 0 |
| Documentation | A3/A4/M1/M2 and parent air-combat docs are synchronized without overclaiming. | partial: A5 and parent air-combat docs synced; full held closure sync pending |

## Minimum Test Shape

The final acceptance record must include the exact commands run. Expected
families include:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/policy/test_execution_policy_surface.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py

git diff --check -- docs/task/air_combat docs/standards/air gym_envs python scenarios examples/config/training/active/air_combat tests tools
```

Learned-policy probes must report deterministic and stochastic event behavior
and must not stage `experiments_tmp`.

The short A5 learned-policy probe is recorded in
[a5_constrained_event_action_model_short_learned_probe_20260603.md](a5_constrained_event_action_model_short_learned_probe_20260603.md).

## Rejection Conditions

A5 must remain held if any of these are true:

- The accepted S1 C2/ROE policy-facing release path still depends on raw
  `sigmoid(logit)>0.5` or a continuous threshold for fire.
- Invalid fire samples are still expected as the main way for policy to learn
  legality.
- Post-launch repeated fire is prevented only by a reward penalty, not by state
  or action support.
- Deterministic and stochastic evaluation use different event semantics.
- Documentation implies missile physics, Pk/fuze, true BVR doctrine, or M2
  release authority.

## Residual Policy

If masked categorical event semantics are structurally accepted but learned
deterministic timing still fails, A5 may close as held with a follow-on event
Q-head or hazard package. That follow-on is now explicit under
[../a6_event_value_first_event_timing/README.md](../a6_event_value_first_event_timing/README.md)
and must not be hidden as reward tuning.
