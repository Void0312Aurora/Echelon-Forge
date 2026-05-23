# WP14-F Compatibility Validation And Acceptance Handoff

Status: `2026-05-21` planned / serial closure lane. Do not create an
acceptance review yet; WP14 first slice is still open/planned.

Language:

- English canonical: `wp14_compatibility_validation_acceptance_cluster_20260521.md`
- Chinese companion:
  [wp14_compatibility_validation_acceptance_cluster_20260521.zh.md](wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)

Inputs:

- [WP14 capability composition](capability_composition_wp14_20260521.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.md)
- [WP14-D additive facade setup DTO](wp14_additive_facade_setup_dto_cluster_20260521.md)
- [WP14-E capability effects materialization](wp14_capability_effects_materialization_cluster_20260521.md)
- [Post-WP9 architecture route plan](../post_wp9_architecture_route_plan_20260520.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

`WP14-F` is the serial compatibility and acceptance handoff lane. It reconciles
A-E, verifies that `type_name` compatibility survived capability composition,
records validation outcomes, publishes residuals, and prepares the acceptance
review.

It should not block A-E from reaching `Mergeable`. It runs after implementation
evidence exists.

Parallel rule:

- This lane is serial and owned by the main integration thread.
- Do not let subagents write acceptance text concurrently with A-E
  implementation workers on the same normative table.

## 2. Scope

In scope:

- verify A-E touched files, commands, blockers, and residuals;
- run or record final validation commands;
- prove compatibility for `spawn_unit(type_name)`, `WorldSpawnRequest`, and
  facade setup;
- update simulation architecture README/index entries;
- update post-WP9 route status from Phase 5 opened to accepted only when
  implementation evidence supports that status;
- publish English and Chinese acceptance review when gates pass;
- ensure final commit messages use capability/result language and avoid
  internal WP labels.

Out of scope:

- hiding failed or blocked validation;
- accepting documentation-only output as implementation closure;
- claiming full spawn-platform migration, backend/fidelity promotion, scenario
  schema replacement, or new tactical behavior.

## 3. Acceptance Packet Checklist

The final handoff must include:

| Item | Required content |
|------|------------------|
| Gate verdict table | A-E pass/fail/blocked with one-line evidence. |
| Validation commands | Exact command, status, and short outcome. |
| Compatibility statement | Explicit note that `spawn_unit(type_name)` and `WorldSpawnRequest.type_name` remain maintained compatibility surfaces. |
| Runtime surface summary | New contracts, lowering helpers, bridge points, DTOs, and evidence fields. |
| Residual register | Named residuals with owner, reason, and next-phase recommendation. |
| Index sync | README, route plan, review index, and bilingual companions checked. |
| Commit-message note | Final suggested commit title avoids internal work-package labels. |

## 4. Validation Commands

Expected final validation set:

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_*.py
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or capabilities or observation_packet"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\test_gpu_runtime_bindings.py -k "runtime_capabilities"
python tools\maintenance\wp_doc_closure_audit.py --wp WP14
```

Minimum acceptance gates for this lane:

- all A-E implementation gates are already mergeable;
- `git diff --check` and the listed validation commands are recorded with exact
  outcomes;
- README, route, and review indices are synchronized;
- `spawn_unit(type_name)` and `WorldSpawnRequest.type_name` compatibility is
  stated explicitly;
- no acceptance review is drafted until A-E are genuinely mergeable.

If a command is blocked by environment, record the blocker and the narrowest
substitute evidence. Do not mark the gate accepted on unrun tests without a
reason.

## 5. Review Draft Requirements

Create only when gates pass:

- `docs/task/review/wp14_capability_composition_acceptance_review_20260521.md`
- `docs/task/review/wp14_capability_composition_acceptance_review_20260521.zh.md`

The review must state:

- accepted scope and non-scope;
- gate verdicts for A-E;
- validation outcomes;
- exact compatibility guarantees that remain maintained;
- residuals for future public `spawn_platform`, scenario schema migration,
  deeper capability effects, and full platform-family expansion;
- recommended next phase: counterfactual and experiment generation only after
  capability composition gates are accepted.

## 6. Handoff Contract

Return:

- final status for A-F;
- files touched during integration/closure;
- exact commands run and outcomes;
- acceptance review links if created;
- residuals and recommended next action;
- suggested capability/result-oriented commit message, without `WP14`.
