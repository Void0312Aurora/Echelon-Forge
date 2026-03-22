# [ARCHIVED] 已终止冻结版三阶段计划

截至 2026-03-22，本方案已完成三阶段收尾，并终止该路线。

本文件已归档，仅保留收尾结论、验收线和止损依据，不再作为执行计划。

当前冻结口径：

- 路线状态：`abort`
- 本文档只保留收尾结论与冻结基线，不再作为执行计划
- 本计划下没有后续实施项

## 当前判断

当前代码树里，已经有两类事实：

1. `execution` 主线已经出现真实但有限的收益
   - 2026-03-22 不带 timing instrumentation 的 execution A/B：
     - `DummyVecEnv`：`0.3792 ms/env-step -> 0.3520 ms/env-step`
     - `WorldBatchVecEnv`：`0.3138 ms/env-step -> 0.2802 ms/env-step`
   - 结论：
     - `ExecutionEpisodeRuntime + ExecutionObservationRuntime` 这条线可以冻结
     - 它不是当前最大的速度问题

2. `leader` 主线仍未被真正解决
   - 2026-03-22 leader `SubprocVecEnv` 的多次 probe 结果，compiled 基本在 `1.00x-1.05x`
   - 结论：
     - 当前真正的瓶颈仍然是 leader decision window
     - 再继续做 `execution` 侧细修，投入产出已经不对

因此，本计划的评估对象已经结束，不再继续实施。

## 冻结规则

以下规则从现在开始生效：

1. 不再扩阶段。
   - 本方案只有三阶段。

2. 不再做微调。
   - 禁止新增 helper runtime
   - 禁止为单个函数做小 cache / 小 copy 消除
   - 禁止为了 benchmark 好看继续堆局部 predictor 调整

3. 每阶段必须有收尾。
   - 固定 benchmark
   - 固定验收线
   - 固定止损条件
   - 固定“完成/停止”结论

4. 不再把“接口铺垫”算作阶段推进。
   - 只有当热路径主逻辑被整块替换时，才算进入下一阶段

## Stage 1: Execution 路径冻结

### 状态

已完成，立即冻结。

### 保留内容

- `ExecutionEpisodeRuntime`
- `ExecutionObservationRuntime`
- execution 路径的 compiled/legacy 双轨
- 现有 parity tests 与 benchmark 脚本

### 允许的修改

- 仅限 bugfix
- 仅限为后续 leader 粗粒度替换提供必要兼容接口

### 禁止的修改

- 不再继续扩展 `ScenarioLoader` 的 helper 级下沉
- 不再继续围绕 `reward/info/obs` 做局部提速
- 不再继续在 `execution` 路径新增 benchmark 驱动的小优化

### 收尾结论

这一阶段已经交付了可保留的基座，但不再是主战场。

## Stage 2: Leader Decision Window 结构替换

### 状态

已完成评估，未过线。

### 目标

把 leader 的整窗热路径，从 Python 编排改成粗粒度 runtime 调用。

这里的“整窗”指：

- begin decision
- action decode / guard / baseline
- rollout 低层 `K` 步
- 聚合 execution reward / C2 transition / report / leader reward terms
- 输出 leader observation / reward / termination / info

### 当前已具备的基座

以下内容仅作为 Stage 2 的替换边界，不再单独扩展：

- `leader_window_runtime`
- `LeaderTrainingEnv`
- `LeaderBatchedVecEnv`
- `LeaderWorldBatchExecutionRuntimeGroup`

它们的意义只有一个：
后续可以直接替换 decision window 的核心实现，而不用再改 env 与 vec backend 的调用关系。

### 当前结构进展

截至 2026-03-22，`leader_window_runtime` 已不再只是薄封装：

- `LocalLeaderWindowRuntime` 已真实接管 leader window 的 `begin / rollout / apply step result / finish`
- `LeaderTrainingEnv` 中对应方法已降为兼容壳
- `LeaderBatchedVecEnv` 与 `LeaderWorldBatchExecutionRuntimeGroup` 继续通过统一 window runtime 接口交互
- `LeaderTrainingEnv` 的低层 execution backend 现已支持单世界 `WorldBatchRuntime` 替换，可在 `SubprocVecEnv` 主基线内直接把 low-level step 从 `UniversalEnv` 路径切到 world-batch 路径
- leader window 现已进一步分出 world-batch 专用 runtime，`execution_world_batch_runtime=true` 时不再复用通用 `LocalLeaderWindowRuntime`

这一步的意义是：
后续整窗级 runtime 不再只剩 shared/batched 旁支可用，而是已经具备了直接命中 `SubprocVecEnv` 主基线的结构替换入口。

### 允许的修改

- 新增或替换“整窗级” runtime
- 新增或替换整窗级 Python/C++ 绑定
- 为整窗 runtime 提供必要的输入/输出合同

### 禁止的修改

- 不再继续优化 `LocalLeaderWindowRuntime`
- 不再继续在 `LeaderTrainingEnv` 里做局部整理
- 不再继续围绕单次 `policy forward` 做小修补
- 不再继续把 leader 热路径拆成更多小 helper

### 固定 benchmark

所有 Stage 2 验收只看固定基线：

- 脚本：`tools/diagnostics/leader_perf_probe.py`
- 场景：`scenarios/takeoff/takeoff.json`
- 配置：`examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json`
- backend：`SubprocVecEnv`
- `n_envs = 4`
- `leader_steps = 64`

### 验收线

Stage 2 只有在下面条件同时满足时才算通过：

1. 语义回归通过
   - 现有 leader/execution 相关单测和合同测试保持通过

2. 吞吐过线
   - 固定 benchmark 连续两次都明显高于当前 baseline
   - 目标不是 `1.01x` 或 `1.05x`
   - 目标至少要进入“值得继续”的区间，默认按 `>= 1.15x` 评估

3. 不是靠 instrumentation 波动得出
   - 带 timing 和不带 timing 的结论不能相互矛盾

### 止损条件

如果第一版整窗级 runtime 落地后，固定 benchmark 仍然只有噪声级变化，或仍不超过 `1.05x`，则停止这条实现路线，不再继续局部修补。

### 当前结果

对固定 benchmark 的最新结构迁移回归：

- 旧的 Stage 2 结构迁移基线：
  - legacy：`25.57 fps`
  - compiled：`26.87 fps`
  - compiled 约 `1.05x`
- 新的单世界 `WorldBatchRuntime` 低层后端替换：
  - 默认 execution backend：`26.04 fps`
  - `execution_world_batch_runtime=true`：`27.45 fps`
  - 约 `1.05x`
- 带 timing 的固定 probe 也保持同方向：
  - 默认 execution backend：`29.31 fps`
  - `execution_world_batch_runtime=true`：`30.65 fps`
  - 约 `1.05x`
- 在 world-batch 专用 leader window runtime 接入后的两轮固定 probe：
  - 第 1 轮：默认 execution backend `26.34 fps`，`execution_world_batch_runtime=true` `25.63 fps`
  - 第 2 轮：默认 execution backend `24.97 fps`，`execution_world_batch_runtime=true` `25.87 fps`
  - 结论：当前没有稳定、可重复的吞吐优势，仍属于噪声级波动区间

结论：

- 这说明新的 Stage 2 结构替换方向没有引入系统性回退
- 但专用 world-batch leader window runtime 没有给出稳定、可重复的吞吐优势
- 结合 timing probe，leader 主时间仍然集中在 frozen execution policy 的 repeated forward，`execution_action_select_ms` 明显高于 window 末端聚合成本
- Stage 2 没有达到通过线，且已经触发止损条件
- 因此这条 leader window runtime 路线应视为评估完成，并已终止

## Stage 3: Cutover Or Abort

### 目标

对 Stage 2 做明确结论，而不是继续拖。

### 状态

已完成，结论为 `abort`。

### 分支 B：终止

Stage 2 未过线，按计划执行：

- 立即停止这条 leader compiled-window / world-batch-window 路线
- 冻结当前最好 baseline
- 不在本计划内追加任何新任务

注意：
这就是三阶段计划的最终收尾结论。

## 当前冻结结论

从现在开始，本计划没有“下一步”。

冻结内容如下：

- 冻结当前最好 baseline
- 把本方向标记为 `abort`

除此之外的任何继续优化或延伸任务，都视为偏离本冻结方案。
