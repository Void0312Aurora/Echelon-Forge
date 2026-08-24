# `src/core/mission/episode/detail` 边界

`mission/episode/detail` 存放剩余 episode 工具的私有实现，不是稳定的跨层 API。

## 允许

- reward breakdown 汇总与稳定 JSON 输出。
- 仅供 `mission/episode` 公共工具内部使用的小型辅助逻辑。

## 禁止

- 被 `interfaces/python`、`runtime/facade`、`gpu` 或 `core/engine` 直接 include。
- 定义新的 public episode contract；公共 contract 应放在 `mission/episode`。
- 实现纯 reward/objective/termination 公式；这些应放在 `mission/runtime`。

## 依赖方向

本目录可以依赖 `mission/episode` 与 `mission/runtime`。仅实现内部使用的辅助逻辑应放入匿名命名空间，避免形成意外的跨层 API。
