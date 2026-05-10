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

## 拆分目标

`execution_episode_controller.cpp` 应逐步拆成：

- `episode_transition_runtime.cpp`
- `episode_reward_breakdown.cpp`
- `mission_command_codec.cpp`

controller 主文件保留 state import/export、prepare、evaluate、step 的协调职责。

## 依赖方向

本层可以消费 `components/command`、`components/tasking`、`core/engine` 的公开 API 和 mission 相关 DTO。它不应依赖 `runtime/facade` 或 `interfaces/python`。
