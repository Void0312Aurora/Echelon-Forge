# A7 Legal-Open Opportunity Credit Prototype

Status: `2026-06-04` `A7-EVC-Q Legal-Open Opportunity Credit Prototype` pass
as a focused implementation slice. Learned-policy behavior remains held until a
bounded follow-on probe is run.

Parent: [README.md](README.md). Contract:
[legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md).

## Implemented Contract

Q implements the P contract by adding direct legal-open quality-window positives:

```text
A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
```

The new source is emitted only for no-release rows that are still real
`AuthorizedReady` / fire-open observations and satisfy the configured
launch-window quality gate. It does not project closed-mask rows, does not reopen
`FiredAssess`, and does not depend on sampling an early accepted release first.

## Code Changes

- `python/rl/policy_algo/first_event_hazard.py`
  - adds `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`;
  - adds `legal_open_quality_weight` and
    `legal_open_quality_min_window_age_steps` to
    `build_first_event_hazard_labels()`;
  - emits legal-open quality positives after deadline fallback so the source
    identity is no longer reported as `DEADLINE` when opportunity credit is
    enabled.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - adds `a7_event_credit_legal_open_quality_weight` and
    `a7_event_credit_legal_open_quality_min_window_age_steps`;
  - passes the new knobs only on the A7 target path;
  - records legal-open quality source counts, positive counts, and source
    advantage mean;
  - keeps projection candidates restricted to `SHADOW_QUALITY`.
- `python/rl/support/nonfinite_probe.py`
  - mirrors the new A7 source metrics in the patched train path.
- Active A7 config
  - enables legal-open quality opportunity credit in the maintained A7 active
    config.

## Diagnostics

New or extended logger tags:

- `a7/event_credit_legal_open_quality_weight`
- `a7/evc_src_legal_open_quality_count_mean`
- `a7/evc_src_legal_open_quality_positive_count_mean`
- `a7/evc_src_deadline_positive_count_mean`
- `a7/evc_src_shadow_positive_count_mean`
- `a7/evc_src_legal_open_quality_advantage_mean`

Existing projection tags remain tied to shadow rows:

- `a7/evc_proj_candidate_count_mean`
- `a7/evc_proj_active_count_mean`
- `a7/evc_proj_unsupported_count_mean`

## Focused Tests

Added or updated tests prove:

- no-release legal-open quality rows become
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` positives;
- the new source is disabled when `launch_window_open` evidence is absent;
- early accepted release still creates `EARLY_ACCEPTED` negatives and
  `SHADOW_QUALITY` repair candidates;
- legal-open quality rows can train event-logit delta directly without
  projection;
- raw shadow rows remain the only projection candidates;
- normal PPO and nonfinite-probe logging expose the new source metrics;
- active A7 config exposes the new opportunity knobs.

## Validation

Commands run:

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py
pytest tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_legal_open_quality_credit_marks_no_release_quality_rows_before_deadline tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_legal_open_quality_credit_requires_launch_window_evidence tests/hmoe/test_a6_first_event_hazard.py::A6FirstEventHazardTests::test_shadow_quality_repair_adds_post_early_positive_credit_without_reopening_fire_mask tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_records_a7_projection_credit_stats tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_legal_open_quality_credit_aligns_event_logits_without_projection -q
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

Observed outcome: compileall passed; focused Q tests passed with `5 passed`;
combined A6/A7/HMoE/active-config pytest passed with `55 passed`.

## Boundaries

- No learned-policy acceptance is claimed by Q.
- No `experiments_tmp` artifacts are staged.
- A3/A5 masks and post-launch suppression remain authoritative.
- Raw `SHADOW_QUALITY` rows still do not train direct event-logit delta.
- M2, HMoE redesign, missile/Pk/fuze/damage authority, `2v2`, self-play, and
  doctrine remain held.

## Dispatch Result

`A7-EVC-Q` implements the non-starved legal-open opportunity-credit path and
passes focused gates. The next bounded work is
`A7-EVC-R Short Opportunity Learned Evidence`.
