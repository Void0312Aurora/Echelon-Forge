# 通用空海军

状态：已于 `2026-05-18` 补充收敛入口；该工作线仍有部分后续项处于活跃状态。

## 当前状态

- `common / air / naval` 拆分已经不再只是分析议题；主冻结计划中已记录到 `WP8` 的较大范围落地结果。
- 当前已经形成 DTO 边界、Python profile 分发、contracts、任务观测 taxonomy，以及第一批 naval profile 骨架等基础结构。
- 该主题尚未完全封口：更广范围的运行时/工具层跟进和后续 naval 扩展仍然存在，但应从新的后续任务单继续推进，而不是重新把分析文档当主入口。

## 已完成基础 vs. 后续承接

- 已完成基础：
  `common` 与 `air` 归属冻结、保兼容 DTO 拆分、profile/dispatch seam、第一批 contract 迁移、mission observation taxonomy 收敛，以及最小 naval profile 骨架。
- 后续承接项：
  更广范围 air-first helper 的物理迁移、更完整的 `tests/contracts` 目录家族整理，以及后续 naval runtime / eval 扩展。

## 推荐阅读顺序

- 当前主记录：
  [common_air_naval_modular_split_plan_20260515.zh.md](common_air_naval_modular_split_plan_20260515.zh.md)
- 历史的拆分前分析：
  [archive/common_air_naval_modular_split_analysis_20260515.zh.md](archive/common_air_naval_modular_split_analysis_20260515.zh.md)

已被主计划吸收的历史分析现统一放入 [archive/README.zh.md](archive/README.zh.md)。
