# M3 Optimal-Stopping Model Selection Dispatch Queue

Status: `2026-06-05` active dispatch queue for
[M3 Optimal-Stopping Model Selection](README.md).

## Dispatch Boundary

This queue distributes research only. Workers produce one document each under a
disjoint write set. They do not edit implementation code, parent indexes, or
status lines outside their assigned packet.

## Packets

| Packet | Cluster | Worker scope | Required output | Write set | Search policy | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `M3-R1` | `M3-R1 Self-Designed Algorithm` | Design algorithms directly from the formal problem using reasoning only. | Self-contained algorithm-design note with objectives, pseudo-code, failure modes, and recommendation. | `m3_self_designed_algorithm_probe_20260605.md` | No web search. No external citations required. | pass |
| `M3-R2` | `M3-R2 Academic Literature Survey` | Search academic sources for model families related to censored optimal stopping, survival RL, event-time prediction, and sequence decision models. | Literature survey with source links, short summaries, and fit-to-M3 analysis. | `m3_academic_literature_model_survey_20260605.md` | Web/academic search allowed; prefer primary sources. | pass |
| `M3-R3` | `M3-R3 Existing Model-Family Fit Survey` | Survey practical candidate model families and toolable designs, including how each would fit the current repo constraints. | Model-family fit note with implementation risk, data needs, and recommendation. | `m3_existing_model_family_fit_survey_20260605.md` | Web search allowed when useful; local repo inspection allowed. | pass |

## Common Worker Context

All workers should read:

- [README.md](README.md)
- [m3_formal_problem_statement_20260605.md](m3_formal_problem_statement_20260605.md)
- [m3_optimal_stopping_model_selection_task_clusters_20260605.md](m3_optimal_stopping_model_selection_task_clusters_20260605.md)

Workers should treat A7 evidence as the motivating failure case, not as a
required military-domain framing.

## Return Packet

Each worker final response should include:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Integration Notes

- The main thread owns
  [m3_model_selection_synthesis_20260605.md](m3_model_selection_synthesis_20260605.md).
- If a worker finds that the formal problem is malformed, it should record that
  as a critique inside its assigned document instead of editing the formal
  problem statement.
- If a worker cannot complete research within one round, it should mark the
  packet `partial` with concrete missing evidence.
