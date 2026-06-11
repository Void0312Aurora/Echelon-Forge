# 工具 README

`tools/` 现在按功能对维护的脚本进行分组，而不是将所有入口点保留在顶级目录。

## 域状态口径

- 这里的大多数通用 eval 示例仍面向 air/execution 任务；cooperative/common 由 maintained learned-policy 与 leader diagnostics 路径覆盖。
- 对于 active training/eval parity，应优先使用 runtime-facade / world-batch 路径的配置。直接构造 `UniversalEnv` 的工具属于 compatibility diagnostics，除非它们显式 opt in `runtime_compatibility_enabled`。
- naval station pre-fire 入口有一个受限 maintained gate：`tools/eval/naval_station_policy_eval.py`。
- ground tasking/schema bootstrap 目前还没有 `tools/` 下的 maintained eval 或 diagnostics runner；不要从本目录清单推断完整 ground runtime 已支持。

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
  - air/execution 任务评估器，支持 `stable_flight`、`takeoff_roll`、`centerline` 和 `waypoint_nav`，可选用 `world_model` 或 `scripted` 后端。它走 raw `UniversalEnv` compatibility path，不是多域 acceptance gate。
- [policy_execution_eval.py](eval/policy_execution_eval.py)
  - learned execution-policy 评估器，支持 `single` 和 `cooperative` 策略，并带有特定模式的指标。`single` 在 `runtime.world_batch_vec_env=true` 时使用 WorldBatchRuntime，否则回落到 raw `UniversalEnv` compatibility path；`cooperative` 使用 `CooperativeWorldBatchVecEnv`。
- [naval_station_policy_eval.py](eval/naval_station_policy_eval.py)
  - 受限 naval station cooperative gate，覆盖 stationing、pre-fire ROE hold reward terms 与 contact-evidence plumbing；这不是 learned-policy acceptance。
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
- [air_combat_weapon_employment_process_probe.py](diagnostics/air_combat_weapon_employment_process_probe.py)
  - 受限 air-combat 武器使用过程 probe，用于 compatibility env path 上的 debug trace、lethality-chain 行与 hybrid action metrics。
- [event_credit_head_probe.py](diagnostics/event_credit_head_probe.py)
  - 统一的 first-event credit-head 诊断入口，用于 fixed-batch fitting 和 online update-path isolation。
- [fire_timing_fault_localization_probe.py](diagnostics/fire_timing_fault_localization_probe.py)
  - 统一的 fire-timing fault-localization 入口，用于 structural toy、real update-path 和 chain-breakpoint probes。
- [analyze_cooperative_observation_scales.py](diagnostics/analyze_cooperative_observation_scales.py)
  - cooperative execution 配置的 observation scale sampler；用于数值卫生检查，不是训练 runner。
- [trace_training_nonfinite_source.py](diagnostics/trace_training_nonfinite_source.py)
  - 聚焦 cooperative training NaN/Inf 的 tracer，会重建维护中的 cooperative flow，并在发现问题时输出 JSON 报告。
- [README.md](diagnostics/README.md)
  - 诊断目录的目录和范围说明。

## 运行器

- [run_scenario_contract.py](runners/run_scenario_contract.py)
  - 运行来自 `tests/contracts/` 的一个或多个 JSON 契约，或运行 `tests/smoke/ci_contract_suite.json` 这类已签入 suite manifest。
- [run_pytest_suite.py](runners/run_pytest_suite.py)
  - 运行已签入的 pytest suite manifest，例如 `tests/smoke/ci_smoke_suite.json`，并在路径过期时提前失败。
  - Suite 条目可以是目录、文件，或 `tests/foo/test_bar.py::test_case` 这类 pytest node ID；node ID 条目仍会在调用 pytest 前检查基础路径是否存在。
- [run_sim_kernel_contracts.py](runners/run_sim_kernel_contracts.py)
  - 对 contract-batch runner 的薄包装，默认使用 `sim_kernel` 分组。

## 维护

- [redundancy_audit.py](maintenance/redundancy_audit.py)
  - 审计工作区中的重复/临时内容。
- [cleanup_redundancy.py](maintenance/cleanup_redundancy.py)
  - 干运行或执行清理，删除缓存/临时工件。
- [isolate_repro_workspace.sh](maintenance/isolate_repro_workspace.sh)
  - 将选定的实验/数据集目录移开，以创建一个更小的复现工作区。
- [translate_docs_batch.py](maintenance/translate_docs_batch.py)
  - 审计双语覆盖率，并使用与 OpenAI 兼容的 API 批量翻译 Markdown 文档对等文件。
- [damage_model_external_evidence.py](maintenance/damage_model_external_evidence.py)
  - 统一的 external signoff evidence CLI，覆盖 source-rights signoff request、intake contract、packet template 和 admission preflight。
- [damage_model_source_governance.py](maintenance/damage_model_source_governance.py)
  - 统一的 source-governance CLI，覆盖 admission audit、retained payload pack 和 source-rights allowed-output policy 检查。
- [damage_model_benchmark_evidence.py](maintenance/damage_model_benchmark_evidence.py)
  - 统一的 benchmark-evidence CLI，覆盖 comparison hashes、mechanism evidence、benchmark execution admission、debris-case admission 和 spreadsheet recalculation/replacement review gate。
- [damage_model_scope_provenance.py](maintenance/damage_model_scope_provenance.py)
  - 统一的 scope/provenance CLI，覆盖 row provenance、target-geometry closeout、warhead-scope closeout 和 mechanism-source closeout。
- [damage_model_independent_review.py](maintenance/damage_model_independent_review.py)
  - 统一的 independent-review CLI，覆盖 effect-scale review、review closeout、scope-bucket review 和 uncertainty review gate。
- 剩余 A2 `a2_blastfrag_*.py`、`a2_candidate_vps_bundle.py` 和 `a2_retained_manifest_integrity.py`
  - 待继续合并为 command family 的候选/retained-artifact governance 任务专用辅助工具。它们是非权威 maintenance gate，不属于 runtime product surface。

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

运行受限 naval station policy gate：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/eval/naval_station_policy_eval.py \
  --scenario scenarios/naval/ddg51_take1_screen_threat_roe_v1.json \
  --train_config examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json \
  --steps 1200
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

- 新的 raw-env/task-metric eval 行为应扩展 `tools/eval/eval_task.py` 和 `tools/eval/task_eval_driver.py`，并在需要时显式处理 compatibility，而不是添加每个任务独立的包装脚本。
- 新的维护 learned-policy 评估行为应扩展 `tools/eval/policy_execution_eval.py` 和 `tools/eval/sb3_eval_base.py` 中的共享 policy-loading helper，而不是重新引入拆分单/协同包装器。
- 共享的评估引导应来自 `tools.eval.eval_utils`，而不是复制的设置块。
- JSON 契约入口点应优先使用 `tools/runners/run_scenario_contract.py`，而不是一次性包装器。
- 维护的诊断应优先使用 `tools/diagnostics/benchmark.py` 用于单个基准测试系列，以及 `tools/diagnostics/run_benchmark_suite.py` 用于多作业套件。
- 协同轨迹诊断应扩展 `tools/diagnostics/diagnose_cooperative_trajectory.py` 和 `tools/diagnostics/cooperative_trajectory_base.py`，而不是添加任务特定的包装 CLI。
- 临时探测和矩阵扫描应归入 `tools/diagnostics/`。
- 清理/审计辅助函数应归入 `tools/maintenance/`。
- 已归档的临时脚本应移至 `tools/archive/`，而不是留在仓库根目录。
