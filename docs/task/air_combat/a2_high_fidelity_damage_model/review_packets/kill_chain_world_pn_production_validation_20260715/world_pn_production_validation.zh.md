# 第一阶段：世界系 LOS-history PN 生产候选验收

结论：候选通过第一阶段门槛，但尚未写入 AIM-120 默认配置。

- 样本数：`20` 个左右镜像 anchor case。
- legacy 默认与显式 legacy 最大差：`0 m`。
- 生产候选与 diagnostics history profile 最大差：`1.00364161426e-12 m`。
- 左右镜像最大差：`5.04054496719e-05 m`。
- N 类最大最近距：`9.257067 m`（fuze 半径 15 m）。
- 旧 O 类进入 fuze 的 case：`guidance_exact_cv_16km_m30deg`, `guidance_exact_cv_16km_p30deg`

验收门：

- `legacy_default_unchanged`: PASS
- `production_matches_diagnostic_history`: PASS
- `mirror_symmetry`: PASS
- `nominal_cells_inside_fuze`: PASS

旧 O 的移动只登记为窗口结构变化，不在第一阶段用旧标签否决坐标机制。
阶段二继续处理 track 世界系运动估计和重复测量消费。
