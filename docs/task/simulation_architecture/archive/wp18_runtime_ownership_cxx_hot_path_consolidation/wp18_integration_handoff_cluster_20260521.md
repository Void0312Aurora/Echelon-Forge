# WP18-F Integration And Handoff

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp18_integration_handoff_cluster_20260521.md`
- Chinese companion:
  [wp18_integration_handoff_cluster_20260521.zh.md](wp18_integration_handoff_cluster_20260521.zh.md)

Inputs:

- [WP18 main plan](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18 dispatch queue](wp18_subagent_dispatch_queue_20260521.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

## Purpose

Own the serial integration lane after WP18-A through WP18-E return. This stream
does not implement the main runtime slices. It verifies integration, records
residuals, synchronizes indexes, and creates an acceptance review only after
implementation evidence exists.

## Scope

In scope:

- collect worker return packets and reconcile conflicting residuals;
- run focused and closure validation;
- update WP18 docs, README entries, review indexes, and bilingual companions;
- create acceptance review only after implementation gates pass;
- route residuals to WP19/WP20/WP21 without opening extra stages.

Out of scope:

- parallel edits to the same normative tables while workers are active;
- accepting planned docs as implementation evidence;
- broad runtime refactors.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `F1` | Worker result rollup | A-E statuses, touched files, commands, blockers, and residuals are summarized. |
| `F2` | Validation rollup | Exact commands and outcomes are recorded. |
| `F3` | Residual routing | Remaining blockers are assigned to WP19, WP20, WP21, or retained compatibility. |
| `F4` | Closure docs | README/review/bilingual docs are synced, and acceptance review is created only after gates pass. |

## Suggested Validation

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
```

## Handoff

Return acceptance decision, exact validation outcomes, residual register,
documentation sync status, and whether WP19 entry conditions are satisfied.
