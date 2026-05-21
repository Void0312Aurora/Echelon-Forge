# WP21-E Experiment Facade And Evidence Collection

状态：`2026-05-21` planned；等待 WP21-C 与 WP21-D。

Language:

- English canonical:
  [wp21_experiment_facade_evidence_cluster_20260521.md](wp21_experiment_facade_evidence_cluster_20260521.md)
- Chinese companion: `wp21_experiment_facade_evidence_cluster_20260521.zh.md`

## 目的

暴露 maintained experiment runtime surface，并跨 setup、generation、branch rollout、
comparison、observations、rewards、terminations 与 traces 收集 evidence。

## 范围

范围内：

- 必要的 experiment run DTOs / facade methods / Python bindings；
- 收集 parent/branch observations、rewards、terminations、traces、causal differences、
  generated-input artifacts 与 evidence ancestry；
- 继承 WP15 的 non-truth-claim 与 support-promotion guards；
- 聚焦测试证明完整 ancestry 与 public visibility。

范围外：

- broad curriculum learning runtime；
- 从 experiment scores 晋级 capability 或 backend support；
- exact GPU 或 resident-state promotion。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `E1` | Experiment run surface | Maintained facade surface 可从 admitted inputs 创建或运行 bounded experiment。 |
| `E2` | Evidence collection | 结果包含 observations、rewards、terminations、traces、causal differences 与 generated-input refs。 |
| `E3` | Ancestry validation | Replay envelope、branch point、setup/generation、backend/fidelity 与 capability refs 存在且一致。 |
| `E4` | Public/binding proof | Python binding 或 facade tests 证明 visibility 与 fail-closed non-truth-claim behavior。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp15_experiment_evidence_bridge.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "experiment or counterfactual or worldline"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "experiment or counterfactual"
```

## 交接

返回 facade/binding surface、evidence schema、ancestry checks、non-truth-claim guards、
touched files、commands run，以及给 F 的 final cleanup notes。
