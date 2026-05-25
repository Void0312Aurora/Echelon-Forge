# M2 Causal Transformer HMoE 任务簇 - 2026-05-25

状态：held，等待 M1 release vote。

## 决策

M2 是正式目标架构，但不是当前立即实现项。它必须由 M1 的 temporal window
证据触发，避免在尚未证明时间信息有效前大规模改写 PPO 训练链。

## 目标形态

目标不是给当前 observation 增加更多字段，而是让训练样本本身保持时间序列：

```text
rollout: (T, N_env, observation/action/reward/done)
sample:  (B, L, observation/action/advantage/return/mask)
model:   causal attention over <= t
loss:    masked PPO loss over valid timesteps
```

## 最小技术包

- sequence rollout buffer；
- causal temporal extractor；
- temporal HMoE policy；
- sequence-aware AdaptiveKLPPO sibling；
- world-batch reset/mask 兼容；
- stage-0 air-combat smoke config；
- profile 与对比报告。

## 关键设计问题

1. 序列长度 `L` 如何选择？
   - stage-0 可从 16/32 起步；
   - BVR 或 missile time-of-flight 相关任务可能需要 64+。
2. action token 如何进入模型？
   - 上一步 action 作为 timestep token；
   - 或把 action history 与 observation token 分离编码。
3. event token 如何进入模型？
   - 发射事件、导弹在飞、命中/失效、RWR cue 应有明确 provenance。
4. value head 是否全序列计算？
   - 首版建议全序列 masked value loss，避免只训练 last token。
5. HMoE route 是否逐 timestep 计算？
   - 首版应逐 timestep route，避免 sequence 内任务状态变化被抹平。

## 释放门

M2-C0 释放必须引用 M1 文档中的证据：

- M1 temporal HMoE 对 reactive baseline 的对比；
- 至少一个稳定改善指标；
- 没有由环境侧战术记忆板造成的伪改善；
- M1 剩余限制需要 C 路径解决。

## 推荐验证

M2 实现后至少需要：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/rl/test_sequence_rollout_buffer.py \
  tests/models/test_causal_temporal_transformer.py
```

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py \
  tests/world_batch/test_world_batch_runtime.py
```

以及一个短程 air-combat PPO probe，用于记录 reactive / M1 / M2 的同预算对比。

