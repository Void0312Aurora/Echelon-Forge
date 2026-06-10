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

- 维护的冻结执行配置：
  [p2_takeoff_retrain_v1.json](../examples/config/training/frozen/execution/p2_takeoff_retrain_v1.json)
- 训练场景：
  [takeoff_stage1_runway45_stresswind.json](../scenarios/takeoff/takeoff_stage1_runway45_stresswind.json)

状态：

- 先前引用的起飞实验输出已从工作空间清理。
- 幸存的维护参考是冻结执行 `p2` 配置，以及 `scenarios/takeoff/` 下的规范起飞场景。

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
- 维护的冷启动/完整航线配置：
  [p5_continuous_coldstart_retrain_v2.json](../examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)
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

## 活跃 Cooperative / Combined 主线

- 维护的 active 索引：
  [examples/config/training/active/README.md](../examples/config/training/active/README.md)
- 配置族：
  cooperative cruise、cooperative interval takeoff/departure、cooperative takeoff-to-cruise、cooperative takeoff-cruise-landing，以及 `examples/config/training/active/` 下的 `p4b` cruise-to-landing reopen 条目。
- 场景族：
  [scenarios/cruise](../scenarios/README.md)、[scenarios/takeoff](../scenarios/README.md) 和 [scenarios/combined](../scenarios/README.md)。

状态：

- 这些条目是 active forward-moving lanes，不是冻结验收工件。
- cooperative/HMoE A/B 控制在 active README 中记录；配置没有嵌入统一的 `scenario_path`，因此启动命令仍需要显式提供 scenario。

## 空战 1v1 Active Probes

- 维护的 active 索引：
  [examples/config/training/active/air_combat/README.md](../examples/config/training/active/air_combat/README.md)
- scripted-red smoke/probe 场景：
  [air_combat_1v1_headon_sensor_smoke_v1.json](../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
- Stage-0 drone probe 场景：
  [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
- Stage-1 BVR non-maneuvering target probe 场景：
  [air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json](../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json)
- Stage-1 active probe config：
  [air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json](../examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json)
- runtime 证据：
  [test_air_combat_1v1_fixture.py](../tests/runtime/air_combat/test_air_combat_1v1_fixture.py)
- active-entry 证据：
  [test_air_combat_training_entry_contracts.py](../tests/training/test_air_combat_training_entry_contracts.py)

状态：

- active `1v1` 配置是 HMoE execution probes 和 smoke entries，不是冻结基线，也不是 self-play 证据。
- Stage-0 和 Stage-1 现在已有 active probe configs；Stage-2 和 Stage-3 仍是受维护但尚未配对 active training config 的课程场景。

## 海军 N4 Active Gate

- 维护的 active 索引：
  [examples/config/training/active/naval/README.md](../examples/config/training/active/naval/README.md)
- Active configs：
  `naval_contact_report_threat_roe_smoke_v1.json`、
  `naval_screen_station_hold_threat_aware_smoke_v1.json` 和
  `naval_screen_station_recovery_threat_aware_smoke_v1.json`。
- 场景：
  [ddg51_take1_screen_threat_roe_v1.json](../scenarios/naval/ddg51_take1_screen_threat_roe_v1.json) 和
  [ddg51_take1_screen_threat_roe_offstation_recovery_v1.json](../scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json)。
- 合约：
  [naval_screen_threat_roe_geometry.json](../tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json) 和
  [naval_screen_threat_roe_offstation_recovery.json](../tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json)。
- eval/test 证据：
  [test_evaluation_cli_contracts.py](../tests/eval/test_evaluation_cli_contracts.py) 和
  [test_naval_training_entry_contracts.py](../tests/training/test_naval_training_entry_contracts.py)。

状态：

- 这只是已接受的 pre-fire/tasking/contact gate。
- 它不暴露 weapon release、damage、kill rewards，也不声明 trained naval-policy。

## Ground Bootstrap

- 场景夹具：
  [ground_platoon_tasking_smoke_v1.json](../scenarios/ground/ground_platoon_tasking_smoke_v1.json)、
  [ground_platoon_static_occupy_v1.json](../scenarios/ground/ground_platoon_static_occupy_v1.json) 和
  [ground_platoon_support_relationship_v1.json](../scenarios/ground/ground_platoon_support_relationship_v1.json)。
- native schema 证据：
  [ground_platoon_mvp.json](../examples/config/database/ground/units/ground_platoon_mvp.json) 和
  [CAPABILITY_NOTE.md](../examples/config/database/ground/units/CAPABILITY_NOTE.md)。
- runtime/contract 证据：
  [tests/runtime/ground](../tests/runtime/ground) 和
  [tests/contracts/unit/ground](../tests/contracts/unit/ground)。

状态：

- Ground 还不是 active RL training line。
- 当前证据仅限 tasking/common-core、native platform-schema/bootstrap 和 lifecycle bridge coverage。movement、terrain、sensing、fires、damage 与完整 ground runtime 行为仍保持 held。
