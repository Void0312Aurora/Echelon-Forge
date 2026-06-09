# A2 G3 Residual Closeout Status - 2026-06-01

状态：`2026-06-01 / G3 residual accounting closeout / research_closed_authority_retained / non_authoritative`。

本文只收口 `G3 residual` 在当前 research / candidate profile 下的台账层：确认
`RES-001..014` 均有明确状态、稳定证据入口和不得上卷的边界，且不再阻塞当前研究级候选模型。
它不关闭 authority residual，不创建 runtime descriptor，不授予 `effect_scale_authority`、
`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

事实源优先级仍是 retained gate JSON / manifest，其次是
[residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)。
本文是清点和分发入口，不覆盖 retained gate 的机器结论。

当前项目默认目标已改为 research / candidate profile，见
[research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md)。
因此本表中的旧 open / fail-closed residual 已重标为 research-closed 或
research-out-of-scope；它们只阻塞 future `G4/G5` authority，或提示哪些 research data
surface 仍应以可替换估计继续完善。

## G3 closeout verdict

`G3` 可以按 `research_closed_authority_retained` 收尾，含义仅限：

- `RES-001..014` 均已有当前状态；
- 每个 residual 都有 retained artifact、活跃状态文档或 backlog 入口；
- authority_blocked / authority_fail_closed / authority_boundary_deferred 项都保留为 future
  authority 阻塞或边界，不被本轮 research closeout 覆盖；
- authority guards 继续全 false，stock descriptor 不创建。

不能写成：

- `all authority residuals closed`；
- `G4 authority promoted`；
- `effect_scale_authority` 或 `component_failure_probability_authority` 已 release；
- Pk calibration claim 或 deterministic fuze authority claim。

## Residual inventory

| residual | G3 closeout class | 当前 residual register 状态 | 主要证据入口 | 后续入口 |
|---|---|---|---|---|
| `RES-001` | narrow closed / non-authoritative | `closed_narrow_internal_signoff_non_authoritative` | `retained_artifacts/res001_release_signoff_20260531/res001_release_signoff_gate.json` | 若进入 G4，重新审阅外部发布权和 benchmark consumption 权限 |
| `RES-002` | scoped closed / non-authoritative | `closed_scoped_identity_non_authoritative` | `retained_artifacts/res002_scoped_release_identity_20260531/res002_scoped_release_identity_gate.json` | 若进入 G4，重新审阅 global clean release identity |
| `RES-003` | research closed / global truth authority blocked | `research_closed_stage_b_witness_geometry_bookkeeping_authority_blocked_global_geometry` | `retained_artifacts/res003_target_geometry_closeout_20260531/res003_target_geometry_closeout_gate.json` | G4 前补真实 F-16 geometry、material、occlusion、exposed-area 来源 |
| `RES-004` | research closed / specific truth authority blocked | `research_closed_stage_b_family_scope_authority_blocked_specific_warhead_truth` | `retained_artifacts/res004_warhead_scope_closeout_20260531/res004_warhead_scope_closeout_gate.json` | G4 前补具体 AIM-120C warhead / fragment / fuze truth 边界 |
| `RES-005` | research closed / authority fail-closed | `research_closed_mechanism_load_envelope_authority_fail_closed_tp21_selected_debris_outputs_missing` | `retained_artifacts/res005_tp21_debris_admission_20260531/res005_tp21_debris_admission_gate.json`；`retained_artifacts/res005_tp21_selected_case_admission_20260601/res005_tp21_selected_case_admission_review_gate.json` | research 用可替换 mechanism-load envelope；G4 前等外部 reviewer/signoff packet 后重跑 selected-case admission gate |
| `RES-006` | research closed / authority fail-closed | `research_closed_mechanism_load_envelope_authority_fail_closed_beco_recalculation_not_admitted` | `retained_artifacts/res006_beco_recalculation_admission_20260531/res006_beco_recalculation_admission_gate.json`；`retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/res006_beco_replacement_tolerance_admission_gate.json` | research 用可替换 blast envelope；G4 前等 lineage / allowed-output / tolerance 或 replacement signoff 后重跑 admission gate |
| `RES-007` | Stage B review closed / release blocked | `closed_stage_b_scope_review_only_release_blocked` | `retained_artifacts/scope_bucket_independent_review_20260531/scope_bucket_independent_review_gate.json` | G4 前重新声明 bucket 对 release scope 的适用性 |
| `RES-008` | Stage B review closed / release blocked | `closed_stage_b_scope_review_only_release_blocked` | `retained_artifacts/scope_bucket_independent_review_20260531/scope_bucket_independent_review_gate.json` | G4 前重新声明 beam/high closure physics 边界 |
| `RES-009` | research closed / Stage C truth authority blocker | `research_closed_stage_c_candidate_surface_authority_blocked_fragility_truth` | `retained_artifacts/stage_c_fragility_review_20260531/stage_c_fragility_review_gate.json`；`retained_artifacts/stage_c_fragility_benchmark_20260531/stage_c_fragility_benchmark.json` | research 保留 candidate surface；另起 `TC-A2-AUTH-C` 前补 independent fragility truth |
| `RES-010` | research closed / Stage C release authority blocked | `research_closed_stage_b_review_authority_blocked_stage_c_release` | `retained_artifacts/stage_b_independent_review_20260531/stage_b_independent_review_gate.json` | G4/G4-C 前补 formal result promotion 与 release-grade closeout |
| `RES-011` | research closed / Stage C uncertainty authority blocked | `research_closed_stage_b_uncertainty_authority_blocked_stage_c_probability` | `retained_artifacts/uncertainty_review_20260531/uncertainty_review_gate.json`；`retained_artifacts/res011012_independent_review_closeout_20260531/res011012_independent_review_closeout_gate.json` | Stage C probability uncertainty coverage 与 reviewer-accepted bounds |
| `RES-012` | research closed / Stage C independence authority blocked | `research_closed_stage_b_independence_authority_blocked_stage_c_probability` | `retained_artifacts/res011012_independent_review_closeout_20260531/res011012_independent_review_closeout_gate.json`；`retained_artifacts/stage_b_independent_review_20260531/stage_b_independent_review_gate.json` | Stage C result-level independence 和 independent fragility truth |
| `RES-013` | research out-of-scope / authority boundary deferred | `research_out_of_scope_authority_boundary_deferred_pk` | [authority_promotion_backlog.zh.md](authority_promotion_backlog.zh.md) | 另起 `TC-A2-KILLCHAIN` Pk 证据链 |
| `RES-014` | research out-of-scope / authority boundary deferred | `research_out_of_scope_authority_boundary_deferred_deterministic_fuze` | [authority_promotion_backlog.zh.md](authority_promotion_backlog.zh.md) | 另起 deterministic fuze / kill-chain 证据链 |

## Current blocker buckets

| bucket | residuals | 当前处理 |
|---|---|---|
| narrow/scoped already closed | `RES-001/002` | 保持 non-authoritative；G4 前重新审阅更高权限 |
| Stage B local review complete | `RES-003/004/007/008/010/011/012` | 不再作为 research candidate 的台账缺口；仍阻塞 release-grade authority 或 Stage C |
| mechanism research envelope / authority fail-closed | `RES-005/006` | research profile 可用可替换 envelope；不消费 TP-21 / BEC-O 输出为 release evidence；G4 等外部 reviewer/signoff packet |
| Stage C research surface / authority truth missing | `RES-009` | research profile 可保留 candidate surface；authority 只能进入 `TC-A2-AUTH-C` |
| kill-chain boundary deferred | `RES-013/014` | research profile out-of-scope；不在本候选包关闭 |

在 research profile 下，`RES-005/006` 的 practical next step 是构造 non-authoritative
mechanism-load envelope，而不是等待工业级准入；`RES-009..012` 的 practical next step 是构造
research component fragility surface 和 uncertainty ledger。

## Acceptance evidence

本轮 G3 台账闭合依赖以下当前工作区复核：

```bash
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py
python -m pytest -q tests/architecture/test_a2_retained_manifest_integrity.py tests/architecture/test_a2_candidate_vps_bundle.py tests/architecture/test_a2_source_admission_audit.py tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py
python -m pytest -q tests/architecture/test_a2_blastfrag_signoff_admission_preflight.py tests/architecture/test_a2_blastfrag_res006_beco_recalculation_admission_gate.py tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_candidate_packet.py tests/architecture/damage_model/test_external_signoff_intake_contracts.py tests/architecture/test_a2_blastfrag_source_rights_signoff_request_packet.py tests/architecture/test_a2_blastfrag_res006_beco_lineage_tolerance_review_packet.py tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_admission_gate.py tests/architecture/test_a2_blastfrag_res006_beco_replacement_tolerance_admission_gate.py
```

验收输出只支持 G3 台账清点，不支持 authority promotion。

当前工作区结果：

- retained manifest integrity：`manifest_count=29`、`missing_total=0`、`sha_mismatch_total=0`、`guard_true_total=0`；
- source admission strict：`9 ledgers, 29 candidate docs, 53 calibration docs`；
- candidate bundle CLI：exit 0，authority boundary 仍为 stock/effect/component/Pk/fuze 全 false；
- A2 candidate/source/manifest/descriptor suite：`17 passed`；
- G2/G3 fail-closed signoff / residual packet focused suite：`44 passed`。

## Closure rule

后续只有两类动作能改变 G3 状态：

1. 新 retained gate 明确给出 `closed_residual_ids_by_this_gate` 或 scoped closeout，且 authority guard 全 false；
2. 明确启动 `G4/G5` 任务，并在该任务中重新声明 residual 依赖。

在此之前，同 scope 下不再追加临时 G3 清点 wave。
