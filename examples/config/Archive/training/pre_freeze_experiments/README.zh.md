<!-- Machine-translated draft generated on 2026-05-18 from examples/config/Archive/training/pre_freeze_experiments/README.md. Review before treating this file as authoritative. -->

# 预冻结训练实验存档

此目录保存了以前直接位于 `examples/config/training/` 下的旧执行层和模型架构训练配置。

这些配置仅出于溯源和对比目的而保留。当前维护的训练面如下：

- `examples/config/training/default_ppo.json`
- `examples/config/training/curriculum/`
- `examples/config/training/frozen/`

## 已存档的组

- `p2_*`
  - 起飞、视觉、稳定性、性能、冒烟和消融实验。
- `p3_*`
  - 从起飞到巡航的全视觉/nav-v2 残差实验。
- `p4_*`
  - 着陆全视觉/ILS 冒烟实验。
- `p5_*`
  - 从起飞到着陆的连续冒烟/重新训练实验。
- `takeoff_departure_full_visual_*`
  - 历史上的起飞-离场残差控制器修复线。
- `transformer_*`
  - 早期的 Transformer 策略/特征提取器规模实验。

`takeoff_departure_full_visual_*` 与 `transformer_*` 两组在磁盘上已无文件；
如需读回，请参见下方的退役登记。

## 已退役文件（2026-08-13）

一次全仓库引用扫描移除了没有任何维护文档、测试、合同或工具指向的归档配置。可用
`git show 3ac600a6:examples/config/Archive/training/pre_freeze_experiments/<名称>` 取回：

- `p2_ablation_longrollout_earlystop_v1.json`
- `p2_ablation_vfboost_earlystop_v1.json`
- `p2_aggressive_adaptivekl_3090.json`
  - 其唯一消费者 `tools/archive/legacy_scripts/train_p2_aggressive.sh` 在同一轮清理中被退役；
    若该退役被撤销，请将两者一并恢复。
- `p2_aggressive_stageA_test.json`
- `p2_aggressive_stageB_test.json`
- `p2_diag_smoke_continue_v1.json`
- `p2_earlystop_smoke_v1.json`
- `p2_midrun_longroll_earlystop_v2.json`
- `p2_perf_smoke_novis.json`
- `p2_rewardbalance_smoke_v1.json`
- `p2_sop_switches_smoke_v1.json`
- `p2_stability_diagnostic_v1.json`
- `p2_stability_long_earlystop_v1.json`
- `p2_visual_aggressive_24env_safeadapt_v2.json`
- `p2_visual_aggressive_24env_v2.json`
- `p2_visual_aggressive_3090_smoke_v2.json`
- `p2_visual_aggressive_3090_v2.json`
- `p2_visual_aggressive_40env_smoke_v2.json`
- `p2_visual_aggressive_40env_v2.json`
- `p2_visual_perf_smoke.json`
- `p3_takeoff_to_cruise_full_visual_navv2_mixedmode_flyoverfocus_smoke_v1.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_smoke_v1.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_smoke_v2.json`
- `p3_takeoff_to_cruise_full_visual_navv2_residual_v1.json`
- `p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v1.json`
- `p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v2.json`
- `takeoff_departure_full_visual_adaptivekl_residual_v9_corridor_smoke.json`
- `takeoff_departure_full_visual_adaptivekl_residual_v9_corridor_train.json`
- `transformer_hardware_max.json`
- `transformer_large_scale.json`
- `transformer_ppo.json`

有四个配置因维护文档仍能解析到它们而保留：
`p2_autopilot_residual_navv2_paramroute_turnaware_long_v1.json`、
`p3_takeoff_to_cruise_full_visual_navv2_multileg_smoke_v1.json`、
`p4_landing_full_visual_ils_smoke_v1.json` 和
`p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json` 由
`docs/reference_artifacts.md` 链接，其中最后一个同时是所有归档领导者配置解析到的
`execution_train_config`。

## 复活规则

不要将新文档、测试或启动命令直接指向此存档。当合同有意保留旧的封装器/控制基线时，现有的历史回归合同可能会引用已存档的配置。要恢复其中某个配置以进行主动训练，请将其复制到一个维护中的活动目录中，记录预期的场景配对，并针对当前的运行时/外观路径进行验证。
