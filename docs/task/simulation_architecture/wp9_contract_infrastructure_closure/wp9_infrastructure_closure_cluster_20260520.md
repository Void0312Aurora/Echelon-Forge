# WP9-C Infrastructure Closure

Status: `2026-05-20` complete / accepted WP9 parallel stream with one tracked residual.

Language:

- English canonical: `wp9_infrastructure_closure_cluster_20260520.md`
- Chinese companion:
  [wp9_infrastructure_closure_cluster_20260520.zh.md](wp9_infrastructure_closure_cluster_20260520.zh.md)

Inputs:

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.md)
- [WP2.5 scheduler semantics freeze](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md)
- [WP3 engagement pilot](../wp3_engagement_pilot/engagement_pilot_wp3_20260519.md)
- [WP4 facade alignment acceptance review](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP6 backend profile policy acceptance review](../../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md)
- [WP7 backend capability materialization](../wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md)

## 1. Purpose

WP9-C closes the small infrastructure residuals that were accepted as deferred
follow-up in earlier work packages. The intent is to make the architecture
track honest: every residual is either closed with evidence or remains visible
with a new owner.

The stream covers INF-1 through INF-7.

## 2. Required Closure Items

| ID | Item | Required output |
|----|------|-----------------|
| `INF-1` | `merge_policy` naming collision | Rename WP2.5 clock-domain wording to `clock_merge_policy`; keep cross-layer `merge_policy` for action/coordination DTOs. |
| `INF-2` | `DiagnosticsTrace` independent facade surface | Add a dedicated facade query endpoint or a clearly named facade method that is not piggybacked solely on engagement export. |
| `INF-3` | `RuntimeCapabilities` population trigger | Document that richer capability projection starts only when at least one non-reference backend profile is maintained. |
| `INF-4` | `StageNodeManifest` registry completion | Add P0-P6 and P8-P10 example manifests alongside the existing P7 example. |
| `INF-5` | Facade split threshold rule | Document split at roughly 40 public methods into Session, Setup, Execution, Observation, Diagnostics, Engagement, and Capability groups. |
| `INF-6` | WP3 real missile terminal effects capture | Move maintained capture toward guidance/effects events instead of debug-only proximity-hit paths, or record a precise blocked handoff. |
| `INF-7` | WP3 recent-event storage strategy | Replace or formally wrap the bounded recent-event buffer with event-queue-aligned ordering semantics, or record a precise blocked handoff. |

## 3. Implementation Route

Recommended route:

1. Patch docs first for INF-1, INF-3, INF-4, and INF-5 because they have no
   runtime dependency.
2. Add the narrow diagnostics facade method for INF-2 with a focused test.
3. Inspect WP3 event capture paths before editing INF-6/INF-7; do not replace
   a working debug path with a less visible abstraction.
4. If INF-6/INF-7 are too large for WP9, create explicit owner notes and tests
   that keep the residual visible rather than silently closing it.

Preferred write scope:

- `docs/plan/architecture/*`
- `docs/task/simulation_architecture/wp25_scheduler_semantics/*`
- `docs/task/simulation_architecture/wp3_engagement_pilot/*`
- `docs/task/simulation_architecture/wp6_backend_profile_policy/*`
- `docs/task/simulation_architecture/wp7_backend_capability_materialization/*`
- `src/runtime/facade/*`
- `src/core/engine/*engagement*`, `src/core/engine/*weapon*`,
  `src/core/engine/*damage*`
- `tests/runtime/engagement/*`
- `tests/runtime/facade/*`
- `tests/architecture/*`

## 4. Work Items

| Stream | Required output | Budget |
|--------|-----------------|--------|
| `WP9-C1 Naming And Capability Docs` | INF-1 and INF-3 doc patches with bilingual references where source docs are bilingual. | Medium. |
| `WP9-C2 Manifest Registry Completion` | P0-P6 and P8-P10 examples or registry entries for `StageNodeManifest`. | High. |
| `WP9-C3 Diagnostics Facade Surface` | Independent diagnostics trace facade query and focused tests. | High. |
| `WP9-C4 Facade Split Rule` | Runtime facade split threshold and target groups documented in architecture/facade docs. | Medium. |
| `WP9-C5 Engagement Event Closure` | INF-6/INF-7 implementation or explicit blocked owner note with retained tests. | Xhigh. |

## 5. Non-Goals

- Do not implement the full scheduler runtime.
- Do not promote backend profiles or alter WP6/WP7 capability truth.
- Do not remove existing engagement export compatibility until replacement
  facade tests pass.
- Do not claim INF-6/INF-7 closed by docs only if code still relies on the
  debug-only path.

## 6. Acceptance Gates

WP9-C is ready for WP9-E when:

1. INF-1 through INF-7 each has a named evidence row.
2. Documentation-only INF items are patched in the authoritative source docs.
3. Diagnostics trace query is available through a facade method or explicitly
   blocked with a reason.
4. WP3 event capture/storage residuals are either fixed or kept visible with a
   concrete follow-up owner and failing/blocked evidence.
5. Focused tests or document checks cover the changed surfaces.

## 7. Validation Commands

```bash
git diff --check
pytest tests/runtime/engagement tests/runtime/facade tests/architecture
rg -n "clock_merge_policy|DiagnosticsTrace|RuntimeCapabilities|StageNodeManifest|facade split|kMaxRecentEngagementEvents|recent engagement" docs src tests
```
