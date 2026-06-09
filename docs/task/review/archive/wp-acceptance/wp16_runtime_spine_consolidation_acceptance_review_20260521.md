# WP16 Runtime Spine Consolidation Acceptance Review

Status: `2026-05-21` accepted / implementation mergeable.

Language:

- English canonical: `wp16_runtime_spine_consolidation_acceptance_review_20260521.md`
- Chinese companion:
  [wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md](wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md)

Inputs:

- [WP16 Runtime Spine Consolidation](../simulation_architecture/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.md)
- [WP16-A Runtime Spine Inventory And Bypass Map](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.md)
- [WP16-B Clock-Domain Enforcement And Merge Trace](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.md)
- [WP16-C Facade And Batch Path Spine Migration](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.md)
- [WP16-D Legacy Path Deprecation And Compatibility Gates](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.md)
- [WP16-E Generated Documentation And Closure Automation](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.md)
- [WP16-F Integration And Acceptance Handoff](../simulation_architecture/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.md)
- [WP15 acceptance review](wp15_counterfactual_experiment_generation_acceptance_review_20260521.md)

## 1. Verdict

WP16 is accepted as the selected-slice runtime-spine consolidation increment. It turns the accepted WP10-WP15 runtime, facade, agency, backend/fidelity, capability, and counterfactual boundaries into the maintained default runtime path for the narrowed spine slice.

This is intentionally not a global rewrite:

- no global scheduler rewrite;
- no full multi-rate support;
- no public legacy API deletion;
- no maintained independent-domain merge success path;
- no counterfactual/scenario generation runtime consumer promotion beyond the recorded compatibility and diagnostics boundaries.

The accepted slice is the runtime-spine handoff centered on `RuntimeWindowRequest` admission, `input_injection`, the maintained `p7.fire_control_launch.v1` / `p9.effects_damage.v1` / `p10.observation_export.v1` nodes, `window_commit`, `export`, facade export, and the current facade-shaped consumer adapters.

## 2. Gate Verdicts

| Gate | Verdict | Evidence |
|------|---------|----------|
| `WP16-A Runtime Spine Inventory And Bypass Map` | pass | `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json` and `docs/task/simulation_architecture/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_evidence_20260521.md` classify maintained, compatibility, diagnostics-only, deprecated, blocked, and unknown paths with explicit owners and next gates. |
| `WP16-B Clock-Domain Enforcement And Merge Trace` | pass | `src/runtime/facade/runtime_window_coordinator.h`, `src/runtime/contracts/stage_node_manifest_registry.h`, and `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` prove trigger/skip evidence for the selected slice and fail-closed handling for missing deterministic merge metadata. |
| `WP16-C Facade And Batch Path Spine Migration` | pass | `src/runtime/facade/runtime_facade.h`, `src/runtime/facade/runtime_facade.cpp`, `python/rl/runtime/world_batch/adapter.py`, `python/rl/runtime/world_batch_vec_env.py`, and `tests/runtime/bindings/test_bindings_engagement_surface.py` preserve compatibility while routing selected maintained consumers through the runtime-window evidence spine or explicit fallback wrappers. |
| `WP16-D Legacy Path Deprecation And Compatibility Gates` | pass | `docs/task/simulation_architecture/wp16_runtime_spine_consolidation/wp16_legacy_path_gate_evidence_20260521.md` and `tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py` keep `WorldBatchRuntime`, `batch_runtime`, `RuntimeFacade.runtime()`, and diagnostics-only paths explicitly bounded rather than silently maintained. |
| `WP16-E Generated Documentation And Closure Automation` | pass | `tools/maintenance/wp_doc_closure_audit.py` now reports the WP16 closure state without replacing acceptance authority; generated summaries remain advisory only. |
| `WP16-F Integration And Acceptance Handoff` | pass | This review records A-E status, exact validation outcomes, residuals, README/route/index sync, and the narrow acceptance boundary. |

## 3. Validation Commands

Passed in the main thread before this review:

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py tests/architecture/runtime_spine/test_clock_domain_enforcement.py tests/architecture/governance/test_doc_closure_audit.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or window or barrier or evidence"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py tests/world_batch/test_world_batch_vec_env.py -k "reset_uses_runtime_facade_compatibly or exposes_batch_runtime_as_compatibility_view or single"
python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "runtime_window or observation_batch_packet or engagement_event_packet"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16 --summary --json
```

Observed outcomes:

- `git diff --check`: passed.
- WP16 architecture batch: `18 passed`.
- Runtime facade window-loop batch: `5 passed`.
- World-batch compatibility batch: `5 passed, 34 deselected`.
- Runtime binding DTO batch: `3 passed, 14 deselected`.
- Closure audit summary: passed with no missing acceptance review and no missing Chinese companion for the optional evidence docs.

Final closure validation was then run again after the review package was added:

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP16
```

Observed outcome:

- both commands passed.

## 4. Runtime Surface Summary

- `RuntimeWindowRequest` admission now records the selected spine slice with `input_injection`, `window_commit`, and `export` barrier evidence.
- The maintained spine remains scoped to `p7.fire_control_launch.v1`, `p9.effects_damage.v1`, and `p10.observation_export.v1`; reserved or diagnostics sibling nodes remain outside the maintained slice.
- `RuntimeFacade.runtime()` and `batch_runtime` remain compatibility surfaces, not promoted maintained frontend contracts.
- `WorldBatchRuntime` remains a deprecated-candidate surface with explicit compatibility retention, not a removed API.
- `python/scenario/compiler/generation_request.py` and `src/runtime/contracts/counterfactual_replay_contracts.h` remain blocked by missing maintained runtime execution linkage and do not become maintained runtime consumers here.

## 5. Residuals And Next Plan

Residuals intentionally carried forward:

- global scheduler rewrite;
- full multi-rate support;
- maintained independent-domain merge success path;
- public legacy API deletion;
- counterfactual/scenario generation maintained runtime consumer promotion;
- any broad replacement of compatibility wrappers before the retained fallback paths have narrower owners.

The accepted WP16 increment is mergeable as a selected-slice runtime-spine consolidation closure packet, but it must continue to preserve the residual register and the narrow implementation boundary described above.
