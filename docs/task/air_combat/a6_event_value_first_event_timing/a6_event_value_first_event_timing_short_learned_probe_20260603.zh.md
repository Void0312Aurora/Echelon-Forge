# A6 短训 Learned-Policy Probe

状态：`2026-06-03` completed；A6 工程路径已证明真实生效，但首个 objective
contract 仍 held，因为 deterministic `fire_once` 仍然 argmax 到 `hold`。

父级：[README.zh.md](README.zh.md)。Baseline：
[a6_event_value_first_event_timing_observation_20260603.zh.md](a6_event_value_first_event_timing_observation_20260603.zh.md)。

## 范围

本 probe 检查首个 A6 objective contract：在现有 `hold/fire_once` event logit delta
上加入 masked first-event hazard，并配套有边界 curriculum bootstrap。本记录不接受
M2、self-play、`2v2`、missile physics、Pk、fuze、damage authority 或真实 doctrine claims。

实验产物位于 `experiments_tmp/`，不得 staging。

## 运行前修复

第一次 A6 训练尝试暴露了两个工程 blocker：

- non-finite probe 复制了旧版 PPO `collect_rollouts` / `train` 逻辑，绕过了 A6 label
  attachment 和 hazard loss；
- world-batch air-combat 路径没有把 A5 event-action info 合回每步 `info`，并且
  `terminal` info mode 会隐藏所需 label。

本轮工程修正：

- 增加 CPU 与 device-resident A6-aware dict rollout buffers；
- 在 policy observations 之外附加 A6 first-event labels；
- 修复 non-finite probe training wrapper，使其保留 A6 loss 与 logs；
- 将 C2/ROE A6 active configs 改为 `step_info_mode=full`；
- 让 `WorldBatchVecEnv` air-combat hybrid action path 与 `UniversalEnv.step()` 对齐：
  apply/finalize event-action gate，并将 event info 合回 step info；
- A6 label window 优先使用 policy-visible C2/ROE mission observation 里的 event mask，
  runtime `info` 仅作为 fallback 与 accepted-release source。

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_first_event_hazard_temporal_32k_policymask_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260628
```

结果：

- 完成 `32768` timesteps。
- final model 位于
  `experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/final_model.zip`。
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`。
- A6 训练信号真实进入：`2048` timesteps 时 `a6/active_count_mean=113`、
  `a6/hazard_loss=0.0113`、`a6/target_positive_frac=0.0175`。
- 有边界 curriculum 在每个 episode 一次 seed 后停止；早期窗口后
  `a6/active_count_mean` 回到 `0`。
- curriculum coefficient 在训练前 25% 后衰减到 `0`。
- 后期 diagnostics 仍显示 event fire probability 接近 A5：约 `30720` timesteps 时
  `a6/event_fire_prob_mean_open ~= 0.251%`，`pi_event_mode_fire_frac = 0`。

## Probe Commands

Deterministic 与 stochastic probe 命令同英文记录，输出分别为：

- `experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_deterministic_probe.json`
- `experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_stochastic_probe.json`

## 结果

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1840 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 741 | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary：

| Episode | Fire mask open | A6 open window | Fire event probability mean / max | Event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1840 | 1840 | `0.247% / 0.248%` | 0 | 0 | 0 |

Stochastic summary：

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 291 | 280 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 368 | 302 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 171 | 159 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## 解释

A6-EVT-E/F 已证明训练路径真实接通：A6 labels 会生成、在 policy observations 外保存、随
PPO minibatch 采样、在 non-finite probe wrapper 下保留，并通过 diagnostics 可见。

但首个 objective contract 仍不足。deterministic policy 在大量 open windows 下仍为零
`fire_once` requests，event probability 维持在约 `0.25%`，接近 A5 baseline
（`0.217% / 0.278%`）。stochastic probe 保留了 A5 release discipline：每个 episode
恰好一次授权释放，没有 rejected requests、violation releases、pending-assessment repeat 或
shot-budget violation。

因此 residual 已不再是 implementation plumbing failure，而是机制问题：每个 episode 一次早期
curriculum seed 能产生有限 A6 gradient，但该信号过短，无法在 curriculum 衰减且真实
accepted-release labels 稀缺的条件下推动 deterministic event argmax。

## Held Outcome

A6 继续 held。推荐下一方向是重新 scope objective，例如：

- 让 first-event hazard 在 open windows 上提供持续 survival/censoring signal，而不是只给一次早期
  positive seed；
- 提高或 staged event-logit curriculum，使其在 decay 前影响 deterministic argmax；
- 增加 event-value head 或 advantage-style target；
- M2/sequence-native modeling 仍 deferred，除非该 residual 被正式投票为下一 release blocker。
