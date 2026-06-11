# A4 授权首发 Binary Diagnostics - 2026-06-03

状态：`2026-06-03`，保留 diagnostics，拒绝 opportunity-penalty trial。
A4 继续 held；M2 继续 held。

语言：

- 英文规范页：
  [a4_authorized_first_shot_binary_diagnostics_20260603.md](a4_authorized_first_shot_binary_diagnostics_20260603.md)
- 中文辅文：`a4_authorized_first_shot_binary_diagnostics_20260603.zh.md`

## Scope

本 packet 检查保留的 routed A4 policy 是否接近 deterministic `tms_up` /
`fire_weapon` 过阈值。它也记录一次有边界 reward-mechanism trial：授权窗口内
pre-release fire opportunity penalty。

本切片保留的代码：

- hybrid action distribution 不再向 PPO 返回 `None` entropy，而是返回有限 entropy；
- 训练 diagnostics 增加紧凑 binary action logits/probabilities，例如
  `diag/pi_bin_fire_p_mean`；
- process probe 输出 per-step 和 authorized-window binary logits/probabilities；
- reward runtime 暴露
  `air_combat_roe_authorized_fire_opportunity_penalty`，但维护中的 S1 C2/ROE
  active scenario 保持 `0.0`。

## Retained-Routed Baseline Diagnostics

命令：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260625 \
  --max_steps 2400 \
  --json_out experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/binary_diagnostics_det_20260603.json
```

结果：

| Probe | Fire attempts | Releases | Authorized-window steps | `tms_up` prob mean/max | `fire_weapon` prob mean/max | `fire_weapon` logit max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic retained routed | 0 | 0 | 2400 | `0.01877 / 0.01880` | `0.002222 / 0.002224` | `-6.106` |

解释：deterministic policy 离过阈值并不近。`fire_weapon` logit 基本仍贴在
safe-action prior 上。

## Opportunity-Penalty Trial

训练命令：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_entropy_opportunity_temporal_32k_v2_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260634
```

该 run 使用临时
`air_combat_roe_authorized_fire_opportunity_penalty=-0.1`。完成下方 probe 后，
active scenario 已恢复为 `0.0`。

训练完成 `32768` timesteps。最终 diagnostics 仍显示：

- `diag/pi_bin_fire_logit_mean ~= -6.12`；
- `diag/pi_bin_fire_p_mean ~= 0.0022`；
- final rollout reward 约 `-3.36e3`；
- stochastic training warning 仍出现 "no missiles remaining"。

deterministic probe：

| Probe | Fire attempts | Releases | Authorized-window steps | `fire_weapon` prob mean/max | `fire_weapon` logit max | Reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| opportunity trial deterministic | 0 | 0 | 2400 | `0.002210 / 0.002215` | `-6.110` | `-164.59` |

stochastic probe：

| Episodes | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 22 | 11 | 3 | 8 | 11 | 0 |

逐 episode stochastic release summary：

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 9 | 4 | 1 | 3 | 5 | 0 |
| 1 | 9 | 4 | 1 | 3 | 5 | 0 |
| 2 | 4 | 3 | 1 | 2 | 1 | 1 |

## Decision

opportunity penalty 不作为 active default 保留：

- 它没有把 deterministic `fire_weapon` logits 从 safe prior 拉出来；
- 它让 deterministic return 更负，但仍不产生 release；
- stochastic 行为相对 retained routed run 退化。

runtime key 保留给未来受控 sweep，但维护中的 S1 C2/ROE active scenario 保持禁用。

## Next Work

残余现在已经窄于 reward magnitude tuning：

- 为 authorized-first-shot route 增加 supervised 或 curriculum-style binary pulse target；
- 或增加 route-specific initialization / curriculum，只抬高
  `authorized_first_shot` subexpert 的 pulse logits，并在 `post_launch_assess` 中抑制 fire。

在维护中的 S1 C2/ROE probe 证明 deterministic 授权首发前，不释放 M2。
