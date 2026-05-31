# Validation Uncertainty Review Gate - 2026-05-31

状态：`uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked / non-authoritative`。

本文档记录 `RES-011` uncertainty review gate 的当前机器化验收结果。它只固化
Stage B 与 Stage C 的 uncertainty 证据分层，不创建 stock descriptor，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 1. Gate Artifact

| 字段 | 值 |
|---|---|
| `tool_ref` | [a2_blastfrag_uncertainty_review_gate.py](../../../../../../tools/maintenance/a2_blastfrag_uncertainty_review_gate.py) |
| `test_ref` | [test_a2_blastfrag_uncertainty_review_gate.py](../../../../../../tests/architecture/test_a2_blastfrag_uncertainty_review_gate.py) |
| `retained_gate` | [uncertainty_review_gate.json](retained_artifacts/uncertainty_review_20260531/uncertainty_review_gate.json) |
| `retained_manifest` | [manifest.json](retained_artifacts/uncertainty_review_20260531/manifest.json) |
| `review_target` | `RES-011_uncertainty_review_only` |
| `release_target` | `none_review_gate_record_only` |

## 2. Stage B Result

Stage B `effect_scale` 的 author-side seed-window CV closeout 已通过当前阈值：

| metric | 当前结论 |
|---|---|
| `fragment_areal_density_per_m2.cv` | pass |
| `blast_impulse_kpa_ms_proxy.cv` | pass |
| `fragment_energy_j_proxy.cv` | pass |
| `penetration_margin_proxy.cv` | pass |

该结果只允许描述为 `narrow_author_side_uncertainty_closeout_complete_release_blocked`。
它仍缺 independent uncertainty reviewer signoff、coverage 解释和 result-level
uncertainty audit，因此不得解释为 release-grade uncertainty boundary。

## 3. Stage C Result

Stage C `right_aileron_actuator` component probability 当前只有 fixed-seed repeatability
与 candidate-vs-synthetic evidence：

| 字段 | 值 |
|---|---|
| `anchor_probe_label` | `middle` |
| `seed_values` | `20260526 / 20260527 / 20260528` |
| `component_failure_probability_cv` | `0.0` |
| `blocking_condition_id` | `BLOCK-CP-004` |

Stage C 仍保持 `blocked_probability_uncertainty_coverage_missing`，因为它缺：

- independent calibration 或 coverage scoring；
- author-side probes 之外的 scenario spread；
- reviewer-accepted confidence 或 coverage interval；
- stock descriptor admission 所需的 release-grade uncertainty budget。

## 4. RES-011 判定

当前 `RES-011` 的合并判定为：

> Stage B author-side uncertainty closeout 可作为窄域 review input；Stage C probability
> uncertainty 仍 blocked；整体 `RES-011` 继续保持 release-grade blocked。

不允许的解释：

- 不得把 Stage B CV pass 上卷为 release-grade uncertainty coverage；
- 不得把 Stage C repeatability 当作 probability calibration；
- 不得因为本 gate 存在而关闭 `RES-010`、`RES-012`、`RES-013` 或 `RES-014`；
- 不得从本 gate 推出 stock/runtime authority。

## 5. Validation

已运行：

```bash
python3 tools/maintenance/a2_blastfrag_uncertainty_review_gate.py
pytest -q tests/architecture/test_a2_blastfrag_uncertainty_review_gate.py
```

测试结果：`4 passed`。
