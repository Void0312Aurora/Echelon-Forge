# M1-A4 Stage-1 短程证据 - 2026-06-02

状态：`needs more A`。本轮证明 Stage-1 reactive / temporal HMoE 入口可训练、可加载、可诊断，
但尚未证明 temporal window 改善武器使用行为。

## 设置

- 场景：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`
- reactive 配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json`
- temporal 配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json`
- seed：`20260525`
- 训练步数：各 `8192`
- 输出目录：
  `experiments/m1_stage1_temporal_evidence_20260602/`

## 训练结果

两条训练均完成并保存 `final_model.zip`：

- reactive：`experiments/m1_stage1_temporal_evidence_20260602/reactive_seed20260525/final_model.zip`
- temporal：`experiments/m1_stage1_temporal_evidence_20260602/temporal_seed20260525/final_model.zip`

bootstrap 确认：

- reactive 使用 `temporal_history_len=1` 与 `TransformerExtractor`；
- temporal 使用 `temporal_history_len=16` 与 `TemporalTransformerExtractor`；
- 两者均走 `WorldBatchVecEnv`、compiled observation / reward runtime、CUDA。

## 固定模型诊断

使用 `tools/diagnostics/air_combat_stage0_process_probe.py --mode model`，
每个模型跑 `3` 个 deterministic episode：

| 模型 | termination | 平均步数 | 平均奖励 | release_total | fire_switch_total | damage_reports |
|---|---:|---:|---:|---:|---:|---:|
| reactive | `combat_timeout: 3` | `2400.0` | `0.0` | `0` | `0` | `0` |
| temporal | `combat_timeout: 3` | `2400.0` | `0.0` | `0` | `0` | `0` |

使用 `--stochastic` 每个模型跑 `3` 个 episode：

| 模型 | termination | 平均步数 | 平均奖励 | release_total | fire_switch_total | damage_reports |
|---|---:|---:|---:|---:|---:|---:|
| reactive | `failfast_deep_stall: 3` | `462.33` | `-165.54` | `0` | `0` | `0` |
| temporal | `failfast_deep_stall: 3` | `714.0` | `-399.97` | `0` | `0` | `0` |

补充 `600` 步 deterministic action-stat probe：

| 模型 | radar_mean / max | master_mean / max | fire_mean / max |
|---|---:|---:|---:|
| reactive | `0.01879 / 0.01885` | `0.01856 / 0.01858` | `0.01865 / 0.01865` |
| temporal | `0.01720 / 0.01722` | `0.01811 / 0.01814` | `0.01803 / 0.01812` |

## 解释

- S1 live damage 链路已恢复，range-gate 固定脚本能稳定产生 damage report；
- 但本轮 8192-step PPO 训练后，deterministic 策略仍未打开 radar/master/fire；
- stochastic 采样也没有产生武器释放，且暴露出 deep-stall 早停；
- action-stat probe 显示三个武器开关动作均值约 `0.018`，距离 `0.5` 开关阈值很远；
- 因此本轮不能声明 temporal window 改善了重复发射或发射策略；
- 当前更像是动作可达性、奖励探索和飞行稳定性仍挡在武器使用之前。

## 下一步

M1-A4 应继续停留在路径 A，而不是释放 M2：

- 继续使用 action-distribution 诊断记录 `radar_active/master_arm/fire_weapon` 原始动作均值与最大值；
- 对 S1 增加更短的 weapon-employment shaping 或 curriculum warm-start，使模型先学会打开武器链路；
- 以同样 seed 规则跑 32k/64k resume，只在出现实际 fire/release 后再比较重复发射和发射间隔；
- 保留 fixed range-gate 诊断作为 damage-chain control，避免把“没有学会开火”误判为杀伤模型问题。
