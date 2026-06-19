# MLF-9 指标契约

状态：`2026-06-19` P2 initial contract pass。本契约定义第一版有边界统计趋势表面，
并继续 hold 校准 Pk。

英文主文：
[missile_lethality_pk_statistical_trends_metric_contract_20260619.md](missile_lethality_pk_statistical_trends_metric_contract_20260619.md)。

## 契约边界

MLF-9 报告的是可回放链路行上的仿真趋势。它不报告真实杀伤概率。本契约下产出的每个
rate 都只能读成：

```text
在这个 synthetic scenario / fixture population 内，在满足这个显式分母的行里，
有这么一部分抵达了这个仿真 outcome bucket
```

不能读成：

```text
这种真实武器对这种真实目标的 Pk 是多少
```

## 必需 Row Source

初始实现必须使用 `lethality_chain_rows`，或字段等价的 test fixture。Rows 必须包含：

- `episode`、`step`、`sim_time_s`
- `chain_id`、`event_id`、`parent_event_id`
- `stage`、`source_event_kind`、`source_event_id`
- `munition_id`、`target_id`
- `evidence_level`、`observation_mode`、`consumer_visibility`

MLF-9 v1 接受的 stage set 是：

1. `nearest_approach`
2. `fuze`
3. `warhead_mechanism`
4. `spatial_coverage`
5. `component_load`
6. `component_damage`
7. `structural_breakup`
8. `platform_consequence`
9. `lifecycle`

`training_projection` 不进入 MLF-9 v1 row source，因为 reward 或训练 consumer 会把统计趋势证据
和训练反馈混在一起。

## 分母

| Denominator | Definition | Allowed use | Not allowed |
| --- | --- | --- | --- |
| `chain_count` | 报告 population 内不同 `chain_id` 数量 | 总样本量 | 除非 fixture generation 证明独立性，否则不得称为真实独立试验 |
| `released_chain_count` | 有 launch/effects source row 或显式 fixture release marker 的链 | given-release rate | 不得当作真实发射次数 |
| `detonated_chain_count` | 有有效 warhead/spatial/component-load 行，且没有 terminal negative fuze reason 的链 | given-effective-detonation rate | 不得把 synthetic fuze outcome 当作真实引信可靠性 |
| `component_damage_chain_count` | 至少有一条 `component_damage` row 的链 | component damage 条件下的 structural / consequence rate | 不得声明 component damage probability 已校准 |
| `structural_breakup_chain_count` | 至少有一条 `structural_breakup` row 的链 | structural breakup 条件下的 consequence / lifecycle rate | 不得把 breakup 当作直接坠毁 / 删除 |
| `platform_consequence_chain_count` | 有 `platform_consequence` row 的链 | functional outcome distribution | 不得当作真实 mission kill probability |

每个报告必须打印 denominator name、count 和 filter expression。

## Outcome Buckets

| Bucket | Row fields | Meaning | Boundary |
| --- | --- | --- | --- |
| `fuze_negative` | `fuze_triggered == 0` 或 terminal negative reason | 链路未抵达有效起爆 | negative reason 是仿真事实，不是真实 miss statistic |
| `effective_component_damage` | `component_damage` row count > 0 | 至少一个 component-damage fact 被采样 | 仅通用部件损伤 |
| `structural_breakup` | `structural_breakup` row count > 0 | 至少一个具名结构断裂事实存在 | 不是坠毁规则 |
| `airframe_breakup` | 任意 structural row 的 `airframe_breakup == 1` | 机体级断裂事实存在 | 不是碎片物理 |
| `functional_kill` | mission/mobility/sensor/survivability kill fields | 平台后果抵达某个功能桶 | 不是真实任务结果概率 |
| `terminal_lifecycle` | lifecycle row 有 `lifecycle_terminal == 1` 或 terminal ground lifecycle | terminal lifecycle fact 存在 | diagnostics-only 行仍不进入 reward |

## Grouping Fields

初始趋势报告可按以下字段分组：

- miss-distance bucket；
- direct-hit vs proximity evidence；
- mechanism family；
- component system；
- component failure mode；
- structural break mode；
- terminal lifecycle class。

报告必须避免暗示校准的 weapon / target 标签。即使 scenario 名包含平台标签，报告标题仍必须写明
“simulation trend” 或 “fixture trend”。

## 不确定性标签

初始 MLF-9 rate 可以使用 Wilson-style binomial intervals，或 diagnostics tooling 已使用的等价显式区间方法。
报告必须写明：

- sample count；
- confidence level；
- interval method；
- high-variance flags 是否触发；
- 样本来自 deterministic fixtures、seed sweeps 还是 live probe episodes。

## P3 实现门

下一步实现 trend harness 只有在满足以下条件时才可推进：

- 消费显式 rows，不读隐藏 runtime state；
- 输出 denominator 和 filters；
- 有 deterministic controlled-fixture tests；
- 拒绝真实 Pk、校准、reward 和 entity-deletion claims。

## 验证

P2 row-surface validation 已通过：

```bash
PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

结果：`47 passed`。
