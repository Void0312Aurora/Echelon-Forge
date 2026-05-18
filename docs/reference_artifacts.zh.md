<!-- Machine-translated draft generated on 2026-05-18 from docs/reference_artifacts.md. Review before treating this file as authoritative. -->

# 参考工件

本文档取代了旧有的分阶段 `active_*_artifacts.md` 笔记。

其目的更窄：

- 记录工作空间中仍存在的维护配置/场景入口点
- 保存历史路线的最小来源注释
- 避免指向已从仓库工作空间清理的实验输出

保留边界：

- `scenarios/` 和维护配置文件仍然是版本化的仓库输入。
- `experiments/`、`datasets/` 和 `output/` 不是权威来源，可能从活动工作空间中清理。
- 当运行目录或生成的数据集被移除时，仅在此处或任务/报告文档中保留最少量的幸存来源指针。

## 起飞到巡航桥接

- 维护的训练配置：
  [p3_takeoff_to_cruise_retrain_v1.json](../examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- 历史工件来源配置：
  [p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json)
- 训练场景：
  [takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json](../scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json)
- 评估场景：
  [takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json](../scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json)

状态：

- 历史桥接实验输出已从活动工作空间清理。
- 使用上述维护的配置和场景作为幸存的参考入口点。

## 巡航

- 用于历史桥接/巡航血统的维护执行配置：
  [p3_takeoff_to_cruise_retrain_v1.json](../examples/config/training/frozen/execution/p3_takeoff_to_cruise_retrain_v1.json)
- 历史工件来源配置：
  [p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json)
- 训练场景：
  [cruise_waypoints_paramroute_navv2_train_v1.json](../scenarios/cruise/cruise_waypoints_paramroute_navv2_train_v1.json)
- 协同训练场景：
  [cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json](../scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json)
- 活动协同训练配置：
  [cooperative_cruise_nav_v2_formation_v1.json](../examples/config/training/active/cooperative_cruise_nav_v2_formation_v1.json)
- 评估场景：
  [cruise_waypoints_stresswind_rewardbalance_v1.json](../scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json)
  [cruise_waypoints_ood_geometry_v1.json](../scenarios/cruise/cruise_waypoints_ood_geometry_v1.json)
  [cruise_waypoints_ood_profile_v1.json](../scenarios/cruise/cruise_waypoints_ood_profile_v1.json)
  [cruise_waypoints_ood_wind_v1.json](../scenarios/cruise/cruise_waypoints_ood_wind_v1.json)

状态：

- 早期巡航实验输出已从活动工作空间清理。
- 此行仍保留的数据集是 `datasets/cruise_waypoints_full_visual_proprio_v1`（如果保留在活动工作空间之外）。

## 起飞

- 训练场景：
  [takeoff_stage1_runway45_stresswind.json](../scenarios/takeoff/takeoff_stage1_runway45_stresswind.json)

状态：

- 先前引用的起飞实验输出和训练配置已从工作空间清理。
- 除非重新引入新的维护配置，否则此行现应仅视为历史记录。

## 着陆

- 维护的训练配置：
  [p4_landing_retrain_v1.json](../examples/config/training/frozen/execution/p4_landing_retrain_v1.json)
- 历史工件来源配置：
  [p4_landing_full_visual_ils_smoke_v1.json](../examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json)
- 训练场景：
  [landing_ils_final_train_v1.json](../scenarios/landing/landing_ils_final_train_v1.json)
- 评估场景：
  [landing_ils_final_eval_v1.json](../scenarios/landing/landing_ils_final_eval_v1.json)
- 已归档的着陆烟雾运行：
  `archive/20260317_landing_cleanup`（如果保留在活动工作空间之外）。

状态：

- 较旧的活跃着陆烟雾实验目录已从工作空间清理。
- 保留的着陆归档仍然是此行唯一的幸存运行级来源标记。

## 连续起飞-巡航-着陆

- 维护的训练配置：
  [p5_continuous_retrain_v1.json](../examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- 历史工件来源配置：
  [p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json](../examples/config/Archive/training/pre_freeze_experiments/p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json)
- 训练场景：
  [takeoff_to_landing_continuous_train_v1.json](../scenarios/combined/takeoff_to_landing_continuous_train_v1.json)
- 评估场景：
  [takeoff_to_landing_continuous_eval_v1.json](../scenarios/combined/takeoff_to_landing_continuous_eval_v1.json)

运行时说明：

- 维护的训练配置在 CPU 上保持精确世界步进，并使用 `batch_observation_backend=compiled` 和 `batch_visual_backend=compiled`。
- 较旧的混合 `gpu_host` 视觉线路仍然是一个仅用于诊断的历史分支。

最新保留的诊断：

- 成功恢复的种子：
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed124.png`（如果保留在活动工作空间之外）。
- 重新训练后的失败种子：
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed125.png`（如果保留在活动工作空间之外）。
- 重新训练前的参考门修复成功：
  `artifacts/takeoff_to_landing_continuous/model_seed123_gatefix_v2.png`（如果保留在活动工作空间之外）。
- 最终重新训练前的剩余失败修复标记：
  `artifacts/takeoff_to_landing_continuous/model_gatefix_retrain_seed126_v3.png`（如果保留在活动工作空间之外）。
- 活跃的最终重新训练成功标记：
  `artifacts/takeoff_to_landing_continuous/model_v3_retrain_seed126.png`（如果保留在活动工作空间之外）。

状态：

- 较旧的活跃连续实验目录和模型检查点已从工作空间清理。
- 维护的参考现在存在于配置/场景层以及上述保留的诊断中。
