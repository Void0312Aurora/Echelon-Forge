# Validation Geometry / Warhead Row Provenance Gate - 2026-05-31

状态：`generated_from_geometry_warhead_row_provenance_gate / non-authoritative / blocked`。

本文记录 `RES-003 target geometry` 与 `RES-004 warhead scope` 的 row-level provenance / bounds gate。该 gate 消费现有 target geometry assumptions、warhead scope/sensitivity、source ledgers、artifact pin manifest、以及可用的 mechanism/source closeout retained artifact。

本文不修改 [residual_register.zh.md](residual_register.zh.md)，不创建 runtime descriptor，不授予 target geometry、warhead、effect-scale、component probability、Pk 或 deterministic-fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.geometry_warhead_row_provenance_gate.v1` |
| `tool_ref` | [a2_blastfrag_geometry_warhead_row_provenance_gate.py](tools/maintenance/a2_blastfrag_geometry_warhead_row_provenance_gate.py) |
| `retained_artifact` | [geometry_warhead_row_provenance_gate.json](docs/task/air_combat/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/geometry_warhead_row_provenance_20260531/geometry_warhead_row_provenance_gate.json) |
| `retained_artifact_sha256` | `648758a2db8f21dc5f35f4b7cfa4ad520f502237881cfa2a1342961432359726` |
| `manifest` | [manifest.json](docs/task/air_combat/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/geometry_warhead_row_provenance_20260531/manifest.json) |
| `manifest_sha256` | `0dfdd2722ff7d28e96040812c655cada107849238093b9836b3be3717c30af0c` |
| `overall_status` | `blocked_non_authoritative_geometry_warhead_row_provenance_candidate` |

## 2. Current Gate Results

| residual | gate result | register status | upstream mechanism gate | true close by this gate | shortest remaining path |
|---|---|---|---|---:|---|
| `RES-003` target geometry | `blocked_row_level_bounds_missing` | `open_stage_b_witness_geometry_bookkeeping_closed_global_geometry_blocked` | `blocked_author_side_review_ready` | `false` | freeze row-level geometry provenance and reviewed uncertainty bounds for coarse bbox / beam witness rows |
| `RES-004` warhead scope | `blocked_warhead_class_bounds_missing` | `open_stage_b_family_scope_closed_specific_warhead_truth_blocked` | `blocked_author_side_review_ready` | `false` | freeze release-grade warhead class/sensitivity envelope without consuming toy mass or fuze/Pk values as truth |

## 3. Non-Authoritative Guards

| guard | current value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `target_geometry_authority_granted` | `false` |
| `row_level_geometry_authority_granted` | `false` |
| `aim120c_warhead_authority_granted` | `false` |
| `warhead_class_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |
| `fuze_authority_granted` | `false` |

`RES-013 Pk boundary` 和 `RES-014 deterministic fuze boundary` 不属于本 gate；当前 gate 明确保持 `Pk=false`、`deterministic_fuze=false`。

## 4. Current Decision

当前可审计结论为：

> `RES-003/004 have machine-readable author-side row provenance evidence, but row-level geometry uncertainty bounds and release-grade warhead class/sensitivity bounds are still missing; neither residual is closed`.

行为风险：

- 如果忽略 `RES-003`，coarse bbox 或 beam witness bookkeeping 可能被误写为真实 vulnerability geometry。
- 如果忽略 `RES-004`，repo toy warhead fields 或 third-party sanity values 可能被误写为 AIM-120C variant-specific truth。
- 如果忽略 source/pin 边界，candidate links 可能被误写为 release-grade rights、retention 或 authority。
