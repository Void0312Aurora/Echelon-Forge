# M3-S1 P4 Dispatch Review

Status: `2026-06-05` pass. P4-A, P4-B, and P4-C are accepted as bounded
implementation slices; P5 diagnostics and short training are now opened by the
[P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.md).

Parent: [M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

## Scope Reviewed

| Slice | Status | Touched surface | Evidence | Does not prove |
| --- | --- | --- | --- | --- |
| `M3S1-P4A Policy Head Skeleton` | pass | `python/rl/policy_algo/policies.py`; focused `tests/hmoe/test_hmoe_policy.py` entries | optional independent `m3_stopping_head`, getter helpers, separate `m3s1/*` stats, focused policy tests | no PPO integration, threshold calibration, or grouped mass learning |
| `M3S1-P4B Grouped Evidence/Loss Skeleton` | pass | `python/rl/policy_algo/m3s1_grouped_stopping.py`; `tests/hmoe/test_m3s1_grouped_stopping.py` | grouped evidence carrier plus pure survival/event-mass loss helper and tests | no rollout-buffer sidecar, PPO auxiliary pass, or training config |
| `M3S1-P4C PPO Auxiliary Integration` | pass | `python/rl/policy_algo/ppo_adaptive_kl.py`; `tests/hmoe/test_hmoe_ppo_warmup.py` | M3-S1 sidecar built before buffer flattening; grouped auxiliary update calls independent stopping head after base PPO loop; focused integration tests | no P5 short training, threshold calibration, or learned-policy success |

## Local Verification

```bash
python -m py_compile python/rl/policy_algo/policies.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  tests/hmoe/test_m3s1_grouped_stopping.py
python -m pytest tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_m3s1_grouped_stopping.py -q
python -m pytest tests/hmoe/test_m3s1_grouped_stopping.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m pytest tests/hmoe/test_a6_event_head_update_strength.py \
  tests/training/test_a6_event_value_active_config.py -q
git diff --check -- python/rl/policy_algo/policies.py \
  tests/hmoe/test_hmoe_policy.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  tests/hmoe/test_m3s1_grouped_stopping.py \
  docs/task/model/m3_s1_censored_optimal_stopping_timing_contract
```

Outcome:

- `py_compile`: pass.
- focused pytest: `44 passed`.
- M3-S1/HMoE integration pytest: `64 passed`.
- A6/A7 adjacent regression pytest: `14 passed`.
- `git diff --check`: pass.

## Acceptance Notes

- P4-A keeps the new stopping score independent from executable hybrid event
  logits. The action branch and existing fire mask remain authoritative.
- P4-A defaults to disabled via `m3_stopping_head_lr_scale = 0.0`, so existing
  behavior is not changed until the head is explicitly enabled.
- P4-B computes `lambda_t = M_t * sigmoid(z_t)`, survival, event mass,
  desirable-window mass, early mass, no-event mass, and early-prefix survival
  over complete ordered groups.
- P4-B preserves group structure and is explicitly not a row-wise BCE helper.
- P4-B currently interprets `support_horizon` in `row_indices` coordinates and
  `censor_step` in `step_indices` coordinates. P4-C must preserve or adapt that
  convention deliberately.
- P4-C preserves full episode chunks in the M3-S1 sidecar, including closed-mask
  rows, and uses `legal_mask` to keep hazards executable-only.
- P4-C keeps base PPO minibatch flow unchanged and runs the grouped stopping
  objective as a separate auxiliary optimizer step after the ordinary PPO loop.
- P4-C defaults disabled via `m3s1_grouped_stopping_coef = 0.0`; it also
  requires a policy exposing `get_m3_stopping_logits()`.

## Residuals

- P5 is active under the
  [P5 dispatch plan](m3_s1_p5_dispatch_plan_20260605.md), and must run
  diagnostic probes and short training before any behavior claim.
- P5 must report deterministic boundary crossing, cumulative early mass,
  no-event mass, one-shot legality, and closed-mask stop attempts.
- Threshold calibration and active training config promotion are not part of P4.
- No reward magnitude, C2/ROE gate, action mask, or one-shot legality behavior
  has been changed by P4.
