# 空战

状态：`1v1` 工作线仍在活跃推进；默认入口已于 `2026-05-18` 收敛。

## 当前状态

- 第一阶段 `1v1` 已落到维护中的 `execution` / HMoE 主线上。
- 当前基线为 `F-16C_Block50 vs F-16C_Block50`，红方使用脚本对手，并支持场景级弹药覆盖。
- 导弹发射桥、最小对抗终止字段、基础 smoke 训练入口都已经接通。
- 当前主要阻塞点已经不是入口接线，而是训练信号质量，尤其是早期 episode 被 `failfast_deep_stall` 主导。

## 当前继续推进重点

- 收紧 `1v1` 早期飞行稳定性与动作面保护
- 冻结专用 `1v1` eval JSON 结构和维护型评估入口
- 在最小胜负钩子之上补齐 reward / termination shaping
- 强化脚本或冻结对手基线
- 在 `1v1` 指标稳定前，继续把 `2v2` 和双边 self-play 排除在本阶段范围外

## 推荐阅读顺序

- 范围与第一阶段边界：
  [air_combat_1v1_entry_analysis_20260516.zh.md](archive/air_combat_1v1_entry_analysis_20260516.zh.md)
- 执行冻结：
  [air_combat_1v1_freeze_plan_20260516.zh.md](archive/air_combat_1v1_freeze_plan_20260516.zh.md)
- 已落地基线与武器链：
  [air_combat_1v1_f16c_baseline_progress_20260516.zh.md](archive/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)、
  [air_combat_1v1_weapon_chain_progress_20260516.zh.md](archive/air_combat_1v1_weapon_chain_progress_20260516.zh.md)、
  [air_combat_scenario_level_ammo_design_20260516.zh.md](archive/air_combat_scenario_level_ammo_design_20260516.zh.md)
- 训练信号与当前主要阻塞：
  [air_combat_1v1_training_smoke_progress_20260516.zh.md](archive/air_combat_1v1_training_smoke_progress_20260516.zh.md)、
  [air_combat_1v1_stall_rootcause_followup_20260516.zh.md](archive/air_combat_1v1_stall_rootcause_followup_20260516.zh.md)

历史带日期快照现统一放入 [archive/README.zh.md](archive/README.zh.md)。
