# 空战 1v1 训练条目

此目录存放正在维护的 `1v1` 空战执行配置。

## 范围

- 该路线的场景配对为：
  - [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
    - 由 scripted-red `F-16C` smoke 和 8k probe 条目使用。
  - [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
    - 由 Stage-0 drone weapon-employment reactive 和 temporal world-batch probe 条目使用。
- 当前基线为：
  - 蓝方学习者：`F-16C_Block50`
  - 红方对手：场景声明的脚本化 `F-16C_Block50`
  - 策略架构：`HierarchicalMoEExecutionPolicy`
- Stage-1 到 Stage-3 的 `scenarios/air_combat/1v1` 文件是受维护的课程场景，但本目录目前还没有与它们配对的 active training config。

## 条目

- [air_combat_1v1_f16c_scripted_red_smoke_v1.json](air_combat_1v1_f16c_scripted_red_smoke_v1.json)
  - 在标准 `execution` vec-env 路径上的最小引导烟雾测试。
  - 直接使用维护中的 HMoE 策略表面，而非共享策略回退。

- [air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json)
  - 在维护中的默认 `WorldBatchVecEnv` 路径上的对应烟雾测试条目。
  - 当你希望验证脚本化红方对手和 HMoE 策略也能在批处理运行时路径上正确推进时，请使用此项。

- [air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json)
  - 维护中的 `WorldBatchVecEnv` 路径上的短程 HMoE 训练探针。
  - 它超过 smoke 长度，但仍足够小，适合高频诊断。
  - 在进入 32k/64k resume ramp 前，先用它确认早期终止是否仍被飞行稳定性伪影主导。

- [air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json)
  - 阶段零无人机武器使用探针，保留单帧 `TransformerExtractor` 作为 reactive 对照。
  - 用于观察基础开火流程、重复发射和奖励/终止链路。

- [air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json)
  - 阶段零的 M1 temporal HMoE 探针。
  - 它启用 `temporal_history_len=16` 与 `TemporalTransformerExtractor`，其余主要超参贴近 reactive 对照。
  - 这是路径 C 前的验证入口，不代表正式 sequence-native 因果策略。

## 设计说明

- 这些烟雾测试条目有意设为非可视化。
  - 目标是首先验证作战任务契约和运行时链路，而非可视吞吐量。
- 这些烟雾测试条目直接使用当前 HMoE 主线架构。
  - `1v1` 并不将独立的共享策略活动条目作为其主要维护路径。
- 当前 `1v1` 烟雾测试仍使用 `mission_obs_mode=basic`。
  - 因此 HMoE 策略处于活跃状态，但暴露给策略的维护路线语义仍然最小化。
  - 在当前烟雾日志中，这意味着路由停留在导航族/子专家上，这对于链路验证是可接受的，但尚未形成完全差异化的作战路由配置。
- 这些烟雾测试条目有意不启用维护中的脚本化残差动作封装。
  - 当前稳定飞行残差预设锁定了几个在空战中有用的开关维度，包括武器相关控制。
  - 在首次 `1v1` 烟雾测试中，我们希望学习者保留原始的 `full` 动作表面。
- 这些条目尚未成为验收/冻结基线。
  - 仅在 `1v1` 奖励/终止/评估行为足够稳定（可跨运行比较）之后才进行提升。
- temporal 条目只增加策略可见的短历史。
  - 它不改变导弹物理、弹药、冷却或环境侧战术记忆。
