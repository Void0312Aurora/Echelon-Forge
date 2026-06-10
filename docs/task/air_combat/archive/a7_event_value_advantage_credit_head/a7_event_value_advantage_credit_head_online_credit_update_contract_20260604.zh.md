# A7 在线 Credit 更新合同

状态：`2026-06-04` implementation contract 通过；A7 行为仍 held。

父级：[README.zh.md](README.zh.md)。

## 目的

`A7-EVC-U` 已将 online blocker 定位到更新合同：A7 credit 被放在同一次 PPO
backward、同一次 global gradient clip、同一套 actor/features representation 与同一次
optimizer step 中训练。这会让本地可分离的 credit-head 信号与 PPO value loss 以及
delta-alignment representation gradients 竞争。

本 slice 实现 U 选定的有界修复：为 A7 value credit 提供独立的
credit-head-only update lane，用独立 gradient clip budget 保护它，并在 learned
credit sign 尚未为正时继续 gate policy delta alignment。

## 实现

代码变更：

- `python/rl/policy_algo/policies.py` 增加
  `HierarchicalMoEExecutionPolicy.get_hybrid_event_credit_values(obs,
  detach_latent=False)`。当 `detach_latent=True` 时，actor features 与 latent
  actor state 在 `no_grad` 下计算，随后只有 `hybrid_event_credit_head` 接收梯度。
- `python/rl/policy_algo/ppo_adaptive_kl.py` 增加：
  - `a7_event_credit_delta_align_positive_only`；
  - `a7_event_credit_separate_update_enabled`；
  - `a7_event_credit_separate_update_max_grad_norm`；
  - `_first_event_credit_head_parameters()`；
  - `_first_event_credit_separate_value_update()`。
- 独立 value update 使用 detached latent features 调用
  `_first_event_credit_loss()`，启用 A7 value/projection-value coefficients，
  并关闭 delta-align。它只更新 `hybrid_event_credit_head`，使用独立 clip budget，
  并在 update 前后清空 optimizer gradients。
- 主 PPO 路径在 separate update 启用时，以 `0.0` 的
  A7 value/projection-value coefficients 调用 `_first_event_credit_loss()`。
  Delta alignment 仍保留在 PPO 路径中，但
  `a7_event_credit_delta_align_positive_only=true` 将其限制到 positive credit
  signs。
- `python/rl/support/nonfinite_probe.py` 镜像同一 separate-update 路径。因为 active
  probe config 会 monkey-patch `model.train()`，缺少该镜像会让被验证的训练入口静默绕过
  修复。

Active A7 configs 现在启用：

```json
"a7_event_credit_delta_align_positive_only": true,
"a7_event_credit_separate_update_enabled": true,
"a7_event_credit_separate_update_max_grad_norm": 0.5
```

## 验证

Focused structural gates：

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py python/rl/support/nonfinite_probe.py tests/policy/test_auxiliary_training_updates.py
pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_separate_credit_update_only_writes_credit_head -q
pytest tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits tests/policy/test_event_head_update_contracts.py -q
pytest tests/training/test_event_timing_training_config_contracts.py::EventTimingTrainingConfigContractTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_c2_roe_a7_event_credit_probe_is_separate_from_a6_launch_window_baseline -q
```

最终验证：compileall 与两个 active-config JSON parse gates 通过；focused
separate-update 与 nonfinite-probe tests 为 `2 passed`；policy/update-strength
tests 为 `7 passed`；active-config tests 为 `2 passed`；最终 combined focused
rerun 为 `111 passed`；diff whitespace check 通过。

短训观察：

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config experiments_tmp/a7_separate_update_8k_v2_config_20260604.json \
  --run_name a7_separate_update_8k_v2_20260604 \
  --output_base experiments_tmp \
  --seed 7
```

观测：

- training 完成 `8192` steps；
- `stderr` 为空，`final_model.zip` 存在；
- `a7/evc_separate_update_enabled=1.0`；
- `a7/evc_separate_update_grad_norm_mean` 早期非零（clip 前 `2.365`），证明独立
  lane 是 live 的；
- `a7/event_credit_advantage_mean` 从早期约 `-0.121` 改善到 final 约
  `-0.0583`；
- `a7/event_credit_delta_align_loss=0.0`，因为 positive-only gate 在 learned
  credit sign 仍为负时正确阻止 policy coupling；
- `train/value_loss` 从约 `9516` 降到约 `0.475`。

最终固定批 credit probe：

```bash
python tools/diagnostics/a7_credit_head_offline_fit_probe.py \
  --model experiments_tmp/a7_separate_update_8k_v2_20260604/final_model.zip \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 0 \
  --eval_batch_size 512 \
  --json_out experiments_tmp/a7_separate_update_8k_v2_final_credit_probe_20260604.json
```

观测：fixed batch 含 `1356` 个 legal-open positives，但
`legal_open_quality_positive_advantage_mean=-0.05257667228579521`，positive sign
fraction 仍为 `0.0`。

最终 process probe：

```bash
python tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config experiments_tmp/a7_separate_update_8k_v2_config_20260604.json \
  --mode model \
  --model experiments_tmp/a7_separate_update_8k_v2_20260604/final_model.zip \
  --episodes 2 \
  --max_steps 640 \
  --device auto \
  --json_out experiments_tmp/a7_separate_update_8k_v2_process_probe_20260604.json
```

观测：`release_count=0`，`fire_once_requested_count=0`，one-shot legality
平凡保持。Quality-window credit advantage 仍为负，两个 episode 的 quality mean
约为 `-0.0542` 与 `-0.0521`。

实验输出保留在 `experiments_tmp/`，不得 staging。

## 解释

V 修复在结构上有效：

- credit-head-only update lane 是 live 的；
- nonfinite probe 的 monkey-patched training loop 也保留该路径；
- 主 PPO value/global-clip 路径不再拥有 A7 value credit；
- 当 credit signs 仍为负时，policy delta alignment 被正确 hold。

但行为 blocker 尚未解决：

- legal-open credit advantage 相比旧 8k endpoint 有明显改善，但没有越过零；
- deterministic policy 仍选择 `hold`；
- 训练早期后，active A7 update windows 可能归零。因此当前剩余问题已转向：
  protected update contract 生效后，credit-sample/update-window 可用性或 curriculum
  scheduling 为什么仍不足。

因此 V 只能作为 online credit-update repair 被接受。A7 first-shot behavior 仍 held。

## 下一边界

不要把下一步重新收缩为 coefficient-only tuning。下一有界工作应解释 protected
update 已接通后 active positive update windows 为什么消失，随后再决定修复属于
curriculum sampling、replay/fixed positive batches、adaptive label scheduling，还是更大的
training-loop contract。
