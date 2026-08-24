# 测试 README

`tests/` 正在围绕一组小型可复用运行程序加上 JSON 契约进行整合。

## 目标

- 减少一次性 Python 回归脚本。
- 将场景/测试意图显式以数据表示，而不是在每个文件中重新编码引导逻辑。
- 便于从 CI 或本地 shell 批量运行相关回归测试。

## 当前结构

- `runtime/`
  - 按能力域与共享 surface 分组的运行时契约测试，位于 `air_combat/`、`bindings/`、`core/`、`engagement/`、`execution/`、`facade/`、`ground/`、`link/`、`mission/`、`multi_agent/`、`naval/` 和 `navigation/` 下。
- `architecture/`
  - 源码/文档护栏和治理检查，与运行时行为测试有意分离。
  - 拆分为默认守卫层与按需 `governance_audit` 审计层；见下文"架构测试分层"。
  - 通过一层语义子目录显式标出 guard owner：`build_system/`、
    `causal_runtime/`、`command_tasking/`、`compatibility_quarantine/`、
    `damage_model/`、`governance/`、`ground/`、`platform_spawn/`、
    `policy_execution/`、`runtime_facade/`、`runtime_profiles/`、
    `runtime_spine/` 和 `structural_boundaries/`。
  - 文件名应优先描述架构不变量。WP/A2 等历史工作包标签只在追溯必要时保留在
    测试名、注释或任务文档中；`RES`、`TP21`、`BECO` 这类残差/来源标签若属于
    被守护的领域契约，可以继续保留。
- `eval/`
  - 维护的 evaluation CLI 契约，覆盖 policy-loading、runtime-entry 和领域基线 probe。
- `training/`
  - 训练 bootstrap/CLI 契约、active-entry gate、诊断回调契约和确定性的
    fault-localization probe。
- `policy/`
  - 策略路由、执行策略 surface、辅助训练更新、事件时序标签、
    grouped-stopping loss、引导和控制配置回归测试。
- `world_batch/`
  - 批量内核和 vec-env 适配器测试。
- `scenario/`
  - 场景编译器、环境基底/投影契约、场景生成契约和空间查询测试。
- `leader/`
  - leader tasking profile、command-field projection、phase-control 和
    runtime-control 测试。
- `runners/`
  - 用于分组 JSON 契约套件的批量运行程序。
- `support/`
  - 多个 Python 测试使用的共享假对象和帮助装置。
- `contracts/`
  - 用于契约驱动回归的维护态 JSON 规范，按类别分组。
  - 仅为追溯保留的历史规范属于 `archive/contracts/`，不属于此维护根目录。
- `archive/`
  - 仅为追溯保留的历史测试资产。
  - 这些文件不属于活跃 pytest 或 JSON contract 覆盖；只有移回维护态测试 surface 并加入相关 matrix 或 suite 后，才应重新视为活跃覆盖。
- `suites/`
  - 建议性的 suite 治理元数据，以及签入的架构分层 manifest
    （`architecture_guard_suite.json`、`governance_audit_suite.json`）。
  - 这些文件本身不会改变 CI wiring。
- `diagnostics/`
  - 仅用于临时探索性诊断。
  - 由 diagnostics 稳定下来的回归应进入拥有该能力的测试域，例如
    `runtime/`、`training/`、`world_batch/`、`scenario/`、`leader/`、
    `bindings/`、`link/` 或 `contracts/`。
- `gpu/`
  - GPU 运行时绑定和 CUDA 集成回归测试。与 `src/gpu/` 和 Python GPU bindings 对齐。
  - GPU 测试默认通过 `EF_ENABLE_CUDA_EXPERIMENTS` 门控；CUDA 不可用时应优雅跳过。
- `scenarios/`
  - 当内联 JSON 不实用时可复用的场景装置，例如导入的预制依赖项。

独立的 Python 测试现在应是例外，而非默认。

手动的一次性探针不应位于 `tests/` 的顶层。
如果文件主要用于人工检查而非自动回归，请优先使用 `tools/diagnostics/` 存放维护的诊断脚本；仅用于参考的遗留/手动探针应直接删除并在 `tools/README.md` 的退役登记中留一行（git 历史即归档）。

当需要独立测试时，优先考虑：

- 每个运行时或适配器边界一个专注的文件
- `tests/` 下小型内部支持模块用于共享假对象/构建器
- 直接包导入而非单文件兼容性垫片

## 实现入口点

- 契约执行逻辑现在位于 [python/testing/contracts/](../python/testing/contracts)。
- 测试使用的场景侧引导逻辑现在位于 `python/scenario/compiler/` 和 `python/scenario/runtime/` 中。
- raw batch 场景 setup diagnostics wrapper 已移除；测试应直接导入 `python/scenario/runtime/` 的 maintained setup helper。

## 契约类型

- `loader_command_chain`
  - 验证 `TaskOrder -> LeaderIntent -> PilotReport -> MissionCommand` 初始化和内核同步。
- `route_generator`
  - 验证生成的航点路线、几何形状、可达性预算、模式循环和世界偏航行为。
- `unit_regression`
  - 验证纯 Python 控制器/配置/加载器/包装器交接逻辑，无需完整场景步进。
  - 还包含参数化的领导者任务泛化检查，这些检查变异 C2 任务输入并验证发出的任务命令行为。

契约执行存在于 [python/testing/contracts/](../python/testing/contracts)。

## 契约批量失败策略

`tests/runners/test_contract_batches.py` 当前通过已签入路径的 glob 解析批量分组。如果被选中的 glob 为空，或任一被选中的契约失败，批量运行都会以非零退出。也就是说，当前 batch runner 对被选中文件执行的是操作层面的 hard-fail。

这种执行行为不同于契约本身希望表达的语义层级。`gating`、`frozen`、`supplemental`、`diagnostic` 和 `archive` 等层级仍需要 metadata 或 manifest 承接，runner 才能按不同 failure policy 执行。在该层落地前，路径位置和 README 文本只是文档说明；它们不会软化已选 batch 的失败。

对于 `unit/kernel` 契约，当前应明确区分稳定 gate 检查与 diagnostic/supplemental realism scan。`sim_kernel` batch 目前会 glob 全部 `tests/contracts/unit/kernel/*.json`，因此被选中的诊断扫描在操作上仍会 hard-fail。不要把这解读为已校准的验收决策；只有在 metadata/manifest 中明确 ownership 和 failure policy 后，扫描才应提升为 gate。

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

运行维护的契约 smoke 套件：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_scenario_contract.py --suite tests/smoke/ci_contract_suite.json
```

运行批量运行程序：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_contract_batches.py --group chain --group route_generator

cmo_python tools/runners/run_contract_batches.py --group unit --group same_process

cmo_python tools/runners/run_contract_batches.py --group sim_kernel

cmo_python tools/runners/run_contract_batches.py --default-group sim_kernel
```

`sim_kernel` 默认分组只是 `tests/contracts/unit/kernel/*.json` 的便利包装；它还不是能够区分 gate、supplemental 和 diagnostic 契约的语义 manifest。

运行维护的仓库 smoke 套件：

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
```

Pytest suite manifest 可以列目录、文件，或
`tests/architecture/runtime_facade/test_runtime_escape_hatches.py::test_runtime_facade_escape_hatch_is_documented`
这类 pytest node ID。当一个宽 guard 文件里只有少量 smoke-safe 子集应进入 CI gate 时，优先使用 node ID。
CI smoke 应优先列显式文件或 node ID，而不是目录条目，避免新增测试被意外提升进 CI。

Suite tier 含义：

- `smoke`
  - 快速、高信号、可以作为 CI gate 的检查。
- `focused`
  - 面向具体领域的小型套件，用于本地 pre-merge 检查和目标化 owner review。
- `local`
  - 开发者本地运行的套件，可能比 focused 更宽或更依赖环境。
- `manual`
  - 需要人工判断或特殊设置的人为触发检查、诊断或工作流。
- `nightly`
  - 稳定后可考虑进入定时自动化的长耗时或宽覆盖回归候选。

`tests/suites/` 此前存放咨询性治理矩阵（`test_system_matrix.json`、`contract_system_matrix.json`）和草稿 `focused_runtime_suite.json`。这些文件已被移除：它们没有被任何 runner 或 CI 步骤引用，且跨文件一致性由元测试而非行为来保证。当前 CI 会运行维护态 pytest smoke 套件、C++ CTest smoke 目标，以及维护态 JSON 契约 smoke 套件。

如果某个 smoke 路径在重构中被移动，先更新 `tests/smoke/ci_smoke_suite.json`。CI 和顶层文档应引用这条 suite runner，而不是重复书写单个测试文件路径。对于 node ID 条目，runner 会先检查基础文件路径，再把完整 node ID 交给 pytest。

## 架构测试分层

`tests/architecture/` 中混有两类失败受众不同的门禁，现通过 pytest marker
拆分，使默认开发回归不再为证据审计买单：

- **守卫层（默认，无标记）。** 普通代码变更就能破坏的代码结构性质：
  include 方向、runtime facade 收口边界、分层/领域边界、information-state
  truth-read 禁令、DTO/schema 与生成物一致性、census/inventory 棘轮，以及
  在线门禁工具的 fail-closed 行为。这些测试在每次默认 pytest 调用中继续运行。
- **治理审计层（`governance_audit` 标记）。** 证据与流程门禁：证据文档与
  retained manifest、admission / signoff / provenance / release closeout
  工作流、文档健康度（链接、双语一致、信息架构、内容 pin），以及仓库自动化
  workflow pin。每个文件带有模块级
  `pytestmark = pytest.mark.governance_audit`；marker 注册在
  `pyproject.toml`。CUDA 证据模块退役后，不再需要 collection-time marker 例外。

判定规则：测试对象是代码的结构性质（普通代码变更可使其变红）→ 守卫层；
测试校验的是证据文档、签入清单、来源/签核/溯源记录或文档健康度 → 审计层。
拿不准的文件默认归守卫层。

默认回归入口 —— 通过 suite runner 运行签入的分层 manifest：

```bash
source tools/maintenance/cmo_env.sh

# 开发回归（仅守卫层）
cmo_python tools/runners/run_pytest_suite.py --suite tests/suites/architecture_guard_suite.json

# 治理/证据审计层（按需）
cmo_python tools/runners/run_pytest_suite.py --suite tests/suites/governance_audit_suite.json
```

默认循环请优先用守卫层 manifest，而不是 `-m "not governance_audit"`。marker
反选并不能省下审计层的 import 开销：pytest 必须先 import 模块才能读到该模块的
`pytestmark`，所以 `-m "not governance_audit"` 仍会收集审计层模块，只是跳过
运行其中的测试。manifest 按文件路径选择，审计层模块根本不会被 import。

marker 仍是层级归属的权威定义，需要在显式路径上按 marker 切片时继续使用：

```bash
# 仅守卫层
pytest -m "not governance_audit" tests/architecture

# 仅治理/证据审计层
pytest -m governance_audit tests/architecture
```

`tests/runners/test_pytest_suite_manifests.py` 中的元测试保证两份 manifest
无重复条目、互斥、完整覆盖 `tests/architecture` 全部测试文件，并与真实的
`pytest --collect-only -m governance_audit` 收集结果保持锁步，
使层级归属变更必须通过显式的 manifest 编辑完成。CI smoke 套件列出显式文件
与 node ID，不受 marker 拆分影响：已提升进 smoke 的条目即使所属文件位于审计
层，也继续作为 CI gate 运行。

## 依赖说明

- `gymnasium` 在此工作区中是可选的。
- 活跃维护的 contract batch 应避免 raw `UniversalEnv` 构造；历史 raw-env 规范已在测试系统整合中退出工作树，可从 git 历史找回。
- 仅内核的契约（例如 `loader_command_chain`）和路线生成器检查无需 `gymnasium` 即可运行。

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

## 面向功能能力的测试文件规范

测试文件是能力/契约容器，不是子项目、工作包、阶段或一次性评审流程的收据。
只有当一个文件拥有稳定的功能 surface，或确实需要不同的执行模型时，才应新增
测试文件。

优先使用一个语义文件覆盖同一能力下的多个场景，并在文件内部通过测试函数、
参数化、fixture 和共享 helper 扩展覆盖面。不要因为某个任务、残差项、阶段、
候选包或归档工作包需要额外 checkpoint，就顺手创建一个新文件。

拟新增的独立文件至少应满足以下条件之一：

- 它守护一个无法自然并入现有文件的新能力边界。
- 它需要不同的 runner、环境层级、生成物生命周期或 fixture shape。
- 拆分后能避免既有文件变成 setup、失败语义互不相关的宽混合 guard。

否则，应把新场景加入既有能力文件。少于三到五个测试的小文件默认应视为合并
候选，除非它们有独立执行层级、昂贵 setup，或有意隔离的 failure policy。

当多个文件共享大部分 imports、工具入口、artifact root、retained manifest
逻辑、fail-closed 语义或 CI/local suite 层级时，应优先合并。如果能力文件
变得过大，也应按能力子面拆分，而不是按工程代号或任务编号拆分。

`A2`、`WP`、`RES`、`TP21`、`BEC-O`、`Stage B/C` 等历史标识只应在追溯
必要时放入测试名、参数 ID、注释、fixture 或任务文档。文件名应保持语义化，
优先使用
`test_<capability>_<contract|governance|admission|guardrails|validation|artifacts>.py`
这类形式。

进入 CI 或 focused suite 应通过 suite manifest 或 pytest node ID 完成。不要
为了方便 promotion/exclusion 而新建一个物理测试文件。

## 命名约定

- `tests/contracts/route_generator/*.json`
  - 路线生成和路线几何回归。
- `tests/contracts/chain/*.json`
  - 命令链和内核同步回归，测试维护的加载器/运行时连接。
- `tests/contracts/unit/**/*.json`
  - 纯逻辑、控制器、加载器和配置回归。
- `tests/contracts/unit/comm/*.json`
  - 命令链路、任务指令、领导者意图和领导者阶段管理器回归。
  - 包含通用核心基线契约以及兼容的空域特定通信/任务分配契约。
- `tests/contracts/unit/kernel/*.json`
  - 内核驱动的飞行回归，直接使用脚本化飞行员输入步进 `SimulationKernel`。
  - 还包含模拟护栏，用于可重复性、符号一致性、粗略物理合理性以及小型参数扫描真实性检查。
  - 在 metadata/manifest failure policy 明确前，将稳定护栏视为 gate 候选，将紧凑 realism scan 视为 supplemental 或 diagnostic。
- `tests/contracts/unit/env/*.json`
  - 环境辅助与 leader-training-env 契约，用于验证 env-side setup、randomization、scripted/frozen model guard、phase 与 curriculum 行为，而不放入完整 scenario env tree。
- `tests/contracts/unit/ground/*.json`
  - 早期 ground tasking/bootstrap 线的 ground profile、common-core、task-order 与 support-relationship 契约。
- `tests/contracts/unit/scenarios/*.json`
  - 场景模板和几何回归，验证静态 JSON 内容，无需步进环境。
- `tests/contracts/unit/training/*.json`
  - 训练/引导回归，例如安全动作偏置初始化。
- `tests/contracts/unit/wrappers/*.json`
  - 脚本化包装器模式选择、控制器交接和剩余容量回归。
- `tests/contracts/unit/world_model/*.json`
  - 回放缓冲区和世界模型数据集回归。

## 当前契约文件夹

- `tests/contracts/chain/`
  - 命令链和内核同步契约。
- `tests/contracts/route_generator/`
  - 路线生成几何和预算契约。
- `tests/contracts/unit/controllers/`
  - 脚本化控制器逻辑契约。
- `tests/contracts/unit/comm/`
  - 针对任务指令、领导者意图、飞行员报告和领导者阶段转换的 C2/任务分配/命令链路契约。
  - 通用核心基线现在与此处遗留的空域特定契约并存，同时该目录正在拆分为以通用优先的系列。
- `tests/contracts/unit/config/`
  - 配置解析契约。
- `tests/contracts/unit/env/`
  - 环境辅助与 leader-training-env 单元契约。
- `tests/contracts/unit/ground/`
  - 早期 ground 线的 ground-specific profile/tasking/common-core 契约。
- `tests/contracts/unit/kernel/`
  - 直接 `SimulationKernel` 飞行回归，用于起飞、地面滑跑和稳定飞行控制律。
  - 还包含核心模拟护栏，用于可重复性、符号一致性、粗略物理合理性检查以及紧凑的现实参数扫描。
  - 当前 batch 执行不区分 gate 与 diagnostic 语义；被 `sim_kernel` 选中的契约仍会 hard-fail，直到 metadata/manifest 层落地。
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
