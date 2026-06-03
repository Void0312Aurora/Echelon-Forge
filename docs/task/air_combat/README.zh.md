# 空战

状态：`1v1` 工作线仍在活跃推进；默认入口已于 `2026-05-18` 收敛；
`2026-05-25` 已开启分阶段 `1v1` 真实度梯度课程；`2026-06-03`
有边界的 A3 C2/ROE 发射纪律层 accepted，M2 继续 held；同日开启 A4
授权首发训练信号 follow-on；A4 reward/routing 证据继续 held 后，已开启 A5
受约束事件动作模型路线，且 A5 已在短训 learned-policy evidence 后保持 held。A6
已完成首轮 event-value / first-event timing evidence wave、deadline-bootstrap re-scope wave
和 event-head update-strength audit，并已完成 event-head optimization learned evidence；A6
因 launch-window timing quality 继续 held。

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
  已改为动态暴露 `shot_budget_remaining=0` / `pending_assessment=1`。post-fix
  reactive/temporal 对照显示 temporal stochastic 可清零违规发射，但 deterministic
  武器使用仍不发射；M2 release 仍 held。
- 直接后续曾进入
  [a4_authorized_first_shot_training_signal/README.zh.md](a4_authorized_first_shot_training_signal/README.zh.md)：
  先用 reward shaping 和 policy-routing 证据让授权首发可训练，再重新讨论 M2。首个 A4
  reward-side probe 显示，episode 内一次性武器链 shaping 仍不够：deterministic 仍不
  fire，stochastic 仍产生违规发射；随后 routing probe 增加显式 `combat_weapons`
  HMoE family。保留的 routed 32k evidence 小幅改善 stochastic 发射纪律，但
  deterministic 仍为 0 fire/release。naive A4-only pulse-prior 放松已被测试并拒绝：
  它增加违规发射，但没有让 deterministic policy fire。binary diagnostics 随后显示
  授权窗口内 `fire_weapon` 仍约 `0.22%` probability / `-6.11` max logit；
  有边界 fire-opportunity penalty trial 也已拒绝，因为它没有推动 deterministic fire，
  且恶化 stochastic release discipline。因此 A4 作为证据保持 held：reward/routing
  repair 不是根治手段。
- 当前模型层 follow-on 是
  [a5_constrained_event_action_model/README.zh.md](a5_constrained_event_action_model/README.zh.md)：
  将武器释放从逐帧 binary/threshold control 改成受约束事件动作，引入显式
  engagement state、action mask、`hold/fire_once` 语义、post-launch `FiredAssess`
  suppression 和显式 reattack gate。A5 短训 learned-policy probe 将 stochastic
  release discipline 修复到每个 episode 一次 authorized release、零 violations，但
  deterministic policy 仍为零 `fire_once` requests。A5 继续 held；下一步应针对
  event-value / first-event timing，而不是 reward-only legality tuning。M2 继续 held。
- 新 follow-on 是
  [a6_event_value_first_event_timing/README.zh.md](a6_event_value_first_event_timing/README.zh.md)：
  首个 masked first-event hazard / bounded curriculum 实现已经有真实 PPO labels 和
  diagnostics，但短训 learned evidence 仍让 deterministic policy 停在 `0` 次
  `fire_once` requests，event probability 约 `0.25%`。deadline-bootstrap re-scope 随后将
  deterministic open-window probability 推到约 `0.49%`，但 deterministic requests 仍为
  `0`；stochastic probing 保持 `3/3` 授权 releases、零 violation/repeat/budget issues，但有
  一次 `weapon_not_ready` rejected request。event-head update audit 随后显示 A6 gradients
  是 live，但当前 optimizer/head scaling 让 event delta 停在约 `-5`。有边界的
  event-head lane 修复了这个狭义 blocker：deterministic probing 现在执行一次 authorized
  release，stochastic probing 保持 `3/3` one-shot authorized releases，且零
  rejected/violation/repeat/budget issues。A6 仍 held，因为 release timing 收敛到
  authorization/contact 后的近立即时刻；下一步是 launch-window / engagement-quality timing
  contract，而不是释放 M2。
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
- 推进
  [A6 event-value / first-event timing](a6_event_value_first_event_timing/README.zh.md)，
  先定义 launch-window / engagement-quality timing contract，再考虑升级到 event-value head
  或重新讨论 M2

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
- 授权首发训练信号 follow-on：
  [a4_authorized_first_shot_training_signal/README.zh.md](a4_authorized_first_shot_training_signal/README.zh.md)
  及 reward 证据：
  [a4_authorized_first_shot_reward_probe_20260603.zh.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_reward_probe_20260603.zh.md)
  和 routing 证据：
  [a4_authorized_first_shot_routing_probe_20260603.zh.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_routing_probe_20260603.zh.md)
  以及 binary diagnostics：
  [a4_authorized_first_shot_binary_diagnostics_20260603.zh.md](a4_authorized_first_shot_training_signal/a4_authorized_first_shot_binary_diagnostics_20260603.zh.md)
- 受约束事件动作模型 follow-on：
  [a5_constrained_event_action_model/README.zh.md](a5_constrained_event_action_model/README.zh.md)
- Event-value / first-event timing follow-on：
  [a6_event_value_first_event_timing/README.zh.md](a6_event_value_first_event_timing/README.zh.md)
- 高真实度毁伤模型封存记录：
  [a2_high_fidelity_damage_model/README.zh.md](a2_high_fidelity_damage_model/README.zh.md)
  与完整归档
  [archive/a2_high_fidelity_damage_model/README.zh.md](archive/a2_high_fidelity_damage_model/README.zh.md)
- 高保真毁伤系统基线：
  [air_combat_damage_model_evaluation_20260522.md](../../forward/air_combat_damage_model_evaluation_20260522.md)

历史带日期快照现统一放入 [archive/README.zh.md](archive/README.zh.md)。
