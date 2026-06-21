# 杀伤链标量归属账本切片

日期：`2026-06-21`

状态：第三个只读诊断切片。本文记录 `producer / owner / consumer` 标量账本，用来把
`fuze_quality`、`effect_scale`、`spatial_effect_scale`、
`component_failure_probability` 等混合标量拆成可审计条目。本文不改 runtime 参数，
不改默认数据库，不声明真实 AIM-120C、F-16C、Pk、deterministic fuze 或校准权威。

## 为什么需要账本

前两步已经说明：

- 8 km / 30 度 AIM-120C 偏置场景不是单纯“没进近炸”：它进入了 fuze/effects 链路。
- 近炸杀伤偏弱主要出现在 load / response 之后，而不是 approach/fuze 完全空白。
- 现有链路里部分标量跨阶段复用严重，只看最终 `component_failure_count` 会把问题压扁。

这次的账本把每个标量写成一行：

- `scalar_id`：稳定名字，例如 `component_load.effect_scale`。
- `current_owner_stage`：当前在哪一段被生产或携带。
- `intended_owner_stage`：解耦后应该归属哪一段。
- `producer_stage` / `producer_field`：来自现有哪种链路 row / 字段。
- `consumer_fields`：下游谁在消费这个数。
- `coupling_flags`：该标量暴露出的耦合类型。
- `calibration_ready`：是否已经适合进入后续校准候选。这里仍只是诊断标注，不等于批准调参。

## 实现入口

新增：

`tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_scalar_ledger.py`

`tools/diagnostics/air_combat_weapon_employment_process_probe.py` 现在在 payload 中输出：

- `lethality_chain_scalar_ledger`
- `lethality_chain_scalar_coupling_summary`

`tools/diagnostics/kill_chain_decoupling_probe.py` 现在在每个 guidance / proximity case 中输出：

- `scalar_coupling_ledger`
- `scalar_coupling_summary`

并在顶层输出跨 case 的：

- `scalar_coupling_summary`

## 当前账本能区分的两类耦合

第一类是 owner 泄漏：一个标量现在由 A 段携带，但解耦后应该归 B 段。

典型例子：

| scalar | 当前 owner | 目标 owner | flag |
| --- | --- | --- | --- |
| `fuze.mechanism_coverage_score` | `fuze_decision` | `warhead_load_field` | `mechanism_coverage_produced_in_fuze_stage` |
| `effects_event.component_failure_probability` | `effects_event` | `component_response` | `effects_event_aggregates_response_probability` |
| `consequence.vulnerability_effect_scale` | `consequence_projection` | `component_response` | `vulnerability_effect_scale_visible_in_consequence` |

第二类是跨阶段消费：标量 owner 可以暂时正确，但它是复合量，正在被多个下游阶段消费。

典型例子：

| scalar | owner | 现象 | flag |
| --- | --- | --- | --- |
| `component_load.effect_scale` | `warhead_load_field` | 载荷、响应、后果都消费同一个复合缩放 | `composite_effect_scale_crosses_stage_boundary` |
| `effects_event.spatial_effect_scale` | `effects_event` | 聚合 spatial scale 直接流入响应/后果 | `aggregate_spatial_effect_scale_crosses_stage_boundary` |
| `effects_event.mechanism_effect_scale` | `effects_event` | 聚合 mechanism scale 直接流入响应/后果 | `aggregate_mechanism_scale_crosses_stage_boundary` |
| `approach.miss_distance_m` | `approach` | 同时被 fuze、load、response 语义复用 | `range_geometry_reused_across_stages` |

这个区分很重要：`component_load.effect_scale` 现在不是“owner 放错”，而是“复合消费过宽”。
后续拆分它时，应优先拆成 spatial intersection、pattern、exposure、armor、sampling、
load intensity 等显式因子，而不是简单移动字段。

## 刷新的 baseline artifact

命令：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --mode all \
  --seed 20260621 \
  --output docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json
```

报告：

`docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json`

刷新后报告大小为 `1186180` bytes，包含 `4` 个 guidance case、`7` 个 proximity case，以及
`646` 条标量账本记录。其中 `246` 条被标注为后续可作为 calibration candidate 的
标量事实；这不是批准调参，只是说明它们已经有相对清晰的 owner / producer。

顶层耦合 flag 计数：

| flag | count |
| --- | ---: |
| `effects_event_aggregates_response_probability` | `20` |
| `effect_scale_decomposition_factor_available` | `77` |
| `component_load_named_factor_available` | `63` |
| `vulnerability_response_factor_aggregated_in_effects_event` | `55` |
| `fuze_quality_damage_multiplier_explicit_policy` | `22` |
| `warhead_damage_scalar_policy_boundary` | `22` |
| `aggregate_mechanism_scale_crosses_stage_boundary` | `11` |
| `aggregate_spatial_effect_scale_crosses_stage_boundary` | `11` |
| `closure_reused_across_stages` | `11` |
| `component_threshold_response_factor_aggregated_in_effects_event` | `11` |
| `fuze_quality_damage_multiplier_candidate` | `11` |
| `mechanism_coverage_produced_in_fuze_stage` | `11` |
| `range_geometry_reused_across_stages` | `11` |
| `vulnerability_effect_scale_visible_in_consequence` | `11` |
| `component_distance_reused_by_load_and_response` | `9` |
| `composite_effect_scale_crosses_stage_boundary` | `9` |

## 8 km / 30 度账本结果

| case | nearest miss distance | max component failure probability | scalar flags |
| --- | ---: | ---: | ---: |
| `aim120_8km_left_30deg` | `10.963446 m` | `0.006350` | `12` 类 |
| `aim120_8km_right_30deg` | `10.963479 m` | `0.006356` | `12` 类 |

两侧都出现：

- `fuze_quality_damage_multiplier_candidate`
- `mechanism_coverage_produced_in_fuze_stage`
- `composite_effect_scale_crosses_stage_boundary`
- `effects_event_aggregates_response_probability`
- `vulnerability_effect_scale_visible_in_consequence`

这进一步支持当前判断：8 km / 30 度的“未有效杀伤”不是一个单点问题，而是从
`warhead_load_field` 到 `component_response` 的复合缩放、effects-event 聚合摘要和后果
trace 耦合叠加。load-row response probability owner 泄漏已由 P5 清理，不再出现在当前
顶层 flag 中。

## 后续拆解顺序

建议继续按机器可验收的小切片推进：

1. P0/P3：旧的 `fuze_quality -> damage` 倍率入口已从 runtime surface 删除；后续
   `fuze_quality` 只应作为 fuze confidence / diagnostics。
2. P1/P4：`component_load.effect_scale` 已拆出 runtime named load factors；后续让
   downstream 消费 spatial intersection、pattern、exposure、armor、sampling 和
   load intensity，而不是继续只读复合 `effect_scale`。
3. P2/P5：`component_load.component_failure_probability` 已不再作为当前 runtime owner；
   `component_response.failure_probability` 由 runtime response rows 产生。
4. P3：让 consequence 只消费 response/consequence facts，不再从 trace 回读
   vulnerability/effect scale。
5. P6：calibration admission gate 已建立；repository engineering proxy 已可进入
   单层 guarded calibration plan，真实 authority flag 继续保持 false。

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

当前边界保持不变：这只是诊断与抽象解耦，不修复 8 km / 30 度命中，不调高近炸杀伤，
也不把任何工程代理结果提升成真实弹种/目标结论。
