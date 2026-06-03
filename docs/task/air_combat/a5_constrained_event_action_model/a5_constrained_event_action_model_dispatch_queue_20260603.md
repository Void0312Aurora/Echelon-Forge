# A5 Constrained Event Action Model Dispatch Queue

Status: `2026-06-03` ready queue for future work packets. No work is currently
delegated.

Parent: [README.md](README.md) and
[task clusters](a5_constrained_event_action_model_task_clusters_20260603.md).

## Queue

| Packet | Cluster | Status | Write set | Expected output | Validation |
| --- | --- | --- | --- | --- | --- |
| `A5-DQ-001 Surface Audit` | `A5-EAM-B Surface Audit` | ready | A5 docs only, optional read-only scan notes | Touchpoint map for action, observation, reward, policy, config, diagnostics, and tests. | markdown link check; no runtime edits |
| `A5-DQ-002 Contract Draft` | `A5-EAM-C Event Contract` | blocked on DQ-001 | `docs/standards/air/act*.md`, A5 docs | Stable field names and event-state transition table. | contract tests proposed or implemented |
| `A5-DQ-003 Runtime Prototype` | `A5-EAM-D Runtime State Machine` | blocked on DQ-002 | `gym_envs/**`, `scenarios/air_combat/1v1/**`, runtime tests | Fire-once state transition and post-launch suppression. | focused runtime tests |
| `A5-DQ-004 Policy Prototype` | `A5-EAM-E Policy Event Head` | blocked on DQ-002 | `python/rl/policy_algo/**`, HMoE/policy tests | Masked event distribution or event Q-head prototype. | forward/evaluate/log-prob tests |
| `A5-DQ-005 Evidence Packet` | `A5-EAM-G Diagnostics And Evidence` | blocked on DQ-003/DQ-004 | diagnostics tools, A5 evidence docs | Deterministic/stochastic event-action evidence. | diagnostics tests and probe logs |

## Dispatch Notes

- Do not create new conversation threads. If the current session offers
  subagents, packets may be delegated inside the current session only.
- Do not stage or commit `experiments_tmp`.
- Keep `A5-DQ-002` serial with implementation packets because field names become
  contract inputs.
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
