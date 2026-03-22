# [ARCHIVED] Phase 5: Multi-rate Runtime

> Archive note
> 本文件已于 2026-03-22 归档，仅保留历史实施记录。文中出现的“已开始”“下一刀”“后续”均为归档前语境，不再构成当前任务清单。

状态：Archive。原记录为已开始，但该路线已于 2026-03-22 统一停止并归档；最后记录日期为 2026-03-22。

## 1. 本阶段目的

Phase 4 证明了 `WorldBatchRuntime` 和 execution-layer batch rollout 是有效的，但也同时暴露了一个更深的结构事实：

- 只要 leader 训练仍然是 `LeaderTrainingEnv -> UniversalEnv -> SimulationKernel`
- 每个 leader env 仍然各自拥有一套 execution env
- leader decision interval 仍然通过 Python 循环去驱动 low-level step

那么总吞吐上限仍然会被 env 套 env 的 ownership 结构卡住。

所以 Phase 5 的目标不是继续修 `ScenarioLoader`，而是拆掉 leader 对单 world execution env 的强耦合，改成统一多速率 runtime。

## 2. 第一刀范围

第一刀不直接引入全新的 leader batch runtime，而是先拆掉最硬的 ownership 边界：

1. `LeaderTrainingEnv` 不再默认要求“自己创建并拥有一个 `UniversalEnv`”
2. execution runtime 通过显式接口注入
3. leader 层只依赖：
   - `reset(seed)`
   - `step(action)`
   - `set_randomization_overrides(overrides)`
   - `unwrapped`
   - `policy_env`
4. 现有单环境路径继续通过 `_SingleExecutionRuntime(UniversalEnv(...))` 工作

这一步的意义不是 wall-clock 立刻飙升，而是把后续：

- shared `WorldBatchRuntime`
- leader vec env 直接驱动 batch low-level worlds
- 真正的 multi-rate scheduler

所必须的执行层 ownership 边界先剥出来。

## 3. 已落地内容

文件：

- [leader_env.py](/home/void0312/CMO/gym_envs/leader_env.py)
- [leader_batched_vec_env.py](/home/void0312/CMO/python/rl/leader_batched_vec_env.py)
- [leader_world_batch_runtime.py](/home/void0312/CMO/python/rl/leader_world_batch_runtime.py)
- [leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py)
- [test_performance_knobs.py](/home/void0312/CMO/tests/leader/test_performance_knobs.py)
- [test_world_batch_runtime.py](/home/void0312/CMO/tests/world_batch/test_world_batch_runtime.py)

已新增：

- `_SingleExecutionRuntime`
- `LeaderTrainingEnv(..., execution_runtime=None)`
- `LeaderTrainingEnv.set_execution_runtime()`
- `LeaderTrainingEnv.apply_execution_step_result()`
- `LeaderWorldBatchExecutionRuntimeGroup`
- `LeaderWorldBatchExecutionRuntimeHandle`
- `LeaderWorldBatchExecutionRuntimeHandle.get_last_state()`
- deferred kernel command-chain sync on the shared-runtime path
- teacher / C2 / mission-nav helpers now accept cached `truth/inst` on the shared-runtime path

当前行为：

- 默认仍走 `UniversalEnv` 单环境执行路径
- 但 `LeaderTrainingEnv` 已可以接收外部 runtime object
- scripted execution policy 现在通过 `execution_runtime.policy_env` 获取低层 env 视图
- `reset()` / `step_execution_once()` / `set_randomization_overrides()` 已切到 runtime 接口
- `LeaderBatchedVecEnv` 现在可选地给多份 leader env 注入同一个 low-level `WorldBatchRuntime`
- 在 shared runtime 打开时，leader batched loop 会把 live worlds 的 low-level stepping 收口到一次 batch `step_worlds()`，而不是逐 env 调 `step()`
- leader observation 现在会优先复用 runtime handle 已缓存的 `inst/truth`，避免在 shared runtime 路径里每个 env 再额外打回单 world `get_instrument_state()/get_agent_observation()`
- leader command / intent / report 写回现在也会在 shared runtime 路径下先标脏，再由 batch scheduler 在 step 前统一 `_sync_command_chain_batch()`，不再在每个 env 的 teacher/C2/leader 更新里立刻逐 world 写 kernel
- `ScenarioLoader.get_mission_observation()`、`ScriptedC2TaskManager` 的 station/fuel/recovery/report helpers 已支持外部 `truth/inst`，shared runtime 测试现在会显式阻止这些路径直接回读 `sim.get_*`
- 当时的 `leader_perf_probe.py` 曾用于这条 A/B 路线；脚本现已迁到 [tools/diagnostics/leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py)，当前维护中的 CLI 已移除那批实验性参数
- 兼容性判定现已显式化：shared `WorldBatchRuntime` 现在支持 visual execution env 和 `MultiTimescaleActionWrapper`，但未知 execution wrapper 仍会直接拒绝；不再允许 silent fallback

## 4. 本刀验证

已通过：

- `tests.leader.test_performance_knobs`
  - `test_leader_env_can_inject_execution_runtime`
- `tests.world_batch.test_world_batch_runtime`
- `tests/contracts/unit/comm/task_order_and_mission_link.json`
- `tests/contracts/unit/comm/scenario_loader_mission_semantics.json`
- `tests/contracts/unit/wrappers/leader_phase_mode_bridge.json`
- `tests/contracts/env/mission_obs/mission_obs_nav_v2.json`

这说明当前 leader 主链已经不再和“内部直接 new 一个 `UniversalEnv`”绑定死，而且单进程 batched leader loop 已经能真正共享 low-level worlds。

## 5. 当前性能判断

我补了两组 probe。

### 5.1 最小 scripted probe

口径：

- `LeaderBatchedVecEnv`
- `4` env
- `scripted` execution backend
- `decision_interval_steps = 2`
- 小型 inline scenario

结果：

- baseline `9.2390 ms/leader-step`
- shared runtime `9.4338 ms/leader-step`
- speedup `0.98x`

这证明第二刀刚落地时，shared runtime 还只是 ownership 收口，没有转成 wall-clock 收益。

### 5.2 真实配置 probe

这轮更新后，我重新把更接近真实使用方式的配置接到了真正的 shared runtime 路径上。

1. scripted takeoff smoke

- 场景：`scenarios/takeoff/takeoff.json`
- 配置：[p6_leader_layer_smoke_v1.json](/home/void0312/CMO/examples/config/training/p6_leader_layer_smoke_v1.json)
- `4` env，`32` leader steps，`vec_backend=batched`
- baseline `leader_fps = 85.5745`
- shared runtime `leader_fps = 85.4199`
- speedup `1.00x`（实际微弱回退）

2. frozen-model C2 task demo

- 场景：`scenarios/combined/takeoff_to_landing_c2_task_only_demo_v1.json`
- 配置：[p7_leader_layer_c2_reporting_smoke_v1.json](/home/void0312/CMO/examples/config/training/p7_leader_layer_c2_reporting_smoke_v1.json)
- execution train config 来自 [p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json](/home/void0312/CMO/examples/config/training/p5_takeoff_to_landing_full_visual_navv2_residual_smoke_v3.json)
- 该 config 解析成 `include_visual=True`，并带 `MultiTimescaleActionWrapper`
- 现在 shared runtime 已能真实激活在这条路径上，probe 输出会显式给出 `leader_world_batch_runtime_active=true`

3. p7 真实 A/B 结果

- `4` env，`32` leader steps，`vec_backend=batched`，`execution_device=cpu`
- baseline `leader_fps = 14.6897`
- shared runtime `leader_fps = 15.2715`
- speedup `1.04x`

4. 更长口径复测

- 同一 p7 frozen-model C2 demo
- `4` env，`64` leader steps，`vec_backend=batched`，`execution_device=cpu`
- baseline `leader_fps = 15.5317`
- shared runtime `leader_fps = 16.5035`
- speedup `1.06x`

5. 更高并行度复测

- 同一 p7 frozen-model C2 demo
- `8` env，`32` leader steps，`vec_backend=batched`，`execution_device=cpu`
- baseline `leader_fps = 17.7994`
- shared runtime `leader_fps = 18.4043`
- speedup `1.03x`

6. 同口径 `SubprocVecEnv`

- `4` env，`64` leader steps`
- `4` env，`64` leader steps
- `leader_fps = 30.2315`

结论：

- 这条 Phase 5 主链已经打通
- shared runtime 路径的 direct-state-read、visual obs 和 `MultiTimescaleActionWrapper` 现在都已经接入真实主力配置
- 长口径下第一次出现了超过 `5%` 的真实收益：`4 env / 64 step` 口径约 `1.06x`
- 当前大头仍然在 leader decision logic、reward/observation、以及单进程 scheduler 自身，而不是 low-level stepping ownership
- 即便如此，这条单进程 shared-runtime 路径仍然只有同口径 `SubprocVecEnv` 的约一半吞吐

所以第三刀的价值是两点：

- 把 leader observation 对 low-level state 的读取、visual obs 和 `MultiTimescaleActionWrapper` 全部接入 shared runtime 主链，终于让主力 frozen-model 配置能跑在真实目标路径上
- 用更长口径证明这一刀已经不只是结构收口，而是开始出现有限但真实的 wall-clock 提升

## 6. 归档前的下一刀设想

归档前判断中，下一刀才是真正影响吞吐上限的部分：

1. 把 leader observation / reward / command-link 主链继续从 `LeaderTrainingEnv` 往 shared runtime scheduler 收口
2. 只在 shared runtime 能继续扩大对 batched baseline 的领先时，再考虑是否值得挑战 `SubprocVecEnv`
3. 真实训练口径下继续测 `frozen_model`，而不是只看 smoke probe

做到这一步，Phase 5 才会从“拆 ownership”进入“真实提速”。 
