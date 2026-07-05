# 杀伤链期望 Harness 初始实现

状态：`2026-06-23` initial executable before-report harness，用于
[杀伤链期望标准化](README.zh.md) 的 future harness implementation 起点。

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
| `REV-RUNTIME-PROJECTION.effect_band` | `outer_effective` |
| `REV-EQ-FUZE.effect_band` | `outer_effective` |
| `REV-SMALLER-LOAD.effect_band` | `unclassified_missing_R_effect` |
| `max_failure_probability` | `0.0063555841366786684` |
| `component_response_band` | `observed_probability_only` |
| `authority_boundary_status` | `engineering_proxy_guarded` |

解释：

- 该 smoke case 当前进入 `R_fuze`，因此不是“完全没有接近 / 没有引信事实”的失败。
- 在 `REV-RUNTIME-PROJECTION` 与 `REV-EQ-FUZE` 下，case-level
  `rho_effect_case` 落在 `outer_effective`；这只是报告分区，不是概率阈值或真实战斗部声明。
- component response 仍显示为低概率观测；该结果支持后续 before heatmap 的
  first-failed-stage 分析，但还不是校准结论。

## 匀速 Anchor Before Report

已生成完整 `nonmaneuvering_constant_velocity` anchor-grid before report：

```text
docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json
```

摘要：

| Field | Value |
| --- | --- |
| `case_count` | `78` |
| `heatmap_row_count` | `234` |
| `launch_class_counts` | `N=23`, `M=21`, `O=34` |
| runtime-row `N` satisfied | `19` |
| runtime-row `N` guidance residual | `4` |
| runtime-row `M` observed marginal | `21` |
| runtime-row `O` negative-control satisfied | `34` |
| authority boundary | `engineering_proxy_guarded` for all rows |

`N` 类 residual cases：

| case_id | range_km | signed_bearing_deg | nearest_distance_m | rho_fuze |
| --- | ---: | ---: | ---: | ---: |
| `kces_anchor_grid_cv_4km_m45deg` | `4` | `-45` | `22.438232265927198` | `1.4958821510618132` |
| `kces_anchor_grid_cv_4km_p45deg` | `4` | `45` | `22.4382609956996` | `1.4958840663799733` |
| `kces_anchor_grid_cv_6km_m45deg` | `6` | `-45` | `22.10101051253856` | `1.473400700835904` |
| `kces_anchor_grid_cv_6km_p45deg` | `6` | `45` | `22.101032317828015` | `1.4734021545218676` |

`8 km / 30 deg` anchor：

| case_id | nearest_distance_m | rho_fuze | `REV-RUNTIME-PROJECTION.effect_band` | max_failure_probability |
| --- | ---: | ---: | --- | ---: |
| `kces_anchor_grid_cv_8km_m30deg` | `10.963446301013404` | `0.7308964200675603` | `outer_effective` | `0.006350331908151525` |
| `kces_anchor_grid_cv_8km_p30deg` | `10.963479375176643` | `0.7308986250117762` | `outer_effective` | `0.0063555841366786684` |

解释：

- 当前匀速 anchor-grid 的 `O` negative controls 全部没有触发异常下游校准压力。
- 主要制导 / 发射窗口错位不在 `8 km / 30 deg`，而在 `4 km / 45 deg`
  和 `6 km / 45 deg` 这四个 `N` cells。
- `8 km / 30 deg` 当前进入 `R_fuze`，但 response 仍低；后续应把它归入
  `warhead_load_field -> component_response` 解释链，而不是继续描述成没有制导接近事实。

## 匀速 Anchor 可视化

已从 before report 生成 reviewable heatmap 矩阵。该步骤只读取 JSON，不重跑仿真、
不修改参数，也不声明真实 weapon / target / Pk authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_visualize.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

产物入口：

| Artifact | Path |
| --- | --- |
| manifest | [kces_anchor_cv_visualization_manifest_20260623.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_manifest_20260623.json) |
| summary | [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md) |
| launch class heatmap | [kces_anchor_cv_launch_class_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.csv) |
| guidance status heatmap | [kces_anchor_cv_guidance_status_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.csv) |
| `rho_fuze` heatmap | [kces_anchor_cv_rho_fuze_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.csv) |
| max failure probability heatmap | [kces_anchor_cv_max_failure_probability_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.csv) |
| effect band heatmap | [kces_anchor_cv_effect_band_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.csv) |

图上直接可见：

- `8 km / +/-30 deg` 在 guidance status 图中为 `sat`，不是当前主要制导 residual。
- `8 km / +/-30 deg` 在 max failure probability 图中为约 `0.006` 的低响应点，
  因此后续分析对象应是 `warhead_load_field -> component_response`。
- 四个 `N` residual cell 集中在 `4/6 km` 的 `+/-45 deg`，需要后续复核 P2
  launch-window class 或当前制导模型。

## 首阶段复核归因

已从同一 before report 生成 first-review-stage triage artifact。该报告回答“每个
heatmap cell 首先应复核哪一层”，不是校准 verdict，也不使用真实武器 / 目标 authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_stage_attribution.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

产物入口：

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md) |
| manifest | [kces_anchor_cv_first_review_stage_manifest_20260623.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_manifest_20260623.json) |
| stage heatmap | [kces_anchor_cv_first_review_stage_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_matrix_20260623.csv) |
| detail CSV | [kces_anchor_cv_first_review_stage_detail_20260623.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_detail_20260623.csv) |

当前归因计数：

| First review stage | Count | Meaning |
| --- | ---: | --- |
| `guidance_approach` | `4` | `N` cell 未进入 `R_fuze`，先复核发射窗口 / 制导模型。 |
| `component_response` | `6` | `N` cell 已有 guidance / fuze / load facts，但 response 未采样到 failure。 |
| `no_review_pressure` | `13` | `N` cell 已进入引信、触发、载荷和 sampled response。 |
| `marginal_observation` | `21` | `M` cell 只保留观测，不按失败处理。 |
| `negative_control_satisfied` | `34` | `O` cell 安静，negative control 通过。 |

这使当前后续工作分叉更清楚：

- `4/6 km +/-45 deg` 进入 `guidance_approach` high-priority 复核。
- `4/6/8 km +/-30 deg` 进入 `component_response` medium-priority 复核，其中包含
  用户最初关注的 `8 km / 30 deg`。
- 没有 `negative_control_alert`，说明本轮 O 类单元没有给出异常校准压力。

## Component Response 局部诊断

已对首阶段归因为 `component_response` 的六个 cells 生成 report-level local diagnosis。
该诊断仍只读取 before report，不重跑仿真、不编辑参数、不声明真实 weapon / target /
Pk authority。

生成工具：

```bash
python tools/diagnostics/kill_chain_expectation_response_diagnosis.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260628
```

产物入口：

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md) |
| manifest | [kces_anchor_cv_response_diagnosis_manifest_20260628.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_manifest_20260628.json) |
| detail CSV | [kces_anchor_cv_response_diagnosis_detail_20260628.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_detail_20260628.csv) |
| matrix CSV | [kces_anchor_cv_response_diagnosis_matrix_20260628.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_matrix_20260628.csv) |
| probability scatter | [kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png) / [svg](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.svg) |

当前诊断：

| Diagnosis bucket | Count | Reading |
| --- | ---: | --- |
| `outer_effect_low_component_load_probability_cliff` | `6` | case-level `outer_effective` band 映射到较弱 component load scale 和极低 response probability。 |

逐部件 projection signal：

| Detail projection signal | Count | Reading |
| --- | ---: | --- |
| `all_component_rows_weak_load_low_response` | `6` | before report 中保留的逐部件 rows 全部同时表现为弱 load scale 和低 response probability。 |

`8 km / +30 deg` 的保留细节：

| Detail | Value |
| --- | --- |
| component detail rows | `4` |
| strongest load component | `right_horizontal_tail_actuator_or_surface_component` / `flight_control` |
| strongest load `effect_scale` | `0.11750353538707678` |
| strongest load `rho_effect_component` | `0.40311860731986976` |
| max-probability component | `right_aileron_actuator` / `flight_control` |
| max component `failure_probability` | `0.0063555841366786684` |
| max component `effect_scale` | `0.06955096109949216` |
| sampled failure | `false` |

对照同距离、同侧 `15 deg` sampled-response 基线后：

- `4 km +/-30 deg` 的 max failure probability 约为 `15 deg` 基线的 `0.98%`，
  strongest component load scale 约为基线的 `17.6%`。
- `6 km +/-30 deg` 的 max failure probability 约为 `15 deg` 基线的 `0.83%`，
  strongest component load scale 约为基线的 `14.4%`。
- `8 km +/-30 deg` 的 max failure probability 约为 `15 deg` 基线的 `0.72%`，
  strongest component load scale 约为基线的 `12.8%`。

解释：

- 六个 cells 都已有 guidance / fuze / case-level load facts，因此不应回退为制导失败。
- 当前低响应更像 case-level `outer_effective` 到 component-level load / response
  的概率断崖，而不是单纯随机采样未命中。
- 当前 before report 通过共享投影保留逐部件 `component_loads[]` 和
  `component_responses[]` 细节；下一步只需继续拆这些既有字段里的低响应原因：
  warhead spatial projection、target receiver exposure / armor / threshold 或
  response curve。

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
- standards promotion；
- 真实 AIM-120C / F-16C / deterministic fuze / Pk authority。

## 后续

下一步建议：

1. 基于共享投影输出中的逐部件 `component_loads[]` / `component_responses[]`
   细节，继续拆分 response cliff 的原因：warhead spatial projection、
   receiver exposure / armor / threshold，或 response curve。
2. 对 `guidance_approach` 四个 cells 复核 P2 launch-window class 与当前制导模型。
3. 再实现 worker 并行与失败 case retry。
4. 补齐 `mild_maneuver` runtime 支持，使完整 `93` anchor-grid 不再含 unsupported rows。
5. 在 anchor-grid 解释稳定后，再进入 `recommended-main-grid` pilot。
