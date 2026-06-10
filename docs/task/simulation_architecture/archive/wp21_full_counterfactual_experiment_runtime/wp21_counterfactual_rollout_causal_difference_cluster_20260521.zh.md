# WP21-C Counterfactual Rollout And Causal Difference

状态：`2026-05-21` planned；等待 WP21-B。

Language:

- English canonical:
  [wp21_counterfactual_rollout_causal_difference_cluster_20260521.md](wp21_counterfactual_rollout_causal_difference_cluster_20260521.md)
- Chinese companion: `wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md`

## 目的

从 admitted inputs 执行 parent 与 branch worldlines，并在声明的 barriers 上产生
causal-difference evidence。该任务把 selected branch/compare proof 转为 maintained
runtime behavior。

## 范围

范围内：

- 从 explicit setup、restore boundary 或 deterministic generated artifact 执行 parent/branch rollout；
- deterministic seed derivation 与 replay envelope checks；
- 在 selected slice 中输出 state、observation、termination 与 trace refs 的 causal difference records；
- 对 raw authoritative mutation 与 unsupported restore scope 做 fail-closed rejection。

范围外：

- broad curriculum orchestration；
- 从 branch outcomes 晋级 truth/support；
- unlimited worldline tree management。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `C1` | Branch execution | Parent 与 branch 从 admitted setup/restore inputs 独立运行。 |
| `C2` | Determinism evidence | Replay envelope、seed、branch point 与 barrier refs 被记录并验证。 |
| `C3` | Causal difference | Runtime 在每个声明 comparison barrier 输出 comparable deltas 与 evidence refs。 |
| `C4` | Rejection behavior | Unsupported mutation、missing envelope/branch point、invalid restore scope 与 unsupported fidelity fail closed。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or causal or worldline"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
```

## 交接

返回 rollout semantics、comparison schema、determinism evidence、touched files、
commands run，以及面向 E 的 experiment collection notes。
