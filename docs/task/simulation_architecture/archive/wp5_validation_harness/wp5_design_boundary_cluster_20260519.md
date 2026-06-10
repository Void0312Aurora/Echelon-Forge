# WP5-B Dispatch Sheet: Design And Boundary Gates

Status: `2026-05-19` first-wave dispatch sheet.

Language:

- English canonical: `wp5_design_boundary_cluster_20260519.md`
- Chinese companion: [wp5_design_boundary_cluster_20260519.zh.md](wp5_design_boundary_cluster_20260519.zh.md)

Inputs:

- [WP5 validation harness](validation_harness_wp5_20260519.md)
- [WP4 facade alignment acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP4-I compatibility guard notes](wp4_compat_guard_notes_20260519.md)
- Current `tests/architecture/runtime_facade`
- Current `tests/runtime/facade/`

## 1. Purpose

WP5-B strengthens design and boundary gates for maintained facade paths. It
should prevent raw runtime access from becoming a maintained frontend dependency
while keeping compatibility adapters and diagnostics paths available.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP5-B1 Facade Escape-Hatch Guard` | Extend or document architecture checks so `RuntimeFacade::runtime()` remains compatibility-only and does not leak into maintained frontend classes. | `tests/architecture/`, optional docs note. | Medium. |
| `WP5-B2 Maintained Surface Ownership Gate` | Add or document checks that maintained facade request/result types stay engine-encapsulated and do not include engine-owner headers. | `tests/architecture/`. | Medium. |
| `WP5-B3 Smoke Candidate Note` | Recommend which design/boundary tests should enter the WP5 smoke loop. | Docs note or report to integration owner. | Medium. |
| `WP5-B4 False-Positive Review` | Keep direct `sim.*` broad bans deferred unless a safe allowlist can be limited to maintained paths. | `tests/architecture/`, docs. | Medium-high. |

## 3. Non-Goals

- Do not ban all direct `sim.*` use across legacy Gym, scenario, oracle, or
  diagnostics paths.
- Do not remove compatibility adapters.
- Do not edit runtime/facade C++ signatures unless a test cannot be expressed
  any other way.
- Do not change smoke-suite membership directly unless the integration owner
  asks for it.

## 4. Acceptance Gates

This cluster is accepted when:

1. Existing raw-runtime guard coverage is preserved or strengthened.
2. Compatibility-only and diagnostics-only paths remain visibly separate from
   maintained facade paths.
3. Any deferred broad guard has a concrete reason and later enforcement route.
4. Focused tests pass locally.
