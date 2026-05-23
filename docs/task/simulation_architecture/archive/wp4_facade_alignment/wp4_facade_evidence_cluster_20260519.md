# WP4-G Dispatch Sheet: Facade Evidence Gates

Status: `2026-05-19` second-wave dispatch sheet.

Language:

- English canonical: `wp4_facade_evidence_cluster_20260519.md`
- Chinese companion: [wp4_facade_evidence_cluster_20260519.zh.md](wp4_facade_evidence_cluster_20260519.zh.md)

Inputs:

- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-B/C engagement-step alignment notes](wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-A surface inventory draft](wp4_surface_inventory_wp4a_20260519.md)
- Current `tests/runtime/engagement/`, `tests/runtime/facade/`, and
  `tests/smoke/ci_smoke_suite.json`

## 1. Purpose

WP4-G turns first-wave engagement and step/lifecycle findings into focused
evidence gates. It should prefer narrow tests and documented skips over broad
facade DTO churn.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP4-G1 Engagement Producer Coverage Gate` | Test or documented fixture proving current `EngagementEventPacket` populated slots and deferred placeholders are intentional. | `tests/runtime/engagement/`, docs. | Medium. |
| `WP4-G2 Multi-World Retag Coverage` | Extend coverage beyond launch-event munition retagging when current fixtures allow effects/damage retag checks. | `tests/runtime/engagement/`. | Medium. |
| `WP4-G3 Diagnostics Piggyback Gate` | Test or doc gate that `DiagnosticsTrace` inside engagement export is piggyback evidence, not a full diagnostics surface. | `tests/runtime/engagement/`, docs. | Medium. |
| `WP4-G4 Step Result Semantic Shape Gate` | Test current `ExecutionBatchStepResult` fields for reward, termination/truncation, reward JSON, step info, controller-state changed, and observation packet presence. | `tests/runtime/facade/`. | Medium-high. |
| `WP4-G5 Smoke Candidate Note` | Recommend which focused tests should be promoted to WP5 smoke and which remain WP4-only. | docs/task/simulation_architecture. | Medium. |

## 3. Non-Goals

- No new public facade DTOs unless a test cannot be written without a minimal,
  accepted field.
- No policy/gym/binding edits.
- No replacement of `RecentEngagementEvents`.
- No dedicated diagnostics facade surface in this cluster.

## 4. Acceptance Gates

This cluster is accepted when:

1. Current engagement export producer coverage is testable or explicitly
   documented.
2. Deferred slots remain intentional and visible.
3. Multi-world retagging has at least one focused guard beyond the already
   accepted WP3 path, or the missing fixture is documented.
4. Step-result semantic shape is guarded without requiring RL training
   dependencies.
5. Recommended commands are recorded for WP4-F/WP5 integration.
