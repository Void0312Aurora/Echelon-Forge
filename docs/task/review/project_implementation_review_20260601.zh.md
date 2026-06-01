# 项目实现审查与行动评价

状态：`2026-06-01` 只读实现审查记录，基于本地代码阅读、既有验证结果和五路 subagent 实现细节分析。

范围：C++ runtime/facade/ECS/physics、Python RL/training、tests/CI/contracts、scenario/config/database、维护工具和入口脚本。

## 1. 总体评价

这个项目不是一个只有文档支撑的空架构。核心链路已经实际落地：

- C++ 侧存在 `RuntimeFacade -> WorldBatchRuntime -> SimulationKernel -> Flecs systems` 的真实执行链。
- Python 训练入口已经能把执行层、协同层、leader 层训练分别落到不同 runtime 后端。
- scenario compiler、loader、profile、world-batch vec env、contract runner 和 smoke CI 已经形成一个可运行的研究工程平台。
- Air/execution/world-batch 是当前最成熟的主线；cooperative 是值得继续押注的集成方向；naval N4 有较完整的 pre-fire 运行时边界；ground 仍偏早期 tasking shell。

但它也还不是一个可以直接对外宣称“产品级仿真平台”的状态。当前最大问题不是“没有实现”，而是：

- 多条新旧路径并存，真实主线和兼容路径没有完全隔离。
- 一些 correctness 风险藏在 runtime hot path 内，不是文档问题。
- CI gate 明显比测试资产窄，容易出现 false green。
- training/config/schema 约束偏弱，配置组合出错时可能很晚才暴露。
- 维护入口和脚本仍有历史包袱，影响新人判断主线。

我的判断：下一步不应继续大铺面新增域功能，而应先把 `world_batch/cooperative` 作为主样线，做一次 correctness hardening 和 gate 收敛。这样能让已有实现从“能跑”变成“可信地跑”。

## 2. 实现链路事实

| 链路 | 当前事实 | 评价 |
| --- | --- | --- |
| C++ runtime | `RuntimeFacade` 仍是对外方向，但 Python bindings 也暴露 `WorldBatchRuntime` 和兼容 quarantine 入口 | 主线存在，边界还没完全收口 |
| ECS/physics | `SimulationKernel` 注册 Flecs systems，exact-stage inventory 有机器可读阶段描述 | 已经具备可审计基础，但阶段顺序和真实 `ecs.progress()` 仍需 parity gate |
| Training | `train.py` 按 `agent_layer` 分 execution/cooperative/leader，world-batch execution 已是成熟路径 | 可用研究训练管线，配置约束和 resume 复现仍弱 |
| Scenario/config | Scenario compiler 支持 import/merge/cache，loader 消费 compiled scenario | 主线存在，但 schema/strict mode 不足 |
| Tests/contracts | smoke CI、pytest suites、JSON contracts 均存在 | 测试资产厚，CI 暴露薄 |
| Domain maturity | Air 最高，cooperative 有集成价值，naval N4 中高，ground 早期 | 应按成熟度推进，不宜平均用力 |
| Maintenance | `cmo_env.sh` 是较好的统一入口 | root 级旧脚本和 entrypoint 分散仍会误导 |

## 3. 分项评价

### 3.1 C++ runtime / facade / physics

评价：潜力高，但必须优先做 correctness hardening。

已经做对的地方：

- `SimulationKernel`、`WorldBatchRuntime`、`RuntimeFacade` 不是纸面概念，真实参与训练和测试。
- exact-stage inventory 给系统排序、阶段名、trace 语义留下了机器可读入口。
- `ef_core` 和 `ef_py` 能在本地构建，并由 Python 层 smoke 测试覆盖主要路径。

主要问题：

- `GroundContactSystem` 捕获裸 `IEnvironmentModel*`，而 `SimulationKernel::set_environment_model()` 可以替换 owning `unique_ptr`，存在悬垂指针风险。
- exact-stage trace 的声明顺序和实际 Flecs pipeline 仍需严格比对，尤其 `FlightControl`、`ClearForces`、`ComputeForces` 的先后关系会影响力矩/力累积。
- `ComputeForces` 在没有 primary flight control input 时直接跳过，导致 gravity 也可能被跳过。这属于物理 hot path correctness 风险。
- Python 绑定仍把较底层 runtime 暴露出来，facade 边界尚未完成治理。

### 3.2 Python RL / training

评价：已经是可用研究管线，但不是强复现训练系统。

已经做对的地方：

- `train.py` 对 execution、cooperative、leader 有清楚分支。
- execution frozen config 已经指向 world-batch vec env，是当前最成熟样线。
- leader 训练可以挂 frozen execution policy，说明系统已经进入分层控制实验阶段。

主要问题：

- frozen leader 配置声明 `execution_backend = frozen_model`，但是否使用 world-batch execution runtime 依赖额外字段。字段缺失时可能回落到 `UniversalEnv` 兼容路径。
- resume 主要依靠路径和备份文件，没有强制校验 train config、scenario、observation/action shape、runtime backend hash。
- step/reset/reward/termination 逻辑在 `UniversalEnv`、`WorldBatchVecEnv`、`CooperativeWorldBatchVecEnv`、`SingleWorldBatchRuntime` 等处重复，长期会让行为漂移。

### 3.3 Tests / CI / contracts

评价：测试资产比 CI gate 丰富很多，当前风险是 false green 和测试意图不透明。

已经做对的地方：

- GitHub CI 明确构建 `ef_core`、`ef_py` 并跑 smoke suite。
- 本地测试资产覆盖 runtime、facade、world-batch、training、eval、leader、scenario 和 JSON contracts。
- contract runner 已经形成独立执行体系。

主要问题：

- CI 只安装 `pytest` 和 `numpy`，许多 gymnasium/training 路径在 CI 中无法真实暴露。
- `run_scenario_contract.py` 遇到 `ContractSkipped` 会打印 SKIP 并继续，contract batch 容易出现 false green。
- `python/testing/contracts/env_regression.py` 使用 `copy.deepcopy`，但文件头没有 `import copy`，这是一个可以立刻修复的硬 bug。
- 测试系统缺少 checked-in focused/full suite manifest 和 contract metadata，外部读者难以区分 PR gate、manual gate、diagnostic、supplemental。

### 3.4 Scenario / config / database

评价：scenario 主线可用，但输入约束偏宽，适合研究迭代，不适合无治理扩张。

已经做对的地方：

- Scenario compiler 有 `compile_path`、`compile_data`、merge/import/cache，loader 消费 compiled scenario。
- Air profile 最成熟，naval profile 已进入 N4 pre-fire 水平，ground profile 有 tasking skeleton。
- database loader 支持目录递归加载，便于扩展单位定义。

主要问题：

- training config 大多是 `json.load` 加局部字段检查，缺少统一 schema 和 strict mode。
- database directory load 遇到单文件失败会 warn 后继续，重复定义/覆盖行为不够硬。
- scenario import path 存在重复实现路径。
- active cooperative config 仍可见 legacy observation/backend 字段，容易让主线样线混入旧路径。
- roster 对坏引用的处理偏宽松，可能静默跳过问题。

### 3.5 Domain maturity

| Domain | 当前成熟度 | 评价 |
| --- | --- | --- |
| Air / execution | 高 | 当前最适合作为主样线和 correctness gate 承载域 |
| Cooperative | 中高潜力 | 有真实 runtime 和 roster 骨架，建议作为下一阶段集成主线 |
| Naval N4 | 中高 | pre-fire bridge、station/order、contact/report 已有基础；weapon/damage outcome 仍不应宣称完成 |
| Ground | 低到中 | 当前主要是 tasking/status/static occupy/support，不能按 ground-combat runtime 评价 |
| A2 / air-combat kill model | 中 | 有 guard 和证据 scaffold，但不应让它代表整个项目成熟度 |
| Game / visualization | 探索性 | 应作为展示/实验面，不应反向决定 core runtime 架构 |

### 3.6 Maintenance / entrypoints

评价：维护工具有基础，但入口还没有完全产品化。

已经做对的地方：

- `tools/maintenance/cmo_env.sh` 是当前最可信的本地环境入口。
- build/test helper 已经降低了手动配置成本。

主要问题：

- `pyproject.toml` 没有 `[project.scripts]`，大量 CLI 仍是 root 脚本。
- `world_model_train.py` 和 `evaluate.py` 仍带有明显 legacy 风险。
- cleanup 脚本虽然默认 dry-run，但 root 范围操作需要更强 guard。
- `.gitignore` 的 `env/` 未锚定，可能让 `tests/contracts/env/` 被忽略。这是高优先级 quick fix。

## 4. 问题登记

### P0 / 应立即处理

| ID | 问题 | 影响 | 建议处理 |
| --- | --- | --- | --- |
| IMPL-001 | `GroundContactSystem` 捕获裸环境指针，`set_environment_model()` 可替换 owner | 可能出现悬垂指针，属于 C++ hot path correctness 风险 | 改为运行时查 `EnvironmentModelRef`，或在替换 model 后重建/重新注册系统，并加 regression |
| QA-003 | `env_regression.py` 缺少 `import copy` | env contract 一旦走到 deepcopy 路径会直接失败 | 立刻补 import，并加一条最小 contract/pytest 覆盖 |
| OPS-002 | `.gitignore` 中 `env/` 未锚定 | 可能误忽略 `tests/contracts/env/` 等目录 | 改成 `/env/`、`/venv/`、`/ENV/`，并确认 contract 文件可被 git 跟踪 |
| TRAIN-001 | frozen leader config/backend 组合可能回落兼容 env | leader frozen baseline 可能不是期望的 world-batch execution 路径 | frozen leader config 显式要求 world-batch runtime；构造时若 backend/config 不匹配则 fail-fast |

### P1 / 下一轮 hardening

| ID | 问题 | 影响 | 建议处理 |
| --- | --- | --- | --- |
| IMPL-002 | exact-stage inventory 与实际 Flecs pipeline 缺少 parity gate | trace 声明和真实执行可能漂移 | 建 exact-stage parity test，覆盖 force/control 系统顺序和 trace |
| IMPL-003 | `ComputeForces` 在无 primary input 时跳过 gravity | 物理基础力可能依赖控制输入存在 | 拆分 gravity/base force 与 control-dependent propulsion/aero 输入条件 |
| TRAIN-002 | resume 缺少配置/shape/backend hash | 训练恢复可复现性弱，silent mismatch 风险高 | 在 checkpoint/run metadata 写入并校验 train config、scenario、observation/action shape、runtime backend |
| TRAIN-003 | step logic 多处复制 | runtime 行为长期漂移 | 抽出共享 step contract 或单一 oracle test，先测后重构 |
| QA-001 | CI smoke 太窄 | 大量真实资产不进入 PR gate | 增加 focused CI tier 或 nightly/manual suite manifest |
| QA-002 | `ContractSkipped` 可导致 false green | 依赖缺失时合同跳过但流程仍成功 | 给 contract spec 增加 `skip_policy`，关键 contract 遇 skip 应失败 |
| CFG-001 | scenario/training/database 缺统一 schema/strict mode | 配置错误暴露晚，域扩展易漂移 | 新增 schema registry 和 strict validation path |
| CFG-003 | active config 中仍可见 legacy backend/observation 字段 | 新主线样线可能混入旧路径 | 对 active/frozen config 加 maintained backend allowlist |
| OPS-001 | `world_model_train.py` root monolith 和 legacy evaluate | 入口语义不清，维护风险高 | 给 maintained entrypoint 建 `[project.scripts]`，旧入口降级到 archive/compat |

### P2 / 治理与清理

| ID | 问题 | 影响 | 建议处理 |
| --- | --- | --- | --- |
| CFG-002 | scenario import/merge 逻辑存在重复路径 | 长期维护和行为一致性风险 | 合并 import path，保留单一 compiler service |
| CFG-004 | roster 对坏引用处理偏宽松 | 场景错误可能被静默吞掉 | strict mode 下 bad refs fail-fast |
| OPS-003 | A2 维护脚本和 artifact 生成边界需继续收口 | 容易把局部子项目状态误认为全项目状态 | 把 A2 作为 domain review，不作为全项目主评价入口 |
| OPS-004 | cleanup 脚本 root 操作 guard 仍偏弱 | 人为误操作风险 | 加 allowlist、repo-root confirmation、dry-run diff artifact |

## 5. 推荐行动顺序

### 5.1 立即修复，低成本高收益

1. 修 `.gitignore`：把 `env/`、`venv/`、`ENV/` 改成 root anchored，确认 `tests/contracts/env/` 不受影响。
2. 修 `env_regression.py`：补 `import copy`，加最小覆盖。
3. 验证并修复 `GroundContactSystem` 环境模型生命周期问题。
4. 给 frozen leader 配置/runtime 构造加 fail-fast：声明 frozen execution model 时，必须明确 backend 和 world-batch 运行方式。
5. 把一小组 contract 放入 focused CI 或新增 checked-in suite manifest，避免 smoke 代表性不足。

### 5.2 下一轮实现 hardening

1. 建 exact-stage parity test，确认 inventory、trace、Flecs 执行顺序一致。
2. 拆分 `ComputeForces` 的 gravity/base force 与 control-dependent 逻辑。
3. 为 training resume 写入并校验 config/scenario/shape/backend hash。
4. 给 JSON contracts 增加 metadata：`status`、`ci_tier`、`failure_policy`、`owner`、`realism_gate`。
5. 给 scenario/training/database 增加 strict schema path，先用于 maintained configs。

### 5.3 战略建议

下一阶段主线建议选 `world_batch + cooperative + air execution`，原因是：

- 它覆盖 C++ runtime、Python vector env、scenario loader、profile、training、contract gate，是最能暴露系统真实问题的链路。
- Air/execution 成熟度最高，适合作为 correctness baseline。
- Cooperative 能检验 roster、multi-agent、leader/execution 分层、batch runtime 和 config discipline。

不建议下一步平均推进 air/naval/ground/game/A2。那会扩大表面积，但不会解决当前最核心的可信执行问题。

## 6. 证据索引

### C++ runtime / physics

- `src/systems/physics/ground_contact_system.h:71`：`register_ground_contact_system` 接收并捕获 `IEnvironmentModel*`。
- `src/core/engine/simulation_kernel.cpp:112`：`set_environment_model()` 替换 `environment_model_` 并更新 `EnvironmentModelRef`。
- `src/core/engine/exact_stage_inventory.cpp:42`：`FlightControl` 阶段声明。
- `src/core/engine/exact_stage_inventory.cpp:45`：`ClearForces` 阶段声明。
- `src/core/engine/exact_stage_inventory.cpp:51`：`ComputeForces` 阶段声明。
- `src/systems/physics/force_system.h:72`：force system 从 control input presence 开始判断。
- `src/systems/physics/force_system.h:78`：无 primary flight control input 时直接 `continue`。
- `src/interfaces/python/bindings_runtime.cpp:2137`：Python 绑定仍暴露 `WorldBatchRuntime`。
- `src/interfaces/python/bindings_runtime.cpp:2144`：Python 绑定仍暴露 compatibility quarantine。

### Training / RL

- `train.py:356`：训练入口。
- `train.py:380`：execution layer 分支。
- `train.py:400`：world-batch vec env 构造。
- `train.py:469`：cooperative 分支。
- `train.py:523`：leader 分支。
- `examples/config/training/frozen/execution/p5_continuous_retrain_v1.json:8`：frozen execution config 的 world-batch vec env 设置。
- `examples/config/training/frozen/execution/p5_continuous_retrain_v1.json:13`：frozen execution config 的 runtime/world-batch 设置。
- `examples/config/training/frozen/leader_c2_frozen_v1.json:14`：leader env 配置。
- `examples/config/training/frozen/leader_c2_frozen_v1.json:16`：`execution_backend = frozen_model`。
- `gym_envs/leader_env_parts/execution_runtime/policy_runtime.py:39`：execution runtime 构造入口。
- `gym_envs/leader_env_parts/execution_runtime/policy_runtime.py:41`：按 `execution_world_batch_runtime` 决定是否走 world-batch runtime。
- `gym_envs/leader_env_parts/execution_runtime/policy_runtime.py:74`：frozen model policy 分支。
- `python/training/bootstrap.py:289`：resume path 处理。
- `python/training/bootstrap.py:320`：新 run 备份 train/scenario config。

### Tests / CI / contracts

- `.github/workflows/ci-smoke.yml:30`：CI Python venv 创建。
- `.github/workflows/ci-smoke.yml:34`：CI 只安装 `pytest`、`numpy`。
- `.github/workflows/ci-smoke.yml:40`：构建 `ef_core`、`ef_py`。
- `.github/workflows/ci-smoke.yml:48`：运行 smoke tests。
- `tests/smoke/ci_smoke_suite.json:3`：smoke manifest 入口。
- `tools/runners/run_scenario_contract.py:21`：scenario contract runner 参数入口。
- `tools/runners/run_scenario_contract.py:29`：捕获 `ContractSkipped`。
- `tools/runners/run_scenario_contract.py:31`：skip 后继续执行。
- `tests/runners/test_contract_batches.py:86`：contract batch runner 对 spec 分组/执行。
- `python/testing/contracts/env_regression.py:1`：文件头当前未 import `copy`。
- `python/testing/contracts/env_regression.py:484`：使用 `copy.deepcopy`。
- `python/testing/runtime.py:22`：Python runtime build dir 选择逻辑。
- `python/testing/runtime.py:91`：ef_py/runtime import 相关逻辑。

### Scenario / config / database

- `gym_envs/scenario_loader/core.py:354`：scenario loader 主加载链路。
- `gym_envs/scenario_loader/loading.py:286`：`load_scenario()` 使用 `ScenarioCompiler.compile_path()`。
- `gym_envs/scenario_loader/loading.py:334`：instantiated scenario 加载入口。
- `python/scenario/compiler/service.py:77`：`ScenarioCompiler.compile_path()`。
- `python/scenario/compiler/service.py:97`：从 JSON 文件读取 scenario。
- `python/scenario/compiler/service.py:113`：读取 merged environment config。
- `python/training/bootstrap.py:333`：training bootstrap 入口。
- `python/env_config.py:72`：env settings 默认/解析入口。
- `python/env_config.py:120`：env config 字段检查边界。
- `src/content/unit_definition_loader.cpp:645`：unit JSON parse 入口。
- `src/content/unit_definition_loader.cpp:1658`：目录加载入口。
- `src/content/unit_definition_loader.cpp:1672`：目录内逐文件 load。
- `src/content/unit_definition_loader.cpp:1677`：单文件失败 warn 后继续。
- `src/models/core/default_unit_factory.h:1528`：默认 unit factory 定义入口。

### Domain maturity

- `python/rl/profile/air_profile.py:90`：air profile 入口。
- `python/rl/profile/air_profile.py:181`：air profile observation/action 相关逻辑。
- `python/rl/profile/air_profile.py:540`：air profile 后段实现。
- `python/rl/profile/naval_profile.py:37`：naval profile 入口。
- `python/rl/profile/naval_profile.py:398`：naval profile 后段实现。
- `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json:1`：naval N4 场景样例。
- `scenarios/ground/ground_platoon_tasking_smoke_v1.json:1`：ground tasking smoke 场景。
- `scenarios/ground/ground_platoon_tasking_smoke_v1.json:66`：ground scenario 任务语义。
- `python/rl/profile/ground_profile.py:253`：ground profile 后段实现。
- `examples/config/database/ground/units/ground_platoon_mvp.json:16`：ground MVP 单位定义。
- `scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json:139`：cooperative scenario roster/combined 语义。
- `python/scenario/runtime/roster.py:20`：roster runtime 入口。
- `python/scenario/runtime/roster.py:101`：roster 解析逻辑。
- `python/rl/runtime/cooperative_world_batch_vec_env.py:174`：cooperative world-batch vec env 初始化。

### Maintenance / entrypoints

- `pyproject.toml:11`：当前只有 optional dependencies，没有 `[project.scripts]`。
- `world_model_train.py:10`：world model 训练入口文件头。
- `world_model_train.py:1949`：root 级训练脚本后段入口。
- `world_model_train.py:2216`：root 级训练脚本后段逻辑。
- `evaluate.py:35`：evaluate 入口。
- `tools/maintenance/cmo_env.sh:65`：环境 helper 主函数区域。
- `tools/maintenance/cmo_env.sh:194`：环境 helper CLI/validate 区域。
- `tools/maintenance/cleanup_redundancy.py:87`：cleanup roots 解析。
- `tools/maintenance/cleanup_redundancy.py:116`：默认 dry-run 边界。
- `tools/maintenance/cleanup_redundancy.py:120`：apply 删除开始。
- `.gitignore:14`：`env/` 未 root anchored。
- `.gitignore:75`：大产物 ignore 规则区域。
- `.gitignore:83`：game 相关 ignore 规则区域。
