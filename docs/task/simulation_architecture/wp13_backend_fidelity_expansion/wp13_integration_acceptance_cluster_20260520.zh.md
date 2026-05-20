# WP13-F Integration And Acceptance Handoff

状态：`2026-05-20` planned / serial closure lane。

语言版本：

- 英文主文：[wp13_integration_acceptance_cluster_20260520.md](wp13_integration_acceptance_cluster_20260520.md)
- 中文辅文：`wp13_integration_acceptance_cluster_20260520.zh.md`

输入：

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP13-A runtime capability query](wp13_runtime_capability_query_cluster_20260520.zh.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.zh.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)
- [WP13-D fidelity profile request gate](wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)
- [WP13-E facade and binding proof](wp13_facade_binding_proof_cluster_20260520.zh.md)
- [Post-WP9 architecture route plan](../post_wp9_architecture_route_plan_20260520.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

`WP13-F` 是串行 integration 与 acceptance handoff lane。它整合 A-E implementation
streams、记录精确 validation outcomes、发布 residual register，并准备 acceptance review。

它不应阻塞 A-E 达到 `Mergeable`，而是在 implementation evidence 已存在后运行。

## 2. 范围

范围内：

- 验证 A-E touched files、commands、blockers 与 residuals；
- 执行或记录最终 validation commands；
- 更新 simulation architecture README/index entries；
- 只有在 implementation evidence 支撑时，才把 post-WP9 route status 从 Phase 4 planned
  更新为 active/accepted；
- gates 通过后发布英文和中文 acceptance review；
- 确保最终 commit messages 使用 capability/result language，避免 internal WP labels。

范围外：

- 未获得 integration ownership 时编辑 A-E implementation semantics；
- 隐藏 failed 或 blocked validation；
- 声称 exact GPU、resident-state、shadow、adaptive fidelity 或 learned provider support；
- 把 documentation-only output 当作 implementation closure。

## 3. 验收包清单

最终 handoff 必须包含：

| Item | Required content |
|------|------------------|
| Gate verdict table | A-E pass/fail/blocked 与一行证据。 |
| Validation commands | 精确 command、status 与短 outcome。 |
| Runtime surface summary | 新 DTOs/helpers/fields 与 compatibility impact。 |
| Conservative support statement | 明确说明 unsupported backend/fidelity support 仍为 false。 |
| Residual register | 具名 residuals，含 owner、reason 与 next-phase recommendation。 |
| Index sync | README、route plan、review index 与 bilingual companions 已检查。 |
| Commit-message note | 最终建议 commit title 避免 internal work-package labels。 |

## 4. 验证命令

预期最终 validation set：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/test_runtime_facade_layering.py
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP13
```

若命令被环境阻塞，应记录 blocker 和最窄替代证据。不得在未运行测试且无理由时标记 gate accepted。

## 5. Review 草稿要求

创建：

- `docs/task/review/wp13_backend_fidelity_expansion_acceptance_review_20260520.md`
- `docs/task/review/wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md`

review 必须说明：

- accepted scope 与 non-scope；
- A-E gate verdicts；
- validation outcomes；
- 哪些 unsupported support claims 仍为 false；
- future exact GPU、resident-state、shadow、adaptive fidelity、`ModelProvider` 与 capability
  composition work 的 residuals；
- 推荐下一阶段：只有 backend/fidelity query 与 rejection gates 通过后才进入 capability composition。

## 6. 交接契约

返回：

- A-F final status；
- integration/closure touched files；
- 精确 commands 与 outcomes；
- 若已创建，提供 acceptance review links；
- residuals 与 recommended next action；
- 不含 `WP13` 的 capability/result-oriented commit message 建议。
