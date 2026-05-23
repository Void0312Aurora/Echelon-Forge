# WP16-D Legacy Path Gate Evidence

Status: `2026-05-21` preliminary compatibility/deprecation gate evidence for
WP16-D.

Related inventory source:

- `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json`

## 1. Scope

This note records the first bounded-status pass for legacy runtime access paths
identified by `WP16-A`. It is a gate-preparation artifact only:

- no public API is removed here;
- no runtime/scheduler/facade/batch implementation is rewritten here;
- diagnostics-only or compatibility paths do not become maintained by omission.

## 2. Key Bounded Paths

| Path or path family | Current status | Owner | Next gate | Why bounded now |
|---------------------|----------------|-------|-----------|-----------------|
| `src/core/engine/world_batch_runtime.h` and `.cpp` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Raw owner still exposes `world()`, direct setup/spawn, `step_batch()`, and direct observation reads that bypass runtime-window admission and facade evidence. |
| `python/rl/runtime/world_batch/compat.py` via `vec_env.batch_runtime` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Public compatibility view remains intentionally preserved while WP16-C has not yet finished routing maintained callers through facade-owned window APIs. |
| `RuntimeFacade.runtime()` and downstream `runtime().world()` access | `compatibility_wrapper` plus diagnostics-bounded callsites | `WP16-C` / `WP16-D` | `WP16-C Facade And Batch Path Spine Migration` / `WP16-D Legacy Path Deprecation And Compatibility Gates` | Escape hatch is still public for diagnostics and migration adapters only; diagnostics tests that rely on `runtime().world()` stay non-maintained. |
| `tests/runtime/engagement/test_facade_engagement_export.py` | `diagnostics_only` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | The test proves export vocabulary, but it synthesizes launch/damage through `facade.runtime().world()` and therefore cannot serve as maintained-spine evidence. |
| `tests/runtime/engagement/test_diagnostics_trace_contract.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Trace-chain validation protects diagnostics vocabulary only, not default runtime-spine execution. |
| `tests/training/test_cooperative_diagnostics_callback.py` | `unknown_requires_owner` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Real consumer path is still missing explicit packet/barrier/trace linkage, so WP16-D must not treat it as maintained by default. |

## 3. Replacement Clues And Retention Bounds

Maintained replacement clues already named by `WP16-A` and preserved by this
gate:

- `RuntimeFacade::run_wp10_window`
- `RuntimeFacade::export_observation_packet`
- `RuntimeFacade::export_engagement_event_packet`
- `RuntimeFacade::export_diagnostics_traces`

Retention bounds for this preliminary gate:

- `WorldBatchRuntime` remains callable, but only as a deprecated-candidate
  surface pending explicit migration or narrower compatibility ownership.
- `vec_env.batch_runtime` remains callable because training and execution
  wrappers still depend on it during `WP16-C`.
- `RuntimeFacade.runtime()` remains callable because diagnostics and adapter
  code still reference it, but it must stay labeled as an escape hatch rather
  than a maintained frontend contract.

## 4. Deprecation And Removal Candidates

Current deprecation candidates:

- `src/core/engine/world_batch_runtime.h`
- `src/core/engine/world_batch_runtime.cpp`
- `tests/world_batch/test_world_batch_runtime.py`

Current removal status:

- No removal candidate is ready for deletion in this pre-gate.
- Any future removal requires maintained replacement evidence from `WP16-C` and
  explicit acceptance through `WP16-F`.

## 5. Compatibility Risks

- If `RuntimeFacade.runtime()` is treated as a normal frontend instead of an
  escape hatch, diagnostics-only setup flows could be misreported as maintained
  runtime-spine coverage.
- If `vec_env.batch_runtime` disappears before `WP16-C` lands maintained
  replacements, Python training and execution wrappers would lose their current
  public compatibility contract.
- If `unknown_requires_owner` paths are allowed to drift without packet/barrier
  evidence, later closure work could silently promote them into maintained
  status.

## 6. WP16-F Handoff Notes

- Reuse the inventory fixture and the focused `WP16-D` guard test as the
  canonical pre-acceptance source for legacy-path status.
- Keep `WorldBatchRuntime`, `batch_runtime`, and `RuntimeFacade.runtime()`
  listed as preserved compatibility/deprecation surfaces until `WP16-C`
  contributes maintained replacement evidence.
- Do not accept any summary that labels diagnostics-only or
  `unknown_requires_owner` paths as maintained.
