# WP11 Facade Vertical Slice And Provenance 验收审查

状态：`2026-05-20` accepted / implementation mergeable。

语言：

- 英文主文：[wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md](wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md)
- 中文辅文：`wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md`

输入：

- [WP11 Facade Vertical Slice And Provenance](../simulation_architecture/wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP11-A ActionHoldPolicy Contract](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.zh.md)
- [WP11-B Information Provenance Labels](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_information_provenance_labels_cluster_20260520.zh.md)
- [WP11-C Facade Vertical Slice Proof](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_facade_vertical_slice_proof_cluster_20260520.zh.md)
- [WP11-D Consumer Boundary Pre-Gates](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.zh.md)
- [WP11-E Integration And Acceptance Handoff](../simulation_architecture/wp11_facade_vertical_slice_provenance/wp11_integration_acceptance_cluster_20260520.zh.md)
- [WP10 acceptance review](wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md)

## 1. 结论

WP11 验收通过，可作为 Phase 2 facade vertical slice and provenance increment
合入。它添加了 `ActionHoldPolicy` contract、稳定 information-state provenance labels、
基于 WP10 seam 的 facade/binding proof，以及 focused consumer boundary pre-gates。

边界需要保留：

- `ActionHoldPolicy` 已 contract-visible 和 binding-visible，但不实现 runtime
  policy/control/physics cadence。
- Consumer boundary 工作是 `GAP-5` precursor，不是完整 Law 14 read-side
  enforcement。
- Vertical proof 不替换 scheduler，不扩张 broad facade，也没有新增 raw runtime escape
  hatch。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP11-A ActionHoldPolicy Contract` | pass | `src/runtime/contracts/policy_contracts.h` 定义 `ActionHoldPolicy`；`src/interfaces/python/bindings_runtime.cpp` 暴露 `ef_py.ActionHoldPolicy`；`tests/runtime/mission/test_policy_contract_shape.py`、`tests/runtime/bindings/test_bindings_policy_surface.py`、`tests/architecture/test_wp11_action_hold_policy_contract.py` 验证字段、保守默认值和 fail-closed normalization。 |
| `WP11-B Information Provenance Labels` | pass | `InformationStateSource`、canonical information-state/status vocabulary、packet provenance fields 与 `DecisionBelief` validators 已在 contracts、facade packet types、runtime exports、bindings 与 focused tests 中可见。 |
| `WP11-C Facade Vertical Slice Proof` | pass | Engagement/facade/binding tests 证明 `p7.fire_control_launch.v1`、`p9.effects_damage.v1`、`p10.observation_export.v1` node evidence，以及 export barrier、snapshot/source-time metadata、diagnostics ancestry 和 maintained/diagnostics provenance labels。 |
| `WP11-D Consumer Boundary Pre-Gates` | pass | `python/rl/runtime/agent_shim.py`、`tests/runtime/test_agent_shim.py`、`tests/architecture/test_policy_belief_boundaries.py` 拒绝 unlabeled maintained consumer fixtures，同时保留显式 diagnostics-only truth/raw-ECS fixtures。 |
| `WP11-E Integration And Acceptance Handoff` | pass | 本审查记录 A-D 状态、validation commands、residuals 与 closure-lane handoff。 |

## 3. 验证命令

已通过：

```bash
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_policy_surface.py tests/architecture/test_wp11_action_hold_policy_contract.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py tests/runtime/facade/test_runtime_dto_promotion_batch1.py tests/runtime/facade/test_runtime_facade.py tests/architecture/test_policy_belief_boundaries.py tests/runtime/mission/test_policy_contract_shape.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/engagement/test_facade_engagement_export.py tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/facade/test_runtime_facade_window_loop_injection.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_policy_belief_boundaries.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_wp11_action_hold_policy_contract.py
git diff --check
```

观察结果：

- build：通过。
- WP11-A 聚焦测试：`17 passed`。
- WP11-A/B 组合聚焦测试：`45 passed`。
- WP11-C vertical slice proof tests：`36 passed`。
- WP11-D consumer pre-gate tests：`20 passed`。
- Architecture guard / ActionHoldPolicy 批次：`16 passed`。
- `git diff --check`：通过。

## 4. 集成说明

- `ActionHoldPolicy` 默认值保持保守且显式 declarative，不得描述为 cadence execution。
- Provenance labels 现在通过 `ObservationBatchPacket.provenance`、
  `EngagementEventPacket.packet_provenance` 与
  `EngagementEventPacket.diagnostics_provenance` 可见。
- `DecisionBelief` truth/raw-ECS 使用通过 validator helpers 变得 diagnostics-visible，
  但完整 Law 14 enforcement 仍后移。
- `run_wp10_window` 仍未 Python-bound；vertical proof 由 facade/window tests 与 live
  facade/binding tests 分段完成。
- WP11-C 未新增 raw runtime escape hatch。

## 5. 剩余工作与下一步

有意后移的 residuals：

- 完整 policy/control/physics multi-rate cadence 应在后续 cadence slice 中消费
  `ActionHoldPolicy`。
- 完整 Law 14 enforcement 仍需要更宽的 read-side static 或 runtime guards。
- Agency Graph authority scope、role-based access control 与 decision-model dispatch
  留给后续 information/agency enforcement。
- `SensedState` 与 `SharedTacticalPicture` 是 vocabulary entries，但 WP11 没有把它们接成新的
  runtime producers。
- Backend/fidelity expansion、capability composition 与 counterfactual worldline work
  仍属于下游阶段。

建议下一 WP：开启 information and agency enforcement phase，并以 WP11 provenance labels
与 consumer pre-gates 作为起点边界。
