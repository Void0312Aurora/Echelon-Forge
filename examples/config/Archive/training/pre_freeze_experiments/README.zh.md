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

## 复活规则

不要将新文档、测试或启动命令直接指向此存档。当合同有意保留旧的封装器/控制基线时，现有的历史回归合同可能会引用已存档的配置。要恢复其中某个配置以进行主动训练，请将其复制到一个维护中的活动目录中，记录预期的场景配对，并针对当前的运行时/外观路径进行验证。
