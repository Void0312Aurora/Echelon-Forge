# M1-A4 Hybrid Temporal Shaped 对照证据 - 2026-06-02

状态：`needs more A`。本轮把已恢复稳定的 Stage-1 hybrid shaped 训练表面与
M1 observation-window temporal extractor 合并，并按同一 seed / 同一 32k 预算做对照。
结果证明 temporal-shaped 路径可训练、可诊断，但尚未改善 learned weapon employment；
stochastic 策略的早发与多发反而更明显。

## 设置

- 场景：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json`
- reactive shaped 配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json`
- temporal shaped 配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json`
- seed：`20260607`
- 训练步数：各 `32768`
- 输出目录：
  - `experiments_tmp/m1_s1_hybrid_shaped_pair32k_20260602/`
  - `experiments_tmp/m1_s1_hybrid_temporal_shaped_pair32k_20260602/`

## 合并内容

temporal shaped 条目保留 hybrid shaped 的训练恢复条件：

- `action_mode=air_combat_hybrid_v1`；
- training-shaped Stage-1 场景与 release shaping；
- stable-flight residual wrapper 只作用于飞控轴 `[0, 1, 2, 3]`；
- combat commands 不锁定、不 snap；
- `log_std_init=-2.0`。

它只额外启用：

- `temporal_history_len=16`；
- `TemporalTransformerExtractor`；
- frame encoder depth 与 shaped reactive 保持 `n_layers=3`，并增加
  `temporal_n_layers=2`。

## 验证

配置与 bootstrap：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_air_combat_training_entry_contracts.py
# 7 passed, 6 subtests passed
```

32k 训练：

| 模型 | 训练状态 | 最终诊断摘要 |
| --- | --- | --- |
| hybrid shaped | complete | `combat_timeout` window，`pitch_mean=1.64deg`，`preterm_max_abs_g=1.04`，`action_fire_weapon_frac=0` |
| hybrid temporal shaped | complete | `combat_timeout` window，`pitch_mean=1.64deg`，`preterm_max_abs_g=1.04`，`action_fire_weapon_frac=0` |

两者均没有 deep-stall / combat-loss 回归。

## 模型诊断

deterministic final model，每个模型 1 episode：

| 模型 | termination | total_reward | fire attempts | releases | invalid fire | damage reports |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| hybrid shaped | `combat_timeout` | `73.1765` | `0` | `0` | `0` | `0` |
| hybrid temporal shaped | `combat_timeout` | `73.2205` | `0` | `0` | `0` | `0` |

stochastic final model，每个模型 3 episodes：

| 模型 | termination | fire attempts | releases | invalid fire | damage reports | first release steps | min release intervals |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| hybrid shaped | `combat_timeout=2`, `combat_win=1` | `[6, 4, 2]` | `[1, 4, 2]` | `[5, 0, 0]` | `[0, 2, 0]` | `[207, 261, 933]` | `[null, 117, 816]` |
| hybrid temporal shaped | `combat_timeout=2`, `combat_win=1` | `[10, 4, 7]` | `[4, 3, 4]` | `[6, 1, 3]` | `[0, 2, 0]` | `[149, 140, 113]` | `[132, 60, 53]` |

## 解释

- M1 temporal-shaped 合并是成功的：配置能 bootstrap、world-batch runtime 能训练、
  temporal observation shape 与 extractor 没有 non-finite 或 reset 问题。
- deterministic policy 仍没有学会主动发射；这仍是 learned policy 未验收的主阻塞。
- stochastic policy 的 release 可达，但 temporal-shaped 在本轮更早开火，且重复发射更密：
  `release_count` 总数从 `7` 增至 `11`，`invalid_fire_attempt_count` 总数从 `5` 增至 `10`。
- 这轮不能支持“时间窗口已改善多发问题”的声明，也不能释放 M2。

## 下一步

M1-A4 应继续停留在路径 A，但需要改变证据采集方式：

1. 增加更直接的可观测武器状态字段审计，确认 policy window 中确实包含弹药、在飞导弹或近期发射事件等可学习证据。
2. 在 reward surface 中把“同一目标短间隔重复发射 / 已有己方导弹在飞时继续发射”的惩罚与 first-release reward 解耦，避免只奖励 release exploration。
3. 在 deterministic learned release 出现前，不把 repeated-release interval 作为 temporal 成功证据。
4. M2 sequence-native PPO 继续 held。
