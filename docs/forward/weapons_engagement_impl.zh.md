# 武器与交战规则实现说明

本文件记录当前代码层落地的武器/交战规则实现，以便与规划对照。

## 已实现内容

### 导弹引导延迟与更新周期
- 通过 `Missile.guidance_delay_s` 控制导弹发射后延迟引导。
- 通过 `Missile.guidance_update_period_s` 控制引导更新频率。
- 相关字段：
  - `Missile.launch_time`
  - `Missile.last_guidance_time`

### 寻标器锁定条件
- 视场限制：`Missile.seeker_fov_deg`。
- 锁定距离：`Missile.seeker_lock_range`。
- 条件不满足时，导弹保持当前速度方向（惯性飞行）。

### 引导模型
- 当前引导为 2D PN（比例导航）：
  - 以 LOS 角速度驱动转弯率。
  - `Missile.nav_gain` 为 PN 增益。
  - 转弯率受 `Missile.turn_rate` 限制。

## 代码入口
- 导弹参数设置：`src/core/simulation_kernel.cpp`
- 引导逻辑：`src/models/default_guidance_model.cpp`
- 引导系统：`src/systems/guidance_system.h`
- 数据结构：`src/components/weapon.h`

## 后续计划（与前瞻文档对齐）
- 引导过载限制（由 `max_g` 或导弹模型约束）。
- 引导/传感器的目标跟踪延迟与失锁逻辑。
- 命中结果分层：Hit / MissionKill / MobilityKill / SensorKill。
- 发射包线估计与规则配置（scenario 级）。
