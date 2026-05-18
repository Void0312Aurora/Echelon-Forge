# `src/systems/core` 边界

`systems/core` 保存通用 ECS operation system。它应只包含跨域、每 tick 都可能需要的基础 world mutation。

## 允许

- operation/lifecycle 相关 system。
- 通用状态清理、激活状态推进等基础逻辑。

## 禁止

- 物理、战斗、平台系统或视觉专用逻辑。
- component 定义。
- runtime owner 或 Python binding。

## 迁移备注

如果逻辑只服务某个业务域，应放入对应 `systems/<domain>` 目录，不要扩大 `systems/core`。
