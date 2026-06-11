# A2 Research Closeout - 2026-06-02

状态：`2026-06-02 / archived / research_profile_closed / sealed_retained_record / non-authoritative`。

本文记录 A2 高保真空战毁伤模型子项目在 research / candidate profile 下的最终归档结论。
它不创建 runtime descriptor，不授予 stock、Pk、deterministic fuze 或 release-grade authority。

## Closeout Decision

A2 子项目可以视为当前 research / candidate 目标下已完成并归档：

| 层级 | 结论 | 保留入口 | 边界 |
|---|---|---|---|
| `G1 runtime` | structured aircraft damage/effects runtime 主链进入维护路径 | [runtime_status.zh.md](../../runtime_status.zh.md) | 不是 calibrated authority |
| `G2 candidate acceptance` | blast-fragmentation 窄域候选包 accepted non-authoritative | [candidate_acceptance_status.zh.md](../../candidate_acceptance_status.zh.md) | 不创建 stock descriptor |
| `G3 residual research closeout` | `RES-001..014` 对当前 research profile 不再阻塞 | [g3_residual_closeout_status_20260601.zh.md](../../g3_residual_closeout_status_20260601.zh.md) | authority residual 只作为未来 opt-in 边界 |
| `G4 research` | mechanism-load envelope 与 component fragility surface 已完成 research integration | [g4_research_integration_acceptance_20260601.zh.md](../../g4_research_integration_acceptance_20260601.zh.md) | 不等于 industrial admission |
| `G5 research` | Pk / fuze proxy source scan、boundary、event-chain 和 audit 已完成 | [g5_research_integration_acceptance_20260602.zh.md](../../g5_research_integration_acceptance_20260602.zh.md) | 不等于 Pk calibration 或 deterministic fuze authority |

## Accepted Evidence

| Evidence surface | Status |
|---|---|
| [research candidate data policy](../../research_candidate_data_policy_20260601.zh.md) | 默认目标固定为 research / candidate；底层数据可替换、可扩展、可追溯 |
| [task granularity ledger](../../task_granularity_and_coordination_20260601.zh.md) | `G1..G5` 粒度、禁止上卷语义和 authority opt-in 边界已固定 |
| [task cluster execution status](../../task_cluster_execution_status_20260601.zh.md) | G2/G3/G4/G5 research 执行状态已记录 |
| [G4/G5 research continuation](../../g4_g5_research_continuation_20260601.zh.md) | G4/G5 research-only 延续已收口 |
| [G5 research dispatch](../../g5_research_dispatch_20260602.zh.md) | `G5-R-A/B/C/D/INTEGRATION` 均为 `pass` |

## Validation Snapshot

归档前最后一次复核结果：

```bash
python tools/maintenance/damage_model_retained_artifacts.py manifest-integrity
python tools/maintenance/damage_model_source_governance.py admission-audit --strict
python tools/maintenance/damage_model_candidate_artifacts.py package-bundle --output /tmp/a2_candidate_vps_bundle_archive_closeout.json
rg -n "pk_authorit[y].*true|deterministic_fuze_authorit[y].*true|stock_descriptor_create[d].*true|replacement_allowe[d].*false" docs/task/air_combat/archive/a2_high_fidelity_damage_model/g5_research_*.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/data_collection/kill_chain_proxy_methods
python -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_source_admission_audit.py tests/architecture/damage_model/test_retained_manifest_integrity.py
python -m pytest -q tests/architecture/damage_model/test_benchmark_evidence_admission.py tests/architecture/damage_model/test_source_evidence_governance.py tests/architecture/damage_model/test_external_signoff_intake_contracts.py tests/architecture/damage_model/test_external_signoff_admission_preflight.py
git diff --check
```

Observed result:

- retained manifest integrity: `manifest_count=29`, `sha_mismatch_total=0`, `guard_true_total=0`;
- source admission strict: `9 ledgers, 29 candidate docs, 53 calibration docs`;
- candidate bundle: `status=candidate_non_authoritative_bundle`,
  `research_profile_closed=true`, `research_blocker_residual_ids=[]`;
- authority guards: `pk_authority=false`, `deterministic_fuze_authority=false`,
  `stock_descriptor_created=false`;
- focused G5 guard grep: no matches;
- candidate/source/manifest tests: `15 passed`;
- retained packet focused tests: `34 passed`;
- `git diff --check`: exit 0.

## Archive Boundary

归档后默认规则：

- 不再分发新的 A2 research task cluster；
- 不移动 `calibration/`、`data_collection/` 或 `retained_artifacts/`，避免破坏维护工具和
  manifest 路径；
- 不把 archived research packet 解读成 industrial / release-grade authority；
- 不把 `DamageReport`、training reward、runtime smoke 或 proxy score 写成 Pk truth；
- 不把 fuze branch label 写成 deterministic fuze trigger truth。

未来只有两类合法恢复方式：

| 恢复类型 | 启动条件 | 初始入口 |
|---|---|---|
| authority promotion | 用户明确要求 stock / release-grade / Pk / deterministic fuze authority | [../../authority_promotion_backlog.zh.md](../../authority_promotion_backlog.zh.md) |
| new research expansion | 用户明确要求新武器、目标、机制或非权威 proxy 扩展 | 先更新 [../../README.zh.md](../../README.zh.md) 并新建独立 follow-on 任务记录 |

除此之外，本子项目应作为 sealed retained record 保留。
