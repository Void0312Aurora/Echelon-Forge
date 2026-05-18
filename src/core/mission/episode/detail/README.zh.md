# `src/core/mission/episode/detail` 边界

`mission/episode/detail` 存放 `ExecutionEpisodeController` 的内部业务辅助逻辑。这里的头用于拆分实现文件和单域复用，不是稳定的跨层 API。

## 允许

- mission-command JSON 往返和 route waypoint materialization。
- post-waypoint、landing transition 和 controller pre-step behavior update。
- reward breakdown 汇总与稳定 JSON 输出。

## 禁止

- 被 `interfaces/python`、`runtime/facade`、`gpu` 或 `core/engine` 直接 include。
- 定义新的 public episode contract；公共 contract 应放在 `mission/episode`。
- 实现纯 reward/objective/termination 公式；这些应放在 `mission/runtime`。

## 依赖方向

本目录可以依赖 `mission/episode` 与 `mission/runtime`。新增辅助逻辑时应保持 `episode_controller_detail` 命名空间，避免被误当成公共 API 使用。
