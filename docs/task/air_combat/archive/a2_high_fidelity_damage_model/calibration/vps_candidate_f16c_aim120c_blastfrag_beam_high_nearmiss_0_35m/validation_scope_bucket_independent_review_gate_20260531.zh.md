# Validation Scope/Bucket Independent Review Gate - RES-007 / RES-008

状态：`scope_bucket_independent_review_passed_release_blocked / non-authoritative / stage_b_scope_bucket_only`。

本文档记录 `A2-EV-SCOPE-BUCKET-INDEPENDENT-REVIEW` 对 `RES-007`
和 `RES-008` 的 bounded scope/bucket independent review gate。该 gate
消费当前 scope boundary probe 复跑结果、Stage B result pack、Stage B
independent review 输出，以及 scope/independence manifest。

它不创建 runtime descriptor，不授予 stock runtime authority，不提升 formal
validation manifest，不释放 effect scale、component failure probability、Pk
或 deterministic fuze authority。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.scope_bucket_independent_review_gate.v1` |
| `reviewer_role` | `A2-EV-SCOPE-BUCKET-INDEPENDENT-REVIEW` |
| `review_target` | `RES-007_RES-008_scope_bucket_independent_review_only` |
| `gate_status` | `scope_bucket_independent_review_passed_release_blocked` |
| `retained_gate_artifact` | [scope_bucket_independent_review_gate.json](retained_artifacts/scope_bucket_independent_review_20260531/scope_bucket_independent_review_gate.json) |
| `retained_probe_rerun` | [scope_boundary_probe_rerun.json](retained_artifacts/scope_bucket_independent_review_20260531/scope_boundary_probe_rerun.json) |
| `retained_manifest` | [manifest.json](retained_artifacts/scope_bucket_independent_review_20260531/manifest.json) |

## 2. Gate Decision

| residual | review area | scope/bucket review status | gate decision | residual register 语义 |
|---|---|---|---|---|
| `RES-007` | `near_miss_0_35m_bucket_boundary` | `narrow_stage_b_scope_review_complete` | `narrow_pass_stage_b_scope_only` | `remains_open_release_blocked` |
| `RES-008` | `beam_high_scope_boundary` | `narrow_stage_b_scope_review_complete` | `narrow_pass_stage_b_scope_only` | `remains_open_release_blocked` |

上述 pass 只表示 bounded Stage B scope/bucket evidence slice 已有独立 review
闭合。它不表示 `RES-007` 或 `RES-008` 可在 release / runtime authority
层面关闭。

## 3. Probe Coverage Summary

| probe | 覆盖 | 当前判定 |
|---|---|---|
| `SCP-PROBE-001` miss distance | `0.25 / 0.35 / 0.45 m`，含 `0.35 m` anchor | 三点均保留在 runtime coarse bucket `near_miss`，scaled distance 单调增加，fragment areal density 单调下降。 |
| `SCP-PROBE-002` closure | `700 / 900 / 1100 mps` | candidate closure response active，且不是 constant；probe 本身不 self-close `RES-008`。 |
| `SCP-PROBE-003` aspect guard | accepted `beam` only | required rejection labels 全部覆盖。 |

Boundary rejection coverage：

| 类别 | 标签 |
|---|---|
| accepted | `beam` |
| rejected | `head_on`, `tail_chase`, `high_off_boresight`, `direct_hit`, `closure_bucket != high`, `weapon_family != blast_fragmentation` |
| missing rejected labels | `[]` |

## 4. Consumed Evidence

| evidence | 当前状态 |
|---|---|
| scope boundary probe rerun | `candidate_non_authoritative_scope_probe_results` |
| scope / independence manifest | `scope_manifest_complete` |
| Stage B result pack | `result_pack_complete` |
| Stage B independent review gate | `independent_review_complete` |
| Stage B independent review manifest | present |
| Stage B independent review doc | present |

当前 `missing_review_evidence` 为 `[]`，`fail_closed_blockers` 为 `[]`。

## 5. Authority Guards

| guard | 值 |
|---|---|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `stock_runtime_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |
| `formal_validation_manifest_promoted` | `false` |
| `hard_gate_pass_is_release` | `false` |

Release 仍由 `RES-001/002/003/004/005/006` 与 `RES-013/014-boundary`
阻塞。不得把本 gate 的 narrow pass 叙述为 stock runtime authority、validated
near-miss sub-bucket authority、closure physics authority、component probability
authority、Pk authority 或 deterministic fuze authority。

## 6. 复现命令

```bash
python3 tools/maintenance/damage_model_independent_review.py scope-bucket-review
pytest -q tests/architecture/damage_model/test_independent_review_closeout_gates.py
```

## 7. 当前判定

`RES-007` 与 `RES-008` 对当前 bounded Stage B scope/bucket slice 为
`narrow_pass_stage_b_scope_only`。Release、stock runtime、Pk、deterministic
fuze 与 component probability authority 全部继续 fail-closed。
