# [ARCHIVED] Phase 3: Mission Observation / Reward / Termination Runtime

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中关于“目标”“下一步”“后续”的描述不再构成当前任务清单。

状态：Archive。已完成并冻结，原冻结日期为 2026-03-21，统一归档日期为 2026-03-22。

## 1. 本阶段目的

Phase 1 和 Phase 2 已经把：

- 几何热路径
- 场景解释 / instantiate

从 Python 主链里拆出去了。

但 `ScenarioLoader` 里仍然有大量高频 mission/runtime 逻辑：

- `get_mission_observation()`
- `heading_error / ground_track_error` 派生
- reward/objective 里的 command-tracking 共用计算
- approach / waypoint / success 判定前置派生

如果这些仍然全部留在 Python，那么后续：

- reward 继续下沉
- objective / termination 下沉
- batch runtime

都会反复重复同一类 mission-state 派生。

## 2. 核心切片范围

Phase 3 这次的目标是把最重的 mission/runtime 主链和终止组合器一起下沉：

1. `nav_v1 / nav_v2` mission-nav 派生
2. command-tracking error
3. ground-track error
4. mission-nav 使用的 own-heading / ground-track / IAS 解析
5. waypoint reward 主链
6. approach / landing reward 主链
7. conditional objective success 组合器
8. fail-fast / runway safety termination 组合器
9. termination reason runtime 输出接口

这一步的目标是把“前置派生 + 主奖励公式 + objective/termination 评估”统一到 runtime，再让 Python 退化成薄适配层和 phase transition 状态机。

## 3. 本次已落地内容

### 3.1 新增 C++ mission runtime helper

文件：

- [mission_runtime.h](/home/void0312/CMO/src/core/mission/mission_runtime.h)
- [mission_runtime.cpp](/home/void0312/CMO/src/core/mission/mission_runtime.cpp)

已实现：

- `MissionNavInputs`
- `MissionNavProducts`
- `compute_waypoint_mission_nav()`
- `compute_command_tracking_error_deg()`
- `compute_ground_track_error_deg()`
- `resolve_ground_track_deg()`

其中：

- `compute_waypoint_mission_nav()` 负责 `nav_v1/nav_v2` 共用的 mission-nav 派生
- tracking helper 负责 reward/objective 里重复出现的 ground-track / heading 口径

### 3.2 新增 C++ reward runtime helper

文件：

- [reward_runtime.h](/home/void0312/CMO/src/core/mission/reward_runtime.h)
- [reward_runtime.cpp](/home/void0312/CMO/src/core/mission/reward_runtime.cpp)

已实现：

- `WaypointRewardInputs`
- `WaypointRewardProducts`
- `ApproachRewardInputs`
- `ApproachRewardProducts`
- `compute_waypoint_reward_terms()`
- `compute_approach_reward_terms()`

其中：

- waypoint helper 覆盖 progress / distance / cross-track / proximity / arrival 判定
- approach helper 覆盖 localizer / glideslope / DME progress / capture bonus / sink-rate penalty
- 历史量（`_approach_prev_*`、`_waypoint_prev_dist_m`）仍由 Python 持有，但更新逻辑已由 runtime 输出驱动

### 3.3 新增 C++ objective runtime helper

文件：

- [objective_runtime.h](/home/void0312/CMO/src/core/mission/objective_runtime.h)
- [objective_runtime.cpp](/home/void0312/CMO/src/core/mission/objective_runtime.cpp)

已实现：

- `ConditionalObjectiveSpec`
- `ConditionalObjectiveCondition`
- `ConditionalObjectiveInputs`
- `ObjectiveShapingConfig`
- `ConditionalObjectiveProducts`
- `evaluate_conditional_objective()`

其中：

- runtime 负责 conditional objective 的属性取值、比较运算、动态 `CMD_*` 目标解析
- success runway-cross / ground-track shaping 也统一放到同一 helper
- Python 不再在 `compute_full_step()` 里逐条件解释 JSON 并重复手写比较逻辑

### 3.4 新增 C++ termination runtime helper

文件：

- [termination_runtime.h](/home/void0312/CMO/src/core/mission/termination_runtime.h)
- [termination_runtime.cpp](/home/void0312/CMO/src/core/mission/termination_runtime.cpp)

已实现：

- `SafetyRuntimeInputs`
- `SafetyRuntimeProducts`
- `TerminationReasonCode`
- `compute_safety_runtime()`
- `finalize_termination_reason()`
- `termination_reason_name()`

其中：

- runtime 负责 `nan_guard / crash_health / fail-fast / gear-collapse / off-runway-terminate`
- safety block 的 `stall_penalty / overload_penalty / off_runway_penalty / gear_stress_penalty` 也统一从 runtime 输出
- termination reason 现在由 runtime code 生成，再映射成现有字符串接口

### 3.5 Python 绑定已接通

文件：

- [python_module.cpp](/home/void0312/CMO/src/interfaces/python/python_module.cpp)

已暴露：

- `MissionNavInputs`
- `MissionNavProducts`
- `compute_waypoint_mission_nav`
- `compute_command_tracking_error_deg`
- `compute_ground_track_error_deg`
- `resolve_ground_track_deg`
- `compute_waypoint_reward_terms`
- `compute_approach_reward_terms`
- `evaluate_conditional_objective`
- `compute_safety_runtime`
- `finalize_termination_reason`
- `termination_reason_name`

### 3.6 `ScenarioLoader` 已切到 runtime helper

文件：

- [scenario_loader.py](/home/void0312/CMO/gym_envs/scenario_loader.py)

本次改动：

- `_get_waypoint_nav_products()` 不再手工计算 `bearing_rel / cdi / track_angle_error`
- `get_mission_observation()` 继续走原接口，但底层派生已切到 C++ runtime helper
- `_command_tracking_error_deg()` 切到 `compute_command_tracking_error_deg()`
- reward / objective 中共用的 ground-track error 逻辑切到 `compute_ground_track_error_deg()`
- waypoint reward 主链切到 `compute_waypoint_reward_terms()`
- approach / landing reward 主链切到 `compute_approach_reward_terms()`
- conditional objective 在 load 时预编译为 runtime spec，每步只填 `ConditionalObjectiveInputs`
- safety / fail-fast / runway termination 链切到 `compute_safety_runtime()`
- `last_termination_reason` 的收口改成 `finalize_termination_reason() + termination_reason_name()`
- 新增 `_instrument_scalar()`，统一 `InstrumentState` 对象和 instrument ndarray 的取值口径

也就是说，这一刀已经同时触达：

- mission observation
- reward 的 tracking term
- waypoint reward 主链
- approach / landing reward 主链
- objective success 主链
- objective success/fail 判定里的 tracking term
- fail-fast / runway safety termination 主链
- termination reason 输出接口

## 4. 验证结果

### 4.1 行为回归

已通过单测：

- `python -m unittest tests.runtime.test_execution_step_runtime tests.runtime.test_mission_runtime tests.scenario.test_scenario_compiler -v`

已通过关键合同：

- `tests/contracts/env/mission_obs/mission_obs_nav_v2.json`
- `tests/contracts/env/phase/post_waypoint_transition_regression.json`
- `tests/contracts/env/waypoint/waypoint_mode_reward_overrides_regression.json`
- `tests/contracts/env/waypoint/waypoint_progress_negative_scale_regression.json`
- `tests/contracts/env/waypoint/waypoint_route_scaling_regression.json`
- `tests/contracts/env/waypoint/waypoint_reward_balance_regression.json`
- `tests/contracts/env/waypoint/waypoint_turn_relief_regression.json`
- `tests/contracts/env/waypoint/flyover_nav_reward_geometry_regression.json`
- `tests/contracts/env/waypoint/waypoint_track_reward_regression.json`
- `tests/contracts/env/landing/landing_dme_progress_quality_gate_regression.json`
- `tests/contracts/env/landing/landing_short_final_not_offrunway_regression.json`
- `tests/contracts/env/landing/landing_objective_properties_regression.json`
- `tests/contracts/env/landing/ils_threshold_crossing_height_regression.json`
- `tests/contracts/bridges/takeoff_to_cruise_scripted_bridge.json`
- `tests/contracts/bridges/takeoff_to_landing_scripted_bridge.json`

### 4.2 Phase 3 benchmark

命令：

```bash
PYTHONPATH=/home/void0312/CMO/build:/home/void0312/CMO \
./.venv/bin/python tools/diagnostics/benchmark_mission_runtime_phase3.py \
  --json-out /tmp/phase3_mission_runtime_benchmark.json
```

结果：

- legacy nav helper: `0.003344 ms`
- runtime nav helper: `0.000228 ms`
- nav helper speedup: `14.69x`
- legacy command tracking helper: `0.000202 ms`
- runtime command tracking helper: `0.000122 ms`
- command tracking helper speedup: `1.66x`
- legacy waypoint reward helper: `0.002022 ms`
- runtime waypoint reward helper: `0.000224 ms`
- waypoint reward helper speedup: `9.01x`
- legacy approach reward helper: `0.002993 ms`
- runtime approach reward helper: `0.000215 ms`
- approach reward helper speedup: `13.95x`
- legacy objective helper: `0.013922 ms`
- runtime objective helper: `0.000285 ms`
- objective helper speedup: `48.91x`
- legacy safety helper: `0.003933 ms`
- runtime safety helper: `0.000184 ms`
- safety helper speedup: `21.35x`

样例 `nav_v2` 输出与 legacy helper 一致：

- `selected_steerpoint = 1.0`
- `steerpoint_mode_code = 1.0`
- `dist_m = 10000.0`
- `next_turn_deg = -45.0`
- `distance_to_turn_m = 6773.7141`

## 5. 当前结论

Phase 3 已经验证了五件事：

1. mission-nav 和 tracking 派生可以稳定从 `ScenarioLoader` 纯 Python 公式中拿掉  
   不需要改变现有 env / contract 接口。

2. waypoint / approach 主奖励链也可以下沉，而不破坏现有 phase-transition / objective 逻辑  
   这说明 reward 热路径已经不需要继续留在 Python。

3. conditional objective success 组合器也可以下沉，而不破坏 landing / runway success 合同  
   这说明 Python 每步里已经不需要继续解释 objective JSON 并逐条件比较。

4. fail-fast / runway safety termination 也可以下沉，而不破坏现有 bridge / landing / waypoint 合同  
   这说明 Python 每步热路径里已经不需要继续做失败条件判定和 reason 收口。

5. 先统一“前置派生 + reward/objective/termination helper runtime”是值得的  
   `nav_v2`、waypoint reward、approach reward、objective helper、safety helper 这五类高频 helper 都已经是明确提速，主链结构已经符合进入 Phase 4 的前提。

## 6. 剩余工作

Phase 3 到这里可以结束。下一步直接进入 Phase 4：`WorldBatchRuntime` 与 batch Python 绑定。
