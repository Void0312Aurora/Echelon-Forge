# 已归档 JSON 契约

此目录包含从维护态 `tests/contracts/` 根目录移出的 JSON contract 规范。

这些归档规范仅用于追溯和对照，不应计入活跃 contract 覆盖；contract batch runner
也不应通过 glob 选中它们。

当前归档 contract 面：

- `env_regression/`：已退役的 raw `UniversalEnv` reset/step/reward/observation 规范。
- `scripted_bridge/`：依赖 raw env executor 的已退役 scripted wrapper bridge 规范。
- `unit/`：用于对照的历史 unit-regression 基线。
