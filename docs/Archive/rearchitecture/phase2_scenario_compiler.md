# [ARCHIVED] Phase 2: ScenarioCompiler / CompiledScenario

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中关于“目标”“后续”“衔接”的描述不再构成当前任务清单。

状态：Archive。已完成并冻结，原冻结日期为 2026-03-20，统一归档日期为 2026-03-22。

## 1. 本阶段目的

第二阶段的目标，是把“场景描述解释”和“运行时实例化”正式分层。

Phase 1 已经把几何热路径从 Python 手写逻辑中拆出去，但 reset 入口仍然存在这些结构问题：

- 每次 reset 重新读 JSON
- 每次 reset 重新处理 imports / prefab 合并
- `ScenarioLoader` 同时承担文件解释、场景实例化、任务随机化、kernel 装配

如果不先把这层拆开，后续：

- `CompiledScenarioRuntime`
- batch reset
- world pool / runtime reuse

都没有稳定边界。

## 2. 本阶段目标

Phase 2 的完成目标是：

1. 引入稳定的 `ScenarioCompiler`
2. 引入可复用的 `CompiledScenario`
3. `ScenarioLoader` 改为消费 compiled scenario，而不是自己解释文件
4. reset 链清晰区分：
   - compile once
   - instantiate many times

## 3. 本阶段已落地内容

Phase 2 最终分两刀完成：

### 3.1 第一刀：新增 `ScenarioCompiler`

文件：

- [scenario_compiler.py](/home/void0312/CMO/python/scenario_compiler.py)

已实现：

- `CompiledScenario`
- `ScenarioCompiler.compile_path()`
- `ScenarioCompiler.compile_data()`
- 路径级缓存
- import 依赖的 mtime 有效性检查
- merged scenario template 的 `instantiate()`

### 3.2 第一刀：`ScenarioLoader` 改为分层入口

文件：

- [scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py)

已新增入口：

- `load_scenario(path, seed)`：
  - 只负责通过 compiler 取 compiled scenario
- `load_compiled_scenario(compiled, seed)`：
  - 负责从 compiled template 实例化 runtime scenario
- `load_scenario_data(data, seed)`：
  - 供 inline / tests / future compiler 调用
- `_load_instantiated_scenario(seed)`：
  - 保留原有 runtime 装配逻辑

这意味着当前 reset 主链已经不再把“文件解释”硬编码在 `ScenarioLoader` 里。

### 3.3 第一刀：新增 Phase 2 benchmark

文件：

- [benchmark_scenario_compiler_phase2.py](/home/void0312/CMO/tools/diagnostics/benchmark_scenario_compiler_phase2.py)

用途：

- 对比 legacy `json.load + imports merge`
- 对比 compiled cold / warm
- 测 `instantiate()`
- 测 `loader.load_compiled_scenario()`

### 3.4 第二刀：去掉 `instantiate()` 的通用 `deepcopy`

文件：

- [scenario_compiler.py](/home/void0312/CMO/python/scenario_compiler.py)
- [test_scenario_compiler.py](/home/void0312/CMO/tests/scenario/test_scenario_compiler.py)

已实现：

- 把 `CompiledScenario.instantiate()` 从整份 scenario dict 的通用 `copy.deepcopy()` 改成针对场景 JSON 树的专用 runtime materializer
- compile 阶段的 raw scenario clone / prefab merge 也统一切到同一套场景树 clone
- 保留非 JSON 值的 slow fallback，避免 inline test scenario 被破坏
- 新增更严格的隔离性回归：
  - `environment.zones[].ils`
  - `entities[].pos`
  - `mission_command` 嵌套分支

## 4. 验证结果

### 4.1 行为回归

已通过单测：

- `python -m unittest tests.scenario.test_scenario_compiler -v`

已通过关键合同：

- `tests/contracts/env/mission_obs/mission_obs_nav_v2.json`
- `tests/contracts/env/phase/post_waypoint_transition_regression.json`
- `tests/contracts/env/waypoint/waypoint_track_reward_regression.json`
- `tests/contracts/bridges/takeoff_to_landing_scripted_bridge.json`

### 4.2 Compiler benchmark

默认 inline 场景（带 prefab import）：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark_scenario_compiler_phase2.py \
  --json-out /tmp/phase2_scenario_compiler_benchmark_default.json
```

结果：

- legacy parse+merge: `0.1254 ms`
- compiled cold: `0.1544 ms`
- compiled warm: `0.0057 ms`
- instantiate: `0.0142 ms`
- load_compiled: `1.8410 ms`
- warm speedup vs legacy parse+merge: `22.15x`
- instantiate speedup vs legacy parse+merge: `8.85x`

真实 combined 场景：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark_scenario_compiler_phase2.py \
  --scenario scenarios/combined/takeoff_to_landing_continuous_train_v1.json \
  --json-out /tmp/phase2_scenario_compiler_benchmark_combined.json
```

结果：

- legacy parse+merge: `0.2964 ms`
- compiled cold: `0.4152 ms`
- compiled warm: `0.0050 ms`
- instantiate: `0.0976 ms`
- load_compiled: `2.7609 ms`
- warm speedup vs legacy parse+merge: `59.46x`
- instantiate speedup vs legacy parse+merge: `3.04x`

相对第一刀 benchmark，`instantiate()` 的改善更关键：

- default inline 场景：`0.0455 ms -> 0.0142 ms`
- real combined 场景：`0.3440 ms -> 0.0976 ms`

## 5. 当前结论

Phase 2 最终证明了三件事：

1. 场景文件解释 / imports 合并可以稳定从 reset 热路径中拿掉  
   warm compiler cache 对 legacy parse+merge 已经是数量级提升。

2. `CompiledScenario.instantiate()` 不再受整份 scenario template `deepcopy` 限制  
   runtime materializer 已经把场景实例化成本压到原先的约三分之一。

3. reset 主成本已经从 compiler/instantiate 转移到 loader runtime 和 kernel 装配  
   `load_compiled_scenario()` 仍然远高于 `instantiate()`，说明下一阶段真正该拆的是 mission/reward/runtime 逻辑，而不是继续回头堆 compiler cache。

所以，Phase 2 到这里可以结束，后续性能主线进入 Phase 3。

## 6. 归档前的后续衔接

Phase 2 结束后，接下来的性能工作应该转入：

- Phase 3：mission observation / reward / termination 下沉
- 继续减少 `ScenarioLoader` 对原始可变 `scenario_data` 的依赖
- 为后续 `CompiledScenarioRuntime` / `WorldBatchRuntime` 准备更稳定的运行时输入结构

## 7. 完成判定

Phase 2 现在满足了下面条件：

1. reset 不再重新解释场景文件和 imports
2. `ScenarioLoader` 只消费 compiled scenario / runtime instance
3. runtime instantiate 不再依赖整份 scenario dict 的重型 `deepcopy`
4. 改进已经在真实 combined 场景上量化体现
