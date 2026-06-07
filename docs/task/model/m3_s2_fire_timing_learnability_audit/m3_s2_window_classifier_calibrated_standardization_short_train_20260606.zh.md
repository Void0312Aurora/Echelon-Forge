# M3-S2 窗口分类器校准标准化短训

日期：2026-06-06

状态：负向集成证据；行为仍 held。

## 问题

上一轮 observation-replay classifier 暴露出一个分裂：训练 replay batch 上正负 logit 可以分开，
但 saved-policy deterministic probe 仍不发射。本切片验证失败是否来自 classifier input
standardization 每个 auxiliary step 都由随机 replay batch 刷新，导致保存后的坐标系漂移。

## 本轮改动

- 为 M3-S2 window classifier standardization 增加确定性的 latest-balanced replay calibration batch。
- 每次 auxiliary update 只在第 0 步刷新一次 classifier input standardization，
  后续 separate update steps 不再反复改坐标系。
- calibration batch 限制为 `m3s2_window_classifier_replay_batch_size`。
  首次全 capacity calibration 会把数千条 observation 一次送入 temporal transformer，
  并触发 CUDA `invalid configuration argument`。

## 证据

聚焦测试：

```text
./.venv/bin/python -m pytest \
  tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_m3s2_window_classifier_replay_calibration_is_latest_balanced_population \
  tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_m3s2_window_classifier_replay_balances_single_class_rollouts -q

2 passed
```

完整 8k 运行：

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/
```

训练末段 replay batch 仍显示局部分离：

- `m3s2/window_classifier_positive_logit_mean ~= 2.25`
- `m3s2/window_classifier_negative_logit_mean ~= -3.06`
- `m3s2/window_classifier_accuracy ~= 0.921`

但固定轨迹 chain probe 对最后 checkpoint 与 final model 均失败：

- `checkpoints/model_8192_steps.zip`
  - current quality logit mean：`-9.495816`
  - current quality boundary count：`0 / 1040`
  - fresh standardized linear probe：通过，quality `1040 / 1040`，prewindow `0 / 840`
  - verdict first breakpoint：`m3_head_optimization_conditioning`
- `final_model.zip`
  - current quality logit mean：`-9.902827`
  - current quality boundary count：`0 / 1040`
  - fresh standardized linear probe：通过，quality `1040 / 1040`，prewindow `0 / 840`
  - verdict first breakpoint：`m3_head_optimization_conditioning`

`final_model.zip` 的 deterministic environment probe：

- `release_count = 0`
- `a7_quality_window_step_count = 1080`
- `a7_quality_window_m3_window_classifier_logit_mean = -9.852545`
- `policy_event_mode_fire_once_count = 0`

## 解释

确定性 standardization calibration 移除了一个随机坐标漂移来源，但没有修复 learned
executable boundary。直接在同一 fixed hold-trajectory latent 上训练 fresh head 仍能快速拟合，
说明 representation 与 adapter 仍是充分的。

剩余失败仍是在线优化合同：auxiliary window classifier 能拟合 sampled replay batch，
却没有在 deterministic executable trajectory 上保持同一边界。这已经不适合再解释为
缺少 label、缺少观测信号、C2/ROE mask 问题或 action adapter transport 问题。

后续定位进一步收紧了这一判断：保存的 `m3_window_classifier_input_mean/std`
buffer 本身就是断点。在固定 `model_event_hold` 轨迹上，保存 buffer 下 quality rows
边界 crossing 为 `0 / 1080`；只在 fixed batch 上重算这些 buffer，不改变 classifier
权重，quality crossing 立刻升至 `1053 / 1080`。参见
[m3_s2_window_classifier_standardization_contract_probe_20260606.zh.md](m3_s2_window_classifier_standardization_contract_probe_20260606.zh.md)。

## 结论

继续在当前 online auxiliary head 上调系数意义有限。下一模型合同切片应先修复
classifier standardization contract：要么从 executable path 移除 mutable population
standardization，要么在 deterministic evaluation 使用的同一 execution-support
分布上校准并冻结它。
