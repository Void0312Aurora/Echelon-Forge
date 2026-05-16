# 架构评审后续冻结计划

状态：`2026-05-16` 冻结执行版。

关联文档：

- [项目结构与架构设计审查报告](/home/void0312/Workshop/CMO/docs/task/review/architecture_review_20260516.zh.md)
- [Code Layer Map](/home/void0312/Workshop/CMO/docs/manual/src_layer_map.md)
- [src 分层边界](/home/void0312/Workshop/CMO/src/README.md)
- [src 分层重构冻结记录](/home/void0312/Workshop/CMO/docs/plan/architecture/src_layered_refactor_freeze.zh.md)

文档定位：

- 本文档用于把架构评审中的“合理建议”收敛为一份可执行的后续任务单。
- 本文档不复述评审全文，只冻结真正采纳或部分采纳且适合继续推进的事项。
- 本文档不授权目录 rename、`SimulationKernel` public API 破坏式重写、完整 CMake target 拆分或依赖管理器迁移。

验证口径：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_env_summary
```

若后续工作触及 Python / nanobind / runtime 主线，默认使用：

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q
```

若触及 C++ / binding / CI 相关脚本，至少应补一次：

```bash
cmake -S . -B build-workshop -DCMAKE_BUILD_TYPE=Release
cmake --build build-workshop --target ef_core ef_py -j4
```

## 一、评审结论转执行口径

### 1.1 本轮明确采纳

1. 补最小 CI 自动化。
2. 继续收口工作区环境入口，在 `cmo_env.sh` 之上补显式校验能力。
3. 澄清并修复 `scenarios/` 的版本策略与 `.gitignore`/README 冲突。

### 1.2 本轮部分采纳，但不作为首批执行

1. `train.py` / `world_model_train.py` 入口膨胀问题成立。
2. CMake source group 向独立 target 的拆分方向成立。
3. `SimulationKernel` public surface 过宽问题成立。
4. `FetchContent` 依赖治理需要加强。
5. 目录命名歧义需要后续处理。

这些事项不否定方向，但当前不宜与首批 follow-up 混做一条线。

### 1.3 本轮明确暂缓

1. `src/interfaces/python -> src/bindings/python`
2. `src/gpu -> src/accelerators/gpu`
3. 直接引入 `vcpkg` / `Conan`
4. 破坏性目录 rename
5. `SimulationKernel` 多 public interface class 的一次性切分

## 二、冻结范围

本文档只冻结四个工作包：

1. `WP-A`：最小 CI smoke 基线
2. `WP-B`：`cmo_env.sh` 校验能力与文档收口
3. `WP-C`：`scenarios/` 版本策略澄清与仓库规则对齐
4. `WP-D`：`train.py` 第一阶段入口瘦身设计与最小实现冻结

本文档明确不覆盖：

1. `world_model_train.py` 全量拆分
2. CMake 多 target 全面拆分
3. `SimulationKernel` API 分裂
4. `src/components/systems` / `src/systems/systems` / `src/core/engine` rename
5. GPU/exact runtime 主线扩张

## 三、总体策略

执行顺序固定为：

1. 先把“验证基础设施”补齐，即 `WP-A` 与 `WP-B`。
2. 再处理“仓库规则冲突”，即 `WP-C`。
3. 最后才启动 `train.py` 第一阶段入口瘦身，即 `WP-D`。

原因：

1. CI 与环境校验是后续任何结构工作能否稳态推进的底座。
2. `scenarios/` 当前存在文档与 ignore 规则冲突，不先澄清会污染后续任务边界。
3. `train.py` 拆分虽然合理，但没有 CI/环境基线时回归成本偏高。

## 四、冻结工作包

### WP-A：最小 CI smoke 基线

目标：

- 为主仓建立第一条自动化质量闸门。
- 只覆盖 CPU 主线、bindings 构建和小集合核心测试。

冻结范围：

- 新增 `.github/workflows/` 下的最小 CI workflow
- 必要时允许新增极少量 CI bootstrap helper
- 允许更新 [README.md](/home/void0312/Workshop/CMO/README.md) 中的本地复现说明

推荐首批验证集合：

1. `cmake --build build-workshop --target ef_core ef_py -j4`
2. `tests/architecture/test_runtime_facade_layering.py`
3. `tests/architecture/test_cmake_target_readiness.py`
4. `tests/runtime/test_env_config.py`
5. `tests/runtime/test_runtime_facade.py`
6. `tests/world_batch/test_world_batch_runtime.py`

明确不做：

1. 不在首批 CI 中引入 CUDA matrix。
2. 不把 cooperative/HMoE 长时回归塞进首批 workflow。
3. 不要求首批 CI 覆盖所有 optional Python 依赖路线。

验收标准：

1. 仓库根目录存在可运行的最小 workflow。
2. README 中能找到本地等价复现命令。
3. workflow 只依赖当前维护主线的构建与测试入口，不额外发明旁路脚本。

当前执行记录：

1. 已新增 [ci-smoke.yml](/home/void0312/Workshop/CMO/.github/workflows/ci-smoke.yml)。
2. workflow 当前覆盖：
   - `.venv` 初始化
   - `cmake -S . -B build-workshop`
   - `cmake --build build-workshop --target ef_core ef_py`
   - `bash tools/maintenance/cmo_env.sh validate`
   - 核心 smoke pytest 集合
3. 已在 [README.md](/home/void0312/Workshop/CMO/README.md) 补充与 workflow 对应的本地复现命令。
4. 已完成本地等价 smoke 验收：
   - `source tools/maintenance/cmo_env.sh`
   - `cmo_env_validate`
   - `cmo_python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_cmake_target_readiness.py tests/runtime/test_env_config.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py`
   - 当前结果：`42 passed`

### WP-B：`cmo_env.sh` 校验能力与文档收口

目标：

- 在现有 [tools/maintenance/cmo_env.sh](/home/void0312/Workshop/CMO/tools/maintenance/cmo_env.sh) 基础上补显式校验能力。
- 进一步收口分散的 `.venv` / `CMO_BUILD_DIR` / `PYTHONPATH` 手写示例。

冻结范围：

- [tools/maintenance/cmo_env.sh](/home/void0312/Workshop/CMO/tools/maintenance/cmo_env.sh)
- [tools/maintenance/README.md](/home/void0312/Workshop/CMO/tools/maintenance/README.md)
- [README.md](/home/void0312/Workshop/CMO/README.md)
- [tools/README.md](/home/void0312/Workshop/CMO/tools/README.md)
- [tests/README.md](/home/void0312/Workshop/CMO/tests/README.md)

明确不做：

1. 不在本阶段引入复杂环境管理器。
2. 不为了统一示例去重写所有历史归档文档。
3. 不改动训练/评估代码行为本身。

验收标准：

1. `cmo_env.sh` 提供显式 validate 能力，能区分“缺 `.venv`”“缺 build”“缺 `ef_py` 产物”等常见问题。
2. 主线 README 与维护型 README 不再继续新增新的手写环境探测逻辑示例。
3. shell workflow 优先复用统一入口，而不是继续复制 build 目录探测代码。

当前执行记录：

1. 已为 [tools/maintenance/cmo_env.sh](/home/void0312/Workshop/CMO/tools/maintenance/cmo_env.sh) 增加显式 `validate`/`summary`/`python` 脚本模式。
2. `validate` 现可区分以下常见失败：
   - 缺少 `.venv/bin/python`
   - 缺少可用 build 目录
   - build 目录存在但缺少 `ef_py` 产物
3. 已将 [README.md](/home/void0312/Workshop/CMO/README.md) 中主线训练、评估、contract、pytest 示例收口到 `source tools/maintenance/cmo_env.sh` + `cmo_env_validate` + `cmo_python ...`。
4. 已更新 [tools/maintenance/README.md](/home/void0312/Workshop/CMO/tools/maintenance/README.md) 记录统一入口与脚本模式。
5. 已将 [.github/workflows/ci-smoke.yml](/home/void0312/Workshop/CMO/.github/workflows/ci-smoke.yml) 的环境校验步骤切换为 `bash tools/maintenance/cmo_env.sh validate`。

### WP-C：`scenarios/` 版本策略澄清与仓库规则对齐

目标：

- 解决 `.gitignore` 与 README 对 `scenarios/` 定位冲突的问题。
- 明确 `scenarios/`、`experiments/`、`datasets/`、`output/` 的差异化策略。

冻结范围：

- [.gitignore](/home/void0312/Workshop/CMO/.gitignore)
- [README.md](/home/void0312/Workshop/CMO/README.md)
- [scenarios/README.md](/home/void0312/Workshop/CMO/scenarios/README.md)
- 必要时允许新增一份简短的 artifact / scenario 策略说明文档

默认方向：

1. `scenarios/` 作为维护主线输入，应与当前文档口径一致并可被版本追溯。
2. `experiments/`、`datasets/`、`output/` 继续保持忽略，除非另起专项计划。

明确不做：

1. 不把训练 checkpoint 和大体积产物直接纳入主仓。
2. 不在本阶段同时解决全部 artifact 管理问题。
3. 不强行引入 Git LFS 作为前置条件。

验收标准：

1. README、`.gitignore` 与 `scenarios/` 的角色说明彼此一致。
2. 仓库对“什么是主线输入、什么是运行产物”的口径清楚。
3. 若选择不取消 ignore，必须在文档中显式写出外部版本策略；不得继续保持“文档说维护、仓库却忽略”的状态。

当前执行记录：

1. 已更新 [.gitignore](/home/void0312/Workshop/CMO/.gitignore)，取消 `scenarios/` ignore，并保留 `experiments/`、`datasets/`、`output/` 为默认忽略的运行产物目录。
2. 已在 [README.md](/home/void0312/Workshop/CMO/README.md) 增补仓库保留策略摘要，明确：
   - `scenarios/` 与 `examples/config/` 属于版本管理的主线输入
   - `experiments/`、`datasets/`、`output/` 属于运行/产物工作区
3. 已更新 [scenarios/README.md](/home/void0312/Workshop/CMO/scenarios/README.md)，把 `scenarios/` 明确为 git 追踪的 canonical 输入面，并补充“仅服务单次实验的 scenario 不应提升为主线 scenario”的保留边界。
4. 已更新 [docs/reference_artifacts.md](/home/void0312/Workshop/CMO/docs/reference_artifacts.md)，补充 repo input 与 artifact workspace 的边界说明，避免后续再次把运行目录误当作长期主线来源。

### WP-D：`train.py` 第一阶段入口瘦身

目标：

- 先对 [train.py](/home/void0312/Workshop/CMO/train.py) 做第一阶段瘦身。
- 把 CLI 解析/调度与训练主循环/环境构造的核心逻辑分离。

冻结范围：

- [train.py](/home/void0312/Workshop/CMO/train.py)
- 允许新增 `python/training/` 或等价主线子包
- 允许更新训练入口相关 README 与最小 smoke 测试

明确不做：

1. 不在本阶段同步重写 [world_model_train.py](/home/void0312/Workshop/CMO/world_model_train.py)。
2. 不改变现有 `train.py` CLI 参数表面。
3. 不借此把 `python/rl/`、`gym_envs/`、callback 全面重构一遍。

验收标准：

1. `train.py` 仍保持现有 CLI 入口与主要参数兼容。
2. 新增的训练子域承担明确的 bootstrap / orchestration 责任，而不是再次形成新的大平面文件。
3. 至少补一条聚焦 smoke，证明原入口仍能完成参数解析与训练 bootstrap。

停止条件：

- 一旦拆分开始要求同步大规模改写 `world_model_train.py`、`gym_envs/` 或 cooperative runtime，即停止并另起专项计划。

当前执行记录：

1. 已新增 [python/training/](/home/void0312/Workshop/CMO/python/training/README.md) 子域，作为 `train.py` 第一阶段入口瘦身的承接位置。
2. 已将 `train.py` 的以下入口职责下沉到新子域：
   - CLI 参数表
   - scenario / train_config 路径校验
   - `agent_layer` 解析与 leader 入口类装载
   - 实验目录、resume / interrupted checkpoint、backup、lock 文件处理
   - seed 与 PyTorch runtime bootstrap
   - 训练开始前的统一运行时摘要打印与 execution visual rollout memory warning
3. [train.py](/home/void0312/Workshop/CMO/train.py) 现保留：
   - vec-env/backend 构造
   - SB3/AdaptiveKLPPO 模型创建与 checkpoint 初始化
   - callback / probe / learn / save 主循环
4. 已新增聚焦 bootstrap 的 smoke 测试 [tests/training/test_train_bootstrap.py](/home/void0312/Workshop/CMO/tests/training/test_train_bootstrap.py)。
5. 已验证 `train.py` CLI 表面兼容仍保持可用：
   - `cmo_python train.py --help`
   - `cmo_python -m pytest -q tests/training/test_train_bootstrap.py`
   - `cmo_python -m pytest -q tests/training/test_train_entry_cooperative.py`

## 五、后续但不在本文档内执行

以下事项保留为后续候选，不进入本计划实现范围：

1. CMake 多 target 渐进拆分
2. `SimulationKernel` 更窄接口抽取
3. 目录命名歧义 rename
4. `FetchContent` → package manager 迁移
5. `world_model_train.py` 大文件拆分

这些项如果要继续推进，必须另起新的冻结任务单。
