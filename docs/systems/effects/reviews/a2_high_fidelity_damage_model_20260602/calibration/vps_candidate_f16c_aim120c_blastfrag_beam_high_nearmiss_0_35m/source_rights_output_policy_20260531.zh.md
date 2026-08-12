# Source Rights / Allowed-Output Policy Gate - 2026-05-31

状态：`blocked_release_candidate_rights_supported_policy_fail_closed / release-candidate / non-authoritative / RES-001`。

本文档记录 `A2-EV-SOURCE-RIGHTS-OUTPUT-POLICY` 对已 retained 且 hash 匹配的 `TP-20.pdf`、`BEC-O-V1.xlsx`、`TP-21.pdf` 三个 payload 的 rights review / allowed-output policy gate。对应工具为 [damage_model.py](../../../../../../../tools/maintenance/damage_model.py) `source-governance rights-output-policy`。

本 gate 不创建 stock descriptor，不消费 benchmark output，不复制 payload 正文或 spreadsheet 输出，不授予 `effect_scale_authority`、`component_failure_probability_authority`、`pk_authority` 或 `deterministic_fuze_authority`。

## 1. 元数据

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.source_rights_output_policy_gate.v1` |
| `policy_id` | `A2-RES001-SOURCE-RIGHTS-OUTPUT-POLICY-20260531` |
| `policy_status` | `release_candidate_fail_closed_policy_frozen` |
| `RES-001 gate result` | `blocked` |
| `source_payload_pack_manifest` | `retained_artifacts/source_payload_pack_20260531/source_artifact_pack_manifest.json` |
| `source_payload_pack_manifest_sha256` | `2fc93a823a7b39328f6ac3238da08904867a82c5308f981ec04f1cf5bdc4d729` |
| `source_rights_output_policy_gate` | `retained_artifacts/source_rights_output_policy_20260531/source_rights_output_policy_gate.json` |
| `source_rights_output_policy_gate_sha256` | `4bbab21fd610dce1b4183e1e6a75e1f781aa8e2e26824ddaa0a5ed6751edcd71` |
| `retained_manifest` | `retained_artifacts/source_rights_output_policy_20260531/manifest.json` |
| `retained_manifest_sha256` | `97379275be5ae53d7e607a727b638ad254c9bbc05eaf35adde7b63f362dcc8ca` |

## 2. Gate Result

| check | result |
|---|---|
| payload retention | `complete`；三份 payload 均存在且 sha256 匹配 source payload pack |
| rights public-distribution support | `supported_candidate`；三份 payload 均检测到 public-release / distribution-unlimited statement 或等价 phrase id |
| release-grade rights review | `false`；公开分发声明可支持 review，但不是 reviewer signoff |
| allowed-output policy freeze | `true`；本 gate 冻结 fail-closed release-candidate copy/hash/consume policy |
| allowed-output release-grade | `false`；尚无 reviewer-frozen release-grade status |
| comparison outputs admitted | `false`；当前没有 selected comparison-output hash manifest |
| benchmark consumption | `false`；payload 和 tool outputs 均未作为 release benchmark input 消费 |
| RES-001 gate result | `blocked` |

最小剩余 blocker：

| blocker |
|---|
| `independent_rights_reviewer_signoff_missing` |
| `allowed_output_policy_release_grade_signoff_missing` |
| `selected_comparison_output_hash_manifest_missing` |
| `benchmark_consumption_release_signoff_missing` |
| `authority_boundary_signoff_missing` |

## 3. Payload Rights Inventory

| payload | sha256 | retention | rights status | public-distribution support | allowed use | forbidden use | output policy |
|---|---|---|---|---|---|---|---|
| `TP-20.pdf` | `293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f` | `retained_hash_matched` | `public_distribution_statement_supported_rights_review_candidate` | `distribution_statement_a_public_release_unlimited` via `pdf_first_8_pages` | candidate provenance、hash、rights evidence、blast method design reference only | 不复制正文/表格/图；不消费文档示例为 benchmark；不作为 source truth、runtime、stock、effect、component、Pk、fuze authority | `release_candidate_fail_closed_policy_frozen` |
| `BEC-O-V1.xlsx` | `82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc` | `retained_hash_matched` | `public_distribution_statement_supported_rights_review_candidate` | `distribution_statement_a_public_release_unlimited` via `xlsx_shared_strings_and_docprops` | candidate provenance、hash、rights evidence、future tool-output hash planning only | 不复制 spreadsheet body/formula/cell/output tables；不消费 tool outputs 为 benchmark；不作为 source truth、runtime、stock、effect、component、Pk、fuze authority | `release_candidate_fail_closed_policy_frozen` |
| `TP-21.pdf` | `84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8` | `retained_hash_matched` | `public_distribution_statement_supported_rights_review_candidate` | `public_release_distribution_unlimited` via `pdf_first_8_pages` | candidate provenance、hash、rights evidence、debris vocabulary reference only | 不复制正文/表格/图；不消费文档示例为 benchmark；不作为 source truth、runtime、stock、effect、component、Pk、fuze authority | `release_candidate_fail_closed_policy_frozen` |

说明：public-distribution support 仅表示 retained payload 中可见的公开分发声明足以支持后续 rights reviewer 判断；本 gate 不把该 evidence 提升为 release-grade approval。

## 4. Allowed-Output Policy

| output class | hash policy | copy policy | consume policy |
|---|---|---|---|
| retained payload files | 可记录 `retained_payload_file_sha256` | 只能复制 filename、sha256、content type、statement locator / phrase id、rights status、allowed/forbidden use | 不得作为 release benchmark input 消费 |
| source / rights manifests | 可记录 `source_manifest_sha256`、`rights_policy_gate_sha256` | 可复制 machine-readable policy metadata | 仅作为 evidence manifest，不是 simulation authority |
| future selected comparison/tool outputs | 仅在 reviewer admission 后可记录 selected output sha256 | 当前不得复制 raw values、tables、cell ranges 或 comparison values | 当前不得消费；未来需 selected hash manifest + benchmark consumption signoff |
| BEC-O spreadsheet formulas / cell ranges / output tables | 不作为当前 admitted output hash | 不得复制 | 不得消费为 release benchmark 或 source truth |
| TP-20 / TP-21 document tables、figures、examples | 不作为当前 admitted output hash | 不得复制正文、表格、图或大段摘录 | 不得消费为 release benchmark、calibration input 或 authority |
| stock/effect/component/Pk/fuze authority outputs | 不得由本 gate hash 成 authority evidence | 不得复制为 descriptor fields | 不得消费或释放 authority |

## 5. Release-Grade Signoff Fields

当前 policy 不能 claim release-grade；剩余 signoff 字段如下：

| field | current | required |
|---|---|---|
| `rights_reviewer_identity` | `missing` | named independent rights reviewer or release owner |
| `rights_review_decision` | `missing` | `release_reviewed` or `reviewer_approved_public_retention` |
| `allowed_output_policy_reviewer_identity` | `missing` | named reviewer who freezes copy/hash/consume policy |
| `allowed_output_policy_release_grade_status` | `release_candidate_fail_closed_policy_frozen` | `reviewer_frozen_release_grade` or `independently_reviewed_release_grade` |
| `selected_comparison_output_hash_manifest_sha256` | `missing` | sha256 manifest for each admitted comparison/tool output |
| `benchmark_consumption_signoff` | `missing` | explicit consume-or-do-not-consume release decision |
| `authority_boundary_signoff` | `missing` | reviewer confirmation that no stock/runtime/Pk/fuze authority is released |

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
python tools/maintenance/damage_model.py source-governance rights-output-policy --write-retained-artifacts
python -m pytest -q tests/architecture/damage_model/test_source_evidence_governance.py
```
