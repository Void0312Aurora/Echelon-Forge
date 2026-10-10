# WorldBatch 线程矩阵基准

`WorldBatchRuntime` 默认使用一个 worker。只有调用方显式选择多 worker 或
auto 模式时才会创建临时 worker。因此 issue #211 是测量任务，不预设一定要
引入 worker pool。

## 可复现命令

在已经生成本地 `ef_py` 构建产物的工作树中运行维护的基准入口：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family world_batch_thread_matrix \
  --scenario scenarios/takeoff/takeoff.json \
  --n-envs 1,2,4,8,16,32,64 \
  --worker-threads 1,2,4,8,0 \
  --steps 64 --repeats 5 --warmup-steps 2 \
  --json-out artifacts/world_batch_thread_matrix.json
```

输出记录代码版本、主机和 Python 信息、配置及有效 worker 数、全部样本、
中位数、p95 和最大值。基准报告应和 JSON 一起保存；没有同时记录版本和
主机配置时，不应跨版本比较结果。

## 计时边界

所有时间统一为每个环境 step 的毫秒数。墙钟样本覆盖维护中的
`WorldBatchVecEnv.step()` 调用；阶段样本来自现有运行时计时契约，包括动作
准备、原生 `step_batch`、状态读取、命令同步、行为更新、观测构建和 reward
处理。这样可以把临时 native batch dispatch 与 Python 适配器/观测工作分开。

该基准不声称测量 policy inference 或完整训练 rollout；做出 RL 吞吐结论前
仍需单独加入对应工作负载。

## 决策规则

将 `worker_threads=1` 作为稳定基线。只有在维护中的工作负载上重复矩阵显示
墙钟和 `batch_step_ms` 均有明显且可重复的收益，并且输出确定性及异常/失败契约
保持不变时，才考虑 worker pool 原型。单世界、小任务或单独的本地 CPU 利用率
不足以支持改变默认值。
