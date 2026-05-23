# WP4-I Dispatch Sheet: Compatibility Guard And Integration

Status: `2026-05-19` second-wave dispatch sheet; serial/integration-oriented.

Language:

- English canonical: `wp4_compat_guard_cluster_20260519.md`
- Chinese companion: [wp4_compat_guard_cluster_20260519.zh.md](wp4_compat_guard_cluster_20260519.zh.md)

Inputs:

- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-A surface inventory draft](wp4_surface_inventory_wp4a_20260519.md)
- [WP4-B/C engagement-step alignment notes](wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding alignment notes](wp4_policy_binding_alignment_notes_20260519.md)
- Current `tests/architecture/`, WP4 docs, and smoke suite metadata

## 1. Purpose

WP4-I is the serial guardrail and integration cluster. It prevents
compatibility-only paths from quietly becoming maintained frontend paths, then
integrates second-wave outcomes into the WP4 handoff to WP5.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP4-I1 Raw Runtime Guard Review` | Review or add architecture checks that maintained paths do not newly depend on `RuntimeFacade::runtime()`, raw `WorldBatchRuntime`, or direct `sim.*` policy inputs. | `tests/architecture/`, docs. | High. |
| `WP4-I2 Surface Inventory Integration` | Update WP4 docs to cite the accepted WP4-A inventory and second-wave gates. | `docs/task/simulation_architecture`. | Medium. |
| `WP4-I3 Review Index Sync` | Add WP4 first-wave acceptance review and second-wave cluster docs to review/task indexes. | `docs/task/review/README*`, `docs/task/simulation_architecture/README*`. | Medium. |
| `WP4-I4 WP5 Handoff Note` | State what WP5 can validate immediately and what remains pending runtime metadata. | `docs/task/simulation_architecture`, optional review doc. | Medium-high. |

## 3. Non-Goals

- Do not implement facade DTO changes.
- Do not remove compatibility adapters.
- Do not run broad test suites unless focused guards pass and local artifacts
  are known fresh.
- Do not close WP4 until WP4-G and WP4-H outcomes are reviewed.

## 4. Acceptance Gates

This cluster is accepted when:

1. WP4 docs and indexes cite the accepted first-wave outputs.
2. Compatibility-only and diagnostics-only paths have guard coverage or a
   documented pending guard.
3. WP5 handoff is explicit about immediate validation targets and metadata
   still pending from runtime/facade work.
4. `git diff --check` passes for touched docs/tests.
