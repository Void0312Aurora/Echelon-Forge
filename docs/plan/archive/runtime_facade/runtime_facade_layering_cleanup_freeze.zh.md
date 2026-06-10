# Runtime Facade 分层清理与解耦冻结执行计划

文档导航：

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
- [runtime_facade_task_bootstrap_plan.zh.md](runtime_facade_task_bootstrap_plan.zh.md)

状态：`2026-05-10` 下一批候选冻结执行计划。  
文档定位：

- 本文档用于承接第一批 `runtime facade` 落地后的下一轮代码清理。
- 本轮目标不是新增加速能力，而是收紧边界、减少层间泄漏、让维护中的前端只依赖 facade。
- 若本文档被采纳为冻结执行单，本轮代码实现只允许围绕本文列出的 `WP1-WP7` 展开。

当前执行进展：

- [x] `WP1` facade API 稳定度分级已在 `RuntimeFacade::runtime()` 和 Python 绑定区块中标注。
- [x] `WP2` `WorldBatchVecEnv` 的 facade/direct runtime 分支已收敛到 `_RuntimeFacadeAdapter`，主类不再缓存 raw runtime/facade 句柄。
- [x] `WP3` 已新增 facade 级 `BatchWorldSetupRequest` / `BatchWorldSetupResult`，`scenario_runtime` 优先使用 typed setup request。
- [x] `WP4` 已新增 `ObservationBatchRequest`，`WorldBatchVecEnv` 状态读回优先走 facade observation packet。
- [x] `WP5` Python 绑定已标注 maintained facade surface 与 simulation compatibility surface。
- [x] `WP6` 已新增 `tests/architecture/runtime_facade` 作为依赖方向回归检查。
- [x] `WP7` target split readiness 已记录 include 阻塞、拆分顺序和进入下一批 target 拆分前的门槛；CMake 源码已按未来 target source groups 分组。

## 一、当前判断

第一批 facade 启动任务已经完成：

- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `WorldBatchVecEnv` 的 reset / step 主路径已开始 facade-first

但从当前代码看，facade 仍然更接近薄包装层，而不是稳定分层边界：

1. `RuntimeFacade` 仍公开 `runtime()`，但已经标注为 compatibility / diagnostics 逃逸口。
2. `WorldBatchVecEnv` 的 facade 与 direct runtime fallback 已收敛到 `_RuntimeFacadeAdapter`，主类不再缓存 `_runtime_facade` / `_batch_runtime` 裸句柄。
3. `RuntimeFacade` 的公开接口仍大量一比一转发底层 `WorldBatchRuntime::*_batch` 方法。
4. `runtime_facade_types.h` 已不再直接包含 `world_batch_runtime.h`；facade-facing world-batch DTO 已先抽入 `runtime/contracts/world_batch_contracts.h`。
5. `python_module.cpp` 同时暴露低层 probe/runtime API 与维护中的 facade API，主线前端和诊断入口的稳定度没有区分。
6. `ef_core` 仍是大单体 target，构建边界暂时无法约束 contracts / facade / simulation / physics 的依赖方向。

因此下一步不应继续扩展 GPU helper、exact backend 或新训练功能；应先做一轮分层清理。

## 二、本轮目标

本轮目标是建立可验证的依赖方向：

`WorldBatchVecEnv / UniversalEnv -> RuntimeFacade -> WorldBatchRuntime -> SimulationKernel`

并且让维护中的前端不再直接依赖：

- `WorldBatchRuntime` 的主线 batch step / setup / readback 方法
- `SimulationKernel` 的低层实体和组件读写
- `python_module.cpp` 中仅供 probe / diagnostics 使用的接口

本轮完成后，下一轮才能更安全地推进：

- observation / reward / info 合同深化
- device-view / DLPack facade 出口
- resident-state 或 exact backend 切换位
- CMake target 级拆分

## 三、非目标

本轮不做：

- exact GPU backend 主线切换
- resident-state 主线接入
- `ScenarioLoader` 全量重写
- 物理引擎独立 target 的完整拆分
- 删除所有低层 Python 绑定
- 改变维护中 `p5` 的默认后端选择

低层 API 可以继续存在，但必须被标记为 diagnostics / compatibility surface，而不是维护中前端的依赖面。

## 四、冻结工作包

### WP1：定义 facade API 稳定度分级

目标：

- 在文档和代码注释中区分 maintained facade API、compatibility API、diagnostics API。
- 明确 `RuntimeFacade::runtime()` 只能作为临时 compatibility escape hatch，不能作为维护中前端依赖。

主要文件：

- [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h)
- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)

验收：

- 文档列出 facade API 稳定度。
- 代码中所有 escape hatch 都有明确命名或注释。

### WP2：收敛 `WorldBatchVecEnv` 的 runtime 访问路径

目标：

- 让维护中的 `WorldBatchVecEnv` 主路径只通过 `RuntimeFacade` 访问 batch runtime 能力。
- 将 direct `WorldBatchRuntime` fallback 收敛到一个兼容适配点，而不是散落在 step/reset/readback 辅助函数里。

主要文件：

- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

建议实现：

- 增加一个内部 `_RuntimeFacadeAdapter` 或等价薄适配对象。
- `WorldBatchVecEnv` 内部只调用 adapter 方法。
- adapter 内部可以临时处理 facade / legacy runtime fallback。

验收：

- `WorldBatchVecEnv` 主体代码不再到处判断 `_runtime_facade is not None`。
- `WorldBatchVecEnv` 主体代码不再直接调用 `_batch_runtime.*_batch` 主线方法。
- 现有 world-batch 测试保持通过。

### WP3：补齐 facade 级 setup / reset request

目标：

- 不再让前端通过多个并列数组直接调用 `apply_world_setup_batch(...)`。
- 增加 facade 级 typed request，使 world setup 成为 facade 合同的一部分。

候选类型：

- `BatchWorldSetupRequest`
- `BatchWorldSetupResult`

主要文件：

- [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h)
- [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h)
- [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp)
- [scenario_runtime.py](../../../python/scenario_runtime.py)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

验收：

- `load_compiled_scenario_batch(...)` 可对 `RuntimeFacade` 使用 typed setup request。
- 旧的并列数组入口保留为 compatibility API，但维护中路径改走 typed request。

### WP4：收敛 observation / state readback 合同

目标：

- 让前端通过 facade 级 `ObservationBatchPacket` 或 request/result 获取 readback，而不是分别调用多个底层 getter。
- 为后续 device-view / partial-sync 留出合同位置。

候选类型：

- `ObservationBatchRequest`
- 扩展后的 `ObservationBatchPacket`

主要文件：

- [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h)
- [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

验收：

- `_read_truth_and_inst_by_refs(...)` 走 facade packet。
- execution controller mainline step 结果与 observation packet 的组合路径有测试覆盖。
- 不改变现有 observation 数值语义。

### WP5：隔离主线绑定与诊断绑定

目标：

- `python_module.cpp` 中保留低层绑定，但把维护中 facade 绑定和 diagnostics / probe 绑定分段清晰。
- 为后续拆文件或拆 target 做准备。

主要文件：

- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)

验收：

- 绑定文件中的 facade 区块、simulation compatibility 区块、diagnostics 区块清晰分离。
- 新增或更新测试，确保维护中 `WorldBatchVecEnv` 不依赖 `ef_py.WorldBatchRuntime` 作为主路径能力探测对象。

### WP6：增加依赖方向回归检查

目标：

- 用轻量测试保护本轮分层清理成果。

建议检查：

- `python/rl/world_batch_vec_env.py` 不直接实例化 `ef_py.WorldBatchRuntime`，除非位于兼容适配点。
- 维护中的前端不调用 `RuntimeFacade.runtime()`。
- facade public header 中的新增 DTO 不继续扩大对 engine 内部头的直接依赖。

主要文件：

- 新增 `tests/architecture/runtime_facade`
- 或并入 [tests/runtime/facade/test_runtime_facade.py](../../../tests/runtime/facade/test_runtime_facade.py)

验收：

- 架构检查能在普通 pytest 中运行。
- 检查失败信息能指向具体违规文件和符号。

### WP7：记录下一轮 target 拆分前置条件

目标：

- 不在本轮强拆 `ef_core`，但记录下一轮 CMake target 拆分的最小前置条件。

候选 target 顺序：

1. `ef_contracts`
2. `ef_mission_runtime`
3. `ef_simulation_engine`
4. `ef_runtime_facade`
5. `ef_models_default`

验收：

- 本轮结束时新增一段 target split readiness 记录。
- 记录当前仍阻止 target 拆分的 include 依赖。

当前记录：

- 当前 `ef_core` 仍同时编译 engine、mission runtime、facade、content loader 和 default model sources。
- 已新增 `src/runtime/contracts/`，并将 `WorldEntityRef`、world setup assignments、command/tasking assignments 和 `WorldExecutionEpisodeStepRequest` 从 `world_batch_runtime.h` 抽入 `runtime/contracts/world_batch_contracts.h`。
- `runtime_facade_types.h` 已不再直接包含 `core/engine/world_batch_runtime.h`。
- `runtime_facade.h` 通过前置声明和 `std::unique_ptr<WorldBatchRuntime>` 隐藏底层 engine owner；完整 `world_batch_runtime.h` include 仅保留在 `runtime_facade.cpp`。
- `world_batch_runtime.h` 直接包含 `simulation_kernel.h`、`execution_episode_controller.h`、observation 和 physics action/instrument component headers。
- `simulation_kernel.h` 直接包含 component headers、`unit_data.h`、`observation.h`，并在 `.cpp` 中聚合 physics / systems / combat / visual systems 与 default unit factory。
- `python_module.cpp` 仍是宽绑定层，同时包含 facade、simulation runtime、mission runtime、GPU helper、models snapshot 和 component headers。
- `CMakeLists.txt` 已用 `EF_CORE_ENGINE_SOURCES`、`EF_CORE_MISSION_SOURCES`、`EF_RUNTIME_FACADE_SOURCES`、`EF_MODEL_DEFAULT_SOURCES`、`EF_CONTENT_SOURCES`、`EF_PYTHON_BINDING_SOURCES` 和 GPU source groups 表达未来 target 边界。

因此下一批不能直接把 `ef_runtime_facade` 单独抽出来。必须先降低 facade public header 对 engine public header 的依赖。

最小拆分前置条件：

1. 已完成：将 facade-facing DTO 从 `WorldBatchRuntime` 头中分离出来，覆盖：
   - `WorldEntityRef`
   - world setup assignments / spawn request
   - execution episode step request
2. 已完成：让 `runtime_facade_types.h` 不直接包含 `world_batch_runtime.h`。
3. 将 `WorldBatchRuntime` 内部依赖 `SimulationKernel` 的 API 保留在 simulation engine target 内，facade 只通过 `.cpp` 包装它。
4. 将 `python_module.cpp` 的绑定区块至少按文件或 include group 预拆：
   - facade bindings
   - simulation compatibility bindings
   - mission runtime bindings
   - diagnostics / GPU helper bindings
5. target 拆分前必须保留当前通过的测试集合，避免拆分过程中混入语义变更。
6. 已完成：用 architecture 检查约束 `ef_core` 和 `ef_py` 只消费分组 source variables，不再直接平铺源码。

推荐 target 拆分顺序：

1. `ef_contracts`
   - 内容：纯 DTO / enum / small value types。
   - 第一批候选：facade DTO、mission runtime DTO、`WorldEntityRef` 和 world setup request。
   - 不应链接 Flecs、nanobind、CUDA 或 model implementation。
2. `ef_mission_runtime`
   - 内容：`src/core/mission/*` 中不依赖 `SimulationKernel` 的 runtime evaluation。
   - 当前可行性较高，但要先确认每个 mission header 不反向包含 engine header。
3. `ef_simulation_engine`
   - 内容：`SimulationKernel`、`WorldBatchRuntime`、geometry runtime、systems orchestration。
   - 继续链接 Flecs、models interfaces 和 default model implementations。
4. `ef_runtime_facade`
   - 内容：`RuntimeFacade`。
   - 依赖 `ef_contracts` 和 `ef_simulation_engine`，但 public header 只暴露 `ef_contracts`。
5. `ef_models_default`
   - 内容：default control / sensor / environment / effects / guidance / unit factory。
   - 当前 `SimulationKernel` 仍直接使用 default unit factory，因此这一步应晚于 simulation engine 边界整理。

不建议的拆分方式：

- 不要先拆 `ef_runtime_facade` target。当前 facade public header 还会把 engine header 泄漏给调用者。
- 不要先拆 physics engine target。当前 physics systems 由 `SimulationKernel` 直接注册和调度，接口边界尚未形成。
- 不要在 target 拆分同时推进 exact GPU 或 resident-state。那会混淆构建边界问题和 backend 语义问题。

本轮已落地的最小 target 准备：

- 新建 `src/runtime/contracts/` 目录。
- 将 facade-facing DTO 从 `world_batch_runtime.h` 搬入 `runtime/contracts/world_batch_contracts.h`。
- 让 `runtime_facade_types.h` 不再包含 `world_batch_runtime.h`。
- 新增 architecture 检查，禁止 `runtime/contracts/*.h` 和 `runtime/facade/*_types.h` include `core/engine/*`。
- 新增 architecture 检查，禁止 `ef_core` / `ef_py` target 重新直接平铺源码文件。
- 暂不改 CMake target，仅用 include 方向检查验证 contracts 抽离。

## 五、推荐执行顺序

1. `WP1`
2. `WP2`
3. `WP3`
4. `WP4`
5. `WP5`
6. `WP6`
7. `WP7`

其中 `WP2-WP4` 是本轮核心；`WP5-WP7` 用来防止清理成果再次漂移。

## 六、验证集合

最低回归集合：

```bash
CMO_BUILD_DIR=build-facade-local \
LD_LIBRARY_PATH=/home/void0312/Workshop/CMO/build-facade-local/_deps/flecs-build:/home/void0312/Workshop/CMO/build-facade-local \
./.venv/bin/python -m pytest \
  tests/runtime/facade/test_runtime_facade.py \
  tests/runtime/execution/test_execution_episode_controller.py \
  tests/runtime/execution/test_execution_episode_state.py \
  tests/runtime/execution/test_execution_episode_batch_prepare.py \
  tests/world_batch/test_world_batch_runtime.py \
  tests/world_batch/test_world_batch_vec_env.py
```

若新增 architecture 检查：

```bash
./.venv/bin/python -m pytest tests/architecture/runtime_facade
```

## 七、完成标准

本轮完成时必须同时满足：

1. `WorldBatchVecEnv` 维护中主路径只依赖 facade 或 facade adapter。
2. `RuntimeFacade::runtime()` 不再被维护中前端主类调用；迁移期只能集中在显式 compatibility adapter 内。
3. world setup 与 observation readback 至少各有一个 facade 级 typed request/result 入口。
4. 低层 `WorldBatchRuntime` Python 绑定仍可用于 diagnostics，但不再作为维护中前端的主依赖。
5. 回归测试通过，并新增一条依赖方向检查。
6. 没有改变 maintained `p5` 的默认 execution / visual / observation backend。

## 八、后续衔接

本轮 `WP1-WP7` 已收尾。后续任务需要另起冻结计划，不继续挂在本文档执行。

本轮完成后，下一批任务再选择以下之一单独冻结：

- facade 级 device observation view
- host observation return contract 深化
- resident-state / exact backend facade switch
- `ef_core` target 拆分
- `ScenarioLoader` episode ownership 进一步下沉

这些后续方向不属于本轮实现范围。
