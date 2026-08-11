# N5 RL 动作面拆分

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/reviews/n5_rl_action_surface_split_20260527/README.md`
Owner: `domains/naval/reviews`
Last verified: `2026-08-09`
Review basis: 已接受 N4 action/observation repair 与保留的 training-entry evidence。

状态：`2026-05-27` 已实现，并保留为已接受的 `N4` pre-fire training-entry repair
记录。它交付了第一段维护中的海军 RL action/observation surface，并将 active N4
入口提升到单策略槽位 cooperative runtime；它不是 active `N5` weapon-engagement
release。

语言：

- 英文规范版：`README.md`
- 中文伴随版：[README.zh.md](README.zh.md)

输入：

- [N4 threat / ROE bridge](../n4_threat_roe_bridge_20260525/README.zh.md)
- [N4 RL task surface preflight](../n4_threat_roe_bridge_20260525/naval_n4_rl_task_surface_preflight_20260525.zh.md)
- [领域 owner 索引](../../../README.zh.md)
- [海军 owner](../../README.zh.md)
- [空军动作契约](../../../air/standards/pilot_action_contract.zh.md)
- [Subagent usage policy](../../../../engineering/automation/standards/subagent_usage_policy.zh.md)

## 目的

把海军 RL 控制面从空军起飞训练面里拆出来。

N4 训练入口此前有价值，因为它证明了场景、奖励和维护中的 world-batch
运行路径可以对接。但正式训练暴露了域错配：`action_mode=takeoff4` 输出的是
空军式 `PilotAction` 杆、舵、油门；舰艇运动系统会把非中性的舵或油门当作
手动接管，从而绕开更适合当前海军场景的站位保持命令链。

本子项目释放一个有限修复：专门的开火前海军动作模式，通过海军 task/command
链改变站位意图，同时保持低层 pilot-action carrier 为中性；同时增加海军任务观测模式，
直接命名站位、接触、ROE、报告链和目标来源字段。

## 当前用途

本目录现在是已接受 N4 repair 的闭合 evidence packet。后续若继续拆分 naval action、
command、observation 或 configuration ownership，应从
[Naval Domain Surface Split](../../work/active/naval_domain_surface_split/README.zh.md) 进入，而不是在这里继续追加新的 N5/N6 声明。

## 输出

- [N5 RL 动作面拆分簇](naval_n5_rl_action_surface_split_cluster_20260526.md)
- 维护中的动作模式：`naval_station3`
- 维护中的观测模式：`naval_screen_station_v1`
- active naval 训练入口迁移：
  `examples/config/training/active/naval/*.json`
- 聚焦运行与训练入口测试。

## 范围

范围内：

- 一个专门用于站位指令 probe 的海军 RL 动作模式；
- 一个专门用于站位、接触、ROE、报告链和指定目标字段的海军任务观测模式；
- active N4 训练入口从 `takeoff4` 迁出；
- active N4 训练入口从空军 formation-role 任务观测迁出；
- 为新动作模式增加 world-batch step 前命令同步；
- 聚焦测试证明 active naval 入口不暴露武器释放、不使用毁伤/击杀奖励、不再复用空军起飞动作面或空军 formation-role 观测。

范围外：

- 武器释放、命中/拦截、毁伤、击杀或交战奖励；
- 完整海军舵令/自动舰艇控制 doctrine；
- 通用 cooperative naval 多槽位提升；
- 最终海军 packet 所有权和 cooperative 观测 schema；
- 用正式 `CommandPacket` 全面替换兼容 `MissionCommand`。

## 守门

本切片可合入条件：

- active naval N4 配置使用 `action_mode=naval_station3`；
- 海军零动作保持当前站位指令；
- 海军非零动作通过海军 task/command 链更新站位方位、半径和速度意图；
- active naval N4 配置使用 `mission_obs_mode=naval_screen_station_v1`；
- 策略任务向量暴露站位误差、屏护距离、接触、支援/报告、ROE 和指定目标字段；
- 新动作模式下舰艇 pilot-action carrier 保持中性；
- training bootstrap 接受 active 入口；
- active cooperative 入口都保留非 agent 支援舰 roster，但不为它分配策略槽位；
- 合同和奖励测试仍保持开火前边界。

## 残留

- 架构线释放后，用更窄的 command/tasking packet 替代兼容 `MissionCommand` 聚合。
- 只有在更广的观测和 packet 所有权模型释放后，才把 cooperative naval 从已接受的
  active N4 单策略槽位支援 roster 情况继续扩大。
- `naval_limited_engagement_v1` 继续阻塞在独立 launch/reject package 之后。
- 只有当场景实际越过 screen-station 与开火前接触/报告行为后，才继续扩展第一段海军观测切片。
