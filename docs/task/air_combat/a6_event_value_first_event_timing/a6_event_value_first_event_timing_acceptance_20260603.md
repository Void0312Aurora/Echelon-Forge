# A6 Acceptance Gate

Status: `2026-06-04` gate evaluated after launch-window short learned evidence
and root-cause re-scope; not accepted.

Parent: [README.md](README.md).

## Accepted Scope Target

A6 acceptance is limited to making the A5 masked `hold/fire_once` event surface
trainable under S1 C2/ROE by adding an explicit event-value, hazard, or
first-event timing objective.

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | Selected objective targets masked event timing directly. | pass for first contracts and L contract: masked first-event hazard, deadline bootstrap, event-head optimization, and launch-window gated labels. |
| Legality boundary | A3/A5 masks and state transitions still own legal support and post-launch suppression. | pass; no reward-only legality penalties were restored. |
| Training-kernel tests | Policy/PPO tests cover objective shape, mask, finite loss/stats, deterministic eval, and compatibility. | pass; deadline label/source tests, event-head update-strength diagnostics, event-head optimizer lane tests, and launch-window label/PPO extraction tests are included. |
| Config/diagnostics tests | Active S1 C2/ROE config exposes A6 knobs and diagnostics without restoring legality-as-penalty defaults. | pass; separate deadline, event-head, and launch-window config/logging tests are included. |
| Learned evidence | Deterministic event probability/mode moves materially from A5 baseline and either fires once authoritatively or leaves a precise held residual. | held: launch-window deterministic probe reaches `34.6% / 35.0%` open-window probability but makes `0` requests; stochastic releases at steps `7`, `43`, `4`. |
| Root-cause analysis | Held residual is assigned to a mechanism class before more training. | pass: A6-EVT-N assigns the blocker to stochastic hazard accumulation, absorbing first-event censoring, and missing counterfactual hold/fire credit. |
| Overclaim refusal | M2, `2v2`, self-play, missile physics, Pk, fuze, damage authority, and real doctrine remain held. | active |

## Current Baseline To Beat

A5 retained short learned-policy evidence:

- deterministic: `1880` fire-mask-open steps, `0` requests, `0` releases,
  `policy_event_prob_fire_once_mean=0.217%`, max `0.278%`;
- stochastic: `3` authorized releases in `3` episodes, `0` violation releases,
  `0` repeat or budget violations.

The first A6 learned-policy probe preserved the stochastic discipline baseline
but did not move deterministic `fire_once` probability/mode materially.

The deadline-bootstrap probe moved deterministic open-window probability to
`0.494% / 0.496%`, but still produced `0` deterministic requests. Stochastic
produced `3/3` authorized releases and zero violation/repeat/budget issues, but
regressed to one `weapon_not_ready` rejected request.

The event-head update audit recorded the prior held residual: labels and
gradients were live, but current `3e-5` learning rate plus damped HMoE residual
ownership was too weak to move a final event delta around `-5.3` across
deterministic argmax.

The event-head optimization lane resolves that narrow blocker. The 32k
event-head run crosses deterministic argmax, executes one deterministic
authorized release at step `2`, and stochastic probing executes one authorized
release in each of `3` episodes with no rejected, violation, repeat, or budget
issues. A6 still remains held because this is not mature first-event timing:
the learned policy releases almost immediately after authorization/contact,
vacating the intended deadline/open-window timing evidence.

The launch-window timing contract changes the label surface so legal
authorization is no longer a positive teacher by itself. It introduces
pre-window hold labels, early-accepted negative labels, contact-quality range
gating, and a separate active config. This is implementation evidence only; the
baseline still must be beaten by a short learned-policy probe.

The launch-window short probe shows the contract is live but not accepted.
Deterministic mode no longer repeats the K-style step-2 release, but it also
does not cross masked argmax: `0` requests, `0` releases, and `34.6% / 35.0%`
open-window fire probability. Stochastic mode still samples one authorized
release per episode at steps `7`, `43`, and `4`; no rejected, violation,
repeat, or budget issues occur.

The root-cause re-scope treats that result as a first-event survival/hazard
blocker instead of an L tuning problem. The stochastic releases occur with
pre-release cumulative early-fire probabilities of `0.810`, `0.556`, and
`0.625`, while deterministic mode still needs `fire_once` probability above
`0.5` to cross argmax. Accepted early release is absorbing for the first-event
window, so later quality-window evidence is censored on-policy. A future gate
therefore needs counterfactual hold/fire credit or an event-time survival
objective before more training.

## Failure Conditions

A6 must remain held or be re-scoped if:

- the selected objective only changes generic reward magnitude;
- implementation bypasses or weakens A5 masks/state transitions;
- deterministic policy still makes zero `fire_once` requests and no stronger
  diagnosis is recorded;
- stochastic discipline regresses without a named and bounded repair path;
- deterministic crossing is presented as mature timing while release occurs
  immediately after authorization/contact;
- docs imply M2, missile authority, or real-world tactics are released.
- fixed-age deadline behavior is presented as doctrine or final tactical
  maturity instead of bounded bootstrap evidence.
- event-head update diagnostics are presented as learned-policy acceptance.
- event-head deterministic crossing is presented as full A6 acceptance without
  a launch-window timing contract.
- launch-window held evidence is presented as A6 acceptance.
- L range/age bootstrap values are presented as doctrine, missile authority, or
  final tactical maturity.
- further L training is started before A7 defines and validates the
  counterfactual target source, stochastic collection handling, and cumulative
  hazard diagnostics.

## Validation Commands

Docs-only initial gate:

```bash
git diff --check -- docs/task/air_combat
```

Implemented validation gate:

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed: `68 passed, 8 subtests passed`.

Deadline focused gate:

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/training/test_air_combat_active_training_entries.py
```

Observed: `26 passed, 9 subtests passed`.

Deadline full A6/diagnostics gate:

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed: `71 passed, 9 subtests passed`.

Event-head update-strength gate:

```bash
.venv/bin/python -m pytest -q tests/hmoe/test_a6_event_head_update_strength.py
```

Observed: `2 passed`.

Event-head optimization gate:

```bash
.venv/bin/python -m pytest -q \
  tests/hmoe/test_a6_event_head_update_strength.py \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/training/test_cooperative_diagnostics_callback.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Observed: `77 passed, 10 subtests passed`.

Launch-window focused implementation gate:

```bash
.venv/bin/python -m compileall -q \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  python/training_callbacks.py
```

Observed: pass.

```bash
.venv/bin/python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  >/dev/null
```

Observed: pass.

```bash
.venv/bin/python -m pytest \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_a6_event_value_diagnostics_callback.py \
  tests/training/test_a6_event_value_active_config.py \
  -q
```

Observed: `28 passed`.

Launch-window learned-policy gate:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_launch_window_temporal_32k_20260604 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260641
```

Observed: completed `32768` timesteps.

Deterministic probe observed `0` requests and `34.6% / 35.0%` open-window event
probability. Stochastic probe observed `3/3` authorized releases at steps `7`,
`43`, and `4`, with zero rejected/violation/repeat/budget issues.

Root-cause docs gate:

```bash
git diff --check -- docs/task/air_combat/a6_event_value_first_event_timing
```
