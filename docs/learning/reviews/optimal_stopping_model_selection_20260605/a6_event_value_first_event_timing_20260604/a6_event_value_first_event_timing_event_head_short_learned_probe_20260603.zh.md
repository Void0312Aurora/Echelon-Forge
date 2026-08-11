# A6 事件头短训 Learned-Policy 探针

状态：`2026-06-03` 已完成；held timing residual。

父级：[README.zh.md](README.zh.md)。event-head optimizer lane 仅通过本 probe
与父级 review 边界保留。

## 范围

本探针验证专用 `hybrid_event_head` optimizer lane 是否能在完整 S1 C2/ROE learned policy
中移动 masked `hold/fire_once` event 决策。它不接受 M2、self-play、`2v2`、missile
physics、Pk、fuze、damage authority 或真实 tactics。

实验产物位于 `experiments_tmp/`，不得 stage。

## 训练命令

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_event_head_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260631
```

结果：

- 完成 `32768` timesteps。
- Final model：
  `experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip`。
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`。
- event-head lane 已生效：
  `a6/event_head_enabled=1`，`a6/event_head_lr_scale=10`。
- 中段 diagnostics 显示该 lane 不再 update-starved：
  约 `20480` timesteps 时，`event_head_delta_fire_mean=1.94`，
  `event_logit_delta_mean_open=-1.68`，open-window fire probability 约 `15.7%`。
- 约 `30720` timesteps 时 deterministic event row 已 crossing：
  `event_head_delta_fire_mean=3.03`，`event_logit_delta_mean_open=0.747`，
  open-window fire probability 约 `67.9%`，且 `pi_event_mode_fire_frac=1`。
- final train log 仍有 `active_count_mean=386`、`target_positive_frac=1`、
  `hazard_loss=0.0856`。

## 探针命令

Deterministic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260632 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_deterministic_probe.json \
  --csv_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_deterministic_probe.csv
```

Stochastic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260632 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_stochastic_probe.json \
  --csv_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_stochastic_probe.csv
```

## 结果

| Probe | Episodes | Termination | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary：

| Episode | First contact | First authorization | First release | Fire-event max probability | Mode-fire count | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 0 | 2 | `72.8%` | 1 | 3 |

Stochastic summary：

| Episode | First contact | First release | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 4 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 41 | 42 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 1 | 2 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## 解读

Event-head lane 修复了 `A6-EVT-J` 中那个狭义 update-strength blocker。不同于 deadline
baseline，deterministic learned policy 现在跨过 masked event argmax，并执行一次 accepted
authorized release。Stochastic probing 同样保留 A5 release-discipline invariant：每个 episode
都是一次 request、一次 accepted release，无 rejected requests、无 violation releases、无 repeat
release、无 shot-budget violation。

这还不是完整 A6 acceptance。learned behavior 收敛到 authorization/contact 之后几乎立即发射：
deterministic release 在 step `2`，stochastic release steps 为 `4`、`42`、`2`。早发之后 A6
deadline/open-window diagnostics 基本被 vacate，因此该 policy 没有证明成熟 first-event timing
model。它证明 event decision 现在可训练，同时暴露更高一层的 timing-quality 问题。

## Held Outcome

`A6-EVT-K` 作为 evidence 已完成，但 A6 继续 held。

下一条有边界方向不应继续简单增大 LR，而应定义 engagement-quality 或 launch-window contract，
把 authorization 与良好 release timing 分开，同时保持 A3/A5 masks 和 state-machine
suppression 的权威性。
