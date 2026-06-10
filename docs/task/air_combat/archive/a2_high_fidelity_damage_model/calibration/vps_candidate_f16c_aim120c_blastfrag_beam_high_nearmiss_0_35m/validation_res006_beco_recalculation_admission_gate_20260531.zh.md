# Validation RES-006 BEC-O Recalculation Admission Gate - 2026-05-31

状态：`partial_fail_closed_res006_beco_recalculation_admission / non-authoritative / hash-only`。

本文记录 `A2-RES006-BECO-ADMISSION` 对 BEC-O blast mechanism recalculation/hash/tolerance blocker 的窄域收口结果。对应工具为
[a2_blastfrag_res006_beco_recalculation_admission_gate.py](../../../../../../tools/maintenance/a2_blastfrag_res006_beco_recalculation_admission_gate.py)。

本 gate 只处理 `RES-006`：不修改 `mechanism_comparison_hashes` cached anchors，不编辑 `residual_register`，不处理 `RES-003/004/005`，不复制 spreadsheet formulas/raw selected values/raw output values，不释放 stock/runtime/effect-scale/component/Pk/fuze authority。

## 1. Retained Artifacts

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.res006_beco_recalculation_admission_gate.v1` |
| `retained_gate` | [res006_beco_recalculation_admission_gate.json](retained_artifacts/res006_beco_recalculation_admission_20260531/res006_beco_recalculation_admission_gate.json) |
| `retained_gate_sha256` | `d45a56aa6d8be816a60b0e9cef31331c582c90f5efe30b6e25c770feb3ec0e8a` |
| `candidate_anchor_set` | [beco_recalculated_hash_anchor_set.json](retained_artifacts/res006_beco_recalculation_admission_20260531/beco_recalculated_hash_anchor_set.json) |
| `candidate_anchor_set_sha256` | `2d26a10918223bfb2b229ed9d11fb0d378d473f0c3dd8674917b8dbb995550a5` |
| `retained_manifest` | [manifest.json](retained_artifacts/res006_beco_recalculation_admission_20260531/manifest.json) |
| `retained_manifest_sha256` | `e056d2c46d346dfc3c9e3f27ac243c95b37b0388e630477ea4ebacf4158a4b65` |

## 2. Gate Result

| 项 | 结果 |
|---|---|
| `RES-006` | `res006_remains_blocked_fail_closed` |
| cached anchors | 9/9 present from `mechanism_comparison_hashes.v1` |
| headless recalculation | completed via `LibreOffice 24.2.7.2 420(Build:2)` |
| recalculated hash anchors | 9/9 retained as candidate replacement set |
| exact cached-vs-recalculated hash check | failed, 0 match / 9 mismatch |
| replacement anchor admission | false |
| allowed-output signoff | false |
| tolerance policy admitted | false |
| residual closed by this gate | none |

当前真实结论：`RES-006` 没有关闭，但 blocker 被精确收口为“candidate recalculated hash anchor set 已保留，仍缺 allowed-output / tolerance / replacement signoff”。

## 3. Mismatch Lineage

Cached anchors 的来源是既有 `mechanism_comparison_hashes.v1`：它读取 workbook cached formula values 并只保留 hash anchor；该路径明确 `spreadsheet_calculation_executed=false`。

Recalculated anchors 的来源是本机 headless LibreOffice reopen/recalculate copy；该路径只保留 selected output hashes，不保留 raw selected values、formula text、temporary workbook copy、stdout 或 stderr。

本轮观测：

| 指标 | 值 |
|---|---:|
| cached anchor count | 9 |
| recalculated anchor count | 9 |
| matching count | 0 |
| mismatch count | 9 |
| missing recalculated count | 0 |

因此，不能把 recalculated hash set 直接视为 cached anchors 的等价验证；只能作为 replacement candidate。

## 4. Replacement Path

已经形成的可执行路径：

| requirement | status |
|---|---|
| retained recalculated hash-only anchor set | present |
| independent reviewer accepts runtime/version lineage | missing |
| allowed-output policy admits selected comparison output hashes | missing |
| exact-hash replacement or numeric tolerance policy signoff | missing |
| separate retained replacement promotion artifact | missing |

允许的下一步不是原地改 `mechanism_comparison_hashes`，而是另起 retained replacement artifact：把本 gate 的 candidate anchor set 作为输入，经独立 reviewer 和 allowed-output/tolerance policy signoff 后再 promotion。

## 5. Authority Guards

| guard | value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `runtime_authority_granted` | `false` |
| `fragment_mechanism_authority_granted` | `false` |
| `blast_mechanism_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |
| `benchmark_consumption_authority_granted` | `false` |
| `replacement_anchor_authority_granted` | `false` |

## 6. Verification

```bash
python3 tools/maintenance/a2_blastfrag_res006_beco_recalculation_admission_gate.py
pytest -q tests/architecture/damage_model/test_benchmark_recalculation_admission.py
```

本轮聚焦测试结果：`4 passed in 6.31s`。
