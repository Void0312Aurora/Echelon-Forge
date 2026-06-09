# A2 G4 Research Integration Acceptance - 2026-06-01

状态：`2026-06-01 / G4 research integration accepted / non_authoritative / replaceable_data`。

本文记录 `G4-R-INTEGRATION` 的串行整合结论。它只验收 research / candidate profile
下的 G4 研究分发，不启动工业级 / release-grade 准入，不创建 runtime descriptor，不把
任何 fragment / blast、component probability、Pk 或 deterministic fuze guard 置真。

## Scope

本次整合覆盖：

- `G4-R-B` mechanism-load envelope：source scan、derived envelope draft、validation audit；
- `G4-R-C` component fragility surface：source scan、surface draft、uncertainty /
  independence audit；
- 中央入口、任务簇状态和 README 的 research-only 边界同步。

不覆盖：

- 工业级 / release-grade source admission；
- stock database row、runtime descriptor 或 calibrated component probability；
- `G5-R` Pk / fuze proxy 分发；
- 受控报告、工具输出、教材表格或 raw selected values 的复制或消费。

## Accepted Packets

| Slice | Packet | Integration result |
|---|---|---|
| `G4-R-B-001` | [mechanism-load source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md) | `pass`，source rows 有 tier、rights、scope、uncertainty/confidence 和 replacement rule |
| `G4-R-B-002` | [mechanism-load envelope draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md) | `pass`，只输出 research mechanism-load vector / placeholder，不写真实战斗部或目标参数 |
| `G4-R-B-003` | [mechanism-load validation audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md) | `pass`，确认 no stock/runtime write、no truth overclaim |
| `G4-R-C-SCAN` | [component fragility source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md) | `pass`，source proposal 可支撑 research surface，不支撑 F-16C 全机真值 |
| `G4-R-C-SURFACE` | [component fragility surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md) | `pass`，只定义 row shape、curve family、uncertainty 和 replacement path |
| `G4-R-C-AUDIT` | [uncertainty / independence audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | `pass`，确认 Stage C test-local、synthetic baseline、derived surface 和 independent truth 分离 |

## Validation

当前工作区复验：

```bash
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py --output /tmp/a2_candidate_vps_bundle_g4_research_continue.json
python -m pytest -q tests/architecture/test_a2_candidate_vps_bundle.py tests/architecture/test_a2_source_admission_audit.py tests/architecture/test_a2_retained_manifest_integrity.py
python -m pytest -q tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_admission_gate.py tests/architecture/test_a2_blastfrag_res005_tp21_selected_case_candidate_packet.py tests/architecture/test_a2_blastfrag_source_rights_signoff_request_packet.py tests/architecture/damage_model/test_external_signoff_intake_contracts.py tests/architecture/test_a2_blastfrag_signoff_admission_preflight.py
rg -n 'authorit[y]=true|component_failure_probability_authorit[y].*true|stock_descriptor_create[d].*true|calibration_statu[s].*calibrated|authority_admissio[n].*true|industrial_admissio[n].*true|replacement_allowe[d].*false' docs/task/air_combat/archive/a2_high_fidelity_damage_model/g4_research_dispatch_20260601.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/g4_research_component_fragility_dispatch_20260601.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/g4_research_integration_acceptance_20260601.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/g4_g5_research_continuation_20260601.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/README.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/task_cluster_dispatch_20260601.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/task_cluster_execution_status_20260601.zh.md
git diff --check
```

结果：

- retained manifest integrity：`manifest_count=29`, `missing_total=0`,
  `sha_mismatch_total=0`, `guard_true_total=0`；
- source admission strict：`9 ledgers, 29 candidate docs, 53 calibration docs`；
- candidate bundle：`status=candidate_non_authoritative_bundle`,
  `research_blocker_residual_ids=[]`, `research_profile_closed=true`；
- candidate/source/manifest tests：`15 passed`；
- retained packet focused tests：`34 passed`；
- G4 guard grep：no matches；
- `git diff --check`：exit 0。

## Integration Decision

`G4 research` 可以标记为 `dispatch_closed_non_authoritative`：

- `G4-R-B` 已成为 downstream research mechanism side input；
- `G4-R-C` 已成为 integration-ready research fragility surface；
- `RES-005/006` 和 `RES-009..012` 在当前 research profile 下不再阻塞继续建模；
- `RES-013/014` 不属于本次 G4 闭合；其 research proxy 已由后续
  [G5 research integration acceptance](g5_research_integration_acceptance_20260602.zh.md) 收口，
  authority 部分仍保持 deferred；
- machine guards 保持 false，工业级准入只作为可选未来边界。

本结论不得写成 full A2 kill-chain complete、industrial admission complete、Pk calibrated
或 deterministic fuze released。
