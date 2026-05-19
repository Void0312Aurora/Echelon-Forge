# WP5-A Dispatch Sheet: Harness Inventory

Status: `2026-05-19` first-wave dispatch sheet.

Language:

- English canonical: `wp5_harness_inventory_cluster_20260519.md`
- Chinese companion: [wp5_harness_inventory_cluster_20260519.zh.md](wp5_harness_inventory_cluster_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-F integration handoff](wp4_integration_handoff_20260519.md)
- Current `tests/architecture/`, `tests/runtime/`, and `tests/smoke/ci_smoke_suite.json`

## 1. Purpose

WP5-A maps current evidence to the five WP5 validation tiers before broader
test promotion. It should find what already proves the architecture and what is
still missing, without changing runtime behavior.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP5-A1 Tier Inventory` | Map existing architecture, facade, engagement, binding, execution, and smoke tests to design, trace, boundary, information/belief, and replay/evidence tiers. | `docs/task/simulation_architecture`. | Medium. |
| `WP5-A2 Smoke Membership Review` | Identify which tests are already in `tests/smoke/ci_smoke_suite.json`, which should be candidates, and which are too broad or metadata-dependent. | Docs only in this cluster. | Medium. |
| `WP5-A3 Gap Register` | Record immediate gaps versus metadata-dependent gaps, using WP4 final acceptance residual risks. | `docs/task/simulation_architecture`. | Medium. |
| `WP5-A4 Dispatch Advice` | Recommend which gates should be implemented by WP5-B/C/D/E and which should stay deferred. | `docs/task/simulation_architecture`. | Medium. |

## 3. Non-Goals

- Do not edit runtime code.
- Do not promote smoke-suite entries in this cluster.
- Do not add new tests unless a tiny documentation-backed fixture is necessary.
- Do not enforce metadata that WP4 explicitly deferred to WP5 or later DTO work.

## 4. Acceptance Gates

This cluster is accepted when:

1. Every WP5 validation tier has current coverage, candidate coverage, or an
   explicit gap.
2. Smoke-suite candidates are listed with rationale.
3. Immediate gates are separated from metadata-dependent gates.
4. The inventory gives WP5-B/C/D/E enough ownership boundaries to proceed
   without overlapping writes.
