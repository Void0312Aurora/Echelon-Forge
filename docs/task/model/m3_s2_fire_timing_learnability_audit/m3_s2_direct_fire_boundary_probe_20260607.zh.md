# M3-S2 Direct Fire-Boundary Probe 2026-06-07

状态：`behavior held / wiring fix accepted`。

## 问题

在不丢弃 HMoE、不替换 PPO、不改变 `air_combat_hybrid_v1` 与 A5 runtime
fire gate 的前提下，active M3-S2 config 能否让现有 `hybrid_event_head`
成为直接的 executable fire-boundary owner？

## 改动

- active M3-S2 config 关闭 M3 stopping-head 与 window-classifier event adapter。
- 直接用 `hybrid_event_head` 接收 M3-S2 fire-boundary auxiliary update；监督目标读取
  final executable fire-event logit delta，而不是旁路 head。
- `NonFiniteTrainingProbe.traced_train()` 现在也会运行并记录同一 direct fire-boundary
  update。修复前，active 短训默认启用 nonfinite probe，因此新 update path 被旧的
  patched train 静默绕过。
- fire-boundary logger key 改为短前缀 `m3s2/fb_*`，避免 SB3 human logger 截断碰撞。

## 验证

聚焦测试：

```bash
python3 -m pytest -q \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_air_combat_active_training_entries.py
```

结果：`93 passed in 37.00s`。

短训：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python3 train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_direct_fire_boundary_8k_20260607_r3 \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260607 \
  --diagnostics \
  --diagnostics_every 2048
```

结果：训练完成 `8192` steps。

Artifacts：

- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/final_model.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_2048_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_4096_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_6144_steps.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/checkpoints/model_8192_steps.zip`

## 观察

接线修复是真实生效的：

- 从 step `512` 起，event 文件中出现 `m3s2/fb_*` tags。
- step `512` 记录 `m3s2/fb_active_count = 255`、
  `m3s2/fb_negative_count = 255`、`m3s2/fb_grad_norm = 0.654093`。
- 在含 positive-window 的 updates 中，`m3s2/fb_grad_norm` 多次达到约
  `1.36e3` 到 `1.40e3`，证明 direct boundary update 已经参与训练。

行为仍然 held：

- step `4096` 时 fire mask 打开，`diag/pi_event_fire_p_mean = 0.373841`；
  相比先前未生效训练的近零值已经明显上升，但 `diag/pi_event_mode_fire_frac = 0`。
- step `6144` 时 fire mask 打开，`diag/pi_event_fire_p_mean = 0.489228`，
  仍略低于 deterministic mode 阈值。
- step `8192` 时 fire mask 仍打开，但 `diag/pi_event_fire_p_mean = 0.0238934`；
  后续负样本较多的 updates 又把 boundary 拉回保守侧。
- 所有 diagnostics 点均记录 `diag/a5_fire_once_requested_count = 0`、
  `diag/a5_release_executed_count = 0`、`diag/action_fire_weapon_frac = 0`。

sidecar target distribution 仍不稳定：

- positive rows 间歇出现：例如 step `768`、`1024`、`1536`、`3840` 为 `225`，
  step `4096` 为 `206`，多个 negative-only update 为 `0`，最终 step `8192` 为 `165`。
- boundary crossing 只是瞬时出现：`m3s2/fb_cross_ratio` 在 `1536` 为 `1`，
  在 `4096` 为 `0.925781`，在 `6400` 为 `0.058594`，最终 `8192` 回到 `0`。
- positive 与 negative logit means 经常一起移动，例如 step `4096` 附近 positive
  为 `0.057552`、negative 为 `-0.094755`。这说明当前更新尚未形成稳定的
  prewindow-versus-quality discriminator。

## 判定

接受接线修复，不接受行为验收。

先前短训“无效果”的直接原因已经明确：`NonFiniteTrainingProbe` 用旧的 copied train
覆盖了模型的 `train()`，没有调用 direct fire-boundary auxiliary update。修复后，
active 训练确实记录 direct-boundary metrics，并把 executable fire probability 提升了
两个数量级。

但模型仍未稳定跨过 deterministic fire threshold。剩余问题不再是“update path 缺失”，
而是 online target/support distribution 与 boundary calibration 仍会在 positive-heavy、
negative-heavy 和 empty-support batches 之间反复拉扯 direct event head。
