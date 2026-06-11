# A7 Post-X Learned Observation

状态：`2026-06-05` 已完成为 bounded learned-policy evidence；结论 held。

父级：[README.zh.md](README.zh.md)。

## 目的

`A7-EVC-X` 已在 focused tests 中修复 rollout-boundary first-event credit state：
PPO rollout chunks 现在可以携带 same-episode context，并恢复完整 episode 中存在的
shadow-quality positives。本记录用于观察 X 后 learned-policy 的真实行为，并区分三个问题：

- 修复后的训练信号是否真的进入 training；
- deterministic policy execution 是否跨过 `fire_once` event-mode 门槛；
- stochastic execution 是否保持 A3/A5 one-shot legality，并产生 missile effects。

## 运行

训练命令：

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --run_name a7_cross_rollout_state_32k_20260605_r1 \
  --output_base experiments_tmp \
  --seed 7
```

输出：

- 运行目录：
  `experiments_tmp/a7_cross_rollout_state_32k_20260605_r1`
- 最终模型：
  `experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip`
- 完成 `32768` timesteps。

## 训练观察

X 修复确实进入了 learned training path。训练早期，cross-rollout carried context
恢复了此前被删失的 shadow/projection activity：

- 在 `3072` timesteps：
  `a7/evc_carried_shadow_positive_count_mean=693`，
  `a7/evc_cross_rollout_context_rows~=1024`，
  `a7/evc_cross_rollout_first_event_count_mean=699`，
  `a7/evc_proj_active_count_mean=346`，且
  `a7/event_credit_target_positive_frac=0.985`；
- 在 `5120` 到 `7168` timesteps，
  `a7/event_credit_advantage_mean` 从 `0.113` 上升到 `0.567`；
- 后续若干窗口中 legal-open source rows 仍可见，例如 `14336` 与 `15360`
  timesteps 的 `a7/evc_src_legal_open_quality_positive_count_mean=512`。

但这种改善没有稳定转化成 policy acceptance。后段窗口继续震荡：

- `20480` timesteps 的诊断窗口中 fire mask 是 open 的，
  `a6/event_fire_prob_mean_open=0.0877`，但
  `pi_event_mode_fire_frac=0`，且 `a7/evc_adv_mean_open=-0.437`；
- `30720` timesteps 时 open-window event fire probability 提升到 `0.287`，
  但 `pi_event_mode_fire_frac` 仍为 `0`，没有 release executed；
- 最终 `32768` timestep 日志为
  `a7/event_credit_active_count_mean=512`，
  `a7/event_credit_target_positive_frac=0.77`，
  `a7/event_credit_advantage_mean=-0.198`。

解释：cross-rollout credit state 已不再是当前最直接的 training-path censoring
故障。剩余失败更接近 event-mode threshold / policy execution 与后续
launch/effects coupling，而不是单纯缺失 post-boundary labels。

## 过程探针

Deterministic probe：

```bash
python tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip \
  --episodes 2 \
  --max_steps 640 \
  --device auto \
  --json_out experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/a7_cross_rollout_deterministic_probe.json \
  --csv_out experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/a7_cross_rollout_deterministic_probe.csv
```

结果：

- `2/2` episodes 均为 `0` releases。
- 最终导弹数保持 `4`。
- 目标血量保持 `40.0`。
- Open-window event fire probability 非零，但没有跨过 event-mode selection：
  mean 为 `0.2736` / `0.2439`，max 为 `0.2827` / `0.2648`。
- Deterministic rollouts 中 A7 quality-window advantage 为正：
  `0.00234` 与 `0.00994`，positive fraction 为 `1.0`。
- `policy_event_mode_fire_once_count=0`。

Stochastic probe，`4 x 640` steps：

- `4/4` episodes 都采样出恰好一次 authorized release。
- Release steps 为 `6`、`45`、`3`、`5`。
- `0` invalid attempts，`0` repeat releases，`0` shot-budget violations。
- `640` steps 内没有 effects 或 damage events。
- 目标血量保持 `40.0`。

长 stochastic probe，`2 x 2400` steps：

- `2/2` episodes 都采样出恰好一次 authorized release。
- Release steps 为 `6` 与 `43`。
- 两个 episodes 均以 `combat_timeout` 结束。
- `0` invalid attempts，`0` repeat releases，`0` shot-budget violations。
- `0` effects events，`0` damage reports。
- 目标血量保持 `40.0`；最近 geometric range 约为 `1610 m` 与 `1647 m`。

## 结论

Post-X evidence 是混合的，但不能验收：

- 正面：cross-rollout label repair 确实进入 training，且早期 A7 credit sign 改善；
- 正面：stochastic execution 在观测 probe 中保持 clean one-shot discipline；
- held：deterministic execution 仍选择 hold，记录 `0` releases；
- held：stochastic releases 仍是 near-immediate/prewindow samples，而不是学到
  quality-window first-shot timing；
- held：即使长 stochastic episodes 中单发授权 release，也没有观察到 effects/damage chain。

A7 应继续 held。下一步不应是另一轮 coefficient sweep。当前断点是：learned event
probability 与 credit 可以转正，但没有转化成 deterministic event-mode execution；
同时采样得到的 early release 没有进入可观测 missile effects/damage 链。
