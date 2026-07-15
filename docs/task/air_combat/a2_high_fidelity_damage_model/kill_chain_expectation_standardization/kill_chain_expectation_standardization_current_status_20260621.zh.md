# 杀伤链期望标准化当前状态

状态：`2026-07-15` accepted / retained expectation-standardization track +
initial before-report harness implementation + post-P5 component-response
threshold addendum + 标准化 v0 期望包络 + 只读 expectation-envelope audit。P0
子项目边界为 pass；P1 期望合同为 pass，已采用
`R_effect_policy=independent_review_variable`；P2 场景矩阵为 pass；P3 指标映射为
pass；P4 harness plan 为 pass；P5 标准提升决策为 pass。P6 已准入 engineering-proxy
guarded single-layer dry-run plans；runtime 参数重调与真实世界 authority 继续 held。

英文规范页：
[kill_chain_expectation_standardization_current_status_20260621.md](kill_chain_expectation_standardization_current_status_20260621.md)

## 创建以来的变化

- 创建独立 A2 follow-on，用于理想化期望标准化。
- 增加 v0 期望合同，定义归一化 `rho_fuze` 和 `rho_effect` 词汇。
- 增加 AIM-120C-like engineering-proxy 种子画像，不声明真实武器或目标权威。
- 已从父级 A2 README 链接本项目。
- 已关闭 P1 半径 policy：`R_effect` 保持独立 review variable。
- 已增加并收口第一版 P2 场景期望 heatmap。
- 已将 P2 验收对象从单一代表性 row 扩展为距离 x 偏置角矩阵：锚点网格覆盖
  `4/6/8/10/12/16 km` 和 `0/15/30/45/60/75/90 deg`，机动目标保留 sparse grid。
- 已补充 P2 采样密度估算：粗网格只作为锚点，推荐 P3/P4 主网格约为 `572`
  signed cases / seed，并在边界追加局部加密。
- 已选择第一轮 P3 / calibration-planning 可读取的 `R_effect_variant` 集合：
  `REV-RUNTIME-PROJECTION`、`REV-EQ-FUZE` 和 `REV-SMALLER-LOAD`。
- 已增加并收口 P3 指标映射，声明 stage-report 字段、derived `rho_*` 字段、
  `R_effect_variant` 映射、heatmap report row schema 和 owner guard 字段。
- 已增加并收口 P4 harness plan，将 P3 report row schema 绑定到 case-grid batch、
  artifact family、`32` worker pilot、P6 delta guard 和 frozen-stage 规则。
- 已增加并收口原 P5 标准提升决策：当时 P1-P4 内容保留为 task-local
  docs-only standard，且不写入 `docs/standards`。
- 已新增 initial before-report harness：
  [kill_chain_harness_implementation_20260623.zh.md](kill_chain_harness_implementation_20260623.zh.md)，
  提供 `anchor-grid` case-grid generator、只读 decoupling-probe wrapper 和 P3 heatmap
  row projection。
- 已新增 before-report visualization：
  [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md)，
  从现有 JSON 生成 launch class、guidance status、`rho_fuze`、max failure probability
  和 effect band 的 CSV/PNG/SVG 矩阵。
- 已新增 first-review-stage attribution：
  [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md)，
  将当前匀速 anchor rows 分为 `4` 个 `guidance_approach` 复核 cells、`19` 个
  `no_review_pressure` cells、`21` 个 `marginal_observation` cells 和 `34` 个
  `negative_control_satisfied` cells。
- 已新增 component-response local diagnosis：
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md)，
  修正 runtime 空间投影后，`REV-RUNTIME-PROJECTION` 下选出的
  `component_response` candidates 为 `0`。
- 已整合 before report 的 `component_detail`：
  `a2.kill_chain_expectation_component_detail.v1` 由共享
  `component_detail_projection.py` 从既有 runtime facade 只读投影逐部件
  load/response 配对；response diagnosis 只消费该投影，不在 KCES 内重新实现
  杀伤归因。runtime variant 现在读取
  `missile_runtime_projection.resolved_projection_radius_m=9.0`，而不是 15 m
  致死半径。
- 已新增 post-P5 component-response 量化阈值附录：
  [kill_chain_component_response_quantization_20260705.zh.md](kill_chain_component_response_quantization_20260705.zh.md)，
  使用 `p_max`、`delta_abs` 和独立 `sampled_failure_observed` 标记定义
  `trace_response`、`weak_response`、`nontrivial_response`、`material_response`
  和 `severe_response`。当前 `4/6/8 km +/-30 deg` 的 trace-response cells 属于
  `outside_effect`，在修正后的 runtime projection 下满足 negative-control 上限。
- 已新增标准化 v0 期望包络：
  [空空杀伤链期望包络](../../../../standards/air/kill_chain_expectation_envelope.zh.md)，
  把人为定义的 profile/grid/radius/band/tolerance 输入与派生报告字段、
  launch/guidance 包络规则、effect-to-response floor/ceiling、分布容忍度、
  连续性规则、cell status labels 和 owner-stage attribution 注册为空中特化
  planning supplement。
- 已新增只读 expectation-envelope audit：
  [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md)，
  将 standards-layer envelope 应用到既有 `78` 个匀速 rows。launch/guidance 与
  marginal 分类先于无关 effect-metadata 检查后，结果分布为 `4` 个
  `guidance_or_model_residual`、`21` 个 `boundary_observation`、`53` 个
  `satisfied`；这是后处理结果，不是重跑仿真、参数修改或校准 verdict。

## 成熟度矩阵

| 项 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 项目边界 | pass | [README.zh.md](README.zh.md) | docs-only，不改 runtime。 |
| 期望合同 | pass | [kill_chain_idealized_expectation_contract_20260621.zh.md](kill_chain_idealized_expectation_contract_20260621.zh.md) | 只有定性分区，没有概率阈值；`R_effect` 保持独立。 |
| 场景矩阵 | pass | [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md) | 已分类 heatmap cells，补充 sampling-density estimate，并选择第一轮 `R_effect_variant`；指标映射已由 P3 独立收口。 |
| 指标映射 | pass | [kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md) | 字段契约已创建；不选择 runtime 参数值。 |
| 校准 harness 计划 | pass | [kill_chain_calibration_harness_plan_20260623.zh.md](kill_chain_calibration_harness_plan_20260623.zh.md) | 计划已创建；不执行批量仿真，不重调 runtime 参数。 |
| 标准提升决策 | pass | [kill_chain_standard_promotion_decision_20260623.zh.md](kill_chain_standard_promotion_decision_20260623.zh.md) | 原 P1-P4 决策保留 task-local workstream；后续 v0 envelope 是 planning supplement，不是 runtime contract。 |
| Harness 初始实现 | partial | [kill_chain_harness_implementation_20260623.zh.md](kill_chain_harness_implementation_20260623.zh.md) | 完整匀速 `78` case anchor before report、逐部件 `component_detail`、可视化 heatmap、首阶段复核归因和 response 局部诊断已生成；完整 `93` anchor/main grid、并行 worker、机动 runtime 支持仍未完成。 |
| 组件响应量化阈值 | pass | [kill_chain_component_response_quantization_20260705.zh.md](kill_chain_component_response_quantization_20260705.zh.md) | task-local docs-only 诊断分区；不授予 component-failure、Pk 或确定性引信权威。 |
| 标准化期望包络 v0 | pass | [docs/standards/air/kill_chain_expectation_envelope.zh.md](../../../../standards/air/kill_chain_expectation_envelope.zh.md) | 空中特化 planning supplement；不是当前 runtime contract，不修改 runtime 参数，也不授予 calibration authority。 |
| Expectation-envelope audit 后处理器 | pass | [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md) | 只读取既有 before report；envelope 字段尚未由 harness 内联输出。 |

## 残余登记

| Residual | Owner | Exit condition |
| --- | --- | --- |
| 概率 / 完整度阈值已形成 task-local v0 附录，尚未实现为 harness 输出字段 | future harness implementation | 若需要机器消费，按附录输出 `component_response_quantized_band`、`component_response_sampled_failure_observed` 和 `component_response_expectation_status`。 |
| 标准化期望包络已有只读后处理器，但 harness 尚未内联输出 | future harness implementation | 若需要在 harness report 内机器消费，从 before/after report 输出 `a2.kill_chain_expectation_envelope.v0` 字段，例如 `envelope_cell_status` 和 `envelope_owner_stage`。 |
| 推荐主采样网格尚未执行 | future harness implementation | initial harness 已生成匀速目标 anchor before report 和 reviewable heatmaps；未来执行 recommended-main before heatmap report。 |
| `N` 类局部制导 residual | future guidance / launch-window review | `4/6 km` 的 `+/-45 deg` 四个 `N` cells 未进入 `R_fuze`，需要复核 P2 launch class 或制导模型。 |
| Runtime projection 来源必须保持显式 | future harness maintenance | 保持 `REV-RUNTIME-PROJECTION` 绑定 `missile_runtime_projection.resolved_projection_radius_m`，并把 `REV-EQ-FUZE` 作为独立 sensitivity variant。 |
| 并行 worker 和 retry 尚未实现 | future harness implementation | worker pool、失败 case retry 和 batch summary writer 落地。 |
| 机动目标 runtime harness 尚未实现 | future harness implementation | `mild_maneuver` grid rows 不再标为 unsupported，并有对应 runtime facts。 |
| 标准提升暂缓 | future standards promotion | 只有在 runtime/test/admission 证据验收后，才按 standards maintenance policy 重开。 |
| 真实 authority 不可用 | future admission work | 未来 authority gate 准入具体字段；此前所有声明保持 engineering proxy。 |

## 推荐下一步

1. 本 P0-P5 workstream 已收口；不要在本批次写入 runtime 变更，也不要把
   standards-layer envelope 当成 runtime contract。
2. 把 `guidance_approach` 四个 cells 作为窗口 / 制导复核队列，并在后续所有
   before/after report 中保留修正后的 9 m runtime-projection 来源。
3. 在任何 after report、参数候选或 standards promotion 前，先保留 P6 frozen-stage
   guard 和 authority boundary。

## 显式拒绝的过度声明

- 真实 AIM-120C 战斗部、引信或破片形态真值。
- 真实 F-16C 易损性或部件失效真值。
- 确定性引信权威。
- Pk 或 stock weapon/target lethality authority。
- 由本 docs-only 种子授予 runtime calibration authority。
