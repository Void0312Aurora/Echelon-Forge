# Echelon Forge

语言版本：

- 英文主文：`README.md`
- 中文辅文：[README.zh.md](README.zh.md)

Echelon Forge 是一个用于空战和飞行任务研究的仿真与强化学习工作台。

该仓库整合了：

- 基于 `flecs` 的 C++ ECS 仿真内核
- 通过 `nanobind` 暴露为 `ef_py` 的 Python 绑定
- 场景编译/运行时工具
- Gymnasium 风格训练环境
- 批量 rollout 和协作训练基础设施
- 评估、诊断和契约式回归工具

该项目仍在演进中，但维护的主线已支持：

- 固定步长仿真和确定性重置种子
- 任务/指令/奖励/终止运行时
- 起飞、巡航、着陆及组合任务训练线路
- 协作执行实验
- 活跃的诊断和评估工具

## 仓库状态

本仓库是一个活跃的研究/工程代码库，并非完善的产物发布。

这意味着：

- 活跃计划和前瞻说明位于 `docs/` 下
- 部分训练线路为冻结基线，其他为活跃实验
- CPU 运行时仍作为规范的世界步进真值
- GPU 辅助路径存在，但仍谨慎对待

## 命名与包标识

仓库目前包含三个相关名称。请有意识地使用它们：

- `Echelon Forge` 是人向项目和仓库名称。
- `EchelonForge` 是 CMake `project(...)` 标识符，除非计划进行专门的构建系统迁移，否则应保持稳定。
- `cmo` 是 `pyproject.toml` 中的遗留 Python 分发/安装标识符，为保持与可编辑安装、本地辅助脚本、缓存构建产物及下游自动化工具的兼容性而保留。

不要将 `cmo` 视为独立产品名，也不要在机会主义下重命名包 ID、CMake ID、辅助名称或脚本路径。完整的命名迁移应作为一个独立的有范围更改来处理，并附上兼容性说明和产物/缓存清理指南。

## 快速开始

本地验证期望在仓库虚拟环境中运行：

```bash
source .venv/bin/activate
```

维护的工作区约定如下：

- 仓库虚拟环境：`.venv`
- Python 元数据和依赖组：`pyproject.toml`
- Linux/macOS 环境辅助脚本：`tools/maintenance/cmo_env.sh`
- Windows/PowerShell 环境辅助脚本：`tools/maintenance/cmo_env.ps1`
- Linux/macOS 构建选择：首选 `CMO_BUILD_DIR`，否则自动检测 `build-workshop`、`build-gpu`、`build`、`build-facade-local`
- Windows 构建选择：首选 `CMO_BUILD_DIR`，否则自动检测 `build-local-win`、`build-workshop`、`build-gpu`、`build`、`build-facade-local`

Linux/macOS 示例：

```bash
python -m pip install pytest numpy
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_summary
cmo_python -m pytest -q tests/runtime/test_env_config.py
```

Windows/PowerShell 示例：

```powershell
.\.venv\Scripts\python.exe -m pip install pytest numpy
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\test_env_config.py
```

当前用于仓库验证的最小烟雾测试集为：

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j4
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/architecture/test_runtime_facade_layering.py \
  tests/architecture/test_cmake_target_readiness.py \
  tests/runtime/test_env_config.py \
  tests/runtime/test_runtime_facade.py \
  tests/world_batch/test_world_batch_runtime.py
```

在 Windows 上，使用 PowerShell 辅助脚本和 Windows 构建目录：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py -j2
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python -m pytest -q `
  tests\architecture\test_runtime_facade_layering.py `
  tests\architecture\test_cmake_target_readiness.py `
  tests\runtime\test_env_config.py
```

上述 Windows 路径仅限于当前本地开发工作流：烟雾测试和重点回归。它并不声称 Windows 不能运行 RL 训练；当本地依赖、运行时产物和运行输出策略就绪后，应有意启用训练工作流。

可选依赖组在 `pyproject.toml` 中声明：

- `.[test]` 声明轻量级烟雾/回归依赖集。
- `.[rl]` 添加 Gymnasium、Stable-Baselines3 和 PyTorch，用于环境/运行时导入。
- `.[train]` 添加训练栈及 TensorBoard。
- `.[world-model]` 覆盖世界模型工具。
- `.[dev]` 是本地开发的便利超集，并非锁定发布环境。

注意：维护的烟雾工作流当前直接安装小型依赖集，然后使用 `cmo_env.sh` / `cmo_env.ps1` 将 Python 指向本地构建的扩展。由于这是一个 scikit-build 项目，`pip install -e ".[test]"` 可能尝试执行可编辑包构建；仅当你有意测试包安装而非快速本地构建循环时才使用它。

目前尚未签入锁定文件。请将可选依赖组视为烟雾/运行时/训练/世界模型工作流的最小能力声明，而非可复现实验锁定。训练结果重现应将解析后的包集与运行产物一同记录，直到引入专用的锁定文件策略。

配置并构建本地扩展：

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j2
```

在 Linux/macOS 上运行 Python 端测试或训练时，优先使用统一仓库辅助脚本：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/architecture/test_runtime_facade_layering.py \
  tests/architecture/test_cmake_target_readiness.py \
  tests/runtime/test_runtime_facade.py \
  tests/world_batch/test_world_batch_runtime.py \
  tests/test_gpu_runtime_bindings.py
```

如果使用不同的构建目录，请在 sourcing `tools/maintenance/cmo_env.sh` 之前导出 `CMO_BUILD_DIR=/path/to/build`，或在 Windows 上调用 `tools\maintenance\cmo_env.ps1` 之前设置 `$env:CMO_BUILD_DIR`。

## 项目布局

- [src/](src/README.md)：C++ 内核、任务运行时、运行时外观、Python 绑定、GPU 辅助。
- [python/](python/README.md)：RL 运行时、训练辅助、场景编译器/运行时、诊断支持。
- [gym_envs/](gym_envs/README.md)：`UniversalEnv`、协作/领导环境支持、场景加载器。
- [scenarios/](scenarios/README.md)：按任务域分组维护的场景定义。
- [examples/](examples/README.md)：配置输入、轻量级固定装置、可视化资产和仅限示例的界面。
- [tests/](tests/README.md)：pytest 套件、契约规范、运行器和固定装置。
- [tools/](tools/README.md)：评估、诊断、运行器、维护脚本。
- [scripts/](scripts/README.md)：保留的操作人员面向的包装器和兼容性工作流外壳。
- [docs/README.md](docs/README.md)：手册、计划、标准、前瞻说明和产物索引。

## 架构边界

维护的依赖方向为：

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content
```

关键规则：

- `components/` 存放 ECS 组件和类似 DTO 的结构
- `systems/` 存放每步突变逻辑
- `models/` 存放可替换的领域模型
- `core/engine` 拥有 `SimulationKernel` 和批量运行时
- `core/mission` 拥有任务运行时和情节编排
- `runtime/facade` 是维护的 C++ 应用程序契约
- `interfaces/python` 应仅保留为绑定/适配

另见：

- [src/README.md](src/README.md)
- [src/core/README.md](src/core/README.md)
- [docs/manual/src_layer_map.md](docs/manual/src_layer_map.md)
- [docs/plan/architecture/src_layered_refactor_freeze.zh.md](docs/plan/architecture/src_layered_refactor_freeze.zh.md)

## 场景与训练配置

维护的场景位于 [scenarios/](scenarios/README.md)，分为：

- `takeoff/`
- `stable_flight/`
- `cruise/`
- `air_combat/`
- `naval/`
- `landing/`
- `combined/`
- `templates/`
- `test/`

训练配置入口点：

- [examples/config/training/README.md](examples/config/training/README.md)
- [examples/config/training/active/README.md](examples/config/training/active/README.md)
- [examples/config/training/frozen/README.md](examples/config/training/frozen/README.md)

其他维护的配置/内容输入位于：

- `examples/config/database/`
- `examples/config/diagnostics/`
- `examples/config/prefabs/`

冻结配置是基线/来源参考。活跃配置是目前训练工作继续的地方。

仓库保留策略概览：

- `scenarios/` 受版本控制，并被视为维护的仓库输入。
- `examples/config/` 受版本控制，并保留维护的和冻结的配置入口点。
- `experiments/`、`datasets/` 和 `output/` 是运行时或产物工作区，默认被忽略。
- 大型运行输出应通过报告、归档清单或留存诊断（位于文档化的产物路径下）来保留，而非将整个实验目录签入主仓库。

## 训练

当前根/操作人员入口点：

- `train.py`
  - 主要执行层和领导层训练入口点。
- `world_model_train.py`
  - 世界模型训练入口点；仍然是一个大型根脚本，尚未像 `train.py` 那样完全拆分。
- `evaluate.py`
  - 历史根评估器，作为兼容性/操作人员界面保留。
- `tools/eval/*.py`
  - 维护的评估 CLI。
- `tools/runners/*.py`
  - 维护的契约和分组回归运行器。
- `scripts/README.md`
  - 小型保留包装器表面，用于仍值得保留为外壳的工作流。

这些入口点的实现主要位于 [python/README.md](python/README.md)、[gym_envs/README.md](gym_envs/README.md) 以及 [src/README.md](src/README.md) 下的 C++ 运行时/绑定层。

训练示例命令：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python train.py \
  --scenario scenarios/combined/takeoff_to_landing_c2_task_only_train_v1.json \
  --train_config examples/config/training/frozen/leader_task_only_retrain_smoke_v1.json \
  --run_name local_smoke \
  --output_base /tmp/cmo_smoke
```

策略评估示例：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/eval/eval_sb3.py \
  --mode single \
  --scenario scenarios/combined/takeoff_to_landing_continuous_eval_v1.json \
  --train_config examples/config/training/frozen/execution/p5_continuous_retrain_v1.json \
  --model path/to/model.zip \
  --episodes 8
```

## 诊断与回归

契约运行器示例：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

典型的 pytest 组：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q \
  tests/runtime \
  tests/world_batch \
  tests/architecture
```

诊断和基准测试脚本集中在 [tools/diagnostics](tools/diagnostics) 下。

## 当前参考文档

- [docs/manual/engine_capabilities.md](docs/manual/engine_capabilities.md)
- [docs/manual/physics_engine_inventory.md](docs/manual/physics_engine_inventory.md)
- [docs/manual/src_layer_map.md](docs/manual/src_layer_map.md)
- [docs/reference_artifacts.md](docs/reference_artifacts.md)

## 前瞻工作

前瞻性说明位于 [docs/forward](docs/forward/README.md) 下。

其中包括新添加的关于执行策略的 HMoE 设计说明：

- [docs/forward/models/hierarchical_moe_execution_policy.md](docs/forward/models/hierarchical_moe_execution_policy.md)

## 工作约定

- 优先使用 `.venv` 进行仓库本地验证
- 优先使用 `tools/maintenance/cmo_env.sh` 进行维护的 Linux/macOS shell 工作流
- 优先使用 `tools/maintenance/cmo_env.ps1` 进行维护的 Windows/PowerShell 工作流
- 优先使用仓库相对路径的场景路径
- 将新的训练配置文件放在明确的子目录中
- 在没有专用冻结的情况下，不要将 GPU 辅助程序视为规范的全局步进真值
- 在引入新的架构目录时添加 README 文件
