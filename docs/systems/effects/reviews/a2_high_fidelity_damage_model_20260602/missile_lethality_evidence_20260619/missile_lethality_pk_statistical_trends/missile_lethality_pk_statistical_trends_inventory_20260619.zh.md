# MLF-9 证据盘点

状态：`2026-06-19` MLF-9 Pk / 统计趋势输入的 P1 inventory pass。

英文主文：
[missile_lethality_pk_statistical_trends_inventory_20260619.md](missile_lethality_pk_statistical_trends_inventory_20260619.md)。

## 盘点决策

MLF-9 可以从现有链路关联的仿真事实开始，但必须把它们当成 replay / trend input，
不能当成校准后的 Pk 数据。当前最合适的入口是 diagnostics process probe 的
`lethality_chain_rows`，因为它已经把 episode/step 上下文、chain/event 标识、
证据标签和阶段字段放在同一张表里。

P1 发现统一 row surface 的唯一硬缺口是结构断裂：C++ 契约、event storage、bindings
和 facade packet 都已经暴露 `StructuralBreakupEvent`，但 Python diagnostics row
contract 没有投影 `structural_breakup` 行。本分支补上这个投影，使 MLF-9 后续定义
结构后果分母时不需要绕过通用 diagnostics 表。

## 输入表面

| Surface | Status | Reusable fields | MLF-9 use | Boundary |
| --- | --- | --- | --- | --- |
| Lethality header | accepted input | [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h) 中的 `chain_id`、`event_id`、`parent_event_id`、`stage`、`source_time_s`、`target`、`evidence_level`、`observation_mode`、`consumer_visibility` | 把行 join 成可回放链路，并保留证据标签 | Header 顺序不是概率校准 |
| Geometry/fuze rows | accepted input | miss distance、local detonation vector、closure、aspect、fuze armed/triggered/sample/reliability、trigger radius | near/far、direct/proximity、trigger/non-trigger 等趋势分桶 | synthetic fuze probability 不是真实引信可靠性 |
| Warhead/spatial rows | accepted input | mechanism family、fragment/blast/rod 值、spatial hit estimate/fraction、pattern/energy scale | 暴露量和机制分组 | 通用 research load 不是具体武器真值 |
| MLF-5 component damage | accepted input | component name/system、integrity before/after、failure mode/severity、failure probability/sample | 部件损伤 outcome 和组件族分组 | 部件概率仍是通用、未校准 |
| MLF-6 structural breakup | row-surface pass in this branch | breakup state、break mode、detached part ref/count、airframe breakup、cause event id | 结构后果桶，以及 component damage 到 terminal outcome 的桥 | 结构事实不是直接坠毁或 Pk 规则 |
| MLF-7 platform consequence | accepted input | mission/mobility/sensor/survivability before/after、deltas、kill flags、loss-state transition | 功能后果桶 | 后果事实不暗示真实杀伤概率 |
| MLF-8 lifecycle | accepted input | lifecycle from/to、ground lifecycle、debris count、terminal flag、terminal projection id、diagnostics-only visibility | terminal wreck / detached-part lifecycle bucket | lifecycle facts 默认仍是 diagnostics-only 且不进 reward |
| Window-position sweep | candidate reference | release/effects/component/consequence/mission-kill rates、confidence intervals、variance flags | rate/uncertainty 计算参考实现 | 这是训练诊断，不自动成为 MLF-9 权威 |

## 当前 Row Surface

本分支通过以下文件把 Python diagnostics 与 C++ 阶段列表对齐，加入
`structural_breakup`：

- [tools/diagnostics/lethality_chain_contract.py](../../../../../../../tools/diagnostics/lethality_chain_contract.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py](../../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py](../../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py)
- [tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py](../../../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py)
- [tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py](../../../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py)

为 MLF-9 增加的 row fields：

- `breakup_state`
- `break_mode`
- `detached_part_ref`
- `detached_part_count`
- `airframe_breakup`
- `cause_event_id`

为后续趋势摘要增加的 snapshot fields：

- `lethality_chain_structural_breakup_count`
- `lethality_chain_breakup_state`
- `lethality_chain_break_mode`
- `lethality_chain_detached_part_ref`
- `lethality_chain_detached_part_count`
- `lethality_chain_airframe_breakup`
- `lethality_chain_structural_cause_event_id`

现在 rows 会按 chain id、canonical stage order、event id 和 source event id 稳定排序，
因此 structural row 会出现在 component-damage 和 platform-consequence 之间，不再取决于
producer loop 谁先 append。

## 缺失或保留输入

| Gap | Effect on MLF-9 | Proposed handling |
| --- | --- | --- |
| 尚无已验收 MLF-9 denominator | “given launch”、“given detonation”、“given component damage”等 rate 会有歧义 | 在 P2 contract 先定义分母 |
| 尚无校准样本总体 | 任何 rate 都只是 simulation replay rate，不是现实 Pk | 每个报告标注为 synthetic simulation trend |
| 尚无公开结果准入 | 不能拟合或验证真实事件 | 留给 MLF-10 |
| 尚无一等 debris entity | 不能统计碎片交互或碎片二次损伤 | 只使用 lifecycle terminal / detached facts |
| DCR 受控非零 consequence fixture 仍 partial | reward/consequence training evidence 不能作为 MLF-9 验收 | 保持 reward 工作相邻但不授权 |

## 安全实现写集

MLF-9 初始实现切片允许：

- 本目录下的 MLF-9 docs。
- 当只是暴露已验收事件事实时，可改 diagnostics row contract 和 process-probe tests。
- 不改变 runtime physics 的 test-only fixture。

后续契约前保持 held：

- Runtime damage physics、probability parameters、weapon profiles、reward shaping、
  entity lifecycle，或已归档 MLF evidence packages。

## 验证

本次 inventory / row-surface pass 执行：

```bash
python3 -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_chain.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_rows.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_snapshot.py \
  tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/schema.py \
  tools/diagnostics/lethality_chain_contract.py

PYTHONPATH=build-workshop:. pytest -q \
  tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py \
  tests/runtime/air_combat/test_diagnostics_process_probe_summary.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

结果：`47 passed`；py-compile 通过。
