# WP16-A 运行时主干盘点证据

状态：`2026-05-21` 首轮 inventory 与 bypass map，为 WP16-B/C/D/E 交接所用。

相关机器可读 fixture：

- `tests/architecture/fixtures/wp16_runtime_spine_inventory_20260521.json`

## 1. 范围说明

本盘点只分类每个路径在 WP16-A 中的主导角色，而不是 mixed file 内的每个符号。
因此像 `runtime_facade.*` 这样的混合 surface，会按 WP16-B/C/D 仍需处理的最大迁移
风险来标记。

分类词汇与 WP16 canonical task 保持一致：

- `maintained_spine`
- `compatibility_wrapper`
- `diagnostics_only`
- `deprecated_candidate`
- `blocked`
- `unknown_requires_owner`

## 2. 选定的 WP16-B/C spine slice

WP16-B/C 选定的 maintained slice 为：

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

必需的 node 和 barrier evidence：

- maintained node ids：
  `p7.fire_control_launch.v1`、
  `p9.effects_damage.v1`、
  `p10.observation_export.v1`
- 必须留在 slice 外的 non-maintained sibling nodes：
  `p7.launch_request_adapter_compat.v1`、
  `p10.observation_trace_diagnostics.v1`
- barrier ids：
  `input_injection`、
  `window_commit`、
  `export`
- 为 maintained slice 预留但尚未选入的项：
  `stage_publish`

后续 stream 应当沿用的 facade API clues：

- `RuntimeFacade::run_wp10_window`
- `RuntimeFacade::export_observation_packet`
- `RuntimeFacade::export_engagement_event_packet`
- `RuntimeFacade::export_diagnostics_traces`

后续 stream 的 consumer 与 test clues：

- consumer migration targets：
  `python/rl/runtime/world_batch_vec_env.py`、
  `python/rl/runtime/leader_world_batch_runtime.py`、
  `python/rl/runtime/single_world_batch_runtime.py`、
  `python/scenario/compiler/generation_request.py`
- 已经命名该 slice 的 spine evidence tests：
  `tests/runtime/facade/test_runtime_facade_window_loop_injection.py`、
  `tests/runtime/bindings/test_bindings_engagement_surface.py`、
  `tests/architecture/causal_runtime/test_stage_node_manifest_registry.py`

## 3. 盘点表

| Path | Classification | Owner | Next gate | Reason |
|------|----------------|-------|-----------|--------|
| `src/runtime/facade/runtime_window_coordinator.h` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | 已经对 window inputs 分类、记录 barrier traces，并执行维护中的 manifest-derived window seam。 |
| `src/runtime/contracts/stage_node_manifest_registry.h` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | 命名维护中的 node ids，并明确把 compatibility/diagnostics nodes 与 maintained scheduler truth 分开。 |
| `tests/runtime/facade/test_runtime_facade_window_loop_injection.py` | `maintained_spine` | `WP16-B` | `WP16-B Clock-Domain Enforcement And Merge Trace` | 现有 focused test 证明了 input admission、barrier order、maintained node enumeration 与 facade export callbacks。 |
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | `maintained_spine` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 公共 binding surface 已证明 maintained export fields 与 dedicated diagnostics export，而不要求 mainline caller 直接拥有 raw world。 |
| `src/runtime/facade/runtime_facade.h` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 包含选定的 maintained window/export API，但仍公开 `runtime()` 与较广的 batch helpers，作为迁移期逃逸口。 |
| `src/runtime/facade/runtime_facade.cpp` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 实现了 maintained export chain，但仍混合了 direct world-batch compatibility methods 与 diagnostics shaping。 |
| `python/rl/runtime/world_batch/adapter.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 这是维护中 Python caller 的中心 adapter，但当 facade coverage 不完整时，它仍会回退到 `RuntimeFacade.runtime()` 或 raw `WorldBatchRuntime`。 |
| `python/rl/runtime/world_batch_vec_env.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 主训练 vec env 通过 facade adapter 读取 observation packets，但 stepping 仍然经过 compatibility batch methods，而不是 `run_wp10_window`。 |
| `python/rl/runtime/world_batch/runtime_access.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 这是对 private vec-env batch helpers 的薄 wrapper；在迁移期间有用，但仍绕过显式 runtime-window admission 与 barrier evidence。 |
| `python/rl/runtime/world_batch/compat.py` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | 重新暴露 vec-env compatibility methods 作为 `batch_runtime`；在有 maintained replacement 前需要明确的 retention / deprecation 边界。 |
| `python/rl/runtime/leader_world_batch_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 共享 leader execution runtime 避免了 raw world handles，但仍通过 compatibility world-batch access 处理 step/read，而不是选定的 window API。 |
| `python/rl/runtime/single_world_batch_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 单世界 execution wrapper 仍直接设置 pilot actions、step worlds 并读取 truth/instruments，没有经过选定 runtime-window evidence seam。 |
| `python/rl/runtime/leader_window_runtime.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 当前 leader decision window 仍是 Python-local orchestration，还没有把 decision-window admission 或 barrier evidence 委派给 runtime spine。 |
| `src/runtime/contracts/platform_capability_contracts.h` | `compatibility_wrapper` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | platform capability resolution 有意保留 `type_name_compatibility` 和 `factory_compatibility_materialization`，所以 spawn materialization 仍是 compatibility-bridged，而不是 spine-native。 |
| `src/core/engine/world_batch_runtime.h` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | 公共 raw owner 暴露 `world()`、direct spawn/setup、direct stepping 与 direct observation reads，绕过 runtime-window admission 与 facade evidence。 |
| `src/core/engine/world_batch_runtime.cpp` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | raw implementation 在 facade 之下仍有必要，但 direct caller ownership 应该收缩到明确的 compatibility gates 后面。 |
| `tests/world_batch/test_world_batch_runtime.py` | `deprecated_candidate` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | 该测试仍把 raw `WorldBatchRuntime` 当作 first-class caller surface，因此记录了后来 deprecation work 必须约束的 bypass。 |
| `tests/world_batch/test_world_batch_vec_env.py` | `compatibility_wrapper` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 当前 vec-env tests 证明的是 training functionality 通过 compatibility view，而不是通过 selected runtime-window barrier evidence。 |
| `tests/runtime/engagement/test_facade_engagement_export.py` | `diagnostics_only` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | 虽然 export assertions 有价值，但 fixture 仍通过 `RuntimeFacade.runtime().world()` escape hatches 合成 launch/damage，因此还不能算 clean maintained consumer proof。 |
| `tests/runtime/engagement/test_diagnostics_trace_contract.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | synthetic trace-chain contract check 保护的是 diagnostics vocabulary，而不是 default runtime-spine execution。 |
| `tests/runtime/bindings/test_lazy_binding_resolution.py` | `diagnostics_only` | `WP16-D` | `WP16-D Legacy Path Deprecation And Compatibility Gates` | import-order coverage 保护的是 tooling，不是 maintained runtime-spine behavior。 |
| `python/scenario/compiler/generation_request.py` | `blocked` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | request contract 的 fail-close 是正确的，而且需要 replay/branch lineage，但它仍然没有和 selected execution slice 建立 maintained runtime-spine packet/barrier binding。 |
| `src/runtime/contracts/counterfactual_replay_contracts.h` | `blocked` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | WP15 admission 仍然是 metadata-only 且明确 restore-unsupported，所以 counterfactual execution 还不能声称拥有 maintained runtime spine。 |
| `tests/training/test_diagnostics_callback_contracts.py` | `unknown_requires_owner` | `WP16-C` | `WP16-C Facade And Batch Path Spine Migration` | training diagnostics metrics 是真实 consumer，但这个路径还没有足够强地命名 observation packet ids、barrier ids 或 replay/trace refs，因此不能分类为 maintained 或 diagnostics-only。 |

## 4. Residuals

后续 stream 必须继续显式保留的 residuals：

- `runtime_facade.*` 与 Python batch adapters 是刻意混合的 surface；已选定的 maintained symbols 已经存在，但默认 caller 仍然会绕过 `run_wp10_window`。
- `generation_request.py` 与 `counterfactual_replay_contracts.h` 被 blocked 的原因是缺少 maintained runtime execution linkage，而不是验证缺口。
- `tests/training/test_diagnostics_callback_contracts.py` 是当前的 `unknown_requires_owner` 样本，在没有显式 runtime evidence fields 之前，不得漂移到 `maintained_spine`。

## 5. 交接说明

- `WP16-B`：只在 `runtime_window_coordinator.h` 和三个 maintained manifest nodes 上实现 trigger/skip/merge evidence；不要把 `p7.launch_request_adapter_compat.v1` 或 `p10.observation_trace_diagnostics.v1` 升格为 maintained scheduler truth。
- `WP16-C`：把 `world_batch_vec_env`、leader runtimes 与 single-world runtime wrappers 通过 `RuntimeFacade::run_wp10_window`，或者通过保留 selected barrier/node evidence 的等价 facade-owned window API 来路由。
- `WP16-D`：把 `WorldBatchRuntime`、`batch_runtime` 与 diagnostics-only engagement tests 变成明确的 compatibility/deprecation guards，而不是静默的默认 surface。
- `WP16-E`：优先从 JSON fixture 生成 summaries，这样 inventory vocabulary 和 selected-slice fields 可以机械复用。
