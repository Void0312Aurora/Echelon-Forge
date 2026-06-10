# A4 授权首发 Reward Probe - 2026-06-03

状态：`2026-06-03`，reward-side 证据。A4 仍为 active；本记录不验收 learned
policy，也不释放 M2。

语言：

- 英文规范页：
  [a4_authorized_first_shot_reward_probe_20260603.md](a4_authorized_first_shot_reward_probe_20260603.md)
- 中文辅文：`a4_authorized_first_shot_reward_probe_20260603.zh.md`

## Scope

本证据接在 A3 reactive/temporal 对照之后，检查额外 reward signal 是否能让 S1 C2/ROE
授权首发可训练。它不改变导弹物理、弹药 runtime、毁伤 authority 或 M2。

维护中的场景/config 对：

- 场景：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- 配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json`

## Implementation

保留实现为授权首发前的武器链增加可配置 C2/ROE reward terms：

- `air_combat_roe_authorized_radar_active_bonus`
- `air_combat_roe_authorized_tms_up_bonus`
- `air_combat_roe_authorized_master_arm_bonus`
- `air_combat_roe_authorized_weapon_selected_bonus`
- `air_combat_roe_authorized_fire_attempt_bonus`
- `air_combat_roe_authorized_fire_no_release_penalty`

正向准备/尝试项在每个 episode 只发放一次，避免策略通过全程打开
radar/master-arm/weapon-select 刷 reward。fire-no-release 罚项仍按失败 fire attempt
逐次生效。维护中的 S1 C2/ROE probe 同时加重 repeat-release 和 single-shot 违规惩罚。

## Commands

Focused tests：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

保留的 32k temporal run：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_temporal_once_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260623
```

模型探针：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a4_authorized_first_shot_temporal_once_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260623 \
  --max_steps 2400
```

stochastic probe 使用同一命令，并加 `--episodes 3 --stochastic`。

## Results

Focused tests 已通过：

- `tests/runtime/air_combat/test_air_combat_reward_surface.py`：`10 passed`。
- `tests/training/test_air_combat_training_entry_contracts.py`：`9 passed, 8 subtests passed`。

训练完成并保存
`experiments_tmp/a4_authorized_first_shot_temporal_once_32k_20260603/final_model.zip`。
未出现 non-finite abort。最终 rollout reward 约 `-3.87e3`，HMoE 诊断仍全部路由到
`nav/vector`。

Final-model probes：

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 20 | 11 | 3 | 8 | 9 | 1 |

逐 episode stochastic summary：

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 5 | 3 | 1 | 2 | 2 | 1 | 0 |
| 1 | 8 | 4 | 1 | 3 | 4 | 0 | 0 |
| 2 | 7 | 4 | 1 | 3 | 3 | 0 | 1 |

## Discarded Per-Step Shaping Attempt

在保留的一次性实现前，曾用同一个 32k temporal surface 测试过按步发放的准备奖励。
它让 deterministic radar/master-arm/weapon-select 稳定打开，并在 stochastic 中产生
一次 `combat_win`，但 deterministic 仍不 fire，stochastic probe 仍产生 `11` 次 release
和 `8` 次 violation release。该尝试已废弃，因为它形成了“不发射也能吃准备奖励”的局部最优。

## Interpretation

reward shaping 单独不足以闭环。保留的一次性 shaping 去掉了明显的 reward-farming
失败模式，并让 violation release 代价变高，但它没有教会 deterministic policy 越过
TMS/fire pulse 阈值。stochastic 行为仍会在授权首发后继续采样重复 fire。

A4 下一刀应转向 policy mechanics：

- 增加或测试 HMoE air-combat weapons-employment route，而不是继续把 C2/ROE engagement
  路由到通用 `nav/vector`；
- 检查 `tms_up` 和 `fire_weapon` 二值 pulse logits；
- 考虑有边界的 action-head prior 或 pulse-action curriculum，而不是继续放大奖励数值。

后续实现证据记录在
[a4_authorized_first_shot_routing_probe_20260603.zh.md](a4_authorized_first_shot_routing_probe_20260603.zh.md)。

M2 继续 held。
