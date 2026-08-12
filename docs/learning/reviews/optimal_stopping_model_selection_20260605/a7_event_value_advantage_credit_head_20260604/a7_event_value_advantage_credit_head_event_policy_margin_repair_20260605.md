# A7 Event-Policy Margin Repair

Status: `2026-06-05` completed as structural repair and short learned-policy
evidence; held outcome.

Parent: [README.md](README.md).

## Purpose

`A7-EVC-Z` isolated the remaining execution breakpoint: labels are present, the
credit head can fit the sign split offline, and the actor can separate timing
windows when event logits receive direct signed supervision. The failing link
was the policy contract:

```text
labels -> credit head -> tiny detached advantage -> event-logit delta
```

This slice implements the bounded repair requested by that diagnosis. It gives
the actor/event path a direct signed event-policy margin for ordinary legal-open
positive rows and prewindow negative rows, while keeping the credit head as
value support rather than the sole teacher for deterministic event-mode
crossing.

## Implemented Repair

Code changes:

- `python/rl/policy_algo/first_event_hazard.py`
  - adds `FirstEventPolicyMarginLoss`;
  - adds `compute_first_event_policy_margin_loss()`;
  - trains `event_logit_delta` with a signed squared hinge:
    positive target pushes fire-logit delta above the margin, negative target
    pushes it below the negative margin;
  - preserves first-event mass caps and supports `policy_active` masking so raw
    closed-mask `shadow_quality` rows are not trained directly into event
    logits.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - adds `a7_event_policy_margin_coef`,
    `a7_event_policy_margin`,
    `a7_event_policy_projection_margin_coef`,
    `a7_event_policy_separate_update_enabled`,
    `a7_event_policy_separate_update_max_grad_norm`, and
    `a7_event_policy_separate_update_steps`;
  - wires `_first_event_policy_margin_loss()`;
  - adds a separate actor/event update lane that updates only
    `action_net`, `hybrid_event_head`, and `mlp_extractor.policy_net`;
  - does not update `hybrid_event_credit_head` through the margin lane.
- `train.py`
  - keeps the hybrid `fire_weapon` startup bias conservative at `-6.0`,
    including when the A7 event-policy margin path is enabled.
- Active A7 configs:
  - disable the old weak detached delta-align coefficients;
  - enable event-policy margin coefficients and separate actor/event update
    steps for both shaped and state-completed A7 active configs.

The runtime A3/A5 legal masks, fire-state machine, shot budget, and one-shot
discipline are unchanged.

## Focused Validation

Focused checks passed:

```bash
python -m compileall -q train.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json
pytest tests/training/test_event_timing_training_config_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py -q
pytest tests/policy/test_auxiliary_training_updates.py -q
pytest tests/policy/test_execution_policy_surface.py -q
git diff --check -- <A7 event-policy margin write set>
```

Observed outcomes:

- active-config tests: `7 passed`;
- event-head update-strength tests: `7 passed`;
- HMoE PPO warmup tests: `18 passed`;
- HMoE policy tests: `32 passed`;
- compile, JSON, and diff whitespace checks passed.

The new tests cover positive and negative margin gradient signs, projection
margin routing, separate-update behavior, and the safe-bias contract that A7
margin must not relax the initial fire prior.

Post-correction checks for the safe-bias reversal:

```bash
python -m compileall -q train.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py
pytest tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_safe_action_bias_initializes_air_combat_hybrid_switch_logits tests/policy/test_event_head_update_contracts.py tests/training/test_event_timing_training_config_contracts.py::EventTimingTrainingConfigContractTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss -q
pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_policy_margin_loss_projects_shadow_rows_into_policy_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_separate_policy_margin_update_only_writes_event_policy_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_legal_open_quality_credit_aligns_event_logits_without_projection -q
```

Observed outcomes: compile passed, targeted safe-bias/A7 config/update-strength
checks `9 passed`, and A7 policy-margin warmup checks `4 passed`.

## Short Learned Evidence

Two 8192-step short runs were used as a narrow before/after check. The run
artifacts remain under `experiments_tmp` and are not staging inputs.

Run directories:

```text
experiments_tmp/a7_event_policy_margin_8k_20260605_r1
experiments_tmp/a7_event_policy_margin_8k_20260605_r2
```

Main r2 temporary train config:

```text
experiments_tmp/a7_short_configs/a7_event_policy_margin_8k_20260605_r2.json
```

Probe summary:

| Run | Probe | Episodes | Accepted releases | Release steps | Quality-window fire probability mean | Prewindow fire probability mean | Open-window logit delta mean |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| r1 | deterministic | `2` | `0` | `[]`, `[]` | `0.00391` | `0.00391` | `-5.5409` |
| r1 | stochastic | `4` | `4` | `[6]`, `[147]`, `[273]`, `[18]` | `0.0` | `0.00389` | `-5.5445` |
| r2 | deterministic | `2` | `0` | `[]`, `[]` | `0.11261` | `0.11262` | `-2.0643` |
| r2 | stochastic | `4` | `4` | `[6]`, `[51]`, `[11]`, `[18]` | `0.0` | `0.11250` | `-2.0655` |

The r2 run is now interpreted as a rejected diagnostic, not an accepted repair:
quality/open-window fire probability rises by roughly one order of magnitude,
but prewindow fire probability rises with it. The startup prior moved from the
old safe-bias region near `-5.5` to about `-2.06`, which makes early stochastic
fire overwhelmingly likely before the legal-quality window can form.

The behavior is still not accepted:

- deterministic probing still records `0` accepted releases;
- stochastic probing preserves authorized one-shot release discipline in the
  observed probes;
- stochastic releases remain early/prewindow samples rather than learned
  quality-window timing;
- r2 raises prewindow and quality fire probability together, so it does not yet
  learn the desired timing discriminator.

### Conservative-Bias Follow-Up

After the safe-bias reversal, one additional 8192-step short run verified the
current conservative startup prior:

```text
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1
experiments_tmp/a7_short_configs/a7_event_policy_margin_safe_bias_8k_20260605_r1.json
```

Probe summary:

| Run | Probe | Episodes | Accepted releases | Release steps | Quality-window fire probability mean | Prewindow fire probability mean | Open-window logit delta mean |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| safe-bias r1 | deterministic | `2` | `0` | `[]`, `[]` | `0.00310`, `0.00308` | `0.00310`, `0.00308` | `-5.7735`, `-5.7804` |
| safe-bias r1 | stochastic | `4` | `3` | `[84]`, `[407]`, `[]`, `[18]` | `0.0`, `0.00308`, `0.00308`, `0.0` | `0.00310`, `0.00308`, `0.00308`, `0.00310` | `-5.7740`, `-5.7807`, `-5.7807`, `-5.7731` |

TensorBoard review:

- `a7/event_credit_active_count_mean` was live in the middle of training
  (`718` at step `3072`, `762` at step `4096`) but ended at `0` by step
  `8192`.
- `a7/evc_src_legal_open_quality_count_mean` briefly recovered
  (`231` at step `3072`, `128` at step `4096`) and then returned to `0`.
- `a7/event_credit_advantage_mean` ended positive at about `0.7148`, but this
  final sign was measured with no active event-credit rows.
- PPO movement stayed small at the end (`train/approx_kl=0.0006695`,
  `train/policy_gradient_loss=-0.0002126`).

The follow-up confirms the safe-bias fix in the narrow sense: the event fire
probability no longer jumps to the rejected `~0.112` region, and stochastic
execution does not violate one-shot discipline. It still does not solve the
learned behavior. Deterministic probing remains `hold`, and stochastic releases
come from cumulative low per-step hazard rather than a learned quality-window
timing discriminator. No probe episode produced effects or damage; final target
health stayed at `40.0`.

## Interpretation

This slice fixes the confirmed implementation-level problem from Z: the actor
now receives a direct signed event-policy margin instead of relying only on a
tiny detached credit advantage. The short train also exposed a second structural
fault: relaxing the startup fire prior is not exploration, but label starvation.
With `fire_weapon` bias at `-2.0` and hold at `0.0`, per-step stochastic fire
probability is about `0.119`, so the probability of at least one pre-window
release in a 32-step window is about `0.983`. That converts ordinary legal-open
positives into early-accepted/shadow-quality rows and forces the actor to learn
mostly through the weaker projection path.

It does not solve A7. The remaining blocker has shifted:

```text
direct signed margin exists
  -> relaxed startup prior makes stochastic samples fire early
  -> deterministic argmax still stays below the fire threshold
  -> legal-open actor labels are starved online
```

The current evidence is therefore not "credit cannot move actor" anymore. It is
closer to policy-threshold and online sampling-distribution structure: the
policy can be nudged into stochastic one-shot firing, but the training
distribution must preserve low prewindow hazard so legal-open quality labels
remain available for the actor margin.

The conservative-bias follow-up narrows that statement further. Restoring low
prewindow hazard prevents the obvious label-starvation failure, but it also
returns the actor to a very low event-fire probability band. The mid-run label
spikes show the credit source is not permanently disconnected; the final
collapse to zero active rows suggests the remaining blocker is now the online
sampling/update distribution that stops maintaining legal-open actor labels
long enough to cross deterministic event-mode selection.

## Status

`A7-EVC-AA` passes as a structural repair and short learned observation. A7
remains held. Acceptance still requires deterministic one-shot release inside
the quality window, bounded stochastic prewindow hazard, and preserved A3/A5
legality.
