# WP16-D 遗留路径门控证据

状态：`2026-05-21` preliminary compatibility/deprecation gate evidence for
WP16-D。

相关 inventory source：

- `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json`

## 1. 范围

本说明记录 WP16-A 所识别的 legacy runtime access paths 的首轮 bounded-status 结果。
它只是一个 gate-preparation artifact：

- 不在此移除任何 public API；
- 不在此重写 runtime/scheduler/facade/batch implementation；
- diagnostics-only 或 compatibility paths 不会因为未提及而自动变成 maintained。

## 2. 关键受限路径

| Path or path family | Current status | Owner | Next gate | Why bounded now |
|---------------------|----------------|-------|-----------|-----------------|
| `src/core/engine/world_batch_runtime.h` and `.cpp` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | raw owner 仍然暴露 `world()`、direct setup/spawn、`step_batch()` 与 direct observation reads，这些都绕过 runtime-window admission 与 facade evidence。 |
| `python/rl/runtime/world_batch/compat.py` via `vec_env.batch_runtime` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | 在 WP16-C 完成把 maintained callers 迁到 facade-owned window APIs 之前，这个 public compatibility view 仍然有意保留。 |
| `RuntimeFacade.runtime()` and downstream `runtime().world()` access | `compatibility_wrapper` plus diagnostics-bounded callsites | `WP16-C` / `WP16-D` | `WP16-C Facade And Batch Path Spine Migration` / `WP16-D Legacy Path Deprecation And Compatibility Gates` | escape hatch 仍然对 diagnostics 和 migration adapters 开放；依赖 `runtime().world()` 的 diagnostics tests 仍然是 non-maintained。 |
| `tests/runtime/engagement/test_facade_engagement_export.py` | `diagnostics_only` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 该测试验证了 export vocabulary，但它通过 `facade.runtime().world()` 合成 launch/damage，因此不能作为 maintained-spine evidence。 |
| `tests/runtime/engagement/test_diagnostics_trace_contract.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | trace-chain validation 只保护 diagnostics vocabulary，而不是 default runtime-spine execution。 |
| `tests/training/test_diagnostics_callback_contracts.py` | `unknown_requires_owner` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 真实 consumer path 仍然缺少显式 packet/barrier/trace linkage，所以 WP16-D 不能默认把它当作 maintained。 |

## 3. 替换线索与保留边界

WP16-A 已命名并由本门控保留的 maintained replacement clues：

- `RuntimeFacade::run_wp10_window`
- `RuntimeFacade::export_observation_packet`
- `RuntimeFacade::export_engagement_event_packet`
- `RuntimeFacade::export_diagnostics_traces`

本预门控的 retention bounds：

- `WorldBatchRuntime` 仍然可调用，但只是 deprecated-candidate surface，等待显式 migration 或更窄的 compatibility ownership。
- `vec_env.batch_runtime` 仍然可调用，因为 training 与 execution wrappers 在 WP16-C 期间仍依赖它。
- `RuntimeFacade.runtime()` 仍然可调用，因为 diagnostics 和 adapter code 仍在引用它，但它必须始终被标记为 escape hatch，而不是 maintained frontend contract。

## 4. 退役与删除候选

当前 deprecation candidates：

- `src/core/engine/world_batch_runtime.h`
- `src/core/engine/world_batch_runtime.cpp`
- `tests/world_batch/test_world_batch_runtime.py`

当前 removal 状态：

- 在这个 pre-gate 中没有 ready-for-deletion 的 removal candidate。
- 任何未来的 removal 都要求来自 WP16-C 的 maintained replacement evidence，以及 WP16-F 的显式接受。

## 5. 兼容性风险

- 如果把 `RuntimeFacade.runtime()` 当作普通 frontend，而不是 escape hatch，那么 diagnostics-only setup flows 可能会被误报为 maintained runtime-spine coverage。
- 如果 `vec_env.batch_runtime` 在 WP16-C 还没落地维护替换前就消失，Python training 与 execution wrappers 会失去当前 public compatibility contract。
- 如果允许 `unknown_requires_owner` paths 在缺少 packet/barrier evidence 的情况下漂移，后续 closure 可能会悄悄把它们升级成 maintained。

## 6. WP16-F 交接说明

- 复用 inventory fixture 与 focused `WP16-D` guard test 作为 legacy-path status 的 canonical pre-acceptance source。
- 在 WP16-C 提供 maintained replacement evidence 之前，继续把 `WorldBatchRuntime`、`batch_runtime` 与 `RuntimeFacade.runtime()` 视为 preserved compatibility/deprecation surfaces。
- 不接受任何把 diagnostics-only 或 `unknown_requires_owner` paths 描述为 maintained 的总结。
