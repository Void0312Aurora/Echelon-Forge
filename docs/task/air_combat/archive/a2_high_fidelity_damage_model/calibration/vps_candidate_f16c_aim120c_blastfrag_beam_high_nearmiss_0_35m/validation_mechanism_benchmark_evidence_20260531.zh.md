# Validation Mechanism Benchmark Evidence - 2026-05-31

状态：`generated_from_mechanism_benchmark_evidence / non-authoritative / fail_closed_benchmark_evidence_manifest`。

本文记录 `RES-003 target geometry`、`RES-004 warhead scope`、`RES-005 fragment mechanism`、`RES-006 blast mechanism` 的 mechanism benchmark evidence 包。它来自
[damage_model.py](../../../../../../tools/maintenance/damage_model.py) `benchmark-evidence mechanism-evidence`，只消费仓库已有 source ledger、artifact pin、Stage B/C scaffold/result-pack 摘要和 closeout 文档面。

本文不修改 [residual_register.zh.md](residual_register.zh.md)，不创建 runtime descriptor，不授予 target geometry、AIM-120C warhead、fragment、blast、effect-scale、component probability、Pk 或 deterministic-fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.mechanism_benchmark_evidence.v1` |
| `tool_ref` | [damage_model.py](../../../../../../tools/maintenance/damage_model.py) `benchmark-evidence mechanism-evidence` |
| `retained_artifact` | [mechanism_benchmark_evidence.json](retained_artifacts/mechanism_benchmark_evidence_20260531/mechanism_benchmark_evidence.json) |
| `retained_artifact_sha256` | `f39d43539e2ec3c85fd7e5287481ccf25dc5412d9a3d6142e0f724b8fa14cfa4` |
| `review_target` | `res_003_004_005_006_mechanism_benchmark_evidence_lane` |
| `overall_status` | `blocked_fail_closed_mechanism_benchmark_evidence_manifest` |

## 2. Current Gate Results

| residual | evidence status | source present | candidate/scaffold consumed | benchmark consumed | release-grade validated | gate result |
|---|---|---:|---:|---:|---:|---|
| `RES-003` target geometry | `review_inputs_present_external_geometry_benchmark_missing` | `true` | `true` | `false` | `false` | `blocked_fail_closed_release_grade_geometry_benchmark_missing` |
| `RES-004` warhead scope | `scope_and_sensitivity_boundary_present_external_warhead_benchmark_missing` | `true` | `true` | `false` | `false` | `blocked_fail_closed_release_grade_warhead_sensitivity_benchmark_missing` |
| `RES-005` fragment mechanism | `source_routes_present_benchmark_payload_not_consumed` | `true` | `true` | `false` | `false` | `blocked_fail_closed_fragment_benchmark_payload_missing` |
| `RES-006` blast mechanism | `source_routes_present_benchmark_payload_not_consumed` | `true` | `true` | `false` | `false` | `blocked_fail_closed_blast_benchmark_payload_missing` |

当前真实关闭的 residual：`none`。

## 3. Source / Benchmark / Validation Separation

| path | source present | benchmark consumed | release-grade validated | interpretation |
|---|---:|---:|---:|---|
| `FRAG-GURNEY-BRL405` | `true` | `false` | `false` | Gurney source route exists, but official artifact/rights/checksum and velocity benchmark payload are still pending. |
| `FRAG-TP21-DEBRIS` | `true` | `false` | `false` | DENIX TP-21 public artifact is externally verified as candidate-only; it is not a retained release benchmark input. |
| `FRAG-TOY-SCAFFOLD` | `true` | `false` | `false` | Stage B/C fragment toy checks are hygiene evidence only, not calibrated fragment authority. |
| `BLAST-KINGERY-BULMASH` | `true` | `false` | `false` | Kingery-Bulmash report route is present, but original official artifact/output provenance is not consumed. |
| `BLAST-BEC-O-TP20` | `true` | `false` | `false` | DENIX TP-20/BEC-O artifacts are externally verified as candidate-only; no comparison-output hashes or release benchmark ingestion exist. |
| `BLAST-TOY-SCAFFOLD` | `true` | `false` | `false` | Stage B/C blast scaled-distance and impulse checks are toy hygiene only, not pressure/impulse validation. |

## 4. Shortest Remaining Paths

| residual | shortest path |
|---|---|
| `RES-003` | freeze row-level geometry uncertainty bounds; independently review that repo hitboxes are engineering scaffolds; add or explicitly waive a release-grade geometry benchmark payload |
| `RES-004` | freeze an AIM-120C-class sensitivity envelope that never treats toy mass as C-model truth; pin admitted benchmark/reference payloads or keep mass/TNT equivalent out of scope; keep Pk and deterministic fuze blocked |
| `RES-005` | resolve or exclude Gurney BRL-405; freeze TP-21 retained refs, allowed-output policy, comparison hashes and tolerances; replace toy fragment probes with retained/reference benchmark consumption |
| `RES-006` | resolve or exclude Kingery-Bulmash ARBRL-TR-02555; freeze TP-20/BEC-O retained refs, package version, output policy, comparison hashes and tolerances; review blast applicability envelope |

## 5. Non-Authoritative Guards

| guard | current value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `target_geometry_authority_granted` | `false` |
| `aim120c_warhead_authority_granted` | `false` |
| `fragment_mechanism_authority_granted` | `false` |
| `blast_mechanism_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |

`RES-013 Pk boundary` 和 `RES-014 deterministic fuze boundary` 不属于本 mechanism benchmark evidence gate；当前 gate 明确保持 `Pk=false`、`deterministic_fuze=false`。

## 6. Current Decision

当前可审计结论为：

> `RES-003/004/005/006 have source-present and toy/scaffold hygiene evidence, but no path has benchmark_consumed=true or release_grade_validated=true; the mechanism benchmark evidence package therefore fails closed`.

行为风险：

- 如果忽略 `RES-003`，F-16 witness geometry 可能被误写为真实 vulnerability geometry。
- 如果忽略 `RES-004`，AIM-120C-class toy warhead inputs 可能被误写为 C-model mass、TNT equivalent 或 fuze truth。
- 如果忽略 `RES-005/006`，Gurney/TP-21 或 Kingery-Bulmash/BEC-O 的 source presence 可能被误写为 consumed benchmark 或 release validation。
