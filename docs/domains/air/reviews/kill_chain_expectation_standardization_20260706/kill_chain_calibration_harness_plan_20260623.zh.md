# 杀伤链校准 Harness 计划

状态：`2026-06-23`，用于
[杀伤链期望标准化](README.zh.md) 的 P4 pass harness plan。本文是 docs-only
计划和 artifact 契约；不运行批量仿真，不重调 runtime 参数，不编辑 descriptor，
不声明真实 AIM-120C / F-16C / Pk 权威。

英文规范页：
[kill_chain_calibration_harness_plan_20260623.md](kill_chain_calibration_harness_plan_20260623.md)

Schema label：`a2.kill_chain_calibration_harness_plan.v0`

## 输入

- P2 场景矩阵：
  [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md)
- P3 指标映射：
  [kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md)
- P6 校准准入门：
  [../kill_chain_calibration_admission_gate_20260621.zh.md](../../../../systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/kill_chain_calibration_admission_gate_20260621.zh.md)
- 当前 decoupled probe：
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)

## P4 边界

P4 只把 P3 字段契约绑定到可执行 harness 形状。它不允许：

- 修改 runtime、C++/Python 行为、descriptor 或测试期望；
- 执行完整校准或把 dry-run 结果提升为 accepted behavior；
- 为 `R_fuze_m`、`R_effect_m`、概率阈值或完整度阈值选择数值；
- 使用 warhead / component response 去补偿 `R_fuze` 外的 guidance miss；
- 声明真实武器、真实目标、确定性引信、Pk、reward 或 calibration authority。

`guidance_approach` 在本 P4 中是只读诊断层。若 `N` cell 未进入 `R_fuze`，
harness 必须输出 `guidance_or_model_residual`，并停止该 case 的下游杀伤校准压力。

## Harness 产物

P4 计划使用以下 artifact family。路径是后续 P4 执行或 review packet 的建议位置，
本 P4 文档不创建这些运行产物。

| Artifact | 建议路径 | Schema / 内容 |
| --- | --- | --- |
| case grid | `docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_p4/case_grid_*.jsonl` | 每行包含 P3 `identity` 和 `launch_window` 字段。 |
| before report | `.../before/<batch_id>.json` 或 `.jsonl` | 未改参数前的 heatmap report rows。 |
| after report | `.../after/<layer_id>/<batch_id>.json` 或 `.jsonl` | 仅单层候选变更后的 heatmap report rows；P4 默认不生成。 |
| delta guard | `.../guard/<layer_id>/<batch_id>.json` | P6 `a2.kill_chain_calibration_delta_guard.v1` 输出。 |
| batch summary | `.../summary/<batch_id>.md` | worker 数、case 数、seed 数、耗时、失败 case、guard 状态。 |

每个 heatmap report row 必须至少实现 P3 的这些字段组：

- `identity`
- `launch_window`
- `guidance_approach`
- `fuze_decision`
- `warhead_load_field`
- `component_response`
- `consequence_projection`
- `guards`

缺失字段必须显式写成 `missing_<field>` 或 `unclassified_missing_R_effect`，
不得用默认零值伪装为观测事实。

## Case Grid 计划

| Batch id | Grid | Cases / seed | Seeds | Workers | 目的 | P4 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `KCES-P4-SMOKE-ANCHOR` | `anchor-grid` signed | `93` | `1` | `<=32` | 验证 schema、分组、`rho_*` 派生和 guard 字段。 | planned |
| `KCES-P4-PILOT-MAIN` | `recommended-main-grid` signed + maneuver sparse | `572` | `1` | `32` | 首个主热图 pilot，采集 per-case 时间、内存和输出争用。 | planned |
| `KCES-P4-MAIN-3SEED` | 同上 | `572` | `3` | `48-64` after pilot pass | 第一轮稳定热图，约 `1716` cases。 | gated by pilot |
| `KCES-P4-BOUNDARY` | `boundary-refinement` add-on | `+200-400` | `1-3` | `48-64` after boundary selection | 加密 `N/M` 和 `M/O` 边界。 | gated by main |
| `KCES-P4-MANEUVER-FULL` | `expanded-maneuver-grid` | `962` | `1-3` | held | 机动层成熟后再扩展。 | held |

Worker 策略：

- 以 `32` workers 开始，不直接占满 `88` logical CPUs。
- pilot pass 条件：无系统性输出写入冲突、失败 case 可重试、内存峰值可控、
  report row 字段完整、guard 字段可序列化。
- 只有 pilot pass 后才允许上调到 `48-64` workers。
- `R_effect_variant` 默认作为离线评价维度，不乘进 simulation case 数。

## Layer Guard 计划

P6 已定义可校准 layer。P4 只把这些 layer 绑定到 P3 report row schema 和
delta guard，不打开真实 authority。

| Layer id | Target stage | 允许改变 | Frozen / reject-if-changed stages | P4 用途 |
| --- | --- | --- | --- | --- |
| `guidance_diagnostic_readonly` | none | none | `approach`, `fuze_decision`, `warhead_load_field`, `component_response`, `consequence_projection` | 只读确认 `N/M/O` cell 是否进入 `R_fuze`；不校准。 |
| `fuze_data` | `fuze_decision` | fuze reliability / detection / delay / detonation-probability candidate fields, only after evidence admission | `approach`, `warhead_load_field`, `component_response`, `consequence_projection` | 若 `entered_R_fuze=true` 但 fuze 未触发，用于后续单层候选。 |
| `warhead_data` | `warhead_load_field` | projection radius、fragment/blast load-field candidate fields, only after evidence admission | `approach`, `fuze_decision`, `component_response`, `consequence_projection` | 若 fuze 成功但 load band 异常，用于后续单层候选。 |
| `target_response_data` | `component_response` | component threshold / failure probability candidate fields, only after evidence admission | `approach`, `fuze_decision`, `warhead_load_field`, `consequence_projection` | 若 load 合理但 response 近零，用于后续单层候选。 |
| `consequence_data` | `consequence_projection` | component-failure to platform-consequence mapping, only after evidence admission | `approach`, `fuze_decision`, `warhead_load_field`, `component_response` | 只在 component response 已明确后评价后果。 |

所有可变 layer 都必须符合：

```text
mutation_scope = single_layer_only
dry_run_only = true
runtime_parameter_retuning = false
default_database_modified = false
before_after_stage_report_required = true
delta_guard_required = true
```

## Before / After 和 Delta Guard

P4 后续执行必须先生成 before report，再生成单层 after report，并运行 P6 delta guard。
delta guard 的 CLI 形状为：

```bash
python tools/diagnostics/kill_chain_decoupling_probe.py \
  --delta-guard-before <before_report.json> \
  --delta-guard-after <after_report.json> \
  --delta-guard-layer <layer_id> \
  --output <guard_report.json>
```

Guard 通过条件：

| 条件 | 要求 |
| --- | --- |
| case overlap | before / after 至少有同一组 `case_id`。 |
| target stage delta | `target_stage_id` 必须变化；否则输出 `target_stage_delta_missing`。 |
| frozen stages | `reject_if_changed_stage_ids` 中任何 stage 变化都必须 fail。 |
| authority boundary | `runtime_parameter_retuning=false`, `default_database_modified=false`, `real_world_pk=false`, `deterministic_fuze_authority=false`, `calibration_authority=false`。 |
| negative controls | `O` cells 不得因下游校准变成强 load / response 证据。 |

## Batch 判读规则

| 情况 | P4 分类 | 后续 |
| --- | --- | --- |
| `N` cell 未进入 `R_fuze` | `guidance_or_model_residual` | 不进入 fuze/load/response 校准；登记制导 / 模型残余。 |
| `N` cell 进入 `R_fuze` 但 fuze 未触发 | `fuze_layer_candidate` | 只有未来 `fuze_data` admission 后才允许单层 dry run。 |
| fuze 成功但 `REV-EQ-FUZE` 仍为 `outside_effect` 或 load 近零 | `warhead_load_mapping_residual` | 检查 load-field 映射，不动 component response。 |
| load 合理但 response 近零 | `component_response_candidate` | 只有未来 `target_response_data` admission 后才允许单层 dry run。 |
| response 合理但后果异常 | `consequence_projection_candidate` | 只评价 consequence layer，不倒推上游。 |
| `O` cell 出现强 trigger/load/response | `negative_control_alert` | 先检查 launch classification、case generation 和 stage facts。 |

## P4 收口

P4 当前为 pass。它完成了：

- 将 P3 heatmap report row schema 绑定到 harness artifact family；
- 将 `anchor-grid`、`recommended-main-grid`、boundary refinement 和 maneuver expansion
  写成 batch 计划；
- 明确 `32` worker pilot、`48-64` worker 上调条件和 seed 预算；
- 将 P6 single-layer calibration plan / delta guard 绑定到四个可校准 layer；
- 明确 `guidance_approach` 在本 harness 中是只读诊断层；
- 命名 frozen / reject-if-changed stages；
- 保持 runtime 校准、descriptor 编辑、真实 authority 和完整 batch 执行为 held。

P4 不解决：

- 实际生成 heatmap runtime report；
- 实际 before / after dry-run；
- 参数值、概率阈值或完整度阈值；
- standards promotion；
- authority admission。

这些进入 P5 决策、未来 harness implementation 或 evidence/admission 工作。
