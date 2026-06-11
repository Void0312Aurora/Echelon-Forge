# M3-S2 发射闭合批量验证 2026-06-08

状态：`bounded firing gate accepted / timing and effects quality held`。

## 问题

A5 武器保险动作帧修复之后，当前 active M3-S2 模型是否通过此前挂起的多 seed / 多
episode 发射闭合门槛？

本验证只检查发射闭合：

- 模型请求 `fire_once`；
- A5 接受该请求；
- 实际少一枚弹；
- 该 release 是授权发射；
- 没有被拒绝的 `fire_once` 请求；
- 没有违规发射，也没有评估前重复发射。

Damage、effects、target-health drop 和 kill-chain outcome 均不属于本 gate。

## 模型与运行时

- 模型：
  `experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip`
- 场景：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- 训练配置：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
- 动作模式：`air_combat_hybrid_v1`
- 每个 episode 最大步数：`800`

## 门槛

每个被检查 episode 必须满足：

- `fire_once_requested_count = 1`
- `fire_once_accepted_count = 1`
- `fire_once_rejected_count = 0`
- `release_count = 1`
- `authorized_release_count = 1`
- `violation_release_count = 0`
- `repeat_release_before_assessment_count = 0`
- `first_release_step` 已报告。

本次验证没有使用任何有界 rejected-request 例外。

## 命令

Deterministic batch：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --episodes 8 \
  --seed 20260608 \
  --max_steps 800 \
  --csv_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/deterministic_seed20260608_ep8_800.csv \
  --json_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/deterministic_seed20260608_ep8_800.json
```

Stochastic batch：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --mode model \
  --stochastic \
  --model experiments_tmp/m3s2_direct_fire_boundary_initfrom_8k_20260608_r1/final_model.zip \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --episodes 8 \
  --seed 20260608 \
  --max_steps 800 \
  --csv_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/stochastic_seed20260608_ep8_800.csv \
  --json_out experiments_tmp/m3s2_fire_closure_batch_validation_20260608_r1/stochastic_seed20260608_ep8_800.json
```

## 结果

Deterministic batch：

| Seeds | Episodes | Passed | Failed | Release steps | Rejected | Violations | Repeats |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20260608..20260615` | 8 | 8 | 0 | `423, 509, 510, 512, 546, 548, 507, 584` | 0 | 0 | 0 |

Stochastic batch：

| Seeds | Episodes | Passed | Failed | Release steps | Rejected | Violations | Repeats |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20260608..20260615` | 8 | 8 | 0 | `283, 282, 282, 282, 323, 322, 282, 285` | 0 | 0 | 0 |

合并发射门槛：

- 检查 episodes：`16`
- 通过 episodes：`16`
- 失败 episodes：`0`
- first-release step 范围：`282..584`
- total rejected `fire_once` requests：`0`
- total violation releases：`0`
- total repeat-before-assessment releases：`0`
- 本 batch 中 effects-event episodes：`0`
- 本 batch 中 damage-report episodes：`0`

## 判定

当前 active M3-S2 模型在该 scenario/config pair 上通过有边界的多 seed / 多 episode
发射闭合门槛。Direct fire-boundary owner 的发射部分从 `batch closure pending`
升级为 `bounded firing gate accepted`。

这不验收 timing quality、effects quality、target damage 或 kill-chain behavior。
这些仍是独立的 A8/model evidence 问题。

后续训练可以把本 active slice 的 release gate 当成已闭合处理：除非该 batch gate
回归，否则未来失败不应首先按“模型不会发射”来调试。
