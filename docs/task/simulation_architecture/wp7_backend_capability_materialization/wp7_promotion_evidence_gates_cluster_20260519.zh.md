# WP7-C 分发单：Promotion Evidence Gates

状态：`2026-05-19` WP7 晋级门计划分发单。

语言版本：

- 英文主文：[wp7_promotion_evidence_gates_cluster_20260519.md](wp7_promotion_evidence_gates_cluster_20260519.md)
- 中文辅文：`wp7_promotion_evidence_gates_cluster_20260519.zh.md`
- 实现级说明：
  [wp7_promotion_evidence_gates_notes_20260519.zh.md](wp7_promotion_evidence_gates_notes_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP6 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [WP6 parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
- [WP6 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)

## 1. 目的

WP7-C 定义 backend candidate 成为维护中 capability 前必须通过的证据门。它是
gate-design 任务，不是 promotion 任务。
它不改变任何 candidate 的 `maintained_status`、parity budget acceptance 或
capability projection。

当前候选 profile 仍保持未维护：

1. `gpu_exact.unmaintained_candidate`
2. `resident_state.unmaintained_candidate`
3. `shadow_compare.unmaintained_candidate`

## 2. 必需工作项

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP7-C1 Exact GPU Promotion Gate` | event-order identity、snapshot identity、ownership/sync、parity budget 与 replay validation checklist。 | 文档与未来测试计划。 | 高。 |
| `WP7-C2 Resident-State Promotion Gate` | host/backend owner split、sync cadence、barrier id、reconstruction/export、stale-state policy 与 validation evidence checklist。 | 文档与未来测试计划。 | 高。 |
| `WP7-C3 Shadow Compare Promotion Gate` | non-interference、diagnostics separation、ancestry、mismatch policy，以及 shadow output 是否可能影响 committed state 的 checklist。 | 文档与未来测试计划。 | 高。 |
| `WP7-C4 WP5 Harness Mapping` | 把每个 promotion gate 映射到 design、trace、boundary、information 与 replay/evidence validation tier。 | 文档与 test-index 提案。 | 中高。 |

## 3. 必需晋级证据

任何 promotion proposal 都必须提供：

1. 维护中的 backend profile registry revision；
2. 维护中的 parity budget revision；
3. host/backend ownership 与 sync policy；
4. event order 与 snapshot/version evidence；
5. 非维护中 state 的 diagnostics label；
6. mismatch 与 quarantine policy；
7. replay evidence；
8. facade/core layering evidence；
9. WP5 harness coverage；
10. 更新 capability projection rule 的 acceptance review。

详细 gate 定义位于实现级说明中。它们定义三个命名 gate：

1. `exact_gpu_promotion_gate`，对应
   `gpu_exact.unmaintained_candidate`；
2. `resident_state_promotion_gate`，对应
   `resident_state.unmaintained_candidate`；
3. `shadow_compare_promotion_gate`，对应
   `shadow_compare.unmaintained_candidate`。

每个 gate 都必须 fail-closed。如果 profile registry revision、parity
budget revision、ownership/sync contract、event order/snapshot evidence、
mismatch/quarantine policy、replay evidence、facade/core layering evidence、
WP5 harness mapping 或 acceptance review 中任意一项缺失或不完整，被晋级
capability 的 capability projection 必须保持 false。

WP7-D fidelity request，包括 `fast_training`、`sensor_heavy` 与
`weapon_effects_heavy`，不能绕过任何 promotion gate。request label 可以表达
期望执行形态或验证重点，但不能把 unmaintained candidate 转换成 maintained
support。

## 4. 非目标

- 本任务簇不晋级任何 profile。
- 不实现 exact GPU world-step。
- 不实现 resident-state runtime code。
- 不让 shadow output 影响 committed state。
- 没有 acceptance review 不放松 WP6 candidate 状态。

## 5. 验收门槛

本任务簇在以下条件满足时验收：

1. 每个当前 candidate 都有命名 promotion gate。
2. 每个 gate 都命名必需的 profile、parity、ownership、sync 与 validation evidence。
3. 每个 gate 都映射到 WP5 validation tiers。
4. 文档说明 gate 失败或不完整时 capability projection 保持 false。
5. 文档说明 WP7-D fidelity request 不能绕过 promotion gate 证据。
6. 没有措辞暗示当前已经维护 exact GPU、resident-state 或 shadow compare support。

## 6. 验证命令

```bash
git diff --check
rg -n "gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|promotion gate|WP5|replay|mismatch|quarantine|acceptance review|capability projection" docs/task/simulation_architecture/wp7_promotion_evidence_gates*20260519*.md
```
