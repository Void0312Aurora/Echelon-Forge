# Validation Provenance / Identity Review Gate - 2026-05-31

状态：`blocked / candidate / non-authoritative / provenance_identity_review_gate`。

本文档记录 `RES-001 source provenance` 与 `RES-002 surrogate identity` 的 release-grade review gate。对应工具为
[damage_model_release_governance.py](../../../../../../tools/maintenance/damage_model_release_governance.py) `provenance-identity-review`。

本 gate 只保留 review blocker surface，不创建 stock descriptor，不授予
`effect_scale_authority`、`component_failure_probability_authority`、`pk_authority`
或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.provenance_identity_review_gate.v1` |
| `review_target` | `res_001_002_provenance_identity_release_review` |
| `readiness_level` | `author_side_subitems_partly_closed_release_grade_review_blocked` |
| `gate_status` | `blocked_non_authoritative_provenance_identity_review_gate` |
| `retained_review_artifact` | `retained_artifacts/provenance_identity_review_20260531/provenance_identity_review_gate.json` |
| `retained_review_artifact_sha256` | `730329ee9b227ffdd1dc87fbfa644479d99e7b7e1100b7f8c151919395cd8bbb` |
| `retained_review_manifest` | `retained_artifacts/provenance_identity_review_20260531/manifest.json` |
| `retained_review_manifest_sha256` | `208274cc976e2e0c4fa8aa38aecaccd23e34ec8c23bf49ae3b6a034256a5a25d` |
| `canonical_source_payload_pack_consumed` | `retained_artifacts/source_payload_pack_20260531/source_artifact_pack_manifest.json` |
| `source_payload_retention_status` | `satisfied_3_of_3_payloads_retained_hash_verified_release_review_blocked` |

## 2. Review Checks

| `check_id` | residual | review surface | author-side 是否满足 | release-grade 是否满足 | 当前判定 |
|---|---|---|---|---|---|
| `REVIEW-RES001-001` | `RES-001` | `retained_source_artifact_pack` | yes | no | canonical `source_payload_pack_20260531/source_artifact_pack_manifest.json` 已保留并 hash-verified TP-20、BEC-O-V1、TP-21 3/3 payload；release-grade rights review 与 source-pack status 仍未闭合。 |
| `REVIEW-RES001-002` | `RES-001` | `allowed_output_policy` | yes | no | source rights/output policy 已冻结为 `release_candidate_fail_closed_policy_frozen`；但仍缺 release-grade reviewer signoff。 |
| `REVIEW-RES001-003` | `RES-001` | `benchmark_consumption_trace` | yes | no | `PIN-BFM-001` 与 `PIN-BFM-002` 已显式 `not_consumed_for_stage_b_release`；但没有 release-reviewed benchmark-consumption chain。 |
| `REVIEW-RES001-004` | `RES-001` | `comparison_output_hash` | yes | no | source payload pack 已消费 mechanism comparison hash manifest，记录 9 个 BEC-O hash-only cached anchors；但它们未经过 release admission、spreadsheet execution/recalculation、tolerance 和 benchmark-consumption signoff。 |
| `REVIEW-RES002-001` | `RES-002` | `clean_release_identity` | yes | no | model/version/repo anchor 已记录；但 `worktree_state` 不是 `clean_release_candidate`，且 identity manifest 仍含 3 个 `/tmp` author-side output anchors。 |
| `REVIEW-RES002-002` | `RES-002` | `release_validation_status` | yes | no | validation 状态字段已显式记录；但 identity 为 `not_validated`，validation manifest 为 `unvalidated`。 |
| `REVIEW-RES002-003` | `RES-002` | `retained_identity_surface` | yes | no | Stage B 与 Stage C author-side retained packs 完整存在；但仍不是 independent release identity artifact。 |
| `REVIEW-RES001-002-001` | `RES-001`, `RES-002` | `independent_review_signoff` | no | no | 没有覆盖 `RES-001/RES-002` 的 independent review signoff manifest。 |

## 3. RES-001 / RES-002 Gate Result

| residual | author-side 已关闭 check | author-side 仍缺 check | release-grade 仍阻塞 check | gate result |
|---|---|---|---|---|
| `RES-001` | `REVIEW-RES001-001`, `REVIEW-RES001-002`, `REVIEW-RES001-003`, `REVIEW-RES001-004` | `REVIEW-RES001-002-001` | `REVIEW-RES001-001`, `REVIEW-RES001-002`, `REVIEW-RES001-003`, `REVIEW-RES001-004`, `REVIEW-RES001-002-001` | `blocked` |
| `RES-002` | `REVIEW-RES002-001`, `REVIEW-RES002-002`, `REVIEW-RES002-003` | `REVIEW-RES001-002-001` | `REVIEW-RES002-001`, `REVIEW-RES002-002`, `REVIEW-RES002-003`, `REVIEW-RES001-002-001` | `blocked` |

## 4. 当前可关闭的 author-side 子项

- `RES-001`：verified DENIX source artifact rows 和 sha256 pins 已存在；canonical source payload pack 已保留并校验 3/3 payload；fail-closed allowed-output policy 已冻结；DENIX rows 的 Stage B release non-consumption trace 已存在；BEC-O 9 个 hash-only cached comparison anchors 已作为非 release-grade evidence 被记录。
- `RES-002`：surrogate model/version/repo anchor 已存在；Stage B 与 Stage C author-side retained identity surfaces 已存在。

这些只关闭 author-side review surface，不关闭 release-grade residual。

## 5. 最短剩余路径

| residual | shortest remaining path |
|---|---|
| `RES-001` | 保持 canonical `retained_artifacts/source_payload_pack_20260531/source_artifact_pack_manifest.json` 作为 source payload pack；补齐 release-grade rights review / reviewer-retained source-pack status；冻结 release-grade allowed-output policy；固定 selected comparison-output sha256；记录 reviewed benchmark-consumption 或 explicit release non-consumption decision；取得 independent reviewer signoff。 |
| `RES-002` | 发布 clean release identity state，移除 `/tmp` anchors，validation status 只能在 formal result table、residual closeout 和 independent reviewer signoff 后提升；新增 distinct release identity artifacts，而不是复用 author-side retained packs。 |

## 6. Authority Guards

所有 authority guards 保持 `false`：

| guard | 值 |
|---|---|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `effect_scale_authority_released` | `false` |
| `effect_scale_authority_in_stock` | `false` |
| `component_failure_probability_authority_released` | `false` |
| `component_failure_probability_authority_in_stock` | `false` |
| `pk_authority_released` | `false` |
| `pk_authority` | `false` |
| `deterministic_fuze_authority_released` | `false` |
| `deterministic_fuze_authority` | `false` |

## 7. 复核命令

```bash
python tools/maintenance/damage_model_release_governance.py provenance-identity-review --write-retained-artifact --retained-output-dir docs/task/air_combat/archive/a2_high_fidelity_damage_model/calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/provenance_identity_review_20260531 --output /tmp/a2_provenance_identity_review_retained_manifest.json
python -m pytest -q tests/architecture/damage_model/test_release_authority_guardrails.py
```
