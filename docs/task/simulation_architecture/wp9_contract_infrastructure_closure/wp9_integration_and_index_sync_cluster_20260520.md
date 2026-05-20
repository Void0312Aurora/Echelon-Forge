# WP9-E Integration And Index Sync

Status: `2026-05-20` complete / accepted serial WP9 integration stream.

Language:

- English canonical: `wp9_integration_and_index_sync_cluster_20260520.md`
- Chinese companion:
  [wp9_integration_and_index_sync_cluster_20260520.zh.md](wp9_integration_and_index_sync_cluster_20260520.zh.md)

Inputs:

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.md)
- [WP9-A DTO promotion batch 1](wp9_dto_promotion_batch1_cluster_20260520.md)
- [WP9-B DTO promotion batch 2](wp9_dto_promotion_batch2_cluster_20260520.md)
- [WP9-C infrastructure closure](wp9_infrastructure_closure_cluster_20260520.md)
- [WP9-D guard enforcement](wp9_guard_enforcement_cluster_20260520.md)
- Worker handoff notes from completed subagents.

## 1. Purpose

WP9-E is the single serial publication pass after A-D. It owns shared binding
glue, CMake/module reconciliation, README/index updates, bilingual alignment,
and final acceptance evidence.

## 2. Preconditions

WP9-E should not start until:

1. WP9-A, WP9-B, WP9-C, and WP9-D have each returned touched files and
   validation results.
2. Any shared edit conflict has a known owner.
3. Binding/CMake changes from DTO streams are either already merged or listed
   as integration work.
4. No worker leaves an untracked residual without a named owner.

## 3. Required Integration Work

| Item | Required output |
|------|-----------------|
| Shared contract includes | Ensure DTO headers are reachable from facade and bindings without circular or engine-owner includes. |
| Python binding glue | Reconcile A/B binding additions, module declarations, and focused smoke tests. |
| README/index sync | Update simulation architecture README and Chinese companion with final WP9 status and links. |
| Architecture cross references | Add or update references for promoted DTOs, diagnostics facade, guard allowlist, and infrastructure closure. |
| Acceptance review | Publish `wp9_contract_infrastructure_closure_acceptance_review_20260520.md` and `.zh.md`. |
| Validation | Run or record blocked status for doc checks, architecture tests, binding smoke, and focused runtime tests. |

## 4. Acceptance Review Shape

The final review must include:

1. Gate-by-gate verdicts for WP9-A through WP9-E.
2. Evidence rows for DTO-1 through DTO-8, INF-1 through INF-7, and GUA-1/GUA-2.
3. Exact validation commands and outcomes.
4. Residual risks, if any, with owners and next work package labels.
5. Bilingual alignment statement.

## 5. Non-Goals

- Do not introduce new WP10+ scope during WP9-E.
- Do not hide blocked runtime validation behind passing doc checks.
- Do not rewrite worker-owned implementation beyond resolving integration
  conflicts.
- Do not mark WP9 accepted until the acceptance review exists in both
  languages.

## 6. Validation Commands

```bash
git diff --check
pytest tests/architecture tests/runtime/bindings tests/runtime/engagement tests/runtime/facade
rg -n "WP9|Contract And Infrastructure Closure|RewardReport|TerminationSpec|ObservationViewSpec|ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|DiagnosticsTrace|StageNodeManifest|sim\\.\\*" docs/task/simulation_architecture docs/task/review docs/plan/architecture src tests
```
