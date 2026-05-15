# [ARCHIVED] Phase 6: Thin Python Adapter

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中出现的“已开始”“下一刀”“后续”均为归档前语境，不再构成当前任务清单。

状态：Archive。原记录为已开始，但该路线已于 2026-03-22 统一停止并归档；最后记录日期为 2026-03-22。

## 1. 本阶段目的

Phase 5 已经证明两件事：

- shared low-level runtime 在真实 `p7` 路径上可以拿到有限但真实的 wall-clock 收益
- 但继续在 leader / wrapper / command-chain 的 Python 中层做局部优化，收益已经明显进入噪声区

所以 Phase 6 不再追着这些中层路径抠局部吞吐，而是开始收口旧 Python ownership：

- 让 `LeaderTrainingEnv` 只依赖统一的 execution runtime 接口
- 把 shared runtime / single-env runtime / wrapper 细节藏到 runtime adapter 后面
- 为后续继续削薄 Python 主链、甚至把更多 ownership 下沉到更低层 runtime 做准备

## 2. 第一刀范围

第一刀只做 execution runtime adapter 收口，不宣称 wall-clock 提升。

范围：

1. 新增统一 execution runtime adapter
2. 单环境 runtime 和 shared runtime 都实现同一组 runtime hooks
3. `LeaderTrainingEnv` 不再直接摸 `policy_env.reset_state()` / `prepare_action()` / `finalize_step_result()`
4. 增加回归，确保这层 delegation 不会退化回旧写法

## 3. 已落地内容

文件：

- [execution_runtime.py](/home/void0312/CMO/python/rl/execution_runtime.py)
- [leader_env.py](/home/void0312/CMO/gym_envs/leader_env.py)
- [leader_world_batch_runtime.py](/home/void0312/CMO/python/rl/leader_world_batch_runtime.py)
- [leader_batched_vec_env.py](/home/void0312/CMO/python/rl/leader_batched_vec_env.py)
- [test_performance_knobs.py](/home/void0312/CMO/tests/leader/test_performance_knobs.py)

已新增：

- `ExecutionRuntimeAdapter`
- `SingleExecutionRuntime`
- `ExecutionRuntimeAdapter.reset_policy_state()`
- `ExecutionRuntimeAdapter.prepare_action()`
- `ExecutionRuntimeAdapter.finalize_step_result()`

当前行为：

- `LeaderTrainingEnv` 现在通过 runtime hook 完成 reset policy state、prepare action、finalize step result
- `SingleExecutionRuntime` 和 shared `LeaderWorldBatchExecutionRuntimeHandle` 都走同一套 runtime adapter 语义
- shared runtime 的 leader-specific orchestration 现在也收口到了 `LeaderWorldBatchExecutionRuntimeGroup`：
  - `step_leader_envs()`
  - `reset_leader_envs()`
- shared runtime 的 leader step 生命周期收口继续推进：
  - `begin_leader_steps()`
  - `collect_live_execution_batch()`
  - `finish_leader_steps()`
- `LeaderBatchedVecEnv` 不再直接调用 `prepare_shared_execution_action()` / `apply_execution_step_result()` / `_finish_execution_reset()`，只保留调度职责
- `LeaderBatchedVecEnv.step_wait()` 现在也不再直接扫描 shared leader env 的 pending/live/finish 细节；这些已经转移到 runtime group
- wrapper 细节仍然保留，但已收口到 runtime adapter 之后，不再散落在 leader 主链里

## 4. 本刀验证

已通过：

- `tests.leader.test_performance_knobs`
  - `test_leader_env_can_inject_execution_runtime`
  - `test_leader_env_delegates_prepare_and_finalize_to_execution_runtime`
- `tests.world_batch.test_world_batch_runtime`
- `tests.world_batch.test_world_batch_vec_env`
- `tests/contracts/unit/wrappers/leader_phase_mode_bridge.json`

## 5. 当前结论

这一刀的价值不是速度，而是把 Phase 5 之后还在 leader 主链里的 runtime 兼容分支再收掉一层。

这意味着后续如果继续做：

- execution action prepare
- execution step result finalize
- shared scheduler 和 single-env scheduler 的进一步合流

都可以继续挂在 runtime adapter 上，而不是继续往 `LeaderTrainingEnv` 里加特判。

## 6. 归档前的下一刀设想

归档前，Phase 6 只认为还值得继续做两类事情：

1. 把 leader / execution 调度里剩余的 runtime-specific Python 分支继续收口到 adapter
2. 在 adapter 边界稳定后，评估是否还值得回到吞吐主线，继续做更低层 ownership 下沉

如果下一刀仍然不能带来明确结构收益，就不再扩张 Phase 6 的表层兼容层。
