# Echelon Forge

语言版本：

- 英文主文：`README.md`
- 中文辅文：[README.zh.md](README.zh.md)

Echelon Forge 是一个面向多域任务研究的语义-因果仿真平台，并带有可选的学习层。
它把场景和内容定义、任务与 tasking 语义、领域模型、agent 接口、保真度要求以及实验协议，
组合为可执行、可检查、可比较和可评估的仿真运行。

## 项目内容

- 基于 `flecs` 的原生 C++ ECS 仿真运行时，提供固定步长 CPU 执行和确定性重置种子。
- 类型化 C++ runtime facade，以及通过 `nanobind` 暴露为 `ef_py` 的 Python 绑定。
- 场景编译与实现，覆盖 content、unit、profile 和 mission setup。
- 可选的 Gymnasium 风格环境适配器、向量化 world-batch 执行，以及面向 policy 实验的协同 command/tasking 表面。
- 用于控制、感知、制导、武器、effects 和平台 capability 的领域模型族，并接入共享运行时生命周期。
- 评估、诊断、replay/evidence 导出、契约规范和架构回归门禁。

当前维护主线最完整的端到端覆盖位于 air/execution 和 cooperative execution。Naval 与 Ground
已经准入有界的 tasking、平台、移动、地形、接触、射击和 evidence 表面；这些领域还不代表完整的生产级任务运行时。

## 核心架构概览

架构围绕五个问题组织，而不是拆成互相独立的垂直 runtime stack：

| 面向 | 问题 | 负责内容 |
| --- | --- | --- |
| Semantic | 世界中有什么？ | 领域 ontology、场景/content 编译、capability、role、task 和类型化契约。 |
| Causal | 什么导致什么？ | 状态转移、事件顺序、阶段依赖、barrier 和可 replay 的因果证据。 |
| Agentic | 谁知道、决定并行动？ | information state、authority scope、command/tasking、policy 接口和协同。 |
| Learning | 系统如何改进？ | 评估、curriculum、capability profile、场景生成、policy 和 world-model 消费者。 |
| Experiment | 具体比较什么？ | 场景引用、配置组合、seed、评估协议和可比性规则。 |

这五面模型是维护中的架构方向；各部分实现成熟度并不相同。下面的准入表说明当前哪些领域路径已经被实际运行，哪些仍然是有界或实验性的。

Evidence 是贯穿各面的公共层：trace、packet ancestry、snapshot version、event order 和 validation
verdict 解释一个运行为什么可信。领域功能通过明确的 model family、capability contract 和 stage
contract 接入这些公共面，而不是创建私有的 `air`、`naval` 或 `weapon` runtime stack。

实现遵循以下执行形状：

```text
scenario + content + profile + experiment settings
  -> content 编译与 world setup
  -> tasking 与 command delivery
  -> control 与 physics 状态更新
  -> sensing、track、link、fire/effects 与 damage
  -> observation/result 导出
  -> policy、评估、诊断和 evidence 消费者
```

这些阶段组成因果-时间执行图，可以使用不同频率运行；有界场景也可以跳过空阶段。反馈必须经过显式
的 state version、event timestamp 或 barrier。这是当前固定步长运行时、facade contract 和 evidence
表面的共同架构规则。

完整的 P0-P10 阶段词汇、graph-of-graphs 模型和 stage contract 规则维护在
[Simulation System Architecture Design](docs/architecture/standards/simulation_system_architecture_design.zh.md) 中。

## 仿真层与学习层是分离的

仿真层可以独立运行。它拥有权威 world state、状态演化、因果-时间调度、event 顺序、
facade 可见 snapshot、仿真语义 termination 和编译后的 mission product；它不拥有训练循环、
curriculum、policy state 或前端专用的 observation encoder。

学习与 policy 层是仿真的消费者。learned policy、scripted doctrine、人类操作员或其他 decision
model 选择 observation view，并通过 facade contract 产生 action 或 coordination intent。RL environment
是 **Env-as-View** 适配器：它消费 `ObservationPacket`，通过 facade 注入 action，并镜像 episode state；
它不拥有仿真真值或 episode phase。

因此，仓库维护两条在同一 native truth boundary 汇合的路径：

```text
直接仿真路径（不依赖 RL）
scenario compiler -> facade_batch -> RuntimeFacade -> native simulation
                                     -> snapshot / step result / replay

RL 或 policy 路径（可选消费者）
scenario loader + policy adapter -> 显式 world_batch / WorldBatchVecEnv
                                 -> 同一个 RuntimeFacade 和 native simulation
                                 -> observation/action bridge -> rollout data
```

`facade_batch` 是默认的 no-RL 场景路径；维护中的 RL 训练和评估显式选择 `world_batch`。
两条适配路径共享 native truth boundary，但不能在没有 parity gate 的情况下假定它们的 reward、
termination 和 autoreset 行为完全相同。轻量仿真路径不要求安装 Gymnasium、Stable-Baselines3 或 PyTorch。

## 这种架构带来的优势

- **共享语义：** 新领域功能接入同一生命周期，使跨领域比较使用一致的 task、state、observation 和 evidence 词汇。
- **仿真独立性：** 场景、scripted run、诊断和 facade client 可以不导入 RL 栈而运行原生仿真；学习层保持为可替换消费者。
- **稳定边界：** 前端依赖 `src/runtime/facade` 和类型化 packet，而不是直接依赖 Flecs entity、kernel 顺序或 backend 细节。
- **权威真值：** 原生 CPU runtime 拥有世界状态和 episode 真值；Python mirror 与 GPU 辅助路径保持为适配器或有界 capability。
- **实验可比：** 固定步长、显式 seed、profile、scenario/config 输入和评估协议让运行更容易复现和比较。
- **结果可解释：** observation provenance、诊断、契约测试和回归门禁可以说明结果使用了什么，以及哪个边界真正得到验证。
- **受控扩展：** 新领域在成为维护路径前，需要声明参与的 lifecycle stage、packet、capability seam 和 evidence。

## 项目范围与状态

本仓库是一个活跃的研究/工程代码库，并非完善的产物发布。

这意味着：

- 活跃计划和前瞻说明位于 `docs/` 下
- 部分训练线路为冻结基线，其他为活跃实验
- CPU 运行时仍作为规范的世界步进真值
- GPU 辅助路径存在，但仍谨慎对待
- 社区贡献目前采用 issue-first 和 owner-scoped 模式；见
  [CONTRIBUTING.md](CONTRIBUTING.md)

## 项目内容与成熟度

本仓库已经是多域项目，但各领域成熟度并不相同。下面的表格是入口地图，不是发布承诺。

| 领域 | 当前状态 | 主要入口 |
| --- | --- | --- |
| Air / execution | 最成熟的 runtime 和训练线，也是当前最适合作为 correctness hardening 的基线。 | `scenarios/takeoff/`、`scenarios/cruise/`、`scenarios/landing/`、`examples/config/training/frozen/` |
| Cooperative / combined | 活跃集成主线，用于验证 multi-agent、leader/execution 和 world-batch 行为。 | `scenarios/combined/`、`python/rl/runtime/cooperative_world_batch_vec_env.py`、`gym_envs/leader_env.py` |
| Naval | 活跃领域，已有 N4 风格的 pre-fire tasking、contact/reporting、screen/station 与评估 gate；武器/毁伤结果 authority 仍是后续工作。 | `scenarios/naval/`、`docs/domains/naval/` |
| Ground | 已有静态 tasking、受限单兵移动、Arnis 地形采样、依赖跟踪目标的直射与共享毁伤探针；完整寻路、感知、压制及生产级 Ground WorldBatch 仍未准入。 | `scenarios/ground/`、`docs/domains/ground/`、`docs/systems/environment/` |
| Air combat / A2 | 聚焦的战斗与高保真毁伤模型工作线，已有 retained evidence gate。它是一个领域线，不是整个项目身份。 | `scenarios/air_combat/`、`docs/domains/air/`、`docs/learning/work/active/`、`docs/systems/effects/reviews/` |
| Visualization / game | 探索性的操作员与前端表面；维护路径应以后端仿真 runtime 真值为准。 | `examples/viz/`、`docs/operations/visualization/` |
| Model / world model | 策略/模型侧规划与实验线，包括 temporal HMoE 和世界模型工具。 | `docs/learning/`、`world_model_train.py` |

## 命名与包标识

仓库目前包含三个相关名称。请有意识地使用它们：

- `Echelon Forge` 是人向项目和仓库名称。
- `EchelonForge` 是 CMake `project(...)` 标识符，除非计划进行专门的构建系统迁移，否则应保持稳定。
- `cmo` 是 `pyproject.toml` 中的遗留 Python 分发/安装标识符，为保持与可编辑安装、本地辅助脚本、缓存构建产物及下游自动化工具的兼容性而保留。

不要将 `cmo` 视为独立产品名，也不要在机会主义下重命名包 ID、CMake ID、辅助名称或脚本路径。完整的命名迁移应作为一个独立的有范围更改来处理，并附上兼容性说明和产物/缓存清理指南。

## 构建与开发

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
cmo_python -m pytest -q tests/runtime/core/test_env_config.py
```

Windows/PowerShell 示例：

```powershell
.\.venv\Scripts\python.exe -m pip install pytest numpy
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 summary
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\core\test_env_config.py
```

当前用于仓库验证的最小烟雾测试集为：

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py ef_test -j4
ctest --test-dir build-workshop -R ef_test_all --output-on-failure
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
cmo_python tools/runners/run_scenario_contract.py --suite tests/smoke/ci_contract_suite.json
```

在 Windows 上，使用 PowerShell 辅助脚本和 Windows 构建目录：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pytest numpy
cmake -S . -B build-local-win -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-local-win --target ef_core ef_py ef_test -j2
ctest --test-dir build-local-win -R ef_test_all --output-on-failure
.\tools\maintenance\cmo_env.ps1 validate
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_pytest_suite.py --suite tests\smoke\ci_smoke_suite.json
.\tools\maintenance\cmo_env.ps1 python tools\runners\run_scenario_contract.py --suite tests\smoke\ci_contract_suite.json
```

上述 Windows 路径仅限于当前本地开发工作流：烟雾测试和重点回归。它并不声称 Windows 不能运行 RL 训练；当本地依赖、运行时产物和运行输出策略就绪后，应有意启用训练工作流。

可选依赖组在 `pyproject.toml` 中声明：

- `.[test]` 声明轻量级烟雾/回归依赖集。
- `.[rl]` 添加 Gymnasium、Stable-Baselines3 和 PyTorch，用于环境/运行时导入。
- `.[train]` 添加训练栈及 TensorBoard。
- `.[world-model]` 覆盖世界模型工具。
- `.[geometry]` 添加 airframe geometry review 工具 whole-airframe alpha-shape
  contour diagnostic 所需的 SciPy 与 Shapely。
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
cmo_env_validate_rl  # 仅在运行会导入 RL 栈的回归测试前需要。
cmo_python -m pytest -q \
  tests/architecture/governance/test_cpp_include_direction.py \
  tests/architecture/build_system/test_cmake_target_readiness.py \
  tests/runtime/facade/test_runtime_facade_core.py \
  tests/world_batch/test_world_batch_runtime_surface.py \
  tests/gpu/test_gpu_runtime_bindings.py
```

如果使用不同的构建目录，请在 sourcing `tools/maintenance/cmo_env.sh` 之前导出 `CMO_BUILD_DIR=/path/to/build`，或在 Windows 上调用 `tools\maintenance\cmo_env.ps1` 之前设置 `$env:CMO_BUILD_DIR`。

## 如何浏览代码

- [src/](src/README.md)：C++ 内核、任务运行时、运行时外观、Python 绑定、GPU 辅助。
- [python/](python/README.md)：RL 运行时、训练辅助、场景编译器/运行时、诊断支持。
- [gym_envs/](gym_envs/README.md)：共享环境辅助、协作/长机支持、场景加载器。
- [scenarios/](scenarios/README.md)：按任务域分组维护的场景定义。
- [examples/](examples/README.md)：配置输入、轻量级固定装置、可视化资产和仅限示例的界面。
- [tests/](tests/README.md)：pytest 套件、契约规范、运行器和固定装置。
- [tools/](tools/README.md)：评估、诊断、运行器、维护脚本。
- [scripts/](scripts/README.md)：保留的操作人员面向的包装器和兼容性工作流外壳。
- [docs/README.md](docs/README.md)：手册、计划、标准、前瞻说明和产物索引。

执行训练使用 `build_execution_world_batch_vec_env`，由规范实现
`python.rl.runtime.world_batch.vec_env.WorldBatchVecEnv` 承载；协作执行使用
`build_cooperative_world_batch_vec_env` 和
`python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv`。
`UniversalEnv` 保留兼容导入名称，其构造函数会立即报错，不能作为训练或评估后端。

## 实现边界

下面是面向代码导航的场景输入到步结果路径：

```text
场景 JSON + profile
  -> python/scenario/compiler 和 python/scenario/runtime
  -> python/simulation 后端选择
       -> facade_batch（默认的非 RL 与 scripted 路径）
       -> 显式 world_batch（训练与评估路径）
  -> ef_py / src/runtime/facade
  -> src/core/mission 和 src/core/engine
  -> src/systems 修改 ECS 世界
  -> observation 与 result packet
  -> gym_envs 和 python/rl
  -> train.py / evaluate.py / tools / tests
```

原生代码的职责边界如下：

```text
src/runtime/facade
  -> src/core/mission
    -> src/core/engine
      -> src/systems
        -> src/models + src/components + src/content
```

- `src/core/engine` 负责规范的 CPU `SimulationKernel`、`WorldBatchRuntime`、世界步进和引擎级传输。
- `src/core/mission` 负责任务目标、奖励与终止决策，以及围绕引擎的 episode 编排。
- `src/systems` 注册 Flecs systems，并应用每个 timestep 的状态修改。
- `src/models` 存放可替换的控制、传感器、制导和 effects 实现；`src/components` 存放 ECS 状态及类型化 command/tasking 数据；`src/content` 负责静态 schema、unit 定义和加载器。
- `src/runtime/facade` 是位于 core 之上的维护型类型化 C++ 应用契约；`src/interfaces/python` 通过 `ef_py` 暴露该契约，只应承担类型转换和错误映射。
- `python/scenario/` 编译并实例化场景；`python/simulation/` 选择后端；`gym_envs/` 将运行时结果适配为 Gymnasium 风格接口；`python/rl/` 负责训练侧消费者。
- `tools/` 和 `tests/` 提供评估、诊断、契约检查和回归门禁，不应成为另一套运行时 authority。

CPU runtime 仍是规范的世界步进真值。GPU 辅助路径可以提供 packet 支持或实验能力，但不替代 CPU 路径。
`UniversalEnv` 名称仍可作为兼容性导入，但其构造函数会快速失败；维护的训练和评估应使用上面的显式
world-batch/facade 适配器。

另见：

- [src/README.md](src/README.md)
- [src/core/README.md](src/core/README.md)
- [python/README.md](python/README.md)
- [gym_envs/README.md](gym_envs/README.md)
- [架构 owner](docs/architecture/README.zh.md)
- [代码层地图](docs/operations/reference/src_layer_map.zh.md)

## 场景与实验输入

维护的场景位于 [scenarios/](scenarios/README.md)，分为：

- `takeoff/`
- `stable_flight/`
- `cruise/`
- `air_combat/`
- `naval/`
- `ground/`
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

## 训练与评估

当前根/操作人员入口点：

- `train.py`
  - 主要执行层、协同层和领导层训练入口点。
- `world_model_train.py`
  - 世界模型训练的薄兼容入口；实现位于 `_world_model_train_impl/` 与
    `python/world_model/`。
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
cmo_python tools/eval/policy_execution_eval.py \
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

- [docs/operations/reference/engine_capabilities.zh.md](docs/operations/reference/engine_capabilities.zh.md)
- [docs/operations/reference/physics_engine_inventory.zh.md](docs/operations/reference/physics_engine_inventory.zh.md)
- [docs/operations/reference/src_layer_map.zh.md](docs/operations/reference/src_layer_map.zh.md)
- [docs/reference_artifacts.zh.md](docs/reference_artifacts.zh.md)

## 规划与开放问题

尚未提升的计划和未解决缺口现在归入各自内容 owner。HMoE 设计方向位于
[docs/learning/work/issues/hierarchical_moe_execution_policy.md](docs/learning/work/issues/hierarchical_moe_execution_policy.md)，
其余路由从[文档索引](docs/README.zh.md)进入。

## 许可

项目代码和维护文档采用 [Apache License 2.0](LICENSE)。

第三方资产和仓库内捆绑的第三方文件保留其各自许可，不会被项目级 Apache-2.0
重新授权。当前本地 notice 清单见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 工作约定

- 优先使用 `.venv` 进行仓库本地验证
- 优先使用 `tools/maintenance/cmo_env.sh` 进行维护的 Linux/macOS shell 工作流
- 优先使用 `tools/maintenance/cmo_env.ps1` 进行维护的 Windows/PowerShell 工作流
- 优先使用仓库相对路径的场景路径
- 将新的训练配置文件放在明确的子目录中
- 在没有专用冻结的情况下，不要将 GPU 辅助程序视为规范的全局步进真值
- 在引入新的架构目录时添加 README 文件
