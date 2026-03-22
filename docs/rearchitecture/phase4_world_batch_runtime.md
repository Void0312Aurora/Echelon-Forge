# [ARCHIVED] Phase 4: World Batch Runtime

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中出现的“进行中”“下一刀”“后续应该继续做”等表述均为归档前语境，不再构成当前任务清单。

状态：Archive。原记录为进行中，但该路线已于 2026-03-22 统一停止并归档；最后记录日期为 2026-03-22。

## 1. 本阶段目的

Phase 1 到 Phase 3 已经分别把：

- 场景几何热路径
- 场景解释 / instantiate
- mission observation / reward / termination helper

从 `ScenarioLoader` 的 Python 主链里剥离出来了。

但真正决定并行训练吞吐上限的一个核心缺口仍然存在：

- C++ 内核仍按“单 world 单接口”暴露
- Python 仍需要逐 env 调 `step() / get_*() / set_*()`
- 现有所谓 batch 仍主要是 Python 侧 batched inference，而不是 world runtime batch

因此 Phase 4 的目标不是再加一个新的 vec-env 包装，而是先在 C++ 内部建立真正的 `WorldBatchRuntime`，给后续：

- `CompiledScenario` 批量实例化
- `UniversalEnv`/训练入口适配
- leader/execution 多速率统一 runtime

提供稳定落点。

## 2. 本阶段当前范围

Phase 4 目前分三刀推进：

第一刀：

1. 一个持有多份 `SimulationKernel` 的 runtime 容器
2. batch reset / step / time-step / database broadcast
3. batch command-chain 写入接口
4. batch observation / instrument / command-chain 读取接口
5. Python 绑定、低层回归测试、诊断 benchmark

第二刀：

1. 给 `WorldBatchRuntime` 增加 batch setup surface
2. 把 compiled scenario 的 world setup 逻辑抽成共享 runtime helper
3. 让单 world `ScenarioLoader` 和 batch runtime 共用同一套 kernel apply 语义
4. 补单 world / batch world 一致性回归
5. 把 benchmark 拆成 `kernel apply` 和 `step/read` 两个口径

第三刀：

1. 新增 execution-layer `WorldBatchVecEnv`
2. 让训练入口能直接消费 `WorldBatchRuntime`
3. 给 batch vec env 补 reset / step / auto-reset / curriculum override 主链
4. 补训练 adapter 的单测与 wall-clock benchmark
5. 明确第一版 guardrail：仅支持 non-visual、无 action wrapper 的 execution 训练

也就是说，这一刀主要解决的是：

- runtime ownership
- batch API 形状
- Python/C++ 边界收口

当前仍没有解决：

- 真正的 batched world stepping
- C++ 内批量场景实例化 / 共享静态 runtime
- visual / wrapper / leader 路径对 `WorldBatchRuntime` 的采用

本阶段截至 2026-03-22 的结论已经很明确：

- rollout 主链收益稳定存在
- reset 主链仍然没有稳定拉出噪声区
- 因此 Phase 4 不应继续停留在 Python reset 微调，而应把重心转到 Phase 5 的 leader / execution ownership 拆分

## 3. 本次已落地内容

### 3.1 新增 C++ `WorldBatchRuntime`

文件：

- [world_batch_runtime.h](/home/void0312/CMO/src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](/home/void0312/CMO/src/core/engine/world_batch_runtime.cpp)

第一刀当前能力：

- 持有 `std::vector<std::unique_ptr<SimulationKernel>>`
- `resize(world_count)`
- `world(index)` 访问单 world
- `reset_batch(seeds)`
- `step_batch()`
- `load_database(path)`
- `load_unit_definitions(path, error)`
- `set_time_step(dt)`

批量写入接口：

- `set_pilot_actions_batch()`
- `set_mission_commands_batch()`
- `set_task_orders_batch()`
- `set_leader_intents_batch()`
- `set_pilot_reports_batch()`

批量读取接口：

- `get_agent_observations_batch()`
- `get_instrument_states_batch()`
- `get_mission_commands_batch()`
- `get_task_orders_batch()`
- `get_leader_intents_batch()`
- `get_pilot_reports_batch()`

### 3.2 新增 batch setup / assignment 结构

文件：

- [world_batch_runtime.h](/home/void0312/CMO/src/core/engine/world_batch_runtime.h)

已新增：

- `WorldEntityRef`
- `WorldTerrainAssignment`
- `WorldWindAssignment`
- `WorldZoneDefinition`
- `WorldSpawnRequest`
- `WorldPilotActionAssignment`
- `WorldMissionCommandAssignment`
- `WorldTaskOrderAssignment`
- `WorldLeaderIntentAssignment`
- `WorldPilotReportAssignment`

这些对象的作用是把“哪个 world 的哪类 setup/state 操作”显式化，避免 Python 继续以隐式循环方式调散碎 `set_* / add_zone / spawn_unit`。

### 3.3 `WorldBatchRuntime` 已补 batch setup surface

文件：

- [world_batch_runtime.h](/home/void0312/CMO/src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](/home/void0312/CMO/src/core/engine/world_batch_runtime.cpp)

第二刀新增：

- `set_terrain_types_batch()`
- `set_winds_batch()`
- `clear_zones_batch()`
- `add_zones_batch()`
- `spawn_units_batch()`

这意味着 Phase 4 不再只有“step/read/write”的 batch API，也开始覆盖 reset/setup 主链里最常见的 kernel surface。

### 3.4 新增共享 scenario runtime apply helper

文件：

- [scenario_runtime.py](/home/void0312/CMO/python/scenario_runtime.py)

已新增：

- `ScenarioWorldLayout`
- `AppliedScenarioWorld`
- `prepare_scenario_world_layout()`
- `apply_world_layout_to_kernel()`
- `build_compiled_world_layout()`
- `apply_world_layouts_to_batch()`
- `load_compiled_scenario_batch()`

作用：

- 把 world-yaw / wind / zone / spawn 这些 kernel setup 逻辑从 `ScenarioLoader` 内联代码中再剥一层出来
- 让单 world loader 和 batch runtime 共享同一套 compiled-scenario apply 语义
- 为后续真正的 batch reset / compiled runtime 奠定一致的 setup 边界

### 3.5 `ScenarioLoader` 已切到共享 setup helper

文件：

- [scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py)

本次改动：

- `_load_instantiated_scenario()` 不再自己内联执行 environment / wind / zones / spawn 主链
- loader 现在先调用 `prepare_scenario_world_layout()`，再通过 `apply_world_layout_to_kernel()` 完成 kernel setup
- loader 后续的 mission randomization、waypoint parse、command-chain reset、reward/runtime 状态机保持不变

这一步的意义是：Phase 4 不再是旁路的 batch 实验代码，而是已经开始触达并重用当前主链。

### 3.6 `SimulationKernel` 读取接口 const 化

文件：

- [simulation_kernel.h](/home/void0312/CMO/src/core/engine/simulation_kernel.h)
- [simulation_kernel.cpp](/home/void0312/CMO/src/core/engine/simulation_kernel.cpp)

为了支持 batch getter，以下接口已改成 `const`：

- `get_agent_observation()`
- `get_task_order()`
- `get_leader_intent()`
- `get_mission_command()`
- `get_pilot_report()`
- `get_world() const`

这一步本质上是在为后续：

- const runtime view
- 只读 batch observation API
- 更干净的并发/多 world 设计

做准备。

### 3.7 Python 绑定已接通

文件：

- [python_module.cpp](/home/void0312/CMO/src/interfaces/python/python_module.cpp)

已暴露：

- `WorldEntityRef`
- `WorldTerrainAssignment`
- `WorldWindAssignment`
- `WorldZoneDefinition`
- `WorldSpawnRequest`
- 各类 `World*Assignment`
- `WorldBatchRuntime`

其中 `WorldBatchRuntime` 目前支持：

- 构造 `WorldBatchRuntime(world_count=0)`
- `world_count()`
- `resize()`
- `world(index)`
- `reset_batch()`
- `step_batch()`
- `load_database()`
- `load_unit_definitions()`
- `set_time_step()`
- `set_terrain_types_batch()`
- `set_winds_batch()`
- `clear_zones_batch()`
- `add_zones_batch()`
- `spawn_units_batch()`
- 全部 batch read/write API

另外这次也显式把 `WorldBatchRuntime` 设成 move-only，避免 `nanobind` 对内部 `unique_ptr` 容器生成错误的 copy wrapper。

### 3.8 Phase 4 低层测试与 benchmark

文件：

- [test_world_batch_runtime.py](/home/void0312/CMO/tests/world_batch/test_world_batch_runtime.py)
- [benchmark_world_batch_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_world_batch_phase4.py)

测试覆盖：

- batch world reset / step
- batch observation / instrument readback
- command chain batch write/read roundtrip
- compiled scenario batch apply
- single-world loader 与 batch runtime 的 setup 一致性

benchmark 覆盖：

- legacy per-world kernel apply vs batch kernel apply
- legacy per-world step/read loop vs batch step/read loop

### 3.9 新增 execution-layer `WorldBatchVecEnv`

文件：

- [world_batch_vec_env.py](/home/void0312/CMO/python/rl/world_batch_vec_env.py)
- [universal_env.py](/home/void0312/CMO/gym_envs/universal_env.py)
- [train.py](/home/void0312/CMO/train.py)
- [test_world_batch_vec_env.py](/home/void0312/CMO/tests/world_batch/test_world_batch_vec_env.py)
- [benchmark_world_batch_vec_env_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_world_batch_vec_env_phase4.py)

第三刀当前能力：

- 新增基于 `WorldBatchRuntime` 的 single-process execution `VecEnv`
- `WorldBatchRuntime` 已新增 `worker_threads` 控制；默认值为 `1`，`0` 才表示 auto
- reset 主链优先走 compiled-scenario batch load；per-env override 或 auto-reset 则回退单 world materialization
- step 主链改为 batch `set_pilot_actions / step_batch / get_*_batch`，不再逐 env 调 `SimulationKernel.step()`
- `UniversalEnv` 的 action / observation / step-info 语义已通过共享 helper 复用，避免 batch adapter 另起一套口径
- `train.py` 已新增 `runtime.world_batch_vec_env` opt-in 入口
- batch reset / step 的 initial truth / instrument state 已改为“先批量取一次，再贯穿 loader finalize / observation build”
- command-chain 写回已从逐 world `set_*` 改成 `set_mission_commands_batch / set_task_orders_batch / set_leader_intents_batch / set_pilot_reports_batch`
- `route_ref_id` 已在 loader/leader tasking 主链中缓存，避免 reset/step 重复 hash 同一条航路
- `CompiledScenario` 已新增 `instantiate_runtime()`，runtime reset 只 clone可变分支，不再整份 materialize 只读树

当前 guardrail：

- 仅支持 execution-layer
- 仅支持 `include_visual = false`
- 仅支持无 action wrapper 的训练入口
- leader runtime 仍不走这条路径

### 3.10 新增 reusable batch apply buffer

文件：

- [scenario_runtime.py](/home/void0312/CMO/python/scenario_runtime.py)
- [world_batch_vec_env.py](/home/void0312/CMO/python/rl/world_batch_vec_env.py)
- [test_world_batch_runtime.py](/home/void0312/CMO/tests/world_batch/test_world_batch_runtime.py)

本次改动：

- 新增 `BatchWorldApplyBuffer`
- `apply_world_layouts_to_batch()` 和 `load_compiled_scenario_batch()` 已支持传入可复用 buffer
- `WorldBatchVecEnv.reset()` 现在复用同一批 `WorldTerrainAssignment / WorldWindAssignment / WorldZoneDefinition / WorldSpawnRequest`
- 这一步的目标不是改变 `SimulationKernel` stepping，而是减少 reset 主链里重复构造 Python batch descriptor 的成本

这意味着 Phase 4 的 reset 主链现在不再每次都重新分配整批 batch apply 对象，后续继续下沉 compiled runtime 时，这个边界可以直接保留下来。

### 3.11 重排 loader finalize / command-chain sync 顺序

文件：

- [scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py)
- [leader_tasking.py](/home/void0312/CMO/python/rl/leader_tasking.py)

本次改动：

- `ScenarioLoader._finalize_loaded_world()` 不再在 reset 时调用整条 `update_behaviors(0.0)` 主链
- reset 现在改成：
  - 先 randomize / parse waypoints
  - 再基于当前 world 提取 ILS beacon
  - 只 rebuild 一次 spatial geometry
  - 只应用一次初始 waypoint guidance
  - 再 reset command-chain
  - 最后只做一次 kernel sync
- `RuleBasedLeaderPhaseManager.reset/update()` 已显式接收 `sync_to_kernel`
- `loader._activate_post_waypoint_transition()` 也已接上这个同步语义，避免 batch path 被单 world `set_mission_command()` 旁路

这一步的意义不是“又做一个小缓存”，而是把 reset 时的 runtime state 计算顺序收回到更合理的 ownership 边界：先完成 Python runtime state 变更，再统一写回 kernel。

### 3.12 实验性 compiled layout template

文件：

- [scenario_compiler.py](/home/void0312/CMO/python/scenario_compiler.py)
- [scenario_runtime.py](/home/void0312/CMO/python/scenario_runtime.py)
- [test_world_batch_runtime.py](/home/void0312/CMO/tests/world_batch/test_world_batch_runtime.py)
- [benchmark_world_batch_phase4.py](/home/void0312/CMO/tools/diagnostics/benchmark_world_batch_phase4.py)

本次改动：

- `CompiledScenarioRuntimeMetadata` 已新增 `layout_template`
- compiler 现在会预编译 world layout 的静态部分：`time_step / terrain / wind / zones / spawns / env randomization / runway heading / wind_ref_alt_m`
- `scenario_runtime` 已补实验性 `use_compiled_template=True` 路径，并新增与 legacy layout build 的等价性回归
- `benchmark_world_batch_phase4.py` 已新增 `legacy layout build` vs `compiled layout build` 口径

当前结论：

- 语义上这条路径已经打通，compiled template build 与 legacy build 的 world yaw / wind / spawn 结果一致
- 但 benchmark 还没有显示正收益；当前 `compiled layout build` 仍慢于 `legacy layout build`
- 因此这条路径目前不挂生产主链，默认 reset 仍走 legacy `build_compiled_world_layout()`；保留这套 metadata 和 benchmark，是为了后续直接做 batch-direct materializer，而不是继续在 Python 对象层硬切换

## 4. 验证结果

### 4.1 构建与单测

已通过：

```bash
cmake --build build -j4

PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python -m unittest \
  tests.world_batch.test_world_batch_runtime \
  tests.world_batch.test_world_batch_vec_env \
  tests.scenario.test_scenario_compiler -v
```

当前回归覆盖了四类验证：

- `step_batch()` 后可批量读回 observation / instrument state
- command chain 的 `MissionCommand / TaskOrder / LeaderIntent / PilotReport` 可批量写回并按预期读回
- `load_compiled_scenario_batch()` 能对多 world 完成 compiled-scenario setup
- 同 seed 下，`ScenarioLoader` 与 batch runtime 的 world-yaw / spawn 结果一致
- `WorldBatchVecEnv` 可完成 reset / step / auto-reset / per-env randomization override 主链
- `BatchWorldApplyBuffer` 可在多次 `load_compiled_scenario_batch()` 间复用，不会破坏 entity 映射或 agent 读取

其中 `MissionCommand` 用例里显式把实体 `CommandLink` 置零，避免把命令链延迟仿真误判成 batch API 故障。

另外也已通过与这次入口替换直接相关的旧回归：

- `tests.scenario.test_scenario_compiler`
- `tests/contracts/env/mission_obs/mission_obs_nav_v2.json`
- `tests/contracts/bridges/takeoff_to_landing_scripted_bridge.json`

### 4.2 Phase 4 benchmark

命令：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark_world_batch_phase4.py \
  --json-out /tmp/phase4_world_batch_benchmark.json
```

结果：

- `scenario = scenarios/combined/takeoff_to_landing_continuous_train_v1.json`
- `world_count = 16`
- `worker_threads = 1`
- `legacy kernel apply = 4.729064 ms`
- `world batch kernel apply = 4.361030 ms`
- `kernel apply speedup = 1.08x`
- `legacy python loop = 0.474527 ms`
- `world batch runtime = 0.467723 ms`
- `step/read speedup = 1.01x`

补充线程口径：

- `worker_threads = 4` 时，`world batch runtime = 0.587226 ms`，`step/read speedup = 0.80x`
- `worker_threads = auto(16)` 时，`world batch runtime = 1.956338 ms`，`step/read speedup = 0.24x`

这说明当前 `SimulationKernel` 的单 world step 仍然太轻，盲目把 batch runtime 线程开到 world-count 只会把线程调度成本直接吃进热路径。

补充本次 `reuse_apply_buffer` 口径：

- `world_count = 16`
- `worker_threads = 1`
- `legacy kernel apply = 4.301965 ms`
- `world batch kernel apply = 4.225554 ms`
- `kernel apply speedup = 1.02x`
- `legacy python loop = 0.516104 ms`
- `world batch runtime = 0.499927 ms`
- `step/read speedup = 1.03x`

再补一个更定向的 reset 主链口径：

- `load_compiled_scenario_batch()`，`world_count = 16`
- 无 reusable buffer：`8.782510 ms`
- 有 reusable buffer：`8.585380 ms`
- `speedup = 1.02x`

再补 profile 口径：

- `WorldBatchVecEnv.reset()`，`n_envs = 16`
- 调整前：
  - `ScenarioLoader._finalize_loaded_world() = 0.021 s`
  - `ScenarioLoader.update_behaviors() = 0.005 s`
  - `ScenarioLoader._rebuild_spatial_geometry()` = `32` calls, `0.003 s`
- 调整后：
  - `ScenarioLoader._finalize_loaded_world() = 0.015 s`
  - `ScenarioLoader.update_behaviors()` 已退出 reset 热路径
  - `ScenarioLoader._rebuild_spatial_geometry()` = `16` calls, `0.001 s`

再补一个实验性 compiled layout template 口径：

- `world_count = 16`
- `worker_threads = 1`
- `legacy layout build = 4.455673 ms`
- `compiled layout build = 4.831221 ms`
- `layout build speedup = 0.92x`

这说明“先把静态 world layout 编译成 metadata”这个方向在语义上是对的，但当前 Python materializer 还没比直接扫 runtime dict 更快；下一步如果继续走这条线，就应该直接面向 batch apply descriptor，而不是继续堆 Python dataclass/template wrapper。

再补两刀已经落地并验证：

- `WorldBatchVecEnv` / `ScenarioLoader.load_prepared_world()` 现在会显式绑定 `compiled runtime metadata`
- batch reset 不再 silently 回退到 `_compile_conditional_objectives()` / `_extract_ils_beacons()` 的 legacy 分支
- `ScenarioLoader._randomize_mission()` 里的 `normalize/materialize/_build_lnav_runtime_config` 已去重，统一只在 `_finalize_loaded_world()` 做一次
- `CompiledScenarioRuntimeMetadata` 已新增 normalized waypoint templates；`ScenarioLoader._randomize_mission()` 选模板时不再从 raw JSON 路径重新 normalize
- runtime world yaw 现在会同步旋转 `mission_cmd["_normalized_waypoints"]`，waypoint cache fast-path 不再默认整段重建
- `route_ref_id` 现在按 route template 的逻辑身份保留，不再因为 world yaw 在 reset 里被清零后反复 hash 重算

定向 profile 下，`WorldBatchVecEnv.reset()` 里：

- `_compile_conditional_objectives()` 已退出热路径
- `_extract_ils_beacons()` 已退出热路径
- `_finalize_loaded_world()` 从 `0.021 s` 进一步降到 `0.014 s`
- `_randomize_mission()` 降到 `0.005 s`
- `materialize_runtime_waypoint_cache()` 已不再出现在 reset 热路径前列
- `route_ref_id` / `_resolve_route_ref_id()` 已退出 reset 热路径前列
- 最新 cProfile 口径下，`WorldBatchVecEnv.reset()` 总时长约 `0.058 s`

也就是说，这一轮终于开始把“compiled metadata ownership”真正接进 batch reset 主链，而不只是优化共享的 Python loader 外围。

### 4.3 Phase 4 execution training adapter benchmark

命令：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark_world_batch_vec_env_phase4.py \
  --scenario scenarios/combined/takeoff_to_landing_continuous_train_v1.json \
  --n-envs 8 \
  --steps 128 \
  --reset-iters 20 \
  --mission-obs-mode nav_v2 \
  --json-out /tmp/phase4_world_batch_vec_env_benchmark.json
```

结果：

- `scenario = scenarios/combined/takeoff_to_landing_continuous_train_v1.json`
- `n_envs = 16`
- `worker_threads = 1`
- `dummy reset = 21.995499 ms`
- `world batch reset = 22.018580 ms`
- `reset speedup = 1.00x`
- `dummy ms/env-step = 0.568250 ms`
- `world batch ms/env-step = 0.505825 ms`
- `step speedup = 1.12x`

补充线程口径：

- `worker_threads = 4` 时，`world batch reset = 24.456712 ms`，`ms/env-step = 0.583615 ms`，`step speedup = 1.00x`
- 当前 reusable apply buffer 接入后，在同口径 `n_envs = 16`、`worker_threads = 1` 下，`world batch reset = 22.152604 ms`，`reset speedup = 1.01x`，`ms/env-step = 0.511517 ms`，`step speedup = 1.13x`
- 在继续重排 finalize / sync 顺序后，同口径 `n_envs = 16`、`worker_threads = 1` 下：
  - `dummy reset = 20.243084 ms`
  - `world batch reset = 20.279023 ms`
  - `reset speedup = 1.00x`
  - `dummy ms/env-step = 0.553388 ms`
  - `world batch ms/env-step = 0.489246 ms`
  - `step speedup = 1.13x`
- 在补齐 compiled metadata ownership、并去掉 mission randomization 的重复 normalize/materialize 后，同口径 `n_envs = 16`、`worker_threads = 1` 下：
  - `dummy reset = 22.383866 ms`
  - `world batch reset = 21.779556 ms`
  - `reset speedup = 1.03x`
  - `dummy ms/env-step = 0.542940 ms`
  - `world batch ms/env-step = 0.471756 ms`
  - `step speedup = 1.15x`
- 在继续补齐 waypoint-template compiled metadata / waypoint cache fast-path 后，同口径 benchmark 仍处于 reset 噪声区：
  - 一次 run：`dummy reset = 20.639908 ms`，`world batch reset = 21.757437 ms`，`reset speedup = 0.95x`
  - 另一次 run：`dummy reset = 22.207889 ms`，`world batch reset = 22.415642 ms`，`reset speedup = 0.99x`
  - 两次 run 都保持 `step speedup = 1.15x`
  - 对应 cProfile 口径下，`WorldBatchVecEnv.reset()` 总时长约 `0.063 s`，优于更早一轮的 `0.066 s`
- 在进一步保留 route template `route_ref_id` 之后：
  - `WorldBatchVecEnv.reset()` 的 cProfile 口径继续降到约 `0.058 s`
  - `40` 次 reset benchmark：`dummy reset = 19.711026 ms`，`world batch reset = 20.312918 ms`，`reset speedup = 0.97x`
  - `120` 次 reset benchmark：`dummy reset = 19.193094 ms`，`world batch reset = 19.936215 ms`，`reset speedup = 0.96x`
  - `step speedup` 仍稳定在约 `1.14x`

也就是说，新增 CPU 目前更适合先换成更高的 `n_envs`，而不是把单个 `WorldBatchRuntime` 的内部线程数直接拉高。

补充口径：

- `CompiledScenario.instantiate() = 0.090577 ms`
- `CompiledScenario.instantiate_runtime() = 0.006641 ms`
- `runtime instantiate speedup = 13.64x`

## 5. 当前结论

这轮结果很明确：

1. Phase 4 的基础设施切口已经成立  
   现在代码库里已经存在真实的 C++ 多 world runtime，而不只是 Python vec-env 封装。

2. 把 compiled-scenario setup 接进 batch runtime 后，收益仍然很有限  
   `kernel apply` 只有 `1.00x`，`step/read` 只有 `1.06x`，说明主要瓶颈并不在 setup surface 的边界调用次数本身。

3. 目前 `WorldBatchRuntime` 仍然是在 C++ 里顺序循环多个 `SimulationKernel`  
   `step_batch()` 还不是 fused stepping，也没有共享静态 scenario runtime、共享 geometry/mission cache、或更粗粒度的批量 observation layout。

4. 第三刀之后，batch runtime 已经开始真正吃到 compiled metadata ownership  
   当前 `WorldBatchVecEnv` 在 non-visual execution 路径上已经拿到 `reset 1.03x`、`ms/env-step 1.15x`，说明收益不再只停留在 setup surface。

5. `worker_threads` 现在必须被当成显式调优项，而不是默认越大越好  
   在当前 world 粒度上，`1 thread` 明显优于 `4` 和 `auto(16)`。新增 CPU 更适合先转化成更高的 `n_envs`，或后续更粗粒度的 batch runtime / fused world lifecycle，而不是在这一版里盲目开内部线程。

6. reusable batch apply buffer 是正确方向，但它还不是吞吐翻倍级变化  
   当前它能稳定压掉一小段 reset 主链里的 Python descriptor 分配成本，但真正的大头仍然在 world lifecycle、loader finalize 和 compiled runtime ownership。

7. 实验性 compiled layout template 目前还不值得挂进主链  
   当前 direct benchmark 下，它的 Python materializer 仍比 legacy layout build 慢，因此这轮只保留 metadata、等价性回归和 benchmark，不把更慢的路径继续接到生产 reset。

8. reset 现在已经进入 benchmark 噪声区  
   profile 显示 reset 主链本身还在继续收缩，但端到端 wall-clock 比值会随着共享路径一起变快而在 `0.95x` 到 `1.03x` 间波动。这说明继续想把 reset 优势稳定拉开，下一步仍然必须把 world lifecycle 和 compiled runtime ownership 往 C++ 推，而不是继续在 Python 主链里修边角。

## 6. 归档前的下一刀设想

归档前，Phase 4 原本认为还应继续做三件事，而不是停在当时的 wrapper 形态：

1. 把 reset/runtime lifecycle 继续往 C++ compiled runtime 推  
   当前 `prepare_scenario_world_layout()` 与 loader finalize 仍在 Python 中完成；虽然 reset 已出现 `1.03x` 的正向收益，但增益仍然过薄，这块仍然是下一刀的主攻方向。

2. 让 `WorldBatchRuntime` 真正管理 compiled scenario / world instance 生命周期  
   不能长期停留在“Python 先准备 layouts，再调用 batch apply”的模式。

3. 扩展 `WorldBatchVecEnv` 的适用面  
   下一步至少要覆盖 action wrapper 语义，随后再讨论 visual path，否则 execution 训练仍需要在配置层规避这条路径。

只有这三步继续推进，Phase 4 才会从“多 world 容器”演进到真正能改写训练吞吐上限的 batch runtime。
