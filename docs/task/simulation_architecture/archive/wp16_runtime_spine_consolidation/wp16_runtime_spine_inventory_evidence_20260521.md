# WP16-A Runtime Spine Inventory Evidence

Status: `2026-05-21` first-pass inventory and bypass map for WP16-B/C/D/E handoff.

Related machine-readable fixture:

- `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json`

## 1. Scope Note

This inventory classifies the dominant WP16-A role of each path, not every
symbol inside a mixed file. Mixed surfaces such as `runtime_facade.*` are
therefore marked by the strongest migration risk that WP16-B/C/D still has to
manage.

Classification vocabulary follows the WP16 canonical task:

- `maintained_spine`
- `compatibility_wrapper`
- `diagnostics_only`
- `deprecated_candidate`
- `blocked`
- `unknown_requires_owner`

## 2. Selected WP16-B/C Spine Slice

Selected maintained slice for WP16-B/C:

```text
RuntimeWindowRequest admission
  -> input_injection barrier
  -> p7.fire_control_launch.v1
  -> p9.effects_damage.v1
  -> window_commit barrier
  -> p10.observation_export.v1
  -> export barrier
  -> observation / engagement / diagnostics facade export
  -> training/scenario/experiment consumers through facade-shaped adapters
```

Required node and barrier evidence:

- Maintained node ids:
  `p7.fire_control_launch.v1`,
  `p9.effects_damage.v1`,
  `p10.observation_export.v1`
- Non-maintained sibling nodes that must stay out of the selected slice:
  `p7.launch_request_adapter_compat.v1`,
  `p10.observation_trace_diagnostics.v1`
- Barrier ids:
  `input_injection`,
  `window_commit`,
  `export`
- Reserved but not yet selected for the maintained slice:
  `stage_publish`

Facade API clues that later streams should route through:

- `RuntimeFacade::run_wp10_window`
- `RuntimeFacade::export_observation_packet`
- `RuntimeFacade::export_engagement_event_packet`
- `RuntimeFacade::export_diagnostics_traces`

Consumer and test clues for later streams:

- Consumer migration targets:
  `python/rl/runtime/world_batch_vec_env.py`,
  `python/rl/runtime/leader_world_batch_runtime.py`,
  `python/rl/runtime/single_world_batch_runtime.py`,
  `python/scenario/compiler/generation_request.py`
- Spine evidence tests already naming this slice:
  `tests/runtime/facade/test_runtime_facade_window_loop_injection.py`,
  `tests/runtime/bindings/test_bindings_engagement_surface.py`,
  `tests/architecture/causal_runtime/test_stage_node_manifest_registry.py`

## 3. Inventory Map

| Path | Classification | Owner | Next gate | Reason |
|------|----------------|-------|-----------|--------|
| `src/runtime/facade/runtime_window_coordinator.h` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | Already classifies window inputs, records barrier traces, and executes the maintained manifest-derived window seam. |
| `src/runtime/contracts/stage_node_manifest_registry.h` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | Names the maintained node ids and explicitly separates compatibility/diagnostics nodes from maintained scheduler truth. |
| `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | Existing focused test proves input admission, barrier order, maintained node enumeration, and facade export callbacks on the selected slice. |
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | `maintained_spine` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Public binding surface already proves maintained export fields and dedicated diagnostics export without requiring raw world ownership in mainline callers. |
| `src/runtime/facade/runtime_facade.h` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Carries the selected maintained window/export APIs, but still publicly exposes `runtime()` and broad batch helpers as the migration-period escape hatch. |
| `src/runtime/facade/runtime_facade.cpp` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Implements the maintained export chain, but still mixes it with direct world-batch compatibility methods and diagnostics shaping. |
| `python/rl/runtime/world_batch/adapter.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Central adapter for maintained Python callers, but it still falls back to `RuntimeFacade.runtime()` or raw `WorldBatchRuntime` when facade coverage is incomplete. |
| `python/rl/runtime/world_batch_vec_env.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Main training vec env reads observation packets through the facade adapter, but stepping still goes through compatibility batch methods instead of `run_wp10_window`. |
| `python/rl/runtime/world_batch/runtime_access.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Thin wrapper around private vec-env batch helpers; useful during migration, but still bypasses explicit runtime-window admission and barrier evidence. |
| `python/rl/runtime/world_batch/compat.py` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Re-exposes vec-env compatibility methods as `batch_runtime`; needs explicit retention/deprecation bounds once maintained replacements are in place. |
| `python/rl/runtime/leader_world_batch_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Shared leader execution runtime avoids raw world handles, but still batches step/read flows through compatibility world-batch access instead of the selected window API. |
| `python/rl/runtime/single_world_batch_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Single-world execution wrapper directly sets pilot actions, steps worlds, and reads truth/instruments without the selected runtime-window evidence seam. |
| `python/rl/runtime/leader_window_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Current leader decision window remains Python-local orchestration and does not yet delegate decision-window admission or barrier evidence to the runtime spine. |
| `src/runtime/contracts/platform_capability_contracts.h` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Platform capability resolution intentionally preserves `type_name_compatibility` and `factory_compatibility_materialization`, so spawn materialization is still compatibility-bridged rather than spine-native. |
| `src/core/engine/world_batch_runtime.h` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Public raw owner exposes `world()`, direct spawn/setup, direct stepping, and direct observation reads that bypass runtime-window admission and facade evidence. |
| `src/core/engine/world_batch_runtime.cpp` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Raw implementation remains necessary underneath the facade, but direct caller ownership of this surface should shrink behind explicit compatibility gates. |
| `tests/world_batch/test_world_batch_runtime.py` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Test coverage still treats raw `WorldBatchRuntime` as a first-class caller surface and therefore documents the bypass that later deprecation work must bound. |
| `tests/world_batch/test_world_batch_vec_env.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Current vec-env tests prove training functionality through the compatibility view, not through selected runtime-window barrier evidence. |
| `tests/runtime/engagement/test_facade_engagement_export.py` | `diagnostics_only` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Valuable export assertions exist, but the fixture still synthesizes launch/damage through `RuntimeFacade.runtime().world()` escape hatches, so it is not a clean maintained consumer proof yet. |
| `tests/runtime/engagement/test_diagnostics_trace_contract.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Synthetic trace-chain contract check is useful for evidence vocabulary, but it is diagnostics shaping rather than maintained runtime-spine execution. |
| `tests/diagnostics/test_diagnostics_import_order.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | Import-order coverage protects tooling, not maintained runtime-spine behavior. |
| `python/scenario/compiler/generation_request.py` | `blocked` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | The request contract fail-closes correctly and requires replay/branch lineage, but it still has no maintained runtime-spine packet/barrier binding to the selected execution slice. |
| `src/runtime/contracts/counterfactual_replay_contracts.h` | `blocked` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | WP15 admission remains metadata-only and explicitly restore-unsupported, so counterfactual execution cannot yet claim the maintained runtime spine. |
| `tests/training/test_cooperative_diagnostics_callback.py` | `unknown_requires_owner` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | Training diagnostics metrics are real consumers, but this path does not yet name observation packet ids, barrier ids, or replay/trace refs strongly enough to classify as maintained or diagnostics-only. |

## 4. Residuals

Residuals that later streams must keep explicit:

- `runtime_facade.*` and Python batch adapters are intentionally mixed surfaces;
  selected maintained symbols already exist, but default callers still bypass
  `run_wp10_window`.
- `generation_request.py` and
  `counterfactual_replay_contracts.h` are blocked by missing maintained runtime
  execution linkage, not by validation gaps.
- `tests/training/test_cooperative_diagnostics_callback.py` is the current
  `unknown_requires_owner` sample and must not drift into `maintained_spine`
  without explicit runtime evidence fields.

## 5. Handoff Notes

- `WP16-B`: implement trigger/skip/merge evidence on
  `runtime_window_coordinator.h` plus the three maintained manifest nodes only.
  Do not promote `p7.launch_request_adapter_compat.v1` or
  `p10.observation_trace_diagnostics.v1` into maintained scheduler truth.
- `WP16-C`: route `world_batch_vec_env`, leader runtimes, and single-world
  runtime wrappers through `RuntimeFacade::run_wp10_window` or an equivalent
  facade-owned window API that preserves selected barrier/node evidence.
- `WP16-D`: turn `WorldBatchRuntime`, `batch_runtime`, and diagnostics-only
  engagement tests into explicit compatibility/deprecation guards rather than
  silent default surfaces.
- `WP16-E`: prefer generating summaries from the JSON fixture so the inventory
  vocabulary and selected-slice fields stay mechanically reusable.
