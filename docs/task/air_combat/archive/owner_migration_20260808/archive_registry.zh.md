# 空战归档注册表

`docs/task/air_combat/archive/` 下已归档空战子项目的注册索引。

## 已归档子项目

| 子项目 | 描述 |
|--------|------|
| `a2_high_fidelity_damage_model/` | 高保真空战毁伤模型。structured-aircraft damage/effects 的 research/candidate profile，含 blast-fragmentation 证据包、G1-G5 research packets。非权威验收；stock authority、Pk 与 deterministic fuze 未放行。 |
| `a3_c2_roe_release_discipline/` | C2/ROE 发射纪律层。武器控制状态、目标身份、开火授权、single-shot-then-assess / salvo / reattack 许可与 mission observation 约束。已 accepted。 |
| `a4_authorized_first_shot_training_signal/` | 授权首发训练信号。已关闭的历史 firing-learning 线路。reward shaping、routing、diagnostics 与 opportunity penalty 没有解决发射。 |
| `a5_constrained_event_action_model/` | 受约束事件动作模型。已关闭。贡献了受约束 hold/fire_once 表面及 M3-S2 使用的 weapon-arm action-frame fix。 |
| `a6_event_value_first_event_timing/` | 事件价值与首事件时机。已关闭。hazard/deadline/window labels 暴露了有用 timing evidence，但未成为当前 firing authority。 |
| `a7_event_value_advantage_credit_head/` | Event-Value / Advantage Credit Head。已关闭。event-credit work 属于 timing-quality research history；当前 launch closure 属于 M3-S2。 |
| `a8_damage_effect_chain/` | 损伤效果链。已 accepted 的有边界切片。missile effects → 具体飞机部位损伤 → 动力/燃油/传感器/火灾/飞行消费路径传播。不增加直接坠毁或特定目标击杀规则。 |
| `a9_high_fidelity_weapon_system_accepted_with_residuals_20260616/` | 高保真武器系统。accepted：23 集群通过、5 项明确推迟，R2 EKF 定量验证已由聚焦 C++ 回归覆盖关闭，R4 马赫 Cd₀/k(M) 表已用工程代理值关闭。不声明 Pk、确定性引信、库存武器真值或武器特定权威。 |
| `flight_control_surface_model_implemented_20260620/` | 飞行控制面模型。implemented / validation green：新增 `ControlSurfaceState`、执行器滞后、q_bar/Mach 缩放的气动控制力矩，以及通过控制面效能承载的损伤耦合。不声明飞测校准或操稳品质权威。 |

## 顶层归档文档

| 文件 | 描述 |
|------|------|
| `air_combat_1v1_entry_analysis_20260516` | 空战 1v1 入口分析 |
| `air_combat_1v1_f16c_baseline_progress_20260516` | F-16C 基线进展 |
| `air_combat_1v1_freeze_plan_20260516` | 1v1 冻结计划 |
| `air_combat_1v1_stall_rootcause_followup_20260516` | 失速根因追踪 |
| `air_combat_1v1_training_smoke_progress_20260516` | 训练 smoke 进展 |
| `air_combat_1v1_weapon_chain_progress_20260516` | 武器链进展 |
| `air_combat_scenario_level_ammo_design_20260516` | 场景级弹药设计 |
