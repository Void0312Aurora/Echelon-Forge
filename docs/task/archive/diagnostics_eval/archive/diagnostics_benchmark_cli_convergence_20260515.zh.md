# Diagnostics Benchmark CLI 收敛计划

状态：阶段 1、阶段 2、阶段 3 已完成，后续仅保留增量清理。

日期：`2026-05-15`

## 1. 背景

当前 `tools/diagnostics/` 中的 benchmark 曾长期按历史阶段拆成多个独立脚本，例如：

- `spatial_query`
- `scenario_compiler`
- `mission_runtime`
- `world_batch_runtime`
- `world_batch_vec_env`
- `policy_observation_bridge`

这种结构在项目推进初期便于快速落专项验证，但长期来看有两个明显问题：

- “阶段号”泄漏到了正式入口层，后续每出现新阶段都倾向于继续新建脚本。
- 使用者需要记忆过多脚本名，而不是记忆一个统一 benchmark CLI 的能力边界。

近期新增的 `run_benchmark_suite.py` 解决了“多个 benchmark 的统一触发”问题。本轮收敛后，它已切换为基于 family 的统一入口分发，不再把 phase 脚本路径作为正式结构的一部分。

## 2. 已确认发现

### 2.1 benchmark 的职责是性能 / 行为回归，不是阶段名展示

这些 benchmark 的共同目标是：

- 比较新旧实现的速度
- 比较新旧实现的数值/行为是否漂移
- 为 runtime/compiler/vec-env/bridge 重构保留回归基线

因此，“phase1/2/3/4” 更适合作为历史来源或 benchmark family 的元信息，而不应继续主导正式 CLI 的命名方式。

### 2.2 能统一的是入口，不是所有测量逻辑

这些 benchmark 的测量对象不同：

- spatial query microbench
- scenario compiler / instantiate / load path
- mission runtime helper microbench
- world batch runtime kernel apply / step-read
- world batch vec env rollout adapter
- policy-observation bridge on/off 对比

因此不应把所有实现强行糊成一个大脚本。但可以统一：

- 一个正式 benchmark CLI
- 一套 mode / family 选择方式
- 一套共享 JSON 输出与参数覆盖方式

### 2.3 本轮收敛边界

本轮实际完成内容聚焦 benchmark CLI / family 实现层收敛，不做：

- 重写每个 benchmark 的核心测量实现
- 批量重写每个 benchmark 的核心测量实现
- 一次性处理所有旧文档中的历史链接

原因：

- 先建立稳定的正式 CLI 更重要
- 先建立稳定的正式 CLI 更重要
- family 实现层与正式入口先收敛，历史文档回填可后置

## 3. 分阶段冻结计划

### 3.1 阶段 1：统一 benchmark CLI 设计冻结

目标：

- 明确一个正式 benchmark CLI 的职责边界
- 将“phase”从入口名中降级为内部 family / mode 元信息

冻结范围：

- 正式入口命名
- family / mode 参数设计
- 与现有脚本的兼容策略

冻结决定：

- 新正式入口采用 `tools/diagnostics/benchmark.py`
- 使用 `--family` 选择 benchmark family，例如：
  - `spatial_query`
  - `scenario_compiler`
  - `mission_runtime`
  - `world_batch_runtime`
  - `world_batch_vec_env`
  - `policy_observation_bridge`
  - `visual_resolution`
- 旧 `benchmark_*_phaseN.py` 不再作为首选入口，后续直接删除

### 3.2 阶段 2：实现统一 benchmark CLI 并迁移 family 实现

已完成：

- 建立 `tools/diagnostics/benchmark.py` 作为统一单 benchmark 入口
- 建立 `tools/diagnostics/benchmark_registry.py`，按 family 懒加载实现模块
- 正式 benchmark 实现迁入 `tools/diagnostics/benchmarks/`
- 临时兼容壳已完成过渡使命，后续直接删除

验收结果：

- 新 CLI `--help` 正常
- family 分发正常
- 旧参数仍可通过 family 实现访问

### 3.3 阶段 3：文档切换与旧入口降级

目标：

- README 与 tools 总览切换到新的正式 benchmark CLI
- 旧 `phase` benchmark 脚本降级为兼容层或内部后端

已完成：

- README 与 `tools/README.md` 已优先推荐 `benchmark.py --family ...`
- `run_benchmark_suite.py` 已以 `family` 为一等输入，不再要求脚本路径
- suite 示例中的 job 名已改为 family 名，不再继续强化 `phaseN` 概念

## 4. 文档约束

## 5. 当前冻结结论

- 正式入口只有两个：
  - `tools/diagnostics/benchmark.py`
  - `tools/diagnostics/run_benchmark_suite.py`
- 正式实现层位于 `tools/diagnostics/benchmarks/`
- `tools/diagnostics/benchmark_*_phaseN.py` 不再保留
- 后续新增 benchmark 时，应新增 family 实现，不应新增新的 `phaseN` 顶层脚本

本文件是 benchmark CLI 收敛工作的唯一冻结计划文档。
