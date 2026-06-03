# A5 Constrained Event Action Model Dispatch Queue

Status: `2026-06-03` dispatch queue. `A5-DQ-001` through `A5-DQ-006` returned
`pass`; short learned-policy evidence is recorded as held. `A5-DQ-007`
returned a read-only `partial` closure-readiness audit and is ready for held
closure sync.

Parent: [README.md](README.md) and
[task clusters](a5_constrained_event_action_model_task_clusters_20260603.md).

## Queue

| Packet | Cluster | Status | Write set | Expected output | Validation |
| --- | --- | --- | --- | --- | --- |
| `A5-DQ-001 Surface Audit` | `A5-EAM-B Surface Audit` | pass: `Lagrange` packet accepted | A5 docs only, optional read-only scan notes | Touchpoint map for action, observation, reward, policy, config, diagnostics, and tests. | read-only audit accepted |
| `A5-DQ-002 Contract Draft` | `A5-EAM-C Event Contract` | pass | `docs/standards/air/act*.md`, A5 docs | Stable field names and event-state transition table. | contract docs frozen; focused tests pending in D/E |
| `A5-DQ-003 Runtime Prototype` | `A5-EAM-D Runtime State Machine` | pass: `Noether` packet accepted | `gym_envs/**`, `scenarios/air_combat/1v1/**`, runtime tests | Fire-once state transition and post-launch suppression. | focused runtime tests |
| `A5-DQ-004 Policy Prototype` | `A5-EAM-E Policy Event Head` | pass: `Hume` packet accepted | `python/rl/policy_algo/**`, HMoE/policy tests | Masked event distribution or event Q-head prototype. | forward/evaluate/log-prob tests |
| `A5-DQ-005 Reward Config Cleanup` | `A5-EAM-F Reward And Config Cleanup` | pass: `Noether` packet accepted | reward runtime/config tests and active S1 C2/ROE configs | Align reward/config defaults with event-action semantics. | reward/config focused tests |
| `A5-DQ-006 Evidence Packet` | `A5-EAM-G Diagnostics And Evidence` | pass: `Hume` packet accepted for diagnostics implementation; learned probes still pending | diagnostics tools, A5 evidence docs | Deterministic/stochastic event-action evidence. | diagnostics tests and probe logs |
| `A5-DQ-007 Closure Readiness` | `A5-EAM-H Acceptance And Closure` | partial: `Lagrange` read-only pre-audit accepted as readiness input; held closure sync pending | A5/A3/A4/M1/M2 docs and parent air-combat indexes | Accepted-or-held closure map with explicit residuals. | focused test suite, docs check, evidence review |

## Dispatch Notes

- Do not create new conversation threads. If the current session offers
  subagents, packets may be delegated inside the current session only.
- `A5-DQ-001` was read-only and is now accepted as planning evidence.
- Do not stage or commit `experiments_tmp`.
- Keep `A5-DQ-002` serial with implementation packets because field names become
  contract inputs.
- `A5-DQ-003` and `A5-DQ-004` ran in parallel through disjoint write sets and
  returned `pass`.
- `A5-DQ-005` returned `pass` and was locally revalidated by the main thread.
- `A5-DQ-006` returned `pass` for diagnostics implementation and was locally
  revalidated by the main thread.
- Short learned-policy evidence is now available and narrows A5 to a held
  event-value / first-event timing residual.
- `A5-DQ-007` should close A5 as held after cross-doc sync, not accepted.
- A packet that cannot close within its round cap should return `partial` and a
  narrowed residual instead of opening a new wave.

## Packet Template

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```
