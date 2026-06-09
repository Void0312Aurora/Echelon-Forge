# 空战

状态：`1v1` 工作线仍在活跃推进；默认入口已于 `2026-05-18` 收敛；
`2026-05-25` 已开启分阶段 `1v1` 真实度梯度课程；`2026-06-03`
有边界的 A3 C2/ROE 发射纪律层 accepted。`2026-06-08` 将 A4-A7 作为历史
firing-learning 线路关闭，不再把它们当作当前 blocker。当前有边界发射门已经由模型侧
M3-S2 包在 A5 weapon-arm action-frame fix 后验收：
[../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md](../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md)。
`2026-06-08` 也已按有边界损伤效果链切片验收 A8：导弹效果现在可以被检查为具体部件损伤
和维护中系统响应；校准后的武器真值、飞机专用飞控律、平台族扩展、真实世界杀伤权威和
一等碎片/残留对象仍是单独后续工作。同日 A1 已建立 Stage-2 C2/ROE 训练入口并完成
第一轮 8k init-from-Stage-1 短训；单 seed deterministic/stochastic probes 保住一次授权发射，
但没有 effects/damage/kill，因此 Stage-2 仍未验收。

## 当前状态

- 第一阶段 `1v1` 已落到维护中的 `execution` / HMoE 主线上。
- 当前 smoke 基线为 `F-16C_Block50 vs F-16C_Block50`，红方使用脚本对手，并支持场景级弹药覆盖。
- 导弹发射桥、最小对抗终止字段、基础 smoke 训练入口都已经接通。
- `2026-05-24` 的 8k HMoE probe 中，早期 episode 被 `failfast_deep_stall`
  主导的现象没有复现；本轮终止集中在 `combat_loss`。
- 旧的训练可达性阻塞已经不是当前发射状态。M3-S2 batch validation 已在 active
  scenario/config pair 上验收有边界发射门：learned policy 请求并执行一次授权
  `fire_once` release，且 rejected requests、violations、repeat-before-assessment
  releases 均为零。
- 第一训练入口应转向
  [a1_1v1_realism_gradient/README.zh.md](a1_1v1_realism_gradient/README.zh.md)
  中定义的分阶段课程，而不是历史 smoke fixture。
- A1 当前推进点是 Stage-2 C2/ROE 机动目标入口：
  [a1_stage2_c2_roe_entry_and_short_train_20260608.zh.md](a1_1v1_realism_gradient/a1_stage2_c2_roe_entry_and_short_train_20260608.zh.md)。
  该入口已能运行、能从 Stage-1 M3-S2 final model 迁移一次授权发射，并完成一轮 8k 短训；
  但只构成进入下一训练阶段的证据，不构成 Stage-2 战果或批量发射验收。
- 重复发射问题进入已 accepted 的有边界 C2/ROE 层：
  [archive/a3_c2_roe_release_discipline/README.zh.md](archive/a3_c2_roe_release_discipline/README.zh.md)：
  武器控制状态、目标身份、开火授权、single-shot-then-assess / salvo / reattack
  许可和策略可观察的 mission observation 约束已经接入。A3 仍是合法性/纪律权威，
  但不是当前发射闭合包。
- 已关闭的历史 firing-learning 线路：
  [archive/a4_authorized_first_shot_training_signal/README.zh.md](archive/a4_authorized_first_shot_training_signal/README.zh.md)：
  A4 原地关闭。保留结论是 reward shaping、routing、diagnostics 和 opportunity penalty
  没有解决发射。
- 已关闭的历史结构性 event-action 线路：
  [archive/a5_constrained_event_action_model/README.zh.md](archive/a5_constrained_event_action_model/README.zh.md)：
  A5 原地关闭。它贡献了受约束 `hold/fire_once` 表面，以及后续 M3-S2 使用的
  weapon-arm action-frame fix。
- 已关闭的历史 first-event timing 线路：
  [archive/a6_event_value_first_event_timing/README.zh.md](archive/a6_event_value_first_event_timing/README.zh.md)：
  A6 原地关闭。保留结论是 hazard/deadline/window labels 暴露了有用 timing evidence，
  但没有成为当前 firing authority。
- 已关闭的历史 event-credit/timing 线路：
  [archive/a7_event_value_advantage_credit_head/README.zh.md](archive/a7_event_value_advantage_credit_head/README.zh.md)：
  A7 原地关闭。保留结论是 event-credit work 属于 timing-quality research history，
  当前 launch closure 属于 M3-S2。
- 高真实度毁伤模型现在在
  [a2_high_fidelity_damage_model/README.zh.md](a2_high_fidelity_damage_model/README.zh.md)
  保留轻量指针；完整包位于
  [archive/a2_high_fidelity_damage_model/](archive/a2_high_fidelity_damage_model/README.zh.md)。
  该线已在 research / candidate profile 下封存归档：structured-aircraft damage/effects
  runtime 进入维护路径，blast-fragmentation 候选包非权威验收通过，G4/G5 research
  packet 已收口；stock authority、Pk 与 deterministic fuze 仍未放行。
- A8 损伤效果链现在在
  [archive/a8_damage_effect_chain/README.zh.md](archive/a8_damage_effect_chain/README.zh.md)
  保留轻量指针；完整包位于
  [archive/archive/a8_damage_effect_chain/](archive/archive/a8_damage_effect_chain/README.zh.md)。
  它已作为有边界切片验收并归档：起爆后的效果可转成具体飞机部位损伤，并通过已有动力、
  燃油、传感器、火灾和飞行消费路径表现出来。已验收证据覆盖动力、一段翼面/操纵气动响应、
  燃油泄漏/质量响应、更完整火灾后果检查、数据链任务/传感器后果，以及窄的地面接触生命周期状态；
  碎片/残留对象后置。它仍不增加直接坠毁规则、MQ-9 特例击杀规则、Pk 声明、确定性引信声明或
  AIM-120C 权威杀伤声明。

## 当前继续推进重点

- 收紧 `1v1` 早期飞行稳定性与动作面保护
- 冻结专用 `1v1` eval JSON 结构和维护型评估入口
- 在最小胜负钩子之上补齐 reward / termination shaping
- 强化脚本或冻结对手基线
- 拆分 `combat_loss`、被击落实体失效和终端 crash penalty 的诊断语义
- 将 A2 高保真空战毁伤模型作为 sealed retained record 读取；只有用户明确要求时，
  才另启 `G4/G5 authority` 或新的 research expansion
- 将
  [A8 损伤效果链](archive/a8_damage_effect_chain/README.zh.md) 作为已归档 accepted record 读取：
  具体损伤可通过维护中的飞机系统传播，但不增加直接坠毁或特定目标击杀规则；只有明确要求校准、
  平台扩展或碎片/残留对象工作时才重开
- 保持当前 blast-fragmentation candidate 包非权威验收边界，不把 test-local descriptor
  演练上卷成 stock authority
- 在 `1v1` 指标稳定前，继续把 `2v2` 和双边 self-play 排除在本阶段范围外
- 按 `scenarios/air_combat/1v1/` 下的 staged 场景，从武器发射到有限双向武器逐步验收；
  当前下一步是 Stage-2 firing-retention 小批量验证，而不是立即进入 Stage-3 或 self-play
- 将 A4-A7 作为 closed historical records 读取；当前 launch closure 是 M3-S2 有边界
  firing gate，新的 timing-quality 工作应另开 model follow-on

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
- A1 Stage-2 C2/ROE 入口与短训：
  [a1_stage2_c2_roe_entry_and_short_train_20260608.zh.md](a1_1v1_realism_gradient/a1_stage2_c2_roe_entry_and_short_train_20260608.zh.md)
- C2/ROE 发射纪律 accepted 层：
  [archive/a3_c2_roe_release_discipline/README.zh.md](archive/a3_c2_roe_release_discipline/README.zh.md)
- 当前有边界发射闭合：
  [M3-S2 fire-timing learnability archive](../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md)
- 已关闭的历史 firing-learning records：
  [archive/a4_authorized_first_shot_training_signal/README.zh.md](archive/a4_authorized_first_shot_training_signal/README.zh.md)、
  [archive/a5_constrained_event_action_model/README.zh.md](archive/a5_constrained_event_action_model/README.zh.md)、
  [archive/a6_event_value_first_event_timing/README.zh.md](archive/a6_event_value_first_event_timing/README.zh.md)
  和
  [archive/a7_event_value_advantage_credit_head/README.zh.md](archive/a7_event_value_advantage_credit_head/README.zh.md)
- A4 reward/routing 证据：
  [archive/a4_authorized_first_shot_training_signal/README.zh.md](archive/a4_authorized_first_shot_training_signal/README.zh.md)
  及 reward 证据：
  [a4_authorized_first_shot_reward_probe_20260603.zh.md](archive/archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_reward_probe_20260603.zh.md)
  和 routing 证据：
  [a4_authorized_first_shot_routing_probe_20260603.zh.md](archive/archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_routing_probe_20260603.zh.md)
  以及 binary diagnostics：
  [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](archive/archive/a4_authorized_first_shot_training_signal/a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)
- 高真实度毁伤模型封存记录：
  [a2_high_fidelity_damage_model/README.zh.md](a2_high_fidelity_damage_model/README.zh.md)
  与完整归档
  [archive/a2_high_fidelity_damage_model/README.zh.md](archive/a2_high_fidelity_damage_model/README.zh.md)
- 损伤效果链 follow-on：
  [archive/a8_damage_effect_chain/README.zh.md](archive/a8_damage_effect_chain/README.zh.md)
- 高保真毁伤系统基线：
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

历史带日期快照现统一放入 [archive/README.zh.md](archive/README.zh.md)。

已归档子项目的完整清单见 [归档注册表](archive_registry.zh.md)。
