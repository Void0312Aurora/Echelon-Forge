# MLF-9 趋势工具结果

状态：`2026-06-19` P3 initial pass。

英文主文：
[missile_lethality_pk_statistical_trends_trend_harness_20260619.md](missile_lethality_pk_statistical_trends_trend_harness_20260619.md)。

## 结果

`tools/diagnostics/mlf9_statistical_trends.py` 现在提供 MLF-9 的确定性行级趋势摘要器。
它消费显式 `lethality_chain_rows` 列表，或包含该字段的 JSON 对象，按
`(episode, chain_id)` 聚合行，派生 chain records，并输出有边界的仿真趋势摘要。

该实现刻意保持在下游。它不改变引信、战斗部、部件、结构、后果、生命周期、奖励、
删除或校准行为。

## 报告形状

摘要 payload 包含：

- `schema_version`：`mlf9.statistical_trends.v1`。
- `confidence_level`、匹配 normal quantile 的 `confidence_z` 和 `interval_method`。
- `group_by`、`chain_count`，以及每个请求分组的条目。
- 每个 group 的 `chain_identities`，使跨 episode 重复的 `chain_id` 仍然可见。
- chain、released、detonated、component-damage、structural-breakup 和
  platform-consequence chain 的分母计数。
- fuze negative、effective component damage、structural breakup、airframe breakup、
  functional kill 和 terminal lifecycle 的后果计数。
- rate records，包含 success count、sample count、rate 和 Wilson 区间边界。
- 明确的 authority-boundary flags，拒绝 real-world Pk、weapon-specific lethality、
  target-specific lethality、calibration authority、reward authority 和
  entity-deletion authority。

## 受控 Fixture 覆盖

`tests/tools/test_mlf9_statistical_trends.py` 覆盖：

- released、component-damage、structural-breakup 和 platform-consequence chains 的分母计数。
- fuze negative、component damage、structural breakup、airframe breakup 和 terminal lifecycle 的后果计数。
- component damage 条件下 structural breakup、structural breakup 条件下 terminal lifecycle 的 Wilson 有界 rate。
- 按 miss-distance bucket 和 breakup mode 分组。
- 保证 payload 留在 synthetic simulation trend 权威内的 non-claim flags。

## 验证

```bash
python3 -m py_compile tools/diagnostics/mlf9_statistical_trends.py
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_mlf9_statistical_trends.py
```

结果：

- `2 passed`。

## 边界

这不是校准后的 Pk 模型。它只是对仿真已经产出的行做确定性摘要。真实武器 Pk、
具体目标杀伤率、公开结果验证、来源准入提升和校准门继续留给 MLF-10 或后续工作。
