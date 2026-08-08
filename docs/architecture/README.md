# Architecture Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-08`

This is the target owner for cross-domain system architecture, runtime layers,
contracts, backends, and architecture decisions. During migration, current
authorities remain under [plan/architecture](../plan/architecture/README.md),
[plan/runtime_facade](../plan/runtime_facade/README.md), and
[plan/exact_runtime](../plan/exact_runtime/README.md). A route moves here only
in a separately reviewed migration slice.

## Standards

- [Simulation conventions](standards/simulation_conventions.md): maintained
  engine-neutral coordinate, unit, observation, array, action, and determinism
  conventions.
- [Runtime workflow and contract baseline](standards/runtime_workflow_and_contract_baseline.md):
  maintained loader-to-runtime stage ownership and roundtrip seams, subordinate
  to the strict simulation architecture baseline.

## Open Issues

- [System modularization issue](work/issues/modularization_plan.md): draft
  residual analysis; directory placement does not authorize implementation.

## Reviews

- [Architecture review — 2026-06-03](reviews/architecture_review_20260603.md)
- [Architecture norms and correctness review — 2026-06-03 (Chinese only)](reviews/architecture_norms_correctness_review_20260603.zh.md)

These are retained review snapshots. They do not replace current standards,
plans, implementation, or executable evidence.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for future architecture standards, references, work, and reviews.
