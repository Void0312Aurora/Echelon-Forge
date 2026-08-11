# Validation Metrics And Acceptance Criteria - Stage B Effect Scale

状态：`frozen_pre_run / candidate / non-authoritative / stage_b_effect_scale_only`。

本文档用于把当前候选包的 validation metrics 与 acceptance criteria 在 benchmark 运行前冻结下来，优先服务于：

- `AIM-120C-class blast_fragmentation -> F-16C_Block50`
- `beam / high / near_miss_0_35m`
- `effect_scale_authority` 的候选放行评审

本文档不是 validation result，不创建 runtime descriptor，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_target` | `a2.vulnerability_surrogate_validation.v1` |
| `criteria_status` | `frozen_pre_run_stage_b_effect_scale_only` |
| `primary_release_scope` | `effect_scale_authority_only` |
| `component_probability_release_status` | `deferred_to_stage_c` |
| `validation_metrics_ref` | `self` |
| `validation_acceptance_criteria_ref` | `self` |
| `review_status` | `author_frozen_pending_independent_review` |
| `runtime_descriptor_action` | `forbidden_until_review_record_and_benchmark_results_exist` |

## 2. 冻结原则

1. 本文所有门槛在 benchmark 结果生成前冻结，不得根据结果回填或放宽。
2. 本文只冻结 Stage B `effect_scale` 评审所需的最小门槛，不把 Stage C `component_failure_probability` 混进同一轮 release。
3. 即使所有 hard gate 后续都通过，只要：
   - source / provenance / residual closeout 不完整，
   - review record 不存在，
   - stock descriptor 未单独审议，
   仍不得宣称 stock authority 已放行。
4. `pk_authority` 与 `deterministic_fuze_authority` 不在本文验收范围内。
5. scope 轴与 independence 边界以
   [validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md)
   为准；若 metrics hard gate 通过但 scope / independence 审计未通过，仍不得进入 authority review。

## 3. Stage B Hard Gates

下表定义 Stage B `effect_scale_authority` 候选评审所需的 hard gates。所有 hard gate 都必须满足，才允许把结果带入下一轮 authority review。

| `criteria_id` | benchmark | metric / field | 冻结门槛 | 失败含义 |
|---|---|---|---|---|
| `BFM-CRIT-ES-001` | `BFM-BM-001` | `metrics.unit_roundtrip_pass` | `true` | 爆轰缩比与单位链不稳定，Stage B 停止。 |
| `BFM-CRIT-ES-002` | `BFM-BM-001` | `metrics.monotonic_overpressure_pass` | `true` | blast surrogate 曲线形状不可信，Stage B 停止。 |
| `BFM-CRIT-ES-003` | `BFM-BM-001` | `metrics.monotonic_impulse_pass` | `true` | impulse surrogate 曲线形状不可信，Stage B 停止。 |
| `BFM-CRIT-ES-004` | `BFM-BM-003` | `metrics.fixed_seed_replay_pass` | `true` | 采样不可复现，Stage B 停止。 |
| `BFM-CRIT-ES-005` | `BFM-BM-003` | `metrics.isotropy_pass` | `true` | uniform toy sampler 本身不稳定，Stage B 停止。 |
| `BFM-CRIT-ES-006` | `BFM-BM-003` | `metrics.sampling_convergence_pass` | `true` | sample-count 对 areal-density 结果过敏，Stage B 停止。 |
| `BFM-CRIT-ES-007` | `BFM-BM-003` | `sampling_convergence_summary.relative_delta` | `<= 0.05` | 收敛误差超出当前候选包可接受范围。 |
| `BFM-CRIT-ES-008` | `BFM-BM-005` | `metrics.source_trace_completeness_pass` | `true` | integrated benchmark 不能回溯输入，Stage B 停止。 |
| `BFM-CRIT-ES-009` | `BFM-BM-005` | `metrics.unit_consistency_pass` | `true` | mechanism-load vector 单位不一致，Stage B 停止。 |
| `BFM-CRIT-ES-010` | `BFM-BM-005` | `metrics.forbidden_authority_fields_absent` | `true` | benchmark 非法混入 authority 字段，Stage B 停止。 |
| `BFM-CRIT-ES-011` | `BFM-BM-005` | `metrics.uncertainty_summary_present` | `true` | 没有 uncertainty 摘要，Stage B 停止。 |
| `BFM-CRIT-ES-012` | `BFM-BM-005` | `metrics.seed_window_cv_pass` | `true` | 多 seed 波动超出当前候选包容忍度，Stage B 停止。 |
| `BFM-CRIT-ES-013` | `BFM-BM-005` | `uncertainty_summary.fragment_areal_density_per_m2.cv` | `<= 0.05` | fragment areal-density proxy 波动过大。 |
| `BFM-CRIT-ES-014` | `BFM-BM-005` | `uncertainty_summary.blast_impulse_kpa_ms_proxy.cv` | `<= 0.05` | blast impulse proxy 波动过大。 |
| `BFM-CRIT-ES-015` | `BFM-BM-005` | `uncertainty_summary.fragment_energy_j_proxy.cv` | `<= 0.05` | fragment energy proxy 波动过大。 |
| `BFM-CRIT-ES-016` | `BFM-BM-005` | `uncertainty_summary.penetration_margin_proxy.cv` | `<= 0.05` | penetration proxy 波动过大。 |
| `BFM-CRIT-ES-017` | `BFM-BM-006` | `metrics.source_trace_error_count` | `= 0` | source trace / rights / authority gate 未通过，Stage B 停止。 |
| `BFM-CRIT-ES-018` | `BFM-BM-006` | `metrics.source_trace_warning_count` | `= 0` | 候选包仍含未解释 warning，Stage B 停止。 |

## 4. Stage B Release Notes

即使第 3 节全部满足，当前 Stage B 也只允许导出如下结论：

- 当前候选 package 已经具备 `effect_scale` row-backed authority review 所需的最小 validation hygiene；
- 可以把结果提交到下一轮 narrow-scope authority 审阅；
- 仍不能把结果自动写入 stock runtime descriptor；
- 仍不能上卷成 `component_failure_probability_authority`、`Pk` 或 deterministic fuze authority。

## 5. Stage C Deferred Gates

下列内容明确不属于本轮 Stage B hard gate，而是留给 Stage C `component_failure_probability_authority`：

| `deferred_id` | 领域 | 当前状态 | 为什么 deferred |
|---|---|---|---|
| `BFM-DEF-001` | `BFM-BM-002` fragment mass / velocity / energy toy benchmark | `tracked_not_release_gating` | 当前主要支撑 fragment method sanity，而不是 Stage B 的最小 effect-scale release。 |
| `BFM-DEF-002` | `BFM-BM-004` penetration-margin domain benchmark | `tracked_not_release_gating` | 当前主要支撑 penetration gate hygiene，而不是 Stage B 最小 release。 |
| `BFM-DEF-003` | component-specific probability calibration | `open` | `RES-009` 仍 open，不能与 Stage B 混验收。 |
| `BFM-DEF-004` | component row completeness | `open` | 当前 broad near-miss projected component rows 仅证明技术通路存在。 |

## 6. 仍然保留的边界

本文冻结之后，以下边界依然成立：

- `RES-010` 不会因为文档冻结就自动关闭；还需要 benchmark result table 与独立 review record。
- `RES-013` 和 `RES-014` 不在本包内关闭。
- 当前 package 仍保持 `candidate / non-authoritative / not_run`。

## 7. 来源依据

本 artifact 的冻结依据来自：

- [梯度真实性原则](../../../../../standards/gradient_realism_principles.zh.md)
- [A2 数据来源准入规则](../../data_collection/source_admission_rules_20260528.zh.md)
- [A2 窄域 Authority 闭环任务定义](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md)
- [Blast-Fragmentation VPS Validation Manifest 草案](validation_manifest_draft_blastfrag_20260528.zh.md)
- [Validation Report Draft](validation_report_draft.zh.md)
- [Benchmark Candidate Matrix：VPS blast_fragmentation methods](../../data_collection/vps_blast_fragmentation_methods/benchmark_candidate_matrix.zh.md)

## 8. 当前判定

当前判定为：

> `validation metrics and acceptance criteria are frozen for Stage B effect-scale-only review, but benchmark results, independent review, residual closeout and stock authority remain pending`.
