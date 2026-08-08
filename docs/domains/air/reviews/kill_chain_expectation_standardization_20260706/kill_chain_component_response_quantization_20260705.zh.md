# 组件响应量化阈值附录

状态：`2026-07-15` post-P5 task-local docs-only threshold addendum，已按修正后的
runtime 空间投影半径刷新。本文补齐
[杀伤链指标映射](kill_chain_metric_mapping_20260623.zh.md) 中保留的
`component_response` 概率 / 完整度阈值空缺。本文不执行校准，不修改 runtime
参数，不编辑 descriptor，不声明真实 AIM-120C / F-16C / Pk 或确定性引信权威。

英文规范页：
[kill_chain_component_response_quantization_20260705.md](kill_chain_component_response_quantization_20260705.md)

Schema label：`a2.kill_chain_component_response_quantization.v0`

## 输入边界

本附录只消费 KCES before/after report 中已经存在或可由既有字段派生的
`component_response` 字段：

- `component_response_row_count`
- `max_failure_probability`
- `sampled_failure_count`
- `min_integrity_delta`
- `primary_failure_mode`
- `component_response_band`
- `component_detail.component_rows[].failure_probability`
- `component_detail.component_rows[].integrity_delta`
- `component_detail.component_rows[].sampled_failure`

派生字段：

```text
p_max = component_response.max_failure_probability
delta_abs = max(0, -component_response.min_integrity_delta)
n_sampled = component_response.sampled_failure_count
n_rows = component_response.component_response_row_count
```

`n_sampled` 是单次 seed 的观察结果，不是阈值本体。量化分区优先使用
`p_max` 和 `delta_abs`；`n_sampled > 0` 只作为 `sampled_failure_observed`
标记附加到分区结果。

## 量化分区

| band | 条件 | 解释 |
| --- | --- | --- |
| `no_component_response` | `n_rows = 0` | 没有可评价组件响应行。 |
| `trace_response` | `n_rows > 0` 且 `p_max < 0.02` 且 `delta_abs < 0.02` | 只有概率痕迹和极小完整度变化；不能满足有效载荷后的非平凡响应期望。 |
| `weak_response` | `0.02 <= p_max < 0.10` 或 `0.02 <= delta_abs < 0.05` | 可见但弱的组件响应；通常只支持边缘解释。 |
| `nontrivial_response` | `0.10 <= p_max < 0.30` 或 `0.05 <= delta_abs < 0.15` | 非平凡组件响应；可支撑 `outer_effective` 下限或 `effective` 的弱端解释。 |
| `material_response` | `0.30 <= p_max < 0.70` 或 `0.15 <= delta_abs < 0.35` | 显著组件响应；适合 `effective` 或强几何下的 `outer_effective`。 |
| `severe_response` | `p_max >= 0.70` 或 `delta_abs >= 0.35` | 强组件响应；不等价于 mission kill / Pk，只说明组件层响应强。 |

若多个条件同时成立，取表中靠后的最高强度 band。`sampled_failure_observed`
是正交标志：

```text
sampled_failure_observed = n_sampled > 0
```

因此 `material_response + sampled_failure_observed=false` 和
`material_response + sampled_failure_observed=true` 都是合法报告状态；前者表示概率 /
完整度阈值已显著，但该 seed 未采样到失败。

## 与 effect band 的复核压力映射

这些阈值不是校准目标值；它们给 `warhead_load_field.effect_band` 与
`component_response` 之间建立复核压力：

| `effect_band` | 期望下限 | 低于下限的处理 |
| --- | --- | --- |
| `core` | `material_response` | `trace_response` / `weak_response` 必须进入 factor decomposition；不得直接调 fuze 或 guidance。 |
| `effective` | `nontrivial_response` | `trace_response` 需要解释为 warhead load、receiver exposure / armor / threshold 或 response curve 问题。 |
| `outer_effective` | `weak_response` | `trace_response` 是 review pressure，不是自动校准授权；必须保留逐部件载荷 / 响应证据。 |
| `edge` | `trace_response` | 弱或痕迹响应可接受；若出现 `material_response` 以上，需检查几何或载荷异常。 |
| `outside_effect` | `no_component_response` 或 `trace_response` | 若出现 `nontrivial_response` 以上，记为 negative-control pressure。 |
| `unclassified_missing_R_effect` | 不判定 | 先声明 `R_effect_m` 或具体 `R_effect_variant`。 |

## 当前 before-report 对照

使用 `REV-RUNTIME-PROJECTION` 的匀速 anchor before report：

[kces_anchor_cv_before_report_20260623.json](review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json)

当前分布可按本附录解释为：

| `effect_band` | count | 量化响应分布 | 本附录解释 |
| --- | ---: | --- | --- |
| `core` | 6 | `severe_response=6` | 符合强载荷区期望。 |
| `effective` | 12 | `severe_response=8`、`material_response=4` | 达到有效区下限。 |
| `outside_effect` | 60 | `trace_response=10`、`no_component_response=50` | 满足包线外 negative-control 上限。 |

`REV-RUNTIME-PROJECTION` 现在读取发射时 runtime projection 快照：
`lethal_radius_m=15`、`projection_radius_fraction=0.60`，解析后的
`resolved_projection_radius_m=9`。因此 `4/6/8 km +/-30 deg` 六个 rows 的
`rho_effect_case=1.05..1.22`，属于 `outside_effect`；其 `trace_response` 被本附录允许，
不再构成当前 component-response residual。`REV-EQ-FUZE` 仍是独立的 15 m sensitivity
variant，不能替代 runtime projection radius。

## 报告字段建议

后续 harness 或 summary 可以在 `component_response` 下增加只读派生字段：

```json
{
  "component_response_quantized_band": "trace_response",
  "component_response_sampled_failure_observed": false,
  "component_response_expectation_status": "below_outer_effective_floor",
  "component_response_quantization_schema": "a2.kill_chain_component_response_quantization.v0"
}
```

推荐 `component_response_expectation_status`：

| 状态 | 条件 |
| --- | --- |
| `not_applicable_no_effect_band` | `effect_band=unclassified_missing_R_effect` |
| `not_applicable_no_rows` | `n_rows=0` 且 `effect_band` 不要求响应 |
| `satisfied` | `component_response_quantized_band` 达到该 `effect_band` 的期望下限 |
| `below_expected_floor` | 低于 `core` / `effective` 期望下限 |
| `below_outer_effective_floor` | `outer_effective` 下只有 `trace_response` |
| `negative_control_pressure` | `outside_effect` 下出现 `nontrivial_response` 或更强 |

## 验收标准

本文的验收只覆盖标准完善，不覆盖校准成功：

- 阈值基于现有 KCES report 字段，可在 before/after 中复用。
- `sampled_failure_count` 不作为单独阈值，只作为观察标记。
- `mission_kill`、`mobility_kill`、`destroyed` 仍属于 `consequence_projection`，
  不反向写入 `component_response`。
- `core/effective/outer_effective/edge/outside_effect` 的复核压力不授予
  `component_failure_probability_authority`、`effect_scale_authority`、`pk_authority`
  或 `deterministic_fuze_authority`。
- 未来 after-report 若声称改善，只能在 P6 单层 guard 下说明目标 layer，并证明
  `guidance_approach`、`fuze_decision` 和非目标 layer 未发生非预期变化。
