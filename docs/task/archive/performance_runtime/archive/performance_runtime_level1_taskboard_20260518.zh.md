# 一级 runtime 优化任务板

状态：`2026-05-18` 活跃执行任务板。  
范围：真实性冻结后的已确认 Level 1 实现优化任务。

关联文档：

- [runtime 性能优化分层与升级规则](performance_runtime_optimization_ladder_20260518.zh.md)
- [一级实现优化分析](performance_runtime_level1_implementation_analysis_20260518.zh.md)

目的：

- 把当前 Level 1 热点分析转换成一个有顺序的任务集合。
- 把已经完成的窄修复与仍未完成的热点分开。
- 让后续性能工作遵循分阶段任务板，而不是零散 spot edit。

---

## 1. 候选确认

当前 Level 1 候选池已经结合以下内容重新核对：

1. 现有 benchmark 样本；
2. 当前 runtime 步进链路；
3. runtime benchmark 已经输出的 hot-path timing 字段；
4. 本轮已经完成的窄修复。

结果：

- 两个候选已确认并启动；
- 三个候选保持确认但未完成；
- 默认不允许 Level 2 或 Level 3 项目进入这个任务板。

## 2. 已完成 / 已启动项目

### L1-ENTRY-01：诊断 / runtime 入口正确性

状态：已完成。

范围：

- 确保 diagnostics import 优先使用仓库 build runtime，而不是陈旧 site-packages 绑定；
- 保持 benchmark 与 runtime 入口测量到的是预期 runtime。

当前结果：

- benchmark CLI 和 suite 入口已经恢复可用；
- 已为 import 顺序补上回归覆盖。

### L1-OBS-01：移除 `WorldBatchVecEnv` 中的重复视觉刷新

状态：已完成，处于 first-pass 形式。

范围：

- 在 observation attach 期间，不要在 batch refresh 之后再重复刷新单 env 的 visual cache。

当前结果：

- 窄实现修复已落地；
- 已添加定向回归测试。

### L1-STATE-01：扁平化 cooperative step 的 state reads

状态：已完成，处于 first-pass 形式。

范围：

- 把 cooperative step 中按 world 做的 state reads 改成一次精确扁平 batch 读取，然后在本地重新分发。

当前结果：

- 窄实现修复已落地；
- 已添加定向回归测试。

## 3. 已确认但仍开放的任务

下面这些仍是后续轮次应继续推进的 Level 1 任务。

### L1-OBS-02：降低 Python 观测组装 churn

优先级：`P0`  
状态：第二轮分析已完成；第一轮已完成，第二轮实现收紧已落地且整体测量中性。

证据：

- `obs_build_ms` 在 `UniversalEnv`、`WorldBatchVecEnv` 和 cooperative timing 输出中都很明显；
- 当前编译路径仍在逐 env / 逐 slot 做：
  - `np.asarray(...)`
  - `reshape(...)`
  - Python `dict` 组装
  - 可选的 `proprio` 拼接

主要文件：

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)

任务目标：

- 在不改变 observation 契约或语义的前提下，减少 Python 侧分配、reshape 和对象构造 churn。

当前结果：

- 编译后的观测组装路径现在统一复用轻量级 float32 view 转换 helper，不再重复 ad hoc wrapper；
- 已补充回归覆盖，确保编译观测输出保持预期的 `float32` 契约；
- 最新窄 benchmark 轮在观测切片上有正向变化：
  - `world_batch_vec_env` 样本：当前轮 `obs_build_ms ~= 0.137`
  - cooperative smoke 样本：当前轮 `obs_build_ms ~= 3.169`

验收：

- 观测等价 / 回归测试保持绿灯；
- 定向 benchmark 显示 `obs_build_ms` 改善，或至少有测量清晰、可自洽的中性结果。

### L1-TAIL-01：收紧 reward/info 尾部物化

优先级：`P1`
状态：第一轮已完成。

证据：

- hot path 末尾仍包含逐 env / 逐 slot 的 `compute_full_step(...)` 以及 `build_step_info(...)` 或 `build_step_info_minimal(...)`；
- timing 字段显示 batch runtime 中仍有明显的 `reward_info_ms` 尾部。

主要文件：

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)

任务目标：

- 确认哪些地方仍在不必要地构建完整 info；
- 减少 hot path 上“精确但没必要”的尾部物化。

当前结果：

- `WorldBatchVecEnv` 在 regular batch 路径进入 `compute_full_step(...)` 时，开始复用同一步缓存的 `step_evaluation`，不再在 reward 尾部重新构建这一步准备；
- execution-episode-controller 主线在 facade 已经返回精确 `step_info_fields` 时，跳过冗余的 Python `build_step_info(...)` 物化；
- 已补充两条复用路径的窄回归覆盖；
- 当前 compiled / no-visual timing 样本朝着预期方向移动：
  - 旧记录：`reward_info_ms ~= 0.0536`，`total_ms ~= 0.3837`
  - 当前样本：`reward_info_ms ~= 0.0502`，`total_ms ~= 0.3663`

验收：

- `step_info_mode` 的 terminal / full / off 语义保持不变；
- 受影响 benchmark 路径上的 `reward_info_ms` 或总 step 时间有改善。

### L1-BEHAV-01：收紧 Python behavior / sync staging

优先级：`P1`
状态：第一轮已完成。

证据：

- cooperative timing 仍显示可见的 `behavior_update_ms` 和 `command_sync_ms`；
- batch 路径仍在 Python 中串行化部分 behavior update 和 sync staging。

主要文件：

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
- 相关 loader behavior 代码在
  [gym_envs/scenario_loader/](../../../gym_envs/scenario_loader/)

任务目标：

- 在不重设 behavior 语义的前提下，减少 Python 协调开销和冗余的精确同步边界。

当前结果：

- `CooperativeWorldBatchVecEnv` 现在区分了 reset / override 的 command-chain dirty 继承和 steady-state step 执行；
- cooperative 路径不再在每次 step 都无条件做一次完整的 pre-step command-chain flush，而是仅在 step 前 world 仍处于 dirty 状态时才额外 flush；
- post-behavior / post-director 的 command-chain flush 仍然保留，因此下一次精确 world step 仍会看到预期命令；
- 已为以下两点补了定向回归：
  - dirty-world 的 first-step pre-sync 仍然会发生；
  - steady-state step 会跳过冗余 pre-sync；
- 当前 cooperative smoke 风格 timing probe 朝着预期方向移动：
  - 旧记录：`command_sync_ms ~= 0.504`，`step_time_ms ~= 6.522`
  - 当前 probe：`command_sync_ms ~= 0.262`，`step_time_ms ~= 6.630`
- 第二个窄实现收紧也落在 `ScriptedCooperativeCoordinationDirector` 上：
  - world 级 `leader_overrides` 不再在每个 slot apply 内重新复制；
  - steady-state director apply 不再无条件重建 `mission_cmd` mapping，并跳过一组相同值的 Python 字段写入；
  - 已补回归覆盖，锁定：
    - 稳定 director 更新复用已有 `mission_cmd` mapping 对象；
    - takeoff-clearance 进展仍能正确推进。
- 第二轮分析还建立了一个重要边界：
  - `update_scripted_opponents(...)` 当前在 cooperative world 中确实按 slot loader 重复；
  - 但不同 slot loader 可能把同一个 scripted red controller 绑定到不同的 `target_id`，所以把这项工作合并成 once-per-world 已不再是显然的 Level 1 精确优化，必须先做 owner / target-selection 语义决策。
