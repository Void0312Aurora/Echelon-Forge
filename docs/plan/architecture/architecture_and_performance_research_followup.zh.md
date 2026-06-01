# 架构与性能路线进一步调研

文档导航：

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
- [runtime_facade_contract_plan.zh.md](../runtime_facade/runtime_facade_contract_plan.zh.md)
- [runtime_facade_task_bootstrap_plan.zh.md](../archive/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md)

状态：`2026-05-10` 调研论述草案。  
文档定位：

- 本文档回答“为什么这样分层、性能瓶颈在哪里、后续路线如何排序”。
- 本文档提供论据和取舍建议，但不是冻结执行计划。
- 本文档产出的建议应下沉为契约方案、专项计划或新的冻结任务单。

本文档是
[system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
的后续深化版本，重点回答以下问题：

1. 当前架构真实边界和文档描述之间是否一致。
2. 分层设计在未来扩展、性能和后端替换上应如何取舍。
3. 哪些慢路径应优先迁到 C++，哪些值得继续推进 CUDA，Rust 当前是否适合引入。
4. 在现有代码和已有实验基础上，下一阶段计划应如何排序。

## 结论摘要

基于当前代码、测试、性能文档和实验线索，可以先给出四个明确结论：

1. 当前项目的主要结构问题不是“缺少加速手段”，而是“架构边界和热路径所有权还不稳定”。
2. 下一阶段最稳妥、收益最高的主线仍然是：继续把 Python 热路径下沉到 C++，并在此基础上推进更稳定的 runtime facade 与 simulation/physics 分层。
3. CUDA 路线已经不是概念验证阶段，而是有真实资产、真实 benchmark 和真实瓶颈结论的既有方向，应该被纳入主计划，而不是单列成未来也许会做的旁支。
4. Rust 当前不应作为第一优先级引入。不是因为 Rust 不可行，而是因为仓库没有现成 Rust 资产，当前瓶颈更偏运行时边界、数据所有权和 GPU residency，而不是“C++ 无法表达”。

一句话总结：

`先稳固架构边界与 C++ 主线，再推进 CUDA；Rust 暂列观察项，不进入近期主实施线。`

## 一、当前架构现状调研

### 1. 代码体量和职责分布显示 Python 仍然过重

代表性文件与包体量如下：

- [gym_envs/scenario_loader/](../../../gym_envs/scenario_loader)：包内合计约 `9292` 行；[core.py](../../../gym_envs/scenario_loader/core.py) 约 `1220` 行。
- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)：约 `1885` 行。
- [python/rl/runtime/world_batch/](../../../python/rl/runtime/world_batch)：支撑包合计约 `2589` 行。
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)：约 `449` 行。
- [src/interfaces/python/](../../../src/interfaces/python)：拆分后的绑定文件合计约 `6682` 行；`python_module.cpp` 现在只是小型模块注册 wrapper。
- [src/core/engine/simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)：engine 拆分后约 `229` 行。
- [src/core/engine/world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)：约 `1255` 行。
- [src/core/mission/episode/execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp)：约 `347` 行。

这说明：

- Python 侧不是薄适配层，而是仍然承载了大量运行时逻辑。
- C++ 侧虽然已经很强，但还没有通过清晰门面和稳定目标构建边界，把这些能力变成一个真正可依赖的“后端平台”。

### 2. 当前文档和代码对“执行层”理解基本一致

旧架构文档虽然已经标注为 archived，但对真实代码热点的判断仍基本准确：

- [docs/Archive/architecture/layers/execution_layer.md](../../Archive/architecture/layers/execution_layer.md)
- [docs/Archive/architecture/layers/operation_physics_layer.md](../../Archive/architecture/layers/operation_physics_layer.md)

它们指出的结构风险今天仍然成立：

- `ScenarioLoader` 过重
- `MissionCommand` 解释逻辑跨 Python/C++ 分散
- operation / physics / runtime / frontend 交叉混杂

### 3. 当前分层的“名义边界”已经存在，但“执行边界”尚未真正形成

当前目录上已经有分层雏形：

- `src/core/engine`：world 和 kernel
- `src/core/mission`：mission/runtime
- `src/components/physics` 与 `src/systems/physics`：物理/控制部件
- `src/models/*`：默认模型实现
- `src/interfaces/python`：Python 绑定
- `python/rl` 与 `gym_envs`：训练和环境包装

但实际执行边界仍不够稳固，原因包括：

- Python 前端仍直接依赖很多低层 runtime 细节。
- `python_module.cpp` 暴露的是低层能力集合，不是高层 runtime facade。
- `ef_core` 仍是大单体，target 边界无法帮助约束 include 和 ownership。

## 二、性能与瓶颈调研

### 1. 当前最稳定的性能结论：Python 热路径仍然是主瓶颈之一

[cpp_exact_runtime_refactor_plan.md](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
已经明确指出：

- `ScenarioLoader` 仍拥有大量 episode state
- `compute_full_step(...)` 仍承担高频编排
- `WorldBatchVecEnv` 仍依赖 Python 侧 loader ownership 完成 step 语义

这不是“感觉上的慢”，而是当前主计划已经确认的结构性瓶颈。

### 2. 编译批处理 helper 已经能带来收益，但收益有限

从
[gpu_execution_runtime_research_and_design.md](../archive/exact_runtime/gpu_execution_runtime_research_and_design.md)
里已有测量看，C++ batch helper 对当前 CPU 主线是有收益的，但收益不是决定性的：

- `64 envs`
  - reset total：`164.33 ms -> 127.46 ms`
  - step total：`15.24 ms -> 14.72 ms`
  - 约 `1.04x` step wall-clock 提升
- `256 envs`
  - step total：`74.20 ms -> 67.27 ms`
  - 约 `1.10x` step wall-clock 提升

这说明：

- 仅仅把局部 observation packing / step preparation 编译化，收益是真实的，但不足以根治架构性瓶颈。
- 当前更大的瓶颈在跨层 ownership 和数据流，而不仅是单个 helper 算子的语言实现。

### 3. rollout 热路径瓶颈已经被进一步定位

[gpu_execution_phase4_rollout_hot_path_freeze.md](../exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md)
进一步确认了：

- learner 侧 device-resident minibatch 已经有收益
- `collect_rollouts()` 仍然不够理想
- 当前维护路径的下一个受限瓶颈是 host observation return contract

即便是去掉 `deepcopy(self.buf_obs)`，测得收益也只是：

- `n_envs=8` 时 `1.7%` 到 `4.2%`
- `n_envs=16` 时接近噪声

这再次说明：

- 单纯改 Python 容器复制策略不是主战场。
- 真正高价值的优化仍然是更深层的 ownership 下沉和更强的设备常驻路径。

### 4. exact GPU world-step 目前仍未成为主线候选

从
[gpu_exact_world_step_performance_and_parity_plan.md](../archive/exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md)
与
[gpu_exact_world_step_rearchitecture_plan.md](../archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md)
的内容看：

- 当前 exact GPU 原型在小 world_count 下仍显著慢于 CPU
- 还存在语义漂移
- 暖启动路径虽然明显缩短，但当前 runtime boundary 仍让它难以直接变成 maintained default

因此：

- exact GPU world-step 仍应视为中长期路线
- 它的前置条件仍然是更稳的 compiled episode ownership 和 backend contract

## 三、CUDA 路线现状判断

### 1. CUDA 不是未来设想，而是已经有真实资产

当前仓库中已有 GPU helper 代码：

- [src/gpu/gpu_execution_observation_runtime.cpp](../../../src/gpu/gpu_execution_observation_runtime.cpp)
- [src/gpu/gpu_flight_shaping_runtime.cpp](../../../src/gpu/gpu_flight_shaping_runtime.cpp)
- [src/gpu/gpu_interaction_broadphase_runtime.cpp](../../../src/gpu/gpu_interaction_broadphase_runtime.cpp)
- [src/gpu/gpu_visual_runtime.cpp](../../../src/gpu/gpu_visual_runtime.cpp)
- 对应 `.cu` 实现

还有 probe 工具：

- [src/tools/experimental/gpu_phase0](../../../src/tools/experimental/gpu_phase0)

并且构建脚手架已存在：

- [CMakeLists.txt](../../../CMakeLists.txt)

### 2. CUDA helper 的价值已经被 benchmark 证明

根据
[gpu_execution_runtime_research_and_design.md](../archive/exact_runtime/gpu_execution_runtime_research_and_design.md)
中的测量：

- object-only visual 在 device-resident 路径可达 `16x` 到 `100x+` 相对 CPU 的提升
- terrain-aware visual 也可达到 `2.8x` host-readback 提升，`15x+` 到 `50x+` device-resident 提升
- sensor / comm / broadphase 方向也已有明显 GPU 潜力

但文档同样清楚指出：

- host readback 是主要墙
- 只有 device-resident consumer 接起来，GPU helper 才真正进入“不同吞吐量级”

这意味着当前 CUDA 路线的真实判断应是：

- 值得继续
- 但必须与 runtime facade、device-resident output、episode ownership 重构联动
- 不能再以“单算子加速”思维孤立推进

### 3. 当前最成熟的 CUDA 应用方向

结合已有资产与测量结果，当前最成熟、最值得继续推进的 CUDA 方向依次是：

1. visual path
2. observation / bridge path
3. flight shaping path
4. broadphase candidate path
5. resident-state runtime path

而不是立即强推：

1. exact full world-step 全量替换
2. 把所有 physics stage 一步迁完

## 四、C++ 继续下沉的价值判断

### 1. 哪些 Python 慢路径最该继续迁到 C++

当前最应该继续迁到 C++ 的，不是所有 Python 代码，而是这些“高频、结构性、可验证”的路径：

1. `ScenarioLoader` 中的 episode state ownership、mirror、route/approach/post-transition 状态迁移
2. reward / termination / mission observation 的主编排路径
3. `WorldBatchVecEnv` 中 execution episode mainline / shadow compare 相关的 request build 与 state consume 逻辑
4. 更稳定的 facade-level batch request / batch response contract

这些路径的共同特征是：

- 每步都会走
- 逻辑复杂
- 当前跨 Python/C++ 交界频繁
- 能被现有测试和 shadow compare 验证

### 2. 哪些部分不值得急着“为了 C++ 而 C++”

下面这些不应因为“Python 慢”就立刻重写：

- 训练脚本层配置与 orchestration
- experiment 管理和 benchmark harness
- 各类低频工具脚本
- 仅在 reset / diagnostics 使用的外围逻辑

原则是：

- 热路径先下沉
- 契约先稳定
- 不为了语言统一牺牲迭代速度

## 五、Rust 路线判断

### 1. 当前仓库没有 Rust 资产

本次调研未发现：

- `Cargo.toml`
- `*.rs`
- Rust toolchain 配置

这意味着 Rust 不是“已有半成品，顺势扶正”的情况，而是“从零引入新语言和新工具链”的情况。

### 2. Rust 当前的潜在优点

如果从长期看，Rust 可能适合这些方向：

- 服务化 runtime facade
- 高可靠 DTO/serialization 层
- 独立 batch service 或外部 orchestrator
- 与 Python / C++ 之间做更清晰的 FFI 边界

### 3. Rust 当前不适合作为近期主线的原因

当前阶段不建议把 Rust 纳入近期待办主线，原因不是语言本身问题，而是时机问题：

1. 现有高性能资产几乎都在 C++/CUDA。
2. 当前最大瓶颈不是“C++ 写不动”，而是 runtime ownership 与 host/device data flow。
3. 引入 Rust 会增加：
   - 新工具链
   - 新 FFI 边界
   - 新构建复杂度
   - 新调试链路
4. 在 exact GPU、runtime facade、batch runtime 尚未稳定前，引入第三种系统语言会放大复杂度。

### 4. 对 Rust 的建议定位

Rust 当前建议作为：

- `观察项`
- `中远期候选`
- `面向服务化和外部 runtime API 的备选实现语言`

而不是：

- 当前执行层主重构语言
- 当前 physics / simulation backend 的第一替代语言

## 六、未来扩展视角下的分层设计建议

### 1. 分层必须同时考虑“可扩展性”和“性能”

仅从概念上分层还不够，下一版分层设计必须同时满足：

- 可以替换物理后端
- 可以替换仿真后端
- 可以支持多种 frontend
- 可以逐步引入 device-resident pipeline
- 可以支持更细的 batch 和 service 化

因此分层不应只是“目录整理”，而应面向以下未来能力：

1. exact CPU backend
2. exact GPU backend
3. reduced-fidelity backend
4. future external FDM bridge
5. local Python frontend
6. future remote/runtime service frontend

### 2. 最关键的新增分层要求

在已有
[system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
基础上，建议补充三个性能导向要求：

#### A. facade 层必须天然支持 batch 和 zero-copy

如果 facade 只抽象“功能”，但不抽象“数据所有权”和“批量协议”，未来还会重新卡在 host copies 上。

因此 facade contract 设计时就应考虑：

- batch request / response
- typed packet
- optional device view / DLPack export
- sync / async 兼容空间

#### B. physics backend contract 必须允许 resident state

如果 physics backend 仍默认每步都假定 CPU 侧是权威状态源，那么未来 exact GPU 路线还会继续受阻。

因此 physics backend contract 应明确支持：

- host-owned state
- backend-owned resident state
- partial sync
- observation-only sync

#### C. simulation engine contract 必须允许“compiled ownership, frontend mirroring”

也就是：

- authoritative state 在 backend
- frontend 只做 mirror
- mirror 可以是 partial 或 delayed

这是未来真正把 Python 从热路径里拿掉的基础。

## 七、下一阶段计划排序建议

### 第一优先级：稳固架构边界与 C++ ownership

这是所有后续性能路线的前提。

应优先推进：

1. execution episode ownership 继续下沉到 C++
2. `ScenarioLoader` 中 state adapter / frontend helper / scenario adapter 的拆分
3. runtime facade contract 初版
4. CMake target 方向性拆分方案

### 第二优先级：把现有 CUDA helper 线接入主计划

这一步不是重新研究，而是把已有成果纳入统一架构。

应优先推进：

1. visual / observation / flight shaping / broadphase 的 facade-level 接入点
2. resident-state 与 device-resident output 的统一 contract
3. 明确 maintained path 与 experimental path 的切换规则

### 第三优先级：继续选择性下沉 Python 热路径

在主边界稳定后，继续把高频热路径迁到 C++：

1. reward / termination 主编排
2. route / approach / post-transition 逻辑
3. mainline step request build / consume

### 第四优先级：评估 exact GPU backend 的新进入条件

只有满足这些前提后，exact GPU backend 才应重新进入主线候选：

1. compiled episode ownership 稳定
2. frontend 不再持有权威 state
3. resident-state contract 稳定
4. host/device sync 策略统一

### 第五优先级：Rust 作为中远期候选调研项

当前不进入主实施线，但可以保留为后续专题：

- 服务化 facade 是否值得用 Rust 实现
- DTO/serialization service 是否有 Rust 优势
- 是否存在比 nanobind/C++ 更清晰的跨语言 runtime service 架构

## 八、建议补充的后续文档主题

说明：以下内容用于说明建议补充的文档主题和后续计划入口，不构成自动启动的任务列表。

基于本次调研，建议下一步新增或细化以下内容：

1. `runtime_facade_contract_plan`
   说明 facade 的 batch contract、DTO、device-view 契约。
2. `execution_state_adapter_split_plan`
   说明如何拆 `ScenarioLoader`。
3. `cxx_hot_path_migration_matrix`
   枚举 Python -> C++ 的优先迁移路径。
4. `cuda_mainline_alignment_plan`
   把现有 visual/observation/flight-shaping/broadphase/resident-state 线对齐到统一 runtime 架构。
5. `rust_evaluation_note`
   单独记录 Rust 的适用边界和进入条件，而不是把它混进当前主计划。

## 九、最终建议

对于“未来扩展 + 性能优化 + 分层谨慎设计”这件事，当前最合理的总路线是：

1. 继续以 C++ 作为核心后端重构语言。
2. 把 CUDA 视为已存在、可持续推进的后端能力，而不是未来再说。
3. 在 facade、ownership、resident-state 三个层面提前为未来扩展留接口。
4. Rust 暂不进入近期主实现线，只保留为中远期的服务化候选方案。

换句话说，下一步计划不应是：

- “先试试 Rust 会不会更快”
- “先把所有慢代码都搬到 GPU”

而应是：

- “先把 backend ownership 和 runtime contract 稳固下来”
- “再把最有价值的热路径继续下沉到 C++”
- “在已有资产基础上推进 CUDA 的 device-resident 主线”

这样做最符合当前仓库的真实演进方向，也最有可能在不牺牲可维护性的前提下，为未来扩展和性能增长留出空间。
