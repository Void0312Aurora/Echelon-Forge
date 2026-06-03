# A3 C2/ROE Learned-Policy 探针证据 - 2026-06-03

状态：`2026-06-03`，本地 learned-policy 证据与发射后 mission observation
修复记录。本记录不验收 learned policy，也不释放 M2。

语言：

- 英文规范页：[a3_c2_roe_learned_policy_probe_20260603.md](a3_c2_roe_learned_policy_probe_20260603.md)
- 中文辅文：`a3_c2_roe_learned_policy_probe_20260603.zh.md`

## 范围

本记录接在 A3 P4 process probe 之后，使用 S1 C2/ROE 场景/config 对运行一次短程
learned-policy 训练：

- `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`

问题是：当 C2/ROE 合同进入策略观测后，当前 hybrid HMoE policy 是否能学出可接受的
single-shot 发射纪律。

## 训练命令

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a3_c2_roe_hybrid_shaped_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260603
```

结果：

- 训练完成并保存 `experiments_tmp/a3_c2_roe_hybrid_shaped_32k_20260603/final_model.zip`；
- 未产生 non-finite report；
- 训练仍以 `combat_timeout` 为主；
- 最终 `ep_rew_mean=-690`；
- rollout 日志反复出现无剩余导弹警告，说明 sampled 行为仍会消耗导弹。

## 模型探针

Deterministic final-model probe：

- `combat_timeout=1`；
- `fire_attempt_count=0`；
- `release_count=0`；
- 飞行稳定，radar/master-arm 打开，但没有 fire pulse。

Stochastic final-model probe，3 个 episode：

- `combat_timeout=3`；
- `fire_attempt_count=16`；
- `release_count=11`；
- `authorized_release_count=3`；
- `violation_release_count=8`；
- `invalid_fire_attempt_count=5`；
- `damage_report_count=1`。

逐 episode 摘要：

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 4 | 3 | 1 | 2 | 1 | 1 | 1 |
| 1 | 5 | 4 | 1 | 3 | 1 | 0 | 0 |
| 2 | 7 | 4 | 1 | 3 | 3 | 0 | 0 |

## 发射后 Observation 修复

learned-policy probe 暴露出一个合同缺口：A3 reward/probe 分类能看到 release count，
但策略侧 mission observation 仍暴露来自 `mission_cmd` 的静态
`shot_budget_remaining`、`pending_assessment` 和 `own_missiles_in_flight_count`。

本地修复将 `air_combat_c2_roe_v1` mission observation 改为从当前导弹余量下降和
reward 侧 release count 推断已知发射数。single-shot 合同下，已知发射后策略会看到：

- `shot_budget_remaining=0`；
- `pending_assessment=1`；
- `own_missiles_in_flight_count>=1`。

修复后的聚焦验证：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/world_batch/test_world_batch_vec_env.py::WorldBatchVecEnvTests::test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation
# 9 passed
```

修复后 process-probe sanity check 仍保持原分类面：

- `forced_fire`：1 次发射，1 次授权，0 次违规；
- `switch_explore`：4 次发射，1 次授权，3 次违规。

## 解释

A3 作为分类器已经成立：它能把授权首发和 single-shot policy 下的后续违规发射拆开。
learned policy 仍未验收：deterministic 行为不发射，stochastic 行为仍会耗弹并产生大量
违规发射。

下一项实质动作是在动态发射后观测修复之后，重跑 reactive/temporal A3 C2/ROE 训练对照。
在可观察合同下 learned-policy 武器使用没有改善前，M2 继续 held。
