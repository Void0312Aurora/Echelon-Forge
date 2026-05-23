# WP5-E Dispatch Sheet: Smoke Promotion And Docs

Status: `2026-05-19` second-wave integration dispatch sheet.

Language:

- English canonical: `wp5_smoke_promotion_cluster_20260519.md`
- Chinese companion: [wp5_smoke_promotion_cluster_20260519.zh.md](wp5_smoke_promotion_cluster_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP5 first-wave acceptance review](../review/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-A harness inventory notes](wp5_harness_inventory_notes_20260519.md)
- [WP5-B design/boundary notes](wp5_design_boundary_notes_20260519.md)
- [WP5-C trace/replay gates notes](wp5_trace_replay_gates_notes_20260519.md)
- WP5-D information/belief output, once accepted
- Current `tests/smoke/ci_smoke_suite.json`

## 1. Purpose

WP5-E is the serial integration stream. It publishes the maintained WP5 smoke
command set, updates indexes, and records why each promoted test belongs in the
validation harness.

WP5-E should not start final smoke-suite edits until WP5-D returns, because
information/belief candidates affect the final five-tier coverage.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP5-E1 Smoke Candidate Merge` | Merge WP5-A/B/C/D candidate lists into a focused suite proposal. | docs first, then `tests/smoke/ci_smoke_suite.json` if accepted. | Medium. |
| `WP5-E2 Smoke Rationale` | Record which validation tier each promoted test covers. | `docs/task/simulation_architecture`. | Medium. |
| `WP5-E3 Index Sync` | Link WP5 notes, reviews, and final validation commands from task/review indexes. | `docs/task/simulation_architecture/README*`, `docs/task/review/README*`. | Medium. |
| `WP5-E4 Final Validation Command` | Publish and run a local command set that covers design, trace, boundary, information/belief, and replay/evidence tiers. | docs, smoke suite. | Medium. |

## 3. Non-Goals

- Do not add new runtime semantics.
- Do not promote broad domain directories unless they have clear WP5 tier
  ownership and acceptable cost.
- Do not enforce metadata-dependent gates before DTO fields exist.
- Do not overwrite existing smoke-suite edits from other workers without
  reading and preserving them.

## 4. Acceptance Gates

This cluster is accepted when:

1. The smoke suite or published smoke command covers all five WP5 tiers.
2. Each promoted test has a tier rationale.
3. Task and review indexes are synchronized.
4. Focused validation and `git diff --check` pass.
