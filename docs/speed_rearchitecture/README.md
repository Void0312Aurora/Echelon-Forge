# [ARCHIVED] 速度重构计划总览

本目录已于 2026-03-22 归档。

这是一套独立于 `docs/rearchitecture/` 的已终止冻结方案。它只保留真实热路径结论、止损依据和历史 benchmark 背景，不再作为当前执行计划。

从 2026-03-22 起，这里只保留三件事：

1. 说明真正的热路径在哪里。
2. 说明哪些工作已经冻结，不再继续微调。
3. 记录该路线已经终止的结论。

## 当前结论

这次调研得到的核心事实是：

- Phase 1-3 类型的“纯几何/纯公式 helper 下沉”收益很大，但它们已经不是主瓶颈。
- Phase 4 的 `WorldBatchRuntime` 只把“reset / apply / set_action / step / readback”这一层做了批处理，未触及执行层每步最重的 Python 编排。
- Leader 层目前最慢的部分不是单次低层世界步进，而是 Python 侧的“高层决策窗口 + 多次低层 rollout + 状态拼装 + 奖励汇总”。
- 现有单进程 batched/shared-runtime 路径并没有稳定打赢 `SubprocVecEnv`，说明“把所有 env 塞回一个进程”不是当前代码库的正确主方向。

因此，后续不再接受局部优化。原本唯一允许继续推进的，是 leader decision window 的整窗级结构替换；截至 2026-03-22 晚上的固定 probe，这条路线已经达到止损条件并终止。

注意：

- 本目录中的“阶段”“方案”“计划”均为历史口径。
- 当前默认不再以吞吐提速作为主线工作目标。

## 本轮实测摘要

在当前工作树、当前机器上得到的轻量基准结果：

- `benchmark_mission_runtime_phase3.py`
  - nav helper: `10.99x`
  - waypoint reward: `10.33x`
  - approach reward: `15.18x`
  - objective helper: `39.62x`
  - safety helper: `19.22x`
- `benchmark_world_batch_phase4.py --world-count 8 --world-batch-threads 1`
  - layout build speedup: `0.96x`
  - kernel apply speedup: `1.01x`
  - step/read speedup: `1.10x`
- `benchmark_world_batch_vec_env_phase4.py --n-envs 8`
  - reset speedup: `0.94x`
  - env-step speedup: `1.06x`
- `tools/diagnostics/leader_perf_probe.py`
  - `subproc`: `leader_fps = 25.59`
  - `batched + leader_world_batch_runtime`: `leader_fps = 15.37`
  - batched/shared-runtime 只有 `0.60x` 的 `subproc` 吞吐

这些数字足以说明，当前真正的速度问题不再是“单个 helper 是否用 C++ 实现”，而是：

- Python 每步 orchestration 仍然过重
- 单进程化破坏了原本有效的进程级并行
- 跨语言边界仍然以“小对象、多次往返、逐步拼装”为主

## 冻结规则

- 不再新增阶段编号。
- 不再继续 helper 级下沉和细粒度热路径打磨。
- `execution` 路径视为已冻结基座，不再作为主战场。
- 该粗粒度 leader decision window 路线现已完成评估并终止。

## 文档结构

- `current_state_and_bottlenecks.md`
  - 当前执行链、leader 链、批处理链的真实结构与热路径归因。
- `target_architecture.md`
  - 已归档的候选目标架构，仅保留作历史记录。
- `migration_plan.md`
  - 冻结版三阶段计划与最终终止结论。

## 当前收尾结论

当前三阶段冻结方案的结论是：

1. `execution` 基座保留，但冻结。
2. `leader decision window` 结构替换已经完成评估，未跨过门控。
3. 这条路线已经停止，不再继续投入。
4. 本目录不再定义任何后续任务。
