# C++ 精确运行时重构计划

导航：

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.md](../architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)

状态：2026-04-03 的草案后续实现计划；已于 2026-07-21（统一架构计划 T4 轨道，I43 迭代）针对下文记录的落地事实普查重新冻结——WP1-WP3 已落地，WP4 有部分选配（opt-in）落地。本次重冻结所依据的普查见"工作包"之后的"T4 普查（I43）"一节。
文档角色：

- 本文档描述了一个候选的下一个主线加速/重构路径。
- 它还不是一个独立冻结的执行计划。
- 在其范围被明确重新冻结之前，不应根据本文档展开任何实现。

这是下一主线加速工作的实时候选计划。

关键决策是：

- GPU 精确步进仍然是目标后端。
- 下一个实现优先级不是更多的辅助级 CUDA 调优。
- 下一个实现优先级是一个 C++ 重构，使精确模拟和执行层运行时显式化、面向数据且可批量处理。

## 为什么存在此计划

目前，三个事实在文档、代码和诊断中保持一致：

1. 粗糙的路段线已关闭，不会推广到训练主线。
2. 辅助优先 GPU 线路仅产生适度的端到端收益，现在更多地受主机/运行时结构的限制，而非 CUDA 内核数学。
3. 仓库中已有大量的 C++ 核心，但热路径所有权仍分布在：
   - C++ 精确世界步进
   - Python 任务/情节状态
   - Python 观测/奖励/终止编排
   - 实验性精确 CPU/GPU 缓存会话运行时管道

相关参考：

- [execution_coarse_grained_route_segments.md](../archive/exact_runtime/execution_coarse_grained_route_segments.md)
- [gpu_exact_world_step_rearchitecture_plan.md](../archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md)
- [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
- [system_layering_and_engine_encapsulation_plan.md](../architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)

## 当前诊断

### 1. C++ 中已有的部分

该仓库已经有一个真正的编译核心：

- 精确世界步进真值源：
  [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)
- 多世界所有者/运行时外壳：
  [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)
- 编译执行辅助函数：
  [execution_step_runtime.cpp](../../../src/core/mission/runtime/execution_step_runtime.cpp)
  [execution_frame_runtime.h](../../../src/core/mission/runtime/execution_frame_runtime.h)
  [execution_episode_runtime.cpp](../../../src/core/mission/runtime/execution_episode_runtime.cpp)
- 精确状态契约和实验性 GPU 后端：
  [exact_stage_inventory.cpp](../../../src/core/engine/exact_stage_inventory.cpp)
  [src/gpu/experimental](../../../src/gpu/experimental)

这意味着项目不需要从头开始在“Python”和“C++”之间做出选择。它需要决定是否应该将剩余的热路径所有权合并到编译端。

### 2. Python 热路径中仍保留的部分

执行热路径仍然过于频繁地跨越 Python：

- `ScenarioLoader` 仍然拥有大量可变的情节状态：
  - 航点进度
  - 进场进度
  - 奖励记账
  - 终止记账
  - 命令链同步外壳
  - 任务观测/状态准备
- `compute_full_step(...)` 即使单个奖励/终止辅助函数已编译，仍然执行高频编排。
- `WorldBatchVecEnv` 仍然依赖 Python 端加载器所有者来完成步进语义。

相关代码：

- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [universal_env.py](../../../gym_envs/universal_env.py)

### 3. 当前 GPU 线路停滞的原因

当前的精确步进 GPU 工作已经表明：

- 对等性和阶段本地回放基础设施是有价值的
- 驻留/设备端回放可以变得非常快（在隔离环境中）
- 除非这些契约首先被重构，否则端到端运行时仍然被提取/应用/物化和 Python/运行时粘合代码支配

因此，真正的障碍不再仅仅是“缺少内核”。  
障碍在于精确步进、情节状态机和批处理运行时仍然没有一个稳定的编译契约来拥有它们。

### 4. 现有批量准备层还不够的原因

新的批量准备辅助函数是一个好的方向，但它仍然不是主线情节控制器：

- [execution_episode_batch_prepare.cpp](../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)

今天它仍然比真正的 Python 路径简化：

- 航点/进场接线不完整
- 跑道/在跑道上/任务上下文被简化
- 几个情节状态转换仍在 Python 中派生

因此，它应该被视为新所有权模型的种子，而不是最终的运行时边界。

## 决策

项目现在应该围绕以下序列进行重新架构：

1. 保持 `SimulationKernel` 作为精确 CPU 真值源。
2. 将执行层情节所有权从 Python 移动到 C++。
3. 在世界步进契约之上引入一个稳定的编译情节/控制器契约。
4. 将 `WorldBatchRuntime` 附加到该编译情节/控制器契约。
5. 只有在这些契约上才能推广精确 CPU 后端工作并恢复精确 GPU 后端切换。

简而言之：

`CPU 真值源 -> 编译的情节运行时 -> 编译的精确 CPU 后端 -> 精确 GPU 后端`

而不是：

`更多辅助函数内核 -> 更多运行时补丁 -> 希望端到端速度随之而来`

## 冻结决策

在新的 C++ 运行时边界存在之前：

- 冻结新的粗糙替代线路，除非它们直接支持诊断。
- 冻结辅助级 GPU 微优化，除非它们解除了新后端契约的阻塞。
- 不要将缓存的精确步进后端作为无条件的默认设置推广到维护的训练中。
- 将所有当前的对等性追踪、阶段比较器和驻留状态探测器保留为回归基础设施。

## 目标架构

### A. `SimulationKernel` 保持语义权威

`SimulationKernel` 仍然是以下方面的真值源：

- 精确阶段排序
- 精确 ECS 语义
- 基线调试和存档追踪生成

它应继续暴露：

- 精确阶段库存
- 阶段契约元数据
- 回放/追踪钩子

相关文件：

- [simulation_kernel.h](../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)

### B. 添加一个编译的 `ExecutionEpisodeState`

引入一个编译的状态对象，拥有 `ScenarioLoader` 当前持有的每个情节可变字段。

此状态应至少覆盖：

- 任务命令运行时副本
- 航点列表运行时所有权 / 活动索引 / 航段起点 / 先前距离
- 进场跟踪历史（`dme`、`loc`、`gs` 先前值）
- 离跑道计数器
- 奖励里程碑标志（`liftoff_awarded`、`gear_bonus_awarded` 等）
- 终止原因 / 任务阶段 / 航点后转换状态
- 缓存的航路引用 / 航路元数据

候选文件：

- `src/core/mission/execution_episode_state.h`
- `src/core/mission/execution_episode_state.cpp`

### C. 添加一个编译的 `ExecutionEpisodeController`

引入一个 C++ 控制器，拥有一个执行情节并执行完整的步进契约：

1. 摄取当前真值/仪器状态
2. 更新任务/航点/进场行为状态
3. 构建任务观测/奖励/终止输入
4. 运行编译的情节/帧/步进运行时
5. 为 Python/VecEnv 消费发出一个紧凑的步进结果

此控制器应成为当前 Python 序列的编译等价物：

- `ScenarioLoader.update_behaviors(...)`
- `build_universal_observation(...)`
- `ScenarioLoader.compute_full_step(...)`
- `build_step_info(...)`

候选文件：

- `src/core/mission/execution_episode_controller.h`
- `src/core/mission/execution_episode_controller.cpp`

### D. 将 `WorldBatchRuntime` 从世界所有者提升为情节运行时所有者

`WorldBatchRuntime` 不仅应拥有世界，还应拥有参与维护执行滚动的世界的编译情节控制器。

它应暴露稳定的批量契约，例如：

- `prime_execution_episode_batch(...)`
- `step_execution_episode_batch(...)`
- `get_execution_episode_outputs_batch(...)`
- `reset_execution_episode_batch(...)`

此层应隐藏底层精确步进是：

- `SimulationKernel::step()`
- 编译的精确 CPU 后端
- 精确 GPU 后端

相关文件：

- [world_batch_runtime.h](../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)

### E. 精确步进后端成为私有实现细节

一旦情节控制器边界存在，精确步进后端应位于其下。

该后端应满足一个稳定的契约：

- 接受精确打包状态/状态存储
- 执行精确的有序阶段契约
- 更新情节控制器所需的学习者面向状态表面

此后端可能具有多个实现：

- 实时 ECS 真值路径
- 编译的精确 CPU 后端
- 精确 GPU 后端

### F. Python 成为薄编排层

切换后，Python 应保留：

- 训练编排
- 场景/配置加载兼容性
- 诊断入口点
- 环境包装器兼容性

Python 应停止拥有：

- 步进时间的情节突变
- 奖励/终止记账
- 精确步进后端语义
- 批量运行时内部调度语义

## 重构后的所有权边界

### `SimulationKernel`

拥有：

- 精确 CPU 真值语义
- ECS 世界生命周期
- 追踪和回放权威

不拥有：

- 维护的执行层情节记账
- 批量训练面向的步进结果组装

### `ExecutionEpisodeController`

拥有：

- 每个情节的可变执行状态
- 任务/航点/进场行为转换
- 编译的步进/帧/情节评估接线

不拥有：

- 场景文件解析
- SB3/Gym 接口语义

### `WorldBatchRuntime`

拥有：

- 世界池
- 情节控制器池
- 后端选择和状态同步
- 批量步进/回读契约

### Python（`ScenarioLoader`、`UniversalEnv`、`WorldBatchVecEnv`）

拥有：

- 兼容性垫片
- 配置和调试入口点
- 训练框架适配

不应再拥有：

- 热路径情节状态

## 工作包

### WP1. 冻结情节状态契约

目标：

- 使可变执行情节状态显式且可序列化

交付物：

- `ExecutionEpisodeState` 结构体
- 对等性友好的快照/导出辅助函数
- 测试：在固定脚本场景上比较 Python 拥有的状态与编译状态

主要文件：

- 新增 `src/core/mission/execution_episode_state.*`
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)

验收标准：

- 编译后的状态能够表示当前的 Python 片段簿记，不丢失字段

2026-07-21（I43）当前进展：已落地。`ExecutionEpisodeState`
（`src/core/mission/episode/execution_episode_state.*`）是权威的可变片段状态结构体。
`gym_envs/scenario_loader/runtime_state.py` 的
`build_execution_episode_state`/`apply_execution_episode_state`/
`apply_execution_episode_runtime_fields` 在 `ExecutionEpisodeState` 与
`ScenarioLoader` 实例字段之间双向镶镜；影子对比路径（WP3）与选配的主线路径（WP4）
都经由这同一套镜像通道，因此它是所有权边界本身的承重基础设施，而不是被取代的重复物
（详见下文"T4 普查（I43）"）。

### WP2. 用真实的步骤输入构建器替换简化的批量准备层

目标：

- 使批量构建器在语义上完整，而非近似

交付物：

- 从实时状态完成 `ExecutionEpisodeRuntimeInputs` 的准备
- 完整覆盖航点/进场/安全/目标
- 从主批量准备路径中移除“简化版”分支

主要文件：

- [execution_episode_batch_prepare.h](../../../src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)

验收标准：

- 批量准备的片段输入与现有单步 Python 路径在精心策划的测试场景上匹配

2026-07-21（I43）当前进展：就其既定范围已落地。`execution_episode_batch_prepare.{h,cpp}`
从 `StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState` 物化出
`ExecutionEpisodeRuntimeInputs`；I41 的登记行（`t6_residual_ledger.md` §7.3）发现
`WorldBatchRuntime` 已经通过九个方法读写生成的 `ExecutionEpisodeController` 批量状态。
剩余缺口位于本工作包既定范围的上游：Python 侧
（`gym_envs/scenario_loader/step_evaluation.py::build_step_evaluation_batch_env_state`）
仍在每步手工把 `truth`/`inst` 采集组装成 `StepEvaluationBatchEnvState`，因为 WP2
的范围是"从 env-state 准备"这一步，不是"从 truth 采集 env-state"这一步。该采集步骤
登记为 WP4/T4 的后续工作，不是 WP2 的回归（详见下文"T4 普查（I43）"）。

### WP3. 以影子模式引入编译后的片段控制器

目标：

- 在切换之前，让 C++ 片段控制器与当前 Python 路径并行运行并比较输出

交付物：

- `ExecutionEpisodeController`
- 影子模式比较辅助函数
- 可选的 `WorldBatchVecEnv` 影子模式比较诊断，支持重置/自动重置时的控制器状态同步
- 以下项的一致性诊断：
  - 奖励总和
  - 终止条件
  - 状态向量
  - 任务观测
  - 步骤信息字段

主要文件：

- 新增 `src/core/mission/execution_episode_controller.*`
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- 在 `tests/runtime/` 下新增测试

验收标准：

- 控制器影子模式与遗留的 Python 路径在维护的执行场景和固定脚本轨迹上匹配

截至 2026-04-04 的当前进展：

- `ExecutionEpisodeController` 已存在于 `ef_py` 中，能够评估/步进其拥有的片段状态。
- `ScenarioLoader` 暴露了一个逐步骤的控制器影子比较辅助函数，以及用于目标、路线、进近和起飞整形案例的一致性测试。
- `WorldBatchVecEnv` 现在具有一个可选的 `execution_episode_controller_shadow_compare` 诊断路径，该路径在 rollout 步骤中以影子模式运行编译后的控制器，并在重置/自动重置时重新同步控制器状态。

### WP4. 将编译后的片段控制附加到 `WorldBatchRuntime`

目标：

- 让维护的执行 rollout 通过编译后的片段控制器进行步进，而不是通过 Python 拥有的片段状态

交付物：

- `WorldBatchRuntime` 控制器所有权
- 执行片段的批量步骤/结果 API
- 可选的世界批次执行路径，使用编译后的片段控制

主要文件：

- [world_batch_runtime.h](../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

验收标准：

- 维护的执行 rollout 可以通过编译后的片段控制器运行，使用 CPU 真值步进，且没有 Python 片段状态所有权

2026-07-21（I43）当前进展：部分落地，且为选配（opt-in）。`WorldBatchRuntime`
为每个世界拥有一个池化的 `ExecutionEpisodeController`，Python 侧在 `WorldBatchVecEnv`
上有一个可用的 `execution_episode_controller_mainline` 切换构造参数
（`python/rl/runtime/world_batch/_execution_episode_mixin.py`），开启后批量经由
`WorldBatchRuntime.step_execution_batch(...)` 步进，完全绕开
`ScenarioLoader.compute_full_step`。该参数默认 `False`，相对默认路径尚不功能完整——
`_air_combat_post_launch_mixin.py` 在其开启时显式禁用了 post-launch 评估功能，且要求
编译版 flight-shaping 后端。本节已陈述的退出条件——"维护的 `p5` 执行路径不再依赖
Python 拥有的热路径片段状态"——因此**尚未达成**；`compute_full_step` 仍是真正的默认路径。
本迭代在结论"尚无安全可退役对象"之前跑的完整双所有权普查，见下文"T4 普查（I43）"。

### WP5. 提升编译后的精确 CPU 后端

目标：

- 从“仅实时 ECS 真值步进”转变为在相同控制器/运行时边界之后使用编译后的精确 CPU 后端

交付物：

- 面向数据的精确 CPU 状态存储
- 实现相同命名阶段合约的精确 CPU 后端
- 逐阶段一致性门控与实时 ECS 真值对比

主要文件：

- 新增 `src/core/engine/exact_cpu_backend.*`
- 新增 `src/core/engine/exact_state_store.*`
- [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)

验收标准：

- 编译后的精确 CPU 后端重放与实时 ECS 真值源相同的精确状态阶段合约

### WP6. 重新附加精确 GPU 后端

目标：

- 将现已稳定的精确 CPU 后端合约移植到 CUDA

交付物：

- 在相同控制器/运行时合约之下的精确 GPU 后端
- 仅在控制器/运行时边界稳定后，设备驻留执行

主要文件：

- [src/gpu/experimental](../../../src/gpu/experimental)
- [src/gpu/README.md](../../../src/gpu/README.md)
- [exact_stage_inventory.cpp](../../../src/core/engine/exact_stage_inventory.cpp)

验收标准：

- 维护的运行时可以切换精确后端，无需更改 Python 片段所有权

## T4 普查（I43，2026-07-21）：Python 逐步 builder 双所有权普查

统一架构计划 T4（"支持 WP4 热路径切换到 `WorldBatchRuntime`；退役被 C++ 所有权替代
的 Python 逐步 builder；重冻结 exact-runtime 计划文档"）以对 `python/**` 与
`gym_envs/**` 中手写逐步（per-step）DTO 构造代码的全仓普查开篇，并与本文档已描述
的 C++ 落地路径逐一对照。本节是追加性质：不推翻上文任何结论，仅记录本次普查与其
处置结果，供下一个 T4 切片参考。

### 普查发现：三层并存，而非一条待替换的遗留路径

Python 执行步进热路径（`gym_envs/scenario_loader/step_evaluation.py`、
`execution_runtime/mainline.py`、`execution_runtime/shadow.py`，以及
`python/rl/runtime/world_batch/_execution_episode_mixin.py`/
`_observation_mixin.py` 这两个 mixin）并不是"一条 Python 所有权路径，等待唯一的
C++ 替代品落地"，而是三层并存、且各自都有真实、当前仍在被使用的消费者：

1. **逐项消费聚合编译产品**——`ScenarioLoader.compute_full_step` 是真正的默认
   编排器（由 `use_compiled_execution_step_runtime` 控制，默认 `True`）：默认路
   径上它逐项消费 `_prepare_step_evaluation` 内一次聚合
   `compute_execution_episode_runtime` 调用的子产品、并围绕各项做 Python 记账；
   真正的逐项编译调用（`compute_safety_runtime`/`compute_approach_reward_terms`
   等）发生在缓存未命中/部分产品路径，以及该开关被强制设为 `False` 的回退通道
   上——这是一条真实、有测试覆盖的回退通道（等价测试节点见
   `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py` 与
   `test_execution_step_runtime.py::ExecutionEpisodeRuntimeTests` 的 frame/episode
   等价契约），不是纯理论上的存在，也是唯一在该开关下仍能工作的一层。
2. **批量 frame-product 准备**（`WorldBatchVecEnv` 的
   `execution_step_batch_prepare=True`）——Python 为每个 env 手工构造
   `StepEvaluationBatchConfig`/`StepEvaluationBatchEnvState`，整批调用一次
   `ef_py.prepare_step_evaluations_batch`；但奖励/终止的提取（第 1 层逐项
   `_add_reward_term` 记账）之后仍在 Python 中运行。真实且有测试覆盖
   （`test_world_batch_vec_env_reuses_cached_step_evaluation_for_reward_tail`）。
3. **execution-episode-controller 主线**（`execution_episode_controller_mainline=True`）
   ——这正是上文 WP4 所描述的那一层，且已经存在于代码中：Python 为每个 env 构造
   `WorldExecutionEpisodeStepRequest`，其余全部交给
   `WorldBatchRuntime.step_execution_batch(...)`，`ScenarioLoader.compute_full_step`
   完全不再被调用。该参数默认 `False`，且 `_air_combat_post_launch_mixin.py` 在其
   开启时显式禁用了 post-launch 评估功能，因此第 3 层相对第 1/2 层尚不功能完整，
   WP4 自身的退出条件也尚未达成（见上文 WP4 的当前进展记录）。

三层均非死代码：每一层都有各自命名清晰的生产触发开关（构造参数），或专门的回归
测试，与本文档"冻结决策"一节"把所有当前的一致性追踪、阶段比较器和驻留状态探测器
保留为回归基础设施"的既定决策完全吻合。项目自身 README 所命名的 T4 关键风险——
"迁移期间的分歧式双所有权"——因此在本提交点被证实确实存在，且是刻意为之，不是
本切片需要修补的缺陷。

### 一对更窄的双所有权配对：已调查，登记为缓办（不退役）

`gym_envs/scenario_loader/step_evaluation.py::prepare_step_evaluation` 中，
`if loader._compiled_execution_episode_enabled(): ... elif
loader._compiled_execution_frame_enabled(): ...` 在
`ExecutionEpisodeRuntimeInputs`/`compute_execution_episode_runtime`（episode 层）
与 `ExecutionFrameRuntimeInputs`/`compute_execution_frame_runtime`（frame 层）
之间做分支选择。两个使能判断函数共享完全相同的门控条件（`use_compiled_execution_step_runtime`
加上一个针对同一个编译好的 `ef_py` 二进制、永远同真同假的 `hasattr` 检查——两个绑定
位于同一个翻译单元内，中间没有任何条件编译分隔），因此该 `elif` 分支在任何生产
配置下都不可能被触达。全仓引用面普查证实了这一点：唯一会观察到 frame 分支的调用方是
`test_scenario_loader_execution_step_runtime.py`，它直接对
`loader._compiled_execution_episode_enabled`/`_compiled_execution_frame_enabled`
做 monkeypatch 以强制触发该分支，专门用于练习 `defer_compiled_runtime`/`compact_output`
机制的"frame"分支。`ExecutionFrameRuntimeInputs`/`compute_execution_frame_runtime`
本身仍是真实、独立被使用的 C++ 资产：`tests/runtime/mission/test_mission_runtime.py`
直接调用该编译函数，
`tests/runtime/execution/test_execution_step_runtime.py::ExecutionEpisodeRuntimeTests::test_frame_compatibility_runtime_matches_episode_owner_across_batch_boundaries`
把 frame/episode 数值等价性本身作为一份独立的兼容性契约钉住。只有 Python 分发逻辑里
的这个 `elif` 分支在生产环境中不可达，且这种不可达是设计使然（只能靠 monkeypatch
触发），不是意外或代码腐化的产物。处置：登记为缓办，不退役——删除它需要改动一个
被直接练习的测试，而其本身对行为零改变，收益不足以支撑单独为它辩护一次退役；因此
把它作为一条命名清晰、原因已查明的残留登记在此，留给下一个重新审视
`prepare_step_evaluation` 分发逻辑的迭代，而不是本切片孤立地去做这一处删除。

### 处置结论与下一次触发条件

在本提交点，三层热路径没有任何一层够格退役：每一层要么是真正的默认消费路径
（第 1 层），要么带有专属、当前全绿的回归/一致性测试（第 2/3 层，以及上文的
frame/episode 分发分支）。但普查的方法级清扫（对 29 个步进层模块中约 591 个
函数/方法的全量引用计数）确实定位到了八个已死的逐步 builder **接口**——在定义点
之外零引用（生产、测试、工具、fixture 全部干净）——本切片按 I14 死接口移除先例
将其退役：五个 `ScenarioLoader` 转发壳，其调用点早已下沉到各自模块级 free
function（`_build_mission_nav_products`、`_compute_mission_observation_products`、
`_build_step_info_runtime_inputs`、`_consume_compiled_episode_runtime`、
`_build_waypoint_reward_inputs`；free function 本身仍是维护中的第 1/2 层基础设施），
以及三个已被 C++ 支撑的批量路径取代的方法——
`_WorldBatchVecEnvObservationMixin._collect_observations`（调用方现在直接驱动
`_read_truth_and_inst_batch` + `_build_observations_from_cached_state`）、
`_WorldBatchVecEnvExecutionEpisodeMixin._execution_episode_controller_state_requires_reprime`
（reprime 判定经由编译侧 `execution_episode_ready` 完成，不再走 Python 侧状态摘要
比对）、`CooperativeWorldBatchVecEnv._build_slot_observation`（被承载在
`ef_py.compute_execution_observation_batch_numpy` 上的批量
`compute_execution_observation_batch` 路径取代）。八个均为私有名，"非目标"一节的
公共表面条款不受触碰，且该移除因构造即零行为变更。下一次真正（层级级别）退役的
触发条件是明确的：一旦第 3 层（`execution_episode_controller_mainline`）覆盖了
post-launch 评估路径与第 1/2 层全部 `flight_shaping_backend` 选项，并从选配升级
为默认，第 1 层 `compute_full_step` 的逐项手工编排就会成为本项目 README 已经命名
的那个退役目标。

### 默认值翻转补记（I82，2026-07-27）：覆盖单元格解析规则落地，翻转 HELD 待性能证据

本补记登记上述触发条件的部分触发，且翻转本身处于 HELD 状态。随着覆盖矩阵
落地（I80）与处置裁定完成（I81/I91），`execution_episode_controller_mainline`
构造函数默认值从硬编码 `False` 改为未设置哨兵值，并在构造时解析
（`WorldBatchVecEnv._resolve_execution_episode_controller_mainline_default`）。
解析器完整编码了覆盖单元格所有权规则——compiled/auto 飞行整形后端、未配置
post-launch 评估、动作模式在一致性钉子白名单内（`full`/`takeoff2`/`takeoff4`，
每个模式都有各自的跨层一致性钉子；白名单极性，新动作模式默认走 Python
路径）、想定未声明脚本化对手、想定未声明第二个实体阵营、未启用第 2 层
`execution_step_batch_prepare` 选配、且运行时片段控制器 API 存在——但翻转
本身被 DISARMED 在模块常量 `_CONTROLLER_DEFAULT_FLIP_ARMED = False` 之后
（python/rl/runtime/world_batch/vec_env.py）：当该常量为 `False` 时，所有
未设置的默认值都解析到 Python 编排路径，而本会被该规则翻转的单元格通过
解析自省属性报告命名原因
`default_off_covered_cell_flip-held-pending-performance`。

HELD 裁定（2026-07-27，依据所有者明示的委托授权——所有者的"允许代签"
授权——签发，登记为受委托的程序性裁定，而非人类专家判断）：本计划的验收
标准要求编译片段切换必须超出噪声地改善维护中执行 rollout 的墙钟时间，而
该切片自身的热路径测量显示控制器路径在内联微型 fixture 上比 Python 路径
慢 20-30%（n_envs=1 中位数 0.297 对 0.244 秒/100 步；n_envs=8 中位数
2.409 对 1.869）。因此默认翻转 HELD，待代表性想定的墙钟证据；依照程序的
性能边界，该性能工作路由到 exact-runtime 线，由其持有解除条件（一次代表性
想定测量，证明控制器路径超出噪声地改善维护中 rollout）。

该切片构建的其余一切均保留。所有非覆盖配置都以命名原因解析回 Python
编排路径且绝不报错（gpu_host 在 Python 路径上保持 HELD；配置了 post-launch
的运行绑定红线，因为 mainline 硬禁用该评估；`naval_station3` 保持 Python
所有的海军奖励表面——直接证据：控制器路径不产生
`naval_station_error_penalty`；多阵营想定保持 Python 所有的战斗产物——直接
证据：第 1 层报告 `combat_win`/`combat_timeout` 之处控制器路径报告泛化的
`timeout`；脚本化对手由 `update_behaviors` 在 Python 侧步进，而 mainline
将其替换为 `update_command_chain_only`）。显式 `True`/`False` 保持翻转前的
精确语义——公共 kwarg 名称不变，且覆盖单元格的跨层一致性证据（显式控制器
对显式 Python 路径）作为显式选配一致性保持绿色。该切片没有发生第 1 层
退役：`compute_full_step` 编排、post-launch mixin、影子比较器与第 2 层
reward tail 仍可从被排除单元格和显式 `False` 到达，因此该切片的只收缩删除
清单经裁定为空（删除拖尾到后续切片，待被排除单元格获得控制器侧所有者且
翻转解除 HELD 之后）。证据：
tests/runtime/exact/test_execution_controller_option_parity.py（覆盖单元格
的 HELD 翻转默认解析钉子、显式选配跨层一致性钉子、被排除单元格解析钉子，
以及记录在案的热路径测量）。

## 阶段性修改计划

### 阶段 0. 边界冻结与仪器化

范围：

- 冻结新的所有权决策
- 添加缺失的比较钩子，以便未来的切换可被测量

变更：

- 记录所有权边界
- 添加片段控制器一致性测试装置
- 收紧运行时统计信息命名，以明确写回/物化/同步

退出条件：

- 一次诊断运行可以比较：
  - 遗留的 Python 片段路径
  - 编译后的控制器影子路径
  - 其下的精确 CPU/GPU 后端路径

### 阶段 1. `ExecutionEpisodeState` 落地

范围：

- 将可变片段状态定义移至 C++

变更：

- 添加 `ExecutionEpisodeState`
- 为测试添加导出/导入辅助函数
- 教导 Python 加载器镜像此状态，而不是成为其唯一所有者

退出条件：

- 状态合约是显式的、可测试的，并且不再隐藏在 Python 实例字段中

### 阶段 2. 完成批量输入准备

范围：

- 从编译的执行输入构造中移除近似

变更：

- 扩展 `execution_episode_batch_prepare`
- 连接完整的航点/进场/目标/安全输入
- 从维护路径中移除当前的简化分支

退出条件：

- 准备好的批量输入足以复现当前的执行步进语义

### 阶段 3. C++ 片段控制器影子切入

范围：

- 实现控制器，但暂时不更改维护的默认行为

变更：

- 添加控制器类
- 从 Python/运行时测试中以影子模式运行控制器
- 在维护的场景上记录/比较一致性

退出条件：

- 控制器一致性足够稳定，可用于选择性切换

### 阶段 4. `WorldBatchRuntime` 切换

范围：

- 使编译后的控制器成为 `WorldBatchRuntime` 下维护的执行层所有者

变更：

- 运行时拥有控制器
- `WorldBatchVecEnv` 读取紧凑的批量输出，而不是依赖 `ScenarioLoader.compute_full_step(...)`
- `ScenarioLoader` 缩减为配置/调试适配器职责

退出条件：

- 维护的 `p5` 执行路径不再依赖 Python 拥有的热路径片段状态

### 阶段 5. 精确 CPU 后端提升

范围：

- 将精确步进移至控制器/运行时边界之后

变更：

- 精确 CPU 后端成为可选择的运行时后端
- 实时 ECS 步进保持为真值参考和调试路径

退出条件：

- 精确 CPU 后端逐阶段匹配实时真值

### 阶段 6. 精确 GPU 后端提升

范围：

- 在新的稳定合约上恢复 GPU 切换

变更：

- GPU 后端移植精确 CPU 后端合约
- 设备驻留状态保持在控制器/运行时边界之下

退出条件：

- 精确 GPU 后端不再同时与 Python 拥有的片段状态和运行时写回语义斗争

## 立即实施的第一批

第一批实施应有意地狭窄：

1. 添加 `ExecutionEpisodeState` 及其 Python 测试/导出接口。
2. 扩展 `execution_episode_batch_prepare`，直到它可以表示真实维护的执行步进输入而不进行简化。
3. 为一个维护的执行场景系列添加影子 `ExecutionEpisodeController`。
4. 添加一致性测试，比较：
   - 奖励
   - 终止条件
   - 状态
   - 任务观测
   - 紧凑步骤信息

这第一批不应：

- 重写主导运行时
- 替换 `SimulationKernel` 真值步进
- 进一步提升精确 GPU 后端
- 扩大粗粒度替代方案

## 建议的文件计划

### 新文件

- `src/core/mission/execution_episode_state.h`
- `src/core/mission/execution_episode_state.cpp`
- `src/core/mission/execution_episode_controller.h`
- `src/core/mission/execution_episode_controller.cpp`
- `tests/runtime/execution/test_execution_episode_controller_parity.py`
- `tools/diagnostics/compare_execution_episode_controller_parity.py`

### 早期可能更改的现有文件

- [execution_episode_batch_prepare.h](../../../src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)
- [world_batch_runtime.h](../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

## 验收标准

### 正确性

- 在声明的打包状态表面上，阶段局部精确步进一致性保持零漂移
- 编译后的片段控制器在策划的场景上与当前维护的 Python 执行逻辑匹配
- 维护的运行时在非 CUDA 构建上保持 CPU 回退行为

### 性能

- 编译后的片段切换必须将维护的执行 rollout 的墙钟时间改善到超出噪声水平
- 在控制器/运行时切换移除当前的提取/应用/Python 瓶颈之前，不应重新考虑精确 GPU 的提升

### 可维护性

- 执行热路径片段状态的一个显式所有者
- 精确步进后端选择之上的一个显式运行时边界
- Python 环境停止重复任务/终止簿记逻辑

## 止损规则

如果发生以下任何情况，停止或重新设定范围：

- 新的 C++ 状态/控制器边界无法表示当前维护的语义，而不过度使用 Python 回退分支
- 因为边界仍然过于底层，任务/航点所有权中的一致性聚类失败
- 即使在精确 GPU 提升之前，控制器切换后的测量增益仍停留在噪声基底

如果发生这种情况，下一步调整应是简化运行时边界，而不是添加更多的本地辅助优化。

## 总结

下一步的主要行动不是“先更多 CUDA”。  
下一步的主要行动是：

- 在 C++ 中显式化执行热路径所有权
- 让 `WorldBatchRuntime` 拥有编译后的执行片段
- 保持 `SimulationKernel` 作为真值
- 然后在该稳定的运行时合约之下提升精确 CPU 和精确 GPU 后端

这是从当前混合所有权模型到能够真正提供 GPU 加速而不与 Python 控制平面斗争的后端的最短路径。
