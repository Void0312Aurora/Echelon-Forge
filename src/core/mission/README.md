# `src/core/mission` 边界

`core/mission` 负责 mission、objective、reward、termination、execution episode 和训练主线需要的任务运行时。这里解释 tasking/command 数据并产出 runtime products，但不定义低层 component，也不做 Python 绑定。

## 允许

- mission runtime、objective runtime、reward runtime、termination runtime。
- `ExecutionEpisodeController` 及其 state import/export。
- mission command codec、episode transition、reward breakdown helper。
- 面向 `WorldBatchRuntime` 或 `RuntimeFacade` 的纯 C++ episode products。

## 禁止

- ECS system tick 逻辑。
- 物理积分、传感器扫描、武器制导实现。
- Python/nanobind 绑定。
- 训练配置文件解析和 UI/API 适配。

## 当前结构

```text
mission/
  runtime/
  episode/
    detail/
```

- `runtime/`：纯 mission/runtime kernels 和 runtime products，包括 mission、objective、reward、termination、observation、step、frame、episode runtime。这里不拥有 episode controller state，也不解释 Python 或 facade contract。
- `episode/`：episode state、batch prepare 和 `ExecutionEpisodeController`。这里负责把 scenario/env state 编排成 runtime inputs，并把 runtime products 应用回 episode state。
- `episode/detail/`：只服务 episode controller 的内部 helper，包括 mission-command codec、post-waypoint/landing transition、reward breakdown JSON。外部代码不应直接 include 这里的头，除非是在拆 controller 期间补充同一 detail 域能力。

后续新增 mission JSON 字段、transition 规则或 reward breakdown term，应先落到 `episode/detail/` 中对应 helper，而不是回填到 controller 主文件。新增纯 reward/objective/termination 计算，应落到 `runtime/`；新增 episode state import/export 或 batch prepare contract，应落到 `episode/`。

## 依赖方向

本层可以消费 `components/command`、`components/tasking`、`core/engine` 的公开 API 和 mission 相关 DTO。它不应依赖 `runtime/facade` 或 `interfaces/python`。

`episode/` 可以依赖 `runtime/`。`runtime/` 不应依赖 `episode/`。`episode/detail/` 可以依赖 `episode/` 和 `runtime/`，但不应成为跨层公开入口。
