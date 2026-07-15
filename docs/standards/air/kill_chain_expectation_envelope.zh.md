# 空空杀伤链期望包络

Language:
- English canonical: [kill_chain_expectation_envelope.md](kill_chain_expectation_envelope.md)
- Chinese companion: `kill_chain_expectation_envelope.zh.md`

状态：`2026-07-06` active planning supplement，不是当前 runtime contract，用于空空杀伤链期望包络。

Owner layer：`air` specialization。本文标准化空空杀伤链期望检查的 review 词汇和包络形状。
它不声明真实 AIM-120C、真实 F-16C、确定性引信、Pk 或 runtime calibration authority。

## 范围

本标准负责定义用于判断 air-to-air kill-chain 诊断分布是否落在工程代理期望范围内的包络。
它目前是 standards-layer planning supplement，因为当前 harness 已能产生 before-report facts，
但尚未把本包络对象作为维护中的 runtime/test contract 输出。

纳入：

- launch window、guidance approach、fuze decision、warhead load field、
  component response 和 consequence projection 的阶段期望词汇
- 期望包络所需的人为定义输入
- 包络检查使用的派生报告字段
- effect-to-response floor、ceiling 和 review-pressure labels
- anchor-grid 报告的分布容忍度
- 偏离的连续性规则和 owner-stage attribution

不纳入：

- runtime 参数值
- descriptor 修改
- 武器或目标的真实世界真值
- probability-of-kill authority
- calibration approval
- reward 或 training acceptance

## 来源证据

当前任务证据位于：

- [KCES 任务入口](../../task/air_combat/a2_high_fidelity_damage_model/kill_chain_expectation_standardization/README.zh.md)
- [KCES 理想化期望合同](../../task/air_combat/a2_high_fidelity_damage_model/kill_chain_expectation_standardization/kill_chain_idealized_expectation_contract_20260621.zh.md)
- [KCES 场景期望矩阵](../../task/air_combat/a2_high_fidelity_damage_model/kill_chain_expectation_standardization/kill_chain_scenario_expectation_matrix_20260622.zh.md)
- [KCES 指标映射](../../task/air_combat/a2_high_fidelity_damage_model/kill_chain_expectation_standardization/kill_chain_metric_mapping_20260623.zh.md)
- [KCES component-response 量化补充](../../task/air_combat/a2_high_fidelity_damage_model/kill_chain_expectation_standardization/kill_chain_component_response_quantization_20260705.zh.md)

当前 schema label：

```text
a2.kill_chain_expectation_envelope.v0
```

## 人为定义输入

以下字段是 policy input，必须在判断报告前声明：

| Field group | Required definition | Current source |
| --- | --- | --- |
| `profile` | `profile_id`、authority level、weapon proxy、target proxy、forbidden claims | KCES seed profile |
| `grid` | `grid_tier`、range axis、有符号/无符号 offset axis、target-motion layer、seed plan | KCES scenario matrix |
| `launch_class` | 每个 heatmap cell 的 `N`、`M` 或 `O` | KCES heatmap |
| `R_fuze_m` | profile 声明的 fuze-radius source | harness metadata |
| `R_effect_variant` | selected effective-load radius policy | KCES variant list |
| `R_effect_m` | variant-specific effective-load radius | derived or harness-declared |
| `effect_band_thresholds` | `rho_effect` 到 effect-band 的映射 | KCES contract/metric mapping |
| `response_band_thresholds` | `p_max` 和 `delta_abs` 到 response-band 的映射 | KCES quantization addendum |
| `distribution_tolerance` | satisfied share 和 negative-control tolerance | 本文 |
| `owner_rules` | deviation type 到 review-stage 的映射 | 本文 |

修改这些 policy input 就等于修改包络，必须记录为新版本或 addendum。

## 派生报告字段

报告从测量事实和声明输入派生这些字段：

```text
rho_fuze = nearest_distance_m / R_fuze_m
entered_R_fuze = rho_fuze <= 1.0

rho_effect_case = nearest_distance_m / R_effect_m
rho_effect_component = component_loads[].distance_m / R_effect_m

p_max = component_response.max_failure_probability
delta_abs = max(0, -component_response.min_integrity_delta)
sampled_failure_observed = component_response.sampled_failure_count > 0
```

包络 labels：

- `guidance_expectation_status`
- `effect_band`
- `component_response_quantized_band`
- `component_response_expectation_status`
- `envelope_cell_status`
- `envelope_owner_stage`

## Launch / Guidance 包络

| `launch_class` | Expected result | Review pressure | Owner stage |
| --- | --- | --- | --- |
| `N` | `entered_R_fuze=true` | 成簇或重复的 `entered_R_fuze=false` | `launch_window -> guidance_approach` |
| `M` | 可能进入 fuze，但不强制要求 | 与邻近 cells 出现系统性不连续 | `launch_window` / boundary review |
| `O` | `entered_R_fuze=false` 且无 load/response pressure | strong load 或 `nontrivial_response` 以上 | negative-control review |

## Effect-To-Response 包络

Response band 顺序：

```text
no_component_response < trace_response < weak_response <
nontrivial_response < material_response < severe_response
```

| `effect_band` | Expected floor | Normal allowed range | Review pressure | Negative-control pressure |
| --- | --- | --- | --- | --- |
| `core` | `material_response` | `material_response..severe_response` | `nontrivial_response` 或更弱 | n/a |
| `effective` | `nontrivial_response` | `nontrivial_response..severe_response` | `trace_response` 或 `weak_response` | n/a |
| `outer_effective` | `weak_response` | `weak_response..material_response` | `trace_response` | `severe_response` |
| `edge` | `trace_response` | `trace_response..weak_response` | `no_component_response` | `material_response` 或更强 |
| `outside_effect` | `no_component_response` | `no_component_response..trace_response` | n/a | `nontrivial_response` 或更强 |
| `unclassified_missing_R_effect` | none | none | cannot judge | cannot judge |

`sampled_failure_observed` 是 observation flag，不能单独用来满足或否决包络。

## 分布容忍度

v0 anchor-grid report 在 repeated seeds 提供 confidence metadata 前使用 cell-count gates：

| Group | v0 tolerance |
| --- | --- |
| non-boundary `N` cells | `>= 90%` 应进入 `R_fuze` |
| immediate `N/M` boundary `N` cells | `>= 75%` 应进入 `R_fuze` |
| `M` cells | 不设 pass/fail share；保留 stage facts 和 continuity |
| `O` cells | `0` cells 应出现 `nontrivial_response` 或更强 |
| `core/effective` effect cells | `>= 90%` 应满足 expected response floor |
| `outer_effective` effect cells | `>= 70%` 应达到 `weak_response` 或更强 |
| `edge` effect cells | `trace_response` 或 `weak_response` 可接受 |
| `outside_effect` cells | `no_component_response` 或 `trace_response` 可接受 |

## 连续性规则

- 固定 offset angle 时，range 增大不应系统性改善 launch class、fuze entry、
  effect band 或 response band，除非声明机制原因。
- 固定 range 时，absolute offset angle 增大不应系统性改善 launch class、fuze entry、
  effect band 或 response band，除非声明机制原因。
- `M` cells 吸收边界模糊性。
- `O` cells 是 negative controls。通过让 `O` cells 强响应来改善目标 cells，
  属于包络失败。

## Cell Status

| Status | Condition |
| --- | --- |
| `satisfied` | 达到 expected floors，且未超过 negative-control ceilings。 |
| `boundary_observation` | 结果位于 `M` cell 或 immediate boundary band，且无 negative-control pressure。 |
| `below_expected_floor` | `core` 或 `effective` response 低于 floor。 |
| `below_outer_effective_floor` | `outer_effective` 只映射到 `trace_response`。 |
| `guidance_or_model_residual` | `N` cell 未进入 `R_fuze`。 |
| `negative_control_pressure` | `O` / `outside_effect` 出现 `nontrivial_response` 或更强，或 `edge` 出现 material/severe response。 |
| `not_judged_missing_metadata` | 缺少必要 radius、variant 或 report field。 |

## Owner Rules

| Deviation | Owner stage |
| --- | --- |
| `N` cell misses `R_fuze` | `launch_window -> guidance_approach` |
| entered `R_fuze` but no fuze trigger | `fuze_decision` |
| triggered but effect band is weaker than the selected variant implies | `warhead_load_field` |
| load is `core/effective/outer_effective` but response is below floor | `warhead_load_field -> component_response` |
| response satisfies floor but consequence remains weak | `consequence_projection` |
| `O/outside_effect` produces strong response | negative-control review, usually `warhead_load_field` first |
| missing radii or variant metadata | `harness_metadata` |

## 最小包络对象

未来 harness summary 可以输出：

```json
{
  "schema_version": "a2.kill_chain_expectation_envelope.v0",
  "profile_id": "KCES-AIM120C-LIKE-FIGHTER-V0",
  "grid_tier": "anchor-grid",
  "case_id": "KCES-S1-8KM-30DEG-CV",
  "launch_class": "N",
  "R_effect_variant": "REV-RUNTIME-PROJECTION",
  "R_effect_m": 9.0,
  "R_effect_source": "missile_runtime_projection.resolved_projection_radius_m",
  "guidance_expectation_status": "satisfied",
  "effect_band": "outside_effect",
  "component_response_quantized_band": "trace_response",
  "component_response_expectation_status": "satisfied",
  "envelope_cell_status": "satisfied",
  "envelope_owner_stage": "no_review_pressure"
}
```

该对象是 standards review label，不是 calibration result。

## 当前 Held 边界

修正后的当前 KCES runtime-projection slice 从发射时 runtime 快照解析出
`R_effect_m=9.0`。因此 `4/6/8 km +/-30 deg` 的 trace-response rows 属于
`outside_effect`，满足 negative-control 上限，不再是当前
`outer_effective -> trace_response` residual。本包络仍为其他显式 variant（例如
`REV-EQ-FUZE`）保留该 residual label；但在 maintained harness 输出该对象并由
focused tests 固定 schema 前，本标准仍是 planning supplement。Runtime retuning
继续受 KCES P6 single-layer admission gate 约束并保持 held。
