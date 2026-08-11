# Validation Report Draft

状态：`candidate / non-authoritative / not_run`。  
本文档把本候选包当前已经明确的 benchmark 计划、manifest 字段、指标占位和审阅边界固化下来，但当前仍没有验证运行结论。只要结果未复核、残差未关闭，就不能声称已校准，不能授予 `Pk` 或 deterministic-fuze authority。

候选 scope 固定为：`F-16C_Block50` × `AIM-120C-class/blast_fragmentation` × `beam` × `high` × `near_miss_0_35m`。

## 验证 Manifest 草案

| 字段 | 值 |
|---|---|
| `schema_version` | `a2.vulnerability_surrogate_validation.v1` |
| `validation_status` | `not_run` |
| `validation_artifact_sha256` | `missing` |
| `validated_surrogate_model_ref` | [surrogate_model_card.zh.md](surrogate_model_card.zh.md) |
| `validation_benchmark_ref` | [validation_manifest_draft_blastfrag_20260528.zh.md](validation_manifest_draft_blastfrag_20260528.zh.md) |
| `validation_metrics_ref` | [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md) |
| `validation_acceptance_criteria_ref` | [validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md) |
| `validation_stage_c_metrics_ref` | [validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md) |
| `validation_scope_ref` | [validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md) |
| `validation_scope_probe_report_ref` | [validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md) |
| `validation_benchmark_snapshot_ref` | [validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md](validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md) |
| `validation_stage_c_snapshot_ref` | [validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md](validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md) |
| `validation_stage_c_result_pack_ref` | [validation_result_pack_stage_c_component_probability_20260530.zh.md](validation_result_pack_stage_c_component_probability_20260530.zh.md) |
| `validation_stage_c_retained_pack_ref` | [validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md](validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md) |
| `validation_stage_c_review_gate_ref` | [validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md](validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md) |
| `validation_provenance_identity_gate_ref` | [validation_provenance_and_identity_gate_20260530.zh.md](validation_provenance_and_identity_gate_20260530.zh.md) |
| `validation_result_pack_ref` | [validation_result_pack_stage_b_effect_scale_20260530.zh.md](validation_result_pack_stage_b_effect_scale_20260530.zh.md) |
| `validation_review_readiness_ref` | [validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md](validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md) |
| `validation_scope.target_type` | `F-16C_Block50` |
| `validation_scope.weapon_family` | `blast_fragmentation` |
| `validation_scope.weapon_class` | `AIM-120C-class` |
| `validation_scope.aspect_bucket` | `beam` |
| `validation_scope.closure_bucket` | `high` |
| `validation_scope.miss_distance_bucket` | `near_miss_0_35m` |

`validation_status=not_run` 是刻意保留的候选状态，不满足 runtime gate。只有未来完整报告将状态改为 `validated` 或 `passed`，且所有引用、artifact hash、review 记录和 residual closeout 都可追溯时，才允许进入下一轮 authority 评审。

## Benchmark 计划

| `benchmark_id` | benchmark 来源 | 覆盖内容 | 独立于模型输入 | 当前状态 | residual |
|---|---|---|---|---|---|
| `BFM-BM-001` | [validation_manifest_draft_blastfrag_20260528.zh.md](validation_manifest_draft_blastfrag_20260528.zh.md) + `SRC-PKG-003` | blast scaled distance / overpressure / impulse unit-domain lock | `yes, if future blast comparison artifact is independently pinned` | `candidate_not_run` | `RES-006`, `RES-010`, `RES-012` |
| `BFM-BM-002` | 同上 + `SRC-PKG-002` / `SRC-PKG-003` | Mott/Gurney fragment mass-energy toy benchmark | `partial` | `candidate_not_run` | `RES-005`, `RES-010`, `RES-011`, `RES-012` |
| `BFM-BM-003` | 同上 + `SRC-PKG-003` | fragment areal-density spatial sampling reproducibility | `yes for sampler design, not yet for physical warhead truth` | `candidate_not_run` | `RES-005`, `RES-007`, `RES-011` |
| `BFM-BM-004` | 同上 + `SRC-PKG-003` | penetration-margin formula shape / domain rejection | `partial` | `candidate_not_run` | `RES-005`, `RES-010`, `RES-012` |
| `BFM-BM-005` | 同上 + `SRC-PKG-005` | integrated near-miss mechanism-load vector toy benchmark | `partial` | `candidate_not_run` | `RES-005`, `RES-006`, `RES-007`, `RES-008`, `RES-011`, `RES-012` |
| `BFM-BM-006` | 同上 + `SRC-PKG-006` | source trace / rights / authority manifest check | `yes` | `implemented_but_non_authoritative` | `RES-001`, `RES-010`, `RES-012` |

benchmark 必须与 surrogate 训练、拟合或参数选择来源分离。当前 `BFM-BM-006` 已有脚手架，但它只证明 source/rights/authority 行政准入，不证明 physics surrogate 已通过验证。
当前 scope / independence 的 pre-run 边界已冻结到
[validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md](validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md)，
当前 boundary probe 的第一版结果表已记录到
[validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md](validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md)，
当前固定种子 benchmark snapshot 已记录到
[validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md](validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md)，
当前统一 candidate result pack 已记录到
[validation_result_pack_stage_b_effect_scale_20260530.zh.md](validation_result_pack_stage_b_effect_scale_20260530.zh.md)，
当前 Stage C component-specific probability 的 pre-run candidate metrics 已冻结到
[validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md)，
当前 Stage C snapshot 已记录到
[validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md](validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md)，
当前 Stage C unified candidate result pack 已记录到
[validation_result_pack_stage_c_component_probability_20260530.zh.md](validation_result_pack_stage_c_component_probability_20260530.zh.md)，
当前 Stage C retained artifact pack 已记录到
[validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md](validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md)，
当前 Stage C blocked review gate 已记录到
[validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md](validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md)，
当前 shared provenance / surrogate identity gate 已记录到
[validation_provenance_and_identity_gate_20260530.zh.md](validation_provenance_and_identity_gate_20260530.zh.md)，
但独立 review 与结果级 closeout 仍未执行。

## 指标与验收门槛

| `metric_id` | 指标 | 适用输出 | 统计口径 | 验收门槛 | 当前结果 | authority 影响 |
|---|---|---|---|---|---|---|
| `MET-001` | Stage B effect-scale hard-gate metrics | `BFM-BM-001/003/005/006` | 见冻结 artifact | `frozen_pre_run` | `not_run` | 不授权 |
| `MET-002` | component probability residual | `component_failure_probability` | `Stage C candidate metrics frozen; Brier/log-loss/calibration-curve route still reserved for later closeout` | `candidate_snapshot_only / not_run` | `not_run` | 不授权 |
| `MET-003` | mechanism-load interval coverage | `min_*` / `max_*` row 门槛 | `coverage + violation-rate route reserved` | `partially_frozen_for_stage_b_only` | `not_run` | 不授权 |
| `MET-004` | uncertainty summary | `BFM-BM-005` multi-seed CV summary | `frozen_for_stage_b_only` | `not_run` | 不授权 |
| `MET-005` | scope leakage check | scope axes | `manual + automated` | `frozen_for_stage_b_only` | `not_run` | 不授权 |

验收门槛不得由同一候选结果事后反推。当前 Stage B `effect_scale` 所需 metrics / thresholds 已冻结到
[validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md](validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md)；
但 benchmark 仍未运行；Stage C `component_failure_probability` 虽已进入 pre-run candidate freeze 状态，仍未完成 fragility / uncertainty / independent review closeout。

## 测试矩阵

| `case_id` | target | weapon family | aspect | closure | miss-distance bucket | 机制载荷 | 预期检查 | 当前状态 |
|---|---|---|---|---|---|---|---|---|
| `VAL-001` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `blast scaled distance + fragment areal density + surface incidence` | future effect-scale residual | `not_run` |
| `VAL-002` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `projected component load rows` | Stage C component-specific candidate probability residual | `candidate_snapshot_only` |
| `VAL-003` | `F-16C_Block50` | `blast_fragmentation` | `beam` | `high` | `near_miss_0_35m` | `bucket sensitivity and uncertainty` | future coverage / leakage check | `not_run` |

## 结果摘要

当前结果：已有脚手架、scope probe、fixed-seed candidate benchmark snapshot、统一 candidate result pack 与 test-local authority 演练，
但仍没有可宣称为验证通过的独立 benchmark 结果。

| 输出 | 结论 | 证据引用 | 是否可授权 |
|---|---|---|---|
| `effect_scale` | `candidate_snapshot_exists + test_local_exercise_only / not_validated` | [validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md](validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md) | 否 |
| `result_pack` | `candidate_result_pack_exists / not_validated` | [validation_result_pack_stage_b_effect_scale_20260530.zh.md](validation_result_pack_stage_b_effect_scale_20260530.zh.md) | 否 |
| `component_failure_probability` | `candidate_metrics_and_result_pack_exist / not_validated` | [validation_result_pack_stage_c_component_probability_20260530.zh.md](validation_result_pack_stage_c_component_probability_20260530.zh.md) | 否 |
| `pk_authority` | `not_in_scope` | [narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) | 否 |
| `deterministic_fuze_authority` | `deferred / out_of_scope` | [narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md](../../narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) | 否 |

## 审阅与发布记录

| `review_id` | 审阅人 / 角色 | 日期 | 结论 | 必须整改项 |
|---|---|---|---|---|
| `REV-001` | `candidate-package assembly` | `2026-05-30` | `candidate_only` | `RES-001..012` 适用项保持 open；`RES-013/014` 继续保留为边界 |
| `REV-002` | `stage_b_metrics_freeze` | `2026-05-30` | `criteria_frozen_pre_run` | 独立 reviewer signoff、benchmark result table 和 residual closeout 仍缺 |
| `REV-003` | `stage_b_author_review_readiness` | `2026-05-30` | `candidate_snapshot_and_review_inputs_present` | 当前只形成 author-side review readiness；独立 review 和 stock authority 仍禁止 |
| `REV-004` | `stage_b_author_result_pack` | `2026-05-30` | `candidate_result_pack_present` | 当前 result pack 仍是 author-side / non-authoritative，不替代独立 review |
| `REV-005` | `stage_c_retained_pack` | `2026-05-30` | `candidate_retained_chain_present` | 当前 retained pack 只保存 Stage C author-side candidate surfaces，不替代独立 fragility release artifact |
| `REV-006` | `stage_c_component_review_gate` | `2026-05-30` | `candidate_component_review_ready_but_blocked` | fragility / uncertainty / geometry / mechanism / independence residual 仍缺；Stage B 仍为单独 blocked upstream track |
| `REV-007` | `shared_provenance_identity_gate` | `2026-05-30` | `shared_author_side_pin_and_identity_surface_present` | provenance / identity 已形成共享 gate，但 `RES-001/002` 仍未闭合 |

## `RES-001..004` Closeout Matrix

| `residual_id` | `evidence_ref` | `current_status` | `blocked_by` | `review_required` | `authority_effect` |
|---|---|---|---|---|---|
| `RES-001` | [artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md](artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md) | `progressed_candidate_pin_surface_written` | external artifact hash / rights / retention chain 仍未完整冻结 | `yes` | 无法证明 Stage B 输入和 benchmark 引用可追溯 |
| `RES-002` | [surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md](surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md) | `progressed_candidate_identity_written` | worktree 仍 dirty，retained validation artifact chain 仍未闭合 | `yes` | 无法把当前 snapshot 升级为可复审的 release-grade surrogate 身份 |
| `RES-003` | [target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md](target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md) | `progressed_candidate_assumptions_written` | target geometry truth 与 unsupported claims 仍未独立审阅 | `yes` | 不得把 beam witness geometry 写成真实 F-16 vulnerability geometry |
| `RES-004` | [warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md](warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md) | `progressed_candidate_scope_written` | family-level / toy proxy / third-party sanity 边界仍未独立审阅 | `yes` | 不得把 repo warhead proxy 或 third-party mass cluster 写成 AIM-120C authority |

## 当前判定

本草案当前判定为：`candidate / non-authoritative / not_run`。不得据此创建 authoritative descriptor，不得把 calibration 状态标为完成，不得放行 `Pk` 或 deterministic fuze。
