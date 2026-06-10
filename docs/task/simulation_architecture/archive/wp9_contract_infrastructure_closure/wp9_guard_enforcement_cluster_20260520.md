# WP9-D Guard Enforcement

Status: `2026-05-20` complete / accepted WP9 parallel stream.

Language:

- English canonical: `wp9_guard_enforcement_cluster_20260520.md`
- Chinese companion:
  [wp9_guard_enforcement_cluster_20260520.zh.md](wp9_guard_enforcement_cluster_20260520.zh.md)

Inputs:

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.md)
- [WP5 validation harness acceptance review](../../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## 1. Purpose

WP9-D turns the deferred guard items into maintained checks. The goal is not to
ban every compatibility path; it is to make each remaining direct `sim.*`,
runtime, or binding surface exception visible, labeled, and testable.

The stream covers:

- GUA-1 global `sim.*` AST guard with allowlist
- GUA-2 binding surface smoke promotion

## 2. Guard Design

The guard must distinguish:

| Category | Allowed when | Required label |
|----------|--------------|----------------|
| Maintained facade path | It uses typed request/result facade APIs. | No exception label needed. |
| Compatibility adapter | It centralizes legacy access behind a named adapter and has no hidden state ownership. | `compatibility_only`. |
| Diagnostics path | It reads trace/debug/export data without affecting committed state. | `diagnostics_only`. |
| Test fixture | It constructs shell worlds or packet defaults for surface validation only. | `test_only`. |
| Violation | It mutates authoritative simulation state outside facade contracts or hides raw runtime access in mainline code. | Not allowed. |

## 3. Implementation Route

Recommended route:

1. Add an allowlist document or table near the architecture guard test.
2. Implement AST checks that scan Python call sites for direct `sim.*` and raw
   runtime escape hatches.
3. Keep existing scoped escape hatch tests, but make the provenance labels more
   explicit.
4. Promote `test_bindings_engagement_surface.py` so the empty packet-shell
   world-index case is covered and no longer a review-only residual.
5. Avoid broad string-grep bans that break diagnostics-only code without
   explaining the allowed path.

Preferred write scope:

- `tests/architecture/*`
- `tests/runtime/bindings/test_bindings_engagement_surface.py`
- `docs/task/simulation_architecture/wp9_contract_infrastructure_closure/*`
- Optional focused allowlist file under `docs/standards/governance/`

## 4. Work Items

| Stream | Required output | Budget |
|--------|-----------------|--------|
| `WP9-D1 Allowlist Vocabulary` | Documented labels and allowed path categories for direct simulation/runtime access. | Medium. |
| `WP9-D2 AST Guard` | Static test that enforces the allowlist without banning diagnostics/compatibility by accident. | High. |
| `WP9-D3 Binding Smoke Promotion` | Binding test for empty engagement packet shell and world-index/default field behavior. | Medium. |
| `WP9-D4 Evidence Sync` | Test names and guard labels recorded for WP9-E acceptance. | Medium. |

## 5. Non-Goals

- Do not delete compatibility adapters while maintained callers still need
  them.
- Do not add a broad `sim.*` ban without an allowlist and labels.
- Do not change C++ runtime behavior in this stream unless a test-only fixture
  exposes a true binding bug.
- Do not infer facade correctness from import success alone.

## 6. Acceptance Gates

WP9-D is ready for WP9-E when:

1. The allowlist labels are documented.
2. Static guard tests enforce the labels and report useful file/line evidence.
3. Binding smoke covers the previously deferred empty packet-shell world-index
   case.
4. Compatibility and diagnostics exceptions remain explicit.
5. Validation commands are recorded for the final WP9 review.

## 7. Validation Commands

```bash
git diff --check
pytest tests/architecture/runtime_facade tests/architecture/runtime_facade/test_design_boundary_gates.py tests/runtime/bindings/test_bindings_engagement_surface.py
rg -n "sim\\.\\*|compatibility_only|diagnostics_only|test_only|Binding surface smoke|EngagementEventPacket" tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
