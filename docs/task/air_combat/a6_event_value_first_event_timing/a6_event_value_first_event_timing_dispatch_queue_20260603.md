# A6 Dispatch Queue

Status: `2026-06-03` first/deadline waves, event-head update audit, and
event-head optimization learned evidence are complete. A6 remains held on
launch-window timing quality.

Parent: [README.md](README.md). Cluster plan:
[a6_event_value_first_event_timing_task_clusters_20260603.md](a6_event_value_first_event_timing_task_clusters_20260603.md).

## Completed Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A6-EVT-B Mathematical Framing` | pass | Arendt returned a complete packet. | Framing notes and README links. | No code/config/scenario/test changes. |
| `A6-EVT-C Objective Contract` | pass | Arendt returned a complete packet. | Objective contract notes. | No code/config/scenario/test changes. |
| `A6-EVT-D Training Kernel Prototype` | pass | Arendt returned a complete packet. | `python/rl/policy_algo/**` and focused policy/training tests. | No config/probe/callback/scenario changes. |
| `A6-EVT-E Scenario Config And Diagnostics` | pass | Arendt returned E; main thread completed runtime/rollout integration blockers. | Active configs, diagnostics, world-batch runtime info, non-finite probe parity, focused tests. | A3/A5 legality remains mask/state-owned. |
| `A6-EVT-F Short Learned Evidence` | pass; held outcome | Main thread ran `32768`-step train plus deterministic/stochastic probes. | Evidence note only; `experiments_tmp` not staged. | Deterministic not fixed; stochastic discipline preserved. |
| `A6-EVT-G Closure And Index Sync` | pass; re-scoped | Main thread plus Arendt read-only check converged on deadline bootstrap as the next bounded wave. | A6 docs, parent indexes as needed. | A6 remains held; M2 remains held. |
| `A6-EVT-H Deadline Bootstrap Implementation` | pass | Main thread implemented deadline labels/config/logging and tests. | A6 label/PPO/logging code, separate active config, focused tests, A6 docs. | A3/A5 masks preserved; fixed-age teacher not accepted as doctrine. |
| `A6-EVT-I Deadline Short Learned Evidence` | pass; held outcome | Main thread ran `32768`-step deadline train plus deterministic/stochastic probes. | Evidence note only; `experiments_tmp` not staged. | Deterministic still 0 requests; stochastic has 1 rejected request but 0 violation/repeat/budget issues. |
| `A6-EVT-J Event-Head Update-Strength Audit` | pass; held outcome | Main thread audited A6 loss/optimizer routing and added a focused update-strength diagnostic test. | `tests/hmoe/test_a6_event_head_update_strength.py`, A6 evidence note. | Diagnostic only; A6 still held and M2 still held. |
| `A6-EVT-K Event-Head Optimization Lane` | pass; held timing residual | Main thread added dedicated zero-initialized event-head optimizer lane, diagnostics, focused tests, separate active config, and short learned evidence. | `python/rl/policy_algo/policies.py`, focused tests, active config, A6 docs/evidence. | Deterministic crossing is proven, but release timing is near-immediate; A6 and M2 held. |

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A6-EVT-L Launch-Window Timing Contract` | planned next | Main thread or future worker; design first. | A6 contract/status docs first; code/config only after contract acceptance. | Separate authorization from good launch timing; keep A3/A5 masks authoritative and M2 held. |

## Completed Blockers

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| `A6-EVT-F Short Learned Evidence` | Needed implementation tests. | Unblocked and completed; result is held. |
| `A6-EVT-G Closure And Index Sync` | Needed learned evidence. | Unblocked by F and completed as re-scope. |
| `A6-EVT-H Deadline Bootstrap Implementation` | Needed re-scope decision. | Unblocked by G and completed. |
| `A6-EVT-I Deadline Short Learned Evidence` | Needed deadline implementation tests. | Unblocked by H and completed; result is held. |
| `A6-EVT-J Event-Head Update-Strength Audit` | Needed deadline evidence. | Unblocked by I and completed; result is held. |
| `A6-EVT-K Event-Head Optimization Lane` | Needed update-strength diagnosis and learned evidence. | Unblocked by J and completed as held timing residual. |
| `A6-EVT-L Launch-Window Timing Contract` | Needs K evidence. | Unblocked by K; ready for design/contract packet. |

## Dispatch Packet Template

```md
cluster: A6-EVT-*
model / reasoning:
scope:
write set:
non-goals:
validation:
return packet:
```

## Integration Notes

- Do not create separate conversation sessions for this work.
- If subagents are used, map each worker to one cluster and follow
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).
- Keep `experiments_tmp` out of staging.
- Keep M2 held unless A6 evidence later creates an explicit release vote.
