# A6 发射窗口短训 Learned-Policy 探针

状态：`2026-06-04` 已完成；held outcome。

父级：[README.zh.md](README.zh.md)。契约：
[a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)。

## 范围

本探针在维护中的 S1 C2/ROE learned-policy 路径中测试 `A6-EVT-L` launch-window timing
contract。它与 `A6-EVT-K` 对照：K 已让 event-head lane 跨过 deterministic argmax，但 release
几乎贴着 authorization/contact 发生。

实验产物位于 `experiments_tmp/`，不得 stage。

## 训练命令

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_launch_window_temporal_32k_20260604 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260641
```

结果：

- 完成 `32768` timesteps。
- Final model：
  `experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip`。
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`。
- Launch-window labels 已生效：
  `a6/launch_window_enabled=1`，
  `a6/launch_window_prewindow_hold_weight=0.3`。
- Training labels 不是 dense positive：`target_positive_frac` 在 `0.86` 这类正例较多的
  rollout 与 `0.0` 这类全负例/无 active rollout 之间切换。
- Event-head 有移动但最后 logged diagnostics 仍未 crossing：
  约 `30720` timesteps 时，`event_logit_delta_mean_open=-2.19`，
  `event_fire_prob_mean_open=0.10`，`pi_event_mode_fire_frac=0`。

## 探针命令

Deterministic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip \
  --episodes 1 \
  --seed 20260642 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_deterministic_probe.json \
  --csv_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_deterministic_probe.csv
```

Stochastic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip \
  --episodes 3 \
  --seed 20260642 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_stochastic_probe.json \
  --csv_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_stochastic_probe.csv
```

## 结果

| Probe | Episodes | Termination | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary：

| Episode | First contact | First release | Open-window event probability mean / max | Mode-fire count | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | none | `34.6% / 35.0%` | 0 | 4 |

Stochastic summary：

| Episode | First contact | First release | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 7 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 41 | 43 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 1 | 4 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## 解读

Launch-window contract 是 live 的，并且改变了 learned-policy behavior。不同于
`A6-EVT-K`，deterministic mode 不再在 authorization/contact 后近立即发射。event probability
也有实质移动：deterministic probe 的 open-window fire probability 为 `34.6% / 35.0%`，
但 masked argmax 仍然选择 `hold`。

这不是 A6 acceptance。Stochastic probing 仍然采样出早期授权发射，步数为 `7`、`43`、`4`。
这比 `A6-EVT-K` stochastic steps `4`、`42`、`2` 略有后移，但没有证明预期的
quality-window timing。该契约因此能压制 deterministic early fire，但当前 32k / weight /
window 设置还没有形成稳定 learned timing policy。

## Held Outcome

`A6-EVT-M` 作为 evidence 已完成，但 A6 继续 held。

建议下一方向：

- 保持 A3/A5 合法性不变；
- M2 继续 held；
- 遵循 [README.zh.md](README.zh.md) 保留的边界：暂停 L 参数调节，并在继续训练前
  定义 `A6-EVT-O` counterfactual event-time objective。
