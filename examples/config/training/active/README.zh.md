<!-- Machine-translated draft generated on 2026-05-18 from examples/config/training/active/README.md. Review before treating this file as authoritative. -->

# 活动训练条目

此目录保留尚未冻结的正在进行的训练配置。

此目录状态为`活动主线`。

## 协同巡航线路

- [cooperative_cruise_nav_v2_formation_v1.json](cooperative_cruise_nav_v2_formation_v1.json)
  - 当前P8协同执行线路的单策略巡航基线。
  - 使用`nav_v2_formation_role_v1`，使策略能够从任务指令链中获取编队和角色/参考语义。
  - 场景配对为`scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`，包含真实协同编队和任务指令中携带的编队偏移量，而非添加合成策略输入族。

## 协同起飞线路

- [cooperative_interval_takeoff_departure_nav_v1.json](cooperative_interval_takeoff_departure_nav_v1.json)
  - 协同执行的第一阶段双机间隔起飞/离场基线。
  - 使用`nav_v2_cooperative_takeoff_v1`，使每个槽位通过维护的任务指令链获取起飞程序、放行许可、间隔、跑道槽位和编队语义。
  - 场景配对为`scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json`。

- [cooperative_takeoff_to_cruise_nav_v1.json](cooperative_takeoff_to_cruise_nav_v1.json)
  - 第二阶段双机协同桥接基线：间隔起飞、离场爬升，然后多航段航线捕获。
  - 保持相同的`nav_v2_cooperative_takeoff_v1`观测合约，使起飞语义和编队/角色语义保持可见，同时任务指令已携带巡航航线。
  - 场景配对为`scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`。

- [cooperative_takeoff_to_cruise_landing_nav_v1.json](cooperative_takeoff_to_cruise_landing_nav_v1.json)
  - 第三阶段双机协同闭环基线：间隔起飞、结构化巡航/返航，然后在本场进行独立ILS着陆。
  - 保持相同的`nav_v2_cooperative_takeoff_v1`观测合约，使编队、起飞和编队语义保持可见，同时维护的任务指令链携带返航航线和着陆过渡。
  - 着陆段现在为脚本化的`landing_ils`基线重新开放一个小残余预算，使策略能够纠正最后进近/滑跑误差，而非硬限制为纯脚本着陆。
  - 场景配对为`scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json`。

- [cooperative_takeoff_to_cruise_nav_hmoe_v1.json](cooperative_takeoff_to_cruise_nav_hmoe_v1.json)
  - 相同起飞至巡航桥接的HMoE实验条目，使用`HierarchicalMoEExecutionPolicy`，包含共享主干、共享动作头基线和语义路由的残差专家。
  - 保持相同的`nav_v2_cooperative_takeoff_v1`观测合约，并遵循真实输入边界：仅向策略暴露驾驶员可接收的维护任务语义。
  - 场景配对仍为`scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json`，确保基线与HMoE直接可比。

- [cooperative_takeoff_to_cruise_nav_shared_fair_v1.json](cooperative_takeoff_to_cruise_nav_shared_fair_v1.json)
  - 公平控制共享基线，用于继续起飞至巡航HMoE对比。
  - 在课程、封装器、运行时、诊断和优化器端KL控制方面与HMoE线路对齐，使主要差异仅停留在策略架构边界。

- [cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json](cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json)
  - 相同公平控制线路的配对HMoE配置。
  - 当需要比早期探索性配置更严格的共享与HMoE A/B对比时，使用此对。

## 空战1v1线路

- [air_combat/README.md](air_combat/README.md)
  - 当前空战线路的维护`1v1`执行层HMoE条目。
  - 保持第一个对手冻结为场景声明的脚本化红方战斗机，以便在转向自对弈或`2v2`之前验证作战任务合约和HMoE运行时链。

## 备注

- 这是当前向前推进的训练线路，而非冻结的验收集。
- 保持条目真实：仅飞行员可接收的字段应属于面向策略的输入。
- 在协同执行路径和场景合约稳定之前，请勿将此配置升级到`frozen/`。
- 协同巡航线路是可选的协同基准线路，与冻结的长机/执行基线并存。
- 对于协同起飞至巡航桥接的直接HMoE控制实验，优先使用`*_shared_fair_v1`和`*_hmoe_fair_v1`对，以保持非策略超参数对齐。
- 不要将活动配置指向`examples/config/Archive/**`；如果旧设置仍需要维护使用，则先将其重新表达在`frozen/`或其他维护兼容性位置下。
