# A7 Dispatch Queue

Status: `2026-06-04` A7 is open. The objective contract is selected, and
`A7-EVC-C Policy Head Prototype` plus `A7-EVC-D PPO Auxiliary Credit` have
passed. The active queue now moves to config and diagnostics.

Parent: [README.md](README.md). Task clusters:
[a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md).

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A7-EVC-E Config And Diagnostics` | planned next | implementation worker; expose A7 coeffs in an active entry and add callback/process-probe metrics for credit loss, advantage signs, and cumulative early-fire hazard. | active configs, diagnostics/callback tests, docs. | No learned-policy run until config and diagnostics tests pass. |

## Completed Dispatches

| Cluster | Result | Evidence | Residual |
| --- | --- | --- | --- |
| `A7-EVC-C Policy Head Prototype` | pass | `hybrid_event_credit_head_lr_scale`, `get_hybrid_event_credit()`, distribution-side `fire_event_q_values()` / `fire_event_advantage()`, default-disabled and A6-coexistence tests. | Head is exposed only; PPO loss coupling remains `A7-EVC-D`. |
| `A7-EVC-D PPO Auxiliary Credit` | pass | `compute_first_event_credit_loss()`, A7-only label collection, PPO loss coupling, optional delta alignment, focused gradient/PPO tests. | Active config and diagnostics remain `A7-EVC-E`. |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| `A7-EVC-G Short Learned Evidence` | Needs implementation validation. | `A7-EVC-F` passes. |

## Dispatch Packet Template

```md
cluster: A7-EVC-*
scope:
write set:
non-goals:
validation:
return packet:
```

## Integration Notes

- Do not create separate conversation sessions for this work.
- `A7-EVC-A/B` are closed by
  [the objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.md).
- `experiments_tmp` stays out of staging.
- Keep A3/A5 legality authoritative.
- Keep M2 and HMoE redesign held unless a separate release vote or issue task
  is created.
