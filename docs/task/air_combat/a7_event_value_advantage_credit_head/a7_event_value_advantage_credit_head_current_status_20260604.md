# A7 Current Status

Status: `2026-06-04` active implementation. A7 has selected its objective
contract and completed `A7-EVC-C Policy Head Prototype`; PPO auxiliary credit is
the next implementation slice.

Parent: [README.md](README.md).

## Checkpoint

- A3 has been archived as an accepted C2/ROE evidence packet and remains
  reachable through a pointer README.
- A6 remains held after root-cause analysis; L tuning is paused.
- A7 is opened to implement counterfactual event-value / advantage credit.
- The objective contract is now selected:
  [a7_event_value_advantage_credit_head_objective_contract_20260604.md](a7_event_value_advantage_credit_head_objective_contract_20260604.md).
- `A7-EVC-C Policy Head Prototype` is complete: the zero-safe
  `hybrid_event_credit_head` API is exposed and covered by focused HMoE policy
  tests.
- The HMoE hierarchical computation gap is recorded as an architecture risk:
  A7 should not rely solely on hard-routed subexpert behavior.

## Maturity Matrix

| Surface | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A7 docs | active | README/task clusters/current status/dispatch/acceptance/objective contract exist. | Documentation and dispatch surface only. |
| Objective contract | pass | The selected contract defines counterfactual target semantics, window balancing, head placement, loss coupling, diagnostics, and rollback gates. | It authorizes focused implementation, not broad architecture release. |
| Policy head prototype | pass | `python/rl/policy_algo/policies.py` exposes `hybrid_event_credit_head_lr_scale`, `get_hybrid_event_credit()`, and distribution-side credit values; `tests/hmoe/test_hmoe_policy.py` covers default-off, zero init, optimizer lane, A6 coexistence, load smoke, and bootstrap zeroing. | No PPO auxiliary loss or training claim. |
| PPO implementation | not started | Entry points remain `first_event_hazard.py` and `ppo_adaptive_kl.py`. | `A7-EVC-D` owns loss coupling and target handling. |
| HMoE relation | watch item | Issue board documents flat subexpert input and combat-family collapse. | A7 does not repair HMoE unless evidence forces a new task. |

## Immediate Next Step

Dispatch `A7-EVC-D PPO Auxiliary Credit`: train the A7 head and couple the
advantage signal to event-logit updates without weakening A3/A5 masks.

## Validation Snapshot

- `python -m compileall -q python/rl/policy_algo/policies.py`: pass.
- `pytest tests/hmoe/test_hmoe_policy.py -q`: pass, `31 passed`.
- `pytest tests/hmoe/test_a6_event_head_update_strength.py -q`: pass,
  `3 passed`.
- `git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py`: pass.

## Held Items

- M2 release.
- HMoE redesign or soft routing.
- Missile/Pk/fuze/damage authority.
- `2v2`, self-play, and real doctrine.
