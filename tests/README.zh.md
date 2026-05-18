<!-- Machine-translated draft generated on 2026-05-18 from tests/README.md. Review before treating this file as authoritative. -->

# 测试 README

`tests/` 正在围绕一组小型可复用运行程序加上 JSON 契约进行整合。

## 目标

- 减少一次性 Python 回归脚本。
- 将场景/测试意图显式以数据表示，而不是在每个文件中重新编码引导逻辑。
- 便于从 CI 或本地 shell 批量运行相关回归测试。

## 当前结构

- `runtime/`
  - 按能力域分组的运行时契约测试，位于 `air_combat/`、`core/`、`execution/`、`facade/`、`link/`、`mission/`、`multi_agent/`、`naval/` 和 `navigation/` 下。
- `eval/`
  - 维护的 CLI 级别评估回归测试。
- `training/`
  - 训练入口和训练回调回归测试。
- `hmoe/`
  - HMoE 路由、策略、引导和控制配置回归测试。
- `world_batch/`
  - 批量内核和 vec-env 适配器测试。
- `scenario/`
  - 场景编译器和空间查询测试。
- `leader/`
  - 领导者层连接和运行时控制测试。
- `runners/`
  - 用于分组 JSON 契约套件的批量运行程序。
- `support/`
  - 多个 Python 测试使用的共享假对象和帮助装置。
- `contracts/`
  - 用于契约驱动回归的 JSON 规范，按类别分组。
- `diagnostics/`
  - 剩余的探索性/调试脚本，尚未适合作为稳定契约。
  - 此文件夹不应托管稳定回归测试；一旦诊断脚本变得确定，将其迁移回 `runtime/`、`world_batch/`、`scenario/`、`leader/` 或 `contracts/`。
- `scenarios/`
  - 当内联 JSON 不实用时可复用的场景装置，例如导入的预制依赖项。

独立的 Python 测试现在应是例外，而非默认。

手动的一次性探针不应位于 `tests/` 的顶层。
如果文件主要用于人工检查而非自动回归，请优先使用 `tools/diagnostics/` 存放维护的诊断脚本，或使用 `tools/archive/` 存放仅用于参考的遗留/手动探针。

当需要独立测试时，优先考虑：

- 每个运行时或适配器边界一个专注的文件
- `tests/` 下小型内部支持模块用于共享假对象/构建器
- 直接包导入而非单文件兼容性垫片

## 实现入口点

- 契约执行逻辑现在位于 [python/testing/contracts/](../python/testing/contracts)。
- [python/testing/scenario_contract_runner.py](../python/testing/scenario_contract_runner.py) 是一个兼容性垫片，重新导出打包的契约运行程序。
- 测试使用的场景侧引导逻辑现在位于 `python/scenario/compiler/` 和 `python/scenario/runtime/` 中。
- [python/scenario_compiler.py](../python/scenario_compiler.py) 和 [python/scenario_runtime.py](../python/scenario_runtime.py) 仍是旧导入的兼容性垫片，不应视为主要实现表面。

## 契约类型

- `loader_command_chain`
  - 验证 `TaskOrder -> LeaderIntent -> PilotReport -> MissionCommand` 初始化和内核同步。
- `route_generator`
  - 验证生成的航点路线、几何形状、可达性预算、模式循环和世界偏航行为。
- `scripted_bridge`
  - 验证包装器驱动的脚本基线是否符合场景成功标准。
- `unit_regression`
  - 验证纯 Python 控制器/配置/加载器/包装器交接逻辑，无需完整场景步进。
  - 还包含参数化的领导者任务泛化检查，这些检查变异 C2 任务输入并验证发出的任务命令行为。

契约执行存在于 [python/testing/contracts/](../python/testing/contracts)，[python/testing/scenario_contract_runner.py](../python/testing/scenario_contract_runner.py) 仅作为兼容性垫片保留。

## 如何运行

直接运行一个契约：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py \
  --spec tests/contracts/chain/loader_command_chain_takeoff_to_landing.json
```

一次调用运行多个契约：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --spec \
  tests/contracts/route_generator/route_generator_v1.json \
  tests/contracts/route_generator/route_generator_waypoint_modes.json
```

运行批量运行程序：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tests/runners/test_contract_batches.py --group chain --group env

cmo_python tests/runners/test_contract_batches.py --group unit --group bridges --group route_generator

cmo_python tests/runners/test_contract_batches.py --group sim_kernel

cmo_python tests/runners/test_contract_batches.py --default-group sim_kernel

cmo_python tools/runners/run_sim_kernel_contracts.py
```

运行维护的仓库 smoke 套件：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

如果某个 smoke 路径在重构中被移动，先更新已签入的 suite manifest。CI 和顶层文档应引用这条 suite runner，而不是重复书写单个测试文件路径。

## 依赖说明

- `gymnasium` 在此工作区中是可选的。
- 实例化 `UniversalEnv` 或包装器的契约在未安装 `gymnasium` 时会打印 `SKIP`。
- 仅内核的契约（例如 `loader_command_chain` 和许多路线生成器检查）无需 `gymnasium` 即可运行。

## 编写指南

当回归主要是以下情况时，优先使用 JSON 契约：

- 一个场景
- 一个重置/步进/检查流程
- 确定性的数值或结构断言
- 重复的 `repo_root/build/PYTHONPATH` 引导

仅在确实需要以下情况时，才优先使用独立 Python 测试：

- 自定义迭代控制流
- 大量猴子补丁
- 无法通过小型虚拟契约装置捕获的非平凡模拟
- 比契约能合理编码的更丰富的诊断信息

## 命名约定

- `tests/contracts/route_generator/*.json`
  - 路线生成和路线几何回归。
- `tests/contracts/chain/*.json`
  - 命令链和内核同步回归，测试维护的加载器/运行时连接。
- `tests/contracts/bridges/*.json`
  - 脚本化包装器桥接回归。
- `tests/contracts/unit/**/*.json`
  - 纯逻辑、控制器、加载器和配置回归。
- `tests/contracts/unit/comm/*.json`
  - 命令链路、任务指令、领导者意图和领导者阶段管理器回归。
  - 包含通用核心基线契约以及兼容的空域特定通信/任务分配契约。
- `tests/contracts/unit/kernel/*.json`
  - 内核驱动的飞行回归，直接使用脚本化飞行员输入步进 `SimulationKernel`。
  - 还包含模拟护栏，用于可重复性、符号一致性、粗略物理合理性以及小型参数扫描真实性检查。
- `tests/contracts/unit/scenarios/*.json`
  - 场景模板和几何回归，验证静态 JSON 内容，无需步进环境。
- `tests/contracts/unit/training/*.json`
  - 训练/引导回归，例如安全动作偏置初始化。
- `tests/contracts/unit/wrappers/*.json`
  - 脚本化包装器模式选择、控制器交接和剩余容量回归。
- `tests/contracts/unit/world_model/*.json`
  - 回放缓冲区和世界模型数据集回归。
- `tests/contracts/bridges/*.json`
  - 脚本化包装器桥接回归。

## 当前契约文件夹

- `tests/contracts/chain/`
  - 命令链和内核同步契约。
- `tests/contracts/bridges/`
  - 脚本化包装器桥接契约。
- `tests/contracts/route_generator/`
  - 路线生成几何和预算契约。
- `tests/contracts/unit/controllers/`
  - 脚本化控制器逻辑契约。
- `tests/contracts/unit/comm/`
  - 针对任务指令、领导者意图、飞行员报告和领导者阶段转换的 C2/任务分配/命令链路契约。
  - 通用核心基线现在与此处遗留的空域特定契约并存，同时该目录正在拆分为以通用优先的系列。
- `tests/contracts/unit/config/`
  - 配置解析契约。
- `tests/contracts/unit/kernel/`
  - 直接 `SimulationKernel` 飞行回归，用于起飞、地面滑跑和稳定飞行控制律。
  - 还包含核心模拟护栏，用于可重复性、符号一致性、粗略物理合理性检查以及紧凑的现实参数扫描。
- `tests/contracts/unit/naval/`
  - 海军特定单元/运行时契约，验证舰船/领域语义，无需依赖单独的环境契约树。
- `tests/contracts/unit/scenarios/`
  - 静态场景/模板几何检查，验证任务 JSON 假设。
- `tests/contracts/unit/training/`
  - 训练时辅助契约，无需完整的场景步进。
  - 包括领导者任务参数泛化契约，这些契约变化 CAP 任务输入并检查任务代码的合理性。
- `tests/contracts/unit/wrappers/`
  - 由虚拟观察和加载器阶段驱动的包装器/控制器交接契约。
- `tests/contracts/unit/world_model/`
  - 用于离线或模仿学习支持代码的回放/数据集契约。
