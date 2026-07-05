# 杀伤链期望标准化当前状态

状态：`2026-06-28` accepted / retained task-local standard + initial
before-report harness implementation。P0 子项目边界为 pass；P1 期望合同为 pass，已采用
`R_effect_policy=independent_review_variable`；P2 场景矩阵为 pass；P3 指标映射为
pass；P4 harness plan 为 pass；P5 标准提升决策为 pass；runtime 校准继续 held。

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
- 已增加并收口 P5 标准提升决策：P1-P4 内容保留为 task-local docs-only standard；
  本轮不写入 `docs/standards`。
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
  将当前匀速 anchor rows 分为 `4` 个 `guidance_approach` 复核 cells、`6` 个
  `component_response` 复核 cells、`13` 个 `no_review_pressure` cells、`21` 个
  `marginal_observation` cells 和 `34` 个 `negative_control_satisfied` cells。
- 已新增 component-response local diagnosis：
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md)，
  六个 `component_response` cells 均归为
  `outer_effect_low_component_load_probability_cliff`，显示 case-level
  `outer_effective` band 映射到较弱 component load scale 和极低 response probability。
- 已整合 before report 的 `component_detail`：
  `a2.kill_chain_expectation_component_detail.v1` 由共享
  `component_detail_projection.py` 从既有 runtime facade 只读投影逐部件
  load/response 配对；response diagnosis 只消费该投影，不在 KCES 内重新实现
  杀伤归因。六个 `component_response` cells 的
  `detail_projection_signal` 均为 `all_component_rows_weak_load_low_response`。

## 成熟度矩阵

| 项 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 项目边界 | pass | [README.zh.md](README.zh.md) | docs-only，不改 runtime。 |
| 期望合同 | pass | [kill_chain_idealized_expectation_contract_20260621.zh.md](kill_chain_idealized_expectation_contract_20260621.zh.md) | 只有定性分区，没有概率阈值；`R_effect` 保持独立。 |
| 场景矩阵 | pass | [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md) | 已分类 heatmap cells，补充 sampling-density estimate，并选择第一轮 `R_effect_variant`；指标映射已由 P3 独立收口。 |
| 指标映射 | pass | [kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md) | 字段契约已创建；不选择 runtime 参数值。 |
| 校准 harness 计划 | pass | [kill_chain_calibration_harness_plan_20260623.zh.md](kill_chain_calibration_harness_plan_20260623.zh.md) | 计划已创建；不执行批量仿真，不重调 runtime 参数。 |
| 标准提升决策 | pass | [kill_chain_standard_promotion_decision_20260623.zh.md](kill_chain_standard_promotion_decision_20260623.zh.md) | 决策为 retained task-local standard；`docs/standards` 本轮不写入。 |
| Harness 初始实现 | partial | [kill_chain_harness_implementation_20260623.zh.md](kill_chain_harness_implementation_20260623.zh.md) | 完整匀速 `78` case anchor before report、逐部件 `component_detail`、可视化 heatmap、首阶段复核归因和 response 局部诊断已生成；完整 `93` anchor/main grid、并行 worker、机动 runtime 支持仍未完成。 |

## 残余登记

| Residual | Owner | Exit condition |
| --- | --- | --- |
| 概率 / 完整度阈值仍未量化 | KCES-P4/future evidence | P4 或后续 admission work 明确阈值依据；P3 只保留报告字段。 |
| 推荐主采样网格尚未执行 | future harness implementation | initial harness 已生成匀速目标 anchor before report 和 reviewable heatmaps；未来执行 recommended-main before heatmap report。 |
| `8 km / 30 deg` 需要后续解释 / 校准决策 | future factor decomposition | before report 已显示进入 `R_fuze`，first-review-stage 归因为 `component_response`；report-level diagnosis 显示为 `outer_effect_low_component_load_probability_cliff`，且已通过共享投影保留逐部件 load/response 细节；后续只需把断崖原因分解到 spatial projection、receiver exposure / armor / threshold 或 response curve。 |
| `N` 类局部制导 residual | future guidance / launch-window review | `4/6 km` 的 `+/-45 deg` 四个 `N` cells 未进入 `R_fuze`，需要复核 P2 launch class 或制导模型。 |
| `N` 类低响应 residual | future factor decomposition | `4/6/8 km` 的 `+/-30 deg` 六个 `N` cells 已进入 `R_fuze` 且有 outer-effective load band，但 response 未采样到 failure；同距离 `15 deg` sampled-response 基线对照显示 max failure probability 仅约 `0.72%~0.98%`，逐部件 `detail_projection_signal` 均为 `all_component_rows_weak_load_low_response`。 |
| 并行 worker 和 retry 尚未实现 | future harness implementation | worker pool、失败 case retry 和 batch summary writer 落地。 |
| 机动目标 runtime harness 尚未实现 | future harness implementation | `mild_maneuver` grid rows 不再标为 unsupported，并有对应 runtime facts。 |
| 标准提升暂缓 | future standards promotion | 只有在 runtime/test/admission 证据验收后，才按 standards maintenance policy 重开。 |
| 真实 authority 不可用 | future admission work | 未来 authority gate 准入具体字段；此前所有声明保持 engineering proxy。 |

## 推荐下一步

1. 本 P0-P5 docs-only workstream 已收口；不要在本批次写入 runtime 或 `docs/standards`。
2. 下一步优先基于共享投影输出中的逐部件 `component_loads[]` /
   `component_responses[]` 细节，继续分解 response cliff 的原因；同时把
   `guidance_approach` 四个 cells 作为窗口 / 制导复核队列。
3. 在任何 after report、参数候选或 standards promotion 前，先保留 P6 frozen-stage
   guard 和 authority boundary。

## 显式拒绝的过度声明

- 真实 AIM-120C 战斗部、引信或破片形态真值。
- 真实 F-16C 易损性或部件失效真值。
- 确定性引信权威。
- Pk 或 stock weapon/target lethality authority。
- 由本 docs-only 种子授予 runtime calibration authority。
