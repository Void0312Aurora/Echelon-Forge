# A7 Acceptance Gate

Status: `2026-06-04` defined; `A7-EVC-C` policy-head prototype evaluated.

Parent: [README.md](README.md).

## Accepted Scope Target

A7 acceptance is limited to proving that an event-value / advantage-credit
mechanism can teach first-event timing under the existing A3/A5 legal event
surface.

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | A7 target gives counterfactual hold/fire credit and names target source. | pass: [objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.md) |
| Policy head prototype | Head shape, zero init, optimizer lane, default-off behavior, serialization/load, and A6 coexistence are tested. | pass: `tests/hmoe/test_hmoe_policy.py` |
| PPO implementation | Loss, masks, stats, and deterministic eval are tested. | not started: owned by `A7-EVC-D` |
| Legality boundary | A3/A5 masks and state machine remain authoritative. | required |
| HMoE risk handling | HMoE gap is considered in head placement and diagnostics. | partial: A7-C keeps credit at policy-head level and does not redesign HMoE |
| Learned evidence | Deterministic fires once inside quality window; stochastic early hazard is bounded. | not evaluated |
| Overclaim refusal | M2, HMoE redesign, missile authority, `2v2`, self-play, and doctrine remain held. | required |

## Failure Conditions

A7 remains held or must be re-scoped if:

- the implementation only changes L weights or generic reward magnitude;
- the advantage head is diagnostic-only and does not affect event logits or
  policy updates;
- early stochastic release still censors quality-window targets without a
  counterfactual repair;
- deterministic fires near-immediately after authorization/contact again;
- stochastic probing violates one-shot release discipline;
- HMoE gap is used to justify a broad architecture rewrite without A7 evidence.

## Validation Commands

Initial docs gate:

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

Implementation gates selected by `A7-EVC-B`:

- policy head shape, zero initialization, and constructor serialization tests;
- first-event credit label tests for pre-quality, quality, early accepted, and
  shadow-quality cases;
- PPO auxiliary-loss finite-value and mask-handling tests;
- diagnostics tests for event advantage signs and cumulative pre-window hazard;
- active config parsing and focused compile/JSON gates.

`A7-EVC-C` focused gates:

```bash
python -m compileall -q python/rl/policy_algo/policies.py
pytest tests/hmoe/test_hmoe_policy.py -q
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py
```

Observed outcome: compileall passed; HMoE policy tests passed with `31 passed`;
A6 event-head update-strength tests passed with `3 passed`; diff whitespace check
passed.
