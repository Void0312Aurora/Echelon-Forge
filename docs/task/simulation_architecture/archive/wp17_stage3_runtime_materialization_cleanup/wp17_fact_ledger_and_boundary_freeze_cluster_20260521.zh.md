# WP17-A Fact Ledger And Boundary Freeze

状态：`2026-05-21` recovered / pass；当前代码事实已锁定，并作为后续实现波次的依据。

英文主文：[wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md](wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [Stage 3 platform expansion plan](../../review/stage3_platform_expansion_mainline_plan_20260521.md)
- [WP16 验收审查](../../review/wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md)

## 目标

在实现 worker 修改 runtime code 前冻结当前代码事实，避免后续工作沿用已经过时的 Stage 3 假设。

## 范围

范围内：

- 校验 WP17 主计划中的六项当前代码事实；
- 标出 runtime capabilities、batch/training reads、scheduler cadence、capability spawn 与 counterfactual runtime 的 maintained、compatibility、diagnostics-only 与 blocked surface；
- 同步首轮派发表中的依赖、模型预算与写入范围；
- 必要时补充 architecture guard inventory。

范围外：

- runtime 行为变更；
- public API 删除；
- README 或 acceptance closure。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `A1` | 代码事实账本 | 每项事实都有 source/test 锚点，并说明相对 Stage 3 计划的漂移。 |
| `A2` | Residual register | 每个 blocked residual 都有 owner stream、原因与 next trigger。 |
| `A3` | Dispatch board sync | 首轮任务包含模型/思考预算、依赖与写入范围。 |
| `A4` | Guard inventory | 现有 guard 足够，或命名缺失 guard candidate，但不修改 runtime code。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
python -m pytest -q tests/architecture/test_wp16_legacy_path_gates.py
```

## 交接

返回 touched files、verified facts、residual IDs、commands run，以及是否有实现流应在 code edits 前被阻塞。
