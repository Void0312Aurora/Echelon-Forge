# Validation Mechanism Comparison Hashes - 2026-05-31

状态：`partial_fail_closed_mechanism_comparison_hash_manifest / non-authoritative / hash-only`。

本文记录 `A2-EV-MECH-COMPARISON-HASHES` 对 retained `TP-20.pdf`、`BEC-O-V1.xlsx`、`TP-21.pdf` 的 mechanism comparison-output hash pass。对应工具为
[damage_model.py](../../../../../../tools/maintenance/damage_model.py) `benchmark-evidence comparison-hashes`。

本文不修改 runtime、stock descriptor、source rights/policy、provenance gate 或 Stage C benchmark 文件；不把 BEC-O/TP-21 source presence 当 calibration；不释放 `effect_scale_authority`、`component_failure_probability_authority`、`Pk` 或 deterministic fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_beam_high_near_miss_0_35m_v0` |
| `schema_version` | `a2.mechanism_comparison_hashes.v1` |
| `retained_artifact` | [mechanism_comparison_hashes.json](retained_artifacts/mechanism_comparison_hashes_20260531/mechanism_comparison_hashes.json) |
| `retained_artifact_sha256` | `5d267029a11a47f281f726d6c58131aea946294a7979d8dcfaa72b27141973d1` |
| `retained_manifest` | [manifest.json](retained_artifacts/mechanism_comparison_hashes_20260531/manifest.json) |
| `retained_manifest_sha256` | `7a4df32ec984718bc914c912235b2b2d8e37e1a363be4331e6fb8c78aeac226e` |
| `BEC-O selected output set sha256` | `93dcc54794dd391b88bd5a6c6a5e50ef80eb739dac18fbd645df4ec671218f21` |
| `TP-21 criteria vocabulary sha256` | `6760351838bd84a24945a5459f53fffc8326edbaf447cb0e2223f7228a2b1969` |

## 2. Gate Result

| residual | gate result | current evidence | still blocked by |
|---|---|---|---|
| `RES-005` | `partial_fail_closed_tp21_criteria_vocabulary_hash_present_selected_debris_output_requirements_open` | TP-21 payload hash retained；controlled criteria vocabulary/hash retained；no source prose/table copied. | reviewer-selected debris comparison cases and hash-only outputs are still missing. |
| `RES-006` | `partial_fail_closed_beco_cached_comparison_hashes_present_spreadsheet_execution_required` | TP-20/BEC-O payload hashes retained；BEC-O workbook metadata/sheet inventory retained；9 cached formula output hashes retained. | spreadsheet calculation was not executed; release use still requires reviewed execution chain, tolerance and allowed-output policy. |

当前真实关闭的 residual：`none`。

## 3. BEC-O Workbook Hash Surface

Workbook sha256：`82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc`。

Sheet inventory 已在 retained JSON 中记录为 sheet name、dimension、formula/cached-value counts；不保留公式文本或 raw cached values。当前 workbook 可解析，且 selected cells 均有 numeric cached formula value；但本 worker 没有执行 spreadsheet calculation，所以这些 hash 只能作为后续工具/人工复算的 anchor。

| comparison id | sheet | cell | output role | comparison-output sha256 |
|---|---|---|---|---|
| `BEC-O-METRIC-DEFAULT-001` | `METRIC UNITS` | `E36` | `scaled_distance_metric_default` | `e1f06f693bd44bfb437fdc95ccf97e36e0edfda1e77e8cfca3124206ce1ac92c` |
| `BEC-O-METRIC-DEFAULT-002` | `METRIC UNITS` | `E38` | `time_of_arrival_metric_default` | `abf887eb1fbdafb1bda0f4d3352633f0239f59d2023ff2a93b5108e4d36f2783` |
| `BEC-O-METRIC-DEFAULT-003` | `METRIC UNITS` | `E40` | `incident_pressure_metric_default` | `0dbe8724edceb81f592172adaee4fc2e0ceb9706117e9d947e12f60f7e7e6ac5` |
| `BEC-O-METRIC-DEFAULT-004` | `METRIC UNITS` | `E43` | `reflected_pressure_metric_default` | `8e3f33c1eddbf85ca61f17182d634bcac84eda471daf918f352816a8531d677c` |
| `BEC-O-METRIC-DEFAULT-005` | `METRIC UNITS` | `E45` | `positive_phase_duration_metric_default` | `86d250933ff3f6225cb44759e8291ab6af98f4d7ed9864fea03868daac7e31dd` |
| `BEC-O-METRIC-DEFAULT-006` | `METRIC UNITS` | `E48` | `positive_phase_impulse_metric_default` | `d6b5226f38a6eebad7dd3762d19c8b90447c53081fe1d604d109f3757208f181` |
| `BEC-O-METRIC-DEFAULT-007` | `METRIC UNITS` | `E51` | `reflected_impulse_metric_default` | `701916857eb03ed760f1423f9d6f4b3f339632f1a20fe8acf43cebcd87d814ad` |
| `BEC-O-METRIC-DEFAULT-008` | `METRIC UNITS` | `E54` | `dynamic_overpressure_metric_default` | `565ee6db32ed7a6721f69f07b303020218da7353be1f3a593caa7a86e3355560` |
| `BEC-O-METRIC-DEFAULT-009` | `METRIC UNITS` | `E57` | `dynamic_impulse_metric_default` | `95b5a8c100ccda24a735d7cbdffb558a88c8f713d4e481d9639a0db54d8a1d68` |

Fail-closed requirement：后续 reviewer/tool 必须执行 retained workbook 或独立复核等价工具，对同一 selected cell set 生成 hash-only comparison outputs，并冻结 tolerance、rights / allowed-output policy 与 benchmark-consumption chain。当前 cached hash 不得作为 calibrated blast authority。

## 4. TP-21 Criteria Vocabulary

TP-21 sha256：`84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8`。

本 pass 只保留 controlled criteria vocabulary/hash，不抽取正文、不复制表格、不把 TP-21 presence 当 fragment calibration。允许 vocabulary keys：

| criteria key | status |
|---|---|
| `debris_item_class` | controlled key only |
| `debris_mass_bin` | controlled key only |
| `debris_velocity_or_throw_bin` | controlled key only |
| `standoff_or_separation_bin` | controlled key only |
| `target_exposure_or_area_bin` | controlled key only |
| `unit_system` | controlled key only |
| `applicability_limit` | controlled key only |
| `exclusion_reason` | controlled key only |

Fail-closed requirement：reviewer 必须选择具体 TP-21 debris comparison cases，单独记录 page/section provenance，并只把 hash-only selected outputs 带入本 package；不得把正文或表格内容复制成数据集。

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

## 6. Verification

```bash
python tools/maintenance/damage_model.py benchmark-evidence comparison-hashes --write-retained-artifacts
python -m pytest -q tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
```
