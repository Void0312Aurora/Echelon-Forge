# Source Payload Pack - 2026-05-31

状态：`partial_payloads_retained_release_review_blocked / candidate / non-authoritative / source_payload_pack`。

本文档记录 `A2-EV-SOURCE-PAYLOAD-PACK` 对 `RES-001 source provenance` 的实际 payload retained 情况，并给 `RES-002 release identity` 提供可消费但不放权的 source payload / rights / consumption evidence。对应工具为
[a2_blastfrag_source_payload_pack.py](../../../../../../tools/maintenance/a2_blastfrag_source_payload_pack.py)。

本 pack 不创建 stock descriptor，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.source_payload_pack.v1` |
| `pack_status` | `partial_payloads_retained_release_review_blocked` |
| `RES-001 gate result` | `blocked` |
| `RES-002 gate result` | `blocked` |
| `required_payload_count` | `3` |
| `retained_payload_count` | `3` |
| `missing_payload_count` | `0` |
| `source_payload_pack` | `retained_artifacts/source_payload_pack_20260531/source_payload_pack.json` |
| `source_payload_pack_sha256` | `0fd5e757ae5f64a8c12a44b4dc395c47d51860237a82b1ce7e5594fa4252384c` |
| `source_artifact_pack_manifest` | `retained_artifacts/source_payload_pack_20260531/source_artifact_pack_manifest.json` |
| `source_artifact_pack_manifest_sha256` | `2fc93a823a7b39328f6ac3238da08904867a82c5308f981ec04f1cf5bdc4d729` |
| `retained_manifest` | `retained_artifacts/source_payload_pack_20260531/manifest.json` |
| `retained_manifest_sha256` | `bf2ca1f9495d43244b9b20c56223136efd61356db304697fd4a8656d1e2a17be` |

## 2. Retained Payload Inventory

| source id | payload | retained path | sha256 | rights status | allowed use | benchmark consumption |
|---|---|---|---|---|---|---|
| `VPS-BFM-014` | `TP-20 PDF` | `retained_artifacts/source_payload_pack_20260531/payloads/TP-20.pdf` | `293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f` | `official_public_candidate_only_rights_not_release_reviewed` | `candidate_provenance_and_benchmark_design_reference_only` | `not_consumed_for_stage_b_release` |
| `VPS-BFM-014` | `BEC-O-V1.xlsx` | `retained_artifacts/source_payload_pack_20260531/payloads/BEC-O-V1.xlsx` | `82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc` | `official_public_candidate_only_rights_not_release_reviewed` | `candidate_provenance_and_benchmark_design_reference_only` | `not_consumed_for_stage_b_release` |
| `VPS-BFM-015` | `TP-21 PDF` | `retained_artifacts/source_payload_pack_20260531/payloads/TP-21.pdf` | `84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8` | `official_public_candidate_only_rights_not_release_reviewed` | `candidate_provenance_and_benchmark_design_reference_only` | `not_consumed_for_stage_b_release` |

说明：`TP-20.pdf` 与 `TP-21.pdf` 由 DENIX 官方 PDF 链接经浏览器网络体 retained，sha256 与 pin manifest 期望值一致；`.playwright-mcp/BEC-O-V1.xlsx` 也已复制到本 pack 的 canonical retained path。此动作只保留 payload 和 checksum，不表示 release-reviewed rights、benchmark-output admission 或 source truth。

## 3. Missing Payloads

无。`TP-20 PDF`、`BEC-O-V1.xlsx` 与 `TP-21 PDF` 三个 required payload 均已 retained，且 sha256 匹配。

因此本 pack 已经不再因 payload 缺失而 blocked；但 release-grade rights review、allowed-output policy signoff、benchmark-consumption chain 和 selected comparison-output hashes 的 release admission 仍未关闭，所以仍不得标记为 `closed` 或 `release_retained_source_artifact_pack`。

## 4. Policy / Consumption Status

| surface | status |
|---|---|
| rights review | `public_distribution_statement_supported_candidate_not_signed_off` |
| allowed-output policy | `release_candidate_fail_closed_policy_frozen`；policy 已冻结为 fail-closed，但尚无 reviewer-frozen release-grade status |
| allowed-output boundary | source rights/output policy gate 只允许 hash-only metadata；禁止复制 source bodies、spreadsheet cells、comparison values 或 runtime authority fields |
| benchmark consumption chain | `explicit_non_consumption_only_release_chain_missing` |
| explicit non-consumed artifacts | `PIN-BFM-001`, `PIN-BFM-002` |
| release-consumed artifacts | none |
| comparison-output hash status | `partial_hash_manifest_present_release_review_blocked` |
| selected comparison-output hashes | `9` 个 BEC-O cached formula hash-only anchors；均非 calibration，且未被 release benchmark 消费 |
| mechanism comparison hash manifest | `retained_artifacts/mechanism_comparison_hashes_20260531/mechanism_comparison_hashes.json` |

## 5. Gate Result

| residual | result | blocker summary |
|---|---|---|
| `RES-001` | `blocked` | required source payloads retained and hash-matched；public-distribution support 与 fail-closed policy 已记录；但 release rights reviewer signoff、allowed-output release-grade signoff、benchmark-consumption release chain 和 selected comparison-output hash release admission 仍缺 |
| `RES-002` | `blocked` | 本 pack 可作为后续 release identity lane 的 source-payload evidence，但不关闭 clean release identity、release validation status 或 independent reviewer signoff |

## 6. Authority Guards

所有 authority guards 保持 `false`：

| guard | 值 |
|---|---|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `runtime_authority_granted` | `false` |
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
python tools/maintenance/a2_blastfrag_source_payload_pack.py --write-retained-artifacts
python -m pytest -q tests/architecture/test_a2_blastfrag_source_payload_pack.py
python -m pytest -q tests/architecture/test_a2_blastfrag_source_payload_pack.py tests/architecture/test_a2_blastfrag_source_rights_output_policy.py tests/architecture/test_a2_blastfrag_mechanism_comparison_hashes.py
```
