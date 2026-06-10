<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/architecture/src_layered_refactor_freeze.md. Review before treating this file as authoritative. -->

# `src/` 分层重构冻结计划

状态：`2026-05-11` 冻结执行版本；`WP1` 至 `WP7` 已完成。
文档定位：

- 本文档冻结了 `src/` 结构一次重大但分阶段的重构。
- 本轮的目标是首先建立目录边界、职责文档和低风险拆分路径，而非立即重写运行时语义。
- 如果本文档被采纳为执行指令，则仅允许在本文列出的工作包范围内扩展开代码实现。
- 本文档不授权直接移动行为代码；除 README 和兼容性入口点外，代码拆分必须根据后续工作包依次执行并验证。

验证标准：当该计划涉及 Python 测试时，应默认使用仓库的虚拟环境执行，即 `./.venv/bin/python -m pytest`，且 `PYTHONPATH=build-workshop` 指向当前的 C++/nanobind 构建产物。不要将系统 Python 解释器作为最终验证标准。

## 1. 当前评估

`src/` 并非完全失控的单体，但已暴露出几个边界热点，未来将继续吸收复杂性：

1. `src/components/physics/action.h` 混合了飞行员动作、任务指令、任务命令、领导者意图、飞行员报告、遗留移动/动作命令和命令链接。
2. `src/core/engine/simulation_kernel.cpp` 同时处理 ECS 系统注册、生成 API、命令 API、武器发射、智能体观测、视觉观测和精确阶段库存。
3. `src/interfaces/python/python_module.cpp` 同时处理核心类型绑定、运行时/外观绑定、GPU 辅助绑定、DLPack 视图和诊断接口。
4. `src/core/mission/episode/execution_episode_controller.cpp` 已提取出细节辅助函数；后续风险在于任务运行时、回合控制器和控制器细节之间的目录边界是否保持清晰。
5. `src/components/systems` 和 `src/systems/systems` 命名过于宽泛，缺乏清晰的业务领域边界。
6. `src/gpu` 同时托管维护中的 GPU 辅助函数和实验性探测历史记录；尽管精确步骤旧代码已移除，目录职责仍需要明确。

这些问题的共同风险是，未来的开发会继续将新功能塞入“最方便”的大文件或宽泛目录，导致架构文档再次与代码实际脱节。

## 2. 目标分层

目标依赖方向：

```text
bindings/python
  -> runtime/facade
    -> core/batch
      -> core/sim
        -> systems
          -> models / components / content

accelerators/gpu
  -> core/mission 或 systems 数据包
  -> 不拥有仿真真值状态
```

目标目录语义：

- `components/`
  - 仅提供 ECS 数据组件和稳定的 DTO 类结构。
  - 不放置系统逻辑、运行时控制器或 Python 绑定辅助函数。
- `systems/`
  - Flecs 系统注册和每帧变异逻辑。
  - 仅消费 components / models / core 接口。
- `models/`
  - 可替换的模型实现，例如控制、传感器、环境、效果、制导。
- `core/`
  - C++ 运行时编排、仿真内核、批量运行时、任务/回合纯运行时。
- `runtime/facade/`
  - 维护的前端所依赖的类型化请求/结果边界。
- `interfaces/python` 或未来的 `bindings/python`
  - Python 暴露层，仅用于绑定和轻量转换，不拥有领域逻辑。
- `gpu` 或未来的 `accelerators/gpu`
  - 加速辅助函数和实验性探测，不拥有标准的世界步进语义。

## 3. 非目标

本轮不做以下事项：

- 重写物理模型或改变 `SimulationKernel::step()` 语义。
- 改变训练配置的默认运行时后端。
- 删除遗留命令界面。
- 强制将所有目录移动到最终目标结构。
- 一次性拆分 `ef_core` CMake 目标。
- 删除低级 Python 绑定。
- 引入新的 GPU 精确步骤主线。

本轮允许添加新的兼容性总括头文件和 README；允许进行保留行为的内联拆分、文件拆分和绑定分割。

## 4. 冻结的工作包

### WP1：建立 `src/` 层级 README 防护栏

目标：

- 为 `src/` 顶层和现有主要目录添加 README。
- 明确说明每个层允许包含什么、不得包含什么、依赖方向以及迁移说明。

主要文件：

- `src/README.md`
- `src/components/README.md`
- `src/systems/README.md`
- `src/core/README.md`
- `src/runtime/README.md`
- `src/interfaces/README.md`
- `src/gpu/README.md`
- `src/models/README.md`
- `src/content/README.md`

验证：

- README 覆盖现有主要层级。
- README 明确禁止继续将新的任务/命令类型塞入 `components/physics`。
- README 明确说明 Python 绑定层不得承载领域逻辑。

执行状态：

- 已完成：为 `src/` 下所有现有目录添加了 README。
- 已完成：为新目标目录 `components/command` 和 `components/tasking` 添加了 README。
- 未开始：行为代码移动、包含迁移和 CMake 目标拆分。

### WP2：拆分 `components/physics/action.h` 的目标边界

目标：

- 建立命令/任务目标目录和 README。
- 后续将 `action.h` 拆分为 `command` 和 `tasking` 头文件时，有明确的落地点。

目标结构：

```text
src/components/command/
  README.md
  pilot_action.h
  mission_command.h
  command_link.h
  legacy_command.h

src/components/tasking/
  README.md
  tasking_enums.h
  task_order.h
  leader_intent.h
  pilot_report.h
```

本轮代码拆分建议：

1. 先添加新的目标头文件，让旧的 `components/physics/action.h` 作为总括包含。
2. 然后逐步更新 C++ 包含路径为新路径。
3. 最后将 `action.h` 标记为兼容性头文件。

验证：

- 新目录 README 清晰描述命令/任务边界。
- 任何未来的新命令/任务组件都有新目录可归属。
- 旧的包含兼容期内不会打破现有的 Python 绑定或 C++ 编译。

执行状态：

- 已完成：添加了 `components/command/{pilot_action.h, mission_command.h, legacy_command.h, command_link.h}`。
- 已完成：添加了 `components/tasking/{tasking_enums.h, task_order.h, leader_intent.h, pilot_report.h}`。
- 已完成：`components/physics/action.h` 降级为兼容性总括包含。
- 已完成：`components/systems/comm.h` 不再拥有 `CommMsgType` / `PilotReport` 定义；它们现在由 `components/tasking/pilot_report.h` 提供。
- 已完成：`src` 下的主要代码不再直接包含 `components/physics/action.h`。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。

### WP3：拆分 `python_module.cpp` 的绑定分区

目标：

- 将 Python 绑定从单个 3000+ 行文件拆分为多个绑定单元。
- 仅拆分绑定结构，不改变暴露的 API 名称。

目标结构：

```text
src/interfaces/python/
  python_module.cpp
  bindings_core.cpp
  bindings_command.cpp
  bindings_episode.cpp
  bindings_runtime.cpp
  bindings_gpu.cpp
  binding_utils.h
```

验证：

- `python_module.cpp` 仅负责 `NB_MODULE` 聚合调用。
- 命令/任务类型绑定集中在 `bindings_command.cpp`。
- GPU 辅助函数 / DLPack 绑定集中在 `bindings_gpu.cpp`。
- 现有的 Python 运行时/外观测试通过。

执行状态：

- 已完成：添加了 `binding_utils.h` 和分区文件 `bindings_{command,core,episode,runtime,gpu}.cpp`。
- 已完成：`python_module.cpp` 缩减为 `NB_MODULE` 聚合入口，按顺序注册 `command -> core -> episode -> runtime -> gpu`。
- 已完成：`CMakeLists.txt` 将所有绑定单元整合到 `ef_py` 中。
- 已完成：更新了 `src/interfaces/python/README.md`，描述当前分区职责。
- 已验证：`cmake --build build-workshop --target ef_py -j2` 通过。
- 已验证：使用 `PYTHONPATH=build-workshop ./.venv/bin/python` 进行冒烟检查，显示 `RuntimeFacade`、`WorldBatchRuntime`、`SimulationKernel`、命令/任务类型和 GPU 辅助函数符号均可见。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py` 通过 —— `26 passed`。

### WP4：拆分 `SimulationKernel` 边界文件

目标：

- 保持 `SimulationKernel` 作为单一世界编排 API，但将其实现拆分为职责文件。

目标结构：

```text
src/core/engine/
  simulation_kernel.cpp              # 构造函数、重置、步进、模型注入
  simulation_kernel_systems.cpp      # ECS 组件/系统注册
  simulation_kernel_command_api.cpp
  simulation_kernel_observation_api.cpp
  simulation_kernel_visual_api.cpp
  simulation_kernel_weapon_api.cpp
  exact_stage_inventory.cpp
```

验证：

- `simulation_kernel.cpp` 不再承载观测/视觉/武器细节。
- 精确阶段库存移出内核的主实现。
- `SimulationKernel` 公共 API 不变。

执行状态：

- 已完成：`simulation_kernel.cpp` 缩小为构造函数/析构函数、模型注入、重置/步进、生成、数据库/环境配置。
- 已完成：添加了 `simulation_kernel_systems.cpp` 以托管 ECS 组件注册和系统注册顺序。
- 已完成：添加了 `simulation_kernel_command_api.cpp` 以托管遗留命令、命令链接、数字飞行员/任务和消息命令。
- 已完成：添加了 `simulation_kernel_observation_api.cpp`、`simulation_kernel_visual_api.cpp`、`simulation_kernel_weapon_api.cpp`。
- 已完成：添加了 `exact_stage_inventory.cpp`；精确阶段库存和跟踪辅助函数移出了主实现文件。
- 已完成：`CMakeLists.txt` 将 WP4 新的引擎实现单元整合到 `ef_core` 中。
- 已完成：更新了 `src/core/engine/README.md`，反映当前职责边界。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py tests/runtime/execution/test_execution_episode_batch_prepare.py tests/runtime/execution/test_execution_episode_controller.py tests/runtime/execution/test_execution_episode_state.py` 通过 —— `38 passed`。

### WP5：拆分 `ExecutionEpisodeController` —— 任务转换和分解

目标：

- 将控制器从“状态机 + JSON 解析器 + 转换规划器 + 奖励分解”拆分为可测试的辅助函数。

目标结构：

```text
src/core/mission/
  runtime/
  episode/
    execution_episode_controller.cpp
    detail/
      episode_transition_runtime.cpp
      episode_reward_breakdown.cpp
      mission_command_codec.cpp
```

验证：

- JSON 任务命令往返逻辑集中在编解码器中。
- 航点后/着陆转换逻辑集中在转换运行时中。
- 奖励分解摘要集中在分解辅助函数中。
- 控制器仅协调状态导入/导出、准备/评估/步进。

执行状态：

- 已完成：添加了 `mission_command_codec.{h,cpp}` 以集中处理任务命令 JSON 往返、航点实体化以及任务目标更新。
- 已完成：添加了 `episode_transition_runtime.{h,cpp}` 以集中处理路线引导目标更新、后航点过渡以及着陆过渡臂/向量更新。
- 已完成：添加了 `episode_reward_breakdown.{h,cpp}` 以集中处理奖励分解摘要和稳定的 JSON 输出。
- 已完成：`execution_episode_controller.cpp` 缩减为协调状态导入/导出、prepare/evaluate/step 以及运行时产品的应用。
- 已完成：`src/core/mission` 物理拆分为 `runtime/`、`episode/` 和 `episode/detail/`；根目录不再包含扁平化的 `.h/.cpp` 文件。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/execution/test_execution_episode_controller.py tests/runtime/execution/test_execution_episode_state.py tests/runtime/execution/test_execution_episode_batch_prepare.py tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py` 通过 — `45 passed`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/execution/test_execution_episode_controller.py tests/runtime/execution/test_execution_episode_state.py tests/runtime/execution/test_execution_episode_batch_prepare.py tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py tests/test_cuda_import_order.py tests/world_batch/test_world_batch_vec_env.py` 通过 — `71 passed, 8 subtests passed`。

### WP6：收紧外观模式逃生口

目标：

- 继续强制贯彻外观优先原则。
- `RuntimeFacade::runtime()` 保留用于兼容性，但不得成为新主线代码的依赖。

验证：

- README 和架构测试标记 `runtime()` 仅允许用于诊断/兼容性。
- 当添加新的主线功能时，必须首先设计外观请求/结果。

执行状态：

- 已完成：`RuntimeFacade::runtime()` 保留作为兼容性/诊断逃生口。
- 已完成：`WorldBatchVecEnv` 的主维护路径通过 `_RuntimeFacadeAdapter` 访问外观形 API；直接调用 `RuntimeFacade.runtime()` 仅在该适配器内允许。
- 已完成：`WorldBatchVecEnv` 主类不再缓存对 `_batch_runtime` / `_runtime_facade` 的原始句柄；ScenarioLoader 底层世界访问、遗留可视化回读和可视化批处理辅助均通过适配器方法。
- 已完成：架构测试禁止主维护类或新代码（适配器外部）直接调用 `RuntimeFacade.runtime()`、直接实例化 `ef_py.WorldBatchRuntime`、缓存原始运行时/外观句柄，或重新暴露 `.compat_runtime`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/runtime_facade` 通过 — `5 passed`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/runtime_facade tests/world_batch/test_world_batch_vec_env.py tests/runtime/facade/test_runtime_facade.py tests/test_cuda_import_order.py` 通过 — `36 passed`。

### WP7：CMake 目标拆分准备

目标：

- 目前不强制拆分目标，但使目录和文件边界支持未来的拆分。

候选目标顺序：

1. `ef_components`
2. `ef_models`
3. `ef_systems`
4. `ef_mission_runtime`
5. `ef_sim_core`
6. `ef_runtime_facade`
7. `ef_python_bindings`
8. `ef_gpu_helpers`

验证：

- 新的 README 应明确界定目标边界。
- 新文件的所有权不应跨越层形成反向依赖。
- CMake 不再添加无限制的“混合包”源文件。

执行状态：

- 已完成：添加 `src/runtime/contracts/` 作为后续 `ef_contracts` 目标的候选起点。
- 已完成：将 `WorldEntityRef`、世界设置分配、命令/任务分配以及 `WorldExecutionEpisodeStepRequest` 从 `world_batch_runtime.h` 提取到 `runtime/contracts/world_batch_contracts.h`。
- 已完成：`runtime_facade_types.h` 不再直接包含 `core/engine/world_batch_runtime.h`。
- 已完成：`RuntimeFacade` 公共头文件使用 `WorldBatchRuntime` 的前向声明和 `std::unique_ptr`；底层引擎所有者的完整定义仅在 `.cpp` 中包含。
- 已完成：添加架构检查，禁止 `runtime/contracts/*.h` 和 `runtime/facade/*_types.h` 包含 `core/engine/*`，并确认外观公共头文件不直接包含 `world_batch_runtime.h`。
- 已完成：`CMakeLists.txt` 已按未来目标边界拆分为 `EF_CORE_ENGINE_SOURCES`、`EF_CORE_MISSION_RUNTIME_SOURCES`、`EF_CORE_MISSION_EPISODE_SOURCES`、`EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`、`EF_CORE_MISSION_SOURCES`、`EF_RUNTIME_FACADE_SOURCES`、`EF_MODEL_DEFAULT_SOURCES`、`EF_CONTENT_SOURCES`、`EF_PYTHON_BINDING_SOURCES` 和 GPU 源文件组；`ef_core` / `ef_py` 目标不再扁平列出源文件。
- 已完成：添加 CMake 目标就绪性架构检查，防止 `ef_core` / `ef_py` 回退到无限制的源文件扁平化。
- 已完成：更新 `src/README.md`，包含 CMake 源文件组所有权规则。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/runtime_facade tests/architecture/build/test_cmake_target_readiness.py tests/world_batch/test_world_batch_vec_env.py tests/runtime/facade/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_cuda_import_order.py tests/test_gpu_runtime_bindings.py` 通过，`62 passed`。

## 5. 执行顺序

推荐顺序：

1. `WP1 + WP2`：首先建立目录文档和命令/任务目标边界。
2. `WP3`：拆分 Python 绑定文件，降低未来类型移动的成本。
3. `WP4`：拆分 `SimulationKernel` 实现文件。
4. `WP5`：拆分 Episode 控制器内部业务辅助。
5. `WP6`：添加架构测试并限制外观逃生口。
6. `WP7`：根据先前拆分的结果决定 CMake 目标拆分。

## 6. 冻结规则

- 任何跨层移动必须保持公共 API 兼容，除非创建单独的冻结文档。
- 所有兼容的伞头文件必须标注迁移目标。
- 新目录必须包含 README。
- 新核心类型必须首先确定其层级；不得为了包含方便而放置在旧的宽泛目录中。
- 新的 Python 绑定不得内联领域逻辑；必须先在 C++ 运行时/外观中形成 API。
- 新的 GPU 辅助不得更改规范的 CPU 真值路径，除非创建单独的确切后端冻结文档。

## 7. 未决问题

本计划在 `WP7` 处结束。以下问题保留作为下一个冻结计划的候选，不在本计划中进一步实施：

- 是否应将 `src/interfaces/python` 重命名为 `src/bindings/python`？
- 是否应将 `components/systems` 和 `systems/systems` 重命名为 `components/comm`、`systems/comm` 或 `components/platform`、`systems/platform`？
- 是否应在下一轮将 `core/engine` 重命名为 `core/sim`，以避免与外观/运行时引擎概念混淆？
- 是否应在下一轮将 `gpu` 重命名为 `accelerators/gpu`，使“GPU 辅助”和“核心运行时真值”之间的边界更清晰？
