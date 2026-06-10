# A7 Shadow Quality Target Repair

状态：`2026-06-04`，`A7-EVC-J` implementation repair 通过；短训 learned-policy outcome
仍然 held。

父级：[README.zh.md](README.zh.md)。英文权威版：
[a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md)。

## 修复

`A7-EVC-I` 发现 early stochastic accepted release 会从 A7 labels 中删失所有后续
quality-window positives。`A7-EVC-J` 修复这一 target construction 路径：

- `build_first_event_hazard_labels()` 现在支持 A7-only
  `shadow_quality_after_early_accept` pass。
- quality 前 early accepted release 仍然生成 pre-window / early-accepted negative labels。
- 同一 episode 后续 launch-window quality facts 现在可以生成挂到 first-event window id 上的
  `shadow_quality` positive credit labels。
- `compute_first_event_credit_loss()` 增加 `delta_align_active` mask。
- `AdaptiveKLPPO._first_event_credit_loss()` 将 `shadow_quality` rows 排除出
  event-logit delta alignment；因此 post-release closed-mask observations 会训练 credit
  head，但不会被蒸馏成合法 fire actions。
- A7 active config 显式设置
  `a7_event_credit_shadow_quality_weight = 1.0`。

该修复不改变 A3/A5 runtime legality。

## Focused Validation

命令：

```bash
python -m compileall -q \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/training/diagnostics.py \
  tests/policy/test_first_event_timing_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/policy/test_first_event_timing_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
```

结果：

- compileall：pass；
- JSON active config：pass；
- first-event label/loss tests：`15 passed`；
- A7 gradient/PPO warmup tests：`14 passed`；
- config/diagnostics/process-probe tests：`27 passed`。

新增 focused tests 覆盖：

- quality 前 early accepted，随后 shadow quality reachable；
- no-shadow-quality fallback，保持 early-accepted negatives；
- shadow rows 跳过 delta alignment。

## Label Reconstruction Check

使用旧 r3 stochastic probe CSV 与修复后的 builder：

| Probe | Active | Positives | Negatives | Sources |
| --- | ---: | ---: | ---: | --- |
| deterministic r3 | `1880` | `1076` | `804` | `prewindow=804`, `deadline=1076` |
| stochastic r3 | `3241` | `3222` | `19` | `prewindow=16`, `early_accepted=3`, `shadow_quality=3222` |

原先 stochastic 的 `0`-positive label distribution 已修复。

## 短训

运行：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_shadow_quality_repair_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260681
```

结果：

- 完成 `32768` steps；
- final model：
  `experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/final_model.zip`；
- final train scalar sample：
  - `a7/event_credit_active_count_mean = 450`；
  - `a7/event_credit_target_positive_frac = 0.6`；
  - `a7/event_credit_loss = 0.322`；
  - `a7/event_credit_delta_align_loss = 0.000476`；
  - `a7/event_credit_advantage_mean = -0.96`。

解释：修复后的 labels 已进入训练流，但 learned event-credit advantage 仍然为负。

## Probe Results

Deterministic probe：

- deterministic release count：`0`；
- fire mask open steps：`1880`；
- open-window event fire probability mean/max：`25.5%` / `27.2%`；
- quality-window A7 advantage mean：`-0.902`；
- legality violations：`0`。

Stochastic probe：

- release steps：`4`、`43`、`2`；
- authorized releases：`3/3`；
- unauthorized、repeat 与 shot-budget violations：`0`；
- 仍未达到 quality-window timing acceptance。

本轮新 probe 的 repaired label reconstruction：

| Probe | Active | Positives | Negatives | Sources |
| --- | ---: | ---: | ---: | --- |
| deterministic r1 | `1880` | `1071` | `809` | `prewindow=809`, `deadline=1071` |
| stochastic r1 | `3215` | `3209` | `6` | `prewindow=3`, `early_accepted=3`, `shadow_quality=3209` |

## 决定

`A7-EVC-J` 修复了已确认的 label-censoring bug：stochastic early accepted episodes
不再变成 zero-positive A7 target samples。

但它没有解决 learned first-shot timing。行为继续 held：

- deterministic 仍不发射；
- stochastic 仍过早发射；
- A7 advantage 在 quality window 内仍为负。

下一机制问题已经不再是“为什么 early accepted release 后没有 positives”，而是如何让
shadow credit 影响 legal-open quality states。可能的 follow-on 是 legal-state
counterfactual projection，或进一步拆分 shadow value learning 与 legal-state policy
distillation。

本轮不释放 M2、HMoE redesign、missile authority、doctrine、`2v2` 或 self-play 范围。
