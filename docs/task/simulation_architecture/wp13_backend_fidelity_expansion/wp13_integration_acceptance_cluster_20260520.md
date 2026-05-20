# WP13-F Integration And Acceptance Handoff

Status: `2026-05-20` planned / serial closure lane.

Language:

- English canonical: `wp13_integration_acceptance_cluster_20260520.md`
- Chinese companion:
  [wp13_integration_acceptance_cluster_20260520.zh.md](wp13_integration_acceptance_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP13-A runtime capability query](wp13_runtime_capability_query_cluster_20260520.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.md)
- [WP13-D fidelity profile request gate](wp13_fidelity_profile_request_gate_cluster_20260520.md)
- [WP13-E facade and binding proof](wp13_facade_binding_proof_cluster_20260520.md)
- [Post-WP9 architecture route plan](../post_wp9_architecture_route_plan_20260520.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

`WP13-F` is the serial integration and acceptance handoff lane. It reconciles
the A-E implementation streams, records exact validation outcomes, publishes
the residual register, and prepares the acceptance review.

It should not block A-E from reaching `Mergeable`. It runs after implementation
evidence exists.

## 2. Scope

In scope:

- verify A-E touched files, commands, blockers, and residuals;
- run or record final validation commands;
- update simulation architecture README/index entries;
- update post-WP9 route status from Phase 4 planned to active/accepted only
  when implementation evidence supports that status;
- publish English and Chinese acceptance review when gates pass;
- ensure final commit messages use capability/result language and avoid
  internal WP labels.

Out of scope:

- editing A-E implementation semantics without being assigned integration
  ownership;
- hiding failed or blocked validation;
- claiming exact GPU, resident-state, shadow, adaptive fidelity, or learned
  provider support;
- accepting documentation-only output as implementation closure.

## 3. Acceptance Packet Checklist

The final handoff must include:

| Item | Required content |
|------|------------------|
| Gate verdict table | A-E pass/fail/blocked with one-line evidence. |
| Validation commands | Exact command, status, and short outcome. |
| Runtime surface summary | New DTOs/helpers/fields and compatibility impact. |
| Conservative support statement | Explicit note that unsupported backend/fidelity support remains false. |
| Residual register | Named residuals with owner, reason, and next-phase recommendation. |
| Index sync | README, route plan, review index, and bilingual companions checked. |
| Commit-message note | Final suggested commit title avoids internal work-package labels. |

## 4. Validation Commands

Expected final validation set:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_runtime_facade_layering.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP13
```

If a command is blocked by environment, record the blocker and the narrowest
substitute evidence. Do not mark the gate accepted on unrun tests without a
reason.

## 5. Review Draft Requirements

Create:

- `docs/task/review/wp13_backend_fidelity_expansion_acceptance_review_20260520.md`
- `docs/task/review/wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md`

The review must state:

- accepted scope and non-scope;
- gate verdicts for A-E;
- validation outcomes;
- exact unsupported support claims that remain false;
- residuals for future exact GPU, resident-state, shadow, adaptive fidelity,
  `ModelProvider`, and capability composition work;
- recommended next phase: capability composition only if backend/fidelity query
  and rejection gates are accepted.

## 6. Handoff Contract

Return:

- final status for A-F;
- files touched during integration/closure;
- exact commands run and outcomes;
- acceptance review links if created;
- residuals and recommended next action;
- suggested capability/result-oriented commit message, without `WP13`.
