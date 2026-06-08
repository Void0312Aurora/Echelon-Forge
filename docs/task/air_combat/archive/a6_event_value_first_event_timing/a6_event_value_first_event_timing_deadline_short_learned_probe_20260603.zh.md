# A6 Deadline-Bootstrap 短训 Learned-Policy Probe

状态：`2026-06-03` completed；held outcome。

父级：[README.zh.md](README.zh.md)。Re-scope note：
[a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.zh.md](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.zh.md)。

## 范围

本 probe 测试首次 A6 hazard/curriculum contract held 后的 deadline-bootstrap wave。它不接受
M2、self-play、`2v2`、missile physics、Pk、fuze、damage authority 或真实 tactics。

实验产物位于 `experiments_tmp/`，不得 staging。

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_deadline_bootstrap_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260629
```

结果：

- 完成 `32768` timesteps。
- Final model：
  `experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/final_model.zip`。
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`。
- Deadline knobs 生效：`a6/curriculum_coef=0`、`a6/deadline_weight=1`、
  `a6/hazard_coef=0.3`。
- 早期训练有真实 deadline labels：`2048` timesteps 时
  `a6/active_count_mean=238`、`a6/target_positive_frac=0.812`、
  `a6/hazard_loss=1.46`。
- 中后期 deadline windows 出现持续正例：约 `16384` timesteps 时
  `active_count_mean=386`、`target_positive_frac=1`、`hazard_loss=1.74`；
  约 `30720` timesteps 时 open-window event probability 为 `0.45%`，mode-fire 仍为 `0`。
- final train log 仍为 `active_count_mean=386`、`target_positive_frac=1`、
  `hazard_loss=1.6`。

## Probe Commands

Deterministic 与 stochastic probe 命令同英文记录，输出分别为：

- `experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_deterministic_probe.json`
- `experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_stochastic_probe.json`

## 结果

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1840 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 1239 | 4 | 3 | 1 | 3 | 3 | 0 | 0 |

Deterministic summary：

| Episode | Fire mask open | A6 open window | Fire event probability mean / max | Event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1840 | 1840 | `0.494% / 0.496%` | 0 | 0 | 0 |

Stochastic summary：

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Rejected reason | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 508 | 487 | 2 | 1 | 1 | `weapon_not_ready=1` | 1 | 1 | 0 | 3 |
| 1 | 572 | 509 | 1 | 1 | 0 | `{}` | 1 | 1 | 0 | 3 |
| 2 | 259 | 243 | 1 | 1 | 0 | `{}` | 1 | 1 | 0 | 3 |

## 解释

Deadline bootstrap 已接通，并产生持续正例。它也推动了 event probability：
deterministic open-window mean 从首次 A6 run 的 `0.247%` 上升到 `0.494%`。但这仍远低于
masked deterministic `fire_once` argmax 门槛，deterministic probe 仍为 `0` requests。

Stochastic 行为仍然每个 episode 产生一次授权 release，并保持零 violation releases、
零 repeat releases、零 shot-budget violations。但它在更严格的 no-rejected-request discipline
上出现退化：episode 0 在 accepted release 之前出现一次 `weapon_not_ready` rejected request。

因此 deadline wave 继续 held。blocker 已不再是 label plumbing。下一步应检查 event-head
update strength 与 optimizer routing：deadline positives 已存在，但 event logit 只从约 `-5.9`
移动到约 `-5.3`，没有朝正 argmax 方向明显推进。

## Held Outcome

A6 仍未 accepted。

推荐下一方向：

- 审计 `fire_once` event logits 的 event-head learning-rate scale、grouped optimizer treatment、
  KL/clip limits，以及 HMoE residual/head warmup；
- 增加 focused gradient/update probe，证明 deadline positives 需要多少 optimizer steps 才能把
  event-logit delta 从约 `-5.3` 推向 `0`；
- 在 event-head update-strength audit 之后，再考虑显式 event-value / advantage head，从而把架构风险和
  optimizer blockage 分开；
- M2 继续 held，除非更窄的 event-head 证据证明 sequence-native modeling 才是真正 release blocker。
