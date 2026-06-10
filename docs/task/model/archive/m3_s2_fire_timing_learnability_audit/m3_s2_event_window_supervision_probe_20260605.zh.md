# M3-S2 Event-Window Supervision Probe - 2026-06-05

父级：[README.zh.md](README.zh.md)。

状态：`held evidence`；实现路径已接通，行为未验收。
collection-support 修复结果见 2026-06-06 support-preserving follow-up。

## 问题

grouped window-level hazard 目标能否直接训练 executable hybrid `fire_once`
event logits，而不是只训练 auxiliary stopping head 或 credit head？

本次测试目标不是单个硬编码最佳发射步，而是窗口合同：

- 抑制 prewindow fire mass；
- 在 quality window 内放置至少一次 event；
- 通过 delay penalty 偏好 quality window 较早部分；
- 通过 deadline penalty 要求 deadline 前有概率质量；
- 依赖既有 one-shot/C2/ROE state machine 抑制重复发射。

## 实现

代码与配置：

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - 为 grouped survival/event-mass loss 增加 `window_delay_coef`、
    `window_deadline_coef` 与 `window_deadline_steps`；
  - 记录 `mean_p_deadline` 与 `mean_quality_delay`。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 增加 `m3s2_event_window_*` hyperparameters；
  - 复用 M3-S1 grouped sidecar，但 logits 来自
    `policy.get_distribution(obs).fire_event_logit_delta()`；
  - 在 separate-update mode 下只更新 executable event-policy path。
- `python/rl/support/nonfinite_probe.py`
  - 在 non-finite probe monkey patch 启用时，同步 M3-S2 sidecar collection、
    auxiliary update 与 logger path。
- Active config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`

## 验证

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_auxiliary_training_updates.py
```

结果：pass。

```bash
pytest tests/policy/test_grouped_stopping_loss_contracts.py -q
pytest tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_air_combat_training_entry_contracts.py -q
```

结果：

- `9 passed`
- `23 passed`
- `16 passed`

HMoE 测试包含一个安装 `NonFiniteTrainingProbe` 的回归用例，用于验证
`m3s2/event_window_loss` 会被记录，且 executable event head 会发生变化。

## 短训

命令：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_event_window_8k_20260605_r2
```

Artifacts：

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/final_model.zip
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_stochastic_probe.json
```

训练观察：

| Step | Window groups | Window logit mean | Window mass | Deadline mass | Grad norm |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2048 | 0 | 0.000 | 0.000 | 0.000 | 7.567 |
| 3072 | 1 | -6.247 | 0.332 | 0.110 | 21.615 |
| 4096 | 1 | -5.992 | 0.398 | 0.137 | 20.607 |
| 5120 | 1 | -5.624 | 0.142 | 0.142 | 22.187 |
| 6144 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| 7168 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8192 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

路径已接通：M3-S2 产生了非零 loss 与梯度；当 quality-window groups 存在时，
window event logit 从约 `-6.25` 上升到约 `-5.62`。但它仍未跨过 deterministic
boundary：`boundary_cross_count` 全程为 `0`。

## Learned-Policy Probe

deterministic probe：

- `first_release_step = null`
- `release_count = 0`
- `fire_mask_open_step_count = 1880`
- `a7_quality_window_step_count = 1080`
- `policy_event_prob_fire_once_max = 0.00556`
- `policy_event_mode_fire_once_count = 0`
- `a7_quality_window_event_fire_prob_mean = 0.00555`
- `final_missiles = 4`
- `final_target_health = 40.0`

stochastic probe：

- `first_release_step = 14`
- `release_count = 1`
- `fire_mask_open_step_count = 11`
- `a7_quality_window_step_count = 0`
- `effects_event_count = 0`
- `damage_report_count = 0`
- `final_missiles = 3`
- `final_target_health = 40.0`

stochastic release 因而是 early low-probability sample，不是 learned
quality-window release。

## 判定

M3-S2 event-window supervision 已实现，并且能够到达 executable event logit
path。但它不能作为行为解法验收。

剩余失败比之前更明确：

- actor 能接收到 direct window-level gradients；
- supported window groups 存在时，这些梯度会轻微抬升 fire logit；
- rollout 后半段 support 消失，logit 仍远低于 deterministic fire boundary；
- learned deterministic policy 在 `1080` 个 quality-window steps 下仍 timeout 无发射。

这指向更深的 support/transport/training-contract 问题，而不是仅仅缺少 direct actor loss。
后续候选工作应优先维持 supported quality-window rows，或把 learned stopping decision 转为
executable low-high-low pulse，再考虑把长记忆作为第一修复。

## 后续

维护 follow-up：
[m3_s2_support_preserving_collect_probe_20260606.zh.md](m3_s2_support_preserving_collect_probe_20260606.zh.md)。

该探针实现了 support-preserving collection，并确认 training-support collapse 可以被阻断：
whole-window shield 在 8k run 中保持 `grouped_active_group_count = 4`，并阻止 collection
阶段出现 accepted rollout events。但行为判定没有改变：deterministic probing 仍记录 `0`
releases，且 `boundary_cross_count` 仍为 `0`。
