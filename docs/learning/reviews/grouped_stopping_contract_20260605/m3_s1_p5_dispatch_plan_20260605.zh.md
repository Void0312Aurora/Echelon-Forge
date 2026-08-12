# M3-S1 P5 Dispatch Plan

状态：`2026-06-05` nonfinite-probe training-path 修复后，short-training
evidence 已通过。这不是 learned-policy acceptance。

父级：[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md)。

## 目的

P5 用于确认 P4 grouped stopping implementation 是否已经暴露足够证据，能够决定下一步
架构行动。它必须回答 independent stopping head 是否在正确时机推动 deterministic stop
boundary、early/prewindow mass 是否保持预算约束、no-event mass 是否可观测，以及
stochastic execution 是否仍在既有 C2/ROE 与 action masks 下保持 one-shot legal。

P5 不能变成又一轮 reward-scale 或 coefficient sweep。

## Active Packets

| Packet | Owner | Write set | Required output | Status |
| --- | --- | --- | --- | --- |
| `M3S1-P5A Diagnostics Surface` | diagnostics worker | `python/rl/policy_algo/ppo_adaptive_kl.py`；`tests/policy/test_auxiliary_training_updates.py` | focused test evidence，证明 `m3s1/*` validation metrics 在不改变 loss/reward/legality semantics 的情况下被记录。 | pass |
| `M3S1-P5B Short Training Evidence Path` | read-only explorer | none | 保守短训命令、artifacts、metrics 与 stop criteria。 | pass |
| `M3S1-P5 Integration Review` | main thread | M3-S1 docs、process probe、active probe config | 验收 worker packet，运行 focused tests，并判断是否可以开始短训。 | pass |
| `M3S1-P5C Nonfinite Probe Drift Repair` | main thread | `python/rl/support/nonfinite_probe.py`；`tests/policy/test_auxiliary_training_updates.py` | 证明 `--nonfinite_probe` 保留 M3-S1 sidecar construction、auxiliary update 与 grouped diagnostics。 | pass |
| `M3S1-P5 Short Training Run` | main thread | `experiments_tmp/` 下的 experiment outputs | 执行有边界 8k M3-S1 probe，并收集 deterministic/stochastic process probes。 | pass |

## Required Diagnostic Surface

| Diagnostic | Question answered | Acceptance role |
| --- | --- | --- |
| grouped sidecar group/row counts | grouped evidence 是否跨过 rollout flattening 与 minibatching。 | 短训前必需。 |
| grouped active group/row counts | auxiliary objective 是否在 supported windows 上训练。 | 解读 loss 前必需。 |
| boundary crossing count and in-window count | deterministic stop boundary 是否移动，以及是否在 desirable windows 内移动。 | P5 核心信号。 |
| early/prewindow event mass | 模型是否在证据支持 stopping 前花掉 stop probability。 | 必须保持在配置预算内。 |
| no-event mass | right-censored/no-window cases 是否被表示，而不是被忽略。 | 诊断 all-wait collapse 的必要项。 |
| closed-mask stop attempts | stopping head 是否在 legal masks closed 时尝试 stop。 | 只能作为 diagnostic；masks 保持权威。 |
| one-shot legality count or violation rate | stochastic execution 是否仍防止 repeated fire/stop behavior。 | learned behavior claim 前必需。 |
| stop-logit or hazard means by window kind | 新 stopping head 是否区分 desirable、prewindow 与 no-window rows。 | 帮助判断失败来自表示还是训练信号。 |

## Validation Ladder

1. P5-A code patch 后先运行 focused M3-S1 tests：

   ```bash
   python -m pytest tests/policy/test_auxiliary_training_updates.py -q -k m3s1
   ```

2. focused tests 通过后运行更宽的 adjacent gate：

   ```bash
   python -m pytest tests/policy/test_grouped_stopping_loss_contracts.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py -q
   ```

3. 只有 diagnostics 存在后，才打开带明确输出 artifacts 与步数预算的短训。不在本次
   dispatch 内执行 long formal training。

4. 短训完成后，用 process probe 的 deterministic 与 stochastic modes，把 independent
   stopping-head movement 和 executable fire-action behavior 分开。

## Worker Evidence

`M3S1-P5A Diagnostics Surface` 返回 pass，并经主线程复核：

```bash
python -m py_compile python/rl/policy_algo/ppo_adaptive_kl.py \
  tests/policy/test_auxiliary_training_updates.py
python -m pytest tests/policy/test_auxiliary_training_updates.py -q -k m3s1
git diff --check -- python/rl/policy_algo/ppo_adaptive_kl.py \
  tests/policy/test_auxiliary_training_updates.py
```

结果：

- `py_compile`：pass。
- focused M3-S1 pytest：`2 passed, 18 deselected`。
- adjacent M3-S1/HMoE pytest：
  `64 passed`。
- A6/A7 adjacent regression pytest：
  `14 passed`。
- `git diff --check`：pass。

P5-A 增加以下日志：

- `m3s1/grouped_labels_reached_loss`；
- all、desirable、prewindow、no-window 与 closed-mask rows 的 stop-logit means/counts；
- event-logit delta diagnostic mean/count，且明确只作为 diagnostic；
- boundary-cross 与 closed-mask ratios；
- rollout-level accepted-event、one-shot-violation 与 closed-mask-accepted event counts。

`M3S1-P5B Short Training Evidence Path` 作为只读 evidence 返回 pass。它最初确认当前没有
专门 M3-S1/P5 active training config。主线程随后新增一份 maintained short-probe config，
并从下列配置派生：

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json
```

维护中的 M3-S1 P5 短探针配置为：

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json
```

它保持 A7 state-completed observation 与 A7 系数不变，只打开
`policy_kwargs.m3_stopping_head_lr_scale = 5.0` 和 `m3s1_grouped_stopping_*`
auxiliary objective，并使用 8k budget。

第一条短训命令应面向 Stage-1 C2/ROE shaped scenario，并把输出写入 `experiments_tmp/`：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --run_name m3s1_p5_state_completed_8k_20260605_r1 \
  --output_base experiments_tmp \
  --seed 7 \
  --diagnostics \
  --diagnostics_every 1024 \
  --nonfinite_probe
```

相对 A7 state-completed 的 config delta 为：

- `total_timesteps = 8192` 用于第一轮 evidence run；若要 dry smoke，可临时复制后改为
  `1024`/`2048`。
- `policy_kwargs.m3_stopping_head_lr_scale = 5.0`。
- `m3s1_grouped_stopping_coef = 1.0`。
- `m3s1_grouped_stopping_early_mass_budget = 0.05`。
- `m3s1_grouped_stopping_boundary_threshold = 0.0`。
- 第一轮比较保持 A7 系数不变。

训练后，用同一份 maintained config 执行 model process probes：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip \
  --algo auto \
  --device cpu \
  --episodes 1 \
  --seed 7 \
  --max_steps 640 \
  --json_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json \
  --csv_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.csv
```

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip \
  --algo auto \
  --device cpu \
  --episodes 4 \
  --seed 17 \
  --max_steps 640 \
  --stochastic \
  --json_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json \
  --csv_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.csv
```

process probe 现在输出 M3 stopping-head diagnostics：

- row-level `policy_m3_stop_logit`、`policy_m3_stop_prob` 与
  `policy_m3_boundary_cross`；
- episode-summary level `policy_m3_boundary_cross_count` 与
  `policy_m3_first_boundary_cross_step`；
- `a7_prewindow_m3_stop_prob_cum`、
  `a7_prewindow_m3_stop_prob_mean`、
  `a7_quality_window_m3_stop_prob_mean`、
  `a7_prewindow_m3_boundary_cross_count` 与
  `a7_quality_window_m3_boundary_cross_count`。

probe/config handoff 的额外主线程检查：

```bash
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
python -m pytest tests/training/test_air_combat_training_entry_contracts.py \
  -q -k 'm3s1 or stage1_bvr_probe_bootstraps'
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json
```

结果：

- diagnostics process-probe tests：`13 passed`；
- active config M3-S1/bootstrap tests：`2 passed, 13 deselected`；
- JSON syntax check：pass。

## Short-Training Evidence

第一轮有边界短训已经完成，但不能作为 M3 learning evidence 接受：

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1
```

观测到的失败：

- `train_config_backup.json` 保留了 `m3s1_grouped_stopping_*` knobs。
- console 只出现 `m3s1/stopping_head_params/*`，没有出现
  `m3s1/grouped_*` loss/sidecar diagnostics。
- M3 stopping-head parameter norms 到 `8192` 步仍保持 0。
- deterministic probe 保持 flat：
  `policy_m3_stop_logit_mean = 0.0`、
  `policy_m3_stop_prob_mean = 0.5`、
  `policy_m3_boundary_cross_count = 640`，且 `release_count = 0`。
- stochastic probe 中 M3 仍保持 flat，但 executable action branch 在 4 个
  episode 中随机产生了 3 个 one-shot releases。

根因：

- `--nonfinite_probe` 安装的是旧 PPO surface 复制出来的 `collect_rollouts()`
  与 `train()` loops。
- 该 diagnostics path 只 attach A6/A7 labels，但没有构建
  `_m3s1_grouped_stopping_sidecar`。
- 复制出来的 `train()` loop 没有调用
  `_m3s1_grouped_stopping_auxiliary_update()`，也没有 emit
  `m3s1/grouped_*` logger keys。

修复：

- `python/rl/support/nonfinite_probe.py` 现在会 reset M3-S1 tracking state，
  在 traced rollout 中构建 grouped stopping sidecar，在 traced train 中运行 grouped
  stopping auxiliary update，并记录 M3 grouped diagnostics。
- 新增 regression coverage：
  `test_nonfinite_probe_preserves_m3s1_grouped_stopping_training_path`。

修复验收：

```bash
python -m py_compile python/rl/support/nonfinite_probe.py \
  tests/policy/test_auxiliary_training_updates.py
python -m pytest tests/policy/test_auxiliary_training_updates.py \
  -q -k 'nonfinite_probe_preserves_m3s1 or m3s1_grouped_stopping_auxiliary'
python -m pytest tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py -q
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  -q -k 'm3s1 or stage1_bvr_probe_bootstraps or model_policy_diagnostics_include_m3'
```

结果：

- `py_compile`：pass。
- targeted nonfinite/M3 pytest：`2 passed, 19 deselected`。
- adjacent HMoE/M3 pytest：`65 passed`。
- diagnostics/config focused pytest：`3 passed, 25 deselected`。

修复后的有边界短训已经完成：

```text
experiments_tmp/m3s1_p5_nonfinite_fixed_8k_20260605_r1
```

训练证据：

- `2048` 步时 M3 grouped diagnostics 已在线：
  `m3s1/grouped_stopping_grad_norm = 8.9`、
  `m3s1/grouped_stopping_loss = 15.9`、
  `m3s1/grouped_sidecar_group_count = 4`、
  `m3s1/grouped_active_group_count = 4`。
- M3 stopping-head parameters 已移动：
  `weight_norm = 0.00208`、`bias_norm = 0.00015`。
- 训练完成 `8192` 步，无 nonfinite abort，并保存 `final_model.zip`。
- final stopping-head parameters 保持非零：
  `weight_norm = 0.00454`、`bias_norm = 0.000328`。
- 后段 rollout 经常出现 `m3s1/grouped_active_group_count = 0`；此时 grouped grad
  为 0 是预期结果，并且现在已经可见，而不是静默断线。

训练后 process probes：

| Probe | Fire behavior | M3 stop output | Boundary signal |
| --- | --- | --- | --- |
| deterministic，seed 7，1 episode | `release_count = 0`，final missiles `4` | `policy_m3_stop_logit_mean = -0.02457`，`policy_m3_stop_prob_mean = 0.49386` | `policy_m3_boundary_cross_count = 0` |
| stochastic，seed 17，4 episodes | episodes `0`、`1`、`3` 各 one-shot release；无 repeated-release violation | per-episode stop-prob means `0.49389` 到 `0.49397` | 所有 episode boundary-cross count 均为 `0` |

解释：

- P5 evidence 证明 independent M3-S1 stopping head 在真实 `--nonfinite_probe`
  diagnostics training path 下可以被训练。
- process probe 现在能够区分已训练的 M3 stopping head 与 executable hybrid action branch。
- 8k probe 没有证明 learned executable fire timing：deterministic release 仍为 flat，
  stochastic release 仍主要由 sampling 产生。
- learned-policy acceptance 继续 held。后续需要判断是把 stopping head 通过 adapter
  接入执行动作、修改训练数据/window 供给，还是重新进入更深层模型分析。

## Behavior Risk

P4/P5 训练的是 independent stopping head，而 executable `model.predict()` 仍走 hybrid
event action branch。因此 P5 可以证明 M3 stopping boundary 学到，但不能直接证明
executable fire timing 学到；反过来 deterministic release 也可能在 M3 head 改善时仍然
flat。只有 adapter/probe 显式连接或比较 stopping head 与 executable action path 后，才可
解除 learned behavior held 状态。

## Stop Criteria

- 如果 diagnostics 无法在不修改 reward magnitude、C2/ROE masks 或 action legality 的情况下
  emit，则停止 P5 并重新划定范围。
- 如果 grouped labels、active rows 与 gradient norms 健康，但 boundary metrics 仍然 flat，
  则停止 P5 并回到模型分析。
- 只有 P5-A diagnostics 与 P5-B command/artifact plan 均已集成，才进入短训。

## Current Outcome

P5 diagnostics、short-probe config、process-probe support、nonfinite-probe
training-path repair、有边界 8k training 与训练后 deterministic/stochastic probes
均已完成。P5 证据已完成，但不是 learned-policy accepted：independent M3 stopping head
已经移动，而 executable fire action 仍是低概率，deterministic release 仍然 flat。
