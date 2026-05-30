<!-- Machine-translated draft generated on 2026-05-18 from tools/diagnostics/README.md. Review before treating this file as authoritative. -->

# 工具诊断 README

`tools/diagnostics/` 包含面向操作人员的探针、基准测试和矩阵检查，用于支持维护的 CPU 主线运行时，以及在明确要求时支持冻结的实验性 GPU 辅助线。

这些脚本特意与顶级入口点分离，因为它们通常：

- 执行一次性的探索性扫描
- 依赖于本地模型/检查点的可用性
- 输出面向人类的摘要，而非稳定的机器可检查断言
- 帮助诊断故障，而非作为维护的核心工作流

维护的诊断共享支持代码现在开始存放在：

- [benchmark.py](benchmark.py)
  - 统一的基准 CLI。这是主要的单一基准入口点；优先使用 `--family ...`。
- [benchmarks/](benchmarks)
  - 维护的基准族实现。新的基准逻辑应放在此处，而不是新创建的顶级 `benchmark_*_phaseN.py` 文件。
- [common.py](common.py)
  - 用于诊断/基准脚本的共享 JSON 输入输出、计时聚合和 GPU 运行时统计帮助程序。
- [run_benchmark_suite.py](run_benchmark_suite.py)
  - 可选的配置驱动套件运行器，构建在统一基准 CLI 和 `family` 调度之上。
- [cooperative_trajectory_base.py](cooperative_trajectory_base.py)
  - 用于维护的协同诊断的共享协同轨迹环境/模型引导、轨迹捕获和绘图帮助程序。

当前维护的诊断：

- [leader_perf_probe.py](leader_perf_probe.py)
  - 针对维护的 `auto`、`subproc`、`shared` 和 `dummy` 基线的快速领导者层吞吐量探针。
- [ablate_visual_training_effect.py](ablate_visual_training_effect.py)
  - 自动执行 `visual_downsample` 训练/评估矩阵，用于视觉执行策略，并按因子聚合最终指标。
- [arma_proxy_backend_stub.py](arma_proxy_backend_stub.py)
  - 面向本地 `game/` Arma bridge 的最小行协议 TCP stub。它确认 `begin_session`，消费 `host_frame`，并为 `echelon_bridge.dll` 产出合成 `proxy_state` 载荷。
- [arma_proxy_backend_echelon_env.py](arma_proxy_backend_echelon_env.py)
  - 面向同一 Arma bridge 的 `UniversalEnv` 真值 TCP 后端。它把后端真值刚体锚定到 Arma host-frame 的位置和朝向上，同时在 Echelon Forge 内真实 step 飞行状态。
- `spatial_query`
  - 编译的空间查询与传统几何基准。
- `scenario_compiler`
  - 场景编译器缓存/实例化/加载基准。
- `mission_runtime`
  - 任务运行时辅助微基准。
- `world_batch_runtime`
  - WorldBatchRuntime 内核应用和步骤/读取基准。
- `world_batch_vec_env`
  - WorldBatchVecEnv 训练适配器基准。
- `policy_observation_bridge`
  - 策略观察桥接基准。
- `visual_resolution`
  - 视觉降采样扫描基准。
- `coarse_route_segments`
  - 粗略航路段错误基准。
- [diagnose_cooperative_trajectory.py](diagnose_cooperative_trajectory.py)
  - 统一的协同轨迹重放/导出 CLI。使用 `--task takeoff` 或 `--task takeoff_to_cruise` 从一个维护的入口点输出特定任务的 PNG + JSON 诊断。
- [diagnose_runway_drift_sweep.py](diagnose_runway_drift_sweep.py)
  - 参数化的起飞地面滑行漂移扫描，用于量化不同种子、风向和政策选择下的偏离跑道行为。
- [diagnose_takeoff_to_landing_trajectory.py](diagnose_takeoff_to_landing_trajectory.py)
  - 用于连续起飞到着陆任务的单集轨迹导出器，输出 PNG + JSON，以便进行脚本/模型比较。

推荐的多个基准维护入口点：

- [run_benchmark_suite.py](run_benchmark_suite.py)
  - 可选的预设运行器，用于可重复的多任务基准套件。
- [benchmark.py](benchmark.py)
  - 主要的单一基准入口点。使用 `--family` 选择基准族。

冻结的实验性 GPU 辅助阶段 0 探针：

- [ef_gpu_visual_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_visual_phase0_probe.cpp)
  - 视觉路径的 C++ 阶段 0 GPU 前端探针。
- [ef_gpu_execution_observation_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_execution_observation_phase0_probe.cpp)
  - 批量执行-观察打包的 C++ 阶段 0 GPU 探针。
- [ef_gpu_flight_shaping_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_flight_shaping_phase0_probe.cpp)
  - 批量 `flight shaping` 奖励项的 C++ 阶段 0 GPU 探针。
- [ef_gpu_interaction_broadphase_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_interaction_broadphase_phase0_probe.cpp)
  - 交互宽阶段的 C++ 阶段 0 GPU 探针。
- [ef_gpu_sensor_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_sensor_candidate_phase0_probe.cpp)
  - 基于保留的宽阶段帮助程序的传感器候选生成的 C++ 阶段 0 GPU 探针。
- [ef_gpu_comm_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_comm_candidate_phase0_probe.cpp)
  - 基于保留的宽阶段帮助程序的通信候选生成的 C++ 阶段 0 GPU 探针。
- [ef_gpu_visual_candidate_phase0_probe](../../src/tools/experimental/gpu_phase0/gpu_visual_candidate_phase0_probe.cpp)
  - 基于保留的宽阶段帮助程序的视觉对象候选生成的 C++ 阶段 0 GPU 探针。

## GPU 阶段 0 构建

保留的 GPU 辅助框架仍然是可选的。要构建它：

```bash
cmake -S . -B build-gpu -DEF_ENABLE_CUDA_EXPERIMENTS=ON
cmake --build build-gpu --target ef_gpu_visual_phase0_probe -j
cmake --build build-gpu --target ef_gpu_execution_observation_phase0_probe -j
cmake --build build-gpu --target ef_gpu_flight_shaping_phase0_probe -j
cmake --build build-gpu --target ef_gpu_interaction_broadphase_phase0_probe -j
cmake --build build-gpu --target ef_gpu_sensor_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_comm_candidate_phase0_probe -j
cmake --build build-gpu --target ef_gpu_visual_candidate_phase0_probe -j
```

示例探针运行：

从单个配置运行多个维护基准：

```bash
./.venv/bin/python tools/diagnostics/run_benchmark_suite.py \
  --config examples/config/diagnostics/benchmark_suite_runtime_phase14_mainline.json \
  --json-out /tmp/runtime_phase14_mainline.json
```

通过统一 CLI 运行一个基准族：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py \
  --family world_batch_vec_env \
  --n-envs 8 --steps 128 --reset-iters 24 --mission-obs-mode nav_v2 --action-mode full
```

运行本地 Arma proxy backend stub：

```bash
./.venv/bin/python tools/diagnostics/arma_proxy_backend_stub.py \
  --host 127.0.0.1 \
  --port 8765 \
  --start-position 1200 3400 1500 \
  --speed-mps 220 \
  --log-requests
```

运行 env-backed Arma proxy backend：

```bash
./.venv/bin/python tools/diagnostics/arma_proxy_backend_echelon_env.py \
  --host 127.0.0.1 \
  --port 8765 \
  --scenario scenarios/stable_flight/stable_flight.json \
  --action-mode full \
  --mission-obs-mode basic
```

显示族特定帮助：

```bash
./.venv/bin/python tools/diagnostics/benchmark.py \
  --family world_batch_vec_env \
  --family-help
```

```bash
./build-gpu/ef_gpu_visual_phase0_probe --frames 512 --objects 64 --envs 16 --history-steps 2048 --terrain off
./build-gpu/ef_gpu_visual_phase0_probe --frames 64 --objects 64 --envs 16 --terrain gpu
./build-gpu/ef_gpu_execution_observation_phase0_probe --frames 128 --envs 1024 --contacts 8 --rwr 4 --max-contacts 16 --max-rwr 8 --mission-mode nav_v2
./build-gpu/ef_gpu_flight_shaping_phase0_probe --frames 256 --envs 4096
./build-gpu/ef_gpu_interaction_broadphase_phase0_probe --worlds 16 --entities 1024 --queries 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_sensor_candidate_phase0_probe --worlds 16 --targets 1024 --sensors 256 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_comm_candidate_phase0_probe --worlds 16 --nodes 1024 --networks 2 --cell-size 10000 --bucket-count 32768 --bucket-capacity 64
./build-gpu/ef_gpu_visual_candidate_phase0_probe --worlds 16 --objects 1024 --cameras 64 --far-range 25000 --cell-size 5000 --bucket-count 32768 --bucket-capacity 64
```

维护说明：

- 新的维护基准逻辑应扩展 `tools/diagnostics/benchmarks/` 和 `benchmark_registry.py`。
- 不要添加新的以阶段命名的顶级基准脚本。
- 协同轨迹诊断应扩展 `tools/diagnostics/diagnose_cooperative_trajectory.py` 和 `cooperative_trajectory_base.py`，而不是重新引入每任务包装脚本。
- 更长的特定任务轨迹或扫描诊断应仅在此处保留，如果它们仍然是维护的操作工具；否则将其存档，而不是留在 `tests/` 下。
