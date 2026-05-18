<!-- Machine-translated draft generated on 2026-05-18 from docs/manual/takeoff_to_cruise_mixedmode_notes.md. Review before treating this file as authoritative. -->

# 起飞到巡航混合模式笔记

本文档记录了当前活跃的起飞到巡航混合模式任务，以及恢复连贯训练行为的路径生成修复。

## 活跃工件

- 活跃实验：
  `/home/void0312/CMO/experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1`
- 维护的训练配置：
  `/home/void0312/CMO/examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json`
- 历史工件来源配置：
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`
- 活跃训练场景：
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- 活跃评估场景：
  `/home/void0312/CMO/scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
- 已归档的仅桥接实验输出：
  `/home/void0312/CMO/experiments_tmp/archive_takeoff_to_cruise_bridge_20260316`

## 2026-03-16 修复的根因

观察到的失败：

- 某些桥接运行结果明显差于较旧的检查点。
- 在可视化中，飞机似乎忽略了巡航路线，并且未能有效捕获第一个航路点。
- 奖励轨迹显示，即使在那些幸存并稳定的运行中，也出现了较大的航路点进展和偏航距惩罚。

确认的根因：

- `world_yaw` 旋转了机场、跑道、生成状态和任务航向。
- 当 `rotate_mission_heading_with_world=true` 时，动态生成的路径航路点并未随相同的世界变换进行旋转。
- 这使得第一个巡航航段与旋转后的起飞几何不一致。
- 结果，任务不再是“起飞、离场、然后加入巡航”，而往往是“起飞，然后立即以一个很大的角度向一个全局固定的航段恢复”。

代码修复：

- 文件：
  `/home/void0312/CMO/gym_envs/scenario_loader.py`
- 更改：
  当任务航头配置为随世界偏航旋转时，动态生成的路径航路点现在会通过 `_rotate_waypoints_inplace(...)` 进行处理。

回归覆盖：

- `/home/void0312/CMO/tests/test_route_generator_world_yaw_alignment.py`
- `/home/void0312/CMO/tests/test_route_generator_rotates_with_world_heading.py`
- `/home/void0312/CMO/tests/test_route_generator_multileg_eval_distribution.py`
- `/home/void0312/CMO/tests/test_flyby_sequence_past_fix_guard.py`

## 最新结果

应用路径旋转修复并从最新的混合模式检查点重新训练后：

- 种子集 `123-126`: `100%` 成功，`100%` 存活，平均奖励 `14356.41`
- 种子集 `1001-1004`: `100%` 成功，`100%` 存活，平均奖励 `13987.14`

这是当前的桥接基线，直到有更新的起飞到巡航检查点明确替代它。

## 可视化

示例命令：

```bash
.venv/bin/python examples/viz/viz_runner.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --model experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1/final_model.zip \
  --algo AdaptiveKLPPO \
  --train_config examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json \
  --seed 123 \
  --port 5000
```
