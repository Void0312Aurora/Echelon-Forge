# GPU 执行主线路集成检查清单

语言：
- 英文规范版：[gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
- 中文伴随版：`gpu_execution_mainline_integration_checklist.zh.md`

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/exact_runtime/gpu_execution_mainline_integration_checklist.md`
Owner: `architecture/exact-runtime`
Last verified: `2026-08-08`
Content status: 迁移后的检查清单快照；激活前须依据当前代码与运行证据重新核验所有项目。

状态：源自 2026-04-18 开放的 draft issue；当时维护的 `p5` 默认值已回退到
编译 CPU 主线路可视化路径。本文当前未激活；后续 CUDA 驻留计划均已无晋级
收口，未来工作需要新的明确授权。
本文记录一条把已关闭第 0-4 阶段 GPU 运行时工作转为维护中执行层加速的候选路线。
它是一个 GPU 集成跟踪检查清单，不是通用架构权威，也不是当范围需要更改时单独冻结的任务边界的替代品。
精确步骤迁移线现已拆分为
gpu_exact_world_step_rearchitecture_plan.md (`git show 70c07a77:docs/plan/archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md`)，
该文档冻结了新的“CPU 真实来源→精确 GPU 后端”重新架构。

## 范围

此检查清单特意比 gpu_execution_runtime_research_and_design.md (`git show 70c07a77:docs/plan/archive/exact_runtime/gpu_execution_runtime_research_and_design.md`) 中的研究/设计文档范围更窄。
它仅跟踪将 GPU 辅助执行集成到以下内容所需的工作：

- 执行层 `train.py` 在维护的冻结后 `p5` 路径中的 rollout
- 依赖于维护的执行工件的冻结 leader 配置
- `ef_py`、`WorldBatchRuntime` 和 `WorldBatchVecEnv` 中维护的运行时边界

独立的探针和实验性 API 本身不视为“主线路”。

## 什么算作主线路

对于此仓库，“主线路”意味着以下所有条件均为真：

- 该路径可从 [train.py](../../../../../train.py) 访问，而无需为每次运行修补本地代码
- 维护的执行配置可以直接选择它
- 该路径具有稳定的 Python 绑定合约，而不仅仅是探针二进制文件
- 在非 CUDA 构建上 CPU 回退行为保持正确

当前维护的执行 `p5` 配置位于
[examples/config/training/frozen/execution](../../../../../examples/config/training/frozen/execution) 下。

## 当前快照

### 已集成到维护边界

- [x] 在 [CMakeLists.txt](../../../../../CMakeLists.txt) 中存在可选的 CUDA 构建脚手架。
- [x] 当存在启用 CUDA 的 `ef_py` 模块时，`train.py` 优先选择 `build-gpu`。
- [x] `WorldBatchVecEnv` 可以通过 `ef_py.compute_world_batch_visual_observation_batch_numpy(...)` 跨世界批量生成可视化观察。
- [x] `WorldBatchVecEnv` 可以通过 `ef_py.compute_execution_observation_batch_numpy(...)` 批量打包执行观察。
- [x] 维护的冻结后执行 `p5` 配置已经公开了一个维护的世界批量路径，具有：
  - `runtime.world_batch_vec_env=true`
  - `batch_observation_backend=compiled`
  - `batch_visual_backend=compiled`
  - `env.execution_step_runtime_mode=compiled`
- [x] 旧的混合 `gpu_host` 可视化通道和更广泛的全部 `gpu_host` 观察/可视化通道仍仅作为明确的诊断手段可重现，而非维护的默认值。
- [x] `WorldBatchRuntime` 暴露了维护的 broadphase 辅助函数，用于传感器、可视化和通信候选列表。
- [x] 世界批量可视化辅助函数已在场景收集之前消耗了维护的可视化候选辅助函数。
- [x] `WorldBatchRuntime` 公开了第 4 阶段打包状态路径的打包飞行提取/应用/实验步进 API。

### 尚未主线路完整

- [ ] 单世界
  [UniversalEnv](../../../../../gym_envs/universal_env.py) 不使用世界批量 GPU 辅助路径。
- [ ] Python 训练仍然承载主机端 rollout 存储 / VecEnv 兼容性开销，尽管维护的 CUDA 路径现在具有基于 DLPack 的设备端导出和 rollout 推理消费能力。
- [ ] GPU 飞行整形内核现已集成到显式后端标志后面，但尚未推广为维护的默认奖励路径。
- [ ] 任务/奖励/终止评估在 [ScenarioLoader](../../../../../gym_envs/scenario_loader/core.py) 中仍为 CPU 端。
- [ ] 实时传感器和通信系统在热路径中不消耗 GPU broadphase 或 GPU narrow phase。
- [ ] 维护的默认 `WorldBatchRuntime.step_batch()` 路径仍然依赖 CPU `SimulationKernel::step()` 语义；新的精确缓存第一作用域后端仍然是显式选择加入的运行时研究基础设施，而非维护的 rollout 默认值。
- [ ] 第 4 阶段打包飞行 GPU 步进尚未匹配完整精确 ECS 世界步进语义。

## 即时一致性差距

在进一步加速工作前应清理这些，否则存储库将继续承载多个关于“当前 `p5`”含义的不兼容概念。

- [x] 活跃的连续工件文档现在将维护的执行配置与历史工件溯源配置分开，位于 [reference_artifacts.md](../../../../reference_artifacts.md) 中。
- [x] 维护的冻结后执行文档指向 [frozen/execution/p5_continuous_retrain_v1.json](../../../../../examples/config/training/frozen/execution/p5_continuous_retrain_v1.json) 和 [frozen/execution/p5_continuous_coldstart_retrain_v2.json](../../../../../examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)。
- [x] 冻结的 leader 配置现在引用维护的冻结后执行 `p5` 配置谱系，而非历史顶层 `p5` 配置。

此项清理的验收标准：

- 一个执行配置谱系被标记为 `p5` 的维护真实来源
- 文档和冻结的 leader 依赖要么指向同一个配置，要么明确记录为何它们有意不同

## 集成顺序

### 1. 基线卫生

- [x] 选择一个维护的执行 `p5` 配置谱系，并使文档保持一致。
- [x] 在维护的配置文档中添加显式说明，解释为什么两个维护的 `p5` 批量后端默认都保持 `compiled`，以及为什么 `gpu_host` 仍仅限基准测试。
- [x] 记录预期的硬件/构建矩阵：
  - 仅 CPU 构建
  - 没有可用运行时设备的 CUDA 构建
  - 有可用运行时设备的 CUDA 构建

主要文件：

- [docs/reference_artifacts.md](../../../../reference_artifacts.md)
- [examples/config/training/frozen/execution/README.md](../../../../../examples/config/training/frozen/execution/README.md)
- [examples/config/training/frozen/execution/p5_continuous_retrain_v1.json](../../../../../examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- [examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json](../../../../../examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)
- [examples/config/training/frozen/leader_c2_frozen_v1.json](../../../../../examples/config/training/frozen/leader_c2_frozen_v1.json)
- [examples/config/training/frozen/leader_task_only_frozen_v1.json](../../../../../examples/config/training/frozen/leader_task_only_frozen_v1.json)

### 2. 稳定当前 GPU 辅助的 CPU 步进通道

这是当前最高置信度的生产路径：

- CPU 精确步进保持权威
- 批量观察保持在编译的 CPU 辅助函数上
- 批量可视化保持在编译的 CPU 辅助函数上
- 保留的 `gpu_host` 辅助函数实验仍为显式选择加入

检查列表：

- [x] 将 `WorldBatchVecEnv` 保持为冻结后执行 `p5` 路径的维护执行 rollout 后端。
- [x] 为维护的 `p5` 场景添加可重现的吞吐量基准测试，涵盖：
  - 传统单世界路径
  - 世界批量编译路径
  - 使用 `gpu_host` 可视化功能的世界批量编译路径
- [x] 添加运行时日志记录或基准测试输出，记录实际使用了哪个可视化后端以及 CUDA 是否可用。

主要文件：

- [train.py](../../../../../train.py)
- [python/rl/runtime/world_batch_vec_env.py](../../../../../python/rl/runtime/world_batch_vec_env.py)
- [tools/diagnostics/benchmark.py](../../../../../tools/diagnostics/benchmark.py)
- [tests/world_batch/test_world_batch_vec_env_execution_and_observation.py](../../../../../tests/world_batch/test_world_batch_vec_env_execution_and_observation.py)

验收标准：

- 维护的 `p5` rollout 在仅 CPU 和 CUDA 构建上都能顺畅启动
- 可视化语义保持在现有容差范围内
- 维护的基准测试将实验性 `gpu_host` 比较保持显式化，并显示任何辅助函数在目标硬件上是否实际值得重新启用

说明：

- `train.py` 现在在执行路径上打印请求的和有效的维护世界批量可视化/奖励后端选择。
- `benchmark.py --family world_batch_vec_env` 记录 CUDA 探针信息以及维护的 `p5` 场景 A/B 运行的有效可视化/观察后端。

### 3. 在触及精确世界步进之前集成 GPU 飞行整形

这是第一个缺失的 GPU 内核，它同时满足：

- 已在探针级别实现
- 相对于当前参考在数值上精确
- 比观察打包更密集的算术运算

检查列表：

- [x] 为批量 GPU 飞行整形评估添加维护的 Python 绑定。
- [x] 在 [ScenarioLoader](../../../../../gym_envs/scenario_loader/core.py) 中的奖励路径中将该辅助函数串联起来，置于显式后端标志之后。
- [x] 将精确的 CPU 奖励语义保持为回退和合约参考。
- [ ] 在推广任何新默认值之前，测量真实的端到端 `p5` 步进改进。

主要文件：

- [src/gpu/gpu_flight_shaping_runtime.h](../../../../../src/gpu/gpu_flight_shaping_runtime.h)
- [src/gpu/gpu_flight_shaping_runtime.cpp](../../../../../src/gpu/gpu_flight_shaping_runtime.cpp)
- [src/gpu/gpu_flight_shaping_runtime_cuda.cu](../../../../../src/gpu/gpu_flight_shaping_runtime_cuda.cu)
- [src/interfaces/python/python_module.cpp](../../../../../src/interfaces/python/python_module.cpp)
- [gym_envs/scenario_loader/](../../../../../gym_envs/scenario_loader)
- [tests/runtime/mission/test_mission_runtime.py](../../../../../tests/runtime/mission/test_mission_runtime.py)

验收标准：

- 奖励总和与当前编译的运行时在数值上保持一致
- 终端/截断行为不发生漂移
- 维护的 `p5` 基准测试在生产批量大小下显示出实际的步进时间收益

### 4. 向学习器公开设备端驻留输出

当前 `gpu_host` 路径在结构上受到限制，因为 Python 训练端仍然消耗主机 NumPy 数组。

检查列表：

- [x] 为可视化输出和观察输出暴露 DLPack 或等效的设备张量导出接口。
- [x] 添加一个 rollout 推理路径，该路径可以在 CUDA 上直接消费当前批次，用于策略/价值前向传递。
- [ ] 端到端移除 rollout 缓冲区存储和学习器更新输入中的 NumPy 暂存。
- [ ] 仅在此零拷贝消费路径存在后，重新评估 `batch_observation_backend=gpu_host`。

主要文件：

- [src/interfaces/python/python_module.cpp](../../../../../src/interfaces/python/python_module.cpp)
- [src/gpu/gpu_visual_runtime.h](../../../../../src/gpu/gpu_visual_runtime.h)
- [src/gpu/gpu_execution_observation_runtime.h](../../../../../src/gpu/gpu_execution_observation_runtime.h)
- [python/models/transformer.py](../../../../../python/models/transformer.py)
- [train.py](../../../../../train.py)

验收标准：

- 当前 rollout 策略/价值推理可以在 CUDA 路径上消费面向学习器的张量，而无需主机往返
- 完整的 rollout 缓冲区存储仍需要后续的后续更改
- 仅 CPU 运行仍无需代码更改即可工作
- rollout 和学习器内存所有权是显式的且可测试

说明：

- 维护的 CUDA 训练过程在同一进程中使用 `torch` 和 `ef_py` 时，必须首先导入 `torch`；直接的 DLPack 桥现在依赖于该导入顺序。
- `tools/diagnostics/benchmark.py --family policy_observation_bridge` 是用于“桥开/关”rollout 对比的维护 A/B 框架。
- 该同一框架现在还记录请求/生效的 `flight_shaping_backend` 以及最新的视觉/飞行塑形运行时统计信息，并支持 `--flight-shaping-backend` 覆盖，用于维护的类似 `p5` 的 A/B 测量。
- 本阶段的下一个冻结后续工作是 [gpu_execution_phase4_rollout_hot_path_freeze.md](../../../../../tests/fixtures/runtime_profiles/cuda_resident_program_2/gpu_execution_phase4_rollout_hot_path_freeze.md)，该文件在任何进一步默认更改之前，隔离了 `WorldBatchVecEnv` 的主机拷贝语义。
- 来自该冻结的初始 Phase 4C 结果显示 `observation_return_mode=view` 是有效的，有时稍快，但维护的 `p5` 增益在较大批量下趋于噪声，因此维护的默认值暂时保持为 `copy`。
- 在引入设备驻留 rollout 缓冲区后的当前 A/B 运行显示出更清晰的分化：
  - `collect_rollouts()` 仍然混合到负面，因为精确的环境步进、动作传递、奖励/完成以及 VecEnv 兼容路径仍然偏向主机。
  - `train()` 变得更快，因为 rollout 小批量不再在每次学习者更新前经过 NumPy 往返。
  - 截至 2026-04-18 的 `p5` 对比，维护的默认值仍保持在编译的视觉路径上；混合的 `gpu_host` 视觉路径仅作为基准参考，因为它在当前生产工作负载上是功能性的但较慢。

### 5. 通过真实运行时消费者扩展 GPU 交互集成

Phase 3 在运行时边界可用，但只有视觉有真实的维护消费者。

检查清单：

- [ ] 决定传感器和通信是否应首先使用维护的宽相位辅助 API，还是直接跳到更深的实时系统集成。
- [ ] 在尝试任何更广泛的窄相位重写之前，添加一个维护的传感器或通信调用点消费者。
- [ ] 保持确切的“候选超集，无遗漏”契约作为验收规则。

主要文件：

- [src/core/engine/world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- [src/gpu/gpu_interaction_broadphase_runtime.h](../../../../../src/gpu/gpu_interaction_broadphase_runtime.h)
- [src/models/systems/default_sensor_model.cpp](../../../../../src/models/systems/default_sensor_model.cpp)
- [tests/gpu/test_gpu_runtime_bindings.py](../../../../../tests/gpu/test_gpu_runtime_bindings.py)

验收标准：

- 相对于当前参考路径，没有遗漏真实的交互
- 至少存在一个超出视觉的维护运行时消费者

### 6. 保持确切 GPU 世界步进分离，直到语义等价存在

当前的打包飞行 GPU 步进是有用的研究基础设施，但它还不是 `SimulationKernel::step()` 的直接替代品。

活跃的确切迁移后续工作：

- gpu_exact_world_step_migration_plan.md (`git show 70c07a77:docs/plan/archive/exact_runtime/gpu_exact_world_step_migration_plan.md`)
- 截至 `2026-03-27` 的状态：新的重新架构线现在已经达到了对于确定性单世界、`world_count=4` 和 `world_count=16` 第一范围飞机夹具在 8 步固定种子扫描上的确切缓存会话等价（`first_cpu_divergence_step=0`，`final_cached_component_digests_match=true`）。相同的 `world_count=16` 夹具现在也通过显式的实验性 `WorldBatchExactStepBackend` 运行时切换路径（`--runtime-step-batch-backend`）匹配。`WorldBatchRuntime` 仍然将该后端保留为显式的选择加入实验，并且它仍然在维护的 `p5` 默认值之外，即使更广泛的批处理门现已关闭。最新的惰性同步后续工作还从该实验性运行时路径中移除了每步实时世界写回，并且最新的 `2026-03-27` 驻留快速路径后续工作还从覆盖的 `step_batch()` 主体中移除了步内 D2H 物化（在任何显式提取/实时世界访问之前 `chain_device_to_host_ms == 0.0`）。后来的 `2026-03-27` 静止路径后续工作现在也完全跳过了当前基准风格运行时步进夹具的 CPU 命令通道批处理（覆盖行上的 `chain_command_lane_ms == 0.0`）。最新的窄化传递还将该路径切换为更小的驻留 `pilot + world_time` 投影，而不是先克隆和重新打包整个缓存状态批处理。最新的 `2026-03-27` 无导弹后续工作然后教导驻留重放在上传的批处理没有导弹行时完全跳过指导计数器 memset、指导内核启动和计数器 D2H 复制。后来的 `2026-03-27` 静止后续工作然后将相同的 `pilot + world_time` 驻留同步与无导弹的仅飞机重放融合，将覆盖的运行时步进热路径收缩为一次 H2D 复制加上一次 CUDA 启动/同步。最新的矩阵现在报告大约 `0.194x`（world_count=1）、`0.197x`（world_count=4）和 `0.583x`（world_count=16）的温暖运行时步进加速比，`chain_host_to_device_ms` 降至约 `0.008-0.009 ms`，而温暖写回和 `chain_command_lane_ms` 保持为 `0.0`。随后的流转换现在还将驻留 CUDA 载体从 `cudaDeviceSynchronize()` 移动到具有可重用计时事件的专用缓存流上，但新的 `world_count=1,4,16` 矩阵仍然稳定在约 `0.096 ms`、`0.099 ms` 和 `0.108 ms` 的温暖运行时步进时间，只有约 `0.136x`、`0.190x` 和 `0.439x` 的温暖运行时步进加速比。最新的原始驻留投影后续工作然后用可重用的固定主机缓冲区替换热路径可分页投影向量，让无导弹图重用固定的 memcpy 源而无需每步节点参数更新，并在上传期间预分配该缓冲区，以便第一次运行时步进不再吸收多秒的惰性分配峰值。最新的矩阵现在稳定在约 `0.089 ms`、`0.092 ms` 和 `0.100 ms` 的温暖运行时步进时间，温暖链总计接近 `0.077 ms`、`0.080 ms` 和 `0.081 ms`，第一步冷成本回到约 `20.3 ms`，近似温暖运行时步进加速比约 `0.150x`、`0.200x` 和 `0.571x`。最新的静止/无导弹驻留后续工作现在还在设备载体内直接推进 `world_time_s`，以便覆盖的热路径可以完全跳过投影 H2D，随后的缓存图传递恢复来自该第一个直接内核版本的大部分增加的启动开销。稳定的重新运行矩阵现在稳定在约 `0.111 ms`、`0.096 ms` 和 `0.099 ms` 的温暖运行时步进时间，温暖链总计接近 `0.078 ms`、`0.079 ms` 和 `0.082 ms`，保持温暖写回、`chain_command_lane_ms` 和 `chain_host_to_device_ms` 为 `0.0`，并测量近似温暖运行时步进加速比约 `0.121x`、`0.193x` 和 `0.466x`。实验性运行时路径仍然不具备推广条件：剩余的阻塞因素现在更明确地是相对于 CPU 的运行时减速以及固定的重放/运行时粘合剂成本，而不是写回负担或 H2D 物化。

检查清单：

- [ ] 不要将 `step_packed_flight_states_experiment_batch(...)` 作为 `WorldBatchRuntime.step_batch()` 的隐藏替代品连接到维护的确切 `p5` 路径中。
- [ ] 如果确切的 GPU 世界步进成为目标，首先针对当前的 ECS 仿真核心定义确切的状态等价边界。
- [ ] 仅在该等价边界明确后，`WorldBatchRuntime` 才应获得可选的 GPU 世界步进后端。

主要文件：

- [src/core/engine/world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- [src/core/engine/simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp)
- [src/core/engine/world_batch_runtime.h](../../../../../src/core/engine/world_batch_runtime.h)
- [src/gpu/README.md](../../../../../src/gpu/README.md)
- [src/gpu/experimental/README.md](../../../../../src/gpu/experimental/README.md)
- [tests/gpu/test_gpu_runtime_bindings.py](../../../../../tests/gpu/test_gpu_runtime_bindings.py)

验收标准：

- 相对于确切 ECS 步进存在固定种子等价，而不仅仅是打包的 Phase-4 参考
- 回滚/回退到当前 CPU 确切路径仍然简单

## 推荐的首个代码目标

在文档/配置清理之后，第一个实际的加速集成目标应该是：

1. GPU 飞行塑形主线集成
2. 训练端设备驻留张量导出
3. 只有在那之后才重新考虑更广泛的 GPU 观察默认值

这个顺序与当前证据一致：

- 视觉已经有维护的运行时消费者
- 单独的 `gpu_host` 观察在当前维护的批量大小下不是强烈的生产胜利
- 飞行塑形是下一个具有实际算术密度的已实现内核
- 确切的 GPU 世界步进仍然存在与 ECS 核心的语义差距

## 护栏

- 不要用其他引擎替换模拟器。
- 不要将仅用于探测的二进制提升为“主线完整”状态。
- 在确切等价存在之前，不要将维护的确切 `p5` rollout 切换到 Phase-4 的打包飞行步进。
- 在零拷贝消费者路径存在之前，不要花更多时间优化主机回读观察打包。
