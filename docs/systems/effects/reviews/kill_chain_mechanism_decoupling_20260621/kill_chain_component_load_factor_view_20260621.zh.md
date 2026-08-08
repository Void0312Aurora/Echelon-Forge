# 逐部件 `effect_scale` 因子视图切片

日期：`2026-06-21`

状态：第五个诊断切片。本文记录 P1-b/P5/P4 边界：在不改默认杀伤参数的前提下，把每个
component load row 的 `effect_scale`、load-only facts、runtime response-owner rows 和
effects-event / runtime named load 因子分开对照，并增加一个诊断用 residual proxy。

## 目标

上一片已经把 effects-event 级别的 spatial、armor、exposure、threshold 和 vulnerability
因子放进摘要和 scalar ledger。但 `component_load.effect_scale` 本身是逐部件的：

- 同一发近炸下，不同部件的距离、投影、暴露和系统脆弱性不同。
- 如果只看 case 级 aggregate，就无法判断哪个 component row 贡献了最大 `effect_scale`，
  哪个 row 贡献了最大 failure probability。
- 后续若扩展 `ComponentLoadEvent` 合同，应先知道 per-component 字段需求，而不是直接
  调整全局近炸半径或总 `effect_scale`。

## 新增输出

每个 guidance / proximity case 现在新增：

- `component_load_factor_rows`
- `component_load_factor_summary`

整份 report 顶层也新增：

- `component_load_factor_summary`

每条 `component_load_factor_rows` 包含 load-side 诊断字段；同一 report 的
`runtime_facade.component_responses` 提供 response-owner 字段，可按 component identity
对照读取。

- component identity：`component_name`、`component_system`
- component load facts：`distance_m`、`effect_scale`
- case aggregate factors：`case_spatial_effect_scale`、
  `case_mechanism_armor_scale`、`case_mechanism_exposure_scale`、
  `case_mechanism_effect_scale`、`case_component_threshold_scale`、
  `case_vulnerability_effect_scale`
- diagnostic proxies：
  - `load_factor_product_proxy`
  - `response_factor_product_proxy`
  - `effect_scale_minus_load_factor_product_proxy`
  - `effect_scale_ratio_to_load_factor_product_proxy`
  - `effect_scale_ratio_to_case_spatial_effect_scale`

response-owner facts 通过 `runtime_facade.component_responses` 分离读取，包括
`failure_probability`、`failure_sample`、`integrity_before/after`。load row 上的 ABI
response 字段保持默认值，不作为响应权威；下表的 response-owner probability 是从
runtime facade response rows 对齐而来。

residual proxy 公式：

```text
effect_scale - spatial_effect_scale * mechanism_armor_scale * mechanism_exposure_scale
```

该 residual 只是诊断 proxy，用于判断 case-level aggregate factors 对 per-component
`effect_scale` 的解释程度。它不是物理模型，不是 calibration formula，也不释放调参权威。

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
- scalar ledger rows：`646`
- component factor rows：`33`
- rows with response fields on load row：`0`
- runtime component response rows：`33`
- 顶层 response-owner max component failure probability：`0.894245`
- 顶层 load-row `component_failure_probability_max`：`null`
- 顶层 max `effect_scale`：`0.828454`
- 顶层 mean abs residual proxy：`0.148861`
- 顶层 max abs residual proxy：`0.486667`

## 8 km / 30 度逐部件结果

左侧 `aim120_8km_left_30deg`：

| component | system | effect_scale | response-owner failure probability | load-factor proxy | residual | ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `left_aileron_actuator` | `flight_control` | `0.069446` | `0.006350` | `0.041755` | `0.027690` | `1.663159` |
| `left_wing_fuel_cell` | `fuel` | `0.060000` | `0.006038` | `0.041755` | `0.018245` | `1.436945` |
| `left_horizontal_tail_actuator_or_surface_component` | `flight_control` | `0.117271` | `0.005710` | `0.041755` | `0.075516` | `2.808543` |

右侧 `aim120_8km_right_30deg`：

| component | system | effect_scale | response-owner failure probability | load-factor proxy | residual | ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `right_aileron_actuator` | `flight_control` | `0.069551` | `0.006356` | `0.041789` | `0.027762` | `1.664354` |
| `right_wing_fuel_cell` | `fuel` | `0.060000` | `0.006042` | `0.041789` | `0.018211` | `1.435800` |
| `right_horizontal_tail_actuator_or_surface_component` | `flight_control` | `0.117504` | `0.005685` | `0.041789` | `0.075715` | `2.811859` |
| `electrical_power_bus` | `avionics` | `0.060000` | `0.005036` | `0.041789` | `0.018211` | `1.435800` |

观察：

- 最大 `effect_scale` 和最大 residual 都落在 horizontal-tail actuator/surface component。
- 最大 response-owner failure probability 却落在 aileron actuator。
- 这说明 `effect_scale` 最大的部件并不必然给出最大 response-owner probability；
  response 层还有 component threshold、系统脆弱性、failure mode 等因素。
- 8 km / 30 度的弱杀伤不能通过“把某一个总标量调大”来干净解释。

## 下一步

P5 response owner 字段边界已补充为
[kill_chain_component_response_boundary_20260621.zh.md](kill_chain_component_response_boundary_20260621.zh.md)。
当前建议：

1. P4 named load factors 已进入 runtime DTO / event surface；继续把下游消费者从复合
   `component_load.effect_scale` 迁移到命名因子。
2. 保留 `response_fields=[]` / `rows_with_response_fields_on_load_row=0` 作为 P5 守卫。
3. 只在 P6 engineering-proxy admission 的单层 guarded calibration 约束下调整
   proximity lethality 参数，并用 delta guard 防止跨层泄漏。

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
