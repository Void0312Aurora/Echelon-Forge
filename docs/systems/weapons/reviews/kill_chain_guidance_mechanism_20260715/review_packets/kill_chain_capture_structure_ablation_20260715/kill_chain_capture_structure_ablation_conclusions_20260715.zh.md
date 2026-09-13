# 第三阶段：capture 结构消融结论 — 2026-07-15

## 结论

本轮冻结世界系 LOS-history PN、世界系 CV tracker、`N=4`、`35 g` 与 `APN gain=0.5`，只改变 capture 的 range 与 lead 结构。共运行 `292` 次确定性案例。

结构选择结果：`P0`（capture 关闭负控）。
该选择只准入第四阶段连续窗口重建；它不是最终 AIM-120 默认参数结论。

## 匹配条件效应

| Effect | 中位有符号效应 (m) | 平均绝对效应 (m) | 最大效应 (m) | 有效 owner |
| --- | ---: | ---: | ---: | --- |
| `base_inverse_given_terminal_flat` | 9.922 | 16.685 | 64.820 | YES |
| `base_inverse_range` | 13.752 | 61.462 | 406.462 | YES |
| `capture_total` | 14.485 | 62.027 | 410.042 | YES |
| `lead_content` | -49.523 | 72.581 | 199.386 | YES |
| `lead_range_schedule` | 0.000 | 0.152 | 1.461 | NO |
| `lead_range_schedule_terminal_flat` | 0.000 | 0.081 | 0.765 | NO |
| `terminal_clamp` | -3.889 | 10.828 | 43.575 | YES |
| `terminal_given_base_flat` | 0.132 | 0.708 | 4.404 | NO |
| `terminal_weighting` | 4.383 | 45.485 | 346.045 | YES |
| `lead_x_terminal_interaction` | 0.000 | 0.228 | 2.225 | NO |
| `range_interaction` | 4.065 | 44.777 | 341.641 | YES |

有效 owner 判据不是“单案改善最大”：matched toggle 必须在至少 3 个单元、至少 3 个 anchor 单元产生 `|Δrho_fuze|>=0.05` 的重复效应；单个边界异常不能成为 owner。旧 O 标签不参与选择门。
`capture_total` 的正号表示加入 capture 后最近距恶化；若全部 anchor 同号，选择纯 world-frame PN，而不是继续给相互补偿的 capture/lead schedule 调参。

## Clamp 边界审计

审计覆盖 `2/2.4/3/20/24/28 km × ±15/±30 deg × P1/P4/P7`。`2.4 km` 与 `24 km` 分别是当前 terminal weight 的上、下 clamp 边界；P4 固定为 unity，P7 保留 reciprocal 但移除 clamp。

## 验收

- `P1_profile_equivalent_to_unprofiled_candidate_within_1e_3_m`: PASS
- `max_P1_profile_equivalence_delta_m`: `2.8599345114344032e-12`
- `selected_profile_matches_production_candidate_within_1e_3_m`: PASS
- `max_selected_profile_production_delta_m`: `1.5506367891104933e-13`
- `mirror_symmetric_within_1e_3_m`: PASS
- `max_mirror_abs_difference_m`: `5.0815396077985575e-05`
- `P0_capture_component_zero_within_1e_12_g`: PASS
- `max_P0_capture_g`: `0.0`
- `postclamp_never_exceeds_35g`: PASS
- `max_postclamp_g`: `35.0`
- `clamp_audit_complete`: PASS
- `clamp_audit_cell_count`: `72`
- `expected_clamp_audit_cell_count`: `72`
- `candidate_structure_selected`: PASS

## 阶段边界

- P1 与未附着 diagnostics profile 的候选 runtime 必须逐案等价，否则本轮结构差异无效。
- P0 必须给出严格零 capture 分量，总指令不得超过 35 g。
- 第四阶段必须在选定结构上重建连续 `4..16 km × 0..90 deg` 包线；不得用旧 `16 km / 30 deg -> O` 反向否决已修正机制。
- 当前匀速矩阵不能授予真实武器、机动目标 APN 或 Pk 权威。
