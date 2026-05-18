# Runtime Facade 接口契约方案

文档导航：

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_task_bootstrap_plan.zh.md](../archive/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](../archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)

状态：`2026-05-10` 接口契约草案。  
文档定位：

- 本文档回答“维护中的前端应该依赖什么 facade 边界，以及核心 request/response/handle 应如何定义”。
- 本文档是 runtime facade 的接口设计依据，但不是自动生效的冻结执行单。
- 任何从本方案导出的实施工作，都必须通过单独冻结的执行计划收口范围。

本文档定义维护中的 `runtime facade` 契约方向，用于把前端与底层
`WorldBatchRuntime` / `SimulationKernel` / `ExecutionEpisodeController`
隔离开。

相关文档：

- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [cpp_exact_runtime_refactor_plan.md](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](../archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)

## 一、文档目的

这份文档回答五个问题：

1. `runtime facade` 到底要解决什么问题。
2. 它和 `WorldBatchRuntime`、`SimulationKernel` 的关系是什么。
3. 维护中的前端应该通过什么接口与后端交互。
4. 这个契约如何为未来的 C++ 下沉、CUDA、resident-state、远程服务化留接口。
5. 第一批实施应先落哪些接口，哪些暂时不进入主线。

## 二、为什么现在必须引入 Runtime Facade

当前仓库已经有很强的编译侧运行时能力，但还缺少一个稳定的上层契约。

现状问题是：

1. Python 前端仍直接依赖很多底层 runtime 行为。
2. `python_module.cpp` 直接暴露了大量低层 API，导致前端容易绕过边界。
3. `WorldBatchVecEnv` 仍自己拼装很多 request / state mirror / step consume 逻辑。
4. 后续若继续推进 C++ ownership、CUDA device-resident path、或者服务化 runtime，这些前端将继续承受不稳定接口。

因此现在需要一个明确目标：

`前端不再依赖底层 runtime 的细碎能力，而是依赖一组维护中的、面向用例的稳定 facade 接口。`

## 三、Facade 的角色定位

### 1. Facade 不是新引擎

`runtime facade` 不是替代 simulation engine 的新引擎。
它的定位是：

- 面向前端暴露稳定契约
- 隐藏底层 engine 组合细节
- 聚合底层多个 runtime 能力点
- 为未来切换 backend 或部署形态提供稳定上边界

也就是说：

- `SimulationKernel` 仍负责精确 world 语义
- `WorldBatchRuntime` 仍负责批量运行时和 world owner
- `ExecutionEpisodeController` 仍负责 compiled episode ownership
- `runtime facade` 负责把这些能力整理成前端可依赖的 API 集

### 2. Facade 的直接服务对象

第一阶段 facade 的直接服务对象应包括：

- `WorldBatchVecEnv`
- `UniversalEnv`
- 训练入口 `train.py`
- 诊断基准工具
- 未来的可视化或服务化前端

### 3. Facade 的核心约束

facade 必须同时满足：

1. 面向 batch，而不是只面向单 world。
2. 面向 typed request / response，而不是自由拼装字典。
3. 为 device-resident / DLPack 预留出口。
4. 支持渐进迁移，而不是一次性重写所有前端。

## 四、Facade 设计目标

### 目标 1：稳定用例边界

前端应通过这些高层用例与后端交互：

- world / batch 初始化
- scenario / layout 应用
- reset
- step
- observation 获取
- runtime state 导入导出
- diagnostics / trace 请求

而不是直接调用：

- 某个内核内部 set/get 组件方法
- 某个阶段性 probe helper
- 某个低层控制器内部函数

### 目标 2：屏蔽底层所有权变动

未来这些变化不应要求前端重写：

- `ScenarioLoader` 不再拥有权威 episode state
- `ExecutionEpisodeController` 变成主 ownership
- `WorldBatchRuntime` 增加 physics backend 选择
- `WorldBatchRuntime` 增加 resident-state mode
- observation 从 host copy 切换成 device view

### 目标 3：天然支持性能优化

facade 设计必须从一开始就考虑：

- batch request / response
- 减少 Python 多次往返
- device view 导出
- optional zero-copy data path
- minimal-sync / partial-sync contract

否则后面仍会在 facade 之上再长出新的性能旁路。

## 五、Facade 不应该做什么

`runtime facade` 不应承担：

- 物理计算
- mission 语义决策本体
- 前端策略逻辑
- 训练算法逻辑
- 低层 probe 细节暴露

它不是：

- `ScenarioLoader v2`
- `WorldBatchVecEnv` 的另一个名字
- `python_module.cpp` 的平移复制

## 六、目标接口分层

建议把 facade 契约拆成四组接口，而不是一个巨大类。

### A. Runtime Lifecycle Facade

负责：

- runtime 创建与销毁
- batch/world 容量配置
- 基础能力协商

建议职责：

- 创建 runtime session
- 配置 worker_threads
- 查询 backend 能力
- 查询 device 能力

### B. Scenario / World Setup Facade

负责：

- scenario 编译后内容应用
- world layout 应用
- batch reset
- seed / randomization 入口

建议职责：

- 加载数据库
- 加载 unit definitions
- 应用 world setup / layout
- reset batch

### C. Execution Step Facade

负责：

- execution 主线 reset / step
- request 打包
- compiled episode state priming
- observation / reward / done / info 结果返回

这是维护中的核心 facade。

### D. Diagnostics / Export Facade

负责：

- 诊断数据导出
- trace / state snapshot
- candidate queries
- experiment-only GPU or exact-state hooks

这组接口可以先保留为“二级稳定接口”，不要求与主线 rollout 契约一样严格冻结。

## 七、建议的核心契约对象

下面定义的是“facade 级对象”，不是底层内部结构的直接映射。

### 1. RuntimeCapabilities

用途：

- 让前端知道当前 runtime 具备哪些主线能力

建议字段：

- `supports_batch_runtime`
- `supports_compiled_episode_controller`
- `supports_compiled_execution_step`
- `supports_gpu_visual`
- `supports_gpu_observation`
- `supports_gpu_flight_shaping`
- `supports_device_observation_view`
- `supports_resident_state`
- `supports_exact_gpu_backend`
- `supports_shadow_compare`

说明：

- 这是 facade 能力协商对象
- 前端不应再自己通过 `hasattr(ef_py, ...)` 到处探测

### 2. RuntimeBatchConfig

用途：

- 定义 batch runtime 的长期配置，而不是每步都重复传

建议字段：

- `world_count`
- `worker_threads`
- `mission_obs_mode`
- `include_visual`
- `include_proprio`
- `observation_return_mode`
- `execution_step_runtime_mode`
- `flight_shaping_backend`
- `execution_episode_controller_mode`
- `policy_observation_bridge_enabled`

### 3. BatchWorldSetupRequest

用途：

- 初始化或 reset world 批次

建议字段：

- `seeds`
- `terrain_assignments`
- `wind_assignments`
- `zone_definitions`
- `spawn_requests`
- `time_steps`
- `randomization_overrides`

### 4. BatchResetRequest

用途：

- 表达“重置哪些 world、用哪些 seed、是否重建 layout”

建议字段：

- `target_world_indices`
- `seed_base` 或 `seeds`
- `rebuild_layout`
- `randomization_overrides`

### 5. ExecutionBatchStepRequest

用途：

- 表达主线 step 调用的所有高层输入

建议字段：

- `pilot_action_assignments`
- `mission_command_assignments`
- `task_order_assignments`
- `leader_intent_assignments`
- `pilot_report_assignments`
- `step_mode`
- `observation_request`
- `timing_enabled`

注意：

- 第一阶段不要求这里承载所有低层调试开关
- 要优先服务维护中的 rollout 主路径

### 6. ExecutionBatchStepResult

用途：

- 作为维护中 `step()` 的统一输出对象

建议字段：

- `observations`
- `rewards`
- `terminated`
- `truncated`
- `infos`
- `runtime_timing`
- `controller_state_changed_flags`
- `status_vectors`

### 7. RuntimeStateSnapshot

用途：

- 统一表达可导入导出的运行时状态

建议字段：

- `execution_episode_states`
- `mission_commands`
- `task_orders`
- `leader_intents`
- `pilot_reports`
- `truth_observations`
- `instrument_states`

第一阶段建议只冻结：

- `ExecutionEpisodeState` 作为稳定主对象

其他内容可按用途逐步加入。

### 8. ObservationBatchPacket

用途：

- 统一表达面向前端的观测包

建议字段：

- `host_observation_dict`
- `device_observation_view`
- `layout_metadata`
- `terminal_observation_mask`

说明：

- 它不是单纯的 numpy dict
- 它也不是直接暴露底层 GPU tensor
- 它是 facade 层的统一观测包

## 八、建议的主接口集合

下面给出第一阶段建议冻结的 facade 级接口。

### 1. `create_runtime_session(config) -> RuntimeSessionHandle`

用途：

- 创建一个维护中的 runtime session

对应当前底层：

- `WorldBatchRuntime(world_count)`
- 基础参数与 capability 初始化

### 2. `get_runtime_capabilities(session) -> RuntimeCapabilities`

用途：

- 获取当前 session 对外可用能力

优点：

- 替代前端散落的 `hasattr` 探测逻辑

### 3. `apply_batch_world_setup(session, request) -> BatchWorldSetupResult`

用途：

- 批量应用 world setup / layout

对应当前底层：

- `apply_world_setup_batch(...)`

### 4. `reset_execution_batch(session, request) -> ExecutionBatchResetResult`

用途：

- 维护中的 execution reset 入口

它应内部负责：

- reset worlds
- prime execution episode state
- build 初始 observation packet

前端不应再自己拼：

- reset -> read truth -> read inst -> sync command chain -> build obs

### 5. `step_execution_batch(session, request) -> ExecutionBatchStepResult`

用途：

- 维护中的主线 step API

它应内部负责：

- apply actions / commands
- step worlds
- compiled episode mainline 或 legacy fallback
- observation / reward / termination / info 汇总

前端不应再自己拼接这些阶段。

### 6. `export_runtime_state(session, request) -> RuntimeStateSnapshot`

用途：

- 导出当前维护态 runtime state

第一阶段主要服务：

- shadow compare
- debug
- resumable rollout

### 7. `import_runtime_state(session, request) -> ImportResult`

用途：

- 导入 runtime state

第一阶段主要服务：

- controller priming
- exact state roundtrip test
- future resumable training / diagnostics

### 8. `get_observation_packet(session, request) -> ObservationBatchPacket`

用途：

- 单独拉取当前 observation 包

主要服务：

- reset 后读观测
- 某些 diagnostic 或 polling 场景

### 9. `run_diagnostics(session, request) -> DiagnosticsResult`

用途：

- 统一封装诊断入口

第一阶段不必把所有 probe 合并，但建议预留统一 facade 入口。

## 九、主线与实验线接口分级

建议把 facade 接口分成两级稳定度。

### 一级：维护中主线接口

必须稳定的接口：

- `create_runtime_session`
- `get_runtime_capabilities`
- `apply_batch_world_setup`
- `reset_execution_batch`
- `step_execution_batch`
- `export_runtime_state`
- `import_runtime_state`
- `get_observation_packet`

这些接口是未来 frontends 的主依赖对象。

### 二级：实验与诊断接口

可保留演进空间的接口：

- exact-state packed import/export
- exact GPU backend opt-in 入口
- candidate helper probes
- stage trace / parity compare
- resident-state experiment-only hooks

它们可以继续由底层 runtime 或 diagnostics facade 暴露，但不应污染主线 step 契约。

## 十、与现有 `WorldBatchRuntime` 的映射关系

现有 [world_batch_runtime.h](../../../src/core/engine/world_batch_runtime.h)
已经具备很多基础能力，适合作为 facade 的底座。

### 当前已经有的底座能力

- `reset_batch`
- `step_batch`
- `apply_world_setup_batch`
- `set_*_batch`
- `prime_execution_episode_controller_batch`
- `step_execution_episode_results_batch`
- `export_execution_episode_states_batch`
- `get_*_batch`
- GPU broadphase candidate helpers

### 当前还缺少的上层整合能力

缺的是 facade 应做的聚合与冻结，而不是缺底层 primitives：

1. reset / step 的高层 request / result 契约
2. capability 协商对象
3. observation packet 统一表达
4. host/device 双视图抽象
5. 主线与实验线的明确分级

因此：

- 不建议重写 `WorldBatchRuntime`
- 建议在其上构建 facade 层

## 十一、device-view 与 zero-copy 预留

facade 设计必须明确支持三种观测返回形态：

### 模式 A：host copy

最保守、兼容性最高。

### 模式 B：host view

用于单进程 world-batch 主线优化。

### 模式 C：device view

面向：

- DLPack
- torch direct consumer
- future device-resident rollout path

因此 facade 契约应允许：

- `observation_access_mode = copy | view | device_view`

而不是把这个概念散落在前端 wrapper 实现里。

## 十二、渐进迁移策略

### 阶段 1：只定义契约，不改动所有权

目标：

- 先定义 facade-level 类型和 API
- 内部仍可调用现有 `WorldBatchRuntime` 和 loader 辅助逻辑

成功标准：

- 新前端或重构中的前端可以开始依赖 facade 契约

### 阶段 2：把 `WorldBatchVecEnv` 切到 facade

目标：

- 保持行为不变
- 把当前 request build / step consume / observation fetch 改走 facade

成功标准：

- `WorldBatchVecEnv` 不再直接依赖过多低层 runtime 细节

### 阶段 3：把 `ScenarioLoader` 角色缩窄

目标：

- `ScenarioLoader` 不再是 runtime backend shell
- 只保留 scenario 适配与前端辅助角色

成功标准：

- compiled ownership 主线与 loader mirror 主线边界清晰

### 阶段 4：为 resident-state / exact backend 加入 facade-level backend switch

目标：

- 未来 backend 选择不影响前端契约

## 十三、第一批实施建议（设计分解，非执行冻结）

说明：本节用于拆解接口落地顺序。实际第一批执行范围以后续冻结文档
[runtime_facade_task_bootstrap_plan.zh.md](../archive/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md)
为准。

更新说明：第一批 `WP1-WP6` 已完成；下一批候选分层清理范围已收敛到
[runtime_facade_layering_cleanup_freeze.zh.md](../archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md)。

建议把实施拆成四个最小工作包。

### WP1：冻结 facade 契约对象

输出：

- facade 文档
- 类型草图
- 命名冻结

建议优先对象：

- `RuntimeCapabilities`
- `RuntimeBatchConfig`
- `BatchResetRequest`
- `ExecutionBatchStepRequest`
- `ExecutionBatchStepResult`
- `ObservationBatchPacket`

### WP2：增加 facade adapter 原型层

输出：

- 一个最小的 Python-facing facade 封装
- 先包住 `WorldBatchRuntime`

目标：

- 不改变行为
- 先改变依赖方向

### WP3：将 `WorldBatchVecEnv` 的 reset / step 路径接到 facade

输出：

- 前端开始依赖 facade，而不是直接拼 runtime plumbing

### WP4：为 device-view 和 capability 协商预留接口

输出：

- facade 中加入 capability 协商
- observation packet 中预留 device-view 字段

## 十四、当前不建议立即做的事

下面这些不建议和 facade 第一期一起做：

- 把所有 probe API 一次性并进 facade
- 把 exact GPU backend 一次性纳入主线 facade
- 在 facade 第一期强行做远程 RPC 版本
- 对前端一次性大规模改名或迁目录

先立契约，再逐步切流量，风险更低。

## 十五、最终建议

`runtime facade` 的第一阶段目标，不是“发明一套大而全的新运行时系统”，而是：

1. 冻结维护中的前端应该依赖的上边界。
2. 把底层 runtime 细碎能力包成稳定用例 API。
3. 为 future C++ ownership、CUDA resident-state、device view、服务化部署留出统一接口。

因此最合适的实施策略是：

- 先文档冻结
- 再做最小 facade 原型
- 再把 `WorldBatchVecEnv` 接上
- 然后才继续推动更深的 backend ownership 重构

这样，前端与后端的真正解耦才会开始发生，而不是继续停留在概念层。
