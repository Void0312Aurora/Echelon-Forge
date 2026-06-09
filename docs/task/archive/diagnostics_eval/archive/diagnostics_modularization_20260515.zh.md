# Diagnostics 收敛与模块化计划

状态：阶段 1、阶段 2、阶段 3、阶段 4 已完成。

日期：`2026-05-15`

## 1. 背景

`tools/diagnostics/` 当前承担了多类职责：

- runtime / compiler / env adapter 的性能 benchmark
- 训练数值问题与非有限值追踪
- 专项轨迹诊断与可视化
- 小规模 train/eval matrix 与探针

目录本身是合理的，但脚本数量与重复实现已经明显增长。当前目录下 Python 脚本约 16 个，总行数约 7k。若继续以“每个问题新建一个独立脚本”的方式推进，后续维护成本会继续上升。

## 2. 已确认发现

### 2.1 目录职责并非错误，问题在于公共底座缺失

`tools/diagnostics/` 的脚本大多不是正式产品化入口，而是：

- 操作员可手动触发的 probe
- 基于本地 checkpoint / build 的 benchmark
- 面向人读摘要而非稳定测试断言的专项诊断

因此不适合简单搬回 repo root，也不适合全部合并成一个 CLI。

问题在于：

- 相同的 repo bootstrap、路径解析、JSON 落盘、timing 聚合在多个脚本中重复实现
- 这些重复没有被沉淀为共享底座
- 已经开始出现“同一类辅助函数复制两次以上”的信号

### 2.2 已确认的重复簇

#### A. benchmark bootstrap / JSON 输出重复

以下 benchmark family 的实现都各自实现了 `json_out` 落盘与路径创建：

- `scenario_compiler`
- `world_batch_runtime`
- `world_batch_vec_env`
- `visual_resolution`
- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`

此外多个脚本还重复实现了：

- repo root 注入
- `ensure_repo_imports()`
- `resolve_repo_path()` / `os.path.abspath()` 组合

#### B. timing 聚合重复

以下实现都各自实现了 timing dict 的 merge / average：

- `leader_perf_probe.py`
- `world_batch_vec_env`

这类逻辑语义非常接近，应该抽成共享工具。

#### C. GPU runtime stats 重复

以下 benchmark family 的实现基本复制了同一套 GPU runtime stats 读取逻辑：

- `policy_observation_bridge`
- `world_batch_vec_env`

涉及：

- `_gpu_device_info_dict()`
- `_visual_stats_dict()`
- `_flight_shaping_stats_dict()`

#### D. 小型 JSON config 加载重复

以下实现都各自实现了本地 `_load_json()`：

- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`

该能力与 `tools/eval/sb3_eval_base.py` 中的 `load_json_config()` 语义相似，但当前目录未复用。

### 2.3 本轮不直接处理的区域

本轮不做：

- 将所有 benchmark 强行合并成一个总 CLI
- 重写 `trace_training_nonfinite_source.py`
- 将 `leader_perf_probe.py` 并入 phase benchmark
- 改写 cooperative trajectory diagnostic 的图表语义

原因：

- 这些脚本虽有样板重复，但业务逻辑差异较大
- 强合并会显著放大回归风险
- 现阶段更高收益的是“抽底座 + 局部迁移”

## 3. 分阶段冻结计划

### 3.1 阶段 1：diagnostics 公共底座抽取

目标：

- 为 `tools/diagnostics/` 建立可复用的共享工具模块
- 先收敛低风险高重复的基础能力

冻结范围：

- repo/bootstrap 常用辅助
- JSON config 加载
- JSON 输出落盘
- timing dict merge / average
- GPU runtime stats 读取

拟新增：

- `tools/diagnostics/common.py`

验收标准：

- 新共享模块能覆盖至少 4 个现有脚本的重复逻辑
- 不改变现有 benchmark 的核心输出 schema

实施结果：

- 新增 [tools/diagnostics/common.py](../../../../tools/diagnostics/common.py)
- 已收敛共享能力：
  - JSON config 加载
  - JSON 输出落盘
  - timing dict merge / average
  - GPU / visual / flight-shaping runtime stats

### 3.2 阶段 2：首批 benchmark / probe 迁移

目标：

- 将首批高重复脚本迁移到共享底座

冻结范围：

- `world_batch_vec_env`
- `policy_observation_bridge`
- `world_batch_runtime`
- `scenario_compiler`
- `visual_resolution`
- `coarse_route_segments`
- `analyze_cooperative_observation_scales.py`
- `leader_perf_probe.py`

验收标准：

- 旧 CLI 参数保持兼容
- `--help` 正常
- `py_compile` 正常

实施结果：

- 已迁移到共享底座 / family 实现层：
  - [tools/diagnostics/benchmarks/world_batch_vec_env.py](../../../../tools/diagnostics/benchmarks/world_batch_vec_env.py)
  - [tools/diagnostics/benchmarks/policy_observation_bridge.py](../../../../tools/diagnostics/benchmarks/policy_observation_bridge.py)
  - [tools/diagnostics/leader_perf_probe.py](../../../../tools/diagnostics/leader_perf_probe.py)
  - [tools/diagnostics/benchmarks/scenario_compiler.py](../../../../tools/diagnostics/benchmarks/scenario_compiler.py)
  - [tools/diagnostics/benchmarks/world_batch_runtime.py](../../../../tools/diagnostics/benchmarks/world_batch_runtime.py)
  - [tools/diagnostics/benchmarks/visual_resolution.py](../../../../tools/diagnostics/benchmarks/visual_resolution.py)
  - [tools/diagnostics/benchmarks/coarse_route_segments.py](../../../../tools/diagnostics/benchmarks/coarse_route_segments.py)
  - [tools/diagnostics/analyze_cooperative_observation_scales.py](../../../../tools/diagnostics/analyze_cooperative_observation_scales.py)

已完成烟测：

- `python -m py_compile tools/diagnostics/common.py ...`
- `./.venv/bin/python tools/diagnostics/benchmark.py --family world_batch_vec_env --family-help`
- `./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge --family-help`
- `./.venv/bin/python tools/diagnostics/leader_perf_probe.py --help`

当前已知环境限制：

- 当前工作区绑定的 `ef_py` 缺少 `ConditionalObjectiveProperty`
- 因此以下脚本在 import `scenario_compiler` / `UniversalEnv` 时会于 `--help` 前失败，这不是本轮重构引入的行为变化：
  - `scenario_compiler`
  - `analyze_cooperative_observation_scales.py`

### 3.3 阶段 3：文档回填与后续候选项整理

目标：

- 更新 `tools/diagnostics/README.md`
- 记录当前已收敛和仍待收敛的区域

当前进度：

- [tools/diagnostics/README.md](../../../../tools/diagnostics/README.md) 已补充共享底座说明
- 已完成本轮尾部整理：
  - `tools/diagnostics/diagnose_training_matrix.py` 已降级迁移到 [tools/archive/diagnose_training_matrix.py](../../../../tools/archive/diagnose_training_matrix.py)
  - `tools/diagnostics/sanity_check.py` 已收敛为正式 runtime test [tests/runtime/core/test_kernel_observation_sanity.py](../../../../tests/runtime/core/test_kernel_observation_sanity.py)

后续候选项：

- 为 subprocess/matrix 型工具抽第二层底座
- 视需要为 archive 工具补充更明确的淘汰说明
- 继续收敛 repo/bootstrap 样板

### 3.4 阶段 4：benchmark 配置驱动入口

目标：

- 避免继续要求使用者记忆大量 benchmark 脚本名
- 将“多个 benchmark 共享一个配置入口”确立为推荐用法

冻结范围：

- 新增一个通用 benchmark suite runner
- 提供至少一份示例 suite 配置
- 文档改为优先推荐通用入口

明确不做：

- 立刻删除现有 benchmark 实现脚本
- 在本阶段重写各 benchmark 的内部逻辑

实施结果：

- 新增 [tools/diagnostics/run_benchmark_suite.py](../../../../tools/diagnostics/run_benchmark_suite.py)
- 新增示例配置 [examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json](../../../../examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json)
- README 与工具总览已切换为优先推荐配置驱动入口

已完成烟测：

- `python -m py_compile tools/diagnostics/run_benchmark_suite.py`
- `./.venv/bin/python tools/diagnostics/run_benchmark_suite.py --help`
- `./.venv/bin/python tools/diagnostics/run_benchmark_suite.py --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json --fail-fast`

烟测观察：

- `spatial_query_phase1` 在 suite runner 下可成功执行
- `world_batch_phase4` 会因当前工作区 `ef_py` 缺少 `ConditionalObjectiveProperty` 而失败
- 这说明通用入口本身可用，当前失败来自具体 benchmark 的环境依赖，而不是 suite runner

## 4. 文档约束

本文件是 `tools/diagnostics` 本轮模块化工作的唯一冻结计划文档。

后续推进要求：

- 先回填本文件，不再额外新增并列计划文档
- 若新增专项文档，只记录实验细节，不重复承担阶段计划职责
