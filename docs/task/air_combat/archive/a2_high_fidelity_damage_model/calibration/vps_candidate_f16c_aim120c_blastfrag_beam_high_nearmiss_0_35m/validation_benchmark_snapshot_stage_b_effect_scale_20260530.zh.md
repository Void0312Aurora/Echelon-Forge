# Validation Benchmark Snapshot - Stage B Effect Scale

状态：`generated_from_candidate_snapshot / non-authoritative / stage_b_effect_scale_only`。

本文档记录当前候选包按 frozen Stage B `effect_scale_authority` hard gates
生成的第一版 benchmark snapshot。它来自
[damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts effect-scale-snapshot`
对当前 non-authoritative validation scaffold 的固定种子执行结果。

本文档不是独立 validation result，不创建 runtime descriptor，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `snapshot_status` | `author_snapshot_complete_pending_independent_review` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `seed` | `20260529` |
| `sample_count` | `4096` |
| `criteria_ref` | [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md) |
| `scaffold_ref` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts validation-scaffold` |
| `snapshot_artifact_ref` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `candidate-artifacts effect-scale-snapshot` |
| `stock_runtime_action` | `forbidden_pending_independent_review_and_residual_closeout` |

## 2. Hard-Gate Snapshot

当前固定种子 snapshot 对 Stage B frozen hard gates 的执行结果如下：

| `criteria_id` | benchmark | 字段 | 当前值 | 门槛 | 结果 |
|---|---|---|---:|---|---|
| `BFM-CRIT-ES-001` | `BFM-BM-001` | `metrics.unit_roundtrip_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-002` | `BFM-BM-001` | `metrics.monotonic_overpressure_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-003` | `BFM-BM-001` | `metrics.monotonic_impulse_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-004` | `BFM-BM-003` | `metrics.fixed_seed_replay_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-005` | `BFM-BM-003` | `metrics.isotropy_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-006` | `BFM-BM-003` | `metrics.sampling_convergence_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-007` | `BFM-BM-003` | `sampling_convergence_summary.relative_delta` | `0.0008023536` | `<= 0.05` | `pass` |
| `BFM-CRIT-ES-008` | `BFM-BM-005` | `metrics.source_trace_completeness_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-009` | `BFM-BM-005` | `metrics.unit_consistency_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-010` | `BFM-BM-005` | `metrics.forbidden_authority_fields_absent` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-011` | `BFM-BM-005` | `metrics.uncertainty_summary_present` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-012` | `BFM-BM-005` | `metrics.seed_window_cv_pass` | `true` | `true` | `pass` |
| `BFM-CRIT-ES-013` | `BFM-BM-005` | `uncertainty_summary.fragment_areal_density_per_m2.cv` | `0.0135564757` | `<= 0.05` | `pass` |
| `BFM-CRIT-ES-014` | `BFM-BM-005` | `uncertainty_summary.blast_impulse_kpa_ms_proxy.cv` | `0.0` | `<= 0.05` | `pass` |
| `BFM-CRIT-ES-015` | `BFM-BM-005` | `uncertainty_summary.fragment_energy_j_proxy.cv` | `0.0` | `<= 0.05` | `pass` |
| `BFM-CRIT-ES-016` | `BFM-BM-005` | `uncertainty_summary.penetration_margin_proxy.cv` | `0.0149534283` | `<= 0.05` | `pass` |
| `BFM-CRIT-ES-017` | `BFM-BM-006` | `metrics.source_trace_error_count` | `0` | `= 0` | `pass` |
| `BFM-CRIT-ES-018` | `BFM-BM-006` | `metrics.source_trace_warning_count` | `0` | `= 0` | `pass` |

当前 snapshot 结论：

- 当前固定种子 candidate snapshot 覆盖的 `18` 个 Stage B hard gates 全部通过；
- 这只说明“当前 scaffold 产物与 frozen hard gates 一致”，不说明 surrogate 已经被独立验证；
- 该表仍不能单独触发 authority release。

## 3. 当前关键数值

| benchmark | 关键字段 | 当前值 |
|---|---|---:|
| `BFM-BM-001` | `blast_scaled_distance_m_kg13 @ 0.35 m` | `0.1289411025` |
| `BFM-BM-001` | `blast_overpressure_kpa_proxy @ 0.35 m` | `2990.1978360199` |
| `BFM-BM-001` | `blast_impulse_kpa_ms_proxy @ 0.35 m` | `1818.2329693285` |
| `BFM-BM-003` | `beam_witness_areal_density_per_m2` | `2.2375438053` |
| `BFM-BM-003` | `hit_count` | `1871` |
| `BFM-BM-005` | `fragment_energy_j_proxy` | `8038.5061543833` |
| `BFM-BM-005` | `penetration_margin_proxy` | `474.2814124898` |
| `BFM-BM-005` | `fragment_areal_density_per_m2.cv` | `0.0135564757` |
| `BFM-BM-005` | `blast_impulse_kpa_ms_proxy.cv` | `0.0` |
| `BFM-BM-005` | `fragment_energy_j_proxy.cv` | `0.0` |
| `BFM-BM-005` | `penetration_margin_proxy.cv` | `0.0149534283` |

## 4. 当前解释边界

这份 snapshot 当前只允许支持以下结论：

- Stage B `effect_scale_authority_only` 的 frozen hard gates 已经有一张可执行、可追溯、可复跑的 candidate result table；
- uncertainty 摘要已经不再只是门槛设计，而是有了固定种子的候选结果；
- `BFM-BM-006` 的 source-trace 行政门禁在当前 snapshot 下没有报错或 warning。

这份 snapshot 当前**不能**支持以下结论：

- `effect_scale_authority` 已经 validated；
- `beam / high / near_miss_0_35m` 已完成独立 review；
- `closure` 物理敏感性已经成立；
- stock runtime authority 已经可以放行。

## 5. 对 residual 的推进含义

这份 snapshot 形成后，相关 residual 当前应解释为：

- `RES-010`：从“缺 benchmark result table”推进到“已有 candidate benchmark snapshot”，但独立 reviewer signoff、artifact hash closeout 与 result-level release 审计仍缺；
- `RES-011`：从“只有 uncertainty gate 设计”推进到“已有 uncertainty snapshot”，但 coverage 解释和独立 review 仍缺；
- `RES-012`：当前 snapshot 仍依赖 repo-authored scaffold，只能作为 author-side review artifact，不能冒充独立 validation。

上述 residual 都**不关闭**。

## 6. 当前判定

当前判定为：

> `Stage B effect-scale hard gates now have a first fixed-seed candidate benchmark snapshot, but the snapshot remains non-authoritative, non-independent, and insufficient for stock authority release`.
