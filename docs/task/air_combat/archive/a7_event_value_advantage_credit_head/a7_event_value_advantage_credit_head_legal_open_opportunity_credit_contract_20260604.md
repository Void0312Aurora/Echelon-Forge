# A7 Legal-Open Opportunity Credit Contract

Status: `2026-06-04` selected design contract for
`A7-EVC-P Legal-Open Opportunity Credit Contract`; implementation is not started
by this document.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md).

## Decision

`A7-EVC-O` shows that the M projection path is structurally correct but
candidate-starved: it trains projected legal-open positives only when
`shadow_quality` rows exist, and those rows exist only after the policy first
samples an early accepted release. That makes M a repair path for sampled early
release, not a proactive opportunity-credit source.

A7 should add a new legal-open source:

```text
A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
```

This source marks real, pre-release, legal-open quality-window observations as
positive `fire_once` opportunity credit. It does not project a closed-mask row,
does not reopen the environment state, and does not depend on an accepted
release already happening.

## Source Contract

The follow-on implementation should add a source with this contract:

| Condition | Required behavior |
| --- | --- |
| A5 state/mask | Only active while the real observation is `AuthorizedReady` and `fire_once` is legal/open. |
| First event | Only before the first accepted `fire_once` in the episode window. |
| Quality gate | Requires the existing launch-window quality predicate to be enabled and true, with the configured minimum window age satisfied. |
| Target | `target=1.0`, positive event credit for firing from the current legal-open state. |
| Weight | Controlled by an explicit opportunity weight; default off outside active A7 configs. |
| Source id | `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`, separate from `DEADLINE` and `SHADOW_QUALITY`. |

Priority should be:

1. Accepted quality release keeps the existing accepted-source path.
2. Early accepted release keeps early-negative plus `shadow_quality` repair.
3. No-release legal-open quality rows become `LEGAL_OPEN_QUALITY` positives.
4. `DEADLINE` remains a late fallback and diagnostic source, not the primary
   quality-window teacher.

If `launch_window_open` is absent, legal-open opportunity credit must remain
disabled by default. Broad censored-survival positives are not allowed as a
stand-in for this source.

## Loss Contract

The loss split after P should be:

| Signal | Source | Observation legality | Trains value | Trains event-logit delta |
| --- | --- | --- | --- | --- |
| Prewindow hold | `PREWINDOW` | legal-open | negative | yes |
| Early accepted | `EARLY_ACCEPTED` | legal-open at sampled early release | negative | yes |
| Legal-open opportunity | `LEGAL_OPEN_QUALITY` | legal-open | positive | yes |
| Late fallback | `DEADLINE` | legal-open | positive | yes, but separately diagnosed |
| Shadow repair | `SHADOW_QUALITY` | closed-mask raw row | raw value/projection candidate only | no on raw row; yes only on projected legal-open sample |

`LEGAL_OPEN_QUALITY` should enter the ordinary A7 value/delta path because the
sample itself is legal-open. It must not be routed through the projection helper.
`SHADOW_QUALITY` keeps the M behavior: raw closed-mask rows cannot train direct
event-logit delta, but they may create projected legal-open positives.

## Diagnostics Contract

The follow-on prototype must expose enough counters to prove that the new signal
is not starved:

- `a7/evc_src_legal_open_quality_count_mean`
- source-specific positive counts for `LEGAL_OPEN_QUALITY`, `DEADLINE`, and
  `SHADOW_QUALITY`
- source-specific event advantage mean for legal-open quality rows
- projection candidate count remains tied to `SHADOW_QUALITY`
- rollout/probe summaries distinguish no-release quality opportunity rows from
  post-release shadow rows

The acceptance question after implementation is not merely whether ordinary A7
is live. It is whether train rollouts contain legal-open quality positives before
the policy samples early release.

## Implementation Entry Points

Expected follow-on write surfaces:

- `python/rl/policy_algo/first_event_hazard.py`
  - add `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`;
  - add explicit opportunity-weight/min-age knobs to
    `build_first_event_hazard_labels()`;
  - emit positive labels for no-release legal-open quality rows.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - include the new source in source diagnostics;
  - keep delta alignment allowed for this source because it is legal-open;
  - keep projection candidates restricted to `SHADOW_QUALITY`.
- `python/rl/support/nonfinite_probe.py`
  - mirror the new source metrics in the patched train path.
- Active A7 config and callback/process-probe diagnostics:
  - expose the new opportunity weight and count metrics;
  - keep defaults off outside the active A7 experiment config.
- Focused tests:
  - no-release quality window creates `LEGAL_OPEN_QUALITY` positives;
  - prewindow rows remain negative;
  - early accepted release still creates `EARLY_ACCEPTED` negatives and
    `SHADOW_QUALITY` repair candidates;
  - delta alignment is allowed for legal-open opportunity rows and still blocked
    for raw shadow rows;
  - source counters reach logger/probe metrics.

## Validation Gates

Before another learned-policy training wave:

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
git diff --check -- docs/task/air_combat python/rl tests/hmoe tests/training
```

The first short learned-policy probe after those gates should report:

- deterministic request/release timing;
- stochastic request/release timing and one-shot violations;
- `LEGAL_OPEN_QUALITY`, `DEADLINE`, and `SHADOW_QUALITY` source counts;
- legal-open quality advantage sign;
- projection candidate/active counts.

## Rollback Gates

Re-scope or roll back the opportunity source if:

- positive labels appear when `fire_once` is not legal-open;
- stochastic near-immediate release probability increases before the quality
  gate opens;
- raw `SHADOW_QUALITY` rows regain direct event-logit delta alignment;
- the new source is active without `launch_window_open` evidence;
- A3/A5 masks, one-shot suppression, or shot-budget discipline are weakened.

## Non-Goals

- Do not implement this contract in P; the implementation candidate is the next
  slice.
- Do not weaken A3/A5 masks or make `FiredAssess` fireable again.
- Do not use broad censored no-release rows as positive labels.
- Do not treat this as HMoE redesign, M2 release, missile authority, `2v2`,
  self-play, or real doctrine.
- Do not run another learned-policy wave until focused source/loss diagnostics
  pass.

## Dispatch Result

`A7-EVC-P` selects direct legal-open quality opportunity credit as the next
non-starved teaching signal. The next implementation candidate is
`A7-EVC-Q Legal-Open Opportunity Credit Prototype`.
