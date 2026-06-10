# A2 G5 Research Integration Acceptance - 2026-06-02

状态：`2026-06-02 / G5 research integration accepted / non_authoritative / replaceable_data`。

本文记录 `G5-R-INTEGRATION` 的串行整合结论。它只验收 research / candidate profile
下的 Pk / fuze proxy packet，不启动工业级 / release-grade 准入，不创建 runtime
descriptor，不改变 stock、Pk 或 fuze guards。

## Accepted Packets

| Slice | Packet | Integration result |
|---|---|---|
| `G5-R-A` | [G5 source scan](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md) | `pass`，列出 method/source inputs、rejected sources、uncertainty 和 replacement rule |
| `G5-R-B` | [Pk / fuze proxy boundary design](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md) | `pass`，定义 proxy variables、forbidden claims and authority-false shape |
| `G5-R-C` | [event-chain map](g5_research_event_chain_map_20260602.zh.md) | `pass`，串联 terminal geometry、fuze proxy、G4 mechanism、G4 component response and consequence surface |
| `G5-R-D` | [uncertainty / independence audit](g5_research_uncertainty_independence_audit_20260602.zh.md) | `pass`，确认 source/model/scope/result uncertainty and non-circularity |

## Integration Decision

`G5-R` can be marked `research_packet_accepted`:

- G5 now has a research source scan, proxy boundary, event-chain map and audit;
- `RES-013/014` remain authority-deferred boundaries, not current blockers;
- G4-R-B and G4-R-C remain research dependencies only;
- candidate bundle remains non-authoritative;
- machine guards remain false.

## Validation

Current workspace validation:

```bash
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py --output /tmp/a2_candidate_vps_bundle_g5_research_acceptance.json
python -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_source_admission_audit.py tests/architecture/damage_model/test_retained_manifest_integrity.py
python -m pytest -q tests/architecture/damage_model/test_benchmark_evidence_admission.py tests/architecture/damage_model/test_source_evidence_governance.py tests/architecture/damage_model/test_external_signoff_intake_contracts.py tests/architecture/damage_model/test_external_signoff_admission_preflight.py
rg -n "pk_authorit[y].*true|deterministic_fuze_authorit[y].*true|stock_descriptor_create[d].*true|replacement_allowe[d].*false" docs/task/air_combat/archive/a2_high_fidelity_damage_model/g5_research_*.zh.md docs/task/air_combat/archive/a2_high_fidelity_damage_model/data_collection/kill_chain_proxy_methods
git diff --check
```

Expected result:

- retained manifest integrity: `manifest_count=29`, `missing_total=0`,
  `sha_mismatch_total=0`, `guard_true_total=0`;
- source admission strict: `9 ledgers, 29 candidate docs, 53 calibration docs`;
- candidate bundle: `status=candidate_non_authoritative_bundle`,
  `research_blocker_residual_ids=[]`;
- `pk_authority=false`;
- `deterministic_fuze_authority=false`;
- candidate/source/manifest tests: `15 passed`;
- retained packet focused tests: `34 passed`;
- G5 guard grep: no matches;
- `git diff --check`: exit 0.

This does not mean full A2 kill-chain completion. It means G5 research proxy packet
is accepted as a non-authoritative, replaceable design surface.
