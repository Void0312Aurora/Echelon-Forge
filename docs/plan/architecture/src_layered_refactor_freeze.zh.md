# `src/` 分层重构冻结计划

状态：`2026-05-11` 冻结执行版；`WP1` 至 `WP7` 已完成。
文档定位：

- 本文档冻结一次较大但分阶段执行的 `src/` 结构重构。
- 本轮目标是先建立目录边界、职责文档和低风险拆分路线，而不是立即重写 runtime 语义。
- 若本文档被采纳为执行单，代码实现只允许围绕本文列出的工作包展开。
- 本文档不授权直接移动行为性代码；除 README 与兼容入口外，代码拆分需要按后续工作包逐项执行和验收。

验证口径：本计划涉及 Python 测试时默认使用仓库虚拟环境执行，即 `./.venv/bin/python -m pytest`，并配合 `PYTHONPATH=build-workshop` 指向当前 C++/nanobind 构建产物。不要用系统 Python 解释器作为最终验收口径。

## 一、当前判断

`src/` 不是完全失控的单体，但已经出现几个会继续吸收复杂度的边界热点：

1. `src/components/physics/action.h` 混合了 pilot action、mission command、task order、leader intent、pilot report、legacy movement/action command 和 command link。
2. `src/core/engine/simulation_kernel.cpp` 同时承担 ECS 系统注册、spawn API、command API、weapon launch、agent observation、visual observation 和 exact-stage inventory。
3. `src/interfaces/python/python_module.cpp` 同时承担核心类型绑定、runtime/facade 绑定、GPU helper 绑定、DLPack 视图和诊断接口。
4. `src/core/mission/episode/execution_episode_controller.cpp` 已拆出 detail helper；后续风险转为 mission runtime、episode controller 与 controller detail 的目录边界是否继续清晰。
5. `src/components/systems` 与 `src/systems/systems` 命名过宽，缺少明确业务域边界。
6. `src/gpu` 同时承载维护中的 GPU helper 与实验探针历史，虽然 exact-step 旧线已移除，但目录职责仍需明确。

这些问题的共同风险是：后续开发会继续把新功能塞进“看起来最方便”的大文件或宽目录，导致架构文档与代码现实再次分叉。

## 二、目标分层

目标依赖方向：

```text
bindings/python
  -> runtime/facade
    -> core/batch
      -> core/sim
        -> systems
          -> models / components / content

accelerators/gpu
  -> core/mission or systems data packets
  -> no ownership of simulation truth state
```

目标目录语义：

- `components/`
  - ECS data-only components and stable DTO-like structs.
  - 不放系统逻辑，不放 runtime controller，不放 Python binding helper。
- `systems/`
  - Flecs system registration and per-frame mutation logic.
  - 只消费 components / models / core interfaces。
- `models/`
  - 可替换模型实现，如 control、sensor、environment、effects、guidance。
- `core/`
  - C++ runtime orchestration, simulation kernel, batch runtime, mission/episode pure runtime.
- `runtime/facade/`
  - 维护中前端依赖的 typed request/result 边界。
- `interfaces/python` 或后续 `bindings/python`
  - Python 暴露层，只做绑定和轻量转换，不拥有领域逻辑。
- `gpu` 或后续 `accelerators/gpu`
  - 加速 helper 和实验 probe，不拥有 canonical world-step 语义。

## 三、非目标

本轮不做：

- 重写物理模型或改变 `SimulationKernel::step()` 语义。
- 改变训练配置默认 runtime backend。
- 删除 legacy command surface。
- 强制移动所有目录到最终目标结构。
- 一次性拆分 `ef_core` CMake target。
- 删除低层 Python 绑定。
- 引入新的 GPU exact-step 主线。

本轮允许新增兼容 umbrella headers 和 README；允许做行为保持的 include 拆分、文件拆分和 binding 分段。

## 四、冻结工作包

### WP1：建立 `src/` 层级 README 护栏

目标：

- 给 `src/` 顶层和现有主要目录补 README。
- 明确每一层允许放什么、不允许放什么、依赖方向和迁移备注。

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

验收：

- README 覆盖现有主要层级。
- README 明确禁止把新 tasking/command 类型继续塞进 `components/physics`。
- README 明确 Python binding 层不能承载领域逻辑。

执行状态：

- 已完成：`src/` 现有目录均补充 README。
- 已完成：新增 `components/command` 与 `components/tasking` 目标目录 README。
- 未开始：行为性代码移动、include 迁移和 CMake target 拆分。

### WP2：拆分 `components/physics/action.h` 的目标边界

目标：

- 建立 command/tasking 目标目录和 README。
- 后续把 `action.h` 拆为 `command` 与 `tasking` 头文件时，有明确落点。

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

1. 先新增目标头文件并让旧 `components/physics/action.h` 作为 umbrella include。
2. 再逐步更新 C++ include 到新路径。
3. 最后把 `action.h` 标注为 compatibility header。

验收：

- 新目录 README 写清 command/tasking 边界。
- 后续任何新增 command/tasking component 都有新目录归属。
- 旧 include 兼容期不破坏现有 Python binding 和 C++ 编译。

执行状态：

- 已完成：新增 `components/command/{pilot_action.h, mission_command.h, legacy_command.h, command_link.h}`。
- 已完成：新增 `components/tasking/{tasking_enums.h, task_order.h, leader_intent.h, pilot_report.h}`。
- 已完成：`components/physics/action.h` 降级为 compatibility umbrella include。
- 已完成：`components/systems/comm.h` 不再拥有 `CommMsgType` / `PilotReport` 定义，改由 `components/tasking/pilot_report.h` 提供。
- 已完成：`src` 主代码不再直接 include `components/physics/action.h`。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。

### WP3：拆 `python_module.cpp` 的绑定分区

目标：

- 把 Python 绑定从一个 3000+ 行文件拆成若干 binding unit。
- 只拆绑定结构，不改暴露 API 名称。

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

验收：

- `python_module.cpp` 只负责 `NB_MODULE` 聚合调用。
- command/tasking 类型绑定集中到 `bindings_command.cpp`。
- GPU helper / DLPack 绑定集中到 `bindings_gpu.cpp`。
- 现有 Python runtime/facade tests 通过。

执行状态：

- 已完成：新增 `binding_utils.h` 和 `bindings_{command,core,episode,runtime,gpu}.cpp` 分区文件。
- 已完成：`python_module.cpp` 缩减为 `NB_MODULE` 聚合入口，按 `command -> core -> episode -> runtime -> gpu` 顺序注册。
- 已完成：`CMakeLists.txt` 将所有 binding unit 接入 `ef_py`。
- 已完成：`src/interfaces/python/README.md` 更新为当前分区职责说明。
- 已验证：`cmake --build build-workshop --target ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python` 冒烟检查 `RuntimeFacade`、`WorldBatchRuntime`、`SimulationKernel`、command/tasking 类型和 GPU helper 符号均可见。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py` 通过，`26 passed`。

### WP4：拆 `SimulationKernel` 边界文件

目标：

- 保留 `SimulationKernel` 作为单 world orchestration API，但把实现拆成职责文件。

目标结构：

```text
src/core/engine/
  simulation_kernel.cpp              # constructor, reset, step, model injection
  simulation_kernel_systems.cpp      # ECS component/system registration
  simulation_kernel_command_api.cpp
  simulation_kernel_observation_api.cpp
  simulation_kernel_visual_api.cpp
  simulation_kernel_weapon_api.cpp
  exact_stage_inventory.cpp
```

验收：

- `simulation_kernel.cpp` 不再承载 observation/visual/weapon 细节。
- exact-stage inventory 从 kernel 主实现中移出。
- `SimulationKernel` public API 不变。

执行状态：

- 已完成：`simulation_kernel.cpp` 收缩为 constructor/destructor、model injection、reset/step、spawn、database/environment configuration。
- 已完成：新增 `simulation_kernel_systems.cpp` 承载 ECS component registration 和系统注册顺序。
- 已完成：新增 `simulation_kernel_command_api.cpp` 承载 legacy command、command link、digital pilot/tasking 和 message command。
- 已完成：新增 `simulation_kernel_observation_api.cpp`、`simulation_kernel_visual_api.cpp`、`simulation_kernel_weapon_api.cpp`。
- 已完成：新增 `exact_stage_inventory.cpp`，exact-stage inventory 与 trace helpers 已从主实现文件移出。
- 已完成：`CMakeLists.txt` 将 WP4 新增 engine implementation units 接入 `ef_core`。
- 已完成：`src/core/engine/README.md` 更新为当前职责边界。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py` 通过，`38 passed`。

### WP5：拆 `ExecutionEpisodeController` 的 mission transition 与 breakdown

目标：

- 把 controller 从“状态机 + JSON parser + transition planner + reward breakdown”拆成可测 helper。

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

验收：

- JSON mission command round-trip 逻辑集中在 codec。
- post-waypoint / landing transition 逻辑集中在 transition runtime。
- reward breakdown 汇总集中在 breakdown helper。
- controller 只协调 state import/export、prepare/evaluate/step。

执行状态：

- 已完成：新增 `mission_command_codec.{h,cpp}`，集中 mission-command JSON round-trip、route waypoint materialization 和 mission target 更新。
- 已完成：新增 `episode_transition_runtime.{h,cpp}`，集中 route guidance target 更新、post-waypoint transition 和 landing transition arm/vector 更新。
- 已完成：新增 `episode_reward_breakdown.{h,cpp}`，集中 reward breakdown 汇总和稳定 JSON 输出。
- 已完成：`execution_episode_controller.cpp` 收缩为 state import/export、prepare/evaluate/step 与 runtime products apply 的协调职责。
- 已完成：`src/core/mission` 物理拆为 `runtime/`、`episode/` 和 `episode/detail/`，根目录不再承载平铺 `.h/.cpp`。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py` 通过，`45 passed`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py tests/test_cuda_import_order.py tests/world_batch/test_world_batch_vec_env.py` 通过，`71 passed, 8 subtests passed`。

### WP6：收紧 facade 逃逸口

目标：

- 继续执行 facade-first 原则。
- `RuntimeFacade::runtime()` 保留 compatibility，但不得成为新主线代码依赖。

验收：

- README 和架构测试标注 `runtime()` 只允许 diagnostics / compatibility。
- 新增主线能力时必须先设计 facade request/result。

执行状态：

- 已完成：`RuntimeFacade::runtime()` 已保留为 compatibility / diagnostics escape hatch。
- 已完成：`WorldBatchVecEnv` 维护中主路径通过 `_RuntimeFacadeAdapter` 访问 facade-shaped API，直接 `RuntimeFacade.runtime()` 调用只允许集中在该 adapter 内。
- 已完成：`WorldBatchVecEnv` 主类不再缓存 `_batch_runtime` / `_runtime_facade` 裸句柄，ScenarioLoader 低层 world 访问、legacy visual readback 和 visual batch helper 均通过 adapter 方法集中。
- 已完成：架构测试禁止维护中主类或新代码在 adapter 之外直接调用 `RuntimeFacade.runtime()`、直接实例化 `ef_py.WorldBatchRuntime`、缓存 raw runtime/facade 句柄或重新暴露 `.compat_runtime`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py` 通过，`5 passed`。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/world_batch/test_world_batch_vec_env.py tests/runtime/test_runtime_facade.py tests/test_cuda_import_order.py` 通过，`36 passed`。

### WP7：CMake target 拆分准备

目标：

- 暂不强拆 target，但使目录与文件边界支持后续拆分。

候选 target 顺序：

1. `ef_components`
2. `ef_models`
3. `ef_systems`
4. `ef_mission_runtime`
5. `ef_sim_core`
6. `ef_runtime_facade`
7. `ef_python_bindings`
8. `ef_gpu_helpers`

验收：

- 新 README 明确 target 边界。
- 新文件归属不跨层反向依赖。
- CMake 不再新增无边界的“大杂烩”源文件。

执行状态：

- 已完成：新增 `src/runtime/contracts/`，作为后续 `ef_contracts` target 的候选起点。
- 已完成：将 `WorldEntityRef`、world setup assignments、command/tasking assignments 和 `WorldExecutionEpisodeStepRequest` 从 `world_batch_runtime.h` 抽入 `runtime/contracts/world_batch_contracts.h`。
- 已完成：`runtime_facade_types.h` 不再直接包含 `core/engine/world_batch_runtime.h`。
- 已完成：`RuntimeFacade` public header 使用 `WorldBatchRuntime` 前置声明和 `std::unique_ptr`，底层 engine owner 的完整定义只在 `.cpp` 中包含。
- 已完成：新增 architecture 检查，禁止 `runtime/contracts/*.h` 与 `runtime/facade/*_types.h` include `core/engine/*`，并确认 facade public header 不直接 include `world_batch_runtime.h`。
- 已完成：`CMakeLists.txt` 已按未来 target 边界拆出 `EF_CORE_ENGINE_SOURCES`、`EF_CORE_MISSION_RUNTIME_SOURCES`、`EF_CORE_MISSION_EPISODE_SOURCES`、`EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`、`EF_CORE_MISSION_SOURCES`、`EF_RUNTIME_FACADE_SOURCES`、`EF_MODEL_DEFAULT_SOURCES`、`EF_CONTENT_SOURCES`、`EF_PYTHON_BINDING_SOURCES` 和 GPU source groups；`ef_core` / `ef_py` target 不再直接平铺源码文件。
- 已完成：新增 CMake target readiness architecture 检查，防止 `ef_core` / `ef_py` 重新回到无边界源码平铺。
- 已完成：`src/README.md` 补充 CMake source group 归属规则。
- 已验证：`cmake --build build-workshop --target ef_core ef_py -j2` 通过。
- 已验证：`PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_cmake_target_readiness.py tests/world_batch/test_world_batch_vec_env.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_cuda_import_order.py tests/test_gpu_runtime_bindings.py` 通过，`62 passed`。

## 五、执行顺序

推荐顺序：

1. `WP1 + WP2`：先建立目录文档和 command/tasking 目标边界。
2. `WP3`：拆 Python binding 文件，降低后续类型移动成本。
3. `WP4`：拆 `SimulationKernel` 实现文件。
4. `WP5`：拆 episode controller 内部业务 helper。
5. `WP6`：补架构测试，限制 facade escape hatch。
6. `WP7`：根据拆分结果再决定 CMake target 拆分。

## 六、冻结规则

- 任何跨层移动必须保持 public API 兼容，除非另起冻结文档。
- 所有兼容 umbrella header 都必须标注迁移目标。
- 新增目录必须同时新增 README。
- 新增核心类型必须先判断归属层级，不允许因为 include 方便而放进旧宽目录。
- 新增 Python binding 不允许内联领域逻辑；需要先在 C++ runtime / facade 中形成 API。
- 新增 GPU helper 不允许改变 canonical CPU truth path，除非另起 exact backend 冻结文档。

## 七、开放问题

本计划到 `WP7` 已关闭。以下问题保留为下一批冻结计划候选，不在本计划内继续实现：

- 是否将 `src/interfaces/python` 重命名为 `src/bindings/python`？
- `components/systems` 与 `systems/systems` 是否改名为 `components/comm`、`systems/comm` 或 `components/platform`、`systems/platform`？
- `core/engine` 是否在下一轮改名为 `core/sim`，避免和 facade/runtime engine 概念混淆？
- `gpu` 是否在下一轮改名为 `accelerators/gpu`，使“GPU helper”与“核心 runtime truth”边界更清楚？
