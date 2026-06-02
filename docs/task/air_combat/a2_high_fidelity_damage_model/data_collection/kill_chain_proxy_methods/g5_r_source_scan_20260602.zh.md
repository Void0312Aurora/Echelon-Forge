# A2 G5-R Source Scan - 2026-06-02

状态：`2026-06-02 / G5-R-A-SOURCE-SCAN / pass / research_candidate / non_authoritative`。

本文是 `G5-R` Pk / fuze proxy 的第一波方法来源扫描。它只为 research proxy design
提供可审计输入，不授予 `pk_authority` 或 `deterministic_fuze_authority`，不移除现有
RNG-compatible fallback。

## 输入分层

| source id | 输入 | class | rights / scope | 可支持 | 不可支持 | uncertainty / confidence | replacement rule |
|---|---|---|---|---|---|---|---|
| `G5SRC-001` | [G4-R-B mechanism-load envelope draft](../../g4_research_mechanism_load_envelope_draft_20260601.zh.md) | `repo_internal_research_input` | repo-internal；AIM-120C-class / F-16C candidate scope | mechanism-load axis、blast / fragment qualitative vector | real warhead truth、effect-scale authority、Pk | medium；依赖 derived proxy 和 placeholder | 被更完整 mechanism-load source ledger 或 admitted row 替换 |
| `G5SRC-002` | [G4-R-C component fragility surface draft](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md) | `repo_internal_research_input` | repo-internal；component fragility research surface | component response axis、consequence mapping placeholders | calibrated component probability、aircraft-wide fragility truth | medium-low；缺 independent fragility truth | 被独立 fragility benchmark / reviewer packet 替换 |
| `G5SRC-003` | [G4-R-C uncertainty / independence audit](../../calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | `repo_internal_boundary_input` | repo-internal；uncertainty / independence boundary | G5 proxy uncertainty categories and non-circularity checks | result-level independent truth | medium | 被 G5-specific uncertainty audit 替换 |
| `G5SRC-004` | [fuze authority package](../../fuze_authority/README.zh.md) | `repo_internal_method_reference` | repo-internal；future deterministic fuze admission design | fuze event fields, replay/admission shape, forbidden claims | deterministic fuze admission | high for boundary, low for data truth | 被 G5-R fuze proxy manifest draft 替换 |
| `G5SRC-005` | [AIM-120C warhead / fuze collection](../aim120c_warhead_fuze/README.zh.md) | `tier_b_c_public_candidate_summary` | public / third-party mixed；AIM-120C-class caveats | public terminology, warhead/fuze family sanity | trigger threshold、delay、reliability、Pk | low-medium；variant uncertainty high | 被 stronger source ledger rows with rights and source refs 替换 |
| `G5SRC-006` | [guidance miss-distance public methods](../guidance_miss_distance_public_methods/README.zh.md) | `tier_a_b_method_reference` | public methods；guidance / terminal geometry | miss-distance axis and terminal geometry proxy | fuze truth or Pk | medium | 被 executed guidance/miss-distance benchmark packet 替换 |
| `G5SRC-007` | [guidance evasion benchmark methods](../guidance_evasion_benchmark_methods/README.zh.md) | `tier_a_b_method_reference` | public methods；terminal evasion / benchmark | evasion / terminal geometry sanity envelope | kill probability truth | medium-low | 被 G5-specific event-chain benchmark packet 替换 |
| `G5SRC-008` | [runtime status](../../runtime_status.zh.md) and existing event/report surfaces | `repo_internal_runtime_input` | repo-internal runtime contract | consequence flags and event-consumer boundary | probability calibration or fuze admission | high for shape, low for realism truth | 被 maintained runtime contract / tests 替换 |

## Rejected / sanity-only 输入

| source group | decision | reason |
|---|---|---|
| game database / simulator config / balance table | `rejected_for_parameter_use` | 不得导入 Pk、kill radius、fuze radius、damage value、fragment field 或 hidden balance value |
| forum table / anonymous spreadsheet / single chart | `rejected_or_sanity_only` | provenance、rights、scope 和 uncertainty 不足；不能支撑 research row |
| training reward / combat win smoke | `rejected_for_truth_claim` | reward consumer 可以测试流程，不能反向定义 Pk 或 fuze truth |
| retained restricted payload raw output | `hash_only_context` | 可记录 locator/hash/rights note，不能复制 raw selected values 或消费为 release evidence |

## 可进入 G5-R 的字段形状

| field family | research value type | required notes |
|---|---|---|
| terminal geometry | qualitative bucket / derived range / event ref | source ids, coordinate frame, scope, uncertainty |
| fuze proxy | branch label / fallback-compatible trigger window | no deterministic trigger claim, no threshold truth |
| mechanism-load coupling | reference to `G4-R-B` axis | replacement rule and sensitivity trigger |
| component response coupling | reference to `G4-R-C` surface | no aircraft-wide truth claim |
| consequence aggregation | ordered consequence label or non-probability score placeholder | not Pk, not mission-kill probability |
| uncertainty | epistemic / aleatory / source / model-form labels | confidence and replacement path |

## Worker Packet

```md
status: pass
touched files:
- docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/kill_chain_proxy_methods/README.zh.md
- docs/task/air_combat/a2_high_fidelity_damage_model/data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md
commands/outcomes:
- pending integration validation
remaining paths:
- G5-R-B proxy boundary design
- G5-R-C event-chain map
- G5-R-D uncertainty / independence audit
behavior risks:
- accidentally treating proxy score as Pk
- accidentally treating fuze branch labels as deterministic admission
integration notes:
- Use this scan as input only; do not create stock/runtime rows.
research boundary confirmation:
- `pk_authority=false`
- `deterministic_fuze_authority=false`
```
