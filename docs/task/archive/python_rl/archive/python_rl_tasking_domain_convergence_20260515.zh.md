# python/rl Tasking 子域收敛分析与第一阶段实现冻结

状态：`2026-05-16` 第一阶段实现已完成并进入根级 shim 清理后状态
范围：`python/rl` 中与 `tasking` 子域直接相关的模块，以及它们在 `gym_envs/`、`python/testing/` 中的外部入口

## 1. 目标

本轮不直接重构 `python/rl` 全部内容，而是先完成 `tasking` 子域的第一阶段收敛：

1. 冻结 `python/rl` 的子域划分。
2. 明确 `tasking` 子域的唯一外部入口策略。
3. 基于真实调用链判断 `tasking_bridge.py`、`tasking_air_adapter.py`、`common_core_profile.py`、`leader_tasking.py` 的冗余性与保留理由。
4. 完成最小代码实现，消除“bridge 与 adapter 直连混用”的状态。

## 2. python/rl 子域冻结

当前建议将 `python/rl` 冻结为以下子域：

- `runtime`
  - `world_batch_vec_env.py`
  - `cooperative_world_batch_vec_env.py`
  - `execution_runtime.py`
  - `single_world_batch_runtime.py`
  - `leader_world_batch_runtime.py`
  - `leader_window_runtime.py`
  - `leader_batched_vec_env.py`
  - `shared_memory_vec_env.py`
  - `multi_agent_runtime.py`
- `tasking`
  - `leader_tasking.py`
  - `bridge.py`
  - `air_adapter.py`
  - `common_core_profile.py`
  - `profile/air_profile.py`
  - `profile/common_core_base.py`
  - `profile/common_core_defaults.py`
- `control`
  - `wrappers.py`
  - `scripted_takeoff.py`
  - `scripted_stable_flight.py`
  - `scripted_landing.py`
  - `mission_defs.py`
- `policy_algo`
  - `policies.py`
  - `hmoe_routing.py`
  - `ppo_adaptive_kl.py`
  - `device_dict_rollout_buffer.py`
- `planning`
  - `coarse_route_propagator.py`
- `support`
  - `nonfinite_probe.py`
  - `multi_agent_benchmark.py`
  - `sb3_vec_env_compat.py`

本文件只推进 `tasking` 子域。

## 3. tasking 调用链现状

已确认的主要调用关系：

- `gym_envs/scenario_loader.py`
  - 通过 `python.rl.tasking.bridge` 使用
    - `build_kernel_mission_command`
    - `make_rule_based_leader_phase_manager`
    - `normalize_task_order_spec`
- `python/testing/scenario_contract_runner.py`
  - 通过 `python.rl.tasking.bridge` 使用
    - `normalize_task_order_spec`
    - `build_kernel_mission_command`
    - `make_rule_based_leader_phase_manager`
- `gym_envs/leader_env.py`
  - 之前同时使用
    - `python.rl.tasking.bridge`
    - `python.rl.tasking.air_adapter.ScriptedC2TaskManager`
- `python/rl/world_batch_vec_env.py`
  - 现直接使用 `python.rl.tasking.leader_tasking.build_kernel_mission_command`
- `python/rl/cooperative_world_batch_vec_env.py`
  - 现直接使用 `python.rl.tasking.leader_tasking.build_kernel_mission_command`
  - 以及 `_apply_task_order_overrides`

因此在本轮实现前，`tasking` 子域同时存在三条入口：

1. `tasking.bridge`
2. `tasking.air_adapter`
3. `tasking.leader_tasking`

这会让调用方难以判断哪个才是稳定 API。

## 4. 对关键模块的判断

### 4.1 `tasking_bridge.py`

判断：

- 不是死代码。
- 也不是当前就能删除的纯冗余层。
- 它现在承担的是“profile dispatch seam”的角色，但实现上仍是单 profile (`air`)。

结论：

- 保留。
- 升格为 `tasking` 子域的唯一外部入口。

### 4.2 `tasking_air_adapter.py`

判断：

- 它本质是 air profile 的聚合 re-export 层。
- 当前最大问题不是文件存在，而是外部调用还在直接 import 它。

结论：

- 暂时保留，作为 `tasking_bridge` 的默认 air profile 载体。
- 不再允许 `gym_envs/`、`tools/`、`tests/` 直接把它当对外入口。

### 4.3 `common_core_profile.py`

判断：

- 它更像 common-core compatibility facade。
- 里面既有真正的 common-core defaults/spec helper，也有大量转发到 `profile/air_profile.py` 的函数。

结论：

- 当前先保留。
- 后续要进一步区分：
  - 真正的 common-core mutation/defaults
  - 仅为空战 profile 提供的语义推断

### 4.4 `leader_tasking.py`

判断：

- 它并非单纯 task manager。
- 目前同时承载：
  - `RuleBasedLeaderPhaseManager`
  - `ScriptedC2TaskManager`
  - `build_kernel_mission_command`
  - 一部分 `air_profile` 代理与覆写逻辑

结论：

- 它是当前 `tasking` 子域的核心实现文件之一，不是冗余文件。
- 但它的职责偏大，后续应继续拆分“phase manager / c2 task manager / mission command bridge / profile helper”。

## 5. 第一阶段冻结策略

本阶段只做以下收敛，不做行为重写：

1. `tasking_bridge` 成为外部唯一入口。
2. `gym_envs/leader_env.py` 不再直接 import `tasking_air_adapter.py`。
3. `tasking_air_adapter.py` 退回为 bridge 背后的默认 air adapter。
4. `leader_tasking.py`、`common_core_profile.py` 暂不做大拆。

本阶段明确不做：

- 删除 `tasking_air_adapter.py`
- 改写 `leader_tasking.py` 内部结构
- 让 `world_batch_vec_env.py` / `cooperative_world_batch_vec_env.py` 立即切换到 bridge
- 引入第二个真实 tasking profile

## 6. 本轮实现

已完成：

1. `python/rl/tasking/bridge.py`
   - 新增 `scripted_c2_task_manager_class(loader=None)`，用于通过 bridge 获取默认 profile 下的 `ScriptedC2TaskManager` 类。
2. `gym_envs/leader_env.py`
   - 移除对 `python.rl.tasking.air_adapter.ScriptedC2TaskManager` 的直接导入。
   - 改为通过 `python.rl.tasking.bridge.scripted_c2_task_manager_class()` 获取默认类绑定。

这样处理后：

- `leader_env` 的外部语义入口已经完全通过 bridge 收口；
- `tasking_air_adapter` 不再暴露给 `gym_envs` 调用面；
- 没有改变现有 `ScriptedC2TaskManager` 的运行时行为。

## 7. 后续阶段建议

### 阶段 2

- 收敛 `world_batch_vec_env.py` 与 `cooperative_world_batch_vec_env.py` 对 `leader_tasking` 的直接 profile helper 调用。
- 目标是让 runtime 层也尽量通过 bridge 获取 profile 相关能力。

### 阶段 3

- 重新切分 `leader_tasking.py`
  - phase manager
  - scripted c2 manager
  - mission command builder
  - task-order override helper

### 阶段 4

- 判断 `common_core_profile.py` 中哪些函数应直接下沉到 `profile/common_core_defaults.py`，哪些应保留为 facade，哪些应删除。

## 8. 当前风险

- `tasking_bridge.py` 仍然只 dispatch 到 air profile，因此“多 profile”仍只是 seam，不是完整能力。
- `leader_tasking.py` 仍被 runtime 层直接依赖，因此子域内部结构还没有真正变薄。
- `tasking_air_adapter.py` 仍会在文档和旧计划中出现，后续文档需要逐步更新为“内部 air adapter”，而非外部入口。
