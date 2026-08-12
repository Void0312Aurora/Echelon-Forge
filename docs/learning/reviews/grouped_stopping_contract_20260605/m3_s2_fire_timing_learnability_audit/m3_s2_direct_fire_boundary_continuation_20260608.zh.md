# M3-S2 Direct Fire-Boundary Continuation 2026-06-08

状态：`behavior improved / still held`。

## 问题

在 `2026-06-07` direct fire-boundary 接线修复之后，如果从 r3 final
checkpoint 继续训练，是否能在不改变 A3/A5 合法性、`air_combat_hybrid_v1`、
active M3-S2 config 或杀伤模型的情况下，让 deterministic learned policy 产生实际发射？

## 方法

本轮使用 r3 final model 初始化参数，但写入独立实验目录：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_direct_fire_boundary_initfrom_8k_20260608_r1 \
  --init_from experiments_tmp/m3s2_direct_fire_boundary_8k_20260607_r3/final_model.zip \
  --n_envs 1 \
  --torch_threads 1 \
  --seed 20260608 \
  --diagnostics \
  --diagnostics_every 2048
```

结果：训练完成 `8192` steps。

Artifacts：

- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/m3s2_stochastic_probe.json`
- `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/nonfinite_probe_report.json`

## 训练观察

- direct fire-boundary update 继续 live；当 support rows 存在时，训练表持续记录
  `m3s2/fb_*` metrics。
- boundary crossing 仍不稳定。例如：
  - step `1024`：`fb_cross_ratio = 0.703`、`fb_cross_in_window_ratio = 1.0`；
  - step `1536`：`fb_cross_ratio = 0.91`、`fb_cross_in_window_ratio = 0.914`；
  - step `6144`：`fb_cross_ratio = 0.73`、`fb_cross_in_window_ratio = 0.957`；
  - step `7936`：`fb_positive_count = 168`，但 `fb_cross_count = 0`。
- diagnostics step `6144` 时，event head 已经跨过 deterministic event mode：
  `diag/pi_event_fire_p_mean = 0.517` 且 `diag/pi_event_mode_fire_frac = 1`。
  同一 diagnostics 点仍记录 `diag/action_fire_weapon_frac = 0` 与
  `diag/a5_fire_once_requested_count = 0`。
- final diagnostics step `8192` 时，event head 仍在 open-window 阈值之上：
  `diag/pi_event_fire_p_mean = 0.634` 且 `diag/pi_event_mode_fire_frac = 1`；
  callback 窗口中 `diag/action_fire_weapon_frac = 0` 与
  `diag/a5_fire_once_requested_count = 0` 仍未改变。

## Learned-Policy Probes

Deterministic probe：

- `first_release_step = 423`
- `fire_once_requested_count = 1`
- `fire_once_accepted_count = 1`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `effects_event_count = 1`
- `damage_report_count = 1`
- `last_effect_miss_distance_m = 6.0240553390109595`
- `last_damage_system_health_delta = 0.0`
- `last_damage_loss_state = combat_capable`
- `final_missiles = 3`
- `final_target_health = 40.0`

Stochastic probe：

- `first_release_step = 290`
- `fire_once_requested_count = 2`
- `fire_once_accepted_count = 1`
- `fire_once_rejected_count = 1`
- `fire_once_rejected_reason_counts = {"weapon_not_ready": 1}`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `effects_event_count = 0`
- `damage_report_count = 0`
- `final_missiles = 3`
- `final_target_health = 40.0`

## 判定

这是 active M3-S2 证据中第一次看到 deterministic learned policy 执行一次合法授权
release。相对 `2026-06-07` r3 的 `0` release，这是明确的行为进展。

但它仍不能作为 learned fire-timing closure 验收：

- deterministic release 仍只是单 seed、单 episode probe；
- stochastic probing 仍产生一次额外 `weapon_not_ready` rejected request；
- quality-window timing 仍不干净，因为 stochastic release 发生在任何 recorded
  quality-window rows 之前；
- deterministic shot 记录了 effects 和 damage report，但没有 health drop，也没有
  mission/mobility/sensor kill；
- 当前 damage result 必须留在 A8 边界内：它是非权威 effects-chain observation，
  不是 Pk 或 AIM-120C kill claim。

下一步应把本轮标为 `behavior improved / held`：保留 direct fire-boundary owner，
继续检查 event-mode 到 action-pulse 的 diagnostics gap、stochastic rejected-request
路径和 post-release effect quality，同时不削弱 A3/A5 release legality。
