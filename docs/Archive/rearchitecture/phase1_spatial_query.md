# [ARCHIVED] Phase 1: Spatial Query 重构

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中关于“目标”“后续”“分步实施”的描述不再构成当前任务清单。

状态：Archive。已完成并冻结，原冻结日期为 2026-03-20，统一归档日期为 2026-03-22。

## 1. 本阶段目的

第一阶段不直接尝试一次性重写整个训练 runtime，而是优先拆掉当前最重、最公共、最适合作为下沉切口的一层：

`ScenarioLoader` 中的几何 / 航路 / 跑道 / ILS / mission 派生计算

这是因为：

- execution 链和 leader 链都依赖它
- 它当前高度集中在 Python
- 它天然适合编译后数据结构和 C++ 查询接口
- 它能为后续 reward/runtime batch 化提供统一底座

## 2. 当前问题

当前 [scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py) 同时承担了：

- 场景 JSON 解释
- 静态几何维护
- route / waypoint 推进
- runway local frame
- ILS 观测派生
- mission observation 派生
- command chain 更新触发
- reward / termination 所需的几何支撑

这带来三个问题：

### 2.1 热路径数学逻辑留在 Python

每步都要在 Python 中重复进行：

- 坐标变换
- 线段投影
- 航迹误差计算
- DME / LOC / GS 几何计算

### 2.2 口径分散

当前相似几何事实在多处被重复解释：

- observation
- reward
- termination
- leader tasking

容易出现“同一 runway / waypoint 几何在不同模块解释不一致”。

### 2.3 后续 batch runtime 无法直接复用

如果几何逻辑继续留在 Python，后续即便 world stepping batch 化，mission/route/ILS 仍会卡在 Python。

## 3. 本阶段目标

Phase 1 的目标不是“完全去掉 `ScenarioLoader`”，而是先建立一个可复用的 compiled spatial runtime，并让 Python 通过它取代手写几何逻辑。

本阶段完成后，应具备：

1. 编译后的静态场景几何表示
2. 统一的 spatial query API
3. route / runway / ILS / recovery 的稳定编号
4. Python 侧 observation / reward / tasking 改为调用 query 结果，而不是重复手写几何

## 4. 本阶段范围

### 4.1 要做

- 为 runway / zone / waypoint / route / ILS 建立编译后结构
- 在 C++ 提供统一 spatial query 接口
- 为 agent 提供下列查询能力：
  - runway local frame
  - nearest / selected runway reference
  - ILS geometry sample
  - route leg projection
  - waypoint cross-track / along-track / dtg
  - route progress / remaining waypoints
- Python 层改为消费 query 结果
- 为 query 结果建立回归合同

### 4.2 暂时不做

- 完整 batch stepping
- 完整 reward 全量下沉
- leader / execution runtime 合并
- 全部场景编译缓存持久化

## 5. 目标设计

### 5.1 新增概念

建议新增两层对象：

#### `CompiledScenarioGeometry`

负责持有静态几何与编号映射。

包含：

- zones / runway 几何
- ILS beacon 定义
- route / waypoint 拓扑
- recovery 参考对象

#### `SpatialQueryRuntime`

负责基于 `CompiledScenarioGeometry + 当前实体状态` 生成查询结果。

## 5.2 Query 结果建议

建议统一一个可绑定结构，例如：

`SpatialQueryResult`

至少包含：

- `runway_valid`
- `runway_along_m`
- `runway_cross_m`
- `runway_heading_deg`
- `ils_valid`
- `ils_loc_error`
- `ils_gs_error`
- `ils_dme_m`
- `route_valid`
- `route_leg_index`
- `route_remaining_count`
- `route_xtk_m`
- `route_along_m`
- `route_dtg_m`
- `route_desired_track_deg`
- `active_waypoint_radius_m`

也可以拆成多个结构，但必须保证 observation / reward / termination / leader 都共享同一口径。

## 6. 推荐落点

### 6.1 C++

优先考虑新增到：

- `src/components/` 下的场景/导航几何组件
- `src/core/engine/` 下的编译后场景运行时入口
- `src/interfaces/python/python_module.cpp`

### 6.2 Python

尽量收缩这些文件中的几何职责：

- [gym_envs/scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py)
- [gym_envs/universal_env.py](/home/void0312/CMO/gym_envs/universal_env.py)
- [python/rl/leader_tasking.py](/home/void0312/CMO/python/rl/leader_tasking.py)

原则是：

- Python 负责组织查询
- C++ 负责产出几何事实

## 7. 分步实施建议

### Step A

先冻结 runway / ILS / route / waypoint 的编译后数据结构和编号规则。

输出：

- 编号规则
- 查询结构定义
- 单元测试样例

### Step B

实现 C++ 单查询接口，先覆盖：

- runway local frame
- ILS sample
- route leg projection

### Step C

让 `ScenarioLoader.get_runway_local_frame()`、`get_ils_observation()`、route 几何计算改为调用新接口。

### Step D

补合同测试，验证：

- mission observation 不变
- reward 几何项不变
- landing / waypoint 判定不变

### Step E

测吞吐与 Python profile，确认热路径 Python 时间明显下降。

## 8. 验证口径

### 8.1 一致性

至少验证：

- takeoff runway 几何
- waypoint route tracking
- landing ILS final
- leader task phase / recover arm 前置判定

### 8.2 性能

至少对比：

- 单 env 每步 wall-clock
- 多 env rollout wall-clock
- Python profile 中 `ScenarioLoader` 热函数占比

### 8.3 稳定性

至少回归：

- `tests/contracts/env/`
- `tests/contracts/unit/`
- `tests/contracts/bridges/`

尤其是 mission obs、landing、waypoint、leader tasking 相关合同。

## 9. 完成标准

当且仅当满足下面条件时，Phase 1 才算完成：

1. Python 不再手写主要几何推导
2. runway / ILS / route 查询口径统一
3. 相关合同不回退
4. 热路径 profile 明确显示 Python 几何计算占比下降

## 10. Phase 1 与后续阶段的关系

Phase 1 不是最终目标，但它会直接决定后续两件事是否容易：

- Phase 2 的 `ScenarioCompiler`
- Phase 3/4 的 reward/runtime batch 下沉

如果第一阶段仍然保留大量分散几何逻辑，后面每一阶段都会被旧口径拖住。

## 11. 已完成实现

截至 2026-03-20，Phase 1 已完成下面这些落地项：

- 新增 C++ 编译后几何运行时：
  - `CompiledScenarioGeometry`
  - runway local frame query
  - ILS query
  - route guidance query
- Python 绑定已暴露：
  - runway / waypoint / route query options/result
  - compiled geometry runtime
- `ScenarioLoader` 已改为优先消费 compiled query 结果，而不是继续手写热路径几何：
  - `get_runway_local_frame()`
  - `get_ils_observation()`
  - `_compute_waypoint_guidance_state()`
  - `_get_waypoint_nav_products()`
  - waypoint arrival / sequencing
  - waypoint turn-relief reward
  - waypoint mission reward 主链
- waypoint / runway / ILS 的观测、奖励、判定已共享同一套 query 口径

Phase 1 仍保留的 Python 责任主要是：

- query 组织与结果拼装
- reward 系数与任务语义装配
- 非热路径兼容 helper

这符合第一阶段“先统一几何运行时，不一次性吞掉全部 reward/runtime”的边界。

## 12. 验证结果

### 12.1 行为回归

已通过低层测试：

- `python -m unittest tests.scenario.test_scenario_compiler -v`

已通过关键合同：

- `tests/contracts/env/mission_obs/mission_obs_nav_v2.json`
- `tests/contracts/env/phase/post_waypoint_transition_regression.json`
- `tests/contracts/env/waypoint/waypoint_turn_relief_regression.json`
- `tests/contracts/env/waypoint/flyover_nav_reward_geometry_regression.json`
- `tests/contracts/env/waypoint/scripted_waypoint_coordination_regression.json`
- `tests/contracts/env/waypoint/flyby_sequence_past_fix_guard_regression.json`
- `tests/contracts/env/waypoint/waypoint_track_reward_regression.json`
- `tests/contracts/bridges/takeoff_to_landing_scripted_bridge.json`

### 12.2 性能基准

新增诊断 benchmark family：

- `spatial_query`

执行命令：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark.py --family spatial_query -- \
  --json-out /tmp/phase1_spatial_query_benchmark.json
```

2026-03-20 本地结果：

- `runway_frame`：compiled `0.000643 ms/call`，legacy Python `0.001159 ms/call`，`1.80x`
- `ils_sample`：compiled `0.000709 ms/call`，legacy Python `0.012589 ms/call`，`17.76x`
- `route_guidance`：compiled `0.017081 ms/call`，legacy Python `0.025377 ms/call`，`1.49x`
- `nav_v2` Python profile：compiled helper `0.1474 s`，legacy helper `0.3089 s`，`2.10x`
- `UniversalEnv` 单环境：`0.4810 ms/step`，`2079.1 steps/s`
- `UniversalEnv` 四环境 rollout：`0.3392 ms/env-step`，`2948.3 env-steps/s`

### 12.3 Profile 结论

在 benchmark 的 `nav_v2` profile 中：

- compiled 路径的主要 Python 时间已经收缩到 query 组织、字典/数组拼装与 `numpy.clip`
- legacy 路径的主要 Python 时间仍集中在 `_legacy_route_guidance`、`_turn_lead_distance_m`、`_bearing_to_deg`

这说明 Phase 1 的目标已经达成：热路径中的主要几何推导不再由 Python 手写执行。

## 13. 完成判定

对照第 9 节的完成标准，当前结论如下：

1. Python 不再手写主要几何推导：已满足
2. runway / ILS / route 查询口径统一：已满足
3. 相关合同不回退：已满足
4. 热路径 profile 明确显示 Python 几何计算占比下降：已满足

因此，Phase 1 已完成，可以进入 Phase 2：`ScenarioCompiler / CompiledScenario`。
