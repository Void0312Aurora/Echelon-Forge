# WP17-F Counterfactual Runtime Slice And Closure

状态：`2026-05-21` narrowed selected-slice runtime implemented；focused validation passed。

英文主文：[wp17_counterfactual_runtime_closure_cluster_20260521.md](wp17_counterfactual_runtime_closure_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP8 learning face](../wp8_learning_face/learning_face_wp8_20260520.md)

## 目标

添加第一条 executable counterfactual slice，并关闭最终 legacy cleanup lane。已接受目标是 explicit-setup selected-entity snapshot/branch/compare path，不是 arbitrary live-world clone 或 full experiment orchestration。

## 入口条件

- WP17-C 已为 selected runtime slice 提供 deterministic cadence/barrier evidence。
- WP17-D 将 accepted fidelity/profile scope 命名为通过 `RuntimeFacade::admit_fidelity_request()` 选择的 reference CPU exact baseline。
- WP17-B 已把 maintained business access 从 compatibility-only `batch_runtime` reads 中收束出来。

## 范围

范围内：

- 对一个 selected entity snapshot position、velocity、orientation 与 minimal physics state；
- 从 explicit `BatchWorldSetupRequest` baseline 创建 branch，携带 deterministic seed 与 mutation metadata；
- 在 barrier 上比较 parent/branch selected entity 并输出 causal deltas；
- final legacy cleanup guard review 与 closure-lane handoff。

范围外：

- arbitrary-depth worldline trees；
- arbitrary live-world reflection/clone 作为 branch baseline；
- full curriculum 或 adversarial experiment orchestration；
- 无 admission 的 generated scenario mutation of authoritative runtime state；
- replacement evidence 完成前删除 compatibility APIs。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `F1` | Physics snapshot/restore | `RuntimeFacade::snapshot_counterfactual_entity()` 捕获 selected-entity position、velocity、orientation、fidelity/provider、cadence、barrier 与 evidence refs。 |
| `F2` | Branch rollout | `RuntimeFacade::run_counterfactual_branch()` 从 explicit setup 构建 parent/branch worlds，应用 facade-owned selected-entity mutation，并拒绝 raw authoritative mutation。 |
| `F3` | Causal comparison | `RuntimeWorldlineComparison` 在 counterfactual barrier 报告 selected-slice deltas。 |
| `F4` | Final cleanup handoff | Legacy paths retained、deprecated 或 blocked 都记录 guard 与 closure-owner notes。 |

## 实现证据

Runtime surfaces：

- `RuntimeCounterfactualSnapshot`
- `RuntimeCounterfactualBranchRequest`
- `RuntimeCounterfactualBranchResult`
- `RuntimeWorldlineComparison`
- `RuntimeFacade::snapshot_counterfactual_entity()`
- `RuntimeFacade::run_counterfactual_branch()`

已接受语义：

- branch baselines 必须来自 explicit `BatchWorldSetupRequest`；
- reference CPU exact-evaluation fidelity 可被 admission；
- resident/exact-GPU/shadow provider requests fail closed；
- `allow_raw_authoritative_state_mutation` 被拒绝；
- WP15 metadata-only replay/admission contracts 对 full snapshot/restore support 仍保持 fail-closed。

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_*.py
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py -k "barrier or evidence"
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or fidelity or provider"
```

## 交接

返回 snapshot scope、determinism evidence、rollout/compare behavior、commands run、final residuals 与 closure-lane requirements。
