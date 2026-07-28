# SCAL 一致性普查（2026-07-20）

语言：
- 英文规范版：[scal_conformance_census_20260720.md](scal_conformance_census_20260720.md)
- 中文伴随版：`scal_conformance_census_20260720.zh.md`

文档类型：`reference`
生命周期：`maintained`
规范路径：`docs/plan/unified_architecture_program/scal_conformance_census_20260720.md`
所有者：`unified architecture program workline`
最近核验：`2026-07-20`
基线提交：`779a821b`

状态：[统一架构计划](README.zh.md)的 T0 阶段一致性与信息状态普查。以下
发现是基线修订 (a)-(e) 的证据基础，已并入
[仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
的第 1.5、6.1/7.1 与 15-17 节。本文档是描述性的普查登记（`reference`
参考记录），不是独立评审：它只记录已核验基线状态下的发现，不含评审裁定。
T0 迭代的独立评审另行派发。

## 1. 违例登记表

针对修订后基线发现的阶段一致性与信息状态层违例。合规路径不列出，只登记
违例。

| 编号 | 类别 | 位置 | 违例 |
|------|------|------|------|
| V1 | Loader 阶段聚集 | `ScenarioLoader`（`loading.py` 的 load/finalize 链；`core.py` 的 `compute_full_step`） | 把 `P0`/`P1`/`P2`/`P3`/`P10` 聚集在同一个对象中，未声明 stage contract。 |
| V2 | Loader 阶段聚集 | `finalize_loaded_world` | 跨越 `P1`/`P2`/`P6`，且直接读取 `World Truth`，而不是通过 sensed/track 导出。 |
| V3 | Observation adapter 跨层消费 | `get_policy_agent_observation` / `get_policy_instrument_state` | 策略路径消费者直接读取 `World Truth`；未声明信息状态层。 |
| V4 | Observation adapter 跨层消费 | `mission_observation` 的 python-owned 模式：`naval_screen_station_v1`；`air_combat_c2_roe_v1`/`v2` | 平行生命周期叠加真值泄漏：naval 模式在 facade 导出之外读取 Track+Picture+Agency；air 模式读取 Track+Picture+Agency，且 `truth.contacts` 来自 truth 层。 |
| V5 | Reward 真值泄漏 | `reward_runtime/air_combat.py` | 直接读取 `WorldTruth` 的 `engagement`/`kill`/`missiles_remaining` 字段。 |
| V6 | Reward 真值泄漏 | `reward_runtime/naval.py` | 直接读取 `WorldTruth` 的 entity position。 |
| V7 | VecEnv 跨阶段捆绑 | `step_evaluation` | 把 `P9`+`P10`（effects/damage 与 observation export）捆绑在一起，没有阶段边界。 |
| V8 | VecEnv 跨阶段捆绑 | `WorldBatchVecEnv.step` | 在一次 step 调用内聚合 `P4`/`P5`/`P10`（control、physics、observation export）。 |
| V9 | Single-world 平行生命周期 | `single_world_batch_runtime` | 用第二套生命周期实现包装 batch runtime，而不是复用共享实现。 |

## 2. 跨界旁路盘点

维护面（`python/` 与 `gym_envs/`，不含测试与诊断面）上的直构路径，对照
Kernel Invariant G1（目标值为一，仅 facade）测算。已按基线 `779a821b`
以源码检索 `ef_py.SimulationKernel(` 与 `ef_py.WorldBatchRuntime(`
构造点复核。

| 事项 | 结论 |
|------|------|
| 维护面跨界路径数 | 1 — 即 facade 路径本身：`RuntimeFacadeAdapter` 构造 `ef_py.RuntimeFacade(world_count)`（`python/rl/runtime/world_batch/adapter.py`）。维护面上不存在任何额外的 `ef_py.SimulationKernel(` 或 `ef_py.WorldBatchRuntime(` 构造点，故在直构维度上 G1 目标（一，仅 facade）已在结构上达成。 |
| `UniversalEnv` 现状 | 已完成降级：`gym_envs/universal_env.py` 是 fail-fast 兼容壳，构造即抛出 "raw ef_py.SimulationKernel constructor path has been removed"；WP24 架构门禁 `test_wp24_universal_env_raw_kernel_constructor_path_is_removed` 钉住该移除。在本基线上它不是旁路路径。 |
| WP24 豁免清单条目 | 1 — `tests/runtime/engagement/test_facade_engagement_evidence_gates.py`（一处 `ef_py.WorldBatchRuntime(` 构造；`diagnostics_only` / `test_only`）。scoped escape-hatch 允许清单的 maintained 层级经门禁断言为空。 |
| 测试/诊断面直构路径 | 存在且已盘点（world-batch/runtime/GPU 测试套件、`python/testing/contracts/` 契约夹具、`tools/` 诊断与几何探针、`examples/viz` 演示服务器）；按定义不计入维护指标。 |
| 收敛缺口 | `ScenarioLoader` 的内核引用面：loader 仍持有一个未类型化的 runtime 句柄（`self.sim`），其 `loader.sim` 调用面较宽（tasking bridge、behavior runtime、loading、vec-env 支撑层），目前由 WP22 标记门禁逐点盘点，而非由声明式契约类型化。维护 batch 路径上该句柄是由 `RuntimeFacadeAdapter.make_scenario_loader` 构造的 facade 支撑 `_ScenarioLoaderRuntimeProxy`，不是 raw kernel；raw kernel 注入只存活于契约测试夹具。缺口在于给这个 loader 接缝定契约，而非 `UniversalEnv` 迁移。 |

## 3. G4 声明机制与首批消费者

G4（每个 observation/reward consumer 都必须声明自己的 information-state
layer）被提议拆分为三部分，风格对齐 `mission_obs_taxonomy` 的 `OWNER`
映射先例：

1. 模块级常量 —— `INFORMATION_LAYER_CONSUMED` / `INFORMATION_LAYER_PRODUCED`
   / `SEMANTIC_STAGE` frozenset 声明；零运行时开销。
2. 集中注册表 —— `python/architecture/information_layer_registry.py`
   风格的模块。
3. AST 门禁 —— 检查声明是否存在、是否与注册表一致，并禁止非 diagnostic
   消费者读取 `WorldTruth`，除非该路径是 facade 编译路径。

首批消费者（按优先级排序）：

| # | 消费者 | 优先级 | 登记条目 |
|---|--------|--------|----------|
| 1 | `mission_observation` python-owned 模式 | 最高 | V4 |
| 2 | `reward_runtime/air_combat.py` | 高 | V5 |
| 3 | `reward_runtime/naval.py` | 高 | V6 |
| 4 | `execution_runtime` / mainline | 中 | — |
| 5 | `step_evaluation` | 中 | V7 |
| 6 | `universal_env` 观测装配 | 中 | — |
| 7 | `world_batch` vec-env 观测批处理 | 低 | 已合规 |

## 4. 组合规则可强制化评估

程序 README 中命名的三条跨图组合规则（语义→因果下沉、因果→时序经由
read/write set、信息→机构经由 view spec）的可强制化情况。

| 规则 | 锚点 | 可立即门禁 | 暂缓 |
|------|------|------------|------|
| Semantic -> Causal | scenario compiler 的 `CompiledScenario` | 编译产物不可变性（frozen dataclass；AST 禁止 `P1` 之后的修改） | `scenario_data["task_order"]` 仍被 `finalize` 修改。 |
| Causal -> Temporal | `runtime_window_coordinator` 与 WP16 spine fixture 的 `read_set`/`write_set` 声明 | 校验 fixture 声明与 facade 调用图的一致性 | Python 侧 step 尚未声明 read/write set（受阻于 T2 基座）。 |
| Information -> Agency | `run_maintained_window` 的 `AgentRole` provenance 强制机制 | 把 provenance 标签检查扩展到非 window 路径 | `ObservationViewSpec` 尚不是运行时结构（将在 T8 具体化）。 |

本次普查得出的修订 (a)-(e) 已记录在
[仿真系统架构设计](../architecture/simulation_system_architecture_design.zh.md)
中。登记表刷新与迭代台账登记不在本文档范围内。
