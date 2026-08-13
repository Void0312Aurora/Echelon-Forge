# `src/core/mission` 边界

`core/mission` 负责训练主线所需的任务运行时，包括 mission、objective、reward、termination 和 execution episode。这里解释 tasking/command 数据并产出运行时产物，但不定义底层 component，也不做 Python 绑定。

当前 mission 层应描述为 multi-domain aware，而不是 air/flight-only。它对 air execution episode 最成熟；`MissionCommand` 字段会通过受控的 codec/state seam 承载，而 tasking packet transport 属于 engine/runtime contract 层。完整 naval mission orchestration 与 full ground runtime 行为仍不属于当前维护中的 mission scope。

## 允许

- mission runtime、objective runtime、reward runtime、termination runtime。
- `ExecutionEpisodeState`、batch prepare 与 reward breakdown 序列化。
- 面向 Python 绑定、GPU 辅助逻辑或 facade 内部实现的纯 C++ episode 产物。
- 在 episode state 中受限存储和比较 `MissionCommand` compatibility shell。

## 禁止

- ECS system tick 逻辑。
- 物理积分、传感器扫描、武器制导实现。
- Python/nanobind 绑定。
- 训练配置文件解析和 UI/API 适配。
- ground owner 存在前的 full ground movement/sensing/fires/damage runtime 或 native ground mission schema。

## 当前结构

```text
mission/
  runtime/
  episode/
    detail/
```

- `runtime/`：纯 mission/runtime kernels 和 runtime products，包括 mission、objective、reward、termination、observation、step、frame、episode runtime。这里不拥有有状态 episode 编排，也不解释 Python 或 facade contract。
- `episode/`：episode state DTO、batch prepare 与公共 reward breakdown 工具。
- `episode/detail/`：reward breakdown 私有实现。外部代码应 include `episode/` 下的公共头。

新增纯 reward/objective/termination 计算应落到 `runtime/`；新增 episode state 或 batch prepare contract 应落到 `episode/`。有状态 transition 规则属于维护中的 Python 编排，不应重新建立并行 C++ controller。

## 依赖方向

本层可以消费 `components/command`、`components/tasking`、`core/engine` 的公开 API 和 mission 相关 DTO。它不应依赖 `runtime/facade` 或 `interfaces/python`。

`episode/` 可以依赖 `runtime/`。`runtime/` 不应依赖 `episode/`。`episode/detail/` 可以依赖 `episode/` 和 `runtime/`，但不应成为跨层公开入口。
