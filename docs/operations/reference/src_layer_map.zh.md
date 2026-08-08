# 代码层地图

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/operations/reference/src_layer_map.md`
Owner: `operations/code-navigation`
Last verified: `2026-08-08`
本文档回答三个问题：

1. 当前主线代码从 C++ 运行时到 Python 训练入口是怎样串起来的。
2. 各个子系统的职责边界写在哪些 README / 方案文档里。
3. 出问题时应该先看哪个目录，而不是在整个仓库里盲搜。

如果历史任务记录、旧计划或归档文档与这里冲突，优先相信当前代码和 owner-local
架构入口。

## 1. 当前主线总览

当前 C++ surface 已经是多域口径，但成熟度并不均匀。air/execution 是最深的维护中路径。
naval 已有平台组件、command/tasking owner slice、舰艇/潜艇/舰载航空 token runtime、
weapon-release hook 和 engagement evidence export，但还不是完整 naval mission runtime。
ground 仍是 bootstrap/evidence-only：`UnitType::Ground` 与 typed platform capability
evidence 已存在，land movement、sensing、terrain ownership、fires、damage 和 full ground
runtime 仍 held。

当前维护中的依赖方向应理解为：

```text
interfaces/python
  -> runtime/facade
    -> core/engine + core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime-visible packets
  -> 不拥有规范的 CPU 真值路径
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
  - 项目总入口，说明主线能力、常用命令和仓库级边界。
- [src/README.md](../../../src/README.md)
  - `src/` 的分层边界和依赖方向。
- [Architecture owner](../../architecture/README.zh.md)
  - 当前架构 standards、reference、reviews 与开放 issues。

## 2. 哪些文档是“当前权威入口”

如果你要判断某个子系统的职责边界是否已经文档化，优先看这些层级：

- `src/` 下各目录 README
  - 这是当前最直接、最接近代码的边界说明。
- `docs/architecture/standards/`
  - 这是回答“为什么这样分层、runtime contract 为什么这样定义”的维护规范层。
- `tests/README.md`
  - 这是回答“哪些约束已经进入自动验证”的入口。
- `python/README.md`、`gym_envs/README.md`、`tools/README.md`
  - 这是 Python 运行时、环境封装和工具面的职责入口。

不应默认当作当前权威的文档：

- `docs/Archive/`
  - 保留历史讨论和旧方案，不作为当前实现的默认依据。
- `docs/temp/`
  - 草稿和临时分析，不作为维护主线依据。
- 具体任务记录中的实施包、进展报告、checkpoint
  - 可用于追溯背景，但不应替代对应目录下 README 的边界说明。

## 3. `src/` 层

`src/` 是 C++ 运行时主线。它已经有比较完整的分层边界说明，是当前判断“子系统职责是否有详细文档”的最强证据。

优先阅读：

- [src/README.md](../../../src/README.md)
- [src/core/README.md](../../../src/core/README.md)
- [src/runtime/README.md](../../../src/runtime/README.md)
- [src/interfaces/README.md](../../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)

### `src/components/`

职责：

- ECS 组件。
- command / tasking DTO。
- naval platform state component。
- 可绑定、可持久化的轻量值类型。

边界入口：

- [src/components/README.md](../../../src/components/README.md)
- [src/components/domains/air/platform/README.md](../../../src/components/domains/air/platform/README.md)
- [src/components/command/README.md](../../../src/components/command/README.md)
- [src/components/command/common/README.md](../../../src/components/command/common/README.md)
- [src/components/domains/air/command/README.md](../../../src/components/domains/air/command/README.md)
- [src/components/domains/naval/command/README.md](../../../src/components/domains/naval/command/README.md)
- [src/components/domains/naval/platform/README.md](../../../src/components/domains/naval/platform/README.md)
- [src/components/tasking/README.md](../../../src/components/tasking/README.md)
- [src/components/tasking/common/README.md](../../../src/components/tasking/common/README.md)
- [src/components/domains/air/tasking/README.md](../../../src/components/domains/air/tasking/README.md)
- [src/components/domains/naval/tasking/README.md](../../../src/components/domains/naval/tasking/README.md)

典型问题：

- `MissionCommand`、`PilotAction`、`TaskOrder`、`LeaderIntent` 的字段定义在哪里。
- 哪些字段属于 `common`，哪些属于 `air` / `naval`。
- ship、submarine 和 embarked-air operation state 存在哪里。

### `src/systems/`

职责：

- Flecs 系统注册。
- 每个 tick 的 ECS 变更逻辑。
- 物理、战斗、平台系统和可视化更新。
- 受限的 naval ship/submarine/embarked-air token runtime 与 naval weapon-release hook。

边界入口：

- [src/systems/README.md](../../../src/systems/README.md)
- [src/systems/core/README.md](../../../src/systems/core/README.md)
- [src/systems/domains/air/README.md](../../../src/systems/domains/air/README.md)
- [src/systems/physics/README.md](../../../src/systems/physics/README.md)
- [src/systems/combat/README.md](../../../src/systems/combat/README.md)
- [src/systems/systems/README.md](../../../src/systems/systems/README.md)
- [src/systems/domains/naval/README.md](../../../src/systems/domains/naval/README.md)
- [src/systems/visual/README.md](../../../src/systems/visual/README.md)

典型问题：

- 命令怎样进入运行时并在每帧生效。
- 空气动力、控制、仪表、导航、传感器、数据链怎样推进。
- naval motion 与 token-level embarked-air 行为在哪里推进。

### `src/models/`

职责：

- 可替换领域模型的默认实现。
- control / sensor / guidance / effects / unit factory。
- naval weapon-mount helper 与 typed platform capability evidence。

边界入口：

- [src/models/README.md](../../../src/models/README.md)
- [src/models/core/README.md](../../../src/models/core/README.md)
- [src/models/domains/air/README.md](../../../src/models/domains/air/README.md)
- [src/models/environment/README.md](../../../src/models/environment/README.md)
- [src/models/systems/README.md](../../../src/models/systems/README.md)
- [src/models/weapons/README.md](../../../src/models/weapons/README.md)

典型问题：

- 默认控制律、传感器、制导和武器效果模型在哪里。
- 某类行为究竟属于“系统逻辑”还是“可替换模型实现”。
- ground 相关数据只是 capability evidence，还是实际 runtime model。

### `src/content/`

职责：

- 内容 schema、单位定义和内容加载器。
- 描述“有哪些静态内容”，包括 naval platform definition 与 ground-aware setup metadata，
  而不是拥有运行时行为。

边界入口：

- [src/content/README.md](../../../src/content/README.md)

### `src/core/`

职责：

- 单世界内核。
- 批量运行时。
- mission 运行时。
- episode 控制器。
- 几何查询。
- engine-level 的维护中 command/tasking contract transport 与 typed platform setup。

边界入口：

- [src/core/README.md](../../../src/core/README.md)
- [src/core/engine/README.md](../../../src/core/engine/README.md)
- [src/core/geometry/README.md](../../../src/core/geometry/README.md)
- [src/core/mission/README.md](../../../src/core/mission/README.md)
- [src/core/mission/runtime/README.md](../../../src/core/mission/runtime/README.md)
- [src/core/mission/episode/README.md](../../../src/core/mission/episode/README.md)
- [src/core/mission/episode/detail/README.md](../../../src/core/mission/episode/detail/README.md)
- [src/core/interfaces/README.md](../../../src/core/interfaces/README.md)

典型问题：

- `SimulationKernel` 和 `WorldBatchRuntime` 的归属在哪里。
- reward / objective / termination / episode transition 在哪里计算。
- 哪些 naval seam 是 engine/runtime transport 或 evidence export，而不是 mission orchestration。

### `src/runtime/`

职责：

- 维护中的 C++ 应用层契约。
- facade request / result。
- 面向 Python 和未来前端的类型化运行时 API。
- tasking、observation、engagement、diagnostics 和 typed platform setup contract。

边界入口：

- [src/runtime/README.md](../../../src/runtime/README.md)
- [src/runtime/contracts/README.md](../../../src/runtime/contracts/README.md)
- [src/runtime/facade/README.md](../../../src/runtime/facade/README.md)

典型问题：

- 外部长期开依赖的 C++ 运行时表面应该是什么。
- 为什么不应直接抓取 `SimulationKernel` 作为上层 API。
- 哪些 facade packet 是 evidence/export surface，而不是 domain owner。

### `src/interfaces/`

职责：

- 语言绑定和外部接口适配。
- 轻量类型转换与错误映射。

边界入口：

- [src/interfaces/README.md](../../../src/interfaces/README.md)
- [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)

典型问题：

- 某个 C++ 类型如何暴露到 Python。
- 某段逻辑应属于绑定层，还是应下沉回 `runtime/facade` / `core`。

### `src/gpu/`

职责：

- GPU 辅助设施。
- 数据包运行时支持。
- 显式实验探针。

边界入口：

- [src/gpu/README.md](../../../src/gpu/README.md)
- [src/gpu/experimental/README.md](../../../src/gpu/experimental/README.md)

典型问题：

- 哪些 GPU 路径已经进入维护面。
- 哪些仍是对齐探针或实验路径。

### `src/tools/`

职责：

- 开发期工具和实验工具。
- 可以调用运行时 API 做探测，但不构成维护中的主线契约。

边界入口：

- [src/tools/README.md](../../../src/tools/README.md)
- [src/tools/experimental/README.md](../../../src/tools/experimental/README.md)
- [src/tools/experimental/gpu_phase0/README.md](../../../src/tools/experimental/gpu_phase0/README.md)

## 4. `python/` 层

`python/` 不是杂项脚本目录，而是位于 C++ 运行时之上的 Python 支撑层。

优先阅读：

- [python/README.md](../../../python/README.md)
- [python/training/README.md](../../../python/training/README.md)

当前主线子域：

- `scenario/`
  - 场景编译和运行时的主实现。
- `rl/`
  - Python 强化学习主线，包含 runtime、tasking、policy algo、planning、profile、support。
- `training/`
  - `train.py` 主线入口复用的 bootstrap、CLI 和运行时支撑。
- `testing/`
  - 契约运行器与测试运行时支撑。
- `world_model/`
  - world model / offline dataset 支撑。
- `models/`
  - Python 侧训练模型辅助。

典型问题：

- 为什么某个训练入口会走到 world-batch 运行时。
- leader / tasking / HMoE 的 Python 胶水代码在哪里。
- contract runner、artifact 路径和训练 bootstrap 为什么这样组织。

实现入口：

- [python/scenario_compiler.py](../../../python/scenario_compiler.py)
  - 兼容性 shim，主实现已下沉到 `python/scenario/compiler/`。
- [python/scenario/runtime/](../../../python/scenario/runtime)
  - 当前 scenario-runtime 主实现。旧的 `python/scenario_runtime.py` shim 在当前
    checkout 中不存在。
- [python/testing/contracts/](../../../python/testing/contracts/)
  - 兼容性 shim，主实现已下沉到 `python/testing/contracts/`。

## 5. `gym_envs/` 层

`gym_envs/` 是环境封装层，负责把 C++ 运行时、mission 状态和训练接口接起来。

优先阅读：

- [gym_envs/README.md](../../../gym_envs/README.md)

主入口：

- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)
  - 执行层 / 单进程主环境。
- [gym_envs/leader_env.py](../../../gym_envs/leader_env.py)
  - 长机层环境。

关键子域：

- `scenario_loader/`
  - 场景运行时胶水、mission observation，以及 execution / navigation / reward / preparation / spatial runtime 等部分。
- `leader_env_parts/`
  - 从长机环境中拆出的决策 / 执行胶水。

典型问题：

- 为什么某个环境 step 会落到某个 reward 或 transition 分支。
- 长机环境与执行环境的职责如何分开。

## 6. `tests/` 层

`tests/` 已经在向“可复用运行器 + JSON 契约”收敛。

优先阅读：

- [tests/README.md](../../../tests/README.md)

当前主线测试域：

- `architecture/`
  - 分层守卫和 target readiness。
- `runtime/`
  - mission / runtime / loader / facade 回归。
- `world_batch/`
  - 批量内核与 vec-env 适配。
- `leader/`
  - leader / tasking / common-core / naval 语义。
- `scenario/`
  - scenario compiler 与 spatial-query 测试。
- `training/`
  - train entry 和 callback 回归。
- `contracts/`
  - JSON 契约规格。
- `diagnostics/`
  - 仍偏探索性，不应替代稳定回归。

维护中的 smoke 入口：

- `tests/smoke/ci_smoke_suite.json`
  - 仓库级 smoke manifest，供 CI 与顶层文档共同引用。
- `tools/runners/run_pytest_suite.py`
  - 先校验 suite 路径、再调用 pytest 的维护入口。

这里也是判断“边界只是写在文档里，还是已经被守住”的主要证据面。比如架构分层、runtime facade 收口和部分契约边界，已经通过自动测试在维持。

## 7. `tools/` 层

`tools/` 是面向操作人员的工具和运行器层，不是核心运行时 API。

优先阅读：

- [tools/README.md](../../../tools/README.md)
- [tools/diagnostics/README.md](../../../tools/diagnostics/README.md)
- [tools/maintenance/README.md](../../../tools/maintenance/README.md)

当前主线分工：

- `tools/eval/`
  - 维护中的评估入口。
- `tools/diagnostics/`
  - benchmark / probe / replay / 面向操作人员的诊断工具。
- `tools/runners/`
  - 契约运行器和批量运行器。
- `tools/maintenance/`
  - 环境、工作区和维护脚本。

## 8. 边界方案文档

如果你要看“为什么这样分层”，而不是只看目录 README，优先读：

1. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
2. [docs/architecture/work/issues/architecture_and_performance_research_followup.zh.md](../../architecture/work/issues/architecture_and_performance_research_followup.zh.md)
3. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.md)
4. docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md (`git show 3dc34673:docs/plan/archive/architecture/src_layered_refactor_freeze.zh.md`)

这些文档回答的是：

- 为什么要有 `runtime/facade`。
- 为什么 `interfaces/python` 不能继续拥有领域逻辑。
- 为什么 `core`、`systems`、`models`、`components` 要保持当前方向的依赖。
- 哪些分层已经冻结成当前主线，哪些仍是后续收口工作。

## 9. 问题定位建议

如果你遇到的是：

- “字段定义在哪”
  - 从 `src/components/` 开始。
- “每个 tick 的行为为什么这样变化”
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
  - 从 `src/runtime/` 和 [runtime facade issue](../../architecture/work/issues/runtime_facade_contract_plan.zh.md) 开始。
- “批量 rollout / world-batch 为什么慢”
  - 从 `src/core/engine/`、`python/rl/runtime/`、`tools/diagnostics/` 开始。

## 10. 推荐阅读顺序

第一次进仓库，建议按这个顺序读：

1. [README.md](../../README.md)
2. [docs/README.md](../README.md)
3. [src/README.md](../../../src/README.md)
4. [src/core/README.md](../../../src/core/README.md)
5. [src/runtime/README.md](../../../src/runtime/README.md)
6. [src/interfaces/python/README.md](../../../src/interfaces/python/README.md)
7. [python/README.md](../../../python/README.md)
8. [gym_envs/README.md](../../../gym_envs/README.md)
9. [tests/README.md](../../../tests/README.md)
10. [tools/README.md](../../../tools/README.md)

如果主要做架构 / 边界工作，再继续读：

1. [Architecture owner](../../architecture/README.zh.md)
2. [docs/architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md](../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
3. [src/runtime/facade/README.md](../../../src/runtime/facade/README.md)
4. [src/core/mission/README.md](../../../src/core/mission/README.md)
5. [tests/architecture/runtime_facade](../../../tests/architecture/runtime_facade)

## 11. 维护说明

这份地图只覆盖当前维护主线。它不承诺：

- 所有历史任务文档都已经同步到当前路径。
- 归档的 plan/task 包仍是当前操作入口。
- `Archive/` 中的旧设计仍与今天的目录组织完全一致。

如果后续发现某份活动 README 已经迁移、改名或职责变化，优先更新对应目录 README，再回到本地图补导航。
