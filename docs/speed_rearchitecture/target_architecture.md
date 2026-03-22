# [ARCHIVED] 归档目标架构

注意：

- 本文件已于 2026-03-22 归档。
- 本文件对应的是已经终止路线下的候选目标架构。
- 它只保留作历史设计记录，不再作为实施目标。
- 除非另行立项并重新批准，否则不得继续按本文推进实现。

## 1. 设计原则

这条已终止路线当时遵守五条原则：

1. 热路径整体下沉，不做零碎 helper 微优化。
2. 保留多进程 actor，并把单进程 batching 限定为局部优化手段。
3. Python 负责训练编排，不再负责每步业务状态机。
4. 执行层与 leader 层共用同一套编译态 episode/runtime 基础设施。
5. 主线 visual + wrapper + leader 流必须在目标架构中是一等公民。

## 2. 目标组件

### 2.1 `CompiledEpisodeProgram`

职责：

- 编译场景静态部分
- 冻结 mission / geometry / objective / reward 配置
- 预编译 route / runway / approach / condition tables
- 输出只读、可复用的 episode program

它是 `ScenarioCompiler` 的下一阶段，不再只做“场景装载缓存”，而是变成真正的运行时输入程序。

### 2.2 `ExecutionEpisodeRuntime`

这是新方案的核心。

它应在 C++ 中持有执行层每个 episode 的全部可变状态，包括：

- 当前 agent/world ref
- waypoint / approach / objective / termination state
- mission observation state
- visual cache metadata
- reward accumulator
- done / truncation / termination reason

它每次 step 直接完成：

1. 应用 action
2. 推进一步世界
3. 更新 mission behavior
4. 生成 observation
5. 计算 reward
6. 判断 termination
7. 产出 compact step result

即把当前 Python 中这几段合并：

- `ScenarioLoader.update_behaviors()`
- `build_universal_observation()`
- `ScenarioLoader.compute_full_step()`
- `build_step_info()`

### 2.3 `ExecutionActor`

这是新的并行基础单位。

一个 actor 进程负责：

- 持有 N 个 `ExecutionEpisodeRuntime`
- 本地推进 episode
- 通过 shared memory 读写 observation/action/result

Python 主进程只做：

- rollout buffer 管理
- policy forward
- actor 调度

关键点：

- actor 是多进程的
- actor 内部是否再做 batch，是实现细节，不是顶层架构假设

### 2.4 `LeaderDecisionRuntime`

leader 层不再在 Python 中手写 decision window 循环。

目标改成：

- 一次 leader step，直接在编译态 runtime 中完成一个 decision window rollout
- window 内部推进低层执行环境 K 步
- 同时更新：
  - leader intent
  - command chain
  - report validity
  - transition
  - baseline deviation
  - aggregated reward terms

这样 leader 侧 Python 只保留：

- action tensor 输入
- leader observation 输出
- rollout buffer 对接

### 2.5 统一的共享内存数据面

目标不是继续传大量 Python object，而是定义稳定的 step contract：

- action tensor in
- observation tensor out
- reward / done / truncated / flags out
- 小尺寸 metadata out

其中大 observation 默认走共享内存：

- instruments
- mission
- contacts
- rwr
- visual
- leader observation blocks

## 3. 目标数据流

### 3.1 执行层

```text
SB3 / trainer
  -> actor command ring
  -> ExecutionActor process
  -> ExecutionEpisodeRuntime.step_batch()
  -> shared-memory observations/results
  -> trainer reads compact tensors
```

### 3.2 Leader 层

```text
SB3 / trainer
  -> leader actor command ring
  -> LeaderDecisionRuntime.step_window()
      -> update leader command
      -> advance low-level runtime K steps
      -> aggregate leader rewards/status
  -> shared-memory leader observations/results
  -> trainer
```

## 4. 边界重划

### 4.1 Python 保留什么

- 训练脚本
- 模型加载与推理
- curriculum/experiment orchestration
- benchmark harness
- regression tests
- 兼容层 env wrapper

### 4.2 Python 不再负责什么

- 每步 reward/termination 主流程
- 每步 mission behavior 状态推进
- leader decision window 内部循环
- 大量 step-time object assembly

### 4.3 `ScenarioLoader` 的新角色

`ScenarioLoader` 需要从“热路径 orchestrator”收缩成：

- 场景解析兼容层
- 编译入口
- debug/inspection helper
- 旧接口适配层

不再承担每步关键逻辑。

## 5. 为什么这比继续扩展 `world_batch` 更合适

因为当前数据已经说明：

- helper 下沉有效，但已经不是主瓶颈
- 单纯 batch `SimulationKernel` 调用只有 `~1.06x - 1.10x`
- leader 单进程 shared runtime 甚至跑不过 subprocess

所以新方案必须改的是：

- step contract 的所属层
- actor 并行模型
- Python/C++ 边界粒度

而不是只继续增加几个 `get_*_batch()` / `set_*_batch()` API。
