# 杀伤链期望 Harness 初始实现

状态：`2026-07-15` initial executable before-report harness，加上只读 diagnostic
postprocessors，用于 [杀伤链期望标准化](README.zh.md) 的 future harness
implementation 起点。

英文规范页：
[kill_chain_harness_implementation_20260623.md](kill_chain_harness_implementation_20260623.md)

## 实现入口

工具：

```bash
python tools/diagnostics/kill_chain_expectation_harness.py --help
```

新增测试：

```bash
python -m pytest tests/tools/test_kill_chain_expectation_harness.py -q
python -m pytest tests/tools/test_kces_expectation_envelope_audit.py -q
```

当前 schema：

| Artifact | Schema |
| --- | --- |
| before report | `a2.kill_chain_expectation_before_report.v1` |
| case grid rows | `a2.kill_chain_expectation_case_grid.v1` |
| heatmap rows | `a2.kill_chain_expectation_heatmap_row.v1` |
| component detail | `a2.kill_chain_expectation_component_detail.v1` |
| visualization manifest | `a2.kill_chain_expectation_visualization_manifest.v1` |
| first-review-stage attribution | `a2.kill_chain_expectation_stage_attribution.v1` |
| response local diagnosis | `a2.kill_chain_expectation_response_diagnosis.v2` |
| expectation-envelope audit | `a2.kill_chain_expectation_envelope_audit.v1` |

## 已实现内容

- 生成 P2 `anchor-grid` case grid。
- `nonmaneuvering_constant_velocity` 匀速目标 runtime case 当前可执行，共 `78`
  signed anchor cases。
- `mild_maneuver` sparse grid 可登记为 grid rows，共 `15` signed cases，但当前
  runtime 执行层仍标为 unsupported，避免伪装成已运行机动目标。
- 调用既有
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)
  生成只读 runtime facts。
- 将每个 runtime case 投影为 P3/P4 heatmap report row 字段组：
  `identity`、`launch_window`、`guidance_approach`、`fuze_decision`、
  `warhead_load_field`、`component_response`、`consequence_projection` 和
  `guards`。
- 在每个 heatmap row 下保留 `component_detail`，但配对逻辑由共享
  `component_detail_projection.py` 从既有 runtime facade 只读投影而来；KCES
  harness 不重新维护部件配对、杀伤归因或 response 规则。
- `R_effect_variant` 作为离线评价维度展开，不乘进 simulation case 数。
- 默认展开 `REV-RUNTIME-PROJECTION`、`REV-EQ-FUZE` 和 `REV-SMALLER-LOAD`。
  若未提供 `--declared-effect-radius-m`，`REV-SMALLER-LOAD` 输出
  `unclassified_missing_R_effect`，不伪造米制半径。
- CLI stdout 保持纯 JSON；native runtime 日志转到 stderr。
- 通过 `tools.diagnostics.kces.envelope_audit` 把 standards-layer v0 期望包络作为
  只读后处理器应用到既有 before report；base harness 尚未内联输出 envelope 字段。

## Smoke 结果

命令：

```bash
python tools/diagnostics/kill_chain_expectation_harness.py \
  --case-id kces_anchor_grid_cv_8km_p30deg \
  --effect-variants REV-RUNTIME-PROJECTION,REV-EQ-FUZE,REV-SMALLER-LOAD
```

关键结果：

| Field | Value |
| --- | --- |
| `case_count` | `1` |
| `heatmap_row_count` | `3` |
| `launch_class` | `N` |
| `nearest_distance_m` | `10.963479375176643` |
| `R_fuze_m` | `15.0` |
| `rho_fuze` | `0.7308986250117762` |
| `entered_R_fuze` | `true` |
| `guidance_expectation_status` | `satisfied` |
| `REV-RUNTIME-PROJECTION.R_effect_m` | `9.0` |
| `REV-RUNTIME-PROJECTION.R_effect_source` | `missile_runtime_projection.resolved_projection_radius_m` |
| `REV-RUNTIME-PROJECTION.rho_effect_case` | `1.218164375019627` |
| `REV-RUNTIME-PROJECTION.effect_band` | `outside_effect` |
| `REV-EQ-FUZE.effect_band` | `outer_effective` |
| `REV-SMALLER-LOAD.effect_band` | `unclassified_missing_R_effect` |
| `max_failure_probability` | `0.0063555841366786684` |
| `component_response_band` | `observed_probability_only` |
| `authority_boundary_status` | `engineering_proxy_guarded` |

解释：

- 该 smoke case 当前进入 `R_fuze`，因此不是“完全没有接近 / 没有引信事实”的失败。
- `REV-RUNTIME-PROJECTION` 使用发射时 runtime 空间投影半径：
  `15 m * 0.60 = 9 m`。因此该 case 属于 `outside_effect`；`REV-EQ-FUZE`
  则仍是独立的 15 m sensitivity row，属于 `outer_effective`。
- 当前 `outside_effect` negative-control 允许低概率 component response；该观测
  不再构成 component-response 校准压力。

## 匀速 Anchor Before Report

已生成完整 `nonmaneuvering_constant_velocity` anchor-grid before report：

```text
docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json
```

摘要：

| Field | Value |
| --- | --- |
| `case_count` | `78` |
| `heatmap_row_count` | `234` |
| `launch_class_counts` | `N=19`, `M=25`, `O=34` |
| runtime-row `N` satisfied | `19` |
| runtime-row `N` guidance residual | `0` |
| runtime-row `M` observed marginal | `25` |
| runtime-row `O` negative-control satisfied | `34` |
| authority boundary | `engineering_proxy_guarded` for all rows |

发射窗口校准 rows：

| case_id | launch_class | nearest_distance_m | rho_fuze |
| --- | --- | ---: | ---: |
| `kces_anchor_grid_cv_4km_m45deg` | `M` | `22.438232265927198` | `1.4958821510618132` |
| `kces_anchor_grid_cv_4km_p45deg` | `M` | `22.4382609956996` | `1.4958840663799733` |
| `kces_anchor_grid_cv_6km_m45deg` | `M` | `22.10101051253856` | `1.473400700835904` |
| `kces_anchor_grid_cv_6km_p45deg` | `M` | `22.101032317828015` | `1.4734021545218676` |

`8 km / 30 deg` anchor：

| case_id | nearest_distance_m | rho_fuze | `REV-RUNTIME-PROJECTION.effect_band` | max_failure_probability |
| --- | ---: | ---: | --- | ---: |
| `kces_anchor_grid_cv_8km_m30deg` | `10.963446301013404` | `0.7308964200675603` | `outside_effect` | `0.006350331908151525` |
| `kces_anchor_grid_cv_8km_p30deg` | `10.963479375176643` | `0.7308986250117762` | `outside_effect` | `0.0063555841366786684` |

解释：

- 当前匀速 anchor-grid 的 `O` negative controls 全部没有触发异常下游校准压力。
- runtime 主网格与局部加密把 `4..8 km` 的 `15 m` 进入边界定位在约
  `36..38 deg`。冻结 `35 g`、`N=4`、`APN=0.5` 代理后，`4/6 km +/-45 deg`
  应归为 marginal；若强制 nominal，单参数扫掠需要约 `N=10..12` 或 `50 g`。
- `8 km / 30 deg` 进入 `R_fuze`，但最近距超过修正后的 9 m runtime projection
  radius；其 trace response 因而属于满足要求的 outside-effect 观测，不是 load /
  response residual。

## 匀速 Anchor 可视化

已从 before report 生成 reviewable heatmap 矩阵。该步骤只读取 JSON，不重跑仿真、
不修改参数，也不声明真实 weapon / target / Pk authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_visualize.py \
  --input docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

产物入口：

| Artifact | Path |
| --- | --- |
| manifest | [kces_anchor_cv_visualization_manifest_20260623.json](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_manifest_20260623.json) |
| summary | [kces_anchor_cv_visualization_summary_20260623.md](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md) |
| launch class heatmap | [kces_anchor_cv_launch_class_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.csv) |
| guidance status heatmap | [kces_anchor_cv_guidance_status_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.csv) |
| `rho_fuze` heatmap | [kces_anchor_cv_rho_fuze_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.csv) |
| max failure probability heatmap | [kces_anchor_cv_max_failure_probability_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.csv) |
| effect band heatmap | [kces_anchor_cv_effect_band_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.csv) |

图上直接可见：

- `8 km / +/-30 deg` 在 guidance status 图中为 `sat`，不是当前主要制导 residual。
- `8 km / +/-30 deg` 在 max failure probability 图中为约 `0.006` 的低响应点，
  但它也位于修正后的 9 m runtime projection radius 外，因此在
  `REV-RUNTIME-PROJECTION` 下仍是满足要求的 negative-control 观测。
- `4/6 km +/-45 deg` 现在在图中为 `marg`，与实测近距方位边界一致，且未修改
  runtime 制导参数。

## 首阶段复核归因

已从同一 before report 生成 first-review-stage triage artifact。该报告回答“每个
heatmap cell 首先应复核哪一层”，不是校准 verdict，也不使用真实武器 / 目标 authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_stage_attribution.py \
  --input docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

产物入口：

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_first_review_stage_summary_20260623.md](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md) |
| manifest | [kces_anchor_cv_first_review_stage_manifest_20260623.json](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_manifest_20260623.json) |
| stage heatmap | [kces_anchor_cv_first_review_stage_heatmap_20260623.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_heatmap_20260623.png) / [csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_matrix_20260623.csv) |
| detail CSV | [kces_anchor_cv_first_review_stage_detail_20260623.csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_detail_20260623.csv) |

当前归因计数：

| First review stage | Count | Meaning |
| --- | ---: | --- |
| `no_review_pressure` | `19` | `N` cell 已达到圈内响应下限，或只在 9 m runtime projection radius 外保留 trace response。 |
| `marginal_observation` | `25` | `M` cell 只保留观测，不按失败处理。 |
| `negative_control_satisfied` | `34` | `O` cell 安静，negative control 通过。 |

这使当前后续工作分叉更清楚：

- 修正 launch-window 后，anchor grid 已无 nominal guidance residual。
- `4/6/8 km +/-30 deg` 位于修正后的 9 m runtime projection radius 外；其 trace
  response 在 `REV-RUNTIME-PROJECTION` 下不产生复核压力。
- 没有 `negative_control_alert`，说明本轮 O 类单元没有给出异常校准压力。

## Component Response 局部诊断

report-level local diagnosis 仍作为后处理器保留。修正 runtime projection 后，
`REV-RUNTIME-PROJECTION` 下没有选出 `component_response` candidates。该诊断仍只读取
before report，不重跑仿真、不编辑参数、不声明真实 weapon / target / Pk authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_response_diagnosis.py \
  --input docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260628
```

产物入口：

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_response_diagnosis_summary_20260628.md](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md) |
| manifest | [kces_anchor_cv_response_diagnosis_manifest_20260628.json](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_manifest_20260628.json) |
| detail CSV | [kces_anchor_cv_response_diagnosis_detail_20260628.csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_detail_20260628.csv) |
| matrix CSV | [kces_anchor_cv_response_diagnosis_matrix_20260628.csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_matrix_20260628.csv) |
| probability scatter | [kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png) / [svg](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.svg) |

当前诊断：

| Field | Value |
| --- | ---: |
| candidate rows | `0` |
| baseline rows | `13` |
| diagnosis buckets | `{}` |

解释：

- `REV-RUNTIME-PROJECTION` 下当前没有 row 归因到 `component_response`，因此本
  artifact 不再声明局部 load / response residual。
- `18` 个 `core/effective` rows 全部满足响应下限，其中 `14` 个为
  `severe_response`、`4` 个为 `material_response`；`10` 个 outside-effect trace rows
  保持 `p_max<=0.008658`、`delta_abs<=0.006434`，且没有 sampled failure。
- 仍可通过 `REV-EQ-FUZE` 把相同 rows 作为显式 radius-policy sensitivity 观察，
  但不得把该结果表述成当前 runtime projection。

## 期望包络审计

同一 before report 也已按 standards-layer v0 期望包络完成审计。该步骤仍是只读
后处理器，不重跑仿真、不编辑参数，也不授予 calibration authority。

生成工具：

```bash
python -m tools.diagnostics.kces.envelope_audit \
  --input docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260706
```

产物入口：

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_expectation_envelope_summary_20260706.md](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md) |
| manifest | [kces_anchor_cv_expectation_envelope_manifest_20260706.json](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_manifest_20260706.json) |
| detail CSV | [kces_anchor_cv_expectation_envelope_detail_20260706.csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_detail_20260706.csv) |
| matrix CSV | [kces_anchor_cv_expectation_envelope_matrix_20260706.csv](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_matrix_20260706.csv) |

当前 envelope status 计数：

| Envelope cell status | Count | Reading |
| --- | ---: | --- |
| `boundary_observation` | `25` | 全部 marginal launch-window cells 继续作为观测保留。 |
| `satisfied` | `53` | nominal 与 negative-control cells 未产生包络压力。 |

Owner-stage 计数：

| Owner stage | Count |
| --- | ---: |
| `launch_window` | `25` |
| `negative_control_satisfied` | `34` |
| `no_review_pressure` | `19` |

## 边界

本切片不做：

- runtime 参数修改；
- descriptor 修改；
- after report；
- delta guard 对比；
- 完整 `93` anchor-grid 或 `572` recommended-main-grid 运行；
- `mild_maneuver` 的 `15` 个 anchor cases 尚未执行，因此完整 `93` anchor-grid
  仍未完成；
- 并行 worker 调度；
- 机动目标 runtime 支持；
- runtime-contract standards promotion；
- 真实 AIM-120C / F-16C / deterministic fuze / Pk authority。

## 后续

下一步建议：

1. 保持已校准的 `4/6 km x 45 deg = M` 边界；除非独立 runtime-retuning 任务提供
   新证据，否则冻结当前制导代理。
2. 把 `REV-EQ-FUZE` 保持为离线 radius sensitivity，并确保
   `REV-RUNTIME-PROJECTION` 只读取发射时 runtime projection 快照。
3. 再实现 worker 并行与失败 case retry。
4. 补齐 `mild_maneuver` runtime 支持，使完整 `93` anchor-grid 不再含 unsupported rows。
5. 在 anchor-grid 解释稳定后，再进入 `recommended-main-grid` pilot。
