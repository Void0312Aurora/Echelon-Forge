# A7 Projected Legal-Open Credit Prototype

Status: `2026-06-04` `A7-EVC-M` implementation pass; learned-policy behavior
not yet evaluated.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md).

## Purpose

`A7-EVC-L` selected legal-state projection because repaired `shadow_quality`
positives live on post-release closed-mask observations, while policy coupling
needs positive `fire_once` credit on legal-open observations. M implements that
contract as a focused prototype.

## Implementation

- Added `python/rl/policy_algo/first_event_projection.py`.
  - Projects only the A3/A5 event-legality surface for
    `air_combat_c2_roe_v1` observations.
  - Rewrites `mission[5]`, `mission[6]`, `mission[14]`, `mission[15]`,
    `mission[16]`, `mission[17]`, `mission[19]`, plus optional
    `event_action_mask` and `fire_mask`.
  - Preserves contacts, contact history, geometry, instruments, RWR,
    proprioception, and unrelated policy inputs.
  - Refuses unsupported mission layouts and reports unsupported rows without
    training closed-mask alignment.
- Extended `AdaptiveKLPPO._first_event_credit_loss()`.
  - Raw `shadow_quality` rows remain excluded from ordinary delta alignment.
  - When `a7_event_credit_legal_projection_enabled=true`, shadow rows with
    contact evidence get a projected legal-open observation pass.
  - Projected rows train positive value and optional projected event-logit
    delta alignment.
- Added A7 projection knobs:
  - `a7_event_credit_legal_projection_enabled`
  - `a7_event_credit_projection_value_coef`
  - `a7_event_credit_projection_delta_align_coef`
- Added short logger stats:
  - `a7/evc_proj_active_count_mean`
  - `a7/evc_proj_unsupported_count_mean`
  - `a7/evc_proj_advantage_mean`
  - `a7/evc_proj_delta_mean`
- Mirrored those projection stats in `NonFiniteTrainingProbe`, whose patched
  `train()` path is used by the active A7 config.
- Enabled projection in the active A7 config.

## Validation

Commands run:

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_first_event_hazard.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
pytest tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

Observed outcomes:

- compileall: pass.
- `tests/hmoe/test_a6_first_event_hazard.py`: `17 passed`.
- focused projected-loss PPO test: `1 passed`.
- HMoE/PPO focused group: `15 passed`.
- active config and active-entry group: `19 passed`.
- A7 JSON parse: pass.
- Combined focused rerun after docs sync: `51 passed`.

## Boundary

M does not run a learned-policy wave and does not accept A7 behavior. It proves
that the projection path exists, respects A3/A5 legality, keeps raw
closed-mask `shadow_quality` out of direct delta alignment, and can create
projected legal-open positive event-logit pressure in a focused PPO test.

## Next

The next bounded slice is `A7-EVC-N Short Projection Learned Evidence`: run a
short learned-policy probe and compare deterministic release timing, stochastic
first-release timing, one-shot violations, projected active count, projected
advantage sign, and projected delta sign.
