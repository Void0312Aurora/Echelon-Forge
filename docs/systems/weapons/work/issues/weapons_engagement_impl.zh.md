# 武器与交战规则实现说明

Language:
- English canonical: [weapons_engagement_impl.md](weapons_engagement_impl.md)
- Chinese companion: `weapons_engagement_impl.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/weapons/work/issues/weapons_engagement_impl.md`
Owner: `systems/weapons`
Last verified: `not established`
Content status: not reverified during the 2026-08-07 ownership migration.

本文件记录当前代码层落地的武器/交战规则实现，以便与规划对照。

## 已实现内容

### 发射初始化与运行时调参
- `SimulationKernel::fire_missile(...)` 会解析已选择的弹药，并在
  `src/core/engine/simulation_kernel_weapon_api.cpp` 中构建导弹发射时的
  运行时状态。
- 当前发射阶段会写入：
  - `Missile.guidance_delay_s` 与 `Missile.guidance_update_period_s`
  - `Missile.max_flight_time_s` 与 `Missile.nav_gain`
  - `Missile.seeker_fov_deg`、`Missile.seeker_lock_range` 等寻标器约束
  - track memory、seeker activation、可选 midcourse datalink 等字段
  - boost/sustain、阻力、自动驾驶相关调参字段

### 寻标筛选与轨迹记忆
- 引导仅会在 `Missile.guidance_delay_s` 之后启动，并可由
  `Missile.guidance_update_period_s` 限制更新频率。
- 候选探测会按敌我关系、指定目标、寻标器视场、锁定距离，以及末制导
  阶段是否具备本地传感器命中等条件筛选。
- 当直接探测丢失时，导弹可在 `Missile.track_memory_timeout_s` 时间内
  继续沿滤波后的轨迹记忆飞行；若无有效轨迹，则退回弹道飞行。
- `Missile.midcourse_datalink_supported` 允许在末制导接管前，使用非本机
  探测结果继续喂给引导。

### 引导与飞行动力学
- 当前引导模型位于 `src/models/weapons/default_guidance_model.cpp`。
- 引导指令由捕获项与基于 LOS 方位/俯仰角速率的 PN 风格指令共同构成。
- 侧向过载由 `Missile.guidance_max_lateral_g` 限制，并通过自动驾驶响应
  项进行整形，而不是简单地直接用 `Missile.turn_rate` 限幅。
- `Missile.turn_rate` 仍然保留为调参输入；当侧向过载上限未显式给出时，
  运行时会用它来推导兜底限制。
- 运行时还会更新 boost/sustain 推力、阻力、燃料消耗，以及
  `Missile.max_flight_time_s` 自毁行为。

## 代码入口
- 导弹发射与调参：`src/core/engine/simulation_kernel_weapon_api.cpp`
- 引导模型：`src/models/weapons/default_guidance_model.cpp`
- 引导系统注册：`src/systems/combat/guidance_system.h`
- 导弹数据结构与运行时状态：`src/components/combat/weapon.h`

## 后续计划（与前瞻文档对齐）
- 继续细化发射包线估计与 scenario 级规则配置。
- 在现有 track-memory 模型之外，扩展 seeker 失锁 / 对抗措施行为。
- 命中结果分层：Hit / MissionKill / MobilityKill / SensorKill。
- 评估是否需要新增引导模型或更高保真的末制导逻辑。
