# A5 短训 Learned-Policy Probe

状态：`2026-06-03`，A5 event-action、reward/config 与 diagnostics 实现后的
learned-policy evidence。A5 仍保持 held：deterministic policy 仍不请求 `fire_once`，
但 stochastic probing 已显示结构性发射纪律。

父级：[README.zh.md](README.zh.md)。实现证据：
[a5_constrained_event_action_model_implementation_evidence_20260603.zh.md](a5_constrained_event_action_model_implementation_evidence_20260603.zh.md)。

## Scope

本次运行检查首版 A5 event-action 实现是否足以让维护中的 S1 C2/ROE temporal probe
学出 deterministic authorized first shot。它不验收 M2、`2v2`、self-play、导弹物理、
Pk、引信或真实 doctrine 声明。

证据有意保持短训边界：一次 A5 post-change `32768` steps 训练，加 deterministic 与
stochastic process probes。产物位于 `experiments_tmp/`，不得 stage。

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a5_event_action_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260626
```

结果：

- 完成 `32768` timesteps。
- final model 保存于
  `experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip`。
- 未出现 non-finite abort。
- final rollout mean reward 约 `528`。
- 训练 diagnostics 确认 `hmoe/fam/combat = 1`。
- 后期 diagnostics 仍显示 `pi_event_fire_mask_frac ~= 0.75`、
  `pi_event_fire_p_mean ~= 0.20%`、`pi_event_mode_fire_frac = 0`。

## Probe Commands

Deterministic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260627 \
  --max_steps 2400 \
  --json_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json \
  --csv_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.csv
```

Stochastic：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a5_event_action_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260627 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json \
  --csv_out experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1880 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 1647 | 4 | 3 | 1 | 3 | 3 | 0 | 0 |

Deterministic summary：

| Episode | Fire mask open | AuthorizedReady steps | Fire event probability mean / max | Fire event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1880 | 1880 | `0.217% / 0.278%` | 0 | 0 | 0 |

Stochastic summary：

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Rejection reason | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 823 | 792 | 2 | 1 | 1 | `weapon_not_ready=1` | 1 | 1 | 0 | 3 |
| 1 | 346 | 296 | 1 | 1 | 0 | none | 1 | 1 | 0 | 3 |
| 2 | 592 | 559 | 1 | 1 | 0 | none | 1 | 1 | 0 | 3 |

## Interpretation

A5 修复了 A4 中结构性多发和 stochastic 发射纪律失败。stochastic probing 中，每个
episode 都只执行一次 authorized release；没有 violation releases，没有 assessment 前
repeat releases，也没有 shot-budget violations。相比保留的 A4 stochastic evidence，
这是显著改善。

A5 还没有解决 deterministic learned release timing。deterministic probe 中有 `1880`
个 fire-mask-open steps 和 `1880` 个 `AuthorizedReady` steps，但 `fire_once` requests
为零。masked event fire probability 仍约 `0.2%`，因此 deterministic argmax 仍为 `hold`。

残余不再是 reward-only legality 问题，而是 policy optimization / event-value 问题：
event-action surface 已能合法表达和抑制 release，但 PPO 仍把 deterministic `fire_once`
保持在 `hold` 之下。

## Held Residual

A5 应保持 held，而不是 accepted。推荐下一包是 event-value 或 first-event timing
机制，例如 event Q-head、显式 first-shot curriculum，或 hazard / first-event objective。
该 follow-on 不应重新打开广泛 invalid-fire penalties 作为合法性机制。
