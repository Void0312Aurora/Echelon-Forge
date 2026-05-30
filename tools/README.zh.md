<!-- Machine-translated draft generated on 2026-05-18 from tools/README.md. Review before treating this file as authoritative. -->

# 工具 README

`tools/` 现在按功能对维护的脚本进行分组，而不是将所有入口点保留在顶级目录。

## 布局

- `tools/eval/`
  - 模型/脚本化评估入口点及共享的评估辅助函数。
- `tools/diagnostics/`
  - 面向操作员的探测、基准测试和矩阵式诊断工具。
- `tools/runners/`
  - 用于 JSON 契约套件及类似维护入口点的稳定运行器。
- `tools/maintenance/`
  - 工作区审计和清理辅助函数。
- `tools/archive/`
  - 已归档的临时探测脚本，从仓库根目录迁移而来。

## 评估

- [eval_task.py](eval/eval_task.py)
  - 统一的任务评估器，支持 `stable_flight`、`takeoff_roll`、`centerline` 和 `waypoint_nav`，可选用 `world_model` 或 `scripted` 后端。
- [eval_sb3.py](eval/eval_sb3.py)
  - 统一的 SB3 评估器，支持 `single` 和 `cooperative` 执行策略，并带有特定模式的指标。
- [task_eval_driver.py](eval/task_eval_driver.py)
  - 单智能体任务指标和后端适配器的共享实现。
- [eval_utils.py](eval/eval_utils.py)
  - 共享的引导、环境构建和统计格式化函数。
- [world_model_eval_utils.py](eval/world_model_eval_utils.py)
  - 共享的检查点加载和循环世界模型 rollout 辅助函数。
- [waypoint_eval_utils.py](eval/waypoint_eval_utils.py)
  - 共享的航点任务状态解析和几何指标辅助函数。

## 诊断

- [benchmark.py](diagnostics/benchmark.py)
  - 用于维护的诊断系列的统一基准测试 CLI。
- [run_benchmark_suite.py](diagnostics/run_benchmark_suite.py)
  - 用于 `tools/diagnostics/` 下维护的基准测试套件的统一配置驱动入口点。
- [arma_proxy_backend_stub.py](diagnostics/arma_proxy_backend_stub.py)
  - 面向第一版 `@EchelonProxy` Arma bridge 协议的最小本地 TCP 后端 stub。
- [arma_proxy_backend_echelon_env.py](diagnostics/arma_proxy_backend_echelon_env.py)
  - 基于 Echelon `UniversalEnv` 的 TCP 后端，让 Arma 继续做表现壳，而后端状态在仓库内真实 step。
- [diagnose_cooperative_trajectory.py](diagnostics/diagnose_cooperative_trajectory.py)
  - 统一的协同轨迹回放/导出 CLI，支持 `takeoff` 和 `takeoff_to_cruise`。
- [leader_perf_probe.py](diagnostics/leader_perf_probe.py)
  - 维护的 Leader 层吞吐量探测，支持 `auto/subproc/shared/dummy`。
- [README.md](diagnostics/README.md)
  - 诊断目录的目录和范围说明。

## 运行器

- [run_scenario_contract.py](runners/run_scenario_contract.py)
  - 运行来自 `tests/contracts/` 的一个或多个 JSON 契约。
- [run_pytest_suite.py](runners/run_pytest_suite.py)
  - 运行已签入的 pytest suite manifest，例如 `tests/smoke/ci_smoke_suite.json`，并在路径过期时提前失败。

## 维护

- [redundancy_audit.py](maintenance/redundancy_audit.py)
  - 审计工作区中的重复/临时内容。
- [cleanup_redundancy.py](maintenance/cleanup_redundancy.py)
  - 干运行或执行清理，删除缓存/临时工件。
- [isolate_repro_workspace.sh](maintenance/isolate_repro_workspace.sh)
  - 将选定的实验/数据集目录移开，以创建一个更小的复现工作区。
- [translate_docs_batch.py](maintenance/translate_docs_batch.py)
  - 审计双语覆盖率，并使用与 OpenAI 兼容的 API 批量翻译 Markdown 文档对等文件。

## 归档

- [README.md](archive/README.md)
  - 归档的根级探测的范围说明。
- [batch_api_probe.py](archive/batch_api_probe.py)
  - 用于 C++ 批处理准备 API 的快速手动探测。
- [world_batch_vec_env_benchmark.py](archive/world_batch_vec_env_benchmark.py)
  - 已归档的 vec-env 吞吐量基准测试，早于当前的诊断布局。
- [diagnose_training_matrix.py](archive/diagnose_training_matrix.py)
  - 已归档的辅助函数，用于解析旧版 `evaluate.py` 的文本输出，适用于小型模型/场景矩阵。

## 常见用法

运行契约：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

运行多个契约：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/env/mission_obs/mission_obs_nav_v1.json
```

运行脚本化评估：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/eval/eval_task.py \
  --task stable_flight \
  --backend scripted \
  --scenario scenarios/stable_flight/stable_flight_stresswind_rewardbalance_v3.json \
  --episodes 10 \
  --max_steps 2000
```

审计并干运行清理：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/maintenance/redundancy_audit.py --roots tests tools scenarios
cmo_python tools/maintenance/cleanup_redundancy.py --roots tests tools --include_named_tmp_dirs
```

探测 Leader 层吞吐量：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/combined/takeoff_to_cruise_paramroute_navv2_mixedmode_eval_v2.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 24 \
  --vec_backend shared
```

从单个配置运行维护的基准测试套件：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/run_benchmark_suite.py \
  --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json
```

运行一个维护的基准测试系列：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family world_batch_runtime \
  --world-count 8 --setup-iters 64 --iters 512
```

回放一个协同轨迹诊断：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/diagnose_cooperative_trajectory.py \
  --task takeoff \
  --scenario scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json \
  --train_config examples/config/training/active/cooperative_interval_takeoff_departure_nav_v1.json \
  --model experiments/example/checkpoints/model.zip \
  --output /tmp/cooperative_takeoff_trace.png
```

## 维护指南

- 新的维护任务评估行为应扩展 `tools/eval/eval_task.py` 和 `tools/eval/task_eval_driver.py`，而不是添加每个任务独立的包装脚本。
- 新的维护 SB3 评估行为应扩展 `tools/eval/eval_sb3.py` 和 `tools/eval/sb3_eval_base.py`，而不是重新引入拆分单/协同包装器。
- 共享的评估引导应来自 `tools.eval.eval_utils`，而不是复制的设置块。
- JSON 契约入口点应优先使用 `tools/runners/run_scenario_contract.py`，而不是一次性包装器。
- 维护的诊断应优先使用 `tools/diagnostics/benchmark.py` 用于单个基准测试系列，以及 `tools/diagnostics/run_benchmark_suite.py` 用于多作业套件。
- 协同轨迹诊断应扩展 `tools/diagnostics/diagnose_cooperative_trajectory.py` 和 `tools/diagnostics/cooperative_trajectory_base.py`，而不是添加任务特定的包装 CLI。
- 临时探测和矩阵扫描应归入 `tools/diagnostics/`。
- 清理/审计辅助函数应归入 `tools/maintenance/`。
- 已归档的临时脚本应移至 `tools/archive/`，而不是留在仓库根目录。
