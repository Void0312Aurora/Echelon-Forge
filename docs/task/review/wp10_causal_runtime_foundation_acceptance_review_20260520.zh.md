# WP10 Causal Runtime Foundation 验收审查

状态：`2026-05-20` accepted / implementation mergeable。

语言：

- 英文主文：[wp10_causal_runtime_foundation_acceptance_review_20260520.md](wp10_causal_runtime_foundation_acceptance_review_20260520.md)
- 中文辅文：`wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md`

输入：

- [WP10 Causal Runtime Foundation](../simulation_architecture/wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP10-A Manifest Registry Seed](../simulation_architecture/wp10_causal_runtime_foundation/wp10_manifest_registry_cluster_20260520.zh.md)
- [WP10-B Window Loop And Injection](../simulation_architecture/wp10_causal_runtime_foundation/wp10_window_loop_injection_cluster_20260520.zh.md)
- [WP10-C Same-Window Edge Validation](../simulation_architecture/wp10_causal_runtime_foundation/wp10_same_window_validation_cluster_20260520.zh.md)
- [WP10-D Event And Snapshot Evidence](../simulation_architecture/wp10_causal_runtime_foundation/wp10_event_snapshot_evidence_cluster_20260520.zh.md)
- [WP10-E Integration And Acceptance Handoff](../simulation_architecture/wp10_causal_runtime_foundation/wp10_integration_acceptance_cluster_20260520.zh.md)

## 1. 结论

WP10 验收通过，可作为第一条 code-owned causal runtime foundation slice
合入。当前实现提供了维护中的 `StageNodeManifest` registry、facade-side
scheduling-window loop skeleton、request injection 状态、schedule-construction
same-window validation，以及 engagement/observation slice 上 facade/binding 可见的
event/snapshot/barrier/source-time evidence。

边界需要保留：

- window loop 是 facade-side skeleton，不是全局 scheduler 替换。
- event ordering 的结论是 selected evidence families 内的稳定 facade export
  ordering，不是全局 event queue ordering。
- strict clock-domain enforcement、`ActionHoldPolicy`、Law 14 read-side
  enforcement、Agency Graph runtime authority、backend/fidelity promotion 与
  counterfactual/worldline branching 都留给后续阶段。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP10-A Manifest Registry Seed` | pass | `src/runtime/contracts/stage_node_manifest_registry.h` 定义维护中的 registry 与 `p7.fire_control_launch.v1`、`p9.effects_damage.v1`、`p10.observation_export.v1`；`tests/architecture/test_wp10_stage_node_manifest_registry.py` 验证 required fields 与 registry shape。 |
| `WP10-B Window Loop And Injection` | pass | `src/runtime/facade/runtime_window_coordinator.h`、`runtime_facade_types.h`、`runtime_facade.h`、`runtime_facade.cpp` 暴露 minimal window loop、barrier trace 与 accepted/deferred/rejected/expired request states；`tests/runtime/facade/test_runtime_facade_window_loop_injection.py` 验证聚焦行为。 |
| `WP10-C Same-Window Edge Validation` | pass | `src/core/engine/same_window_edge_validation.h` 使用 producer publish intent、consumer declaration、shared read/write contracts 与 acyclic construction 验证 declared same-window edges；`tests/architecture/test_wp10_same_window_edge_validation.py` 覆盖 passing/failing fixtures。 |
| `WP10-D Event And Snapshot Evidence` | pass | `src/runtime/contracts/engagement_contracts.h`、`src/runtime/facade/runtime_facade_types.h`、`src/runtime/facade/runtime_facade.cpp`、`src/interfaces/python/bindings_runtime.cpp` 暴露 snapshot、barrier、source-time、producer-node 与 diagnostics ancestry metadata；engagement、facade 与 binding tests 验证可见性。 |
| `WP10-E Integration And Acceptance Handoff` | pass | 在 `tests/architecture/test_runtime_facade_layering.py` 显式更新 diagnostics-only escape-hatch allowlist 后最终验证通过；本审查记录 commands、residuals 与下一阶段 handoff。 |

## 3. 验证命令

已通过：

```bash
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/engagement/test_facade_engagement_evidence_gates.py tests/runtime/engagement/test_diagnostics_trace_contract.py tests/runtime/engagement/test_trace_replay_gates.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/facade/test_runtime_facade.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_wp10_stage_node_manifest_registry.py tests/runtime/facade/test_runtime_facade_window_loop_injection.py tests/architecture/test_wp10_same_window_edge_validation.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_live_engagement_event_capture.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp9_infrastructure_closure_docs.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP10
git diff --check
```

观察结果：

- build：通过。
- WP10-D engagement/facade/binding 聚焦批次：`36 passed`。
- WP10 A/B/C/D 回归批次：`48 passed`。
- architecture closure/layering 批次：首次发现一个 allowlist drift；显式更新
  diagnostics-only 计数后 `17 passed`。
- runtime engagement/facade/bindings 批次：`88 passed`。
- `git diff --check`：通过。

## 4. 集成说明

- `tests/architecture/test_runtime_facade_layering.py` 已更新，因为
  `tests/runtime/engagement/test_facade_engagement_export.py` 现在有两个
  diagnostics-only `facade.runtime().world(...)` setup paths。该更新保持
  escape hatch 显式登记，而不是放松 guard。
- 当前本机 binding build 使用 `build-workshop`；其他 build directory 的旧结果不应作为
  WP10 验收依据。
- WP10 已无 runtime blocker。

## 5. 剩余工作与下一步

有意后移的 residuals：

- Phase 2 应把 selected causal seam 推进为更强的 facade vertical slice，并添加
  `ActionHoldPolicy` 与 information-state provenance labels。
- 后续 scheduler 工作应在 skeleton 稳定后再加入 strict clock-domain enforcement 与更宽的
  multi-rate scheduling。
- Law 14 read-side enforcement 与 Agency Graph runtime authority 留给后续
  information/agency enforcement 阶段。
- Backend/fidelity expansion 与 counterfactual/worldline branching 属于下游阶段，
  不应由 WP10 宣称完成。

建议下一 WP：从 post-WP9 route 打开 Phase 2 facade vertical slice，并把 WP10 的 node ids、
barrier ids 与 evidence metadata 作为不可绕过的 runtime seam。
