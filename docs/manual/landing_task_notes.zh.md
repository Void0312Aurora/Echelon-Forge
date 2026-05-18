<!-- Machine-translated draft generated on 2026-05-18 from docs/manual/landing_task_notes.md. Review before treating this file as authoritative. -->

# 着陆任务说明

本文档定义了起飞和巡航之后的下一训练阶段的初始着陆任务支架。

## 任务语义

- `command_code = 4`
- 含义：跑道对齐的着陆/最后进近任务
- `target_heading`：跑道最终航向
- `target_altitude`：跑道标高/着陆参考高度
- `target_speed`：进近参考速度（类`Vref`目标）
- `threshold_crossing_height_m`：目标高度超出跑道入口，用于稳定进近；ILS下滑道参考对齐此点
- 垂直航迹引导通过观察中已有的仪表式ILS通道提供：
  `ils_valid`、`loc_dev`、`gs_dev`、`dme_m`

关键设计选择是保持着陆的真实性优先：

- 侧向和垂直航迹提示来自类似航向道/下滑道的可观测项
- 策略不直接获得跑道航向或特权着陆点几何信息
- 跑道几何信息仅用于奖励塑造和成功评估

对于面向人类的可视化和场景语义，着陆路径现在被视为一个序列而不是单个地面点：

- 在ILS最后航向上切入并稳定
- 在跑道入口上方穿越，而不是在接地时
- 在跑道更远处的着陆区内接地
- 保持可控通过滑跑并减速到类似低速停止的状态

## 新任务文件

- 训练场景：
  `/home/void0312/CMO/scenarios/landing/landing_ils_final_train_v1.json`
- 评估场景：
  `/home/void0312/CMO/scenarios/landing/landing_ils_final_eval_v1.json`
- 维护的训练配置：
  `/home/void0312/CMO/examples/config/training/frozen/execution/p4_landing_retrain_v1.json`
- 历史工件来源配置：
  `/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/p4_landing_full_visual_ils_smoke_v1.json`

## 添加的着陆钩子

环境/目标属性：

- `on_runway_geom`
- `on_runway`
- `on_ground`
- `ground_speed`
- `sink_rate_abs_mps`
- `vertical_speed_abs_mps`
- `ils_localizer_abs`
- `ils_glideslope_abs`
- `dme_m`

奖励钩子：

- `approach_localizer_weight`
- `approach_localizer_improve_weight`
- `approach_glideslope_weight`
- `approach_glideslope_improve_weight`
- `approach_dme_progress_weight`
- `approach_capture_bonus`
- `landing_sink_rate_penalty_weight`

可选的DME质量门控：

- `approach_dme_progress_localizer_band`
- `approach_dme_progress_glideslope_band`
- `approach_dme_progress_quality_power`

着陆奖励设计现在采用混合策略：

- 适度的绝对偏差惩罚保持进近稳定
- 改进奖励为减小航向道/下滑道误差支付
- DME进度可由ILS质量门控，因此错误对齐的俯冲向入口不会像稳定进近一样获得奖励
- 捕获奖励使得“正确继续进近”比故意提前终止更好

跑道接地成功评估使用与任务逻辑相同的实际地面接触包络：具体来说，最终的`altitude_agl`成功阈值与着陆`on_ground`阈值对齐，而不是拒绝稳定着陆滑跑的过于严格的数值。

滑跑停止成功应使用`ground_speed`，而不是`speed`/IAS：

- 指示空速保持相对于空气，即使在飞机物理停止在跑道上后，在有风的情况下也可能保持非零
- 因此滑跑完成由低地面速度加上在跑道地面接触条件判断
- 地面接触模型现在也应用低速刹车保持/静摩擦行为，以使接地不会留下不现实的长时间蠕变尾巴

当前训练默认还包括：

- 着陆代理的跑道相关空中初始位置随机化
- 训练初始位置范围保持在真实捕获包络内，以便策略首先学习跑道航向对齐和稳定进近，而不是立即投入不可恢复的偏移情况
- 一个脚本化的`landing_ils`基线选项，用于在全17维动作空间中进行残差PPO训练

这些钩子很通用，可以支持后续的着陆课程，例如：

- 稳定直线进近ILS
- 偏置航向道恢复
- 侧风着陆
- 拉平/滑跑精炼
- 复飞决策任务
