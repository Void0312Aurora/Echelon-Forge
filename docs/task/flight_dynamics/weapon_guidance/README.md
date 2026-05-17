# 武器与制导子项目

状态：`2026-05-17` 已形成 `P0/P1` 实施包；当前代码已跑通 seeker-only guidance、最小 3DoF/PN-autopilot surrogate、shared missile tuning 与 launch/runtime 守门测试，文档中的未完成项需要以 `P1` 包里的最新核对结论为准。

本子项目收纳武器链、导引头、制导回路、近炸/毁伤与其数据参考方案文档。

## 文档入口

- [武器系统与制导回路现实性分析](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
  作用：冻结记录当前武器链与导弹制导的主要失真点。
- [武器系统与制导回路真实化核实与落地方案](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md)
  作用：核实调研结论并整理可落地实现方案与数据来源。
- [武器/制导真实化 P0 实施包](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_p0_implementation_package_20260516.zh.md)
  作用：记录 seeker-only guidance、最小 `3DoF` 能量学与 PN/autopilot surrogate 的首轮实现范围。
- [武器/制导真实化 P1 实施包](/home/void0312/Workshop/CMO/docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)
  作用：承接共享收尾、数据接入、引信/毁伤深化与配置暴露工作。

## 维护约定

1. 后续武器参数参考表、导引头标定摘记和外部数据来源说明优先放在本目录。
2. 若继续拆出导弹数据库或引信子方向，应从本目录继续分层，而不是回到 `flight_dynamics/` 顶层。
