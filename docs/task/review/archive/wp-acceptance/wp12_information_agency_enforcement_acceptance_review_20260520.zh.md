# WP12 Information And Agency Enforcement 验收审查

状态：`2026-05-20` accepted / implementation mergeable。

语言：

- 英文主文：[wp12_information_agency_enforcement_acceptance_review_20260520.md](wp12_information_agency_enforcement_acceptance_review_20260520.md)
- 中文辅文：`wp12_information_agency_enforcement_acceptance_review_20260520.zh.md`

输入：

- [WP12 Information And Agency Enforcement](../simulation_architecture/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)
- [WP12-A Law 14 Read-Side Enforcement](../simulation_architecture/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.zh.md)
- [WP12-B Agency Role Authority Boundary](../simulation_architecture/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.zh.md)
- [WP12-C Information Transformation Surface](../simulation_architecture/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.zh.md)
- [WP12-D Intent Injection Authority Guard](../simulation_architecture/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.zh.md)
- [WP12-E Integration And Acceptance Handoff](../simulation_architecture/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.zh.md)
- [WP11 验收审查](wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md)

## 1. 结论

WP12 验收通过，可作为 Phase 3 information and agency enforcement increment
合入。它把 WP11 provenance/pre-gate 词汇推进为 focused、test-backed read-side、
authority、transformation 与 intent-injection guards。

边界需要保留：

- Law 14 enforcement 只覆盖 selected maintained consumer 与 belief/intent
  fixtures，不是 repository-wide static coverage。
- `AgentRole` authority validation 是第一个 maintained authority slice，不是完整
  Agency Graph runtime dispatch。
- Information transformation evidence 是 selected slice 的 contract/helper
  surface，没有迁移所有 sensor、track 或 data-link producer。
- Intent injection enforcement 是 contract-level / architecture-level guard
  evidence，尚未接入 `run_wp10_window()` request admission。
- 不声明 backend/fidelity、capability composition、counterfactual/worldline 或
  policy/control/physics cadence。

## 2. Gate 结论

| Gate | 结论 | 证据 |
|------|------|------|
| `WP12-A Law 14 Read-Side Enforcement` | pass | `python/rl/runtime/agent_shim.py`、`tests/runtime/test_agent_shim.py` 与 `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py` 对 provenance-labeled `ObservationPacket` / `DecisionBelief` inputs 建立 focused maintained read-side allowlist，同时保持 diagnostics-only truth/raw paths 显式。 |
| `WP12-B Agency Role Authority Boundary` | pass | `src/runtime/contracts/policy_contracts.h`、`src/interfaces/python/bindings_runtime.cpp`、`tests/runtime/mission/test_policy_contract_shape.py`、`tests/runtime/bindings/test_bindings_runtime_dto_surface.py` 与 `tests/architecture/policy_execution/test_agent_role_authority.py` 增加 fail-closed `AgentRole` authority/source/interface validation 与 Python-visible authorization helpers。 |
| `WP12-C Information Transformation Surface` | pass | `src/runtime/contracts/information_transform_contracts.h` 与 `tests/architecture/policy_execution/test_information_transformation_surface.py` 增加 canonical transformation vocabulary、evidence structs、validators、diagnostics-only shortcut rules，以及 invalid belief-to-intent provenance 负例。 |
| `WP12-D Intent Injection Authority Guard` | pass | `src/runtime/contracts/information_transform_contracts.h` 与 `tests/architecture/policy_execution/test_intent_injection_authority_guard.py` 把 A/B/C 组合为 `authorize_maintained_decision_belief_action_intent_injection()`，覆盖 authority、transformation、ancestry、timing、merge-policy 与 no-raw-facade-bypass checks。 |
| `WP12-E Integration And Acceptance Handoff` | pass | 本审查记录 A-D 状态、validation commands、residuals、route/index updates 与 closure-lane scope boundary。 |

## 3. 验证命令

已通过：

```bash
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/policy_execution/test_intent_injection_authority_guard.py tests/architecture/policy_execution/test_agent_role_authority.py tests/architecture/policy_execution/test_information_transformation_surface.py tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py tests/runtime/test_agent_shim.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/mission/test_policy_contract_shape.py tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
git diff --check
```

本审查前观察结果：

- WP12 architecture guard set：`25 passed`。
- Runtime facade/window plus agent shim set：`20 passed`。
- Mission/bindings contract set：`31 passed`。
- `git diff --check`：通过。

最终 closure validation 还应运行：

```bash
cmake --build build-workshop -j4
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP12
```

## 4. 集成说明

- WP12-A 保留 diagnostics-only truth/raw runtime paths，不增加全局 raw ECS ban。
- WP12-B 当前授权的第一个 maintained authority vocabulary 是：
  `platform_control -> PilotActionAssignmentCompat / pilot_action`、
  `mission_command -> CommandChainAssignmentCompat / mission_command` 与
  `formation_coordination -> CommandChainAssignmentCompat /
  coordination_intent`。
- WP12-C 的 transformation surface 保持独立，不要求大范围 DTO/binding expansion。
- WP12-D 组合已验收 A/B/C helpers，没有新增第二套 authority 或 injection path。
- `RuntimeFacade` 没有新增 maintained raw injection API。

## 5. 剩余工作与下一步

有意后移的 residuals：

- 在声明 runtime admission enforcement 前，把
  `authorize_maintained_decision_belief_action_intent_injection()` 接入 maintained
  facade-compatible request admission seam。
- 当打开具体 maintained coordination-injection slice 时，把组合 guard 扩展到
  `CoordinationIntentPacket`。
- 只有在存在更宽 static 或 runtime guard 方案后，才把 Law 14 coverage 扩出
  selected Python/architecture fixtures。
- 完整 Agency Graph runtime dispatch、覆盖每个 producer 的 role-based access
  control 与 decision-model dispatch 保留给后续工作。
- Backend/fidelity expansion 只有在本 information/agency evidence boundary
  验收后，才进入下一条 post-WP9 route phase。

建议下一 WP：开启 Phase 4 backend/fidelity expansion，并把 WP10 causal seam、WP11
provenance 与 WP12 enforcement guards 作为 evidence boundary。不要在缺少
query/reject/evidence gates 时晋升 exact GPU、resident-state、shadow 或
multi-fidelity capability。
