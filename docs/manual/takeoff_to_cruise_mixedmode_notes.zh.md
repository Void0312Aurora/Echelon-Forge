# 起飞到巡航混合模式笔记

本文档记录历史 P3 起飞到巡航混合模式基线，以及恢复连贯训练行为的路径生成修复。
下列 config 和 scenario 路径在注明处是维护中的仓库输入；experiment 目录属于
本地/留存制品，除非更新的 task 或 reference-artifact 页面提升它们，否则不是
当前权威依据。

## 制品引用

- 历史/本地实验制品：
  `experiments_tmp/20260316_p3_takeoff_to_cruise_mixedmode_worldyawroutefix_retrain_v1`
- 维护的训练配置：
  `examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json`
- 历史工件来源配置：
  `examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`
- 维护中的训练场景：
  `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- 维护中的评估场景：
  `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json`
- 历史/本地仅桥接实验输出：
  `experiments_tmp/archive_takeoff_to_cruise_bridge_20260316`

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

- 当前实现入口：
  `gym_envs/scenario_loader/route_generation.py` 和
  `gym_envs/scenario_loader/core.py`
- 更改：
  当任务航头配置为随世界偏航旋转时，动态生成的路径航路点现在会通过 `_rotate_waypoints_inplace(...)` 进行处理。

回归覆盖：

- `tests/world_batch/test_world_batch_runtime.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
- `tests/scenario/test_scenario_compiler.py`

## 本文保留的历史结果

应用路径旋转修复并从最新的混合模式检查点重新训练后：

- 种子集 `123-126`: `100%` 成功，`100%` 存活，平均奖励 `14356.41`
- 种子集 `1001-1004`: `100%` 成功，`100%` 存活，平均奖励 `13987.14`

请将其视为历史桥接基线。更新的起飞到巡航工作若要替代它，应先提升自己的冻结
config、制品记录或任务状态，再替换上面的维护场景/配置引用。

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
