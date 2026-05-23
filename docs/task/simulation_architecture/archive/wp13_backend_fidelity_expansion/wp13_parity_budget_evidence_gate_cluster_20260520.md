# WP13-C Parity Budget Evidence Gate

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp13_parity_budget_evidence_gate_cluster_20260520.md`
- Chinese companion:
  [wp13_parity_budget_evidence_gate_cluster_20260520.zh.md](wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP6 parity budget registry](../wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md)
- [WP7 promotion evidence gates](../wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md)
- [WP5 validation harness](../wp5_validation_harness/validation_harness_wp5_20260519.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)

## 1. Purpose

`WP13-C` turns parity budgets into code-owned evidence gates. A backend profile
cannot be treated as maintained unless its profile-owned parity budget is
present, class-compatible, and accepted for the requested capability.

The first implementation should preserve `cpu_exact.reference` as the only
maintained exact baseline budget. Candidate exact GPU, resident-state, and
shadow budgets remain unavailable for maintained promotion.

## 2. Scope

In scope:

- add a small parity budget record/schema/helper under a runtime contract owner;
- encode the accepted budget ids needed by the first profile gate;
- validate profile/budget class compatibility;
- validate comparison domains, sync barriers, diagnostics requirements,
  mismatch policy, and acceptance gate presence;
- return stable rejection reasons for missing, candidate, diagnostics-only, or
  incompatible budgets.

Out of scope:

- implementing numeric comparator engines;
- executing backend comparisons;
- changing backend support booleans to true;
- adaptive fidelity scheduling;
- writing the backend profile registry rows owned by `WP13-B`, except by
  agreed integration.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/`
- `src/runtime/contracts/stage_node_manifest_registry.h`
- `src/runtime/facade/runtime_facade_types.h`
- `tests/architecture/`
- `tests/runtime/facade/test_runtime_facade.py`

Preferred approach:

- keep the first budget gate deterministic and data-driven;
- use stable ids such as `parity_budget.cpu_exact.reference.v1`;
- represent comparison domains as named fields or string vectors rather than
  free prose;
- make `acceptance_gate` explicit, so candidate budgets cannot pass by merely
  existing;
- leave future comparator execution as a residual, not a hidden claim.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Budget ownership | A maintained capability must cite a budget owned by the backend profile. |
| Class compatibility | Profile class and budget class must match or be explicitly compatible. |
| Acceptance evidence | Maintained use requires an accepted gate, not just a budget row. |
| Comparison domains | Event order and snapshot versions remain exact identity domains. |
| Diagnostics split | Diagnostics prose and report-only helper outputs cannot become maintained truth. |

## 5. Acceptance Tests

Minimum tests:

- `parity_budget.cpu_exact.reference.v1` is present and accepted for
  `cpu_exact.reference`;
- candidate exact GPU, resident-state, and shadow budgets reject maintained
  capability promotion;
- missing budget ref rejects with a stable reason;
- incompatible profile/budget class rejects with a stable reason;
- comparison-domain data includes event order, snapshot versions, observation
  export, diagnostics trace, sync barriers, mismatch policy, and acceptance
  gate.

Suggested commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture tests/runtime/facade/test_runtime_facade.py
```

## 6. Handoff Contract

Return:

- parity budget contract/helper files touched;
- budget ids encoded;
- validator names and rejection reason values;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP13-A` projection or `WP13-D` fidelity request binding;
- residuals for future comparator execution.
