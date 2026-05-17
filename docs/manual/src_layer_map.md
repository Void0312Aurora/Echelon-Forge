# Code Layer Map

状态：`2026-05-18` 维护版。
本文档回答三个问题：

1. 当前主线代码从 C++ runtime 到 Python 训练入口是怎样串起来的。
2. 各个子系统的职责边界写在哪些 README / 方案文档里。
3. 出问题时应该先看哪个目录，而不是在整个仓库里盲搜。

如果某份历史任务记录、旧计划或归档文档与这里冲突，优先相信当前代码树中的活动 README，以及 `docs/plan/architecture/` 下仍作为主线的架构说明。

## 1. 当前主线总览

当前维护中的依赖方向应理解为：

```text
interfaces/python
  -> runtime/facade
    -> core/engine + core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime-visible packets
  -> 不拥有 canonical CPU truth path
```

如果按“运行链路”来理解，则更接近：

```text
SimulationKernel / WorldBatchRuntime
  -> mission runtime / episode controller
    -> RuntimeFacade / Python bindings
      -> gym_envs / scenario loader / python runtime support
        -> training / evaluation / diagnostics / contracts
```

这条主线的权威入口主要有三组：

- [README.md](../../README.md)
  - 项目总入口，说明主线能力、常用命令和 repo 级边界。
- [src/README.md](../../src/README.md)
  - `src/` 分层边界和依赖方向。
- [docs/plan/architecture/README.md](../plan/architecture/README.md)
  - 当前架构主方案、分层冻结记录和性能/路线调研。

## 2. 哪些文档是“当前权威入口”

如果你要判断某个子系统的职责边界是否已经文档化，优先看这些层级：

- `src/` 下各目录 README
  - 这是当前最直接、最接近代码的边界说明。
- `docs/plan/architecture/`
  - 这是“为什么这样分层”的主方案层。
- `tests/README.md`
  - 这是“哪些约束已经进入自动验证”的入口。
- `python/README.md`、`gym_envs/README.md`、`tools/README.md`
  - 这是 Python 运行时、环境封装和工具面的职责入口。

不应默认当作当前权威的文档：

- `docs/Archive/`
  - 保留历史讨论和旧方案，不作为当前实现默认依据。
- `docs/temp/`
  - 草稿/临时分析，不作为维护主线依据。
- 具体任务记录中的实施包、进展报告、checkpoint
  - 可用于追溯背景，但不应替代对应目录下 README 的边界说明。

## 3. `src/` 层

`src/` 是 C++ runtime 主线。它已经有比较完整的分层边界说明，是当前“子系统职责是否有详细文档”的 strongest evidence。

优先阅读：

- [src/README.md](../../src/README.md)
- [src/core/README.md](../../src/core/README.md)
- [src/runtime/README.md](../../src/runtime/README.md)
- [src/interfaces/README.md](../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../src/interfaces/python/README.md)

### `src/components/`

职责：

- ECS component。
- command / tasking DTO。
- 可绑定、可持久化的轻量值类型。

边界入口：

- [src/components/README.md](../../src/components/README.md)
- [src/components/command/README.md](../../src/components/command/README.md)
- [src/components/command/common/README.md](../../src/components/command/common/README.md)
- [src/components/command/air/README.md](../../src/components/command/air/README.md)
- [src/components/tasking/README.md](../../src/components/tasking/README.md)
- [src/components/tasking/common/README.md](../../src/components/tasking/common/README.md)
- [src/components/tasking/air/README.md](../../src/components/tasking/air/README.md)
- [src/components/tasking/naval/README.md](../../src/components/tasking/naval/README.md)

典型问题：

- `MissionCommand`、`PilotAction`、`TaskOrder`、`LeaderIntent` 的字段定义在哪里。
- 哪些字段属于 `common`，哪些属于 `air` / `naval`。

### `src/systems/`

职责：

- Flecs system registration。
- 每 tick 的 ECS mutation 逻辑。
- 物理、战斗、平台系统、视觉更新。

边界入口：

- [src/systems/README.md](../../src/systems/README.md)
- [src/systems/core/README.md](../../src/systems/core/README.md)
- [src/systems/physics/README.md](../../src/systems/physics/README.md)
- [src/systems/combat/README.md](../../src/systems/combat/README.md)
- [src/systems/systems/README.md](../../src/systems/systems/README.md)
- [src/systems/visual/README.md](../../src/systems/visual/README.md)

典型问题：

- 命令怎样进入 runtime 并在每帧生效。
- 空气动力、控制、仪表、导航、传感器、数据链怎样推进。

### `src/models/`

职责：

- 可替换的领域模型默认实现。
- control / sensor / guidance / effects / unit factory。

边界入口：

- [src/models/README.md](../../src/models/README.md)
- [src/models/core/README.md](../../src/models/core/README.md)
- [src/models/air/README.md](../../src/models/air/README.md)
- [src/models/environment/README.md](../../src/models/environment/README.md)
- [src/models/systems/README.md](../../src/models/systems/README.md)
- [src/models/weapons/README.md](../../src/models/weapons/README.md)

典型问题：

- 默认控制律、传感器、制导、武器效果模型在哪里。
- 某类行为是“系统逻辑”还是“可替换模型实现”。

### `src/content/`

职责：

- 内容 schema、unit definition、内容加载器。
- 描述“有哪些静态内容”，而不是拥有 runtime 行为。

边界入口：

- [src/content/README.md](../../src/content/README.md)

### `src/core/`

职责：

- 单 world kernel。
- batch runtime。
- mission runtime。
- episode controller。
- geometry query。

边界入口：

- [src/core/README.md](../../src/core/README.md)
- [src/core/engine/README.md](../../src/core/engine/README.md)
- [src/core/geometry/README.md](../../src/core/geometry/README.md)
- [src/core/mission/README.md](../../src/core/mission/README.md)
- [src/core/mission/runtime/README.md](../../src/core/mission/runtime/README.md)
- [src/core/mission/episode/README.md](../../src/core/mission/episode/README.md)
- [src/core/mission/episode/detail/README.md](../../src/core/mission/episode/detail/README.md)
- [src/core/interfaces/README.md](../../src/core/interfaces/README.md)

典型问题：

- `SimulationKernel` 和 `WorldBatchRuntime` 的 owner 在哪里。
- reward / objective / termination / episode transition 在哪里计算。

### `src/runtime/`

职责：

- 维护中的 C++ 应用层 contract。
- facade request / result。
- 面向 Python 和未来前端的 typed runtime API。

边界入口：

- [src/runtime/README.md](../../src/runtime/README.md)
- [src/runtime/contracts/README.md](../../src/runtime/contracts/README.md)
- [src/runtime/facade/README.md](../../src/runtime/facade/README.md)

典型问题：

- 外部长期依赖的 C++ runtime surface 应该是什么。
- 为什么不应直接抓 `SimulationKernel` 作为上层 API。

### `src/interfaces/`

职责：

- 语言绑定和外部接口适配。
- 轻量类型转换与错误映射。

边界入口：

- [src/interfaces/README.md](../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../src/interfaces/python/README.md)

典型问题：

- 某个 C++ 类型如何暴露到 Python。
- 某段逻辑应属于 binding 还是应该下沉回 `runtime/facade` / `core`。

### `src/gpu/`

职责：

- GPU helper。
- packet runtime。
- 显式实验探针。

边界入口：

- [src/gpu/README.md](../../src/gpu/README.md)
- [src/gpu/experimental/README.md](../../src/gpu/experimental/README.md)

典型问题：

- 哪些 GPU 路径已经进入维护面。
- 哪些仍是 parity probe 或实验路径。

### `src/tools/`

职责：

- 开发期工具和实验工具。
- 允许调用 runtime API 做探测，但不构成维护中的主线 contract。

边界入口：

- [src/tools/README.md](../../src/tools/README.md)
- [src/tools/experimental/README.md](../../src/tools/experimental/README.md)
- [src/tools/experimental/gpu_phase0/README.md](../../src/tools/experimental/gpu_phase0/README.md)

## 4. `python/` 层

`python/` 不是杂项脚本目录，而是 C++ runtime 上方的 Python 支撑层。

优先阅读：

- [python/README.md](../../python/README.md)
- [python/training/README.md](../../python/training/README.md)

当前主线子域：

- `scenario/`
  - 场景编译和运行时主实现。
- `rl/`
  - Python RL 主线，包含 runtime、tasking、policy algo、planning、profile、support。
- `training/`
  - `train.py` 主线入口复用的 bootstrap、CLI 和运行时支撑。
- `testing/`
  - contract runner 与测试运行时支撑。
- `world_model/`
  - world model / offline dataset 支撑。
- `models/`
  - Python 侧训练模型辅助。

典型问题：

- 为什么某个训练入口走到 world-batch runtime。
- leader/tasking/HMoE 的 Python glue 在哪里。
- contract runner、artifact 路径和训练 bootstrap 为什么这样组织。

实现入口：

- [python/scenario_compiler.py](../../python/scenario_compiler.py)
  - 兼容 shim，主实现已下沉到 `python/scenario/compiler/`。
- [python/scenario_runtime.py](../../python/scenario_runtime.py)
  - 兼容 shim，主实现已下沉到 `python/scenario/runtime/`。
- [python/testing/scenario_contract_runner.py](../../python/testing/scenario_contract_runner.py)
  - 兼容 shim，主实现已下沉到 `python/testing/contracts/`。

## 5. `gym_envs/` 层

`gym_envs/` 是环境封装层，负责把 C++ runtime、mission state 和训练接口接起来。

优先阅读：

- [gym_envs/README.md](../../gym_envs/README.md)

主入口：

- [gym_envs/universal_env.py](../../gym_envs/universal_env.py)
  - 执行层 / 单机主环境。
- [gym_envs/leader_env.py](../../gym_envs/leader_env.py)
  - 长机层环境。

关键子域：

- `scenario_loader/`
  - 场景运行时 glue、mission observation、execution / navigation / reward / preparation / spatial runtime。
- `leader_env_parts/`
  - 长机环境拆分后的 decision / execution glue。

典型问题：

- 为什么某个 env step 落到某个 reward / transition 分支。
- 长机环境与执行环境的职责如何分开。

## 6. `tests/` 层

`tests/` 已经在向“reusable runners + JSON contracts”收敛。

优先阅读：

- [tests/README.md](../../tests/README.md)

当前主线测试域：

- `architecture/`
  - 分层守卫和 target readiness。
- `runtime/`
  - mission / runtime / loader / facade 回归。
- `world_batch/`
  - batch kernel 与 vec-env 适配。
- `leader/`
  - leader / tasking / common-core / naval 语义。
- `scenario/`
  - scenario compiler 与 spatial-query 测试。
- `training/`
  - train entry 和 callback 回归。
- `contracts/`
  - JSON contract 规格。
- `diagnostics/`
  - 仍偏探索性，不应替代稳定 regression。

这里也是“边界是否只是写在文档里，还是已经被守住”的主要证据面。比如架构分层、runtime facade 收口和部分 contract 边界，已经通过自动测试在维持。

## 7. `tools/` 层

`tools/` 是 operator-facing 工具和 runner 面，不是核心 runtime API。

优先阅读：

- [tools/README.md](../../tools/README.md)
- [tools/diagnostics/README.md](../../tools/diagnostics/README.md)
- [tools/maintenance/README.md](../../tools/maintenance/README.md)

当前主线分工：

- `tools/eval/`
  - 维护中的评估入口。
- `tools/diagnostics/`
  - benchmark / probe / replay / operator-facing diagnostics。
- `tools/runners/`
  - contract 和批量 runner。
- `tools/maintenance/`
  - 环境、workspace、维护脚本。

## 8. 边界方案文档

如果你要看“为什么这样分层”，而不是只看目录 README，优先读：

1. [docs/plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md](../plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md)
2. [docs/plan/architecture/architecture_and_performance_research_followup.zh.md](../plan/architecture/architecture_and_performance_research_followup.zh.md)
3. [docs/plan/architecture/system_layering_and_engine_encapsulation_plan.md](../plan/architecture/system_layering_and_engine_encapsulation_plan.md)
4. [docs/plan/architecture/src_layered_refactor_freeze.zh.md](../plan/architecture/src_layered_refactor_freeze.zh.md)

这些文档回答的是：

- 为什么要有 `runtime/facade`。
- 为什么 `interfaces/python` 不能继续拥有领域逻辑。
- 为什么 `core`、`systems`、`models`、`components` 要保持当前方向的依赖。
- 哪些分层已经冻结成当前主线，哪些仍是后续收口工作。

## 9. 问题定位建议

如果你遇到的是：

- “字段定义在哪”
  - 从 `src/components/` 开始。
- “每 tick 行为为什么这样变化”
  - 从 `src/systems/` 和 `src/models/` 开始。
- “mission / reward / termination 为什么这样算”
  - 从 `src/core/mission/` 开始。
- “为什么 Python 拿到这个观测、奖励或 phase transition”
  - 从 `gym_envs/scenario_loader/` 开始。
- “leader / tasking 为什么发出这个命令”
  - 从 `python/rl/tasking/` 和 `gym_envs/leader_env_parts/` 开始。
- “binding surface 为什么不一致”
  - 从 `src/interfaces/python/` 和 `tests/runtime/` 开始。
- “facade contract 为什么这样设计”
  - 从 `src/runtime/` 和 `docs/plan/runtime_facade/` 开始。
- “批量 rollout / world-batch 为什么慢”
  - 从 `src/core/engine/`、`python/rl/runtime/`、`tools/diagnostics/` 开始。

## 10. 推荐阅读顺序

第一次进仓库，建议按这个顺序读：

1. [README.md](../../README.md)
2. [docs/README.md](../README.md)
3. [src/README.md](../../src/README.md)
4. [src/core/README.md](../../src/core/README.md)
5. [src/runtime/README.md](../../src/runtime/README.md)
6. [src/interfaces/python/README.md](../../src/interfaces/python/README.md)
7. [python/README.md](../../python/README.md)
8. [gym_envs/README.md](../../gym_envs/README.md)
9. [tests/README.md](../../tests/README.md)
10. [tools/README.md](../../tools/README.md)

如果主要做架构/边界工作，再继续读：

1. [docs/plan/architecture/README.md](../plan/architecture/README.md)
2. [docs/plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md](../plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md)
3. [src/runtime/facade/README.md](../../src/runtime/facade/README.md)
4. [src/core/mission/README.md](../../src/core/mission/README.md)
5. [tests/architecture/test_runtime_facade_layering.py](../../tests/architecture/test_runtime_facade_layering.py)

## 11. 维护说明

这份地图只覆盖当前维护主线。它不承诺：

- 所有历史任务文档都已经同步到当前路径。
- 所有 `docs/task/` 下的实施包都仍可直接当作操作入口。
- `Archive/` 中的旧设计仍与今天的目录组织完全一致。

如果后续发现某份活动 README 已经迁移、改名或职责变化，优先更新对应目录 README，再回到本地图补导航。
