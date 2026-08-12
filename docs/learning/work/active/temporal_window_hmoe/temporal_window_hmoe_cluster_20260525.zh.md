# M1 观测窗口 HMoE 任务簇 - 2026-05-25

状态：`M1-A2/A3` 已完成首版实现并通过聚焦测试；`M1-A4` 已进入 Stage-0 /
Stage-1 reactive-vs-temporal 证据采集。

## 决策

M1 是路径 A 的验证包，不是最终架构。它的唯一任务是回答：

在不改写 PPO 算法的前提下，把短时间窗口作为 observation 暴露给 HMoE，是否能改善
`1v1` 空战武器使用中的重复发射、动作可达性和策略稳定性？

如果答案是肯定的，M1 为 M2 路径 C 提供证据；如果答案是否定或不清楚，M2 不启动。

## 最小实现目标

首个实现目标为非视觉 temporal HMoE：

- `history_len` 可配置；
- reset 时用零帧或首帧填充历史；
- step 后推进历史，并同步 previous action；
- `done` 后清空对应 env/handle 历史；
- world-batch 路径与单 env 路径 shape 一致；
- extractor 输出仍是单个 `features_dim` embedding，供现有 HMoE policy 使用。

## 推荐文件面

预计写入面：

- `gym_envs/universal_env.py`
- `gym_envs/universal_env_parts/observations.py`
- `python/rl/runtime/world_batch_vec_env.py`
- `python/models/transformer.py` 或新增 `python/models/temporal_transformer.py`
- `python/env_config.py` 或训练 config 解析注册点
- `examples/config/training/active/air_combat/*.json`
- `tests/runtime/air_combat/*`
- `tests/world_batch/*`

M1 不应触碰：

- `src/systems/combat/*` 战术记忆；
- `src/core/engine/simulation_kernel_weapon_api.cpp` 武器物理与发射判定；
- `python/rl/policy_algo/ppo_adaptive_kl.py` 的 sequence-native 训练逻辑；
- `python/rl/policy_algo/device_dict_rollout_buffer.py` 的 sequence sampling。

## 任务流

| 流 | 状态 | 目标 | 关键问题 | 验证 |
|----|------|------|----------|------|
| `A1 Shape Contract` | accepted | 定义 temporal observation space 与 config 字段。 | 采用显式 `*_history` keys，默认 `temporal_history_len=1` 不改变旧空间。 | observation space probe |
| `A2 Runtime History` | accepted | 在单 env 与 world-batch 中维护历史。 | reset/done/terminal obs 一致性。 | runtime shape tests |
| `A3 Temporal Extractor` | accepted | 实现 temporal attention extractor。 | 复用单帧 embedding 且不破坏旧 checkpoint。 | forward + non-finite tests |
| `A4 Air-Combat Probe Config` | in evidence | 增加 stage-0 temporal config。 | 与 reactive baseline 公平对比。 | short PPO smoke |
| `A5 Evidence Review` | held | 决定是否释放 M2。 | 改善是否来自策略历史。 | metrics report |

## 2026-05-25 首轮实现记录

已落地内容：

- 新增 opt-in 观测历史：`instruments_history`、`contacts_history`、`rwr_history`、`mission_history`、`proprio_history`；
- `UniversalEnv`、`WorldBatchVecEnv`、`CooperativeWorldBatchVecEnv` 均接受 `temporal_history_len`，默认值为 `1` 时不暴露历史键；
- world-batch compiled/legacy 观测路径都附加历史窗口；
- CUDA policy observation bridge 会把历史键交给策略；
- 新增 `TemporalTransformerExtractor`，每帧复用当前非视觉 token 结构，再做 causal temporal attention；
- 新增 stage-0 temporal 训练配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json`。
- 在 S1 live damage 链路恢复后，新增 stage-1 temporal 训练配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json`。

验证结果：

- `py_compile` 覆盖 temporal history、world-batch/cooperative runtime、transformer、训练入口；
- `tests/runtime/core/test_env_config.py`：`7 passed`；
- `tests/policy/test_execution_policy_surface.py -k "temporal or transformer"`：`4 passed, 10 deselected`；
- `tests/world_batch/test_world_batch_vec_env.py -k "temporal_history"`：`2 passed, 62 deselected`；
- `tests/training/test_training_bootstrap_contracts.py tests/runtime/core/test_env_config.py`：`8 passed`；
- `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py -k "initializes or reset or observation"`：`4 passed, 26 deselected`；
- stage-0 temporal PPO smoke 完成 `4096` timesteps，final model 保存到
  `experiments/temporal_stage0_smoke_20260525/final_model.zip`；
- test-only deterministic rollout 使用同一 world-batch temporal 配置加载 final model 并执行 `1000` 步，无 runtime/shape/non-finite 报错。
- 2026-06-02 Stage-1 temporal 入口验证：
  `tests/training/test_air_combat_training_entry_contracts.py` 通过，覆盖 reactive/temporal 配置配对与 train bootstrap；
  `tests/policy/test_execution_policy_surface.py -k "temporal or transformer"` 通过；
  `tests/world_batch/test_world_batch_vec_env.py -k "temporal_history"` 通过；
  使用 Stage-1 temporal 配置运行 range-gate 固定诊断，单枚导弹产生 `effects_event_count=1`、
  `damage_report_count=1`、`projected_hitbox_count=3`、`component_hit_count=4`、
  `system_health_delta=-0.449619135218419`。

当前解释：

- “能正常训练”已成立：temporal observation、HMoE、CUDA rollout buffer、world-batch compiled runtime 链路可达；
- “行为已经改善”尚未成立：短烟测末尾 value loss 有明显抬升，test-only rollout 的粗粒度奖励打印仍为 `0.00`，需要后续与 reactive baseline 做同 seed、同指标对照；
- Stage-1 的 S1 probe 现在应优先记录 live-fire damage 是否稳定出现，以及 temporal window 是否改善重复发射、发射间隔和固定诊断指标；
- 2026-06-02 第一轮 Stage-1 8192-step 同 seed 对照记录为
  [M1-A4 Stage-1 短程证据](m1_a4_stage1_evidence_20260602.zh.md)：reactive 与 temporal 均能训练和加载，
  但 deterministic 策略均为 `combat_timeout`、`release_total=0`，stochastic 策略均为
  `failfast_deep_stall`、`release_total=0`，action-stat probe 显示武器开关动作均值约 `0.018`；
- 因此 M2 路径 C 仍保持 held，等待 A4 evidence review。

## 指标

建议记录：

- episode reward；
- missile launch count；
- missiles in flight over time；
- fire action high-rate；
- repeated launch interval；
- invalid/no-target fire attempts；
- target track continuity；
- ammo remaining；
- terminal reason；
- non-finite probe 是否触发。

## M2 释放门

只有满足以下条件时，M2 才能从 held 进入实现：

- M1 temporal probe 至少在一个 stage-0 或 stage-1 指标上优于 reactive baseline；
- 优势在多个 seed 或多次短程 probe 中不是明显偶然；
- 没有依赖环境侧战术 latch 获得改善；
- 文档明确路径 C 要解决的 M1 剩余限制。
