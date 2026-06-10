# WP10 Causal Runtime Foundation Acceptance Review

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp10_causal_runtime_foundation_acceptance_review_20260520.md`
- Chinese companion:
  [wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md](wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md)

Inputs:

- [WP10 Causal Runtime Foundation](../simulation_architecture/wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP10-A Manifest Registry Seed](../simulation_architecture/wp10_causal_runtime_foundation/wp10_manifest_registry_cluster_20260520.md)
- [WP10-B Window Loop And Injection](../simulation_architecture/wp10_causal_runtime_foundation/wp10_window_loop_injection_cluster_20260520.md)
- [WP10-C Same-Window Edge Validation](../simulation_architecture/wp10_causal_runtime_foundation/wp10_same_window_validation_cluster_20260520.md)
- [WP10-D Event And Snapshot Evidence](../simulation_architecture/wp10_causal_runtime_foundation/wp10_event_snapshot_evidence_cluster_20260520.md)
- [WP10-E Integration And Acceptance Handoff](../simulation_architecture/wp10_causal_runtime_foundation/wp10_integration_acceptance_cluster_20260520.md)

## 1. Verdict

WP10 is accepted as the first code-owned causal runtime foundation slice. The
implementation provides a maintained `StageNodeManifest` registry, a
facade-side scheduling-window loop skeleton with request injection states,
schedule-construction same-window validation, and facade/binding-visible
event/snapshot/barrier/source-time evidence for the engagement/observation
slice.

Scope caveats are intentional:

- The window loop is a facade-side skeleton, not a global scheduler
  replacement.
- The event ordering claim is stable facade export ordering within the selected
  evidence families, not a global event queue ordering guarantee.
- Strict clock-domain enforcement, `ActionHoldPolicy`, Law 14 read-side
  enforcement, Agency Graph runtime authority, backend/fidelity promotion, and
  counterfactual/worldline branching remain later-phase work.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP10-A Manifest Registry Seed` | pass | `src/runtime/contracts/stage_node_manifest_registry.h` defines the maintained registry and node ids `p7.fire_control_launch.v1`, `p9.effects_damage.v1`, and `p10.observation_export.v1`; `tests/architecture/causal_runtime/test_stage_node_manifest_registry.py` verifies required fields and registry shape. |
| `WP10-B Window Loop And Injection` | pass | `src/runtime/facade/runtime_window_coordinator.h`, `runtime_facade_types.h`, `runtime_facade.h`, and `runtime_facade.cpp` expose the minimal window loop, barrier trace, and accepted/deferred/rejected/expired request states; `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` verifies the focused behavior. |
| `WP10-C Same-Window Edge Validation` | pass | `src/core/engine/same_window_edge_validation.h` validates declared same-window edges using producer publish intent, consumer declaration, shared read/write contracts, and acyclic construction; `tests/architecture/causal_runtime/test_same_window_edge_validation.py` covers passing and failing fixtures. |
| `WP10-D Event And Snapshot Evidence` | pass | `src/runtime/contracts/engagement_contracts.h`, `src/runtime/facade/runtime_facade_types.h`, `src/runtime/facade/runtime_facade.cpp`, and `src/interfaces/python/bindings_runtime.cpp` expose snapshot, barrier, source-time, producer-node, and diagnostics ancestry metadata; engagement, facade, and binding tests verify visibility. |
| `WP10-E Integration And Acceptance Handoff` | pass | Final validation passed after explicitly updating the diagnostics-only escape-hatch allowlist in `tests/architecture/runtime_facade`; this review records commands, residuals, and next-phase handoff. |

## 3. Validation Commands

Passed:

```bash
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/facade/test_runtime_facade.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/causal_runtime/test_stage_node_manifest_registry.py tests/runtime/facade/test_runtime_facade_window_loop_injection.py tests/architecture/causal_runtime/test_same_window_edge_validation.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_live_engagement_event_capture.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/runtime_facade tests/architecture/governance/test_runtime_infrastructure_documentation.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP10
git diff --check
```

Observed outcomes:

- Build: passed.
- Focused WP10-D engagement/facade/binding batch: `36 passed`.
- Focused WP10 A/B/C/D regression batch: `48 passed`.
- Architecture closure/layering batch: initially found one allowlist drift,
  then passed with `17 passed` after the explicit diagnostics-only count update.
- Runtime engagement/facade/bindings batch: `88 passed`.
- `git diff --check`: passed.

## 4. Integration Notes

- `tests/architecture/runtime_facade` was updated because
  `tests/runtime/engagement/test_facade_engagement_export.py` now has two
  diagnostics-only `facade.runtime().world(...)` setup paths. The update keeps
  the escape hatch explicit rather than weakening the guard.
- The current local binding build uses `build-workshop`; stale results from
  another build directory should not be used as WP10 acceptance evidence.
- No runtime blocker remains for WP10 acceptance.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- Phase 2 should turn the selected causal seam into a stronger facade vertical
  slice and add `ActionHoldPolicy` plus information-state provenance labels.
- Later scheduler work should add strict clock-domain enforcement and broader
  multi-rate scheduling only after the skeleton remains stable.
- Law 14 read-side enforcement and Agency Graph runtime authority remain later
  information/agency enforcement work.
- Backend/fidelity expansion and counterfactual/worldline branching remain
  downstream phases and should not be claimed by WP10.

Recommended next WP: open the Phase 2 facade vertical slice from the
post-WP9 route, using WP10 node ids, barrier ids, and evidence metadata as the
non-negotiable runtime seam.
