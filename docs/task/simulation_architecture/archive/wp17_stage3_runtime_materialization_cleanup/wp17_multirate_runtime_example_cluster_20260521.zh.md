# WP17-C Multi-Rate Runtime Example

状态：`2026-05-21` implemented / focused validation passed for the selected runtime-window cadence slice。

英文主文：[wp17_multirate_runtime_example_cluster_20260521.md](wp17_multirate_runtime_example_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP2.5 scheduler semantics](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)
- [WP11 ActionHoldPolicy](../wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.zh.md)
- [WP16 clock-domain enforcement](../wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.zh.md)

## 目标

让架构 §8 示例在一个 maintained slice 上可运行：policy 10Hz、control 20Hz、physics 60Hz，observation 在 policy boundary 采样，并输出显式 hold/skip evidence。

## 范围

范围内：

- 一个 selected window-loop slice 的 nested clock-domain trigger/skip 行为；
- runtime 消费 `ActionHoldPolicy.hold_last`、expiry 与可选 interpolation evidence；
- 聚焦 fixture 证明 policy/control/physics tick counts 与 observation barrier versions；
- 区分 skipped、held、interpolated 与 expired actions 的 diagnostics。

范围外：

- global scheduler rewrite；
- independent wall-clock domains；
- backend/fidelity 或 capability composition changes；
- counterfactual rollout claims。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `C1` | Cadence planner | Selected nodes 声明 policy/control/physics cadence，并产生 trigger/skip decisions。 |
| `C2` | Hold policy runtime | `hold_last` 在 control ticks 之间可见，expiry 会丢弃 stale input 并产生 evidence。 |
| `C3` | §8 runnable fixture | 测试验证一个或多个 100ms windows 的 10Hz/20Hz/60Hz counts 与 barrier exports。 |
| `C4` | Advisory flag boundary | 已声明 maintained slice 不再依赖 silent advisory behavior；global advisory residual 保持诚实。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_spine/test_clock_domain_enforcement.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "clock or cadence or hold or barrier"
```

## 交接

返回 scheduler files touched、cadence semantics、evidence fields、commands run，以及 selected slice 外仍保持 advisory 的部分。
