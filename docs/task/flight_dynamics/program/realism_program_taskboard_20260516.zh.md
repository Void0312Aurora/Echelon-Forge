# 真实化任务总表

状态：`2026-05-16` 主线程收敛版。

关联文档：

- [飞行动力学现实性分析、失真清单与空战前置门槛](../flight/flight_dynamics_realism_analysis_20260516.zh.md)
- [飞行动力学真实化 P0 实施包](../flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
- [传感器/态势感知真实化核实与实现方案](../sensor_situation/sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [传感器/态势真实化 P0 实施包](../sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md)
- [武器系统与制导回路真实化核实与落地方案](../weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md)
- [武器/制导真实化 P0 实施包](../weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md)

文档目的：

- 把三条方向的核实结论、实现建议、数据源和 `P0` 包收敛成一个统一入口。
- 明确当前真实性推进的推荐顺序、依赖关系和停止条件。
- 为后续开分支、分 PR、补数据和补测试提供同一张任务板。

---

## 一、总判断

当前仓库的空战主线已经不是“完全没有物理”的壳子，但距离“可信战术仿真”仍有明显缺口。

这三个缺口不是独立问题，而是耦合问题：

1. `飞行动力学`
   - 决定平台能量管理、姿态恢复、高攻角行为是否可信
2. `传感器/态势`
   - 决定目标能否被合理地发现、确认、共享与分类
3. `武器/制导`
   - 决定导弹是否依赖合理的 seeker、能量与引信逻辑，而不是“看见就必中”

如果只修其中一条线，另外两条仍然会把训练结果带歪。

因此更合适的推进口径不是“先把某个方向做到很深”，而是：

- 先把三条线都推进到 `P0 可用且可测试`
- 再决定进入哪条线的 `P1`

---

## 二、推荐优先级

### 2.1 P0-A：先冻字段骨架和测试骨架

这一步先于任何“公式升级”。

原因：

- 飞行动力学需要 `aero_tuning / engine_tuning / stall_state`
- 传感器需要 `SNR/Pd / M-of-N / track quality`
- 武器需要 `missile tuning / seeker state / autopilot surrogate`

如果字段骨架不先定下来，后面每做一条线都会反复返工。

### 2.2 P0-B：先解决最会污染训练信号的三件事

这三件事建议作为第一批代码工作并行推进：

1. `高攻角恢复趋势`
   - 来自飞行动力学方向
   - 目标：不再只靠 failfast 末端终止来“处理失速”
2. `DataLink 不再直接共享真值风格 contact`
   - 来自传感器/态势方向
   - 目标：切断最明显的上帝视角泄漏
3. `Guidance 切断 target truth 直接依赖`
   - 来自武器/制导方向
   - 目标：不再让导弹“看见 seeker，计算靠真值”

### 2.3 P0-C：再补能量与跟踪的一致性

下一批建议接上：

1. 发动机瞬态 + 油耗/仪表一致性
2. SNR/Pd 近似 + M-of-N
3. 3DoF 导弹 boost/coast + drag + mass

这一层的目标不是“接近公开手册中的每个数字”，而是先把输入-输出因果链改回合理方向。

---

## 三、依赖关系

### 3.1 飞行动力学 -> 武器/制导

导弹的 3DoF 能量学和 seeker 几何虽然可以先独立推进，但：

- 高空/高速空气密度、声速、阻力趋势
- 平台高攻角行为
- closure rate 与发射时机

都依赖飞行动力学这一侧的基础物理口径。

因此：

- 武器方向可以先做 `truth cut + seeker state + 3DoF 骨架`
- 但真正做参数标定前，飞行动力学至少要先把大气/推进/失速恢复的口径稳住

### 3.2 传感器/态势 -> 武器/制导

武器方向对传感器方向有直接依赖：

- seeker contact 质量
- M-of-N 后的航迹确认
- 数据链中制导
- 干扰和诱饵进入 seeker 视场后的状态演化

因此：

- 传感器方向至少要先交付 `track quality / confirm state / datalink track report`
- 武器方向再去接 seeker state 和 lock memory

### 3.3 飞行动力学 -> 传感器/态势

这一条依赖最弱，但仍存在：

- 平台姿态和速度会影响 Doppler、beam aspect、line-of-sight 几何
- RCS aspect、视轴角和太阳背景都依赖姿态

因此：

- 传感器方向可以先做大部分 `P0`
- 但某些高阶验证要等飞行动力学姿态语义继续收敛

---

## 四、三条线的 P0 任务包摘要

### 4.1 飞行动力学 P0

主文档：

- [flight_dynamics_realism_p0_implementation_package_20260516.zh.md](../flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md)

核心目标：

1. 建立 `aero_tuning / engine_tuning` 参数骨架
2. 建立 `stall_state / alpha_dot / propulsion_state`
3. 为后续压缩性、发动机瞬态、pitch break 打基础

建议最先动的文件：

- `src/content/unit_definition.h`
- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`
- `src/components/physics/dynamics.h`
- `src/components/physics/forces.h`
- 新增 `src/components/physics/flight_dynamics_tuning.h`

最小守门测试：

- `throttle_step_response`
- `stall_pitch_break_and_recovery`
- `mach_drag_rise_trend`
- `level_accel_vs_alt_mach`

### 4.2 传感器/态势 P0

主文档：

- [sensor_situation_realism_p0_implementation_package_20260516.zh.md](../sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md)

核心目标：

1. 引入 `SNR/Pd` 近似
2. 引入 `M-of-N` 确认
3. 给 `TrackManager` 加最小 `alpha-beta` 滤波
4. 让 `DataLink` 改传 `track/report`，不再直接写 `ContactList`

建议最先动的文件：

- `src/components/systems/sensor.h`
- `src/components/systems/track_management.h`
- `src/components/systems/comm.h`
- `src/components/command/common/comm_message.h`
- `src/models/systems/default_sensor_model.cpp`
- `src/systems/systems/sensor_system.h`
- `src/systems/systems/track_manager_system.h`
- `src/systems/systems/data_link_system.h`

最小守门测试：

- 边缘目标的 `Pd` 趋势
- `2-of-3` 航迹确认
- 滤波后航迹平滑性
- 数据链共享不再直接生成本地 contact

### 4.3 武器/制导 P0

主文档：

- [weapon_guidance_realism_p0_implementation_package_20260516.zh.md](../weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md)

核心目标：

1. guidance 切断对 target truth 的直接依赖
2. 导弹从“恒速 Rodrigues 旋转”升级到 `3DoF boost/coast + drag + mass`
3. PN 从几何旋转升级到“加速度指令 + 一阶 autopilot surrogate”

建议最先动的文件：

- `src/core/engine/simulation_kernel.h`
- `src/core/engine/simulation_kernel_weapon_api.cpp`
- `src/components/combat/weapon.h`
- `src/models/weapons/default_guidance_model.cpp`
- `src/models/weapons/default_effects_model.cpp`
- `src/systems/combat/damage_system.h`

最小守门测试：

- seeker-only lock / break / reacquire
- 3DoF 速度衰减与助推段趋势
- PN 过载/加速度有界
- near miss / fuze / damage 分层

---

## 五、数据源策略

三条线都已经确认：当前本地数据库和参数配置不足以支撑真实化，必须补一轮外部参考。

原则：

1. `一手资料优先`
   - NASA / NOAA / FAA / ITU / NATO 等公开资料
2. `二手工程资料次之`
   - AeroBench、JSBSim、MathWorks 文档、公开仿真教材
3. `社区/非官方资料可用，但只做初始值或 sanity check`
   - DCS/BMS/论坛摘录/CMANO 数据库

---

## 六、推荐实施顺序

建议按下面顺序推进，而不是三条线完全独立乱序开工。

### 阶段 1：只冻字段与配置路径

目标：

- 三条线都把 `P0` 必需字段加进去
- loader / factory / API 能把数据读通
- 不急着接入完整运行逻辑

### 阶段 2：切断最明显的上帝视角

目标：

1. DataLink 不再直接共享 `ContactList`
2. guidance 不再直接读 target truth 做 PN
3. IFF/分类和 track quality 至少先有“模糊层”

### 阶段 3：补最值钱的动态行为

目标：

1. stall / pitch break / 高攻角恢复
2. propulsion transient
3. seeker track state + missile 3DoF
4. SNR/Pd + M-of-N + alpha-beta

### 阶段 4：再进 P1

这时才适合继续：

- 压缩性更深的修正
- IFF / data link 更完整的语义
- 近炸与毁伤的更细层次
- 阵风、湍流、复杂诱饵/干扰

---

## 七、建议的停止条件

在 `P0` 完成前，不建议把以下结果当成“可信空战结论”：

- 不同机型之间的能量机动优劣
- 某类雷达 / seeker / data link 的真实战术价值比较
- 某型导弹的命中概率和发射包线优劣
- 高攻角格斗策略是否“真实有效”

`P0` 完成后，才建议重新评估：

1. 是否重启更深入的 1v1 训练
2. 是否开始做 P1 级真实化
3. 是否需要重新标定已有奖励与终止逻辑

---

## 八、当前主线程建议

如果现在就要开工，我建议第一轮不是同时大改三条线，而是按这个顺序：

1. `fields-only PR`
   - 三条线统一把 `P0` 字段和配置路径冻住
2. `anti-cheat PR`
   - 先切掉最明显的上帝视角：`DataLink truth leak` 和 `guidance truth dependence`
3. `dynamics PR`
   - 飞行动力学的 `stall_state + propulsion_state`
4. `tracking PR`
   - `SNR/Pd + M-of-N + alpha-beta`
5. `missile PR`
   - `3DoF + PN accel surrogate + fuse layering`

这样推进的好处是：

- 每一轮都能单独验收
- 每一轮都有明确的真实性收益
- 不会因为某一条线做到一半就把另外两条拖进返工
