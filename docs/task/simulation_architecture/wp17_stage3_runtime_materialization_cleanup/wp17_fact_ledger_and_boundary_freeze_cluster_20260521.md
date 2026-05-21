# WP17-A Fact Ledger And Boundary Freeze

Status: `2026-05-21` recovered / pass; current code facts locked for the
implementation waves.

Inputs:

- [WP17 main plan](stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [Stage 3 platform expansion plan](../../review/stage3_platform_expansion_mainline_plan_20260521.md)
- [WP16 acceptance review](../../review/wp16_runtime_spine_consolidation_acceptance_review_20260521.md)

## Purpose

Freeze the current code facts before implementation workers start. This stream
prevents later work from planning from stale Stage 3 assumptions.

## Scope

In scope:

- verify the six code facts in the WP17 main plan;
- identify current maintained, compatibility, diagnostics-only, and blocked
  surfaces for runtime capabilities, batch/training reads, scheduler cadence,
  capability spawn, and counterfactual runtime;
- keep the first-wave dispatch board synchronized with dependency and model
  rules;
- add or update architecture guard inventory only if needed.

Out of scope:

- runtime behavior changes;
- public API removal;
- README or acceptance closure.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `A1` | Verify code-fact ledger | Each fact links to concrete source/test files and names any drift from the Stage 3 plan. |
| `A2` | Residual register | Every blocked residual has owner stream, reason, and next trigger. |
| `A3` | Dispatch board sync | First-wave tasks include model/reasoning budgets, dependencies, and write scopes. |
| `A4` | Guard inventory | Existing guards are sufficient or missing guard candidates are named without changing runtime code. |

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
python -m pytest -q tests/architecture/test_wp16_legacy_path_gates.py
```

## Handoff

Return touched files, verified facts, residual IDs, commands run, and whether
any implementation stream should be blocked before code edits begin.
