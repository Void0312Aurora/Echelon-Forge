# 项目结构与架构设计审查报告

状态：`2026-05-16` 已完成首次全量审查；`2026-05-16` 已补充处理批注
范围：C++ 内核、ECS 组件体系、运行时分层、Python 训练基础设施、构建系统、文档与测试

关联后续计划：

- [架构评审后续冻结计划](architecture_review_followup_freeze_20260516.zh.md)

## 1. 背景

本文档基于对仓库的首次全面审查，覆盖 `src/`、`python/`、`gym_envs/`、`tests/`、`tools/`、`docs/`、构建配置等各层级的设计评价。目标是识别当前架构的优势、风险和待改进项，并冻结一份可追踪的问题清单。

## 2. 审查范围

- `src/` — C++ ECS 内核、分层边界、facade contract
- `python/` — RL 运行时、训练入口、policy/tasking
- `gym_envs/` — Gymnasium 环境封装与 scenario loader
- `tests/` — 测试覆盖与架构测试
- `docs/` — 文档体系完整性
- `CMakeLists.txt` — 构建系统与依赖管理
- `.gitignore` — 版本控制范围

## 3. 架构优势

### 3.1 分层依赖方向清晰且可测试执行

依赖方向：

```text
interfaces/python → runtime/facade → core/engine + core/mission
    → systems → models / components / content
```

- [src/README.md](../../../src/README.md) 和各层级 README 明确定义了每层允许放什么、禁止放什么
- [docs/plan/architecture/src_layered_refactor_freeze.zh.md](../../plan/architecture/src_layered_refactor_freeze.zh.md) 冻结了 WP1-WP7 的执行记录
- [tests/architecture/test_runtime_facade_layering.py](../../../tests/architecture/test_runtime_facade_layering.py) 和 [test_cmake_target_readiness.py](../../../tests/architecture/test_cmake_target_readiness.py) 将架构约束变成自动验证

评价：研究代码库中将架构约束可测试化极为罕见，是最大亮点。

### 3.2 Facade 模式收口合理

[RuntimeFacade](../../../src/runtime/facade/runtime_facade.h) 是 C++ 层唯一对外 contract，提供 typed request/result 接口：
- `BatchWorldSetupRequest` / `BatchWorldSetupResult`
- `ExecutionBatchStepRequest` / `ExecutionBatchStepResult`
- `ObservationBatchRequest` / `ObservationBatchPacket`

Python 侧通过 `_RuntimeFacadeAdapter` 集中适配，`WorldBatchRuntime` 直接访问被架构测试禁止扩散到 adapter 之外。

### 3.3 ECS (Flecs v4.0) 选型契合领域

空战仿真涉及大量异构实体（飞机、导弹、传感器、通信链路），Flecs 的 system ordering + pipeline 天然匹配分阶段执行模式。`SimulationKernel` 的 `exact_stage_inventory` 将 pipeline 阶段显式化，为 GPU migration 提供清晰地图。

### 3.4 Command/Tasking 语义拆分

将原本混在 `components/physics/action.h` 的 DTO 拆为：
- `components/command/` — 底层指令（PilotAction、MissionCommand、CommandLink）
- `components/tasking/` — 高层任务语义（TaskOrder、LeaderIntent、PilotReport）
- 每个子域再分 `common/`、`air/`、`naval/`

与 HMoE 设计文档中的 `TaskOrder → LeaderIntent → MissionCommand → execution-layer control` 路由层级完全对应。

### 3.5 文档体系系统化

| 目录 | 职责 |
|------|------|
| `docs/manual/` | 当前维护主线的代码地图和能力清单 |
| `docs/plan/` | 架构冻结计划和执行工作包 |
| `docs/forward/` | 未排期的前瞻设计 |
| `docs/standards/` | 编码和设计标准 |
| `docs/task/` | 短生命周期任务文档 |

[src_layer_map.md](../../manual/src_layer_map.md) 提供"问题→定位指南"——按问题类型指引该去哪个目录看代码。

### 3.6 实验管理与归档

- `experiments/` 按 `YYYYMMDD_purpose` 命名规范
- `examples/config/training/` 分 `active/` 和 `frozen/`
- `tools/archive/` 专门归档旧诊断脚本

---

## 4. 待改进项（按优先级排列）

### 4.1 🔴 缺少 CI/CD 配置

**位置**：仓库根目录

**现象**：没有 `.github/workflows/` 或任何 CI 配置文件。仓库有 50+ 测试文件，C++ 和 Python 双语言混合构建，但缺乏自动化验证管道。

**影响**：
- PR 合入前无自动化质量闸门
- 多平台构建兼容性（Linux only? CUDA 变体?）无检查
- 回归只能靠人工

**建议**：优先补最小 CI（build ef_core + ef_py → pytest 核心套件），后续扩展 matrix build。

**处理批注（`2026-05-16`）**：

- 采纳。
- 当前仓库确实缺少任何 CI 定义；这一点与现有测试规模、C++/Python 双构建现实不匹配。
- 后续执行应先以 Linux 主线最小 smoke 为第一阶段，不默认把 CUDA matrix、长时训练或 cooperative/HMoE 大回归纳入首批 CI。

### 4.2 🟡 CMake target 拆分尚未执行

**位置**：[CMakeLists.txt](../../../CMakeLists.txt)

**现象**：虽然 `CMakeLists.txt` 已定义 `EF_CORE_ENGINE_SOURCES`、`EF_CORE_MISSION_SOURCES` 等 source group，但最终全部打入单个 `ef_core` 静态库。

**影响**：
- 任何 `.cpp` 修改导致 `ef_core` 全量重编译
- 无法在 CMake link-time 层面强制依赖方向
- WP7 候选 target 顺序已明确但未执行：`ef_components → ef_models → ef_systems → ef_mission_runtime → ef_sim_core → ef_runtime_facade`

**建议**：作为 FP2（Freeze Plan 2）执行，将 source group 逐个拆为独立 CMake target。

**处理批注（`2026-05-16`）**：

- 部分采纳。
- `source group 已定义但 target 尚未拆` 这一事实判断成立。
- 但不建议把它作为当前最先执行的 follow-up 主线，也不建议一次性按文中列出的 target 链整体落地。
- 更合理的策略是：先完成 CI 与入口/版本策略收口，再单独冻结一份渐进式 target split 计划。

### 4.3 🟡 `SimulationKernel` public API 过于宽泛

**位置**：[src/core/engine/simulation_kernel.h](../../../src/core/engine/simulation_kernel.h)

**现象**：头文件约 200 行、50+ public 方法，同时承担生命周期、工厂注入、环境配置、命令注入（三套接口）、观测查询、武器发射、exact-stage trace 等各类职责。

**影响**：
- 违反 Interface Segregation 原则
- 单元测试需要 mock 整个 kernel
- 新增能力时找不到合理归属

**建议**：拆分为 `SimulationKernel`（生命周期）+ `KernelCommandInterface` + `KernelObservationInterface` + `KernelEnvironmentInterface`，由 facade 组合。

**处理批注（`2026-05-16`）**：

- 部分采纳。
- `SimulationKernel` 的 public surface 过宽这一诊断成立。
- 但当前不建议直接引入多套新的 public interface class，因为这会同时波及 binding、tests 与现有 owner 语义。
- 更稳的路线应是：先保持 `SimulationKernel` 作为 owner，不破坏现有 public name，再逐步把命令、观测、环境相关实现下沉到更窄的 helper / adapter / facade 组合层。

### 4.4 🟡 Python 入口脚本过大

**位置**：
- [train.py](../../../train.py) — 1127 行
- [world_model_train.py](../../../world_model_train.py) — 约 3000+ 行

**现象**：顶层入口脚本混合了参数解析、环境构建、训练循环、回调注册、checkpoint 管理等多种职责。

**影响**：
- 新增训练模式需要修改全局入口
- 训练循环逻辑无法在 `python/rl/` 内部复用
- 代码导航困难

**建议**：将训练循环核心逻辑下沉到 `python/rl/training/`（新子域），顶层 `train.py` 只做 CLI 解析和调度。

**处理批注（`2026-05-16`）**：

- 部分采纳，且判断问题本身成立。
- [train.py](../../../train.py) 与 [world_model_train.py](../../../world_model_train.py) 的确已经超过“单入口脚本”应承载的复杂度。
- 但具体落点不宜机械统一为 `python/rl/training/`：
  - `train.py` 更适合下沉到通用 `python/training/` 或等价主线包；
  - `world_model_train.py` 更适合在 `python/world_model/` 下形成独立训练子域。
- 当前适合先冻结 `train.py` 的第一阶段收口，不与 `world_model_train.py` 的大规模重构绑定推进。

### 4.5 🟢 目录命名存在歧义

**位置**：
- `src/components/systems/`
- `src/systems/systems/`
- `src/core/engine/`

**现象**：
- 嵌套 `systems` 含义不清，`components/systems` 实际是"平台系统组件（sensor/comm/navigation）"，`systems/systems` 是"平台系统的每帧 mutation 逻辑"
- `core/engine` 容易与 facade/runtime engine 概念混淆

**影响**：新人（或 AI agent）持续产生认知困惑。

**建议**：冻结文档已标记为开放问题。建议：
- `components/systems` → `components/platform`
- `systems/systems` → `systems/platform`
- `core/engine` → `core/sim`

**处理批注（`2026-05-16`）**：

- 部分采纳。
- “命名歧义存在”这一点判断准确，尤其是 `components/systems` 与 `systems/systems`。
- 但“纯 rename、低风险”这一风险评估过于乐观；真实代价会覆盖 include 路径、README、测试与冻结文档。
- 当前不把目录 rename 作为首批 follow-up 主线。若后续执行，应单独冻结，并优先处理最容易误导阅读的一个点，而不是三处一起改。

### 4.6 🟢 外部依赖通过 FetchContent 即时下载

**位置**：[CMakeLists.txt:20-49](../../../CMakeLists.txt)

**现象**：
```cmake
FetchContent_Declare(flecs GIT_TAG v4.0.0)
FetchContent_Declare(spdlog GIT_TAG v1.13.0)
FetchContent_Declare(nanobind GIT_TAG v1.9.2)
FetchContent_Declare(nlohmann_json GIT_TAG v3.11.3)
```

**影响**：
- 离线环境不可构建
- 依赖版本分散在 CMakeLists.txt 中，无集中管理
- 无 hash 校验（FetchContent 不校验内容完整性）

**建议**：考虑 vcpkg manifest 或 Conan。最低成本方案是添加 CMake `FetchContent_Declare` 的 `URL_HASH` 参数。

**处理批注（`2026-05-16`）**：

- 部分采纳。
- 当前 `FetchContent` 路线的离线构建与依赖治理问题判断成立。
- 但这里的“最低成本方案”表述需要修正：现有写法是 `GIT_REPOSITORY + GIT_TAG`，并不直接适配 `URL_HASH`。
- 更现实的近期修正是：
  - 先把第三方依赖从 tag pin 收紧到 commit SHA pin；
  - 后续若真的需要 hash 校验，再转成 archive URL 或引入包管理器。
- `vcpkg/Conan` 应保留为后续评估项，而不是本轮立即落地的执行项。

### 4.7 🟢 `.gitignore` 排除了关键开发目录

**位置**：[.gitignore](../../../.gitignore#L56-L63)

**现象**：`scenarios/`、`datasets/`、`experiments/`、`output/` 被 gitignore 完全排除。

**影响**：
- `scenarios/`：场景定义无版本追溯。如果场景通过其他渠道管理，需在 README 中说明
- `experiments/`：训练运行记录无 git 历史，无法从提交记录恢复"某次训练用了什么配置和种子"

**建议**：区分处理：
- `scenarios/` 可能值得取消 gitignore（或建立独立的 scenarios 仓库和版本化引用）
- `experiments/` 考虑用 Git LFS 或保留当前策略但补充 experiment metadata 的版本化记录

**处理批注（`2026-05-16`）**：

- 部分采纳，但其中 `scenarios/` 应优先处理。
- 当前 [.gitignore](../../../.gitignore) 与 [README.md](../../../README.md) 对 `scenarios/` 的定位存在明显冲突：前者忽略，后者又把它描述为维护主线输入。
- 相比之下，`experiments/`、`datasets/`、`output/` 继续保持忽略更符合当前研究型工作流，不建议为了“版本完整”把大体积运行产物直接纳入主仓。
- 因此后续任务应先澄清并处理 `scenarios/` 版本策略，再决定是否需要独立仓库或主仓收纳。

### 4.8 🟢 构建目录碎片化

**现象**：仓库存在多个构建目录：
- `build/`
- `build-gpu/`
- `build-workshop/`
- `build-facade-local/`

**影响**：多构建目标的管理依赖环境变量 `CMO_BUILD_DIR` 和 `PYTHONPATH` 手动切换，容易出错。

**建议**：README 已将 `build-workshop` 设为推荐约定，但建议在 `tools/maintenance/cmo_env.sh` 中统一管理，并添加 `cmo_env_validate` 检查。

**处理批注（`2026-05-16`）**：

- 采纳。
- 其中“统一管理”这一半已经部分完成：仓库已新增 [tools/maintenance/cmo_env.sh](../../../tools/maintenance/cmo_env.sh) 作为 `.venv`、`CMO_BUILD_DIR` 与 `PYTHONPATH` 的统一入口。
- 仍待继续完成的是：
  - 补一个显式的 `cmo_env_validate` 或等价校验命令；
  - 逐步把 README / 脚本示例从散落的手写环境变量切换到统一入口。

---

## 5. 非目标

本次审查不做：
- 重写物理模型或改变 SimulationKernel::step() 语义
- 改变训练配置默认 runtime backend
- 删除 legacy command surface
- 提出新的 GPU exact-step 主线
- 破坏性 API 重命名

---

## 6. 推荐执行顺序

| 优先级 | 事项 | 预期收益 | 风险 |
|--------|------|----------|------|
| P0 | 补 CI 自动化 | 防止回归 | 低 |
| P1 | CMake target 拆分（WP7 后半程） | 增量编译 + link 层检查 | 中（需逐 target 验证） |
| P1 | 拆分 train.py 训练循环 | 代码可维护性 | 中（需保持 CLI 兼容） |
| P2 | SimulationKernel 接口拆分 | 可测试性 + 扩展性 | 中高（改 API 面） |
| P2 | 处理目录命名歧义 | 可读性 | 低（纯 rename） |
| P3 | 依赖管理加固 | 离线构建 + 安全 | 低 |
| P3 | .gitignore 策略审查 | 版本追溯 | 低（但有策略影响） |

## 7. 开放问题（下一轮冻结计划候选）

- 是否将 `src/interfaces/python` 重命名为 `src/bindings/python`
- 是否将 `gpu` 改名为 `accelerators/gpu`
- 是否引入包管理器（vcpkg/Conan）替代 FetchContent
- scenarios 的版本管理策略：独立仓库 vs 取消 gitignore vs Git LFS

**处理批注（`2026-05-16`）**：

- 本轮不将 `interfaces/python -> bindings/python` 与 `gpu -> accelerators/gpu` 作为活动任务。
- `vcpkg/Conan` 保留为后续评估议题，不进入当前冻结计划。
- `scenarios` 的版本管理策略保留为活动问题，但会进入后续冻结计划中的明确工作包。
