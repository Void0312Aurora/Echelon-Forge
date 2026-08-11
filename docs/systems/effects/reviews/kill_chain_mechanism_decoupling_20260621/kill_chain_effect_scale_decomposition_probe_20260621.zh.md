# `effect_scale` 拆分观测切片

日期：`2026-06-21`

状态：第四个诊断切片，后续 P4 runtime 合同扩展已落地。本文最初记录 P1 方向的推进：
先把现有 effects event 中已经存在的细粒度因子暴露到 probe 摘要和 scalar ledger，
作为拆 `component_load.effect_scale` 的机器可读入口；当前版本已进一步把 component
load named factors 暴露到 runtime DTO / event surface，不改默认杀伤参数。

## 背景

上一片标量账本已经区分了两类问题：

- `component_load.component_failure_probability` 曾属于 owner 泄漏；当前 P5 已把有效
  probability 迁到 `component_response` runtime rows，load row 只保留默认 ABI 字段。
- `component_load.effect_scale` 属于复合消费过宽：它现在仍归 `warhead_load_field`，
  但被 response / consequence 等下游共同消费。

因此 P1/P4 不应该简单移动 `effect_scale` 字段，而应该先拆出它背后的因子。当前 runtime
里这些因子已经存在于 `EffectsResult` / `EffectsEvent`，并投影到
`ComponentLoadEvent` / `KillChainComponentLoadFact`：

- spatial intersection / sampling：`warhead_spatial_hit_estimate`、
  `warhead_spatial_hit_fraction`、`warhead_spatial_energy_scale`、
  `warhead_spatial_pattern_scale`、`warhead_orientation_pattern_scale`
- mechanism/load factor：`mechanism_armor_scale`、`mechanism_exposure_scale`、
  `mechanism_effect_scale`
- response susceptibility：`component_threshold_scale`
- vulnerability response factor：`vulnerability_family_scale`、
  `vulnerability_aspect_scale`、`vulnerability_closure_scale`、
  `vulnerability_miss_distance_scale`、`vulnerability_effect_scale`

本切片把它们纳入诊断输出、账本和 runtime named-factor surface，不改变实际杀伤计算。

## 实现

`tools/diagnostics/kill_chain_decoupling_probe.py` 的 `effect` 摘要新增：

- `mechanism_armor_scale`
- `mechanism_exposure_scale`
- `component_threshold_scale`
- `warhead_spatial_hit_estimate`
- `warhead_spatial_hit_fraction`
- `warhead_spatial_energy_scale`
- `warhead_spatial_pattern_scale`
- `warhead_orientation_pattern_scale`
- `vulnerability_family_scale`
- `vulnerability_aspect_scale`
- `vulnerability_closure_scale`
- `vulnerability_miss_distance_scale`
- `vulnerability_effect_scale`

`tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_scalar_ledger.py`
新增这些 scalar id：

- `effects_event.warhead_spatial_hit_estimate`
- `effects_event.warhead_spatial_hit_fraction`
- `effects_event.warhead_spatial_energy_scale`
- `effects_event.warhead_spatial_pattern_scale`
- `effects_event.warhead_orientation_pattern_scale`
- `effects_event.mechanism_armor_scale`
- `effects_event.mechanism_exposure_scale`
- `effects_event.component_threshold_scale`
- `effects_event.vulnerability_family_scale`
- `effects_event.vulnerability_aspect_scale`
- `effects_event.vulnerability_closure_scale`
- `effects_event.vulnerability_miss_distance_scale`
- `effects_event.vulnerability_effect_scale`

新增 flag：

| flag | 含义 |
| --- | --- |
| `effect_scale_decomposition_factor_available` | 已有可用于拆解 `effect_scale` 的 spatial / armor / exposure / pattern 因子 |
| `component_load_named_factor_available` | runtime component load row 已暴露 spatial / pattern / exposure / armor / sampling / load intensity 命名因子 |
| `component_threshold_response_factor_aggregated_in_effects_event` | response 层阈值/脆弱性因子仍聚合在 effects event |
| `vulnerability_response_factor_aggregated_in_effects_event` | vulnerability response 因子仍聚合在 effects event |

## 刷新后的 baseline

命令：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --mode all \
  --seed 20260621 \
  --output docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json
```

刷新后 artifact：

- 文件大小 `1186180` bytes
- guidance cases：`4`
- proximity cases：`7`
- scalar ledger rows：`646`
- component factor rows：`33`
- calibration-ready scalar rows：`246`
- cross-owner scalar ids：`24`

顶层新增/关键 flag：

| flag | count |
| --- | ---: |
| `effect_scale_decomposition_factor_available` | `77` |
| `component_load_named_factor_available` | `63` |
| `vulnerability_response_factor_aggregated_in_effects_event` | `55` |
| `component_threshold_response_factor_aggregated_in_effects_event` | `11` |
| `composite_effect_scale_crosses_stage_boundary` | `9` |

## 8 km / 30 度观测

| case | miss distance | max component failure probability | spatial scale | armor | exposure | mechanism scale | threshold scale | vulnerability scale |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `aim120_8km_left_30deg` | `10.963446 m` | `0.006350` | `0.129719` | `0.626108` | `0.514112` | `0.573004` | `1.815000` | `0.800000` |
| `aim120_8km_right_30deg` | `10.963479 m` | `0.006356` | `0.129839` | `0.626066` | `0.514081` | `0.676873` | `1.815000` | `0.800000` |

这说明 8 km / 30 度的弱杀伤现在至少可以拆成几类可观察因素：

- spatial scale 已低到约 `0.13`；
- armor / exposure 继续压低机制作用；
- `component_threshold_scale` 约 `1.815`，说明 response 层门槛也在抬高；
- vulnerability aggregate scale 为 `0.8`，仍然是 response/consequence 边界上的聚合因子；
- 最终 max component failure probability 仍约 `0.00635`。

这不是说这些数都“不合理”，而是说明后续校准要先决定每个因子的物理语义和 owner。
如果直接调高总 `effect_scale` 或总杀伤半径，会继续把 spatial、armor、exposure、
threshold 和 vulnerability 混在一起。

## 后续建议

P1-b 已补充为
[kill_chain_component_load_factor_view_20260621.zh.md](kill_chain_component_load_factor_view_20260621.zh.md)。
后续可以继续：

1. 给每个 component row 标注 `load_only_fields` 与 `response_fields`。
2. 单独列出 `component_load.component_failure_probability` 与
   `component_response.failure_probability` 的重复/回收关系。
3. P4 runtime named factors 已进入 `ComponentLoadEvent` / `KillChainComponentLoadFact`；
   后续重点转为下游消费者从复合 `effect_scale` 迁移到命名因子。

当前仍不建议无边界地直接重调近炸杀伤数值；P6 已允许 engineering-proxy scope
下的单层 guarded calibration，但每次必须用 stage report 和 delta guard 证明没有跨层泄漏。

## 验证

命令：

```bash
python -m pytest \
  tests/tools/test_kill_chain_decoupling_probe.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  -q
```

结果：`36 passed`。
