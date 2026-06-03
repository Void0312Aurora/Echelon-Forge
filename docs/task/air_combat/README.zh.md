# 空战

状态：`1v1` 工作线仍在活跃推进；默认入口已于 `2026-05-18` 收敛；
`2026-05-25` 已开启分阶段 `1v1` 真实度梯度课程；`2026-06-03`
有边界的 A3 C2/ROE 发射纪律层 accepted，M2 继续 held。

## 当前状态

- 第一阶段 `1v1` 已落到维护中的 `execution` / HMoE 主线上。
- 当前 smoke 基线为 `F-16C_Block50 vs F-16C_Block50`，红方使用脚本对手，并支持场景级弹药覆盖。
- 导弹发射桥、最小对抗终止字段、基础 smoke 训练入口都已经接通。
- `2026-05-24` 的 8k HMoE probe 中，早期 episode 被 `failfast_deep_stall`
  主导的现象没有复现；本轮终止集中在 `combat_loss`。
- 当前主要阻塞点已明确为训练可达性：武器开关动作初始几乎不可达，smoke
  红方会在开局立即发射，且 `mission_obs_mode=basic` 下 HMoE 路由仍集中在
  `nav/vector`。
- 第一训练入口应转向
  [a1_1v1_realism_gradient/README.zh.md](a1_1v1_realism_gradient/README.zh.md)
  中定义的分阶段课程，而不是历史 smoke fixture。
- 重复发射问题现在先进入已 accepted 的有边界 C2/ROE 层：
  [a3_c2_roe_release_discipline/README.zh.md](a3_c2_roe_release_discipline/README.zh.md)：
  武器控制状态、目标身份、开火授权、single-shot-then-assess / salvo / reattack
  许可和策略可观察的 mission observation 约束已经接入。P4 probe 能拆分授权发射与
  违规发射。`2026-06-03` 32k A3 learned-policy probe 显示 deterministic
  模型不发射，stochastic probe 仍产生多次违规发射；发射后 mission observation
  已改为动态暴露 `shot_budget_remaining=0` / `pending_assessment=1`，但 learned-policy
  武器使用验收和 M2 release 仍 held。
- 高真实度毁伤模型现在在
  [a2_high_fidelity_damage_model/README.zh.md](a2_high_fidelity_damage_model/README.zh.md)
  保留轻量指针；完整包位于
  [archive/a2_high_fidelity_damage_model/](archive/a2_high_fidelity_damage_model/README.zh.md)。
  该线已在 research / candidate profile 下封存归档：structured-aircraft damage/effects
  runtime 进入维护路径，blast-fragmentation 候选包非权威验收通过，G4/G5 research
  packet 已收口；stock authority、Pk 与 deterministic fuze 仍未放行。

## 当前继续推进重点

- 收紧 `1v1` 早期飞行稳定性与动作面保护
- 冻结专用 `1v1` eval JSON 结构和维护型评估入口
- 在最小胜负钩子之上补齐 reward / termination shaping
- 强化脚本或冻结对手基线
- 拆分 `combat_loss`、被击落实体失效和终端 crash penalty 的诊断语义
- 将 A2 高保真空战毁伤模型作为 sealed retained record 读取；只有用户明确要求时，
  才另启 `G4/G5 authority` 或新的 research expansion
- 保持当前 blast-fragmentation candidate 包非权威验收边界，不把 test-local descriptor
  演练上卷成 stock authority
- 在 `1v1` 指标稳定前，继续把 `2v2` 和双边 self-play 排除在本阶段范围外
- 按 `scenarios/air_combat/1v1/` 下的 staged 场景，从武器发射到有限双向武器逐步验收
- 在发射后动态观测修复之后，使用 A3 C2/ROE probe config 继续 reactive/temporal
  learned-policy 对照；不用 process-probe 分类结果或单次 32k 未通过结果直接释放 M2

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
- 当前分阶段课程：
  [a1_1v1_realism_gradient/README.zh.md](a1_1v1_realism_gradient/README.zh.md)
- C2/ROE 发射纪律 accepted 层：
  [a3_c2_roe_release_discipline/README.zh.md](a3_c2_roe_release_discipline/README.zh.md)
- 高真实度毁伤模型封存记录：
  [a2_high_fidelity_damage_model/README.zh.md](a2_high_fidelity_damage_model/README.zh.md)
  与完整归档
  [archive/a2_high_fidelity_damage_model/README.zh.md](archive/a2_high_fidelity_damage_model/README.zh.md)
- 高保真毁伤系统基线：
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

历史带日期快照现统一放入 [archive/README.zh.md](archive/README.zh.md)。
