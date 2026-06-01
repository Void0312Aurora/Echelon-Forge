# 冻结执行课程

本目录包含维护的冻结后执行层课程。

此目录的状态为“冻结基线”。

## 阶段顺序

1. [p2_takeoff_retrain_v1.json](p2_takeoff_retrain_v1.json)
2. [p3_takeoff_to_cruise_retrain_v1.json](p3_takeoff_to_cruise_retrain_v1.json)
3. [p4_landing_retrain_v1.json](p4_landing_retrain_v1.json)
4. [p4b_cruise_to_landing_retrain_v1.json](p4b_cruise_to_landing_retrain_v1.json)
5. [p5_continuous_retrain_v1.json](p5_continuous_retrain_v1.json)
6. [p5_continuous_coldstart_retrain_v2.json](p5_continuous_coldstart_retrain_v2.json)

## 推荐场景配对

- `p2`
  - `scenarios/takeoff/takeoff_stage1_runway45_stresswind.json`
- `p3`
  - `scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_train_v2.json`
- `p4`
  - `scenarios/landing/landing_ils_final_train_v1.json`
- `p4b`
  - `scenarios/combined/cruise_to_landing_continuous_train_v1.json`
- `p5`
  - `scenarios/combined/takeoff_to_landing_continuous_train_v1.json`
- `p5 冷启动`
  - `scenarios/combined/takeoff_to_landing_continuous_train_v1.json`

## 备注

- 这些配置现在已调整为历史上成功的 `p2/p3/p4/p5` 训练备份，而不是早期首次重写的结果。
- `p2` 遵循已存档的起飞-离场控制器修复线，因为这是仓库中幸存的最强跑道起飞参考。
- `p3`、`p4` 和 `p5` 有意地镜像了历史上成功的重新训练/烟雾测试配置，尽量减少偏离。
- 专用的 `p4b` 桥仍然是新的，但其预算和课程现在保持在与历史上 `p5` 连续线一致的家族内。
- 历史影响仅作为谱系：维护的桥和合约应直接使用这些冻结配置，而不是指向 `examples/config/Archive/**`。
- 执行配置现在默认设置 `env.step_info_mode=terminal`。这样可以保留终端诊断，同时避免在热路径上打包每步 step-info。
- 截至 2026-04-18 经过验证的 `p5` 比较，维护的 `p5` 配置现在默认使用 CPU 主线的世界批处理路径：
  `runtime.world_batch_vec_env=true`、`batch_observation_backend=compiled`、
  `batch_visual_backend=compiled` 以及
  `env.execution_step_runtime_mode=compiled`。
- 维护的运行时立场：
  精确的世界步进保持在 CPU `SimulationKernel::step()` 路径上，并且
  维护的默认值避免选择可选的 GPU 辅助程序，除非后续基准测试明确重新推广其中一个。
- `batch_visual_backend` 现在默认保持 `compiled`，因为最新的维护的 `p5` 训练和 rollout 端比较显示，保留的 `gpu_host` 辅助程序在当前生产路径上功能正常但速度较慢。
- `batch_observation_backend` 也保持 `compiled`。更广泛的 `gpu_host/fullgpu` 观察线仅可用于受控的基准测试和兼容性检查，不作为维护的默认值。
- 维护的 `p5` 配置的预期构建/运行时矩阵：
  - 仅 CPU 构建：
    `world_batch_vec_env` 保持可用，视觉/观察辅助程序保持在使用维护的编译 CPU 路径上。
  - 无可用运行时设备的 CUDA 构建：
    相同的配置仍然可以使用相同的编译默认值启动。
  - 有可用运行时设备的 CUDA 构建：
    维护的配置仍然保持相同的编译默认值；可选的 `gpu_host` 辅助程序实验仅作为显式选择加入覆盖。
- `p5_continuous_retrain_v1.json` 是一个热启动/继续配置。它镜像了历史上成功的 `p5` 重新训练，但总步数为 `32768` 且使用 `4` 个环境，每个环境仅获得 `8192` 步，约 `409.6 秒` 的模拟时间。
- 当前完整的连续路线约为 `121-125 公里`，按场景的航路点速度剖面计算，大致为 `755-776 秒`。因此，在 `v1` 下，冷启动 `p5` 训练无法可靠地看到完整的任务完成。
- 在新架构上使用 `p5_continuous_coldstart_retrain_v2.json` 进行冷启动/完整路线重新训练。它减少了 `n_envs` 并增加了总步数，使每个环境可以经历多个完整的 episode。
