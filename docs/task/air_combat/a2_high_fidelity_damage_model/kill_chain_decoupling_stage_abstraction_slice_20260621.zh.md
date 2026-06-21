# 杀伤链解耦分层诊断切片

日期：`2026-06-21`

状态：首个实现切片 / 只读诊断。本文记录本轮从机制解耦分析进入代码面的工作。
本切片不改变 runtime 参数，不改变 C++ 制导/引信/战斗部/部件杀伤模型，不放行真实
AIM-120C、F-16C、Pk、deterministic fuze 或校准权威。

## 目标

先把现有 `lethality_chain_rows` 投影成更接近解耦设计的五段视图：

`approach -> fuze_decision -> warhead_load_field -> component_response -> consequence_projection`

这样后续观察 8 km / 30 度偏置场景时，不再只看最终 `component_failure_count` 或
target active，而是能直接看每段是否存在、每段观测了什么、以及哪些旧耦合仍在输出里。

## 实现入口

- 新增
  `tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_abstraction.py`。
- `tools/diagnostics/air_combat_weapon_employment_process_probe.py` 现在在 payload 中输出：
  - `lethality_chain_stage_abstractions`
  - `lethality_chain_decoupling_summary`
- 现有 `lethality_chain_rows`、chain CSV、MLF-9 statistical trends 不变。

## 新增输出

### `lethality_chain_stage_abstractions`

逐 chain 输出五个抽象 stage。每行包含：

- `abstraction_stage`：五段之一。
- `owner`：该段的唯一职责。
- `source_stages` / `source_event_kinds`：从哪些现有标准/兼容事件投影而来。
- `observed`：该段拥有的关键观测字段。
- `coupling_flags`：该段仍暴露出的历史耦合痕迹。

当前 stage 到 owner 的映射：

| abstraction stage | owner | 主要来源 |
| --- | --- | --- |
| `approach` | `guidance_kinematics` | `nearest_approach` |
| `fuze_decision` | `fuze_decision` | `fuze` |
| `warhead_load_field` | `warhead_load_field` | `warhead_mechanism`、`spatial_coverage`、`component_load` |
| `component_response` | `component_response` | `component_damage`，或未触发 damage 时从 `component_load` 候选概率回收 |
| `consequence_projection` | `consequence_projection` | `structural_breakup`、`platform_consequence`、`lifecycle` |

### `lethality_chain_decoupling_summary`

汇总所有 stage abstraction，包含：

- `chain_count`
- `abstraction_count`
- `present_stage_counts`
- `coupling_flag_counts`
- `missing_stages_by_chain`
- `authority_boundary`

`authority_boundary` 明确保持：

- `runtime_parameter_retuning = false`
- `real_world_pk = false`
- `deterministic_fuze_authority = false`
- `calibration_authority = false`

## 当前能自动暴露的耦合痕迹

| flag | 含义 |
| --- | --- |
| `fuze_stage_contains_mechanism_coverage_score` | 引信层仍带有机制覆盖/作用质量信息 |
| `component_load_uses_composite_effect_scale` | component load 仍消费复合 `effect_scale` |
| `consequence_trace_contains_vulnerability_effect_scale` | 后果层 trace 中仍可见 vulnerability/effect scale 耦合 |

这些 flag 不是验收失败；它们是后续 P0/P1 耦合账本和分层诊断的机器可读入口。P5
迁移后，旧 `component_load_row_contains_response_probability` 和
`component_response_inferred_from_load_row_candidate` 不再由默认 load-row ABI 字段触发。

## 验证

命令：

```bash
python -m pytest tests/runtime/air_combat/test_diagnostics_process_probe_summary.py -q
python -m pytest tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py -q
```

结果：

- `19 passed`
- `8 passed`

## 当前边界

这只是第一个可执行诊断切片：

- 已开始把杀伤链输出按五段抽象。
- 已能在 process-probe payload 中看到分层视图和耦合 flag 汇总。
- 未拆 `effect_scale` 字段本身。
- 未移除 `fuze_quality` 到 `effective.damage` 的隐式缩放。
- 未重调 AIM-120C、F-16C 或任意 runtime 杀伤参数。
- 未声称 8 km / 30 度场景已修复。

下一步应在该输出基础上跑 8 km / 30 度和近炸距离 sweep，让报告直接指出弱化发生在
approach、fuze、load、response 还是 consequence 段。
